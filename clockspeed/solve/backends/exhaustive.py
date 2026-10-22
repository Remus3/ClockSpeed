"""The oracle: every subset of the candidate set, evaluated, global minimum taken.

Owns one strategy behind ``clockspeed/solve/optimize.py``'s ``OptimizerBackend``
seam. It holds no objective arithmetic and no notion of what a plan is - those
belong to ``optimize`` - and it reads no file, no registry of its own and no
save. What it owns is the SEARCH.

THE MECHANISM, AND WHY IT IS THE UNINTERESTING ONE ON PURPOSE
--------------------------------------------------------------
The candidate set is turned into its complete subset lattice by counting a bit
mask from zero, each selection is handed to ``optimize.evaluate_selection``, and
the lowest-ranking result wins. There is no pruning, no ordering heuristic and
no early exit. Every one of those would be an opportunity to be subtly wrong,
and this backend's whole job is to be the thing a subtler search is checked
against. Its correctness argument is that it looks at everything.

The empty subset is enumerated too. It is a real selection - it is the answer to
a target rate of zero - and skipping it because "no recipes cannot be a plan"
would be an assumption rather than a result.

WHY THE TIE-BREAK IS NOT DEFINED HERE
---------------------------------------
It is ``optimize.ranking_key``, owned by the layer whose determinism claim
already describes it and argued at length in that module's docstring: one
documented stable key, consumed by this backend - through
``optimize.result_ranking_key`` - and by the strategy ladder. The greedy backend
does NOT consume it: what greedy scores is a relaxed probe plan with no
canonical selection to read positions from, and ``greedy.py`` states that
asymmetry at its own comparison. This file re-exports the key, so
``exhaustive.ranking_key`` still resolves and the name stays in this module's
``__all__``.

What stays here is what the ENUMERATION contributes. Ties are ordinary rather
than exotic - the C8 fixture's two twin recipes are byte-for-byte equivalent in
duration, ingredients, products and building, so every objective scores them
identically by construction - and with only the score to rank by, the winner
would be whichever mask happened to be visited first, which is a property of
this enumeration rather than of the problem.

Note what that makes UNOBSERVABLE from this backend's output. Because the key is
unique per canonical selection, and because the mask enumeration is itself
deterministic, a score-only rule computes the same winner on every input this
project can build a fixture for - the position half is invisible in the return
value, exactly as ``exact.py``'s pivot rule is invisible in ``solve_linear``'s.
It is nonetheless load-bearing: without a stated rule the tie-break is
"whichever mask came first", which is an implementation detail a REPLACEMENT
backend cannot reproduce, and two backends would then disagree on ties while
each looked correct alone. So the rule is tested at the selector rather than
through a run of this backend, on the same reasoning and by the same route
``tests/solve/test_exact.py`` uses for ``_pivot_row``. A contract with no test
is the CONVENTIONS.md section 7.2 unrun gate.

The position mapping this backend hands the key is its own usable-candidate
index, not the whole registry's. That is licensed rather than convenient: the
key reads only the ORDER of the mapping, and both indexes are strictly
increasing in registry order.

WHY THE CAP IS A REFUSAL AND NOT A DEGRADATION
------------------------------------------------
The work doubles per candidate. Above ``optimize.MAX_EXHAUSTIVE_CANDIDATES``
this raises ``SearchSpaceTooLargeError`` BEFORE doing any work, rather than
quietly switching to a cheaper search. Silently degrading to a heuristic would
return a plausible plan under the name of the exact backend, and nothing in the
result would say the guarantee had been dropped - the same failure shape as a
backend name falling back on a typo.
"""

from __future__ import annotations

from fractions import Fraction

from clockspeed.data.registry import Registry
from clockspeed.solve.backends import BACKEND_EXHAUSTIVE
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    NoFeasibleSelectionError,
    OptimizeRequest,
    OptimizeResult,
    SearchSpaceTooLargeError,
    evaluate_selection,
    ranking_key,
    result_ranking_key,
    usable_candidates,
)

#: Re-exported from its owner, ``clockspeed/solve/optimize.py``, so the name
#: this module published before the rule moved still resolves here.
__all__ = ["ExhaustiveBackend", "ranking_key"]


class ExhaustiveBackend:
    """Complete enumeration of the candidate subset lattice.

    Structurally satisfies ``optimize.OptimizerBackend``. It is registered in
    ``clockspeed/solve/backends/__init__.py`` and is reached through
    ``optimize.select_backend``; constructing it directly works and proves
    nothing about the seam, which is why the suite never does.
    """

    @property
    def name(self) -> str:
        """The registered name this backend is selected by.

        Returns:
            :data:`~clockspeed.solve.backends.BACKEND_EXHAUSTIVE`.
        """
        return BACKEND_EXHAUSTIVE

    def optimize(self, registry: Registry, request: OptimizeRequest) -> OptimizeResult:
        """Evaluate every subset and return the global minimum.

        Args:
            registry: The built registry.
            request: The problem.

        Returns:
            The lowest-ranking result, with ties broken by registry position.

        Raises:
            ValueError: A candidate names no recipe in this registry.
            SearchSpaceTooLargeError: More candidates than the cap allows.
            NoFeasibleSelectionError: Not one subset solves.
            ObjectiveUndefinedError: The objective names no usable direction.
            PowerNotComparableError: The power objective is weighted and some
                used recipe has no exact draw.
        """
        usable, excluded = usable_candidates(registry, request)
        if len(usable) > MAX_EXHAUSTIVE_CANDIDATES:
            raise SearchSpaceTooLargeError(
                f"{len(usable)} usable candidates describe more subsets than this backend will "
                f"enumerate; the cap is {MAX_EXHAUSTIVE_CANDIDATES} and the work doubles per "
                "candidate. This refuses rather than switching to a cheaper search, because a "
                "heuristic answer returned under the exact backend's name carries a guarantee it "
                "no longer has"
            )

        position = {key: index for index, key in enumerate(usable)}
        best: OptimizeResult | None = None
        best_key: tuple[Fraction, tuple[int, ...]] | None = None

        # A bit mask counted from zero, so the empty subset is member zero and
        # every subset is visited exactly once. The tie-break below is what makes
        # the ANSWER independent of this order.
        for mask in range(1 << len(usable)):
            selection = tuple(key for index, key in enumerate(usable) if (mask >> index) & 1)
            result = evaluate_selection(
                registry, request, selection, backend=self.name, excluded=excluded
            )
            if result is None:
                continue
            ranking = result_ranking_key(result, position)
            if best_key is None or ranking < best_key:
                best, best_key = result, ranking

        if best is None:
            raise NoFeasibleSelectionError(
                f"none of the subsets of {len(usable)} usable candidate(s) solves this request; "
                "the search was complete, so this is the absence of any plan rather than the "
                f"failure of one search. Usable: {', '.join(usable) or 'nothing'}"
            )
        return best
