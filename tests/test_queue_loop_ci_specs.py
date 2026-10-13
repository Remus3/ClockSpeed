"""The driver's CI specs must still describe the workflows on disk.

WHY THIS IS A SEPARATE MODULE FROM tests/test_queue_loop.py. That module grades
the driver against FIXTURES - job payloads written by hand - and it must, because
a unit test may not reach `gh`. But a fixture agrees with whatever it was written
from, forever. Rename `full suite` in `.github/workflows/tier2.yml` and every arm
over there stays green while the live grader quietly answers `unavailable` for the
rest of the project's life: the driver would wait out a run, fail to find the job
it grades, record an answer about the TOOL, and never once say the tree was red.
That is a silent loss of the whole acceptance gate.

So this module reads the WORKFLOW FILES and asserts the specs still fit them. It
is the only place in the suite where the two are compared.

NO YAML PARSER. `tests/conftest.py` is dependency-free on purpose - the suite has
to run on a clean machine - so the little that is needed here is read off the
lines. The parser is deliberately strict: it recognises the shape these two files
actually use and raises on anything else rather than silently matching nothing,
because a parser that quietly returns an empty set turns every assertion below
into a vacuous pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ops.loop import queue_loop  # noqa: E402

WORKFLOWS = ROOT / ".github" / "workflows"

#: A job key at two spaces, then its `name:` at four. Both files use this shape.
_JOB_KEY = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
_JOB_NAME = re.compile(r"^    name:\s*(.+?)\s*$")
#: `${{ matrix.os }}` and friends. A matrix job's declared name is a TEMPLATE;
#: what CI reports is one job per leg with the expansion substituted in, which
#: is exactly why the driver's matchers are prefixes.
_TEMPLATE = re.compile(r"\$\{\{[^}]*\}\}")


def declared_job_names(workflow: str) -> dict[str, str]:
    """{job key: declared name} for one workflow file.

    Raises rather than returning empty when the `jobs:` block cannot be found -
    see the module docstring on vacuous passes.
    """
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "jobs:")
    except StopIteration:  # pragma: no cover - a broken file
        raise AssertionError(f"{workflow} has no top-level `jobs:` block") from None
    found: dict[str, str] = {}
    key = None
    for line in lines[start + 1 :]:
        if line and not line.startswith((" ", "#")):
            break  # left the jobs block
        match = _JOB_KEY.match(line)
        if match:
            key = match.group(1)
            continue
        if key is not None and key not in found:
            name = _JOB_NAME.match(line)
            if name:
                found[key] = name.group(1)
    assert found, f"{workflow}: parsed no job names, so nothing below would mean anything"
    return found


def trigger_block(workflow: str) -> str:
    """The `on:` block, verbatim, up to the next top-level key."""
    lines = (WORKFLOWS / workflow).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.rstrip() == "on:")
    out = []
    for line in lines[start + 1 :]:
        if line and not line.startswith((" ", "#")):
            break
        out.append(line)
    return "\n".join(out)


def _matchable(name: str) -> str:
    """A declared name with its templating cut back to the literal prefix.

    `full suite (${{ matrix.os }})` becomes `full suite (` - which is exactly
    what CI reports the common prefix of its legs to be, and exactly the form
    the driver matches on.
    """
    match = _TEMPLATE.search(name)
    return name[: match.start()] if match else name


# ---------------------------------------------------------------------------


def test_the_parser_actually_finds_the_jobs_it_claims_to():
    """The known-good control. Everything below is vacuous without it."""
    tier1 = declared_job_names("tier1.yml")
    tier2 = declared_job_names("tier2.yml")
    # THE SET IS PINNED ON PURPOSE - this is the parser's known-good control,
    # so it names what the parse must find rather than deriving it from the
    # same file. `hooks` joined it deliberately with CS-1193's fourth shard,
    # `fill` with CS-1198's fifth and `scan` with CS-1317's sixth.
    assert set(tier1) == {"fast", "save", "guards", "hooks", "fill", "scan"}, tier1
    assert set(tier2) >= {"suite", "clean-checkout-probe", "audits"}, tier2


@pytest.mark.parametrize("spec", queue_loop.CI_SPECS, ids=lambda s: s.workflow)
def test_every_required_matcher_still_matches_a_declared_job(spec):
    """A matcher that matches nothing grades nothing, forever and silently."""
    declared = [_matchable(name) for name in declared_job_names(spec.workflow).values()]
    unmatched = [
        m
        for m in spec.required
        if not any(name == m or name.startswith(m) or m.startswith(name) for name in declared)
    ]
    assert not unmatched, (
        f"{spec.workflow} declares {declared}; these matchers now match NOTHING "
        f"and the driver would answer 'unavailable' for every run: {unmatched}"
    )


@pytest.mark.parametrize("spec", queue_loop.CI_SPECS, ids=lambda s: s.workflow)
def test_every_advisory_matcher_still_matches_a_declared_job(spec):
    """An advisory matcher that matches nothing is a job silently GRADED.

    The failure runs the other way from the one above and is easier to miss: the
    exclusion stops applying, the audit job's red starts ending nights, and
    nothing anywhere says why.
    """
    declared = [_matchable(name) for name in declared_job_names(spec.workflow).values()]
    unmatched = [
        m
        for m in spec.advisory
        if not any(name == m or name.startswith(m) or m.startswith(name) for name in declared)
    ]
    assert not unmatched, f"{spec.workflow}: advisory matchers matching nothing: {unmatched}"


@pytest.mark.parametrize("spec", queue_loop.CI_SPECS, ids=lambda s: s.workflow)
def test_every_declared_job_is_covered_by_some_matcher(spec):
    """Every job a workflow declares must be covered by some matcher.

    THE REVERSE DIRECTION. The two arms above ask matcher -> job; this one asks
    job -> matcher, and nothing in this suite asked it before.

    Add a shard to a workflow and touch nothing else and the driver grades it
    by accident or not at all: a guard shard that is SKIPPED, or that the run
    never reached, is not a required matcher and is not advisory, so the
    grader's tail accepts it and the verdict is `success`. The lane then pushes
    the next row onto a main whose new shard was never measured.

    COVERAGE IS ONE-WAY ON PURPOSE. A declared name is a TEMPLATE; what CI
    reports is that name with `${{ ... }}` expanded, so the literal prefix is
    all this file can know. Matcher `m` is guaranteed to match EVERY expansion
    only when the declared prefix itself starts with `m` - the symmetric test
    the forward arms use would let a declared `tests` count as covered by a
    matcher `tests (save shard)`, which matches no job the workflow can emit.
    """
    declared = declared_job_names(spec.workflow)
    matchers = (*spec.required, *spec.advisory)
    uncovered = {
        key: name
        for key, name in declared.items()
        if not any(_matchable(name).startswith(m) for m in matchers)
    }
    assert not uncovered, (
        f"{spec.workflow} declares job(s) no matcher covers: {uncovered}. "
        f"Neither required nor advisory, so the driver grades them by accident: "
        f"a skipped or never-reached one reads as success and the lane ships on "
        f"a shard nobody measured. Matchers are {matchers}"
    )


@pytest.mark.parametrize("spec", queue_loop.CI_SPECS, ids=lambda s: s.workflow)
def test_the_dispatch_flag_agrees_with_the_workflow_triggers(spec):
    """`dispatch` is a claim about the file, and this is where it is checked.

    True must mean: the workflow declares `workflow_dispatch` AND does not fire
    on a branch push, so a worker's commit produces no run unless the driver
    asks for one. False must mean the push already triggered it - and
    dispatching one of those can only fail.
    """
    block = trigger_block(spec.workflow)
    declares_dispatch = "workflow_dispatch" in block
    # A branch push, as opposed to a tag push. tier2's `push:` carries `tags:`.
    fires_on_branch_push = (
        bool(re.search(r"^  push:\s*$", block, re.MULTILINE)) and "branches:" in block
    )
    if spec.dispatch:
        assert declares_dispatch, (
            f"{spec.workflow} is marked dispatch=True but declares no "
            f"workflow_dispatch trigger - every dispatch would fail"
        )
        assert not fires_on_branch_push, (
            f"{spec.workflow} fires on a branch push, so the worker's push "
            f"already made a run; dispatching a second one wastes a runner"
        )
    else:
        assert fires_on_branch_push, (
            f"{spec.workflow} is marked dispatch=False, which claims the push "
            f"already triggered it - but it does not fire on a branch push, so "
            f"no run will ever appear and the driver will wait for nothing"
        )


def test_the_self_cancelling_trap_is_still_where_the_driver_thinks_it_is():
    """tier1 cancels in progress; tier2 does not. Both are load-bearing.

    If tier1 ever stopped cancelling, the driver-owned wait would still be
    correct but its stated reason would be false. If tier2 STARTED cancelling,
    the dispatched run this driver waits on could be killed by the next cycle
    and the whole acceptance gate would go quiet - which is the failure the
    ported design was built to end.
    """
    tier1 = (WORKFLOWS / "tier1.yml").read_text(encoding="utf-8")
    tier2 = (WORKFLOWS / "tier2.yml").read_text(encoding="utf-8")
    assert re.search(r"cancel-in-progress:\s*true", tier1), (
        "tier1 no longer cancels superseded runs - ops/loop/queue_loop.py says "
        "it does, in the paragraph explaining why the driver owns the wait"
    )
    assert re.search(r"cancel-in-progress:\s*false", tier2), (
        "tier2 now CANCELS in progress. A dispatched run can be killed by the "
        "next cycle's dispatch, so the driver's acceptance gate can go silent"
    )
