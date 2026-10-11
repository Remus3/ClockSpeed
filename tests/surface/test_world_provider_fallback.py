"""The world provider falls back past a save the reader refuses, and says so.

THE DEFECT. ``SaveWorldProvider`` resolved the newest save and stopped there.
The newest file in the operator's save directory was a save re-encoded by a
third-party tool, which the object reader refuses - correctly - and the
companion answered "no world" for a directory holding dozens of readable
saves. Non-negotiable 7: unknown content is flagged and skipped, never fatal.

WHAT IS GRADED, on synthetic bytes in ``tmp_path`` with NO real save and NO
game install:

a. A refused newest save falls back to the next one, and the world handed up
   carries the ``WARN_NEWER_SAVE_REFUSED`` flag.
b. The refusal is remembered by identity, so a refused save is not copied and
   parsed again on every call - the CS-1203 cost the memo exists to remove -
   while a REWRITTEN refused save is tried again.
c. Nothing readable still answers None.
d. The default wiring ranks the account directory through ``workdir`` and
   loads through the real reader.
e. The real defect's shape end to end - a header the reader accepts over a
   body the OBJECT reader refuses - falls back through the default wiring,
   and the save directory is left exactly as it was found (CS-1309).

EVERY ASSERTION IS ON A SCALAR BOUND TO A LOCAL. A ``tmp_path`` lives under a
home directory, so no assertion renders a path.
"""

from __future__ import annotations

import hashlib
import os
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.save import workdir, world
from clockspeed.surface import providers
from tests.save import synthetic

if TYPE_CHECKING:
    from pathlib import Path

#: A walk that tried two saves, or a save loaded twice.
TWO_LOADS: Final = 2

#: 2020-09-13T12:26:40Z, a whole second so the rendered time is exact.
BASE_SECONDS: Final = 1_600_000_000

#: The flag subject a newest save written one minute after the base carries
#: when the object reader refuses it.
NEWER_OBJECTS_SUBJECT: Final = "objects.ObjectFormatError.mtime-2020-09-13T12-27-40Z"

#: How many times each arm asks the provider.
CALLS: Final = 3


@pytest.fixture(autouse=True)
def isolated_work_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Send workdir's copies under tmp_path so no test writes into the repo."""
    root = tmp_path / "work-root"
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(root))
    return root


def plant(path: Path, payload: bytes, seconds: int) -> Path:
    """Write synthetic bytes with an exact, whole-second modification time.

    Args:
        path: Where to write, under tmp_path.
        payload: Synthetic bytes - never a real save.
        seconds: The modification time in seconds since the epoch.

    Returns:
        The same path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    stamp = seconds * 1_000_000_000
    os.utime(path, ns=(stamp, stamp))
    return path


def subjects_of(model: world.WorldModel | None) -> list[str]:
    """The subject of every fallback flag the model carries, in order."""
    if model is None:
        return []
    return [
        warning.subject or ""
        for warning in model.warnings
        if warning.code == world.WARN_NEWER_SAVE_REFUSED
    ]


class CountingLoad:
    """A ``load`` that refuses planted names with an objects-stage refusal.

    Every other path is loaded through the real reader, FLAT, because the
    corpus fixture used here is flat-bodied.

    Attributes:
        calls: File name to how many times it was loaded.
    """

    def __init__(self, refused: set[str]) -> None:
        """Remember which file names the reader refuses.

        Args:
            refused: File names that raise an objects-stage refusal.
        """
        self.calls: dict[str, int] = {}
        self._refused = refused

    def __call__(self, path: Path) -> world.WorldModel:
        """Refuse a planted name, or load the save flat."""
        self.calls[path.name] = self.calls.get(path.name, 0) + 1
        if path.name in self._refused:
            raise world.WorldLoadError(world.STAGE_OBJECTS, "ObjectFormatError")
        return world.load_world(path, body_layout=world.BODY_LAYOUT_FLAT)


def provider_over(saves: list[Path], load: CountingLoad) -> providers.SaveWorldProvider:
    """A provider whose ranking is ``saves``, newest first."""
    return providers.SaveWorldProvider(
        find_saves=lambda _dir: tuple(saves),
        load=load,
    )


# ---------------------------------------------------------------------------
# a. fall back, and flag it
# ---------------------------------------------------------------------------


def test_a_refused_newest_save_falls_back_and_is_flagged(tmp_path: Path) -> None:
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = CountingLoad({newest.name})

    model = provider_over([newest, older], load).world()

    present = model is not None
    assert present, "a readable older save was not handed up past a refused newest one"
    subjects = subjects_of(model)
    assert subjects == [NEWER_OBJECTS_SUBJECT]


# ---------------------------------------------------------------------------
# b. remembered by identity, retried when rewritten
# ---------------------------------------------------------------------------


def test_a_refused_save_is_not_parsed_again_on_every_call(tmp_path: Path) -> None:
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = CountingLoad({newest.name})
    provider = provider_over([newest, older], load)

    answers = [provider.world() for _ in range(CALLS)]

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == 1, "an unchanged refused save was parsed again"
    fallback_loads = load.calls.get(older.name, 0)
    assert fallback_loads == 1, "an unchanged fallback save was parsed again"
    flagged = [subjects_of(answer) for answer in answers]
    assert flagged == [[NEWER_OBJECTS_SUBJECT]] * CALLS


def test_a_refused_save_arriving_does_not_re_parse_the_remembered_world(
    tmp_path: Path,
) -> None:
    """The world already in memory IS the fallback; refusing a newer file must not drop it."""
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    ranking = [older]
    load = CountingLoad({newest.name})
    provider = providers.SaveWorldProvider(find_saves=lambda _dir: tuple(ranking), load=load)
    provider.world()

    ranking.insert(0, newest)
    model = provider.world()

    fallback_loads = load.calls.get(older.name, 0)
    assert fallback_loads == 1, "the remembered world was parsed again behind a refusal"
    subjects = subjects_of(model)
    assert subjects == [NEWER_OBJECTS_SUBJECT]


def test_a_rewritten_refused_save_is_tried_again(tmp_path: Path) -> None:
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = CountingLoad({newest.name})
    provider = provider_over([newest, older], load)
    provider.world()

    plant(newest, b"re-encoded, and longer", BASE_SECONDS + 90)
    provider.world()

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == TWO_LOADS, "a rewritten save was judged by its old refusal"


def test_a_refused_save_the_game_has_replaced_is_read(tmp_path: Path) -> None:
    """The flag goes when its cause goes: a newest save that now loads wins."""
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    refused = {newest.name}
    load = CountingLoad(refused)
    provider = provider_over([newest, older], load)
    provider.world()

    refused.clear()
    plant(newest, synthetic.SAVE_V52.blob, BASE_SECONDS + 120)
    model = provider.world()

    subjects = subjects_of(model)
    assert subjects == []
    newest_loads = load.calls.get(newest.name, 0)
    assert newest_loads == TWO_LOADS


# ---------------------------------------------------------------------------
# c. nothing readable
# ---------------------------------------------------------------------------


def test_every_save_refused_answers_none(tmp_path: Path) -> None:
    newest = plant(tmp_path / "Newest.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Older.sav", b"also re-encoded", BASE_SECONDS)
    load = CountingLoad({newest.name, older.name})

    absent = provider_over([newest, older], load).world() is None

    assert absent, "a directory of refused saves handed up a world"


def test_find_save_and_find_saves_together_are_refused() -> None:
    """Two rankings for one provider is a wiring bug, refused at construction."""
    with pytest.raises(ValueError, match="find_save"):
        providers.SaveWorldProvider(find_save=lambda _dir: None, find_saves=lambda _dir: ())


# ---------------------------------------------------------------------------
# d. the default wiring
# ---------------------------------------------------------------------------


def test_the_default_wiring_ranks_through_workdir_and_falls_back(tmp_path: Path) -> None:
    """No injected seam: workdir ranks the directory and the real reader refuses."""
    account = tmp_path / "pretend-account"
    plant(account / "Newest.sav", b"not a save the game wrote", BASE_SECONDS + 60)
    plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)

    model = providers.SaveWorldProvider(account).world()

    present = model is not None
    assert present, "the default wiring did not fall back past a refused newest save"
    subjects = subjects_of(model)
    flagged = len(subjects)
    assert flagged == 1
    header_refusal = subjects[0].startswith(world.STAGE_HEADER + ".")
    assert header_refusal


# ---------------------------------------------------------------------------
# e. the real defect's shape end to end, and the save directory untouched
# ---------------------------------------------------------------------------

#: How many body bytes the synthetic re-encoded save is short of the body its
#: header describes. The real file's body was shorter than the game's; any
#: shortfall the object reader cannot walk draws the same refusal.
BODY_SHORTFALL: Final = 16


def reencoded_levelled_save() -> bytes:
    """A synthetic save whose header reads and whose body the object reader refuses.

    The real defect's SHAPE on synthetic bytes: the levelled corpus fixture's
    own header over its body cut short, so the refusal comes from the OBJECTS
    stage as the real one did, not from a header that never parsed. Built
    from the corpus fixture, never from a real save.

    Returns:
        The save bytes.
    """
    fixture = synthetic.SAVE_LEVELLED_V36
    body = fixture.body[: len(fixture.body) - BODY_SHORTFALL]
    framed = synthetic.build_chunks(body, framing=fixture.framing)
    return fixture.blob[: fixture.chunk_offset] + framed


def directory_state(directory: Path) -> tuple[tuple[str, int, int, str], ...]:
    """Every entry under ``directory`` by relative name, size, mtime and digest.

    Compared whole and never rendered: the names are synthetic, but the
    directory sits under a home directory.

    Args:
        directory: The pretend account directory.

    Returns:
        One row per entry, sorted, a directory carrying no size or digest.
    """
    rows: list[tuple[str, int, int, str]] = []
    for entry in directory.rglob("*"):
        name, stat = entry.relative_to(directory).as_posix(), entry.stat()
        if entry.is_file():
            digest = hashlib.sha256(entry.read_bytes()).hexdigest()
            rows.append((name, stat.st_size, stat.st_mtime_ns, digest))
        else:
            rows.append((name, 0, stat.st_mtime_ns, ""))
    return tuple(sorted(rows))


def warnings_render_none_of(model: world.WorldModel | None, fragments: tuple[str, ...]) -> bool:
    """Whether no warning the model carries renders any of ``fragments``.

    A helper so the rendered text lives in THIS frame, which holds no
    assertion, and never in a test's frame at an assert.

    Args:
        model: The world handed up, or None.
        fragments: Text that must not appear - file names and their directory.

    Returns:
        True when no warning renders any fragment.
    """
    rendered = "" if model is None else "".join(repr(warning) for warning in model.warnings)
    return all(fragment not in rendered for fragment in fragments)


def plant_the_defect(account: Path) -> tuple[Path, Path]:
    """Plant a re-encoded newest save over a readable older one.

    Args:
        account: The pretend account directory, under tmp_path.

    Returns:
        The newest and the older save.
    """
    newest = plant(account / "Newest.sav", reencoded_levelled_save(), BASE_SECONDS + 60)
    older = plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    return newest, older


def test_an_objects_stage_refusal_by_the_real_reader_falls_back(tmp_path: Path) -> None:
    """No injected seam and no fake refusal: the object reader itself refuses the newest."""
    newest, older = plant_the_defect(tmp_path / "pretend-account")
    with pytest.raises(world.WorldLoadError) as direct:
        world.load_world(newest)
    refusal = (direct.value.stage, direct.value.cause_type)
    assert refusal == (world.STAGE_OBJECTS, "ObjectFormatError")
    older_records = len(world.load_world(older).objects.records)

    model = providers.SaveWorldProvider(tmp_path / "pretend-account").world()

    present = model is not None
    assert present, "the default wiring did not fall back past an objects-stage refusal"
    records = 0 if model is None else len(model.objects.records)
    assert records == older_records
    subjects = subjects_of(model)
    assert subjects == [NEWER_OBJECTS_SUBJECT]
    name_free = warnings_render_none_of(
        model, ("Newest", "Older", "pretend-account", tmp_path.name, str(tmp_path))
    )
    assert name_free, "a warning rendered a save name or its directory"


def test_the_fallback_writes_nothing_into_the_save_directory(tmp_path: Path) -> None:
    """Never write to a save directory - not a copy, a marker, a rename or a touch."""
    account = tmp_path / "pretend-account"
    plant_the_defect(account)
    before = directory_state(account)

    answers = [providers.SaveWorldProvider(account).world() for _ in range(CALLS)]

    served = all(answer is not None for answer in answers)
    assert served, "the walk never got past the refusal, so it graded nothing"
    unchanged = directory_state(account) == before
    assert unchanged, "the fallback walk changed the save directory"


def test_the_directory_probe_sees_a_write(tmp_path: Path) -> None:
    """The control: the probe the no-write test trusts does see each kind of write."""
    account = tmp_path / "pretend-account"
    newest, _older = plant_the_defect(account)
    before = directory_state(account)

    plant(account / "Marker.tmp", b"", BASE_SECONDS)
    added = directory_state(account) != before
    (account / "Marker.tmp").unlink()
    plant(newest, newest.read_bytes(), BASE_SECONDS + 61)
    touched = directory_state(account) != before
    plant(newest, reencoded_levelled_save()[:-1], BASE_SECONDS + 60)
    rewritten = directory_state(account) != before

    assert (added, touched, rewritten) == (True, True, True)
