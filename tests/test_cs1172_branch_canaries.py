"""CS-1172 - the credential canaries are earned PER BRANCH, not per rule.

THE DEFECT. CS-1167 gave every rule in ``SECRET_PATTERNS`` one canary. A rule
NARROWED so it still matches that one example - an AWS rule losing one key
prefix, a GitHub rule losing a token prefix, the vendor-prefix rule losing a
family - stayed green, because a rule was graded on a single string. MEASURED
before this file existed: three such narrowings planted at once left the
CS-1167, CS-1166 and outbound gate suites at 91 passed, exit 0.

THE POPULATION IS DERIVED, NEVER TYPED. The branches are read out of each
compiled pattern by ``tools/outbound_gate.py::credential_branches``, so a
branch added to a rule with no canary gets a red case of its own at
collection, and a branch removed leaves a canary naming a branch that no
longer exists.

EVERY ASSERTION BINDS TO A SCALAR FIRST. pytest's assertion rewriting renders
the asserted expression and every call inside it, so an ``assert reason in
f(canary)`` prints the canary on failure. Arm 4 forces every arm red in a
child run and counts canary values in what it printed.
"""

from __future__ import annotations

import importlib.util
import operator
import os
import re
import subprocess
import sys
from itertools import chain
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOUND_PATH = REPO_ROOT / "tools" / "outbound_gate.py"

#: Private to this file, so no other suite's patches can reach this copy.
OUTBOUND_MODULE_NAME = "clockspeed_outbound_gate_for_cs1172"

TIMEOUT = 300

#: CS-1301: the largest exit a process reports for itself; past it, the
#: number is a Windows status the child died with.
LAST_REPORTED_EXIT = 255

#: The acceptance's own floor: mutation on at least three rules with branches.
MIN_RULES_WITH_BRANCHES = 3


def load_outbound() -> ModuleType:
    """Load the outbound gate by path under a module name private to this file."""
    cached = sys.modules.get(OUTBOUND_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(OUTBOUND_MODULE_NAME, OUTBOUND_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[OUTBOUND_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


OUTBOUND = load_outbound()
GATE = OUTBOUND.load_precommit_gate()

#: Independent plants: each drops ONE branch from ONE rule by editing the
#: rule's SOURCE TEXT, never through the module's own narrowing code, so the
#: arm cannot share a blind spot with the thing it grades. The last field is
#: the branch label the row must name. The vendor-prefix label is assembled
#: from fragments for the same reason every canary is.
PLANTS: tuple[tuple[str, str, str, str], ...] = (
    ("AWS access key id", "(?:AKIA|ASIA)", "(?:AKIA)", "A(SIA)"),
    ("GitHub token", "(?:ghp|gho|ghu|ghs|ghr)", "(?:ghp|gho|ghu|ghs)", "gh[r]_"),
    (
        "Anthropic API or admin key (vendor prefix)",
        "(?:admin|api)",
        "(?:api)",
        "sk" + "-ant-a(dmin)",
    ),
    ("Slack token", "xox[abprs]", "xox[abpr]", "xox[s]-"),
    ("bearer token", "[Bb]earer", "Bearer", "[b]earer"),
    (
        "credential assigned a quoted literal of 16 or more characters",
        "|passwd",
        "",
        "(passwd)",
    ),
    (
        "credential assigned a bare high-entropy literal",
        "(?:key|token|secret)",
        "(?:key|token)",
        "(secret)",
    ),
)


def pin_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Remove every machine-derived capability, so only the canary rows vary."""
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-save-root"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv(OUTBOUND.ENV_OUTBOUND_EXCLUSIONS, raising=False)
    monkeypatch.setenv("USERNAME", "gatetestaccount")
    monkeypatch.setenv("USER", "gatetestaccount")


def credential_row(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[bool, str]:
    """Scan a clean payload and return the credential row as (measured, reason)."""
    pin_environment(monkeypatch, tmp_path)
    _, _, rows = OUTBOUND.scan("ordinary prose\n")
    matching = [row for row in rows if row.klass == OUTBOUND.CLASS_CREDENTIAL]
    count = len(matching)
    assert count == 1, "expected exactly one credential row, got %d" % count
    return bool(matching[0].measured), str(matching[0].reason)


def planted(reason: str, old: str, new: str) -> list[tuple[re.Pattern[str], str]]:
    """The rule list with ONE rule's source edited, asserting the edit landed."""
    rules: list[tuple[re.Pattern[str], str]] = []
    landed = 0
    for pattern, rule_reason in GATE.SECRET_PATTERNS:
        if rule_reason == reason and old in pattern.pattern:
            rules.append((re.compile(pattern.pattern.replace(old, new, 1), pattern.flags), reason))
            landed += 1
        else:
            rules.append((pattern, rule_reason))
    assert landed == 1, "the plant did not land on exactly one rule: " + reason
    return rules


# --------------------------------------------------------------------------
# Arm 1 - a narrowed rule reddens the row, naming the rule AND the branch
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("reason", "old", "new", "label"), PLANTS, ids=[p[3] for p in PLANTS])
def test_a_dropped_branch_reddens_the_row_by_rule_and_branch(
    reason: str,
    old: str,
    new: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Dropping one branch of one rule turns the row UNMEASURED and names both.

    The pristine row is read in the SAME test as the control, so a row that
    was already red cannot pass this arm by accident.
    """
    healthy, healthy_reason = credential_row(monkeypatch, tmp_path)
    assert healthy is True, "the pristine row is not MEASURED: " + healthy_reason

    monkeypatch.setattr(GATE, "SECRET_PATTERNS", planted(reason, old, new))
    measured, row_reason = credential_row(monkeypatch, tmp_path)
    assert measured is False, "a rule narrowed by one branch read MEASURED: " + label
    named_rule = reason in row_reason
    named_branch = label in row_reason
    assert named_rule, "the row did not name the narrowed rule: " + reason
    assert named_branch, "the row did not name the dropped branch: " + label


# --------------------------------------------------------------------------
# Arm 2 - every DERIVED branch has a canary that proves it
# --------------------------------------------------------------------------

#: Read at COLLECTION from the live rule list, so a branch added upstream is a
#: new red case here without anyone editing this file.


def derive_branches() -> list[tuple[str, str]]:
    """Every (reason, label) the module derives; an underivable rule adds none.

    Never raises at collection: an underivable rule is named by the gap
    function and reddens the control arm, and the vacuity arm below catches a
    population that collapsed.
    """
    branches: list[tuple[str, str]] = []
    for pattern, reason in GATE.SECRET_PATTERNS:
        try:
            derived = OUTBOUND.credential_branches(pattern)
        except OUTBOUND._PARSE_ERRORS:  # noqa: SLF001 - the module's own closed set
            continue
        branches.extend((reason, label) for label, _ in derived)
    return branches


BRANCHES = derive_branches()


def branch_gaps_for(reason: str, label: str) -> list[str]:
    """The gaps `credential_branch_gaps` names for exactly this branch."""
    head = reason + " / branch " + label + " ("
    return [gap for gap in OUTBOUND.credential_branch_gaps(GATE) if gap.startswith(head)]


def test_the_branch_population_is_not_vacuous() -> None:
    """Anti-vacuity: the parametrizations below must collect real branches."""
    rules_with_branches = len({reason for reason, _ in BRANCHES})
    total = len(BRANCHES)
    unique = len(set(BRANCHES))
    floor = MIN_RULES_WITH_BRANCHES
    assert rules_with_branches >= floor, "rules with branches: %d" % rules_with_branches
    assert total > len(GATE.SECRET_PATTERNS), "no more branches than rules: %d" % total
    assert unique == total, "two branches of one rule share a label"


@pytest.mark.parametrize(("reason", "label"), BRANCHES, ids=[b[1] for b in BRANCHES])
def test_every_branch_has_a_canary_that_proves_it(reason: str, label: str) -> None:
    """The branch's canary is flagged by its rule and NOT by the rule without it."""
    gaps = branch_gaps_for(reason, label)
    count = len(gaps)
    assert count == 0, "; ".join(gaps)


def test_the_tree_as_it_stands_has_no_branch_gap() -> None:
    """The control for every mutation below: pristine, nothing is named."""
    gaps = OUTBOUND.credential_branch_gaps(GATE)
    count = len(gaps)
    assert count == 0, "; ".join(gaps)


@pytest.mark.parametrize(("reason", "label"), BRANCHES, ids=[b[1] for b in BRANCHES])
def test_every_derived_narrowing_reddens_the_row_by_name(
    reason: str, label: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Replacing a rule with itself minus ONE branch names that rule and branch.

    Covers the declared equivalents too: dropping one leaves a canary filed
    under a branch the rule no longer has, which is named as such.
    """
    healthy, healthy_reason = credential_row(monkeypatch, tmp_path)
    assert healthy is True, "the pristine row is not MEASURED: " + healthy_reason

    rules = []
    for pattern, rule_reason in GATE.SECRET_PATTERNS:
        if rule_reason == reason:
            narrowed = dict(OUTBOUND.credential_branches(pattern))[label]
            rules.append((narrowed, rule_reason))
        else:
            rules.append((pattern, rule_reason))
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", rules)
    measured, row_reason = credential_row(monkeypatch, tmp_path)
    named = (reason + " / branch " + label) in row_reason
    assert measured is False, "a rule narrowed by one branch read MEASURED: " + label
    assert named, "the row did not name the rule and branch: " + label


# --------------------------------------------------------------------------
# Arm 3 - the table cannot drift from the rules it certifies
# --------------------------------------------------------------------------


def test_a_branch_added_upstream_with_no_canary_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """A new alternative in a rule is a gap by name, with no edit to this file."""
    reason = "AWS access key id"
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", planted(reason, "|ASIA)", "|ASIA|ABIA)"))
    gaps = OUTBOUND.credential_branch_gaps(GATE)
    expected = [reason + " / branch A(BIA) (no canary)"]
    matched = gaps == expected
    assert matched, "; ".join(gaps)


def test_every_table_entry_names_a_derived_branch() -> None:
    """No canary is filed under a branch or a rule the patterns do not have."""
    derived = set(BRANCHES)
    filed = {
        (reason, label)
        for reason, table in OUTBOUND.CREDENTIAL_BRANCH_CANARIES.items()
        for label in table
    }
    stale = sorted(label for _, label in filed - derived)
    missing = sorted(label for _, label in derived - filed)
    assert not stale, "canaries for no such branch: " + ", ".join(stale)
    assert not missing, "branches with no canary: " + ", ".join(missing)


def test_every_declared_equivalent_is_a_derived_branch() -> None:
    """An equivalence declaration for a branch that does not exist is drift."""
    derived = set(BRANCHES)
    stale = sorted(
        label
        for reason, label in OUTBOUND.CREDENTIAL_EQUIVALENT_BRANCHES
        if (reason, label) not in derived
    )
    assert not stale, "equivalences for no such branch: " + ", ".join(stale)


def test_a_false_equivalence_declaration_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """Declaring a PROVABLE branch equivalent is named, so it cannot hide one."""
    reason = "AWS access key id"
    widened = OUTBOUND.CREDENTIAL_EQUIVALENT_BRANCHES | {(reason, "A(SIA)")}
    monkeypatch.setattr(OUTBOUND, "CREDENTIAL_EQUIVALENT_BRANCHES", widened)
    gaps = OUTBOUND.credential_branch_gaps(GATE)
    expected = [reason + " / branch A(SIA) (declared equivalent, but its canary proves it)"]
    matched = gaps == expected
    assert matched, "; ".join(gaps)


def file_one_canary_twice(
    monkeypatch: pytest.MonkeyPatch, reason: str, source: str, target: str
) -> None:
    """File the canary of branch `source` under branch `target` too.

    CS-1175: a helper, so the canary tables never reach the test's frame,
    whose locals `--showlocals` renders when it fails. CS-1177: and no table is
    bound to a name HERE either, because a helper that raises has its locals
    rendered too - the new table is built in one expression and handed on.
    """
    monkeypatch.setattr(
        OUTBOUND,
        "CREDENTIAL_BRANCH_CANARIES",
        {
            **OUTBOUND.CREDENTIAL_BRANCH_CANARIES,
            reason: {
                **OUTBOUND.CREDENTIAL_BRANCH_CANARIES[reason],
                target: OUTBOUND.CREDENTIAL_BRANCH_CANARIES[reason][source],
            },
        },
    )


def test_a_canary_another_branch_matches_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """A canary the rule still flags with its branch removed proves nothing."""
    reason = "bearer token"
    file_one_canary_twice(monkeypatch, reason, "[B]earer", "[b]earer")
    gaps = OUTBOUND.credential_branch_gaps(GATE)
    expected = [reason + " / branch [b]earer (its canary is matched without it)"]
    matched = gaps == expected
    assert matched, "; ".join(gaps)


def test_an_underivable_parser_names_every_rule(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If the private parser API moves, every rule is named, never called measured."""

    class Moved:
        """A parser whose entry point is gone."""

        def parse(self, *_: object) -> object:
            """Raise as a moved private API would."""
            message = "parse moved"
            raise AttributeError(message)

    monkeypatch.setattr(OUTBOUND, "_RE_PARSER", Moved())
    gaps = OUTBOUND.credential_branch_gaps(GATE)
    suffix = " (its branches could not be derived)"
    expected = [reason + suffix for _, reason in GATE.SECRET_PATTERNS]
    matched = gaps == expected
    assert matched, "; ".join(gaps)
    measured, _ = credential_row(monkeypatch, tmp_path)
    assert measured is False, "an underivable branch population read MEASURED"


# --------------------------------------------------------------------------
# Arm 4 - no canary arm renders a canary value when it fails
# --------------------------------------------------------------------------

#: Loaded by the child run; forces every secret rule to match nothing, so
#: every canary arm goes red at once.
FORCER = """
import importlib.util, re, sys
from pathlib import Path

NAME = "clockspeed_precommit_gate_for_outbound_gate"


def pytest_configure(config):
    path = Path(%r) / "tools" / "precommit_gate.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = module
    spec.loader.exec_module(module)
    never = re.compile("(?!)")
    module.SECRET_PATTERNS[:] = [(never, reason) for _, reason in module.SECRET_PATTERNS]
"""

#: The positive control: an arm that DOES render a canary through assertion
#: rewriting, so a count of zero from the real arms is a measurement.
LEAKY = """
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs1172_leaky_outbound", Path(%r))
module = importlib.util.module_from_spec(spec)
sys.modules["cs1172_leaky_outbound"] = module
spec.loader.exec_module(module)


def absent(value):
    return value is None


def test_leaks():
    assert absent(module.CREDENTIAL_CANARIES["AWS access key id"])
"""


def every_canary() -> list[str]:
    """Every canary value either table carries.

    CS-1177: built in one expression, so no value and no table is ever bound
    to a name of this frame - a helper that raises has its locals rendered.
    """
    return [
        *OUTBOUND.CREDENTIAL_CANARIES.values(),
        *chain.from_iterable(
            map(operator.methodcaller("values"), OUTBOUND.CREDENTIAL_BRANCH_CANARIES.values())
        ),
    ]


def canaries_in(output: str) -> int:
    """How many canary values appear in `output`, counted in THIS frame.

    CS-1175: a helper, so the values are never a local of a test frame that
    `--showlocals` would render if the test failed. CS-1177: nor a local of a
    generator here - the count maps over the values and names none of them.
    """
    return sum(map(output.count, every_canary()))


def child_pytest(tmp_path: Path, args: list[str]) -> tuple[int, str]:
    """Run pytest in a child with `tmp_path` importable; return (code, output)."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    env["PYTHONPATH"] = str(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-vv", "-p", "no:cacheprovider", *args],
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    output = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    return proc.returncode, output


def control_pytest(tmp_path: Path, args: list[str]) -> tuple[int, str]:
    """The leaky control's child run, its collection cut at `tmp_path`.

    CS-1301: the control's only path lives under the temp root, on another
    drive from the repo the child runs in. pytest then finds no common
    ancestor, keeps the confcutdir at the repo, and walks EVERY ancestor of
    the temp path from the drive root down, listing and lstat'ing each
    sibling; one removed mid-walk by a concurrent run's temp cleanup made the
    control exit 2 under load. Not in `child_pytest`: the forced run's paths
    are in the repo, where this cut would walk the repo's drive instead.
    """
    return child_pytest(tmp_path, ["--confcutdir=%s" % tmp_path, *args])


def child_failure(code: int, output: str) -> str:
    """The child's exit and the error it raised, named by identifiers only.

    CS-1301: the error types its report printed and the frames they were
    raised in - never the report's text, where a path carries the home
    directory and an E line can carry a canary - and any canary value among
    those identifiers is redacted. An exit past 255 is a Windows status the
    child died with before it could report, so it is shown in hex too.
    Built in one expression, so no value is bound to a name of this frame
    (CS-1177).
    """
    return re.sub(
        "|".join(map(re.escape, every_canary())),
        "<redacted>",
        "exit %s; raised %s; in %s"
        % (
            str(code)
            if 0 <= code <= LAST_REPORTED_EXIT
            else "%d (0x%08X)" % (code, code & 0xFFFFFFFF),
            ", ".join(
                dict.fromkeys(
                    re.findall(
                        r"^E\s+((?:\w+\.)*\w*(?:Error|Exception|Exit|Interrupt))\b",
                        output,
                        re.MULTILINE,
                    )
                )
            )
            or "nothing",
            ", ".join(dict.fromkeys(re.findall(r":\d+: in (\w+)\s*$", output, re.MULTILINE)))
            or "no frame",
        ),
    )


#: CS-1301: loaded by a control child as a `-p` plugin. It removes a SIBLING
#: of the control's directory while pytest lists that directory's parent, the
#: way a concurrent run's temp cleanup does under load.
REAPER = """
from pathlib import Path

SIBLING = Path(%r)


def pytest_collect_directory(path, parent):
    if path == SIBLING:
        path.rmdir()
"""


def test_a_reaped_sibling_leaves_the_control_red_forced_red_output(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The leaky control fails on its canary even as a sibling vanishes.

    CS-1301: the control's collection never lists above its own directory,
    so a temp directory removed beside it cannot turn its exit 1 into 2. The
    name carries `forced_red_output`, so a forced child never recurses here.
    """
    sibling = tmp_path_factory.mktemp("cs1301_sibling")
    assert sibling.parent == tmp_path.parent, "the sibling is not beside the control"
    (tmp_path / "cs1301_reaper.py").write_text(REAPER % str(sibling), encoding="ascii")
    leaky = tmp_path / "cs1172_leaky_check.py"
    leaky.write_text(LEAKY % str(OUTBOUND_PATH), encoding="ascii")

    failure = child_failure(*control_pytest(tmp_path, ["-p", "cs1301_reaper", str(leaky)]))
    assert failure.startswith("exit 1;"), "the leaky control did not fail: " + failure
    assert sibling.is_dir(), "the control's collection listed above its own directory"


def test_forced_red_output_renders_no_canary(tmp_path: Path) -> None:
    """Every canary arm forced red at once prints no whole canary value.

    The control runs first in the same test: an arm that renders a canary
    through assertion rewriting IS found by the same count, so zero from the
    real arms is not a capture that cannot see.
    """
    (tmp_path / "cs1172_forcer.py").write_text(FORCER % str(REPO_ROOT), encoding="ascii")
    leaky = tmp_path / "cs1172_leaky_check.py"
    leaky.write_text(LEAKY % str(OUTBOUND_PATH), encoding="ascii")

    code, output = control_pytest(tmp_path, [str(leaky)])
    control = canaries_in(output)
    assert code == 1, "the leaky control did not fail: " + child_failure(code, output)
    assert control > 0, "the capture cannot see a rendered canary"

    code, output = child_pytest(
        tmp_path,
        [
            "-p",
            "cs1172_forcer",
            "-k",
            "not forced_red_output",
            "tests/test_cs1167_credential_canary_coverage.py",
            "tests/test_cs1172_branch_canaries.py",
        ],
    )
    failed = re.search(r"(\d+) failed", output)
    failures = int(failed.group(1)) if failed else 0
    leaked = canaries_in(output)
    assert code == 1, "the forced run did not fail: " + child_failure(code, output)
    assert failures >= len(GATE.SECRET_PATTERNS), "too few arms went red: %d" % failures
    assert leaked == 0, "the forced-red output rendered %d canary value(s)" % leaked
