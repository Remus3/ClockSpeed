"""CS-1368 - the one-command kit repin: stable, fail-closed, and never touching a reason.

Every rewriting arm runs on a synthetic fixture tree in tmp_path, or on a COPY of this
tree's pin files and kit bytes, so no tracked file can be left mutated by a kill. The only
arm on the live tree is read-only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def _load_tool() -> Any:
    """Import the tool by path: `tools` has no __init__.py, and mypy reads it bare."""
    path = Path(__file__).resolve().parents[1] / "tools" / "repin_kit.py"
    spec = importlib.util.spec_from_file_location("clockspeed_repin_kit", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


repin_kit = _load_tool()

RENDER_REL = "tests/test_exception_rendering.py"
EXEMPT_REL = "tests/test_subprocess_timeouts.py"
PINS_REL = "tests/test_fleet_kit.py"
ALPHA_REL = "ops/fleet_kit/fleet_alpha.py"
TEXT_REL = "ops/fleet_kit/notes.txt"
PAD = "PADDING = 0\n"
OFF_SITE = "a row is not on a site of the previous bytes"
MOVED_SCOPE = "scope or handler changed"

ALPHA = """\
import subprocess


def first():
    try:
        return 1
    except ValueError as exc:
        return str(exc)


def second():
    try:
        return 2
    except KeyError as exc:
        return str(exc)


def launch():
    return subprocess.run(["x"], check=False)
"""
# The lines of the three sites in ALPHA above.
FIRST_LINE, SECOND_LINE, LAUNCH_LINE = 8, 15, 19


def _render_table(first: int = FIRST_LINE, second: int = SECOND_LINE) -> str:
    return (
        "VENDORED_RENDER_RESIDUALS = {\n"
        f'    ("{ALPHA_REL}", "str(exc)", {second}): (\n'
        '        "The second reason, moved 1 -> 2 on some bytes."\n'
        "    ),\n"
        f'    ("{ALPHA_REL}", "str(exc)", {first}): "The first reason.",\n'
        "}\n"
    )


def _exempt_table(line: int = LAUNCH_LINE) -> str:
    return (
        "EXEMPTIONS = {\n"
        f'    ("{ALPHA_REL}", "launch", "subprocess.run", {line}): "The launch reason.",\n'
        '    ("tools/not_kit.py", "main", "subprocess.run", 3): "Not a kit row at all.",\n'
        "}\n"
    )


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _manifest(kit: Path, version: int = 28) -> bytes:
    files = {
        path.name: _sha(path.read_bytes())
        for path in sorted(kit.iterdir())
        if path.is_file() and path.name != "MANIFEST.json"
    }
    body = {"common_block_sha256": files[Path(TEXT_REL).name], "files": files, "version": version}
    return (json.dumps(body, indent=1, sort_keys=True) + "\n").encode("ascii")


def _pins(manifest_sha: str, alpha_sha: str, text_sha: str, version: int = 28) -> str:
    return (
        'KIT_DIR = REPO_ROOT / "ops" / "fleet_kit"\n'
        'KIT_MANIFEST = KIT_DIR / "MANIFEST.json"\n'
        'KIT_COMMON = KIT_DIR / "notes.txt"\n'
        'KIT_ALPHA = KIT_DIR / "fleet_alpha.py"\n'
        f"KIT_VERSION = {version}\n"
        f'MANIFEST_SHA256 = "{manifest_sha}"\n'
        f'COMMON_SHA256 = "{text_sha}"\n'
        f'ALPHA_SHA256 = "{alpha_sha}"\n'
        "NOTE_FILE_SHA256 = {\n"
        "    KIT_COMMON.name: COMMON_SHA256,\n"
        "    KIT_ALPHA.name: ALPHA_SHA256,\n"
        "}\n"
    )


def _reseal(root: Path, version: int = 28) -> str:
    """Rewrite the fixture manifest over the current kit bytes; return its digest."""
    kit = root / "ops" / "fleet_kit"
    raw = _manifest(kit, version)
    (kit / "MANIFEST.json").write_bytes(raw)
    return _sha(raw)


def _tree(tmp_path: Path) -> Path:
    root = tmp_path / "tree"
    kit = root / "ops" / "fleet_kit"
    kit.mkdir(parents=True)
    (root / "tests").mkdir()
    (kit / "fleet_alpha.py").write_bytes(ALPHA.encode("ascii"))
    (kit / "notes.txt").write_bytes(b"notes\n")
    manifest_sha = _reseal(root)
    (root / RENDER_REL).write_bytes(_render_table().encode("ascii"))
    (root / EXEMPT_REL).write_bytes(_exempt_table().encode("ascii"))
    pins = _pins(manifest_sha, _sha(ALPHA.encode("ascii")), _sha(b"notes\n"))
    (root / PINS_REL).write_bytes(pins.encode("ascii"))
    return root


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _unchanged(_rel: str) -> bytes | None:
    """A previous-bytes reader with nothing to say - the fixture has no history."""
    return None


def _previous_of(root: Path) -> Callable[[str], bytes | None]:
    """A previous-bytes reader frozen at the fixture's bytes as they stand now."""
    frozen = _snapshot(root)

    def read(rel: str) -> bytes | None:
        return frozen.get(rel)

    return read


def _move_kit(root: Path, source: str) -> str:
    """Install new kit bytes and reseal the manifest; return the manifest digest."""
    (root / ALPHA_REL).write_bytes(source.encode("ascii"))
    return _reseal(root)


def _rows(root: Path, rel: str) -> str:
    return (root / rel).read_bytes().decode("ascii")


def test_a_matching_tree_is_a_no_op(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root)], previous=_unchanged)
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_OK, True)


def test_moved_rows_follow_their_function_and_reasons_stay_byte_identical(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD * 3 + ALPHA)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    expected_render = _render_table(FIRST_LINE + 3, SECOND_LINE + 3)
    expected_exempt = _exempt_table(LAUNCH_LINE + 3)
    assert code == repin_kit.EXIT_OK
    assert _rows(root, RENDER_REL) == expected_render
    assert _rows(root, EXEMPT_REL) == expected_exempt


def test_a_second_run_changes_nothing(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD * 3 + ALPHA)
    args = ["--root", str(root), "--expect-manifest-sha", new_sha]
    first_code = repin_kit.main(args, previous=previous)
    once = _snapshot(root)
    second_code = repin_kit.main(args, previous=previous)
    assert (first_code, second_code, _snapshot(root) == once) == (0, 0, True)


def test_rows_crossing_a_digit_width_and_each_other_land_exactly(tmp_path: Path) -> None:
    # 96 pads carry both render rows past 99 on one table: a sequential text replace
    # would corrupt the second splice; offsets taken from one parse cannot.
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD * 96 + ALPHA)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    assert code == repin_kit.EXIT_OK
    assert _rows(root, RENDER_REL) == _render_table(FIRST_LINE + 96, SECOND_LINE + 96)


def test_check_reports_a_moved_row_and_writes_nothing(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    _move_kit(root, PAD + ALPHA)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--check"], previous=previous)
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_STALE, True)


def test_a_pin_row_altered_in_a_fixture_fails_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    (root / RENDER_REL).write_bytes(_render_table(first=FIRST_LINE + 1).encode("ascii"))
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--check"], previous=previous)
    assert code == repin_kit.EXIT_REFUSED
    assert OFF_SITE in capsys.readouterr().err
    assert _snapshot(root) == before


def test_a_digest_pin_altered_in_a_fixture_fails_check(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    good = _rows(root, PINS_REL)
    bad = good.replace(_sha(ALPHA.encode("ascii")), "0" * 64)
    (root / PINS_REL).write_bytes(bad.encode("ascii"))
    code = repin_kit.main(["--root", str(root), "--check"], previous=_unchanged)
    assert code == repin_kit.EXIT_STALE
    write_code = repin_kit.main(["--root", str(root)], previous=_unchanged)
    assert (write_code, _rows(root, PINS_REL)) == (repin_kit.EXIT_OK, good)


def test_a_new_site_refuses_naming_file_and_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path)
    added = ALPHA + "\n\ndef third():\n    try:\n        return 3\n"
    added += "    except OSError as exc:\n        return str(exc)\n"
    new_sha = _move_kit(root, added)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha])
    captured = capsys.readouterr()
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)
    assert ALPHA_REL in captured.err
    assert "str(exc)" in captured.err


def test_a_removed_site_refuses(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    removed = ALPHA.replace('    return subprocess.run(["x"], check=False)\n', "    return 0\n")
    new_sha = _move_kit(root, removed)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha])
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_a_new_unbounded_site_in_a_file_with_no_row_refuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path)
    beta = b'import subprocess\n\n\ndef go():\n    return subprocess.run(["y"], check=False)\n'
    (root / "ops/fleet_kit/fleet_beta.py").write_bytes(beta)
    new_sha = _reseal(root)
    pins = _rows(root, PINS_REL).replace(
        "KIT_VERSION = 28\n", 'KIT_BETA = KIT_DIR / "fleet_beta.py"\nKIT_VERSION = 28\n'
    )
    pins += f'BETA_SHA256 = "{_sha(beta)}"\n'
    pins = pins.replace(
        "    KIT_ALPHA.name: ALPHA_SHA256,\n",
        "    KIT_ALPHA.name: ALPHA_SHA256,\n    KIT_BETA.name: BETA_SHA256,\n",
    )
    (root / PINS_REL).write_bytes(pins.encode("ascii"))
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha])
    captured = capsys.readouterr()
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)
    assert "fleet_beta.py" in captured.err
    assert "subprocess.run" in captured.err


def test_a_site_moving_to_another_function_refuses_at_equal_count(tmp_path: Path) -> None:
    # Same count, same shape, so line order alone would hand first's reason to the
    # renamed function. The enclosing function read off the previous bytes refuses it.
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, ALPHA.replace("def second", "def renamed"))
    before = _snapshot(root)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    # Lines are unmoved, so nothing needs placing and the rename is not this tool's to see.
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_OK, False)
    moved_sha = _move_kit(root, PAD + ALPHA.replace("def second", "def renamed"))
    held = _snapshot(root)
    moved = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", moved_sha], previous=previous
    )
    assert (moved, _snapshot(root) == held) == (repin_kit.EXIT_REFUSED, True)


def test_a_changed_source_line_at_a_moved_site_refuses(tmp_path: Path) -> None:
    # The site kept its function and shape but its line changed: the reason was MEASURED
    # on the old text, so a human re-measures it.
    root = _tree(tmp_path)
    previous = _previous_of(root)
    changed = ALPHA.replace(
        "    except KeyError as exc:\n        return str(exc)\n",
        "    except KeyError as exc:\n        return 'prefix ' + str(exc)\n",
    )
    new_sha = _move_kit(root, PAD + changed)
    before = _snapshot(root)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_a_moved_row_with_no_previous_bytes_refuses(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    new_sha = _move_kit(root, PAD + ALPHA)
    before = _snapshot(root)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=_unchanged
    )
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_expect_manifest_sha_refuses_a_manifest_that_does_not_hash_to_it(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", "a" * 64])
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_a_new_manifest_digest_is_never_pinned_without_the_note_sha(tmp_path: Path) -> None:
    # Otherwise MANIFEST_SHA256 is derived from the very bytes it witnesses.
    root = _tree(tmp_path)
    (root / "ops/fleet_kit/notes.txt").write_bytes(b"new notes\n")
    _reseal(root)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root)])
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_version_and_every_digest_are_rewritten_under_the_note_sha(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "ops/fleet_kit/notes.txt").write_bytes(b"new notes\n")
    new_sha = _reseal(root, version=29)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha])
    expected = _pins(new_sha, _sha(ALPHA.encode("ascii")), _sha(b"new notes\n"), version=29)
    assert (code, _rows(root, PINS_REL)) == (repin_kit.EXIT_OK, expected)


def test_a_kit_file_not_matching_the_manifest_refuses(tmp_path: Path) -> None:
    # A local edit to MAIN's bytes must never be pinned over.
    root = _tree(tmp_path)
    (root / "ops/fleet_kit/notes.txt").write_bytes(b"edited here\n")
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root)])
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_a_manifest_file_with_no_named_constant_refuses(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "ops/fleet_kit/fleet_gamma.js").write_bytes(b"// new\n")
    new_sha = _reseal(root)
    before = _snapshot(root)
    code = repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha])
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)


def test_a_rewrite_preserves_lf_and_output_is_names_and_counts_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD + ALPHA)
    repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous)
    captured = capsys.readouterr()
    carriage = [
        rel for rel in (RENDER_REL, EXEMPT_REL, PINS_REL) if b"\r" in (root / rel).read_bytes()
    ]
    leaked = str(tmp_path) in captured.out + captured.err
    reason_echoed = "reason" in captured.out
    assert (carriage, leaked, reason_echoed) == ([], False, False)
    assert RENDER_REL in captured.out


def test_no_scratch_file_survives_a_rewrite(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD + ALPHA)
    repin_kit.main(["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous)
    names = sorted(path.name for path in (root / "tests").iterdir())
    assert names == sorted(Path(rel).name for rel in (RENDER_REL, EXEMPT_REL, PINS_REL))


LAUNCH_BLOCK = 'def launch():\n    return subprocess.run(["x"], check=False)\n'
HEADER = "import subprocess\n\n\n"
TWO_HANDLERS = (
    HEADER + "def first():\n"
    "    try:\n"
    "        return 1\n"
    "    except ValueError as exc:\n"
    "        return str(exc)\n"
    "    except KeyError as exc:\n"
    "        return str(exc)\n\n\n" + LAUNCH_BLOCK
)
HANDLERS_SWAPPED = (
    HEADER + "def first():\n"
    "    try:\n"
    "        return 1\n"
    "    except KeyError as exc:\n"
    "        return str(exc)\n"
    "    except ValueError as exc:\n"
    "        return str(exc)\n\n\n" + LAUNCH_BLOCK
)
ALPHA_RUN = (
    "class Alpha:\n"
    "    def run(self):\n"
    "        try:\n"
    "            return 1\n"
    "        except ValueError as exc:\n"
    "            return str(exc)\n\n\n"
)
BETA_RUN = ALPHA_RUN.replace("Alpha", "Beta").replace("return 1", "return 2")
CLASSES_IN_ORDER = HEADER + ALPHA_RUN + BETA_RUN + LAUNCH_BLOCK
CLASSES_REORDERED = HEADER + BETA_RUN + ALPHA_RUN + LAUNCH_BLOCK
VALUE_THEN_KEY = (
    HEADER + "def first():\n"
    "    try:\n"
    "        return 1\n"
    "    except ValueError as exc:\n"
    "        return str(exc)\n"
    "    try:\n"
    "        return 2\n"
    "    except KeyError as exc:\n"
    "        return str(exc)\n\n\n" + LAUNCH_BLOCK
)
KEY_THEN_OS = (
    HEADER + "def first():\n"
    "    try:\n"
    "        return 2\n"
    "    except KeyError as exc:\n"
    "        return str(exc)\n"
    "    try:\n"
    "        return 3\n"
    "    except OSError as exc:\n"
    "        return str(exc)\n\n\n" + LAUNCH_BLOCK
)


def _lines_holding(source: str, needle: str) -> list[int]:
    return [number for number, line in enumerate(source.splitlines(), start=1) if needle in line]


def _tree_of(tmp_path: Path, source: str) -> Path:
    """A fixture tree pinned, row by row, to the two handlers and the call of ``source``."""
    root = _tree(tmp_path)
    raw = source.encode("ascii")
    (root / ALPHA_REL).write_bytes(raw)
    manifest_sha = _reseal(root)
    first, second = _lines_holding(source, "return str(exc)")
    (root / RENDER_REL).write_bytes(_render_table(first, second).encode("ascii"))
    launch = _lines_holding(source, "subprocess.run(")[0]
    (root / EXEMPT_REL).write_bytes(_exempt_table(launch).encode("ascii"))
    pins = _pins(manifest_sha, _sha(raw), _sha(b"notes\n"))
    (root / PINS_REL).write_bytes(pins.encode("ascii"))
    return root


@pytest.mark.parametrize(
    ("old", "new"),
    [
        pytest.param(TWO_HANDLERS, HANDLERS_SWAPPED, id="A-handlers-swapped"),
        pytest.param(CLASSES_IN_ORDER, CLASSES_REORDERED, id="B-same-named-methods-reordered"),
        pytest.param(VALUE_THEN_KEY, KEY_THEN_OS, id="C-one-site-out-one-in-count-kept"),
    ],
)
def test_a_re_point_onto_another_scope_or_handler_refuses_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], old: str, new: str
) -> None:
    # Same count, same shape, same source line at every site, so only the handler's
    # exception or the qualified scope tells these rows they would land on the wrong site.
    root = _tree_of(tmp_path, old)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD + new)
    before = _snapshot(root)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    captured = capsys.readouterr()
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)
    assert MOVED_SCOPE in captured.err
    assert ALPHA_REL in captured.err


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(TWO_HANDLERS, id="A"),
        pytest.param(CLASSES_IN_ORDER, id="B"),
        pytest.param(VALUE_THEN_KEY, id="C"),
    ],
)
def test_a_plain_move_of_each_refusal_fixture_still_re_points(tmp_path: Path, source: str) -> None:
    # The control: each refusal above is the reorder, not the fixture.
    root = _tree_of(tmp_path, source)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD + source)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    first, second = _lines_holding(source, "return str(exc)")
    assert code == repin_kit.EXIT_OK
    assert _rows(root, RENDER_REL) == _render_table(first + 1, second + 1)


def test_the_write_applies_to_the_planned_bytes_not_a_second_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Offsets belong to the bytes they were parsed from; a second read can shift them.
    root = _tree(tmp_path)
    previous = _previous_of(root)
    new_sha = _move_kit(root, PAD + ALPHA)
    real_plan = repin_kit.plan

    def plan_then_edit(*args: Any, **kwargs: Any) -> Any:
        planned = real_plan(*args, **kwargs)
        target = root / RENDER_REL
        target.write_bytes(b"# written after the plan\n" + target.read_bytes())
        return planned

    monkeypatch.setattr(repin_kit, "plan", plan_then_edit)
    code = repin_kit.main(
        ["--root", str(root), "--expect-manifest-sha", new_sha], previous=previous
    )
    assert code == repin_kit.EXIT_OK
    assert _rows(root, RENDER_REL) == _render_table(FIRST_LINE + 1, SECOND_LINE + 1)


def test_a_failed_temp_write_leaves_no_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "pin.py"
    target.write_bytes(b"old\n")

    def broken(self: Path, _data: bytes) -> int:
        with self.open("wb") as handle:
            handle.write(b"par")
        raise OSError("no space")

    monkeypatch.setattr(Path, "write_bytes", broken)
    with pytest.raises(OSError, match="no space"):
        repin_kit.write_atomic(target, b"new\n")
    monkeypatch.undo()
    names = sorted(path.name for path in tmp_path.iterdir())
    assert (names, target.read_bytes()) == (["pin.py"], b"old\n")


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param(OSError("not a share refusal"), id="other-oserror"),
        pytest.param(PermissionError("still shared"), id="retries-exhausted"),
    ],
)
def test_a_failed_rename_leaves_no_scratch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: OSError
) -> None:
    target = tmp_path / "pin.py"
    target.write_bytes(b"old\n")

    def broken(_self: Path, _target: Path) -> Path:
        raise failure

    monkeypatch.setattr(Path, "replace", broken)
    monkeypatch.setattr(repin_kit, "REPLACE_BACKOFF_S", 0)
    with pytest.raises(OSError, match=r"refusal|shared"):
        repin_kit.write_atomic(target, b"new\n")
    monkeypatch.undo()
    names = sorted(path.name for path in tmp_path.iterdir())
    assert (names, target.read_bytes()) == (["pin.py"], b"old\n")


def test_a_missing_pytest_is_a_one_line_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _tree(tmp_path)
    before = _snapshot(root)

    def absent(_name: str) -> Any:
        raise ModuleNotFoundError("No module named 'pytest'", name="pytest")

    monkeypatch.setattr(repin_kit, "importlib", SimpleNamespace(import_module=absent))
    code = repin_kit.main(["--root", str(root), "--check"], previous=_unchanged)
    captured = capsys.readouterr()
    err_lines = captured.err.strip().splitlines()
    assert (code, _snapshot(root) == before) == (repin_kit.EXIT_REFUSED, True)
    assert len(err_lines) == 1
    assert "pytest" in captured.err
    assert str(tmp_path) not in captured.err


def _copy_of_this_tree(tmp_path: Path) -> Path:
    root = tmp_path / "copy"
    source = repin_kit.REPO_ROOT
    (root / "tests").mkdir(parents=True)
    (root / "ops").mkdir()
    shutil.copytree(
        source / "ops" / "fleet_kit",
        root / "ops" / "fleet_kit",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    for rel in (RENDER_REL, EXEMPT_REL, PINS_REL):
        (root / rel).write_bytes((source / rel).read_bytes())
    return root


def test_todays_tree_is_stable_byte_for_byte_across_two_runs(tmp_path: Path) -> None:
    root = _copy_of_this_tree(tmp_path)
    before = _snapshot(root)
    first = repin_kit.main(["--root", str(root)], previous=_unchanged)
    after_first = _snapshot(root)
    second = repin_kit.main(["--root", str(root)], previous=_unchanged)
    identical = (after_first == before, _snapshot(root) == before)
    assert (first, second, identical) == (0, 0, (True, True))


def test_a_row_altered_in_a_copy_of_todays_tree_fails_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_of_this_tree(tmp_path)
    frozen = _previous_of(root)
    target = root / EXEMPT_REL
    source = target.read_bytes()
    row = b'"ops/fleet_kit/fleet_rewrite.py", "run", "subprocess.run", '
    assert source.count(row) == 1
    index = source.index(row) + len(row)
    target.write_bytes(source[:index] + b"1" + source[index:])
    code = repin_kit.main(["--root", str(root), "--check"], previous=frozen)
    assert code == repin_kit.EXIT_REFUSED
    assert OFF_SITE in capsys.readouterr().err


def test_the_live_tree_passes_check() -> None:
    assert repin_kit.main(["--check"], previous=_unchanged) == repin_kit.EXIT_OK


def test_the_git_previous_reader_answers_bytes_or_none() -> None:
    read = repin_kit.git_previous(repin_kit.REPO_ROOT, "HEAD")
    found = read("ops/fleet_kit/LICENSE")
    assert read("ops/fleet_kit/no_such_file.py") is None
    assert found is not None
    assert found == (repin_kit.REPO_ROOT / "ops" / "fleet_kit" / "LICENSE").read_bytes()
