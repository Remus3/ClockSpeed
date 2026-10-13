"""CS-1323 - three arms of the /done ritual, held as tests.

``.claude/commands/done.md`` is prose an agent executes, so these arms read it
for KEY PHRASES inside a labelled block rather than pinning whole paragraphs:
the voice may be tightened freely, but the rule may not go missing.

1. THE CS-700 WINDOW. From the flip block's step b until S12a no commit of any
   kind lands on the main tree's main, so a /done inside it commits nothing,
   runs no suite and pushes nothing, and says its hand-off is uncommitted. The
   window is read from a concrete signal: HEAD's own commit is the
   regeneration commit, the only one that writes the historical citation set.
2. THE GATE-REFUSAL PATH. The kit suite gate exits 3 WITHOUT RUNNING the suite
   when it refuses, so a refused push is retried exactly once; a second refusal
   stops the ritual with nothing pushed and a failed marker. A red suite is not
   a refusal and never retries the push.
3. NO BARE IGNORED PATH. A gitignored path spelled in backticks in a tracked
   record is a site the bare-path ladder answers on its R2 rung, and an
   undisclosed one turns the push suite red - CS-1321's first push.

Each arm also checks the fact its rule rests on against the code that owns it,
so the prose cannot drift away from the mechanism it describes. This module
spells no gitignored path itself: it builds the one it needs from components,
because a backticked spelling here would be an R2 site in a tracked file.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from tests.bare_path_guard import BARE_PATH_RE, DECLARED_UNTRACKED

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

DONE_MD: Final = ".claude/commands/done.md"
SUITE_GATE: Final = "ops/fleet_kit/fleet_suite_gate.py"
DONE_MARKER: Final = "ops/fleet_kit/fleet_done.py"
SHA_GATE: Final = "tools/sha_citation_gate.py"
HISTORICAL_FILE: Final = "tools/sha_citation_historical.json"

WINDOW_LABEL: Final = "THE CS-700 WINDOW"
REFUSAL_LABEL: Final = "GATE-REFUSAL PATH"
IGNORED_LABEL: Final = "NO BARE IGNORED PATH"

#: Where each labelled block OPENS - a bold paragraph or a checklist bullet - so a
#: passing mention of the label elsewhere is never read as the rule itself.
WINDOW_OPENER: Final = f"**{WINDOW_LABEL}"
REFUSAL_OPENER: Final = f"- [ ] {REFUSAL_LABEL}"
IGNORED_OPENER: Final = f"- [ ] {IGNORED_LABEL}"


def _text(rel: str) -> str:
    """A tracked file's text, decoded as 7-bit ASCII so a stray byte fails loudly."""
    return (REPO_ROOT / rel).read_bytes().decode("ascii")


def _steps() -> dict[str, str]:
    """done.md split at its level-2 headings, keyed by step number ('' = preamble)."""
    parts = re.split(r"^## ", _text(DONE_MD), flags=re.MULTILINE)
    steps = {"": parts[0]}
    for part in parts[1:]:
        number = re.match(r"(\d+)\.", part)
        steps[number.group(1) if number else part.split("\n", 1)[0]] = part
    return steps


def _block(text: str, opener: str) -> str:
    """The paragraph or checklist bullet that opens with ``opener``, up to its end.

    It ends at the next blank line or the next top-level checklist bullet,
    whichever comes first; an indented sub-bullet stays inside it.
    """
    start = text.find(opener)
    if start < 0:
        return ""
    ends = [i for i in (text.find("\n\n", start), text.find("\n- [ ]", start)) if i >= 0]
    return text[start : min(ends) if ends else len(text)]


# --- arm 1: the CS-700 window ----------------------------------------------


def test_the_cs700_window_is_read_from_a_concrete_signal() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert block, f"done.md carries no {WINDOW_LABEL} block"
    assert "step b" in block, "the window's opening bound is not named"
    assert "S12a" in block, "the window's closing bound is not named"
    assert "git diff-tree" in block, "the window has no git signal"
    assert "HEAD" in block, "the git signal does not read HEAD"
    assert HISTORICAL_FILE in block, "the signal does not name the regenerated set"


def test_the_cs700_window_commits_nothing_runs_no_suite_and_pushes_nothing() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert re.search(r"commits?\s+nothing", block), "the window does not forbid a commit"
    assert re.search(r"runs\s+no\s+(?:test\s+)?suite", block), "the window runs a suite"
    assert re.search(r"push(?:es)?\s+nothing", block), "the window does not forbid a push"
    assert re.search(r"UNCOMMITTED|uncommitted", block), "the hand-off is not said uncommitted"
    assert "first /done that pushes" in block, "the DONE-SLOW measurement is not deferred"


def test_the_commit_and_push_steps_defer_to_the_window() -> None:
    steps = _steps()

    for number in ("7", "8"):
        assert "CS-700 window" in steps.get(number, ""), f"step {number} ignores the window"


def test_the_window_signal_names_the_file_only_the_regeneration_writes() -> None:
    gate = _text(SHA_GATE)

    assert f'HISTORICAL_FILE: Final = "{HISTORICAL_FILE}"' in gate
    assert "--emit-historical" in gate


# --- arm 2: the gate-refusal path ------------------------------------------


def test_a_gate_refusal_retries_the_push_once_and_stops_on_the_second() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)

    assert block, f"step 8 carries no {REFUSAL_LABEL} bullet"
    assert "exit 3" in block, "a refusal is not identified by its exit code"
    assert "SUITE-GATE:" in block, "a refusal is not told apart from pytest's own exit 3"
    assert "WAIT_S" in block, "the gate's wait limit is not named at its owner"
    assert re.search(r"exactly\s+ONCE|exactly\s+once", block), "the retry is not bounded to one"
    assert re.search(r"second\s+refusal", block, re.IGNORECASE), "no stop on a second refusal"
    assert "--status failed" in block, "a second refusal does not mark the ritual failed"
    assert re.search(r"nothing\s+pushed", block), "a second refusal does not say nothing pushed"


def test_a_red_suite_never_retries_the_push() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)

    assert re.search(r"red\s+suite[^.]*never\s+retr", block, re.IGNORECASE)
    assert re.search(r"\bALONE\b|\balone\b", block), "a red suite's tests are not re-run alone"


def test_the_refusal_rule_matches_the_kit() -> None:
    gate = _text(SUITE_GATE)
    marker = _text(DONE_MARKER)
    messages = re.findall(r'raise GateRefused\(\s*f?"([^"]*)', gate)

    assert re.search(r"^WAIT_S = \d", gate, re.MULTILINE), "the kit no longer defines WAIT_S"
    assert re.search(r"except GateRefused[^\n]*\n[^\n]*\n\s*return 3\b", gate)
    assert messages, "the kit raises no GateRefused this arm can read"
    assert all(m.startswith("SUITE-GATE:") for m in messages)
    assert "--status done|failed [--reason TEXT]" in marker


# --- arm 3: no bare ignored path -------------------------------------------


def test_the_ledger_step_forbids_a_backticked_ignored_path() -> None:
    block = _block(_steps().get("2", ""), IGNORED_OPENER)

    assert block, f"step 2 carries no {IGNORED_LABEL} bullet"
    assert "gitignored" in block, "the rule does not name what it forbids"
    assert re.search(r"backtick", block, re.IGNORECASE), "the rule does not name the spelling"
    assert "tests/test_citation_tables.py" in block, "the rule does not name the arm's module"
    assert DECLARED_UNTRACKED in block, "the rule does not name the rung"
    assert "in words" in block, "the rule does not say how such a file may be named"


def test_every_record_writing_step_carries_the_rule() -> None:
    steps = _steps()

    for number in ("2", "4", "6"):
        assert IGNORED_LABEL in steps.get(number, ""), f"step {number} lacks the rule"


def test_the_rule_names_the_spelling_the_ladder_reads() -> None:
    record = "/".join(("ops", "loop", "control", "done_timing.json"))

    assert BARE_PATH_RE.search(f"`{record}`"), "a backticked path is no longer a site"
    assert not BARE_PATH_RE.search("this ritual's timing record"), "words became a site"
