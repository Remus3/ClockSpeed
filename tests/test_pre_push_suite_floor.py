"""CS-821 - the pre-push gate judges what the run EXECUTED, never pytest's exit code.

THE DEFECT, measured at base. ``.githooks/pre-push`` checked that ``import
pytest`` succeeded and then trusted the exit status of ``-m pytest``. A
one-comment ``pytest.py`` placed first on ``PYTHONPATH`` passes the import check,
``-m pytest`` runs that empty module, exits 0, and the push ships with not one
test run. A tree whose every test is skipped exits 0 the same way. Only exit 5,
"collected nothing", was ever refused.

THE REPAIR, under the frozen-file grant recorded in ``docs/LEDGER.md`` under
"CS-821, CS-824, CS-704 - FROZEN-FILE GRANT". The run writes a junit report into
a private ``mktemp`` directory outside the repository, and the hook reads that
report back. A report that is missing, unreadable, or records zero executed
tests REFUSES, whatever status pytest chose. A skipped test counts as not run.

EVERY ARM IS A REAL PUSH to a bare remote under ``tmp_path``, never origin, and
the oracle is the remote itself read with ``git ls-remote`` - never the exit
notice of the push. The remote is seeded FIRST, through ``--no-verify``, so an
arm that is refused can prove the remote ref did not MOVE, which is stronger
than proving no ref exists. No arm pushes from this repository.

RESOURCE LIFETIME. Every child is a ``subprocess.run`` bounded by
``GIT_TIMEOUT``, which reaps it. The sandbox, its bare remote and the hook's own
temporary directory all live under pytest's ``tmp_path``, which pytest removes on
its own retention schedule. The hook's ``TMPDIR`` is pointed at a directory the
arm owns, so the arm can prove the hook removed its report on every exit path.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.git_env import scrub

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
TRACKED_HOOK: Final = REPO_ROOT / ".githooks" / "pre-push"

GIT_TIMEOUT: Final = 300
BRANCH: Final = "cs821-sandbox"
FIXTURE_NAME: Final = "CS-821 Fixture"
FIXTURE_EMAIL: Final = "cs821@example.invalid"
HOOK_BANNER: Final = "clockspeed pre-push"
ENVIRONMENT_REPR: Final = "<environment withheld>"
PYTHONPATH_ENV: Final = "PYTHONPATH"

#: The cause each refusal must NAME on its banner line. A refusal that names the
#: wrong cause is a different check firing, so every refused arm asserts one.
NO_REPORT: Final = "pytest wrote no report of what it executed"
UNREADABLE: Final = "pytest's report could not be read"
ZERO_EXECUTED: Final = "pytest executed zero tests"
INSIDE_REPO: Final = "the report directory resolves inside the repository"

#: Distinctive, so an arm can prove the refusal never renders the report path.
REPORT_PARENT: Final = "cs821-report-parent"

#: The prefix of the directory pytest itself makes under ``TMPDIR``.
PYTEST_BASETEMP: Final = "pytest-of-"

PASSING_TEST: Final = "def test_{index}() -> None:\n    assert True\n\n\n"
SKIPPED_TEST: Final = (
    "@pytest.mark.skip(reason='CS-821 sandbox')\ndef test_{index}() -> None:\n    assert True\n\n\n"
)

#: One comment and nothing else - the whole of the shadow the acceptance names.
SHADOW_PYTEST: Final = b"# CS-821: a shadow pytest that runs nothing at all\n"

#: The adversary's shadow: runs nothing, but writes a report claiming one passed
#: test and exits 0. Every report check alone accepts it; only where pytest
#: RESOLVES FROM can refuse it.
FORGING_PYTEST: Final = (
    b"import sys\n"
    b"if '--junitxml' in sys.argv:\n"
    b"    target = sys.argv[sys.argv.index('--junitxml') + 1]\n"
    b"    with open(target, 'w', encoding='ascii') as handle:\n"
    b'        handle.write(\'<testsuite><testcase classname="x" name="y"/></testsuite>\')\n'
)

#: Rewrites a red session to exit 0. The report still records the failure.
GREEN_LYING_CONFTEST: Final = (
    "import pytest\n"
    "\n"
    "\n"
    "@pytest.hookimpl(trylast=True)\n"
    "def pytest_sessionfinish(session, exitstatus):\n"
    "    session.exitstatus = 0\n"
)

FAILING_TEST: Final = "def test_{index}() -> None:\n    assert False\n\n\n"

#: A real python behind a wrapper that DROPS ``-P``, which is how an interpreter
#: without safe-path mode behaves when the flag is silently not honoured.
#: ``@PYTHON@`` is replaced at run time with this interpreter's POSIX path.
SAFE_PATH_DROPPING_WRAPPER: Final = (
    '#!/bin/sh\nfor a do shift; [ "$a" = "-P" ] || set -- "$@" "$a"; done\nexec "@PYTHON@" "$@"\n'
)

SHADOWED: Final = "pytest does not resolve from the interpreter's site-packages"
NO_SAFE_PATH: Final = "cannot run pytest in safe-path mode"
RED_REPORT: Final = "pytest's report records failed or errored tests, yet pytest exited 0"
RED_EXIT: Final = "BLOCKED (pytest exit"

#: Overwrites the finished report with bytes no XML parser accepts. It acts in
#: the CONTROLLER only: an xdist worker also loads this conftest, and a worker
#: corrupting the file before the controller writes it would measure nothing.
CORRUPTING_CONFTEST: Final = (
    "from pathlib import Path\n"
    "\n"
    "\n"
    "def pytest_unconfigure(config):\n"
    "    target = config.option.xmlpath\n"
    "    if target and not hasattr(config, 'workerinput'):\n"
    "        Path(target).write_bytes(b'<not-xml')\n"
)


class Environment(NamedTuple):
    """The child environment, wrapped so pytest cannot render its contents."""

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Sandbox(NamedTuple):
    """A throwaway repository wired to a copy of the hook, with a bare remote."""

    work: Path
    remote: Path
    reports: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-821 sandbox, paths withheld>"


class Push(NamedTuple):
    """One real push through the hook, and what the remote held afterwards."""

    returncode: int
    seeded_tip: str
    local_tip: str
    remote_tip: str
    hook_said: tuple[str, ...]
    leaked_path: bool

    @property
    def landed(self) -> bool:
        """The remote holds the commit the push offered."""
        return bool(self.local_tip) and self.remote_tip == self.local_tip

    @property
    def unmoved(self) -> bool:
        """The remote still holds the seed, and the offered commit is a different one."""
        return (
            bool(self.seeded_tip)
            and self.remote_tip == self.seeded_tip
            and self.local_tip != self.seeded_tip
        )

    def said(self, cause: str) -> bool:
        """Whether one of the hook's own banner lines names ``cause``."""
        return any(cause in line for line in self.hook_said)

    @property
    def report(self) -> str:
        """A renderable summary that carries no path and no environment."""
        return (
            f"exit={self.returncode} seeded={self.seeded_tip[:12]} "
            f"local={self.local_tip[:12]} remote={self.remote_tip[:12]}\n"
            + "\n".join(self.hook_said)
        )


def hook_output(stderr: str) -> tuple[str, ...]:
    """Only the hook's own banner lines; the rest can carry absolute paths."""
    return tuple(
        line.strip() for line in stderr.splitlines() if line.strip().startswith(HOOK_BANNER)
    )


def git(
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


def tip(box: Sandbox, *, remote: bool) -> str:
    """The sandbox branch locally, or as the bare remote itself holds it."""
    if remote:
        proc = git(box, "ls-remote", "origin", "refs/heads/" + BRANCH)
        line = proc.stdout.strip() if proc.returncode == 0 else ""
        return line.split()[0] if line else ""
    proc = git(box, "rev-parse", "refs/heads/" + BRANCH)
    return proc.stdout.strip() if proc.returncode == 0 else ""


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment cut loose from the operator's git config and from this pytest.

    ``TMPDIR`` is aimed at a directory this arm owns, so the hook's ``mktemp``
    lands where the arm can prove it was removed.
    """
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for leaked in [
        name
        for name in env
        if name.upper().startswith("PYTEST_")
        or name.upper() in {"CLOCKSPEED_PYTHON", PYTHONPATH_ENV, "TMPDIR"}
    ]:
        env.pop(leaked, None)
    reports = tmp_path / REPORT_PARENT
    reports.mkdir()
    env["TMPDIR"] = str(reports)
    return Environment(env)


def make_sandbox(
    tmp_path: Path,
    isolated: Environment,
    *,
    tests: dict[str, str],
    hook: bytes | None = None,
    root_files: dict[str, bytes] | None = None,
) -> Sandbox:
    """A real repository wired to ``hook`` (the tracked bytes by default), seeded remotely.

    The seed reaches the remote through ``--no-verify``, so it grades nothing and
    exists only so a refused arm can prove the remote ref did not move.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / "pre-push"
    installed.write_bytes(TRACKED_HOOK.read_bytes() if hook is None else hook)
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    remote = tmp_path / "remote.git"
    box = Sandbox(
        work=work, remote=remote, reports=tmp_path / REPORT_PARENT, env=isolated.variables
    )

    assert git(box, "init", "-q", "-b", BRANCH).returncode == 0, "the sandbox could not init"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks)),
    ):
        assert git(box, "config", key, value).returncode == 0, f"{key} did not write"
    readback = git(box, "config", "--get", "core.hooksPath")
    took = readback.returncode == 0 and readback.stdout.strip() == str(hooks)
    assert took, "core.hooksPath did not take in the sandbox"

    suite = work / "tests"
    suite.mkdir()
    for name, body in tests.items():
        (suite / name).write_bytes(body.encode("ascii"))
    # Files at the repository ROOT are COMMITTED, so they model a pushed tree.
    for name, raw in (root_files or {}).items():
        (work / name).write_bytes(raw)
    # Pins pytest's rootdir at the sandbox, so it never walks up into the temp root.
    (work / "pytest.ini").write_bytes(b"[pytest]\n")

    assert git(box, "init", "-q", "--bare", str(remote)).returncode == 0, "no bare remote"
    assert git(box, "remote", "add", "origin", str(remote)).returncode == 0, "no origin"
    assert git(box, "add", "-A").returncode == 0, "the seed could not be staged"
    assert git(box, "commit", "-q", "-m", "CS-821 seed").returncode == 0, "no seed commit"
    seeded = git(box, "push", "-q", "--no-verify", "origin", BRANCH)
    assert seeded.returncode == 0, "the seed could not reach the bare remote"
    assert tip(box, remote=True) == tip(box, remote=False), "the seed is not on the remote"
    return box


def push(box: Sandbox, *, extra_env: dict[str, str] | None = None) -> Push:
    """Offer one new commit through the hook and read back what the remote holds."""
    seeded = tip(box, remote=True)
    made = git(box, "commit", "-q", "--allow-empty", "-m", "CS-821 offered commit")
    assert made.returncode == 0, "the offered commit could not be made"
    env = dict(box.env)
    env.update(extra_env or {})
    proc = git(box, "push", "origin", BRANCH, env=env)
    return Push(
        returncode=proc.returncode,
        seeded_tip=seeded,
        local_tip=tip(box, remote=False),
        remote_tip=tip(box, remote=True),
        hook_said=hook_output(proc.stderr),
        leaked_path=REPORT_PARENT in proc.stderr,
    )


def suite_of(template: str, count: int, *, header: str = "") -> dict[str, str]:
    """One test module holding ``count`` tests written from ``template``."""
    body = header + "".join(template.format(index=index) for index in range(count))
    return {"test_sandbox.py": body}


def leftovers(box: Sandbox) -> int:
    """How many entries the hook left in the temporary directory it was handed.

    PYTEST'S OWN BASETEMP IS NOT THE HOOK'S. The sandbox pytest creates a
    ``pytest-of-<user>`` directory under ``TMPDIR`` on every run, MEASURED at
    base on an ordinary passing push, and it is pytest's to retain. Everything
    else in the directory is something the hook made and failed to remove.
    """
    return sum(1 for entry in box.reports.iterdir() if not entry.name.startswith(PYTEST_BASETEMP))


# --- the positive control ---------------------------------------------------


def test_a_genuinely_passing_tree_still_pushes(tmp_path: Path, isolated: Environment) -> None:
    """THE CONTROL. A hook that refused every push would satisfy every arm below."""
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    result = push(box)
    assert result.landed, f"an ordinary passing push was refused:\n{result.report}"
    assert leftovers(box) == 0, "the hook left its report behind after a pass"


# --- CS-821: a run that did not execute is refused --------------------------


def test_a_shadowed_pytest_is_refused_and_the_remote_does_not_move(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE ACCEPTANCE ARM. A real python, with a one-comment pytest.py first on PYTHONPATH.

    RED at base: the import check passes, ``-m pytest`` runs the empty module and
    exits 0, and the offered commit lands on the remote. Refused now because the
    pytest the interpreter would import does not live in its site-packages.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "pytest.py").write_bytes(SHADOW_PYTEST)
    result = push(box, extra_env={PYTHONPATH_ENV: str(shadow)})
    assert result.unmoved, f"a push that ran no test moved the remote:\n{result.report}"
    assert result.returncode != 0, f"the refused push reported success:\n{result.report}"
    assert result.said(SHADOWED), f"the refusal did not name the shadow:\n{result.report}"
    assert not result.leaked_path, "the refusal rendered the report's temporary path"
    assert leftovers(box) == 0, "the hook left its report directory behind on a refusal"


def test_a_report_forging_shadow_on_pythonpath_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """A3. The shadow WRITES a plausible report and exits 0.

    RED at 73beebc: every report check accepted the forged report and the push
    landed. The report cannot tell a forged record from a real one, so the refusal
    has to come from where pytest resolves.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "pytest.py").write_bytes(FORGING_PYTEST)
    result = push(box, extra_env={PYTHONPATH_ENV: str(shadow)})
    assert result.unmoved, f"a forged report moved the remote:\n{result.report}"
    assert result.said(SHADOWED), f"the refusal did not name the shadow:\n{result.report}"


def test_a_report_forging_pytest_at_the_repository_root_is_ignored(
    tmp_path: Path, isolated: Environment
) -> None:
    """A3, working-directory route. ``-m`` puts the working directory on sys.path.

    The pushed tree carries a forging pytest.py at its root and one FAILING test.
    RED at 73beebc: the forgery ran in place of pytest, reported a pass and the
    push landed. Under safe-path mode the real pytest runs, the test fails, and
    the push is refused for THAT reason - which is what proves the real one ran.
    """
    box = make_sandbox(
        tmp_path,
        isolated,
        tests=suite_of(FAILING_TEST, 1),
        root_files={"pytest.py": FORGING_PYTEST},
    )
    result = push(box)
    assert result.unmoved, f"a forgery in the pushed tree moved the remote:\n{result.report}"
    assert result.said(RED_EXIT), f"the real pytest did not run and fail:\n{result.report}"


def test_an_interpreter_that_does_not_honour_safe_path_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """A3. The ``-P`` defence is only real if the interpreter honours it.

    A wrapper that drops ``-P`` models an interpreter without safe-path mode. It
    passes the ladder's probe - it IS a working python - and must still refuse.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    wrapper = tmp_path / "python-without-safe-path"
    body = SAFE_PATH_DROPPING_WRAPPER.replace("@PYTHON@", Path(sys.executable).as_posix())
    wrapper.write_bytes(body.encode("ascii"))
    wrapper.chmod(0o755)
    result = push(box, extra_env={"CLOCKSPEED_PYTHON": wrapper.as_posix()})
    assert result.unmoved, f"an interpreter without -P moved the remote:\n{result.report}"
    assert result.said(NO_SAFE_PATH), f"the refusal named another cause:\n{result.report}"


def test_a_conftest_that_turns_a_red_session_green_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """A1. The exit status says 0 while the report records a failed test.

    RED at 73beebc: the passed count was computed and never compared, so the
    hook trusted the rewritten exit status and the push landed.
    """
    tests = suite_of(FAILING_TEST, 1)
    tests["conftest.py"] = GREEN_LYING_CONFTEST
    box = make_sandbox(tmp_path, isolated, tests=tests)
    result = push(box)
    assert result.unmoved, f"a red report behind a green exit moved the remote:\n{result.report}"
    assert result.said(RED_REPORT), f"the refusal named another cause:\n{result.report}"


def test_a_wholly_skipped_tree_is_refused(tmp_path: Path, isolated: Environment) -> None:
    """Skipped is NOT RUN. RED at base: every test skips, pytest exits 0, the push lands."""
    tests = suite_of(SKIPPED_TEST, 3, header="import pytest\n\n\n")
    box = make_sandbox(tmp_path, isolated, tests=tests)
    result = push(box)
    assert result.unmoved, f"a wholly skipped suite moved the remote:\n{result.report}"
    assert result.said(ZERO_EXECUTED), f"the refusal named another cause:\n{result.report}"
    assert leftovers(box) == 0, "the hook left its report directory behind on a refusal"


def test_an_addopts_that_disables_the_report_is_refused_as_no_report(
    tmp_path: Path, isolated: Environment
) -> None:
    """Grant condition 1: a flag that suppresses the report lands in the no-report refusal."""
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    result = push(box, extra_env={"PYTEST_ADDOPTS": "-p no:junitxml"})
    assert result.unmoved, f"a run with its report disabled moved the remote:\n{result.report}"
    assert result.said(NO_REPORT), f"the refusal did not name a missing report:\n{result.report}"


def test_an_unreadable_report_is_refused(tmp_path: Path, isolated: Environment) -> None:
    """The report is read, not merely found. A conftest overwrites it with non-XML bytes."""
    tests = suite_of(PASSING_TEST, 3)
    tests["conftest.py"] = CORRUPTING_CONFTEST
    box = make_sandbox(tmp_path, isolated, tests=tests)
    result = push(box)
    assert result.unmoved, f"an unreadable report moved the remote:\n{result.report}"
    assert result.said(UNREADABLE), f"the refusal named another cause:\n{result.report}"
    assert leftovers(box) == 0, "the hook left its report directory behind on a refusal"


def test_a_report_directory_inside_the_repository_is_refused(
    tmp_path: Path, isolated: Environment
) -> None:
    """Grant condition 2: the report never lands in the repository, even when TMPDIR says so."""
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    # Built from tmp_path, never from the sandbox's withheld field (the locals guard).
    inside = tmp_path / "work" / "inside-tmp"
    inside.mkdir()
    result = push(box, extra_env={"TMPDIR": str(inside)})
    assert result.unmoved, f"a report aimed into the tree moved the remote:\n{result.report}"
    assert result.said(INSIDE_REPO), f"the refusal named another cause:\n{result.report}"
    assert sum(1 for _ in inside.iterdir()) == 0, "the hook left a directory inside the tree"
