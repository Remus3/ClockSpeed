"""Tests for the item-notes index guard (j).

THE CRITERION GUARD (j) GRADES. `docs/item_notes.md` stopped holding item
bodies on 2026-08-25 and became an index over `docs/item_notes/`. An index is a
RESTATED FACT - the one thing CLAUDE.md section 4 says will drift - so it is
machine-checked in BOTH directions: a routed item with no section is red, a
section with no routing row is red, and a row naming the wrong leaf is red.

THE TWO HALVES ARE GRADED ON DIFFERENT MATERIAL, following the module that
grades guards (h) and (i). The FIRING half runs on synthetic families built
under tmp_path, because a plant has to be planted and planting into the tracked
docs/ would mean a test that edits the repository it is measuring. The GREEN
half runs on the REAL tree, because a fixture proves nothing about the file the
operator actually reads.

AN EMPTY FAMILY IS A SKIP, NOT A PASS, and that is the point of
``test_an_empty_family_is_a_skip_rather_than_a_vacuous_pass``. Session 40's
finding was that `assert count == 0` passes when the property holds AND when
nothing was measured, and the two produce byte-identical output. Every
equality this guard asserts is over a population that could be empty, so the
empty case is graded explicitly rather than left to satisfy the equality for
free.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"

GUARD_ID = "j"

INDEX_RELATIVE = "docs/item_notes.md"
LEAF_DIR_RELATIVE = "docs/item_notes"

_SECTION = re.compile(r"(?m)^## (CS-G?\d+)[ \t]*$")
_ROADMAP_PHASE = re.compile(r"^## (Phase \d+)")
_ROADMAP_ITEM = re.compile(r"^(CS-G?\d+) - ")

# The CS-8nn follow-up block's bounds, from ROADMAP.md's own ID-block rule:
# CS-4nn filled up at 98 of 100, so CS-8nn takes phase-4 residuals (operator
# decision 2026-08-21). These are the seams docs/item_notes/ splits phase 4 on.
#
# THE BLOCK ITSELF THEN SPLIT AT CS-850, so phase 4 is three leaves and there
# are two seams rather than one. See docs/adr/0011-the-cs-8nn-follow-up-leaf
# -splits-at-cs-850.md. The follow-up leaf reached 99 per cent of its budget
# with no closed section left to relocate - the same shape, one level down,
# that ADR 0010 split docs/item_notes.md for.
#
# THE SEAM NUMBER SPELLS THE LEAF NAME BELOW RATHER THAN BEING WRITTEN BESIDE
# IT. A hand-typed 'phase4-followups-850.md' next to a _SEAM of 850 is two
# copies of one fact with somewhere to drift to; deriving the name from the
# constant leaves the pair unable to disagree.
_FOLLOWUP_BLOCK_FIRST = 800
_FOLLOWUP_BLOCK_LIMIT = 900
_FOLLOWUP_LEAF_SEAM = 850

# THE SECOND FOLLOW-UP BLOCK. CS-8nn filled up at 100 of 100, measured
# 2026-09-05, so CS-9nn takes phase-4 residuals from there (operator decision
# 2026-09-05). Its leaf name is DERIVED from this constant for the same reason
# the seam above is: a hand-typed name beside a number is two copies of one
# fact with somewhere to drift to.
_SECOND_BLOCK_FIRST = 900


def _load_drift_guard() -> ModuleType:
    """Load tools/drift_guard.py by path.

    tools/ is not an importable package - it is a directory of entry-point
    scripts - so the module is loaded from its file.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location(
        "clockspeed_drift_guard_index", DRIFT_GUARD_SOURCE
    )
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()


# ---------------------------------------------------------------------------
# A family the guard can be pointed at
# ---------------------------------------------------------------------------

_INDEX_HEAD = """# Clockspeed - live per-item detail, index

**Section status: LIVE.** A dated heading in this file records provenance.

## Routing table

| Item | Leaf |
|---|---|
"""

_LEAF_HEAD = """# Clockspeed - live per-item detail, {leaf}

**Section status: LIVE.** A dated heading in this file records provenance.

---

"""


def _build(root: Path, leaves: dict[str, list[str]], rows: list[tuple[str, str]]) -> None:
    """Write a synthetic index plus leaves under ``root``.

    Args:
        root: The fabricated repository root.
        leaves: Leaf filename mapped to the item ids its sections carry.
        rows: The routing rows to write, as (item, leaf filename).
    """
    leaf_dir = root / LEAF_DIR_RELATIVE
    leaf_dir.mkdir(parents=True, exist_ok=True)
    for leaf, items in leaves.items():
        body = _LEAF_HEAD.format(leaf=leaf)
        for item in items:
            body += f"## {item}\n\nDetail for {item}.\n\n"
        (leaf_dir / leaf).write_text(body, encoding="utf-8")
    table = "".join(f"| {item} | `{LEAF_DIR_RELATIVE}/{leaf}` |\n" for item, leaf in rows)
    (root / INDEX_RELATIVE).write_text(_INDEX_HEAD + table, encoding="utf-8")


def _run(root: Path) -> tuple[str, str]:
    """Run guard (j) against ``root``.

    Args:
        root: The repository root under audit.

    Returns:
        (status, rendered detail).
    """
    guard, _skips = drift_guard.guard_index(root)
    assert guard["id"] == GUARD_ID, f"guard letter moved: {guard['id']}"
    return guard["status"], "\n".join(guard["detail"])


@pytest.fixture
def family(tmp_path: Path) -> Path:
    """A well-formed two-leaf family that the guard passes."""
    _build(
        tmp_path,
        {"phase4.md": ["CS-401", "CS-402"], "phase7.md": ["CS-701"]},
        [("CS-401", "phase4.md"), ("CS-402", "phase4.md"), ("CS-701", "phase7.md")],
    )
    return tmp_path


# ---------------------------------------------------------------------------
# The firing half - each plant is one way the index can lie
# ---------------------------------------------------------------------------


def test_a_well_formed_family_passes(family: Path) -> None:
    """The floor. Every plant below is measured against this being green."""
    status, rendered = _run(family)
    assert status == "PASS", rendered


def test_a_section_with_no_routing_row_is_red(family: Path) -> None:
    """A body nobody can find from the index. The commonest way to file wrong."""
    leaf = family / LEAF_DIR_RELATIVE / "phase4.md"
    leaf.write_text(leaf.read_text(encoding="utf-8") + "## CS-403\n\nUnrouted.\n", encoding="utf-8")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert "CS-403" in rendered


def test_a_routing_row_with_no_section_is_red(family: Path) -> None:
    """The other direction. A row that survives its item's closure."""
    index = family / INDEX_RELATIVE
    index.write_text(
        index.read_text(encoding="utf-8") + f"| CS-499 | `{LEAF_DIR_RELATIVE}/phase4.md` |\n",
        encoding="utf-8",
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert "CS-499" in rendered


def test_a_row_naming_the_wrong_leaf_is_red(family: Path) -> None:
    """Both sets match and the routing is still wrong - set equality alone misses this."""
    index = family / INDEX_RELATIVE
    index.write_text(
        index.read_text(encoding="utf-8").replace(
            f"| CS-701 | `{LEAF_DIR_RELATIVE}/phase7.md` |",
            f"| CS-701 | `{LEAF_DIR_RELATIVE}/phase4.md` |",
        ),
        encoding="utf-8",
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert "CS-701" in rendered


def test_an_item_body_written_into_the_index_is_red(family: Path) -> None:
    """The index holds no bodies. A body here is invisible to anyone following the table."""
    index = family / INDEX_RELATIVE
    index.write_text(
        index.read_text(encoding="utf-8") + "\n## CS-404\n\nA body in the index.\n",
        encoding="utf-8",
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert "CS-404" in rendered


def test_an_empty_family_is_a_skip_rather_than_a_vacuous_pass(tmp_path: Path) -> None:
    """Session 40's finding, applied to this guard's own equality.

    Zero routed items and zero sections satisfy every equality here. That has
    to be distinguishable from a family that was actually read, so it is a
    non-PASS that names itself in the skip list.
    """
    _build(tmp_path, {"phase4.md": []}, [])

    guard, skips = drift_guard.guard_index(tmp_path)
    assert guard["status"] != "PASS", "an empty family read as a pass - the equality was vacuous"
    assert skips, "an empty family produced no skip record, so nothing says it was never graded"


def test_a_missing_leaf_directory_is_a_skip_rather_than_a_failure(tmp_path: Path) -> None:
    """A wrong root is not drift. Guard (i) makes the same distinction."""
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / INDEX_RELATIVE).write_text(_INDEX_HEAD, encoding="utf-8")

    guard, skips = drift_guard.guard_index(tmp_path)
    assert guard["status"] == "WARN", "\n".join(guard["detail"])
    assert skips


# ---------------------------------------------------------------------------
# The green half - the REAL tree is the control and must be green, unedited
# ---------------------------------------------------------------------------


def _real_sections() -> dict[str, str]:
    """Return item id mapped to leaf filename, read from the tracked leaves."""
    out: dict[str, str] = {}
    for leaf in sorted((REPO_ROOT / LEAF_DIR_RELATIVE).glob("*.md")):
        for mark in _SECTION.finditer(leaf.read_text(encoding="utf-8")):
            out[mark.group(1)] = leaf.name
    return out


def _real_phases() -> dict[str, str]:
    """Return item id mapped to the ROADMAP phase heading that files it."""
    phase = None
    out: dict[str, str] = {}
    for line in (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8").splitlines():
        head = _ROADMAP_PHASE.match(line)
        if head:
            phase = head.group(1)
            continue
        item = _ROADMAP_ITEM.match(line)
        if item and phase is not None:
            out[item.group(1)] = phase
    return out


def test_the_real_tree_carries_sections_to_grade() -> None:
    """The floor under both real-tree controls below.

    Without this, an emptied family would make each of them pass while
    measuring nothing - which is the shape this module exists to refuse.
    """
    found = len(_real_sections())
    assert found > 0, "docs/item_notes/ carries no section - the controls below prove nothing"


def test_the_real_tree_index_is_green() -> None:
    """A proof must stay green when the defect is absent."""
    status, rendered = _run(REPO_ROOT)
    assert status == "PASS", rendered


def test_every_section_sits_in_the_leaf_the_membership_rule_names() -> None:
    """The membership rule, machine-checked against ROADMAP's own headings.

    The rule has ONE owner - the phase heading ROADMAP.md files an item under -
    and one stated exception, CS-501, which predates the CS-8nn block and is
    filed under phase 4. Anything else here means a body was hand-placed.

    PHASE 4 IS FOUR LEAVES AND THE RULE STAYS A DERIVATION FROM THE ID. It is
    computable from an item number alone and is deliberately not a table of
    which item lives where: a hand-listed mapping would have to be edited by
    the same hand that misplaces a body, so it would agree with the mistake.
    """
    sections = _real_sections()
    phases = _real_phases()
    assert sections, "no sections - this control proves nothing"

    misplaced: list[str] = []
    orphaned: list[str] = []
    for item, leaf in sorted(sections.items()):
        phase = phases.get(item)
        if phase is None:
            orphaned.append(f"{item} in {leaf}")
            continue
        digit = phase.split()[1]
        if digit == "4":
            number = int(item.split("-")[1])
            in_block = _FOLLOWUP_BLOCK_FIRST <= number < _FOLLOWUP_BLOCK_LIMIT
            if number >= _SECOND_BLOCK_FIRST:
                want = f"phase4-followups-{_SECOND_BLOCK_FIRST}.md"
            elif not in_block:
                want = "phase4.md"
            elif number < _FOLLOWUP_LEAF_SEAM:
                want = "phase4-followups.md"
            else:
                want = f"phase4-followups-{_FOLLOWUP_LEAF_SEAM}.md"
        else:
            want = f"phase{digit}.md"
        if leaf != want:
            misplaced.append(f"{item} sits in {leaf}, the rule says {want}")

    assert not orphaned, (
        "these carry detail but no OPEN line in ROADMAP.md - a closed item's detail "
        "moves to docs/history_notes.md, not to a leaf:\n" + "\n".join(orphaned)
    )
    assert not misplaced, "\n".join(misplaced)


def test_the_index_holds_no_item_body() -> None:
    """The tracked index, graded directly rather than only through the guard."""
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    found = [mark.group(1) for mark in _SECTION.finditer(text)]
    assert not found, f"{INDEX_RELATIVE} carries item bodies: {found}"
