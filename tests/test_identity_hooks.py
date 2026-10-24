"""CS-1290 - the kit v13 identity lines, graded through the REAL tracked hooks.

FLEET-COMMON 17 (kit v13): no commit reaching a remote carries an AI or bot
attribution line, or a non-operator author or committer. The CS-1290 frozen-file
grant (``docs/LEDGER.md``, 2026-10-09) wires ``ops/fleet_kit/fleet_identity.py``
into ``.githooks/commit-msg`` - last, after every check that may reject, and
never rejecting itself - and into ``.githooks/pre-push`` - first, fed the ref
list the CS-954 capture already read, refusing on any violation.

Every arm drives a real ``git commit`` or ``git push`` through a sandbox copy of
the tracked hook built by the module that already owns that sandbox, so these
arms grade the shipped bytes and nothing else. The positive controls - an
ordinary commit and an ordinary push that land - are those modules' own, run on
the same sandboxes.

Each arm was RED on the pre-grant hooks: the stripped lines were stored, and
the refused pushes landed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

import pytest

from tests import test_commit_msg_gate as commit_msg_arms
from tests import test_pre_push_suite_floor as floor_arms
from tests.fleet_hook_kit import (
    HOOK_KIT_FILES,
    KIT_DIR,
    OPERATOR_IDENT_KEY,
    SUITE_DIR_ENV,
    commit_margin_env,
    install_hook_kit,
    suite_dir_env,
)
from tests.test_commit_msg_gate import Sandbox as CommitSandbox
from tests.test_commit_msg_gate import attempt
from tests.test_pre_push_suite_floor import (
    BRANCH,
    PASSING_TEST,
    Environment,
    git,
    make_sandbox,
    suite_of,
    tip,
)

# The two owning modules' fixtures, bound here under names pytest resolves.
# The commit-msg sandbox asks for ``isolated`` by name, so that module's takes
# the plain name; the floor module's is bound under a second one.
isolated = commit_msg_arms.isolated
sandbox = commit_msg_arms.sandbox
push_isolated = floor_arms.isolated


@pytest.fixture
def commit_box(request: pytest.FixtureRequest) -> CommitSandbox:
    """The commit-msg module's sandbox, with the kit files its last line runs."""
    box: CommitSandbox = request.getfixturevalue("sandbox")
    install_hook_kit(box.work)
    return box


@pytest.fixture
def push_env(request: pytest.FixtureRequest) -> Environment:
    """The floor module's isolated push environment."""
    env: Environment = request.getfixturevalue("push_isolated")
    # CS-1349: the gate's commit margin is 0 for a sandbox push (grant clause C).
    env.variables.update(commit_margin_env())
    return env


#: A harness-style session trailer: a ``Claude-*:`` line the kit strips.
SESSION_TRAILER: Final = "Claude-Session: https://claude.ai/code/session_cs1290fixture"
#: The generated-with line the kit strips.
GENERATED_LINE: Final = "Generated with Claude Code"
SUBJECT: Final = "CS-1290: an ordinary subject that says what changed"
#: A synthetic NON-operator identity: neither the sandbox committer nor a bot.
OUTSIDER: Final = "CS-1290 Outsider <cs1290-outsider@example.invalid>"


def identity_refused(stderr: str) -> bool:
    """True when the kit's identity line printed a refusal, not its clean line."""
    return any(
        line.strip().startswith("IDENTITY:") and "clean" not in line for line in stderr.splitlines()
    )


def stored_message(box: CommitSandbox) -> str:
    """The message git stored for HEAD."""
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=60,
        env=box.env,
        check=False,
    )
    assert proc.returncode == 0, "the stored message could not be read"
    return proc.stdout


def test_commit_msg_strips_a_session_trailer_and_a_generated_line(
    commit_box: CommitSandbox,
) -> None:
    """The commit LANDS, and the stored message no longer carries either line."""
    message = f"{SUBJECT}\n\nAn ordinary body.\n\n{GENERATED_LINE}\n\n{SESSION_TRAILER}\n"
    outcome = attempt(commit_box, message)
    assert outcome.accepted, f"the commit was refused:\n{outcome.report}"
    stored = stored_message(commit_box)
    assert SUBJECT in stored, "the subject did not survive the strip"
    assert "Claude-Session" not in stored, "the session trailer was stored"
    assert GENERATED_LINE not in stored, "the generated-with line was stored"


def test_commit_msg_leaves_an_ordinary_message_byte_for_byte(commit_box: CommitSandbox) -> None:
    """The control: nothing to strip, so the stored message is the one offered."""
    message = f"{SUBJECT}\n\nAn ordinary body naming no tool.\n"
    outcome = attempt(commit_box, message)
    assert outcome.accepted, f"an ordinary commit was refused:\n{outcome.report}"
    assert stored_message(commit_box).rstrip("\n") == message.rstrip("\n")


def test_pre_push_refuses_when_no_operator_identity_is_set(
    tmp_path: Path, push_env: Environment
) -> None:
    """No ``fleet.operatorIdent`` in LOCAL config = every push refused."""
    box = make_sandbox(tmp_path, push_env, tests=suite_of(PASSING_TEST, 3))
    unset = git(box, "config", "--unset-all", OPERATOR_IDENT_KEY)
    assert unset.returncode == 0, "the operator identity could not be unset"
    seeded = tip(box, remote=True)
    made = git(box, "commit", "-q", "--allow-empty", "-m", SUBJECT)
    assert made.returncode == 0, "the offered commit could not be made"
    # Bound to scalars first: an asserted CompletedProcess renders its output,
    # which names the sandbox path.
    proc = git(box, "push", "origin", BRANCH)
    pushed, said = proc.returncode, identity_refused(proc.stderr)
    assert pushed != 0, "the push exited 0"
    assert said, "no IDENTITY: refusal line on stderr"
    assert tip(box, remote=True) == seeded, "the remote moved"


def test_pre_push_refuses_a_non_operator_author(tmp_path: Path, push_env: Environment) -> None:
    """One commit authored outside the operator set: the push is refused."""
    box = make_sandbox(tmp_path, push_env, tests=suite_of(PASSING_TEST, 3))
    seeded = tip(box, remote=True)
    made = git(box, "commit", "-q", "--allow-empty", "--author", OUTSIDER, "-m", SUBJECT)
    assert made.returncode == 0, "the outsider commit could not be made"
    # Bound to a scalar first: an asserted CompletedProcess renders its output,
    # which names the sandbox path.
    proc = git(box, "push", "origin", BRANCH)
    pushed, said = proc.returncode, identity_refused(proc.stderr)
    assert said, "no IDENTITY: refusal line on stderr"
    assert pushed != 0, "a non-operator author was pushed"
    assert tip(box, remote=True) == seeded, "the remote moved"


def test_pre_push_refuses_an_ai_attribution_line(tmp_path: Path, push_env: Environment) -> None:
    """A trailer that bypassed commit-msg (``--no-verify``) is still refused at push."""
    box = make_sandbox(tmp_path, push_env, tests=suite_of(PASSING_TEST, 3))
    seeded = tip(box, remote=True)
    message = f"{SUBJECT}\n\n{SESSION_TRAILER}\n"
    made = git(box, "commit", "-q", "--no-verify", "--allow-empty", "-m", message)
    assert made.returncode == 0, "the trailer commit could not be made"
    # Bound to a scalar first: an asserted CompletedProcess renders its output,
    # which names the sandbox path.
    proc = git(box, "push", "origin", BRANCH)
    pushed, said = proc.returncode, identity_refused(proc.stderr)
    assert said, "no IDENTITY: refusal line on stderr"
    assert pushed != 0, "an AI attribution line was pushed"
    assert tip(box, remote=True) == seeded, "the remote moved"


def test_the_sandbox_helper_copies_each_hook_kit_file_byte_for_byte(tmp_path: Path) -> None:
    """The helper every hook sandbox leans on installs the real kit bytes, all of them."""
    target = install_hook_kit(tmp_path)
    copied = sorted(path.name for path in target.iterdir())
    assert copied == sorted(HOOK_KIT_FILES), f"the helper installed {copied}"
    differing = [
        name
        for name in HOOK_KIT_FILES
        if (target / name).read_bytes() != (KIT_DIR / name).read_bytes()
    ]
    assert differing == [], f"copied bytes differ from the kit: {differing}"
    gate = suite_dir_env(tmp_path)[SUITE_DIR_ENV]
    assert Path(gate).parent == tmp_path, "the gate directory is not under the arm's own tmp"
