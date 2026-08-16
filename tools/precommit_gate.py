#!/usr/bin/env python3
"""Clockspeed enforcement gate - one checker core, three entry modes.

Modes (mutually exclusive, exactly one is required):

  --staged        Enumerate staged paths and check THE BYTES GIT WILL COMMIT,
                  read from the index with `git show :<path>` - never from the
                  working tree. Gating the worktree is a real hole: a path can
                  be staged clean and then dirtied, or staged dirty and then
                  cleaned, and a worktree gate would read the wrong bytes.
  --files <p...>  Check working-tree paths. Used by the Claude PostToolUse
                  path and by manual runs.
  --text-stdin    Read text from stdin and run the character-set and secret
                  checks over it. This is what the Claude PreToolUse hook
                  feeds a proposed command string into.

Exit codes: 0 pass, 1 block. Nothing else. An unexpected exception exits 1 - a
gate that crashes open is worse than no gate at all - and reports the exception
CLASS plus its redacted text.

The TRACEBACK is suppressed by default and revealed only by setting
CLOCKSPEED_CRASH_TRACEBACK=1. That is the same shape CLAUDE.md non-negotiable
12 already mandates for the save header options string, and it is here for the
same reason: a traceback cannot be honestly redacted. It renders an absolute
path per frame - a home path on any checkout under a user profile - and its
final line is str(exc), the exact rendering safe_exc_text() removes everywhere
else in this file. Suppressing it changes what is PRINTED and never whether the
gate fails: the exit code is 1 with the flag on and with it off.

CONVENTIONS.md section 15.1: "a guard can be green while self-excusing -
skipping itself on the very files it is meant to cover." This gate therefore
has NO path allowlist of any kind. It checks its own source, its own tests and
its own hooks exactly like anything else, and `--verbose` / `--list-skipped`
print every path it did not check together with the reason it did not.

A COVERAGE skip - one saying this gate's own DETECTION was reduced, rather than
that a unit went unread - prints with NO flag at all, because the git hook
passes none. See COVERAGE_SKIP_LABELS.

Nothing personal is hardcoded here. The Windows account name comes from the
environment, the platform account id from listing the save root, and the world
names from the `.sav` basenames under it plus an operator declaration - all at
runtime. No such value appears in this file, and the gate checking its own
source is what proves it: a literal here would make the gate block itself.

Detection of a world value is VALUE-based and never SHAPE-based, and that is a
measurement rather than a preference. A world token is 22 characters of
[A-Za-z0-9_-]; over the tracked tree, an anchored exact-22 match that also
demands a digit, an upper and a lower still hits ordinary game class names of
the `Build_ConstructorMk1_C` shape, a population clockspeed/data/registry.py
only grows. A shape-only detector would refuse nearly every commit here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from shutil import which

GATE_NAME = "precommit_gate"

# The highest byte that may appear in authored text. Anything above it is a
# character-set violation (CONVENTIONS.md section 10).
MAX_ASCII = 0x7E

# Content larger than this is not scanned; the skip is reported, never silent.
MAX_CONTENT_BYTES = 4 * 1024 * 1024

# Subprocess budgets. A gate that hangs is a gate that gets disabled.
GIT_TIMEOUT = 60
RUFF_TIMEOUT = 90


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Diagnostic:
    """One blocking finding, rendered as `path:line:col: CODE reason`."""

    path: str
    line: int
    col: int
    code: str
    reason: str

    def render(self) -> str:
        """Render as `path:line:col: CODE reason`."""
        return "%s:%d:%d: %s %s" % (
            self.path,
            self.line,
            self.col,
            self.code,
            self.reason,
        )


@dataclass
class Unit:
    """One thing to check: a path plus, when readable, its bytes."""

    label: str
    origin: str
    data: bytes | None = None
    ext: str = ""
    # Set only when the checked bytes are exactly what sits at this path on
    # disk. Lets the linter run against the real file, where ruff's own config
    # discovery and per-file-ignores resolve correctly.
    disk_path: str | None = None


@dataclass
class Report:
    """Everything one gate run learned: findings, skips and notes."""

    diagnostics: list[Diagnostic] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    checked: list[tuple[str, str, int]] = field(default_factory=list)
    units: list[Unit] = field(default_factory=list)

    def add(self, diag: Diagnostic) -> None:
        """Record a blocking finding."""
        self.diagnostics.append(diag)

    def skip(self, label: str, why: str) -> None:
        """Record something not checked, and the reason it was not."""
        self.skipped.append((label, why))


# --------------------------------------------------------------------------
# Exception rendering
# --------------------------------------------------------------------------


def safe_exc_text(exc: BaseException) -> str:
    """Render an exception with no path and no argument vector left in it.

    THE ROOT CAUSE, stated once here so the seven call sites below do not each
    have to restate it: on Windows, str() on an OSError appends the FILENAME it
    failed on - "[Errno 2] No such file or directory: '<a path>'" - and that
    path routinely carries the account name and the home directory. An error
    message is an echo path exactly like a debug dump or a hex preview
    (CLAUDE.md non-negotiable 12), so a guard that reports a failed read has to
    strip it. Note that the formatting SYNTAX is irrelevant: this file renders
    exceptions through f-strings, through %, and through .format, and all three
    leak identically. The fix is at the value, not at the format string.

    PER EXCEPTION TYPE, and deliberately not one OSError-shaped helper for all
    of them. `strerror` is an OSError attribute, so a helper that reaches for
    it on any other type finds nothing and falls back to the full str() -
    which is precisely the leak it was written to prevent. Several of the types
    that reach this function have no strerror at all:

        OSError                     str() appends the filename, strerror does not
        SyntaxError                 str() appends the file compile() was handed
        subprocess.TimeoutExpired   str() renders the whole command line, and
        subprocess.CalledProcessError   in --files mode that argv is built from
                                    paths the caller supplied
        anything else               str() may be absolutely anything

    So this is an ALLOWLIST rather than a denylist: a field is rendered only
    where that field is known not to carry a path, and an unrecognised type
    contributes its class name and nothing else. That trades message detail for
    the guarantee, and the trade is cheap - every diagnostic already names the
    file in its LABEL, so a reader is never left wondering which path failed.

    Returns:
        A rendering that is safe to print, and never empty: a skip whose reason
        is blank tells the reader less than nothing.
    """
    # GitError is defined further down under "Git plumbing", where it belongs.
    # The name resolves at call time, and every caller runs after import.
    if isinstance(exc, GitError):
        # Its message is built by git_run_error() below, already argv-free.
        return str(exc) or type(exc).__name__
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, SyntaxError):
        return exc.msg or type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return "%s after %s seconds" % (type(exc).__name__, exc.timeout)
    if isinstance(exc, subprocess.CalledProcessError):
        return "%s exit %d" % (type(exc).__name__, exc.returncode)
    return type(exc).__name__


# --------------------------------------------------------------------------
# Extension policy
# --------------------------------------------------------------------------

# Authored text. A NUL byte in one of these is itself a finding rather than a
# reason to skip - a text file with a NUL is either mis-encoded or not text.
TEXT_EXTS = frozenset(
    {
        ".py",
        ".pyi",
        ".md",
        ".rst",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".txt",
        ".sh",
        ".ps1",
        ".bat",
        ".cmd",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".svg",
        ".sql",
        ".xml",
        ".csv",
    }
)

# Known binary. Skipped by extension before a single byte is read.
BINARY_EXTS = frozenset(
    {
        ".sav",
        ".usmap",
        ".pak",
        ".ucas",
        ".utoc",
        ".uasset",
        ".uexp",
        ".zip",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".tar",
        ".rar",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".bmp",
        ".webp",
        ".tif",
        ".tiff",
        ".pdf",
        ".exe",
        ".dll",
        ".pyd",
        ".so",
        ".dylib",
        ".lib",
        ".obj",
        ".o",
        ".class",
        ".jar",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".mp3",
        ".mp4",
        ".wav",
        ".ogg",
        ".webm",
        ".avi",
        ".mov",
        ".bin",
        ".dat",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".pyc",
        ".pyo",
        ".whl",
        ".pdb",
    }
)

# Publisher-owned artifacts. This is the second line of defence behind
# .gitignore, which does NOT stop `git add -f`.
PUBLISHER_EXTS = frozenset({".sav", ".usmap", ".pak", ".ucas", ".utoc"})
PUBLISHER_NAMES = frozenset({"headers.zip"})
# Root-anchored, exactly like .gitignore's `/data/` and `/corpus/`. Anchoring
# matters: BOOTSTRAP.md section 6 puts SOURCE at clockspeed/data/, and an
# unanchored rule would block the entire data layer from ever being committed.
PUBLISHER_ROOT_DIRS = ("data", "corpus")


# --------------------------------------------------------------------------
# Character set
# --------------------------------------------------------------------------

# Bytes 0x00-0x7E survive; anything left after the delete is a violation.
_ASCII_BYTES = bytes(range(0x7F))

NAMED_OFFENDERS = {
    0x2014: "U+2014 em dash (use a spaced hyphen ' - ')",
    0x2013: "U+2013 en dash (use a plain hyphen '-')",
    0x2018: "U+2018 left smart single quote (use ')",
    0x2019: "U+2019 right smart single quote (use ')",
    0x201C: 'U+201C left smart double quote (use ")',
    0x201D: 'U+201D right smart double quote (use ")',
    0x00A0: "U+00A0 non-breaking space (use a plain space)",
    0xFEFF: "U+FEFF byte order mark (write the file without a BOM)",
}

MAX_CHARSET_DIAGS = 25


def has_non_ascii(data: bytes) -> bool:
    """Return True when any byte in data is above MAX_ASCII."""
    return bool(data.translate(None, delete=_ASCII_BYTES))


def decode_for_report(data: bytes) -> tuple[str, str | None]:
    """Decode bytes to text for line/column reporting.

    Returns (text, note). Decoding never raises: a file that is not valid
    UTF-8 is still reported, it is not silently skipped.
    """
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return (
            data.decode("latin-1"),
            "content is not valid UTF-8; decoded as latin-1 for reporting",
        )


def describe_codepoint(ch: str) -> str:
    """Name a non-ASCII character, spelling out the common offenders."""
    order = ord(ch)
    named = NAMED_OFFENDERS.get(order)
    if named is not None:
        return named
    return "U+{:04X} {}".format(order, unicodedata.name(ch, "unnamed codepoint"))


def check_charset(label: str, data: bytes, report: Report) -> None:
    """Any byte above 0x7E in authored text is a violation."""
    if not has_non_ascii(data):
        return
    text, note = decode_for_report(data)
    if note:
        report.notes.append(f"{label}: {note}")
    found = 0
    for lineno, line in enumerate(text.split("\n"), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) <= MAX_ASCII:
                continue
            found += 1
            if found > MAX_CHARSET_DIAGS:
                report.notes.append(
                    "%s: more than %d non-ASCII characters; "
                    "only the first %d are listed" % (label, MAX_CHARSET_DIAGS, MAX_CHARSET_DIAGS)
                )
                return
            report.add(
                Diagnostic(
                    label,
                    lineno,
                    col,
                    "CHARSET",
                    "non-ASCII character: " + describe_codepoint(ch),
                )
            )


def check_nul(label: str, data: bytes, report: Report) -> None:
    """A NUL byte inside a known-text extension is a finding, not a skip."""
    index = data.find(b"\x00")
    if index < 0:
        return
    line = data.count(b"\n", 0, index) + 1
    start = data.rfind(b"\n", 0, index) + 1
    report.add(
        Diagnostic(
            label,
            line,
            index - start + 1,
            "BINARY",
            "NUL byte inside a text file; content is binary or mis-encoded",
        )
    )


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------

# Obvious placeholders. Matched against the offending literal itself, not the
# whole line: a trailing `# TODO` comment must not excuse a real credential
# sitting on the same line.
PLACEHOLDER_RE = re.compile(
    "|".join(
        [
            "CHANGE_?ME",
            "XXXX",
            "EXAMPLE",
            "SAMPLE",
            "DUMMY",
            "REDACT",
            "PLACEHOLDER",
            "NOT_?A_?SECRET",
            "TODO",
            "YOUR[-_]",
            "<",
            r"\{\{",
        ]
    ),
    re.IGNORECASE,
)

# Assembled from fragments on purpose. A pattern spelled out literally would
# match this very file, and the gate checks its own source.
_ALNUM_UPPER = "[0-9A-Z]"
_B64ISH = "[A-Za-z0-9_-]"

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"-----BEGIN [A-Z0-9 ]{0,32}PRIVATE KEY-----"),
        "PEM private key block",
    ),
    (
        re.compile(r"PuTTY-User-Key-File-\d"),
        "PuTTY private key file",
    ),
    (
        re.compile(r"\b(?:AKIA|ASIA)" + _ALNUM_UPPER + "{16}\\b"),
        "AWS access key id",
    ),
    (
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
        "GitHub token",
    ),
    (
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
        "GitHub fine-grained personal access token",
    ),
    (
        re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
        "Slack token",
    ),
    (
        re.compile(r"\bAIza" + _B64ISH + "{35}\\b"),
        "Google API key",
    ),
    (
        re.compile(r"\b[Bb]earer\s+[A-Za-z0-9._~+/=-]{20,}"),
        "bearer token",
    ),
    (
        re.compile(
            r"(?i)\b(?:api[_-]?keys?|apikeys?|secrets?|tokens?|passwords?"
            r"|passwd|pwd|access[_-]?keys?|private[_-]?keys?"
            r"|client[_-]?secrets?|auth[_-]?tokens?)\b"
            r"\s*(?:[:=]|=>)\s*"
            r"[\"']([^\"'\n]{16,})[\"']"
        ),
        "credential assigned a quoted literal of 16 or more characters",
    ),
    (
        re.compile(
            r"(?i)\b\w*(?:key|token|secret)\w*\b\s*(?:[:=]|=>)\s*"
            r"([A-Fa-f0-9]{32,}"
            # The base64-shaped branch requires at least TWO digits. Without that,
            # any long camelCase identifier after a word containing "key" matches -
            # e.g. "KEY: mProductionBoostPowerConsumptionExponent" in a spike report,
            # which blocked a real commit and was a pure false positive. A gate that
            # fires on ordinary prose gets overridden, and an overridden gate is dead.
            # Real base64 and hex credentials effectively always carry digits.
            r"|(?=[A-Za-z+/]*[0-9][A-Za-z0-9+/]*[0-9])[A-Za-z0-9+/]{40,}={0,2}"
            r")(?![\w=])"
        ),
        "credential assigned a bare high-entropy literal",
    ),
]


def check_secrets(label: str, text: str, report: Report) -> None:
    """Scan for credential shapes, allowlisting obvious placeholders."""
    for lineno, line in enumerate(text.split("\n"), 1):
        for pattern, reason in SECRET_PATTERNS:
            for match in pattern.finditer(line):
                candidate = match.group(match.lastindex or 0)
                if PLACEHOLDER_RE.search(candidate):
                    continue
                report.add(
                    Diagnostic(
                        label,
                        lineno,
                        match.start() + 1,
                        "SECRET",
                        reason,
                    )
                )


# --------------------------------------------------------------------------
# PII
# --------------------------------------------------------------------------

# Assembled from fragments so the literal home-path prefixes never appear in
# this file. This gate checks its own source; a literal here would block it.
_HOME_DIR_NAMES = ("home", "Users")

PII_WIN_HOME_RE = re.compile(rf"[A-Za-z]:[\\/]+{_HOME_DIR_NAMES[1]}[\\/]+([A-Za-z0-9 ._-]+)")
PII_NIX_HOME_RE = re.compile(
    r"(?<![A-Za-z0-9_.])/(?:{})/([A-Za-z0-9._-]+)".format("|".join(_HOME_DIR_NAMES))
)

# Account names too generic to match on: a CI container running as `user` or
# `runner` would otherwise flag half the repository. Reported by
# --list-skipped so the exemption is never invisible.
GENERIC_ACCOUNT_NAMES = frozenset(
    {
        "user",
        "users",
        "admin",
        "root",
        "test",
        "runner",
        "build",
        "ci",
        "guest",
        "default",
        "public",
        "owner",
        "home",
    }
)

SAVE_ROOT_PARTS = ("FactoryGame", "Saved", "SaveGames")

# Override surface. The three names clockspeed/data/locate.py already honours
# are read here under exactly those names, so the two resolvers cannot drift
# apart on the inputs they share; the two world names are new and are owned by
# this gate. Nothing below is a VALUE - every one of these is the name of a
# place a value may be found at runtime (CLAUDE.md non-negotiable 3).
ENV_SAVE_ROOT = "CLOCKSPEED_SAVE_ROOT"
ENV_ACCOUNT_DIR = "CLOCKSPEED_ACCOUNT_DIR"
ENV_LOCAL_CONFIG = "CLOCKSPEED_LOCAL_CONFIG"
ENV_WORLD_NAMES = "CLOCKSPEED_WORLD_NAMES"
ENV_WORLD_TOKENS = "CLOCKSPEED_WORLD_TOKENS"

# The sixth override, and the only SUBTRACTIVE one: it names world values that
# were discovered correctly and that the operator has decided not to block on.
# See EXCLUSION SURFACE below for why subtracting per value is the only shape
# that was allowed.
ENV_WORLD_NAME_EXCLUSIONS = "CLOCKSPEED_WORLD_NAME_EXCLUSIONS"

# The seventh name, and the only one that is not about a discovered value at
# all: it opts IN to printing the crash traceback that the handler at the foot
# of this file suppresses by default. See the module docstring.
ENV_CRASH_TRACEBACK = "CLOCKSPEED_CRASH_TRACEBACK"

CONFIG_ACCOUNT_DIR = "account_dir"
CONFIG_WORLD_NAMES = "world_names"
CONFIG_WORLD_TOKENS = "world_tokens"

# EXCLUSION SURFACE (CS-209), and the shape of it is a measurement rather than
# a preference. CS-208 proposed raising the world-name length floor to suppress
# a false positive and was DENIED BY MEASUREMENT on 2026-08-14: 16 matchable
# world names exist on the operator's machine and the shortest is 4 characters,
# so any floor at or above 5 drops a REAL world name and it then commits.
# Narrowing a PII blocklist BY DEFAULT trades a diagnosable fail-closed for a
# certain fail-open. This key does the opposite: it subtracts ONE value the
# operator named, leaving every sibling matching, and it announces the
# subtraction through the skip channel on every run.
CONFIG_WORLD_NAME_EXCLUSIONS = "world_name_exclusions"

# config/local.json is gitignored, by `config/local.json` and again by the
# `*.local.json` pattern beside it. That is what makes it the right place for
# a declared world value: it is machine-local and it cannot be committed.
LOCAL_CONFIG_RELATIVE = ("config", "local.json")
MAX_LOCAL_CONFIG_BYTES = 64_000

# Skip labels. A skip is how an exemption stays visible instead of silent
# (CONVENTIONS.md section 15.1), so every filter below reports through one.
PII_ACCOUNT_ID_LABEL = "<pii:account-id>"
PII_ACCOUNT_NAME_LABEL = "<pii:account-name>"
PII_WORLD_LABEL = "<pii:world>"

# COVERAGE SKIPS versus VOLUME SKIPS, and the split is what makes the promise
# above true rather than merely written down (CS-209).
#
# The three labels here mean "this gate's own DETECTION was reduced" - a value
# was discovered and then dropped, or was never discoverable at all. Every
# other skip means "this UNIT was not read", which is volume: its count is
# already on the PASS line and the paths are one flag away.
#
# emit() prints the coverage skips UNCONDITIONALLY, because .githooks/pre-commit
# runs the gate with neither --verbose nor --list-skipped. Until CS-209 the
# skipped channel printed under those flags only, every test in the suite
# passed them explicitly, and so the claim that a dropped value stays visible
# was FALSE on the one path that actually gates a commit. Printing the volume
# skips there too would put a line per unchecked asset in front of the operator
# on every commit, and a gate that becomes noise is a gate that gets turned off.
COVERAGE_SKIP_LABELS = frozenset({PII_ACCOUNT_ID_LABEL, PII_ACCOUNT_NAME_LABEL, PII_WORLD_LABEL})

# Shorter than this and a whole-word match on the account name would flag
# ordinary prose more often than it would catch a leak. World names route
# through this SAME floor: a world called "Ab" is not matchable either.
MIN_ACCOUNT_NAME_CHARS = 3

# An account directory name shorter than this is not an id on any platform.
# This replaces the old digit-count floor, which was quietly doing two jobs at
# once - the id-shape test AND the matchability filter - so removing the
# all-digits test beside it would have left the second job undone and widened
# the blocklist with nothing filtering it.
MIN_ACCOUNT_DIR_CHARS = 8

# A declared world token is matched verbatim, so it needs a floor of its own.
MIN_WORLD_TOKEN_CHARS = 8

# The save root is listed one level deep and no deeper, and the listing stops
# here. A gate that hangs is a gate that gets turned off.
MAX_SAVE_ROOT_ENTRIES = 512

# The two bounds on the header scan CS-403 added, and they exist for the same
# reason as the entry cap above. The game keeps a rotating autosave set, so a
# long-running world leaves dozens of .sav files in one directory; parsing all
# of them on every commit would turn a gate into a bulk reader. Whichever bound
# trips first, the remainder is REPORTED rather than silently dropped.
MAX_SAVE_HEADER_FILES = 24
SAVE_HEADER_BUDGET_SECONDS = 5.0

# Directory names that sit BESIDE an account directory without being one.
# Separate from GENERIC_ACCOUNT_NAMES because the two lists answer different
# questions and would otherwise drift into one blurred list: this one is
# "names found under a save root", that one is "login names".
GENERIC_SAVE_ROOT_DIRS = frozenset(
    {
        "archive",
        "archives",
        "backup",
        "backups",
        "blueprints",
        "cache",
        "common",
        "logs",
        "old",
        "savegames",
        "saves",
        "screenshots",
        "server",
        "servers",
        "shared",
        "temp",
        "tmp",
    }
)

# A save filename, with the optional second suffix the game writes for a
# rotated copy. Anchored at both ends: this matches a whole basename, never a
# fragment of one.
_SAVE_FILE_RE = re.compile(r"^(?P<stem>.+?)\.sav(?:\.[A-Za-z0-9]{1,8})?$", re.IGNORECASE)

# The rotation suffix the game appends to an autosave. Deliberately narrow -
# a looser rule would strip a real part of a world name and add a SHORTER
# blocklist entry than the operator ever chose, which is how a whole-word
# blocklist starts flagging prose.
_ROTATION_SUFFIX_RE = re.compile(r"_autosave_\d+$", re.IGNORECASE)


def save_root() -> Path | None:
    """Locate the platform save root without hardcoding any path."""
    override = os.environ.get(ENV_SAVE_ROOT)
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    if not base:
        return None
    return Path(base).joinpath(*SAVE_ROOT_PARTS)


def _repo_root() -> Path:
    """This checkout's root, derived from this file's own location."""
    return Path(__file__).resolve().parents[1]


def local_config() -> dict[str, str]:
    """Read this machine's gitignored local configuration, if it has one.

    A SECOND reader of config/local.json - clockspeed/data/locate.py owns the
    canonical one - and the duplication is deliberate rather than an oversight.
    This gate is the one tool that must run in a checkout where nothing is
    installed and where the package may be mid-edit and not importable at all.
    Importing the data layer here would make the commit gate fail whenever an
    unrelated module was broken, and a gate that cannot start does not block.
    clockspeed/data/locate.py records the same split at its own module head.

    Absence, an implausible size, unreadable bytes and malformed JSON are all
    the normal case and all mean the same thing: no local config.

    Returns:
        The string-valued entries, or an empty mapping. Never raises.
    """
    override = os.environ.get(ENV_LOCAL_CONFIG)
    path = Path(override) if override else _repo_root().joinpath(*LOCAL_CONFIG_RELATIVE)
    try:
        if not path.is_file() or path.stat().st_size > MAX_LOCAL_CONFIG_BYTES:
            return {}
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    try:
        payload = json.loads(raw)
    except ValueError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, str)}


def declared_values(env_name: str, config_key: str) -> list[str]:
    """Read an operator declaration: the environment first, the config second.

    Comma separated, because a machine has many worlds where it has only one
    save root. An empty declaration is not an error; it is the normal case.

    Args:
        env_name: Environment variable to read first.
        config_key: config/local.json key to read when the variable is unset.

    Returns:
        The declared values, whitespace trimmed, empties dropped.
    """
    raw = (os.environ.get(env_name) or "").strip()
    if not raw:
        raw = (local_config().get(config_key) or "").strip()
    return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]


def _matchable(value: str, minimum: int, generic: frozenset[str]) -> str | None:
    """Judge whether a discovered value is safe to match as a whole word.

    Returns:
        None when the value is fine, otherwise the reason it was dropped. The
        reason NEVER contains the value: a skip line that prints what it
        skipped is itself an echo path (CLAUDE.md non-negotiable 12). That
        constraint got STRICTER with CS-209, not looser - these reasons now
        print on every commit rather than only under --list-skipped, so a
        reason that echoed its value would leak on the busiest path there is.
    """
    if len(value) < minimum:
        return "a discovered value of %d character(s) is too short to match safely" % len(value)
    if value.lower() in generic:
        return "a discovered value is a generic word; whole-word match would flag ordinary prose"
    return None


def _save_root_dirs(report: Report | None) -> list[Path]:
    """List the save root's immediate subdirectories. READ-ONLY and bounded.

    The save directory is never written to and never opened for write
    (CLAUDE.md non-negotiable 1). Only entry NAMES are read here; no file is
    opened at all.

    Returns:
        The subdirectories, or an empty list. Every reason for an empty list is
        reported rather than swallowed.
    """
    root = save_root()
    if root is None:
        _report_skip(report, PII_ACCOUNT_ID_LABEL, "no LOCALAPPDATA in the environment")
        return []
    found: list[Path] = []
    try:
        if not root.is_dir():
            _report_skip(report, PII_ACCOUNT_ID_LABEL, "save root does not exist on this machine")
            return []
        for index, entry in enumerate(sorted(root.iterdir(), key=lambda item: item.name)):
            if index >= MAX_SAVE_ROOT_ENTRIES:
                _report_skip(
                    report,
                    PII_ACCOUNT_ID_LABEL,
                    "save root holds more than %d entries; the rest were not read"
                    % MAX_SAVE_ROOT_ENTRIES,
                )
                break
            if entry.is_dir():
                found.append(entry)
    except OSError as exc:
        _report_skip(report, PII_ACCOUNT_ID_LABEL, "save root unreadable: " + safe_exc_text(exc))
        return []
    return found


def _report_skip(report: Report | None, label: str, why: str) -> None:
    """Record a skip when there is a report to record it on."""
    if report is not None:
        report.skip(label, why)


def discover_account_ids(report: Report | None = None) -> list[str]:
    """Discover account directory names under the save root, at runtime.

    NOT `.isdigit()`, and that is the whole point of this function's shape.
    An account directory is identified by WHERE it sits - immediately below the
    save root - and never by what it is made of, because only one of the three
    shipping platforms writes digits there: Epic writes a hex token and the
    Microsoft Store a braceless GUID. A digits-only filter recognised one
    platform out of three and let the other two reach a commit unblocked.
    clockspeed/data/locate.py keeps its own `.isdigit()` filter and that
    asymmetry is deliberate - that site SELECTS which world to read, and
    widening a selector makes the resolver silently pick the wrong world. This
    gate only widens what it REFUSES to commit, so it is meant to be wider.

    Widening the filter widens a whole-word blocklist, so the widening arrives
    with a filter of its own. A name that is not matchable is dropped and the
    drop is REPORTED, never silent:

        too short       a short name matched as a whole word flags prose
        generic         "backup" beside the account directory is not an id
        no digit        every id shape carries digits; ordinary words do not

    That last test is the deliberate opposite of `.isdigit()`: that one asked
    whether EVERY character was a digit, this asks whether ANY is. It admits
    all three id shapes and rejects the English words a save root collects.
    An operator-DECLARED account directory skips it entirely, exactly as
    clockspeed/data/locate.py declines to shape-check its own override - the
    override exists precisely for a directory that does not look like the
    default, and rejecting it would break the case it is for.

    BOOTSTRAP.md section 2.2: the platform account id is personal data and must
    never be written down. It is therefore never written down here. It is
    discovered, and no code path below prints it.
    """
    found: list[str] = []
    for value in declared_values(ENV_ACCOUNT_DIR, CONFIG_ACCOUNT_DIR):
        name = PurePosixPath(value.replace("\\", "/")).name or value
        reason = _matchable(name, MIN_ACCOUNT_DIR_CHARS, GENERIC_ACCOUNT_NAMES)
        if reason is None:
            found.append(name)
        else:
            _report_skip(report, PII_ACCOUNT_ID_LABEL, "declared account directory: " + reason)

    for entry in _save_root_dirs(report):
        name = entry.name
        reason = _matchable(
            name, MIN_ACCOUNT_DIR_CHARS, GENERIC_ACCOUNT_NAMES | GENERIC_SAVE_ROOT_DIRS
        )
        if reason is not None:
            _report_skip(
                report,
                PII_ACCOUNT_ID_LABEL,
                "save-root subdirectory is not an account id: " + reason,
            )
            continue
        if not any(char.isdigit() for char in name):
            _report_skip(
                report,
                PII_ACCOUNT_ID_LABEL,
                "save-root subdirectory is not an account id: it carries no digit, "
                "and every platform id shape does",
            )
            continue
        found.append(name)

    if report is not None and not found:
        report.skip(PII_ACCOUNT_ID_LABEL, "no account directory is discoverable on this machine")
    return sorted(set(found))


def discover_world_names(report: Report | None = None) -> list[str]:
    """Discover this machine's world names, at runtime, from three sources.

    NEVER a literal. This gate is a tracked file and a world name is personal
    data (CLAUDE.md non-negotiable 3), so no world value is written down here.
    It is discovered, exactly as the account name and the account id are.

    Sources, highest precedence first:

      1. CLOCKSPEED_WORLD_NAMES, comma separated.
      2. "world_names" in config/local.json, which is gitignored.
      3. The `.sav` basenames under the save root, read READ-ONLY, names only.

    Source 3 is the one that needs no setup, which is what makes it the source
    that protects a machine nobody configured. Its blind spot is worth naming:
    it sees a world that has been SAVED, so a world renamed since its last save
    is matched under the old name and not the new one.

    Every discovered name goes through the same two filters that already
    protect the account name - a length floor and the generic-name list -
    because a world called "test" must not blocklist the word "test" across the
    whole repository. A dropped name is reported, never silently ignored.

    A FOURTH filter runs LAST and subtracts rather than narrows: a name the
    operator listed under CONFIG_WORLD_NAME_EXCLUSIONS is dropped AFTER it has
    been discovered. After, not during, and the ordering is the whole design.
    Narrowing discovery to pre-empt a collision was CS-208 and was denied by
    measurement; subtracting one named value leaves every sibling matching and
    leaves the drop visible.
    """
    candidates = list(declared_values(ENV_WORLD_NAMES, CONFIG_WORLD_NAMES))
    for directory in [*_save_root_dirs(None), *_declared_account_dirs()]:
        candidates.extend(_world_names_from_saves(directory))

    excluded = _world_name_exclusions()
    dropped_by_exclusion = False
    found: list[str] = []
    for value in candidates:
        reason = _matchable(value, MIN_ACCOUNT_NAME_CHARS, GENERIC_ACCOUNT_NAMES)
        if reason is not None:
            _report_skip(report, PII_WORLD_LABEL, "world name: " + reason)
            continue
        if value.casefold() in excluded:
            dropped_by_exclusion = True
            _report_skip(
                report,
                PII_WORLD_LABEL,
                "a discovered world name is excluded by the %s key; remove it from "
                "there to block on that name again" % CONFIG_WORLD_NAME_EXCLUSIONS,
            )
            continue
        found.append(value)

    # `not dropped_by_exclusion` is load bearing and was found by reading a
    # real transcript rather than by reasoning. When every discovered name is
    # excluded, `found` is empty but the ADVICE below is false: the operator
    # has already declared a name, and this line would sit directly under the
    # exclusion skip contradicting it. Two skip lines that disagree teach a
    # reader to stop reading the channel - which CS-209 cannot afford, since
    # printing this channel on the authoritative path IS the item.
    if report is not None and not found and not dropped_by_exclusion:
        report.skip(
            PII_WORLD_LABEL,
            "no world name is discoverable on this machine; set %s or add %s to "
            "config/local.json to enable this check" % (ENV_WORLD_NAMES, CONFIG_WORLD_NAMES),
        )
    return sorted(set(found))


def _world_name_exclusions() -> frozenset[str]:
    """The world names the operator has opted OUT of blocking on.

    CASE FOLDED, because the matcher these exempt is built with re.IGNORECASE.
    An exclusion that compared case-sensitively would read as working and do
    nothing whenever the operator typed the name with different capitalisation
    than the `.sav` basename carries - which is the normal case, since one is
    typed and the other is generated.

    Returns:
        The folded exclusions. Empty is the normal case and is not an error.
    """
    return frozenset(
        value.casefold()
        for value in declared_values(ENV_WORLD_NAME_EXCLUSIONS, CONFIG_WORLD_NAME_EXCLUSIONS)
    )


def _declared_account_dirs() -> list[Path]:
    """Resolve an operator-declared account directory to a path to list.

    An override may be a bare directory name, joined onto the save root, or an
    absolute path used as given - a copied or moved account directory still
    works that way. Mirrors clockspeed/data/locate.py.
    """
    root = save_root()
    resolved: list[Path] = []
    for value in declared_values(ENV_ACCOUNT_DIR, CONFIG_ACCOUNT_DIR):
        candidate = Path(value)
        if not candidate.is_absolute():
            if root is None:
                continue
            candidate = root / value
        resolved.append(candidate)
    return resolved


def _world_names_from_saves(directory: Path) -> list[str]:
    """Read world names out of the `.sav` basenames in one directory.

    READ-ONLY: this lists entry names and opens nothing. Any failure returns an
    empty list, because a save directory that cannot be listed is the same
    situation as a machine with no game installed.
    """
    names: list[str] = []
    try:
        for index, entry in enumerate(directory.iterdir()):
            if index >= MAX_SAVE_ROOT_ENTRIES:
                break
            match = _SAVE_FILE_RE.match(entry.name)
            if match is None:
                continue
            stem = match.group("stem")
            names.append(stem)
            bare = _ROTATION_SUFFIX_RE.sub("", stem)
            if bare != stem:
                names.append(bare)
    except OSError:
        return names
    return names


def _load_header_reader() -> object:
    """Import the save-header reader LAZILY, and never at module scope.

    THIS FUNCTION IS THE ENTIRE RISK OF CS-403, so the reasoning lives here
    rather than in a document that will drift away from it.

    The seam direction is fine and was settled by reading the line rather than
    by assuming: docs/ARCHITECTURE.md prohibits clockspeed/ importing tools/,
    and NOT the reverse. tools/drift_guard.py already lazily imports
    clockspeed.data.* and records that same direction as correct.

    What is NOT fine is importing a product module at STARTUP. This gate has to
    run in a checkout where nothing is installed and where the package may be
    mid-edit and not importable at all, and A GATE THAT CANNOT START DOES NOT
    BLOCK - it is the one failure a gate must not have. So the import sits
    inside a function that main() reaches long after the module body has
    finished executing, and every caller treats failure as an ordinary skip.

    The path insertion is needed because the gate runs as
    `python tools/precommit_gate.py`, which puts tools/ on sys.path and not the
    repository root, so `clockspeed` does not resolve on its own. The entry is
    removed again immediately, so the shadowing window is this one import - and
    the repository root holds no top-level module that could shadow a standard
    library name anyway.

    Returns:
        The ``read_header`` callable.

    Raises:
        BaseException: Whatever the import raised. Callers catch it; nothing is
            handled here, because a partial recovery would hide which of the
            several failure modes actually occurred.
    """
    root = str(_repo_root())
    inserted = root not in sys.path
    if inserted:
        sys.path.insert(0, root)
    try:
        # The suppression below is the entire point of this function.
        # Hoisting this import to module scope is the one edit it exists to
        # prevent, so the rule that would demand exactly that is silenced HERE
        # and nowhere else in the file.
        from clockspeed.save.header import read_header  # noqa: PLC0415
    finally:
        if inserted and root in sys.path:
            sys.path.remove(root)
    return read_header


def _save_files(directory: Path) -> list[Path]:
    """The `.sav` paths in one directory. READ-ONLY, name-listing only.

    NEWEST FIRST, tie-broken by name. The ordering is load bearing rather than
    cosmetic: MAX_SAVE_HEADER_FILES truncates this list, and the worlds most
    likely to have their token pasted into a commit are the ones just played.
    Truncating alphabetically would silently drop the recent ones. The name is
    the tie-break so the order is deterministic when two files share an mtime,
    which is the normal case in a test and the rare case on a real machine.

    Any failure yields what was collected so far: a save directory that cannot
    be listed is the same situation as a machine with no game installed.
    """
    found: list[Path] = []
    try:
        for index, entry in enumerate(sorted(directory.iterdir(), key=lambda item: item.name)):
            if index >= MAX_SAVE_ROOT_ENTRIES:
                break
            if _SAVE_FILE_RE.match(entry.name) and entry.is_file():
                found.append(entry)
    except OSError:
        return found

    def sort_key(path: Path) -> tuple[float, str]:
        try:
            modified = path.stat().st_mtime
        except OSError:
            modified = 0.0
        return (-modified, path.name)

    return sorted(found, key=sort_key)


def _world_tokens_from_headers(report: Report | None) -> list[str]:
    """Read world tokens out of the save headers under the save root.

    CS-403, and it closes the gap the docstring below used to record as an
    honest limit. No second parser was grown here: this calls the one in
    clockspeed/save/header.py, which reads a bounded prefix, opens READ ONLY,
    and steps over the personal-data strings rather than decoding them.

    EVERY failure mode is a skip and none of them is fatal. The reader may be
    unimportable, the save root may be absent, a `.sav` may be truncated,
    half-written by an autosave in progress, or not a save at all. The scan is
    bounded twice, by MAX_SAVE_HEADER_FILES and by SAVE_HEADER_BUDGET_SECONDS,
    and whichever bound trips says so.

    Returns:
        The tokens read, unfiltered. Never raises.
    """
    started = time.monotonic()
    try:
        read_header = _load_header_reader()
    # BaseException, not Exception, and deliberately: a mid-edit module that
    # calls sys.exit() at import time raises SystemExit, and letting that
    # through would end the gate with the wrong exit code - the exact
    # fail-to-start the grant forbids.
    except BaseException as exc:
        _report_skip(
            report,
            PII_WORLD_LABEL,
            "the save-header reader is not importable from this checkout, so a "
            "token is matchable only when declared (" + safe_exc_text(exc) + ")",
        )
        return []

    paths: list[Path] = []
    for directory in [*_save_root_dirs(None), *_declared_account_dirs()]:
        paths.extend(_save_files(directory))

    if len(paths) > MAX_SAVE_HEADER_FILES:
        _report_skip(
            report,
            PII_WORLD_LABEL,
            "more save files than the %d-file cap; the headers past it were not "
            "read and their tokens are not matchable" % MAX_SAVE_HEADER_FILES,
        )
        paths = paths[:MAX_SAVE_HEADER_FILES]

    found: list[str] = []
    unreadable = 0
    for path in paths:
        if time.monotonic() - started > SAVE_HEADER_BUDGET_SECONDS:
            _report_skip(
                report,
                PII_WORLD_LABEL,
                "the %.1f second save-header budget was spent; the remaining "
                "headers were not read" % SAVE_HEADER_BUDGET_SECONDS,
            )
            break
        try:
            found.append(read_header(path).world_token)  # type: ignore[operator]
        except BaseException:
            # A bad save is the NORMAL case, never fatal (non-negotiable 7).
            # The exception text is NOT rendered. Every header exception in
            # that module carries a redacted path, but "redacted by the code
            # under test" is not an oracle a PII gate may rely on, and the
            # filename it would name embeds the world name.
            unreadable += 1

    if unreadable:
        _report_skip(
            report,
            PII_WORLD_LABEL,
            "%d save header(s) under the save root could not be parsed; their "
            "tokens are not matchable" % unreadable,
        )
    return found


def discover_world_tokens(report: Report | None = None) -> list[str]:
    """Discover this machine's world tokens, at runtime, from three sources.

    Sources, highest precedence first:

      1. CLOCKSPEED_WORLD_TOKENS, comma separated.
      2. "world_tokens" in config/local.json, which is gitignored.
      3. The save HEADERS under the save root, read through the parser in
         clockspeed/save/header.py.

    Source 3 is CS-403 and it is what makes an UNDECLARED token matchable. It
    replaces the honest limit this docstring used to record - that a token
    lives in the header, that this gate held no parser, and that an undeclared
    token was therefore unmatched and would commit. The limit is not gone so
    much as moved: on a checkout where the package cannot be imported the gate
    degrades to sources 1 and 2, exactly as before, and SAYS SO through the
    skip channel. Sources 1 and 2 keep working in that state - the fallback
    degrades the header source alone and never the whole check.

    Matching is case SENSITIVE, unlike a world name. A token is generated
    rather than typed, so a case-folded match would only widen the false
    positives without catching anything a case-sensitive match misses.
    """
    found: list[str] = []
    for value in declared_values(ENV_WORLD_TOKENS, CONFIG_WORLD_TOKENS):
        reason = _matchable(value, MIN_WORLD_TOKEN_CHARS, GENERIC_ACCOUNT_NAMES)
        if reason is None:
            found.append(value)
        else:
            _report_skip(report, PII_WORLD_LABEL, "world token: " + reason)

    for value in _world_tokens_from_headers(report):
        reason = _matchable(value, MIN_WORLD_TOKEN_CHARS, GENERIC_ACCOUNT_NAMES)
        if reason is None:
            found.append(value)
        else:
            _report_skip(report, PII_WORLD_LABEL, "world token from a save header: " + reason)

    if report is not None and not found:
        report.skip(
            PII_WORLD_LABEL,
            "no world token is discoverable on this machine; set %s or add %s to "
            "config/local.json" % (ENV_WORLD_TOKENS, CONFIG_WORLD_TOKENS),
        )
    return sorted(set(found))


def current_account_names(report: Report | None = None) -> list[str]:
    """Read this machine's account name from the environment, at runtime.

    Never hardcoded (BOOTSTRAP.md section 12 item 3). Names that are too short
    or too generic to match safely are dropped, and the drop is recorded as a
    skip so the exemption shows up in --list-skipped instead of being silent.
    """
    names = []
    for key in ("USERNAME", "USER"):
        value = (os.environ.get(key) or "").strip()
        if not value or value in names:
            continue
        if len(value) < MIN_ACCOUNT_NAME_CHARS:
            if report is not None:
                report.skip(
                    PII_ACCOUNT_NAME_LABEL,
                    "%s=<%d chars> is too short to match safely" % (key, len(value)),
                )
            continue
        if value.lower() in GENERIC_ACCOUNT_NAMES:
            if report is not None:
                report.skip(
                    PII_ACCOUNT_NAME_LABEL,
                    f"{key} is a generic account name; whole-word match would flag ordinary prose",
                )
            continue
        names.append(value)
    return names


def _word_res(values: list[str], fold: bool) -> list[re.Pattern[str]]:
    """Compile whole-word matchers for discovered values.

    Every pattern is built with re.escape from a value found at runtime, which
    is what keeps this gate free of the literals it exists to catch - and what
    lets it check its own source without blocking itself.

    Args:
        values: Discovered values.
        fold: Match case-insensitively. True for a name a human typed, False
            for a generated token, where folding widens false positives
            without catching anything a sensitive match misses.
    """
    flags = re.IGNORECASE if fold else 0
    return [
        re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(value)}(?![A-Za-z0-9_-])", flags)
        for value in values
    ]


class PiiMatchers:
    """Runtime-built PII matchers. Never constructed from a literal."""

    def __init__(self, report: Report | None = None) -> None:
        """Discover this machine's account name, account id and world values."""
        self.account_names = current_account_names(report)
        self.account_ids = discover_account_ids(report)
        self.world_names = discover_world_names(report)
        self.world_tokens = discover_world_tokens(report)
        self.name_res = _word_res(self.account_names, fold=True)
        self.id_res = _word_res(self.account_ids, fold=False)
        self.world_name_res = _word_res(self.world_names, fold=True)
        self.world_token_res = _word_res(self.world_tokens, fold=False)


def check_pii(label: str, text: str, matchers: PiiMatchers, report: Report) -> None:
    """Scan for home paths and for this machine's account name and id."""
    for lineno, line in enumerate(text.split("\n"), 1):
        for match in PII_WIN_HOME_RE.finditer(line):
            report.add(
                Diagnostic(
                    label,
                    lineno,
                    match.start() + 1,
                    "PII",
                    "absolute Windows home path; auto-detect it at runtime "
                    "instead (CONVENTIONS.md section 10)",
                )
            )
        for match in PII_NIX_HOME_RE.finditer(line):
            report.add(
                Diagnostic(
                    label,
                    lineno,
                    match.start() + 1,
                    "PII",
                    "absolute POSIX home path; auto-detect it at runtime "
                    "instead (CONVENTIONS.md section 10)",
                )
            )
        for patterns, reason in _discovered_rules(matchers):
            for pattern in patterns:
                for match in pattern.finditer(line):
                    report.add(Diagnostic(label, lineno, match.start() + 1, "PII", reason))


def _discovered_rules(matchers: PiiMatchers) -> list[tuple[list[re.Pattern[str]], str]]:
    """Pair each set of runtime-discovered matchers with the reason it blocks.

    The reasons never quote the value they matched. A diagnostic is printed to
    a terminal and pasted into issues, so a diagnostic that echoes the personal
    data it found is the same leak in a different costume (CLAUDE.md
    non-negotiable 12). The LABEL and the line:column say where to look.

    The world-name reason carries a REMEDY (CS-209), and naming the key is the
    point of it. A diagnostic that says "this is personal data" and stops
    leaves an operator with a red gate, a true positive they cannot act on and
    a false positive they cannot clear, and the move available to them then is
    --no-verify. The remedy names the key and never the value.
    """
    return [
        (matchers.name_res, "this machine's account name appears as a whole word"),
        (
            matchers.id_res,
            "platform account id discovered under the save root (BOOTSTRAP.md section 2.2)",
        ),
        (
            matchers.world_name_res,
            "a world name discovered on this machine appears as a whole word "
            "(CLAUDE.md non-negotiable 3); if that is a false positive, add the "
            "name to the %s key in config/local.json, which is gitignored"
            % CONFIG_WORLD_NAME_EXCLUSIONS,
        ),
        (
            matchers.world_token_res,
            # Not "declared": since CS-403 a token is also read out of a save
            # header, so a reason naming only the declaration source would
            # send a reader looking in config/local.json for a value that is
            # not there.
            "a world token for this machine appears (CLAUDE.md non-negotiable 3)",
        ),
    ]


# --------------------------------------------------------------------------
# Path-level checks
# --------------------------------------------------------------------------


def check_path(label: str, report: Report) -> bool:
    """Path-only checks. Returns False when the path itself is a violation."""
    ok = True
    pure = PurePosixPath(label.replace("\\", "/"))
    name = pure.name
    lowered = name.lower()
    suffix = pure.suffix.lower()

    if suffix in PUBLISHER_EXTS or lowered in PUBLISHER_NAMES:
        report.add(
            Diagnostic(
                label,
                0,
                0,
                "PUBLISHER",
                "publisher-owned game artifact must never be committed "
                "(BOOTSTRAP.md section 8.1); .gitignore does not stop "
                "`git add -f`, this does",
            )
        )
        ok = False

    parts = pure.parts
    if parts and not pure.is_absolute() and parts[0] in PUBLISHER_ROOT_DIRS:
        report.add(
            Diagnostic(
                label,
                0,
                0,
                "PUBLISHER",
                "path is under the root-anchored generated/corpus directory "
                f"'{parts[0]}/', which is gitignored and must stay untracked",
            )
        )
        ok = False

    if any(ord(ch) > MAX_ASCII for ch in label):
        offending = next(ch for ch in label if ord(ch) > MAX_ASCII)
        report.add(
            Diagnostic(
                label,
                0,
                label.index(offending) + 1,
                "CHARSET",
                "non-ASCII character in the path itself: " + describe_codepoint(offending),
            )
        )
        ok = False

    return ok


# --------------------------------------------------------------------------
# Python syntax
# --------------------------------------------------------------------------


def check_python_syntax(label: str, data: bytes, report: Report) -> None:
    """compile() the source; a syntax error blocks the commit."""
    text, _ = decode_for_report(data)
    try:
        compile(text, label, "exec")
    except SyntaxError as exc:
        report.add(
            Diagnostic(
                label,
                exc.lineno or 0,
                exc.offset or 0,
                "SYNTAX",
                "python syntax error: %s" % (safe_exc_text(exc),),
            )
        )
    except ValueError as exc:
        report.add(
            Diagnostic(label, 0, 0, "SYNTAX", "python source rejected: " + safe_exc_text(exc))
        )


# --------------------------------------------------------------------------
# Lint
# --------------------------------------------------------------------------

# The classic "real error" selection. Everything else ruff reports is style
# and is printed but never blocks, so the gate stays usable.
RUFF_BLOCKING_PREFIXES = ("E9", "F63", "F7", "F82")

# Advisory findings are listed up to this many, then counted. An unreadable
# wall of style notes is a wall nobody reads.
MAX_STYLE_NOTES = 20


def ruff_command() -> list[str] | None:
    """Locate ruff on PATH, else as an importable module, else None."""
    found = which("ruff")
    if found:
        return [found]
    try:
        # A probe, not a dependency: importing at module scope would make the
        # gate refuse to start on a machine without ruff.
        import ruff  # noqa: F401, PLC0415
    except ImportError:
        return None
    return [sys.executable, "-m", "ruff"]


def ruff_config_args(root: Path | None) -> list[str]:
    """Point ruff at the project's own config.

    Only needed for units linted as temp copies (--staged, where the checked
    bytes are the INDEX bytes and so cannot be linted in place). Ruff's upward
    config discovery finds nothing beside a temp file and would silently fall
    back to its defaults, making the hook disagree with CI about which rules
    exist. Passing the repo's config explicitly closes most of that gap.

    Known limitation, stated rather than hidden: per-file-ignores are globs
    resolved against the project root, so a temp copy never matches
    `tools/**` or `tests/**`. That makes --staged report MORE advisory style
    findings than CI would, never fewer, and it cannot change what blocks -
    the blocking band is RUFF_BLOCKING_PREFIXES, which no per-file-ignore in
    this project touches.
    """
    if root is None:
        return []
    for name in ("ruff.toml", ".ruff.toml"):
        candidate = root / name
        if candidate.is_file():
            return ["--config", str(candidate)]
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        # ruff errors out on a pyproject with no [tool.ruff] table.
        if "[tool.ruff" in text:
            return ["--config", str(pyproject)]
    return []


def normalized_key(path: str) -> str:
    """Case-folded absolute key, for matching ruff's reported filenames."""
    return os.path.normcase(str(Path(path).resolve()))


def stage_for_lint(
    targets: list[Unit], tmp: Path, report: Report
) -> tuple[list[str], dict[str, str]]:
    """Resolve each unit to a path ruff can read, and map it back to its label.

    A unit whose checked bytes are exactly what is on disk is linted IN PLACE,
    so ruff resolves the project config and its per-file-ignores the same way
    CI does. Only index bytes, which exist nowhere on disk, are staged into
    the temp directory.
    """
    mapping: dict[str, str] = {}
    paths: list[str] = []
    copied = 0
    for index, unit in enumerate(targets):
        if unit.disk_path is not None:
            mapping[normalized_key(unit.disk_path)] = unit.label
            paths.append(unit.disk_path)
            continue
        staging = tmp / f"u{index:04d}"
        staging.mkdir(parents=True, exist_ok=True)
        copy = staging / PurePosixPath(unit.label.replace("\\", "/")).name
        copy.write_bytes(unit.data or b"")
        mapping[normalized_key(str(copy))] = unit.label
        paths.append(str(copy))
        copied += 1
    if copied:
        report.notes.append(
            f"ruff: {copied} unit(s) linted from a temp copy of the index "
            "bytes, so project per-file-ignores do not apply to them"
        )
    return paths, mapping


def record_ruff_findings(findings: list[dict], mapping: dict[str, str], report: Report) -> None:
    """Split ruff output into the blocking band and advisory style notes."""
    style = 0
    for item in findings:
        filename = normalized_key(str(item.get("filename", "")))
        label = mapping.get(filename, item.get("filename", "<unknown>"))
        location = item.get("location") or {}
        row = int(location.get("row") or 0)
        col = int(location.get("column") or 0)
        code = item.get("code")
        message = item.get("message", "")
        if code is None or str(code).startswith(RUFF_BLOCKING_PREFIXES):
            report.add(Diagnostic(label, row, col, "LINT", f"ruff {code or 'syntax'}: {message}"))
            continue
        style += 1
        if style <= MAX_STYLE_NOTES:
            report.notes.append(f"ruff (style, not blocking) {label}:{row}:{col}: {code} {message}")
    if style:
        shown = min(style, MAX_STYLE_NOTES)
        report.notes.append(
            f"ruff: {style} style finding(s) did not block "
            f"({shown} listed above); run `ruff check` for the full set"
        )


def run_ruff(units: list[Unit], report: Report, root: Path | None = None) -> None:
    """Lint the checked bytes. Only the real-error band blocks.

    Every failure to RUN ruff is a note, never a block. That fail-open is
    deliberate and narrow: a gate that refuses every commit on a machine
    without a linter is a gate the operator turns off. Everything else in
    this file fails closed.
    """
    targets = [u for u in units if u.ext == ".py" and u.data is not None]
    if not targets:
        return
    command = ruff_command()
    if command is None:
        report.notes.append(
            "ruff: not on PATH and not importable - lint was NOT run and is "
            "NOT blocking; install it via scripts/verify_env.py"
        )
        return

    with tempfile.TemporaryDirectory(prefix="clockspeed_gate_") as tmp:
        paths, mapping = stage_for_lint(targets, Path(tmp), report)
        argv = [
            *command,
            "check",
            "--no-cache",
            "--output-format",
            "json",
            *ruff_config_args(root),
            *paths,
        ]
        try:
            proc = subprocess.run(argv, capture_output=True, timeout=RUFF_TIMEOUT, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            report.notes.append(
                "ruff: could not be run (%s) - lint skipped, not blocking" % (safe_exc_text(exc),)
            )
            return
        raw = proc.stdout.decode("utf-8", "replace").strip()
        if not raw:
            if proc.returncode not in (0, 1):
                report.notes.append(
                    f"ruff: exited {proc.returncode} with no JSON output - "
                    "lint skipped, not blocking"
                )
            return
        try:
            findings = json.loads(raw)
        except ValueError:
            report.notes.append("ruff: output was not valid JSON - lint skipped, not blocking")
            return

    record_ruff_findings(findings, mapping, report)


# --------------------------------------------------------------------------
# Content dispatch
# --------------------------------------------------------------------------


def check_content(unit: Unit, matchers: PiiMatchers, report: Report) -> None:
    """Run every content check over one unit's bytes."""
    data = unit.data
    if data is None:
        return
    if unit.ext in TEXT_EXTS:
        check_nul(unit.label, data, report)
    check_charset(unit.label, data, report)
    text, note = decode_for_report(data)
    if note and unit.ext not in TEXT_EXTS:
        report.notes.append(f"{unit.label}: {note}")
    check_secrets(unit.label, text, report)
    check_pii(unit.label, text, matchers, report)
    if unit.ext == ".py":
        check_python_syntax(unit.label, data, report)


def classify_for_read(label: str, ext: str, report: Report) -> bool:
    """Decide whether a path is worth reading at all."""
    if ext in BINARY_EXTS:
        report.skip(label, f"known-binary extension '{ext}'")
        return False
    return True


def accept_bytes(unit: Unit, data: bytes, report: Report) -> bool:
    """Attach bytes to a unit unless they are oversized or binary."""
    if len(data) > MAX_CONTENT_BYTES:
        report.skip(
            unit.label,
            "%d bytes exceeds the %d byte content-scan cap" % (len(data), MAX_CONTENT_BYTES),
        )
        return False
    if unit.ext not in TEXT_EXTS and b"\x00" in data:
        report.skip(unit.label, "NUL-byte sniff says binary")
        return False
    unit.data = data
    report.checked.append((unit.label, unit.origin, len(data)))
    report.units.append(unit)
    return True


# --------------------------------------------------------------------------
# Git plumbing
# --------------------------------------------------------------------------


class GitError(RuntimeError):
    """A git invocation that failed. Always fatal to the gate: fail closed."""


def _git_subcommand(args: list[str]) -> str:
    """Name the git subcommand, and nothing else from the argument vector.

    Every argv this module builds starts with a fixed literal - "rev-parse",
    "show", "diff" - so the subcommand is safe to print. The REST of the vector
    is not: in --files mode it is derived from paths the caller typed on the
    command line, and a message that echoes those echoes whatever home
    directory they came from.
    """
    return args[0] if args else "<no subcommand>"


def git_run_error(args: list[str], exc: BaseException) -> GitError:
    """Build the error for a git invocation that could not be run at all.

    Args:
        args: The argument vector, of which only the subcommand is rendered.
        exc: The failure, rendered through safe_exc_text - a git that is
            missing raises FileNotFoundError, whose str() names the path it
            searched.
    """
    return GitError("git %s failed to run: %s" % (_git_subcommand(args), safe_exc_text(exc)))


def git(args: list[str], cwd: str | None = None) -> bytes:
    """Run git and return stdout as bytes, raising GitError on any failure.

    `git` is resolved from PATH on purpose. Hardcoding an absolute executable
    path into a tracked file is forbidden (CONVENTIONS.md section 10), and the
    argument vector is a list with no shell, so there is nothing to inject.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            cwd=cwd,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise git_run_error(args, exc) from exc
    if proc.returncode != 0:
        # The argv is dropped here for the same reason git_run_error drops it.
        # Git's own stderr is KEPT: it is not an exception rendering, and what
        # it carries for the invocations this module makes is a repo-relative
        # index path, which the diagnostic LABEL already shows. Tightening that
        # channel further belongs with the rest of the sweep in CS-205.
        raise GitError(
            "git %s exited %d: %s"
            % (
                _git_subcommand(args),
                proc.returncode,
                proc.stderr.decode("utf-8", "replace").strip(),
            )
        )
    return proc.stdout


def repo_root(cwd: str | None = None) -> str:
    """Locate the repository root rather than assuming the current directory."""
    return git(["rev-parse", "--show-toplevel"], cwd=cwd).decode("utf-8").strip()


def staged_paths(root: str) -> list[str]:
    """List staged paths, NUL-separated so odd filenames survive intact."""
    raw = git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], cwd=root)
    return [chunk.decode("utf-8", "surrogateescape") for chunk in raw.split(b"\x00") if chunk]


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------


def mode_staged(report: Report, matchers: PiiMatchers) -> None:
    """Check the bytes git will commit, read from the index."""
    root = repo_root()
    paths = staged_paths(root)
    if not paths:
        report.notes.append("no staged paths matched --diff-filter=ACMR")
        return
    for label in paths:
        ext = PurePosixPath(label).suffix.lower()
        unit = Unit(label=label, origin="index", ext=ext)
        if not check_path(label, report):
            report.skip(label, "path itself is a violation; content not read")
            continue
        if not classify_for_read(label, ext, report):
            continue
        try:
            data = git(["show", ":" + label], cwd=root)
        except GitError as exc:
            report.add(
                Diagnostic(
                    label,
                    0,
                    0,
                    "INDEX",
                    "could not read the staged blob from the index: " + safe_exc_text(exc),
                )
            )
            continue
        if accept_bytes(unit, data, report):
            check_content(unit, matchers, report)


def label_for(path: str) -> str:
    """Render a path repo-relative when possible, so diagnostics stay stable.

    A repo-relative label is also what makes the root-anchored publisher-data
    directory check meaningful. A path outside any repository is returned
    as given, with separators normalised.
    """
    absolute = Path(path).absolute()
    try:
        root = repo_root(cwd=str(absolute.parent))
    except (GitError, OSError):
        return path.replace("\\", "/")
    try:
        rel = os.path.relpath(str(absolute), root)
    except ValueError:
        return path.replace("\\", "/")
    if rel.startswith(".."):
        return path.replace("\\", "/")
    return rel.replace("\\", "/")


def mode_files(paths: list[str], report: Report, matchers: PiiMatchers) -> None:
    """Check working-tree paths as they currently sit on disk."""
    for given in paths:
        label = label_for(given)
        ext = PurePosixPath(label).suffix.lower()
        unit = Unit(label=label, origin="worktree", ext=ext, disk_path=given)
        if not check_path(label, report):
            report.skip(label, "path itself is a violation; content not read")
            continue
        if not classify_for_read(label, ext, report):
            continue
        try:
            data = Path(given).read_bytes()
        except OSError as exc:
            report.add(
                Diagnostic(label, 0, 0, "IO", "could not read the file: " + safe_exc_text(exc))
            )
            continue
        if accept_bytes(unit, data, report):
            check_content(unit, matchers, report)


def mode_text_stdin(report: Report) -> None:
    """Check text on stdin: character set and secrets only."""
    data = sys.stdin.buffer.read()
    label = "<stdin>"
    report.checked.append((label, "stdin", len(data)))
    check_charset(label, data, report)
    text, note = decode_for_report(data)
    if note:
        report.notes.append(f"{label}: {note}")
    check_secrets(label, text, report)
    report.skip(
        label,
        "stdin carries no path, so the publisher-data, python-syntax and lint "
        "checks do not apply; character-set and secret checks ran",
    )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI. Exactly one mode flag is required."""
    parser = argparse.ArgumentParser(
        prog=GATE_NAME,
        description="Clockspeed commit gate. Exit 0 pass, exit 1 block.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--staged",
        action="store_true",
        help="check staged paths, reading content from the git index",
    )
    group.add_argument(
        "--files",
        nargs="+",
        metavar="PATH",
        help="check these working-tree paths",
    )
    group.add_argument(
        "--text-stdin",
        action="store_true",
        help="check text supplied on stdin (character set and secrets)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="list every path checked, its origin and its size",
    )
    parser.add_argument(
        "--list-skipped",
        action="store_true",
        help="list every path NOT checked and the reason it was not",
    )
    return parser


# --------------------------------------------------------------------------
# The render boundary
# --------------------------------------------------------------------------
#
# A label is VERDICT-BEARING. The extension is derived from it and selects
# which checks run; it becomes SyntaxError.filename via compile(); it names
# the staging copy ruff actually lints; it keys the ruff output mapping; it is
# scanned for non-ASCII with the column reported as label.index(...) + 1; and
# it is interpolated into `git show :<label>`. Changing what a label IS would
# therefore change verdicts. So label_for() and Unit.label keep returning the
# path exactly as before, and the redaction happens HERE, on the way to the
# terminal, as a pure function of the label.
#
# The rule never consults the environment: a label that is not repo-relative
# is reduced to its basename. Keying on "is this under the home directory"
# would render differently depending on where that directory sits, which is
# how a test ends up green in CI and red locally - pytest's tmp_path is under
# the home directory on Windows and under /tmp on Linux.

OUTSIDE_REPO_PREFIX = "<outside-repo>/"


def label_is_outside_repo(label: str) -> bool:
    """True when a label is not a repo-relative path.

    Pure string inspection: no filesystem access, no environment lookup and no
    home directory. Both platform spellings are recognised on both platforms,
    because this runs on Windows and in CI on Linux and must render the same
    shape on each.
    """
    norm = label.replace("\\", "/")
    if norm.startswith("/"):
        # POSIX absolute, and UNC once the separators are normalised.
        return True
    if norm[1:2] == ":" and norm[:1].isalpha():
        # A drive-letter prefix. Sliced rather than indexed so a one-character
        # label cannot raise here.
        return True
    return norm == ".." or norm.startswith("../")


def display_label(label: str) -> str:
    """Render a label for output, dropping every directory above the basename.

    The basename survives VERBATIM: it identifies the file to the operator and
    carries no personal data, while anything above it can carry the account
    name. A repo-relative label is returned unchanged, and so is a non-path
    label such as `<stdin>` or `<pii:world>`.
    """
    if not label_is_outside_repo(label):
        return label
    base = PurePosixPath(label.replace("\\", "/")).name
    return OUTSIDE_REPO_PREFIX + base if base else OUTSIDE_REPO_PREFIX


def label_replacements(report: Report) -> list[tuple[str, str]]:
    """Every label this run carries, paired with its redacted form.

    Longest raw label first, so a path that is a prefix of another cannot be
    partly replaced and leave a fragment of the directory behind.
    """
    raw: set[str] = {label for label, _origin, _size in report.checked}
    raw.update(label for label, _why in report.skipped)
    raw.update(diag.path for diag in report.diagnostics)
    pairs = [(item, display_label(item)) for item in raw if display_label(item) != item]
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    return pairs


def display_note(note: str, replacements: list[tuple[str, str]]) -> str:
    """Redact the labels interpolated into a free-text note.

    A note is a sentence with a label built into it rather than a field that
    can be redacted on its own, and the label sits at the start in three of
    the four shapes and mid-string in the ruff one. Two passes cover both.
    The exact-label pass handles a path containing spaces, which no token
    split could put back together. The token pass is the safety net: the ruff
    output mapping falls back to ruff's OWN filename when a lookup misses, and
    that filename is the temp staging copy, which sits under the home
    directory on Windows and appears in no label list.
    """
    for raw, shown in replacements:
        note = note.replace(raw, shown)
    return " ".join(display_label(token) for token in note.split(" "))


def display_diagnostic(diag: Diagnostic) -> str:
    """Render a diagnostic with the label redacted and the verdict intact.

    Line, column and code are untouched - they ARE the verdict. Deduplication
    in emit() runs on the raw render and never on this one, because two
    out-of-repo files can share a basename, and collapsing them here would
    silently drop a finding and change the blocking count.
    """
    return Diagnostic(
        display_label(diag.path),
        diag.line,
        diag.col,
        diag.code,
        diag.reason,
    ).render()


def skipped_lines(report: Report, verbose: bool, list_skipped: bool) -> list[str]:
    """Render the skipped channel, splitting coverage skips from volume skips.

    Under either flag the count header and every skip render, exactly as they
    did before CS-209. With NEITHER flag - which is how .githooks/pre-commit
    invokes this gate, and therefore the only invocation that gates a commit -
    the COVERAGE skips still render, because a reduction in this gate's own
    detection that nobody is ever shown is not an exemption, it is a silent
    hole (CONVENTIONS.md section 15.1). See COVERAGE_SKIP_LABELS.

    Returns:
        The lines to write, each already newline-terminated.
    """
    lines: list[str] = []
    if verbose or list_skipped:
        lines.append("%s: skipped %d unit(s)\n" % (GATE_NAME, len(report.skipped)))
        shown = list(report.skipped)
    else:
        shown = [pair for pair in report.skipped if pair[0] in COVERAGE_SKIP_LABELS]
    lines.extend(f"  skipped  {display_label(label)}  -  {why}\n" for label, why in shown)
    return lines


def emit(report: Report, verbose: bool, list_skipped: bool) -> int:
    """Print the report and return the process exit code."""
    out = sys.stdout
    replacements = label_replacements(report)
    if verbose:
        out.write("%s: checked %d unit(s)\n" % (GATE_NAME, len(report.checked)))
        for label, origin, size in report.checked:
            out.write("  checked  %s  [%s, %d bytes]\n" % (display_label(label), origin, size))
    for line in skipped_lines(report, verbose, list_skipped):
        out.write(line)
    if verbose:
        for note in report.notes:
            out.write(f"  note     {display_note(note, replacements)}\n")
    out.flush()

    if not report.diagnostics:
        out.write(
            "%s: PASS - %d checked, %d skipped, 0 blocking\n"
            % (GATE_NAME, len(report.checked), len(report.skipped))
        )
        out.flush()
        return 0

    err = sys.stderr
    err.write(f"{GATE_NAME}: BLOCKED\n")
    seen: set[str] = set()
    for diag in report.diagnostics:
        # Deduplicate on the RAW render, display the redacted one. Two
        # out-of-repo files can share a basename, so deduplicating on the
        # redacted text would drop a real finding and change len(seen),
        # which is the blocking count reported below.
        rendered = diag.render()
        if rendered in seen:
            continue
        seen.add(rendered)
        err.write(display_diagnostic(diag) + "\n")
    if not verbose:
        for note in report.notes:
            if note.startswith("ruff (style"):
                continue
            err.write(f"  note     {display_note(note, replacements)}\n")
    err.write(
        "%s: BLOCKED - %d diagnostic(s) across %d checked unit(s). "
        "Nothing was committed.\n" % (GATE_NAME, len(seen), len(report.checked))
    )
    err.flush()
    return 1


def main(argv: list[str] | None = None) -> int:
    """Dispatch to the selected mode and emit the report."""
    args = build_parser().parse_args(argv)
    report = Report()
    matchers = PiiMatchers(report)

    if args.text_stdin:
        mode_text_stdin(report)
    else:
        if args.files:
            mode_files(args.files, report, matchers)
        else:
            mode_staged(report, matchers)
        # Lint runs over the SAME bytes the checks above ran over: in --staged
        # mode those are the index bytes, not the working tree's.
        try:
            root: Path | None = Path(repo_root())
        except (GitError, OSError):
            root = None
        run_ruff(report.units, report, root)

    return emit(report, args.verbose, args.list_skipped)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        # SUPPRESS BY DEFAULT, OPT IN EXPLICITLY. The class name and the
        # per-type redacted text say what broke; the traceback says where, and
        # cannot say it without rendering an absolute path per frame and a
        # final str(exc). Reformatting the crash report is all that happens
        # here - the failure is never swallowed.
        sys.stderr.write(
            "%s: crashed with %s: %s\n" % (GATE_NAME, type(exc).__name__, safe_exc_text(exc))
        )
        if os.environ.get(ENV_CRASH_TRACEBACK) == "1":
            traceback.print_exc()
        else:
            sys.stderr.write(
                f"  The traceback is suppressed. Set {ENV_CRASH_TRACEBACK}=1 to print it -\n"
                "  it renders an absolute path per frame (CLAUDE.md non-negotiable 12).\n"
            )
        sys.stderr.write(
            f"{GATE_NAME}: the gate itself raised. Failing CLOSED with exit 1 - a gate "
            "that crashes open is worse than no gate.\n"
        )
        raise SystemExit(1) from None
