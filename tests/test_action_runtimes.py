"""CS-990 - the arms over `tools/action_runtimes.py`.

WHAT THESE ARMS GRADE. That every action pin in every TRACKED workflow names a
version whose Node runtime GitHub still supports, over a population DERIVED from the
workflow files rather than transcribed into a list here.

WHY THE POPULATION IS DERIVED TWICE. A single derivation is graded by nothing. Two
derivations sharing a constant are graded by nothing either - they inherit the same
blind spot and agree for that reason, and agreement between two readings that cannot
disagree is not evidence. So one enumeration asks the YAML PARSER what the step
reference key resolves to and the other recognises a pin by its SHAPE in the raw
text, naming no key at all; a third arm below proves mechanically, off the AST, that
the two share no literal and read no module constant.

AND NEVER BY A FLOOR OVER THE PIN COUNT. A threshold summed over a population is met
by its strongest member - the CS-988 shape, which CS-990's item line forbids here by
name. The comparison is a MULTISET equality, which reddens on one pin appearing in
either reading and not the other.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import re
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GRADER_SOURCE = REPO_ROOT / "tools" / "action_runtimes.py"


def _load_grader() -> ModuleType:
    """Load the grader by PATH, because tools/ is not an importable package.

    tools/ is a directory of entry-point scripts with no __init__.py. Importing
    one as a package member makes mypy discover the same source under two module
    names and the repo-wide gate goes red on a duplicate - MEASURED on the first
    cut of this module, which is why this loader is here rather than an import.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_action_runtimes", GRADER_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {GRADER_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


action_runtimes = _load_grader()

# The planted workflow below carries this many pins, and the last arm plants it
# twice. Named rather than written inline so the arm reads as arithmetic over the
# fixture instead of a number nobody can re-derive.
GREEN_WORKFLOW_PINS = 2
PLANTED_COPIES = 2

# A whole workflow, small enough to read, carrying one pin whose runtime is current.
# The arms below mutate THIS text rather than the shipped files, so a planted defect
# can never reach the tree.
GREEN_WORKFLOW = """\
name: planted
on: [push]
jobs:
  only:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14'
      - run: python -m pytest tests -q
"""


def plant(root: Path, name: str, text: str) -> Path:
    directory = root / str(action_runtimes.WORKFLOW_DIRECTORY)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def green_tree(tmp_path: Path) -> Path:
    """A tree whose only workflow is clean, so a planted red is the plant's doing."""
    plant(tmp_path, "planted.yml", GREEN_WORKFLOW)
    assert action_runtimes.offences(tmp_path) == [], (
        "the fixture is not green before anything is planted"
    )
    return tmp_path


def test_no_tracked_workflow_pins_a_deprecated_runtime() -> None:
    """THE HEADLINE ARM. Every pin, every tracked workflow, graded by runtime."""
    found = action_runtimes.offences(REPO_ROOT)

    assert found == [], "tracked workflows carry deprecated action runtimes:\n" + "\n".join(
        f"  {offence}" for offence in found
    )


def test_the_graded_population_is_not_empty() -> None:
    """THE ANTI-VACUITY BOUND ON THE ARM ABOVE.

    An empty population satisfies every equality above for free, so a derivation
    that silently resolved nothing would read exactly like a clean tree.
    """
    assert action_runtimes.workflow_files(REPO_ROOT), "no tracked workflow was found"
    assert action_runtimes.derive_pins(REPO_ROOT), "enumeration one resolved no pin"
    assert action_runtimes.derive_pins_independently(REPO_ROOT), "enumeration two resolved no pin"


def test_the_two_enumerations_agree_as_multisets() -> None:
    """SET EQUALITY, not a floor - and a multiset, so a duplicate cannot go missing."""
    by_parse = Counter(action_runtimes.derive_pins(REPO_ROOT))
    by_scan = Counter(action_runtimes.derive_pins_independently(REPO_ROOT))

    only_parsed = by_parse - by_scan
    only_scanned = by_scan - by_parse

    assert by_parse == by_scan, (
        f"the two enumerations disagree. Resolved only by the parser: "
        f"{sorted(pin.spelling for pin in only_parsed.elements())}. Seen only by the "
        f"scan: {sorted(pin.spelling for pin in only_scanned.elements())}."
    )


def _source_tree(function: Callable[..., object]) -> ast.AST:
    return ast.parse(inspect.getsource(function).lstrip())


def _literals(function: Callable[..., object]) -> set[object]:
    return {
        node.value
        for node in ast.walk(_source_tree(function))
        if isinstance(node, ast.Constant) and node.value is not None
    }


def _module_level_names() -> set[str]:
    """EVERY module-level name, filtered by NOTHING but the dunders.

    The first cut filtered by type and the filter was the defect: a compiled
    `re.Pattern` is not a str, int, dict or tuple, so the one module constant an
    enumeration actually read was invisible and the assertion passed for the wrong
    reason. An oracle that cannot observe its subject passes BECAUSE it is blind.
    """
    return {name for name in vars(action_runtimes) if not name.startswith("__")}


def _names_read(function: Callable[..., object]) -> set[str]:
    """The module-level names this function reads, callees included."""
    module_level = _module_level_names()
    return {
        node.id
        for node in ast.walk(_source_tree(function))
        if isinstance(node, ast.Name) and node.id in module_level
    }


def _closure_literals(function: Callable[..., object]) -> set[object]:
    """This function's literals PLUS those of every module-level name it reads.

    Without the second half, factoring a shared pattern into a helper would defeat
    the whole proof while leaving both function bodies literal-free and disjoint.
    """
    found = _literals(function)
    for name in _names_read(function):
        target = getattr(action_runtimes, name)
        if callable(target) and hasattr(target, "__code__"):
            found |= _literals(target)
        elif isinstance(target, re.Pattern):
            found.add(target.pattern)
        elif isinstance(target, str):
            found.add(target)
    return found


def test_the_two_enumerations_share_no_constant() -> None:
    """THE CLAIM THE ITEM LINE MAKES, PROVEN OFF THE AST RATHER THAN ASSERTED.

    A comment saying two derivations are independent is worth nothing the first
    time somebody factors a shared pattern out of them. This reads both functions,
    follows every module-level name each one reaches for, and fails on any literal
    or any name the two hold in common.
    """
    module_level = _module_level_names()
    assert module_level, "the module exposes no names, so this proof would be vacuous"

    parse_literals = _closure_literals(action_runtimes.pins_by_parse)
    scan_literals = _closure_literals(action_runtimes.pins_by_scan)
    assert parse_literals, "enumeration one carries no literal, so the proof is vacuous"
    assert scan_literals, "enumeration two carries no literal, so the proof is vacuous"

    shared_literals = parse_literals & scan_literals
    assert not shared_literals, (
        f"the two enumerations share literals: {sorted(map(repr, shared_literals))}"
    )

    shared_names = _names_read(action_runtimes.pins_by_parse) & _names_read(
        action_runtimes.pins_by_scan
    )
    assert not shared_names, (
        f"the two enumerations share module-level names: {sorted(shared_names)}"
    )


def test_the_independence_proof_can_see_the_constant_each_enumeration_reads() -> None:
    """THE BOUND ON THE ARM ABOVE, and it is the arm that refuted the first cut.

    A disjointness check is satisfied for free by an oracle that reads nothing. So
    this pins the two distinguishing constants in place: enumeration one keys on the
    step-reference word and enumeration two must not carry it anywhere in its
    closure, and enumeration two's pattern must actually be visible to the proof.
    """
    parse_literals = _closure_literals(action_runtimes.pins_by_parse)
    scan_literals = _closure_literals(action_runtimes.pins_by_scan)

    assert "uses" in parse_literals, "enumeration one no longer keys on the step word"
    assert "uses" not in scan_literals, "enumeration two reached for the step word"
    assert action_runtimes.SLUG_LINE.pattern in scan_literals, (
        "the proof cannot see the pattern enumeration two is built on"
    )
    assert action_runtimes.SLUG_LINE.pattern not in parse_literals, (
        "enumeration one reached for enumeration two's pattern"
    )


def test_a_planted_deprecated_pin_reddens_the_grade(green_tree: Path) -> None:
    """THE ARM THE ACCEPTANCE NAMES. A pin below its supported major must be loud."""
    plant(green_tree, "planted.yml", GREEN_WORKFLOW.replace("checkout@v5", "checkout@v4"))

    found = action_runtimes.offences(green_tree)

    assert found, "a deprecated pin passed the grade"
    assert any("checkout@v4" in offence for offence in found), (
        f"the red does not name the planted pin: {found}"
    )


def test_a_pin_in_a_second_workflow_is_graded_too(green_tree: Path) -> None:
    """THE POPULATION IS THE DIRECTORY, not one named file.

    A defect that hides by moving to a new workflow file is the shape this project
    has already paid for elsewhere: a check anchored on one filename grades one file.
    """
    stale = GREEN_WORKFLOW.replace("setup-python@v6", "setup-python@v5")
    plant(green_tree, "second.yml", stale)

    found = action_runtimes.offences(green_tree)

    assert any("second.yml" in offence for offence in found), (
        f"a second workflow's deprecated pin was never graded: {found}"
    )


def test_an_action_the_record_does_not_name_is_a_loud_offence(green_tree: Path) -> None:
    """NO SILENT FORGIVENESS. An ungraded pin reddens rather than passing.

    A table that waves through what it does not recognise fails in the permissive
    direction and forgives a real deprecation forever with nothing red. A loud false
    positive beats a silent forgiveness, which is this project's recorded doctrine.
    """
    swapped = GREEN_WORKFLOW.replace("actions/checkout@v5", "vendor/thing@v1")
    plant(green_tree, "planted.yml", swapped)

    found = action_runtimes.offences(green_tree)

    assert any("vendor/thing@v1" in offence for offence in found), (
        f"an action outside the runtime table passed the grade: {found}"
    )


def test_a_ref_carrying_no_major_version_is_a_loud_offence(green_tree: Path) -> None:
    """A SHA OR A BRANCH NAMES NO RUNTIME, so it cannot be graded and must not pass."""
    plant(green_tree, "planted.yml", GREEN_WORKFLOW.replace("checkout@v5", "checkout@main"))

    found = action_runtimes.offences(green_tree)

    assert any("checkout@main" in offence for offence in found), (
        f"an ungradable ref passed the grade: {found}"
    )


def test_a_major_the_record_carries_no_reading_for_is_a_loud_offence(
    green_tree: Path,
) -> None:
    """AN ACTION THE RECORD NAMES IS NOT A MAJOR THE RECORD HAS READ.

    This is the exact shape that refuted the first cut of this module: a per-action
    threshold answered for every major of an action it named, including the ones
    nobody had measured. A per-major record cannot do that, and this arm is what
    holds it to it.
    """
    ahead = GREEN_WORKFLOW.replace("checkout@v5", "checkout@v99")
    plant(green_tree, "planted.yml", ahead)

    found = action_runtimes.offences(green_tree)

    assert any("checkout@v99" in offence for offence in found), (
        f"an unmeasured major passed the grade: {found}"
    )


def test_both_enumerations_see_a_planted_pin(green_tree: Path) -> None:
    """NEITHER READING IS A NO-OP, which their agreement alone would not show."""
    plant(green_tree, "second.yml", GREEN_WORKFLOW)

    by_parse = Counter(action_runtimes.derive_pins(green_tree))
    by_scan = Counter(action_runtimes.derive_pins_independently(green_tree))

    expected = PLANTED_COPIES * GREEN_WORKFLOW_PINS
    assert sum(by_parse.values()) == expected, f"enumeration one read {by_parse}"
    assert by_parse == by_scan, f"parser {by_parse} against scan {by_scan}"
