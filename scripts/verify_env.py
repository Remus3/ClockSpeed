#!/usr/bin/env python3
"""Clockspeed environment verification.

Prints one row per external dependency with FOUND or MISSING plus a discovered
value, then the live state of every port in the reserved band. Exits non-zero
when any HARD dependency is missing. A bound port in the band is a SOFT failure
carrying a loud note.

Nothing here hardcodes a machine-specific fact. The interpreter comes from
sys.executable, and every path is discovered at runtime.

RESOLUTION IS NOT IMPLEMENTED HERE, AND THAT IS THE POINT. The phase 2 note
this docstring used to carry has been honoured: clockspeed/data/locate.py now
owns finding the install, the save root and the account directory, and owns
the precedence they follow - environment variable, then config/local.json,
then auto-detection. This script imports those resolvers and reports what they
answer, so what it prints is what the rest of the project will actually use. A
second copy here would be a second answer to "where is the game" waiting to
disagree with the first.

The re-export is deliberate and load-bearing rather than incidental:
tools/facts_probe.py imports resolve_game_dir, resolve_save_root and
numeric_account_dirs from THIS module, so keeping those names bound here is
what made the delegation cost its caller nothing.

The build string is still read here, because it is a property of the installed
binaries rather than a location.

PRIVACY: every path this script prints goes through redact() first, and the
account directory NAME is never printed - only a count and a redacted marker.
This output is meant to be safe to paste into an issue.

Usage:
    python scripts/verify_env.py
    python scripts/verify_env.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# The bootstrap order in CONVENTIONS.md section 1 runs this script in a FRESH
# CLONE, before anything is installed and with no virtual environment active,
# so the package cannot be assumed importable from site-packages. Running a
# file puts that file's own directory on sys.path, not the repository root -
# hence the insert. Without it, `python scripts/verify_env.py` in a fresh
# clone dies on the import below instead of printing the dependency table it
# exists to print.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# E402: this import must follow the sys.path insert above. The four names are
# re-exported by being bound here - tools/facts_probe.py reads three of them
# off this module (see the module docstring).
from clockspeed.data.locate import (  # noqa: E402
    numeric_account_dirs,
    redact,
    resolve_game_dir,
    resolve_save_root,
)

# --- policy constants -------------------------------------------------------

MIN_PYTHON = (3, 13)

EXPECTED_HOOKS_PATH = ".githooks"

# The five known CommunityResources artifacts, by relative path. Names only. No
# size is asserted against a literal: a game patch changes them, and a measured
# number frozen into a checker is a lie with a timestamp on it. Sizes are
# probed and reported.
COMMUNITY_ARTIFACTS = (
    "Docs/en-US.json",
    "FactoryGame.usmap",
    "CustomVersions.json",
    "DedicatedServerAPIDocs.md",
    "Headers.zip",
)

USMAP_RELATIVE = "FactoryGame.usmap"

# The default install locations, the Steam library parsing and the redaction
# needles all live in clockspeed/data/locate.py. Do not reintroduce them here.

BUILD_STRING_RE = re.compile(r"\+\+[A-Za-z0-9+._-]{0,120}CL-\d+")

MAX_BAND_WIDTH = 512
ADDRESS_IN_USE_ERRNOS = frozenset({48, 98})
ADDRESS_IN_USE_WINERRORS = frozenset({10048, 10013})
MAX_EXE_CANDIDATES = 6
MAX_MANIFEST_BYTES = 2_000_000

_DEP_HEADERS = ("SCOPE", "DEPENDENCY", "STATUS", "DISCOVERED VALUE")
_PORT_HEADERS = ("PORT", "STATE", "ALLOCATION", "DETAIL")


# --- small helpers ----------------------------------------------------------


def repo_root() -> Path:
    """Return the repository root, derived from this file's location."""
    return Path(__file__).resolve().parents[1]


def _run(cmd: list[str], timeout: int = 20) -> str | None:
    """Run a command and return stripped stdout, or None on any failure."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip()


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _tool_version(exe_name: str) -> tuple[bool, str]:
    """Locate an executable on PATH and read its version line."""
    found = shutil.which(exe_name)
    if not found:
        return False, "not on PATH"
    version = _first_line(_run([found, "--version"]))
    where = redact(found)
    if version:
        return True, f"{version}  ({where})"
    return True, where


def _module_version(module: str) -> tuple[bool, str]:
    """Fall back to `python -m <module> --version` for a pip-installed tool."""
    version = _first_line(_run([sys.executable, "-m", module, "--version"]))
    if version:
        return True, f"{version}  (via python -m {module})"
    return False, "not importable as a module"


def _size_of(path: Path) -> str:
    try:
        return f"{path.stat().st_size} bytes"
    except OSError:
        return "size unreadable"


# --- build string -----------------------------------------------------------


def _version_info_strings(path: Path) -> dict[str, str]:
    """Read a Windows PE version resource with ctypes only. No dependency."""
    if sys.platform != "win32":
        return {}
    out: dict[str, str] = {}
    try:
        # PLC0415: ctypes.wintypes is Windows-only, same reason as winreg above.
        import ctypes  # noqa: PLC0415
        from ctypes import wintypes  # noqa: PLC0415

        version_dll = ctypes.WinDLL("version.dll")
        version_dll.GetFileVersionInfoSizeW.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        version_dll.GetFileVersionInfoSizeW.restype = wintypes.DWORD
        version_dll.GetFileVersionInfoW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        version_dll.GetFileVersionInfoW.restype = wintypes.BOOL
        version_dll.VerQueryValueW.argtypes = [
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_uint),
        ]
        version_dll.VerQueryValueW.restype = wintypes.BOOL

        target = str(path)
        handle = wintypes.DWORD(0)
        size = version_dll.GetFileVersionInfoSizeW(target, ctypes.byref(handle))
        if not size:
            return {}
        buffer = ctypes.create_string_buffer(size)
        if not version_dll.GetFileVersionInfoW(target, 0, size, buffer):
            return {}

        pointer = ctypes.c_void_p()
        length = ctypes.c_uint()
        translations: list[tuple[int, int]] = []
        found = version_dll.VerQueryValueW(
            buffer, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(length)
        )
        if found and length.value:
            words = ctypes.cast(pointer, ctypes.POINTER(wintypes.WORD))
            translations = [
                (words[index * 2], words[index * 2 + 1]) for index in range(length.value // 4)
            ]
        if not translations:
            translations = [(0x0409, 0x04B0)]

        for language, codepage in translations:
            for key in ("ProductVersion", "FileVersion", "ProductName", "FileDescription"):
                sub_block = f"\\StringFileInfo\\{language:04x}{codepage:04x}\\{key}"
                value_ptr = ctypes.c_void_p()
                value_len = ctypes.c_uint()
                hit = version_dll.VerQueryValueW(
                    buffer, sub_block, ctypes.byref(value_ptr), ctypes.byref(value_len)
                )
                if hit and value_len.value:
                    text = ctypes.wstring_at(value_ptr, value_len.value).rstrip("\x00").strip()
                    if text and key not in out:
                        out[key] = text
    except Exception:
        # A version-resource read must never be able to fail a probe. Unknown
        # beats a guess, and both beat a traceback out of an environment check.
        return {}
    return out


def _executable_candidates(game_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    try:
        candidates.extend(sorted(game_dir.glob("*.exe"))[:MAX_EXE_CANDIDATES])
        win64 = game_dir / "FactoryGame" / "Binaries" / "Win64"
        candidates.extend(sorted(win64.glob("*-Shipping.exe"))[:4])
        candidates.extend(sorted(win64.glob("*FactoryGame-Win64-Shipping.dll"))[:4])
    except OSError:
        return candidates
    return candidates


def _build_from_version_info(game_dir: Path) -> tuple[str | None, str]:
    """Best build string from a PE version resource, plus how it was read."""
    fallback: tuple[str | None, str] = (None, "")
    for candidate in _executable_candidates(game_dir):
        strings = _version_info_strings(candidate)
        for key in ("ProductVersion", "FileVersion"):
            value = strings.get(key, "")
            if BUILD_STRING_RE.fullmatch(value):
                return value, f"version-info:{key}"
            if value and fallback[0] is None:
                fallback = (value, f"version-info:{key} (not a full build string)")
    return fallback


def _build_from_modules(game_dir: Path) -> tuple[str | None, str]:
    win64 = game_dir / "FactoryGame" / "Binaries" / "Win64"
    try:
        modules_files = sorted(win64.glob("*.modules"))[:4]
    except OSError:
        return None, ""
    for modules_file in modules_files:
        try:
            payload = json.loads(modules_file.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        build_id = str(payload.get("BuildId", "")).strip()
        if build_id:
            return f"CL-{build_id}", "modules-buildid (changelist only)"
    return None, ""


def _build_from_manifest(game_dir: Path) -> tuple[str | None, str]:
    for name in ("Manifest_NonUFSFiles_Win64.txt", "Manifest_DebugFiles_Win64.txt"):
        manifest = game_dir / name
        try:
            if not manifest.is_file():
                continue
            text = manifest.read_text(encoding="utf-8", errors="replace")[:MAX_MANIFEST_BYTES]
        except OSError:
            continue
        match = BUILD_STRING_RE.search(text)
        if match:
            return match.group(0), f"manifest:{name}"
    return None, ""


def read_build_string(game_dir: Path | None) -> tuple[str | None, str]:
    """Return (build string, how it was read) for the installed game.

    Primary source is the shipping executable's PE version resource, read with
    ctypes and no third-party dependency. Fallbacks are the shipping .modules
    manifest, which carries only the changelist, then the packaged file
    manifests. If none of them answers the result is unknown - never a guess,
    because a wrong build string silently invalidates every version-pinned
    artifact downstream.
    """
    if game_dir is None:
        return None, "no install"

    value, source = _build_from_version_info(game_dir)
    if value is not None and source.endswith(("ProductVersion", "FileVersion")):
        return value, source

    for probe in (_build_from_modules, _build_from_manifest):
        found, how = probe(game_dir)
        if found is not None:
            return found, how

    if value is not None:
        return value, source
    return None, "unknown"


# --- ports ------------------------------------------------------------------


def load_ports(root: Path) -> tuple[dict | None, str]:
    """Load config/ports.json. Returns (payload, error message)."""
    path = root / "config" / "ports.json"
    if not path.is_file():
        return None, "config/ports.json not found"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except (OSError, ValueError) as exc:
        return None, f"config/ports.json unreadable: {exc}"


def band_ports(payload: dict | None) -> list[int]:
    """Return every port in the recorded band, or an empty list if unusable."""
    if not payload:
        return []
    band = payload.get("band") or {}
    try:
        start = int(band["start"])
        end = int(band["end"])
    except (KeyError, TypeError, ValueError):
        return []
    if end < start or end - start > MAX_BAND_WIDTH:
        return []
    return list(range(start, end + 1))


def probe_port(port: int) -> tuple[str, str]:
    """Return (state, detail). FREE means nothing is bound on the loopback."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1.0)
        sock.bind(("127.0.0.1", port))
    except OSError as exc:
        code = getattr(exc, "errno", None)
        winerror = getattr(exc, "winerror", None)
        if code in ADDRESS_IN_USE_ERRNOS or winerror in ADDRESS_IN_USE_WINERRORS:
            return "BOUND", "something is listening"
        return "ERROR", str(exc)
    else:
        return "FREE", ""
    finally:
        sock.close()


# --- checks -----------------------------------------------------------------


def _row(scope: str, name: str, ok: bool, value: str, note: str = "") -> dict:
    return {
        "scope": scope,
        "name": name,
        "status": "FOUND" if ok else "MISSING",
        "ok": ok,
        "value": value,
        "note": note,
    }


def _hard_rows(root: Path, facts: dict) -> list[dict]:
    version = ".".join(str(part) for part in sys.version_info[:3])
    minimum = ".".join(str(part) for part in MIN_PYTHON)
    python_ok = sys.version_info[:2] >= MIN_PYTHON
    facts["python_version"] = version
    rows = [
        _row(
            "HARD",
            f"python >= {minimum}",
            python_ok,
            f"{version}  ({redact(sys.executable)})",
            "" if python_ok else "interpreter predates the minimum",
        )
    ]

    git_ok, git_value = _tool_version("git")
    rows.append(_row("HARD", "git", git_ok, git_value))

    tree = _run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"]) if git_ok else None
    tree_ok = tree == "true"
    rows.append(
        _row(
            "HARD",
            "repo root is a git work tree",
            tree_ok,
            redact(root) if tree_ok else "rev-parse says no",
        )
    )

    hooks_dir = root / EXPECTED_HOOKS_PATH
    hooks_dir_ok = hooks_dir.is_dir()
    hook_names: list[str] = []
    if hooks_dir_ok:
        try:
            hook_names = sorted(path.name for path in hooks_dir.iterdir() if path.is_file())
        except OSError:
            hook_names = []
    if hook_names:
        hooks_value = f"{len(hook_names)} hook file(s): {', '.join(hook_names)}"
    elif hooks_dir_ok:
        hooks_value = "present but empty"
    else:
        hooks_value = "absent"
    rows.append(
        _row(
            "HARD",
            f"{EXPECTED_HOOKS_PATH} directory",
            hooks_dir_ok,
            hooks_value,
            "" if hooks_dir_ok else "run: python scripts/install_hooks.py",
        )
    )

    configured = (
        _run(["git", "-C", str(root), "config", "--get", "core.hooksPath"]) if git_ok else None
    )
    hooks_path_ok = (configured or "").replace("\\", "/").strip("/") == EXPECTED_HOOKS_PATH
    facts["hooks_path"] = configured or ""
    rows.append(
        _row(
            "HARD",
            f"core.hooksPath == {EXPECTED_HOOKS_PATH}",
            hooks_path_ok,
            configured or "unset",
            ""
            if hooks_path_ok
            else "a fresh clone runs ZERO protection until install_hooks.py sets this",
        )
    )

    for name in ("pytest", "ruff"):
        ok, value = _tool_version(name)
        if not ok:
            ok, value = _module_version(name)
        rows.append(_row("HARD", name, ok, value))
    return rows


def _optional_tool_rows() -> list[dict]:
    rows = []
    for exe in ("node", "gh", "mypy"):
        ok, value = _tool_version(exe)
        if not ok and exe == "mypy":
            ok, value = _module_version(exe)
        rows.append(_row("SOFT", exe, ok, value))
    return rows


def _locale_file_count(community: Path) -> int:
    docs_dir = community / "Docs"
    if not docs_dir.is_dir():
        return 0
    try:
        return sum(1 for path in docs_dir.iterdir() if path.is_file() and path.suffix == ".json")
    except OSError:
        return 0


def _game_rows(facts: dict) -> list[dict]:
    game_dir, resolver = resolve_game_dir()
    facts["game_resolver"] = resolver
    rows = [
        _row(
            "SOFT",
            "game install",
            game_dir is not None,
            f"{redact(game_dir)}  (resolved by {resolver})"
            if game_dir is not None
            else "not resolved (tried env, steam library index, defaults)",
            "" if game_dir is not None else "the rule suite must still run without it",
        )
    ]

    build_string, build_source = read_build_string(game_dir)
    facts["game_build"] = build_string or ""
    rows.append(
        _row(
            "SOFT",
            "game build string",
            build_string is not None,
            f"{build_string}  (via {build_source})" if build_string else "unknown",
        )
    )

    community = (game_dir / "CommunityResources") if game_dir is not None else None
    community_ok = community is not None and community.is_dir()
    locale_count = _locale_file_count(community) if community_ok else 0
    rows.append(
        _row(
            "SOFT",
            "CommunityResources",
            community_ok,
            f"{redact(community)}  ({locale_count} locale json file(s) in Docs/)"
            if community_ok
            else "absent",
        )
    )

    for relative in COMMUNITY_ARTIFACTS:
        artifact = (community / relative) if community_ok else None
        artifact_ok = artifact is not None and artifact.is_file()
        rows.append(
            _row(
                "SOFT",
                f"  CommunityResources/{relative}",
                artifact_ok,
                _size_of(artifact) if artifact_ok else "absent",
            )
        )

    usmap = (community / USMAP_RELATIVE) if community_ok else None
    usmap_ok = usmap is not None and usmap.is_file()
    rows.append(
        _row(
            "SOFT",
            "usmap property mappings",
            usmap_ok,
            _size_of(usmap) if usmap_ok else "absent",
            "same file as the CommunityResources row above; called out separately "
            "because the save reader is built around it",
        )
    )
    return rows


def _save_rows(facts: dict) -> list[dict]:
    save_root = resolve_save_root()
    rows = [
        _row(
            "SOFT",
            "save root",
            save_root is not None,
            redact(save_root) if save_root is not None else "absent",
        )
    ]
    accounts = numeric_account_dirs(save_root)
    facts["account_dir_count"] = len(accounts)
    rows.append(
        _row(
            "SOFT",
            "numeric account dir",
            bool(accounts),
            f"{len(accounts)} found; using <account-dir:redacted> (most recently modified)"
            if accounts
            else "none found",
            "the directory name is a platform account id and is never printed",
        )
    )
    return rows


def collect_rows(root: Path) -> tuple[list[dict], list[dict], dict]:
    """Run every check. Returns (dependency rows, port rows, extra facts)."""
    facts: dict = {}
    rows = _hard_rows(root, facts)
    rows.extend(_optional_tool_rows())
    rows.extend(_game_rows(facts))
    rows.extend(_save_rows(facts))

    ports_payload, ports_error = load_ports(root)
    if ports_payload is not None:
        band = ports_payload.get("band") or {}
        ports_value = (
            f"base {ports_payload.get('base')}, band {band.get('start')}-{band.get('end')}"
        )
    else:
        ports_value = ports_error
    rows.append(_row("SOFT", "config/ports.json", ports_payload is not None, ports_value))

    allocations = (ports_payload or {}).get("allocations") or {}
    port_rows = []
    for port in band_ports(ports_payload):
        state, detail = probe_port(port)
        port_rows.append(
            {
                "port": port,
                "state": state,
                "detail": detail,
                "allocation": allocations.get(str(port), "reserved"),
            }
        )
    return rows, port_rows, facts


# --- rendering --------------------------------------------------------------


def _table(headers: tuple[str, ...], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    out = ["  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))).rstrip()]
    out.append("  ".join("-" * widths[i] for i in range(len(headers))))
    out.extend(
        "  ".join(row[i].ljust(widths[i]) for i in range(len(headers))).rstrip() for row in rows
    )
    return out


def _render_ports(port_rows: list[dict], bound: list[dict]) -> list[str]:
    if not port_rows:
        return ["Reserved port band: NOT PROBED - no usable band in config/ports.json"]
    out = ["Reserved port band (config/ports.json is the owner of these numbers)"]
    out.extend(
        _table(
            _PORT_HEADERS,
            [
                [str(row["port"]), row["state"], row["allocation"], row["detail"]]
                for row in port_rows
            ],
        )
    )
    if bound:
        out.append("")
        out.append("!" * 72)
        out.append(f"SOFT FAILURE: {len(bound)} port(s) in the reserved band are not free.")
        out.extend(f"  {row['port']} is {row['state']} {row['detail']}" for row in bound)
        out.append("The band was recorded as free at allocation time. Something else took a")
        out.append("port, or a previous Clockspeed process did not shut down. Find it before")
        out.append("binding, and re-record config/ports.json if the band has to move.")
        out.append("!" * 72)
    return out


def render(rows: list[dict], port_rows: list[dict], root: Path) -> list[str]:
    """Render the dependency table, the port table and the verdict."""
    out = ["Clockspeed environment verification", f"repo: {redact(root)}", ""]
    out.extend(
        _table(
            _DEP_HEADERS,
            [[row["scope"], row["name"], row["status"], row["value"]] for row in rows],
        )
    )

    notes = [row for row in rows if row["note"] and not row["ok"]]
    if notes:
        out.extend(["", "Notes on missing items:"])
        out.extend(f"  {row['scope']:<8} {row['name']}: {row['note']}" for row in notes)

    bound = [row for row in port_rows if row["state"] != "FREE"]
    out.append("")
    out.extend(_render_ports(port_rows, bound))

    hard_missing = [row for row in rows if row["scope"] == "HARD" and not row["ok"]]
    soft_missing = [row for row in rows if row["scope"] == "SOFT" and not row["ok"]]
    hard_total = sum(1 for row in rows if row["scope"] == "HARD")
    soft_total = sum(1 for row in rows if row["scope"] == "SOFT")
    out.append("")
    out.append(
        f"HARD: {hard_total - len(hard_missing)}/{hard_total} present    "
        f"SOFT: {soft_total - len(soft_missing)}/{soft_total} present    "
        f"ports free: {len(port_rows) - len(bound)}/{len(port_rows)}"
    )
    if hard_missing:
        names = ", ".join(row["name"] for row in hard_missing)
        out.append(f"VERDICT: FAIL - missing HARD dependencies: {names}")
    else:
        out.append("VERDICT: PASS - every HARD dependency is present")
    if soft_missing:
        names = ", ".join(row["name"].strip() for row in soft_missing)
        out.append(f"SOFT missing (reported, not fatal): {names}")
    return out


def main(argv: list[str] | None = None) -> int:
    """Verify the environment and print the result. Returns the exit code."""
    parser = argparse.ArgumentParser(
        description="Verify the Clockspeed environment. Exits non-zero on a missing HARD "
        "dependency. Never prints an account id, a world name or a home path."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    root = repo_root()
    rows, port_rows, facts = collect_rows(root)
    hard_missing = [row for row in rows if row["scope"] == "HARD" and not row["ok"]]
    bound = [row for row in port_rows if row["state"] != "FREE"]

    if args.json:
        print(
            json.dumps(
                {
                    "schema": 1,
                    "repo": redact(root),
                    "dependencies": rows,
                    "ports": port_rows,
                    "facts": facts,
                    "hard_missing": [row["name"] for row in hard_missing],
                    "ports_not_free": [row["port"] for row in bound],
                    "verdict": "FAIL" if hard_missing else "PASS",
                },
                indent=2,
            )
        )
    else:
        print("\n".join(render(rows, port_rows, root)))

    return 1 if hard_missing else 0


if __name__ == "__main__":
    sys.exit(main())
