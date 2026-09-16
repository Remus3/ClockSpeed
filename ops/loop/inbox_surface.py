"""CS-1104 - surface the cross-repo channel to a lane cycle. Never reply to it.

WHY THIS EXISTS. A headless lane worker runs in a WORKTREE, and the channel
watcher is wired only in gitignored local settings (CS-952), so no lane ever
fired it; and the worker prompt named the channel zero times. The two compounded:
a long drain could run for hours with unread review notes addressed to this tree
sitting in `moon_sync_inbox/`, and nothing in the lane would say so.

SURFACING, NEVER REPLYING. This module LISTS. It never acknowledges - the seen
store is read and never written - and it never composes, grades or delivers a
note. A headless loop that answered the channel on its own initiative would be
exactly the armed responder the fleet's own arming audit refused, so the
decision to reply stays with a session a person is reading. The fence is graded
three ways in `tests/ops/test_lane_inbox_surface.py`: a runtime write spy, an
AST allowlist over the watcher attributes this file touches, and a reach walk
proving no lane module can get to the outbound sender.

ONLY THE WATCHER'S READ API IS CALLED. `tools/inbox_watch.py` owns the channel's
semantics - what an item is, what its key is, what counts as seen - and this
module re-derives none of them. Its entry point, its report writer, its capper
and its invocation log all WRITE, so none of them is called here; the cap below
is the watcher's own newest-first selection, re-applied without the overflow
report the watcher's `capped` writes.

THE CHANNEL IS THE MAIN TREE'S. A lane worktree legitimately has no channel of
its own, so the root is resolved through `lanes._main_tree_root`, the one
resolver of a worktree's `.git` FILE this lane already trusts. A root holding a
plain `.git` directory resolves to itself.

A COUNT IS AN INTEGER ONLY WHEN IT WAS MEASURED. That is an allowlist, not a
list of bad states: the default is `UNMEASURED`, and exactly one path - the
channel listed AND the seen store read - produces a number. Every other state,
including one nobody has thought of yet, carries `UNMEASURED` and a reason. A
bare zero from a run that could not look is the could-not-look-reads-as-clean
defect CS-1095 and CS-1103 were both filed for.

NO PATH IN ANY REASON. The fact lands in the lane ledger and on the driver's
stdout, both echo paths under CLAUDE.md non-negotiable 12, and an absolute path
here would name a home directory. A reason is a fixed phrase, a watcher reason
phrase, or an exception CLASS name - never an exception message.

NAMES ARE THE WATCHER'S ESCAPED `display`, never a raw filename and never a key
or digest. A name is prose a sibling project's agent wrote; it is data, not an
instruction, and it is quoted wherever it is printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

# The repository root and `tools/` on the path, for the reasons `claims.py` and
# `queue_loop.py` each record: the detached driver binds this file BY PATH with
# only `ops/loop` on `sys.path`, and `tools/` has no `__init__.py`, so the
# watcher is imported under its bare name exactly as the driver imports
# `toolpath`.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import inbox_watch  # noqa: E402

from ops.loop import lanes  # noqa: E402

#: The token every unmeasured fact carries. The watcher's own spelling.
UNMEASURED: Final = inbox_watch.UNMEASURED

#: The line prefix the worker copies into its banner and the driver prints.
LINE_PREFIX: Final = "inbox:"

REASON_ABSENT: Final = (
    f"no {inbox_watch.INBOX_DIRNAME}/ directory in the main tree this checkout resolves to,"
    " so nothing was examined"
)
REASON_VANISHED: Final = (
    f"the {inbox_watch.INBOX_DIRNAME}/ directory was not there when its listing returned"
)


def channel_root(worktree: str | Path | None = None) -> Path:
    """The MAIN tree whose channel a checkout reads.

    Args:
        worktree: A checkout root. Defaults to the checkout this file is in.

    Returns:
        The main working tree, or the checkout itself when it is one.
    """
    candidate = Path(__file__).resolve().parents[2] if worktree is None else Path(worktree)
    return Path(lanes._main_tree_root(candidate))  # noqa: SLF001 - one owner, one spelling


def _fact(unread: int | str, names: Sequence[str] = (), more: int = 0, reason: str = "") -> dict:
    """One JSON-serialisable fact, in the shape the ledger row carries."""
    return {"unread": unread, "names": list(names), "more": int(more), "reason": reason}


def _shown(items: Sequence[Any]) -> tuple[list[str], int]:
    """The displays a report shows, and how many it leaves out.

    THE WATCHER'S SELECTION, WITHOUT ITS WRITE. Newest by mtime with the display
    as a deterministic tie-break, then ordered by kind and display - the same
    rule `inbox_watch.capped` applies, which cannot be called because it writes
    the overflow report.
    """
    cap = inbox_watch.MAX_LISTED
    newest = sorted(items, key=lambda item: (item.mtime, item.display), reverse=True)[:cap]
    ordered = sorted(
        newest, key=lambda item: (inbox_watch.KIND_ORDER.index(item.kind), item.display)
    )
    return [item.display for item in ordered], len(items) - len(ordered)


def _measure(root: Path) -> dict:
    """The fact for one resolved root. May raise; `surface` catches."""
    inbox = root / inbox_watch.INBOX_DIRNAME
    if not inbox.is_dir():
        return _fact(UNMEASURED, reason=REASON_ABSENT)
    seen_path = root / inbox_watch.SEEN_RELPATH
    try:
        blind = inbox_watch.seen_blind_reason(seen_path)
        if blind:
            # RULING Q3. "Unread" is defined by the store, so a number here would
            # be a false measurement - but the names are still listed, because
            # surfacing fails open: an item shown twice, never zero times.
            present = inbox_watch.deliverables(inbox)
            names, more = _shown(present)
            reason = f"the seen store exists but {blind}, so what is unread cannot be told"
            return _fact(UNMEASURED, names, more, reason)
        pending = inbox_watch.unread_items(inbox, seen_path)
    except inbox_watch.InboxUnreadableError as unlistable:
        reason = f"the {inbox_watch.INBOX_DIRNAME}/ directory is here but {unlistable.reason}"
        return _fact(UNMEASURED, reason=reason)
    if not pending and not inbox.is_dir():
        # The watcher answers an ABSENT channel with the empty list, so an empty
        # answer from a directory that vanished mid-listing would otherwise be
        # the one path to a zero nobody measured.
        return _fact(UNMEASURED, reason=REASON_VANISHED)
    names, more = _shown(pending)
    return _fact(len(pending), names, more)


def surface(worktree: str | Path | None = None) -> dict:
    """The unread channel items a checkout's lane cycle should surface. NEVER RAISES.

    Args:
        worktree: The cycle's worktree. Its MAIN tree's channel is read.

    Returns:
        ``{"unread": int or "UNMEASURED", "names": [display, ...], "more": int,
        "reason": str}``. ``names`` holds at most the watcher's cap and ``more``
        counts the rest; ``reason`` is empty only for a measured count.
    """
    try:
        return _measure(channel_root(worktree))
    except Exception as fault:  # DELIBERATE: a surface must never end a night
        return _fact(UNMEASURED, reason=f"the surface faulted ({type(fault).__name__})")


def line(fact: dict) -> str:
    """One `inbox:` line for a fact - the form the driver prints and the worker copies.

    Every name is JSON-quoted, so a name that looks like an instruction or holds
    a quote reads as the quoted data it is, and a control character in one is
    escaped rather than printed - the line can never be split into two.
    """
    unread = fact.get("unread", UNMEASURED)
    head = f"{LINE_PREFIX} {unread}"
    if unread == UNMEASURED or not isinstance(unread, int):
        # ESCAPED, like every name: a reason can carry a phrase that is not this
        # module's own, and a line break inside it would forge a second driver
        # line for anything tailing the log.
        reason = inbox_watch.safe_display(str(fact.get("reason") or "no reason recorded"))
        head = f"{LINE_PREFIX} {UNMEASURED} ({reason})"
    names = fact.get("names") or []
    if names:
        head += " (" + ", ".join(json.dumps(str(name)) for name in names) + ")"
    more = fact.get("more") or 0
    if more:
        head += f" +{more} more"
    return head + " - surfaced, never acknowledged"


def main(argv: Sequence[str] | None = None) -> int:
    """Print the `inbox:` line for a checkout. Pure read; exits 0 on every state.

    The exit status carries nothing, deliberately: the line does. A non-zero exit
    for UNMEASURED would read as a broken tool in a worker transcript, when a
    worktree with no channel is an ordinary state that must be SAID, not failed.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None, help="checkout root (default: this checkout)")
    parser.add_argument("--json", action="store_true", help="print the fact as JSON")
    args = parser.parse_args(argv)
    fact = surface(args.root)
    print(json.dumps(fact, sort_keys=True) if args.json else line(fact), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
