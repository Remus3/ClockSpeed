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
NOT SPENT. The measurement then: `moon_sync_inbox/` is itself gitignored, so a
fresh clone has no channel to read; the tool gave that state a non-zero code,
which the refusal argued would cost a `SessionStart` hook its stdout, so the
tracked wiring would have fired, failed and said nothing. What a client does
with a hook's stdout is a property of the client, not of this repository, and
no test here grades it. The correction branch was taken instead, which is
also what `docs/LEDGER.md` records for CS-931, the same defect one tool
earlier.

THAT REASON IS RETIRED AND THE REFUSAL WAS RE-DERIVED WITHOUT IT (CS-1101).
CS-1095 made every default path of the watcher return 0. The old codes moved
behind `--strict`. So today the tool answers that state with exit 0 and
prints its `UNMEASURED` banner - a tracked hook WOULD speak. The refusal still holds,
on a different reason: the watcher resolves its root from its own file, and the
channel exists only in the one working copy that is already wired locally. In a
fresh clone and in every worktree - the default session shape here - a tracked
hook could only ever announce that the channel is absent. It would surface no
item the local wiring does not, at the cost of a frozen-file exception. Giving a
clone or a worktree a channel to read is a different item, and is the thing to
do before tracking the wiring is worth re-pitching.
`test_each_live_docstring_states_the_exit_code_the_hook_actually_gets` runs the
watcher as the hook does and grades the code stated above against the code it
returns, so this paragraph cannot go stale a second time without going red.

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

import ast
import io
import json
import re
import subprocess
import sys
import tarfile
import tokenize
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.conftest import run_git
from tests.git_env import REPO_LOCATING, scrubbed_env

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


# ---------------------------------------------------------------------------
# CS-1101 - the refusal's stated exit code is graded against the real return.
# ---------------------------------------------------------------------------

#: The sentence shape both live docstrings use to state what the watcher
#: returns in a tree with no channel. It is deliberately the shape the ORIGINAL
#: false sentence had, so the arm read the stale copies at the SHA it was
#: written against, and a history mention of a retired code is written in a
#: different shape precisely so that it is not mistaken for the current claim.
CLAIM_PATTERN: Final = re.compile(
    r"answers\s+that(?:\s+state)?\s+with\s+exit\s+(\d+)", re.IGNORECASE
)

#: EVERY exit code a docstring states, in any sentence shape. `CLAIM_PATTERN`
#: only LOCATES the claim; grading reads every code this one matches, so a
#: sentence stating a contradicting code cannot sit beside a decoy written in
#: the anchored shape and pass. Each code is graded by the SENTENCE it sits in:
#: one naming `--strict` against the measured strict return, any other against
#: the measured default return.
CODE_PATTERN: Final = re.compile(
    r"\b(?:exit(?:s|ed|ing)?|return(?:s|ed|ing)?|code)\s+(?:with\s+)?"
    r"(?:(?:exit\s+)?code\s+)?(\d+)\b",
    re.IGNORECASE,
)

#: The two live docstrings that argue the CS-952 refusal from the exit code.
LIVE_CLAIM_FILES: Final = ("tests/test_session_start_wiring.py", WATCHED_TOOL)

#: The deep archive holding dated copies of the same premise. Annotated beside
#: each copy, never rewritten - it is a record of what was measured at the time.
ARCHIVE_FILE: Final = "docs/history_notes.md"

#: The annotation every archive copy of the premise must carry in its paragraph.
SUPERSESSION_MARKER: Final = "SUPERSEDED BY CS-1095"

#: The hook's command line, shared with `_wiring_document` so the controls and
#: the CS-1101 probe cannot describe two different hooks.
HOOK_COMMAND: Final = "python " + WATCHED_TOOL

#: A SessionStart payload, so the watcher reads its labels and never waits on
#: a stdin that does not close.
_HOOK_PAYLOAD: Final = json.dumps(
    {"hook_event_name": "SessionStart", "source": "startup", "session_id": "cs1101-probe"}
)


def _stated_exit_codes(text: str) -> list[int]:
    """Every exit code `text` states for the no-channel state, in order.

    Reads PROSE ONLY. It never imports or runs the watcher, so it cannot learn
    the answer from the thing it is being compared with.
    """
    return [int(match.group(1)) for match in CLAIM_PATTERN.finditer(text)]


def _all_stated_codes(text: str) -> list[int]:
    """Every exit code `text` states in any shape, in order. Prose only."""
    return [int(match.group(1)) for match in CODE_PATTERN.finditer(text)]


#: Why a code about something other than the watcher is still red, carried in
#: the assertion so the next author is told rather than left to guess.
GRADING_RULE: Final = (
    "every exit code a live docstring states is read as a claim about the watcher's"
    " no-channel return: a code in a sentence naming --strict is graded against the"
    " measured --strict return, every other code against the measured default return."
    " A code about something else (e.g. a hook that exits 2 blocks) is red too - write"
    " it without the number."
)


def _misgraded_codes(text: str, default: int, strict: int) -> list[str]:
    """Each stated code that disagrees with the return its sentence is graded against.

    Prose only - the two returns are passed in, measured by the caller.
    """
    wrong: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(text.split())):
        mode, expected = ("--strict", strict) if "--strict" in sentence else ("default", default)
        wrong.extend(
            f"{code} (graded against the {mode} return {expected})"
            for code in _all_stated_codes(sentence)
            if code != expected
        )
    return wrong


def _module_docstring(path: Path) -> str:
    """The module docstring of `path`, parsed from source and never imported."""
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def _isolated_git_env(base: Path) -> dict[str, str]:
    """This process's environment with git cut off from every real repository.

    Repository-locating variables are removed through `tests/git_env.py` - a
    push from a worktree exports `GIT_DIR`, and a git child that inherits it
    acts on the real repository. The user's global and system configuration
    are replaced by an empty file, so no operator setting shapes the decoys.
    The scrub is ASSERTED rather than trusted, upper-cased, because Windows
    folds environment keys and a mixed-case pop removes nothing.
    """
    empty = base / "gitconfig-empty"
    empty.write_text("", encoding="ascii")
    env = scrubbed_env()
    env["GIT_CONFIG_GLOBAL"] = str(empty)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    survivors = sorted(key for key in env if key.upper() in REPO_LOCATING)
    assert survivors == [], f"repository-locating variables survived the scrub: {survivors}"
    return env


#: The program `_git` runs, read at CALL time so the CS-1107 plant can swap in a
#: child that hangs. Never an absolute path - PATH resolves it.
GIT_PROGRAM: Final[tuple[str, ...]] = ("git",)

#: Seconds `_git` waits for one decoy-tree git command, read at CALL time so the
#: CS-1107 plant can shrink it.
GIT_TIMEOUT_SECONDS: Final[float] = 120


def _git(cwd: Path, env: dict[str, str], *args: str) -> None:
    """Run one git command in a decoy tree, or skip when git is not installed.

    A TIMEOUT IS RED, NEVER A SKIP (CS-1107). `subprocess.SubprocessError` once
    sent a hung git down the not-installed skip, so the CS-1101 arms stopped
    grading without a red. Only an `OSError` - no program to start - skips;
    `test_a_git_timeout_in_a_decoy_tree_fails_rather_than_skips` plants the hang.
    """
    proc: subprocess.CompletedProcess[str] | None = None
    try:
        proc = subprocess.run(
            [*GIT_PROGRAM, "-c", "user.name=probe", "-c", "user.email=probe@invalid", *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # Bound outside the handler, so the red carries no chained exception
        # and no rendered command line.
        proc = None
    except OSError:
        pytest.skip("git is unavailable, so the decoy checkouts cannot be built")
    timed_out = proc is None
    assert not timed_out, (
        f"git {args[0]} TIMED OUT in a decoy tree after {GIT_TIMEOUT_SECONDS}s -"
        " a hung git is a failure, never a skip"
    )
    assert proc is not None
    code = proc.returncode
    assert code == 0, f"git {args[0]} failed in a decoy tree with exit {code}"


def _decoy_checkout(tree: Path, repo_root: Path, env: dict[str, str]) -> Path:
    """A REAL git checkout shaped like the main one: a channel with a note, and the tool."""
    (tree / "moon_sync_inbox").mkdir(parents=True)
    (tree / "moon_sync_inbox" / f"cs1101-decoy-{tree.name}.md").write_text(
        "decoy\n", encoding="ascii"
    )
    (tree / "tools").mkdir()
    (tree / WATCHED_TOOL).write_bytes((repo_root / WATCHED_TOOL).read_bytes())
    _git(tree, env, "init", "--quiet")
    _git(tree, env, "add", WATCHED_TOOL)
    _git(tree, env, "commit", "--quiet", "--no-verify", "-m", "decoy")
    return tree


class HookLayout(NamedTuple):
    """Where one probe run's watcher lives, where it starts, what sits above it."""

    root: Path
    cwd: Path
    ancestor: Path
    env: dict[str, str]


def _hook_layout(base: Path, repo_root: Path) -> HookLayout:
    """Mirror a worktree nested under a main checkout that HAS the channel.

    `ancestor` is a real git checkout holding a channel and the tool. `root` is
    a real `git worktree add` of it at `.claude/worktrees/<name>`, which is
    exactly how this repository's worktrees sit under the one working copy that
    holds `moon_sync_inbox/` - the channel is untracked, so the worktree has
    none. `cwd` is a SECOND real checkout holding a channel and the tool.

    NO GIT COMMAND RUNS INSIDE A REAL REPOSITORY. The base is asserted to have
    no `.git` above it before anything is built, and every command gets the
    isolated environment.
    """
    outer = [parent for parent in base.resolve().parents if (parent / ".git").exists()]
    assert outer == [], "the decoy base sits inside a git repository"
    env = _isolated_git_env(base)
    ancestor = _decoy_checkout(base / "ancestor", repo_root, env)
    root = ancestor / ".claude" / "worktrees" / "cs1101-copy"
    _git(ancestor, env, "worktree", "add", "--detach", "--quiet", str(root), "HEAD")
    # Byte-identical whatever checkout filter git applied.
    (root / WATCHED_TOOL).write_bytes((repo_root / WATCHED_TOOL).read_bytes())
    cwd = _decoy_checkout(base / "cwd", repo_root, env)
    return HookLayout(root=root, cwd=cwd, ancestor=ancestor, env=env)


def _run_like_the_hook(layout: HookLayout, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run the watcher as the SessionStart hook does, from a tree with no channel.

    ACROSS A PROCESS BOUNDARY, on a byte-identical copy of the watcher in
    `layout.root`. The copy is what isolates the run: the watcher resolves its
    root from its OWN file, so running the real file would read and write the
    real checkout, invocation log included.

    EVERY OTHER ROOT IN REACH HOLDS A CHANNEL - the ancestor the copy is a git
    worktree of, the working directory it is started from (itself a git
    checkout), and `CLAUDE_PROJECT_DIR`, which the child is given pointing at
    the ancestor. That is the CS-952 refusal's stated reason made observable.
    The copy is named by ABSOLUTE path rather than by the hook's relative
    `tools/inbox_watch.py`, which is the one
    departure from `HOOK_COMMAND`, and it is the departure the check needs.

    `sys.executable` stands in for the hook's bare `python`, deliberately: the
    subject is what the watcher returns, and which interpreter PATH resolves on
    a given client is outside this repository - the module docstring already
    names it as not covered.
    """
    assert not (layout.root / "moon_sync_inbox").exists()
    assert (layout.root / ".git").is_file(), "the copy is not in a git worktree"
    assert (layout.cwd / "moon_sync_inbox").is_dir()
    assert (layout.cwd / ".git").is_dir()
    assert (layout.ancestor / "moon_sync_inbox").is_dir()
    assert (layout.ancestor / ".git").is_dir()
    command = HOOK_COMMAND.split()
    assert command == ["python", WATCHED_TOOL]
    child = dict(layout.env)
    child["CLAUDE_PROJECT_DIR"] = str(layout.ancestor)
    survivors = sorted(key for key in child if key.upper() in REPO_LOCATING)
    assert survivors == [], f"repository-locating variables reached the child: {survivors}"
    return subprocess.run(
        [sys.executable, str(layout.root / WATCHED_TOOL), *extra],
        cwd=layout.cwd,
        env=child,
        input=_HOOK_PAYLOAD,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


class HookRuns(NamedTuple):
    """The default run and the `--strict` run, each in its own layout."""

    default: HookLayout
    default_run: subprocess.CompletedProcess[str]
    strict: HookLayout
    strict_run: subprocess.CompletedProcess[str]


@pytest.fixture(scope="module")
def hook_run(tmp_path_factory: pytest.TempPathFactory) -> HookRuns:
    """One default and one `--strict` no-channel run, shared by the arms that read them."""
    repo = Path(__file__).resolve().parent.parent
    default = _hook_layout(tmp_path_factory.mktemp("cs1101-default"), repo)
    strict = _hook_layout(tmp_path_factory.mktemp("cs1101-strict"), repo)
    return HookRuns(
        default=default,
        default_run=_run_like_the_hook(default),
        strict=strict,
        strict_run=_run_like_the_hook(strict, "--strict"),
    )


def test_the_claim_extractor_sees_one_code_none_and_a_retired_mention() -> None:
    """CONTROL on the PROSE side. The extractor must be able to return red inputs.

    A docstring that states no code must come back empty, so the live arm can
    refuse it rather than pass it; and a history mention written in the other
    shape must not be read as a second, current claim.
    """
    assert _stated_exit_codes("the tool answers that state with exit 3, and") == [3]
    assert _stated_exit_codes("this tool answers that\n  with exit 0") == [0]
    assert _stated_exit_codes("the refusal was right and says why") == []
    assert _stated_exit_codes("the exit 3 it carried before CS-1095") == []
    assert _all_stated_codes("still exits 3 there. A quiet one answers that with exit 0.") == [
        3,
        0,
    ]
    assert _all_stated_codes("it RETURNS 0, and exit code 4 under --strict") == [0, 4]
    assert _all_stated_codes("a hook exiting non-zero loses its stdout") == []
    true_strict = "It exits 0. Under `--strict` the no-channel state still exits 3."
    assert _misgraded_codes(true_strict, default=0, strict=3) == []
    assert _misgraded_codes("Under `--strict` it exits 7.", default=0, strict=3) != []
    assert _misgraded_codes("A hook that exits 2 blocks.", default=0, strict=3) != []


def test_the_probe_enters_the_no_channel_path_under_an_isolated_root(
    hook_run: HookRuns,
) -> None:
    """CONTROL on the BEHAVIOUR side, and the arm that sees FILE-LOCATION resolution.

    The run must be the no-channel run - it says so, and `--strict` tells it
    apart from a quiet channel. It is nested under an ancestor that holds a
    channel and started from a cwd that holds one, so it only reports no
    channel, and only logs under its own root, while the watcher resolves its
    root from its own file and nothing else - the fact the CS-952 refusal now
    rests on. Red for a root taken from, or walked up from, the file's
    ancestry or the cwd; from `git rev-parse` (top level or common dir) run in
    either; or from `CLAUDE_PROJECT_DIR`.

    DOCUMENTED LIMIT, not a gap left for later repair: a resolution that
    consults none of those four sources - a hardcoded path, a config file, a
    registry key, some other environment variable - is not seen by this arm.
    """
    # Every observation is bound to a scalar BEFORE it is asserted. pytest
    # renders an asserted expression independently of the message, and a
    # CompletedProcess carries the interpreter's absolute path, which is a home
    # directory on this machine.
    layout, result = hook_run.default, hook_run.default_run
    says_unmeasured = "UNMEASURED" in result.stdout
    says_no_channel = "no moon_sync_inbox/ directory" in result.stdout
    names_a_decoy = "cs1101-decoy" in result.stdout
    logged_under_root = (layout.root / "data" / "inbox_watch_invocations.log").is_file()
    wrote_under_cwd = (layout.cwd / "data").exists()
    wrote_under_ancestor = (layout.ancestor / "data").exists()
    assert says_unmeasured, "the run did not report UNMEASURED"
    assert says_no_channel, "the run did not report a missing channel"
    assert not names_a_decoy, "the run listed a channel from its cwd or an ancestor"
    assert logged_under_root, "the invocation log is not under the watcher's own root"
    assert not wrote_under_cwd, "the watcher wrote under its working directory"
    assert not wrote_under_ancestor, "the watcher wrote under an ancestor checkout"
    strict_code = hook_run.strict_run.returncode
    strict_unmeasured = "UNMEASURED" in hook_run.strict_run.stdout
    strict_names_a_decoy = "cs1101-decoy" in hook_run.strict_run.stdout
    assert strict_code != 0, "--strict did not distinguish the no-channel state"
    assert strict_unmeasured, "--strict did not report UNMEASURED"
    assert not strict_names_a_decoy, "--strict listed a channel from its cwd or an ancestor"


@pytest.mark.parametrize("relpath", LIVE_CLAIM_FILES)
def test_each_live_docstring_states_the_exit_code_the_hook_actually_gets(
    relpath: str,
    hook_run: HookRuns,
    repo_root: Path,
) -> None:
    """THE LOAD-BEARING CS-1101 ARM. Every code the docstring states is the real one.

    The prose side reads only the docstring; the behaviour side only runs the
    watcher. EXACTLY ONE anchored claim is required, so a docstring that drops
    the number is red rather than vacuously green; and EVERY exit code the
    docstring states in any shape is graded per `GRADING_RULE` against a
    MEASURED return, so a contradicting sentence beside a correct decoy is red
    and a true sentence about `--strict` is not.
    """
    docstring = _module_docstring(repo_root / relpath)
    anchored = len(_stated_exit_codes(docstring))
    default = hook_run.default_run.returncode
    strict = hook_run.strict_run.returncode
    misgraded = _misgraded_codes(docstring, default=default, strict=strict)
    assert anchored == 1, f"{relpath} states {anchored} anchored exit codes, not 1"
    disagreement = f"{relpath}: misgraded={misgraded}. Rule: {GRADING_RULE}"
    assert misgraded == [], disagreement


def test_each_archive_copy_of_the_premise_carries_its_supersession_note(
    repo_root: Path,
) -> None:
    """The archive keeps its dated copies, and each one says it was superseded.

    Presence only, per paragraph. At least one copy must be found, so an
    extractor that stopped matching reads red instead of passing on nothing.
    """
    text = (repo_root / ARCHIVE_FILE).read_text(encoding="utf-8")
    copies = [para for para in text.split("\n\n") if _stated_exit_codes(para)]
    unannotated = sum(1 for para in copies if SUPERSESSION_MARKER not in para)
    assert copies, f"no copy of the premise found in {ARCHIVE_FILE}"
    assert unannotated == 0, f"{unannotated} of {len(copies)} archive copies lack the note"


# ---------------------------------------------------------------------------
# CS-1107 - the hook-stdout claim is stated as UNGRADED, and a hung git is red.
# ---------------------------------------------------------------------------
#
# WHY THE STDOUT CLAIM IS REWORDED RATHER THAN GRADED, decided by measurement.
# The claim is about what the CONSUMER of a `SessionStart` hook does with the
# stdout of a hook that exits non-zero. The only process boundary this
# repository owns is the watcher's own exit, which the CS-1101 arm already
# grades. The consumer is the Claude client: no module in this tree consumes a
# hook's stdout (every `SessionStart` mention under `tools/` and `tests/` is a
# hook or a test of one), the client is not part of this repository, and the
# tier-2 CI workflow installs no client at all - and driving one would put a
# model session in a test. So the claim is carried as the CS-1095 contract's
# premise and marked UNGRADED at every site, and the arm below holds that.

#: A sentence of watcher prose is a HOOK-STDOUT CLAIM SITE when it names a hook
#: and matches this. It LOCATES only; nothing is graded by the words it matches.
HOOK_OUTPUT_LOCATOR: Final = re.compile(r"\b(?:stdout|non-zero|output)\b", re.IGNORECASE)

#: THE ALLOWLIST. Every claim site in the watcher's prose - docstrings, string
#: literals and comments - must be EXACTLY one of these sentences, and each one
#: must be present exactly once. A site reworded to assert the claim as measured
#: is not on the list and is red; a site reworded out of the locator's reach
#: leaves an entry unmatched and is red too, which is the anti-narrowing count.
APPROVED_HOOK_STDOUT_SENTENCES: Final = (
    # Module docstring, the CS-952 paragraph.
    "Tracking the wiring was proposed, granted as a frozen-file edit and then"
    " refused on a premise CS-1095 has since retired: the no-channel code was"
    " non-zero then, which the refusal argued would cost the hook its stdout -"
    " UNGRADED, a client property no test here grades.",
    # Module docstring, the CS-1095 contract clause.
    "A `SessionStart` hook that exits non-zero has its stdout dropped, says the"
    " CS-1095 contract - UNGRADED, a client property no test here grades, carried"
    " as that contract's premise and never as a measurement of this tree.",
    # `main()` docstring, Returns.
    "A `SessionStart` hook that exits non-zero has its stdout dropped, says the"
    " CS-1095 contract - UNGRADED, a client property no test here grades - and on"
    " that premise a non-zero code would silence the missing-channel banner, the"
    " loudest thing this tool has to say, in exactly the tree that needed it.",
    # `--strict` help text.
    "For a gate or a script; a SessionStart hook must NOT use it, because the"
    " CS-1095 contract says a non-zero exit costs a hook its stdout - UNGRADED, a"
    " client property no test here grades.",
)


def _prose_chunks(source: str) -> list[str]:
    """Every string literal and every run of adjacent comment lines in `source`.

    Read from the syntax tree and the token stream, never by importing, so an
    implicitly concatenated help string arrives as the one string argparse sees.
    """
    chunks = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    block: list[str] = []
    layout = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            block.append(token.string.lstrip("#"))
        elif token.type not in layout and block:
            chunks.append(" ".join(block))
            block = []
    if block:
        chunks.append(" ".join(block))
    return chunks


def _hook_stdout_sentences(source: str) -> list[str]:
    """Every whitespace-normalised prose sentence of `source` that is a claim site."""
    sentences = [
        sentence
        for chunk in _prose_chunks(source)
        for sentence in re.split(r"(?<=[.!?])\s+", " ".join(chunk.split()))
    ]
    return [s for s in sentences if "hook" in s.lower() and HOOK_OUTPUT_LOCATOR.search(s)]


def test_the_claim_site_locator_sees_a_docstring_a_help_string_and_a_comment() -> None:
    """CONTROL. The locator must find a measured wording in all three prose forms.

    The pre-CS-1107 wording is planted once as a docstring, once split across an
    implicitly concatenated help string and once as a comment block, and each
    copy must be located and must be off the allowlist - otherwise the live arm
    could pass by seeing nothing.
    """
    measured = "A `SessionStart` hook that exits non-zero has its stdout DROPPED, so it is lost."
    source = (
        f'"""{measured}"""\n'
        'HELP = ("A hook must not use it, because a"\n'
        '    " non-zero exit costs the hook its stdout.")\n'
        "# A hook that exits non-zero\n# has its stdout DROPPED.\nX = 1\n"
    )
    planted_sites = 3
    found = _hook_stdout_sentences(source)
    approved = [sentence for sentence in found if sentence in APPROVED_HOOK_STDOUT_SENTENCES]
    assert len(found) == planted_sites, f"located {len(found)} planted claim sites, not 3"
    assert approved == [], "a planted measured wording read as approved"
    control = f'"""{APPROVED_HOOK_STDOUT_SENTENCES[0]} The rest."""\n'
    assert _hook_stdout_sentences(control) == [APPROVED_HOOK_STDOUT_SENTENCES[0]]


def test_every_hook_stdout_claim_in_the_watcher_is_an_approved_ungraded_sentence(
    repo_root: Path,
) -> None:
    """THE LOAD-BEARING CS-1107 PROSE ARM. The claim is UNGRADED at every site.

    Allowlist, not denylist: every located site must be an approved sentence,
    and every approved sentence must be located exactly once.

    DOCUMENTED LIMIT: a NEW sentence restating the claim without naming a hook,
    or without any word the locator matches, is not located. An EXISTING site
    rewritten that way is red, because its approved entry then goes unmatched.
    """
    source = (repo_root / WATCHED_TOOL).read_text(encoding="utf-8")
    found = sorted(_hook_stdout_sentences(source))
    unapproved = [sentence for sentence in found if sentence not in APPROVED_HOOK_STDOUT_SENTENCES]
    unmatched = sorted(set(APPROVED_HOOK_STDOUT_SENTENCES) - set(found))
    assert unapproved == [], f"{WATCHED_TOOL}: claim sites not on the allowlist: {unapproved}"
    assert unmatched == [], f"{WATCHED_TOOL}: approved sentences not found: {unmatched}"
    assert found == sorted(APPROVED_HOOK_STDOUT_SENTENCES), "a claim site is duplicated"


def _git_outcome(tree: Path, env: dict[str, str], *args: str) -> tuple[str, str]:
    """Run `_git` and report how it ended - passed, failed or skipped - with the message."""
    try:
        _git(tree, env, *args)
    except (AssertionError, pytest.fail.Exception) as failure:
        return "failed", str(failure)
    except pytest.skip.Exception as skipped:
        return "skipped", str(skipped)
    return "passed", ""


def test_a_git_timeout_in_a_decoy_tree_fails_rather_than_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-1107 PLANT. A hung git is RED, never read as git not being installed.

    The plant swaps `_git`'s program for an interpreter that sleeps far past a
    shrunken timeout. It runs in a temporary directory under the scrubbed
    environment, so no real repository is reachable. The outcome is caught
    explicitly: a skip escaping into pytest would turn this arm SKIPPED, not red.
    """
    env = _isolated_git_env(tmp_path)
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "GIT_TIMEOUT_SECONDS", 2.0)
    monkeypatch.setattr(
        module, "GIT_PROGRAM", (sys.executable, "-c", "import time; time.sleep(30)")
    )
    outcome, message = _git_outcome(tmp_path, env, "init")
    assert outcome == "failed", f"a planted git timeout ended {outcome}, not failed"
    assert "TIMED OUT" in message, "the failure does not say the git command timed out"


def test_the_git_plant_is_what_runs_and_a_missing_git_still_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CONTROLS for the plant. The swapped program is really run, and absence still skips.

    A child exiting 3 must fail with that code, which real `git init` in an
    empty directory would not - so the plant cannot pass by being ignored. A
    program that does not exist must SKIP, because git not being installed is
    still a skip; only a hang moved to red.
    """
    env = _isolated_git_env(tmp_path)
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "GIT_PROGRAM", (sys.executable, "-c", "raise SystemExit(3)"))
    exit_outcome, exit_message = _git_outcome(tmp_path, env, "init")
    monkeypatch.setattr(module, "GIT_PROGRAM", ("cs1107-no-such-git-program",))
    missing_outcome, _ = _git_outcome(tmp_path, env, "init")
    assert exit_outcome == "failed", f"a planted exit 3 ended {exit_outcome}"
    assert "exit 3" in exit_message, "the planted program was not the one that ran"
    assert missing_outcome == "skipped", f"a missing git ended {missing_outcome}, not skipped"


def _wiring_document() -> dict[str, object]:
    """The settings shape that declares the watcher's SessionStart hook."""
    return {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": HOOK_COMMAND}]}]}}


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
