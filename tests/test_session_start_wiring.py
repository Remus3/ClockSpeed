"""CS-952: the published session-start claim must match what a clean checkout wires.

THE DEFECT THIS GRADES. `tools/inbox_watch.py` is invoked by a `SessionStart`
hook that was declared in `.claude/settings.local.json`, which `.gitignore`
excludes at `*.local.json`. The wiring is therefore a property of ONE WORKING
COPY. `CLAUDE.md` section 2.2 publishes the firing as a property of the TOOL,
and the two were reported as the same thing - here and, more expensively, on the
cross-project channel, where at least one sibling asked directly whether this
repository fires a watcher without the operator asking and was told yes.

THIS IS THE SECOND TIME. `docs/LEDGER.md` records CS-931: the same tooling map
named a `SessionStart` hook for `tools/facts_probe.py` that this repository does
not have, and it was closed by correcting the sentence. Nothing was left behind
that would notice the third instance, so the row went stale again with a
different tool's name in it. A guard is what makes the class stay closed.

WHAT THIS MODULE ASSERTS IS AGREEMENT, NOT A PARTICULAR ANSWER. CS-952's
acceptance is disjunctive - either the wiring is tracked, or the claim is
corrected - so grading either branch alone would fail the repository for taking
the other. The property here is that the TRACKED CLAIM and the TRACKED WIRING
say the same thing. It goes green when the hook is tracked, green when the row
says the tool is run by hand, and red only when the row promises firing that a
fresh clone does not get.

WHY THE CHECKOUT IS TAKEN FROM GIT AND NEVER FROM THE FILESYSTEM. The whole
defect is that the working tree has wiring the repository does not. A reader
that walked `.claude/` on disk would find `settings.local.json`, report the hook
present, and pass green on precisely the tree that motivated the item - the
vacuous check wearing the costume of the guard. `_clean_checkout` therefore
materialises HEAD through `git archive` into a temporary directory, and
`test_untracked_wiring_does_not_satisfy_the_reader` is the negative control that
proves it: a repository whose only wiring is untracked reads as UNWIRED.

WHICH BRANCH THIS REPOSITORY TOOK, AND THE MEASUREMENT THAT DECIDED IT. The
tracking branch was proposed, and an adjudicator granted the frozen-file edit
with conditions. AN ADVERSARIAL PASS THEN REFUTED THE PREMISE and the grant was
NOT SPENT. The measurement: `moon_sync_inbox/` is itself gitignored, so a fresh
clone has no channel to read, and the tool answers that state with exit 3. A
`SessionStart` hook that exits non-zero does not get its stdout injected, so the
tracked wiring would have fired, failed and said nothing - moving the published
claim from FALSE to false in a harder-to-see way, at the cost of a frozen-file
exception. The correction branch was taken instead, which is also what
`docs/LEDGER.md` records for CS-931, the same defect one tool earlier.

THIS GUARD READS HEAD, NOT THE WORKING TREE AND NOT THE INDEX, and the cost of
that is stated rather than discovered. A clone materialises HEAD, so HEAD is the
honest subject. The consequence is that the commit which REPAIRS the row is the
commit that turns this arm green - it cannot go green before it exists. The
enforcement point is therefore the pre-push suite, which grades a HEAD that is
already written, and that is the right place for it: a push is the first moment
the defect could reach a clone.

WHAT THIS DELIBERATELY DOES NOT COVER, stated rather than left silent.

  1. It grades the CLAIM AS PUBLISHED IN `CLAUDE.md`'s section 2.2 tooling map,
     which is the row auto-loaded into every session and the one that misled
     this project twice. It does NOT grade prose elsewhere in the tree, and it
     cannot reach the copies of the claim already delivered to sibling
     repositories - those are outbound notes this repository does not hold, and
     retracting one is a channel action, not a test.
  2. It grades that a clean checkout DECLARES the hook, not that the hook RUNS.
     Whether a given client honours a tracked project hook - trust prompts,
     working directory, an interpreter named `python` being on PATH - is outside
     any test in this repository. A green here means the wiring ships, and
     nothing stronger may be published from it.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from tests.conftest import run_git

#: The tool whose firing property the tooling map publishes.
WATCHED_TOOL = "tools/inbox_watch.py"

#: The paths a clean checkout must supply for this question to be answerable at
#: all. A pathspec-limited archive keeps the extraction cheap and makes the
#: scope of the probe explicit rather than incidental.
CHECKOUT_PATHSPEC = (".claude", "CLAUDE.md")

#: Substrings that, in a section 2.2 tooling-map row, assert the tool fires on
#: its own at session start. `run BY HAND` - the wording CS-931 left behind on
#: the `tools/facts_probe.py` row - is deliberately absent from this list.
FIRING_PHRASES = (
    "at session start",
    "on session start",
    "sessionstart",
    "every session start",
)

#: The claim row the control repositories publish, so every control states the
#: firing property and only the WIRING differs between them.
_CLAIM_ROW = "| `tools/inbox_watch.py` | at session start |" + "\n"

#: The wording that withdraws the claim. A row carrying one of these is stating
#: the honest answer for an unwired tool, so it is not a firing claim even if it
#: also mentions session start in passing.
WITHDRAWAL_PHRASES = (
    "by hand",
    "not a hook",
)


def _clean_checkout(repo_root: Path, destination: Path) -> Path:
    """Materialise HEAD's tracked content for CHECKOUT_PATHSPEC under `destination`.

    Uses `git archive` rather than a filesystem copy so that an untracked file
    cannot reach the result. That is the whole point of the probe, and
    `test_untracked_wiring_does_not_satisfy_the_reader` grades it.
    """
    archive = destination / "head.tar"
    destination.mkdir(parents=True, exist_ok=True)
    tree = destination / "tree"
    tree.mkdir()
    proc = run_git(
        repo_root,
        "archive",
        "--format=tar",
        "-o",
        str(archive),
        "HEAD",
        "--",
        *CHECKOUT_PATHSPEC,
    )
    if proc is None or proc.returncode != 0:
        pytest.skip("git archive is unavailable, so a clean checkout cannot be taken")
    with tarfile.open(archive) as bundle:
        # The unfiltered fallback carries a reasoned S202 suppression rather
        # than a silent one. The archive is not third-party input: it was
        # produced by `git archive` from this repository's own HEAD, into a
        # temporary directory, four lines above. The `data` filter is used
        # wherever the interpreter has it, which is what the rule asks for.
        try:
            bundle.extractall(tree, filter="data")
        except TypeError:  # pragma: no cover - interpreters before the filter arg
            bundle.extractall(tree)  # noqa: S202
    return tree


def _session_start_commands(tree: Path, tool: str) -> list[str]:
    """Return every SessionStart hook command in `tree` that invokes `tool`.

    Searches EVERY json file under `.claude/`, not `settings.json` alone. The
    wiring moving to another tracked settings file is a repair, not an evasion,
    and a reader that named one filename would call that repair a regression.
    """
    found: list[str] = []
    for path in sorted((tree / ".claude").rglob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict):
            continue
        hooks = document.get("hooks")
        if not isinstance(hooks, dict):
            continue
        for matcher in hooks.get("SessionStart", []) or []:
            if not isinstance(matcher, dict):
                continue
            for hook in matcher.get("hooks", []) or []:
                if not isinstance(hook, dict):
                    continue
                command = hook.get("command")
                if isinstance(command, str) and tool in command.replace("\\", "/"):
                    found.append(command)
    return found


def _tooling_map_rows(claude_md: Path, tool: str) -> list[str]:
    """Return the section 2.2 table rows that name `tool`.

    A row is a markdown table line - it starts with a pipe - so a sentence of
    surrounding prose that happens to name the tool is not mistaken for the
    published property.
    """
    rows: list[str] = []
    for line in claude_md.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and tool in stripped:
            rows.append(stripped)
    return rows


def _claims_firing(row: str) -> bool:
    """Whether a tooling-map row asserts the tool fires on its own."""
    lowered = row.lower()
    if any(phrase in lowered for phrase in WITHDRAWAL_PHRASES):
        return False
    return any(phrase in lowered for phrase in FIRING_PHRASES)


def test_the_claim_reader_sees_a_firing_row_and_a_withdrawn_one() -> None:
    """Control on the DOC side of the comparison.

    An agreement guard passes trivially if it cannot see the claim, so the
    reader is exercised against both wordings before its verdict is trusted.
    """
    firing = "| `tools/inbox_watch.py` | Unread items at session start |"
    withdrawn = "| `tools/facts_probe.py` | Fact set. Run BY HAND from `/drift-guard` |"
    assert _claims_firing(firing) is True
    assert _claims_firing(withdrawn) is False


def test_the_tooling_map_still_has_a_row_for_the_watcher(repo_root: Path, tmp_path: Path) -> None:
    """The comparison is only meaningful while the row exists.

    If the row is ever deleted outright, this arm goes red rather than letting
    the agreement arm pass by having nothing to compare.
    """
    tree = _clean_checkout(repo_root, tmp_path)
    rows = _tooling_map_rows(tree / "CLAUDE.md", WATCHED_TOOL)
    assert len(rows) == 1


def test_untracked_wiring_does_not_satisfy_the_reader(tmp_path: Path) -> None:
    """NEGATIVE CONTROL, and the arm that makes the whole module non-vacuous.

    Builds a repository whose SessionStart wiring exists ONLY in an untracked
    file - the exact shape of this project on the day CS-952 was filed - and
    asserts the clean checkout reads as unwired. Without this arm, a reader that
    silently fell back to the filesystem would pass on the defective tree.
    """
    origin = _scratch_repo(tmp_path / "origin")
    (origin / ".claude").mkdir()
    (origin / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": []}}), encoding="utf-8"
    )
    (origin / "CLAUDE.md").write_text(_CLAIM_ROW, encoding="utf-8")
    _commit_all(origin)
    # Written AFTER the commit, so it is present on disk and absent from HEAD.
    (origin / ".claude" / "settings.local.json").write_text(
        json.dumps(_wiring_document()), encoding="utf-8"
    )
    tree = _clean_checkout(origin, tmp_path / "probe")
    assert _session_start_commands(tree, WATCHED_TOOL) == []


def test_tracked_wiring_does_satisfy_the_reader(tmp_path: Path) -> None:
    """POSITIVE CONTROL. A green from the agreement arm has to be capable of red.

    Same repository as the negative control except that the wiring is committed.
    If this arm ever fails, the reader has stopped recognising wiring and every
    other verdict in this module is a statement about nothing.
    """
    origin = _scratch_repo(tmp_path / "origin")
    (origin / ".claude").mkdir()
    (origin / ".claude" / "settings.json").write_text(
        json.dumps(_wiring_document()), encoding="utf-8"
    )
    (origin / "CLAUDE.md").write_text(_CLAIM_ROW, encoding="utf-8")
    _commit_all(origin)
    tree = _clean_checkout(origin, tmp_path / "probe")
    assert len(_session_start_commands(tree, WATCHED_TOOL)) == 1


def test_wiring_in_any_tracked_claude_json_counts(tmp_path: Path) -> None:
    """SCOPE. The reader is not keyed to the filename `settings.json`.

    Moving the declaration into another tracked file under `.claude/` is a
    legitimate repair. A reader that named one file would grade that repair red,
    which would push the project back towards the untracked answer.
    """
    origin = _scratch_repo(tmp_path / "origin")
    (origin / ".claude").mkdir()
    (origin / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": []}}), encoding="utf-8"
    )
    (origin / ".claude" / "hooks.json").write_text(json.dumps(_wiring_document()), encoding="utf-8")
    (origin / "CLAUDE.md").write_text(_CLAIM_ROW, encoding="utf-8")
    _commit_all(origin)
    tree = _clean_checkout(origin, tmp_path / "probe")
    assert len(_session_start_commands(tree, WATCHED_TOOL)) == 1


def test_a_clean_checkout_wires_what_the_tooling_map_claims(
    repo_root: Path, tmp_path: Path
) -> None:
    """THE LOAD-BEARING ARM. The published claim and the shipped wiring agree.

    Red means a fresh clone of this repository does not do what `CLAUDE.md`
    tells every session it does. Either branch of CS-952's acceptance turns it
    green; nothing else does.
    """
    tree = _clean_checkout(repo_root, tmp_path)
    rows = _tooling_map_rows(tree / "CLAUDE.md", WATCHED_TOOL)
    claimed = any(_claims_firing(row) for row in rows)
    wired = bool(_session_start_commands(tree, WATCHED_TOOL))
    disagreement = f"claimed_firing={claimed} wired_in_clean_checkout={wired}"
    assert (not claimed) or wired, disagreement


def _wiring_document() -> dict[str, object]:
    """The settings shape that declares the watcher's SessionStart hook."""
    return {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "python tools/inbox_watch.py"}]}
            ]
        }
    }


def _scratch_repo(root: Path) -> Path:
    """Initialise an empty git repository at `root`, or skip if git is absent."""
    root.mkdir(parents=True)
    proc = run_git(root.parent, "init", "--quiet", str(root))
    if proc is None or proc.returncode != 0:
        pytest.skip("git is unavailable, so the controls cannot be built")
    return root


def _commit_all(root: Path) -> None:
    """Commit everything currently on disk under `root`.

    Identity is supplied per-command so the controls do not depend on, and do
    not touch, any configured user identity.
    """
    run_git(root, "add", "-A")
    proc = run_git(
        root,
        "-c",
        "user.name=probe",
        "-c",
        "user.email=probe@invalid",
        "commit",
        "--quiet",
        "--no-verify",
        "-m",
        "control",
    )
    if proc is None or proc.returncode != 0:
        detail = "" if proc is None else proc.stderr.decode("utf-8", "replace")
        pytest.skip(f"the control repository could not be committed: {detail}")
