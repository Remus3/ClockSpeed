"""Pillar 2 - the objective, the backend seam, and the C5 degenerate agreement.

WHY EVERY BACKEND HERE IS REACHED THROUGH ``select_backend``
------------------------------------------------------------
Not one test in this file constructs a backend class, and that is the point of
the file rather than a style choice. Constructing ``ExhaustiveBackend()`` and
``GreedyBackend()`` side by side proves the two backends agree; it proves
NOTHING about whether the selection mechanism works, because the mechanism is
never exercised - the CONVENTIONS.md section 7.2 unrun gate exactly. CS-G02's
gate is that an external solver later slots in WITHOUT CHANGING A CALLER, and
the only evidence for that is a caller that never names a class. So every
backend below arrives through ``select_backend``, which is what
``optimize_plan`` itself does.

WHY THE C5 CASE ASSERTS THREE THINGS AND NOT ONE
-------------------------------------------------
CLAUDE.md section 5: agreement between two agents is not evidence, because two
implementations derived from the same fixture are wrong the same way. Two
backends are the same hazard. C5 therefore carries a HAND-VERIFIED ABSOLUTE -
``C5_STD_MACHINES``, ``C5_ORE_DEMAND``, ``C5_POWER_MW``, derived in
``tests/solve/synthetic.py`` from the recipe arithmetic and not from any solver
- and the assertions are:

  1. exhaustive equals that absolute,
  2. greedy equals that absolute,
  3. exhaustive equals greedy.

The third alone would pass with both backends broken identically. The first two
carry the proof; the third catches a divergence the absolute cannot see, such
as one backend publishing a different selection for the same numbers.

WHY C5 MAKES THE AGREEMENT MEANINGFUL RATHER THAN TRIVIAL
-----------------------------------------------------------
``Alt_Gadget`` is strictly better than ``Std_Gadget`` on every objective this
module models - one machine against three, 10 Ore/min against 120, 15 MW
against 45 - and it is declared FIRST in registry order. It is also INFEASIBLE,
because it consumes an item with no producing recipe that is not a declared raw
input. So a registry-order stub picks the wrong one, and a greedy that scores
before it checks feasibility picks the wrong one too. Both wrong answers are
finite, positive and plausible. ``test_a_registry_order_stub_would_fail`` and
``test_a_score_first_stub_would_fail`` pin those two shapes as findings rather
than leaving them to review.

NO TOLERANCE, AND EQUALITY IS NOT ENOUGH ON ITS OWN
----------------------------------------------------
``tests/solve/__init__.py`` binds this file: no ``pytest.approx``, no
``math.isclose``, no epsilon. It also records why ``==`` alone is insufficient -
``Fraction(1, 2) == 0.5`` is True - so the numeric assertions here are paired
with ``audit_exact`` over the whole result and with ``type(x) is Fraction``
rather than ``isinstance``, because ``isinstance(True, int)`` is True as well.
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from clockspeed.data.registry import Registry
from clockspeed.solve import optimize
from clockspeed.solve.backends import (
    BACKEND_EXHAUSTIVE,
    BACKEND_GREEDY,
    available_backends,
    exhaustive,
)
from clockspeed.solve.backends import greedy as greedy_backend
from clockspeed.solve.backends.exhaustive import ranking_key
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    BACKEND_ENV_VAR,
    DEFAULT_BACKEND,
    EXCLUDED_LOCKED,
    MAX_EXHAUSTIVE_CANDIDATES,
    NoFeasibleSelectionError,
    Objective,
    ObjectiveUndefinedError,
    OptimizeRequest,
    OptimizeResult,
    PowerNotComparableError,
    SearchSpaceTooLargeError,
    SolveConfig,
    UnknownBackendError,
    optimize_plan,
    registry_positions,
    result_ranking_key,
    score_plan,
    select_backend,
    usable_candidates,
    weighted_objective,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    BYPRODUCT_SINKABLE,
    EXCLUDED_ZERO_DURATION,
    ExclusionNote,
    ProductionPlan,
)
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_INGREDIENTS,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)
from tests.solve.synthetic import (
    ALT_GADGET_RECIPE,
    C3_FLUID_MACHINES,
    C3_GADGET_MACHINES,
    C3_GADGET_TARGET,
    C3_ORE_DEMAND,
    C3_PLATE_MACHINES,
    C3_POWER_MW,
    C3_RECOVER_MACHINES,
    C5_ALT_MACHINES_IF_FEASIBLE,
    C5_ORE_DEMAND,
    C5_POWER_MW,
    C5_STD_MACHINES,
    C5_TRINKET_TARGET,
    C8_TWIN_PER_MACHINE,
    FLUID_RECIPE,
    GADGET_RECIPE,
    ORPHAN_RECIPE,
    PLATE_RECIPE,
    RECOVER_RECIPE,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_GADGET_ITEM,
    SOLVE_ORE_ITEM,
    SOLVE_PLATE_ITEM,
    SOLVE_RELIC_ITEM,
    SOLVE_RESIDUE_ITEM,
    SOLVE_ROD_ITEM,
    SOLVE_TRINKET_ITEM,
    SOLVE_TWIN_ITEM,
    STD_GADGET_RECIPE,
    TWIN_A_RECIPE,
    TWIN_B_RECIPE,
    ZERO_DURATION_RECIPE,
    building_path,
    registry_with,
    solve_registry,
)

# ---------------------------------------------------------------------------
# Named objectives and candidate sets, so no assertion carries a bare literal
# ---------------------------------------------------------------------------

UNIT: Fraction = Fraction(1)

MINIMIZE_RAW: Objective = weighted_objective(raw=UNIT)
MINIMIZE_POWER: Objective = weighted_objective(power=UNIT)
MINIMIZE_BUILDINGS: Objective = weighted_objective(buildings=UNIT)
MINIMIZE_EVERYTHING: Objective = weighted_objective(raw=UNIT, power=UNIT, buildings=UNIT)

BOTH_BACKENDS: tuple[str, ...] = (BACKEND_EXHAUSTIVE, BACKEND_GREEDY)

C5_CANDIDATES: tuple[str, ...] = (ALT_GADGET_RECIPE, STD_GADGET_RECIPE)
C3_CANDIDATES: tuple[str, ...] = (GADGET_RECIPE, RECOVER_RECIPE, FLUID_RECIPE, PLATE_RECIPE)
C8_CANDIDATES: tuple[str, ...] = (TWIN_B_RECIPE, TWIN_A_RECIPE)

#: One objective per direction ``optimize.OBJECTIVES`` names. Spelled out rather
#: than derived from that tuple, so adding a fourth direction reddens this file
#: instead of silently widening every parametrization that reads it.
EACH_OBJECTIVE: tuple[Objective, ...] = (MINIMIZE_RAW, MINIMIZE_POWER, MINIMIZE_BUILDINGS)

#: Every objective shape the C8 tie is asked under - one per direction, plus the
#: combination the arm this replaced used when it ran on one backend only.
C8_OBJECTIVES: tuple[Objective, ...] = (*EACH_OBJECTIVE, MINIMIZE_EVERYTHING)

LOCKED_ALTERNATE: ExclusionNote = ExclusionNote(
    recipe_key=ALT_GADGET_RECIPE, reason=EXCLUDED_LOCKED
)

#: A recipe with a real duration and NO automated producer. Built here rather
#: than added to ``tests/solve/synthetic.py``, which is not this slice's to
#: edit. The corpus's own zero-duration build-gun recipe cannot stand in: pillar
#: 2 drops a zero-duration candidate at the door, so it never reaches the power
#: objective at all. This one solves perfectly well and simply has no building
#: to read a draw from.
NO_PRODUCER_RECIPE: str = "R_NoProducer"

#: Filler for the search-space cap. Each is a distinct ClassName producing an
#: item that already has a descriptor, so the variant registry still builds.
PADDING_PREFIX: str = "R_Pad"

_SOURCE_FILES: tuple[tuple[str, ...], ...] = (
    ("clockspeed", "solve", "bound.py"),
    ("clockspeed", "solve", "optimize.py"),
    ("clockspeed", "solve", "backends", "__init__.py"),
    ("clockspeed", "solve", "backends", "exhaustive.py"),
    ("clockspeed", "solve", "backends", "greedy.py"),
)


def _recipe_entry(class_name: str, product: str, building: str | None) -> dict[str, str]:
    """Build one recipe entry as docs text, in the grammar the corpus uses.

    Args:
        class_name: The entry's ClassName.
        product: The item ClassName it produces, one per cycle.
        building: The producing building ClassName, or None for no automated
            producer - which is the shape the power objective cannot price.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: "6.000000",
        KEY_INGREDIENTS: amount_blob([(SOLVE_ORE_ITEM, 1)]),
        KEY_PRODUCT: amount_blob([(product, 1)]),
        KEY_PRODUCED_IN: class_path_blob([building_path(building)] if building else []),
    }


def _request(backend: str | None, **overrides: Any) -> OptimizeRequest:
    """Build a request from the C5 shape, with named fields replaced.

    Args:
        backend: The backend name for the config, or None to leave it unstated.
        **overrides: Fields to replace.

    Returns:
        The request.
    """
    base = OptimizeRequest(
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: C5_TRINKET_TARGET}),
        candidates=C5_CANDIDATES,
        unlocked=C5_CANDIDATES,
        raw_items=(SOLVE_ORE_ITEM,),
        byproduct_policy=BYPRODUCT_BALANCED,
        objective=MINIMIZE_EVERYTHING,
        config=SolveConfig(backend=backend),
    )
    return replace(base, **overrides) if overrides else base


def _c3_request(backend: str, **overrides: Any) -> OptimizeRequest:
    """Build the C3 byproduct-loop request.

    BYPRODUCT_BALANCED on purpose. Under ``sinkable`` the subset that drops
    ``R_Recover`` and vents the residue is ALSO feasible, and it wins on
    machines and on power while losing on ore - so the answer would depend on
    the objective and would stop being the fixture's published C3 figures. Under
    ``balanced`` the residue balance forces that subset to zero machines, and
    the four-recipe loop is the only feasible member of the whole space.

    Args:
        backend: The backend name for the config.
        **overrides: Fields to replace.

    Returns:
        The request.
    """
    fields: dict[str, Any] = {
        "targets": MappingProxyType({SOLVE_GADGET_ITEM: C3_GADGET_TARGET}),
        "candidates": C3_CANDIDATES,
        "unlocked": C3_CANDIDATES,
        "objective": MINIMIZE_RAW,
    }
    fields.update(overrides)
    return _request(backend, **fields)


def _c8_request(backend: str | None, objective: Objective) -> OptimizeRequest:
    """Build the C8 twin request - two recipes nothing in any objective tells apart.

    Args:
        backend: The backend name for the config, or None to leave it unstated.
        objective: What to minimize.

    Returns:
        The request. The target is one twin's whole per-machine output, so the
        answer is one machine of whichever twin the tie-break names.
    """
    return _request(
        backend,
        targets=MappingProxyType({SOLVE_TWIN_ITEM: C8_TWIN_PER_MACHINE}),
        candidates=C8_CANDIDATES,
        unlocked=C8_CANDIDATES,
        objective=objective,
    )


def _machines(plan: ProductionPlan) -> dict[str, Fraction]:
    """Index a plan's machine counts by recipe key.

    Args:
        plan: The plan.

    Returns:
        Recipe key to machine count.
    """
    return {step.recipe_key: step.machines for step in plan.steps}


def _run(registry: Registry, request: OptimizeRequest) -> OptimizeResult:
    """Run the optimizer the way a caller does - through the seam, naming no class.

    Args:
        registry: The registry to solve against.
        request: The request, whose config names the backend.

    Returns:
        The result.
    """
    return optimize_plan(registry, request)


# ===========================================================================
# a. C5 - the degenerate case, and its three assertions
# ===========================================================================


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c5_matches_the_hand_verified_absolute(backend: str) -> None:
    result = _run(solve_registry(), _request(backend))

    assert result.selection == (STD_GADGET_RECIPE,)
    assert _machines(result.plan) == {STD_GADGET_RECIPE: C5_STD_MACHINES}
    assert result.plan.raw_inputs[SOLVE_ORE_ITEM] == C5_ORE_DEMAND
    assert result.plan.targets[SOLVE_TRINKET_ITEM] == C5_TRINKET_TARGET


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c5_never_selects_the_infeasible_alternate(backend: str) -> None:
    result = _run(solve_registry(), _request(backend))

    assert ALT_GADGET_RECIPE not in result.selection
    assert ALT_GADGET_RECIPE not in _machines(result.plan)


def test_c5_the_two_backends_produce_structurally_identical_plans() -> None:
    registry = solve_registry()

    exhaustive = _run(registry, _request(BACKEND_EXHAUSTIVE))
    greedy = _run(registry, _request(BACKEND_GREEDY))

    assert exhaustive.plan == greedy.plan
    assert exhaustive.selection == greedy.selection
    assert exhaustive.score == greedy.score
    assert exhaustive.backend != greedy.backend


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c5_result_is_exact_end_to_end(backend: str) -> None:
    result = _run(solve_registry(), _request(backend))

    audit_exact(result, path="result")
    for step in result.plan.steps:
        assert type(step.machines) is Fraction
    assert type(result.score) is Fraction
    assert type(result.plan.raw_inputs[SOLVE_ORE_ITEM]) is Fraction


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c5_power_is_priced_at_the_unsharded_base(backend: str) -> None:
    result = _run(solve_registry(), _request(backend, objective=MINIMIZE_POWER))

    assert result.score == C5_POWER_MW
    assert type(result.score) is Fraction


def test_a_registry_order_stub_would_fail() -> None:
    """The first candidate in registry order is the WRONG answer, so order cannot decide."""
    registry = solve_registry()
    order = [key for key in registry.recipes if key in C5_CANDIDATES]

    assert order[0] == ALT_GADGET_RECIPE
    assert _run(registry, _request(BACKEND_EXHAUSTIVE)).selection != (order[0],)


def test_a_score_first_stub_would_fail() -> None:
    """The infeasible alternate wins on every objective, so scoring cannot decide either."""
    result = _run(solve_registry(), _request(BACKEND_GREEDY, objective=MINIMIZE_BUILDINGS))

    assert C5_ALT_MACHINES_IF_FEASIBLE < C5_STD_MACHINES
    assert result.score == C5_STD_MACHINES


# ===========================================================================
# b. C3 - the byproduct loop, where the two mechanisms take different paths
# ===========================================================================


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c3_loop_matches_the_fixtures_published_answer(backend: str) -> None:
    result = _run(solve_registry(), _c3_request(backend))

    assert _machines(result.plan) == {
        GADGET_RECIPE: C3_GADGET_MACHINES,
        RECOVER_RECIPE: C3_RECOVER_MACHINES,
        FLUID_RECIPE: C3_FLUID_MACHINES,
        PLATE_RECIPE: C3_PLATE_MACHINES,
    }
    assert result.plan.raw_inputs[SOLVE_ORE_ITEM] == C3_ORE_DEMAND
    assert result.score == C3_ORE_DEMAND


def test_c3_the_two_backends_agree_on_the_loop() -> None:
    registry = solve_registry()

    exhaustive = _run(registry, _c3_request(BACKEND_EXHAUSTIVE))
    greedy = _run(registry, _c3_request(BACKEND_GREEDY))

    assert exhaustive.plan == greedy.plan
    assert exhaustive.selection == greedy.selection


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_c3_power_total_matches_the_fixture(backend: str) -> None:
    registry = solve_registry()
    result = _run(registry, _c3_request(backend))

    assert score_plan(registry, result.plan, MINIMIZE_POWER) == C3_POWER_MW


def test_greedy_finds_the_loop_from_the_whole_corpus() -> None:
    """The reachability prune, on a candidate set far wider than the answer."""
    registry = solve_registry()
    candidates = tuple(registry.recipes)

    result = _run(registry, _c3_request(BACKEND_GREEDY, candidates=candidates, unlocked=candidates))

    assert set(result.selection) == set(C3_CANDIDATES)


# ===========================================================================
# c. The selection mechanism - precedence, and a refusal that never falls back
# ===========================================================================


def test_available_backends_names_both_shipped_backends() -> None:
    names = available_backends()

    assert BACKEND_EXHAUSTIVE in names
    assert BACKEND_GREEDY in names
    assert DEFAULT_BACKEND in names
    assert names == tuple(sorted(names))


def test_override_argument_beats_the_config_and_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_EXHAUSTIVE)

    backend = select_backend(SolveConfig(backend=BACKEND_EXHAUSTIVE), override=BACKEND_GREEDY)

    assert backend.name == BACKEND_GREEDY


def test_config_beats_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_EXHAUSTIVE)

    assert select_backend(SolveConfig(backend=BACKEND_GREEDY)).name == BACKEND_GREEDY


def test_the_environment_beats_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(BACKEND_ENV_VAR, BACKEND_GREEDY)

    assert select_backend(SolveConfig()).name == BACKEND_GREEDY


def test_the_default_applies_when_nothing_states_a_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)

    assert select_backend(SolveConfig()).name == DEFAULT_BACKEND


def test_an_empty_environment_value_reads_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(BACKEND_ENV_VAR, "")

    assert select_backend(SolveConfig()).name == DEFAULT_BACKEND


@pytest.mark.parametrize("bad", ["exhausitve", "EXHAUSTIVE", "lp", " greedy"])
def test_an_unknown_override_refuses_and_never_falls_back(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)

    with pytest.raises(UnknownBackendError) as caught:
        select_backend(SolveConfig(), override=bad)

    assert bad in str(caught.value)
    assert DEFAULT_BACKEND in str(caught.value)


def test_an_unknown_config_backend_refuses_and_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(BACKEND_ENV_VAR, raising=False)

    with pytest.raises(UnknownBackendError):
        select_backend(SolveConfig(backend="branch-and-bound"))


def test_an_unknown_environment_backend_refuses_and_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(BACKEND_ENV_VAR, "simplex")

    with pytest.raises(UnknownBackendError):
        select_backend(SolveConfig())


def test_a_typo_in_the_environment_does_not_silently_produce_a_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole reason a fallback is forbidden: a typo must be a finding, not a plan."""
    monkeypatch.setenv(BACKEND_ENV_VAR, "exhaustve")

    with pytest.raises(UnknownBackendError):
        _run(solve_registry(), _request(None))


def test_swapping_the_backend_changes_no_caller(monkeypatch: pytest.MonkeyPatch) -> None:
    """CS-G02's actual gate: one call site, two backends, one answer."""
    registry = solve_registry()
    request = _request(None)
    plans = []

    for name in BOTH_BACKENDS:
        monkeypatch.setenv(BACKEND_ENV_VAR, name)
        plans.append(_run(registry, request).plan)

    assert plans[0] == plans[1]


# ===========================================================================
# d. Determinism
# ===========================================================================


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_two_runs_on_one_input_are_byte_identical(backend: str) -> None:
    registry = solve_registry()
    request = _c3_request(backend)

    assert repr(_run(registry, request)) == repr(_run(registry, request))


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_candidate_order_and_duplicates_do_not_move_the_answer(backend: str) -> None:
    registry = solve_registry()
    straight = _run(registry, _c3_request(backend))
    permuted = tuple(reversed(C3_CANDIDATES)) + C3_CANDIDATES

    shuffled = _run(
        registry,
        _c3_request(backend, candidates=permuted, unlocked=tuple(reversed(C3_CANDIDATES))),
    )

    assert repr(shuffled) == repr(straight)


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_the_selection_is_published_in_registry_order(backend: str) -> None:
    registry = solve_registry()

    result = _run(registry, _c3_request(backend, candidates=tuple(reversed(C3_CANDIDATES))))

    assert list(result.selection) == [key for key in registry.recipes if key in result.selection]
    assert result.selection == tuple(step.recipe_key for step in result.plan.steps)


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
@pytest.mark.parametrize("objective", C8_OBJECTIVES)
def test_both_backends_break_a_tie_with_the_same_documented_key(
    objective: Objective, backend: str
) -> None:
    """C8's twins are identical in every objective, so only a stated rule decides.

    Widened from an exhaustive-only arm. It is not evidence of a behaviour
    change - both backends already answered this way under every objective - and
    that is the point: the CONTRACT is that one key decides a tie everywhere,
    and an arm on one backend leaves the other free to drift. The assertion is
    the hand-derived absolute rather than backend agreement, for the reason this
    file's docstring records for C5: two backends broken identically agree.
    """
    result = _run(solve_registry(), _c8_request(backend, objective))

    assert result.selection == (TWIN_A_RECIPE,)


def test_the_key_is_published_by_the_layer_that_documents_it() -> None:
    """One owner. The module whose docstring argues the rule is the one exporting it."""
    assert "ranking_key" in optimize.__all__
    assert "result_ranking_key" in optimize.__all__
    assert "registry_positions" in optimize.__all__


def test_the_backend_re_export_is_the_owner_s_function_and_not_a_copy() -> None:
    """``in __all__`` on both modules would also pass on two drifting definitions."""
    assert exhaustive.ranking_key is optimize.ranking_key
    assert "ranking_key" in exhaustive.__all__


# --- the tie-break rule itself ---------------------------------------------
#
# Tested at the selector rather than through a backend run, on the same
# reasoning tests/solve/test_exact.py records for _pivot_row: the rule is
# INVISIBLE in the backend's output. The key is unique per canonical selection
# and the mask enumeration is deterministic, so a score-only rule computes the
# same winner on every fixture this project can build - which means an
# end-to-end test of it can only ever pass. The rule still matters, because
# "whichever mask came first" is an implementation detail a REPLACEMENT backend
# cannot reproduce, and two backends would then disagree on ties.


#: Positions for the arms below. Strictly increasing, which is the one property
#: ``ranking_key`` documents as required, and named rather than real recipe keys
#: so an arm about the RULE cannot be read as an arm about the fixture.
STUB_POSITIONS: dict[str, int] = {"first": 0, "second": 1, "third": 2}


def _ranked(selection: tuple[str, ...], score: Fraction) -> tuple[Fraction, tuple[int, ...]]:
    """Build a ranking key from a selection and a score, with fixed positions.

    Args:
        selection: Recipe keys in registry order.
        score: The objective value.

    Returns:
        The ranking key.
    """
    return ranking_key(score, selection, STUB_POSITIONS)


def _result(selection: tuple[str, ...], score: Fraction) -> OptimizeResult:
    """Build a result carrying nothing but the two fields the key reads.

    Args:
        selection: Recipe keys in registry order.
        score: The objective value.

    Returns:
        The result. Its plan is empty - ``result_ranking_key`` reads ``score``
        and ``selection`` and nothing else, and an arm that needed a real plan
        would be an arm about the solver.
    """
    plan = ProductionPlan(
        steps=(),
        targets=MappingProxyType({}),
        raw_inputs=MappingProxyType({}),
        byproducts=MappingProxyType({}),
        excluded=(),
        byproduct_policy=BYPRODUCT_BALANCED,
    )
    return OptimizeResult(
        backend=BACKEND_EXHAUSTIVE,
        selection=selection,
        plan=plan,
        score=score,
        objective=MINIMIZE_RAW,
        excluded=(),
    )


def test_the_ranking_key_puts_the_score_ahead_of_every_position() -> None:
    assert _ranked(("third",), Fraction(1)) < _ranked(("first",), Fraction(2))


def test_the_ranking_key_breaks_a_tie_by_registry_position() -> None:
    tied = Fraction(7)

    assert _ranked(("first",), tied) < _ranked(("second",), tied)
    assert _ranked(("first", "second"), tied) < _ranked(("second", "third"), tied)


def test_the_ranking_key_prefers_the_smaller_of_two_tied_selections() -> None:
    tied = Fraction(7)

    assert _ranked(("first",), tied) < _ranked(("first", "second"), tied)


def test_the_ranking_key_is_exact_and_carries_no_float() -> None:
    key = _ranked(("first",), Fraction(1, 3))

    assert type(key[0]) is Fraction
    assert key[1] == (0,)


def test_the_result_shaped_key_reads_the_result_own_score_and_selection() -> None:
    """The wrapper a backend calls, so its call site cannot pass the two apart."""
    result = _result(("second",), Fraction(1, 3))

    key = result_ranking_key(result, STUB_POSITIONS)

    assert key == ranking_key(result.score, result.selection, STUB_POSITIONS)
    assert type(key[0]) is Fraction
    assert key[1] == (1,)


def test_the_ranking_key_order_is_invariant_under_an_order_preserving_reindexing() -> None:
    """Any mapping monotone in registry order picks the same winner.

    The documented licence for ``exhaustive.py`` passing its usable-candidate
    index while a later ladder passes :func:`registry_positions`: the two
    mappings disagree on every VALUE and agree on every ORDER, and the position
    tuple decides only a tie, so only the order can be observed.
    """
    registry = solve_registry()
    usable, _ = usable_candidates(registry, _c8_request(BACKEND_EXHAUSTIVE, MINIMIZE_RAW))
    candidate_index = {key: index for index, key in enumerate(usable)}
    whole_registry = registry_positions(registry)
    tied = Fraction(7)

    assert candidate_index != dict(whole_registry)
    # Each row carries the EXPECTED sign as well, so an implementation that
    # dropped the position half entirely - making both sides False and the two
    # equal - is red rather than vacuously green.
    for left, right, expected in (
        ((TWIN_A_RECIPE,), (TWIN_B_RECIPE,), True),
        ((TWIN_B_RECIPE,), (TWIN_A_RECIPE,), False),
        ((TWIN_A_RECIPE,), (TWIN_A_RECIPE, TWIN_B_RECIPE), True),
    ):
        narrow = ranking_key(tied, left, candidate_index) < ranking_key(
            tied, right, candidate_index
        )
        wide = ranking_key(tied, left, whole_registry) < ranking_key(tied, right, whole_registry)

        assert narrow == expected, f"{left} vs {right} is wrong under the candidate index"
        assert wide == expected, f"{left} vs {right} reorders under a reindexing"


# ===========================================================================
# e. The door - what is unlocked, and what cannot be used at all
# ===========================================================================


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_a_locked_candidate_is_excluded_with_a_reason(backend: str) -> None:
    result = _run(solve_registry(), _request(backend, unlocked=(STD_GADGET_RECIPE,)))

    assert result.excluded == (LOCKED_ALTERNATE,)
    assert result.selection == (STD_GADGET_RECIPE,)


def test_locking_the_only_feasible_recipe_refuses_rather_than_answering() -> None:
    with pytest.raises(NoFeasibleSelectionError):
        _run(solve_registry(), _request(BACKEND_EXHAUSTIVE, unlocked=(ALT_GADGET_RECIPE,)))


def test_a_zero_duration_candidate_is_dropped_at_the_door() -> None:
    registry = solve_registry()
    candidates = (PLATE_RECIPE, ZERO_DURATION_RECIPE)
    request = _request(
        BACKEND_EXHAUSTIVE,
        targets=MappingProxyType({SOLVE_PLATE_ITEM: Fraction(30)}),
        candidates=candidates,
        unlocked=candidates,
        objective=MINIMIZE_RAW,
    )

    usable, excluded = usable_candidates(registry, request)

    assert usable == (PLATE_RECIPE,)
    assert [note.reason for note in excluded] == [EXCLUDED_ZERO_DURATION]
    assert _run(registry, request).selection == (PLATE_RECIPE,)


def test_an_unreachable_chain_refuses_rather_than_returning_an_empty_plan() -> None:
    """C7: the orphan ingredient is produced by nothing and is not raw."""
    request = _request(
        BACKEND_EXHAUSTIVE,
        targets=MappingProxyType({SOLVE_RELIC_ITEM: Fraction(10)}),
        candidates=(ORPHAN_RECIPE,),
        unlocked=(ORPHAN_RECIPE,),
        objective=MINIMIZE_RAW,
    )

    with pytest.raises(NoFeasibleSelectionError):
        _run(solve_registry(), request)


def test_an_unknown_candidate_is_a_caller_bug_and_not_a_refusal() -> None:
    with pytest.raises(ValueError, match="does not model"):
        _run(solve_registry(), _request(BACKEND_EXHAUSTIVE, candidates=("R_Nope",)))


def test_the_exhaustive_search_space_is_capped_rather_than_left_to_hang() -> None:
    padding = [
        _recipe_entry(f"{PADDING_PREFIX}{index}", SOLVE_ROD_ITEM, SOLVE_ASSEMBLER_BUILDING)
        for index in range(MAX_EXHAUSTIVE_CANDIDATES + 1)
    ]
    registry = registry_with(add=padding)
    candidates = tuple(key for key in registry.recipes if key.startswith(PADDING_PREFIX))
    request = _request(
        BACKEND_EXHAUSTIVE,
        targets=MappingProxyType({SOLVE_ROD_ITEM: Fraction(10)}),
        candidates=candidates,
        unlocked=candidates,
        objective=MINIMIZE_RAW,
    )

    assert len(candidates) > MAX_EXHAUSTIVE_CANDIDATES

    with pytest.raises(SearchSpaceTooLargeError) as caught:
        _run(registry, request)

    assert str(MAX_EXHAUSTIVE_CANDIDATES) in str(caught.value)


# ===========================================================================
# f. Objectives
# ===========================================================================


def test_an_objective_with_no_weight_at_all_is_refused() -> None:
    with pytest.raises(ObjectiveUndefinedError):
        weighted_objective()


@pytest.mark.parametrize("weight", [Fraction(0), Fraction(-1)])
def test_a_non_positive_weight_is_refused(weight: Fraction) -> None:
    with pytest.raises(ObjectiveUndefinedError):
        weighted_objective(raw=weight)


def test_an_inexact_weight_is_refused() -> None:
    with pytest.raises(ObjectiveUndefinedError):
        weighted_objective(raw=1)  # type: ignore[arg-type]


def test_an_unknown_objective_name_is_refused() -> None:
    registry = solve_registry()
    plan = _run(registry, _request(BACKEND_EXHAUSTIVE)).plan

    with pytest.raises(ObjectiveUndefinedError):
        score_plan(registry, plan, Objective(weights=MappingProxyType({"minimize-belts": UNIT})))


def test_weights_combine_exactly_rather_than_by_the_largest_term() -> None:
    registry = solve_registry()
    plan = _run(registry, _request(BACKEND_EXHAUSTIVE)).plan
    combined = weighted_objective(raw=Fraction(1, 3), power=Fraction(2), buildings=Fraction(5))

    scored = score_plan(registry, plan, combined)

    assert scored == C5_ORE_DEMAND / 3 + C5_POWER_MW * 2 + C5_STD_MACHINES * 5
    assert type(scored) is Fraction


def test_each_objective_is_individually_selectable() -> None:
    registry = solve_registry()
    plan = _run(registry, _request(BACKEND_EXHAUSTIVE)).plan

    assert score_plan(registry, plan, MINIMIZE_RAW) == C5_ORE_DEMAND
    assert score_plan(registry, plan, MINIMIZE_POWER) == C5_POWER_MW
    assert score_plan(registry, plan, MINIMIZE_BUILDINGS) == C5_STD_MACHINES


def test_power_that_cannot_be_compared_refuses_instead_of_scoring_zero() -> None:
    registry = registry_with(add=[_recipe_entry(NO_PRODUCER_RECIPE, SOLVE_TRINKET_ITEM, None)])
    request = _request(
        BACKEND_EXHAUSTIVE,
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: Fraction(10)}),
        candidates=(NO_PRODUCER_RECIPE,),
        unlocked=(NO_PRODUCER_RECIPE,),
        objective=MINIMIZE_POWER,
    )

    with pytest.raises(PowerNotComparableError, match=NO_PRODUCER_RECIPE):
        _run(registry, request)


def test_an_unpriceable_building_does_not_poison_an_objective_that_ignores_power() -> None:
    registry = registry_with(add=[_recipe_entry(NO_PRODUCER_RECIPE, SOLVE_TRINKET_ITEM, None)])
    request = _request(
        BACKEND_EXHAUSTIVE,
        targets=MappingProxyType({SOLVE_TRINKET_ITEM: Fraction(10)}),
        candidates=(NO_PRODUCER_RECIPE,),
        unlocked=(NO_PRODUCER_RECIPE,),
        objective=MINIMIZE_BUILDINGS,
    )

    assert _run(registry, request).selection == (NO_PRODUCER_RECIPE,)


# ===========================================================================
# g. The static fence - no inexact construct anywhere in the slice
#
# Over the AST rather than over the text. A text scan for "**" cannot tell the
# power operator from markdown emphasis in a docstring, and every module in this
# project uses the latter; a scan for "float(" cannot tell a call from the word
# inside a sentence. Both directions of that error matter - the false positive
# makes the fence unmaintainable, and the false negative is the one that ships.
# ===========================================================================


def _tree(parts: tuple[str, ...]) -> ast.Module:
    """Parse one of this slice's modules.

    Args:
        parts: Path components relative to the repository root.

    Returns:
        The parsed module.
    """
    root = Path(__file__).resolve().parents[2]
    return ast.parse(root.joinpath(*parts).read_text(encoding="ascii"))


@pytest.mark.parametrize("parts", _SOURCE_FILES)
def test_no_module_in_this_slice_uses_the_power_operator(parts: tuple[str, ...]) -> None:
    """Fraction raised to the shipped exponent returns a FLOAT, silently."""
    operators = [node for node in ast.walk(_tree(parts)) if isinstance(node, ast.Pow)]

    assert operators == [], f"{parts[-1]} uses the power operator"


@pytest.mark.parametrize("parts", _SOURCE_FILES)
def test_no_module_in_this_slice_calls_an_inexact_builtin(parts: tuple[str, ...]) -> None:
    banned = {"pow", "float", "complex", "round"}
    called = {
        node.func.id
        for node in ast.walk(_tree(parts))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert called & banned == set(), f"{parts[-1]} calls {sorted(called & banned)}"


@pytest.mark.parametrize("parts", _SOURCE_FILES)
def test_no_module_in_this_slice_imports_an_inexact_library(parts: tuple[str, ...]) -> None:
    banned = {"math", "statistics", "decimal", "numpy"}
    imported: set[str] = set()

    for node in ast.walk(_tree(parts)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert imported & banned == set(), f"{parts[-1]} imports {sorted(imported & banned)}"


@pytest.mark.parametrize("parts", _SOURCE_FILES)
def test_no_module_in_this_slice_carries_a_float_literal(parts: tuple[str, ...]) -> None:
    literals = [
        node.value
        for node in ast.walk(_tree(parts))
        if isinstance(node, ast.Constant) and type(node.value) is float
    ]

    assert literals == [], f"{parts[-1]} carries float literals {literals}"


# ===========================================================================
# h. CS-1347 - greedy returns the lowest-ranking selection its walk REACHED
# ===========================================================================
#
# THE FIXTURE, DERIVED BY HAND. Two recipes join the corpus through
# registry_with, beside C1's R_Plate (1 Ore -> 1 Plate, 2 s: Ore -30 and
# Plate +30 per machine per minute). Both run 4 s, so 15 cycles a minute, and
# Residue is RF_LIQUID, so its 1000 L on the wire is 1 cubic metre a cycle:
#
#   R_ScrapRod  1 Plate -> 1 Rod + 1000 L Residue   Plate -15, Rod +15, Residue +15
#   R_Reclaim   2000 L Residue -> 1 Plate           Residue -30, Plate +15
#
# Target 30 Rod/min, byproducts SINKABLE, minimize raw. With p, s and r the
# machine counts of R_Plate, R_ScrapRod and R_Reclaim:
#
#   {R_Plate, R_ScrapRod}             Rod 15s = 30 -> s = 2; Plate 30p - 30 = 0
#                                     -> p = 1; Residue vented at 30   Ore 30
#   {R_Plate, R_ScrapRod, R_Reclaim}  s = 2; Residue 30 - 30r = 0 -> r = 1;
#                                     Plate 30p - 30 + 15 = 0 -> p = 1/2  Ore 15
#
# No other subset solves. R_ScrapRod is the only Rod producer, and without
# R_Plate the Plate balance -15s + 15r = 0 and the Residue balance 15s - 30r = 0
# contradict each other at s = 2.
#
# THE WALK, DERIVED BY HAND. Round 0: only R_ScrapRod probes feasible - the
# other two produce no Rod. Round 1: R_ScrapRod alone does not solve, since
# nothing makes Plate, and of the two additions only R_Plate probes feasible,
# by the contradiction above. Round 2: {R_Plate, R_ScrapRod} SOLVES at Ore 30.
# That is the first selection the walk reaches that solves, and it is what the
# walk used to return. R_Reclaim then probes feasible, and round 3's
# three-recipe selection solves at Ore 15. So the first solve is NOT the
# lowest-ranking selection the walk reached, and a walk that returns at its
# first solve answers 30 where 15 is right - which is what makes the arms below
# non-vacuous rather than a re-run of C3, where the two coincide.

SCRAP_ROD_RECIPE: str = "R_ScrapRod"
RECLAIM_RECIPE: str = "R_Reclaim"

#: Both added recipes run 4 s a cycle, written as the document writes durations.
RECLAIM_DURATION_TEXT: str = "4.000000"

#: Residue on the wire, in LITRES - the registry converts, nothing here does.
SCRAP_ROD_RESIDUE_LITRES: int = 1000
RECLAIM_RESIDUE_LITRES: int = 2000

RECLAIM_ROD_TARGET: Fraction = Fraction(30)

#: The first selection the walk reaches that solves, and what it costs.
RECLAIM_FIRST_SOLVE: tuple[str, ...] = (PLATE_RECIPE, SCRAP_ROD_RECIPE)
RECLAIM_FIRST_SOLVE_ORE: Fraction = Fraction(30)

#: The lowest-ranking selection the walk reaches, in registry order - R_Plate is
#: in the main corpus, and registry_with appends the two added recipes after it.
RECLAIM_ANSWER: tuple[str, ...] = (PLATE_RECIPE, SCRAP_ROD_RECIPE, RECLAIM_RECIPE)
RECLAIM_ANSWER_MACHINES: dict[str, Fraction] = {
    PLATE_RECIPE: Fraction(1, 2),
    SCRAP_ROD_RECIPE: Fraction(2),
    RECLAIM_RECIPE: Fraction(1),
}
RECLAIM_ANSWER_ORE: Fraction = Fraction(15)

#: Deliberately NOT in registry order, so no arm leans on caller order.
RECLAIM_CANDIDATES: tuple[str, ...] = (RECLAIM_RECIPE, SCRAP_ROD_RECIPE, PLATE_RECIPE)


def _flow_recipe_entry(
    class_name: str,
    ingredients: Sequence[tuple[str, int]],
    products: Sequence[tuple[str, int]],
) -> dict[str, str]:
    """Build one multi-flow recipe entry as docs text, in the corpus grammar.

    Args:
        class_name: The entry's ClassName.
        ingredients: ``(item ClassName, verbatim amount)`` pairs. Fluid amounts
            are LITRES.
        products: The product side, byproducts included.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: RECLAIM_DURATION_TEXT,
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob([building_path(SOLVE_ASSEMBLER_BUILDING)]),
    }


def _reclaim_registry() -> Registry:
    """Build the CS-1347 variant: the main corpus plus the two added recipes.

    Returns:
        The variant registry, built through the real docs seam.
    """
    return registry_with(
        add=[
            _flow_recipe_entry(
                SCRAP_ROD_RECIPE,
                [(SOLVE_PLATE_ITEM, 1)],
                [(SOLVE_ROD_ITEM, 1), (SOLVE_RESIDUE_ITEM, SCRAP_ROD_RESIDUE_LITRES)],
            ),
            _flow_recipe_entry(
                RECLAIM_RECIPE,
                [(SOLVE_RESIDUE_ITEM, RECLAIM_RESIDUE_LITRES)],
                [(SOLVE_PLATE_ITEM, 1)],
            ),
        ]
    )


def _reclaim_request(backend: str) -> OptimizeRequest:
    """Build the CS-1347 request: 30 Rod/min, residue sinkable, minimize raw.

    Args:
        backend: The backend name for the config.

    Returns:
        The request.
    """
    return _request(
        backend,
        targets=MappingProxyType({SOLVE_ROD_ITEM: RECLAIM_ROD_TARGET}),
        candidates=RECLAIM_CANDIDATES,
        unlocked=RECLAIM_CANDIDATES,
        byproduct_policy=BYPRODUCT_SINKABLE,
        objective=MINIMIZE_RAW,
    )


class _WalkSpy:
    """Record every selection the greedy walk hands to ``evaluate_selection``.

    Installed over the NAME the greedy module calls, so it sees exactly the
    selections the walk evaluates against the real request and nothing a probe
    tries. It delegates to the real function, so the run it records is the
    run that would have happened without it.
    """

    def __init__(self) -> None:
        """Start with nothing recorded.

        The real function is read from its owner, ``optimize``, which is the
        object the greedy module imported by name - so the spy delegates to
        exactly what it replaces.
        """
        self.real = optimize.evaluate_selection
        self.handed: list[tuple[str, ...]] = []
        self.reached: list[OptimizeResult] = []

    def __call__(
        self,
        registry: Registry,
        request: OptimizeRequest,
        selection: Sequence[str],
        *,
        backend: str,
        excluded: tuple[ExclusionNote, ...],
    ) -> OptimizeResult | None:
        """Record the selection, delegate, and record the canonical result.

        Args:
            registry: As ``evaluate_selection`` takes it.
            request: As ``evaluate_selection`` takes it.
            selection: The walk's selection, in the order the walk grew it.
            backend: As ``evaluate_selection`` takes it.
            excluded: As ``evaluate_selection`` takes it.

        Returns:
            Whatever the real function returns.
        """
        self.handed.append(tuple(selection))
        result = self.real(registry, request, selection, backend=backend, excluded=excluded)
        if result is not None:
            self.reached.append(result)
        return result


def _spied_greedy_run(monkeypatch: pytest.MonkeyPatch) -> tuple[Registry, OptimizeResult, _WalkSpy]:
    """Run greedy on the CS-1347 fixture through the seam, with the walk recorded.

    Args:
        monkeypatch: The fixture that installs, and later removes, the spy.

    Returns:
        The registry, the result ``optimize_plan`` returned, and the spy.
    """
    spy = _WalkSpy()
    monkeypatch.setattr(greedy_backend, "evaluate_selection", spy)
    variant = _reclaim_registry()
    return variant, _run(variant, _reclaim_request(BACKEND_GREEDY)), spy


@pytest.mark.parametrize("backend", BOTH_BACKENDS)
def test_cs1347_reclaim_matches_the_hand_derived_absolute(backend: str) -> None:
    """Both backends answer 15 Ore. The old greedy walk answered 30."""
    result = _run(_reclaim_registry(), _reclaim_request(backend))

    assert result.selection == RECLAIM_ANSWER
    assert _machines(result.plan) == RECLAIM_ANSWER_MACHINES
    assert result.plan.raw_inputs[SOLVE_ORE_ITEM] == RECLAIM_ANSWER_ORE
    assert result.score == RECLAIM_ANSWER_ORE
    assert type(result.score) is Fraction
    audit_exact(result, path="result")


def test_cs1347_greedy_returns_the_lowest_ranking_selection_its_walk_reached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The acceptance clause, graded on the reached set rather than on one number.

    The first two asserts are the anti-vacuity control: the first selection
    the walk reaches that solves is the hand-derived 30-Ore one, and something
    the walk reached ranks strictly below it. Only then is the return graded,
    against the minimum of everything reached under the shared key.
    """
    variant, result, spy = _spied_greedy_run(monkeypatch)
    positions = registry_positions(variant)
    first = spy.reached[0]
    lowest = min(spy.reached, key=lambda each: result_ranking_key(each, positions))

    assert (first.selection, first.score) == (RECLAIM_FIRST_SOLVE, RECLAIM_FIRST_SOLVE_ORE)
    assert result_ranking_key(lowest, positions) < result_ranking_key(first, positions)
    assert result == lowest
    assert any(result is each for each in spy.reached)


def test_cs1347_the_greedy_walk_still_never_backtracks(monkeypatch: pytest.MonkeyPatch) -> None:
    """The restated guarantee: each evaluated selection is the last plus one key.

    Re-ranking what the walk reached is not backtracking, and this arm is what
    keeps that sentence in ``greedy.py`` true: the walk starts from nothing,
    grows by exactly one new recipe per round, and never drops one.
    """
    _, _, spy = _spied_greedy_run(monkeypatch)

    assert spy.handed[0] == ()
    for before, after in pairwise(spy.handed):
        assert after[: len(before)] == before
        assert len(after) == len(before) + 1
        assert after[-1] not in before
