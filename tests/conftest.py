"""Shared fixtures for the Clockspeed test suite, and one suite-wide hook.

Dependency-free by design: standard library plus pytest, nothing else. The
rule suite has to run on a clean machine with no game installed
(BOOTSTRAP.md section 5.4), and a fixture that needs a package installed is a
fixture that does not run there.

Nothing here resolves a path from a literal. The repo root is derived from
this file's own location, and the file inventory is derived from git. An
absolute path under a user home directory in a tracked file is forbidden
outright (CONVENTIONS.md section 10, BOOTSTRAP.md section 12 item 3), and
tests/test_scaffold.py asserts the absence of one across the whole tree - a
harness that hardcoded one would be asserting against itself.

THE HOOKS AT THE BOTTOM ARE HERE AND NOT IN A TEST MODULE, and that placement
is the whole shape of CS-428. pytest renders the failing frame's ARGUMENTS by
default, so every test taking ``tmp_path`` or a fixture derived from it prints
its base temporary directory when it fails, across most test modules in the
tree. NO COUNT IS WRITTEN HERE, DELIBERATELY: the figure this sentence first
carried was restated from a roadmap note, was already wrong when it was
written, and drifts every time a test is added - CLAUDE.md section 4. A
per-module fix would be one edit per module that the next module escapes;
this is a property of the harness, so the harness is where it is fixed. The
grading for it lives in tests/test_tmp_path_privacy.py, which runs real pytest subprocesses
and scans their real output, because the subject is what pytest prints rather than what
any function returns - and, for the one property no subprocess can observe, runs a
repointing failure and its victim inside a single session.

WHAT THIS REDACTOR COVERS, AND WHAT IT DELIBERATELY DOES NOT. Two of the four
personal-data classes CLAUDE.md names are COVERED here - a home path and the
account name - and two are REGISTERED AND UNCOVERED: the platform account id
and the world name. The uncovered pair is declared in ``UNCOVERED_CLASSES``
below with a reason each, and the grading module checks the declaration rather
than reading it. Registering them beats dropping them: a dropped class is a
silence, and a stated exemption is a fact the next reader can check.

WHY THEY ARE UNCOVERED - THE DURABLE DESIGN FINDING, not a scheduling note.
CS-860 covered both with SHAPE rules built on a path-segment character class
borrowed from clockspeed/data/locate.py. That class is CORRECT where it was
borrowed from, because ``locate.redact`` receives PATHS. This module's
``redact_personal_data`` receives WHOLE FAILURE REPORTS, which are arbitrary
prose, and a path-segment class is destructive on arbitrary text in BOTH
directions at once. Measured on the shipped rules, not predicted:

  - TOO NARROW. The class excluded whitespace and both quote characters, so the
    world-name rule ate only the run after the last space. ``Some Save
    Name.sav`` rendered as ``Some Save <redacted-save>`` - the world name it
    existed to hide, still standing.

  - TOO GREEDY. The class admitted brackets, commas and colons and was
    unanchored, so it swallowed across delimiters.
    ``workdir.py:120: in copy_for_read(World.sav)`` rendered as
    ``workdir.py:120: in <redacted-save>)``, ERASING A FUNCTION NAME FROM A
    TRACEBACK FRAME LINE.

THE TWO ENDS ARE ONE KNOB AND CANNOT BE FIXED INDEPENDENTLY: widening the class
to reach the narrow case worsens the greedy case by exactly the same edit. So
the rules came out rather than being tuned, and the classes stayed registered.
A rule for either needs a mechanism that does not assume its input is a path -
that is what CS-860 still owes, and it is why this file's surviving rules are
all LITERAL spellings of values this machine already holds. A literal cannot
over-reach: it rewrites the exact bytes it was built from and nothing else.
"""

from __future__ import annotations

import contextlib
import getpass
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol
from urllib.parse import quote

import pytest

# ---------------------------------------------------------------------------
# File inventory
# ---------------------------------------------------------------------------

# Directories the fallback walk never descends into. These lists are ONLY used
# when git is unavailable; the git path gets the real answer from .gitignore.
# Kept in sync with .gitignore by intent, not by machine - if the two disagree,
# .gitignore wins and these lists are what is wrong.
#
# The split between "at any depth" and "at the root only" is load-bearing and
# mirrors the leading slash in .gitignore. /data/ is the gitignored generated
# artifact directory; clockspeed/data/ is the SOURCE package for the data
# layer. A name-only skip would silently drop the entire data layer from every
# scan below, which is the same bug the anchored pattern in .gitignore exists
# to prevent. The same reasoning covers work/, run/, logs/ and the rest.
_SKIP_DIR_NAMES_ANYWHERE = frozenset(
    {
        ".git",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".recall",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "htmlcov",
        "node_modules",
        "venv",
    }
)
_SKIP_DIR_NAMES_AT_ROOT = frozenset(
    {
        "build",
        "captures",
        "certs",
        "corpus",
        "data",
        "dist",
        "gamedata",
        "logs",
        "moon_sync_inbox",
        "run",
        "screenshots",
        "var",
        "work",
    }
)

# Suffixes that are legitimately not 7-bit ASCII because they are not text.
# This is a DENY list rather than an allow list on purpose: an unrecognised
# extension is treated as authored text and therefore gets scanned. That
# direction fails loudly on a new file type and is corrected by adding it here
# deliberately. An allow list would silently stop scanning whatever it did not
# know about, which is the failure mode that matters.
_BINARY_SUFFIXES = frozenset(
    {
        ".bin",
        ".bmp",
        ".dat",
        ".der",
        ".dll",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".icns",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".pfx",
        ".png",
        ".pyc",
        ".pyd",
        ".sav",
        ".so",
        ".ttf",
        ".usmap",
        ".webp",
        ".woff",
        ".woff2",
        ".zip",
    }
)

_SNIFF_BYTES = 8192


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    """Run a git subcommand in ``root``: None when git is missing, RED when it cannot run.

    Public because test modules import it: git alone answers "would this path be
    committed" and "is this path ignored". PATH resolves the program (CONVENTIONS.md 10).

    A HANG OR A START FAULT IS RED, NEVER A SKIP (CS-1116, CS-1118, CS-1120). Callers skip
    on None, so only a program no PATH lookup resolves returns it; one that resolves and
    still raises ``FileNotFoundError`` (a missing #! interpreter) FAILS, as do a hang and a
    directory or data file, named by error field and never the object, which carries the
    path. A non-zero exit is returned for the caller to judge. tests/test_conftest_run_git.py.
    """
    proc: subprocess.CompletedProcess[bytes] | None = None
    try:
        proc = subprocess.run(
            [*RUN_GIT_PROGRAM, "-C", str(root), *args],
            capture_output=True,
            timeout=RUN_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:  # failed BELOW the handler, so the red chains nothing
        fault = f"TIMED OUT after {RUN_GIT_TIMEOUT_SECONDS}s"
    except OSError as error:  # CS-1120 - not found AND unresolvable is the only "no git"
        if isinstance(error, FileNotFoundError) and shutil.which(RUN_GIT_PROGRAM[0]) is None:
            return None
        fault = f"could not START ({type(error).__name__}, errno {error.errno})"
    if proc is None:
        pytest.fail(f"git {args[0] if args else '(no subcommand)'} {fault} - never a skip")
    return proc


def _git_inventory(root: Path) -> list[Path] | None:
    """List every file git tracks or WOULD track in ``root``.

    ``--cached`` covers tracked files and ``--others --exclude-standard``
    covers untracked files that .gitignore does not exclude. Together they are
    the set that a commit would capture, which is the correct set for a
    hygiene assertion: a file that is about to be committed is exactly as
    dangerous as one already committed.

    Args:
        root: Repository root.

    Returns:
        Absolute paths, or None if git could not answer.
    """
    proc = run_git(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "--full-name",
        "-z",
    )
    if proc is None or proc.returncode != 0:
        return None
    names = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    return [root / name for name in names if name]


def walk_inventory(root: Path) -> list[Path]:
    """List candidate files by walking the tree, skipping known noise.

    Public because tests/test_scaffold.py pins its directory-skip logic: the
    root-anchored half of that logic is what keeps the clockspeed/data/
    source package out of the gitignored /data/ bucket.

    The fallback for a checkout with no usable git. Less accurate than
    :func:`_git_inventory` because it approximates .gitignore rather than
    reading it, so it is deliberately the second choice.

    Args:
        root: Repository root.

    Returns:
        Absolute paths.
    """
    found: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        for entry in sorted(directory.iterdir()):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                at_root = entry.parent == root
                skipped = entry.name in _SKIP_DIR_NAMES_ANYWHERE or (
                    at_root and entry.name in _SKIP_DIR_NAMES_AT_ROOT
                )
                if not skipped:
                    stack.append(entry)
            elif entry.is_file():
                found.append(entry)
    return found


def _looks_binary(path: Path) -> bool:
    """Report whether a file should be treated as binary rather than authored text.

    Two independent signals, because either alone is weak: a known binary
    suffix, and a NUL byte in the first block. A file with neither is treated
    as authored text.

    Args:
        path: File to classify.

    Returns:
        True if the file is binary.
    """
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return True
    try:
        with path.open("rb") as handle:
            return b"\0" in handle.read(_SNIFF_BYTES)
    except OSError:
        return True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root, resolved from this file's location.

    Never a literal. This file lives at ``<root>/tests/conftest.py``, so the
    root is two parents up. Resolving it this way means the suite runs from a
    worktree, a fresh clone, or a temporary checkout with no edit.

    Returns:
        The repository root.
    """
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def git_available(repo_root: Path) -> bool:
    """Report whether git can answer questions about this checkout.

    Args:
        repo_root: Repository root.

    Returns:
        True if git is on PATH and ``repo_root`` is inside a work tree.
    """
    proc = run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    return proc is not None and proc.returncode == 0


@pytest.fixture(scope="session")
def repo_files(repo_root: Path) -> list[Path]:
    """Every file that git tracks or would track, git being the authority.

    Falls back to a tree walk if git cannot answer, so the suite still runs in
    an exported tarball. The fallback approximates .gitignore and is therefore
    the weaker answer; it is never silently preferred.

    Args:
        repo_root: Repository root.

    Returns:
        Sorted absolute paths to existing files.
    """
    inventory = _git_inventory(repo_root)
    if inventory is None:
        inventory = walk_inventory(repo_root)
    return sorted(path for path in inventory if path.is_file())


@pytest.fixture(scope="session")
def authored_text_files(repo_files: list[Path]) -> list[Path]:
    """The authored text subset of the repository: what the character-set rule governs.

    Authored text is every tracked-or-would-be-tracked file that is not
    binary. Markdown, Python, TOML, JSON, YAML, shell hooks, extensionless
    scripts and anything else a human typed all qualify. The 7-bit ASCII rule
    covers all of it, not just source code (BOOTSTRAP.md section 12 item 4).

    Args:
        repo_files: Full file inventory.

    Returns:
        Sorted absolute paths.
    """
    return [path for path in repo_files if not _looks_binary(path)]


# ---------------------------------------------------------------------------
# CS-428 - personal data never reaches a rendered failure report
# ---------------------------------------------------------------------------

#: What a redacted home directory renders as. Owned here, imported by
#: tests/test_tmp_path_privacy.py rather than restated there.
REDACTED_HOME = "<redacted-home>"

#: What a redacted account name renders as.
REDACTED_USER = "<redacted-user>"

#: CS-1156. What a credential is replaced by. A DISTINCT placeholder rather
#: than reusing one above, because a reader who sees it must be able to tell
#: that a secret was removed here and not a home path - the two carry different
#: consequences and a shared token would flatten them.
REDACTED_CREDENTIAL = "<redacted-credential>"

#: THE FOUR PERSONAL-DATA CLASSES CLAUDE.md NAMES, one id each, and every rule
#: below is TAGGED with the one it serves. These ids are not the definition of
#: what gets redacted - CLAUDE.md is. tests/test_report_redaction_classes.py
#: reads the two sentences in that file which name personal data, in section 2
#: and in non-negotiable 3, and goes RED on any class either sentence demands
#: that no id here claims, on any id no sentence claims, on any id that is
#: declared neither covered nor uncovered, on any COVERED id whose own tagged
#: rules do not demonstrably rewrite a planted string of that class, on any
#: UNCOVERED id that some rule serves anyway, and on any id with no named arm.
#: So the SET is derived, only the mapping is authored, and COVERAGE IS
#: MEASURED RATHER THAN DECLARED.
CLASS_HOME_PATH = "home-path"
CLASS_ACCOUNT_NAME = "account-name"
CLASS_ACCOUNT_ID = "account-id"
CLASS_WORLD_NAME = "world-name"

#: The classes this rule set actually SERVES. Membership is a claim the grading
#: module CHECKS BEHAVIOURALLY - a class listed here whose own tagged rules
#: rewrite nothing is a RED rather than a comment, which is what stops a rule
#: from being registered hollow or from carrying another class's tag.
COVERED_CLASSES: frozenset[str] = frozenset({CLASS_HOME_PATH, CLASS_ACCOUNT_NAME})

#: The classes this rule set deliberately does NOT serve, each with its reason.
#: REGISTERED RATHER THAN DROPPED - see this module's docstring for the
#: measurement. The grading module asserts that NO rule is tagged with any of
#: these and that each planted probe of these classes passes through UNCHANGED,
#: so a rule creeping back without its class moving to :data:`COVERED_CLASSES`
#: is a RED, and so is an uncovered class quietly claiming coverage.
UNCOVERED_CLASSES: Mapping[str, str] = MappingProxyType(
    {
        CLASS_ACCOUNT_ID: (
            "CS-860's positional rule was built on a path-segment character "
            "class borrowed from clockspeed/data/locate.py, where it is "
            "correct because that redactor receives PATHS. Against the "
            "arbitrary prose of a failure report the same class was measured "
            "both too narrow and too greedy at once, and the two ends are one "
            "knob. Backed out rather than tuned; a replacement needs a "
            "mechanism that does not assume its input is a path."
        ),
        CLASS_WORLD_NAME: (
            "Same root cause and the same backout: the suffix-anchored rule "
            "inherited that segment class, so it leaked a world name "
            "containing a space and erased a function name from a traceback "
            "frame line. A BARE world name is separately out of reach - it is "
            "operator-authored free text derivable from nothing on this "
            "machine - and that half belongs to CS-850 and CS-851."
        ),
    }
)

#: Refuse to treat a one-component path as a home directory. ``C:\\`` and ``/``
#: are not personal data and redacting either would gut every report.
_MIN_HOME_PARTS = 2

#: Environment variables that name the logged-in account on some platform.
_ACCOUNT_VARIABLES = ("USERNAME", "USER", "LOGNAME")

#: One percent-escape, as a URL-quoted path spells a separator: ``%5C``, ``%2F``.
_PERCENT_ESCAPE = "%[0-9A-Fa-f]{2}"

#: What may sit either side of a bare account name. Not a word character, OR a
#: percent-escape - whose last character IS a word character, which is what
#: makes a plain boundary refuse to match inside a quoted path. Each lookaround
#: is individually fixed-width, which Python's lookbehind requires.
_NAME_LEFT_BOUNDARY = f"(?:(?<={_PERCENT_ESCAPE})|(?<![0-9A-Za-z_]))"
_NAME_RIGHT_BOUNDARY = f"(?:(?={_PERCENT_ESCAPE})|(?![0-9A-Za-z_]))"

#: One backslash. Named so the doubled home spelling below is PRODUCED by
#: calling ``str.replace`` on an already-derived root rather than written out a
#: second time by hand.
_BACKSLASH = "\\"

#: HOW A HOME PATH IS SPELLED IN A REPORT, expressed as TRANSFORMS rather than
#: as patterns. Each is APPLIED to the roots already derived, so no transform
#: can introduce a spelling the frozen root set does not license, and none of
#: them reads the environment, touches the filesystem, or caches anything.
#:
#: THE DOUBLING IS THE ONE THAT WAS MISSING AND IT IS THE ONE THAT MATTERS.
#: ``OSError.__str__`` renders its ``filename`` through ``%r``, which doubles
#: every backslash, so the doubled spelling is what a chained cause actually
#: prints. MEASURED before CS-860: against the real home, the doubled spelling
#: and both URL-quoted spellings all missed the home rule and were caught only
#: by the weaker account-name rule - which holds on this machine solely because
#: the account name happens to be the only personal component of the home
#: prefix. That is a naming accident, not a control, and it does not transfer
#: to a CI runner or to another machine.
#:
#: DEPTH IS BOUNDED AT ONE ESCAPING LEVEL, stated rather than implied. A
#: quadrupled spelling - a repr of a repr - and the compositions, a quoted
#: doubled path or a doubled quoted path, are NOT covered by these transforms
#: and are a named residual rather than a claim.
_HOME_SPELLING_TRANSFORMS: tuple[Callable[[str], str], ...] = (
    lambda spelling: spelling,
    lambda spelling: spelling.replace(_BACKSLASH, _BACKSLASH * 2),
    quote,
)

#: Printed in place of a report the redaction could not process. Failing CLOSED
#: is the only safe direction here: a redactor that cannot read a report cannot
#: promise anything about what is in it, and printing it anyway would be the
#: leak this hook exists to stop. The exception TYPE is named and its message
#: is not - a message is an echo path (CLAUDE.md non-negotiable 12).
_REDACTION_FAILED = (
    "clockspeed: this failure report was WITHHELD because the personal-data "
    "redaction in tests/conftest.py raised {kind}. Nothing was suppressed on "
    "purpose - fix the redaction to see the report."
)


def _resolved(path: Path) -> Path:
    """Resolve ``path``, tolerating a filesystem that refuses.

    Resolution is what expands a Windows 8.3 short name, which is the reason
    this is not simply ``Path.home()`` everywhere: ``tempfile.gettempdir()``
    can hand back the short form of the profile directory while pytest stores
    the long form, and both spell the same personal data.

    Args:
        path: Path to resolve.

    Returns:
        The resolved path, or the original if the platform refused.
    """
    try:
        return path.resolve()
    except OSError:
        return path


def _home_like_roots() -> frozenset[Path]:
    """Every directory on this machine that IS the user profile, in any spelling.

    Two sources, and the second is not redundant. ``Path.home()`` gives the
    canonical spelling. ``tempfile.gettempdir()`` truncated to the profile's
    depth gives whatever spelling the temporary directory was configured with -
    on Windows that is routinely the 8.3 short form, which shares no substring
    with the long form past the profile's parent. A candidate is kept ONLY if
    it resolves to the same directory as the home, which is what stops this
    from claiming ``/tmp`` on a container whose home is ``/root``.

    Returns:
        Profile directories, each with at least two path components.
    """
    home = Path.home()
    resolved_home = _resolved(home)
    roots = {home, resolved_home}
    depth = len(resolved_home.parts)
    temp = Path(tempfile.gettempdir())
    for variant in (temp, _resolved(temp)):
        if len(variant.parts) < depth:
            continue
        candidate = Path(*variant.parts[:depth])
        if _resolved(candidate) == resolved_home:
            roots.add(candidate)
    return frozenset(root for root in roots if len(root.parts) >= _MIN_HOME_PARTS)


def _account_names(roots: frozenset[Path]) -> frozenset[str]:
    """Every spelling of the logged-in account name this machine can produce.

    The profile directory's own name is included because pytest builds its base
    temporary directory as ``pytest-of-<user>`` from ``getpass.getuser()``, and
    the two can differ - a renamed account keeps its old profile directory.
    Both spellings are personal data, so both are redacted.

    Args:
        roots: The profile directories from :func:`_home_like_roots`.

    Returns:
        Non-empty account name spellings.
    """
    names = {root.name for root in roots}
    with contextlib.suppress(OSError, KeyError):
        names.add(getpass.getuser())
    for variable in _ACCOUNT_VARIABLES:
        names.add(os.environ.get(variable, ""))
    return frozenset(name for name in names if name.strip())


def _build_redaction_rules() -> tuple[tuple[re.Pattern[str], str, str], ...]:
    """The substitutions, longest source first, each tagged with its class.

    TWO CLASSES ARE SERVED HERE AND FOUR ARE REGISTERED. A home path and the
    account name are COVERED; the platform account id and the world name are
    REGISTERED AND UNCOVERED, with a reason each in :data:`UNCOVERED_CLASSES`
    and the measurement behind them in this module's docstring. Nothing built
    here is tagged with an uncovered class, and
    tests/test_report_redaction_classes.py goes red the moment anything is.

    Order is load-bearing, and it is two deep.

      1. Whole profile paths, so a home directory is replaced as one unit, in
         every spelling :data:`_HOME_SPELLING_TRANSFORMS` produces.
      2. Bare account names LAST, so they only ever match what the home rules
         left standing - such as the ``pytest-of-<user>`` component.

    Account names match on boundaries rather than as bare substrings. That is a
    deliberate limit on the blast radius: without it an account named ``test``
    would rewrite every occurrence of that word in every traceback, and a
    report mangled past reading hides the next defect. With it, a short account
    name costs a few mangled words instead of the whole report.

    A PERCENT-ESCAPE COUNTS AS A BOUNDARY. In a URL-quoted path the separator
    is spelled ``%5C``, which ends in an alphanumeric, so a plain
    "not a word character" boundary refuses to match the name beside it and
    renders it in full.

    EVERY RULE IS A LITERAL SPELLING OF A VALUE THIS MACHINE ALREADY HOLDS, and
    that is the property the backed-out shape rules did not have. A literal
    cannot over-reach: it rewrites the exact bytes it was built from, so it is
    safe against arbitrary report prose in the way a character-class pattern is
    not.

    NOTHING HERE READS THE ENVIRONMENT OR THE FILESYSTEM BEYOND THE ONE
    ``_home_like_roots`` CALL IT ALWAYS MADE, and that property is why the home
    widening could be built on top of :func:`_seed_redaction_rules` without
    reopening the defect that refuted CS-428's first build. The widening is a
    PURE TRANSFORM of the already-derived root set - see
    :data:`_HOME_SPELLING_TRANSFORMS`. No new environment read, no new
    filesystem call, no cache, and no rebuild path.

    Returns:
        ``(pattern, replacement, class_id)`` triples, applied in order.
    """
    roots = _home_like_roots()
    spellings = {
        transform(spelling)
        for root in roots
        for spelling in (str(root), root.as_posix())
        for transform in _HOME_SPELLING_TRANSFORMS
    }
    rules: list[tuple[re.Pattern[str], str, str]] = [
        (re.compile(re.escape(spelling), re.IGNORECASE), REDACTED_HOME, CLASS_HOME_PATH)
        for spelling in sorted((s for s in spellings if s), key=len, reverse=True)
    ]
    rules.extend(
        (
            re.compile(
                rf"{_NAME_LEFT_BOUNDARY}{re.escape(name)}{_NAME_RIGHT_BOUNDARY}",
                re.IGNORECASE,
            ),
            REDACTED_USER,
            CLASS_ACCOUNT_NAME,
        )
        for name in sorted(_account_names(roots), key=len, reverse=True)
    )
    return tuple(rules)


def _seed_redaction_rules() -> tuple[tuple[re.Pattern[str], str, str], ...]:
    """Freeze the rule set NOW, before any test can move the environment.

    WHY THE TIMING IS THE WHOLE MECHANISM, and not an optimisation. The rules
    are derived from ``Path.home()``, which on Windows reads ``USERPROFILE``,
    and from the profile directory's own name. Several tests in this suite
    monkeypatch ``USERPROFILE`` at a ``tmp_path`` subdirectory and fail while
    the patch is live - so a rule set built ON DEMAND, at the first report that
    needs one, is built from whichever test got there first.

    That direction of failure is the dangerous one. A rule set derived from a
    repointed profile no longer contains the real profile's spellings, so the
    redaction stops redacting the thing it exists to redact for the rest of the
    session, while ALSO installing that directory's name as an account-name
    spelling and rewriting it wherever it appears in later reports. Seeding at
    import makes the rule set monotone by construction: it is computed at the
    earliest moment the module exists and there is no later path that rebuilds
    it, so it can neither shrink nor acquire a spelling from a patched
    environment.

    Import is used rather than a pytest hook because it is strictly earlier and
    needs no wiring: any route that reaches this module at all - collection of
    a conftest, or an explicit ``from tests.conftest import ...`` - has already
    run it. tests/test_tmp_path_privacy.py grades the property in one session
    with a repointing failure ordered ahead of an ordinary victim, because two
    separate processes cannot observe session state at all.

    A failure here leaves the module unimportable and the suite refusing to
    start. That is the correct direction for a privacy control: a redactor that
    cannot determine what to redact must not run unprotected.

    Returns:
        The frozen rule set.
    """
    return _build_redaction_rules()


#: Built at import. THIS NAME MUST BE ASSIGNED EXACTLY ONCE, HERE. A second
#: assignment, or any path that rebuilds the rules later, reintroduces the
#: defect the seeding exists to prevent - see :func:`_seed_redaction_rules`.
_REDACTION_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = _seed_redaction_rules()


# --- credentials ------------------------------------------------------------
#
# CS-1156 - A SEPARATE LAYER, DELIBERATELY NOT A FIFTH PERSONAL-DATA CLASS. A
# credential is not personal data: it identifies nobody, it is rotatable, and
# the consequence of leaking one is unauthorised ACCESS rather than exposure.
# Folding it into `_REDACTION_RULES` would also have meant editing CLAUDE.md's
# two class regions and the fingerprint map to admit a class that is not what
# either region is about. `redact_personal_data` keeps its exact contract and
# its honest docstring; this layer stands beside it and the render path applies
# both.
#
# THE DEFECT, MEASURED. 2026-09-19: an unrelated `FileNotFoundError` inside
# `tests/test_pre_push_ref_race.py` made pytest render the frame it crashed in,
# that frame was a `subprocess.run(..., env=...)` call, and the rendered
# arguments were the whole environment dict. An `sk-ant-` prefixed admin key
# printed in full, beside a home path this module DID replace.
#
# TWO RULE KINDS, AND THEY COVER DIFFERENT FAILURES.
#
#   LITERALS, from named variables. The shape `_build_redaction_rules` already
#   trusts: a literal cannot over-reach, because it rewrites the exact bytes it
#   was built from. This is what catches a token with no recognisable prefix -
#   a bare hex messaging token, say - which no shape rule could ever anchor on
#   without rewriting every SHA in every traceback.
#
#   SHAPES, from VENDOR-ASSIGNED prefixes. This is what catches a credential
#   arriving under a variable nobody listed, which is the failure a name list
#   structurally cannot cover. It is NOT the backed-out kind of shape rule: the
#   two rules `UNCOVERED_CLASSES` records were path-segment character classes
#   matched against arbitrary prose, measured too narrow and too greedy at once.
#   These anchor on a literal vendor prefix that does not occur in English, in
#   a path or in a traceback frame line, and each requires a long run of
#   credential alphabet after it. The blast radius is a string that already
#   looks exactly like a key.
#
# A FLOOR, BECAUSE AN EMPTY LITERAL MATCHES EVERYWHERE. A variable that is
# absent, blank or implausibly short contributes NO rule. Without the floor a
# variable set to "" would compile to a pattern matching at every position and
# would destroy every report on the machine that set it.

#: Variables whose WHOLE VALUE is a secret on this machine or on CI. Listed by
#: name rather than sniffed, so adding one is a decision somebody made.
_CREDENTIAL_VARIABLES: tuple[str, ...] = (
    "ANTHROPIC_USAGE_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_ADMIN_KEY",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "CODSPEED_TOKEN",
)

#: The shortest value admitted as a literal rule. Below this a value is more
#: likely a flag, a mode or a placeholder than a secret, and the cost of a
#: wrong literal is a mangled report rather than a leak.
_CREDENTIAL_MIN_LITERAL = 16

#: Vendor-assigned prefixes and the alphabet that follows them. Every entry is
#: a prefix no English word, path or identifier begins with.
#:
#: NO LENGTH FLOOR ONCE THE PREFIX IS PRESENT - CS-820, from an adversary's
#: measurement. The first build required a run of 16 or 20 after the prefix,
#: and pytest's middle cut of a long repr left a prefix with 8 to 19 characters
#: in front of its ``...`` marker: twelve such stubs survived. A floor protects
#: nothing here, because the prefix alone is what makes a string look like a
#: key, so any run of the alphabet after it goes with it.
_CREDENTIAL_SHAPES: tuple[str, ...] = (
    r"sk-ant-[A-Za-z0-9_\-]*",
    r"ghp_[A-Za-z0-9]*",
    r"gho_[A-Za-z0-9]*",
    r"ghs_[A-Za-z0-9]*",
    r"ghu_[A-Za-z0-9]*",
    r"github_pat_[A-Za-z0-9_]*",
)


def _build_credential_rules() -> tuple[tuple[re.Pattern[str], str], ...]:
    """The vendor shapes first, then the literals, longest literal first.

    ORDER DECIDES CORRECTNESS, AND THE FIRST BUILD HAD IT BACKWARDS AND SAID SO
    IN A SENTENCE THAT WAS FALSE. That sentence claimed a value matching both a
    literal and a shape came out identical either way. It does not, and the
    counter-example is one an adversary measured rather than one reasoned about:
    with a listed variable holding ``ghp_`` + twenty ``A``s, against the text
    ``value=<that token>BBBB end``, LITERALS FIRST replaces exactly the bytes the
    literal was built from and leaves ``BBBB`` standing beside the placeholder,
    while SHAPES FIRST matches greedily through the trailing alphanumerics and
    leaves nothing. Residue beside a placeholder is the worst of the three
    outcomes: it looks redacted.

    Literals are still sorted longest first, for the reason
    `_build_redaction_rules` sorts its home spellings that way - a literal that
    is a PREFIX of a longer one would otherwise cut the longer one in half.

    THE FLOOR IS APPLIED TO THE VALUE THAT IS COMPILED. The first build measured
    the STRIPPED length and compiled the RAW value, so a padded variable
    contributed a literal that could never match rendered text - a rule that
    passes every test by never firing.

    Returns:
        ``(pattern, replacement)`` pairs, applied in order. No class tag: these
        rules serve no personal-data class and
        tests/test_report_redaction_classes.py must keep finding none.
    """
    rules: list[tuple[re.Pattern[str], str]] = [
        (re.compile(shape), REDACTED_CREDENTIAL) for shape in _CREDENTIAL_SHAPES
    ]
    values = {os.environ.get(name, "").strip() for name in _CREDENTIAL_VARIABLES}
    rules.extend(
        (re.compile(re.escape(value)), REDACTED_CREDENTIAL)
        for value in sorted(
            (value for value in values if len(value) >= _CREDENTIAL_MIN_LITERAL),
            key=len,
            reverse=True,
        )
    )
    return tuple(rules)


#: Built at import, for the reason :func:`_seed_redaction_rules` gives at
#: length: a rule set built on demand is built from whichever test had last
#: moved the environment, and the dangerous direction is the one where the real
#: value drops OUT of the set and stops being redacted for the rest of the run.
_CREDENTIAL_RULES: tuple[tuple[re.Pattern[str], str], ...] = _build_credential_rules()


#: WHAT THIS LAYER DOES NOT REACH, REGISTERED RATHER THAN LEFT TO BE
#: DISCOVERED - the shape :data:`UNCOVERED_CLASSES` established for the
#: personal-data layer, and for the same reason: a dropped case is a silence,
#: a stated exemption is a fact the next reader can check.
#: tests/test_credential_redaction.py asserts each entry is genuinely still
#: uncovered, so an entry that quietly starts working is a RED too.
UNCOVERED_SECRETS: Mapping[str, str] = MappingProxyType(
    {
        "unlisted-and-unprefixed": (
            "a secret held in a variable nobody listed AND carrying no vendor "
            "prefix is reachable by neither rule kind. The two kinds were "
            "chosen to cover each other's blind spot and this is the residue "
            "where both are blind at once. Closing it needs entropy detection, "
            "which on arbitrary report prose is the same too-narrow-and-too-"
            "greedy knob that backed CS-860's rules out."
        ),
        "not-in-the-environment": (
            "a secret read from a file, a keyring or a service at runtime is "
            "never a value this module can enumerate, so no literal rule can "
            "be built from it. Only the vendor shapes can reach one."
        ),
        "cut-tail-of-an-unlisted-key": (
            "a cut that lands inside a key held under an UNLISTED name leaves "
            "its tail beside the marker with no prefix. The shape rules need "
            "the prefix and no literal was built for the name, so the tail "
            "stands; its head, which keeps the prefix, does not."
        ),
        "node-ids-outside-the-reporter": (
            "a node id is REDACTED WHERE IT IS RENDERED and never rewritten, so "
            "selection by it keeps working. The terminal reporter's location "
            "and summary lines and each failure's header are reached; "
            "--durations, the warnings summary and --collect-only print ids "
            "through paths no hook here sees."
        ),
        "internal-errors": (
            "a pytest INTERNALERROR is rendered by pytest itself and not from "
            "a report object, so no report hook sees it. Collection reports "
            "ARE reached - see pytest_collectreport below, added when an "
            "adversary reproduced the original leak at import time."
        ),
    }
)


def redact_credentials(text: str) -> str:
    """Replace every credential this module can recognise with a placeholder.

    NOT A COMPLETE SECRET FILTER, and it must not be described as one. It
    covers the values of :data:`_CREDENTIAL_VARIABLES` on this machine, and any
    string carrying one of the vendor prefixes in :data:`_CREDENTIAL_SHAPES`.
    What it does NOT reach is declared in :data:`UNCOVERED_SECRETS`, with a
    reason on each entry.

    Args:
        text: Rendered output.

    Returns:
        The text with recognised credentials replaced. Unchanged text is
        returned unchanged, which is how a caller tells whether anything was
        found.
    """
    for pattern, replacement in _CREDENTIAL_RULES:
        text = pattern.sub(replacement, text)
    return text


def redact_personal_data(text: str) -> str:
    """Replace every personal value in ``text`` with a placeholder.

    TWO of the four classes CLAUDE.md names: a home path, in every spelling
    :data:`_HOME_SPELLING_TRANSFORMS` produces, and the account name. The
    platform account id and the world name are REGISTERED AND UNCOVERED -
    :data:`UNCOVERED_CLASSES` carries a reason for each and this module's
    docstring carries the measurement. SO THIS IS NOT A COMPLETE PERSONAL-DATA
    FILTER and must not be described as one.

    Args:
        text: Rendered output.

    Returns:
        The text with personal data replaced. Unchanged text is returned
        unchanged, which is how callers tell whether anything was found.

    Raises:
        RuntimeError: If the rule set is empty. Refusing is the safe direction -
            a redactor with no rules changes nothing and would report every
            leaking string as clean.
    """
    if not _REDACTION_RULES:
        raise RuntimeError("the personal-data redaction rule set is empty")
    for pattern, replacement, _class_id in _REDACTION_RULES:
        text = pattern.sub(replacement, text)
    return text


#: CS-820 - a PIECE of a known value standing against pytest's cut marker.
#: pytest shortens a long repr by keeping its two ends and joining them with
#: ``...``, and whatever the cut landed inside is left as a piece on either side
#: of the marker. An adversary measured the last four letters of the account
#: name surviving in a home path whose head the cut had removed, and a listed
#: secret's tail survives the same way. No rule built from the WHOLE value can
#: match a piece of it.
#:
#: ONLY PIECES OF A KNOWN VALUE ARE REMOVED, and that is the whole rule. A run of
#: identifier characters touching a ``...`` loses its part that is a piece - at
#: least :data:`_MIN_CUT_PIECE` characters, or the whole value if it is shorter
#: - of an account-name spelling from :func:`_account_names` or of a listed
#: credential variable's value. The first build removed EVERY run touching a
#: ``...``, and a message pytest never cut - ``retrying connection...giving_up``
#: - lost both words; this rule leaves any text whose touching runs are not such
#: pieces exactly as written, whether or not pytest cut it.
#:
#: A key's prefix with a short stub is the shape layer's, which has no length
#: floor; the tail of a key held under an UNLISTED name is reachable by neither
#: and is declared in :data:`UNCOVERED_SECRETS`.
_CUT_RUN = re.compile(r"(?P<head>[A-Za-z0-9_\-]+)(?=\.\.\.)|(?<=\.\.\.)(?P<tail>[A-Za-z0-9_\-]+)")

#: The shortest piece counted, below which a piece of a name is too likely to be
#: a piece of an ordinary word as well.
_MIN_CUT_PIECE = 4


def _cut_sources() -> tuple[str, ...]:
    """The known values whose pieces are removed, lower-cased, built at import."""
    names = {name.strip().lower() for name in _account_names(_home_like_roots())}
    values = {os.environ.get(name, "").strip().lower() for name in _CREDENTIAL_VARIABLES}
    literals = {value for value in values if len(value) >= _CREDENTIAL_MIN_LITERAL}
    return tuple(sorted(source for source in names | literals if source))


#: Built at import, for the reason :data:`_CREDENTIAL_RULES` is.
_CUT_SOURCES: tuple[str, ...] = _cut_sources()


def _is_piece(piece: str, *, head: bool) -> bool:
    """Whether `piece` is a piece of a known value - its start if `head`, else its end."""
    lowered = piece.lower()
    return any(
        len(lowered) >= min(_MIN_CUT_PIECE, len(source))
        and (source.startswith(lowered) if head else source.endswith(lowered))
        for source in _CUT_SOURCES
    )


def _without_piece(match: re.Match[str]) -> str:
    """The run with its longest known-value piece removed from the side touching the cut."""
    head = match.group("head")
    if head is not None:
        for size in range(len(head), 0, -1):
            if _is_piece(head[-size:], head=True):
                return head[:-size]
        return head
    tail = match.group("tail")
    for size in range(len(tail), 0, -1):
        if _is_piece(tail[:size], head=False):
            return tail[size:]
    return tail


def redact_cut_fragments(text: str) -> str:
    """Remove every piece of a known value that stands against a ``...`` marker.

    A third layer beside the personal-data and credential layers: it removes
    pieces of the values those layers replace whole, where a cut left only a
    piece. See :data:`_CUT_RUN` for the rule and the measurement behind it.

    Args:
        text: Rendered output.

    Returns:
        The text with each known-value piece beside a marker removed and every
        other character, the marker included, left as it was.
    """
    return _CUT_RUN.sub(_without_piece, text)


def redact_report(text: str) -> str:
    """Every layer, in the order a rendered report needs them.

    CS-1156 - THE RENDER PATH APPLIES BOTH, AND NEITHER FUNCTION KNOWS ABOUT
    THE OTHER. `redact_personal_data` keeps its exact contract and its honest
    docstring about the two classes it covers; `redact_credentials` keeps its
    own about the secrets it recognises. This is the only place that says a
    report needs both, so a caller that wants one layer can still ask for it -
    `tests/test_redaction_scope.py` and the class-grading module both do.

    ORDER. Personal data first, credentials second. A credential is replaced by
    a fixed placeholder containing no path and no account name, so running the
    personal layer afterwards would find nothing new; the reverse order is safe
    too, and the choice is stated rather than left to be inferred. The cut
    pieces go LAST - CS-820 - so a whole value standing beside a cut is still
    replaced by its own rule and only the piece the cut left is removed.

    Args:
        text: Rendered output.

    Returns:
        The text with both classes of value replaced and every known-value
        piece beside a cut marker removed.
    """
    return redact_cut_fragments(redact_credentials(redact_personal_data(text)))


class _LineWriter(Protocol):
    """The one method pytest's terminal writer needs to be for a longrepr.

    Declared structurally rather than by importing pytest's own writer type,
    which lives behind a private module path. A rename there would then be an
    ImportError in this conftest, and an unimportable conftest is a suite that
    does not start at all - far too much to risk for an annotation.
    """

    def line(self, s: str = "", **markup: bool) -> None:
        """Write one line."""


@dataclass(frozen=True)
class _RedactedCrash:
    """The crash location of a redacted report, shaped like pytest's own.

    ``__str__`` matters as much as the fields. Under ``--tb=line`` pytest
    renders a failure by printing ``str(report.longrepr.reprcrash)`` itself
    rather than asking the longrepr to render, so this object's string form IS
    the FAILURES section for that style. It reproduces pytest's own
    ``path:lineno: message`` shape, first message line only.
    """

    path: str
    lineno: int
    message: str

    def __str__(self) -> str:
        """Render as pytest's crash line - what ``--tb=line`` prints verbatim."""
        return f"{self.path}:{self.lineno}: {self.message.split(chr(10), 1)[0]}"


@dataclass(frozen=True)
class _RedactedRepr:
    """A rendered failure report with the personal data taken out.

    Duck-typed against the two things pytest asks of a ``longrepr``:
    ``toterminal`` for the FAILURES section and ``reprcrash.message`` for the
    ``-ra`` short summary line. Handing back a bare ``str`` instead is simpler
    and was measured worse - pytest uses the whole string as the summary
    message, so every redacted failure's summary line became the first line of
    its own traceback instead of naming its exception.

    DELIBERATELY WITHOUT a ``reprtraceback`` attribute. pytest serializes a
    longrepr structurally only when ``toterminal``, ``reprtraceback`` AND
    ``reprcrash`` are all present, and this object has no structure to
    serialize; without it, serialization falls back to ``str()``, which is
    exactly the redacted text.

    STATED COST: the report is emitted as plain text, so it loses terminal
    colour. That is paid only by a report that actually carried personal data.
    """

    text: str
    reprcrash: _RedactedCrash | None

    def toterminal(self, out: _LineWriter) -> None:
        """Write the redacted text to pytest's terminal writer."""
        out.line(self.text)

    def __str__(self) -> str:
        """Render as the redacted text - what junitxml and reportlog store."""
        return self.text


def _redacted_crash(longrepr: object) -> _RedactedCrash | None:
    """Copy a report's crash location, redacted, or None if it has none."""
    crash = getattr(longrepr, "reprcrash", None)
    if crash is None:
        return None
    return _RedactedCrash(
        path=redact_report(str(getattr(crash, "path", ""))),
        lineno=int(getattr(crash, "lineno", 0)),
        message=redact_report(str(getattr(crash, "message", ""))),
    )


def _redact_report(report: pytest.TestReport | pytest.CollectReport) -> None:
    """Redact a report's rendered failure and its captured output, in place.

    Two channels, both of which a forced failure prints. ``longrepr`` carries
    the traceback, the frame ARGUMENTS - the measured leak - and the locals
    under ``-l``. ``sections`` carries captured stdout, stderr and logging.

    The rendered TEXT is what gets rewritten, not the structured repr, because
    the leak reaches the terminal through the rendering and a structural rewrite
    would have to know every pytest version's node layout. The cost is that a
    redacted report loses its colour markup; the replacement is gated on a
    comparison, so a report that neither comparison moves is passed through
    unchanged.

    THE GATE READS TWO CHANNELS, NOT ONE. ``longreprtext`` is what the default
    traceback style renders, and ``reprcrash`` is what ``--tb=line`` and
    ``--tb=no -ra`` render - pytest prints the crash location itself for those
    styles, so a report whose rendered text holds nothing can still carry an
    absolute crash path. Gating on the rendered text alone leaves that style
    unreached.

    A skip report is left alone unconditionally: its ``longrepr`` is a
    ``(path, lineno, reason)`` tuple that pytest INDEXES when folding the skip
    summary, and replacing it with text breaks that reporting.

    Args:
        report: The report to sanitize in place.
    """
    if isinstance(report, pytest.TestReport):
        # CS-820: the failure's header line is the location's name, which is
        # the parametrize id - redacted here, where it is rendered from.
        fspath, lineno, domain = report.location
        moved = redact_report(domain)
        if moved != domain:
            report.location = (fspath, lineno, moved)
    longrepr = report.longrepr
    if longrepr is not None and not isinstance(longrepr, tuple):
        rendered = report.longreprtext
        redacted = redact_report(rendered)
        crash_text = str(getattr(longrepr, "reprcrash", "") or "")
        if redacted != rendered or redact_report(crash_text) != crash_text:
            # Duck-typed on purpose: pytest declares this attribute as its own
            # TerminalRepr, which lives behind a private module path. Importing
            # it for one annotation would make a rename there an unimportable
            # conftest, and an unimportable conftest is a suite that does not
            # start. pytest only ever calls toterminal() and reads
            # reprcrash.message on this object; _RedactedRepr provides both.
            report.longrepr = _RedactedRepr(  # type: ignore[assignment]
                redacted, _redacted_crash(longrepr)
            )
    sections = [(name, redact_report(content)) for name, content in report.sections]
    if sections != report.sections:
        report.sections = sections


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport() -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Strip personal data out of every setup, call and teardown report.

    CS-428. pytest renders the failing frame's ARGUMENTS whenever the traceback
    style is long, which is the default, so any test taking ``tmp_path`` or a
    fixture derived from it prints its base temporary directory on failure. On
    Windows that directory is under the user profile and its own name embeds
    ``getpass.getuser()``, so one line carries an absolute home path and the
    account name twice - both forbidden by CLAUDE.md non-negotiable 3, and both
    reaching an echo path in the sense of non-negotiable 12.

    WHY THIS LEVER AND NOT A BASETEMP REDIRECT. Redirecting pytest's base
    temporary directory changes the VALUE, which is the more thorough remedy
    where it is available - and it is not available here. On Windows
    ``tempfile.gettempdir()`` is itself inside the user profile, so a redirect
    within it changes nothing, and the alternatives are worse: a repo-local
    root is under a home directory on a Linux CI runner, and any fixed absolute
    root is a hardcoded machine layout, which non-negotiable 3 forbids outright.
    A redirect would also change isolation and retention semantics for every
    test that takes ``tmp_path``. Redacting at render time changes nothing about
    where a test writes; what it rewrites is a report's rendered text and crash
    location, gated on either one changing under redaction.

    SCOPE, stated rather than implied. Some but NOT ALL of these boundaries are
    measured by tests/test_tmp_path_privacy.py; the ones that are not are named
    as such below rather than left to read as measured. This acts on the setup,
    call and teardown reports of items under ``tests/``. Reports that reach the
    terminal through a parallel worker need the second hook below as well.

    NOT reached: pytest's session header, the warnings summary - which pytest
    builds from its own warning store rather than from a report - ``--co``
    output, and internal errors. CS-447 owns the session header and the
    warnings summary.

    COLLECTION REPORTS WERE ON THAT LIST AND ARE NOT ANY MORE. An adversary
    reproduced CS-1156's original leak at IMPORT time - the same
    ``subprocess.run(..., env=...)`` frame, moved to module level - and the
    planted credential printed three times with no placeholder anywhere,
    because a collection failure is rendered from a CollectReport that no hook
    here touched. :func:`pytest_collectreport` below closes it, and it applies
    the SAME redaction, so the two paths cannot drift apart.

    REACHED, and this list was WRONG until an adversary measured it. Output
    from a child process the suite starts IS reached whenever the child writes
    to INHERITED stdout, because pytest captures that into the ``Captured
    stdout call`` section and this hook rewrites ``report.sections``. The
    earlier text claimed the opposite and claimed the boundary was measured;
    neither held, and no test in tests/test_tmp_path_privacy.py covers a
    child's inherited stdout. A child whose output this suite captures and
    renders ITSELF - as the grading module's own subprocess arms do - is a
    different case and is genuinely outside, because that text is read as data
    rather than rendered into a report.

    Returns:
        The report, sanitized in place.
    """
    report = yield
    try:
        _redact_report(report)
    except Exception as exc:
        # Deliberately broad, and it fails CLOSED - see _REDACTION_FAILED. Only
        # the exception TYPE is rendered; its message would be an echo path.
        report.longrepr = _REDACTION_FAILED.format(kind=type(exc).__name__)
    return report


def _redact_worker_description(node: Any) -> None:
    """Redact the parallel worker's description, in place.

    Under xdist a report is built in the WORKER and rendered in the CONTROLLER,
    which attaches the worker to it on arrival. pytest then prints a line above
    the traceback naming that worker's platform and INTERPRETER PATH, built
    from the worker's own description dictionary and memoised on the worker
    object. On a machine whose interpreter lives under the user profile - the
    default for a per-user Python install on Windows - that line is an absolute
    home path, composed after the worker-side report hook has already run and
    therefore unreachable from it.

    Both the source dictionary and the memo are rewritten: the dictionary
    because the line is normally composed later from it, the memo because a
    report rendered earlier in the session may already have composed it.

    Args:
        node: The worker the controller attached to a report.
    """
    info = getattr(node, "workerinfo", None)
    if isinstance(info, dict):
        for key, value in list(info.items()):
            if isinstance(value, str):
                info[key] = redact_report(value)
    cached = getattr(node, "_workerinfocache", None)
    if isinstance(cached, str):
        node._workerinfocache = redact_report(cached)  # noqa: SLF001


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Redact node ids WHERE THEY ARE RENDERED - CS-820, and never rewrite one.

    MEASURED by an adversary: a parametrize id derived from a mapping's items,
    an ``ids=`` callable or an ``ids=`` list printed whole credentials on the
    ``-v`` progress line, the FAILED summary line and each failure's header. The
    first repair rewrote the ids at collection, and a second adversary measured
    what that broke: ``-k`` and ``--deselect`` by the original id matched
    nothing, and an id copied from the output reran nothing.

    So the id is left exactly as pytest built it and only its RENDERINGS pass
    through :func:`redact_report`: ``Config.cwd_relative_nodeid``, which the
    terminal reporter renders every summary line's id through, and the
    reporter's own location line, whose trailing name it renders from the
    report's location - redacted by :func:`_redact_report` for the header too.
    An id redaction does not move renders byte for byte as pytest built it.

    Duck-typed, for the reason `_redact_report` gives: each is wrapped only
    where it exists, so a rename in pytest leaves this conftest importable.

    Args:
        config: The session's configuration.
    """
    if getattr(config, "_cs820_ids_redacted", False):
        return
    config._cs820_ids_redacted = True  # type: ignore[attr-defined]  # noqa: SLF001
    relative = config.cwd_relative_nodeid

    def redacted_relative(nodeid: str) -> str:
        return redact_report(relative(nodeid))

    config.cwd_relative_nodeid = redacted_relative  # type: ignore[method-assign]
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    locate = getattr(reporter, "_locationline", None)
    if callable(locate):

        def redacted_location(nodeid: str, fspath: str, lineno: int | None, domain: str) -> str:
            return redact_report(locate(nodeid, fspath, lineno, redact_report(domain)))

        reporter._locationline = redacted_location  # noqa: SLF001


@pytest.hookimpl(tryfirst=True)
def pytest_collectreport(report: pytest.CollectReport) -> None:
    """Redact a COLLECTION failure the same way a test failure is redacted.

    CS-1156. A module that raises at import - which is where a session-scoped
    probe, a module-level constant or a module-level subprocess call lives -
    fails during COLLECTION, and pytest renders that from a CollectReport.
    Nothing here saw one until an adversary planted the original leaking frame
    at module level and watched the credential print three times.

    It calls the same :func:`_redact_report`, deliberately: a second
    implementation would be a second thing to keep in step, and the channels a
    CollectReport carries - ``longrepr`` and ``sections`` - are the two that
    helper already reads.

    THIS ONE IS NOT A WRAPPER, AND THE RUNTEST HOOK ABOVE IS. The difference is
    pytest's own: ``pytest_runtest_makereport`` BUILDS a report and a wrapper is
    how you get at the built one, while ``pytest_collectreport`` is HANDED one
    and returns nothing. Written as a wrapper it yields the hook's combined
    result - a list - and the first attribute write raises INTERNALERROR, which
    is how this was caught. ``tryfirst`` puts it ahead of pytest's own terminal
    reporter, which is the consumer that renders the text.

    Args:
        report: The collection report to sanitize in place.
    """
    try:
        _redact_report(report)
    except Exception as exc:
        # Fails CLOSED, exactly as the runtest hook does, and for the same
        # reason: the exception MESSAGE would itself be an echo path.
        report.longrepr = _REDACTION_FAILED.format(kind=type(exc).__name__)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Redact the parallel worker description the controller renders above a failure.

    CS-428, second channel. Fires in both processes; only a report that has
    been through a worker carries one, so this is a no-op in the ordinary
    single-process run and in the worker itself.

    Args:
        report: The report the controller received.
    """
    node = getattr(report, "node", None)
    if node is not None:
        _redact_worker_description(node)


def _scrub_repo_locating_environment() -> None:
    """Remove every inherited git repository POINTER from this process.

    CS-968, MEASURED 2026-09-11. ``git push`` exports ``GIT_DIR`` to the
    pre-push hook WHEN THE PUSH COMES FROM A LINKED WORKTREE, and not from a
    normal checkout. ``.githooks/pre-push`` runs ``pytest tests``, so this whole
    suite can run with a pointer at a repository nobody in it named.

    THIS IS THE PROCESS-WIDE HALF, AND IT IS NOT REDUNDANT WITH THE PER-SPAWN
    SCRUBS. ``tests/git_env.py`` cleans the environment handed to a CHILD, which
    is the half that stops a throwaway ``git init`` from re-initialising the real
    repository as bare. It cannot help a test that reads the pointer IN-PROCESS -
    ``tools/precommit_gate.py`` imported through ``load_gate()`` resolves its repo
    from ``os.environ`` at call time, and the drift driver enumerates documents
    the same way. Both were measured going red in a real worktree push while
    every child spawn was already clean.

    NOTHING IN THIS SUITE MAY DEPEND ON AN INHERITED POINTER. A test that wants
    to act on a specific repository says so with ``-C``, a ``cwd``, or an
    explicit environment; one that wants to GRADE inheritance builds the
    variable itself rather than hoping the runner exported one.

    Done at import rather than in an autouse fixture on purpose: module-level
    code in a test module runs during COLLECTION, before any fixture, and a
    pointer that survives until the first test has already been read by then.

    AT THE FOOT OF THIS FILE, AND THE IMPORT IS LOCAL, so that adding this
    inserted NO line above any existing one. The deep archive pins line
    numbers into this module, and a block placed higher up moved them - which
    is rot manufactured by the repair rather than found by it.
    """
    from tests import git_env  # noqa: PLC0415 - see the placement note above

    for name in [key for key in os.environ if git_env.relocates(key)]:
        del os.environ[name]


_scrub_repo_locating_environment()


# ---------------------------------------------------------------------------
# CS-973 - the live copies directory is left as it was found
#
# APPENDED AT THE FOOT FOR THE SAME REASON THE SCRUB ABOVE IS: the deep archive
# pins line numbers into this module, so a block placed higher up manufactures
# rot rather than finding it. A fixture is resolved by NAME, so position costs
# nothing here.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _the_live_copies_directory_is_left_as_it_was_found() -> Generator[None]:
    """Count the real-save copies in the live work directory before and after the run.

    THE DEFECT THIS GRADES, MEASURED 2026-09-11. ``world.load_world`` copies its
    subject through ``workdir.copy_for_read`` before it parses a byte, and the
    work root that copy lands in DEFAULTS TO ``<repo>/work``. Two test modules
    reached real saves without redirecting it and left 23 files carrying
    ``COPY_SUFFIX`` in the live copies directory - one per save in the
    operator's library. The originals were untouched and the directory is
    gitignored with no ``.sav`` tracked, so this was corpus pollution rather
    than a leak: anything globbing ``*.sav`` there saw 23 worlds that are not
    worlds, and that directory is what the save layer is measured against.

    IT DISCOVERS THE WRITER RATHER THAN NAMING IT. The two modules were found
    from outside, by a sibling project's write-attribution run, and a guard that
    encoded that attribution would grade only the two writers already known. A
    count over the whole session catches the next one, wherever it is written,
    including one added by a module that does not exist yet.

    SESSION SCOPE IS THE CLAIM. Per-module redirects are the fix and each is
    graded where it lives; this is the arm that says the SUITE leaves the
    directory as it found it, which is the property CS-973 asks for and which no
    per-module arm can assert.

    THE DEFAULT ROOT IS DERIVED, NOT RESOLVED. ``workdir.work_root()`` reads
    ``ENV_WORK_ROOT``, so calling it here would make this guard watch whatever
    directory the last redirect pointed at - which is every directory except the
    one at risk. The location is built from this file's own position instead,
    exactly as :func:`repo_root` builds the root.

    A COUNT, NOT A LISTING. A copy is named after the save it came from, so a
    set of names rendered into a failing assertion is a set of the operator's
    world names (non-negotiable 12). The delta is a number and the remedy is to
    run the write tracer, which is where attribution belongs.

    Yields:
        Nothing. The assertion is the teardown.
    """
    from clockspeed.save import workdir  # noqa: PLC0415 - see the placement note above

    live = Path(__file__).resolve().parents[1] / workdir.WORK_DIR_NAME / workdir.COPIES_DIR_NAME

    def _copies() -> int:
        """Count the copies present now.

        Returns:
            How many files carrying ``COPY_SUFFIX`` the live directory holds.
        """
        if not live.is_dir():
            return 0
        return sum(1 for _ in live.glob("*" + workdir.COPY_SUFFIX))

    before = _copies()
    yield
    after = _copies()

    assert after == before, (
        f"the suite added {after - before} real-save copies to the live copies "
        f"directory; run the write tracer to attribute them"
    )


# ---------------------------------------------------------------------------
# CS-1116 - the program and the bound ``run_git`` spawns with
#
# APPENDED AT THE FOOT FOR THE SAME REASON THE SCRUB ABOVE IS: the deep archive
# pins line numbers into this module. Both are module globals read at CALL time,
# so tests/test_conftest_run_git.py can swap in a child that hangs past a
# shrunken bound, and position costs nothing.
# ---------------------------------------------------------------------------

#: The program ``run_git`` runs. Never an absolute path - PATH resolves it
#: (CONVENTIONS.md section 10).
RUN_GIT_PROGRAM: tuple[str, ...] = ("git",)

#: Seconds ``run_git`` waits for one git command (CS-896 bound).
RUN_GIT_TIMEOUT_SECONDS: float = 120
