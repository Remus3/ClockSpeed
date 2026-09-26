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
import subprocess
import sys
from collections.abc import Callable
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
# Repair 3 adds the credential shapes an adjudicator ruled inside the clause:
# `.gitignore` files them under LOCAL-ONLY, but their CONTENT is key material.
FILED_SHAPES = frozenset(
    {"*.sav", "*.log", "*.pem", ".env", ".mcp.json", "*.key", "*.pfx", "*.p12", ".env.*"}
)

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
        for n, leaf in enumerate(leaves):
            target = root / shape_dir / leaf
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\x00synthetic\x00")
            if "*" in pattern:
                # The token itself, never a split of the leaf: `.env.*` has
                # an empty first segment, which every text contains.
                planted.tokens.append(f"zzleaf{index}x{n}")
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


# ---------------------------------------------------------------------------
# The adversary's two leak paths - the repair, ADR 0023 rules 1 and 2
# ---------------------------------------------------------------------------
#
# 1. `.gitignore` files `*.sav.bak` and `*.savbackup` under its PII-BEARING
#    section, and git on this platform folds case, so `*.SAV` too. The static
#    floor carried `*.sav` alone and matched case-sensitively, so all three fell
#    to the classless gitignored reason - or, with git unreachable, were walked
#    and named by a reader's own skip record - and printed their names.
# 2. A directory git collapses to ONE ignored entry, because everything in it
#    is ignored, printed its own name. An account-id-shaped name is personal
#    data under rule 1, and a directory holding a withheld-class file locates
#    one.

# The PII-BEARING shapes this arm plants, beyond the floor's own `*.sav`. Their
# presence in the real `.gitignore` section is pinned by the arm below, so the
# plants cannot drift from the file that classifies them.
SECTION_SHAPES = ("*.sav.bak", "*.savbackup")


def _gitignore_sections() -> dict[str, list[str]]:
    """The real `.gitignore` as banner class -> patterns, read independently.

    A banner is a `# ====` rule followed by a `# CLASS - title` line. Written
    here rather than imported so the guard's parser and this one cannot agree
    by construction.
    """
    sections: dict[str, list[str]] = {}
    current = ""
    lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# ====") and index + 1 < len(lines):
            head = lines[index + 1]
            if head.startswith("# ") and " - " in head:
                current = head[2:].split(" - ", 1)[0].strip()
            continue
        if line.strip() and not line.startswith("#"):
            sections.setdefault(current, []).append(line.strip())
    return sections


def _real_gitignore_repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> bool:
    """A real git repository at ``root`` carrying the REAL `.gitignore`.

    core.ignorecase is set TRUE explicitly, so git folds case the way it does
    on this platform on every runner, and the arm is not a statement about the
    host. Returns False when git is not installed.
    """
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns
    from tests.git_env import relocates  # noqa: PLC0415

    for key in [key for key in os.environ if relocates(key)]:
        monkeypatch.delenv(key, raising=False)
    root.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    for args in (("init", "--quiet"), ("config", "core.ignorecase", "true")):
        proc = conftest.run_git(root, *args)
        if proc is None:
            return False
        assert proc.returncode == 0, f"control: git {args[0]} exited {proc.returncode}"
    return True


def test_the_section_shapes_are_filed_under_pii_bearing() -> None:
    """Anti-drift: the shapes planted below are the real file's PII shapes."""
    pii = _gitignore_sections().get("PII-BEARING", [])
    missing = [shape for shape in (*SECTION_SHAPES, "*.sav") if shape not in pii]
    assert not missing, f"no longer under PII-BEARING in .gitignore: {missing}"


def test_every_root_path_gitignore_files_as_pii_carries_a_withheld_reason() -> None:
    """The two classifications of a pruned ROOT may not disagree.

    `.gitignore` is where a pattern's class is declared; WALK_SKIP_ROOT_PATHS
    restates a reason for each root it prunes. A root the file puts under
    PII-BEARING and the table calls `local-only` renders its name under a class
    the source of truth denies it. Measured: `captures` and `screenshots`.
    """
    pii = {p.strip("/") for p in _gitignore_sections().get("PII-BEARING", []) if p.startswith("/")}
    assert pii, "control: no anchored root under PII-BEARING at all"
    table = drift_guard.WALK_SKIP_ROOT_PATHS
    wrong = sorted(r for r in pii if r in table and _class_of(table[r]) not in WITHHELD_CLASSES)
    assert not wrong, f"roots .gitignore files as PII that the table does not withhold: {wrong}"


def _plant_section_shapes(root: Path) -> list[str]:
    """Plant each section shape plus an upper-cased save; return the tokens."""
    tokens: list[str] = []
    (root / "zzsec").mkdir(parents=True, exist_ok=True)
    (root / "zzsec" / "keep.md").write_text("# kept\n", encoding="utf-8")
    leaves = [shape.replace("*", f"zzsec{n}x") for n, shape in enumerate(SECTION_SHAPES)]
    # Upper case of a SECTION-only shape, never of `*.sav`: the file floor folds
    # case too since repair 3, so an upper `.SAV` would grade the floor, not
    # the section's own folding.
    leaves.append("ZZSECUPPER.SAVBACKUP")
    for leaf in leaves:
        (root / "zzsec" / leaf).write_bytes(b"\x00synthetic\x00")
        tokens.append(leaf.split(".")[0].lower())
    (root / CONTROL_LOCAL).write_text("{}\n", encoding="utf-8")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    return tokens


def _leaks(text: str, tokens: list[str]) -> int:
    folded = text.lower()
    return sum(1 for token in tokens if token in folded)


def test_a_section_shape_is_withheld_with_git_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    tokens = _plant_section_shapes(root)
    # Rule 2 with git unreachable: nothing prunes this directory, so it is
    # walked and a READER's skip record ("not an authored text file type")
    # carries the path. The account-id-shaped component must not render.
    digits = "8" * drift_guard.account_id_min_digits()
    (root / digits).mkdir()
    (root / digits / "Thumbs.db").write_bytes(b"\x00synthetic\x00")
    tokens.append(digits)
    _point_at(monkeypatch, root, tmp_path)
    _floor_only(monkeypatch)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    leaked = _leaks(text, tokens) + _leaks(raw, tokens)
    assert leaked == 0, f"{leaked} section-shape name(s) rendered with git unreachable"
    assert CONTROL_LOCAL in {skip["path"] for skip in report["skipped"]}, "control vanished"
    assert sum(entry["count"] for entry in report["withheld"]) >= len(tokens), report["withheld"]


def test_a_section_shape_is_withheld_where_git_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    tokens = _plant_section_shapes(root)
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    assert report["enumeration"].startswith("directory walk"), report["enumeration"]
    leaked = _leaks(text, tokens) + _leaks(raw, tokens)
    assert leaked == 0, f"{leaked} section-shape name(s) rendered with git answering"
    assert CONTROL_LOCAL in {skip["path"] for skip in report["skipped"]}, "control vanished"
    assert sum(entry["count"] for entry in report["withheld"]) >= len(tokens), report["withheld"]


def test_a_collapsed_directory_is_withheld_by_shape_or_by_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rule 1 and rule 3 for the entry git collapses a whole directory into.

    Three collapsed directories must not render: one named like an account id
    holding only an ignored non-sensitive file (the NAME decides), one with an
    ordinary name holding only a save (the CONTENT decides), and one holding a
    save only two levels down (the content search is not one level deep). Two
    must: an ordinary name over ordinary content, and a digit run too short to
    be an account id - the controls that keep both halves from being a blanket
    withhold of every collapsed entry.
    """
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    digits = "9" * drift_guard.account_id_min_digits()
    short = "9" * (drift_guard.account_id_min_digits() - 1)
    plants = {
        f"{digits}/Thumbs.db": False,
        "zzcoll/zzinner.sav": False,
        "zzdeep/zzmid/zzlow.sav": False,
        # A SECTION-only shape, which the floor does not carry: the content
        # search must ask `.gitignore`'s PII-BEARING section too.
        "zzbakcoll/zzbak.sav.bak": False,
        "zzplain/Thumbs.db": True,
        f"{short}/Thumbs.db": True,
    }
    for relative in plants:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"\x00synthetic\x00")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    lines = {line.strip() for line in text.splitlines()}
    shown = {skip["path"] for skip in report["skipped"]}
    tops = {relative.split("/", 1)[0] + "/": renders for relative, renders in plants.items()}
    # Proof git collapsed them: each directory appears as ONE entry somewhere.
    assert {top for top, renders in tops.items() if renders} <= shown, sorted(shown)
    assert {top for top, renders in tops.items() if renders} <= lines, "a control did not render"
    hidden = [top for top, renders in tops.items() if not renders]
    leaked = sum(1 for top in hidden if top in lines or top in shown or top.rstrip("/") in raw)
    assert leaked == 0, f"{leaked} collapsed directory name(s) rendered"
    assert sum(entry["count"] for entry in report["withheld"]) >= len(hidden), report["withheld"]


# ---------------------------------------------------------------------------
# Repair 3 - every withheld class, in upper case, in every enumeration mode
# ---------------------------------------------------------------------------
#
# An adjudicator measured `ZQ.LOG` and `ZQ.PEM` printing by name with and
# without git after repair 2 folded case for the `.gitignore` PII section alone:
# the floor's own withheld shapes still matched case-sensitively. Every class
# is planted here in upper case, each in its own directory beside a kept file,
# so the directory token is in every path that could render.


def _plant_upper(root: Path) -> list[str]:
    tokens: list[str] = []
    for index, pattern in enumerate(sorted(_withheld_file_patterns())):
        shape_dir = f"zzupper{index}"
        leaf = pattern.replace("*", f"zzup{index}").upper()
        (root / shape_dir).mkdir(parents=True)
        # Clean ASCII on purpose. Under `git-keeps-case` a text-typed shape
        # (`.MCP.JSON`) is an authored file by git's answer and guard (c) READS
        # it; a violation there reaches that GUARD's detail, a different
        # renderer from the skip list this arm grades - CS-1195's arms below.
        (root / shape_dir / leaf).write_bytes(b"synthetic\n")
        (root / shape_dir / "keep.md").write_text("# kept\n", encoding="utf-8")
        tokens.append(shape_dir)
    (root / CONTROL_LOCAL).write_text("{}\n", encoding="utf-8")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    return tokens


@pytest.mark.parametrize("mode", ["no-git", "git-folds-case", "git-keeps-case"])
def test_every_withheld_class_is_withheld_in_upper_case(
    mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One upper-case plant per withheld floor shape, in all three modes.

    `git-keeps-case` is the Linux runner's setting: git does NOT ignore the
    upper-case shape, git decides, and the file is WALKED - so a reader's own
    skip record ("not an authored text file type") carries the path, and only
    the render seam stands between it and the report.
    """
    root = tmp_path / "tree"
    if mode == "no-git":
        root.mkdir()
        _floor_only(monkeypatch)
    else:
        if not _real_gitignore_repo(root, monkeypatch):
            pytest.skip("git is not installed, so its answer cannot be asked")
        if mode == "git-keeps-case":
            from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

            proc = conftest.run_git(root, "config", "core.ignorecase", "false")
            assert proc is not None
            assert proc.returncode == 0, "control: core.ignorecase false did not set"
    tokens = _plant_upper(root)
    assert len(tokens) >= len(FILED_SHAPES), "control: fewer upper-case plants than shapes"
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    leaked = _leaks(text, tokens) + _leaks(raw, tokens)
    assert leaked == 0, f"{leaked} upper-case withheld-class name(s) rendered in mode {mode}"
    assert CONTROL_LOCAL in {skip["path"] for skip in report["skipped"]}, "control vanished"


def test_every_withheld_root_is_withheld_in_upper_case_with_git_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The ROOT table folds by the same rule as the file floor.

    An upper-cased withheld root that the walk ENTERED hands its files to the
    readers, and a non-text file there comes back as a reader's own skip record
    carrying the path. The plant inside each root is a non-text shape of no
    withheld class, so only the root's own classification can withhold it.
    """
    root = tmp_path / "tree"
    root.mkdir()
    _floor_only(monkeypatch)
    tokens: list[str] = []
    for index, relative in enumerate(sorted(_withheld_root_paths())):
        token = f"zzrootup{index}"
        target = root / relative.upper() / f"{token}.bin"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"synthetic\n")
        tokens.append(token)
    assert tokens, "control: no withheld root to plant"
    (root / CONTROL_LOCAL).write_text("{}\n", encoding="utf-8")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    leaked = _leaks(text, tokens) + _leaks(raw, tokens)
    assert leaked == 0, f"{leaked} name(s) under an upper-cased withheld root rendered"
    assert CONTROL_LOCAL in {skip["path"] for skip in report["skipped"]}, "control vanished"


def test_a_section_shape_is_withheld_where_git_keeps_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Repair 4 - git's case handling must not decide what is withheld.

    With core.ignorecase false, as on the Linux runner, git's own match is
    case-sensitive: an upper-cased `*.sav.bak` or `*.savbackup` is NOT ignored,
    git decides, and the file is walked - so a reader's own skip record carries
    the path. An adjudicator measured both printing. The render seam must ask
    the tool's own case-folded classification, including the `.gitignore`
    section's, whatever reason the record carries.
    """
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    proc = conftest.run_git(root, "config", "core.ignorecase", "false")
    assert proc is not None
    assert proc.returncode == 0, "control: core.ignorecase false did not set"
    tokens = ["zzkeepcase1", "zzkeepcase2"]
    for token, leaf in zip(tokens, ["ZZKEEPCASE1.SAV.BAK", "zzkeepcase2.SAVBACKUP"], strict=True):
        (root / f"{token}dir").mkdir()
        (root / f"{token}dir" / leaf).write_bytes(b"synthetic\n")
        (root / f"{token}dir" / "keep.md").write_text("# kept\n", encoding="utf-8")
    ignored_check = conftest.run_git(
        root, "check-ignore", "-q", "--", "zzkeepcase1dir/ZZKEEPCASE1.SAV.BAK"
    )
    assert ignored_check is not None
    assert ignored_check.returncode == 1, "control: git ignored the upper-case shape anyway"
    (root / CONTROL_LOCAL).write_text("{}\n", encoding="utf-8")
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    leaked = _leaks(text, tokens) + _leaks(raw, tokens)
    assert leaked == 0, f"{leaked} section-shape name(s) rendered with git keeping case"
    assert CONTROL_LOCAL in {skip["path"] for skip in report["skipped"]}, "control vanished"


# --- CS-1195: guard (c)'s own detail lines --------------------------------
#
# The arms above keep every planted file clean so guard (c) has nothing to
# say about it. These plant the violation on purpose: guard (c) READS a
# text-typed file git lists, and its detail lines - an offender, a NOT READ
# entry, an unlisted directory - carried the path with no classification. The
# withheld form is the CS-1158 one: the reason and a count, then the marker.
# The hits text (line, column, byte) is withheld with the name, because it
# describes the content of a credential-bearing file.

NON_ASCII = b"synthetic \xe9 byte\n"


def _guard_c(report: dict[str, Any]) -> dict[str, Any]:
    matches = [guard for guard in report["guards"] if guard["id"] == "c"]
    assert len(matches) == 1, f"control: {len(matches)} guard (c) record(s) in the payload"
    record: dict[str, Any] = matches[0]
    return record


def _withheld_group_total(detail: list[str]) -> int:
    """The sum of the counts on every `  {reason}  ({count})` line of a withheld class."""
    total = 0
    for line in detail:
        stripped = line.strip()
        if _class_of(stripped) not in WITHHELD_CLASSES or not stripped.endswith(")"):
            continue
        head, _, count = stripped.rpartition("  (")
        if head and count[:-1].isdigit():
            total += int(count[:-1])
    return total


def test_guard_c_withholds_a_tracked_upper_case_key_file_where_git_keeps_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The acceptance arm: a text-typed withheld-class file git TRACKS with its case kept.

    core.ignorecase false is set explicitly, as it is on the Linux runner, so
    `.gitignore`'s `.mcp.json` misses `.MCP.JSON`, a plain `git add` admits
    it, guard (c) reads it, and its non-ASCII byte made the offender line
    print its path. The host's own setting is never consulted.
    """
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    proc = conftest.run_git(root, "config", "core.ignorecase", "false")
    assert proc is not None
    assert proc.returncode == 0, "control: core.ignorecase false did not set"
    key_dir = "zz1195key"
    (root / key_dir).mkdir()
    (root / key_dir / ".MCP.JSON").write_bytes(NON_ASCII)
    (root / key_dir / "keep.md").write_text("# kept\n", encoding="utf-8")
    control = "zz1195ctl.txt"
    (root / control).write_bytes(NON_ASCII)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    planted = [f"{key_dir}/.MCP.JSON", f"{key_dir}/keep.md", control, "top.md", ".gitignore"]
    added = conftest.run_git(root, "add", "--", *planted)
    assert added is not None
    assert added.returncode == 0, "control: git refused to stage the plants without -f"
    listed = conftest.run_git(root, "ls-files", "-z")
    assert listed is not None
    tracked = listed.stdout.decode("utf-8").split("\0")
    assert f"{key_dir}/.MCP.JSON" in tracked, "control: git did not track the key file, case kept"
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    assert report["enumeration"].startswith("git ls-files"), "control: git did not enumerate"
    guard = _guard_c(report)
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    leaked = _leaks(text, [key_dir]) + _leaks(raw, [key_dir])
    assert leaked == 0, f"{leaked} surface(s) named the tracked withheld-class file"
    reason = drift_guard.WALK_SKIP_FILE_PATTERNS[".mcp.json"]
    detail = [line.strip() for line in guard["detail"]]
    assert f"{reason}  (1)" in detail, "guard (c) did not count the withheld offender"
    assert drift_guard.WITHHELD_MARKER in detail, "guard (c) carries no withheld marker"
    named = sum(1 for line in detail if line.startswith(f"{control} -> line 1 col "))
    assert named == 1, "control: guard (c) no longer names an ordinary offender"
    assert "non-ASCII or control bytes in 2 file(s):" in detail, "the offender count moved"


def test_guard_c_withholds_a_path_under_a_withheld_directory_shape(tmp_path: Path) -> None:
    """A text file BENEATH a withheld-shape directory: the leaf alone is innocent.

    Three ancestor shapes - a floor file shape used as a directory name, a
    withheld root in upper case, and an account-id-shaped component - each
    over an ordinary `.txt` carrying a non-ASCII byte, plus a control.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    digits = "7" * drift_guard.account_id_min_digits()
    plants = {
        "ZZ1195.LOG/zzin.txt": "zz1195.log",
        "CORPUS/zz1195c.txt": "zz1195c",
        f"{digits}/zz1195acct.txt": digits,
    }
    for relative in plants:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(NON_ASCII)
    control = "zz1195plain.txt"
    (root / control).write_bytes(NON_ASCII)
    files = [root / relative for relative in plants] + [root / control]

    guard, _skips = drift_guard.guard_charset(root, files, "test enumeration")

    joined = "\n".join(guard["detail"])
    leaked = _leaks(joined, [*plants.values(), "zzin"])
    assert leaked == 0, f"guard (c) named {leaked} path(s) under a withheld directory shape"
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    assert _withheld_group_total(guard["detail"]) == len(plants), "withheld counts do not add up"
    assert drift_guard.WITHHELD_MARKER in {line.strip() for line in guard["detail"]}
    named = sum(1 for line in guard["detail"] if line.strip().startswith(f"{control} -> "))
    assert named == 1, "control: guard (c) no longer names an ordinary offender"
    assert f"non-ASCII or control bytes in {len(plants) + 1} file(s):" in guard["detail"]


def test_guard_c_withholds_unread_and_unlisted_entries_of_a_withheld_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The NOT READ and NOT LISTED detail lines go through the same classifier.

    A withheld-shape file whose read fails and a directory under a withheld
    root that the reader was handed, each beside an ordinary one of the same
    kind that must still be named. The status stays a could-not-look WARN.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    unread_hidden = root / "zz1195u" / ".ENV.JSON"
    unread_shown = root / "zz1195ushown.txt"
    for path in (unread_hidden, unread_shown):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"clean\n")
    unlisted_hidden = root / "CORPUS" / "zz1195d"
    unlisted_shown = root / "zz1195dshown"
    for path in (unlisted_hidden, unlisted_shown):
        path.mkdir(parents=True)
    original: Callable[[Path], tuple[list[str], str]] = vars(drift_guard)["_ascii_violations"]

    def _fail_two(path: Path) -> tuple[list[str], str]:
        if path in (unread_hidden, unread_shown):
            return [], "unreadable: synthetic refusal"
        return original(path)

    monkeypatch.setattr(drift_guard, "_ascii_violations", _fail_two)
    files = [unread_hidden, unread_shown, unlisted_hidden, unlisted_shown]
    hidden = (unread_hidden, unlisted_hidden)

    guard, _skips = drift_guard.guard_charset(root, files, "test enumeration")

    joined = "\n".join(guard["detail"])
    leaked = _leaks(joined, ["zz1195u/", "zz1195d/", "zz1195d "])
    assert leaked == 0, f"guard (c) named {leaked} withheld NOT READ or NOT LISTED entries"
    assert guard["status"] == "WARN", f"guard (c) is {guard['status']}, not WARN"
    assert _withheld_group_total(guard["detail"]) == len(hidden), "withheld counts do not add up"
    assert "text files listed: 2" in guard["detail"], "the listed count dropped a withheld file"
    shown_unread = sum(1 for line in guard["detail"] if line.startswith("zz1195ushown.txt NOT"))
    shown_unlisted = sum(1 for line in guard["detail"] if line.startswith("zz1195dshown/ NOT"))
    assert (shown_unread, shown_unlisted) == (1, 1), "control: an ordinary entry is no longer named"


# CS-1195 repair - each directory authority the classifier asks gets a plant
# ONLY that authority withholds, so dropping any one of them reddens an arm.
# A plant two authorities both cover (`CORPUS`, in the root table AND the
# `.gitignore` section) survives the loss of either one.
ROOT_TABLE_ONLY_DIR = "MOON_SYNC_INBOX"
FLOOR_ONLY_DIR = "ZZ1195F.LOG"
SECTION_ONLY_DIR = "zz1195q.SAV.BAK"


def test_each_single_authority_plant_is_covered_by_that_authority_alone() -> None:
    """Anti-vacuity: the three plants below separate the three authorities."""
    pii = drift_guard._gitignore_pii_patterns(REPO_ROOT)  # noqa: SLF001 - the section reader under test

    def _section(relative: str) -> bool:
        name = relative.rsplit("/", 1)[-1]
        matches = drift_guard._gitignore_matches  # noqa: SLF001
        return any(matches(p, relative, name, is_dir=True) for p in pii)

    def _root(relative: str) -> bool:
        reason = drift_guard._root_reason(relative)  # noqa: SLF001
        return reason is not None and _class_of(reason) in WITHHELD_CLASSES

    def _floor(relative: str) -> bool:
        reason = drift_guard._floor_reason(relative, relative)  # noqa: SLF001
        return reason is not None and _class_of(reason) in WITHHELD_CLASSES

    observed = {
        shape: (_root(shape), _floor(shape), _section(shape))
        for shape in (ROOT_TABLE_ONLY_DIR, FLOOR_ONLY_DIR, SECTION_ONLY_DIR)
    }
    assert observed == {
        ROOT_TABLE_ONLY_DIR: (True, False, False),
        FLOOR_ONLY_DIR: (False, True, False),
        SECTION_ONLY_DIR: (False, False, True),
    }


@pytest.mark.parametrize("directory", [ROOT_TABLE_ONLY_DIR, FLOOR_ONLY_DIR, SECTION_ONLY_DIR])
def test_guard_c_withholds_an_offender_under_a_single_authority_directory(
    directory: str, tmp_path: Path
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    (root / directory).mkdir()
    (root / directory / "zz1195leaf.txt").write_bytes(NON_ASCII)
    control = "zz1195plain.txt"
    (root / control).write_bytes(NON_ASCII)
    files = [root / directory / "zz1195leaf.txt", root / control]

    guard, _skips = drift_guard.guard_charset(root, files, "test enumeration")

    joined = "\n".join(guard["detail"])
    leaked = _leaks(joined, [directory.lower(), "zz1195leaf"])
    assert leaked == 0, f"guard (c) named {leaked} token(s) under a single-authority directory"
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    assert _withheld_group_total(guard["detail"]) == 1, "the withheld offender was not counted"
    named = sum(1 for line in guard["detail"] if line.strip().startswith(f"{control} -> "))
    assert named == 1, "control: guard (c) no longer names an ordinary offender"


@pytest.mark.parametrize("directory", [ROOT_TABLE_ONLY_DIR, FLOOR_ONLY_DIR, SECTION_ONLY_DIR])
def test_partition_skips_withholds_a_record_beneath_a_withheld_directory_shape(
    directory: str,
) -> None:
    """The ancestor widening, through the skip-list seam itself.

    Before CS-1195 a reader's own skip record beneath `MOON_SYNC_INBOX/` or
    `zz.SAV.BAK/` carried its path: the leaf is an ordinary `.bin`.
    """
    reason = "not an authored text file type (.bin)"
    skips = [
        {"path": f"{directory}/zz1195p.bin", "reason": reason},
        {"path": "zz1195ordinary.bin", "reason": reason},
    ]
    pii = drift_guard._gitignore_pii_patterns(REPO_ROOT)  # noqa: SLF001 - the real section

    shown, withheld = drift_guard.partition_skips(skips, pii)

    shown_paths = [skip["path"] for skip in shown]
    assert shown_paths == ["zz1195ordinary.bin"], "the record beneath the shape was named"
    assert sum(withheld.values()) == 1, "the withheld record was not counted"
    assert all(_class_of(key) in WITHHELD_CLASSES for key in withheld), "counted outside a class"


def test_guard_c_withholds_an_unlisted_directory_a_dir_only_pattern_names(
    tmp_path: Path,
) -> None:
    """A directory handed to the reader is classified AS a directory.

    The `.gitignore` here files one dir-only pattern under PII-BEARING that no
    table carries, so only a directory reading of the path withholds it.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_text(
        "# ====\n# PII-BEARING - synthetic\n# ====\n/zz1195dironly/\n", encoding="utf-8"
    )
    hidden = root / "zz1195dironly"
    shown = root / "zz1195dirshown"
    hidden.mkdir()
    shown.mkdir()

    guard, _skips = drift_guard.guard_charset(root, [hidden, shown], "test enumeration")

    joined = "\n".join(guard["detail"])
    assert _leaks(joined, ["zz1195dironly"]) == 0, "guard (c) named a dir-only PII directory"
    assert guard["status"] == "WARN", f"guard (c) is {guard['status']}, not WARN"
    assert _withheld_group_total(guard["detail"]) == 1, "the withheld directory was not counted"
    named = sum(1 for line in guard["detail"] if line.startswith("zz1195dirshown/ NOT"))
    assert named == 1, "control: an ordinary unlisted directory is no longer named"


def test_a_gitlink_named_like_a_withheld_root_is_withheld_from_the_skip_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The path ITSELF is a directory shape: a gitlink is in the index, not on disk.

    `enumerate_files` records it "in the git index but not on disk" under its
    own path, and that path is a withheld ROOT - not an ancestor, not a leaf
    shape the file floor knows. A second gitlink of no shape is the control.
    """
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    added = conftest.run_git(root, "add", "--", "top.md", ".gitignore")
    assert added is not None
    assert added.returncode == 0, "control: git refused to stage the plain files"
    control = "zz1195gitlink"
    for link in (ROOT_TABLE_ONLY_DIR, control):
        proc = conftest.run_git(
            root, "update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},{link}"
        )
        assert proc is not None
        assert proc.returncode == 0, "control: git refused the gitlink"
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    assert report["enumeration"].startswith("git ls-files"), "control: git did not enumerate"
    # A gitlink is a directory entry, so it may render with a trailing slash.
    skipped = {skip["path"].rstrip("/") for skip in report["skipped"]}
    assert control in skipped, "control: an ordinary gitlink is no longer named"
    lines = {line.strip().rstrip("/") for line in text.splitlines()}
    named = int(ROOT_TABLE_ONLY_DIR in skipped) + int(ROOT_TABLE_ONLY_DIR in lines)
    assert named == 0, f"{named} surface(s) named a gitlink shaped like a withheld root"
    reason = drift_guard.WALK_SKIP_ROOT_PATHS[ROOT_TABLE_ONLY_DIR.lower()]
    counts = {entry["reason"]: entry["count"] for entry in report["withheld"]}
    assert counts.get(reason) == 1, "the withheld gitlink was not counted under its root reason"


@pytest.mark.parametrize("name", ["corpus", "moon_sync_inbox", "CORPUS"])
def test_a_plain_file_named_like_a_withheld_root_is_still_named(name: str) -> None:
    """ADR 0023 rule 5 against rule 3: a FILE is not the directory its name matches.

    The root table and the `.gitignore` section name DIRECTORIES. A plain file
    whose name happens to equal one locates nothing the rule withholds, so its
    skip record still names it. Only a directory entry - a trailing slash, as
    the walk and a gitlink record carry - is read as the directory shape.
    """
    reason = "not an authored text file type (no extension)"
    skips = [
        {"path": name, "reason": reason},
        {"path": f"{name}/", "reason": "in the git index but not on disk"},
    ]
    pii = drift_guard._gitignore_pii_patterns(REPO_ROOT)  # noqa: SLF001 - the real section

    shown, withheld = drift_guard.partition_skips(skips, pii)

    assert [skip["path"] for skip in shown] == [name], "a plain file was withheld as a directory"
    assert sum(withheld.values()) == 1, "control: the directory entry was not withheld"


def test_guard_c_fails_when_its_only_offender_is_withheld(tmp_path: Path) -> None:
    """No control offender: the withheld one alone must still make guard (c) FAIL."""
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    (root / "CORPUS").mkdir()
    (root / "CORPUS" / "zz1195only.txt").write_bytes(NON_ASCII)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    files = [root / "CORPUS" / "zz1195only.txt", root / "top.md"]

    guard, _skips = drift_guard.guard_charset(root, files, "test enumeration")

    joined = "\n".join(guard["detail"])
    assert _leaks(joined, ["zz1195only"]) == 0, "guard (c) named its only, withheld offender"
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    assert "non-ASCII or control bytes in 1 file(s):" in guard["detail"], "the count was lost"
    assert _withheld_group_total(guard["detail"]) == 1, "the withheld offender was not counted"


# CS-1195 repair - the index-entry type question. A missing index entry is a
# directory entry when git says gitlink OR the disk says directory, and EVERY
# entry is when git cannot answer (fails closed). The index listing itself is
# stubbed so only the `ls-files -s` question varies; no git runs.
GONE_FILE = "zz1195gone.txt"


def _missing_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entries: list[str]
) -> tuple[list[dict[str, str]], dict[str, int]]:
    root = tmp_path / "tree"
    root.mkdir(exist_ok=True)
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    monkeypatch.setattr(drift_guard, "_git_ls_files", lambda _root: ["top.md", *entries])
    _files, _source, skips = drift_guard.enumerate_files(root)
    pii = drift_guard._gitignore_pii_patterns(root)  # noqa: SLF001 - the tree's own section
    result: tuple[list[dict[str, str]], dict[str, int]] = drift_guard.partition_skips(skips, pii)
    return result


def _refusing_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=128, stdout="", stderr="")


def _raising_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    message = "synthetic start fault"
    raise OSError(message)


@pytest.mark.parametrize("failure", ["answer-is-none", "git-not-found", "non-zero", "start-fault"])
def test_a_gitlink_stays_withheld_when_git_cannot_say_it_is_one(
    failure: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fails closed: with no answer from `ls-files -s`, every missing entry is a directory.

    DECLARED, not accidental: a missing plain file then renders as
    `zz1195gone.txt/` - named, with a slash - because git could not say it
    was a file. The gitlink shaped like a withheld root is counted, never named.
    """
    if failure == "answer-is-none":
        monkeypatch.setattr(drift_guard, "_git_gitlinks", lambda _root: None)
    elif failure == "git-not-found":
        monkeypatch.setattr(drift_guard, "resolve_tool", lambda _name: None)
    else:
        monkeypatch.setattr(drift_guard, "resolve_tool", lambda _name: "git-synthetic")
        runner = _refusing_run if failure == "non-zero" else _raising_run
        monkeypatch.setattr(drift_guard.subprocess, "run", runner)

    shown, withheld = _missing_entries(tmp_path, monkeypatch, [ROOT_TABLE_ONLY_DIR, GONE_FILE])

    shown_paths = [skip["path"] for skip in shown]
    assert shown_paths == [f"{GONE_FILE}/"], "the fail-closed branch did not read a directory"
    reason = drift_guard.WALK_SKIP_ROOT_PATHS[ROOT_TABLE_ONLY_DIR.lower()]
    assert withheld == {reason: 1}, "the gitlink was not withheld under its root reason"


def test_an_index_entry_the_disk_calls_a_directory_is_read_as_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git answers "not a gitlink", and the entry is a DIRECTORY on disk.

    Only the disk's own answer marks it a directory entry, so only that
    withholds a directory named like a withheld root. A missing plain file
    beside it, which git DID answer for, renders as the file it is.
    """
    monkeypatch.setattr(drift_guard, "_git_gitlinks", lambda _root: frozenset())
    (tmp_path / "tree" / ROOT_TABLE_ONLY_DIR).mkdir(parents=True)

    shown, withheld = _missing_entries(tmp_path, monkeypatch, [ROOT_TABLE_ONLY_DIR, GONE_FILE])

    reason = drift_guard.WALK_SKIP_ROOT_PATHS[ROOT_TABLE_ONLY_DIR.lower()]
    assert withheld == {reason: 1}, "the on-disk directory entry was not withheld"
    assert [skip["path"] for skip in shown] == [GONE_FILE], "control: a missing file moved"


# CS-1195 repair - a `.gitignore` PII-BEARING section of DIRECTORY-ONLY
# patterns no table carries, so only the directory reading decides. One names a
# directory the offender sits BENEATH; two name directories whose spelling a
# plain text FILE also has - and a file is not the directory (ADR 0023 rule 5).
DIR_ONLY_PARENT = "zz1195dironly"
DIR_ONLY_FILE_OFFENDER = "zz1195dirfile.txt"
DIR_ONLY_FILE_UNREAD = "zz1195dirunread.txt"


def _dir_only_tree(tmp_path: Path) -> Path:
    root = tmp_path / "tree"
    root.mkdir()
    patterns = "".join(
        f"/{name}/\n" for name in (DIR_ONLY_PARENT, DIR_ONLY_FILE_OFFENDER, DIR_ONLY_FILE_UNREAD)
    )
    (root / ".gitignore").write_text(
        f"# ====\n# PII-BEARING - synthetic\n# ====\n{patterns}", encoding="utf-8"
    )
    return root


def test_guard_c_withholds_an_offender_beneath_a_dir_only_pattern_directory(
    tmp_path: Path,
) -> None:
    root = _dir_only_tree(tmp_path)
    (root / DIR_ONLY_PARENT).mkdir()
    hidden = root / DIR_ONLY_PARENT / "zz1195in.txt"
    hidden.write_bytes(NON_ASCII)

    guard, _skips = drift_guard.guard_charset(root, [hidden], "test enumeration")

    joined = "\n".join(guard["detail"])
    leaked = _leaks(joined, [DIR_ONLY_PARENT, "zz1195in"])
    assert leaked == 0, f"guard (c) named {leaked} token(s) beneath a dir-only PII directory"
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    assert _withheld_group_total(guard["detail"]) == 1, "the withheld offender was not counted"


def test_guard_c_names_a_plain_file_spelt_like_a_dir_only_pattern(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither an offender FILE nor a NOT READ FILE is read as a directory."""
    root = _dir_only_tree(tmp_path)
    offender = root / DIR_ONLY_FILE_OFFENDER
    offender.write_bytes(NON_ASCII)
    unread = root / DIR_ONLY_FILE_UNREAD
    unread.write_bytes(b"clean\n")
    original: Callable[[Path], tuple[list[str], str]] = vars(drift_guard)["_ascii_violations"]

    def _fail_one(path: Path) -> tuple[list[str], str]:
        if path == unread:
            return [], "unreadable: synthetic refusal"
        return original(path)

    monkeypatch.setattr(drift_guard, "_ascii_violations", _fail_one)

    guard, _skips = drift_guard.guard_charset(root, [offender, unread], "test enumeration")

    detail = [line.strip() for line in guard["detail"]]
    named_offender = sum(1 for line in detail if line.startswith(f"{DIR_ONLY_FILE_OFFENDER} -> "))
    named_unread = sum(1 for line in detail if line.startswith(f"{DIR_ONLY_FILE_UNREAD} NOT READ"))
    assert named_offender == 1, "a plain offender FILE was withheld as a directory"
    assert named_unread == 1, "a plain NOT READ FILE was withheld as a directory"
    assert _withheld_group_total(guard["detail"]) == 0, "a plain file was counted as withheld"


def test_guard_c_names_a_nested_directory_spelt_like_a_withheld_root(tmp_path: Path) -> None:
    """The root table is ANCHORED: `zz/MOON_SYNC_INBOX/` is not the root it names."""
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    nested = root / "zz1195sub" / ROOT_TABLE_ONLY_DIR / "zz1195n.txt"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(NON_ASCII)

    guard, _skips = drift_guard.guard_charset(root, [nested], "test enumeration")

    expected = f"zz1195sub/{ROOT_TABLE_ONLY_DIR}/zz1195n.txt -> "
    named = sum(1 for line in guard["detail"] if line.strip().startswith(expected))
    assert named == 1, "a nested directory was withheld as the anchored root it is not"
    assert _withheld_group_total(guard["detail"]) == 0, "a nested directory was counted as a root"


def test_guard_c_counts_every_withheld_entry_under_its_own_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TWO of each withheld kind under one reason: the count is 2, never capped at 1.

    Each withheld group follows its own heading - NOT READ, NOT LISTED and the
    offender header - so the line after each heading carries that group's count.
    """
    root = tmp_path / "tree"
    root.mkdir()
    (root / ".gitignore").write_bytes((REPO_ROOT / ".gitignore").read_bytes())
    corpus = root / "CORPUS"
    corpus.mkdir()
    offenders = [corpus / "zz1195o1.txt", corpus / "zz1195o2.txt"]
    unread = [corpus / "zz1195u1.txt", corpus / "zz1195u2.txt"]
    unlisted = [corpus / "zz1195d1", corpus / "zz1195d2"]
    for path in offenders:
        path.write_bytes(NON_ASCII)
    for path in unread:
        path.write_bytes(b"clean\n")
    for path in unlisted:
        path.mkdir()
    original: Callable[[Path], tuple[list[str], str]] = vars(drift_guard)["_ascii_violations"]

    def _fail_unread(path: Path) -> tuple[list[str], str]:
        if path in unread:
            return [], "unreadable: synthetic refusal"
        return original(path)

    monkeypatch.setattr(drift_guard, "_ascii_violations", _fail_unread)

    guard, _skips = drift_guard.guard_charset(
        root, [*offenders, *unread, *unlisted], "test enumeration"
    )

    detail = guard["detail"]
    assert _leaks("\n".join(detail), ["zz1195"]) == 0, "guard (c) named a withheld entry"
    assert guard["status"] == "FAIL", f"guard (c) is {guard['status']}, not FAIL"
    group = f"  {drift_guard.WALK_SKIP_ROOT_PATHS['corpus']}  ({len(offenders)})"
    headings = [
        "NOT READ - its bytes were never checked, under a withheld reason:",
        f"{drift_guard.UNLISTED_CONSEQUENCE}, under a withheld reason:",
        f"non-ASCII or control bytes in {len(offenders)} file(s):",
    ]
    for heading in headings:
        present = heading in detail
        assert present, f"guard (c) lost a withheld group heading ({headings.index(heading)})"
        after = detail[detail.index(heading) + 1]
        assert after == group, f"group {headings.index(heading)} does not carry the count 2"


# --- CS-1210: guard_dated's own detail lines ------------------------------
#
# The CS-1195 leak one guard over. guard_dated rendered `_rel(root, path)`
# with no classification in its heading records (both families, the
# historical-in-live list and the unclassified list), its undeclared list,
# its NOT READ lines and its unlisted-directory lines. Each render site is a
# KIND below with its own plant, so a bypass at any one site reddens that kind
# alone. A withheld path drops its heading TEXT with its name - a heading can
# carry a leaf. Every arm also runs a TWIN tree, the same plants beneath an
# ordinary directory, and asserts the verdict and the counts do not move.

WITHHELD_HEAD = "zz1210head"
CONTROL_HEAD = "zz1210hctl"
CONTROL_STEM = "zz1210ctl"
WITHHELD_PARENT = "CORPUS"
TWIN_PARENT = "zz1210twin"
REFUSED_READ = "synthetic refusal"

#: kind -> (the file's declaration or None, the heading with `{token}` in it).
DATED_FILE_KINDS: dict[str, tuple[str | None, str]] = {
    "status": ("HISTORICAL", "## 2031-02-03 {token}"),
    "provenance": ("LIVE", "## Notes - filed 2031-02-03 {token}"),
    "historical_in_live": ("LIVE", "## 2031-02-03 {token}"),
    "unclassified": ("LIVE", "## {token} sits 2031-02-03"),
    "undeclared": (None, "## Notes - filed 2031-02-03 {token}"),
}
DATED_KINDS = (*DATED_FILE_KINDS, "unread", "unlisted")
#: The kinds that decide guard_dated's verdict on their own.
DATED_VERDICT_KINDS = ("historical_in_live", "unclassified", "undeclared", "unread", "unlisted")


def _dated_group_heading(kind: str) -> str:
    """The detail line each kind's group follows, by prefix."""
    return {
        "status": f"{drift_guard.STATUS_DATE} dates (",
        "provenance": f"{drift_guard.PROVENANCE_DATE} dates (",
        "historical_in_live": f"DRIFT - a {drift_guard.STATUS_DATE} date inside",
        "unclassified": "DRIFT - dated headings in an idiom",
        "undeclared": "DRIFT - files carrying dated headings",
        "unread": "NOT READ - its headings were never classified, under a withheld reason:",
        "unlisted": f"{drift_guard.UNLISTED_CONSEQUENCE}, under a withheld reason:",
    }[kind]


def _group_block(detail: list[str], prefix: str) -> list[str]:
    """The indented lines under the first detail line starting ``prefix``."""
    starts = [index for index, line in enumerate(detail) if line.startswith(prefix)]
    assert starts, f"no detail line opens the group ({prefix[:24]})"
    block: list[str] = []
    for line in detail[starts[0] + 1 :]:
        if not line.startswith(" "):
            break
        block.append(line)
    return block


def _plant_dated(root: Path, stem: str, kind: str, token: str) -> Path:
    """One entry of ``kind`` at ``stem``: a directory, or `stem.md` carrying a dated heading."""
    if kind == "unlisted":
        path = root / stem
        path.mkdir(parents=True)
        return path
    declaration, heading = DATED_FILE_KINDS.get(kind, ("LIVE", "## Notes {token}"))
    header = "" if declaration is None else f"**Section status: {declaration}**\n\n"
    path = root / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"# zz title\n\n{header}{heading.format(token=token)}\n\nbody\n"
    path.write_bytes(body.encode("ascii"))
    return path


def _refuse_reads(monkeypatch: pytest.MonkeyPatch, refused: set[Path]) -> None:
    """Make ``read_text`` refuse exactly ``refused``, so the guard's own read path runs."""
    original: Callable[..., str] = Path.read_text

    def _read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if self in refused:
            raise PermissionError(13, REFUSED_READ)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _read_text)


def _run_dated(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    entries: list[tuple[str, str, str]],
    gitignore: bytes | None = None,
) -> dict[str, Any]:
    """Plant (stem, kind, heading token) entries under ``root`` and run guard_dated."""
    root.mkdir(parents=True)
    ignore = (REPO_ROOT / ".gitignore").read_bytes() if gitignore is None else gitignore
    (root / ".gitignore").write_bytes(ignore)
    files = [_plant_dated(root, stem, kind, token) for stem, kind, token in entries]
    kinds = [kind for _stem, kind, _token in entries]
    refused = {path for path, kind in zip(files, kinds, strict=True) if kind == "unread"}
    with monkeypatch.context() as patch:
        _refuse_reads(patch, refused)
        guard, _skips = drift_guard.guard_dated(root, files)
    record: dict[str, Any] = dict(guard)
    return record


def _dated_counts(detail: list[str]) -> list[str]:
    """The count lines guard_dated derives - they must not move for a withheld path."""
    prefixes = (
        "markdown files scanned:",
        f"{drift_guard.STATUS_DATE} dates (",
        f"{drift_guard.PROVENANCE_DATE} dates (",
    )
    return [line for line in detail if line.startswith(prefixes)]


def _withheld_and_twin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    leaves: list[str],
    extra: list[tuple[str, str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run ``leaves`` of ``kind`` beneath the withheld parent, and again beneath a twin."""
    guards = []
    for tree, parent in (("withheld", WITHHELD_PARENT), ("twin", TWIN_PARENT)):
        entries = [(f"{parent}/{leaf}", kind, WITHHELD_HEAD) for leaf in leaves]
        guards.append(_run_dated(tmp_path / tree, monkeypatch, [*entries, *extra]))
    return guards[0], guards[1]


def _assert_twin_verdict(withheld: dict[str, Any], twin: dict[str, Any]) -> None:
    assert withheld["status"] == twin["status"], (
        f"the verdict moved: {withheld['status']} withheld, {twin['status']} ordinary"
    )
    same_counts = _dated_counts(withheld["detail"]) == _dated_counts(twin["detail"])
    assert same_counts, "a count line moved when the path was withheld"


@pytest.mark.parametrize("kind", DATED_KINDS)
def test_guard_dated_withholds_each_render_site_and_names_the_control(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each render site alone: the withheld entry is counted, the control still named.

    The heading token is asserted absent too - the heading TEXT of a withheld
    path is dropped with its name. The twin run proves the verdict and the
    count lines are those of the same entry beneath an ordinary directory.
    """
    control = [(CONTROL_STEM, kind, CONTROL_HEAD)]
    guard, twin = _withheld_and_twin(tmp_path, monkeypatch, kind, ["zz1210w"], control)

    detail: list[str] = guard["detail"]
    joined = "\n".join(detail)
    leaked = _leaks(joined, ["zz1210w", WITHHELD_HEAD])
    assert leaked == 0, f"guard_dated named {leaked} token(s) of a withheld {kind} entry"
    reason = drift_guard.WALK_SKIP_ROOT_PATHS[WITHHELD_PARENT.lower()]
    prefix = _dated_group_heading(kind)
    block = [line.strip() for line in _group_block(detail, prefix)]
    assert f"{reason}  (1)" in block, f"the withheld {kind} entry was not counted in its group"
    assert drift_guard.WITHHELD_MARKER in block, f"the {kind} group carries no withheld marker"
    assert _leaks(joined, [CONTROL_STEM]) == 1, f"control: an ordinary {kind} entry is not named"
    if kind in DATED_FILE_KINDS:
        assert _leaks(joined, [CONTROL_HEAD]) == 1, "control: an ordinary heading is not named"
    _assert_twin_verdict(guard, twin)


@pytest.mark.parametrize("kind", DATED_VERDICT_KINDS)
def test_guard_dated_keeps_its_verdict_when_its_only_finding_is_withheld(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No control finding: the withheld entry alone must keep guard_dated off PASS."""
    clean = [("zz1210top", "clean", CONTROL_HEAD)]
    guard, twin = _withheld_and_twin(tmp_path, monkeypatch, kind, ["zz1210w"], clean)

    leaked = _leaks("\n".join(guard["detail"]), ["zz1210w", WITHHELD_HEAD])
    assert leaked == 0, f"guard_dated named {leaked} token(s) of its only, withheld finding"
    assert twin["status"] != "PASS", f"control: an ordinary {kind} entry alone passed"
    _assert_twin_verdict(guard, twin)


@pytest.mark.parametrize("kind", DATED_KINDS)
def test_guard_dated_counts_two_withheld_entries_as_two(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TWO withheld entries of one kind under one reason: the count is 2, never capped."""
    leaves = ["zz1210w1", "zz1210w2"]
    guard, twin = _withheld_and_twin(tmp_path, monkeypatch, kind, leaves, [])

    detail: list[str] = guard["detail"]
    leaked = _leaks("\n".join(detail), ["zz1210w", WITHHELD_HEAD])
    assert leaked == 0, f"guard_dated named {leaked} token(s) of two withheld {kind} entries"
    reason = drift_guard.WALK_SKIP_ROOT_PATHS[WITHHELD_PARENT.lower()]
    block = [line.strip() for line in _group_block(detail, _dated_group_heading(kind))]
    assert block[:1] == [f"{reason}  ({len(leaves)})"], f"the {kind} group does not count 2"
    _assert_twin_verdict(guard, twin)


# A `.gitignore` PII-BEARING section of DIRECTORY-ONLY patterns no table
# carries, so only the directory reading decides: one names a directory a
# markdown file sits BENEATH, one a directory handed to the reader, and two
# name directories whose spelling a plain markdown FILE also has - and a file
# is not the directory (ADR 0023 rule 5).
DATED_DIR_ONLY_PARENT = "zz1210dironly"
DATED_DIR_ONLY_LISTED = "zz1210dirlisted"
DATED_DIR_ONLY_FILE = "zz1210dirfile"
DATED_DIR_ONLY_UNREAD = "zz1210dirunread"


def _dated_dir_only_gitignore() -> bytes:
    patterns = "".join(
        f"/{name}/\n"
        for name in (
            DATED_DIR_ONLY_PARENT,
            DATED_DIR_ONLY_LISTED,
            f"{DATED_DIR_ONLY_FILE}.md",
            f"{DATED_DIR_ONLY_UNREAD}.md",
        )
    )
    return f"# ====\n# PII-BEARING - synthetic\n# ====\n{patterns}".encode("ascii")


def test_guard_dated_withholds_entries_a_dir_only_pattern_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Beneath a dir-only directory, and a handed directory a dir-only pattern names."""
    entries = [
        (f"{DATED_DIR_ONLY_PARENT}/zz1210in", "unclassified", WITHHELD_HEAD),
        (DATED_DIR_ONLY_LISTED, "unlisted", WITHHELD_HEAD),
    ]

    guard = _run_dated(tmp_path / "tree", monkeypatch, entries, _dated_dir_only_gitignore())

    detail: list[str] = guard["detail"]
    tokens = [DATED_DIR_ONLY_PARENT, DATED_DIR_ONLY_LISTED, "zz1210in", WITHHELD_HEAD]
    leaked = _leaks("\n".join(detail), tokens)
    assert leaked == 0, f"guard_dated named {leaked} token(s) a dir-only PII pattern withholds"
    assert guard["status"] == "FAIL", f"guard_dated is {guard['status']}, not FAIL"
    for kind in ("unclassified", "unlisted"):
        block = [line.strip() for line in _group_block(detail, _dated_group_heading(kind))]
        expected = f"{drift_guard.GITIGNORE_PII_REASON}  (1)"
        assert expected in block, f"the withheld {kind} entry was not counted"


def test_guard_dated_names_a_plain_file_spelt_like_a_dir_only_pattern(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither a heading-bearing FILE nor a NOT READ FILE is read as a directory."""
    entries = [
        (DATED_DIR_ONLY_FILE, "unclassified", CONTROL_HEAD),
        (DATED_DIR_ONLY_UNREAD, "unread", CONTROL_HEAD),
    ]

    guard = _run_dated(tmp_path / "tree", monkeypatch, entries, _dated_dir_only_gitignore())

    detail = [line.strip() for line in guard["detail"]]
    record = f"{DATED_DIR_ONLY_FILE}.md:5  ## {CONTROL_HEAD} sits 2031-02-03"
    named_record = sum(1 for line in detail if line == record)
    named_unread = sum(1 for line in detail if line.startswith(f"{DATED_DIR_ONLY_UNREAD}.md NOT"))
    assert named_record == 1, "a plain heading-bearing FILE was withheld as a directory"
    assert named_unread == 1, "a plain NOT READ FILE was withheld as a directory"
    assert _withheld_group_total(guard["detail"]) == 0, "a plain file was counted as withheld"


@pytest.mark.parametrize("ignorecase", ["false", "true"])
def test_guard_dated_withholds_a_tracked_upper_case_key_file_under_either_git_case(
    ignorecase: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The acceptance arm: `.ENV.MD` git TRACKS, with case kept and with case folded.

    Under core.ignorecase false `.gitignore`'s `.env.*` misses `.ENV.MD` and a
    plain `git add` admits it; under true it is ignored, so it is force-added.
    Either way git lists it, guard_dated reads it, and its dated heading made
    the heading record print its path and its heading text.
    """
    root = tmp_path / "tree"
    if not _real_gitignore_repo(root, monkeypatch):
        pytest.skip("git is not installed, so its answer cannot be asked")
    from tests import conftest  # noqa: PLC0415 - the one git runner the suite owns

    proc = conftest.run_git(root, "config", "core.ignorecase", ignorecase)
    assert proc is not None
    assert proc.returncode == 0, "control: core.ignorecase did not set"
    key_dir = "zz1210key"
    (root / key_dir).mkdir()
    (root / key_dir / ".ENV.MD").write_bytes(
        f"# zz\n\n**Section status: LIVE**\n\n## {WITHHELD_HEAD} sits 2031-02-03\n".encode("ascii")
    )
    (root / key_dir / "keep.md").write_text("# kept\n", encoding="utf-8")
    _plant_dated(root, CONTROL_STEM, "unclassified", CONTROL_HEAD)
    (root / "top.md").write_text("# clean\n", encoding="utf-8")
    plain = [f"{key_dir}/keep.md", f"{CONTROL_STEM}.md", "top.md", ".gitignore"]
    key = [f"{key_dir}/.ENV.MD"]
    staged = [*plain, *key] if ignorecase == "false" else plain
    added = conftest.run_git(root, "add", "--", *staged)
    assert added is not None
    assert added.returncode == 0, "control: git refused to stage the plants without -f"
    if ignorecase == "true":
        forced = conftest.run_git(root, "add", "-f", "--", *key)
        assert forced is not None
        assert forced.returncode == 0, "control: git refused to force-add the key file"
    listed = conftest.run_git(root, "ls-files", "-z")
    assert listed is not None
    tracked = listed.stdout.decode("utf-8").split("\0")
    assert key[0] in tracked, "control: git does not track the key file"
    _point_at(monkeypatch, root, tmp_path)

    text = _run(capsys)
    raw = _run(capsys, "--json")
    report: dict[str, Any] = json.loads(raw)

    assert report["enumeration"].startswith("git ls-files"), "control: git did not enumerate"
    matches = [guard for guard in report["guards"] if guard["name"] == "dated sections"]
    assert len(matches) == 1, f"control: {len(matches)} guard_dated record(s) in the payload"
    guard = matches[0]
    assert guard["status"] == "FAIL", f"guard_dated is {guard['status']}, not FAIL"
    leaked = _leaks(text, [key_dir, WITHHELD_HEAD]) + _leaks(raw, [key_dir, WITHHELD_HEAD])
    assert leaked == 0, f"{leaked} surface(s) named the tracked withheld-class markdown file"
    reason = drift_guard.WALK_SKIP_FILE_PATTERNS[".env.*"]
    block = [line.strip() for line in _group_block(guard["detail"], "DRIFT - dated headings")]
    assert f"{reason}  (1)" in block, "guard_dated did not count the withheld heading record"
    assert _leaks(text, [CONTROL_HEAD]) == 1, "control: an ordinary dated heading is not named"


def test_guard_dated_withholds_an_unread_file_beneath_a_dir_only_pattern_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A NOT READ file whose parent ONLY the `.gitignore` PII-BEARING section withholds.

    The parent is in no table, so only the tree's own section - not an empty
    pattern set - decides that its unread child is counted, never named.
    """
    entries = [(f"{DATED_DIR_ONLY_PARENT}/zz1210unl", "unread", WITHHELD_HEAD)]

    guard = _run_dated(tmp_path / "tree", monkeypatch, entries, _dated_dir_only_gitignore())

    detail: list[str] = guard["detail"]
    leaked = _leaks("\n".join(detail), [DATED_DIR_ONLY_PARENT, "zz1210unl"])
    assert leaked == 0, f"guard_dated named {leaked} token(s) of an unread dir-only child"
    assert guard["status"] == "WARN", f"guard_dated is {guard['status']}, not WARN"
    block = [line.strip() for line in _group_block(detail, _dated_group_heading("unread"))]
    expected = f"{drift_guard.GITIGNORE_PII_REASON}  (1)"
    assert expected in block, "the withheld NOT READ entry was not counted"


@pytest.mark.parametrize("kind", ["status", "provenance"])
def test_guard_dated_does_not_call_withheld_headings_absent(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every dated heading withheld: they are counted, so none is `not found`.

    The whole detail is compared with the twin's, line for line, once the
    records themselves are set aside - the two differ only in how a record
    is shown, never in what the guard says it found.
    """
    guard, twin = _withheld_and_twin(tmp_path, monkeypatch, kind, ["zz1210w"], [])

    detail: list[str] = guard["detail"]
    absent = "no dated headings found; nothing is self-marked historical"
    said_absent = absent in detail
    assert not said_absent, f"guard_dated called its withheld {kind} heading absent"
    assert absent not in twin["detail"], "control: the twin's heading was called absent"
    unindented = [line for line in detail if not line.startswith(" ")]
    twin_unindented = [line for line in twin["detail"] if not line.startswith(" ")]
    same = unindented == twin_unindented
    assert same, f"guard_dated's {kind} detail differs from the ordinary twin's"
    _assert_twin_verdict(guard, twin)
