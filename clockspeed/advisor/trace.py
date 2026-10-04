"""CS-500: the rule execution trace - the one record all three explain tiers project.

WHAT THIS MODULE OWNS (BOOTSTRAP.md sections 5.1 and 5.4). A rule is a
:class:`RuleSpec`: an id, a domain, the inputs it DECLARES, the unlocks it
REQUIRES, and a pure ``evaluate`` function. :func:`run_rule` runs one spec
against one :class:`WorldInputs` and returns a :class:`Trace` - every input read
with its source, every number computed, every alternative rejected with its
reason, every unmet precondition, and the recommendation if one survived. Cards
consume the trace; nothing renders advice from anywhere else, which is why
tier 3 cannot drift from tiers 1 and 2.

THE ENGINE, NOT THE RULE, ENFORCES THE INVARIANTS. A rule is never trusted to
check its own preconditions:

- **Required unlocks are checked BEFORE the rule runs.** An unmet one is
  recorded as a ``precondition-unmet`` step and the rule is never evaluated, so
  it cannot suggest something the player cannot build. A recommendation may
  also name per-recommendation unlocks in ``requires`` - a recipe chosen from
  data - and those are checked after evaluation the same way.
- **An undeclared read is REFUSED AND RECORDED.** :meth:`RuleContext.read`
  raises :class:`InputRefusedError` and records an ``input-refused`` step. A
  rule that swallows the exception gains nothing: any refusal drops the
  recommendation.
- **Only immutable exact values cross.** Every value read is walked by an
  ALLOWLIST (non-negotiable 6): ``Fraction``, ``int``, ``bool``, ``str``,
  ``None``, enum members, tuples, ``MappingProxyType`` and FROZEN dataclasses,
  recursively. A SET IS REFUSED, frozen or not: its iteration order and repr
  depend on ``PYTHONHASHSEED``, so a set value would make two runs on the same
  save render different traces. A float anywhere refuses the read, and so does a
  MUTABLE container - a dict, a list, a set, a non-frozen dataclass - even
  when every part of it is exact, because a rule could write a float into it
  and reach the trace and every later rule through the shared reference.
  :meth:`RuleContext.compute` takes exactly a ``Fraction``.
- **Text is ASCII strings only.** A recommendation's fields, a computed label
  and a rejected alternative's text must be non-empty ASCII ``str``. Anything
  else is a rule bug: recorded as a ``rule-error`` step, recommendation
  dropped.
- **Unknown content and rule bugs are flagged and skipped, never raised**
  (non-negotiable 7). A missing declared input is an ``input-missing`` step;
  an exception out of ``evaluate`` is a ``rule-error`` step naming the
  exception TYPE only - never its message, which may carry a world value. A
  duplicated rule id refuses every rule carrying it, identically in any order.

WHAT "THE ONLY DOOR" DOES AND DOES NOT ENFORCE. Python has no privacy, so this
is stated precisely rather than claimed. ENFORCED: the context a rule receives
holds no world, no step list and no refusal counter as attributes - it carries
only the rule id and bound methods over engine-held state, and ``__slots__``
stops a rule from planting attributes on it - so assigning or clearing a
context attribute cannot unrefuse a read or erase a step. NOT ENFORCED: a rule
that follows a bound method's ``__self__`` to the engine's recorder, uses
``gc`` or ``ctypes``, or reads a
world it captured from its own module scope bypasses all of this. Those are
deliberate subversion, outside what a runtime check can stop; review and the
per-rule synthetic fixture tests are the control for them.

DETERMINISM. Steps are appended in execution order; required unlocks are
checked in their declared tuple order; :func:`run_rules` orders traces by rule
id; an inexact value's reason is the lexically smallest over its parts; set
values are refused outright. No ``hash()``, no clock.

ZERO LANGUAGE MODEL, NO FILE I/O. Nothing here opens a file or calls out.
"""

from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from clockspeed.save.world import UnlockState

#: How deep the exactness walk descends before refusing a value as unbounded.
MAX_EXACT_DEPTH: Final = 32

#: Scalar types a rule input may hold. An ALLOWLIST: anything else is refused.
_EXACT_SCALARS: Final = (Fraction, int, str)

#: Rule ids, domains and input names: lower-case ASCII identifiers only, so a
#: name interpolated into a message cannot carry world data in practice.
NAME_PATTERN: Final = re.compile(r"[a-z0-9_.:-]+")

#: Unlock keys: ASCII with no whitespace. Wider than :data:`NAME_PATTERN`
#: because a key embeds an asset path, which carries ``/`` and capitals.
UNLOCK_PATTERN: Final = re.compile(r"[A-Za-z0-9_.:/-]+")

#: The ``rule-error`` subject for a recommendation the engine refused.
_RECOMMENDATION: Final = "recommendation"


class StepKind(enum.Enum):
    """The kind of one trace step. The value is the stable wire spelling."""

    INPUT_READ = "input-read"
    INPUT_REFUSED = "input-refused"
    INPUT_MISSING = "input-missing"
    COMPUTED = "computed"
    ALTERNATIVE_REJECTED = "alternative-rejected"
    PRECONDITION_UNMET = "precondition-unmet"
    RULE_FIRED = "rule-fired"
    RULE_ERROR = "rule-error"


class InputRefusedError(Exception):
    """A rule's read or record was refused: undeclared, missing, inexact or bad text.

    Raised inside the context so the rule stops at the bad call, and caught by
    :func:`run_rule`, so it never escapes the engine. The message names only
    the rule id and an authored name - never a value.
    """


@dataclass(frozen=True)
class InputValue:
    """One input a world offers a rule: the value and where it was read from."""

    value: object
    source: str

    def __repr__(self) -> str:
        """Render the value's TYPE only - never the value, never the source."""
        return f"InputValue(value=<{type(self.value).__name__}>, source=<redacted>)"


@dataclass(frozen=True)
class WorldInputs:
    """Everything a rule may be handed: named inputs plus the unlock key set.

    The top-level mapping is copied into a read-only proxy; each VALUE must
    itself be immutable or :meth:`RuleContext.read` refuses it, so no rule can
    alter what another rule reads next.
    """

    values: Mapping[str, InputValue]
    unlocks: frozenset[str]

    def __post_init__(self) -> None:
        """Freeze the input mapping behind a read-only proxy."""
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def __repr__(self) -> str:
        """Render counts only. Unlock keys embed save object paths."""
        return f"WorldInputs(values={len(self.values)}, unlocks={len(self.unlocks)})"


@dataclass(frozen=True)
class Recommendation:
    """What a rule proposes. Tiers 1 and 2 are projected from it plus the trace.

    Every text field must be non-empty ASCII ``str``; the engine refuses
    anything else as a rule bug.

    Attributes:
        subject_key: The stable identity of the thing advised about. Feeds the
            card id, so it must encode nothing volatile.
        action: The imperative the headline is built from.
        reason: The binding constraint the one-line reason is built from.
        target_milestone: The milestone the advice serves, or None.
        requires: Unlock keys THIS recommendation needs beyond the rule's own -
            a recipe chosen from data. Checked by the engine after evaluation.
    """

    subject_key: str
    action: str
    reason: str
    target_milestone: str | None = None
    requires: tuple[str, ...] = ()

    def __repr__(self) -> str:
        """Render field TYPES only: a subject key or unlock may name save content."""
        return (
            f"Recommendation(subject_key=<{type(self.subject_key).__name__}>, "
            f"action=<{type(self.action).__name__}>, reason=<{type(self.reason).__name__}>, "
            f"target_milestone=<{type(self.target_milestone).__name__}>, "
            f"requires=<{type(self.requires).__name__}>)"
        )


@dataclass(frozen=True)
class TraceStep:
    """One step of a rule's execution.

    Attributes:
        kind: What happened.
        subject: The input name, computed label, rejected alternative, unmet
            unlock key, the recommendation's subject key (``rule-fired``), or
            for ``rule-error`` an exception type name, ``recommendation``, or
            the duplicated rule id.
        source: Where an input was read from; empty for other kinds.
        value: The value read or computed; None for other kinds.
        reason: Why an alternative was rejected, an input refused, or a rule
            bug recorded. Always authored here or by the rule, never a value.
    """

    kind: StepKind
    subject: str
    source: str = ""
    value: object = None
    reason: str = ""

    def __repr__(self) -> str:
        """Render the kind and the value's TYPE only.

        The subject can be an unlock key embedding a save object path, the
        source names where a world value came from, and the value is world
        data, so none of them reaches a repr, a log line or an assertion.
        """
        return (
            f"TraceStep(kind={self.kind.value!r}, subject=<redacted>, source=<redacted>, "
            f"value=<{type(self.value).__name__}>, reason=<redacted>)"
        )


@dataclass(frozen=True)
class Trace:
    """The complete record of one rule run. The sole source of a card."""

    rule_id: str
    domain: str
    steps: tuple[TraceStep, ...]
    recommendation: Recommendation | None

    @property
    def unmet(self) -> tuple[str, ...]:
        """The unmet unlock keys, in the order they were checked."""
        return tuple(s.subject for s in self.steps if s.kind is StepKind.PRECONDITION_UNMET)

    @property
    def refused(self) -> tuple[str, ...]:
        """The input names refused, in the order the rule tried them."""
        return tuple(s.subject for s in self.steps if s.kind is StepKind.INPUT_REFUSED)


@dataclass(frozen=True)
class RuleSpec:
    """A rule: its declarations plus the pure function that evaluates it.

    Attributes:
        rule_id: Stable id. Feeds the card id and the global mute.
        domain: The advice domain the rule belongs to.
        inputs: Every input name the rule may read. Anything else is refused.
        unlocks: Every unlock key the rule requires before it may run at all.
        evaluate: Reads through the context, returns a recommendation or None.
    """

    rule_id: str
    domain: str
    inputs: tuple[str, ...]
    unlocks: tuple[str, ...]
    evaluate: Callable[[RuleContext], Recommendation | None] = field(compare=False)

    def __post_init__(self) -> None:
        """Refuse a malformed declaration at construction, not at run time.

        Messages name the FIELD, never the offending text, so a bad id cannot
        reach an exception either.
        """
        if not _matches(NAME_PATTERN, self.rule_id):
            raise ValueError("a rule id must match NAME_PATTERN")
        if not _matches(NAME_PATTERN, self.domain):
            raise ValueError("a rule domain must match NAME_PATTERN")
        if type(self.inputs) is not tuple or not all(
            _matches(NAME_PATTERN, name) for name in self.inputs
        ):
            raise ValueError("rule inputs must be a tuple matching NAME_PATTERN")
        if type(self.unlocks) is not tuple or not all(
            _matches(UNLOCK_PATTERN, key) for key in self.unlocks
        ):
            raise ValueError("rule unlocks must be a tuple matching UNLOCK_PATTERN")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError("a rule declares an input twice")
        if len(set(self.unlocks)) != len(self.unlocks):
            raise ValueError("a rule declares an unlock twice")


def _matches(pattern: re.Pattern[str], value: object) -> bool:
    """Whether ``value`` is exactly a ``str`` wholly matching ``pattern``."""
    return type(value) is str and pattern.fullmatch(value) is not None


def _is_text(value: object) -> bool:
    """Whether ``value`` is non-empty ASCII text, exactly a ``str``."""
    return type(value) is str and value != "" and value.isascii()


def _children(value: object) -> tuple[object, ...] | None:
    """Return the parts of an allowlisted immutable container, or None otherwise."""
    if isinstance(value, enum.Enum):
        return (value.value,)
    if isinstance(value, tuple):
        return tuple(value)
    if type(value) is MappingProxyType:
        return tuple(part for pair in value.items() for part in pair)
    if (
        dataclasses.is_dataclass(value)
        and not isinstance(value, type)
        and type(value).__dataclass_params__.frozen  # type: ignore[attr-defined]
    ):
        return tuple(getattr(value, fld.name) for fld in dataclasses.fields(value))
    return None


def _inexact_reason(value: object, depth: int = 0) -> str | None:
    """Return why ``value`` is not immutable and exact, or None when it is.

    An ALLOWLIST walk over :func:`_children`; anything it does not name - a
    float, a Decimal, a dict, a list, a set or frozenset, a non-frozen
    dataclass - is
    refused, so a new inexact or mutable type cannot slip past by not being
    named. When several parts fail, the lexically smallest reason is returned.
    """
    if depth > MAX_EXACT_DEPTH:
        return "nested too deeply to prove exact"
    if value is None or isinstance(value, bool) or type(value) in _EXACT_SCALARS:
        return None
    children = _children(value)
    if children is None:
        return f"a {type(value).__name__} is not an exact type"
    reasons = [r for r in (_inexact_reason(c, depth + 1) for c in children) if r is not None]
    return min(reasons) if reasons else None


class RuleContext:
    """The door a rule has onto the world. Every use is recorded engine-side.

    Holds the rule id and four bound callables over state :func:`run_rule`
    keeps; see the module docstring for exactly what that does and does not
    enforce. Only the engine constructs one.
    """

    __slots__ = ("_compute", "_read", "_refuse_exact", "_reject", "_rule_id")

    def __init__(self, recorder: _Recorder) -> None:
        """Bind the engine's recorder through its methods only, never itself."""
        self._rule_id = recorder.spec.rule_id
        self._read = recorder.read
        self._compute = recorder.compute
        self._reject = recorder.reject
        self._refuse_exact = recorder.read_exact_refusal

    @property
    def rule_id(self) -> str:
        """The id of the rule this context serves."""
        return self._rule_id

    def read(self, name: str) -> object:
        """Read one DECLARED input, recording it with its source.

        Raises:
            InputRefusedError: the name is undeclared, the world lacks it, or
                its value is not immutable and exact. The refusal is recorded
                first.
        """
        return self._read(name)

    def read_exact(self, name: str) -> Fraction:
        """Read one declared input that must be exactly a ``Fraction``."""
        value = self._read(name)
        if type(value) is not Fraction:
            self._refuse_exact(name)
            raise InputRefusedError(f"rule {self._rule_id}: input is not a Fraction")
        return value

    def compute(self, label: str, value: Fraction) -> Fraction:
        """Record one computed number. It must be exactly a ``Fraction``."""
        return self._compute(label, value)

    def reject(self, alternative: str, reason: str) -> None:
        """Record one alternative the rule considered and why it lost."""
        self._reject(alternative, reason)


def _unmet_steps(keys: tuple[str, ...], unlocks: frozenset[str]) -> list[TraceStep]:
    return [
        TraceStep(kind=StepKind.PRECONDITION_UNMET, subject=key, reason="unlock not held")
        for key in keys
        if key not in unlocks
    ]


def _recommendation_fault(proposed: object) -> str | None:
    """Return why ``proposed`` is not a well-formed recommendation, or None."""
    if type(proposed) is not Recommendation:
        return "evaluate returned a non-Recommendation"
    for name in ("subject_key", "action", "reason"):
        if not _is_text(getattr(proposed, name)):
            return f"field {name} is not non-empty ASCII text"
    if proposed.target_milestone is not None and not _is_text(proposed.target_milestone):
        return "field target_milestone is not non-empty ASCII text"
    if type(proposed.requires) is not tuple or not all(_is_text(k) for k in proposed.requires):
        return "field requires is not a tuple of non-empty ASCII text"
    return None


class _Recorder:
    """Engine-held state for one rule run. Never handed to the rule itself."""

    __slots__ = ("refused", "spec", "steps", "world")

    def __init__(self, spec: RuleSpec, world: WorldInputs) -> None:
        """Start an empty record for one rule over one world."""
        self.spec = spec
        self.world = world
        self.steps: list[TraceStep] = []
        self.refused: list[str] = []

    def refuse(self, kind: StepKind, subject: str, reason: str) -> InputRefusedError:
        self.refused.append(subject)
        self.steps.append(TraceStep(kind=kind, subject=subject, reason=reason))
        return InputRefusedError(f"rule {self.spec.rule_id}: {reason}")

    def read(self, name: str) -> object:
        if name not in self.spec.inputs:
            raise self.refuse(StepKind.INPUT_REFUSED, name, "undeclared input")
        offered = self.world.values.get(name)
        if offered is None:
            raise self.refuse(StepKind.INPUT_MISSING, name, "input absent from the world")
        inexact = _inexact_reason(offered.value)
        if inexact is not None:
            raise self.refuse(StepKind.INPUT_REFUSED, name, inexact)
        self.steps.append(
            TraceStep(
                kind=StepKind.INPUT_READ,
                subject=name,
                source=offered.source,
                value=offered.value,
            )
        )
        return offered.value

    def read_exact_refusal(self, name: str) -> None:
        """Withdraw the provisional read of ``name`` and record its refusal."""
        if self.steps and self.steps[-1].kind is StepKind.INPUT_READ:
            self.steps.pop()
        self.refuse(StepKind.INPUT_REFUSED, name, "input is not a Fraction")

    def compute(self, label: object, value: object) -> Fraction:
        if not _is_text(label):
            raise self.refuse(StepKind.RULE_ERROR, "compute", "label is not ASCII text")
        if type(value) is not Fraction:
            raise self.refuse(StepKind.RULE_ERROR, "compute", "computed value is not a Fraction")
        self.steps.append(TraceStep(kind=StepKind.COMPUTED, subject=str(label), value=value))
        return value

    def reject(self, alternative: object, reason: object) -> None:
        if not (_is_text(alternative) and _is_text(reason)):
            raise self.refuse(StepKind.RULE_ERROR, "reject", "alternative text is not ASCII text")
        self.steps.append(
            TraceStep(
                kind=StepKind.ALTERNATIVE_REJECTED,
                subject=str(alternative),
                reason=str(reason),
            )
        )


def run_rule(spec: RuleSpec, world: WorldInputs) -> Trace:
    """Run one rule against one world and return its complete trace.

    Never raises for world content or a rule bug: an unmet unlock, an
    undeclared or missing input, an inexact or mutable value, malformed text
    and an exception out of ``evaluate`` each end in a trace with no
    recommendation.
    """
    unmet = _unmet_steps(spec.unlocks, world.unlocks)
    if unmet:
        return Trace(spec.rule_id, spec.domain, tuple(unmet), None)

    recorder = _Recorder(spec, world)
    proposed: object = None
    try:
        proposed = spec.evaluate(RuleContext(recorder))
    except InputRefusedError:
        proposed = None
    except Exception as exc:  # a rule bug is recorded, never fatal
        recorder.steps.append(
            TraceStep(kind=StepKind.RULE_ERROR, subject=type(exc).__name__, reason="rule raised")
        )
        recorder.refused.append(type(exc).__name__)
    steps = list(recorder.steps)
    if recorder.refused or proposed is None:
        return Trace(spec.rule_id, spec.domain, tuple(steps), None)

    fault = _recommendation_fault(proposed)
    if fault is not None or not isinstance(proposed, Recommendation):
        steps.append(
            TraceStep(kind=StepKind.RULE_ERROR, subject=_RECOMMENDATION, reason=fault or "")
        )
        return Trace(spec.rule_id, spec.domain, tuple(steps), None)

    late_unmet = _unmet_steps(proposed.requires, world.unlocks)
    if late_unmet:
        return Trace(spec.rule_id, spec.domain, (*steps, *late_unmet), None)

    steps.append(TraceStep(kind=StepKind.RULE_FIRED, subject=proposed.subject_key))
    return Trace(spec.rule_id, spec.domain, tuple(steps), proposed)


def run_rules(specs: tuple[RuleSpec, ...], world: WorldInputs) -> tuple[Trace, ...]:
    """Run every rule against one world, traces ordered by rule id.

    A rule id carried by more than one spec is refused for ALL of them: one
    trace with a ``rule-error`` step and no recommendation, built from the
    sorted domains, so the output does not depend on the order ``specs`` came
    in.
    """
    by_id: dict[str, list[RuleSpec]] = {}
    for spec in specs:
        by_id.setdefault(spec.rule_id, []).append(spec)
    traces: list[Trace] = []
    for rule_id in sorted(by_id):
        group = by_id[rule_id]
        if len(group) == 1:
            traces.append(run_rule(group[0], world))
            continue
        step = TraceStep(
            kind=StepKind.RULE_ERROR,
            subject=rule_id,
            reason="rule id declared by more than one rule",
        )
        domain = min(spec.domain for spec in group)
        traces.append(Trace(rule_id, domain, (step,), None))
    return tuple(traces)


def unlock_keys(state: UnlockState) -> frozenset[str]:
    """Flatten an unlock state into the prefixed key set rules declare against.

    ``schematic:<path>`` per purchased schematic, ``recipe:<path>`` per unlocked
    recipe, ``feature:<name>`` per feature flag that is TRUE. A false flag
    contributes nothing, so a rule requiring it cannot fire.
    """
    keys = {f"schematic:{path}" for path in state.purchased_schematics}
    keys.update(f"recipe:{path}" for path in state.recipes)
    keys.update(f"feature:{name}" for name, held in state.feature_flags.items() if held is True)
    return frozenset(keys)
