"""Where the game install, the save root and the account directory actually are.

WHY THIS MODULE EXISTS. Three facts about this machine are needed by almost
everything above this layer, and not one of them may ever be written into a
tracked file (CLAUDE.md non-negotiable 3, BOOTSTRAP.md section 2.2): the
install path, the save root, and the numeric account directory beneath it.
They are therefore resolved at runtime, every time, from the environment and
from the filesystem. This module is the ONE place that does it. Before it
existed the logic lived in scripts/verify_env.py; that script now delegates
here rather than keeping a second copy, because two copies of a resolver are
two answers to "where is the game" waiting to disagree.

RESOLUTION PRECEDENCE, identical for all three and checked in this order:

  1. the environment variable  - CLOCKSPEED_GAME_DIR, CLOCKSPEED_SAVE_ROOT,
                                 CLOCKSPEED_ACCOUNT_DIR
  2. config/local.json         - the "game_dir", "save_root" and
                                 "account_dir" keys. The file is gitignored,
                                 is absent on a normal machine, and its
                                 absence is normal rather than an error.
  3. auto-detection            - the Steam library index then the common
                                 install locations; %LOCALAPPDATA% for the
                                 save root; the most-recently-modified
                                 all-digit directory for the account.

An override that names something which is not a directory resolves to None
and says so. It does NOT fall through to auto-detection: an operator who
pointed the tool somewhere explicitly is owed the answer "your override is
wrong", not a silent guess from somewhere else. Nothing here raises on a
missing install, a missing save root or a missing account directory - absent
content is reported, never fatal (CLAUDE.md non-negotiable 7), because the
rule suite has to run on a machine that has never had the game on it.

PRIVACY, and this is the highest-risk part of this file. The account
directory NAME is a platform account id. It is personal data, as are the
Windows account name, the machine name, the world name and any absolute path
under a home directory. Callers get Path objects so they can stat them; they
must never print one raw. Every path this module can put into a message, an
exception or a repr goes through redact() first.

WHAT redact() LEARNED THE HARD WAY, because each of these was a real leak
found by reading the output rather than the code:

  - Stripping the home prefix alone leaves the id in the tail of the path.
  - Identifying the account directory BY PATTERN covers exactly one platform.
    It is identified by POSITION - the segment below the save root - because
    Epic, the Microsoft Store and a hand-written override each put a
    different character class there and all three are equally personal.
  - An override may relocate the account directory outside the save root
    entirely, where there is no position to key on. So every account
    directory this module hands out is remembered by name.
  - Windows renders a home path two ways. The 8.3 short form spells the
    account name as six characters, a tilde and a digit, matches no
    environment value, and is what tempfile.gettempdir() returns.
  - The 8.3 problem is NOT only a home-path problem. The account directory
    has a short rendering too, and remembering only its long name left that
    one standing even with CLOCKSPEED_ACCOUNT_DIR declared. Every account
    directory is remembered in every rendering.
  - The SAVE ROOT itself may be relocated by an override, which leaves the
    account directory sitting in position with no fixed marker above it for
    position to key on. So position keys on a SET of anchors - the marker,
    the declared root, and every root this module resolved - and not on the
    marker alone.
  - A save filename embeds the world name, so the filename component goes
    too.

SEAM. This is the bottom of the stack (docs/ARCHITECTURE.md section 3). It
imports nothing from scripts/ or tools/ and nothing from any layer above it.
tools/precommit_gate.py holds its own independent save-root resolver; that
file is frozen (CLAUDE.md section 6) and consolidating it onto this module
needs an adjudicator grant recorded in docs/LEDGER.md.
"""

from __future__ import annotations

import contextlib
import functools
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# --- override surface -------------------------------------------------------

ENV_GAME_DIR = "CLOCKSPEED_GAME_DIR"
ENV_SAVE_ROOT = "CLOCKSPEED_SAVE_ROOT"
ENV_ACCOUNT_DIR = "CLOCKSPEED_ACCOUNT_DIR"

# Where config/local.json is read from, for a checkout that is not the repo
# root - an installed copy of the package, or a test that must not be able to
# reach the operator's real local configuration.
ENV_LOCAL_CONFIG = "CLOCKSPEED_LOCAL_CONFIG"

CONFIG_GAME_DIR = "game_dir"
CONFIG_SAVE_ROOT = "save_root"
CONFIG_ACCOUNT_DIR = "account_dir"

LOCAL_CONFIG_RELATIVE = ("config", "local.json")

# A local config file is a handful of short strings. Anything larger is not
# the file this module is looking for, and reading it whole would be the only
# unbounded read in the layer.
MAX_LOCAL_CONFIG_BYTES = 64_000

# --- discovery constants ----------------------------------------------------

# %LOCALAPPDATA%/FactoryGame/Saved/SaveGames (BOOTSTRAP.md section 2). The
# leading root is discovered, never written down; only the suffix is fixed.
SAVE_ROOT_PARTS = ("FactoryGame", "Saved", "SaveGames")

# Common default install locations, tried last, relative to each existing
# drive root. These are program-install locations, never user-home paths, and
# none is authoritative - each is probed and the first that exists wins.
DEFAULT_INSTALL_SUFFIXES = (
    "Program Files (x86)/Steam/steamapps/common/Satisfactory",
    "Program Files/Steam/steamapps/common/Satisfactory",
    "SteamLibrary/steamapps/common/Satisfactory",
    "Games/Steam/steamapps/common/Satisfactory",
    "Program Files/Epic Games/SatisfactoryEarlyAccess",
    "Program Files/Epic Games/SatisfactoryExperimental",
    "Program Files/Epic Games/Satisfactory",
)

GAME_RELATIVE_TO_LIBRARY = ("steamapps", "common", "Satisfactory")

# --- redaction --------------------------------------------------------------

ACCOUNT_DIR_PLACEHOLDER = "<account-dir>"

# A save file is named after the world, and the world name is operator-chosen
# and is personal data (CLAUDE.md non-negotiable 3). Nothing short of parsing
# the save distinguishes a world name from any other filename stem, so the
# whole component goes rather than some guessed part of it.
SAVE_FILE_PLACEHOLDER = "<save-file>"

# A BACKSTOP, not the rule. The rule is positional - see
# _save_root_anchors - because an account directory is whatever name sits in
# the account-id position, and only one platform puts digits there: Epic
# writes a hex token, the Microsoft Store a braceless GUID, and the
# CLOCKSPEED_ACCOUNT_DIR override writes whatever the operator typed. An
# earlier version of this module carried a comment asserting "a platform
# account id is 17 digits" and an all-digit pattern to match, which is
# precisely how a redactor comes to be correct for one shape and silent for
# the other three. The floor stays well below seventeen because over-redacting
# a long number costs nothing and under-redacting an id is permanent.
MIN_ACCOUNT_ID_DIGITS = 8

# A short environment value would match half the words in a path, so values
# below this length are not used as redaction needles at all.
MIN_REDACTABLE_LEN = 3

# Account directory names this module has itself handed out, so redact() can
# strip the one shape POSITION cannot reach: an override naming an absolute
# path OUTSIDE the save root, where there is no save-root marker to sit below
# and, unless the operator chose digits, no digit run either. It only ever
# grows from a directory this module resolved - never from parsed text - so it
# cannot be poisoned into over-matching by anything a caller passes in, and
# every entry only ever makes redaction stricter. A list rather than a set
# because redact() iterates a slice copy of it while a resolver may be
# appending, and slicing a list is atomic where iterating a set is not.
_RESOLVED_ACCOUNT_NAMES: list[str] = []

# Save roots this module has itself resolved, in every rendering Windows spells
# them, kept for the same reason and with the same safety property as the names
# above: it only ever grows from a directory this module resolved, never from
# parsed text, and every entry only ever makes redaction stricter. A save root
# is an ANCHOR rather than a needle - it is never substituted on its own, only
# used to find the ONE segment sitting directly below it - so remembering one
# cannot over-redact the way a free-floating needle would.
_RESOLVED_SAVE_ROOTS: list[str] = []

# Bounded by non-alphanumerics on both sides so this matches a path SEGMENT or
# a standalone token, and not the digits inside a longer identifier.
_ACCOUNT_ID_RE = re.compile(
    r"(?<![0-9A-Za-z])[0-9]{" + str(MIN_ACCOUNT_ID_DIGITS) + r",}(?![0-9A-Za-z])"
)

# One path segment. Defined ONCE and shared by every rule below that needs it,
# because three hand-copied spellings of a character class are three chances
# for one of them to drift. It excludes the angle brackets a placeholder is
# made of, which is what makes a second pass over an already-redacted string a
# no-op, and the quote and whitespace characters that end a segment inside a
# rendered message.
_PATH_SEGMENT_CLASS = r"[^/\\\s\"'<>|]+"

# THE PRIMARY RULE. The account directory is the segment immediately below the
# save root, so it is identified by where it sits and never by what it is made
# of. The marker is derived from SAVE_ROOT_PARTS rather than restated, so the
# redactor cannot drift from the resolver.
_SAVE_ROOT_MARKER = "/".join(SAVE_ROOT_PARTS)

# A save filename, with the optional second suffix the game writes for its
# rotated copies. The trailing guard stops an unrelated word that merely
# begins with the suffix from being cut in half.
_SAVE_FILE_RE = re.compile(
    _PATH_SEGMENT_CLASS + r"\.sav(?:\.[A-Za-z0-9]{1,8})?(?![A-Za-z0-9])", re.IGNORECASE
)


@functools.lru_cache(maxsize=128)
def _account_position_re(anchor: str) -> re.Pattern[str]:
    """Compile the positional rule for one save-root anchor.

    Cached because redact() rebuilds its anchor list on every call - the
    environment is re-read every time, deliberately - while the compiled form
    of a given anchor never changes. Bounded because the anchor set is the
    marker plus a handful of renderings of the roots this module resolved.

    Args:
        anchor: A save-root spelling, already normalized to forward slashes.

    Returns:
        A pattern capturing the anchor in group 1 and consuming the ONE
        segment below it, which is the account directory.
    """
    return re.compile("(" + re.escape(anchor) + ")/" + _PATH_SEGMENT_CLASS, re.IGNORECASE)


@functools.lru_cache(maxsize=64)
def _win_path_form(value: str, api: str) -> str | None:
    """Ask Windows for one alternate rendering of a path.

    CACHED, and note carefully what is NOT cached: :func:`_redaction_pairs`
    still re-reads the environment on every call, because where home is can
    change within a process and a redactor that answers from a stale
    environment is the failure that docstring warns about. What is cached here
    is a different kind of fact - the 8.3 rendering of a given directory is a
    property of the filesystem, not of the environment. Without the cache each
    redact() paid four cross-boundary calls into Win32, which measured at
    about a millisecond per call; the save layer will redact paths in bulk.

    The cache is bounded because it is only ever asked about the handful of
    directories the environment names. If a directory were deleted and
    recreated with a different short name, the stale entry would leave an
    extra needle in place rather than remove one - over-redaction, which is
    the safe direction.

    Args:
        value: An existing path. The APIs answer only for a path that exists.
        api: ``GetShortPathNameW`` or ``GetLongPathNameW``.

    Returns:
        The alternate rendering, or None off Windows, on any failure, or when
        the volume has 8.3 name generation disabled and there is no second
        rendering to have.
    """
    if sys.platform != "win32":
        return None
    try:
        # PLC0415: ctypes.windll exists only on Windows, so both imports have
        # to follow the platform check above rather than sit at module level.
        import ctypes  # noqa: PLC0415
        from ctypes import wintypes  # noqa: PLC0415

        function = getattr(ctypes.windll.kernel32, api)
        function.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        function.restype = wintypes.DWORD
        needed = function(value, None, 0)
        if not needed:
            return None
        buffer = ctypes.create_unicode_buffer(needed)
        if not function(value, buffer, needed):
            return None
    except (AttributeError, ImportError, OSError, ValueError):
        return None
    return buffer.value or None


def _path_forms(value: str) -> list[str]:
    """Return every rendering of one path that a message could arrive carrying.

    THE DEFECT THIS EXISTS FOR. Windows keeps a legacy 8.3 SHORT name for most
    directories, and on a default install ``tempfile.gettempdir()`` hands one
    back - so a temporary path arrives spelling the account name as its first
    six characters plus a tilde and a digit. That matches no long-form
    environment value, and the account name is not a substring of it either,
    so a redactor built only from the environment leaves six characters of the
    operator's account name standing in every line it "redacted".

    Args:
        value: A path in whichever form the environment supplied it.

    Returns:
        The given form first, then any distinct short or long rendering.
    """
    forms = [value]
    for api in ("GetShortPathNameW", "GetLongPathNameW"):
        other = _win_path_form(value, api)
        if other and other not in forms:
            forms.append(other)
    return forms


def _redaction_pairs() -> list[tuple[str, str]]:
    """Build the longest-first (needle, replacement) list used by redact().

    Rebuilt on every call rather than cached at import. The environment is the
    source of truth for where home is, a cached copy would answer from
    whatever the environment looked like at import time, and a redactor that
    silently stops matching is worse than no redactor at all.

    Returns:
        Pairs of (needle, replacement token), longest needle first so a
        nested path is replaced by its most specific token.
    """
    pairs: list[tuple[str, str]] = []

    def remember_path(value: str | None, token: str) -> None:
        if not value:
            return
        pairs.extend(
            (form.replace("\\", "/").rstrip("/"), token)
            for form in _path_forms(value)
            if len(form) >= MIN_REDACTABLE_LEN
        )

    def remember_name(value: str | None, token: str) -> None:
        if value and len(value) >= MIN_REDACTABLE_LEN:
            pairs.append((value, token))

    home = os.environ.get("USERPROFILE")
    remember_path(os.environ.get("LOCALAPPDATA"), "<localappdata>")
    remember_path(os.environ.get("APPDATA"), "<appdata>")
    remember_path(home, "<home>")
    with contextlib.suppress(OSError, RuntimeError):
        remember_path(str(Path.home()), "<home>")
        remember_name(Path.home().name, "<user>")
    remember_name(os.environ.get("USERNAME"), "<user>")
    remember_name(os.environ.get("COMPUTERNAME"), "<machine>")

    # The 8.3 rendering of the profile directory ends in a SHORTENED account
    # name, which is a distinct string from the account name and is not a
    # substring of it. A path that carries only that tail - a bare directory
    # name lifted out of a longer path - is covered by nothing above.
    for candidate in _path_forms(home) if home else []:
        remember_name(Path(candidate).name, "<user>")

    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    return pairs


def _save_root_anchors() -> list[str]:
    """Every spelling of a save root the account directory could be sitting under.

    WHY THIS IS NOT A RESOLVER CALL. The obvious implementation asks
    resolve_save_root() where the save root is. It cannot: resolve_save_root
    reaches _override, which reaches local_config, which reaches
    _read_local_config, which calls _note, which calls redact. That is a cycle,
    and it is not theoretical - it survives today only because _override passes
    no warning collector and _note returns immediately when there is none.
    Wiring a collector through, which CS-443 is open to do, closes the loop.
    Beyond the recursion, resolve_save_root can raise on a declared floor while
    redact() is documented never to raise and is called from except bodies.

    So the three sources here are exactly the ones that cannot recurse:

      1. the fixed marker built from SAVE_ROOT_PARTS - today's rule, unchanged;
      2. CLOCKSPEED_SAVE_ROOT read STRAIGHT from os.environ, with no override
         ladder, no config read and no filesystem call. This is the idiom
         _redaction_pairs already uses for LOCALAPPDATA, APPDATA, USERPROFILE,
         USERNAME and COMPUTERNAME, and for the same reason;
      3. _RESOLVED_SAVE_ROOTS, which resolve_save_root fills with roots it has
         already confirmed are directories.

    THE ORDERING TRAP, and it is why each source is offered in three forms
    rather than one. By the time the positional pass runs, the environment
    needles have ALREADY rewritten the text - so on a default machine the save
    root arrives already spelled with a "<localappdata>" token in front of it,
    while an anchor built from the raw value still spells the absolute home
    path it was read from, and the two never meet - the substitution has moved
    the text out from under the needle. An anchor set that only offered the
    raw value would be
    INERT on the ordinary machine and live only on the relocated one, which is
    the inverse of the case this exists for. Today's marker escapes the trap by
    accident: it is a SUFFIX, so the home substitution cannot touch it.

    Each candidate is therefore offered as given, in every rendering Windows
    spells it, and passed through the same substitution the text has received.

    Returns:
        Anchor strings, longest first, each already normalized to forward
        slashes. Never raises.
    """
    pairs = _redaction_pairs()
    anchors: list[str] = [_SAVE_ROOT_MARKER]

    def offer(value: str) -> None:
        for form in _path_forms(value):
            normalized = form.replace("\\", "/").rstrip("/")
            substituted = normalized
            for needle, token in pairs:
                substituted = re.sub(re.escape(needle), token, substituted, flags=re.IGNORECASE)
            for variant in (normalized, substituted):
                if len(variant) >= MIN_REDACTABLE_LEN and variant not in anchors:
                    anchors.append(variant)

    declared = (os.environ.get(ENV_SAVE_ROOT) or "").strip()
    if declared:
        offer(declared)
    for remembered in _RESOLVED_SAVE_ROOTS[:]:
        offer(remembered)
    anchors.sort(key=len, reverse=True)
    return anchors


def redact(text: object) -> str:
    """Strip personal data out of anything about to be printed or raised.

    Removes the home prefixes in every rendering Windows offers, the account
    name, the machine name, the account directory, and the save filename that
    carries the world name; and collapses backslashes to forward slashes so
    the result is stable and safe to paste into an issue.

    FIVE PASSES, IN THIS ORDER, and the order is load-bearing. The environment
    needles go first so the save-root marker is left sitting behind a token
    rather than behind an absolute path. Position goes next, because where a
    segment sits is the only reliable account-directory rule; it runs once per
    save-root ANCHOR rather than once against the fixed marker, so a save root
    the operator relocated still has a position to key on (CS-454, and see
    _save_root_anchors for why the anchors cannot be a resolver call and why
    each is offered in a substituted form). The remembered names follow,
    covering an override that put the account directory somewhere with no
    marker above it. The digit-run backstop then catches an id encountered
    outside any path at all. The save filename goes last, so it is matched
    against a string whose directories are already tokens.

    Idempotent: every placeholder is built from characters the patterns
    exclude, so redacting an already-redacted string returns it unchanged.
    That matters because output is redacted at more than one seam - a skip
    record built by a guard is redacted again when it is rendered.

    Args:
        text: Anything renderable - a Path, an exception, a message.

    Returns:
        The redacted rendering. Never raises.
    """
    out = str(text).replace("\\", "/")
    for needle, token in _redaction_pairs():
        out = re.sub(re.escape(needle), token, out, flags=re.IGNORECASE)
    for anchor in _save_root_anchors():
        out = _account_position_re(anchor).sub(r"\1/" + ACCOUNT_DIR_PLACEHOLDER, out)
    for name in _RESOLVED_ACCOUNT_NAMES[:]:
        out = re.sub(
            r"(?<![0-9A-Za-z])" + re.escape(name) + r"(?![0-9A-Za-z])",
            ACCOUNT_DIR_PLACEHOLDER,
            out,
            flags=re.IGNORECASE,
        )
    out = _ACCOUNT_ID_RE.sub(ACCOUNT_DIR_PLACEHOLDER, out)
    return _SAVE_FILE_RE.sub(SAVE_FILE_PLACEHOLDER, out)


def _remember_account_dir(path: Path) -> Path:
    """Record an account directory name so redact() can strip it by name.

    Called on every account directory this module hands back to a caller. The
    positional rule in redact() covers a directory that sits under the save
    root; this covers the documented override that does not, which is the case
    where neither position nor pattern can see it.

    EVERY RENDERING, not just ``path.name``, and that was a live leak (CS-454).
    Windows spells a directory two ways, and this module has known it since
    _path_forms was written for the HOME directory - but the account directory
    was remembered by its long name alone. So the 8.3 short form, which is the
    first six characters of the operator's account id plus a tilde and a digit
    and which is what tempfile.gettempdir() hands back, matched nothing and
    reached the output in plaintext EVEN WITH CLOCKSPEED_ACCOUNT_DIR declared -
    the configuration resolve_account_dir documents as the safe one.

    The forms are taken HERE rather than at redaction time because Windows only
    answers for a path that still exists, and the directory is known to exist
    at this moment: every caller has just checked.

    Args:
        path: The resolved account directory.

    Returns:
        ``path``, unchanged, so callers can return through this.
    """
    for form in _path_forms(str(path)):
        name = Path(form).name
        if len(name) >= MIN_REDACTABLE_LEN and name not in _RESOLVED_ACCOUNT_NAMES:
            _RESOLVED_ACCOUNT_NAMES.append(name)
    return path


def _remember_save_root(path: Path) -> Path:
    """Record a resolved save root so redact() can anchor positionally on it.

    The mirror of :func:`_remember_account_dir`, and it exists for the case
    that function cannot cover: the account directory is still SITTING under a
    save root, so there is a position to key on, but the operator relocated
    that save root and the fixed FactoryGame/Saved/SaveGames marker is nowhere
    in the string. Remembering the root restores the position.

    Only ever called with a directory this module has confirmed exists, which
    is what keeps the memory from being poisoned by parsed text, and what lets
    _path_forms answer for it.

    Args:
        path: A save root that resolved.

    Returns:
        ``path``, unchanged, so callers can return through this.
    """
    for form in _path_forms(str(path)):
        normalized = form.replace("\\", "/").rstrip("/")
        if len(normalized) >= MIN_REDACTABLE_LEN and normalized not in _RESOLVED_SAVE_ROOTS:
            _RESOLVED_SAVE_ROOTS.append(normalized)
    return path


# --- local configuration ----------------------------------------------------


def _repo_root() -> Path:
    """Return the repository root, derived from this file's own location.

    Returns:
        The directory two levels above ``clockspeed/data/``.
    """
    return Path(__file__).resolve().parents[2]


def local_config_path() -> Path:
    """Return where the local configuration file is read from.

    Returns:
        The path named by CLOCKSPEED_LOCAL_CONFIG, or config/local.json under
        the repository root. The file need not exist.
    """
    override = os.environ.get(ENV_LOCAL_CONFIG)
    if override:
        return Path(override)
    return _repo_root().joinpath(*LOCAL_CONFIG_RELATIVE)


WARN_LOCAL_CONFIG_OVERSIZE: Final = "local-config-oversize"
WARN_LOCAL_CONFIG_UNREADABLE: Final = "local-config-unreadable"
WARN_LOCAL_CONFIG_UNDECODABLE: Final = "local-config-undecodable"
WARN_LOCAL_CONFIG_MALFORMED: Final = "local-config-malformed"
WARN_LOCAL_CONFIG_NOT_A_MAPPING: Final = "local-config-not-a-mapping"
WARN_LOCAL_CONFIG_NON_STRING_VALUE: Final = "local-config-non-string-value"


@dataclass(frozen=True)
class LocalConfigWarning:
    """An operator declaration that was discarded, and why (CS-443).

    Attributes:
        code: One of this module's WARN_LOCAL_CONFIG_* constants.
        subject: What was discarded - the redacted config location for a
            whole-file refusal, or the key name for a single dropped entry.
            Redacted here rather than at the render seam, because a skip
            record is an echo path exactly like a log line (CLAUDE.md
            non-negotiable 12) and redact() is idempotent.
        detail: A fixed line keyed by code, naming the consequence. NEVER
            built from file content: the values in this file are paths, and a
            reason that quoted the value it rejected would publish one.
    """

    code: str
    subject: str
    detail: str


def _note(
    warnings: list[LocalConfigWarning] | None, code: str, subject: object, detail: str
) -> None:
    """Append one discard record, if the caller asked for a channel.

    Args:
        warnings: The caller's collector, or None when it did not want one.
        code: A WARN_LOCAL_CONFIG_* constant.
        subject: What was discarded. Redacted before it is stored.
        detail: The fixed consequence line for ``code``.
    """
    if warnings is None:
        return
    warnings.append(LocalConfigWarning(code=code, subject=redact(subject), detail=detail))


def _read_local_config(path: Path, warnings: list[LocalConfigWarning] | None) -> str | None:
    """Read the local config file's text, reporting whatever stopped it.

    Split out from :func:`local_config` so the three ways READING can fail
    stay separate from the two ways PARSING can, and so neither function has
    to be read as one long ladder of returns.

    Args:
        path: The configuration location.
        warnings: The caller's collector, or None.

    Returns:
        The file's text, or None when there is nothing to parse. None covers
        two different facts on purpose - absence, which is silent, and a
        discard, which has already been reported through ``warnings`` by the
        time this returns.
    """
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > MAX_LOCAL_CONFIG_BYTES:
            _note(
                warnings,
                WARN_LOCAL_CONFIG_OVERSIZE,
                path,
                "the file is larger than a local config plausibly is; it was not read",
            )
            return None
        return path.read_text(encoding="utf-8")
    except OSError:
        _note(
            warnings,
            WARN_LOCAL_CONFIG_UNREADABLE,
            path,
            "the file could not be read; every declaration in it was discarded",
        )
        return None
    except UnicodeDecodeError:
        # NOT an OSError - UnicodeDecodeError is a ValueError, so the handler
        # above never saw it and it propagated out of a function documented as
        # never raising. Reported rather than decoded with errors="replace":
        # mangling an operator's declared path into U+FFFD would hand back a
        # value that cannot resolve, which is the silent-wrong-answer failure
        # non-negotiable 7 forbids.
        _note(
            warnings,
            WARN_LOCAL_CONFIG_UNDECODABLE,
            path,
            "the file is not valid UTF-8; every declaration in it was discarded",
        )
        return None


def local_config(*, warnings: list[LocalConfigWarning] | None = None) -> dict[str, str]:
    """Read the gitignored local configuration file, if there is one.

    The file is machine-specific and holds the paths that must never be
    tracked, which is why it is gitignored and why every machine is expected
    to be without one. Absence is the normal case and is not an error.

    ABSENCE AND DISCARD ARE DIFFERENT FACTS, and conflating them was CS-443.
    A file that could not be read, sized, decoded or parsed used to return the
    same empty mapping as no file at all, in silence. The operator-facing
    consequence was not merely quiet: having recovered no declarations, the
    tool went on to advise the operator to write the very declaration they had
    already written and that had just been thrown away. Every discard is
    therefore reported through ``warnings`` while absence stays silent - a
    channel that fires on every clean checkout is a channel nobody reads.

    Reporting is the ONLY thing that changed. Each branch returns exactly what
    it returned before, because resolution runs underneath every entry point
    and this reader must not move an outcome. ``_override`` passes no
    collector and is unaffected.

    Args:
        warnings: Optional collector, appended to in place. Omit it to read
            the configuration without asking what was thrown away.

    Returns:
        The string-valued entries, or an empty mapping. Never raises.
    """
    path = local_config_path()
    raw = _read_local_config(path, warnings)
    if raw is None:
        return {}
    try:
        payload = json.loads(raw)
    except ValueError:
        _note(
            warnings,
            WARN_LOCAL_CONFIG_MALFORMED,
            path,
            "the file is not valid JSON; every declaration in it was discarded",
        )
        return {}
    if not isinstance(payload, dict):
        _note(
            warnings,
            WARN_LOCAL_CONFIG_NOT_A_MAPPING,
            path,
            "the file is valid JSON but not an object; no declaration could be read",
        )
        return {}
    values: dict[str, str] = {}
    for key, value in payload.items():
        name = str(key)
        if isinstance(value, str):
            values[name] = value
        else:
            # The quietest path of all: one key at a time, with the surviving
            # keys still returned, so the mapping looks well-formed and merely
            # incomplete.
            _note(
                warnings,
                WARN_LOCAL_CONFIG_NON_STRING_VALUE,
                name,
                "the value is not a string; this one entry was dropped",
            )
    return values


def _override(env_name: str, config_key: str) -> tuple[str, str] | None:
    """Return the highest-precedence override for one resolved path.

    Args:
        env_name: Environment variable to check first.
        config_key: config/local.json key to check second.

    Returns:
        (value, source label), or None when neither is set.
    """
    from_env = (os.environ.get(env_name) or "").strip()
    if from_env:
        return from_env, f"env:{env_name}"
    from_config = (local_config().get(config_key) or "").strip()
    if from_config:
        return from_config, f"config:{config_key}"
    return None


# --- install ----------------------------------------------------------------


def _drive_roots() -> list[Path]:
    """List existing filesystem roots to probe. Discovered, never one drive.

    Returns:
        Every drive root that exists, or ``/`` off Windows.
    """
    if sys.platform != "win32":
        return [Path("/")]
    roots = []
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        candidate = Path(f"{letter}:/")
        try:
            if candidate.exists():
                roots.append(candidate)
        except OSError:
            continue
    return roots


def _registry_steam_roots() -> list[Path]:
    """Read Steam roots out of the Windows registry, if there are any.

    Returns:
        Registry-named Steam roots, empty off Windows or with no Steam key.
    """
    if sys.platform != "win32":
        return []
    try:
        # PLC0415: winreg is a Windows-only stdlib module. A top-level import
        # would make this file unimportable on any other platform, and the
        # rule suite has to run on a machine with no game install at all.
        import winreg  # noqa: PLC0415
    except ImportError:
        return []
    probes = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    )
    roots: list[Path] = []
    for hive, subkey, value_name in probes:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                raw, _kind = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        if raw:
            roots.append(Path(str(raw)))
    return roots


def _steam_roots() -> list[Path]:
    """List candidate Steam roots, registry first then the defaults.

    Returns:
        Unique candidate roots in probe order. Existence is not checked here.
    """
    roots = _registry_steam_roots()
    for drive in _drive_roots():
        roots.extend(
            drive / suffix for suffix in ("Program Files (x86)/Steam", "Program Files/Steam")
        )
    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def _steam_library_paths() -> list[Path]:
    """Parse libraryfolders.vdf under each Steam root for library paths.

    Steam puts games on any drive the user chose, so the library index is the
    only reliable answer and the default locations below it are a fallback.

    Returns:
        Every library path named by any readable libraryfolders.vdf, plus the
        Steam roots themselves.
    """
    libraries: list[Path] = []
    for steam_root in _steam_roots():
        for relative in ("steamapps/libraryfolders.vdf", "config/libraryfolders.vdf"):
            vdf = steam_root / relative
            try:
                if not vdf.is_file():
                    continue
                text = vdf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            libraries.append(steam_root)
            libraries.extend(
                Path(match.group(1).replace("\\\\", "/"))
                for match in re.finditer(r'"path"\s*"([^"]+)"', text)
            )
    return libraries


def _detected_game_dir() -> tuple[Path | None, str]:
    """Auto-detect the install, with no override in play.

    Returns:
        (install directory, resolver label), or (None, "unresolved").
    """
    for library in _steam_library_paths():
        candidate = library.joinpath(*GAME_RELATIVE_TO_LIBRARY)
        try:
            if candidate.is_dir():
                return candidate, "steam-library-index"
        except OSError:
            continue

    for drive in _drive_roots():
        for suffix in DEFAULT_INSTALL_SUFFIXES:
            candidate = drive / suffix
            try:
                if candidate.is_dir():
                    return candidate, "default-location"
            except OSError:
                continue
    return None, "unresolved"


def resolve_game_dir() -> tuple[Path | None, str]:
    """Locate the game install directory.

    Order: CLOCKSPEED_GAME_DIR, then config/local.json "game_dir", then the
    Steam library index, then the common default locations. The Steam path is
    never hardcoded as the answer.

    Returns:
        (install directory, the resolution path that found it). The directory
        is None when nothing resolved, and the label says which step spoke -
        including when an override was set but does not name a directory.
    """
    override = _override(ENV_GAME_DIR, CONFIG_GAME_DIR)
    if override is not None:
        value, source = override
        candidate = Path(value)
        if candidate.is_dir():
            return candidate, source
        return None, f"{source} set but not a directory"
    return _detected_game_dir()


# --- saves ------------------------------------------------------------------


def resolve_save_root() -> Path | None:
    """Locate the save root, never hardcoding a path to it.

    Order: CLOCKSPEED_SAVE_ROOT, then config/local.json "save_root", then
    %LOCALAPPDATA%/FactoryGame/Saved/SaveGames. %LOCALAPPDATA% itself falls
    back to the home directory when the variable is unset.

    Whatever resolves is remembered, so redact() can key the account-directory
    position on it. That matters for a relocated root, where the fixed
    FactoryGame/Saved/SaveGames marker is not in the string at all.

    Returns:
        The save root, or None if it does not exist. An override naming a
        missing directory returns None rather than falling through, so a
        wrong override cannot be mistaken for a correct auto-detection.
    """
    override = _override(ENV_SAVE_ROOT, CONFIG_SAVE_ROOT)
    if override is not None:
        root = Path(override[0])
        return _remember_save_root(root) if root.is_dir() else None

    local = os.environ.get("LOCALAPPDATA")
    if not local:
        try:
            local = str(Path.home() / "AppData" / "Local")
        except (OSError, RuntimeError):
            return None
    root = Path(local).joinpath(*SAVE_ROOT_PARTS)
    return _remember_save_root(root) if root.is_dir() else None


def _safe_mtime(path: Path) -> float:
    """Return a modification time, or 0.0 for anything unreadable.

    Args:
        path: Path to stat.

    Returns:
        The mtime, or 0.0 - which sorts an unreadable directory last rather
        than failing a listing that is otherwise fine.
    """
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def numeric_account_dirs(save_root: Path | None) -> list[Path]:
    """List the all-digit subdirectories of the save root, newest first.

    The directory NAME is a platform account id and is personal data. Callers
    get paths so they can stat them; they must never print the names. Ordering
    is by modification time descending, with the name as a tiebreak so the
    answer is identical on two runs over the same directory - an advisor that
    disagrees with itself between runs is a bug (CLAUDE.md section 1).

    Args:
        save_root: The save root, or None.

    Returns:
        Account directories, most recently modified first. Empty if the save
        root is None, missing or unreadable.
    """
    if save_root is None:
        return []
    found: list[Path] = []
    try:
        for child in save_root.iterdir():
            try:
                if child.is_dir() and child.name.isdigit():
                    found.append(child)
            except OSError:
                continue
    except OSError:
        return []
    found.sort(key=lambda path: (-_safe_mtime(path), path.name))
    for path in found:
        _remember_account_dir(path)
    return found


def resolve_account_dir(save_root: Path | None) -> Path | None:
    """Pick the account directory to read saves from.

    Order: CLOCKSPEED_ACCOUNT_DIR, then config/local.json "account_dir", then
    the most-recently-modified all-digit directory. BOOTSTRAP.md section 2.2
    requires both halves of that - pick by most-recently-modified, and make it
    overridable - because a machine with two accounts would otherwise silently
    switch worlds when the other account saved more recently.

    An override may be a bare directory name, which is joined onto the save
    root, or an absolute path, which is used as given so an account directory
    that has been moved or copied elsewhere still works.

    NO SHAPE CHECK IS APPLIED TO AN OVERRIDE, and that is deliberate rather
    than an omission. Auto-detection looks for all-digit names because that is
    what the platform this project was probed against writes; an override
    exists precisely so a directory that does NOT look like that - an Epic hex
    token, a Microsoft Store GUID, a copy the operator renamed - can still be
    used. Rejecting a non-digit override would break the case the override is
    for. The privacy consequence is handled where it belongs: whatever this
    returns is recorded so redact() strips it, which is what makes an override
    naming a path outside the save root safe to render.

    Args:
        save_root: The save root, or None.

    Returns:
        The account directory, or None when none resolves. An override that
        names a missing directory returns None rather than falling back to
        detection.
    """
    override = _override(ENV_ACCOUNT_DIR, CONFIG_ACCOUNT_DIR)
    if override is not None:
        candidate = Path(override[0])
        if not candidate.is_absolute():
            if save_root is None:
                return None
            candidate = save_root / override[0]
        return _remember_account_dir(candidate) if candidate.is_dir() else None

    found = numeric_account_dirs(save_root)
    return _remember_account_dir(found[0]) if found else None
