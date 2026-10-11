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

EVERY ASSERTION IS ON A SCALAR BOUND TO A LOCAL. A ``tmp_path`` lives under a
home directory, so no assertion here renders a path.
"""

from __future__ import annotations

import ast
import inspect
import os
import re
import textwrap
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.save import workdir, world
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
    """End to end through the real reader: garbage newest, synthetic older."""
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
    flags = refused_flags(model)
    assert flags == [(expected, 1)]


def test_the_flag_names_the_stage_and_the_cause_and_never_the_file(tmp_path: Path) -> None:
    """The real defect's shape: an objects-stage refusal of the newest file."""
    newest = plant(tmp_path / "Refused_autosave_0.sav", b"re-encoded", BASE_SECONDS + 60)
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
    newest = plant(tmp_path / "Refused.sav", b"re-encoded", BASE_SECONDS + 60)
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
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
    middle = plant(tmp_path / "B.sav", b"re-encoded", BASE_SECONDS + 30)
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
    first = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
    second = plant(tmp_path / "B.sav", b"re-encoded", BASE_SECONDS + 50)
    third = plant(tmp_path / "C.sav", b"re-encoded", BASE_SECONDS + 40)
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
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
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
    newest = plant(tmp_path / "A.sav", b"re-encoded", BASE_SECONDS + 60)
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
        plant(tmp_path / name, b"re-encoded", BASE_SECONDS + 600 - index)
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
