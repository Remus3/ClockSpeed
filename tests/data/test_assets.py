"""Tests for the shipped-asset header index - the declaration-grade field oracle.

WHY THIS FILE EXISTS. Until CS-1040 every "is this field in the save" question in
this project was answered by sampling: grep a save, count the hits, and conclude
from an absence. ADR 0003 had to settle for exactly that about node purity. The
install ships `CommunityResources/Headers.zip`, 1112 publisher-authored C++
headers sitting beside the `Docs` file `clockspeed/data/docs_extract.py` already
reads, and an Unreal property is serialized into a save if and only if its
`UPROPERTY` macro carries the `SaveGame` specifier. That turns the question into
a LOOKUP with a yes, a no, and - the part that matters most - an UNKNOWN.

Three decisions shape every arm below.

- **Fixtures are hand-authored synthetic C++**, never a slice of a real header
  (BOOTSTRAP.md section 8.1, CLAUDE.md non-negotiable 2). The shipped headers are
  publisher-owned and may not be committed, so every grammar case here is written
  out character for character in the shape the real macro takes.
- **The three-valued answer is asserted as three values.** A lookup that returned
  False for a name the headers never declare would be a confident wrong answer
  about unknown game content, which non-negotiable 7 forbids. `None` is the
  unknown, and it has its own arm.
- **The read-only claim is measured at RUNTIME with a recording spy, and the spy
  carries its own potency control.** A spy that records nothing agrees with a
  clean run, so the acceptance arm asserts the recorder actually saw the archive
  opened, and a companion arm proves the same recorder reddens on a real write.
  An oracle blind to its own subject passes for that reason alone.
"""

from __future__ import annotations

import builtins
import io
import json
import os
from pathlib import Path
from typing import Any

import pytest

from clockspeed.data import locate
from clockspeed.data.assets import (
    ARTIFACT_PARTS,
    HEADERS_ARCHIVE_PARTS,
    HeaderIndex,
    HeaderProperty,
    artifact_path,
    extract_header_index,
    headers_archive_path,
    load_header_index,
    parse_header_text,
    write_index,
)

# ---------------------------------------------------------------------------
# Synthetic headers - the real macro's shape, none of the publisher's bytes
# ---------------------------------------------------------------------------

#: The declaration shape that settles node purity. Two properties on one class:
#: one with no SaveGame specifier and one that has it, so a parser that ignores
#: the specifier list entirely cannot pass this fixture.
_PURITY_HEADER = """
#pragma once

UCLASS()
class SYNTH_API ASynthResourceNode : public AActor
{
\tGENERATED_BODY()
public:
\t/** Instance-authored, never serialized. */
\tUPROPERTY( EditInstanceOnly, Category = "Resources" )
\tTEnumAsByte<ESynthPurity> mPurity;

\t/** Serialized, and only ever written when overridden. */
\tUPROPERTY( SaveGame, Replicated )
\tTEnumAsByte< ESynthPurity > mPurityOverride = RP_MAX;
};
"""

#: Two declaring types in one file, which is the common shape and the one a
#: file-keyed index gets wrong.
_TWO_OWNER_HEADER = """
USTRUCT()
struct FSynthClearance
{
\tUPROPERTY( EditDefaultsOnly, Category = "Clearance" )
\tFBox ClearanceBox;
};

UCLASS()
class ASynthBuildable : public AActor
{
\tUPROPERTY( EditDefaultsOnly, Category = "Buildable" )
\tTArray< FSynthClearance > mClearanceData;
};
"""

#: The `final` specifier, which sits between the type name and the thing the
#: owner scan looks for. The shipped archive really does use it, and the
#: forward declaration above it is the shape that must NOT become an owner.
_FINAL_HEADER = """
class USomethingElse;

USTRUCT()
struct SYNTH_API FSynthFinal final
{
\tUPROPERTY( SaveGame )
\tint32 mCarried;
};
"""

#: A retired declaration left behind as a comment, which the shipped archive
#: really does carry. The live property below it is what a reader wants; the
#: commented one must not be indexed at all.
_COMMENTED_HEADER = """
UCLASS()
class ASynthRetired : public AActor
{
	//UPROPERTY( SaveGame )
	//TArray<uint8> mRetiredButSaved;

	/* UPROPERTY( SaveGame )
	int32 mAlsoRetired; */

	UPROPERTY( EditDefaultsOnly )
	int32 mLive;
};
"""

#: A type whose whole declaration is commented out, sitting above a live one.
#: A scan that read the comment attributes the live property to a type that
#: does not exist, which is a confident wrong answer rather than an unknown.
_RETIRED_OWNER_HEADER = """
//UCLASS()
//class ARetired : public AActor

UCLASS()
class ALive : public AActor
{
\tUPROPERTY( SaveGame )
\tint32 mField;
};
"""

_HEADER_NAME = "Source/Synth/Public/SynthResourceNode.h"
_TWO_OWNER_NAME = "Source/Synth/Public/SynthBuildable.h"
_COMMENTED_NAME = "Source/Synth/Public/SynthRetired.h"
_FINAL_NAME = "Source/Synth/Public/SynthFinal.h"


def _index_of(text: str, header: str) -> HeaderIndex:
    """A one-header index, so the query arms read as queries rather than setup."""
    return HeaderIndex(
        properties=parse_header_text(text, header=header), headers=(header,), skipped=()
    )


# ---------------------------------------------------------------------------
# The grammar
# ---------------------------------------------------------------------------


def test_the_specifier_list_is_parsed_whole_not_sampled() -> None:
    """The whole property is pinned, never one field of it.

    A partial assertion passes for a parser that dropped the type, the owner or
    the rest of the specifiers.
    """
    parsed = parse_header_text(_PURITY_HEADER, header=_HEADER_NAME)

    assert parsed == (
        HeaderProperty(
            owner="ASynthResourceNode",
            name="mPurity",
            type_text="TEnumAsByte<ESynthPurity>",
            specifiers=("EditInstanceOnly", 'Category = "Resources"'),
            header=_HEADER_NAME,
        ),
        HeaderProperty(
            owner="ASynthResourceNode",
            name="mPurityOverride",
            type_text="TEnumAsByte< ESynthPurity >",
            specifiers=("SaveGame", "Replicated"),
            header=_HEADER_NAME,
        ),
    )


def test_the_owner_is_the_declaring_type_and_not_the_file() -> None:
    """The owner comes from the enclosing type, never from the file name.

    A file-keyed index answers "which type declares this" wrongly the moment a
    header holds a struct and a class, which is the common shape.
    """
    owners = [prop.owner for prop in parse_header_text(_TWO_OWNER_HEADER, header=_TWO_OWNER_NAME)]

    assert owners == ["FSynthClearance", "ASynthBuildable"]


# ---------------------------------------------------------------------------
# The three-valued answer
# ---------------------------------------------------------------------------


def test_a_property_without_the_savegame_specifier_cannot_reach_a_save() -> None:
    """The declaration-grade answer ADR 0003 had to reach by sampling."""
    index = _index_of(_PURITY_HEADER, _HEADER_NAME)

    assert index.save_game("mPurity") is False


def test_a_savegame_property_is_reported_as_serialized() -> None:
    """The other direction, so the arm above cannot pass by always saying False."""
    index = _index_of(_PURITY_HEADER, _HEADER_NAME)

    assert index.save_game("mPurityOverride") is True


def test_a_name_the_headers_never_declare_is_unknown_rather_than_false() -> None:
    """An undeclared name is unknown, and unknown is not False.

    Non-negotiable 7: an absent declaration is unknown game content, and a
    lookup that answered False would be a confident wrong answer about it.
    """
    index = _index_of(_PURITY_HEADER, _HEADER_NAME)

    assert index.save_game("mNameNoHeaderDeclares") is None


def test_the_declarations_of_a_name_carry_every_owner_that_declares_it() -> None:
    """A name lookup returns the whole population that declares it.

    A member name is not unique across the shipped types, so returning one
    winner chosen by scan order would answer a different question in silence.
    """
    index = HeaderIndex(
        properties=parse_header_text(_PURITY_HEADER, header=_HEADER_NAME)
        + parse_header_text(_TWO_OWNER_HEADER, header=_TWO_OWNER_NAME),
        headers=(_HEADER_NAME, _TWO_OWNER_NAME),
        skipped=(),
    )

    assert [prop.owner for prop in index.declarations("mPurity")] == ["ASynthResourceNode"]
    assert index.properties_of("ASynthBuildable") == (
        HeaderProperty(
            owner="ASynthBuildable",
            name="mClearanceData",
            type_text="TArray< FSynthClearance >",
            specifiers=("EditDefaultsOnly", 'Category = "Buildable"'),
            header=_TWO_OWNER_NAME,
        ),
    )


def test_a_final_type_still_owns_its_properties() -> None:
    """MEASURED: `final` sits where the owner scan looked for the body.

    The shipped archive uses it, and the scan that missed it left nineteen
    properties - five of them `SaveGame` - attributed to no type at all. The
    forward declaration above the fixture is here in the same arm because the
    obvious widening, accepting anything after the name, makes `class UFoo;`
    an owner and is a worse fault than the one it repairs.
    """
    parsed = parse_header_text(_FINAL_HEADER, header=_FINAL_NAME)

    assert [(prop.owner, prop.name) for prop in parsed] == [("FSynthFinal", "mCarried")]


def test_a_commented_out_macro_is_not_a_declaration() -> None:
    """A retired property left behind as a comment must not reach the index.

    THE WORST FAILURE THIS MODULE CAN MAKE is a FALSE TRUE - saying a field can
    reach a save when it cannot. A commented-out `UPROPERTY( SaveGame )` is
    exactly that shape, and the shipped archive really does carry commented-out
    macros. Both comment spellings are here because a scan that handled only
    `//` would pass this arm on half its subject.
    """
    parsed = parse_header_text(_COMMENTED_HEADER, header=_COMMENTED_NAME)

    assert [prop.name for prop in parsed] == ["mLive"]


def test_a_commented_out_type_declaration_owns_nothing() -> None:
    """The owner scan reads comments too, and a retired class is not an owner.

    A header whose whole type is commented out leaves every live property below
    it attributed to a type that does not exist, which is a confident wrong
    answer rather than an unknown.
    """
    parsed = parse_header_text(_RETIRED_OWNER_HEADER, header=_COMMENTED_NAME)

    assert [(prop.owner, prop.name) for prop in parsed] == [("ALive", "mField")]


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_artifact_lands_under_the_gitignored_generated_directory() -> None:
    """The generated index lands where git will never take it.

    `data/` is gitignored and `clockspeed/data/` is tracked source, so an
    artifact that landed in the second would commit extracted game data.
    """
    assert ARTIFACT_PARTS[0] == "data"
    assert artifact_path(Path("repo")).parts[-len(ARTIFACT_PARTS) :] == ARTIFACT_PARTS


def test_the_written_payload_round_trips_through_json(tmp_path: Path) -> None:
    """The written payload keeps everything a query needs.

    The artifact is the queryable form, so a payload that lost the specifiers
    would leave every later lookup a grep again.
    """
    index = _index_of(_PURITY_HEADER, _HEADER_NAME)
    target = tmp_path / "header_index.json"

    write_index(index, target)
    payload: Any = json.loads(target.read_text(encoding="ascii"))

    assert [entry["specifiers"] for entry in payload["properties"]] == [
        ["EditInstanceOnly", 'Category = "Resources"'],
        ["SaveGame", "Replicated"],
    ]


# ---------------------------------------------------------------------------
# The read-only spy, and its potency control
# ---------------------------------------------------------------------------


class _OpenRecorder:
    """Every open this process makes while installed, with its mode or flags."""

    def __init__(self) -> None:
        self.opens: list[tuple[str, str]] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch every channel a file can be opened through, not just one.

        `builtins.open` and `io.open` are the same function but are SEPARATE
        bindings, and `pathlib` reaches for the second. Patching only the first
        records nothing a `Path.open`, `Path.read_bytes` or `Path.write_bytes`
        does, which is most of what this project actually calls - the recorder
        would then report a clean run over a module that writes on every call.
        """
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open

        def spy_builtin_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            self.opens.append((str(file), mode))
            return real_builtin_open(file, mode, *args, **kwargs)

        def spy_io_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            self.opens.append((str(file), mode))
            return real_io_open(file, mode, *args, **kwargs)

        def spy_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> Any:
            self.opens.append((str(path), f"os_flags={flags}"))
            return real_os_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", spy_builtin_open)
        monkeypatch.setattr(io, "open", spy_io_open)
        monkeypatch.setattr(os, "open", spy_os_open)

    def writes(self) -> list[tuple[str, str]]:
        """Every recorded open that could modify a file."""
        found = []
        for target, mode in self.opens:
            if mode.startswith("os_flags="):
                flags = int(mode.split("=", 1)[1])
                if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC):
                    found.append((target, mode))
            elif set(mode) & set("wax+"):
                found.append((target, mode))
        return found


def test_the_open_recorder_reddens_on_a_real_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """POTENCY CONTROL for the acceptance arm below, and it is not optional.

    A recorder that silently failed to install would report an empty write list
    on a module that writes to the install on every call, and the acceptance arm
    would pass for that reason alone.
    """
    recorder = _OpenRecorder()
    recorder.install(monkeypatch)

    (tmp_path / "written.txt").write_text("synthetic", encoding="ascii")

    assert recorder.writes(), "the recorder saw no write while a file was being written"


def test_the_extraction_reads_only_and_skips_cleanly_with_no_install(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CS-1040 acceptance. Three claims, in the order they can be measured.

    First, and on every machine including one with no game: pointing the
    resolver at nothing must produce a REASON rather than an exception, because
    the whole suite has to run where the game is not installed.

    Then, and only where the install is really present: every open under the
    install is read-only, the archive is actually opened - the recorder's own
    subject - and the only write lands under the gitignored generated
    directory.
    """
    monkeypatch.setenv(locate.ENV_GAME_DIR, str(tmp_path / "no-install-here"))
    absent = extract_header_index(destination=tmp_path / "absent.json")

    # BOUND TO SCALARS BEFORE THE ASSERT, and not as a style choice. pytest
    # reprs the sub-expressions of an assert independently of the message, so
    # `assert absent.artifact is None` renders the Path that ExtractResult
    # ships a __repr__ to WITHHOLD - measured as four findings by
    # tests/test_assertion_rendering.py, which is what this shape repairs.
    built_no_index = absent.index is None
    wrote_nothing = absent.artifact is None

    assert built_no_index
    assert wrote_nothing
    assert absent.reason != ""

    monkeypatch.delenv(locate.ENV_GAME_DIR, raising=False)
    game_dir, source = locate.resolve_game_dir()
    if game_dir is None:
        pytest.skip(
            f"no game install on this machine, so the read-only arms have no subject; "
            f"the resolver reported: {source}"
        )

    archive = headers_archive_path(game_dir)
    if not archive.is_file():
        pytest.skip("this install ships no headers archive, so there is nothing to read")

    destination = tmp_path / "header_index.json"
    recorder = _OpenRecorder()
    recorder.install(monkeypatch)
    result = extract_header_index(destination=destination)

    install_prefix = str(game_dir).replace("\\", "/").rstrip("/").lower()
    touched_install = [
        (target, mode)
        for target, mode in recorder.opens
        if target.replace("\\", "/").lower().startswith(install_prefix)
    ]
    writes = recorder.writes()
    assert touched_install, "the recorder saw no open under the install at all"
    assert [entry for entry in touched_install if entry in writes] == []

    # The atomic write lands on a scratch file beside the destination and is
    # renamed onto it, so the recorded target is that neighbour rather than the
    # destination itself. Both share the destination's own prefix and nothing
    # else may.
    assert writes, "the recorder saw no write at all, so it graded nothing"
    assert [target for target, _mode in writes if not target.startswith(str(destination))] == []
    landed_where_asked = result.artifact == destination
    built_an_index = result.index is not None

    assert landed_where_asked
    assert built_an_index
    assert destination.is_file()

    # The DEFAULT destination, which is the one a caller gets, is under the
    # gitignored generated directory rather than the tracked source package.
    assert artifact_path().parts[-len(ARTIFACT_PARTS) :] == ARTIFACT_PARTS


def test_a_real_archive_declares_the_savegame_specifier_on_something() -> None:
    """The index is worthless if the specifier never appears in the live data.

    Live-install arm, skipped where there is no game. It asserts only structure
    - that both answers occur - because a count from the shipped build is a
    build fact and `clockspeed/data/version.py` owns those.
    """
    game_dir, source = locate.resolve_game_dir()
    if game_dir is None:
        pytest.skip(f"no game install on this machine; the resolver reported: {source}")

    archive = headers_archive_path(game_dir)
    if not archive.is_file():
        pytest.skip("this install ships no headers archive, so there is nothing to read")

    index = load_header_index(archive)

    assert any(prop.is_save_game for prop in index.properties)
    assert any(not prop.is_save_game for prop in index.properties)
    assert archive.parts[-len(HEADERS_ARCHIVE_PARTS) :] == HEADERS_ARCHIVE_PARTS
