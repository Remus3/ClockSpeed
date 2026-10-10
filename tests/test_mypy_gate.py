#!/usr/bin/env python3
"""Tests for WHAT the repo-wide mypy invocation covers - not only whether it passes.

THE DEFECT THIS FILE PINS. CI's type gate is `python -m mypy` invoked bare,
with no target (.github/workflows/tier1.yml), so pyproject.toml's mypy `files`
key is the sole authority on what gets checked. That key once named only the
package and the suite, which left every file under scripts/ and tools/ outside
the gate entirely - including scripts/install_hooks.py, the first thing a fresh
clone executes, and tools/precommit_gate.py, the tier-0 blocking gate that
installer wires up. Those are the two files whose failure leaves a clone
unprotected while reporting itself protected.

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
counts, and what --linecount-report lists) and a REPORTED-ON set (every module
it actually builds, which includes anything a discovered file imports).
`exclude` filters DISCOVERY ONLY. A file kept out of discovery is still built,
and still has its errors printed, the moment any checked file imports it.
Measured rather than assumed - see ``test_exclude_filters_discovery_and_does_
not_contain_errors``, which demonstrates it on a throwaway project so the proof
cannot rot when this repository's own files change.

So the oracle below reports COVERAGE BY DISCOVERY and structurally cannot see
an import-pulled file. Every test here that depends on the reported-on set uses
mypy's actual error output instead, never the oracle.

THE ORACLE. ``mypy.main.process_options([])`` is precisely what the mypy CLI
calls with an empty argument list - not a re-implementation of mypy's path
resolution, and not a per-path run standing in for a repo-wide one. It applies
`files`, `exclude` and the namespace rules exactly as the real run does, without
paying for a type check.

WHICH CONFIG FILE IS ALSO ASKED, NOT ASSUMED. The same call reports the config
mypy selected, and every config assertion here goes through it. mypy prefers
``mypy.ini`` and ``.mypy.ini`` over ``pyproject.toml``, so a single file dropped
beside pyproject.toml demotes the ``[tool.mypy]`` table to decoration - and four
tests that read pyproject.toml directly would have gone on describing it. That
was a hole in the CONFIG assertions only: the coverage assertions ask mypy and
would have followed the move.

THE GAP RECORD RETIRES ITSELF, AND IT HAS TWO ORACLES. An earlier version of
this file recorded each gap as free prose that no test read, so a reason could
be - and was - simply false. Every entry in ``_UNCOVERED`` now owes both a
measured error count and a reason naming the error codes that run reports:
``test_the_recorded_error_counts_are_still_accurate`` and
``test_a_recorded_reason_names_the_error_codes_a_real_run_reports``. A gap that
is fixed, worsened or misdescribed turns this file red rather than sitting there
being believed.

MEASURED BY A RUN THAT DISCOVERS THE GAP, which the bare invocation structurally
cannot be. A gap is a file outside `files`; mypy reports nothing for a file it
never discovers; so an oracle reading the bare run answers 0 for every genuine
gap and can only be satisfied by a record that writes ``errors=0`` - the one
value carrying no information. ``_measure_gaps`` names the gate's own targets
AND each gap, so the number means what ``Gap.errors`` says it does.

THE RECORD IS EMPTY as of CS-415: all four authored directories are inside the
gate and the bare run is clean. The machinery is kept, dormant and skipping
visibly, because the next gap should arrive with an oracle already attached
rather than as fresh prose. A skip conceals whether the thing skipping is
correct, and this file has already shipped one dormant oracle that could not
have passed, so both oracles are additionally driven against a throwaway project
that really does contain a gap - with a true record and with a false one.
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import io
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The acceptance criterion of CS-411, named as a path rather than a directory:
# this is the file that item exists for.
HOOK_INSTALLER = "scripts/install_hooks.py"

# The file CS-414 fixed and un-excluded. Two tools import it as a TOP-LEVEL
# module, which is the route by which an `exclude` key on it was always inert.
ENV_VERIFIER = "scripts/verify_env.py"
IMPORTERS_OF_THE_ENV_VERIFIER = ("tools/drift_guard.py", "tools/facts_probe.py")

# CLAUDE.md section 6 OWNS the frozen list, so it is read from there rather than
# restated here. The restatement drifted exactly as CLAUDE.md section 4 says a
# restated fact does: a hardcoded pair held 2 of that section's 5 entries under
# a test name claiming every frozen file. The other three are shell, JSON and a
# licence text - not Python, so not checkable by a type gate - and the filter
# that drops them is now visible instead of being baked into a literal.
_FROZEN_SECTION_HEADING = "## 6. Frozen files"

# The third-party modules that ship no type information, named in a SCOPED
# overrides block rather than by loosening the global ignore_missing_imports.
STUBLESS_MODULES = ["ruff", "yaml"]

# A module name that cannot resolve, used as the negative control that proves
# mypy really does report a non-matching overrides block.
UNMATCHABLE_MODULE = "clockspeed_no_such_module_exists"

# Zero-based index of the module-name column in mypy's --linecount-report
# output, which is four whitespace-separated counts followed by the module.
_LINECOUNT_MODULE_COLUMN = 4

# The exclusion arm's throwaway-project pattern, and a mutant of it that matches
# nothing - the control that proves the arm still sees discovery stop filtering.
_LEAF_EXCLUDE = r"(^|/)leaf\.py$"
_NON_MATCHING_EXCLUDE = r"(^|/)no_such_leaf\.py$"
# Source files that project's discovery finds when the exclude filters nothing.
_UNFILTERED_SOURCE_COUNT = 2

# The bound on every mypy subprocess here, named once so the runs this module
# makes outside ``_run_mypy`` cannot drift from it. Generous on purpose: a
# cold cache on a loaded runner is slow, and a bound tight enough to trip on
# that would report a flake as a finding. It is a RUNAWAY cutoff, not a
# budget - tier 1 owns the budget, and it is minutes below this.
_MYPY_TIMEOUT_SECONDS = 900

# Hazards planted in the pytest process to prove the exclusion arm does not
# report on its ambient environment (CS-1125): (id, variables, value tokens).
# Every one but the absolute repository root breaks the arm when mypy inherits
# it, and each hazard is COMPLETE on both Windows and POSIX - it names every
# variable its mechanism needs, so it is not live on one platform only:
#   PYTHONPATH: mypy builds its search path from its child interpreter's
#     sys.path on every platform. "." is the literal `PYTHONPATH=.` and resolves
#     against mypy's working directory, the throwaway project, not the repo root.
#   FORCE_COLOR plus TERM: FORCE_COLOR only bypasses mypy's isatty check. On
#     Windows it then emits VT100 escapes unconditionally; on POSIX it calls
#     curses.setupterm(), which fails with no TERM - measured on ubuntu CI,
#     where the run then stayed plain. `xterm` is in ncurses-base and carries
#     every capability mypy asks for (bold, smul, setaf, cup, sgr0).
#   PYTHONIOENCODING=utf-16: the child's stdout encoding on every platform.
_AMBIENT_PLANTS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("pythonpath_dot", (("PYTHONPATH", "."),)),
    ("pythonpath_repo_root", (("PYTHONPATH", "<repo_root>"),)),
    ("pythonpath_project_root", (("PYTHONPATH", "<project_root>"),)),
    ("pythonpath_source_root", (("PYTHONPATH", "<source_root>"),)),
    ("force_color", (("FORCE_COLOR", "1"), ("TERM", "xterm"))),
    ("pythonioencoding_utf16", (("PYTHONIOENCODING", "utf-16"),)),
)
_HARMLESS_PLANTS = frozenset({"pythonpath_repo_root"})
_AMBIENT_PARAMS = [pytest.param(dict(plant), id=name) for name, plant in _AMBIENT_PLANTS]
_LIVE_AMBIENT_PARAMS = [
    pytest.param(dict(plant), id=name)
    for name, plant in _AMBIENT_PLANTS
    if name not in _HARMLESS_PLANTS
]


class Gap(NamedTuple):
    """A file outside the gate, with the measured cost of bringing it in.

    Attributes:
        errors: Errors mypy reports for this file under the committed config
            when the file is DISCOVERED - the gate's own targets plus this one.
            Not what the bare invocation reports, which is 0 for every gap by
            construction and is therefore no measurement at all.
        reason: Why the gap is not closed. Prose, but it owes the count above
            and the name of every error code the measuring run reports, and
            ``_unsupported_reason_claims`` collects whatever it does not pay.
    """

    errors: int
    reason: str


# ---------------------------------------------------------------------------
# The gap record
# ---------------------------------------------------------------------------
#
# RECORDED, NOT ENDORSED. Every entry is a real hole in the type gate.
#
# EMPTY AS OF CS-415, and that is a measured state rather than an abandoned
# structure. CS-414 fixed scripts/verify_env.py's 5 narrowing errors and deleted
# the `exclude` key that had been holding them out of sight; CS-415 added tools/
# to `files` and fixed the two errors that surfaced. The tests below that read
# this record skip loudly while it is empty, so a dormant gate is visible in the
# summary instead of passing vacuously.

_UNCOVERED: dict[str, Gap] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _discovered_config_file(root: Path = REPO_ROOT) -> Path:
    """Ask mypy which config file a bare run in ``root`` would actually read.

    Derived from mypy's own option processing rather than re-implemented, for
    exactly the reason ``_repo_wide_mypy_sources`` is: a search order written
    out here can disagree with the real invocation, and an assertion about a
    config mypy is not reading is an assertion about nothing.

    It has to be derived because mypy PREFERS ``mypy.ini`` and ``.mypy.ini``
    over ``pyproject.toml`` - ``mypy.defaults.CONFIG_NAMES`` is consulted before
    ``SHARED_CONFIG_NAMES`` - so one file dropped beside pyproject.toml takes
    the entire configuration away from it silently. Measured rather than
    assumed: see ``test_a_competing_mypy_ini_takes_the_config_away_from_pyproject``.

    Args:
        root: Directory the bare invocation would run in.

    Returns:
        Absolute path to the config file mypy selected.
    """
    import mypy.main  # noqa: PLC0415

    with contextlib.chdir(root):
        _sources, options = mypy.main.process_options(
            [], stdout=io.StringIO(), stderr=io.StringIO()
        )
    assert options.config_file is not None, (
        f"mypy selected no configuration file in {root}, so the bare invocation "
        "runs on defaults and nothing asserted about a config file describes it."
    )
    return (root / options.config_file).resolve()


def _mypy_config(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Parse the mypy configuration the real invocation reads.

    Parsed rather than string-matched: an assertion against a literal config
    line turns red when someone reflows the list, which trains readers to
    "fix" the test. The parsed value is what mypy itself acts on.

    The file is CONFIRMED to be the one mypy selects before it is parsed, not
    assumed to be pyproject.toml. Every config assertion in this module goes
    through here, so a competing ``mypy.ini`` cannot leave four tests reading a
    table that governs nothing.

    Args:
        root: Directory the bare invocation would run in.

    Returns:
        The [tool.mypy] table.
    """
    expected = (root / "pyproject.toml").resolve()
    selected = _discovered_config_file(root)
    assert selected == expected, (
        f"mypy reads its configuration from {selected}, not from {expected}. "
        "mypy.ini and .mypy.ini both outrank pyproject.toml, so the [tool.mypy] "
        "table every config assertion in this file reads is governing nothing. "
        "Delete the competing file, or move the configuration into it."
    )
    parsed = tomllib.loads(expected.read_text(encoding="utf-8"))
    config: dict[str, Any] = parsed["tool"]["mypy"]
    return config


def _frozen_entries() -> list[str]:
    """Read the frozen-file list out of CLAUDE.md section 6.

    Returns:
        Every backtick-quoted bullet in that section, in document order.
    """
    lines = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == _FROZEN_SECTION_HEADING),
        None,
    )
    assert start is not None, (
        f"CLAUDE.md has no {_FROZEN_SECTION_HEADING!r} heading, so the frozen "
        "list cannot be read from the file that owns it."
    )
    entries: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        match = re.match(r"^- `([^`]+)`\s*$", line)
        if match is not None:
            entries.append(match.group(1))
    return entries


def _frozen_python_files() -> frozenset[str]:
    """The frozen entries a type gate can actually check.

    Glob entries are dropped rather than expanded: the checkable claim is about
    named files, and a pattern that matches no Python file would quietly widen
    the set to nothing.

    Returns:
        Repo-relative POSIX paths of the frozen Python files.
    """
    return frozenset(
        entry for entry in _frozen_entries() if entry.endswith(".py") and "*" not in entry
    )


def _module_patterns(block: Mapping[str, Any]) -> list[str]:
    """The module patterns an overrides block names, order-insensitively.

    Sorted because TOML array order carries no meaning to mypy. Comparing the
    raw list made a reflow of ["ruff", "yaml"] to ["yaml", "ruff"] turn a test
    red over a change with no behaviour in it, which is how a reader learns to
    edit the assertion rather than read it.

    Args:
        block: One [[tool.mypy.overrides]] table.

    Returns:
        The patterns, sorted. A bare string is treated as a one-element list.
    """
    module = block.get("module", [])
    return [module] if isinstance(module, str) else sorted(module)


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


def _uncovered_within(
    directory: str, present: set[str], covered: set[str], recorded: dict[str, Gap]
) -> set[str]:
    """Files under ``directory`` that are neither covered nor a recorded gap.

    A PURE function of its four arguments, so a test can hand it a synthetic
    repository and pin the property that a newly added script must not turn
    the suite red. An earlier version of this file asserted set EQUALITY
    against a hardcoded one-file set, which forbade exactly the behaviour the
    directory was named to get.

    ``recorded`` is a parameter rather than a read of the module global for the
    same reason: with the real record now empty, a test that wants to prove a
    recorded gap is tolerated has to be able to supply one.

    Args:
        directory: Top-level directory name.
        present: Repo-relative POSIX paths that exist.
        covered: Repo-relative POSIX paths mypy discovers.
        recorded: The gap record to consult.

    Returns:
        The unexplained subset, empty when the directory is properly covered.
    """
    return {
        path
        for path in present
        if _top_level(path) == directory and path not in covered and path not in recorded
    }


# WHAT A MYPY SUBPROCESS HERE IS CONTROLLED BY (CS-1125). Three mechanisms, and
# each closes a leak that was measured, not imagined:
#
# 1. AN ALLOWLIST of inherited variables. The denylist it replaced dropped
#    PYTHONPATH and MYPY* and still passed FORCE_COLOR, which mypy reads as the
#    fallback for MYPY_FORCE_COLOR, and PYTHONIOENCODING, which re-encodes every
#    byte mypy prints. What mypy and its interpreter read is open-ended - mypy
#    starts a child interpreter over os.environ and expands $VARIABLES inside
#    config values - so no denylist can be shown complete, and a missing
#    allowlist entry fails LOUD (mypy cannot start) where a denylist leak fails
#    as an empty parse.
# 2. PINS laid over it (``_PINNED_ENVIRONMENT``). PYTHONNOUSERSITE=1, because
#    a .pth file in the per-user site directory runs at interpreter start and
#    put a throwaway project on the search path mypy builds from its child
#    interpreter's sys.path. Pinned in the ENVIRONMENT rather than passed as
#    `python -s`, because every interpreter mypy itself starts inherits the
#    environment and none inherits the flag. A per-user-installed mypy therefore
#    cannot import here - every arm reddens, which is the loud failure intended.
#    PYTHONIOENCODING=utf-8, because the output is decoded as UTF-8 here.
# 3. AN EXPLICIT CONFIG on every run (``_run_mypy`` has no default for it).
#    With no config beside the project, mypy falls back to ~/.mypy.ini or
#    ~/.config/mypy/config, located through home variables kept below.
#
# DELIBERATELY KEPT, AND WHY - the interpreter needs these to start or to
# resolve its own paths, and each reader that could turn one into a leak is shut
# by mechanism 2 or 3 above:
#   Windows: SYSTEMROOT (CPython's random seeding and sockets), WINDIR,
#     SYSTEMDRIVE, COMSPEC, PATHEXT.
#   Both: PATH; TEMP and TMP for temporary files.
#   Home, for `~` expansion (mypy expands it in cache and config paths, and on
#     Windows an unset USERPROFILE leaves `~` literal): HOME, USERPROFILE,
#     HOMEDRIVE, HOMEPATH. Their other readers - the per-user site and the
#     per-user config - are mechanisms 2 and 3.
#   POSIX: TMPDIR, LANG, LC_ALL, LC_CTYPE, and LD_LIBRARY_PATH for a
#     shared-library interpreter build.
# NOT kept: APPDATA and LOCALAPPDATA, whose only reader on this path was the
# per-user site directory.
_INHERITED_FOR_STARTUP: frozenset[str] = frozenset(
    {
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LD_LIBRARY_PATH",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USERPROFILE",
        "WINDIR",
    }
)

_PINNED_ENVIRONMENT: dict[str, str] = {"PYTHONIOENCODING": "utf-8", "PYTHONNOUSERSITE": "1"}


def _controlled_environment(ambient: Mapping[str, str] | None = None) -> dict[str, str]:
    """The environment a mypy subprocess here runs under - controlled, not inherited.

    CS-1125. A run that inherits whatever launched pytest reports on that
    launcher rather than on the project it was pointed at: under
    ``PYTHONPATH=.`` a throwaway project landed on mypy's search path and mypy
    printed Success over a real error; under ``FORCE_COLOR=1`` every line
    carried ANSI escapes no parser here matches. So nothing is inherited except
    ``_INHERITED_FOR_STARTUP``, and ``_PINNED_ENVIRONMENT`` is laid over it. The
    comment above that set says what each kept variable is for.

    Matched CASE-INSENSITIVELY: on Windows ``dict(os.environ)`` upper-cases its
    keys, but a mapping built any other way need not. A kept variable keeps
    its own spelling.

    Args:
        ambient: The environment to draw from, defaulting to this process's own.

    Returns:
        A fresh mapping, safe to hand to ``subprocess.run``.
    """
    source = os.environ if ambient is None else ambient
    kept = {name: value for name, value in source.items() if name.upper() in _INHERITED_FOR_STARTUP}
    return {**kept, **_PINNED_ENVIRONMENT}


def _run_mypy(
    *args: str,
    config: Path,
    cache: Path | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run mypy and return the completed process.

    ``sys.executable`` rather than a literal interpreter name: an absolute or
    guessed interpreter path in a tracked file hardcodes a machine layout
    (CONVENTIONS.md section 10), and on this machine several interpreters
    report the same version while only one carries the toolchain.

    Args:
        *args: Trailing mypy arguments, usually target paths.
        config: The config file mypy reads. REQUIRED, with no default: a run
            left to discover one falls back to a per-user config whenever no
            project config sits beside it (CS-1125).
        cache: Optional cache directory, so a generated config never writes
            into the repository's own incremental cache.
        cwd: Optional working directory, defaulting to the repository root.
        env: Optional explicit environment. Omitted, the run gets
            ``_controlled_environment()``; only the arm proving that a planted
            variable is hazardous passes one.

    Returns:
        The completed process. A non-zero exit is not raised: most tests here
        assert on COVERAGE, and mypy reports its summary on the error path too.

    Raises:
        UnicodeDecodeError: mypy wrote a stream that is not UTF-8.
    """
    command = [sys.executable, "-m", "mypy", "--no-pretty", "--config-file", str(config)]
    if cache is not None:
        command += ["--cache-dir", str(cache)]
    command += list(args)
    # Captured as BYTES and decoded here. With text=True the decode runs in a
    # reader thread on Windows, and a stream that is not valid text leaves
    # stdout as None instead of raising where a test can see why.
    completed = subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        env=_controlled_environment() if env is None else dict(env),
        capture_output=True,
        timeout=_MYPY_TIMEOUT_SECONDS,
        check=False,
    )
    return subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        completed.stdout.decode("utf-8"),
        completed.stderr.decode("utf-8"),
    )


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


def _error_codes_by_file(output: str) -> dict[str, frozenset[str]]:
    """Collect the mypy error CODES reported per file.

    The code is the falsifiable part of an error. A count alone cannot tell a
    narrowing bug that got fixed from an unrelated assignment bug that replaced
    it, and a recorded reason describing the first would stay green over the
    second.

    Args:
        output: mypy stdout, from a run with error codes shown.

    Returns:
        Repo-relative POSIX path to the set of codes seen for it. Files with no
        errors are absent rather than empty.
    """
    codes: dict[str, set[str]] = {}
    for line in output.splitlines():
        located = re.match(r"^(.+?):\d+: error:", line)
        tagged = re.search(r"\[([a-z][a-z0-9-]*)\]$", line)
        if located is None or tagged is None:
            continue
        codes.setdefault(located.group(1).replace("\\", "/"), set()).add(tagged.group(1))
    return {path: frozenset(seen) for path, seen in codes.items()}


def _measure_gaps(
    gaps: Sequence[str], *, root: Path = REPO_ROOT, cache: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run mypy over the gate's own targets PLUS the recorded gap files.

    THE BARE INVOCATION CANNOT MEASURE A GAP. A gap is a file outside `files`;
    mypy reports nothing for a file it never discovers; so the bare run answers
    0 for every genuine gap no matter what that file contains. Naming each gap
    as an explicit target is what puts it in the discovered set, which is what
    ``Gap.errors`` means by "the measured cost of bringing it in".

    The gate's own `files` entries are passed alongside rather than dropped, so
    the gap is measured in the same import graph the real run builds - an error
    that only appears because a checked module imports the gap is part of that
    cost too.

    Args:
        gaps: Paths relative to ``root`` that the gate does not discover.
        root: Directory the gate's config lives in.
        cache: Optional cache directory.

    Returns:
        The completed process.
    """
    targets = [str(entry) for entry in _mypy_config(root)["files"]]
    return _run_mypy(*targets, *gaps, config=root / "pyproject.toml", cache=cache, cwd=root)


def _gap_count_mismatches(
    recorded: Mapping[str, Gap], measured: Mapping[str, int]
) -> dict[str, tuple[int, int]]:
    """Recorded gap counts a measuring run does not bear out.

    Pure, so the comparison can be driven with a synthetic record against a
    synthetic measurement. With the real record empty that is the only way the
    machinery gets exercised at all, and dormant-and-unexercised is how it came
    to be dormant-and-wrong.

    Args:
        recorded: The gap record.
        measured: Errors per path from a run that DISCOVERS each path.

    Returns:
        Path to (recorded, measured) for every disagreement.
    """
    return {
        path: (gap.errors, measured.get(path, 0))
        for path, gap in recorded.items()
        if gap.errors != measured.get(path, 0)
    }


def _unsupported_reason_claims(
    recorded: Mapping[str, Gap],
    measured: Mapping[str, int],
    codes: Mapping[str, frozenset[str]],
) -> dict[str, list[str]]:
    """Claims a recorded reason owes but a measuring run does not bear out.

    THE CHECK THAT MAKES A REASON MORE THAN PROSE. ``reason.strip()`` asserts
    only that a string is non-empty, and a non-empty string can be, and once
    was, simply false. A reason is required to state the count and to name every
    error code the file really reports, both of which a run can contradict.

    One direction only. A reason may say more than the run does - "the fix needs
    a signature change upstream" is not falsifiable and is not meant to be - but
    it may not say LESS than the run about the errors themselves, because that
    is how a gap changes shape without the record noticing.

    Pure, for the same reason ``_gap_count_mismatches`` is: the real record is
    empty, so a synthetic one is the only thing that exercises this at all.

    Args:
        recorded: The gap record.
        measured: Errors per path from a run that DISCOVERS each path.
        codes: Error codes per path from that same run.

    Returns:
        Path to its unsupported claims, sorted, for every reason that owes one.
    """
    complaints: dict[str, list[str]] = {}
    for path, gap in sorted(recorded.items()):
        owed: list[str] = []
        if not gap.reason.strip():
            owed.append("states no reason at all")
        if str(measured.get(path, 0)) not in gap.reason:
            owed.append(f"states no count {measured.get(path, 0)}")
        owed += [
            f"never names code {code}"
            for code in sorted(codes.get(path, frozenset()))
            if code not in gap.reason
        ]
        if owed:
            complaints[path] = owed
    return complaints


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


def _unused_section_lines(output: str) -> list[str]:
    """Select mypy's warn_unused_configs diagnostics from its output.

    That diagnostic is the ONLY signal mypy gives that an overrides block
    matched nothing, and it is what makes per-module scoping checkable at all.

    Args:
        output: mypy stdout.

    Returns:
        Every line reporting an unused config section.
    """
    return [line for line in output.splitlines() if "unused section" in line]


@pytest.fixture(scope="session")
def repo_wide_mypy() -> subprocess.CompletedProcess[str]:
    """The real bare invocation, run once and shared.

    A full run costs several seconds and more than one test needs it. This is
    the actual command CI runs, with the committed config - not a generated
    variant standing in for it.

    Returns:
        The completed process.
    """
    return _run_mypy(config=REPO_ROOT / "pyproject.toml")


class _SyntheticGap(NamedTuple):
    """A throwaway project holding one file the gate's own config never reaches.

    Attributes:
        root: The throwaway project root.
        path: The gap file, relative to ``root``, in the same nested
            directory/file.py shape the real record and FROZEN_PYTHON_FILES use.
        errors: How many errors the gap file really contains, from reading it.
        codes: The mypy error codes those errors really carry.
        gate_counts: Errors per file from the gate's own bare invocation - the
            run that does NOT discover the gap.
        measured_counts: Errors per file from a run that DOES discover it.
        measured_codes: Error codes per file from that same run.
    """

    root: Path
    path: str
    errors: int
    codes: frozenset[str]
    gate_counts: dict[str, int]
    measured_counts: dict[str, int]
    measured_codes: dict[str, frozenset[str]]


@pytest.fixture(scope="session")
def synthetic_gap(tmp_path_factory: pytest.TempPathFactory) -> _SyntheticGap:
    """A real, measurable gap, built on a throwaway project.

    THIS REPOSITORY CANNOT SUPPLY ONE. Every authored file is inside the gate as
    of CS-415, so the only file that could stand in for a gap would have to be
    written into scripts/ or tools/ - a directory shared with concurrent work,
    and a tracked file this suite must never create. A throwaway project is also
    the stronger fixture: it keeps a claim about mypy proven against mypy rather
    than against whichever local file happens to be failing this month.

    Args:
        tmp_path_factory: pytest's session-scoped temporary directory factory.

    Returns:
        The built project and both measurements, taken once and shared.
    """
    root = tmp_path_factory.mktemp("gap_project")
    (root / "inside").mkdir()
    (root / "inside" / "clean.py").write_text("value: int = 1\n", encoding="utf-8")
    (root / "orphan").mkdir()
    # Three errors, two distinct codes: two arg-type and one assignment. Two
    # codes rather than one so a reason naming only the first is still wrong.
    (root / "orphan" / "broken.py").write_text(
        'def take(count: int) -> int:\n    return count\n\n\ntake("one")\ntake("two")\n'
        'total: int = "three"\n',
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        '[tool.mypy]\nfiles = ["inside"]\nshow_error_codes = true\n', encoding="utf-8"
    )

    gap = "orphan/broken.py"
    gate = _run_mypy(config=root / "pyproject.toml", cache=root / "gate_cache", cwd=root)
    measured = _measure_gaps([gap], root=root, cache=root / "measure_cache")
    return _SyntheticGap(
        root=root,
        path=gap,
        errors=3,
        codes=frozenset({"arg-type", "assignment"}),
        gate_counts=_errors_by_file(gate.stdout),
        measured_counts=_errors_by_file(measured.stdout),
        measured_codes=_error_codes_by_file(measured.stdout),
    )


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


def test_repo_wide_mypy_checks_every_frozen_python_file() -> None:
    # Frozen means "not editable without a grant", NOT "not checkable". The two
    # were conflated while tools/ sat outside `files`, and the conflation cost
    # coverage on the tier-0 gate itself. A scoped overrides block brought
    # tools/precommit_gate.py inside with no edit to it - see CS-415.
    #
    # PYTHON files, and the name says so. CLAUDE.md section 6 also freezes shell
    # hooks, a JSON settings file and the licence text; no mypy configuration
    # covers those, and a name promising every frozen file would be claiming
    # otherwise.
    covered = _repo_wide_mypy_sources()
    missing = sorted(path for path in _frozen_python_files() if path not in covered)
    assert not missing, (
        f"these frozen Python files are outside the bare `python -m mypy` "
        f"invocation: {missing}. Being frozen is a reason to check a file more "
        "carefully, not a reason to leave it unchecked."
    )


def test_the_frozen_list_is_read_from_the_file_that_owns_it() -> None:
    # The parse is load-bearing for two tests, so its failure has to be loud.
    # An empty or unfiltered result would make both of them assert nothing.
    entries = _frozen_entries()
    python_files = _frozen_python_files()
    assert entries, f"no frozen entries parsed out of {_FROZEN_SECTION_HEADING!r}"
    assert python_files, "the frozen list parsed, but no Python file came out of it"
    assert set(python_files) < set(entries), (
        f"every entry in CLAUDE.md section 6 is now a Python file: {entries}. "
        "The filter in _frozen_python_files is therefore doing nothing, and the "
        "coverage claim it feeds has quietly become a claim about the whole "
        "frozen list - which is what this test exists to keep it from doing."
    )


def test_the_environment_verifier_is_inside_the_gate() -> None:
    # CS-414. This file was held out of DISCOVERY by an `exclude` key over five
    # narrowing errors. The errors were fixed and the key deleted.
    covered = _repo_wide_mypy_sources()
    assert ENV_VERIFIER in covered, (
        f"{ENV_VERIFIER} is outside the bare `python -m mypy` invocation, so "
        "the gate CI runs never looks at it."
    )


@pytest.mark.slow
def test_the_bare_repo_wide_invocation_reports_no_errors(
    repo_wide_mypy: subprocess.CompletedProcess[str],
) -> None:
    # The acceptance criterion of CS-414 and CS-415 stated as the command CI
    # actually runs. Every other test in this file asserts what the gate LOOKS
    # AT; this one asserts it passes. Both are needed, and neither implies the
    # other.
    assert repo_wide_mypy.returncode == 0, (
        f"`python -m mypy` bare does not exit 0.\n{repo_wide_mypy.stdout}\n{repo_wide_mypy.stderr}"
    )


# ---------------------------------------------------------------------------
# Directory coverage, as directories
# ---------------------------------------------------------------------------


def test_the_scripts_directory_is_covered_as_a_directory(repo_files: list[Path]) -> None:
    # The property is "nothing under scripts/ is unexplained", NOT "the covered
    # set equals one hardcoded path". Equality would forbid the very thing
    # naming the directory buys, and its failure message would tell the next
    # reader to narrow `files` back down - reopening CS-411 to fix a red.
    present = set(_tracked_python_files(repo_files))
    unexplained = _uncovered_within("scripts", present, _repo_wide_mypy_sources(), _UNCOVERED)
    assert not unexplained, (
        f"these files under scripts/ are neither discovered by the bare mypy "
        f"invocation nor recorded as known gaps: {sorted(unexplained)}"
    )


def test_the_tools_directory_is_covered_as_a_directory(repo_files: list[Path]) -> None:
    # CS-415, and the same property as the scripts/ test above for the same
    # reason: a tool added tomorrow is covered because the DIRECTORY is named.
    present = set(_tracked_python_files(repo_files))
    unexplained = _uncovered_within("tools", present, _repo_wide_mypy_sources(), _UNCOVERED)
    assert not unexplained, (
        f"these files under tools/ are neither discovered by the bare mypy "
        f"invocation nor recorded as known gaps: {sorted(unexplained)}"
    )


def test_a_newly_added_script_would_not_turn_this_suite_red() -> None:
    # The regression test for the assertion this file used to make. A clean new
    # script is covered automatically because `files` names the directory, so
    # the correct outcome is silence. Synthetic sets rather than real files:
    # scripts/ is shared with concurrent work and a test must not write there.
    present = {HOOK_INSTALLER, "scripts/new_tool.py"}
    covered = {HOOK_INSTALLER, "scripts/new_tool.py"}
    assert _uncovered_within("scripts", present, covered, {}) == set()


def test_a_recorded_gap_is_tolerated_but_an_unrecorded_one_is_not() -> None:
    # The other half of _uncovered_within, which the real record can no longer
    # exercise now that it is empty. Supplied synthetically so the behaviour
    # stays pinned for whoever files the next gap.
    recorded = {"scripts/known_hole.py": Gap(errors=3, reason="measured elsewhere")}
    present = {HOOK_INSTALLER, "scripts/known_hole.py", "scripts/surprise.py"}
    covered = {HOOK_INSTALLER}
    assert _uncovered_within("scripts", present, covered, recorded) == {"scripts/surprise.py"}


# ---------------------------------------------------------------------------
# The configuration says what we think it says
# ---------------------------------------------------------------------------


def test_the_files_key_names_every_authored_directory(repo_files: list[Path]) -> None:
    # DERIVED from the repository, not compared against a hardcoded four-tuple.
    # The tuple was a restatement of the `files` key sitting next to an
    # assertion that the `files` key equalled it, so a fifth authored directory
    # would have had to be added in two places to be noticed in one.
    named = set(_mypy_config()["files"])
    authored = {_top_level(path) for path in _tracked_python_files(repo_files)}
    missing = sorted(authored - named - {"."})
    assert not missing, (
        f"these directories hold authored Python files but are not in the mypy "
        f"`files` key: {missing}. That key is the SOLE authority on what the "
        "bare invocation checks, so narrowing it silently removes files from "
        "the gate while CI stays green."
    )
    at_repo_root = sorted(
        path for path in _tracked_python_files(repo_files) if _top_level(path) == "."
    )
    assert not at_repo_root, (
        f"these authored Python files sit at the repository root: {at_repo_root}. "
        "`files` names DIRECTORIES so that a file added tomorrow is covered by "
        "default, and a root-level file is covered by no directory entry."
    )
    not_directories = sorted(entry for entry in named if not (REPO_ROOT / entry).is_dir())
    assert not not_directories, (
        f"the mypy `files` key names {not_directories}, which are not "
        "directories. A `files` entry that resolves to nothing contributes "
        "nothing to the gate while looking like coverage."
    )


def test_the_gate_config_declares_no_exclude_key() -> None:
    # CS-414 deleted the last one. The reflex this guards against is reaching
    # for `exclude` to make a red gate green: it filters DISCOVERY only, so it
    # hides a file from the walk while leaving every error intact the moment
    # anything imports it - see the hermetic demonstration below.
    config = _mypy_config()
    assert "exclude" not in config, (
        f"[tool.mypy] declares exclude = {config.get('exclude')!r}. An exclusion "
        "is not containment and it outlives its reason. Fix the errors instead, "
        "or record the file in _UNCOVERED with a measured count."
    )


def test_the_stubless_import_override_exists_and_is_narrow() -> None:
    overrides = _mypy_config()["overrides"]
    wanted = sorted(STUBLESS_MODULES)
    matching = [block for block in overrides if _module_patterns(block) == wanted]
    assert len(matching) == 1, (
        f"expected exactly one overrides block naming {STUBLESS_MODULES}, found "
        f"{len(matching)}. That block is what keeps the frozen "
        "tools/precommit_gate.py inside the gate with no edit to it."
    )
    assert matching[0].get("ignore_missing_imports") is True
    assert _mypy_config().get("ignore_missing_imports") is False, (
        "the GLOBAL ignore_missing_imports must stay false - a silent import "
        "failure makes a whole run vacuous."
    )


def test_the_config_these_tests_read_is_the_config_mypy_reads() -> None:
    # THE HOLE THE FOUR TESTS ABOVE SAT OVER. They read [tool.mypy] out of
    # pyproject.toml because that is where it lives - but mypy does not look
    # there first, so "the committed config says X" was a claim about a file
    # that a single untracked mypy.ini would have demoted to decoration. The
    # coverage assertions were never exposed: _repo_wide_mypy_sources asks mypy
    # itself and would follow the config move. This was a hole in the CONFIG
    # assertions only, and it is closed by asking mypy the same way.
    assert _discovered_config_file() == (REPO_ROOT / "pyproject.toml").resolve()


# ---------------------------------------------------------------------------
# The release the gate runs (CS-1302)
# ---------------------------------------------------------------------------
#
# WHICH MYPY, NOT ONLY WHICH CONFIG. Every test above pins what the bare
# invocation reads and covers; none pinned which RELEASE runs it. tier1 installs
# its toolchain from pyproject.toml's `dev` extra and nowhere else, and that
# extra once carried only a floor, so CI resolved whatever mypy was newest on the
# day while this machine ran the release it had. MEASURED (tier1 run
# 37958927844): CI installed a later mypy than this box ran, and the two reported
# one positional call to a keyword-only parameter under different error codes, so
# an ignore right for one was wrong for the other. A green bare run here was
# evidence about one release. The pin makes it evidence about the release CI runs.

_REQUIREMENT_NAME = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_EXACT_MYPY_PIN = re.compile(r"mypy==(\d+(?:\.\d+)*)")


def _dev_mypy_requirements(root: Path = REPO_ROOT) -> list[str]:
    """Every `dev` extra requirement naming mypy itself, PARSED rather than grepped.

    The name is the requirement's leading token, normalised the PEP 503 way, so a
    neighbour such as ``mypy-extensions`` is never mistaken for the pin, and a
    comment in pyproject.toml that spells a requirement is never read as one.

    Args:
        root: The directory holding the pyproject.toml to read.

    Returns:
        The matching requirement strings, stripped, in file order.
    """
    parsed = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    listed = parsed["project"]["optional-dependencies"]["dev"]
    found: list[str] = []
    for item in listed:
        match = _REQUIREMENT_NAME.match(str(item))
        if match and re.sub(r"[-_.]+", "-", match.group(1)).lower() == "mypy":
            found.append(str(item).strip())
    return found


def test_the_dev_extra_pins_mypy_to_one_exact_release() -> None:
    # A floor, a range or a compatible-release clause each still lets CI and
    # this machine resolve different releases, and different releases emit
    # different error codes. Only `==` names one release both installs read.
    requirements = _dev_mypy_requirements()

    assert len(requirements) == 1, (
        f"expected exactly one mypy requirement in the dev extra, found {requirements}"
    )
    assert _EXACT_MYPY_PIN.fullmatch(requirements[0]), (
        f"the dev extra pins mypy as {requirements[0]!r}, which is not one exact release. "
        "tier1 installs from this extra, so anything but `mypy==<version>` lets CI run a "
        "release this machine never ran"
    )


def test_the_pinned_mypy_is_the_release_this_interpreter_runs() -> None:
    # The pin is half the contract; the other half is that the local gate runs
    # it. _run_mypy invokes `sys.executable -m mypy`, so the distribution
    # installed in THIS interpreter is the release a local bare run uses.
    pinned = [
        match.group(1)
        for requirement in _dev_mypy_requirements()
        if (match := _EXACT_MYPY_PIN.fullmatch(requirement))
    ]
    installed = importlib.metadata.version("mypy")

    assert pinned == [installed], (
        f"the dev extra pins mypy {pinned or 'to no exact release'} but this interpreter "
        f'runs mypy {installed}. Install the pin (`python -m pip install -e ".[dev]"`) '
        "or move the pin deliberately, in one change, after a bare `python -m mypy` "
        "exits 0 under the new release"
    )


@pytest.mark.slow
def test_a_competing_mypy_ini_takes_the_config_away_from_pyproject(tmp_path: Path) -> None:
    # The measurement behind _mypy_config's guard, on a throwaway project so it
    # cannot rot and so proving it never writes a config into this repository.
    #
    # Both halves are needed. Without the first, "pyproject.toml wins" would be
    # indistinguishable from "this test never had a competitor to lose to".
    project = tmp_path / "throwaway"
    for name in ("alpha", "beta"):
        (project / name).mkdir(parents=True)
        (project / name / f"{name}.py").write_text("value: int = 1\n", encoding="utf-8")
    (project / "pyproject.toml").write_text('[tool.mypy]\nfiles = ["alpha"]\n', encoding="utf-8")

    assert _discovered_config_file(project) == (project / "pyproject.toml").resolve()
    assert _mypy_config(project)["files"] == ["alpha"]

    (project / "mypy.ini").write_text("[mypy]\nfiles = beta\n", encoding="utf-8")

    assert _discovered_config_file(project) == (project / "mypy.ini").resolve(), (
        "mypy no longer prefers mypy.ini over pyproject.toml, so _mypy_config's "
        "guard is now asserting against a precedence that has changed."
    )
    # Not merely a different filename in a field: the competitor takes over
    # DISCOVERY, which is the thing every other test in this file measures.
    with contextlib.chdir(project):
        import mypy.main  # noqa: PLC0415

        sources, _options = mypy.main.process_options(
            [], stdout=io.StringIO(), stderr=io.StringIO()
        )
    assert sorted(source.module for source in sources) == ["beta"]

    # And the parser refuses rather than reading the demoted table.
    with pytest.raises(AssertionError, match=r"mypy\.ini"):
        _mypy_config(project)


def test_no_overrides_block_sets_strict() -> None:
    # The trap documented at length in pyproject.toml, executed. `strict` in an
    # overrides block is accepted without complaint and applied GLOBALLY, which
    # is the opposite of the per-module scoping every other key in that position
    # gets. Acceptance of the key is not evidence of scoping.
    offenders = [block.get("module") for block in _mypy_config()["overrides"] if "strict" in block]
    assert not offenders, (
        f"these overrides blocks set `strict`: {offenders}. It is NOT scoped to "
        "the module pattern - it turns the strict flags on globally. Write the "
        "per-module-settable constituents instead."
    )


# ---------------------------------------------------------------------------
# The oracle stands for the real invocation
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_the_oracle_reproduces_the_real_runs_discovered_set(tmp_path: Path) -> None:
    # SETS, not counts. mypy's success line prints len(sources) - the same
    # quantity the oracle counts - so comparing counts is very nearly a
    # tautology and would not notice one file being swapped for another.
    # --linecount-report is a documented flag that names every module in the
    # run's source set, unlike the cache, whose layout is internal. Measured:
    # it lists the DISCOVERED set, so it agrees with the oracle rather than
    # with the larger reported-on set.
    report_dir = tmp_path / "report"
    _run_mypy("--linecount-report", str(report_dir), config=REPO_ROOT / "pyproject.toml")
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


def _build_exclusion_project(root: Path, exclude: str = _LEAF_EXCLUDE) -> Path:
    """Write the throwaway project the exclusion arms run mypy against.

    One module, ``leaf``, carries one real error and is named by ``exclude``;
    a second module, ``trunk``, imports it. Built fresh per arm so no arm can
    read another arm's cache or config.

    Args:
        root: The throwaway project root, created here.
        exclude: The mypy ``exclude`` pattern to write. The control arm passes
            one that matches nothing, so discovery genuinely stops filtering.

    Returns:
        The written config file.
    """
    source_dir = root / "src"
    source_dir.mkdir(parents=True)
    (source_dir / "leaf.py").write_text(
        "def take(count: int) -> int:\n    return count\n\n\ntake('not a number')\n",
        encoding="utf-8",
    )
    (source_dir / "trunk.py").write_text("import leaf\n\nleaf.take(1)\n", encoding="utf-8")
    config = root / "mypy.ini"
    config.write_text(f"[mypy]\nfiles = src\nexclude = {exclude}\n", encoding="utf-8")
    return config


def _assert_exclude_filters_discovery_only(result: subprocess.CompletedProcess[str]) -> None:
    """The exclusion arm's two checks, shared so its control runs the SAME checks.

    Args:
        result: A mypy run over the project ``_build_exclusion_project`` wrote.

    Raises:
        AssertionError: Discovery was not filtered, or leaf.py's error was not
            attributed to leaf.py.
    """
    assert _reported_file_count(result.stdout) == 1, (
        "the exclusion did not remove leaf.py from DISCOVERY, so this test is "
        f"not measuring what it claims to.\n{result.stdout}"
    )
    assert _errors_by_file(result.stdout) == {"src/leaf.py": 1}, (
        "mypy did not report leaf.py's one error against leaf.py, so either "
        "`exclude` now behaves as containment - and the reasoning recorded in "
        "pyproject.toml and in this module's docstring needs rechecking - or the "
        f"error is being attributed somewhere else.\n{result.stdout}"
    )


def _resolve_plant(plant: Mapping[str, str], project: Path) -> dict[str, str]:
    """Resolve a hazard's value tokens to the values planted.

    Args:
        plant: Variables to value tokens, from ``_AMBIENT_PLANTS``. Path tokens
            are resolved here because the throwaway project only exists per
            test; any other token is planted literally.
        project: The throwaway project root.

    Returns:
        Variables to the values to plant.
    """
    paths = {
        "<repo_root>": str(REPO_ROOT),
        "<project_root>": str(project),
        "<source_root>": str(project / "src"),
    }
    return {name: paths.get(token, token) for name, token in plant.items()}


@pytest.fixture(scope="session")
def warm_mypy_cache(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A mypy cache holding only what a one-empty-module project builds.

    THE COST IT REMOVES. A cold mypy run spends most of its time building the
    standard library - measured locally at 1.07s cold against 0.29s from a warm
    copy - and the CS-1125 environment arms make dozens of runs, all of them in
    the tier-1 guard shard, which runs this module on one worker.

    WHY IT CANNOT HIDE A HAZARD. It is built under the controlled environment
    from a project whose only module is empty, so it holds no module any arm
    checks: every leaf, trunk and planted module is built fresh in every run.
    And no run shares it - each gets a PRIVATE copy through ``_seeded_cache`` -
    so nothing one run records can reach another. The anti-vacuity arms run on
    seeded copies too, so a hazard a warm cache masked would turn them red.

    Args:
        tmp_path_factory: pytest's session-scoped temporary directory factory.

    Returns:
        The warm cache directory. Never pass it to a run directly.
    """
    root = tmp_path_factory.mktemp("warm_mypy_cache")
    project = root / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "empty.py").write_text("", encoding="utf-8")
    config = project / "mypy.ini"
    config.write_text("[mypy]\nfiles = src\n", encoding="utf-8")
    cache = root / "cache"
    warmed = _run_mypy(config=config, cache=cache, cwd=project)
    assert warmed.returncode == 0, f"the cache warm-up run failed:\n{warmed.stdout}{warmed.stderr}"
    return cache


def _seeded_cache(warm: Path, destination: Path) -> Path:
    """Give one mypy run a private copy of the warm cache.

    Args:
        warm: The ``warm_mypy_cache`` fixture's directory.
        destination: Where this run's cache lives; must not exist yet.

    Returns:
        ``destination``, now holding the copy.
    """
    shutil.copytree(warm, destination)
    return destination


def _run_exclusion_arm(
    project: Path, config: Path, cache: Path, env: Mapping[str, str] | None = None
) -> None:
    """Run mypy over the exclusion project and apply the arm's checks.

    Args:
        project: The throwaway project root, used as mypy's working directory.
        config: The project's mypy config.
        cache: A cache directory private to this run.
        env: Passed through to ``_run_mypy``.

    Raises:
        AssertionError: The arm's checks refused the run.
        UnicodeDecodeError: mypy wrote a stream that is not UTF-8.
    """
    _assert_exclude_filters_discovery_only(
        _run_mypy(config=config, cache=cache, cwd=project, env=env)
    )


@pytest.mark.slow
def test_exclude_filters_discovery_and_does_not_contain_errors(tmp_path: Path) -> None:
    # THE CLAIM THE CONFIG COMMENT MAKES, EXECUTED. `exclude` keeps mypy from
    # WALKING to a file; it does not stop a checked file from IMPORTING it, and
    # an imported module is built and reported on in full.
    #
    # Demonstrated on a THROWAWAY PROJECT rather than on this repository's own
    # files. The version of this test that measured scripts/verify_env.py could
    # only work while that file was both excluded AND broken, so fixing it
    # under CS-414 destroyed the fixture the proof rested on. A property of
    # mypy should be proven against mypy, not against whichever local file
    # happens to be failing this month.
    project = tmp_path / "throwaway"
    config = _build_exclusion_project(project)

    result = _run_mypy(config=config, cache=tmp_path / "cache", cwd=project)

    _assert_exclude_filters_discovery_only(result)


@pytest.mark.slow
@pytest.mark.parametrize("plant", _AMBIENT_PARAMS)
def test_the_exclusion_arm_does_not_report_on_the_ambient_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plant: dict[str, str],
    warm_mypy_cache: Path,
) -> None:
    # CS-1125. The arm above once INHERITED its environment: run as
    # `PYTHONPATH=.`, mypy put the throwaway project on its search path,
    # `import leaf` stopped resolving to the excluded file beside it, and the arm
    # failed against an empty mapping while mypy printed Success. FORCE_COLOR=1
    # and PYTHONIOENCODING=utf-16 break it too, by making the output unparseable.
    # Planted in the pytest PROCESS's own environment, not a shell variable:
    # MSYS mangles a POSIX path in env.
    project = tmp_path / "throwaway"
    config = _build_exclusion_project(project)
    for variable, value in _resolve_plant(plant, project).items():
        monkeypatch.setenv(variable, value)
        planted = os.environ.get(variable) == value
        assert planted, f"the ambient {variable} was never planted"

    _run_exclusion_arm(project, config, _seeded_cache(warm_mypy_cache, tmp_path / "cache"))


@pytest.mark.slow
@pytest.mark.parametrize("plant", _AMBIENT_PARAMS)
def test_the_exclusion_arm_reddens_when_discovery_stops_filtering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plant: dict[str, str],
    warm_mypy_cache: Path,
) -> None:
    # THE CONTROL. Controlling the environment must not have made the arm blind:
    # with an `exclude` that matches nothing, discovery genuinely stops
    # filtering, and the SAME checks must refuse it under the same planted
    # variable the arm above is proven against.
    project = tmp_path / "throwaway"
    config = _build_exclusion_project(project, exclude=_NON_MATCHING_EXCLUDE)
    written = config.read_text(encoding="utf-8")
    assert _NON_MATCHING_EXCLUDE in written, f"the mutated exclude never landed:\n{written}"
    assert _LEAF_EXCLUDE not in written, f"the original exclude survived:\n{written}"
    for variable, value in _resolve_plant(plant, project).items():
        monkeypatch.setenv(variable, value)

    result = _run_mypy(
        config=config, cache=_seeded_cache(warm_mypy_cache, tmp_path / "cache"), cwd=project
    )

    assert _reported_file_count(result.stdout) == _UNFILTERED_SOURCE_COUNT, (
        f"the mutated exclude still filtered discovery:\n{result.stdout}"
    )
    with pytest.raises(AssertionError, match=re.escape("did not remove leaf.py from DISCOVERY")):
        _assert_exclude_filters_discovery_only(result)


@pytest.mark.slow
@pytest.mark.parametrize("plant", _LIVE_AMBIENT_PARAMS)
def test_each_planted_variable_really_breaks_the_exclusion_arm(
    tmp_path: Path, plant: dict[str, str], warm_mypy_cache: Path
) -> None:
    # ANTI-VACUITY for the ambient arm. A planted value mypy happens to ignore
    # would keep that arm green without controlling anything, so each variable
    # named live is shown to break the arm when it DOES reach mypy. The rest of
    # the environment is the controlled one, so the planted variable is the
    # only difference between the green run and the red one - an inherited
    # environment carrying some OTHER hazard cannot satisfy this arm for it.
    # An absolute repository root is absent on purpose: measured harmless. No
    # platform is excused: a hazard live on only one platform is an incomplete
    # plant, and ubuntu CI caught exactly that for FORCE_COLOR without TERM.
    project = tmp_path / "throwaway"
    config = _build_exclusion_project(project)

    _run_exclusion_arm(
        project,
        config,
        _seeded_cache(warm_mypy_cache, tmp_path / "clean_cache"),
        env=_controlled_environment(),
    )

    planted = {**_controlled_environment(), **_resolve_plant(plant, project)}
    with pytest.raises((AssertionError, UnicodeDecodeError)):
        _run_exclusion_arm(
            project, config, _seeded_cache(warm_mypy_cache, tmp_path / "planted_cache"), env=planted
        )


def test_the_controlled_environment_is_an_allowlist_in_any_case() -> None:
    # Case-INSENSITIVE on purpose. On Windows `dict(os.environ)` upper-cases
    # keys, but a mapping built any other way need not. Anything not named is
    # dropped, including variables no denylist here ever named.
    ambient = {
        "Path": "kept",
        "SystemRoot": "kept",
        "AppData": "dropped",
        "PythonPath": ".",
        "mypypath": ".",
        "force_color": "1",
        "PYTHONIOENCODING": "utf-16",
        "SOME_FUTURE_VARIABLE": "1",
    }
    expected = {"Path": "kept", "SystemRoot": "kept", **_PINNED_ENVIRONMENT}
    # CS-1199. The helper's return reads this process's environment on its
    # default path, so only KEY NAMES cross the assertion.
    controlled = _controlled_environment(ambient)
    differing = sorted(
        name
        for name in set(controlled) | set(expected)
        if controlled.get(name) != expected.get(name)
    )
    assert differing == [], f"the controlled environment differs at: {differing}"


def _hostile_home(root: Path) -> dict[str, str]:
    """Build a fake user home that plants a mypy config, and name its variables.

    Every per-user config location mypy falls back to when no project config is
    found carries ``ignore_errors = True``, so a run that reads any of them
    reports Success over a real error.

    Args:
        root: Directory to build the fake home under.

    Returns:
        The variables that point a process at that home, on Windows and POSIX.
    """
    home = root / "hostile_home"
    planted = "[mypy]\nignore_errors = True\n"
    for config in (home / ".mypy.ini", home / ".config" / "mypy" / "config"):
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(planted, encoding="utf-8")
    return {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "APPDATA": str(home / "AppData" / "Roaming"),
    }


@pytest.mark.slow
def test_a_non_ascii_path_decodes_and_no_user_config_reaches_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, warm_mypy_cache: Path
) -> None:
    # Two controls, one project, because both bite only a project with no config
    # file of its own beside it.
    #
    # THE PYTHONIOENCODING PIN. Measured on Windows: without it the child writes
    # a non-ASCII path in the locale's code page and this process's UTF-8
    # decode raises. A UTF-8 locale agrees without the pin, so there this arm
    # cannot tell them apart.
    #
    # THE EXPLICIT CONFIG. With no config beside the project, mypy falls back to
    # a per-user one - ~/.mypy.ini, ~/.config/mypy/config - and the home
    # variables that locate it are ones the interpreter keeps. A real
    # ~/.mypy.ini with ignore_errors turned this arm into Success over an error.
    project = tmp_path / "throwaway"
    (project / "src").mkdir(parents=True)
    module = "caf" + chr(0xE9)
    (project / "src" / f"{module}.py").write_text("x: int = 'not a number'\n", encoding="utf-8")
    home = _hostile_home(tmp_path)

    # ANTI-VACUITY: the planted home really is read by a run that names no config.
    discovering = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--no-pretty",
            "--cache-dir",
            str(_seeded_cache(warm_mypy_cache, tmp_path / "c0")),
            "src",
        ],
        cwd=project,
        env={**_controlled_environment(), **home},
        capture_output=True,
        timeout=_MYPY_TIMEOUT_SECONDS,
        check=False,
    ).stdout.decode("utf-8")
    assert _errors_by_file(discovering) == {}, f"the planted config was not read:\n{discovering}"

    # The run names a config that is NOT beside the project, so dropping the
    # name would leave mypy discovering - and finding the planted home.
    config = tmp_path / "named_config" / "mypy.ini"
    config.parent.mkdir()
    config.write_text("[mypy]\n", encoding="utf-8")
    for name, value in home.items():
        monkeypatch.setenv(name, value)
    result = _run_mypy(
        "src", config=config, cache=_seeded_cache(warm_mypy_cache, tmp_path / "cache"), cwd=project
    )

    assert _errors_by_file(result.stdout) == {f"src/{module}.py": 1}, result.stdout


@pytest.mark.slow
def test_a_planted_user_site_cannot_reach_the_exclusion_arm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, warm_mypy_cache: Path
) -> None:
    # A .pth file in the per-user site-packages directory is executed at
    # interpreter start, and mypy builds its search path from a child
    # interpreter's sys.path. One naming the throwaway project's src put the
    # excluded leaf on that path: Success over a real error, the CS-1125
    # symptom again, located through APPDATA on Windows and HOME on POSIX.
    # HOME stays inherited, so on POSIX only the PYTHONNOUSERSITE pin holds;
    # the direct half below plants APPDATA over the pins too, so the pin is
    # proven on Windows as well rather than the allowlist standing in for it.
    project = tmp_path / "throwaway"
    config = _build_exclusion_project(project)
    home = _hostile_home(tmp_path)
    hostile = {**_controlled_environment(), **home}
    enabled = {name: value for name, value in hostile.items() if name.upper() != "PYTHONNOUSERSITE"}

    # CS-1187, measured in a never-seen sandbox: a default `python -m venv`
    # interpreter switches the user site OFF in site.py itself, whatever the
    # environment says. There the plant cannot reach mypy with or without the
    # pin, the anti-vacuity half below cannot go red, and every half of this
    # arm would be a measurement of nothing.
    user_site_live = (
        subprocess.run(
            [sys.executable, "-c", "import site; print(site.ENABLE_USER_SITE)"],
            env=enabled,
            capture_output=True,
            timeout=_MYPY_TIMEOUT_SECONDS,
            check=True,
        )
        .stdout.decode("utf-8")
        .strip()
        == "True"
    )
    if not user_site_live:
        pytest.skip(
            "NOT RUN, NOT PASSED: this interpreter disables the per-user site itself "
            "(a venv without system site packages), so no planted user site can reach "
            "mypy and the anti-vacuity half cannot go red (CS-1187). Read the arm as "
            "NOT RUN, never as covered."
        )

    user_site = (
        subprocess.run(
            [sys.executable, "-c", "import site; print(site.getusersitepackages())"],
            env=hostile,
            capture_output=True,
            timeout=_MYPY_TIMEOUT_SECONDS,
            check=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    Path(user_site).mkdir(parents=True)
    (Path(user_site) / "cs1125_plant.pth").write_text(f"{project / 'src'}\n", encoding="utf-8")

    # ANTI-VACUITY: with the user site enabled, the plant really breaks the arm.
    with pytest.raises(AssertionError):
        _run_exclusion_arm(
            project, config, _seeded_cache(warm_mypy_cache, tmp_path / "enabled_cache"), env=enabled
        )

    # The controls hold with the hostile home planted directly over them...
    _run_exclusion_arm(
        project, config, _seeded_cache(warm_mypy_cache, tmp_path / "direct_cache"), env=hostile
    )

    # ...and when it is merely ambient.
    for name, value in home.items():
        monkeypatch.setenv(name, value)
    _run_exclusion_arm(project, config, _seeded_cache(warm_mypy_cache, tmp_path / "ambient_cache"))


def test_the_importers_of_the_environment_verifier_are_recorded(repo_files: list[Path]) -> None:
    # Both directions, so the record cannot rot: every recorded importer really
    # imports it, and no unrecorded file does. These are the imports that made
    # the deleted `exclude` key inert, and they are also the reason scripts/ and
    # tools/ have to enter the gate together rather than one at a time.
    module = Path(ENV_VERIFIER).stem
    pattern = re.compile(rf"^\s*import\s+{module}\b", re.MULTILINE)
    found = {
        path
        for path in _tracked_python_files(repo_files)
        if path != ENV_VERIFIER and pattern.search((REPO_ROOT / path).read_text(encoding="utf-8"))
    }
    assert found == set(IMPORTERS_OF_THE_ENV_VERIFIER), (
        f"the set of files importing `{module}` as a top-level module has "
        f"changed: recorded {sorted(IMPORTERS_OF_THE_ENV_VERIFIER)}, found "
        f"{sorted(found)}. This import only resolves because scripts/ is a "
        "mypy source base dir, and it is what defeats any exclusion of that file."
    )


# ---------------------------------------------------------------------------
# Per-module overrides really are per-module
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_the_stubless_override_is_scoped_and_mypy_would_say_so_if_it_were_not(
    tmp_path: Path,
    repo_wide_mypy: subprocess.CompletedProcess[str],
) -> None:
    # THE SCOPING IS PROVEN, NOT ASSUMED, and this is the measurement that
    # proves it. `warn_unused_configs = true` makes mypy name any overrides
    # block whose module pattern matched nothing in the run. So:
    #
    #   the committed run names NO block  ->  every block, including the
    #                                         ruff/yaml one, matched something
    #   a block naming an impossible module IS named  ->  the mechanism works,
    #                                         and silence above was not silence
    #                                         about everything
    #
    # Without the negative control the first assertion alone would be satisfied
    # by mypy simply never emitting the diagnostic.
    assert _unused_section_lines(repo_wide_mypy.stdout) == [], (
        "mypy reports an unused overrides section under the committed config, "
        "so a block that is meant to be scoped is matching nothing.\n"
        f"{repo_wide_mypy.stdout}"
    )

    source = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    probe = (
        f'{source}\n[[tool.mypy.overrides]]\nmodule = ["{UNMATCHABLE_MODULE}"]\n'
        "ignore_missing_imports = true\n"
    )
    config = tmp_path / "with_unmatchable.toml"
    config.write_text(probe, encoding="utf-8")
    control = _run_mypy(config=config, cache=tmp_path / "cache")

    unused = _unused_section_lines(control.stdout)
    assert len(unused) == 1, (
        "the negative control did not produce exactly one unused-section "
        "diagnostic, so this test cannot tell scoping from silence.\n"
        f"{control.stdout}"
    )
    assert UNMATCHABLE_MODULE in unused[0], f"unexpected diagnostic: {unused[0]}"
    for module in STUBLESS_MODULES:
        assert module not in unused[0], (
            f"mypy named the `{module}` override as unused, so the block that "
            "keeps the frozen tools/precommit_gate.py inside the gate is no "
            f"longer matching anything.\n{control.stdout}"
        )


@pytest.mark.slow
def test_the_frozen_commit_gate_reports_no_errors(
    repo_wide_mypy: subprocess.CompletedProcess[str],
) -> None:
    # The tripwire CS-415 was dispatched with. Bringing tools/ into `files`
    # makes mypy CHECK a frozen file, and an error there cannot be fixed
    # without an adjudicator grant. It reports none - the one error it had was
    # an import-untyped for the stub-less `ruff`, cleared from OUTSIDE the file
    # by the scoped override above.
    #
    # IMPLIED BY ITS NEIGHBOUR TODAY, and that is not a reason to drop it. While
    # the bare run exits 0 this cannot fail, so it earns nothing that
    # test_the_bare_repo_wide_invocation_reports_no_errors does not; it earns
    # its place on the day the bare run goes red, by saying WHICH kind of red it
    # is. A red here means the fix needs a grant, which is a different next step
    # from a red anywhere else, and nothing else in this file distinguishes them.
    # Its live risk is the other way round - passing because _errors_by_file
    # never produces a key of the recorded shape - and that is what the
    # companion below measures.
    observed = _errors_by_file(repo_wide_mypy.stdout)
    frozen = _frozen_python_files()
    frozen_errors = {path: count for path, count in observed.items() if path in frozen}
    assert not frozen_errors, (
        f"mypy reports errors in frozen files: {frozen_errors}. These cannot be "
        "fixed without an adjudicator grant recorded in docs/LEDGER.md, and "
        "silencing them with a broadened override would be the same evasion in "
        f"a different file.\n{repo_wide_mypy.stdout}"
    )


@pytest.mark.slow
def test_the_error_parser_keys_files_the_way_the_frozen_list_names_them(
    synthetic_gap: _SyntheticGap,
) -> None:
    # THE NON-VACUITY COMPANION the tripwire above lacked. That test asks
    # whether any _errors_by_file key matches a frozen path, and it is satisfied
    # just as well by the parser never producing a matching key at all - which a
    # change in how mypy prints paths would cause silently, leaving a green
    # tripwire wired to nothing.
    #
    # So this measures the key format against a REAL run over a file at the same
    # depth every frozen entry sits at: repo-relative, forward slashes, no drive
    # letter, no leading "./". mypy prints a backslash separator on this
    # platform, so the normalisation in _errors_by_file is load-bearing rather
    # than decorative.
    key = synthetic_gap.path
    assert set(synthetic_gap.measured_counts) == {key}, (
        f"the measuring run did not key its errors by the gap's own relative path.\n{synthetic_gap}"
    )
    assert "\\" not in key
    assert not Path(key).is_absolute()
    assert not key.startswith("./")
    frozen_depths = {len(Path(entry).parts) for entry in _frozen_python_files()}
    assert len(Path(key).parts) in frozen_depths, (
        f"the parser keys a nested file as {key!r}, which is not the shape the "
        f"frozen list is written in {sorted(_frozen_python_files())}. The "
        "tripwire above compares those two forms directly, so it would pass "
        "forever without ever matching."
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
    if not _UNCOVERED:
        pytest.skip("the gap record is empty - every authored file is inside the gate")
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
def test_the_recorded_error_counts_are_still_accurate() -> None:
    # THE ORACLE THE RECORD USED TO LACK, MEASURED BY A RUN THAT DISCOVERS THE
    # GAP. The bare invocation is the wrong instrument for this and reading it
    # made the oracle unsatisfiable: a gap is BY DEFINITION a file outside
    # `files`, mypy reports nothing for a file it never discovers, so the
    # measured count was always 0 and the only record that could ever pass was
    # one that wrote errors=0 - the single value carrying no information.
    #
    # _measure_gaps names the gate's own targets AND each gap, so the number is
    # the one Gap.errors claims to be: the measured cost of bringing it in.
    if not _UNCOVERED:
        pytest.skip("the gap record is empty - there are no counts to re-measure")
    measured = _measure_gaps(sorted(_UNCOVERED))
    mismatches = _gap_count_mismatches(_UNCOVERED, _errors_by_file(measured.stdout))
    assert not mismatches, (
        "the recorded per-file error counts no longer match a run that "
        f"discovers them: {mismatches} as path -> (recorded, measured). Update "
        f"_UNCOVERED, and update any roadmap item quoting these numbers.\n"
        f"{measured.stdout}"
    )


@pytest.mark.slow
def test_a_recorded_reason_names_the_error_codes_a_real_run_reports() -> None:
    # M2's replacement for the deleted reason check. `gap.reason.strip()` alone
    # asserts that a string is non-empty, which is the free-prose state this
    # module's docstring says an earlier version was corrected out of.
    #
    # A reason has to carry claims a run can falsify. The codes are that claim:
    # a count alone cannot tell "the narrowing bug got fixed" from "an unrelated
    # assignment bug replaced it", and a reason describing the first would stay
    # green over the second.
    if not _UNCOVERED:
        pytest.skip("the gap record is empty - there are no reasons to falsify")
    measured = _measure_gaps(sorted(_UNCOVERED))
    unsupported = _unsupported_reason_claims(
        _UNCOVERED, _errors_by_file(measured.stdout), _error_codes_by_file(measured.stdout)
    )
    assert not unsupported, (
        "these recorded reasons make claims a real run does not bear out: "
        f"{unsupported}. A reason must name every error code the file actually "
        "reports and state the count, so a gap that changed shape turns this "
        f"file red instead of sitting there being believed.\n{measured.stdout}"
    )


# ---------------------------------------------------------------------------
# ... and the dormant machinery above is exercised on a gap that really exists
# ---------------------------------------------------------------------------
#
# WHY THESE ARE HERE AT ALL. The two tests above skip, and a skip conceals
# whether the thing skipping is correct. The previous version of this file
# skipped over an oracle that COULD NOT PASS for any genuine gap, and the skip
# is precisely what kept that invisible. So the same functions are driven here
# against a throwaway project that does contain a gap, with the right answer and
# with a wrong one.


@pytest.mark.slow
def test_the_gate_run_cannot_measure_a_gap_but_the_measuring_run_can(
    synthetic_gap: _SyntheticGap,
) -> None:
    # THE DEFECT, DEMONSTRATED. Both halves matter: the first is what the old
    # oracle read, and it reports nothing at all for a file the gate never
    # walks to.
    assert synthetic_gap.gate_counts == {}, (
        "the gate's own invocation reported errors for a file outside its "
        f"`files` key, so this fixture is not modelling a gap.\n{synthetic_gap}"
    )
    assert synthetic_gap.measured_counts == {synthetic_gap.path: synthetic_gap.errors}, (
        "a run naming the gap as a target did not report the errors the gap "
        f"file really contains.\n{synthetic_gap}"
    )
    assert synthetic_gap.measured_codes[synthetic_gap.path] == synthetic_gap.codes


@pytest.mark.slow
def test_the_count_oracle_passes_a_true_record_and_fails_a_wrong_one(
    synthetic_gap: _SyntheticGap,
) -> None:
    # The repopulation the empty record cannot provide. errors=3 is the real,
    # NON-ZERO count of a real file, so this pins that the oracle can pass on
    # something other than zero - which the version it replaces could not.
    truthful = {synthetic_gap.path: Gap(errors=synthetic_gap.errors, reason="measured")}
    assert _gap_count_mismatches(truthful, synthetic_gap.measured_counts) == {}

    wrong = {synthetic_gap.path: Gap(errors=synthetic_gap.errors + 2, reason="measured")}
    assert _gap_count_mismatches(wrong, synthetic_gap.measured_counts) == {
        synthetic_gap.path: (synthetic_gap.errors + 2, synthetic_gap.errors)
    }

    # And the failure mode that made the old oracle unsatisfiable: measured
    # against the gate's own run, the true record is the one that looks wrong.
    assert _gap_count_mismatches(truthful, synthetic_gap.gate_counts) == {
        synthetic_gap.path: (synthetic_gap.errors, 0)
    }


@pytest.mark.slow
def test_the_reason_oracle_rejects_a_reason_a_real_run_contradicts(
    synthetic_gap: _SyntheticGap,
) -> None:
    counts = synthetic_gap.measured_counts
    codes = synthetic_gap.measured_codes

    honest = Gap(
        errors=synthetic_gap.errors,
        reason="3 errors, arg-type and assignment, from an unannotated helper.",
    )
    assert _unsupported_reason_claims({synthetic_gap.path: honest}, counts, codes) == {}

    # Non-empty prose that names nothing measurable - the state `reason.strip()`
    # accepts and this oracle exists to reject.
    vague = Gap(errors=synthetic_gap.errors, reason="not worth fixing right now")
    assert _unsupported_reason_claims({synthetic_gap.path: vague}, counts, codes) == {
        synthetic_gap.path: [
            "states no count 3",
            "never names code arg-type",
            "never names code assignment",
        ]
    }

    # Half-true is still false: naming one of the two codes leaves a claim the
    # run contradicts, which is exactly the drift a fixed-then-reappeared bug
    # produces.
    partial = Gap(errors=synthetic_gap.errors, reason="3 arg-type errors")
    assert _unsupported_reason_claims({synthetic_gap.path: partial}, counts, codes) == {
        synthetic_gap.path: ["never names code assignment"]
    }
