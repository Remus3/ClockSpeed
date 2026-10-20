#!/usr/bin/env python3
"""CS-946 slice S1 - the vendored shared slot protocol, and the pin that holds it.

``ops/loop/slots.py`` is VENDORED BYTE-IDENTICAL from the carrier trees that
already share the machine-wide lane-slot bucket. It is not this repository's
file to edit. The carriers coordinate THROUGH its on-disk protocol, so two
trees running different implementations can each believe they hold the only
slot - a fork of a mutex is not a fork, it is a second mutex.

WHY A DIGEST ALONE IS NOT THE PIN. Three failures a bare digest arm reports as
an unexplained hex mismatch, each given its own arm here and each declared
AHEAD of the digest arm in file order so the cause reddens beside the symptom:

  1. LINE ENDINGS. ``.gitattributes`` pins ``*.py text eol=lf``, so git checks
     the file out with LF and NORMALISES the blob on the way in. A tool that
     rewrites the working tree with CRLF therefore leaves ``git status``
     reporting clean over a file that violates the rule, and the digest - which
     hashes WORKING-TREE BYTES, not the blob - goes red with nothing naming
     why. ``test_the_vendored_file_carries_no_carriage_return`` names it.

  2. CHARACTER SET. CLAUDE.md non-negotiable 4 is 7-bit ASCII in authored
     content, and a vendored file is content this tree now ships.
     ``test_the_vendored_file_is_seven_bit_ascii`` measures the bytes rather
     than believing the upstream header's claim to be portable.

  3. A CARRIER NAME RE-ENTERING. A digest CANNOT catch this, and the reason is
     structural rather than incidental: during a re-pin round the digest
     changes LEGITIMATELY in the same commit that would carry the new name, so
     the one arm that would notice is the one arm already expected to move.
     ``test_the_vendored_file_names_no_carrier_beyond_the_bucket_path`` pins a
     CENSUS - an exact mapping of token to occurrence count - rather than an
     absence, so a name arriving reddens even in a round where the digest is
     being re-typed on purpose.

THE CENSUS IS NOT EMPTY AND THAT IS THE FINDING. The upstream header says
"Nothing here may reference ANY of them: every project-specific value arrives
as an argument". Measured on the bytes, that claim is very nearly but not
exactly true: ``DEFAULT_ROOT`` hardcodes ``lw-loop`` as the bucket directory
name, which is a carrier's short code baked into the shared path. It is
PROTOCOL rather than prose - every carrier must spell the same directory or
they are not sharing a bucket - so it is pinned as an expected hit with its
count, not waved through and not edited out.

THE HARDCODED ROOT IS ASSERTED AGAINST THE ENVIRONMENT, not read and trusted.
``slots.DEFAULT_ROOT`` is an absolute literal. The adapter CS-946 slice S2 will
add must resolve ``bucket_root()`` to exactly this path, because a bucket root
that merely LOOKS right joins a DIFFERENT bucket: the governor silently stops
governing while every arm in the tree stays green. This module pins the
literal's identity with the path derived from ``PROGRAMDATA`` so S2 has a fixed
target to equal rather than a coincidence to inherit.

THE GUARD TOOK THE EXEMPTION, NOT THE FILE, AND THE EXEMPTION IS PINNED HERE.
Three tree-wide gates refused the vendored bytes the moment they were tracked -
`ruff check` on nine rule codes, `ruff format --check` on its line wrapping, and
`python -m mypy` on two Any-typed returns. Editing the file to satisfy any of
them would change its sha256, break byte-identity with four carrier trees, and
make this module's own digest arm a lie about a protocol rather than a fact
about a file. So `pyproject.toml` carries three exemptions and the file carries
none.

AN EXEMPTION IS A HOLE, SO ITS SHAPE IS GRADED. The arms below assert each one
is scoped to the ONE path and no other - a literal path, never a glob, never a
directory. An allowlist written as `ops/loop/*.py` absorbs whatever arrives
next, which is how an allowlist becomes a denylist by another name; this tree
has that failure on record. The exempted RULE CODES are pinned as an exact set
too, so widening the hole for a file already inside it also reddens.

NOTHING HERE ACQUIRES A SLOT. No arm calls ``hold``, ``try_acquire`` or
``reap``, and no arm creates, reads or removes a file in the real bucket. This
module reads one file's bytes and one module constant.

Authority: CLAUDE.md section 4 (a guard that refuses a vendored file gets the
exemption, never the file a byte), non-negotiables 4 and 9.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import tomllib
from pathlib import Path
from typing import Final

import pytest

#: The repository root, derived from this file's own location rather than from
#: a literal - an absolute path under a home directory in a tracked file is
#: forbidden outright (CLAUDE.md non-negotiable 3).
REPO_ROOT: Final = Path(__file__).resolve().parents[2]

#: The vendored file, named as a relative POSIX string in every failure message
#: so a report never renders a checkout path.
RELATIVE: Final = "ops/loop/slots.py"
SLOTS_PATH: Final = REPO_ROOT / "ops" / "loop" / "slots.py"

#: The bucket directory, relative to the all-users data root. Pinned HERE, in
#: the module that pins the protocol file, because it is part of the protocol:
#: a carrier spelling a different relative path is not in the same bucket. The
#: adapter slice S2 adds must join exactly these parts.
BUCKET_RELPATH: Final = ("lw-loop", "slots")

#: Every sibling project on this box by name, plus the delimited two-letter
#: short codes those projects use in channel notes and lock payloads. Searched
#: case-insensitively over the whole file. A plain substring would be useless
#: for the short codes - "ll" occurs inside "will" and "cs" inside "docs" - so
#: the codes are matched at word boundaries and the names are not.
#:
#: ROSTER CHANGE (CS-1272 R, MAIN 0230): "ebonwake" / "ew" JOINED, and
#: "lanternlight" / "ll" are RETIRED - kept, never removed, because a retired
#: sibling's name re-entering a file this tree ships is still a leak.
CARRIER_NAMES: Final = (
    "legion",
    "wallpaper",
    "resin",
    "compute",
    "riot",
    "commander",
    "substrate",
    "lanternlight",  # retired (MAIN 0230) - kept as a needle
    "clockspeed",
    "ghost toolbox",
    "monster",
    "replaybook",
    "moonbeam",
    "ebonwake",
)
CARRIER_CODES: Final = ("lw", "rsc", "rc", "ss", "ll", "cs", "ew")

#: THE CENSUS, MEASURED 2026-09-20 ON ALL FOUR CARRIER DISKS AND TYPED BY HAND.
#: One permitted hit: the short code "lw" inside ``lw-loop``, the shared bucket
#: directory name in ``DEFAULT_ROOT``. Every other token is expected to be
#: absent, and an ABSENT token is recorded as a zero rather than omitted, so
#: this mapping is an exact statement about the whole vocabulary instead of a
#: floor over the part of it somebody remembered to list. The two EW keys were
#: measured zero on the C4 bytes on 2026-10-08 (CS-1272 R) and the retired LL
#: keys stay pinned at zero.
EXPECTED_NAME_CENSUS: Final = {
    "legion": 0,
    "wallpaper": 0,
    "resin": 0,
    "compute": 0,
    "riot": 0,
    "commander": 0,
    "substrate": 0,
    "lanternlight": 0,
    "clockspeed": 0,
    "ghost toolbox": 0,
    "monster": 0,
    "replaybook": 0,
    "moonbeam": 0,
    "ebonwake": 0,
    "code:lw": 1,
    "code:rsc": 0,
    "code:rc": 0,
    "code:ss": 0,
    "code:ll": 0,
    "code:cs": 0,
    "code:ew": 0,
}

#: The first byte value that is NOT 7-bit ASCII. Named rather than written
#: inline because ruff's PLR2004 reads a bare literal in a comparison as a
#: magic value, and a name in the comparison reads better than a suppression -
#: the same reasoning ``tests/test_lane_lock.py`` records for its own ONE/TWO.
ASCII_CEILING: Final = 0x80

#: The config file the three tree-wide gates all read. Named once here so the
#: arms below cannot each resolve a different file.
GATE_CONFIG: Final = REPO_ROOT / "pyproject.toml"

#: The dotted module name mypy resolves ``ops/loop/slots.py`` to.
MODULE_NAME: Final = "ops.loop.slots"

#: Characters that turn a per-file-ignores or exclude key from one path into a
#: family of them.
GLOB_MARKERS: Final = ("*", "?", "[")

#: Keys that WOULD widen the exemption, used as the positive control for the
#: detector. Each is a real thing somebody could plausibly type instead.
WIDENING_PROBE: Final = ("ops/loop/*.py", "ops/**", "vendor[eo]d/slots.py")

#: THE EXEMPTED RULE CODES, TYPED BY HAND FROM A MEASURED `ruff check .` RUN ON
#: 2026-09-20 - nine codes, ten findings, N806 twice - plus D205 and D209,
#: measured on the C4 bytes on 2026-10-03 at the new two-line ``is_stale``
#: docstring and added with the C4 re-pin (CS-1216). Pinned as an exact tuple
#: rather than a floor: a code added here is a rule this tree stopped applying
#: to a file it ships, and that should take a reading of the file rather than a
#: quiet append.
EXEMPTED_RULE_CODES: Final = (
    "N818",
    "PLR0911",
    "PLC0415",
    "N806",
    "PLR2004",
    "PTH123",
    "SIM105",
    "PLR0913",
    "S311",
    "D205",
    "D209",
)

#: Every per-file-ignores key that legitimately covers the vendored file. The
#: ``ops/**`` entry predates CS-946 and covers the whole headless lane; the
#: literal entry is this item's. A THIRD key appearing is the widening this
#: module exists to catch.
EXPECTED_COVERING_KEYS: Final = ["ops/**", "ops/loop/slots.py"]

#: The single setting the type gate relaxes, as (key, value) pairs sorted the
#: way the arm sorts them.
EXPECTED_MYPY_RELAXATIONS: Final = [("warn_return_any", False)]

#: The measured size, carried so a truncated or re-wrapped copy reports its
#: shape rather than only a changed digest.
EXPECTED_BYTES: Final = 11426


def _gate_config() -> dict:
    """Parse the gate config from disk, in BINARY, for every arm that reads it.

    Parsed rather than grepped. A substring search over a file this heavily
    commented is a search of its documentation: every rule code exempted below
    is also spelled in the prose beside it, so `"S311" in text` would stay green
    through the code's removal from the list that actually governs.
    """
    return tomllib.loads(GATE_CONFIG.read_bytes().decode("utf-8"))


def _vendored_bytes() -> bytes:
    """Read the vendored file in BINARY, failing by NAME when it is absent.

    Binary, never text: ``read_text`` hides a CR, which is precisely the
    failure arm 1 above exists to catch.

    The presence check is an assertion rather than a bare read so the red run
    of a tree that has not vendored the file yet names the missing PATH. An
    ``ImportError`` or a bare ``FileNotFoundError`` traceback would be a
    failure about the harness instead of about the subject.
    """
    present = SLOTS_PATH.is_file()
    assert present is True, f"{RELATIVE} is absent from this working tree"
    return SLOTS_PATH.read_bytes()


def test_the_vendored_file_is_present_and_is_the_expected_size() -> None:
    raw = _vendored_bytes()
    size = len(raw)
    assert size == EXPECTED_BYTES


def test_the_vendored_file_carries_no_carriage_return() -> None:
    raw = _vendored_bytes()
    carriage_returns = raw.count(b"\r")
    assert carriage_returns == 0


def test_the_vendored_file_is_seven_bit_ascii() -> None:
    raw = _vendored_bytes()
    above_ascii = sum(1 for byte in raw if byte >= ASCII_CEILING)
    assert above_ascii == 0


def test_the_vendored_file_names_no_carrier_beyond_the_bucket_path() -> None:
    raw = _vendored_bytes()
    text = raw.decode("ascii", errors="replace").lower()
    census = {name: text.count(name) for name in CARRIER_NAMES}
    for code in CARRIER_CODES:
        census[f"code:{code}"] = len(re.findall(rf"\b{code}\b", text))
    assert census == EXPECTED_NAME_CENSUS


def test_the_vendored_file_matches_the_upstream_digest() -> None:
    raw = _vendored_bytes()
    digest = _sha256_of(raw)
    assert digest == SLOTS_DIGEST


def test_the_hardcoded_bucket_root_is_the_all_users_data_root_joined_with_the_relpath() -> None:
    """The literal root and the derived root are the SAME directory.

    CS-946 slice S2's ``lane_slot.bucket_root()`` must equal this value. If the
    two ever diverge, Clockspeed joins a bucket no carrier is in and the
    concurrency governor stops governing while nothing anywhere goes red.
    """
    _vendored_bytes()
    from ops.loop import slots  # noqa: PLC0415 - deliberately after the presence assertion

    program_data = os.environ.get("PROGRAMDATA", "").strip()
    if program_data == "":
        # PROGRAMDATA is a WINDOWS variable. The vendored file hardcodes an
        # all-users path under it, so on a platform that has no such variable
        # there is no derived root to compare the literal against - the equality
        # this arm exists to check cannot be CONSTRUCTED, let alone fail. Tier 1
        # runs on ubuntu, where that is the normal case, so asserting the
        # variable's presence turned a platform fact into a red suite.
        #
        # SKIPPED, not silently passed: the divergence this arm guards against is
        # UNMEASURED on this platform, not absent. It is measured on every
        # Windows run, which is where the bucket actually lives and where a
        # divergence could strand Clockspeed in a bucket no carrier is in.
        pytest.skip(
            "PROGRAMDATA is unset on this platform, so the all-users root the "
            "vendored file hardcodes cannot be derived here and the literal has "
            "nothing to be compared against. The literal-versus-derived "
            "divergence is UNMEASURED here, not absent - it is measured on every "
            "Windows run."
        )

    derived = Path(program_data).joinpath(*BUCKET_RELPATH)
    same = str(slots.DEFAULT_ROOT).casefold() == str(derived).casefold()
    assert same is True


def _sha256_of(raw: bytes) -> str:
    """Hash the bytes handed in, never a path this module re-reads."""
    import hashlib  # noqa: PLC0415 - kept beside its one caller

    return hashlib.sha256(raw).hexdigest()


def _is_literal_path(key: str) -> bool:
    """True when the key names one path rather than matching a family of them.

    Ruff resolves a per-file-ignores key as a glob, so ``ops/loop/*.py`` and
    ``ops/loop/slots.py`` are the same KIND of entry to it and differ only in
    what they will silently cover a year from now. That difference is the whole
    subject of the arms below, so it is measured rather than read.
    """
    return not any(marker in key for marker in GLOB_MARKERS)


def test_the_glob_detector_is_not_vacuous() -> None:
    """The positive control for all three scope arms.

    Without it, a detector that answered True for everything would report the
    exemptions narrow for the one reason that proves nothing.
    """
    literal = _is_literal_path(RELATIVE)
    widened = [_is_literal_path(key) for key in WIDENING_PROBE]
    assert (literal, widened) == (True, [False, False, False])


def test_the_lint_exemption_is_scoped_to_the_one_vendored_path() -> None:
    config = _gate_config()
    ignores = config["tool"]["ruff"]["lint"]["per-file-ignores"]
    entry = ignores.get(RELATIVE)
    present = entry is not None
    assert present is True, f"no per-file-ignores entry names {RELATIVE}"

    literal = _is_literal_path(RELATIVE)
    codes = tuple(entry)
    assert (literal, codes) == (True, EXEMPTED_RULE_CODES)


def test_no_other_lint_exemption_reaches_the_vendored_file() -> None:
    """Only the ops/** entry and the file's own entry may cover it.

    A second, wider key covering the same path would make the exact rule-code
    set above unenforceable: the file would be exempt from whatever that key
    listed as well, and the arm above would still be green.
    """
    config = _gate_config()
    ignores = config["tool"]["ruff"]["lint"]["per-file-ignores"]
    covering = sorted(key for key in ignores if fnmatch.fnmatch(RELATIVE, key))
    assert covering == EXPECTED_COVERING_KEYS


#: The vendored fleet kit modules the formatter is excluded from, for the same
#: byte-pin reason as this file: CS-1231 (fleet_headless.py), CS-1272 (the six
#: FLEET-KIT version 9 added) and CS-1282 (the one version 10 added), each
#: MEASURED "Would reformat". FLEET item 11 - a kit file is never edited
#: locally. Exact paths, in pyproject order, typed by hand rather than derived,
#: so a new entry is a diff to argue with.
KIT_FORMAT_EXCLUSIONS: Final = [
    "ops/fleet_kit/fleet_headless.py",
    "ops/fleet_kit/fleet_checklist.py",
    "ops/fleet_kit/fleet_done.py",
    "ops/fleet_kit/fleet_inbox.py",
    "ops/fleet_kit/fleet_lanes.py",
    "ops/fleet_kit/fleet_secrets.py",
    "ops/fleet_kit/fleet_watch.py",
    "ops/fleet_kit/fleet_subagent_first.py",
    # CS-1290 - the six modules kit versions 12 and 13 added.
    "ops/fleet_kit/fleet_claims.py",
    "ops/fleet_kit/fleet_gitlock.py",
    "ops/fleet_kit/fleet_identity.py",
    "ops/fleet_kit/fleet_rewrite.py",
    "ops/fleet_kit/fleet_suite_gate.py",
    "ops/fleet_kit/fleet_test_guard.py",
    # CS-1330 - the one module kit version 19 added.
    "ops/fleet_kit/fleet_board.py",
]

#: The kit's own pin, which names every file it vendors.
KIT_MANIFEST: Final = REPO_ROOT / "ops" / "fleet_kit" / "MANIFEST.json"


def test_the_formatter_exclusion_is_scoped_to_the_one_vendored_path() -> None:
    config = _gate_config()
    excluded = list(config["tool"]["ruff"]["format"].get("exclude", []))
    literal = all(_is_literal_path(key) for key in excluded)
    # The other entries are the vendored fleet kit modules, exact paths
    # excluded for the same byte-pin reason. Exact list, never a pattern.
    assert (excluded, literal) == ([RELATIVE, *KIT_FORMAT_EXCLUSIONS], True)
    # And each kit entry names a file the kit's MANIFEST pins, so the list can
    # never carry a tree-owned module under the vendored reason.
    pinned = json.loads(KIT_MANIFEST.read_bytes().decode("ascii"))["files"]
    unpinned = [path for path in KIT_FORMAT_EXCLUSIONS if path.rsplit("/", 1)[1] not in pinned]
    assert unpinned == [], f"formatter exclusions the kit MANIFEST does not pin: {unpinned}"


def test_the_formatter_exclusion_survives_being_handed_the_path_explicitly() -> None:
    """Without ``force-exclude`` the exclusion above applies to a WALK only.

    MEASURED: ``ruff format --check .`` reported exit 0 on this tree while the
    pre-commit gate, which hands ruff each staged path by name, blocked on this
    same file in the same minute. Two tools disagreeing about one file is the
    shape a byte-pin cannot survive, because the only way to satisfy the gate
    would be to rewrite bytes four carrier trees share.

    THE SECOND HALF IS THE QUIET ONE. ``force-exclude`` acts on every exclude
    list ruff holds, so a top-level ``exclude`` added later would start being
    enforced against explicit paths too - widening this hole without anybody
    writing the word. Its absence is asserted, not assumed.
    """
    config = _gate_config()
    ruff = config["tool"]["ruff"]
    forced = ruff.get("force-exclude")
    top_level_exclude = ruff.get("exclude")
    lint_exclude = ruff.get("lint", {}).get("exclude")
    assert (forced, top_level_exclude, lint_exclude) == (True, None, None)


def test_the_type_gate_exemption_is_scoped_to_the_one_vendored_module() -> None:
    """One overrides block, naming one module, relaxing one setting.

    ``exclude`` is deliberately not asserted here - tests/test_mypy_gate.py owns
    the fact that the gate declares none, and a second owner of that fact is a
    second place for it to drift.
    """
    config = _gate_config()
    blocks = config["tool"]["mypy"]["overrides"]
    ours = [block for block in blocks if MODULE_NAME in block.get("module", [])]
    count = len(ours)
    assert count == 1, f"{count} mypy overrides blocks name {MODULE_NAME}, expected 1"

    block = dict(ours[0])
    modules = list(block.pop("module"))
    relaxations = sorted(block.items())
    assert (modules, relaxations) == ([MODULE_NAME], EXPECTED_MYPY_RELAXATIONS)


#: THE UPSTREAM DIGEST, TYPED BY HAND AND DECLARED AFTER THE ARM THAT READS IT.
#: The precedent and the reason are ``tests/test_lane_lock.py``'s own forked-copy
#: pin: a digest COMPUTED from the file it pins is a tautology that reports
#: green through any edit. Re-measured 2026-09-20 from all four carrier working
#: copies on this disk, which agreed with each other and with the value
#: ``UPSTREAM_SLOTS_DIGEST`` already records.
#:
#: NEVER RE-TYPE THIS TO MAKE AN ARM PASS. A changed digest means either the
#: working tree was rewritten locally - check the CR and ASCII arms above first,
#: they name that case - or a carrier re-pinned the protocol, which is a joint
#: round with every carrier and not a local edit.
#:
#: RE-PINNED 2026-10-04 TO C4, the joint round's landed candidate: rebuilt here
#: from the two fenced diffs in the carriers' 2026-10-02 notes applied to the
#: previous bytes ``71fa2a68...``, and equal to the digest and size two carriers
#: stated from their own disks after landing it (11,426 B). The previous
#: upstream digest survives as ``UPSTREAM_SLOTS_DIGEST`` in
#: ``tests/test_lane_lock.py``, which records history and is never bumped.
SLOTS_DIGEST: Final = "290cbf80ce6989e15ad778be9032503733c8820030bfa6a9b27439b29d70486e"
