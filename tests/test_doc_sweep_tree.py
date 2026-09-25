"""CS-1184 - the doc sweep as a live gate over THIS repository's tracked markdown.

``tools/doc_sweep.py`` is otherwise called by nothing on push, so a clean verdict
there would be a claim nobody re-measures. This module runs it over the real
tracked tree under the suite - which the pre-push hook and CI both run - and
asserts exit 0.

A GREEN GATE IS ONLY EVIDENCE BESIDE A CONTROL THAT CAN REDDEN IT. The control
copies every tracked file into a throwaway repository, proves the copy sweeps
to the same clean verdict, then COMMITS one planted orphan and proves the same
entry point turns red on it. The plant goes into a copy rather than the real
tree because the population is what git tracks: an untracked plant in the real
tree would be invisible, and a committed one would not be a test.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import doc_sweep  # noqa: E402
from toolpath import resolve_tool  # noqa: E402

GIT_TIMEOUT: Final = 120
#: Built at import time from parts so the literal plant path never appears in this tracked
#: file - a whole spelling here would count as a reference and hide the orphan (CS-1184).
PLANT: Final = "/".join(("docs", "zz-planted" + "-orphan.md"))


def _git_env() -> dict[str, str]:
    """Return the environment minus inherited ``GIT_`` variables, config isolated."""
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def _git(root: Path, *args: str) -> None:
    """Run git in ``root`` and fail the test on a non-zero exit."""
    git = resolve_tool("git")
    if git is None:
        pytest.skip("git is not on PATH; the control repository cannot be built")
    completed = subprocess.run(
        [
            git,
            "-C",
            str(root),
            "-c",
            "user.name=doc-sweep-test",
            "-c",
            "user.email=doc-sweep-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
        env=_git_env(),
    )
    assert completed.returncode == 0, completed.stderr


def _findings(out: str) -> list[str]:
    """Return the finding lines of a sweep's stdout."""
    return [line for line in out.splitlines() if not line.startswith("doc_sweep:")]


def test_the_real_tracked_tree_sweeps_clean(capsys: pytest.CaptureFixture[str]) -> None:
    code = doc_sweep.main(["--root", str(REPO_ROOT)])
    out = capsys.readouterr().out
    findings = _findings(out)
    assert findings == []
    assert code == doc_sweep.EXIT_CLEAN


def test_a_planted_orphan_reddens_a_copy_of_the_real_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    copy = tmp_path / "copy"
    copy.mkdir()
    copied = 0
    for name in doc_sweep.tracked_files(REPO_ROOT):
        source = REPO_ROOT / name
        if not source.is_file():
            continue
        target = copy / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied += 1
    assert copied > 0
    _git(copy, "init", "-q")
    _git(copy, "add", "-A")
    _git(copy, "commit", "-q", "-m", "copy")

    pristine = doc_sweep.main(["--root", str(copy)])
    pristine_findings = _findings(capsys.readouterr().out)
    assert pristine_findings == []
    assert pristine == doc_sweep.EXIT_CLEAN

    (copy / PLANT).write_bytes(b"# Planted\n")
    _git(copy, "add", PLANT)
    _git(copy, "commit", "-q", "-m", "plant")
    planted = doc_sweep.main(["--root", str(copy)])
    planted_findings = _findings(capsys.readouterr().out)
    assert planted_findings == [f"{doc_sweep.ORPHAN} {PLANT}: no other tracked file references it"]
    assert planted == doc_sweep.EXIT_FINDINGS
