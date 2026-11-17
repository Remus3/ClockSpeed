r"""CS-1402 - no scratch, temp or worktree path at a drive root, anywhere this tree authors one.

WHY. Sub-agents and headless runs left scratch directly under the E: drive root
(a scratch folder, a headless temp folder, version logs, a stray output file) and,
by handing Windows Python a ROOTED path with no drive letter such as a Users-relative
temp path while the cwd was on E:, a whole Users and Windows tree under E:. The root
of every drive is nobody's directory. The scratch root is `<sidecars>\CS\Scratch`,
the lane worktree root is `<sidecars>\CS\Worktree` (ADR 0026), and an output path is
absolute or repo-relative, never relative to whatever the cwd happens to be.

WHAT IS GRADED, one arm each:

a. the authored code, config, shell sources, git hooks, prompts and helper scripts name
   no path whose parent is a drive root, bar the repo root and the sidecar root (an
   allowlist on the PARENT, not a name heuristic on the child);
b. they name no drive-less rooted path into a temp directory;
c. the lane worktree this tree derives lies under the sidecar root (skipped, with
   its reason, where that directory does not exist, e.g. CI);
d. ``tools/freeze_witness.py freeze --out`` refuses a cwd-relative path.

ANTI-VACUITY. Every detector is run against planted strings and against a planted
file in a tmp_path population, so a detector that matched nothing would fail here
rather than pass the real population. Nothing tracked is mutated.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

import pytest
from ops.loop import lanes

REPO_ROOT = Path(__file__).resolve().parent.parent
REFUSED = 2  # freeze_witness exit code for a refusal

#: Where scratch-bearing text is authored. docs/, tests/ and the vendored kit are not here:
#: docs/history_notes.md, docs/LEDGER.md and docs/_archive are RECORDS, and the kit is
#: byte-pinned (CLAUDE.md FLEET item 11).
SCOPE_PREFIXES = (
    "clockspeed/",
    "ops/loop/",
    "tools/",
    "scripts/",
    "config/",
    "shell/",
    ".githooks/",
    ".claude/agents/",
    ".claude/commands/",
)
SCOPE_FILES = ("CLAUDE.md",)
EXCLUDED_PREFIXES = ("ops/fleet_kit/",)
#: Vendored or generated directories (anywhere in the path) and generated files.
EXCLUDED_PARTS = ("/node_modules/", "/dist/", "/out/", "/build/", "/coverage/")
#: A lockfile carries registry URLs and hashes: generated, not authored.
EXCLUDED_NAMES = ("package-lock.json",)
#: Extensionless files under these prefixes (the git hooks) are authored text.
EXTENSIONLESS_PREFIXES = (".githooks/",)
TEXT_SUFFIXES = (
    ".py",
    ".md",
    ".ps1",
    ".sh",
    ".cmd",
    ".bat",
    ".txt",
    ".json",
    ".toml",
    ".yml",
    ".js",
    ".cjs",
    ".mjs",
)

#: The only two drive-root children this tree may name: its own root and the sidecar root.
ALLOWED_DRIVE_CHILDREN = ("clockspeed", "sidecars")
#: The repo-root folder name, taken from the allowlist so no test line spells a drive plus it.
_ROOT = ALLOWED_DRIVE_CHILDREN[0].capitalize()
#: The sidecar root, its CS folder and the old lanes root, built from parts for the same reason.
_SIDE = ALLOWED_DRIVE_CHILDREN[1].capitalize()
_SIDE_CS = f"{_SIDE}/CS"
_SIDE_CS_BS = _SIDE_CS.replace("/", "\\")
_OLD_LANES = "cs-" + "worktrees"
#: A drive letter, a colon, a separator, then the first path segment (the drive-root child).
DRIVE_CHILD = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]+([^\\/\s'\"`<>|*?:,;)\]]+)")
#: A bare drive root joined with a child in code: ``Path("E:/") / "x"``, ``join("E:/", "x")``.
DRIVE_JOIN = re.compile(
    r"""(?:Path\(\s*|join\(\s*)[rR]?(['"])[A-Za-z]:[\\/]*\1\s*(?:\)\s*/|,)\s*[rR]?(['"])([^'"\\/]+)\2"""
)
#: A rooted path with NO drive letter into a temp dir. The lookbehind refuses a segment
#: inside a longer path (``a/tmp``), a drive path (``C:\tmp`` is arm a), ``~/`` and ``$``.
ROOTED_TEMP = re.compile(
    r"(?<![\w:.~$)\]>}/\\-])[\\/]"
    r"(?:Users[\\/][^\s'\"`]*?[\\/]Temp|Windows[\\/]Temp|tmp|temp|var[\\/]tmp)(?![\w.-])"
)

#: (path, substring, reason) LINES that match a detector and are KNOWN legitimate. The whole
#: line is skipped, so keep the substring specific. Each carries its reason; a new entry
#: needs one, and ``test_exempt_entries_are_all_live`` keeps each matching a real line that
#: a detector still flags (a dead waiver, or a line that no longer hits, fails there).
EXEMPT_LINES: tuple[tuple[str, str, str], ...] = (
    (
        "tools/precommit_gate.py",
        "under /tmp on Linux",
        "a comment about where a Linux home may sit; frozen file (CLAUDE.md section 6)",
    ),
    (
        ".claude/commands/drift-guard.md",
        "path-string keying - `C:\\X`,",
        "prose naming placeholder paths to explain a config-keying defect; nothing is created",
    ),
    (
        ".claude/commands/drift-guard.md",
        "`C:/X` and `C:/x` are three separate",
        "prose naming placeholder paths to explain a config-keying defect; nothing is created",
    ),
    (
        "clockspeed/surface/config.py",
        "KeyError('C:/Users/<account>/...')",
        "a comment quoting a redacted exception text; the path is a placeholder",
    ),
    (
        "clockspeed/surface/config.py",
        "WindowsPath('C:/Users/<account>/...')",
        "a docstring quoting a redacted exception text; the path is a placeholder",
    ),
    (
        "ops/loop/launch_queue_loop.ps1",
        "can't open file 'C:\\Riot'",
        "a comment quoting an error message from a mis-split path; the path is only read",
    ),
    (
        "ops/loop/slots.py",
        'DEFAULT_ROOT = Path(r"C:\\ProgramData\\lw-loop\\slots")',
        "the machine-wide slot-lease directory the fleet kit shares across trees; ProgramData "
        "is the system's shared-state root, not scratch, and a per-user path cannot be shared",
    ),
    (
        "scripts/install_hooks.py",
        "path-string keying (C:\\\\X and C:/x are",
        "a message naming placeholder paths; frozen file (CLAUDE.md section 6)",
    ),
    (
        "tools/census_axis.py",
        "character: K:\\X, k:/x and the JSON-escaped",
        "a docstring giving placeholder drive-path examples for a census axis",
    ),
    (
        "tools/outbound_send.py",
        '"C:/b"` yields `C:/b` - but it is a fast rejection',
        "a comment explaining pathlib join semantics with placeholder paths",
    ),
    (
        "tools/outbound_send.py",
        'onto the channel root, and `Path("/a") / "C:/b"` yields',
        "a comment explaining pathlib join semantics with placeholder paths",
    ),
    (
        "shell/test/endpoint.test.js",
        '"/tmp/anything",',
        "a NEGATIVE fixture: arbitrary path text the endpoint verdict must refuse; never opened",
    ),
)


def drive_root_scratch(text: str) -> list[str]:
    r"""Every path in ``text`` whose parent is a drive root, bar the repo root and the sidecars.

    The allowlist is the PARENT: a child of ``E:\`` is a violation unless it is the repo
    root (``Clockspeed``) or ``Sidecars``, whatever its name looks like. A bare drive
    root with nothing joined to it names no child and is not a hit.
    """
    hits = [
        m.group(0)
        for m in DRIVE_CHILD.finditer(text)
        if m.group(1).lower() not in ALLOWED_DRIVE_CHILDREN
    ]
    hits.extend(
        m.group(0)
        for m in DRIVE_JOIN.finditer(text)
        if m.group(3).lower() not in ALLOWED_DRIVE_CHILDREN
    )
    return hits


def rooted_temp(text: str) -> list[str]:
    """Drive-less rooted paths into a temp directory named in ``text``."""
    return [m.group(0) for m in ROOTED_TEMP.finditer(text)]


def in_scope(rel: str) -> bool:
    """True when ``rel`` (a repo-relative POSIX path) is authored scratch-bearing text."""
    if rel.startswith(EXCLUDED_PREFIXES) or rel.rsplit("/", 1)[-1] in EXCLUDED_NAMES:
        return False
    if any(part in "/" + rel for part in EXCLUDED_PARTS):
        return False
    if rel.startswith(EXTENSIONLESS_PREFIXES):
        return True
    if not rel.endswith(TEXT_SUFFIXES):
        return False
    if rel.startswith("ops/") and rel.count("/") == 1:
        return rel.endswith(".json")  # ops/*.json; ops/__init__.py is not scratch-bearing
    return rel in SCOPE_FILES or rel.startswith(SCOPE_PREFIXES)


def _exempt(rel: str, line: str) -> bool:
    return any(rel == path and sub in line for path, sub, _why in EXEMPT_LINES)


def scan(files: dict[str, str], detector) -> list[str]:
    """``rel:lineno: match`` for every non-exempt hit of ``detector`` in the in-scope files."""
    found: list[str] = []
    for rel, text in sorted(files.items()):
        if not in_scope(rel):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if _exempt(rel, line):
                continue
            found.extend(f"{rel}:{number}: {hit}" for hit in detector(line))
    return found


def _population(repo_files: list[Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in repo_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if in_scope(rel) and path.is_file():
            out[rel] = path.read_text(encoding="utf-8", errors="replace")
    return out


@pytest.fixture(scope="module")
def population(repo_files: list[Path]) -> dict[str, str]:
    """The in-scope authored text, keyed by repo-relative path."""
    return _population(repo_files)


# --- arms a and b: the real population --------------------------------------------------


def test_population_is_not_empty_and_names_the_known_surfaces(population: dict[str, str]) -> None:
    """An empty scan passes for the wrong reason: assert the inventory carries the prompts."""
    for needed in (
        "CLAUDE.md",
        "tools/headless-queue.md",
        "tools/headless-inbox.md",
        ".claude/agents/builder.md",
        ".claude/commands/orchestrated-run.md",
        "tools/freeze_witness.py",
        "ops/loop/lanes.py",
        "config/ports.json",
        "shell/main.js",
        ".githooks/pre-commit",
        "ops/status_board.json",
    ):
        assert needed in population
    assert not any(rel.startswith("ops/fleet_kit/") for rel in population)
    assert not any("node_modules" in rel for rel in population)
    assert "shell/package-lock.json" not in population


def test_no_drive_root_scratch_path_is_authored(population: dict[str, str]) -> None:
    """Arm a: nothing tracked names a drive-root child, bar the repo root and the sidecars."""
    hits = scan(population, drive_root_scratch)
    assert hits == [], "drive-root path authored: " + "; ".join(hits)


def test_no_driveless_rooted_temp_path_is_authored(population: dict[str, str]) -> None:
    """Arm b: nothing tracked hands Python a rooted temp path with no drive letter."""
    hits = scan(population, rooted_temp)
    assert hits == [], "drive-less rooted temp path authored: " + "; ".join(hits)


# --- anti-vacuity: each detector is red against a planted violation ----------------------


@pytest.mark.parametrize(
    "planted",
    [
        r"E:\tmp_x",
        "C:/scratch/run1",
        f"E:/{_OLD_LANES}/lane-0",
        r"E:\cs-scratch",
        r"E:\tmp_hd\out",
        r"E:\cs_v24_check.log",
        "output goes to e:/Scratch and is read back",
        r"cd E:\worktrees && run",
        'cs_tmp = Path("E:/") / "cs-tmp"',
        'Path("E:/")/"cs-tmp"',
        "Path('E:\\\\') / 'cs-tmp'",
        'os.path.join("E:/", "run1")',
        'out = "E:/foo_out"',
        'root = "E:/work/x"',
        'data = "E:/Data"',
        r"E:\Data\run",
        f"D:/{_ROOT}2/x",
        f"E:/{_SIDE}x/CS",
    ],
)
def test_drive_root_detector_is_red_on_a_planted_violation(planted: str) -> None:
    """Arm a is live: each planted path whose parent is a drive root is found."""
    assert drive_root_scratch(planted) != []
    assert scan({"tools/planted.py": planted}, drive_root_scratch) != []


@pytest.mark.parametrize(
    "allowed",
    [
        rf"E:\{_ROOT}",
        rf"E:\{_ROOT}\.claude\worktrees\agent-x",
        f"E:/{_ROOT}/tools/x.py",
        f"e:/{_ROOT.lower()}/tools/x.py",
        rf"E:\{_SIDE_CS_BS}\Scratch\run1",
        f"E:/{_SIDE_CS}/Scratch/inbox/x.py",
        f"E:/{_SIDE_CS}/Worktree/lane-0",
        'Path("E:/") / "Sidecars"',
        f'Path("E:/") / "{_ROOT}" / "tools"',
        'os.path.join("E:/", "Sidecars", "CS")',
        'Path("E:/")',
        'root = "E:/"',
        "C:/",
        r"<sidecars>\CS\Scratch",
        "see the Windows Temp rule",
        "no path here at all",
    ],
)
def test_drive_root_detector_is_quiet_on_legitimate_text(allowed: str) -> None:
    """The arm allowlists the PARENT: the repo root, the sidecars root and a bare root pass."""
    assert drive_root_scratch(allowed) == []


@pytest.mark.parametrize(
    "planted",
    [
        "python tools/x.py --out /Users/<account>/AppData/Local/Temp/cs-kit-v30-a",
        r"dir = \Users\<account>\AppData\Local\Temp\run",
        "cp f /Windows/Temp/s04a1",
        r"log=\Windows\Temp\s04a1",
        "open('/tmp/scratch.txt')",
        r"path \tmp\out",
        "(/temp/run) is wrong",
    ],
)
def test_rooted_temp_detector_is_red_on_a_planted_violation(planted: str) -> None:
    """Arm b is live: each planted drive-less rooted temp path is found."""
    assert rooted_temp(planted) != []
    assert scan({"tools/planted.py": planted}, rooted_temp) != []


@pytest.mark.parametrize(
    "allowed",
    [
        r"C:\Users\<account>\AppData\Local\Temp\run",
        "tempfile lives under work/tmp/run",
        "~/tmp/run",
        "$HOME/tmp/run",
        "the tmp folder and a temp file",
        "https://example.invalid/tmp/x",
        "mount /tmpfs here",
        "no path here at all",
    ],
)
def test_rooted_temp_detector_is_quiet_on_legitimate_text(allowed: str) -> None:
    """The detector is narrow: a drive path, a relative segment and a URL pass."""
    assert rooted_temp(allowed) == []


@pytest.mark.parametrize(
    "rel",
    [
        "CLAUDE.md",
        "config/ports.json",
        "shell/main.js",
        "shell/lib/state.js",
        ".githooks/pre-commit",
        ".githooks/pre-push",
        "ops/status_board.json",
        ".claude/commands/orchestrated-run.md",
    ],
)
def test_scope_includes_the_surface(rel: str) -> None:
    """Config, the shell sources, the git hooks and ops/*.json are scanned."""
    assert in_scope(rel)


@pytest.mark.parametrize(
    "rel",
    [
        "shell/node_modules/x/index.js",
        "shell/dist/main.js",
        "shell/package-lock.json",
        "ops/fleet_kit/fleet_lanes.py",
        "ops/__init__.py",
        "docs/LEDGER.md",
        "tests/test_x.py",
    ],
)
def test_scope_excludes_vendored_generated_and_record_files(rel: str) -> None:
    """Vendored, generated, record and test files are not scanned."""
    assert not in_scope(rel)


def test_scan_is_red_on_a_planted_file_and_ignores_out_of_scope_files(tmp_path: Path) -> None:
    """A planted file in a tmp_path population is found; records, tests and the kit are not."""
    planted = r"scratch = 'E:\cs-scratch'" + "\n" + "tmp = '/tmp/x'\n"
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "planted.py").write_text(planted, encoding="ascii")
    files = {
        "tools/planted.py": (tmp_path / "tools" / "planted.py").read_text(encoding="ascii"),
        "docs/LEDGER.md": planted,
        "docs/history_notes.md": planted,
        "docs/_archive/old.md": planted,
        "tests/test_planted.py": planted,
        "ops/fleet_kit/fleet_lanes.py": planted,
        "shell/node_modules/x/y.js": planted,
    }
    a = scan(files, drive_root_scratch)
    b = scan(files, rooted_temp)
    assert a == ["tools/planted.py:1: E:\\cs-scratch"]
    assert b == ["tools/planted.py:2: /tmp"]


def test_scan_flags_a_planted_hook_and_a_planted_shell_file() -> None:
    """The widened scope is live: an extensionless hook and a shell source are graded."""
    hook = {".githooks/pre-commit": 'WORK="E:/foo_out"\n'}
    shell = {"shell/lib/x.js": 'const p = "E:/work/x";\n'}
    assert scan(hook, drive_root_scratch) == [".githooks/pre-commit:1: E:/foo_out"]
    assert scan(shell, drive_root_scratch) == ["shell/lib/x.js:1: E:/work"]


def test_exempt_entries_are_all_live() -> None:
    """Every EXEMPT_LINES entry still matches real lines, each of which a detector flags."""
    for rel, sub, why in EXEMPT_LINES:
        assert why
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        live = [line for line in text.splitlines() if sub in line]
        assert live, (rel, sub)
        for line in live:
            assert drive_root_scratch(line) or rooted_temp(line), (rel, sub)


# --- arm c: the derived lane worktree ----------------------------------------------------


def under(path: Path | str, root: Path | str) -> bool:
    """True when ``path`` lies strictly beneath ``root`` (lexically, case-insensitive)."""
    p = str(path).replace("\\", "/").rstrip("/").lower()
    r = str(root).replace("\\", "/").rstrip("/").lower()
    return p.startswith(r + "/")


def test_under_is_red_on_a_drive_root_worktree() -> None:
    """Anti-vacuity for arm c: the old drive-root-adjacent layout is not under the sidecar."""
    assert not under(f"E:/{_OLD_LANES}/lane-0", f"E:/{_SIDE_CS}")
    assert not under(f"E:/{_SIDE_CS}X/Worktree/lane-0", f"E:/{_SIDE_CS}")
    assert under(f"E:/{_SIDE_CS}/Worktree/lane-0", f"E:/{_SIDE_CS}")
    assert under(f"e:\\{_SIDE_CS_BS.lower()}\\Worktree\\lane-0", f"E:/{_SIDE_CS}")


def test_lane_worktrees_derive_under_the_sidecar_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arm c: ``lane_worktree`` lands under ``<sidecars>/CS/Worktree`` when that root exists."""
    default = str(lanes.kit_lanes().SIDECAR_DEFAULT)
    if os.name != "nt" or not default:
        pytest.skip("the kit's built-in sidecar root is a Windows default")
    sidecar = Path(default) / "CS"
    if not sidecar.is_dir():
        pytest.skip("no sidecar root on this machine (CI): the kit falls back by design")
    # The kit ignores its built-in default inside a pytest process; a lane runs outside one.
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("FLEET_SIDECAR_ROOT", raising=False)
    derived = lanes.lane_worktree(0)
    assert under(derived, sidecar / "Worktree"), "lane worktree is not under the sidecar root"


# --- arm d: freeze_witness --out ---------------------------------------------------------


def _freeze_witness():
    spec = importlib.util.spec_from_file_location(
        "cs1402_freeze_witness", REPO_ROOT / "tools" / "freeze_witness.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_freeze_out_refuses_a_cwd_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Arm d: ``--out x`` once wrote ``x`` at the drive root; it is now refused, nothing written."""
    witness = _freeze_witness()
    monkeypatch.chdir(tmp_path)
    rc = witness.main(["--root", str(tmp_path), "freeze", "--out", "x"])
    assert rc == REFUSED
    assert "absolute" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
