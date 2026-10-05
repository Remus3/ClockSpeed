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
the audit power balance plus the unlock state. The second load reuses the token
and moves the numbers, which is what a later save of the same world looks like
to this layer; the stores are rebuilt from the directory alone, which is what a
process restart looks like.

Every token is an invented 22-character literal and every number is invented.
Assertions that grade a token's absence bind the verdict to a scalar first.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from clockspeed.advisor import advise as advise_mod
from clockspeed.advisor.advise import Advice, advise, advise_and_record, world_inputs
from clockspeed.advisor.cards import card_for
from clockspeed.advisor.ledger import (
    LEDGER_FILENAME,
    MUTES_FILENAME,
    CardState,
    Ledger,
    MuteStore,
    WorldTokenError,
)
from clockspeed.advisor.rules import power, registered_rules
from clockspeed.advisor.trace import (
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    WorldInputs,
    run_rule,
)
from clockspeed.audit.balance import (
    WorldBalance,
    WorldClockedDraw,
    WorldDraw,
    WorldStarvation,
)
from clockspeed.save.world import UnlockState

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


def _first_load() -> WorldInputs:
    """A world whose clocked draw has three unpriced machines: the gap rule fires."""
    balance = _balance(
        lower=Fraction(50), upper=Fraction(60), complete=False, unread=2, unmodeled=1
    )
    return world_inputs(balance, _unlocks())


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
    return world_inputs(balance, _unlocks())


def _headroom_world(generation: Fraction) -> WorldInputs:
    """A complete exact draw of 120 MW with generation supplied (CS-1059)."""
    balance = _balance(lower=Fraction(120), upper=Fraction(120), complete=True)
    values = power.balance_inputs(balance)
    values[power.IN_PRODUCTION_AVAILABLE] = InputValue(True, "synthetic.production_available")
    values[power.IN_GENERATION] = InputValue(generation, "synthetic.generation")
    return WorldInputs(values=values, unlocks=frozenset())


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


def _undecided(rule_id: str, how: str) -> RuleSpec:
    """A rule that reaches NO definite verdict: it raises, lacks input, or is locked."""

    def _evaluate(ctx: RuleContext) -> Recommendation | None:
        if how == "raise":
            raise RuntimeError
        ctx.read("synthetic.absent")
        return Recommendation(subject_key=f"{rule_id}-s", action="Do the thing", reason="because")

    inputs = ("synthetic.absent",) if how == "missing" else ()
    unlocks = ("schematic:/Synthetic/Schematic_Never",) if how == "locked" else ()
    return RuleSpec(
        rule_id=rule_id, domain="power", inputs=inputs, unlocks=unlocks, evaluate=_evaluate
    )


@pytest.mark.parametrize("how", ["raise", "missing", "locked", "not-run"])
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
        TOKEN_A, WORLD, ledger=Ledger(tmp_path), mutes=MuteStore(tmp_path), now=NOW, rules=rules
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
