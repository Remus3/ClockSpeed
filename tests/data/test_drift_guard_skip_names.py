"""CS-1158 - the drift guard never names a path it pruned for a sensitive reason.

THE ACCEPTANCE, verbatim from the item note: "no path a skip record carries
because it is PII-bearing or credential-bearing reaches a rendered report or the
`--json` payload in a form that names the artifact, and a test plants one of
each declared class and asserts the rendered bytes carry no leaf name, with a
control proving the same run DOES render an ordinary pruned path".

THE RULE IS ADR 0023's, AND IT IS STATED BY REASON CLASS. A skip record whose
reason is in the `PII-bearing` or `credential material` class renders as its
reason and a count - no leaf, no masked leaf, no hash. So the plants below are
DERIVED from the two declared tables by reason class rather than listed, and an
anti-narrowing pin asserts the shapes the item was filed over are among them:
a table that lost `*.sav` would otherwise shrink the plant set and stay green.

WHY EVERY ARM ALSO RENDERS A CONTROL. An implementation that stopped rendering
skip paths at all would satisfy every "the leaf is absent" assertion here. The
control is a fixed name this repository chose itself - ADR 0023 rule 5 - pruned
for a `local-only` reason, and the same run must print it. And the COUNT must
survive, per CONVENTIONS.md section 15.1: a verdict needs the list of what was
never looked at, so each withheld class is asserted present with its count.

Every name planted here is synthetic, carries a `zz` token no real tree has,
and resembles no world name.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from clockspeed.data.locate import ENV_ACCOUNT_DIR, ENV_GAME_DIR, ENV_LOCAL_CONFIG, ENV_SAVE_ROOT

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIFT_GUARD_SOURCE = REPO_ROOT / "tools" / "drift_guard.py"

# ADR 0023 rule 3 - the two classes whose records never name their path. Spelt
# here rather than imported, so a guard whose class set lost a member cannot
# agree with this module by construction.
WITHHELD_CLASSES = ("PII-bearing", "credential material")

# The shapes CS-1158 was filed over. The plant set is derived from the tables;
# this pins that the derivation still reaches every one of them.
FILED_SHAPES = frozenset({"*.sav", "*.log", "*.pem", ".env", ".mcp.json"})

# The control - ADR 0023 rule 5's own examples of a fixed name this repository
# chose itself, pruned for a `local-only` reason.
CONTROL_LOCAL = "zzcontrol.local.json"
CONTROL_LANE = "ops/loop/config.json"

PLANTS_PER_SHAPE = 2


def _load_drift_guard() -> ModuleType:
    """Load tools/drift_guard.py from its file; tools/ is not a package."""
    name = "clockspeed_drift_guard_skip_names"
    spec = importlib.util.spec_from_file_location(name, DRIFT_GUARD_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DRIFT_GUARD_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drift_guard = _load_drift_guard()


def _class_of(reason: str) -> str:
    return reason.split(" - ", 1)[0]


def _withheld_file_patterns() -> dict[str, str]:
    table = drift_guard.WALK_SKIP_FILE_PATTERNS
    return {p: r for p, r in table.items() if _class_of(r) in WITHHELD_CLASSES}


def _withheld_root_paths() -> dict[str, str]:
    table = drift_guard.WALK_SKIP_ROOT_PATHS
    return {p: r for p, r in table.items() if _class_of(r) in WITHHELD_CLASSES}


@dataclass
class Planted:
    """What one planted tree holds, and what must and must not render.

    Attributes:
        tokens: Substrings no rendered byte may carry.
        root_dirs: Fixed withheld root paths, spelt as skip paths.
        counts: Withheld reason to the number of records planted under it.
    """

    tokens: list[str] = field(default_factory=list)
    root_dirs: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def _plant(root: Path) -> Planted:
    """Plant every withheld-class shape, twice where a shape can vary, plus the controls.

    Each file shape lives in its own `zzplantN/` directory beside a kept
    markdown file, so the directory is ENTERED (it is not itself pruned) and
    git, where asked, cannot collapse it into one directory entry. The token
    hunt then covers the directory name and the leaf alike.
    """
    planted = Planted()
    for index, (pattern, reason) in enumerate(sorted(_withheld_file_patterns().items())):
        shape_dir = f"zzplant{index}"
        leaves = (
            [pattern.replace("*", f"zzleaf{index}x{n}") for n in range(PLANTS_PER_SHAPE)]
            if "*" in pattern
            else [pattern]
        )
        for leaf in leaves:
            target = root / shape_dir / leaf
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\x00synthetic\x00")
            if "*" in pattern:
                planted.tokens.append(leaf.split(".")[0])
        (root / shape_dir / "keep.md").write_text("# kept\n", encoding="utf-8")
        planted.tokens.append(shape_dir)
        planted.counts[reason] = planted.counts.get(reason, 0) + len(leaves)
    for relative, reason in sorted(_withheld_root_paths().items()):
        target = root / relative / "zzinner.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("synthetic\n", encoding="utf-8")
        planted.root_dirs.append(relative + "/")
        planted.counts[reason] = planted.counts.get(reason, 0) + 1
    (root / CONTROL_LOCAL).write_text("{}\n", encoding="utf-8")
    lane = root / CONTROL_LANE
    lane.parent.mkdir(parents=True, exist_ok=True)
    lane.write_text("{}\n", encoding="utf-8")
    # A kept sibling, for the reason each plant directory carries one: git
    # collapses a directory whose every entry it ignores into ONE entry.
    (lane.parent / "keep.md").write_text("# kept\n", encoding="utf-8")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    return planted


def _point_at(monkeypatch: pytest.MonkeyPatch, root: Path, tmp_path: Path) -> None:
    """Aim the driver at ``root`` with no install, save root or local config."""
    monkeypatch.setattr(drift_guard, "repo_root", lambda: root)
    for name in (ENV_GAME_DIR, ENV_SAVE_ROOT, ENV_ACCOUNT_DIR, ENV_LOCAL_CONFIG):
        monkeypatch.setenv(name, str(tmp_path / "absent" / name.lower()))


def _floor_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Withhold git entirely, so the static floor alone decides on any runner."""
    monkeypatch.setattr(drift_guard, "_git_ls_files", lambda _root: [])
    monkeypatch.setattr(drift_guard, "_git_ignored", lambda _root: None)
    monkeypatch.setattr(drift_guard, "_registered_worktrees", lambda _root: ())


def _run(capsys: pytest.CaptureFixture[str], *args: str) -> str:
    drift_guard.main(list(args))
    return capsys.readouterr().out


def _assert_nothing_named(text: str, planted: Planted, surface: str) -> None:
    """No planted token and no withheld root path reaches ``text``."""
    # Bound to scalars first: pytest renders an asserted expression whatever
    # the message says, and the list here is exactly what must not be echoed.
    leaked_tokens = sum(1 for token in planted.tokens if token in text)
    assert leaked_tokens == 0, f"{surface} named {leaked_tokens} withheld plant(s)"
    lines = {line.strip() for line in text.splitlines()}
    leaked_roots = sum(1 for path in planted.root_dirs if path in lines or f'"{path}"' in text)
    assert leaked_roots == 0, f"{surface} named {leaked_roots} withheld root path(s)"


def test_the_plant_set_reaches_every_shape_the_item_was_filed_over() -> None:
    """Anti-narrowing: the derived plant set is not allowed to shrink silently."""
    derived = set(_withheld_file_patterns())
    missing = sorted(FILED_SHAPES - derived)
    assert not missing, f"a filed shape left the withheld classes: {missing}"
    classes = {_class_of(r) for r in _withheld_file_patterns().values()}
    assert classes == set(WITHHELD_CLASSES), classes
    assert _withheld_root_paths(), "no withheld-class root path is declared at all"


def test_the_text_report_withholds_every_sensitive_name_and_renders_the_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "tree"
    planted = _plant(root)
    _point_at(monkeypatch, root, tmp_path)
    _floor_only(monkeypatch)

    text = _run(capsys)

    _assert_nothing_named(text, planted, "the text report")
    # The control, from the SAME run: an ordinary pruned path still renders.
    assert f"      {CONTROL_LOCAL}" in text.splitlines(), "the local-only control vanished"
    assert f"      {CONTROL_LANE}" in text.splitlines(), "the lane-config control vanished"
    # The count survives, per withheld reason, and the total counts them too.
    for reason, count in planted.counts.items():
        assert f"  {reason}  ({count})" in text.splitlines(), f"lost the count for {reason!r}"
    total = sum(planted.counts.values()) + 2
    summary = [line for line in text.splitlines() if "skipped paths:" in line]
    assert len(summary) == 1, summary
    assert int(summary[0].rsplit(":", 1)[1]) >= total, summary[0]


def test_the_json_payload_withholds_every_sensitive_name_and_keeps_the_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "tree"
    planted = _plant(root)
    _point_at(monkeypatch, root, tmp_path)
    _floor_only(monkeypatch)

    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    _assert_nothing_named(raw, planted, "the --json payload")
    shown = {skip["path"] for skip in report["skipped"]}
    assert CONTROL_LOCAL in shown, "the local-only control vanished from --json"
    assert CONTROL_LANE in shown, "the lane-config control vanished from --json"
    withheld = {entry["reason"]: entry["count"] for entry in report["withheld"]}
    assert withheld == planted.counts, withheld
    assert all(set(entry) == {"reason", "count"} for entry in report["withheld"]), (
        "a withheld entry carries a field beyond its reason and count"
    )


def test_the_same_holds_where_git_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Git naming a path must not flatten its class into the generic reason.

    Where git answers, `_skip_file_reason` looks the path up in the floor first
    so the specific class survives. If that order ever flipped, every sensitive
    record would carry the classless gitignored reason and render its name - so
    the withholding is graded here with git answering, not only with it absent.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns
    from tests.git_env import relocates  # noqa: PLC0415

    for key in [key for key in os.environ if relocates(key)]:
        monkeypatch.delenv(key, raising=False)
    root = tmp_path / "tree"
    planted = _plant(root)
    ignore = [*_withheld_file_patterns(), *(f"/{p}/" for p in _withheld_root_paths())]
    ignore += ["*.local.json", f"/{CONTROL_LANE}", "zzhoard.txt"]
    (root / ".gitignore").write_text("\n".join(ignore) + "\n", encoding="utf-8")
    (root / "zzhoard.txt").write_text("git alone names this\n", encoding="utf-8")
    proc = conftest.run_git(root, "init", "--quiet")
    if proc is None:
        pytest.skip("git is not installed, so its answer cannot be asked")
    assert proc.returncode == 0, f"control: git init exited {proc.returncode}"
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    assert report["enumeration"].startswith("directory walk"), report["enumeration"]
    _assert_nothing_named(text, planted, "the text report")
    _assert_nothing_named(raw, planted, "the --json payload")
    shown = {skip["path"] for skip in report["skipped"]}
    assert {CONTROL_LOCAL, CONTROL_LANE, "zzhoard.txt"} <= shown, sorted(shown)
    withheld = {entry["reason"]: entry["count"] for entry in report["withheld"]}
    assert withheld == planted.counts, withheld
