"""CS-840 - a dated heading classifies, and a live file may not mark itself historical.

THE CONTRADICTION THIS MODULE SETTLES. `CLAUDE.md` said a doc heading carrying
an explicit date marks its own section historical, while `docs/item_notes.md`
says the blocks inside it are LIVE INSTRUCTIONS. Both sentences shipped and
neither had a cost, because the drift guard's dated-heading arm REPORTED its
population instead of failing on it.

THE FIRST REPAIR WAS NOT ENOUGH, AND AN ADVERSARY PROVED IT. Classifying every
heading as STATUS or PROVENANCE gave the guard a failure direction only for
headings it could not classify. A STATUS classification was a PASS outcome, so
nine plants of a leading status date into live files all left the guard at exit
0. The guard could not redden for the exact thing the item exists to catch.

SO THE RULE HAS TWO HALVES NOW, AND BOTH ARE GRADED HERE.

    SHAPE decides what a date MEANS. Leading position, or a governing
    terminal-state verb, is a STATUS date. A date after a governing filing or
    measurement verb is a PROVENANCE date. Neither is DRIFT.

    THE FILE decides whether a status date is ALLOWED. A file carrying dated
    headings declares its own status in its header, and a STATUS date inside a
    file declaring itself LIVE is DRIFT.

WHY A DECLARATION IS NOT THE PER-FILE LIST THE OPERATOR REJECTED. A list lives
in code, is hand-maintained, and rots the moment a file is renamed, split or
archived, because nothing binds the entry to the file. A declaration lives
INSIDE the file it describes - moved by the same edit that moves the file,
deleted by the same edit that deletes it. It has no separate existence to drift
from.

WHY THE TRACKED TREE MUST STAY GREEN. Stripping a date off a heading changes
what a reader believes about that section, so resolving any of this by dating
fewer headings would be a semantic change wearing a formatting hat. Not one
heading was edited to make this module pass, and `test_the_real_tree_is_green`
is what holds that.

THE VACUITY CONTROLS, AND WHAT EACH ONE KILLS. A guard can be green while
grading nothing, so these exist to kill specific mutants rather than to
describe behaviour:

    a constant classifier - killed by the leading-position and provenance-verb
    parametrizations, and by the live-file plant when the constant is
    PROVENANCE;
    a frozen transcription of today's headings - killed by every heading in
    this module being one no tracked file carries;
    a declaration reader stuck on HISTORICAL or None, or a deleted live-file
    arm, or an undeclared arm reverted to skip-and-pass - killed by the arms
    that drive the GUARD rather than the classifier. Each of those has two
    killers from different directions: a plant-and-revert transcript reading an
    exit code, and a differential putting byte-identical heading text in two
    files so the declaration is the only thing that can separate them;
    a padded vocabulary - killed by the leave-one-out arm, which requires every
    entry to change an outcome or match nothing at all.

WHAT ROUND THREE ADDED, because each was a real escape rather than a
hypothetical: a terminal verb outranked by a nearer filing verb, which made
the guard's own error message a recipe for laundering; a declaration forged
inside the file it describes, using an HTML comment, a code fence or a table
cell; a header ended only at ``## ``, so a level-three heading could declare
on the file's behalf; and three ordinary date shapes the patterns could not
see at all.

NO POPULATION FIGURE IS WRITTEN IN THIS MODULE - CLAUDE.md section 4. Every
count is derived from the tree on the run that asserts it.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"

GUARD_ID = "g"

# CS-840's named subject. The file whose header declares its blocks LIVE while
# every section heading in it carries a date.
LIVE_INSTRUCTION_DOC = "docs/item_notes.md"

# A date this module owns, far outside the range any real entry uses.
PLANTED = "2031-02-03"

# The UN-NARROWED rule: "a heading carrying an explicit date marks its own
# section historical", with no mention of where the date sits. Matched loosely
# enough to catch a rewording, because the hazard is the CLAIM and not the
# phrasing. The narrowed sentence says the date LEADS the heading, so it does
# not match.
UN_NARROWED_RULE = re.compile(
    r"heading\s+carrying\s+an\s+explicit\s+date\s+marks\s+its\s+own\s+section\s+historical",
    re.IGNORECASE,
)


def _load_drift_guard() -> Any:
    """Load the guard by file location - it is a script in tools/, not a package.

    Returns:
        The drift_guard module.

    Raises:
        ImportError: The source could not be loaded from this checkout.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_drift_guard", DRIFT_GUARD_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()

LIVE_HEADER = "# Fixture\n\n**Section status: LIVE.** Provenance only.\n\nBody.\n"
HISTORICAL_HEADER = "# Fixture\n\n**Section status: HISTORICAL.** A record.\n\nBody.\n"
UNDECLARED_HEADER = "# Fixture\n\nThis header declares nothing.\n\nBody.\n"

# The forged line, hidden inside a comment, a fence or a table cell.
FORGE = "**Section status: HISTORICAL.**"


# ---------------------------------------------------------------------------
# Populations, every one derived from the guard's own enumeration and patterns
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tracked_dated_headings() -> list[tuple[str, int, str]]:
    """Every dated heading in the tracked tree, as (path, line number, heading).

    Derived through ``enumerate_files`` and ``dated_headings`` rather than
    through a second scan of this module's own. Two derivations from one regex
    agree by construction and would grade nothing.

    Returns:
        One row per dated heading, in enumeration order.
    """
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)
    rows: list[tuple[str, int, str]] = []
    for path in files:
        if path.suffix.lower() not in (".md", ".markdown"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.extend(
            (path.relative_to(REPO_ROOT).as_posix(), number, heading)
            for number, heading in drift_guard.dated_headings(text)
        )
    return rows


@pytest.fixture
def clean_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tree the whole driver reports CLEAN, so a later red is attributable.

    Only the port record is copied in. Guard (e) is the one guard that FAILS
    outright on an absent file rather than warning, and a red on a tree that
    was never green attributes to nothing.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The synthetic repository root, with the driver pointed at it.
    """
    root = tmp_path / "tree"
    (root / "config").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "config" / "ports.json", root / "config" / "ports.json")
    (root / "live.md").write_bytes(LIVE_HEADER.encode("ascii"))
    (root / "hist.md").write_bytes(HISTORICAL_HEADER.encode("ascii"))
    monkeypatch.setattr(drift_guard, "repo_root", lambda: root)
    return root


def run_driver(capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    """Run the guard driver end to end and read back its machine-readable report.

    Args:
        capsys: pytest capture fixture.

    Returns:
        (process exit code, the parsed JSON report).
    """
    code = drift_guard.main(["--json"])
    return code, json.loads(capsys.readouterr().out)


def guard_of(report: dict[str, Any]) -> dict[str, Any]:
    """Pull guard (g)'s record out of a report.

    Args:
        report: The parsed JSON report.

    Returns:
        The guard record.
    """
    matches: list[dict[str, Any]] = [g for g in report["guards"] if g["id"] == GUARD_ID]
    assert len(matches) == 1, f"expected exactly one guard {GUARD_ID!r}, found {len(matches)}"
    return matches[0]


def plant(path: Path, heading: str) -> bytes:
    """Append a heading to a markdown file and PROVE the append landed.

    A mutation that never applied is indistinguishable from one that survived
    (CONVENTIONS.md section 7.2), so this refuses to return a plant it did not
    make.

    Args:
        path: The markdown file to mutate.
        heading: The heading line to append.

    Returns:
        The file's bytes as they stood BEFORE the plant.
    """
    before = path.read_bytes()
    path.write_bytes(before + b"\n" + heading.encode("ascii") + b"\n\nBody text.\n")
    assert path.read_bytes() != before, "the plant did not apply"
    assert heading.encode("ascii") in path.read_bytes(), "the plant is not in the file"
    return before


# ---------------------------------------------------------------------------
# The arm the adversary proved missing: a LIVE file may not mark itself historical
# ---------------------------------------------------------------------------


def test_a_status_date_in_a_live_file_turns_the_guard_red(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """THE ARM CS-840 EXISTS FOR, and the one the first build shipped without.

    A leading status date in a file that declares itself LIVE says the section
    is history while the file says its sections are current. Before this arm,
    nine such plants across five real files all left the guard at exit 0,
    because a STATUS classification was a PASS outcome.

    This is also the only arm in this module that exercises the GUARD rather
    than the classifier, which makes it the one that kills a deleted live-file
    check, a declaration reader stuck on HISTORICAL or None, and a classifier
    that returns PROVENANCE unconditionally.
    """
    live = clean_tree / "live.md"

    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "the floor must be clean or the red proves nothing"

    heading = f"## {PLANTED} - CS-901 - CLOSED, and this section is now history"
    pristine = plant(live, heading)

    code, report = run_driver(capsys)
    guard = guard_of(report)
    assert guard["status"] == "FAIL"
    assert report["drift"] == [GUARD_ID], "the red must attribute to this guard and no other"
    assert code != 0, "a report is not a failure - the exit code is what CI reads"
    assert any(heading in line for line in guard["detail"]), "the red must name the heading"

    live.write_bytes(pristine)
    assert live.read_bytes() == pristine, "the revert did not land byte-identically"
    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "removing the plant must restore the green"


def test_the_same_status_date_is_fine_in_a_file_that_declares_itself_historical(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other half of the partition, without which the arm could just ban status dates.

    `docs/LEDGER.md` is nothing BUT status dates. An arm that reddened on every
    one of them would be a rule against the ledger existing.
    """
    heading = f"## {PLANTED} - CS-901 - CLOSED, and this section is now history"
    plant(clean_tree / "hist.md", heading)

    code, report = run_driver(capsys)

    assert guard_of(report)["status"] == "PASS"
    assert (code, report["drift"]) == (0, [])


def drift_records(guard: dict[str, Any], marker: str) -> list[str]:
    """Return the records listed under the DRIFT block whose header holds ``marker``.

    Args:
        guard: A guard record.
        marker: Text identifying which DRIFT block to read.

    Returns:
        The indented record lines under that block.
    """
    out: list[str] = []
    collecting = False
    for line in guard["detail"]:
        if line.startswith("DRIFT"):
            collecting = marker in line
        elif collecting and line.startswith("  "):
            out.append(line)
        elif collecting:
            collecting = False
    return out


def test_the_guard_reds_the_live_copy_of_a_heading_and_leaves_the_historical_one(
    clean_tree: Path,
) -> None:
    """A SECOND killer for a deleted live-file arm, approaching from another direction.

    The plant-and-revert transcript drives ``main`` against one file and reads
    an exit code. This drives ``guard_dated`` directly, against a different
    pair of files, with BYTE-IDENTICAL heading text in both - so the
    declaration is the only thing that can separate them.

    That makes it a differential inside a single run rather than a comparison
    between runs, and it closes from both sides at once. A deleted arm greens
    both copies. An arm that reddened on any status date anywhere - which would
    be a rule against `docs/LEDGER.md` existing - reds both copies. Only an arm
    that actually reads the declaration produces exactly one of each, and only
    this test can tell those three apart.
    """
    heading = f"## {PLANTED} - CS-902 - CLOSED, and this section is now history"
    body = f"\n{heading}\n\nBody.\n".encode("ascii")
    live = clean_tree / "second_live.md"
    historical = clean_tree / "second_hist.md"
    live.write_bytes(LIVE_HEADER.encode("ascii") + body)
    historical.write_bytes(HISTORICAL_HEADER.encode("ascii") + body)
    assert live.read_bytes().endswith(body), "the live copy did not land"
    assert historical.read_bytes().endswith(body), "the historical copy did not land"

    guard, _skips = drift_guard.guard_dated(clean_tree, [live, historical])

    assert guard["status"] == "FAIL"
    flagged = drift_records(guard, f"declares itself {drift_guard.LIVE}")
    assert any("second_live.md" in record for record in flagged), (
        "the live copy of the heading was not reported as drift"
    )
    assert not any("second_hist.md" in record for record in flagged), (
        "the historical copy was reported too, so the declaration is not being read"
    )


def test_a_provenance_date_is_fine_in_a_live_file(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A classifier stuck on STATUS would redden here; the tracked tree depends on it."""
    plant(clean_tree / "live.md", f"## NOTE - filed {PLANTED} by the merger")

    code, report = run_driver(capsys)

    assert guard_of(report)["status"] == "PASS"
    assert (code, report["drift"]) == (0, [])


def test_a_file_carrying_dated_headings_without_a_declaration_turns_the_guard_red(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AN UNDECLARED DATED FILE IS DRIFT, and the first build of this repair got it wrong.

    It recorded a skip and passed, reasoning that the live arm had nothing to
    grade. But CS-840 was filed BECAUSE this guard reported its population
    instead of failing on it, and a guard that reports cannot lose. A skip that
    passes is a report, so the first build reproduced the item's own defect
    inside the fix for it.

    An undeclared file is precisely the case the guard cannot judge - a status
    date in it may be a closure record or a live section marked historical -
    which makes it the case to FAIL on rather than the one to excuse.
    """
    mystery = clean_tree / "mystery.md"

    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "the floor must be clean or the red proves nothing"

    mystery.write_bytes(
        UNDECLARED_HEADER.encode("ascii") + f"\n## {PLANTED} - CS-901 - CLOSED\n".encode("ascii")
    )
    assert mystery.exists(), "the plant did not apply"

    code, report = run_driver(capsys)
    guard = guard_of(report)
    assert guard["status"] == "FAIL"
    assert report["drift"] == [GUARD_ID], "the red must attribute to this guard and no other"
    assert code != 0, "a skip that passes is a report - the exit code is what CI reads"
    assert any("mystery.md" in line for line in guard["detail"]), "the red must name the file"

    mystery.unlink()
    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "removing the file must restore the green"


def test_the_guard_reds_the_undeclared_copy_of_a_heading_and_leaves_the_declared_one(
    clean_tree: Path,
) -> None:
    """A SECOND killer for the undeclared arm, by the same differential shape.

    The transcript above drives ``main`` and reads an exit code; this drives
    ``guard_dated`` directly with byte-identical heading text in a declared and
    an undeclared file, so the declaration is the only thing separating them.
    An arm reverted to skip-and-pass greens both; an arm that demanded a
    declaration of every markdown file would red both.
    """
    heading = f"## NOTE - filed {PLANTED} by the merger"
    body = f"\n{heading}\n\nBody.\n".encode("ascii")
    declared = clean_tree / "third_declared.md"
    undeclared = clean_tree / "third_undeclared.md"
    declared.write_bytes(LIVE_HEADER.encode("ascii") + body)
    undeclared.write_bytes(UNDECLARED_HEADER.encode("ascii") + body)
    assert declared.read_bytes().endswith(body), "the declared copy did not land"
    assert undeclared.read_bytes().endswith(body), "the undeclared copy did not land"

    guard, _skips = drift_guard.guard_dated(clean_tree, [declared, undeclared])

    assert guard["status"] == "FAIL"
    flagged = drift_records(guard, "declare no section status")
    assert any("third_undeclared.md" in record for record in flagged), (
        "the undeclared file was not reported as drift"
    )
    assert not any("third_declared.md" in record for record in flagged), (
        "the declared file was reported too, so the declaration is not being read"
    )


def test_an_undeclared_file_with_no_dated_heading_is_not_anybodys_business(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The bound on the arm above, without which it would demand a declaration everywhere.

    Most markdown in this repository carries no dated heading and has no reason
    to declare anything. The requirement attaches to dating a heading, not to
    being a markdown file.
    """
    (clean_tree / "ordinary.md").write_bytes(UNDECLARED_HEADER.encode("ascii"))

    code, report = run_driver(capsys)

    assert guard_of(report)["status"] == "PASS"
    assert (code, report["drift"]) == (0, [])


def test_every_tracked_file_carrying_dated_headings_declares_its_status() -> None:
    """The real-tree completeness the guard deliberately does not enforce.

    The guard treats an undeclared file as ungraded rather than failed, so this
    is where the tracked tree is held to actually declaring. It also kills a
    declaration reader that returns None unconditionally.
    """
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)
    undeclared = []
    dated_files = 0
    for path in files:
        if path.suffix.lower() not in (".md", ".markdown"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not drift_guard.dated_headings(text):
            continue
        dated_files += 1
        if drift_guard.read_status_declaration(text) is None:
            undeclared.append(path.relative_to(REPO_ROOT).as_posix())

    assert dated_files, "no tracked file carries a dated heading - this control proves nothing"
    assert not undeclared, "tracked files carry dated headings but declare nothing:\n" + "\n".join(
        undeclared
    )


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("# T\n\n**Section status: LIVE.** x\n", "LIVE"),
        ("# T\n\n**Section status: HISTORICAL.** x\n", "HISTORICAL"),
        ("# T\n\nnothing here\n", None),
        ("# T\n\nprose\n\n**Section status: LIVE.** x\n\n## S\n", "LIVE"),
        ("# T\n\n## S\n\n**Section status: LIVE.** x\n", None),
    ],
)
def test_the_declaration_is_read_from_the_header_only(header: str, expected: str | None) -> None:
    """A section QUOTING the declaration must not be able to declare for the file."""
    assert drift_guard.read_status_declaration(header) == expected


@pytest.mark.parametrize(
    "header",
    [
        "# T\n\n### S\n\n**Section status: LIVE.** x\n",
        "# T\n\n#### S\n\n**Section status: LIVE.** x\n",
        "# T\n\n###### S\n\n**Section status: LIVE.** x\n",
        "# T\n\n# S\n\n**Section status: LIVE.** x\n",
        "# T\n\nS\n----\n\n**Section status: LIVE.** x\n",
        "# T\n\nS\n====\n\n**Section status: LIVE.** x\n",
        "# T\n\n##S\n\n**Section status: LIVE.** x\n",
    ],
)
def test_a_heading_of_any_level_or_style_ends_the_header(header: str) -> None:
    """A SECTION COULD DECLARE ON THE FILE'S BEHALF by being level three.

    The header used to end at ``line.startswith("## ")`` and nothing else, so
    the literal level-2 case was pinned while every other way of writing a
    heading walked straight past it - level three, a setext underline, or a
    line like ``##S``. The first heading is still allowed through, because it
    is the document title and the declaration sits under it; every heading
    after that ends the header, whatever its level or style.
    """
    assert drift_guard.read_status_declaration(header) is None


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (f"# T\n\n<!--\n{FORGE}\n-->\n\n**Section status: LIVE.** r\n", "LIVE"),
        (f"# T\n\n<!-- {FORGE} -->\n\n**Section status: LIVE.** r\n", "LIVE"),
        (f"# T\n\n```\n{FORGE}\n```\n\n**Section status: LIVE.** r\n", "LIVE"),
        (f"# T\n\n~~~\n{FORGE}\n~~~\n\n**Section status: LIVE.** r\n", "LIVE"),
        (f"# T\n\n<!--\n{FORGE}\n-->\n", None),
        (f"# T\n\n```\n{FORGE}\n```\n", None),
        (f"# T\n\n| a |\n|---|\n| {FORGE} |\n", None),
        (f"# T\n\na | b\n--- | ---\n{FORGE} | x\n", None),
    ],
)
def test_a_declaration_the_reader_cannot_see_is_not_a_declaration(
    header: str, expected: str | None
) -> None:
    """THE DECLARATION WAS FORGEABLE FROM INSIDE THE FILE IT DESCRIBES.

    Three invisible lines above the real one -

        <!--
        **Section status: HISTORICAL.**
        -->

    - and the guard read HISTORICAL while every human reading the rendered
    file saw LIVE. Status dates then passed freely. A code fence did the same,
    and so did the first cell of a pipeless table row. The same forge also
    SILENCED the undeclared-is-fatal arm on a file that really declares
    nothing, which is the last two cases here.

    The forge was order-dependent - the same comment placed BELOW the real
    line failed - which is what proved it a genuine precedence bug rather than
    an artefact of the regex matching twice.
    """
    assert drift_guard.read_status_declaration(header) == expected


def test_the_forge_is_order_dependent_which_is_what_made_it_real() -> None:
    """The control that separates a precedence bug from a regex artefact.

    If the guard had simply been matching the forged line wherever it sat,
    placing it BELOW the real declaration would forge just as well. It did
    not: below, the real line won. That asymmetry is what proved the header
    scan was reading raw text in document order, and it is what this pins.
    """
    below = "# T\n\n**Section status: LIVE.** real\n\n<!--\n**Section status: HISTORICAL.**\n-->\n"
    above = "# T\n\n<!--\n**Section status: HISTORICAL.**\n-->\n\n**Section status: LIVE.** real\n"

    assert drift_guard.read_status_declaration(below) == drift_guard.LIVE
    assert drift_guard.read_status_declaration(above) == drift_guard.LIVE


def test_a_forged_declaration_cannot_smuggle_a_status_date_into_a_live_file(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The forge at the GUARD level, which is where it bought something.

    Forging HISTORICAL above a real LIVE declaration is only interesting
    because it lets status dates through. This plants the forge AND the status
    date together and requires the guard to redden anyway.
    """
    forged = clean_tree / "forged.md"
    forged.write_bytes(
        b"# Fixture\n\n<!--\n**Section status: HISTORICAL.**\n-->\n\n"
        b"**Section status: LIVE.** Provenance only.\n\n"
        + f"## {PLANTED} - CS-901 - CLOSED\n".encode("ascii")
    )

    code, report = run_driver(capsys)

    assert guard_of(report)["status"] == "FAIL", "a forged HISTORICAL let a status date pass"
    assert code != 0
    assert any("forged.md" in line for line in guard_of(report)["detail"])


def test_a_forged_declaration_cannot_silence_the_undeclared_arm(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same forge against the newer arm - a file that really declares nothing."""
    hidden = clean_tree / "hidden.md"
    hidden.write_bytes(
        b"# Fixture\n\n<!--\n**Section status: HISTORICAL.**\n-->\n\n"
        + f"## NOTE - filed {PLANTED} by the merger\n".encode("ascii")
    )

    code, report = run_driver(capsys)

    assert guard_of(report)["status"] == "FAIL", "a forged declaration silenced the undeclared arm"
    assert code != 0
    assert any("hidden.md" in line for line in guard_of(report)["detail"])


# ---------------------------------------------------------------------------
# The other failure direction: an idiom the closed vocabulary does not cover
# ---------------------------------------------------------------------------


def test_a_dated_heading_in_an_unclassifiable_idiom_turns_the_guard_red(
    clean_tree: Path,
) -> None:
    """A plausible provenance idiom that is deliberately NOT in the vocabulary.

    Somebody writes a new date idiom, and the guard makes them say which of the
    two families it belongs to instead of silently absorbing it.
    """
    live = clean_tree / "live.md"
    heading = f"## Reviewed on {PLANTED} by the operator"
    plant(live, heading)

    guard, _skips = drift_guard.guard_dated(clean_tree, [live])

    assert guard["status"] == "FAIL"
    assert any(heading in line for line in guard["detail"]), (
        "a red that does not name the heading it tripped on is not actionable"
    )


def test_the_red_names_the_two_families_the_author_has_to_choose_between(
    clean_tree: Path,
) -> None:
    """A guard that says only NO leaves the next author guessing."""
    live = clean_tree / "live.md"
    plant(live, f"## Reviewed on {PLANTED} by the operator")

    guard, _skips = drift_guard.guard_dated(clean_tree, [live])

    rendered = " ".join(guard["detail"]).upper()
    assert drift_guard.STATUS_DATE.upper() in rendered
    assert drift_guard.PROVENANCE_DATE.upper() in rendered


# ---------------------------------------------------------------------------
# The classification direction - what each shape means
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "heading",
    [
        f"### {PLANTED} - CS-999 - CLOSED, and the reason is recorded in this entry",
        f"## {PLANTED}",
        f"#### {PLANTED}: the decision and the fence around it",
    ],
)
def test_a_date_in_the_leading_position_is_a_status_date(heading: str) -> None:
    assert drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE


@pytest.mark.parametrize(
    "heading",
    [
        f"## **{PLANTED}** - CS-901 closed",
        f"## __{PLANTED}__ - CS-901 closed",
        f"## _{PLANTED}_ - CS-901 closed",
        f"## ({PLANTED}) CS-901 closed",
        f"## [{PLANTED}] CS-901 closed",
        f"## `{PLANTED}` - CS-901 closed",
        f'## "{PLANTED}" - CS-901 closed',
    ],
)
def test_a_leading_date_wearing_markdown_decoration_is_still_leading(heading: str) -> None:
    """DEFECT 2. The ruling is about POSITION, and these all open with their date.

    Every one of these classified as NEITHER and reddened a correct heading
    before this fix. Two of them - the underscore forms - were worse than that:
    an underscore is a word character, so the old word-boundary escape found no
    date at all and the heading was INVISIBLE to the guard. Italicising a date
    was enough to smuggle a status date into a live file.
    """
    assert drift_guard.dated_headings(heading), "the date must be visible at all"
    assert drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE


@pytest.mark.parametrize(
    "heading",
    [
        f"### NOTE - relocated from `ROADMAP.md` {PLANTED}",
        f"### detail - relocated to `docs/upstream_watch.md` {PLANTED}",
        f"### NOTE - filed {PLANTED} by the merger, on an operator ruling",
        f"#### Operator decision {PLANTED}: the flip ships from a FRESH history",
        f"#### Measured {PLANTED} (CS-999): the rule was broken the day after it was written",
        f"## Session 91 - {PLANTED} - four units land and one of them is refuted",
        f"## Session 91, continued - {PLANTED} - the held push lands",
        f"### Archived {PLANTED} from `WAKEUP_NOTES.md` - session 91 at full fidelity",
        f"### Relocated from WAKEUP_NOTES.md on {PLANTED}",
        f"### 9.4 Spike results - session 2, {PLANTED}",
    ],
)
def test_a_date_after_a_governing_provenance_verb_is_a_provenance_date(heading: str) -> None:
    assert drift_guard.classify_dated_heading(heading) == drift_guard.PROVENANCE_DATE


@pytest.mark.parametrize(
    "heading",
    [
        f"## Superseded - filed {PLANTED}",
        f"## Closed and retired, recorded {PLANTED}",
        f"## Superseded and closed - filed {PLANTED}",
        f"## Retired - relocated from `ROADMAP.md` {PLANTED}",
        f"## CS-901 closed, archived {PLANTED}",
    ],
)
def test_a_governing_terminal_verb_beats_a_filing_verb_wherever_it_sits(heading: str) -> None:
    """A COMPLIANCE FAILURE AGAINST THE RULING, and the worst kind of one.

    The ruling says a terminal-state verb before the date IS a status date.
    Nearest-wins silently dropped it whenever a filing verb sat closer, so
    "Superseded - filed <date>" read as PROVENANCE and passed inside a file
    declaring itself LIVE.

    What made it the worst kind: the guard's own error message told authors to
    put the date after a provenance verb. Following the guard's advice
    laundered a historical section into a live file, so the message was a
    recipe for defeating the check it belonged to. Nearest-wins now breaks
    ties only WITHIN a class, and the message no longer reads as instructions.
    """
    assert drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE


def test_a_terminal_verb_in_a_live_file_reddens_the_guard_however_it_is_worded(
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same defect at the GUARD level, which is where it actually bit.

    Classifying correctly is not the claim - the claim is that these cannot be
    planted into a live file and pass. Each is planted, graded, and removed.
    """
    live = clean_tree / "live.md"
    for wording in (
        f"## Superseded - filed {PLANTED}",
        f"## Closed and retired, recorded {PLANTED}",
        f"## Superseded and closed - filed {PLANTED}",
    ):
        code, report = run_driver(capsys)
        assert (code, report["drift"]) == (0, []), "the floor must be clean"

        pristine = plant(live, wording)
        code, report = run_driver(capsys)
        assert guard_of(report)["status"] == "FAIL", f"{wording!r} passed inside a LIVE file"
        assert code != 0, f"{wording!r} did not move the exit code"

        live.write_bytes(pristine)
        assert live.read_bytes() == pristine, "the revert did not land byte-identically"


def test_the_red_does_not_read_as_instructions_for_getting_past_it(
    clean_tree: Path,
) -> None:
    """An error message that teaches the reader how to defeat the guard is a defect.

    The old text said the date "belongs after a provenance verb" - do exactly
    that and the section stays historical inside a live file while the guard
    goes green. The replacement tells the author to decide which is TRUE and
    move the section or change the declaration, and says in terms not to
    reword past the check.
    """
    live = clean_tree / "live.md"
    plant(live, f"## {PLANTED} - CS-901 - CLOSED")

    guard, _skips = drift_guard.guard_dated(clean_tree, [live])
    rendered = " ".join(guard["detail"]).lower()

    assert guard["status"] == "FAIL"
    assert "do not reword the heading to get past this check" in rendered
    assert "belongs after a provenance verb" not in rendered


@pytest.mark.parametrize(
    "heading",
    [
        f"## The closed vocabulary and its fence - reviewed {PLANTED}",
        f"## Session 91 - the operator takes ALL FOUR units {PLANTED}",
        f"## A retired idea that someone revived and then wrote up on {PLANTED}",
    ],
)
def test_a_verb_that_does_not_govern_the_date_does_not_classify_it(heading: str) -> None:
    """DEFECT 3, and the reword flip with it.

    "closed" is this project's own adjective for a bounded set, and matching it
    anywhere before a date let it claim one it had nothing to do with. The date
    has to be the verb's OWN object, so only connectives and the name of a file
    being moved may sit between them. Anything else and the author is asked
    which family the heading belongs to.

    The second case is the reword the merger flagged: moving a date to the end
    of a session heading used to flip PROVENANCE to STATUS silently. It now
    goes red instead, and would be caught by the live-file arm even if it did
    not.
    """
    assert drift_guard.dated_headings(heading), "the date must be visible at all"
    assert drift_guard.classify_dated_heading(heading) is None


@pytest.mark.parametrize(
    "heading",
    [
        "## This May need 2031 rework",
        "## March on, and do not stop before 2031",
        "## Sep the branch, then ship it in 2031",
    ],
)
def test_a_month_name_far_from_a_year_is_not_a_date(heading: str) -> None:
    """DEFECT 4. The month pattern allowed twelve arbitrary characters before the year.

    "This May need 2031 rework" carries no date, and the guard reddened it.
    A year now has to be the month's own - directly after it, or after a day
    number that follows it.
    """
    assert not drift_guard.dated_headings(heading)
    assert drift_guard.classify_dated_heading(heading) is None


@pytest.mark.parametrize(
    "heading",
    [
        "### August 2031 - CS-901 - CLOSED",
        "### August 13, 2031 - CS-901 - CLOSED",
        "### Aug 13 2031 - CS-901 - CLOSED",
    ],
)
def test_a_month_name_beside_its_year_is_still_a_date(heading: str) -> None:
    """The other side of defect 4 - the tightening must not blind the guard."""
    assert drift_guard.dated_headings(heading)
    assert drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE


@pytest.mark.parametrize(
    "heading",
    [
        "## 2031/02/03 - CS-901 - CLOSED",
        "## 2031-2-3 - CS-901 - CLOSED",
        "## 31-02-03 - CS-901 - CLOSED",
        "## 2031-02-03 - CS-901 - CLOSED",
    ],
)
def test_ordinary_date_shapes_are_visible_to_the_guard(heading: str) -> None:
    """AN INVISIBLE DATE IS NOT "DATED", so no arm of this guard can fire on it.

    Three ordinary shapes were invisible - a year-first slash date, an
    unpadded ISO date, and a two-digit year - which falsified the claim that a
    leading status date in a live file is caught. It was caught only in this
    project's house format. The claim now holds for all four shapes rather
    than needing a format qualifier.
    """
    assert drift_guard.dated_headings(heading), "the date is invisible to the guard"
    assert drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE


@pytest.mark.parametrize(
    "heading",
    [
        "## This May need 2031 rework",
        "## CS-999 - the item and its fence",
        "## Version 1.2-3 of the format",
        "## Ports 8900-8911 and the band around them",
    ],
)
def test_widening_the_date_shapes_did_not_start_seeing_dates_everywhere(heading: str) -> None:
    """The bound on the widening. Reaching more shapes must not invent dates."""
    assert not drift_guard.dated_headings(heading)
    assert drift_guard.classify_dated_heading(heading) is None


def test_a_heading_with_no_date_at_all_is_not_this_guards_business() -> None:
    assert drift_guard.classify_dated_heading("## CS-999 - the item and its fence") is None


def test_no_tracked_file_still_states_the_un_narrowed_dated_heading_rule() -> None:
    """CS-840's ORIGINAL DEFECT, RELOCATED INTO THE INSTRUCTIONS AGENTS ACT ON.

    The rule was narrowed in the two files that STATE it and left verbatim in
    three that agents OBEY - a sub-agent definition and two command
    checklists. An agent following the old sentence refuses to audit every
    live per-item note as current, because each carries a provenance date.
    That is the item's own defect, one layer out.

    THE POPULATION IS DERIVED, NOT LISTED. A list of three files is exactly
    the hand-maintained thing this project keeps recording as the thing that
    rots, so this sweeps every tracked file for the un-narrowed sentence and
    fails on whatever it finds. Files that RECORD the old rule as history -
    the ledger, the deep archive, an ADR, and CS-840's own item note - are
    excluded by a stated criterion: they declare themselves HISTORICAL, or
    they are the note describing the defect.
    """
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)
    recorded_history = {
        "docs/LEDGER.md",
        "docs/history_notes.md",
        "docs/item_notes.md",
        "tests/test_dated_headings.py",
    }
    offenders: list[str] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in recorded_history or relative.startswith("docs/adr/"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        offenders.extend(
            f"{relative}:{number}  {line.strip()}"
            for number, line in enumerate(text.splitlines(), start=1)
            if UN_NARROWED_RULE.search(line)
        )

    assert not offenders, (
        "these still state that ANY dated heading marks its section historical, which "
        "tells an agent to skip every live section carrying a provenance date:\n"
        + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# The tracked tree is the control - it must be GREEN, unedited
# ---------------------------------------------------------------------------


def test_every_dated_heading_in_the_tracked_tree_classifies(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """Today's tree passes with no heading edited - the item's binding constraint."""
    assert tracked_dated_headings, "no dated headings found - this control proves nothing"

    unclassified = [
        f"{path}:{number}  {heading}"
        for path, number, heading in tracked_dated_headings
        if drift_guard.classify_dated_heading(heading) is None
    ]

    assert not unclassified, "unclassifiable dated headings:\n" + "\n".join(unclassified)


def test_the_real_tree_is_green(capsys: pytest.CaptureFixture[str]) -> None:
    """The end-to-end control, through the driver, on the real tree.

    This is what a constant classifier dies on: STATUS everywhere reddens every
    live file, and None everywhere reddens the lot. It is also what a
    declaration reader stuck on LIVE dies on, because the ledger is nothing but
    status dates.
    """
    guards, _skips, _source = drift_guard.run_all(REPO_ROOT)
    matches = [guard for guard in guards if guard["id"] == GUARD_ID]
    assert len(matches) == 1
    assert matches[0]["status"] == "PASS", "\n".join(matches[0]["detail"])
    capsys.readouterr()


def test_the_live_instruction_file_carries_no_status_date(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """CS-840's named subject, and the reason the contradiction is gone.

    Every dated heading in the live-instruction file records when a note was
    FILED or RELOCATED, so none of them marks its section historical - and not
    one heading had to lose its date for that to be true.
    """
    live = [row for row in tracked_dated_headings if row[0] == LIVE_INSTRUCTION_DOC]
    assert live, f"{LIVE_INSTRUCTION_DOC} carries no dated heading - this control proves nothing"

    marked_historical = [
        f"{path}:{number}  {heading}"
        for path, number, heading in live
        if drift_guard.classify_dated_heading(heading) == drift_guard.STATUS_DATE
    ]

    assert not marked_historical, (
        "a live-instruction section is marked historical by its own heading:\n"
        + "\n".join(marked_historical)
    )


def test_the_tracked_tree_exercises_BOTH_families(  # noqa: N802
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """A partition only one side of which is ever taken is not a partition."""
    families = {
        drift_guard.classify_dated_heading(heading)
        for _path, _number, heading in tracked_dated_headings
    }
    assert drift_guard.STATUS_DATE in families
    assert drift_guard.PROVENANCE_DATE in families


def test_the_tracked_tree_declares_BOTH_statuses() -> None:  # noqa: N802
    """The same argument one level up.

    If every declaring file said LIVE, an arm that reddened on any status date
    anywhere would pass every test here. If every file said HISTORICAL, the
    live arm would never fire on the real tree at all.
    """
    files, _source, _skips = drift_guard.enumerate_files(REPO_ROOT)
    declared = set()
    for path in files:
        if path.suffix.lower() not in (".md", ".markdown"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if drift_guard.dated_headings(text):
            declared.add(drift_guard.read_status_declaration(text))
    assert drift_guard.LIVE in declared
    assert drift_guard.HISTORICAL in declared


# ---------------------------------------------------------------------------
# The controls against a classifier that is secretly a list of today's headings
# ---------------------------------------------------------------------------


NOVEL_HEADINGS = (
    (f"### {PLANTED} - CS-998 - CLOSED on the second arm", "STATUS"),
    (f"## {PLANTED} - the sweep and what it refused", "STATUS"),
    (f"### CS-998 - detail - superseded {PLANTED}", "STATUS"),
    (f"## CS-997 - detail - retired {PLANTED}", "STATUS"),
    (f"### CS-996 - withdrawn {PLANTED} by the operator", "STATUS"),
    (f"### NOTE - filed {PLANTED} by an adversary that wrote none of the code", "PROVENANCE"),
    (f"### NOTE - relocated from `BACKLOG.md` {PLANTED}", "PROVENANCE"),
    (f"#### Probed {PLANTED}: the endpoint answers and the doc does not", "PROVENANCE"),
    (f"#### Observed {PLANTED} on a machine with no game installed", "PROVENANCE"),
    (f"#### Recorded {PLANTED} against the pinned development world", "PROVENANCE"),
    (f"## Session 92, continued - {PLANTED} - the held push lands", "PROVENANCE"),
    (f"### Archived {PLANTED} from `docs/GATED.md` - the gate cleared", "PROVENANCE"),
    (f"#### Operator ruling {PLANTED}: shape decides, and a file list does not", "PROVENANCE"),
    (f"## Live per-item detail moved out - {PLANTED}", "PROVENANCE"),
)


@pytest.mark.parametrize(("heading", "family"), NOVEL_HEADINGS)
def test_the_vocabulary_classifies_idioms_no_tracked_file_carries(
    heading: str, family: str, tracked_dated_headings: list[tuple[str, int, str]]
) -> None:
    """GENERALISATION - the control that kills a lookup table of today's headings.

    Every heading here is composed in this module and carried by no tracked
    file, which the first assertion proves rather than assumes.
    """
    carried = {row[2].strip() for row in tracked_dated_headings}
    assert heading not in carried, "this control needs a heading the tracked tree does NOT carry"

    expected = getattr(drift_guard, f"{family}_DATE")
    assert drift_guard.classify_dated_heading(heading) == expected


def test_the_vocabulary_holds_idioms_the_tracked_tree_never_uses(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """UNUSED ENTRIES - the control that kills a vocabulary fitted to today's tree."""
    headings = [row[2] for row in tracked_dated_headings]
    assert headings, "no dated headings found - this control proves nothing"

    unused = [
        pattern.pattern
        for pattern in drift_guard.DATE_IDIOMS
        if not any(pattern.search(heading) for heading in headings)
    ]

    assert unused, "every vocabulary entry is used by today's tree - that is a transcription"


def test_no_vocabulary_entry_ever_spans_a_whole_heading(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """PROPER SUBSTRING - the control that kills a vocabulary made OF headings.

    An idiom is a fragment of a heading. If a vocabulary entry ever matched a
    heading end to end, the entry would BE that heading.

    THE CARDINALITY ASSERTION THIS ARM USED TO CARRY WAS DELETED RATHER THAN
    KEPT. It compared the size of the vocabulary with the size of the
    population - a dozen-odd idioms against hundreds of headings. A closed
    vocabulary is always smaller than a population that grows every session, so
    the comparison could not fail on any tree this project will ever have. It
    read like a control and graded nothing.
    """
    headings = [row[2].strip() for row in tracked_dated_headings]
    assert headings, "no dated headings found - this control proves nothing"

    spanned = [
        f"{pattern.pattern} spans {heading}"
        for heading in headings
        for pattern in drift_guard.DATE_IDIOMS
        for match in [pattern.search(heading)]
        if match is not None and len(match.group(0)) >= len(heading)
    ]

    assert not spanned, "\n".join(spanned)


def test_every_vocabulary_entry_changes_an_outcome_or_matches_nothing(
    tracked_dated_headings: list[tuple[str, int, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """LEAVE ONE OUT - the control that kills a padded vocabulary.

    Removing an entry must either change how some tracked heading classifies -
    the entry is load-bearing - or change nothing because the entry reaches no
    heading's LEAD-IN, which is a spare kept on purpose so the vocabulary is
    not a transcription of the tree. An entry that reaches a lead-in but
    changes no outcome is dead weight wearing the shape of a rule.

    REACH IS MEASURED AGAINST THE LEAD-IN, NOT THE WHOLE HEADING, and the
    difference is not academic: this arm's first run reported three entries as
    dead, and all three turned out to match only words in a heading's TAIL -
    after its date, in a region the classifier never reads. The control was
    measuring somewhere the code does not look. It now asks the module for the
    lead-in rather than deriving one of its own.
    """
    headings = [row[2] for row in tracked_dated_headings]
    assert headings, "no dated headings found - this control proves nothing"
    lead_ins = [lead for lead in map(drift_guard.heading_lead_in, headings) if lead]
    baseline = [drift_guard.classify_dated_heading(heading) for heading in headings]

    dead: list[str] = []
    for name in ("PROVENANCE_IDIOMS", "STATUS_IDIOMS"):
        full = getattr(drift_guard, name)
        for index, pattern in enumerate(full):
            monkeypatch.setattr(drift_guard, name, full[:index] + full[index + 1 :])
            changed = [
                drift_guard.classify_dated_heading(heading) for heading in headings
            ] != baseline
            monkeypatch.setattr(drift_guard, name, full)
            reaches = any(pattern.search(lead) for lead in lead_ins)
            if reaches and not changed:
                dead.append(pattern.pattern)

    assert not dead, "entries reaching a lead-in but changing no outcome:\n" + "\n".join(dead)
