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
    tree        whether that commit WAS the tree - clean, dirty or unwitnessed (CS-1220)

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

THE TREE WITNESS, AND THE RULE FOR WHO MAY CLAIM `clean` (CS-1220). A commit sha
names a tree only when the working tree matched it; a reading taken over
uncommitted edits measured code no sha names. So every reading carries `tree`:

    clean        the working tree matched `commit` when the reading was taken
    dirty        it did not - the reading measured code no sha names
    unwitnessed  nobody recorded which - the escape for the seeded rows only

A `ci_job` reading, and a `derived` reading every input of which is one, may
claim `clean` BY THE FACT of the runner's fresh checkout of `commit`, the same
fact that lets it claim `contended: false` (CS-1223 F2). The `ci_job` reading
must say WHICH run: a `ci_run` field holding the run's GitHub Actions URL. The
grader checks only its shape - it never reaches the network, so it does NOT
verify that the run exists, checked out `commit`, or produced the value. A
`derived` reading names its `inputs` by index, and may claim `clean` only when
every one is a `ci_job` reading itself claiming `clean`. A locally-sourced reading - `paired`,
`unpaired`, `local_suite` or `profile` - may claim `clean` only by carrying a
`witness` (CS-1223, below). `unwitnessed` is accepted only on one of the rows of
:data:`SEEDED_UNWITNESSED_READINGS` (CS-1223, below), which is how the sixteen
seeded rows keep their values and dates unchanged while every other reading must
say which tree it read. :func:`comparability` returns
:data:`UNWITNESSED_TREE` - a non-comparable verdict naming the cause - for any
pair with an unwitnessed side, and `not_comparable` for any pair with a dirty one.

THE ESCAPE IS A PINNED SEED SET, NOT A DATE (CS-1223). CS-1220 gated
`unwitnessed` on the reading's own `date`, which whoever writes the row supplies,
so a new row dated before the cutover passed. The escape is now granted by ROW
IDENTITY: each row that was in the record when CS-1220 landed is pinned WHOLE -
every field, its `source` included - by :data:`SEEDED_ROW_DIGESTS` (its receipt
is also listed readably in :data:`SEEDED_UNWITNESSED_READINGS`). Each may claim
the escape at most once, and any other row - an edited seed row, or a new row
whatever its date - is refused.

THE WITNESS A LOCAL `clean` CLAIM CARRIES, AND WHAT "CHECKABLE" MEANS (CS-1223).
The `witness` field is the record `python tools/freeze_witness.py freeze` prints,
verbatim, taken at the time of the reading: `schema`, `tree`, `tree_files`,
`bytecode`, `bytecode_files`. Its `tree` half is a digest of the raw on-disk
bytes of every tracked and untracked-unignored file. Over a CLEAN checkout those
bytes are exactly the blobs of `commit` - this repository checks out every text
file LF with no smudge filter - so the grader RE-DERIVES that digest from the
commit's own objects (:func:`commit_tree_digest`) and refuses the claim unless it
matches, file count included. :func:`grade` checks the shape; :func:`grade_tree`
does the re-derivation, and refuses when the commit is not in the clone - an
unpublished commit cannot be witnessed - except in a SHALLOW clone, where an
absent commit is reported as unchecked rather than refused, because CI's
depth-one checkout lacks every historical commit by construction. Unchecked is
never silent: the CLI prints each one, and the tracked-record test warns with
the count in a shallow clone and FAILS on any in a full-history one (tier2's
suite job checks out full history, so the record is enforced there).

What this DOES catch: a reading taken over uncommitted edits, a stray untracked
file, an LF-to-CRLF flip that porcelain cannot see, a witness copied from another
commit, and a hand-typed or forged digest. What it CANNOT catch, recorded as the
residual rather than hidden: the digest is a function of `commit` alone over a
clean tree, so anyone can compute a matching witness AFTER the fact without ever
having read the tree. The witness turns `clean` from an unrecorded assertion into
a mechanically-captured one that refutes an honest mistake; it does not bind a
dishonest recorder. The `bytecode` half cannot be re-derived from any commit
(bytecode is gitignored) and is shape-checked only. A symlink in the commit is
refused, because its checkout on this platform is not determined by the commit,
and so is a submodule, whose content the witness hashes as one opaque entry.

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

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date as _date
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TOOLS_DIR.parent

# `tools` carries no __init__.py, so siblings are imported under their BARE
# names, the way tools/freeze_witness.py imports the resolver.
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import freeze_witness  # noqa: E402
from freeze_witness import _GIT_RELOCATING, _feed  # noqa: E402
from toolpath import resolve_tool  # noqa: E402

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
READING_FIELDS = (*RECEIPT_FIELDS, "tree", "source", "superseded_by")

#: CS-1223. Fields a reading MAY carry. Absence of `witness` means none was taken.
OPTIONAL_READING_FIELDS = ("witness", "ci_run", "inputs")

#: CS-1223. The shape of a witness: the freeze_witness record, verbatim.
WITNESS_FIELDS = ("schema", "tree", "tree_files", "bytecode", "bytecode_files")

#: CS-1220. The tree a reading was taken over. See the module docstring.
TREE_CLEAN = "clean"
TREE_DIRTY = "dirty"
TREE_UNWITNESSED = "unwitnessed"
TREE_STATES = (TREE_CLEAN, TREE_DIRTY, TREE_UNWITNESSED)

#: The day CS-1220 was filed; every seeded row predates it. Since CS-1223 it
#: gates NOTHING - a date is supplied by whoever writes the row - and is kept as
#: the record of when the witness became required.
TREE_WITNESS_REQUIRED_FROM = "2026-10-02"

_SEED_A = ("2026-09-05", "c33afca")
_SEED_B = ("2026-09-17", "e3169a64770a00fd4484452148a9ef66ac33cb7b")

#: CS-1223. The ONLY rows that may claim `unwitnessed`: the receipt of each row
#: that was in `tools/measurements.json` when CS-1220 landed, in RECEIPT_FIELDS
#: order, pinned by identity so neither a backdated new row nor an edited seed
#: row inherits the escape. Each may be claimed at most once.
SEEDED_UNWITNESSED_READINGS: tuple[tuple[Any, ...], ...] = (
    ("tier1_pytest_step_seconds", 541.68, "seconds", "ci_job", 1, False, *_SEED_A),
    ("tier1_pytest_step_seconds", 590.82, "seconds", "ci_job", 1, False, *_SEED_A),
    ("tier1_pytest_step_seconds", 424.18, "seconds", "ci_job", "unresolved", False, *_SEED_A),
    ("tier1_pytest_step_seconds", 475.98, "seconds", "ci_job", "unresolved", False, *_SEED_A),
    ("tier1_pytest_step_seconds", 483.14, "seconds", "ci_job", "unresolved", False, *_SEED_A),
    ("tier1_pytest_step_seconds", 470.67, "seconds", "ci_job", "unresolved", False, *_SEED_A),
    ("tier1_nauto_speedup_ratio", 1.222, "ratio", "unpaired", "unresolved", False, *_SEED_A),
    ("tier1_tests_passed", 4784, "count", "ci_job", 1, False, *_SEED_A),
    ("tier1_slowest_test_seconds", 111.39, "seconds", "profile", 1, False, *_SEED_A),
    ("tier1_slowest_test_share_percent", 18.9, "percent", "profile", 1, False, *_SEED_A),
    *(
        (metric, value, unit, "derived", "unresolved", False, *_SEED_B)
        for metric, value, unit in (
            ("tier1_jitter_seconds_gates_lint_types_tests", 129, "seconds"),
            ("tier1_jitter_seconds_guard_shard", 28, "seconds"),
            ("tier1_jitter_seconds_save_shard", 38, "seconds"),
            ("tier1_growth_seconds_per_commit_gates_lint_types_tests", -1.04, "seconds_per_commit"),
            ("tier1_growth_seconds_per_commit_guard_shard", 0.48, "seconds_per_commit"),
            ("tier1_growth_seconds_per_commit_save_shard", -0.1, "seconds_per_commit"),
        )
    ),
)

#: CS-1223 F1. The receipts above are the READABLE pin; the escape is granted by
#: these - the SHA-256 of each seeded row's canonical JSON with every field but
#: `superseded_by` (`source` included), so any edit to a seed row loses it while
#: superseding one - ordinary record use - does not (R12).
SEEDED_ROW_DIGESTS = frozenset(
    (
        "aee06004a07acdef0efcb06c3873853328d155f4864e0c0a000ec99cf3d620ef",
        "f15e2ddc282e6f9caff783998c832397148039acdca684ead46e8d87735bf78c",
        "a2cda6ba3e0651e4b0b7237d9ca90e6e4da8828a577979dbfaa0e8beeb571b68",
        "309a2a8e523ba5b367d990d694138153573a051a6fab0d0b5bc40d3e65a95403",
        "fb7e72e826c063fde04d4ba01abc808d58c209221aa44f7adbefaad56124efcf",
        "b65f0396b6f85a2a47fc2d77e9e95b116a25e912f504ec2830dd7bb0895ac25b",
        "1a0859eb20a3294c72e787043adee7ca2efd8579a4b0cf61a343e3eacf7d5364",
        "b5a4b52e313f33aab3b2c0619e49e473824c895d9d6f644b4a7bc57428fe495d",
        "6407bfbfef598b917d5bf9755d813713ce07aa0092c97f9d6591448e1b123975",
        "5689ba691094430899ee89b38a5477523b122d59e21f7e407df262a3c974e0a5",
        "3a5cf7d1cdabbb6e0b373e5f3a50873a89fd92ff605e29b36aae89b878c9f864",
        "af952c161e7708ac229345de40a7de47c650549caa894eb87b624c2f33acc86b",
        "f5c9a0487114da22c277ed6347a37b665b9baa83c0c0d55d1d0246f7a267fc3c",
        "24fc4b3a9db041fd0adfc78e7d42f3c58e9dd3cbea72c44ddbaa6c1758d22bb9",
        "09ad140d7cd090a527a45396711586b18b01419584748fc08f4d08c486f72b04",
        "546dec463b10920e7034256dce2e5d0b78e6be2c2ac14374fc91d6c4e13b032f",
    )
)

#: A metric is declared once. `sense` is required of a bound and refused of an
#: observation, because only a bound has a direction it can be refuted from.
OBSERVATION_FIELDS = ("kind", "unit")
BOUND_FIELDS = ("kind", "unit", "sense")

UNITS = ("seconds", "ratio", "count", "percent", "seconds_per_commit")
METHODS = ("paired", "unpaired", "ci_job", "local_suite", "profile", "derived")
#: CS-1223. The locally-sourced methods: a `clean` claim from one needs a witness.
LOCAL_METHODS = ("paired", "unpaired", "local_suite", "profile")
KINDS = ("observation", "bound")
SENSES = ("upper", "lower")

#: The two escape values. See the module docstring for what they cost.
WORKERS_UNRESOLVED = "unresolved"
CONTENDED_UNKNOWN = "unknown"

#: Comparability of a pair of readings.
COMPARABLE = "comparable"
UNPROVEN = "unproven"
NOT_COMPARABLE = "not_comparable"
#: Non-comparable BECAUSE a side's tree was never recorded. Distinct from
#: `not_comparable` so the verdict names the cause (CS-1220).
UNWITNESSED_TREE = "unwitnessed_tree"

#: Verdicts of the survives-next-reading query.
SURVIVED = "survived"
FALSIFIED = "falsified"
UNTESTED = "untested"
SUPERSEDED = "superseded"

_METRIC_SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
#: Round 4. A reading citing a run spells its commit whole.
_FULL_COMMIT = re.compile(r"^[0-9a-f]{40}\Z")
_CITATION = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*#\S.*$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
#: CS-1223. THIS repository, as the tracked CITATION.cff names it; a test pins
#: the two equal, so a run of another repository can never be cited.
REPOSITORY_URL = "https://github.com/Remus3/Clockspeed"
#: CS-1223 F2(b). A GitHub Actions run of this repository, optionally narrowed
#: to one job. Digits only after the fixed prefix, so no `..` can be spelt.
_CI_RUN = re.compile(
    "^" + re.escape(REPOSITORY_URL) + r"/actions/runs/(?P<run>[1-9][0-9]*)(/job/[1-9][0-9]*)?\Z"
)
_GIT_TIMEOUT_SECONDS = 300


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
    # A non-string metric is refused by name, never raised on (rule 7).
    declaration = (
        metrics.get(metric) if isinstance(metrics, dict) and isinstance(metric, str) else None
    )
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


def row_digest(reading: dict[str, Any]) -> str:
    """SHA-256 of the row as canonical JSON, `superseded_by` aside - a seed's identity."""
    pinned = {field: value for field, value in reading.items() if field != "superseded_by"}
    canonical = json.dumps(pinned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _grade_tree_witness(where: str, reading: dict[str, Any], claimed: set[str]) -> list[str]:
    """CS-1220 and CS-1223. The field is in domain, the escape is a seeded row's.

    Presence is graded with every other field in :func:`grade`. `unwitnessed` is
    accepted only on a row whose whole digest is in :data:`SEEDED_ROW_DIGESTS`,
    once; ``claimed`` carries the pins already used. A local `clean` claim must
    carry a witness and a runner `clean` claim must cite its run; a `derived`
    claim's inputs are graded in :func:`_grade_inputs`.
    """
    tree = reading["tree"]
    if isinstance(tree, bool) or tree not in TREE_STATES:
        return [f"{where}: tree {tree!r} is not one of {TREE_STATES}"]
    offences: list[str] = []
    if tree == TREE_UNWITNESSED:
        key = row_digest(reading)
        if key not in SEEDED_ROW_DIGESTS:
            offences.append(
                f"{where}: tree {TREE_UNWITNESSED!r} is refused on any row but an unedited"
                " seeded row CS-1220 marked, whatever its date - record 'clean' or 'dirty'"
            )
        elif key in claimed:
            offences.append(
                f"{where}: tree {TREE_UNWITNESSED!r} is refused on a second copy of a seeded row"
            )
        else:
            claimed.add(key)
    if "witness" in reading:
        offences.extend(_grade_witness_shape(where, reading["witness"]))
    elif tree == TREE_CLEAN and reading["method"] in LOCAL_METHODS:
        offences.append(
            f"{where}: tree {TREE_CLEAN!r} on a {reading['method']!r} reading carries no"
            " witness - record the output of tools/freeze_witness.py freeze, or 'dirty'"
        )
    if "ci_run" in reading or (tree == TREE_CLEAN and reading["method"] == "ci_job"):
        ci_run = reading.get("ci_run")
        if reading["method"] != "ci_job":
            offences.append(f"{where}: ci_run is carried only by a 'ci_job' reading")
        elif not isinstance(reading["commit"], str) or not _FULL_COMMIT.match(reading["commit"]):
            offences.append(
                f"{where}: a reading citing a ci_run needs a full 40-hex commit - a short"
                " sha can name more than one commit"
            )
        elif not isinstance(ci_run, str) or not _CI_RUN.match(ci_run):
            offences.append(
                f"{where}: tree {TREE_CLEAN!r} on a 'ci_job' reading needs a ci_run naming"
                " the GitHub Actions run whose checkout it read, as its run URL"
            )
    return offences


def _grade_inputs(
    where: str, index: int, reading: dict[str, Any], readings: list[Any]
) -> list[str]:
    """CS-1223 F2(a). A `derived` `clean` claim rests on runner readings only.

    `inputs` lists the indices of the readings a derived figure was computed
    from. A `derived` reading may claim `clean` only when every input is a
    `ci_job` reading that itself claims `clean` - the fact the docstring names -
    taken on the derived reading's own `commit`, not superseded, and named once.
    """
    if "inputs" not in reading and not (
        reading["method"] == "derived" and reading["tree"] == TREE_CLEAN
    ):
        return []
    if reading["method"] != "derived":
        return [f"{where}: inputs are carried only by a 'derived' reading"]
    inputs = reading.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        return [
            f"{where}: tree {TREE_CLEAN!r} on a 'derived' reading needs inputs naming"
            " the 'ci_job' readings it was computed from"
        ]
    offences: list[str] = []
    seen: set[int] = set()
    for target in inputs:
        if (
            isinstance(target, bool)
            or not isinstance(target, int)
            or not 0 <= target < len(readings)
            or target == index
        ):
            offences.append(f"{where}: input {target!r} names no other reading")
            continue
        if target in seen:
            offences.append(f"{where}: input {target} is named twice")
            continue
        seen.add(target)
        named = readings[target]
        if reading["tree"] != TREE_CLEAN:
            continue
        if not (
            isinstance(named, dict)
            and named.get("method") == "ci_job"
            and named.get("tree") == TREE_CLEAN
        ):
            offences.append(
                f"{where}: input {target} is not a 'ci_job' reading claiming {TREE_CLEAN!r},"
                f" so a 'derived' reading over it may not claim {TREE_CLEAN!r}"
            )
            continue
        if named.get("commit") != reading["commit"]:
            offences.append(
                f"{where}: input {target} was taken on another commit, so it does not"
                " vouch for this reading's tree"
            )
        if named.get("superseded_by") is not None:
            offences.append(f"{where}: input {target} is superseded and vouches for nothing")
    return offences


def _grade_witness_shape(where: str, witness: Any) -> list[str]:
    """CS-1223. A witness is the freeze_witness record verbatim, nothing more."""
    if not isinstance(witness, dict):
        return [f"{where}: witness is not a freeze_witness record"]
    if tuple(sorted(witness)) != tuple(sorted(WITNESS_FIELDS)):
        return [f"{where}: witness fields {sorted(witness)} are not {sorted(WITNESS_FIELDS)}"]
    offences: list[str] = []
    schema = witness["schema"]
    if isinstance(schema, bool) or schema != freeze_witness.SCHEMA:
        offences.append(f"{where}: witness schema {schema!r} is not {freeze_witness.SCHEMA}")
    for field in ("tree", "bytecode"):
        digest = witness[field]
        if not isinstance(digest, str) or not _DIGEST.match(digest):
            offences.append(f"{where}: witness {field} is not a lowercase SHA-256 hex digest")
    for field in ("tree_files", "bytecode_files"):
        count = witness[field]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            offences.append(f"{where}: witness {field} {count!r} is not a count")
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


def _grade_run_commits(readings: list[Any]) -> list[str]:
    """A run checks out ONE commit, so its URL vouches for one commit (rounds 3-4).

    The run id is the number after `/actions/runs/`; a `/job/` suffix names a job
    of the same run and the same checkout, so it is ignored. Every reading citing
    a run carries a FULL commit (graded in :func:`_grade_tree_witness`), so commit
    identity is plain equality - no prefix rule, which is not transitive. When one
    run is cited on more than one commit, EVERY reading citing it is refused, so
    the verdict does not depend on the order of the record.
    """
    by_run: dict[str, list[tuple[int, str]]] = {}
    for index, reading in enumerate(readings):
        if not isinstance(reading, dict):
            continue
        ci_run, commit = reading.get("ci_run"), reading.get("commit")
        if not isinstance(ci_run, str) or not isinstance(commit, str):
            continue
        matched = _CI_RUN.match(ci_run)
        if not matched or not _FULL_COMMIT.match(commit):
            continue
        by_run.setdefault(matched.group("run"), []).append((index, commit))
    offences: list[str] = []
    for run, citations in sorted(by_run.items()):
        commits = sorted({commit for _, commit in citations})
        if len(commits) < 2:  # noqa: PLR2004 - one commit is the rule itself
            continue
        offences.extend(
            f"reading {index}: ci_run cites run {run}, which the record cites on"
            f" {len(commits)} commits - one run checks out one commit"
            for index, _ in citations
        )
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

    claimed: set[str] = set()
    for index, reading in enumerate(readings):
        where = f"reading {index}"
        if not isinstance(reading, dict):
            offences.append(f"{where}: not a mapping")
            continue
        missing = [field for field in READING_FIELDS if field not in reading]
        allowed = (*READING_FIELDS, *OPTIONAL_READING_FIELDS)
        extra = [field for field in reading if field not in allowed]
        for field in missing:
            offences.append(f"{where}: receipt field {field!r} is missing")
        for field in extra:
            offences.append(f"{where}: field {field!r} is not on the record's allowlist")
        if missing:
            continue
        offences.extend(_grade_receipt(where, reading, record["metrics"]))
        offences.extend(_grade_tree_witness(where, reading, claimed))
        offences.extend(_grade_inputs(where, index, reading, readings))
        offences.extend(_grade_source(where, reading))

    offences.extend(_grade_supersession(readings))
    offences.extend(_grade_run_commits(readings))
    return offences


class WitnessCheckError(Exception):
    """git could not answer a witness question. ``reason`` is authored text only."""

    def __init__(self, reason: str) -> None:
        """Keep the authored text as the printable field."""
        super().__init__(reason)
        self.reason = reason


def _git(root: Path, *args: str, stdin: bytes | None = None) -> tuple[int, bytes]:
    git = resolve_tool("git")
    if git is None:
        raise WitnessCheckError("git is not on PATH")
    env = {k: v for k, v in os.environ.items() if k.upper() not in _GIT_RELOCATING}
    try:
        proc = subprocess.run(
            [git, "-c", "core.autocrlf=false", "-C", str(root), *args],
            input=stdin,
            capture_output=True,
            env=env,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WitnessCheckError(f"git {args[0]} could not run ({type(exc).__name__})") from None
    return proc.returncode, proc.stdout


def _resolve_commit(root: Path, commit: str) -> str | None:
    """The full sha ``commit`` names in ``root``, or None when the clone lacks it."""
    rc, out = _git(root, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}")
    return out.decode("ascii").strip() if rc == 0 else None


def is_shallow(root: Path) -> bool:
    """Whether ``root`` is a shallow clone, whose history lacks old commits."""
    rc, out = _git(root, "rev-parse", "--is-shallow-repository")
    if rc != 0:
        raise WitnessCheckError(f"git rev-parse exited {rc}")
    return out.strip() == b"true"


def commit_tree_digest(root: Path, commit: str) -> tuple[str, int]:
    """CS-1223. The freeze_witness tree digest a CLEAN checkout of ``commit`` has.

    Re-derived from the commit's own objects: each path's bytes are its blob,
    because this repository checks text out LF with no smudge filter. A symlink
    is refused - its checkout on Windows is not determined by the commit - and
    so is a gitlink: freeze_witness hashes a submodule as an opaque `dir`, so
    nothing inside it is witnessed.
    """
    rc, listing = _git(root, "ls-tree", "-r", "-z", "--full-tree", commit)
    if rc != 0:
        raise WitnessCheckError(f"git ls-tree exited {rc}")
    entries: list[tuple[str, str, str]] = []
    for record in listing.split(b"\0"):
        if not record:
            continue
        meta, _, raw_path = record.partition(b"\t")
        mode, _kind, sha = meta.decode("ascii").split(" ")
        entries.append((raw_path.decode("utf-8", "surrogateescape"), mode, sha))
    if any(mode == "120000" for _, mode, _ in entries):
        raise WitnessCheckError("the commit carries a symlink, whose checkout it does not fix")
    if any(mode == "160000" for _, mode, _ in entries):
        raise WitnessCheckError("the commit carries a submodule, whose content is not witnessed")
    blobs = [sha for _, _, sha in entries]
    rc, batch = _git(root, "cat-file", "--batch", stdin="".join(f"{s}\n" for s in blobs).encode())
    if rc != 0:
        raise WitnessCheckError(f"git cat-file exited {rc}")
    contents: dict[str, bytes] = {}
    cursor = 0
    for sha in blobs:
        newline = batch.index(b"\n", cursor)
        answered, kind, size_text = [*batch[cursor:newline].decode("ascii").split(" "), "", ""][:3]
        if answered != sha or kind != "blob" or not size_text.isdigit():
            raise WitnessCheckError("git cat-file answered out of step")
        size = int(size_text)
        contents[sha] = batch[newline + 1 : newline + 1 + size]
        cursor = newline + 1 + size + 1
    digest = hashlib.sha256()
    for path, _, sha in sorted(entries):
        _feed(digest, path.encode("utf-8", "surrogateescape"))
        _feed(digest, b"file:" + hashlib.sha256(contents[sha]).digest())
    return digest.hexdigest(), len(entries)


def _check_witness(root: Path, where: str, reading: dict[str, Any], unchecked: list[str]) -> str:
    """One offence, or the empty string. A shallow clone's gap goes to ``unchecked``."""
    commit = reading["commit"]
    try:
        full = _resolve_commit(root, commit)
        if full is None:
            if is_shallow(root):
                unchecked.append(f"{where}: witness of {commit} not re-derived - shallow clone")
                return ""
            return (
                f"{where}: witness binds commit {commit}, which this clone does not hold"
                " - an unpublished commit cannot be witnessed"
            )
        derived = commit_tree_digest(root, full)
    except WitnessCheckError as exc:
        return f"{where}: witness could not be re-derived - {exc.reason}"
    witness = reading["witness"]
    if (witness["tree"], witness["tree_files"]) != derived:
        return (
            f"{where}: tree {TREE_CLEAN!r} is refuted - the witness digest is not the digest"
            f" of a clean checkout of {commit}, so the reading read other bytes"
        )
    return ""


def grade_tree(root: Path, unchecked: list[str] | None = None) -> list[str]:
    """Grade the record in ``root`` AND check that every citation names a file.

    CS-1223: every well-formed witness on a `clean` reading is re-derived from
    its commit. A witness a shallow clone cannot re-derive is listed in
    ``unchecked`` when the caller passes one.
    """
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
    gaps: list[str] = [] if unchecked is None else unchecked
    for index, reading in enumerate(readings):
        if not isinstance(reading, dict):
            continue
        if (
            reading.get("tree") == TREE_CLEAN
            and isinstance(reading.get("commit"), str)
            and _COMMIT.match(reading["commit"])
            and not _grade_witness_shape("", reading.get("witness"))
        ):
            refuted = _check_witness(root, f"reading {index}", reading, gaps)
            if refuted:
                offences.append(refuted)
        source = reading.get("source")
        for citation in source if isinstance(source, list) else []:
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

    CS-1220: the tree is checked FIRST so the verdict names it. A side whose tree
    was never recorded - or is absent or out of domain - makes the pair
    `unwitnessed_tree`; a side read over a dirty tree measured code no sha names,
    so the pair is `not_comparable`.
    """
    trees = (left.get("tree", TREE_UNWITNESSED), right.get("tree", TREE_UNWITNESSED))
    if any(tree not in (TREE_CLEAN, TREE_DIRTY) for tree in trees):
        return UNWITNESSED_TREE
    if TREE_DIRTY in trees:
        return NOT_COMPARABLE
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
            if basis not in (NOT_COMPARABLE, UNWITNESSED_TREE):
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
            f" contended {reading['contended']}, {reading['date']}, {reading['commit']},"
            f" tree {reading['tree']}]"
        )


def main(argv: list[str] | None = None) -> int:
    """Grade the tracked record, then print whichever reports were asked for."""
    argv = list(sys.argv[1:] if argv is None else argv)
    unchecked: list[str] = []
    offences = grade_tree(REPO_ROOT, unchecked)
    for gap in unchecked:
        print(f"UNCHECKED: {gap}")
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
