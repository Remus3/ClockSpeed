#!/usr/bin/env python3
"""Tests for WHAT the repo-wide mypy invocation covers - not whether it passes.

THE DEFECT THIS FILE PINS. CI's type gate is `python -m mypy` invoked bare,
with no target (.github/workflows/tier1.yml), so pyproject.toml's mypy `files`
key is the sole authority on what gets checked. That key named only the package
and the suite, which left every file under scripts/ and tools/ outside the gate
entirely - including scripts/install_hooks.py, the first thing a fresh clone
executes and the one file whose failure leaves a clone unprotected while
reporting itself protected.

WHY A GREEN GATE WAS NOT EVIDENCE. The bare invocation exited 0 the whole time
it was checking none of those files, because a file outside `files` produces no
error rather than a failure. "The type gate is green" and "the type gate looked
at this file" are different claims, and only the second one is worth anything
about a specific file.

That is exactly the failure class CONVENTIONS.md section 7.2 names as
"'zero bad rows' is relative to a SET - state the set". Zero mypy errors was
relative to `files`, and `files` did not contain this file.

TWO SETS, NOT ONE, AND THE DIFFERENCE IS LOAD-BEARING. mypy has a DISCOVERED
set (what `files` and `exclude` resolve to, what "checked N source files"
counts) and a REPORTED-ON set (every module it actually builds, which includes
anything a discovered file imports). `exclude` filters DISCOVERY ONLY. A file
kept out of discovery is still built, and still has its errors printed, the
moment any checked file imports it. Measured, not assumed - see
``test_the_exclusion_is_discovery_only_not_containment``.

So the oracle below reports COVERAGE BY DISCOVERY and structurally cannot see
an import-pulled file. Every test here that depends on the reported-on set uses
mypy's actual error output instead, never the oracle.

THE ORACLE. ``mypy.main.process_options([])`` is precisely what the mypy CLI
calls with an empty argument list - not a re-implementation of mypy's path
resolution, and not a per-path run standing in for a repo-wide one. It reads
pyproject.toml and applies `files`, `exclude` and the namespace rules exactly
as the real run does, without paying for a type check.

THE GAP RECORD RETIRES ITSELF, AND IT HAS AN ORACLE. An earlier version of this
file recorded each gap as free prose that no test read, so a reason could be -
and was - simply false. Every entry in ``_UNCOVERED`` now carries a measured
error count that ``test_the_recorded_error_counts_are_still_accurate`` checks
against a real run, so a gap that is fixed, worsened or misdescribed turns this
file red rather than sitting there being believed.
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The acceptance criterion of CS-411, named as a path rather than a directory:
# this is the file the item exists for.
HOOK_INSTALLER = "scripts/install_hooks.py"

# The one file `files` discovers but `exclude` filters back out.
EXCLUDED_FROM_DISCOVERY = "scripts/verify_env.py"

# The exact `files` line, used as a REPLACEMENT ANCHOR when a test generates a
# variant config. Anchoring on this line rather than slicing the file at the
# first "[[tool.mypy.overrides]]" is deliberate: that literal appears inside a
# comment above the real blocks, so slicing on it truncates mid-comment and
# silently changes what the generated config means.
FILES_KEY = 'files = ["clockspeed", "scripts", "tests"]'
FILES_KEY_WITH_TOOLS = 'files = ["clockspeed", "scripts", "tests", "tools"]'

# Frozen under CLAUDE.md section 6: an agent may not edit these without an
# adjudicator grant recorded in docs/LEDGER.md.
FROZEN_FILES = frozenset(
    {
        "scripts/install_hooks.py",
        "tools/precommit_gate.py",
    }
)

# Files that import the excluded module as a TOP-LEVEL module, which is the
# route by which `exclude` is defeated. Pinned in both directions by
# test_the_importers_of_the_excluded_module_are_recorded.
IMPORTERS_OF_EXCLUDED = ("tools/drift_guard.py", "tools/facts_probe.py")

# Zero-based index of the module-name column in mypy's --linecount-report
# output, which is four whitespace-separated counts followed by the module.
_LINECOUNT_MODULE_COLUMN = 4


class Gap(NamedTuple):
    """A file outside the gate, with the measured cost of bringing it in.

    Attributes:
        errors: Errors mypy reports for this file under the tools rung - the
            committed config with "tools" appended to `files`. That is the
            configuration the next step would actually use, so it is the only
            one whose counts are worth recording.
        reason: Why the gap is not closed. Prose, but every load-bearing claim
            in it is checked by a test in this file.
    """

    errors: int
    reason: str


# ---------------------------------------------------------------------------
# The gap record
# ---------------------------------------------------------------------------
#
# RECORDED, NOT ENDORSED. Every entry is a real hole in the type gate.

_TOOLS_REASON = (
    "tools/ is not in `files`. Bringing it in is blocked on nothing frozen: "
    "the only error in the frozen tools/precommit_gate.py is an import-untyped "
    "for the stub-less `ruff`, which a scoped ignore_missing_imports override "
    "removes with no edit to the file itself. What it is really blocked on is "
    "that tools/ files are not on this slice's write-list, and that adding "
    "tools/ to `files` resurrects every error in " + EXCLUDED_FROM_DISCOVERY + "."
)

_UNCOVERED: dict[str, Gap] = {
    EXCLUDED_FROM_DISCOVERY: Gap(
        errors=5,
        reason=(
            "Kept out of DISCOVERY by the `exclude` key so the rest of scripts/ "
            "could come inside the gate now. Codes arg-type and operator, all "
            "from one shape: an Optional[Path] proven non-None by a separate "
            "boolean flag instead of by a narrowing check. A code fix, not a "
            "gate-coverage fix. Note the exclusion is NOT containment - see the "
            "module docstring - so these 5 return the moment tools/ is added."
        ),
    ),
    "tools/doc_budget.py": Gap(errors=0, reason=_TOOLS_REASON),
    "tools/drift_guard.py": Gap(errors=1, reason=_TOOLS_REASON),
    "tools/edit_lint_check.py": Gap(errors=1, reason=_TOOLS_REASON),
    "tools/facts_probe.py": Gap(errors=1, reason=_TOOLS_REASON),
    "tools/memory_sync.py": Gap(errors=0, reason=_TOOLS_REASON),
    "tools/precommit_gate.py": Gap(errors=1, reason=_TOOLS_REASON),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_wide_mypy_sources() -> set[str]:
    """Resolve what a bare ``python -m mypy`` DISCOVERS.

    Calls mypy's own option processing with an empty argument list, which is
    what ``mypy`` with no arguments does. Nothing here re-implements mypy's
    file discovery, so the answer cannot disagree with the real invocation
    over a `files` entry, an `exclude` pattern or a namespace-package rule.

    This is the discovered set, NOT everything mypy reports on. See the module
    docstring.

    The chdir is load-bearing: mypy resolves both the config file and the
    relative paths inside `files` against the current directory, and pytest
    does not guarantee one.

    Returns:
        Repo-relative POSIX paths of every source the bare invocation
        discovers.
    """
    import mypy.main  # noqa: PLC0415

    with contextlib.chdir(REPO_ROOT):
        sources, _options = mypy.main.process_options(
            [], stdout=io.StringIO(), stderr=io.StringIO()
        )

    covered: set[str] = set()
    for source in sources:
        if source.path is None:
            continue
        covered.add(Path(source.path).resolve().relative_to(REPO_ROOT).as_posix())
    return covered


def _repo_wide_mypy_modules() -> set[str]:
    """Module names the bare invocation discovers, for the equivalence check.

    Returns:
        Dotted module names.
    """
    import mypy.main  # noqa: PLC0415

    with contextlib.chdir(REPO_ROOT):
        sources, _options = mypy.main.process_options(
            [], stdout=io.StringIO(), stderr=io.StringIO()
        )
    return {source.module for source in sources if source.module}


def _tracked_python_files(repo_files: list[Path]) -> list[str]:
    """Select the authored Python files from the repository inventory.

    Args:
        repo_files: Every file git tracks or would track, from conftest.

    Returns:
        Repo-relative POSIX paths, sorted.
    """
    return sorted(
        path.resolve().relative_to(REPO_ROOT).as_posix()
        for path in repo_files
        if path.suffix == ".py"
    )


def _top_level(relative_path: str) -> str:
    """Name the top-level directory a repo-relative path sits under.

    Args:
        relative_path: A repo-relative POSIX path.

    Returns:
        The first path component, or "." for a file at the repository root.
    """
    head, separator, _tail = relative_path.partition("/")
    return head if separator else "."


def _uncovered_within(directory: str, present: set[str], covered: set[str]) -> set[str]:
    """Files under ``directory`` that are neither covered nor a recorded gap.

    A PURE function of its three arguments, so a test can hand it a synthetic
    repository and pin the property that a newly added script must not turn
    the suite red. An earlier version of this file asserted set EQUALITY
    against a hardcoded one-file set, which forbade exactly the behaviour the
    directory was named to get.

    Args:
        directory: Top-level directory name.
        present: Repo-relative POSIX paths that exist.
        covered: Repo-relative POSIX paths mypy discovers.

    Returns:
        The unexplained subset, empty when the directory is properly covered.
    """
    return {
        path
        for path in present
        if _top_level(path) == directory and path not in covered and path not in _UNCOVERED
    }


def _run_mypy(*args: str, config: Path | None = None, cache: Path | None = None) -> str:
    """Run mypy from the repository root and return its stdout.

    ``sys.executable`` rather than a literal interpreter name: an absolute or
    guessed interpreter path in a tracked file hardcodes a machine layout
    (CONVENTIONS.md section 10), and on this machine several interpreters
    report the same version while only one carries the toolchain.

    Args:
        *args: Trailing mypy arguments, usually target paths.
        config: Optional config file to use instead of pyproject.toml.
        cache: Optional cache directory, so a generated config never writes
            into the repository's own incremental cache.

    Returns:
        Combined stdout. A non-zero exit is not raised: these tests assert on
        COVERAGE, and mypy reports its summary on the error path too.
    """
    command = [sys.executable, "-m", "mypy", "--no-pretty"]
    if config is not None:
        command += ["--config-file", str(config)]
    if cache is not None:
        command += ["--cache-dir", str(cache)]
    command += list(args)
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    return proc.stdout


def _errors_by_file(output: str) -> dict[str, int]:
    """Count mypy errors per file from its output.

    Args:
        output: mypy stdout.

    Returns:
        Repo-relative POSIX path to error count. Files with no errors are
        absent rather than zero.
    """
    counts: dict[str, int] = {}
    for line in output.splitlines():
        match = re.match(r"^(.+?):\d+: error:", line)
        if match is None:
            continue
        path = match.group(1).replace("\\", "/")
        counts[path] = counts.get(path, 0) + 1
    return counts


def _reported_file_count(output: str) -> int:
    """Read the source-file count out of mypy's summary line.

    Handles both summary forms, because coverage is the subject here and the
    count is printed whether the run passed or failed:
    "Success: no issues found in 63 source files" and
    "Found 9 errors in 5 files (checked 71 source files)".

    Args:
        output: mypy stdout.

    Returns:
        The number of source files mypy reported discovering.

    Raises:
        AssertionError: The summary line was absent or unrecognised.
    """
    match = re.search(r"(?:no issues found in|checked) (\d+) source files?", output)
    assert match is not None, f"could not find mypy's summary line in:\n{output}"
    return int(match.group(1))


def _config_with_tools(tmp_path: Path) -> Path:
    """Write a variant config identical to the real one but with tools/ added.

    This is the configuration the next rung would actually use, so it is the
    only one whose error counts are worth recording.

    Args:
        tmp_path: Directory to write the generated config into.

    Returns:
        Path to the generated config.

    Raises:
        AssertionError: The replacement anchor was not found, which would make
            the generated config silently identical to the real one. A
            mutation that fails to apply looks GREEN (CONVENTIONS.md section
            7.2), so this is checked rather than assumed.
    """
    source = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert FILES_KEY in source, (
        f"the `files` anchor {FILES_KEY!r} is no longer in pyproject.toml, so "
        "this test would silently measure the unmodified config"
    )
    generated = source.replace(FILES_KEY, FILES_KEY_WITH_TOOLS)
    assert generated != source, "the files-key mutation did not apply"
    target = tmp_path / "pyproject_with_tools.toml"
    target.write_text(generated, encoding="utf-8")
    return target


def _comment_block_above(text: str, needle: str) -> str:
    """Extract the contiguous comment lines immediately above a config line.

    Args:
        text: Full file text.
        needle: A line prefix to find.

    Returns:
        The comment block, joined with newlines, or "" if there is none.
    """
    lines = text.splitlines()
    index = next((n for n, line in enumerate(lines) if line.startswith(needle)), None)
    if index is None:
        return ""
    block: list[str] = []
    for line in reversed(lines[:index]):
        if line.lstrip().startswith("#"):
            block.append(line)
        else:
            break
    return "\n".join(reversed(block))


@pytest.fixture(scope="session")
def tools_rung_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Type-checker output under the tools rung, run once and shared.

    A full run costs about six seconds cold, and several tests need it.

    Args:
        tmp_path_factory: pytest's session-scoped temp directory factory.

    Returns:
        mypy stdout for the generated tools-included config.
    """
    tmp_path = tmp_path_factory.mktemp("tools_rung")
    config = _config_with_tools(tmp_path)
    return _run_mypy(config=config, cache=tmp_path / "cache")


# ---------------------------------------------------------------------------
# The acceptance criterion
# ---------------------------------------------------------------------------


def test_repo_wide_mypy_checks_the_hook_installer() -> None:
    covered = _repo_wide_mypy_sources()
    assert HOOK_INSTALLER in covered, (
        f"{HOOK_INSTALLER} is outside the bare `python -m mypy` invocation, so "
        "the gate CI runs never looks at it. A green gate says nothing about "
        "this file while that is true. Add it to the mypy `files` key in "
        "pyproject.toml."
    )


def test_the_scripts_directory_is_covered_as_a_directory(repo_files: list[Path]) -> None:
    # The property is "nothing under scripts/ is unexplained", NOT "the covered
    # set equals one hardcoded path". Equality would forbid the very thing
    # naming the directory buys, and its failure message would tell the next
    # reader to narrow `files` back down - reopening CS-411 to fix a red.
    present = set(_tracked_python_files(repo_files))
    unexplained = _uncovered_within("scripts", present, _repo_wide_mypy_sources())
    assert not unexplained, (
        f"these files under scripts/ are neither discovered by the bare mypy "
        f"invocation nor recorded as known gaps: {sorted(unexplained)}"
    )


def test_a_newly_added_script_would_not_turn_this_suite_red() -> None:
    # The regression test for the assertion this file used to make. A clean new
    # script is covered automatically because `files` names the directory, so
    # the correct outcome is silence. Synthetic sets rather than a real file:
    # scripts/ is shared with concurrent work and a test must not write there.
    present = {HOOK_INSTALLER, EXCLUDED_FROM_DISCOVERY, "scripts/new_tool.py"}
    covered = {HOOK_INSTALLER, "scripts/new_tool.py"}
    assert _uncovered_within("scripts", present, covered) == set()


# ---------------------------------------------------------------------------
# The oracle stands for the real invocation
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_the_oracle_reproduces_the_real_runs_discovered_set(tmp_path: Path) -> None:
    # SETS, not counts. mypy's success line prints len(sources) - the same
    # quantity the oracle counts - so comparing counts is very nearly a
    # tautology and would not notice one file being swapped for another.
    # --linecount-report is a documented flag that names every module in the
    # run's source set, unlike the cache, whose layout is internal.
    report_dir = tmp_path / "report"
    _run_mypy("--linecount-report", str(report_dir))
    lines = (report_dir / "linecount.txt").read_text(encoding="utf-8").splitlines()
    # Four count columns then the module name; the first row is the "total".
    real = {
        line.split()[_LINECOUNT_MODULE_COLUMN]
        for line in lines[1:]
        if len(line.split()) > _LINECOUNT_MODULE_COLUMN
    }
    assert real == _repo_wide_mypy_modules(), (
        "mypy's own option processing and a real bare run disagree about which "
        "modules the invocation discovers, so the fast oracle in this file no "
        "longer stands for the real thing."
    )


# ---------------------------------------------------------------------------
# exclude is a discovery filter, not containment
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_the_exclusion_is_discovery_only_not_containment(tools_rung_output: str) -> None:
    # The claim the config comment makes, executed. `exclude` keeps mypy from
    # WALKING to a file; it does not stop a checked file from IMPORTING it.
    # CS-411 created the resolution path itself: adding scripts/ to `files`
    # made scripts/ a source base dir, so `verify_env` became importable as a
    # top-level module for the first time.
    resurrected = _errors_by_file(tools_rung_output).get(EXCLUDED_FROM_DISCOVERY, 0)
    assert resurrected == _UNCOVERED[EXCLUDED_FROM_DISCOVERY].errors, (
        f"under the tools rung, {EXCLUDED_FROM_DISCOVERY} reports "
        f"{resurrected} errors despite being excluded. The recorded count is "
        f"{_UNCOVERED[EXCLUDED_FROM_DISCOVERY].errors}. Either the exclusion "
        "started working as containment, or the file changed.\n"
        f"{tools_rung_output}"
    )


def test_the_importers_of_the_excluded_module_are_recorded(repo_files: list[Path]) -> None:
    # Both directions, so the record cannot rot: every recorded importer really
    # imports it, and no unrecorded file does. A new importer appearing is the
    # sibling case of the defect above and must not arrive unnoticed.
    module = Path(EXCLUDED_FROM_DISCOVERY).stem
    pattern = re.compile(rf"^\s*import\s+{module}\b", re.MULTILINE)
    found = {
        path
        for path in _tracked_python_files(repo_files)
        if path != EXCLUDED_FROM_DISCOVERY
        and pattern.search((REPO_ROOT / path).read_text(encoding="utf-8"))
    }
    assert found == set(IMPORTERS_OF_EXCLUDED), (
        f"the set of files importing `{module}` as a top-level module has "
        f"changed: recorded {sorted(IMPORTERS_OF_EXCLUDED)}, found "
        f"{sorted(found)}. Every one of these defeats the `exclude` key the "
        "moment its directory enters `files`."
    )


# ---------------------------------------------------------------------------
# The gap record, asserted in both directions and against a real run
# ---------------------------------------------------------------------------


def test_every_authored_python_file_is_covered_or_recorded(repo_files: list[Path]) -> None:
    covered = _repo_wide_mypy_sources()
    unexplained = [
        path
        for path in _tracked_python_files(repo_files)
        if path not in covered and path not in _UNCOVERED
    ]
    assert not unexplained, (
        "these authored Python files are outside the bare `python -m mypy` "
        "invocation and are not recorded as known gaps, so the type gate is "
        f"silently ignoring them: {unexplained}. Either add them to the mypy "
        "`files` key in pyproject.toml, or record them in _UNCOVERED with the "
        "reason they cannot be covered yet."
    )


def test_the_recorded_gaps_are_still_gaps() -> None:
    # File granularity, deliberately. A directory-level record asserting only
    # "something under here is still uncovered" stays green while all but one
    # of its files get covered, which is a record that has stopped describing
    # reality without ever saying so.
    covered = _repo_wide_mypy_sources()
    for path, gap in _UNCOVERED.items():
        assert (REPO_ROOT / path).is_file(), f"_UNCOVERED names a missing file: {path}"
        assert gap.reason.strip(), f"_UNCOVERED entry {path} states no reason"
        assert path not in covered, (
            f"{path} is now discovered by the bare mypy invocation, so its "
            "entry in _UNCOVERED is stale. Delete the entry, and delete any "
            "matching exclusion from pyproject.toml."
        )


@pytest.mark.slow
def test_the_recorded_error_counts_are_still_accurate(tools_rung_output: str) -> None:
    # THE ORACLE THE RECORD USED TO LACK. Without this, an entry's reason is
    # whatever the last author believed, and a wrong belief survives forever
    # because nothing reads it. Measured under the tools rung, which is the
    # configuration the next step would actually use.
    observed = _errors_by_file(tools_rung_output)
    recorded = {path: gap.errors for path, gap in _UNCOVERED.items()}
    actual = {path: observed.get(path, 0) for path in recorded}
    assert actual == recorded, (
        "the recorded per-file error counts no longer match a real run under "
        f"the tools rung. recorded={recorded} actual={actual}. Update "
        "_UNCOVERED, and update any roadmap item quoting these numbers.\n"
        f"{tools_rung_output}"
    )


@pytest.mark.slow
def test_no_recorded_gap_is_blocked_by_a_frozen_file(tmp_path: Path) -> None:
    # The correction to a reason this file previously stated as fact. It
    # claimed tools/ could not enter the gate without an adjudicator grant,
    # because tools/precommit_gate.py is frozen. That was false: the frozen
    # file's only error is an import-untyped for the stub-less `ruff`, and a
    # scoped override removes it with no edit to the file at all.
    frozen_with_errors = sorted(
        path for path in _UNCOVERED if path in FROZEN_FILES and _UNCOVERED[path].errors
    )
    assert frozen_with_errors == ["tools/precommit_gate.py"], (
        f"the set of frozen files carrying errors has changed: {frozen_with_errors}"
    )

    source = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    override = '\n[[tool.mypy.overrides]]\nmodule = ["ruff"]\nignore_missing_imports = true\n'
    config = tmp_path / "with_override.toml"
    config.write_text(source + override, encoding="utf-8")

    before = _run_mypy("tools/precommit_gate.py", cache=tmp_path / "cache_a")
    after = _run_mypy("tools/precommit_gate.py", config=config, cache=tmp_path / "cache_b")
    assert "import-untyped" in before, (
        "tools/precommit_gate.py no longer reports the import-untyped error "
        f"this test is about:\n{before}"
    )
    assert _errors_by_file(after) == {}, (
        "a scoped ignore_missing_imports override no longer clears the frozen "
        "file, so the recorded reason for the tools/ gap needs rechecking.\n"
        f"{after}"
    )


# ---------------------------------------------------------------------------
# The exclusion is deliberate, and says so where the exclusion lives
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_the_config_comment_names_a_reason_that_is_still_true() -> None:
    # CS-411's second acceptance branch is "carries a comment naming the
    # reason". Substring presence of the path is NOT that test: replacing the
    # whole comment with a bare "# scripts/verify_env.py" satisfied it. So the
    # comment has to carry claims that a real run can falsify - the error
    # codes, the count, and the importers that defeat the exclusion.
    config = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = _comment_block_above(config, "exclude =")
    assert EXCLUDED_FROM_DISCOVERY in block, (
        "the comment above the `exclude` key never names the excluded file, so "
        "the exclusion is indistinguishable from an oversight"
    )

    output = _run_mypy(EXCLUDED_FROM_DISCOVERY)
    codes = set(re.findall(r"\[([a-z-]+)\]", output))
    assert codes, f"no error codes parsed from:\n{output}"
    missing = sorted(code for code in codes if code not in block)
    assert not missing, (
        f"the comment does not name these error codes mypy actually reports "
        f"for {EXCLUDED_FROM_DISCOVERY}: {missing}. A reason that does not "
        "match the errors is not a reason."
    )

    count = sum(_errors_by_file(output).values())
    assert str(count) in block, (
        f"the comment does not state the error count ({count}), so it cannot "
        "go stale visibly when the count changes"
    )
    for importer in IMPORTERS_OF_EXCLUDED:
        assert importer in block, (
            f"the comment does not name {importer}, which imports the excluded "
            "module and therefore defeats this exclusion once tools/ is added. "
            "A reader changing `files` needs that at the config."
        )


@pytest.mark.slow
def test_the_exclusion_retires_itself_once_the_file_is_clean() -> None:
    # A per-path mypy run is the WRONG tool for "is the gate green" and the
    # right one for "is this one file clean yet", which is the question here.
    # The day it is, this test fails and says to delete the exclusion, so the
    # hole cannot outlive its reason.
    output = _run_mypy(EXCLUDED_FROM_DISCOVERY)
    # Via the shared parser, which reads BOTH summary forms. Matching the
    # error-path wording alone would misreport the clean case - the very case
    # this test exists to catch - as "mypy never ran".
    assert _reported_file_count(output) == 1, (
        f"mypy did not actually check {EXCLUDED_FROM_DISCOVERY}, so this test "
        f"proves nothing about whether the exclusion is still justified.\n{output}"
    )
    found = re.search(r"Found (\d+) error", output)
    assert found is not None, (
        f"{EXCLUDED_FROM_DISCOVERY} now type-checks clean on its own, so the "
        "reason it is excluded no longer holds. Remove the `exclude` entry "
        f"from pyproject.toml and the _UNCOVERED entry from this file.\n{output}"
    )
    assert int(found.group(1)) > 0, (
        f"mypy reported zero errors in {EXCLUDED_FROM_DISCOVERY}, so its "
        "exclusion is no longer justified."
    )
