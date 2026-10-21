#!/usr/bin/env python3
r"""CS-1328 (b) - the census axis for drive-rooted project paths and foreign host names.

THE TRACKED FORM of the out-of-tree v3 measurement the session 146 flip block ran inside
the S7a..S12 window (its counts are in ``docs/LEDGER.md``, the 2026-10-18 CS-1328
record). The measurement is v3's: the same needles, the same three populations, the same
two scopes, v3's five controls and v3's count lines. What changed, so it can be tracked
and run on any tree:

  - no drive letter is written here, and none is guessed: every root is spelled on
    EVERY letter A-Z. The SEED letters - the repo root's own drive, then the system
    drive (where the tree lived before ADR 0026's move), or exactly the ``--drive``
    names, in that order - are always printed, first; any other letter is printed only
    where a root occurs on it. v3 spelled each root on two fixed letters only, so its
    counts miss a root written behind any third letter;
  - two controls are added (drive_coverage and sidecar_categories_live, below), so a
    needle that is derived wrong fails a control instead of quietly counting less;
  - a POSIX absolute root is read as well as a drive-rooted one, so the arms in
    ``tests/test_census_axis.py`` - v3's own self-test, moved into the suite - run on
    any platform;
  - ``--root`` may name the repository being measured itself, so the axis can run on a
    checkout as well as on a clone; a root derived from a clone's origin still may not
    resolve to the clone;
  - git is resolved on PATH by ``tools/toolpath.py``, and every git call carries a
    timeout.

WHAT IS MEASURED. The closure of <T> in <repo>: every commit reachable from <T> (walked
by its own parent lines) and every tree and blob reachable from those commits. Three
populations, counted SEPARATELY, each once for the HEAD tree (the tree of <T>, and the
message of <T> alone) and once for the full closure:
  blobs     the bytes of every distinct blob; a blob opening with a UTF-16 byte-order
            mark is decoded and scanned as text
  paths     every distinct leaf path, as `git ls-tree -r` names them (blobs, symlinks,
            gitlinks), joined with '/'
  messages  the raw message of every commit: the bytes after the header block

NEEDLES - built at run time, never printed; labelled by category only:
  repo_root           this repository's root, from the clone's origin (or --root)
  sidecar_root        the current fleet sidecar root: the nearest ancestor of <repo>
                      holding both SIDECAR_MARKERS, else the one top-level folder of the
                      repo root's drive that holds both (or --sidecars)
  sidecar_hist<i>     the tree's historical sidecar folders, which sat directly under a
                      drive root: the cs- folder alternation of _SIDECAR_NAME in
                      tests/test_readme_audit.py under the repo root, read with ast at run
                      time (never imported, never hardcoded), numbered in its order
  sidecar_bare<i>     the same pattern's bare folder alternatives (a plain folder name,
                      such as the current sidecar root's own name), numbered in its order;
                      one may coincide with sidecar_root, and roots_distinct then says so
  sidecar_wt          the old worktree root: the repo root's own folder name plus
                      WT_SUFFIX, directly under a drive root
  sidecar_walk        the old walk harness folder, directly under a drive root: a fixed
                      historical folder name (WALK_FOLDER), derivable from no live source;
                      it names no person, account, host or home path
  main_root           MAIN's root, the main_root key of config/main_tree.local.json under
                      the repo root - the gitignored local file the tree reads it from
Each root above is counted in two spellings per drive letter <D> of A-Z (a letter off the
seeds is printed only where it counts), each its own needle:
  <root>.<D>          drive spelling  <D>:<sep><c1><sep>...<cn>
  <root>.bash.<D>     Git Bash        <lead><d><sep><c1><sep>...<cn>
  any_drive           every drive-rooted path: a letter, a colon, a separator
  any_bash            every Git Bash drive root: <lead>, a letter, a separator
  host.netbios/.dns/.fqdn  this machine's names from the OS; localhost, IP literals,
                      placeholders and public example names excluded
<sep> is any run of '\' or '/'. <lead> is one to three of them, or one to three
JSON-escaped slashes (one or more '\' then '/'), so /k/x, //k/x and \/k\/x count and
////k/x does not. The left edge of <lead> is the one tests/test_readme_audit.py gives
its own Git Bash branch: its first byte is not preceded by a letter, digit, '.', '~' or
a separator - or it is preceded by a glued single-letter option, a '-' and a letter with
no letter or digit before the '-' - so -C/k/x counts and /mnt/k/x, ./k/x, a/k/x and
a-C/k/x do not. A drive spelling is never preceded by a letter or digit, except behind
such a glued option. Both are ASCII case-insensitive and never followed by a name
character: K:\X, k:/x and the JSON-escaped K:\\X count, K:\X-old and K:X do not. A
drive needle is tried only where any_drive matches and a Git Bash needle only where
any_bash matches, so each is a subset of its family's any_ count. A host needle counts
where it is not touched by a letter, digit or '-'.

THE PATTERN SOURCE IS READ FAIL CLOSED: exit 2 unless _SIDECAR_NAME is bound exactly
once in the whole module (no augmented assignment, no second binding anywhere, no string
that spells the name), by a plain module-level assignment of a string literal, an
f-string or a '+' of them, whose every field is a bare module-level name bound the same
way to one whole regex group. The text must be one (?:...) group whose top-level
alternatives are each read: exactly one cs-(?:a|b) folder alternation, any number of
bare folder names, and the layout alternative cs<sep>+(?:a|b)(?![A-Za-z0-9]) - folders
below a sidecar root, never directly under a drive root, so it adds no needle.

LIVENESS. For each sidecar category its full-closure count is printed, the occurrences
summed over its spellings, once for full.blobs and once over all three populations, with
zero_in_history true when the latter is 0. v3 printed it as a report only; here it is
also the control sidecar_categories_live, because a needle-derivation break (a wrong
old-worktree suffix, a wrong walk folder name) zeroes a category while the summed
sidecar residual stays non-zero.

COVERAGE. Each root is also counted, hidden, by a second construction: ONE needle per
spelling with a letter class in place of the letter. Each per-letter needle counts a
subset of it and no two letters overlap, so the any-letter count less the sum over all
26 per-letter needles is the root's occurrences the per-letter needles missed. The
control drive_coverage needs that to be 0 for every root, so a per-letter needle built
wrong fails it instead of quietly undercounting.

COUNTS, per scope, population and needle: occ (matches), lines (distinct lines holding
one, summed over objects), objs (objects holding one). COUNTS AND BOOLEANS ONLY: no
matched string, path, name, SHA or environment value is printed. Errors print a fixed
phrase or an exception's class name, never its text; git's stderr is discarded.

CONTROLS. Hits never abort. A failed control prints FAIL and exits 1 - UNMEASURED:
  root_residual_nonzero  full.blobs occ of the repo_root drive spellings is non-zero:
                         the accepted history residual (the ORDER's addition 2a)
  sidecar_residual_nonzero  full.blobs occ summed over every sidecar needle is non-zero
  absent_token_zero      a random root (every spelling) and a random host token, scanned
                         in the same pass by the same code, count 0 in all six cells
  matcher_selfcheck      each needle, fed an in-memory buffer built from itself, counts
                         exactly its planted positives and none of its negatives
  walk_complete          this walk's commit, tree and blob sets equal those of
                         `git rev-list --objects <T>` (a second family)
  drive_coverage         every root's any-letter count equals its per-letter sum, over
                         the full closure (see COVERAGE)
  sidecar_categories_live  every sidecar category occurs somewhere in the closure
The first five are v3's, in v3's order; the last two are this file's.
Exit 2 is UNMEASURED too: a usage error, a failed precondition (the tip not a full hex
SHA or not a commit, a shallow clone, a grafts file) or a needle that cannot be derived.

USAGE
  python -B tools/census_axis.py --repo <clone or checkout> --tip <T>
      [--root <repo root>] [--sidecars <dir>] [--drive <letter>]...
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import ctypes
import json
import os
import re
import secrets
import socket
import string
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import IO, Final, NoReturn

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/trailer_census.py does it.
_TOOLS_DIR: Final = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

#: The two folder layouts that mark a directory as the fleet sidecar root.
SIDECAR_MARKERS: Final = (("CS", "Walk"), ("CS", "Scratch", "cs-flip-backup"))
MAIN_CONFIG: Final = ("config", "main_tree.local.json")
MAIN_KEY: Final = "main_root"
SIDECAR_ROOT: Final = "sidecar_root"
SIDECAR_HIST: Final = "sidecar_hist"
SIDECAR_BARE: Final = "sidecar_bare"
SIDECAR_WT: Final = "sidecar_wt"
SIDECAR_WALK: Final = "sidecar_walk"
#: The old worktree root: the repo root's folder name plus this.
WT_SUFFIX: Final = "-wt"
#: The old walk harness folder; no live source names it.
WALK_FOLDER: Final = "cs-walk-131"
#: The file that owns the historical sidecar folder names, and its constant.
HIST_SOURCE: Final = ("tests", "test_readme_audit.py")
HIST_CONST: Final = "_SIDECAR_NAME"
#: Stands for one f-string field, itself one whole regex group.
FIELD: Final = "\0"
HIST_FOLDER: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
#: The top-level alternative shapes the pattern source may hold, besides a bare folder.
HIST_CS_ALT: Final = re.compile(r"cs-\(\?:([a-z0-9\-]+(?:\|[a-z0-9\-]+)*)\)")
HIST_LAYOUT: Final = re.compile(r"cs\0\+\(\?:[a-z]+(?:\|[a-z]+)*\)\(\?!\[A-Za-z0-9\]\)")
BASH: Final = "bash"
#: COMPUTER_NAME_FORMAT values: NetBIOS, DNS host name, fully qualified DNS name.
HOST_KINDS: Final = (("netbios", 0), ("dns", 1), ("fqdn", 3))
HOST_PLACEHOLDERS: Final = frozenset({
    "localhost", "localdomain", "localhost.localdomain", "ip6-localhost", "host",
    "hostname", "computer", "machine", "example", "example.com", "example.net",
    "example.org", "invalid", "test", "local", "workgroup", "desktop", "pc", "server",
    "none", "unknown", "github.com", "noreply",
})  # fmt: skip
PUBLIC_SUFFIXES: Final = (".example.com", ".example.net", ".example.org", ".invalid", ".test")
MIN_HOST_LEN: Final = 3
SCOPES: Final = ("head", "full")
POPULATIONS: Final = ("blobs", "paths", "messages")
ANY_LABEL: Final = "any_drive"
BASH_LABEL: Final = "any_bash"
ABSENT_PREFIX: Final = "absent."
#: The hidden any-letter needles behind the drive_coverage control.
COVER_PREFIX: Final = "cover."
ANY_LETTER: Final = rb"[a-z]"

#: Seconds one git call may take, and one git child may take to exit once closed.
GIT_TIMEOUT_S: Final = 600
PROC_WAIT_S: Final = 30
#: Fields of a `git cat-file --batch` header line: oid, type, size.
HEADER_FIELDS: Final = 3
HEX_PER_BYTE: Final = 2
RAW_OID_LEN: Final = {"sha1": 20, "sha256": 32}
MODE_MASK: Final = 0o170000
MODE_TREE: Final = 0o040000
MODE_GITLINK: Final = 0o160000
MODE_BLOBS: Final = (0o100000, 0o120000)
UTF16_BOMS: Final = (b"\xff\xfe", b"\xfe\xff")

SEP: Final = rb"[\\/]+"
NAME_TAIL: Final = rb"(?![a-z0-9_\-\x80-\xff])"
# A drive: a letter, a colon, a separator; the letter is not preceded by a letter or
# digit, unless a glued single-letter option stands before it ('-' and a letter, no
# letter or digit before the '-'). Written letter-first so the engine can skip to
# candidate bytes; the lookbehinds then judge the bytes before the letter.
ANY_DRIVE: Final = re.compile(
    rb"[a-z]:[\\/](?:(?<![a-z0-9][a-z]:[\\/])"
    rb"|(?<=-[a-z][a-z]:[\\/])(?<![a-z0-9]-[a-z][a-z]:[\\/]))"
)
# Git Bash: a lead, a letter, a separator. The lead is one to three separators, or one
# to three JSON-escaped slashes (one or more backslashes, then a slash). Its first byte
# is not preceded by a letter, digit, '.', '~' or a separator, unless a glued
# single-letter option stands before it. Written separator-first so the engine can skip
# to candidate bytes; the lookbehinds then judge the bytes before it.
ANY_BASH: Final = re.compile(
    rb"[\\/](?:(?<![a-z0-9.~/\\][\\/])"
    rb"|(?<=-[a-z][\\/])(?<![a-z0-9]-[a-z][\\/]))"
    rb"(?:[\\/]{0,2}|(?<=\\)\\*/(?:\\+/){0,2})[a-z][\\/]"
)
BASH_LEAD: Final = rb"(?:[\\/]{1,3}|(?:\\+/){1,3})"
HOST_EDGE: Final = frozenset(b"abcdefghijklmnopqrstuvwxyz0123456789-") | frozenset(
    range(0x80, 0x100)
)
HEX_OID: Final = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
DRIVE_PATH: Final = re.compile(r"([A-Za-z]):[\\/]+(.*)", re.DOTALL)
DRIVE_LEAD: Final = re.compile(r"([A-Za-z]):")
UNC_PREFIXES: Final = ("\\\\?\\", "//?/")

Counts = list[tuple[int, int]]
Table = dict[tuple[str, str], dict[str, tuple[int, int, int]]]
Emit = Callable[[str], None]
Reader = Callable[[str], tuple[str, bytes]]


class UnmeasuredError(Exception):
    """A precondition or derivation failure. ``reason`` is a fixed phrase, never a value."""

    def __init__(self, reason: str) -> None:
        """Keep ``reason``, the fixed phrase the census prints."""
        super().__init__(reason)
        self.reason = reason


def _emit(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# ---------------------------------------------------------------- git plumbing


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def _git_argv(repo: Path, *args: str) -> list[str]:
    git = resolve_tool("git")
    if git is None:
        raise UnmeasuredError("git is not on PATH")
    return [git, "--no-replace-objects", "--no-optional-locks", "-C", str(repo), *args]


def _git(repo: Path, *args: str, stdin: bytes | None = None) -> tuple[int, bytes]:
    argv = _git_argv(repo, *args)
    try:
        proc = subprocess.run(
            argv,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_git_env(),
            check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except OSError:
        raise UnmeasuredError("git could not be started") from None
    except subprocess.TimeoutExpired:
        raise UnmeasuredError("git timed out") from None
    return proc.returncode, proc.stdout


def read_object(stream: IO[bytes], want: str) -> tuple[str, bytes]:
    """One object of a `git cat-file --batch` stream: (type, data).

    Args:
        stream: The batch's stdout.
        want: The object id the caller asked for, so an out-of-order answer is caught.

    Returns:
        The object's type and its bytes.

    Raises:
        UnmeasuredError: When the object is missing, out of order or cut short.
    """
    header = stream.readline()
    parts = header.split()
    if len(parts) != HEADER_FIELDS:
        raise UnmeasuredError("an object of the closure is missing or ambiguous")
    if parts[0].decode("ascii", "replace") != want:
        raise UnmeasuredError("the object reader answered out of order")
    kind = parts[1].decode("ascii", "replace")
    size = int(parts[2])
    data = stream.read(size)
    if len(data) != size or stream.read(1) != b"\n":
        raise UnmeasuredError("the object reader ended early")
    return kind, data


@contextlib.contextmanager
def object_reader(repo: Path) -> Iterator[Reader]:
    """One `git cat-file --batch`, one object per round trip, closed on exit.

    Args:
        repo: The repository to read.

    Yields:
        A function from an object id to (type, data).

    Raises:
        UnmeasuredError: When git cannot be started.
    """
    argv = _git_argv(repo, "cat-file", "--batch")
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_git_env(),
        )
    except OSError:
        raise UnmeasuredError("git could not be started") from None
    feed, out = proc.stdin, proc.stdout
    if feed is None or out is None:
        proc.kill()
        proc.wait(timeout=PROC_WAIT_S)
        raise UnmeasuredError("git could not be started")

    def read(oid: str) -> tuple[str, bytes]:
        feed.write(oid.encode("ascii") + b"\n")
        feed.flush()
        return read_object(out, oid)

    try:
        yield read
    finally:
        with contextlib.suppress(OSError):
            feed.close()
        try:
            proc.wait(timeout=PROC_WAIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=PROC_WAIT_S)


def stream_objects(repo: Path, oids: list[str]) -> Iterator[tuple[str, str, bytes]]:
    """Yield (oid, type, data) for ``oids`` in order, through one buffered batch.

    Args:
        repo: The repository to read.
        oids: The objects, in the order they are wanted.

    Yields:
        One (oid, type, data) per object.

    Raises:
        UnmeasuredError: When git cannot be started or its answer is malformed.
    """
    argv = _git_argv(repo, "cat-file", "--batch", "--buffer")
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_git_env(),
        )
    except OSError:
        raise UnmeasuredError("git could not be started") from None
    feed, out = proc.stdin, proc.stdout
    if feed is None or out is None:
        proc.kill()
        proc.wait(timeout=PROC_WAIT_S)
        raise UnmeasuredError("git could not be started")

    def feed_all() -> None:
        with contextlib.suppress(OSError):
            for oid in oids:
                feed.write(oid.encode("ascii") + b"\n")
            feed.close()

    feeder = threading.Thread(target=feed_all, daemon=True)
    feeder.start()
    finished = False
    try:
        for oid in oids:
            kind, data = read_object(out, oid)
            yield oid, kind, data
        finished = True
    finally:
        with contextlib.suppress(OSError):
            out.close()
        try:
            proc.wait(timeout=PROC_WAIT_S if finished else 0.1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=PROC_WAIT_S)
        feeder.join(timeout=5)


def pack_order(repo: Path, wanted: set[str]) -> list[str]:
    """``wanted`` in the object store's own order, so delta chains resolve cheaply."""
    rc, out = _git(repo, "cat-file", "--batch-check", "--batch-all-objects", "--unordered")
    order: list[str] = []
    seen: set[str] = set()
    if rc == 0:
        for line in out.splitlines():
            oid = line.split(b" ", 1)[0].decode("ascii", "replace")
            if oid in wanted and oid not in seen:
                seen.add(oid)
                order.append(oid)
    order.extend(sorted(wanted - seen))
    return order


def parse_commit(data: bytes) -> tuple[str, list[str], bytes]:
    """A commit object's (tree, parents, message); the message is the bytes after the header.

    Args:
        data: The raw commit object.

    Returns:
        The tree id, the parent ids in order, and the raw message.

    Raises:
        UnmeasuredError: When the object names no tree.
    """
    head, sep, message = data.partition(b"\n\n")
    tree = None
    parents: list[str] = []
    for line in head.split(b"\n"):
        if line.startswith(b"tree ") and tree is None:
            tree = line[5:].decode("ascii", "replace")
        elif line.startswith(b"parent "):
            parents.append(line[7:].decode("ascii", "replace"))
    if tree is None:
        raise UnmeasuredError("a commit object is malformed")
    return tree, parents, message if sep else b""


def _entry_kind(mode: int) -> str:
    kind = {MODE_TREE: "tree", MODE_GITLINK: "gitlink"}.get(mode)
    if kind is None and mode in MODE_BLOBS:
        kind = "blob"
    if kind is None:
        message = "unknown mode"
        raise ValueError(message)
    return kind


def parse_tree(data: bytes, raw_len: int) -> list[tuple[str, bytes, str]]:
    """A tree object's entries as (kind, name, child id).

    Args:
        data: The raw tree object.
        raw_len: The byte length of one raw object id.

    Returns:
        One (kind, name, hex id) per entry; kind is tree, gitlink or blob.

    Raises:
        UnmeasuredError: When the object is malformed.
    """
    entries: list[tuple[str, bytes, str]] = []
    i = 0
    n = len(data)
    try:
        while i < n:
            space = data.index(b" ", i)
            nul = data.index(b"\0", space)
            mode = int(data[i:space], 8) & MODE_MASK
            name = data[space + 1 : nul]
            raw = data[nul + 1 : nul + 1 + raw_len]
            if len(raw) != raw_len:
                message = "short tree entry"
                raise ValueError(message)
            entries.append((_entry_kind(mode), name, raw.hex()))
            i = nul + 1 + raw_len
    except ValueError:
        raise UnmeasuredError("a tree object is malformed") from None
    return entries


class Closure:
    """Every commit, tree, blob and leaf path reachable from the tip, plus the HEAD subset."""

    def __init__(self, read: Reader, tip: str, raw_len: int) -> None:
        """Walk the tip's parent lines, then expand every tree once per path prefix.

        Args:
            read: An object reader.
            tip: The tip commit's full id.
            raw_len: The byte length of one raw object id.

        Raises:
            UnmeasuredError: When a parent is not a commit or an object is malformed.
        """
        self._read = read
        self._raw_len = raw_len
        self._entries: dict[str, list[tuple[str, bytes, str]]] = {}
        self.messages: dict[str, bytes] = {}
        roots: dict[str, str] = {}
        stack = [tip]
        seen = {tip}
        while stack:
            oid = stack.pop()
            kind, data = read(oid)
            if kind != "commit":
                raise UnmeasuredError("the closure holds a parent that is not a commit")
            tree, parents, message = parse_commit(data)
            roots[oid] = tree
            self.messages[oid] = message
            for parent in parents:
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        self.tip = tip
        self.head_trees, self.head_paths, self.head_blobs = self._expand([roots[tip]])
        self.trees, self.paths, self.blobs = self._expand(list(roots.values()))

    def _tree(self, oid: str) -> list[tuple[str, bytes, str]]:
        cached = self._entries.get(oid)
        if cached is None:
            kind, data = self._read(oid)
            if kind != "tree":
                raise UnmeasuredError("a tree entry names an object that is not a tree")
            cached = parse_tree(data, self._raw_len)
            self._entries[oid] = cached
        return cached

    def _expand(self, root_trees: list[str]) -> tuple[set[str], set[bytes], set[str]]:
        trees: set[str] = set()
        paths: set[bytes] = set()
        blobs: set[str] = set()
        visited: set[tuple[bytes, str]] = set()
        stack = [(b"", oid) for oid in root_trees]
        while stack:
            prefix, oid = stack.pop()
            if (prefix, oid) in visited:
                continue
            visited.add((prefix, oid))
            trees.add(oid)
            for kind, name, child in self._tree(oid):
                path = prefix + name
                if kind == "tree":
                    stack.append((path + b"/", child))
                else:
                    paths.add(path)
                    if kind == "blob":
                        blobs.add(child)
        return trees, paths, blobs


def rev_list_family(repo: Path, tip: str) -> dict[str, set[str]]:
    """The second family: `git rev-list --objects <tip>`'s objects, grouped by type.

    Args:
        repo: The repository.
        tip: The tip commit's full id.

    Returns:
        Object ids keyed by type (commit, tree, blob and any other git names).

    Raises:
        UnmeasuredError: When git fails or names a missing object.
    """
    rc, out = _git(repo, "rev-list", "--objects", tip)
    if rc != 0:
        raise UnmeasuredError("git rev-list failed")
    oids = [line.split(b" ", 1)[0] for line in out.splitlines() if line.strip()]
    rc, out = _git(repo, "cat-file", "--batch-check", stdin=b"\n".join(oids) + b"\n")
    if rc != 0:
        raise UnmeasuredError("git cat-file --batch-check failed")
    family: dict[str, set[str]] = {"commit": set(), "tree": set(), "blob": set()}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != HEADER_FIELDS:
            raise UnmeasuredError("git cat-file --batch-check named a missing object")
        family.setdefault(parts[1].decode("ascii", "replace"), set()).add(
            parts[0].decode("ascii", "replace")
        )
    return family


# ---------------------------------------------------------------- needles and the scanner


def split_root(text: str) -> list[str]:
    """The components of a root after its drive, or after a POSIX root's '/'.

    Args:
        text: A drive-rooted path, optionally behind a long-path prefix, or a POSIX
            absolute path.

    Returns:
        The non-empty components, '.' segments dropped.

    Raises:
        UnmeasuredError: When ``text`` is neither, or has no usable component.
    """
    text = text.strip()
    if text.startswith(UNC_PREFIXES):
        text = text[len(UNC_PREFIXES[0]) :]
    match = DRIVE_PATH.fullmatch(text)
    if match is not None:
        rest = match.group(2)
    elif text.startswith("/") and not text.startswith("//"):
        rest = text[1:]
    else:
        raise UnmeasuredError("a root is not a drive-rooted or POSIX absolute path")
    comps = [c for c in re.split(r"[\\/]+", rest) if c and c != "."]
    if not comps or ".." in comps:
        raise UnmeasuredError("a root has no usable components below its drive")
    return comps


def _body(comps: list[str]) -> bytes:
    return SEP.join(re.escape(c.encode("utf-8").lower()) for c in comps)


def root_pattern(drive: str, comps: list[str]) -> re.Pattern[bytes]:
    """The drive spelling of a root on ``drive``; tried only at an ANY_DRIVE match."""
    letter = re.escape(drive.encode("ascii").lower())
    return re.compile(letter + b":" + SEP + _body(comps) + NAME_TAIL)


def bash_pattern(drive: str, comps: list[str]) -> re.Pattern[bytes]:
    """The Git Bash spelling; tried only at an ANY_BASH match, which owns the left edge."""
    letter = re.escape(drive.encode("ascii").lower())
    return re.compile(BASH_LEAD + letter + SEP + _body(comps) + NAME_TAIL)


def cover_pattern(comps: list[str]) -> re.Pattern[bytes]:
    """The drive spelling of a root behind ANY letter; a superset of every root_pattern."""
    return re.compile(ANY_LETTER + b":" + SEP + _body(comps) + NAME_TAIL)


def cover_bash_pattern(comps: list[str]) -> re.Pattern[bytes]:
    """The Git Bash spelling of a root behind ANY letter; a superset of every bash_pattern."""
    return re.compile(BASH_LEAD + ANY_LETTER + SEP + _body(comps) + NAME_TAIL)


def spell(drive: bytes, comps: list[bytes], sep: bytes) -> bytes:
    """A drive spelling: ``drive``, a colon, then ``comps`` joined by ``sep``."""
    return drive + b":" + sep + sep.join(comps)


def bash_spell(drive: bytes, comps: list[bytes], sep: bytes, lead: bytes = b"/") -> bytes:
    """A Git Bash spelling: ``lead``, the lower-case ``drive``, then ``comps``."""
    return lead + drive.lower() + sep + sep.join(comps)


def _count_anchored(
    low: bytes, anchor: re.Pattern[bytes], pats: list[re.Pattern[bytes]]
) -> tuple[Counts, tuple[int, int]]:
    """(occ, lines) per needle and for the anchor itself, each needle tried at each anchor."""
    n = len(pats)
    r_occ = [0] * n
    r_lines = [0] * n
    r_last = [-2] * n
    a_occ = a_lines = 0
    a_last = -2
    prev = 0
    line = -1
    for match in anchor.finditer(low):
        pos = match.start()
        nl = low.rfind(b"\n", prev, pos)
        if nl != -1:
            line = nl
        prev = pos
        a_occ += 1
        if line != a_last:
            a_lines += 1
            a_last = line
        for k, pat in enumerate(pats):
            if pat.match(low, pos) is not None:
                r_occ[k] += 1
                if r_last[k] != line:
                    r_lines[k] += 1
                    r_last[k] = line
    return list(zip(r_occ, r_lines, strict=True)), (a_occ, a_lines)


def _count_host(low: bytes, needle: bytes) -> tuple[int, int]:
    """(occ, lines) of ``needle`` where no letter, digit or '-' touches it."""
    occ = lines = 0
    last = -2
    prev = 0
    line = -1
    width = len(needle)
    size = len(low)
    i = low.find(needle)
    while i != -1:
        j = i + width
        if (i == 0 or low[i - 1] not in HOST_EDGE) and (j >= size or low[j] not in HOST_EDGE):
            nl = low.rfind(b"\n", prev, i)
            if nl != -1:
                line = nl
            prev = i
            occ += 1
            if line != last:
                lines += 1
                last = line
        i = low.find(needle, i + 1)
    return occ, lines


class Scanner:
    """Counts every needle in one buffer: [(occ, lines)] in ``labels`` order.

    ``labels`` is: the drive needles, the Git Bash needles, any_drive, any_bash, the hosts.
    """

    def __init__(
        self,
        drive_roots: list[tuple[str, re.Pattern[bytes]]],
        bash_roots: list[tuple[str, re.Pattern[bytes]]],
        hosts: list[tuple[str, bytes]],
    ) -> None:
        """Keep each family's needles under its anchor, and the label order.

        Args:
            drive_roots: (label, drive-spelling pattern) per root and drive.
            bash_roots: (label, Git Bash pattern) per root and drive.
            hosts: (label, lower-case host name) per host needle.
        """
        self._families = (
            (ANY_DRIVE, [pat for _, pat in drive_roots]),
            (ANY_BASH, [pat for _, pat in bash_roots]),
        )
        self._hosts = [needle for _, needle in hosts]
        self.labels = [
            *(label for label, _ in drive_roots),
            *(label for label, _ in bash_roots),
            ANY_LABEL,
            BASH_LABEL,
            *(label for label, _ in hosts),
        ]

    def scan(self, data: bytes) -> Counts:
        """Count every needle in ``data``, ASCII case-insensitively.

        Args:
            data: One buffer: a blob, a path or a message.

        Returns:
            One (occ, lines) per label, in ``labels`` order.
        """
        low = data.lower()
        out: Counts = []
        anchors: Counts = []
        for anchor, pats in self._families:
            counts, total = _count_anchored(low, anchor, pats)
            out.extend(counts)
            anchors.append(total)
        out.extend(anchors)
        out.extend(_count_host(low, needle) for needle in self._hosts)
        return out


def build_scanner(
    root_comps: dict[str, list[str]],
    hosts: dict[str, str],
    absent_comps: list[str],
    absent_host: str,
    drives: list[str],
) -> Scanner:
    """The census scanner: every root on every drive in both spellings, then the hosts.

    Args:
        root_comps: Each root's components, keyed by its category label.
        hosts: Each host name, keyed by its kind.
        absent_comps: The absent control's root.
        absent_host: The absent control's host.
        drives: The drive letters, in label order.

    Returns:
        The scanner; the absent needles carry ``ABSENT_PREFIX``, and each root's hidden
        any-letter needles, after every derived one, carry ``COVER_PREFIX``.
    """
    drive_roots = []
    bash_roots = []
    for name, comps in [*root_comps.items(), (f"{ABSENT_PREFIX}root", absent_comps)]:
        for drive in drives:
            drive_roots.append((f"{name}.{drive}", root_pattern(drive, comps)))
            bash_roots.append((f"{name}.{BASH}.{drive}", bash_pattern(drive, comps)))
    for name, comps in root_comps.items():
        drive_roots.append((f"{COVER_PREFIX}{name}", cover_pattern(comps)))
        bash_roots.append((f"{COVER_PREFIX}{name}.{BASH}", cover_bash_pattern(comps)))
    host_list = [(f"host.{label}", name.lower().encode("ascii")) for label, name in hosts.items()]
    host_list.append((f"{ABSENT_PREFIX}host", absent_host.lower().encode("ascii")))
    return Scanner(drive_roots, bash_roots, host_list)


def _counts_exactly(
    scanner: Scanner, index: int, positives: list[bytes], negatives: list[bytes]
) -> bool:
    """Label ``index`` counts each positive line once and no negative line at all."""
    want = (len(positives), len(positives))
    return scanner.scan(b"\n".join(positives))[index] == want and scanner.scan(
        b"\n".join(negatives)
    )[index] == (0, 0)


def _drive_cases(d: bytes, cb: list[bytes]) -> tuple[list[bytes], list[bytes]]:
    positives = [
        spell(d, cb, b"\\") + b"\\x",
        spell(d.lower(), cb, b"/"),
        b'"' + spell(d, cb, b"\\\\") + b'"',
        spell(d, cb, b"\\").upper(),
        b"(" + spell(d, cb, b"/") + b"/)",
        b"-I" + spell(d, cb, b"\\"),  # behind a glued option
        b"cc -i" + spell(d.lower(), cb, b"/") + b"/x",
    ]
    negatives = [
        spell(d, cb, b"\\") + b"x",
        spell(d, cb, b"\\") + b"-",
        b"x" + spell(d, cb, b"\\"),
        b"9" + spell(d, cb, b"/"),
        d + b":" + b"\\".join(cb),
        bash_spell(d, cb, b"/"),  # the Git Bash spelling is not a drive spelling
        b"x-I" + spell(d, cb, b"\\"),  # the glued option's '-' has a left edge
        b"9-I" + spell(d, cb, b"/"),
    ]
    return positives, negatives


def _bash_cases(d: bytes, cb: list[bytes]) -> tuple[list[bytes], list[bytes]]:
    positives = [
        bash_spell(d, cb, b"/") + b"/x",
        bash_spell(d, cb, b"/", lead=b"//"),
        b'"' + bash_spell(d, cb, b"\\/", lead=b"\\/") + b'"',
        bash_spell(d, cb, b"/").upper(),
        b"(" + bash_spell(d, cb, b"/") + b"/)",
        b"PATH=/x/y:" + bash_spell(d, cb, b"/") + b"/bin",
        b"-C" + bash_spell(d, cb, b"/"),  # behind a glued option
        b"git -I" + bash_spell(d, cb, b"/", lead=b"//") + b"/x",
        b'"' + bash_spell(d, cb, b"\\/", lead=b"\\/\\/") + b'"',  # JSON-escaped //
        bash_spell(d, cb, b"\\/", lead=b"\\/\\/\\/"),
        bash_spell(d, cb, b"\\\\/", lead=b"\\\\/\\\\/"),  # and its backslash doubled
        b"-C" + bash_spell(d, cb, b"\\/", lead=b"\\/\\/"),
    ]
    negatives = [
        bash_spell(d, cb, b"/") + b"x",
        bash_spell(d, cb, b"/") + b"-",
        b"x" + bash_spell(d, cb, b"/"),
        b"9" + bash_spell(d, cb, b"/"),
        b"/mnt" + bash_spell(d, cb, b"/"),
        b"." + bash_spell(d, cb, b"/"),
        b"~" + bash_spell(d, cb, b"/"),
        bash_spell(d, cb, b"/", lead=b"////"),
        b"/" + d.lower() + b"/".join(cb),
        spell(d, cb, b"/"),  # the drive spelling is not a Git Bash spelling
        b"x-C" + bash_spell(d, cb, b"/"),  # the glued option's '-' has a left edge
        b"9-I" + bash_spell(d, cb, b"/"),
        bash_spell(d, cb, b"\\/", lead=b"\\/\\/\\/\\/"),  # four JSON-escaped slashes
        b"x" + bash_spell(d, cb, b"\\/", lead=b"\\/\\/"),
    ]
    return positives, negatives


def _anchor_cases() -> tuple[list[bytes], list[bytes], list[bytes], list[bytes]]:
    """The any_drive and any_bash positives and negatives, built from neutral letters."""
    k, m, z, q = b"k", b"m", b"z", b"q"
    drive_pos = [
        spell(k.upper(), [b"a"], b"\\"), spell(k, [b"b"], b"/"),
        b'"' + spell(m.upper(), [b"c"], b"\\\\") + b'"', b" " + spell(z, [b"d"], b"/"),
        b"(" + spell(q.upper(), [b"e"], b"\\") + b")", b"-I" + spell(m.upper(), [b"x"], b"\\"),
        b"cc -i" + spell(k, [b"y"], b"/"), b"-" + b"-" + spell(m.upper(), [b"z"], b"/"),
    ]  # fmt: skip
    drive_neg = [
        b"https://x", b"x" + spell(k.upper(), [b"a"], b"\\"), k.upper() + b":a",
        b"1" + spell(m.upper(), [b"x"], b"/"), k.upper() + b":",
        b"a-I" + spell(m.upper(), [b"x"], b"\\"), b"1-I" + spell(m.upper(), [b"x"], b"\\"),
    ]  # fmt: skip
    bash_pos = [
        bash_spell(k, [b"a"], b"/"), bash_spell(m, [b"b"], b"/", lead=b"//"),
        b'"' + bash_spell(z, [b"w"], b"\\/", lead=b"\\/") + b'"',
        b" " + bash_spell(q, [b"r"], b"/"),
        b"(" + bash_spell(b"x", [b"y"], b"/") + b")", b"-C" + bash_spell(k, [b"x"], b"/"),
        b"git -I" + bash_spell(m, [b"y"], b"/"),
        b'"' + bash_spell(k, [b"x"], b"\\/", lead=b"\\/\\/") + b'"',
        bash_spell(k, [b"x"], b"\\/", lead=b"\\/\\/\\/"),
        bash_spell(k, [b"x"], b"\\\\/", lead=b"\\\\/\\\\/"),
        b"-C" + bash_spell(k, [b"x"], b"\\/", lead=b"\\/\\/"),
    ]  # fmt: skip
    bash_neg = [
        b"a/b/c", b"/mnt" + bash_spell(m, [b"x"], b"/"), b"x" + bash_spell(k, [b"y"], b"/"),
        bash_spell(k, [b"x"], b"/", lead=b"////"), b"/ab/c", b"." + bash_spell(k, [b"x"], b"/"),
        b"~" + bash_spell(k, [b"x"], b"/"), b"https://example.com" + bash_spell(k, [b"x"], b"/"),
        spell(k.upper(), [b"a"], b"\\"), b"a-C" + bash_spell(k, [b"x"], b"/"),
        b"9-I" + bash_spell(m, [b"y"], b"/"),
        b'"' + bash_spell(k, [b"x"], b"\\/", lead=b"\\/\\/\\/\\/") + b'"',
        b"x" + bash_spell(k, [b"x"], b"\\/", lead=b"\\/\\/"), b"-CI" + bash_spell(k, [b"x"], b"/"),
    ]  # fmt: skip
    return drive_pos, drive_neg, bash_pos, bash_neg


def _host_cases(h: bytes) -> tuple[list[bytes], list[bytes]]:
    positives = [h, b" " + h.upper() + b".", b"(" + h.lower() + b")", b"/" + h + b"/",
                 b"@" + h + b"_"]  # fmt: skip
    negatives = [b"x" + h, h + b"x", h + b"-y", b"-" + h, b"9" + h + b"9"]
    return positives, negatives


def matcher_selfcheck(
    root_comps: dict[str, list[str]], hosts: dict[str, str], drives: list[str]
) -> bool:
    """Each needle counts its own planted positives exactly and none of its negatives.

    Args:
        root_comps: Each root's components, keyed by its category label.
        hosts: Each host name, keyed by its kind.
        drives: The drive letters.

    Returns:
        True when every needle - derived and any-letter - both anchors and every host
        needle pass.
    """
    checks = [ok for name, comps in root_comps.items() for ok in _root_checks(name, comps, drives)]
    anchors = Scanner([], [], [])
    drive_pos, drive_neg, bash_pos, bash_neg = _anchor_cases()
    checks.append(_counts_exactly(anchors, 0, drive_pos, drive_neg))
    checks.append(_counts_exactly(anchors, 1, bash_pos, bash_neg))
    for label, host in hosts.items():
        h = host.encode("ascii")
        positives, negatives = _host_cases(h)
        checks.append(
            _counts_exactly(Scanner([], [], [(label, h.lower())]), 2, positives, negatives)
        )
    return all(checks)


def _probe_letter(drives: list[str]) -> bytes | None:
    """A letter outside ``drives``, so the any-letter needles are tried off the derived set.

    None when ``drives`` holds every letter.
    """
    outside = [c for c in "QJXZABCDEFGHIKLMNOPRSTUVWY" if c not in drives]
    return outside[0].encode("ascii") if outside else None


def _root_checks(name: str, comps: list[str], drives: list[str]) -> Iterator[bool]:
    """One root's checks.

    Each derived needle counts its own letter and no other; the root's any-letter
    needles count every derived letter and one letter outside the set.
    """
    cb = [c.encode("utf-8") for c in comps]
    probe = _probe_letter(drives)
    probe_drive = _drive_cases(probe, cb)[0] if probe is not None else []
    probe_bash = _bash_cases(probe, cb)[0] if probe is not None else []
    cover_d = Scanner([(name, cover_pattern(comps))], [], [])
    cover_b = Scanner([], [(name, cover_bash_pattern(comps))], [])
    letters = [d.encode("ascii") for d in drives]
    for letter in [*letters, *([probe] if probe is not None else [])]:
        d_pos, d_neg = _drive_cases(letter, cb)
        b_pos, b_neg = _bash_cases(letter, cb)
        yield _counts_exactly(cover_d, 0, d_pos, d_neg)
        yield _counts_exactly(cover_b, 0, b_pos, b_neg)
        if letter not in letters:
            continue
        drive = letter.decode("ascii")
        yield _counts_exactly(
            Scanner([(name, root_pattern(drive, comps))], [], []), 0, d_pos, d_neg + probe_drive
        )
        yield _counts_exactly(
            Scanner([], [(name, bash_pattern(drive, comps))], []), 0, b_pos, b_neg + probe_bash
        )


def text_of(data: bytes) -> tuple[bytes, bool]:
    """A blob's text to scan, and whether it was decoded from UTF-16.

    Args:
        data: The blob's bytes.

    Returns:
        The bytes to scan (UTF-8 when a UTF-16 byte-order mark opened the blob and it
        decoded) and True for a decoded blob.
    """
    if data[:2] in UTF16_BOMS:
        try:
            return data.decode("utf-16").encode("utf-8"), True
        except UnicodeError:
            return data, False
    return data, False


class Cell:
    """One (scope, population) cell's running totals, per label."""

    def __init__(self, width: int) -> None:
        """Start every total at zero for ``width`` labels."""
        self.objects = 0
        self.occ = [0] * width
        self.lines = [0] * width
        self.objs = [0] * width

    def add(self, result: Counts) -> None:
        """Add one object's scan result."""
        self.objects += 1
        for k, (occ, lines) in enumerate(result):
            if occ:
                self.occ[k] += occ
                self.lines[k] += lines
                self.objs[k] += 1


# ---------------------------------------------------------------- derivations


def _computer_name(kind: int) -> str:
    """One Windows computer name format, or "" when the call fails."""
    func = ctypes.windll.kernel32.GetComputerNameExW
    func.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    func.restype = ctypes.c_int
    size = ctypes.c_ulong(0)
    func(kind, None, ctypes.byref(size))
    if size.value == 0:
        return ""
    buf = ctypes.create_unicode_buffer(size.value + 1)
    size = ctypes.c_ulong(size.value + 1)
    if not func(kind, buf, ctypes.byref(size)):
        return ""
    return buf.value


def host_usable(name: str) -> bool:
    """Whether ``name`` is a real host name, not localhost, an IP or a placeholder."""
    n = name.strip().lower().rstrip(".")
    if len(n) < MIN_HOST_LEN or n in HOST_PLACEHOLDERS or n.startswith("localhost"):
        return False
    if ":" in n or re.fullmatch(r"[0-9.]+", n):
        return False
    if n.endswith(PUBLIC_SUFFIXES):
        return False
    return re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", n) is not None


def derive_hosts() -> tuple[dict[str, str], int]:
    """This machine's usable host names by kind, and how many were excluded.

    Returns:
        The usable names keyed by netbios, dns and fqdn, and the excluded count.
    """
    raw: dict[str, str] = {}
    if sys.platform == "win32":
        for label, kind in HOST_KINDS:
            try:
                raw[label] = _computer_name(kind)
            except (OSError, AttributeError, ValueError):
                raw[label] = ""
    if not raw.get("dns"):
        with contextlib.suppress(OSError):
            raw["dns"] = socket.gethostname().split(".")[0]
    if not raw.get("fqdn"):
        with contextlib.suppress(OSError):
            raw["fqdn"] = socket.gethostname()
    hosts = {label: value.strip().rstrip(".") for label, value in raw.items() if host_usable(value)}
    return hosts, len(raw) - len(hosts)


def same_path(a: Path, b: Path) -> bool:
    """Whether two paths name the same place, case-folded where the platform folds."""
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))  # noqa: PTH100


def _absolute(text: str) -> Path:
    return Path(os.path.abspath(text))  # noqa: PTH100 - normalised, never resolved


def _origin_root(clone: Path) -> Path:
    rc, out = _git(clone, "config", "--get", "remote.origin.url")
    if rc != 0 or not out.strip():
        raise UnmeasuredError("repo root not derivable: the clone has no origin URL; pass --root")
    try:
        url = out.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise UnmeasuredError("repo root not derivable: origin URL not UTF-8") from None
    if url.startswith("file://"):
        url = url[len("file://") :]
        if re.match(r"/[A-Za-z]:", url):
            url = url[1:]
    local = DRIVE_PATH.fullmatch(url) is not None or (
        url.startswith("/") and not url.startswith("//")
    )
    if "://" in url or not local:
        raise UnmeasuredError("repo root not derivable: origin is not a local path")
    root = Path(url)
    return root.parent if root.name == ".git" else root


def derive_repo_root(clone: Path, override: str | None) -> tuple[Path, str]:
    """This repository's root: ``override``, else the clone's local origin.

    Args:
        clone: The repository being measured.
        override: The ``--root`` value, which may name ``clone`` itself.

    Returns:
        The root and its source, "arg" or "origin".

    Raises:
        UnmeasuredError: When no root is derivable, the root holds no git dir or local
            main-tree config, or an origin-derived root is the clone itself.
    """
    if override:
        root, source = _absolute(override), "arg"
    else:
        root, source = _origin_root(clone), "origin"
    if not (root / ".git").exists() or not root.joinpath(*MAIN_CONFIG).is_file():
        raise UnmeasuredError("repo root not derivable: no git dir or no local main-tree config")
    if source == "origin" and same_path(root, clone):
        raise UnmeasuredError("repo root resolves to the clone itself")
    return root, source


def _is_sidecar_root(path: Path) -> bool:
    try:
        return all(path.joinpath(*marker).is_dir() for marker in SIDECAR_MARKERS)
    except OSError:
        return False


def derive_sidecar_root(clone: Path, repo_root: Path, override: str | None) -> tuple[Path, str]:
    """The fleet sidecar root: ``override``, an ancestor of the clone, or a drive scan.

    Args:
        clone: The repository being measured.
        repo_root: This repository's root, whose drive the scan reads.
        override: The ``--sidecars`` value.

    Returns:
        The sidecar root and its source, "arg", "ancestor" or "drive-scan".

    Raises:
        UnmeasuredError: When the override lacks the markers, or none or several
            candidates are found.
    """
    if override:
        root = _absolute(override)
        if not _is_sidecar_root(root):
            raise UnmeasuredError("--sidecars does not hold the sidecar markers")
        return root, "arg"
    anchor = _absolute(str(clone))
    for candidate in (anchor, *anchor.parents):
        if _is_sidecar_root(candidate):
            return candidate, "ancestor"
    try:
        drive_root = Path(repo_root.anchor)
        found = [d for d in drive_root.iterdir() if d.is_dir() and _is_sidecar_root(d)]
    except OSError:
        found = []
    if len(found) == 1:
        return found[0], "drive-scan"
    raise UnmeasuredError("sidecar root not derivable (none or several); pass --sidecars")


def derive_main_root(repo_root: Path) -> list[str]:
    """MAIN's root components, from the repo root's gitignored local main-tree config.

    Args:
        repo_root: This repository's root.

    Returns:
        The components of MAIN's root.

    Raises:
        UnmeasuredError: When the config is unreadable or names no root.
    """
    try:
        data = json.loads(repo_root.joinpath(*MAIN_CONFIG).read_bytes().decode("utf-8"))
    except (OSError, ValueError, RecursionError):
        raise UnmeasuredError("main root not derivable: the local config is unreadable") from None
    value = data.get(MAIN_KEY) if isinstance(data, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise UnmeasuredError("main root not derivable: the local config names no root")
    return split_root(value)


_HIST_FAIL: Final = "historical sidecar folders not derivable: "


def _hist_refuse(why: str) -> UnmeasuredError:
    return UnmeasuredError(_HIST_FAIL + why)


_TYPE_PARAMS: Final = tuple(
    getattr(ast, k) for k in ("TypeVar", "ParamSpec", "TypeVarTuple") if hasattr(ast, k)
)
_NAMED_DEFS: Final = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.MatchAs, ast.MatchStar,
    *_TYPE_PARAMS,
)  # fmt: skip


def _binds(node: ast.AST, name: str) -> bool:
    """Whether ``node`` binds, rebinds or deletes ``name``."""
    if isinstance(node, ast.Name):
        hit = node.id == name and not isinstance(node.ctx, ast.Load)
    elif isinstance(node, _NAMED_DEFS):
        hit = getattr(node, "name", None) == name
    elif isinstance(node, ast.ExceptHandler):
        hit = node.name == name
    elif isinstance(node, ast.alias):  # a star import may bind any name
        hit = node.name == "*" or (node.asname or node.name.split(".")[0]) == name
    elif isinstance(node, (ast.Global, ast.Nonlocal)):
        hit = name in node.names
    elif isinstance(node, ast.arg):
        hit = node.arg == name
    elif isinstance(node, ast.MatchMapping):
        hit = node.rest == name
    else:
        hit = False
    return hit


def _binding_sites(tree: ast.Module, name: str) -> list[ast.AST]:
    """Every node anywhere in ``tree`` that binds, rebinds or deletes ``name``."""
    return [node for node in ast.walk(tree) if _binds(node, name)]


def _regex_scan(text: str) -> tuple[list[str], int] | None:
    """(top-level alternatives, index where depth first returns to 0) or None if unbalanced.

    Escapes and character classes are skipped; the index is -1 if depth never closes.
    """
    parts: list[str] = []
    depth = 0
    start = 0
    first_close = -1
    i = 0
    n = len(text)
    in_class = False
    while i < n:
        c = text[i]
        if c == "\\":
            if i + 1 >= n:
                return None
            i += 2
            continue
        if in_class:
            in_class = c != "]"
        elif c == "[":
            in_class = True
            j = i + 1
            if j < n and text[j] == "^":
                j += 1
            if j < n and text[j] == "]":  # a ']' first in a class is literal
                i = j
        elif c in "()":
            depth += 1 if c == "(" else -1
            if depth < 0:
                return None
            if depth == 0 and c == ")" and first_close == -1:
                first_close = i
        elif c == "|" and depth == 0:
            parts.append(text[start:i])
            start = i + 1
        i += 1
    if depth or in_class:
        return None
    parts.append(text[start:])
    return parts, first_close


def _one_group(text: str) -> bool:
    """``text`` is one whole regex group: it opens at 0 and first closes at its end."""
    scanned = _regex_scan(text)
    return scanned is not None and text.startswith("(") and scanned[1] == len(text) - 1


def _module_literal(tree: ast.Module, name: str, seen: tuple[str, ...], role: str) -> str:
    """The text ``name`` is bound to, read fail closed; FIELD stands for each field."""
    if name in seen:
        raise _hist_refuse("the pattern reads a name in a cycle")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            raise _hist_refuse(f"{role} is augmented")
    sites = _binding_sites(tree, name)
    if not sites:
        raise _hist_refuse(f"{role} is not bound")
    if len(sites) != 1:
        raise _hist_refuse(f"{role} is bound more than once")
    value = None
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target: ast.AST = stmt.targets[0]
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            target = stmt.target
        else:
            continue
        if target is sites[0]:
            value = stmt.value
    if value is None:
        raise _hist_refuse(f"{role} is not bound by a plain module-level assignment")
    return _pattern_text(tree, value, (*seen, name))


def _pattern_text(tree: ast.Module, node: ast.AST, seen: tuple[str, ...]) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _pattern_text(tree, node.left, seen) + _pattern_text(tree, node.right, seen)
    if isinstance(node, ast.JoinedStr):
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            elif (
                isinstance(part, ast.FormattedValue)
                and part.conversion == -1
                and part.format_spec is None
                and isinstance(part.value, ast.Name)
            ):
                field = _module_literal(tree, part.value.id, seen, "a name the pattern reads")
                if not _one_group(field):
                    raise _hist_refuse("a name the pattern reads is not one whole regex group")
                parts.append(FIELD)
            else:
                raise _hist_refuse("the pattern holds a field this script does not read")
        return "".join(parts)
    raise _hist_refuse("the pattern is not a literal this script reads")


def _read_pattern_source(repo_root: Path) -> ast.Module:
    try:
        return ast.parse(repo_root.joinpath(*HIST_SOURCE).read_bytes(), filename="<source>")
    except (OSError, SyntaxError, ValueError, RecursionError, MemoryError):
        raise _hist_refuse("the test pattern source is unreadable") from None


def derive_hist_sidecars(repo_root: Path) -> tuple[list[list[str]], list[list[str]], int]:
    """(cs- folders, bare folders, layout alternatives) of the tree's sidecar pattern.

    Read from the tree's own sidecar guard, the module-level ``_SIDECAR_NAME`` of
    ``tests/test_readme_audit.py``, FAIL CLOSED: any binding, field or alternative shape
    this function does not fully read raises UnmeasuredError (exit 2). The file is
    parsed, never imported; nothing here names a folder.

    Args:
        repo_root: The root whose pattern source is read.

    Returns:
        Each cs- folder and each bare folder as a one-component root, and the number of
        layout alternatives.

    Raises:
        UnmeasuredError: On any source this function does not fully read.
    """
    tree = _read_pattern_source(repo_root)
    for node in ast.walk(tree):
        value = node.value if isinstance(node, ast.Constant) else None
        if isinstance(value, str) and HIST_CONST in value:
            raise _hist_refuse("a string spells the pattern's name")
    text = _module_literal(tree, HIST_CONST, (), "the pattern")
    scanned = _regex_scan(text[3:-1]) if text.startswith("(?:") and _one_group(text) else None
    if scanned is None:
        raise _hist_refuse("the pattern is not one (?:...) group")
    cs_groups: list[list[str]] = []
    bare: list[str] = []
    layout = 0
    for alt in scanned[0]:
        match = HIST_CS_ALT.fullmatch(alt)
        if match is not None:
            cs_groups.append(match.group(1).split("|"))
        elif HIST_FOLDER.fullmatch(alt) is not None:
            bare.append(alt)
        elif HIST_LAYOUT.fullmatch(alt) is not None:
            layout += 1
        else:
            raise _hist_refuse("an alternative has a shape this script does not read")
    if len(cs_groups) != 1:
        raise _hist_refuse("the pattern holds no single cs- folder alternation")
    names = [f"cs-{name}" for name in cs_groups[0]]
    if any(HIST_FOLDER.fullmatch(n) is None for n in names):
        raise _hist_refuse("an alternative is not a plain folder name")
    if len(set(names + bare)) != len(names) + len(bare):
        raise _hist_refuse("a folder name is repeated")
    return [[n] for n in names], [[b] for b in bare], layout


def derive_wt_root(repo_root: Path) -> list[str]:
    """The old worktree root: the repo root's own folder name plus WT_SUFFIX.

    Args:
        repo_root: This repository's root.

    Returns:
        The one-component root.

    Raises:
        UnmeasuredError: When the repo root has no folder name.
    """
    name = split_root(str(repo_root))[-1]
    if not name.strip(" ."):
        raise UnmeasuredError("old worktree root not derivable: the repo root has no folder name")
    return [name + WT_SUFFIX]


def _letter(text: str) -> str | None:
    """The drive letter ``text`` opens with, upper case, or None."""
    text = text.strip()
    if text.startswith(UNC_PREFIXES):
        text = text[len(UNC_PREFIXES[0]) :]
    match = DRIVE_LEAD.match(text)
    return match.group(1).upper() if match is not None else None


def derive_drives(
    repo_root: str, overrides: list[str] | None, system_drive: str | None
) -> tuple[list[str], str]:
    """The seed drive letters, always printed and first in label order, never repeated.

    Args:
        repo_root: This repository's root, whose own drive comes first.
        overrides: The ``--drive`` values; when given, exactly these, in their order.
        system_drive: The system drive (the ``SystemDrive`` value), which comes second.

    Returns:
        The upper-case letters and their source, "arg" or "derived".

    Raises:
        UnmeasuredError: When an override is not one drive letter, or no letter derives.
    """
    letters: list[str] = []
    if overrides:
        for value in overrides:
            v = value.strip().removesuffix(":")
            if len(v) != 1 or not v.isascii() or not v.isalpha():
                raise UnmeasuredError("--drive takes one drive letter")
            if v.upper() not in letters:
                letters.append(v.upper())
        return letters, "arg"
    for text in (repo_root, system_drive or ""):
        letter = _letter(text)
        if letter is not None and letter not in letters:
            letters.append(letter)
    if not letters:
        raise UnmeasuredError("no drive letter derivable; pass --drive")
    return letters, "derived"


# ---------------------------------------------------------------- the census


def _flag(value: bool) -> str:
    return str(value).lower()


def _grafted(repo: Path) -> bool:
    rc, out = _git(repo, "rev-parse", "--git-path", "info/grafts")
    if rc != 0:
        return True
    grafts_path = Path(out.decode("utf-8", "replace").strip())
    if not grafts_path.is_absolute():
        grafts_path = repo / grafts_path
    return grafts_path.exists()


def preconditions(repo: Path, tip: str, emit: Emit) -> int:
    """Validate the clone and the tip; return the raw object-id length.

    Args:
        repo: The repository being measured.
        tip: The tip, a full lower-case hex object id.
        emit: Where each precondition line goes.

    Returns:
        The byte length of one raw object id in the repository's format.

    Raises:
        UnmeasuredError: On a tip that is not a full hex commit id of the repository's
            format, a shallow repository or a grafts file.
    """
    full_hex = HEX_OID.fullmatch(tip) is not None
    emit(f"precondition tip_full_hex {_flag(full_hex)}")
    if not full_hex:
        raise UnmeasuredError("the tip is not a full lower-case hex object id")
    rc, out = _git(repo, "rev-parse", "--show-object-format")
    fmt = out.decode("ascii", "replace").strip() if rc == 0 else ""
    raw_len = RAW_OID_LEN.get(fmt, 0)
    if raw_len * HEX_PER_BYTE != len(tip):
        raise UnmeasuredError("the tip length does not match the clone's object format")
    rc, out = _git(repo, "rev-parse", "--verify", "--quiet", "--end-of-options", tip + "^{commit}")
    is_commit = rc == 0 and out.decode("ascii", "replace").strip() == tip
    emit(f"precondition tip_is_commit {_flag(is_commit)}")
    if not is_commit:
        raise UnmeasuredError("the tip is not a commit in the clone")
    rc, out = _git(repo, "rev-parse", "--is-shallow-repository")
    shallow = rc != 0 or out.strip() != b"false"
    emit(f"precondition shallow {_flag(shallow)}")
    if shallow:
        raise UnmeasuredError("the clone is shallow or its depth is unreadable")
    grafts = _grafted(repo)
    emit(f"precondition grafts {_flag(grafts)}")
    if grafts:
        raise UnmeasuredError("the clone carries a grafts file or its git dir is unreadable")
    rc, out = _git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/main")
    emit(f"info tip_is_clone_main {_flag(rc == 0 and out.strip() == tip.encode())}")
    return raw_len


def root_set(
    repo: list[str],
    sidecar: list[str],
    hist: list[list[str]],
    bare: list[list[str]],
    wt: list[str],
    walk: list[str],
    main: list[str],
) -> dict[str, list[str]]:
    """Every root needle's components, keyed by its category label."""
    roots = {"repo_root": repo, SIDECAR_ROOT: sidecar}
    roots.update({f"{SIDECAR_HIST}{i}": comps for i, comps in enumerate(hist, 1)})
    roots.update({f"{SIDECAR_BARE}{i}": comps for i, comps in enumerate(bare, 1)})
    roots[SIDECAR_WT] = wt
    roots[SIDECAR_WALK] = walk
    roots["main_root"] = main
    return roots


def sidecar_category(label: str) -> str | None:
    """The sidecar category a needle label belongs to, or None for any other label."""
    name = label.split(".", 1)[0]
    if name in (SIDECAR_ROOT, SIDECAR_WT, SIDECAR_WALK):
        return name
    for prefix in (SIDECAR_HIST, SIDECAR_BARE):
        if name.startswith(prefix) and name[len(prefix) :].isdigit():
            return name
    return None


def is_sidecar_label(label: str) -> bool:
    """A needle of the current sidecar root or of any historical sidecar folder."""
    return sidecar_category(label) is not None


def _scan_closure(
    repo: Path, closure: Closure, scanner: Scanner
) -> tuple[dict[tuple[str, str], Cell], dict[str, int], int]:
    """Every population of both scopes scanned: (cells, utf16 decodes, blob bytes)."""
    width = len(scanner.labels)
    cells = {(s, p): Cell(width) for s in SCOPES for p in POPULATIONS}
    for oid, message in closure.messages.items():
        result = scanner.scan(message)
        cells[("full", "messages")].add(result)
        if oid == closure.tip:
            cells[("head", "messages")].add(result)
    for path in closure.paths:
        result = scanner.scan(path)
        cells[("full", "paths")].add(result)
        if path in closure.head_paths:
            cells[("head", "paths")].add(result)
    utf16 = {"head": 0, "full": 0}
    blob_bytes = 0
    for oid, kind, data in stream_objects(repo, pack_order(repo, closure.blobs)):
        if kind != "blob":
            raise UnmeasuredError("a blob entry names an object that is not a blob")
        blob_bytes += len(data)
        text, decoded = text_of(data)
        result = scanner.scan(text)
        cells[("full", "blobs")].add(result)
        utf16["full"] += decoded
        if oid in closure.head_blobs:
            cells[("head", "blobs")].add(result)
            utf16["head"] += decoded
    return cells, utf16, blob_bytes


def label_letter(label: str) -> str | None:
    """The drive letter a root needle's label ends with, or None for any other label."""
    last = label.rsplit(".", 1)[-1] if "." in label else ""
    return last if len(last) == 1 and last in string.ascii_uppercase else None


def shown_labels(table: Table, labels: list[str], seeds: list[str]) -> list[str]:
    """The labels a report prints, in label order.

    Never a hidden (absent or any-letter) needle; a root needle only on a seed letter or
    where it counts at least one occurrence in some cell; every other label always.
    """
    shown = []
    for label in labels:
        if label.startswith((ABSENT_PREFIX, COVER_PREFIX)):
            continue
        letter = label_letter(label)
        if letter is None or letter in seeds or any(row[label][0] for row in table.values()):
            shown.append(label)
    return shown


def _report_cells(
    cells: dict[tuple[str, str], Cell], labels: list[str], seeds: list[str], emit: Emit
) -> Table:
    table: Table = {
        key: {label: (cell.occ[k], cell.lines[k], cell.objs[k]) for k, label in enumerate(labels)}
        for key, cell in cells.items()
    }
    shown = shown_labels(table, labels, seeds)
    for scope in SCOPES:
        for pop in POPULATIONS:
            emit(f"cell {scope}.{pop} objects {cells[(scope, pop)].objects}")
            row = table[(scope, pop)]
            for label in shown:
                occ, lines, objs = row[label]
                emit(f"count {scope}.{pop} {label} occ {occ} lines {lines} objs {objs}")
    return table


def _report_liveness(table: Table, labels: list[str], emit: Emit) -> tuple[int, int, int, int]:
    """One liveness line per sidecar category.

    Returns:
        The full.blobs occ summed over every sidecar needle, the number of those
        needles, the number of categories with any occurrence in the closure, and the
        number of categories.
    """
    full_blobs = table[("full", "blobs")]
    sidecar_labels = [label for label in labels if is_sidecar_label(label)]
    categories: dict[str, list[str]] = {}
    for label in sidecar_labels:
        categories.setdefault(sidecar_category(label) or label, []).append(label)
    live = 0
    for category, members in categories.items():
        in_blobs = sum(full_blobs[label][0] for label in members)
        in_all = sum(table[("full", pop)][label][0] for pop in POPULATIONS for label in members)
        live += in_all > 0
        emit(
            f"liveness {category} full_blobs_occ {in_blobs} full_all_occ {in_all} "
            f"zero_in_history {_flag(in_all == 0)}"
        )
    occ = sum(full_blobs[label][0] for label in sidecar_labels)
    return occ, len(sidecar_labels), live, len(categories)


def uncovered(table: Table, roots: list[str], drives: list[str]) -> int:
    """The roots' closure occurrences the per-letter needles of ``drives`` did not count.

    Args:
        table: The census table, hidden any-letter needles included.
        roots: The root labels, absent root excluded.
        drives: The letters whose per-letter needles are summed.

    Returns:
        Each root's any-letter occ less its per-letter occ over ``drives``, summed over
        the full closure's three populations, both spellings and every root.
    """
    total = 0
    for pop in POPULATIONS:
        row = table[("full", pop)]
        for name in roots:
            for any_label, prefix in (
                (f"{COVER_PREFIX}{name}", f"{name}."),
                (f"{COVER_PREFIX}{name}.{BASH}", f"{name}.{BASH}."),
            ):
                total += row[any_label][0] - sum(row[prefix + d][0] for d in drives)
    return total


def scan_letters(seeds: list[str]) -> list[str]:
    """Every drive letter the census scans: the seeds in their order, then the rest A-Z."""
    return [*seeds, *(c for c in string.ascii_uppercase if c not in seeds)]


def run_census(
    repo: Path,
    tip: str,
    root_comps: dict[str, list[str]],
    hosts: dict[str, str],
    drives: list[str],
    emit: Emit,
) -> tuple[int, Table]:
    """Measure every needle over the tip's closure and report the counts and controls.

    Args:
        repo: The repository being measured.
        tip: The tip, a full lower-case hex commit id.
        root_comps: Each root's components, keyed by its category label.
        hosts: Each host name, keyed by its kind.
        drives: The seed letters, always printed and first in label order; every other
            letter A-Z is scanned too and printed only where a root occurs on it.
        emit: Where each report line goes.

    Returns:
        The exit code (0 every control passed, 1 one failed) and the full table over
        every letter, absent and any-letter needles included.

    Raises:
        UnmeasuredError: On a failed precondition or an unreadable object.
    """
    started = time.monotonic()
    raw_len = preconditions(repo, tip, emit)
    absent_comps = [f"cs-absent-{secrets.token_hex(12)}"]
    absent_host = f"absent-{secrets.token_hex(8)}"
    letters = scan_letters(drives)
    scanner = build_scanner(root_comps, hosts, absent_comps, absent_host, letters)
    labels = scanner.labels
    selfcheck_ok = matcher_selfcheck(
        {**root_comps, "absent": absent_comps}, {**hosts, "absent": absent_host}, letters
    )
    with object_reader(repo) as read:
        closure = Closure(read, tip, raw_len)
    cells, utf16, blob_bytes = _scan_closure(repo, closure, scanner)
    family = rev_list_family(repo, tip)
    walk_ok = (
        family["commit"] == set(closure.messages)
        and family["tree"] == closure.trees
        and family["blob"] == closure.blobs
    )
    emit(
        f"size commits {len(closure.messages)} trees {len(closure.trees)} "
        f"blobs {len(closure.blobs)} paths {len(closure.paths)} "
        f"head_trees {len(closure.head_trees)} head_blobs {len(closure.head_blobs)} "
        f"head_paths {len(closure.head_paths)} blob_bytes {blob_bytes} "
        f"utf16_decoded_head {utf16['head']} utf16_decoded_full {utf16['full']}"
    )
    table = _report_cells(cells, labels, drives, emit)
    shown = shown_labels(table, labels, drives)
    full_blobs = table[("full", "blobs")]
    residual = sum(full_blobs[f"repo_root.{letter}"][0] for letter in letters)
    sidecar, sidecar_needles, live, categories = _report_liveness(table, shown, emit)
    off_set = uncovered(table, list(root_comps), letters)
    absent_total = sum(
        v[0]
        for row in table.values()
        for label, v in row.items()
        if label.startswith(ABSENT_PREFIX)
    )
    controls = [
        ("root_residual_nonzero", residual > 0, f"full.blobs repo_root occ {residual}"),
        (
            "sidecar_residual_nonzero",
            sidecar > 0,
            f"full.blobs sidecar occ {sidecar} over {sidecar_needles} needles",
        ),
        ("absent_token_zero", absent_total == 0, f"occ {absent_total} over 6 cells"),
        ("matcher_selfcheck", selfcheck_ok, "every needle"),
        ("walk_complete", walk_ok, "commits, trees and blobs equal rev-list --objects"),
        (
            "drive_coverage",
            off_set == 0,
            f"any-letter occ less the per-letter sum over {len(letters)} letters {off_set}",
        ),
        (
            "sidecar_categories_live",
            live == categories,
            f"{live} of {categories} categories occur in the closure",
        ),
    ]
    for name, ok, detail in controls:
        emit(f"control {name} {'PASS' if ok else 'FAIL'} ({detail})")
    passed = sum(1 for _, ok, _ in controls if ok)
    emit(f"result controls_passed {passed} of {len(controls)}; hits never abort")
    emit(f"elapsed_s {int(time.monotonic() - started)}")
    code = 0 if passed == len(controls) else 1
    if code:
        emit("UNMEASURED a control failed - an adjudicator rules before the count is used")
    emit(f"exit {code}")
    return code, table


# ---------------------------------------------------------------- entry point


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:  # never echo an argument value
        del message
        raise UnmeasuredError("usage error (argument values are never printed)")


def _parser() -> _Parser:
    parser = _Parser(description="CS-1328 (b) census axis - counts and booleans only.")
    parser.add_argument("--repo", help="the repository to measure: a clone or a checkout")
    parser.add_argument("--tip", help="<T>, the full hex SHA of the tip to measure")
    parser.add_argument("--root", help="override: this repository's root (may be --repo)")
    parser.add_argument("--sidecars", help="override: the fleet sidecar root")
    parser.add_argument(
        "--drive", action="append", help="a drive letter to spell every root on (repeatable)"
    )
    return parser


def _main(argv: list[str] | None) -> int:
    args = _parser().parse_args(argv)
    if not args.repo or not args.tip:
        raise UnmeasuredError("usage error: --repo and --tip are required")
    _emit("census CS-1328 (b) axis, tracked - counts and booleans only")
    repo = _absolute(args.repo)
    rc, _ = _git(repo, "rev-parse", "--git-dir")
    if rc != 0:
        raise UnmeasuredError("--repo is not a git repository git can read")
    repo_root, src_root = derive_repo_root(repo, args.root)
    _emit(f"derive repo_root true (source {src_root})")
    sidecars, src_sc = derive_sidecar_root(repo, repo_root, args.sidecars)
    _emit(f"derive sidecar_root true (source {src_sc})")
    hist, bare, layout = derive_hist_sidecars(repo_root)
    _emit(
        f"derive {SIDECAR_HIST} true (source test pattern) folders {len(hist)} "
        f"bare {len(bare)} layout {layout}"
    )
    wt = derive_wt_root(repo_root)
    _emit(f"derive {SIDECAR_WT} true (source repo root folder name)")
    _emit(f"derive {SIDECAR_WALK} true (source fixed historical name)")
    main_comps = derive_main_root(repo_root)
    _emit("derive main_root true (source local config)")
    drives, src_drv = derive_drives(str(repo_root), args.drive, os.environ.get("SYSTEMDRIVE"))
    _emit(f"derive drives {len(drives)} (source {src_drv})")
    hosts, excluded = derive_hosts()
    if not hosts:
        raise UnmeasuredError("no usable host name derived from the OS")
    distinct = len({h.lower() for h in hosts.values()})
    _emit(f"derive host_labels {len(hosts)} distinct {distinct} excluded {excluded}")
    root_comps = root_set(
        split_root(str(repo_root)), split_root(str(sidecars)), hist, bare, wt, [WALK_FOLDER],
        main_comps,
    )  # fmt: skip
    lowered = {tuple(c.lower() for c in comps) for comps in root_comps.values()}
    _emit(f"info roots_distinct {_flag(len(lowered) == len(root_comps))}")
    code, _ = run_census(repo, args.tip, root_comps, hosts, drives, _emit)
    return code


def main(argv: list[str] | None = None) -> int:
    """Run the census; exit 0 every control passed, 1 one failed, 2 unmeasured.

    Args:
        argv: The arguments, or None for the process's own.

    Returns:
        The exit code.
    """
    try:
        return _main(argv)
    except UnmeasuredError as exc:
        _emit(f"UNMEASURED {exc.reason}")
        _emit("exit 2")
        return 2
    except (Exception, KeyboardInterrupt) as exc:  # never let a traceback print a path
        _emit(f"UNMEASURED internal error {type(exc).__name__}")
        _emit("exit 2")
        return 2


if __name__ == "__main__":
    sys.exit(main())
