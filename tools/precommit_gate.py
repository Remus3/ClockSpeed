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

Exit codes: 0 pass, 1 block. Nothing else. An unexpected exception prints its
traceback and exits 1 - a gate that crashes open is worse than no gate at all.

CONVENTIONS.md section 15.1: "a guard can be green while self-excusing -
skipping itself on the very files it is meant to cover." This gate therefore
has NO path allowlist of any kind. It checks its own source, its own tests and
its own hooks exactly like anything else, and `--verbose` / `--list-skipped`
print every path it did not check together with the reason it did not.

Nothing personal is hardcoded here. The Windows account name comes from the
environment at runtime and the numeric platform account id is discovered by
globbing the save root at runtime. Neither value appears in this file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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
MIN_ACCOUNT_ID_DIGITS = 8
# Shorter than this and a whole-word match on the account name would flag
# ordinary prose more often than it would catch a leak.
MIN_ACCOUNT_NAME_CHARS = 3


def save_root() -> Path | None:
    """Locate the platform save root without hardcoding any path."""
    override = os.environ.get("CLOCKSPEED_SAVE_ROOT")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    if not base:
        return None
    return Path(base).joinpath(*SAVE_ROOT_PARTS)


def discover_account_ids(report: Report | None = None) -> list[str]:
    """Glob the save root for numeric account directories, at runtime.

    BOOTSTRAP.md section 2.2: the numeric platform account id is personal data
    and must never be written down. It is therefore never written down here -
    it is discovered. A machine with no game installed must still be able to
    commit, so a missing save root is a quiet skip.
    """
    root = save_root()
    if root is None:
        if report is not None:
            report.skip(
                "<pii:account-id>",
                "no LOCALAPPDATA in the environment; save root unknown",
            )
        return []
    try:
        if not root.is_dir():
            if report is not None:
                report.skip(
                    "<pii:account-id>",
                    "save root does not exist on this machine",
                )
            return []
        found = sorted(
            entry.name
            for entry in root.iterdir()
            if entry.is_dir() and entry.name.isdigit() and len(entry.name) >= MIN_ACCOUNT_ID_DIGITS
        )
    except OSError as exc:
        if report is not None:
            report.skip("<pii:account-id>", f"save root unreadable: {exc}")
        return []
    if report is not None and not found:
        report.skip(
            "<pii:account-id>",
            "save root exists but holds no numeric account directory",
        )
    return found


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
                    "<pii:account-name>",
                    "%s=<%d chars> is too short to match safely" % (key, len(value)),
                )
            continue
        if value.lower() in GENERIC_ACCOUNT_NAMES:
            if report is not None:
                report.skip(
                    "<pii:account-name>",
                    f"{key} is a generic account name; whole-word match would flag ordinary prose",
                )
            continue
        names.append(value)
    return names


class PiiMatchers:
    """Runtime-built PII matchers. Never constructed from a literal."""

    def __init__(self, report: Report | None = None) -> None:
        """Discover the account name and account id for this machine."""
        self.account_names = current_account_names(report)
        self.account_ids = discover_account_ids(report)
        self.name_res = [
            re.compile(
                rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])",
                re.IGNORECASE,
            )
            for name in self.account_names
        ]
        self.id_res = [
            re.compile(rf"(?<!\d){re.escape(value)}(?!\d)") for value in self.account_ids
        ]


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
        for pattern in matchers.name_res:
            for match in pattern.finditer(line):
                report.add(
                    Diagnostic(
                        label,
                        lineno,
                        match.start() + 1,
                        "PII",
                        "this machine's account name appears as a whole word",
                    )
                )
        for pattern in matchers.id_res:
            for match in pattern.finditer(line):
                report.add(
                    Diagnostic(
                        label,
                        lineno,
                        match.start() + 1,
                        "PII",
                        "numeric platform account id discovered under the save "
                        "root (BOOTSTRAP.md section 2.2)",
                    )
                )


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
                "python syntax error: %s" % (exc.msg or exc),
            )
        )
    except ValueError as exc:
        report.add(Diagnostic(label, 0, 0, "SYNTAX", f"python source rejected: {exc}"))


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
            report.notes.append(f"ruff: could not be run ({exc}) - lint skipped, not blocking")
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
        raise GitError("git {} failed to run: {}".format(" ".join(args), exc)) from exc
    if proc.returncode != 0:
        raise GitError(
            "git %s exited %d: %s"
            % (
                " ".join(args),
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
                    f"could not read the staged blob from the index: {exc}",
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
            report.add(Diagnostic(label, 0, 0, "IO", f"could not read the file: {exc}"))
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


def emit(report: Report, verbose: bool, list_skipped: bool) -> int:
    """Print the report and return the process exit code."""
    out = sys.stdout
    if verbose:
        out.write("%s: checked %d unit(s)\n" % (GATE_NAME, len(report.checked)))
        for label, origin, size in report.checked:
            out.write("  checked  %s  [%s, %d bytes]\n" % (label, origin, size))
    if verbose or list_skipped:
        out.write("%s: skipped %d unit(s)\n" % (GATE_NAME, len(report.skipped)))
        for label, why in report.skipped:
            out.write(f"  skipped  {label}  -  {why}\n")
    if verbose:
        for note in report.notes:
            out.write(f"  note     {note}\n")
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
        rendered = diag.render()
        if rendered in seen:
            continue
        seen.add(rendered)
        err.write(rendered + "\n")
    if not verbose:
        for note in report.notes:
            if note.startswith("ruff (style"):
                continue
            err.write(f"  note     {note}\n")
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
    except BaseException:
        traceback.print_exc()
        sys.stderr.write(
            f"{GATE_NAME}: the gate itself raised. Failing CLOSED with exit 1 - a gate "
            "that crashes open is worse than no gate.\n"
        )
        raise SystemExit(1) from None
