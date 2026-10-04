"""CS-500: advice cards - a stable identity plus three tiers projected from ONE trace.

WHAT THIS MODULE OWNS (BOOTSTRAP.md sections 5.1 and 5.2). A :class:`Card` is
built from exactly one :class:`~clockspeed.advisor.trace.Trace` and from
nothing else. Its only constructor parameter is that trace, so no caller can
hand it a headline, a reason or a derivation: tier 1, tier 2 and tier 3 are
read-only properties computed from the trace on every access (non-negotiable
8 - the derivation is generated, never hand-written). A trace that carries no
recommendation yields no card: :func:`card_for` returns None and the
constructor refuses it.

IDENTITY. :func:`card_id` is the SHA-256 hex digest of the canonical ASCII
JSON array ``[CARD_ID_SCHEME, rule_id, subject_key, target_milestone]`` -
compact separators, ``ensure_ascii``, ``null`` for no milestone. JSON quoting
makes the encoding unambiguous: no choice of field text can make two different
triples serialise alike. Nothing volatile enters it - no input value, no
computed number, no step, no world token - so the same advice on a reloaded
save whose numbers moved keeps its id and its ledger state. Python's
``hash()`` is never used: it is salted per process.

THE TIERS.

- Tier 1, the headline: the recommendation's ``action``, whitespace collapsed
  to one line.
- Tier 2, the reason: the recommendation's ``reason``, the same way.
- Tier 3, the derivation: a header naming the rule, the advice and the target,
  then EVERY step of the trace in execution order, one numbered line each -
  every input read with its value and its source, every number computed, every
  alternative rejected with the reason it lost, and the rule firing. Every
  step kind the engine defines has a line shape here; a kind added later
  without one still renders its subject rather than vanishing.

NUMBERS. Every ``Fraction`` - read or computed - renders through
:func:`clockspeed.solve.exact.display_decimal` at :data:`DISPLAY_PLACES`
places, rounded once, half-even. When that rounding lost information the exact
ratio follows it, ``0.33 (exactly 1/3)``, so a reader reasoning it out by hand
is never handed a rounded figure as if it were the true one.

DETERMINISM AND ASCII. Output depends only on the trace. Steps keep the
trace's order; a mapping's entries are sorted by their rendered key; a set is
NEVER iterated - its rendering names only its type, because its order depends
on ``PYTHONHASHSEED`` (the engine refuses set inputs anyway). A string VALUE
is always quoted in JSON's ASCII escape, so it can never read as a number, as
the bare ``none`` of a None, or as a different string. Authored names -
subjects, sources, reasons - write every character outside printable ASCII in
Python's ``unicode_escape`` spelling. Card text is therefore always 7-bit
ASCII and always one line per step.

REFUSALS. The constructor refuses a trace it could not project honestly: no
recommendation; an identity or tier field that is not exactly a ``str``; a
headline or reason that is empty once collapsed to one line; or a step list
that does not end in exactly one ``rule-fired`` step naming the
recommendation's subject key - the engine's own shape, so a forged trace
whose firing and recommendation disagree never becomes a card.

PRIVACY. Tier text renders the input values a rule read - that IS the product.
``repr(card)`` does not: it carries the id, the domain and step counts only,
so a card in a log line, an assertion or an exception context leaks nothing.
No world token is read here; a card knows only its trace.

ZERO LANGUAGE MODEL, NO FILE I/O. Every word of every tier is either authored
in this module or taken verbatim from the trace.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

from clockspeed.advisor.trace import (
    MAX_EXACT_DEPTH,
    Recommendation,
    StepKind,
    Trace,
    TraceStep,
)
from clockspeed.solve.exact import display_decimal

#: Versions the identity encoding. Changing it changes EVERY card id, which
#: orphans every ledger entry - so it never changes silently.
CARD_ID_SCHEME: Final = "clockspeed.card.v1"

#: Digits after the point when a Fraction is displayed in tier 3.
DISPLAY_PLACES: Final = 2

#: Printable 7-bit ASCII, kept verbatim. Everything else is escaped.
_PRINTABLE_LOW: Final = " "
_PRINTABLE_HIGH: Final = "~"


def card_id(rule_id: str, subject_key: str, target_milestone: str | None) -> str:
    """Return the stable card id for one identity triple.

    SHA-256 hex over the canonical ASCII JSON array of
    ``[CARD_ID_SCHEME, rule_id, subject_key, target_milestone]``. Pure and
    salt-free: the same triple gives the same id in every process.

    Raises:
        TypeError: ``rule_id`` or ``subject_key`` is not exactly a ``str``, or
            ``target_milestone`` is neither None nor exactly a ``str``. JSON
            would serialise a tuple and a list - or a ``str`` subclass and its
            base - alike, so only the exact types may reach the hash.
    """
    if type(rule_id) is not str or type(subject_key) is not str:
        raise TypeError("a card id takes a rule id and a subject key that are exactly str")
    if target_milestone is not None and type(target_milestone) is not str:
        raise TypeError("a card id takes a target milestone that is None or exactly str")
    canonical = json.dumps(
        [CARD_ID_SCHEME, rule_id, subject_key, target_milestone],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _escape(text: str) -> str:
    """Render ``text`` as printable 7-bit ASCII, escaping everything else."""
    out = []
    for char in text:
        if _PRINTABLE_LOW <= char <= _PRINTABLE_HIGH:
            out.append(char)
        else:
            out.append(char.encode("unicode_escape").decode("ascii"))
    return "".join(out)


def _one_line(text: str) -> str:
    """Collapse every whitespace run to one space, then escape."""
    return _escape(" ".join(text.split()))


def _quote(text: str) -> str:
    """Render a string VALUE quoted, in JSON's ASCII escape - never mistakable.

    A quoted value cannot read as a number, as the bare ``none`` of a None,
    or as another string: JSON escapes the quote, the backslash and every
    control and non-ASCII character. DEL, which JSON leaves raw, is escaped
    too so the line stays printable.
    """
    return json.dumps(text, ensure_ascii=True).replace("\x7f", "\\u007f")


def _number(value: Fraction) -> str:
    """Display a Fraction once, half-even, with the exact ratio when rounding lost it."""
    shown = display_decimal(value, DISPLAY_PLACES)
    if Fraction(shown) == value:
        return shown
    return f"{shown} (exactly {value.numerator}/{value.denominator})"


def _join(parts: Iterable[str]) -> str:
    return ", ".join(parts)


def render_value(value: object, depth: int = 0) -> str:  # noqa: PLR0911 - one return per allowlisted type is the clearest surface
    """Render one trace value as deterministic ASCII.

    Covers exactly what the engine lets a rule read, matched by EXACT type:
    ``None`` (the bare token ``none``), ``bool`` (``true`` / ``false``),
    ``int``, ``Fraction`` (see :func:`_number`), ``str`` (always quoted - see
    :func:`_quote`), tuples, ``MappingProxyType`` and frozen dataclasses,
    recursively. Anything else - a set above all - renders as its type name in
    angle brackets and is never iterated. No two values of different kinds
    render alike: only a string is quoted, only a Fraction carries a point.
    """
    if depth > MAX_EXACT_DEPTH:
        return "<nested too deeply>"
    kind = type(value)
    if value is None:
        return "none"
    if kind is bool:
        return "true" if value else "false"
    if kind is Fraction:
        return _number(value)  # type: ignore[arg-type]
    if kind is int:
        return str(value)
    if kind is str:
        return _quote(value)  # type: ignore[arg-type]
    if isinstance(value, tuple) and kind is tuple:
        return f"({_join(render_value(part, depth + 1) for part in value)})"
    if isinstance(value, MappingProxyType) and kind is MappingProxyType:
        entries = sorted(
            (render_value(key, depth + 1), render_value(item, depth + 1))
            for key, item in value.items()
        )
        return "{" + _join(f"{key}: {item}" for key, item in entries) + "}"
    if (
        dataclasses.is_dataclass(value)
        and not isinstance(value, type)
        and type(value).__dataclass_params__.frozen  # type: ignore[attr-defined]
    ):
        body = _join(
            f"{fld.name}={render_value(getattr(value, fld.name), depth + 1)}"
            for fld in dataclasses.fields(value)
        )
        return f"{_escape(type(value).__name__)}({body})"
    return f"<{_escape(type(value).__name__)}>"


def _source(step: TraceStep) -> str:
    return _escape(step.source) if step.source else "an unnamed source"


#: One line shape per step kind. Each names every field that kind carries.
_STEP_LINES: Final[dict[StepKind, Callable[[Trace, TraceStep], str]]] = {
    StepKind.INPUT_READ: lambda _t, s: (
        f"Read {_escape(s.subject)} = {render_value(s.value)} from {_source(s)}"
    ),
    StepKind.INPUT_REFUSED: lambda _t, s: (
        f"Refused input {_escape(s.subject)}: {_escape(s.reason)}"
    ),
    StepKind.INPUT_MISSING: lambda _t, s: (
        f"Missing input {_escape(s.subject)}: {_escape(s.reason)}"
    ),
    StepKind.COMPUTED: lambda _t, s: f"Computed {_escape(s.subject)} = {render_value(s.value)}",
    StepKind.ALTERNATIVE_REJECTED: lambda _t, s: (
        f"Rejected {_escape(s.subject)}: {_escape(s.reason)}"
    ),
    StepKind.PRECONDITION_UNMET: lambda _t, s: (
        f"Unmet precondition {_escape(s.subject)}: {_escape(s.reason)}"
    ),
    StepKind.RULE_FIRED: lambda t, s: f"Rule {_escape(t.rule_id)} fired for {_escape(s.subject)}",
    StepKind.RULE_ERROR: lambda _t, s: f"Rule error {_escape(s.subject)}: {_escape(s.reason)}",
}


def _step_line(trace: Trace, step: TraceStep) -> str:
    shape = _STEP_LINES.get(step.kind)
    if shape is None:
        return f"Step {_escape(str(step.kind.value))} {_escape(step.subject)}"
    return shape(trace, step)


@dataclass(frozen=True, eq=False)
class Card:
    """One piece of advice. Every tier is a projection of :attr:`trace`.

    The trace is the ONLY constructor parameter; tier text cannot be supplied.
    Compare cards by :attr:`id` or by their tier text - instances compare by
    identity, because a trace may hold unhashable mapping values.
    """

    trace: Trace

    def __post_init__(self) -> None:
        """Refuse any trace the card could not project honestly.

        Raises:
            TypeError: the argument is not a Trace; or its rule id, the
                recommendation's subject key, action or reason is not exactly
                a ``str``, or its target milestone is neither None nor exactly
                a ``str``.
            ValueError: the trace carries no recommendation; it does not end in
                exactly one ``rule-fired`` step naming the recommendation's
                subject key; or the headline or reason is empty once
                collapsed to one line.
        """
        trace = self.trace
        if type(trace) is not Trace:
            raise TypeError("a card is built from a Trace and nothing else")
        recommendation = trace.recommendation
        if recommendation is None:
            raise ValueError("a trace with no recommendation yields no card")
        if not all(
            type(text) is str
            for text in (
                trace.rule_id,
                recommendation.subject_key,
                recommendation.action,
                recommendation.reason,
            )
        ):
            raise TypeError("a card's rule id, subject key, action and reason must be str")
        milestone = recommendation.target_milestone
        if milestone is not None and type(milestone) is not str:
            raise TypeError("a card's target milestone must be None or str")
        fired = [step for step in trace.steps if step.kind is StepKind.RULE_FIRED]
        if (
            len(fired) != 1
            or trace.steps[-1] is not fired[0]
            or fired[0].subject != recommendation.subject_key
        ):
            raise ValueError(
                "a card's trace must end in exactly one rule-fired step for its subject key"
            )
        if not _one_line(recommendation.action) or not _one_line(recommendation.reason):
            raise ValueError("a card's headline or reason is empty")

    @property
    def _recommendation(self) -> Recommendation:
        recommendation = self.trace.recommendation
        if recommendation is None:  # unreachable after __post_init__
            raise ValueError("a trace with no recommendation yields no card")
        return recommendation

    @property
    def rule_id(self) -> str:
        """The rule that produced this card."""
        return self.trace.rule_id

    @property
    def domain(self) -> str:
        """The advice domain of the rule that produced this card."""
        return self.trace.domain

    @property
    def subject_key(self) -> str:
        """The stable identity of the thing advised about."""
        return self._recommendation.subject_key

    @property
    def target_milestone(self) -> str | None:
        """The milestone the advice serves, or None."""
        return self._recommendation.target_milestone

    @property
    def id(self) -> str:
        """The stable card id - see :func:`card_id`."""
        return card_id(self.rule_id, self.subject_key, self.target_milestone)

    @property
    def tier1(self) -> str:
        """The headline: one imperative line, no reasoning."""
        return _one_line(self._recommendation.action)

    @property
    def tier2(self) -> str:
        """The reason: one line naming the binding constraint."""
        return _one_line(self._recommendation.reason)

    @property
    def tier3(self) -> str:
        """The full derivation: every step of the trace, in order, one line each."""
        target = self.target_milestone
        lines = [
            f"Derivation of rule {_escape(self.rule_id)} (domain {_escape(self.domain)})",
            f"Advice: {self.tier1}",
            f"Because: {self.tier2}",
            f"Target milestone: {render_value(target)}",
            "Steps:",
        ]
        lines.extend(
            f"  {number}. {_step_line(self.trace, step)}"
            for number, step in enumerate(self.trace.steps, start=1)
        )
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Render the id, the domain and counts only - never tier text or values.

        Never raises: an instance whose constructor was bypassed and whose
        field holds something other than a recommending trace renders a fixed
        placeholder, never the held value.
        """
        trace = getattr(self, "trace", None)
        if type(trace) is not Trace or trace.recommendation is None:
            return "Card(<not built from a recommending trace>)"
        rejected = sum(1 for step in self.trace.steps if step.kind is StepKind.ALTERNATIVE_REJECTED)
        return (
            f"Card(id={self.id}, domain={_escape(self.domain)}, "
            f"steps={len(self.trace.steps)}, rejected={rejected})"
        )

    __str__ = __repr__


def card_for(trace: Trace) -> Card | None:
    """Return the card a trace yields, or None when it recommends nothing."""
    if trace.recommendation is None:
        return None
    return Card(trace)


def cards_for(traces: Iterable[Trace]) -> tuple[Card, ...]:
    """Return every card the traces yield, ordered by rule id then card id.

    The sort is stable: cards whose rule id AND card id tie - the same advice
    from two traces - keep the order their traces came in. A trace that
    recommends nothing yields no card and is dropped.
    """
    cards = [card for card in (card_for(trace) for trace in traces) if card is not None]
    return tuple(sorted(cards, key=lambda card: (card.rule_id, card.id)))
