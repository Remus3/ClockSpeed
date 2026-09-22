"""CS-1169 - the bounds of the placeholder allowlist, graded in both directions.

THE DEFECT. ``check_secrets`` in ``tools/precommit_gate.py`` matches a rule
and then asks ``PLACEHOLDER_RE`` whether the offending literal is an obvious
placeholder. The allowlist matched on SUBSTRINGS, so a real credential whose
body merely carried a member as a mid-body infix passed every rule in
``SECRET_PATTERNS``. The allowlist sits downstream of all eleven rules, so it
was a switch able to turn any of them off.

THE CONTRACT. A member forgives a candidate only where it is the whole body,
bounds the body at its start or end, or is delimited on both sides by a
non-alphanumeric character. A member embedded inside an alphanumeric run
forgives nothing.

FIVE ARMS.

1. Forgiveness: the two censused documented shapes stay forgiven. Green
   BEFORE and AFTER the repair by design; each carries a control.
2. Refusal: per rule and per member spelling its charset admits, a mid-body
   infix is REFUSED. Measured TWICE - as shipped, and with ``PLACEHOLDER_RE``
   patched to never match - so a pass because the rule never fired is
   distinguishable from a pass because the allowlist declined.
3. Boundary: an edge-anchored member stays forgiven and the same member one
   alphanumeric character inside the edge is refused, pinned from both sides.
4. Enumeration: the membership lives in ONE place, the compiled pattern is
   derived from it alone, and this file's spelling table must move with it.
5. Neighbour: a positive control per existing rule.

EVERY TOKEN HERE IS FRAGMENT-ASSEMBLED and synthetic. No line of this file
spells a whole credential, so the gate that checks this file on commit finds
nothing in its source while the joined values match the rules under test.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "tools" / "precommit_gate.py"

#: Distinct from every other loader's module name, so no two suites can patch
#: each other's copy of the gate.
GATE_MODULE_NAME = "clockspeed_gate_for_cs1169"

#: A pattern that never matches, standing in for a disabled allowlist.
NEVER = re.compile(r"(?!)")


def load_gate() -> ModuleType:
    """Load the frozen gate by path under a module name private to this file."""
    spec = importlib.util.spec_from_file_location(GATE_MODULE_NAME, GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[GATE_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


#: Loaded at import because the refusal cases are derived from the rules.
GATE = load_gate()


@pytest.fixture
def gate() -> ModuleType:
    """The gate module shared by every arm in this file."""
    return GATE


def reasons(gate: ModuleType, text: str) -> list[str]:
    """Every SECRET reason ``check_secrets`` reports for ``text``."""
    report = gate.Report()
    gate.check_secrets("cs1169", text, report)
    return [diag.reason for diag in report.diagnostics if diag.code == "SECRET"]


# --------------------------------------------------------------------------
# Fragments and the member spelling table
# --------------------------------------------------------------------------

_Q = '"'
_PAD = "Q7vR2mZ9" * 8
_PAD_UP = "Q7M2" * 8
_PW = "pass" + "word = "

#: Concrete spellings of every member, keyed by the member exactly as the
#: gate enumerates it. Arm 4 requires the keys to equal the enumeration, so a
#: member added or removed in the gate cannot go ungraded here.
SPELLINGS: dict[str, tuple[str, ...]] = {
    "CHANGE_?ME": ("CHANGE" + "ME", "CHANGE" + "_ME", "change" + "me"),
    "XXXX": ("XX" + "XX", "xx" + "xx"),
    "EXAMPLE": ("EXAM" + "PLE", "exam" + "ple"),
    "SAMPLE": ("SAM" + "PLE", "sam" + "ple"),
    "DUMMY": ("DUM" + "MY", "dum" + "my"),
    "REDACT": ("RED" + "ACT", "red" + "act"),
    "PLACEHOLDER": ("PLACE" + "HOLDER", "place" + "holder"),
    "NOT_?A_?SECRET": ("NOTA" + "SECRET", "NOT_A" + "_SECRET", "not_a" + "_secret"),
    "TODO": ("TO" + "DO", "to" + "do"),
    "YOUR[-_]": ("YOUR" + "-", "YOUR" + "_", "your" + "_"),
    "<": ("<",),
    r"\{\{": ("{" + "{",),
}


def _aws(inner: str) -> str:
    """An AWS-shaped token whose 16-character body carries ``inner``."""
    return "AK" + "IA" + "Q" + inner + _PAD_UP[: 15 - len(inner)]


def _google(inner: str) -> str:
    """A Google-shaped token whose 35-character body carries ``inner``."""
    return "AI" + "za" + "Q7" + inner + _PAD[: 33 - len(inner)]


def _pem(inner: str) -> str:
    """A PEM header whose label carries ``inner`` inside an alphanumeric run."""
    return "-----BEGIN " + "R" + inner + "S PRIVATE " + "KEY-----"


#: Per rule, a builder placing a spelling as a MID-BODY infix: an alphanumeric
#: character on both sides and never at an edge of the candidate.
INFIX_BUILDERS = {
    "PEM private key block": _pem,
    "AWS access key id": _aws,
    "GitHub token": lambda s: "ghp" + "_Q7" + s + _PAD[:24],
    "GitHub fine-grained personal access token": lambda s: "github" + "_pat_Q7" + s + _PAD[:24],
    "Slack token": lambda s: "xox" + "b-Q7" + s + _PAD[:16],
    "Google API key": _google,
    "bearer token": lambda s: "Bea" + "rer Q7" + s + _PAD[:24],
    "credential assigned a quoted literal of 16 or more characters": (
        lambda s: _PW + _Q + "Q7" + s + _PAD[:20] + _Q
    ),
    "credential assigned a bare high-entropy literal": (
        lambda s: "session" + "_key=" + "Q7" + s + _PAD[:44]
    ),
    "Anthropic API or admin key (vendor prefix)": (
        lambda s: "sk" + "-ant-" + "api" + "03-Q7" + s + _PAD[:24]
    ),
}


def _admitted(reason: str, spelling: str) -> bool:
    """True when the rule's own pattern captures the spelling in its candidate.

    Decided from the rule itself, never from ``check_secrets``, so which cases
    the refusal arm grades cannot depend on the allowlist under test.
    """
    line = INFIX_BUILDERS[reason](spelling)
    for pattern, rule_reason in GATE.SECRET_PATTERNS:
        if rule_reason != reason:
            continue
        for match in pattern.finditer(line):
            if spelling in match.group(match.lastindex or 0):
                return True
    return False


REFUSAL_CASES = [
    (reason, member, spelling)
    for reason in sorted(INFIX_BUILDERS)
    for member in sorted(SPELLINGS)
    for spelling in SPELLINGS[member]
    if _admitted(reason, spelling)
]

#: Admitted cases per rule. An anti-narrowing control: a builder that silently
#: stops producing a matching token drops its rule's count and goes red here.
EXPECTED_ADMITTED = {
    "PEM private key block": 9,
    "AWS access key id": 9,
    "GitHub token": 17,
    "GitHub fine-grained personal access token": 22,
    "Slack token": 18,
    "Google API key": 23,
    "bearer token": 23,
    "credential assigned a quoted literal of 16 or more characters": 25,
    "credential assigned a bare high-entropy literal": 17,
    "Anthropic API or admin key (vendor prefix)": 23,
}


# --------------------------------------------------------------------------
# Arm 1 - forgiveness of the two censused documented shapes
# --------------------------------------------------------------------------

FORGIVEN_SITES = {
    # The canonical documented AWS example key: the member is the TRAILING run.
    "aws-documented-example": ("AK" + "IA" + "IOSFODNN7" + "EXAM" + "PLE", "AWS access key id"),
    # The whole-body change-me literal in the gate's own suite.
    "changeme-whole-body": (
        "api" + "_key = " + _Q + "CHANGE" + "ME_" + "CHANGE" + "ME" + _Q,
        "credential assigned a quoted literal of 16 or more characters",
    ),
}


@pytest.mark.parametrize("site", sorted(FORGIVEN_SITES))
def test_a_documented_shape_stays_forgiven(gate: ModuleType, site: str) -> None:
    """This arm is green BEFORE and AFTER the repair, by design.

    It is not evidence the repair works - arms 2 and 3 are. It exists so a
    narrowing that reddens a documented example goes red here first.
    """
    assert reasons(gate, FORGIVEN_SITES[site][0]) == []


@pytest.mark.parametrize("site", sorted(FORGIVEN_SITES))
def test_a_documented_shape_is_caught_once_the_allowlist_is_disabled(
    gate: ModuleType, monkeypatch: pytest.MonkeyPatch, site: str
) -> None:
    """The control: the forgiveness above is the allowlist's, not a blind rule."""
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    text, reason = FORGIVEN_SITES[site]
    assert reason in reasons(gate, text)


# --------------------------------------------------------------------------
# Arm 2 - a mid-body infix is refused, measured twice
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("reason", "member", "spelling"), REFUSAL_CASES)
def test_a_mid_body_member_is_refused_as_shipped(
    gate: ModuleType, reason: str, member: str, spelling: str
) -> None:
    """Measurement one: the rule reports a token carrying a member as an infix.

    Red before the repair on every case - the substring allowlist forgave it.
    """
    found = reasons(gate, INFIX_BUILDERS[reason](spelling))
    assert reason in found, member + " as an infix neutered the rule"


@pytest.mark.parametrize(("reason", "member", "spelling"), REFUSAL_CASES)
def test_a_mid_body_member_is_caught_with_the_allowlist_disabled(
    gate: ModuleType, monkeypatch: pytest.MonkeyPatch, reason: str, member: str, spelling: str
) -> None:
    """Measurement two: with the allowlist disabled, the same token is caught.

    So measurement one cannot pass because the rule never fired.
    """
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    assert reason in reasons(gate, INFIX_BUILDERS[reason](spelling)), member


def test_every_rule_admits_its_expected_number_of_infix_cases() -> None:
    """Per rule, the graded population is pinned so it cannot silently narrow."""
    counts = dict.fromkeys(INFIX_BUILDERS, 0)
    for reason, _, _ in REFUSAL_CASES:
        counts[reason] += 1
    assert counts == EXPECTED_ADMITTED


def test_every_member_is_graded_by_at_least_one_rule() -> None:
    """No member escapes the refusal arm for want of an admitting charset."""
    graded = {member for _, member, _ in REFUSAL_CASES}
    assert graded == set(SPELLINGS)


# --------------------------------------------------------------------------
# Arm 3 - the anchoring, pinned from both sides
# --------------------------------------------------------------------------

_QUOTED = "credential assigned a quoted literal of 16 or more characters"


def _quoted(body: str) -> str:
    """A quoted-assignment line; this rule's charset admits every member."""
    return _PW + _Q + body + _Q


BOUNDARY_CASES = [
    (member, spelling) for member in sorted(SPELLINGS) for spelling in SPELLINGS[member]
]

FORGIVEN_SHAPES = {
    "start": lambda s: _quoted(s + _PAD[:20]),
    "end": lambda s: _quoted(_PAD[:20] + s),
    "delimited": lambda s: _quoted(_PAD[:10] + "-" + s + "-" + _PAD[:10]),
    "whole": lambda s: _quoted(s * (16 // len(s) + 1)),
}

REFUSED_SHAPES = {
    "one-inside-start": lambda s: _quoted("Q" + s + _PAD[:20]),
    "one-inside-end": lambda s: _quoted(_PAD[:20] + s + "Q"),
}


@pytest.mark.parametrize("shape", sorted(FORGIVEN_SHAPES))
@pytest.mark.parametrize(("member", "spelling"), BOUNDARY_CASES)
def test_an_edge_anchored_or_delimited_member_is_forgiven(
    gate: ModuleType, monkeypatch: pytest.MonkeyPatch, member: str, spelling: str, shape: str
) -> None:
    """Green before and after: the contract keeps forgiving these shapes.

    Measured twice - the disabled-allowlist half proves the rule fires, so the
    forgiveness is the allowlist's and not a blind rule's.
    """
    line = FORGIVEN_SHAPES[shape](spelling)
    assert _QUOTED not in reasons(gate, line), member + " at " + shape
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    assert _QUOTED in reasons(gate, line), member + " control at " + shape


@pytest.mark.parametrize("shape", sorted(REFUSED_SHAPES))
@pytest.mark.parametrize(("member", "spelling"), BOUNDARY_CASES)
def test_a_member_one_character_inside_the_edge_is_refused(
    gate: ModuleType, monkeypatch: pytest.MonkeyPatch, member: str, spelling: str, shape: str
) -> None:
    """Red before the repair: one alphanumeric character inside the edge.

    Measured twice, so a refusal cannot pass because the rule never fired.
    """
    line = REFUSED_SHAPES[shape](spelling)
    assert _QUOTED in reasons(gate, line), member + " at " + shape
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    assert _QUOTED in reasons(gate, line), member + " control at " + shape


def test_the_documented_aws_example_one_character_short_of_the_edge_is_refused(
    gate: ModuleType,
) -> None:
    """The trailing member moved one character inward is no longer forgiven."""
    token = "AK" + "IA" + "IOSFODN7" + "EXAM" + "PLE" + "Q"
    assert "AWS access key id" in reasons(gate, token)


# --------------------------------------------------------------------------
# Arm 4 - the membership lives in ONE place
# --------------------------------------------------------------------------

#: The shape the compiled pattern takes around the member alternation. Every
#: member reaches the pattern ONLY through the enumeration.
_SKELETON = "^M|M$|(?<![A-Za-z0-9])M(?![A-Za-z0-9])"


def test_the_spelling_table_moves_with_the_enumeration(gate: ModuleType) -> None:
    """A member added or removed in the gate reddens this until graded here."""
    assert tuple(sorted(gate.PLACEHOLDER_MEMBERS)) == tuple(sorted(SPELLINGS))
    assert len(set(gate.PLACEHOLDER_MEMBERS)) == len(gate.PLACEHOLDER_MEMBERS)


def test_the_compiled_pattern_is_derived_from_the_enumeration_alone(gate: ModuleType) -> None:
    """No member can reach ``PLACEHOLDER_RE`` except through the enumeration."""
    alternation = "(?:" + "|".join(gate.PLACEHOLDER_MEMBERS) + ")"
    skeleton = gate.PLACEHOLDER_RE.pattern.replace(alternation, "M")
    assert skeleton == _SKELETON
    assert gate.PLACEHOLDER_RE.flags & re.IGNORECASE


@pytest.mark.parametrize(("member", "spelling"), BOUNDARY_CASES)
def test_every_enumerated_member_is_live_as_a_whole_body(
    gate: ModuleType, member: str, spelling: str
) -> None:
    """Each member, alone, is forgiven - so none is enumerated but dead."""
    assert gate.PLACEHOLDER_RE.search(spelling), member


# --------------------------------------------------------------------------
# Arm 5 - one positive control per existing rule
# --------------------------------------------------------------------------

NEIGHBOUR_CONTROLS: dict[str, tuple[str, ...]] = {
    "PEM private key block": ("-----BEGIN " + "RSA PRIVATE " + "KEY-----",),
    "PuTTY private key file": ("PuTTY-User-" + "Key-File-" + "2",),
    "AWS access key id": ("AK" + "IA" + ("Q7" * 8),),
    "GitHub token": ("ghp" + "_" + ("Q7vR" * 6),),
    "GitHub fine-grained personal access token": ("github" + "_pat_" + ("Q7vR" * 6),),
    "Slack token": ("xox" + "b-" + ("Q7vR" * 4),),
    "Google API key": ("AI" + "za" + ("Q7vR2mZ" * 5),),
    "bearer token": ("Bea" + "rer " + ("Q7vR" * 6),),
    _QUOTED: (_PW + _Q + ("Q7vR" * 5) + _Q,),
    # Two controls: the hex branch, then the base64-shaped branch.
    "credential assigned a bare high-entropy literal": (
        "session" + "_key=" + ("a1b2" * 10),
        "session" + "_key=" + ("Q7vR2mZ9" * 6),
    ),
    "Anthropic API or admin key (vendor prefix)": ("sk" + "-ant-" + "admin" + "01-" + _PAD[:48],),
}


def test_every_rule_has_a_named_control(gate: ModuleType) -> None:
    """The control table names exactly the rules in ``SECRET_PATTERNS``."""
    assert {reason for _, reason in gate.SECRET_PATTERNS} == set(NEIGHBOUR_CONTROLS)


NEIGHBOUR_CASES = [
    (reason, index)
    for reason in sorted(NEIGHBOUR_CONTROLS)
    for index in range(len(NEIGHBOUR_CONTROLS[reason]))
]


@pytest.mark.parametrize(("reason", "index"), NEIGHBOUR_CASES)
def test_each_rule_still_fires_on_its_own_control(
    gate: ModuleType, reason: str, index: int
) -> None:
    """Per rule, not per count: the named rule itself reports its control."""
    assert reason in reasons(gate, NEIGHBOUR_CONTROLS[reason][index])
