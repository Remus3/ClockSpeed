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
    skipped = {skip["path"] for skip in report["skipped"]}
    assert control in skipped, "control: an ordinary gitlink is no longer named"
    lines = {line.strip() for line in text.splitlines()}
    named = int(ROOT_TABLE_ONLY_DIR in skipped) + int(ROOT_TABLE_ONLY_DIR in lines)
    assert named == 0, f"{named} surface(s) named a gitlink shaped like a withheld root"
    reason = drift_guard.WALK_SKIP_ROOT_PATHS[ROOT_TABLE_ONLY_DIR.lower()]
    counts = {entry["reason"]: entry["count"] for entry in report["withheld"]}
    assert counts.get(reason) == 1, "the withheld gitlink was not counted under its root reason"
