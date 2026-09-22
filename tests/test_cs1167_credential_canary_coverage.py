"""CS-1167 - the credential coverage row is earned PER RULE, not per class.

THE DEFECT. ``tools/outbound_gate.py`` proved the credential class live with
ONE canary of one vendor's shape, so the coverage row read MEASURED while any
rule other than the one that canary was shaped for could be deleted, inverted
or narrowed. A pooled guard: the class green on the strength of its strongest
member.

THE POPULATION IS DERIVED, NEVER TYPED. Every arm below iterates the commit
gate's own ``SECRET_PATTERNS``, so a rule added there with no canary gets a
red case of its own at collection without anyone editing this file.

EVERY CANARY IS FRAGMENT-ASSEMBLED in ``tools/outbound_gate.py``. This file
holds none of them; it reads them back from the module under test.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOUND_PATH = REPO_ROOT / "tools" / "outbound_gate.py"

#: Private to this file, so no other suite's patches can reach this copy.
OUTBOUND_MODULE_NAME = "clockspeed_outbound_gate_for_cs1167"

TIMEOUT = 180

#: Matches nothing anywhere - an empty negative lookahead fails at every
#: position. A VALID pattern, so a weakened rule is not an exception test.
NEVER_MATCHES = re.compile("(?!)")

#: The reason a planted rule carries. It is matched by no canary.
FAKE_REASON = "cs1167 planted rule with no canary"


def load_outbound() -> ModuleType:
    """Load the outbound gate by path under a module name private to this file."""
    cached = sys.modules.get(OUTBOUND_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(OUTBOUND_MODULE_NAME, OUTBOUND_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module: dataclasses under postponed annotations
    # resolve through sys.modules.
    sys.modules[OUTBOUND_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


OUTBOUND = load_outbound()
GATE = OUTBOUND.load_precommit_gate()
#: Read at COLLECTION, so the parametrization below is the live rule list.
RULE_REASONS = [reason for _, reason in GATE.SECRET_PATTERNS]


def pin_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Remove every machine-derived capability, so only the canary rows vary."""
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-save-root"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv(OUTBOUND.ENV_OUTBOUND_EXCLUSIONS, raising=False)
    monkeypatch.setenv("USERNAME", "gatetestaccount")
    monkeypatch.setenv("USER", "gatetestaccount")


def credential_row(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> object:
    """Scan a clean payload and return the credential coverage row."""
    pin_environment(monkeypatch, tmp_path)
    _, _, rows = OUTBOUND.scan("ordinary prose\n")
    matching = [row for row in rows if row.klass == OUTBOUND.CLASS_CREDENTIAL]
    assert len(matching) == 1, "expected exactly one credential row"
    return matching[0]


def secret_reasons(text: str) -> list[str]:
    """Every SECRET reason the commit gate's own pipeline reports for `text`."""
    report = GATE.Report()
    GATE.check_secrets("cs1167", text, report)
    return [diag.reason for diag in report.diagnostics if diag.code == "SECRET"]


# --------------------------------------------------------------------------
# Arm 1 - every rule has a canary it matches, derived from the rule list
# --------------------------------------------------------------------------


def test_the_rule_list_is_non_empty() -> None:
    """Anti-vacuity: an empty parametrization below would pass by collecting nothing."""
    assert len(RULE_REASONS) > 1, "the rule list read back empty or singular"
    assert len(set(RULE_REASONS)) == len(RULE_REASONS), "two rules share one reason"


@pytest.mark.parametrize("reason", RULE_REASONS)
def test_every_secret_rule_has_a_live_canary(reason: str) -> None:
    """Each rule in SECRET_PATTERNS has a canary that rule itself flags.

    Graded through ``check_secrets``, so the placeholder allowance is applied
    exactly as the commit gate applies it: a canary suppressed by
    ``PLACEHOLDER_RE`` would not report its reason and fails here.
    """
    canary = OUTBOUND.CREDENTIAL_CANARIES.get(reason)
    assert canary is not None, "no canary for rule: " + reason
    assert reason in secret_reasons(canary), "the canary for this rule is not flagged: " + reason
    assert reason not in OUTBOUND.credential_canary_gaps(GATE), "the gate names it a gap: " + reason


def test_no_canary_names_a_rule_that_does_not_exist() -> None:
    """A stale canary is a table that has drifted from the list it certifies."""
    stale = sorted(set(OUTBOUND.CREDENTIAL_CANARIES) - set(RULE_REASONS))
    assert stale == [], "canaries for rules not in SECRET_PATTERNS: " + ", ".join(stale)


# --------------------------------------------------------------------------
# Arm 2 - mutation in both directions, each with a same-run control
# --------------------------------------------------------------------------


def test_control_the_tree_as_it_stands_is_measured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The control: on the unmodified tree the credential row reads MEASURED."""
    row = credential_row(monkeypatch, tmp_path)
    assert row.measured is True, row.reason  # type: ignore[attr-defined]
    assert row.reason == "canary matched"  # type: ignore[attr-defined]


@pytest.mark.parametrize("reason", RULE_REASONS)
def test_a_weakened_rule_reddens_the_row_by_name(
    reason: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Weakening ANY one rule turns the row UNMEASURED and names that rule.

    This is the arm that failed first: under the single canary, weakening any
    rule but the one it was shaped for left the row MEASURED.
    """
    healthy = credential_row(monkeypatch, tmp_path)
    assert healthy.measured is True  # type: ignore[attr-defined]

    weakened = [
        (NEVER_MATCHES if rule_reason == reason else pattern, rule_reason)
        for pattern, rule_reason in GATE.SECRET_PATTERNS
    ]
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", weakened)
    row = credential_row(monkeypatch, tmp_path)
    assert row.measured is False, "a rule that catches nothing read MEASURED: " + reason  # type: ignore[attr-defined]
    assert reason in row.reason  # type: ignore[attr-defined]


def test_a_removed_canary_reddens_the_row_by_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Removing one canary names exactly the rule left uncovered."""
    victim = RULE_REASONS[-1]
    healthy = credential_row(monkeypatch, tmp_path)
    assert healthy.measured is True  # type: ignore[attr-defined]

    monkeypatch.delitem(OUTBOUND.CREDENTIAL_CANARIES, victim)
    assert OUTBOUND.credential_canary_gaps(GATE) == [victim]
    row = credential_row(monkeypatch, tmp_path)
    assert row.measured is False  # type: ignore[attr-defined]
    assert victim in row.reason  # type: ignore[attr-defined]
    assert OUTBOUND.verdict([], [row]) == OUTBOUND.EXIT_UNMEASURED


def test_an_added_rule_with_no_canary_reddens(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A rule added to the list with no canary is red without editing any test."""
    healthy = credential_row(monkeypatch, tmp_path)
    assert healthy.measured is True  # type: ignore[attr-defined]

    planted = [*GATE.SECRET_PATTERNS, (re.compile("cs1167planted"), FAKE_REASON)]
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", planted)
    assert OUTBOUND.credential_canary_gaps(GATE) == [FAKE_REASON]
    row = credential_row(monkeypatch, tmp_path)
    assert row.measured is False  # type: ignore[attr-defined]
    assert FAKE_REASON in row.reason  # type: ignore[attr-defined]


def test_a_placeholder_suppressed_canary_is_not_live(monkeypatch: pytest.MonkeyPatch) -> None:
    """A canary the placeholder allowance swallows does not count as live."""
    victim = RULE_REASONS[0]
    monkeypatch.setattr(GATE, "PLACEHOLDER_RE", re.compile(".", re.DOTALL))
    gaps = OUTBOUND.credential_canary_gaps(GATE)
    assert victim in gaps
    assert gaps == RULE_REASONS, "an all-suppressing allowance must leave every rule uncovered"


# --------------------------------------------------------------------------
# Arm 3 - the gate still blocks a real message carrying each canary
# --------------------------------------------------------------------------


@pytest.mark.parametrize("reason", RULE_REASONS)
def test_scan_refuses_each_canary_in_a_message(
    reason: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Each canary, inside ordinary prose, yields a credential refusal."""
    pin_environment(monkeypatch, tmp_path)
    message = "Status report.\nsee " + OUTBOUND.CREDENTIAL_CANARIES[reason] + " here\n"
    refusals, _, _ = OUTBOUND.scan(message)
    lines = {f.line for f in refusals if f.klass == OUTBOUND.CLASS_CREDENTIAL}
    assert lines == {2}, "the message carrying this canary was not refused: " + reason


def test_cli_refuses_a_message_carrying_every_canary(tmp_path: Path) -> None:
    """End to end: the CLI refuses, finds one credential per line, echoes none."""
    canaries = [OUTBOUND.CREDENTIAL_CANARIES[reason] for reason in RULE_REASONS]
    payload = "".join("line " + canary + "\n" for canary in canaries)
    env = dict(os.environ)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    env.pop(OUTBOUND.ENV_OUTBOUND_EXCLUSIONS, None)
    proc = subprocess.run(
        [sys.executable, str(OUTBOUND_PATH)],
        input=payload.encode("ascii"),
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    both = proc.stdout.decode("ascii") + proc.stderr.decode("ascii")
    assert proc.returncode == OUTBOUND.EXIT_REFUSED, "exit %d" % proc.returncode
    refused = {
        int(match.group(1))
        for match in re.finditer(r"<pii:credential>  line (\d+) col \d+", proc.stderr.decode())
    }
    assert refused == set(range(1, len(canaries) + 1)), "a canary line was not refused"
    leaked = [canary for canary in canaries if canary in both]
    assert leaked == [], "the refusal echoed %d canary value(s)" % len(leaked)
