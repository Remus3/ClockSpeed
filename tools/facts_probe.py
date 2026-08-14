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


def _git_facts(root: Path) -> dict:
    head = _git(root, ["rev-parse", "--short", "--verify", "HEAD"])
    branch = _git(root, ["symbolic-ref", "--short", "-q", "HEAD"])
    if not branch:
        branch = _git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    status = _git(root, ["status", "--porcelain"])
    hooks_path = _git(root, ["config", "--get", "core.hooksPath"])
    return {
        "branch": branch or "unknown",
        "head": bool(head),
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
    name and save filenames are personal data and never appear by default.
    """
    root = repo_root()
    facts: dict = {
        # 2, not 1: "dir" and "root_path" are now present on the DEFAULT path
        # carrying a redacted rendering, where schema 1 emitted them only
        # under --unredacted. A shape change with the version left alone is
        # the drift the field exists to make visible.
        "schema": 2,
        "redacted": not unredacted,
        "py": ".".join(str(part) for part in sys.version_info[:3]),
        "git": _git_facts(root),
    }

    try:
        locate = _load_locate()
    except ImportError:
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
        help="LOCAL DEBUGGING ONLY - adds the account directory names, the newest save "
        "filename and resolved paths. Never pass this in a hook, a log or a report.",
    )
    args = parser.parse_args(argv)

    facts = probe(unredacted=args.unredacted)
    print(json.dumps(facts, separators=(",", ":"), sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
