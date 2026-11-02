#!/usr/bin/env python3
"""CS-1368 - rewrite the fleet kit's mechanical pins in one command, in the adoption commit.

WHAT IT REWRITES, AND ONLY THIS. Three tables a human used to re-point by hand on every
kit adoption:

- ``tests/test_exception_rendering.py`` ``VENDORED_RENDER_RESIDUALS`` - the LINE of each
  row whose path is under ``ops/fleet_kit/``;
- ``tests/test_subprocess_timeouts.py`` ``EXEMPTIONS`` - the LINE of each such row;
- ``tests/test_fleet_kit.py`` - ``KIT_VERSION``, ``MANIFEST_SHA256`` and each named digest
  constant ``NOTE_FILE_SHA256`` maps a kit file to.

Each rewrite is a splice of ONE literal at an offset from one parse of the file, so a row's
reason text, every comment and every other byte stay identical. It never writes a reason
and never edits one. Left to the human, because they are arguments rather than
measurements: reason and comment prose ("moved 2826 -> 2869"), the test module docstring's
version history, ``pyproject.toml``'s measured kit codes, and any re-embed of FLEET-COMMON.

HOW A MOVED ROW IS MATCHED. By (file, expression or call, enclosing function), in line
order among rows sharing that key. A render row's own key carries no function, so the
function is read off the PREVIOUS kit bytes at the row's old line (``--previous-rev``,
default ``HEAD``, which holds them until the adoption commit lands). That is what stops a
same-count shuffle handing one site's reason to another. It REFUSES, naming file and key,
when:

- the count of measured sites differs from the rows for a key: a new site needs a human
  reason, and a vanished one needs a human to retire its reason;
- a row does not sit on a measured site of the previous bytes, or those bytes are absent;
- the rows' functions differ from the sites' functions;
- a moved site's context differs from its old context: the qualified enclosing name and the
  source of the nearest ``except`` type, since a reason about one handler or one class's
  method says nothing about another's, whose source line can read identically;
- a moved site's source line differs from its old text: its reason was MEASURED on the old
  text, and the same line is what a human checked when re-pointing by hand;
- a kit file does not hash to the manifest, or the manifest names a file no constant pins,
  or names one a constant no longer has a file for.

A refusal writes nothing. Everything is planned before the first write, and each write
applies to the bytes that plan parsed, never a second read.

TWO NAMED LIMITS. Unmoved rows: a key whose rows' lines already equal its sites' lines is
not placed, so the function, context and text checks never run on it, and a same-line text
change repins silently as a no-op. The graders key on the same literals and tolerate it too.
Indistinguishable sites: two sites of one key agreeing on function, context and text pair in
line order, so a swap of the two is not seen.

THE WITNESS. ``MANIFEST_SHA256`` is an independent witness only because a human copied it
from MAIN's note. A tool that derives it from the bytes on disk turns the pin into a
tautology: any manifest passes. So ``--expect-manifest-sha`` names the digest in MAIN's
note and refuses a manifest that does not hash to it, and a write that would CHANGE the
pinned digest refuses without that flag. ``--check`` needs no flag: it writes nothing.

THE SCANNERS ARE THE TESTS' OWN. ``scan_source`` is imported from the two test modules that
grade these tables, so the tool cannot measure a different population from its grader. They
always come from this checkout, never ``--root``, and a pytest that cannot be imported is a
one-line refusal. Neither ``Rendering`` nor ``CallSite`` needs changing; the enclosing
function of a render site and every site's context are derived here because neither records
them.

Prints file names and counts only. Exit codes: 0 clean or rewritten, 1 ``--check`` found a
stale pin, 2 refused.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
# `tools` carries no __init__.py, so the sibling is imported under its bare name; the root
# is on the path so the graders' scanners import as `tests.<module>` from a script run too.
for _entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from toolpath import resolve_tool  # noqa: E402

RENDER_REL: Final = "tests/test_exception_rendering.py"
RENDER_TABLE: Final = "VENDORED_RENDER_RESIDUALS"
RENDER_WIDTH: Final = 3
EXEMPT_REL: Final = "tests/test_subprocess_timeouts.py"
EXEMPT_TABLE: Final = "EXEMPTIONS"
EXEMPT_WIDTH: Final = 4
PINS_REL: Final = "tests/test_fleet_kit.py"
KIT_REL: Final = "ops/fleet_kit"
MANIFEST_NAME: Final = "MANIFEST.json"
MODULE_SCOPE: Final = "<module>"
NO_HANDLER: Final = "<no handler>"
BARE_HANDLER: Final = "<bare except>"
COMMON_CONSTANT: Final = "COMMON_SHA256"

EXIT_OK: Final = 0
EXIT_STALE: Final = 1
EXIT_REFUSED: Final = 2

GIT_TIMEOUT_S: Final = 60
REPLACE_ATTEMPTS: Final = 5
REPLACE_BACKOFF_S: Final = 0.2
# A pre-push hook exports these; a child git must read --root's repository, not the hook's.
GIT_ENV_DROPPED: Final = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR")

Previous = Callable[[str], bytes | None]
# Bytes in, the sites of that file out; the file's repo-relative path comes first.
Measure = Callable[[str, bytes], "list[Site]"]


class RepinRefusedError(Exception):
    """A pin this tool must not rewrite; ``problem`` names file and key, never a value."""

    def __init__(self, problem: str) -> None:
        """Hold the refusal text; rendered by field, never by the object."""
        super().__init__(problem)
        self.problem = problem


@dataclass(frozen=True)
class Splice:
    """Replace ``raw[start:end]`` with ``text``."""

    start: int
    end: int
    text: bytes


@dataclass(frozen=True)
class Row:
    """One kit row of a line-keyed table, with the offsets of its line literal."""

    path: str
    group: tuple[str, ...]
    line: int
    start: int
    end: int


@dataclass(frozen=True)
class Site:
    """One measured site: its key beside the file, enclosing function, line, text, context.

    ``context`` is the qualified enclosing name and the nearest ``except`` type's source,
    which ``function`` (a bare name, as the subprocess scanner scopes it) cannot tell apart.
    """

    group: tuple[str, ...]
    function: str
    line: int
    text: str
    context: str


@dataclass(frozen=True)
class FilePlan:
    """The bytes one file was parsed from, and the splices whose offsets index them."""

    raw: bytes
    splices: list[Splice]


def _parse(raw: bytes, rel: str) -> ast.Module:
    try:
        return ast.parse(raw)
    except (SyntaxError, ValueError):
        raise RepinRefusedError(rel + ": does not parse") from None


def _line_starts(raw: bytes) -> list[int]:
    starts = [0]
    index = raw.find(b"\n")
    while index != -1:
        starts.append(index + 1)
        index = raw.find(b"\n", index + 1)
    return starts


def _span(node: ast.expr, starts: Sequence[int]) -> tuple[int, int]:
    end_line = node.end_lineno if node.end_lineno is not None else node.lineno
    end_col = node.end_col_offset if node.end_col_offset is not None else node.col_offset
    return (starts[node.lineno - 1] + node.col_offset, starts[end_line - 1] + end_col)


def _assignments(tree: ast.Module) -> dict[str, ast.expr]:
    """Every module-level ``NAME = value``, annotated or not."""
    found: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target: ast.expr = node.targets[0]
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        else:
            continue
        if isinstance(target, ast.Name) and value is not None:
            found[target.id] = value
    return found


def _row(key: ast.expr, rel: str, width: int, starts: Sequence[int]) -> Row:
    """One table key as a Row, refusing any shape a literal cannot answer for."""
    elements = key.elts if isinstance(key, ast.Tuple) else []
    literals = [item.value for item in elements if isinstance(item, ast.Constant)]
    if len(literals) != width or len(elements) != width:
        raise RepinRefusedError(rel + ": a table key is not a literal tuple")
    names = [name for name in literals[:-1] if isinstance(name, str)]
    line = literals[-1]
    if len(names) != width - 1 or not isinstance(line, int):
        raise RepinRefusedError(rel + ": a table key has the wrong literal types")
    start, end = _span(elements[-1], starts)
    return Row(names[0], tuple(names[1:]), line, start, end)


def _table_rows(raw: bytes, rel: str, name: str, width: int) -> list[Row]:
    """The rows of table ``name`` whose path sits under the kit directory."""
    table = _assignments(_parse(raw, rel)).get(name)
    if not isinstance(table, ast.Dict):
        raise RepinRefusedError(rel + ": no literal table " + name)
    starts = _line_starts(raw)
    rows = []
    for key in table.keys:
        if key is None:
            raise RepinRefusedError(rel + ": a ** entry in table " + name)
        row = _row(key, rel, width, starts)
        if row.path.startswith(KIT_REL + "/"):
            rows.append(row)
    keys = [(row.path, row.group, row.line) for row in rows]
    if len(set(keys)) != len(keys):
        raise RepinRefusedError(rel + ": a duplicate row in table " + name)
    return rows


def _enclosing(tree: ast.Module, line: int) -> str:
    """The innermost function holding ``line``, as the subprocess scanner scopes it."""
    best = MODULE_SCOPE
    best_line = -1
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        end = node.end_lineno if node.end_lineno is not None else node.lineno
        if node.lineno <= line <= end and node.lineno > best_line:
            best, best_line = node.name, node.lineno
    return best


def _scopes(node: ast.AST, prefix: str) -> Iterator[tuple[str, ast.stmt]]:
    """Every class and function beneath ``node``, with its dotted qualified name."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            yield prefix + child.name, child
            yield from _scopes(child, prefix + child.name + ".")
        else:
            yield from _scopes(child, prefix)


def _holds(node: ast.stmt | ast.ExceptHandler, line: int) -> bool:
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    return node.lineno <= line <= end


def _context(tree: ast.Module, raw: bytes, line: int) -> str:
    """The qualified scope holding ``line``, and the source of the nearest handler's type."""
    scope = MODULE_SCOPE
    scope_line = -1
    for name, node in _scopes(tree, ""):
        if _holds(node, line) and node.lineno > scope_line:
            scope, scope_line = name, node.lineno
    handler = NO_HANDLER
    handler_line = -1
    starts = _line_starts(raw)
    for candidate in ast.walk(tree):
        if not isinstance(candidate, ast.ExceptHandler) or not _holds(candidate, line):
            continue
        if candidate.lineno > handler_line:
            handler_line = candidate.lineno
            handler = BARE_HANDLER
            if candidate.type is not None:
                start, end = _span(candidate.type, starts)
                handler = raw[start:end].decode("utf-8", "replace")
    return scope + " | " + handler


def _source_line(raw: bytes, line: int) -> str:
    return raw.split(b"\n")[line - 1].strip().decode("utf-8", "replace")


def _scanner(module: str) -> Any:
    """A grader module, or a refusal: an import traceback would carry this machine's paths."""
    try:
        return importlib.import_module(module)
    except ImportError:
        raise RepinRefusedError(
            module + ": cannot be imported; pytest must be installed to measure sites"
        ) from None


def _render_sites(rel: str, raw: bytes) -> list[Site]:
    """Every caught-exception render in one file, by the grader's own scanner."""
    scanner = _scanner("tests.test_exception_rendering")
    tree = _parse(raw, rel)
    found = scanner.scan_source(rel, raw.decode("utf-8")).found
    return [
        Site(
            (item.shape,),
            _enclosing(tree, item.lineno),
            item.lineno,
            _source_line(raw, item.lineno),
            _context(tree, raw, item.lineno),
        )
        for item in found
    ]


def _exempt_sites(rel: str, raw: bytes) -> list[Site]:
    """Every unbounded subprocess call in one file, by the grader's own scanner."""
    scanner = _scanner("tests.test_subprocess_timeouts")
    tree = _parse(raw, rel)
    return [
        Site(
            (item.function, item.callee),
            item.function,
            item.lineno,
            _source_line(raw, item.lineno),
            _context(tree, raw, item.lineno),
        )
        for item in scanner.scan_source(rel, raw.decode("utf-8"))
        if not item.bounded
    ]


def _key_text(rel: str, group: Iterable[str]) -> str:
    return rel + ": " + " ".join(group)


def _function_then_line(site: Site) -> tuple[str, int]:
    return (site.function, site.line)


def _place_moved(
    rel: str, rows: Sequence[Row], sites: Sequence[Site], measure: Measure, previous: Previous
) -> list[tuple[Row, int]]:
    """Pair moved rows with their new sites, by enclosing function, then in line order."""
    key = _key_text(rel, rows[0].group)
    old_raw = previous(rel)
    if old_raw is None:
        raise RepinRefusedError(key + ": rows moved and no previous bytes to place them on")
    old = {(site.group, site.line): site for site in measure(rel, old_raw)}
    pairs = []
    for row in rows:
        site = old.get((row.group, row.line))
        if site is None:
            raise RepinRefusedError(key + ": a row is not on a site of the previous bytes")
        pairs.append((row, site))
    pairs.sort(key=lambda pair: _function_then_line(pair[1]))
    placed = sorted(sites, key=_function_then_line)
    if [pair[1].function for pair in pairs] != [site.function for site in placed]:
        raise RepinRefusedError(key + ": the rows' enclosing functions differ from the sites'")
    if [pair[1].context for pair in pairs] != [site.context for site in placed]:
        raise RepinRefusedError(key + ": a site's scope or handler changed; a human re-measures it")
    if [pair[1].text for pair in pairs] != [site.text for site in placed]:
        raise RepinRefusedError(key + ": a site's source line changed; a human re-measures it")
    return [(pair[0], site.line) for pair, site in zip(pairs, placed, strict=True)]


def _repoint_file(
    rel: str, rows: Sequence[Row], sites: Sequence[Site], measure: Measure, previous: Previous
) -> list[tuple[Row, int]]:
    """The (row, new line) pairs of one kit file, refusing any count that differs."""
    moves: list[tuple[Row, int]] = []
    groups = {row.group for row in rows} | {site.group for site in sites}
    for group in sorted(groups):
        group_rows = sorted((row for row in rows if row.group == group), key=lambda row: row.line)
        group_sites = sorted((site for site in sites if site.group == group), key=lambda s: s.line)
        if len(group_rows) != len(group_sites):
            raise RepinRefusedError(
                _key_text(rel, group)
                + ": "
                + str(len(group_rows))
                + " row(s) against "
                + str(len(group_sites))
                + " measured site(s); a human owns the reason"
            )
        if [row.line for row in group_rows] == [site.line for site in group_sites]:
            continue
        moves.extend(_place_moved(rel, group_rows, group_sites, measure, previous))
    return moves


def _kit_python(root: Path) -> list[str]:
    return sorted(path.name for path in (root / KIT_REL).glob("*.py"))


def _table_splices(
    root: Path,
    table_rel: str,
    table: tuple[str, int],
    measure: Measure,
    previous: Previous,
) -> FilePlan:
    """The line-literal splices for one table, over every kit python file."""
    raw = (root / table_rel).read_bytes()
    rows = _table_rows(raw, table_rel, table[0], table[1])
    rels = {KIT_REL + "/" + name for name in _kit_python(root)} | {row.path for row in rows}
    splices = []
    for rel in sorted(rels):
        path = root / rel
        sites = measure(rel, path.read_bytes()) if path.is_file() else []
        file_rows = [row for row in rows if row.path == rel]
        for row, line in _repoint_file(rel, file_rows, sites, measure, previous):
            if row.line != line:
                splices.append(_line_splice(raw, row, line, table_rel))
    return FilePlan(raw, splices)


def _line_splice(raw: bytes, row: Row, line: int, table_rel: str) -> Splice:
    if raw[row.start : row.end] != str(row.line).encode("ascii"):
        raise RepinRefusedError(table_rel + ": a line literal is not spelled plainly")
    return Splice(row.start, row.end, str(line).encode("ascii"))


def _spell(value: str | int) -> bytes:
    text = '"' + value + '"' if isinstance(value, str) else str(value)
    return text.encode("ascii")


def _literal_splice(
    raw: bytes, node: ast.expr, new: str | int, rel: str, name: str
) -> list[Splice]:
    """A one-literal splice of a module constant, empty when it already holds ``new``."""
    if not isinstance(node, ast.Constant) or type(node.value) is not type(new):
        raise RepinRefusedError(rel + ": " + name + " is not a literal of the pinned type")
    if node.value == new:
        return []
    start, end = _span(node, _line_starts(raw))
    if raw[start:end] != _spell(node.value):
        raise RepinRefusedError(rel + ": " + name + " is not spelled plainly")
    return [Splice(start, end, _spell(new))]


def _named_constants(assigned: dict[str, ast.expr]) -> dict[str, tuple[str, ast.expr]]:
    """Map each kit file NOTE_FILE_SHA256 names to its (constant name, literal node)."""
    table = assigned.get("NOTE_FILE_SHA256")
    if not isinstance(table, ast.Dict):
        raise RepinRefusedError(PINS_REL + ": no literal table NOTE_FILE_SHA256")
    named: dict[str, tuple[str, ast.expr]] = {}
    for key, value in zip(table.keys, table.values, strict=True):
        source = None
        if (
            isinstance(key, ast.Attribute)
            and key.attr == "name"
            and isinstance(key.value, ast.Name)
        ):
            source = assigned.get(key.value.id)
        if (
            not isinstance(source, ast.BinOp)
            or not isinstance(source.right, ast.Constant)
            or not isinstance(source.right.value, str)
            or not isinstance(value, ast.Name)
            or value.id not in assigned
        ):
            raise RepinRefusedError(PINS_REL + ": a NOTE_FILE_SHA256 row is not KIT_X.name: X")
        named[source.right.value] = (value.id, assigned[value.id])
    return named


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_manifest(root: Path) -> tuple[bytes, int, dict[str, str], str]:
    """The manifest's bytes, version, file digests and common-block digest."""
    rel = KIT_REL + "/" + MANIFEST_NAME
    path = root / rel
    if not path.is_file():
        raise RepinRefusedError(rel + ": absent")
    raw = path.read_bytes()
    try:
        body = json.loads(raw.decode("ascii"))
        version, files, common = body["version"], dict(body["files"]), body["common_block_sha256"]
    except (ValueError, KeyError, TypeError):
        raise RepinRefusedError(rel + ": not a kit manifest") from None
    if not isinstance(version, int):
        raise RepinRefusedError(rel + ": its version is not an integer")
    return raw, version, files, common


def _check_kit_bytes(
    root: Path, files: dict[str, str], common: str, named: dict[str, tuple[str, ast.expr]]
) -> None:
    """Refuse anything a digest pin could not honestly witness."""
    kit = root / KIT_REL
    unpinned = sorted(set(files) ^ set(named))
    if unpinned:
        raise RepinRefusedError(KIT_REL + "/" + unpinned[0] + ": in only one of manifest and pins")
    on_disk = {path.name for path in kit.iterdir() if path.is_file()} - {MANIFEST_NAME}
    strays = sorted(on_disk ^ set(files))
    if strays:
        raise RepinRefusedError(KIT_REL + "/" + strays[0] + ": in only one of manifest and disk")
    for name in sorted(files):
        if _sha((kit / name).read_bytes()) != files[name]:
            raise RepinRefusedError(KIT_REL + "/" + name + ": does not hash to the manifest")
    commons = [name for name, (constant, _node) in named.items() if constant == COMMON_CONSTANT]
    if len(commons) != 1 or files[commons[0]] != common:
        raise RepinRefusedError(
            KIT_REL + "/" + MANIFEST_NAME + ": common block digest is not " + COMMON_CONSTANT
        )


def _pin_splices(root: Path, expect: str | None, need_witness: bool) -> FilePlan:
    """The version and digest splices of the pin module, checked against the manifest."""
    manifest_raw, version, files, common = _load_manifest(root)
    digest = _sha(manifest_raw)
    if expect is not None and expect.lower() != digest:
        raise RepinRefusedError(
            KIT_REL + "/" + MANIFEST_NAME + ": does not hash to --expect-manifest-sha"
        )
    raw = (root / PINS_REL).read_bytes()
    assigned = _assignments(_parse(raw, PINS_REL))
    named = _named_constants(assigned)
    _check_kit_bytes(root, files, common, named)
    for name in ("KIT_VERSION", "MANIFEST_SHA256"):
        if name not in assigned:
            raise RepinRefusedError(PINS_REL + ": no constant " + name)
    manifest_splices = _literal_splice(
        raw, assigned["MANIFEST_SHA256"], digest, PINS_REL, "MANIFEST_SHA256"
    )
    if manifest_splices and need_witness:
        raise RepinRefusedError(
            PINS_REL + ": MANIFEST_SHA256 would change; name MAIN's digest in --expect-manifest-sha"
        )
    splices = [
        *_literal_splice(raw, assigned["KIT_VERSION"], version, PINS_REL, "KIT_VERSION"),
        *manifest_splices,
    ]
    for name, (constant, node) in sorted(named.items()):
        splices.extend(_literal_splice(raw, node, files[name], PINS_REL, constant))
    return FilePlan(raw, splices)


def plan(
    root: Path, *, expect: str | None, need_witness: bool, previous: Previous
) -> dict[str, FilePlan]:
    """Every splice this tree needs, per file, or a refusal. Writes nothing."""
    planned = {
        RENDER_REL: _table_splices(
            root, RENDER_REL, (RENDER_TABLE, RENDER_WIDTH), _render_sites, previous
        ),
        EXEMPT_REL: _table_splices(
            root, EXEMPT_REL, (EXEMPT_TABLE, EXEMPT_WIDTH), _exempt_sites, previous
        ),
        PINS_REL: _pin_splices(root, expect, need_witness),
    }
    return {rel: file_plan for rel, file_plan in planned.items() if file_plan.splices}


def _apply(raw: bytes, splices: Iterable[Splice]) -> bytes:
    """Apply splices from the last offset back, so no offset is disturbed."""
    for splice in sorted(splices, key=lambda item: item.start, reverse=True):
        raw = raw[: splice.start] + splice.text + raw[splice.end :]
    return raw


def write_atomic(path: Path, data: bytes) -> None:
    """Write bytes through a sibling temp and a rename, retrying a Windows share refusal."""
    temp = path.with_name(path.name + ".repin-tmp")
    try:
        temp.write_bytes(data)
        for attempt in range(REPLACE_ATTEMPTS):
            try:
                temp.replace(path)
            except PermissionError:
                if attempt == REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(REPLACE_BACKOFF_S)
            else:
                return
    except OSError:
        temp.unlink(missing_ok=True)
        raise


def git_previous(root: Path, rev: str) -> Previous:
    """A reader of ``rev:<path>`` in ``root``'s repository; None when it holds no such file."""
    env = {key: value for key, value in os.environ.items() if key not in GIT_ENV_DROPPED}
    git = resolve_tool("git")

    def read(rel: str) -> bytes | None:
        if git is None:
            return None
        argv = [git, "-C", str(root), "show", rev + ":" + rel]
        try:
            done = subprocess.run(
                argv, capture_output=True, check=False, timeout=GIT_TIMEOUT_S, env=env
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return done.stdout if done.returncode == 0 else None

    return read


def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rewrite the fleet kit's mechanical pins.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="tree holding the pins")
    parser.add_argument("--check", action="store_true", help="exit 1 on a stale pin; never write")
    parser.add_argument(
        "--expect-manifest-sha", default=None, help="the MANIFEST.json digest MAIN's note names"
    )
    parser.add_argument(
        "--previous-rev", default="HEAD", help="the revision holding the previous kit bytes"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None, *, previous: Previous | None = None) -> int:
    """Run the tool; ``previous`` replaces the git reader so a test needs no repository."""
    args = _arguments(argv)
    root = args.root
    reader = previous if previous is not None else git_previous(root, args.previous_rev)
    try:
        planned = plan(
            root,
            expect=args.expect_manifest_sha,
            need_witness=not args.check and args.expect_manifest_sha is None,
            previous=reader,
        )
        for rel, file_plan in planned.items():
            count = str(len(file_plan.splices))
            if args.check:
                print("repin_kit: " + rel + ": " + count + " pin(s) stale")
                continue
            write_atomic(root / rel, _apply(file_plan.raw, file_plan.splices))
            print("repin_kit: " + rel + ": " + count + " pin(s) rewritten")
    except RepinRefusedError as refused:
        print("repin_kit: REFUSED: " + refused.problem, file=sys.stderr)
        return EXIT_REFUSED
    except OSError as failed:
        print("repin_kit: REFUSED: " + type(failed).__name__ + " on a pin file", file=sys.stderr)
        return EXIT_REFUSED
    if not planned:
        print("repin_kit: no pin to change")
    return EXIT_STALE if planned and args.check else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
