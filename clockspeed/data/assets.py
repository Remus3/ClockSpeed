"""The queryable index over the game's shipped C++ headers.

WHY THIS MODULE EXISTS. Until CS-1040 every "is this field in the save"
question in this project was answered by SAMPLING: grep a save, count the hits,
conclude from an absence. ADR 0003 had to settle for exactly that about node
purity, and an absence measured by sampling is the weakest evidence this
project accepts - it cannot distinguish "the game never writes it" from "this
world happens not to carry it".

The install ships ``CommunityResources/Headers.zip`` beside the ``Docs`` file
``clockspeed/data/docs_extract.py`` already reads: publisher-authored C++
headers for the whole game, a plain deflate archive needing nothing but the
standard library. Unreal serializes a property into a save if and only if its
``UPROPERTY`` macro carries the ``SaveGame`` specifier, so those headers turn
the question into a LOOKUP with a DECLARATION-grade answer. One query would
have answered ADR 0003 outright. ADR 0020 records what each of purity, building
extent, the map underlay and water geometry turned out to be, and this module
is the instrument those verdicts were read from.

THE ANSWER IS THREE-VALUED AND THAT IS THE LOAD-BEARING PART. ``True`` the
headers declare it with ``SaveGame``; ``False`` they declare it without;
``None`` they do not declare it at all. Collapsing ``None`` into ``False``
would make this module answer confidently about unknown game content, which
non-negotiable 7 forbids and which is precisely the failure a grep already
commits.

WHAT THIS MODULE NEVER DOES
---------------------------
- It never writes to the game install (non-negotiable 1). The archive is opened
  read-only and no path under the install is ever passed to a writing call.
- It never commits what it extracts (non-negotiable 2). The generated index
  lands under the repository's gitignored ``data/`` directory and nowhere else.
- It never echoes a header's text into an error message or a log line.
  Diagnostics carry archive-relative entry names and counts only.
- It never decides where the install is. ``clockspeed/data/locate.py`` owns
  that, and every parsing entry point here takes a ``Path`` or a ``str`` so the
  grammar can be exercised with no game installed at all. Only
  :func:`extract_header_index`, the end-to-end convenience path, resolves - and
  it reports a missing install as a reason rather than raising, so the whole
  suite runs on a machine with no game.

THE RESIDUAL, RECORDED RATHER THAN CHASED. Four properties in the pinned build
resolve to an EMPTY owner, all four in one deprecated plugin class whose name
is separated from the ``class`` keyword by a ``UE_DEPRECATED( ... )`` macro.
None of the four carries ``SaveGame``. The empty string is honest - it is not a
wrong type name - and the obvious widening, accepting anything between the
keyword and the body, would make a forward declaration an owner, which is a
worse fault than the one it repairs. An owner-side gap costs a query that names
a type; a false owner would answer one wrongly.

WHY THE SPECIFIER LIST IS SPLIT AT PAREN DEPTH ZERO. Real specifier lists carry
``meta = ( ... )`` groups whose commas are not separators. A naive split on
every comma shreds those into fragments, and a fragment named ``SaveGame``
cannot occur - so the damage is silent: the shredded entry simply never matches
anything a caller asks for.
"""

from __future__ import annotations

import json
import re
import time
import zipfile
from collections.abc import Sized
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from clockspeed.data import locate

# --- where things are -------------------------------------------------------

#: The archive's location under the install root, as path parts. Joined onto a
#: resolved install directory by :func:`headers_archive_path`; never spelled as
#: an absolute path anywhere, because no absolute path on this machine may be
#: written into a tracked file (non-negotiable 3).
HEADERS_ARCHIVE_PARTS: Final[tuple[str, ...]] = ("CommunityResources", "Headers.zip")

#: Where the generated index lands, relative to the repository root. The
#: leading part is the GITIGNORED generated-artifact directory and must stay
#: distinct from the tracked ``clockspeed/data/`` source package - see the
#: anchoring note in ``.gitignore``.
ARTIFACT_PARTS: Final[tuple[str, ...]] = ("data", "header_index.json")

#: The one specifier that decides whether a property can reach a save.
SPECIFIER_SAVE_GAME: Final = "SaveGame"

#: Only C++ headers are parsed. The archive also carries build scripts and
#: plugin descriptors, which declare no properties and are recorded as skipped
#: rather than dropped.
HEADER_SUFFIX: Final = ".h"

# --- extraction limits ------------------------------------------------------

#: A ceiling on the decompressed size of a single entry, so a malformed or
#: hostile archive cannot be inflated without bound. The largest header in the
#: pinned build is far below this.
MAX_ENTRY_BYTES: Final = 4_000_000

#: Windows can hold a brief share violation on a file another process just
#: read, so the artifact's replace is retried rather than failing the write.
#: Same shape and the same reason as ``clockspeed/data/version.py``.
_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_SECONDS: Final = 0.05

#: Suffix of the scratch file the atomic write lands on first. It sits beside
#: the destination so the replace is a same-directory rename.
_TEMP_SUFFIX: Final = ".assets-tmp"

# --- the grammar ------------------------------------------------------------

#: The macro that opens a reflected property declaration. The specifier list is
#: NOT captured here - it is scanned for a balanced closing paren instead,
#: because ``meta = ( ... )`` nests.
_UPROPERTY_RE: Final = re.compile(r"\bUPROPERTY\s*\(")

#: A type declaration that OPENS a body, which is what distinguishes it from a
#: forward declaration. ``class AFoo;`` ends at a semicolon and must never be
#: mistaken for the owner of the properties that follow it - so what may follow
#: the name is an explicit, closed list rather than anything at all.
#:
#: ``final`` is in that list because it is MEASURED in the shipped archive, and
#: leaving it out left nineteen properties - five of them ``SaveGame`` - owned
#: by no type. The export macro is optional for the same reason: the plugin
#: headers spell it and some of the game headers do not.
_TYPE_DECL_RE: Final = re.compile(
    r"^[ \t]*(?:class|struct)\s+(?:\w+_API\s+)?(?P<name>[A-Za-z_]\w*)"
    r"(?:\s+final)?\s*(?::|\{|$)",
    re.MULTILINE,
)

#: A reflected enumeration, captured with its members so an enum's spelling is
#: a lookup as well. The body is taken to the first closing brace; no member of
#: any shipped enum carries one.
_UENUM_RE: Final = re.compile(
    r"\bUENUM\s*\([^)]*\)\s*enum(?:\s+class)?\s+(?P<name>[A-Za-z_]\w*)"
    r"[^{;]*\{(?P<body>[^}]*)\}",
    re.DOTALL,
)

#: One member of an enum body, before any ``= value`` or ``UMETA( ... )`` tail.
_ENUM_MEMBER_RE: Final = re.compile(r"^\s*(?P<name>[A-Za-z_]\w*)", re.MULTILINE)

#: An identifier, used to split a declaration into its type and its name.
_IDENTIFIER_RE: Final = re.compile(r"[A-Za-z_]\w*")

#: How far past a ``UPROPERTY`` macro a declaration may run before the scan
#: gives up on it. Generous enough for the longest multi-line declaration in
#: the pinned build and small enough that a malformed file cannot make the
#: scan quadratic.
_DECLARATION_WINDOW: Final = 2000


# --- errors -----------------------------------------------------------------


class AssetsError(Exception):
    """Base class for every failure raised by this module."""


class HeadersArchiveError(AssetsError):
    """The headers archive could not be opened, read or decompressed."""


# --- the model --------------------------------------------------------------


@dataclass(frozen=True)
class HeaderProperty:
    """One reflected property, exactly as the header declares it.

    Attributes:
        owner: The declaring class or struct. Derived from the enclosing type
            declaration and never from the file name - a header commonly
            declares a struct and a class, and a file-keyed index answers
            "which type declares this" wrongly for one of them.
        name: The member's identifier, for example ``mPurity``.
        type_text: The declared type, with the header's own internal spacing
            preserved. Never parsed further: the template spelling is what a
            reader needs, and normalizing it would invent a canonical form the
            publisher never wrote.
        specifiers: The macro's specifier list, split at paren depth zero so a
            ``meta = ( ... )`` group survives whole.
        header: The archive-relative entry name, in posix form.
    """

    owner: str
    name: str
    type_text: str
    specifiers: tuple[str, ...]
    header: str

    @property
    def is_save_game(self) -> bool:
        """Whether this declaration can be serialized into a save at all."""
        return any(
            specifier.split("=", 1)[0].strip() == SPECIFIER_SAVE_GAME
            for specifier in self.specifiers
        )


@dataclass(frozen=True)
class HeaderEnum:
    """One reflected enumeration and the members it declares.

    Attributes:
        name: The enum's identifier, for example ``EResourcePurity``.
        members: Member identifiers in declaration order, with any ``= value``
            and ``UMETA`` tail dropped.
        header: The archive-relative entry name, in posix form.
    """

    name: str
    members: tuple[str, ...]
    header: str


@dataclass(frozen=True)
class SkippedHeader:
    """An archive entry that was not parsed, recorded rather than dropped.

    Attributes:
        header: The archive-relative entry name, in posix form.
        reason: Why it was skipped, in words, carrying no file content.
    """

    header: str
    reason: str


@dataclass(frozen=True)
class HeaderIndex:
    """Every reflected declaration the archive ships, queryable three ways.

    Attributes:
        properties: Every parsed property, in archive order then declaration
            order.
        headers: Every entry that was parsed, in posix form.
        skipped: Every entry that was not, with the reason.
        enums: Every reflected enumeration that was parsed.
    """

    properties: tuple[HeaderProperty, ...]
    headers: tuple[str, ...]
    skipped: tuple[SkippedHeader, ...]
    enums: tuple[HeaderEnum, ...] = ()

    def owners(self) -> tuple[str, ...]:
        """Every declaring type that owns at least one property, sorted."""
        return tuple(sorted({prop.owner for prop in self.properties}))

    def properties_of(self, owner: str) -> tuple[HeaderProperty, ...]:
        """Every property declared by one type, in declaration order."""
        return tuple(prop for prop in self.properties if prop.owner == owner)

    def declarations(self, name: str) -> tuple[HeaderProperty, ...]:
        """Every declaration of one member name, across every type.

        A member name is not unique across the shipped types, so this returns
        the whole population. Picking one by scan order would answer a
        different question from the one asked and would not say so.
        """
        return tuple(prop for prop in self.properties if prop.name == name)

    def save_game(self, name: str, *, owner: str | None = None) -> bool | None:
        """Whether a member name can be serialized into a save.

        Args:
            name: The member identifier to look up.
            owner: Restrict the lookup to one declaring type. Omit it to ask
                about the name across every type that declares it.

        Returns:
            ``True`` when at least one matching declaration carries the
            ``SaveGame`` specifier, ``False`` when matching declarations exist
            and none of them does, and ``None`` when the headers declare the
            name nowhere. The third value is not a convenience: an undeclared
            name is unknown game content, and answering ``False`` about it
            would be a confident wrong answer (non-negotiable 7).
        """
        found = self.declarations(name)
        if owner is not None:
            found = tuple(prop for prop in found if prop.owner == owner)
        if not found:
            return None
        return any(prop.is_save_game for prop in found)

    def enum(self, name: str) -> HeaderEnum | None:
        """One reflected enumeration by name, or ``None`` when undeclared."""
        for declared in self.enums:
            if declared.name == name:
                return declared
        return None

    def as_payload(self) -> dict[str, Any]:
        """The index as JSON-ready data, losing nothing a query needs."""
        return {
            "headers": list(self.headers),
            "properties": [
                {
                    "owner": prop.owner,
                    "name": prop.name,
                    "type": prop.type_text,
                    "specifiers": list(prop.specifiers),
                    "save_game": prop.is_save_game,
                    "header": prop.header,
                }
                for prop in self.properties
            ],
            "enums": [
                {"name": item.name, "members": list(item.members), "header": item.header}
                for item in self.enums
            ],
            "skipped": [{"header": item.header, "reason": item.reason} for item in self.skipped],
        }


def _rendered_count(index: object) -> str:
    """How many properties an index holds, for a repr, and NEVER a raise.

    A ``__repr__`` THAT RAISES FAILS EXACTLY WHEN SOMETHING HAS ALREADY GONE
    WRONG, which is the one moment it exists for. Measured here rather than
    reasoned about: the first draft called ``len(self.index.properties)``
    straight, and
    ``tests/test_assertion_rendering.py::test_the_shipped_repr_is_what_gets_
    bypassed_in_every_forced_arm`` reddened
    because the forced arm constructs the type with a planted value the field's
    annotation does not admit. The GENERATED repr this method replaced was
    total, so anything less would be a regression bought with a privacy fix.

    Same shape and the same reason as ``clockspeed/save/chunks.py``'s
    ``_rendered_length``; not imported, because ``data/`` reaching into a
    private underscore name of ``save/`` is the seam violation CLAUDE.md
    section 2.1 names.

    Args:
        index: Whatever a caller actually put in the field.

    Returns:
        The property count, ``none`` for a missing index, or ``?`` for a value
        that cannot report one.
    """
    if index is None:
        return "none"
    found = getattr(index, "properties", None)
    return str(len(found)) if isinstance(found, Sized) else "?"


@dataclass(frozen=True)
class ExtractResult:
    """What one end-to-end extraction did, including doing nothing.

    Attributes:
        index: The parsed index, or ``None`` when there was nothing to parse.
        artifact: Where the index was written, or ``None`` when nothing was
            written.
        reason: Empty when the extraction ran; otherwise a sentence saying why
            it did not. A missing install is a reason, never an exception.
    """

    index: HeaderIndex | None
    artifact: Path | None
    reason: str

    def __repr__(self) -> str:
        """Say whether an artifact was written, and never render its path.

        ``artifact`` defaults to a path under the repository root, and a caller
        is free to pass one anywhere - including under a home directory, which
        no diagnostic in this project may render (non-negotiable 3). A frozen
        dataclass with no ``__repr__`` generates one from its fields, so this
        type would have disclosed the path in every log line and every pytest
        assertion rendering until somebody wrote this method. CS-852 is the
        item that measured that exact shape on a different class.

        ``reason`` IS SHOWN rather than withheld. It is authored in this module
        from a fixed vocabulary plus a resolver label, carries no path by
        construction, and withholding a safe field is a CLAIM that it is
        sensitive - which the CS-850 sweep then reads as a leak wherever a test
        asserts on it. The index is counted, not rendered: its contents are
        publisher-owned header text.
        """
        written = "none" if self.artifact is None else "written"
        counted = _rendered_count(self.index)
        return f"ExtractResult(artifact={written}, properties={counted}, reason={self.reason!r})"


# --- parsing ----------------------------------------------------------------


def _balanced_close(text: str, open_at: int) -> int:
    """Index just past the paren that closes the one at ``open_at``.

    Returns ``-1`` when the archive entry ends before the list closes, which is
    treated as a declaration the scan cannot read rather than as a failure.
    """
    depth = 0
    index = open_at
    limit = len(text)
    while index < limit:
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return -1


def _split_specifiers(raw: str) -> tuple[str, ...]:
    """Split a specifier list at paren depth zero, preserving ``meta`` groups."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in raw:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return tuple(" ".join(part.split()) for part in parts if part.strip())


#: The four states :func:`blank_comments` walks. Held as plain integers with
#: one step function each, so no single function carries the whole machine.
_SCAN_CODE: Final = 0
_SCAN_LINE: Final = 1
_SCAN_BLOCK: Final = 2
_SCAN_STRING: Final = 3


def _scan_code(text: str, out: list[str], index: int, limit: int) -> tuple[int, int]:
    """One step outside any comment or string. Returns the next index and state."""
    char = text[index]
    following = text[index + 1] if index + 1 < limit else ""
    if char == "/" and following in ("/", "*"):
        out[index] = " "
        out[index + 1] = " "
        return index + 2, _SCAN_LINE if following == "/" else _SCAN_BLOCK
    if char == '"':
        return index + 1, _SCAN_STRING
    return index + 1, _SCAN_CODE


def _scan_line(text: str, out: list[str], index: int) -> tuple[int, int]:
    """One step inside a ``//`` comment, which the newline ends."""
    if text[index] == "\n":
        return index + 1, _SCAN_CODE
    out[index] = " "
    return index + 1, _SCAN_LINE


def _scan_block(text: str, out: list[str], index: int, limit: int) -> tuple[int, int]:
    """One step inside a block comment.

    Newlines survive so offsets and line anchors both stay true.
    """
    if text[index] == "*" and index + 1 < limit and text[index + 1] == "/":
        out[index] = " "
        out[index + 1] = " "
        return index + 2, _SCAN_CODE
    if text[index] != "\n":
        out[index] = " "
    return index + 1, _SCAN_BLOCK


def _scan_string(text: str, index: int, limit: int) -> tuple[int, int]:
    """One step inside a double-quoted literal, which is copied through."""
    char = text[index]
    if char == "\\" and index + 1 < limit:
        return index + 2, _SCAN_STRING
    return index + 1, _SCAN_CODE if char == '"' else _SCAN_STRING


def blank_comments(text: str) -> str:
    """Replace every comment body with spaces, preserving length and offsets.

    MEASURED, not anticipated: the pinned build's archive carries 11
    commented-out ``UPROPERTY`` lines, and a scan that reads them indexes a
    RETIRED declaration as a live one. That is the worst answer this module can
    give - a FALSE TRUE about whether a field reaches a save - so both comment
    spellings are consumed. A commented-out type declaration is the same fault
    on the owner side: it makes every live property below it belong to a type
    that does not exist.

    Length and newlines are preserved rather than the comment being deleted,
    because the owner scan and the macro scan compare OFFSETS into this text.
    Deleting would shift them and misattribute owners across a comment, which
    is a quieter fault than the one being fixed.

    Double-quoted strings are tracked so a ``//`` inside a tooltip or a URL is
    not mistaken for a comment. Single quotes are deliberately NOT tracked: an
    apostrophe outside a literal is common in prose and a char-literal state
    that never closes would blank the rest of the file.
    """
    out = list(text)
    index = 0
    limit = len(text)
    state = _SCAN_CODE
    while index < limit:
        if state == _SCAN_CODE:
            index, state = _scan_code(text, out, index, limit)
        elif state == _SCAN_LINE:
            index, state = _scan_line(text, out, index)
        elif state == _SCAN_BLOCK:
            index, state = _scan_block(text, out, index, limit)
        else:
            index, state = _scan_string(text, index, limit)
    return "".join(out)


def _split_declaration(raw: str) -> tuple[str, str] | None:
    """Split a member declaration into its type text and its member name.

    The trailing initializer is dropped first - both the ``= value`` and the
    braced ``{value}`` spellings occur in the shipped headers - and the last
    identifier of what remains is the member name.
    """
    body = raw
    for cut in ("=", "{"):
        position = body.find(cut)
        if position != -1:
            body = body[:position]
    body = " ".join(body.split())
    matches = list(_IDENTIFIER_RE.finditer(body))
    if not matches:
        return None
    last = matches[-1]
    type_text = body[: last.start()].rstrip()
    if not type_text:
        return None
    return type_text, last.group(0)


def _owner_positions(text: str) -> list[tuple[int, str]]:
    """Every body-opening type declaration, as (offset, name), in file order."""
    return [(match.start(), match.group("name")) for match in _TYPE_DECL_RE.finditer(text)]


def _owner_at(owners: list[tuple[int, str]], offset: int) -> str:
    """The type whose declaration most recently preceded ``offset``."""
    found = ""
    for position, name in owners:
        if position > offset:
            break
        found = name
    return found


def parse_header_text(text: str, *, header: str) -> tuple[HeaderProperty, ...]:
    """Parse every reflected property one header declares.

    Args:
        text: The header's decoded source.
        header: The archive-relative entry name, recorded on every result so a
            declaration can be cited back to where it was read.

    Returns:
        The properties in declaration order. A macro whose specifier list or
        declaration cannot be read is skipped: a header this scan cannot follow
        is unknown content, and guessing at it would be worse than omitting it.
    """
    source = blank_comments(text)
    owners = _owner_positions(source)
    found: list[HeaderProperty] = []
    for match in _UPROPERTY_RE.finditer(source):
        close = _balanced_close(source, match.end() - 1)
        if close == -1:
            continue
        specifiers = _split_specifiers(source[match.end() : close - 1])
        tail = source[close : close + _DECLARATION_WINDOW]
        end = tail.find(";")
        if end == -1:
            continue
        split = _split_declaration(tail[:end])
        if split is None:
            continue
        type_text, name = split
        found.append(
            HeaderProperty(
                owner=_owner_at(owners, match.start()),
                name=name,
                type_text=type_text,
                specifiers=specifiers,
                header=header,
            )
        )
    return tuple(found)


def parse_header_enums(text: str, *, header: str) -> tuple[HeaderEnum, ...]:
    """Parse every reflected enumeration one header declares."""
    found: list[HeaderEnum] = []
    for match in _UENUM_RE.finditer(blank_comments(text)):
        members = tuple(
            member.group("name")
            for line in match.group("body").split(",")
            for member in [_ENUM_MEMBER_RE.search(line)]
            if member is not None
        )
        found.append(HeaderEnum(name=match.group("name"), members=members, header=header))
    return tuple(found)


# --- reading the archive ----------------------------------------------------


def headers_archive_path(game_dir: Path) -> Path:
    """Where the headers archive sits under a resolved install directory."""
    return game_dir.joinpath(*HEADERS_ARCHIVE_PARTS)


def _read_entry(archive: zipfile.ZipFile, name: str) -> bytes:
    """Decompress one archive entry, or fail naming the entry and nothing else.

    A SEPARATE FUNCTION rather than a second ``try`` inside the walk, and the
    reason is a guard rather than taste: two raise sites in one function that
    catch the same tuple and raise the same class are INDISTINGUISHABLE to the
    chained-cause census, so an exemption written for one would silently cover
    the other. ``tests/test_chained_cause_census.py::test_every_site_key_is_distinct``
    measured exactly that collision here.

    The message carries the entry name and the caught exception's CLASS NAME.
    It never renders the exception itself: ``OSError.__str__`` appends
    ``filename`` verbatim, and an absolute path on this machine may contain a
    home directory (non-negotiable 3).

    Raises:
        HeadersArchiveError: The entry would not decompress.
    """
    try:
        return archive.read(name)
    except (zipfile.BadZipFile, OSError) as exc:
        raise HeadersArchiveError(
            f"the headers archive entry {name} would not decompress: {type(exc).__name__}"
        ) from exc


def load_header_index(path: Path) -> HeaderIndex:
    """Read the headers archive and build the index.

    The archive is opened read-only and nothing under the install is written
    (non-negotiable 1). An entry that is not a C++ header, that exceeds
    :data:`MAX_ENTRY_BYTES`, or that will not decode is FLAGGED AND SKIPPED
    rather than dropped or fatal (non-negotiable 7) - the index publishes them
    on ``skipped`` so a consumer can see what this build shipped that the scan
    could not read.

    Args:
        path: The archive to read.

    Returns:
        The index over every entry that parsed.

    Raises:
        HeadersArchiveError: The archive could not be opened or is not a zip.
            The message carries the entry name and the operating system's own
            words, never any of the file's content.
    """
    properties: list[HeaderProperty] = []
    enums: list[HeaderEnum] = []
    headers: list[str] = []
    skipped: list[SkippedHeader] = []
    try:
        archive = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError) as exc:
        raise HeadersArchiveError(
            f"the headers archive is not readable: {type(exc).__name__}"
        ) from exc
    with archive:
        for info in archive.infolist():
            name = info.filename
            if info.is_dir():
                continue
            if not name.lower().endswith(HEADER_SUFFIX):
                skipped.append(SkippedHeader(header=name, reason="not a C++ header"))
                continue
            if info.file_size > MAX_ENTRY_BYTES:
                skipped.append(SkippedHeader(header=name, reason="entry exceeds the size ceiling"))
                continue
            raw = _read_entry(archive, name)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped.append(SkippedHeader(header=name, reason="not decodable as utf-8"))
                continue
            headers.append(name)
            properties.extend(parse_header_text(text, header=name))
            enums.extend(parse_header_enums(text, header=name))
    return HeaderIndex(
        properties=tuple(properties),
        headers=tuple(headers),
        skipped=tuple(skipped),
        enums=tuple(enums),
    )


# --- writing the artifact ---------------------------------------------------


def repo_root() -> Path:
    """This repository's root, derived from this module's own location."""
    return Path(__file__).resolve().parents[2]


def artifact_path(root: Path | None = None) -> Path:
    """Where the generated index lands, under the gitignored ``data/``.

    Args:
        root: The repository root. Defaults to :func:`repo_root`.
    """
    return (repo_root() if root is None else root).joinpath(*ARTIFACT_PARTS)


def write_index(index: HeaderIndex, path: Path) -> None:
    """Write the index to ``path`` atomically, as 7-bit ASCII with LF endings.

    Bytes are written explicitly rather than through a text-mode write, which
    on Windows would turn every LF into CRLF and make the artifact's byte count
    depend on which machine produced it (CONVENTIONS.md section 10).

    Args:
        index: The index to write.
        path: The destination. Never a path under the game install - nothing in
            this project writes there.

    Raises:
        OSError: The artifact could not be written or replaced.
    """
    payload = json.dumps(index.as_payload(), indent=2, sort_keys=True, ensure_ascii=True)
    data = (payload + "\n").encode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + _TEMP_SUFFIX)
    temporary.write_bytes(data)
    last: OSError | None = None
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            temporary.replace(path)
        except OSError as exc:
            last = exc
            time.sleep(_RENAME_PAUSE_SECONDS * (attempt + 1))
        else:
            return
    temporary.unlink(missing_ok=True)
    raise last if last is not None else OSError("replace failed with no error recorded")


def extract_header_index(
    *, game_dir: Path | None = None, destination: Path | None = None
) -> ExtractResult:
    """Read the install's headers archive and write the index, or say why not.

    This is the ONLY entry point here that asks where the install is, and it
    asks ``clockspeed/data/locate.py`` rather than deciding. A machine with no
    game installed gets a ``reason`` and no exception, so the whole suite runs
    where the game is absent.

    Args:
        game_dir: The install root. Defaults to the resolved one.
        destination: Where to write. Defaults to :func:`artifact_path`, which
            is under the gitignored generated directory - extracted game data
            is never committed (non-negotiable 2).

    Returns:
        The result, whose ``reason`` is empty exactly when an index was built
        and written.

    Raises:
        HeadersArchiveError: The archive exists but could not be read.
        OSError: The artifact could not be written.
    """
    if game_dir is None:
        resolved, source = locate.resolve_game_dir()
    else:
        resolved, source = game_dir, "caller"
    if resolved is None:
        return ExtractResult(
            index=None,
            artifact=None,
            reason=f"no game install was resolved, so there is nothing to read ({source})",
        )
    archive = headers_archive_path(resolved)
    if not archive.is_file():
        return ExtractResult(
            index=None,
            artifact=None,
            reason="the resolved install ships no headers archive, so there is nothing to read",
        )
    index = load_header_index(archive)
    target = artifact_path() if destination is None else destination
    write_index(index, target)
    return ExtractResult(index=index, artifact=target, reason="")
