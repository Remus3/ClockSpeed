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
import sys
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
    return json.loads(RECORD_SOURCE.read_text(encoding="utf-8"))


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
    offences = tool.grade_tree(REPO_ROOT)
    assert offences == [], "\n".join(offences)


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
    assert tool.grade(record) == []


def _graded_in(tool: ModuleType, root: Path, record: dict[str, Any]) -> list[str]:
    (root / "tools").mkdir(exist_ok=True)
    (root / "tools" / "measurements.json").write_text(json.dumps(record), encoding="utf-8")
    return tool.grade_tree(root)


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
