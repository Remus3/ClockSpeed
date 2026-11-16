"""CS-1390 - warn the day the installed game build differs from the pin.

THE DEFECT. Guard (h) of `tools/drift_guard.py` refused every push from the
2026-11-08 game patch to the 2026-11-12 re-pin, so landing product work was
blocked for four days with nothing saying why until a push was tried. The
guard fires only at push. This tool fires from the inbox responder's
fifteen-minute tick instead, so the day the installed build and the pin part
company, the hand-off the next session reads first carries one line naming the
re-pin command.

WHAT IT WRITES. One marker-prefixed line in the hand-off file, and only when
the installed build is READABLE, the tree is PINNED and the two DIFFER. A
matching build, an unreadable one, an unpinned tree and an absent hand-off each
write nothing - a check that could not look is never read as a clean result,
and is never turned into a false alarm either. The write is idempotent: a line
already carrying the same two builds is left as it is (so a second run, the
same day or a later one, changes no byte), and a line carrying a different
pair is REPLACED, never joined by a second.

WHAT IT READS. The installed build comes through `scripts/verify_env.py`'s
`read_build_string`, the reader guard (h) already uses - there is no second
reader. The pin is `clockspeed.data.version.GAME_BUILD`. The re-pin command is
the pin module's public `version.REGENERATE_COMMAND`. Nothing
under the game install or the save directory is written, and no path is printed.

NEVER FATAL. `run` swallows every fault and returns an outcome word, because the
caller is a scheduled responder tick that must not fail on a stale pin.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import os
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
for _dir in (_REPO_ROOT, _TOOLS_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

#: The hand-off file, relative to the tree root.
HANDOFF_NAME: Final = "CS-NEXT-SESSION.txt"

#: Every line this tool writes starts with this, and nothing else may.
MARKER: Final = "BUILD PIN DRIFT:"

_JOINER: Final = " installed game build "
#: A /done marker pins the hand-off only while it is younger than this.
_MARKER_FRESH_S: Final = 1800.0
_MARKER_AT_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"
_RENAME_ATTEMPTS: Final = 5
_RENAME_PAUSE_S: Final = 0.2
_PRINTABLE: Final = frozenset(range(0x20, 0x7F))


def repin_command() -> str:
    """The re-pin command - the pin module's public one, never a second literal."""
    from clockspeed.data import version  # noqa: PLC0415 - loaded on use

    command: str = version.REGENERATE_COMMAND
    return command


def installed_build() -> str | None:
    """The installed game build, or None when it cannot be read.

    Read through `verify_env.read_build_string`, the reader guard (h) uses, from
    the install `locate.resolve_game_dir` finds. Any fault - no install, an
    unreadable one, an unimportable reader - is None, never an exception.
    """
    try:
        from clockspeed.data import locate  # noqa: PLC0415

        game_dir, _how = locate.resolve_game_dir()
        if game_dir is None:
            return None
        scripts = str(_REPO_ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        verify_env = importlib.import_module("verify_env")
        build, _source = verify_env.read_build_string(game_dir)
    except Exception:  # DELIBERATE: a probe that cannot look reports unknown, never a fault
        return None
    return str(build) if build else None


def repin_line(installed: str | None, pinned: str, command: str, today: str) -> str | None:
    """The one line to write, or None when there is nothing to say.

    None for an unreadable build, an unpinned tree, matching builds, and a build
    string that is not plain printable ASCII (it would otherwise carry a
    newline or a non-ASCII byte into the hand-off).
    """
    build = (installed or "").strip()
    pin = (pinned or "").strip()
    if not build or not pin or build == pin:
        return None
    if not all(ord(ch) in _PRINTABLE for ch in build + pin):
        return None
    return f"{MARKER} {today}{_JOINER}{build} differs from the pin {pin} - re-pin with: {command}"


def _same_pair(old: str, new: str) -> bool:
    """Whether two marker lines state the same builds, whatever day each was written."""
    return old.split(_JOINER, 1)[-1] == new.split(_JOINER, 1)[-1]


def _replace_with_retry(tmp: Path, target: Path) -> None:
    for attempt in range(_RENAME_ATTEMPTS):
        try:
            tmp.replace(target)
        except PermissionError:
            if attempt == _RENAME_ATTEMPTS - 1:
                raise
            time.sleep(_RENAME_PAUSE_S)
        else:
            return


def default_claimed() -> Callable[[list[str]], list[object]]:
    """The kit's claim probe: `fleet_claims.foreign_claims`, loaded on use, never copied."""
    from ops.fleet_kit import fleet_claims  # noqa: PLC0415

    probe: Callable[[list[str]], list[object]] = fleet_claims.foreign_claims
    return probe


def _held_by_claim(claimed: Callable[[list[str]], list[object]], path: Path) -> bool:
    """True when another live agent claims `path`, or the probe cannot say."""
    try:
        return bool(claimed([str(path.resolve())]))
    except Exception:  # DELIBERATE: a probe that cannot look is a hold, never a write
        return True


def _marker_age_s(doc: dict[str, object], now: float) -> float | None:
    """Seconds since the marker's `at` (UTC, `%Y-%m-%dT%H:%M:%SZ`), or None if unreadable."""
    at = doc.get("at")
    if not isinstance(at, str):
        return None
    try:
        stamp = datetime.strptime(at, _MARKER_AT_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None
    return now - stamp.timestamp()


def _done_marker_pins(path: Path, raw: bytes, now: float) -> bool:
    """True when a FRESH valid /done marker hashes THIS hand-off, so a write would void it.

    `fleet_done.validate` compares the on-disk hand-off sha256 with the marker's,
    so a write right after /done reads as work after /done and silences the Stop
    hook. The pin holds only while the marker is done, names this hand-off, hashes
    these exact bytes and is under `_MARKER_FRESH_S` old: a marker left behind by
    a finished session must not mute the warning for good. An unreadable marker,
    a missing or unparseable `at`, and a future-dated one pin nothing.
    """
    try:
        import hashlib  # noqa: PLC0415

        from ops.fleet_kit import fleet_done  # noqa: PLC0415

        doc = fleet_done.read_marker(path.parent)
        if not doc or doc.get("status") != "done" or doc.get("handoff") != path.name:
            return False
        if doc.get("handoff_sha256") != hashlib.sha256(raw).hexdigest():
            return False
        age = _marker_age_s(doc, now)
        return age is not None and 0 <= age < _MARKER_FRESH_S
    except Exception:  # DELIBERATE: a marker that cannot be read pins nothing
        return False


def upsert(
    path: Path,
    line: str,
    *,
    claimed: Callable[[list[str]], list[object]] | None = None,
    now: Callable[[], float] = time.time,
) -> str:
    """Put `line` in the hand-off as its one marker line. Returns the outcome word.

    The hand-off is tracked and shared, so this read-modify-write yields rather
    than races: probe the claims, read, build, probe again, re-read and compare,
    then rename. A live claim or a probe fault is `held`, a changed byte between
    the read and the rename is `raced`, a valid /done marker over these bytes is
    `held`; each writes nothing and the next tick retries. `unchanged` when the
    same two builds are already there, `written` otherwise. Temp-then-rename.
    """
    probe = default_claimed() if claimed is None else claimed
    if _held_by_claim(probe, path):
        return "held"
    before = path.read_bytes()
    kept: list[str] = []
    olds: list[str] = []
    for existing in before.decode("ascii").splitlines():
        (olds if existing.startswith(MARKER) else kept).append(existing)
    if len(olds) == 1 and _same_pair(olds[0], line):
        return "unchanged"
    if _done_marker_pins(path, before, now()):
        return "held"
    body = "\n".join(kept)
    text = (body + "\n" if body else "") + line + "\n"
    if _held_by_claim(probe, path):
        return "held"
    if path.read_bytes() != before:
        return "raced"
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(text.encode("ascii"))
        _replace_with_retry(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()
    return "written"


def check(
    handoff: Path,
    *,
    installed: Callable[[], str | None],
    pinned: str,
    command: str,
    today: str,
    claimed: Callable[[list[str]], list[object]] | None = None,
    now: Callable[[], float] = time.time,
) -> str:
    """Compare the installed build with the pin and record a difference. Returns the outcome.

    Outcomes: `written`, `unchanged` (the line is already there), `held` (a live
    claim, a probe fault or a valid /done marker), `raced` (another writer got
    there first), `match`, `unpinned`, `unreadable`, `no_handoff`. Only `written`
    changes a byte.
    """
    if not pinned.strip():
        return "unpinned"
    try:
        build = installed()
    except Exception:  # DELIBERATE: a reader fault is an unknown build, never a failure
        build = None
    if not build or not build.strip():
        return "unreadable"
    if build.strip() == pinned.strip():
        return "match"
    line = repin_line(build, pinned, command, today)
    if line is None:
        return "unreadable"
    if not handoff.is_file():
        return "no_handoff"
    return upsert(handoff, line, claimed=claimed, now=now)


def run(handoff: Path | None = None) -> str:
    """The real check against the live install and pin. NEVER raises, never prints."""
    try:
        from clockspeed.data import version  # noqa: PLC0415

        target = _REPO_ROOT / HANDOFF_NAME if handoff is None else Path(handoff)
        return check(
            target,
            installed=installed_build,
            pinned=version.GAME_BUILD,
            command=repin_command(),
            today=datetime.now().astimezone().strftime("%Y-%m-%d"),
        )
    except Exception:  # DELIBERATE: the caller is a scheduled tick that must never fail on this
        return "error"


def main(argv: list[str] | None = None) -> int:
    """`--once`: run the check; print the outcome word only; always exit 0."""
    parser = argparse.ArgumentParser(description="CS-1390 build-pin watch")
    parser.add_argument("--once", action="store_true", required=True, help="run the check once")
    parser.parse_args(argv)
    sys.stdout.write(run() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
