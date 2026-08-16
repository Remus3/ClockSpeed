#!/usr/bin/env python3
"""PreToolUse hook wrapper - makes the character-set and secret gate actually fire.

WHAT THIS FIXES (CS-425). The hook was wired as
`python tools/precommit_gate.py --text-stdin` and it did nothing at all, for
two independent reasons, each of which is sufficient on its own:

  1. IT COULD NOT DENY. Claude Code denies a tool call on exit code 2 and
     treats every other status as surfaced-and-non-blocking. The gate exits 1
     on a violation, so a violation was reported and then run anyway.
  2. IT COULD NOT SEE. A hook does not receive raw text on stdin, it receives
     a JSON envelope. A JSON emitter escapes a non-ASCII character to a
     backslash-u sequence which is itself pure ASCII, so the character-set scan
     read the transport encoding, found nothing above 0x7E, and returned PASS.
     `--text-stdin` is named for what it wants and was never given it.

Measured end to end before this file was written: a tool call carrying a
literal em dash RAN UNBLOCKED. This wrapper parses the envelope so the scan
sees the real command, and exits 2 so a finding genuinely denies the call.

THE AUTHORITATIVE GATE IS STILL `.githooks`, WHICH THIS DOES NOT TOUCH.
CLAUDE.md section 2.2 is exactly right that the Claude hooks are a convenience
layer. What was wrong is that the convenience layer provided no convenience
while costing a process spawn per shell call.

--------------------------------------------------------------------------
THE TWO HALVES OF THE CONTRACT, AND WHY THEY POINT OPPOSITE WAYS
--------------------------------------------------------------------------

FAIL CLOSED on a real finding      -> exit 2. The call is denied and stderr is
                                      handed to the model so it can rewrite.

FAIL OPEN on this wrapper's own    -> exit 0. Bad JSON, an envelope shape
error                                 nobody anticipated, an unimportable
                                      gate: the call proceeds and the reason
                                      is printed. A convenience layer that
                                      bricks every shell call is far worse
                                      than one that misses, and the commit
                                      path is protected by .githooks
                                      regardless of what happens here.

A fail-open ALWAYS says so, in those words. A silent fail-open would be the
false-guarantee class this project rates worse than the bug it hides, so
"PASS" and "NOT SCANNED" are deliberately different sentences.

--------------------------------------------------------------------------
THE SCAN IS IMPORTED, NEVER TRANSCRIBED
--------------------------------------------------------------------------

Every pattern, every codepoint name and the whole render boundary come from
tools/precommit_gate.py by import. A second transcription of a security scan
is a second place to get it subtly wrong. tools/precommit_gate.py is a FROZEN
file (CLAUDE.md section 6) and this wrapper exists in part so that making the
hook work needed no edit to it at all.

GATE_SYMBOLS below names that dependency explicitly, and
tests/test_pretooluse_gate.py asserts every name in it resolves - so a rename
inside the frozen gate turns the suite red rather than degrading this into a
permanent silent fail-open.

--------------------------------------------------------------------------
WHAT IS SCANNED, AND WHAT DELIBERATELY IS NOT
--------------------------------------------------------------------------

SCANNED: every string anywhere inside `tool_input`, found by walking it, not
by an allowlist of key names. An allowlist would silently miss whichever field
a tool gains tomorrow, and `description` is authored content that non-negotiable
4 covers just as much as `command` does.

NOT SCANNED: the envelope fields AROUND `tool_input` - `cwd`,
`transcript_path`, `session_id`. Those are harness-supplied absolute paths
under the operator's home directory. Scanning them would deny every call on a
machine whose account name is not ASCII and would report the operator's own
directory back as a finding. They are harness metadata, not the tool call's
content, and nothing the model writes can change them.

A SHARP EDGE THAT IS NOT OURS TO FIX: CPython exits with status 2 when it
cannot open the script it was handed, which is the same number as a deny. So a
missing or unreadable copy of THIS file denies every shell call rather than
failing open. The exposure is pre-existing and unchanged - the old wiring named
precommit_gate.py and behaved identically - and it is loud, because the
interpreter names the file it could not open. It is recorded here and pinned by
tests/test_pretooluse_gate.py so it is a known property rather than a surprise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType
from typing import TextIO

WRAPPER_NAME = "pretooluse_gate"

# Claude Code's PreToolUse protocol: exit 2 denies the tool call and feeds
# stderr back to the model. Every other status is non-blocking, which is
# precisely why the old wiring's exit 1 never stopped anything.
DENY_EXIT_CODE = 2

# Everything that is not a denial. Used for a clean pass AND for every
# fail-open path, because a broken convenience layer must never block work.
ALLOW_EXIT_CODE = 0

# The envelope key holding the tool call's own arguments.
TOOL_INPUT_KEY = "tool_input"

# Depth cap for the walk. The walk is iterative so a deep envelope cannot
# raise RecursionError; this bounds the work rather than the stack.
MAX_WALK_DEPTH = 16

# The exact surface this wrapper needs from the frozen gate. Named as data so
# the suite can assert every one of them resolves.
GATE_SYMBOLS: tuple[str, ...] = (
    "Report",
    "check_charset",
    "check_secrets",
    "decode_for_report",
    "display_diagnostic",
    "display_note",
    "label_replacements",
)


def write(stream: TextIO | None, text: str) -> None:
    """Write to a stream that may not be usable.

    A GUI-subsystem interpreter such as pythonw.exe has sys.stdout set to None
    when the parent supplies no redirection, and a closed pipe raises on write.
    Neither is a reason to lose a verdict, so reporting failures are swallowed
    here and the exit code carries the answer on its own.
    """
    if stream is None:
        return
    try:
        stream.write(text)
        stream.flush()
    except (OSError, ValueError):
        return


def load_gate() -> ModuleType:
    """Import the frozen gate from beside this file.

    Resolved from __file__ rather than from the working directory: a hook's cwd
    is whatever the harness chose, and a gate found by luck is a gate that
    stops being found.

    Returns:
        The precommit_gate module.

    Raises:
        ImportError: The gate is not importable from beside this file.
    """
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import precommit_gate  # noqa: PLC0415

    return precommit_gate


def read_envelope(stream: TextIO | None) -> object:
    """Read and parse the hook envelope from stdin.

    Decoded with errors="replace" before parsing, so malformed bytes surface as
    a JSON error - one failure mode to handle instead of two.

    Returns:
        The parsed envelope, which is whatever JSON happened to be there.

    Raises:
        ValueError: stdin held no usable JSON.
        AttributeError: stdin is not readable at all.
    """
    if stream is None:
        raise ValueError("stdin is not available")
    data: bytes = stream.buffer.read()
    if not data.strip():
        raise ValueError("stdin was empty")
    return json.loads(data.decode("utf-8", "replace"))


def extract_strings(envelope: object) -> list[tuple[str, str]]:
    """Walk `tool_input` and return every string in it, with a readable label.

    Iterative rather than recursive so a pathologically nested envelope cannot
    raise RecursionError inside a hook. Every string is returned regardless of
    which key holds it - see the module docstring on why this is a walk and not
    an allowlist.

    Returns:
        (label, value) pairs in envelope order.

    Raises:
        TypeError: The envelope is not an object, or carries no `tool_input`
            object. Both are fail-open conditions, raised rather than silently
            returning an empty list so the two cases stay distinguishable.
    """
    if not isinstance(envelope, dict):
        raise TypeError("the envelope is not a JSON object")
    if TOOL_INPUT_KEY not in envelope:
        raise TypeError("the envelope carries no " + TOOL_INPUT_KEY)
    root = envelope[TOOL_INPUT_KEY]
    if not isinstance(root, dict):
        raise TypeError(TOOL_INPUT_KEY + " is not a JSON object")

    found: list[tuple[str, str]] = []
    stack: list[tuple[str, object, int]] = [(TOOL_INPUT_KEY, root, 0)]
    while stack:
        path, node, depth = stack.pop(0)
        if isinstance(node, str):
            found.append(("<" + path + ">", node))
        elif depth >= MAX_WALK_DEPTH:
            continue
        elif isinstance(node, dict):
            stack.extend((f"{path}.{key}", value, depth + 1) for key, value in node.items())
        elif isinstance(node, list):
            stack.extend((f"{path}[{i}]", value, depth + 1) for i, value in enumerate(node))
    return found


def scan_text(gate: ModuleType, label: str, value: str, report: object) -> None:
    """Run the gate's character-set and secret checks over one string.

    This is the same composition as the gate's own stdin mode and it is held to
    that by tests/test_pretooluse_gate.py, which runs both over the same text
    and compares the findings character for character. If the gate grows a
    third check there, that test goes red and this grows it too.

    surrogatepass on the encode is load-bearing: json.loads yields an unpaired
    surrogate for a lone backslash-u escape, and a plain UTF-8 encode raises on
    one. Passing it through leaves bytes above 0x7E, which is exactly what an
    unpaired surrogate in a shell command deserves to be called.
    """
    data = value.encode("utf-8", "surrogatepass")
    report.checked.append((label, TOOL_INPUT_KEY, len(data)))  # type: ignore[attr-defined]
    gate.check_charset(label, data, report)
    text, note = gate.decode_for_report(data)
    if note:
        report.notes.append(f"{label}: {note}")  # type: ignore[attr-defined]
    gate.check_secrets(label, text, report)


def report_denial(gate: ModuleType, report: object, scanned: int) -> None:
    """Render a denial to stderr, which is what the model is handed on exit 2.

    Rendered through the gate's own display boundary rather than by printing
    the raw diagnostics: display_diagnostic and display_note are where label
    redaction happens (CLAUDE.md non-negotiable 12), and a second renderer
    would be a second place for a home path to escape.

    The gate's own emit() is deliberately NOT reused here. It is correct, but
    its wording is commit-specific - "Nothing was committed" - and a tool call
    that was refused is not a commit that was refused.
    """
    err = sys.stderr
    replacements = gate.label_replacements(report)
    write(err, WRAPPER_NAME + ": DENIED - this tool call was NOT run.\n")
    seen: set[str] = set()
    for diag in report.diagnostics:  # type: ignore[attr-defined]
        # Deduplicate on the RAW render and display the redacted one, matching
        # the gate: two labels can redact to the same text, and collapsing on
        # the redacted form would drop a real finding.
        rendered = diag.render()
        if rendered in seen:
            continue
        seen.add(rendered)
        write(err, gate.display_diagnostic(diag) + "\n")
    for note in report.notes:  # type: ignore[attr-defined]
        write(err, "  note     " + gate.display_note(note, replacements) + "\n")
    write(
        err,
        "%s: DENIED - %d finding(s) across %d scanned string(s). CLAUDE.md "
        "non-negotiable 4 is 7-bit ASCII in all authored content; a spaced "
        "hyphen ' - ' replaces a dash. Rewrite the call and retry.\n"
        % (WRAPPER_NAME, len(seen), scanned),
    )


def fail_open(why: str) -> int:
    """Report that nothing was checked, and let the call through.

    Printed to stdout because that is the stream the harness renders for a
    non-denying exit. The words "NOT SCANNED" are load-bearing and are pinned
    by the suite: a fail-open that reads like a pass is the false guarantee
    this whole item exists to remove.

    Returns:
        ALLOW_EXIT_CODE, always.
    """
    write(
        sys.stdout,
        "%s: NOT SCANNED - %s. Letting the tool call through: the authoritative "
        "gate is .githooks, and a hook that blocks every call is worse than one "
        "that misses.\n" % (WRAPPER_NAME, why),
    )
    return ALLOW_EXIT_CODE


def main() -> int:
    """Scan the tool call on stdin and return the process exit code.

    Returns:
        DENY_EXIT_CODE when the call carries a finding, ALLOW_EXIT_CODE
        otherwise - including every way this wrapper can fail.
    """
    try:
        gate = load_gate()
    except BaseException as exc:  # the fail-open contract, stated at the top
        return fail_open("the gate could not be imported (" + type(exc).__name__ + ")")

    try:
        strings = extract_strings(read_envelope(sys.stdin))
    except BaseException as exc:  # the fail-open contract, stated at the top
        # No exception text is rendered. safe_exc_text() exists in the gate for
        # this reason and str() on an OSError appends the path it failed on;
        # the class name says enough for a convenience layer.
        return fail_open("the hook envelope could not be read (" + type(exc).__name__ + ")")

    if not strings:
        return fail_open(TOOL_INPUT_KEY + " carried no text to check")

    try:
        report = gate.Report()
        for label, value in strings:
            scan_text(gate, label, value, report)
        blocked = bool(report.diagnostics)
    except BaseException as exc:  # the fail-open contract, stated at the top
        return fail_open("the scan itself raised (" + type(exc).__name__ + ")")

    # PAST THIS POINT THE VERDICT IS DECIDED AND IS NOT REVISITED. Reporting is
    # allowed to fail - a GUI-subsystem interpreter can hand us a None stdout -
    # but a failure to PRINT a finding is not a reason to run the call. Only
    # the code above, which decides whether there IS a finding, can fail open.
    if not blocked:
        write(
            sys.stdout,
            "%s: PASS - %d string(s) scanned, 0 findings\n" % (WRAPPER_NAME, len(strings)),
        )
        return ALLOW_EXIT_CODE

    try:
        report_denial(gate, report, len(strings))
    except BaseException:  # the verdict outranks the rendering
        write(sys.stderr, WRAPPER_NAME + ": DENIED - findings could not be rendered.\n")
    return DENY_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
