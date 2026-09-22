#!/usr/bin/env python3
"""A lift with no byte pin and no register row, found by what its bytes name.

CS-1165. ``tests/test_third_party_register.py`` derives its population from
byte PINS, so a file lifted into this tree that nobody pinned and nobody
registered has no digest for its bytes to agree with and is invisible there.
This module grades that residual with an oracle that is neither a list kept in
this tree nor a read of any sibling tree.

THE SIGNAL. A file written in a sibling repository names that repository's
namespace: its item ids are spelled with the sibling's code followed by a
number, and its machine-wide resources are spelled with the lower-cased code
followed by a word. This tree's own authored files do neither. So a tracked or
untracked-unignored file that spells a SIBLING code in either shape, and is not
accounted for, is red here, named, with the marker and the line it sits on.

THE CODES ARE NOT A LIST ANYBODY HERE MAINTAINS. They are read at runtime from
the roster table of ``docs/CHANNEL.md`` - a vendored, byte-pinned record whose
re-pin is a joint act across every carrying tree - and this tree's own code is
derived from the prefix ``ROADMAP.md`` spells its item ids with. Neither is
typed into this module, so no code, and no file, reaches the graded population
by somebody remembering to add it.

ACCOUNTED FOR IS DERIVED TOO. A file is accounted for when the register's
vendored table names it, or when it is the test module that byte-pins one of
those files - a pin module quotes its subject's bytes, so it carries the
subject's markers by construction. Both sets are computed by the register
module's own readers, never listed here. :data:`MARKED_BUT_AUTHORED_HERE` is
the one escape, it is empty, and an entry needs a written reason; the absence
of an entry is red, not silent.

WHAT THIS DOES NOT COVER, stated rather than left to be discovered: a lift
whose bytes name no sibling namespace. ``ops/loop/winmutex.py`` is exactly
that shape - a fork whose header was retargeted at this project - and a copy of
it at a fresh path would pass this module green. No content signal inside this
tree can see such a file; only a comparison against the sibling trees (which
this suite must never read) or a provenance manifest every tracked file is
entered in could. This module narrows the CS-1165 class to that de-branded
residue; it does not close it.
"""

from __future__ import annotations

import functools
import re
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path

from tests.test_third_party_register import (
    REPO_ROOT,
    _byte_pinned_paths,
    _listed_paths,
    _register_text,
    _table_rows,
)

#: The vendored cross-repo record whose roster names every sibling code.
CHANNEL = REPO_ROOT / "docs" / "CHANNEL.md"

#: The heading that opens the roster table inside it.
ROSTER_HEADING = "## 0. Roster"

#: The owner of open work, whose item ids carry this tree's own code.
ROADMAP = REPO_ROOT / "ROADMAP.md"

#: An item id as this fleet spells one: a two-to-three letter code, a hyphen,
#: digits. Used only to DERIVE this tree's code, never to enumerate siblings.
ITEM_ID_RE = re.compile(r"\b([A-Z]{2,3})-[0-9]+\b")

#: Files that spell a sibling marker and are authored here anyway, each mapped
#: to the reason. Empty today; a file reaches it only by a written sentence.
MARKED_BUT_AUTHORED_HERE: dict[str, str] = {}

#: The smallest roster that makes this arm mean anything: this tree plus one
#: sibling. Below it the marker pattern has nothing foreign to look for.
MIN_ROSTER = 2

#: Seconds allowed for the one child this module spawns.
GIT_TIMEOUT = 30

#: The file whose bytes the mutation arm lifts to a fresh path. It is a real
#: sibling file - byte-identical by contract with the trees that carry it -
#: and it is read at RUNTIME, so this module's own source carries no marker.
LIFT_SOURCE = "ops/loop/slots.py"

#: Where the mutation arm plants the lift. Nothing pins or registers this path.
LIFT_TARGET = "ops/loop/cs1165_lifted_copy.py"


def _roster_codes() -> list[str]:
    """Return every repository code the channel roster names.

    Returns:
        The codes from column 0 of the roster table, in table order.
    """
    text = CHANNEL.read_bytes().decode("ascii").replace("\r\n", "\n")
    return [row[0].strip("`* ") for row in _table_rows(text, ROSTER_HEADING)]


def _own_code() -> str:
    """Return this tree's code: the prefix ``ROADMAP.md`` spells item ids with.

    Returns:
        The most frequent item-id prefix in the roadmap.
    """
    text = ROADMAP.read_bytes().decode("ascii")
    prefixes: Counter[str] = Counter(match.group(1) for match in ITEM_ID_RE.finditer(text))
    return prefixes.most_common(1)[0][0]


def _foreign_codes() -> list[str]:
    """Return every roster code except this tree's own.

    Returns:
        The sibling codes, longest first so an alternation prefers the longer.
    """
    own = _own_code()
    return sorted((code for code in _roster_codes() if code != own), key=len, reverse=True)


def _marker_re(codes: Iterable[str]) -> re.Pattern[str]:
    """Return the pattern matching a sibling namespace marker.

    Args:
        codes: The sibling codes.

    Returns:
        A pattern matching an upper-case code followed by a hyphen and a digit
        (an item id, or a dated inbox name) or a lower-case code followed by a
        hyphen and a letter (a namespaced machine resource), not glued to a
        preceding alphanumeric.
    """
    upper = "|".join(re.escape(code) for code in codes)
    lower = "|".join(re.escape(code.lower()) for code in codes)
    return re.compile(rf"(?<![A-Za-z0-9])(?:(?:{upper})-[0-9]|(?:{lower})-[a-z])")


def _candidate_paths() -> list[str]:
    """Return every tracked path plus every untracked path git does not ignore.

    Untracked files are included because a lift dropped into the tree is a
    lift before anybody stages it, and a tracked-only population is blind to it.

    Returns:
        Repo-relative POSIX paths that are files on disk.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    names = {name for name in listing.stdout.decode("utf-8").split("\0") if name}
    return sorted(name for name in names if (REPO_ROOT / name).is_file())


@functools.cache
def _tree_bytes() -> dict[str, bytes]:
    """Return the bytes of every candidate path, read once per run.

    Returns:
        Repo-relative POSIX paths mapped to their bytes on disk.
    """
    return {name: (REPO_ROOT / name).read_bytes() for name in _candidate_paths()}


def _accounted_for() -> set[str]:
    """Return the files whose sibling markers are already accounted for.

    Returns:
        The register's vendored rows, plus the test module that byte-pins each
        of them, plus the written exemptions.
    """
    listed = set(_listed_paths(_register_text()))
    pin_modules = {
        Path(*pin.rsplit(".", 1)[0].split(".")).with_suffix(".py").as_posix()
        for path, pin in _byte_pinned_paths().items()
        if path in listed
    }
    return listed | pin_modules | set(MARKED_BUT_AUTHORED_HERE)


def _unaccounted_lifts(
    files: Mapping[str, bytes], accounted: set[str], pattern: re.Pattern[str]
) -> list[str]:
    """Return each unaccounted file that spells a sibling marker.

    Args:
        files: Repo-relative paths mapped to their bytes.
        accounted: Paths whose markers are already accounted for.
        pattern: The sibling marker pattern.

    Returns:
        One ``path (marker ..., line N)`` entry per offending file, sorted.
    """
    found: list[str] = []
    for name in sorted(files):
        if name in accounted:
            continue
        text = files[name].decode("utf-8", "replace")
        hit = pattern.search(text)
        if hit is not None:
            line = text.count("\n", 0, hit.start()) + 1
            found.append(f"{name} (marker {hit.group(0)!r}, line {line})")
    return found


def test_the_roster_yields_this_tree_and_at_least_one_sibling() -> None:
    # Anti-vacuity: a roster that stopped parsing, or an own-code derivation
    # that drifted off the roster, would leave the marker pattern with nothing
    # foreign to find and every arm below green over nothing.
    roster = _roster_codes()
    own = _own_code()
    assert len(roster) >= MIN_ROSTER, f"the channel roster parsed to {roster}"
    assert own in roster, f"this tree's derived code {own!r} is not in the roster {roster}"
    assert own not in _foreign_codes()


def test_the_marker_pattern_fires_on_every_sibling_and_not_on_this_tree() -> None:
    # The pattern is built at runtime, so it is probed at runtime: every
    # sibling code in both shapes must match, and this tree's own must not.
    pattern = _marker_re(_foreign_codes())
    silent = [
        probe
        for code in _foreign_codes()
        for probe in (f"see {code}-12 here", f"root {code.lower()}-loop here")
        if pattern.search(probe) is None
    ]
    assert silent == [], f"the marker pattern misses these sibling probes: {silent}"
    own = _own_code()
    assert pattern.search(f"see {own}-12 and {own.lower()}-loop") is None


def test_no_unaccounted_file_spells_a_sibling_namespace_marker() -> None:
    # THE ARM. Its oracle is what the bytes NAME, against codes read from a
    # vendored roster - no list of files is consulted to decide what is red.
    files = _tree_bytes()
    assert LIFT_SOURCE in files, f"{LIFT_SOURCE} is not in the candidate population"
    found = _unaccounted_lifts(files, _accounted_for(), _marker_re(_foreign_codes()))
    assert found == [], (
        f"these files spell a sibling repository's namespace and are neither in "
        f"the third-party register nor the byte-pin module of a file that is: "
        f"{found}. A file written in a sibling tree and copied here carries a "
        "licence obligation recorded nowhere. Register it in THIRD_PARTY.md, or "
        "if it is authored here say so in MARKED_BUT_AUTHORED_HERE with a reason."
    )


def test_a_verbatim_sibling_lift_at_a_fresh_path_is_named() -> None:
    # THE MUTATION. A real sibling file's bytes land at a path nothing pins and
    # nothing registers - nothing added anywhere else - and the arm above must
    # name exactly that path. The plant is asserted APPLIED before the verdict
    # is read, so a plant that silently missed cannot pass as a kill.
    pristine = _tree_bytes()
    accounted = _accounted_for()
    planted = {**pristine, LIFT_TARGET: pristine[LIFT_SOURCE]}
    assert LIFT_TARGET not in pristine, f"{LIFT_TARGET} already exists, so nothing was planted"
    assert planted[LIFT_TARGET] == pristine[LIFT_SOURCE]
    assert LIFT_TARGET not in accounted, f"{LIFT_TARGET} is already accounted for"
    pattern = _marker_re(_foreign_codes())
    assert _unaccounted_lifts(pristine, accounted, pattern) == []
    named = [entry.split(" ", 1)[0] for entry in _unaccounted_lifts(planted, accounted, pattern)]
    assert named == [LIFT_TARGET], f"the planted lift was not named alone: {named}"


def test_the_authored_here_declarations_are_real_and_reasoned() -> None:
    # An escape hatch nothing grades is a hole: each entry must name a file in
    # the tree that actually spells a marker, and carry a reason.
    files = _tree_bytes()
    pattern = _marker_re(_foreign_codes())
    broken = sorted(
        path
        for path, reason in MARKED_BUT_AUTHORED_HERE.items()
        if path not in files
        or not reason.strip()
        or pattern.search(files[path].decode("utf-8", "replace")) is None
    )
    assert broken == [], f"these exemptions are stale or unreasoned: {broken}"
