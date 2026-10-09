"""CS-954 - the pre-push gate must not let a ref move out from under its verdict.

THE INCIDENT, measured 2026-09-07 in this repository. ``git push origin main``
was invoked with local ``main`` at one commit; the hook ran the whole suite to
completion and git printed that commit's range and exited 0; the forge afterwards
held a LATER commit, created by the same session while the hook was still
running. The forge's own record settles it: no CI run has ever existed for the
SHA the hook graded, while a push-event run exists for the later one, created
three seconds after the push completed. One push event, and its tip was never
graded.

WHAT THIS MODULE DOES NOT CLAIM. The MECHANISM is not established. Two controlled
reproductions on 2026-09-08 - one over a plain local path, one over ``file://`` -
advanced the local ref mid-hook and BOTH shipped exactly the SHA the hook was
handed, with a control proving the ref really had moved by the time the hook
returned. So on this git, over local transports, the race does not bite. The real
incident used HTTPS to a forge, and the difference is unexplained.

WHICH IS WHY THE ARMS BELOW GRADE THE HOOK'S REFUSAL AND NEVER GIT'S TRANSPORT.
A test that asserted "the remote holds the graded SHA" would pass today, on this
machine, for a reason that has nothing to do with the defect - the local
transport already behaves. The property actually worth having is
mechanism-agnostic: **when the local ref no longer matches what git handed the
hook on stdin, the hook refuses.** Whichever half of the unestablished mechanism
is true, that is safe - either git ships the graded SHA and the check never
fires, or it ships a later one and the push is blocked before it can.

THE HOOK HAS NEVER READ ITS STDIN. ``.githooks/pre-push`` runs pytest with
stdin closed and nothing in it consumes the ref list git supplies, so it grades
the WORKING TREE and never learns which commits are being pushed. That is the
root, and it is why the gate can report on a commit that never ships and stay
silent about one that does.
"""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.fleet_hook_kit import OPERATOR_IDENT_KEY, install_hook_kit, suite_dir_env
from tests.git_env import gnu_timeout_first, program_on_child_path, scrub
from tests.pre_push_floor import differs_only_on_floor_line, wired_hook_bytes

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
HOOKS_DIR: Final = REPO_ROOT / ".githooks"
PRE_PUSH: Final = "pre-push"

GIT_TIMEOUT: Final = 300
SANDBOX_BRANCH: Final = "cs954-sandbox"

#: A SECOND branch, so one push event can carry a deletion AND an update at
#: once. CS-989 skips the suite only when EVERY line is a deletion, and a
#: single-branch sandbox cannot construct the mixed push that grades that word.
DOOMED_BRANCH: Final = "cs989-doomed"
FIXTURE_NAME: Final = "CS-954 Fixture"
FIXTURE_EMAIL: Final = "cs954@example.invalid"

#: How long the sandbox suite blocks for, so a commit can land mid-hook. Long
#: enough that the advance is comfortably inside the window on a loaded machine,
#: short enough that the module stays cheap.
SUITE_SECONDS: Final = 8.0

#: When the mid-hook commit is made, measured from the push starting. It must be
#: after the hook's interpreter probes and inside the suite's window.
ADVANCE_AT: Final = 3.0

#: Written by the sandbox suite when it actually executes. PRESENCE IS NOT
#: FIRING: without this, a hook that never ran and a hook that ran and passed are
#: the same observation, and every arm below would pass for the wrong reason.
MARKER_NAME: Final = "suite_really_ran.txt"

HOOK_BANNER: Final = "clockspeed pre-push"

ENVIRONMENT_REPR: Final = "<environment withheld>"


class Environment(NamedTuple):
    """The child environment, wrapped so pytest cannot render its contents.

    A failing test renders its arguments, and the raw mapping carries the Windows
    account name and absolute home paths (CLAUDE.md non-negotiable 3).
    """

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Sandbox(NamedTuple):
    """A throwaway repository with the real pre-push hook wired and a bare remote."""

    work: Path
    hooks: Path
    remote: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-954 sandbox, paths withheld>"


class Race(NamedTuple):
    """One real push raced against one real commit."""

    returncode: int
    graded_tip: str
    advanced_tip: str
    remote_tip: str
    suite_ran: bool
    hook_said: tuple[str, ...]

    @property
    def blocked(self) -> bool:
        """Whether git refused to complete the push."""
        return self.returncode != 0

    @property
    def ref_really_moved(self) -> bool:
        """THE CONTROL. Without this the arm measures an unraced push."""
        return bool(self.advanced_tip) and self.advanced_tip != self.graded_tip

    @property
    def report(self) -> str:
        """A renderable summary that carries no path and no environment."""
        return (
            f"exit={self.returncode} graded={self.graded_tip[:12]} "
            f"advanced={self.advanced_tip[:12]} remote={self.remote_tip[:12]} "
            f"suite_ran={self.suite_ran}\n" + "\n".join(self.hook_said)
        )


def hook_output(stderr: str) -> tuple[str, ...]:
    """Only the hook's own banner lines, because the rest carries absolute paths.

    git renders the remote URL and pytest renders its rootdir, and in a sandbox
    both sit under the operator's profile - so echoing raw stderr into a failure
    report writes the Windows account name into test output, which non-negotiable
    3 forbids and non-negotiable 12 names as an echo path.
    """
    return tuple(
        line.strip() for line in stderr.splitlines() if line.strip().startswith(HOOK_BANNER)
    )


def run_git(
    box: Sandbox, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run git inside the sandbox with the operator's own configuration excluded."""
    return subprocess.run(
        ["git", *args],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=box.env if env is None else env,
        check=False,
    )


def local_tip(box: Sandbox) -> str:
    """What the sandbox branch resolves to right now, or an empty string."""
    proc = run_git(box, "rev-parse", "refs/heads/" + SANDBOX_BRANCH)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def remote_tip(box: Sandbox) -> str:
    """What the bare remote holds for the sandbox branch, or an empty string.

    THE ORACLE IS THE REMOTE ITSELF, never the remote-tracking ref. The incident
    is precisely a case where git's own bookkeeping disagreed with what the forge
    received, so a tracking ref cannot be the witness here.
    """
    proc = run_git(box, "ls-remote", "origin", "refs/heads/" + SANDBOX_BRANCH)
    if proc.returncode != 0:
        return ""
    line = proc.stdout.strip()
    return line.split()[0] if line else ""


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment with the operator's own git configuration excluded.

    Both files are aimed at paths that do not exist, so a machine carrying
    core.hooksPath or commit.gpgsign globally cannot answer for git here.

    THE NESTED PYTEST IS CUT LOOSE FROM THIS ONE. The hook runs pytest, and an
    inherited ``PYTEST_XDIST_WORKER`` makes that inner CONTROLLER file itself as a
    worker; ``PYTEST_CURRENT_TEST`` and a plugin list leak in the same way. They
    are removed rather than trusted.
    """
    # CS-968: scrubbed FIRST, for the same reason the sandbox cuts off global
    # config - an inherited GIT_DIR relocates every git call below.
    # CS-1187: Git's GNU timeout ahead of System32's, or the hook refuses.
    env = gnu_timeout_first(scrub(dict(os.environ)))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    env.pop("CLOCKSPEED_PYTHON", None)
    for leaked in [name for name in env if name.startswith("PYTEST_")]:
        env.pop(leaked, None)
    env.update(suite_dir_env(tmp_path))
    return Environment(env)


def make_sandbox(tmp_path: Path, isolated: Environment, *, seconds: float) -> Sandbox:
    """A real repository wired to the real tracked hook, with a deliberately slow suite.

    The identity is synthetic. Falling back to the machine's real user.name would
    write the Windows account name into a commit object (non-negotiable 3).

    The copy differs from the tracked hook on its CS-824 floor line only, which is
    rewritten to a test-local value so this one-test suite clears it.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir(exist_ok=True)
    installed = hooks / PRE_PUSH
    installed.write_bytes(wired_hook_bytes(PRE_PUSH, (HOOKS_DIR / PRE_PUSH).read_bytes()))
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    remote = tmp_path / "remote.git"
    box = Sandbox(work=work, hooks=hooks, remote=remote, env=isolated.variables)

    started = run_git(box, "init", "-q", "-b", SANDBOX_BRANCH)
    assert started.returncode == 0, "the throwaway repository could not be initialised"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks)),
        (OPERATOR_IDENT_KEY, FIXTURE_EMAIL),
    ):
        written = run_git(box, "config", key, value)
        assert written.returncode == 0, f"{key} could not be written in the sandbox"

    # Setting a value is not evidence the value took.
    readback = run_git(box, "config", "--get", "core.hooksPath")
    took = readback.returncode == 0 and readback.stdout.strip() == str(hooks)
    assert took, "core.hooksPath did not take in the sandbox"

    # A TINY SUITE THAT BLOCKS. The hook runs pytest against $ROOT/tests, and
    # pointing that at this repository's own suite would put minutes into every
    # arm. The sleep is what opens the race window; the marker is what proves the
    # suite ran at all.
    tests = work / "tests"
    tests.mkdir()
    body = (
        "import pathlib\n"
        "import time\n"
        "\n"
        "\n"
        "def test_sandbox_arm() -> None:\n"
        f"    pathlib.Path(__file__).parent.parent.joinpath({MARKER_NAME!r}).write_text(\n"
        '        "ran", encoding="ascii"\n'
        "    )\n"
        f"    time.sleep({seconds!r})\n"
    )
    (tests / "test_sandbox_arm.py").write_bytes(body.encode("ascii"))
    # PINS PYTEST'S ROOTDIR AT THE SANDBOX. Without an ini file pytest walks
    # upward looking for one and reaches the system temp directory.
    (work / "pytest.ini").write_bytes(b"[pytest]\n")
    # CS-1290: the kit files the wired identity and suite-gate lines run.
    install_hook_kit(work)

    initialised = run_git(box, "init", "-q", "--bare", str(remote))
    assert initialised.returncode == 0, "the bare remote could not be initialised"
    added = run_git(box, "remote", "add", "origin", str(remote))
    assert added.returncode == 0, "the bare remote could not be added"

    payload = work / "seed.txt"
    payload.write_bytes(b"an ordinary line of 7-bit ascii\n")
    staged = run_git(box, "add", "-A")
    assert staged.returncode == 0, "the sandbox seed could not be staged"
    seeded = run_git(box, "commit", "-q", "-m", "CS-954 sandbox seed")
    assert seeded.returncode == 0, "the sandbox could not make its first commit"
    return box


def race_a_push(box: Sandbox, *, advance: bool) -> Race:
    """Drive a real push and, optionally, advance the local ref while it runs."""
    graded = local_tip(box)
    advanced: list[str] = []

    def advance_the_ref() -> None:
        run_git(box, "commit", "-q", "--allow-empty", "-m", "CS-954 mid-hook commit")
        advanced.append(local_tip(box))

    timer = threading.Timer(ADVANCE_AT, advance_the_ref)
    if advance:
        timer.start()
    try:
        proc = run_git(box, "push", "origin", SANDBOX_BRANCH)
    finally:
        # CANCEL AND JOIN ONLY A TIMER THAT WAS STARTED. Joining an unstarted
        # Timer raises, and the raise landed on the NEGATIVE CONTROL - the one
        # arm that must pass today - which read as the hook refusing an ordinary
        # push rather than as a defect in this file.
        if advance:
            timer.cancel()
            timer.join()

    return Race(
        returncode=proc.returncode,
        graded_tip=graded,
        advanced_tip=advanced[0] if advanced else "",
        remote_tip=remote_tip(box),
        suite_ran=(box.work / MARKER_NAME).exists(),
        hook_said=hook_output(proc.stderr),
    )


def test_the_wired_hook_is_a_byte_identical_copy_of_the_tracked_hook(
    tmp_path: Path, isolated: Environment
) -> None:
    """Without this, every arm below could be grading a copy that drifted.

    THE WHOLE PREDICATE IS BOUND TO A BOOL, and it took both guards in this
    suite to arrive there. Binding the sandbox hook's BYTES leaves a local
    derived from a field whose class ships a ``__repr__`` to WITHHOLD it, and
    ``--showlocals`` renders that frame whatever the assertion said. Inlining the
    read instead moves the same field into the asserted EXPRESSION, which pytest
    reprs independently of the message. Only a plain scalar satisfies both: it
    neither holds the field nor renders it.

    BYTE-IDENTICAL EXCEPT THE SINGLE CS-824 FLOOR LINE. The copy must equal the
    helper's output AND differ from the tracked hook on that one line only, so any
    other drift is still red. Both halves are bound to one bool for the reason above.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.0)
    identical = (box.hooks / PRE_PUSH).read_bytes() == wired_hook_bytes(
        PRE_PUSH, (HOOKS_DIR / PRE_PUSH).read_bytes()
    ) and differs_only_on_floor_line(
        (box.hooks / PRE_PUSH).read_bytes(), (HOOKS_DIR / PRE_PUSH).read_bytes()
    )
    assert identical, (
        "the sandbox hook is not the tracked hook, so nothing below grades the real file"
    )


def test_an_unraced_push_is_still_accepted(tmp_path: Path, isolated: Environment) -> None:
    """THE NEGATIVE CONTROL, and it is the one that stops a useless repair.

    A hook that refused every push would satisfy the raced arm below and be
    worthless. This arm is what makes that repair fail, so the two must be read
    together.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.5)
    race = race_a_push(box, advance=False)

    assert race.suite_ran, f"the hook never ran its suite, so this measures nothing:\n{race.report}"
    assert not race.blocked, f"an ordinary push was refused:\n{race.report}"
    assert race.remote_tip == race.graded_tip, (
        f"the remote does not hold the graded commit:\n{race.report}"
    )


def test_the_hook_does_not_block_when_stdin_is_closed(
    tmp_path: Path, isolated: Environment
) -> None:
    """The check reads stdin, and a blocking read is a HANG rather than a failure.

    WHAT THIS ARM COVERS IS EXACTLY CLOSED STDIN, and the docstring says so
    because its first version did not. It claimed to cover "the way a person
    debugging it would" invoke the hook - and a person debugging it runs it from
    a TERMINAL, which was the one case the arm did not exercise and the one case
    that hung. The hook now refuses to read a terminal at all; that guard cannot
    be exercised here, because a pseudo-terminal is not portable to this suite.

    STILL UNCOVERED AND DELIBERATELY SO: stdin held open by another process
    blocks, as it would for any program reading to end-of-file. Real ``git push``
    always closes the pipe.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.0)
    proc = subprocess.run(
        # CS-1187: a default Git for Windows install puts no sh on PATH; the
        # fixture put Git's coreutils on the CHILD's PATH, so look there.
        [
            program_on_child_path(box.env, "sh"),
            str(box.hooks / PRE_PUSH),
            "origin",
            str(box.remote),
        ],
        cwd=str(box.work),
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=box.env,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    said = hook_output(proc.stderr)
    assert any("did NOT run" in line for line in said), (
        "the hook did not say that the ref check was skipped, so a check that "
        f"never ran is indistinguishable from one that found nothing:\n{said}"
    )


def test_a_ref_advanced_mid_hook_is_refused_rather_than_shipped(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-954's acceptance, stated against the HOOK and not against the transport.

    The hook is handed one SHA on stdin and the branch resolves to a later one by
    the time it returns. It must refuse. Asserting instead that the remote holds
    the graded SHA would pass today for a reason unrelated to the defect: the
    local transport already ships the resolved SHA, measured twice.
    """
    box = make_sandbox(tmp_path, isolated, seconds=SUITE_SECONDS)
    race = race_a_push(box, advance=True)

    assert race.suite_ran, f"the hook never ran its suite, so this measures nothing:\n{race.report}"
    assert race.ref_really_moved, (
        "the ref did not move during the hook, so the race never happened and this "
        f"arm proves nothing:\n{race.report}"
    )
    assert race.blocked, (
        "the hook accepted a push whose ref moved out from under its verdict - "
        f"CS-954:\n{race.report}"
    )
    # ATTRIBUTE THE REFUSAL, do not merely count it. A bare `returncode != 0`
    # is satisfied by ANY non-zero push exit - a network failure, a rejected
    # non-fast-forward, a red suite - so without this the arm would accept an
    # unrelated failure as evidence that CS-954's check fired.
    assert any("moved while the suite ran" in line for line in race.hook_said), (
        "the push failed, but not because of the CS-954 ref check - so this arm "
        f"would pass on an unrelated failure:\n{race.report}"
    )
    assert race.remote_tip != race.advanced_tip, (
        f"the ungraded mid-hook commit reached the remote - CS-954:\n{race.report}"
    )


def test_deleting_a_ref_is_not_refused_by_the_ref_check(
    tmp_path: Path, isolated: Environment
) -> None:
    """A delete sends the all-zero id as the local sha; nothing was graded.

    THIS ARM EXISTS BECAUSE THE SKIP WAS IMPLEMENTED AND UNGRADED. An adversary
    deleted the zero-sha branch from the hook and all four arms stayed green,
    while a real delete went from accepted to BLOCKED. A condition that no arm
    can fail is a sentence, not a guarantee.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.5)
    pushed = race_a_push(box, advance=False)
    assert not pushed.blocked, f"the sandbox branch would not push:\n{pushed.report}"

    deleted = run_git(box, "push", "origin", "--delete", SANDBOX_BRANCH)
    said = hook_output(deleted.stderr)
    # BOUND TO A SCALAR BEFORE ASSERTING, and this is not style. pytest rewrites
    # the asserted EXPRESSION and renders it independently of the message, so
    # `assert deleted.returncode == 0` prints the whole CompletedProcess - argv,
    # stdout and stderr - which carries the sandbox's absolute path under the
    # operator's profile. Measured here: it leaked one on the run that proved
    # this arm kills its mutant. Non-negotiables 3 and 12.
    code = deleted.returncode
    assert code == 0, (
        "the hook refused a ref DELETE, which grades nothing and ships nothing:\n" + "\n".join(said)
    )
    assert not remote_tip(box), "the branch is still on the remote after a delete"


def marker_present(box: Sandbox) -> bool:
    """Whether the sandbox suite left its marker behind - a BOOL, never a path.

    THE PATH IS NEVER RETURNED AND NEVER BOUND IN A CALLER'S FRAME. ``Sandbox``
    ships a ``__repr__`` that withholds its paths, but ``Sandbox.work`` itself is
    a bare ``Path`` under the operator's profile, so a local holding it is
    rendered in full by ``-l`` whatever the assertion's message said. Measured:
    binding ``marker = box.work / MARKER_NAME`` reddened both
    ``tests/test_assertion_rendering.py`` and ``tests/test_locals_rendering.py``,
    and their remedy is to stop binding it rather than to bind a scalar beside
    it - CLAUDE.md non-negotiables 3 and 12.
    """
    return (box.work / MARKER_NAME).exists()


def clear_the_marker(box: Sandbox) -> bool:
    """Remove the marker and report whether it is gone, handing back no path.

    THE RETURN IS THE READBACK, not the unlink's own silence. A marker that
    survived its removal would make the arm below read the PREVIOUS push's
    result and report the exact opposite of the truth.
    """
    (box.work / MARKER_NAME).unlink()
    return not (box.work / MARKER_NAME).exists()


def test_a_pure_delete_push_skips_the_suite_entirely(tmp_path: Path, isolated: Environment) -> None:
    """CS-989 - a push that only deletes refs must not pay for a whole suite.

    THIS ARM CANNOT BE THE ONE ABOVE IT. ``test_deleting_a_ref_is_not_refused_by
    _the_ref_check`` reads the EXIT CODE only, so removing the CS-989 skip leaves
    it green - the hook would simply run the suite and still exit 0. What has to
    be observed is whether pytest RAN, which the sandbox suite's marker records.

    THE MARKER IS CLEARED BEFORE THE DELETE PUSH, and that is load-bearing rather
    than tidy. The ordinary push immediately above leaves a marker behind;
    without the clear this arm would read THAT one and report the exact opposite
    of the truth on a hook that skipped nothing.

    THE ORDINARY PUSH IS ALSO THE POSITIVE CONTROL. A marker mechanism that never
    writes would make the absence below pass for a reason that has nothing to do
    with CS-989, so the same test first proves the marker appears when the suite
    really does run.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.5)

    pushed = race_a_push(box, advance=False)
    assert not pushed.blocked, f"the sandbox branch would not push:\n{pushed.report}"
    # THE POSITIVE CONTROL, asserted before the marker is trusted as an oracle.
    control = marker_present(box)
    assert control, (
        "the sandbox suite left no marker on an ORDINARY push, so its absence "
        "after the delete push below would prove nothing about CS-989"
    )

    cleared = clear_the_marker(box)
    assert cleared, "the marker survived its own removal"

    deleted = run_git(box, "push", "origin", "--delete", SANDBOX_BRANCH)
    said = hook_output(deleted.stderr)
    # Bound to scalars before asserting: pytest renders the asserted EXPRESSION
    # independently of the message, and a CompletedProcess carries the sandbox's
    # absolute path under the operator's profile (non-negotiables 3 and 12).
    code = deleted.returncode
    ran = marker_present(box)
    assert code == 0, (
        "the hook refused a ref DELETE, which grades nothing and ships nothing:\n" + "\n".join(said)
    )
    assert not ran, (
        "the pre-push suite RAN on a push that only deletes refs - CS-989. The "
        "delete grades nothing and ships nothing, so the run is pure cost:\n" + "\n".join(said)
    )
    # ATTRIBUTE THE SKIP, do not merely observe a missing marker. A hook that
    # died before reaching pytest for an unrelated reason also leaves none.
    assert any("CS-989" in line for line in said), (
        "the suite did not run, but the hook never said so - a silent skip is "
        "indistinguishable from a gate that broke:\n" + "\n".join(said)
    )
    assert not remote_tip(box), "the branch is still on the remote after a delete"


def test_a_mixed_delete_and_update_push_still_runs_the_suite(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-989 skips on EVERY, never on ANY - one shipping ref pays the full suite.

    THE MUTATION THIS ARM EXISTS TO KILL is the word EVERY weakened to ANY: a
    ``grep -q`` for a zero sha, or a ``case`` over the whole blob, both answer
    "there is a deletion here" when the question is "is there anything else".
    That mutant ships an ungraded commit whenever one travels beside a deletion,
    which is the worst outcome this hook has, and no arm that pushes a single
    ref can see it.
    """
    box = make_sandbox(tmp_path, isolated, seconds=0.5)

    seeded = race_a_push(box, advance=False)
    assert not seeded.blocked, f"the sandbox branch would not push:\n{seeded.report}"

    branched = run_git(box, "branch", DOOMED_BRANCH)
    made = branched.returncode
    assert made == 0, "the second sandbox branch could not be created"
    planted = run_git(box, "push", "origin", DOOMED_BRANCH)
    plant_code = planted.returncode
    assert plant_code == 0, "the second sandbox branch would not push"

    shipped = run_git(box, "commit", "-q", "--allow-empty", "-m", "CS-989 shipping commit")
    commit_code = shipped.returncode
    assert commit_code == 0, "the shipping commit could not be made"
    tip = local_tip(box)
    assert tip, "the sandbox branch will not resolve after the shipping commit"

    cleared = clear_the_marker(box)
    assert cleared, "the marker survived its own removal"

    # ONE push event carrying TWO lines: an update and a deletion. `--delete`
    # cannot be used here - it would make BOTH refspecs deletions and rebuild
    # the pure-delete case this arm is the counterpart to.
    mixed = run_git(
        box,
        "push",
        "origin",
        f"refs/heads/{SANDBOX_BRANCH}:refs/heads/{SANDBOX_BRANCH}",
        f":refs/heads/{DOOMED_BRANCH}",
    )
    said = hook_output(mixed.stderr)
    code = mixed.returncode
    ran = marker_present(box)
    assert code == 0, "the hook refused a push carrying one update and one deletion:\n" + "\n".join(
        said
    )
    assert ran, (
        "the pre-push suite did NOT run on a push that ships a commit, because "
        "a deletion travelled beside it - CS-989 skips on EVERY, never on ANY:\n" + "\n".join(said)
    )
    assert remote_tip(box) == tip, "the shipping commit did not reach the remote"
