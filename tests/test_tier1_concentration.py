"""CS-900 - grade the tier1 lane's CONCENTRATION record offline.

Every arm here runs against the TRACKED record and hand-authored fixture text.
Nothing in this module reaches the network: the refresh that takes a profile from
`gh` is a by-hand path with its fetch injected, the way `tests/test_tier1_growth.py`
keeps its own refresh offline.

THE NON-VACUITY ARMS ARE THE POINT OF THIS FILE. This project has repeatedly
measured oracles that pass because they cannot observe their subject, so three
shapes with KNOWN verdicts are pinned here - one that warns, one that clears, one
that breaches - and a fourth arm asserts that a job whose log carried no durations
block scores UNMEASURED rather than a comfortable zero.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import tier1_concentration as concentration  # noqa: E402

WORKFLOW_PATH = _ROOT / concentration.WORKFLOW_RELATIVE
RECORD_PATH = _ROOT / concentration.RECORD_RELATIVE

#: The fast shard, the save shard, the guard shard, the hook shard and the fill
#: shard. Three was the partition CS-896 and CS-1060 split into; CS-1193 added
#: the fourth, the hook shard, when the catch-all read over its ceiling (the
#: wave-3 CI route ruling), and CS-1198 the fifth, the fill shard, when the hook
#: shard read over its budget on a slow runner.
SUITE_RUNNING_JOBS = 5

#: THE PENDING-PROFILE RATCHET (CS-1193). Every declared job no recorded run has
#: profiled yet because it is NEW. Two-way, the rule tools/tier1_growth.py uses
#: for its reading floor: a listed job the workflow does not declare is red, and
#: a listed job profiled in EVERY recorded run is red, which forces this literal
#: down at the refresh that profiles it at both ends. The fill shard joined it
#: with CS-1198, by the same rule.
EXPECTED_PENDING_PROFILE = ("tests (hook shard)", "tests (fill shard)")


@pytest.fixture(scope="module")
def workflow_text() -> str:
    """The real tier1 workflow, read as text."""
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def record() -> object:
    """The tracked concentration record, parsed."""
    return json.loads(RECORD_PATH.read_text(encoding="ascii"))


# ---------------------------------------------------------------------------
# The two levels - both derived, neither transcribed
# ---------------------------------------------------------------------------


def test_the_worker_count_is_read_from_the_workflow_runs_on(workflow_text: str) -> None:
    """Every tier1 job's worker count comes from the parsed `runs-on`."""
    counts = concentration.worker_counts(workflow_text)
    assert set(counts) == set(concentration.declared_jobs(workflow_text))
    assert set(counts.values()) == {2}, counts


def test_a_runs_on_the_table_has_no_entry_for_is_refused() -> None:
    """An unmapped runner REFUSES. That refusal is what pins W rather than assuming it."""
    unmapped = (
        "name: tier1\njobs:\n  only:\n    name: only job\n    runs-on: moonbase-alpha-64core\n"
    )
    with pytest.raises(ValueError, match="moonbase-alpha-64core") as caught:
        concentration.worker_counts(unmapped)
    assert "moonbase-alpha-64core" in str(caught.value)


def test_a_list_valued_runs_on_is_refused_rather_than_guessed() -> None:
    """A label list is not a runner this table can price, so it refuses too."""
    listed = "name: tier1\njobs:\n  only:\n    name: only job\n    runs-on: [self-hosted, linux]\n"
    with pytest.raises(ValueError, match="not a plain"):
        concentration.worker_counts(listed)


def test_the_hard_level_is_the_reciprocal_of_the_worker_count(workflow_text: str) -> None:
    """HARD = 1/W. Above it the top test, not the total, is the parallel floor's binding term."""
    levels = concentration.hard_levels(workflow_text)
    assert set(levels.values()) == {Fraction(1, 2)}, levels


def test_the_warn_level_is_the_band_divided_by_the_budget(workflow_text: str) -> None:
    """WARN = (CEILING - BUDGET) / BUDGET, read live from the workflow's env block."""
    budget, ceiling = concentration.declared_levels(workflow_text)
    assert concentration.warn_level(workflow_text) == Fraction(ceiling - budget, budget)


def _numeric_leaves(value: object) -> list[int]:
    """Every integer leaf of a parsed record, so a hex SHA cannot be read as a number."""
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in _numeric_leaves(item)]
    if isinstance(value, list):
        return [leaf for item in value for leaf in _numeric_leaves(item)]
    return []


def test_neither_level_is_transcribed_into_the_tool_or_the_record(
    workflow_text: str, record: object
) -> None:
    """A level spelled in either artifact is a level that will drift from the workflow.

    Graded over NUMBERS rather than raw bytes in both halves. A substring scan
    reddened on `60` occurring inside a head SHA's hex, which is a coincidence
    and not a transcription - and an arm that cries wolf on hex gets relaxed
    rather than read.
    """
    budget, ceiling = concentration.declared_levels(workflow_text)
    literals = {int(found) for found in re.findall(r"\d+", concentration.__doc__ or "")}
    source = Path(concentration.__file__).read_text(encoding="ascii")
    literals |= {int(found) for found in re.findall(r"(?<![\w.])\d+(?![\w.])", source)}
    leaves = set(_numeric_leaves(record))
    for value in (budget, ceiling, ceiling - budget):
        assert value not in literals, f"{value} is a literal in the tool"
        assert value not in leaves, f"{value} is a recorded number"


def test_a_share_is_rendered_by_rounding_the_exact_fraction_half_up() -> None:
    """One seventh is 14.2857 per cent, so truncation would report it a hundredth low."""
    assert concentration.render_share(Fraction(1, 7)) == "14.29 per cent"
    assert concentration.render_share(Fraction(1, 2)) == "50.00 per cent"
    assert concentration.render_share(Fraction(2, 3)) == "66.67 per cent"
    assert concentration.render_share(None) == "UNMEASURED"


def test_the_warn_level_is_below_the_hard_level(workflow_text: str) -> None:
    """An ordering that inverted would make every warn verdict unreachable."""
    warn = concentration.warn_level(workflow_text)
    assert all(warn < hard for hard in concentration.hard_levels(workflow_text).values())


# ---------------------------------------------------------------------------
# The three non-vacuity shapes, each with a verdict known before the code existed
# ---------------------------------------------------------------------------


def _verdict_for(workflow_text: str, job: str, step_seconds: int, centiseconds: int) -> str:
    """One profile's verdict, against the live levels."""
    profile = concentration.Profile(
        job=job,
        step_seconds=step_seconds,
        top_test="tests/test_shape.py::test_shape",
        top_test_centiseconds=centiseconds,
    )
    return concentration.verdict(
        profile,
        concentration.warn_level(workflow_text),
        concentration.hard_levels(workflow_text)[job],
    )


def test_the_recorded_before_reading_of_the_fast_shard_warns(workflow_text: str) -> None:
    """158.74s of a 445s step is over the warn level and under the hard one."""
    assert _verdict_for(workflow_text, "gates, lint, types, tests", 445, 15874) == "WARN"


def test_the_recorded_after_reading_of_the_fast_shard_clears(workflow_text: str) -> None:
    """31.04s of a 383s step is under both levels."""
    assert _verdict_for(workflow_text, "gates, lint, types, tests", 383, 3104) == "CLEAR"


def test_the_cs896_era_save_shard_shape_breaches_the_hard_level(workflow_text: str) -> None:
    """170.30s of a 208s step - `docs/LEDGER.md` under CS-896's split - is over 1/W.

    The shape is historical rather than current, which is exactly why it is here:
    it is a reading this grader MUST redden on, taken from a tree that really
    produced it, so the hard level is shown to be reachable rather than decorative.
    """
    assert _verdict_for(workflow_text, "tests (save shard)", 208, 17030) == "BREACH"


def test_a_job_whose_log_carried_no_durations_block_is_unmeasured(workflow_text: str) -> None:
    """The mandatory anti-vacuity arm. No block means no measurement, not a share of zero."""
    profile = concentration.Profile(
        job="tests (save shard)",
        step_seconds=208,
        top_test=None,
        top_test_centiseconds=None,
    )
    assert profile.share is None
    assert (
        concentration.verdict(
            profile,
            concentration.warn_level(workflow_text),
            concentration.hard_levels(workflow_text)["tests (save shard)"],
        )
        == "UNMEASURED"
    )


def test_an_unmeasured_profile_never_renders_as_a_share(workflow_text: str) -> None:
    """A zero rendered where nothing was measured is the failure mode this forbids."""
    unmeasured = {
        "runs": [
            {
                "run_id": 1,
                "head_sha": "0" * 40,
                "label": "before",
                "profiles": [
                    {
                        "job": job,
                        "step_seconds": 208,
                        "top_test": None,
                        "top_test_centiseconds": None,
                    }
                    for job in concentration.declared_jobs(workflow_text)
                ],
            }
        ]
    }
    rendered = concentration.report(unmeasured, workflow_text)
    assert "UNMEASURED" in rendered
    # The LEVELS line legitimately renders a percentage, and "50.00 per cent"
    # carries "0.00 per cent" as a substring - which is why this grades the
    # PROFILE lines rather than the whole report. A looser arm passed on the
    # levels line and would have said nothing about the subject.
    job_lines = [line for line in rendered.splitlines() if "shard" in line or "gates" in line]
    assert len(job_lines) == len(concentration.declared_jobs(workflow_text)), job_lines
    for line in job_lines:
        assert "UNMEASURED" in line, line
        assert "per cent" not in line, line


def test_an_unmeasured_profile_reddens_the_grade(workflow_text: str) -> None:
    """UNMEASURED is an offence, so a profile that observed nothing cannot pass."""
    offences = concentration.grade_profile(
        "before",
        concentration.Profile(
            job="tests (save shard)",
            step_seconds=208,
            top_test=None,
            top_test_centiseconds=None,
        ),
        concentration.warn_level(workflow_text),
        Fraction(1, 2),
    )
    assert offences, "an unmeasured profile scored clean"
    assert any("UNMEASURED" in offence for offence in offences)


def test_a_breaching_profile_reddens_the_grade(workflow_text: str) -> None:
    """The hard level is enforced, not merely reported."""
    offences = concentration.grade_profile(
        "before",
        concentration.Profile(
            job="tests (save shard)",
            step_seconds=208,
            top_test="tests/save/test_phase4_gate.py::test_shape",
            top_test_centiseconds=17030,
        ),
        concentration.warn_level(workflow_text),
        Fraction(1, 2),
    )
    assert any("BREACH" in offence for offence in offences)


def test_a_warning_profile_does_not_redden_the_grade(workflow_text: str) -> None:
    """WARN is the band between the levels; reddening on it would forbid the recorded before."""
    offences = concentration.grade_profile(
        "before",
        concentration.Profile(
            job="gates, lint, types, tests",
            step_seconds=445,
            top_test="tests/test_disposition_sites.py::test_shape",
            top_test_centiseconds=15874,
        ),
        concentration.warn_level(workflow_text),
        Fraction(1, 2),
    )
    assert offences == []


# ---------------------------------------------------------------------------
# The tracked record
# ---------------------------------------------------------------------------


def test_the_tracked_record_grades_clean() -> None:
    """The shipped record carries no breach and no unmeasured job."""
    assert concentration.grade_tree(_ROOT) == []


def test_the_record_carries_exactly_one_before_and_one_after(record: object) -> None:
    """The acceptance asks for a profile taken BEFORE and AFTER, so both ends are pinned."""
    assert isinstance(record, dict)
    labels = sorted(run["label"] for run in record["runs"])
    assert labels == ["after", "before"]


def test_every_declared_job_is_profiled_at_both_ends(record: object, workflow_text: str) -> None:
    """The ruling's owed half - the share is reported for EVERY suite-running job.

    Every job but a PENDING one, which no recorded run can have profiled yet -
    and a pending job is never profiled by a made-up row to satisfy this arm.
    """
    declared = set(concentration.declared_jobs(workflow_text))
    assert isinstance(record, dict)
    assert len(declared) == SUITE_RUNNING_JOBS, declared
    pending = set(concentration.PENDING_PROFILE)
    for run in record["runs"]:
        profiled = {profile["job"] for profile in run["profiles"]}
        assert profiled | pending == declared, run["label"]


# ---------------------------------------------------------------------------
# The pending set - a NEW job's profile exemption, and nothing wider (CS-1193)
# ---------------------------------------------------------------------------

_NEW_JOB = "tests (new shard)"


def _with_new_job(workflow_text: str) -> str:
    """The shipped workflow plus one more job the record has never profiled.

    The shipped workflow already carries the shipped pending job, so every arm
    below names that one alongside the new job and varies ONLY the new job.
    """
    return workflow_text + (
        "\n  newshard:\n"
        f"    name: {_NEW_JOB}\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - run: echo hi\n"
    )


def _profiled_everywhere(record: object, job: str, centiseconds: int = 500) -> dict:
    """A copy of the record carrying one more profile, for ``job``, in every run."""
    copied = dict(json.loads(json.dumps(record)))
    for run in copied["runs"]:
        run["profiles"].append(
            {
                "job": job,
                "step_seconds": 200,
                "top_test": "tests/test_shape.py::test_shape",
                "top_test_centiseconds": centiseconds,
            }
        )
    return copied


def test_the_pending_profile_set_is_what_this_module_pins() -> None:
    assert tuple(concentration.PENDING_PROFILE) == EXPECTED_PENDING_PROFILE


def test_a_pending_job_no_run_profiled_is_exempt_from_the_absence_offence(
    record: object, workflow_text: str
) -> None:
    workflow = _with_new_job(workflow_text)
    unpended = concentration.grade(record, workflow, pending=EXPECTED_PENDING_PROFILE)
    assert any(_NEW_JOB in offence for offence in unpended), unpended
    assert (
        concentration.grade(record, workflow, pending=(*EXPECTED_PENDING_PROFILE, _NEW_JOB)) == []
    )


def test_a_pending_job_profiled_in_every_run_is_an_offence(
    record: object, workflow_text: str
) -> None:
    """The closing direction: profiled at both ends, and the name must go."""
    workflow = _with_new_job(workflow_text)
    both = _profiled_everywhere(record, _NEW_JOB)
    assert concentration.grade(both, workflow, pending=EXPECTED_PENDING_PROFILE) == []
    offences = concentration.grade(both, workflow, pending=(*EXPECTED_PENDING_PROFILE, _NEW_JOB))
    assert any(_NEW_JOB in offence and "pending" in offence for offence in offences)


def test_a_pending_job_profiled_in_one_run_only_stays_pending(
    record: object, workflow_text: str
) -> None:
    """A job added after the before run can be profiled only in the after one."""
    workflow = _with_new_job(workflow_text)
    one = _profiled_everywhere(record, _NEW_JOB)
    del one["runs"][0]["profiles"][-1]
    assert concentration.grade(one, workflow, pending=(*EXPECTED_PENDING_PROFILE, _NEW_JOB)) == []
    assert concentration.grade(one, workflow, pending=EXPECTED_PENDING_PROFILE) != []


def test_a_pending_job_that_is_profiled_is_still_graded_on_its_share(
    record: object, workflow_text: str
) -> None:
    """Only ABSENCE is waived. A pending job's breaching profile still reddens."""
    workflow = _with_new_job(workflow_text)
    breaching = _profiled_everywhere(record, _NEW_JOB, centiseconds=19000)
    del breaching["runs"][0]["profiles"][-1]
    offences = concentration.grade(
        breaching, workflow, pending=(*EXPECTED_PENDING_PROFILE, _NEW_JOB)
    )
    assert any("BREACH" in offence for offence in offences), offences


def test_the_pending_exemption_does_not_reach_a_job_it_does_not_name(
    record: object, workflow_text: str
) -> None:
    workflow = _with_new_job(workflow_text)
    stripped = json.loads(json.dumps(record))
    stripped["runs"][0]["profiles"] = [
        profile
        for profile in stripped["runs"][0]["profiles"]
        if profile["job"] != "tests (save shard)"
    ]
    offences = concentration.grade(
        stripped, workflow, pending=(*EXPECTED_PENDING_PROFILE, _NEW_JOB)
    )
    assert any("tests (save shard)" in offence for offence in offences), offences


def test_a_pending_job_the_workflow_does_not_declare_is_an_offence(
    workflow_text: str,
) -> None:
    assert concentration.pending_undeclared(workflow_text, ("ghost job",)) == [
        "the pending set names 'ghost job', which the workflow does not declare"
    ]
    assert concentration.pending_undeclared(workflow_text) == []


def test_the_tree_grade_carries_the_undeclared_direction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "tools").mkdir()
    (tmp_path / concentration.WORKFLOW_RELATIVE).write_bytes(WORKFLOW_PATH.read_bytes())
    (tmp_path / concentration.RECORD_RELATIVE).write_bytes(RECORD_PATH.read_bytes())
    assert concentration.grade_tree(tmp_path) == []
    monkeypatch.setattr(concentration, "PENDING_PROFILE", (*EXPECTED_PENDING_PROFILE, "ghost job"))
    assert any("ghost job" in offence for offence in concentration.grade_tree(tmp_path))


def test_a_job_renamed_in_the_workflow_is_red_against_the_record(
    record: object, workflow_text: str
) -> None:
    """Staleness is bounded on the structural half even though the readings age."""
    renamed = workflow_text.replace(
        "name: tests (guard shard)", "name: tests (guard shard renamed)"
    )
    assert renamed != workflow_text
    offences = concentration.grade(record, renamed)
    assert offences, "a renamed job graded clean against the record"


def test_the_record_is_ascii_and_lf_only() -> None:
    """`CLAUDE.md` non-negotiable 4, and the LF rule the harness edits break."""
    raw = RECORD_PATH.read_bytes()
    raw.decode("ascii")
    assert b"\r" not in raw


def test_the_record_carries_no_field_off_the_allowlist(record: object) -> None:
    """The jobs API returns owner-bearing URLs and host labels; none is kept."""
    assert isinstance(record, dict)
    for run in record["runs"]:
        assert set(run) == set(concentration.RUN_FIELDS)
        for profile in run["profiles"]:
            assert set(profile) == set(concentration.PROFILE_FIELDS)


def test_the_recorded_shares_reproduce_the_ledgers_two_figures(record: object) -> None:
    """The two figures `docs/LEDGER.md` records are re-derived here, not transcribed.

    Both are the `gates, lint, types, tests` job. They are asserted as the exact
    rationals the record's own integers give, so a record edited to flatter itself
    moves them.
    """
    assert isinstance(record, dict)
    by_label = {run["label"]: run for run in record["runs"]}
    shares = {}
    for label, run in by_label.items():
        for profile in run["profiles"]:
            if profile["job"] == "gates, lint, types, tests":
                shares[label] = Fraction(
                    profile["top_test_centiseconds"], profile["step_seconds"] * 100
                )
    assert shares["before"] == Fraction(15874, 44500)
    assert shares["after"] == Fraction(3104, 38300)


# ---------------------------------------------------------------------------
# The parsers the by-hand refresh uses, driven offline
# ---------------------------------------------------------------------------


_JOBS_PAYLOAD = {
    "total_count": 2,
    "jobs": [
        {
            "name": "only job",
            "run_id": 7,
            "head_sha": "a" * 40,
            "status": "completed",
            "steps": [
                {
                    "name": "Install toolchain",
                    "started_at": "2026-09-18T09:00:00Z",
                    "completed_at": "2026-09-18T09:01:00Z",
                },
                {
                    "name": "Unit tests",
                    "started_at": "2026-09-18T09:24:26Z",
                    "completed_at": "2026-09-18T09:31:51Z",
                },
            ],
        },
        {
            "name": "not yet done",
            "run_id": 7,
            "head_sha": "a" * 40,
            "status": "in_progress",
            "steps": [],
        },
    ],
}


def test_the_step_seconds_come_from_the_named_step_of_the_jobs_payload() -> None:
    """445s is the `Unit tests` step, not the job, and not another step of it."""
    assert concentration.step_seconds_by_job(_JOBS_PAYLOAD) == {"only job": 445}


def test_a_job_still_running_contributes_no_step() -> None:
    """An incomplete job has no duration, so it is dropped rather than recorded as short."""
    assert "not yet done" not in concentration.step_seconds_by_job(_JOBS_PAYLOAD)


def test_the_top_test_sums_every_phase_of_one_node_id() -> None:
    """Phases of one node id sum: xdist cannot split a test, so their total is unsplittable."""
    log = "\n".join(
        [
            "only job\tUnit tests\t2026-09-18T09:31:51.5354883Z "
            "============================= slowest 15 durations "
            "=============================",
            "only job\tUnit tests\t2026-09-18T09:31:51.5355910Z "
            "20.00s call     tests/test_a.py::test_one",
            "only job\tUnit tests\t2026-09-18T09:31:51.5357149Z "
            "18.00s setup    tests/test_b.py::test_two",
            "only job\tUnit tests\t2026-09-18T09:31:51.5358843Z "
            "17.50s call     tests/test_b.py::test_two",
            "only job\tUnit tests\t2026-09-18T09:31:51.5359843Z "
            "=========================== short test summary info "
            "============================",
        ]
    )
    assert concentration.top_test_by_job(log) == {"only job": ("tests/test_b.py::test_two", 3550)}


def test_a_log_with_no_durations_block_yields_no_top_test() -> None:
    """The anti-vacuity mechanism at its source: nothing parsed means nothing claimed."""
    log = "only job\tUnit tests\t2026-09-18T09:31:51.5354883Z 4784 passed, 117 skipped in 590.82s"
    assert concentration.top_test_by_job(log) == {}


def test_the_log_parser_reads_only_the_named_step() -> None:
    """Another step printing a durations-shaped line must not be read as the suite's."""
    log = "\n".join(
        [
            "only job\tType check\t2026-09-18T09:31:51.5354883Z "
            "============================= slowest 15 durations "
            "=============================",
            "only job\tType check\t2026-09-18T09:31:51.5355910Z "
            "99.00s call     tests/test_a.py::test_one",
        ]
    )
    assert concentration.top_test_by_job(log) == {}


def test_the_refresh_takes_its_fetch_by_injection() -> None:
    """No test on this project reaches the network, so the only gh path is injectable."""
    signature = inspect.signature(concentration.refresh)
    assert "fetch" in signature.parameters
    assert signature.parameters["fetch"].default is concentration.gh_fetch
