"""Kit v25 (LANE-CAP) guard: this tree's lane cap follows the machine config.

MAIN's v25 ORDER (2026-10-27 21:36) section 5 item 4. The kit reads the lane
cap ceiling and the governor width from the machine config; this tree's lane
driver must FOLLOW it, so no hard-coded width of 3 may be left in
``ops/loop/lanes.py``. With ``FLEET_LANES_CONFIG`` naming a file of width 5 and
cap 5 the driver's cap and slot count read 5; with the file missing they read
the kit's defaults, 3 and 3. And FAIR RELEASE is advisory: when
``should_yield`` answers True the driver ends the night BETWEEN cycles and
never calls kill or terminate on a worker.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.loop import lanes, queue_loop  # noqa: E402

from tests.test_queue_loop import FakeClock, FakeSingleton, _no_night, loop_seams  # noqa: E402

#: The kit's own defaults, which a missing machine config must reproduce.
KIT_DEFAULT: Final = 3
#: The width and cap the ORDER's guard names.
WIDER: Final = 5


def _caps() -> tuple[int, int]:
    """The driver's live (cap, slot count) - two scalars, read the way it reads them."""
    return lanes.lane_cap(), lanes.max_slots()


def test_kit_v25_the_driver_cap_and_slot_count_follow_the_machine_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Width 5 / cap 5 in the named config reads 5 and 5; a missing file reads 3 and 3."""
    config = tmp_path / "lanes.json"
    config.write_text(
        json.dumps({"governor_width": WIDER, "lane_cap_max": WIDER}), encoding="ascii"
    )
    monkeypatch.setenv("FLEET_LANES_CONFIG", str(config))
    wide = _caps()
    # The widened slot count is USED, not only reported: the last index exists.
    last = lanes.lane_worktree(WIDER - 1).name
    config.unlink()
    missing = _caps()
    assert (wide, last, missing) == (
        (WIDER, WIDER),
        f"lane-{WIDER - 1}",
        (KIT_DEFAULT, KIT_DEFAULT),
    ), f"config-driven caps {wide} / {missing}"


def test_kit_v25_no_hard_coded_width_is_left_in_the_lane_module() -> None:
    """No module-level cap or slot-count constant is assigned a number in lanes.py."""
    tree = ast.parse((ROOT / "ops" / "loop" / "lanes.py").read_text(encoding="ascii"))
    pinned = []
    for node in tree.body:
        targets: list[str] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets, value = [node.target.id], node.value
        for name in targets:
            constant = isinstance(value, ast.Constant) and value.value is not None
            if re.search(r"CAP|SLOTS|WIDTH", name) and constant:
                pinned.append(name)
    assert pinned == [], f"hard-coded widths left: {pinned}"


def test_kit_v25_should_yield_ends_the_night_between_cycles_and_kills_nothing(
    tmp_path: Path,
) -> None:
    """should_yield True after cycle 1: cycle 2 never starts, no kill is ever called."""
    clock = FakeClock()
    killed: list[int] = []
    launched: list[int] = []
    asked: list[int] = []

    def launch(_lane, **_kw):
        launched.append(1)
        return {"pid": 4242, "log": "l"}

    def fair_yield() -> bool:
        asked.append(1)
        return True

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=3,
            launch=launch,
            kill=killed.append,
            control_dir=tmp_path / "control",
            fair_yield=fair_yield,
        )
    )
    verdict = (summary["stopped_by"], len(summary["records"]), len(launched), len(asked), killed)
    assert verdict == (queue_loop.FAIR_YIELD_STOP, 1, 1, 1, []), f"night {verdict}"
    assert queue_loop.FAIR_YIELD_STOP in queue_loop._SUCCESS_STOPS  # noqa: SLF001


def _called_names(nodes: list[ast.AST]) -> set[str]:
    """Every function or method name called anywhere under ``nodes``."""
    names = set()
    for node in nodes:
        for call in ast.walk(node):
            if isinstance(call, ast.Call):
                func = call.func
                if isinstance(func, ast.Attribute):
                    names.add(func.attr)
                elif isinstance(func, ast.Name):
                    names.add(func.id)
    return names


def test_kit_v25_the_yield_path_calls_no_kill_or_terminate() -> None:
    """Structural: the reader and the run_loop branch it feeds CALL no kill or terminate."""
    tree = ast.parse((ROOT / "ops" / "loop" / "queue_loop.py").read_text(encoding="ascii"))
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    branches = [
        node
        for node in ast.walk(funcs["run_loop"])
        if isinstance(node, ast.If) and "fair_yield" in _called_names([node.test])
    ]
    called = _called_names([funcs["kit_should_yield"], *branches])
    named = sorted(n for n in called if "kill" in n.lower() or "terminate" in n.lower())
    assert (len(branches), named) == (1, []), f"yield branches {len(branches)}, calls {named}"


def test_kit_v25_the_cli_binds_the_kits_should_yield(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production reads the REAL governor: `main` hands the night `kit_should_yield`."""
    called = _no_night(monkeypatch)
    queue_loop.main(["--once"], singleton=FakeSingleton())
    bound = called[0].get("fair_yield") if called else None
    assert bound is queue_loop.kit_should_yield, "the night was not handed the kit's reader"


def test_kit_v25_an_admission_refusal_is_retried_like_lanes_full(tmp_path: Path) -> None:
    """A refusal of "admission" is the lanes_full outcome, retried, with its own detail."""
    clock = FakeClock()
    asked: list[int] = []

    def acquire(_lane, **_kw):
        asked.append(1)
        return {"ok": False, "refused": "admission", "holders": []}

    summary = queue_loop.run_loop(
        **loop_seams(
            clock,
            max_cycles=1,
            acquire=acquire,
            acquire_retries=3,
            control_dir=tmp_path / "control",
        )
    )
    row = summary["records"][0]
    verdict = (row["outcome"], len(asked), "admission gate" in row["detail"])
    assert verdict == (queue_loop.OUTCOME_LANES_FULL, 3, True), f"row {verdict}"


def test_kit_v25_the_lane_acquire_refuses_below_the_ram_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The tree's own acquire applies the kit's admission gate and writes no lock."""
    config = tmp_path / "lanes.json"
    config.write_text(json.dumps({"ram_floor_mb": 4096}), encoding="ascii")
    monkeypatch.setenv("FLEET_LANES_CONFIG", str(config))
    root = tmp_path / "locks"
    tree = tmp_path / "tree"
    tree.mkdir()
    claim = lanes.try_acquire_lane(
        lanes.LANES[0],
        run_id="r1",
        worktree=tree,
        root=root,
        admit=lambda: {"free_ram_mb": 100.0, "cpu_pct": 1.0},
    )
    written = sorted(p.name for p in root.glob("*.lock")) if root.exists() else []
    assert (claim.get("ok"), claim.get("refused"), written) == (False, "admission", [])
