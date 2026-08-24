"""CS-840 - every dated heading is a STATUS date or a PROVENANCE date, or guard (g) is RED.

THE CONTRADICTION THIS MODULE SETTLES. `CLAUDE.md` section 4 said that a doc
heading carrying an explicit date marks its own section historical, while
`docs/item_notes.md` says the blocks inside it are LIVE INSTRUCTIONS. Both
sentences shipped and neither had a cost, because the drift guard's
dated-heading arm REPORTED its population instead of failing on it. A guard
that reports cannot lose, which is exactly why the contradiction survived.

THE SURVIVING RULE IS A SHAPE RULE AND IT IS NOT A FILE LIST. A date in the
LEADING position of a heading is a STATUS date: it declares the section
historical. A date sitting AFTER a provenance verb - relocated, filed,
archived, measured, an operator decision, a numbered session - is a PROVENANCE
date: it records when the text was filed or when the measurement was taken,
and it marks the section's status not at all. A per-file carve-out was offered
and rejected, because a hand-maintained list of exempt files is the thing this
project keeps recording as the thing that rots.

WHERE THE FAILURE DIRECTION COMES FROM. The vocabulary of idioms is CLOSED. A
dated heading matching NEITHER family is RED, and the person who invented a
new date idiom is the person who has to say which of the two it is. That is a
red a correct tree cannot produce, which is what the report-only arm never had.

WHY THE TRACKED TREE MUST STAY GREEN, and it is not a convenience. Stripping a
date off a heading changes what an outside reader believes about that
section's status, so resolving this by dating fewer headings would be a
semantic change wearing a formatting hat. The tracked tree is the CONTROL: the
surviving rule has to leave every heading in it exactly as it stands.

THE THREE CONTROLS AGAINST A GUARD THAT GRADES ITSELF. A classifier that were
secretly a list of the exact headings present today would pass every green
assertion here, so three arms exist purely to catch that substitution.
GENERALISATION grades headings composed in this module and carried by no
tracked file - a lookup table returns NEITHER for all of them and goes red.
UNUSED ENTRIES asserts the vocabulary holds idioms the tree never uses - a
vocabulary fitted to today's headings holds none. PROPER SUBSTRING asserts no
vocabulary entry ever spans a whole heading - a vocabulary made OF headings
spans every one it matches.

NO POPULATION FIGURE IS WRITTEN IN THIS MODULE - CLAUDE.md section 4. Every
count below is derived from the tree on the run that asserts it. The tree
gains dated headings every session, and a restated figure would be a lie with
a timestamp on it.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"

GUARD_ID = "g"

# CS-840's named subject. The file whose header declares its blocks LIVE while
# every one of its section headings carries a date - the two sentences that
# contradicted each other until the shape rule separated them.
LIVE_INSTRUCTION_DOC = "docs/item_notes.md"

# A date this module owns, far outside the range any real entry uses. Finding
# it in a tracked file would itself be the bug.
PLANTED = "2031-02-03"


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


# ---------------------------------------------------------------------------
# Populations, every one derived from the guard's own enumeration and patterns
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tracked_dated_headings() -> list[tuple[str, int, str]]:
    """Every dated heading in the tracked tree, as (path, line number, heading).

    Derived through ``enumerate_files`` and ``dated_headings`` rather than
    through a second scan of this module's own. Two derivations from one regex
    agree by construction and would grade nothing; one derivation through the
    guard's own compiled patterns grades the guard.

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
    outright on an absent file rather than warning, and without it the driver
    would already be red - an exit code from a tree that was never green
    proves nothing about the arm under test.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The synthetic repository root, with the driver pointed at it.
    """
    root = tmp_path / "tree"
    (root / "config").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "config" / "ports.json", root / "config" / "ports.json")
    (root / "notes.md").write_bytes(b"# Notes\n\nNothing here carries a date.\n")
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
    matches: list[dict[str, Any]] = [guard for guard in report["guards"] if guard["id"] == GUARD_ID]
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
        The file's bytes as they stood BEFORE the plant, for the restore.
    """
    before = path.read_bytes()
    after = before + heading.encode("ascii") + b"\n\nBody text.\n"
    path.write_bytes(after)
    assert path.read_bytes() != before, "the plant did not apply"
    assert heading.encode("ascii") in path.read_bytes(), "the plant is not in the file"
    return before


# ---------------------------------------------------------------------------
# The failure direction - the half the report-only arm never had
# ---------------------------------------------------------------------------


def test_a_dated_heading_in_an_unclassifiable_idiom_turns_the_guard_red(
    clean_tree: Path,
) -> None:
    """The acceptance's core: the arm FAILS rather than reports.

    "Reviewed on" is a plausible provenance idiom that is deliberately NOT in
    the vocabulary. That is the case the item exists for - somebody writes a
    new date idiom, and the guard makes them say which of the two families it
    belongs to instead of silently absorbing it.
    """
    notes = clean_tree / "notes.md"
    heading = f"## Reviewed on {PLANTED} by the operator"
    plant(notes, heading)

    guard, _skips = drift_guard.guard_dated(clean_tree, [notes])

    assert guard["status"] == "FAIL"
    assert any(heading in line for line in guard["detail"]), (
        "a red that does not name the heading it tripped on is not actionable"
    )


def test_an_unclassifiable_heading_is_a_NON_ZERO_EXIT_naming_this_guard(  # noqa: N802
    clean_tree: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The whole transcript: pristine floor, plant, red, byte-identical revert, green.

    THE EXIT CODE IS THE ASSERTION THAT MATTERS. A red word in a report is
    what the arm already produced in every meaningful sense - a line of text
    nothing reads. CI reads the exit code, so the exit code is what has to
    move.

    The floor is asserted CLEAN before the plant. A red on a tree that was
    never green attributes to nothing.
    """
    notes = clean_tree / "notes.md"

    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "the floor must be clean or the red proves nothing"

    heading = f"### The great filing of {PLANTED}"
    pristine = plant(notes, heading)

    code, report = run_driver(capsys)
    assert guard_of(report)["status"] == "FAIL"
    assert report["drift"] == [GUARD_ID], "the red must attribute to this guard and no other"
    assert report["verdict"] == "DRIFT"
    assert code != 0, "a report is not a failure - the exit code is what CI reads"

    notes.write_bytes(pristine)
    assert notes.read_bytes() == pristine, "the revert did not land byte-identically"

    code, report = run_driver(capsys)
    assert (code, report["drift"]) == (0, []), "removing the plant must restore the green"


def test_the_red_names_the_two_families_the_author_has_to_choose_between(
    clean_tree: Path,
) -> None:
    """A guard that says only NO leaves the next author guessing."""
    notes = clean_tree / "notes.md"
    plant(notes, f"## Reviewed on {PLANTED} by the operator")

    guard, _skips = drift_guard.guard_dated(clean_tree, [notes])

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
        f"### NOTE - relocated from `ROADMAP.md` {PLANTED}",
        f"### detail - relocated to `docs/upstream_watch.md` {PLANTED}",
        f"### NOTE - filed {PLANTED} by the merger, on an operator ruling",
        f"#### Operator decision {PLANTED}: the flip ships from a FRESH history",
        f"#### Measured {PLANTED} (CS-999): the rule was broken the day after it was written",
        f"## Session 91 - {PLANTED} - four units land and one of them is refuted",
        f"### Archived {PLANTED} from `WAKEUP_NOTES.md` - session 91 at full fidelity",
        f"### 9.4 Spike results - session 2, {PLANTED}",
    ],
)
def test_a_date_after_a_provenance_verb_is_a_provenance_date(heading: str) -> None:
    assert drift_guard.classify_dated_heading(heading) == drift_guard.PROVENANCE_DATE


def test_the_verb_NEAREST_the_date_decides_when_a_heading_carries_two() -> None:  # noqa: N802
    """After a provenance verb means after the LAST one before the date.

    The tree already carries this shape - "Session 34 wakeup note - relocated
    2026-08-23" holds a session ordinal and a relocation verb, and the date
    sits after both. Reading the nearest one is the only reading of "the verb
    the date appears after" that does not need a precedence table.
    """
    assert (
        drift_guard.classify_dated_heading(f"## CS-999 - CLOSED, then relocated {PLANTED}")
        == drift_guard.PROVENANCE_DATE
    )
    assert (
        drift_guard.classify_dated_heading(f"## Relocated here, then CLOSED {PLANTED}")
        == drift_guard.STATUS_DATE
    )


def test_a_heading_with_no_date_at_all_is_not_this_guards_business() -> None:
    assert drift_guard.classify_dated_heading("## CS-999 - the item and its fence") is None


# ---------------------------------------------------------------------------
# The tracked tree is the control - it must be GREEN, unedited
# ---------------------------------------------------------------------------


def test_every_dated_heading_in_the_tracked_tree_classifies(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """Today's tree passes with no heading edited - the item's binding constraint.

    A rule whose first act is to demand edits to existing headings is the
    wrong rule: it would resolve the contradiction by dating fewer headings,
    which the item forbids.
    """
    assert tracked_dated_headings, "no dated headings found - this control proves nothing"

    unclassified = [
        f"{path}:{number}  {heading}"
        for path, number, heading in tracked_dated_headings
        if drift_guard.classify_dated_heading(heading) is None
    ]

    assert not unclassified, "unclassifiable dated headings:\n" + "\n".join(unclassified)


def test_the_real_tree_is_green_on_this_guard(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The end-to-end form of the control above, through the driver."""
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
    FILED or RELOCATED. Under the shape rule none of them marks its section
    historical, so the file's live-instruction header and the dated-heading
    rule no longer contradict each other - and not one heading had to lose its
    date for that to be true.
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
    """A partition only one side of which is ever taken is not a partition.

    If every tracked heading classified the same way, a classifier that
    returned that one answer unconditionally would pass every green assertion
    in this module.
    """
    families = {
        drift_guard.classify_dated_heading(heading)
        for _path, _number, heading in tracked_dated_headings
    }
    assert drift_guard.STATUS_DATE in families
    assert drift_guard.PROVENANCE_DATE in families


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
    file, which the first assertion proves rather than assumes. A classifier
    replaced by the set of headings present today returns NEITHER for all of
    them, and this arm goes red - which is the whole point of shipping it.
    """
    carried = {row[2].strip() for row in tracked_dated_headings}
    assert heading not in carried, "this control needs a heading the tracked tree does NOT carry"

    expected = getattr(drift_guard, f"{family}_DATE")
    assert drift_guard.classify_dated_heading(heading) == expected


def test_the_vocabulary_holds_idioms_the_tracked_tree_never_uses(
    tracked_dated_headings: list[tuple[str, int, str]],
) -> None:
    """UNUSED ENTRIES - the control that kills a vocabulary fitted to today's tree.

    A vocabulary derived by reading off the headings that happen to exist
    would contain no entry the tree does not use. This one does, so it is a
    vocabulary of idioms rather than a transcription of a population.
    """
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
    heading end to end, the entry would BE that heading, and the classifier
    would be grading the tree against itself. Both sides are derived on this
    run; neither is written down.
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
    assert len(drift_guard.DATE_IDIOMS) < len(headings), (
        "a vocabulary as large as the population it grades is a copy of it"
    )
