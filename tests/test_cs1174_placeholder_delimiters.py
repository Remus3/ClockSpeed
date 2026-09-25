"""CS-1174 - what counts as a delimiter around a placeholder member.

THE DEFECT. ``tools/precommit_gate.py::PLACEHOLDER_RE`` forgives a member
delimited on both sides by a non-alphanumeric character (CS-1169). Its
lookarounds spelled "alphanumeric" as the ASCII class, so a NON-ASCII letter
counted as a delimiter: a member sitting between two such letters inside a
credential body was forgiven, on every rule whose alphabet admits them. Today
that is the quoted-assignment rule, and the exposure is content arriving from
outside, which is what the sweep and the outbound gate read.

THE SECOND HALF IS A TEST-STRENGTH GAP, NOT A LIVE ESCAPE. The shipped pattern
already refuses a member with a digit beside it, but no behavioural arm put a
digit there, so a mutant letting digits delimit was killed only by the
pattern-text pin. The digit arm below is therefore green against the shipped
gate by design, and its fail-first evidence is that mutant.

FOUR ARMS.

1. Non-ASCII letter: per rule whose alphabet admits one, a member with such a
   letter on one side or both is REFUSED. Measured twice, so a pass because the
   rule never fired is distinguishable from a pass because the allowlist
   declined.
2. Digit: per rule, a digit on the left of a member with a true delimiter on
   the right, then the mirror, is REFUSED. Measured twice.
3. Differential: across every code point in both positions, and across every
   member beside a broad context sample, nothing the ASCII-class pattern
   refuses is forgiven now, and every ASCII character is classified exactly
   as it was. The change may only TIGHTEN.
4. Population: which rules admit each case is pinned, so a builder that stops
   producing a matching token cannot silently narrow either arm.

EVERY NON-ASCII CHARACTER HERE IS BUILT WITH ``chr()`` AT RUN TIME. This file
is authored content and is held to 7-bit ASCII like every other.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.test_cs1169_placeholder_bounds import INFIX_BUILDERS, SPELLINGS

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "tools" / "precommit_gate.py"

#: Distinct from every other loader's module name, so no two suites can patch
#: each other's copy of the gate.
GATE_MODULE_NAME = "clockspeed_gate_for_cs1174"

#: A pattern that never matches, standing in for a disabled allowlist.
NEVER = re.compile(r"(?!)")

_QUOTED = "credential assigned a quoted literal of 16 or more characters"


def load_gate() -> ModuleType:
    """Load the frozen gate by path under a module name private to this file."""
    spec = importlib.util.spec_from_file_location(GATE_MODULE_NAME, GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[GATE_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


GATE = load_gate()

#: The pattern as CS-1169 shipped it, rebuilt from the gate's own member list
#: with the ASCII-only class. The differential grades the change against it.
_ASCII_RUN = "[A-Za-z" + "0-9]"
BASE_RE = re.compile(
    "^(?:{0})|(?:{0})$|(?<!{1})(?:{0})(?!{1})".format(
        "|".join(GATE.PLACEHOLDER_MEMBERS), _ASCII_RUN
    ),
    re.IGNORECASE,
)


@pytest.fixture
def gate() -> ModuleType:
    """The gate module shared by every arm in this file."""
    return GATE


def reasons(gate: ModuleType, text: str) -> list[str]:
    """Every SECRET reason ``check_secrets`` reports for ``text``."""
    report = gate.Report()
    gate.check_secrets("cs1174", text, report)
    return [diag.reason for diag in report.diagnostics if diag.code == "SECRET"]


def captured(reason: str, inner: str) -> bool:
    """Whether the rule's own pattern captures ``inner`` whole in its candidate.

    Decided from the rule itself, never from ``check_secrets``, so which cases
    an arm grades cannot depend on the allowlist under test.
    """
    line = INFIX_BUILDERS[reason](inner)
    for pattern, rule_reason in GATE.SECRET_PATTERNS:
        if rule_reason != reason:
            continue
        for match in pattern.finditer(line):
            if inner in match.group(match.lastindex or 0):
                return True
    return False


# --------------------------------------------------------------------------
# Arm 1 - a non-ASCII letter is part of the run, not a delimiter
# --------------------------------------------------------------------------

#: Non-ASCII alphanumerics from several scripts, plus a non-ASCII DIGIT. Each is
#: a delimiter to the ASCII-only class, and each is alphanumeric by
#: ``str.isalnum``. The Kelvin sign and the long s are deliberately absent:
#: case folding already made the old class treat them as letters, so they
#: cannot fail first; the differential arm covers them.
NON_ASCII_ALNUM = {
    "latin-e-acute": chr(0xE9),
    "cyrillic-zhe": chr(0x416),
    "greek-alpha": chr(0x3B1),
    "cjk-middle": chr(0x4E2D),
    "arabic-indic-three": chr(0x663),
}

#: Where the letter sits. A hyphen - a true delimiter - takes the other side,
#: so each placement isolates one side of the lookaround.
PLACEMENTS = {
    "both": lambda s, c: c + s + c,
    "left": lambda s, c: c + s + "-",
    "right": lambda s, c: "-" + s + c,
}

LETTER_CASES = [
    (reason, member, spelling, name, placement)
    for reason in sorted(INFIX_BUILDERS)
    for member in sorted(SPELLINGS)
    for spelling in SPELLINGS[member]
    for name in sorted(NON_ASCII_ALNUM)
    for placement in sorted(PLACEMENTS)
    if captured(reason, PLACEMENTS[placement](spelling, NON_ASCII_ALNUM[name]))
]


@pytest.mark.parametrize(("reason", "member", "spelling", "name", "placement"), LETTER_CASES)
def test_a_member_beside_a_non_ascii_letter_is_refused(
    gate: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    member: str,
    spelling: str,
    name: str,
    placement: str,
) -> None:
    """Red before the repair: the ASCII class read the letter as a delimiter."""
    line = INFIX_BUILDERS[reason](PLACEMENTS[placement](spelling, NON_ASCII_ALNUM[name]))
    refused = reason in reasons(gate, line)
    assert refused, member + " beside " + name + " on " + placement + " was forgiven"
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    fired = reason in reasons(gate, line)
    assert fired, member + " control: the rule never fired beside " + name


# --------------------------------------------------------------------------
# Arm 2 - a digit on each side in turn, graded by behaviour
# --------------------------------------------------------------------------

#: Candidate true delimiters, tried in order; each rule takes the first its own
#: alphabet admits beside the member. A space is included for the PEM label.
DELIMITERS = ("-", "_", ".", "+", "/", "~", "=", " ")

DIGIT_SIDES = {
    "left": lambda s, d: "7" + s + d,
    "right": lambda s, d: d + s + "7",
}


def _digit_case(reason: str, spelling: str, side: str) -> str | None:
    """The first delimiter the rule admits opposite the digit, or None."""
    for delimiter in DELIMITERS:
        if captured(reason, DIGIT_SIDES[side](spelling, delimiter)):
            return delimiter
    return None


DIGIT_CASES = [
    (reason, member, spelling, side, delimiter)
    for reason in sorted(INFIX_BUILDERS)
    for member in sorted(SPELLINGS)
    for spelling in SPELLINGS[member]
    for side in sorted(DIGIT_SIDES)
    for delimiter in [_digit_case(reason, spelling, side)]
    if delimiter is not None
]


@pytest.mark.parametrize(("reason", "member", "spelling", "side", "delimiter"), DIGIT_CASES)
def test_a_member_with_a_digit_on_one_side_is_refused(
    gate: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    member: str,
    spelling: str,
    side: str,
    delimiter: str,
) -> None:
    """A digit is part of the run; the far side is a true delimiter.

    Green against the shipped gate by design. A mutant that lets digits
    delimit forgives every case here, so this kills it by behaviour.
    """
    line = INFIX_BUILDERS[reason](DIGIT_SIDES[side](spelling, delimiter))
    refused = reason in reasons(gate, line)
    assert refused, member + " with a digit on the " + side + " was forgiven"
    monkeypatch.setattr(gate, "PLACEHOLDER_RE", NEVER)
    fired = reason in reasons(gate, line)
    assert fired, member + " control: the rule never fired with a digit on the " + side


# --------------------------------------------------------------------------
# Arm 3 - the differential: the change only tightens
# --------------------------------------------------------------------------

_PAD = "Q7vR2mZ9"

#: The first code point past 7-bit ASCII.
ASCII_END = 0x80

#: UTF-16 surrogates, which are not Unicode scalar values.
SURROGATES = range(0xD800, 0xE000)

#: The pattern carries the member alternation once per branch: start, end, delimited.
BRANCHES = 3


def _code_points() -> list[str]:
    """Every Unicode scalar value, surrogates excluded."""
    return [chr(cp) for cp in range(0x110000) if cp not in SURROGATES]


def test_every_code_point_is_classified_no_looser_than_before(gate: ModuleType) -> None:
    """Exhaustive over code points, on each side of a member, by the gate itself.

    Three properties at once. Nothing the ASCII-class pattern refused is now
    forgiven. Every ASCII character keeps its old verdict, underscore included.
    Every non-ASCII alphanumeric is now part of the run.
    """
    member = "TO" + "DO"
    loosened = 0
    ascii_moved = 0
    alnum_forgiven = 0
    for char in _code_points():
        for candidate in (_PAD + char + member + "-" + _PAD, _PAD + "-" + member + char + _PAD):
            now = gate.PLACEHOLDER_RE.search(candidate) is not None
            before = BASE_RE.search(candidate) is not None
            loosened += now and not before
            if ord(char) < ASCII_END:
                ascii_moved += now != before
            elif char.isalnum():
                alnum_forgiven += now
    assert (loosened, ascii_moved, alnum_forgiven) == (0, 0, 0)


#: The context sample for the member-wide differential: all of ASCII, plus
#: non-ASCII letters, digits, marks, symbols and spaces, and the case-folding
#: letters the old class already treated as letters.
_CONTEXT = [chr(cp) for cp in range(ASCII_END)] + [
    chr(cp)
    for cp in (
        0xA0, 0xAA, 0xB2, 0xB5, 0xBA, 0xC0, 0xDF, 0xE9, 0xF7, 0x130, 0x131, 0x17F,
        0x2BC, 0x300, 0x3B1, 0x416, 0x5D0, 0x663, 0x966, 0x2014, 0x2019, 0x2126,
        0x212A, 0x2160, 0x3000, 0x3042, 0x4E2D, 0xFF10, 0xFF21, 0x1D400,
    )
]  # fmt: skip


def test_no_member_candidate_the_old_pattern_refused_is_forgiven_now(gate: ModuleType) -> None:
    """Every member spelling beside every pair of context characters."""
    loosened = 0
    ascii_moved = 0
    graded = 0
    for member in sorted(SPELLINGS):
        for spelling in SPELLINGS[member]:
            for left in _CONTEXT:
                for right in _CONTEXT:
                    candidate = _PAD + left + spelling + right + _PAD
                    now = gate.PLACEHOLDER_RE.search(candidate) is not None
                    before = BASE_RE.search(candidate) is not None
                    graded += 1
                    loosened += now and not before
                    if ord(left) < ASCII_END and ord(right) < ASCII_END:
                        ascii_moved += now != before
    assert graded > 0
    assert (loosened, ascii_moved) == (0, 0)


def test_the_pattern_is_still_case_insensitive_and_built_from_the_enumeration(
    gate: ModuleType,
) -> None:
    """The member list reaches the pattern only through the enumeration."""
    alternation = "(?:" + "|".join(gate.PLACEHOLDER_MEMBERS) + ")"
    assert gate.PLACEHOLDER_RE.pattern.count(alternation) == BRANCHES
    assert gate.PLACEHOLDER_RE.flags & re.IGNORECASE


# --------------------------------------------------------------------------
# Arm 4 - the graded populations are pinned
# --------------------------------------------------------------------------

#: Only the quoted-assignment rule's alphabet admits a non-ASCII letter.
EXPECTED_LETTER_RULES = {_QUOTED: 25 * len(NON_ASCII_ALNUM) * len(PLACEMENTS)}

#: Measured. The AWS and classic GitHub rules are absent because their
#: alphabets admit no delimiter at all, so no digit case can be built for them.
EXPECTED_DIGIT_RULES = {
    "Anthropic API or admin key (vendor prefix)": 46,
    "GitHub fine-grained personal access token": 44,
    "Google API key": 46,
    "Slack token": 36,
    "bearer token": 46,
    _QUOTED: 50,
    "credential assigned a bare high-entropy literal": 34,
    "PEM private key block": 18,
}


def test_the_letter_population_is_pinned() -> None:
    """Which rules admit a non-ASCII letter, and how many cases each grades."""
    counts: dict[str, int] = {}
    for reason, *_ in LETTER_CASES:
        counts[reason] = counts.get(reason, 0) + 1
    assert counts == EXPECTED_LETTER_RULES


def test_the_digit_population_is_pinned() -> None:
    """Which rules admit a digit beside a delimiter, and how many cases each grades."""
    counts: dict[str, int] = {}
    for reason, *_ in DIGIT_CASES:
        counts[reason] = counts.get(reason, 0) + 1
    assert counts == EXPECTED_DIGIT_RULES
