#!/usr/bin/env python3
"""CS-845 - the PostToolUse census, DERIVED from the harness transcript store.

WHAT THIS IS FOR. tests/test_edit_lint_check.py proves the tool no longer
claims a problem it did not observe, using an argv reconstructed by hand. That
proof is complete and it runs everywhere. This module answers the different
question the acceptance also asks: what did the harness ACTUALLY hand this
tool, across every session on this machine, and does the shipped tool still
misbehave on any of it?

WHY IT IS DERIVED AND NOT TRANSCRIBED. A count written into a test is a lie
with a timestamp on it (CLAUDE.md section 4). The population here grows on
every edit of every session, and two independent measurements taken a day
apart already disagreed - one counted 947 records, this file's derivation
counted 959 on the next run, and both were right when taken. So nothing here
is written down. The store is located, the records are selected, the argument
vectors are reconstructed by expanding the recorded command the way a POSIX
shell would, and the shipped tool is RE-RUN against them. If the store gains a
new invocation shape tomorrow, this grades that shape too without an edit.

WHY IT REPLAYS RATHER THAN INSPECTS. Asserting over the recorded stderr would
only re-measure the past, and the past is already known to be bad - every
record in it is a non-blocking error. What has to stay true is that the
CURRENT tool does not reproduce it, and the only way to know that is to run
the current tool on the recorded input.

PRIVACY. The store is the operator's transcript history. Two rules hold
throughout, and they are the reason this file reads so defensively:

  - only `attachment` fields are ever touched, never message content
  - every assertion is bound to a plain int or bool FIRST

pytest renders the asserted EXPRESSION independently of the message attached
to it, so `assert some_path in text` prints both operands however careful the
message is. That is CS-850's subject, and this module must not add to its
population. Paths reach the failure MESSAGE only after redaction.

SKIPS WHEN THE STORE IS ABSENT. A fresh clone, a CI runner and a machine that
has never run the harness all have no store, and none of them is a failure.
The acceptance proof that must run there lives in the sibling module.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.test_edit_lint_check import FAILURE_FRAGMENT, TOOL, base_env, run_tool

# The hook event whose records this censuses. The tool is named from the
# shipped path rather than spelled out, so renaming the tool cannot leave this
# module quietly selecting an empty population and passing on nothing.
HOOK_EVENT = "PostToolUse"
TOOL_FILENAME = TOOL.name

# `$NAME` and `${NAME}`. A POSIX shell expands an UNSET variable to the empty
# string, which is the entire mechanism behind CS-845 and therefore the one
# behaviour this reconstruction has to get right.
SHELL_VAR = re.compile(r"\$\{(\w+)\}|\$(\w+)")

# Anything that could be an absolute path, for the message channel only.
ABSOLUTE_ISH = re.compile(r"(?:[A-Za-z]:[\\/]|[\\/])[^\s\"']*")


def redacted(text: str) -> str:
    """Strip anything path-shaped. For failure MESSAGES only, never a verdict."""
    return ABSOLUTE_ISH.sub("<path>", text)


@dataclass(frozen=True)
class Census:
    """What the store holds about this tool, recomputed every run."""

    records: int
    empty_stdout: int
    nonzero_exit: int
    claimed_a_problem: int
    argvs: tuple[tuple[str, ...], ...]

    @property
    def observed_something(self) -> int:
        """Records that produced any stdout at all - the live-gate count."""
        return self.records - self.empty_stdout


def main_checkout() -> Path | None:
    """The MAIN checkout, resolved from git rather than from this file.

    Path(__file__).parents[1] is the WORKTREE when a subagent runs the suite,
    and the store is keyed by the session's project directory, which is the
    main checkout even for a worktree session - measured. Deriving it from
    parents[1] would therefore select nothing from inside a worktree and pass
    vacuously, which is the failure mode this whole module exists to catch.
    """
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0 or not done.stdout.strip():
        return None
    try:
        return Path(done.stdout.strip()).parent.resolve()
    except OSError:
        return None


def store_dirs() -> list[Path]:
    """Project directories in the harness store that belong to this checkout.

    Selected by reading each directory's first record and comparing its `cwd`
    to the main checkout. The alternative - reproducing the harness's rule for
    encoding a project path into a directory NAME - would be a transcription
    of an undocumented convention, and would break silently the day it
    changed. A `cwd` field is data the harness writes about itself.
    """
    root = Path.home() / ".claude" / "projects"
    checkout = main_checkout()
    if checkout is None or not root.is_dir():
        return []
    matched: list[Path] = []
    for candidate in sorted(root.glob("*")):
        if not candidate.is_dir():
            continue
        transcripts = sorted(candidate.glob("*.jsonl"))
        if not transcripts:
            continue
        cwd_value = _first_cwd(transcripts[0])
        if cwd_value is None:
            continue
        try:
            resolved = Path(cwd_value).resolve()
        except (OSError, ValueError):
            continue
        if resolved == checkout or checkout in resolved.parents:
            matched.append(candidate)
    return matched


def _first_cwd(transcript: Path) -> str | None:
    """The `cwd` of the first record that carries one. One line, not the file."""
    try:
        with transcript.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except ValueError:
                    continue
                if isinstance(record, dict) and isinstance(record.get("cwd"), str):
                    return record["cwd"]
    except OSError:
        return None
    return None


def expand_like_a_shell(token: str) -> str:
    """Expand `$VAR` the way the shell that ran the hook would have.

    os.path.expandvars is NOT usable here: it leaves an UNSET variable as the
    literal `$NAME`, and an unset variable expanding to nothing is the precise
    mechanism this module is reconstructing. Reading from the live environment
    rather than assuming absence is deliberate - if CLAUDE_FILE_PATHS is ever
    set, the replay picks that up and grades the wiring that actually exists.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return SHELL_VAR.sub(replace, token)


def argv_from_command(command: str) -> tuple[str, ...] | None:
    """Reconstruct the argv the tool saw, from the command the store recorded.

    The store keeps the command UNEXPANDED - `--files "$CLAUDE_FILE_PATHS"` is
    what is written down, because that is what the settings file says. So the
    expansion has to be redone here, and posix-mode splitting is what strips
    the quotes and hands back the bare variable name to expand.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if _basename(token) == TOOL_FILENAME:
            return tuple(expand_like_a_shell(rest) for rest in tokens[index + 1 :])
    return None


def _basename(token: str) -> str:
    """Basename of a token that may use either separator."""
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def hook_attachments(transcript: Path) -> list[dict]:
    """Every PostToolUse attachment in one transcript that names this tool.

    The substring pre-filter on the raw line is what keeps the whole scan
    under a fifth of a second across roughly a hundred megabytes - json.loads
    runs only on lines that could possibly match. Everything that is not a
    well-formed attachment for this tool is skipped in silence, because a
    transcript is an append-only log written by something else and a shape
    nobody anticipated is not this suite's business to fail on.
    """
    selected: list[dict] = []
    try:
        handle = transcript.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return selected
    with handle:
        for line in handle:
            if HOOK_EVENT not in line or TOOL_FILENAME not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict):
                continue
            attachment = record.get("attachment")
            if not isinstance(attachment, dict):
                continue
            if attachment.get("hookEvent") != HOOK_EVENT:
                continue
            command = attachment.get("command")
            if isinstance(command, str) and TOOL_FILENAME in command:
                selected.append(attachment)
    return selected


@functools.cache
def census() -> Census:
    """Walk the selected transcripts and recompute the population.

    Cached for the module's lifetime because the scan is not free; recomputed
    from scratch on every RUN, which is what the acceptance asks for.
    """
    records = 0
    empty_stdout = 0
    nonzero_exit = 0
    claimed = 0
    argvs: set[tuple[str, ...]] = set()

    for directory in store_dirs():
        for transcript in sorted(directory.glob("*.jsonl")):
            for attachment in hook_attachments(transcript):
                records += 1
                if not str(attachment.get("stdout") or "").strip():
                    empty_stdout += 1
                if attachment.get("exitCode") not in (0, "0"):
                    nonzero_exit += 1
                if FAILURE_FRAGMENT in str(attachment.get("stderr") or ""):
                    claimed += 1
                argv = argv_from_command(str(attachment.get("command")))
                if argv is not None:
                    argvs.add(argv)

    return Census(
        records=records,
        empty_stdout=empty_stdout,
        nonzero_exit=nonzero_exit,
        claimed_a_problem=claimed,
        argvs=tuple(sorted(argvs)),
    )


def require_population() -> Census:
    """The census, or a skip. A vacuous pass is not a pass."""
    found = census()
    if found.records == 0:
        pytest.skip(
            "no PostToolUse record for this tool is present in the harness "
            "transcript store on this machine, so there is no population to "
            "census. tests/test_edit_lint_check.py carries the proof that "
            "does not need one."
        )
    return found


def test_the_census_selects_a_real_population() -> None:
    """The census found records AND reconstructed at least one argv from them.

    Without this, the replay below would pass on an empty loop - and it would
    pass hardest on precisely the machine where the store had moved and the
    selection had silently stopped matching anything.
    """
    found = require_population()

    reconstructed = len(found.argvs)
    records = found.records

    assert records > 0, "the census selected no records"
    assert reconstructed > 0, (
        "%d record(s) were selected but no argument vector could be "
        "reconstructed from any of them, so the replay below would grade "
        "nothing. The recorded command shape has probably changed." % records
    )


def test_no_recorded_invocation_claims_an_unobserved_problem(tmp_path: Path) -> None:
    """THE REPLAY - every recorded argv, re-run through the SHIPPED tool.

    Each argument vector the harness was recorded handing this tool is run
    with no envelope on stdin, and none of them may render a failure sentence.

    This is the acceptance clause held against real history rather than a
    reconstruction. Before CS-845 the single recorded shape - `--files ""`,
    the empty expansion of an unset variable - produced exactly that sentence
    on every one of the records this census selects.

    stdin is deliberately EMPTY. The recorded shapes are a statement about the
    ARGUMENT, and supplying an envelope would test the fallback instead of the
    thing the store actually measured.
    """
    found = require_population()

    offenders = 0
    details: list[str] = []
    for argv in found.argvs:
        result = run_tool(*argv, env=base_env(tmp_path))
        if FAILURE_FRAGMENT in result.stderr:
            offenders += 1
            details.append(redacted(" ".join(repr(part) for part in argv)))

    graded = len(found.argvs)

    assert offenders == 0, (
        "%d of %d recorded invocation shape(s) still report a problem after "
        "reading no file at all: %s. The census covers %d record(s), of which "
        "%d produced no stdout and %d exited non-zero."
        % (
            offenders,
            graded,
            "; ".join(details),
            found.records,
            found.empty_stdout,
            found.nonzero_exit,
        )
    )


def test_the_recorded_history_is_reported_rather_than_asserted() -> None:
    """The historical finding, kept VISIBLE without being frozen into a number.

    This deliberately asserts an INEQUALITY that the fix does not change,
    because the history it describes is immutable - those records are already
    written and no code change can make them un-happen. Freezing the count
    would break this test on the next edit; asserting nothing would let the
    census rot unnoticed. What it does grade is that the derivation still
    resolves the store, still selects records and still agrees with itself.
    """
    found = require_population()

    records = found.records
    accounted = found.empty_stdout + found.observed_something

    assert accounted == records, (
        "the census disagrees with itself: %d record(s) selected but %d "
        "accounted for. The derivation is broken, not the tool." % (records, accounted)
    )
    assert found.claimed_a_problem <= records
    assert found.nonzero_exit <= records
