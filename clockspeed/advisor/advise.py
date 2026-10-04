"""CS-500 slice S6: the advise() entry point - rules, cards, ledger and mutes, wired.

WHAT THIS MODULE OWNS (BOOTSTRAP.md sections 5.1 and 5.2). One call,
:func:`advise`, takes what the layers below hand the advisor after one save is
read - the header's world token and the rule inputs built from the audit and
unlock models - and returns an :class:`Advice`: every rule's trace, every card
a firing trace yields, and each card's resolution against BOTH persistence
layers. :func:`world_inputs` is the adapter from the audit power balance and
the unlock state to those inputs, :func:`inputs_of` composes that balance
from a world model and a registry through the audit constructors (CS-1270), and
:func:`advise_world` is the one call a surface makes over a world it holds.

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

READ-ONLY. :func:`advise` never writes either store; recording a state or a
mute is the caller's act through the store's own methods. ``completed`` is
not set automatically here: the ledger offers no listing of a world's
recorded cards, so the advice that STOPPED firing cannot be found from this
side yet.

SEAMS. This module consumes the audit models, the unlock state, the rule
registry and the stores. It opens no save, reads no docs file and renders
nothing on a surface. COMPOSING THE AUDIT MODELS IS THIS LAYER'S JOB (CS-1270):
the surface holds a parsed world model and a normalized registry and may not
reach the audit machines model itself (CS-1189), so :func:`inputs_of` calls
placement, machines, network and balance here, over the already-parsed model -
never over save or docs bytes. NO CLOCK: ``now`` is injected. NO LANGUAGE MODEL: every
word of every tier comes from :mod:`clockspeed.advisor.cards`.

PRIVACY. The world token is personal data. It is handed to the ledger and
held nowhere else: :class:`Advice` does not carry it, and no ``repr`` here
renders it, a tier text or an input value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.cards import Card, cards_for
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.rules import registered_rules
from clockspeed.advisor.rules.power import balance_inputs
from clockspeed.advisor.trace import RuleSpec, Trace, WorldInputs, run_rules, unlock_keys
from clockspeed.audit.balance import balance_of
from clockspeed.audit.machines import machines_of
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of

if TYPE_CHECKING:
    from clockspeed.audit.balance import WorldBalance
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import UnlockState, WorldModel

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
    """

    traces: tuple[Trace, ...]
    cards: tuple[AdvisedCard, ...]
    new_world: bool

    @property
    def shown(self) -> tuple[AdvisedCard, ...]:
        """The visible cards, in card order."""
        return tuple(advised for advised in self.cards if advised.visible)

    def __repr__(self) -> str:
        """Render counts and the new-world flag only."""
        return (
            f"Advice(traces={len(self.traces)}, cards={len(self.cards)}, "
            f"shown={len(self.shown)}, new_world={self.new_world})"
        )


def world_inputs(balance: WorldBalance, unlocks: UnlockState) -> WorldInputs:
    """Build the rule inputs for one world from its audit balance and unlock state.

    Offers every input the D4 power family reads from the balance, each sourced
    to its audit field, and the unlock key set the engine checks declared
    unlocks against. Generation is not offered: no audit model publishes it
    yet (CS-1059).
    """
    return WorldInputs(values=balance_inputs(balance), unlocks=unlock_keys(unlocks))


def inputs_of(model: WorldModel, registry: Registry) -> WorldInputs:
    """Build the rule inputs for one parsed world against one registry (CS-1270).

    Composes the audit models the power balance needs - placement, machines
    and network, each read off the model - prices them against the registry's
    buildings, and hands the balance and the model's unlock state to
    :func:`world_inputs`. Reads no file: both arguments are already parsed.

    Args:
        model: The world model the surface holds.
        registry: The normalized registry.

    Returns:
        The rule inputs.
    """
    balance = balance_of(
        placement_of(model), registry.buildings, machines_of(model), network_of(model)
    )
    return world_inputs(balance, model.unlocks)


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


def advise_world(
    model: WorldModel,
    registry: Registry,
    *,
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
        ledger: The per-world ledger.
        mutes: The global per-rule mute store.
        now: The current instant, injected.

    Returns:
        The advice, as :func:`advise` returns it.

    Raises:
        clockspeed.advisor.ledger.StoreError: as :func:`advise` raises it.
    """
    return advise(model.token, inputs_of(model, registry), ledger=ledger, mutes=mutes, now=now)
