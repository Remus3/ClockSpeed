"""The world provider falls back past a save the reader refuses, and says so.

THE DEFECT. ``SaveWorldProvider`` resolved the newest save and stopped there.
The newest file in the operator's save directory was a save re-encoded by a
third-party tool, which the object reader refuses - correctly - and the
companion answered "no world" for a directory holding dozens of readable
saves. Non-negotiable 7: unknown content is flagged and skipped, never fatal.

WHAT IS GRADED, on synthetic bytes in ``tmp_path`` with NO real save and NO
game install - the install's property map is replaced by "none found" for every
arm, so nothing here reads the install either:

a. A refused newest save falls back to the next one, and the world handed up
   carries the ``newer-save-refused`` flag.
b. A refusal that is the reader's verdict on the save's own BYTES is
   remembered by identity, so it is not copied and parsed again on every call,
   while a REWRITTEN refused save is tried again.
c. Nothing readable still answers None.
d. The default wiring ranks the account directory through ``workdir`` and
   loads through the real reader.
e. The real defect's shape end to end, and the save directory is left exactly
   as it was found - its own entry included.
f. A failure that is NOT about the save's bytes - the install's property map
   failing to read, a save the game is still writing - is never remembered
   against the save and never falls back: the next call tries the newest again.
g. No cap: however many newer saves are refused, the newest readable one is
   served, and each file is parsed at most once per identity.
h. A flagged world is the loaded world with its own warnings first, the flag
   last, and every other field carried.
i. ``GET /api/world`` serves the flag with no time and no digit in its subject
   or detail, and its whole body is byte-identical whatever the refused save
   is called and whenever it was written - recent times included, so a
   mutant that fires only on a fresh file is measured too.
j. A failure that is no verdict MERGES into the memo rather than replacing it:
   every remembered verdict on a file still ranked with an unchanged identity
   survives, a file gone from the ranking is dropped, and nothing the
   provider holds outgrows the ranking.
k. Only the refused newest save's OWN world is fallen back to when its world
   token is known; with no readable save of that world the world is refused.
   A newest save refused before its world could be read serves the newest
   readable save under a DISTINCT flag saying the world may be another one,
   and no world token and no world name reaches a flag, a message or the wire.
l. A refused save leaves no work copy behind in the work root.
m. The memo holds no exception the reader raised, and a remembered verdict is
   raised again with no cause and no context - nothing save-derived rides
   along in either chain.

THE BEHAVIOURAL ARMS DRIVE ONLY ENTRY POINTS THAT EXISTED BEFORE THE FALLBACK -
``SaveWorldProvider(account_dir, load=...)``, ``world.load_world`` and the route
table - and spell the served code as the wire does, so against the pre-fallback
tree they fail on what they observe rather than on a missing name.

EVERY ASSERTION IS ON A SCALAR BOUND TO A LOCAL. A ``tmp_path`` lives under a
home directory, so no assertion renders a path.
"""

from __future__ import annotations

import gc
import hashlib
import os
import re
import time
import weakref
from dataclasses import fields, is_dataclass
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.save import usmap, workdir, world
from clockspeed.save.header import masked_token
from clockspeed.surface import providers, server
from clockspeed.surface.api import contract, routes
from clockspeed.surface.api import world as endpoint
from tests.save import synthetic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from pathlib import Path

#: The served warning code, spelled as the wire spells it.
NEWER_SAVE_REFUSED: Final = "newer-save-refused"

#: The subject the object reader's refusal of the re-encoded shape carries.
OBJECTS_SUBJECT: Final = "objects.ObjectFormatError"

#: The save versions of the two levelled corpus fixtures - which world is which.
NEWEST_VERSION: Final = 60
OLDER_VERSION: Final = 36

#: A walk that tried two saves, or a save loaded twice.
TWO_LOADS: Final = 2

#: 2020-09-13T12:26:40Z, a whole second.
BASE_SECONDS: Final = 1_600_000_000

#: How many times each arm asks the provider.
CALLS: Final = 3

#: How many refused saves the no-cap arms plant above the readable one. More
#: than the cap of three the first cut carried, so a cap reddens them.
MANY_REFUSED: Final = 10

#: How many body bytes the synthetic re-encoded save is short of the intact
#: levelled body. INCIDENTAL TO THE VERDICT - see
#: :func:`reencoded_levelled_save` for what the reader actually refuses.
BODY_SHORTFALL: Final = 16

#: The planted modification time of the arm (i) canary, 2033-05-18T03:33:20Z.
CANARY_SECONDS: Final = 2_000_000_000

#: The served code of a world read past a newest save whose world is unknown,
#: spelled as the wire spells it.
NEWEST_UNIDENTIFIED: Final = "newest-save-unidentified"

#: The subject of the default wiring's refusal of a few bytes that are no save.
HEADER_SUBJECT: Final = "header.UnsupportedHeaderVersionError"

#: A second invented world, so two worlds can share one account directory.
OTHER_WORLD: Final = synthetic.SYNTHETIC_WORLD_TOKEN_B

#: Invented 22-character world tokens and world names for the arm (k) and (m)
#: canaries. None of them can appear anywhere the walk renders.
CANARY_TOKEN_REFUSED: Final = "ClockspeedCanaryQzxRfZ"  # noqa: S105
CANARY_TOKEN_OTHER: Final = "ClockspeedCanaryQzxOtW"  # noqa: S105
CANARY_SESSIONS: Final = ("CanaryRefusedQzx", "CanaryOtherQzx", "CanaryServedQzx")

#: A day, in seconds - the arm (i) recent-time pair sits inside one month.
DAY_SECONDS: Final = 86_400


@pytest.fixture(autouse=True)
def isolated_work_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Send workdir's copies under tmp_path so no test writes into the repo."""
    root = tmp_path / "work-root"
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(root))
    return root


@pytest.fixture(autouse=True)
def no_installed_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader finds no property map, so no arm reads this machine's install."""
    monkeypatch.setattr(world, "cached_usmap", lambda: None)


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


def reencoded_levelled_save(token: str = synthetic.SYNTHETIC_WORLD_TOKEN, **header: str) -> bytes:
    """A synthetic save whose header reads and whose body the object reader refuses.

    The real defect's STAGE on synthetic bytes: a header that parses over a
    body the object reader refuses with ``ObjectFormatError``, the refusal the
    real file drew - not a header that never parsed. Built from the corpus
    fixture, never from a real save.

    WHAT THE READER REFUSES IS THE MISSING LENGTH PREFIX, NOT THE SHORTFALL.
    The body is framed WITHOUT the length prefix its header version carries,
    so the reader takes the body's first word for that prefix and refuses the
    walk. The :data:`BODY_SHORTFALL` cut is incidental: MEASURED, the same cut
    with the prefix restored draws ``ObjectTruncatedError`` instead, so the
    cut alone is not what any arm here observes.

    Args:
        token: The invented world token the header carries.
        header: Further header overrides - a session name, for a canary.

    Returns:
        The save bytes.
    """
    fixture = synthetic.SAVE_LEVELLED_V36
    body = fixture.body[: len(fixture.body) - BODY_SHORTFALL]
    framed = synthetic.build_chunks(body, framing=fixture.framing)
    return relabelled_header(fixture, token, **header) + framed


def relabelled_header(fixture: synthetic.SyntheticSave, token: str, **header: str) -> bytes:
    """The fixture's header rebuilt to carry ``token`` and any header overrides.

    Args:
        fixture: The corpus fixture whose versions the header keeps.
        token: The invented world token.
        header: Further header overrides.

    Returns:
        The header bytes, ending before the chunk magic.
    """
    return synthetic.build_header(
        header_version=fixture.header_version,
        save_version=fixture.save_version,
        world_token=token,
        **header,  # type: ignore[arg-type]
    )


def relabelled(fixture: synthetic.SyntheticSave, token: str, **header: str) -> bytes:
    """The whole fixture, readable, as a save of the world ``token`` names.

    Args:
        fixture: The corpus fixture.
        token: The invented world token.
        header: Further header overrides.

    Returns:
        The save bytes.
    """
    return relabelled_header(fixture, token, **header) + fixture.blob[fixture.chunk_offset :]


def fallback_flags(model: world.WorldModel | None) -> list[tuple[str, str, int]]:
    """Every flag of either fallback code as (code, subject, count), in order."""
    if model is None:
        return []
    return [
        (warning.code, warning.subject or "", warning.count)
        for warning in model.warnings
        if warning.code in (NEWER_SAVE_REFUSED, NEWEST_UNIDENTIFIED)
    ]


def is_world(model: world.WorldModel | None, token: str) -> bool:
    """Whether the world handed up is the one ``token`` names."""
    return model is not None and model.token == token


def flags_of(model: world.WorldModel | None) -> list[tuple[str, int]]:
    """Each fallback flag the model carries as (subject, count), in order."""
    if model is None:
        return []
    return [
        (warning.subject or "", warning.count)
        for warning in model.warnings
        if warning.code == NEWER_SAVE_REFUSED
    ]


def version_of(model: world.WorldModel | None) -> int | None:
    """Which corpus world was handed up, by its save version, or None."""
    return None if model is None else model.header.save_version


def plant_pair(account: Path, *, newest: bytes) -> tuple[Path, Path]:
    """Plant ``newest`` one minute after a readable older save.

    Args:
        account: The pretend account directory, under tmp_path.
        newest: The newest save's synthetic bytes.

    Returns:
        The newest and the older save.
    """
    older = plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    return plant(account / "Newest.sav", newest, BASE_SECONDS + 60), older


class CountingLoad:
    """The real loader, counted per file, refusing the names it is told to.

    Attributes:
        calls: File name to how many times it was loaded.
        returned: File name to the world the real loader last handed back.
    """

    def __init__(self, refusals: dict[str, BaseException] | None = None) -> None:
        """Remember which file names refuse, and with what.

        Args:
            refusals: File name to the exception a load of it raises.
        """
        self.calls: dict[str, int] = {}
        self.returned: dict[str, world.WorldModel] = {}
        self.refusals: dict[str, BaseException] = dict(refusals or {})

    def __call__(self, path: Path) -> world.WorldModel:
        """Raise the planted refusal for ``path``, or load it for real."""
        self.calls[path.name] = self.calls.get(path.name, 0) + 1
        refusal = self.refusals.get(path.name)
        if refusal is not None:
            raise refusal
        model = world.load_world(path)
        self.returned[path.name] = model
        return model

    @property
    def total(self) -> int:
        """Every load, across every file."""
        return sum(self.calls.values())


def objects_refusal() -> world.WorldLoadError:
    """The refusal the re-encoded file draws from the real object reader."""
    return world.WorldLoadError(world.STAGE_OBJECTS, "ObjectFormatError")


# ---------------------------------------------------------------------------
# a. fall back, and flag it
# ---------------------------------------------------------------------------


def test_a_refused_newest_save_falls_back_and_is_flagged(tmp_path: Path) -> None:
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: objects_refusal()})

    model = providers.SaveWorldProvider(account, load=load).world()

    served = version_of(model)
    assert served == OLDER_VERSION, "a readable older save was not handed up"
    flags = flags_of(model)
    assert flags == [(OBJECTS_SUBJECT, 1)]


# ---------------------------------------------------------------------------
# b. a verdict on the bytes is remembered by identity, retried when rewritten
# ---------------------------------------------------------------------------


def test_a_refused_save_is_not_parsed_again_on_every_call(tmp_path: Path) -> None:
    account = tmp_path / "pretend-account"
    newest, older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: objects_refusal()})
    provider = providers.SaveWorldProvider(account, load=load)

    answers = [provider.world() for _ in range(CALLS)]

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == 1, "an unchanged refused save was parsed again"
    fallback_loads = load.calls.get(older.name, 0)
    assert fallback_loads == 1, "an unchanged fallback save was parsed again"
    flagged = [flags_of(answer) for answer in answers]
    assert flagged == [[(OBJECTS_SUBJECT, 1)]] * CALLS


def test_a_refused_save_arriving_does_not_re_parse_the_remembered_world(
    tmp_path: Path,
) -> None:
    """The world already in memory IS the fallback; refusing a newer file must not drop it."""
    account = tmp_path / "pretend-account"
    older = plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    load = CountingLoad({"Newest.sav": objects_refusal()})
    provider = providers.SaveWorldProvider(account, load=load)
    provider.world()

    plant(account / "Newest.sav", reencoded_levelled_save(), BASE_SECONDS + 60)
    model = provider.world()

    fallback_loads = load.calls.get(older.name, 0)
    assert fallback_loads == 1, "the remembered world was parsed again behind a refusal"
    flags = flags_of(model)
    assert flags == [(OBJECTS_SUBJECT, 1)]


def test_a_rewritten_refused_save_is_tried_again(tmp_path: Path) -> None:
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: objects_refusal()})
    provider = providers.SaveWorldProvider(account, load=load)
    provider.world()

    plant(newest, reencoded_levelled_save() + b"longer", BASE_SECONDS + 90)
    provider.world()

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == TWO_LOADS, "a rewritten save was judged by its old refusal"


def test_a_refused_save_the_game_has_replaced_is_read(tmp_path: Path) -> None:
    """The flag goes when its cause goes: a newest save that now loads wins."""
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: objects_refusal()})
    provider = providers.SaveWorldProvider(account, load=load)
    provider.world()

    load.refusals.clear()
    plant(newest, synthetic.SAVE_LEVELLED_V60.blob, BASE_SECONDS + 120)
    model = provider.world()

    served = version_of(model)
    assert served == NEWEST_VERSION
    flags = flags_of(model)
    assert flags == []
    newest_loads = load.calls.get(newest.name, 0)
    assert newest_loads == TWO_LOADS


# ---------------------------------------------------------------------------
# c. nothing readable
# ---------------------------------------------------------------------------


def test_every_save_refused_answers_none(tmp_path: Path) -> None:
    account = tmp_path / "pretend-account"
    newest, older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: objects_refusal(), older.name: objects_refusal()})

    absent = providers.SaveWorldProvider(account, load=load).world() is None

    assert absent, "a directory of refused saves handed up a world"


def test_find_save_and_find_saves_together_are_refused() -> None:
    """Two rankings for one provider is a wiring bug, refused at construction."""
    with pytest.raises(ValueError, match="find_save"):
        providers.SaveWorldProvider(find_save=lambda _dir: None, find_saves=lambda _dir: ())


# ---------------------------------------------------------------------------
# d. the default wiring
# ---------------------------------------------------------------------------


def test_the_default_wiring_ranks_through_workdir_and_falls_back(tmp_path: Path) -> None:
    """No injected seam: workdir ranks the directory and the real reader refuses.

    The newest file is refused at the HEADER, so its world is never read and
    the world served past it is flagged as possibly another one - arm (k).
    """
    account = tmp_path / "pretend-account"
    plant_pair(account, newest=b"not a save the game wrote")

    model = providers.SaveWorldProvider(account).world()

    served = version_of(model)
    assert served == OLDER_VERSION, "the default wiring did not fall back"
    flags = fallback_flags(model)
    assert flags == [(NEWEST_UNIDENTIFIED, HEADER_SUBJECT, 1)]


# ---------------------------------------------------------------------------
# e. the real defect's shape end to end, and the save directory untouched
# ---------------------------------------------------------------------------


def directory_state(directory: Path) -> tuple[tuple[str, int, int, str], ...]:
    """The directory's OWN entry, then every entry under it, by name, size, mtime, digest.

    THE DIRECTORY'S OWN ROW IS THE POINT. A file created and deleted again, or
    a save renamed away and back, leaves every entry under the directory as it
    was - only the directory's own modification time records that its listing
    changed. A snapshot of the entries alone is blind to both.

    Compared whole and never rendered: the names are synthetic, but the
    directory sits under a home directory.

    Args:
        directory: The pretend account directory.

    Returns:
        The directory's own row first - name ``.``, size 0 - then one row per
        entry, sorted, a sub-directory carrying no size or digest.
    """
    rows: list[tuple[str, int, int, str]] = []
    for entry in directory.rglob("*"):
        name, stat = entry.relative_to(directory).as_posix(), entry.stat()
        if entry.is_file():
            digest = hashlib.sha256(entry.read_bytes()).hexdigest()
            rows.append((name, stat.st_size, stat.st_mtime_ns, digest))
        else:
            rows.append((name, 0, stat.st_mtime_ns, ""))
    own = (".", 0, directory.stat().st_mtime_ns, "")
    return (own, *sorted(rows))


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


def test_an_objects_stage_refusal_by_the_real_reader_falls_back(tmp_path: Path) -> None:
    """No injected seam and no fake refusal: the object reader itself refuses the newest."""
    account = tmp_path / "pretend-account"
    newest, older = plant_pair(account, newest=reencoded_levelled_save())
    with pytest.raises(world.WorldLoadError) as direct:
        world.load_world(newest)
    refusal = (direct.value.stage, direct.value.cause_type)
    assert refusal == (world.STAGE_OBJECTS, "ObjectFormatError")
    older_records = len(world.load_world(older).objects.records)

    model = providers.SaveWorldProvider(account).world()

    records = 0 if model is None else len(model.objects.records)
    assert records == older_records, "the default wiring did not fall back"
    flags = flags_of(model)
    assert flags == [(OBJECTS_SUBJECT, 1)]
    name_free = warnings_render_none_of(
        model, ("Newest", "Older", "pretend-account", tmp_path.name, str(tmp_path))
    )
    assert name_free, "a warning rendered a save name or its directory"


def test_the_fallback_writes_nothing_into_the_save_directory(tmp_path: Path) -> None:
    """Never write to a save directory - not a copy, a marker, a rename or a touch."""
    account = tmp_path / "pretend-account"
    plant_pair(account, newest=reencoded_levelled_save())
    before = directory_state(account)

    answers = [providers.SaveWorldProvider(account).world() for _ in range(CALLS)]

    served = [version_of(answer) for answer in answers]
    assert served == [OLDER_VERSION] * CALLS, "the walk never got past the refusal"
    unchanged = directory_state(account) == before
    assert unchanged, "the fallback walk changed the save directory"


def test_the_directory_probe_sees_a_write(tmp_path: Path) -> None:
    """The control: the probe the no-write test trusts sees every kind of write.

    The last two are the shapes that leave every entry as it was found: a file
    created and deleted again, and a save renamed away and back. Only the
    directory's own row can see them.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    original = newest.read_bytes()

    before = directory_state(account)
    plant(account / "Marker.tmp", b"", BASE_SECONDS)
    added = directory_state(account) != before
    (account / "Marker.tmp").unlink()

    before = directory_state(account)
    plant(newest, original, BASE_SECONDS + 61)
    touched = directory_state(account) != before

    before = directory_state(account)
    plant(newest, original[:-1], BASE_SECONDS + 61)
    rewritten = directory_state(account) != before

    before = directory_state(account)
    time.sleep(0.05)
    (account / "Scratch.tmp").write_bytes(b"")
    (account / "Scratch.tmp").unlink()
    created_and_deleted = directory_state(account) != before

    before = directory_state(account)
    time.sleep(0.05)
    away = newest.with_name("Away.sav")
    newest.rename(away)
    away.rename(newest)
    renamed_and_back = directory_state(account) != before

    seen = (added, touched, rewritten, created_and_deleted, renamed_and_back)
    assert seen == (True, True, True, True, True)


# ---------------------------------------------------------------------------
# f. a failure that is not about the save's bytes is never held against it
# ---------------------------------------------------------------------------


class FlakyMapping:
    """A stand-in for the install's mapping that fails while told to.

    Attributes:
        failing: Whether the next read fails.
        failures_left: How many reads fail before ``failing`` turns itself off,
            or None to fail until told otherwise.
    """

    def __init__(self, *, failures_left: int | None) -> None:
        """Start failing.

        Args:
            failures_left: Reads that fail before it recovers by itself, or
                None to fail until ``failing`` is cleared.
        """
        self.failing = True
        self.failures_left = failures_left

    def __call__(self) -> None:
        """Fail as told, else find no mapping - absence is not an error."""
        if not self.failing:
            return
        if self.failures_left is not None:
            self.failures_left -= 1
            if self.failures_left <= 0:
                self.failing = False
        raise usmap.UsmapError


def test_a_mapping_that_fails_once_is_retried_and_never_pinned_on_the_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One transient install-side failure costs one call, never the newest save.

    The mapping lives in the INSTALL, so its failure is no verdict on any save:
    remembering it against the newest save served the older one for as long
    as nothing changed on disk.
    """
    account = tmp_path / "pretend-account"
    plant_pair(account, newest=synthetic.SAVE_LEVELLED_V60.blob)
    monkeypatch.setattr(world, "cached_usmap", FlakyMapping(failures_left=1))
    provider = providers.SaveWorldProvider(account)

    served = [version_of(provider.world()) for _ in range(4)]

    assert served == [None, NEWEST_VERSION, NEWEST_VERSION, NEWEST_VERSION]


def test_a_mapping_that_fails_for_a_whole_call_then_recovers_serves_the_newest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mapping down for one whole call is not remembered against any save."""
    account = tmp_path / "pretend-account"
    plant_pair(account, newest=synthetic.SAVE_LEVELLED_V60.blob)
    mapping = FlakyMapping(failures_left=None)
    monkeypatch.setattr(world, "cached_usmap", mapping)
    provider = providers.SaveWorldProvider(account)

    first = version_of(provider.world())
    mapping.failing = False
    later = [version_of(provider.world()) for _ in range(2)]

    served = [first, *later]
    assert served == [None, NEWEST_VERSION, NEWEST_VERSION]


def test_a_copy_failure_is_retried_rather_than_remembered(tmp_path: Path) -> None:
    """A save the game is still writing is not skipped, and is tried again next call."""
    account = tmp_path / "pretend-account"
    newest, older = plant_pair(account, newest=synthetic.SAVE_LEVELLED_V60.blob)
    busy = world.WorldLoadError(world.STAGE_COPY, "SourceUnreadableError")
    load = CountingLoad({newest.name: busy})
    provider = providers.SaveWorldProvider(account, load=load)

    first = version_of(provider.world())
    load.refusals.clear()
    second = version_of(provider.world())

    served = [first, second]
    assert served == [None, NEWEST_VERSION], "a busy newest save was skipped or remembered"
    newest_loads = load.calls.get(newest.name, 0)
    assert newest_loads == TWO_LOADS
    older_loads = load.calls.get(older.name, 0)
    assert older_loads == 0, "the walk fell back past a save that was merely busy"


@pytest.mark.parametrize("stage", [world.STAGE_COPY, world.STAGE_USMAP])
def test_a_failure_that_is_no_verdict_is_never_remembered_whatever_its_cause_names(
    tmp_path: Path, stage: str
) -> None:
    """The STAGE decides alone: a reader's class name on a copy or usmap failure changes nothing.

    The cause-type check would refuse a copy or mapping class name anyway, so
    this pins the stage gate by itself - a failure of the environment or the
    install is retried, never held against the save, whatever its cause says.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=synthetic.SAVE_LEVELLED_V60.blob)
    load = CountingLoad({newest.name: world.WorldLoadError(stage, "ObjectFormatError")})
    provider = providers.SaveWorldProvider(account, load=load)

    first = version_of(provider.world())
    load.refusals.clear()
    second = version_of(provider.world())

    served = [first, second]
    assert served == [None, NEWEST_VERSION], "a failure that is no verdict was remembered"


# ---------------------------------------------------------------------------
# g. no cap, and each file parsed at most once per identity
# ---------------------------------------------------------------------------


def plant_many_refused(account: Path, count: int) -> list[Path]:
    """Plant ``count`` re-encoded saves, all newer than one readable older save.

    Args:
        account: The pretend account directory, under tmp_path.
        count: How many refused saves.

    Returns:
        The refused saves, newest first.
    """
    plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    payload = reencoded_levelled_save()
    return [
        plant(account / f"Refused{index:02d}.sav", payload, BASE_SECONDS + 600 - index)
        for index in range(count)
    ]


def test_every_refused_newer_save_is_walked_past_however_many(tmp_path: Path) -> None:
    """No cap leaves the world None while a readable save remains."""
    account = tmp_path / "pretend-account"
    plant_many_refused(account, MANY_REFUSED)

    model = providers.SaveWorldProvider(account).world()

    served = version_of(model)
    assert served == OLDER_VERSION, "a readable save was left unread behind refused ones"
    flags = flags_of(model)
    assert flags == [(OBJECTS_SUBJECT, MANY_REFUSED)]


def test_each_save_is_parsed_once_on_the_first_request_and_never_again(
    tmp_path: Path,
) -> None:
    """The first request pays one parse per file it walks; later ones pay none."""
    account = tmp_path / "pretend-account"
    refused = plant_many_refused(account, MANY_REFUSED)
    load = CountingLoad()
    provider = providers.SaveWorldProvider(account, load=load)

    first = version_of(provider.world())
    first_loads = load.total
    once_each = sorted(set(load.calls.values()))
    later = [version_of(provider.world()) for _ in range(CALLS)]
    later_loads = load.total - first_loads

    served = [first, *later]
    assert served == [OLDER_VERSION] * (CALLS + 1)
    assert first_loads == len(refused) + 1, "the first request did not walk every save once"
    assert once_each == [1], "a file was parsed twice on the first request"
    assert later_loads == 0, "an unchanged save was parsed again on a later request"


# ---------------------------------------------------------------------------
# h. a flagged world is the loaded world, flag last, every field carried
# ---------------------------------------------------------------------------


def test_a_flagged_world_keeps_its_own_warnings_first_and_the_flag_last(
    tmp_path: Path,
) -> None:
    account = tmp_path / "pretend-account"
    newest, older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad()

    model = providers.SaveWorldProvider(account, load=load).world()

    loaded = load.returned.get(older.name)
    assert loaded is not None, "the older save was never loaded, so nothing fell back"
    own_count = len(loaded.warnings)
    assert own_count > 0, "the loaded world carried no warning, so this grades nothing"
    total = 0 if model is None else len(model.warnings)
    assert total == own_count + 1
    kept = model is not None and model.warnings[:own_count] == loaded.warnings
    assert kept, "the flagged world lost or reordered the loaded world's own warnings"
    last_code = "" if model is None else model.warnings[-1].code
    assert last_code == NEWER_SAVE_REFUSED, "the flag is not last"
    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == 1


def test_a_flagged_world_carries_every_other_field_of_the_world_it_copies(
    tmp_path: Path,
) -> None:
    """Field by field, by identity - so a field reset to its default reddens."""
    account = tmp_path / "pretend-account"
    _newest, older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad()

    model = providers.SaveWorldProvider(account, load=load).world()

    loaded = load.returned.get(older.name)
    assert loaded is not None, "the older save was never loaded, so nothing fell back"
    names = [field.name for field in fields(world.WorldModel) if field.name != "warnings"]
    differing = [
        name for name in names if model is None or getattr(model, name) is not getattr(loaded, name)
    ]
    assert differing == []
    populated = (
        loaded.properties is not world.EMPTY_WORLD_PROPERTIES
        and loaded.parents is not world.EMPTY_WORLD_PARENTS
    )
    assert populated, "the fixture's properties or parents are the defaults, so this grades less"


class _ReaderLocal:
    """Stands in for what a reader frame holds - in production, the inflated body."""


def test_a_remembered_refusal_keeps_no_reader_frame_alive(tmp_path: Path) -> None:
    """The memo keeps the refusal, never the frames it unwound through.

    A traceback holds every frame a refusal unwound through, and a reader
    frame can hold a whole save's inflated body. The planted loader keeps a
    local in the frame that raises, and the arm asserts that local is gone
    once the call returns, while the refusal itself is still remembered.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    held: list[weakref.ref[_ReaderLocal]] = []
    calls = {"refused": 0}

    def load(path: Path) -> world.WorldModel:
        if path.name != newest.name:
            return world.load_world(path)
        calls["refused"] += 1
        local = _ReaderLocal()
        held.append(weakref.ref(local))
        try:
            raise ValueError
        except ValueError as exc:
            raise world.WorldLoadError(world.STAGE_OBJECTS, "ObjectFormatError") from exc

    provider = providers.SaveWorldProvider(account, load=load)
    first = version_of(provider.world())
    gc.collect()
    alive = sum(1 for reference in held if reference() is not None)
    second = version_of(provider.world())

    served = [first, second]
    assert served == [OLDER_VERSION, OLDER_VERSION]
    assert alive == 0, "a remembered refusal kept the frame that raised it alive"
    refused_loads = calls["refused"]
    assert refused_loads == 1, "the refusal was not remembered, so this grades nothing"


# ---------------------------------------------------------------------------
# i. GET /api/world serves the flag with nothing filesystem-derived in it
# ---------------------------------------------------------------------------


class _NoRegistry:
    """A registry provider on a machine with no game installed. Opens nothing."""

    def registry(self) -> None:
        """The normalized registry.

        Returns:
            None, always.
        """
        return


def served_flags(wire: Mapping[str, object]) -> list[dict[str, object]]:
    """The fallback flags of one ``/api/world`` body.

    Args:
        wire: The decoded payload.

    Returns:
        Every served warning whose code is the fallback code.
    """
    data = wire.get("data")
    warnings = data.get("warnings", []) if isinstance(data, dict) else []
    return [
        warning
        for warning in warnings
        if isinstance(warning, dict) and warning.get("code") == NEWER_SAVE_REFUSED
    ]


def canary_fragments(seconds: int) -> tuple[str, ...]:
    """Every spelling of the planted modification time a subject could carry.

    Args:
        seconds: The planted time.

    Returns:
        The spellings.
    """
    moment = time.gmtime(seconds)
    return (
        str(seconds),
        str(seconds * 1_000_000_000),
        time.strftime("%Y-%m-%d", moment),
        time.strftime("%H-%M-%S", moment),
        time.strftime("%H:%M:%S", moment),
        "mtime",
    )


def test_get_api_world_serves_the_flag_with_no_time_and_no_digit(tmp_path: Path) -> None:
    """The flag says WHY a save was skipped, never WHEN it was written.

    A save's write time is when the operator last played - behavioural data the
    endpoint withholds from the header for exactly that reason - and a time to
    the second singles one file out of a listing. WHAT THIS ARM MEASURES: the
    served subject is exactly the stage and the cause, the subject and the
    detail carry no digit, and no spelling of the planted time is anywhere in
    the body. The whole-body claim - nothing derived from the refused file's
    name or write time, in any field - is the next arm's, by difference.
    """
    account = tmp_path / "pretend-account"
    plant(account / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    plant(account / "Newest.sav", reencoded_levelled_save(), CANARY_SECONDS)
    provider = providers.SaveWorldProvider(account)
    table = server.routing(routes.build_routes(provider, _NoRegistry()))

    response = table[endpoint.ENDPOINT][routes.METHOD_GET]({})

    status = response.http_status
    assert status == contract.HTTP_OK, "no world was served past the refused save"
    wire = contract.encode(response.payload).decode("ascii")
    flags = served_flags(response.payload)
    subjects = [flag.get("subject") for flag in flags]
    assert subjects == [OBJECTS_SUBJECT]
    served_text = [str(flag.get(key)) for flag in flags for key in ("subject", "detail")]
    digit_free = all(re.search(r"\d", text) is None for text in served_text)
    assert digit_free, "a served flag carries a digit"
    canaries = sum(1 for fragment in canary_fragments(CANARY_SECONDS) if fragment in wire)
    assert canaries == 0, "the body carries a spelling of the refused save's write time"


def get_api_world(account: Path) -> tuple[int, bytes]:
    """One ``GET /api/world`` against a fresh provider over ``account``.

    Args:
        account: The pretend account directory.

    Returns:
        The HTTP status and the encoded body.
    """
    provider = providers.SaveWorldProvider(account)
    table = server.routing(routes.build_routes(provider, _NoRegistry()))
    response = table[endpoint.ENDPOINT][routes.METHOD_GET]({})
    return response.http_status, contract.encode(response.payload)


def test_the_served_body_is_the_same_whatever_the_refused_save_is_called_or_when_written(
    tmp_path: Path,
) -> None:
    """Two directories holding the same bytes under other names and other RECENT times.

    BY DIFFERENCE, SO NO SPELLING HAS TO BE GUESSED. A value derived from a
    file's name or write time - in any field, spelled in digits, letters or
    anything else - makes the two bodies differ. Both directories' times sit
    within the last month, so a derivation that fires only for a fresh file
    fires on both sides here, where the 2020 and 2033 fixtures above never
    trigger it.
    """
    now = int(time.time())
    first = tmp_path / "first-account"
    plant(first / "Older.sav", synthetic.SAVE_LEVELLED_V36.blob, now - 2 * DAY_SECONDS)
    plant(first / "Newest.sav", reencoded_levelled_save(), now - 1)
    second = tmp_path / "second-account"
    plant(
        second / "Archive_autosave_2.sav",
        synthetic.SAVE_LEVELLED_V36.blob,
        now - 25 * DAY_SECONDS,
    )
    plant(second / "Fresh_autosave_0.sav", reencoded_levelled_save(), now - 20 * DAY_SECONDS)

    first_status, first_body = get_api_world(first)
    second_status, second_body = get_api_world(second)

    statuses = (first_status, second_status)
    assert statuses == (contract.HTTP_OK, contract.HTTP_OK), "no world was served past the refusal"
    same = first_body == second_body
    assert same, "the served body depends on a refused save's name or write time"
    wire = first_body.decode("ascii")
    canaries = sum(1 for fragment in canary_fragments(now - 1) if fragment in wire)
    assert canaries == 0, "the body carries a spelling of the refused save's write time"


# ---------------------------------------------------------------------------
# j. a failure that is no verdict merges into the memo, never replaces it
# ---------------------------------------------------------------------------


def test_a_transient_failure_keeps_every_remembered_verdict(tmp_path: Path) -> None:
    """One copy failure on a NEW newest save costs one load, never a re-parse of the rest.

    The four calls of the refuting repro: the first walks every save, the
    second walks none, the third meets a new newest save a writer holds open,
    and the fourth - the writer gone, the reader refusing the new file - pays
    for the new file alone. A memo REPLACED by the third call's walk, which
    met no verdict, re-parsed every unchanged file on the fourth.
    """
    account = tmp_path / "pretend-account"
    plant_many_refused(account, MANY_REFUSED)
    load = CountingLoad()
    provider = providers.SaveWorldProvider(account, load=load)

    provider.world()
    after_first = load.total
    provider.world()
    after_second = load.total
    fresh = plant(account / "Fresh.sav", reencoded_levelled_save(), BASE_SECONDS + 900)
    load.refusals[fresh.name] = world.WorldLoadError(world.STAGE_COPY, "SourceUnreadableError")
    third = version_of(provider.world())
    after_third = load.total
    del load.refusals[fresh.name]
    fourth_model = provider.world()
    after_fourth = load.total

    per_call = [
        after_first,
        after_second - after_first,
        after_third - after_second,
        after_fourth - after_third,
    ]
    assert per_call == [MANY_REFUSED + 1, 0, 1, 1], "an unchanged save was parsed again"
    assert third is None, "a newest save held open was skipped"
    fourth = version_of(fourth_model)
    assert fourth == OLDER_VERSION
    flags = flags_of(fourth_model)
    assert flags == [(OBJECTS_SUBJECT, MANY_REFUSED + 1)]


def test_a_save_gone_from_the_ranking_is_dropped_from_the_memo(tmp_path: Path) -> None:
    """Merging is bounded: a refused file that leaves the ranking leaves the memo.

    The file comes back byte for byte with its modification time restored -
    the SAME identity - so only a memo that kept the departed file's verdict
    can skip parsing it again.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    original = newest.read_bytes()
    load = CountingLoad()
    provider = providers.SaveWorldProvider(account, load=load)

    provider.world()
    newest.unlink()
    provider.world()
    plant(newest, original, BASE_SECONDS + 60)
    model = provider.world()

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == TWO_LOADS, "a verdict on a file no longer ranked was kept"
    flags = flags_of(model)
    assert flags == [(OBJECTS_SUBJECT, 1)]


def collection_sizes(holder: object) -> list[int]:
    """The size of every collection the provider holds as an attribute."""
    return [
        len(value)
        for value in vars(holder).values()
        if isinstance(value, dict | list | set | frozenset)
    ]


def test_the_memo_is_bounded_by_the_ranking(tmp_path: Path) -> None:
    """Whatever the provider remembers, it remembers per ranked file at most."""
    account = tmp_path / "pretend-account"
    refused = plant_many_refused(account, MANY_REFUSED)
    provider = providers.SaveWorldProvider(account)
    provider.world()
    for path in refused[1:]:
        path.unlink()

    provider.world()

    ranked = len(workdir.ranked_saves(account))
    largest = max(collection_sizes(provider), default=0)
    assert largest <= ranked, "the provider holds more entries than the ranking has files"


# ---------------------------------------------------------------------------
# k. the refused newest save's own world, or a flag saying it may be another
# ---------------------------------------------------------------------------


def test_a_refused_newest_save_falls_back_only_to_its_own_world(tmp_path: Path) -> None:
    """The newest save is world B, refused after its header was read: B is served, never A.

    A save of another world sits between them in the ranking. Serving it under
    a flag reading "read from an older save and may be behind the game" is
    false advice about a different world - non-negotiable 7, never silently
    wrong - and it is never even parsed.
    """
    account = tmp_path / "pretend-account"
    plant(
        account / "OlderB.sav",
        relabelled(synthetic.SAVE_LEVELLED_V36, OTHER_WORLD),
        BASE_SECONDS,
    )
    other = plant(account / "OtherA.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS + 30)
    plant(account / "NewestB.sav", reencoded_levelled_save(OTHER_WORLD), BASE_SECONDS + 60)
    load = CountingLoad()

    model = providers.SaveWorldProvider(account, load=load).world()

    own_world = is_world(model, OTHER_WORLD)
    assert own_world, "a refused newest save fell back to another world"
    other_loads = load.calls.get(other.name, 0)
    assert other_loads == 0, "another world's save was parsed during the walk"
    flags = fallback_flags(model)
    assert flags == [(NEWER_SAVE_REFUSED, OBJECTS_SUBJECT, 1)]


def test_no_readable_save_of_the_refused_newest_world_answers_none(tmp_path: Path) -> None:
    """With nothing of world B readable, world A is never served in its place."""
    account = tmp_path / "pretend-account"
    plant(account / "OtherA.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    plant(account / "NewestB.sav", reencoded_levelled_save(OTHER_WORLD), BASE_SECONDS + 60)
    provider = providers.SaveWorldProvider(account)

    answers = [provider.world() for _ in range(CALLS)]

    absent = [answer is None for answer in answers]
    assert absent == [True] * CALLS, "another world was served in place of the refused one"


def test_a_header_refusal_serves_the_newest_readable_save_under_the_distinct_flag(
    tmp_path: Path,
) -> None:
    """The newest save's world is unknown, so the newest readable save is served - and says so.

    Refusing outright would leave a dead dashboard after any header-format
    game update; serving silently, or under the "behind the game" flag, would
    claim a world the walk never identified. The world served here IS another
    one, which is exactly the case the flag exists to say may be true.
    """
    account = tmp_path / "pretend-account"
    plant(account / "OlderA.sav", synthetic.SAVE_LEVELLED_V36.blob, BASE_SECONDS)
    plant(
        account / "OtherB.sav",
        relabelled(synthetic.SAVE_LEVELLED_V36, OTHER_WORLD),
        BASE_SECONDS + 30,
    )
    plant(account / "Newest.sav", b"not a save the game wrote", BASE_SECONDS + 60)

    model = providers.SaveWorldProvider(account).world()

    newest_readable = is_world(model, OTHER_WORLD)
    assert newest_readable, "the newest readable save was not the one served"
    flags = fallback_flags(model)
    assert flags == [(NEWEST_UNIDENTIFIED, HEADER_SUBJECT, 1)]
    says_so = all(
        "could not be identified" in w.detail and "a different one" in w.detail
        for w in (model.warnings if model is not None else ())
        if w.code == NEWEST_UNIDENTIFIED
    )
    assert says_so, "the distinct flag does not say the world may be another one"


def canary_hits(texts: list[str]) -> int:
    """How many canary spellings appear across ``texts``.

    A helper so the rendered text lives in THIS frame, never in a test's frame
    at an assert.

    Args:
        texts: Everything rendered - flag reprs, messages, encoded bodies.

    Returns:
        The number of (text, canary) pairs that matched.
    """
    canaries = (
        CANARY_TOKEN_REFUSED,
        CANARY_TOKEN_OTHER,
        masked_token(CANARY_TOKEN_OTHER),
        *CANARY_SESSIONS,
    )
    return sum(1 for text in texts for canary in canaries if canary in text)


def flag_reprs(model: world.WorldModel | None) -> list[str]:
    """The repr of every warning the model carries."""
    return [] if model is None else [repr(warning) for warning in model.warnings]


def test_no_world_token_or_world_name_reaches_a_flag_a_message_or_the_wire(
    tmp_path: Path,
) -> None:
    """Three walks - fallen back, refused, unidentified - and not one canary rendered.

    The refused newest save and another world's save carry canary tokens and
    canary world names; the save served carries a canary world name too, which
    the wire never serves. The served world's own MASKED token is the one
    token-derived value the wire carries by design, so it is not a canary -
    which is why the unidentified walk serves that same world rather than the
    other one, whose masked token IS a canary in the fallen-back walk.
    """
    refused_name, other_name, served_name = CANARY_SESSIONS
    fallen = tmp_path / "fallen-back"
    served = plant(
        fallen / "Served.sav",
        relabelled(synthetic.SAVE_LEVELLED_V36, CANARY_TOKEN_REFUSED, session_name=served_name),
        BASE_SECONDS,
    )
    other = plant(
        fallen / "Other.sav",
        relabelled(synthetic.SAVE_LEVELLED_V36, CANARY_TOKEN_OTHER, session_name=other_name),
        BASE_SECONDS + 30,
    )
    newest = plant(
        fallen / "Newest.sav",
        reencoded_levelled_save(CANARY_TOKEN_REFUSED, session_name=refused_name),
        BASE_SECONDS + 60,
    )
    refused_dir = tmp_path / "refused"
    plant(refused_dir / "Other.sav", other.read_bytes(), BASE_SECONDS)
    plant(refused_dir / "Newest.sav", newest.read_bytes(), BASE_SECONDS + 60)
    unknown = tmp_path / "unidentified"
    plant(unknown / "Served.sav", served.read_bytes(), BASE_SECONDS)
    unreadable = synthetic.build_header(
        header_version=synthetic.UNSUPPORTED_HEADER_VERSION,
        world_token=CANARY_TOKEN_REFUSED,
        session_name=refused_name,
    )
    plant(unknown / "Newest.sav", unreadable, BASE_SECONDS + 60)
    planted = CANARY_TOKEN_REFUSED.encode("ascii") in newest.read_bytes()
    assert planted, "the canary token was never planted, so this grades nothing"

    texts = [
        *flag_reprs(providers.SaveWorldProvider(fallen).world()),
        *flag_reprs(providers.SaveWorldProvider(unknown).world()),
    ]
    statuses: list[int] = []
    for account in (fallen, refused_dir, unknown):
        status, body = get_api_world(account)
        statuses.append(status)
        texts.append(body.decode("ascii"))
    with pytest.raises(world.WorldLoadError) as walked:
        world.load_newest_world(workdir.ranked_saves(refused_dir))
    texts.extend((str(walked.value), repr(walked.value)))

    assert statuses == [contract.HTTP_OK, contract.HTTP_UNAVAILABLE, contract.HTTP_OK]
    hits = canary_hits(texts)
    assert hits == 0, "a world token or a world name was rendered"


# ---------------------------------------------------------------------------
# l. a refused save leaves no work copy behind
# ---------------------------------------------------------------------------


def copies_in(work_root: Path) -> list[str]:
    """The names of the save copies under ``work_root`` - synthetic, never rendered."""
    copies = work_root / workdir.COPIES_DIR_NAME
    if not copies.is_dir():
        return []
    return sorted(entry.name for entry in copies.iterdir())


def test_a_refused_save_leaves_no_work_copy(tmp_path: Path, isolated_work_root: Path) -> None:
    """The walk's copies of refused saves are removed; the served save's own copy may stay.

    Each refused save the walk met used to leave a full copy in the work root
    for good - a real library left dozens. The save directory is untouched
    either way, which arm (e) owns.
    """
    account = tmp_path / "pretend-account"
    plant_many_refused(account, MANY_REFUSED)

    model = providers.SaveWorldProvider(account).world()

    served = version_of(model)
    assert served == OLDER_VERSION
    left = copies_in(isolated_work_root)
    refused_copies = sum(1 for name in left if name.startswith("Refused"))
    assert refused_copies == 0, "a refused save's work copy was left in the work root"
    total = len(left)
    assert total <= 1, "more copies remain than the one save served"


# ---------------------------------------------------------------------------
# m. the memo holds no reader exception, and a re-raise carries no chain
# ---------------------------------------------------------------------------

#: The canary each planted refusal leaves in a string the reader failed to
#: decode - a world token in the header, a level name in the body.
HEADER_CANARY: Final = b"CanaryQzx"
BODY_CANARY: Final = b"CanaryLevelQzx"


def header_canary_save() -> bytes:
    """A save whose world token holds one byte that is no UTF-8 - a HEADER refusal."""
    blob = relabelled(synthetic.SAVE_LEVELLED_V36, CANARY_TOKEN_REFUSED)
    return blob.replace(b"QzxRfZ", b"QzxRf\xff")


def body_canary_save() -> bytes:
    """A save whose body holds a level name with one byte that is no UTF-8 - an OBJECTS refusal."""
    fixture = synthetic.SAVE_LEVELLED_V36
    named = (
        synthetic.SyntheticLevel(name="Persistent_Level:CanaryLevelQzxZ"),
        *synthetic.LEVELLED_NAMED[1:],
    )
    body = synthetic.build_levelled_body(
        named,
        synthetic.LEVELLED_PERSISTENT,
        header_version=fixture.header_version,
        save_version=fixture.save_version,
    ).replace(b"CanaryLevelQzxZ", b"CanaryLevelQzx\xff")
    payload = synthetic.body_with_prefix(body, fixture.header_version)
    framed = synthetic.build_chunks(payload, framing=fixture.framing)
    return fixture.blob[: fixture.chunk_offset] + framed


def _children(item: object) -> list[object]:
    """What one reachable object holds, for the canary walk."""
    if isinstance(item, BaseException):
        return [item.__cause__, item.__context__, *item.args, *vars(item).values()]
    if isinstance(item, dict | MappingProxyType):
        return [*item.keys(), *item.values()]
    if isinstance(item, list | tuple | set | frozenset):
        return list(item)
    if is_dataclass(item) and not isinstance(item, type):
        return [getattr(item, field.name) for field in fields(item)]
    opaque = callable(item) or isinstance(
        item, str | bytes | bytearray | int | float | bool | type | ModuleType
    )
    return [] if opaque else list(getattr(item, "__dict__", {}).values())


def reachable_faults(root: object, canary: bytes) -> tuple[int, int]:
    """Exceptions held, and canary hits, across everything reachable from ``root``.

    Walks containers, dataclass fields, plain attributes and - for an
    exception - its args, attributes, cause and context, so a byte string
    hidden in a suppressed context is reached as surely as one in a field.
    Every string reached and every exception's repr is searched for the canary.

    Args:
        root: Where to start.
        canary: The save-derived bytes no reachable value may hold.

    Returns:
        (exceptions reached, values or reprs holding the canary).
    """
    text = canary.decode("ascii")
    exceptions = hits = 0
    seen: set[int] = set()
    pending: list[object] = [root]
    while pending:
        item = pending.pop()
        if item is None or id(item) in seen:
            continue
        seen.add(id(item))
        if isinstance(item, BaseException):
            exceptions += 1
            hits += text in repr(item)
        if isinstance(item, bytes | bytearray):
            hits += canary in item
        elif isinstance(item, str):
            hits += text in item
        pending.extend(_children(item))
    return exceptions, hits


@pytest.mark.parametrize(
    ("payload", "canary"),
    [(header_canary_save, HEADER_CANARY), (body_canary_save, BODY_CANARY)],
    ids=["header", "objects"],
)
def test_the_memo_holds_no_reader_exception_and_a_re_raise_carries_no_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: Callable[[], bytes],
    canary: bytes,
) -> None:
    """A refusal's suppressed context holds the undecodable bytes; none of it may be kept.

    ``raise ... from None`` hides a ``UnicodeDecodeError`` from a printed
    traceback and keeps it on ``__context__``, its ``object`` holding the
    string that failed - here the canary. The memo may keep only the stage and
    the cause type, and the refusal it raises again on a later call is a fresh
    one with no cause and no context at all.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=payload())
    with pytest.raises(world.WorldLoadError) as direct:
        world.load_world(newest)
    original_hits = reachable_faults(direct.value, canary)[1]
    assert original_hits > 0, "the reader's own refusal holds no canary, so this grades nothing"
    load = CountingLoad()
    provider = providers.SaveWorldProvider(account, load=load)
    provider.world()
    raised: list[BaseException] = []
    walk = world.load_newest_world

    def spying_walk(candidates: Iterable[Path], **seams: Any) -> world.WorldModel | None:
        inner: Callable[[Path], world.WorldModel] = seams["load"]

        def recording(path: Path) -> world.WorldModel:
            try:
                return inner(path)
            except world.WorldLoadError as exc:
                raised.append(exc)
                raise

        return walk(candidates, **{**seams, "load": recording})

    monkeypatch.setattr(providers, "load_newest_world", spying_walk)
    provider.world()

    refused_loads = load.calls.get(newest.name, 0)
    assert refused_loads == 1, "the verdict was not remembered, so this grades nothing"
    re_raised = len(raised)
    assert re_raised >= 1, "no remembered verdict was raised again, so this grades nothing"
    memo = reachable_faults(provider, canary)
    assert memo == (0, 0), "the memo holds a reader exception or a save-derived string"
    chains = [reachable_faults(exc, canary) for exc in raised]
    assert chains == [(1, 0)] * re_raised, "a re-raised verdict carries a chain or a canary"
    bare = [exc.__cause__ is None and exc.__context__ is None for exc in raised]
    assert bare == [True] * re_raised


def test_a_cause_type_outside_the_reader_vocabulary_is_never_served(tmp_path: Path) -> None:
    """Fail closed: a subject built from anything but the closed vocabulary serves no world.

    The cause here is a write time spelled in letters - the shape a rewrite of
    ``cause_type`` anywhere between the reader and the flag would take.
    """
    account = tmp_path / "pretend-account"
    newest, _older = plant_pair(account, newest=reencoded_levelled_save())
    load = CountingLoad({newest.name: world.WorldLoadError(world.STAGE_OBJECTS, "bgaaaaaaaa")})

    model = providers.SaveWorldProvider(account, load=load).world()

    refused = model is None
    assert refused, "a subject outside the closed vocabulary was served"
