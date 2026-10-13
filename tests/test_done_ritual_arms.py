"""CS-1323 - four arms of the /done ritual, held as tests.

``.claude/commands/done.md`` is prose an agent executes. Where a rule is a
procedure these arms RUN it; where it is prose they read key phrases inside a
labelled block, so the voice may be tightened freely but the rule may not go
missing.

1. THE CS-700 WINDOW. From the flip block's step b until S12a no commit of any
   kind lands on the main tree's main, so a /done inside the window - or one
   that cannot read it - commits nothing, runs no suite and pushes nothing. The
   signal commands are EXTRACTED from done.md and run against throwaway
   repositories: the regeneration commit reads OPEN, the commit after it reads
   CLOSED, and a merge HEAD and a repository with no HEAD read UNKNOWN.
2. S12a KEEPS THE WINDOW'S RECORDS. The uncommitted records survive the S12a
   reset as a copy under the gitignored data directory, which a hard reset is
   shown here to leave alone.
3. THE GATE-REFUSAL PATH. A refused push ran no suite. The hook reports a suite
   gate refusal as its own exit 1, so the refusal is read from the gate's line:
   a slot timeout or a git-lock refusal is retried once, and another live
   agent's uncommitted edits stop the ritual at once. A red suite never retries
   the push.
4. NO BARE IGNORED PATH. A gitignored path spelled in backticks in a tracked
   record is a site the bare-path ladder answers on its R2 rung, and an
   undisclosed one turns the push suite red - CS-1321's first push. No template
   in done.md spells one.

Each arm also checks the facts its rule rests on against the code that owns
them, through ``ast`` where the owner is Python. This module spells no
gitignored path itself: it builds the ones it needs from components, because a
backticked spelling here would be an R2 site in a tracked file.
"""

from __future__ import annotations

import ast
import os
import re
import shlex
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Final

import pytest

from tests.bare_path_guard import BARE_PATH_RE, DECLARED_UNTRACKED, declares_untracked
from tests.git_env import scrubbed_env

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

DONE_MD: Final = ".claude/commands/done.md"
SUITE_GATE: Final = "ops/fleet_kit/fleet_suite_gate.py"
GIT_LOCK: Final = "ops/fleet_kit/fleet_gitlock.py"
DONE_MARKER: Final = "ops/fleet_kit/fleet_done.py"
PRE_PUSH: Final = ".githooks/pre-push"
SHA_GATE: Final = "tools/sha_citation_gate.py"
HISTORICAL_FILE: Final = "tools/sha_citation_historical.json"

#: The gitignored directory the S12a rule names in words.
DATA_DIR: Final = "data"

#: Where each labelled block OPENS - a bold paragraph or a checklist bullet - so
#: a passing mention of the label elsewhere is never read as the rule itself.
WINDOW_OPENER: Final = "**THE CS-700 WINDOW"
SIGNAL_OPENER: Final = "- [ ] READ THE CS-700 WINDOW SIGNAL"
KEEP_OPENER: Final = "**S12a KEEPS THE WINDOW'S RECORDS"
KEEP_RULE_LABEL: Final = "KEEP RULE"
REFUSAL_OPENER: Final = "- [ ] GATE-REFUSAL PATH"
MEASURE_OPENER: Final = "- [ ] MEASURE"
IGNORED_LABEL: Final = "NO BARE IGNORED PATH"
IGNORED_OPENER: Final = f"- [ ] {IGNORED_LABEL}"

#: The steps whose text is written INTO tracked records - the ledger, the
#: roadmap, the wakeup notes, the hand-off and its report.
TEMPLATE_STEPS: Final = ("2", "3", "4", "6", "9")

#: Seconds one git call in a throwaway repository may take.
GIT_TIMEOUT: Final = 120

#: What ``git rev-list --parents -n 1`` prints for a commit with one parent:
#: the commit and that parent. A merge prints more.
PARENT_LINE_TOKENS: Final = 2


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


def _items(block: str) -> list[str]:
    """The indented sub-bullets of a checklist bullet, each flattened to one line."""
    return [" ".join(item.split()) for item in re.split(r"\n[ \t]+- ", block)[1:]]


# --- the window signal, extracted from done.md and run -----------------------


def _condition(clause: str) -> str | None:
    """Which observation a signal clause keys on, or None for prose."""
    if "non-zero exit" in clause:
        return "failed"
    if "more than two SHAs" in clause:
        return "merge"
    if "does not list" in clause:
        return "absent"
    if re.search(r"\blists\b", clause):
        return "present"
    return None


def _signal_rules(text: str) -> list[tuple[list[str], list[tuple[str, str]]]]:
    """Each signal command done.md names, in order, with its (condition, state) clauses."""
    rules: list[tuple[list[str], list[tuple[str, str]]]] = []
    for item in _items(_block(text, SIGNAL_OPENER)):
        command = re.match(r"`(git [^`]+)`:(.*)", item)
        if command is None:
            continue
        clauses = []
        for clause in command.group(2).split(";"):
            state = re.search(r"\breads (OPEN|CLOSED|UNKNOWN)\b", clause)
            condition = _condition(clause)
            if state is not None and condition is not None:
                clauses.append((condition, state.group(1)))
        rules.append((shlex.split(command.group(1)), clauses))
    return rules


def _git_env() -> dict[str, str]:
    """No inherited repository pointer, no system or global configuration."""
    env = scrubbed_env()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not on PATH; the throwaway repositories cannot be built")
    return subprocess.run(
        [
            git,
            "-C",
            str(repo),
            "-c",
            "user.name=cs1323-test",
            "-c",
            "user.email=cs1323-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
        env=_git_env(),
    )


def _must(repo: Path, *args: str) -> None:
    """Run a building step; a failure names the subcommand and never a path."""
    if _git(repo, *args).returncode != 0:
        raise RuntimeError(f"git {args[0]} failed while building a throwaway repository")


def _new_repo(root: Path, name: str) -> Path:
    repo = root / name
    repo.mkdir()
    _must(repo, "init", "-q", "-b", "main")
    return repo


def _commit(repo: Path, name: str, body: str, message: str) -> None:
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body.encode("ascii"))
    _must(repo, "add", "--", name)
    _must(repo, "commit", "-q", "-m", message)


def _build_window_repos(root: Path) -> dict[str, Path]:
    """One throwaway repository per window state, HEAD where that state lives."""
    empty = _new_repo(root, "empty")
    regeneration = _new_repo(root, "regeneration")
    _commit(regeneration, "README.md", "base\n", "base")
    _commit(regeneration, HISTORICAL_FILE, "{}\n", "regenerate the set")
    after = _new_repo(root, "after")
    _commit(after, "README.md", "base\n", "base")
    _commit(after, HISTORICAL_FILE, "{}\n", "regenerate the set")
    _commit(after, "docs/LEDGER.md", "record\n", "a commit after the regeneration")
    merge = _new_repo(root, "merge")
    _commit(merge, "README.md", "base\n", "base")
    _must(merge, "checkout", "-q", "-b", "side")
    _commit(merge, HISTORICAL_FILE, "{}\n", "regenerate on a side branch")
    _must(merge, "checkout", "-q", "main")
    _commit(merge, "docs/LEDGER.md", "record\n", "main moves on")
    _must(merge, "merge", "-q", "--no-ff", "-m", "merge the side branch", "side")
    return {
        "empty": empty,
        "regeneration": regeneration,
        "after": after,
        "merge": merge,
        "unreadable": _unreadable_repo(root),
    }


def _unreadable_repo(root: Path) -> Path:
    """HEAD's commit object reads, so the parent check passes, but its tree is gone.

    The diff of HEAD against its parent then exits non-zero: the read failure
    the signal's second command has to turn into UNKNOWN rather than CLOSED.
    """
    repo = _new_repo(root, "unreadable")
    _commit(repo, "README.md", "base\n", "base")
    _commit(repo, "docs/LEDGER.md", "record\n", "a commit whose tree goes missing")
    tree = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    loose = repo / ".git" / "objects" / tree[:2] / tree[2:]
    loose.chmod(stat.S_IWRITE | stat.S_IREAD)
    loose.unlink()
    return repo


def _decides(condition: str, done: subprocess.CompletedProcess[str]) -> bool:
    """Whether one clause's observation holds for one command's result."""
    if done.returncode != 0:
        return condition == "failed"
    tokens = done.stdout.split()
    return {
        "merge": len(tokens) > PARENT_LINE_TOKENS,
        "present": HISTORICAL_FILE in tokens,
        "absent": HISTORICAL_FILE not in tokens,
    }.get(condition, False)


def _read_window(repo: Path, rules: list[tuple[list[str], list[tuple[str, str]]]]) -> str | None:
    """Apply done.md's signal to ``repo``, first deciding clause wins; None when none does."""
    for words, clauses in rules:
        if words[:1] != ["git"]:
            return None
        done = _git(repo, *words[1:])
        decided = [state for condition, state in clauses if _decides(condition, done)]
        if decided:
            return decided[0]
        if done.returncode != 0:
            return None
    return None


def _window_states(root: Path) -> dict[str, str | None]:
    rules = _signal_rules(_text(DONE_MD))
    return {name: _read_window(repo, rules) for name, repo in _build_window_repos(root).items()}


@pytest.fixture(scope="module")
def window_states(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str | None]:
    return _window_states(tmp_path_factory.mktemp("cs1323-window"))


# --- the kit facts, read through ast ------------------------------------------


def _module_constant(tree: ast.Module, name: str) -> object:
    """The literal value of a module-level ``name = ...`` or ``name: T = ...``."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return ast.literal_eval(value)
    return None


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _handler_returns(tree: ast.Module, function: str, exception: str) -> set[object]:
    """The constants returned by ``function``'s ``except exception`` handlers."""
    found: set[object] = set()
    body = _function(tree, function)
    for node in ast.walk(body) if body is not None else []:
        if (
            isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id == exception
        ):
            found |= {
                ret.value.value
                for ret in ast.walk(node)
                if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Constant)
            }
    return found


def _leading_text(node: ast.expr) -> str:
    """The literal text a message expression starts with."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        return _leading_text(node.values[0])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return _leading_text(node.func.value)
    return ""


def _raised_messages(tree: ast.Module, exception: str) -> list[str]:
    return [
        _leading_text(node.exc.args[0])
        for node in ast.walk(tree)
        if isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id == exception
        and node.exc.args
    ]


def _in_slot_refusal_records_a_null_exit(tree: ast.Module) -> bool:
    """``run`` starts ``rc`` at None, re-checks inside a try, and records ``rc`` in finally."""
    run = _function(tree, "run")
    if run is None:
        return False
    starts_none = any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "rc" for t in node.targets)
        and isinstance(node.value, ast.Constant)
        and node.value.value is None
        for node in run.body
    )
    tries = [node for node in ast.walk(run) if isinstance(node, ast.Try)]
    rechecks = any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "check_straddle"
        for node in tries
        for stmt in node.body
        for call in ast.walk(stmt)
    )
    records = any(
        isinstance(record, ast.Dict)
        and any(
            isinstance(key, ast.Constant)
            and key.value == "exit"
            and isinstance(value, ast.Name)
            and value.id == "rc"
            for key, value in zip(record.keys, record.values, strict=True)
        )
        for node in tries
        for stmt in node.finalbody
        for record in ast.walk(stmt)
    )
    return starts_none and rechecks and records


# --- arm 1: the CS-700 window -------------------------------------------------


def test_the_signal_reads_open_on_the_regeneration_commit(
    window_states: dict[str, str | None],
) -> None:
    assert window_states["regeneration"] == "OPEN"


def test_the_signal_reads_closed_on_the_commit_after_it(
    window_states: dict[str, str | None],
) -> None:
    assert window_states["after"] == "CLOSED"


def test_the_signal_reads_unknown_on_a_merge_head(window_states: dict[str, str | None]) -> None:
    assert window_states["merge"] == "UNKNOWN"


def test_the_signal_reads_unknown_with_no_head(window_states: dict[str, str | None]) -> None:
    assert window_states["empty"] == "UNKNOWN"


def test_the_signal_reads_unknown_when_the_diff_cannot_be_read(
    window_states: dict[str, str | None],
) -> None:
    assert window_states["unreadable"] == "UNKNOWN"


def test_the_window_bounds_and_its_soundness_are_stated() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert block, "done.md carries no CS-700 WINDOW paragraph"
    assert "step b" in block, "the window's opening bound is not named"
    assert "S12a" in block, "the window's closing bound is not named"
    assert HISTORICAL_FILE in block, "the signal does not name the regenerated set"
    assert "HEAD's own commit" in block, "the signal is not HEAD's own commit"
    assert re.search(r"nothing\s+else\s+commits", block), "the signal's soundness is unstated"
    assert not re.search(r"only\s+commit\s+that\s+writes", block), "a false sole-writer claim"


def test_open_or_unknown_commits_nothing_runs_no_suite_and_pushes_nothing() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert re.search(r"OPEN,?\s+or\s+the\s+signal\s+is\s+UNKNOWN", block), "UNKNOWN is not covered"
    assert re.search(r"commits?\s+nothing", block), "the window does not forbid a commit"
    assert re.search(r"runs\s+no\s+(?:test\s+)?suite", block), "the window runs a suite"
    assert re.search(r"push(?:es)?\s+nothing", block), "the window does not forbid a push"
    assert re.search(r"orders\s+NO\s+push", block), "the hand-off may still order a push"
    assert "UNCOMMITTED" in block, "the hand-off is not said uncommitted"
    assert "first /done that pushes" in block, "the DONE-SLOW measurement is not deferred"


def test_unknown_marks_failed_and_is_never_carried_forward_as_open() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert re.search(r'--status\s+failed\s+--reason\s+"[^"]*unreadable', block)
    assert re.search(r"never\s+carried\s+forward\s+as\s+OPEN", block), "UNKNOWN could deadlock"
    assert "adjudicator" in block, "nothing resolves an unreadable signal"


def test_the_commit_and_push_steps_defer_to_the_window() -> None:
    steps = _steps()

    for number in ("7", "8"):
        assert "CS-700 window" in steps.get(number, ""), f"step {number} ignores the window"
        assert "UNKNOWN" in steps.get(number, ""), f"step {number} ignores an unreadable signal"


def test_the_hand_off_orders_no_push_inside_the_window() -> None:
    step = _steps().get("6", "")

    assert re.search(r"orders\s+NO\s+push", step), "step 6 still orders a push first"
    assert re.search(r"OPEN\s+or\s+UNKNOWN", step), "the push suspension is not scoped"


def test_the_window_signal_names_the_set_the_regeneration_writes() -> None:
    gate = _text(SHA_GATE)

    assert _module_constant(ast.parse(gate), "HISTORICAL_FILE") == HISTORICAL_FILE
    assert "--emit-historical" in gate


# --- arm 2: S12a keeps the window's records -----------------------------------


def _reset_round_trip(root: Path) -> tuple[bytes, bytes]:
    """Copy an uncommitted record under the ignored data directory, then reset hard."""
    repo = _new_repo(root, "reset")
    _commit(repo, ".gitignore", f"/{DATA_DIR}/\n", "ignore the data directory")
    _commit(repo, "CS-NEXT-SESSION.txt", "committed\n", "a hand-off")
    (repo / "CS-NEXT-SESSION.txt").write_bytes(b"uncommitted\n")
    keep = repo / DATA_DIR / "cs1323-window" / "CS-NEXT-SESSION.txt"
    keep.parent.mkdir(parents=True)
    shutil.copyfile(repo / "CS-NEXT-SESSION.txt", keep)
    _must(repo, "reset", "-q", "--hard", "HEAD")
    return (repo / "CS-NEXT-SESSION.txt").read_bytes(), keep.read_bytes()


def _keep_rule() -> str:
    """The KEEP RULE itself: from its label to the end of the S12a paragraph."""
    block = _block(_text(DONE_MD), KEEP_OPENER)
    start = block.find(KEEP_RULE_LABEL)
    return block[start:] if start >= 0 else ""


def test_s12a_keeps_the_window_records() -> None:
    block = _block(_text(DONE_MD), KEEP_OPENER)
    rule = _keep_rule()

    assert block, "done.md carries no S12a KEEPS THE WINDOW'S RECORDS paragraph"
    assert rule, f"the S12a paragraph carries no {KEEP_RULE_LABEL}"
    assert re.search(r"[Bb]efore\s+any\s+CS-700\s+S12a\s+reset", rule), "no copy before"
    assert re.search(r"gitignored\s+data\s+directory", rule), "the location is not named"
    for record in ("hand-off", "docs/LEDGER.md", "WAKEUP_NOTES.md", "ROADMAP.md"):
        assert record in rule, f"the KEEP RULE omits {record}"


def test_the_keep_copy_goes_to_a_new_empty_folder_named_for_the_session() -> None:
    rule = _keep_rule()

    assert re.search(r"NEW,?\s+EMPTY\s+folder\s+of\s+its\s+own", rule), "a stale folder is reused"
    assert re.search(r"named\s+after\s+the\s+session\s+number", rule), "the folder is unnamed"
    assert re.search(r"fails[^.]*already\s+exists", rule), "an existing folder does not fail"
    assert re.search(r"only\s+from\s+that\s+folder", rule), "the restore source is unbounded"


def test_the_keep_restore_is_immediate_and_the_folder_is_then_removed() -> None:
    rule = _keep_rule()

    assert re.search(r"IMMEDIATELY\s+after\s+the\s+reset", rule), "the restore is not immediate"
    assert re.search(r"before\s+any\s+other\s+S12a\s+act", rule), "an S12a act may come first"
    assert not re.search(r"[Rr]estore[^.]*closing\s+commit", rule), "the restore waits too long"
    assert re.search(r"remove\s+(?:that|the)\s+folder", rule), "the folder is never removed"
    assert "plain delete" in rule, "the removal method is not stated"


def test_the_window_hand_off_carries_the_keep_rule_word_for_word() -> None:
    block = _block(_text(DONE_MD), WINDOW_OPENER)

    assert KEEP_RULE_LABEL in block, "the window hand-off is not told to carry the KEEP RULE"
    assert re.search(r"WORD\s+FOR\s+WORD", block), "the KEEP RULE may be paraphrased"


def test_the_data_directory_is_ignored_in_this_tree() -> None:
    probe = "/".join((DATA_DIR, "cs1323-window", "CS-NEXT-SESSION.txt"))

    assert declares_untracked([probe]) == frozenset({probe})


def test_a_hard_reset_drops_the_record_and_keeps_the_ignored_copy(tmp_path: Path) -> None:
    tracked, kept = _reset_round_trip(tmp_path)

    assert tracked == b"committed\n", "the reset left the uncommitted record in place"
    assert kept == b"uncommitted\n", "the reset touched the ignored copy"


# --- arm 3: the gate-refusal path ---------------------------------------------


def test_a_slot_timeout_or_a_lock_refusal_is_retried_once() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)
    retry = [item for item in _items(block) if "no suite slot free" in item]

    assert len(retry) == 1, "step 8 has no single slot-timeout sub-bullet"
    assert "GITLOCK:" in retry[0], "a git-lock refusal is not retried"
    assert "WAIT_S" in retry[0], "the gate's wait limit is not named at its owner"
    assert "exactly ONCE" in retry[0], "the retry is not bounded to one"
    assert re.search(r"second refusal", retry[0], re.IGNORECASE), "no stop on a second refusal"


def test_foreign_uncommitted_edits_stop_the_ritual_without_a_retry() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)
    stop = [item for item in _items(block) if "uncommitted edits by another live agent" in item]

    assert len(stop) == 1, "step 8 has no single uncommitted-edits sub-bullet"
    assert "NO retry" in stop[0], "the uncommitted-edits refusal is retried"
    assert "exactly ONCE" not in stop[0], "the uncommitted-edits refusal is retried"
    assert re.search(r"[Ss]top at once", stop[0]), "the ritual does not stop at once"


def test_a_refusal_is_read_from_the_output_and_never_from_the_exit_code() -> None:
    step = _steps().get("8", "")
    block = _block(step, REFUSAL_OPENER)

    assert "2>&1" in step, "the push's stderr is not captured"
    assert "exit 1" in block, "the hook's own exit code for a refusal is not stated"
    assert "SUITE-GATE:" in block, "a gate refusal is not read from its line"
    assert "--status failed" in block, "a stop does not mark the ritual failed"
    assert re.search(r"nothing\s+pushed", block), "a stop does not say nothing pushed"
    assert re.search(r"next\s+session\s+pushes\s+first", block), "the next session is not told"


def _line_role(spelled: str) -> str:
    """Which refusal line a spelled pattern is for, read from its literal text."""
    text = spelled.lstrip("^")
    if "no suite slot free" in text:
        return "timeout"
    if "uncommitted edits" in text:
        return "foreign"
    if "wrote no report" in text:
        return "noreport"
    if text.startswith("GITLOCK:"):
        return "lock"
    if text.startswith("clockspeed pre-push:"):
        return "hook"
    return "other"


def _refusal_patterns() -> dict[str, list[re.Pattern[str]]]:
    """The refusal line patterns step 8 spells, compiled per line, keyed by role."""
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)
    roles: dict[str, list[re.Pattern[str]]] = {}
    for spelled in re.findall(r"`(\^?(?:SUITE-GATE|GITLOCK|clockspeed pre-push):[^`]*)`", block):
        roles.setdefault(_line_role(spelled), []).append(re.compile(spelled, re.MULTILINE))
    return roles


def _classify(log: str, roles: dict[str, list[re.Pattern[str]]]) -> str:
    """retry, stop or none for a captured push log, by the rule step 8 states."""

    def seen(role: str) -> bool:
        return any(pattern.search(log) for pattern in roles.get(role, []))

    if seen("noreport") and seen("timeout"):
        return "retry"
    if seen("noreport") and seen("foreign"):
        return "stop"
    if seen("lock") and not seen("hook"):
        return "retry"
    return "none"


def _real_lines() -> dict[str, str]:
    """One line per role exactly as the kit and the hook print it."""
    gate = _raised_messages(ast.parse(_text(SUITE_GATE)), "GateRefused")
    lock = _raised_messages(ast.parse(_text(GIT_LOCK)), "LockRefused")
    no_report = re.search(r'die "(pytest wrote no report[^"]*)"', _text(PRE_PUSH))
    return {
        "timeout": next((m for m in gate if "no suite slot free" in m), "") + "3600s",
        "foreign": next((m for m in gate if "uncommitted edits" in m), "").format("tests"),
        "noreport": "clockspeed pre-push: " + (no_report.group(1) if no_report else ""),
        "lock": next((m for m in lock if "lock still held" in m), "") + "600s",
        "hook": "clockspeed pre-push: BLOCKED (pytest exit 1). Nothing was pushed.",
    }


def test_the_real_refusal_lines_are_printed_unprefixed_at_column_0() -> None:
    hook = _text(PRE_PUSH)
    real = _real_lines()

    assert "printf 'clockspeed pre-push: %s\\n' \"$1\"" in hook, "die prints another prefix"
    assert "'clockspeed pre-push: BLOCKED (pytest exit %s). Nothing was pushed.\\n'" in hook
    assert real["timeout"].startswith("SUITE-GATE: no suite slot free")
    assert "has uncommitted edits by another live agent" in real["foreign"]
    assert real["noreport"].startswith("clockspeed pre-push: pytest wrote no report")
    assert real["lock"].startswith("GITLOCK: lock still held")
    for owner in (SUITE_GATE, GIT_LOCK):
        assert 'sys.stderr.write(msg + "\\n")' in _text(owner), f"{owner} prefixes its lines"


def test_each_refusal_pattern_matches_its_real_line_only_at_column_0() -> None:
    roles = _refusal_patterns()
    real = _real_lines()

    for role in ("timeout", "foreign", "noreport", "lock", "hook"):
        patterns = roles.get(role, [])
        assert patterns, f"step 8 spells no {role} line pattern"
        assert all(p.search(real[role]) for p in patterns), f"a {role} pattern misses its line"
        assert not any(p.search("    " + real[role]) for p in patterns), f"indented {role} counts"
        assert not any(p.search("E   x: " + real[role]) for p in patterns), f"mid-line {role}"


def test_a_gate_refusal_needs_its_line_and_the_hook_no_report_line() -> None:
    roles = _refusal_patterns()
    real = _real_lines()

    assert _classify(f"{real['timeout']}\n{real['noreport']}\n", roles) == "retry"
    assert _classify(f"{real['foreign']}\n{real['noreport']}\n", roles) == "stop"
    assert _classify(f"{real['timeout']}\n", roles) == "none", "one line alone retried"
    assert _classify(f"{real['foreign']}\n", roles) == "none", "one line alone stopped"
    assert _classify(f"    {real['timeout']}\n{real['noreport']}\n", roles) == "none"
    assert _classify(f"E   x: {real['timeout']}\n{real['noreport']}\n", roles) == "none"


def test_a_lock_refusal_counts_only_when_the_hook_never_ran() -> None:
    roles = _refusal_patterns()
    real = _real_lines()

    assert _classify(f"{real['lock']}\n", roles) == "retry"
    assert _classify(f"{real['hook']}\n{real['lock']}\n", roles) == "none", "a red suite retried"
    assert _classify(f"    {real['lock']}\n", roles) == "none", "an indented lock line counts"


def test_step_8_states_the_rule_the_classifier_applies() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)
    retry = [item for item in _items(block) if "no suite slot free" in item]
    stop = [item for item in _items(block) if "uncommitted edits by another live agent" in item]

    assert len(retry) == 1, "step 8 has no single slot-timeout sub-bullet"
    assert len(stop) == 1, "step 8 has no single uncommitted-edits sub-bullet"
    assert "wrote no report" in retry[0], "a timeout line alone would be retried"
    assert "wrote no report" in stop[0], "an uncommitted-edits line alone would stop"
    assert re.search(r"`\^GITLOCK:`[^`]*with\s+no\s+`\^clockspeed pre-push:`", retry[0])
    assert re.search(r"STARTS\s+with", block), "the anchoring is not stated in words"


def test_the_push_runs_in_git_bash_with_its_log_outside_the_tree() -> None:
    step = _steps().get("8", "")

    assert "Git Bash" in step, "the push shell is not named"
    assert "UTF-16" in step, "the PowerShell 5.1 hazard is not stated"
    assert re.search(r"outside\s+the\s+tree", step), "the push log may sit inside the tree"
    assert re.search(r"never\s+a\s+tracked\s+or\s+claimable\s+path", step)


def test_a_red_suite_never_retries_the_push() -> None:
    block = _block(_steps().get("8", ""), REFUSAL_OPENER)

    assert re.search(r"red\s+suite[^.]*never\s+retr", block, re.IGNORECASE)
    assert re.search(r"\bALONE\b", block), "a red suite's tests are not re-run alone"


def test_measure_skips_a_refusal_line() -> None:
    step = _steps().get("8", "")
    measure = _block(step, MEASURE_OPENER)

    assert measure, "step 8 carries no MEASURE bullet"
    assert re.search(r"`exit`\s+is\s+not\s+null", measure), "MEASURE reads a refusal's line"
    assert "writes no gate line" not in step, "the false no-line claim is back"


def test_the_suite_gate_facts_hold() -> None:
    tree = ast.parse(_text(SUITE_GATE))
    messages = _raised_messages(tree, "GateRefused")

    assert isinstance(_module_constant(tree, "WAIT_S"), (int, float))
    assert _handler_returns(tree, "main", "GateRefused") == {3}
    assert messages, "the kit raises no GateRefused this arm can read"
    assert all(m.startswith("SUITE-GATE:") for m in messages)
    assert any(m.startswith("SUITE-GATE: no suite slot free") for m in messages)
    assert any("uncommitted edits by another live agent" in m for m in messages)
    assert _in_slot_refusal_records_a_null_exit(tree), "an in-slot refusal writes no null line"


def test_the_git_lock_facts_hold() -> None:
    tree = ast.parse(_text(GIT_LOCK))
    messages = _raised_messages(tree, "LockRefused")

    assert _handler_returns(tree, "main", "LockRefused") == {3}
    assert messages, "the kit raises no LockRefused this arm can read"
    assert all(m.startswith("GITLOCK:") for m in messages)


def test_the_hook_reports_a_gate_refusal_as_its_own_exit_1() -> None:
    hook = _text(PRE_PUSH)

    assert re.search(r"^die\(\) \{\n(?:.*\n)*?    exit 1\n\}", hook, re.MULTILINE)
    assert "pytest wrote no report" in hook


def test_the_marker_takes_the_statuses_done_md_uses() -> None:
    tree = ast.parse(_text(DONE_MARKER))
    flags = [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and call.args
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value in ("--status", "--reason")
    ]
    choices = [kw.value for call in flags for kw in call.keywords if kw.arg == "choices"]
    named = {call.args[0].value for call in flags if isinstance(call.args[0], ast.Constant)}
    statuses = _module_constant(tree, "STATUSES")

    assert isinstance(statuses, tuple), "fleet_done.py has no STATUSES tuple"
    assert set(statuses) == {"done", "failed"}
    assert len(choices) == 1, "--status has no single choices list"
    assert isinstance(choices[0], ast.Name), "--status choices are not the STATUSES constant"
    assert choices[0].id == "STATUSES"
    assert named == {"--status", "--reason"}


# --- arm 4: no bare ignored path ----------------------------------------------


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


def test_no_template_spells_an_ignored_path_in_backticks() -> None:
    text = _text(DONE_MD)
    steps = _steps()
    templates = [steps.get(number, "") for number in TEMPLATE_STEPS]
    templates += [_block(text, WINDOW_OPENER), _block(text, KEEP_OPENER)]
    spelled = sorted({m.group(1) for t in templates for m in BARE_PATH_RE.finditer(t)})
    ignored = sorted(declares_untracked(spelled))

    assert spelled, "the templates spell no path, so this arm measures nothing"
    assert not ignored, "a template spells a gitignored path in backticks"


def test_the_rule_names_the_spelling_the_ladder_reads() -> None:
    record = "/".join(("ops", "loop", "control", "done_timing.json"))

    assert BARE_PATH_RE.search(f"`{record}`"), "a backticked path is no longer a site"
    assert not BARE_PATH_RE.search("this ritual's timing record"), "words became a site"
