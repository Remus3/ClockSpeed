"""CS-1177's two whole-population forced arms, in a module of their own - CS-1193.

WHY A SEPARATE FILE. The ``pristine`` fixture forces the whole derived canary
population in one child, and the CS-1175 suite forces it again in another.
Under ``--dist loadfile`` a module is one unit of work, so while both lived
beside the rest of tests/test_canary_population.py that module was the
shard's tail on one of CI's two workers. Here, the two big children can land
on different workers. The membership rule, the forcer and every helper stay
in tests/test_canary_population.py; this module only runs the arms that
consume ``pristine``, and its meaning is theirs, unchanged.

THIS MODULE IS ITSELF A MEMBER - it imports the population module, which
reads a canary table - so the forced children run it. Every arm here spawns a
forced run and is deselected in a child by ``forced_red_output``; the one
cheap arm that is not keeps the module graded in the child, as the "no member
ungraded" check requires.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_canary_population import (
    OUTBOUND_PATH,
    REPO_ROOT,
    Verdict,
    canary_suites,
    derived_canary_suites,
    forced_run,
)


@pytest.fixture(scope="module")
def pristine(tmp_path_factory: pytest.TempPathFactory) -> Verdict:
    """The derived population of THIS tree, forced once and shared - counts only."""
    return forced_run(
        tmp_path_factory.mktemp("cs1177_pristine"), REPO_ROOT, derived_canary_suites()
    )


# --------------------------------------------------------------------------
# Arm 2 - a raise inside a holding helper renders no canary
# --------------------------------------------------------------------------

#: The hygienic line in the CS-1167 suite's `refused_lines`, and the same
#: helper with its hygiene removed - the message bound to a named local. The
#: control edits a TEMPORARY copy, never the tree.
HYGIENIC = (
    "    refusals, _, _ = OUTBOUND.scan(\n"
    '        "Status report.\\nsee " + OUTBOUND.CREDENTIAL_CANARIES[reason] + " here\\n"\n'
    "    )\n"
)
UNHYGIENIC = (
    '    message = "Status report.\\nsee " + OUTBOUND.CREDENTIAL_CANARIES[reason] + " here\\n"\n'
    "    refusals, _, _ = OUTBOUND.scan(message)\n"
)
ROOT_LINE = "REPO_ROOT = Path(__file__).resolve().parents[1]\n"
CONTROL_SUITE = "tests/test_cs1167_credential_canary_coverage.py"


def unhygienic_copy(root: Path) -> tuple[str, int, int]:
    """Copy the CS-1167 suite under `root` with one helper's hygiene removed.

    Returns:
        ``(relative path, hygiene edits landed, root edits landed)`` - both
        must be exactly one, or the control grades a copy it did not make.
    """
    source = (REPO_ROOT / CONTROL_SUITE).read_text(encoding="utf-8")
    hygiene = source.count(HYGIENIC)
    rooted = source.count(ROOT_LINE)
    source = source.replace(HYGIENIC, UNHYGIENIC).replace(
        ROOT_LINE, "REPO_ROOT = Path(%r)\n" % str(REPO_ROOT)
    )
    relative = "tests/test_cs1177_unhygienic_copy.py"
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / relative).write_text(source, encoding="utf-8")
    return relative, hygiene, rooted


def test_the_unhygienic_copy_lands_each_edit_exactly_once(tmp_path: Path) -> None:
    """The control's two edits each land once on the suite as it stands - no child spawned.

    The forced arm below asserts the same before it spends a child on the
    copy; this arm states it on its own, cheaply, and is the one arm of this
    module a forced child runs, so the module is graded there.
    """
    relative, hygiene, rooted = unhygienic_copy(tmp_path / "control")
    written = (tmp_path / "control" / relative).is_file()
    assert hygiene == 1, "the hygiene edit landed %d times" % hygiene
    assert rooted == 1, "the root edit landed %d times" % rooted
    assert written, "the unhygienic copy was not written"


def test_a_helper_raise_under_showlocals_renders_no_canary_forced_red_output(
    tmp_path: Path, pristine: Verdict
) -> None:
    """CS-1177: every derived member, holding helpers forced to RAISE, renders no canary.

    THE CONTROL RUNS IN THE SAME TEST: the CS-1167 suite with ONE helper's
    hygiene removed, forced the same way, renders the planted canary - so the
    zero from the tree is a measurement of hygiene, not a capture that cannot
    see a local.
    """
    relative, hygiene, rooted = unhygienic_copy(tmp_path / "control")
    assert hygiene == 1, "the hygiene edit landed %d times" % hygiene
    assert rooted == 1, "the root edit landed %d times" % rooted
    control = forced_run(tmp_path / "control_work", tmp_path / "control", (relative,))
    control_forced = control.forced[relative]
    control_leaked = control.leaked
    assert control_forced >= 1, "the control forced no helper raise"
    assert control_leaked >= 1, "the unhygienic control rendered no canary"

    # Every verdict is bound to a scalar first: assertion rewriting renders an
    # asserted attribute's whole owner, and the owner is not what is graded.
    code = pristine.code
    ungraded = sorted(suite for suite, count in pristine.graded.items() if count == 0)
    total = sum(pristine.forced.values())
    leaked = pristine.leaked
    assert code == 1, "the forced run did not fail: exit %d" % code
    assert ungraded == [], "members no test of which ran: " + ", ".join(ungraded)
    assert total >= 1, "no helper raise was forced in the tree"
    assert leaked == 0, "the forced run rendered %d canary value(s)" % leaked


# --------------------------------------------------------------------------
# Arm 3 - a new module named in no list is picked up and graded
# --------------------------------------------------------------------------

#: A new canary-holding module, named in no list anywhere. Its helper binds a
#: canary to a local, so a forced run that GRADED it renders one.
PLANTED = """
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs1177_planted_outbound", Path(%r))
module = importlib.util.module_from_spec(spec)
sys.modules["cs1177_planted_outbound"] = module
spec.loader.exec_module(module)


def held_length():
    held = module.CREDENTIAL_CANARIES["AWS access key id"]
    return len(held)


def test_a_planted_module_reads_a_canary():
    size = held_length()
    assert size > 0
"""


def test_a_new_canary_module_in_no_list_is_picked_up_and_graded_forced_red_output(
    tmp_path: Path, pristine: Verdict
) -> None:
    """The mutation the acceptance names: plant a module, derive, force, and see it graded.

    The pristine tree is green IN THE SAME RUN - the shared forced verdict of
    this tree is asserted here too, so a planted red and a pristine green are
    one run's two readings.
    """
    root = tmp_path / "planted"
    (root / "tests").mkdir(parents=True)
    planted = root / "tests" / "test_cs1177_planted.py"
    planted.write_text(PLANTED % str(OUTBOUND_PATH), encoding="ascii")
    members = canary_suites(root / "tests")
    picked = members == [planted]
    assert picked, "the planted module was not derived: %d member(s)" % len(members)

    relative = planted.relative_to(root).as_posix()
    verdict = forced_run(tmp_path / "planted_work", root, (relative,))
    graded = verdict.graded[relative]
    forced = verdict.forced[relative]
    rendered = verdict.leaked
    assert graded >= 1, "the planted module was not run"
    assert forced >= 1, "the planted helper was not forced"
    assert rendered >= 1, "the planted module was run but not graded"

    code = pristine.code
    leaked = pristine.leaked
    assert code == 1, "the pristine forced run did not fail: exit %d" % code
    assert leaked == 0, "the pristine tree rendered %d canary value(s)" % leaked
