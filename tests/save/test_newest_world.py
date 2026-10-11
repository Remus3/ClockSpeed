"""load_newest_world - a save the reader refuses is skipped and flagged, never fatal.

THE DEFECT. ``workdir.latest_save`` picks the newest file and stops there. A
save the game did not write - re-encoded by a third-party tool - is refused by
the object reader, correctly, and while it was the newest file in the save
directory the companion refused the whole world with it. Non-negotiable 7:
unknown content is flagged and skipped, never fatal and never silently wrong.

WHAT IS GRADED, all on synthetic bytes in ``tmp_path`` - never a real save:

a. A refused newest save falls back to the next one, and the world carries a
   ``WARN_NEWER_SAVE_REFUSED`` flag whose subject is the refusing stage and the
   cause type and NOTHING ELSE - no file name, no time, no digit. Skipped saves
   refused the same way are one flag counting them.
b. Every candidate refused raises the NEWEST refusal, typed, exactly as a
   single load did before - and so does a walk that a LATER candidate stops for
   a reason that is no verdict on its bytes.
c. Only a verdict on the save's own bytes falls back. The stages partition
   into those verdicts and the rest, exhaustively, and a copy or usmap failure
   of the newest propagates.
d. No cap: the walk goes on while a candidate remains.
e. A newest save that loads is handed up untouched, with no flag.
f. A failure that is not a ``WorldLoadError`` propagates unchanged.
g. The subject builder reads the refusal's two closed-vocabulary fields and
   nothing else - judged on the shipped syntax tree, with planted positives.
h. When the refused newest save's world is known the walk falls back only to
   that world, and to nothing when none of it is readable; when it is not
   known, the newest readable save is served under a distinct code.
i. The detail agrees with the count, and spells no number.
j. A subject outside the closed vocabulary fails closed, and the memo's
   re-raise is a fresh refusal that takes nothing else.
k. The objects stage is a verdict on the bytes: one corrupt save, two
   mappings, one verdict.
l. A save's world is read from the header alone, answered as a digest, and
   neither that read nor a refused load leaves a work copy behind.
m. An identifier no ledger keys names no known world, and the rule is the
   ledger's own; a header longer than the bounded prefix still names its
   world; a save of unknown world met past a known one is counted under the
   known world's code while that world is served; a rebuilt refusal carries
   no context even inside a handler; and a cause outside the vocabulary fails
   closed with no frame rendering it.

EVERY ASSERTION IS ON A SCALAR BOUND TO A LOCAL. A ``tmp_path`` lives under a
home directory, so no assertion here renders a path.
"""

from __future__ import annotations

import ast
import inspect
import os
import re
import textwrap
import traceback
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import ledger
from clockspeed.save import usmap, workdir, world
from clockspeed.save.chunks import ChunkError
from clockspeed.save.header import MAX_HEADER_BYTES, HeaderError
from clockspeed.save.objects import ObjectError
from tests.save import synthetic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

#: A walk that tried two saves, or a save loaded twice.
TWO_LOADS: Final = 2

#: 2020-09-13T12:26:40Z, a whole second.
BASE_SECONDS: Final = 1_600_000_000

#: What the panel accepts as a subject: a structural token, no path separator,
#: and no digit - a time, a size or an index would be one.
TOKEN_SHAPE: Final = re.compile(r"[A-Za-z_.]+")

#: More refused saves than the cap of three the first cut carried.
MANY_REFUSED: Final = 10

#: The two fields of a refusal the subject may read. Both closed vocabulary.
SUBJECT_FIELDS: Final = frozenset({"stage", "cause_type"})

#: The bytes every planted refused save carries: a readable save of the
#: fixture world, so its header names the same world as the save the walk
#: falls back to. The FAKE loader refuses it by name; the real ``identify``
#: reads its header.
SAME_WORLD: Final = synthetic.SAVE_V60.blob

#: The code of a world served past a newest save whose world is unknown,
#: spelled as the wire spells it.
UNIDENTIFIED: Final = "newest-save-unidentified"

#: How many body bytes the corrupt levelled save is cut short by.
REENCODED_SHORTFALL: Final = 16


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


def refused_flags(model: world.WorldModel) -> list[tuple[str, int]]:
    """Each fallback flag the model carries as (subject, count), in order."""
    return [
        (warning.subject or "", warning.count)
        for warning in model.warnings
        if warning.code == world.WARN_NEWER_SAVE_REFUSED
    ]


def flags_render_none_of(model: world.WorldModel, fragments: Iterable[str]) -> bool:
    """Whether no fallback flag's repr carries any of ``fragments``.

    A helper rather than inline so the rendered text lives in THIS frame, which
    holds no assertion, and never in a test's frame at an assert.

    Args:
        model: The world the walk handed up.
        fragments: Text that must not appear - file names and their directory.

    Returns:
        True when no flag renders any fragment.
    """
    rendered = "".join(
        repr(warning) for warning in model.warnings if warning.code == world.WARN_NEWER_SAVE_REFUSED
    )
    return all(fragment not in rendered for fragment in fragments)


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


def refusal_at(stage: str, cause: str) -> world.WorldLoadError:
    """A refusal at ``stage`` with ``cause`` as its type name."""
    return world.WorldLoadError(stage, cause)


# ---------------------------------------------------------------------------
# a. fall back, and flag it
# ---------------------------------------------------------------------------


def test_a_newest_save_the_reader_refuses_falls_back_to_the_next_one(tmp_path: Path) -> None:
    """End to end through the real reader: garbage newest, synthetic older.

    Garbage is refused at the HEADER, so the newest save's world is never read
    and the flag is the distinct one saying the world may be another.
    """
    newest = plant(
        tmp_path / "Refused_autosave_0.sav", b"not a save the game wrote", BASE_SECONDS + 60
    )
    older = plant(tmp_path / "Readable_autosave_1.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    with pytest.raises(world.WorldLoadError) as direct:
        load_flat(newest)
    expected = f"{direct.value.stage}.{direct.value.cause_type}"

    model = walked((newest, older), load=load_flat)

    same_world = model.token == load_flat(older).token
    assert same_world, "the walk did not hand up the older save's world"
    # NO WARNING IS BOUND TO A LOCAL: the read is reduced to a scalar inline.
    distinct = [(w.code, w.subject, w.count) for w in model.warnings if w.code == UNIDENTIFIED] == [
        (UNIDENTIFIED, expected, 1)
    ]
    assert distinct, "the walk did not flag the unidentified newest save exactly once"


def test_the_flag_names_the_stage_and_the_cause_and_never_the_file(tmp_path: Path) -> None:
    """The real defect's shape: an objects-stage refusal of the newest file."""
    newest = plant(tmp_path / "Refused_autosave_0.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "Readable_autosave_1.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: objects_refusal()})

    model = walked((newest, older), load=load)

    # NO WARNING IS BOUND TO A LOCAL: each read is reduced to a scalar inline,
    # so nothing the warning's own repr withholds is in this frame at an assert.
    named = refused_flags(model) == [("objects.ObjectFormatError", 1)]
    assert named, "the flag did not name exactly the stage and the cause"
    from_world = all(
        w.source == world.SOURCE_WORLD
        for w in model.warnings
        if w.code == world.WARN_NEWER_SAVE_REFUSED
    )
    assert from_world
    name_free = flags_render_none_of(
        model, ("Refused", "Readable", "autosave", tmp_path.name, str(tmp_path))
    )
    assert name_free, "the flag rendered the file name or its directory"


def test_the_subject_and_detail_carry_no_digit(tmp_path: Path) -> None:
    """No separator a path needs, and no digit: a time or a size would carry one."""
    newest = plant(tmp_path / "Refused.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "Readable.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    model = walked((newest, older), load=Recorder({newest.name: objects_refusal()}))

    token_shaped = all(
        TOKEN_SHAPE.fullmatch(w.subject or "") is not None and not re.search(r"\d", w.detail)
        for w in model.warnings
        if w.code == world.WARN_NEWER_SAVE_REFUSED
    )
    assert token_shaped


def test_two_refusals_are_flagged_newest_first(tmp_path: Path) -> None:
    """Different refusals are different flags, in the order the walk met them."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    middle = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS + 30)
    oldest = plant(tmp_path / "C.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder(
        {
            newest.name: objects_refusal(),
            middle.name: refusal_at(world.STAGE_HEADER, "HeaderTruncatedError"),
        }
    )

    model = walked((newest, middle, oldest), load=load)

    flags = refused_flags(model)
    assert flags == [("objects.ObjectFormatError", 1), ("header.HeaderTruncatedError", 1)]


def test_saves_refused_alike_are_one_flag_counting_them(tmp_path: Path) -> None:
    """Identical subjects aggregate, so a run of refused files is one line on the panel."""
    first = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    second = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS + 50)
    third = plant(tmp_path / "C.sav", SAME_WORLD, BASE_SECONDS + 40)
    readable = plant(tmp_path / "D.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder(
        {
            first.name: objects_refusal(),
            second.name: refusal_at(world.STAGE_HEADER, "HeaderTruncatedError"),
            third.name: objects_refusal(),
        }
    )

    model = walked((first, second, third, readable), load=load)

    flags = refused_flags(model)
    assert flags == [("objects.ObjectFormatError", 2), ("header.HeaderTruncatedError", 1)]


# ---------------------------------------------------------------------------
# b. nothing readable keeps today's typed failure - the NEWEST refusal
# ---------------------------------------------------------------------------


def test_every_candidate_refused_raises_the_newest_refusal(tmp_path: Path) -> None:
    """The typed failure a single load raised before, from the newest save."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", b"also refused", BASE_SECONDS)
    load = Recorder(
        {
            newest.name: objects_refusal(),
            older.name: refusal_at(world.STAGE_HEADER, "HeaderTruncatedError"),
        }
    )

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, older), load=load)

    stage, cause = caught.value.stage, caught.value.cause_type
    assert (stage, cause) == (world.STAGE_OBJECTS, "ObjectFormatError")
    calls = load.calls
    assert calls == TWO_LOADS


@pytest.mark.parametrize(
    ("stage", "cause"),
    [
        (world.STAGE_COPY, "SourceUnreadableError"),
        (world.STAGE_USMAP, "UsmapFormatError"),
    ],
)
def test_a_newest_refusal_is_re_raised_past_a_later_failure_that_is_no_verdict(
    tmp_path: Path, stage: str, cause: str
) -> None:
    """A later save that is busy, or a mapping that will not read, stops the walk.

    It does not replace the newest save's refusal with its own: the newest
    refusal is what a caller is told, exactly as when every candidate refused.
    """
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    busy = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS + 30)
    oldest = plant(tmp_path / "C.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: objects_refusal(), busy.name: refusal_at(stage, cause)})

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, busy, oldest), load=load)

    raised = (caught.value.stage, caught.value.cause_type)
    assert raised == (world.STAGE_OBJECTS, "ObjectFormatError")
    calls = load.calls
    assert calls == TWO_LOADS, "the walk went on past a save that was no verdict"


def test_no_candidate_answers_none_without_loading() -> None:
    """No save at all is a supported state, not a refusal."""
    load = Recorder({})
    absent = world.load_newest_world((), load=load) is None
    assert absent
    calls = load.calls
    assert calls == 0


# ---------------------------------------------------------------------------
# c. only a verdict on the save's own bytes falls back
# ---------------------------------------------------------------------------


def test_the_stages_partition_into_verdicts_on_the_bytes_and_the_rest() -> None:
    """Every stage is classified, so a new stage cannot fall back by omission."""
    verdicts = set(world.SAVE_VERDICT_STAGES)
    rest = {world.STAGE_COPY, world.STAGE_USMAP}
    partition = (verdicts | rest == set(world.STAGES), verdicts & rest == set())
    assert partition == (True, True)
    named = sorted(verdicts)
    assert named == sorted((world.STAGE_HEADER, world.STAGE_CHUNKS, world.STAGE_OBJECTS))


@pytest.mark.parametrize(
    ("stage", "cause"),
    [
        (world.STAGE_COPY, "SourceUnreadableError"),
        (world.STAGE_USMAP, "UsmapFormatError"),
    ],
)
def test_a_newest_failure_that_is_no_verdict_does_not_fall_back(
    tmp_path: Path, stage: str, cause: str
) -> None:
    """A busy save, or the install's mapping failing to read, says nothing about the bytes.

    Falling back past it would serve an older world while the newest one is
    readable, so the failure propagates and nothing older loads.
    """
    newest = plant(tmp_path / "A.sav", b"busy", BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: refusal_at(stage, cause)})

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, older), load=load)

    raised = caught.value.stage
    assert raised == stage
    calls = load.calls
    assert calls == 1


# ---------------------------------------------------------------------------
# d. no cap
# ---------------------------------------------------------------------------


def test_the_walk_goes_on_while_a_candidate_remains(tmp_path: Path) -> None:
    """THE REPLACEMENT FOR THE CAP OF THREE: ten refused saves, then a readable one.

    The acceptance reads "the newest save the parser accepts", so no cap may
    leave the world unread while a readable save remains. Each candidate is
    loaded exactly once.
    """
    names = [f"S{index:02d}.sav" for index in range(MANY_REFUSED)]
    refused = [
        plant(tmp_path / name, SAME_WORLD, BASE_SECONDS + 600 - index)
        for index, name in enumerate(names)
    ]
    readable = plant(tmp_path / "Readable.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({name: objects_refusal() for name in names})

    model = walked((*refused, readable), load=load)

    calls = load.calls
    assert calls == MANY_REFUSED + 1
    flags = refused_flags(model)
    assert flags == [("objects.ObjectFormatError", MANY_REFUSED)]


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
    flagged = refused_flags(model)
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


# ---------------------------------------------------------------------------
# g. the subject builder, judged on the shipped syntax tree
# ---------------------------------------------------------------------------

#: The first cut's subject builder, verbatim in substance: it stat-ed the
#: refused save and rendered its write time into the subject. The planted
#: positive the detector below must catch.
PLANTED_MTIME_BUILDER: Final = """
def _refusal_subject(refusal, path):
    try:
        seconds = path.stat().st_mtime_ns // 1_000_000_000
        stamp = "mtime-" + time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime(seconds))
    except (OSError, OverflowError, ValueError):
        stamp = "mtime-unknown"
    return f"{refusal.stage}.{refusal.cause_type}.{stamp}"
"""

#: A one-parameter builder that reaches the filesystem through the refusal's
#: own traceback - the shape a builder keeping one parameter could still grow.
PLANTED_REACHING_BUILDER: Final = """
def _refusal_subject(refusal):
    return f"{refusal.stage}.{refusal.__traceback__.tb_frame.f_locals}"
"""

#: A one-parameter builder that appends a size it read off a global.
PLANTED_GLOBAL_BUILDER: Final = """
def _refusal_subject(refusal):
    return f"{refusal.stage}.{refusal.cause_type}.{LAST_SIZE}"
"""


def subject_builder_faults(source: str) -> list[str]:
    """What a subject builder reads beyond the refusal's two vocabulary fields.

    The builder must take ONE parameter, call nothing, name nothing but that
    parameter, and read no attribute of it but ``stage`` and ``cause_type``.
    Anything else - a ``stat``, a clock, a global, a second parameter - is a
    route for a filesystem-derived value into a subject the endpoint serves.

    Args:
        source: The builder's source.

    Returns:
        One short label per fault - node kinds and field names, never values.
    """
    tree = ast.parse(textwrap.dedent(source))
    (function,) = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    faults: list[str] = []
    parameters = [argument.arg for argument in function.args.args]
    if len(parameters) != 1:
        faults.append("parameters")
    allowed = set(parameters[:1])
    # The BODY only: the annotations name types, which carry no value.
    body = [node for statement in function.body for node in ast.walk(statement)]
    for node in body:
        if isinstance(node, ast.Call):
            faults.append("call")
        elif isinstance(node, ast.Attribute):
            on_parameter = isinstance(node.value, ast.Name) and node.value.id in allowed
            if not on_parameter or node.attr not in SUBJECT_FIELDS:
                faults.append(f"attribute {node.attr}")
        elif isinstance(node, ast.Name) and node.id not in allowed:
            faults.append(f"name {node.id}")
        elif isinstance(node, ast.Try | ast.With | ast.Assign | ast.AugAssign | ast.NamedExpr):
            faults.append(type(node).__name__)
    return faults


def test_the_flag_subject_is_built_from_the_refusal_vocabulary_alone() -> None:
    """The shipped builder reads stage and cause type and nothing filesystem-derived."""
    faults = subject_builder_faults(inspect.getsource(world._refusal_subject))  # noqa: SLF001
    assert faults == []


@pytest.mark.parametrize(
    "planted",
    [PLANTED_MTIME_BUILDER, PLANTED_REACHING_BUILDER, PLANTED_GLOBAL_BUILDER],
    ids=["mtime", "traceback", "global"],
)
def test_the_subject_detector_sees_a_planted_reach(planted: str) -> None:
    """The control: each planted builder is caught, so a clean result means something."""
    caught = len(subject_builder_faults(planted)) > 0
    assert caught


def test_the_walk_builds_every_subject_through_the_builder() -> None:
    """No subject reaches a flag except through the builder the arm above grades."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(world.load_newest_world)))
    built = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_refusal_subject"
    )
    assert built == 1
    constructions = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "WorldWarning"
    )
    assert constructions == 0, "the walk builds a warning itself instead of through the flags"


# ---------------------------------------------------------------------------
# h. the refused newest save's own world, or the distinct flag (CS-1309 F2)
# ---------------------------------------------------------------------------


class TokenBook:
    """A fake ``identify``: file name to the world its header names, answered as a digest.

    Attributes:
        asked: The file names it was asked about, in order.
    """

    def __init__(self, tokens: dict[str, str | None]) -> None:
        """Remember each file's token; a name not listed reads as unidentifiable.

        Args:
            tokens: File name to its token, or None for a header that will not read.
        """
        self.asked: list[str] = []
        self._tokens = tokens

    def __call__(self, path: Path) -> str | None:
        """The digest of the planted token for ``path``, as the shipped reader answers."""
        self.asked.append(path.name)
        token = self._tokens.get(path.name)
        return None if token is None else world.world_digest(token)


def test_the_walk_skips_another_worlds_save_without_loading_it(tmp_path: Path) -> None:
    """Known newest world: another world's save is skipped unread, its own world's is served."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    other = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS + 30)
    own = plant(tmp_path / "C.sav", SAME_WORLD, BASE_SECONDS)
    fixture_world = synthetic.SYNTHETIC_WORLD_TOKEN
    book = TokenBook({newest.name: fixture_world, other.name: "X", own.name: fixture_world})
    loaded: list[str] = []

    def load(path: Path) -> world.WorldModel:
        loaded.append(path.name)
        if path.name == newest.name:
            raise objects_refusal()
        return load_flat(path)

    model = world.load_newest_world((newest, other, own), load=load, identify=book)

    order = loaded == [newest.name, own.name]
    assert order, "another world's save was loaded"
    flags = refused_flags(model) if model is not None else []
    assert flags == [("objects.ObjectFormatError", 1)]


def test_a_known_world_with_no_readable_save_raises_the_newest_refusal(tmp_path: Path) -> None:
    """Never another world in its place: the walk ends as if every candidate refused."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    other = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS)
    book = TokenBook({newest.name: synthetic.SYNTHETIC_WORLD_TOKEN, other.name: "X"})
    load = Recorder({newest.name: objects_refusal()})

    with pytest.raises(world.WorldLoadError) as caught:
        world.load_newest_world((newest, other), load=load, identify=book)

    raised = (caught.value.stage, caught.value.cause_type)
    assert raised == (world.STAGE_OBJECTS, "ObjectFormatError")
    calls = load.calls
    assert calls == 1, "another world's save was loaded"


def test_a_loaded_save_of_another_world_is_not_served(tmp_path: Path) -> None:
    """The token is checked on the loaded world too, so a save rewritten mid-walk is caught.

    The fake ``identify`` answers None for the middle file - a header it could
    not read - so the walk loads it, and the world it loads is another one.
    """
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    middle = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS)
    book = TokenBook({newest.name: "not-the-fixture-world"})
    load = Recorder({newest.name: objects_refusal()})

    with pytest.raises(world.WorldLoadError):
        world.load_newest_world((newest, middle), load=load, identify=book)

    calls = load.calls
    assert calls == TWO_LOADS


def test_a_world_that_cannot_be_recovered_after_the_header_stops_the_walk(
    tmp_path: Path,
) -> None:
    """The header WAS read, so the world is known: failing to recover it serves nothing.

    Treating it as unknown would serve another world under the distinct flag
    on a transient copy failure; the walk instead ends exactly as when every
    candidate refused, and the provider tries again next call.
    """
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS)
    load = Recorder({newest.name: objects_refusal()})

    with pytest.raises(world.WorldLoadError):
        world.load_newest_world((newest, older), load=load, identify=TokenBook({}))

    calls = load.calls
    assert calls == 1


def test_a_header_refusal_serves_the_newest_readable_save_under_the_distinct_code(
    tmp_path: Path,
) -> None:
    """Unknown newest world: the newest readable save is served, whatever its world, and flagged."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    other = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS)
    book = TokenBook({other.name: "X"})
    load = Recorder({newest.name: refusal_at(world.STAGE_HEADER, "HeaderFormatError")})

    model = walked_with((newest, other), load=load, identify=book)

    distinct = [
        (w.code, w.subject, w.count)
        for w in model.warnings
        if w.code in (world.WARN_NEWER_SAVE_REFUSED, UNIDENTIFIED)
    ] == [(UNIDENTIFIED, "header.HeaderFormatError", 1)]
    assert distinct, "the fallback flags are not exactly the one distinct flag"
    asked = book.asked
    assert asked == [], "an unknown world was looked up, so a token was compared"


def walked_with(
    candidates: Iterable[Path],
    *,
    load: Callable[[Path], world.WorldModel],
    identify: Callable[[Path], str | None],
) -> world.WorldModel:
    """Run the walk with an explicit ``identify`` and insist it handed up a world.

    Args:
        candidates: Saves to try, newest first.
        load: The loader under test.
        identify: The world-token reader under test.

    Returns:
        The world the walk handed up.
    """
    model = world.load_newest_world(candidates, load=load, identify=identify)
    assert model is not None, "the walk handed up no world"
    return model


# ---------------------------------------------------------------------------
# i. the detail agrees with the count (CS-1309 F3)
# ---------------------------------------------------------------------------


def test_the_detail_agrees_with_the_count(tmp_path: Path) -> None:
    """One save is "a newer save"; several are "newer saves" - and no count is spelled."""
    first = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    second = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS + 50)
    third = plant(tmp_path / "C.sav", SAME_WORLD, BASE_SECONDS + 40)
    readable = plant(tmp_path / "D.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder(
        {
            first.name: objects_refusal(),
            second.name: refusal_at(world.STAGE_HEADER, "HeaderTruncatedError"),
            third.name: objects_refusal(),
        }
    )

    model = walked((first, second, third, readable), load=load)

    agreeing = [
        (w.count, w.detail.split(" refused")[0], re.search(r"\d", w.detail) is None)
        for w in model.warnings
        if w.code == world.WARN_NEWER_SAVE_REFUSED
    ] == [(2, "newer saves were", True), (1, "a newer save was", True)]
    assert agreeing, "a detail disagrees with its count or spells a number"


# ---------------------------------------------------------------------------
# j. a subject is the closed vocabulary or nothing (CS-1309 F-C)
# ---------------------------------------------------------------------------


def reader_refusal_names() -> set[str]:
    """Every class name the three readers' refusal taxonomies define, bases included."""
    names: set[str] = set()
    pending: list[type[BaseException]] = [HeaderError, ChunkError, ObjectError]
    while pending:
        cls = pending.pop()
        names.add(cls.__name__)
        pending.extend(cls.__subclasses__())
    return names


def test_the_reader_vocabulary_is_exactly_the_readers_refusal_classes() -> None:
    """The closed set is the readers' own taxonomies - a class added there reddens here."""
    listed = set(world.READER_REFUSAL_TYPES)
    assert listed == reader_refusal_names()


def test_a_subject_outside_the_closed_vocabulary_fails_closed(tmp_path: Path) -> None:
    """A cause rewritten anywhere between reader and flag is refused, never rendered."""
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", synthetic.SAVE_V60.blob, BASE_SECONDS)
    load = Recorder({newest.name: refusal_at(world.STAGE_OBJECTS, "bgaaaaaaaa")})

    with pytest.raises(ValueError, match="closed vocabulary"):
        world.load_newest_world((newest, older), load=load)


def test_a_rebuilt_refusal_is_fresh_and_takes_only_the_closed_vocabulary() -> None:
    """The memo's re-raise: a new refusal with no chain, and nothing outside the two sets."""
    with pytest.raises(world.WorldLoadError) as caught:
        world.refuse_again(world.STAGE_OBJECTS, "ObjectFormatError")
    rebuilt = (
        caught.value.stage,
        caught.value.cause_type,
        caught.value.__cause__ is None,
        caught.value.__context__ is None,
        caught.value.__suppress_context__,
    )
    assert rebuilt == (world.STAGE_OBJECTS, "ObjectFormatError", True, True, True)
    with pytest.raises(ValueError, match="closed vocabulary"):
        world.refuse_again(world.STAGE_COPY, "ObjectFormatError")
    with pytest.raises(ValueError, match="closed vocabulary"):
        world.refuse_again(world.STAGE_OBJECTS, "bgaaaaaaaa")


# ---------------------------------------------------------------------------
# k. the objects stage is a verdict on the bytes alone (CS-1309 F5)
# ---------------------------------------------------------------------------


def mapping_of(*class_names: str) -> usmap.PropertyMap:
    """A minimal parsed mapping modelling exactly the named classes."""
    return usmap.PropertyMap(
        names=class_names,
        enums={},
        schemas={
            name: usmap.Schema(name=name, super_name=None, properties=()) for name in class_names
        },
        warnings=(),
        container=usmap.UsmapContainer(
            magic=usmap.USMAP_MAGIC,
            version=0,
            compression_method=usmap.COMPRESSION_NONE,
            compressed_size=0,
            decompressed_size=0,
            header_size=0,
        ),
        body_consumed=0,
    )


def test_the_objects_verdict_is_the_same_under_two_mappings() -> None:
    """The same corrupt bytes draw the same refusal with no mapping and with one.

    That is what entitles the provider to remember an objects-stage refusal
    against the file: the installed mapping drives resolution, never the
    decode. The control proves the mapping is really in effect on the intact
    bytes, so the equality is not two loads that never read it.
    """
    fixture = synthetic.SAVE_LEVELLED_V36
    cut = fixture.body[: len(fixture.body) - REENCODED_SHORTFALL]
    corrupt = fixture.blob[: fixture.chunk_offset] + synthetic.build_chunks(
        cut, framing=fixture.framing
    )
    modelled = mapping_of(*(obj.class_path.rsplit(".", 1)[-1] for obj in fixture.objects))
    verdicts = []
    for mapping in (None, modelled):
        with pytest.raises(world.WorldLoadError) as caught:
            world.load_world_from_bytes(corrupt, property_map=mapping)
        verdicts.append((caught.value.stage, caught.value.cause_type))
    assert verdicts == [(world.STAGE_OBJECTS, "ObjectFormatError")] * 2
    unmapped = world.WARN_NO_PROPERTY_MAP in {
        w.code for w in world.load_world_from_bytes(fixture.blob, property_map=None).warnings
    }
    mapped = world.WARN_NO_PROPERTY_MAP in {
        w.code for w in world.load_world_from_bytes(fixture.blob, property_map=modelled).warnings
    }
    assert (unmapped, mapped) == (True, False), "the mapping was never in effect"


# ---------------------------------------------------------------------------
# l. reading which world a save names, and the work copies it leaves (CS-1309 F2, F4)
# ---------------------------------------------------------------------------


def test_the_world_is_read_from_the_header_alone(tmp_path: Path) -> None:
    """A refused body still names its world; an empty identifier names none; no save is unread.

    Answered as a digest, never as the token, and a header longer than the
    bounded prefix is read in full rather than taken for an unread one.
    """
    corrupt = plant(tmp_path / "A.sav", SAME_WORLD[: len(SAME_WORLD) - 8], BASE_SECONDS)
    garbage = plant(tmp_path / "B.sav", b"not a save the game wrote", BASE_SECONDS)
    empty_header, body = flat_parts("")
    empty = plant(tmp_path / "C.sav", empty_header + body, BASE_SECONDS)
    long_header, _ = flat_parts(synthetic.SYNTHETIC_WORLD_TOKEN, oversize=True)
    oversize = plant(tmp_path / "D.sav", long_header + body[:CHUNK_STUB], BASE_SECONDS)
    fixture_world = world.world_digest(synthetic.SYNTHETIC_WORLD_TOKEN)

    answers = [world.read_world_digest(path) for path in (corrupt, garbage, empty, oversize)]

    assert answers == [fixture_world, None, world.NO_WORLD, fixture_world]


def test_reading_and_refusing_leave_no_work_copy(tmp_path: Path, isolated_work_root: Path) -> None:
    """Neither the token read nor a refused load leaves a copy in the work root."""
    corrupt = plant(tmp_path / "A.sav", SAME_WORLD[: len(SAME_WORLD) - 8], BASE_SECONDS)
    world.read_world_digest(corrupt)
    with pytest.raises(world.WorldLoadError):
        load_flat(corrupt)

    # Counted through the work directory's own purge, which removes and counts
    # only the copies it made - so this module reaches no listing primitive.
    left = workdir.purge_work_dir(work_root=isolated_work_root)
    assert left == 0, "a work copy of a refused save was left behind"
    kept = corrupt.is_file()
    assert kept, "the save itself was touched"


# ---------------------------------------------------------------------------
# m. an identifier no ledger keys, a header past the prefix, a save of unknown
#    world met past a known one, and frames that render nothing (CS-1309 r3)
# ---------------------------------------------------------------------------

#: Two identifiers ``clockspeed/advisor/ledger.py`` refuses as a world key:
#: empty, and not ASCII. Invented.
LEDGER_REFUSED_TOKENS: Final = ("", "W\u00f6rldTokenNotAsciiQzx")

#: Values the save-side world rule and the ledger must judge alike.
LEDGER_SAMPLES: Final = (
    "",
    "a",
    synthetic.SYNTHETIC_WORLD_TOKEN,
    "W\u00f6rldTokenNotAsciiQzx",
    "tab\tand space",
    7,
    None,
    b"ClockspeedSynthToken00",
)

#: How many body bytes a save cut short at its chunks keeps - the chunk
#: reader refuses it with ``ChunkTruncatedError``, measured.
CHUNK_STUB: Final = 20

#: How many bytes a save whose header will not read keeps - the header reader
#: refuses it with ``HeaderTruncatedError``, measured.
HEADER_STUB: Final = 12

#: Each header string's length in the oversize header: under the reader's own
#: per-string cap, and four of them carry the header past the identify prefix.
OVERSIZE_STRING: Final = 16_300

#: What the oversize header's map name carries past the measured one, so the
#: five strings together clear the prefix.
OVERSIZE_MAP_TAIL: Final = 2_000

#: Two play durations that tell two worlds' saves apart without naming either.
ALPHA_PLAY: Final = 11
BETA_PLAY: Final = 22

#: A cause no reader class is called. Letters only, so it has a subject's shape.
CANARY_CAUSE: Final = "QzxCanaryCauseNotAType"

#: The served code of a known-world fallback, as the wire spells it.
NEWER: Final = "newer-save-refused"


def flat_parts(
    token: str, *, play_duration: int = 0, oversize: bool = False
) -> tuple[bytes, bytes]:
    """A flat-bodied synthetic save of the world ``token`` names, as (header, body).

    Args:
        token: The invented identifier the header carries.
        play_duration: Tells two worlds' saves apart.
        oversize: Make the header longer than the identify prefix, each
            string under the reader's per-string cap.

    Returns:
        The header bytes and the chunked body bytes.
    """
    fixture = synthetic.SAVE_V60
    filler = "x" * OVERSIZE_STRING
    strings = (
        {
            "save_name": filler,
            "options": "?" + filler[:-1],
            "session_name": filler,
            "mod_metadata": filler,
            "map_name": synthetic.MAP_NAME + "y" * OVERSIZE_MAP_TAIL,
        }
        if oversize
        else {}
    )
    header = synthetic.build_header(
        header_version=fixture.header_version,
        save_version=fixture.save_version,
        world_token=token,
        play_duration=play_duration,
        **strings,  # type: ignore[arg-type]
    )
    return header, fixture.blob[fixture.chunk_offset :]


def all_fallback_flags(model: world.WorldModel | None) -> list[tuple[str, str, int]]:
    """Every flag of either fallback code as (code, subject, count), in order."""
    if model is None:
        return []
    return [
        (w.code, w.subject or "", w.count)
        for w in model.warnings
        if w.code in (world.WARN_NEWER_SAVE_REFUSED, UNIDENTIFIED)
    ]


@pytest.mark.parametrize("token", LEDGER_REFUSED_TOKENS, ids=["empty", "not-ascii"])
def test_an_identifier_no_ledger_keys_names_no_known_world(tmp_path: Path, token: str) -> None:
    """Two worlds sharing an identifier the ledger refuses are not one known world.

    Alpha's newest save is cut short at its chunks and Beta's save is
    readable; both headers carry the same refused identifier. Taking it for a
    KNOWN world served Beta under "a newer save of this world was refused" - a
    claim about a world the walk never identified. It names no world, so Beta
    is served under the distinct flag.
    """
    alpha_header, body = flat_parts(token, play_duration=ALPHA_PLAY)
    beta_header, _ = flat_parts(token, play_duration=BETA_PLAY)
    alpha = plant(tmp_path / "Alpha.sav", alpha_header + body[:CHUNK_STUB], BASE_SECONDS + 60)
    beta = plant(tmp_path / "Beta.sav", beta_header + body, BASE_SECONDS)

    model = world.load_newest_world((alpha, beta), load=load_flat)

    served = model is not None and model.header.play_duration == BETA_PLAY
    assert served, "the newest readable save was not the one served"
    flags = all_fallback_flags(model)
    assert flags == [(UNIDENTIFIED, "chunks.ChunkTruncatedError", 1)]


def ledger_accepts(value: object) -> bool:
    """Whether the advice ledger keys a world by ``value``."""
    try:
        ledger.world_key(value)  # type: ignore[arg-type]
    except ledger.WorldTokenError:
        return False
    return True


def test_the_save_side_world_rule_is_the_ledgers() -> None:
    """One rule in two layers, pinned equal, because save/ may not import advisor/.

    The walk's rule for "names a world" and the ledger's rule for "keys a
    world" are the same predicate, and the walk's digest is the ledger's key,
    so the world the walk compares is the world the ledger stores.
    """
    rule = [world.is_world_token(value) for value in LEDGER_SAMPLES]
    keyed = [ledger_accepts(value) for value in LEDGER_SAMPLES]
    assert rule == keyed
    digests = [
        world.world_digest(value) == (ledger.world_key(value) if ok else world.NO_WORLD)  # type: ignore[arg-type]
        for value, ok in zip(LEDGER_SAMPLES, keyed, strict=True)
    ]
    assert digests == [True] * len(LEDGER_SAMPLES)


def test_a_save_of_unknown_world_met_past_a_known_one_is_counted_and_the_world_served(
    tmp_path: Path,
) -> None:
    """Newest A refused at its chunks, then a save whose header will not read, then a readable A.

    THE RULE PINNED. Only the NEWEST refusal is identified: the walk does not
    re-identify past it, so the world stays A and A is served. The middle
    save's world cannot be read, so it is not known to be another world's: it
    is loaded, refused, and COUNTED under the known world's code - it may be a
    newer save of A, which is what "may be behind the game" warns of - and not
    under the unidentified code, whose detail is about the NEWEST save, which
    was identified.
    """
    cut = synthetic.SAVE_V60.chunk_offset + CHUNK_STUB
    newest = plant(tmp_path / "A.sav", SAME_WORLD[:cut], BASE_SECONDS + 60)
    unknown = plant(tmp_path / "H.sav", SAME_WORLD[:HEADER_STUB], BASE_SECONDS + 30)
    readable = plant(tmp_path / "C.sav", SAME_WORLD, BASE_SECONDS)

    model = world.load_newest_world((newest, unknown, readable), load=load_flat)

    served = model is not None and model.token == synthetic.SYNTHETIC_WORLD_TOKEN
    assert served, "a readable save of the refused newest world was not served"
    flags = all_fallback_flags(model)
    assert flags == [
        (NEWER, "chunks.ChunkTruncatedError", 1),
        (NEWER, "header.HeaderTruncatedError", 1),
    ]


def test_a_header_longer_than_the_identify_prefix_still_names_its_world(tmp_path: Path) -> None:
    """A header the full load reads but the bounded prefix cuts short is not an unknown world.

    Every walk past such a refused newest save ended with no world while a
    readable save of the same world sat next in the ranking.
    """
    header, body = flat_parts(synthetic.SYNTHETIC_WORLD_TOKEN, oversize=True)
    oversize = len(header) > MAX_HEADER_BYTES
    assert oversize, "the header fits the prefix, so this grades nothing"
    newest = plant(tmp_path / "A.sav", header + body[:CHUNK_STUB], BASE_SECONDS + 60)
    readable = plant(tmp_path / "C.sav", SAME_WORLD, BASE_SECONDS)

    model = world.load_newest_world((newest, readable), load=load_flat)

    flags = all_fallback_flags(model)
    assert flags == [(NEWER, "chunks.ChunkTruncatedError", 1)]


def test_a_rebuilt_refusal_raised_inside_a_handler_carries_no_context() -> None:
    """Called while an exception is being handled, the rebuilt refusal still has no context."""

    def inside_a_handler() -> None:
        try:
            raise KeyError(CANARY_CAUSE)
        except KeyError:
            world.refuse_again(world.STAGE_OBJECTS, "ObjectFormatError")

    with pytest.raises(world.WorldLoadError) as caught:
        inside_a_handler()

    bare = (
        caught.value.__context__ is None,
        caught.value.__cause__ is None,
        caught.value.__suppress_context__,
    )
    assert bare == (True, True, True)


def every_frame_rendered(error: BaseException) -> str:
    """Every exception reachable by cause or context, each frame's locals rendered.

    The shape a locals-showing renderer prints - ``capture_locals`` - with the
    suppressed context walked too, because it is still on the object.

    Args:
        error: Where the chain starts.

    Returns:
        The whole rendering.
    """
    parts: list[str] = []
    seen: set[int] = set()
    pending: list[BaseException | None] = [error]
    while pending:
        item = pending.pop()
        if item is None or id(item) in seen:
            continue
        seen.add(id(item))
        rendering = traceback.TracebackException.from_exception(item, capture_locals=True)
        parts.extend(rendering.format())
        pending.extend((item.__cause__, item.__context__))
    return "".join(parts)


def raised_by(walk: Callable[[], object]) -> BaseException:
    """What ``walk`` raised. A helper, so the catching frame holds no canary.

    Args:
        walk: The walk to run.

    Returns:
        The exception it raised.

    Raises:
        AssertionError: It raised nothing.
    """
    try:
        walk()
    except BaseException as error:
        return error
    raise AssertionError("the walk raised nothing")


@pytest.mark.parametrize("readable_older", [True, False], ids=["older-readable", "all-refused"])
def test_a_cause_outside_the_vocabulary_is_rendered_by_no_frame(
    tmp_path: Path, readable_older: bool
) -> None:
    """Fail closed, and keep the refused value out of every frame the failure carries.

    The vocabulary check exists because a cause can be rewritten between the
    reader and the flag; the value it refuses is exactly what must not reach a
    log, and a locals-showing renderer is one (non-negotiable 12).
    """
    newest = plant(tmp_path / "A.sav", SAME_WORLD, BASE_SECONDS + 60)
    older = plant(tmp_path / "B.sav", SAME_WORLD, BASE_SECONDS)
    refusals: dict[str, BaseException] = {
        newest.name: refusal_at(world.STAGE_OBJECTS, CANARY_CAUSE)
    }
    if not readable_older:
        refusals[older.name] = objects_refusal()
    load = Recorder(refusals)

    error = raised_by(lambda: world.load_newest_world((newest, older), load=load))

    refused = isinstance(error, ValueError)
    assert refused, "a cause outside the vocabulary did not fail closed"
    hits = every_frame_rendered(error).count(CANARY_CAUSE)
    assert hits == 0, "a frame of the failure renders the refused cause"
