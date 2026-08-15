"""The CS-400 phase 4 gate: the four acceptance clauses, graded honestly.

READ THIS BLOCK BEFORE CITING A GREEN RUN OF THIS FILE AS PROOF OF ANYTHING.
============================================================================
A green run of this module does NOT mean CS-400 may close. One of the four
acceptance clauses is blocked on work that has not been done, and this module
is written so that the blocked clause is visibly skipped rather than quietly
absent. The status of each clause, as this module measures it:

    CLAUSE 1  a real world parses ............................. PARTIAL
    CLAUSE 2  a corrupted save produces a clean error ......... MET
    CLAUSE 3  a truncated save produces a clean error ......... MET
    CLAUSE 4  the save directory is never opened for write .... MET

**CLAUSE 1 IS PARTIAL, AND PARTIAL IS NOT MET.** A real world DOES now parse end
to end through the single entry point - ``test_a_real_world_parses_end_to_end``
runs and asserts rather than skipping. It holds for ONE of the four real
(header version, save version) pairs.

The other three are refused BY DESIGN and cannot be read at all. A real body is
not an object table with a preamble in front of it: it is a LIST OF LEVELS, each
carrying its own record table, collectable list and payload section. CS-407
derived that layout for header 10 / save 36 and confirmed it on all three real
files of that pair, each landing on its exact final byte. The remaining pairs
raise ``UnsupportedBodyLayoutError`` eagerly, which is non-negotiable 7 working -
flagged and refused, never a silently wrong world.

So the test deliberately selects the newest save OF A MEASURED PAIR rather than
the newest save. Using ``latest_save`` alone would be a bug here: on a library
whose newest file is an unmeasured pair, the reader refuses it exactly as
specified and the test would fail while nothing was wrong.

CS-400 MUST NOT CLOSE ON THIS. Eleven of the fourteen saves on the machine this
was written against cannot be loaded, and CS-402 is separately unmet.

What IS provable against a real save today is asserted by
``test_a_real_save_reaches_the_body_partial``, and it is named a partial
because that is what it is: the save is FOUND, the header PARSES, its version
is supported, the token is the measured width, and the chunk walk yields a
non-empty payload over at least one chunk. The object walk is not attempted.
That test is skip-if-absent: CI has no save library, and a clause that cannot
be graded in CI is stated as such rather than implied to have passed.

**CS-402 IS NOT MET AND CANNOT BE MET HERE.** Three of the four save versions
in the operator's library parse. The fourth, save version 42, is REFUSED BY
DESIGN because its transform delta is unmeasured (CS-408), and
``objects.transform_delta(42)`` raises rather than interpolating a plausible
number from 36 and 60. ``test_the_loadable_version_set_is_three_of_four``
asserts that true shape - including the refusal - rather than a comfortable
"every fixture loads".

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
from dataclasses import dataclass
from pathlib import Path
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
from tests.save import synthetic

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
# Clause 1 - A REAL WORLD PARSES.  PARTIAL - met for ONE measured pair only.
# ===========================================================================


def _real_save_or_skip() -> Path:
    """Return the newest save in the operator's library, or skip.

    Returns:
        The save path. Never rendered into an assertion message - it sits under
        a home directory and carries both the account id and the world name.
    """
    source = workdir.latest_save()
    if source is None:
        pytest.skip("no save library on this machine - clause 1 is not gradeable here")
    return source


def _real_save_of_a_measured_pair_or_skip() -> Path:
    """Return the newest real save whose BODY LAYOUT this project has measured.

    ``latest_save`` alone is not enough and using it here would be a bug rather
    than a simplification: it returns the newest file, and on a library whose
    newest file is an UNMEASURED pair that save is refused by design. The test
    would then fail while the reader was behaving exactly as specified.

    Returns:
        The save path. NEVER rendered into an assertion message - it sits under
        a home directory and carries both the account id and the world name.
    """
    root = locate.resolve_save_root()
    account = locate.resolve_account_dir(root) if root is not None else None
    if account is None:
        pytest.skip("no save library on this machine - clause 1 is not gradeable here")
    candidates: list[tuple[float, Path]] = []
    for path in account.glob("*.sav"):
        try:
            parsed = header.read_header(path)
        except (header.HeaderError, OSError):
            continue
        if (parsed.header_version, parsed.save_version) in objects.MEASURED_BODY_LAYOUTS:
            candidates.append((path.stat().st_mtime, path))
    if not candidates:
        pytest.skip(
            "no save of a MEASURED body-layout pair on this machine - three of the four "
            "real pairs are still underived (CS-407), so clause 1 is not gradeable here"
        )
    return max(candidates)[1]


def test_a_real_world_parses_end_to_end() -> None:
    """CLAUSE 1 - MET for a measured body-layout pair, and only for one.

    This was skipped when the gate was written, because nothing could locate a
    real body's object table. CS-407 derived the levelled layout for header 10 /
    save 36 and CS-409 routed ``load_world`` to it, so the assertion is now real.

    READ THE LIMIT BEFORE CITING THIS AS CS-400 CLOSED. Three of the four real
    version pairs are STILL underived and are refused by design, and this test
    deliberately selects a save of a MEASURED pair rather than the newest file.
    Passing here means the seam works end to end on the pair it can read - not
    that the save reader reads saves.

    COUNTS ONLY. It binds derived scalars to locals and asserts on those; it
    renders no token, no map name, no instance name and no path. The load is
    GUARDED because pytest renders the ARGUMENTS of a failing frame, and the
    frame inside the reader holds the whole save.
    """
    source = _real_save_of_a_measured_pair_or_skip()

    try:
        model = world.load_world(source)
    except world.WorldLoadError as exc:
        pytest.fail(
            f"a real save of a measured pair did not load: {type(exc).__name__}",
            pytrace=False,
        )

    record_count = len(model.objects.records)
    token_length = len(model.token)
    level_count = model.objects.level_count
    assert record_count > 0, "a real world parsed to an empty record table"
    assert token_length == header.WORLD_TOKEN_LENGTH
    assert model.header.header_version in header.SUPPORTED_HEADER_VERSIONS
    assert level_count > 1, "a real body carries a list of levels, not a single table"


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
    source = _real_save_or_skip()

    # GUARDED, and the guard closes a leak measured on this machine rather than
    # reasoned about. pytest renders the ARGUMENTS of every frame in a failing
    # traceback - no --showlocals needed, no opt-in. Passing real save bytes into
    # a frame that can raise therefore prints the HEAD of the file, and the head
    # of a save is precisely the PII-bearing header: the save name, the options
    # string carrying platform, account id and player display name, and the
    # session name, which is the operator's world name (non-negotiables 11, 12).
    # Nothing may raise with those bytes in flight.
    try:
        parsed = header.read_header(source)
        body = chunks.decompress_body(
            source.read_bytes(), parsed.body_offset, header_version=parsed.header_version
        )
    except (header.HeaderError, chunks.ChunkError, OSError) as exc:
        pytest.fail(
            f"the newest real save did not reach a body: {type(exc).__name__}", pytrace=False
        )

    token_length = len(parsed.world_token)
    payload_length = len(body.payload)
    chunk_count = body.chunk_count

    assert parsed.header_version in header.SUPPORTED_HEADER_VERSIONS
    assert token_length == header.WORLD_TOKEN_LENGTH
    assert chunk_count >= 1
    assert payload_length > 0


# The fixtures that load through the one entry point. SAVE_V42 is absent because
# save version 42's transform delta is UNMEASURED, and the corpus builds that
# fixture with an EMPTY object section for the same reason.
LOADABLE_FIXTURES: Final = (
    synthetic.SAVE_V36,
    synthetic.SAVE_V52,
    synthetic.SAVE_V60,
    synthetic.SAVE_CROSS,
)

#: The save version that is refused by design. CS-408 owns measuring its delta.
UNMEASURED_SAVE_VERSION: Final = 42


def test_the_loadable_version_set_is_three_of_four() -> None:
    """CS-402's TRUE shape: three of four save versions parse, and one is refused.

    Asserting "every fixture loads" would be a comfortable lie. Save version 42
    is refused BY DESIGN because its transform delta has never been measured,
    and an absent key raises rather than defaulting to a plausible neighbour's
    value. Both halves are asserted here so a future reader cannot mistake the
    green suite for CS-402 being met.
    """
    loadable = {fixture.save_version for fixture in LOADABLE_FIXTURES}
    assert loadable == {36, 52, 60}, (
        "the loadable save-version set changed; CS-402's status must be re-stated"
    )
    assert UNMEASURED_SAVE_VERSION not in objects.TRANSFORM_DELTA_BY_SAVE_VERSION, (
        "save version 42 gained a transform delta; CS-408 has landed and this gate, "
        "CS-402 and the module docstring above all need updating together"
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


#: The header version that CANNOT be exercised end to end today. It appears in
#: exactly one fixture, SAVE_V42, and that fixture is refused at the object
#: stage because save version 42's transform delta is unmeasured.
HEADER_VERSION_GATED_BY_CS_408: Final = 13


def test_header_version_coverage_through_the_entry_point_is_two_of_three() -> None:
    """MEASURED, and it contradicts the comfortable claim - so the measurement wins.

    ROADMAP CS-402 records that "header version dispatch IS fully covered, on
    all three header versions". That is true at the HEADER LAYER, where
    ``tests/save/test_header.py`` parses all three directly. It is NOT true
    through the composed ``load_world`` entry point, and this gate says so:

        header 10  reachable (SAVE_V36)
        header 13  UNREACHABLE - its only fixture is SAVE_V42, refused at the
                   object stage because save 42's delta is unmeasured (CS-408)
        header 14  reachable (SAVE_V52, SAVE_V60, SAVE_CROSS)

    So the header-13 BODY PREFIX WIDTH - the wide int64 prefix that versions 13
    and 14 share - is exercised end to end only through header 14. That is a
    real coverage gap, not a naming quibble, and it is asserted rather than
    described so that CS-408 landing makes this test RED and forces the claim to
    be restated.
    """
    reachable = {fixture.header_version for fixture in LOADABLE_FIXTURES}
    supported = set(header.SUPPORTED_HEADER_VERSIONS)

    assert reachable == supported - {HEADER_VERSION_GATED_BY_CS_408}, (
        "the set of header versions reachable through load_world changed; CS-402's status "
        "and this gate's module docstring must be restated together"
    )
    assert HEADER_VERSION_GATED_BY_CS_408 in supported, (
        "header 13 is no longer a supported version, which is a bigger change than this "
        "test is about"
    )

    gated_fixtures = [
        fixture.name
        for fixture in synthetic.ALL_SAVES
        if fixture.header_version == HEADER_VERSION_GATED_BY_CS_408
    ]
    assert gated_fixtures == ["SAVE_V42"], (
        "header 13 now appears in a fixture other than SAVE_V42. If that fixture carries a "
        "measured save version, header 13 has become reachable and this gap has closed"
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


def _child_pytest_args() -> list[str]:
    """Build the argv for the child pytest run over the save-layer suite.

    The recursion guard is explicit and not incidental: without ``--ignore`` the
    child collects this module, which launches its own child, forever. It is an
    absolute path derived from ``__file__``, so a rename cannot leave it
    pointing at a path that no longer exists - which would look green right up
    to the moment the machine ran out of processes.

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
    ]


def test_the_save_suite_passes_with_no_install_and_no_save() -> None:
    """PHASE INVARIANT. The whole save suite is green with all four overrides absent.

    This is the environment CI and every fresh clone run in, and on the
    operator's machine - where the game IS installed and a save library DOES
    exist - it is the only thing that reproduces it. A test that reached for the
    real install, the real save root or the operator's config/local.json turns
    this red here, which is the only place the mistake is otherwise invisible.

    A test that genuinely needs a save is not forbidden; it must skip with a
    reason, and a skip keeps the exit code at zero.
    """
    child = _run_child(_child_pytest_args())
    exit_code = child.returncode
    assert exit_code == 0, (
        "the save-layer suite does not pass without an install or a save library.\n"
        f"exit code: {exit_code}\n"
        f"stdout:\n{child.stdout}\n"
        f"stderr:\n{child.stderr}"
    )

    passed = re.search(r"(\d+) passed", child.stdout)
    assert passed is not None, f"the child run reported no passing tests:\n{child.stdout}"
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
        pytest.skip(f"clockspeed/save/{relative} calls no redactor")

    imports_directly = "from clockspeed.data.locate import" in source and "redact" in source
    imports_module = "from clockspeed.data import locate" in source
    assert imports_directly or imports_module, (
        f"clockspeed/save/{relative} calls redact() without importing it from "
        "clockspeed.data.locate, so it is calling something else"
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
