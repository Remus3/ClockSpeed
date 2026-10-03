"""CS-920 - every reading this project takes of ITSELF carries its own receipt.

THE DEFECT THIS MODULE CLOSES. A measured number published in prose carries its
provenance at DOCUMENT scope: the conditions it was taken under live in the
surrounding paragraph and do not travel when the figure is quoted. Three numbers
were published and then corrected on this project in one session alone, and none
of the three was a careless reading - each was a correct reading whose CONDITIONS
did not travel with it. `tools/measurements.json` gives every reading a ROW-scoped
receipt and `tools/measurement_record.py` grades it.

THE ARM THE ACCEPTANCE CLAUSE NAMES is
:func:`test_a_reading_missing_any_receipt_field_is_an_offence`, which strips each
receipt field in turn from the TRACKED record and asserts the grader names it.
Stripping from the tracked record rather than from a hand-built row is deliberate:
an arm built on its own fixture stays green when the shipped record grows a shape
the fixture does not have.

WHAT THE QUERY ANSWERS, AND WHY IT REPORTS A BASIS RATHER THAN A BARE VERDICT.
CS-917's acceptance asks for a noise figure that SURVIVES ITS OWN NEXT READING.
That is a query over a measurement history, and this project has already published
a false delta by comparing a SERIAL reading against a PARALLEL one. So the tool's
`survives_next_reading` reports the comparability of the pair beside the
verdict: a pair whose worker count or load state is not recorded is `unproven`,
and a pair that disagrees on them cannot falsify anything at all.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_SOURCE = REPO_ROOT / "tools" / "measurement_record.py"
RECORD_SOURCE = REPO_ROOT / "tools" / "measurements.json"

#: THE RECEIPT, PINNED HERE AS WELL AS IN THE TOOL. The acceptance clause names
#: these eight by name, so a tool that quietly drops one is red here.
EXPECTED_RECEIPT_FIELDS = (
    "metric",
    "value",
    "unit",
    "method",
    "workers",
    "contended",
    "date",
    "commit",
)


def _load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cs920_measurement_record", TOOL_SOURCE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return _load_tool()


@pytest.fixture(scope="module")
def tracked() -> dict[str, Any]:
    record: dict[str, Any] = json.loads(RECORD_SOURCE.read_text(encoding="utf-8"))
    return record


def test_the_tool_and_the_record_are_both_present() -> None:
    """Named for what it asserts. It checks PRESENCE, not that git knows the file.

    CS-920's verifier found the earlier name claimed the stronger property and
    would have stayed green on an untracked file. The weaker check is the one
    that is wanted here - a repo-wide guard already enumerates through git - so
    the name moved to the check rather than the check to the name.
    """
    assert TOOL_SOURCE.is_file()
    assert RECORD_SOURCE.is_file()


def test_the_receipt_is_the_eight_fields_the_acceptance_clause_names(tool: ModuleType) -> None:
    assert tool.RECEIPT_FIELDS == EXPECTED_RECEIPT_FIELDS


def test_the_tracked_record_grades_clean(tool: ModuleType) -> None:
    """CS-1223 F3: a witness the clone could not re-derive is never a silent pass.

    In a full-history clone (tier2's suite job, the operator's box) an unchecked
    witness FAILS here; in a shallow one (tier1's fast job) it warns, by count.
    """
    unchecked: list[str] = []
    offences = tool.grade_tree(REPO_ROOT, unchecked)
    assert offences == [], "\n".join(offences)
    count = len(unchecked)
    if count and tool.is_shallow(REPO_ROOT):
        warnings.warn(
            f"{count} witness(es) not re-derived - shallow clone", UserWarning, stacklevel=1
        )
        return
    assert count == 0, "\n".join(unchecked)


def test_the_tracked_record_holds_at_least_one_reading(tracked: dict[str, Any]) -> None:
    # A grader over an empty list is green for the wrong reason.
    assert len(tracked["readings"]) >= 1


@pytest.mark.parametrize("field", EXPECTED_RECEIPT_FIELDS)
def test_a_reading_missing_any_receipt_field_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any], field: str
) -> None:
    """THE ACCEPTANCE ARM - a reading added without its receipt reddens."""
    record = copy.deepcopy(tracked)
    del record["readings"][0][field]
    offences = tool.grade(record)
    assert any(field in offence for offence in offences), offences


def test_a_reading_carrying_an_undeclared_field_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["looks_fine"] = "but is not on the allowlist"
    offences = tool.grade(record)
    assert any("looks_fine" in offence for offence in offences), offences


def test_a_reading_whose_unit_disagrees_with_its_metric_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    reading = record["readings"][0]
    declared = record["metrics"][reading["metric"]]["unit"]
    reading["unit"] = next(unit for unit in tool.UNITS if unit != declared)
    offences = tool.grade(record)
    assert any("unit" in offence for offence in offences), offences


def test_a_reading_of_an_undeclared_metric_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["metric"] = "nobody_declared_this_one"
    offences = tool.grade(record)
    assert any("nobody_declared_this_one" in offence for offence in offences), offences


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workers", 0),
        ("workers", "eight"),
        ("workers", True),
        ("contended", "yes"),
        ("date", "2026-9-5"),
        ("date", "2026-02-30"),
        ("commit", "nothexatall"),
        ("commit", "abc"),
        ("method", "vibes"),
        ("value", "590.82"),
        ("value", True),
    ],
)
def test_a_receipt_field_outside_its_domain_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any], field: str, value: object
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0][field] = value
    offences = tool.grade(record)
    assert any(field in offence for offence in offences), offences


def test_the_two_escape_values_are_accepted_and_nothing_else_is(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """A reading whose worker count or load state was never recorded is KEPT.

    Losing the reading would be worse than keeping it. What the escape value
    costs is stated and enforced elsewhere: such a reading can never be found
    COMPARABLE, so it can never produce a delta.
    """
    record = copy.deepcopy(tracked)
    record["readings"][0]["workers"] = tool.WORKERS_UNRESOLVED
    record["readings"][0]["contended"] = tool.CONTENDED_UNKNOWN
    # CS-1223: an edited seed row is a new row and loses the tree escape, so it
    # records a tree; the escapes graded here are the worker and load ones.
    record["readings"][0]["tree"] = tool.TREE_DIRTY
    assert tool.grade(record) == []


def _graded_in(tool: ModuleType, root: Path, record: dict[str, Any]) -> list[str]:
    (root / "tools").mkdir(exist_ok=True)
    (root / "tools" / "measurements.json").write_text(json.dumps(record), encoding="utf-8")
    offences: list[str] = tool.grade_tree(root)
    return offences


def test_a_source_citation_must_name_a_file_that_exists(
    tool: ModuleType, tracked: dict[str, Any], tmp_path: Path
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["source"] = ["docs/THIS_FILE_DOES_NOT_EXIST.md#anywhere"]
    offences = _graded_in(tool, tmp_path, record)
    assert any("THIS_FILE_DOES_NOT_EXIST" in offence for offence in offences), offences


def test_a_source_citation_whose_anchor_is_gone_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any], tmp_path: Path
) -> None:
    """A LINE NUMBER INTO `docs/LEDGER.md` WOULD CHECK NOTHING.

    That file is append-at-TOP, so every line number in it is stale as soon as
    the next entry lands. An anchor is text that must still appear, so the
    citation survives the file growing and reddens when the sentence it names is
    reworded away - which is the event that leaves a number with no provenance.
    """
    record = copy.deepcopy(tracked)
    record["readings"][0]["source"] = ["docs/LEDGER.md#no sentence in that file says this"]
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "LEDGER.md").write_text("## Entries", encoding="utf-8")
    offences = _graded_in(tool, tmp_path, record)
    assert any("anchor" in offence for offence in offences), offences


def test_a_reading_with_no_source_citation_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["source"] = []
    offences = tool.grade(record)
    assert any("source" in offence for offence in offences), offences


def test_supersession_must_name_a_later_reading_of_the_same_metric(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["superseded_by"] = 0
    offences = tool.grade(record)
    assert any("superseded_by" in offence for offence in offences), offences


# ---------------------------------------------------------------------------
# THE QUERY. CS-917's survives-its-next-reading test, answered mechanically.
# ---------------------------------------------------------------------------


def _reading(**overrides: Any) -> dict[str, Any]:
    reading = {
        "metric": "a_noise_figure_seconds",
        "value": 21,
        "unit": "seconds",
        "method": "derived",
        "workers": 8,
        "contended": False,
        "date": "2026-09-05",
        "commit": "c33afca",
        "tree": "clean",
        "source": ["docs/LEDGER.md### Entries"],
        "superseded_by": None,
    }
    reading.update(overrides)
    return reading


def _bound_record(*readings: dict[str, Any]) -> dict[str, Any]:
    return {
        "metrics": {
            "a_noise_figure_seconds": {"kind": "bound", "unit": "seconds", "sense": "upper"}
        },
        "readings": list(readings),
    }


def test_a_noise_figure_its_next_reading_exceeds_is_reported_falsified(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=21, date="2026-09-05"),
        _reading(value=36, date="2026-09-06"),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert [v["verdict"] for v in verdicts] == [tool.FALSIFIED, tool.UNTESTED]
    assert verdicts[0]["basis"] == tool.COMPARABLE


def test_a_noise_figure_its_next_reading_does_not_exceed_survives(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=36, date="2026-09-05"),
        _reading(value=21, date="2026-09-06"),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["verdict"] == tool.SURVIVED


def test_a_single_reading_is_untested_rather_than_surviving(tool: ModuleType) -> None:
    record = _bound_record(_reading(value=21))
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert [v["verdict"] for v in verdicts] == [tool.UNTESTED]


def test_a_pair_disagreeing_on_worker_count_cannot_falsify(tool: ModuleType) -> None:
    """THE DEFECT THIS RULE EXISTS FOR, measured on this project.

    A published growth of +57s compared a SERIAL reading against a PARALLEL one.
    The two are not comparable and the growth was not established by them.
    """
    record = _bound_record(
        _reading(value=21, date="2026-09-05", workers=1),
        _reading(value=36, date="2026-09-06", workers=8),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["verdict"] == tool.UNTESTED
    assert verdicts[0]["basis"] == tool.NOT_COMPARABLE


def test_a_pair_disagreeing_on_load_state_cannot_falsify(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=21, date="2026-09-05", contended=False),
        _reading(value=36, date="2026-09-06", contended=True),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["basis"] == tool.NOT_COMPARABLE


def test_an_unrecorded_worker_count_makes_the_comparison_unproven_not_comparable(
    tool: ModuleType,
) -> None:
    """The escape value is kept, and this is the price it pays.

    Both readings agree on every recorded field, so the pair is not REFUSED -
    but the field they agree on is `unresolved`, which is agreement about
    nothing. The verdict still lands; its basis says what it rests on.
    """
    record = _bound_record(
        _reading(value=21, date="2026-09-05", workers=tool.WORKERS_UNRESOLVED),
        _reading(value=36, date="2026-09-06", workers=tool.WORKERS_UNRESOLVED),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["verdict"] == tool.FALSIFIED
    assert verdicts[0]["basis"] == tool.UNPROVEN


def test_a_superseded_reading_is_reported_as_superseded(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=21, date="2026-09-05", superseded_by=1),
        _reading(value=36, date="2026-09-06"),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["verdict"] == tool.SUPERSEDED


def test_the_query_orders_by_date_rather_than_by_record_position(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=36, date="2026-09-06"),
        _reading(value=21, date="2026-09-05"),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert [v["value"] for v in verdicts] == [21, 36]
    assert verdicts[0]["verdict"] == tool.FALSIFIED


def test_the_query_refuses_a_metric_that_is_not_a_bound(tool: ModuleType) -> None:
    record = {
        "metrics": {"a_duration_seconds": {"kind": "observation", "unit": "seconds"}},
        "readings": [_reading(metric="a_duration_seconds")],
    }
    with pytest.raises(ValueError, match="bound"):
        tool.survives_next_reading(record, "a_duration_seconds")


def test_the_query_refuses_a_metric_nobody_declared(tool: ModuleType) -> None:
    with pytest.raises(KeyError):
        tool.survives_next_reading(_bound_record(), "no_such_metric")


def test_the_cli_grades_the_tree_and_exits_zero(tool: ModuleType) -> None:
    assert tool.main([]) == 0


def test_the_cli_answers_the_survives_query_for_every_bound_metric(
    tool: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    assert tool.main(["--survives"]) == 0
    printed = capsys.readouterr().out
    assert "survives" in printed


# ---------------------------------------------------------------------------
# CS-1220. A reading records the TREE it was taken over, and a pair resting on
# an unrecorded tree is never `comparable`.
# ---------------------------------------------------------------------------

#: A reading dated on or after the day the witness became required. Any later
#: date works; this one is fixed so the arm cannot rot into the grandfathered
#: window as the calendar moves.
_NEW_READING_DATE = "2026-10-03"

#: The locally-sourced methods - every method but the runner-checkout pair.
_LOCAL_METHODS = ("paired", "unpaired", "local_suite", "profile")

#: The rows seeded before CS-1220 - marked, never re-seeded or re-dated.
_SEEDED_ROWS = 16


def _new_local_reading(tracked: dict[str, Any], method: str) -> dict[str, Any]:
    reading: dict[str, Any] = copy.deepcopy(tracked["readings"][8])
    reading["method"] = method
    reading["date"] = _NEW_READING_DATE
    reading.pop("tree", None)
    return reading


@pytest.mark.parametrize("method", _LOCAL_METHODS)
def test_a_new_local_reading_with_no_tree_field_is_refused(
    tool: ModuleType, tracked: dict[str, Any], method: str
) -> None:
    """THE FIRST ACCEPTANCE ARM - a new local reading must say what tree it read."""
    record = copy.deepcopy(tracked)
    record["readings"].append(_new_local_reading(tracked, method))
    new_index = len(record["readings"]) - 1
    offences = tool.grade(record)
    named = [o for o in offences if o.startswith(f"reading {new_index}:") and "tree" in o]
    assert named, offences


@pytest.mark.parametrize("method", _LOCAL_METHODS)
def test_a_new_local_reading_may_not_claim_the_unwitnessed_escape(
    tool: ModuleType, tracked: dict[str, Any], method: str
) -> None:
    """The escape exists for rows taken BEFORE the witness was required, only."""
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, method)
    reading["tree"] = tool.TREE_UNWITNESSED
    record["readings"].append(reading)
    new_index = len(record["readings"]) - 1
    offences = tool.grade(record)
    named = [o for o in offences if o.startswith(f"reading {new_index}:") and "tree" in o]
    assert named, offences


@pytest.mark.parametrize("tree", ["clean", "dirty"])
def test_a_new_local_reading_that_records_its_tree_grades_clean(
    tool: ModuleType, tracked: dict[str, Any], tree: str
) -> None:
    # The control for the two refusal arms: they refuse the omission, not the row.
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, "profile")
    reading["tree"] = tree
    if tree == "clean":
        # CS-1223: a local `clean` claim carries a witness; its digest is
        # re-derived only by grade_tree, so a well-formed one suffices here.
        reading["witness"] = _WELL_FORMED_WITNESS
    record["readings"].append(reading)
    assert tool.grade(record) == []


def test_a_tree_value_outside_its_domain_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][0]["tree"] = "probably_clean"
    offences = tool.grade(record)
    assert any("tree" in offence for offence in offences), offences


def test_every_tracked_row_predating_the_witness_is_marked_unwitnessed(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """The sixteen seeded rows are MARKED, not re-seeded: no tree was recorded."""
    legacy = [r for r in tracked["readings"] if r["date"] < tool.TREE_WITNESS_REQUIRED_FROM]
    assert len(legacy) >= _SEEDED_ROWS
    assert {r["tree"] for r in legacy} == {tool.TREE_UNWITNESSED}


def test_a_pair_where_exactly_one_side_has_no_tree_witness_is_not_comparable(
    tool: ModuleType,
) -> None:
    """THE SECOND ACCEPTANCE ARM. Every other field agrees; only the tree differs."""
    witnessed = _reading(tree="clean")
    unwitnessed = _reading(tree="unwitnessed")
    for left, right in ((witnessed, unwitnessed), (unwitnessed, witnessed)):
        verdict = tool.comparability(left, right)
        assert verdict != tool.COMPARABLE
        assert verdict == tool.UNWITNESSED_TREE
    # The control: the same pair, both witnessed clean, IS comparable.
    assert tool.comparability(witnessed, _reading(tree="clean")) == tool.COMPARABLE


def test_a_pair_where_both_sides_have_no_tree_witness_is_not_comparable(
    tool: ModuleType,
) -> None:
    verdict = tool.comparability(_reading(tree="unwitnessed"), _reading(tree="unwitnessed"))
    assert verdict == tool.UNWITNESSED_TREE


def test_a_reading_over_a_dirty_tree_is_not_comparable_with_anything(tool: ModuleType) -> None:
    # A dirty tree is not identified by its commit, so it measured unnamed code.
    for other in ("clean", "dirty"):
        verdict = tool.comparability(_reading(tree="dirty"), _reading(tree=other))
        assert verdict == tool.NOT_COMPARABLE


def test_an_unwitnessed_pair_cannot_falsify_a_bound(tool: ModuleType) -> None:
    record = _bound_record(
        _reading(value=21, date="2026-09-05", tree="unwitnessed"),
        _reading(value=36, date="2026-09-06", tree="clean"),
    )
    verdicts = tool.survives_next_reading(record, "a_noise_figure_seconds")
    assert verdicts[0]["verdict"] == tool.UNTESTED
    assert verdicts[0]["basis"] == tool.UNWITNESSED_TREE


# ---------------------------------------------------------------------------
# CS-1223. The `unwitnessed` escape is a PINNED SEED SET, not a date, and a
# local `clean` claim carries a witness the grader re-derives from its commit.
# ---------------------------------------------------------------------------

#: A freeze_witness record of the right shape. Its digests are arbitrary, so it
#: can only pass `grade`, which checks shape; `grade_tree` re-derives the digest.
_WELL_FORMED_WITNESS: dict[str, Any] = {
    "schema": 2,
    "tree": "0" * 64,
    "tree_files": 3,
    "bytecode": "1" * 64,
    "bytecode_files": 0,
}

#: A date BEFORE the CS-1220 cutover, so a date-gated escape would accept it.
_BACKDATED = "2026-09-06"

_GIT_TIMEOUT = 120


def _tree_offences(offences: list[str], index: int) -> list[str]:
    return [o for o in offences if o.startswith(f"reading {index}:") and "tree" in o]


@pytest.mark.parametrize("method", [*_LOCAL_METHODS, "ci_job", "derived"])
def test_a_backdated_new_row_may_not_claim_the_unwitnessed_escape(
    tool: ModuleType, tracked: dict[str, Any], method: str
) -> None:
    """THE FIRST CS-1223 ARM. A new row dated before the cutover is still a new row."""
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, method)
    reading["date"] = _BACKDATED
    reading["tree"] = tool.TREE_UNWITNESSED
    assert reading["date"] < tool.TREE_WITNESS_REQUIRED_FROM
    record["readings"].append(reading)
    index = len(record["readings"]) - 1
    assert _tree_offences(tool.grade(record), index), tool.grade(record)


def test_a_copy_of_a_seeded_row_may_not_claim_the_escape_twice(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    # Pinned by identity, so a verbatim duplicate would otherwise ride the pin.
    record = copy.deepcopy(tracked)
    record["readings"].append(copy.deepcopy(tracked["readings"][8]))
    index = len(record["readings"]) - 1
    assert _tree_offences(tool.grade(record), index)


@pytest.mark.parametrize("field", ["source", "extra_witness", "unit", "contended"])
def test_a_seeded_row_with_any_field_edited_loses_the_escape(
    tool: ModuleType, tracked: dict[str, Any], field: str
) -> None:
    """CS-1223 F1. Any edit to a seed row but its `superseded_by` loses the escape."""
    record = copy.deepcopy(tracked)
    row = record["readings"][8]
    if field == "source":
        row["source"] = list(tracked["readings"][0]["source"])
    elif field == "unit":
        row["unit"] = "ratio"
    elif field == "contended":
        row["contended"] = "unknown"
    else:
        row["witness"] = _WELL_FORMED_WITNESS
    assert _tree_offences(tool.grade(record), 8), tool.grade(record)


def test_a_seeded_row_may_still_be_superseded(tool: ModuleType, tracked: dict[str, Any]) -> None:
    """CS-1223 R12. Setting `superseded_by` is ordinary record use, not an edit."""
    record = copy.deepcopy(tracked)
    later = _new_local_reading(tracked, "profile")
    later["tree"] = "dirty"
    record["readings"].append(later)
    record["readings"][8]["superseded_by"] = len(record["readings"]) - 1
    assert tool.grade(record) == []


def test_a_seeded_row_with_an_edited_value_loses_the_escape(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][8]["value"] = 111.4
    assert _tree_offences(tool.grade(record), 8)


@pytest.mark.parametrize("method", _LOCAL_METHODS)
def test_a_local_clean_reading_with_no_witness_is_refused(
    tool: ModuleType, tracked: dict[str, Any], method: str
) -> None:
    """THE SECOND CS-1223 ARM. `clean` from a local box must carry its evidence."""
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, method)
    reading["tree"] = tool.TREE_CLEAN
    record["readings"].append(reading)
    index = len(record["readings"]) - 1
    named = [o for o in tool.grade(record) if o.startswith(f"reading {index}:") and "witness" in o]
    assert named, tool.grade(record)


_CI_RUN = "https://github.com/Remus3/Clockspeed/actions/runs/12345678901/job/23456789012"


def test_the_pinned_repository_is_the_one_the_citation_file_names(tool: ModuleType) -> None:
    # Ground truth with no remote: the tracked CITATION.cff names the repository.
    lines = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8").splitlines()
    named = [ln.split(":", 1)[1].strip() for ln in lines if ln.startswith("repository-code:")]
    assert named == [tool.REPOSITORY_URL]
    assert _CI_RUN.startswith(tool.REPOSITORY_URL + "/actions/runs/")


#: Round 4: a reading citing a run carries a FULL commit. Two distinct ones.
_FULL_A = "e3169a64770a00fd4484452148a9ef66ac33cb7b"
_FULL_B = "0123456789abcdef0123456789abcdef01234567"


def _ci_clean(tracked: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    reading = _new_local_reading(tracked, "ci_job")
    reading["tree"] = "clean"
    reading["commit"] = _FULL_A
    reading.update(overrides)
    return reading


def test_a_runner_clean_reading_needs_no_witness(tool: ModuleType, tracked: dict[str, Any]) -> None:
    # Control for the second arm: the runner's fresh checkout, cited, IS the witness.
    record = copy.deepcopy(tracked)
    record["readings"].append(_ci_clean(tracked, ci_run=_CI_RUN))
    assert tool.grade(record) == []


def _named(tool: ModuleType, record: dict[str, Any], index: int, word: str) -> list[str]:
    return [o for o in tool.grade(record) if o.startswith(f"reading {index}:") and word in o]


@pytest.mark.parametrize(
    "ci_run",
    [
        None,
        "",
        "run 12345",
        "https://github.com/example/clockspeed/actions/runs/",
        "https://github.com/example/clockspeed/actions/runs/12x",
        "https://example.invalid/example/clockspeed/actions/runs/123",
        "https://github.com/example/clockspeed/actions/runs/123",
        "https://github.com/Remus3/Other/actions/runs/123",
        "https://github.com/Remus3/Clockspeed/actions/runs/123/../../../Other/runs/9",
        "https://github.com/Remus3/Clockspeed/../Other/actions/runs/123",
        "https://github.com/Remus3/Clockspeed/actions/workflows/123",
        "https://github.com/Remus3/Clockspeed/actions/runs/123/job/",
        "https://github.com/Remus3/Clockspeed/actions/runs/123?x=1",
        # Round 3: a trailing newline (`$` would accept it), the owner and name in
        # another case (`(?i)` would), and non-ASCII digits (`\\d` would).
        "https://github.com/Remus3/Clockspeed/actions/runs/123\n",
        "https://github.com/remus3/clockspeed/actions/runs/123",
        "https://github.com/Remus3/Clockspeed/actions/runs/\u0661\u0662\u0663",
        "https://github.com/Remus3/Clockspeed/actions/runs/123/job/\u0661",
        12345,
    ],
)
def test_a_runner_clean_reading_must_cite_its_run(
    tool: ModuleType, tracked: dict[str, Any], ci_run: Any
) -> None:
    """CS-1223 F2(b). `clean` BY THE RUNNER'S CHECKOUT names the run that checked out."""
    record = copy.deepcopy(tracked)
    reading = _ci_clean(tracked) if ci_run is None else _ci_clean(tracked, ci_run=ci_run)
    record["readings"].append(reading)
    assert _named(tool, record, len(record["readings"]) - 1, "ci_run"), tool.grade(record)


def _derived_clean(tracked: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    reading = _new_local_reading(tracked, "derived")
    reading["tree"] = "clean"
    reading["commit"] = _FULL_A
    reading.update(overrides)
    return reading


def test_a_derived_clean_reading_over_runner_inputs_grades_clean(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    # Control for F2(a): every input is a cited, clean runner reading.
    record = copy.deepcopy(tracked)
    record["readings"].append(_ci_clean(tracked, ci_run=_CI_RUN))
    first = len(record["readings"]) - 1
    record["readings"].append(_ci_clean(tracked, ci_run=_CI_RUN, value=112.0))
    record["readings"].append(_derived_clean(tracked, inputs=[first, first + 1]))
    assert tool.grade(record) == []


@pytest.mark.parametrize("inputs", ["absent", [], "local", "unwitnessed", "self", "range", "x"])
def test_a_derived_clean_reading_needs_runner_inputs(
    tool: ModuleType, tracked: dict[str, Any], inputs: Any
) -> None:
    """CS-1223 F2(a). `derived` may claim `clean` only if every input is a runner reading."""
    record = copy.deepcopy(tracked)
    local = _new_local_reading(tracked, "profile")
    local["tree"] = "dirty"
    record["readings"].append(local)
    local_index = len(record["readings"]) - 1
    derived_index = local_index + 1
    named = {
        "local": [local_index],
        "unwitnessed": [0],
        "self": [derived_index],
        "range": [derived_index + 5],
        "x": ["0"],
    }
    if inputs == "absent":
        reading = _derived_clean(tracked)
    else:
        reading = _derived_clean(
            tracked, inputs=named[inputs] if isinstance(inputs, str) else inputs
        )
    record["readings"].append(reading)
    assert _named(tool, record, derived_index, "input"), tool.grade(record)


def _runner_record(tracked: dict[str, Any], *readings: dict[str, Any]) -> dict[str, Any]:
    """A record of ONLY the given readings, so an index means exactly that row."""
    return {"metrics": copy.deepcopy(tracked["metrics"]), "readings": list(readings)}


def test_a_derived_clean_reading_over_a_witnessed_local_reading_is_refused(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """Mutant C. A `clean` LOCAL input is still not a runner input."""
    local = _new_local_reading(tracked, "profile")
    local["tree"] = "clean"
    local["witness"] = _WELL_FORMED_WITNESS
    record = _runner_record(tracked, local, _derived_clean(tracked, inputs=[0]))
    assert _named(tool, record, 1, "is not a 'ci_job' reading"), tool.grade(record)


def test_a_ci_run_on_any_other_method_is_refused(tool: ModuleType, tracked: dict[str, Any]) -> None:
    """Mutant R. A well-formed run URL on a local reading is a false citation."""
    reading = _new_local_reading(tracked, "profile")
    reading["tree"] = "dirty"
    reading["ci_run"] = _CI_RUN
    record = _runner_record(tracked, reading)
    assert _named(tool, record, 0, "ci_run is carried only"), tool.grade(record)


@pytest.mark.parametrize("target", ["self", True, False])
def test_a_derived_input_naming_itself_or_a_bool_is_refused(
    tool: ModuleType, tracked: dict[str, Any], target: Any
) -> None:
    """Mutants A and N. Rows 0 and 1 are valid runner inputs, so only the guard refuses."""
    runner = _ci_clean(tracked, ci_run=_CI_RUN)
    inputs = [2] if target == "self" else [target]
    record = _runner_record(tracked, runner, copy.deepcopy(runner), {})
    record["readings"][2] = _derived_clean(tracked, inputs=inputs)
    assert _named(tool, record, 2, "names no other reading"), tool.grade(record)


@pytest.mark.parametrize("fault", ["commit", "superseded", "duplicate"])
def test_a_derived_clean_reading_is_tied_to_its_own_inputs(
    tool: ModuleType, tracked: dict[str, Any], fault: str
) -> None:
    """R8. Inputs share the derived row's commit, are live, and are named once."""
    first = _ci_clean(tracked, ci_run=_CI_RUN)
    second = _ci_clean(tracked, ci_run=_CI_RUN, value=112.0)
    inputs = [0, 1]
    if fault == "commit":
        second["commit"] = _FULL_B
    elif fault == "superseded":
        first["superseded_by"] = 1
        second["date"] = "2026-10-04"
    else:
        inputs = [0, 0]
    record = _runner_record(tracked, first, second, _derived_clean(tracked, inputs=inputs))
    assert _named(tool, record, 2, "input"), tool.grade(record)
    # Control: the same three rows, fault removed, grade clean.
    healthy = _runner_record(
        tracked,
        _ci_clean(tracked, ci_run=_CI_RUN),
        _ci_clean(tracked, ci_run=_CI_RUN, value=112.0),
        _derived_clean(tracked, inputs=[0, 1]),
    )
    assert tool.grade(healthy) == []


def test_one_run_may_not_vouch_for_two_commits(tool: ModuleType, tracked: dict[str, Any]) -> None:
    """Round-3 F1. A run checks out exactly one commit, whatever job is cited."""
    first = _ci_clean(tracked, ci_run=_CI_RUN)
    other = _ci_clean(
        tracked,
        ci_run=_CI_RUN.rsplit("/job/", 1)[0],
        commit=_FULL_B,
    )
    record = _runner_record(tracked, first, other)
    offences = tool.grade(record)
    assert any(o.startswith("reading 1:") and "ci_run" in o for o in offences), offences


def test_a_reading_citing_a_run_must_give_a_full_commit(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """Round 4. A short sha prefix-matches many commits, so a run's one commit is spelt whole."""
    record = _runner_record(tracked, _ci_clean(tracked, ci_run=_CI_RUN, commit="abcdef1"))
    assert _named(tool, record, 0, "full 40-hex commit"), tool.grade(record)


_K1_SHORT = "abcdef1"
_K1_A = "abcdef1" + "0" * 33
_K1_B = "abcdef1" + "1" * 33


@pytest.mark.parametrize(
    "order",
    [
        (_K1_SHORT, _K1_A, _K1_B),
        (_K1_A, _K1_SHORT, _K1_B),
        (_K1_A, _K1_B, _K1_SHORT),
        (_K1_B, _K1_A, _K1_SHORT),
        (_K1_SHORT, _K1_B, _K1_A),
    ],
)
def test_one_run_on_two_full_commits_is_refused_in_any_order(
    tool: ModuleType, tracked: dict[str, Any], order: tuple[str, str, str]
) -> None:
    """Round 4 K1. A short first can no longer bridge two distinct full shas.

    EVERY reading on a run that names two commits is refused, so the verdict does
    not depend on which reading came first.
    """
    readings = [
        _ci_clean(tracked, ci_run=_CI_RUN, commit=commit, value=100.0 + n)
        for n, commit in enumerate(order)
    ]
    record = _runner_record(tracked, *readings)
    offences = tool.grade(record)
    for index, commit in enumerate(order):
        if commit == _K1_SHORT:
            assert _named(tool, record, index, "full 40-hex commit"), offences
        else:
            assert any(
                o.startswith(f"reading {index}:") and "one run checks out one commit" in o
                for o in offences
            ), offences


def test_a_full_commit_with_a_trailing_newline_is_not_full(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """Round 5 mutant C. `$` would accept a newline after the forty digits."""
    record = _runner_record(tracked, _ci_clean(tracked, ci_run=_CI_RUN, commit=_FULL_A + "\n"))
    assert _named(tool, record, 0, "full 40-hex commit"), tool.grade(record)


def test_a_superseded_reading_still_counts_against_its_run(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """Round 5 mutant I. Supersession replaces a VALUE; it does not un-cite a run.

    One run cited on two commits is refused on both rows even when the first is
    superseded - the stricter policy is deliberate.
    """
    first = _ci_clean(tracked, ci_run=_CI_RUN, superseded_by=1)
    second = _ci_clean(tracked, ci_run=_CI_RUN, commit=_FULL_B, date="2026-10-04")
    record = _runner_record(tracked, first, second)
    offences = tool.grade(record)
    for index in (0, 1):
        assert any(
            o.startswith(f"reading {index}:") and "one run checks out one commit" in o
            for o in offences
        ), offences


def test_one_run_may_vouch_for_two_readings_of_its_one_commit(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    # Control for round-3 F1: two metrics from the same run and commit.
    first = _ci_clean(tracked, ci_run=_CI_RUN)
    second = _ci_clean(tracked, ci_run=_CI_RUN, metric="tier1_slowest_test_share_percent")
    second["unit"] = "percent"
    record = _runner_record(tracked, first, second)
    assert tool.grade(record) == []


_MALFORMED = (["x"], {"k": 1}, None, 3.5, True, "")


@pytest.mark.parametrize("field", ["metric", "unit", "method", "commit", "date", "tree"])
@pytest.mark.parametrize("bad", _MALFORMED, ids=lambda v: type(v).__name__ + repr(v)[:6])
def test_a_malformed_field_is_an_offence_never_a_crash(
    tool: ModuleType, tracked: dict[str, Any], field: str, bad: Any
) -> None:
    """Rule 7. Unknown content is refused by name, never fatal."""
    record = copy.deepcopy(tracked)
    record["readings"][8][field] = bad
    offences = tool.grade(record)
    assert any(o.startswith("reading 8:") for o in offences), offences


@pytest.mark.parametrize(
    "field", ["value", "workers", "contended", "source", "superseded_by", "witness", "inputs"]
)
@pytest.mark.parametrize("bad", _MALFORMED, ids=lambda v: type(v).__name__ + repr(v)[:6])
def test_no_malformed_field_crashes_the_grader(
    tool: ModuleType, tracked: dict[str, Any], field: str, bad: Any
) -> None:
    record = copy.deepcopy(tracked)
    record["readings"][8][field] = bad
    tool.grade(record)


def test_only_a_derived_reading_names_inputs(tool: ModuleType, tracked: dict[str, Any]) -> None:
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, "profile")
    reading["tree"] = "dirty"
    reading["inputs"] = [0]
    record["readings"].append(reading)
    assert _named(tool, record, len(record["readings"]) - 1, "input")


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("schema", 1),
        ("tree", "A" * 64),
        ("tree", "0" * 63),
        ("tree_files", -1),
        ("tree_files", True),
        ("bytecode", None),
        ("bytecode_files", "0"),
    ],
)
def test_a_malformed_witness_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any], field: str, bad: Any
) -> None:
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, "profile")
    reading["tree"] = tool.TREE_CLEAN
    reading["witness"] = {**_WELL_FORMED_WITNESS, field: bad}
    record["readings"].append(reading)
    index = len(record["readings"]) - 1
    named = [o for o in tool.grade(record) if o.startswith(f"reading {index}:") and "witness" in o]
    assert named, tool.grade(record)


@pytest.mark.parametrize("shape", ["missing_key", "extra_key", "not_a_mapping"])
def test_a_witness_of_the_wrong_shape_is_an_offence(
    tool: ModuleType, tracked: dict[str, Any], shape: str
) -> None:
    witness: Any = dict(_WELL_FORMED_WITNESS)
    if shape == "missing_key":
        del witness["bytecode"]
    elif shape == "extra_key":
        witness["note"] = "trust me"
    else:
        witness = None
    record = copy.deepcopy(tracked)
    reading = _new_local_reading(tracked, "profile")
    reading["tree"] = tool.TREE_CLEAN
    reading["witness"] = witness
    record["readings"].append(reading)
    index = len(record["readings"]) - 1
    named = [o for o in tool.grade(record) if o.startswith(f"reading {index}:") and "witness" in o]
    assert named, tool.grade(record)


def test_the_tracked_rows_are_exactly_the_pinned_seed_set(
    tool: ModuleType, tracked: dict[str, Any]
) -> None:
    """CONTROL. The sixteen seeded rows keep their values and dates, and grade clean."""
    pinned = [list(row) for row in tool.SEEDED_UNWITNESSED_READINGS]
    assert len(pinned) == _SEEDED_ROWS
    seeded = [r for r in tracked["readings"] if r["tree"] == tool.TREE_UNWITNESSED]
    assert [[r[f] for f in EXPECTED_RECEIPT_FIELDS] for r in seeded] == pinned
    assert tool.grade(tracked) == []


# ---- the witness re-derived from the reading's commit ----------------------


def _git(tool: ModuleType, root: Path, *args: str) -> str:
    git = tool.resolve_tool("git")
    assert git is not None
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    proc = subprocess.run(
        [
            git,
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
        env=env,
        timeout=_GIT_TIMEOUT,
        check=False,
    )
    rc = proc.returncode
    assert rc == 0, f"git {args[0]} exited {rc}"
    return proc.stdout.decode("ascii", "replace").strip()


def _witnessed_repo(tool: ModuleType, tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "cs1223_repo"
    (root / "pkg").mkdir(parents=True)
    (root / ".gitignore").write_bytes(b"__pycache__/\nwitness.json\n")
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 1\n")
    (root / "notes.md").write_bytes(b"# notes\n\nthe-reading-anchor\n")
    _git(tool, root, "init", "-q")
    _git(tool, root, "add", "-A")
    _git(tool, root, "commit", "-q", "-m", "seed")
    return root, _git(tool, root, "rev-parse", "HEAD")


def _write_record(root: Path, reading: dict[str, Any]) -> None:
    record = {
        "metrics": {"a_local_seconds": {"kind": "observation", "unit": "seconds"}},
        "readings": [reading],
    }
    (root / "tools").mkdir(exist_ok=True)
    (root / "tools" / "measurements.json").write_bytes(json.dumps(record).encode("ascii"))


def _local_clean(commit: str, witness: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "a_local_seconds",
        "value": 12.5,
        "unit": "seconds",
        "method": "local_suite",
        "workers": 4,
        "contended": "unknown",
        "date": _NEW_READING_DATE,
        "commit": commit,
        "tree": "clean",
        "witness": witness,
        "source": ["notes.md#the-reading-anchor"],
        "superseded_by": None,
    }


def test_a_local_clean_reading_with_a_valid_witness_grades_clean(
    tool: ModuleType, tmp_path: Path
) -> None:
    """CONTROL. Frozen over a clean checkout of its commit, the claim is re-derived."""
    root, head = _witnessed_repo(tool, tmp_path)
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    assert tool.grade_tree(root) == []
    # The re-derivation agrees with the tool that took the witness.
    assert tool.commit_tree_digest(root, head) == (witness["tree"], witness["tree_files"])


def test_a_clean_claim_whose_witness_saw_other_bytes_is_refused(
    tool: ModuleType, tmp_path: Path
) -> None:
    """The witness was taken honestly over a dirty tree; `clean` is then refuted."""
    root, head = _witnessed_repo(tool, tmp_path)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 2\n")
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    offences = tool.grade_tree(root)
    assert any("witness" in o and "reading 0:" in o for o in offences), offences


def test_a_clean_claim_over_a_crlf_flip_is_refused(tool: ModuleType, tmp_path: Path) -> None:
    # The damage porcelain cannot see: git normalises it, the raw digest does not.
    root, head = _witnessed_repo(tool, tmp_path)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 1\r\n")
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    assert tool.grade_tree(root)


def test_a_clean_claim_with_an_untracked_file_is_refused(tool: ModuleType, tmp_path: Path) -> None:
    root, head = _witnessed_repo(tool, tmp_path)
    (root / "stray.py").write_bytes(b"X = 1\n")
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    assert tool.grade_tree(root)


def test_a_forged_witness_digest_is_refused(tool: ModuleType, tmp_path: Path) -> None:
    root, head = _witnessed_repo(tool, tmp_path)
    witness = {**tool.freeze_witness.freeze(root), "tree": "f" * 64}
    _write_record(root, _local_clean(head, witness))
    assert tool.grade_tree(root)


def test_a_witness_bound_to_a_commit_the_clone_lacks_is_refused(
    tool: ModuleType, tmp_path: Path
) -> None:
    root, _ = _witnessed_repo(tool, tmp_path)
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean("abcdef0123456789abcdef0123456789abcdef01", witness))
    offences = tool.grade_tree(root)
    assert any("does not hold" in o for o in offences), offences


def test_a_witness_is_bound_to_the_readings_own_commit(tool: ModuleType, tmp_path: Path) -> None:
    # A valid witness of ONE commit does not vouch for a reading citing another.
    root, first = _witnessed_repo(tool, tmp_path)
    witness = tool.freeze_witness.freeze(root)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 3\n")
    _git(tool, root, "commit", "-q", "-am", "second")
    second = _git(tool, root, "rev-parse", "HEAD")
    _write_record(root, _local_clean(second, witness))
    assert tool.grade_tree(root)
    _write_record(root, _local_clean(first, witness))
    assert tool.grade_tree(root) == []


def test_a_shallow_clone_reports_an_absent_commit_unchecked(
    tool: ModuleType, tmp_path: Path
) -> None:
    # CI's depth-one checkout lacks history by construction: listed, not refused.
    root, first = _witnessed_repo(tool, tmp_path)
    witness = tool.freeze_witness.freeze(root)
    (root / "pkg" / "mod.py").write_bytes(b"VALUE = 4\n")
    _git(tool, root, "commit", "-q", "-am", "second")
    shallow = tmp_path / "cs1223_shallow"
    _git(tool, tmp_path, "clone", "-q", "--depth", "1", root.as_uri(), str(shallow))
    _write_record(shallow, _local_clean(first, witness))
    unchecked: list[str] = []
    assert tool.grade_tree(shallow, unchecked) == []
    assert len(unchecked) == 1
    assert "shallow" in unchecked[0]


def test_a_witness_with_the_right_digest_and_a_forged_file_count_is_refused(
    tool: ModuleType, tmp_path: Path
) -> None:
    root, head = _witnessed_repo(tool, tmp_path)
    witness = tool.freeze_witness.freeze(root)
    witness["tree_files"] += 1
    _write_record(root, _local_clean(head, witness))
    offences = tool.grade_tree(root)
    assert any("refuted" in o for o in offences), offences


def _plant_index_entry(tool: ModuleType, root: Path, mode: str, sha: str, path: str) -> str:
    _git(tool, root, "update-index", "--add", "--cacheinfo", f"{mode},{sha},{path}")
    _git(tool, root, "commit", "-q", "-m", f"plant {mode}")
    return _git(tool, root, "rev-parse", "HEAD")


def test_a_commit_carrying_a_symlink_is_refused(tool: ModuleType, tmp_path: Path) -> None:
    root, _ = _witnessed_repo(tool, tmp_path)
    blob = _git(tool, root, "hash-object", "-w", "notes.md")
    head = _plant_index_entry(tool, root, "120000", blob, "link")
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    offences = tool.grade_tree(root)
    assert any("symlink" in o for o in offences), offences


def test_a_commit_carrying_a_submodule_is_refused(tool: ModuleType, tmp_path: Path) -> None:
    root, first = _witnessed_repo(tool, tmp_path)
    head = _plant_index_entry(tool, root, "160000", first, "sub")
    (root / "sub").mkdir()
    witness = tool.freeze_witness.freeze(root)
    _write_record(root, _local_clean(head, witness))
    offences = tool.grade_tree(root)
    assert any("submodule" in o for o in offences), offences


@pytest.mark.parametrize("bad", [5, {"k": 1}, None, "notes.md#the-reading-anchor"])
def test_a_malformed_source_does_not_crash_the_tree_grader(
    tool: ModuleType, tmp_path: Path, bad: Any
) -> None:
    root, head = _witnessed_repo(tool, tmp_path)
    reading = _local_clean(head, tool.freeze_witness.freeze(root))
    reading["source"] = bad
    _write_record(root, reading)
    assert any("source" in o for o in tool.grade_tree(root))
