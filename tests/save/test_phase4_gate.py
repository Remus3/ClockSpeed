"""The CS-400 phase 4 gate: the four acceptance clauses, graded honestly.

READ THIS BLOCK BEFORE CITING A GREEN RUN OF THIS FILE AS PROOF OF ANYTHING.
============================================================================
A green run of this module does NOT mean CS-400 may close. One of the four
acceptance clauses is blocked on work that has not been done, and this module
is written so that the blocked clause is visibly skipped rather than quietly
absent. The status of each clause, as this module measures it:

    CLAUSE 1  a real world parses .. MET via the building path, test_inventory_library
    CLAUSE 2  a corrupted save produces a clean error ......... MET
    CLAUSE 3  a truncated save produces a clean error ......... MET
    CLAUSE 4  the save directory is never opened for write .... MET

**CLAUSE 1 IS STILL PARTIAL, AND THE REASON CHANGED COMPLETELY UNDER CS-407.**
Read the new reason rather than assuming it is the old one, because the old one
is gone and the replacement is much easier to overlook.

It used to be partial on COVERAGE: only one of the four real (header version,
save version) pairs had a derived body layout, the other three were refused by
design, and eleven of the fourteen saves on this machine could not be loaded at
all. That is fixed. All four pairs are measured, and
``test_every_real_save_in_the_library_loads_through_the_one_entry_point``
sweeps the whole library through ``load_world`` rather than sampling one file.

It is now partial on DEPTH. **What CS-407 measured is the body SKELETON, not
the body.** Roughly three quarters of every real body is opaque property
payload the walk steps over by its declared length - 69.5% to 77.7% across the
eight real save-52 files, and 12100463 of 18086289 bytes on the one real
save-42 file. The framing is consumed to the exact final byte and the CONTENTS
of the objects are not read at all. So a real world "parses" in the sense that
its structure is fully accounted for, and does not parse in the sense a
consumer of this data will eventually need.

A pair outside the measured set is still refused eagerly with
``UnsupportedBodyLayoutError``, which is non-negotiable 7 working - flagged and
refused, never a silently wrong world. Since CS-407 that means a pair occurring
in no real save; ``synthetic.SAVE_CROSS`` is the fixture that carries the case.

``test_a_real_world_parses_end_to_end`` still selects the newest save OF A
MEASURED PAIR rather than the newest save. That is no longer load-bearing on
this library, where every pair is measured, and it is kept because the property
it defends against - a library whose newest file is an unmeasured pair failing a
test while the reader behaves exactly as specified - returns the moment a new
game build ships a fifth pair.

CS-400 MUST NOT CLOSE ON THIS, and the skeleton limit above is why.

What IS provable against a real save today is asserted by
``test_a_real_save_reaches_the_body_partial``, and it is named a partial
because that is what it is: the save is FOUND, the header PARSES, its version
is supported, the token is the measured width, and the chunk walk yields a
non-empty payload over at least one chunk. The object walk is not attempted.
That test is skip-if-absent: CI has no save library, and a clause that cannot
be graded in CI is stated as such rather than implied to have passed.

**CS-402 SHIPPED (docs/LEDGER.md, 2026-08-15) - WHAT IT RESTED ON.** All four save
versions in the operator's library now parse. Save version 42 used to be
refused by design because its transform delta was unmeasured; CS-407 measured
it at 4, against a real body, using a corroborator independent of the section
arithmetic - every actor rotation is a unit quaternion, and 17763 of 17763
actors give one at shift 4. ``test_the_loadable_version_set_is_four_of_four``
asserts that shape.

What CS-402 left in force is the same skeleton limit as clause 1, plus the rule
the old refusal existed to protect: a version with no measured delta must still
RAISE rather than default to a plausible neighbour's value. That rule is now
pinned against a version nobody has measured, so it survives the example that
used to carry it.

WHAT THE NO-WRITE CLAUSE NEEDS, AND WHY ONE SIGNAL IS NOT ENOUGH
================================================================
Clause 4 is the clause with the most ways to look convincing while proving
nothing, so it is carried by THREE INDEPENDENT SIGNALS, each with its own
companion test that proves the detector can actually fail:

  SIGNAL 1 - a runtime audit hook, in a CHILD PROCESS. The child installs
    ``sys.addaudithook`` BEFORE importing ``clockspeed.save`` and records every
    file-mutating event whose path lands under a pretend save root. A child is
    required twice over: an audit hook cannot be uninstalled once installed,
    and it must be in place before the import it is auditing.
    THE RECORDER IS A SPY, NEVER A RAISER. A hook that raised would be vacuous
    against this layer, which is deliberately fail-soft - ``workdir._save_files``
    and ``purge_work_dir`` both swallow ``OSError`` by design, so a raising spy
    would be caught by the code under test and the run would go green having
    proven nothing.
    THE MANDATORY HALF IS THE READ COUNT. Asserting "no write happened" passes
    perfectly for a ``load_world`` that opened nothing at all, so
    ``test_the_audited_load_actually_read_the_save`` asserts a NON-ZERO number
    of read opens under the pretend root. Without it the whole signal is a
    tautology.

  SIGNAL 2 - a filesystem fingerprint. Entry set, name, size, ``st_mtime_ns``,
    ``st_ctime_ns`` and the sha256 of every byte under the pretend save root,
    taken before the parse and recomputed after. This catches a write the audit
    hook cannot see, and its companion mutates a single fixture byte to prove
    the comparison fails when it should.

  SIGNAL 3 - a static AST gate over ``clockspeed/save/``. **IT COVERS
    ``os.open`` WITH FLAGS, and that is not decoration.** Measured this
    session: a scan that inspects only mode strings returns EMPTY for
    ``os.open(p, os.O_WRONLY | os.O_CREAT)``, so a mode-only gate would wave a
    real flag-based write straight through. The scanned file set is asserted
    EQUAL to a pinned tuple, so a rename or a new module fails the gate instead
    of silently shrinking its coverage.

A FOURTH SIGNAL WAS CONSIDERED AND REJECTED, recorded here so it is not
proposed again: making the pretend save root read-only through Windows ACLs.
ACL behaviour differs between a privileged local account and a CI runner, so
the test would pass for the wrong reason on at least one of them, and a check
that passes for the wrong reason is worse than no check.

(That sentence originally named the privileged account type directly, and the
commit gate BLOCKED it: on this machine that word is also the Windows account
name, so it matched as a whole word. The gate was right and the prose was
changed. It is a live instance of the collision class CS-209 exists to handle,
and it diagnosed itself to file, line and column on the first block rather than
sending anyone hunting - which is the measurement CS-208's denial rested on.)

WHAT CLAUSE 4 COVERS HERE, AND WHAT IT DOES NOT
===============================================
CS-400's clause names THE SAVE DIRECTORY, and that is what signals 1 and 2
measure: a pretend save root, fingerprinted and audited around a real load.
THE GAME INSTALL DIRECTORY IS NOT SEPARATELY FINGERPRINTED BY THIS MODULE.
Non-negotiable 1 covers both, and the install half is carried elsewhere -
``workdir._forbidden_roots`` refuses a destination inside the install and
``tests/save/test_workdir.py`` owns that refusal. Signal 3 is the one check
here that covers both at once, because a write-capable call site is forbidden
outright regardless of which directory it would have aimed at. Stated so that
"clause 4 is MET" is not read as "nothing anywhere is ever written".

WHY THE RECORDER STORES A COUNT AND NEVER A PATH
================================================
Measured while building this module: on Windows the temporary directory
resolves through an 8.3 short name, so ``Path.resolve()`` expands it into a
path containing the Windows account name. A recorder that logged raw paths
would therefore print personal data into CI logs and pytest failure output -
non-negotiable 3, and exactly the echo path non-negotiable 12 governs. The
child records the EVENT, how many of its arguments landed under the root, the
normalised mode and the integer flags, and never the path itself.

That same short-name expansion is why the pretend root is passed to the child
in BOTH spellings. A child matching only the raw spelling records nothing at
all, and every assertion in signal 1 would pass vacuously. That failure was
observed directly - the first working draft of the harness returned zero
records against a load that demonstrably read the file - and the read-count
assertion is what caught it.

TWO MEASURED FACTS THE AUDIT ASSERTIONS DEPEND ON
=================================================
Both re-measured on this interpreter rather than taken from documentation, and
both pinned by ``test_the_measured_audit_event_shapes_still_hold`` so a CPython
change makes this module red rather than silently blind:

  * ``os.open`` does NOT raise an ``os.open`` audit event. It raises ``open``,
    with ``mode`` as None and the integer flags in the third argument. A
    recorder watching for the name ``os.open`` sees nothing, which is precisely
    how a flag-based write would go unnoticed.
  * The ``open`` event NORMALISES the mode: ``"rb"`` is reported as ``"r"`` and
    ``"wb"`` as ``"w"``. An assertion written against ``"wb"`` never fires.
  * ``Path.replace`` raises ``os.rename`` and ``Path.unlink`` raises
    ``os.remove``, so the mutating-event watch list is stated in terms of the
    OS-level event names rather than the pathlib method names.

THIS MODULE RENDERS NO TRACEBACK AND NO EXCEPTION OBJECT
========================================================
``tests/test_exception_rendering.py`` sweeps the whole tree and fails on a new
unguarded traceback rendering. This module needs no residual entry there: it
asserts on ``type(exc).__name__`` and on the two closed-vocabulary fields
``WorldLoadError`` publishes, and never formats the exception object or its
traceback.

WHY THE CHILD-PROCESS HELPERS ARE RE-DERIVED RATHER THAN IMPORTED
=================================================================
``tests/data/test_phase2_gate.py`` and ``tests/solve/test_phase3_gate.py`` each
carry their own ``no_install_env`` and child runner, and this module carries a
third. That is deliberate and is the same reasoning the phase 3 gate records: a
shared helper between gates is a single point of failure that makes all of them
wrong the same way, and agreement between checks derived from one source is not
evidence (CLAUDE.md section 5). Each gate stands on its own.

Nothing here requires a game install, nothing here writes to one, and no real
save is ever read except by the two explicitly skip-if-absent tests.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.data import locate
from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
)
from clockspeed.save import chunks, header, objects, workdir, world

# `test_properties` supplies the CONTAINED discovery, the two forced-failure
# pairs and the library-reach guard, all imported rather than transcribed - see
# the CS-429 section at the foot of this file.
from tests.save import reach_guard, synthetic, test_properties

# ---------------------------------------------------------------------------
# Paths, derived rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SAVE_PACKAGE = REPO_ROOT / "clockspeed" / "save"
SAVE_TESTS = REPO_ROOT / "tests" / "save"

# This module's own path. The child pytest run below MUST exclude it or the gate
# re-runs itself forever. Derived from __file__ rather than from a literal
# filename, so a rename cannot leave the guard pointing at a path that no longer
# exists - which would look green right up to the moment the machine ran out of
# processes.
THIS_MODULE = Path(__file__).resolve()

_CHILD_TIMEOUT_SECONDS = 300


# ---------------------------------------------------------------------------
# The module set, pinned
# ---------------------------------------------------------------------------

# "No write-capable call site outside workdir.py" is a claim relative to a SET.
# Pinning the set makes this gate a stated contract rather than a description of
# whatever happened to be on disk when it ran.
#
# THE PACKAGE __init__.py IS ON THE LIST DELIBERATELY. CS-400 names six modules;
# the package initialiser is a seventh file that can hold a write just as easily
# as any of them, and a scan that skipped it would carry a hole exactly where
# nobody looks. Covering it is strictly stronger than the clause requires.
SAVE_SOURCES: Final[tuple[str, ...]] = (
    "__init__.py",
    "chunks.py",
    "header.py",
    "objects.py",
    "usmap.py",
    "workdir.py",
    "world.py",
)

#: The one module allowed to write, per ADR 0007 decision item 6.
WRITER_SOURCE: Final = "workdir.py"

#: Every source that must be provably write-free.
READ_ONLY_SOURCES: Final[tuple[str, ...]] = tuple(
    name for name in SAVE_SOURCES if name != WRITER_SOURCE
)


def _relative_python_sources(root: Path, *, exclude: Path | None = None) -> tuple[str, ...]:
    """List every Python source under a root, as posix paths relative to it.

    Args:
        root: Directory to walk.
        exclude: An absolute path to omit, or None.

    Returns:
        Sorted relative posix paths, bytecode caches skipped.
    """
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts and (exclude is None or path.resolve() != exclude)
        )
    )


def _dotted_name(relative: str) -> str:
    """Convert a path relative to the save package into its importable name.

    Args:
        relative: A posix path such as ``header.py``.

    Returns:
        The dotted module name. A package ``__init__.py`` maps to the package
        itself rather than to a submodule literally named ``__init__``, which
        would import the same file a SECOND time and register a module object
        nothing else in the process is using.
    """
    stem = relative.removesuffix(".py")
    if stem == "__init__":
        return "clockspeed.save"
    return "clockspeed.save." + stem.replace("/", ".")


SAVE_MODULES: Final[tuple[str, ...]] = tuple(_dotted_name(name) for name in SAVE_SOURCES)


def test_the_scanned_module_set_is_exactly_the_save_package() -> None:
    """The pinned file list matches what is on disk, in BOTH directions.

    Asserted EQUAL rather than merely non-empty. A gate that scans "whatever it
    finds" reports zero violations just as happily when it finds nothing, so a
    module added to the save package fails this test until someone adds it to
    the list - at which point every scan below starts covering it.
    """
    assert _relative_python_sources(SAVE_PACKAGE) == SAVE_SOURCES, (
        "clockspeed/save/ no longer matches SAVE_SOURCES; a module was added, renamed or "
        "removed and the phase 4 write scan is no longer covering what it claims to"
    )


def test_the_dotted_module_names_derive_from_the_pinned_file_set() -> None:
    """The package initialiser maps to the package, not to a submodule."""
    assert _dotted_name("__init__.py") == "clockspeed.save"
    assert _dotted_name("workdir.py") == "clockspeed.save.workdir"
    assert "clockspeed.save.__init__" not in SAVE_MODULES


def test_the_writer_is_on_the_scanned_set_and_is_the_only_exemption() -> None:
    """The one exempt file is a real member of the set, and there is exactly one.

    Without this, a typo in WRITER_SOURCE would exempt nothing and hide nothing
    - or, worse, a second entry could be added to the exemption without anybody
    noticing that the gate had been widened.
    """
    assert WRITER_SOURCE in SAVE_SOURCES
    assert len(READ_ONLY_SOURCES) == len(SAVE_SOURCES) - 1
    assert WRITER_SOURCE not in READ_ONLY_SOURCES


# ===========================================================================
# Clause 1 - A REAL WORLD PARSES.  PARTIAL - all pairs load; DEPTH: test_phase4_gate_depth
# ===========================================================================


def _real_save_or_skip() -> Path:
    """Return the newest save in the operator's library, or skip.

    ``workdir.latest_save`` resolves the account directory, so a failure inside
    it unwinds through a frame holding a path whose own NAME is the platform
    account id. Its docstring promises it never raises for an absent, empty or
    unresolvable directory - which is a promise about those three states and not
    about every state, and this module may not rest a privacy claim on another
    module's promise. The call is therefore contained here regardless.

    ``KeyboardInterrupt`` is deliberately still free to unwind, so a walk over a
    real library stays abortable; it renders nothing without ``--full-trace``.

    Returns:
        The save path. Never rendered into an assertion message - it sits under
        a home directory and carries both the account id and the world name.
    """
    try:
        source = workdir.latest_save()
    # `SystemExit` is named beside `Exception` because it is a `BaseException`
    # and `except Exception` does not hold one. Nothing about the failure is
    # reported - not even a type name, because a frame that has to unwind to
    # produce one is exactly what this contains.
    except (Exception, SystemExit):
        source = None
    if source is None:
        pytest.skip("no save library on this machine - clause 1 is not gradeable here")
    return source


def _newest_real_saves_of_a_measured_pair_or_skip() -> tuple[Path, ...]:
    """Return the newest real saves whose BODY LAYOUT this project has measured.

    NEWEST FIRST, TIES BY NAME, AND ALL OF THEM - the ranking
    ``workdir.ranked_saves`` hands the companion, restricted
    to measured pairs. It used to return the single newest one, and the newest
    file in the operator's library became a save re-encoded by a third-party
    tool, which the object reader refuses correctly. Clause 1 then graded a
    file the game never wrote. The caller walks these through
    ``world.load_newest_world``, exactly as the companion does, so the clause
    grades the world the product would actually read - and still fails when
    every save it may fall back to is refused.

    ``latest_save`` alone is not enough and using it here would be a bug rather
    than a simplification: it returns the newest file, and on a library whose
    newest file is an UNMEASURED pair that save is refused by design. The test
    would then fail while the reader was behaving exactly as specified.

    THE DISCOVERY IS IMPORTED, NOT TRANSCRIBED. Both locators and the glob used
    to sit here outside every ``try``; forcing the glob to raise rendered the
    account directory itself under ``-q`` alone.
    ``test_properties._library_save_paths`` already contains exactly this
    sequence and is graded where it lives, so a third transcription of it would
    be a third place to get it subtly wrong.

    THE PER-SAVE CATCH NOW HAS A BACKSTOP. ``except (HeaderError, OSError)``
    names the two failures somebody predicted; ``header.read_header(path)``
    takes the save path as its ARGUMENT, so every other type rendered an
    absolute path under a home directory on the way out.

    Returns:
        The save paths. NEVER rendered into an assertion message - each sits
        under a home directory and carries both the account id and the world
        name.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        pytest.skip("no save library on this machine - clause 1 is not gradeable here")
    candidates: list[tuple[int, str, Path]] = []
    for path in saves:
        try:
            parsed = header.read_header(path)
        except (header.HeaderError, OSError):
            # The two EXPECTED failures - an unreadable file and a save of a
            # version this project does not parse - stay silent skips, because
            # the library legitimately holds both.
            continue
        # THE BACKSTOP, and `SystemExit` is named because it is not an
        # `Exception`. Nothing about the failure is reported - not even a type
        # name - because this helper returns a path or skips and has nowhere to
        # put one.
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
        # `path.stat()` gets its own containment: a save that vanishes between
        # the glob and the stat fails with the path in the frame.
        try:
            if (parsed.header_version, parsed.save_version) in objects.MEASURED_BODY_LAYOUTS:
                candidates.append((-path.stat().st_mtime_ns, path.name, path))
        except (Exception, SystemExit):  # noqa: S112 - reporting it IS the leak
            continue
    if not candidates:
        pytest.skip(
            "no save of a MEASURED body-layout pair on this machine, so clause 1 is not "
            "gradeable here"
        )
    ranked = sorted(candidates, key=lambda entry: (entry[0], entry[1]))
    return tuple(entry[2] for entry in ranked)


@dataclass(frozen=True)
class _MeasuredPairScalars:
    """What loading one real save of a measured pair yielded - SCALARS ONLY.

    No field can hold a path, a blob, a token or a decoded string, which is what
    makes this type safe to return across the containment boundary and safe for
    pytest to render.

    Attributes:
        record_count: Records in the parsed table, or 0 on failure.
        token_length: The world token's LENGTH - never the token.
        level_count: Levels in the body, or 0 on failure.
        header_version: The declared header version, or 0 on failure.
        failure: The contained failure's type NAME, or None on success.
    """

    record_count: int
    token_length: int
    level_count: int
    header_version: int
    failure: str | None


def _measured_pair_scalars_or_skip() -> _MeasuredPairScalars:
    """Load the newest loadable real save of a measured pair and reduce it to scalars.

    THROUGH ``world.load_newest_world``, the companion's own walk: a newer save
    the reader refuses is skipped and flagged rather than graded as the world.
    ``load`` is passed as ``world.load_world`` looked up at CALL time, so a
    grader that patches the module attribute reaches the walk.

    ``world.load_world(source)`` takes the save path as its ARGUMENT, and the
    catch around it named ``world.WorldLoadError`` alone - the narrowest of the
    three catches in this module and the widest gap. Any type outside that one
    family rendered an absolute path under a home directory the moment pytest
    unwound the call, and a forced ``MemoryError`` through the reader was
    measured rendering all six probed markers.

    The model is bound HERE and nowhere else and never crosses back to a caller,
    so no frame holding a real world can unwind out of this function.

    Returns:
        The scalars. Never a path, a token or a decoded string.
    """
    sources = _newest_real_saves_of_a_measured_pair_or_skip()
    try:
        model = world.load_newest_world(sources, load=world.load_world)
        if model is None:
            raise LookupError
        return _MeasuredPairScalars(
            record_count=len(model.objects.records),
            token_length=len(model.token),
            level_count=model.objects.level_count,
            header_version=model.header.header_version,
            failure=None,
        )
    # BROAD BY DESIGN, `SystemExit` named because it is not an `Exception`.
    except (Exception, SystemExit) as exc:
        return _MeasuredPairScalars(
            record_count=0,
            token_length=0,
            level_count=0,
            header_version=0,
            failure=type(exc).__name__,
        )


def test_a_real_world_parses_end_to_end() -> None:
    """CLAUSE 1 - MET for a measured body-layout pair.

    This was skipped when the gate was written, because nothing could locate a
    real body's object table. CS-407 derived the levelled layout and CS-409
    routed ``load_world`` to it, so the assertion is real.

    READ THE LIMIT BEFORE CITING THIS AS CS-400 CLOSED. It has MOVED, not gone:
    all four real pairs now parse, but what is measured is the body SKELETON,
    and roughly three quarters of every real body is opaque property payload
    the walk steps over by declared length. Passing here means the seam works
    end to end - not that the reader understands a save.

    COUNTS ONLY. Every subject is reduced to a scalar inside
    :func:`_measured_pair_scalars_or_skip` before it crosses back here, so this
    frame holds no token, no map name, no instance name, no path and no save
    bytes - there is nothing here for a failing assertion to render.
    """
    found = _measured_pair_scalars_or_skip()

    assert found.failure is None, f"a real save of a measured pair did not load: {found.failure}"
    assert found.record_count > 0, "a real world parsed to an empty record table"
    assert found.token_length == header.WORLD_TOKEN_LENGTH
    assert found.header_version in header.SUPPORTED_HEADER_VERSIONS
    assert found.level_count > 1, "a real body carries a list of levels, not a single table"


def _load_every_real_save() -> tuple[int, int, tuple[str, ...]] | None:
    """Load every real save through the ONE entry point and return COUNTS ONLY.

    NOTHING RAISES WITH A PATH OR BYTES IN FLIGHT. pytest renders the ARGUMENTS
    of every frame in a failing traceback, and here the argument is a PATH that
    sits under a home directory and carries both the account id and the world
    name - so the containment matters even before the body is read. Every
    failure is reduced to an exception type name inside this helper, and the
    broad catch is what makes that total rather than nearly total.

    THE DISCOVERY IS IMPORTED, NOT TRANSCRIBED. Both locators and the glob used
    to sit above the loop outside every ``try``, and forcing the glob to raise
    rendered the account directory itself under ``-q`` alone.
    ``test_properties._library_save_paths`` contains exactly that sequence and
    is graded where it lives.

    Returns:
        ``(saves found, saves loaded, failure type names)``, or None when no
        save library is reachable. Never returns a path or a decoded string.
    """
    saves = test_properties._library_save_paths()  # noqa: SLF001
    if not saves:
        return None

    found = loaded = 0
    failures: list[str] = []
    for path in saves:
        found += 1
        try:
            model = world.load_world(path)
        # BROAD BY DESIGN - see the docstring. The argument in flight is a PATH
        # carrying the account id and the world name, so no exception type may
        # reach a frame pytest would render. The type NAME is preserved.
        #
        # `SystemExit` IS NAMED BECAUSE IT IS NOT AN `Exception`, and that was
        # not a theoretical gap here: this catch read `except Exception` alone,
        # and a forced `SystemExit` escaped it and rendered all six probed
        # markers under `-q`. `KeyboardInterrupt` is deliberately left free to
        # unwind so a walk over a real library stays abortable.
        except (Exception, SystemExit) as exc:
            failures.append(type(exc).__name__)
            continue
        if model.objects.level_count > 1:
            loaded += 1
        else:
            failures.append("FlatLevelCount")
    return (found, loaded, tuple(sorted(set(failures))))


def test_every_real_save_in_the_library_loads_through_the_one_entry_point() -> None:
    """CLAUSE 1 AT LIBRARY SCALE - the assertion the previous wave could not make.

    ``test_a_real_world_parses_end_to_end`` above loads ONE save, deliberately
    chosen from a measured pair. That was the strongest claim available while
    three of the four pairs were underived, and it is weak in a specific way: a
    library where thirteen of fourteen files refuse would pass it.

    This sweeps every save in the library through ``load_world``. It is the
    difference between "the reader can read a save" and "the reader can read
    this operator's saves", and only the second is what CS-400 clause 1 asks.

    STILL NOT CS-400 CLOSED. Every byte of framing being consumed says nothing
    about the property payload that is three quarters of each file.

    Skip-if-absent and COUNTS ONLY.
    """
    swept = _load_every_real_save()
    if swept is None:
        pytest.skip("no save library on this machine - clause 1 is not gradeable here")
    found, loaded, failures = swept

    assert found > 0, "a save library was found but holds no .sav file"
    assert failures == (), f"{len(failures)} distinct failure kinds loading real saves: {failures}"
    assert loaded == found, f"only {loaded} of {found} real saves loaded end to end"


@dataclass(frozen=True)
class _BodyPartialScalars:
    """What the newest real save yielded as far as the chunk layer - SCALARS ONLY.

    Attributes:
        header_version: The declared header version, or 0 on failure.
        token_length: The world token's LENGTH - never the token.
        payload_length: Decompressed payload length, or 0 on failure.
        chunk_count: Chunks walked, or 0 on failure.
        failure: The contained failure's type NAME, or None on success.
    """

    header_version: int
    token_length: int
    payload_length: int
    chunk_count: int
    failure: str | None


def _body_partial_scalars_or_skip() -> _BodyPartialScalars:
    """Walk the newest real save to the chunk layer and reduce it to scalars.

    THE GUARD HERE CLOSES A LEAK MEASURED ON THIS MACHINE rather than reasoned
    about. pytest renders the ARGUMENTS of every frame in a failing traceback -
    no ``--showlocals`` needed, no opt-in. ``source.read_bytes()`` unwinds
    through a bound method whose ``self`` IS the save path, and passing real
    save bytes into a frame that can raise prints the HEAD of the file, which is
    precisely the PII-bearing header: the save name, the options string carrying
    platform, account id and player display name, and the session name, which is
    the operator's world name (non-negotiables 11 and 12).

    The catch used to name ``(HeaderError, ChunkError, OSError)`` - three
    predicted families - and a forced ``MemoryError`` walked straight out of it
    and rendered the account directory. The blob and the parsed header are bound
    HERE and nowhere else, so nothing holding either can unwind to a caller.

    Returns:
        The scalars. Never a path, a token or save bytes.
    """
    source = _real_save_or_skip()
    try:
        parsed = header.read_header(source)
        body = chunks.decompress_body(
            source.read_bytes(), parsed.body_offset, header_version=parsed.header_version
        )
        return _BodyPartialScalars(
            header_version=parsed.header_version,
            token_length=len(parsed.world_token),
            payload_length=len(body.payload),
            chunk_count=body.chunk_count,
            failure=None,
        )
    # BROAD BY DESIGN, `SystemExit` named because it is not an `Exception`.
    except (Exception, SystemExit) as exc:
        return _BodyPartialScalars(
            header_version=0,
            token_length=0,
            payload_length=0,
            chunk_count=0,
            failure=type(exc).__name__,
        )


def test_a_real_save_reaches_the_body_partial(tmp_path: Path) -> None:
    """CLAUSE 1, PARTIAL - and it is named a partial because that is what it is.

    Skip-if-absent and COUNTS ONLY. What this proves is the half of clause 1
    that does not depend on CS-407: the save is FOUND, the header PARSES, the
    declared version is one the reader supports, the world token is the measured
    width, and the chunk walk returns a non-empty payload over at least one
    chunk. The object walk is deliberately not attempted.

    This is NOT clause 1. Do not cite it as clause 1.

    The file is read through ``read_bytes`` rather than copied, so this test
    performs no write anywhere; ``tmp_path`` is bound only to keep the work root
    off the repo should any future edit introduce a copy.
    """
    assert tmp_path.exists()
    found = _body_partial_scalars_or_skip()

    assert found.failure is None, f"the newest real save did not reach a body: {found.failure}"
    assert found.header_version in header.SUPPORTED_HEADER_VERSIONS
    assert found.token_length == header.WORLD_TOKEN_LENGTH
    assert found.chunk_count >= 1
    assert found.payload_length > 0


# The FLAT fixtures that load through the one entry point. SAVE_V42 joined this
# tuple when CS-407 measured save version 42's transform delta at 4; it was
# absent while that delta was unmeasured, and the corpus still builds it with an
# EMPTY object section, so it exercises the header-13 prefix and nothing else.
LOADABLE_FIXTURES: Final = (
    synthetic.SAVE_V36,
    synthetic.SAVE_V42,
    synthetic.SAVE_V52,
    synthetic.SAVE_V60,
    synthetic.SAVE_CROSS,
)

#: A save version in no real file and in no measured table. The refusal below
#: needs one, and 42 stopped being one when its delta was measured.
UNMEASURED_SAVE_VERSION: Final = 97


def test_the_loadable_version_set_is_four_of_four() -> None:
    """RESTATED UNDER CS-407. Every save version in the real library now parses.

    This was ``..._is_three_of_four``, and it asserted that save version 42 was
    refused BY DESIGN because its transform delta had never been measured. That
    delta has now been measured at 4 - by a corroborator independent of the
    section arithmetic, since every actor rotation is a unit quaternion and
    17763 of 17763 give one at shift 4 - so the refusal is retired rather than
    loosened, and the version set is restated to what it actually is.

    THE GUARD THE OLD TEST CARRIED SURVIVES, pointed at a version nobody has
    measured. Its subject was never 42 in particular: it was that an absent key
    RAISES instead of defaulting to a plausible neighbour's value. Pointing it
    at a still-unmeasured version keeps that alive; deleting it would have
    thrown the rule away with the example.

    CS-402 SHIPPED (docs/LEDGER.md, 2026-08-15), and not on this evidence alone.
    Four of four save versions parsing is a statement about the SKELETON grammar;
    what a payload holds is graded by other arms, so a green run here is still
    not the reader understanding a save.
    """
    loadable = {fixture.save_version for fixture in LOADABLE_FIXTURES}
    assert loadable == {36, 42, 52, 60}, (
        "the loadable save-version set changed; CS-402's status must be re-stated"
    )
    assert UNMEASURED_SAVE_VERSION not in objects.TRANSFORM_DELTA_BY_SAVE_VERSION, (
        "the version chosen to stand for 'unmeasured' gained a delta; pick one that "
        "is still unmeasured rather than deleting the refusal this test pins"
    )
    with pytest.raises(objects.UnsupportedSaveVersionError):
        objects.transform_delta(UNMEASURED_SAVE_VERSION)


@pytest.mark.parametrize("fixture", LOADABLE_FIXTURES, ids=lambda save: save.name)
def test_every_loadable_fixture_parses_through_the_one_entry_point(
    fixture: synthetic.SyntheticSave,
) -> None:
    """The synthetic half of clause 1: the composition works end to end.

    This is the corpus, not a real world. It proves the seam - both version
    scalars threaded separately into a chunk walk and a record walk - and it
    proves nothing at all about the real body layout CS-407 governs.
    """
    model = world.load_world_from_bytes(fixture.blob, body_layout=world.BODY_LAYOUT_FLAT)

    assert len(model.token) == header.WORLD_TOKEN_LENGTH
    assert model.header.header_version == fixture.header_version
    assert model.header.save_version == fixture.save_version
    assert len(model.objects.records) == len(fixture.objects)


#: The header version that WAS unreachable end to end until CS-407 measured
#: save version 42's transform delta. Kept as a named constant rather than
#: deleted: the gap it marks is the one this gate now asserts is CLOSED, and a
#: closed gap that loses its name is a gap that can silently reopen.
HEADER_VERSION_GATED_BY_CS_408: Final = 13


def test_header_version_coverage_through_the_entry_point_is_three_of_three() -> None:
    """THE DESIGNED RED, FIRED AND RESTATED. It went red exactly as it was built to.

    This was ``..._is_two_of_three``, and it asserted that header 13 was
    UNREACHABLE through ``load_world``. Its own docstring recorded why it was
    written as an assertion rather than as a comment: so that CS-408 landing
    would make it RED and force the claim to be restated instead of quietly
    decaying into a false sentence. CS-407 measured save version 42's transform
    delta, SAVE_V42 became loadable, and the test went red on schedule.

    RESTATED, NOT LOOSENED. The old shape was:

        header 10  reachable (SAVE_V36)
        header 13  UNREACHABLE - its only fixture is SAVE_V42, refused at the
                   object stage because save 42's delta was unmeasured
        header 14  reachable (SAVE_V52, SAVE_V60, SAVE_CROSS)

    and the new one is that all three are reachable, asserted as an EQUALITY
    against the supported set so it cannot pass by a fixture disappearing.

    READ WHAT HEADER 13's COVERAGE ACTUALLY IS. SAVE_V42 carries an EMPTY object
    section, so through the flat reader it exercises the wide int64 prefix and
    zero records. The coverage that carries records is the LEVELLED fixture for
    the same pair, which is why both tuples are unioned below rather than only
    the flat one - a reachability claim resting on an empty body would be thin
    enough to mislead.
    """
    reachable = {
        fixture.header_version for fixture in (*LOADABLE_FIXTURES, *synthetic.LEVELLED_SAVES)
    }
    supported = set(header.SUPPORTED_HEADER_VERSIONS)

    assert reachable == supported, (
        "the set of header versions reachable through load_world changed; CS-402's status "
        "and this gate's module docstring must be restated together"
    )
    assert HEADER_VERSION_GATED_BY_CS_408 in supported, (
        "header 13 is no longer a supported version, which is a bigger change than this "
        "test is about"
    )

    with_records = [
        fixture.name
        for fixture in synthetic.LEVELLED_SAVES
        if fixture.header_version == HEADER_VERSION_GATED_BY_CS_408 and fixture.objects
    ]
    assert with_records == ["SAVE_LEVELLED_V42"], (
        "header 13's end-to-end coverage no longer includes a fixture carrying records. "
        "Without one the claim collapses back to a prefix-width check on an empty body"
    )


def test_the_body_prefix_width_dispatch_is_still_exercised_on_both_widths() -> None:
    """The gap above does NOT leave the prefix-width dispatch untested. Proven, not assumed.

    Header 10 takes the NARROW int32 prefix and headers 13 and 14 take the WIDE
    int64 one, so losing header 13 from the reachable set costs nothing here -
    header 14 exercises the same branch. Asserted directly so the previous test's
    gap is not read as wider than it is.
    """
    reachable = {fixture.header_version for fixture in LOADABLE_FIXTURES}
    widths = {objects.body_prefix_width(version) for version in reachable}

    assert widths == {objects.BODY_PREFIX_WIDTH_NARROW, objects.BODY_PREFIX_WIDTH_WIDE}, (
        "the reachable fixtures no longer cover both body-prefix widths"
    )
    assert objects.body_prefix_width(HEADER_VERSION_GATED_BY_CS_408) == (
        objects.BODY_PREFIX_WIDTH_WIDE
    ), "header 13 no longer shares header 14's prefix width, so the gap above is now wider"


# ===========================================================================
# Clause 2 - A CORRUPTED SAVE PRODUCES A CLEAN ERROR.  MET.
# ===========================================================================
#
# "Clean" means a WorldLoadError out of load_world_from_bytes and nothing else.
# The forbidden outcomes are named rather than implied: a bare struct.error, a
# zlib.error, an IndexError, a MemoryError, or any unhandled exception at all.
# A parse that SUCCEEDS on a corrupted blob is equally a failure, and is checked
# separately - a reader that silently accepted damaged bytes would produce
# confident wrong advice, which is worse than a crash.


@dataclass(frozen=True)
class CorruptionCase:
    """One named corruption, with the stage the reader is measured to refuse it at.

    Attributes:
        label: The corpus helper's own name.
        blob: The damaged bytes.
        stage: The ``world.STAGES`` entry the refusal is measured to come from.
    """

    label: str
    blob: bytes
    stage: str


def _corruption_cases() -> tuple[CorruptionCase, ...]:
    """Build every corruption the corpus publishes.

    EVERY published helper is used. A gate that exercised four of the eight
    would report a clean sweep of half the surface, and the half left out is
    where the next defect lives.

    Returns:
        The cases, with the measured refusal stage for each.
    """
    subject = synthetic.SAVE_V60
    return (
        CorruptionCase("corrupt_magic", synthetic.corrupt_magic(subject), world.STAGE_CHUNKS),
        CorruptionCase("corrupt_marker", synthetic.corrupt_marker(subject), world.STAGE_CHUNKS),
        CorruptionCase(
            "corrupt_size_disagreement",
            synthetic.corrupt_size_disagreement(subject),
            world.STAGE_CHUNKS,
        ),
        CorruptionCase(
            "corrupt_zlib_stream", synthetic.corrupt_zlib_stream(subject), world.STAGE_CHUNKS
        ),
        CorruptionCase(
            "absurd_string_length", synthetic.absurd_string_length(), world.STAGE_HEADER
        ),
        CorruptionCase(
            "negative_string_length", synthetic.negative_string_length(), world.STAGE_HEADER
        ),
        CorruptionCase(
            "declared_chunk_bomb", synthetic.declared_chunk_bomb(subject), world.STAGE_CHUNKS
        ),
        CorruptionCase(
            "unsupported_header_version",
            synthetic.unsupported_header_version(),
            world.STAGE_HEADER,
        ),
    )


CORRUPTION_CASES: Final = _corruption_cases()


def _outcome_of(blob: bytes) -> BaseException | None:
    """Load a blob and return what came back out, without judging it.

    ``pytest.raises`` is the wrong instrument for clauses 2 and 3 and this
    helper is why. ``pytest.raises(WorldLoadError)`` conflates two very
    different failures into one red - a raw ``zlib.error`` escaping, and the
    reader ACCEPTING damaged bytes - and says nothing at all about the second
    when it passes. Separating the three outcomes needs the exception as a
    VALUE, so the caller can name each one in its own message.

    ``BaseException`` rather than ``Exception``, deliberately: a
    ``MemoryError`` from a reader that believed a declared size is exactly the
    outcome the chunk-bomb case exists to forbid, and it is not an
    ``Exception`` subclass in every case a caller cares about. Nothing is
    re-raised and nothing is suppressed - the object is handed straight back.

    Args:
        blob: The save bytes to attempt.

    Returns:
        The exception the load raised, or None when it parsed cleanly.
    """
    try:
        world.load_world_from_bytes(blob, body_layout=world.BODY_LAYOUT_FLAT)
    except BaseException as exc:
        return exc
    return None


#: The corpus helpers this gate is required to exercise. Asserted against the
#: cases actually built, so a helper added to the corpus and forgotten here
#: fails the gate rather than silently going untested.
REQUIRED_CORRUPTION_HELPERS: Final = frozenset(
    {
        "absurd_string_length",
        "corrupt_magic",
        "corrupt_marker",
        "corrupt_size_disagreement",
        "corrupt_zlib_stream",
        "declared_chunk_bomb",
        "negative_string_length",
        "unsupported_header_version",
    }
)


def test_every_published_corruption_helper_is_exercised() -> None:
    """The case list covers every corruption helper the corpus publishes.

    Both directions. A helper missing from the cases means the gate is narrower
    than it claims; a case naming a helper the corpus no longer has means the
    list has rotted.
    """
    exercised = {case.label for case in CORRUPTION_CASES}
    assert exercised == REQUIRED_CORRUPTION_HELPERS

    published = {
        name
        for name in dir(synthetic)
        if name.startswith(("corrupt_", "absurd_", "negative_", "declared_", "unsupported_"))
        and callable(getattr(synthetic, name))
    }
    assert published == REQUIRED_CORRUPTION_HELPERS, (
        "the corpus's corruption surface moved; this gate is no longer exercising all of it"
    )


@pytest.mark.parametrize("case", CORRUPTION_CASES, ids=lambda case: case.label)
def test_a_corrupted_save_produces_a_clean_error(case: CorruptionCase) -> None:
    """CLAUSE 2. A named WorldLoadError, never a crash and never a silent accept.

    ``pytest.raises`` on ``WorldLoadError`` alone would be too weak: it says
    nothing about the case where the reader ACCEPTS damaged bytes. So the call
    is made bare and the three outcomes are separated explicitly - refused
    cleanly, refused by leaking a lower-level exception, or accepted.
    """
    caught = _outcome_of(case.blob)

    if caught is None:
        pytest.fail(
            f"{case.label} PARSED CLEANLY. Accepting damaged bytes is worse than refusing "
            "them: it produces confident wrong advice instead of an error"
        )
    if not isinstance(caught, world.WorldLoadError):
        pytest.fail(
            f"{case.label} escaped as {type(caught).__name__} rather than a WorldLoadError; "
            "a corrupted save must never surface a raw parser or runtime error"
        )
    assert caught.stage in world.STAGES
    assert caught.cause_type, "the refusal named no cause type"


@pytest.mark.parametrize("case", CORRUPTION_CASES, ids=lambda case: case.label)
def test_a_corrupted_save_is_refused_at_the_measured_stage(case: CorruptionCase) -> None:
    """The refusal comes from the layer that should have noticed, not by luck.

    Stage is pinned per case because "it raised something" is a much weaker
    claim than "the chunk layer rejected a bad magic". A refusal that drifted to
    a different stage would still be a clean error and would still mean the
    layer that owns the check had stopped performing it.
    """
    with pytest.raises(world.WorldLoadError) as caught:
        world.load_world_from_bytes(case.blob, body_layout=world.BODY_LAYOUT_FLAT)

    assert caught.value.stage == case.stage


@pytest.mark.parametrize("case", CORRUPTION_CASES, ids=lambda case: case.label)
def test_the_corruption_helpers_really_damage_the_blob(case: CorruptionCase) -> None:
    """Non-vacuous: each damaged blob actually differs from a fixture that loads.

    A helper that silently returned the pristine bytes would make every
    assertion above a test of the happy path wearing a corruption label.
    """
    assert case.blob != synthetic.SAVE_V60.blob or case.label in {
        "absurd_string_length",
        "negative_string_length",
        "unsupported_header_version",
    }
    assert len(case.blob) > 0


@pytest.mark.parametrize("fixture", list(LOADABLE_FIXTURES), ids=lambda save: save.name)
def test_corruption_is_refused_on_every_framing_and_every_version(
    fixture: synthetic.SyntheticSave,
) -> None:
    """The clause holds across BOTH chunk framings, not just the newest one.

    Header version 10 frames a chunk with a zero marker and NO compression
    algorithm byte, which shifts the zlib stream by one. A corruption gate run
    only against header 14 would leave the older framing - a majority of the
    operator's own library - ungraded.
    """
    for damage in (
        synthetic.corrupt_magic,
        synthetic.corrupt_marker,
        synthetic.corrupt_size_disagreement,
        synthetic.corrupt_zlib_stream,
        synthetic.declared_chunk_bomb,
    ):
        with pytest.raises(world.WorldLoadError):
            world.load_world_from_bytes(damage(fixture), body_layout=world.BODY_LAYOUT_FLAT)


def test_a_declared_chunk_bomb_is_refused_without_allocating_it() -> None:
    """A terabyte declared by a chunk carrying a few hundred bytes is refused on the DECLARATION.

    The failure mode this forbids is a reader that believes the declared size
    and preallocates: that is a MemoryError or a hung machine rather than an
    error message. The refusal must therefore be a budget rejection, not an
    allocation that happened to fail.
    """
    blob = synthetic.declared_chunk_bomb(synthetic.SAVE_V60)
    parsed = header.parse_header(blob)

    with pytest.raises(chunks.ChunkBudgetExceededError):
        chunks.decompress_body(blob, parsed.body_offset, header_version=parsed.header_version)

    assert synthetic.CHUNK_BOMB_UNCOMPRESSED_SIZE > chunks.MAX_TOTAL_BODY_BYTES, (
        "the bomb fixture no longer exceeds the reader's ceiling, so the refusal above "
        "proves nothing about the budget"
    )


# ===========================================================================
# Clause 3 - A TRUNCATED SAVE PRODUCES A CLEAN ERROR.  MET.
# ===========================================================================
#
# THE SUBTLETY THIS SECTION REFUSES TO PAPER OVER.
# ``synthetic.save_with_truncated_body`` rewrites the length prefix and
# RECOMPRESSES, so the damage is invisible to the chunk layer BY CONSTRUCTION.
# The corpus says so deliberately: the point of a body-scope cut is to be
# reachable only after a successful inflate, or it is testing the framing again
# instead of the record walk.
#
# So the honest assertion is not "every truncation point fails the same way".
# Measured on this tree, all six points DO raise a WorldLoadError, but they do
# not raise at the same stage and the difference is the whole content of the
# claim:
#
#   file-scope cuts     -> refused at the HEADER or the CHUNK stage
#   the body-scope cut  -> sails cleanly through BOTH and is refused at the
#                          OBJECT stage
#
# ``test_the_body_scope_truncation_is_invisible_to_the_chunk_layer`` asserts
# that invisibility directly rather than leaving it as a comment, because it is
# the property that makes the body-scope point worth having at all.


@dataclass(frozen=True)
class TruncationCase:
    """One truncation point, with the stage it is measured to be refused at."""

    label: str
    scope: str
    blob: bytes
    stage: str


#: The stage each pinned cut point is MEASURED to be refused at. Written down
#: rather than derived so a drift in which layer notices is red rather than
#: absorbed. Keyed by the corpus's own label.
_TRUNCATION_STAGE: Final[dict[str, str]] = {
    "mid-length-prefix": world.STAGE_HEADER,
    "mid-string-bytes": world.STAGE_HEADER,
    "mid-magic": world.STAGE_HEADER,
    "mid-chunk-header": world.STAGE_CHUNKS,
    "mid-zlib-stream": world.STAGE_CHUNKS,
    "one-byte-short-of-an-object-record": world.STAGE_OBJECTS,
}


def _truncation_blob(point: synthetic.TruncationPoint) -> bytes:
    """Build the truncated blob for one cut point, honouring its scope.

    Args:
        point: The corpus's cut point.

    Returns:
        The truncated save bytes.

    Raises:
        AssertionError: The point declares a scope the corpus does not publish.
    """
    if point.scope == synthetic.SCOPE_FILE:
        return synthetic.truncated_at(synthetic.SAVE_V60.blob, point.offset)
    assert point.scope == synthetic.SCOPE_BODY, f"unknown truncation scope: {point.scope}"
    return synthetic.save_with_truncated_body(synthetic.SAVE_V60, point.offset)


TRUNCATION_CASES: Final = tuple(
    TruncationCase(
        label=point.label,
        scope=point.scope,
        blob=_truncation_blob(point),
        stage=_TRUNCATION_STAGE[point.label],
    )
    for point in synthetic.TRUNCATION_BOUNDARIES
)


def test_every_pinned_truncation_boundary_is_exercised() -> None:
    """Every point the corpus pins is covered, and both scopes are represented.

    A truncation gate that happened to cover only file-scope cuts would never
    reach the record walk at all, which is the layer the body-scope point exists
    to exercise.
    """
    assert len(TRUNCATION_CASES) == len(synthetic.TRUNCATION_BOUNDARIES)
    assert {case.label for case in TRUNCATION_CASES} == set(_TRUNCATION_STAGE)

    scopes = {case.scope for case in TRUNCATION_CASES}
    assert scopes == {synthetic.SCOPE_FILE, synthetic.SCOPE_BODY}, (
        "both truncation scopes must be present; file scope alone never reaches the walk"
    )


@pytest.mark.parametrize("case", TRUNCATION_CASES, ids=lambda case: case.label)
def test_a_truncated_save_produces_a_clean_error(case: TruncationCase) -> None:
    """CLAUSE 3. Measured on this tree: all six points raise, none crashes.

    Stated as a measurement rather than as a design guarantee, because it is
    one. The three outcomes are separated the same way clause 2 separates them,
    so a truncation that started PARSING would be red rather than green.
    """
    caught = _outcome_of(case.blob)

    if caught is None:
        pytest.fail(
            f"truncation {case.label} PARSED CLEANLY, so the reader accepted a file that "
            "ends mid-structure and will report a world it never finished reading"
        )
    if not isinstance(caught, world.WorldLoadError):
        pytest.fail(
            f"truncation {case.label} escaped as {type(caught).__name__} rather than a "
            "WorldLoadError; a short file must never surface a raw parser error"
        )
    assert caught.stage in world.STAGES


@pytest.mark.parametrize("case", TRUNCATION_CASES, ids=lambda case: case.label)
def test_a_truncated_save_is_refused_at_the_measured_stage(case: TruncationCase) -> None:
    """WHICH layer notices, per point. This is where the scopes stop agreeing.

    File-scope cuts are refused at the header or the chunk stage. The body-scope
    cut is refused at the OBJECT stage, because the corpus rebuilt a
    well-formed file around a short body on purpose.
    """
    with pytest.raises(world.WorldLoadError) as caught:
        world.load_world_from_bytes(case.blob, body_layout=world.BODY_LAYOUT_FLAT)

    assert caught.value.stage == case.stage


def test_the_body_scope_truncation_is_invisible_to_the_chunk_layer() -> None:
    """The measured subtlety, asserted rather than described.

    ``save_with_truncated_body`` rewrites the length prefix and recompresses, so
    the header parse and the whole chunk walk SUCCEED on it. Proving that
    directly is what makes the object-stage refusal above meaningful: without
    it, the body-scope point could be being caught by the framing checks and
    nobody would know the record walk had never been reached.
    """
    point = next(
        item for item in synthetic.TRUNCATION_BOUNDARIES if item.scope == synthetic.SCOPE_BODY
    )
    blob = synthetic.save_with_truncated_body(synthetic.SAVE_V60, point.offset)

    parsed = header.parse_header(blob)
    body = chunks.decompress_body(blob, parsed.body_offset, header_version=parsed.header_version)

    assert len(body.payload) > 0, "the chunk layer produced nothing, so it did NOT accept the file"
    assert body.chunk_count >= 1

    with pytest.raises(objects.ObjectTruncatedError):
        objects.parse_object_headers(
            body.payload,
            save_version=parsed.save_version,
            header_version=parsed.header_version,
            known_classes=None,
        )


@pytest.mark.parametrize("case", TRUNCATION_CASES, ids=lambda case: case.label)
def test_the_truncation_points_really_truncate(case: TruncationCase) -> None:
    """Non-vacuous - and the two scopes need DIFFERENT evidence, which is the point.

    A file-scope cut simply drops the tail, so the blob gets shorter. A
    body-scope cut does NOT: it rewrites the length prefix and RECOMPRESSES,
    and zlib is under no obligation to emit fewer bytes for one byte less
    input. Measured here: the intact SAVE_V60 blob and its body-truncated
    rebuild are the SAME LENGTH while differing in content, and the declared
    body length drops by one.

    Asserting "shorter" for both scopes would therefore be a false claim that
    happens to be checkable - which is worse than no check, because it fails
    for a reason that has nothing to do with truncation.
    """
    assert len(case.blob) > 0

    if case.scope == synthetic.SCOPE_FILE:
        assert len(case.blob) < len(synthetic.SAVE_V60.blob), (
            f"{case.label} is a file-scope cut and must produce a shorter blob"
        )
        return

    assert case.blob != synthetic.SAVE_V60.blob, (
        f"{case.label} is a body-scope cut and produced the intact fixture unchanged"
    )
    point = next(item for item in synthetic.TRUNCATION_BOUNDARIES if item.label == case.label)
    assert point.offset < len(synthetic.SAVE_V60.body), (
        "the body-scope cut point is not inside the body, so nothing was truncated"
    )


def test_truncating_a_save_to_nothing_is_also_refused() -> None:
    """The degenerate cut the pinned list does not carry.

    Zero bytes and one byte are the two inputs a reader is likeliest to meet in
    the wild - a save caught mid-write, or a zero-length file left by a failed
    copy - and neither is a pinned boundary, so both are asserted here.
    """
    for length in (0, 1):
        with pytest.raises(world.WorldLoadError) as caught:
            world.load_world_from_bytes(
                synthetic.SAVE_V60.blob[:length], body_layout=world.BODY_LAYOUT_FLAT
            )
        assert caught.value.stage == world.STAGE_HEADER


# ===========================================================================
# Clause 4 - THE SAVE DIRECTORY IS NEVER OPENED FOR WRITE.  MET.
# Signal 1 of 3: a runtime audit hook, in a child process.
# ===========================================================================

# The events worth watching. ``os.open`` is on the list even though it is
# MEASURED not to fire - CPython routes it through the ``open`` event with a
# None mode - because a future interpreter that started emitting it must be
# recorded rather than missed, and listing it costs nothing.
#: The pretend account directory's name. A WORD, never a digit run - see
#: :func:`_pretend_save_root` for why the obvious all-zeros stand-in is worse.
PRETEND_ACCOUNT_DIR_NAME: Final = "pretend-account"

_WATCHED_EVENTS: Final[tuple[str, ...]] = (
    "open",
    "os.open",
    "os.rename",
    "os.remove",
    "os.mkdir",
    "os.rmdir",
    "os.truncate",
    "os.link",
    "os.symlink",
    "shutil.copyfile",
    "shutil.copymode",
    "shutil.copystat",
    "shutil.copytree",
    "shutil.move",
    "shutil.rmtree",
)

#: Every watched event that is inherently a mutation. ``open`` is NOT one of
#: them - it is the read path too - so it is judged on its mode and flags
#: instead, which is the whole reason both are recorded.
_MUTATING_EVENTS: Final = frozenset(_WATCHED_EVENTS) - {"open", "os.open"}

#: A mode character that means write intent. The ``open`` audit event
#: NORMALISES the mode, so "rb" arrives as "r" and "wb" as "w"; testing for
#: these single characters is what survives that normalisation.
_WRITE_MODE_CHARACTERS: Final = frozenset("wax+")

#: Flag bits that mean write intent. O_RDONLY is ZERO and therefore cannot be
#: tested for at all - only the presence of a write bit is observable, which is
#: why this is stated as a positive mask rather than as "not read-only".
_WRITE_FLAG_MASK: Final = (
    os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | getattr(os, "O_APPEND", 0)
)

# The child. It installs the hook FIRST, then puts the repo on sys.path, then
# imports the save layer - in that order, because an audit hook cannot be
# uninstalled and must be in place before the import it is auditing.
#
# It records a COUNT of matching path arguments and never a path: the pretend
# root resolves through an 8.3 short name into a path carrying the Windows
# account name, and a recorder that logged it would print personal data into CI
# output (non-negotiables 3 and 12).
_AUDIT_CHILD: Final = '''
"""Signal 1 child. argv: <roots joined by |> <save path> <repo root> <action>."""

import json
import os
import sys

WATCHED = frozenset(%(watched)r)
ROOTS = tuple(os.path.normcase(part) for part in sys.argv[1].split("|") if part)
RECORDS = []


def _candidate_paths(args):
    found = []
    for item in args:
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, bytes):
            found.append(item.decode("utf-8", "replace"))
        elif hasattr(item, "__fspath__"):
            try:
                found.append(os.fspath(item))
            except (TypeError, ValueError):
                pass
    return found


def _under_root(text):
    try:
        candidate = os.path.normcase(os.path.abspath(text))
    except (OSError, ValueError):
        return False
    return any(candidate == root or candidate.startswith(root + os.sep) for root in ROOTS)


def _hook(event, args):
    # A RECORDING spy, never a raising one. This layer is deliberately
    # fail-soft, so an exception raised here would be swallowed by the code
    # under test and the whole signal would go green having proven nothing.
    try:
        if event not in WATCHED:
            return
        hits = [path for path in _candidate_paths(args) if _under_root(path)]
        if not hits:
            return
        mode = args[1] if event == "open" and len(args) > 1 else None
        flags = args[2] if event == "open" and len(args) > 2 else None
        RECORDS.append(
            {
                "event": event,
                "hits": len(hits),
                "mode": mode if isinstance(mode, str) else None,
                "flags": flags if isinstance(flags, int) else None,
            }
        )
    except BaseException:
        pass


sys.addaudithook(_hook)

sys.path.insert(0, sys.argv[3])
from clockspeed.save.world import BODY_LAYOUT_FLAT, load_world

ACTION = sys.argv[4]
ROOT = sys.argv[1].split("|")[0]

model = load_world(sys.argv[2], body_layout=BODY_LAYOUT_FLAT)

# The companion actions. Each plants ONE deliberate write under the pretend
# save root so the recorder can be proven able to catch it.
if ACTION == "plant-mode":
    with open(os.path.join(ROOT, "planted-mode.tmp"), "wb") as handle:
        handle.write(b"planted")
elif ACTION == "plant-flags":
    # The case a mode-string scan CANNOT see: os.open reports mode None and
    # carries its intent in the integer flags alone.
    descriptor = os.open(os.path.join(ROOT, "planted-flags.tmp"), os.O_WRONLY | os.O_CREAT)
    os.close(descriptor)
elif ACTION == "plant-remove":
    victim = os.path.join(ROOT, "planted-remove.tmp")
    with open(victim, "wb") as handle:
        handle.write(b"x")
    os.remove(victim)

print(json.dumps({"records": RECORDS, "objects": len(model.objects.records)}))
''' % {"watched": list(_WATCHED_EVENTS)}


@dataclass(frozen=True)
class AuditRun:
    """The outcome of one audited child run.

    Attributes:
        records: One entry per watched event that touched the pretend root.
        object_count: How many records the child's load produced.
    """

    records: tuple[dict[str, object], ...]
    object_count: int


def _has_write_intent(record: dict[str, object]) -> bool:
    """Whether one recorded open carries write intent, by mode OR by flags.

    BOTH channels are checked and neither is sufficient alone. A mode string is
    absent for ``os.open``, and the flags are absent for some call shapes, so a
    detector reading only one of the two has a hole exactly the size of the
    other.

    Args:
        record: One recorded event.

    Returns:
        True when the record shows an intent to write.
    """
    mode = record.get("mode")
    if isinstance(mode, str) and (_WRITE_MODE_CHARACTERS & set(mode)):
        return True
    flags = _recorded_flags(record)
    return flags is not None and bool(flags & _WRITE_FLAG_MASK)


def _recorded_flags(record: dict[str, object]) -> int | None:
    """Return the integer open flags a record carried, or None when it has none.

    The records arrive as decoded JSON, so every value is typed ``object`` and
    has to be narrowed before it can be masked. Narrowing in one helper rather
    than at each use keeps the two call sites - the write-intent judgement and
    the flag-channel companion - reading the same field the same way.

    Args:
        record: One recorded event.

    Returns:
        The flags, or None.
    """
    flags = record.get("flags")
    return flags if isinstance(flags, int) else None


def _read_open_count(run: AuditRun) -> int:
    """Count the read opens the child performed under the pretend save root.

    Args:
        run: The audited run.

    Returns:
        How many ``open`` events carried no write intent.
    """
    return sum(
        1
        for record in run.records
        if record.get("event") in {"open", "os.open"} and not _has_write_intent(record)
    )


def _pretend_save_root(tmp_path: Path) -> tuple[Path, Path]:
    """Lay out a pretend save root holding one synthetic save.

    SYNTHETIC BYTES ONLY. A real save is personal-data bearing and never goes
    into a fixture directory or a temporary tree a test controls.

    THE ACCOUNT DIRECTORY IS DELIBERATELY NOT DIGIT-SHAPED. A real one is a
    platform account id and is personal data, and the obvious stand-in - a long
    run of zeros - is a digit run that the account-id SHAPE detectors in
    ``tests/data/test_phase2_gate.py`` match on. Nothing needs the name to look
    numeric here, because ``CLOCKSPEED_ACCOUNT_DIR`` is set explicitly and the
    numeric glob in ``locate.resolve_account_dir`` is never reached. A word is
    therefore strictly safer than a shape, and costs nothing.

    Args:
        tmp_path: The per-test temporary directory.

    Returns:
        The pretend save root and the save inside it.
    """
    root = tmp_path / "pretend-save-root"
    account = root / PRETEND_ACCOUNT_DIR_NAME
    account.mkdir(parents=True)
    save = account / "SyntheticWorld_autosave_0.sav"
    save.write_bytes(synthetic.SAVE_V60.blob)
    return root, save


def _child_env(tmp_path: Path, root: Path) -> dict[str, str]:
    """Build the child environment: the pretend root, and no install anywhere.

    The work root is pointed OUTSIDE the pretend save root deliberately.
    ``workdir.copy_for_read`` refuses a destination inside the save root, so a
    work root nested in it would make the child fail on the refusal rather than
    on anything this signal is measuring.

    Args:
        tmp_path: The per-test temporary directory.
        root: The pretend save root.

    Returns:
        The environment mapping.
    """
    env = dict(os.environ)
    env[ENV_SAVE_ROOT] = str(root)
    env[ENV_ACCOUNT_DIR] = str(root / PRETEND_ACCOUNT_DIR_NAME)
    env[ENV_GAME_DIR] = str(tmp_path / "absent-install")
    env[ENV_LOCAL_CONFIG] = str(tmp_path / "absent.json")
    env[workdir.ENV_WORK_ROOT] = str(tmp_path / "work-root")
    # CONVENTIONS.md section 10: pin the child's text encoding so its output
    # decodes identically on every machine.
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run_audited_child(tmp_path: Path, action: str) -> AuditRun:
    """Run one audited load in a child interpreter and parse what it recorded.

    THE ROOT IS PASSED IN BOTH SPELLINGS. On Windows the temporary directory
    reaches the child through an 8.3 short name while every path the save layer
    resolves comes back expanded, so a child matching one spelling records
    NOTHING and every assertion built on it passes vacuously. That was observed
    directly while building this harness.

    Args:
        tmp_path: The per-test temporary directory.
        action: ``load`` for the real measurement, or a ``plant-*`` action for a
            companion that proves the recorder detects.

    Returns:
        The parsed run.
    """
    root, save = _pretend_save_root(tmp_path)
    script = tmp_path / "audited_child.py"
    script.write_text(_AUDIT_CHILD, encoding="utf-8")

    spellings = "|".join({str(root), str(root.resolve())})
    child = subprocess.run(
        [sys.executable, str(script), spellings, str(save), str(REPO_ROOT), action],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=_child_env(tmp_path, root),
        check=False,
    )

    # Bound to a local before asserting. Asserting on the CompletedProcess makes
    # pytest repr the whole object, and args[0] is the absolute interpreter path
    # - which on a default install sits under a home directory and carries the
    # account name into the log. The phase 2 gate records the same discipline.
    exit_code = child.returncode
    assert exit_code == 0, f"the audited child failed:\n{child.stdout}\n{child.stderr}"

    payload = json.loads(child.stdout.strip().splitlines()[-1])
    return AuditRun(records=tuple(payload["records"]), object_count=int(payload["objects"]))


def test_the_measured_audit_event_shapes_still_hold() -> None:
    """The three interpreter facts every assertion in this section rests on.

    Pinned so a CPython change makes this module RED rather than silently blind.
    If ``os.open`` ever stopped routing through the ``open`` event, or the mode
    stopped being normalised, the flag-based and mode-based checks below would
    keep passing while no longer detecting anything.
    """
    recorded: list[tuple[str, object, object]] = []

    # The audit event's argument positions, named rather than spelled as bare
    # integers: args[1] is the mode and args[2] is the flags, and a reader
    # meeting 1 and 2 has no way to know which is which.
    mode_index = 1
    flags_index = 2

    def _spy(event: str, args: tuple[object, ...]) -> None:
        if event in {"open", "os.open", "os.rename", "os.remove"}:
            recorded.append(
                (
                    event,
                    args[mode_index] if len(args) > mode_index else None,
                    args[flags_index] if len(args) > flags_index else None,
                )
            )

    sys.addaudithook(_spy)

    with tempfile.TemporaryDirectory() as name:
        scratch = Path(name)
        target = scratch / "probe.bin"
        with target.open("wb") as writer:
            writer.write(b"x")
        with target.open("rb") as reader:
            reader.read()
        descriptor = os.open(str(scratch / "flagged.bin"), os.O_WRONLY | os.O_CREAT)
        os.close(descriptor)
        (scratch / "flagged.bin").replace(scratch / "renamed.bin")
        (scratch / "renamed.bin").unlink()

    events = [entry[0] for entry in recorded]
    modes = [entry[1] for entry in recorded if entry[0] == "open"]

    assert "os.open" not in events, (
        "os.open now raises its own audit event; the recorder's mode/flag reasoning and "
        "the module docstring both need revisiting"
    )
    assert "w" in modes, "the open event no longer normalises 'wb' to 'w'"
    assert "r" in modes, "the open event no longer normalises 'rb' to 'r'"
    assert "os.rename" in events, "Path.replace no longer raises os.rename"
    assert "os.remove" in events, "Path.unlink no longer raises os.remove"

    flagged = [entry[2] for entry in recorded if entry[0] == "open" and entry[1] is None]
    assert any(isinstance(value, int) and value & _WRITE_FLAG_MASK for value in flagged), (
        "an os.open write no longer presents as a mode-less open carrying write flags, so "
        "the flag channel would no longer detect one"
    )


def test_no_event_under_the_pretend_save_root_carries_write_intent(tmp_path: Path) -> None:
    """CLAUSE 4, signal 1a. No open under the save root asks for write access.

    Judged on mode AND on flags together. The mode channel alone misses
    ``os.open`` entirely, which is the exact hole the roadmap recorded as
    measured this session.
    """
    run = _run_audited_child(tmp_path, "load")

    offenders = [record for record in run.records if _has_write_intent(record)]
    assert not offenders, (
        f"a load opened something under the save root with write intent: {offenders}"
    )


def test_no_mutating_event_names_the_pretend_save_root(tmp_path: Path) -> None:
    """CLAUSE 4, signal 1b. Nothing was renamed, removed, created or copied there.

    A separate assertion from the write-intent one because a rename or an unlink
    carries no mode and no flags at all: a check that looked only at open modes
    would watch a file be deleted and report a clean run.
    """
    run = _run_audited_child(tmp_path, "load")

    offenders = [record for record in run.records if record.get("event") in _MUTATING_EVENTS]
    assert not offenders, f"a mutating call named a path under the save root: {offenders}"


def test_the_audited_load_actually_read_the_save(tmp_path: Path) -> None:
    """CLAUSE 4, signal 1c. THE MANDATORY HALF, and the whole test without it.

    Both assertions above pass perfectly for a ``load_world`` that opened
    nothing, parsed nothing and returned nothing - which is exactly what the
    first working draft of this harness measured, because the pretend root was
    being matched in the wrong path spelling. A non-zero read count is what
    separates "proved no write happened" from "proved nothing happened".
    """
    run = _run_audited_child(tmp_path, "load")

    read_opens = _read_open_count(run)
    assert read_opens > 0, (
        "ZERO read opens were recorded under the pretend save root. The no-write "
        "assertions are therefore vacuous: nothing was measured. Either the load did not "
        "touch the save, or the recorder is matching the root in the wrong spelling"
    )
    assert run.object_count == len(synthetic.SAVE_V60.objects), (
        "the audited child did not actually parse the save it was pointed at"
    )


def test_the_audit_recorder_detects_a_mode_based_write(tmp_path: Path) -> None:
    """COMPANION for signal 1: the recorder catches a plain ``open(..., "wb")``.

    Without this the three assertions above are a claim about the harness rather
    than about the save layer - a recorder that recorded nothing would satisfy
    all of them.
    """
    run = _run_audited_child(tmp_path, "plant-mode")

    caught = [record for record in run.records if _has_write_intent(record)]
    assert caught, "the recorder missed a deliberate mode-based write under the save root"
    assert any(isinstance(record.get("mode"), str) for record in caught), (
        "the write was caught, but not through the mode channel this companion exercises"
    )


def test_the_audit_recorder_detects_a_flag_based_write(tmp_path: Path) -> None:
    """COMPANION for signal 1: the recorder catches ``os.open`` with WRITE FLAGS.

    THE SHARPEST OF THE THREE COMPANIONS. ``os.open`` reports its mode as None,
    so a recorder judging write intent by mode string alone sees a mode-less
    event and waves it through. This asserts the catch came through the FLAG
    channel specifically, so a regression to mode-only detection is red here
    rather than silently unprotected.
    """
    run = _run_audited_child(tmp_path, "plant-flags")

    caught = [record for record in run.records if _has_write_intent(record)]
    assert caught, "the recorder missed a deliberate flag-based os.open write"

    by_flags = [
        record
        for record in caught
        if record.get("mode") is None and (_recorded_flags(record) or 0) & _WRITE_FLAG_MASK
    ]
    assert by_flags, (
        "the flag-based write was not caught through the FLAG channel. A mode-only "
        "detector passes this exact construct, which is why the flag channel exists"
    )


def test_the_audit_recorder_detects_a_mutating_event(tmp_path: Path) -> None:
    """COMPANION for signal 1: the recorder catches a deliberate ``os.remove``.

    Proves the mutating-event half is live. A deletion carries no mode and no
    flags, so it is invisible to both channels the other two companions test.
    """
    run = _run_audited_child(tmp_path, "plant-remove")

    caught = [record for record in run.records if record.get("event") in _MUTATING_EVENTS]
    assert caught, "the recorder missed a deliberate os.remove under the save root"


# ===========================================================================
# Clause 4, signal 2 of 3: a filesystem fingerprint.
# ===========================================================================


def _fingerprint(root: Path) -> dict[str, tuple[str, int, int, int, str]]:
    """Fingerprint every entry under a directory, deeply.

    Six independent facts per entry - relative name, size, modification time in
    nanoseconds, creation time in nanoseconds, and the sha256 of the bytes -
    because any one of them alone is defeatable. A rewrite with identical
    content and a restored mtime changes nothing but the ctime; a rewrite of
    equal length changes only the hash.

    Args:
        root: The directory to fingerprint.

    Returns:
        Relative posix path -> (kind, size, mtime_ns, ctime_ns, sha256).
    """
    prints: dict[str, tuple[str, int, int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.stat()
        if path.is_dir():
            prints[relative] = ("dir", 0, info.st_mtime_ns, info.st_ctime_ns, "")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        prints[relative] = ("file", info.st_size, info.st_mtime_ns, info.st_ctime_ns, digest)
    return prints


def test_a_load_leaves_the_pretend_save_root_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLAUSE 4, signal 2. Nothing under the save root changed, by six measures.

    Independent of signal 1 rather than a restatement of it: this catches a
    write the audit hook cannot see - one performed by a C extension, by a
    mechanism that raises no audit event, or by any path the watch list does not
    enumerate. The two signals fail for different reasons, which is the only
    thing that makes having both worth the cost.

    The ENTRY SET is compared as well as the per-entry prints, so a NEW file
    left beside the save - a lock file, a sidecar, a stray copy - is caught even
    though it changes nothing about the save itself.
    """
    root, save = _pretend_save_root(tmp_path)
    monkeypatch.setenv(ENV_SAVE_ROOT, str(root))
    monkeypatch.setenv(ENV_ACCOUNT_DIR, str(save.parent))
    monkeypatch.setenv(ENV_GAME_DIR, str(tmp_path / "absent-install"))
    monkeypatch.setenv(ENV_LOCAL_CONFIG, str(tmp_path / "absent.json"))
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(tmp_path / "work-root"))

    before = _fingerprint(root)
    # The planted save is a SYNTHETIC one, and the corpus builds the flat body
    # layout. CS-409 made the LEVELLED reader the default, because that is what a
    # real save needs and the safe path must be the one a caller gets without
    # thinking. So this probe opts into flat explicitly - the clause under test is
    # "nothing under the save root was written", and which body reader ran does
    # not bear on it, but a refused load would make the assertion vacuous.
    model = world.load_world(save, body_layout=world.BODY_LAYOUT_FLAT)
    after = _fingerprint(root)

    assert model.objects.records, "the load produced nothing, so this proves nothing"
    assert set(before) == set(after), (
        f"the entry set under the save root changed: "
        f"added={sorted(set(after) - set(before))} removed={sorted(set(before) - set(after))}"
    )
    assert before == after, "a load modified something under the save root"


def test_the_fingerprint_detects_a_single_changed_byte(tmp_path: Path) -> None:
    """COMPANION for signal 2: the comparison FAILS when one byte moves.

    A fingerprint that compared equal no matter what would make the test above
    permanently green. One byte is the smallest change that must be caught, and
    the sha256 is the term that catches it - the size is unchanged by
    construction.
    """
    root, save = _pretend_save_root(tmp_path)

    before = _fingerprint(root)
    blob = bytearray(save.read_bytes())
    blob[-1] ^= 0xFF
    save.write_bytes(bytes(blob))
    after = _fingerprint(root)

    assert before != after, "the fingerprint did not notice a changed byte"
    assert set(before) == set(after), "the entry set should be unchanged by an in-place edit"

    changed = [name for name in before if before[name] != after[name]]
    assert changed, "no entry was reported as changed"
    assert before[changed[0]][4] != after[changed[0]][4], (
        "the sha256 term did not change, so the difference was noticed by an mtime alone - "
        "which a writer that restored the timestamp would defeat"
    )


def test_the_fingerprint_detects_a_new_file_beside_the_save(tmp_path: Path) -> None:
    """COMPANION for signal 2: an added entry is caught even with the save untouched.

    The failure this covers is a load that leaves a lock file or a sidecar
    behind. Every per-entry print would compare equal, so only the entry-set
    comparison can catch it.
    """
    root, save = _pretend_save_root(tmp_path)

    before = _fingerprint(root)
    (save.parent / "stray.lock").write_bytes(b"")
    after = _fingerprint(root)

    assert set(before) != set(after), "the fingerprint did not notice a new file"
    assert sorted(set(after) - set(before)) == [f"{PRETEND_ACCOUNT_DIR_NAME}/stray.lock"]


# ===========================================================================
# Clause 4, signal 3 of 3: a static AST gate over clockspeed/save/.
# ===========================================================================
#
# THE SCAN IS OVER THE AST AND NEVER OVER THE FILE TEXT. Every module in this
# package documents its own write discipline at length - workdir.py's docstring
# alone names "open", "mkdir", "rename" and "remove" in prose - so a text sweep
# flags its own documentation. A guard that fires on the documentation
# explaining the guard gets switched off within a week.
#
# WHAT THIS STATIC SCAN CANNOT SEE, stated plainly because a gate whose limits
# are not written down gets read as covering more than it does:
#   - a write reached through getattr or any other runtime name resolution;
#   - a write performed inside a C extension or a third-party call;
#   - a write in a module OUTSIDE clockspeed/save/ that the save layer calls.
# Signals 1 and 2 are what cover those, at runtime, which is why all three
# exist rather than whichever one was cheapest.

_WRITE_MODE_CHARACTERS_STATIC: Final = frozenset("wax+")

#: Call names that mutate the filesystem. Matched on the bare attribute name, so
#: ``os.remove``, ``shutil.rmtree`` and ``path.unlink`` all reduce to the name
#: the ban is stated at and no import spelling can dodge it.
_MUTATING_CALL_NAMES: Final = frozenset(
    {
        "chmod",
        "copy",
        "copy2",
        "copyfile",
        "copymode",
        "copystat",
        "copytree",
        "link",
        "makedirs",
        "mkdir",
        "mkdtemp",
        "mkstemp",
        "move",
        "remove",
        "removedirs",
        "rename",
        "renames",
        "replace",
        "rmdir",
        "rmtree",
        "symlink",
        "touch",
        "truncate",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
        "writelines",
    }
)

#: The ``os`` flag names that mean write intent, as they appear in source.
_WRITE_FLAG_NAMES: Final = ("O_APPEND", "O_CREAT", "O_RDWR", "O_TRUNC", "O_WRONLY")


@dataclass(frozen=True)
class WriteSite:
    """One write-capable call site found by the static scan.

    Attributes:
        line: 1-based line number.
        function: The enclosing function's name, or ``<module>``.
        construct: What was found, as a short fixed description.
    """

    line: int
    function: str
    construct: str


def _called_name(call: ast.Call) -> str:
    """Return the bare name a call targets, ignoring how it was reached.

    Args:
        call: The call node.

    Returns:
        The identifier, or an empty string for a call on a complex expression.
    """
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _is_os_open(call: ast.Call) -> bool:
    """Whether a call is ``os.open`` rather than the builtin ``open``.

    Args:
        call: The call node.

    Returns:
        True for the ``os`` module's low-level open.
    """
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "os"
    )


def _mode_argument(call: ast.Call) -> tuple[bool, str | None]:
    """Return (present, literal) for an open call's mode, handling BOTH call shapes.

    THIS IS THE SUBTLE PART AND GETTING IT WRONG SILENTLY DISABLES THE CHECK.
    The builtin ``open(path, mode)`` carries the mode at position ONE, while the
    bound method ``path.open(mode)`` carries it at position ZERO. A scanner that
    assumes a single shape reads the PATH expression as the mode on half of all
    call sites, finds it is not a string constant, and either reports every
    builtin open as suspicious or - worse, depending on which way it errs -
    reports a genuine ``open(p, "wb")`` as having no mode at all.

    Args:
        call: The call node.

    Returns:
        Whether a mode argument is present, and its literal value when it is a
        string constant. A present-but-not-literal mode returns (True, None) and
        is treated as a violation: it cannot be shown to be read-only, and the
        project's rule when a check is uncertain is to refuse.
    """
    for keyword in call.keywords:
        if keyword.arg == "mode":
            value = keyword.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return True, value.value
            return True, None
    index = 1 if isinstance(call.func, ast.Name) else 0
    if len(call.args) > index:
        node = call.args[index]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True, node.value
        return True, None
    return False, None


def _enclosing_functions(tree: ast.Module) -> dict[int, str]:
    """Map every line inside a function body to that function's name.

    Args:
        tree: The parsed module.

    Returns:
        Line number -> innermost enclosing function name.
    """
    owner: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for child in ast.walk(node):
                line = getattr(child, "lineno", None)
                if line is not None:
                    owner.setdefault(line, node.name)
    return owner


def write_sites(source: str) -> list[WriteSite]:
    """Report every write-capable call site in a module's AST.

    Walks the parsed tree, never the text: a docstring is one ``ast.Constant``
    holding a str and a comment does not survive parsing at all, which is what
    lets the modules that document their write discipline in prose scan clean.

    Args:
        source: Module source text.

    Returns:
        The sites, ordered by line.
    """
    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    found: list[WriteSite] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        line = getattr(node, "lineno", 0)
        where = owner.get(line, "<module>")
        name = _called_name(node)

        if name == "open":
            if _is_os_open(node):
                # THE MEASURED GAP. os.open carries its intent in integer flags,
                # so a mode-string scan returns EMPTY for a real write here. Any
                # os.open is reported: proving a flag expression read-only would
                # mean evaluating it, and an unproven one is refused.
                bits = [flag for flag in _WRITE_FLAG_NAMES if flag in ast.dump(node)]
                found.append(WriteSite(line, where, f"os.open flags={bits or ['UNPROVEN']}"))
                continue
            present, mode = _mode_argument(node)
            if present and mode is None:
                found.append(WriteSite(line, where, "open with a non-literal mode"))
            elif mode is not None and (_WRITE_MODE_CHARACTERS_STATIC & set(mode)):
                found.append(WriteSite(line, where, f"open(mode={mode!r})"))
        elif name in _MUTATING_CALL_NAMES:
            found.append(WriteSite(line, where, f"call to {name}"))

    return sorted(found, key=lambda site: site.line)


@pytest.mark.parametrize("relative", READ_ONLY_SOURCES)
def test_no_save_module_outside_the_writer_has_a_write_capable_call_site(relative: str) -> None:
    """CLAUSE 4, signal 3. ADR 0007 decision item 6, converted from intent to assertion.

    That ADR item is explicit that it states a COMMITMENT rather than describing
    shipped code, and that "the phase-4 gate is what converts it from an
    intention into an assertion". This test is that conversion.
    """
    sites = write_sites((SAVE_PACKAGE / relative).read_text(encoding="utf-8"))
    listed = "\n  ".join(f"line {site.line} in {site.function}: {site.construct}" for site in sites)
    assert not sites, (
        f"clockspeed/save/{relative} contains a write-capable call site. Only "
        f"{WRITER_SOURCE} may write:\n  {listed}"
    )


#: The writer's ENTIRE write surface, as (function, construct) pairs. Pinned and
#: asserted EQUAL, not merely non-empty, because workdir.py's own docstring
#: makes a specific claim - one call opens for writing, one renames, one
#: removes, one creates a directory - and a claim in a docstring that nothing
#: checks is a claim that stops being true. Line numbers are deliberately NOT
#: pinned: they drift on any edit and would make this a test about formatting.
WRITER_WRITE_SURFACE: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("_make_dir", "call to mkdir"),
        ("_stream_copy", "open(mode='wb')"),
        ("_stream_copy", "call to write"),
        ("_replace_with_retry", "call to replace"),
        ("_remove_quietly", "call to unlink"),
    }
)


def test_the_writer_write_surface_is_exactly_the_pinned_set() -> None:
    """The one module allowed to write is held to a pinned, audited surface.

    Exempting workdir.py outright would leave the package's only write
    unmeasured, which is the opposite of what ADR 0007 item 6 is for. Asserting
    EQUALITY means a fifth mutating call is red - and so is the quiet deletion
    of one, which would mean the module had stopped doing its job.
    """
    sites = write_sites((SAVE_PACKAGE / WRITER_SOURCE).read_text(encoding="utf-8"))
    surface = {(site.function, site.construct) for site in sites}

    assert surface == WRITER_WRITE_SURFACE, (
        f"{WRITER_SOURCE}'s write surface changed.\n"
        f"  added:   {sorted(surface - WRITER_WRITE_SURFACE)}\n"
        f"  removed: {sorted(WRITER_WRITE_SURFACE - surface)}\n"
        "This is the package's only sanctioned write. A change here needs review, not a "
        "test update."
    )


def test_every_write_in_the_writer_sits_inside_a_function() -> None:
    """No write runs at import time. Importing the module must not touch a disk.

    A module-level write would fire on any import anywhere - including in CI,
    including on a machine with no game - before any caller had asked for
    anything.
    """
    sites = write_sites((SAVE_PACKAGE / WRITER_SOURCE).read_text(encoding="utf-8"))
    at_module_level = [site for site in sites if site.function == "<module>"]
    assert not at_module_level, f"{WRITER_SOURCE} writes at import time: {at_module_level}"


# --- the companion: the scanner is proven to detect, per module -------------

#: One forbidden construct per row, with the marker text expected in the finding.
#: ``os.open`` is first because it is the construct a text-level or mode-only
#: scan MISSES ENTIRELY - measured this session - and it is the reason this
#: scanner reads flags at all.
_INJECTIONS: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "os.open with write flags",
        "def _injected(path):\n    return os.open(path, os.O_WRONLY | os.O_CREAT)\n",
        "os.open",
    ),
    (
        "os.open with unproven flags",
        "def _injected(path, flags):\n    return os.open(path, flags)\n",
        "os.open",
    ),
    (
        "bound open in write mode",
        'def _injected(path):\n    return path.open("wb")\n',
        "open(mode='wb')",
    ),
    (
        "builtin open in write mode",
        'def _injected(path):\n    return open(path, "wb")\n',
        "open(mode='wb')",
    ),
    (
        "builtin open with a keyword mode",
        'def _injected(path):\n    return open(path, mode="a")\n',
        "open(mode='a')",
    ),
    (
        "open with a computed mode",
        "def _injected(path, mode):\n    return open(path, mode)\n",
        "non-literal mode",
    ),
    (
        "write_bytes",
        "def _injected(path):\n    path.write_bytes(b'x')\n",
        "call to write_bytes",
    ),
    ("write_text", "def _injected(path):\n    path.write_text('x')\n", "call to write_text"),
    ("replace", "def _injected(a, b):\n    a.replace(b)\n", "call to replace"),
    ("unlink", "def _injected(path):\n    path.unlink()\n", "call to unlink"),
    ("mkdir", "def _injected(path):\n    path.mkdir()\n", "call to mkdir"),
    ("rmtree", "def _injected(path):\n    shutil.rmtree(path)\n", "call to rmtree"),
    ("os.truncate", "def _injected(path):\n    os.truncate(path, 0)\n", "call to truncate"),
    ("os.symlink", "def _injected(a, b):\n    os.symlink(a, b)\n", "call to symlink"),
)


@pytest.mark.parametrize("relative", READ_ONLY_SOURCES)
@pytest.mark.parametrize(("label", "snippet", "marker"), _INJECTIONS, ids=lambda value: value)
def test_the_write_scanner_catches_each_injected_construct(
    relative: str, label: str, snippet: str, marker: str
) -> None:
    """COMPANION for signal 3: every forbidden construct is caught, in every real module.

    Injected into a COPY OF THE REAL MODULE SOURCE rather than into a synthetic
    stand-in, and into every read-only module rather than one of them. A
    stand-in would prove only that the scanner handles a string this test wrote
    itself; a single module would prove nothing about the other five, each of
    which has its own imports, its own docstring prose and its own shape.

    The line number is asserted too, so a scanner that found the construct
    somewhere and reported it in the wrong place is red - a finding that points
    at the wrong line is a finding a reader cannot act on.
    """
    original = (SAVE_PACKAGE / relative).read_text(encoding="utf-8")
    clean = write_sites(original)
    assert not clean, f"clockspeed/save/{relative} is not clean before injection: {clean}"

    injected_line = len(original.splitlines()) + 2
    doctored = original + "\n\n" + snippet

    sites = write_sites(doctored)
    assert sites, f"the scanner missed an injected {label} in a copy of {relative}"
    assert any(marker in site.construct for site in sites), (
        f"the injected {label} was caught, but not as {marker!r}: "
        f"{[site.construct for site in sites]}"
    )
    assert any(site.line >= injected_line for site in sites), (
        f"the injected {label} was reported at the wrong line; findings must point at the "
        f"injection near line {injected_line}"
    )


_SCANNER_NEGATIVES: Final[tuple[tuple[str, str], ...]] = (
    ("bound open read binary", 'def _f(path):\n    return path.open("rb")\n'),
    ("builtin open read binary", 'def _f(path):\n    return open(path, "rb")\n'),
    ("builtin open keyword read", 'def _f(path):\n    return open(path, mode="rb")\n'),
    ("read_bytes", "def _f(path):\n    return path.read_bytes()\n"),
    ("read_text", "def _f(path):\n    return path.read_text()\n"),
    ("stat", "def _f(path):\n    return path.stat().st_size\n"),
    ("iterdir", "def _f(path):\n    return list(path.iterdir())\n"),
    ("resolve", "def _f(path):\n    return path.resolve()\n"),
    ("is_file", "def _f(path):\n    return path.is_file()\n"),
    ("prose mentioning writes", '"""This module never calls mkdir, rename, unlink or write."""\n'),
)


@pytest.mark.parametrize(("label", "snippet"), _SCANNER_NEGATIVES, ids=lambda value: value)
def test_the_write_scanner_leaves_read_only_constructs_alone(label: str, snippet: str) -> None:
    """COMPANION for signal 3, the other direction: no false positives.

    This half is load-bearing. A scanner that flagged ``path.open("rb")`` or a
    docstring that names the forbidden calls in prose would be switched off
    within a week, and the last entry is the concrete case: every module in this
    package documents its write discipline in exactly those words.
    """
    assert not write_sites(snippet), f"the scanner falsely flagged {label}"


def test_a_mode_only_scan_would_miss_the_flag_based_write() -> None:
    """The measured gap, asserted so the reason for the flag channel cannot be lost.

    Not a test of production code - a test of the CLAIM that justifies the
    scanner's shape. A future reader looking at the os.open branch and thinking
    it redundant will find this, which demonstrates that removing it re-opens a
    real hole.
    """
    snippet = "def _injected(path):\n    return os.open(path, os.O_WRONLY | os.O_CREAT)\n"

    def _mode_only_flags_a_write(call: ast.Call) -> bool:
        """What a mode-string-only scanner would conclude about one call."""
        _, mode = _mode_argument(call)
        return mode is not None and bool(_WRITE_MODE_CHARACTERS_STATIC & set(mode))

    # What a mode-string scan sees: nothing at all. os.open takes no mode
    # string, so there is no mode to inspect and the construct is invisible.
    mode_only = [
        node
        for node in ast.walk(ast.parse(snippet))
        if isinstance(node, ast.Call)
        and _called_name(node) == "open"
        and _mode_only_flags_a_write(node)
    ]
    assert not mode_only, (
        "a mode-string scan now flags os.open; the measurement this scanner's shape rests "
        "on has changed and the flag channel's justification needs restating"
    )

    assert write_sites(snippet), "the full scanner must catch what the mode-only scan misses"


# ===========================================================================
# Phase invariants
# ===========================================================================

# module -> the clockspeed.save submodules importing it is allowed to pull in.
# Read as a CONTRACT, not as a description. Both halves are asserted: the
# forbidden half because that is the layering claim, and the REQUIRED half
# because a negative assertion rules out without pinning down - it would pass
# just as happily for a module that had collapsed to importing nothing.
#
# The four leaf readers import NOTHING from each other, which is what lets each
# be reasoned about and tested alone. objects imports usmap because a property
# map is its input type. world imports all five because composing them is what
# it is for.
ALLOWED_SAVE_IMPORTS: Final[dict[str, frozenset[str]]] = {
    "clockspeed.save": frozenset(),
    "clockspeed.save.chunks": frozenset(),
    "clockspeed.save.header": frozenset(),
    "clockspeed.save.usmap": frozenset(),
    "clockspeed.save.workdir": frozenset(),
    "clockspeed.save.objects": frozenset({"usmap"}),
    "clockspeed.save.world": frozenset({"chunks", "header", "objects", "usmap", "workdir"}),
}

#: No module in this package may reach these. ``solve`` and ``advisor`` sit
#: ABOVE the save layer, and ``tools`` is not a library at all.
FORBIDDEN_IMPORT_ROOTS: Final[tuple[str, ...]] = (
    "clockspeed.advisor",
    "clockspeed.audit",
    "clockspeed.progress",
    "clockspeed.solve",
    "clockspeed.surface",
    "tools",
)

ABSENT = REPO_ROOT / "no-such-path-phase-4-gate"

_IMPORT_PROBE: Final = (
    "import importlib, json, sys\n"
    "importlib.import_module(sys.argv[1])\n"
    "print(json.dumps(sorted(n for n in sys.modules "
    "if n.startswith('clockspeed') or n.startswith('tools'))))\n"
)


def _no_install_env() -> dict[str, str]:
    """Build a child environment in which nothing resolves.

    All four overrides are set. Leaving ``CLOCKSPEED_SAVE_ROOT`` unset would let
    a child fall through to the real save directory, which is exactly the
    machine dependence these tests exist to forbid.

    Returns:
        The environment mapping.
    """
    env = dict(os.environ)
    env[ENV_GAME_DIR] = str(ABSENT / "install")
    env[ENV_SAVE_ROOT] = str(ABSENT / "saves")
    env[ENV_ACCOUNT_DIR] = str(ABSENT / "account")
    env[ENV_LOCAL_CONFIG] = str(ABSENT / "local.json")
    env[workdir.ENV_WORK_ROOT] = str(ABSENT / "work")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run_child(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a child interpreter from the repo root with nothing resolvable.

    ``sys.executable`` is the only correct way to name the interpreter: a bare
    name resolves off PATH to whatever happens to be first, and an absolute
    interpreter path in a tracked file is forbidden outright.

    Args:
        args: Arguments after the interpreter.

    Returns:
        The completed process. A non-zero exit is returned rather than raised.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=_no_install_env(),
        check=False,
    )


def test_the_forced_absent_path_really_is_absent() -> None:
    """The path every child points at must not exist, or the overrides resolve."""
    assert not ABSENT.exists(), (
        f"{ABSENT.name} exists, so the no-install overrides resolve to something real"
    )


@pytest.mark.parametrize("module", SAVE_MODULES)
def test_importing_a_save_module_reaches_only_its_permitted_set(module: str) -> None:
    """IMPORT DIRECTION, measured in a child rather than read out of source text.

    A source scan cannot see an import that fires only under a conditional, nor
    one reached indirectly through a third module. ``sys.modules`` after a fresh
    import sees both.
    """
    probe = _run_child(["-c", _IMPORT_PROBE, module])
    exit_code = probe.returncode
    assert exit_code == 0, f"importing {module} with no install failed:\n{probe.stderr}"

    loaded: list[str] = json.loads(probe.stdout.strip().splitlines()[-1])

    prefix = "clockspeed.save."
    siblings = {
        name.removeprefix(prefix)
        for name in loaded
        if name.startswith(prefix) and name != module and name.removeprefix(prefix)
    }
    permitted = ALLOWED_SAVE_IMPORTS[module]

    forbidden = sorted(siblings - permitted)
    assert not forbidden, (
        f"importing {module} also loaded {forbidden}, outside its permitted set "
        f"{sorted(permitted)} - a layer reaching past its neighbour"
    )

    missing = sorted(permitted - siblings)
    assert not missing, (
        f"{module} no longer imports {missing}; the allowed-import matrix is the contract "
        "and must be changed deliberately, not left describing the past"
    )


@pytest.mark.parametrize("module", SAVE_MODULES)
def test_no_save_module_reaches_a_layer_above_it(module: str) -> None:
    """Nothing under clockspeed/save/ imports solve, advisor, audit, progress or tools.

    The seam discipline in the other direction. ``solve/`` never reads a save,
    and equally the save layer never reaches up into the solver - a layer that
    imports its own consumer cannot be tested or reasoned about alone.
    """
    probe = _run_child(["-c", _IMPORT_PROBE, module])
    exit_code = probe.returncode
    assert exit_code == 0, f"importing {module} failed:\n{probe.stderr}"

    loaded: list[str] = json.loads(probe.stdout.strip().splitlines()[-1])
    violations = sorted(
        name
        for name in loaded
        for root in FORBIDDEN_IMPORT_ROOTS
        if name == root or name.startswith(root + ".")
    )
    assert not violations, f"importing {module} reached {violations}, which sits above it"


def test_the_four_leaf_readers_import_nothing_from_each_other() -> None:
    """The claim stated positively, so it cannot be lost in the matrix above.

    header, chunks, usmap and workdir are the four independent readers. Each was
    proven alone against its own fixtures, and that separation is only real if
    none of them consumes another.
    """
    for module in (
        "clockspeed.save.chunks",
        "clockspeed.save.header",
        "clockspeed.save.usmap",
        "clockspeed.save.workdir",
    ):
        assert ALLOWED_SAVE_IMPORTS[module] == frozenset(), (
            f"{module} is a leaf reader and must import no sibling"
        )


def test_the_composer_imports_all_five() -> None:
    """world.py consumes every sibling, which is what makes it the single seam.

    Asserted so that a composer quietly losing a stage - no longer resolving a
    property map, say - is red rather than a load that silently does less.
    """
    assert ALLOWED_SAVE_IMPORTS["clockspeed.save.world"] == frozenset(
        {"chunks", "header", "objects", "usmap", "workdir"}
    )
    assert len(ALLOWED_SAVE_IMPORTS["clockspeed.save.world"]) == len(SAVE_SOURCES) - 2


#: Workers for the child pytest run, BOUNDED rather than ``auto`` on purpose.
#:
#: THE CHILD USED TO RUN SERIALLY WHILE THE PARENT RAN ``-n auto``, and that is
#: what timed out. The windows-latest leg of tier 2 crossed this module's own
#: ``_CHILD_TIMEOUT_SECONDS`` outright while the ubuntu leg did not, against
#: 68.98s measured serially on the operator's 16 core machine. The runner is
#: 3.6x to 4.3x slower for this work, so the timeout is not mis-set: the work
#: was being done one test at a time on a box the parent had already filled.
#: Distributing the child costs the invariant nothing, because the same tests
#: run in the same stripped environment and only the scheduling changes.
#:
#: NO LANE DURATION TARGET IS RESTATED HERE, and that is deliberate rather than
#: terse - ``.github/workflows/tier1.yml`` is the one owner of this lane's
#: levels and ``tools/drift_guard.py`` guard (k) fails any second statement of
#: one. The CI readings that motivated this change live in the ledger entry.
#:
#: ``auto`` IS THE WRONG ANSWER AND THE CAP IS MEASURED RATHER THAN PREFERRED.
#: The parent is itself running ``-n auto``, so an ``auto`` child asks for a
#: second full set of workers on a box that already carries one, and this
#: repository has measured that hazard twice: concurrent suites exhausting the
#: box RAM, and two parallel xdist suites exhausting the Windows fork budget so
#: that the failures land on unrelated subprocess tests and read as flakes.
#:
#: THE EXTRA WORKERS BUY NOTHING ANYWAY. Measured on this machine at one tree,
#: ``--dist loadfile`` throughout, 1197 passed and 96 skipped on every point:
#:
#:     serial 68.98s | -n 2 46.68s | -n 4 37.72s | -n 8 33.41s | -n 16 33.96s
#:
#: Sixteen workers are SLOWER than eight and the floor sits near 33s, because
#: the critical path under ``loadfile`` is the single slowest FILE and
#: ``test_absolute_claims.py`` alone is roughly 30 of the 69 serial seconds.
#: Four workers take 88 per cent of the entire available gain at a quarter of
#: the process count, and on a four core hosted runner the cap does not bind at
#: all - ``auto`` would ask for four there too - so it costs the platform that
#: actually failed nothing. The floor of two is not taste either: one IS the
#: serial case this constant exists to remove.
#:
#: MEASURED UNDER THE REAL CONTENTION, not just alone: the whole of tests/save
#: run as tier 1 runs it, ``-n auto --dist loadfile`` with sixteen parent
#: workers on sixteen cores, put this child at 39.41s against 37.37s unopposed.
#: The nested run degrades by two seconds under a fully loaded box, which is the
#: property the serial child did not have.
_CHILD_WORKERS: Final = min(4, max(2, os.cpu_count() or 2))

#: How the child distributes, and it is the CI-proven mode rather than the
#: fastest one. ``tests/save`` is run as ``-n auto --dist loadfile`` by tier 1's
#: own save job, so parallel-safety at this setting is established by evidence
#: rather than argued. Per-test ``--dist load`` was measured FASTER here - 32.68s
#: at four workers against 37.72s - and is declined anyway, because it spreads a
#: file's tests across workers in a mode no lane has ever run this directory
#: under, and 5 seconds on the operator's box is not worth finding that out from
#: a red gate.
_CHILD_DIST: Final = "loadfile"


def _child_pytest_args() -> list[str]:
    """Build the argv for the child pytest run over the save-layer suite.

    The recursion guard is explicit and not incidental: without ``--ignore`` the
    child collects this module, which launches its own child, forever. It is an
    absolute path derived from ``__file__``, so a rename cannot leave it
    pointing at a path that no longer exists - which would look green right up
    to the moment the machine ran out of processes.

    The single ``-q`` is deliberate and must stay single: a second one collapses
    ``--collect-only`` to a bare count, and a count carries no test name, so the
    recursion guard below would assert against an empty haystack.

    Returns:
        Arguments after the interpreter.
    """
    return [
        "-m",
        "pytest",
        str(SAVE_TESTS),
        f"--ignore={THIS_MODULE}",
        "-p",
        "no:cacheprovider",
        "-q",
        "-n",
        str(_CHILD_WORKERS),
        "--dist",
        _CHILD_DIST,
    ]


#: How many SEQUENTIAL child calls the nested run is split into.
#:
#: TIER 2 RUN 37193626407 IS WHY. Its windows-latest probe leg ran the whole of
#: tests/save as ONE child call underneath a parent already running ``-n auto``
#: on a four core runner, and that call crossed ``_CHILD_TIMEOUT_SECONDS``. The
#: timeout is a runaway detector, so it is not raised; the work is split so
#: that each call carries a fraction of it. The shards run one after another
#: inside the one gate test, so the process count on the box is unchanged.
#:
#: The per-shard walls this split was sized from are in the ledger entry, not
#: here, for the same reason ``_CHILD_WORKERS`` restates no lane duration.
_CHILD_SHARD_COUNT: Final = 3

#: The fewest shards that split anything. One IS the shape that timed out.
_MIN_CHILD_SHARDS: Final = 2

#: Files split into one unit per top-level test function or class rather than
#: run whole. A file is the smallest unit ``--dist loadfile`` can schedule, so a
#: file heavier than a shard's share would make that shard as slow as the file
#: however the rest were dealt. These two carry most of the nested run's serial
#: time, measured. A name here that no longer exists collects nothing and
#: :func:`_shard_partition_faults` names it, so the pin cannot rot quietly.
_CHILD_SPLIT_FILES: Final = ("test_absolute_claims.py", "test_reach_guard.py")


def _child_units() -> list[str]:
    """Every unit the nested run is dealt from, as a rootdir-relative node id prefix.

    A unit is a test FILE, except in :data:`_CHILD_SPLIT_FILES`, where it is each
    top-level ``test`` function or ``Test`` class. The derivation is not
    trusted: :func:`test_the_shards_partition_the_whole_collection_exactly`
    checks it against pytest's own collection of the whole command.

    Returns:
        The units, files in sorted order and functions in source order.
    """
    units: list[str] = []
    for path in sorted(SAVE_TESTS.glob("test_*.py")):
        if path.resolve() == THIS_MODULE:
            continue
        relative = path.relative_to(REPO_ROOT).as_posix()
        if path.name not in _CHILD_SPLIT_FILES:
            units.append(relative)
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                prefix = "test"
            elif isinstance(node, ast.ClassDef):
                prefix = "Test"
            else:
                continue
            if node.name.startswith(prefix):
                units.append(f"{relative}::{node.name}")
    return units


def _child_shards() -> list[tuple[str, ...]]:
    """Deal the units round-robin into :data:`_CHILD_SHARD_COUNT` shards.

    Round-robin in source order keeps a split file's heavy functions apart
    rather than stacked in one shard, and needs no timing table to rot.

    Returns:
        One tuple of units per shard.
    """
    units = _child_units()
    return [tuple(units[index::_CHILD_SHARD_COUNT]) for index in range(_CHILD_SHARD_COUNT)]


def _child_shard_args(index: int) -> list[str]:
    """The whole child command with its one target replaced by a shard's units.

    Args:
        index: Which shard, from zero.

    Returns:
        Arguments after the interpreter.
    """
    whole = _child_pytest_args()
    at = whole.index(str(SAVE_TESTS))
    return [*whole[:at], *_child_shards()[index], *whole[at + 1 :]]


def _unit_covers(unit: str, node_id: str) -> bool:
    """Whether running ``unit`` as a pytest target runs ``node_id``.

    Args:
        unit: A file, or a file plus one function or class name.
        node_id: A collected node id.

    Returns:
        True when the node id is the unit or sits under it at a real boundary.
    """
    return node_id == unit or node_id.startswith((f"{unit}::", f"{unit}["))


def _shard_partition_faults(shards: list[tuple[str, ...]], collected: list[str]) -> list[str]:
    """Every way ``shards`` fails to run each of ``collected`` exactly once.

    Separated from the arm that uses it so it can be graded by planted faults.

    Args:
        shards: The units of each shard.
        collected: Node ids collected by the whole command.

    Returns:
        A sentence per fault, sorted.
    """
    found: list[str] = []
    if len(shards) < _MIN_CHILD_SHARDS:
        found.append(f"the run is {len(shards)} shard(s), which is one call over the whole")
    found.extend(f"shard {index} is empty" for index, units in enumerate(shards) if not units)
    every_unit = [unit for units in shards for unit in units]
    for node_id in collected:
        runs = sum(1 for unit in every_unit if _unit_covers(unit, node_id))
        if runs != 1:
            found.append(f"{node_id} is run {runs} times across the shards")
    found.extend(
        f"the unit {unit} collects nothing"
        for unit in every_unit
        if not any(_unit_covers(unit, node_id) for node_id in collected)
    )
    return sorted(found)


def test_the_save_suite_passes_with_no_install_and_no_save() -> None:
    """PHASE INVARIANT. The whole save suite is green with all four overrides absent.

    This is the environment CI and every fresh clone run in, and on the
    operator's machine - where the game IS installed and a save library DOES
    exist - it is the only thing that reproduces it. A test that reached for the
    real install, the real save root or the operator's config/local.json turns
    this red here, which is the only place the mistake is otherwise invisible.

    A test that genuinely needs a save is not forbidden; it must skip with a
    reason, and a skip keeps the exit code at zero.

    THE WHOLE IS RUN AS SEQUENTIAL SHARDS, each its own child call under its own
    timeout - see :data:`_CHILD_SHARD_COUNT`. That they are together the whole,
    each exactly once, is graded by
    :func:`test_the_shards_partition_the_whole_collection_exactly`.
    """
    for index in range(len(_child_shards())):
        child = _run_child(_child_shard_args(index))
        exit_code = child.returncode
        assert exit_code == 0, (
            f"shard {index} of the save-layer suite does not pass without an install or "
            "a save library.\n"
            f"exit code: {exit_code}\n"
            f"stdout:\n{child.stdout}\n"
            f"stderr:\n{child.stderr}"
        )

        passed = re.search(r"(\d+) passed", child.stdout)
        assert passed is not None, f"shard {index} reported no passing tests:\n{child.stdout}"
        assert int(passed.group(1)) > 0


def test_the_child_run_excludes_this_module_so_the_gate_cannot_recurse() -> None:
    """The recursion guard is verified against pytest's own collection, not assumed.

    ``--ignore`` silently accepts a path it does not match, so the guard working
    is a claim until pytest is asked what it collected. Both halves matter: this
    module absent, and the rest of the save suite present. A guard that excluded
    everything would also make the test above pass.
    """
    child = _run_child([*_child_pytest_args(), "--collect-only"])
    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = child.stdout
    assert THIS_MODULE.name not in collected, (
        f"{THIS_MODULE.name} is collected by its own child run, so the gate recurses"
    )
    for sibling in ("test_header.py", "test_chunks.py", "test_workdir.py", "test_world.py"):
        assert sibling in collected, (
            f"the child run collects no {sibling}; the ignore is too wide and the gate "
            "would pass by testing nothing"
        )


#: Every flag that makes pytest collect LESS than its targets name, scanned
#: AFTER the literal ``pytest`` token. That boundary is not a detail: this argv
#: opens with PYTHON's own ``-m``, and a scan over the whole list would read the
#: module flag as pytest's marker expression and refuse a correct command.
#:
#: ``-p`` IS NOT HERE BECAUSE IT IS GRADED BY VALUE INSTEAD, and that is a
#: judgement rather than an omission (CS-1073). This command carries
#: ``-p no:cacheprovider`` on purpose - the child must not write a cache into
#: the parent's rootdir - so a flat ban would refuse the shipped command, and a
#: flat permission would let any other plugin be disabled. MEASURED on this box:
#: ``-p no:unittest`` silently drops ``unittest.TestCase`` collection, three
#: collected becoming two passed, exit 0. tests/save carries no TestCase today,
#: so that one is latent rather than live - but tier 1 no longer runs this gate,
#: which raises the stakes on every remaining way it can quietly collect less.
#: :data:`_CHILD_PERMITTED_PLUGIN_ARGUMENTS` is the allowlist that settles it.
_CHILD_NARROWING_FLAGS: Final = (
    "-k",
    "-m",
    "--deselect",
    "--ignore-glob",
    "--maxfail",
    "-x",
    "--exitfirst",
    "--lf",
    "--ff",
    "--last-failed",
    "--failed-first",
    "--co",
    "--collect-only",
)

#: The flags in this command that take their value as the NEXT token. Without
#: them the value reads as a positional target - ``4`` after ``-n``, ``loadfile``
#: after ``--dist`` - and the target check below would report a narrowing that
#: is not there.
_CHILD_VALUE_FLAGS: Final = ("-n", "--dist", "-p", "-k", "-m", "--deselect", "--maxfail")

#: The only ``-p`` arguments this command may carry. AN ALLOWLIST, for the
#: reason `tests/test_tier1_budget.py` records beside its own: a rule phrased as
#: "not the bad ones" is a list somebody has to keep complete, and this
#: repository has already measured one defect wearing four different fields
#: across four green commits before an allowlist of good values held it.
_CHILD_PERMITTED_PLUGIN_ARGUMENTS: Final = ("no:cacheprovider",)

#: The plugin flag, named once. Also the reason the scan below binds its loop
#: variable to `word` rather than `token`: ruff's S105 reads a comparison
#: against anything called `token` as a hardcoded credential.
_PLUGIN_FLAG: Final = "-p"


def _child_targets(args: list[str]) -> list[str]:
    """The paths the child hands pytest, with flag values not mistaken for one.

    Args:
        args: The child's argv after the interpreter.

    Returns:
        Every positional target, in order.
    """
    assert "pytest" in args, f"this command does not invoke pytest: {args}"
    after = args[args.index("pytest") + 1 :]
    targets: list[str] = []
    skip = False
    for token in after:
        if skip:
            skip = False
            continue
        if token.startswith("-"):
            skip = "=" not in token and token in _CHILD_VALUE_FLAGS
            continue
        targets.append(token)
    return targets


def _child_narrowings(args: list[str]) -> list[str]:
    """Every way ``args`` collects less than the whole of ``tests/save``.

    SEPARATED FROM THE ARM THAT USES IT SO IT CAN BE GRADED. An arm that reads
    the shipped command and finds nothing wrong passes identically whether it
    asks the right question or no question at all, so the question is lifted out
    and the arm below hands it commands with known holes.

    THE RECURSION GUARD IS THE ONE PERMITTED EXCLUSION AND IT IS PINNED BY
    IDENTITY, not merely counted. One ``--ignore=`` naming this module is how
    the gate avoids launching itself forever; a second one, or a first one
    naming anything else, is a narrowing whatever it is spelled as.

    Args:
        args: The child's argv after the interpreter.

    Returns:
        A sentence per narrowing found, sorted.
    """
    found: list[str] = []

    targets = _child_targets(args)
    if targets != [str(SAVE_TESTS)]:
        found.append(f"the child targets {targets} rather than [{str(SAVE_TESTS)!r}]")

    permitted = f"--ignore={THIS_MODULE}"
    excluded = [token for token in args if token.startswith("--ignore=")]
    if excluded != [permitted]:
        found.append(f"the child excludes {excluded} rather than [{permitted!r}]")

    after = args[args.index("pytest") + 1 :] if "pytest" in args else args
    selectors = [token for token in after if token.split("=", 1)[0] in _CHILD_NARROWING_FLAGS]
    found.extend(f"the child passes the selector {token!r}" for token in selectors)

    plugins = [
        after[index + 1]
        for index, word in enumerate(after)
        if word == _PLUGIN_FLAG and index + 1 < len(after)
    ]
    found.extend(
        f"the child disables the plugin {argument!r}"
        for argument in plugins
        if argument not in _CHILD_PERMITTED_PLUGIN_ARGUMENTS
    )
    if len(plugins) != after.count(_PLUGIN_FLAG):
        found.append("the child writes a bare -p with no argument after it")

    return sorted(found)


def test_the_child_runs_the_whole_of_the_save_suite_and_not_a_slice_of_it() -> None:
    """CS-1073 - tier 1 stopped running this module, so its own reach is now the gate.

    THE DELETION THIS ARM EXISTS FOR. `.github/workflows/tier1.yml`'s save shard
    carries `--ignore=tests/save/test_phase4_gate.py`, because this one test
    re-runs the whole of tests/save as a nested child and dominated that shard.
    The measurement, the run it came from and the reasoning are in the workflow,
    which owns every duration this project states about that lane - repeating
    one here would make this file a second owner of it. What is left running the
    gate is `.githooks/pre-push` - on the operator's box, where the game IS
    installed and a save library DOES exist, which is where its docstring says
    the value actually is - and tier 2's `full suite`, on both legs of every
    lane row.

    SO THE REMAINING RISK IS NOT THAT THE GATE STOPS RUNNING. It is that the
    gate goes on running while quietly covering less: a target pointed at one
    file or one subdirectory, a second ``--ignore=`` for whatever is slow this
    month, a marker expression. Every one of those leaves this module green, the
    parent suite green and the lane green, over a save suite nobody proved clean
    on a machine with no install and no save. A deletion from tier 1 must not be
    convertible into a weaker gate here, and that is exactly what this pins.
    """
    narrowings = _child_narrowings(_child_pytest_args())

    assert narrowings == [], (
        f"{narrowings}. The child run is the WHOLE of tests/save minus this module and "
        "nothing else: tier 1 no longer runs this gate, so a child that collects less is "
        "a claim about the save suite that nothing anywhere makes"
    )


def test_a_narrowed_child_command_is_named_rather_than_walked_past() -> None:
    """CS-1073 - the arm above passes over the shipped command, and only over that.

    It reports the same empty list whether it reads the target, reads a key that
    does not exist, or reads nothing. So each narrowing is PLANTED IN TURN and
    the detector is required to name that one - every plant is checked to have
    actually changed the command first, because a mutation that never applied
    and a detector that missed it print the same thing.

    IN TURN, AND NOT ONCE. A detector that stopped at the first fault, or that
    reported only the last, passes a single-mutation grading and then misses the
    shape nobody thought to try.
    """
    shipped = _child_pytest_args()
    assert _child_narrowings(shipped) == [], (
        "the shipped command is already narrowed, so a red below attributes to nothing"
    )

    one_file = str(SAVE_TESTS / "test_header.py")
    plants: dict[str, list[str]] = {
        # Pointed at one file of the directory rather than the directory.
        "a single file": [one_file if token == str(SAVE_TESTS) else token for token in shipped],
        # Pointed at a subdirectory. Named rather than walked, so a subdirectory
        # added later cannot quietly become the whole target.
        "a subdirectory": [
            str(SAVE_TESTS / "data") if token == str(SAVE_TESTS) else token for token in shipped
        ],
        # The target dropped entirely, which leaves pytest collecting rootdir.
        "no target at all": [token for token in shipped if token != str(SAVE_TESTS)],
        # A second exclusion beside the recursion guard.
        "a second ignore": [*shipped, f"--ignore={one_file}"],
        # A marker expression, which subtracts in total silence.
        "a marker expression": [*shipped, "-m", "not slow"],
        # A name expression, the same fault wearing a different flag.
        "a name expression": [*shipped, "-k", "not header"],
        # Collection only, which makes every assertion about a run vacuous.
        "collection only": [*shipped, "--collect-only"],
        # A plugin disabled by name. MEASURED: `-p no:unittest` drops
        # `unittest.TestCase` collection and still exits 0, so the summary line
        # is identical whether the tests ran or were never seen.
        "a disabled plugin": [*shipped, "-p", "no:unittest"],
        # The permitted plugin argument swapped for another, which a rule
        # phrased as "-p is fine" would wave through.
        "the permitted -p retargeted": [
            "no:unittest" if word in _CHILD_PERMITTED_PLUGIN_ARGUMENTS else word for word in shipped
        ],
        # A bare -p with nothing after it, which the scan above would otherwise
        # read as a flag carrying no argument and therefore no narrowing.
        "a bare -p": [*shipped, "-p"],
    }

    escaped: list[str] = []
    for case, planted in plants.items():
        assert planted != shipped, f"{case}: the plant never landed, so it graded nothing"
        if not _child_narrowings(planted):
            escaped.append(case)

    assert escaped == [], (
        f"{escaped} were planted into the child command and the detector named NONE of "
        "them, so it reports a clean command for one that collects less than the save "
        "suite"
    )


def test_the_child_run_asks_for_bounded_parallelism_rather_than_auto() -> None:
    """The child is parallel AND capped, and neither half may be lost in silence.

    Both regressions are invisible in a green summary line. Dropping ``-n`` puts
    the child back to one process underneath a parent running ``-n auto``, which
    is precisely the shape that crossed the timeout; widening it to ``auto``
    asks a box already carrying a full set of workers for a second one.

    THE CEILING IS A LITERAL HERE, stated independently of the expression that
    computes :data:`_CHILD_WORKERS`, so an edit letting that expression track the
    core count reddens on any machine with more than four. An arm that recomputed
    the same formula would agree with the constant by construction and grade
    nothing.

    The distribution mode is asserted too. ``loadfile`` is the only mode any lane
    has run ``tests/save`` under, so switching it is a claim about parallel
    safety that no measurement in this repository backs.
    """
    args = _child_pytest_args()

    assert "-n" in args, (
        "the child run names no worker count, so it is serial again underneath a "
        "parent running -n auto - the shape that timed out"
    )
    workers = args[args.index("-n") + 1]
    assert workers != "auto", (
        "the child asks for auto workers while the parent already runs -n auto, which "
        "is the oversubscription this cap exists to refuse"
    )
    assert workers.isdigit(), f"the child's worker count is not a plain number: {workers!r}"

    # STATED AS LITERALS, AND DELIBERATELY NOT READ FROM _CHILD_WORKERS. Reading
    # the bound from the expression under test would make this agree by
    # construction and grade nothing; written out here, an edit that lets the
    # constant track the core count reddens on any machine with more than four.
    serial_is_one, measured_floor_is_reached_by = 2, 4
    assert serial_is_one <= int(workers) <= measured_floor_is_reached_by, (
        f"the child asks for {workers} workers; four reaches the measured floor and one "
        "is the serial case this bound exists to remove"
    )

    assert "--dist" in args, "the child states no distribution mode"
    assert args[args.index("--dist") + 1] == "loadfile", (
        "the child distributes by something other than loadfile, which is the only mode "
        "a lane has ever run tests/save under"
    )


# --- the nested run is SHARDED, and the shards together are the whole ---------


def test_the_nested_run_is_split_so_no_one_child_call_carries_the_whole_suite() -> None:
    """Tier 2 run 37193626407 - one child call over the whole suite crossed its timeout.

    The windows-latest probe leg ran the nested child as ONE call and it crossed
    ``_CHILD_TIMEOUT_SECONDS`` under a parent running ``-n auto``. The timeout is
    a runaway detector and is not raised; the run is split instead, so each call
    carries a fraction of the work. Two is the floor because one IS the shape
    that timed out.
    """
    shard_count = len(_child_shards())
    assert shard_count >= _MIN_CHILD_SHARDS, (
        f"the nested run is {shard_count} child call(s), and one call over the whole "
        "save suite is the shape that crossed the timeout"
    )
    whole_target = str(SAVE_TESTS)
    for index in range(shard_count):
        targets = _child_targets(_child_shard_args(index))
        target_count = len(targets)
        assert target_count > 0, f"shard {index} names no target, so pytest walks rootdir"
        assert whole_target not in targets, (
            f"shard {index} targets the whole of tests/save, so the split splits nothing"
        )


def test_every_shard_command_is_the_whole_command_with_only_its_targets_swapped() -> None:
    """A shard may differ from the graded whole command in its targets and nowhere else.

    The narrowing, recursion and parallelism arms above all grade
    ``_child_pytest_args``. They say something about what actually RUNS only
    while every shard is that command with the one target replaced, so that is
    pinned token for token rather than assumed.
    """
    whole = _child_pytest_args()
    whole_target = str(SAVE_TESTS)
    for index, units in enumerate(_child_shards()):
        shard = _child_shard_args(index)
        targets = _child_targets(shard)
        assert targets == list(units), f"shard {index} runs targets other than its units"
        rest = [token for token in shard if token not in targets]
        expected_rest = [token for token in whole if token != whole_target]
        assert rest == expected_rest, (
            f"shard {index} carries a flag the graded whole command does not, or lacks one"
        )


def _collected_node_ids(stdout: str) -> list[str]:
    """The node ids a ``-q --collect-only`` run printed, one per line.

    Args:
        stdout: The child's standard output.

    Returns:
        Every line that is a node id, in order.
    """
    return [line.strip() for line in stdout.splitlines() if "::" in line]


def test_the_shards_partition_the_whole_collection_exactly() -> None:
    """Every test the whole command collects is run by EXACTLY ONE shard.

    The claim "the save suite passes with no install and no save" is now made by
    several calls, so it is only as true as their union. The reference is
    pytest's own collection of the whole command - the one the narrowing arm
    grades - not this module's derivation of its units, which is the thing
    being checked.
    """
    child = _run_child([*_child_pytest_args(), "--collect-only"])
    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = _collected_node_ids(child.stdout)
    collected_count = len(collected)
    assert collected_count > 0, "the whole command collected no node id to partition"

    faults = _shard_partition_faults(_child_shards(), collected)
    assert faults == [], f"{faults}. The shards must together run every collected test exactly once"


def test_a_broken_partition_is_named_rather_than_walked_past() -> None:
    """The partition detector is graded by planting each fault in turn.

    The arm above passes identically over a correct split and over a detector
    that reads nothing, so every plant is first checked to have landed and the
    detector is then required to name it.
    """
    collected = [
        "tests/save/test_a.py::test_one",
        "tests/save/test_a.py::test_two[x]",
        "tests/save/test_a.py::test_two[y]",
        "tests/save/test_b.py::test_three",
        "tests/save/test_b.py::TestGroup::test_four",
    ]
    good: list[tuple[str, ...]] = [
        ("tests/save/test_a.py::test_one", "tests/save/test_b.py"),
        ("tests/save/test_a.py::test_two",),
    ]
    assert _shard_partition_faults(good, collected) == [], (
        "the control partition is already faulted, so a red below attributes to nothing"
    )

    plants: dict[str, list[tuple[str, ...]]] = {
        "a unit dropped": [("tests/save/test_a.py::test_one",), good[1]],
        "a unit in two shards": [good[0], (*good[1], "tests/save/test_b.py")],
        "a file beside its own function": [good[0], (*good[1], "tests/save/test_a.py")],
        "a unit naming nothing": [good[0], (*good[1], "tests/save/test_gone.py")],
        "an empty shard": [*good, ()],
        "one shard only": [(*good[0], *good[1])],
        "a prefix that is not a boundary": [
            ("tests/save/test_a.py::test_one", "tests/save/test_b.py"),
            ("tests/save/test_a.py::test_tw",),
        ],
    }

    escaped: list[str] = []
    for case, planted in plants.items():
        assert planted != good, f"{case}: the plant never landed, so it graded nothing"
        if not _shard_partition_faults(planted, collected):
            escaped.append(case)

    assert escaped == [], f"{escaped} were planted and the partition detector named none"


# --- the redactor is imported, never re-implemented -------------------------


def _redact_definitions(source: str) -> list[str]:
    """Find any function or assignment in a module that DEFINES a redactor.

    Args:
        source: Module source text.

    Returns:
        The offending names.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and "redact" in node.name:
            found.append(node.name)
        elif isinstance(node, ast.Assign):
            found.extend(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and "redact" in target.id
            )
    return found


@pytest.mark.parametrize("relative", SAVE_SOURCES)
def test_no_save_module_defines_its_own_redactor(relative: str) -> None:
    """PHASE INVARIANT. There is ONE redactor and this package does not fork it.

    A second redactor is a second thing to keep correct, and the one that gets
    forgotten is the one that leaks. ADR 0007 is explicit that redaction is the
    load-bearing privacy mechanism here, and a per-module copy is how it stops
    being one.
    """
    definitions = _redact_definitions((SAVE_PACKAGE / relative).read_text(encoding="utf-8"))
    assert not definitions, (
        f"clockspeed/save/{relative} defines its own redactor {definitions}; import "
        "clockspeed.data.locate.redact instead"
    )


# --- CS-423: a module that calls no redactor states WHY, and it is checked ----
#
# THE SWEEP ABOVE USED TO SKIP, AND THE SKIP WAS THE BUG. Four of the seven
# scanned modules emitted `SKIPPED ... calls no redactor` on every run, one of
# them the module holding decoded world content. That is the unrun-gate failure
# class: a skip is invisible in a green summary line, and this one had been
# visible-but-ignored since before the module it most mattered for grew its leak
# surface.
#
# THE HONEST COMPLICATION IS WHY THIS IS NOT SIMPLY A BUG. "Calls no redactor"
# is arguably CORRECT for all four. `clockspeed.data.locate.redact()` strips
# PATHS, account names and account ids; a module that never receives a path has
# nothing for it to strip, and calling it anyway would be cargo cult. So the
# skip was defensible and the SILENCE was not.
#
# WHAT IS GENERALISED HERE IS THE QUESTION, NOT THE ANSWER. The question asked
# of every module in the scanned set is the same one - "if you do not redact,
# what stops you rendering personal data?" - and the four answers genuinely
# differ. A single blanket assertion over all four would be the thing that reads
# as coverage and is not. Each module therefore declares one or more mitigation
# KINDS from a closed set, and each kind has its own checker that is asserted
# LIVE against the shipped source.
#
# EVERY KIND IS DISCRIMINATING RATHER THAN UNIVERSAL, and that is checked:
# `test_each_absence_checker_rejects_the_violation_it_describes` splices the
# matching violation into a copy of a real module and asserts the checker goes
# red. A checker that passed on everything would be worse than the skip it
# replaced, because it would look like a grade.
#
# `redact()` IS ALSO A MEASURED NO-OP ON THE PINNED PROJECT ROOT, so an oracle
# built on "the redacted rendering differs from the raw one" would pass here and
# fail on a clone under a home directory. Nothing below depends on redact()
# transforming anything.

#: The module defines no function and no class, so it has no surface that could
#: raise or render in the first place.
_MITIGATION_NO_CODE: Final = "defines-no-code"

#: No path ever reaches the module - no pathlib import, no ``Path`` annotation
#: and no filesystem primitive - so the redactor would have nothing to strip.
_MITIGATION_NO_PATH: Final = "no-path-reaches-it"

#: No RECORD the module exposes carries save bytes: no field of any dataclass it
#: defines is annotated ``bytes``. Records reference the caller's buffer by
#: offset and length instead.
#:
#: THE NAME AND THE TEXT ARE NARROW ON PURPOSE, and CS-433 is why. This kind was
#: spelled ``retains-no-save-bytes`` and its text said the module "parses save
#: bytes but RETAINS none of them" - a claim about the whole module, checked by
#: a function that reads dataclass fields. ``objects.py`` binds the whole body
#: to ``_Cursor._data``, which is not a dataclass field, so the module shipped a
#: green grade asserting an absence it did not have. A false guarantee is worse
#: than the skip CS-423 replaced, because a skip is visible in every run and a
#: green grade reads as evidence. The claim now stops where its checker does,
#: and the retention it does have is graded by
#: :data:`_MITIGATION_RETAINED_BYTES_NEVER_RENDERED`.
_MITIGATION_RECORDS_RETAIN_NO_BYTES: Final = "records-retain-no-save-bytes"

#: The module DOES hold save bytes on an attribute, and no rendering construct
#: in it can reach them: no ``raise`` names one, no f-string interpolates one,
#: no ``repr``/``str`` call takes one and no ``__repr__`` or ``__str__`` renders
#: one.
#:
#: THE KIND IS ONLY AVAILABLE TO A MODULE THAT ACTUALLY RETAINS, and its checker
#: reports a violation when nothing does. Without that, deleting the retaining
#: class would leave this passing vacuously - the "negative assertion rules out
#: without pinning down" class from memory/test-quality-failure-classes.md,
#: where an empty module satisfies every absence check ever written.
_MITIGATION_RETAINED_BYTES_NEVER_RENDERED: Final = "retained-bytes-are-never-rendered"

#: The module DOES take a path, but no ``raise`` in it names one: every failure
#: is reported as a stage constant plus an exception type name, and the path
#: handling is delegated to a module that does redact.
_MITIGATION_PATH_IS_NEVER_RAISED: Final = "path-is-never-raised"

#: Attribute or bare names through which a path can enter a module.
#:
#: IMPORTED RATHER THAN TRANSCRIBED, and that is CS-433's repair. This tuple was
#: authored here in the same commit that left ``test_properties``' reach guard
#: naming none of these, so the two lists disagreed about what a path-bearing
#: name is from the moment both existed - and the reach guard was the one that
#: mattered, because it passed helpers walking a save root with ``rglob`` and
#: ``iterdir``. ``test_properties`` owns the vocabulary now and derives its own
#: narrower reach set from it by a declared partition; this module keeps the
#: WHOLE vocabulary, because the subject differs. A SAVE module has no
#: legitimate reason to read a file or walk a tree at all, so nothing here is
#: excluded.
_FILESYSTEM_PRIMITIVES: Final = reach_guard._FILESYSTEM_PRIMITIVES  # noqa: SLF001


def _defines_no_code(tree: ast.Module) -> list[str]:
    """Violations of :data:`_MITIGATION_NO_CODE`.

    Args:
        tree: The parsed module.

    Returns:
        The names of any functions or classes defined, empty when there are none.
    """
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    ]


def _path_reaches(tree: ast.Module) -> list[str]:
    """Violations of :data:`_MITIGATION_NO_PATH`.

    Three ways a path gets in, and all three are checked: imported, annotated,
    or produced by a filesystem call.

    Args:
        tree: The parsed module.

    Returns:
        Short labels for each way a path reaches the module.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.ImportFrom) and node.module == "pathlib") or (
            isinstance(node, ast.Import) and any(a.name == "pathlib" for a in node.names)
        ):
            found.append("imports pathlib")
        elif isinstance(node, ast.arg) and node.annotation is not None:
            if "Path" in ast.unparse(node.annotation):
                found.append(f"parameter {node.arg}")
        elif isinstance(node, ast.FunctionDef) and node.returns is not None:
            if "Path" in ast.unparse(node.returns):
                found.append(f"returns from {node.name}")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in _FILESYSTEM_PRIMITIVES:
                found.append(f"calls .{func.attr}")
            elif isinstance(func, ast.Name) and func.id in _FILESYSTEM_PRIMITIVES:
                found.append(f"calls {func.id}")
    return sorted(set(found))


def _retained_bytes_fields(tree: ast.Module) -> list[str]:
    """Violations of :data:`_MITIGATION_RECORDS_RETAIN_NO_BYTES`.

    A dataclass field annotated ``bytes`` is a RECORD holding save content
    rather than pointing at the caller's copy of it. That is the precise sense
    in which this mitigation is absence-of-value, and the precise thing that
    would stop being true.

    IT IS A CLAIM ABOUT RECORDS AND NOT ABOUT THE MODULE. Reading dataclass
    fields is all this function has ever done; what changed in CS-433 is the
    kind it answers for, which used to be worded as though it covered every
    attribute in the file. :func:`_retained_body_attributes` is the one that
    covers those.

    NOT A UNIVERSAL PROPERTY, which is what makes it a grade rather than a
    decoration: ``chunks.DecompressedBody.payload`` is annotated ``bytes``,
    correctly and by design, so ``chunks.py`` cannot and does not claim this
    kind.

    Args:
        tree: The parsed module.

    Returns:
        ``Class.field`` for each bytes-typed dataclass field.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(ast.unparse(d).startswith("dataclass") for d in node.decorator_list):
            continue
        found.extend(
            f"{node.name}.{stmt.target.id}"
            for stmt in node.body
            if isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and "bytes" in ast.unparse(stmt.annotation)
        )
    return found


#: Type words that mean "this attribute has come to hold the decompressed
#: world". DERIVED from the reach guard's own personal-data vocabulary rather
#: than written down again, minus the ones that are a PATH rather than a body.
#:
#: CS-494 - THIS WALK AND ``reach_guard._bound_parameter_annotations`` ARE TWO
#: WALKS OVER ONE KIND OF THING, which is the drift ``_FILESYSTEM_PRIMITIVES``
#: was unified to prevent. They are not merged, because they answer different
#: questions over different files: that one asks whether a class in the TEST
#: package holds anything personal-data bearing, including a real path; this one
#: asks whether an attribute of a SHIPPED save module holds save BYTES. What was
#: wrong is that this one was keyed on the single word ``bytes`` while its
#: sibling read a vocabulary, so ``bytearray``, ``memoryview`` and ``BytesIO``
#: were outside it for no stated reason. The remaining difference is recorded
#: and graded by
#: ``test_the_two_walks_over_held_bytes_differ_only_where_recorded``.
_BODY_TYPE_WORDS: Final = frozenset(reach_guard._PERSONAL_DATA_TYPES) - {"Path"}  # noqa: SLF001


def _names_a_body_type(annotation: ast.expr | None) -> bool:
    """Whether an annotation names a type that carries the decompressed world.

    Args:
        annotation: The annotation node, or None when there is none.

    Returns:
        True when it names one of :data:`_BODY_TYPE_WORDS`.
    """
    if annotation is None:
        return False
    rendered = ast.unparse(annotation)
    return any(word in rendered for word in _BODY_TYPE_WORDS)


def _retained_body_attributes(tree: ast.Module) -> list[str]:
    """Every attribute in a module that comes to hold save bytes, dataclass or not.

    THREE SHAPES, because the dataclass one alone missed the module the whole
    grade was about. ``_Cursor.__init__`` does ``self._data = data`` where
    ``data`` is the decompressed body, and an ordinary assignment in an ordinary
    class is invisible to a walk that reads ``@dataclass`` annotated fields.

    - A dataclass field annotated with a body type.
    - ``self.x: bytes = ...``, an annotated attribute assignment.
    - ``self.x = param`` where the enclosing function annotates ``param`` as one.
      Derived from the SIGNATURE rather than from a list of attribute names, so a
      module that renames its buffer is still read.
    - ``self.x, self.y = a, b``, a TUPLE target, whose elements a single-target
      read cannot pair with their values.
    - ``@property def x(self) -> bytes``, which hands the held thing out and
      states its type on the way.

    THE LAST TWO AND THE VOCABULARY ARE CS-494. This walk read the single word
    ``bytes`` and three shapes while ``reach_guard._bound_parameter_annotations``
    read a vocabulary and covered the tuple target and the property. **Measured
    before the widening: it adds nothing at all on the shipped save modules** -
    which is the point, since a grade that only catches what is already there
    catches nothing. The two walks are still not merged; they ask different
    questions over different files, and the difference that remains is graded by
    ``test_the_two_walks_over_held_bytes_differ_only_where_recorded``.

    A reference is retention for this purpose even though ``bytes`` is immutable
    and nothing is copied: the object outlives the call that made it, and every
    frame holding it is a frame pytest can render.

    Args:
        tree: The parsed module.

    Returns:
        ``Class.attribute`` for each, sorted and deduplicated.
    """
    found: list[str] = []
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        found.extend(
            f"{cls.name}.{stmt.target.id}"
            for stmt in cls.body
            if isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and _names_a_body_type(stmt.annotation)
        )
        for member in cls.body:
            if not isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            # A PROPERTY HANDS THE HELD THING OUT and states its type on the
            # way. Read here for the reason the sibling walk gives: the type is
            # written plainly and was simply not being read.
            if any(
                "property" in ast.unparse(one) for one in member.decorator_list
            ) and _names_a_body_type(member.returns):
                found.append(f"{cls.name}.{member.name}")
            args = member.args
            byte_params = {
                arg.arg
                for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]
                if _names_a_body_type(arg.annotation)
            }
            for stmt in ast.walk(member):
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Attribute)
                    and _names_a_body_type(stmt.annotation)
                ):
                    found.append(f"{cls.name}.{stmt.target.attr}")
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    # THE TUPLE TARGET, paired element by element. A
                    # single-target read cannot pair `self.a, self.b = x, y`
                    # with its values, which is the shape the sibling walk
                    # covers and this one did not.
                    if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Tuple):
                        pairs = list(zip(target.elts, stmt.value.elts, strict=False))
                    else:
                        pairs = [(target, stmt.value)]
                    found.extend(
                        f"{cls.name}.{one.attr}"
                        for one, value in pairs
                        if isinstance(one, ast.Attribute)
                        and isinstance(value, ast.Name)
                        and value.id in byte_params
                    )
    return sorted(set(found))


#: One source per shape a class can come to hold the decompressed world by,
#: with what each of the two walks reports and - where they differ - why.
#:
#: THIS IS CS-494's SECOND ACCEPTANCE BRANCH: the difference between
#: :func:`_retained_body_attributes` and
#: ``reach_guard._bound_parameter_annotations`` is RECORDED here and GRADED by
#: the test below, rather than described in a docstring where nothing can check
#: it. Five of the six differences that existed when this was written were
#: closed by widening this module's walk; the one that remains is a difference
#: of SUBJECT rather than of coverage, and it is written down with its reason.
#:
#: Each entry is the source, what the reach guard's wrapper walk says, what this
#: module's retention walk says, and the reason they differ - empty when they
#: agree, which the test requires both ways round.
_HELD_BYTES_SHAPES: Final[Mapping[str, tuple[str, bool, bool, str]]] = MappingProxyType(
    {
        "dataclass-field": (
            "from dataclasses import dataclass\n\n\n@dataclass\nclass _Holder:\n    body: bytes\n",
            True,
            True,
            "",
        ),
        "annotated-store": (
            "class _Holder:\n    def __init__(self, body):\n        self.body: bytes = body\n",
            True,
            True,
            "",
        ),
        "annotated-parameter": (
            "class _Holder:\n    def __init__(self, body: bytes):\n        self.body = body\n",
            True,
            True,
            "",
        ),
        "tuple-target": (
            "class _Holder:\n    def __init__(self, body: bytes, count: int):\n"
            "        self.body, self.count = body, count\n",
            True,
            True,
            "",
        ),
        "property-accessor": (
            "class _Holder:\n    @property\n    def body(self) -> bytes:\n"
            "        return self._body\n",
            True,
            True,
            "",
        ),
        "bytearray-parameter": (
            "class _Holder:\n    def __init__(self, body: bytearray):\n        self.body = body\n",
            True,
            True,
            "",
        ),
        "memoryview-parameter": (
            "class _Holder:\n    def __init__(self, body: memoryview):\n        self.body = body\n",
            True,
            True,
            "",
        ),
        "bytesio-parameter": (
            "from io import BytesIO\n\n\nclass _Holder:\n"
            "    def __init__(self, body: BytesIO):\n        self.body = body\n",
            True,
            True,
            "",
        ),
        "path-parameter": (
            "from pathlib import Path\n\n\nclass _Holder:\n"
            "    def __init__(self, source: Path):\n        self.source = source\n",
            True,
            False,
            "A DIFFERENCE OF SUBJECT, NOT OF COVERAGE, and the only one left. The "
            "reach guard asks whether a class in the TEST package holds anything "
            "personal-data bearing, and a real save path is one - it is what its "
            "whole guard is about. This module asks whether an attribute of a "
            "SHIPPED save module holds save BYTES, which a path is not. Teaching "
            "this walk to report paths would make its own callers wrong: the "
            "rendering grade built on it looks for a retained BUFFER reaching a "
            "repr, and a path reaching one is a different finding with a "
            "different mitigation.",
        ),
        "fully-unannotated": (
            "class _Holder:\n    def __init__(self, body):\n        self.body = body\n",
            False,
            False,
            "",
        ),
        "unrelated-scalar": (
            "class _Holder:\n    def __init__(self, count: int):\n        self.count = count\n",
            False,
            False,
            "",
        ),
    }
)


def test_the_two_walks_over_held_bytes_differ_only_where_recorded() -> None:
    """CS-494 - two walks over one kind of thing, with the difference graded.

    WHAT WAS WRONG. ``reach_guard._bound_parameter_annotations`` and
    :func:`_retained_body_attributes` both read which attributes come to hold
    the decompressed world, and they disagreed in six ways that existed only in
    prose. Two hand-maintained walks over one kind of thing is the drift
    ``_FILESYSTEM_PRIMITIVES`` was unified to prevent, recreated inside the fix
    for CS-491 and found by the refutation pass on it. Neither walk could see
    the disagreement, because they grade different files.

    THEY ARE NOT MERGED, AND THAT IS THE ANSWER RATHER THAN A COMPROMISE. They
    answer different questions - one about personal data in the TEST package,
    one about save bytes in the SHIPPED save modules - and return different
    things. Merging them would make one of the two callers wrong. What was
    genuinely broken was the coverage difference, and that is closed: five of
    the six disagreements went away when this module's walk gained the tuple
    target, the property accessor and the bytes-LIKE vocabulary its sibling
    already had. **Measured before that widening: it adds nothing on the shipped
    save modules**, so it is a grade that starts catching things rather than one
    that reports what was already known.

    THE SURVIVING DIFFERENCE IS RECORDED WITH ITS REASON, and the reason is
    asserted present. A row that differs and explains nothing fails here, and so
    does a row that agrees and carries an explanation - a stale reason for a
    difference that no longer exists is the shape CS-471 shipped eight of.

    IT NEEDS NO SAVE LIBRARY. Every subject is a synthetic source in this file.
    """
    disagreements: dict[str, tuple[bool, bool]] = {}
    unexplained: list[str] = []
    stale: list[str] = []

    for label, (source, wraps, retains, reason) in _HELD_BYTES_SHAPES.items():
        tree = ast.parse(source)
        actual_wraps = bool(reach_guard._body_wrapping_classes(tree))  # noqa: SLF001
        actual_retains = bool(_retained_body_attributes(tree))

        assert (actual_wraps, actual_retains) == (wraps, retains), (
            f"{label}: the walks now report {(actual_wraps, actual_retains)} and this "
            f"record says {(wraps, retains)}. One of them changed - update the record "
            "with the reason, or restore the coverage."
        )
        if wraps != retains:
            disagreements[label] = (wraps, retains)
            if not reason.strip():
                unexplained.append(label)
        elif reason.strip():
            stale.append(label)

    assert not unexplained, (
        f"these shapes are reported by one walk and not the other with no reason "
        f"recorded: {unexplained}. A difference nobody wrote down is the drift this "
        "record exists to stop."
    )
    assert not stale, (
        f"these shapes agree and still carry a reason for differing: {stale}. A reason "
        "that outlives the difference it described reads as a live constraint and holds "
        "nothing."
    )

    # NON-VACUITY, all three ways. A record where nothing differs would satisfy
    # the assertions above while grading no difference at all; one where nothing
    # agrees would mean the two walks share no subject and comparing them says
    # nothing; and one where nothing is flagged would pass for two walks that
    # report nothing whatever.
    assert disagreements, (
        "the two walks agree on every shape here, so this record grades no difference. "
        "Either they were unified - in which case delete this - or the corpus stopped "
        "covering the shapes where they part."
    )
    assert any(wraps and retains for _s, wraps, retains, _r in _HELD_BYTES_SHAPES.values()), (
        "no shape is reported by both walks, so they share no subject and comparing "
        "them grades nothing"
    )
    assert any(
        not wraps and not retains for _s, wraps, retains, _r in _HELD_BYTES_SHAPES.values()
    ), "no shape is refused by both walks, so neither is shown to refuse anything"


def _reaches_a_rendering(node: ast.AST, attributes: frozenset[str]) -> bool:
    """Whether an expression lets one of the named attributes reach a rendering.

    ``len(...)`` IS NOT A RENDERING and is not descended into. ``usmap.py``
    raises with ``actual=max(len(self._data) - start, 0)``, which reports a
    COUNT and cannot disclose a byte; treating the mention as a render would
    report a leak that provably is not one. Excluding it is the equivalent-mutant
    distinction from memory/test-quality-failure-classes.md rather than a
    weakening - the splices in
    ``test_each_absence_checker_rejects_the_violation_it_describes`` still go
    red, because they pass the attribute itself.

    Args:
        node: The expression to inspect.
        attributes: Bare attribute names that hold save bytes.

    Returns:
        True when one of them is reachable as a value.
    """
    if isinstance(node, ast.Call):
        func = node.func
        called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if called == "len":
            return False
    if isinstance(node, ast.Attribute) and node.attr in attributes:
        return True
    return any(_reaches_a_rendering(child, attributes) for child in ast.iter_child_nodes(node))


def _rendered_retained_bytes(tree: ast.Module) -> list[str]:
    """Violations of :data:`_MITIGATION_RETAINED_BYTES_NEVER_RENDERED`.

    The needles are DERIVED from :func:`_retained_body_attributes` rather than
    written down, so the check cannot describe a buffer the module no longer
    has, and a second retained attribute is covered the day it appears.

    Args:
        tree: The parsed module.

    Returns:
        One label per rendering site, plus the vacuity report when the module
        retains nothing at all and should be declaring a different kind.
    """
    attributes = frozenset(name.split(".", 1)[1] for name in _retained_body_attributes(tree))
    if not attributes:
        return [
            "nothing in this module holds save bytes, so this kind grades nothing here; "
            f"declare {_MITIGATION_RECORDS_RETAIN_NO_BYTES!r} instead"
        ]

    renderers = {"repr", "str", "ascii", "format", "hex"}
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            if node.exc is not None and _reaches_a_rendering(node.exc, attributes):
                found.append(f"line {node.lineno} raises naming a retained buffer")
        elif isinstance(node, ast.JoinedStr):
            if _reaches_a_rendering(node, attributes):
                found.append(f"line {node.lineno} interpolates a retained buffer")
        elif isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if called in renderers and any(
                _reaches_a_rendering(arg, attributes) for arg in node.args
            ):
                found.append(f"line {node.lineno} passes a retained buffer to {called}()")
        elif (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name in {"__repr__", "__str__"}
            and _reaches_a_rendering(node, attributes)
        ):
            found.append(f"line {node.lineno} {node.name} renders a retained buffer")
    return sorted(set(found))


def _raises_naming_a_path(tree: ast.Module) -> list[str]:
    """Violations of :data:`_MITIGATION_PATH_IS_NEVER_RAISED`.

    The needles are DERIVED from the module's own signatures - every parameter
    it annotates as a ``Path`` - rather than written down, so the check cannot
    drift from the names it is about. A module that renames its path parameter
    is still checked; a module that adds a second one is checked on that too.

    Args:
        tree: The parsed module.

    Returns:
        The unparsed raise expressions that mention a path-annotated name.
    """
    needles = {
        node.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.arg)
        and node.annotation is not None
        and "Path" in ast.unparse(node.annotation)
    }
    if not needles:
        return []
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        mentioned = {
            inner.id for inner in ast.walk(node.exc) if isinstance(inner, ast.Name)
        } & needles
        if mentioned:
            found.append(f"line {node.lineno} raises naming {sorted(mentioned)}")
    return found


#: Kind to the checker that decides whether it holds. Each returns the
#: VIOLATIONS it found, so an empty list means the mitigation holds.
_MITIGATION_CHECKERS: Final = MappingProxyType(
    {
        _MITIGATION_NO_CODE: _defines_no_code,
        _MITIGATION_NO_PATH: _path_reaches,
        _MITIGATION_RECORDS_RETAIN_NO_BYTES: _retained_bytes_fields,
        _MITIGATION_RETAINED_BYTES_NEVER_RENDERED: _rendered_retained_bytes,
        _MITIGATION_PATH_IS_NEVER_RAISED: _raises_naming_a_path,
    }
)

_MITIGATION_KINDS: Final = frozenset(_MITIGATION_CHECKERS)

#: Every scanned module that calls NO redactor, to the mitigation kinds that
#: make that correct there and the reason each is the right answer FOR THAT
#: MODULE. This is the shipped data CS-423 asks for, in place of a skip and in
#: place of a comment: a comment cannot be asserted and cannot go red.
_ABSENCE_MITIGATIONS: Final = MappingProxyType(
    {
        "__init__.py": (
            (_MITIGATION_NO_CODE,),
            "a re-export surface with no statements of its own, so there is no "
            "frame, no message and no repr in it that could render anything",
        ),
        "chunks.py": (
            (_MITIGATION_NO_PATH, _MITIGATION_RETAINED_BYTES_NEVER_RENDERED),
            "it works on a blob handed to it by a caller and never learns where "
            "that blob came from. It DOES hold save bytes - DecompressedBody."
            "payload is the decompressed body and is its whole purpose - so the "
            "records kind is unavailable to it and would be a false claim. What "
            "it can be held to is that the buffer it holds reaches no raise, no "
            "f-string and no repr, and that is graded",
        ),
        "objects.py": (
            (
                _MITIGATION_NO_PATH,
                _MITIGATION_RECORDS_RETAIN_NO_BYTES,
                _MITIGATION_RETAINED_BYTES_NEVER_RENDERED,
            ),
            "THE MODULE CS-423 IS ABOUT, and the one CS-433 caught being graded "
            "against a claim it does not satisfy. No path reaches it, so the "
            "redactor - which strips paths, account names and account ids - "
            "would have nothing to strip. Its RECORDS hold no save bytes: every "
            "one points into the caller's buffer by offset and length, so no "
            "field of any type it returns is bytes. THE MODULE ITSELF DOES HOLD "
            "THE BODY - _Cursor.__init__ binds it to _data and keeps it for the "
            "length of the parse - which is why the third kind is declared and "
            "the second is worded about records only. An earlier revision "
            "claimed the module retained none of it, which was false and green. "
            "The decoded values it also holds live behind hand-written reprs "
            "that withhold every string, which is a separate guarantee graded "
            "by tests/save/test_properties.py rather than restated here",
        ),
        "world.py": (
            (_MITIGATION_PATH_IS_NEVER_RAISED,),
            "the one of the four that DOES take a path, so no-path-reaches-it "
            "is unavailable to it and would be a false claim. It refuses by "
            "raising WorldLoadError(stage constant, exception type name) and "
            "delegates every path-handling step to workdir, which redacts",
        ),
    }
)


def _redact_call_lines(source: str) -> list[int]:
    """Find every line that actually CALLS a redactor, prose excluded.

    An AST walk, not a text search: every module in this package discusses
    redaction at length in its docstring, and a text sweep would report those
    mentions as calls.

    Args:
        source: Module source text.

    Returns:
        The line numbers of real call sites.
    """
    return [
        getattr(node, "lineno", 0)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and _called_name(node) == "redact"
    ]


@pytest.mark.parametrize("relative", SAVE_SOURCES)
def test_every_redact_call_resolves_to_the_locate_redactor(relative: str) -> None:
    """A module that CALLS redact must import it from clockspeed.data.locate.

    Both import spellings are accepted because both are in use and both are
    correct: ``from clockspeed.data.locate import redact`` in header.py and
    usmap.py, and ``from clockspeed.data import locate`` then
    ``locate.redact(...)`` in workdir.py.

    Stated as a conditional rather than as "every module imports redact",
    because that stronger claim is FALSE and asserting it would be a test named
    for something it does not check: chunks.py imports nothing from clockspeed
    at all, and objects.py and world.py mention redaction only in prose.
    """
    source = (SAVE_PACKAGE / relative).read_text(encoding="utf-8")
    if not _redact_call_lines(source):
        # NOT A SKIP ANY MORE, AND THAT IS CS-423. This line used to read
        # `pytest.skip(f"clockspeed/save/{relative} calls no redactor")`, and it
        # fired on FOUR of the seven scanned modules - including the one with
        # the largest leak surface in the package. A privacy oracle that skips
        # is the unrun-gate class from memory/test-quality-failure-classes.md:
        # a skipped suite is not a passing suite, and the skip was visible in
        # every single run for as long as it existed. The module is handed to
        # the absence grader below instead, which is where the real work is.
        assert relative in _ABSENCE_MITIGATIONS, (
            f"clockspeed/save/{relative} calls no redactor and declares no mitigation "
            "either, so nothing in this suite grades how it avoids rendering personal "
            f"data; add it to _ABSENCE_MITIGATIONS with a kind from {sorted(_MITIGATION_KINDS)}"
        )
        return

    assert relative not in _ABSENCE_MITIGATIONS, (
        f"clockspeed/save/{relative} declares an absence mitigation but now calls "
        "redact(), so the declaration describes code that no longer exists"
    )
    imports_directly = "from clockspeed.data.locate import" in source and "redact" in source
    imports_module = "from clockspeed.data import locate" in source
    assert imports_directly or imports_module, (
        f"clockspeed/save/{relative} calls redact() without importing it from "
        "clockspeed.data.locate, so it is calling something else"
    )


@pytest.mark.parametrize("relative", sorted(_ABSENCE_MITIGATIONS))
def test_every_declared_absence_mitigation_actually_holds(relative: str) -> None:
    """CS-423 - the four modules that call no redactor are GRADED, not skipped.

    This is the assertion that replaces ``SKIPPED ... calls no redactor``. Each
    module's declared kinds are run against its SHIPPED source, so the
    declaration is a claim about code rather than a note about intent.

    IT CAN GO RED, WHICH IS THE POINT. For ``objects.py`` the claim is
    absence-of-value, and it fails the moment the module starts holding one: add
    a ``bytes`` field to any of its dataclasses and
    ``retains-no-save-bytes`` reports it; give any function a ``Path``
    parameter and ``no-path-reaches-it`` reports that.
    """
    kinds, reason = _ABSENCE_MITIGATIONS[relative]
    assert reason.strip(), f"{relative} declares a mitigation with no reason"
    assert kinds, f"{relative} declares no mitigation kind at all"
    unknown = sorted(set(kinds) - _MITIGATION_KINDS)
    assert not unknown, f"{relative} declares unknown mitigation kinds {unknown}"

    tree = ast.parse((SAVE_PACKAGE / relative).read_text(encoding="utf-8"))
    for kind in kinds:
        violations = _MITIGATION_CHECKERS[kind](tree)
        assert not violations, (
            f"clockspeed/save/{relative} declares the mitigation {kind!r} and no longer "
            f"satisfies it: {violations}. Either the module changed and its declared "
            "mitigation is now false, or the declaration was wrong when it was written"
        )


def test_the_module_graded_for_absence_of_value_does_hold_the_body() -> None:
    """CS-433 - the reality the retention grade has to be written against.

    ``objects.py`` binds the whole decompressed body to an attribute and keeps
    it for the length of the parse. The grade shipped beside that fact said the
    module retains none of it, and stayed green because the checker read
    ``@dataclass`` annotated fields only and the binding is an ordinary
    assignment in an ordinary class.

    This test pins the FACT rather than the grade, so the two cannot drift
    apart again: if the body stops being held the assertion goes red and the
    declaration has to be revisited, and while it is held no wording that denies
    it can pass.
    """
    tree = ast.parse((SAVE_PACKAGE / "objects.py").read_text(encoding="utf-8"))
    held = _retained_body_attributes(tree)
    assert held, (
        "clockspeed/save/objects.py binds the decompressed body to an instance "
        "attribute, and the retention checker reports nothing - so any grade "
        "built on it is asserting an absence the module does not have"
    )

    # The two halves of the split, asserted against each other on the module
    # that forced it. The narrow checker is SILENT here and the broad one is
    # not, which is exactly the gap the old single kind was worded across.
    assert not _retained_bytes_fields(tree), (
        "a record in objects.py now carries a bytes field, so records-retain-no-"
        f"save-bytes is no longer true of it: {_retained_bytes_fields(tree)}"
    )
    assert _MITIGATION_RECORDS_RETAIN_NO_BYTES in _ABSENCE_MITIGATIONS["objects.py"][0]
    assert _MITIGATION_RETAINED_BYTES_NEVER_RENDERED in _ABSENCE_MITIGATIONS["objects.py"][0]


def test_the_declared_absences_are_exactly_the_modules_that_call_no_redactor() -> None:
    """The declaration set is DERIVED-CHECKED against the scanned set, both ways.

    Both directions matter and they fail differently. A module that stops
    calling the redactor and is not declared would silently fall out of every
    grade - the original CS-423 defect - and a declaration that outlives the
    module it describes is a note about code that no longer exists.
    """
    silent = {
        relative
        for relative in SAVE_SOURCES
        if not _redact_call_lines((SAVE_PACKAGE / relative).read_text(encoding="utf-8"))
    }

    assert silent == frozenset(_ABSENCE_MITIGATIONS), (
        f"undeclared modules that call no redactor: "
        f"{sorted(silent - frozenset(_ABSENCE_MITIGATIONS))}; declarations that no "
        f"longer describe a silent module: {sorted(frozenset(_ABSENCE_MITIGATIONS) - silent)}"
    )
    # NON-VACUITY. If every module called the redactor this test would pass by
    # comparing two empty sets, and so would every grade above it.
    assert silent, "no module calls the redactor-free path, so the absence graders are vacuous"


#: Kind to a source fragment that violates exactly that kind.
#:
#: NOT THE PARAMETRISATION - the parametrisation is derived from
#: :data:`_MITIGATION_KINDS`, and this is looked up inside the test. That
#: ordering is the whole point. When the cases were listed here directly, a kind
#: could be added to the registry, declared by a module and graded by a checker
#: that returned an empty list, and nothing would parametrize over it: the suite
#: stayed green and the new kind was never forced to prove it could go red. A
#: kind with no entry here now produces a FAILING case rather than no case.
_MITIGATION_VIOLATION_SPLICES: Final = MappingProxyType(
    {
        _MITIGATION_NO_CODE: "\n\ndef _spliced_surface():\n    return 1\n",
        _MITIGATION_NO_PATH: (
            "\n\nfrom pathlib import Path\n\n\ndef _spliced(p: Path):\n    return p.read_bytes()\n"
        ),
        _MITIGATION_RECORDS_RETAIN_NO_BYTES: (
            "\n\n@dataclass(frozen=True)\nclass _Spliced:\n    payload: bytes\n"
        ),
        # Self-contained: it BRINGS its own retention rather than naming a
        # buffer the host module happens to have, so the same fragment forces
        # every module that could ever declare this kind.
        _MITIGATION_RETAINED_BYTES_NEVER_RENDERED: (
            "\n\nclass _SplicedRenderer:\n"
            "    def __init__(self, blob: bytes) -> None:\n"
            "        self._kept = blob\n"
            "\n"
            "    def boom(self):\n"
            "        raise ValueError(self._kept)\n"
        ),
        _MITIGATION_PATH_IS_NEVER_RAISED: (
            "\n\ndef _spliced(path: Path):\n    raise ValueError(path)\n"
        ),
    }
)


@pytest.mark.parametrize("kind", sorted(_MITIGATION_KINDS))
def test_each_absence_checker_rejects_the_violation_it_describes(kind: str) -> None:
    """THE CHECKERS' POWER, forced rather than asserted about.

    A checker that returned an empty list on everything would pass every grade
    above and would be strictly worse than the skip it replaced, because it
    would look like a grade. Each violation is spliced into a copy of the
    module that declares that kind, in memory, and the checker must report it.

    THE CASES ARE DERIVED FROM THE REGISTRY, which is CS-433's repair here: the
    list used to be written out beside this decorator, so a fifth kind could
    join ``_MITIGATION_CHECKERS`` and be graded by nothing while every test in
    the file stayed green. Parametrizing over the registry makes an unchecked
    kind impossible to add quietly - it arrives as a red case.

    The positive control runs in the same test: the same checker on the
    UNSPLICED source of the same module must stay clean, so a red above is the
    splice rather than a checker that rejects everything.
    """
    assert kind in _MITIGATION_VIOLATION_SPLICES, (
        f"the mitigation kind {kind!r} is in the registry and no fragment here violates it, "
        "so nothing forces its checker to prove it can go red; add one to "
        "_MITIGATION_VIOLATION_SPLICES"
    )
    declaring = [name for name, (kinds, _reason) in _ABSENCE_MITIGATIONS.items() if kind in kinds]
    assert declaring, (
        f"the mitigation kind {kind!r} is in the registry and no module declares it, so it "
        "grades nothing shipped; either a module should be claiming it or it should go"
    )

    splice = _MITIGATION_VIOLATION_SPLICES[kind]
    checker = _MITIGATION_CHECKERS[kind]

    # Every declaring module, not just the first. Two modules claim the render
    # kind, and grading one of them would leave the other's positive control
    # unmeasured.
    for relative in declaring:
        source = (SAVE_PACKAGE / relative).read_text(encoding="utf-8")
        assert not checker(ast.parse(source)), (
            f"the positive control failed: {relative} does not satisfy {kind!r} unspliced"
        )
        assert checker(ast.parse(source + splice)), (
            f"the {kind!r} checker passed {relative} carrying the exact violation it names, "
            "so it grades nothing"
        )


def test_the_redactor_call_finder_separates_calls_from_prose() -> None:
    """COMPANION: the finder catches a real call and ignores a docstring mention.

    Both directions, because the negative is the one that matters: every module
    in this package names ``redact`` in prose, so a finder that could not tell
    the two apart would report six call sites where there are three.
    """
    assert _redact_call_lines("def f(p):\n    return redact(p)\n") == [2]
    assert _redact_call_lines("def f(p):\n    return locate.redact(p)\n") == [2]
    assert _redact_call_lines('"""Paths go through redact() before rendering."""\n') == []
    assert _redact_call_lines("# every path is passed to redact(path) first\n") == []

    # The definition finder matches on the SUBSTRING "redact", deliberately.
    # A fork of the redactor would not be named `redact` - it would be
    # `_redact_path`, `redactor` or `redact_for_log`, which is exactly how a
    # second copy gets in. Matching the substring costs a possible false
    # positive on an unrelated name; missing a fork costs a leak.
    assert _redact_definitions("def redact(path):\n    return path\n") == ["redact"]
    assert _redact_definitions("def _redact_path(p):\n    return p\n") == ["_redact_path"]
    assert _redact_definitions("redactor = None\n") == ["redactor"]
    assert _redact_definitions("my_redact = None\n") == ["my_redact"]
    # An IMPORT is not a definition. This is the direction that matters: every
    # module that legitimately uses the shared redactor imports it, and a
    # finder that flagged the import would make the whole check unusable.
    assert _redact_definitions("from clockspeed.data.locate import redact\n") == []
    assert _redact_definitions("from clockspeed.data import locate\n") == []
    assert _redact_definitions("def f(p):\n    return redact(p)\n") == []


# ---------------------------------------------------------------------------
# CS-429 - the three real-library helpers here are CONTAINED, and every site is
# GRADED
#
# Three helpers in this module reach the operator's save library, and until this
# section existed nothing forced a failure through any of them. Which ones they
# are is DERIVED rather than counted here - ``test_every_library_reaching_
# function_here_is_declared`` reads this module's own AST - so adding one cannot
# falsify this paragraph.
#
# EVERY LEAK BELOW WAS MEASURED UNDER `-q` ALONE on a machine with a real
# library, by forcing one failure and probing the output for markers. Six
# markers were probed: the Windows account name, the account directory NAME
# (which is the platform account id), the save root, the account directory path,
# the save filename stem and the full save path.
#
#   THE DISCOVERY. ``locate.resolve_save_root``, ``locate.resolve_account_dir``
#   and the save glob sat outside every ``try`` in two of the three helpers.
#   Forcing the glob to raise rendered FOUR of the six markers, the account
#   directory among them (CLAUDE.md section 2, non-negotiable 3).
#
#   THE READ. ``header.read_header(path)`` sat under ``except (HeaderError,
#   OSError)`` and ``world.load_world(path)`` under ``except Exception``. Both
#   name the failures somebody predicted. Forcing a ``MemoryError`` through the
#   first rendered ALL SIX markers; forcing a ``SystemExit`` through the second
#   rendered ALL SIX as well, because ``SystemExit`` is a ``BaseException`` and
#   ``except Exception`` does not hold one.
#
#   TWO TYPES FORCE IT, AND ONE HANDLER SHAPE DOES NOT HOLD BOTH. That
#   ``SystemExit`` result is the whole reason every read grader below is
#   parametrized over both forced failures rather than one. ``KeyboardInterrupt``
#   is deliberately left free to unwind so that a walk over a real library stays
#   abortable; it renders nothing without ``--full-trace``.
#
# EVERY SUBJECT BELOW IS SYNTHETIC. The graders run on a machine with no game
# installed and no save library, never put a real path into the frame under
# test, and reduce every assertion to a type NAME, an integer or a boolean
# first - a test that grades a leak must not be the leak.
# ---------------------------------------------------------------------------

#: The helpers whose containment the graders below force a failure through.
_GRADED_LIBRARY_REACH: Final = MappingProxyType(
    {
        "_real_save_or_skip": "wraps workdir.latest_save",
        "_newest_real_saves_of_a_measured_pair_or_skip": (
            "reads the header of every save in the library"
        ),
        "_load_every_real_save": "loads every save in the library",
        "_body_partial_scalars_or_skip": "reads the newest save whole",
        "_measured_pair_scalars_or_skip": (
            "loads the newest loadable real save through world.load_newest_world"
        ),
    }
)

#: Reaches or touches a primitive without being a grader-able library helper,
#: name to why. Asserted still reaching, so none outlives its reason.
_EXEMPT_LIBRARY_REACH: Final = MappingProxyType(
    {
        reach_guard.MODULE_SCOPE_REACH: (
            "Path(__file__).resolve() at module scope, building this repo's "
            "own root and this module's own path as constants. It resolves a "
            "tracked source file, never a save directory and never the "
            "account directory"
        ),
        "_fingerprint": (
            "reads bytes under a pretend save root supplied by the caller as "
            "tmp_path, never a discovered save directory"
        ),
        "test_the_fingerprint_detects_a_single_changed_byte": (
            "a test rather than a helper, and its read_bytes is on a synthetic "
            "save written into tmp_path"
        ),
        # The three below entered the flagged set when CS-433 widened the reach
        # vocabulary to the path-bearing primitives. None of them was newly
        # written and none reaches the library; they are the visible price of a
        # guard keyed on names rather than on targets, which is the trade the
        # keying note in test_properties records and prefers.
        "_relative_python_sources": (
            "rglob and resolve over a SOURCE root handed in by the caller - the "
            "save package or the repo - listing .py files. No discovery "
            "primitive feeds it and it never sees a save directory"
        ),
        "_run_audited_child": (
            "resolves the PRETEND save root that _pretend_save_root built under "
            "tmp_path, to pass the child both Windows spellings of it. The "
            "resolve is the point of the helper and the path is synthetic"
        ),
        "test_the_measured_audit_event_shapes_still_hold": (
            "a test rather than a helper, and its open and os.open calls are on "
            "files inside a tempfile.TemporaryDirectory, made solely to force "
            "the CPython audit events this module's write scanner reasons about"
        ),
        "test_the_library_sweep_leaves_its_copies_off_the_repo": (
            "a test rather than a helper. Its rglob runs over exactly two roots "
            "and neither is discovered: this repo's own work directory, built "
            "from the REPO_ROOT constant, and the redirected work root the "
            "isolated_work_root fixture placed under tmp_path. It counts the "
            "matches and binds no path, so no save name reaches a frame"
        ),
        "_child_units": (
            "glob, resolve and read_text over SAVE_TESTS, this repo's own "
            "tests/save directory built from the REPO_ROOT constant, listing "
            "test modules and parsing their source. No discovery primitive "
            "feeds it and it never sees a save directory"
        ),
    }
)


def _assert_contained_outcome(label: str, expected: str, call: Callable[[], object]) -> None:
    """Assert a helper ended in the named CONTAINED outcome rather than unwinding.

    Both operands are exception type NAMES, so a failure here renders two class
    names and the label and nothing else. That is deliberate: the helpers under
    test hold a save path, and a grader that rendered one would be the leak it
    grades.

    Args:
        label: What to call the helper in a failure message.
        expected: The type name of the outcome the containment must produce.
        call: The helper.
    """
    escaped, _value = test_properties._contained_call(call)  # noqa: SLF001
    assert escaped == expected, (
        f"the {label} ended in {escaped} rather than {expected}, so the failure was not "
        "contained and every frame it unwound through held a save path"
    )


def test_every_library_reaching_function_here_is_declared() -> None:
    """The reach guard, keyed on the RISKY primitives rather than the safe route.

    Keyed that way because the inverted alternative has already shipped in this
    package once: a guard keyed on the CONTAINED entry point detects safe
    helpers and is blind to unsafe ones, so every assertion in it stays true
    while the module leaks. The guard is owned by ``reach_guard`` and consumed
    here, so the sibling modules share one implementation rather than several
    transcriptions.
    """
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


def test_no_test_in_this_module_is_gutted_to_an_early_return() -> None:
    """CS-433 - the graded absences cannot be quietly emptied.

    Imported rather than transcribed, like the reach guard beside it. The kinds
    above are the file's whole contribution to CS-423, and a test cut short
    before its assertions passes exactly as an absent one would.
    """
    reach_guard._assert_no_test_is_gutted(Path(__file__))  # noqa: SLF001


def test_the_guard_catches_a_spliced_uncontained_helper(tmp_path: Path) -> None:
    """The guard's POWER, forced rather than asserted about.

    The splice is this module's OWN pre-repair shape - the locators and the glob
    outside every ``try``, under a catch naming two families - wired in exactly
    as ``_newest_real_saves_of_a_measured_pair_or_skip`` carried it. Run against a COPY
    in ``tmp_path``, so nothing tracked is mutated and no restore is needed.
    """
    spliced = tmp_path / "spliced.py"
    spliced.write_text(
        Path(__file__).read_text(encoding="utf-8") + "\n\ndef _spliced_uncontained_helper():\n"
        '    """A helper carrying the known-bad shape."""\n'
        "    root = locate.resolve_save_root()\n"
        "    account = locate.resolve_account_dir(root)\n"
        '    for path in sorted(account.glob("*.sav")):\n'
        "        try:\n"
        "            return header.read_header(path)\n"
        "        except (OSError, header.HeaderError):\n"
        "            continue\n"
        "    return None\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as caught:
        reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
            spliced, graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
        )
    assert "_spliced_uncontained_helper" in str(caught.value)

    # The positive control: the same guard on the unspliced source passes, so
    # the red above is the splice rather than the guard rejecting everything.
    reach_guard._assert_library_reach_is_declared(  # noqa: SLF001
        Path(__file__), graded=_GRADED_LIBRARY_REACH, exempt=_EXEMPT_LIBRARY_REACH
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_newest_save_lookup_does_not_unwind_through_clause_one(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``workdir.latest_save`` resolves the account directory and sat outside any ``try``.

    Its own docstring promises it never raises for an absent, empty or
    unresolvable directory - a promise about those three states and not about
    every state, and this module cannot rest a privacy claim on another
    module's promise.
    """
    monkeypatch.setattr(workdir, "latest_save", raiser)
    _assert_contained_outcome(
        "newest-save helper", pytest.skip.Exception.__name__, _real_save_or_skip
    )
    _assert_contained_outcome(
        "body-partial helper", pytest.skip.Exception.__name__, _body_partial_scalars_or_skip
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_root_lookup_does_not_unwind_through_either_library_walk(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The first of the three discovery calls both library walks made bare."""
    monkeypatch.setattr(locate, "resolve_save_root", raiser)
    _assert_contained_outcome(
        "measured-pair finder",
        pytest.skip.Exception.__name__,
        _newest_real_saves_of_a_measured_pair_or_skip,
    )
    test_properties._assert_sweep_declines("library sweep", _load_every_real_save)  # noqa: SLF001


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_account_directory_lookup_does_not_unwind_through_either_library_walk(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The second, and the one whose frame holds the platform account id."""
    monkeypatch.setattr(locate, "resolve_save_root", lambda: Path("synthetic-root"))
    monkeypatch.setattr(locate, "resolve_account_dir", raiser)
    _assert_contained_outcome(
        "measured-pair finder",
        pytest.skip.Exception.__name__,
        _newest_real_saves_of_a_measured_pair_or_skip,
    )
    test_properties._assert_sweep_declines("library sweep", _load_every_real_save)  # noqa: SLF001


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_DISCOVERY_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_a_failing_save_glob_does_not_unwind_through_either_library_walk(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """The third - it was in the ``for`` statement itself, and it MEASURED a leak.

    Forcing this one rendered the account directory itself, the save root and
    the Windows account name under ``-q`` alone, through both walks.
    """
    monkeypatch.setattr(Path, "glob", raiser)
    _assert_contained_outcome(
        "measured-pair finder",
        pytest.skip.Exception.__name__,
        _newest_real_saves_of_a_measured_pair_or_skip,
    )
    test_properties._assert_sweep_declines("library sweep", _load_every_real_save)  # noqa: SLF001


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_header_read_failure_does_not_unwind_through_the_measured_pair_finder(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``except (HeaderError, OSError)`` names the two failures somebody predicted.

    ``header.read_header(path)`` takes the save path as its ARGUMENT, so any
    other type renders an absolute path under a home directory the moment pytest
    unwinds the call. Measured: a forced ``MemoryError`` here rendered all six
    probed markers.

    The finder has nowhere to record a type name - it returns a path or skips -
    so containment here means skipping.
    """
    monkeypatch.setattr(
        test_properties,
        "_library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(header, "read_header", raiser)
    _assert_contained_outcome(
        "measured-pair finder",
        pytest.skip.Exception.__name__,
        _newest_real_saves_of_a_measured_pair_or_skip,
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_load_failure_does_not_unwind_through_the_library_sweep(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``except Exception`` held the ``MemoryError`` and leaked on the ``SystemExit``.

    This is the site that proves the parametrization earns its keep rather than
    doubling the count: the sweep's catch was ``except Exception``, so the first
    forced failure was already contained and only the second one was red. A
    grader forcing ``MemoryError`` alone would have passed on leaking code.
    """
    monkeypatch.setattr(
        test_properties,
        "_library_save_paths",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(world, "load_world", raiser)
    escaped, value = test_properties._contained_call(_load_every_real_save)  # noqa: SLF001
    assert escaped is None, (
        f"{escaped} escaped the library sweep instead of being reduced to a type name "
        "inside it, and the frame it unwound through held the save path"
    )
    # Reduced to scalars before the assertion, so a failure renders integers and
    # exception type names and nothing else - never a path and never a save.
    assert isinstance(value, tuple), (
        "the library sweep declined instead of recording the contained failure"
    )
    assert value == (1, 0, (_forced,)), (
        f"the library sweep reported {value} rather than the one contained {_forced}"
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_read_failure_does_not_unwind_through_the_body_partial(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``source.read_bytes()`` sat under a catch naming three predicted families.

    Forced through ``header.read_header`` rather than through ``read_bytes``
    because ``read_header`` runs first and opens the file itself: a synthetic
    path makes it raise before the ``read_bytes`` line is ever reached, so
    patching ``read_bytes`` alone would grade nothing.
    """
    monkeypatch.setattr(workdir, "latest_save", lambda: test_properties._SYNTHETIC_SAVE)  # noqa: SLF001
    monkeypatch.setattr(header, "read_header", raiser)
    escaped, value = test_properties._contained_call(_body_partial_scalars_or_skip)  # noqa: SLF001
    assert escaped is None, (
        f"{escaped} escaped the body-partial helper instead of being reduced to a type "
        "name inside it, and the frame it unwound through held the save path"
    )
    reported = getattr(value, "failure", None)
    assert reported == _forced, (
        f"the body-partial helper reported {reported} rather than the one contained {_forced}"
    )


@pytest.mark.parametrize(
    ("_forced", "raiser"),
    test_properties._FORCED_READ_FAILURES,  # noqa: SLF001
    ids=lambda value: value if isinstance(value, str) else "",
)
def test_an_unexpected_load_failure_does_not_unwind_through_the_measured_pair_load(
    monkeypatch: pytest.MonkeyPatch, _forced: str, raiser: Callable[..., object]
) -> None:
    """``except world.WorldLoadError`` is the narrowest catch of the three, and the widest gap.

    ``world.load_world(source)`` takes the save path as its ARGUMENT, so any
    type outside that one family renders an absolute path under a home
    directory the moment pytest unwinds the call.
    """
    monkeypatch.setattr(
        "tests.save.test_phase4_gate._newest_real_saves_of_a_measured_pair_or_skip",
        lambda: (test_properties._SYNTHETIC_SAVE,),  # noqa: SLF001
    )
    monkeypatch.setattr(world, "load_world", raiser)
    escaped, value = test_properties._contained_call(_measured_pair_scalars_or_skip)  # noqa: SLF001
    assert escaped is None, (
        f"{escaped} escaped the measured-pair loader instead of being reduced to a type "
        "name inside it, and the frame it unwound through held the save path"
    )
    reported = getattr(value, "failure", None)
    assert reported == _forced, (
        f"the measured-pair loader reported {reported} rather than the one contained {_forced}"
    )


# ===========================================================================
# CS-973 - the copies this module's real-save arms make land off the repo
#
# AT THE FOOT, AND THE PLACEMENT IS THE POINT. This module's Clause 1 section
# is where these two read, and putting them there is what the first attempt
# did - which moved `WRITER_WRITE_SURFACE` off line 2089 and broke the archive
# pin in `docs/item_notes/phase4.md` that anchors it. A block appended below
# every existing line moves none of them. Fixtures and tests are collected by
# name, so position costs nothing but the reading order.
# ===========================================================================


@pytest.fixture(autouse=True)
def isolated_work_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Send workdir's copies under tmp_path so no test writes into the repo.

    AUTOUSE, AND THAT IS THE POINT. ``world.load_world`` copies its subject
    through ``workdir.copy_for_read`` before it reads a byte, and the work root
    that copy lands in DEFAULTS TO ``<repo>/work``. Two arms in this module
    reached a real save without redirecting it, and the library sweep below
    reaches EVERY save the operator has - so a plain run of this file deposited
    one ``.copy.sav`` per real save into the tracked tree, each one a real save
    carrying the account id and the world name (non-negotiables 11 and 12).
    That was measured at 23 files, not theorised.

    Requesting it by name on the two arms that copy today would close those two
    and leave the NEXT arm that loads a real save to re-open the hole, which is
    how this one was opened. Autouse closes the module.

    The sibling fixture in ``tests/save/test_world.py`` is the same redirect for
    the same reason; this module could not borrow it because a fixture defined
    in a test module is private to that module.

    Args:
        monkeypatch: Restores the environment when the test ends.
        tmp_path: The per-test sandbox the work root is placed under.

    Returns:
        The redirected work root. Bound so an arm can assert copies landed in it.
    """
    root = tmp_path / "work-root"
    monkeypatch.setenv(workdir.ENV_WORK_ROOT, str(root))
    return root


def test_the_library_sweep_leaves_its_copies_off_the_repo(isolated_work_root: Path) -> None:
    """THE REGRESSION ARM for the copies this module used to deposit in the tree.

    ``world.load_world`` copies before it parses, so the sweep above writes one
    file per real save. Where they land is the whole subject here: under the
    redirected work root, and NOT in the repo's own ``work`` directory. The
    measured defect was 23 real saves copied into the tracked tree.

    THE REPO HALF IS A DELTA, NOT A CENSUS. Asserting the repo work directory is
    EMPTY would grade the machine rather than this run - a stray left by some
    earlier run would fail an arm that is innocent of it. What is asserted is
    that this test ADDED nothing there, which is the claim the fix actually
    makes and is true on a dirty machine as well as a clean one.

    THE FIRST ASSERTION IS THE VACUITY CONTROL. Every other assertion here
    passes when the sweep copied nothing at all, which is precisely the state a
    broken ``_load_every_real_save`` would present.

    COUNTS ONLY, AND THAT IS NOT STYLE. A copy is named after the save it came
    from, so a set of copy paths rendered into a pytest assertion line is a set
    of the operator's world names (non-negotiable 12). Nothing below binds a
    name.

    Args:
        isolated_work_root: The redirected root, requested by name rather than
            left to the autouse so the reader can see what is being graded.
    """
    repo_work = REPO_ROOT / workdir.WORK_DIR_NAME
    before = len(list(repo_work.rglob("*" + workdir.COPY_SUFFIX))) if repo_work.is_dir() else 0

    swept = _load_every_real_save()
    if swept is None:
        pytest.skip("no save library on this machine - there is nothing to copy")
    found, _loaded, _failures = swept

    after = len(list(repo_work.rglob("*" + workdir.COPY_SUFFIX))) if repo_work.is_dir() else 0
    copied = len(list(isolated_work_root.rglob("*" + workdir.COPY_SUFFIX)))

    assert copied > 0, "the sweep copied nothing, so this arm would pass over any work root"
    assert copied <= found, "more copies than saves swept - the redirect is not the only writer"
    assert after == before, f"the sweep added {after - before} copies to the repo work directory"
