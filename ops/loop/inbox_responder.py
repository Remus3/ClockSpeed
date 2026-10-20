r"""CS-1226 - the one-shot inbox responder: spawn one routed worker when mail is waiting.

OPERATOR RULING, 2026-10-02 (recorded in docs/LEDGER.md): arm an autonomous
responder for the cross-repo channel. That ruling SUPERSEDES the "surfacing,
never replying" fence FOR THIS MODULE ONLY. The queue lane still never replies,
and `ops/loop/inbox_surface.py` keeps its fence and its tests unchanged.

THE FENCE STILL HOLDS BY STRUCTURE, so no exemption was written into it. This
module never composes, grades, sends or acknowledges anything. It decides
WHETHER to start a worker, starts it, and records the outcome. Everything the
worker does - reading notes, replying through the gated sender, acknowledging -
is instructed by the tracked prompt `tools/headless-inbox.md` and happens inside
the spawned process, so the reach walk over `ops/loop/*.py` in
`tests/ops/test_lane_inbox_surface.py` still finds no lane module that reaches
the sender, and it stays the arm that would redden if this file ever did.

ONE SHOT, `--once`, meant for a Windows scheduled task every fifteen minutes:

  1. A stop sentinel - `ops/loop/control/STOP` (the lane-wide one) or
     `ops/loop/control/lanes/INBOX_STOP` (this responder's own, mirroring the
     queue lane's QUEUE_STOP) - ends the run before anything else.
     The halted path still publishes `inbox_status.json` (state "halted")
     before it exits, so the widget shows a halt, never no signal.
  2. A single-instance named mutex; a run already in progress ends this one
     after refreshing the age of the status that run owns.
  3. The channel is listed through `inbox_surface.surface`, the watcher's READ
     API and nothing else. Zero unread ends the run quietly - no log line, so
     a quiet channel costs 96 no-ops a day and zero bytes. An UNMEASURED count
     never spawns: a run that could not look must not guess.
     LOOP DAMPING (`is_damped`): our OWN notes, notes FROM a retired sibling
     (`RETIRED_SENDERS`, MAIN 0230 item 4) and notes marked TERMINAL or
     no-reply never start a run; with nothing else unread the pass is idle.
     Who a note is FROM is the kit's own `note_sender` (CS-1272 H2), never a
     local pattern. A pass that listed a retired sibling's note logs a NAMED
     skip ("retired_skip", the sibling's code from the table) every time it does.
     CS-1272 H3: every per-note decision reads the REAL filename the kit reads,
     never the watcher's capped display - the surface hands `verdict` each
     unread item's real name, past the listing cap too, and carries back only
     the closed-vocabulary word (`VERDICTS`), never the name.
  4. A back-off file written after a usage-limit refusal holds every run for
     `BACKOFF_S`, so the account's "no" is not hammered every fifteen minutes.
  5. CS-1231 SLICE C - THE WORKER STARTS ONLY THROUGH THE FLEET KIT'S SPAWN
     HELPER (`ops/fleet_kit/fleet_headless.spawn`, FLEET item 10), the one path
     that starts `claude` on this machine. The kit reads its headless route
     and fails closed exactly as FLEET item 10 states; counts the start
     against its tree-wide budget of 120 per rolling 24 hours under a lock,
     refusing every start on an unreadable budget and never resetting it
     (CS-1234, MAIN 0855); keeps the CLI off the working directory; and kills
     the whole tree on a timeout. `floors_in_hooks=True` (`FLOORS_IN_HOOKS`),
     because this tree's floors live in hooks and `--bare` skips them, so the
     kit refuses a bare run. A triage pass spawns with the kit's
     `fleet_inbox.triage_spawn_kwargs(FLOORS_IN_HOOKS)` whole, its timeout
     included (FLEET-KIT v11, CS-1287); every other pass with `WORKER_TIMEOUT_S`.
  6. Strict MCP and project settings, the prompt on stdin, cwd the main tree
     root, `--dangerously-skip-permissions` the one extra flag. Sonnet unless a
     live note is an ORDER, FIX or RULING or sits past the listing cap; effort
     low only when every live note is an acknowledgement (`_kit_inputs`).
     CS-1272 H: the spawn carries a NON-EMPTY label (`run_label`, the first
     live note's basename) and a kind (`run_kind`: "triage" on the kit's
     triage shape, sonnet at effort low, else "inbox"), so the kit's usage
     line under `ops/loop/control/` attributes the run. While the worker runs,
     the fire's progress file carries its item-13 checklist (`_Progress`).
  7. The exit is classified and one JSON line is appended to a gitignored log
     under `data/`. The line holds outcome words, counts and durations ONLY -
     no path, no env value, no message body, no worker output (CLAUDE.md rules
     12 and 13).
  8. Every state change publishes the inbox-status file in the control directory
     (schema 1, MAIN 0915) through `ops/loop/inbox_status.py`. The kit writes the
     same file on its own transitions; the responder writes after each of them,
     so the published task, ETA and window are always the responder's.
     CS-1282 (FLEET-KIT v10): a start that never ran - refused by the kit, an
     unmeasured channel, an unreadable prompt, a worker that could not start -
     reads state "refused" with the kit's own `REFUSED_TASK` ("Idle"); only a
     halt reads "Halted", so the board never contradicts the kit's own write.

THE SCHEDULED TASK, armed by the merger, never by this module. `<pythonw>` and
`<repo>` are resolved at arm time (`(Get-Command pythonw).Source`, the checkout
root); no interpreter or checkout path is written into a tracked file:

  schtasks /Create /F /SC MINUTE /MO 15 /TN "Clockspeed inbox responder"
    /TR "\"<pythonw>\" \"<repo>\ops\loop\inbox_responder.py\" --once"

It must run as the operator's own account, so the user environment store the
route reads is the right one.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Final

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ops.fleet_kit import fleet_checklist  # noqa: E402
from ops.fleet_kit import fleet_headless as kit  # noqa: E402
from ops.fleet_kit import fleet_inbox as inbox_kit  # noqa: E402
from ops.loop import headless_route, inbox_status, inbox_surface, winmutex  # noqa: E402

#: The control directory and the sentinels that stop this responder.
CONTROL: Final = _HERE / "control"
STOP_RELPATHS: Final = ("STOP", "lanes/INBOX_STOP")

#: The single-instance mutex, in the session namespace.
MUTEX_NAME: Final = "Local\\clockspeed-inbox-responder"

#: The tracked worker prompt, relative to the main tree root.
PROMPT_RELPATH: Final = Path("tools") / "headless-inbox.md"

#: The gitignored run log and back-off file, relative to the main tree root.
LOG_RELPATH: Final = Path("data") / "inbox_responder.jsonl"
BACKOFF_RELPATH: Final = Path("data") / "inbox_responder_backoff.json"

#: How long a usage-limit refusal holds every later run.
BACKOFF_S: Final = 3600.0

#: The worker's wall-clock ceiling. A reply plus a pushed fix runs the whole
#: suite in the pre-push hook; three hours bounds a wedged worker without
#: killing an honest one.
WORKER_TIMEOUT_S: Final = 3 * 3600.0

#: This tree's floors live in hooks, and ``--bare`` skips hooks, so the kit is
#: told so on every spawn and refuses a bare run. FLEET-KIT v11 ORDER item 3
#: (CS-1287): a triage spawn takes ``fleet_inbox.triage_spawn_kwargs`` of this
#: flag WHOLE - model, effort and the kit's own triage timeout included - in
#: place of any local override.
FLOORS_IN_HOOKS: Final = True

#: The one flag the kit's argv does not carry. The worker runs unattended, so a
#: permission prompt would wait forever; the kit refuses only fallback and bare
#: flags here.
KIT_EXTRA: Final = ("--dangerously-skip-permissions",)

#: The kit's refusal when its budget lock stays busy - a counting failure, so it
#: is logged with the unreadable budget rather than with a proxy refusal. The
#: kit is byte-pinned, so this string moves only with a new kit version.
KIT_LOCK_BUSY: Final = "budget lock busy"

#: Set on the worker for the reasons `ops/loop/run_lane.ps1` records (CS-1108):
#: nothing backgrounded, and a long foreground command survives. The kit builds
#: the child's environment from this process's own, so they are set here, for
#: the length of the spawn only.
WORKER_ENV: Final = {
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "2400000",
    "BASH_MAX_TIMEOUT_MS": "2400000",
    "BASH_DEFAULT_TIMEOUT_MS": "2400000",
}

EXIT_OK: Final = 0
EXIT_ROUTE_REFUSED: Final = 3
EXIT_WORKER_FAILED: Final = 4
EXIT_USAGE_LIMIT: Final = 5
EXIT_UNMEASURED: Final = 6
EXIT_SPAWN_FAILED: Final = 7
EXIT_TIMEOUT: Final = 8
EXIT_BUDGET_REFUSED: Final = 9

#: Every key a log line may carry. A closed set, graded by the tests.
LOG_KEYS: Final = frozenset(
    {"ts", "outcome", "exit", "unread", "returncode", "duration_s", "reason"}
)

#: The CANONICAL sender position - the first ``-from-<CODE>-`` straight after
#: the timestamp - and the damping markers. CS-1272 H2: this shape is read for
#: ONE rule only, MAIN's exemption from the terminal rule, because an exemption
#: is a reason TO start a run and so is read narrowly. Every reason NOT to start
#: one (our own note, a retired sibling) reads the sender exactly as the kit
#: does (`kit.note_sender`), which also finds a date-only, a sender-leading and
#: an upper-cased ``FROM`` name - shapes this anchored pattern never matched.
_CANONICAL_SENDER_RE: Final = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}-from-([A-Za-z0-9]+)-")
_TERMINAL_RE: Final = re.compile(r"terminal|no-?reply", re.IGNORECASE)
_EXEMPT_SENDER: Final = "MAIN"

#: RETIRED SIBLINGS by channel code (CS-1272 H, MAIN 0230 item 4: "Never spawn
#: a headless run for LL"). A note FROM one never starts a run, and a pass that
#: listed one records a named skip.
# MIRRORED, NOT IMPORTED, from the RETIRED_SIBLINGS table of the outbound
# sender in tools/ (slice R). The A6 reach fence in
# tests/ops/test_lane_inbox_surface.py reddens on any lane module that reaches
# the sender, by import or even by spelling its name in a string, so this
# module may not read that table; tests/ops/test_inbox_responder.py pins this
# set to that table's values, so the two cannot part.
RETIRED_SENDERS: Final = frozenset({"LL"})

#: CS-1272 H3 - THE VERDICT on one unread item, decided by `verdict` on the
#: item's REAL name and carried back by the surface IN PLACE of that name. A
#: closed vocabulary: the only per-item words that leave the judge, so no byte
#: a sender wrote rides with them. Damped words start nothing; live words start
#: a run and weigh it.
VERDICT_OWN: Final = "own"
VERDICT_TERMINAL: Final = "terminal"
VERDICT_LIVE: Final = "live"
VERDICT_ACK: Final = "live-ack"
VERDICT_HEAVY: Final = "live-heavy"
#: An item past the cap that no judge saw, or a word outside the vocabulary:
#: live, and assumed heavy rather than guessed light.
VERDICT_UNSEEN: Final = "unseen"
#: One damped word per retired code, spelled from the table, never from a name.
RETIRED_VERDICTS: Final = {code: f"retired:{code}" for code in sorted(RETIRED_SENDERS)}
DAMPED_VERDICTS: Final = frozenset({VERDICT_OWN, VERDICT_TERMINAL, *RETIRED_VERDICTS.values()})
VERDICTS: Final = DAMPED_VERDICTS | {VERDICT_LIVE, VERDICT_ACK, VERDICT_HEAVY}

#: The run kinds the kit's usage line carries (FLEET-KIT v8/v9 `kind`).
KIND_INBOX: Final = "inbox"
KIND_TRIAGE: Final = "triage"

#: The spawn label when no live note is NAMED - every live item sits past the
#: listing cap, so no basename can be given. Authored, never empty, and not in
#: the channel-note shape, so it can never pass for a note's name.
UNLISTED_LABEL: Final = "inbox-unlisted-past-cap"

#: The fire's progress file stem: `ops/loop/control/progress/<stem>.json`
#: (FLEET item 12), written through the kit's `write_progress`, carrying the
#: fire's item-13 checklist (FLEET item 13 d) built by the kit's checklist.
PROGRESS_TASK: Final = "inbox-responder"

#: The checklist row id of the items past the listing cap, which have no name.
MORE_ROW_ID: Final = "MORE"

_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2

#: The kit's own spawn, and its injectable seams by name. The responder passes
#: every key through untouched; production passes none, so every seam is the
#: kit's fail-closed default.
KitSpawn = Callable[..., tuple[dict[str, Any], str]]


def _default_lock() -> Any:
    return winmutex.hold(MUTEX_NAME, timeout=0.0)


@contextlib.contextmanager
def _worker_env() -> Iterator[None]:
    """`WORKER_ENV` in this process's environment for the spawn, then restored."""
    saved = {key: os.environ.get(key) for key in WORKER_ENV}
    os.environ.update(WORKER_ENV)
    try:
        yield None
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def kit_spawn(
    root: Path,
    prompt: str,
    *,
    writes_code: bool,
    effort: str,
    note: str,
    kind: str,
    before_start: Callable[[], None],
    **seams: Any,
) -> tuple[dict[str, Any], str]:
    """Start the worker through the fleet kit and wait. THE DEFAULT REALLY STARTS A PROCESS.

    ``before_start`` runs after the kit has refused or counted the start and
    written its own "running" status, immediately before the process starts, so
    the responder's status is the one the run is shown under.

    Args:
        root: The main tree root - the worker's cwd and the kit's file root.
        prompt: The worker prompt, sent on stdin.
        writes_code: Whether the kit picks the code model.
        effort: The kit effort word.
        note: The run's label in the kit's usage line (`run_label`), never empty.
        kind: The run's kind in the kit's usage line (`run_kind`).
        before_start: Called once, just before the process starts.
        **seams: Passed to ``kit.spawn`` untouched. ``run`` is wrapped, not
            replaced, so the worker's own output can be classified.

    Returns:
        The kit's usage line, and the worker's captured stdout.

    Raises:
        kit.Refused: Before anything starts, when the fleet rules forbid it.
    """
    inner = seams.pop("run", None) or kit._run  # noqa: SLF001 - the kit's own default
    captured: list[str] = []

    def run(argv: list[str], **kw: Any) -> Any:
        before_start()
        proc = inner(argv, **kw)
        out = getattr(proc, "stdout", None)
        captured.append(out if isinstance(out, str) else "")
        return proc

    shape: dict[str, Any]
    if kind == KIND_TRIAGE:
        shape = inbox_kit.triage_spawn_kwargs(FLOORS_IN_HOOKS)
    else:
        shape = {
            "effort": effort,
            "bare": not FLOORS_IN_HOOKS,
            "floors_in_hooks": FLOORS_IN_HOOKS,
            "timeout": WORKER_TIMEOUT_S,
        }
    with _worker_env():
        line = kit.spawn(
            root,
            inbox_status.CODE,
            prompt,
            note=note,
            kind=kind,
            writes_code=writes_code,
            stdin=True,
            cwd=root,
            extra=KIT_EXTRA,
            run=run,
            **shape,
            **seams,
        )
    usage: dict[str, Any] = dict(line) if isinstance(line, dict) else {}
    return usage, captured[-1] if captured else ""


def _replace_with_retry(tmp: Path, target: Path) -> None:
    """``tmp.replace(target)``, retried for a reader holding the target on Windows."""
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            tmp.replace(target)
        except PermissionError:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise
            time.sleep(_RENAME_PAUSE_S)
        else:
            return


def _backoff_until(path: Path) -> float:
    """The epoch second the back-off lifts, or 0 for none or an unreadable file."""
    try:
        parsed = json.loads(path.read_bytes().decode("ascii"))
    except (OSError, ValueError):
        return 0.0
    until = parsed.get("until") if isinstance(parsed, dict) else None
    if isinstance(until, bool) or not isinstance(until, (int, float)):
        return 0.0
    return float(until)


def _write_backoff(path: Path, until: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(json.dumps({"until": until}).encode("ascii") + b"\n")
    _replace_with_retry(tmp, path)


def _log(root: Path, now: float, outcome: str, code: int, **fields: Any) -> None:
    """Append one JSON line. Authored words, counts and durations only. Never raises."""
    record: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "outcome": outcome,
        "exit": code,
    }
    record.update({key: val for key, val in fields.items() if key in LOG_KEYS})
    line = json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n"
    with contextlib.suppress(OSError):
        target = root / LOG_RELPATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("ab") as handle:
            handle.write(line.encode("ascii"))


def _stopped(control: Path) -> bool:
    return any((control / rel).exists() for rel in STOP_RELPATHS)


def _halted_since(control: Path, fallback: float) -> float:
    """When the standing sentinel was placed - its mtime - or ``fallback``."""
    stamps: list[float] = []
    for rel in STOP_RELPATHS:
        with contextlib.suppress(OSError):
            stamps.append((control / rel).stat().st_mtime)
    return min(stamps) if stamps else fallback


def _canonical_sender(name: str) -> str | None:
    """The canonical sender position: the first ``-from-<CODE>-`` after the timestamp."""
    match = _CANONICAL_SENDER_RE.match(name)
    return match.group(1) if match else None


def _kit_sender(name: str) -> str | None:
    """Who a note is FROM, decided by the kit's own `note_sender` on the name, or None.

    The one sender rule the kit applies to every spawn (CS-1272 H2): the first
    ``from-<CODE>-`` anywhere in the basename, ``from`` in any case, the code
    upper-case. Never reimplemented here, so the two cannot part.
    """
    found = kit.note_sender(name)
    return found if isinstance(found, str) else None


def retired_sender(name: str) -> str | None:
    """The retired sibling's code (from `RETIRED_SENDERS`) a note is FROM, or None.

    THE KIT DECIDES (CS-1272 H2, H3): every name the kit attributes to a
    retired sibling is retired, and a name the kit attributes to anyone else is
    THEIRS - an upper-cased reading never overrides it, so a lower-case code
    ahead of MAIN's never drops MAIN's ORDER. The kit reads a sender code
    upper-case only, so ONLY where it attributes the name to nobody at all is
    the name read again upper-cased, and a lower-case retired code is retired
    there. The code returned is the table's own spelling, so nothing the
    sender wrote reaches a log line.
    """
    found = _kit_sender(name)
    if found is None:
        found = _kit_sender(name.upper())
    return next((code for code in sorted(RETIRED_SENDERS) if code == found), None)


def is_damped(name: str) -> bool:
    """Loop damping (MAIN 0845 section 3, kept by 0855): a note that never starts a run.

    Three rules, read from the NAME only - a body scan damps the very orders that
    quote the rule (LL 0958 measured it on MAIN 0845 and 0855):

      1. OUR OWN note: the sender the kit reads (`_kit_sender`, the first
         ``from-<CODE>-`` in the name) is this tree's code - the note the kit's
         own `should_skip` calls "self". A later ``-from-CS-`` quoted inside
         another sender's name is not ours.
      2. A note FROM a retired sibling (`RETIRED_SENDERS`, MAIN 0230 item 4),
         whatever its class - a retired tree's ORDER or FIX buys no run either.
      3. A note marked TERMINAL or no-reply, case-insensitive. MAIN's notes are
         exempt, because an order needs acting on whether or not it wants a
         reply - read from the CANONICAL sender position only, so a departure
         from the kit's damping is never wider than the canonical shape.
    """
    if _kit_sender(name) == inbox_status.CODE or retired_sender(name) is not None:
        return True
    if _canonical_sender(name) == _EXEMPT_SENDER:
        return False
    return _TERMINAL_RE.search(name) is not None


def verdict(name: str) -> str:
    """The `VERDICTS` word for one unread item, decided on its REAL name (CS-1272 H3).

    The surface's judge: it is handed the whole filename the kit reads, never
    the capped display, and answers one closed-vocabulary word - the damping
    rule of `is_damped`, the retired code from the table, and for a live note
    the weight the kit reads (an ORDER, FIX or RULING is heavy; an
    acknowledgement is effort low). Nothing of the name is returned.
    """
    if _kit_sender(name) == inbox_status.CODE:
        return VERDICT_OWN
    retired = retired_sender(name)
    if retired is not None:
        return RETIRED_VERDICTS[retired]
    if is_damped(name):
        return VERDICT_TERMINAL
    if str(kit.note_class(name)) in kit.NEVER_DAMP:
        return VERDICT_HEAVY
    return VERDICT_ACK if kit.pick_effort(name) == "low" else VERDICT_LIVE


def judged_surface(root: Any) -> Mapping[str, Any]:
    """The production surface: the watcher's listing, every unread item judged by `verdict`."""
    return inbox_surface.surface(root, judge=verdict)


def _listed(fact: Mapping[str, Any]) -> list[str]:
    names = fact.get("names")
    return [n for n in names if isinstance(n, str)] if isinstance(names, list) else []


def _words(raw: Any, count: int) -> list[str] | None:
    """``raw`` as ``count`` verdict words, an unknown word read as unseen; else None."""
    if not isinstance(raw, list) or len(raw) != count or not all(isinstance(w, str) for w in raw):
        return None
    return [word if word in VERDICTS else VERDICT_UNSEEN for word in raw]


def _judged(fact: Mapping[str, Any]) -> list[tuple[str, str]]:
    """``(display, verdict)`` per listed item, in the listing's own order.

    The surface's words when it judged the listing. A fact nobody judged - an
    injected one - has its names judged as they stand.
    """
    listed = _listed(fact)
    words = _words(fact.get("verdicts"), len(listed))
    picked = [verdict(name) for name in listed] if words is None else words
    return list(zip(listed, picked, strict=True))


def _past(fact: Mapping[str, Any], unread: int) -> list[str]:
    """One verdict per item past the listing cap. Unjudged, each is `VERDICT_UNSEEN`."""
    count = max(0, unread - len(_listed(fact)))
    words = _words(fact.get("more_verdicts"), count)
    return [VERDICT_UNSEEN] * count if words is None else words


def _retired(fact: Mapping[str, Any], unread: int) -> list[str]:
    """The retired codes, from the table, of every unread item - listed or past the cap."""
    found = {word for _name, word in _judged(fact)} | set(_past(fact, unread))
    return [code for code, word in RETIRED_VERDICTS.items() if word in found]


def _worthy(fact: Mapping[str, Any], unread: int) -> int:
    """Unread items that may start a run, listed or past the cap, each on its verdict."""
    words = [word for _name, word in _judged(fact)] + _past(fact, unread)
    return sum(1 for word in words if word not in DAMPED_VERDICTS)


def _past_live(fact: Mapping[str, Any], unread: int) -> int:
    """The live items past the listing cap, which no row can name."""
    return sum(1 for word in _past(fact, unread) if word not in DAMPED_VERDICTS)


def _kit_inputs(fact: Mapping[str, Any], unread: int) -> tuple[bool, str]:
    """``(writes_code, effort)`` for the kit, from the live notes' verdicts only.

    MAIN 0855: sonnet unless the work writes code, effort low for
    acknowledgements. One pass answers every live note, so the pass takes the
    heaviest: the code model when any live note is an ORDER, FIX or RULING (the
    classes the kit never damps), and effort low only when the kit reads every
    live note as an acknowledgement. A live note past the listing cap is
    unseen by the worker's listing, so it is assumed heavy rather than guessed
    light; a damped one past the cap weighs nothing (CS-1272 H3).
    """
    live = [word for _name, word in _judged(fact) if word not in DAMPED_VERDICTS]
    unseen = _past_live(fact, unread) > 0
    writes_code = unseen or any(word in {VERDICT_HEAVY, VERDICT_UNSEEN} for word in live)
    effort = "low" if live and not unseen and set(live) == {VERDICT_ACK} else "medium"
    return writes_code, effort


def _live(fact: Mapping[str, Any]) -> list[str]:
    """The listed displays that may start a run, in the listing's own order."""
    return [name for name, word in _judged(fact) if word not in DAMPED_VERDICTS]


def run_label(fact: Mapping[str, Any]) -> str:
    """The kit's ``note`` label for a pass: the first live note's basename. Never empty.

    The basename is taken the way the kit takes it (``Path(name).name``). With
    every live item past the listing cap no name is known, so the label is
    `UNLISTED_LABEL`.
    """
    for name in _live(fact):
        base = Path(name).name
        if base.strip():
            return base
    return UNLISTED_LABEL


def run_kind(writes_code: bool, effort: str) -> str:
    """The kit's ``kind`` for a pass: triage on the kit's triage shape, else inbox.

    "triage" exactly when the pass runs on the model and effort the kit's inbox
    module names for a triage look (`triage_spawn_kwargs`: sonnet, effort low) -
    a pass over acknowledgements only. Every other pass, an ORDER, a question
    or an item past the cap, is an ordinary "inbox" run.
    """
    shape = inbox_kit.triage_spawn_kwargs(FLOORS_IN_HOOKS)
    triage = (shape["model"], shape["effort"])
    return KIND_TRIAGE if (kit.pick_model(writes_code), effort) == triage else KIND_INBOX


def checklist_rows(
    fact: Mapping[str, Any], unread: int, state: str, eta_s: int | None = None
) -> list[dict[str, Any]]:
    """The fire's item-13 checklist: one row per live note, then one for the unnamed rest.

    Every row is built by the kit's own `fleet_checklist.item`, so a row the kit
    would refuse is refused here first. A display is capped at the kit's task
    length already; the "Handle " prefix is cut back to fit, never wrapped.
    """
    rows = [
        fleet_checklist.item(
            f"N{index}", f"Handle {Path(name).name}"[: fleet_checklist.TASK_MAX], state, eta_s
        )
        for index, name in enumerate(_live(fact), start=1)
    ]
    past = _past_live(fact, unread)
    if past > 0:
        noun = "item" if past == 1 else "items"
        task = f"Handle {past} unread {noun} past the listing cap"
        rows.append(fleet_checklist.item(MORE_ROW_ID, task, state, eta_s))
    return rows[: fleet_checklist.ROWS_MAX]


class _Progress:
    """The fire's item-12 progress file with its item-13 checklist. Display only; never raises.

    Written only once a worker is about to start: a pass that starts nothing
    leaves no progress file, as a quiet channel leaves no log line. A finished
    fire has no remaining task; a failed one keeps its rows, marked failed.
    """

    def __init__(self, root: Path, rows: Callable[[str, int | None], list[dict[str, Any]]]) -> None:
        self.root = root
        self.rows = rows
        self.fired = False

    def _write(
        self, pct: int, step: str, eta_s: int | None, status: str, rows: list[dict[str, Any]]
    ) -> None:
        with contextlib.suppress(OSError, ValueError):
            kit.write_progress(self.root, PROGRESS_TASK, pct, step, eta_s, status, checklist=rows)

    def running(self, eta_s: int | None) -> None:
        self.fired = True
        with contextlib.suppress(ValueError):
            self._write(0, "Running Session", eta_s, "running", self.rows("running", eta_s))

    def ended(self, outcome: str) -> None:
        if not self.fired:
            return
        if outcome == headless_route.OUTCOME_OK:
            self._write(100, outcome, 0, "done", [])
            return
        with contextlib.suppress(ValueError):
            self._write(0, outcome, 0, "failed", self.rows("failed", None))


class _Board:
    """Publishes `inbox_status` for one pass. Every write is display only and never raises."""

    def __init__(
        self,
        control: Path,
        now: Callable[[], float],
        tick: Callable[[float], float | None],
    ) -> None:
        self.control = control
        self.now = now
        self.tick = tick
        self.clock = inbox_status.TaskClock(control)
        # THE KIT'S BUDGET, read where the kit writes it: one tree-wide count
        # for every headless start, never a second counter beside it.
        self.budget = kit.RunBudget(control / kit.BUDGET_REL.name)
        self._tick: float | None = None
        self._tick_asked = False

    def next_tick(self, at: float) -> float | None:
        """The scheduler's next fire, asked once per pass unless it has passed."""
        if not self._tick_asked or (self._tick is not None and self._tick <= at):
            self._tick_asked = True
            self._tick = self.tick(at)
        return self._tick

    def window(self, at: float) -> inbox_status.Window:
        """The kit's run window. An unreadable budget renders FULL - it refuses every start."""
        self.budget.clock = lambda: at
        count = int(self.budget.used())
        frees = self.budget.frees_at()
        return inbox_status.Window(count=count, frees_at=None if frees is None else float(frees))

    def show(self, state: str, task: str, *, started: float | None = None) -> None:
        at = self.now()
        inbox_status.publish(
            self.control,
            now=at,
            state=state,
            task=task,
            task_started=at if started is None else started,
            eta_s=self.clock.eta(task),
            next_tick=self.next_tick(at),
            window=self.window(at),
        )

    def idle(self) -> None:
        since = self.clock.idle_since()
        if since is None:
            since = self.now()
            self.clock.set_idle_since(since)
        self.show("idle", "Idle", started=since)

    def ended(self, finished: float, seconds: float) -> None:
        self.clock.record("Running Session", seconds)
        self.clock.set_idle_since(finished)

    def refresh(self) -> None:
        at = self.now()
        inbox_status.refresh(
            self.control, now=at, next_tick=self.next_tick(at), window=self.window(at)
        )


def _outcome_exit(outcome: str) -> int:
    return {
        headless_route.OUTCOME_OK: EXIT_OK,
        headless_route.OUTCOME_USAGE_LIMIT: EXIT_USAGE_LIMIT,
    }.get(outcome, EXIT_WORKER_FAILED)


def run_once(
    *,
    root: Path | None = None,
    control_dir: Path | None = None,
    now: Callable[[], float] = time.time,
    surface: Callable[[Any], Mapping[str, Any]] | None = None,
    lock: Callable[[], Any] | None = None,
    spawn: KitSpawn | None = None,
    kit_seams: Mapping[str, Any] | None = None,
    next_tick: Callable[[float], float | None] | None = None,
) -> int:
    """One responder pass. See the module docstring for the order.

    Args:
        root: The main tree root, or None to resolve it from this checkout.
        control_dir: The sentinel directory, or None for ``ops/loop/control``.
        now: The wall clock.
        surface: The channel lister, or None for `judged_surface` - the
            watcher's listing with every unread item judged on its real name.
        lock: A zero-argument context-manager factory, or None for the mutex.
        spawn: The kit spawn, or None for `kit_spawn`.
        kit_seams: Passed to the kit's ``spawn`` untouched - its proxy, probe,
            executable and runner seams. None in production, so every one is
            the kit's fail-closed default.
        next_tick: The scheduler's next fire after an epoch, or None for the
            real query of `inbox_status.TASK_NAME`.

    Returns:
        The process exit code.
    """
    control = CONTROL if control_dir is None else Path(control_dir)
    board = _Board(control, now, inbox_status.query_next_tick if next_tick is None else next_tick)
    if _stopped(control):
        # QUIET in the log, like a quiet channel: a standing sentinel would
        # otherwise write 96 identical lines a day. The STATUS is still
        # published, so the widget shows a halt rather than no signal.
        board.show("halted", "Halted", started=_halted_since(control, now()))
        return EXIT_OK
    main_root = inbox_surface.channel_root() if root is None else Path(root)
    take = _default_lock if lock is None else lock
    try:
        with take():
            return _locked_pass(
                main_root,
                now,
                judged_surface if surface is None else surface,
                kit_spawn if spawn is None else spawn,
                dict(kit_seams or {}),
                board,
            )
    except winmutex.MutexTimeout:
        # The run holding the lock owns the status; only its age is refreshed,
        # so an hours-long session still shows a live signal.
        board.refresh()
        _log(main_root, now(), "lock_held", EXIT_OK)
        return EXIT_OK


def _locked_pass(  # noqa: PLR0911 - one return per recorded outcome
    root: Path,
    now: Callable[[], float],
    surface: Callable[[Any], Mapping[str, Any]],
    spawn: KitSpawn,
    seams: dict[str, Any],
    board: _Board,
) -> int:
    """Everything after the lock is held."""
    checking = now()
    board.show("idle", "Checking Inbox", started=checking)
    fact = surface(root)
    board.clock.record("Checking Inbox", now() - checking)
    unread = fact.get("unread")
    if type(unread) is not int:
        _log(root, now(), "unmeasured", EXIT_UNMEASURED)
        board.show("refused", kit.REFUSED_TASK)
        return EXIT_UNMEASURED
    retired = _retired(fact, unread)
    if retired:
        # THE NAMED SKIP (MAIN 0230 item 4). The retired sibling's notes start
        # nothing; the line names the sibling from the table, never the note.
        reason = "retired sibling " + ",".join(retired)
        _log(root, now(), "retired_skip", EXIT_OK, unread=unread, reason=reason)
    if _worthy(fact, unread) == 0:
        board.idle()
        return EXIT_OK
    started = now()
    held_until = _backoff_until(root / BACKOFF_RELPATH)
    if started < held_until:
        _log(root, started, "backoff", EXIT_OK, unread=unread)
        board.show("backoff", "Backing Off", started=held_until - BACKOFF_S)
        return EXIT_OK
    try:
        prompt = (root / PROMPT_RELPATH).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        _log(root, started, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        board.show("refused", kit.REFUSED_TASK)
        return EXIT_SPAWN_FAILED
    writes_code, effort = _kit_inputs(fact, unread)
    progress = _Progress(root, lambda state, eta: checklist_rows(fact, unread, state, eta))

    def before_start() -> None:
        board.show("running", "Running Session", started=started)
        progress.running(board.clock.eta("Running Session"))

    try:
        line, output = spawn(
            root,
            prompt,
            writes_code=writes_code,
            effort=effort,
            note=run_label(fact),
            kind=run_kind(writes_code, effort),
            before_start=before_start,
            **seams,
        )
    except kit.Refused as refused:
        return _refused(root, board, refused, unread, started)
    except OSError:
        finished = now()
        board.ended(finished, finished - started)
        _log(root, finished, "spawn_failed", EXIT_SPAWN_FAILED, unread=unread)
        progress.ended("spawn_failed")
        board.show("refused", kit.REFUSED_TASK)
        return EXIT_SPAWN_FAILED
    code, outcome = _finished(root, now, board, line, output, unread, started)
    progress.ended(outcome)
    return code


def is_lock_busy(refused: Exception) -> bool:
    """Whether the kit refused because its budget lock stayed busy.

    Matched on the refusal's ARGS, never on a rendering of the exception
    object (CS-205): the kit raises it with the one message word and no cause.
    The kit-words pin in tests/ops/test_inbox_responder.py drives THIS
    predicate against the vendored kit, so the pin and the route cannot part.
    """
    return refused.args == (KIT_LOCK_BUSY,)


def _refused(root: Path, board: _Board, refused: Exception, unread: int, started: float) -> int:
    """The kit refused before anything started. Nothing ran, so no duration is recorded."""
    if isinstance(refused, kit.BudgetUnreadable) or is_lock_busy(refused):
        # FAIL CLOSED: the kit never resets its budget, and nothing starts uncounted.
        _log(root, started, "budget_refused", EXIT_BUDGET_REFUSED, unread=unread)
        board.show("refused", kit.REFUSED_TASK)
        return EXIT_BUDGET_REFUSED
    window = board.window(started)
    if window.count >= board.budget.cap:
        _log(root, started, "limit", EXIT_OK, unread=unread)
        board.show("limit", "Turn Limit Reached")
        return EXIT_OK
    # The proxy, the door or the executable. The kit's words are not logged:
    # the outcome word is the closed vocabulary, and the reason stays authored.
    _log(root, started, "kit_refused", EXIT_ROUTE_REFUSED, unread=unread, reason="kit")
    board.show("refused", kit.REFUSED_TASK)
    return EXIT_ROUTE_REFUSED


def _finished(
    root: Path,
    now: Callable[[], float],
    board: _Board,
    line: Mapping[str, Any],
    output: str,
    unread: int,
    started: float,
) -> tuple[int, str]:
    """Classify the finished run, publish and log it. Returns the exit code and outcome word."""
    finished = now()
    board.ended(finished, finished - started)
    if line.get("error") == "timeout":
        _log(root, finished, "timeout", EXIT_TIMEOUT, unread=unread)
        board.idle()
        return EXIT_TIMEOUT, "timeout"
    rc = line.get("rc")
    returncode = rc if type(rc) is int else None
    outcome = headless_route.classify_exit(returncode, output)
    if outcome == headless_route.OUTCOME_USAGE_LIMIT:
        _write_backoff(root / BACKOFF_RELPATH, finished + BACKOFF_S)
    code = _outcome_exit(outcome)
    _log(
        root,
        finished,
        outcome,
        code,
        unread=unread,
        returncode=returncode,
        duration_s=round(finished - started, 3),
    )
    if outcome == headless_route.OUTCOME_USAGE_LIMIT:
        board.show("backoff", "Backing Off", started=finished)
    else:
        board.idle()
    return code, outcome


def main(argv: Sequence[str] | None = None) -> int:
    """Parse ``--once`` and run one pass."""
    parser = argparse.ArgumentParser(description="CS-1226 one-shot inbox responder")
    parser.add_argument("--once", action="store_true", required=True, help="run one pass")
    parser.parse_args(argv)
    return run_once()


if __name__ == "__main__":
    raise SystemExit(main())
