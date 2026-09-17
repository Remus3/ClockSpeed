#!/usr/bin/env python3
"""Tests for tools/doc_budget.py, and the CS-475 checkout-boundary control.

CS-475: the tool derived its population with ``root.rglob("CLAUDE.md")`` and
pruned only by directory NAME, so it descended into every linked git worktree
sitting inside the repository and measured that other checkout's copy of a
budgeted file as if it were this one's.

THE CONTROL BUILDS ITS OWN REPOSITORY. It never plants into, and never runs
`git worktree add/remove/prune` against, the repository the suite lives in.
That is not tidiness. Those commands mutate SHARED worktree administration,
and this project runs several agents in linked worktrees off one checkout -
a suite that pruned live admin state on every run would be reproducing CS-448's
own mechanism automatically, including during the end-of-session ritual. A
throwaway `git init` repo under tmp_path is a real checkout and reproduces the
defect exactly as well, which is how every adversary and verifier on this item
reproduced it.

Two further properties of the control are load-bearing:

  1. It creates a GENUINE linked worktree with ``git worktree add`` and proves
     the planted copy is on disk before it grades anything. A control that
     silently created nothing would pass trivially.
  2. It plants at a site that is NOT under ``.claude/worktrees/`` as well as
     one that is. A fix that recognised that NAME would pass a control that
     only looked there and would fail the day a harness moved its worktrees.

THE ORDERING INSIDE THE CONTROL IS ALSO LOAD-BEARING. The graded assertion uses
only symbols that exist in the pre-fix module, so against real pre-fix code the
control fails on the leak rather than on a missing attribute - CLAUDE.md
non-negotiable 9. Anything touching the newer reporting API comes strictly
after it.

No test id carries a pid or any other per-process value. xdist compares
collected node ids across workers and errors on any divergence, so a pid in a
parametrize argument breaks the very `pytest -q -n auto` invocation this
module's isolation exists to survive. Isolation comes from tmp_path, which is
already unique per worker.
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType

import pytest

from tests import liveness

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_BUDGET_SOURCE = REPO_ROOT / "tools" / "doc_budget.py"

GIT_TIMEOUT = 120

#: Identifiers this module's git calls may target - each one a scratch checkout
#: a fixture in this file built under tmp_path, never the live repository.
#:
#: WIDENED BY CS-496 FROM THE SINGLE NAME ``repo``, deliberately and not as a
#: way past the guard. The guard's rule is that a git call must target a
#: scratch repo the test built; ``repo_template`` is one, and the single name
#: was the rule's implementation rather than its intent. The alternative was
#: binding ``repo = repo_template`` before the call, which is bypass 1 in
#: :func:`test_the_suite_never_mutates_this_repository_worktree_admin`'s own
#: list of what it cannot see - using a hole a guard documents to get past that
#: guard is worse than widening it in the open.
SCRATCH_REPO_NAMES = ("repo", "repo_template")

NEWLINE = chr(10)

# A declared reason shorter than this is a label, not a reason.
MINIMUM_STATED_REASON = 40

# One survey per invocation asks git twice: the membership listing and the
# worktree registration. More than that means a consumer re-queried.
MAX_GIT_CALLS_PER_INVOCATION = 2

# add, remove and prune - the three worktree subcommands the control issues.
EXPECTED_WORKTREE_COMMANDS = 3

# The two plant sites, as STABLE ids. The first is where the harness put its
# worktrees when the defect was measured; the second is deliberately nowhere
# near it, and is not covered by any ignore rule.
HARNESS_SITE = ".claude/worktrees/wt"
ELSEWHERE_SITE = "elsewhere/wt"
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


def _population(root: Path) -> list[str]:
    """The display paths of every row the tool actually measured."""
    return sorted(row["file"] for row in doc_budget.evaluate(root) if row["status"] != "MISSING")


def _git_reason() -> str:
    """Empty when git can build a scratch checkout, else why it cannot."""
    if shutil.which("git") is None:
        return "git is not on PATH"
    try:
        done = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"git could not be run: {type(exc).__name__}"
    if done.returncode != 0:
        return "git --version failed"
    return ""


def _require_git() -> None:
    reason = _git_reason()
    if reason:
        pytest.skip(f"CS-475 control needs git: {reason}")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
    )


def _build_template(repo: Path) -> None:
    """Build a real, throwaway git checkout shaped like this project's tree.

    Three git processes, not five: identity is passed inline to the commit
    rather than written with two `git config` calls.

    It carries a .gitignore with the same anchored worktree pattern this
    repository uses, because the membership rule's ignore half is only
    meaningful against a real ignore file.
    """
    repo.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
    )
    # CS-496 - HOUSEKEEPING OFF, BEFORE ANY COMMIT. `git commit` runs
    # `git maintenance run --auto` and DETACHES it, so a template built here
    # keeps a background process that creates and removes
    # .git/objects/maintenance.lock after this function has returned. Every
    # later test copies this directory, and CI lost that race on run
    # 32346100111. Both knobs are set because the two git versions this project
    # runs read different ones: `gc.auto` is the older name and
    # `maintenance.auto` the one that gates the detached run.
    _git(repo, "config", "maintenance.auto", "false")
    _git(repo, "config", "gc.auto", "0")

    (repo / "CLAUDE.md").write_text("# scratch root" + NEWLINE, encoding="ascii")
    (repo / ".gitignore").write_text("/.claude/worktrees/" + NEWLINE, encoding="ascii")
    (repo / "memory").mkdir()
    (repo / "memory" / "MEMORY.md").write_text("# index" + NEWLINE, encoding="ascii")
    (repo / "ROADMAP.md").write_text("# roadmap" + NEWLINE, encoding="ascii")
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.email=control@example.invalid",
        "-c",
        "user.name=cs475 control",
        "commit",
        "-q",
        "-m",
        "scratch base",
    )


def _copy_checkout(
    source: Path, destination: Path, _hook: Callable[[str, list[str]], set[str]] | None = None
) -> None:
    """Copy a git checkout.

    A FILE THAT VANISHES BETWEEN THE WALK AND THE COPY IS SKIPPED, not raised.
    `shutil.copytree` stats a tree and then copies it, so anything git removes
    in between kills it - which is what CI hit on run 32346100111, on a commit
    that changed two markdown files and no Python. `_build_template` now turns
    git housekeeping off so the lock should never appear at all; this is the
    second line, because a fixture resting on one config being honoured by
    every future git version has one point of failure and no second.

    WHAT IS SKIPPED IS NARROW AND IS NOT SWALLOWED SILENTLY IN THE CASE THAT
    MATTERS. Only a file that has ceased to exist by the time it is read is
    passed over. A tracked file that goes missing would take its content with
    it, and the callers assert on the content they need, so a copy that lost
    something real still fails - it just fails where the content is missing
    rather than inside the copy.

    Args:
        source: The checkout to copy.
        destination: Where to copy it.
        _hook: Test seam, called with each directory and its entries as the
            walk reaches them. Production callers pass nothing.
    """
    destination.mkdir(parents=True, exist_ok=True)
    entries = sorted(source.iterdir())
    skipped: set[str] = set()
    if _hook is not None:
        skipped = set(_hook(str(source), [entry.name for entry in entries]))

    for entry in entries:
        if entry.name in skipped:
            continue
        try:
            if entry.is_dir():
                _copy_checkout(entry, destination / entry.name, _hook)
            else:
                shutil.copy2(entry, destination / entry.name)
        except FileNotFoundError:
            continue


@pytest.fixture(scope="session")
def repo_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One scratch checkout for the whole session.

    Built once. Every test gets its own COPY, so no test can observe another's
    mutations, and copying costs no subprocess.
    """
    _require_git()
    template = tmp_path_factory.mktemp("cs475-template") / "scratch"
    _build_template(template)
    return template


@pytest.fixture
def scratch_repo(repo_template: Path, tmp_path: Path) -> Path:
    """A private copy of the session template.

    A copied git directory is a valid checkout, which is what keeps this off
    the subprocess path.
    """
    destination = tmp_path / "scratch"
    _copy_checkout(repo_template, destination)
    return destination


def _copy_racing_a_vanishing_lock(source: Path, destination: Path) -> None:
    """Copy ``source`` while a git housekeeping lock vanishes mid-copy.

    ``shutil.copytree`` lists a directory, hands the names to its ``ignore``
    callback, and only then copies what survives that filter. Deleting the lock
    from inside that callback removes it AFTER the walk has seen it and BEFORE
    the copy reaches it, which is precisely the window CI lost. A deterministic
    reproduction of a race, rather than a re-run until it happens again.

    Args:
        source: The checkout to copy.
        destination: Where to copy it.
    """
    lock = source / ".git" / "objects" / "maintenance.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("", encoding="ascii")

    def _vanish(directory: str, _names: list[str]) -> set[str]:
        if Path(directory) == lock.parent and lock.exists():
            lock.unlink()
        return set()

    try:
        _copy_checkout(source, destination, _hook=_vanish)
    finally:
        lock.unlink(missing_ok=True)


def test_the_scratch_copy_survives_a_git_lock_vanishing_mid_copy(
    repo_template: Path, tmp_path: Path
) -> None:
    """CS-496 - the fixture cannot fail because a file inside .git disappeared.

    MEASURED ON CI, NOT SUSPECTED. Run 32346100111 errored with
    ``shutil.Error: ... '.git/objects/maintenance.lock' ... [Errno 2] No such
    file or directory`` on a commit that changed two markdown files and no
    Python, and re-running the same job passed. ``git commit`` runs
    ``git maintenance run --auto`` and DETACHES it, so the template this
    fixture builds can still be dropping lock files under ``.git/objects``
    while a later test copies it.

    THE FIX HAS TWO HALVES AND THIS GRADES THE SECOND. The template now
    disables auto maintenance, so the lock should never appear - that is
    :func:`test_the_scratch_template_has_git_housekeeping_disabled`. This test
    assumes the prevention failed anyway and requires the copy to survive it,
    because a fixture resting on one git config being honoured by every future
    git version has one point of failure and no second.

    IT IS THE CS-483 SHAPE. A test that fails for a reason unrelated to what it
    grades spends the suite's credibility, and the tempting response - re-run
    it, it passed - is how a suite stops being believed.

    Args:
        repo_template: The session-scoped template checkout.
        tmp_path: The per-test temporary directory.
    """
    destination = tmp_path / "scratch"

    _copy_racing_a_vanishing_lock(repo_template, destination)

    assert (destination / ".git").is_dir(), "the copy produced no .git directory"
    assert (destination / "CLAUDE.md").read_text(encoding="ascii").startswith("# scratch"), (
        "the copy dropped a tracked file while tolerating the vanished lock"
    )
    assert not (destination / ".git" / "objects" / "maintenance.lock").exists(), (
        "the vanished lock reached the copy, so the hook did not reproduce the race and "
        "this test grades nothing"
    )


def test_the_scratch_template_has_git_housekeeping_disabled(repo_template: Path) -> None:
    """CS-496's first half - the lock is prevented, not only tolerated.

    Turning both knobs off in the template is what stops the lock file existing
    at all; the copy's tolerance is the second line, not the first.

    READ FROM GIT, NOT FROM THE FIXTURE'S SOURCE. Asserting that the fixture
    contains a ``git config`` call would grade a transcription of the setting
    rather than the setting, which is the ADR 0008 shape.

    Args:
        repo_template: The session-scoped template checkout.
    """
    for key in ("maintenance.auto", "gc.auto"):
        result = _git(repo_template, "config", "--get", key)
        assert result.stdout.strip() in {"false", "0"}, (
            f"{key} reads {result.stdout.strip()!r} in the scratch template, so git may run "
            "housekeeping in it while another test is copying it"
        )


@contextlib.contextmanager
def _linked_worktree(repo: Path, relative: str) -> Iterator[Path]:
    """Create a genuine linked worktree at ``relative`` inside ``repo``.

    ``repo`` is always a throwaway scratch checkout. The worktree has to sit
    INSIDE it, because the defect is that the walk descends into it.

    Yields:
        The absolute path of the live worktree.
    """
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)

    added = _git(repo, "worktree", "add", "--detach", str(target), "HEAD")
    if added.returncode != 0:
        message = f"git worktree add failed for {relative} with code {added.returncode}"
        raise AssertionError(message)
    try:
        # SELF-CHECK. All of these must hold before anything is graded, or a
        # control that created nothing would pass by doing nothing.
        assert target.is_dir(), f"{relative} was not created"
        assert (target / ".git").exists(), f"{relative} carries no .git entry"
        assert (target / "CLAUDE.md").is_file(), f"{relative} carries no CLAUDE.md copy"
        listed = _git(repo, "worktree", "list", "--porcelain")
        assert listed.returncode == 0, "git worktree list failed"
        assert target.name in listed.stdout, f"{relative} is not a live worktree"
        yield target
    finally:
        _git(repo, "worktree", "remove", "--force", str(target))
        _git(repo, "worktree", "prune")
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)


def _inflate_past_budget(path: Path) -> None:
    """Make a copy breach its own budget, so a leak flips a verdict."""
    filler = ("x" * 79 + chr(10)) * ((doc_budget.AUTOLOADED_BUDGET // 80) + 64)
    with path.open("a", encoding="ascii") as handle:
        handle.write(filler)
    assert path.stat().st_size > doc_budget.AUTOLOADED_BUDGET, "the planted copy is still in budget"


# ---------------------------------------------------------------------------
# The control
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative", PLANT_SITES)
def test_a_live_linked_worktree_is_not_measured(scratch_repo: Path, relative: str) -> None:
    repo = scratch_repo
    planted_file = f"{relative}/CLAUDE.md"

    baseline = _population(repo)

    with _linked_worktree(repo, relative) as worktree:
        _inflate_past_budget(worktree / "CLAUDE.md")

        # ---- GRADED, reachable with pre-fix symbols only ----
        measured = _population(repo)
        assert planted_file not in measured, (
            f"a live linked worktree's copy was measured as this tree's: {planted_file}"
        )
        assert measured == baseline, "the population changed while a worktree was live"

        breached = [row["file"] for row in doc_budget.hard_failures(doc_budget.evaluate(repo))]
        assert planted_file not in breached, (
            f"a copy inside another checkout flipped the budget verdict: {planted_file}"
        )

        rendered = chr(10).join(doc_budget.render(doc_budget.evaluate(repo)))
        assert planted_file not in rendered

        # ---- A GUARD'S PRESENCE IS NOT A GUARD'S FIRING ----
        during = [record["path"] for record in doc_budget.checkout_boundaries(repo)]
        assert relative in during, f"the walk did not report stopping at {relative}"

    after = [record["path"] for record in doc_budget.checkout_boundaries(repo)]
    assert relative not in after, f"a boundary outlived its worktree: {relative}"
    assert _population(repo) == baseline


@pytest.mark.parametrize("relative", PLANT_SITES)
def test_the_teardown_window_does_not_leak_a_dying_worktree(
    scratch_repo: Path, relative: str
) -> None:
    """`git worktree remove` deletes the .git marker BEFORE the files.

    Probed over 8 teardown rounds, 8 of 8 showed a window in which the
    directory still held a populated CLAUDE.md and carried NO marker. The
    window is reproduced here by deleting the marker directly, which is the
    state the probe observed rather than a hypothetical one.

    BOTH SITES ARE GRADED, and that is the point. The ignore half of the
    membership rule excludes the copy under ``.claude/worktrees/`` only. At an
    un-ignored site the dying copy is untracked AND not ignored, so it looks
    exactly like a new file this tree owns - measured directly, it passes the
    tracked-or-not-ignored test there. What holds at both is that git still
    lists the directory as a registered worktree once the marker is gone.
    """
    repo = scratch_repo
    planted_file = f"{relative}/CLAUDE.md"

    with _linked_worktree(repo, relative) as worktree:
        marker = worktree / ".git"
        marker.unlink()

        # SELF-CHECK: the window really is open - unmarked, still populated.
        assert not marker.exists(), "the marker was not removed"
        assert (worktree / "CLAUDE.md").stat().st_size > 0, "the copy is already gone"

        assert planted_file not in _population(repo), (
            "an unmarked but populated dying worktree was measured as this tree's"
        )
        observed = doc_budget.survey(repo)
        assert relative in observed.boundaries, "the dying worktree was not reported as a boundary"


def test_a_registered_worktree_is_what_closes_the_un_ignored_teardown(scratch_repo: Path) -> None:
    """The un-ignored dying copy really does pass the ignore half.

    Without this, the previous test could be green for the wrong reason - it
    would look like the ignore rule covered both sites. It does not, and the
    registration test is carrying the un-ignored one.
    """
    repo = scratch_repo

    with _linked_worktree(repo, ELSEWHERE_SITE) as worktree:
        (worktree / ".git").unlink()
        facts = doc_budget.git_facts(repo)

        assert facts.available
        assert f"{ELSEWHERE_SITE}/CLAUDE.md".lower() in facts.members, (
            "an un-ignored dying copy is expected to PASS the tracked-or-not-ignored test"
        )
        assert facts.worktrees, "git no longer registers the worktree once its marker is gone"


def test_an_untracked_but_owned_over_budget_file_still_hard_fails(scratch_repo: Path) -> None:
    """The enforcement the tracked-only rule gave up, restored.

    A brand-new nested CLAUDE.md this tree genuinely owns is untracked and NOT
    ignored. It costs context exactly like a committed one, so an over-budget
    one must still fail the hard gate.
    """
    repo = scratch_repo

    area = repo / "docs" / "newarea"
    area.mkdir(parents=True)
    new_file = area / "CLAUDE.md"
    new_file.write_text("# brand new, never committed" + NEWLINE, encoding="ascii")
    _inflate_past_budget(new_file)

    rows = doc_budget.evaluate(repo)
    hard = [row["file"] for row in doc_budget.hard_failures(rows)]

    assert "docs/newarea/CLAUDE.md" in hard, (
        "an untracked file this tree owns escaped the hard budget gate"
    )


def test_an_ignored_over_budget_file_is_not_measured(scratch_repo: Path) -> None:
    repo = scratch_repo

    hidden = repo / ".claude" / "worktrees" / "leftover"
    hidden.mkdir(parents=True)
    stale = hidden / "CLAUDE.md"
    stale.write_text("# a leftover copy under an ignored path" + NEWLINE, encoding="ascii")
    _inflate_past_budget(stale)

    observed = doc_budget.survey(repo)
    assert ".claude/worktrees/leftover/CLAUDE.md" not in _population(repo)
    assert ".claude/worktrees/leftover/CLAUDE.md" in observed.excluded, (
        "an ignored copy was dropped silently instead of being reported"
    )
    assert not doc_budget.hard_failures(doc_budget.evaluate(repo))


def test_one_invocation_asks_git_once_per_question(
    scratch_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() must not re-ask git per consumer.

    An earlier revision spawned three git processes per invocation because
    evaluate(), survey() and checkout_boundaries() each queried independently.
    """
    repo = scratch_repo
    calls: list[tuple[str, ...]] = []

    # Reaching for the private runner IS the subject: the property under
    # test is how many subprocesses one invocation spawns, which no public
    # surface reports.
    real = doc_budget._git  # noqa: SLF001

    def counting(root: Path, *args: str) -> object:
        calls.append(args)
        return real(root, *args)

    monkeypatch.setattr(doc_budget, "_git", counting)
    monkeypatch.setattr(doc_budget, "repo_root", lambda: repo)

    doc_budget.main([])

    assert len(calls) <= MAX_GIT_CALLS_PER_INVOCATION, (
        f"one invocation asked git {len(calls)} times: {calls}"
    )


# ---------------------------------------------------------------------------
# The boundary without git, so the rule is graded on a clean machine too
# ---------------------------------------------------------------------------


def test_a_nested_checkout_marker_stops_the_walk(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")

    carried = tmp_path / "subsystem"
    carried.mkdir()
    (carried / "CLAUDE.md").write_text("# carried by this tree" + NEWLINE, encoding="ascii")

    other = tmp_path / "other-checkout"
    other.mkdir()
    # Exactly what a linked worktree carries: .git as a FILE, not a directory.
    (other / ".git").write_text("gitdir: elsewhere" + NEWLINE, encoding="ascii")
    (other / "CLAUDE.md").write_text("# a different checkout's copy" + NEWLINE, encoding="ascii")

    deep = other / "nested"
    deep.mkdir()
    (deep / "CLAUDE.md").write_text("# below the boundary" + NEWLINE, encoding="ascii")

    measured = _population(tmp_path)

    assert "CLAUDE.md" in measured
    assert "subsystem/CLAUDE.md" in measured, "a directory this tree carries must be measured"
    assert "other-checkout/CLAUDE.md" not in measured
    assert "other-checkout/nested/CLAUDE.md" not in measured


def test_a_nested_clone_directory_marker_stops_the_walk(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")

    clone = tmp_path / "vendored-clone"
    (clone / ".git").mkdir(parents=True)
    (clone / "CLAUDE.md").write_text("# a nested clone's copy" + NEWLINE, encoding="ascii")

    assert "vendored-clone/CLAUDE.md" not in _population(tmp_path)


def test_the_walk_root_is_not_pruned_by_its_own_marker(tmp_path: Path) -> None:
    (tmp_path / ".git").write_text("gitdir: elsewhere" + NEWLINE, encoding="ascii")
    (tmp_path / "CLAUDE.md").write_text("# the root of this walk" + NEWLINE, encoding="ascii")

    assert "CLAUDE.md" in _population(tmp_path)


def test_a_tree_git_cannot_answer_for_states_its_degradation(tmp_path: Path) -> None:
    """Non-negotiable 7: flagged and skipped, never silently wrong."""
    (tmp_path / "CLAUDE.md").write_text("# not a checkout at all" + NEWLINE, encoding="ascii")

    observed = doc_budget.survey(tmp_path)
    assert observed.index_available is False

    text = chr(10).join(doc_budget.render(doc_budget.evaluate(tmp_path), observed))
    assert "DEGRADED" in text
    assert doc_budget.INDEX_UNAVAILABLE_REASON in text


# ---------------------------------------------------------------------------
# The shape of the fix: a stated boundary, not a special-cased directory name
# ---------------------------------------------------------------------------


def test_a_harness_named_directory_carrying_no_marker_is_still_measured(tmp_path: Path) -> None:
    """The criterion is the marker, and a directory NAME is not the criterion.

    A directory named exactly like the harness's worktree directory, but which
    is part of THIS tree rather than a checkout of its own, carries a budgeted
    file that really does cost context. A fix that added ".claude" or
    "worktrees" to a skip list would fail here.

    This uses a non-git tree deliberately, so the ignore rule cannot be what
    excludes it - the marker is the only thing under test.
    """
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")

    lookalike = tmp_path / ".claude" / "worktrees" / "not-a-checkout"
    lookalike.mkdir(parents=True)
    (lookalike / "CLAUDE.md").write_text(
        "# carried by this tree after all" + NEWLINE, encoding="ascii"
    )

    measured = _population(tmp_path)

    assert ".claude/worktrees/not-a-checkout/CLAUDE.md" in measured
    assert not doc_budget.checkout_boundaries(tmp_path), "nothing here is a checkout root"


#: The APPROACH band for the routing index, as a fraction of its own budget.
#: CS-1062 required an arm that reddens BEFORE the index becomes a blocker, and
#: the number is a literal here rather than a fraction of whatever the file
#: currently measures - a bound computed from the thing it bounds is the
#: tautology `tests/test_tier1_budget.py` records this project filing twice.
ITEM_NOTES_INDEX_APPROACH = 0.90


def test_the_routing_index_stays_below_its_approach_band() -> None:
    """CS-1062's third clause. The blocker is caught on APPROACH, not on arrival.

    WHY AN ARM AND NOT JUST THE BUDGET. `tools/doc_budget.py` WARNS at the
    ceiling and does not fail, which is right for a size budget and wrong for
    this particular file: the index is the single hop every reader of an item
    takes, and until CS-1112 every filing session also wrote a routing row INTO
    it. It reached ELEVEN bytes of headroom, and at that point the next session
    to file an item could not add its row without first doing unrelated surgery
    under time pressure - which is how a rule gets bent instead of a file getting
    split. CS-1112 removed the rows, so the index no longer grows per item; the
    band stays, because a rule block written here grows it just the same.
    Session 94 relocated mid-session to keep filing and session 95 spent its
    last headroom correcting one sentence.

    THE REPAIR IS RELOCATION, NEVER DELETION, and never raising the ceiling.
    `tools/doc_budget.py` argues the 16 KB number where it is defined: a body
    must not fit in the index. Move a block to an annex under
    `docs/item_notes/` that carries no `## CS-nnn` section, the way
    `docs/item_notes/leaf-membership-rule.md` was moved, and leave a pointer.

    THIS ARM REDDENS WHILE THERE IS STILL ROOM TO ACT. That is the mechanism
    working, not a false alarm.
    """
    index = REPO_ROOT / "docs" / "item_notes.md"
    size = len(index.read_bytes())
    budget = doc_budget.ITEM_NOTES_INDEX_BUDGET
    band = int(budget * ITEM_NOTES_INDEX_APPROACH)

    assert size <= band, (
        "docs/item_notes.md is %d bytes, past the %d-byte approach band "
        "(%.0f per cent of its %d-byte budget). RELOCATE a block to an annex "
        "under docs/item_notes/ and leave a pointer. Do NOT delete the leaf "
        "table, do NOT re-add a routing row, and do NOT raise the budget."
        % (size, band, 100 * ITEM_NOTES_INDEX_APPROACH, budget)
    )


def test_the_approach_band_sits_below_the_budget_it_guards() -> None:
    """The band is only a warning if it is strictly inside the thing it guards.

    An approach band equal to the budget reddens at the same moment the budget
    does and buys nothing, which is the whole defect CS-1062 filed. Asserted
    rather than assumed, because the fraction is a literal somebody can edit.
    """
    budget = doc_budget.ITEM_NOTES_INDEX_BUDGET
    assert 0 < ITEM_NOTES_INDEX_APPROACH < 1, ITEM_NOTES_INDEX_APPROACH
    assert int(budget * ITEM_NOTES_INDEX_APPROACH) < budget


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
    # so mypy sees Any here and only the runtime behaviour is checkable.
    with pytest.raises((AttributeError, TypeError)):
        doc_budget.WALK_BOUNDARY.marker = "not-git"
    with pytest.raises(TypeError):
        doc_budget.WALK_SKIP_DIRS["injected"] = "no reason"


def test_the_rendered_report_states_every_membership_rule(scratch_repo: Path) -> None:
    repo = scratch_repo
    observed = doc_budget.survey(repo)
    text = chr(10).join(doc_budget.render(doc_budget.evaluate(repo, observed), observed))

    assert "Population walked" in text
    for walked in doc_budget.WALKED_ROOTS:
        assert f"root {walked.relative}" in text
        assert walked.reason in text
    assert doc_budget.WALK_BOUNDARY.reason in text
    assert doc_budget.REGISTERED_WORKTREE_REASON in text
    assert doc_budget.MEMBERSHIP_REASON in text


def test_json_mode_states_the_population(
    scratch_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = scratch_repo
    monkeypatch.setattr(doc_budget, "repo_root", lambda: repo)

    code = doc_budget.main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    population = payload["population"]
    assert population["boundary_marker"] == ".git"
    assert population["boundary_reason"] == doc_budget.WALK_BOUNDARY.reason
    assert population["membership_reason"] == doc_budget.MEMBERSHIP_REASON
    assert population["registered_worktree_reason"] == doc_budget.REGISTERED_WORKTREE_REASON
    assert population["index_available"] is True
    assert [entry["relative"] for entry in population["walked_roots"]] == [
        walked.relative for walked in doc_budget.WALKED_ROOTS
    ]
    assert set(population["skipped_directory_names"]) == set(doc_budget.WALK_SKIP_DIRS)


def test_the_suite_never_mutates_this_repository_worktree_admin() -> None:
    """No git worktree mutation in this module may target the live repository.

    The suite runs from the project root and from agent worktrees off it, where
    `git worktree add/remove/prune` writes SHARED administration that other
    live agents depend on. Every such call in this file must take a scratch
    repo the test built.

    Graded by parsing this module rather than by scanning its text: a text
    scan matches its own needle and grades nothing.

    WHAT THIS GUARD AND ITS SIBLING DO NOT CATCH, stated because a guard whose
    reach is assumed is worse than no guard at all. Both match on NAMES: a call
    to ``_git`` whose first argument is the identifier ``repo``. Two bypasses
    pass them cleanly.

      1. ``repo = REPO_ROOT`` assigned anywhere above the call. The argument is
         still spelled ``repo``, so both guards stay green.
      2. A direct ``subprocess.run`` invoking git, which never routes through
         ``_git`` and is therefore invisible to an AST search keyed on that
         name. This one is NOT hypothetical: _build_template in this very file
         calls subprocess.run for `git init`, so the pattern is already live
         here and a future edit could copy it without noticing.

    So these two catch an ACCIDENTAL future edit - someone reaching for
    REPO_ROOT out of habit - and not a determined one. The real assurance that
    this suite leaves the live repository's worktree administration alone is a
    reviewer, and git's own trace of what the suite executed.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_git":
            continue
        if not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Name) and first.id not in SCRATCH_REPO_NAMES:
            offenders.append(f"line {node.lineno}: _git({first.id}, ...)")

    assert not offenders, f"git commands aimed at a repository the test did not build: {offenders}"


def test_every_worktree_command_in_this_module_targets_a_scratch_repo() -> None:
    """The positive half: worktree subcommands exist, and all take `repo`.

    Without this, the guard above passes vacuously the day someone deletes
    every _git call.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="ascii"))
    seen = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_git":
            continue
        literals = [a.value for a in node.args if isinstance(a, ast.Constant)]
        if "worktree" not in literals:
            continue
        seen += 1
        first = node.args[0]
        assert isinstance(first, ast.Name), (
            f"line {node.lineno}: a worktree command's target is not a plain name"
        )
        assert first.id == "repo", (
            f"line {node.lineno}: a worktree command does not target a scratch repo"
        )

    assert seen >= EXPECTED_WORKTREE_COMMANDS, (
        f"expected the worktree add/remove/prune calls, found {seen}"
    )


def test_the_walk_does_not_touch_the_process_environment() -> None:
    before = dict(os.environ)
    doc_budget.evaluate(REPO_ROOT)
    assert dict(os.environ) == before


# ---------------------------------------------------------------------------
# CS-846 - the liveness census, graded from a file that is not its own
# ---------------------------------------------------------------------------
#
# WHY THIS LIVES HERE, since it has nothing to do with byte budgets. The
# liveness check in tests/test_liveness.py grades every control and grader in
# the tree, and every consumer of its census used to sit inside the file it
# grades. An adversary silenced all of them with ONE edit - wrapping the
# consumer's body so it never ran - because the thing that would have reported
# the wrap was the thing wrapped. Four consumers in one file is one consumer.
#
# So one consumer lives OUTSIDE that file, and it re-derives rather than
# importing a result. Its home is this module because the property needs a file
# that is not tests/test_liveness.py and that already runs in the fast tier;
# the choice of WHICH other file is arbitrary and the requirement that it be
# another file is not. tests/test_liveness.py asserts this test still exists,
# so deleting it is a second edit in a second file rather than a silent one.


def test_the_liveness_census_is_clean_when_read_from_another_module() -> None:
    """Grade the liveness checker's own source from outside it.

    A gutting planted in tests/test_liveness.py shows up as a finding in the
    census computed here, and nothing in that file can suppress this.
    """
    own = [
        "tests/liveness.py",
        "tests/test_liveness.py",
    ]
    survey = liveness.survey(REPO_ROOT, own)
    findings = [finding.rendered() for finding in [*survey.findings, *survey.dead_grading]]
    count = len(findings)
    population = len(survey.members)
    assert population > 1, (
        f"the liveness checker's own modules contribute {population} member(s) to its "
        "own population, so this cross-file grader is green about nothing"
    )
    assert not count, (
        f"{count} finding(s) in the liveness checker's own source, read from outside it: "
        f"{findings[:20]}"
    )


# ---------------------------------------------------------------------------
# CS-910 - what this module actually hands to the spawn
# ---------------------------------------------------------------------------


def test_the_git_this_module_spawns_is_resolved_and_never_named(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CS-910 - a RUNTIME reading, which the static census cannot give.

    ``tests/toolpath_guard.py`` grades this site by reading the source, and a
    source reading is only ever as good as its fold. This one intercepts the
    spawn itself and looks at the argv that was really built, so the two
    instruments have to agree before the claim stands.

    WHY IT MATTERS HERE SPECIFICALLY: a bare ``"git"`` in an argv is resolved by
    ``CreateProcess``, which searches the CURRENT DIRECTORY before PATH whenever
    the gate variable is absent from the environment - its state at both machine
    and user scope on the development machine. This tool walks trees it did not
    create and runs from wherever the operator is standing.

    NOTHING BELOW ASSERTS ON A PATH. Every assertion binds a boolean, because
    pytest renders the asserted expression independently of the message.
    """
    recorded: list[list[str]] = []

    def record(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        recorded.append(list(argv))
        return subprocess.CompletedProcess(list(argv), 0, "", "")

    monkeypatch.setattr(doc_budget.subprocess, "run", record)
    doc_budget._git(tmp_path, "rev-parse", "--show-toplevel")  # noqa: SLF001 - the site under test

    assert len(recorded) == 1, "the module did not spawn exactly once, so this grades nothing"
    program = recorded[0][0]
    rooted = Path(program).is_absolute()
    assert rooted, "the program handed to the spawn is not an absolute path"
    named = program == doc_budget.GIT_NAME
    assert not named, "the program handed to the spawn is the bare tool name"


def test_an_unresolvable_git_answers_none_rather_than_spawning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CS-910 - the refusal path, which the arm above cannot reach.

    A resolver that finds nothing must stop the spawn rather than fall back to
    the name, because falling back is exactly the behaviour being removed. This
    is the half that would go unmeasured if only the success path were graded.
    """
    spawned: list[object] = []

    def record(argv: object, **_kwargs: object) -> None:
        spawned.append(argv)

    monkeypatch.setattr(doc_budget, "resolve_tool", lambda _name: None)
    monkeypatch.setattr(doc_budget.subprocess, "run", record)

    answer = doc_budget._git(tmp_path, "rev-parse")  # noqa: SLF001 - the site under test

    assert answer is None
    assert spawned == [], "the module spawned something after the resolver refused"


# ---------------------------------------------------------------------------
# CS-1115 - a directory the tool could not LIST is reported, never globbed away
#
# ``glob`` and ``os.walk`` both swallow a refused listing and yield nothing, so
# a budgeted population behind a refused directory vanished from the table and
# the count, and the verdict still said every measured file was inside budget.
# Every fault here is REAL - an exclusive Windows handle, or a mode of zero -
# held by the drift guard suite's ``refused``, never a stub.
# ---------------------------------------------------------------------------


def _unlisted(rows: list[dict]) -> list[str]:
    """The files of every row whose directory could not be listed."""
    return sorted(row["file"] for row in rows if row["status"] == doc_budget.UNLISTED)


@pytest.mark.parametrize(
    ("directory", "leaf"),
    [("memory", "a-leaf.md"), ("docs/item_notes", "phase7.md")],
)
def test_a_refused_leaf_directory_is_an_unlisted_row(
    tmp_path: Path, directory: str, leaf: str
) -> None:
    """The leaves cannot be counted, so the DIRECTORY is the row, and the verdict says so."""
    from tests.data.test_drift_guard_data import refused  # noqa: PLC0415 - one fault helper

    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    folder = tmp_path / directory
    folder.mkdir(parents=True)
    (folder / leaf).write_text("# a leaf" + NEWLINE, encoding="ascii")
    assert f"{directory}/{leaf}" in _population(tmp_path), "control: the leaf is not measured"

    with refused(folder):
        with pytest.raises(PermissionError):
            list(folder.iterdir())
        rows = doc_budget.evaluate(tmp_path)
        text = NEWLINE.join(doc_budget.render(rows))

    # Graded first with symbols the pre-fix module has, so it fails on the
    # silent drop rather than on a missing attribute (non-negotiable 9).
    assert "VERDICT: PASS" not in text, text
    # TWO populations sit behind this one directory - its leaves, and any nested
    # CLAUDE.md the walk would have collected - so it may carry a row for each.
    assert set(_unlisted(rows)) == {f"{directory}/"}, rows
    leaf_rules = {"memory": "memory leaf", "docs/item_notes": "item-notes leaf"}
    assert [
        row["file"]
        for row in rows
        if row["status"] == doc_budget.UNLISTED and row["rule"] == leaf_rules[directory]
    ] == [f"{directory}/"], rows
    assert f"{directory}/{leaf}" not in [row["file"] for row in rows]
    assert "VERDICT: INCOMPLETE" in text, text
    assert "VERDICT: PASS" not in text, text


def test_a_refused_directory_under_a_walked_root_is_an_unlisted_row(tmp_path: Path) -> None:
    """The os.walk sibling: a nested CLAUDE.md behind a refused listing was dropped silently."""
    from tests.data.test_drift_guard_data import refused  # noqa: PLC0415 - one fault helper

    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    carried = tmp_path / "subsystem"
    carried.mkdir()
    (carried / "CLAUDE.md").write_text("# carried by this tree" + NEWLINE, encoding="ascii")
    assert "subsystem/CLAUDE.md" in _population(tmp_path), "control: the nested file is unmeasured"

    with refused(carried):
        observed = doc_budget.survey(tmp_path)
        rows = doc_budget.evaluate(tmp_path, observed)

    assert "subsystem/" in [row["file"] for row in rows], "the refused directory vanished"
    assert observed.unlisted == ("subsystem",), observed
    assert _unlisted(rows) == ["subsystem/"], rows
    assert [row["severity"] for row in rows if row["file"] == "subsystem/"] == ["HARD"]


def test_json_mode_reports_an_unlisted_directory_as_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The machine-readable verdict is never PASS over a directory nobody listed."""
    from tests.data.test_drift_guard_data import refused  # noqa: PLC0415 - one fault helper

    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "MEMORY.md").write_text("# index" + NEWLINE, encoding="ascii")
    monkeypatch.setattr(doc_budget, "repo_root", lambda: tmp_path)

    with refused(memory):
        code = doc_budget.main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["verdict"] == "INCOMPLETE", payload["verdict"]
    assert set(payload["unlisted"]) == {"memory/"}, payload
    assert code == 0, "the CLI still exits non-zero on a HARD failure only"


# ---------------------------------------------------------------------------
# CS-1117 - a DIRECTORY carrying a budgeted file's name is not a 0 byte file
#
# ``_entry`` took ``stat().st_size`` of whatever answered, and a directory
# answers - so a directory named like a leaf printed as an OK 0.0 KB row, and
# the verdict counted it measured and inside budget.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "relative", ["memory/zz-cs1117-dir.md", "docs/item_notes/zz-cs1117-dir.md", "ROADMAP.md"]
)
def test_a_directory_carrying_a_budgeted_name_is_its_own_finding(
    tmp_path: Path, relative: str
) -> None:
    """Never OK, never measured, and named under its own heading."""
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text("# index" + NEWLINE, encoding="ascii")
    (tmp_path / relative).mkdir(parents=True)

    rows = doc_budget.evaluate(tmp_path)
    text = NEWLINE.join(doc_budget.render(rows))
    matching = [row for row in rows if row["file"] == relative]

    # Graded first with symbols the pre-fix module has (non-negotiable 9).
    assert len(matching) == 1, rows
    assert matching[0]["status"] != "OK", matching
    assert matching[0]["actual_bytes"] is None, matching
    assert "VERDICT: PASS" not in text, text
    assert matching[0]["status"] == doc_budget.NOT_A_FILE, matching
    assert doc_budget.not_files(rows) == [relative], rows
    assert f"  {relative}" in text.split("NOT A FILE (")[1], text
    assert "VERDICT: NOT A FILE" in text, text


def test_an_absent_budgeted_file_is_still_missing_not_a_directory(tmp_path: Path) -> None:
    """The anti-narrowing control: absent stays MISSING, and a real file stays OK."""
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text("# index" + NEWLINE, encoding="ascii")

    rows = doc_budget.evaluate(tmp_path)
    by_file = {row["file"]: row["status"] for row in rows}

    assert by_file["ROADMAP.md"] == "MISSING", by_file
    assert by_file["CLAUDE.md"] == "OK", by_file
    assert by_file["memory/MEMORY.md"] == "OK", by_file
    assert doc_budget.not_files(rows) == [], rows
    assert "VERDICT: PASS" in NEWLINE.join(doc_budget.render(rows))


def test_json_mode_reports_a_directory_carrying_a_budgeted_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The machine-readable verdict names the finding; the exit code still moves on HARD only."""
    (tmp_path / "CLAUDE.md").write_text("# root" + NEWLINE, encoding="ascii")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "MEMORY.md").write_text("# index" + NEWLINE, encoding="ascii")
    (tmp_path / "memory" / "zz-cs1117-dir.md").mkdir()
    monkeypatch.setattr(doc_budget, "repo_root", lambda: tmp_path)

    code = doc_budget.main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["verdict"] == "NOT_A_FILE", payload["verdict"]
    assert payload["not_files"] == ["memory/zz-cs1117-dir.md"], payload
    assert code == 0, "the CLI still exits non-zero on a HARD failure only"
