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

CS-824, THE FLOOR. A green run must also have PASSED at least one literal count
of tests, declared on one line of the hook. The CS-821 arms install a copy whose
floor line alone is rewritten to a test-local value through
``tests/pre_push_floor.py``; the CS-824 arms install the tracked hook UNMODIFIED
and read the shipped value from it (ruling recorded in ``docs/LEDGER.md`` under
"CS-824 - GRANT CLARIFICATION", condition C4).

CS-1349, ONE GATE COMMAND PER CHECKOUT. Two landed pushes through one sandbox
must leave the suite gate two records carrying ONE command hash, read from the
gate's own durations file; the arms are at the end of this module, under the
frozen-file grant recorded in ``docs/LEDGER.md`` under "2026-10-23 - CS-1349".

RESOURCE LIFETIME. Every child is a ``subprocess.run`` bounded by
``GIT_TIMEOUT``, which reaps it. The sandbox, its bare remote and the hook's own
temporary directory all live under pytest's ``tmp_path``, which pytest removes on
its own retention schedule. The hook's ``TMPDIR`` is pointed at a directory the
arm owns, so the arm can prove the hook removed its report on every exit path.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.fleet_hook_kit import (
    COMMIT_MARGIN_ENV,
    DURATIONS_FILE,
    OPERATOR_IDENT_KEY,
    SUITE_DIR_ENV,
    commit_margin_env,
    install_hook_kit,
    suite_dir_env,
)
from tests.git_env import scrub
from tests.pre_push_floor import (
    FLOOR_LINE,
    FloorLineError,
    differs_only_on_floor_line,
    shipped_floor,
    wired_hook_bytes,
    with_test_floor,
)

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
#: RESOLVES FROM can refuse it. CS-1349: it expands the report word the way
#: pytest's junitxml plugin does, so it writes where the real report would land.
FORGING_PYTEST: Final = (
    b"import os\n"
    b"import sys\n"
    b"if '--junitxml' in sys.argv:\n"
    b"    word = sys.argv[sys.argv.index('--junitxml') + 1]\n"
    b"    target = os.path.expanduser(os.path.expandvars(word))\n"
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
#: CS-1349: the option holds the hook's report WORD, which it expands the way
#: pytest's junitxml plugin does, so it overwrites the report pytest wrote.
CORRUPTING_CONFTEST: Final = (
    "import os\n"
    "from pathlib import Path\n"
    "\n"
    "\n"
    "def pytest_unconfigure(config):\n"
    "    target = config.option.xmlpath\n"
    "    if target and not hasattr(config, 'workerinput'):\n"
    "        place = os.path.expanduser(os.path.expandvars(target))\n"
    "        Path(place).write_bytes(b'<not-xml')\n"
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
    env.update(suite_dir_env(tmp_path))
    # CS-1349: the gate's commit margin is 0 for a sandbox push (grant clause C).
    env.update(commit_margin_env())
    return Environment(env)


def make_sandbox(
    tmp_path: Path,
    isolated: Environment,
    *,
    tests: dict[str, str],
    real_floor: bool = False,
    root_files: dict[str, bytes] | None = None,
) -> Sandbox:
    """A real repository wired to a copy of the tracked hook, seeded remotely.

    The CS-821 arms install the copy with its CS-824 floor line rewritten to a
    test-local value (``tests/pre_push_floor.py``), so a three-test tree clears
    it. ``real_floor`` installs the tracked bytes UNMODIFIED, which is what the
    CS-824 boundary arms grade (ruling condition C4).

    The seed reaches the remote through ``--no-verify``, so it grades nothing and
    exists only so a refused arm can prove the remote ref did not move.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / "pre-push"
    tracked = TRACKED_HOOK.read_bytes()
    installed.write_bytes(tracked if real_floor else with_test_floor(tracked))
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
        (OPERATOR_IDENT_KEY, FIXTURE_EMAIL),
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
    # CS-1290: the kit files the wired identity and suite-gate lines run.
    install_hook_kit(work)

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

    RED at the first CS-821 repair: every report check accepted the forged report and the push
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
    RED at the first CS-821 repair: the forgery ran in place of pytest, reported a pass and the
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

    RED at the first CS-821 repair: the passed count was computed and never compared, so the
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


# --- CS-824: the shipped floor, graded through an UNMODIFIED copy -----------

BELOW_FLOOR: Final = "below the floor of"
FLOOR_NAME: Final = "CS_PASS_FLOOR"

#: ``count`` trivially passing cases, generated rather than written out.
PARAMETRIZED_SUITE: Final = (
    "import pytest\n"
    "\n"
    "\n"
    "@pytest.mark.parametrize('case', range({count}))\n"
    "def test_case(case: int) -> None:\n"
    "    assert case >= 0\n"
)


def test_the_hook_declares_its_floor_on_exactly_one_literal_line() -> None:
    """Ruling C1. One ``NAME=digits`` line, and the name is never set any other way.

    A second assignment, an ``export``, a ``read`` or a default expansion such as
    ``${NAME:-...}`` would each let the environment or a config reach the floor.
    Only plain ``$NAME`` expansions may appear outside the declaration.
    """
    lines = TRACKED_HOOK.read_bytes().decode("ascii").split("\n")
    declared = sum(1 for line in lines if FLOOR_LINE.fullmatch(line.encode("ascii")))
    stray = [
        line.strip()
        for line in lines
        if FLOOR_NAME in line
        and not line.lstrip().startswith("#")
        and not FLOOR_LINE.fullmatch(line.encode("ascii"))
        and re.search(r"(?<!\$)" + FLOOR_NAME + r"|\$\{" + FLOOR_NAME, line)
    ]
    assert declared == 1, f"the hook declares the floor on {declared} lines, not one"
    assert stray == [], f"the floor name is set outside its one literal line: {stray}"
    assert shipped_floor(TRACKED_HOOK.read_bytes()) > 1, "the shipped floor is not a floor"


def test_a_tree_cut_to_one_passing_test_is_refused_by_the_shipped_floor(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE CS-824 ACCEPTANCE ARM, through the tracked hook UNMODIFIED.

    The environment also names the floor variable with a value of 1, and the
    push is refused anyway: the literal line overwrites anything inherited.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 1), real_floor=True)
    result = push(box, extra_env={FLOOR_NAME: "1"})
    assert result.unmoved, f"a one-test tree moved the remote:\n{result.report}"
    assert result.said(BELOW_FLOOR), f"the refusal named another cause:\n{result.report}"


@pytest.mark.parametrize(("offset", "lands"), [(-1, False), (0, True)], ids=["below", "at"])
def test_the_shipped_floor_boundary_both_ways(
    tmp_path: Path, isolated: Environment, offset: int, lands: bool
) -> None:
    """Grant condition 4: floor minus one is refused and the floor itself pushes.

    The count is READ from the tracked hook, never restated here, so a re-pinned
    floor moves this arm with it.
    """
    count = shipped_floor(TRACKED_HOOK.read_bytes()) + offset
    tests = {"test_sandbox.py": PARAMETRIZED_SUITE.format(count=count)}
    box = make_sandbox(tmp_path, isolated, tests=tests, real_floor=True)
    result = push(box)
    if lands:
        assert result.landed, f"a tree AT the floor was refused:\n{result.report}"
    else:
        assert result.unmoved, f"a tree one below the floor moved the remote:\n{result.report}"
        assert result.said(BELOW_FLOOR), f"the refusal named another cause:\n{result.report}"


# --- the substitution helper (ruling C2) ------------------------------------


def test_the_helper_refuses_a_hook_without_exactly_one_floor_line() -> None:
    """C2(i). Zero floor lines and two floor lines each raise, never pass through."""
    tracked = TRACKED_HOOK.read_bytes()
    line = next(ln for ln in tracked.split(b"\n") if FLOOR_LINE.fullmatch(ln))
    for broken in (
        tracked.replace(line, b"# no floor"),
        tracked.replace(line, line + b"\n" + line),
    ):
        with pytest.raises(FloorLineError):
            with_test_floor(broken)


def test_the_helper_changes_the_floor_line_and_nothing_else() -> None:
    """C2(ii)-(iv). One line differs, a planted drift is caught, other hooks stay verbatim."""
    tracked = TRACKED_HOOK.read_bytes()
    copy = with_test_floor(tracked)
    drifted = copy.replace(b"set -u", b"set -u ", 1)
    assert differs_only_on_floor_line(copy, tracked), "the floor copy is not a one-line change"
    assert not differs_only_on_floor_line(tracked, tracked), "an unsubstituted copy passed"
    assert not differs_only_on_floor_line(drifted, tracked), "a second drifted line passed"
    assert wired_hook_bytes("pre-commit", b"x\n") == b"x\n", "a non-push hook was rewritten"
    assert wired_hook_bytes("commit-msg", b"x\n") == b"x\n", "a non-push hook was rewritten"


# --- CS-1349: two pushes from one checkout hand the suite gate ONE command --
#
# THE GAP. The suite gate keys its own history - the commit admission's
# ``required_commit_mb`` and the short-suite lane's ``median_hold`` - by
# ``ops/fleet_kit/fleet_suite_gate.py::cmd_hash``, taken over EVERY command word
# after ``--``. The hook handed it the junit report's path as one of those words,
# inside a fresh ``mktemp -d`` directory new on every push, so no push matched
# an earlier one and every push asked for the kit's default commit requirement.
#
# THE GRANT, ``docs/LEDGER.md``, 2026-10-23 CS-1349: only how the report path
# reaches pytest changes. The directory stays a fresh ``mktemp -d`` per run,
# outside the tree, removed by the trap and never rendered; an inherited
# ``PYTEST_ADDOPTS`` reaches pytest unchanged.
#
# THE ORACLE IS THE GATE'S OWN RECORD: one line per run in its durations file,
# in the slot directory ``isolated`` aims under the arm's own ``tmp_path``.

#: The variable the hook hands pytest the report's place through. Named here so
#: the planted-value arm can aim it; the static arm proves the hook uses it.
REPORT_ENV: Final = "CS_PUSH_REPORT"

#: The one command word that carries it: single-quoted, so the SHELL never
#: expands it and pytest's own junitxml plugin does.
REPORT_WORD: Final = "'${" + REPORT_ENV + "}'"

#: A harmless, distinctive inherited value the sandbox test checks byte for byte.
INHERITED_ADDOPTS: Final = "-p no:cacheprovider"

#: A sandbox test that passes only when pytest saw the inherited value unchanged.
ADDOPTS_TEST: Final = (
    "import os\n"
    "\n"
    "\n"
    "def test_the_inherited_addopts_reached_pytest_unchanged() -> None:\n"
    f"    assert os.environ.get('PYTEST_ADDOPTS') == {INHERITED_ADDOPTS!r}\n"
)

#: The shape of the gate's ``cmd`` field: 16 lowercase hex digits.
CMD_HASH: Final = re.compile(r"[0-9a-f]{16}")

#: How many pushes the acceptance arm makes, so how many records the gate owes.
PUSHES: Final = 2


def gate_records(tmp_path: Path) -> list[dict[str, object]]:
    """Every record the sandbox's suite gate appended, oldest first."""
    durations = Path(suite_dir_env(tmp_path)[SUITE_DIR_ENV]) / DURATIONS_FILE
    if not durations.is_file():
        return []
    lines = durations.read_bytes().decode("ascii").split("\n")
    return [json.loads(line) for line in lines if line.strip()]


def test_two_pushes_from_one_checkout_hand_the_gate_one_command_hash(
    tmp_path: Path, isolated: Environment
) -> None:
    """THE CS-1349 ACCEPTANCE ARM. RED at base: two records, two distinct ``cmd`` hashes."""
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    first = push(box)
    assert first.landed, f"the first ordinary push was refused:\n{first.report}"
    second = push(box)
    assert second.landed, f"the second ordinary push was refused:\n{second.report}"
    hashes = [record.get("cmd") for record in gate_records(tmp_path)]
    recorded = len(hashes)
    assert recorded == PUSHES, f"the gate recorded {recorded} runs for two pushes, not two"
    shaped = sum(1 for value in hashes if isinstance(value, str) and CMD_HASH.fullmatch(value))
    assert shaped == PUSHES, f"{shaped} of the two records carry a command hash"
    distinct = len(set(hashes))
    assert distinct == 1, f"two pushes from one checkout handed the gate {distinct} commands"
    leaked = first.leaked_path or second.leaked_path
    assert not leaked, "a push rendered the report's temporary path"
    assert leftovers(box) == 0, "the hook left a report directory behind across two pushes"


def test_an_inherited_addopts_reaches_pytest_unchanged(
    tmp_path: Path, isolated: Environment
) -> None:
    """CS-1349 grant clause A. The report path never rides on ``PYTEST_ADDOPTS``.

    The sandbox's one test passes only when pytest saw the inherited value byte
    for byte, so a hook that appended to it, replaced it or dropped it is refused.
    """
    tests = {"test_sandbox.py": ADDOPTS_TEST}
    box = make_sandbox(tmp_path, isolated, tests=tests)
    result = push(box, extra_env={"PYTEST_ADDOPTS": INHERITED_ADDOPTS})
    assert result.landed, f"the inherited value did not reach pytest unchanged:\n{result.report}"


def test_an_inherited_report_variable_cannot_aim_the_report(
    tmp_path: Path, isolated: Environment
) -> None:
    """The hook ASSIGNS the variable; a value planted in the environment is overwritten.

    The planted place is inside the work tree, which the CS-821 check refuses for
    the hook's own directory. Were the planted value used, pytest would write
    there and the hook would find no report of its own.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    # Built from tmp_path, never from the sandbox's withheld field (the locals guard).
    planted = tmp_path / "work" / "planted-report.xml"
    result = push(box, extra_env={REPORT_ENV: str(planted)})
    assert result.landed, f"a planted report variable broke an ordinary push:\n{result.report}"
    written = planted.exists()
    assert not written, "pytest wrote its report where an inherited variable aimed it"


#: Other spellings of the report variable. sh keeps each spelling as a variable
#: of its own, but a Windows child resolves its environment case-insensitively,
#: so an inherited spelling could outrank the hook's own assignment there.
REPORT_ENV_VARIANTS: Final = (REPORT_ENV.lower(), "Cs_Push_Report")


@pytest.mark.parametrize("spelling", REPORT_ENV_VARIANTS, ids=["lower-case", "mixed-case"])
def test_an_inherited_case_variant_of_the_report_variable_cannot_aim_the_report(
    tmp_path: Path, isolated: Environment, spelling: str
) -> None:
    """CS-1349 repair. A planted case variant must not aim the report either.

    RED at bb4458fe on Windows, measured by a distinct adversary: the variant
    reached pytest beside the hook's own name, pytest wrote the report inside
    the work tree, and the push was refused as "no report".
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    # Built from tmp_path, never from the sandbox's withheld field (the locals guard).
    planted = tmp_path / "work" / "planted-report.xml"
    result = push(box, extra_env={spelling: str(planted)})
    written = planted.exists()
    assert not written, "pytest wrote its report where an inherited case variant aimed it"
    assert result.landed, f"a planted case variant broke an ordinary push:\n{result.report}"


#: Stands in for a sandbox's suite gate. It loads the REAL kit file installed
#: beside it, records only WHETHER the kit's own ``commit_margin_mb()`` reads 0 in
#: the process the hook starts as the gate - never the value - and exits 3, the
#: gate's own refusal code, without running the suite, so no arm can wait on the
#: machine's free commit.
MARGIN_SPY_GATE: Final = (
    "import json\n"
    "import runpy\n"
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "kit = runpy.run_path(str(Path(__file__).with_name('fleet_suite_gate_real.py')))\n"
    "record = Path(kit['gate_dir']()) / 'cs1349-margin-spy.json'\n"
    "record.parent.mkdir(parents=True, exist_ok=True)\n"
    "record.write_text(json.dumps({'zero': kit['commit_margin_mb']() == 0}))\n"
    "sys.exit(3)\n"
)

#: Where the spy writes its one boolean, inside the sandbox's slot directory.
MARGIN_SPY_RECORD: Final = "cs1349-margin-spy.json"


@pytest.mark.parametrize(
    ("override", "reads_zero"), [(None, True), ("", False)], ids=["margin-set", "control-emptied"]
)
def test_the_sandbox_margin_reaches_the_kit_gate_as_zero(
    tmp_path: Path, isolated: Environment, override: str | None, reads_zero: bool
) -> None:
    """CS-1349 grant clause C, proved where it acts: inside the gate's own process.

    ``isolated`` sets the margin through ``tests/fleet_hook_kit.py::commit_margin_env``.
    A real push through the tracked hook starts the spy as the gate, and the
    KIT's reader answers 0. THE CONTROL empties the variable for one push and the
    same reader answers non-zero, so the oracle can see the difference. What the
    margin then changes in admission depends on the machine's free commit and is
    not measured here.
    """
    box = make_sandbox(tmp_path, isolated, tests=suite_of(PASSING_TEST, 3))
    # Built from tmp_path, never from the sandbox's withheld field (the locals guard).
    kit = tmp_path / "work" / "ops" / "fleet_kit"
    (kit / "fleet_suite_gate_real.py").write_bytes((kit / "fleet_suite_gate.py").read_bytes())
    (kit / "fleet_suite_gate.py").write_bytes(MARGIN_SPY_GATE.encode("ascii"))
    extra = {} if override is None else {COMMIT_MARGIN_ENV: override}
    result = push(box, extra_env=extra)
    record = Path(suite_dir_env(tmp_path)[SUITE_DIR_ENV]) / MARGIN_SPY_RECORD
    ran = record.is_file()
    assert ran, f"the spy never ran as the gate:\n{result.report}"
    zero = json.loads(record.read_bytes())["zero"]
    assert zero is reads_zero, f"the kit's margin reader answered zero={zero}"
    assert not result.landed, "a push whose gate never ran the suite moved the remote"


def test_the_suite_line_hands_pytest_the_report_through_one_quoted_word() -> None:
    """The CS-1349 static half: the word, its export, and no per-run path among the words.

    One suite line; it carries the single-quoted word once and no ``$CS_REPORT``
    expansion; the hook exports the variable exactly once.
    """
    lines = TRACKED_HOOK.read_bytes().decode("ascii").split("\n")
    suite = [line for line in lines if "fleet_suite_gate.py" in line and " run " in line]
    count = len(suite)
    assert count == 1, f"the hook carries {count} suite lines, not one"
    words = suite[0].split(" -- ", 1)[1]
    quoted = words.count("--junitxml " + REPORT_WORD)
    assert quoted == 1, f"the suite line hands the report word {quoted} times, not once"
    per_run = "$CS_REPORT" in words
    assert not per_run, "a per-run report path is still among the command words"
    exported = sum(1 for line in lines if line.strip() == "export " + REPORT_ENV)
    assert exported == 1, f"the hook exports the report variable on {exported} lines, not one"
