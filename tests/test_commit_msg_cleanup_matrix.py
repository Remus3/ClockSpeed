"""CS-813 - no stored violation lands, whichever cleanup mode, path and leader git uses.

THE ROOT FACT. git runs its message cleanup AFTER the commit-msg hook, so every
check the hook makes is a PREDICTION of the stored bytes. The old hook predicted
one cleanup mode out of five: it dropped every '#' line and cut at any '#' line
carrying '>8', whatever git was about to do. Four leaks followed, each measured
with a real commit landing and the hook silent: a long comment first line
stored as the subject, a comment line carrying a byte above 0x7E, a '#' line
that a remapped comment leader turns into content, and the trailing whitespace
that ``--cleanup=verbatim`` keeps on the subject.

THE MATRIX. Every cell is a cleanup mode (none given, verbatim, whitespace,
strip, scissors, default) by a commit path (the editor with git's own template,
``-m``, ``-F``) by a comment leader (the default, ``core.commentChar`` and
``core.commentString`` remapped). An explicit ``--cleanup`` on the editor path is
IN the matrix, because that is exactly the combination no hook can observe.

GIT IS THE ORACLE, AND THE STORED BYTES ARE READ RAW. What a cell stores is read
back with ``git cat-file commit HEAD`` and never through ``%s`` or ``%B``:
``%s`` renders 70 for a commit whose object stores 75 (the CS-813 note), so the
prescribed oracle is blind to the verbatim leak and a suite built on it stays
green while the escape is live.

THE DIRECTIONS ASSERTED IN EVERY CELL.

- NOTHING VIOLATING LANDS. A shape the hook accepts is read back, and its stored
  bytes must carry no byte above 0x7E and no subject over the cap. This is the
  acceptance, and it is what the old hook failed.
- A CLEAN CONTROL LANDS, so a hook that refuses everything cannot pass.
- THE CELL IS NOT VACUOUS. At least one shape the hook refused is committed again
  with ``--no-verify``, and git must then STORE a violation - so every cell
  proves a real stored violation was stopped, not merely that something was.

A REFUSED SHAPE WHOSE UNHOOKED COMMIT STORES CLEAN BYTES IS PERMITTED, and that
is the ruling rather than a gap. The hook cannot see an explicit ``--cleanup``
or ``-v``, so it grades every cleanup mode it cannot rule out and refuses if any
of them would store a violation. The adjudicator's grant recorded under CS-813
in ``docs/LEDGER.md`` chose that fail-closed rule over declaring the unobservable
modes a residual.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE, as in ``tests/test_commit_msg_gate.py``:
tmp_path sits under the real user profile, so every result is reduced to a bool,
an int, a label or the hook's own output before it is asserted on.
"""

import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests import git_env

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOK_PATH: Final = REPO_ROOT / ".githooks" / "commit-msg"

GIT_TIMEOUT: Final = 120
TOOL_PREFIX: Final = "clockspeed commit-msg"
REJECTED: Final = "REJECTED"

# Mirrors the hook's own LIMIT, so a change to either side shows up as a failure.
SUBJECT_LIMIT: Final = 72
MAX_ASCII_BYTE: Final = 0x7E

# git's own blank-line whitespace (its sane_ctype space class). A form feed or a
# vertical tab is NOT whitespace to git, so a line of them is a subject.
GIT_BLANK: Final = b" \t\r"

# git's scissors line WITHOUT its leader, measured from git 2.53.
CUT: Final = "------------------------ >8 ------------------------"

# U+2014, built at run time so this file stays 7-bit ASCII on disk.
EM_DASH: Final = chr(0x2014)

FIXTURE_NAME: Final = "CS-813 Fixture"
FIXTURE_EMAIL: Final = "cs813@example.invalid"
TRACKED_NAME: Final = "tracked.txt"
MESSAGE_NAME: Final = "commit-message.txt"
PAYLOAD_NAME: Final = "editor-payload.txt"
PAYLOAD_VARIABLE: Final = "CS813_EDITOR_PAYLOAD"

# The scripted editor PREPENDS the payload to the buffer git opened it on, so
# the editor path keeps git's own template - the ordinary editor commit - and a
# verbatim cell really does store that template. git runs the editor value as
# `sh -c '<value> "$@"'`, so a function is a portable way to name the file.
EDITOR_COMMAND: Final = (
    'cs813_edit() { cat "$' + PAYLOAD_VARIABLE + '" "$1" > "$1.cs813" && mv "$1.cs813" "$1"; }; '
    "cs813_edit"
)

CONTROL: Final = b"CS-813 - an ordinary subject that says what changed\n\nAn ordinary body.\n"

PATHS: Final = ("editor", "message", "file")
MODES: Final = (None, "verbatim", "whitespace", "strip", "scissors", "default")


class Leader(NamedTuple):
    """One comment-leader configuration: the git key that sets it, and its text."""

    label: str
    key: str | None
    text: str


LEADERS: Final = (
    Leader("default", None, "#"),
    Leader("commentChar", "core.commentChar", ";"),
    Leader("commentString", "core.commentString", "//"),
)


class Shape(NamedTuple):
    """A message that stores a violation under at least one cell's cleanup."""

    label: str
    payload: bytes


def shapes_for(leader: Leader) -> tuple[Shape, ...]:
    """The four CS-813 leaks, spelled for this cell's comment leader.

    The comment-line shapes use the CELL'S leader, so git strips them exactly
    where it strips comments. The '#' shapes exist for a remapped leader, where
    a '#' line is ordinary content that the old pre-filter dropped anyway.
    """
    lead = leader.text
    shapes = [
        Shape(
            "a long comment line first",
            (lead + " " + "c" * 90 + "\n\nCS-813 - a short subject\n").encode("utf-8"),
        ),
        Shape(
            "a '#' line carrying an em dash",
            ("CS-813 - a short subject\n\n# an em " + EM_DASH + " dash\n").encode("utf-8"),
        ),
        Shape(
            "an em dash below the scissors line",
            (
                "CS-813 - a short subject\n\n" + lead + " " + CUT + "\nbelow " + EM_DASH + " it\n"
            ).encode("utf-8"),
        ),
        Shape(
            "trailing whitespace on the subject",
            ("C" * 70 + " " * 5 + "\n").encode("utf-8"),
        ),
        # The mirror of the first shape: where git strips the short comment,
        # the long line under it becomes the stored subject. Only a hook that
        # knows the cell's leader can see that.
        Shape(
            "a short comment line above a long one",
            (lead + " c\n" + "C" * 80 + "\n").encode("utf-8"),
        ),
    ]
    if lead != "#":
        shapes.append(
            Shape(
                "a long '#' line first",
                ("# " + "c" * 90 + "\n\nCS-813 - a short subject\n").encode("utf-8"),
            )
        )
    return tuple(shapes)


class Sandbox(NamedTuple):
    """A throwaway repository whose only wired hook is commit-msg.

    THE REPR WITHHOLDS EVERY PATH. pytest renders reachable fixture values in a
    failure report, and both fields carry absolute paths under the user profile.
    """

    work: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-813 sandbox repository, paths withheld>"


class Outcome(NamedTuple):
    """The measured result of one real ``git commit``."""

    returncode: int
    moved: bool
    stored: bytes
    output: tuple[str, ...]

    @property
    def accepted(self) -> bool:
        """Whether git succeeded AND a commit landed."""
        return self.returncode == 0 and self.moved

    @property
    def refused_by_this_hook(self) -> bool:
        """Whether THIS hook refused and nothing was committed."""
        return (
            self.returncode != 0
            and not self.moved
            and any(line.startswith(TOOL_PREFIX) and REJECTED in line for line in self.output)
        )

    @property
    def report(self) -> str:
        """A path-free rendering safe to put in an assertion message."""
        shown = "\n".join(self.output) if self.output else "(no hook output)"
        return f"exit={self.returncode} moved={self.moved}\n{shown}"


def violates(stored: bytes) -> bool:
    """Whether STORED message bytes break the CS-813 rule. The oracle's grader.

    A byte above 0x7E anywhere, or a subject - the first line with anything but
    git whitespace on it, UNTRIMMED, as the object stores it - over the cap.
    """
    if any(byte > MAX_ASCII_BYTE for byte in stored):
        return True
    for line in stored.split(b"\n"):
        if line.strip(GIT_BLANK):
            return len(line) > SUBJECT_LIMIT
    return False


def hook_output(stderr: bytes) -> tuple[str, ...]:
    """Keep only the hook's own lines, so no git-rendered path can reach a report."""
    text = stderr.decode("utf-8", "replace")
    return tuple(
        line for line in text.split("\n") if line.startswith((TOOL_PREFIX, "  ")) and line.strip()
    )


def run_git(
    box: Sandbox, *args: str, extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run git inside the sandbox, bytes in and bytes out."""
    env = dict(box.env)
    if extra:
        env.update(extra)
    return subprocess.run(
        ["git", *args],
        cwd=str(box.work),
        capture_output=True,
        timeout=GIT_TIMEOUT,
        env=env,
        check=False,
    )


def head_of(box: Sandbox) -> str:
    """The current HEAD commit id."""
    return run_git(box, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def stored_message(box: Sandbox) -> bytes:
    """The message bytes the HEAD commit object stores - never a log format."""
    raw = run_git(box, "cat-file", "commit", "HEAD").stdout
    return raw.split(b"\n\n", 1)[1]


def make_sandbox(tmp_path: Path, leader: Leader) -> Sandbox:
    """A real repository with the tracked hook wired and one commit in it.

    The operator's own git configuration is cut off, every inherited repository
    pointer is scrubbed (tests/git_env.py), and the harness's GIT_EDITOR is
    removed, so only what a cell sets can answer for git here.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / "commit-msg"
    installed.write_bytes(HOOK_PATH.read_bytes())
    installed.chmod(0o755)
    work = tmp_path / "work"
    work.mkdir()

    env = git_env.scrubbed_env()
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    env.pop("GIT_EDITOR", None)
    box = Sandbox(work=work, env=env)

    assert run_git(box, "init", "-q", "-b", "cs813-sandbox").returncode == 0
    settings = [
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("core.hooksPath", str(hooks)),
    ]
    if leader.key is not None:
        settings.append((leader.key, leader.text))
    for key, value in settings:
        written = run_git(box, "config", key, value).returncode == 0
        assert written, f"{key} could not be written in the sandbox"
    readback = run_git(box, "config", "--get", "core.hooksPath").stdout.decode().strip()
    took = readback == str(hooks)
    assert took, "core.hooksPath did not take in the sandbox"

    (work / TRACKED_NAME).write_bytes(b"first\n")
    assert run_git(box, "add", TRACKED_NAME).returncode == 0
    first = run_git(box, "commit", "-q", "--no-verify", "-m", "CS-813 - sandbox root")
    assert first.returncode == 0, "the sandbox could not make its root commit"
    return box


def staged_a_change(box: Sandbox) -> bool:
    """Append one line to the tracked file and stage it; whether that worked.

    Kept apart from every assertion, so no path-bearing local is in a frame
    that pytest renders under ``-l`` (tests/test_locals_rendering.py).
    """
    with (box.work / TRACKED_NAME).open("ab") as handle:
        handle.write(b"one more line\n")
    return run_git(box, "add", TRACKED_NAME).returncode == 0


def attempt(
    box: Sandbox, payload: bytes, path: str, mode: str | None, *, verify: bool = True
) -> Outcome:
    """Stage a real change and drive a real ``git commit`` down ``path``."""
    assert staged_a_change(box), "the change could not be staged"

    flags = [] if mode is None else ["--cleanup=" + mode]
    if not verify:
        flags.append("--no-verify")
    extra: dict[str, str] = {}
    if path == "editor":
        payload_file = box.work.parent / PAYLOAD_NAME
        payload_file.write_bytes(payload)
        extra = {"GIT_EDITOR": EDITOR_COMMAND, PAYLOAD_VARIABLE: str(payload_file)}
        args = ["commit", *flags]
    elif path == "message":
        args = ["commit", "-m", payload.decode("utf-8"), *flags]
    else:
        message_file = box.work.parent / MESSAGE_NAME
        message_file.write_bytes(payload)
        args = ["commit", "-F", str(message_file), *flags]

    before = head_of(box)
    proc = run_git(box, *args, extra=extra)
    moved = head_of(box) != before
    stored = stored_message(box) if moved else b""
    return Outcome(proc.returncode, moved, stored, hook_output(proc.stderr))


def cell_id(value: object) -> str:
    """A readable parametrize id for a mode, a path or a leader."""
    if isinstance(value, Leader):
        return "leader-" + value.label
    if value is None:
        return "mode-unset"
    return str(value)


@pytest.mark.parametrize("leader", LEADERS, ids=cell_id)
@pytest.mark.parametrize("mode", MODES, ids=lambda mode: "mode-" + cell_id(mode))
@pytest.mark.parametrize("path", PATHS, ids=lambda path: "path-" + path)
def test_no_stored_violation_lands_in_any_cell(
    tmp_path: Path, path: str, mode: str | None, leader: Leader
) -> None:
    """THE ACCEPTANCE, one cell at a time, with both directions and a vacuity floor."""
    box = make_sandbox(tmp_path, leader)

    control = attempt(box, CONTROL, path, mode)
    assert control.accepted, f"the clean control was refused:\n{control.report}"
    control_clean = not violates(control.stored)
    assert control_clean, "the clean control stored a violation, so the cell is misbuilt"

    landed: list[str] = []
    stopped: list[str] = []
    for shape in shapes_for(leader):
        outcome = attempt(box, shape.payload, path, mode)
        if outcome.accepted:
            if violates(outcome.stored):
                landed.append(shape.label)
            continue
        assert outcome.refused_by_this_hook, (
            f"{shape.label!r} was stopped, but not by this hook:\n{outcome.report}"
        )
        if stopped:
            # The floor below needs ONE measured stop; further unhooked commits
            # would cost time and assert nothing.
            continue
        unhooked = attempt(box, shape.payload, path, mode, verify=False)
        assert unhooked.accepted, f"{shape.label!r} could not be committed with --no-verify"
        if violates(unhooked.stored):
            stopped.append(shape.label)

    assert not landed, f"a stored violation LANDED with the hook silent: {landed}"
    assert stopped, (
        "no shape both stored a violation and was refused in this cell, so the "
        "cell proves nothing about the hook"
    )


def test_a_verbose_editor_commit_with_an_ascii_diff_still_lands(tmp_path: Path) -> None:
    """``git commit -v`` puts the whole diff below git's scissors line in the buffer.

    The hook cannot see ``-v``, so it grades that buffer uncut as well. This is
    the ordinary control: a verbose commit whose diff is plain ASCII must land,
    and git's own cut must still keep the diff out of the stored message.
    """
    box = make_sandbox(tmp_path, LEADERS[0])
    outcome = commit_through_the_editor(box, CONTROL, "-v", verify=True)
    assert outcome.accepted, f"an ordinary verbose commit was refused:\n{outcome.report}"
    diff_stored = b"diff --git" in outcome.stored
    assert not diff_stored, "git stored the verbose diff, so the cut did not happen"


def test_a_hash_line_that_is_not_gits_scissors_line_no_longer_ends_the_message(
    tmp_path: Path,
) -> None:
    """THE ONE BASE REFUSAL THIS ITEM LIFTS, enumerated with its proof.

    The old pre-filter stopped at ANY '#' line carrying '>8', so a message whose
    only content followed such a line read as EMPTY and was refused. git cuts
    only at its exact scissors line, so it stores the content. The lift is
    permitted only because every image is compliant, and that is measured here:
    the message is committed unhooked under every cleanup mode and each stored
    image is graded, before the hooked commit is required to land.
    """
    box = make_sandbox(tmp_path, LEADERS[0])
    message = b"# not a scissors line >8\nCS-813 - the subject after it\n"
    for mode in MODES:
        unhooked = attempt(box, message, "file", mode, verify=False)
        assert unhooked.accepted, f"git refused the message unhooked under {mode}"
        clean = not violates(unhooked.stored)
        assert clean, f"the message stores a violation under {mode}, so no lift is allowed"
    outcome = attempt(box, message, "file", None)
    assert outcome.accepted, f"a compliant message was refused:\n{outcome.report}"


def test_a_message_that_is_only_a_comment_is_still_refused_as_empty(tmp_path: Path) -> None:
    """NOT A LIFT: the empty refusal still fires when ANY stored image is empty.

    Under ``-F`` git keeps a '#' line by default, so the whole-message image is
    not empty - but ``--cleanup=strip`` stores nothing, and the hook cannot see
    that flag. The old hook refused this message, and so must this one.
    """
    box = make_sandbox(tmp_path, LEADERS[0])
    outcome = attempt(box, b"# only a comment line\n", "file", None)
    refused = outcome.refused_by_this_hook and any("empty" in line for line in outcome.output)
    assert refused, f"a comment-only message was not refused as empty:\n{outcome.report}"


def commit_through_the_editor(box: Sandbox, payload: bytes, *flags: str, verify: bool) -> Outcome:
    """One real editor-path commit with extra flags, hooked or with --no-verify."""
    assert staged_a_change(box), "the change could not be staged"
    payload_file = box.work.parent / PAYLOAD_NAME
    payload_file.write_bytes(payload)
    extra = {"GIT_EDITOR": EDITOR_COMMAND, PAYLOAD_VARIABLE: str(payload_file)}
    args = ["commit", *flags] + ([] if verify else ["--no-verify"])
    before = head_of(box)
    proc = run_git(box, *args, extra=extra)
    moved = head_of(box) != before
    stored = stored_message(box) if moved else b""
    return Outcome(proc.returncode, moved, stored, hook_output(proc.stderr))


def test_the_last_comment_setting_wins_as_it_does_for_git(tmp_path: Path) -> None:
    """core.commentChar and core.commentString are ONE setting; the later line wins.

    Set ';' first and '//' after it. git then strips the '//' line, so the long
    line under it is the stored subject. A hook that took the FIRST setting would
    model ';', see a short '//' subject in every image, and let it land.
    """
    box = make_sandbox(tmp_path, LEADERS[1])
    assert run_git(box, "config", "core.commentString", "//").returncode == 0
    payload = b"// c\n" + b"C" * 80 + b"\n"

    unhooked = commit_through_the_editor(box, payload, verify=False)
    stored_bad = unhooked.accepted and violates(unhooked.stored)
    assert stored_bad, "git did not store the long line as the subject, so the arm is vacuous"
    outcome = commit_through_the_editor(box, payload, verify=True)
    assert outcome.refused_by_this_hook, f"the '//'-led message landed:\n{outcome.report}"


def test_an_auto_comment_leader_is_modelled_over_every_leader_git_can_pick(
    tmp_path: Path,
) -> None:
    """core.commentChar=auto: git picks a leader no line of the message starts with.

    The -F file here starts with '#', so git picks ';' for this commit. The
    editor then adds a ';' line above a long one; git strips the ';' line and
    stores the long line as the subject. A hook that modelled only '#' would see
    the short ';' line as the subject in every image and let it land.
    """
    box = make_sandbox(tmp_path, Leader("auto", "core.commentChar", "auto"))
    unhooked, outcome = edit_a_hash_led_file_twice(box, b"; c\n" + b"C" * 80 + b"\n")
    stored_bad = unhooked.accepted and violates(unhooked.stored)
    assert stored_bad, "git did not store the long line as the subject, so the arm is vacuous"
    assert outcome.refused_by_this_hook, f"the ';'-led message landed:\n{outcome.report}"


def edit_a_hash_led_file_twice(box: Sandbox, payload: bytes) -> tuple[Outcome, Outcome]:
    """``-e -F`` over a file whose first line starts with '#': unhooked, then hooked.

    No assertion lives in this frame, so the message file's path never sits in
    a frame pytest renders under ``-l``.
    """
    source = box.work.parent / MESSAGE_NAME
    source.write_bytes(b"# a first line that starts with a hash\n")
    unhooked = commit_through_the_editor(box, payload, "-e", "-F", str(source), verify=False)
    hooked = commit_through_the_editor(box, payload, "-e", "-F", str(source), verify=True)
    return unhooked, hooked
