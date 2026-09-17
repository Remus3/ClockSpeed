"""CS-1126 - a ledger record lives under `## Entries`, never inside the shape example.

THE DEFECT. `docs/LEDGER.md` opens with an `## Entry shape` section whose fenced
code block is a TEMPLATE, and says the newest entry goes directly under the
`## Entries` heading. Records were prepended directly after that block's opening
fence instead - eight of them over two dates, then the lane's CS-930 closure - so
a reader of the template saw real records, and those records sat outside their
newest-first position. Nothing graded either fault.

WHAT THIS MODULE HOLDS. Every dated record heading (`### YYYY-MM-DD - ...`) in the
ledger sits inside the `## Entries` section, and nowhere else - the shape section
included. The section split is fence-aware, so a `## Entries` line typed INSIDE the
shape block's fence cannot open a counterfeit Entries section and launder a plant
sitting under it. Record headings themselves are matched regardless of fences,
because the stranded records this item exists for sat inside one.

THE BINDING. The lane worker is told where to write a record by one sentence in
`tools/headless-queue.md`, and the ledger's own preamble says it again. Both must
spell the SAME anchor this guard admits records under, and the lane sentence must
also name the shape section as the place never to write. Renaming a heading, or
rewording either sentence away from it, reddens an arm here, so the instruction and
the guard cannot drift apart.

THE VACUITY CONTROLS. A guard that finds no sections reports no strays, so the live
ledger must yield both sections, the template heading inside the shape section, and
an Entries population equal to a whole-file count taken by a different route.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: The ledger under guard, and the lane worker prompt that instructs writes to it.
LEDGER_PATH: Final = "docs/LEDGER.md"
PROMPT_PATH: Final = "tools/headless-queue.md"

#: The only section a dated record may live in.
ENTRIES_HEADING: Final = "## Entries"

#: The template section a record must never land in.
SHAPE_HEADING: Final = "## Entry shape"

#: The name given to the text above the first level-2 heading.
PREAMBLE: Final = "(preamble)"

#: A dated record heading. Digits only, so the template's `YYYY-MM-DD` is not one.
RECORD_HEADING: Final = re.compile(r"^### \d{4}-\d{2}-\d{2} - ")

#: A level-2 heading, and never a level-3 one.
SECTION_HEADING: Final = re.compile(r"^## (?!#)")

#: A fence opener or closer.
FENCE: Final = "```"

#: The template heading the shape section must still carry.
TEMPLATE_HEADING: Final = "### YYYY-MM-DD - <ITEM-ID> -"

#: How the lane prompt's ledger bullet begins. Spelled once.
PROMPT_BULLET_START: Final = "- **`docs/LEDGER.md`** gets the completion record"

#: How the ledger preamble's placement sentence begins. Spelled once.
PREAMBLE_SENTENCE_START: Final = "Newest entry goes directly under the"

#: The heading the tests plant. Carries the CS- prefix the item names.
PLANT: Final = "### 2099-01-01 - CS-0000 - PLANTED. A record inside the wrong section"


def read_repo_text(path: str) -> str:
    """Read a tracked text file as bytes and decode it, so no newline translation occurs.

    Args:
        path: The repo-relative path.

    Returns:
        The decoded text with its LF endings intact.
    """
    return (REPO_ROOT / path).read_bytes().decode("ascii")


def sections(text: str) -> list[tuple[str, list[str]]]:
    """Split a markdown document at its level-2 headings, outside fences only.

    Args:
        text: The document.

    Returns:
        Ordered (heading, body lines) pairs. The first pair is the preamble.
    """
    out: list[tuple[str, list[str]]] = [(PREAMBLE, [])]
    in_fence = False
    for line in text.split("\n"):
        if line.startswith(FENCE):
            in_fence = not in_fence
        elif not in_fence and SECTION_HEADING.match(line):
            out.append((line, []))
            continue
        out[-1][1].append(line)
    return out


def stranded_records(text: str) -> list[tuple[str, str]]:
    """Every dated record heading that sits outside the Entries section.

    Args:
        text: The ledger.

    Returns:
        (section heading, record heading) for each stray, in document order.
    """
    return [
        (heading, line)
        for heading, body in sections(text)
        if heading != ENTRIES_HEADING
        for line in body
        if RECORD_HEADING.match(line)
    ]


def section_body(text: str, heading: str) -> list[str]:
    """The body lines of every section carrying a heading, concatenated.

    Args:
        text: The document.
        heading: The exact level-2 heading line.

    Returns:
        The lines, empty when no such section exists.
    """
    return [line for name, body in sections(text) if name == heading for line in body]


def plant_after_shape_fence(text: str, heading: str) -> str:
    """Insert a heading directly after the shape section's opening fence.

    This is the exact position the stranded records were written to.

    Args:
        text: The ledger.
        heading: The line to insert.

    Returns:
        The planted ledger.
    """
    start = text.index("\n" + SHAPE_HEADING + "\n")
    fence = text.index("\n" + FENCE + "\n", start) + len(FENCE) + 2
    return text[:fence] + heading + "\n\n" + text[fence:]


def paragraph_starting(text: str, start: str) -> str:
    """The paragraph or bullet that begins with a phrase, joined onto one line.

    Args:
        text: The document.
        start: The phrase the paragraph begins with, after indentation.

    Returns:
        The text up to the next blank line or the next bullet.

    Raises:
        AssertionError: When the phrase begins no line.
    """
    lines = text.split("\n")
    first = next((i for i, line in enumerate(lines) if line.lstrip().startswith(start)), None)
    assert first is not None, f"no line begins with {start!r}"
    taken = [lines[first].strip()]
    for line in lines[first + 1 :]:
        if not line.strip() or line.lstrip().startswith("- "):
            break
        taken.append(line.strip())
    return " ".join(taken)


def anchor_problems(sentence: str, *, requires_never_shape: bool) -> list[str]:
    """What a placement sentence fails to say about where a record goes.

    Args:
        sentence: The sentence, joined onto one line.
        requires_never_shape: Whether it must also forbid the shape section.

    Returns:
        One message per missing clause, empty when the sentence names the anchor.
    """
    problems = []
    if f"`{ENTRIES_HEADING}`" not in sentence:
        problems.append(f"does not name `{ENTRIES_HEADING}` as the anchor")
    named = set(re.findall(r"`(## [^`]+)`", sentence))
    stray = named - {ENTRIES_HEADING, SHAPE_HEADING}
    if stray:
        problems.append(f"names a heading the guard does not read: {sorted(stray)}")
    if requires_never_shape and not re.search(
        r"\bnever\b[^.]*`" + re.escape(SHAPE_HEADING) + "`", sentence, re.IGNORECASE
    ):
        problems.append(f"does not forbid the `{SHAPE_HEADING}` section")
    return problems


# ---------------------------------------------------------------------------
# The live ledger.
# ---------------------------------------------------------------------------


def test_no_dated_record_sits_outside_the_entries_section() -> None:
    """The live ledger strands no record in the shape block or anywhere above Entries."""
    stray = stranded_records(read_repo_text(LEDGER_PATH))
    count = len(stray)
    assert count == 0, f"{count} record heading(s) outside {ENTRIES_HEADING}: {stray[:10]}"


def test_control_the_live_ledger_yields_both_sections_and_the_template() -> None:
    """Anti-vacuity: a split that found no sections would report no strays."""
    text = read_repo_text(LEDGER_PATH)
    names = [name for name, _body in sections(text)]
    assert names.count(ENTRIES_HEADING) == 1
    assert names.count(SHAPE_HEADING) == 1
    assert names.index(SHAPE_HEADING) < names.index(ENTRIES_HEADING)
    shape = section_body(text, SHAPE_HEADING)
    assert any(line.startswith(TEMPLATE_HEADING) for line in shape)


def test_control_the_entries_population_matches_a_whole_file_count() -> None:
    """Anti-vacuity by a second route: every dated heading in the file is under Entries."""
    text = read_repo_text(LEDGER_PATH)
    whole_file = sum(1 for line in text.split("\n") if RECORD_HEADING.match(line))
    under_entries = sum(
        1 for line in section_body(text, ENTRIES_HEADING) if RECORD_HEADING.match(line)
    )
    assert under_entries > 0
    assert under_entries == whole_file


# ---------------------------------------------------------------------------
# The arm, driven over plants.
# ---------------------------------------------------------------------------


def test_a_record_planted_inside_the_shape_block_is_reported() -> None:
    """The exact fault CS-1126 filed: a CS- heading right after the shape fence."""
    planted = plant_after_shape_fence(read_repo_text(LEDGER_PATH), PLANT)
    assert stranded_records(planted) == [(SHAPE_HEADING, PLANT)]


def test_a_record_planted_under_entries_is_not_reported() -> None:
    """The arm reports position, not the presence of a record."""
    text = read_repo_text(LEDGER_PATH)
    anchor = "\n" + ENTRIES_HEADING + "\n\n"
    at = text.index(anchor) + len(anchor)
    planted = text[:at] + PLANT + "\n\n" + text[at:]
    assert stranded_records(planted) == []


def test_a_counterfeit_entries_heading_inside_the_fence_does_not_launder_a_plant() -> None:
    """A `## Entries` line typed inside the template fence opens no section."""
    planted = plant_after_shape_fence(read_repo_text(LEDGER_PATH), ENTRIES_HEADING + "\n\n" + PLANT)
    assert stranded_records(planted) == [(SHAPE_HEADING, PLANT)]


def test_a_record_in_the_preamble_or_a_later_section_is_reported() -> None:
    """Every non-Entries section is graded, not only the shape section."""
    doc = "\n".join(
        [
            "# Ledger",
            PLANT,
            SHAPE_HEADING,
            ENTRIES_HEADING,
            "### 2099-01-02 - CS-0001 - fine",
            "## Afterword",
            PLANT,
        ]
    )
    assert stranded_records(doc) == [(PREAMBLE, PLANT), ("## Afterword", PLANT)]


# ---------------------------------------------------------------------------
# The binding between the instruction and the guard.
# ---------------------------------------------------------------------------


def test_the_lane_prompt_names_the_entries_heading_as_the_insertion_anchor() -> None:
    """The lane's ledger bullet names the anchor this guard reads, and forbids the shape."""
    sentence = paragraph_starting(read_repo_text(PROMPT_PATH), PROMPT_BULLET_START)
    assert anchor_problems(sentence, requires_never_shape=True) == []


def test_the_ledger_preamble_names_the_same_anchor() -> None:
    """The ledger's own placement sentence and the guard spell one heading."""
    text = read_repo_text(LEDGER_PATH)
    sentence = paragraph_starting(
        "\n".join(section_body(text, SHAPE_HEADING)), PREAMBLE_SENTENCE_START
    )
    assert anchor_problems(sentence, requires_never_shape=False) == []


def test_control_a_sentence_naming_another_anchor_is_reported() -> None:
    """The binding reddens on a renamed anchor and on a dropped prohibition."""
    renamed = (
        "- gets the record, directly under the `## Records` heading, never in `## Entry shape`."
    )
    missing_anchor_and_stray_heading = 2
    assert len(anchor_problems(renamed, requires_never_shape=True)) == (
        missing_anchor_and_stray_heading
    )
    unforbidden = "- gets the record, directly under the `## Entries` heading."
    assert len(anchor_problems(unforbidden, requires_never_shape=True)) == 1
    assert anchor_problems(unforbidden, requires_never_shape=False) == []


def test_control_the_bullet_extraction_stops_at_the_next_bullet() -> None:
    """A bullet read that ran on would let a later bullet satisfy the binding."""
    doc = "- **first** one\n  continued\n- `## Entries` in the second bullet\n"
    assert paragraph_starting(doc, "- **first**") == "- **first** one continued"
