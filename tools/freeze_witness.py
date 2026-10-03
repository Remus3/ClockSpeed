"""CS-1219 - the witness that an adjudication's candidate did not move under it.

WHY THIS EXISTS. `CLAUDE.md` section 5 and `tools/headless-queue.md` order the
candidate frozen before an adjudicator is dispatched. Until this tool the order
was prose alone: nothing recorded what was dispatched over and nothing re-checked
it when the verdict came back.

WHAT IT RECORDS, AND WHY THOSE TWO HALVES:

    tree      the git TREE OBJECT of the working state - tracked files plus
              untracked files that .gitignore does not exclude, uncommitted
              edits included. Built through a private temporary index, so the
              caller's real index is never touched. A tree and not a commit: a
              commit that leaves the tree identical is not a move, and an
              uncommitted edit is.
    bytecode  a SHA-256 over every ``.pyc`` in a ``__pycache__`` directory that
              sits beside a tracked or would-be-tracked file - each file's
              repo-relative path and bytes. ``__pycache__/`` is gitignored, so
              the tree half and every porcelain check are blind to a swapped
              ``.pyc``, and a swapped ``.pyc`` is what the interpreter loads.

WHERE THE RECORD LIVES. Wherever the caller says (``--out``), or stdout. Put it
in a scratch path or the gitignored ``data/`` tree: a record written inside the
population would itself move the tree it witnesses.

CLI (``--root`` defaults to this repository; exit 0 unmoved, 1 moved, 2 refused)::

    python tools/freeze_witness.py freeze [--out RECORD]
    python tools/freeze_witness.py check RECORD

``check`` names which half moved. No message carries an absolute path or an
environment value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/provenance_stamp.py does it.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

SCHEMA = 1
SUBPROCESS_TIMEOUT_SECONDS = 300
RENAME_ATTEMPTS = 5
REPO_ROOT = _TOOLS_DIR.parent

#: A pre-push hook exports GIT_DIR; inheriting any of these would witness a
#: different repository or index than ``--root`` names.
_GIT_RELOCATING = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
    }
)


class WitnessError(Exception):
    """A refusal: git could not answer, or a record does not parse."""


def _git_env(index_file: Path | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() not in _GIT_RELOCATING}
    if index_file is not None:
        env["GIT_INDEX_FILE"] = str(index_file)
    return env


def _git(root: Path, *args: str, index_file: Path | None = None) -> bytes:
    git = resolve_tool("git")
    if git is None:
        raise WitnessError("git is not on PATH")
    try:
        proc = subprocess.run(
            [git, "-c", "core.autocrlf=false", "-C", str(root), *args],
            capture_output=True,
            env=_git_env(index_file),
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WitnessError(f"git {args[0]} could not run ({type(exc).__name__})") from None
    if proc.returncode != 0:
        raise WitnessError(f"git {args[0]} exited {proc.returncode}")
    return proc.stdout


def working_tree_object(root: Path) -> str:
    """Return the tree object id of the working state, via a private index."""
    with tempfile.TemporaryDirectory(prefix="cs1219-") as tmp:
        # An EMPTY private index, never a copy of the real one: a copy carries
        # git's stat cache, and a same-size edit that keeps its mtime is then
        # trusted as unchanged and never re-hashed. Hashing every file is the
        # price of a witness that reads bytes rather than timestamps.
        index = Path(tmp) / "index"
        _git(root, "add", "-A", "--", ".", index_file=index)
        return _git(root, "write-tree", index_file=index).decode().strip()


def population_dirs(root: Path) -> list[str]:
    """Every directory holding a tracked or would-be-tracked file, repo-relative."""
    out = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    dirs = set()
    for name in out.decode("utf-8", "surrogateescape").split("\0"):
        if name:
            dirs.add(name.rsplit("/", 1)[0] if "/" in name else "")
    return sorted(dirs)


def bytecode_digest(root: Path) -> tuple[str, int]:
    """SHA-256 over (path, bytes) of every reachable ``.pyc``, and their count."""
    entries: list[tuple[str, Path]] = []
    for rel in population_dirs(root):
        cache = (root / rel / "__pycache__") if rel else (root / "__pycache__")
        if not cache.is_dir():
            continue
        entries.extend(
            (pyc.relative_to(root).as_posix(), pyc) for pyc in cache.rglob("*.pyc") if pyc.is_file()
        )
    entries.sort()
    digest = hashlib.sha256()
    for rel_name, path in entries:
        data = path.read_bytes()
        encoded = rel_name.encode("utf-8", "surrogateescape")
        digest.update(len(encoded).to_bytes(8, "big") + encoded)
        digest.update(len(data).to_bytes(8, "big") + data)
    return digest.hexdigest(), len(entries)


def freeze(root: Path) -> dict[str, object]:
    """Return the witness record for ``root`` as it stands now."""
    pyc_digest, pyc_count = bytecode_digest(root)
    return {
        "schema": SCHEMA,
        "tree": working_tree_object(root),
        "bytecode": pyc_digest,
        "bytecode_files": pyc_count,
    }


def load_record(path: Path) -> dict[str, object]:
    """Parse a witness record, refusing anything that is not one."""
    try:
        record = json.loads(path.read_bytes().decode("ascii"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise WitnessError("record unreadable or not ASCII JSON") from None
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise WitnessError("record has no recognised schema")
    for key in ("tree", "bytecode"):
        if not isinstance(record.get(key), str):
            raise WitnessError(f"record lacks {key}")
    return record


def compare(recorded: dict[str, object], now: dict[str, object]) -> list[str]:
    """Return one finding per half that moved; empty when nothing did."""
    findings = []
    if recorded["tree"] != now["tree"]:
        findings.append(f"tree moved: {recorded['tree']} -> {now['tree']}")
    if recorded["bytecode"] != now["bytecode"]:
        findings.append(
            "bytecode moved: "
            f"{recorded.get('bytecode_files')} -> {now['bytecode_files']} .pyc files,"
            " digest differs"
        )
    return findings


def _atomic_write(target: Path, data: bytes) -> None:
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_bytes(data)
    for attempt in range(RENAME_ATTEMPTS):
        try:
            tmp.replace(target)
            return
        except PermissionError:
            if attempt == RENAME_ATTEMPTS - 1:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.1 * (attempt + 1))


def main(argv: list[str] | None = None) -> int:
    """Run the CLI; return 0 unmoved, 1 moved, 2 refused."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_freeze = sub.add_parser("freeze", help="record the candidate")
    p_freeze.add_argument("--out", type=Path, default=None)
    p_check = sub.add_parser("check", help="refuse if the candidate moved")
    p_check.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.cmd == "freeze":
            payload = (json.dumps(freeze(root), indent=2, sort_keys=True) + "\n").encode("ascii")
            if args.out is None:
                sys.stdout.write(payload.decode("ascii"))
            else:
                _atomic_write(args.out, payload)
            return 0
        recorded = load_record(args.record)
        findings = compare(recorded, freeze(root))
    except WitnessError as exc:
        print(f"freeze_witness: refused - {exc}", file=sys.stderr)
        return 2
    if findings:
        print("MOVED - a verdict taken over this candidate covers no recorded state")
        for line in findings:
            print(f"  {line}")
        return 1
    print("unmoved - tree and bytecode match the record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
