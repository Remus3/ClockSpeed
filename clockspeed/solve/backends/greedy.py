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
never the relaxed plan: the walk returns only when the REAL request solves,
under the caller's own byproduct policy and raw set.

WHY THE WALK GROWS INSTEAD OF SHRINKING
-----------------------------------------
Each round asks the real request first. If it solves, that is the answer. If it
does not, exactly one recipe is added - the feasible-probing addition with the
lowest score, ties going to registry order. The selection therefore grows by one
per round and the loop is bounded by the candidate count, so it terminates
whether or not it succeeds. When no addition probes feasible, there is nothing
left to try and the refusal is reported rather than an empty plan returned.

Growing rather than shrinking is what makes the first step meaningful. Starting
from the full candidate set and removing would begin by solving a system that
usually has several producers for one item, which is underdetermined, and the
first decision would be made with no information at all.
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
    oracle that says when that has happened.
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
            # papered over. That key ranks a canonical result; what is scored
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
        """Prune by reachability, then grow one selection until the request solves.

        Args:
            registry: The built registry.
            request: The problem.

        Returns:
            The first selection that solves the real request, in canonical form.

        Raises:
            ValueError: A candidate names no recipe in this registry.
            NoFeasibleSelectionError: The walk ran out of feasible additions.
            ObjectiveUndefinedError: The objective names no usable direction.
            PowerNotComparableError: The power objective is weighted and some
                used recipe has no exact draw.
        """
        usable, excluded = usable_candidates(registry, request)
        reachable = _reachable_items(registry, usable, request.raw_items)
        pool = tuple(key for key in usable if _inputs_reachable(registry.recipes[key], reachable))

        selected: tuple[str, ...] = ()
        # One round per possible addition, plus the round that asks the real
        # request about the empty selection. Bounded, so the walk terminates
        # whether or not it succeeds.
        for _ in range(len(pool) + 1):
            result = evaluate_selection(
                registry, request, selected, backend=self.name, excluded=excluded
            )
            if result is not None:
                return result
            chosen = self._best_addition(registry, request, selected, pool)
            if chosen is None:
                break
            selected = (*selected, chosen)

        raise NoFeasibleSelectionError(
            f"no feasible addition remains after {len(selected)} step(s): "
            f"{', '.join(selected) or 'nothing was selected'}. "
            f"{len(usable) - len(pool)} of {len(usable)} usable candidate(s) were pruned as "
            "unreachable - some ingredient of theirs is neither a declared raw input nor produced "
            "by anything in the candidate set. This search is a heuristic, so a refusal here is "
            "not proof that no plan exists; the exhaustive backend is what settles that"
        )
