#!/usr/bin/env python3
"""Tests for tools/doc_budget.py, and the CS-475 checkout-boundary control.

CS-475 is why the control in this module creates a real linked worktree. The
defect it grades was MEASURED, not inferred: the tool derived its population
with ``root.rglob("CLAUDE.md")`` and pruned only by directory NAME, so it
descended into every linked git worktree sitting inside the repository and
measured that other checkout's copy of a budgeted file as if it were this
one's. A throwaway worktree moved the reported ``measured:`` count by one on
create and back on remove.

TWO PROPERTIES OF THE CONTROL ARE LOAD-BEARING and neither is decoration.

  1. It creates a GENUINE linked worktree with ``git worktree add`` and proves
     the planted copy is on disk before it grades anything. A control that
     silently created nothing would pass trivially and prove nothing, which is
     exactly the shape it exists to rule out.
  2. It plants at a location that is NOT under ``.claude/worktrees/`` as well
     as one that is. The acceptance names that directory because that is where
     the harness put them on the day the defect was measured - but a fix that
     recognised that NAME would pass a control that only ever looked there and
     would fail the moment a harness moved its worktrees. Planting outside it
     is what separates a stated boundary rule from a special-cased name.

The planted copy is deliberately made LARGER THAN ITS OWN BUDGET before the
graded measurement. That turns a silent count drift into a verdict flip, so a
regression cannot be read as a rounding difference. It is the same mechanism
as the hazard the item names - a stale copy reported inside budget while the
tracked file is over - driven in the direction that is loud.

The worktree is removed on every exit path including a failing assertion, and
``git worktree prune`` runs behind the removal, because leaving one live would
hand the next run a different repository than the one this one measured.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_BUDGET_SOURCE = REPO_ROOT / "tools" / "doc_budget.py"

GIT_TIMEOUT = 120

# A declared reason shorter than this is a label, not a reason.
MINIMUM_STATED_REASON = 40

# The two plant sites. The first is where the harness put them when the defect
# was measured; the second is deliberately nowhere near it.
#
# BOTH CARRY THIS PROCESS'S PID. tier2 runs `pytest tests -q -n auto`, so two
# workers can be inside this module at once; a shared plant path would let one
# worker's teardown delete the other's worktree mid-assertion. The pid makes
# each plant private to the process that created it.
HARNESS_SITE = f".claude/worktrees/cs475-control-{os.getpid()}"
ELSEWHERE_SITE = f"cs475-control-elsewhere-{os.getpid()}"
PLANT_SITES = (HARNESS_SITE, ELSEWHERE_SITE)


def _load_doc_budget() -> ModuleType:
    """Load tools/doc_budget.py by path.

    tools/ is a directory of entry-point scripts rather than an importable
    package, so the module is loaded from its file the same way
    tools/drift_guard.py loads it.

    Returns:
        The loaded module.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_doc_budget", DOC_BUDGET_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {DOC_BUDGET_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


doc_budget = _load_doc_budget()


# ---------------------------------------------------------------------------
# Population helpers - what "the measured population" means here
# ---------------------------------------------------------------------------


def _population(root: Path) -> list[str]:
    """The display paths of every row the tool actually measured."""
    return sorted(row["file"] for row in doc_budget.evaluate(root) if row["status"] != "MISSING")


# ---------------------------------------------------------------------------
# The real linked worktree
# ---------------------------------------------------------------------------


def _git_is_usable() -> str:
    """Return an empty string when git can drive this checkout, else a reason."""
    if shutil.which("git") is None:
        return "git is not on PATH"
    try:
        done = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"git could not be run: {type(exc).__name__}"
    if done.returncode != 0 or done.stdout.strip() != "true":
        return "the test tree is not a git checkout"
    return ""


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
    )


@contextlib.contextmanager
def _linked_worktree(relative: str) -> Iterator[Path]:
    """Create a genuine linked worktree at ``relative`` inside the repository.

    It has to sit INSIDE the repository, because the defect is that the walk
    descends into it - a worktree outside the tree is never reached and would
    make the control vacuous. That makes the cleanup obligation stricter, not
    looser, so removal runs in a finally with a prune behind it and a direct
    tree removal behind that.

    Args:
        relative: Path relative to the repository root.

    Yields:
        The absolute path of the live worktree.
    """
    target = REPO_ROOT / relative
    created_parents: list[Path] = []
    parent = target.parent
    while parent != REPO_ROOT and not parent.exists():
        created_parents.append(parent)
        parent = parent.parent

    added = _git("worktree", "add", "--detach", str(target), "HEAD")
    if added.returncode != 0:
        message = f"git worktree add failed for {relative} with code {added.returncode}"
        raise AssertionError(message)
    try:
        # SELF-CHECK. Every one of these must hold before anything is graded,
        # or a control that created nothing would pass by doing nothing.
        assert target.is_dir(), f"{relative} was not created"
        assert (target / ".git").exists(), f"{relative} carries no .git entry"
        assert (target / "CLAUDE.md").is_file(), f"{relative} carries no CLAUDE.md copy"
        listed = _git("worktree", "list", "--porcelain")
        assert listed.returncode == 0, "git worktree list failed"
        assert target.name in listed.stdout, f"{relative} is not a live worktree"
        yield target
    finally:
        removed = _git("worktree", "remove", "--force", str(target))
        _git("worktree", "prune")
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        for stale in created_parents:
            with contextlib.suppress(OSError):
                stale.rmdir()
        assert removed.returncode == 0 or not target.exists(), (
            f"the planted worktree {relative} survived cleanup"
        )


def _inflate_past_budget(path: Path) -> None:
    """Make the planted copy breach its own budget, so a leak flips a verdict."""
    filler = ("x" * 79 + "\n") * ((doc_budget.AUTOLOADED_BUDGET // 80) + 64)
    with path.open("a", encoding="ascii") as handle:
        handle.write(filler)
    assert path.stat().st_size > doc_budget.AUTOLOADED_BUDGET, "the planted copy is still in budget"


# ---------------------------------------------------------------------------
# The control
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative", PLANT_SITES)
def test_a_live_linked_worktree_is_not_measured(relative: str) -> None:
    """The graded control. EVERY assertion here is scoped to THIS test's plant.

    Nothing asserts a global emptiness or a global count, and that is not a
    style choice. Other linked worktrees exist inside the checkout during any
    multi-agent session - which is CS-475's own scenario and CLAUDE.md section
    5's default session shape - and a concurrent pytest worker may have its own
    plant live at the same moment. An assertion about the whole repository
    would be red for reasons that have nothing to do with this test.

    THE ORDERING IS LOAD-BEARING. The graded assertion uses only symbols that
    exist in the pre-fix module, so against real pre-fix code this fails on the
    leak rather than on a missing attribute. Anything referring to the new
    reporting API comes strictly after it.
    """
    reason = _git_is_usable()
    if reason:
        pytest.skip(f"CS-475 control needs a git checkout: {reason}")

    planted_file = f"{relative}/CLAUDE.md"

    with _linked_worktree(relative) as worktree:
        _inflate_past_budget(worktree / "CLAUDE.md")

        # ---- GRADED, and reachable with pre-fix symbols only ----
        measured = _population(REPO_ROOT)
        assert planted_file not in measured, (
            f"a live linked worktree's copy was measured as this tree's: {planted_file}"
        )

        # The planted copy is over its own budget. If it leaked into the
        # population it would also flip the verdict, so this pins the
        # consequence and not merely the row.
        breached = [row["file"] for row in doc_budget.hard_failures(doc_budget.evaluate(REPO_ROOT))]
        assert planted_file not in breached, (
            f"a copy inside another checkout flipped the budget verdict: {planted_file}"
        )

        # The report must not NAME the plant either - scoped to this plant
        # rather than to the global count the report happens to print.
        rendered = chr(10).join(doc_budget.render(doc_budget.evaluate(REPO_ROOT)))
        assert planted_file not in rendered

        # ---- A GUARD'S PRESENCE IS NOT A GUARD'S FIRING ----
        # Absence from the population is also satisfied by a walk that never
        # reached the plant, so the boundary must be seen naming the exact
        # directory it refused to enter.
        during_boundaries = [record["path"] for record in doc_budget.checkout_boundaries(REPO_ROOT)]
        assert relative in during_boundaries, f"the walk did not report stopping at {relative}"

    # Scoped to this plant: the boundary is gone because THIS worktree is gone,
    # said without claiming anything about anyone else's worktrees.
    after_boundaries = [record["path"] for record in doc_budget.checkout_boundaries(REPO_ROOT)]
    assert relative not in after_boundaries, f"a boundary outlived its worktree: {relative}"
    assert planted_file not in _population(REPO_ROOT)


def test_the_teardown_window_does_not_leak_a_dying_worktree() -> None:
    """Finding 4: `git worktree remove` deletes the .git marker BEFORE the files.

    Probed over 8 teardown rounds, 8 of 8 showed a window in which the
    directory still held a populated CLAUDE.md and carried NO marker. In that
    window the boundary test alone answers "this tree owns it" and the walk
    descends into another checkout - the exact failure CS-475 exists to
    prevent, arriving at the exact moment the end-of-session ritual runs this
    tool. The window is reproduced here by deleting the marker directly, which
    is the state the probe observed rather than a hypothetical one.

    In the same 8 rounds the dying copy was in this checkout's index 0 times
    out of 8, which is why the index is the test that closes this.
    """
    reason = _git_is_usable()
    if reason:
        pytest.skip(f"CS-475 control needs a git checkout: {reason}")

    relative = f"cs475-teardown-{os.getpid()}"
    planted_file = f"{relative}/CLAUDE.md"

    with _linked_worktree(relative) as worktree:
        marker = worktree / ".git"
        marker.unlink()

        # SELF-CHECK: the window really is open - unmarked, still populated.
        assert not marker.exists(), "the marker was not removed"
        assert (worktree / "CLAUDE.md").stat().st_size > 0, "the copy is already gone"

        assert planted_file not in _population(REPO_ROOT), (
            "an unmarked but populated dying worktree was measured as this tree's"
        )
        assert planted_file in doc_budget.survey(REPO_ROOT).untracked, (
            "the dying copy was dropped silently instead of being reported"
        )


# ---------------------------------------------------------------------------
# The same boundary without git, so the rule is graded on a clean machine too
# ---------------------------------------------------------------------------


def test_a_nested_checkout_marker_stops_the_walk(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# root\n", encoding="ascii")

    carried = tmp_path / "subsystem"
    carried.mkdir()
    (carried / "CLAUDE.md").write_text("# carried by this tree\n", encoding="ascii")

    other = tmp_path / "other-checkout"
    other.mkdir()
    # Exactly what a linked worktree carries: .git as a FILE, not a directory.
    (other / ".git").write_text("gitdir: elsewhere\n", encoding="ascii")
    (other / "CLAUDE.md").write_text("# a different checkout's copy\n", encoding="ascii")

    deep = other / "nested"
    deep.mkdir()
    (deep / "CLAUDE.md").write_text("# below the boundary\n", encoding="ascii")

    measured = _population(tmp_path)

    assert "CLAUDE.md" in measured
    assert "subsystem/CLAUDE.md" in measured, "a directory this tree carries must be measured"
    assert "other-checkout/CLAUDE.md" not in measured
    assert "other-checkout/nested/CLAUDE.md" not in measured


def test_a_nested_clone_directory_marker_stops_the_walk(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# root\n", encoding="ascii")

    clone = tmp_path / "vendored-clone"
    (clone / ".git").mkdir(parents=True)
    (clone / "CLAUDE.md").write_text("# a nested clone's copy\n", encoding="ascii")

    assert "vendored-clone/CLAUDE.md" not in _population(tmp_path)


def test_the_walk_root_is_not_pruned_by_its_own_marker(tmp_path: Path) -> None:
    (tmp_path / ".git").write_text("gitdir: elsewhere\n", encoding="ascii")
    (tmp_path / "CLAUDE.md").write_text("# the root of this walk\n", encoding="ascii")

    assert "CLAUDE.md" in _population(tmp_path)


def test_no_stale_plant_of_this_process_survives() -> None:
    # Scoped to THIS process's plant paths. A global check here would be red
    # whenever a concurrent worker has its own plant live, which is precisely
    # the shape this module must not assert.
    for relative in PLANT_SITES:
        assert not (REPO_ROOT / relative).exists(), f"a previous run left {relative} behind"


def test_the_walk_does_not_touch_the_process_environment() -> None:
    before = dict(os.environ)
    doc_budget.evaluate(REPO_ROOT)
    assert dict(os.environ) == before


# ---------------------------------------------------------------------------
# The shape of the fix: a stated boundary, not a special-cased directory name
# ---------------------------------------------------------------------------


def test_a_harness_named_directory_carrying_no_marker_is_still_measured(tmp_path: Path) -> None:
    """The criterion is the marker, and a directory NAME is not the criterion.

    This is the test that separates the shipped fix from the wrong one. A
    directory named exactly like the harness's worktree directory, but which
    is part of THIS tree rather than a checkout of its own, carries a budgeted
    file that really does cost context - so it must be measured. A fix that
    added ".claude" or "worktrees" to a skip list would fail here.
    """
    (tmp_path / "CLAUDE.md").write_text("# root\n", encoding="ascii")

    lookalike = tmp_path / ".claude" / "worktrees" / "not-a-checkout"
    lookalike.mkdir(parents=True)
    (lookalike / "CLAUDE.md").write_text("# carried by this tree after all\n", encoding="ascii")

    measured = _population(tmp_path)

    assert ".claude/worktrees/not-a-checkout/CLAUDE.md" in measured
    assert not doc_budget.checkout_boundaries(tmp_path), "nothing here is a checkout root"


def test_no_pruning_criterion_names_a_harness_directory() -> None:
    assert doc_budget.WALK_BOUNDARY.marker == ".git"
    for name in doc_budget.WALK_SKIP_DIRS:
        assert "worktree" not in name.lower(), f"{name} prunes by harness layout, not by structure"
        assert name != ".claude", "the harness directory is not a pruning criterion"


def test_every_declared_walked_root_carries_its_reason() -> None:
    assert doc_budget.WALKED_ROOTS, "the population must name at least one root"
    for walked in doc_budget.WALKED_ROOTS:
        assert isinstance(walked, doc_budget.WalkedRoot)
        assert walked.relative
        assert walked.filename
        assert len(walked.reason) > MINIMUM_STATED_REASON, (
            f"root {walked.relative} states no reason"
        )


def test_every_skipped_directory_name_carries_its_reason() -> None:
    for name, reason in doc_budget.WALK_SKIP_DIRS.items():
        assert reason.strip(), f"{name} is pruned with no stated reason"


def test_the_declared_data_is_immutable() -> None:
    # A population a caller can edit at runtime is a population decided
    # somewhere other than where it is stated. The module is loaded by path,
    # so mypy sees Any here and only the runtime behaviour is checkable -
    # which is the behaviour that matters for this property anyway.
    with pytest.raises((AttributeError, TypeError)):
        doc_budget.WALK_BOUNDARY.marker = "not-git"
    with pytest.raises(TypeError):
        doc_budget.WALK_SKIP_DIRS["injected"] = "no reason"


def test_the_rendered_report_states_the_population() -> None:
    text = "\n".join(
        doc_budget.render(doc_budget.evaluate(REPO_ROOT), doc_budget.survey(REPO_ROOT))
    )

    assert "Population walked" in text
    for walked in doc_budget.WALKED_ROOTS:
        assert f"root {walked.relative}" in text
        assert walked.reason in text
    assert doc_budget.WALK_BOUNDARY.reason in text
    assert doc_budget.INDEX_MEMBERSHIP_REASON in text


def test_json_mode_states_the_population(capsys: pytest.CaptureFixture[str]) -> None:
    code = doc_budget.main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    population = payload["population"]
    assert population["boundary_marker"] == ".git"
    assert population["boundary_reason"] == doc_budget.WALK_BOUNDARY.reason
    assert [entry["relative"] for entry in population["walked_roots"]] == [
        walked.relative for walked in doc_budget.WALKED_ROOTS
    ]
    assert set(population["skipped_directory_names"]) == set(doc_budget.WALK_SKIP_DIRS)
    assert population["index_membership_reason"] == doc_budget.INDEX_MEMBERSHIP_REASON
    assert population["index_available"] is True
    assert population["index_unavailable_reason"] == ""
