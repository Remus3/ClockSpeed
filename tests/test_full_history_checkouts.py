"""CS-1228 - every CI job whose pytest run collects a full-history module checks out full history.

THE DEFECT THIS MODULE CLOSES. ``tests/test_sha_citation_gate.py`` carries the
CS-1222 live arm, which FAILS - by design, never skips - on a shallow clone.
``actions/checkout`` is shallow unless told otherwise, and the ``suite`` job of
``.github/workflows/tier2.yml`` ran ``pytest tests`` over a default checkout, so
its ubuntu leg went red every night on that one arm while the module's own
docstring said CI ran it only in a full-history shard. Nothing tied the two.

THE SHAPE. Both workflows are PARSED, never scanned: every ``run`` line of every
step that invokes pytest is split into tokens, its ``tests`` targets and its
``--ignore=`` paths are read, and a job that collects a module named in
:data:`FULL_HISTORY_MODULES` must carry ``fetch-depth: 0`` on its checkout. A
job that ignores the module, or targets elsewhere, owes nothing.

WHAT IS NOT CLAIMED. A target spelled other than ``tests`` or ``tests/...``
(a glob, a variable) is not read as a target, so it would be invisible here. The
anti-vacuity arm below pins that the tier2 ``suite`` job IS found, so the
reader is measured on the job that broke.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Final

import yaml

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
WORKFLOWS: Final = (".github/workflows/tier1.yml", ".github/workflows/tier2.yml")

#: Modules whose live arm FAILS on a shallow clone. Each entry is checked below
#: to still carry that refusal, so a module that stops needing history is red
#: here until it leaves this tuple.
FULL_HISTORY_MODULES: Final = ("tests/test_sha_citation_gate.py",)
SHALLOW_REFUSAL: Final = "assert not report.shallow"

TARGET_ROOT: Final = "tests"
IGNORE_PREFIX: Final = "--ignore="
CHECKOUT_ACTION: Final = "actions/checkout"


def load(relative: str) -> dict[str, Any]:
    """One workflow, parsed.

    Args:
        relative: The workflow's path from the repository root.

    Returns:
        The parsed document.
    """
    document = yaml.safe_load((REPO_ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(document, dict), f"{relative} did not parse to a mapping"
    return document


def covers(claim: str, path: str) -> bool:
    """Whether a pytest target or ignore ``claim`` reaches ``path``.

    Args:
        claim: A path as handed to pytest.
        path: The module asked about.

    Returns:
        True when ``claim`` is ``path`` or a directory above it.
    """
    claim = claim.rstrip("/")
    return path == claim or path.startswith(claim + "/")


def collects(tokens: list[str], path: str) -> bool:
    """Whether one pytest command line collects ``path``.

    Args:
        tokens: The command line, split.
        path: The module asked about.

    Returns:
        True when a target reaches ``path`` and no ``--ignore=`` removes it.
    """
    after = tokens[tokens.index("pytest") + 1 :]
    targets = [t for t in after if t == TARGET_ROOT or t.startswith(TARGET_ROOT + "/")]
    ignores = [t[len(IGNORE_PREFIX) :] for t in after if t.startswith(IGNORE_PREFIX)]
    reached = any(covers(target, path) for target in targets)
    return reached and not any(covers(ignored, path) for ignored in ignores)


def checkout_depth(job: dict[str, Any]) -> object:
    """The ``fetch-depth`` of a job's first checkout step.

    Args:
        job: The parsed job.

    Returns:
        The declared value, or None when the job declares none or has no checkout.
    """
    for step in job.get("steps") or []:
        if isinstance(step, dict) and str(step.get("uses", "")).startswith(CHECKOUT_ACTION):
            return (step.get("with") or {}).get("fetch-depth")
    return None


def collecting_jobs(documents: dict[str, dict[str, Any]]) -> list[tuple[str, str, object]]:
    """Every job that collects a full-history module, with its checkout depth.

    Args:
        documents: Workflow path to parsed document.

    Returns:
        (workflow, job id, fetch-depth) for every collecting job.
    """
    found: list[tuple[str, str, object]] = []
    for relative, document in documents.items():
        jobs = document.get("jobs")
        assert isinstance(jobs, dict), f"{relative} declares no jobs mapping"
        for job_id, job in jobs.items():
            lines = [
                line.split()
                for step in job.get("steps") or []
                if isinstance(step, dict) and isinstance(step.get("run"), str)
                for line in step["run"].splitlines()
            ]
            hit = any(
                "pytest" in tokens and collects(tokens, module)
                for tokens in lines
                for module in FULL_HISTORY_MODULES
            )
            if hit:
                found.append((relative, str(job_id), checkout_depth(job)))
    return found


def offences(documents: dict[str, dict[str, Any]]) -> list[str]:
    """Every collecting job whose checkout is not full history.

    Args:
        documents: Workflow path to parsed document.

    Returns:
        One line per offending job.
    """
    return [
        f"{relative} job {job_id!r}: fetch-depth {depth!r}, needs 0"
        for relative, job_id, depth in collecting_jobs(documents)
        if depth != 0
    ]


def shipped() -> dict[str, dict[str, Any]]:
    """Both shipped workflows, parsed.

    Returns:
        Workflow path to parsed document.
    """
    return {relative: load(relative) for relative in WORKFLOWS}


# --- the live arm --------------------------------------------------------------


def test_every_job_collecting_a_full_history_module_checks_out_full_history() -> None:
    found = offences(shipped())
    assert found == []


def test_the_tier2_suite_job_is_among_the_jobs_read() -> None:
    """Anti-vacuity: the job that broke must be one this module grades."""
    jobs = {(relative, job_id) for relative, job_id, _ in collecting_jobs(shipped())}
    assert (".github/workflows/tier2.yml", "suite") in jobs, sorted(jobs)


def test_every_listed_module_still_refuses_a_shallow_clone() -> None:
    stale = [
        module
        for module in FULL_HISTORY_MODULES
        if SHALLOW_REFUSAL not in (REPO_ROOT / module).read_text(encoding="utf-8")
    ]
    assert stale == []


# --- plants, each checked to have landed -----------------------------------------


def test_a_suite_checkout_without_full_history_is_named() -> None:
    documents = copy.deepcopy(shipped())
    steps = documents[".github/workflows/tier2.yml"]["jobs"]["suite"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith(CHECKOUT_ACTION))
    checkout.pop("with", None)
    assert checkout_depth(documents[".github/workflows/tier2.yml"]["jobs"]["suite"]) is None
    found = offences(documents)
    assert found == [".github/workflows/tier2.yml job 'suite': fetch-depth None, needs 0"]


def test_a_depth_of_one_is_as_shallow_as_none() -> None:
    documents = copy.deepcopy(shipped())
    steps = documents[".github/workflows/tier2.yml"]["jobs"]["suite"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith(CHECKOUT_ACTION))
    checkout["with"] = {"fetch-depth": 1}
    found = offences(documents)
    assert found == [".github/workflows/tier2.yml job 'suite': fetch-depth 1, needs 0"]


def test_an_ignored_module_owes_no_history() -> None:
    """Control: tier1's catch-all ignores the module, so its shallow checkout is fine."""
    assert collects(["python", "-m", "pytest", "tests"], FULL_HISTORY_MODULES[0])
    ignored = ["python", "-m", "pytest", "tests", f"{IGNORE_PREFIX}{FULL_HISTORY_MODULES[0]}"]
    assert not collects(ignored, FULL_HISTORY_MODULES[0])
    sibling = ["python", "-m", "pytest", "tests/test_sha_citation_gate_other.py"]
    assert not collects(sibling, FULL_HISTORY_MODULES[0])
