#!/usr/bin/env python3
"""CS-857 - a chained cause renders its own message, and the redactor never sees it.

THE CHANNEL, NAMED PRECISELY, because the remedy depends on which one it is.
``raise Wrapper(...) from exc`` makes the CAUSE's own text part of the
formatted traceback. The wrapper's message can be perfectly redacted while the
chained ``OSError`` renders the raw path beside it, on the same failure,
under default flags and with no debugging switch turned on. The redactor is
never consulted: the interpreter's own traceback machinery walks
``__cause__`` and ``__context__`` and formats each hop itself.

This module owns the RUNTIME half of that property. It forces the failure at
shipped sites, formats the traceback ITSELF, and grades the string it produced.

WHY NOT A PYTEST REPORT. ``tests/conftest.py`` carries a CS-428
``pytest_runtest_makereport`` hook that redacts the rendered report, chained
cause included. Asserting on a report would therefore measure that redactor
rather than this channel, and would report clean on a tree where the channel
leaks everywhere else - a CLI traceback, a log line, an uncaught exception in
``clockspeed/surface/`` or the Electron shell. Every rendering assertion below
reads a string this module built with ``traceback.format_exception``. That is
structural rather than a flag: there is no report object in this file.

THE ORACLE IS THE REDACTOR'S OWN OUTPUT, WHICH IS WHY NO MARKER IS PLANTED.
The tempting probe - plant a synthetic marker in a directory name, call the
shipped code, assert the marker reaches the traceback - measures the marker.
``clockspeed/data/locate.py::redact`` has no needle for an invented directory
name, so the marker appears in the wrapper's message too and the arm cannot
tell a leak from a non-leak. Here the property is ``redact(rendered) ==
rendered`` over a rendering built from a REAL temporary path, which sits under
the user profile and which redact therefore genuinely rewrites. If redact
rewrote something in the wrapper and the cause renders it verbatim, that IS the
leak, and no synthetic needle took part.

THE ISOLATION, AND IT IS THE LOAD-BEARING DESIGN DECISION HERE. A default
rendering also contains ``File "..."`` frame lines, and on this machine the
standard library lives under the user profile - measured, not assumed. So
``redact(rendered) != rendered`` over a complete rendering is satisfied by the
interpreter's OWN install path, with no chained cause involved at all. An arm
written that way is red before the defect and red after it, which makes it a
permanent red rather than a proof. Every arm here therefore grades
``format_exception(exc, limit=0)``: the real formatter, the whole chain, every
message and every note, and ZERO frame lines. Each arm additionally asserts
that what it graded is a line-subset of the DEFAULT rendering, so the isolated
channel cannot drift away from the channel a user actually sees. The frame-path
question is a different channel and is not this item's.

WHAT EACH ARM CARRIES, because none of the three is optional.

  A NEEDLE CONTROL. ``redact(x) == x`` proves only that redact found nothing,
  so an arm that never establishes redact CAN rewrite the path in play issues a
  false clearance. Every arm first asserts redact demonstrably rewrites the
  temporary root it is about to use. Where it cannot, the arm SKIPS as
  UNPROVEN rather than passing.

  A BASELINE CONTROL. The wrapper's own message, rendered with the chain
  suppressed, must be clean. Without it, a red arm cannot be attributed to the
  cause rather than to the wrapper.

  A FIDELITY CHECK. The graded lines must all appear in the default rendering.

NO ARM REQUIRES THE DEFECT, AND TWO NEAR-MISSES ARE RECORDED BECAUSE THEY LOOK
HARMLESS. The shipped-site arms go GREEN the moment the channel is closed, at
any of the sites, by any means. The synthetic arms build their own chains and
never consult the shipped tree at all, so they hold on a tree with zero chained
raises - which ``test_a_synthetic_tree_with_no_chained_site_renders_clean``
demonstrates directly, by compiling a module that has none and grading it with
the same grader.

The two lines that had to come out both read as ordinary non-vacuity checks.
``assert chain_depth >= 2`` at a shipped site, and ``assert not hop_clean[2]``
at the transitive one, each state that the site STILL CHAINS A DIRTY CAUSE.
Suppressing the cause is a legitimate repair, so both would turn RED on the
repaired tree and their green would have certified the defect was still there.
Non-vacuity is carried by the needle and baseline controls, which survive the
repair; the transitive claim is asserted in its surviving direction - every hop
down to the immediate cause is CLEAN - which yields the same conclusion.

WHAT THIS MODULE DOES NOT ESTABLISH, stated because an overclaim inside a
privacy control is the defect the control exists to catch.

  - It does NOT enumerate the chained-raise sites in ``clockspeed/``. It
    forces a named few. A site added tomorrow is invisible here. That is a
    STATIC question and it belongs to a static guard, which this module
    deliberately does not import: two derivations of one property that share a
    module are one derivation.
  - It does NOT establish that a clean rendering carries no personal data. It
    establishes that the project's own redactor finds nothing to rewrite in it.
    A save-derived word that redact cannot know about passes through untouched,
    exactly as it does everywhere else redact is used.
  - It does NOT cover the frame-location channel, the interpreter path, or
    anything ``-l`` or ``--showlocals`` opens.
  - Nothing here needs a game install, a save library, or any real save. Every
    input is a synthetic path under ``tmp_path``.
"""

from __future__ import annotations

import errno
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from unittest.mock import patch

import pytest

from clockspeed.data.locate import redact
from clockspeed.save import workdir
from clockspeed.save.usmap import UsmapError, load_usmap
from clockspeed.save.workdir import WorkDirError, copy_for_read
from clockspeed.save.world import STAGE_COPY, WorldLoadError, load_world

# The synthetic filename a compiled-in-memory module is given, so its frames
# carry no real path at all. Angle brackets keep linecache from finding source.
SYNTHETIC_FILENAME: Final = "<cs857-synthetic-tree>"

#: Chain depths, named so an arm reads as a claim about SHAPE rather than as a
#: comparison against a bare number. UNCHAINED means the formatter renders one
#: exception and stops - which is what a closed channel looks like.
UNCHAINED: Final = 1
TWO_HOPS: Final = 2
THREE_HOPS: Final = 3

#: How many times the CS-881 deferred-raise shapes go round their retry loop.
#: Named so no bare number sits in a fixture, and small because the loop is the
#: SHAPE the shipped retry sites are written in rather than a timing test.
DEFERRED_ATTEMPTS: Final = 2

#: What a forcing function hands back: the exception it caught, and the root
#: whose redactability is that arm's needle control.
Forced = tuple[BaseException, Path]


def _n(text: object) -> str:
    """Render with forward slashes, matching redact's own first act.

    ``clockspeed/data/locate.py::redact`` collapses backslashes before it does
    anything else, so on Windows ``redact(x) != x`` holds for every string
    containing a backslash whether or not a single needle matched. Comparing
    normalized strings isolates the REDACTION rewrites from that separator
    normalization; without it every arm here would be red for a reason that has
    nothing to do with personal data.

    Args:
        text: Anything renderable.

    Returns:
        The rendering with backslashes collapsed.
    """
    return str(text).replace("\\", "/")


def _rewrites(text: object) -> bool:
    """Report whether the project's redactor rewrites this string.

    Args:
        text: Anything renderable.

    Returns:
        True when redact changes it, which is what "carries something redact
        recognizes as personal" means for every arm in this module.
    """
    rendered = _n(text)
    return redact(rendered) != rendered


def _chain(exc: BaseException) -> list[BaseException]:
    """Walk the cause chain the way the interpreter's formatter walks it.

    ``__cause__`` wins; ``__context__`` follows only when the raise did not
    suppress it. The cycle guard mirrors the formatter's own.

    USED ONLY FOR PER-HOP ATTRIBUTION. The graded property never comes from
    this walk - it comes from :func:`traceback.format_exception`. This exists so
    an arm can say WHICH hop carried the value, which is what distinguishes a
    transitive leak from an immediate one.

    Args:
        exc: The outermost exception.

    Returns:
        The exceptions in rendering order, outermost first.
    """
    out: list[BaseException] = []
    seen: set[int] = set()
    cursor: BaseException | None = exc
    while cursor is not None and id(cursor) not in seen:
        seen.add(id(cursor))
        out.append(cursor)
        if cursor.__cause__ is not None:
            cursor = cursor.__cause__
        elif not cursor.__suppress_context__:
            cursor = cursor.__context__
        else:
            cursor = None
    return out


@dataclass(frozen=True)
class Verdict:
    """One traceback graded. Holds booleans and counts, never rendered text.

    Deliberately carries no string. A local holding the rendered traceback
    would be printed by ``--showlocals`` in the frame where an arm fails, which
    would make this module the leak it grades - see
    ``memory/moving-an-assert-can-create-the-leak.md``. Every field below is a
    scalar, so a failing arm renders a number.
    """

    needle_present: bool
    baseline_clean: bool
    chained_clean: bool
    faithful_subset: bool
    hop_clean: tuple[bool, ...]
    chain_depth: int
    graded_lines: int


def grade(exc: BaseException, needle_root: Path) -> Verdict:
    """Format the traceback here and reduce it to scalars.

    The whole chain's messages and notes, with every frame line dropped by
    ``limit=0`` - the real formatter, not a re-implementation of it. See the
    module docstring for why the frame lines have to go.

    Args:
        exc: The exception to render.
        needle_root: The temporary root this arm used, whose redactability is
            the arm's positive control.

    Returns:
        The verdict. No rendered text escapes this function.
    """
    graded = "".join(traceback.format_exception(exc, limit=0))
    baseline = "".join(traceback.format_exception(exc, limit=0, chain=False))
    default = "".join(traceback.format_exception(exc))

    graded_lines = graded.splitlines()
    return Verdict(
        needle_present=_rewrites(needle_root),
        baseline_clean=not _rewrites(baseline),
        chained_clean=not _rewrites(graded),
        faithful_subset=set(graded_lines) <= set(default.splitlines()),
        hop_clean=tuple(not _rewrites(hop) for hop in _chain(exc)),
        chain_depth=len(_chain(exc)),
        graded_lines=len(graded_lines),
    )


def require_provable(verdict: Verdict) -> None:
    """Skip as UNPROVEN unless both controls hold.

    A green arm whose needle control failed is a FALSE CLEARANCE - redact found
    nothing because it had nothing it could find - and a red arm whose baseline
    failed cannot be attributed to the cause. Neither is worth reporting as a
    result, so the arm says UNPROVEN out loud instead. See
    ``memory/a-guard-can-measure-spelling.md`` on a false clearance being worse
    than a silence.

    Args:
        verdict: The verdict to check.
    """
    if not verdict.needle_present:
        pytest.skip("UNPROVEN: redact has no needle for this temporary root")
    if not verdict.baseline_clean:
        pytest.skip("UNPROVEN: the wrapper's own message is not clean")
    if not verdict.faithful_subset:
        pytest.skip("UNPROVEN: the graded lines are not a subset of the default rendering")


# ---------------------------------------------------------------------------
# Forcing the five OSError-rooted shipped sites
#
# Each forcer drives the SHIPPED statement. Four of the five reach it through
# the real filesystem with nothing patched; the fifth is marked FORCED in its
# docstring and in its site label, because making ``Path.is_file`` fail with a
# non-ignored OSError is not something a test can arrange for real on Windows.
# ---------------------------------------------------------------------------


def _readable_save(tmp: Path) -> Path:
    """Write a real, readable source file for the workdir arms.

    Args:
        tmp: The temporary root.

    Returns:
        The path of the file.
    """
    source = tmp / "probe.sav"
    source.write_bytes(b"not a real save, and never parsed by any arm here")
    return source


def force_usmap_read(tmp: Path) -> Forced:
    """Force ``clockspeed/save/usmap.py::load_usmap`` against a directory.

    ``path.read_bytes()`` on a directory raises OSError, which the shipped
    site re-raises as ``UsmapError`` from that cause. Nothing is patched.

    Args:
        tmp: The temporary root.

    Returns:
        The caught wrapper and the needle root.
    """
    target = tmp / "mapping_is_a_directory"
    target.mkdir()
    try:
        load_usmap(target)
    except UsmapError as exc:
        return exc, tmp
    pytest.fail("clockspeed/save/usmap.py::load_usmap accepted a directory")


def force_workdir_make_dir(tmp: Path) -> Forced:
    """Force ``clockspeed/save/workdir.py::_make_dir`` through ``copy_for_read``.

    The copies directory is pre-created as a FILE, so ``mkdir(exist_ok=True)``
    raises - ``exist_ok`` forgives an existing directory and not an existing
    file. Nothing is patched.

    Args:
        tmp: The temporary root.

    Returns:
        The caught wrapper and the needle root.
    """
    source = _readable_save(tmp)
    root = tmp / "work_root"
    root.mkdir()
    (root / workdir.COPIES_DIR_NAME).write_bytes(b"a file where a directory belongs")
    try:
        copy_for_read(source, work_root=root)
    except WorkDirError as exc:
        return exc, tmp
    pytest.fail("clockspeed/save/workdir.py::copy_for_read wrote into a file")


def force_workdir_stream_copy(tmp: Path) -> Forced:
    """Force the ``_stream_copy`` handler in ``clockspeed/save/workdir.py``.

    The partial file's name is pre-created as a DIRECTORY, so opening it for
    write raises OSError inside the shipped copy loop. Nothing is patched.

    Args:
        tmp: The temporary root.

    Returns:
        The caught wrapper and the needle root.
    """
    source = _readable_save(tmp)
    root = tmp / "work_root"
    copies = root / workdir.COPIES_DIR_NAME
    copies.mkdir(parents=True)
    partial = copies / (source.stem + workdir.COPY_SUFFIX + workdir.PARTIAL_SUFFIX)
    partial.mkdir()
    try:
        copy_for_read(source, work_root=root)
    except WorkDirError as exc:
        return exc, tmp
    pytest.fail("clockspeed/save/workdir.py::copy_for_read opened a directory for write")


def force_workdir_rename(tmp: Path) -> Forced:
    """Force the ``_replace_with_retry`` handler in ``clockspeed/save/workdir.py``.

    The destination name is pre-created as a DIRECTORY, so the rename of the
    finished copy onto it raises after the copy itself succeeded. Nothing is
    patched.

    Args:
        tmp: The temporary root.

    Returns:
        The caught wrapper and the needle root.
    """
    source = _readable_save(tmp)
    root = tmp / "work_root"
    copies = root / workdir.COPIES_DIR_NAME
    copies.mkdir(parents=True)
    (copies / (source.stem + workdir.COPY_SUFFIX)).mkdir()
    try:
        copy_for_read(source, work_root=root)
    except WorkDirError as exc:
        return exc, tmp
    pytest.fail("clockspeed/save/workdir.py::copy_for_read renamed a copy onto a directory")


def force_workdir_readable_source(tmp: Path) -> Forced:
    """Force the ``_readable_source`` handler in ``clockspeed/save/workdir.py``.

    FORCED, and stated as such. The shipped handler catches an OSError out of
    ``Path.is_file``, and ``pathlib`` swallows every errno a test could arrange
    on Windows - a missing path, a path through a file and an unresolvable name
    all return False rather than raising. So ``is_file`` is replaced, for the
    duration of one call, with one that raises the OSError the real filesystem
    would raise on a permission failure, carrying the real temporary path as
    its filename exactly as the operating system would.

    THE SHIPPED STATEMENT STILL RUNS. What is replaced is the operating
    system's answer, not the ``raise ... from exc`` under test.

    Args:
        tmp: The temporary root.

    Returns:
        The caught wrapper and the needle root.
    """
    source = _readable_save(tmp)
    root = tmp / "work_root"
    root.mkdir()

    def denied(self: Path) -> bool:
        raise PermissionError(errno.EACCES, "permission denied", str(self))

    try:
        with patch.object(Path, "is_file", denied):
            copy_for_read(source, work_root=root)
    except WorkDirError as exc:
        return exc, tmp
    pytest.fail("clockspeed/save/workdir.py::copy_for_read ignored an unreadable source")


#: The five OSError-rooted shipped sites, by the module and callable that owns
#: each. Labels are full repo-relative paths; a bare basename is a dead
#: citation. No line number is written down: a line number in a test is a
#: pointer that the next edit above it silently invalidates.
OSERROR_ROOTED_SITES: Final[tuple[tuple[str, Callable[[Path], Forced]], ...]] = (
    ("clockspeed/save/usmap.py::load_usmap", force_usmap_read),
    ("clockspeed/save/workdir.py::_make_dir", force_workdir_make_dir),
    ("clockspeed/save/workdir.py::_stream_copy handler", force_workdir_stream_copy),
    ("clockspeed/save/workdir.py::_replace_with_retry handler", force_workdir_rename),
    ("clockspeed/save/workdir.py::_readable_source (FORCED)", force_workdir_readable_source),
)


@pytest.mark.parametrize(
    ("site", "forcer"),
    OSERROR_ROOTED_SITES,
    ids=[label for label, _ in OSERROR_ROOTED_SITES],
)
def test_an_oserror_rooted_site_renders_a_redactable_path(
    site: str,
    forcer: Callable[[Path], Forced],
    tmp_path: Path,
) -> None:
    """A4 - the cause's message reaches the traceback and redact rewrites it.

    RED until the channel is closed, GREEN the moment it is, by any means at
    any of the five sites. The baseline control in the same verdict is what
    makes a red here attributable to the CAUSE rather than to the wrapper.

    NOTHING HERE ASSERTS THAT THE SITE STILL CHAINS, and the omission is
    deliberate. ``assert chain_depth >= 2`` reads like a harmless non-vacuity
    check and is not one: suppressing the cause is a legitimate repair, and an
    arm carrying that line would go RED on the repaired tree - so its green
    would certify that the defect is still present. Non-vacuity is carried by
    the needle and baseline controls instead, and both survive the repair.
    """
    exc, needle_root = forcer(tmp_path)
    verdict = grade(exc, needle_root)
    require_provable(verdict)

    assert verdict.hop_clean[0], f"{site}: the wrapper's own hop was not clean"
    assert verdict.chained_clean, (
        f"{site}: the chained rendering carries text the redactor rewrites, "
        f"while the wrapper's own message does not - {verdict.graded_lines} lines graded"
    )


def test_every_oserror_rooted_site_was_actually_provable(tmp_path: Path) -> None:
    """The census - an arm that skipped is not an arm that passed.

    Without this, every arm above could skip as UNPROVEN and the module would
    report success while grading nothing. See
    ``memory/an-empty-population-satisfies-every-zero.md``. This arm holds
    whether or not the channel leaks, so it does not require the defect.
    """
    provable = 0
    for index, (_site, forcer) in enumerate(OSERROR_ROOTED_SITES):
        root = tmp_path / f"site_{index}"
        root.mkdir()
        exc, needle_root = forcer(root)
        verdict = grade(exc, needle_root)
        if verdict.needle_present and verdict.baseline_clean and verdict.faithful_subset:
            provable += 1
    assert provable == len(OSERROR_ROOTED_SITES), (
        f"only {provable} of {len(OSERROR_ROOTED_SITES)} sites were provable; "
        "the rest reported UNPROVEN and graded nothing"
    )


# ---------------------------------------------------------------------------
# A5 - transitivity, at a world.py re-wrap whose wrapper is structurally
# path-free
# ---------------------------------------------------------------------------


def force_world_rewrap(tmp: Path, monkeypatch: pytest.MonkeyPatch) -> WorldLoadError:
    """Force ``clockspeed/save/world.py::load_world`` to re-wrap a WorkDirError.

    The copies directory is pre-created as a FILE, exactly as in
    :func:`force_workdir_make_dir`, and the work root is pointed at it through
    the environment variable ``clockspeed/save/workdir.py`` documents as its own
    override. Nothing is patched: the failure travels the shipped path from the
    operating system up through two shipped re-raises.

    Args:
        tmp: The temporary root.
        monkeypatch: Used only to set the documented work-root override.

    Returns:
        The caught wrapper.
    """
    source = _readable_save(tmp)
    root = tmp / "work_root"
    root.mkdir()
    (root / workdir.COPIES_DIR_NAME).write_bytes(b"a file where a directory belongs")
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(root))
    try:
        load_world(source)
    except WorldLoadError as exc:
        return exc
    pytest.fail("clockspeed/save/world.py::load_world loaded an uncopyable save")


def test_a_world_rewrap_leaks_through_a_clean_immediate_cause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A5 - hop 2 carries the value while hops 0 and 1 are both clean.

    ``clockspeed/save/world.py::load_world`` wraps a ``WorkDirError`` as
    ``WorldLoadError(STAGE_COPY, type(exc).__name__)`` - a stage constant and a
    type name, structurally incapable of holding a path. Its immediate cause,
    the ``WorkDirError`` out of ``clockspeed/save/workdir.py``, renders its path
    through ``locate.redact`` and is clean too. The raw path is two hops down.

    So the leak cannot be satisfied by the wrapper, and a check that reads only
    ``__cause__`` is blind to it. Both halves are asserted here rather than
    described, because a described control is not a control.

    THE TRANSITIVITY IS ASSERTED IN THE DIRECTION THAT SURVIVES THE REPAIR.
    ``assert not hop_clean[2]`` would say "hop 2 is dirty", which is the defect
    itself, and an arm carrying it is GREEN ONLY WHILE THE DEFECT LIVES. What
    is asserted instead is that every hop DOWN TO AND INCLUDING the immediate
    cause is clean - true today and still true once the channel is closed - so
    a leak in the rendering cannot have entered above hop 2. That delivers the
    same conclusion and inverts the failure direction.
    """
    wrapper = force_world_rewrap(tmp_path, monkeypatch)
    verdict = grade(wrapper, tmp_path)
    require_provable(verdict)

    # The wrapper's whole message is composed from these two fields, and both
    # are closed vocabulary - a stage constant and a class name. That is what
    # "structurally path-free" means here, and it is asserted rather than
    # assumed, because the arm below is only interesting if the wrapper had no
    # opportunity to carry the path in the first place.
    assert wrapper.stage == STAGE_COPY, f"wrong stage: {wrapper.stage!r}"
    assert wrapper.cause_type == WorkDirError.__name__, f"wrong cause type: {wrapper.cause_type!r}"
    assert verdict.hop_clean[0], "hop 0, the wrapper, was expected to be structurally path-free"
    if verdict.chain_depth > UNCHAINED:
        # Only while a chain exists. Suppressing the cause is a legitimate
        # repair, and it leaves no hop 1 to grade rather than a dirty one.
        assert verdict.hop_clean[1], "hop 1, the immediate cause, was expected to be redacted"
    assert verdict.chained_clean, (
        "the rendering leaks through a clean wrapper and a clean immediate cause: "
        f"{verdict.graded_lines} lines graded, chain depth {verdict.chain_depth}"
    )


# ---------------------------------------------------------------------------
# The escape shapes. Each is a synthetic chain built here, so none of them
# consults the shipped tree and none can be repaired away by fixing a site.
# Each asserts that a naive remedy or a naive detector FAILS to close or see
# the channel - which is the thing a positive control on the modelled shape
# cannot establish. See memory/a-guard-can-measure-spelling.md.
# ---------------------------------------------------------------------------


class SentinelError(Exception):
    """A wrapper whose own message is clean by construction."""


def _raw_oserror(path: Path) -> OSError:
    """Build the OSError shape the operating system produces for a real path.

    Args:
        path: A real temporary path, which redact recognizes.

    Returns:
        The error, carrying the path as its filename exactly as the OS would.
    """
    return PermissionError(errno.EACCES, "permission denied", str(path))


def _identity(exc: BaseException) -> BaseException:
    """Return its argument, so a cause can be a CALL rather than a name.

    Args:
        exc: Any exception.

    Returns:
        The same exception.
    """
    return exc


def test_deleting_from_exc_falls_through_to_context_and_still_leaks(tmp_path: Path) -> None:
    """Escape 1 - removing ``from exc`` does not close the channel.

    Raising inside a handler sets ``__context__`` whether or not a cause was
    named, and the default formatter renders that too. So the obvious remedy is
    not a remedy, and a detector keyed on ``ast.Raise.cause`` being non-None
    cannot see this shape at all.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError:
            # The suppression below is the ARM, not a waiver. B904 asks for
            # `from err` or `from None`; this shape is the one that has
            # NEITHER, and the point of the arm is that Python chains it
            # anyway through __context__. Obeying the rule would delete the
            # test.
            raise SentinelError("clean message, no path")  # noqa: B904
    except SentinelError as exc:
        wrapper = exc

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.baseline_clean, "the wrapper's own message was not clean"
    assert verdict.chain_depth == TWO_HOPS, f"context was not chained, depth {verdict.chain_depth}"
    assert not verdict.chained_clean, (
        "a raise with no cause rendered clean, so this escape shape no longer "
        "demonstrates that deleting `from exc` is not the fix"
    )


def test_an_aliased_cause_still_leaks(tmp_path: Path) -> None:
    """Escape 2 - one assignment moves the cause to a name nothing watches.

    ``kept = exc`` is all it takes. Any check that resolves the handler's bound
    name reports a non-finding here while the rendering leaks exactly as much.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError as exc:
            kept = exc
            raise SentinelError("clean message, no path") from kept
    except SentinelError as exc:
        wrapper = exc

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.baseline_clean, "the wrapper's own message was not clean"
    assert not verdict.chained_clean, "an aliased cause rendered clean"


def test_a_call_expression_cause_still_leaks(tmp_path: Path) -> None:
    """Escape 3 - the cause need not be a name at all.

    ``from _identity(exc)`` is a ``ast.Call`` node. A detector that reads
    ``ast.Name`` cause nodes sees nothing here.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError as exc:
            raise SentinelError("clean message, no path") from _identity(exc)
    except SentinelError as exc:
        wrapper = exc

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.baseline_clean, "the wrapper's own message was not clean"
    assert not verdict.chained_clean, "a call-expression cause rendered clean"


def _raise_with_a_note(path: Path) -> None:
    """Raise a clean-messaged error carrying the path only as a note.

    Args:
        path: A real temporary path, which redact recognizes.

    Raises:
        SentinelError: Always. Its message holds no path; the note does.
    """
    exc = SentinelError("clean message, no path")
    exc.add_note(f"while reading {path}")
    raise exc


def test_add_note_reaches_the_traceback_without_any_chain(tmp_path: Path) -> None:
    """Escape 4 - a note renders too, and there is no cause to inspect.

    ``BaseException.add_note`` attaches text that the formatter prints under
    default flags. It reaches neither ``args`` nor ``__cause__``, so both the
    message-content guards and every chain check are structurally blind to it.
    Here the BASELINE is dirty on purpose - the note is on the wrapper itself -
    which is what distinguishes this shape from the three above.
    """
    with pytest.raises(SentinelError) as caught:
        _raise_with_a_note(tmp_path)

    wrapper = caught.value
    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.chain_depth == UNCHAINED, f"expected no chain at all, got {verdict.chain_depth}"
    assert not verdict.baseline_clean, "the note did not reach the unchained rendering"
    assert not verdict.chained_clean, "the note rendered clean"


def _deferred_raise_of_a_stored_binding(path: Path) -> None:
    """Store the handler's own binding, then raise it after the handler exits.

    WRITTEN THE WAY THE SHIPPED RETRY LOOPS WRITE IT: a bounded loop, the last
    failure kept in a local, and the raise below the loop where no handler is
    active and no cause is named.

    Args:
        path: A real temporary path, which redact recognizes.

    Raises:
        OSError: Always, and it is the CAUGHT one rather than a wrapper.
    """
    last: OSError | None = None
    for _attempt in range(DEFERRED_ATTEMPTS):
        try:
            raise _raw_oserror(path)
        except OSError as exc:
            last = exc
    if last is None:
        last = OSError("nothing was recorded")
    raise last


def test_a_deferred_raise_of_a_stored_binding_leaks_with_no_chain(tmp_path: Path) -> None:
    """Escape 5 - the handler's binding outlives the handler, and so does the path.

    CS-881. THE SHAPE HAS NO CHAIN AT ALL, which is what makes it different
    from the four above rather than a fifth spelling of them. ``__cause__`` is
    None, ``__context__`` is None because the handler had already exited, and
    the depth is ONE. Every check written against a chain - and every static
    walk keyed on ``ast.Raise.cause`` or on a raise sitting lexically inside a
    handler - is structurally blind here, while the rendering carries the same
    path a graded site would: the object raised IS the caught ``OSError``, so
    ``OSError.__str__`` appends the ``filename`` the interpreter attached.

    THE BASELINE IS DIRTY ON PURPOSE, as it is in escape 4. There is no
    wrapper to be clean: the leak is the raised exception itself.
    """
    with pytest.raises(OSError, match="permission denied") as caught:
        _deferred_raise_of_a_stored_binding(tmp_path)

    verdict = grade(caught.value, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.faithful_subset, "the graded lines were not a subset of the default rendering"
    assert verdict.chain_depth == UNCHAINED, (
        f"the deferred raise chained {verdict.chain_depth} link(s); a chain "
        "would mean this shape is visible to a cause walk after all"
    )
    assert not verdict.baseline_clean, (
        "the raised exception's own rendering was clean, so this shape is not "
        "the leak it is planted to demonstrate"
    )
    assert not verdict.chained_clean, "a deferred raise of a stored binding rendered clean"


# ---------------------------------------------------------------------------
# The controls. Every one of these is GREEN now and stays green when the
# channel is closed - none requires the defect.
# ---------------------------------------------------------------------------


def test_from_none_closes_the_channel(tmp_path: Path) -> None:
    """The control - the same failure, the cause suppressed, renders clean.

    This is the shape ``clockspeed/save/header.py`` already uses. It is the
    proof that a clean verdict is REACHABLE from a dirty cause, which is what
    makes a red arm above a finding rather than an artifact of the grader.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError:
            raise SentinelError("clean message, no path") from None
    except SentinelError as exc:
        wrapper = exc

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.chain_depth == UNCHAINED, (
        f"the cause was not suppressed, depth {verdict.chain_depth}"
    )
    assert verdict.faithful_subset, "the graded lines were not a subset of the default rendering"
    assert verdict.chained_clean, "a suppressed cause still rendered a redactable path"


def test_a_chain_whose_every_hop_is_clean_renders_clean(tmp_path: Path) -> None:
    """Clean transitivity - a three-hop chain carrying nothing redactable.

    The mirror of the A5 arm. Three hops, a real chain rendered by the real
    formatter, and a clean verdict - so a red A5 is about the CONTENT of a hop
    and not about chaining as such.
    """
    try:
        try:
            try:
                raise SentinelError(f"innermost, redacted: {redact(tmp_path)}")
            except SentinelError as inner:
                raise SentinelError("middle, no path") from inner
        except SentinelError as middle:
            raise SentinelError("outermost, no path") from middle
    except SentinelError as exc:
        wrapper = exc

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.chain_depth == THREE_HOPS, (
        f"expected a three-hop chain, got {verdict.chain_depth}"
    )
    assert all(verdict.hop_clean), f"a hop was dirty: {verdict.hop_clean}"
    assert verdict.chained_clean, "a chain of clean hops rendered something redactable"


def _deferred_raise_of_a_pathless_clone(path: Path) -> None:
    """The repair - keep the failure, raise a clone built from errno and strerror.

    THE IDIOM THE TREE ALREADY SHIPS FOUR COPIES OF. ``errno`` is an integer
    code and ``strerror`` is the platform's own text for it; ``filename`` and
    ``filename2`` - the two fields ``OSError.__str__`` appends a path from -
    are absent by construction rather than by redaction.

    Args:
        path: A real temporary path, which redact recognizes.

    Raises:
        OSError: Always, and it carries no path.
    """
    last: OSError | None = None
    for _attempt in range(DEFERRED_ATTEMPTS):
        try:
            raise _raw_oserror(path)
        except OSError as exc:
            last = exc
    if last is None:
        last = OSError("nothing was recorded")
    raise OSError(last.errno, last.strerror)


def test_a_deferred_raise_of_a_pathless_clone_renders_clean(tmp_path: Path) -> None:
    """The control for escape 5 - a clean verdict is REACHABLE from that shape.

    CS-881. Without this, the red arm above is not a finding about the deferred
    shape: it could be a property of raising anything at all after a handler
    that touched a path. The same loop, the same caught failure, the same
    needle armed - and the rendering carries nothing redact rewrites.
    """
    with pytest.raises(OSError, match="permission denied") as caught:
        _deferred_raise_of_a_pathless_clone(tmp_path)

    verdict = grade(caught.value, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.faithful_subset, "the graded lines were not a subset of the default rendering"
    assert verdict.chain_depth == UNCHAINED, (
        f"the clone was chained to something, depth {verdict.chain_depth}"
    )
    assert verdict.chained_clean, "a clone built from errno and strerror rendered a path"


#: A module with ZERO chained raises, compiled with a synthetic filename so its
#: frames carry no real path. This is the defect-free tree the arms are run
#: against, and it is built here rather than derived from the current state of
#: ``clockspeed/`` - a proof whose cases come from today's tree encodes today's
#: defects as its passing condition. See memory/a-proof-can-require-the-defect.md.
TREE_WITHOUT_A_CHAINED_SITE: Final = '''
"""A synthetic module that chains nothing."""


class SyntheticError(Exception):
    """Raised with the cause deliberately suppressed."""


def refuse(path, redactor):
    """Fail on a path, chaining nothing, rendering only a redacted form."""
    try:
        path.read_bytes()
    except OSError:
        raise SyntheticError("unreadable: " + redactor(path)) from None
'''


def test_a_synthetic_tree_with_no_chained_site_renders_clean(tmp_path: Path) -> None:
    """A7 - the grader returns GREEN on a tree that has no chained site.

    Run against a module built to have none, every control still armed - the
    needle holds, so a leak WOULD have been caught - the verdict is clean. That
    is what makes each red arm above a statement about the shipped tree rather
    than a property of this module's grader.
    """
    namespace: dict[str, object] = {}
    exec(compile(TREE_WITHOUT_A_CHAINED_SITE, SYNTHETIC_FILENAME, "exec"), namespace)  # noqa: S102
    refuse = namespace["refuse"]
    error_type = namespace["SyntheticError"]
    assert isinstance(error_type, type), "the synthetic tree did not define its exception"

    target = tmp_path / "a_directory"
    target.mkdir()
    try:
        refuse(target, redact)  # type: ignore[operator]
    except error_type as exc:  # type: ignore[misc]
        wrapper = exc
    else:
        pytest.fail("the synthetic tree accepted a directory")

    verdict = grade(wrapper, tmp_path)
    assert verdict.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert verdict.chain_depth == UNCHAINED, (
        f"the synthetic tree chained something, {verdict.chain_depth}"
    )
    assert verdict.faithful_subset, "the graded lines were not a subset of the default rendering"
    assert verdict.chained_clean, "a tree with no chained site still rendered a redactable path"


def test_the_grader_separates_a_dirty_chain_from_a_clean_one(tmp_path: Path) -> None:
    """The grader discriminates - the positive control on the grader itself.

    ``assert not leaked`` passes equally when nothing was ever planted, so the
    grader is run over two chains that differ ONLY in whether the cause carries
    the path, and the two verdicts are required to disagree. Without this, every
    green arm in this module is consistent with a grader that always says clean.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError as inner:
            raise SentinelError("clean message, no path") from inner
    except SentinelError as exc:
        dirty = grade(exc, tmp_path)

    try:
        try:
            raise SentinelError("innermost, no path")
        except SentinelError as inner:
            raise SentinelError("clean message, no path") from inner
    except SentinelError as exc:
        clean = grade(exc, tmp_path)

    assert dirty.needle_present, "UNPROVEN: redact has no needle for this temporary root"
    assert dirty.chain_depth == clean.chain_depth == TWO_HOPS, (
        "the two chains are not the same shape"
    )
    assert clean.chained_clean, "the clean chain was graded dirty"
    assert not dirty.chained_clean, "the dirty chain was graded clean"


def test_the_graded_channel_is_a_subset_of_what_default_flags_render(tmp_path: Path) -> None:
    """The isolation is faithful - nothing graded here is invisible to a user.

    ``limit=0`` removes frame lines and changes no message line. If that ever
    stopped being true, every arm in this module would be grading a channel
    nobody sees. Asserted against a real chain rather than described.
    """
    try:
        try:
            raise _raw_oserror(tmp_path)
        except OSError as inner:
            raise SentinelError("clean message, no path") from inner
    except SentinelError as exc:
        wrapper = exc

    graded = "".join(traceback.format_exception(wrapper, limit=0))
    default = "".join(traceback.format_exception(wrapper))
    graded_lines = graded.splitlines()

    frame_lines = [line for line in graded_lines if line.lstrip().startswith('File "')]
    assert not frame_lines, f"{len(frame_lines)} frame lines survived limit=0"
    assert set(graded_lines) <= set(default.splitlines()), "graded a line the default never renders"
    assert len(graded_lines) < len(default.splitlines()), "limit=0 removed nothing at all"
