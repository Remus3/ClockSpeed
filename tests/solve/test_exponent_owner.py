"""CS-1030: the shipped power-consumption exponent has ONE owner.

THE OWNER is the ``power_consumption_exponents`` map of the pinned fingerprint
in ``clockspeed/data/version.py`` - a measured census of the shipped docs file,
held under the drift guard that reddens when the shipped data moves. The
modules that used to restate an exponent now point at that pin in prose and
spell no value, so a balance patch moves the exponent in one place and leaves
no stale copy behind in them that still reads as current.

THE SCOPE IS THE NAMED MODULES, AND DELIBERATELY SO. The ban reads exactly the
modules in :data:`SCOPE` - the five the CS-1030 ruling measured as carriers. It
does not read the rest of ``clockspeed/``, because the ban is by VALUE and a
pinned exponent's value is not unique there: a bare decimal of the same value
is also a CSS length, a line height, a version string or a section number, and
no reader can tell those apart from a restatement by value alone. Widening the
scope is therefore a deliberate act, and
``test_the_scope_is_the_ruling_module_set`` makes it one.

THE BAN IS BY VALUE, NOT BY TEXT. Every key of the owner's map is read at test
time - never typed in this file, because a typed copy would be one more
restatement - and parsed to an exact Fraction. The spellings listed below are
parsed the same way, and a scoped module is refused when any of them EQUALS a
pinned exponent. Comparing values catches a spelling that differs from the
census key only by a trailing zero, which is the same value, and lets through a
number that merely contains the key's digits but is another value.

RECOGNISED IN CODE, read with :mod:`tokenize`:

- a numeric literal, with a unary minus applied;
- a literal ``a / b`` division, spaced or not, when it is a subexpression of
  its own: Python binds ``/`` left to right, so the pair is evaluated when the
  token before ``a`` is not a multiplicative operator or ``**`` and the token
  after ``b`` is not ``**`` or a trailer. ``a / b * y`` is ``(a / b) * y`` and
  IS evaluated; the ``b / c`` of ``a / b / c`` is not a subexpression and is
  not;
- a ``Fraction(a, b)`` call whose two arguments are each a signed numeric
  literal, optionally raised by ``**`` to an integer literal no larger in size
  than a fixed cap, with or without a trailing comma.

RECOGNISED IN PROSE - string literals, docstrings and comments - by a
digit-bounded pattern:

- a number, or a chain of numbers joined by ``/``, with no digit, decimal point
  or slash immediately before and no digit, decimal continuation or further
  ``/`` term immediately after. A number is a decimal with an optional
  exponent, so scientific notation parses. A single number or a two-term
  quotient is evaluated, with a leading minus applied; a chain of three or more
  terms, which is a date or a path, is not;
- ``Fraction(a, b)`` written out, on the same argument rule as code.

NAMED RESIDUALS - spellings of a pinned value this scan does NOT recognise:

- any argument or operand that is a name, a call, a parenthesised expression or
  a keyword argument, and any arithmetic other than the forms above;
- a value in words, a percentage, or a string handed to another parser;
- a prose quotient of three or more terms that happens to evaluate to a pin.

OUT OF SCOPE, stated so it is not read as covered:

- every file under ``clockspeed/`` outside :data:`SCOPE`, for the reason above;
- ``tests/``, whose fixtures carry the exponent as INPUT DATA, and ``docs/``;
- the float the power law degrades to when evaluated - the measured RESULT of
  evaluating the law, not the exponent, and outside CS-1030.

THE COMMON-MODE RISK is that every ban derives from the pin's key STRINGS. A
census format change that emptied the map, or wrote keys that no longer parse
as numbers, would silently narrow the scan to nothing while it stayed green.
``test_the_pinned_exponent_map_is_a_parsable_census`` refuses that.
"""

from __future__ import annotations

import io
import keyword
import re
import tokenize
from collections.abc import Callable, Mapping
from fractions import Fraction
from pathlib import Path
from typing import Final

import pytest

from clockspeed.data import version

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
OWNER: Final = Path(version.__file__).resolve()

#: Where in the pin the exponent values live: the census section, under the
#: exponent key. Key NAMES, not values - renaming either in the pin fails this
#: module loudly with a KeyError at collection.
CENSUS_SECTION: Final = "census"
EXPONENT_CENSUS_KEY: Final = "power_consumption_exponents"

#: The modules the ban reads. Held apart from the ruling's set below so that
#: changing either one alone reddens the scope arm.
SCOPE: Final = (
    "clockspeed/data/registry.py",
    "clockspeed/solve/exact.py",
    "clockspeed/solve/optimize.py",
    "clockspeed/solve/power.py",
    "clockspeed/surface/api/power.py",
)

#: The carrier set the CS-1030 adjudicator ruling measured at base.
RULING_MODULE_SET: Final = frozenset(
    {
        "clockspeed/surface/api/power.py",
        "clockspeed/solve/power.py",
        "clockspeed/solve/optimize.py",
        "clockspeed/solve/exact.py",
        "clockspeed/data/registry.py",
    }
)

#: A power argument's exponent is capped so a pathological literal cannot make
#: the scan evaluate an enormous integer.
_MAX_POWER: Final = 64

# --- literal arithmetic shared by both readers --------------------------------


def number_value(text: str) -> Fraction | None:
    """Evaluate one numeric literal exactly, or None for a complex literal."""
    cleaned = text.replace("_", "")
    if cleaned[-1:] in {"j", "J"}:
        return None
    try:
        return Fraction(cleaned)
    except ValueError:
        return Fraction(int(cleaned, 0))


def power_value(base: Fraction, exponent: Fraction) -> Fraction | None:
    """Evaluate ``base ** exponent`` exactly, for an integer exponent only."""
    if exponent.denominator != 1 or abs(exponent) > _MAX_POWER:
        return None
    if base == 0 and exponent < 0:
        return None
    return base**exponent.numerator


# --- the prose reader --------------------------------------------------------

_NUMBER: Final = r"[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?"
_SLASH: Final = r"[ \t]*/[ \t]*"
_ARG: Final = rf"(?P<{{name}}>[-+]?{_NUMBER})(?:[ \t]*\*\*[ \t]*(?P<{{name}}_pow>[-+]?{_NUMBER}))?"

#: A number or a ``/`` chain of numbers, digit-bounded on both sides.
PROSE_NUMBER_RE: Final = re.compile(
    rf"(?<![0-9./])(?P<sign>-?)(?P<chain>{_NUMBER}(?:{_SLASH}{_NUMBER})*)"
    rf"(?![0-9]|\.[0-9]|{_SLASH}[0-9])"
)
PROSE_FRACTION_CALL_RE: Final = re.compile(
    r"Fraction\([ \t]*"
    + _ARG.format(name="num")
    + r"[ \t]*,[ \t]*"
    + _ARG.format(name="den")
    + r"[ \t]*(?:,[ \t]*)?\)"
)

#: A quotient has exactly two terms; a longer ``/`` chain is a date or a path.
_QUOTIENT_TERMS: Final = 2


def _prose_arg(match: re.Match[str], name: str) -> Fraction | None:
    value = Fraction(match[name])
    if match[f"{name}_pow"] is None:
        return value
    return power_value(value, Fraction(match[f"{name}_pow"]))


def prose_values(text: str) -> list[tuple[int, Fraction]]:
    """Every recognised value a run of prose spells, with its character offset.

    Args:
        text: Prose - a docstring, a comment or a string literal.

    Returns:
        ``(offset, value)`` pairs, exact.
    """
    found: list[tuple[int, Fraction]] = []
    for match in PROSE_NUMBER_RE.finditer(text):
        terms = [Fraction(term.strip()) for term in match["chain"].split("/")]
        if len(terms) == 1:
            value = terms[0]
        elif len(terms) == _QUOTIENT_TERMS and terms[1] != 0:
            value = terms[0] / terms[1]
        else:
            continue
        found.append((match.start(), -value if match["sign"] else value))
    for match in PROSE_FRACTION_CALL_RE.finditer(text):
        numerator = _prose_arg(match, "num")
        denominator = _prose_arg(match, "den")
        if numerator is not None and denominator:
            found.append((match.start(), numerator / denominator))
    return found


# --- the code reader ---------------------------------------------------------

_PROSE_TOKENS: Final = frozenset(
    getattr(tokenize, name)
    for name in ("STRING", "COMMENT", "FSTRING_MIDDLE", "TSTRING_MIDDLE")
    if hasattr(tokenize, name)
)
_SKIPPED_TOKENS: Final = frozenset(
    {tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER}
)
#: A token before the numerator that binds it into an earlier operand, so the
#: literal pair either side of ``/`` is not a subexpression of its own.
_BINDS_BEFORE: Final = frozenset({"*", "/", "//", "%", "@", "**"})
#: A token after the denominator that binds it tighter than ``/`` does.
_BINDS_AFTER: Final = frozenset({"**", ".", "(", "["})


def _is_operand(token: tokenize.TokenInfo) -> bool:
    """True when a token ends an operand, which makes a following minus binary."""
    if token.type in {tokenize.NUMBER, tokenize.STRING}:
        return True
    if token.type == tokenize.NAME:
        return not keyword.iskeyword(token.string)
    return token.type == tokenize.OP and token.string in {")", "]", "}"}


def _op(tokens: list[tokenize.TokenInfo], index: int, spelled: str) -> bool:
    return (
        0 <= index < len(tokens)
        and tokens[index].type == tokenize.OP
        and tokens[index].string == spelled
    )


def _sign(tokens: list[tokenize.TokenInfo], index: int) -> tuple[int, int]:
    """Return the sign in front of ``tokens[index]`` and where the operand starts."""
    minus = index >= 1 and _op(tokens, index - 1, "-")
    if minus and (index == 1 or not _is_operand(tokens[index - 2])):
        return -1, index - 1
    return 1, index


def _signed_literal(tokens: list[tokenize.TokenInfo], index: int) -> tuple[Fraction, int] | None:
    """Read ``[+-] NUMBER`` at ``index``; return its value and the next index."""
    sign = 1
    if _op(tokens, index, "-") or _op(tokens, index, "+"):
        sign = -1 if tokens[index].string == "-" else 1
        index += 1
    if index >= len(tokens) or tokens[index].type != tokenize.NUMBER:
        return None
    value = number_value(tokens[index].string)
    if value is None:
        return None
    return sign * value, index + 1


def _call_argument(tokens: list[tokenize.TokenInfo], index: int) -> tuple[Fraction, int] | None:
    """Read a signed literal or a signed literal ``int ** int`` power."""
    sign = 1
    if _op(tokens, index, "-") or _op(tokens, index, "+"):
        sign = -1 if tokens[index].string == "-" else 1
        index += 1
    base = _signed_literal(tokens, index)
    if base is None:
        return None
    value, index = base
    if _op(tokens, index, "**"):
        exponent = _signed_literal(tokens, index + 1)
        if exponent is None:
            return None
        powered = power_value(value, exponent[0])
        if powered is None:
            return None
        value, index = powered, exponent[1]
    return sign * value, index


def _fraction_call(tokens: list[tokenize.TokenInfo], index: int) -> Fraction | None:
    """Evaluate ``Fraction(a, b)`` whose name token sits at ``index``, if literal."""
    if not _op(tokens, index + 1, "("):
        return None
    first = _call_argument(tokens, index + 2)
    if first is None or not _op(tokens, first[1], ","):
        return None
    second = _call_argument(tokens, first[1] + 1)
    if second is None:
        return None
    close = second[1] + 1 if _op(tokens, second[1], ",") else second[1]
    if not _op(tokens, close, ")") or second[0] == 0:
        return None
    return first[0] / second[0]


def code_values(tokens: list[tokenize.TokenInfo]) -> list[tuple[int, Fraction]]:
    """Every recognised value the code tokens of a module spell, with its line.

    Args:
        tokens: The significant tokens of one module, prose tokens excluded.

    Returns:
        ``(line, value)`` pairs, exact.
    """
    found: list[tuple[int, Fraction]] = []
    for index, token in enumerate(tokens):
        line = token.start[0]
        if token.type == tokenize.NUMBER:
            value = number_value(token.string)
            if value is None:
                continue
            sign, start = _sign(tokens, index)
            found.append((line, sign * value))
            divisor = tokens[index + 2] if index + 2 < len(tokens) else None
            bound_before = start >= 1 and tokens[start - 1].string in _BINDS_BEFORE
            bound_after = index + 3 < len(tokens) and tokens[index + 3].string in _BINDS_AFTER
            if (
                _op(tokens, index + 1, "/")
                and divisor is not None
                and divisor.type == tokenize.NUMBER
                and not bound_before
                and not bound_after
            ):
                denominator = number_value(divisor.string)
                if denominator:
                    found.append((line, sign * value / denominator))
        elif token.type == tokenize.NAME and token.string == "Fraction":
            called = _fraction_call(tokens, index)
            if called is not None:
                found.append((line, called))
    return found


def source_values(source: str) -> list[tuple[int, Fraction]]:
    """Every recognised value a Python module spells, code and prose, with its line."""
    found: list[tuple[int, Fraction]] = []
    code: list[tokenize.TokenInfo] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in _PROSE_TOKENS:
            for offset, value in prose_values(token.string):
                found.append((token.start[0] + token.string.count("\n", 0, offset), value))
        elif token.type not in _SKIPPED_TOKENS:
            code.append(token)
    found.extend(code_values(code))
    return found


def is_pinned(value: Fraction, exponents: frozenset[Fraction]) -> bool:
    """True when a spelled value equals a pinned exponent - by VALUE."""
    return value in exponents


# --- the owner ---------------------------------------------------------------


def census_problems(exponents: object) -> list[str]:
    """Name every way the pinned exponent map fails to be a usable census.

    Args:
        exponents: The value the pin holds under the exponent census key.

    Returns:
        One line per problem; empty when every key parses as a number.
    """
    if not isinstance(exponents, Mapping):
        return [f"the exponent census is a {type(exponents).__name__}, not a mapping"]
    if not exponents:
        return ["the exponent census is empty, so the scan would ban nothing"]
    problems = []
    for key in exponents:
        try:
            Fraction(str(key))
        except ValueError:
            problems.append(f"census key {key!r} does not parse as a Fraction")
    return problems


def pinned_exponents() -> list[str]:
    """Return every exponent key the owner pins, in pin order."""
    return [str(key) for key in version.pin()[CENSUS_SECTION][EXPONENT_CENSUS_KEY]]


def restatements(key: str) -> list[str]:
    """Name every scoped module line that spells the value of one pinned exponent.

    Args:
        key: A key of the pinned exponent map.

    Returns:
        ``path:line`` for each carrier, relative to the repository root.
    """
    exponents = frozenset({Fraction(key)})
    found = []
    for relative in SCOPE:
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for line, value in source_values(source):
            if is_pinned(value, exponents):
                found.append(f"{relative}:{line}")
    return found


# --- the spellings, derived from the owner -----------------------------------


def _decimal_places(key: str) -> int:
    return len(key.partition(".")[2])


def _scaled(key: str) -> int:
    """The key's digits as an integer over ``10 ** decimal places``."""
    return int(Fraction(key) * 10 ** _decimal_places(key))


def _stripped(key: str) -> str:
    return key.rstrip("0").rstrip(".") if "." in key else key


def _n(key: str) -> int:
    return Fraction(key).numerator


def _d(key: str) -> int:
    return Fraction(key).denominator


#: Spellings of a pinned exponent that ARE its value, each built from the key.
RESTATING_SPELLINGS: Final[dict[str, Callable[[str], str]]] = {
    "verbatim-key": lambda key: key,
    "trailing-zero": lambda key: f"{key}0",
    "quotient": lambda key: f"{_n(key)}/{_d(key)}",
    "spaced-quotient": lambda key: f"{_n(key)} / {_d(key)}",
    "leftmost-division-of-a-chain": lambda key: f"{_n(key)} / {_d(key)} * y",
    "fraction-call": lambda key: f"Fraction({_n(key)}, {_d(key)})",
    "fraction-call-trailing-comma": lambda key: f"Fraction({_n(key)}, {_d(key)},)",
    "fraction-call-sign-pair": lambda key: f"Fraction(-{_n(key)}, -{_d(key)})",
    "fraction-call-power-argument": lambda key: (
        f"Fraction({_scaled(key)}, 10**{_decimal_places(key)})"
    ),
    "fraction-of-stripped-string": lambda key: f"Fraction('{_stripped(key)}')",
    "scientific": lambda key: f"{_scaled(key)}e-{_decimal_places(key)}",
}

#: Spellings that CONTAIN a pinned exponent's digits and are another value.
LOOKALIKE_SPELLINGS: Final[dict[str, Callable[[str], str]]] = {
    "digit-before": lambda key: f"2{key}",
    "value-changing-digit-after": lambda key: f"{key}1",
    "date-chain": lambda key: f"2026/{_n(key)}/{_d(key)}",
    "negative-quotient": lambda key: f"-{_n(key)}/{_d(key)}",
    "dotted-version": lambda key: f"1.{key}",
    "path-segments": lambda key: f"v/{_n(key)}/{_d(key)}",
}

#: Where a spelling is placed: as code, inside a docstring, inside a comment.
CONTEXTS: Final[dict[str, str]] = {
    "code": "value = {spelled}\n",
    "docstring": '"""The shipped exponent is {spelled} on this build."""\n',
    "comment": "# the exponent is {spelled}, measured\nvalue = 0\n",
}


def _spelled_values(spelled: str, context: str) -> list[Fraction]:
    source = CONTEXTS[context].format(spelled=spelled)
    return [value for _, value in source_values(source)]


_KEYS: Final = pinned_exponents()


# --- the arms ----------------------------------------------------------------


def test_the_pinned_exponent_map_is_a_parsable_census() -> None:
    """The owner's map is non-empty and every key parses, so the scan bans something.

    Each refusal is watched firing on a synthetic stand-in, because an arm
    that has only ever passed says nothing about whether it can fail.
    """
    problems = census_problems(version.pin()[CENSUS_SECTION][EXPONENT_CENSUS_KEY])
    assert not problems, "\n".join(problems)
    assert census_problems({}), "an empty census was accepted"
    assert census_problems({"not-a-number": 1}), "an unparsable census key was accepted"
    assert census_problems([]), "a census that is not a mapping was accepted"


def test_the_scope_is_the_ruling_module_set() -> None:
    """The ban reads exactly the ruling's modules, each real, and never the owner.

    Widening or narrowing :data:`SCOPE` without the ruling's set moving with it
    reddens here, so a change of scope is a decision rather than a drift.
    """
    assert set(SCOPE) == RULING_MODULE_SET, sorted(set(SCOPE) ^ RULING_MODULE_SET)
    assert len(SCOPE) == len(RULING_MODULE_SET), "SCOPE lists a module twice"
    missing = [relative for relative in SCOPE if not (REPO_ROOT / relative).is_file()]
    assert not missing, f"scoped modules that do not exist: {missing}"
    owner_relative = OWNER.relative_to(REPO_ROOT).as_posix()
    assert owner_relative not in SCOPE, "the scan reads the owner it exists to defer to"


@pytest.mark.parametrize("key", _KEYS)
def test_no_scoped_module_restates_a_pinned_exponent(key: str) -> None:
    """No scoped module spells a pinned exponent's value in a recognised form.

    Parametrized one key per case, so the weakest member is graded on its own
    rather than hidden inside a pooled count.
    """
    carriers = restatements(key)
    count = len(carriers)
    listed = "\n  ".join(carriers)
    assert count == 0, (
        f"{count} scoped line(s) spell the value of a pinned exponent; cite the pin in "
        f"clockspeed/data/version.py instead of the digits:\n  {listed}"
    )


@pytest.mark.parametrize("context", list(CONTEXTS))
@pytest.mark.parametrize("spelling", list(RESTATING_SPELLINGS))
@pytest.mark.parametrize("key", _KEYS)
def test_a_restating_spelling_is_caught(key: str, spelling: str, context: str) -> None:
    """Every recognised spelling of a pinned exponent's value is caught, in every context.

    The spelling is rebuilt from the key, never typed, then placed as code, in
    a docstring and in a comment.
    """
    spelled = RESTATING_SPELLINGS[spelling](key)
    values = _spelled_values(spelled, context)
    caught = any(is_pinned(value, frozenset({Fraction(key)})) for value in values)
    assert caught, f"the {spelling} spelling in {context} was not caught"


@pytest.mark.parametrize("context", list(CONTEXTS))
@pytest.mark.parametrize("spelling", list(LOOKALIKE_SPELLINGS))
@pytest.mark.parametrize("key", _KEYS)
def test_a_lookalike_spelling_is_not_caught(key: str, spelling: str, context: str) -> None:
    """A number that contains a pinned exponent's digits but is another value passes.

    Each lookalike is built from the key, and is first checked to CONTAIN the
    key's digits as text - so it is a real trap for a text matcher - before the
    value reader is asserted to let it through.
    """
    spelled = LOOKALIKE_SPELLINGS[spelling](key)
    value = Fraction(key)
    digits = (key, f"{value.numerator}/{value.denominator}")
    assert any(text in spelled for text in digits), "the lookalike does not contain the digits"
    values = _spelled_values(spelled, context)
    caught = [item for item in values if is_pinned(item, frozenset({value}))]
    assert not caught, f"the {spelling} lookalike in {context} was caught as {caught}"


@pytest.mark.parametrize("key", _KEYS)
def test_the_owner_carries_each_key_it_is_scanned_for(key: str) -> None:
    """The keys come from the owner's own text, which the scan never reads.

    If the pin ever stopped carrying a key verbatim, the census would be
    reporting a spelling nothing owns.
    """
    owner_text = OWNER.read_text(encoding="utf-8")
    assert f'"{key}"' in owner_text, "the owner does not carry a key its own pin reports"


@pytest.mark.parametrize("key", _KEYS)
def test_no_pinned_exponent_is_exact_in_binary(key: str) -> None:
    """Each pinned exponent's reduced denominator is not a power of two.

    ``clockspeed/data/registry.py`` and ``clockspeed/solve/exact.py`` say, now
    without the digits, that a shipped exponent is not representable in binary
    floating point. That is true exactly when its reduced denominator is not a
    power of two, so this arm is the claim, measured against the owner.
    """
    denominator = Fraction(key).denominator
    power_of_two = denominator & (denominator - 1) == 0
    assert not power_of_two, "a pinned exponent is exact in binary; the prose claims otherwise"
