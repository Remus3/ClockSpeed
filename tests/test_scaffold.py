"""Phase 0 acceptance tests: the scaffold surface itself.

These are not placeholders. Each one asserts a condition BOOTSTRAP.md or
CONVENTIONS.md states as a requirement, and each one is capable of failing.

What is covered, and the authority for it:

a. The module topology of BOOTSTRAP.md section 6 exists and every package in
   it is genuinely importable.
b. Every file in the documentation-ownership table of CONVENTIONS.md
   section 2 exists. Some of these are authored by other slices; it is
   CORRECT for this to be red until they land, and the assertion is not
   weakened or skipped to hide that.
c. Every authored text file is pure 7-bit ASCII, asserted on the raw BYTES.
   BOOTSTRAP.md section 12 item 4 and CONVENTIONS.md section 10. This is the
   most valuable test in the file: the rule exists because one non-ASCII
   character in a PowerShell script cascaded into a parse failure, and the
   only check that cannot be fooled is one that reads bytes.
d. LICENSE names a real copyright holder. CONVENTIONS.md section 14 trap 3:
   a LICENSE naming nobody is a grant with no grantor, and both files can
   "agree on MIT" while an SPDX grep passes.
e. .gitignore actually excludes the dangerous classes - saves, generated data,
   local config - asserted both as declared patterns and as git's own
   behaviour.
f. No authored file contains an absolute path under a user home directory.
   BOOTSTRAP.md section 12 item 3, CONVENTIONS.md section 10.

Test-quality discipline (CONVENTIONS.md section 7.2): a negative assertion
rules out without pinning down - "field X is absent" passes for the correct
output AND for a totally collapsed one. Every absence assertion below is
therefore paired with a presence assertion. The character-set scan asserts its
own inventory is populated; the home-path scan asserts its detector actually
detects; the .gitignore check asserts that source files are NOT ignored as
well as that saves are.
"""

from __future__ import annotations

import importlib
import re
import tomllib
import unicodedata
from pathlib import Path
from typing import Any

import pytest

import clockspeed
from tests.conftest import run_git, walk_inventory

# ---------------------------------------------------------------------------
# The topology under test (BOOTSTRAP.md section 6)
# ---------------------------------------------------------------------------

# Every directory below must exist AND be an importable package.
PACKAGE_TOPOLOGY: tuple[str, ...] = (
    "clockspeed",
    "clockspeed/data",
    "clockspeed/save",
    "clockspeed/solve",
    "clockspeed/solve/backends",
    "clockspeed/audit",
    "clockspeed/progress",
    "clockspeed/advisor",
    "clockspeed/advisor/rules",
    "clockspeed/surface",
    "clockspeed/surface/api",
    "tests",
)

CLOCKSPEED_PACKAGES: tuple[str, ...] = tuple(
    name for name in PACKAGE_TOPOLOGY if name.split("/")[0] == "clockspeed"
)

# Directories from the section 6 tree that are NOT python packages but must
# exist by the end of phase 0 (BOOTSTRAP.md section 10, CONVENTIONS.md
# section 19 checklist).
#
# Two section 6 directories are deliberately absent from this list, each for
# a stated reason rather than to make the suite green:
#   clockspeed/surface/web  dashboard assets, phase 6. It would also be
#                           untestable in phase 0: git does not track empty
#                           directories, so a clean clone could not reproduce
#                           it and the assertion would be red with no
#                           legitimate fix available.
#   data/                   generated artifacts, GITIGNORED (section 6). It
#                           exists only after an extraction run; asserting its
#                           presence would assert that the game is installed,
#                           which contradicts "runs on a clean machine with no
#                           game installed" (section 8.1).
REQUIRED_DIRECTORIES: tuple[str, ...] = (
    "docs",
    "memory",
    "scripts",
    "shell",
    "tools",
)

# CONVENTIONS.md section 2, the documentation-ownership table. Every fact has
# exactly one owner file; a missing owner means the fact has nowhere to live
# and will be restated somewhere it drifts.
DOC_OWNERSHIP_FILES: tuple[str, ...] = (
    "CLAUDE.md",
    "README.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "docs/LEDGER.md",
    "docs/ARCHITECTURE.md",
    "docs/OPERATIONS.md",
    "docs/adr/README.md",
    "docs/GATED.md",
    "WAKEUP_NOTES.md",
    "docs/history_notes.md",
    "memory/MEMORY.md",
)

# The three sentences of the seam discipline, verbatim from BOOTSTRAP.md
# section 6. Every package under clockspeed/ restates them at the module they
# govern, because a subagent editing one module does not read the root
# architecture doc.
SEAM_SENTENCES: tuple[str, ...] = (
    "solve/ never reads a save.",
    "advisor/ never reads the raw docs file.",
    "surface/ never computes.",
)
SEAM_MARKER = "SEAM DISCIPLINE"

# ---------------------------------------------------------------------------
# Thresholds, named so the assertions read as intent rather than as magic
# ---------------------------------------------------------------------------

_MAX_ASCII = 0x7E
_MIN_AUTHORED_TEXT_FILES = 20
_MIN_HOLDER_CHARS = 2


# ===========================================================================
# a. Module topology
# ===========================================================================


@pytest.mark.parametrize("relative_path", PACKAGE_TOPOLOGY)
def test_topology_directory_is_an_importable_package(repo_root: Path, relative_path: str) -> None:
    """Each section 6 package directory exists and imports as a real package.

    Importing is the load-bearing half. A directory with no __init__.py still
    imports on python 3 as a namespace package, resolves attributes, and looks
    fine right up to the point where packaging or a mypy run disagrees. The
    __file__ assertion is what separates the two: a namespace package has
    __file__ set to None.

    Args:
        repo_root: Repository root.
        relative_path: Package directory relative to the root.
    """
    directory = repo_root / relative_path
    assert directory.is_dir(), f"missing package directory: {relative_path}"

    init_file = directory / "__init__.py"
    assert init_file.is_file(), f"missing {relative_path}/__init__.py"

    dotted = relative_path.replace("/", ".")
    module = importlib.import_module(dotted)

    assert module.__file__ is not None, f"{dotted} imported as a namespace package, not a package"
    assert Path(module.__file__).name == "__init__.py"
    assert module.__doc__, f"{dotted} has no module docstring"
    assert module.__doc__.strip().splitlines()[0].strip(), f"{dotted} docstring starts blank"


@pytest.mark.parametrize("relative_path", REQUIRED_DIRECTORIES)
def test_required_repo_directory_exists(repo_root: Path, relative_path: str) -> None:
    """Each non-package directory phase 0 requires exists and is not empty.

    Emptiness matters because git does not track empty directories: a
    directory that exists locally but holds nothing does not survive a clean
    clone, and the clean-clone case is the one the bootstrap order in
    CONVENTIONS.md section 1 is written for.

    Args:
        repo_root: Repository root.
        relative_path: Directory relative to the root.
    """
    directory = repo_root / relative_path
    assert directory.is_dir(), f"missing directory required by phase 0: {relative_path}"
    assert any(directory.iterdir()), f"{relative_path} exists but is empty, so it will not clone"


@pytest.mark.parametrize("relative_path", CLOCKSPEED_PACKAGES)
def test_package_states_the_seam_discipline(repo_root: Path, relative_path: str) -> None:
    """Every package under clockspeed/ carries the seam discipline at its own module.

    BOOTSTRAP.md section 6 states it once. Restating it in each package is the
    one place restatement is correct: this is a rule ABOUT the module, and the
    agent about to violate it is reading that module, not the architecture
    doc. The wording is asserted verbatim so a paraphrase that softens it -
    "solve/ should not read a save" - turns the suite red.

    Args:
        repo_root: Repository root.
        relative_path: Package directory relative to the root.
    """
    source = (repo_root / relative_path / "__init__.py").read_text(encoding="ascii")

    assert SEAM_MARKER in source, f"{relative_path}/__init__.py does not mark the seam discipline"
    for sentence in SEAM_SENTENCES:
        assert sentence in source, f"{relative_path}/__init__.py is missing: {sentence!r}"


# ===========================================================================
# b. Documentation ownership table
# ===========================================================================


@pytest.mark.parametrize("relative_path", DOC_OWNERSHIP_FILES)
def test_doc_ownership_file_exists(repo_root: Path, relative_path: str) -> None:
    """Every owner file in the CONVENTIONS.md section 2 table exists and has content.

    Non-empty, not merely present: an empty owner file is worse than a missing
    one because it looks like the fact has a home while every reader still has
    to restate it elsewhere.

    Args:
        repo_root: Repository root.
        relative_path: Document path relative to the root.
    """
    document = repo_root / relative_path
    assert document.is_file(), (
        f"the documentation-ownership table names {relative_path}, which is absent"
    )
    assert document.stat().st_size > 0, f"{relative_path} exists but is empty"


# ===========================================================================
# c. Character set - the byte-level gate
# ===========================================================================


def _first_non_ascii(path: Path) -> str | None:
    """Describe the first non-ASCII character in a file, or None if there is none.

    Reads BYTES. A text-mode read would decode the file and hide exactly the
    thing being looked for.

    Args:
        path: File to scan.

    Returns:
        A human-readable location and codepoint, or None if the file is clean.
        The description is itself pure ASCII - it names the codepoint and its
        Unicode name rather than echoing the offending character, so a failure
        report cannot become a second violation.
    """
    data = path.read_bytes()
    offset = next((index for index, byte in enumerate(data) if byte > _MAX_ASCII), None)
    if offset is None:
        return None

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        line = data[:offset].count(b"\n") + 1
        return (
            f"line {line} (byte offset {offset}): raw byte 0x{data[offset]:02X}; "
            f"the file is not valid UTF-8 either"
        )

    position = next(index for index, char in enumerate(text) if ord(char) > _MAX_ASCII)
    head = text[:position]
    line = head.count("\n") + 1
    column = position - (head.rfind("\n") + 1) + 1
    char = text[position]
    name = unicodedata.name(char, "UNNAMED CONTROL OR PRIVATE-USE CHARACTER")
    return f"line {line} column {column}: U+{ord(char):04X} {name}"


def test_authored_text_inventory_is_populated(
    repo_root: Path, authored_text_files: list[Path]
) -> None:
    """The character-set scan has something to scan.

    Paired with the scan itself (CONVENTIONS.md section 7.2). A scan over an
    empty list passes, reports nothing, and proves nothing - that is the
    "unrun gate" failure class wearing a green tick. This test pins the
    inventory down positively: it must contain the specific files this slice
    authored, so a collection bug is visible rather than silent.

    Args:
        repo_root: Repository root.
        authored_text_files: The inventory under test.
    """
    names = {path.relative_to(repo_root).as_posix() for path in authored_text_files}

    for required in (
        ".gitignore",
        "pyproject.toml",
        "clockspeed/__init__.py",
        "tests/conftest.py",
        "tests/test_scaffold.py",
    ):
        assert required in names, f"authored-text inventory did not collect {required}"

    assert len(names) >= _MIN_AUTHORED_TEXT_FILES, (
        f"authored-text inventory holds only {len(names)} files, which is too few to be "
        f"the real repository - suspect the collection, not the repository"
    )


def test_fallback_inventory_does_not_confuse_the_data_package_with_generated_data(
    repo_root: Path,
) -> None:
    """The git-less fallback walk keeps clockspeed/data/ and drops the caches.

    /data/ in .gitignore is anchored to the repo root precisely so it cannot
    touch the clockspeed/data/ SOURCE package. The fallback inventory has to
    honour the same anchoring, and a name-only skip list silently did not: it
    dropped the entire data layer from every scan while leaving the suite
    green, because a scan that skips a file reports no violation in it.

    Both halves are asserted (CONVENTIONS.md section 7.2): the source package
    IS collected, and the git metadata directory is NOT.

    Args:
        repo_root: Repository root.
    """
    names = {path.relative_to(repo_root).as_posix() for path in walk_inventory(repo_root)}

    assert "clockspeed/data/__init__.py" in names, (
        "the fallback walk dropped the data layer, most likely by skipping every "
        "directory named 'data' instead of only the one at the repo root"
    )
    assert "clockspeed/save/__init__.py" in names
    assert not any(name.startswith(".git/") for name in names), (
        "the fallback walk descended into .git"
    )


def test_authored_text_files_are_seven_bit_ascii(
    repo_root: Path, authored_text_files: list[Path]
) -> None:
    """Every authored text file is pure 7-bit ASCII, asserted on the raw bytes.

    BOOTSTRAP.md section 12 item 4 and CONVENTIONS.md section 10. The rule
    covers code, comments, docstrings, markdown, shell scripts and config -
    everything a human typed - which is why the inventory is "not binary"
    rather than "has a source extension".

    Args:
        repo_root: Repository root.
        authored_text_files: Files to scan.
    """
    violations: list[str] = []
    for path in authored_text_files:
        detail = _first_non_ascii(path)
        if detail is not None:
            violations.append(f"{path.relative_to(repo_root).as_posix()}: {detail}")

    assert not violations, "non-ASCII bytes in authored text (7-bit ASCII is required):\n  " + (
        "\n  ".join(violations)
    )


# ===========================================================================
# d. LICENSE
# ===========================================================================

# "Copyright (c) <year(s)> <holder>". The holder group is greedy and may be
# empty, which is the point: an empty holder is the bare-year failure.
_COPYRIGHT_LINE = re.compile(
    r"copyright\s*(?:\(c\))?\s*(?P<years>[0-9]{4}(?:\s*[-,]\s*[0-9]{4})*)\s*(?P<holder>.*)$",
    re.IGNORECASE,
)

# Template residue. An unrendered license template is the trap: both files
# "agree on MIT" and an SPDX grep passes while the grant names nobody
# (CONVENTIONS.md section 14 trap 3).
_PLACEHOLDER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("an unrendered template variable", re.compile(r"\{\{.*?\}\}")),
    ("an angle-bracket placeholder", re.compile(r"<[^>]*>")),
    ("a square-bracket placeholder", re.compile(r"\[[^\]]*\]")),
    ("the words 'your name'", re.compile(r"\byour\s*name\b", re.IGNORECASE)),
    ("the word 'fullname'", re.compile(r"\bfull\s*name\b", re.IGNORECASE)),
    ("the word 'organization'", re.compile(r"\borgani[sz]ation\b", re.IGNORECASE)),
    ("the words 'copyright holder'", re.compile(r"\bcopyright\s+holders?\b", re.IGNORECASE)),
    ("the words 'name of author'", re.compile(r"\bname\s+of\s+(?:the\s+)?author\b", re.IGNORECASE)),
    ("an unresolved marker", re.compile(r"\bTODO\b|\bTBD\b|\bXXX+\b")),
)


def test_license_names_a_real_copyright_holder(repo_root: Path) -> None:
    """LICENSE exists and its copyright line names somebody.

    CONVENTIONS.md section 14 trap 3: read the copyright LINE, not just the
    license name. A grant with no grantor grants nothing, and the two cheap
    checks that would catch a wrong license - an SPDX grep and a filename
    check - both pass on an unrendered template.

    Args:
        repo_root: Repository root.
    """
    license_file = repo_root / "LICENSE"
    assert license_file.is_file(), "LICENSE is absent"
    assert license_file.stat().st_size > 0, "LICENSE is empty"

    text = license_file.read_text(encoding="ascii")

    copyright_lines = [line for line in text.splitlines() if "copyright" in line.lower()]
    assert copyright_lines, "LICENSE contains no copyright line at all"

    match = None
    for line in copyright_lines:
        match = _COPYRIGHT_LINE.search(line)
        if match is not None:
            break
    assert match is not None, (
        "no copyright line matched 'Copyright (c) <year> <holder>'; "
        f"lines found: {copyright_lines!r}"
    )

    holder = match.group("holder").strip().strip(".,")
    assert holder, (
        "LICENSE has a bare copyright year with no holder - a grant with no grantor "
        "(CONVENTIONS.md section 14 trap 3)"
    )
    assert len(holder) >= _MIN_HOLDER_CHARS, (
        f"copyright holder {holder!r} is too short to be a name"
    )
    assert any(char.isalpha() for char in holder), (
        f"copyright holder {holder!r} contains no letters"
    )

    for description, pattern in _PLACEHOLDER_PATTERNS:
        assert not pattern.search(holder), (
            f"copyright holder {holder!r} looks like an unrendered template: "
            f"it contains {description}"
        )


def test_license_body_is_complete(repo_root: Path) -> None:
    """The LICENSE body is the whole license, not a truncated one.

    CONVENTIONS.md section 14 trap 4: a truncated license - the warranty
    clause missing - is not the license it claims to be. Positive assertions
    on the three load-bearing clauses, paired with the holder check above.

    Args:
        repo_root: Repository root.
    """
    text = (repo_root / "LICENSE").read_text(encoding="ascii")

    for clause in (
        "Permission is hereby granted, free of charge",
        "The above copyright notice and this permission notice shall be included",
        "WITHOUT WARRANTY OF ANY KIND",
    ):
        assert clause in text, f"LICENSE is missing a load-bearing clause: {clause!r}"


# ===========================================================================
# e. .gitignore
# ===========================================================================

# Each entry is (what class it protects, a regex matched against declared
# patterns). Matched against the pattern LINES rather than the whole file so a
# mention inside a comment cannot satisfy the assertion.
_REQUIRED_IGNORE_CLASSES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "save files - a .sav embeds a platform account id and the player display name "
        "in plaintext (BOOTSTRAP.md section 2.2)",
        re.compile(r"(^|/)\*\.sav$"),
    ),
    (
        "the generated data directory - BOOTSTRAP.md section 6 marks data/ GITIGNORED",
        re.compile(r"^/?data/$"),
    ),
    (
        "local configuration - per-machine wiring that names interpreters, home paths "
        "and account directories (CONVENTIONS.md section 10)",
        re.compile(r"^(\.env|\.env\..*|\.mcp\.json|.*\.local\.json|.*/local\.json)$"),
    ),
)


def _gitignore_patterns(repo_root: Path) -> list[str]:
    """Return the declared, non-comment patterns from .gitignore.

    Args:
        repo_root: Repository root.

    Returns:
        Stripped pattern lines with comments and blanks removed.
    """
    text = (repo_root / ".gitignore").read_text(encoding="ascii")
    lines = (line.strip() for line in text.splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def test_gitignore_declares_the_dangerous_classes(repo_root: Path) -> None:
    """.gitignore exists and declares a pattern for each dangerous class.

    The three classes are not interchangeable and each is excluded for a
    different reason: publisher-owned content, personal data, and machine
    drift. A .gitignore missing any one of them is a leak waiting for its
    first commit, and git history is the part that cannot be un-leaked.

    Args:
        repo_root: Repository root.
    """
    gitignore = repo_root / ".gitignore"
    assert gitignore.is_file(), ".gitignore is absent"

    patterns = _gitignore_patterns(repo_root)
    assert patterns, ".gitignore exists but declares no patterns"

    for description, pattern in _REQUIRED_IGNORE_CLASSES:
        assert any(pattern.match(line) for line in patterns), (
            f".gitignore declares no pattern covering {description}"
        )


def test_gitignore_behaves_as_declared(repo_root: Path, git_available: bool) -> None:
    """Git itself agrees about what is ignored AND about what is not.

    Declared patterns are a claim; git's answer is the behaviour. The
    not-ignored half is the pairing required by CONVENTIONS.md section 7.2 and
    it is not decoration: /data/ is anchored precisely so it cannot swallow
    the clockspeed/data/ SOURCE package, and a wider pattern would silently
    untrack the data layer while every "is it ignored" assertion stayed green.

    Args:
        repo_root: Repository root.
        git_available: Whether git can answer.
    """
    if not git_available:
        pytest.skip("git is not available, so its ignore behaviour cannot be probed")

    must_be_ignored = (
        "data/registry.json",
        "example_world_autosave_0.sav",
        ".env",
        ".mcp.json",
        # CS-1161. BOTH halves of the note channel, never just the inbox. The
        # inbox was ignored and the outbox was not, which left the half this
        # tree AUTHORS as the unprotected one - and `git status` reported
        # `?? moon_sync_outbox/` with three delivered notes in it. Phase 7 is a
        # public flip, so correspondence reaching a commit is not a tidiness
        # fault.
        #
        # --no-index IS LOAD-BEARING HERE, and so is the trailing slash. A
        # directory-only rule cannot match a path git cannot see is a
        # directory, so without the slash the answer comes from the filesystem
        # rather than from the rules and the arm reports on whichever checkout
        # runs it - green in the primary, red in a worktree. Asking about a
        # path that need not exist is the whole point: it grades the RULE.
        "moon_sync_inbox/",
        "moon_sync_outbox/",
    )
    must_not_be_ignored = (
        "pyproject.toml",
        ".gitignore",
        "docs/LEDGER.md",
        "clockspeed/data/registry.py",
        "tests/test_scaffold.py",
    )

    wrong: list[str] = []
    for candidate in must_be_ignored:
        proc = run_git(repo_root, "check-ignore", "--no-index", "-q", candidate)
        assert proc is not None, "git disappeared mid-test"
        if proc.returncode != 0:
            wrong.append(f"{candidate} is NOT ignored but must be")
    for candidate in must_not_be_ignored:
        proc = run_git(repo_root, "check-ignore", "--no-index", "-q", candidate)
        assert proc is not None, "git disappeared mid-test"
        if proc.returncode == 0:
            wrong.append(f"{candidate} IS ignored but must stay tracked")

    assert not wrong, ".gitignore behaviour disagrees with its intent:\n  " + "\n  ".join(wrong)


# ===========================================================================
# f. Absolute home paths
# ===========================================================================

# Built from fragments on purpose. A literal example of the thing being
# searched for would make this file match its own pattern, and would also put
# an account name into a tracked file - the exact violation under test.
_ACCOUNT = r"[A-Za-z0-9._-]{1,64}"
_HOME_PATH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "windows user profile",
        re.compile(
            r"(?P<root>[A-Za-z]:[\\/]{1,2}" + "Users" + r"[\\/]{1,2})(?P<account>" + _ACCOUNT + ")"
        ),
    ),
    (
        "linux home",
        re.compile(r"(?<![\w.-])(?P<root>/" + "home" + r"/)(?P<account>" + _ACCOUNT + ")"),
    ),
    (
        "macos home",
        re.compile(r"(?<![\w.-])(?P<root>/" + "Users" + r"/)(?P<account>" + _ACCOUNT + ")"),
    ),
)


def _find_home_path(line: str) -> str | None:
    """Describe an absolute home path in ``line``, with the account name redacted.

    The account name is personal data (BOOTSTRAP.md section 2.2). A failure
    message that quoted it would print it into CI logs and session
    transcripts, so only the shape is reported.

    Args:
        line: One line of an authored file.

    Returns:
        A redacted description, or None if the line is clean.
    """
    for description, pattern in _HOME_PATH_PATTERNS:
        match = pattern.search(line)
        if match is not None:
            account_length = len(match.group("account"))
            return (
                f"{description}: {match.group('root')}"
                f"<redacted account name, {account_length} characters>"
            )
    return None


def test_home_path_detector_actually_detects() -> None:
    """The home-path patterns match real home paths and do not match innocent ones.

    An empty grep is a claim about your PATTERN, not about the codebase
    (CONVENTIONS.md section 15.1). Without this, a typo in the regex above
    would turn the scan below into a permanently green no-op. Samples are
    assembled from fragments so this file stays clean of the literal it hunts.
    """
    sep = "\\"
    positives = (
        "C:" + sep + "Users" + sep + "someone" + sep + "AppData",
        "C:/" + "Users" + "/someone/AppData",
        "/" + "home" + "/someone/.config",
        "/" + "Users" + "/someone/Library",
    )
    negatives = (
        "C:" + sep + "Clockspeed" + sep + "clockspeed",
        "C:" + sep + "Program Files",
        "/usr/local/bin",
        "%LOCALAPPDATA%" + sep + "SomeApp" + sep + "Saved",
        "the users directory",
    )

    for sample in positives:
        assert _find_home_path(sample) is not None, f"detector missed a home path: {sample!r}"
    for sample in negatives:
        assert _find_home_path(sample) is None, f"detector false-positived on: {sample!r}"


def test_no_absolute_home_paths_in_authored_files(
    repo_root: Path, authored_text_files: list[Path]
) -> None:
    """No authored file hardcodes an absolute path under a user home directory.

    BOOTSTRAP.md section 12 item 3 and CONVENTIONS.md section 10: never
    hardcode a machine name, a user account id, or an absolute home path into
    a tracked file. Two harms, not one - it is personal data, and it is drift,
    because the path is wrong on every other machine including a clean CI
    checkout. Auto-detect at runtime instead.

    Args:
        repo_root: Repository root.
        authored_text_files: Files to scan.
    """
    violations: list[str] = []
    for path in authored_text_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            found = _find_home_path(line)
            if found is not None:
                violations.append(f"{path.relative_to(repo_root).as_posix()}:{number}: {found}")

    assert not violations, (
        "absolute home paths in authored files (auto-detect these at runtime instead):\n  "
        + "\n  ".join(violations)
    )


# ===========================================================================
# Configuration: the version and the test-harness safety controls
# ===========================================================================


def _pyproject(repo_root: Path) -> dict[str, Any]:
    """Parse pyproject.toml.

    Args:
        repo_root: Repository root.

    Returns:
        The parsed document.
    """
    return tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="ascii"))


def test_version_exists_in_exactly_one_place(repo_root: Path) -> None:
    """The project version is single-sourced from clockspeed.__version__.

    CONVENTIONS.md section 2: do not restate a measured fact - a restated
    number is a number that will drift. This asserts the wiring in both
    directions, so neither a second literal in pyproject.toml nor a rename of
    the attribute can pass unnoticed.

    Args:
        repo_root: Repository root.
    """
    document = _pyproject(repo_root)
    project = document["project"]

    assert "version" in project.get("dynamic", []), (
        "pyproject.toml must declare the version dynamic so it is read from the package"
    )
    assert "version" not in project, (
        "pyproject.toml declares a second version literal; the version lives in "
        "clockspeed/__init__.py and nowhere else"
    )

    setuptools_config = document["tool"]["setuptools"]
    assert setuptools_config["dynamic"] == {"version": {"attr": "clockspeed.__version__"}}

    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+([.+-][0-9A-Za-z.]+)?", clockspeed.__version__), (
        f"clockspeed.__version__ is not a recognisable version: {clockspeed.__version__!r}"
    )


def test_pytest_configuration_cannot_sweep_runtime_state(repo_root: Path) -> None:
    """Collection is pinned to tests/ and the fast-subset marker is declared.

    CONVENTIONS.md section 7.1: never a bare recursive invocation from the
    root - it can sweep runtime state directories and destroy live locks or
    data. This repository will hold /data/, /work/ (save copies), /run/ and
    /logs/ at the root, so an unpinned testpaths is a real hazard rather than
    a tidiness preference.

    The "slow" marker is what lets the pre-push hook select a fast subset
    (CONVENTIONS.md section 8, tier 0), and --strict-markers is what stops a
    typo in that marker from silently selecting nothing.

    Args:
        repo_root: Repository root.
    """
    pytest_config = _pyproject(repo_root)["tool"]["pytest"]["ini_options"]

    assert pytest_config["testpaths"] == ["tests"], (
        "testpaths must pin collection to tests/ so a bare pytest cannot walk runtime state"
    )

    markers = pytest_config["markers"]
    assert any(str(entry).split(":")[0].strip() == "slow" for entry in markers), (
        "a 'slow' marker must be registered so the pre-push hook can select a fast subset"
    )

    addopts = str(pytest_config["addopts"])
    assert "--strict-markers" in addopts, "an unregistered marker must be an error, not a shrug"


def test_ruff_selects_the_character_set_rules(repo_root: Path) -> None:
    """The ruff selection includes the rule families that police non-ASCII source.

    Ruff has no "reject every byte above 0x7E" rule, so the constraint is
    covered by PLC2401 and PLC2403 (non-ASCII names and import names) plus
    RUF001, RUF002 and RUF003 (ambiguous Unicode in strings, docstrings and
    comments - the family that catches em-dashes, en-dashes and smart quotes).
    Those arrive through the PL and RUF selectors. This test exists so nobody
    narrows either selector without the suite objecting, since the byte-level
    test above would still pass on a repository whose linter had gone quiet.

    Args:
        repo_root: Repository root.
    """
    ruff_config = _pyproject(repo_root)["tool"]["ruff"]
    selected = {str(code) for code in ruff_config["lint"]["select"]}

    for family in ("PL", "RUF"):
        assert any(code.startswith(family) for code in selected), (
            f"ruff must select the {family} family: it carries the non-ASCII source rules"
        )

    assert "F" in selected, "ruff must select pyflakes (F): undefined names are real bugs"
    assert ruff_config["line-length"] > 0, "ruff must enforce a line length"
