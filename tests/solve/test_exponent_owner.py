"""CS-1030: the shipped power-consumption exponent has ONE owner.

THE OWNER is the ``power_consumption_exponents`` map of the pinned fingerprint
in ``clockspeed/data/version.py`` - a measured census of the shipped docs file,
held under the drift guard that reddens when the shipped data moves. Every
other shipped source that needs to talk about the exponent points at that pin
in prose and never spells a value out, so a balance patch moves the exponent in
one place and leaves no stale copy behind that still reads as current.

WHAT THE SCAN BANS. Every key of that map is read from the owner at test time -
never typed in this file, because a typed copy would be one more restatement -
and three spellings of each are refused in every file under ``clockspeed/``
other than the owner:

- the key string verbatim, exactly as the census records it;
- its reduced fraction ``n/d``, bounded by digits on both sides, so the value
  written as a quotient is caught while a longer quotient that merely CONTAINS
  those digits is not;
- its constructor spelling ``Fraction(n, d)``.

WHAT THE SCAN DOES NOT COVER, stated so it is not read as covering it:

- ``tests/``. Fixtures there carry the exponent as INPUT DATA - a synthetic
  registry has to hold some value - and an input is not a restatement.
- ``docs/``, ADRs and the other markdown. Those belong to a separate census.
- A spelling with its trailing zeros stripped, or any spelling of a key that
  is not one of the three above.
- The float the power law degrades to when evaluated. That is the measured
  RESULT of evaluating the law, not the exponent, and it is outside CS-1030.

THE COMMON-MODE RISK is that every ban derives from the pin's key STRINGS. A
census format change that emptied the map, or wrote keys that no longer parse
as numbers, would silently narrow the scan to nothing while it stayed green.
``test_the_pinned_exponent_map_is_a_parsable_census`` refuses that.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import version

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final = REPO_ROOT / "clockspeed"
OWNER: Final = Path(version.__file__).resolve()

#: Where in the pin the exponent values live: the census section, under the
#: exponent key. Key NAMES, not values - renaming either in the pin fails this
#: module loudly with a KeyError at collection.
CENSUS_SECTION: Final = "census"
EXPONENT_CENSUS_KEY: Final = "power_consumption_exponents"

#: Every shipped source that restated an exponent value before CS-1030, held
#: so the scan is proven to REACH them rather than trusted to.
FORMER_CARRIERS: Final = (
    "clockspeed/data/registry.py",
    "clockspeed/solve/exact.py",
    "clockspeed/solve/optimize.py",
    "clockspeed/solve/power.py",
    "clockspeed/surface/api/power.py",
)

SPELLING_VERBATIM: Final = "verbatim key"
SPELLING_QUOTIENT: Final = "reduced fraction"
SPELLING_CONSTRUCTOR: Final = "Fraction constructor"
SPELLINGS: Final = (SPELLING_VERBATIM, SPELLING_QUOTIENT, SPELLING_CONSTRUCTOR)


def census_problems(exponents: object) -> list[str]:
    """Name every way the pinned exponent map fails to be a usable census.

    Args:
        exponents: The value the pin holds under the exponent census key.

    Returns:
        One line per problem; empty when every key parses as a number.
    """
    if not isinstance(exponents, Mapping):
        return [f"the exponent census is a {type(exponents).__name__}, not a mapping"]
    if not exponents:
        return ["the exponent census is empty, so the scan would ban nothing"]
    problems = []
    for key in exponents:
        try:
            Fraction(str(key))
        except ValueError:
            problems.append(f"census key {key!r} does not parse as a Fraction")
    return problems


def pinned_exponents() -> list[str]:
    """Return every exponent key the owner pins, in pin order."""
    return [str(key) for key in version.pin()[CENSUS_SECTION][EXPONENT_CENSUS_KEY]]


def spelling_pattern(key: str, spelling: str) -> re.Pattern[str]:
    """Compile the matcher for one spelling of one pinned exponent.

    Args:
        key: A key of the pinned exponent map.
        spelling: One of :data:`SPELLINGS`.

    Returns:
        The compiled pattern. The quotient is digit-bounded on both sides, so
        it does not match inside a longer quotient that contains its digits.
    """
    value = Fraction(key)
    numerator, denominator = value.numerator, value.denominator
    if spelling == SPELLING_VERBATIM:
        return re.compile(re.escape(key))
    if spelling == SPELLING_QUOTIENT:
        return re.compile(rf"(?<![0-9.]){numerator}/{denominator}(?![0-9])")
    if spelling == SPELLING_CONSTRUCTOR:
        return re.compile(rf"Fraction\(\s*{numerator}\s*,\s*{denominator}\s*\)")
    raise ValueError(f"unknown spelling {spelling!r}")


def shipped_sources() -> list[Path]:
    """Every file under ``clockspeed/`` except the owner and bytecode caches."""
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.resolve() != OWNER
    )


def restatements(key: str, spelling: str) -> list[str]:
    """Name every shipped source line that spells one pinned exponent one way.

    Args:
        key: A key of the pinned exponent map.
        spelling: One of :data:`SPELLINGS`.

    Returns:
        ``path:line`` for each carrier, relative to the repository root.
    """
    pattern = spelling_pattern(key, spelling)
    found = []
    for path in shipped_sources():
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                found.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{number}")
    return found


_CASES: Final = [(key, spelling) for key in pinned_exponents() for spelling in SPELLINGS]


def test_the_pinned_exponent_map_is_a_parsable_census() -> None:
    """The owner's map is non-empty and every key parses, so the scan bans something.

    Both refusals are watched firing on a synthetic stand-in, because an arm
    that has only ever passed says nothing about whether it can fail.
    """
    problems = census_problems(version.pin()[CENSUS_SECTION][EXPONENT_CENSUS_KEY])
    assert not problems, "\n".join(problems)
    assert census_problems({}), "an empty census was accepted"
    assert census_problems({"not-a-number": 1}), "an unparsable census key was accepted"
    assert census_problems([]), "a census that is not a mapping was accepted"


@pytest.mark.parametrize(("key", "spelling"), _CASES, ids=str)
def test_no_shipped_source_restates_a_pinned_exponent(key: str, spelling: str) -> None:
    """No file under ``clockspeed/`` but the owner spells a pinned exponent.

    Parametrized one key and one spelling per case, so the weakest member is
    graded on its own rather than hidden inside a pooled count.
    """
    carriers = restatements(key, spelling)
    count = len(carriers)
    listed = "\n  ".join(carriers)
    assert count == 0, (
        f"{count} shipped line(s) restate a pinned exponent as a {spelling}; cite the "
        f"pin in clockspeed/data/version.py instead of the digits:\n  {listed}"
    )


def test_the_scan_reaches_every_former_carrier_and_skips_only_the_owner() -> None:
    """The scan walks the modules that used to restate the exponent.

    Without this the ban could pass because the walk found no files at all, or
    because it quietly stopped descending into a sub-package.
    """
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in shipped_sources()}
    missing = [relative for relative in FORMER_CARRIERS if relative not in scanned]
    assert not missing, f"the scan does not reach {missing}"
    owner_relative = OWNER.relative_to(REPO_ROOT).as_posix()
    assert owner_relative not in scanned, "the scan reads the owner it exists to defer to"


@pytest.mark.parametrize(("key", "spelling"), _CASES, ids=str)
def test_each_matcher_fires_on_its_spelling(key: str, spelling: str) -> None:
    """Every matcher is watched catching the spelling it exists to catch.

    The spelling is rebuilt from the derived value, never typed, and dropped
    into prose the way a docstring would carry it.
    """
    value = Fraction(key)
    written = {
        SPELLING_VERBATIM: key,
        SPELLING_QUOTIENT: f"{value.numerator}/{value.denominator}",
        SPELLING_CONSTRUCTOR: f"Fraction({value.numerator}, {value.denominator})",
    }[spelling]
    prose = f"the shipped exponent is ({written}), so the term is irrational"
    matched = spelling_pattern(key, spelling).search(prose) is not None
    assert matched, f"the {spelling} matcher missed its own spelling"


@pytest.mark.parametrize("key", pinned_exponents())
def test_the_quotient_matcher_is_digit_bounded(key: str) -> None:
    """A longer quotient that CONTAINS the reduced fraction is not a restatement.

    The embedding is built from the derived fraction with a digit added on
    each side, which is the shape that turns a short quotient into a false
    positive inside an unrelated ratio.
    """
    value = Fraction(key)
    embedded = f"1{value.numerator}/{value.denominator}0"
    matched = spelling_pattern(key, SPELLING_QUOTIENT).search(embedded) is not None
    assert not matched, "the quotient matcher fired inside a longer quotient"


@pytest.mark.parametrize("key", pinned_exponents())
def test_the_owner_carries_each_key_it_is_scanned_for(key: str) -> None:
    """The keys come from the owner's own text, which the scan then excludes.

    If the pin ever stopped carrying a key verbatim, the verbatim ban would be
    checking for a string nothing owns.
    """
    owner_text = OWNER.read_text(encoding="utf-8")
    carried = spelling_pattern(key, SPELLING_VERBATIM).search(owner_text) is not None
    assert carried, "the owner does not carry a key its own pin reports"


@pytest.mark.parametrize("key", pinned_exponents())
def test_no_pinned_exponent_is_exact_in_binary(key: str) -> None:
    """Each pinned exponent's reduced denominator is not a power of two.

    ``clockspeed/data/registry.py`` and ``clockspeed/solve/exact.py`` say, now
    without the digits, that a shipped exponent is not representable in binary
    floating point. That is true exactly when its reduced denominator is not a
    power of two, so this arm is the claim, measured against the owner.
    """
    denominator = Fraction(key).denominator
    power_of_two = denominator & (denominator - 1) == 0
    assert not power_of_two, "a pinned exponent is exact in binary; the prose claims otherwise"
