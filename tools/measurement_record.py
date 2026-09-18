"""CS-920 - a row-scoped receipt for every measurement this project takes of ITSELF.

WHY THIS EXISTS. A number this project measures about its own suite, its own lane
or its own box is published in PROSE, and its provenance is DOCUMENT-scoped: the
conditions it was taken under live in the surrounding paragraph. A later session
quotes the row, not the document, and the receipt is left behind. That is not a
careless-reading failure - three figures were published and corrected on this
project in a single session, and each was a CORRECT reading whose conditions did
not travel with it.

WHAT A RECEIPT CARRIES, and every field is here because a published number was
corrected for the want of it:

    metric      what was measured, declared once so a unit cannot drift row to row
    value       the number
    unit        seconds, a ratio, a count, a percentage, seconds per commit
    method      paired, unpaired, ci_job, local_suite, profile or derived
    workers     the pytest worker count ACTUALLY RESOLVED, never the core count
    contended   whether another suite was live on the same box
    date        when it was taken
    commit      the tree it was taken on

THE ONE LOAD STATE THIS TOOL LETS A READING CLAIM WITHOUT AN OBSERVATION, stated
here because a rule that is applied and not written down is an inference wearing a
fact's clothes. A `ci_job` reading, and a `derived` reading every input of which is
one, runs on a GitHub-hosted runner, which is a dedicated virtual machine per job -
so its load state is `false` BY THAT FACT rather than by anyone having watched the
box. No other method may claim `false` without a citation that says the box was
quiet; a local reading whose load state nobody recorded is `unknown`, and this
project's own notes say the operator runs several projects' sessions at once, so
`unknown` there is closer to probably-contended than to quiet. CS-920's verifier
raised this as the softest field on every seeded row and it is answered by naming
the rule, not by hiding it.

TWO ESCAPE VALUES EXIST AND THEY ARE NOT A FREE PASS. A worker count that was
never recorded is `unresolved` and a load state that was never recorded is
`unknown`. Keeping such a reading is better than losing it, and what the escape
costs is enforced rather than promised: :func:`comparability` never returns
`comparable` for a pair resting on one, so a delta drawn across it is reported
as `unproven` instead of as fact. ABSENCE of the field remains an offence - that
is the arm CS-920's acceptance clause names.

    python tools/measurement_record.py             grade the tracked record, exit 1 on any offence
    python tools/measurement_record.py --survives  answer the survives-next-reading query
    python tools/measurement_record.py --show      print every reading with its receipt

NO MODE OF THIS TOOL REACHES THE NETWORK OR TAKES A READING. It records readings
a human or a session already took. It is not a benchmarking harness: a harness
would re-measure, and re-measuring is exactly what a session cannot do for a
reading taken three weeks ago on a tree that has moved.

WHY THE QUERY REPORTS A BASIS BESIDE ITS VERDICT. CS-917's acceptance asks for a
noise figure that SURVIVES ITS OWN NEXT READING - a query over a measurement
history. This project has already published a false delta by comparing a SERIAL
reading against a PARALLEL one, so a verdict with no statement of what it rests
on would reproduce the defect the record exists to stop. A pair that disagrees on
method, worker count or load state falsifies NOTHING and is reported `untested`;
a pair that agrees only because both sides are unrecorded is reported `unproven`.

WHY A BOUND AND AN OBSERVATION ARE DIFFERENT KINDS. A single duration cannot be
falsified by a later duration - the lane simply took longer that day. A BOUND
claims something about readings yet to come, so a later reading that exceeds it
refutes it. Only a bound is subject to the survives query, and asking it of an
observation is an error rather than a green answer.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date as _date
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TOOLS_DIR.parent

#: The record, relative to the repo root, so a tree can be graded by path.
RECORD_RELATIVE = "tools/measurements.json"

#: THE RECEIPT. The acceptance clause for CS-920 names these eight by name and
#: `tests/test_measurement_record.py` pins the tuple, so dropping one is red.
RECEIPT_FIELDS = (
    "metric",
    "value",
    "unit",
    "method",
    "workers",
    "contended",
    "date",
    "commit",
)

#: The receipt plus the two fields that make a row auditable and revisable:
#: where the reading was published, and which later reading replaced it.
READING_FIELDS = (*RECEIPT_FIELDS, "source", "superseded_by")

#: A metric is declared once. `sense` is required of a bound and refused of an
#: observation, because only a bound has a direction it can be refuted from.
OBSERVATION_FIELDS = ("kind", "unit")
BOUND_FIELDS = ("kind", "unit", "sense")

UNITS = ("seconds", "ratio", "count", "percent", "seconds_per_commit")
METHODS = ("paired", "unpaired", "ci_job", "local_suite", "profile", "derived")
KINDS = ("observation", "bound")
SENSES = ("upper", "lower")

#: The two escape values. See the module docstring for what they cost.
WORKERS_UNRESOLVED = "unresolved"
CONTENDED_UNKNOWN = "unknown"

#: Comparability of a pair of readings.
COMPARABLE = "comparable"
UNPROVEN = "unproven"
NOT_COMPARABLE = "not_comparable"

#: Verdicts of the survives-next-reading query.
SURVIVED = "survived"
FALSIFIED = "falsified"
UNTESTED = "untested"
SUPERSEDED = "superseded"

_METRIC_SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
_CITATION = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*#\S.*$")


def load(root: Path) -> Any:
    """Read the tracked record from ``root``. Raises rather than guessing."""
    return json.loads((root / RECORD_RELATIVE).read_text(encoding="utf-8"))


def _grade_metrics(metrics: Any) -> list[str]:
    offences: list[str] = []
    if not isinstance(metrics, dict):
        return ["metrics: not a mapping"]
    for slug, declaration in sorted(metrics.items()):
        where = f"metric {slug!r}"
        if not isinstance(slug, str) or not _METRIC_SLUG.match(slug):
            offences.append(f"{where}: not a lower_snake_case slug")
        if not isinstance(declaration, dict):
            offences.append(f"{where}: declaration is not a mapping")
            continue
        kind = declaration.get("kind")
        if kind not in KINDS:
            offences.append(f"{where}: kind {kind!r} is not one of {KINDS}")
            continue
        expected = BOUND_FIELDS if kind == "bound" else OBSERVATION_FIELDS
        if tuple(sorted(declaration)) != tuple(sorted(expected)):
            offences.append(f"{where}: fields {sorted(declaration)} are not {sorted(expected)}")
            continue
        if declaration["unit"] not in UNITS:
            offences.append(f"{where}: unit {declaration['unit']!r} is not one of {UNITS}")
        if kind == "bound" and declaration["sense"] not in SENSES:
            offences.append(f"{where}: sense {declaration['sense']!r} is not one of {SENSES}")
    return offences


def _grade_receipt(where: str, reading: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    offences: list[str] = []

    metric = reading["metric"]
    declaration = metrics.get(metric) if isinstance(metrics, dict) else None
    if not isinstance(metric, str) or declaration is None:
        offences.append(f"{where}: metric {metric!r} is not declared under 'metrics'")
    elif isinstance(declaration, dict) and reading["unit"] != declaration.get("unit"):
        offences.append(
            f"{where}: unit {reading['unit']!r} disagrees with the unit declared for {metric!r}"
        )
    elif reading["unit"] not in UNITS:
        offences.append(f"{where}: unit {reading['unit']!r} is not one of {UNITS}")

    value = reading["value"]
    if isinstance(value, bool) or not isinstance(value, int | float):
        offences.append(f"{where}: value {value!r} is not a number")

    if reading["method"] not in METHODS:
        offences.append(f"{where}: method {reading['method']!r} is not one of {METHODS}")

    workers = reading["workers"]
    if workers != WORKERS_UNRESOLVED and (
        isinstance(workers, bool) or not isinstance(workers, int) or workers < 1
    ):
        offences.append(
            f"{where}: workers {workers!r} is neither a count of at least one"
            f" nor {WORKERS_UNRESOLVED!r}"
        )

    contended = reading["contended"]
    if contended != CONTENDED_UNKNOWN and not isinstance(contended, bool):
        offences.append(
            f"{where}: contended {contended!r} is neither true, false nor {CONTENDED_UNKNOWN!r}"
        )

    stamp = reading["date"]
    if not isinstance(stamp, str) or not _DATE.match(stamp):
        offences.append(f"{where}: date {stamp!r} is not an ISO calendar date")
    else:
        try:
            _date.fromisoformat(stamp)
        except ValueError:
            offences.append(f"{where}: date {stamp!r} is not a real calendar date")

    commit = reading["commit"]
    if not isinstance(commit, str) or not _COMMIT.match(commit):
        offences.append(f"{where}: commit {commit!r} is not a lowercase hex sha of 7 to 40 digits")

    return offences


def _grade_source(where: str, reading: dict[str, Any]) -> list[str]:
    """A citation is `path#anchor`, and the anchor is the point.

    `docs/LEDGER.md` is append-at-TOP, so a line number in it is stale the moment
    the next entry lands and a grader over line numbers checks nothing. An anchor
    is text that must still APPEAR in the cited file, so it survives the file
    growing and reddens when the sentence it names is reworded away.
    """
    source = reading["source"]
    if not isinstance(source, list) or not source:
        return [f"{where}: source is not a non-empty list of 'path#anchor' citations"]
    return [
        f"{where}: source citation {citation!r} is not 'path#anchor'"
        for citation in source
        if not isinstance(citation, str) or not _CITATION.match(citation)
    ]


def _grade_supersession(readings: list[Any]) -> list[str]:
    offences: list[str] = []
    for index, reading in enumerate(readings):
        if not isinstance(reading, dict) or "superseded_by" not in reading:
            continue
        target = reading["superseded_by"]
        where = f"reading {index}"
        if target is None:
            continue
        if isinstance(target, bool) or not isinstance(target, int):
            offences.append(f"{where}: superseded_by {target!r} is not an index")
            continue
        if not 0 <= target < len(readings) or target == index:
            offences.append(f"{where}: superseded_by {target!r} names no other reading")
            continue
        later = readings[target]
        if not isinstance(later, dict):
            offences.append(f"{where}: superseded_by {target!r} names a malformed reading")
            continue
        if later.get("metric") != reading.get("metric"):
            offences.append(f"{where}: superseded_by {target!r} names a different metric")
        if str(later.get("date")) < str(reading.get("date")):
            offences.append(f"{where}: superseded_by {target!r} names an EARLIER reading")

    # A supersession cycle would make every reading in it both live and replaced.
    for index in range(len(readings)):
        seen = set()
        cursor: Any = index
        while isinstance(cursor, int) and 0 <= cursor < len(readings):
            if cursor in seen:
                offences.append(f"reading {index}: superseded_by forms a cycle")
                break
            seen.add(cursor)
            entry = readings[cursor]
            cursor = entry.get("superseded_by") if isinstance(entry, dict) else None
    return offences


def grade(record: Any) -> list[str]:
    """Return every offence in ``record``. An empty list is the only pass."""
    if not isinstance(record, dict):
        return ["record: not a mapping"]
    if tuple(sorted(record)) != ("metrics", "readings"):
        return [f"record: top-level keys {sorted(record)} are not ['metrics', 'readings']"]

    offences = _grade_metrics(record["metrics"])
    readings = record["readings"]
    if not isinstance(readings, list):
        return [*offences, "readings: not a list"]

    for index, reading in enumerate(readings):
        where = f"reading {index}"
        if not isinstance(reading, dict):
            offences.append(f"{where}: not a mapping")
            continue
        missing = [field for field in READING_FIELDS if field not in reading]
        extra = [field for field in reading if field not in READING_FIELDS]
        for field in missing:
            offences.append(f"{where}: receipt field {field!r} is missing")
        for field in extra:
            offences.append(f"{where}: field {field!r} is not on the record's allowlist")
        if missing:
            continue
        offences.extend(_grade_receipt(where, reading, record["metrics"]))
        offences.extend(_grade_source(where, reading))

    offences.extend(_grade_supersession(readings))
    return offences


def grade_tree(root: Path) -> list[str]:
    """Grade the record in ``root`` AND check that every citation names a file."""
    try:
        record = load(root)
    except FileNotFoundError:
        return [f"record: {RECORD_RELATIVE} is absent from {root}"]
    except json.JSONDecodeError as exc:
        return [f"record: {RECORD_RELATIVE} is not valid JSON ({exc.msg})"]

    offences = grade(record)
    readings = record["readings"] if isinstance(record, dict) else []
    if not isinstance(readings, list):
        return offences
    for index, reading in enumerate(readings):
        if not isinstance(reading, dict):
            continue
        for citation in reading.get("source") or []:
            if not isinstance(citation, str) or "#" not in citation:
                continue
            relative, anchor = citation.split("#", 1)
            cited = root / relative
            if not cited.is_file():
                offences.append(f"reading {index}: source cites {relative}, which is not a file")
            elif anchor not in cited.read_text(encoding="utf-8"):
                offences.append(
                    f"reading {index}: source cites {relative}, which no longer carries"
                    f" the anchor {anchor!r}"
                )
    return offences


def comparability(left: dict[str, Any], right: dict[str, Any]) -> str:
    """How far a delta between two readings can be trusted.

    A pair disagreeing on method, worker count or load state establishes NOTHING:
    this project published a growth of +57 seconds by comparing a serial reading
    against a parallel one. A pair agreeing only because both sides were never
    recorded is `unproven` - agreement about nothing is not agreement.
    """
    for field in ("method", "workers", "contended"):
        if left[field] != right[field]:
            return NOT_COMPARABLE
    if WORKERS_UNRESOLVED in (left["workers"], right["workers"]):
        return UNPROVEN
    if CONTENDED_UNKNOWN in (left["contended"], right["contended"]):
        return UNPROVEN
    return COMPARABLE


def _ordered(record: dict[str, Any], metric: str) -> list[tuple[int, dict[str, Any]]]:
    rows = [
        (index, reading)
        for index, reading in enumerate(record["readings"])
        if reading["metric"] == metric
    ]
    return sorted(rows, key=lambda row: (row[1]["date"], row[0]))


def survives_next_reading(record: dict[str, Any], metric: str) -> list[dict[str, Any]]:
    """Answer CS-917's survives-its-next-reading question for ``metric``.

    One row per reading, oldest first, each carrying the verdict AND the basis it
    rests on. A reading with no later reading is `untested` rather than
    `survived`: a bound nothing has tested yet has not survived anything, and
    reporting it as survived is how a figure that was never re-read becomes fact.
    """
    declaration = record["metrics"][metric]
    if declaration["kind"] != "bound":
        raise ValueError(
            f"metric {metric!r} is an observation, not a bound;"
            " a single reading cannot be falsified by a later one"
        )
    sense = declaration["sense"]
    rows = _ordered(record, metric)

    answers: list[dict[str, Any]] = []
    for position, (index, reading) in enumerate(rows):
        answer = {
            "index": index,
            "metric": metric,
            "value": reading["value"],
            "date": reading["date"],
            "commit": reading["commit"],
            "verdict": UNTESTED,
            "basis": None,
            "next_index": None,
        }
        if reading["superseded_by"] is not None:
            answer["verdict"] = SUPERSEDED
            answer["next_index"] = reading["superseded_by"]
            answers.append(answer)
            continue
        if position + 1 < len(rows):
            next_index, following = rows[position + 1]
            basis = comparability(reading, following)
            answer["basis"] = basis
            answer["next_index"] = next_index
            if basis != NOT_COMPARABLE:
                exceeded = (
                    following["value"] > reading["value"]
                    if sense == "upper"
                    else following["value"] < reading["value"]
                )
                answer["verdict"] = FALSIFIED if exceeded else SURVIVED
        answers.append(answer)
    return answers


def bound_metrics(record: dict[str, Any]) -> list[str]:
    """Every metric the survives-next-reading query can be asked of."""
    return sorted(
        slug
        for slug, declaration in record["metrics"].items()
        if declaration.get("kind") == "bound"
    )


def _print_survives(record: dict[str, Any]) -> None:
    for metric in bound_metrics(record):
        print(f"{metric} - survives-next-reading")
        for answer in survives_next_reading(record, metric):
            basis = f" on a {answer['basis']} pair" if answer["basis"] else ""
            print(
                f"  {answer['date']} {answer['commit']}"
                f" value {answer['value']}: {answer['verdict']}{basis}"
            )


def _print_readings(record: dict[str, Any]) -> None:
    for index, reading in enumerate(record["readings"]):
        print(
            f"{index:>3} {reading['metric']} = {reading['value']} {reading['unit']}"
            f" [{reading['method']}, workers {reading['workers']},"
            f" contended {reading['contended']}, {reading['date']}, {reading['commit']}]"
        )


def main(argv: list[str] | None = None) -> int:
    """Grade the tracked record, then print whichever reports were asked for."""
    argv = list(sys.argv[1:] if argv is None else argv)
    offences = grade_tree(REPO_ROOT)
    if offences:
        for offence in offences:
            print(f"OFFENCE: {offence}")
        print(f"FAIL: {len(offences)} offence(s) in {RECORD_RELATIVE}.")
        return 1

    record = load(REPO_ROOT)
    if "--show" in argv:
        _print_readings(record)
    if "--survives" in argv:
        _print_survives(record)
    print(
        f"PASS: {len(record['readings'])} reading(s) in {RECORD_RELATIVE},"
        " every one carrying its receipt."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
