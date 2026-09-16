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


def _build(root: Path, leaves: dict[str, list[str]], rows: list[tuple[str, str]]) -> None:
    """Write a synthetic index plus leaves under ``root``.

    A ROADMAP.md routing every row's item is written too, filed under the phase
    its leaf name spells, so a well-formed family agrees with the derivation.
    A test planting a ROADMAP disagreement overwrites it afterwards.

    Args:
        root: The fabricated repository root.
        leaves: Leaf filename mapped to the item ids its sections carry.
        rows: The routing rows to write, as (item, leaf filename).
    """
    phases: dict[str, list[str]] = {}
    for item, leaf in rows:
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
# CS-1086 - every row is checked against a DERIVATION from ROADMAP.md
#
# The table is kept (the CS-1062 fence) and graded against inputs other than
# itself: the leaf from ROADMAP's phase heading plus the ID block rule, the row
# set from the TRAILING detail field of each item line. Each arm below is a
# disagreement the pre-CS-1086 guard could not see, because it never read
# ROADMAP.md - so every one of them passed there.
# ---------------------------------------------------------------------------


def _count_line(rendered: str) -> str:
    """Return the guard's routed-count detail line, or '' when it has none."""
    for line in rendered.splitlines():
        if line.startswith(f"routed items in {ROADMAP_RELATIVE}"):
            return line
    return ""


@pytest.mark.parametrize(
    ("item", "phase", "want"),
    [
        ("CS-501", "4", "phase4.md"),
        ("CS-799", "4", "phase4.md"),
        ("CS-800", "4", "phase4-followups.md"),
        ("CS-849", "4", "phase4-followups.md"),
        ("CS-850", "4", "phase4-followups-850.md"),
        ("CS-899", "4", "phase4-followups-850.md"),
        ("CS-900", "4", "phase4-followups-900.md"),
        ("CS-1086", "4", "phase4-followups-900.md"),
        ("CS-950", "5", "phase5.md"),
        ("CS-701", "7", "phase7.md"),
    ],
)
def test_the_leaf_rule_has_a_code_owner_at_every_seam(item: str, phase: str, want: str) -> None:
    """The block rule, as a LITERAL table rather than a second copy of the arithmetic.

    Both sides of every seam are pinned, so moving a seam by one ID reddens here.
    """
    assert drift_guard.item_notes_leaf(item, phase) == f"{LEAF_DIR_RELATIVE}/{want}"


def test_a_row_agreeing_with_its_section_but_not_the_derivation_is_red(tmp_path: Path) -> None:
    """The row and the section agree with EACH OTHER and both disagree with ROADMAP.

    Row-versus-section equality is satisfied, so only the derivation can see it.
    """
    _build(
        tmp_path,
        {"phase4.md": ["CS-401", "CS-701"]},
        [("CS-401", "phase4.md"), ("CS-701", "phase4.md")],
    )
    _write_roadmap(tmp_path, {"4": [_item_line("CS-401")], "7": [_item_line("CS-701")]})

    status, rendered = _run(tmp_path)
    assert status == "FAIL", rendered
    assert (
        f"  CS-701 routed to {LEAF_DIR_RELATIVE}/phase4.md, {ROADMAP_RELATIVE} Phase 7 "
        f"derives {LEAF_DIR_RELATIVE}/phase7.md"
    ) in rendered.splitlines(), rendered


def test_a_routed_item_with_no_section_in_its_computed_leaf_is_red(tmp_path: Path) -> None:
    """The row names the derived leaf; the section sits one seam away.

    A section in ANY leaf is not enough - it must be in the leaf the rule computes,
    which is the file a reader following the rule opens.
    """
    _build(
        tmp_path,
        {"phase4-followups.md": ["CS-850"]},
        [("CS-850", "phase4-followups-850.md")],
    )
    _write_roadmap(tmp_path, {"4": [_item_line("CS-850")]})

    status, rendered = _run(tmp_path)
    assert status == "FAIL", rendered
    # CS-1113 - the check that used to print "has no section in" was retired as
    # provably covered, so the line that names this plant is the covering one.
    assert (
        f"  CS-850 routed to {LEAF_DIR_RELATIVE}/phase4-followups-850.md, detail is in "
        f"{LEAF_DIR_RELATIVE}/phase4-followups.md"
    ) in rendered.splitlines(), rendered
    assert RETIRED_NO_SECTION_LINE not in rendered, rendered


def test_a_detail_field_with_no_row_is_red(family: Path) -> None:
    """ROADMAP says the item carries detail; the table does not route it."""
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "7": [_item_line("CS-701"), _item_line("CS-702")],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    lines = rendered.splitlines()
    assert "  CS-702 carries a trailing detail: field and no routing row" in lines, rendered
    assert RETIRED_NO_SECTION_LINE not in rendered, rendered


def test_a_row_with_no_detail_field_is_red(family: Path) -> None:
    """The other direction: the table routes an item whose ROADMAP line carries no field."""
    _write_roadmap(
        family,
        {
            "4": [_item_line("CS-401"), _item_line("CS-402")],
            "7": [_item_line("CS-701", detail=None)],
        },
    )

    status, rendered = _run(family)
    assert status == "FAIL", rendered
    assert "  CS-701 has a routing row and no trailing detail: field" in rendered.splitlines(), (
        rendered
    )


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
    assert (
        "  CS-703 carries a trailing detail: field and no routing row" in rendered.splitlines()
    ), rendered


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
    """Located by POSITION, then its TARGET must agree with the row.

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
# CS-1113 (a) - the "no section in its derived leaf" check was RETIRED
#
# It could never be the reason for a FAIL: every state it saw is also seen by
# no_row, dangling, misrouted or wrong_leaf (the proof is recorded beside the
# retirement in tools/drift_guard.py). A plant that ONLY it caught would have
# kept it; none exists, so the arm below enumerates EVERY state a routed item's
# row and section can be in relative to its derived leaf and asserts the VERDICT
# on each - not a message - so deleting any one covering check reddens a combo.
# ---------------------------------------------------------------------------

#: The phrase only the retired check ever printed. Held here, not imported, so a
#: re-added check is visible to this module rather than agreed with by it.
RETIRED_NO_SECTION_LINE = "has no section in"

#: Where a row or a section can sit relative to CS-701's derived leaf, phase7.md.
_PLACES = {"absent": None, "derived": "phase7.md", "elsewhere": "phase4.md"}


@pytest.mark.parametrize("section_at", sorted(_PLACES))
@pytest.mark.parametrize("row_at", sorted(_PLACES))
def test_every_state_the_retired_no_section_check_saw_still_fails(
    tmp_path: Path, row_at: str, section_at: str
) -> None:
    """Row and section of a routed item, each absent, in its derived leaf, or elsewhere.

    CS-401 is a fully consistent control item in every combination, so the
    family is never empty and a FAIL is never about anything but CS-701. Only
    (derived, derived) agrees with the derivation, and it must PASS - which is
    what stops this arm passing on a guard that simply fails everything.
    """
    row_leaf = _PLACES[row_at]
    section_leaf = _PLACES[section_at]
    leaves: dict[str, list[str]] = {"phase4.md": ["CS-401"], "phase7.md": []}
    if section_leaf is not None:
        leaves[section_leaf].append("CS-701")
    rows = [("CS-401", "phase4.md")]
    if row_leaf is not None:
        rows.append(("CS-701", row_leaf))
    _build(tmp_path, leaves, rows)
    _write_roadmap(tmp_path, {"4": [_item_line("CS-401")], "7": [_item_line("CS-701")]})

    status, rendered = _run(tmp_path)

    agrees = row_at == "derived" and section_at == "derived"
    assert status == ("PASS" if agrees else "FAIL"), rendered
    if not agrees:
        named = [line for line in rendered.splitlines() if line.startswith("  CS-701 ")]
        assert named, f"the FAIL named no line for the planted item: {rendered}"
    assert RETIRED_NO_SECTION_LINE not in rendered, rendered


def test_an_unreadable_roadmap_is_a_warn_never_a_pass(family: Path) -> None:
    """Could-not-look must not read as clean: the rows were never checked."""
    (family / ROADMAP_RELATIVE).unlink()

    guard, skips = drift_guard.guard_index(family)
    assert guard["status"] == "WARN", "\n".join(guard["detail"])
    assert any(skip["path"] == ROADMAP_RELATIVE for skip in skips), skips


# ---------------------------------------------------------------------------
# CS-1115 - a leaf that EXISTS but cannot be read is could-not-look, not absent
#
# `item_notes_sections` caught OSError on a leaf and CONTINUED, so the leaf's
# sections vanished and its routed items read as rows with no section. Every
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
    assert "CS-701" not in rendered, "a row routed to the unread leaf was graded as dangling"


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


def test_a_row_with_no_section_in_a_read_leaf_still_fails_beside_an_unread_one(
    tmp_path: Path,
) -> None:
    """Only rows routed TO the unread leaf go ungraded; a dangling row elsewhere is red.

    The derivation agrees with every row here, so the dangling check is the
    only thing that can make this FAIL.
    """
    _build(
        tmp_path,
        {"phase4.md": ["CS-401"], "phase7.md": ["CS-701"]},
        [("CS-401", "phase4.md"), ("CS-402", "phase4.md"), ("CS-701", "phase7.md")],
    )
    assert _run(tmp_path)[0] == "FAIL", "control: the dangling row is not red with nothing refused"

    with refused(tmp_path / LEAF_DIR_RELATIVE / "phase7.md"):
        status, rendered = _run(tmp_path)

    assert status == "FAIL", rendered
    assert "  CS-402 routed to" in rendered, rendered
    assert "  CS-701 routed to" not in rendered, rendered


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


def test_the_real_tree_routed_count_matches_an_independent_count() -> None:
    """The anti-narrowing control on the REAL tree.

    The guard's routed count must equal a test-side count of ROADMAP item lines
    whose LAST field is a detail field, and both must equal the rows and the
    sections. A narrowed domain shows up as a short count AND as enumerated ids.
    DISCLOSED BLIND SPOT: every real field names the same target, so this arm
    cannot see a target-matching narrowing; the synthetic position arms carry that.
    """
    trailing: set[str] = set()
    for line in (REPO_ROOT / ROADMAP_RELATIVE).read_text(encoding="utf-8").splitlines():
        item = _ROADMAP_ITEM.match(line)
        if item and line.rsplit(" - ", 1)[-1].startswith("detail:"):
            trailing.add(item.group(1))
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
