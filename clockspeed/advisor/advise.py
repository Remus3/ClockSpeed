"""CS-500 slice S6: the advise() entry point - rules, cards, ledger and mutes, wired.

WHAT THIS MODULE OWNS (BOOTSTRAP.md sections 5.1 and 5.2). One call,
:func:`advise`, takes what the layers below hand the advisor after one save is
read - the header's world token and the rule inputs built from the audit and
unlock models - and returns an :class:`Advice`: every rule's trace, every card
a firing trace yields, and each card's resolution against BOTH persistence
layers. :func:`world_inputs` is the adapter from the audit power balance and
the unlock state to those inputs, :func:`inputs_of` composes that balance
from a world model and a registry through the audit constructors (CS-1270),
adds the fuel audit's inputs over the same machines model (CS-1285 slice D)
and the build check's (CS-1288) through :func:`merged_inputs`, and
:func:`advise_world` is the one call a surface makes over a world it holds.

THE PIN IS A PARAMETER, NEVER AN IMPORT (CS-1288, the session 138 ruling F2).
Every figure a rule prices from a nameplate is the PINNED build's, so
:func:`inputs_of` hands the audit's build check the pin and offers its three
inputs (:func:`clockspeed.advisor.build.build_inputs`); every rule reads them
first and, off the pin, names both builds on its card and settles nothing.
The pin is a REQUIRED keyword of :func:`inputs_of` and :func:`advise_world`
with no default: this module never imports the pin's owner,
``clockspeed.data.version``, and a caller that forgets the pin fails to call
rather than pricing silently.

THE TWO LAYERS, BOTH CONSULTED, NEVER MERGED (CLAUDE.md section 7).

- The per-world ledger answers each card's state in THIS world, keyed by the
  world token through :class:`clockspeed.advisor.ledger.Ledger` - never by a
  save filename and never by a world name. A token the ledger has never seen
  is a NEW WORLD: every card answers ``new`` and :attr:`Advice.new_world` is
  True. That is never a failure.
- The global mute store answers whether the card's RULE is silenced across
  every world. A mute hides the card whatever its ledger state, a pin
  included, because a mute is the "stop telling me" control.

VISIBILITY. A card is shown when its rule is not muted and its state is
``new``, ``accepted`` or ``pinned``. ``dismissed``, ``completed`` and an
active ``snoozed`` hide it. A lapsed snooze is resolved to ``new`` by the
ledger against the injected ``now``, so it shows again. Hidden cards are kept
in :attr:`Advice.cards` with their state, so a surface can offer to restore
one; :attr:`Advice.shown` is the visible subset in card order.

RELOAD (CS-500 acceptance A3). A card's id is a pure function of the identity
triple (:func:`clockspeed.advisor.cards.card_id`), and the stores are read
from the directory on every call, so the same advice on a later save of the
same world - numbers moved, stores rebuilt from disk - meets the state
recorded for it before.

READ-ONLY, AND THE ONE WRITE PATH. :func:`advise` never writes either store;
recording a state or a mute is the caller's act through the store's own
methods. ``completed`` (BOOTSTRAP.md section 5.2) is set by the stated write
path, :func:`advise_and_record` (CS-1268): it runs :func:`advise`, then hands
the ledger every firing card with its rule, the rules that reached a definite
verdict (:func:`settled_rules`) and every card shown ``new`` through
:meth:`clockspeed.advisor.ledger.Ledger.reconcile`. A recorded ``new`` or
``accepted`` card whose rule ran to a definite verdict without it becomes
``completed`` - a rule that raised, lacked input or was not run completes
nothing; a
``completed`` card whose rule fires again is surfaced as ``new``; the player's
``dismissed``, ``snoozed`` and ``pinned`` are never changed. Both transitions
are surfaced on :attr:`Advice.completed` and :attr:`Advice.reopened`. It never
writes the mute store.

SEAMS. This module consumes the audit models, the unlock state, the rule
registry and the stores. It opens no save, reads no docs file and renders
nothing on a surface. COMPOSING THE AUDIT MODELS IS THIS LAYER'S JOB (CS-1270):
the surface holds a parsed world model and a normalized registry and may not
reach the audit machines model itself (CS-1189), so :func:`inputs_of` calls
placement, machines, network, balance and fuel here, over the already-parsed
model - never over save or docs bytes. NO CLOCK: ``now`` is injected. NO LANGUAGE MODEL: every
word of every tier comes from :mod:`clockspeed.advisor.cards`.

PRIVACY. The world token is personal data. It is handed to the ledger and
held nowhere else: :class:`Advice` does not carry it, and no ``repr`` here
renders it, a tier text or an input value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import build_inputs
from clockspeed.advisor.cards import Card, cards_for
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.rules import registered_rules
from clockspeed.advisor.rules.fuel import fuel_inputs
from clockspeed.advisor.rules.power import balance_inputs
from clockspeed.advisor.trace import (
    InputValue,
    RuleSpec,
    StepKind,
    Trace,
    WorldInputs,
    run_rules,
    unlock_keys,
)
from clockspeed.audit.balance import balance_of
from clockspeed.audit.build import build_check_of
from clockspeed.audit.fuel import fuel_supply_of
from clockspeed.audit.machines import machines_of
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.audit.balance import WorldBalance
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import UnlockState, WorldModel

#: The ALLOWLIST (CS-1268): the trace steps a definite verdict is made of. A
#: rule whose trace holds ANY other kind reached no verdict, so a step kind
#: added to the engine later counts as undecided until it is classified here.
SETTLED_STEP_KINDS: Final = frozenset(
    {
        StepKind.INPUT_READ,
        StepKind.COMPUTED,
        StepKind.ALTERNATIVE_REJECTED,
        StepKind.RULE_FIRED,
    }
)

#: The step kinds that mean a rule reached no verdict. Documentation and the
#: partition test only - :func:`settled_rules` reads the allowlist alone.
UNDECIDED_STEP_KINDS: Final = frozenset(
    {
        StepKind.RULE_ERROR,
        StepKind.INPUT_MISSING,
        StepKind.INPUT_REFUSED,
        StepKind.PRECONDITION_UNMET,
        StepKind.VERDICT_INDETERMINATE,
    }
)

#: The ledger state kinds under which an unmuted card is shown.
VISIBLE_KINDS: Final = frozenset({"new", "accepted", "pinned"})


@dataclass(frozen=True, eq=False)
class AdvisedCard:
    """One card resolved against the per-world ledger and the global mute.

    Attributes:
        card: The card, all three tiers projected from its trace.
        state: Its state in this world, a snooze resolved against ``now``.
        muted: Whether its rule is muted across every world.
    """

    card: Card
    state: CardState
    muted: bool

    @property
    def visible(self) -> bool:
        """Whether the card is shown: not muted, and in a visible state."""
        return not self.muted and self.state.kind in VISIBLE_KINDS

    def __repr__(self) -> str:
        """Render the card's safe repr, the state and the flags - never tier text."""
        return (
            f"AdvisedCard(card={self.card!r}, state={self.state!r}, "
            f"muted={self.muted}, visible={self.visible})"
        )


@dataclass(frozen=True, eq=False)
class Advice:
    """Everything one :func:`advise` call produced over one world.

    Attributes:
        traces: Every rule's trace, ordered by rule id - silent rules included.
        cards: Every card a trace yielded, ordered by rule id then card id,
            each resolved against both persistence layers.
        new_world: Whether the ledger held nothing for this world token.
        completed: The card ids this run recorded ``completed``, sorted -
            always empty from the read-only :func:`advise`.
        reopened: The card ids this run moved from ``completed`` back to
            ``new``, sorted - always empty from the read-only :func:`advise`.
    """

    traces: tuple[Trace, ...]
    cards: tuple[AdvisedCard, ...]
    new_world: bool
    completed: tuple[str, ...] = ()
    reopened: tuple[str, ...] = ()

    @property
    def shown(self) -> tuple[AdvisedCard, ...]:
        """The visible cards, in card order."""
        return tuple(advised for advised in self.cards if advised.visible)

    def __repr__(self) -> str:
        """Render counts and the new-world flag only."""
        return (
            f"Advice(traces={len(self.traces)}, cards={len(self.cards)}, "
            f"shown={len(self.shown)}, new_world={self.new_world}, "
            f"completed={len(self.completed)}, reopened={len(self.reopened)})"
        )


def world_inputs(balance: WorldBalance, unlocks: UnlockState) -> WorldInputs:
    """Build the rule inputs for one world from its audit balance and unlock state.

    Offers every input the D4 power family reads from the balance, each sourced
    to its audit field, and the unlock key set the engine checks declared
    unlocks against. When the balance carries a production model, its
    capacity and completeness flag are offered too (CS-1271).
    """
    return WorldInputs(values=balance_inputs(balance), unlocks=unlock_keys(unlocks))


def merged_inputs(*groups: Mapping[str, InputValue]) -> dict[str, InputValue]:
    """Merge the input groups the family adapters offer into one mapping.

    Args:
        groups: One mapping per adapter, each keyed by input name.

    Returns:
        A fresh dict holding every group's inputs.

    Raises:
        ValueError: an input name is offered by more than one group. Refused,
            never overwritten: a rule would otherwise read another family's
            figure under its own name, and its derivation would lie. The
            message names the inputs, never a value.
    """
    merged: dict[str, InputValue] = {}
    for group in groups:
        clashing = sorted(name for name in group if name in merged)
        if clashing:
            raise ValueError("rule inputs offered by more than one adapter: " + ", ".join(clashing))
        merged.update(group)
    return merged


def inputs_of(
    model: WorldModel, registry: Registry, *, pinned_changelist: int | None
) -> WorldInputs:
    """Build the rule inputs for one parsed world against one registry (CS-1270).

    Composes the audit models the power balance needs - placement, machines
    and network, each read off the model - prices them against the registry's
    buildings, hands it the registry's generator namespace so a built
    generator's capacity is computed (CS-1271), and hands the balance and the
    model's unlock state to :func:`world_inputs`. Reads no file: both
    arguments are already parsed.

    THE FUEL AUDIT (CS-1285 slice D) runs over the SAME machines model, read
    once, and its inputs (:func:`clockspeed.advisor.rules.fuel.fuel_inputs`)
    are merged beside the balance inputs through :func:`merged_inputs`, which
    refuses a name both offer. ``raw_items`` stays at the audit's default of
    none: a world model declares no item supplied from outside its machines,
    and inventing one would mark a fuel unmeasured that the flow measures.

    THE BUILD CHECK (CS-1288) holds the model's header build beside the pin it
    is handed, and its three inputs are merged beside the other two groups
    the same way. Every registered rule reads them first.

    Args:
        model: The world model the surface holds.
        registry: The normalized registry.
        pinned_changelist: The pinned build's changelist, or None when the pin
            did not parse - never imported here (ruling F2).

    Returns:
        The rule inputs.

    Raises:
        ValueError: two adapters offer one input name.
    """
    machines = machines_of(model)
    balance = balance_of(
        placement_of(model),
        registry.buildings,
        machines,
        network_of(model),
        generators=registry.generators,
    )
    balanced = world_inputs(balance, model.unlocks)
    fuel = fuel_inputs(fuel_supply_of(machines, registry), registry)
    build = build_inputs(build_check_of(model, pinned_changelist=pinned_changelist))
    return WorldInputs(values=merged_inputs(balanced.values, fuel, build), unlocks=balanced.unlocks)


def advise(
    token: str,
    world: WorldInputs,
    *,
    ledger: Ledger,
    mutes: MuteStore,
    now: int,
    rules: tuple[RuleSpec, ...] | None = None,
) -> Advice:
    """Run the rules over one world and resolve every card against both stores.

    Args:
        token: The save header's world token. Personal data; handed to the
            ledger only.
        world: The rule inputs, as :func:`world_inputs` builds them.
        ledger: The per-world ledger.
        mutes: The global per-rule mute store.
        now: The current instant, for resolving a snooze. Never read from a
            clock here.
        rules: The rules to run. Defaults to the registry.

    Returns:
        The traces, the resolved cards and whether the world is new.

    Raises:
        clockspeed.advisor.ledger.StoreError: a store is corrupt, unreadable,
            or the token is not a world token. An unseen token is NOT an error.
    """
    specs = registered_rules() if rules is None else rules
    traces = run_rules(specs, world)
    muted = mutes.muted()
    new_world = not ledger.knows_world(token)
    advised = tuple(
        AdvisedCard(
            card=card,
            state=ledger.state(token, card.id, now=now),
            muted=card.rule_id in muted,
        )
        for card in cards_for(traces)
    )
    return Advice(traces=traces, cards=advised, new_world=new_world)


def settled_rules(traces: tuple[Trace, ...]) -> frozenset[str]:
    """The rule ids that reached a DEFINITE verdict - fired, or ran clean to silence.

    A rule is settled only when EVERY step of its trace is in the allowlist
    :data:`SETTLED_STEP_KINDS`. A ``rule-error``, ``input-missing``,
    ``input-refused``, ``precondition-unmet`` or ``verdict-indeterminate``
    step - or any kind not yet classified - means the rule raised, was
    refused an input, was never evaluated, or could not decide over an
    incomplete input or over a figure priced at a build other than the
    save's own (CS-1288: an off-pin or uncompared build records one
    ``verdict-indeterminate`` step, ``clockspeed/advisor/build.py``). Its
    silence says nothing about the world, so its cards may not be completed
    (CS-1268, CLAUDE.md non-negotiable 7).
    """
    return frozenset(
        trace.rule_id
        for trace in traces
        if all(step.kind in SETTLED_STEP_KINDS for step in trace.steps)
    )


def advise_and_record(
    token: str,
    world: WorldInputs,
    *,
    ledger: Ledger,
    mutes: MuteStore,
    now: int,
    rules: tuple[RuleSpec, ...] | None = None,
) -> Advice:
    """Advise over one world, then record what the run implies (CS-1268).

    The one advisor call that writes the per-world ledger. It never writes the
    mute store. Arguments are :func:`advise`'s.

    Returns:
        The advice, each reopened card resolved to ``new``, with the run's
        transitions on :attr:`Advice.completed` and :attr:`Advice.reopened`.
        ``new_world`` answers for the ledger as it stood BEFORE this run.

    Raises:
        clockspeed.advisor.ledger.StoreError: as :func:`advise` raises it, or
            the ledger could not be written.
    """
    advice = advise(token, world, ledger=ledger, mutes=mutes, now=now, rules=rules)
    completed, reopened = ledger.reconcile(
        token,
        firing={advised.card.id: advised.card.rule_id for advised in advice.cards},
        settled=settled_rules(advice.traces),
        shown_new=(advised.card.id for advised in advice.shown if advised.state.kind == "new"),
    )
    back = frozenset(reopened)
    cards = tuple(
        AdvisedCard(card=advised.card, state=CardState.new(), muted=advised.muted)
        if advised.card.id in back
        else advised
        for advised in advice.cards
    )
    return Advice(
        traces=advice.traces,
        cards=cards,
        new_world=advice.new_world,
        completed=completed,
        reopened=reopened,
    )


def advise_world(
    model: WorldModel,
    registry: Registry,
    *,
    pinned_changelist: int | None,
    ledger: Ledger,
    mutes: MuteStore,
    now: int,
) -> Advice:
    """Advise over one parsed world: inputs, rules, cards and both stores.

    The one advisor call a surface makes (CS-1270). The world token is the
    model's own header token, handed to the ledger and nowhere else.

    Args:
        model: The world model the surface holds.
        registry: The normalized registry.
        pinned_changelist: The pinned build's changelist, or None when the pin
            did not parse - the caller's, never imported here (CS-1288).
        ledger: The per-world ledger.
        mutes: The global per-rule mute store.
        now: The current instant, injected.

    Returns:
        The advice, as :func:`advise` returns it.

    Raises:
        clockspeed.advisor.ledger.StoreError: as :func:`advise` raises it.
    """
    world = inputs_of(model, registry, pinned_changelist=pinned_changelist)
    return advise(model.token, world, ledger=ledger, mutes=mutes, now=now)
