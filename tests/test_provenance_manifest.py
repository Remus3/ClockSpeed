#!/usr/bin/env python3
"""Every tracked file is accounted for in a produced provenance manifest.

CS-1165. ``tests/test_unregistered_lift.py`` finds a lift by the sibling
namespace its bytes NAME, so a de-branded lift - ``ops/loop/winmutex.py`` at a
fresh path is the measured shape - names nothing and passes it green. This
module closes that half with an oracle every checkout carries: the manifest
``tools/provenance.tsv``, one row per tracked path, and a tracked path with no
row is RED naming it. Nothing is added anywhere by a lift, so a lift has no row.

THE POPULATION is ``git ls-files --cached --others --exclude-standard``: the
index plus every untracked file git does not ignore, the same population the
branded arm reads. It reads no history, so it is exact on the depth-1 checkout
CI makes, where it reduces to the index. Untracked files are IN it by
adjudication (CS-1165, Q2): a plain copy with no ``git add`` is the literal
acceptance mutation and must be red. Scratch output belongs in a scratchpad.

THE MANIFEST GRAMMAR, which ``tools/provenance_stamp.py`` writes and this module
alone grades. 7-bit ASCII, LF only, a final newline. Line 1 is one header
comment starting with :data:`HEADER_PREFIX`. Every later line is one row of
exactly four TAB-separated cells, no quoting, no blank lines, no further
comments, sorted by path bytes, each path once::

    path    class    item    basis

``class`` is ``authored`` or ``vendored`` and nothing else parses. ``item`` is
a ``CS-`` id; it is TRACEABILITY, not evidence - any real id can be cited, and
the record check below is weak for that reason and says so. ``basis`` is
``stamped`` (written by the tool's add or mv), ``first-add:CS-NNNN`` or
``first-add:root`` (the one-time bootstrap). There is deliberately no digest
column: vendored bytes are already pinned by their own test modules, and a
second digest here would be a restated fact needing a re-pin in two places.

WHAT A LYING ROW MEETS. A file stamped ``authored`` is compared with every
vendored file's live bytes by the near-duplicate metric below, so a copy of a
vendored file under an authored row is red whatever it is called. The set of
``vendored`` rows must equal the register's vendored table, both directions.

THE ARMS THAT GRADE THE REAL TREE FAIL, NOT SKIP, WHILE THE MANIFEST IS ABSENT.
This module therefore ships in the same push as the manifest (CS-1165 S3).
Every other arm grades synthetic manifests - in a throwaway git repository
under ``tmp_path`` and over an in-memory population read from the real index -
and each mutant is asserted to have LANDED before its verdict is read.

WHAT THIS DOES NOT COVER, stated rather than left to be discovered: a file
lifted from a sibling that was NEVER vendored here, de-branded, and stamped
``authored`` with a real item id. Authorship is not a property of bytes; the
manifest turns that silent lift into a recorded false declaration with an item
id and a commit on it. A lift edited below the overlap threshold is residual
too. No arm here reads a sibling tree, and none may.
"""

from __future__ import annotations

import ast
import functools
import os
import re
import shutil
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import NamedTuple

import pytest

from tests.test_third_party_register import REPO_ROOT, _listed_paths, _register_text

#: The manifest, repo-relative. Tool-owned data beside its tool.
MANIFEST_RELATIVE = "tools/provenance.tsv"

#: The manifest on disk in this tree.
MANIFEST = REPO_ROOT / MANIFEST_RELATIVE

#: The tool that writes it. Named in every missing-manifest message.
STAMP_TOOL = "tools/provenance_stamp.py"

#: The only two classes a row may carry.
CLASSES = ("authored", "vendored")

#: The number of TAB-separated cells in every row.
COLUMNS = 4

#: What line 1 must start with. Its remainder is free ASCII text.
HEADER_PREFIX = "# "

#: A row's item cell, matched whole.
ITEM_RE = re.compile(r"CS-[0-9]+")

#: A row's basis cell, matched whole.
BASIS_RE = re.compile(r"stamped|first-add:(?:root|CS-[0-9]+)")

#: An item id as it is cited in the record files, not glued to a neighbour.
CITED_RE = re.compile(r"(?<![A-Za-z0-9])CS-[0-9]+(?![0-9A-Za-z])")

#: The files an item id must appear in. OPEN work and CLOSED work between them
#: hold every id this tree has used; measured 2026-09-22, every CS id in a
#: first-add commit subject appears in one of the two.
RECORD_FILES = ("ROADMAP.md", "docs/LEDGER.md")

#: The shortest stripped line the near-duplicate metric counts. Shorter lines
#: - a bare ``return``, a closing bracket, ``else:`` - recur in any two files of
#: the same language and would measure the language rather than the lift.
LINE_FLOOR = 20

#: The overlap at or above which an authored file is a near-duplicate of a
#: vendored one: at least half the vendored file's distinct long lines. The
#: measured maximum on the tree this was written on was 7 of 110 (0.064), so
#: the threshold sits far from both a real lift (1.0) and the tree's own code.
THRESHOLD = Fraction(1, 2)

#: The current tree must stay below THRESHOLD divided by this, so the margin
#: eroding is loud long before a real file crosses the threshold by accident.
MARGIN_DIVISOR = 2

#: A threshold no score can reach. Used ONLY by the sensitivity control, which
#: proves the near-duplicate red comes from the metric and not from vacuity.
UNREACHABLE = Fraction(3, 2)

#: Seconds allowed for each git child this module spawns.
GIT_TIMEOUT = 60

#: The de-branded vendored file the acceptance lifts.
LIFT_SOURCE = "ops/loop/winmutex.py"

#: A byte-pinned vendored file lifted byte-identical by M3, and unregistered by M5.
SECOND_VENDORED = "ops/loop/slots.py"

#: Where every mutation plants. Nothing lists, pins or registers this path.
LIFT_TARGET = "ops/loop/cs1165_provenance_copy.py"

#: The item a synthetic row cites. It is this item, so it is on record.
SYNTHETIC_ITEM = "CS-1165"

#: The basis a synthetic row carries.
SYNTHETIC_BASIS = "first-add:root"

#: The check names :func:`_grade` reports under, in reporting order.
CHECKS = ("parse", "unrepresentable", "unlisted", "stale", "vendored", "near_duplicate", "uncited")


class Row(NamedTuple):
    """One manifest row after its path cell."""

    klass: str
    item: str
    basis: str


def _path_key(path: str) -> bytes:
    """Return the sort key the manifest is ordered by: the path's bytes.

    Args:
        path: A repo-relative POSIX path.

    Returns:
        Its UTF-8 bytes.
    """
    return path.encode("utf-8")


def _parse_manifest(raw: bytes) -> tuple[dict[str, Row], list[str]]:
    """Parse manifest bytes into rows, collecting every grammar fault.

    Args:
        raw: The manifest's bytes.

    Returns:
        The rows keyed by path, and one fault message per violation. A row
        that fails its own line's grammar is dropped from the mapping.
    """
    faults: list[str] = []
    if not raw.isascii():
        faults.append("the manifest is not 7-bit ASCII")
    if b"\r" in raw:
        faults.append("the manifest carries a CR; it is LF only")
    if not raw.endswith(b"\n"):
        faults.append("the manifest is empty or has no final newline")
    lines = raw.decode("ascii", "replace").replace("\r", "").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or not lines[0].startswith(HEADER_PREFIX):
        faults.append(f"line 1 is not a header comment starting with {HEADER_PREFIX!r}")
    rows: dict[str, Row] = {}
    order: list[str] = []
    for number, line in enumerate(lines[1:], start=2):
        cells = line.split("\t")
        if line == "" or line.startswith("#"):
            faults.append(f"line {number} is blank or a second comment")
            continue
        if len(cells) != COLUMNS:
            faults.append(f"line {number} has {len(cells)} cells, not {COLUMNS}")
            continue
        path, klass, item, basis = cells
        bad = [
            label
            for label, ok in (
                ("an empty path", path != ""),
                ("an unknown class", klass in CLASSES),
                ("a malformed item", ITEM_RE.fullmatch(item) is not None),
                ("a malformed basis", BASIS_RE.fullmatch(basis) is not None),
            )
            if not ok
        ]
        if bad:
            faults.append(f"line {number} ({path!r}) carries {', '.join(bad)}")
            continue
        if path in rows:
            faults.append(f"line {number} repeats the path {path!r}")
            continue
        rows[path] = Row(klass, item, basis)
        order.append(path)
    if order != sorted(order, key=_path_key):
        first = next(p for p, q in zip(order, sorted(order, key=_path_key), strict=True) if p != q)
        faults.append(f"the rows are not sorted by path bytes, first out of place: {first!r}")
    return rows, faults


def _render(rows: Mapping[str, Row]) -> bytes:
    """Return the canonical manifest bytes for ``rows``.

    Args:
        rows: Rows keyed by path.

    Returns:
        A header line and one sorted row per path, LF, final newline.
    """
    header = f"{HEADER_PREFIX}path\tclass\titem\tbasis - CS-1165 provenance manifest\n"
    body = "".join(
        f"{path}\t{row.klass}\t{row.item}\t{row.basis}\n"
        for path, row in sorted(rows.items(), key=lambda pair: _path_key(pair[0]))
    )
    return (header + body).encode("ascii")


def _unrepresentable(tracked: Iterable[str]) -> list[str]:
    """Return every tracked path the manifest grammar cannot hold.

    Args:
        tracked: Repo-relative paths.

    Returns:
        The paths carrying a TAB, a newline or a non-ASCII character, sorted.
    """
    return sorted(
        (path for path in tracked if not path.isascii() or "\t" in path or "\n" in path),
        key=_path_key,
    )


def _distinct_lines(raw: bytes) -> frozenset[str] | None:
    """Return the set of stripped lines at least :data:`LINE_FLOOR` long.

    Args:
        raw: A file's bytes.

    Returns:
        The line set, or None when the bytes do not decode as UTF-8.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return frozenset(
        stripped
        for stripped in (line.strip() for line in text.splitlines())
        if len(stripped) >= LINE_FLOOR
    )


def _overlap(candidate: bytes, vendored: bytes) -> Fraction | None:
    """Return the share of the vendored file's long lines the candidate holds.

    Args:
        candidate: An authored file's bytes.
        vendored: A vendored file's bytes.

    Returns:
        ``|L(candidate) & L(vendored)| / |L(vendored)|``, or None when either
        file is undecodable or the vendored file has no long line - the regime
        in which only byte equality is graded.
    """
    shared = _shared(candidate, vendored)
    return None if shared is None else Fraction(*shared)


def _shared(candidate: bytes, vendored: bytes) -> tuple[int, int] | None:
    """Return the shared and total long-line counts behind :func:`_overlap`.

    Args:
        candidate: An authored file's bytes.
        vendored: A vendored file's bytes.

    Returns:
        ``(shared, total)`` unreduced, or None in the byte-equality regime.
    """
    theirs = _distinct_lines(vendored)
    ours = _distinct_lines(candidate)
    if theirs is None or ours is None or not theirs:
        return None
    return len(ours & theirs), len(theirs)


def _near_duplicates(
    files: Mapping[str, bytes],
    rows: Mapping[str, Row],
    vendored: Iterable[str],
    threshold: Fraction,
) -> list[str]:
    """Return each authored row whose file duplicates a vendored file.

    Byte identity is NOT graded separately where the metric applies: an
    identical file scores exactly 1, which meets any threshold at or below 1.
    That keeps the sensitivity control honest - raise the threshold past 1 and
    a verbatim copy survives, proving the red came from the metric.

    Args:
        files: Repo-relative paths mapped to their bytes.
        rows: The manifest rows.
        vendored: The vendored paths to compare against.
        threshold: The overlap at or above which a pair is red.

    Returns:
        One ``path vs vendored (overlap n/d)`` or ``(byte-identical)`` entry
        per offending pair, sorted.
    """
    sources = sorted((path for path in set(vendored) if path in files), key=_path_key)
    found: list[str] = []
    for path in sorted(rows, key=_path_key):
        if rows[path].klass != "authored" or path not in files:
            continue
        for source in sources:
            shared = _shared(files[path], files[source])
            if shared is None:
                if files[path].replace(b"\r\n", b"\n") == files[source].replace(b"\r\n", b"\n"):
                    found.append(f"{path} vs {source} (byte-identical)")
            elif Fraction(*shared) >= threshold:
                found.append(f"{path} vs {source} (overlap {shared[0]}/{shared[1]})")
    return found


def _identical_finding(source: str, raw: bytes) -> str:
    """Return the finding a verbatim copy of ``source`` at the lift target yields.

    Args:
        source: The vendored path copied.
        raw: Its bytes.

    Returns:
        The exact near-duplicate entry, every long line shared.
    """
    shared = _shared(raw, raw)
    assert shared is not None, f"{source} is in the byte-equality regime"
    return f"{LIFT_TARGET} vs {source} (overlap {shared[0]}/{shared[1]})"


def _grade(
    files: Mapping[str, bytes],
    tracked: Iterable[str],
    manifest: bytes,
    register: str,
    record: str,
    threshold: Fraction = THRESHOLD,
) -> dict[str, list[str]]:
    """Grade one population against one manifest, every check at once.

    Args:
        files: Tracked paths that are files, mapped to their bytes.
        tracked: Every path in the index.
        manifest: The manifest's bytes.
        register: The third-party register's text.
        record: The concatenated record files' text.
        threshold: The near-duplicate threshold.

    Returns:
        Each name in :data:`CHECKS` mapped to its findings; all empty is green.
    """
    rows, faults = _parse_manifest(manifest)
    population = set(tracked)
    registered = set(_listed_paths(register))
    vendored_rows = {path for path, row in rows.items() if row.klass == "vendored"}
    cited = set(CITED_RE.findall(record))
    grade = {
        "parse": faults,
        "unrepresentable": _unrepresentable(population),
        "unlisted": sorted(population - set(rows), key=_path_key),
        "stale": sorted(set(rows) - population, key=_path_key),
        "vendored": sorted(
            [f"{p} (vendored row, no register row)" for p in vendored_rows - registered]
            + [f"{p} (register row, no vendored row)" for p in registered - vendored_rows]
        ),
        "near_duplicate": _near_duplicates(files, rows, registered | vendored_rows, threshold),
        "uncited": sorted(
            f"{path} ({row.item})" for path, row in rows.items() if row.item not in cited
        ),
    }
    assert tuple(grade) == CHECKS
    return grade


def _git_env() -> dict[str, str]:
    """Return the environment with every ``GIT_`` variable removed.

    The pre-push hook exports ``GIT_DIR``; a child inheriting it would act on
    the REAL repository instead of the one its working directory names.

    Returns:
        A copy of the environment safe to run git in a throwaway tree with.
    """
    return {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}


def _candidate_paths(root: Path, *, isolated: bool = False) -> list[str]:
    """Return every indexed path plus every untracked path git does not ignore.

    Untracked files are IN the population: a lift copied in with nothing
    added anywhere - not even ``git add`` - must still go red (CS-1165
    adjudication, Q2). A clean CI checkout has none, so CI grades the index.

    Args:
        root: A repository work tree.
        isolated: Strip inherited ``GIT_`` variables, for a throwaway tree.

    Returns:
        Repo-relative POSIX paths, sorted by bytes, each once.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=GIT_TIMEOUT,
        env=_git_env() if isolated else None,
    )
    names = {name for name in listing.stdout.decode("utf-8").split("\0") if name}
    return sorted(names, key=_path_key)


def _read_population(root: Path, tracked: Iterable[str]) -> dict[str, bytes]:
    """Return the bytes of every tracked path that is a file on disk.

    Args:
        root: The work tree.
        tracked: Repo-relative paths.

    Returns:
        Paths mapped to their bytes.
    """
    return {name: (root / name).read_bytes() for name in tracked if (root / name).is_file()}


@functools.cache
def _real_population() -> tuple[tuple[str, ...], dict[str, bytes]]:
    """Return this tree's index and its files' bytes, read once per run.

    Returns:
        The tracked paths and the bytes of each that is a file.
    """
    tracked = _candidate_paths(REPO_ROOT)
    return tuple(tracked), _read_population(REPO_ROOT, tracked)


def _record_text() -> str:
    """Return the record files' text, concatenated.

    Returns:
        ROADMAP.md then docs/LEDGER.md, decoded as UTF-8.
    """
    return "\n".join((REPO_ROOT / name).read_bytes().decode("utf-8") for name in RECORD_FILES)


def _real_manifest() -> bytes:
    """Return this tree's manifest bytes, RED when it does not exist.

    Returns:
        The manifest's bytes.
    """
    assert MANIFEST.is_file(), (
        f"{MANIFEST_RELATIVE} does not exist. Every tracked file must have a row "
        f"in it; produce it once with `python {STAMP_TOOL} bootstrap` and keep it "
        f"current with `python {STAMP_TOOL} add|mv|rm` (CS-1165)."
    )
    return MANIFEST.read_bytes()


def _real_grade() -> dict[str, list[str]]:
    """Grade this tree against its own manifest.

    Returns:
        The findings of every check.
    """
    tracked, files = _real_population()
    return _grade(files, tracked, _real_manifest(), _register_text(), _record_text())


def _rows_for(paths: Iterable[str], vendored: Iterable[str]) -> dict[str, Row]:
    """Return synthetic rows for ``paths``: vendored when registered, else authored.

    Args:
        paths: The paths to give rows.
        vendored: The registered paths.

    Returns:
        One row per path citing :data:`SYNTHETIC_ITEM`.
    """
    registered = set(vendored)
    return {
        path: Row("vendored" if path in registered else "authored", SYNTHETIC_ITEM, SYNTHETIC_BASIS)
        for path in paths
    }


def _debranded(raw: bytes) -> bytes:
    """Return ``raw`` with its module docstring replaced and its body kept.

    Args:
        raw: A Python module's bytes.

    Returns:
        The same module under a one-line docstring naming nothing.
    """
    text = raw.decode("utf-8")
    first = ast.parse(text).body[0]
    assert isinstance(first, ast.Expr), "the module opens with no docstring to replace"
    assert first.end_lineno is not None
    body = "".join(text.splitlines(keepends=True)[first.end_lineno :])
    return ('"""A small helper written here."""\n' + body).encode("utf-8")


def _without_register_row(register: str, path: str) -> str:
    """Return the register text with the vendored row naming ``path`` removed.

    Args:
        register: The register's text.
        path: The vendored path whose row is dropped.

    Returns:
        The mutated text.
    """
    kept = [
        line
        for line in register.split("\n")
        if not (line.startswith("|") and f"`{path}`" in line.split("|")[1])
    ]
    return "\n".join(kept)


def _only(grade: Mapping[str, Sequence[str]], check: str) -> list[str]:
    """Return the findings of ``check``, asserting every other check is green.

    Args:
        grade: The output of :func:`_grade`.
        check: The one check expected to carry findings.

    Returns:
        That check's findings.
    """
    others = {name: list(found) for name, found in grade.items() if name != check and found}
    assert others == {}, f"checks other than {check!r} went red: {others}"
    return list(grade[check])


# --- the grammar, graded on synthetic manifests -------------------------------------------------

WELL_FORMED = (
    b"# path\tclass\titem\tbasis - synthetic\n"
    b"a.py\tauthored\tCS-1\tstamped\n"
    b"b/c.py\tvendored\tCS-22\tfirst-add:CS-22\n"
    b"b/d.py\tauthored\tCS-1165\tfirst-add:root\n"
)

MALFORMED = {
    "crlf": WELL_FORMED.replace(b"\n", b"\r\n"),
    "non-ascii": WELL_FORMED.replace(b"a.py", b"\xc3\xa9.py"),
    "no final newline": WELL_FORMED[:-1],
    "no header": WELL_FORMED.split(b"\n", 1)[1],
    "empty": b"",
    "three columns": WELL_FORMED.replace(b"\tstamped\n", b"\n"),
    "five columns": WELL_FORMED.replace(b"\tstamped\n", b"\tstamped\textra\n"),
    "unknown class": WELL_FORMED.replace(b"\tauthored\tCS-1\t", b"\tforked\tCS-1\t"),
    "bad item": WELL_FORMED.replace(b"\tCS-1\t", b"\tCS1\t"),
    "bad basis": WELL_FORMED.replace(b"\tstamped\n", b"\tguessed\n"),
    "duplicate path": WELL_FORMED + b"b/d.py\tauthored\tCS-1\tstamped\n",
    "unsorted": WELL_FORMED + b"a0.py\tauthored\tCS-1\tstamped\n",
    "blank line": WELL_FORMED + b"\n",
    "second comment": WELL_FORMED + b"# another\n",
    "empty path": WELL_FORMED + b"\tauthored\tCS-1\tstamped\n",
}


def test_the_grammar_accepts_a_well_formed_manifest() -> None:
    rows, faults = _parse_manifest(WELL_FORMED)
    assert faults == []
    assert rows == {
        "a.py": Row("authored", "CS-1", "stamped"),
        "b/c.py": Row("vendored", "CS-22", "first-add:CS-22"),
        "b/d.py": Row("authored", "CS-1165", "first-add:root"),
    }


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_the_grammar_refuses_each_malformation(name: str) -> None:
    mutant = MALFORMED[name]
    assert mutant != WELL_FORMED, f"the {name!r} mutation never applied"
    _rows, faults = _parse_manifest(mutant)
    assert faults != [], f"the {name!r} malformation parsed clean"


def test_render_round_trips_through_the_grammar() -> None:
    rows, _faults = _parse_manifest(WELL_FORMED)
    rendered = _render(rows)
    assert _parse_manifest(rendered) == (rows, [])
    assert rendered.startswith(HEADER_PREFIX.encode("ascii"))


def test_an_unrepresentable_path_is_named() -> None:
    accented = "caf" + chr(0xE9) + ".py"
    assert _unrepresentable(["ok.py", "tab\there.py", accented, "nl\nx.py"]) == [
        accented,
        "nl\nx.py",
        "tab\there.py",
    ]


def test_an_uncited_item_is_named() -> None:
    rows = {"a.py": Row("authored", "CS-999999", "stamped")}
    files = {"a.py": b"x = 1\n"}
    grade = _grade(files, ["a.py"], _render(rows), _register_text(), "CS-1 and CS-9999990")
    assert grade["uncited"] == ["a.py (CS-999999)"]
    rows["a.py"] = Row("authored", "CS-1", "stamped")
    grade = _grade(files, ["a.py"], _render(rows), _register_text(), "CS-1 and CS-9999990")
    assert grade["uncited"] == [], "the control id on record was still reported"


def test_a_block_name_is_not_a_citation_of_its_prefix() -> None:
    # The record spells a block of ids, `CS-9nn`, and never the id CS-9 itself. A
    # lookahead that refuses only a following digit read CS-9 out of it, so a row
    # citing an item that does not exist went green (measured on the S3 bootstrap).
    rows = {"a.py": Row("authored", "CS-9", "stamped")}
    files = {"a.py": b"x = 1\n"}
    record = "the CS-9nn block, and CS-900 filed in it"
    grade = _grade(files, ["a.py"], _render(rows), _register_text(), record)
    assert grade["uncited"] == ["a.py (CS-9)"]
    rows["a.py"] = Row("authored", "CS-900", "stamped")
    grade = _grade(files, ["a.py"], _render(rows), _register_text(), record)
    assert grade["uncited"] == [], "the control id on record was still reported"


def test_a_missing_manifest_is_red_naming_the_manifest_and_the_tool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(f"{__name__}.MANIFEST", tmp_path / "absent.tsv")
    with pytest.raises(AssertionError) as caught:
        _real_manifest()
    assert MANIFEST_RELATIVE in str(caught.value)
    assert STAMP_TOOL in str(caught.value)


# --- the metric ---------------------------------------------------------------------------------


def test_the_metric_is_exact_and_directional() -> None:
    vendored = b"".join(f"line number {n:04d} of the vendored file\n".encode() for n in range(4))
    half = b"".join(f"line number {n:04d} of the vendored file\n".encode() for n in range(2))
    assert _overlap(vendored, vendored) == 1
    assert _overlap(half, vendored) == Fraction(1, 2)
    assert _overlap(vendored + b"short\n", half) == 1
    assert _overlap(b"\xff\xfe", vendored) is None
    assert _overlap(vendored, b"tiny\n") is None


# --- a throwaway git repository: the lister, the manifest file and M1/M2 on real git -------------


def _git(root: Path, *args: str) -> str:
    """Run git in the throwaway tree at ``root``, stripped of inherited GIT_ vars.

    Args:
        root: The throwaway work tree.
        *args: The git arguments.

    Returns:
        Its stdout.
    """
    done = subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=GIT_TIMEOUT,
        env=_git_env(),
    )
    return done.stdout.decode("utf-8")


def _stage(root: Path, rows: Mapping[str, Row]) -> None:
    """Write the manifest into the throwaway tree and stage everything.

    Args:
        root: The throwaway work tree.
        rows: The rows to write.
    """
    target = root / MANIFEST_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_render(rows))
    top = _git(root, "rev-parse", "--show-toplevel").strip()
    assert Path(top).samefile(root), f"git resolved {top}, not the throwaway tree"
    _git(root, "add", "-A")


@pytest.fixture
def synthetic_repo(tmp_path: Path) -> Path:
    """Return a throwaway repository holding the vendored files and two authored ones.

    Args:
        tmp_path: pytest's per-test directory.

    Returns:
        The work tree, every file staged, its manifest green.
    """
    root = tmp_path / "tree"
    root.mkdir()
    _git(root, "init", "-q")
    for name in _listed_paths(_register_text()):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / name, root / name)
    (root / "pkg").mkdir()
    (root / "pkg" / "alpha.py").write_bytes(b'"""Alpha, written for this synthetic tree."""\n')
    (root / "pkg" / "beta.md").write_bytes(b"# Beta\n\nA document written for this tree.\n")
    paths = [*_listed_paths(_register_text()), "pkg/alpha.py", "pkg/beta.md", MANIFEST_RELATIVE]
    _stage(root, _rows_for(paths, _listed_paths(_register_text())))
    return root


def _grade_repo(root: Path, threshold: Fraction = THRESHOLD) -> dict[str, list[str]]:
    """Grade a throwaway tree exactly as the real arms grade this one.

    Args:
        root: The throwaway work tree.
        threshold: The near-duplicate threshold.

    Returns:
        The findings of every check.
    """
    tracked = _candidate_paths(root, isolated=True)
    files = _read_population(root, tracked)
    manifest = (root / MANIFEST_RELATIVE).read_bytes()
    return _grade(files, tracked, manifest, _register_text(), _record_text(), threshold)


def test_the_synthetic_repo_is_green_pristine(synthetic_repo: Path) -> None:
    tracked = _candidate_paths(synthetic_repo, isolated=True)
    assert MANIFEST_RELATIVE in tracked
    assert LIFT_SOURCE in tracked
    assert {name: found for name, found in _grade_repo(synthetic_repo).items() if found} == {}


@pytest.mark.parametrize("staged", [False, True], ids=["plain-copy", "git-added"])
def test_m1_an_unlisted_copy_in_a_synthetic_repo_is_named(
    synthetic_repo: Path, staged: bool
) -> None:
    # THE ACCEPTANCE MUTATION, twice: a plain copy with nothing added anywhere
    # - not even to the index - and the same copy staged. Both are red.
    shutil.copyfile(synthetic_repo / LIFT_SOURCE, synthetic_repo / LIFT_TARGET)
    if staged:
        _git(synthetic_repo, "add", "--", LIFT_TARGET)
    indexed = _git(synthetic_repo, "ls-files", "--cached", "--", LIFT_TARGET).strip()
    assert (indexed == LIFT_TARGET) is staged, f"M1 landed with the wrong index state: {indexed!r}"
    assert LIFT_TARGET in _candidate_paths(synthetic_repo, isolated=True), "M1 never landed"
    assert (synthetic_repo / LIFT_TARGET).read_bytes() == (REPO_ROOT / LIFT_SOURCE).read_bytes()
    assert _only(_grade_repo(synthetic_repo), "unlisted") == [LIFT_TARGET]


def _plant_m2(root: Path) -> None:
    """Copy the lift source to the target and stamp it authored, in a throwaway tree.

    Args:
        root: The throwaway work tree.
    """
    shutil.copyfile(root / LIFT_SOURCE, root / LIFT_TARGET)
    rows, faults = _parse_manifest((root / MANIFEST_RELATIVE).read_bytes())
    assert faults == []
    rows[LIFT_TARGET] = Row("authored", SYNTHETIC_ITEM, "stamped")
    _stage(root, rows)
    landed, _faults = _parse_manifest((root / MANIFEST_RELATIVE).read_bytes())
    assert landed.get(LIFT_TARGET) == Row("authored", SYNTHETIC_ITEM, "stamped"), "M2 never landed"
    assert LIFT_TARGET in _candidate_paths(root, isolated=True), "M2 never landed"


def test_m2_a_copy_stamped_authored_in_a_synthetic_repo_is_named(synthetic_repo: Path) -> None:
    _plant_m2(synthetic_repo)
    found = _only(_grade_repo(synthetic_repo), "near_duplicate")
    assert found == [_identical_finding(LIFT_SOURCE, (REPO_ROOT / LIFT_SOURCE).read_bytes())]


def test_m2_survives_a_threshold_above_one_so_the_red_is_the_metric(
    synthetic_repo: Path,
) -> None:
    # SENSITIVITY CONTROL. The same planted tree, graded with a threshold no
    # score can reach, must come back fully green: the M2 red above is caused
    # by the metric crossing THRESHOLD, not by an arm that is red about anything.
    _plant_m2(synthetic_repo)
    assert {n: f for n, f in _grade_repo(synthetic_repo, UNREACHABLE).items() if f} == {}


def test_an_ignored_file_is_outside_the_population_and_an_unignored_one_is_in(
    synthetic_repo: Path,
) -> None:
    (synthetic_repo / "ignored").mkdir()
    (synthetic_repo / "ignored" / "scratch.txt").write_bytes(b"ignored\n")
    (synthetic_repo / "loose.txt").write_bytes(b"neither staged nor ignored\n")
    (synthetic_repo / ".git" / "info" / "exclude").write_bytes(b"ignored/\n")
    population = _candidate_paths(synthetic_repo, isolated=True)
    assert "ignored/scratch.txt" not in population
    assert "loose.txt" in population
    assert _only(_grade_repo(synthetic_repo), "unlisted") == ["loose.txt"]


# --- a population read from the real index, graded against a synthetic manifest ------------------


def _index_case() -> tuple[list[str], dict[str, bytes], dict[str, Row], str]:
    """Return the real index population with a synthetic manifest that is green over it.

    Returns:
        The tracked paths, their bytes, the synthetic rows and the register text.
    """
    tracked, files = _real_population()
    register = _register_text()
    assert LIFT_TARGET not in tracked, f"{LIFT_TARGET} is already tracked, so nothing can plant"
    return list(tracked), dict(files), _rows_for(tracked, _listed_paths(register)), register


def _grade_index(
    tracked: Sequence[str],
    files: Mapping[str, bytes],
    rows: Mapping[str, Row],
    register: str,
    threshold: Fraction = THRESHOLD,
) -> dict[str, list[str]]:
    """Grade an in-memory population.

    Args:
        tracked: The index paths.
        files: Their bytes.
        rows: The manifest rows.
        register: The register text.
        threshold: The near-duplicate threshold.

    Returns:
        The findings of every check.
    """
    return _grade(files, tracked, _render(rows), register, _record_text(), threshold)


def test_the_index_population_is_green_under_a_synthetic_manifest() -> None:
    tracked, files, rows, register = _index_case()
    assert {LIFT_SOURCE, SECOND_VENDORED} <= set(files)
    assert {n: f for n, f in _grade_index(tracked, files, rows, register).items() if f} == {}


def _mutant(name: str) -> tuple[list[str], dict[str, bytes], dict[str, Row], str]:
    """Return the index case with mutation ``name`` applied and asserted landed.

    Args:
        name: One of M1 to M5.

    Returns:
        The mutated tracked paths, bytes, rows and register text.
    """
    tracked, files, rows, register = _index_case()
    authored = Row("authored", SYNTHETIC_ITEM, "stamped")
    if name == "M5":
        mutated = _without_register_row(register, SECOND_VENDORED)
        assert SECOND_VENDORED not in _listed_paths(mutated), "M5 never landed"
        return tracked, files, rows, mutated
    source = SECOND_VENDORED if name == "M3" else LIFT_SOURCE
    planted = _debranded(files[source]) if name == "M4" else files[source]
    files[LIFT_TARGET] = planted
    tracked = sorted([*tracked, LIFT_TARGET], key=_path_key)
    if name != "M1":
        rows[LIFT_TARGET] = authored
    assert files[LIFT_TARGET] == planted, f"{name} never landed"
    assert LIFT_TARGET in tracked, f"{name} never landed"
    if name == "M4":
        header = files[source].split(b"\n", 2)[1]
        assert header.strip(), "the source has no header line to remove"
        assert header not in planted, "M4 kept the original header"
    return tracked, files, rows, register


MUTANTS = {
    "M1": ("unlisted", LIFT_TARGET),
    "M2": ("near_duplicate", f"{LIFT_TARGET} vs {LIFT_SOURCE} (overlap "),
    "M3": ("near_duplicate", f"{LIFT_TARGET} vs {SECOND_VENDORED} (overlap "),
    "M4": ("near_duplicate", f"{LIFT_TARGET} vs {LIFT_SOURCE} (overlap "),
    "M5": ("vendored", f"{SECOND_VENDORED} (vendored row, no register row)"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_of_the_index_population_is_named(name: str) -> None:
    check, expected = MUTANTS[name]
    found = _only(_grade_index(*_mutant(name)), check)
    assert len(found) == 1, f"{name} was not named alone: {found}"
    assert found[0].startswith(expected), f"{name} was not named: {found}"


def test_the_debranded_mutant_still_crosses_the_threshold_on_its_body() -> None:
    _tracked, files, _rows, _register = _mutant("M4")
    score = _overlap(files[LIFT_TARGET], files[LIFT_SOURCE])
    assert score is not None
    assert score >= THRESHOLD, f"M4 scored {score}"
    assert score < 1, "M4 kept the header, so it proves nothing a byte copy does not"


def test_m2_on_the_index_population_survives_a_threshold_above_one() -> None:
    assert {n: f for n, f in _grade_index(*_mutant("M2"), UNREACHABLE).items() if f} == {}


def _keeping(raw: bytes, keep: int) -> bytes:
    """Return ``raw`` with all but its first ``keep`` distinct long lines deleted.

    Short lines are kept, so only the metric's numerator moves. Every copy of
    a dropped line goes, so the kept count is exact.

    Args:
        raw: A vendored file's bytes.
        keep: How many distinct long lines, in first-occurrence order, survive.

    Returns:
        The trimmed file.
    """
    lines = raw.decode("utf-8").splitlines(keepends=True)
    order = list(dict.fromkeys(s.strip() for s in lines if len(s.strip()) >= LINE_FLOOR))
    kept = set(order[:keep])
    trimmed = [s for s in lines if len(s.strip()) < LINE_FLOOR or s.strip() in kept]
    return "".join(trimmed).encode("utf-8")


#: The boundary pair (CS-1165 adjudication, Q5): one distinct long line either
#: side of the threshold, plus the exact threshold, which is red because the
#: comparison is inclusive.
BOUNDARY = {"one-below": (-1, False), "exactly-at": (0, True), "one-above": (1, True)}


@pytest.mark.parametrize("name", sorted(BOUNDARY))
def test_the_threshold_sits_exactly_where_the_red_line_is(name: str) -> None:
    offset, red = BOUNDARY[name]
    tracked, files, rows, register = _index_case()
    distinct = _distinct_lines(files[LIFT_SOURCE])
    assert distinct is not None
    at = -(-len(distinct) * THRESHOLD.numerator // THRESHOLD.denominator)
    keep = at + offset
    planted = _keeping(files[LIFT_SOURCE], keep)
    landed = _overlap(planted, files[LIFT_SOURCE])
    assert landed == Fraction(keep, len(distinct)), f"{name} landed at {landed}, not {keep}"
    assert (landed >= THRESHOLD) is red, f"{name} sits on the wrong side: {landed}"
    files[LIFT_TARGET] = planted
    tracked = sorted([*tracked, LIFT_TARGET], key=_path_key)
    rows[LIFT_TARGET] = Row("authored", SYNTHETIC_ITEM, "stamped")
    found = _grade_index(tracked, files, rows, register)["near_duplicate"]
    expected = f"{LIFT_TARGET} vs {LIFT_SOURCE} (overlap {keep}/{len(distinct)})"
    assert found == ([expected] if red else [])


# --- the real tree ------------------------------------------------------------------------------


def test_no_tracked_path_is_unrepresentable() -> None:
    tracked, _files = _real_population()
    assert _unrepresentable(tracked) == [], "these tracked paths cannot be held by the manifest"


def test_the_current_tree_stays_far_below_the_threshold() -> None:
    # The margin, re-measured every run: no tracked file outside the register
    # may overlap a vendored file by even half the threshold. A creeping score
    # is loud here long before it flips the near-duplicate arm.
    _tracked, files = _real_population()
    vendored = _listed_paths(_register_text())
    scores = {
        (name, source): _overlap(files[name], files[source])
        for name in files
        if name not in vendored
        for source in vendored
    }
    worst = max((score for score in scores.values() if score is not None), default=Fraction(0))
    assert worst < THRESHOLD / MARGIN_DIVISOR, f"the tree's worst overlap is {worst}"


def test_the_real_manifest_parses() -> None:
    _rows, faults = _parse_manifest(_real_manifest())
    assert faults == [], f"{MANIFEST_RELATIVE} breaks its grammar: {faults}"


def test_every_tracked_path_has_a_manifest_row() -> None:
    # THE ACCEPTANCE ARM. A lift adds a file and nothing else, so it has no row.
    unlisted = _real_grade()["unlisted"]
    assert unlisted == [], (
        f"these tracked files have no row in {MANIFEST_RELATIVE}: {unlisted}. Classify each "
        f"with `python {STAMP_TOOL} add PATH --class authored|vendored --item CS-NNNN`."
    )


def test_every_manifest_row_names_a_tracked_path() -> None:
    stale = _real_grade()["stale"]
    assert stale == [], f"these rows name no tracked file: {stale}; `{STAMP_TOOL} rm|mv` them"


def test_the_vendored_rows_equal_the_register() -> None:
    mismatch = _real_grade()["vendored"]
    assert mismatch == [], f"the manifest and THIRD_PARTY.md disagree: {mismatch}"


def test_no_authored_row_is_a_near_duplicate_of_a_vendored_file() -> None:
    found = _real_grade()["near_duplicate"]
    assert found == [], f"these authored rows duplicate a vendored file: {found}"


def test_every_cited_item_is_on_record() -> None:
    # WEAK BY DESIGN: any real id passes. It catches a typo or an invented id,
    # not a false attribution.
    uncited = _real_grade()["uncited"]
    assert uncited == [], f"these rows cite an id on no record: {uncited}"


def test_the_real_manifest_reddens_on_m1_and_m2() -> None:
    # The mutation arm on the REAL manifest, in memory: nothing is written.
    tracked, files = _real_population()
    manifest = _real_manifest()
    rows, _faults = _parse_manifest(manifest)
    planted_files = {**files, LIFT_TARGET: files[LIFT_SOURCE]}
    planted_tracked = sorted([*tracked, LIFT_TARGET], key=_path_key)
    assert LIFT_TARGET not in tracked
    assert LIFT_TARGET not in rows
    args = (register := _register_text(), _record_text())
    m1 = _grade(planted_files, planted_tracked, manifest, *args)
    assert _only(m1, "unlisted") == [LIFT_TARGET]
    m2_rows = {**rows, LIFT_TARGET: Row("authored", SYNTHETIC_ITEM, "stamped")}
    m2 = _grade(planted_files, planted_tracked, _render(m2_rows), register, _record_text())
    assert _only(m2, "near_duplicate") == [_identical_finding(LIFT_SOURCE, files[LIFT_SOURCE])]
