"""CS-1166 - a secret rule anchored on the literal vendor prefix of the key family.

THE DEFECT. ``SECRET_PATTERNS`` in ``tools/precommit_gate.py`` carried no rule
anchored on the vendor prefix of the Anthropic key families, so a bare admin
-family token, a bare api-family token, a dict-repr line carrying one, the
vendor-named environment assignment and its shell-export spelling ALL scored
clean. One list feeds four consumers - the commit gate, the PreToolUse gate,
the outbound gate and the repo-wide sweep - so all four were blind at once.

FIVE ARMS, TWO OF THEM AGAINST VACUITY.

1. The catch arm, which failed first on all five spellings before the rule.
2. The false-positive arm, green BEFORE and AFTER the rule by design.
3. The placeholder arm, measured twice: as the allowlist stands, and with
   ``PLACEHOLDER_RE`` patched to never match, so it cannot pass for the wrong
   reason.
4. The neighbour arm, one positive control PER EXISTING RULE rather than a
   count, so a silently broken neighbour cannot hide behind the total.
5. The consumer arms, driving four consumers end to end as subprocesses or
   through their own entry points.

EVERY TOKEN HERE IS FRAGMENT-ASSEMBLED and synthetic. No line of this file
spells a whole credential, so the gate that checks this file on commit finds
nothing in its source while the joined values match the rules under test.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests import secret_sweep_guard as sweep

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "tools" / "precommit_gate.py"
PRETOOLUSE_PATH = REPO_ROOT / "tools" / "pretooluse_gate.py"
OUTBOUND_PATH = REPO_ROOT / "tools" / "outbound_gate.py"

#: Distinct from every other loader's module name, so no two suites can patch
#: each other's copy of the gate.
GATE_MODULE_NAME = "clockspeed_gate_for_cs1166"

TIMEOUT = 120

#: The PreToolUse gate's deny status, as ``tools/pretooluse_gate.py`` defines it.
PRETOOLUSE_DENY = 2

#: The reason string the new rule reports. Read back from the gate, never
#: restated as a pattern.
NEW_REASON = "Anthropic API or admin key (vendor prefix)"

# Fragments. The vendor prefix is split so no line here carries it whole.
_PFX = "sk" + "-" + "ant" + "-"
_ADMIN = "admin" + "01" + "-"
_API = "api" + "03" + "-"
#: A synthetic body: no placeholder word, digits and case mixed, 48 chars.
_BODY = "Q7vR2mZ9" * 6

ADMIN_TOKEN = _PFX + _ADMIN + _BODY
API_TOKEN = _PFX + _API + _BODY
_ENV_NAME = "ANTHROPIC" + "_API_" + "KEY"


def load_gate() -> ModuleType:
    """Load the frozen gate by path under a module name private to this file."""
    spec = importlib.util.spec_from_file_location(GATE_MODULE_NAME, GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[GATE_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> ModuleType:
    """The gate module, loaded once for this file."""
    return load_gate()


def reasons(gate: ModuleType, text: str) -> list[str]:
    """Every SECRET reason ``check_secrets`` reports for ``text``."""
    report = gate.Report()
    gate.check_secrets("cs1166", text, report)
    return [diag.reason for diag in report.diagnostics if diag.code == "SECRET"]


CATCH_SPELLINGS = {
    "bare-admin": ADMIN_TOKEN,
    "bare-api": API_TOKEN,
    "dict-repr": repr({"api" + "_key": API_TOKEN}),
    "env-assign": _ENV_NAME + "=" + API_TOKEN,
    "env-export": "export " + _ENV_NAME + "=" + ADMIN_TOKEN,
    # After a word character, where a leading word boundary would not hold.
    "url-encoded": "api" + "_key%3D" + API_TOKEN,
    "json-escaped-newline": "line one" + chr(92) + "n" + ADMIN_TOKEN,
    "glued-to-name": "KEY" + API_TOKEN,
}


# --------------------------------------------------------------------------
# Arm 1 - catch
# --------------------------------------------------------------------------


@pytest.mark.parametrize("spelling", sorted(CATCH_SPELLINGS))
def test_the_vendor_prefix_rule_catches_every_spelling(gate: ModuleType, spelling: str) -> None:
    """Each of the five spellings is caught BY THE NEW RULE, not incidentally.

    This arm failed on the first five before the rule existed - the gate
    returned no finding at all for any of them. The last three failed against
    the first version of the rule, whose leading word boundary could not hold
    after a word character: a URL-encoded assignment, a JSON-escaped newline
    and a token glued to a name.
    """
    found = reasons(gate, CATCH_SPELLINGS[spelling])
    assert NEW_REASON in found, spelling + " was not caught by the vendor-prefix rule"


def test_the_new_rule_has_zero_capturing_groups(gate: ModuleType) -> None:
    """The new rule carries ZERO capturing groups.

    ``check_secrets`` takes the LAST group; a capture would narrow the window
    ``PLACEHOLDER_RE`` inspects and silently change suppression.
    """
    rules = [pattern for pattern, reason in gate.SECRET_PATTERNS if reason == NEW_REASON]
    assert len(rules) == 1, "exactly one rule carries the vendor-prefix reason"
    assert rules[0].groups == 0


# --------------------------------------------------------------------------
# Arm 2 - false positives
# --------------------------------------------------------------------------

FALSE_POSITIVE_LINES = [
    "the " + _PFX + " prefix names the family; prose about it is not a key",
    _PFX + _API + "Q7vR2mZ9",
    _PFX + "other" + "01" + "-" + _BODY,
    "KEY: mProductionBoostPowerConsumptionExponent",
]


@pytest.mark.parametrize("index", range(len(FALSE_POSITIVE_LINES)))
def test_near_miss_lines_score_clean(gate: ModuleType, index: int) -> None:
    """This arm is green BEFORE and AFTER the new rule, by design.

    It is NOT evidence the rule works - arm 1 is. It exists so a rule widened
    to prose, to a short body, to a different family or to the recorded
    game-data identifier that once blocked a real commit goes red here rather
    than on an author's commit. A prefix embedded after a word character is
    deliberately NOT here: the rule carries no leading boundary, and arm 1
    requires that spelling to be caught.
    """
    assert reasons(gate, FALSE_POSITIVE_LINES[index]) == []


# --------------------------------------------------------------------------
# Arm 3 - placeholder, measured twice
# --------------------------------------------------------------------------

PLACEHOLDER_TOKEN = _PFX + _API + _BODY + "EXAM" + "PLE"


def test_a_placeholder_bodied_token_is_suppressed_as_the_allowlist_stands(
    gate: ModuleType,
) -> None:
    """Measurement one: the documented-example word suppresses the finding.

    The word ENDS the body. CS-1169 bounded the allowlist so a member forgives
    only at an edge or between non-alphanumerics; the earlier token carried it
    as a mid-body infix, which the bounded allowlist correctly refuses.
    """
    assert NEW_REASON not in reasons(gate, PLACEHOLDER_TOKEN)


def test_the_placeholder_token_is_caught_once_the_allowlist_is_disabled(
    gate: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Measurement two: the allowlist disabled, the same token is caught.

    With ``PLACEHOLDER_RE`` never matching, the rule reports the token - so
    measurement one passed BECAUSE of the allowlist and not because the rule
    was blind to the token. The SAME edge-anchored token as measurement one,
    so the pair stays non-vacuous across the CS-1169 bound.
    """
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", re.compile(r"(?!)"))
    assert NEW_REASON in reasons(gate, PLACEHOLDER_TOKEN)


# --------------------------------------------------------------------------
# Arm 4 - one positive control per existing rule
# --------------------------------------------------------------------------

_Q = '"'
NEIGHBOUR_CONTROLS: dict[str, tuple[str, ...]] = {
    "PEM private key block": ("-----BEGIN " + "RSA PRIVATE " + "KEY-----",),
    "PuTTY private key file": ("PuTTY-User-" + "Key-File-" + "2",),
    "AWS access key id": ("AKIA" + ("Q7" * 8),),
    "GitHub token": ("ghp" + "_" + ("Q7vR" * 6),),
    "GitHub fine-grained personal access token": ("github" + "_pat_" + ("Q7vR" * 6),),
    "Slack token": ("xox" + "b-" + ("Q7vR" * 4),),
    "Google API key": ("AIza" + ("Q7vR2mZ" * 5),),
    "bearer token": ("Bea" + "rer " + ("Q7vR" * 6),),
    "credential assigned a quoted literal of 16 or more characters": (
        "pass" + "word = " + _Q + ("Q7vR" * 5) + _Q,
    ),
    # Two controls: the hex branch, then the base64-shaped branch.
    "credential assigned a bare high-entropy literal": (
        "session" + "_key=" + ("a1b2" * 10),
        "session" + "_key=" + ("Q7vR2mZ9" * 6),
    ),
}


def test_every_existing_rule_has_a_named_control(gate: ModuleType) -> None:
    """The control table names exactly the rules other than the new one."""
    existing = {reason for _, reason in gate.SECRET_PATTERNS if reason != NEW_REASON}
    assert existing == set(NEIGHBOUR_CONTROLS)


NEIGHBOUR_CASES = [
    (reason, index)
    for reason in sorted(NEIGHBOUR_CONTROLS)
    for index in range(len(NEIGHBOUR_CONTROLS[reason]))
]


@pytest.mark.parametrize(("reason", "index"), NEIGHBOUR_CASES)
def test_each_existing_rule_still_fires_on_its_own_control(
    gate: ModuleType, reason: str, index: int
) -> None:
    """Per rule, not per count: the named rule itself must report its control.

    The high-entropy rule has two branches, hex and base64-shaped, and each
    carries its own control, so one branch cannot stay green for the other.
    """
    assert reason in reasons(gate, NEIGHBOUR_CONTROLS[reason][index])


# --------------------------------------------------------------------------
# Arm 5 - consumers, end to end
# --------------------------------------------------------------------------


def _run(argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    """Run one consumer as a subprocess, capturing its exit code directly."""
    return subprocess.run(
        [sys.executable, *argv],
        input=stdin,
        capture_output=True,
        cwd=str(REPO_ROOT),
        timeout=TIMEOUT,
        check=False,
    )


def test_the_commit_gate_stdin_mode_blocks_the_token() -> None:
    """Commit gate, text-stdin call site: exit 1 and the new rule is named."""
    proc = _run([str(GATE_PATH), "--text-stdin"], (API_TOKEN + "\n").encode("ascii"))
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    assert proc.returncode == 1
    assert NEW_REASON in output
    assert _BODY not in output, "a finding must never echo the matched value"


def test_the_commit_gate_files_mode_blocks_the_token(tmp_path: Path) -> None:
    """Commit gate, file-content call site: exit 1 and the new rule is named."""
    planted = tmp_path / "cs1166_planted.txt"
    planted.write_bytes(("export " + _ENV_NAME + "=" + ADMIN_TOKEN + "\n").encode("ascii"))
    proc = _run([str(GATE_PATH), "--files", str(planted)], b"")
    output = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    assert proc.returncode == 1
    assert NEW_REASON in output


def test_the_pretooluse_gate_denies_the_tool_call() -> None:
    """PreToolUse gate: a tool call carrying the token is DENIED with exit 2."""
    envelope = {"tool_name": "Bash", "tool_input": {"command": "echo " + API_TOKEN}}
    proc = _run([str(PRETOOLUSE_PATH)], json.dumps(envelope).encode("ascii"))
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "can't open file" not in stderr
    assert proc.returncode == PRETOOLUSE_DENY
    assert NEW_REASON in stderr


def test_the_outbound_gate_refuses_the_payload(tmp_path: Path) -> None:
    """Outbound gate: the payload is REFUSED and attributed to the credential class."""
    payload = tmp_path / "cs1166_outbound.txt"
    payload.write_bytes(("note body\n" + repr({"k": ADMIN_TOKEN}) + "\n").encode("ascii"))
    proc = _run([str(OUTBOUND_PATH), "--file", str(payload)], b"")
    stderr = proc.stderr.decode("utf-8", "replace")
    assert proc.returncode == 1
    assert "<pii:credential>  line 2" in stderr


def test_the_repo_wide_sweep_reports_the_token(tmp_path: Path) -> None:
    """Repo-wide sweep: the planted file yields a finding naming the new rule."""
    (tmp_path / "cs1166_swept.md").write_bytes((API_TOKEN + "\n").encode("ascii"))
    findings = sweep.sweep_paths(["cs1166_swept.md"], tmp_path)
    assert any(NEW_REASON in finding for finding in findings)
