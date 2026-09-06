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
grading for it lives in tests/test_tmp_path_privacy.py, which runs real pytest
subprocesses and scans their real output, because the subject is what pytest
prints rather than what any function returns - and, for the one property no
subprocess can observe, runs a repointing failure and its victim inside a
single session.

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
    """Run a git subcommand in ``root``, or return None if git is unusable.

    Public because test modules import it: git is the only tool that can
    answer "would this path be committed" and "is this path ignored", and both
    questions are asserted on in tests/test_scaffold.py.

    The executable is resolved from PATH rather than from an absolute path.
    That is required, not lazy: an absolute tool path in a tracked file
    hardcodes a machine layout (CONVENTIONS.md section 10).

    Args:
        root: Directory to run git in.
        *args: Arguments after the ``git -C <root>`` prefix.

    Returns:
        The completed process, or None if git is missing or timed out. A
        non-zero exit is returned rather than swallowed so the caller can
        decide whether it matters.
    """
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


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
        path=redact_personal_data(str(getattr(crash, "path", ""))),
        lineno=int(getattr(crash, "lineno", 0)),
        message=redact_personal_data(str(getattr(crash, "message", ""))),
    )


def _redact_report(report: pytest.TestReport) -> None:
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
    longrepr = report.longrepr
    if longrepr is not None and not isinstance(longrepr, tuple):
        rendered = report.longreprtext
        redacted = redact_personal_data(rendered)
        crash_text = str(getattr(longrepr, "reprcrash", "") or "")
        if redacted != rendered or redact_personal_data(crash_text) != crash_text:
            # Duck-typed on purpose: pytest declares this attribute as its own
            # TerminalRepr, which lives behind a private module path. Importing
            # it for one annotation would make a rename there an unimportable
            # conftest, and an unimportable conftest is a suite that does not
            # start. pytest only ever calls toterminal() and reads
            # reprcrash.message on this object; _RedactedRepr provides both.
            report.longrepr = _RedactedRepr(  # type: ignore[assignment]
                redacted, _redacted_crash(longrepr)
            )
    sections = [(name, redact_personal_data(content)) for name, content in report.sections]
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
    builds from its own warning store rather than from a report - collection
    reports, ``--co`` output, and internal errors. CS-447 owns the session
    header and the warnings summary.

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
                info[key] = redact_personal_data(value)
    cached = getattr(node, "_workerinfocache", None)
    if isinstance(cached, str):
        node._workerinfocache = redact_personal_data(cached)  # noqa: SLF001


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
