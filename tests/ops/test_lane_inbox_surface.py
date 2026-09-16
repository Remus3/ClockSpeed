"""CS-1104 - a lane cycle SURFACES the cross-repo channel and never replies to it.

THE DEFECT. The worker prompt named the channel zero times, and the watcher is
wired only in gitignored local settings, so a worktree - where every lane worker
runs - fired no watcher at all. A long drain could run for hours with unread
review notes sitting in `moon_sync_inbox/` and nothing in the lane saying so.

WHAT IS GRADED HERE, AND WHERE THE PROOF LIVES. The proof is DRIVER-computed:
the `inbox` key in the cycle record the driver appends to its own ledger, and
the one `queue-loop inbox` line the driver prints per cycle. A worker's banner
is prose a model wrote and is pinned only by `tests/test_headless_queue_prompt.py`;
it is never the evidence.

THE FENCE IS SURFACING, NEVER REPLYING, and three arms carry it: nothing in the
surface writes (a runtime write spy, fronted by a control proving the spy sees
the watcher's own writers), nothing in the surface calls outside the watcher's
read API (an AST allowlist, fronted by a planted control), and no lane module
can reach the outbound sender by import, by `_LAZY` row, by path-load string or
by spawn argv (a reach walk, fronted by planted controls for each shape AND a
positive control proving the walk sees the edges it exists to follow).

A COUNT IS AN INTEGER ONLY WHEN A LISTING DEMONSTRABLY HAPPENED AND THE SEEN
STORE WAS READ. Every other state is the string `UNMEASURED` with a reason: an
absent channel (a worktree legitimately has none), an unlistable one, an
unreadable seen store (adjudicated ruling Q3), or a fault. A bare zero in any
of those is the could-not-look-reads-as-clean defect CS-1095 and CS-1103 were
filed for. A measured zero is asserted too, so `UNMEASURED` cannot pass by being
unconditional.

EVERY FIXTURE IS A TMP ROOT. No arm reads the live channel, the live seen store
or the live ledger, and no arm touches `ops/loop/control/` or `ops/loop/reports/`.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.loop import queue_loop  # noqa: E402

TOOLS_DIR: Final = ROOT / "tools"
LOOP_DIR: Final = ROOT / "ops" / "loop"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import inbox_watch  # noqa: E402

UNMEASURED: Final = inbox_watch.UNMEASURED
INBOX: Final = inbox_watch.INBOX_DIRNAME

#: A planted note name in the channel's own naming shape. Not a real sibling
#: code and not a world name.
NOTE: Final = "2026-01-01-0900-from-XX-topic.md"

#: The modules that send. Named, never discovered: a walk that found no sender
#: file would otherwise pass by grading an empty set.
SENDER_STEMS: Final = frozenset({"outbound_send", "outbound_gate"})

#: THE ALLOWLIST, per the four-denylists lesson. A `tools/` module reached from
#: any lane module must be argued into this set, so a FUTURE sender under a name
#: nobody thought to deny is red by default rather than green by omission.
LANE_TOOLS_ALLOWED: Final = frozenset({"toolpath", "inbox_watch"})

#: The watcher's READ API - the only attributes of it the surface may touch.
#: Also an allowlist: `save_seen`, `write_report`, `capped`, `render`, `main`
#: and `append_invocation` all write, and none of them is here.
READ_API: Final = frozenset(
    {
        "INBOX_DIRNAME",
        "SEEN_RELPATH",
        "MAX_LISTED",
        "UNMEASURED",
        "KIND_ORDER",
        "InboxUnreadableError",
        "Deliverable",
        "deliverables",
        "unread_items",
        "seen_blind_reason",
        "safe_display",
    }
)

#: The modules the surface may import. An ALLOWLIST: `subprocess`, `importlib`,
#: `os` and `shutil` are absent, so a spawn of the watcher's acknowledging entry
#: point or a dynamic bind of its writers cannot enter without being argued in.
SURFACE_IMPORTS: Final = frozenset(
    {"__future__", "argparse", "json", "sys", "collections.abc", "pathlib", "typing"}
    | {"inbox_watch", "ops.loop"}
)

#: Spellings that reach a callable by a name the AST cannot read. Any of them in
#: the surface makes the read-API allowlist above unenforceable, so each is a
#: finding on sight.
DYNAMIC_REACH: Final = frozenset(
    {"getattr", "setattr", "delattr", "__import__", "exec", "eval", "compile"}
    | {"globals", "vars", "__dict__", "import_module", "modules", "system", "popen"}
)

#: Method and function names that write, move or delete. Checked on every call
#: in the surface module, whatever object it is called on.
WRITE_CALLS: Final = frozenset(
    {
        "write",
        "write_text",
        "write_bytes",
        "writelines",
        "mkdir",
        "makedirs",
        "touch",
        "unlink",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "rmtree",
        "truncate",
        "chmod",
        "symlink_to",
        "hardlink_to",
        "copy",
        "copy2",
        "copyfile",
        "copytree",
        "move",
        "dump",
        "save_seen",
        "write_report",
        "append_invocation",
    }
)


# ---------------------------------------------------------------------------
# Fixtures - trees, seams and a surface module handle.
# ---------------------------------------------------------------------------


def _main_tree(root: Path) -> Path:
    """A fixture MAIN tree: a real `.git` directory, so it resolves to itself."""
    (root / ".git").mkdir(parents=True)
    return root


def _plant_note(tree: Path, name: str = NOTE, body: bytes = b"a review note\n") -> Path:
    """One note in the tree's channel directory, created on demand."""
    inbox = tree / INBOX
    inbox.mkdir(parents=True, exist_ok=True)
    note = inbox / name
    note.write_bytes(body)
    return note


def _linked_worktree(main: Path, wt: Path) -> Path:
    """A fixture WORKTREE whose `.git` FILE points at `main`, as git writes it."""
    admin = main / ".git" / "worktrees" / "lane"
    admin.mkdir(parents=True)
    wt.mkdir(parents=True)
    (wt / ".git").write_bytes(f"gitdir: {admin}\n".encode("ascii"))
    return wt


class _Clock:
    """Wall and monotonic time that move only when slept."""

    def __init__(self) -> None:
        self.wall = 1_000_000.0
        self.mono = 0.0

    def time(self) -> float:
        return self.wall

    def monotonic(self) -> float:
        return self.mono

    def sleep(self, seconds: float) -> None:
        self.wall += float(seconds)
        self.mono += float(seconds)


class _NullHold:
    """A ledger mutex stand-in that takes no OS handle."""

    def __call__(self) -> _NullHold:
        return self

    def __enter__(self) -> _NullHold:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


def _cycle_seams(clock: _Clock, worktree: Path, **over: Any) -> dict[str, Any]:
    """Every run_cycle seam faked EXCEPT the inbox surface, which is the subject."""
    seams: dict[str, Any] = {
        "acquire": lambda lane, **_kw: {"ok": True, "token": "T", "lane": lane},
        "release": lambda _token, **_kw: True,
        "launch": lambda _lane, **_kw: {"pid": 4242, "log": "lane.log"},
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _started: False,
        "kill": lambda _pid: None,
        "sleep": clock.sleep,
        "clock": clock.time,
        "monotonic": clock.monotonic,
        "worktree": str(worktree),
    }
    seams.update(over)
    return seams


def _loop_seams(clock: _Clock, tmp: Path, worktree: Path, **over: Any) -> dict[str, Any]:
    """Every run_loop seam faked except the surface, with a TMP ledger and control dir."""
    ticks = {"n": 0}

    def tree_sha(_cwd: object) -> str:
        ticks["n"] += 1
        return f"sha-{ticks['n']}"

    seams: dict[str, Any] = {
        "max_cycles": 1,
        "settle_s": 0,
        "poll_s": 1,
        "ci_gate": False,
        "cycle_log": tmp / "ledger" / "queue_loop.jsonl",
        "control_dir": tmp / "control",
        "hold": _NullHold(),
        "acquire": lambda _lane, **_kw: {"ok": True, "token": "T"},
        "release": lambda _token, **_kw: True,
        "launch": lambda _lane, **_kw: {"pid": 1, "log": "l"},
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _s: False,
        "kill": lambda _pid: None,
        "head_sha": lambda: "sha-unchanged",
        "tree_sha": tree_sha,
        "permit": lambda _lane, *_a, **_kw: {
            "ok": True,
            "lane_scope": "fixture",
            "allowed": ("CS-FIXTURE",),
            "detail": "",
        },
        "claim_states": lambda _root=None, _now=None: {},
        "sleep": clock.sleep,
        "clock": clock.time,
        "monotonic": clock.monotonic,
        "worktree": str(worktree),
    }
    seams.update(over)
    return seams


def _surface_module() -> Any:
    """The surface module, or an ASSERTION failure naming what is missing.

    Not a collection-time import, so a tree without the module reddens on a
    sentence ("nothing surfaces") rather than on exit 2, which is not
    self-evidencing.
    """
    try:
        return importlib.import_module("ops.loop.inbox_surface")
    except ModuleNotFoundError as missing:
        # The named FIELD, never the exception object - an echo path (CLAUDE.md 12).
        pytest.fail(f"ops/loop/inbox_surface.py does not exist - nothing surfaces ({missing.name})")


def _inbox_lines(text: str) -> list[str]:
    """The driver's per-cycle inbox lines out of captured stdout or an emit list."""
    return [line for line in text.splitlines() if line.startswith("queue-loop inbox")]


# ---------------------------------------------------------------------------
# A1 - A4: the driver's cycle record and printed line.
# ---------------------------------------------------------------------------


def test_a1_an_unread_note_is_named_in_the_cycle_record_and_the_driver_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """THE ACCEPTANCE ARM: plant one unread note, run one cycle, the record names it."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == 1, inbox
    assert inbox["names"] == [NOTE], inbox
    assert inbox["more"] == 0, inbox
    lines = _inbox_lines(capsys.readouterr().out)
    assert len(lines) == 1, f"expected ONE driver inbox line for the cycle, got {lines}"
    assert NOTE in lines[0], lines
    assert not (tree / "data").exists(), "a cycle on a no-store tree created a seen store"


def test_a1b_a_sender_controlled_name_is_escaped_never_rendered_raw(tmp_path: Path) -> None:
    """M8: the record carries the watcher's escaped `display`, never the raw filename.

    THE CONTROL IS IN THE FIXTURE: the raw name really carries a byte above
    7-bit ASCII, asserted before the cycle runs, so an escaping that did nothing
    could not pass by being handed a name with nothing to escape.
    """
    raw = "2026-01-01-0901-from-XX-caf" + chr(233) + ".md"
    assert not raw.isascii(), "control: the planted name has nothing to escape"
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree, raw)

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["names"] == [inbox_watch.safe_display(raw)], inbox
    serialised = json.dumps(record, ensure_ascii=False)
    assert raw not in serialised, "the raw sender-controlled name reached the record"


def test_a2_no_channel_directory_is_unmeasured_never_zero(tmp_path: Path) -> None:
    """A worktree legitimately has no channel; a bare zero there reads as clean."""
    tree = _main_tree(tmp_path / "wt")

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == UNMEASURED, inbox
    assert inbox["unread"] != 0
    assert inbox["reason"], "UNMEASURED without a reason tells a reader nothing"
    assert inbox["names"] == [], inbox
    assert str(tmp_path) not in json.dumps(inbox), "a reason carried an absolute path"


def test_a2b_a_listed_empty_channel_is_a_measured_zero(tmp_path: Path) -> None:
    """THE OTHER DIRECTION: UNMEASURED is not unconditional. Looked, found nothing -> 0."""
    tree = _main_tree(tmp_path / "wt")
    (tree / INBOX).mkdir()

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == 0, inbox
    assert type(inbox["unread"]) is int
    assert inbox["reason"] == "", inbox


def test_a2c_an_acknowledged_note_is_not_unread(tmp_path: Path) -> None:
    """The seen store is READ: a key already in it is not counted and not named."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    (key,) = [d.key for d in inbox_watch.deliverables(tree / INBOX)]
    store = tree / inbox_watch.SEEN_RELPATH
    store.parent.mkdir(parents=True)
    store.write_bytes(json.dumps({"seen": [key]}).encode("ascii"))

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == 0, inbox
    assert inbox["names"] == [], inbox


def test_a3_a_worktree_surfaces_its_main_trees_channel(tmp_path: Path) -> None:
    """The channel lives in the MAIN checkout; a lane runs in a worktree of it.

    THE CONTROL: the worktree itself has no channel directory, asserted, so a
    surface that resolved from the worktree would answer UNMEASURED here (M4).
    """
    main = _main_tree(tmp_path / "main")
    _plant_note(main)
    wt = _linked_worktree(main, tmp_path / "wt")
    assert not (wt / INBOX).exists()

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), wt))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == 1, inbox
    assert inbox["names"] == [NOTE], inbox


def test_a4_an_unlistable_channel_is_unmeasured_not_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Present but unlistable is not "nothing unread" (CS-1103)."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)

    def blind(_inbox: Path) -> list[Any]:
        raise inbox_watch.InboxUnreadableError("it could not be listed")

    monkeypatch.setattr(inbox_watch, "deliverables", blind)

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == UNMEASURED, inbox
    assert inbox["unread"] not in (0, [])
    assert "could not be listed" in inbox["reason"], inbox


def test_q3_an_unreadable_seen_store_is_unmeasured_and_still_names(tmp_path: Path) -> None:
    """RULING Q3: unread is defined by the store, so a number would be false; names stay."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    store = tree / inbox_watch.SEEN_RELPATH
    store.parent.mkdir(parents=True)
    store.write_bytes(b"{ not json")
    assert inbox_watch.seen_blind_reason(store), "control: the store must read as blind"

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == UNMEASURED, inbox
    assert inbox_watch.seen_blind_reason(store) in inbox["reason"], inbox
    assert inbox["names"] == [NOTE], inbox


def test_a4b_a_fault_in_the_surface_never_escapes_into_the_driver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unexpected fault is UNMEASURED carrying the CLASS name only, and the cycle completes."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    secret = str(tmp_path / "private-detail")

    def boom(_inbox: Path) -> list[Any]:
        raise ValueError(secret)

    monkeypatch.setattr(inbox_watch, "deliverables", boom)

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    assert record["outcome"] == queue_loop.OUTCOME_COMPLETED
    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == UNMEASURED, inbox
    assert "ValueError" in inbox["reason"], inbox
    assert secret not in json.dumps(inbox), "an exception message reached the record"


def test_the_names_are_capped_and_the_rest_counted(tmp_path: Path) -> None:
    """A wall of names is not a report; the cap is the watcher's, the remainder is counted."""
    tree = _main_tree(tmp_path / "wt")
    extra = 3
    total = inbox_watch.MAX_LISTED + extra
    for n in range(total):
        _plant_note(tree, f"2026-01-01-{n:04d}-from-XX-topic.md", body=f"note {n}\n".encode())

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    inbox = record.get("inbox")
    assert inbox is not None, "the cycle record carries no `inbox` key - nothing surfaces"
    assert inbox["unread"] == total, inbox
    assert len(inbox["names"]) == inbox_watch.MAX_LISTED, inbox
    assert inbox["more"] == extra, inbox


# ---------------------------------------------------------------------------
# The lane ledger - the row `run_loop` appends, on the normal and fault paths.
# ---------------------------------------------------------------------------


def _ledger_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_the_lane_ledger_row_carries_the_count_and_the_names(tmp_path: Path) -> None:
    """The JSONL row a night leaves behind names the note, and the emit line does too."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    said: list[str] = []
    seams = _loop_seams(_Clock(), tmp_path, tree, emit=said.append)

    queue_loop.run_loop(**seams)

    (row,) = _ledger_rows(seams["cycle_log"])
    assert row.get("inbox") is not None, "the ledger row carries no `inbox` key"
    assert row["inbox"]["unread"] == 1, row["inbox"]
    assert row["inbox"]["names"] == [NOTE], row["inbox"]
    lines = _inbox_lines("\n".join(said))
    assert len(lines) == 1, lines
    assert NOTE in lines[0], lines
    cycle_lines = [line for line in said if line.startswith("queue-loop cycle ")]
    assert len(cycle_lines) == 1, f"the inbox line must not read as a second cycle line: {said}"


def test_a_cycle_that_faulted_still_leaves_an_inbox_in_its_row(tmp_path: Path) -> None:
    """The run_loop fault path builds its own row; it must not drop the surface."""
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)

    def exploding_acquire(_lane: str, **_kw: Any) -> dict[str, Any]:
        raise RuntimeError("the lock fell over")

    seams = _loop_seams(_Clock(), tmp_path, tree, acquire=exploding_acquire, emit=lambda _l: None)

    queue_loop.run_loop(**seams)

    (row,) = _ledger_rows(seams["cycle_log"])
    assert row["outcome"] == queue_loop.OUTCOME_ERROR, "control: the cycle really faulted"
    assert row.get("inbox") is not None, "the faulted row carries no `inbox` key"
    assert row["inbox"]["names"] == [NOTE], row["inbox"]


# ---------------------------------------------------------------------------
# A5 - runtime purity: the surface writes nothing, anywhere.
# ---------------------------------------------------------------------------

_WRITE_FLAGS: Final = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


@contextlib.contextmanager
def _write_spy() -> Iterator[list[str]]:
    """Record every write-shaped call made through the common spellings.

    Records AND passes through, so a spied writer still behaves; the arm reads
    the record. Installed for the length of the `with` block only, so pytest's
    own capture and cache writes outside it are never counted.
    """
    attempts: list[str] = []
    patches = pytest.MonkeyPatch()
    real_open = io.open

    def spy_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in "wax+"):
            attempts.append(f"open({mode!r})")
        return real_open(file, mode, *args, **kwargs)

    real_os_open = os.open

    def spy_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if flags & _WRITE_FLAGS:
            attempts.append("os.open(write flags)")
        return real_os_open(path, flags, *args, **kwargs)

    def recorder(label: str, real: Callable[..., Any]) -> Callable[..., Any]:
        def spy(*args: Any, **kwargs: Any) -> Any:
            attempts.append(label)
            return real(*args, **kwargs)

        return spy

    patches.setattr(builtins, "open", spy_open)
    patches.setattr(io, "open", spy_open)
    patches.setattr(os, "open", spy_os_open)
    for name in (
        "write_text",
        "write_bytes",
        "mkdir",
        "touch",
        "unlink",
        "rename",
        "replace",
        "rmdir",
        "chmod",
    ):
        patches.setattr(Path, name, recorder(f"Path.{name}", getattr(Path, name)))
    for name in ("replace", "rename", "remove", "unlink", "mkdir", "makedirs", "rmdir"):
        patches.setattr(os, name, recorder(f"os.{name}", getattr(os, name)))
    for name in ("copy", "copy2", "copyfile", "copytree", "move", "rmtree"):
        patches.setattr(shutil, name, recorder(f"shutil.{name}", getattr(shutil, name)))
    try:
        yield attempts
    finally:
        patches.undo()


def _snapshot(tree: Path) -> dict[str, tuple[int, int, bytes]]:
    """Every entry under a tree with mtime and bytes - a same-bytes rewrite still moves mtime."""
    shot: dict[str, tuple[int, int, bytes]] = {}
    for path in sorted(tree.rglob("*")):
        stat = path.lstat()
        body = path.read_bytes() if path.is_file() else b""
        shot[path.relative_to(tree).as_posix()] = (stat.st_mtime_ns, stat.st_size, body)
    return shot


def test_a5_control_the_write_spy_sees_the_watchers_own_writers(tmp_path: Path) -> None:
    """KNOWN-GOOD CONTROL: every writer the fence excludes is visible to the spy.

    Without this the no-writes arm below is a negative with no control: a spy
    that recorded nothing would pass it on a surface that acknowledged every note.
    """
    store = tmp_path / "data" / "inbox_seen.json"
    report = tmp_path / "data" / "inbox_report.txt"
    log = tmp_path / "data" / "inbox_watch_invocations.log"

    for label, act in (
        ("save_seen", lambda: inbox_watch.save_seen(store, {"note:x:y"})),
        ("write_report", lambda: inbox_watch.write_report(report, [], [])),
        ("append_invocation", lambda: inbox_watch.append_invocation(log, mode="m", source="s")),
    ):
        with _write_spy() as attempts:
            act()
        assert attempts, f"the write spy recorded nothing for inbox_watch.{label}"


def test_a5_the_surface_writes_nothing_and_both_trees_are_unchanged(tmp_path: Path) -> None:
    """RUNTIME PURITY on the richest fixture: main tree, worktree, a seen store, one unread.

    THE ORACLE SEES ITS SUBJECT FIRST: the surface must actually have surfaced
    the unread note, asserted before the no-writes verdict is read, so a surface
    that returned early without listing could not pass as pure.
    """
    surface_mod = _surface_module()
    main = _main_tree(tmp_path / "main")
    _plant_note(main, "2026-01-01-0800-from-XX-seen.md")
    _plant_note(main)
    seen_key = next(d.key for d in inbox_watch.deliverables(main / INBOX) if "seen" in d.display)
    store = main / inbox_watch.SEEN_RELPATH
    store.parent.mkdir(parents=True)
    store.write_bytes(json.dumps({"seen": [seen_key]}).encode("ascii"))
    wt = _linked_worktree(main, tmp_path / "wt")
    before_main, before_wt = _snapshot(main), _snapshot(wt)

    with _write_spy() as attempts:
        fact = surface_mod.surface(wt)

    assert fact["unread"] == 1, fact
    assert fact["names"] == [NOTE], fact
    assert attempts == [], f"the surface attempted writes: {attempts}"
    assert _snapshot(main) == before_main, "the main tree changed under a pure read"
    assert _snapshot(wt) == before_wt, "the worktree changed under a pure read"
    assert not (wt / "data").exists(), "the surface created data/ in the worktree"


# ---------------------------------------------------------------------------
# A7 - static purity: the surface touches only the watcher's read API.
# ---------------------------------------------------------------------------


def purity_findings(source: str, module: str = "inbox_watch") -> list[str]:
    """Every call or watcher attribute in `source` outside the read-only fence.

    Two checks, both allowlist-or-verb shaped. Any attribute of the watcher
    module, or any name imported from it, that is not in :data:`READ_API` is a
    finding. Any call whose final name is a write verb in :data:`WRITE_CALLS`,
    and any `open` given a write mode, is a finding.
    """
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [f"import {a.name}" for a in node.names if a.name not in SURFACE_IMPORTS]
        if isinstance(node, ast.ImportFrom) and node.module not in SURFACE_IMPORTS:
            found.append(f"from {node.module} import")
        if isinstance(node, ast.Name) and node.id in DYNAMIC_REACH:
            found.append(f"dynamic reach {node.id}")
        if isinstance(node, ast.Attribute) and node.attr in DYNAMIC_REACH:
            found.append(f"dynamic reach .{node.attr}")
        if isinstance(node, ast.ImportFrom) and node.module == module:
            outside = [a.name for a in node.names if a.name not in READ_API]
            found += [f"from {module} import {name}" for name in outside]
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == module
            and node.attr not in READ_API
        ):
            found.append(f"{module}.{node.attr}")
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in WRITE_CALLS:
                found.append(f"call {name}()")
            if name == "open":
                modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)]
                modes += [
                    k.value.value
                    for k in node.keywords
                    if k.arg == "mode" and isinstance(k.value, ast.Constant)
                ]
                if any(isinstance(m, str) and any(c in m for c in "wax+") for m in modes):
                    found.append(f"open mode {modes}")
    return found


def test_a7_control_the_purity_walk_reports_each_forbidden_shape() -> None:
    """PLANTED CONTROL: a synthetic module carrying each forbidden shape is reported for each."""
    planted = (
        "import inbox_watch\n"
        "from inbox_watch import render\n"
        "inbox_watch.save_seen(p, s)\n"
        "inbox_watch.main([])\n"
        "Path('x').write_text('y')\n"
        "open('x', 'a')\n"
        "os.replace('a', 'b')\n"
        "import subprocess\n"
        "getattr(inbox_watch, 'save_' + 'seen')(p, s)\n"
        "__import__('importlib').import_module('inbox_watch')\n"
        "sys.modules['inbox_watch']\n"
    )
    found = purity_findings(planted)
    for shape in (
        "from inbox_watch import render",
        "inbox_watch.save_seen",
        "inbox_watch.main",
        "call write_text()",
        "call replace()",
        "import subprocess",
        "dynamic reach getattr",
        "dynamic reach __import__",
        "dynamic reach .import_module",
        "dynamic reach .modules",
    ):
        assert shape in found, f"the purity walk missed {shape!r}: {found}"
    assert any(f.startswith("open mode") for f in found), found
    clean = "import inbox_watch\nx = inbox_watch.unread_items(a, b)\nopen('x', 'rb')\n"
    assert purity_findings(clean) == [], "the walk fires on a clean read"


def test_a7_the_surface_module_calls_only_the_read_api() -> None:
    """THE LIVE ARM, with the population asserted non-empty so an empty walk cannot pass."""
    surface_mod = _surface_module()
    source = Path(surface_mod.__file__).read_text(encoding="utf-8")
    used = {
        node.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "inbox_watch"
    }
    assert {"deliverables", "unread_items", "seen_blind_reason"} <= used, (
        f"the surface does not read the watcher API at all, so purity grades nothing: {used}"
    )
    assert purity_findings(source) == []


# ---------------------------------------------------------------------------
# A6 - the reach fence: no lane module can reach the outbound sender.
# ---------------------------------------------------------------------------

_PY_PATH_STRING: Final = re.compile(r"(?:.*[/\\])?(\w+)\.py")

#: The watcher's module stem. IMPORTING it by name is the sanctioned route; a
#: PATH to its file is what a spawn or a path-load of its writing entry point
#: needs, so a whole-string path to it in any lane module is a finding.
WATCHER_STEM: Final = "inbox_watch"

#: The watcher's acknowledging flag. No lane module has a reason to spell it.
ACK_FLAG: Final = "--ack"
_DOTTED_STRING: Final = re.compile(r"\w+(?:\.\w+)*")


def _refs(source: str) -> tuple[set[str], set[str], set[str]]:  # noqa: PLR0912 - one branch per shape
    """Candidate module stems a source names, its sender spellings, and its channel hazards.

    A HAZARD is a spelling only a LANE module is forbidden: the watcher's
    acknowledging flag, or a path to the watcher's own file. The watcher itself
    legitimately spells both, so `reach` counts hazards in lane modules only.

    THREE SHAPES, because a walker that reads only `import` is blind to the lane:
    `import` / `from ... import`, a whole-string dotted name (a `_LAZY` row's
    first element), and a whole-string `name.py` or path to one (a `_LAZY` row's
    filename, a `spec_from_file_location` target, a spawn argv).
    """
    stems: set[str] = set()
    senders: set[str] = set()
    hazards: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        spellings: list[str] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                stems.add(alias.name.rsplit(".", 1)[-1])
                spellings.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                stems.add(node.module.rsplit(".", 1)[-1])
                spellings.append(node.module)
            for alias in node.names:
                stems.add(alias.name)
                spellings.append(alias.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            spellings.append(text)
            if text.strip().startswith(ACK_FLAG):
                hazards.add(f"the acknowledging flag {ACK_FLAG}")
            path_match = _PY_PATH_STRING.fullmatch(text)
            if path_match and path_match.group(1) == WATCHER_STEM:
                hazards.add("a path to the watcher entry point")
            if path_match:
                stems.add(path_match.group(1))
            elif _DOTTED_STRING.fullmatch(text):
                stems.add(text.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Name):
            spellings.append(node.id)
        elif isinstance(node, ast.Attribute):
            spellings.append(node.attr)
        senders.update(s for s in SENDER_STEMS for text in spellings if s in text)
    return stems, senders, hazards


def reach(loop_dir: Path, tools_dir: Path) -> dict[str, Any]:
    """The transitive reach of every lane module, and what it found.

    Seeds are EVERY `.py` in the lane directory, so a module no other module
    imports is still graded. A stem resolves to every file of that name in
    either directory - over-approximating is the right error for a fence.
    Non-Python lane files (the launcher scripts) are text-scanned for a sender
    name, since they have no AST to walk.
    """
    edges: set[tuple[str, str]] = set()
    reached: dict[Path, str] = {}
    literal_hits: set[str] = set()
    queue = sorted(loop_dir.glob("*.py"))
    while queue:
        path = queue.pop()
        if path in reached:
            continue
        reached[path] = "tools" if path.parent == tools_dir else "loop"
        stems, senders, hazards = _refs(path.read_text(encoding="utf-8"))
        literal_hits.update(f"{path.name}: {s}" for s in senders)
        if reached[path] == "loop":
            literal_hits.update(f"{path.name}: {h}" for h in hazards)
        for stem in sorted(stems):
            for base in (loop_dir, tools_dir):
                target = base / f"{stem}.py"
                if target.is_file() and target != path:
                    edges.add((path.stem, stem))
                    if target not in reached:
                        queue.append(target)
    for other in sorted(p for p in loop_dir.iterdir() if p.is_file() and p.suffix != ".py"):
        text = other.read_text(encoding="utf-8", errors="replace")
        literal_hits.update(f"{other.name}: {s}" for s in SENDER_STEMS if s in text)
        if ACK_FLAG in text:
            literal_hits.add(f"{other.name}: the acknowledging flag {ACK_FLAG}")
    stems_reached = {p.stem for p in reached}
    tools_reached = {p.stem for p, where in reached.items() if where == "tools"}
    return {
        "edges": edges,
        "reached": stems_reached,
        "senders_reached": stems_reached & SENDER_STEMS,
        "literal_hits": literal_hits,
        "tools_outside_allowlist": tools_reached - LANE_TOOLS_ALLOWED,
    }


def _violations(found: dict[str, Any]) -> list[str]:
    return sorted(
        [f"reached {s}" for s in found["senders_reached"]]
        + [f"names {h}" for h in found["literal_hits"]]
        + [f"tool outside allowlist: {t}" for t in found["tools_outside_allowlist"]]
    )


def test_a6_control_the_walk_sees_the_edges_it_exists_to_follow() -> None:
    """POSITIVE CONTROL, LIVE tree: the driver reaches the surface, the surface the watcher.

    A walker that returned nothing would pass the fence below; this cannot.
    The `_LAZY` edge in particular is a whole-string shape an import-only walk
    misses, so seeing it proves the walk reads that shape.
    """
    found = reach(LOOP_DIR, TOOLS_DIR)

    assert ("queue_loop", "inbox_surface") in found["edges"], sorted(found["edges"])
    assert ("inbox_surface", "inbox_watch") in found["edges"], sorted(found["edges"])
    assert ("queue_loop", "claims") in found["edges"], "the _LAZY row shape is not followed"
    assert {p.stem for p in LOOP_DIR.glob("*.py")} <= found["reached"]
    tool_stems = {p.stem for p in TOOLS_DIR.glob("*.py")}
    assert tool_stems >= SENDER_STEMS, (
        "control: the sender files this fence names are not where it looks"
    )


def test_a6_no_lane_module_reaches_the_outbound_sender() -> None:
    """THE FENCE, on the live tree: no sender reached, no sender named, no unlisted tool."""
    assert _violations(reach(LOOP_DIR, TOOLS_DIR)) == []


def _copy_tree(tmp_path: Path) -> tuple[Path, Path]:
    loop = tmp_path / "ops" / "loop"
    tools = tmp_path / "tools"
    loop.mkdir(parents=True)
    tools.mkdir()
    for src in LOOP_DIR.iterdir():
        if src.is_file() and src.suffix in (".py", ".ps1"):
            shutil.copyfile(src, loop / src.name)
    for src in TOOLS_DIR.glob("*.py"):
        shutil.copyfile(src, tools / src.name)
    return loop, tools


_PLANTS: Final = (
    ("a bare import", "planted.py", "import outbound_send\n", "reached outbound_send"),
    (
        "a _LAZY row",
        "planted.py",
        '_LAZY = {"x": ("ops.loop.x", "cs_loop_x", "outbound_gate.py")}\n',
        "reached outbound_gate",
    ),
    (
        "a path-load string",
        "planted.py",
        "import importlib.util\n"
        'spec = importlib.util.spec_from_file_location("m", "outbound_send.py")\n',
        "reached outbound_send",
    ),
    (
        "a spawn argv",
        "planted.py",
        'ARGV = ["python", "tools/outbound_gate.py"]\n',
        "reached outbound_gate",
    ),
    (
        "a launcher script naming the sender",
        "planted.ps1",
        "& python tools/outbound_send.py --send\n",
        "names planted.ps1: outbound_send",
    ),
    (
        "an unlisted tool reached through a path-load",
        "planted.py",
        'TARGET = "drift_guard.py"\n',
        "tool outside allowlist: drift_guard",
    ),
    (
        "a spawn of the watcher entry point (M3e)",
        "planted.py",
        'import sys\nARGV = [sys.executable, str(_TOOLS_DIR / "inbox_watch.py")]\n',
        "names planted.py: a path to the watcher entry point",
    ),
    (
        "the acknowledging flag in an argv (M3e)",
        "planted.py",
        'ARGV = ["python", "-m", "x", "--ack"]\n',
        "names planted.py: the acknowledging flag --ack",
    ),
)


def test_a6_control_a_clean_copy_of_the_lane_has_no_violations(tmp_path: Path) -> None:
    """The plants below are the only cause of their verdicts."""
    loop, tools = _copy_tree(tmp_path)
    assert _violations(reach(loop, tools)) == []


@pytest.mark.parametrize(("shape", "filename", "plant", "expected"), _PLANTS)
def test_a6_control_each_planted_reach_shape_is_reported(
    tmp_path: Path, shape: str, filename: str, plant: str, expected: str
) -> None:
    """PLANTED CONTROLS, one per shape the lane actually uses to reach a module."""
    loop, tools = _copy_tree(tmp_path)
    target = loop / filename
    target.write_bytes(plant.encode("ascii"))
    assert target.read_bytes() == plant.encode("ascii"), "control: the plant did not land"

    got = _violations(reach(loop, tools))

    assert expected in got, f"the walk missed {shape}: {got}"


def test_a6_control_a_sender_reached_through_an_allowed_tool_is_still_reported(
    tmp_path: Path,
) -> None:
    """TRANSITIVITY: a lane module path-loads a tool that itself imports the gate."""
    loop, tools = _copy_tree(tmp_path)
    (tools / "relay.py").write_bytes(b"import outbound_gate\n")
    (loop / "planted.py").write_bytes(b'RELAY = "relay.py"\n')

    found = reach(loop, tools)

    assert ("planted", "relay") in found["edges"]
    assert "outbound_gate" in found["senders_reached"], sorted(found["reached"])


# ---------------------------------------------------------------------------
# The detached driver's sys.path - the one shape no in-repo import has.
# ---------------------------------------------------------------------------

_BIND_PROBE: Final = """
try:
    import ops  # noqa: F401
    print("OPS_IMPORTABLE")
except ModuleNotFoundError:
    print("OPS_ABSENT")
import queue_loop
mod = queue_loop._mod("inbox_surface")
print("BOUND " + mod.__name__)
"""


def test_the_detached_driver_can_bind_the_surface_without_the_repository_root() -> None:
    """`pythonw <repo>/ops/loop/queue_loop.py` has `ops/loop` on its path and the root nowhere.

    FRONTED BY A CONTROL: the child must be unable to import `ops`, or it is not
    the detached shape and the bind below proves nothing.
    """
    argv = [sys.executable, "-c", _BIND_PROBE]
    done = subprocess.run(
        argv, capture_output=True, text=True, check=False, timeout=120, cwd=str(LOOP_DIR)
    )
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    assert lines, f"the probe printed nothing - stderr {done.stderr[-600:]!r}"
    assert lines[0] == "OPS_ABSENT", "the child can import ops, so this grades nothing"
    assert done.returncode == 0, f"the surface failed to bind detached: {done.stderr[-800:]!r}"
    assert any(line.startswith("BOUND ") for line in lines), lines


# ---------------------------------------------------------------------------
# Repair arms - D3, D4, W1, W2, W5.
# ---------------------------------------------------------------------------


def test_d3_a_no_store_tree_is_read_twice_identically_and_never_written(tmp_path: Path) -> None:
    """D3: the write-spy arm on the fixture with NO seen store, which is the FIRST-RUN state.

    An acknowledgement guarded on "no store yet" is invisible to a fixture that
    already has one. Read twice: an acknowledging surface answers 1 then 0, or
    leaves a store behind, or moves the tree - three independent oracles, one of
    which (the second read) also sees a write a CHILD process made, which no
    in-process spy can.
    """
    surface_mod = _surface_module()
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    assert not (tree / inbox_watch.SEEN_RELPATH).exists(), "control: the fixture has a store"
    before = _snapshot(tree)

    with _write_spy() as attempts:
        first = surface_mod.surface(tree)
        second = surface_mod.surface(tree)

    assert first["unread"] == 1, first
    assert second == first, f"a second read disagreed with the first: {first} then {second}"
    assert attempts == [], f"the surface attempted writes: {attempts}"
    assert not (tree / "data").exists(), "the surface created data/ on a first run"
    assert _snapshot(tree) == before, "the tree changed under two pure reads"


def test_d4_a_lying_worker_banner_never_replaces_the_driver_measurement(tmp_path: Path) -> None:
    """D4: the row carries what the DRIVER measured, whatever the worker's output says.

    The worker's log - the only worker text the driver holds - is planted with an
    `inbox:` banner that disagrees in count and names. The control asserts the
    lie really is in the file the cycle records as its log.
    """
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    log = tmp_path / "worker.log"
    lie = 'inbox: 7 ("forged-by-the-worker.md") - surfaced, never acknowledged\n'
    log.write_bytes(("CLOCKSPEED QUEUE CYCLE WRAP\n  " + lie).encode("ascii"))
    said: list[str] = []
    seams = _cycle_seams(
        _Clock(),
        tree,
        launch=lambda _lane, **_kw: {"pid": 4242, "log": str(log)},
        emit=said.append,
    )

    record = queue_loop.run_cycle(1, **seams)

    assert record["detail"] == str(log), "control: the cycle did not record the lying log"
    assert "forged-by-the-worker.md" in log.read_text(encoding="ascii")
    assert record["inbox"]["unread"] == 1, record["inbox"]
    assert record["inbox"]["names"] == [NOTE], record["inbox"]
    assert not any("forged-by-the-worker" in line for line in said), said


def test_w1_a_channel_that_is_a_file_is_unmeasured(tmp_path: Path) -> None:
    """W1: a FILE where the channel directory should be was not looked into. Never 0."""
    tree = _main_tree(tmp_path / "wt")
    (tree / INBOX).write_bytes(b"not a directory\n")
    assert (tree / INBOX).is_file(), "control: the channel is not a file"

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    assert record["inbox"]["unread"] == UNMEASURED, record["inbox"]
    assert record["inbox"]["reason"], record["inbox"]


@contextlib.contextmanager
def _unlistable(directory: Path) -> Iterator[None]:
    """A REAL listing fault on a directory that still stats as a directory.

    On Windows an EXCLUSIVE handle on the directory itself (share mode zero), so
    every listing meets a real sharing violation while a stat still answers.
    MEASURED: a deny ACE for list-directory did NOT stop an elevated listing on
    this machine, so it is not used. Elsewhere, a mode of zero. No stub: the
    fault is the operating system's, so the whole read path meets it.
    """
    if os.name == "nt":
        import ctypes  # noqa: PLC0415 - Windows-only
        from ctypes import wintypes  # noqa: PLC0415 - Windows-only

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        generic_read, no_sharing, open_existing, backup_semantics = 0x80000000, 0, 3, 0x02000000
        handle = kernel32.CreateFileW(
            str(directory), generic_read, no_sharing, None, open_existing, backup_semantics, None
        )
        assert handle not in (None, wintypes.HANDLE(-1).value), "control: no exclusive handle"
        try:
            yield
        finally:
            kernel32.CloseHandle(handle)
    else:
        mode = directory.stat().st_mode
        directory.chmod(0)
        # CONTROL, as on Windows: the fault really landed. Restore before failing,
        # so a refused chmod never strands an unreadable directory behind it.
        landed = directory.stat().st_mode & 0o777
        if landed:
            directory.chmod(mode)
        assert not landed, "control: the mode did not drop to zero"
        try:
            yield
        finally:
            directory.chmod(mode)


def test_w1_a_real_permission_fault_on_the_listing_is_unmeasured(tmp_path: Path) -> None:
    """W1: the operating system refuses the listing -> UNMEASURED, not 0 and not [].

    CONTROLS INSIDE THE FAULT: the directory still reports as a directory, and a
    direct listing really raises PermissionError - so the verdict is about a
    real refusal, not a fixture that quietly let the listing through.
    """
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    inbox = tree / INBOX

    with _unlistable(inbox):
        assert inbox.is_dir(), "control: the refused channel no longer stats as a directory"
        with pytest.raises(PermissionError):
            list(inbox.iterdir())
        record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    assert record["inbox"]["unread"] == UNMEASURED, record["inbox"]
    assert record["inbox"]["names"] == [], record["inbox"]
    assert "could not be listed" in record["inbox"]["reason"], record["inbox"]


_BLIND_STORES: Final = (
    ("not JSON", b"{ not json"),
    ("a JSON list, not an object", b"[]"),
    ("no seen key", b'{"other": []}'),
    ("seen is a string", b'{"seen": "x"}'),
    ("seen is an object", b'{"seen": {}}'),
    ("a directory", None),
)


@pytest.mark.parametrize(("shape", "body"), _BLIND_STORES)
def test_w2_every_store_that_yields_no_seen_set_is_unmeasured(
    tmp_path: Path, shape: str, body: bytes | None
) -> None:
    """W2: ANY failure to yield a seen set - not only invalid JSON - is UNMEASURED with names.

    CONTROL: the watcher itself calls each planted store blind, so the arm grades
    the surface's handling rather than a store the watcher would have read.
    """
    tree = _main_tree(tmp_path / "wt")
    _plant_note(tree)
    store = tree / inbox_watch.SEEN_RELPATH
    if body is None:
        store.mkdir(parents=True)
    else:
        store.parent.mkdir(parents=True)
        store.write_bytes(body)
    blind = inbox_watch.seen_blind_reason(store)
    assert blind, f"control: the watcher reads the {shape} store as fine"

    record = queue_loop.run_cycle(1, **_cycle_seams(_Clock(), tree))

    assert record["inbox"]["unread"] == UNMEASURED, (shape, record["inbox"])
    assert blind in record["inbox"]["reason"], (shape, record["inbox"])
    assert record["inbox"]["names"] == [NOTE], (shape, record["inbox"])


def test_w5_ledger_names_are_escaped_with_no_path_component(tmp_path: Path) -> None:
    """W5 (CS-701): names reach a gitignored ledger by acceptance, so each is a bare escaped name.

    The fixture carries a PAYLOAD directory holding a nested file and a non-ASCII
    note, so a surface that walked into the payload or rendered a raw name has
    something to leak. The control asserts the nested file and the raw glyph
    are really on disk.
    """
    tree = _main_tree(tmp_path / "wt")
    raw = "2026-01-01-0902-from-XX-na" + chr(239) + "ve.md"
    _plant_note(tree, raw)
    payload = tree / INBOX / "2026-01-01-0903-from-XX-payload"
    (payload / "inner").mkdir(parents=True)
    (payload / "inner" / "deep.md").write_bytes(b"deep\n")
    assert (payload / "inner" / "deep.md").is_file()
    said: list[str] = []
    seams = _loop_seams(_Clock(), tmp_path, tree, emit=said.append)

    queue_loop.run_loop(**seams)

    (row,) = _ledger_rows(seams["cycle_log"])
    names = row["inbox"]["names"]
    assert len(names) == 2, row["inbox"]  # noqa: PLR2004 - the note and the payload
    for name in names:
        assert name.isascii(), name
        assert name.isprintable(), name
        assert "/" not in name, name
        assert "\\" not in name, name
        assert "deep" not in name, name
        assert "inner" not in name, name
    raw_line = seams["cycle_log"].read_bytes()
    assert raw.encode("utf-8") not in raw_line, "the raw sender-controlled name reached the ledger"
    assert str(tmp_path).encode("utf-8") not in raw_line.replace(b"\\\\", b"\\"), (
        "an absolute path reached the ledger"
    )


def test_a6_control_the_hazard_detector_sees_the_watchers_own_ack_flag() -> None:
    """POSITIVE CONTROL for the lane-only hazards: the watcher really spells `--ack`.

    The live fence counts hazards in lane modules only. This proves the detector
    fires on the one file that legitimately carries the flag, so its silence over
    the lane is a measurement rather than a detector that never matches.
    """
    _stems, _senders, hazards = _refs((TOOLS_DIR / "inbox_watch.py").read_text(encoding="utf-8"))

    assert f"the acknowledging flag {ACK_FLAG}" in hazards, hazards
