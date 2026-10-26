"""CS-1355 - the shell's security floor for electron and undici, graded at rest.

Three advisories put a floor under the shell's lock: electron 44.0.0 sat inside
GHSA-fw47-9c62-h3vw (fixed 44.3.0) and GHSA-jr5w-w6x2-84p9 (fixed 44.9.1), and
the transitive undici 7.29.1 sat inside GHSA-xjj6-f33q-929c (fixed 7.30.1).
These arms read ``shell/package.json`` and ``shell/package-lock.json`` as JSON
off disk - nothing here runs Node or npm - and fail if a regenerated lock ever
resolves either package back below its floor, or if the manifest loosens the
exact pin into a range.

A floor comparison is a detector, so it carries a planted control in both
directions: a version below the floor must be refused and one at the floor
accepted, or a comparator that always says yes would read green.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
MANIFEST: Final = REPO_ROOT / "shell" / "package.json"
LOCKFILE: Final = REPO_ROOT / "shell" / "package-lock.json"

#: The fixed release named by each advisory, as an exact dotted triple.
ELECTRON_FLOOR: Final = (44, 9, 1)
UNDICI_FLOOR: Final = (7, 30, 1)

_EXACT: Final = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def triple(version: str) -> tuple[int, int, int]:
    """The numeric triple of an EXACT ``major.minor.patch`` version string.

    Args:
        version: A version string with no range operator and no prerelease tag.

    Returns:
        The three components as integers.

    Raises:
        ValueError: The string is not an exact three-part version.
    """
    match = _EXACT.fullmatch(version)
    if match is None:
        raise ValueError("not an exact major.minor.patch version")
    major, minor, patch = (int(part) for part in match.groups())
    return (major, minor, patch)


def meets(version: str, floor: tuple[int, int, int]) -> bool:
    """Whether an exact version is at or above a floor."""
    return triple(version) >= floor


def locked_version(name: str) -> str:
    """The version the committed lock resolves for a top-level install path."""
    packages = json.loads(LOCKFILE.read_bytes())["packages"]
    entry = packages.get(f"node_modules/{name}")
    assert isinstance(entry, dict), f"the lock holds no node_modules/{name} entry"
    version = entry.get("version")
    assert isinstance(version, str), f"node_modules/{name} carries no version string"
    return version


def test_the_locked_electron_meets_the_advisory_floor() -> None:
    """Electron resolves at or above 44.9.1, the fix for GHSA-jr5w-w6x2-84p9."""
    version = locked_version("electron")
    ok = meets(version, ELECTRON_FLOOR)
    assert ok, f"locked electron {version} is below {ELECTRON_FLOOR}"


def test_the_locked_undici_meets_the_advisory_floor() -> None:
    """Undici resolves at or above 7.30.1, the fix for GHSA-xjj6-f33q-929c."""
    version = locked_version("undici")
    ok = meets(version, UNDICI_FLOOR)
    assert ok, f"locked undici {version} is below {UNDICI_FLOOR}"


def test_the_lock_holds_no_second_nested_undici() -> None:
    """No nested copy of undici escapes the override at a lower version."""
    packages = json.loads(LOCKFILE.read_bytes())["packages"]
    stale = sorted(
        path
        for path, entry in packages.items()
        if path.endswith("node_modules/undici")
        and not meets(str(entry.get("version", "0.0.0")), UNDICI_FLOOR)
    )
    count = len(stale)
    assert count == 0, f"{count} undici install path(s) below the floor: {stale}"


def test_the_manifest_pins_electron_exactly_at_or_above_the_floor() -> None:
    """The manifest pins electron EXACTLY - no range - at or above the floor."""
    pin = json.loads(MANIFEST.read_bytes())["devDependencies"]["electron"]
    ok = isinstance(pin, str) and _EXACT.fullmatch(pin) is not None and meets(pin, ELECTRON_FLOOR)
    assert ok, f"electron devDependency pin {pin!r} is not an exact version at the floor"


def test_the_manifest_overrides_undici_exactly_at_or_above_the_floor() -> None:
    """An npm ``overrides`` entry pins the transitive undici exactly."""
    overrides = json.loads(MANIFEST.read_bytes()).get("overrides", {})
    pin = overrides.get("undici") if isinstance(overrides, dict) else None
    ok = isinstance(pin, str) and _EXACT.fullmatch(pin) is not None and meets(pin, UNDICI_FLOOR)
    assert ok, f"undici override {pin!r} is not an exact version at the floor"


def test_the_floor_comparator_refuses_below_and_accepts_at_the_floor() -> None:
    """Planted controls: the comparator can say no, and says yes at the floor."""
    assert not meets("44.0.0", ELECTRON_FLOOR)
    assert not meets("44.9.0", ELECTRON_FLOOR)
    assert meets("44.9.1", ELECTRON_FLOOR)
    assert meets("45.0.0", ELECTRON_FLOOR)
    assert not meets("7.29.1", UNDICI_FLOOR)
    assert not meets("7.30.0", UNDICI_FLOOR)
    assert meets("7.30.1", UNDICI_FLOOR)


def test_the_exact_pattern_refuses_a_range() -> None:
    """A caret or tilde range is not an exact pin and is refused."""
    ranges = ("^44.9.1", "~7.30.1", "44.9", ">=7.30.1")
    accepted = tuple(text for text in ranges if _EXACT.fullmatch(text) is not None)
    assert not accepted, f"range spellings accepted as exact: {accepted}"
