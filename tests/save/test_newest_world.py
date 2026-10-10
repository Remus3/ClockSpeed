"""load_newest_world - a save the reader refuses is skipped and flagged, never fatal.

THE DEFECT. ``workdir.latest_save`` picks the newest file and stops there. A
save the game did not write - re-encoded by a third-party tool - is refused by
the object reader, correctly, and while it was the newest file in the save
directory the companion refused the whole world with it. Non-negotiable 7:
unknown content is flagged and skipped, never fatal and never silently wrong.

WHAT IS GRADED, all on synthetic bytes in ``tmp_path`` - never a real save:

a. A refused newest save falls back to the next one, and the world carries one
   ``WARN_NEWER_SAVE_REFUSED`` per skipped save, naming the refusing stage, the
   cause and the skipped save's modification time - never its file name.
b. Every candidate refused raises the NEWEST refusal, typed, exactly as a
   single load did before.
c. A copy failure is not a parser refusal and does not fall back.
d. The walk is bounded.
e. A newest save that loads is handed up untouched, with no flag.
f. A failure that is not a ``WorldLoadError`` propagates unchanged.

EVERY ASSERTION IS ON A SCALAR BOUND TO A LOCAL. A ``tmp_path`` lives under a
home directory, so no assertion here renders a path.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.save import workdir, world
from tests.save import synthetic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

#: A walk that tried two saves, or a save loaded twice.
TWO_LOADS: Final = 2

#: 2020-09-13T12:26:40Z, a whole second so the rendered time is exact.
BASE_SECONDS: Final = 1_600_000_000

#: One minute after :data:`BASE_SECONDS`, as the subject spells it.
NEWER_STAMP: Final = "mtime-2020-09-13T12-27-40Z"

#: What the panel accepts as a subject: a structural token, no path separator.
TOKEN_SHAPE: Final = re.compile(r"[A-Za-z0-9_.-]+")

#: A digit run this long is what the dashboard sink withholds as identifier
#: shaped, so a subject must never carry one.
OPAQUE_DIGIT_RUN: Final = re.compile(r"\d{12}")


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
    path.write_bytes(payload)
    stamp = seconds * 1_000_000_000
    os.utime(path, ns=(stamp, stamp))
    return path


def load_flat(path: Path) -> world.WorldModel:
    """Load a FLAT-bodied corpus fixture, saying so at the call site."""
    return world.load_world(path, body_layout=world.BODY_LAYOUT_FLAT)


def walked(
    candidates: Iterable[Path], *, load: Callable[[Path], world.WorldModel]
) -> world.WorldModel:
    """Run the walk and insist it handed up a world.

    Args:
        candidates: Saves to try, newest first.
        load: The loader under test.

    Returns:
        The world the walk handed up.
    """
    model = world.load_newest_world(candidates, load=load)
    assert model is not None, "the walk handed up no world"
    return model


def refused_subjects(model: world.WorldModel) -> list[str]:
    """The subject of every fallback flag the model carries, in order."""
    return [
        warning.subject or ""
        for warning in model.warnings
        if warning.code == world.WARN_NEWER_SAVE_REFUSED
    ]


class Recorder:
    """A fake ``load`` that refuses the planted names it is told to, else loads.

    Attributes:
        calls: How many times it was called.
    """

    def __init__(self, refusals: dict[str, BaseException]) -> None:
        """Remember which file names refuse, and with what.

        Args:
            refusals: File name to the exception a load of it raises.
        """
        self.calls = 0
        self._refusals = refusals

    def __call__(self, path: Path) -> world.WorldModel:
        """Raise the planted refusal for ``path``, or load it flat."""
        self.calls += 1
        refusal = self._refusals.get(path.name)
        if refusal is not None:
            raise refusal
        return load_flat(path)


def objects_refusal() -> world.WorldLoadError:
    """The refusal the re-encoded file draws from the real object reader."""
    return world.WorldLoadError(world.STAGE_OBJECTS, "ObjectFormatError")


# ---------------------------------------------------------------------------
# a. fall back, and flag it
# ---------------------------------------------------------------------------


def test_a_newest_save_the_reader_refuses_falls_back_to_the_next_one(tmp_path: Path) -> None:
    """End to end through the real reader: garbage newest, synthetic older."""
    newest = plant(
        tmp_path / "Refused_autosave_0.sav", b"not a save the game wrote", BASE_SECONDS + 60
    )
    older = plant(tmp_path / "Readable_autosave_1.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    with pytest.raises(world.WorldLoadError) as direct:
        load_flat(newest)
    expected = f"{direct.value.stage}.{direct.value.cause_type}.{NEWER_STAMP}"

    model = walked((newest, older), load=load_flat)

    same_world = model.token == load_flat(older).token
    assert same_world, "the walk did not hand up the older save's world"
    subjects = refused_subjects(model)
    assert subjects == [expected]


def test_the_flag_names_the_stage_the_cause_and_the_mtime_and_never_the_file(
    tmp_path: Path,
) -> None:
    """The real defect's shape: an objects-stage refusal of the newest file."""
    newest = plant(tmp_path / "Refused_autosave_0.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Readable_autosave_1.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: objects_refusal()})

    model = walked((newest, older), load=load)

    flags = [w for w in model.warnings if w.code == world.WARN_NEWER_SAVE_REFUSED]
    count = len(flags)
    assert count == 1
    flag = flags[0]
    named = (flag.subject or "") == f"objects.ObjectFormatError.{NEWER_STAMP}"
    assert named, "the flag did not name the stage, the cause and the time"
    from_world = flag.source == world.SOURCE_WORLD
    assert from_world
    rendered = repr(flag)
    name_free = all(
        fragment not in rendered
        for fragment in ("Refused", "Readable", "autosave", tmp_path.name, str(tmp_path))
    )
    assert name_free, "the flag rendered the file name or its directory"


def test_the_subject_is_a_token_the_dashboard_sink_will_show(tmp_path: Path) -> None:
    """No separator a path needs, and no digit run the sink withholds as an id."""
    newest = plant(tmp_path / "Refused.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Readable.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    model = walked((newest, older), load=Recorder({newest.name: objects_refusal()}))

    (subject,) = refused_subjects(model)
    token_shaped = TOKEN_SHAPE.fullmatch(subject) is not None
    assert token_shaped
    opaque = OPAQUE_DIGIT_RUN.search(subject) is not None
    assert not opaque


def test_two_refused_saves_are_flagged_newest_first(tmp_path: Path) -> None:
    """Each skipped save is its own flag, in the order the walk met them."""
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
    middle = plant(tmp_path / "B.sav", b"re-encoded", BASE_SECONDS + 30)
    oldest = plant(tmp_path / "C.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder(
        {
            newest.name: objects_refusal(),
            middle.name: world.WorldLoadError(world.STAGE_HEADER, "HeaderTruncatedError"),
        }
    )

    model = walked((newest, middle, oldest), load=load)

    subjects = refused_subjects(model)
    assert subjects == [
        f"objects.ObjectFormatError.{NEWER_STAMP}",
        "header.HeaderTruncatedError.mtime-2020-09-13T12-27-10Z",
    ]


def test_an_unreadable_modification_time_is_flagged_as_unknown(tmp_path: Path) -> None:
    """A refused save that vanished before its time was read still gets a flag."""
    vanished = tmp_path / "Vanished.sav"
    older = plant(tmp_path / "Readable.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({vanished.name: objects_refusal()})

    model = walked((vanished, older), load=load)

    subjects = refused_subjects(model)
    assert subjects == ["objects.ObjectFormatError.mtime-unknown"]


@pytest.mark.parametrize("failure", [OverflowError, OSError, ValueError])
def test_a_modification_time_the_clock_cannot_render_is_flagged_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: type[Exception]
) -> None:
    """Windows ``gmtime`` refuses a year past 3000; the flag must not become the failure.

    A time that stats but will not render is still a refused save to skip, so
    the walk must reach the older save rather than unwind on the stamp.
    """
    newest = plant(tmp_path / "Refused.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "Readable.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)

    def refusing_clock(_seconds: float) -> object:
        raise failure

    monkeypatch.setattr(world.time, "gmtime", refusing_clock)
    model = walked((newest, older), load=Recorder({newest.name: objects_refusal()}))

    subjects = refused_subjects(model)
    assert subjects == ["objects.ObjectFormatError.mtime-unknown"]


# ---------------------------------------------------------------------------
# b. nothing readable keeps today's typed failure
# ---------------------------------------------------------------------------


def test_every_candidate_refused_raises_the_newest_refusal(tmp_path: Path) -> None:
    """The typed failure a single load raised before, from the newest save."""
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", b"also refused", BASE_SECONDS)
    load = Recorder(
        {
            newest.name: objects_refusal(),
            older.name: world.WorldLoadError(world.STAGE_HEADER, "HeaderTruncatedError"),
        }
    )

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, older), load=load)

    stage, cause = caught.value.stage, caught.value.cause_type
    assert (stage, cause) == (world.STAGE_OBJECTS, "ObjectFormatError")
    calls = load.calls
    assert calls == TWO_LOADS


def test_no_candidate_answers_none_without_loading() -> None:
    """No save at all is a supported state, not a refusal."""
    load = Recorder({})
    absent = world.load_newest_world((), load=load) is None
    assert absent
    calls = load.calls
    assert calls == 0


# ---------------------------------------------------------------------------
# c. a copy failure is not a parser refusal
# ---------------------------------------------------------------------------


def test_a_copy_failure_does_not_fall_back(tmp_path: Path) -> None:
    """A save the game is still writing is not a save the reader refused.

    Falling back past it would serve an older world while the newest one is
    merely busy, so the copy-stage failure propagates and nothing older loads.
    """
    newest = plant(tmp_path / "A.sav", b"busy", BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: world.WorldLoadError(world.STAGE_COPY, "SourceUnreadableError")})

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, older), load=load)

    stage = caught.value.stage
    assert stage == world.STAGE_COPY
    calls = load.calls
    assert calls == 1


# ---------------------------------------------------------------------------
# d. bounded
# ---------------------------------------------------------------------------


def test_the_walk_is_bounded_by_default(tmp_path: Path) -> None:
    """A directory of refused files costs MAX_RANKED_SAVES loads, not one per file."""
    names = [f"S{index}.sav" for index in range(workdir.MAX_RANKED_SAVES + 3)]
    paths = [
        plant(tmp_path / name, b"re-encoded", BASE_SECONDS - index)
        for index, name in enumerate(names)
    ]
    load = Recorder({name: objects_refusal() for name in names})

    with pytest.raises(world.WorldLoadError):
        world.load_newest_world(paths, load=load)

    calls = load.calls
    assert calls == workdir.MAX_RANKED_SAVES


def test_the_walk_honours_a_smaller_limit(tmp_path: Path) -> None:
    """The bound is the caller's to tighten."""
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: objects_refusal()})

    with pytest.raises(world.WorldLoadError):
        world.load_newest_world((newest, older), load=load, limit=1)

    calls = load.calls
    assert calls == 1


@pytest.mark.parametrize("limit", [0, -1])
def test_a_limit_below_one_is_refused(limit: int) -> None:
    """A walk of nothing is a caller's bug, refused rather than obeyed."""
    with pytest.raises(ValueError, match="limit"):
        world.load_newest_world((), load=Recorder({}), limit=limit)


# ---------------------------------------------------------------------------
# e. and f. the newest loads, or fails in a way that is not a refusal
# ---------------------------------------------------------------------------


def test_a_newest_save_that_loads_is_handed_up_untouched(tmp_path: Path) -> None:
    """No fallback, no flag, and the very object the loader returned."""
    newest = plant(tmp_path / "A.sav", synthetic.SAVE_V60.blob, BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    loaded = load_flat(newest)
    calls = [0]

    def load(_path: Path) -> world.WorldModel:
        calls[0] += 1
        return loaded

    model = walked((newest, older), load=load)

    same = model is loaded
    assert same
    count = calls[0]
    assert count == 1
    flagged = refused_subjects(model)
    assert flagged == []


def test_a_failure_that_is_not_a_world_load_error_propagates(tmp_path: Path) -> None:
    """An OSError is not the parser's verdict on the bytes, so nothing older is tried."""
    newest = plant(tmp_path / "A.sav", b"busy", BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: OSError()})

    with pytest.raises(OSError):  # noqa: PT011 - the bare type IS the contract
        world.load_newest_world((newest, older), load=load)

    calls = load.calls
    assert calls == 1
