"""The fast one: reachability prune first, then one incremental score-guided walk.

Owns one strategy behind ``clockspeed/solve/optimize.py``'s ``OptimizerBackend``
seam. Like every backend it holds no objective arithmetic, reads no file and
never touches a save. It exists so that the exponential oracle in
``exhaustive.py`` is not the only thing that can answer, and so that agreement
between the two says something: the two searches share their EVALUATION and
share nothing of their SEARCH.

FEASIBILITY IS ESTABLISHED BEFORE ANY OBJECTIVE IS COMPUTED, IN TWO PLACES
----------------------------------------------------------------------------
This is the load-bearing property of the whole module, and the C5 fixture is
built to punish its absence. There, ``Alt_Gadget`` beats ``Std_Gadget`` on every
objective this project models - one machine against three, 10 Ore a minute
against 120, 15 MW against 45 - and it is INFEASIBLE, because it consumes an
item no recipe produces and which is not a declared raw input. A greedy that
ranks candidates by their intrinsic cost per unit of output picks it, reports a
plan that is better on every axis, and is wrong. Nothing about that plan looks
wrong.

So feasibility comes first twice over, by data flow rather than by convention:

1. **The reachability prune.** An item is reachable if it is a declared raw
   input, or if some candidate recipe produces it and every one of that recipe's
   inputs is reachable. That is a monotone definition, so it is computed as a
   least fixed point - repeat until nothing new is added - which terminates and
   is correct in the presence of CYCLES. The C3 loop is exactly such a cycle:
   the gadget needs the fluid, the fluid comes back from the residue, the residue
   comes from the gadget. A recursive walk does not terminate on it; a fixed
   point does not care. Any candidate with an unreachable input is dropped here,
   before it has a score.
2. **The probe.** Every proposed addition is SOLVED first, and only the ones
   that solve are scored at all. There is no code path in this file that
   computes a score for a selection that has not already come back from pillar 1
   as a plan.

WHAT THE PROBE RELAXES, AND WHY THAT IS A HEURISTIC RATHER THAN A PROOF
-------------------------------------------------------------------------
A partial chain does not solve against the real request - halfway to the answer,
the intermediate items have no producer yet and the byproducts have no consumer
yet, so pillar 1 correctly refuses. Probing with the real request would
therefore reject every partial selection and the walk could never take its first
step.

So the probe solves a RELAXED request: every non-raw item the trial consumes but
does not itself produce is treated as raw ("assume the rest of the chain will
supply it"), and the byproduct policy is the sinkable one ("assume the rest of
the chain will absorb the surplus"). Target items are never relaxed into the raw
set, because an item that is both raw and a target is a contradiction pillar 1
refuses outright.

State the limit plainly rather than let the word "feasibility" imply more: the
relaxation is a PROBE, not a proof. A trial that passes it can still fail the
real request, and a trial that fails it is not proven hopeless. That is why this
backend is a heuristic and why ``exhaustive.py`` exists. The final answer is
never the relaxed plan: the walk returns only a selection on which the REAL
request solved, under the caller's own byproduct policy and raw set.

WHY THE WALK GROWS INSTEAD OF SHRINKING
-----------------------------------------
Each round asks the real request about the current selection first, and keeps
the canonical result when it solves. Then exactly one recipe is added - the
feasible-probing addition with the lowest score, ties going to registry order.
The selection therefore grows by one per round and the loop is bounded by the
candidate count, so it terminates whether or not it succeeds. When no addition
probes feasible, the walk ends; if no round's selection solved, the refusal is
reported rather than an empty plan returned.

Growing rather than shrinking is what makes the first step meaningful. Starting
from the full candidate set and removing would begin by solving a system that
usually has several producers for one item, which is underdetermined, and the
first decision would be made with no information at all.

WHAT THE WALK RETURNS - AMENDED BY CS-1347
-------------------------------------------
The LOWEST-RANKING of the canonical selections the walk actually reached, by
``optimize.result_ranking_key`` - the one documented key the exhaustive backend
ranks by, handed the same usable-candidate position index. "Reached" means
exactly the selections the walk handed to ``optimize.evaluate_selection``: one
per round, along the single path it grew. A probe trial is not reached in that
sense, because what a probe solves is the relaxed request, which has no
canonical result to rank.

This replaces the walk's earlier contract, "the first selection that solves the
real request". That walk stopped at its first solve, so a later round it never
ran could not be compared at all. The two differ whenever adding a recipe to a
selection that already solves makes a better factory - a recipe that turns a
vented byproduct back into an intermediate is the ordinary case, and
``tests/solve/test_optimize.py``'s CS-1347 reclaim fixture is built on that: the
first solve costs 30 Ore a minute and the next round's selection costs 15. So a
solve no longer ends the walk; the walk runs on until no addition probes
feasible, and the cost bound is the one it already had: at most one round per
pool member, plus the round that asks about the empty selection.

THE NO-BACKTRACKING GUARANTEE, RESTATED. Re-ranking what the walk reached is
not backtracking, and the walk still never backtracks: every step it commits to
stays committed, it never removes a recipe, and it never returns to a fork to
try the branch it declined. So the heuristic's limit is unchanged in kind - on a
problem where a worse first step leads to a better factory, it can still return
the worse factory, because the better one lies on a path it did not take. What
CS-1347 adds is the guarantee on the path it DID take: nothing it reached ranks
below what it returns.

A POWER OBJECTIVE THE WALK CANNOT PRICE IS REFUSED - RULED, CS-1347
--------------------------------------------------------------------
Because a solve no longer ends the walk, the walk now probes additions the
first-solve walk never reached. A probe is scored by ``optimize.score_plan``
inside ``_best_addition``, so when the objective weights power and the probed
plan uses a recipe with no exact draw, ``PowerNotComparableError`` is raised
THERE - on C10 in ``tests/solve/synthetic.py``, while probing R_Reclaim, which
names no building, after the first solve. The first-solve walk answered that
request with a 34 MW plan only because it stopped before pricing R_Reclaim: an
answer to a question the objective cannot compare, decided by walk order.

The exhaustive backend refuses the same request, raising from
``optimize.evaluate_selection`` when it scores the three-recipe subset, and
greedy now refuses it exactly as exhaustive does; ``POST /api/optimize``
transcribes the refusal as HTTP 400 ``power_not_comparable`` for either
backend. The CS-1347 adjudicator ACCEPTED it: the error is not caught here, and
the walk is not changed to avoid it. The two backends price different sets of
recipes - greedy every recipe on a probe it scores, exhaustive every recipe of a
canonical result it scores - so the equality is graded on that request rather
than claimed for every request.
"""

from __future__ import annotations

from collections.abc import Container, Sequence
from fractions import Fraction

from clockspeed.data.registry import Recipe, Registry
from clockspeed.solve.backends import BACKEND_GREEDY
from clockspeed.solve.optimize import (
    NoFeasibleSelectionError,
    OptimizeRequest,
    OptimizeResult,
    evaluate_selection,
    result_ranking_key,
    score_plan,
    usable_candidates,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_SINKABLE,
    ProductionPlan,
    RatioError,
    RatioRequest,
    solve_for_targets,
)

__all__ = ["GreedyBackend"]


def _inputs_reachable(recipe: Recipe, reachable: Container[str]) -> bool:
    """Whether every ingredient of a recipe can be supplied at all.

    Args:
        recipe: The recipe to test.
        reachable: The items established as reachable so far.

    Returns:
        True when the recipe could run given those items.
    """
    return all(flow.item_key in reachable for flow in recipe.inputs)


def _reachable_items(
    registry: Registry, candidates: Sequence[str], raw_items: Sequence[str]
) -> frozenset[str]:
    """The least fixed point of "this item can be supplied".

    Iterated to a fixed point rather than walked recursively, for the reason the
    module docstring gives and the reason ``clockspeed/solve/ratio.py`` gives for
    having no walk either: the recipe graph genuinely contains cycles, and a walk
    over one does not terminate. Adding an item is monotone, so repeating until
    nothing changes reaches the same answer regardless of the order candidates
    are visited in.

    Args:
        registry: The built registry.
        candidates: The usable candidate keys.
        raw_items: The declared raw inputs, which seed the set.

    Returns:
        Every item some subset of the candidates could ever produce, plus the
        raw inputs themselves.
    """
    reachable = set(raw_items)
    growing = True
    while growing:
        growing = False
        for key in candidates:
            recipe = registry.recipes[key]
            if not _inputs_reachable(recipe, reachable):
                continue
            for flow in recipe.outputs:
                if flow.item_key not in reachable:
                    reachable.add(flow.item_key)
                    growing = True
    return frozenset(reachable)


def _relaxed_raw(
    registry: Registry, request: OptimizeRequest, trial: Sequence[str]
) -> tuple[str, ...]:
    """The raw set a partial selection is probed against.

    Every non-raw item the trial consumes without producing is added, which is
    the "assume the rest of the chain supplies it" half of the relaxation. Target
    items are excluded from that addition: pillar 1 refuses an item declared both
    raw and a target, and rightly - a raw item is unbounded, so targeting one
    asks for a rate that is already unlimited.

    Args:
        registry: The built registry.
        request: The problem, for the real raw set and the targets.
        trial: The selection being probed.

    Returns:
        The relaxed raw set, sorted so the probe is identical between runs.
    """
    produced: set[str] = set()
    consumed: set[str] = set()
    for key in trial:
        recipe = registry.recipes[key]
        for flow in recipe.inputs:
            consumed.add(flow.item_key)
        for flow in recipe.outputs:
            produced.add(flow.item_key)
    declared = set(request.raw_items)
    missing = consumed - produced - declared - set(request.targets)
    return tuple(sorted(declared | missing))


def _probe(
    registry: Registry, request: OptimizeRequest, trial: Sequence[str]
) -> ProductionPlan | None:
    """Solve a relaxed version of the request, to test a partial selection.

    This is the ONLY gate a candidate passes before it is scored, and it returns
    a plan or nothing - so there is no way to reach the objective arithmetic with
    an infeasible trial. That is enforced by the shape of the value rather than
    by the order of two statements, which is what keeps it true after an edit.

    Args:
        registry: The built registry.
        request: The problem.
        trial: The selection to probe.

    Returns:
        The relaxed plan, or None when even the relaxation does not solve.
    """
    try:
        return solve_for_targets(
            registry,
            RatioRequest(
                targets=request.targets,
                recipes=tuple(trial),
                raw_items=_relaxed_raw(registry, request, trial),
                byproduct_policy=BYPRODUCT_SINKABLE,
            ),
        )
    except RatioError:
        return None


class GreedyBackend:
    """Reachability-pruned incremental search, scoring only what already solves.

    Structurally satisfies ``optimize.OptimizerBackend``. Registered in
    ``clockspeed/solve/backends/__init__.py`` and reached through
    ``optimize.select_backend``.

    A HEURISTIC, stated rather than implied: it takes the locally best feasible
    step and never backtracks, so on a problem where a worse first step leads to
    a better factory it returns the worse factory. ``exhaustive.py`` is the
    oracle that says when that has happened. Among the selections its one path
    DID reach, it returns the lowest-ranking under the shared key - the
    CS-1347 amendment the module docstring records.
    """

    @property
    def name(self) -> str:
        """The registered name this backend is selected by.

        Returns:
            :data:`~clockspeed.solve.backends.BACKEND_GREEDY`.
        """
        return BACKEND_GREEDY

    def _best_addition(
        self,
        registry: Registry,
        request: OptimizeRequest,
        selected: Sequence[str],
        pool: Sequence[str],
    ) -> str | None:
        """Pick the lowest-scoring addition that already probes feasible.

        Args:
            registry: The built registry.
            request: The problem.
            selected: What is chosen so far.
            pool: The reachability-pruned candidates, in registry order.

        Returns:
            The chosen recipe key, or None when nothing probes feasible.

        Raises:
            PowerNotComparableError: The power objective is weighted and a
                probed plan uses a recipe with no exact draw.
        """
        chosen: str | None = None
        best: Fraction | None = None
        taken = set(selected)
        for key in pool:
            if key in taken:
                continue
            probed = _probe(registry, request, (*selected, key))
            if probed is None:
                # Infeasible, and therefore never scored. This is the branch the
                # C5 fixture exists to force.
                continue
            scored = score_plan(registry, probed, request.objective)
            # NOT optimize.ranking_key, and the asymmetry is stated rather than
            # papered over. That key ranks a canonical result - optimize() below
            # ranks the walk's reached results by it; what is scored
            # here is the RELAXED PROBE plan _probe returns, which sinks
            # byproducts and relaxes the raw set, so it is not a result and has
            # no canonical selection to read positions from. The tie therefore
            # resolves through `pool` order - registry order, as this method's
            # Args record and its caller builds it - plus a STRICTLY less
            # comparison, which keeps the earlier key. Same registry ordering
            # optimize.ranking_key breaks a tie with, reached by a different
            # route rather than by the key itself.
            if best is None or scored < best:
                chosen, best = key, scored
        return chosen

    def optimize(self, registry: Registry, request: OptimizeRequest) -> OptimizeResult:
        """Prune by reachability, grow one selection, and rank what the walk reached.

        Args:
            registry: The built registry.
            request: The problem.

        Returns:
            The lowest-ranking, by ``optimize.result_ranking_key``, of the
            canonical results of every selection the walk evaluated against the
            real request - not merely the first one that solved.

        Raises:
            ValueError: A candidate names no recipe in this registry.
            NoFeasibleSelectionError: The walk ran out of feasible additions.
            ObjectiveUndefinedError: The objective names no usable direction.
            PowerNotComparableError: The power objective is weighted and a plan
                the walk scores uses a recipe with no exact draw - raised by
                ``optimize.score_plan``, from ``_best_addition`` when it is a
                probe, as on C10, or from ``optimize.evaluate_selection`` when
                it is a reached selection. Not caught, by the CS-1347 ruling.
        """
        usable, excluded = usable_candidates(registry, request)
        reachable = _reachable_items(registry, usable, request.raw_items)
        pool = tuple(key for key in usable if _inputs_reachable(registry.recipes[key], reachable))

        # The same position mapping the exhaustive backend hands the shared
        # key, so the two rank a canonical result by one rule and one index.
        position = {key: index for index, key in enumerate(usable)}
        best: OptimizeResult | None = None
        best_key: tuple[Fraction, tuple[int, ...]] | None = None

        selected: tuple[str, ...] = ()
        # One round per possible addition, plus the round that asks the real
        # request about the empty selection. Bounded, so the walk terminates
        # whether or not it succeeds. A round whose selection solves does NOT
        # end the walk: its canonical result is kept if it ranks lowest so
        # far, and the walk grows on until no addition probes feasible.
        for _ in range(len(pool) + 1):
            result = evaluate_selection(
                registry, request, selected, backend=self.name, excluded=excluded
            )
            if result is not None:
                ranking = result_ranking_key(result, position)
                if best_key is None or ranking < best_key:
                    best, best_key = result, ranking
            chosen = self._best_addition(registry, request, selected, pool)
            if chosen is None:
                break
            selected = (*selected, chosen)

        if best is not None:
            return best
        raise NoFeasibleSelectionError(
            f"no feasible addition remains after {len(selected)} step(s): "
            f"{', '.join(selected) or 'nothing was selected'}. "
            f"{len(usable) - len(pool)} of {len(usable)} usable candidate(s) were pruned as "
            "unreachable - some ingredient of theirs is neither a declared raw input nor produced "
            "by anything in the candidate set. This search is a heuristic, so a refusal here is "
            "not proof that no plan exists; the exhaustive backend is what settles that"
        )
