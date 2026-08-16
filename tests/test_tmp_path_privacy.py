#!/usr/bin/env python3
"""CS-428 - a forced failure in a tmp_path test renders no home path, no account name.

THE CHANNEL, named precisely, because the remedy depends on which one it is.
pytest renders the FRAME ARGUMENTS of a failing frame whenever the traceback
style is long, and long is the default. Any test taking ``tmp_path``, or a
fixture derived from it, therefore prints a line shaped like

    tmp_path = WindowsPath('<home>/AppData/Local/Temp/pytest-of-<user>/...')

with no ``-l`` and no ``--tb`` override anywhere. On Windows the pytest base
temporary directory sits under the user profile AND its own directory name
embeds ``getpass.getuser()``, so that one line carries an absolute home path
plus the Windows account name twice. CLAUDE.md non-negotiable 3 forbids the
account name and any home path in this project's output; non-negotiable 12
counts an error message and a debug dump as echo paths. This is both.

It is NOT the assertion-message channel and it is not a rendering of a caught
exception object, so ``tests/test_exception_rendering.py`` is structurally
blind to it - that module keys on an AST shape inside a handler, and a frame
argument is emitted by the reporter after the test has already died.

HOW THIS IS GRADED. The subject is what pytest ACTUALLY PRINTS, so the only
honest oracle is a real pytest run's real output. Each arm writes a synthetic
test module into a sandbox, runs ``python -m pytest`` on it as a subprocess,
and scans the captured text. The acceptance arm adds no flags at all, because
"under DEFAULT pytest flags" is the item's literal wording; the arms below it
add one flag each to reach a channel the default style does not render. Two
exception types are forced, and the pair is deliberate: ``SystemExit`` was live
disclosure in an earlier session, rendering under ``-q`` alone, while other
BaseExceptions behave differently - so a harness that covered only the ordinary
``AssertionError`` path would be measuring the easy case.

ONE ARM IS NOT A SUBPROCESS PAIR, AND CANNOT BE. The redaction rules are
derived from the environment, and a cold subprocess always derives them from a
clean one - so no pair of subprocesses can observe a rule set that an EARLIER
TEST influenced. That arm runs a home-repointing failure and an ordinary victim
inside ONE session, in an asserted order.

THE CONTROL IS THE HALF THAT MAKES THE REST MEAN ANYTHING. A sweep that finds
nothing is indistinguishable from a sweep that looks for nothing, so every
guarded arm is paired with the same sandbox run with the redaction NOT
installed, asserting the markers ARE present there. If a control arm ever finds
none, this module proves nothing and says so in those words rather than passing.

DETECTED IS NOT CRASHED. Every arm asserts that its sandbox ran tests and
failed, and that the failure blocks it expected were rendered. A sandbox that
died during collection renders no account name either, and that is not the
property under test.

THE MARKERS ARE DERIVED AT RUNTIME AND ARE NEVER PRINTED. Writing this
machine's account name into a tracked file would commit the exact string the
item exists to suppress, so the oracle reads the home directory and the login
name at run time, and every failure message below reports COUNTS and LINE
NUMBERS only. Nothing here echoes the matched text, on any path.

THE ORACLE IS NOT THE REDACTOR. A redactor is blind exactly where it is blind,
so it can never be its own oracle. The spellings scanned for here are derived
from ``Path.home()`` and ``getpass.getuser()`` directly, by this module, and
the short-name token is derived from a different rule than the one the redactor
uses. Only the two placeholder constants are imported, and those are checked as
the remedy's FINGERPRINT rather than used as the test of whether it worked.

STATED LIMITS, since a green run here should not be read as more than it is.
The graded region is :func:`guarded_region`: the tail of a real run from the
FAILURES banner onward - traceback, frame arguments, locals under ``-l``, crash
lines, short summary and final counts - MINUS pytest's warnings summary, which
pytest composes from its own warning store rather than from a report and which
the remedy therefore does not reach. That exclusion is measured rather than
assumed; see
test_the_warnings_summary_is_a_measured_residual_and_not_a_covered_channel,
which forces a marker into the warnings summary and pins where it lands. Two
further limits: the session header names the sandbox root, which
test_only_the_session_header_names_the_sandbox_root bounds to known prefixes in
both arms; and collection-time reports, ``--co`` output, internal errors and
output from any process this suite starts are all outside the region.

And pytest sanitizes the login name when it builds ``pytest-of-<user>``, so an
account name containing a non-word character would reach the directory in a
spelling this oracle does not construct - on such a machine the control arm
goes red saying the grading was inconclusive, which is the intended failure
direction.
"""

from __future__ import annotations

import contextlib
import getpass
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.conftest import REDACTED_HOME, REDACTED_USER

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT = 300

#: pytest's exit code when tests ran and at least one of them failed.
PYTEST_TESTS_FAILED = 1

#: Both synthetic tests must be collected and both must fail, in every arm.
EXPECTED_FAILURES = 2

#: A home directory is at least a root plus a name. Anything shorter is a bare
#: drive or filesystem root, which is not personal data and would match half
#: the output if it were scanned for.
MIN_HOME_SPELLING = 4

SANDBOX_TEST_FILENAME = "test_forced_failures.py"
MEMORY_TEST = "test_forced_memory_error"
EXIT_TEST = "test_forced_system_exit"
DERIVED_FIXTURE = "isolated_work_root"

FAILURES_BANNER = "= FAILURES ="
SUMMARY_BANNER = " short test summary info "
WARNINGS_BANNER = " warnings summary "

#: A pytest section banner: "===== name =====". Used to bound the warnings
#: block, which sits INSIDE the tail of the run that starts at the FAILURES
#: banner and which the remedy provably does not reach - see
#: test_the_warnings_summary_is_a_measured_residual_and_not_a_covered_channel.
_SECTION_BANNER = re.compile(r"^=+ .+ =+$")

#: Session-header lines that may legitimately name the sandbox root. The
#: harness has to put its sandbox SOMEWHERE, and on Windows ``tmp_path`` is
#: under the user profile, so pytest's own "rootdir:" line reports where this
#: harness stood rather than anything the failure rendering produced. It is
#: byte-identical in the control arm and the guarded arm, which is what makes
#: excluding it a scoping decision rather than a place to hide a leak - and
#: test_only_the_session_header_names_the_sandbox_root asserts that no OTHER
#: header line carries a marker, in both arms.
HEADER_PREFIXES_THAT_MAY_NAME_THE_SANDBOX = (
    "rootdir:",
    "configfile:",
    "testpaths:",
    "cachedir:",
)

#: One failure block per test, as pytest centres it: "____ test_name ____".
_BLOCK_BANNER = re.compile(r"^_+ (?P<name>\S+) _+$")


# ---------------------------------------------------------------------------
# The sandbox
# ---------------------------------------------------------------------------

# Two forced failures, one reached through a fixture DERIVED from tmp_path and
# one taking tmp_path directly. The derived shape is the one the item measured
# in the wild, and it is the shape a fixture-return-type change would miss.
SANDBOX_TESTS = '''
"""Synthetic module: two forced failures in tests that take tmp_path."""

from pathlib import Path

import pytest


@pytest.fixture
def isolated_work_root(tmp_path: Path) -> Path:
    """A fixture DERIVED from tmp_path, which is the measured leak shape."""
    root = tmp_path / "work"
    root.mkdir()
    return root


def test_forced_memory_error(isolated_work_root: Path) -> None:
    assert isolated_work_root.exists()
    raise MemoryError("forced by the CS-428 grading harness")


def test_forced_system_exit(tmp_path: Path) -> None:
    assert tmp_path.exists()
    raise SystemExit("forced by the CS-428 grading harness")
'''

# A test module whose FIRST test repoints the home directory and fails while
# the patch is live, and whose SECOND test is an ordinary tmp_path victim. The
# ORDER is the whole point and it is asserted from the output rather than
# assumed. The victim's source carries the ordinary English word "home" so a
# rule set that mistook the patched directory's name for an account name is
# visible as mangling, not only as a missing redaction.
#
# The shape is copied from real shipped tests rather than invented - several
# modules monkeypatch USERPROFILE at a tmp_path directory named "home".
SANDBOX_POISON_TESTS = '''
"""Synthetic module: a home-repointing failure, then an ordinary victim."""

import tempfile
from pathlib import Path

import pytest


def test_aaa_repoints_the_home_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake_home = tmp_path / "home"
    (fake_home / "AppData" / "Local").mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    raise AssertionError("forced while the home directory is repointed")


def test_zzz_a_later_victim_renders_no_home_path(tmp_path: Path) -> None:
    sentence = "the run is on the home stretch"
    assert sentence
    raise MemoryError("forced by the CS-428 harness under " + tempfile.gettempdir())
'''

# A module whose failure message carries a URL-QUOTED path. urllib quotes a
# Windows separator as "%5C", whose last character is alphanumeric, so an
# account-name rule bounded by "not a word character" refuses to match the name
# beside it. The ordinary token in the source line is the blast-radius control:
# widening that boundary must not start rewriting text that merely sits next to
# a percent sign.
SANDBOX_QUOTED_TESTS = '''
"""Synthetic module: a forced failure whose message carries a quoted path."""

from pathlib import Path
from urllib.parse import quote


def test_forced_error_with_a_quoted_path(tmp_path: Path) -> None:
    note = "coverage held at 100%3A of the target"
    assert note
    raise MemoryError("forced by the CS-428 harness under " + quote(str(tmp_path)))
'''

# A module that warns with a tmp_path value. pytest renders the warnings
# summary after the FAILURES section and builds it from its own warning store
# rather than from a TestReport, so the report hook cannot reach it. This
# sandbox exists to MEASURE that residual rather than leave it implied.
SANDBOX_WARNING_TESTS = '''
"""Synthetic module: a warning carrying tmp_path, plus one forced failure."""

import warnings
from pathlib import Path


def test_warns_with_the_temp_path(tmp_path: Path) -> None:
    warnings.warn(str(tmp_path), UserWarning, stacklevel=1)


def test_forced_memory_error(tmp_path: Path) -> None:
    assert tmp_path.exists()
    raise MemoryError("forced by the CS-428 grading harness")
'''

# The guarded arm installs the repository's redaction and NOTHING else, by
# importing the real tests/conftest.py by dotted name and re-exporting whatever
# pytest hooks it defines. Loading it that way is what makes this arm a test of
# the shipped remedy rather than of a copy of it that could drift, and the
# re-export is by PREFIX rather than by a written list so a hook added to the
# remedy is exercised here without this string being edited to match. The repo
# root is interpolated at run time; a spelled-out path in a tracked file is
# itself a violation.
SANDBOX_CONFTEST = '''
"""Install the repository's failure-report redaction into this sandbox."""

import sys

sys.path.insert(0, {repo_root!r})

from tests import conftest as _shipped  # noqa: E402

for _name in dir(_shipped):
    if _name.startswith("pytest_"):
        globals()[_name] = getattr(_shipped, _name)
'''


@dataclass(frozen=True, repr=False)
class SandboxRun:
    """One captured pytest run, held so its text can never become a func arg.

    ``repr=False`` and the custom ``__repr__`` are the point of the class. The
    control arm's output CONTAINS the account name, and pytest renders a
    fixture value as a frame argument on any failure - so a plain str fixture
    would put the leak straight back into this suite's own output through the
    exact channel under test. The label and the size are all a reader needs.
    """

    label: str
    returncode: int
    output: str

    def __repr__(self) -> str:
        """Render as a label and a size - never the captured text."""
        return f"<SandboxRun {self.label} rc={self.returncode} chars={len(self.output)}>"


def _build_sandbox(root: Path, *, guarded: bool, body: str = SANDBOX_TESTS) -> Path:
    """Write the synthetic test module, and the redaction conftest if guarded."""
    root.mkdir(parents=True, exist_ok=True)
    (root / SANDBOX_TEST_FILENAME).write_bytes(body.encode("ascii"))
    if guarded:
        conftest = SANDBOX_CONFTEST.format(repo_root=str(REPO_ROOT))
        (root / "conftest.py").write_bytes(conftest.encode("ascii"))
    return root


def _run_sandbox(root: Path, label: str, *args: str) -> SandboxRun:
    """Run pytest on the sandbox with DEFAULT flags plus whatever ``args`` adds.

    ``PYTEST_ADDOPTS`` is stripped from the child environment on purpose: it
    would silently add flags from the parent session, and "under DEFAULT pytest
    flags" is the literal wording of this item's acceptance.
    """
    env = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_CURRENT_TEST", "PYTEST_DEBUG_TEMPROOT", "PYTHONPATH"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", SANDBOX_TEST_FILENAME, *args],
        cwd=str(root),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        check=False,
    )
    return SandboxRun(label, completed.returncode, completed.stdout + completed.stderr)


@pytest.fixture(scope="module")
def control_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The sandbox with NO redaction installed - the proof this harness can fail."""
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_control"), guarded=False)
    return _run_sandbox(root, "control")


@pytest.fixture(scope="module")
def guarded_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The sandbox with the shipped redaction installed, default flags."""
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_guarded"), guarded=True)
    return _run_sandbox(root, "guarded")


@pytest.fixture(scope="module")
def guarded_showlocals_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The guarded sandbox under ``-l``, which widens the same longrepr channel."""
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_locals"), guarded=True)
    return _run_sandbox(root, "guarded-showlocals", "-l")


@pytest.fixture(scope="module")
def guarded_tb_line_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The guarded sandbox under ``--tb=line``, which renders the CRASH LOCATION.

    A different channel from the one the default style uses. Under this style
    pytest prints ``str(report.longrepr.reprcrash)`` itself rather than asking
    the longrepr to render, so a remedy that only rewrites the rendered
    traceback text never reaches the crash path.
    """
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_tbline"), guarded=True)
    return _run_sandbox(root, "guarded-tb-line", "--tb=line")


@pytest.fixture(scope="module")
def control_tb_line_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """``--tb=line`` with NO redaction - the proof that style renders a crash path."""
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_tbline_ctl"), guarded=False)
    return _run_sandbox(root, "control-tb-line", "--tb=line")


@pytest.fixture(scope="module")
def guarded_xdist_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The guarded sandbox under ``-n 2`` - the shape CI actually runs.

    xdist attaches the worker to the report IN THE CONTROLLER, after the
    worker's own report hook has already run, and pytest then renders a worker
    line naming the worker's interpreter. A worker-side remedy alone cannot see
    it.
    """
    pytest.importorskip("xdist", reason="the parallel lane needs pytest-xdist")
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_xdist"), guarded=True)
    return _run_sandbox(root, "guarded-xdist", "-n", "2")


@pytest.fixture(scope="module")
def control_xdist_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """``-n 2`` with NO redaction - the proof the parallel lane renders markers."""
    pytest.importorskip("xdist", reason="the parallel lane needs pytest-xdist")
    root = _build_sandbox(tmp_path_factory.mktemp("cs428_xdist_ctl"), guarded=False)
    return _run_sandbox(root, "control-xdist", "-n", "2")


@pytest.fixture(scope="module")
def guarded_poison_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """One session: a home-repointing failure FIRST, then an ordinary victim.

    THE SHAPE A COLD SUBPROCESS CANNOT GRADE. Every other arm in this module
    starts a fresh interpreter, so each one measures a rule set built from a
    clean environment. A rule set derived lazily is built from whatever the
    environment held when the FIRST report needed it, and a test that repoints
    the home directory before failing is therefore able to decide what the rest
    of the session redacts. Both halves have to run in ONE session for that to
    be observable at all.
    """
    root = _build_sandbox(
        tmp_path_factory.mktemp("cs428_poison"), guarded=True, body=SANDBOX_POISON_TESTS
    )
    return _run_sandbox(root, "guarded-poisoned")


@pytest.fixture(scope="module")
def control_poison_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The poisoning sandbox with NO redaction - proof the victim block renders markers."""
    root = _build_sandbox(
        tmp_path_factory.mktemp("cs428_poison_ctl"), guarded=False, body=SANDBOX_POISON_TESTS
    )
    return _run_sandbox(root, "control-poisoned")


@pytest.fixture(scope="module")
def guarded_quoted_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The guarded sandbox whose failure message carries a URL-quoted path."""
    root = _build_sandbox(
        tmp_path_factory.mktemp("cs428_quoted"), guarded=True, body=SANDBOX_QUOTED_TESTS
    )
    return _run_sandbox(root, "guarded-quoted")


@pytest.fixture(scope="module")
def control_quoted_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The quoted-path sandbox with NO redaction - proof the quoted form renders."""
    root = _build_sandbox(
        tmp_path_factory.mktemp("cs428_quoted_ctl"), guarded=False, body=SANDBOX_QUOTED_TESTS
    )
    return _run_sandbox(root, "control-quoted")


@pytest.fixture(scope="module")
def guarded_warning_run(tmp_path_factory: pytest.TempPathFactory) -> SandboxRun:
    """The guarded sandbox with a warning carrying tmp_path - the residual arm."""
    root = _build_sandbox(
        tmp_path_factory.mktemp("cs428_warn"), guarded=True, body=SANDBOX_WARNING_TESTS
    )
    return _run_sandbox(root, "guarded-warning")


# ---------------------------------------------------------------------------
# The oracle - derived at run time, never printed
# ---------------------------------------------------------------------------


def _resolved(path: Path) -> Path:
    """Resolve, tolerating a filesystem that refuses. Expands 8.3 names on Windows."""
    try:
        return path.resolve()
    except OSError:
        return path


def home_path_spellings() -> tuple[str, ...]:
    """Every spelling of THIS machine's home directory a render could emit.

    Both separator conventions, because they come from different calls:
    ``str(Path)`` uses the native separator and ``PurePath.__repr__`` uses
    ``as_posix()``, and the measured leak is a repr.

    Returns:
        Longest first, so a caller reporting an index reports the widest hit.
    """
    spellings: set[str] = set()
    home = Path.home()
    for candidate in (home, _resolved(home)):
        spellings.add(str(candidate))
        spellings.add(candidate.as_posix())
    return tuple(sorted((s for s in spellings if s), key=len, reverse=True))


def account_name_spellings() -> tuple[str, ...]:
    """Every spelling of THIS machine's account name a render could emit.

    The short-name token is derived by a rule of this module's own - any
    component of the temporary directory carrying a tilde is an 8.3 short name
    - rather than by the rule the redactor uses. Two derivations that agree are
    worth something; one derivation checked against itself is worth nothing.

    Returns:
        Sorted, deduplicated, non-empty.
    """
    names: set[str] = {Path.home().name, _resolved(Path.home()).name}
    with contextlib.suppress(OSError, KeyError):
        names.add(getpass.getuser())
    for variable in ("USERNAME", "USER", "LOGNAME"):
        names.add(os.environ.get(variable, ""))
    names.update(part for part in Path(tempfile.gettempdir()).parts if "~" in part)
    return tuple(sorted(name for name in names if name.strip()))


def temp_root_is_under_home() -> bool:
    """Report whether the pytest base temp directory sits under the home directory.

    True on Windows, where it is the whole defect. False on a Linux runner,
    where ``/tmp`` carries the account name in ``pytest-of-<user>`` but no home
    path - so the home-path half of the control assertion is conditioned on
    this rather than asserted blind and going red on CI for being right.
    """
    try:
        return _resolved(Path(tempfile.gettempdir())).is_relative_to(_resolved(Path.home()))
    except (OSError, ValueError):
        return False


def hit_counts(text: str, markers: Sequence[str]) -> list[tuple[int, int]]:
    """Count each marker in ``text``, case-insensitively, WITHOUT returning it.

    Args:
        text: The captured output to scan.
        markers: The derived spellings.

    Returns:
        ``(marker index, occurrences)`` for every marker that occurs at least
        once. The marker itself is deliberately not in the result.
    """
    lowered = text.lower()
    counts = ((index, lowered.count(marker.lower())) for index, marker in enumerate(markers))
    return [(index, count) for index, count in counts if count]


def leaky_line_numbers(text: str, markers: Sequence[str]) -> list[int]:
    """1-based line numbers carrying any marker - safe to print, unlike the lines."""
    lowered = [marker.lower() for marker in markers]
    return [
        number
        for number, line in enumerate(text.splitlines(), 1)
        if any(marker in line.lower() for marker in lowered)
    ]


def failures_section(output: str) -> str:
    """Everything from the FAILURES banner to the end of the run.

    The whole TAIL, not only the per-test blocks: it also carries the warnings
    summary, the short test summary and the final counts line. Callers that
    mean "the region the report hook can reach" want :func:`guarded_region`.
    """
    index = output.find(FAILURES_BANNER)
    return "" if index < 0 else output[index:]


def warnings_block(output: str) -> str:
    """Just pytest's warnings summary, banner excluded, or empty if there is none.

    Built by pytest from its own warning store rather than from a TestReport,
    which is why a report hook cannot reach it and why this module measures it
    separately instead of folding it into the graded region.
    """
    kept: list[str] = []
    inside = False
    for line in failures_section(output).splitlines():
        if _SECTION_BANNER.match(line):
            inside = WARNINGS_BANNER in line
        elif inside:
            kept.append(line)
    return "\n".join(kept)


def guarded_region(output: str) -> str:
    """The run tail MINUS the warnings summary - the region the remedy reaches.

    The exclusion is exactly one banner-delimited block. Where that boundary
    actually falls is measured by
    test_the_warnings_summary_is_a_measured_residual_and_not_a_covered_channel
    rather than asserted here.
    """
    kept: list[str] = []
    inside = False
    for line in failures_section(output).splitlines():
        if _SECTION_BANNER.match(line):
            inside = WARNINGS_BANNER in line
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def header_section(output: str) -> str:
    """The output BEFORE the FAILURES banner - the session header."""
    index = output.find(FAILURES_BANNER)
    return output if index < 0 else output[:index]


def failure_blocks(output: str) -> dict[str, str]:
    """Split the FAILURES section into one block per failing test, by its banner.

    A block ends at the next per-test banner or at ANY section banner. Ending
    it only at the short-summary banner would attribute the whole warnings
    summary to whichever test happened to fail last.
    """
    blocks: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in failures_section(output).splitlines():
        banner = _BLOCK_BANNER.match(line)
        if banner is not None:
            current = []
            blocks[banner.group("name")] = current
        elif _SECTION_BANNER.match(line):
            current = None
        elif current is not None:
            current.append(line)
    return {name: "\n".join(lines) for name, lines in blocks.items()}


def assert_ran_and_rendered(run: SandboxRun, expected_blocks: Sequence[str]) -> None:
    """DETECTED, not CRASHED: the run failed tests and rendered the named blocks.

    A sandbox that died during collection renders no account name either, and
    that is not the property under test.
    """
    assert run.returncode == PYTEST_TESTS_FAILED, (
        f"the {run.label} sandbox exited {run.returncode}; expected "
        f"{PYTEST_TESTS_FAILED}, which is 'tests ran and failed'. A sandbox "
        f"that crashed or collected nothing renders no account name either, "
        f"and that is not the property under test."
    )
    assert "INTERNALERROR" not in run.output, f"the {run.label} sandbox hit an internal error"
    blocks = failure_blocks(run.output)
    assert set(blocks) == set(expected_blocks), (
        f"the {run.label} sandbox rendered failure blocks {sorted(blocks)}, "
        f"expected exactly {sorted(expected_blocks)}"
    )


def assert_ran_and_failed_both(run: SandboxRun) -> None:
    """DETECTED, not CRASHED: two tests were collected and both failed."""
    assert f"collected {EXPECTED_FAILURES} items" in run.output, (
        f"the {run.label} sandbox did not collect {EXPECTED_FAILURES} tests"
    )
    assert f"{EXPECTED_FAILURES} failed" in run.output, (
        f"the {run.label} sandbox did not report {EXPECTED_FAILURES} failures"
    )
    assert_ran_and_rendered(run, (MEMORY_TEST, EXIT_TEST))


# ---------------------------------------------------------------------------
# The control - without this, everything below is a green light with nothing
# behind it
# ---------------------------------------------------------------------------


def test_the_oracle_is_not_vacuous() -> None:
    # Both marker sets must be non-empty and non-trivial before any arm is
    # scanned with them. An empty marker list finds nothing on every input.
    homes = home_path_spellings()
    names = account_name_spellings()
    assert homes, "no home-directory spelling could be derived; the scan would be vacuous"
    assert names, "no account-name spelling could be derived; the scan would be vacuous"
    assert all(len(spelling) >= MIN_HOME_SPELLING for spelling in homes), (
        "a home-directory spelling is shorter than a bare drive or filesystem "
        "root, so it is not a home directory and scanning for it would be worse "
        "than vacuous - it would match everywhere"
    )


def test_the_control_run_proves_this_harness_can_see_a_leak(control_run: SandboxRun) -> None:
    # THE POSITIVE CONTROL. The same sandbox, the same forced failures, the
    # same default flags - with the redaction NOT installed. If this finds
    # nothing, the guarded arms below are indistinguishable from a scan that
    # looks for nothing, and this says exactly that instead of passing.
    assert_ran_and_failed_both(control_run)
    section = failures_section(control_run.output)

    names = hit_counts(section, account_name_spellings())
    assert names, (
        "the UNGUARDED control rendered no account-name spelling at all, so this "
        "module proves nothing on this machine. Suspect the oracle before the "
        "remedy: pytest strips non-word characters when it builds its base "
        "temporary directory name, so an account name carrying one reaches the "
        "path in a spelling derived here."
    )

    if temp_root_is_under_home():
        homes = hit_counts(section, home_path_spellings())
        assert homes, (
            "the base temporary directory IS under the home directory on this "
            "machine, yet the unguarded control rendered no home path. The "
            "oracle and the render disagree; do not trust the guarded arms."
        )


def test_the_control_run_leaks_through_both_exception_types(control_run: SandboxRun) -> None:
    # The pair is the point: SystemExit is a non-OSError that was live
    # disclosure in an earlier session. Measuring only the MemoryError block
    # would leave the harder half unmeasured.
    blocks = failure_blocks(control_run.output)
    markers = account_name_spellings()
    for name in (MEMORY_TEST, EXIT_TEST):
        assert hit_counts(blocks[name], markers), (
            f"the unguarded control's {name} block carries no account-name "
            f"spelling, so the guarded assertion for that block proves nothing"
        )


# ---------------------------------------------------------------------------
# The graded property
# ---------------------------------------------------------------------------


def test_a_forced_memory_error_renders_no_home_path_and_no_account_name(
    guarded_run: SandboxRun,
) -> None:
    # ACCEPTANCE, first half: a fixture DERIVED from tmp_path, killed by a
    # MemoryError, under default flags.
    assert_ran_and_failed_both(guarded_run)
    block = failure_blocks(guarded_run.output)[MEMORY_TEST]

    assert f"{DERIVED_FIXTURE} =" in block, (
        "the derived fixture is no longer rendered as a frame argument at all, "
        "so this block no longer covers the measured leak shape"
    )
    assert "MemoryError" in block, "the forced MemoryError did not reach the report"
    _assert_no_personal_data(block, f"the guarded {MEMORY_TEST} block")


def test_a_forced_system_exit_renders_no_home_path_and_no_account_name(
    guarded_run: SandboxRun,
) -> None:
    # ACCEPTANCE, second half: tmp_path taken directly, killed by a SystemExit.
    # SystemExit is a BaseException that does not pass through an ordinary
    # `except Exception`, which is why it is forced separately.
    block = failure_blocks(guarded_run.output)[EXIT_TEST]

    assert "tmp_path =" in block, (
        "tmp_path is no longer rendered as a frame argument at all, so this "
        "block no longer covers the measured leak shape"
    )
    assert "SystemExit" in block, "the forced SystemExit did not reach the report"
    _assert_no_personal_data(block, f"the guarded {EXIT_TEST} block")


def test_the_whole_guarded_region_is_clean(guarded_run: SandboxRun) -> None:
    # Wider than the two blocks: the region also carries the traceback source
    # lines, the crash locations, the short summary and the final counts line.
    _assert_no_personal_data(guarded_region(guarded_run.output), "the guarded region")


def test_showlocals_widens_the_channel_without_widening_the_leak(
    guarded_showlocals_run: SandboxRun,
) -> None:
    # -l puts the same values through the locals sub-channel of the same
    # longrepr. Not required by the acceptance, which names default flags, and
    # measured anyway because the next reader will reach for -l on a real
    # failure and should not be handed a leak for it.
    assert_ran_and_failed_both(guarded_showlocals_run)
    section = failures_section(guarded_showlocals_run.output)
    assert "tmp_path     = " in section or "tmp_path   = " in section or "tmp_path = " in section, (
        "the -l arm rendered no tmp_path local at all; it is not covering the channel it claims to"
    )
    _assert_no_personal_data(section, "the guarded FAILURES section under -l")


def test_the_path_was_redacted_rather_than_deleted(guarded_run: SandboxRun) -> None:
    # A remedy that blanked the whole report would also pass every assertion
    # above. The placeholders are the remedy's fingerprint, and the surviving
    # tail of the path is the evidence that the VALUE was rewritten in place
    # rather than the line dropped.
    section = failures_section(guarded_run.output)
    assert REDACTED_USER in section, (
        "no account-name placeholder is present, so nothing was redacted - "
        "either the hook did not run or it matched nothing"
    )
    assert REDACTED_HOME in section or "pytest-of-" in section, (
        "neither a home placeholder nor the surviving base-temp prefix is "
        "present; the report looks blanked rather than redacted"
    )
    assert "pytest-of-" in section, "the base temp directory name did not survive redaction"
    assert MEMORY_TEST in section, "the MemoryError test name did not survive redaction"
    assert EXIT_TEST in section, "the SystemExit test name did not survive redaction"


def test_the_short_summary_still_names_the_exception(guarded_run: SandboxRun) -> None:
    # A REGRESSION THIS SLICE ALREADY CAUSED ONCE, so it is graded rather than
    # remembered. Handing pytest a bare redacted string works for the FAILURES
    # section and quietly wrecks the "-ra" line, because pytest uses the whole
    # string as the summary message - every redacted failure then summarised
    # itself as the first line of its own traceback instead of naming its
    # exception. The remedy keeps a redacted crash location, and this is what
    # says so.
    section = failures_section(guarded_run.output)
    assert f"{MEMORY_TEST} - MemoryError" in section, (
        "the short summary line no longer names the exception for the "
        "MemoryError case; the redacted report lost its crash location"
    )
    assert f"{EXIT_TEST} - SystemExit" in section, (
        "the short summary line no longer names the exception for the "
        "SystemExit case; the redacted report lost its crash location"
    )


def test_only_the_session_header_names_the_sandbox_root(
    control_run: SandboxRun, guarded_run: SandboxRun
) -> None:
    # The scoping decision, asserted rather than assumed. This harness must put
    # its sandbox somewhere and on Windows tmp_path is under the user profile,
    # so pytest's own rootdir line names it. That line is identical in both
    # arms. What this pins is that NO OTHER header line carries a marker, in
    # either arm - so "we looked at the FAILURES section" is a scope and not a
    # place to hide one.
    markers = (*home_path_spellings(), *account_name_spellings())
    for run in (control_run, guarded_run):
        offenders = [
            line.split(":", 1)[0]
            for line in header_section(run.output).splitlines()
            if hit_counts(line, markers)
            and not line.startswith(HEADER_PREFIXES_THAT_MAY_NAME_THE_SANDBOX)
        ]
        assert not offenders, (
            f"the {run.label} session header carries a marker on a line this "
            f"module does not account for; leading tokens: {sorted(set(offenders))}"
        )


# ---------------------------------------------------------------------------
# The failure modes AROUND the remedy - each one measured in the shape that
# produces it, because none of them is visible in the default single-process
# arm above
# ---------------------------------------------------------------------------


def test_an_earlier_test_that_repoints_the_home_directory_cannot_poison_a_later_report(
    control_poison_run: SandboxRun, guarded_poison_run: SandboxRun
) -> None:
    # ONE SESSION, IN THE RECORDED ORDER. A rule set derived on demand is
    # derived from whatever the environment holds when the first report needs
    # it, and several shipped tests repoint USERPROFILE at a tmp_path directory
    # while failing. The control arm proves the victim block renders markers at
    # all; the guarded arm is the graded half.
    poisoner = "test_aaa_repoints_the_home_directory"
    victim = "test_zzz_a_later_victim_renders_no_home_path"

    for run in (control_poison_run, guarded_poison_run):
        assert_ran_and_rendered(run, (poisoner, victim))
        order = [name for name in _rendered_block_order(run.output) if name in {poisoner, victim}]
        assert order == [poisoner, victim], (
            f"the {run.label} sandbox rendered {order}; this arm only means "
            f"something if the repointing failure is reported FIRST"
        )

    control_blocks = failure_blocks(control_poison_run.output)
    assert hit_counts(control_blocks[victim], account_name_spellings()), (
        "the UNGUARDED victim block carries no account-name spelling, so the "
        "guarded assertion below proves nothing on this machine"
    )

    blocks = failure_blocks(guarded_poison_run.output)
    _assert_no_personal_data(blocks[poisoner], "the guarded repointing block")
    _assert_no_personal_data(blocks[victim], "the guarded victim block")
    _assert_no_personal_data(guarded_region(guarded_poison_run.output), "the guarded region")

    # The other direction of the same defect, and the one that reads as noise
    # rather than as disclosure: a rule set built while the home directory
    # pointed at a directory NAMED "home" installs that ordinary English word
    # as an account-name spelling for the rest of the session.
    assert "the run is on the home stretch" in blocks[victim], (
        "the ordinary word 'home' was rewritten in a later report, so the "
        "redaction rules were derived from a repointed home directory"
    )


def test_a_line_style_traceback_renders_no_crash_path(
    control_tb_line_run: SandboxRun, guarded_tb_line_run: SandboxRun
) -> None:
    # A SECOND CHANNEL OUT OF THE SAME REPORT. Under --tb=line pytest prints
    # str(report.longrepr.reprcrash) itself instead of asking the longrepr to
    # render, so the crash path reaches the terminal without passing through
    # the rendered traceback text. --tb=no -ra reads the same crash message.
    for run in (control_tb_line_run, guarded_tb_line_run):
        assert_ran_and_rendered(run, ())
        assert f"{EXPECTED_FAILURES} failed" in run.output, (
            f"the {run.label} sandbox did not report {EXPECTED_FAILURES} failures"
        )

    control_region = guarded_region(control_tb_line_run.output)
    markers = (*home_path_spellings(), *account_name_spellings())
    assert hit_counts(control_region, markers), (
        "the UNGUARDED --tb=line run rendered no marker at all, so the guarded "
        "assertion below proves nothing. This arm depends on the sandbox living "
        "under a home directory; where it does not, this channel is unmeasured "
        "rather than clean."
    )

    region = guarded_region(guarded_tb_line_run.output)
    blanked = "the guarded --tb=line run no longer names its exceptions, so the crash line "
    assert "MemoryError" in region, blanked + "was blanked rather than redacted"
    assert "SystemExit" in region, blanked + "was blanked rather than redacted"
    _assert_no_personal_data(region, "the guarded --tb=line region")


def test_the_parallel_lane_renders_no_worker_interpreter_path(
    control_xdist_run: SandboxRun, guarded_xdist_run: SandboxRun
) -> None:
    # THE LANE CI ACTUALLY RUNS. .github/workflows/tier2.yml runs the suite
    # under xdist when it is available. xdist attaches the worker to the report
    # in the CONTROLLER, after the worker's own report hook has run, and pytest
    # then renders a line naming that worker's interpreter - which on this
    # machine sits under the user profile.
    for run in (control_xdist_run, guarded_xdist_run):
        assert_ran_and_rendered(run, (MEMORY_TEST, EXIT_TEST))

    markers = (*home_path_spellings(), *account_name_spellings())
    control_worker_lines = [
        line
        for line in guarded_region(control_xdist_run.output).splitlines()
        if line.startswith("[gw") and hit_counts(line, markers)
    ]
    assert control_worker_lines, (
        "the UNGUARDED parallel run rendered no worker line carrying a marker, "
        "so the guarded assertion below proves nothing on this machine"
    )

    region = guarded_region(guarded_xdist_run.output)
    assert [line for line in region.splitlines() if line.startswith("[gw")], (
        "the guarded parallel run rendered no worker line at all; the line was "
        "removed rather than redacted, which loses which worker failed"
    )
    _assert_no_personal_data(region, "the guarded parallel region")


def test_a_url_quoted_path_renders_no_account_name(
    control_quoted_run: SandboxRun, guarded_quoted_run: SandboxRun
) -> None:
    # A path that has been through URL quoting spells its separators as %5C,
    # which ends in an alphanumeric. An account-name rule whose boundary is
    # "not a word character" therefore refuses to match the name beside it and
    # renders it in full. No shipped test quotes a path today, so this arm
    # forces the shape rather than waiting for a test that produces it.
    for run in (control_quoted_run, guarded_quoted_run):
        assert run.returncode == PYTEST_TESTS_FAILED, (
            f"the {run.label} sandbox exited {run.returncode}; expected a test failure"
        )

    control_region = guarded_region(control_quoted_run.output)
    assert hit_counts(control_region, account_name_spellings()), (
        "the UNGUARDED quoted-path run rendered no account-name spelling, so "
        "the guarded assertion below proves nothing on this machine"
    )

    region = guarded_region(guarded_quoted_run.output)
    assert "MemoryError" in region, "the forced failure did not reach the guarded report"
    _assert_no_personal_data(region, "the guarded quoted-path region")

    # The blast radius stays narrow: widening the boundary must not start
    # rewriting an ordinary token that merely sits next to a percent sign.
    assert "coverage held at 100%3A of the target" in region, (
        "the widened account-name boundary is rewriting ordinary text next to a percent escape"
    )


def test_the_warnings_summary_is_a_measured_residual_and_not_a_covered_channel(
    guarded_warning_run: SandboxRun,
) -> None:
    # THE SCOPE STATEMENT AND THE SCANNED REGION, MADE TO AGREE. pytest builds
    # the warnings summary from its own warning store rather than from a
    # TestReport, so the report hook provably cannot reach it. That is stated
    # in both docstrings; what was not true is that the scanned region excluded
    # it. This test measures the boundary in BOTH directions so the exclusion
    # is a recorded residual rather than a place a leak could hide.
    run = guarded_warning_run
    assert run.returncode == PYTEST_TESTS_FAILED, (
        f"the {run.label} sandbox exited {run.returncode}; expected a test failure"
    )
    assert WARNINGS_BANNER in run.output, (
        "the warning sandbox produced no warnings summary, so this test is vacuous"
    )
    assert SUMMARY_BANNER in run.output, "the warning sandbox produced no short summary"

    markers = (*home_path_spellings(), *account_name_spellings())
    assert hit_counts(warnings_block(run.output), markers), (
        "the warnings summary carries no marker, so this test is not measuring "
        "the residual it claims to measure"
    )
    _assert_no_personal_data(guarded_region(run.output), "the guarded region beside a warning")

    # And the mis-attribution that hid it: a failure block must not swallow the
    # warnings summary that follows it.
    for name, body in failure_blocks(run.output).items():
        assert WARNINGS_BANNER not in body, (
            f"the {name} failure block absorbed the warnings summary, so a "
            f"per-block scan would be reporting on lines that are not its own"
        )


def _rendered_block_order(output: str) -> list[str]:
    """The failing-test block names in the order pytest rendered them."""
    return [
        banner.group("name")
        for banner in (_BLOCK_BANNER.match(line) for line in failures_section(output).splitlines())
        if banner is not None
    ]


def _assert_no_personal_data(text: str, what: str) -> None:
    """Assert no derived marker occurs, reporting counts and line numbers only.

    Args:
        text: The captured region to scan.
        what: A label for the failure message.

    Raises:
        AssertionError: With marker INDEXES, occurrence counts and line
            numbers. Never with the matched text - printing it here would
            commit the leak into this suite's own output, which is the defect
            under repair.
    """
    homes = home_path_spellings()
    names = account_name_spellings()
    home_hits = hit_counts(text, homes)
    name_hits = hit_counts(text, names)
    assert not home_hits, (
        f"{what} renders a home path. Home-path spelling (index, occurrences): "
        f"{home_hits}; lines {leaky_line_numbers(text, homes)}. The spellings "
        f"themselves are withheld - they are the personal data (CLAUDE.md "
        f"non-negotiable 3)."
    )
    assert not name_hits, (
        f"{what} renders the account name. Account-name spelling (index, "
        f"occurrences): {name_hits}; lines {leaky_line_numbers(text, names)}. "
        f"The spellings themselves are withheld."
    )
