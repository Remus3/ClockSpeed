"""CS-1165 - stamp rows into the whole-population provenance manifest.

WHAT THIS IS, AND WHAT IT IS NOT. ``tools/provenance.tsv`` accounts for every
file in this tree's population - tracked, staged, or untracked-but-not-ignored -
with a class (``authored`` or ``vendored``), a CS item id and a basis. This tool
is the ERGONOMIC way to write a row. It is NOT the oracle: the manifest arm
(the ``test_provenance_manifest`` module) re-derives every rule from the
manifest bytes, so a row written by hand, by another tool, or by a rebase
resolution is graded exactly as one written here. Nothing this tool accepts is
evidence of anything; everything it refuses would also be red in the arm.

THE MANIFEST FORMAT, owned by the plan section 2.1 and followed exactly:

    7-bit ASCII, LF line endings, one header comment line beginning ``# ``, then
    one row per path sorted by the path's bytes, TAB-separated, no quoting:

        path    class    item    basis

    class   ``authored`` or ``vendored``; nothing else parses
    item    ``CS-`` and digits, required on every row
    basis   ``stamped`` (written by add or mv), or ``first-add:CS-NNNN`` /
            ``first-add:root`` (written once by bootstrap)

    No digest column. Vendored bytes are pinned by their own test modules and a
    second digest here would be a restated fact.

THE ITEM ID IS TRACEABILITY, NOT EVIDENCE. Any real id can be cited, and this
tool checks only its SHAPE. A row saying ``authored`` with a plausible id is a
DECLARATION with a commit on it, visible in review - it is not proof that the
file was authored here. Authorship is not a property of bytes.

WHAT IS REFUSED, every one exit 2, and a refusal writes nothing:

    * a class that is not given - there is NO default, classification is always
      an explicit decision - or is not one of the closed pair
    * an item that is not ``CS-`` followed by digits, or that appears in
      neither ROADMAP.md nor docs/LEDGER.md (weak: any real id passes)
    * a path outside the population, already listed, not plain repo-relative
      POSIX, not 7-bit ASCII, carrying a TAB or a line break, or spelling this
      machine's home directory
    * ``vendored`` for a path with no row in the THIRD_PARTY.md vendored table
    * ``authored`` for a path that the register names vendored, or whose bytes
      equal a vendored file's (as-is or LF-normalised), or near-duplicate one:
      at least NEAR_DUPLICATE_THRESHOLD of the vendored file's distinct long
      lines appear in it (see :func:`overlap_score`)
    * any write over a manifest that does not parse - the tool never "repairs"
      a manifest by rewriting it

THERE IS NO BULK MODE, deliberately. ``add`` takes one path. ``bootstrap`` is
the only writer of many rows and it REFUSES when the manifest already exists, so
"regenerate everything" - which would stamp every unclassified new file in one
stroke - cannot be done through this tool at all.

A DELETED MANIFEST IS RESTORED, NEVER RE-SEEDED (CS-1176). ``bootstrap`` also
refuses whenever any commit reachable from ANY ref - HEAD, every branch, tag
and ``refs/remotes/*`` - holds the manifest, so neither a deletion (committed or
not) nor an orphan or squashed branch reopens the seed, and every
missing-manifest message points at ``git checkout <rev> -- tools/provenance.tsv``,
where ``<rev>`` is the newest commit holding one (HEAD's line first). It never
recommends the seed: re-deriving a deleted manifest would classify every
unstamped file, a lift included, as authored. The arm grades a re-seed made
around this refusal separately.

NAMED RESIDUAL, for an adjudicator to rule on: a rewrite that ALSO deletes
every ref reaching a manifest - every branch, tag and remote-tracking ref - and
so leaves only the reflog (not searched) looks exactly like a history that never
held one, and is seeded as a first seed would be. So is a branch cut before the
manifest existed in a clone that holds no ref to the manifest at all.

CLI (``--root`` defaults to this repository; exit 0 done, 1 check found
something, 2 refused or bad usage)::

    python tools/provenance_stamp.py add PATH --class authored|vendored --item CS-NNNN
    python tools/provenance_stamp.py mv OLD NEW
    python tools/provenance_stamp.py rm PATH
    python tools/provenance_stamp.py check
    python tools/provenance_stamp.py bootstrap

Every write is atomic: a sibling temp file, then a rename retried on Windows,
and the temp file is removed on any failure. Messages name repo-relative paths
and overlap scores only - never file bytes and never the absolute root.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Sequence
from fractions import Fraction
from pathlib import Path

# `tools` carries no __init__.py, so the sibling resolver is imported under its
# BARE name, the way tools/tier1_growth.py does it.
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from toolpath import resolve_tool  # noqa: E402

REPO_ROOT = _TOOLS_DIR.parent

MANIFEST_RELATIVE = "tools/provenance.tsv"
REGISTER_RELATIVE = "THIRD_PARTY.md"
TOOL_RELATIVE = "tools/provenance_stamp.py"

#: The heading that opens the register's machine-graded table of vendored
#: files. The register's other tables name items merely considered.
VENDORED_HEADING = "### Vendored files"

#: Header and separator rows of a markdown table.
TABLE_PREAMBLE_ROWS = 2

BACKTICK_RE = re.compile(r"`([^`\n]+)`")

HEADER = (
    "# tools/provenance.tsv - path, class, item, basis; TAB-separated, sorted by path"
    " bytes; written by tools/provenance_stamp.py (CS-1165)"
)

CLASSES = ("authored", "vendored")
ITEM_RE = re.compile(r"CS-[0-9]+")
BASIS_RE = re.compile(r"stamped|first-add:(?:root|CS-[0-9]+)")
#: How an item id is recognised inside prose - a commit subject, ROADMAP.md,
#: docs/LEDGER.md. The same boundaries the arm uses, so "CS-12" never matches
#: inside "CS-123" and "XCS-1" is not an id.
CITED_RE = re.compile(r"(?<![A-Za-z0-9])CS-[0-9]+(?![0-9A-Za-z])")

#: The files an item id must appear in. OPEN work lives in the first and
#: CLOSED work in the second, so a real id is in one of them. This is weak -
#: any real id passes - and it is here so the tool never writes a row the arm
#: would redden, not because it proves anything.
RECORD_FILES = ("ROADMAP.md", "docs/LEDGER.md")
STAMPED = "stamped"

#: The id a bootstrap row cites when its first-add subject carries none, and
#: the id the manifest's own row cites. This item introduced the manifest.
BOOTSTRAP_ITEM = "CS-1165"

#: THE NEAR-DUPLICATE LINE. A score of one half means half of a vendored file's
#: distinct long lines reappear in the candidate. Measured on the tree this was
#: written against, the worst authored-versus-vendored score was 0.064, so the
#: line sits far from every honest file while a lift that kept most of its body
#: under a rewritten header scores well above it.
NEAR_DUPLICATE_THRESHOLD = Fraction(1, 2)

#: Lines shorter than this carry no identity - blank lines, brackets, ``else:``,
#: ``return None`` - and would make any two files in one language overlap.
MIN_LINE_LENGTH = 20

#: How long any one git child may take. Bounded so a hung child is a named
#: failure rather than a stalled caller.
SUBPROCESS_TIMEOUT_SECONDS = 120

#: Variables that point a git child at a repository, index or configuration
#: its caller never named. A pre-push hook exports GIT_DIR, so a tool run from
#: one would otherwise answer about the wrong tree whatever ``-C`` says.
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
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    }
)
_GIT_RELOCATING_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")

SUBCOMMANDS = ("add", "mv", "rm", "check", "bootstrap")

Row = tuple[str, str, str, str]
ROW_FIELDS = 4


class RefusalError(Exception):
    """A request this tool will not carry out. Nothing has been written.

    Every raise site builds its message from repo-relative paths, ids and scores
    only; it is carried as :attr:`reason` so the CLI renders that field, not the
    exception object.
    """

    def __init__(self, reason: str) -> None:
        """Keep ``reason`` as the one field the CLI prints."""
        super().__init__(reason)
        self.reason = reason


# --- git ------------------------------------------------------------------


def _child_env() -> dict[str, str]:
    """Return a copy of the environment with every git relocating variable removed."""
    env = dict(os.environ)
    for name in list(env):
        folded = name.upper()
        if folded in _GIT_RELOCATING or folded.startswith(_GIT_RELOCATING_PREFIXES):
            del env[name]
    return env


def _git(root: Path, *args: str) -> str:
    """Run git against ``root`` and return its stdout.

    Raises:
        RefusalError: git is absent or the command failed.
    """
    git = resolve_tool("git")
    if git is None:
        message = "git is not on PATH; the population cannot be read"
        raise RefusalError(message)
    completed = subprocess.run(
        [git, "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        env=_child_env(),
    )
    if completed.returncode != 0:
        message = f"git {args[0]} failed with exit {completed.returncode}"
        raise RefusalError(message)
    return completed.stdout


def _git_succeeds(root: Path, *args: str) -> bool:
    """Run git against ``root`` and return whether it exited 0; stdout is discarded.

    Raises:
        RefusalError: git is absent.
    """
    git = resolve_tool("git")
    if git is None:
        message = "git is not on PATH; the history cannot be read"
        raise RefusalError(message)
    completed = subprocess.run(
        [git, "-C", str(root), *args],
        capture_output=True,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        env=_child_env(),
    )
    return completed.returncode == 0


def last_committed_manifest(root: Path) -> str | None:
    """Return the full SHA of the newest commit holding the manifest on ANY ref.

    HEAD's own history is searched first, so the restore it names is on the
    line being worked; then every ref - branches, tags and ``refs/remotes/*``
    (CS-1176 F4) - so an orphan or squashed branch cut away from the manifest
    does not reopen the seed while any ref still reaches one. Both walks keep
    ``--full-history``, so no side of a merge is simplified away. A commit that
    deleted it is skipped, so the answer is always a commit a
    ``git checkout <rev> -- tools/provenance.tsv`` can restore from. None when
    no ref reaches a commit that holds one.
    """
    if not _git(root, "for-each-ref", "--count=1").strip():
        return None
    scopes = [["--all"]]
    if _git_succeeds(root, "rev-parse", "--verify", "-q", "HEAD"):
        scopes.insert(0, ["HEAD"])
    for scope in scopes:
        listing = _git(
            root, "log", *scope, "--full-history", "--format=%H", "--", MANIFEST_RELATIVE
        )
        for rev in listing.split():
            if _git_succeeds(root, "cat-file", "-e", f"{rev}:{MANIFEST_RELATIVE}"):
                return rev
    return None


def restore_advice(root: Path) -> str:
    """Return what to do about a missing manifest. It never recommends the seed."""
    rev = last_committed_manifest(root)
    if rev is None:
        return (
            "no commit on this history holds one; restore it from a full-history clone,"
            " never re-derive it (CS-1176)"
        )
    return (
        f"restore the committed manifest with `git checkout {rev} -- {MANIFEST_RELATIVE}`;"
        " never re-derive it, which would classify every unstamped file as authored (CS-1176)"
    )


def _nul_split(text: str) -> set[str]:
    return {entry for entry in text.split("\0") if entry}


def population(root: Path) -> set[str]:
    """Return tracked, staged and untracked-not-ignored paths.

    The same population the arm grades: a plain copy with no ``git add`` is
    the acceptance mutation, so an index-only population would be blind to it.
    """
    return _nul_split(_git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"))


# --- paths ----------------------------------------------------------------


def _home_markers() -> tuple[str, ...]:
    """Return lower-cased POSIX spellings of this machine's home directory.

    Both the full spelling and the drive-less tail are returned, so a
    repo-relative path that embeds ``users/<account>`` is caught as well as
    one embedding the whole absolute path.
    """
    home = Path.home().as_posix().lower().rstrip("/")
    tail = re.sub(r"^[a-z]:", "", home).lstrip("/")
    return tuple(marker for marker in (home, tail) if len(marker) >= len("x/y"))


def normalise(raw: str) -> str:
    """Return ``raw`` as a plain repo-relative POSIX path.

    Raises:
        RefusalError: the path is absolute, escapes, is not 7-bit ASCII,
            carries a TAB or line break, or spells the home directory.
    """
    path = raw.replace("\\", "/")
    if not path or not path.isascii() or any(ch in path for ch in "\t\r\n\0"):
        message = f"not a plain 7-bit repo-relative path: {path!r}"
        raise RefusalError(message)
    if path.startswith("/") or re.match(r"[A-Za-z]:", path):
        message = f"an absolute path is never written into the manifest: {path!r}"
        raise RefusalError(message)
    if any(part in {"", ".", ".."} for part in path.split("/")):
        message = f"a path with an empty, '.' or '..' part is not repo-relative: {path!r}"
        raise RefusalError(message)
    lowered = path.lower()
    if any(marker in lowered for marker in _home_markers()):
        message = "the path spells this machine's home directory; it is never written"
        raise RefusalError(message)
    return path


# --- the register ---------------------------------------------------------


def register_vendored(root: Path) -> set[str]:
    """Return every path the THIRD_PARTY.md vendored table names.

    Raises:
        RefusalError: the register or its vendored table cannot be read.
    """
    register = root / REGISTER_RELATIVE
    if not register.is_file():
        message = f"{REGISTER_RELATIVE} is absent; the vendored set cannot be read"
        raise RefusalError(message)
    text = register.read_bytes().decode("utf-8", "replace")
    lines = text.splitlines()
    if VENDORED_HEADING not in lines:
        message = f"{REGISTER_RELATIVE} carries no {VENDORED_HEADING!r} section"
        raise RefusalError(message)
    rows: list[str] = []
    for line in lines[lines.index(VENDORED_HEADING) + 1 :]:
        if line.startswith("|"):
            rows.append(line)
        elif rows:
            break
    listed: set[str] = set()
    for row in rows[TABLE_PREAMBLE_ROWS:]:
        first = row.strip().strip("|").split("|")[0]
        quoted = BACKTICK_RE.findall(first)
        if not quoted:
            message = f"a {REGISTER_RELATIVE} vendored row names no backticked file"
            raise RefusalError(message)
        listed.add(quoted[0])
    return listed


# --- the near-duplicate metric ---------------------------------------------


def _long_lines(data: bytes) -> set[str] | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    stripped = (line.strip() for line in text.splitlines())
    return {line for line in stripped if len(line) >= MIN_LINE_LENGTH}


def overlap_score(candidate: bytes, vendored: bytes) -> Fraction:
    """Return the share of ``vendored``'s distinct long lines found in ``candidate``.

    L(f) is the set of stripped lines of at least MIN_LINE_LENGTH characters of
    ``f`` decoded as UTF-8. The score is ``|L(candidate) & L(vendored)|`` over
    ``|L(vendored)|``, exact. An undecodable file, or a vendored file with no
    long line, scores zero here and is graded by byte equality alone.
    """
    theirs = _long_lines(vendored)
    ours = _long_lines(candidate)
    if not theirs or ours is None:
        return Fraction(0)
    return Fraction(len(ours & theirs), len(theirs))


def _same_bytes(left: bytes, right: bytes) -> bool:
    return left == right or left.replace(b"\r\n", b"\n") == right.replace(b"\r\n", b"\n")


def authored_objection(root: Path, path: str, vendored: Iterable[str]) -> str | None:
    """Return why ``path`` may not be declared authored, or None.

    Args:
        root: The repository root.
        path: The repo-relative candidate.
        vendored: Every path held vendored, by the register or the manifest.
    """
    vendored = sorted(set(vendored))
    if path in vendored:
        return f"{path} is vendored by the register or the manifest, not authored here"
    candidate_file = root / path
    if not candidate_file.is_file():
        return f"{path} is not a file on disk, so its bytes cannot be graded"
    candidate = candidate_file.read_bytes()
    for other in vendored:
        other_file = root / other
        if not other_file.is_file():
            return f"the vendored file {other} is not on disk, so {path} cannot be graded"
        theirs = other_file.read_bytes()
        score = Fraction(1) if _same_bytes(candidate, theirs) else overlap_score(candidate, theirs)
        if score >= NEAR_DUPLICATE_THRESHOLD:
            return (
                f"{path} matches the vendored file {other} at overlap {float(score):.3f}"
                f" (threshold {float(NEAR_DUPLICATE_THRESHOLD):.3f})"
            )
    return None


# --- the manifest ---------------------------------------------------------


def parse(data: bytes) -> list[Row]:
    """Parse manifest bytes, strictly.

    Raises:
        RefusalError: the bytes break any rule of the format.
    """
    if not data.isascii():
        message = f"{MANIFEST_RELATIVE} is not 7-bit ASCII"
        raise RefusalError(message)
    if b"\r" in data:
        message = f"{MANIFEST_RELATIVE} carries a CR; it must be LF only"
        raise RefusalError(message)
    if not data.endswith(b"\n"):
        message = f"{MANIFEST_RELATIVE} does not end with a line feed"
        raise RefusalError(message)
    lines = data.decode("ascii").split("\n")[:-1]
    if not lines or not lines[0].startswith("# "):
        message = f"{MANIFEST_RELATIVE} does not open with its header comment line"
        raise RefusalError(message)
    rows: list[Row] = []
    for number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        if len(fields) != ROW_FIELDS:
            message = f"{MANIFEST_RELATIVE} line {number} does not carry four TAB-separated fields"
            raise RefusalError(message)
        path, klass, item, basis = fields
        if normalise(path) != path:
            message = f"{MANIFEST_RELATIVE} line {number} names a path not in POSIX form"
            raise RefusalError(message)
        if klass not in CLASSES:
            message = f"{MANIFEST_RELATIVE} line {number} carries a class outside {CLASSES}"
            raise RefusalError(message)
        if not ITEM_RE.fullmatch(item):
            message = f"{MANIFEST_RELATIVE} line {number} carries an item that is not CS-NNNN"
            raise RefusalError(message)
        if not BASIS_RE.fullmatch(basis):
            message = f"{MANIFEST_RELATIVE} line {number} carries an unknown basis"
            raise RefusalError(message)
        if rows and rows[-1][0].encode() >= path.encode():
            message = f"{MANIFEST_RELATIVE} line {number} is out of order or repeats a path"
            raise RefusalError(message)
        rows.append((path, klass, item, basis))
    return rows


def serialise(rows: Iterable[Row]) -> bytes:
    """Return the canonical manifest bytes: header, rows sorted by path bytes, LF."""
    ordered = sorted(rows, key=lambda row: row[0].encode())
    body = "".join("\t".join(row) + "\n" for row in ordered)
    return (HEADER + "\n" + body).encode("ascii")


def _load(root: Path, *, required: bool) -> list[Row]:
    manifest = root / MANIFEST_RELATIVE
    if not manifest.is_file():
        if required:
            message = f"{MANIFEST_RELATIVE} is absent; {restore_advice(root)}"
            raise RefusalError(message)
        return []
    return parse(manifest.read_bytes())


def atomic_write(target: Path, data: bytes) -> None:
    """Write ``data`` via a sibling temp file and a rename retried on Windows.

    The temp file is removed on every path that does not rename it into place,
    so a failed write leaves the old manifest and nothing beside it.

    Raises:
        PermissionError: the rename kept failing.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed below, before the rename
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
    )
    staging = Path(handle.name)
    try:
        with handle:
            handle.write(data)
        for attempt in range(4):
            try:
                staging.replace(target)
            except PermissionError:
                time.sleep(0.05 * (attempt + 1))
            else:
                return
        # The fifth attempt is unguarded, so a persistent refusal propagates as itself.
        staging.replace(target)
    finally:
        with contextlib.suppress(FileNotFoundError):
            staging.unlink()


# --- the subcommands ------------------------------------------------------


def _check_class(root: Path, path: str, klass: str, rows: Sequence[Row]) -> None:
    registered = register_vendored(root)
    if klass == "vendored":
        if path not in registered:
            message = f"{path} has no row in the {REGISTER_RELATIVE} vendored table"
            raise RefusalError(message)
        return
    held = registered | {row[0] for row in rows if row[1] == "vendored"}
    objection = authored_objection(root, path, held)
    if objection is not None:
        raise RefusalError(objection)


def recorded_items(root: Path) -> set[str]:
    """Return every item id spelled in ROADMAP.md or docs/LEDGER.md."""
    cited: set[str] = set()
    for relative in RECORD_FILES:
        record = root / relative
        if record.is_file():
            cited |= set(CITED_RE.findall(record.read_bytes().decode("utf-8", "replace")))
    return cited


def _check_item(root: Path, item: str) -> None:
    if not ITEM_RE.fullmatch(item):
        message = f"the item must be CS- followed by digits, got {item!r}"
        raise RefusalError(message)
    if item not in recorded_items(root):
        message = f"{item} appears in neither {' nor '.join(RECORD_FILES)}"
        raise RefusalError(message)


def cmd_add(root: Path, raw_path: str, klass: str, item: str) -> str:
    """Stamp one path. Returns the confirmation line."""
    path = normalise(raw_path)
    _check_item(root, item)
    rows = _load(root, required=False)
    if any(row[0] == path for row in rows):
        message = f"{path} is already listed; use mv or rm, never a second add"
        raise RefusalError(message)
    if path not in population(root):
        message = f"{path} is not tracked, staged, or untracked-and-unignored"
        raise RefusalError(message)
    _check_class(root, path, klass, rows)
    atomic_write(root / MANIFEST_RELATIVE, serialise([*rows, (path, klass, item, STAMPED)]))
    return f"STAMPED: {path} {klass} {item}"


def cmd_mv(root: Path, raw_old: str, raw_new: str) -> str:
    """Move one row to a new path, keeping class and item."""
    old, new = normalise(raw_old), normalise(raw_new)
    rows = _load(root, required=True)
    found = [row for row in rows if row[0] == old]
    if not found:
        message = f"{old} is not listed"
        raise RefusalError(message)
    if any(row[0] == new for row in rows):
        message = f"{new} is already listed"
        raise RefusalError(message)
    present = population(root)
    if old in present:
        message = f"{old} is still in the population; a copy is an add, not a mv"
        raise RefusalError(message)
    if new not in present:
        message = f"{new} is not tracked, staged, or untracked-and-unignored"
        raise RefusalError(message)
    _, klass, item, _ = found[0]
    rest = [row for row in rows if row[0] != old]
    _check_class(root, new, klass, rest)
    atomic_write(root / MANIFEST_RELATIVE, serialise([*rest, (new, klass, item, STAMPED)]))
    return f"MOVED: {old} -> {new} {klass} {item}"


def cmd_rm(root: Path, raw_path: str) -> str:
    """Drop the row of a path that has left the population."""
    path = normalise(raw_path)
    rows = _load(root, required=True)
    if not any(row[0] == path for row in rows):
        message = f"{path} is not listed"
        raise RefusalError(message)
    if path in population(root):
        message = f"{path} is still in the population; remove the file first"
        raise RefusalError(message)
    atomic_write(root / MANIFEST_RELATIVE, serialise(row for row in rows if row[0] != path))
    return f"REMOVED: {path}"


def findings(root: Path, rows: Sequence[Row]) -> list[str]:
    """Return every way the manifest disagrees with the tree, sorted."""
    present = population(root)
    listed = {row[0] for row in rows}
    registered = register_vendored(root)
    vendored_rows = {row[0] for row in rows if row[1] == "vendored"}
    found = [f"UNLISTED: {path}" for path in sorted(present - listed, key=str.encode)]
    found += [f"STALE: {path}" for path in sorted(listed - present, key=str.encode)]
    found += [f"UNREGISTERED VENDORED ROW: {path}" for path in sorted(vendored_rows - registered)]
    found += [f"REGISTER ROW NOT VENDORED: {path}" for path in sorted(registered - vendored_rows)]
    recorded = recorded_items(root)
    found += [f"UNRECORDED ITEM: {row[0]} cites {row[2]}" for row in rows if row[2] not in recorded]
    held = registered | vendored_rows
    for path, klass, _, _ in rows:
        if klass == "authored" and path in present and path not in held:
            objection = authored_objection(root, path, held)
            if objection is not None:
                found.append(f"NEAR-DUPLICATE: {objection}")
    return found


def cmd_check(root: Path) -> tuple[int, list[str]]:
    """Grade the manifest against the tree. Exit 1 if anything disagrees."""
    manifest = root / MANIFEST_RELATIVE
    if not manifest.is_file():
        return 1, [f"FAIL: {MANIFEST_RELATIVE} is absent; {restore_advice(root)}"]
    rows = parse(manifest.read_bytes())
    found = findings(root, rows)
    if found:
        return 1, [*found, f"FAIL: {len(found)} finding(s) in {MANIFEST_RELATIVE}"]
    return 0, [f"PASS: {len(rows)} row(s) in {MANIFEST_RELATIVE}, every path accounted for"]


def first_adds(root: Path) -> dict[str, str]:
    """Return each path mapped to the subject of the OLDEST commit that added it."""
    out = _git(
        root,
        "-c",
        "core.quotepath=off",
        "log",
        "--reverse",
        "--diff-filter=A",
        "--no-renames",
        "--name-only",
        "--format=%x01%s",
    )
    adds: dict[str, str] = {}
    subject = ""
    for line in out.splitlines():
        if line.startswith("\x01"):
            subject = line[1:]
        elif line:
            adds.setdefault(line, subject)
    return adds


def cmd_bootstrap(root: Path) -> str:
    """Seed the manifest once, from full history.

    Refuses if it exists, and refuses if any commit on HEAD's history ever held
    it (CS-1176): a deleted manifest is restored from that commit, never
    re-derived, because a re-derivation classifies every unstamped file as
    authored.
    """
    if (root / MANIFEST_RELATIVE).exists():
        message = f"{MANIFEST_RELATIVE} exists; bootstrap never overwrites it - use add"
        raise RefusalError(message)
    if _git(root, "rev-parse", "--is-shallow-repository").strip() != "false":
        message = "this is a shallow clone; bootstrap needs the full history"
        raise RefusalError(message)
    if last_committed_manifest(root) is not None:
        message = (
            f"{MANIFEST_RELATIVE} is held by this history, so bootstrap never re-derives it;"
            f" {restore_advice(root)}"
        )
        raise RefusalError(message)
    registered = register_vendored(root)
    present = population(root) - {MANIFEST_RELATIVE}
    for path in sorted(present):
        normalise(path)
    missing = sorted(registered - present)
    if missing:
        message = f"the register names {missing[0]}, which is not in the population"
        raise RefusalError(message)
    adds = first_adds(root)
    _check_item(root, BOOTSTRAP_ITEM)
    recorded = recorded_items(root)
    rows: list[Row] = [(MANIFEST_RELATIVE, "authored", BOOTSTRAP_ITEM, STAMPED)]
    for path in sorted(present, key=str.encode):
        if path not in adds:
            message = f"{path} has no first-add commit; commit it, or stamp it with add"
            raise RefusalError(message)
        cited = CITED_RE.search(adds[path])
        item, basis = (
            (cited.group(0), f"first-add:{cited.group(0)}")
            if cited
            else (BOOTSTRAP_ITEM, "first-add:root")
        )
        if item not in recorded:
            message = (
                f"{path} first-add cites {item}, which appears in neither"
                f" {' nor '.join(RECORD_FILES)}"
            )
            raise RefusalError(message)
        klass = "vendored" if path in registered else "authored"
        if klass == "authored":
            objection = authored_objection(root, path, registered)
            if objection is not None:
                raise RefusalError(objection)
        rows.append((path, klass, item, basis))
    atomic_write(root / MANIFEST_RELATIVE, serialise(rows))
    return f"BOOTSTRAPPED: {len(rows)} row(s) in {MANIFEST_RELATIVE}"


# --- the CLI --------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_RELATIVE, description="Stamp rows into tools/provenance.tsv (CS-1165)."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="stamp one path with an explicit class and item")
    add.add_argument("path")
    add.add_argument("--class", dest="klass", required=True, choices=CLASSES)
    add.add_argument("--item", required=True)
    move = sub.add_parser("mv", help="move one row to a renamed path")
    move.add_argument("old")
    move.add_argument("new")
    remove = sub.add_parser("rm", help="drop the row of a path that has left the tree")
    remove.add_argument("path")
    sub.add_parser("check", help="print unlisted and stale paths; exit 1 if any")
    sub.add_parser(
        "bootstrap", help="seed the manifest once; refuses if it exists or history holds one"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand. Returns 0 done, 1 check found something, 2 refused."""
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    root: Path = args.root.resolve()
    try:
        if args.command == "check":
            code, lines = cmd_check(root)
            for line in lines:
                print(line)
            return code
        if args.command == "add":
            said = cmd_add(root, args.path, args.klass, args.item)
        elif args.command == "mv":
            said = cmd_mv(root, args.old, args.new)
        elif args.command == "rm":
            said = cmd_rm(root, args.path)
        else:
            said = cmd_bootstrap(root)
    except RefusalError as refusal:
        print(f"REFUSED: {refusal.reason}", file=sys.stderr)
        return 2
    print(said)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
