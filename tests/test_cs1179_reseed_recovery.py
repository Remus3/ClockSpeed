"""CS-1179 - the way out of the CS-1176 R3 red, measured in a throwaway repository.

THE STATE BEING RECOVERED FROM (R3, named in the re-seed arm's module). Delete
``tools/provenance.tsv`` in a commit, commit an honest edit to a seed-era file
while it is absent, then run the advised restore
``git checkout <rev> -- tools/provenance.tsv``. The re-seed arm - the
``_reseed_grade`` helper the real-tree test drives - is then red for that file,
and stays red: the gap closes on bytes other than those it opened on, which is
exactly the shape of F1's lift, and the arm must not forgive F1.

THE RECOVERY, MEASURED HERE. Keep the edited bytes, ``git rm`` the path (the
tool's ``rm`` refuses a path still in the population), run
``python tools/provenance_stamp.py rm PATH``, put the bytes back, ``git add``
the path, and stamp it again with
``python tools/provenance_stamp.py add PATH --class authored --item CS-NNNN``.
The row that results carries basis ``stamped``. The re-seed arm grades only
``first-add:`` rows, so it no longer grades that path, and the recovered path
is green. It is therefore NOT the impossible route: the recovered row does not
read as a row postdating the seed.

WHY THE GREEN IS NOT A GRADER THAT FORGIVES EVERYTHING. The same repository
carries F1 - a seed-era path that left, came back as an unstamped lift, and was
brought back into the manifest by a re-seed. In the same run F1 stays red and
the recovered path is green, so the arm still discriminates.

TWO IN-TEST MUTANTS keep each half live. A stamp that keeps a ``first-add:``
basis does not recover, so the green depends on the recovery's own row. A
history whose blobs all compare equal forgives F1, so the F1 control depends on
the byte comparison. Each mutant is asserted to have LANDED before its verdict
is read.

RESIDUAL, measured rather than claimed away. The recovery is a per-path
declaration - a ``stamped`` row with an item id and a commit on it - so applied
to F1's own path it greens that path too. That is the re-seed arm's existing
residual, that a ``stamped`` row passes it, and is not new with this item: the
near-duplicate arm and the tool's own ``add`` refusals still grade the bytes.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import pytest

import tests.test_provenance_manifest as manifest_arm
from tests.test_provenance_manifest import (
    MANIFEST_RELATIVE,
    RESEED_LIFT_BYTES,
    History,
    Row,
    _commit,
    _git,
    _grade_repo,
    _missing_manifest_message,
    _parse_manifest,
    _repo_history,
    _reseed_grade,
    _stamp_tool,
    _tool,
)
from tests.test_third_party_register import REPO_ROOT, _listed_paths, _register_text

#: The seed-era path F1 removes and brings back as an unstamped lift through a re-seed.
F1_PATH = "pkg/alpha.py"

#: The seed-era path given an honest edit while the manifest is absent (R3).
R3_PATH = "pkg/omega.py"

#: A path stamped AFTER the seed, so its row carries basis ``stamped``.
STAMPED_PATH = "pkg/later.py"

#: The item every stamp in the throwaway tree cites; its ROADMAP.md records it.
ITEM = "CS-1165"

#: The runbook that carries the recovery recipe, repo-relative.
RUNBOOK = "docs/OPERATIONS.md"

#: The recipe's two tool commands, exactly as the runbook spells them.
RECIPE_COMMANDS = (
    "python tools/provenance_stamp.py rm PATH",
    "python tools/provenance_stamp.py add PATH --class authored --item CS-NNNN",
)


def _rows(root: Path) -> dict[str, Row]:
    """Return the work tree's manifest rows.

    Args:
        root: The throwaway work tree.

    Returns:
        The rows, keyed by path.
    """
    rows, faults = _parse_manifest((root / MANIFEST_RELATIVE).read_bytes())
    assert faults == [], f"the throwaway manifest breaks its grammar: {faults}"
    return rows


def _green_elsewhere(root: Path) -> dict[str, list[str]]:
    """Return every non-empty CS-1165 check over the throwaway tree.

    Args:
        root: The throwaway work tree.

    Returns:
        The checks that found something.
    """
    return {name: found for name, found in _grade_repo(root).items() if found}


@pytest.fixture
def seeded(tmp_path: Path) -> Path:
    """Return a throwaway repository whose manifest the REAL tool seeded.

    Args:
        tmp_path: pytest's per-test directory.

    Returns:
        The work tree, the seed committed, two seed-era ``pkg`` files in it.
    """
    root = tmp_path / "cs1179"
    root.mkdir()
    _git(root, "init", "-q")
    for name in [*_listed_paths(_register_text()), "THIRD_PARTY.md"]:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / name, root / name)
    (root / "docs").mkdir(exist_ok=True)
    (root / "ROADMAP.md").write_bytes(f"# Roadmap\n\n- {ITEM} open\n".encode("ascii"))
    (root / "docs" / "LEDGER.md").write_bytes(f"# Ledger\n\n- {ITEM} closed\n".encode("ascii"))
    (root / "pkg").mkdir()
    (root / F1_PATH).write_bytes(b'"""Alpha, written for this synthetic tree."""\n')
    (root / R3_PATH).write_bytes(b'"""Omega, written for this synthetic tree."""\n')
    _git(root, "add", "-A")
    _commit(root, f"{ITEM} - the tree before the seed")
    assert _tool(root, "bootstrap") == 0, "the real tool would not seed a fresh history"
    _git(root, "add", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - seed the manifest")
    rows = _rows(root)
    assert rows[F1_PATH].basis.startswith("first-add:"), "F1's path is not seed-era"
    assert rows[R3_PATH].basis.startswith("first-add:"), "R3's path is not seed-era"
    assert _reseed_grade(root).findings == [], "the seeded tree is not green pristine"
    return root


def _plant_f1(root: Path, monkeypatch: pytest.MonkeyPatch) -> Row:
    """Plant F1 and commit its re-seed: a seed-era row left and returned with a lift.

    Args:
        root: The throwaway work tree.
        monkeypatch: Blinds the tool's history lookup for the re-seed only.

    Returns:
        The seed's row for F1's path.
    """
    seed_row = _rows(root)[F1_PATH]
    _git(root, "rm", "-q", "--", F1_PATH)
    assert _tool(root, "rm", F1_PATH) == 0
    _git(root, "add", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - drop alpha")
    (root / F1_PATH).write_bytes(RESEED_LIFT_BYTES)
    _git(root, "add", "--", F1_PATH)
    _commit(root, f"{ITEM} - alpha returns as a lift")
    _git(root, "rm", "-q", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - lose the manifest")
    with monkeypatch.context() as blind:
        blind.setattr(_stamp_tool(), "last_committed_manifest", lambda _root: None)
        assert _tool(root, "bootstrap") == 0, "the blinded seed did not run"
    _git(root, "add", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - commit the re-seed")
    assert _rows(root)[F1_PATH] == seed_row, "F1 never landed: the re-seed row differs"
    assert (root / F1_PATH).read_bytes() == RESEED_LIFT_BYTES, "F1 never landed: no lift"
    return seed_row


def _delete_edit_restore(root: Path, path: str) -> bytes:
    """Delete the manifest, commit an honest edit to ``path``, then restore as advised.

    Args:
        root: The throwaway work tree.
        path: The file edited while the manifest is absent.

    Returns:
        The edited bytes.
    """
    held = _rows(root)[path]
    _git(root, "rm", "-q", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - lose the manifest")
    edited = (root / path).read_bytes() + b"# an honest edit made while the manifest was gone\n"
    (root / path).write_bytes(edited)
    _git(root, "add", "--", path)
    _commit(root, f"{ITEM} - edit while the manifest is absent")
    assert not (root / MANIFEST_RELATIVE).exists(), "the deletion never landed"
    rev = _stamp_tool().last_committed_manifest(root)
    assert rev is not None, "no commit holds a manifest to restore"
    _git(root, "checkout", rev, "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - restore the manifest as advised")
    assert _rows(root)[path] == held, "the advised restore did not bring the row back"
    assert (root / path).read_bytes() == edited, "the honest edit never landed"
    return edited


def _recover(root: Path, path: str) -> None:
    """THE RECOVERY: take the path out, drop its row, put it back, stamp it, commit.

    Args:
        root: The throwaway work tree.
        path: The path whose first-add row is replaced by a stamped one.
    """
    kept = (root / path).read_bytes()
    assert _tool(root, "rm", path) == manifest_arm.REFUSED_EXIT, "rm took a present path"
    _git(root, "rm", "-q", "--", path)
    assert _tool(root, "rm", path) == 0, "the tool would not drop the row"
    (root / path).write_bytes(kept)
    _git(root, "add", "--", path)
    assert _tool(root, "add", path, "--class", "authored", "--item", ITEM) == 0
    _git(root, "add", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - re-stamp the file edited while the manifest was gone")
    assert (root / path).read_bytes() == kept, "the recovery changed the file's bytes"


def _finding(path: str, row: Row) -> str:
    """Return the re-seed arm's finding for ``path``.

    Args:
        path: The row's path.
        row: The row.

    Returns:
        The finding string the arm emits.
    """
    return f"{path} ({row.basis})"


def blind(tree: Path) -> History:
    """THE F1 MUTANT: the real history, but every blob compares equal.

    Args:
        tree: A work tree.

    Returns:
        A history under which every gap is forgiven.
    """
    real = _repo_history(tree)
    return real._replace(blob=lambda _rev, _path: "same")


class Scenario(NamedTuple):
    """The combined F1 plus R3 tree, before the recovery is run."""

    root: Path
    f1_row: Row
    r3_row: Row
    edited: bytes


@pytest.fixture
def f1_and_r3(seeded: Path, monkeypatch: pytest.MonkeyPatch) -> Scenario:
    """Return one tree carrying F1 AND the R3 red, the restore already run.

    Args:
        seeded: The seeded throwaway tree.
        monkeypatch: Blinds the tool for F1's re-seed only.

    Returns:
        The scenario.
    """
    f1_row = _plant_f1(seeded, monkeypatch)
    r3_row = _rows(seeded)[R3_PATH]
    edited = _delete_edit_restore(seeded, R3_PATH)
    return Scenario(seeded, f1_row, r3_row, edited)


def test_cs1179_the_restore_leaves_r3_red_beside_f1(f1_and_r3: Scenario) -> None:
    # The state to recover from is real: after the advised restore, the R3 path
    # is red for its honest edit and F1 is red for its lift.
    grade = _reseed_grade(f1_and_r3.root)
    assert grade.findings == [
        _finding(F1_PATH, f1_and_r3.f1_row),
        _finding(R3_PATH, f1_and_r3.r3_row),
    ]


def test_cs1179_the_recovery_greens_r3_while_f1_stays_red_in_the_same_run(
    f1_and_r3: Scenario,
) -> None:
    root = f1_and_r3.root
    assert _reseed_grade(root).findings == [
        _finding(F1_PATH, f1_and_r3.f1_row),
        _finding(R3_PATH, f1_and_r3.r3_row),
    ], "the R3 red never landed, so a green after the recovery would prove nothing"
    _recover(root, R3_PATH)
    rows = _rows(root)
    assert rows[R3_PATH] == Row("authored", ITEM, "stamped"), rows[R3_PATH]
    assert (root / R3_PATH).read_bytes() == f1_and_r3.edited
    grade = _reseed_grade(root)
    # F1 is NOT forgiven: it is the only finding, and the arm still graded rows.
    assert grade.findings == [_finding(F1_PATH, f1_and_r3.f1_row)]
    assert grade.first_adds > 1, grade
    assert _green_elsewhere(root) == {}
    assert _tool(root, "check") == 0


def test_cs1179_the_recovery_alone_returns_the_whole_arm_green(seeded: Path) -> None:
    held = _rows(seeded)[R3_PATH]
    edited = _delete_edit_restore(seeded, R3_PATH)
    assert _reseed_grade(seeded).findings == [_finding(R3_PATH, held)], "R3 never landed"
    _recover(seeded, R3_PATH)
    grade = _reseed_grade(seeded)
    assert grade.findings == []
    assert grade.first_adds > 1, grade
    assert grade.versions > 1, grade
    assert (seeded / R3_PATH).read_bytes() == edited
    assert _green_elsewhere(seeded) == {}
    assert _tool(seeded, "check") == 0


def test_cs1179_a_stamped_row_edited_while_absent_is_green_after_the_restore_alone(
    seeded: Path,
) -> None:
    # The other reading of "a stamped file": a row the tool's add wrote carries
    # basis `stamped`, which the re-seed arm never grades, so the restore alone
    # is enough and no recovery is needed.
    (seeded / STAMPED_PATH).write_bytes(b"x = 'stamped after the seed'\n")
    assert _tool(seeded, "add", STAMPED_PATH, "--class", "authored", "--item", ITEM) == 0
    _git(seeded, "add", "-A")
    _commit(seeded, f"{ITEM} - stamp a later file")
    assert _rows(seeded)[STAMPED_PATH].basis == "stamped"
    _delete_edit_restore(seeded, STAMPED_PATH)
    assert _reseed_grade(seeded).findings == []
    assert _green_elsewhere(seeded) == {}


def test_cs1179_mutant_a_restamp_that_keeps_first_add_does_not_recover(
    f1_and_r3: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Live arm for the recovery's green: the green comes from the `stamped`
    # basis the tool's add writes. A stamp writing a first-add basis leaves R3 red.
    # The mutant basis differs from the seed's, so the recovery still commits a change.
    mutant = "first-add:root"
    assert f1_and_r3.r3_row.basis != mutant, f1_and_r3.r3_row
    tool = _stamp_tool()
    monkeypatch.setattr(tool, "STAMPED", mutant)
    assert mutant == tool.STAMPED, "the mutant never landed"
    _recover(f1_and_r3.root, R3_PATH)
    assert _rows(f1_and_r3.root)[R3_PATH].basis == mutant
    assert R3_PATH in {entry.split(" ", 1)[0] for entry in _reseed_grade(f1_and_r3.root).findings}


def test_cs1179_mutant_a_history_blind_to_bytes_forgives_f1(
    f1_and_r3: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Live arm for the F1 control: with every blob comparing equal, the gap
    # forgiveness forgives F1's lift, so the control above is red only because
    # the arm compares the bytes either side of the gap.
    root = f1_and_r3.root
    monkeypatch.setattr(manifest_arm, "_repo_history", blind)
    assert vars(manifest_arm)["_repo_history"] is blind, "the mutant never landed"
    assert _reseed_grade(root).findings == []
    monkeypatch.undo()
    assert _reseed_grade(root).findings != [], "the pristine arm did not come back red"


@pytest.fixture(autouse=True)
def _restore_stamp_constant() -> Iterator[None]:
    """Assert no test leaves the shared tool module's stamp basis mutated.

    Yields:
        Nothing; the check runs after the test.
    """
    yield
    assert _stamp_tool().STAMPED == "stamped", "a mutant of the stamp basis leaked"


def test_cs1179_residual_the_recovery_is_a_declaration_on_any_path(
    f1_and_r3: Scenario,
) -> None:
    # RESIDUAL, measured: applied to F1's own path the recovery greens it too,
    # because a `stamped` row is a declaration the re-seed arm does not grade.
    # The row it leaves names the class, the item and the basis in a commit.
    root = f1_and_r3.root
    _recover(root, F1_PATH)
    assert _rows(root)[F1_PATH] == Row("authored", ITEM, "stamped")
    assert _finding(F1_PATH, f1_and_r3.f1_row) not in _reseed_grade(root).findings


def test_cs1179_after_the_recovery_f1_is_still_named_and_only_by_the_byte_check(
    f1_and_r3: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The F1 control AFTER the recovery, with no precondition in front of it, so
    # a mutant of the byte comparison reddens THIS assert rather than a
    # precondition that happens to run first.
    root = f1_and_r3.root
    _recover(root, R3_PATH)
    assert _reseed_grade(root).findings == [_finding(F1_PATH, f1_and_r3.f1_row)]
    with monkeypatch.context() as mutant:
        mutant.setattr(manifest_arm, "_repo_history", blind)
        assert vars(manifest_arm)["_repo_history"] is blind, "the mutant never landed"
        assert _reseed_grade(root).findings == [], "F1 survived a history blind to bytes"


def _lose_the_manifest(root: Path) -> None:
    """Delete the manifest in a commit.

    Args:
        root: The throwaway work tree.
    """
    _git(root, "rm", "-q", "--", MANIFEST_RELATIVE)
    _commit(root, f"{ITEM} - lose the manifest")
    assert not (root / MANIFEST_RELATIVE).exists(), "the deletion never landed"


def test_cs1179_the_tool_missing_manifest_advice_names_the_recovery(seeded: Path) -> None:
    _lose_the_manifest(seeded)
    advice = _stamp_tool().restore_advice(seeded)
    assert "git checkout " in advice, "the advice lost the restore"
    assert RUNBOOK in advice, "the tool's missing-manifest advice does not name the runbook"
    assert "CS-1179" in advice


def test_cs1179_the_arm_missing_manifest_red_names_the_recovery(seeded: Path) -> None:
    _lose_the_manifest(seeded)
    message = _missing_manifest_message(seeded)
    assert "git checkout " in message, "the red lost the restore"
    assert RUNBOOK in message, "the arm's missing-manifest red does not name the runbook"
    assert "CS-1179" in message


def test_cs1179_the_runbook_carries_the_recipe_and_what_it_does_not_do() -> None:
    text = (REPO_ROOT / RUNBOOK).read_text(encoding="ascii")
    start = text.find("(CS-1179)")
    assert start >= 0, f"{RUNBOOK} carries no CS-1179 recovery entry"
    end = text.find("\n\n**", start)
    entry = text[start : end if end >= 0 else len(text)]
    for command in RECIPE_COMMANDS:
        assert command in entry, f"the runbook entry lacks `{command}`"
    assert "`stamped`" in entry, "the entry does not say the row it leaves is stamped"
    assert "tests/test_provenance_manifest.py" in entry, "the entry cites no residual"
