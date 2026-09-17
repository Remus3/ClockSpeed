"""Tests for the item-notes index guard (j).

THE CRITERION GUARD (j) GRADES. `docs/item_notes.md` stopped holding item
bodies on 2026-08-25 and became an index over `docs/item_notes/`. CS-1112
removed its per-item routing rows: routing is DERIVED from `ROADMAP.md` - the
item lines whose LAST field is a detail field, filed under a Phase heading -
through the leaf membership rule, which the index states as its leaf table and
`tools/drift_guard.py::item_notes_leaf` owns as code. The guard grades that
derivation against the sections in BOTH directions: a routed item with no
section in its derived leaf is red, a section nothing routes is red, a routing
row left in the index is red, and the index's rule table must agree with the
code at every seam, in both directions.

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

from tests.data.test_drift_guard_data import refused

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

# CS-1079 - THE FOUR-DIGIT IDS TOOK A LEAF OF THEIR OWN. The CS-9nn leaf had been
# an open-ended floor, so it went over its soft doc budget holding IDs its own
# selector did not name. Every phase 4 ID at CS-1000 or above now sits in the
# leaf this constant spells, and the CS-9nn leaf holds exactly its block.
_THIRD_BLOCK_FIRST = 1000


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

#: The leaf table's phase rows, spelled here as a FIXTURE rather than read from
#: the tracked index, so a plant into it never edits the repository.
_RULE_ROWS = (
    "| `docs/item_notes/phase4.md` | ROADMAP `Phase 4`, ID BELOW the `CS-8nn` block |\n"
    "| `docs/item_notes/phase4-followups.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block "
    "below CS-850 |\n"
    "| `docs/item_notes/phase4-followups-850.md` | ROADMAP `Phase 4`, ID in the `CS-8nn` block "
    "at or above CS-850 |\n"
    "| `docs/item_notes/phase4-followups-900.md` | ROADMAP `Phase 4`, ID in the `CS-9nn` block |\n"
    "| `docs/item_notes/phase4-followups-1000.md` | ROADMAP `Phase 4`, ID at or above CS-1000 |\n"
    "| `docs/item_notes/phase5.md` | ROADMAP `Phase 5` |\n"
    "| `docs/item_notes/phase6.md` | ROADMAP `Phase 6` |\n"
    "| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |\n"
)

_INDEX_HEAD = (
    "# Clockspeed - live per-item detail, index\n"
    "\n"
    "**Section status: LIVE.** A dated heading in this file records provenance.\n"
    "\n"
    "## Which leaf an item lands in\n"
    "\n"
    "| Leaf | Holds |\n"
    "|---|---|\n" + _RULE_ROWS + "\n## Rules every leaf obeys\n\nNone here.\n"
)

_LEAF_HEAD = """# Clockspeed - live per-item detail, {leaf}

**Section status: LIVE.** A dated heading in this file records provenance.

---

"""


ROADMAP_RELATIVE = "ROADMAP.md"


def _item_line(item: str, detail: str | None = "`docs/item_notes.md`") -> str:
    """Return one synthetic ROADMAP item line.

    Args:
        item: The item id.
        detail: The trailing detail field's target, or None for a line with no field.

    Returns:
        The line, newline-terminated.
    """
    line = f"{item} - a headline - acceptance: a condition - tier: 2"
    if detail is not None:
        line += f" - detail: {detail}"
    return line + "\n"


def _roadmap(phases: dict[str, list[str]]) -> str:
    """Return a synthetic ROADMAP.md whose phase headings file the given lines.

    Args:
        phases: Phase digit mapped to the ready-made item lines filed under it.

    Returns:
        The file text.
    """
    body = "# Roadmap - OPEN work only\n\nCS-nnn - <one line> - tier: <0|1|2>\n\n"
    for digit, lines in phases.items():
        body += f"## Phase {digit} - a phase\n\n" + "".join(lines) + "\n"
    return body


def _write_roadmap(root: Path, phases: dict[str, list[str]]) -> None:
    """Write a synthetic ROADMAP.md under ``root``.

    Args:
        root: The fabricated repository root.
        phases: Phase digit mapped to the item lines filed under it.
    """
    (root / ROADMAP_RELATIVE).write_text(_roadmap(phases), encoding="utf-8")


def _build(root: Path, leaves: dict[str, list[str]], routed: list[tuple[str, str]]) -> None:
    """Write a synthetic index plus leaves plus the ROADMAP.md that routes them.

    The index carries the leaf table and NO routing row. Each routed item gets a
    ROADMAP line with a trailing detail field, filed under the phase its leaf
    name spells, so a well-formed family agrees with the derivation. A test
    planting a ROADMAP disagreement overwrites it afterwards.

    Args:
        root: The fabricated repository root.
        leaves: Leaf filename mapped to the item ids its sections carry.
        routed: The items ROADMAP.md routes, as (item, leaf filename).
    """
    phases: dict[str, list[str]] = {}
    for item, leaf in routed:
        digit = leaf.removeprefix("phase")[0]
        phases.setdefault(digit, []).append(_item_line(item))
    _write_roadmap(root, phases)
    leaf_dir = root / LEAF_DIR_RELATIVE
    leaf_dir.mkdir(parents=True, exist_ok=True)
    for leaf, items in leaves.items():
        body = _LEAF_HEAD.format(leaf=leaf)
        for item in items:
            body += f"## {item}\n\nDetail for {item}.\n\n"
        (leaf_dir / leaf).write_text(body, encoding="utf-8")
    (root / INDEX_RELATIVE).write_text(_INDEX_HEAD, encoding="utf-8")


def _append_to_index(root: Path, text: str) -> None:
    """Append ``text`` to the synthetic index."""
    index = root / INDEX_RELATIVE
    index.write_text(index.read_text(encoding="utf-8") + text, encoding="utf-8")


def _replace_in_index(root: Path, old: str, new: str) -> None:
    """Replace exactly one occurrence of ``old`` in the synthetic index."""
    index = root / INDEX_RELATIVE
    text = index.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"plant anchor not unique: {old!r}"
    index.write_text(text.replace(old, new), encoding="utf-8")


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


def _no_section(item: str, leaf: str, elsewhere: str | None = None) -> str:
    """The exact line the restored no-section check prints for ``item``."""
    line = f"  {item} has no section in {LEAF_DIR_RELATIVE}/{leaf}"
    if elsewhere is not None:
        line += f", detail is in {LEAF_DIR_RELATIVE}/{elsewhere}"
    return line


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
# The firing half - each plant is one way the family can lie
# ---------------------------------------------------------------------------


def test_a_well_formed_family_passes(family: Path) -> None:
    """The floor. Every plant below is measured against this being green."""
    status, rendered = _run(family)
    assert status == "PASS", rendered


def test_a_section_no_detail_field_routes_is_red(family: Path) -> None:
    """A body nobody can find by the rule. The commonest way to file wrong."""
    leaf = family / LEAF_DIR_RELATIVE / "phase4.md"
    leaf.write_text(leaf.read_text(encoding="utf-8") + "## CS-403\n\nUnrouted.\n", encoding="utf-8")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  CS-403 in {LEAF_DIR_RELATIVE}/phase4.md" in rendered.splitlines(), rendered


def test_a_routed_item_with_no_section_anywhere_is_red(family: Path) -> None:
    """The other direction. A detail field that survives its section's removal."""
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402"), _item_line("CS-499")],
            "7": [_item_line("CS-701")],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert _no_section("CS-499", "phase4.md") in rendered.splitlines(), rendered


def test_a_section_in_a_leaf_other_than_the_derived_one_is_red(family: Path) -> None:
    """Both sets match and the placement is still wrong - set equality alone misses this."""
    phase4 = family / LEAF_DIR_RELATIVE / "phase4.md"
    phase7 = family / LEAF_DIR_RELATIVE / "phase7.md"
    phase7.write_text(_LEAF_HEAD.format(leaf="phase7.md"), encoding="utf-8")
    phase4.write_text(
        phase4.read_text(encoding="utf-8") + "## CS-701\n\nMisplaced.\n", encoding="utf-8"
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert _no_section("CS-701", "phase7.md", "phase4.md") in rendered.splitlines(), rendered


def test_an_item_body_written_into_the_index_is_red(family: Path) -> None:
    """The index holds no bodies. A body here is invisible to anyone following the rule."""
    _append_to_index(family, "\n## CS-404\n\nA body in the index.\n")

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
# CS-1112 - no routing row may come back
#
# The rows were removed because routing is derived. A row re-added by hand is a
# second owner of the same fact, so it is red even when it AGREES - an agreeing
# row is exactly the one nobody would notice drifting later.
# ---------------------------------------------------------------------------


def test_a_re_added_routing_row_is_red_even_when_it_agrees(family: Path) -> None:
    """The one row that agrees with everything is still a second owner."""
    _append_to_index(family, f"\n| CS-701 | `{LEAF_DIR_RELATIVE}/phase7.md` |\n")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  CS-701 has a routing row in {INDEX_RELATIVE}" in rendered.splitlines(), rendered


def test_a_routing_row_of_any_shape_is_red(family: Path) -> None:
    """A row is found by its FIRST cell, never by a well-formed leaf cell."""
    _append_to_index(family, "\n| CS-999 | somewhere |\n")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  CS-999 has a routing row in {INDEX_RELATIVE}" in rendered.splitlines(), rendered


@pytest.mark.parametrize(
    "row",
    [
        "| `CS-904` | somewhere |",
        "| **CS-904** | somewhere |",
        "| _CS-904_ | somewhere |",
        "   | CS-904 | somewhere |",
        "|CS-904|somewhere|",
        "| ` **CS-904** ` | somewhere |",
    ],
)
def test_a_routing_row_in_another_spelling_is_red(family: Path, row: str) -> None:
    """Backticks, emphasis and indentation do not stop a row being a routing row.

    The first cell is stripped of backticks, asterisks, underscores and
    whitespace before it is compared, so no markdown spelling of an id hides it.
    """
    _append_to_index(family, f"\n{row}\n")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  CS-904 has a routing row in {INDEX_RELATIVE}" in rendered.splitlines(), rendered


def test_a_routing_row_inside_the_leaf_table_is_red_and_not_a_rule(family: Path) -> None:
    """A spelled-around row planted AMONG the rule rows is a routing row, not a rule row."""
    phase7 = f"| `{LEAF_DIR_RELATIVE}/phase7.md` | ROADMAP `Phase 7` |\n"
    _replace_in_index(
        family, phase7, phase7 + f"  | **`CS-701`** | `{LEAF_DIR_RELATIVE}/phase7.md` |\n"
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    lines = rendered.splitlines()
    assert f"  CS-701 has a routing row in {INDEX_RELATIVE}" in lines, rendered
    assert "residue" not in rendered, rendered


def test_a_first_cell_that_only_mentions_an_id_is_not_a_routing_row(family: Path) -> None:
    """The paired control: the WHOLE stripped cell must be an id, not merely contain one."""
    _append_to_index(family, "\n| see CS-904 | somewhere |\n")

    status, rendered = _run(family)
    assert status == "PASS", rendered


# ---------------------------------------------------------------------------
# CS-1086 - routing is a DERIVATION from ROADMAP.md, graded against the sections
#
# The leaf is computed from ROADMAP's phase heading plus the ID block rule, and
# the routed set from the TRAILING detail field of each item line.
# ---------------------------------------------------------------------------


def _count_line(rendered: str) -> str:
    """Return the guard's routed-count detail line, or '' when it has none."""
    for line in rendered.splitlines():
        if line.startswith(f"routed items in {ROADMAP_RELATIVE}"):
            return line
    return ""


#: The block rule as a LITERAL table - both sides of every seam.
_SEAM_CASES = [
    ("CS-501", "4", "phase4.md"),
    ("CS-799", "4", "phase4.md"),
    ("CS-800", "4", "phase4-followups.md"),
    ("CS-849", "4", "phase4-followups.md"),
    ("CS-850", "4", "phase4-followups-850.md"),
    ("CS-899", "4", "phase4-followups-850.md"),
    ("CS-900", "4", "phase4-followups-900.md"),
    ("CS-999", "4", "phase4-followups-900.md"),
    ("CS-1000", "4", "phase4-followups-1000.md"),
    ("CS-1086", "4", "phase4-followups-1000.md"),
    ("CS-1127", "4", "phase4-followups-1000.md"),
    ("CS-950", "5", "phase5.md"),
    ("CS-701", "7", "phase7.md"),
]


@pytest.mark.parametrize(("item", "phase", "want"), _SEAM_CASES)
def test_the_leaf_rule_has_a_code_owner_at_every_seam(item: str, phase: str, want: str) -> None:
    """The block rule, as a LITERAL table rather than a second copy of the arithmetic.

    Both sides of every seam are pinned, so moving a seam by one ID reddens here.
    """
    assert drift_guard.item_notes_leaf(item, phase) == f"{LEAF_DIR_RELATIVE}/{want}"


@pytest.mark.parametrize(("item", "phase", "want"), _SEAM_CASES)
def test_the_real_index_text_alone_resolves_every_seam(item: str, phase: str, want: str) -> None:
    """The SAME literal table, resolved from the tracked index's text with no code rule.

    This is the single hop a reader takes: `docs/item_notes.md`'s leaf table,
    read as text, names the leaf. Were the table and the code to disagree at a
    seam, one of this arm and the code-owner arm above would redden.
    """
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    rules, problems = drift_guard.item_notes_rule_rows(text)
    assert not problems, problems
    assert drift_guard.item_notes_rule_leaves(rules, item, phase) == [f"{LEAF_DIR_RELATIVE}/{want}"]


def test_a_section_agreeing_with_a_leftover_row_but_not_the_derivation_is_red(
    tmp_path: Path,
) -> None:
    """The row and the section agree with EACH OTHER and both disagree with ROADMAP.

    Row-versus-section equality is satisfied, so only the derivation can see it,
    and the row is its own finding besides.
    """
    _build(
        tmp_path,
        {"phase4.md": ["CS-401", "CS-701"]},
        [("CS-401", "phase4.md"), ("CS-701", "phase7.md")],
    )
    _append_to_index(tmp_path, f"\n| CS-701 | `{LEAF_DIR_RELATIVE}/phase4.md` |\n")

    status, rendered = _run(tmp_path)
    assert status == "FAIL", rendered
    lines = rendered.splitlines()
    assert _no_section("CS-701", "phase7.md", "phase4.md") in lines, rendered
    assert f"  CS-701 has a routing row in {INDEX_RELATIVE}" in lines, rendered


def test_a_routed_item_with_no_section_in_its_computed_leaf_is_red(tmp_path: Path) -> None:
    """The derived leaf is one seam away from where the section sits.

    A section in ANY leaf is not enough - it must be in the leaf the rule computes,
    which is the file a reader following the rule opens. CS-1113 retired this
    check on a proof that leaned on the routing table; with the table gone the
    proof is false, so the check is restored and its own line is asserted.
    """
    _build(tmp_path, {"phase4-followups.md": ["CS-850"]}, [("CS-850", "phase4.md")])
    _write_roadmap(tmp_path, {"4": [_item_line("CS-850")]})

    status, rendered = _run(tmp_path)
    assert status == "FAIL", rendered
    assert (
        _no_section("CS-850", "phase4-followups-850.md", "phase4-followups.md")
        in rendered.splitlines()
    ), rendered


def test_a_detail_field_with_no_section_is_red(family: Path) -> None:
    """ROADMAP routes the item into a leaf that does not even exist yet.

    An absent leaf is not an unread one: nothing was refused, so the item is
    graded and red rather than skipped.
    """
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "6": [_item_line("CS-601")],
            "7": [_item_line("CS-701")],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert _no_section("CS-601", "phase6.md") in rendered.splitlines(), rendered
    assert "NOT READ" not in rendered, rendered


def test_a_section_whose_line_carries_no_detail_field_is_red(family: Path) -> None:
    """The other direction: a section exists and its ROADMAP line routes nothing."""
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "7": [_item_line("CS-701", detail=None)],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  CS-701 in {LEAF_DIR_RELATIVE}/phase7.md" in rendered.splitlines(), rendered


def test_the_detail_field_is_found_by_position_not_by_its_target(family: Path) -> None:
    """A trailing field whose target is NOT the index still routes the item.

    Matching the target narrows the population until it empties - measured
    doing that to CS-1026 - so an unusual target is exactly the member to keep.
    """
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "7": [_item_line("CS-701"), _item_line("CS-703", detail="see the phase leaf")],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert _no_section("CS-703", "phase7.md") in rendered.splitlines(), rendered


def test_a_detail_spelling_mid_line_does_not_route_the_item(family: Path) -> None:
    """The paired negative: the marker is a POSITION, so mid-line prose is not a field.

    The count line is the anti-narrowing control in the other direction - it
    must equal the trailing population exactly, never the substring population.
    """
    mid_line = (
        "CS-704 - a headline - detail: `docs/item_notes.md` - acceptance: a condition - tier: 2\n"
    )
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "7": [_item_line("CS-701"), mid_line],
        },
    )

    status, rendered = _run(family)
    assert status == "PASS", rendered
    assert "CS-704" not in rendered, rendered
    assert _count_line(rendered) == f"routed items in {ROADMAP_RELATIVE}: 3", rendered


def test_a_detail_field_naming_a_leaf_other_than_the_derived_one_is_red(family: Path) -> None:
    """Located by POSITION, then its TARGET must agree with the derivation.

    The index (the one hop ROADMAP.md prescribes) and the derived leaf itself
    both agree; any other target sends a reader somewhere the rule does not.
    CS-401 names its derived leaf and is the in-arm control that must stay silent.
    """
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401", detail="`docs/item_notes/phase4.md`"), _item_line("CS-402")],
            "7": [_item_line("CS-701", detail="`docs/item_notes/phase4.md`")],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    lines = rendered.splitlines()
    assert (
        f"  CS-701 detail: field names {LEAF_DIR_RELATIVE}/phase4.md, the rule derives "
        f"{LEAF_DIR_RELATIVE}/phase7.md and the index is {INDEX_RELATIVE}"
    ) in lines, rendered
    assert not [line for line in lines if line.startswith("  CS-401")], rendered


def test_a_second_detail_spelling_on_a_routed_line_is_red(family: Path) -> None:
    """A routed line spelling detail: twice carries two fields that can disagree.

    The spellings count is the control that sees it even where no id is named.
    """
    doubled = (
        "CS-701 - a headline - detail: `docs/item_notes/phase4.md` - "
        "acceptance: a condition - tier: 2 - detail: `docs/item_notes.md`\n"
    )
    _write_roadmap(
        family,
        {"4": [_item_line("CS-401"), _item_line("CS-402")], "7": [doubled]},
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    lines = rendered.splitlines()
    assert "  CS-701 spells detail: again before its trailing field" in lines, rendered
    assert f"detail: spellings on routed lines in {ROADMAP_RELATIVE}: 4" in lines, rendered


# ---------------------------------------------------------------------------
# CS-1112 - the restored no-section check, over EVERY placement
#
# CS-1113 retired "routed item has no section in its derived leaf" on a proof
# that every state it saw was also seen by a row check. The rows are gone, so
# that proof is false and the check is back. The arm enumerates every state a
# routed item's ROADMAP line and section can be in and asserts the VERDICT and
# the naming line on each, so deleting either direction reddens a combination.
# ---------------------------------------------------------------------------

#: Where a section can sit relative to CS-701's derived leaf, phase7.md.
_PLACES = {"absent": None, "derived": "phase7.md", "elsewhere": "phase4.md"}

#: What CS-701's ROADMAP line can be: routed (trailing field), unrouted (no
#: field), or absent (no line at all).
_LINES = ("routed", "unrouted", "absent")

#: The phrase only the no-section check prints.
NO_SECTION_LINE = "has no section in"


@pytest.mark.parametrize("section_at", sorted(_PLACES))
@pytest.mark.parametrize("line_at", _LINES)
def test_every_placement_of_a_routed_items_section_is_graded(
    tmp_path: Path, line_at: str, section_at: str
) -> None:
    """ROADMAP line and section of one item, each in every state it can take.

    CS-401 is a fully consistent control item in every combination, so the
    family is never empty and a FAIL is never about anything but CS-701. Only
    (routed, derived) and an unrouted-or-absent line with no section agree, and
    both must PASS - which stops this arm passing on a guard that fails everything.
    """
    section_leaf = _PLACES[section_at]
    leaves: dict[str, list[str]] = {"phase4.md": ["CS-401"], "phase7.md": []}
    if section_leaf is not None:
        leaves[section_leaf].append("CS-701")
    _build(tmp_path, leaves, [("CS-401", "phase4.md")])
    phases = {"4": [_item_line("CS-401")]}
    if line_at == "routed":
        phases["7"] = [_item_line("CS-701")]
    elif line_at == "unrouted":
        phases["7"] = [_item_line("CS-701", detail=None)]
    _write_roadmap(tmp_path, phases)

    status, rendered = _run(tmp_path)

    routed = line_at == "routed"
    agrees = (routed and section_at == "derived") or (not routed and section_at == "absent")
    assert status == ("PASS" if agrees else "FAIL"), rendered
    named = [line for line in rendered.splitlines() if line.startswith("  CS-701 ")]
    if agrees:
        assert not named, rendered
    elif routed:
        assert [line for line in named if NO_SECTION_LINE in line], rendered
    else:
        assert f"  CS-701 in {LEAF_DIR_RELATIVE}/{section_leaf}" in named, rendered


def test_an_unreadable_roadmap_is_a_warn_never_a_pass(family: Path) -> None:
    """Could-not-look must not read as clean: nothing was routed."""
    (family / ROADMAP_RELATIVE).unlink()

    guard, skips = drift_guard.guard_index(family)
    assert guard["status"] == "WARN", "\n".join(guard["detail"])
    assert any(skip["path"] == ROADMAP_RELATIVE for skip in skips), skips


# ---------------------------------------------------------------------------
# CS-1112 - the index's leaf table is BOUND to item_notes_leaf, both directions
#
# The table is what a reader follows; the code is what the guard derives with.
# Every row's range is probed at both ends and every code seam is probed on
# both sides, so a seam moved in EITHER copy reddens.
# ---------------------------------------------------------------------------


def test_a_table_seam_moved_away_from_the_code_is_red(family: Path) -> None:
    """The table says CS-860; the code says CS-850."""
    _replace_in_index(family, "block below CS-850", "block below CS-860")
    _replace_in_index(family, "block at or above CS-850", "block at or above CS-860")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 4 CS-850: the leaf table names {LEAF_DIR_RELATIVE}/phase4-followups.md, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase4-followups-850.md"
    ) in rendered.splitlines(), rendered


def test_a_code_seam_moved_away_from_the_table_is_red(
    family: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other direction: the code moves, the table stays, the probe follows the code."""
    monkeypatch.setattr(drift_guard, "_ITEM_NOTES_FOLLOWUP_SEAM", 860)

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 4 CS-859: the leaf table names {LEAF_DIR_RELATIVE}/phase4-followups-850.md, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase4-followups.md"
    ) in rendered.splitlines(), rendered


def test_a_table_floor_moved_away_from_the_code_is_red(family: Path) -> None:
    """CS-1079. The table's open-ended floor says CS-1100; the code says CS-1000."""
    _replace_in_index(family, "ID at or above CS-1000 |", "ID at or above CS-1100 |")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 4 CS-1000: the leaf table names 0 leaves, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase4-followups-{_THIRD_BLOCK_FIRST}.md"
    ) in rendered.splitlines(), rendered


def test_a_code_floor_moved_away_from_the_table_is_red(
    family: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1079, the other direction: the code's floor moves, the probe follows it."""
    monkeypatch.setattr(drift_guard, "_ITEM_NOTES_THIRD_BLOCK_FIRST", 1100)

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 4 CS-1100: the leaf table names "
        f"{LEAF_DIR_RELATIVE}/phase4-followups-{_THIRD_BLOCK_FIRST}.md, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase4-followups-1100.md"
    ) in rendered.splitlines(), rendered


def test_a_routed_phase_the_table_does_not_cover_is_red(family: Path) -> None:
    """A phase with a routed item and no rule row resolves to nothing from the index."""
    _replace_in_index(family, "| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |\n", "")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 7 CS-701: the leaf table names 0 leaves, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase7.md"
    ) in rendered.splitlines(), rendered


def test_a_rule_row_naming_the_wrong_leaf_is_red(family: Path) -> None:
    """The table routes phase 7 into phase 6's leaf."""
    _replace_in_index(
        family,
        "| `docs/item_notes/phase7.md` | ROADMAP `Phase 7` |",
        "| `docs/item_notes/phase6.md` | ROADMAP `Phase 7` |",
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  Phase 7 CS-701: the leaf table names {LEAF_DIR_RELATIVE}/phase6.md, "
        f"item_notes_leaf derives {LEAF_DIR_RELATIVE}/phase7.md"
    ) in rendered.splitlines(), rendered


def test_an_unparseable_rule_row_is_red(family: Path) -> None:
    """A row the parser cannot read is never skipped - it would be a hole in the binding."""
    _replace_in_index(
        family,
        "| `docs/item_notes/phase5.md` | ROADMAP `Phase 5` |",
        "| `docs/item_notes/phase5.md` | whatever phase five is |",
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  {LEAF_DIR_RELATIVE}/phase5.md: unparsed residue in rule row - 'whatever phase five is'"
    ) in rendered.splitlines(), rendered


#: Rule rows that PASSED at 8d13134: each carries a clause the parser did not
#: recognise and silently ignored, so the row read as a whole-phase rule while a
#: reader following its words finds no leaf for some ids. Grammar is an ALLOWLIST.
_RESIDUE_PLANTS = [
    (
        "| `docs/item_notes/phase5.md` | ROADMAP `Phase 5` |",
        "| `docs/item_notes/phase5.md` | ROADMAP `Phase 5`, ID BELOW CS-1000 only |",
        "phase5.md",
        ", ID BELOW CS-1000 only",
    ),
    (
        "| `docs/item_notes/phase6.md` | ROADMAP `Phase 6` |",
        "| `docs/item_notes/phase6.md` | ROADMAP `Phase 6` except the `CS-9nn` block |",
        "phase6.md",
        " except the `CS-9nn` block",
    ),
    (
        "block below CS-850 |",
        "block below CS-850 or so |",
        "phase4-followups.md",
        " or so",
    ),
    (
        "ID in the `CS-9nn` block |",
        "ID in the `CS-9nn` block, mostly |",
        "phase4-followups-900.md",
        ", mostly",
    ),
    (
        "ID at or above CS-1000 |",
        "ID at or above CS-1000, mostly |",
        "phase4-followups-1000.md",
        ", mostly",
    ),
    # CS-1079 retired the "sends up" clause with the open-ended CS-9nn leaf it
    # existed to spell. The closed grammar no longer carries it, so re-spelling
    # the retired phase4.md row is residue rather than a silent rule.
    (
        "ID BELOW the `CS-8nn` block |",
        "ID BELOW the `CS-8nn` block. NOT the `CS-10nn` block - the rule sends every "
        "phase 4 ID at 900 or higher to the `CS-9nn` leaf |",
        "phase4.md",
        ". NOT the `CS-10nn` block - the rule sends every phase 4 ID at 900 or higher "
        "to the `CS-9nn` leaf",
    ),
]

# CS-1079 repair. EVERY PLANT ABOVE APPENDS JUNK AT THE END, so a grammar
# loosened at the START or in the MIDDLE of a clause - a case-insensitive
# keyword, a run of whitespace, a space after `CS-` - survived all of them.
#
# WHAT THIS COVERS IS ONE POSITION PER PERTURBATION, NOT EVERY POSITION. Each
# comment below names the exact spots its form is perturbed at. A keyword, a
# space or a case change anywhere ELSE in a row is not planted here, so a grammar
# loosened only at an unplanted spot still passes this arm - the older forms'
# mid-row looseness is a separate row, not this one. CS-1079's floor form is
# planted at the most spots, and those plants kill the M8 and M12 mutants that
# loosen its comma, its keyword case, its word spacing and its `CS-` joint.
#
# A LEADING ZERO IS REFUSED in an id NUMBER rather than read as the same id:
# `CS-01000` is a spelling no reader or search for `CS-1000` finds. The BLOCK
# spelling `CS-0nn` is the one real zero-led name and stays accepted.
#
# Each entry is (anchor, the anchor perturbed, leaf, the residue it leaves).
_P4 = "ROADMAP `Phase 4`"
_LOOSENING = [
    # The phase-only form: a doubled space after ROADMAP, ROADMAP lowercased, Phase
    # lowercased.
    ("ROADMAP `Phase 5` |", "ROADMAP  `Phase 5` |", "phase5.md", "ROADMAP  `Phase 5`"),
    ("ROADMAP `Phase 5` |", "roadmap `Phase 5` |", "phase5.md", "roadmap `Phase 5`"),
    ("ROADMAP `Phase 5` |", "ROADMAP `phase 5` |", "phase5.md", "ROADMAP `phase 5`"),
    # ", ID BELOW the `CS-nnn` block": a doubled space after the comma, BELOW
    # lowercased, a doubled space before the backtick, a space after CS-, a
    # zero-led block other than `CS-0nn`.
    *(
        (f"{_P4}, ID BELOW the `CS-8nn` block |", f"{_P4}{clause} |", "phase4.md", clause)
        for clause in (
            ",  ID BELOW the `CS-8nn` block",
            ", ID below the `CS-8nn` block",
            ", ID BELOW the  `CS-8nn` block",
            ", ID BELOW the `CS- 8nn` block",
            ", ID BELOW the `CS-08nn` block",
        )
    ),
    # ", ID in the `CS-nnn` block below CS-n": in the narrowing, a doubled space
    # before CS-, below uppercased, a space after CS-, a leading zero in the id;
    # in the block clause, IN uppercased, a space after CS-, a zero-led block.
    *(
        (
            "`CS-8nn` block below CS-850 |",
            f"{perturbed} |",
            "phase4-followups.md",
            residue,
        )
        for perturbed, residue in (
            ("`CS-8nn` block below  CS-850", " below  CS-850"),
            ("`CS-8nn` block BELOW CS-850", " BELOW CS-850"),
            ("`CS-8nn` block below CS- 850", " below CS- 850"),
            ("`CS-8nn` block below CS-0850", " below CS-0850"),
        )
    ),
    *(
        (
            f"{_P4}, ID in the `CS-8nn` block below CS-850 |",
            f"{_P4}{clause} |",
            "phase4-followups.md",
            clause,
        )
        for clause in (
            ", ID IN the `CS-8nn` block below CS-850",
            ", ID in the `CS- 8nn` block below CS-850",
            ", ID in the `CS-08nn` block below CS-850",
        )
    ),
    # ", ID in the `CS-nnn` block at or above CS-n": a doubled space between or and
    # above, at uppercased, a space after CS-, a leading zero in the id.
    *(
        (
            "`CS-8nn` block at or above CS-850 |",
            f"`CS-8nn` block{residue} |",
            "phase4-followups-850.md",
            residue,
        )
        for residue in (
            " at or  above CS-850",
            " AT or above CS-850",
            " at or above CS- 850",
            " at or above CS-0850",
        )
    ),
    # ", ID in the `CS-nnn` block" alone: a doubled space after in, a zero-led block.
    *(
        (
            f"{_P4}, ID in the `CS-9nn` block |",
            f"{_P4}{clause} |",
            "phase4-followups-900.md",
            clause,
        )
        for clause in (
            ", ID in  the `CS-9nn` block",
            ", ID in the `CS-09nn` block",
        )
    ),
    # CS-1079's floor form, ", ID at or above CS-n": a doubled space and no space
    # after the comma, ID lowercased, a doubled space after at, a space after CS-,
    # CS lowercased, a leading zero in the id.
    *(
        (f"{_P4}, ID at or above CS-1000 |", f"{_P4}{clause} |", "phase4-followups-1000.md", clause)
        for clause in (
            ",  ID at or above CS-1000",
            ",ID at or above CS-1000",
            ", id at or above CS-1000",
            ", ID at  or above CS-1000",
            ", ID at or above CS- 1000",
            ", ID at or above cs-1000",
            ", ID at or above CS-01000",
        )
    ),
]


@pytest.mark.parametrize(("old", "new", "leaf", "residue"), _RESIDUE_PLANTS + _LOOSENING)
def test_a_rule_row_clause_outside_the_grammar_is_red(
    family: Path, old: str, new: str, leaf: str, residue: str
) -> None:
    """Every Holds cell must parse COMPLETELY; any unparsed residue is named and red."""
    _replace_in_index(family, old, new)

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  {LEAF_DIR_RELATIVE}/{leaf}: unparsed residue in rule row - {residue!r}"
    ) in rendered.splitlines(), rendered


#: `CS-0nn` is the real block name of CS-001 to CS-007, so a zero BLOCK is a
#: spelling the grammar accepts - in both block forms - while a zero-led id is not.
_ZERO_BLOCK_ROWS = [
    ("ROADMAP `Phase 5`, ID in the `CS-0nn` block", 0, 100),
    ("ROADMAP `Phase 5`, ID BELOW the `CS-0nn` block", 0, 0),
    ("ROADMAP `Phase 5`, ID in the `CS-0nn` block below CS-5", 0, 5),
]


@pytest.mark.parametrize(("holds", "low", "high"), _ZERO_BLOCK_ROWS)
def test_the_cs_0nn_block_spelling_parses(holds: str, low: int, high: int) -> None:
    """CS-1079 pass 2. The leading-zero refusal is for id NUMBERS, never the `CS-0nn` block."""
    text = (
        f"{drift_guard.ITEM_NOTES_RULE_HEADING}\n\n| Leaf | Holds |\n|---|---|\n"
        f"| `docs/item_notes/phase5.md` | {holds} |\n"
    )
    rules, problems = drift_guard.item_notes_rule_rows(text)
    assert not problems, problems
    assert [(rule.phase, rule.low, rule.high) for rule in rules] == [("5", low, high)]


@pytest.mark.parametrize(
    "holds",
    [
        "ROADMAP `Phase 5`, ID in the `CS-00nn` block",
        "ROADMAP `Phase 5`, ID in the `CS-0nn` block below CS-05",
        "ROADMAP `Phase 5`, ID at or above CS-0",
    ],
)
def test_a_zero_led_id_beside_the_cs_0nn_block_is_refused(holds: str) -> None:
    """CS-1079 pass 2. Accepting `CS-0nn` must not re-admit `CS-00nn`, `CS-05` or `CS-0`."""
    text = (
        f"{drift_guard.ITEM_NOTES_RULE_HEADING}\n\n| Leaf | Holds |\n|---|---|\n"
        f"| `docs/item_notes/phase5.md` | {holds} |\n"
    )
    rules, problems = drift_guard.item_notes_rule_rows(text)
    assert rules == [], rules
    problem_count = len(problems)
    assert problem_count == 1, problems
    assert "unparsed residue in rule row" in problems[0], problems


def test_an_annex_row_outside_the_grammar_is_red(family: Path) -> None:
    """An ANNEX row has a fixed lead too, so a near-miss is not waved through as an annex."""
    phase7 = f"| `{LEAF_DIR_RELATIVE}/phase7.md` | ROADMAP `Phase 7` |\n"
    _replace_in_index(
        family, phase7, phase7 + f"| `{LEAF_DIR_RELATIVE}/{_ANNEX_NAME}` | ANNEXED |\n"
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert (
        f"  {LEAF_DIR_RELATIVE}/{_ANNEX_NAME}: unparsed residue in rule row - 'ANNEXED'"
    ) in rendered.splitlines(), rendered


def test_an_index_with_no_leaf_table_is_red(family: Path) -> None:
    """Routed items and no table: a reader has no hop to take."""
    _replace_in_index(family, "## Which leaf an item lands in", "## Something else")

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"{INDEX_RELATIVE} carries no leaf table under" in rendered, rendered


def test_a_leaf_file_no_table_row_names_is_red(family: Path) -> None:
    """Both directions over FILES too: a leaf on disk the table never mentions."""
    (family / LEAF_DIR_RELATIVE / "phase8.md").write_text(
        _LEAF_HEAD.format(leaf="phase8.md"), encoding="utf-8"
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  {LEAF_DIR_RELATIVE}/phase8.md" in rendered.splitlines(), rendered


#: A synthetic annex. Its row is composed, never spelled, because the path does
#: not exist in the tree and a spelled one reads as a fixture literal citation.
_ANNEX_NAME = "record.md"


def _add_annex_row(root: Path) -> None:
    """Add an ANNEX row for the synthetic annex to the index's leaf table."""
    phase7 = f"| `{LEAF_DIR_RELATIVE}/phase7.md` | ROADMAP `Phase 7` |\n"
    annex = f"| `{LEAF_DIR_RELATIVE}/{_ANNEX_NAME}` | ANNEX, not a phase leaf - a record |\n"
    _replace_in_index(root, phase7, phase7 + annex)


def test_an_annex_row_naming_a_file_that_carries_a_section_is_red(family: Path) -> None:
    """An ANNEX holds no item section; a body there is found by no rule."""
    _add_annex_row(family)
    (family / LEAF_DIR_RELATIVE / _ANNEX_NAME).write_text(
        "## CS-402\n\nA body.\n", encoding="utf-8"
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert f"  {LEAF_DIR_RELATIVE}/{_ANNEX_NAME} holds a section for CS-402" in rendered, rendered


def test_an_annex_row_with_no_section_passes(family: Path) -> None:
    """The paired control: a real annex is named by its row and carries no section."""
    _add_annex_row(family)
    (family / LEAF_DIR_RELATIVE / _ANNEX_NAME).write_text("# A record\n", encoding="utf-8")

    status, rendered = _run(family)
    assert status == "PASS", rendered


# ---------------------------------------------------------------------------
# CS-1115 - a leaf that EXISTS but cannot be read is could-not-look, not absent
#
# `item_notes_sections` caught OSError on a leaf and CONTINUED, so the leaf's
# sections vanished and its routed items read as items with no section. Every
# fault below is REAL - an exclusive Windows handle, or a mode of zero - held
# by `refused`, which a stub cannot stand in for: a stub is a statement about
# the stub, while this is the whole read path meeting the operating system.
# ---------------------------------------------------------------------------


def test_an_unreadable_leaf_is_a_warn_naming_it_never_a_silent_skip(family: Path) -> None:
    """The CS-1115 acceptance arm, at the guard: WARN, not advisory, the leaf named."""
    leaf = family / LEAF_DIR_RELATIVE / "phase7.md"
    relative = f"{LEAF_DIR_RELATIVE}/phase7.md"

    with refused(leaf):
        assert leaf.is_file(), "control: the refused leaf no longer stats as a file"
        with pytest.raises(PermissionError):
            leaf.read_bytes()
        guard, skips = drift_guard.guard_index(family)

    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert f"{relative} NOT READ" in rendered, rendered
    assert any(skip["path"] == relative for skip in skips), skips
    assert "  CS-701" not in rendered, "an item routed to the unread leaf was graded as missing"


def test_an_unreadable_leaf_does_not_hide_drift_in_a_leaf_that_was_read(family: Path) -> None:
    """The fault narrows what is graded; it never pardons what WAS read."""
    phase4 = family / LEAF_DIR_RELATIVE / "phase4.md"
    phase4.write_text(
        phase4.read_text(encoding="utf-8") + "## CS-403\n\nUnrouted.\n", encoding="utf-8"
    )

    with refused(family / LEAF_DIR_RELATIVE / "phase7.md"):
        status, rendered = _run(family)

    assert status == "FAIL", rendered
    assert "CS-403" in rendered
    assert f"{LEAF_DIR_RELATIVE}/phase7.md NOT READ" in rendered, rendered


def test_a_routed_item_with_no_section_in_a_read_leaf_still_fails_beside_an_unread_one(
    tmp_path: Path,
) -> None:
    """Only items derived INTO the unread leaf go ungraded; a missing section elsewhere is red.

    The rule table agrees with every routed item here, so the no-section check
    is the only thing that can make this FAIL.
    """
    _build(
        tmp_path,
        {"phase4.md": ["CS-401"], "phase7.md": ["CS-701"]},
        [("CS-401", "phase4.md"), ("CS-402", "phase4.md"), ("CS-701", "phase7.md")],
    )
    assert _run(tmp_path)[0] == "FAIL", (
        "control: the missing section is not red with nothing refused"
    )

    with refused(tmp_path / LEAF_DIR_RELATIVE / "phase7.md"):
        status, rendered = _run(tmp_path)

    assert status == "FAIL", rendered
    assert _no_section("CS-402", "phase4.md") in rendered.splitlines(), rendered
    assert "  CS-701 " not in rendered, rendered


def test_a_directory_carrying_a_leaf_name_is_its_own_finding_not_a_read_failure(
    family: Path,
) -> None:
    """A directory named like a leaf is a tree shape the family forbids - graded, not unread.

    Reading it raises, and CS-1115's first cut reported that as an unreadable
    leaf and made the run UNGRADED, which names the wrong defect.
    """
    (family / LEAF_DIR_RELATIVE / "phase9.md").mkdir()

    status, rendered = _run(family)

    assert status == "FAIL", rendered
    assert f"{LEAF_DIR_RELATIVE}/phase9.md is a directory, not a leaf" in rendered, rendered
    assert "NOT READ" not in rendered, rendered


def test_an_unlistable_leaf_directory_is_a_warn_never_a_fail(family: Path) -> None:
    """The sibling one level up: a refused listing globbed as zero leaves, silently."""
    leaf_dir = family / LEAF_DIR_RELATIVE

    with refused(leaf_dir):
        assert leaf_dir.is_dir(), "control: the refused directory no longer stats"
        with pytest.raises(PermissionError):
            list(leaf_dir.iterdir())
        guard, skips = drift_guard.guard_index(family)

    rendered = "\n".join(guard["detail"])
    assert guard["status"] == "WARN", rendered
    assert guard["advisory"] is False, rendered
    assert f"{LEAF_DIR_RELATIVE} NOT READ" in rendered, rendered
    assert any(skip["path"] == LEAF_DIR_RELATIVE for skip in skips), skips


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


def _real_trailing() -> set[str]:
    """Return the ROADMAP item ids whose LAST field is a detail field, counted test-side."""
    trailing: set[str] = set()
    for line in (REPO_ROOT / ROADMAP_RELATIVE).read_text(encoding="utf-8").splitlines():
        item = _ROADMAP_ITEM.match(line)
        if item and line.rsplit(" - ", 1)[-1].startswith("detail:"):
            trailing.add(item.group(1))
    return trailing


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

    PHASE 4 IS FIVE LEAVES AND THE RULE STAYS A DERIVATION FROM THE ID. It is
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
            if number >= _THIRD_BLOCK_FIRST:
                want = f"phase4-followups-{_THIRD_BLOCK_FIRST}.md"
            elif number >= _SECOND_BLOCK_FIRST:
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


def test_every_real_routed_id_resolves_to_its_section_from_the_index_text_alone() -> None:
    """The CS-1112 acceptance, on the real tree, with NO call to the code rule.

    Each routed id's leaf is read out of `docs/item_notes.md`'s leaf table as
    text, and its section must sit in exactly that leaf. The resolved count is
    held equal to a test-side count of trailing detail fields, so a narrowed
    population shows as a short count rather than a green arm.
    """
    trailing = _real_trailing()
    phases = _real_phases()
    sections = _real_sections()
    rules, problems = drift_guard.item_notes_rule_rows(
        (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    )
    assert not problems, problems
    assert trailing, "ROADMAP.md carries no trailing detail field - this arm proves nothing"

    resolved: list[str] = []
    unresolved: list[str] = []
    for item in sorted(trailing):
        digit = phases[item].split()[1]
        leaves = drift_guard.item_notes_rule_leaves(rules, item, digit)
        if len(leaves) == 1 and leaves[0] == f"{LEAF_DIR_RELATIVE}/{sections.get(item)}":
            resolved.append(item)
        else:
            unresolved.append(f"{item}: table names {leaves}, section in {sections.get(item)}")
    resolved_count = len(resolved)
    trailing_count = len(trailing)
    assert not unresolved, "\n".join(unresolved)
    assert resolved_count == trailing_count, "resolved fewer ids than ROADMAP routes"


def test_every_real_leaf_selector_describes_the_ids_its_leaf_holds() -> None:
    """CS-1079. Each phase row's selector, read as text, names every section its leaf holds.

    The CS-9nn row once read as its block while the leaf also held four-digit IDs
    through a clause on ANOTHER row, so a split on the declared selector moved
    nothing. Here each section is resolved from the index text alone, and must
    resolve to exactly the leaf it sits in; a phase 4 section count of zero
    proves nothing and is refused.
    """
    sections = _real_sections()
    phases = _real_phases()
    rules, problems = drift_guard.item_notes_rule_rows(
        (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    )
    assert not problems, problems
    phase4 = sorted(item for item in sections if phases.get(item, "").endswith(" 4"))
    phase4_count = len(phase4)
    assert phase4_count > 0, "no phase 4 section - this arm proves nothing"

    wrong: list[str] = []
    for item, leaf in sorted(sections.items()):
        phase = phases.get(item)
        if phase is None:
            continue
        named = drift_guard.item_notes_rule_leaves(rules, item, phase.split()[1])
        if named != [f"{LEAF_DIR_RELATIVE}/{leaf}"]:
            wrong.append(f"{item} sits in {leaf}, its selector names {named}")
    assert not wrong, "\n".join(wrong)


def test_the_real_tree_routed_count_matches_an_independent_count() -> None:
    """The anti-narrowing control on the REAL tree.

    The guard's routed count must equal a test-side count of ROADMAP item lines
    whose LAST field is a detail field, and both must equal the sections.
    A narrowed domain shows up as a short count AND as enumerated ids.
    DISCLOSED BLIND SPOT: every real field names the same target, so this arm
    cannot see a target-matching narrowing; the synthetic position arms carry that.
    """
    trailing = _real_trailing()
    sections = _real_sections()
    assert trailing, "ROADMAP.md carries no trailing detail field - this control proves nothing"

    _status, rendered = _run(REPO_ROOT)
    assert _count_line(rendered) == f"routed items in {ROADMAP_RELATIVE}: {len(trailing)}", rendered
    spellings = f"detail: spellings on routed lines in {ROADMAP_RELATIVE}: {len(trailing)}"
    assert spellings in rendered.splitlines(), rendered
    assert trailing == set(sections), (
        f"detail field, no section: {sorted(trailing - set(sections))}; "
        f"section, no detail field: {sorted(set(sections) - trailing)}"
    )


def test_the_index_holds_no_item_body() -> None:
    """The tracked index, graded directly rather than only through the guard."""
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    found = [mark.group(1) for mark in _SECTION.finditer(text)]
    assert not found, f"{INDEX_RELATIVE} carries item bodies: {found}"


def test_the_index_holds_no_routing_row() -> None:
    """The tracked index, graded directly: CS-1112 removed every row."""
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    rows = re.findall(r"(?m)^\|\s*(CS-G?\d+)\s*\|", text)
    assert not rows, f"{INDEX_RELATIVE} carries routing rows: {rows}"


# ---------------------------------------------------------------------------
# CS-1112 - the three descriptions of routing say the same thing as the guard
#
# CLAUDE.md section 4, CONVENTIONS.md section 2, and the lane prompt each tell
# a reader how an item is routed. Each is tied to the guard's own constants, so
# a guard that renames the rule, or a doc that goes back to a table, reddens.
# ---------------------------------------------------------------------------

#: The lane prompt states routing twice - step 4c and the doc topology list.
PROMPT_ROUTING_SITES = 2

_OWNS_CELL = "The INDEX over `docs/item_notes/` - the {rule} plus the rules every leaf obeys"


def _topology_row(relative: str) -> str:
    """Return the `docs/item_notes.md` row of ``relative``'s ownership table."""
    for line in (REPO_ROOT / relative).read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| `{INDEX_RELATIVE}` |"):
            return line
    return ""


@pytest.mark.parametrize("relative", ["CLAUDE.md", "CONVENTIONS.md"])
def test_the_topology_row_names_the_rule_the_guard_binds(relative: str) -> None:
    """The Owns cell spells the guard's rule name, and no table of rows."""
    row = _topology_row(relative)
    assert row, f"{relative} has no {INDEX_RELATIVE} ownership row"
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    assert cells[1] == _OWNS_CELL.format(rule=drift_guard.ITEM_NOTES_RULE_NAME), row
    assert "routing table" not in row, row
    assert "per-item routing row" in cells[2], row


def test_the_lane_prompt_routes_by_the_rule_the_guard_binds() -> None:
    """Both prompt sentences name the rule and the index, and no routing table."""
    text = " ".join((REPO_ROOT / "tools" / "headless-queue.md").read_text(encoding="utf-8").split())
    phrase = f"by the {drift_guard.ITEM_NOTES_RULE_NAME} in `{INDEX_RELATIVE}`"
    found = text.count(phrase)
    assert found == PROMPT_ROUTING_SITES, (
        f"expected the routing phrase at both sites, found {found}"
    )
    assert "routing table" not in text
    assert "routed by the table" not in text


def test_the_annex_row_describes_what_the_annex_now_holds() -> None:
    """CS-1112 left the rule table here; the annex keeps only the seam reasoning."""
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith(f"| `{LEAF_DIR_RELATIVE}/leaf-")]
    assert len(rows) == 1, rows
    assert "the leaf membership rule itself" not in rows[0], rows[0]
    assert "seam reasoning" in rows[0], rows[0]


def test_the_index_heading_is_the_one_the_guard_parses() -> None:
    """The guard reads the leaf table under a heading; the tracked index carries it."""
    text = (REPO_ROOT / INDEX_RELATIVE).read_text(encoding="utf-8")
    assert f"\n{drift_guard.ITEM_NOTES_RULE_HEADING}\n" in text
    assert drift_guard.ITEM_NOTES_RULE_NAME in text
    assert "## Routing table" not in text
