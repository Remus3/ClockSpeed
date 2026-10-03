"""CS-1219 - the adjudication candidate freeze has a mechanical witness.

`tools/freeze_witness.py freeze` records the candidate an adjudication is
dispatched over; `check` refuses a verdict taken over a tree that moved under
it. Every arm runs in a throwaway git repository under ``tmp_path`` - nothing
here reads or writes this checkout's own bytecode.

THE TWO ARMS THE ACCEPTANCE CLAUSE NAMES:

    test_an_uncommitted_tracked_edit_reddens_the_witness
    test_a_swapped_pyc_alone_reddens_the_witness

The second one asserts its own precondition: porcelain reports the tree clean
and every tracked file is byte-identical, so the only thing that moved is the
gitignored bytecode.
"""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "freeze_witness.py"

_TIMEOUT = 120
EXIT_MOVED = 1
EXIT_REFUSED = 2


def _env() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key.upper().startswith("GIT_"):
            del env[key]
    return env


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        [
            "git",
            "-c",
            "user.name=witness",
            "-c",
            "user.email=witness@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        env=_env(),
        timeout=_TIMEOUT,
        check=False,
    )
    rc = proc.returncode
    assert rc == 0, f"git {args[0]} exited {rc}"
    return proc.stdout.decode("ascii", "replace")


def _tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        env=_env(),
        timeout=_TIMEOUT,
        check=False,
    )


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    pkg = root / "pkg"
    pkg.mkdir(parents=True)
    (root / ".gitignore").write_bytes(b"__pycache__/\n")
    (pkg / "__init__.py").write_bytes(b"")
    (pkg / "mod.py").write_bytes(b"VALUE = 1\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    cache = pkg / "__pycache__"
    cache.mkdir()
    py_compile.compile(str(pkg / "mod.py"), cfile=str(cache / "mod.pyc"), doraise=True)
    return root


def _freeze(root: Path, tmp_path: Path) -> Path:
    record = tmp_path / "witness.json"
    rc = _tool("--root", str(root), "freeze", "--out", str(record)).returncode
    assert rc == 0
    assert record.is_file()
    return record


def _check(root: Path, record: Path) -> tuple[int, str]:
    # A scalar pair, never the CompletedProcess: assertion rendering would echo
    # its argv, and that argv carries temp paths under a home directory.
    proc = _tool("--root", str(root), "check", str(record))
    return proc.returncode, proc.stdout + proc.stderr


def _tracked_bytes(root: Path) -> dict[str, bytes]:
    names = _git(root, "ls-files", "-z").split("\0")
    return {n: (root / n).read_bytes() for n in names if n}


def test_an_unmoved_candidate_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    rc, out = _check(root, record)
    assert rc == 0, out


def test_an_uncommitted_tracked_edit_reddens_the_witness(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 2\n")
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "tree moved" in out
    assert "bytecode moved" not in out


def test_a_stat_identical_edit_reddens_the_witness(tmp_path: Path) -> None:
    """Same size, same mtime: a witness trusting git's stat cache would miss it."""
    root = _repo(tmp_path)
    mod = root / "pkg" / "mod.py"
    stat = mod.stat()
    record = _freeze(root, tmp_path)
    mod.write_bytes(b"VALUE = 7\n")
    os.utime(mod, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "tree moved" in out


def test_a_swapped_pyc_alone_reddens_the_witness(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    before = _tracked_bytes(root)
    pyc = root / "pkg" / "__pycache__" / "mod.pyc"
    donor = tmp_path / "donor.py"
    donor.write_bytes(b"VALUE = 99\n")
    swapped = tmp_path / "donor.pyc"
    py_compile.compile(str(donor), cfile=str(swapped), doraise=True)
    assert swapped.read_bytes() != pyc.read_bytes()
    pyc.write_bytes(swapped.read_bytes())
    # Precondition: nothing a porcelain check can see has moved.
    assert _git(root, "status", "--porcelain") == ""
    assert _tracked_bytes(root) == before
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "bytecode moved" in out
    assert "tree moved" not in out


def test_a_new_pyc_reddens_the_witness(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    cache = root / "pkg" / "__pycache__"
    py_compile.compile(str(root / "pkg" / "__init__.py"), cfile=str(cache / "i.pyc"), doraise=True)
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "bytecode moved" in out


def test_a_tree_identical_commit_is_not_a_move(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    _git(root, "commit", "-q", "--allow-empty", "-m", "no tree change")
    rc, out = _check(root, record)
    assert rc == 0, out


def test_committing_an_edit_is_a_move(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 3\n")
    _git(root, "commit", "-q", "-am", "edit")
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "tree moved" in out


def test_an_untracked_unignored_file_is_a_move(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    record = _freeze(root, tmp_path)
    (root / "pkg" / "new.py").write_bytes(b"X = 1\n")
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "tree moved" in out


def test_freezing_leaves_the_real_index_untouched(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "pkg" / "new.py").write_bytes(b"X = 1\n")
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 5\n")
    status = _git(root, "status", "--porcelain")
    _freeze(root, tmp_path)
    assert _git(root, "status", "--porcelain") == status
    assert _git(root, "diff", "--cached", "--name-only") == ""


def test_a_crlf_flip_under_eol_lf_reddens_the_witness(tmp_path: Path) -> None:
    """`* text=auto eol=lf` normalises on add, so a git tree object misses this."""
    root = _repo(tmp_path)
    (root / ".gitattributes").write_bytes(b"* text=auto eol=lf\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "attributes")
    record = _freeze(root, tmp_path)
    mod = root / "pkg" / "mod.py"
    mod.write_bytes(mod.read_bytes().replace(b"\n", b"\r\n"))
    rc, out = _check(root, record)
    assert rc == EXIT_MOVED
    assert "tree moved" in out


def _object_files(root: Path) -> list[str]:
    objects = root / ".git" / "objects"
    return sorted(p.relative_to(objects).as_posix() for p in objects.rglob("*") if p.is_file())


def test_freezing_writes_no_object_into_the_repository(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "pkg" / "untracked.py").write_bytes(b"Y = 2\n")
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 6\n")
    before = _object_files(root)
    record = _freeze(root, tmp_path)
    _check(root, record)
    after = _object_files(root)
    assert after == before


def test_a_malformed_record_is_refused(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"{not json")
    rc, _out = _check(root, bad)
    assert rc == EXIT_REFUSED
