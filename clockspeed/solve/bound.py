"""CS-1245 - a BOUNDED candidate enumeration over pillar 2, with its trim recorded.

``clockspeed/solve/backends/exhaustive.py`` REFUSES above
:data:`~clockspeed.solve.optimize.MAX_EXHAUSTIVE_CANDIDATES`, and that refusal
stands exactly as written. This module does not reverse it; it ANSWERS it. The
question the refusal leaves open is what a caller who cannot shrink the request
themselves should do, and the answer here is a DIFFERENT function that narrows
the request by a NAMED rule and hands back a RECORD of what the narrowing
dropped. A caller who wants the whole-set optimum still calls
:func:`~clockspeed.solve.optimize.optimize_plan` and still gets the refusal.

WHY THE TRIM LIVES ABOVE THE BACKEND SEAM
-------------------------------------------
Nothing below ``OptimizerBackend`` changes. ``optimize.py`` is byte-unchanged,
both shipped backends are byte-unchanged, no field joins
:class:`~clockspeed.solve.optimize.SolveConfig`, and ``optimize_plan`` with no
new configuration behaves exactly as it did. The bound is OPT-IN BY CALL SITE: a
caller reaches it by calling this function INSTEAD, which is the only shape
under which the exhaustive backend's guarantee stays honest. A bound wired in
below the seam would make ``optimize_plan`` return a narrowed-search answer
under the exact backend's name, which is precisely the failure
``exhaustive.py``'s docstring section "WHY THE CAP IS A REFUSAL AND NOT A
DEGRADATION" exists to forbid.

The cap is also this module's SAFETY FLOOR rather than merely its parameter.
Every narrowed request handed to ``optimize_plan`` carries at most
``MAX_EXHAUSTIVE_CANDIDATES`` usable candidates, so a miscomputed trim does not
quietly search a space that was never bounded - it fires that loud refusal
instead.

THE SCOPE OF THAT FLOOR, SAID RATHER THAN IMPLIED: the refusal is the EXHAUSTIVE
backend's, and the greedy backend names no cap at all. This module passes
``request.config`` through untouched and pins no backend, so under a greedy
config there is no floor to fire - the bound still holds, because the trim
narrows the request either way, but nothing below would catch a trim that did
not.

THE TRIM RULE, AND WHY TARGET PRODUCERS RANK FIRST
----------------------------------------------------
One rule today, named :data:`TRIM_TARGET_PRODUCERS_FIRST` and the sole member of
the closed vocabulary :data:`TRIM_RULES`, so a second rule cannot arrive
unnamed. It ranks the usable candidates by the key::

    (0 if the recipe produces any item in request.targets else 1,
     the recipe's position in registry order)

and keeps the first ``MAX_EXHAUSTIVE_CANDIDATES`` of that ranking. Both halves
are ints; no float enters the key.

The first tier is what keeps a bounded search's feasibility NON-ARBITRARY. A
bound that dropped every producer of a target would make every prefix
infeasible, and the refusal that followed would say "no plan" about a request
the unbounded search might well have answered - a wrong answer dressed as an
absence. Ranking direct target-producers ahead of everything else means the
bound never drops a target's last producer while keeping a recipe that cannot
contribute to a target at all. The second tier is registry order, which is the
same order the whole determinism claim in ``optimize.py`` rests on.

WHY EVERY ORDER HERE IS A TUPLE AND NEVER A SET
-------------------------------------------------
``clockspeed/advisor/trace.py`` records the reason in its own header: a set's
iteration order and its repr depend on PYTHONHASHSEED, so two runs would render
differently. A set is used below ONLY as a private membership test, and never to
decide an order. :attr:`TrimStep.kept` and :attr:`TrimStep.removed` are tuples,
in registry order, both of them.

THE ASCENT, AND WHY THE FIRST PREFIX THAT SOLVES IS THE SMALLEST
------------------------------------------------------------------
The ranking defines NESTED prefixes S_1 subset S_2 subset ... subset S_K, where
K is the smaller of the usable count and the cap, and S_k is the first k members
OF THE TRIM RANKING - not of registry order. The ascent runs k from 1 upwards
and returns the first prefix that yields a plan. Because the chain is nested,
that first k IS the smallest k whose prefix solves: a smaller prefix is a SUBSET
of it, and had any subset of it solved, the ascent would have reached that
smaller k first. That is a proof about the chain, not an early-exit heuristic.

(Each narrowed request may hand its prefix over in any order, because
``optimize.usable_candidates`` sorts the door into registry order itself. The
prefix is passed in ranking order purely because that is the order it was built
in.)

Inside one prefix, the winner is whichever backend the request configured,
untouched - which for the exhaustive backend is the oracle's own
``optimize.result_ranking_key``, and for the greedy backend is that heuristic's
own first-that-solves walk, which consults no shared key and whose re-ranking is
CS-1347's open subject. This module changes neither.

Only ``NoFeasibleSelectionError`` is absorbed as "not this
prefix", on exactly ``relax.py``'s reasoning: every other refusal says the
request is malformed or unanswerable as asked rather than infeasible, so it is a
shape bug every prefix would hit and swallowing it would turn one into a plan.

THE COST BOUND, AS ARITHMETIC
-------------------------------
Prefix S_k has k members, so the exhaustive backend evaluates (1 << k) subsets
of it. The whole ascent therefore evaluates at most::

    (1 << 1) + (1 << 2) + ... + (1 << K)  ==  (1 << (K + 1)) - 2

subsets. The single capped search this replaces evaluates (1 << K). So bounding
by prefixes costs a factor of just under two, and never an unbounded run. For
K at the shipped cap of twelve that is 8190 subsets against 4096.

THE CONSEQUENCE, STATED PLAINLY
---------------------------------
Because k dominates the order, this function CAN return a plan that scores WORSE
than the best plan over the whole trimmed set. The order it implements is
lexicographic ``(k: int, score: Fraction, positions: tuple[int, ...])`` with k
OUTERMOST, so a cheaper plan that needs one more recipe than the smallest
feasible prefix is not chosen. That is the specified behaviour rather than a
defect, and :class:`TrimRecord` plus :attr:`BoundedResult.chosen_size` are what
make the trade visible to the caller instead of silent. A caller who wants the
whole-set optimum calls ``optimize_plan`` and gets the refusal.

Two narrower consequences, for the same honesty:

- The EMPTY prefix is not in the chain, so the ascent starts at k = 1. A request
  whose usable set is empty is refused with :class:`BoundExhaustedError` having
  tried nothing, where ``optimize_plan`` would have answered a zero target rate
  with the empty selection.
- The returned :attr:`~clockspeed.solve.optimize.OptimizeResult.excluded` notes
  describe the NARROWED request, so candidates the caller named but the door
  excluded - locked, or zero duration - are not listed on it. The trim record
  names what the BOUND dropped; what the DOOR dropped is read by calling
  ``optimize.usable_candidates`` on the original request.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final

from clockspeed.data.registry import Registry
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    MAX_EXHAUSTIVE_CANDIDATES,
    NoFeasibleSelectionError,
    OptimizeRequest,
    OptimizeResult,
    optimize_plan,
    registry_order,
    registry_positions,
    usable_candidates,
)

__all__ = [
    "TRIM_RULES",
    "TRIM_TARGET_PRODUCERS_FIRST",
    "BoundExhaustedError",
    "BoundedResult",
    "TrimRecord",
    "TrimStep",
    "optimize_within_bound",
]

#: The trim rule's stable name: direct producers of a requested item are kept
#: ahead of everything else, then registry order decides. The module docstring
#: argues why that first tier is the one that keeps a bound non-arbitrary.
TRIM_TARGET_PRODUCERS_FIRST: Final = "target-producers-first"

#: THE closed vocabulary of trim rules. One member today, stated as a tuple so
#: that a second rule has to JOIN it rather than arriving unnamed on a step.
#: ``tests/solve/test_bound.py`` pins the membership.
TRIM_RULES: Final[tuple[str, ...]] = (TRIM_TARGET_PRODUCERS_FIRST,)

#: The trim rule's first tier: the recipe produces at least one requested item.
_TIER_TARGET_PRODUCER: Final = 0

#: Its second tier: the recipe produces no requested item.
_TIER_EVERYTHING_ELSE: Final = 1


@dataclass(frozen=True)
class TrimStep:
    """One narrowing of the usable candidate set, in exact terms.

    Attributes:
        rule: The rule's name, as :data:`TRIM_RULES` lists it.
        cap: The candidate count the narrowing was down TO - the exhaustive
            backend's own ``MAX_EXHAUSTIVE_CANDIDATES``, carried on the step so
            a reader of the record needs nothing else to interpret it.
        kept: The candidates that entered the search, in REGISTRY order. A
            tuple, never a set: the module docstring records why.
        removed: The candidates the bound dropped, in REGISTRY order, and a
            tuple for the same reason. Together with :attr:`kept` it partitions
            the usable set exactly, so a reader can see what was lost rather
            than only how much.
    """

    rule: str
    cap: int
    kept: tuple[str, ...]
    removed: tuple[str, ...]


@dataclass(frozen=True)
class TrimRecord:
    """Every narrowing applied to reach the returned plan.

    Attributes:
        steps: The applied steps, in the order they were applied. Never empty:
            a request that needed no trim gets NO record at all rather than an
            empty one, which is ``relax.py``'s precedent and the same reason -
            an empty record claims a narrowing that never happened.
    """

    steps: tuple[TrimStep, ...]

    @property
    def first(self) -> TrimStep:
        """The first narrowing applied - the one the bound reached first."""
        return self.steps[0]


@dataclass(frozen=True)
class BoundedResult:
    """A plan, what the bound dropped to get it, and which prefix won.

    Attributes:
        result: The optimizer's result for the narrowed request actually solved.
            Its ``excluded`` notes describe THAT request, not the original - see
            the module docstring.
        record: What the bound dropped, or None when every usable candidate fit
            under the cap and nothing was dropped.
        chosen_size: The size of the winning prefix. ALWAYS present, including
            when :attr:`record` is None, because it describes the ascent rather
            than the trim. Together with the record it is what makes the
            smallest-prefix trade visible instead of silent.
    """

    result: OptimizeResult
    record: TrimRecord | None
    chosen_size: int


class BoundExhaustedError(NoFeasibleSelectionError):
    """No prefix up to the cap yields a plan.

    A subclass of :class:`~clockspeed.solve.optimize.NoFeasibleSelectionError`,
    so a caller already handling "no plan" handles this without change -
    ``relax.py``'s ``LadderExhaustedError`` sets that precedent.

    Attributes:
        cap: The cap the ascent was bounded by.
        rule: The trim rule that ranked the prefixes.
        tried: How many prefixes were evaluated. Zero when the usable set was
            empty, which is a distinguishable and honest answer rather than the
            same refusal as a full ascent that found nothing.
    """

    def __init__(self, cap: int, rule: str, tried: int, message: str) -> None:
        """Record the bound alongside the message.

        Args:
            cap: The cap the ascent was bounded by.
            rule: The trim rule's name.
            tried: How many prefixes were evaluated.
            message: The full explanation.
        """
        super().__init__(message)
        self.cap = cap
        self.rule = rule
        self.tried = tried


def _trim_ranking(registry: Registry, request: OptimizeRequest) -> tuple[str, ...]:
    """Rank the usable candidates by :data:`TRIM_TARGET_PRODUCERS_FIRST`.

    Args:
        registry: The built registry.
        request: The problem, as the caller stated it.

    Returns:
        Every usable candidate, ranked: direct producers of a requested item
        first, then registry order within each tier. A tuple, and the only
        order this module's ascent reads.

    Raises:
        ValueError: A candidate names no recipe in this registry, raised by
            :func:`~clockspeed.solve.optimize.usable_candidates` at the door.
    """
    usable, _excluded = usable_candidates(registry, request)
    # A set, and ONLY as a membership test - it decides no order anywhere.
    wanted = frozenset(request.targets)
    positions = registry_positions(registry)

    def rank(recipe_key: str) -> tuple[int, int]:
        """Rank one candidate.

        Args:
            recipe_key: The candidate's recipe key.

        Returns:
            Its ``(tier, registry position)`` key. Both ints.
        """
        outputs = registry.recipes[recipe_key].outputs
        produces_a_target = any(output.item_key in wanted for output in outputs)
        tier = _TIER_TARGET_PRODUCER if produces_a_target else _TIER_EVERYTHING_ELSE
        return (tier, positions[recipe_key])

    return tuple(sorted(usable, key=rank))


def optimize_within_bound(registry: Registry, request: OptimizeRequest) -> BoundedResult:
    """Trim to the cap by a named rule, then take the smallest prefix that solves.

    The module docstring holds the argument: why the trim is above the seam, why
    target producers rank first, why the first solving prefix is provably the
    smallest, the cost bound as arithmetic, and the plans this order
    deliberately does not return.

    Args:
        registry: The built registry. The only input this layer reads.
        request: The problem, as the caller stated it. It is not mutated; each
            prefix is solved through a replaced copy.

    Returns:
        The result for the smallest ranked prefix that yields a plan, the record
        of what the bound dropped - None when nothing was - and that prefix's
        size. Audited exact on the way out.

    Raises:
        BoundExhaustedError: No prefix up to the cap yields a plan. Names the
            cap, the rule and how many prefixes were tried.
        ValueError: A candidate names no recipe in this registry.
        ObjectiveUndefinedError, PowerNotComparableError, UnknownBackendError:
            As :func:`~clockspeed.solve.optimize.optimize_plan` raises them, at
            whichever prefix they arise. None of them means infeasible, so none
            is absorbed.
        SearchSpaceTooLargeError: Only reachable if the trim above were wrong,
            since every prefix is at most ``MAX_EXHAUSTIVE_CANDIDATES`` long. It
            is left to propagate deliberately - the module docstring's safety
            floor.
    """
    ranked = _trim_ranking(registry, request)
    limit = min(len(ranked), MAX_EXHAUSTIVE_CANDIDATES)

    record: TrimRecord | None = None
    if len(ranked) > limit:
        step = TrimStep(
            rule=TRIM_TARGET_PRODUCERS_FIRST,
            cap=MAX_EXHAUSTIVE_CANDIDATES,
            kept=registry_order(registry, ranked[:limit]),
            removed=registry_order(registry, ranked[limit:]),
        )
        record = TrimRecord(steps=(step,))

    # The nested chain, smallest first. The empty prefix is not a member; the
    # module docstring states what that costs.
    for size in range(1, limit + 1):
        try:
            result = optimize_plan(registry, replace(request, candidates=ranked[:size]))
        except NoFeasibleSelectionError:
            continue
        bounded = BoundedResult(result=result, record=record, chosen_size=size)
        audit_exact(bounded, path="bounded")
        return bounded

    raise BoundExhaustedError(
        MAX_EXHAUSTIVE_CANDIDATES,
        TRIM_TARGET_PRODUCERS_FIRST,
        limit,
        f"no prefix of the {TRIM_TARGET_PRODUCERS_FIRST} ranking yields a plan. "
        f"{len(ranked)} usable candidate(s) were ranked, bounded to a cap of "
        f"{MAX_EXHAUSTIVE_CANDIDATES}, and all {limit} nested prefix(es) from size 1 "
        "upwards were evaluated and refused. Because the prefixes are nested, this is "
        "the absence of any plan over the kept set rather than the failure of one "
        "search - but it is a statement about the KEPT set only, and the record names "
        "what the bound dropped",
    )
