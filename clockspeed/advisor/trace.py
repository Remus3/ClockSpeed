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
  raises :class:`InputRefusedError` and appends an ``input-refused`` step. A
  rule that swallows the exception gains nothing: any refusal in the context
  drops the recommendation.
- **Floats are refused.** Every value read is walked by an ALLOWLIST of exact
  types (non-negotiable 6); a float anywhere inside it refuses the read, and
  :meth:`RuleContext.compute` takes exactly a ``Fraction``.
- **Unknown content is flagged and skipped, never raised** (non-negotiable 7).
  A declared input the world does not carry is an ``input-missing`` step and
  no recommendation - never an exception out of :func:`run_rule`.

DETERMINISM. Steps are appended in execution order; required unlocks are
checked in their declared tuple order; :func:`run_rules` orders traces by rule
id. No ``hash()``, no set iteration feeds an output, no clock is read.

ZERO LANGUAGE MODEL, NO FILE I/O. Nothing here opens a file or calls out.
"""

from __future__ import annotations

import dataclasses
import enum
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


class StepKind(enum.Enum):
    """The kind of one trace step. The value is the stable wire spelling."""

    INPUT_READ = "input-read"
    INPUT_REFUSED = "input-refused"
    INPUT_MISSING = "input-missing"
    COMPUTED = "computed"
    ALTERNATIVE_REJECTED = "alternative-rejected"
    PRECONDITION_UNMET = "precondition-unmet"
    RULE_FIRED = "rule-fired"


class InputRefusedError(Exception):
    """A rule read an input it may not have: undeclared, missing or inexact.

    Raised inside :meth:`RuleContext.read` so the rule stops at the bad read,
    and caught by :func:`run_rule`, so it never escapes the engine. The message
    names only the rule id and the input NAME - both authored in this
    repository - and never the value.
    """


@dataclass(frozen=True)
class InputValue:
    """One input a world offers a rule: the value and where it was read from."""

    value: object
    source: str


@dataclass(frozen=True)
class WorldInputs:
    """Everything a rule may be handed: named inputs plus the unlock key set.

    The mapping is copied into a read-only proxy, so a rule cannot mutate the
    world another rule sees next.
    """

    values: Mapping[str, InputValue]
    unlocks: frozenset[str]

    def __post_init__(self) -> None:
        """Freeze the input mapping behind a read-only proxy."""
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True)
class Recommendation:
    """What a rule proposes. Tiers 1 and 2 are projected from it plus the trace.

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


@dataclass(frozen=True)
class TraceStep:
    """One step of a rule's execution.

    Attributes:
        kind: What happened.
        subject: The input name, computed label, rejected alternative, unmet
            unlock key, or (for ``rule-fired``) the recommendation's subject key.
        source: Where an input was read from; empty for other kinds.
        value: The value read or computed; None for other kinds.
        reason: Why an alternative was rejected or an input refused.
    """

    kind: StepKind
    subject: str
    source: str = ""
    value: object = None
    reason: str = ""


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
        """Refuse a malformed declaration at construction, not at run time."""
        if not self.rule_id or not self.rule_id.isascii():
            raise ValueError("a rule id must be non-empty ASCII")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError(f"rule {self.rule_id} declares an input twice")
        if len(set(self.unlocks)) != len(self.unlocks):
            raise ValueError(f"rule {self.rule_id} declares an unlock twice")


def _children(value: object) -> tuple[object, ...] | None:
    """Return the parts of an allowlisted container, or None for anything else."""
    if isinstance(value, enum.Enum):
        return (value.value,)
    if isinstance(value, (tuple, frozenset)):
        return tuple(value)
    if isinstance(value, Mapping):
        return tuple(part for pair in value.items() for part in pair)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return tuple(getattr(value, fld.name) for fld in dataclasses.fields(value))
    return None


def _inexact_reason(value: object, depth: int = 0) -> str | None:
    """Return why ``value`` is not exact, or None when every part of it is.

    An ALLOWLIST walk: exact scalars, None, enum members (by their value),
    tuples, frozensets, mappings and dataclass instances (by their fields).
    Anything else - a float, a Decimal, a list, an arbitrary object - is
    refused, so a new inexact type cannot slip past by not being named. When
    several parts are inexact the lexically smallest reason is returned, so a
    frozenset's iteration order never reaches the trace.
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
    """The only door a rule has onto the world. Every use is recorded."""

    def __init__(self, spec: RuleSpec, world: WorldInputs) -> None:
        """Bind one rule to one world with an empty step record."""
        self._spec = spec
        self._world = world
        self._steps: list[TraceStep] = []
        self._refusals = 0

    @property
    def rule_id(self) -> str:
        """The id of the rule this context serves."""
        return self._spec.rule_id

    @property
    def steps(self) -> tuple[TraceStep, ...]:
        """The steps recorded so far, in execution order."""
        return tuple(self._steps)

    @property
    def refusals(self) -> int:
        """How many reads or computations were refused."""
        return self._refusals

    def _refuse(self, kind: StepKind, subject: str, reason: str) -> InputRefusedError:
        self._refusals += 1
        self._steps.append(TraceStep(kind=kind, subject=subject, reason=reason))
        return InputRefusedError(f"rule {self._spec.rule_id}: {reason}: {subject}")

    def read(self, name: str) -> object:
        """Read one DECLARED input, recording it with its source.

        Raises:
            InputRefusedError: the name is undeclared, the world lacks it, or
                its value is not exact. The refusal is recorded first.
        """
        if name not in self._spec.inputs:
            raise self._refuse(StepKind.INPUT_REFUSED, name, "undeclared input")
        offered = self._world.values.get(name)
        if offered is None:
            raise self._refuse(StepKind.INPUT_MISSING, name, "input absent from the world")
        inexact = _inexact_reason(offered.value)
        if inexact is not None:
            raise self._refuse(StepKind.INPUT_REFUSED, name, inexact)
        self._steps.append(
            TraceStep(
                kind=StepKind.INPUT_READ,
                subject=name,
                source=offered.source,
                value=offered.value,
            )
        )
        return offered.value

    def read_exact(self, name: str) -> Fraction:
        """Read one declared input that must be exactly a ``Fraction``."""
        value = self.read(name)
        if type(value) is not Fraction:
            self._steps.pop()
            raise self._refuse(StepKind.INPUT_REFUSED, name, "input is not a Fraction")
        return value

    def compute(self, label: str, value: Fraction) -> Fraction:
        """Record one computed number. It must be exactly a ``Fraction``."""
        if type(value) is not Fraction:
            raise self._refuse(StepKind.INPUT_REFUSED, label, "computed value is not a Fraction")
        self._steps.append(TraceStep(kind=StepKind.COMPUTED, subject=label, value=value))
        return value

    def reject(self, alternative: str, reason: str) -> None:
        """Record one alternative the rule considered and why it lost."""
        self._steps.append(
            TraceStep(kind=StepKind.ALTERNATIVE_REJECTED, subject=alternative, reason=reason)
        )


def _unmet_steps(keys: tuple[str, ...], unlocks: frozenset[str]) -> list[TraceStep]:
    return [
        TraceStep(kind=StepKind.PRECONDITION_UNMET, subject=key, reason="unlock not held")
        for key in keys
        if key not in unlocks
    ]


def run_rule(spec: RuleSpec, world: WorldInputs) -> Trace:
    """Run one rule against one world and return its complete trace.

    Never raises for world content: an unmet unlock, an undeclared or missing
    input and an inexact value each end in a trace with no recommendation. An
    exception the rule raises for any other reason is a rule bug and propagates.
    """
    unmet = _unmet_steps(spec.unlocks, world.unlocks)
    if unmet:
        return Trace(spec.rule_id, spec.domain, tuple(unmet), None)

    ctx = RuleContext(spec, world)
    try:
        proposed = spec.evaluate(ctx)
    except InputRefusedError:
        proposed = None
    steps = list(ctx.steps)
    if ctx.refusals or proposed is None:
        return Trace(spec.rule_id, spec.domain, tuple(steps), None)
    if not isinstance(proposed, Recommendation):
        raise TypeError(f"rule {spec.rule_id} returned a non-Recommendation")

    late_unmet = _unmet_steps(proposed.requires, world.unlocks)
    if late_unmet:
        return Trace(spec.rule_id, spec.domain, (*steps, *late_unmet), None)

    steps.append(TraceStep(kind=StepKind.RULE_FIRED, subject=proposed.subject_key))
    return Trace(spec.rule_id, spec.domain, tuple(steps), proposed)


def run_rules(specs: tuple[RuleSpec, ...], world: WorldInputs) -> tuple[Trace, ...]:
    """Run every rule against one world, traces ordered by rule id."""
    ordered = sorted(specs, key=lambda spec: spec.rule_id)
    return tuple(run_rule(spec, world) for spec in ordered)


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
