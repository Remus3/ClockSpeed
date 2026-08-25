#!/usr/bin/env python3
"""Tests for tools/edit_lint_check.py.

The tool is invoked as a SUBPROCESS throughout, for the same reason the gate
suite does it: the exit code is half the contract, 0 pass and 1 problem, and
this runs as a PostToolUse hook where that code is the whole signal.

CS-204 is why this file exists. edit_lint_check builds its own labels - it
calls gate.label_for itself and constructs its own gate.Unit, both inside its
`main` - but it renders them through the SAME gate.emit. So a redaction
applied in emit covers both tools, and a redaction applied anywhere else
covers only one. The grant made this a test obligation rather than an
inspection obligation precisely because "it shares the renderer" is the kind
of claim that is true right up until someone adds a second printer.

Those three call sites were cited by LINE NUMBER until CS-845. All three had
already rotted - :102 and :104 pointed at a closing paren and a blank line in
an unrelated function before this item touched the file at all. A line number
into a live source file is a fact with no owner and no guard (CLAUDE.md
section 4), so the citation is by NAME now, which the tree moves with.

Every violating literal is assembled at runtime rather than spelled out: this
file is itself checked by the gate, so a literal em dash or home path here
would block the commit that adds it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
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
    stdin_text: str = "",
) -> subprocess.CompletedProcess[str]:
    """Run the tool as a subprocess with stdin under the test's control.

    stdin is PINNED rather than inherited. CS-845 gave this tool a stdin
    fallback - the harness delivers the edited path in a JSON envelope there -
    so a suite that let the subprocess inherit pytest's stdin would be
    asserting against whatever the runner happened to leave attached. The
    default is the empty string, which is what "no envelope" means.
    """
    proc = subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        input=stdin_text.encode("utf-8"),
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


def clean_verdict() -> str:
    """gate.emit's clean banner, with the movable half IMPORTED not restated.

    CLAUDE.md section 4 gives every fact one owner, and this one's owner -
    tools/precommit_gate.py - is FROZEN. Spelling "precommit_gate" out here
    would mean that rewording it through the section-6 route reddens this test
    for a reason with nothing to do with its subject. Only GATE_NAME is owned
    over there; the literal ": PASS " belongs to emit's format string and has
    no separate owner to import, so it stays.

    Loaded by path rather than imported as tools.precommit_gate, which is the
    same choice tests/test_precommit_gate.py::load_gate makes and for the same
    reason: it keeps tools/ out of the import graph.
    """
    name = "clockspeed_gate_banner"
    spec = importlib.util.spec_from_file_location(name, GATE)
    assert spec is not None, "the gate could not be located for its banner token"
    assert spec.loader is not None, "the gate has no loader"
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module, for the reason
    # tests/test_precommit_gate.py::load_gate records: the gate declares
    # dataclasses under `from __future__ import annotations`, and @dataclass
    # resolves those string annotations through sys.modules[cls.__module__].
    # Unregistered, that lookup returns None and the decorator raises while the
    # class body is still running. Measured here the hard way.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return str(module.GATE_NAME) + ": PASS"


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

    # ORDERING, pinned because the tool CLAIMS it in a comment. Moving the
    # disclosure after gate.emit survives every other assertion in this file,
    # so without this the claim is decoration. No consumer parses this stdout
    # today - the point is that the code should not assert what nothing checks.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[-1].startswith(clean_verdict()), (
        "the tool claims the PASS banner stays its last line; it does not: " + repr(lines)
    )
    assert any(FORMAT_SKIP_MARKER in line for line in lines[:-1]), repr(lines)


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


# --------------------------------------------------------------------------
# CS-841 REPAIR - the tripwire above is SPECIFIC, and a specific tripwire over
# the wrong path guards nothing. These generalise it.
# --------------------------------------------------------------------------

# `work/`, and the two rejected candidates are why. FOUR criteria, all MEASURED,
# and no candidate satisfying three of them is good enough:
#
#   1. NOT in `git ls-files --cached --others --exclude-standard`. That is the
#      WOULD-BE-TRACKED inventory tests/conftest.py builds as `repo_files`, and
#      tests/test_mypy_gate.py reads it. An untracked unignored directory is
#      INSIDE it, so a bait at the repo root makes that module fail - only
#      under `-n auto`, which is what .github/workflows/tier2.yml runs and what
#      the serial pre-push hook does not. Green here, red in the nightly lane.
#   2. NOT swept by `ruff format --check .` from the root, which is CI tier1.
#   3. NOT refused by the gate's PUBLISHER rule, or the bait never reaches the
#      format check and the tripwire grades a path rejection instead.
#   4. Still inside THIS checkout, so a root resolved from the edited file and
#      a root conditioned on this checkout BOTH still arm.
#
# `data/` fails 3: PUBLISHER_ROOT_DIRS refuses it before a byte is read.
# The repo ROOT fails 1 and 2. A throwaway git repo under tmp_path fails 4 -
# measured, it disarms any mutant conditioned on this checkout, which would
# have retired a live tripwire silently. `work/` is gitignored, is not a
# PUBLISHER root dir, and is inside the checkout.
IN_REPO_BAIT_PARENT = REPO_ROOT / "work"


@pytest.fixture
def in_repo_bait() -> Iterator[Path]:
    """A format-dirty .py INSIDE the repository, removed again afterwards.

    THE BAIT ABOVE IS OUTSIDE ANY REPOSITORY AND THE OPERATOR'S EDIT PATH IS
    NEVER OUTSIDE ONE. That gap is not academic. Any arming conditioned on the
    edited file's LOCATION is invisible to an out-of-repo bait, and the most
    natural way to arm this tool is exactly that: resolve the root from the
    file being edited, which yields nothing for a temp copy and the project
    config for a real edit.

    Created at runtime rather than committed, because a format-dirty file
    tracked in this repository would fail `ruff format --check .` in CI - the
    very check whose absence here is the item.

    THE TEARDOWN FAILS LOUDLY. An earlier version swallowed errors, so one open
    handle on Windows left the directory behind and the mypy gate went
    permanently red naming a directory nobody would recognise. A cleanup that
    cannot report its own failure is how a test leaves landmines.
    """
    IN_REPO_BAIT_PARENT.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(dir=str(IN_REPO_BAIT_PARENT), prefix="cs841_bait_"))
    target = directory / "bait.py"
    target.write_bytes(FORMAT_DIRTY)
    try:
        yield target
    finally:
        for _ in range(5):
            shutil.rmtree(directory, ignore_errors=True)
            if not directory.exists():
                break
            time.sleep(0.1)
        assert not directory.exists(), (
            "the bait directory survived teardown at " + str(directory) + " - remove it "
            "before running the suite again, or tests that read the repository "
            "inventory will fail naming a path that has nothing to do with them"
        )


def test_a_root_reaching_this_tool_arms_it_on_an_in_repo_edit(
    tmp_path: Path,
    in_repo_bait: Path,
) -> None:
    """The tripwire GENERALISED to the path it actually protects.

    The out-of-repo case pins a root taken from a CONSTANT and nothing more.
    Two arming mutants sail straight past it, both leaving that case green
    while a blocking `ruff format --check` fires on every real edit:

      1. Resolve the root from the EDITED FILE's repository. Not exotic - it
         is the most natural repair anyone would reach for, precisely because
         the stated reason the root is None is that temp copies resolve no
         config.
      2. Swap gate.ruff_config_args around the lint call for in-repo paths,
         which is THE SAME IDIOM this tool already uses on gate.RUFF_TIMEOUT.

    Under the second the tool also PRINTS the skip notice while the check is
    enforced and blocking, so this test is what stops that notice lying.
    """
    reference = run_gate("--files", str(in_repo_bait), env=base_env(tmp_path))

    assert reference.returncode == 1, (
        "the in-repo bait is no longer refused by the tool that DOES pass a root, "
        "so this tripwire guards nothing: " + reference.stdout + reference.stderr
    )
    assert FORMAT_CODE in reference.stderr, (
        "the sibling gate refused the in-repo bait for some reason OTHER than "
        "formatting, so the differential under test is not the root: " + reference.stderr
    )

    result = run_tool("--files", str(in_repo_bait), env=base_env(tmp_path))

    assert result.returncode == 0, (
        "a root now reaches tools/edit_lint_check.py on an IN-REPO edit: the format "
        "check is armed and BLOCKING on the operator's live edit path. CS-841 says "
        "that needs a grant and a recorded review, not a one-line edit. " + result.stderr
    )
    assert FORMAT_CODE not in result.stderr, result.stderr
    assert FORMAT_SKIP_MARKER in result.stdout, (
        "the notice is absent on an in-repo edit, so either the check is now armed "
        "or the disclosure never covered the real path: " + repr(result.stdout)
    )


def test_the_notice_and_an_enforced_format_check_never_co_occur(
    tmp_path: Path,
    in_repo_bait: Path,
) -> None:
    """The notice must not be able to DISAGREE with the run it describes.

    THIS REPLACED A STATIC CHECK THAT WAS A SPELLING CHECK. That one parsed
    main and asserted the linter and the disclosure were handed the same
    ast.Name. Rebinding that one name between the two call sites is invisible
    to it, so an arming mutant plus a one-line rebind blocked a real in-repo
    edit while printing that the check was not enforced - with the guard
    green. Tightening the AST check would have been an arms race against
    Python syntax, and there is no reason to expect to win it.

    So the property is asserted on BEHAVIOUR instead, where spelling cannot
    reach it. For a format-dirty python file, exactly one of these is true and
    never both and never neither:

      - the format check was ENFORCED, so a FORMAT diagnostic names the file
      - the format check was SKIPPED, so the notice says it is not enforced

    Both at once is the lie. Neither is a disclosure that has gone silent
    again, which is the original defect returning. Whatever the wiring looks
    like, it has to land on exactly one.
    """
    result = run_tool("--files", str(in_repo_bait), env=base_env(tmp_path))

    enforced = FORMAT_CODE in result.stderr
    disclosed = FORMAT_SKIP_MARKER in result.stdout

    assert enforced != disclosed, (
        "the notice and the run disagree. enforced=%r disclosed=%r. Either the "
        "tool printed that the format check is off while a FORMAT diagnostic "
        "blocked the edit, or it enforced nothing and said nothing.\nstdout: %s\n"
        "stderr: %s" % (enforced, disclosed, result.stdout, result.stderr)
    )


# --------------------------------------------------------------------------
# CS-845 - the tool was handed an EMPTY path set on every live invocation.
#
# MEASURED, not inferred. A probe temporarily installed in this tool and
# triggered by one real edit captured the process it actually runs as:
#
#   argv                  ["tools/edit_lint_check.py", "--files", ""]
#   CLAUDE_FILE_PATHS     ABSENT from the environment entirely, alongside 22
#                         other CLAUDE_* variables that ARE set
#   stdin                 19086 characters of JSON that parse to an object
#                         whose hook_event_name is "PostToolUse" and whose
#                         tool_input.file_path is the absolute edited path
#
# So `--files "$CLAUDE_FILE_PATHS"` expands to the empty string because the
# variable does not exist. The tool then read nothing, staged nothing, linted
# nothing, and printed that the edit had left a problem on disk.
#
# THE READ FAILURE IN THAT MESSAGE IS NOT A PERMISSIONS PROBLEM, which is
# exactly what it reads like. Path("") is Path("."), and reading a directory
# raises PermissionError on Windows. The label tracks the working directory
# precisely as Path("") does, which is why the store's records carry a
# worktree directory as the label whenever a subagent made the edit.
# --------------------------------------------------------------------------

# The sentence the tool must NOT print about an edit it never looked at. Held
# as an independent literal rather than imported from the tool: importing it
# would let a rename carry this test to green while the operator still reads a
# claim the run did not earn.
FAILURE_FRAGMENT = "left a problem on disk"

# The distinct sentence a run that observed nothing owes its reader. Distinct
# is the whole contract - tools/pretooluse_gate.py already records why "PASS"
# and "NOT SCANNED" are deliberately different sentences, and a run that
# checked nothing must not borrow either one.
NOTHING_CHECKED_FRAGMENT = "NOTHING WAS CHECKED"

# A basename that appears ONLY inside an envelope, so a channel naming it
# proves the envelope was consumed rather than merely parsed.
ENVELOPE_BASE = "zzenvelopezz"


def envelope_for(target: Path, tool_name: str = "Edit") -> str:
    """A PostToolUse envelope of the shape the harness was MEASURED to send.

    Only the fields this tool consumes are populated. The measured envelope
    also carries cwd, transcript_path, session_id and agent_id - absolute
    paths and identifiers under the operator's home directory (CLAUDE.md
    non-negotiable 3), and none of them anything this tool has any business
    reading. Their absence here is the point: if the tool ever starts
    depending on one, this fixture stops satisfying it.
    """
    return json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": tool_name,
            "tool_input": {"file_path": str(target)},
        }
    )


def test_an_empty_path_argument_claims_no_problem(tmp_path: Path) -> None:
    """THE CS-845 ACCEPTANCE TEST - no readable path, so no failure sentence.

    This is the exact argv the harness was measured to produce, reproduced
    WITHOUT the transcript store, so the proof runs on a fresh clone and on a
    machine that has never run the harness at all.
    """
    result = run_tool("--files", "", env=base_env(tmp_path))

    assert FAILURE_FRAGMENT not in result.stderr, (
        "the tool reported a problem on disk after reading no file at all.\n"
        "stdout: %s\nstderr: %s" % (result.stdout, result.stderr)
    )


def test_an_empty_path_argument_says_it_checked_nothing(tmp_path: Path) -> None:
    """Silence is the other way to get this wrong, and it is worse.

    A run that quietly exits 0 having checked nothing is the self-arming skip
    class CS-841 was about: the gate goes dark and no output says so. The fix
    for the false claim must not buy its silence.
    """
    result = run_tool("--files", "", env=base_env(tmp_path))
    combined = result.stdout + result.stderr

    assert NOTHING_CHECKED_FRAGMENT in combined, (
        "the tool checked nothing and did not say so.\nstdout: %s\nstderr: %s"
        % (result.stdout, result.stderr)
    )


def test_a_genuinely_unreadable_path_is_still_reported(tmp_path: Path) -> None:
    """The over-broad fix, refused.

    Dropping the empty argument must not drop a REAL observation beside it. A
    non-empty path that cannot be read is something the run actually looked at
    and failed on, and the failure sentence is earned there. A fix that
    suppressed this too would satisfy the acceptance test above while quietly
    disarming the tool.
    """
    missing = tmp_path / OUTSIDE_DIR / (OUTSIDE_BASE + ".py")
    missing.parent.mkdir(parents=True, exist_ok=True)

    result = run_tool("--files", str(missing), env=base_env(tmp_path))

    # Bound to plain scalars before asserting. pytest renders the asserted
    # EXPRESSION independently of the message, and `result` is a
    # CompletedProcess whose repr carries the absolute interpreter path
    # (CLAUDE.md non-negotiable 3). Every assertion below does the same.
    code = result.returncode
    reported = FAILURE_FRAGMENT in result.stderr

    assert code == 1, "a path that cannot be read was not reported.\nstdout: %s\nstderr: %s" % (
        result.stdout,
        result.stderr,
    )
    assert reported, result.stderr


def test_the_edited_path_arrives_on_the_stdin_envelope(tmp_path: Path) -> None:
    """THE DELIVERY HALF, end to end.

    The harness delivers the edited path as JSON on stdin. This drives the
    tool exactly as the harness does - the same empty --files argument, the
    same envelope shape - and asserts it reaches the file and produces the
    verdict that file earns. Hook presence is not hook firing, and an argument
    that parses is not a path that was read: the proof is the DIAGNOSTIC
    naming the file, not the exit code alone.
    """
    body = ("# T\n\nAlpha " + EM_DASH + " b\n").encode("utf-8")
    target = outside_target(tmp_path, ".md", body)

    result = run_tool("--files", "", env=base_env(tmp_path), stdin_text=envelope_for(target))

    code = result.returncode
    names_the_file = OUTSIDE_BASE in result.stderr
    said_nothing_checked = NOTHING_CHECKED_FRAGMENT in (result.stdout + result.stderr)

    assert code == 1, "the envelope path was not checked.\nstdout: %s\nstderr: %s" % (
        result.stdout,
        result.stderr,
    )
    assert names_the_file, result.stderr
    assert not said_nothing_checked, result.stdout


def test_a_clean_file_on_the_stdin_envelope_passes(tmp_path: Path) -> None:
    """The other verdict. Without this, "it refuses everything" would pass."""
    target = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')

    result = run_tool("--files", "", env=base_env(tmp_path), stdin_text=envelope_for(target))

    code = result.returncode

    assert code == 0, "a clean file delivered by envelope was refused.\nstdout: %s\nstderr: %s" % (
        result.stdout,
        result.stderr,
    )


def test_an_explicit_path_is_not_overridden_by_the_envelope(tmp_path: Path) -> None:
    """The envelope is a FALLBACK, and a fallback that fires anyway is not one.

    An explicit --files argument is what the suite, the operator at a shell
    and every future caller use. If a stray envelope on stdin could add
    targets to that run, the tool would check files nobody asked it about.
    """
    clean = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')
    dirty = tmp_path / OUTSIDE_DIR / (ENVELOPE_BASE + ".md")
    dirty.write_bytes(("# T\n\nAlpha " + EM_DASH + " b\n").encode("utf-8"))

    result = run_tool("--files", str(clean), env=base_env(tmp_path), stdin_text=envelope_for(dirty))

    code = result.returncode
    envelope_was_consumed = ENVELOPE_BASE in (result.stdout + result.stderr)

    assert code == 0, (
        "the envelope was consumed even though an explicit path was given.\n"
        "stdout: %s\nstderr: %s" % (result.stdout, result.stderr)
    )
    assert not envelope_was_consumed, result.stdout + result.stderr


def test_an_explicit_path_never_reads_stdin_at_all(tmp_path: Path) -> None:
    """The no-hang guard, on the one path where hanging became possible.

    This module's opening promise is that it never hangs, and reading stdin is
    the only thing that put that promise at risk.

    stdin is left OPEN and never written to. A tool that reads it blocks
    forever; a tool that never reaches the read exits normally. The test above
    proves the envelope is not USED, which a tool that read stdin first and
    then discarded it would also satisfy - and that tool would hang here.
    """
    target = outside_target(tmp_path, ".py", b'"""Doc."""\n\nVALUE = 1\n')

    proc = subprocess.Popen(
        [sys.executable, str(TOOL), "--files", str(target)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env(tmp_path),
    )
    try:
        code = proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)
        pytest.fail("the tool blocked on stdin even though an explicit path was given")
    finally:
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()

    assert code == 0
