#!/usr/bin/env python3
"""Clockspeed PostToolUse guard - fast syntax and content check on edited files.

Seam: `edit_lint_check.py [--files <p...>]`, or a PostToolUse JSON envelope on
stdin; exit 0 pass, exit 1 problem.

This runs after EVERY Edit and Write, so it is built to be fast and to never
hang: every subprocess call carries a timeout and there is exactly one of them.
The stdin read is bounded by the same promise - see read_hook_envelope.

WHERE THE EDITED PATH COMES FROM (CS-845). Two sources, argument first:

  1. `--files`, for the suite, for a shell, and for any future caller.
  2. the PostToolUse envelope on stdin, which is how the HARNESS delivers it.

MEASURED end to end by a probe temporarily installed in this file and fired by
one real edit. `.claude/settings.json` invokes this as
`--files "$CLAUDE_FILE_PATHS"`, and that variable IS NOT SET - 22 other
CLAUDE_* variables are, and this is not one of them. So argv arrived as
`["--files", ""]` on every invocation the harness transcript store holds, for
the whole life of that store. Meanwhile stdin carried 19086 characters of JSON
whose `hook_event_name` was "PostToolUse" and whose `tool_input.file_path` was
the absolute edited path - unread, because nothing here looked at it.

THE FAILURE THAT PRODUCED READS LIKE A PERMISSIONS PROBLEM AND IS NOT ONE.
`Path("")` is `Path(".")`, and reading a directory raises PermissionError on
Windows. Anyone diagnosing that message at face value fixes the wrong thing.

Reading the envelope here rather than changing the invocation is deliberate:
`.claude/settings.json` is FROZEN (CLAUDE.md section 6) and needs an
adjudicator grant to touch, while this file does not. `--files` is therefore
OPTIONAL, so the tool behaves identically whether or not the dead argument is
ever removed from the frozen file, and removing it needs no code change here.

It shares the checker core with tools/precommit_gate.py by importing it rather
than reimplementing it. Two copies of a character-set rule drift; one does not.
Consequently a violation is reported the moment it is written to disk instead
of minutes later at commit time. The git hook remains authoritative
(CONVENTIONS.md section 8, tier 0) - this is the convenience layer.

What blocks (exit 1):
  - a python syntax error, a malformed .json, a malformed .yml/.yaml
  - a byte above 0x7E in an authored text file
  - a secret or PII match
  - ruff findings in the E9/F63/F7/F82 "real error" band
What does not block:
  - ruff style findings, printed as notes
  - a .yml/.yaml file when pyyaml is not importable, reported as a skip
  - a FORMATTING violation. `ruff format --check` is not enforced here at all,
    for the reason recorded at LINT_ROOT, and every run that could have
    reached it says so on stdout without needing --verbose. CS-841.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

import precommit_gate as gate

TOOL_NAME = "edit_lint_check"

# Tighter than the gate's: this runs on a single freshly edited file.
RUFF_TIMEOUT = 20

# The repository root handed to gate.run_ruff, and the ONE token that would
# arm a blocking format check on this path.
#
# gate.run_ruff resolves the project's ruff configuration from this root, and
# gate.run_ruff_format SKIPS the format check when nothing resolves. None is
# deliberate here rather than an oversight: this tool builds its Unit with no
# disk_path, so every unit is staged into a temp directory where ruff
# discovers no configuration at all, and MEASURED during CS-838 the great
# majority of this repo's tracked python "would be reformatted" against ruff's
# own defaults. Handing a root over would refuse edits this project formats
# correctly.
#
# It is NAMED rather than left implicit because this file is not frozen
# (CLAUDE.md section 6): a one-line change here arms a blocking check on the
# operator's live edit path with no grant and no review, and the first sign of
# it would be an edit being refused. CS-841.
#
# THE TRIPWIRES ARE IN tests/test_edit_lint_check.py, and there are two of them
# because one was not general enough. The out-of-repo case pins a root taken
# from a CONSTANT. The IN-REPO case is the one that carries the weight: the
# operator's live edit path is ALWAYS inside a repository, so a root resolved
# from the edited file - the most natural way anyone would ever arm this, given
# that the stated reason for None is that temp copies resolve nothing - is
# invisible to any bait sitting outside one.
LINT_ROOT: Path | None = None

# What the operator is owed when the check above is off. gate.emit renders
# report.notes under --verbose or on a run that already BLOCKED, and the
# PostToolUse entry passes neither, so the gate's own skip note is invisible
# on exactly the path it covers.
FORMAT_SKIP_NOTICE = (
    "edit_lint_check: ruff format --check is NOT enforced here - this tool "
    "lints temp-staged copies with no project config, so a formatting "
    "violation passes. The pre-commit gate and CI still block it."
)

# What a run that observed NOTHING says. CS-845.
#
# It is a THIRD sentence, deliberately unlike the other two. Saying "PASS"
# would claim a clean file nobody looked at, and saying a problem was left on
# disk claims a finding nobody made - which is the defect this closes, and it
# ran on every edit for the whole life of the transcript store. A gate that
# always cries wolf trains its reader to ignore it.
#
# It is also not SILENCE. tools/pretooluse_gate.py already records why a
# fail-open must always say so in its own words: a convenience layer that
# quietly stops covering the path it names is the false-guarantee class this
# project rates worse than the bug it hides. Exiting 0 without a word here
# would be exactly that, and it is what makes this notice load-bearing rather
# than decorative - tests/test_edit_lint_check.py pins both halves.
NOTHING_CHECKED_NOTICE = (
    "edit_lint_check: NOTHING WAS CHECKED - this run was given no readable "
    "path, on the argument or in a PostToolUse envelope on stdin, so it makes "
    "NO claim about the edit. That is a fault in the hook wiring, not a "
    "finding about the file. The pre-commit gate and CI are unaffected."
)

# Where an edited path lives inside `tool_input`. Edit, Write and MultiEdit
# all use `file_path`; `notebook_path` is NotebookEdit's, carried because the
# matcher in .claude/settings.json is frozen and may widen without this file
# getting a say. An unknown tool contributes nothing and is not an error.
ENVELOPE_PATH_KEYS = ("file_path", "notebook_path")


def read_hook_envelope() -> dict | None:
    """Return the PostToolUse envelope on stdin, or None. Never raises.

    FAILS OPEN, and the caller turns that into a stated "nothing was checked"
    rather than a verdict. Every way this can go wrong - no stdin, a closed
    stdin, bytes that are not JSON, JSON that is not an object - means the
    same thing: no path arrived here, so no claim can be made about one.
    Raising instead would turn a wiring fault into a crash on the operator's
    live edit path, and the authoritative gate is .githooks regardless.

    THE isatty CHECK IS THE NO-HANG GUARD and is the reason this is safe to
    call at all. A terminal's stdin never reaches EOF, so a blocking read
    there would hang until the harness killed it - and this module's opening
    promise is that it never hangs. The caller adds the other half by never
    reaching this function when an explicit path was given, so the ordinary
    shell invocation does not depend on the check at all.

    Under pytest, sys.stdin is a DontReadFromInput whose read raises OSError.
    That is caught here, which is why the suite does not need to special-case
    a tool that reads stdin.
    """
    stream = sys.stdin
    if stream is None:
        return None
    try:
        if stream.isatty():
            return None
        buffer = getattr(stream, "buffer", None)
        raw = buffer.read() if buffer is not None else stream.read().encode("utf-8", "replace")
    except (AttributeError, OSError, ValueError, UnicodeError):
        return None
    if not raw or not raw.strip():
        return None
    try:
        envelope = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        return None
    return envelope if isinstance(envelope, dict) else None


def paths_from_envelope(envelope: dict) -> list[str]:
    """Pull the edited path out of a PostToolUse envelope.

    `tool_input` is preferred over `tool_response` because it is what the
    model asked for, and it is present on the PreToolUse envelope too, so the
    two events could share this reader if one is ever added. `tool_response`
    is the fallback for a tool that reports a path it was not handed.

    NOTHING ELSE IN THE ENVELOPE IS READ. The measured payload also carries
    `cwd`, `transcript_path`, `session_id` and `agent_id` - absolute paths and
    identifiers under the operator's home directory. tools/pretooluse_gate.py
    records the same boundary for the same reason: they are harness metadata,
    they are not the edit, and touching them puts CLAUDE.md non-negotiable 3
    one careless render away.
    """
    found: list[str] = []
    tool_input = envelope.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ENVELOPE_PATH_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                found.append(value)
    if found:
        return found
    response = envelope.get("tool_response")
    if isinstance(response, dict):
        value = response.get("filePath")
        if isinstance(value, str) and value.strip():
            found.append(value)
    return found


def resolve_target_paths(given: list[str]) -> list[str]:
    """Decide what this run checks: the argument if it has one, else stdin.

    AN EMPTY STRING IS NOT A PATH, IT IS AN ABSENT ARGUMENT, and separating
    those two is the whole of CS-845. `--files "$CLAUDE_FILE_PATHS"` with the
    variable unset hands this an argument list of one empty string; treating
    it as a path made `Path("")` into `Path(".")`, failed to read a directory,
    and reported that failure as a problem with the edit.

    The filter is deliberately narrow. A non-empty path that cannot be read is
    something this run genuinely looked at, and it must still be reported -
    suppressing it too would satisfy the acceptance test while disarming the
    tool, and tests/test_edit_lint_check.py refuses that fix explicitly.

    THE ARGUMENT WINS AND STDIN IS NOT EVEN READ WHEN IT DOES. A fallback that
    fires anyway is not a fallback: it would check files the caller never
    named, and on a terminal it would block on a read that never returns.
    """
    named = [path for path in given if path.strip()]
    if named:
        return named
    envelope = read_hook_envelope()
    if envelope is None:
        return []
    return paths_from_envelope(envelope)


def check_json(label: str, data: bytes, report: gate.Report) -> None:
    """Parse the file as JSON; a parse error blocks."""
    try:
        json.loads(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        # exc.reason and exc.start are the decoder's REASON and offset. The
        # object itself is never rendered: str() on it would carry the bytes
        # it choked on, and exc.object holds file CONTENT rather than a reason.
        detail = f"{exc.reason} at byte {exc.start}"
        report.add(gate.Diagnostic(label, 0, 0, "SYNTAX", f"json is not UTF-8: {detail}"))
    except ValueError as exc:
        detail = getattr(exc, "msg", None) or type(exc).__name__
        report.add(
            gate.Diagnostic(
                label,
                getattr(exc, "lineno", 0) or 0,
                getattr(exc, "colno", 0) or 0,
                "SYNTAX",
                f"invalid json: {detail}",
            )
        )


def check_yaml(label: str, data: bytes, report: gate.Report) -> None:
    """Parse the file as YAML when pyyaml is importable, else skip."""
    try:
        # Optional: a machine without pyyaml must still be able to
        # edit a yaml file, so the import is a probe, not a dependency.
        import yaml  # noqa: PLC0415
    except ImportError:
        report.skip(label, "pyyaml is not importable; yaml was NOT parsed")
        return
    try:
        yaml.safe_load(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        detail = f"{exc.reason} at byte {exc.start}"
        report.add(gate.Diagnostic(label, 0, 0, "SYNTAX", f"yaml is not UTF-8: {detail}"))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        # The DEFAULT was the exception object itself. That reads like a field
        # access and is not one: whenever `problem` is absent it rendered the
        # whole exception, and a YAMLError raised from a file operation carries
        # the path in its text. Falling back to the class name fails closed.
        problem = getattr(exc, "problem", None) or type(exc).__name__
        report.add(
            gate.Diagnostic(
                label,
                (mark.line + 1) if mark else 0,
                (mark.column + 1) if mark else 0,
                "SYNTAX",
                f"invalid yaml: {problem}",
            )
        )


def lint_and_report_enforcement(report: gate.Report, root: Path | None) -> bool:
    """Run the gate's linter and RETURN whether the format check was ENFORCED.

    ONE function owns both the running and the verdict, and that is the entire
    point of its shape. The previous version had main derive the verdict a
    SECOND time from an argument it also chose, and a fact derived twice can
    disagree with itself - which it did, twice, both measured.

    gate.RUFF_TIMEOUT is swapped around the call rather than passed, because
    run_ruff reads it from the module at call time. The swap is restored in a
    finally so a raising linter cannot leak this tool's tighter editor budget
    into a later caller.
    """
    config = gate.ruff_config_args(root)
    saved = gate.RUFF_TIMEOUT
    gate.RUFF_TIMEOUT = RUFF_TIMEOUT
    try:
        gate.run_ruff(report.units, report, root)
    finally:
        gate.RUFF_TIMEOUT = saved
    return bool(config)


def disclose_format_skip(report: gate.Report, enforced: bool) -> bool:
    """Say that the format check did not run, on a channel --verbose does not gate.

    gate.emit is in a frozen file (CLAUDE.md section 6) and prints report.notes
    only under --verbose or on a run that already BLOCKED. So the disclosure is
    made here instead of there. A permanent disablement that no output mentions
    is the half of CS-841 this closes; the other half is the tripwire in
    tests/test_edit_lint_check.py.

    THIS TAKES THE RUN'S OWN VERDICT AND NEVER RE-DERIVES IT. Two earlier
    shapes are recorded because both shipped and both were refuted:

      1. It read gate.ruff_config_args itself, and the docstring claimed the
         notice "cannot outlive the skip it describes". FALSE. The CONDITION
         was read from the gate but the ARGUMENT was main's to choose, and
         swapping gate.ruff_config_args around the lint call - the same idiom
         this module uses on gate.RUFF_TIMEOUT - printed "NOT enforced here"
         while the check was enforced and BLOCKING.
      2. It took a root, and a static test asserted main handed the same NAME
         to both call sites. THAT IS A SPELLING CHECK. Rebinding that one name
         between the two calls is invisible to it, and restored the lie in
         full with the guard still green.

    There is no argument left here to diverge. `enforced` is returned by the
    call that did the linting, so the notice reports the run instead of taking
    a second guess at it. What still needs testing is that main keeps wiring
    it that way - and that is a BEHAVIOURAL question, not a syntactic one: the
    notice and an enforced format check must never appear together, however
    the wiring happens to be spelled. Checking the spelling instead is an arms
    race against the AST, and it was already lost once.

    The python filter mirrors gate.run_ruff's target selection, so a markdown
    edit - which never reaches ruff at all - says nothing rather than
    reporting a skip that was never reached.

    Returns whether the notice was written, which separates "disclosed" from
    "there was nothing to disclose".
    """
    if enforced:
        return False
    if not any(unit.ext == ".py" and unit.data is not None for unit in report.units):
        return False
    sys.stdout.write(FORMAT_SKIP_NOTICE + "\n")
    return True


def main(argv: list[str] | None = None) -> int:
    """Check each edited path and return the process exit code."""
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Syntax and content check for freshly edited files.",
    )
    # OPTIONAL, and that is a compatibility decision rather than a loosening.
    # The frozen .claude/settings.json passes `--files "$CLAUDE_FILE_PATHS"`,
    # which expands to nothing; making the flag optional means this tool
    # behaves identically whether that dead argument is removed through the
    # section-6 route or left exactly where it is forever. Requiring it would
    # make the frozen file's wording load-bearing on a path where the argument
    # has never once carried a value. CS-845.
    parser.add_argument("--files", nargs="*", default=[], metavar="PATH")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--list-skipped", action="store_true")
    args = parser.parse_args(argv)

    targets = resolve_target_paths(list(args.files))
    if not targets:
        # BEFORE gate.emit, and returning rather than falling through, so no
        # verdict is rendered at all. Falling through would print the gate's
        # PASS banner over zero units, which is a smaller lie than the one
        # this replaces but is still a claim about a file nobody opened.
        sys.stdout.write(NOTHING_CHECKED_NOTICE + "\n")
        return 0

    report = gate.Report()
    matchers = gate.PiiMatchers(report)

    for given in targets:
        label = gate.label_for(given)
        ext = PurePosixPath(label).suffix.lower()
        unit = gate.Unit(label=label, origin="worktree", ext=ext)
        if not gate.check_path(label, report):
            report.skip(label, "path itself is a violation; content not read")
            continue
        if not gate.classify_for_read(label, ext, report):
            continue
        try:
            data = Path(given).read_bytes()
        except OSError as exc:
            # The CS-204 residual. That item redacted the diagnostic LABEL
            # channel, so the label here is already safe - but the REASON was
            # still the raw object, and str() on an OSError appends the path it
            # failed on. Redacting one channel and leaving the other beside it
            # is not a fix, it is a narrower leak.
            reason = gate.safe_exc_text(exc)
            report.add(gate.Diagnostic(label, 0, 0, "IO", f"could not read the file: {reason}"))
            continue
        if not gate.accept_bytes(unit, data, report):
            continue
        gate.check_content(unit, matchers, report)
        if ext == ".json":
            check_json(label, data, report)
        elif ext in (".yml", ".yaml"):
            check_yaml(label, data, report)

    # One subprocess, bounded. Reuse the gate's runner so the blocking rule
    # band cannot diverge between the two tools. The call RETURNS whether the
    # format check was enforced, and the disclosure below reads that RETURN
    # VALUE rather than deriving the same fact again from an argument. Two
    # derivations can disagree with each other; one cannot.
    enforced = lint_and_report_enforcement(report, LINT_ROOT)

    # Before emit, so the PASS banner stays the last line the tool writes -
    # pinned by test_the_format_skip_is_disclosed_without_verbose rather than
    # merely asserted here.
    disclose_format_skip(report, enforced)

    code = gate.emit(report, args.verbose, args.list_skipped)
    if code:
        sys.stderr.write(
            f"{TOOL_NAME}: the edit above left a problem on disk. Fix it now - the "
            "pre-commit gate will block the commit otherwise.\n"
        )
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        # Suppressed by default, opt in explicitly - the same shape CLAUDE.md
        # non-negotiable 12 already mandates for the save header options
        # string. A traceback cannot be honestly redacted: it renders an
        # absolute path per frame and its final line is str(exc). The opt-in
        # name is the gate's, shared rather than duplicated, so the two crash
        # handlers cannot drift apart on the contract they publish.
        sys.stderr.write(
            "%s: guard raised %s: %s\n" % (TOOL_NAME, type(exc).__name__, gate.safe_exc_text(exc))
        )
        if os.environ.get(gate.ENV_CRASH_TRACEBACK) == "1":
            traceback.print_exc()
        else:
            sys.stderr.write(f"  Set {gate.ENV_CRASH_TRACEBACK}=1 to print the traceback.\n")
        sys.stderr.write(f"{TOOL_NAME}: failing closed with exit 1.\n")
        raise SystemExit(1) from None
