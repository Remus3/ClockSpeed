"""CS-1297 - a canary-driven inner pytest keeps its temp root under the arm's tmp_path.

THE DEFECT. ``tests/test_hook_env_echo.py`` plants a ``cs814canary`` marker as
the account name of every child it spawns, and its pre-push arms run a nested
pytest through the real hook. That nested pytest names its base temporary
directory ``pytest-of-<account>`` under the SYSTEM temporary directory, so every
run left a fresh ``pytest-of-cs814canary<hex>`` root at the top of temp that
nothing ever removed.

THE ARM drives exactly that mechanism without the hook: a minimal pytest run
under each module's own ``child_env``, whose one test records where its
``tmp_path`` landed. It must land under the OUTER arm's ``tmp_path``, and no
root named for this run's markers may appear in the system temporary directory.
Every observation is reduced to a bool or a count before an assertion sees it,
so no assertion renders a path or an environment value.

RESOURCE LIFETIME. A root the inner run may have left at the top of temp is
named for THIS process's markers alone, so the finalizer removes only what this
arm made - never another run's root and never a pre-existing one.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

import tests.test_hook_env_echo as echo
import tests.test_probe_refusal_output as probe

CALL_TIMEOUT: Final = 300
SEEN_NAME: Final = "seen.txt"
INNER_TEST: Final = (
    b"from pathlib import Path\n"
    b"\n"
    b"\n"
    b"def test_records_its_tmp_path(tmp_path: Path) -> None:\n"
    b'    target = Path(__file__).parent / "' + SEEN_NAME.encode("ascii") + b'"\n'
    b'    target.write_text(str(tmp_path.resolve()), encoding="utf-8")\n'
)
MODULES: Final = {"hook_env_echo": echo, "probe_refusal_output": probe}


def marker_roots(module: ModuleType) -> list[Path]:
    """Top-level temp roots named for one of ``module``'s markers, this run only."""
    top = Path(tempfile.gettempdir())
    return [top / ("pytest-of-" + marker) for marker in module.MARKERS]


def _writable_retry(func: Callable[..., object], path: str, _exc: BaseException) -> None:
    """Clear the read-only bit on ``path`` and retry the removal once."""
    Path(path).chmod(stat.S_IWRITE)
    func(path)


@pytest.fixture
def no_marker_roots_left() -> Iterator[None]:
    """Remove any root this arm's inner run left at the top of temp."""
    yield
    for module in MODULES.values():
        for root in marker_roots(module):
            if root.is_dir():
                shutil.rmtree(root, onexc=_writable_retry)


@pytest.mark.usefixtures("no_marker_roots_left")
@pytest.mark.parametrize("name", sorted(MODULES))
def test_the_inner_pytest_temp_root_stays_under_tmp_path(tmp_path: Path, name: str) -> None:
    """The nested run's tmp_path lands under the arm's tmp_path, never top of temp."""
    module = MODULES[name]
    before = sum(1 for root in marker_roots(module) if root.exists())
    inner = tmp_path / "inner"
    inner.mkdir()
    (inner / "pytest.ini").write_bytes(b"[pytest]\n")
    (inner / "test_inner.py").write_bytes(INNER_TEST)
    env = module.child_env(tmp_path)
    for key in [key for key in env if key.upper().startswith("PYTEST_")]:
        env.pop(key)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_inner.py"],
        cwd=str(inner),
        capture_output=True,
        env=env,
        timeout=CALL_TIMEOUT,
        check=False,
    )
    code = proc.returncode
    assert code == 0, f"{name}: the inner pytest exited {code}"
    seen_file = inner / SEEN_NAME
    recorded = seen_file.is_file()
    assert recorded, f"{name}: the inner test recorded no tmp_path"
    seen = Path(seen_file.read_text(encoding="utf-8"))
    under = seen.is_relative_to(tmp_path.resolve())
    assert under, f"{name}: the inner tmp_path landed outside the arm's tmp_path"
    after = sum(1 for root in marker_roots(module) if root.exists())
    assert after == before, f"{name}: {after - before} new marker root(s) at the top of temp"
