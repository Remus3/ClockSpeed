#!/usr/bin/env python3
r"""The detached driver's sys.path, which no in-repo test ever has.

WHAT THIS GRADES, AND WHY NOTHING ELSE COULD SEE IT. Every suite in this
repository runs with the repository ROOT on ``sys.path`` - `tests/conftest.py`
and each test module put it there - so ``from ops.loop import lanes`` resolves
for free in every arm ever written. The detached driver has the opposite shape:
``ops/loop/launch_queue_loop.ps1`` starts it as ``pythonw <repo>/ops/loop/queue_loop.py``,
which puts ``ops/loop`` on ``sys.path`` and the repository root NOWHERE. A
module the driver binds by file path then hits its own bare package import and
raises ``ModuleNotFoundError: No module named 'ops'``.

MEASURED, not predicted. One real detached cycle was run to prove the launch
path end to end and never reached a cycle at all::

    File "C:\\Clockspeed\\ops\\loop\\scope.py", line 93, in <module>
        from ops.loop import lanes
    ModuleNotFoundError: No module named 'ops'

The driver died in ``run_loop`` before its first acquire, so no lane lock, no
worker, no JSONL row - a night that produces nothing and explains nothing. This
is the same family as CS-1000 one file over: the launch path's imports are the
one thing a suite run from the repository root structurally cannot grade.

THE ARM SPAWNS A CHILD, because the property IS a ``sys.path`` this process
cannot have. It is FRONTED BY A CONTROL asserting the child really cannot
import ``ops`` - without that leg, "the binds succeeded" is also exactly what a
child with the repository root on its path would print.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
LOOP_DIR: Final = ROOT / "ops" / "loop"

#: Generous, and present only so a wedged arm fails rather than hanging the run.
_CHILD_TIMEOUT_S: Final = 120.0

#: The modules the driver binds through `queue_loop._mod`. Named here rather
#: than discovered, so an arm cannot pass by grading an empty population.
_DRIVER_BINDS: Final = ("lanes", "lane_launcher", "winmutex", "ration", "scope", "claims")

#: A child with the DETACHED driver's path shape and nothing else: `ops/loop`
#: on `sys.path`, the repository root absent. `sys.path[0]` is the script's own
#: directory, which for `pythonw <repo>/ops/loop/queue_loop.py` is `ops/loop` -
#: reproduced here by running the child with that directory as the script dir.
_BIND_PROBE: Final = """
import sys

# THE CONTROL, printed rather than asserted, so the parent grades it.
try:
    import ops  # noqa: F401
    print("OPS_IMPORTABLE")
except ModuleNotFoundError:
    print("OPS_ABSENT")

import queue_loop

for name in {names!r}:
    queue_loop._mod(name)
    print("BOUND " + name)
"""


def _run_probe() -> subprocess.CompletedProcess[str]:
    """Bind every driver module from a child shaped like the detached driver.

    The probe script is written INTO ``ops/loop`` for the length of the call, so
    the interpreter puts that directory on ``sys.path`` as the script's own
    directory - which is exactly how the launcher starts the driver. It is
    removed again whatever happens, because this repository's own control plane
    lives one directory up and a stray file there is the fault this file's
    neighbour guards against.

    Returns:
        The completed child.
    """
    probe = LOOP_DIR / "cs_bind_probe_tmp.py"
    probe.write_text(_BIND_PROBE.format(names=_DRIVER_BINDS), encoding="ascii")
    try:
        return subprocess.run(
            [sys.executable, str(probe)],
            capture_output=True,
            text=True,
            check=False,
            timeout=_CHILD_TIMEOUT_S,
            cwd=str(LOOP_DIR),
        )
    finally:
        probe.unlink(missing_ok=True)


def test_every_module_the_driver_binds_imports_without_the_repository_root() -> None:
    """THE DEFECT, MEASURED ON A REAL DETACHED RUN.

    A module bound by file path must not carry a bare ``from ops.loop import
    ...`` at its top level: the driver reaches it precisely when the package
    route is unavailable, so that line is guaranteed to fail exactly when it
    matters and never to fail in a suite.
    """
    done = _run_probe()
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]

    # THE CONTROL FIRST. If the child could import `ops`, it is not the driver's
    # environment and every bind below proves nothing.
    assert lines, f"the probe printed nothing - stderr was {done.stderr[-600:]!r}"
    assert lines[0] == "OPS_ABSENT", (
        "the child can import `ops`, so it is not the detached driver's sys.path "
        "and this arm grades nothing"
    )

    ran = done.returncode
    assert ran == 0, f"a driver module failed to bind - stderr was {done.stderr[-800:]!r}"

    bound = {line.removeprefix("BOUND ") for line in lines if line.startswith("BOUND ")}
    assert bound == set(_DRIVER_BINDS), "not every module the driver binds was reached"
