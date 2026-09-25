"""CS-1030: the shipped power-consumption exponent has ONE owner.

THE OWNER is the ``power_consumption_exponents`` map of the pinned fingerprint
in ``clockspeed/data/version.py`` - a measured census of the shipped docs file,
held under the drift guard that reddens when the shipped data moves. Every
other shipped source that needs to talk about the exponent points at that pin
in prose and never spells a value out, so a balance patch moves the exponent in
one place and leaves no stale copy behind that still reads as current.

THE BAN IS BY VALUE, NOT BY TEXT. Every key of that map is read from the owner
at test time - never typed in this file, because a typed copy would be one more
restatement - and parsed to an exact Fraction. Every number a shipped source
spells is parsed the same way, and a source is refused when any of them EQUALS
a pinned exponent, however it is written. A text match misses the spellings a
formatter or a hurried author produces and fires on unrelated numbers that
merely contain the digits; comparing values does neither. Two readers do it:

- CODE, in a Python module, is read with :mod:`tokenize`. A numeric literal, a
  literal ``int / int`` division (spaced or not) and a ``Fraction(a, b)`` call
  on two literals are each evaluated exactly. A unary minus is applied, so a
  negative value is a different value. A division inside a longer chain of
  multiplicative operators is not a quotient of its own and is not evaluated.
- PROSE - string literals, docstrings, comments, and every file that is not a
  Python module - is read with a digit-bounded pattern: a number, or a chain of
  numbers joined by ``/``, with no digit, decimal point or slash immediately
  before and no digit, decimal continuation or further ``/`` term immediately
  after. A number is a decimal
  with an optional exponent, so scientific notation parses. A single number or
  a two-term quotient is evaluated; a longer chain, which is a date or a path,
  is not. A leading minus is applied. ``Fraction(a, b)`` written in prose is
  evaluated as the call it spells.

A spelling that differs from the census key only by a trailing zero is the SAME
value and IS a restatement. A spelling with a digit added before or after that
changes the value is a different number and is not.

WHAT THE SCAN DOES NOT COVER, stated so it is not read as covering it:

- ``tests/``. Fixtures there carry the exponent as INPUT DATA - a synthetic
  registry has to hold some value - and an input is not a restatement.
- ``docs/``, ADRs and the other markdown. Those belong to a separate census.
- A value reached by any other computation, a value spelled in words, and a
  percentage.
- The float the power law degrades to when evaluated. That is the measured
  RESULT of evaluating the law, not the exponent, and it is outside CS-1030.

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
PACKAGE_ROOT: Final = REPO_ROOT / "clockspeed"
OWNER: Final = Path(version.__file__).resolve()

#: Where in the pin the exponent values live: the census section, under the
#: exponent key. Key NAMES, not values - renaming either in the pin fails this
#: module loudly with a KeyError at collection.
CENSUS_SECTION: Final = "census"
EXPONENT_CENSUS_KEY: Final = "power_consumption_exponents"

#: Every shipped source that restated an exponent value before CS-1030, held
#: so the scan is proven to REACH them rather than trusted to.
FORMER_CARRIERS: Final = (
    "clockspeed/data/registry.py",
    "clockspeed/solve/exact.py",
    "clockspeed/solve/optimize.py",
    "clockspeed/solve/power.py",
    "clockspeed/surface/api/power.py",
)

# --- the prose reader --------------------------------------------------------

_NUMBER: Final = r"[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?"
_SLASH: Final = r"[ \t]*/[ \t]*"

#: A number or a ``/`` chain of numbers, digit-bounded on both sides. The
#: lookbehind refuses a digit, a decimal point or a slash immediately before;
#: the lookahead refuses a digit, a decimal continuation, or a further ``/``
#: term, so a chain is only ever matched whole.
PROSE_NUMBER_RE: Final = re.compile(
    rf"(?<![0-9./])(?P<sign>-?)(?P<chain>{_NUMBER}(?:{_SLASH}{_NUMBER})*)"
    rf"(?![0-9]|\.[0-9]|{_SLASH}[0-9])"
)
#: A quotient has exactly two terms; a longer ``/`` chain is a date or a path.
_QUOTIENT_TERMS: Final = 2

PROSE_FRACTION_CALL_RE: Final = re.compile(
    rf"Fraction\([ \t]*(?P<num>-?{_NUMBER})[ \t]*,[ \t]*(?P<den>-?{_NUMBER})[ \t]*\)"
)


def prose_values(text: str) -> list[tuple[int, Fraction]]:
    """Every value a run of prose spells, with its character offset.

    Args:
        text: Prose - a docstring, a comment, a string literal or a whole file.

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
        denominator = Fraction(match["den"])
        if denominator != 0:
            found.append((match.start(), Fraction(match["num"]) / denominator))
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
#: Operators that bind a literal division into a longer expression, so the
#: two literals either side of ``/`` are not a quotient of their own.
_BINDING_OPERATORS: Final = frozenset({"*", "/", "//", "%", "@", "**"})

#: The tokens after ``Fraction`` in a two-literal call: ``( a , b )``.
_CALL_WINDOW: Final = 5


def number_value(text: str) -> Fraction | None:
    """Evaluate one numeric literal exactly, or None for a complex literal."""
    cleaned = text.replace("_", "")
    if cleaned[-1:] in {"j", "J"}:
        return None
    try:
        return Fraction(cleaned)
    except ValueError:
        return Fraction(int(cleaned, 0))


def _is_operand(token: tokenize.TokenInfo) -> bool:
    """True when a token ends an operand, which makes a following minus binary."""
    if token.type in {tokenize.NUMBER, tokenize.STRING}:
        return True
    if token.type == tokenize.NAME:
        return not keyword.iskeyword(token.string)
    return token.type == tokenize.OP and token.string in {")", "]", "}"}


def _sign(tokens: list[tokenize.TokenInfo], index: int) -> tuple[int, int]:
    """Return the sign in front of ``tokens[index]`` and where the operand starts."""
    minus = index >= 1 and _op(tokens, index - 1, "-")
    if minus and (index == 1 or not _is_operand(tokens[index - 2])):
        return -1, index - 1
    return 1, index


def _op(tokens: list[tokenize.TokenInfo], index: int, spelled: str) -> bool:
    return (
        0 <= index < len(tokens)
        and tokens[index].type == tokenize.OP
        and tokens[index].string == spelled
    )


def code_values(tokens: list[tokenize.TokenInfo]) -> list[tuple[int, Fraction]]:
    """Every value the code tokens of a module spell, with its line.

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
            bound_before = start >= 1 and tokens[start - 1].string in _BINDING_OPERATORS
            bound_after = index + 3 < len(tokens) and (
                tokens[index + 3].string in _BINDING_OPERATORS
            )
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
            window = tokens[index + 1 : index + 1 + _CALL_WINDOW]
            shape = [(item.type, item.string) for item in window]
            if (
                len(window) == _CALL_WINDOW
                and shape[0] == (tokenize.OP, "(")
                and window[1].type == tokenize.NUMBER
                and shape[2] == (tokenize.OP, ",")
                and window[3].type == tokenize.NUMBER
                and shape[4] == (tokenize.OP, ")")
            ):
                numerator = number_value(window[1].string)
                denominator = number_value(window[3].string)
                if numerator is not None and denominator:
                    found.append((line, numerator / denominator))
    return found


def source_values(source: str, *, python: bool) -> list[tuple[int, Fraction]]:
    """Every value a shipped source spells, code and prose alike, with its line.

    Args:
        source: The file's text.
        python: Read code with :mod:`tokenize` and only its prose tokens as
            prose; otherwise the whole file is prose.

    Returns:
        ``(line, value)`` pairs, exact.
    """
    if not python:
        return [
            (source.count("\n", 0, offset) + 1, value) for offset, value in prose_values(source)
        ]
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


def shipped_sources() -> list[Path]:
    """Every file under ``clockspeed/`` except the owner and bytecode caches."""
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.resolve() != OWNER
    )


def restatements(key: str) -> list[str]:
    """Name every shipped source line that spells the value of one pinned exponent.

    Args:
        key: A key of the pinned exponent map.

    Returns:
        ``path:line`` for each carrier, relative to the repository root.
    """
    exponents = frozenset({Fraction(key)})
    found = []
    for path in shipped_sources():
        source = path.read_text(encoding="utf-8")
        for line, value in source_values(source, python=path.suffix == ".py"):
            if is_pinned(value, exponents):
                found.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{line}")
    return found


# --- the spellings, derived from the owner -----------------------------------


def _decimal_places(key: str) -> int:
    return len(key.partition(".")[2])


def _stripped(key: str) -> str:
    return key.rstrip("0").rstrip(".") if "." in key else key


#: Spellings of a pinned exponent that ARE its value, each built from the key.
RESTATING_SPELLINGS: Final[dict[str, Callable[[str], str]]] = {
    "verbatim-key": lambda key: key,
    "trailing-zero": lambda key: f"{key}0",
    "quotient": lambda key: f"{Fraction(key).numerator}/{Fraction(key).denominator}",
    "spaced-quotient": lambda key: f"{Fraction(key).numerator} / {Fraction(key).denominator}",
    "fraction-call": lambda key: (
        f"Fraction({Fraction(key).numerator}, {Fraction(key).denominator})"
    ),
    "fraction-of-stripped-string": lambda key: f"Fraction('{_stripped(key)}')",
    "scientific": lambda key: (
        f"{Fraction(key) * 10 ** _decimal_places(key)}e-{_decimal_places(key)}"
    ),
}

#: Spellings that CONTAIN a pinned exponent's digits and are another value.
LOOKALIKE_SPELLINGS: Final[dict[str, Callable[[str], str]]] = {
    "digit-before": lambda key: f"2{key}",
    "value-changing-digit-after": lambda key: f"{key}1",
    "date-chain": lambda key: f"2026/{Fraction(key).numerator}/{Fraction(key).denominator}",
    "negative-quotient": lambda key: f"-{Fraction(key).numerator}/{Fraction(key).denominator}",
    "dotted-version": lambda key: f"1.{key}",
    "path-segments": lambda key: f"v/{Fraction(key).numerator}/{Fraction(key).denominator}",
}

#: Where a spelling is placed: as code, inside a docstring, inside a comment,
#: and inside a file that is not a Python module.
CONTEXTS: Final[dict[str, tuple[str, bool]]] = {
    "code": ("value = {spelled}\n", True),
    "docstring": ('"""The shipped exponent is {spelled} on this build."""\n', True),
    "comment": ("# the exponent is {spelled}, measured\nvalue = 0\n", True),
    "non-python": ("const note = 'the exponent is {spelled} here';\n", False),
}


def _placed(spelled: str, context: str) -> tuple[str, bool]:
    template, python = CONTEXTS[context]
    return template.format(spelled=spelled), python


def _spelled_values(spelled: str, context: str) -> list[Fraction]:
    source, python = _placed(spelled, context)
    return [value for _, value in source_values(source, python=python)]


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


@pytest.mark.parametrize("key", _KEYS)
def test_no_shipped_source_restates_a_pinned_exponent(key: str) -> None:
    """No file under ``clockspeed/`` but the owner spells a pinned exponent's value.

    Parametrized one key per case, so the weakest member is graded on its own
    rather than hidden inside a pooled count.
    """
    carriers = restatements(key)
    count = len(carriers)
    listed = "\n  ".join(carriers)
    assert count == 0, (
        f"{count} shipped line(s) spell the value of a pinned exponent; cite the pin in "
        f"clockspeed/data/version.py instead of the digits:\n  {listed}"
    )


def test_the_scan_reaches_every_former_carrier_and_skips_only_the_owner() -> None:
    """The scan walks the modules that used to restate the exponent.

    Without this the ban could pass because the walk found no files at all, or
    because it quietly stopped descending into a sub-package.
    """
    scanned = {path.relative_to(REPO_ROOT).as_posix() for path in shipped_sources()}
    missing = [relative for relative in FORMER_CARRIERS if relative not in scanned]
    assert not missing, f"the scan does not reach {missing}"
    owner_relative = OWNER.relative_to(REPO_ROOT).as_posix()
    assert owner_relative not in scanned, "the scan reads the owner it exists to defer to"


@pytest.mark.parametrize("context", list(CONTEXTS))
@pytest.mark.parametrize("spelling", list(RESTATING_SPELLINGS))
@pytest.mark.parametrize("key", _KEYS)
def test_a_restating_spelling_is_caught(key: str, spelling: str, context: str) -> None:
    """Every spelling of a pinned exponent's value is caught, in every context.

    The spelling is rebuilt from the key, never typed, then placed as code, in
    a docstring, in a comment and in a non-Python file.
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
    """The keys come from the owner's own text, which the scan then excludes.

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
