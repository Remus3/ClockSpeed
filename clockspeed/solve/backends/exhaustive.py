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

WHY THE TIE-BREAK IS THE SCORE PAIRED WITH REGISTRY POSITIONS
---------------------------------------------------------------
Ties are ordinary rather than exotic: the C8 fixture's two twin recipes are
byte-for-byte equivalent in duration, ingredients, products and building, so
every objective scores them identically by construction. With only the score to
rank by, the winner would be whichever mask happened to be visited first, and
that is a property of the enumeration rather than of the problem.

So the ranking key is ``(score, registry positions of the selection)``. Both
halves are exact and neither depends on visit order: distinct selections have
distinct position tuples, so the key is a total order and the same selection
wins no matter how the lattice is walked. A shorter tuple that is a prefix of a
longer one sorts first, which means a tie between a selection and a superset of
it resolves to the smaller factory - the right answer and, more importantly, a
STATED one.

Note what that makes UNOBSERVABLE from this backend's output, and why
:func:`ranking_key` is a named function rather than an inline tuple. Because the
key is unique per canonical selection, and because the mask enumeration is
itself deterministic, a score-only rule computes the same winner on every input
this project can build a fixture for - the position half is invisible in the
return value, exactly as ``exact.py``'s pivot rule is invisible in
``solve_linear``'s. It is nonetheless load-bearing: without a stated rule the
tie-break is "whichever mask came first", which is an implementation detail a
REPLACEMENT backend cannot reproduce, and two backends would then disagree on
ties while each looked correct alone. So the rule is extracted here and tested
at the selector, on the same reasoning and by the same route
``tests/solve/test_exact.py`` uses for ``_pivot_row``. A contract with no test
is the CONVENTIONS.md section 7.2 unrun gate.

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

from collections.abc import Mapping
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
    usable_candidates,
)

__all__ = ["ExhaustiveBackend", "ranking_key"]


def ranking_key(
    result: OptimizeResult, positions: Mapping[str, int]
) -> tuple[Fraction, tuple[int, ...]]:
    """The total order the search minimizes over: score first, then registry position.

    A named function rather than an inline tuple, for the reason the module
    docstring gives at length and ``clockspeed/solve/exact.py`` gives for
    ``_pivot_row``: the rule is invisible in the backend's return value, so this
    is the only place it can be tested, and an untested rule is one somebody
    simplifies away.

    Args:
        result: A canonical result, whose selection is in registry order.
        positions: Recipe key to its index among the usable candidates.

    Returns:
        The key. Lower wins. The score dominates; the position tuple decides
        only a tie, and decides it in favour of the selection whose recipes come
        earliest in the registry - which also means the smaller of two
        selections when one is a prefix of the other.
    """
    return (result.score, tuple(positions[key] for key in result.selection))


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
            ranking = ranking_key(result, position)
            if best_key is None or ranking < best_key:
                best, best_key = result, ranking

        if best is None:
            raise NoFeasibleSelectionError(
                f"none of the subsets of {len(usable)} usable candidate(s) solves this request; "
                "the search was complete, so this is the absence of any plan rather than the "
                f"failure of one search. Usable: {', '.join(usable) or 'nothing'}"
            )
        return best
