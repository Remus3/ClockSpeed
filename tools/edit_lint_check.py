#!/usr/bin/env python3
"""Clockspeed PostToolUse guard - fast syntax and content check on edited files.

Seam: `edit_lint_check.py --files <p...>`; exit 0 pass, exit 1 problem.

This runs after EVERY Edit and Write, so it is built to be fast and to never
hang: every subprocess call carries a timeout and there is exactly one of them.

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


def main(argv: list[str] | None = None) -> int:
    """Check each edited path and return the process exit code."""
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Syntax and content check for freshly edited files.",
    )
    parser.add_argument("--files", nargs="+", required=True, metavar="PATH")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--list-skipped", action="store_true")
    args = parser.parse_args(argv)

    report = gate.Report()
    matchers = gate.PiiMatchers(report)

    for given in args.files:
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
    # band cannot diverge between the two tools.
    saved = gate.RUFF_TIMEOUT
    gate.RUFF_TIMEOUT = RUFF_TIMEOUT
    try:
        gate.run_ruff(report.units, report)
    finally:
        gate.RUFF_TIMEOUT = saved

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
