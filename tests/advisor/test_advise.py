"""CS-500 slice S6: the advise() entry point, and the RELOAD half of acceptance A3.

THE CLAIM. :func:`clockspeed.advisor.advise.advise` runs the registered rules
over one world's inputs, builds a card per firing trace with all three tiers
projected from that trace, and resolves each card against BOTH persistence
layers - the per-world ledger keyed by the save header's world token, and the
global per-rule mute. A3's reload half: a card's id AND its recorded state
survive two loads of one world through freshly constructed stores, even when
the world's numbers moved between the loads. A token the ledger has never seen
is a new world - every card ``new`` - and never a failure.

TWO LOADS OF ONE SAVE, SYNTHETICALLY. No save is read. A "load" is what the
layers below hand the advisor after reading one: the header's world token plus
the audit power balance plus the unlock state, beside the build inputs of a
save the pinned build wrote (CS-1288). The second load reuses the token
and moves the numbers, which is what a later save of the same world looks like
to this layer; the stores are rebuilt from the directory alone, which is what a
process restart looks like.

Every token is an invented 22-character literal and every number is invented.
Assertions that grade a token's absence bind the verdict to a scalar first.
"""

from __future__ import annotations

import ast
import inspect
from fractions import Fraction
from pathlib import Path

import pytest

from clockspeed.advisor import advise as advise_mod
from clockspeed.advisor import ranking
from clockspeed.advisor.advise import (
    SETTLED_STEP_KINDS,
    UNDECIDED_STEP_KINDS,
    Advice,
    AdvisedCard,
    advise,
    advise_and_record,
    settled_rules,
    world_inputs,
)
from clockspeed.advisor.cards import card_for
from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    CardState,
    Ledger,
    MuteStore,
    WorldTokenError,
)
from clockspeed.advisor.plans import PlanRequest
from clockspeed.advisor.rules import power, registered_rules
from clockspeed.advisor.rules.plan import IN_REDESIGN_UNLOCKS, RedesignUnlocks
from clockspeed.advisor.trace import (
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    StepKind,
    WorldInputs,
    run_rule,
)
from clockspeed.audit.balance import (
    WorldBalance,
    WorldClockedDraw,
    WorldDraw,
    WorldStarvation,
)
from clockspeed.data.registry import Registry
from clockspeed.data.schematics import SchematicCatalog, normalize_schematics
from clockspeed.save.world import UnlockState, WorldModel
from tests.advisor import test_plan_redesign as worlds
from tests.advisor import test_plan_world as plan_fixtures
from tests.advisor import test_world_advice as world_fixtures
from tests.advisor.build_fixtures import docs_pin, game_pin, pinned_build_inputs
from tests.data.test_schematics import schematic_document, schematic_entry

TOKEN_A = "AAAAsyntheticTokenAAAA"  # noqa: S105 - a synthetic world token, not a secret
TOKEN_B = "BBBBsyntheticTokenBBBB"  # noqa: S105 - a synthetic world token, not a secret

#: The instant every resolution here reads. Injected, never a clock.
NOW = 1000


def _balance(
    *,
    lower: Fraction,
    upper: Fraction,
    complete: bool,
    unread: int = 0,
    unmodeled: int = 0,
    considered: int = 10,
) -> WorldBalance:
    """Hand-build one synthetic audit balance."""
    draw = WorldDraw(
        contributions=(),
        gaps=(),
        consumption_megawatts=Fraction(1),
        consumption_complete=True,
        classes_considered=0,
        unmodeled_class_count=0,
        unmodeled_contributor_count=0,
        warnings=(),
    )
    clocked = WorldClockedDraw(
        contributions=(),
        gaps=(),
        lower_megawatts=lower,
        upper_megawatts=upper,
        exact=lower == upper and complete,
        complete=complete,
        machines_considered=considered,
        bounded_machine_count=0,
        unread_clock_count=unread,
        elided_clock_count=0,
        unmodeled_machine_count=unmodeled,
        warnings=(),
    )
    starvation = WorldStarvation(
        starved_indices=(),
        running_count=0,
        unconfigured_count=0,
        unknown_state_count=0,
        machines_considered=0,
        producing_available=False,
        warnings=(),
    )
    return WorldBalance(
        draw=draw,
        clocked_draw=clocked,
        starvation=starvation,
        production_available=False,
        connected_edges_available=False,
        warnings=(),
    )


def _unlocks(*schematics: str) -> UnlockState:
    return UnlockState(
        purchased_schematics=frozenset(schematics),
        recipes=frozenset(),
        current_game_phase=None,
        feature_flags={},
        scanned_resources=frozenset(),
    )


def _pinned(world: WorldInputs) -> WorldInputs:
    """The world beside the build inputs of a save the pinned build wrote (CS-1288).

    Every registered rule reads the three build inputs first, so a world
    offering none would stop every rule on ``input-missing``. The pin is read
    at test time, and :func:`advise_mod.merged_inputs` refuses a name both
    groups offer.
    """
    values = advise_mod.merged_inputs(world.values, pinned_build_inputs(game_pin()))
    return WorldInputs(values=values, unlocks=world.unlocks)


def _first_load() -> WorldInputs:
    """A world whose clocked draw has three unpriced machines: the gap rule fires."""
    balance = _balance(
        lower=Fraction(50), upper=Fraction(60), complete=False, unread=2, unmodeled=1
    )
    return _pinned(world_inputs(balance, _unlocks()))


def _second_load() -> WorldInputs:
    """The same world saved later: more machines, a moved draw, the same gap advice."""
    balance = _balance(
        lower=Fraction(71, 3),
        upper=Fraction(90),
        complete=False,
        unread=4,
        unmodeled=2,
        considered=17,
    )
    return _pinned(world_inputs(balance, _unlocks()))


def _headroom_world(generation: Fraction) -> WorldInputs:
    """A complete exact draw of 120 MW with generation supplied (CS-1059)."""
    balance = _balance(lower=Fraction(120), upper=Fraction(120), complete=True)
    values = power.balance_inputs(balance)
    values[power.IN_PRODUCTION_AVAILABLE] = InputValue(True, "synthetic.production_available")
    values[power.IN_PRODUCTION_COMPLETE] = InputValue(True, "synthetic.production_complete")
    values[power.IN_GENERATION] = InputValue(generation, "synthetic.generation")
    return _pinned(WorldInputs(values=values, unlocks=frozenset()))


def _stores(directory: Path) -> tuple[Ledger, MuteStore]:
    """Construct both stores from the directory alone - what a reload sees."""
    return Ledger(directory), MuteStore(directory)


def _run(directory: Path, token: str, world: WorldInputs) -> Advice:
    led, mutes = _stores(directory)
    return advise(token, world, ledger=led, mutes=mutes, now=NOW)


def _gap_id(advice: Advice) -> str:
    ids = [a.card.id for a in advice.cards if a.card.rule_id == power.GAP_RULE.rule_id]
    count = len(ids)
    assert count == 1, "expected exactly one gap card"
    return ids[0]


# --- the entry point ---------------------------------------------------------


def test_advise_runs_every_registered_rule_and_keeps_every_trace(tmp_path: Path) -> None:
    advice = _run(tmp_path, TOKEN_A, _first_load())
    every = [trace.rule_id for trace in advice.traces] == [s.rule_id for s in registered_rules()]
    assert every


def test_each_card_is_projected_from_its_own_trace(tmp_path: Path) -> None:
    world = _first_load()
    advice = _run(tmp_path, TOKEN_A, world)
    count = len(advice.cards)
    assert count == 1
    advised = advice.cards[0]
    direct = card_for(run_rule(power.GAP_RULE, world))
    assert direct is not None
    same = (advised.card.id, advised.card.tier1, advised.card.tier2, advised.card.tier3) == (
        direct.id,
        direct.tier1,
        direct.tier2,
        direct.tier3,
    )
    assert same
    kept = any(trace is advised.card.trace for trace in advice.traces)
    assert kept


def test_two_runs_over_one_world_render_identically(tmp_path: Path) -> None:
    first = _run(tmp_path, TOKEN_A, _first_load())
    second = _run(tmp_path, TOKEN_A, _first_load())
    render_a = [(a.card.id, a.card.tier3, a.state) for a in first.cards]
    render_b = [(a.card.id, a.card.tier3, a.state) for a in second.cards]
    assert render_a == render_b


def test_a_card_is_new_until_the_ledger_records_otherwise(tmp_path: Path) -> None:
    advice = _run(tmp_path, TOKEN_A, _first_load())
    states = [a.state for a in advice.cards]
    assert states == [CardState.new()]
    visible = [a.visible for a in advice.cards]
    assert visible == [True]


@pytest.mark.parametrize(
    ("state", "visible"),
    [
        (CardState.accepted(), True),
        (CardState.pinned(), True),
        (CardState.dismissed(), False),
        (CardState.completed(), False),
        (CardState.snoozed(NOW + 1), False),
    ],
)
def test_the_ledger_state_decides_visibility(
    tmp_path: Path, state: CardState, visible: bool
) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).set_state(TOKEN_A, gap, state)
    advice = _run(tmp_path, TOKEN_A, _first_load())
    found = [(a.state, a.visible) for a in advice.cards if a.card.id == gap]
    assert found == [(state, visible)]
    shown = [a.card.id for a in advice.shown]
    assert (gap in shown) is visible


def test_a_lapsed_snooze_reads_new_against_the_injected_now(tmp_path: Path) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).snooze(TOKEN_A, gap, until=NOW, now=NOW - 1)
    advice = _run(tmp_path, TOKEN_A, _first_load())
    found = [(a.state, a.visible) for a in advice.cards]
    assert found == [(CardState.new(), True)]


def test_a_globally_muted_rule_shows_no_card_in_any_world(tmp_path: Path) -> None:
    MuteStore(tmp_path).mute(power.GAP_RULE.rule_id)
    for token in (TOKEN_A, TOKEN_B):
        advice = _run(tmp_path, token, _first_load())
        flags = [(a.muted, a.visible) for a in advice.cards]
        assert flags == [(True, False)]
        shown = len(advice.shown)
        assert shown == 0


def test_a_mute_overrides_a_pinned_state(tmp_path: Path) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).set_state(TOKEN_A, gap, CardState.pinned())
    MuteStore(tmp_path).mute(power.GAP_RULE.rule_id)
    advice = _run(tmp_path, TOKEN_A, _first_load())
    found = [(a.state, a.muted, a.visible) for a in advice.cards]
    assert found == [(CardState.pinned(), True, False)]


def _always(rule_id: str, subject: str) -> RuleSpec:
    def _evaluate(_ctx: RuleContext) -> Recommendation:
        return Recommendation(subject_key=subject, action="Do the thing", reason="because")

    return RuleSpec(rule_id=rule_id, domain="power", inputs=(), unlocks=(), evaluate=_evaluate)


def test_shown_keeps_the_card_order_and_drops_the_hidden(tmp_path: Path) -> None:
    specs = (
        _always("synthetic.c", "s-c"),
        _always("synthetic.a", "s-a"),
        _always("synthetic.b", "s-b"),
    )
    led, mutes = _stores(tmp_path)
    first = advise(TOKEN_A, _first_load(), ledger=led, mutes=mutes, now=NOW, rules=specs)
    order = [a.card.rule_id for a in first.cards]
    assert order == ["synthetic.a", "synthetic.b", "synthetic.c"]
    middle = first.cards[1].card.id
    led.set_state(TOKEN_A, middle, CardState.dismissed())
    second = advise(TOKEN_A, _first_load(), ledger=led, mutes=mutes, now=NOW, rules=specs)
    shown = [a.card.rule_id for a in second.shown]
    assert shown == ["synthetic.a", "synthetic.c"]


def test_the_rules_argument_replaces_the_registry(tmp_path: Path) -> None:
    spec = _always("synthetic.s6", "synthetic-s6")
    led, mutes = _stores(tmp_path)
    advice = advise(TOKEN_A, _first_load(), ledger=led, mutes=mutes, now=NOW, rules=(spec,))
    ids = [a.card.rule_id for a in advice.cards]
    assert ids == ["synthetic.s6"]


def test_a_rule_that_raises_is_traced_and_skipped_never_fatal(tmp_path: Path) -> None:
    def _broken(_ctx: RuleContext) -> Recommendation:
        raise RuntimeError

    spec = RuleSpec(
        rule_id="synthetic.broken", domain="power", inputs=(), unlocks=(), evaluate=_broken
    )
    led, mutes = _stores(tmp_path)
    advice = advise(
        TOKEN_A,
        _first_load(),
        ledger=led,
        mutes=mutes,
        now=NOW,
        rules=(*registered_rules(), spec),
    )
    traced = any(trace.rule_id == "synthetic.broken" for trace in advice.traces)
    assert traced
    ids = [a.card.rule_id for a in advice.cards]
    assert ids == [power.GAP_RULE.rule_id]


def test_the_world_inputs_adapter_offers_the_balance_and_the_unlock_keys() -> None:
    balance = _balance(lower=Fraction(50), upper=Fraction(60), complete=False, unread=1)
    world = world_inputs(balance, _unlocks("/Synthetic/Schematic_TierTwo"))
    offers_balance = sorted(world.values) == sorted(power.balance_inputs(balance))
    assert offers_balance
    offers_keys = world.unlocks == frozenset({"schematic:/Synthetic/Schematic_TierTwo"})
    assert offers_keys


@pytest.mark.parametrize("function", ["inputs_of", "advise_world", "advise_world_and_record"])
def test_the_pin_is_a_required_keyword_of_every_world_entry_point(function: str) -> None:
    """CS-1288 ruling F2: the caller names the pin; the advisor never imports it.

    No default, so a surface that forgets the pin fails to call rather than
    pricing every world as uncompared; keyword-only, so it is named at every
    call. The module never imports the pin's owner, ``clockspeed.data.version``.
    """
    parameter = inspect.signature(getattr(advise_mod, function)).parameters.get("pinned_changelist")
    assert parameter is not None, function
    keyword_only = parameter.kind is inspect.Parameter.KEYWORD_ONLY
    required = parameter.default is inspect.Parameter.empty
    assert keyword_only, function
    assert required, function
    tree = ast.parse(Path(inspect.getfile(advise_mod)).read_bytes().decode("ascii"))
    imported = [
        f"{node.module}.{alias.name}" if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    ]
    pin_owner = sorted(name for name in imported if name.startswith("clockspeed.data.version"))
    assert pin_owner == []


def test_advise_never_writes_either_store(tmp_path: Path) -> None:
    _run(tmp_path, TOKEN_A, _first_load())
    written = sorted(p.name for p in tmp_path.iterdir())
    assert written == []


def test_the_advice_repr_carries_no_token_and_no_tier_text(tmp_path: Path) -> None:
    advice = _run(tmp_path, TOKEN_A, _first_load())
    rendered = repr(advice) + repr(advice.cards[0])
    leaked = TOKEN_A in rendered or advice.cards[0].card.tier1 in rendered
    assert leaked is False


def test_a_bad_token_is_refused_by_the_store_error(tmp_path: Path) -> None:
    with pytest.raises(WorldTokenError):
        _run(tmp_path, "", _first_load())


def test_the_advise_module_reads_no_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _no_clock() -> float:
        raise AssertionError

    monkeypatch.setattr("time.time", _no_clock)
    monkeypatch.setattr("time.monotonic", _no_clock)
    advice = _run(tmp_path, TOKEN_A, _first_load())
    count = len(advice.cards)
    assert count == 1
    assert not hasattr(advise_mod, "time")


# --- A3, the reload half, and A5 -------------------------------------------------


def test_a_card_id_and_its_state_survive_two_loads_of_one_save(tmp_path: Path) -> None:
    """A3 reload half: same world token, moved numbers, rebuilt stores - same card, same state."""
    first = _run(tmp_path, TOKEN_A, _first_load())
    gap = _gap_id(first)
    Ledger(tmp_path).set_state(TOKEN_A, gap, CardState.accepted())

    second = _run(tmp_path, TOKEN_A, _second_load())
    assert _gap_id(second) == gap
    found = [a.state for a in second.cards if a.card.id == gap]
    assert found == [CardState.accepted()]
    moved = first.cards[0].card.tier3 != second.cards[0].card.tier3
    assert moved, "the second load must move the numbers, or it is not a reload test"
    assert second.new_world is False


def test_a_dismissal_survives_a_reload_and_the_card_stays_hidden(tmp_path: Path) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).set_state(TOKEN_A, gap, CardState.dismissed())
    second = _run(tmp_path, TOKEN_A, _second_load())
    shown = [a.card.id for a in second.shown]
    assert gap not in shown


def test_a_mute_survives_a_reload(tmp_path: Path) -> None:
    MuteStore(tmp_path).mute(power.GAP_RULE.rule_id)
    second = _run(tmp_path, TOKEN_A, _second_load())
    flags = [a.muted for a in second.cards]
    assert flags == [True]


def test_ledger_state_does_not_cross_worlds(tmp_path: Path) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).set_state(TOKEN_A, gap, CardState.dismissed())
    other = _run(tmp_path, TOKEN_B, _first_load())
    found = [(a.card.id, a.state, a.visible) for a in other.cards]
    assert found == [(gap, CardState.new(), True)]


def test_an_unseen_world_token_is_a_new_world_never_a_failure(tmp_path: Path) -> None:
    gap = _gap_id(_run(tmp_path, TOKEN_A, _first_load()))
    Ledger(tmp_path).set_state(TOKEN_A, gap, CardState.accepted())
    fresh = _run(tmp_path, TOKEN_B, _second_load())
    assert fresh.new_world is True
    states = [a.state for a in fresh.cards]
    assert states == [CardState.new()]
    known = _run(tmp_path, TOKEN_A, _second_load())
    assert known.new_world is False


def test_an_absent_store_is_a_new_world(tmp_path: Path) -> None:
    advice = _run(tmp_path / "never-written", TOKEN_A, _first_load())
    assert advice.new_world is True
    ledger_absent = not (tmp_path / "never-written" / LEDGER_FILENAME).exists()
    mutes_absent = not (tmp_path / "never-written" / MUTES_FILENAME).exists()
    assert ledger_absent
    assert mutes_absent


def test_the_headroom_card_id_survives_a_moved_generation(tmp_path: Path) -> None:
    first = _run(tmp_path, TOKEN_A, _headroom_world(Fraction(100)))
    second = _run(tmp_path, TOKEN_A, _headroom_world(Fraction(70)))
    head_a = [a.card for a in first.cards if a.card.rule_id == power.HEADROOM_RULE.rule_id]
    head_b = [a.card for a in second.cards if a.card.rule_id == power.HEADROOM_RULE.rule_id]
    count = (len(head_a), len(head_b))
    assert count == (1, 1)
    assert head_a[0].id == head_b[0].id
    assert head_a[0].tier1 != head_b[0].tier1


# --- CS-1268: completed when advice stops firing, and the world listing ------------
#
# BOOTSTRAP.md section 5.2: ``completed`` is set automatically when the world
# state satisfies the advice, and the transition is surfaced. The read-only
# advise() cannot find a card that STOPPED firing, so the write path is
# advise_and_record(), over Ledger.reconcile() and the listing Ledger.recorded().
# The ruling filed with CS-1268 (docs/item_notes/phase5.md): a completed card
# whose rule fires again is surfaced as ``new``; a card the player set
# ``dismissed``, ``snoozed`` or ``pinned`` keeps that state. A rule "stops
# firing" when the same rule id returns no recommendation.

RULE = "synthetic.completion"
OTHER = "synthetic.steady"

WORLD = WorldInputs(values={}, unlocks=frozenset())


def _spec(rule_id: str, *, fires: bool) -> RuleSpec:
    def _evaluate(_ctx: RuleContext) -> Recommendation | None:
        if not fires:
            return None
        return Recommendation(subject_key=f"{rule_id}-s", action="Do the thing", reason="because")

    return RuleSpec(rule_id=rule_id, domain="power", inputs=(), unlocks=(), evaluate=_evaluate)


def _rules(*, fires: bool) -> tuple[RuleSpec, ...]:
    return (_spec(RULE, fires=fires), _spec(OTHER, fires=True))


def _record(directory: Path, *, fires: bool, token: str = TOKEN_A) -> Advice:
    """One load: stores rebuilt from the directory, the write path run."""
    return advise_and_record(
        token,
        WORLD,
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        rules=_rules(fires=fires),
    )


def _card_id(advice: Advice, rule_id: str) -> str:
    ids = [a.card.id for a in advice.cards if a.card.rule_id == rule_id]
    count = len(ids)
    assert count == 1
    return ids[0]


def _recorded(directory: Path, token: str = TOKEN_A) -> dict[str, CardState]:
    return dict(Ledger(directory).recorded(token))


# --- the listing ----------------------------------------------------------------


def test_the_ledger_lists_one_worlds_recorded_cards(tmp_path: Path) -> None:
    led = Ledger(tmp_path)
    led.set_state(TOKEN_A, "c-2", CardState.pinned())
    led.set_state(TOKEN_A, "c-1", CardState.accepted())
    led.snooze(TOKEN_A, "c-3", until=NOW + 5, now=NOW)
    led.set_state(TOKEN_B, "c-other", CardState.dismissed())
    listed = Ledger(tmp_path).recorded(TOKEN_A)
    assert listed == (
        ("c-1", CardState.accepted()),
        ("c-2", CardState.pinned()),
        ("c-3", CardState.snoozed(NOW + 5)),
    )


def test_an_unseen_world_lists_nothing(tmp_path: Path) -> None:
    assert Ledger(tmp_path).recorded(TOKEN_A) == ()


# --- the completed transition ---------------------------------------------------


@pytest.mark.parametrize("recorded", ["accepted", "new"])
def test_a_shown_card_whose_rule_stops_firing_is_completed_on_disk(
    tmp_path: Path, recorded: str
) -> None:
    first = _record(tmp_path, fires=True)
    card = _card_id(first, RULE)
    if recorded == "accepted":
        Ledger(tmp_path).set_state(TOKEN_A, card, CardState.accepted())
    shown = [a.card.id for a in first.shown]
    assert card in shown

    second = _record(tmp_path, fires=False)
    assert _recorded(tmp_path)[card] == CardState.completed()
    transitions = second.completed == (card,) and second.reopened == ()
    assert transitions


def test_the_steady_card_is_not_completed(tmp_path: Path) -> None:
    first = _record(tmp_path, fires=True)
    steady = _card_id(first, OTHER)
    second = _record(tmp_path, fires=False)
    assert _recorded(tmp_path)[steady] == CardState.new()
    untouched = steady not in second.completed
    assert untouched


def test_a_completed_card_whose_rule_fires_again_is_surfaced_as_new(tmp_path: Path) -> None:
    card = _card_id(_record(tmp_path, fires=True), RULE)
    _record(tmp_path, fires=False)
    again = _record(tmp_path, fires=True)
    found = [(a.state, a.visible) for a in again.cards if a.card.id == card]
    assert found == [(CardState.new(), True)]
    transitions = again.reopened == (card,) and again.completed == ()
    assert transitions
    assert _recorded(tmp_path)[card] == CardState.new()


@pytest.mark.parametrize(
    "state",
    [CardState.dismissed(), CardState.pinned(), CardState.snoozed(NOW + 1)],
)
def test_a_player_state_survives_its_rule_stopping(tmp_path: Path, state: CardState) -> None:
    card = _card_id(_record(tmp_path, fires=True), RULE)
    Ledger(tmp_path).set_state(TOKEN_A, card, state)
    second = _record(tmp_path, fires=False)
    assert _recorded(tmp_path)[card] == state
    none_completed = second.completed == ()
    assert none_completed


def test_a_lapsed_snooze_whose_rule_stops_keeps_its_snooze(tmp_path: Path) -> None:
    card = _card_id(_record(tmp_path, fires=True), RULE)
    Ledger(tmp_path).snooze(TOKEN_A, card, until=NOW, now=NOW - 1)
    _record(tmp_path, fires=False)
    assert _recorded(tmp_path)[card] == CardState.snoozed(NOW)


def test_a_muted_new_card_is_never_recorded_as_shown(tmp_path: Path) -> None:
    MuteStore(tmp_path).mute(RULE)
    card = _card_id(_record(tmp_path, fires=True), RULE)
    second = _record(tmp_path, fires=False)
    assert card not in _recorded(tmp_path)
    none_completed = second.completed == ()
    assert none_completed


def test_completion_does_not_cross_worlds(tmp_path: Path) -> None:
    card = _card_id(_record(tmp_path, fires=True), RULE)
    _record(tmp_path, fires=False, token=TOKEN_B)
    assert _recorded(tmp_path)[card] == CardState.new()
    assert card not in _recorded(tmp_path, TOKEN_B)


def test_two_runs_over_the_same_inputs_give_the_same_states(tmp_path: Path) -> None:
    def _sequence(directory: Path) -> list[tuple[object, ...]]:
        out: list[tuple[object, ...]] = []
        for fires in (True, False, False, True, True):
            advice = _record(directory, fires=fires)
            out.append(
                (
                    tuple((a.card.id, a.state) for a in advice.cards),
                    advice.completed,
                    advice.reopened,
                    Ledger(directory).recorded(TOKEN_A),
                )
            )
        return out

    left = _sequence(tmp_path / "left")
    right = _sequence(tmp_path / "right")
    assert left == right
    same_bytes = (tmp_path / "left" / "ledger.json").read_bytes() == (
        tmp_path / "right" / "ledger.json"
    ).read_bytes()
    assert same_bytes


def test_the_read_only_advise_still_writes_nothing_and_reports_no_transition(
    tmp_path: Path,
) -> None:
    led, mutes = Ledger(tmp_path), MuteStore(tmp_path)
    advice = advise(TOKEN_A, WORLD, ledger=led, mutes=mutes, now=NOW, rules=_rules(fires=True))
    no_transition = (advice.completed, advice.reopened) == ((), ())
    assert no_transition
    written = sorted(p.name for p in tmp_path.iterdir())
    assert written == []


def test_the_advice_repr_renders_transition_counts_only(tmp_path: Path) -> None:
    _record(tmp_path, fires=True)
    second = _record(tmp_path, fires=False)
    rendered = repr(second)
    leaked = second.completed[0] in rendered or TOKEN_A in rendered
    assert leaked is False


#: Each way a rule reaches no verdict, and the trace step that records it.
UNDECIDED_HOWS = {
    "raise": StepKind.RULE_ERROR,
    "missing": StepKind.INPUT_MISSING,
    "undeclared": StepKind.INPUT_REFUSED,
    "inexact": StepKind.INPUT_REFUSED,
    "locked": StepKind.PRECONDITION_UNMET,
    "indeterminate": StepKind.VERDICT_INDETERMINATE,
}

#: A world offering the read input as a float: present, but inexact.
INEXACT_WORLD = WorldInputs(
    values={"synthetic.absent": InputValue(1.5, "synthetic.source")}, unlocks=frozenset()
)


def _undecided(rule_id: str, how: str) -> RuleSpec:
    """A rule that reaches NO definite verdict: it raises, is refused, is locked or undecided."""

    def _evaluate(ctx: RuleContext) -> Recommendation | None:
        if how == "raise":
            raise RuntimeError
        if how == "indeterminate":
            ctx.indeterminate("compare the thing", "an input is a floor")
            return None
        ctx.read("synthetic.absent")
        return Recommendation(subject_key=f"{rule_id}-s", action="Do the thing", reason="because")

    inputs = ("synthetic.absent",) if how in {"missing", "inexact"} else ()
    unlocks = ("schematic:/Synthetic/Schematic_Never",) if how == "locked" else ()
    return RuleSpec(
        rule_id=rule_id, domain="power", inputs=inputs, unlocks=unlocks, evaluate=_evaluate
    )


def _world_for(how: str) -> WorldInputs:
    return INEXACT_WORLD if how == "inexact" else WORLD


@pytest.mark.parametrize("how", sorted(UNDECIDED_HOWS))
def test_each_undecided_rule_records_the_step_it_is_named_for(how: str) -> None:
    """Anti-vacuity: each arm below really ends in its own undecided step kind."""
    trace = run_rule(_undecided(RULE, how), _world_for(how))
    kinds = {step.kind for step in trace.steps}
    named = UNDECIDED_HOWS[how] in kinds and trace.recommendation is None
    assert named
    unsettled = RULE not in settled_rules((trace,))
    assert unsettled


def test_the_step_kinds_partition_into_settled_and_undecided() -> None:
    """Every StepKind is classified exactly once, so a new kind reds this test."""
    settled = frozenset(SETTLED_STEP_KINDS)
    undecided = frozenset(UNDECIDED_STEP_KINDS)
    every = frozenset(StepKind)
    partitioned = settled | undecided == every and not settled & undecided
    assert partitioned
    pinned = settled == {
        StepKind.INPUT_READ,
        StepKind.COMPUTED,
        StepKind.ALTERNATIVE_REJECTED,
        StepKind.RULE_FIRED,
    }
    assert pinned
    reached = frozenset(UNDECIDED_HOWS.values()) == undecided
    assert reached


def test_a_trace_of_settled_steps_only_is_settled() -> None:
    """Control: a clean silent run and a firing run are both definite verdicts."""
    traces = (
        run_rule(_spec(RULE, fires=False), WORLD),
        run_rule(_spec(OTHER, fires=True), WORLD),
    )
    assert settled_rules(traces) == frozenset({RULE, OTHER})


@pytest.mark.parametrize("how", [*sorted(UNDECIDED_HOWS), "not-run"])
@pytest.mark.parametrize("recorded", ["accepted", "new"])
def test_a_rule_without_a_definite_verdict_never_completes_its_card(
    tmp_path: Path, how: str, recorded: str
) -> None:
    """Non-negotiable 7: an errored, input-less or unevaluated rule says nothing."""
    card = _card_id(_record(tmp_path, fires=True), RULE)
    state = CardState.accepted() if recorded == "accepted" else CardState.new()
    if recorded == "accepted":
        Ledger(tmp_path).set_state(TOKEN_A, card, state)
    steady = _spec(OTHER, fires=True)
    rules = (steady,) if how == "not-run" else (_undecided(RULE, how), steady)
    second = advise_and_record(
        TOKEN_A,
        _world_for(how),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
        rules=rules,
    )
    assert _recorded(tmp_path)[card] == state
    none_completed = second.completed == ()
    assert none_completed


def test_an_accepted_card_keeps_its_rule_across_a_player_write(tmp_path: Path) -> None:
    """The player's accept overwrites the state, never the card's recorded rule."""
    card = _card_id(_record(tmp_path, fires=True), RULE)
    Ledger(tmp_path).set_state(TOKEN_A, card, CardState.dismissed())
    Ledger(tmp_path).set_state(TOKEN_A, card, CardState.accepted())
    second = _record(tmp_path, fires=False)
    assert _recorded(tmp_path)[card] == CardState.completed()
    completed = second.completed == (card,)
    assert completed


# ---------------------------------------------------------------------------
# CS-1246: the showing order - quick wins first, with an aging guard read from
# the ledger's shown-and-deferred record.
#
# Acceptance (docs/item_notes/phase5.md, CS-1246): "a fixture with one large
# and several small cards brings the large card to the top after the configured
# number of evaluations; the same ledger state gives the same order".
#
# The four synthetic rules below carry REAL registered rule ids, because
# clockspeed/advisor/ranking.py declares effort per rule id. Two of them are
# LARGE and they sit at OPPOSITE ends of the identity order (plan.adopt first,
# power.headroom last), so neither half of the acceptance can pass by accident:
# the unaged order has to move plan.adopt DOWN off the identity order's front,
# and the aged order has to bring power.headroom UP off its back.

#: One LARGE card that leads the identity order, two QUICK ones, and one LARGE
#: card that trails it.
RANK_LEAD_LARGE = "plan.adopt"
RANK_QUICK_ONE = "power.draw_incomplete"
RANK_QUICK_TWO = "power.fuel_demand"
RANK_TRAIL_LARGE = "power.headroom"

#: Every one of them, in the identity order cards_for gives: rule id, card id.
RANK_RULES = (RANK_LEAD_LARGE, RANK_QUICK_ONE, RANK_QUICK_TWO, RANK_TRAIL_LARGE)


def _rank_specs() -> tuple[RuleSpec, ...]:
    """Four firing rules, one per effort-bearing rule id above."""
    return tuple(_spec(rule_id, fires=True) for rule_id in RANK_RULES)


def _rank_advise(directory: Path) -> Advice:
    """One READ-ONLY load over the ranking fixture. Records nothing."""
    return advise(
        TOKEN_A,
        WORLD,
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        rules=_rank_specs(),
    )


def _rank_record(directory: Path) -> Advice:
    """One load over the ranking fixture, through the stated write path."""
    return advise_and_record(
        TOKEN_A,
        WORLD,
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        rules=_rank_specs(),
    )


def _rules_in_order(found: Advice, order: tuple[AdvisedCard, ...]) -> tuple[str, ...]:
    """The rule ids of one ordering, read back through the advice's own cards."""
    listed = {advised.card.id: advised.card.rule_id for advised in found.cards}
    return tuple(listed[advised.card.id] for advised in order)


def test_a_shown_card_that_keeps_firing_ages_by_one_evaluation_per_run(tmp_path: Path) -> None:
    """A deferral is a run the card was shown in and the player passed it over."""
    first = _rank_record(tmp_path)
    card = _card_id(first, RANK_TRAIL_LARGE)
    counts = [Ledger(tmp_path).deferrals(TOKEN_A).get(card, 0)]
    for _ in range(3):
        _rank_record(tmp_path)
        counts.append(Ledger(tmp_path).deferrals(TOKEN_A).get(card, 0))
    assert counts == [0, 1, 2, 3]


def test_the_quick_wins_lead_the_showing_order_while_nothing_has_aged(tmp_path: Path) -> None:
    """Identity order leads with a LARGE card; the showing order must not."""
    found = _rank_record(tmp_path)
    identity = _rules_in_order(found, found.cards)
    assert identity == RANK_RULES
    ranked = _rules_in_order(found, found.ranked)
    assert ranked == (RANK_QUICK_ONE, RANK_QUICK_TWO, RANK_LEAD_LARGE, RANK_TRAIL_LARGE)


def test_a_large_card_reaches_the_top_after_the_configured_evaluations(tmp_path: Path) -> None:
    """The acceptance arm: the large card the quick wins kept pushing down leads."""
    card = _card_id(_rank_record(tmp_path), RANK_TRAIL_LARGE)
    for _ in range(ranking.AGING_EVALUATIONS):
        _rank_record(tmp_path)
    reached = Ledger(tmp_path).deferrals(TOKEN_A)[card] >= ranking.AGING_EVALUATIONS
    assert reached
    found = _rank_advise(tmp_path)
    ranked = _rules_in_order(found, found.ranked)
    assert ranked == (RANK_TRAIL_LARGE, RANK_QUICK_ONE, RANK_QUICK_TWO, RANK_LEAD_LARGE)


def test_one_evaluation_short_of_the_threshold_promotes_nothing(tmp_path: Path) -> None:
    """The off-by-one fence: the guard fires AT the configured count, not before."""
    _rank_record(tmp_path)
    for _ in range(ranking.AGING_EVALUATIONS - 1):
        _rank_record(tmp_path)
    found = _rank_advise(tmp_path)
    card = _card_id(found, RANK_TRAIL_LARGE)
    short = found.deferrals[card] == ranking.AGING_EVALUATIONS - 1
    assert short
    ranked = _rules_in_order(found, found.ranked)
    assert ranked == (RANK_QUICK_ONE, RANK_QUICK_TWO, RANK_LEAD_LARGE, RANK_TRAIL_LARGE)


def test_the_same_ledger_state_gives_the_same_order(tmp_path: Path) -> None:
    """Determinism: two reads of one stored state give one order, ids and all."""
    _rank_record(tmp_path)
    _rank_record(tmp_path)
    reads = [_rank_advise(tmp_path), _rank_advise(tmp_path)]
    orders = [tuple(advised.card.id for advised in found.ranked) for found in reads]
    same = orders[0] == orders[1]
    assert same
    counts = [dict(found.deferrals) for found in reads]
    equal_counts = counts[0] == counts[1]
    assert equal_counts


def test_the_shown_order_is_the_ranked_order_without_the_hidden_cards(tmp_path: Path) -> None:
    """ranked_shown is the ranked order filtered, never a second ordering."""
    found = _rank_record(tmp_path)
    hidden = _card_id(found, RANK_QUICK_ONE)
    Ledger(tmp_path).set_state(TOKEN_A, hidden, CardState.dismissed())
    after = _rank_advise(tmp_path)
    ranked = tuple(advised.card.id for advised in after.ranked if advised.card.id != hidden)
    shown = tuple(advised.card.id for advised in after.ranked_shown)
    assert shown == ranked


def test_a_player_write_clears_the_aging_the_deferrals_had_built(tmp_path: Path) -> None:
    """The count measures deferral; acting on a card is not deferring it."""
    card = _card_id(_rank_record(tmp_path), RANK_TRAIL_LARGE)
    for _ in range(ranking.AGING_EVALUATIONS):
        _rank_record(tmp_path)
    aged = Ledger(tmp_path).deferrals(TOKEN_A)[card] >= ranking.AGING_EVALUATIONS
    assert aged
    Ledger(tmp_path).set_state(TOKEN_A, card, CardState.accepted())
    cleared = card not in Ledger(tmp_path).deferrals(TOKEN_A)
    assert cleared


def test_an_advice_built_without_deferrals_still_orders_rather_than_not_at_all() -> None:
    """The default is empty counts, never an empty order."""
    built = Advice(traces=(), cards=(), new_world=True)
    empty = dict(built.deferrals) == {}
    assert empty
    none_ranked = built.ranked == ()
    assert none_ranked


# ---------------------------------------------------------------------------
# The schematic source rides through to the plan offer (CS-1374)
# ---------------------------------------------------------------------------


class _AskedSource:
    """A schematic source that publishes nothing and records that it exists."""

    def catalog(self) -> None:
        """Publish no catalog."""


def _plan_offer_spy(seen: list[object]) -> object:
    """A stand-in for ``plan_offer_with_schematics`` that records the source it was handed."""

    def spy(*offered: object) -> dict[str, InputValue]:
        # (unlocks, registry, request, schematics): only the source is recorded.
        seen.append(offered[3])
        return {}

    return spy


def test_inputs_of_hands_its_schematic_source_to_the_plan_offer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[object] = []
    monkeypatch.setattr(advise_mod, "plan_offer_with_schematics", _plan_offer_spy(seen))
    source = _AskedSource()
    registry = worlds._three_locked_registry()  # noqa: SLF001

    advise_mod.inputs_of(
        worlds._model(()),  # noqa: SLF001
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=None,
        schematics=source,
    )
    advise_mod.inputs_of(
        worlds._model(()),  # noqa: SLF001
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=None,
    )

    # The source itself reaches it, and a call that names none hands on None.
    assert [value is source for value in seen] == [True, False]
    assert seen[1] is None


def test_advise_world_hands_its_schematic_source_on_to_inputs_of(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: list[object] = []
    monkeypatch.setattr(advise_mod, "plan_offer_with_schematics", _plan_offer_spy(seen))
    source = _AskedSource()
    ledger, mutes = _stores(tmp_path)

    advise_mod.advise_world(
        worlds._model(()),  # noqa: SLF001
        worlds._three_locked_registry(),  # noqa: SLF001
        pinned_changelist=game_pin(),
        pinned_docs_sha256=None,
        ledger=ledger,
        mutes=mutes,
        now=NOW,
        schematics=source,
    )

    assert [value is source for value in seen] == [True]


class _CatalogSource:
    """A schematic source over one tiny catalog, which counts how often it is asked."""

    def __init__(self) -> None:
        self.calls = 0

    def catalog(self) -> SchematicCatalog:
        """Publish a one-schematic catalog, and count the ask."""
        self.calls += 1
        return normalize_schematics(schematic_document([schematic_entry("Schematic_Arm_C")]))


def _unlock_reading_type(world: WorldInputs) -> type:
    """The type of the route's unlock reading a world offers, so no value is rendered."""
    return type(world.values[IN_REDESIGN_UNLOCKS].value)


def test_inputs_of_offers_the_unlock_reading_only_when_it_is_handed_a_source() -> None:
    """End to end and with no stand-in: a source reaches the reading, and none leaves it None.

    The world reads no-plan, so a route is derived and the source is the only thing that can
    make the reading exist. A call that drops the source on its way to the offer reads None.
    """
    registry = worlds._three_locked_registry()  # noqa: SLF001
    request = worlds._request(registry)  # noqa: SLF001
    model = worlds._model((worlds.HELD_STAGE,))  # noqa: SLF001
    source = _CatalogSource()

    handed = advise_mod.inputs_of(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=None,
        plan_request=request,
        schematics=source,
    )
    withheld = advise_mod.inputs_of(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=None,
        plan_request=request,
    )

    assert _unlock_reading_type(handed) is RedesignUnlocks
    assert source.calls == 1
    assert _unlock_reading_type(withheld) is type(None)


# ---------------------------------------------------------------------------
# CS-1397: advise_world_and_record - one advice ACT over a parsed world
# ---------------------------------------------------------------------------
#
# The recording door a served act reaches. It sits beside ``advise_world`` (which only
# reads), builds its inputs through the SAME private helper, calls ``advise_and_record``
# once, and re-attaches ``plan_outcome`` when a request was stated.


def _act_fixtures() -> tuple[WorldModel, Registry]:
    """A world firing one quick card, and the registry that prices its buildings."""
    return world_fixtures.gap_world(), world_fixtures.synthetic_registry()


def _act(directory: Path, *, plan_request: PlanRequest | None = None, now: int = NOW) -> Advice:
    """One act through the recording door, over the invented world and fresh stores."""
    model, registry = _act_fixtures()
    return advise_mod.advise_world_and_record(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=now,
        plan_request=plan_request,
    )


def _read(directory: Path, *, plan_request: PlanRequest | None = None) -> Advice:
    """One READ through the sibling door, over the same world and the same pin."""
    model, registry = _act_fixtures()
    return advise_mod.advise_world(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(directory),
        mutes=MuteStore(directory),
        now=NOW,
        plan_request=plan_request,
    )


def test_an_act_records_the_world_it_advised_in_the_ledger_keyed_by_its_own_token(
    tmp_path: Path,
) -> None:
    model, _registry = _act_fixtures()

    first = _act(tmp_path)

    recorded = Ledger(tmp_path).recorded(model.token)
    count = len(recorded)
    assert count == len(first.cards)
    assert count > 0
    assert first.new_world is True


def test_a_read_of_the_same_world_records_nothing(tmp_path: Path) -> None:
    _read(tmp_path)

    created = len(list(tmp_path.iterdir()))
    assert created == 0


def test_an_act_never_writes_the_mute_store(tmp_path: Path) -> None:
    _act(tmp_path)
    _act(tmp_path)

    assert not (tmp_path / MUTES_FILENAME).exists()
    assert (tmp_path / LEDGER_FILENAME).is_file()


def test_an_act_hands_the_ledger_one_reconcile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []
    real = Ledger.reconcile

    def counted(self: Ledger, *args: object, **kwargs: object) -> object:
        calls.append(1)
        return real(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Ledger, "reconcile", counted)

    _act(tmp_path)

    count = len(calls)
    assert count == 1


def test_an_acts_advice_carries_the_post_record_deferrals_the_ledger_holds(
    tmp_path: Path,
) -> None:
    model, _registry = _act_fixtures()
    _act(tmp_path)

    second = _act(tmp_path)

    same = dict(second.deferrals) == dict(Ledger(tmp_path).deferrals(model.token))
    assert same


def test_an_act_and_a_read_build_their_inputs_through_the_one_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two doors, one helper: a copy of the composition in either would drift."""
    built: list[tuple[str, object]] = []
    real = advise_mod._world_inputs_for  # noqa: SLF001

    def spy(*args: object, **kwargs: object) -> object:
        made = real(*args, **kwargs)  # type: ignore[arg-type]
        built.append((str(sorted(kwargs)), made))
        return made

    monkeypatch.setattr(advise_mod, "_world_inputs_for", spy)

    _read(tmp_path)
    _act(tmp_path)

    count = len(built)
    expected_builds = 2
    assert count == expected_builds
    assert built[0][0] == built[1][0]
    same_inputs = built[0][1] == built[1][1]
    assert same_inputs


def test_an_act_with_no_request_carries_no_plan_outcome(tmp_path: Path) -> None:
    absent = _act(tmp_path).plan_outcome is None

    assert absent


def test_an_act_with_a_stated_request_re_attaches_the_plan_outcome(tmp_path: Path) -> None:
    model = plan_fixtures._model(plan_fixtures.ASCENT_PATHS)  # noqa: SLF001
    registry = plan_fixtures._registry()  # noqa: SLF001
    request = plan_fixtures._request()  # noqa: SLF001

    found = advise_mod.advise_world_and_record(
        model,
        registry,
        pinned_changelist=game_pin(),
        pinned_docs_sha256=docs_pin(),
        ledger=Ledger(tmp_path),
        mutes=MuteStore(tmp_path),
        now=NOW,
        plan_request=request,
    )

    status = getattr(found.plan_outcome, "status", None)
    assert status == "ranked"
    recorded = len(Ledger(tmp_path).recorded(model.token))
    assert recorded == len(found.cards)
