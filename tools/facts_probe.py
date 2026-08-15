#!/usr/bin/env python3
"""Clockspeed live-state probe for SessionStart injection.

Emits one compact JSON object describing the live state of the machine at the
moment a session starts: interpreter, git, hook wiring, game install and build
string, and save-file counts.

CONTEXT IS THE BINDING BUDGET. This output is injected into EVERY session, so it
is deliberately small - counts and booleans, never listings, and no
pretty-printing. Anything that wants detail runs scripts/verify_env.py instead.

REDACTION IS THE DEFAULT, NOT A MODE.
The save directory is named after a platform account id, the world name is
operator-chosen, and save filenames embed the world name. All three are personal
data (BOOTSTRAP.md section 2.2). Every path this probe emits by default goes
through clockspeed.data.locate.redact() first, so what appears is the SHAPE of
the answer - "<localappdata>/FactoryGame/Saved/SaveGames" - and never the
operator's home directory or their account id.

Two fields are withheld entirely rather than redacted, because redacting them
would leave a constant that says nothing: the account directory NAMES, whose
count is already reported, and the newest save FILENAME, which is a world name
with a suffix on it. Both appear only under --unredacted, which exists for local
debugging and which nothing consuming this probe should ever pass.

THE GIT FACTS ARE PART OF THAT, and were not always (CS-206). core.hooksPath is
whatever the operator configured, which git returns verbatim and which is an
ABSOLUTE path on this project's own checkout; a branch name is operator-chosen
free text, and naming a branch after the account that owns it is an everyday
convention. Both now take the same route as every other field. The branch can
never BE a path - git's ref format forbids the backslash, the colon and the
space - and is redacted for the separate reason that the Windows account name
is personal data in its own right (CLAUDE.md non-negotiable 3).

git.sha is deliberately NOT redacted. A short SHA is machine-generated hex, it
cannot carry a path, and passing it through the redactor would let the digit-run
backstop in locate.redact() rewrite an all-numeric abbreviation into a token.

The build string is read from the shipping executable's PE version resource with
ctypes - no third-party dependency - falling back to the shipping .modules
manifest, which carries only the changelist. If neither answers, the field reads
"unknown". It never guesses: a wrong build string silently invalidates every
version-pinned artifact downstream.

WHERE THE ANSWERS COME FROM. Finding the install, the save root and the account
directory is clockspeed/data/locate.py's job and is imported from there, so this
tool and scripts/verify_env.py cannot disagree about where the game is. Only the
build string still comes from scripts/verify_env.py, because it is a property of
the installed binaries rather than a location.

Usage:
    python tools/facts_probe.py
    python tools/facts_probe.py --json          (alias; the output is JSON already)
    python tools/facts_probe.py --unredacted    (local debugging only)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

GIT_TIMEOUT = 20

# What an operator-controlled value renders as when the redactor itself could
# not be imported. DISTINCT FROM None, which means "not configured": a reader
# has to be able to tell a wired checkout whose value is being withheld from an
# unwired one, and collapsing the two would report an UNPROTECTED repository as
# a protected one. Emitting the raw value instead is not an option - a probe
# that leaks whenever its redactor is missing is the defect, not the fallback.
WITHHELD = "<withheld>"


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


def _load_locate() -> Any:
    """Import the resolvers and the redactor from the data layer.

    Returns:
        The clockspeed.data.locate module.

    Raises:
        ImportError: The package is not importable from this checkout.
    """
    root = repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # PLC0415: the import has to follow the sys.path insert above, and this
    # module must stay runnable as a bare script from any working directory.
    from clockspeed.data import locate  # noqa: PLC0415

    return locate


def _build_string(game_dir: Path | None) -> tuple[str | None, str]:
    """Read the installed build string, or say why it could not be read.

    The reader lives in scripts/verify_env.py and stays there: the build
    string is a property of the installed binaries, not a location, so it is
    the one thing this probe does not get from the data layer.

    Args:
        game_dir: The resolved install, or None.

    Returns:
        (build string or None, how it was read).
    """
    scripts_dir = repo_root() / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        # PLC0415: the import has to follow the sys.path insert above.
        import verify_env  # noqa: PLC0415
    except ImportError:
        return None, "build reader unavailable"
    build, how = verify_env.read_build_string(game_dir)
    return build, str(how)


def _git(root: Path, args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip()


def _iso(timestamp: float) -> str:
    # A local wall-clock timestamp is what the operator reads against their own
    # clock. A UTC-aware stamp here would be correct and unhelpful.
    return datetime.fromtimestamp(timestamp).replace(microsecond=0).isoformat()


def _redact_or_withhold(value: str | None, locate: Any | None) -> str | None:
    """Redact an operator-controlled string, or withhold it if that is impossible.

    THE EMPTY CHECK IS THE POINT, not a tidiness habit. locate.redact() accepts
    an ``object`` and stringifies whatever it is handed, so redact(None) returns
    the truthy string "None". Any caller that wrote ``redact(value) or None``
    would therefore turn "this is not configured" into a value that reads as
    configured, which is the one failure mode a fix here must not introduce.

    Args:
        value: The raw string, or None when git had no answer.
        locate: The data layer, or None when it did not import.

    Returns:
        The redacted string, WITHHELD when there is no redactor, or None when
        there was nothing configured to redact.
    """
    if not value:
        return None
    if locate is None:
        return WITHHELD
    # ANNOTATED AT THE SEAM, not suppressed at the return. `locate` is the
    # lazily imported data layer and is typed Any, so this call yields Any and
    # `warn_return_any` rejects handing it straight back as `str | None`. The
    # annotation records the real contract where the Any enters the function -
    # clockspeed/data/locate.py:303 declares `def redact(text: object) -> str`,
    # which is also why the None case cannot arrive here.
    redacted: str = locate.redact(value)
    return redacted


def _hooks_path(root: Path, configured: str | None, locate: Any | None) -> str | None:
    """Render core.hooksPath so it keeps its meaning without carrying a home path.

    WHY NOT SIMPLY WITHHOLD IT. This field answers exactly one question a
    SessionStart reader has - are the hooks wired, and to this repository's own
    .githooks - and a bare token answers none of it. A fresh clone runs zero
    protection until someone wires it (CLAUDE.md section 2.2), so "no value" and
    "some value" are genuinely different states worth injecting. The value is
    therefore REDUCED rather than withheld: the absolute prefix is the personal
    part, the tail is the informative part, and only the prefix goes.

    REPO-RELATIVE FIRST, REDACTION SECOND. scripts/install_hooks.py writes the
    relative ".githooks", but git accepts an absolute value too and this
    project's own checkout carries one, so both shapes occur in practice. An
    absolute path INSIDE the checkout is rendered relative to it - the same
    answer with the machine-specific prefix removed - and that also closes a
    leak class redaction cannot reach, because locate.redact() builds its home
    needles from the ENVIRONMENT and a checkout under a directory the
    environment never names matches none of them. Everything else falls through
    to locate.redact(), which is the project's single redactor
    (clockspeed/data/locate.py) rather than a second one invented here.

    Both sides are resolved before being compared so the two spellings Windows
    offers for the same directory - the 8.3 short form and the long form - do
    not defeat the containment check.

    Args:
        root: The repository root.
        configured: Whatever ``git config --get core.hooksPath`` said. None
            when the key is unset, "" when it is set to an empty string.
        locate: The data layer, or None when it did not import.

    Returns:
        The rendering, or None when no hooks path is configured. An unset key
        and an empty value both wire nothing, so both answer None.
    """
    if not configured:
        return None
    candidate = Path(configured)
    if candidate.is_absolute():
        with contextlib.suppress(OSError, ValueError):
            return candidate.resolve().relative_to(root.resolve()).as_posix()
    return _redact_or_withhold(str(candidate), locate)


def _git_facts(root: Path, locate: Any | None, unredacted: bool) -> dict:
    head = _git(root, ["rev-parse", "--short", "--verify", "HEAD"])
    branch = _git(root, ["symbolic-ref", "--short", "-q", "HEAD"])
    if not branch:
        branch = _git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    status = _git(root, ["status", "--porcelain"])
    hooks_path = _git(root, ["config", "--get", "core.hooksPath"])
    if not unredacted:
        branch = _redact_or_withhold(branch, locate)
        hooks_path = _hooks_path(root, hooks_path, locate)
    return {
        "branch": branch or "unknown",
        "head": bool(head),
        # Left exactly as git gave it - see the module docstring. A short SHA
        # is machine-generated hex, not personal data, and not a path.
        "sha": head or None,
        "dirty": bool(status) if status is not None else None,
        "hooks_path": hooks_path or None,
    }


def _game_facts(locate: Any, unredacted: bool) -> dict:
    game_dir, resolver = locate.resolve_game_dir()
    build, build_via = _build_string(game_dir)
    game: dict = {
        "found": game_dir is not None,
        # The resolver label can carry an override value the operator typed,
        # so it is redacted like any other path-bearing string.
        "via": locate.redact(resolver),
        "build": build or "unknown",
        "build_via": build_via,
        "dir": None,
    }
    if game_dir is not None:
        game["dir"] = game_dir.as_posix() if unredacted else locate.redact(game_dir)
    return game


def _save_facts(locate: Any, unredacted: bool) -> dict:
    save_root = locate.resolve_save_root()
    accounts = locate.numeric_account_dirs(save_root)
    sav_count = 0
    newest_time = 0.0
    newest_name = None
    if save_root is not None:
        with contextlib.suppress(OSError):
            for path in save_root.rglob("*.sav"):
                try:
                    stat = path.stat()
                except OSError:
                    continue
                sav_count += 1
                if stat.st_mtime > newest_time:
                    newest_time = stat.st_mtime
                    newest_name = path.name

    save: dict = {
        "root": save_root is not None,
        "accounts": len(accounts),
        "savs": sav_count,
        "newest": _iso(newest_time) if newest_time else None,
        "root_path": None,
    }
    if save_root is not None:
        save["root_path"] = save_root.as_posix() if unredacted else locate.redact(save_root)
    if unredacted:
        # Withheld rather than redacted by default. An account directory name
        # redacts to a placeholder and its count is already reported above; a
        # save filename is a world name with a suffix on it, so redacting it
        # yields a constant. Emitting either as a token would spend context on
        # a string that carries no information.
        save["account_dirs"] = [path.name for path in accounts]
        save["newest_name"] = newest_name
    return save


def probe(unredacted: bool = False) -> dict:
    """Collect the live-state snapshot.

    Redacted unless unredacted is True. The account directory name, the world
    name, save filenames, the configured hooks path and the branch name are
    personal data or carry it, and none of them appears raw by default.
    """
    root = repo_root()

    # Resolved BEFORE the git facts, which is a change of order rather than of
    # output: _git_facts() now needs the redactor too, and a probe that
    # collected git facts first would have had nothing to redact them with.
    try:
        locate: Any | None = _load_locate()
    except ImportError:
        locate = None

    facts: dict = {
        # 2, not 1: "dir" and "root_path" are now present on the DEFAULT path
        # carrying a redacted rendering, where schema 1 emitted them only
        # under --unredacted. A shape change with the version left alone is
        # the drift the field exists to make visible.
        "schema": 2,
        "redacted": not unredacted,
        "py": ".".join(str(part) for part in sys.version_info[:3]),
        "git": _git_facts(root, locate, unredacted),
    }

    if locate is None:
        facts["game"] = {"found": None, "via": "resolver unavailable", "build": "unknown"}
        facts["save"] = {"root": None, "accounts": None, "savs": None, "newest": None}
        facts["probe_error"] = "clockspeed.data.locate not importable"
        return facts

    facts["game"] = _game_facts(locate, unredacted)
    facts["save"] = _save_facts(locate, unredacted)
    return facts


def main(argv: list[str] | None = None) -> int:
    """Print the live-state snapshot as one compact JSON line. Returns 0."""
    parser = argparse.ArgumentParser(
        description="Emit a compact JSON live-state snapshot for SessionStart injection. "
        "Redacted by default; never emits an account id, a world name or a save filename."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="accepted for seam compatibility; the output is JSON with or without it",
    )
    parser.add_argument(
        "--unredacted",
        action="store_true",
        help="LOCAL DEBUGGING ONLY - adds the account directory names and the newest save "
        "filename, and emits the resolved paths, the configured hooks path and the branch "
        "name raw. Never pass this in a hook, a log or a report.",
    )
    args = parser.parse_args(argv)

    facts = probe(unredacted=args.unredacted)
    print(json.dumps(facts, separators=(",", ":"), sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
