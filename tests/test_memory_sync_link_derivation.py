"""CS-892 - the memory sync tool consumes the link derivation it used to copy.

WHAT WAS WRONG. `tools/drift_guard.py` and `tools/memory_sync.py` each declared
their own `_WIKILINK`, `_MDLINK` and `_BACKTICK` patterns and their own
`_link_targets`, byte-identical in both files, and each ran its own
transitive-through-index reachability walk over them. CS-890 repaired the guard's
copy. Nothing reached the sync tool's, because it was on no slice's write-list,
and nothing in the tree compared the two. The copies agreed on the day CS-892 was
filed; what had changed is that they had stopped being maintained together, so the
next edit to either would land in one copy and the two would silently disagree.

WHY ONE OWNER RATHER THAN AN AGREEMENT ASSERTION, which is the other branch the
item's acceptance allows. CS-885 kept four copies of the path-free OSError clone
and made them compare on every run, and its module records WHY: the clearance that
makes a copy safe is structurally same-module, so collapsing to a shared owner
would have dropped every live site from `closed-pathless` to `unproven`. No such
clearance exists over the link derivation - nothing in the tree grades
`_link_targets` by the module it is defined in - so the reason that forced four
copies to stay four does not reach here, and the stronger branch is available.
A single owner removes the drift class; an agreement assertion only detects it.

HOW THE ARMS ARE WRITTEN, AND WHY NOT BY NAME. An arm that asserted
`memory_sync.link_targets is drift_guard.link_targets` would be a spelling
measure - `memory/a-guard-can-measure-spelling.md` - and would report a clean
verdict about the wrong question the moment a name moved. The arms here are
behavioural and structural instead: a recording spy proves the walk RUNS through
the guard's derivation, a shape TAUGHT to the guard alone is asserted to reach the
sync tool's answer, and an AST pass proves no regex literal is declared in both
files. The AST pass carries a planted positive, because an extractor blind to its
subject reports an empty intersection for that reason alone.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
MEMORY_SYNC_SOURCE = TOOLS_DIR / "memory_sync.py"
DRIFT_GUARD_SOURCE = TOOLS_DIR / "drift_guard.py"


def _load(name: str, source: Path) -> ModuleType:
    """Load a tool by path under ``name``, the way the rest of the suite does."""
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        pytest.fail(f"cannot load {source.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


memory_sync = _load("clockspeed_memory_sync", MEMORY_SYNC_SOURCE)


def _owner_of(module: ModuleType) -> ModuleType:
    """The guard module the sync tool derives link tokens through."""
    owner = getattr(module, "drift_guard", None)
    assert owner is not None, (
        "tools/memory_sync.py declares its own link derivation instead of "
        "consuming the one tools/drift_guard.py owns - CS-892"
    )
    return cast("ModuleType", owner)


def _write_store(root: Path, index_body: str, leaves: dict[str, str]) -> list[Path]:
    """Write a memory store and return its ordinary leaf paths."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "MEMORY.md").write_text(index_body, encoding="utf-8")
    written = []
    for stem, body in leaves.items():
        leaf = root / f"{stem}.md"
        leaf.write_text(body, encoding="utf-8")
        written.append(leaf)
    return written


def _compiled_literals_of_text(text: str) -> set[str]:
    """Every module-level regex literal the source compiles, by pattern text.

    Read from the AST rather than from the imported module, so a pattern that
    is declared but never referenced still counts as a declaration.
    """
    found: set[str] = set()
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        attr = func.attr if isinstance(func, ast.Attribute) else None
        if attr != "compile" or not call.args:
            continue
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.add(first.value)
    return found


def _compiled_literals(source: Path) -> set[str]:
    """The same extractor over a tracked file."""
    return _compiled_literals_of_text(source.read_text(encoding="utf-8"))


def test_the_three_link_shapes_still_reach_a_leaf(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    index = "\n".join(
        (
            "# Memory Index",
            "- [[wiki-leaf]] a wikilink",
            "- [md](md-leaf.md) a markdown link",
            "- `tick-leaf` a backticked span",
        )
    )
    leaves = _write_store(
        root,
        index,
        {"wiki-leaf": "one", "md-leaf": "two", "tick-leaf": "three"},
    )
    unreachable, note = memory_sync.reachability(root, leaves)
    assert note == ""
    assert [leaf.stem for leaf in unreachable] == []


def test_an_unindexed_leaf_is_still_reported_unreachable(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    leaves = _write_store(
        root,
        "# Memory Index\n- [[named]] the only entry\n",
        {"named": "one", "orphan": "two"},
    )
    unreachable, _note = memory_sync.reachability(root, leaves)
    assert [leaf.stem for leaf in unreachable] == ["orphan"]


def test_the_walk_runs_through_the_guards_own_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner_of(memory_sync)
    seen: list[str] = []
    real: Callable[[str], set[str]] = owner.link_targets

    def spy(text: str) -> set[str]:
        seen.append(text)
        return real(text)

    monkeypatch.setattr(owner, "link_targets", spy)
    root = tmp_path / "memory"
    leaves = _write_store(root, "# Memory Index\n- [[named]] entry\n", {"named": "one"})
    memory_sync.reachability(root, leaves)
    assert [text for text in seen if "named" in text], (
        "the sync walk never called the guard's link derivation, so it is still "
        "reading links through a second copy - CS-892"
    )


def test_a_shape_taught_to_the_owner_alone_reaches_the_sync_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The acceptance arm: teaching ONE copy a link shape must not diverge.

    The shape is taught to the owner and to nothing else. With a second copy in
    `tools/memory_sync.py` the leaf below reads as unreachable, which is exactly
    the silent disagreement CS-892 was filed against.
    """
    owner = _owner_of(memory_sync)
    real: Callable[[str], set[str]] = owner.link_targets

    def taught(text: str) -> set[str]:
        tokens = set(real(text))
        for chunk in text.split("<<")[1:]:
            head, delimiter, _rest = chunk.partition(">>")
            if delimiter:
                tokens.add(head.strip().lower())
        return tokens

    monkeypatch.setattr(owner, "link_targets", taught)
    root = tmp_path / "memory"
    leaves = _write_store(root, "# Memory Index\n- <<taught-leaf>> entry\n", {"taught-leaf": "one"})
    unreachable, _note = memory_sync.reachability(root, leaves)
    assert [leaf.stem for leaf in unreachable] == [], (
        "a link shape taught to the guard's derivation did not reach the sync "
        "walk, so the two are separate copies - CS-892"
    )


def test_no_regex_literal_is_declared_in_both_tools() -> None:
    shared = _compiled_literals(MEMORY_SYNC_SOURCE) & _compiled_literals(DRIFT_GUARD_SOURCE)
    assert shared == set(), (
        "these regex literals are declared in both tools/memory_sync.py and "
        f"tools/drift_guard.py: {sorted(shared)} - CS-892"
    )


def test_the_duplication_extractor_sees_a_planted_duplicate() -> None:
    """Anti-vacuity: the arm above must be able to FAIL, not merely be blind."""
    left = 'import re\nA = re.compile(r"shared-shape")\n'
    right = 'import re\nB = re.compile(r"shared-shape")\nC = re.compile(r"private")\n'
    shared = _compiled_literals_of_text(left) & _compiled_literals_of_text(right)
    assert shared == {"shared-shape"}


def test_the_owner_is_the_tracked_guard_and_not_a_third_copy() -> None:
    owner = _owner_of(memory_sync)
    assert owner.__file__ is not None
    assert Path(owner.__file__).resolve() == DRIFT_GUARD_SOURCE.resolve()
