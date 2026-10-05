"""CS-1270: the advisor builds its own rule inputs from a world model.

THE CLAIM. :func:`clockspeed.advisor.advise.inputs_of` takes the world model
the surface already holds plus the normalized registry and returns the
:class:`~clockspeed.advisor.trace.WorldInputs` :func:`advise` needs, composing
the audit models itself - placement, machines, network, then the power
balance. :func:`clockspeed.advisor.advise.advise_world` is the one call a
surface makes: inputs, rules, cards and both stores, keyed by the model's own
world token. The surface may not compose the audit models (CS-1189's machines
seam); the advisor is the layer that consumes audit, so the composition lives
here.

THE ORACLE IS THE AUDIT CONSTRUCTORS CALLED BY HAND. Every arm compares the
advisor's answer against ``world_inputs(balance_of(placement_of, buildings,
machines_of, network_of), unlocks)`` built in this module, so the function is
graded against the composition it claims to perform rather than against a
number transcribed from a run. Non-vacuity: one world carries a machine with
no priced draw, so the composed inputs differ from an empty world's and the
gap rule fires a card.

Every token, class name and number here is invented. No save and no install
is read; every store lives in a temporary directory and every instant is
injected.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.advisor import advise as advise_module
from clockspeed.advisor.advise import advise, advise_world, inputs_of, world_inputs
from clockspeed.advisor.ledger import CardState, Ledger, MuteStore
from clockspeed.advisor.rules import power
from clockspeed.audit.balance import balance_of
from clockspeed.audit.machines import PROPERTY_PRODUCING, machines_of
from clockspeed.audit.network import network_of
from clockspeed.audit.placement import placement_of
from clockspeed.data.registry import Registry
from clockspeed.save.world import RecordProperties, WorldModel, WorldProperties
from tests.audit import test_balance as balance_fixtures
from tests.audit import test_production as production_fixtures

if TYPE_CHECKING:
    from pathlib import Path

    from clockspeed.advisor.trace import WorldInputs
    from clockspeed.audit.balance import WorldBalance
    from clockspeed.save.world import UnlockState

#: The instant every resolution here reads. Injected, never a clock.
NOW: Final = 1000

#: A machine class no synthetic registry here prices, so its draw is a gap.
UNPRICED_MACHINE: Final = balance_fixtures.NOT_IN_REGISTRY


def synthetic_registry() -> Registry:
    """A registry whose buildings are the balance suite's whole-world set."""
    return Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=MappingProxyType(dict(balance_fixtures.whole_world_registry())),
        warnings=(),
        unknown_groups=(),
    )


def gap_world() -> WorldModel:
    """A world of one priced building and one producing machine nothing prices."""
    base = balance_fixtures.world_of(balance_fixtures.FIXED_WHOLE, UNPRICED_MACHINE)
    entries = dict(base.properties.by_record_index)
    machine_index = 1
    entries[machine_index] = replace(
        entries[machine_index],
        values=MappingProxyType({PROPERTY_PRODUCING: True}),
    )
    return replace(base, properties=WorldProperties(by_record_index=MappingProxyType(entries)))


def by_hand(model: WorldModel, registry: Registry) -> WorldInputs:
    """The composition :func:`inputs_of` claims, spelled out through the audit."""
    balance = balance_of(
        placement_of(model),
        registry.buildings,
        machines_of(model),
        network_of(model),
        generators=registry.generators,
    )
    return world_inputs(balance, model.unlocks)


def test_inputs_of_is_the_audit_composition_over_one_world() -> None:
    model = gap_world()
    registry = synthetic_registry()

    built = inputs_of(model, registry)
    expected = by_hand(model, registry)

    same_values = dict(built.values) == dict(expected.values)
    same_unlocks = built.unlocks == expected.unlocks
    assert same_values
    assert same_unlocks


def test_inputs_of_reads_the_world_rather_than_answering_a_constant() -> None:
    registry = synthetic_registry()

    gap = inputs_of(gap_world(), registry)
    empty = inputs_of(balance_fixtures.world_of(), registry)

    differs = dict(gap.values) != dict(empty.values)
    assert differs, "two different worlds produced the same inputs"


def test_the_machine_world_fixture_really_carries_a_machine() -> None:
    entry = gap_world().properties.by_record_index[1]

    assert isinstance(entry, RecordProperties)
    assert PROPERTY_PRODUCING in entry.values


def test_advise_world_equals_advise_over_the_built_inputs(tmp_path: Path) -> None:
    model = gap_world()
    registry = synthetic_registry()

    served = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )
    direct = advise(
        model.token,
        by_hand(model, registry),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    assert [a.card.id for a in served.cards] == [a.card.id for a in direct.cards]
    assert [a.card.tier3 for a in served.cards] == [a.card.tier3 for a in direct.cards]
    fired = [a.card.rule_id for a in served.cards]
    assert power.GAP_RULE.rule_id in fired


def test_advise_world_keys_the_ledger_by_the_models_own_token(tmp_path: Path) -> None:
    model = gap_world()
    registry = synthetic_registry()
    first = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )
    gap_id = next(a.card.id for a in first.cards if a.card.rule_id == power.GAP_RULE.rule_id)
    Ledger(tmp_path).set_state(model.token, gap_id, CardState.dismissed())

    again = advise_world(
        model, registry, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW
    )

    state = next(a.state.kind for a in again.cards if a.card.id == gap_id)
    assert first.new_world is True
    assert again.new_world is False
    assert state == "dismissed"


def test_advise_world_writes_no_store(tmp_path: Path) -> None:
    advise_world(
        gap_world(),
        synthetic_registry(),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
    )

    created = len(list(tmp_path.iterdir()))
    assert created == 0


# CS-1271: generated power is live through the advisor's own composition.
#
# THE CLAIM. :func:`inputs_of` hands ``balance_of`` the registry's generator
# namespace, so a built generator reaches the balance the rules read. THE
# ORACLE is ``balance_of`` called by hand WITH ``generators=registry.generators``
# over the same world; the balance :func:`inputs_of` builds is captured by a
# recording spy on :func:`world_inputs`, the one call it hands the balance to.
# Red first: omitting the keyword leaves the flag False and no figure.


def generator_registry() -> Registry:
    """A registry carrying real generator spellings in both namespaces."""
    return Registry(
        items=MappingProxyType({}),
        recipes=MappingProxyType({}),
        buildings=production_fixtures.real_consumers(),
        warnings=(),
        unknown_groups=(),
        generators=production_fixtures.real_generators(),
    )


def captured_balance(
    model: WorldModel, registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> tuple[WorldInputs, WorldBalance]:
    """Run :func:`inputs_of` and capture the balance it hands :func:`world_inputs`."""
    seen: list[WorldBalance] = []

    def spy(balance: WorldBalance, unlocks: UnlockState) -> WorldInputs:
        seen.append(balance)
        return world_inputs(balance, unlocks)

    monkeypatch.setattr(advise_module, "world_inputs", spy)
    built = inputs_of(model, registry)
    calls = len(seen)
    assert calls == 1
    return built, seen[0]


def test_inputs_of_makes_a_built_generators_capacity_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = balance_fixtures.world_of(production_fixtures.FUEL)
    registry = generator_registry()
    oracle = balance_of(
        placement_of(model),
        registry.buildings,
        machines_of(model),
        network_of(model),
        generators=registry.generators,
    )

    built, balance = captured_balance(model, registry, monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    available = balance.production_available
    assert offered is True
    assert available is True
    assert balance.production is not None
    assert oracle.production is not None
    capacity = balance.production.capacity_megawatts
    expected = oracle.production.capacity_megawatts
    exact = type(capacity) is Fraction
    assert exact
    assert capacity == expected
    assert capacity == production_fixtures.FUEL_MEGAWATTS


def test_a_registry_with_no_generator_namespace_keeps_production_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = balance_fixtures.world_of(balance_fixtures.FIXED_WHOLE)

    built, balance = captured_balance(model, synthetic_registry(), monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    assert offered is False
    assert balance.production is None


def test_a_world_with_no_built_generator_is_an_exact_zero_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MEASURED balance_of contract (CS-1059): a non-empty namespace computes a figure.

    With the registry's generator namespace supplied and no generator built,
    ``balance_of`` computes a complete production model of exactly zero, so
    the flag is True. Pinned so the behaviour is explicit, not assumed.
    """
    model = balance_fixtures.world_of()

    built, balance = captured_balance(model, generator_registry(), monkeypatch)

    offered = built.values[power.IN_PRODUCTION_AVAILABLE].value
    assert offered is True
    assert balance.production is not None
    capacity = balance.production.capacity_megawatts
    complete = balance.production.production_complete
    assert capacity == Fraction(0)
    assert complete is True
