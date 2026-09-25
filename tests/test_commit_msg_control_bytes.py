"""CS-822 - a control byte in a commit message is REJECTED end to end.

THE DEFECT. The commit-msg byte check built its offender list from bytes ABOVE
0x7E only, so NUL and the rest of the C0 control range were accepted into a
stored commit message. Every arm here drives a REAL commit through the tracked
hook and reads what landed with ``git cat-file``; the sandbox and the commit
drivers are the CS-813 matrix's own (``tests/test_commit_msg_cleanup_matrix.py``),
imported so the two items grade one harness rather than two copies of it.

TAB AND NEWLINE ARE PERMITTED BY NAME, not by omission - which is why this is
its own item rather than a one-character change to a comparison. The hook
carries them in one explicit constant, and an arm here reads that constant out
of the hook's program and proves each of them still lands.

CR IS A CONTROL BYTE, GRADED ON THE STORED IMAGE. On the ``-m`` and ``-F`` paths
git trims every line end BEFORE the hook unless the cleanup is verbatim, so an
ordinary CRLF message file reaches the hook as LF and lands. Under verbatim the
CR is handed over and would be stored, so it refuses. On the editor path git
has trimmed nothing and an explicit ``--cleanup=verbatim`` is invisible to any
hook, so a CRLF buffer refuses: the fail-closed rule the grant recorded under
CS-822 in ``docs/LEDGER.md``. MEASURED before shipping it: this box's default
editor, with no editor configured, is ``vi``, and it saved a git LF buffer as LF.

THE REFUSAL NEVER ECHOES THE BYTE. It names the line, the column and the hex
value, and it runs before any check that echoes message text, so a control
byte cannot reach a terminal through a ``Subject:`` or ``Line:`` echo either.
"""

import ast
from pathlib import Path
from typing import Final

import pytest

from tests.test_commit_msg_cleanup_matrix import (
    HOOK_PATH,
    LEADERS,
    Outcome,
    attempt,
    commit_through_the_editor,
    make_sandbox,
)

CONTROL_REASON: Final = "control byte"
SUBJECT: Final = b"CS-822 - a subject that says what changed\n\n"

# Every C0 control byte the hook must refuse: all of them bar tab and newline.
REFUSED_C0: Final = tuple(byte for byte in range(0x20) if byte not in (0x09, 0x0A))

# The five the grant names, driven down every path. NUL cannot travel in argv,
# so the -m path carries the other four.
NAMED_BYTES: Final = (0x00, 0x01, 0x1B, 0x7F, 0x0D)


def carrying(byte: int) -> bytes:
    """A message whose third line carries ``byte`` mid-line, where no cleanup trims it."""
    return SUBJECT + b"a body line with " + bytes([byte]) + b" inside it\n"


def echoes(outcome: Outcome, byte: int) -> bool:
    """Whether any line of the hook's refusal carries the raw byte.

    Each captured line may END in a CR, because python writes stderr in text
    mode on Windows; that line terminator is not an echo and is trimmed first.
    """
    return any(chr(byte) in line.rstrip("\r") for line in outcome.output)


def drive(tmp_path: Path, payload: bytes, path: str, mode: str | None = None) -> Outcome:
    """One hooked commit of ``payload`` down ``path`` in a fresh sandbox."""
    box = make_sandbox(tmp_path, LEADERS[0])
    return attempt(box, payload, path, mode)


@pytest.mark.parametrize("byte", REFUSED_C0, ids=lambda byte: f"0x{byte:02X}")
def test_every_c0_control_byte_is_refused_on_the_file_path(tmp_path: Path, byte: int) -> None:
    """The whole C0 range bar tab and newline, each by a real ``-F`` commit."""
    outcome = drive(tmp_path, carrying(byte), "file")
    by_rule = outcome.refused_by_this_hook and any(
        CONTROL_REASON in line for line in outcome.output
    )
    assert by_rule, f"control byte 0x{byte:02X} was not refused by its rule:\n{outcome.report}"
    located = any(f"line 3, column 18: 0x{byte:02X}" in line for line in outcome.output)
    assert located, f"the refusal does not name line, column and hex value:\n{outcome.report}"
    echoed = echoes(outcome, byte)
    assert not echoed, f"the refusal echoed the raw 0x{byte:02X} byte"


@pytest.mark.parametrize("byte", NAMED_BYTES, ids=lambda byte: f"0x{byte:02X}")
@pytest.mark.parametrize("path", ["editor", "file", "message"])
def test_each_named_byte_is_refused_on_every_path(tmp_path: Path, path: str, byte: int) -> None:
    """NUL, 0x01, 0x1B, DEL and CR, each refused with HEAD unchanged, the byte never echoed.

    DEL is refused by the long-standing above-0x7E check rather than by the new
    control range, and stays refused; the other four are CS-822's.
    """
    if path == "message" and byte == 0x00:
        pytest.skip("NOT RUN: a NUL cannot be carried in a command-line argument")
    outcome = drive(tmp_path, carrying(byte), path)
    echoed = echoes(outcome, byte)
    assert outcome.refused_by_this_hook, f"0x{byte:02X} landed on {path}:\n{outcome.report}"
    assert not echoed, f"the refusal echoed the raw 0x{byte:02X} byte on {path}"


@pytest.mark.parametrize("path", ["editor", "file", "message"])
def test_tab_and_newline_each_land_and_are_stored(tmp_path: Path, path: str) -> None:
    """The two permitted control bytes, proven to reach the stored object."""
    message = b"CS-822 -\ta tab in the subject\n\nA body\twith a tab.\nAnd a second line.\n"
    outcome = drive(tmp_path, message, path)
    assert outcome.accepted, f"tab and newline were refused on {path}:\n{outcome.report}"
    stored_verbatim = outcome.stored == message
    assert stored_verbatim, f"the stored message lost a tab or a newline on {path}"


def test_the_permitted_set_is_one_named_constant_naming_tab_and_newline() -> None:
    """Permitted BY NAME: the hook's program carries exactly one such constant."""
    source = HOOK_PATH.read_bytes().decode("ascii")
    start = source.index("<<'CLOCKSPEED_COMMIT_MSG'\n") + len("<<'CLOCKSPEED_COMMIT_MSG'\n")
    program = source[start : source.index("\nCLOCKSPEED_COMMIT_MSG\n", start)]
    values = [
        ast.literal_eval(node.value)
        for node in ast.walk(ast.parse(program))
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PERMITTED_CONTROLS" for t in node.targets)
    ]
    assert values == [{0x09: "tab", 0x0A: "newline"}], f"permitted controls: {values}"


def test_a_crlf_message_file_lands_under_the_default_cleanup(tmp_path: Path) -> None:
    """THE ORDINARY LANE COMMIT: a CRLF ``-F`` file, as a Windows writer leaves it.

    git trims every line end before the hook, so the hook sees LF and the object
    stores no CR. Refusing this would refuse ordinary commits on this machine.
    """
    outcome = drive(tmp_path, SUBJECT.replace(b"\n", b"\r\n") + b"A body.\r\n", "file")
    assert outcome.accepted, f"an ordinary CRLF message file was refused:\n{outcome.report}"
    stored_cr = outcome.stored.count(b"\r")
    assert stored_cr == 0, "git stored a CR, so the premise of this arm is wrong"


def test_a_crlf_message_on_the_command_line_lands_under_the_default_cleanup(
    tmp_path: Path,
) -> None:
    """The same for ``-m``, which a double-quoted CRLF here-string produces."""
    outcome = drive(tmp_path, SUBJECT.replace(b"\n", b"\r\n") + b"A body.\r\n", "message")
    assert outcome.accepted, f"an ordinary CRLF -m message was refused:\n{outcome.report}"


def test_a_crlf_message_file_under_verbatim_is_refused(tmp_path: Path) -> None:
    """Under verbatim git hands the CRs over AND stores them, so the hook refuses."""
    payload = SUBJECT.replace(b"\n", b"\r\n") + b"A body.\r\n"
    outcome = drive(tmp_path, payload, "file", "verbatim")
    assert outcome.refused_by_this_hook, f"a stored CR landed:\n{outcome.report}"


def test_a_crlf_editor_buffer_is_refused_because_verbatim_cannot_be_ruled_out(
    tmp_path: Path,
) -> None:
    """The fail-closed ruling: an explicit --cleanup=verbatim is invisible to the hook.

    This is the one CR refusal that can meet an otherwise ordinary commit, which
    is why the default editor on this machine was measured first (module note).
    """
    box = make_sandbox(tmp_path, LEADERS[0])
    payload = SUBJECT.replace(b"\n", b"\r\n") + b"A body.\r\n"
    outcome = commit_through_the_editor(box, payload, verify=True)
    assert outcome.refused_by_this_hook, f"a CRLF editor buffer landed:\n{outcome.report}"


@pytest.mark.parametrize(
    ("label", "payload", "echo"),
    [
        ("over-long subject", b"C" * 80 + b"\x1b\n", "Subject:"),
        ("trailer", SUBJECT + b"Co-authored-by: A Person\x1b <a@example.invalid>\n", "Line:"),
    ],
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_the_control_check_runs_before_any_site_that_echoes_message_text(
    tmp_path: Path, label: str, payload: bytes, echo: str
) -> None:
    """A message that would also trip an ECHOING check is refused as a control byte first."""
    outcome = drive(tmp_path, payload, "file")
    by_control = outcome.refused_by_this_hook and any(
        CONTROL_REASON in line for line in outcome.output
    )
    assert by_control, f"{label}: not refused by the control check first:\n{outcome.report}"
    echoed = any(echo in line for line in outcome.output)
    assert not echoed, f"{label}: the refusal echoed message text through {echo!r}"
