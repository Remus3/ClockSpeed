"""CS-1369 - every `dev` extra requirement carries a lower AND an upper bound.

WHY A BOUND IS A TESTED FACT RATHER THAN A HABIT. tier1 installs its toolchain
from this extra, so an unbounded row lets CI resolve a release this machine never
ran. That has reddened the runner twice: ruff's reworded format output and mypy's
changed error codes (CS-1302), both explained beside their rows in pyproject.toml.
A local suite says nothing about a release it did not run.

WHAT COUNTS. A bound is read from the PEP 440 clauses of a PARSED requirement, so
a comment in pyproject.toml that spells a range is never read as one, and an
environment marker such as ``; python_version < "3.14"`` is never read as an upper
bound. ``==``, ``===`` and ``~=`` are both bounds at once (mypy's exact pin is the
live case); ``!=`` is neither, because it excludes one release and permits the
next. A row this parser cannot read fails rather than passing as bounded.

THE ONE WAIVER WAIVES ONE HALF. pyproject.toml documents PyYAML as deliberately
having NO UPPER BOUND, so ``UPPER_BOUND_WAIVED`` lifts the upper half only and its
floor is still required. A row that needs a waiver gets a bound instead: its
installed major range is the repair, never a wider set.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Normalised names whose upper bound pyproject.toml documents as deliberately absent.
UPPER_BOUND_WAIVED = frozenset({"pyyaml"})

_NAME = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_EXTRAS = re.compile(r"\s*\[[^\]]*\]")
_CLAUSE = re.compile(r"\s*(===|==|~=|>=|<=|!=|>|<)\s*[^\s,]")
_BOTH = frozenset({"===", "==", "~="})
_LOWER = _BOTH | {">=", ">"}
_UPPER = _BOTH | {"<=", "<"}


def normalised_name(name: str) -> str:
    """Return a distribution name the PEP 503 way.

    Args:
        name: The name as a requirement spells it.

    Returns:
        The lower-cased name with each separator run reduced to one hyphen.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def unbounded_requirements(
    requirements: Iterable[str], upper_waived: frozenset[str] = UPPER_BOUND_WAIVED
) -> tuple[str, ...]:
    """Name every requirement that lacks a lower or an upper bound.

    Args:
        requirements: PEP 508 requirement strings.
        upper_waived: Normalised names whose upper bound alone is not required.

    Returns:
        One finding per missing bound, in input order, each opening with the
        requirement's name. Empty when every requirement is bounded.
    """
    findings: list[str] = []
    for requirement in requirements:
        body = requirement.split(";", 1)[0]
        name = _NAME.match(body)
        if name is None:
            findings.append(f"{requirement}: not a readable requirement")
            continue
        specifier = _EXTRAS.sub("", body[name.end() :], count=1).strip().strip("()")
        operators = {
            clause.group(1)
            for clause in (_CLAUSE.match(part) for part in specifier.split(","))
            if clause is not None
        }
        if not operators & _LOWER:
            findings.append(f"{name.group(1)}: no lower bound")
        if not operators & _UPPER and normalised_name(name.group(1)) not in upper_waived:
            findings.append(f"{name.group(1)}: no upper bound")
    return tuple(findings)


def dev_requirements(root: Path) -> list[str]:
    """Read the `dev` extra out of a pyproject.toml, parsed rather than grepped.

    Args:
        root: The directory holding the pyproject.toml.

    Returns:
        The requirement strings in file order.
    """
    parsed = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return [str(row) for row in parsed["project"]["optional-dependencies"]["dev"]]


def test_the_live_dev_extra_is_bounded() -> None:
    rows = dev_requirements(REPO_ROOT)

    assert rows, "the dev extra read as empty, so this arm graded nothing"
    assert unbounded_requirements(rows) == ()


def test_the_waiver_is_live_and_is_the_only_thing_excusing_the_extra() -> None:
    # A waiver naming a row that has since gained a bound, or a second row hiding
    # behind it, both change this set. Without the waiver exactly one row is short.
    assert unbounded_requirements(dev_requirements(REPO_ROOT), upper_waived=frozenset()) == (
        "pyyaml: no upper bound",
    )


def test_the_waiver_is_documented_beside_its_row() -> None:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "NO UPPER BOUND, DELIBERATELY" in text


def test_a_bound_removed_from_a_real_row_in_a_fixture_names_that_row(tmp_path: Path) -> None:
    pristine = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    planted = pristine.replace('"ruff>=0.13,<0.16"', '"ruff>=0.13"')
    assert planted != pristine, "the plant did not land on the real ruff row"
    (tmp_path / "pyproject.toml").write_text(planted, encoding="utf-8")

    assert unbounded_requirements(dev_requirements(tmp_path)) == ("ruff: no upper bound",)


def test_either_clause_removed_from_every_live_range_names_that_row() -> None:
    planted = 0
    for row in dev_requirements(REPO_ROOT):
        name = _NAME.match(row)
        assert name is not None
        head, tail = row[: name.end()], row[name.end() :]
        clauses = tail.split(",")
        if len(clauses) == 1:
            continue
        for kept, missing in zip(clauses, ("upper", "lower"), strict=True):
            planted += 1
            assert unbounded_requirements([head + kept]) == (
                f"{name.group(1)}: no {missing} bound",
            )
    assert planted, "no live row is a two-clause range, so this arm planted nothing"


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ("mypy==2.1.0", ()),
        ("mypy===2.1.0", ()),
        ("mypy~=2.1", ()),
        ("mypy>=2.1.0", ("mypy: no upper bound",)),
        ("mypy<3", ("mypy: no lower bound",)),
        ("ruff", ("ruff: no lower bound", "ruff: no upper bound")),
        ("ruff!=0.15.1", ("ruff: no lower bound", "ruff: no upper bound")),
        ("ruff>=0.13,!=0.15.1", ("ruff: no upper bound",)),
        ("ruff[extra]>=0.13,<0.16", ()),
        ("ruff[extra]", ("ruff: no lower bound", "ruff: no upper bound")),
        ("ruff>=0.13 ; python_version < '3.14'", ("ruff: no upper bound",)),
        ("ruff ; python_version >= '3.13'", ("ruff: no lower bound", "ruff: no upper bound")),
        ("ruff @ https://example.invalid/r.whl", ("ruff: no lower bound", "ruff: no upper bound")),
        ("pyyaml", ("pyyaml: no lower bound",)),
        ("PyYAML>=6.0", ()),
        ("py.yaml>=6.0", ("py.yaml: no upper bound",)),
        ("pytest-xdist>=3.8", ("pytest-xdist: no upper bound",)),
        ("=>not a name", ("=>not a name: not a readable requirement",)),
    ],
)
def test_a_row_grades_by_its_parsed_clauses(row: str, expected: tuple[str, ...]) -> None:
    assert unbounded_requirements([row]) == expected
