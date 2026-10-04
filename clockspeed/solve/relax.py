"""CS-1237 - a transparent, fixed-order constraint-relaxation ladder over pillar 2.

When a request has no feasible selection, the question a player actually has is
"what would I have to give up to get a plan". This module answers it the only
way that stays deterministic and explainable: it loosens ONE named constraint at
a time, in an order fixed by ONE data table, re-solves through the ordinary door
(:func:`~clockspeed.solve.optimize.optimize_plan`), and stops at the first rung
that yields a plan. What comes back is the plan plus a structured record of
exactly which constraints were loosened and how. The record is the data a later
advisor rule trace projects into an explanation; nothing here renders prose for
a player.

WHY THE LADDER LIVES IN solve/ AND COVERS ONLY TWO CONSTRAINTS
----------------------------------------------------------------
``clockspeed/progress/`` holds no router yet and ``clockspeed/advisor/`` holds
no rule trace, so there is nothing above this layer to own the ladder. It is
built over the constraints :class:`~clockspeed.solve.optimize.OptimizeRequest`
carries TODAY, and over nothing it does not: a rung for a constraint that does
not exist would be a rung that can never fire, which reads as coverage and is
none. Power cap, node subset and clock ceiling rungs join the table when those
constraints exist on the request.

THE TABLE, AND WHY IT IS IN THIS ORDER
----------------------------------------
:data:`RELAXATION_LADDER`, least to most severe:

1. ``byproduct-sinkable`` - ``byproduct_policy`` from ``balanced`` to
   ``sinkable``. An unconsumed byproduct may be vented instead of forced to
   balance. The plan still uses only unlocked recipes, and the vented items are
   REPORTED on the plan's ``byproducts`` rather than hidden, so the player can
   still build it today.
2. ``admit-locked`` - ``unlocked`` widened to include every candidate. The plan
   may now use a recipe the player has not unlocked. That is the wish list the
   optimizer exists to refuse, which is exactly why it is LAST and why the
   record names every recipe it admitted rather than saying "some".

A rung whose transform would not change the request - the policy is already
``sinkable``, or every candidate is already unlocked - is SKIPPED: it is not
solved, not reported in the record, and not named as tried in a refusal. A no-op
reported as a relaxation would claim a constraint was given up that never bound.

WHY THERE IS NO INTERMEDIATE-AS-RAW RUNG
------------------------------------------
Declaring an intermediate item raw is a real constraint on the request
(``raw_items``), but no single deterministic transform of it is well defined.
Declaring EVERY non-target ingredient raw makes nearly any request trivially
feasible from one recipe, so the "plan" says nothing about production and the
record would amount to "assumed everything is free". Declaring a MINIMAL set raw
is a combinatorial choice with no unique answer - two different items can each
unblock the same chain - so the ladder would be choosing which supply to invent,
and that choice would carry no stated reason. Both readings fail the
transparency the ladder exists for, so the rung is left out until a request
carries a statement of which items the player can actually import.

WHY THE LADDER IS CUMULATIVE
------------------------------
Each rung applies ON TOP of every rung before it that applied, rather than each
rung being tried alone against the original request. Two reasons:

- A request that needs two constraints loosened at once is answered rather than
  refused. Tried one at a time, it would fail every rung and the refusal would
  wrongly suggest nothing short of a different request could help.
- The record then describes EXACTLY the request that was solved: every step in
  it was in force for the returned plan, in table order, and the first step is
  the first constraint given up. A single-from-original ladder would publish a
  plan whose request differs from the stated one in a way the record does not
  fully describe once two rungs interact.

The cost, stated plainly: an earlier rung that did not by itself rescue the
request stays applied. Because the table is ordered least severe first, what the
record lists is the shortest PREFIX of the ladder that yields a plan - which is
the transparent unit the ladder offers, not a claim that every listed rung was
individually necessary.

WHICH REFUSALS MEAN "INFEASIBLE"
----------------------------------
Exactly one: :class:`~clockspeed.solve.optimize.NoFeasibleSelectionError`. Every
pillar 1 refusal that describes an infeasible chain - ``UnsolvableChain``,
``InfeasibleChain``, ``UnderdeterminedChain`` - is already absorbed per
selection by ``solve_selection`` and surfaces from a backend as that one error,
so it is the single signal that "nothing in the searched space solves". With the
greedy backend that signal is the heuristic's own verdict, and the ladder
inherits it rather than second-guessing it; the exhaustive backend's is proof.

Every other refusal propagates UNRELAXED, because it does not say the request is
infeasible - it says the request is malformed or unanswerable as asked:
``ValueError`` (a candidate the registry does not model), ``ObjectiveUndefinedError``,
``PowerNotComparableError``, ``SearchSpaceTooLargeError`` (which the admit rung
can itself provoke by widening the usable set past the exhaustive cap - a loud
refusal, never a silent switch of backend), and ``UnknownBackendError``.

One pillar 1 refusal needs a door of its own: ``ByproductPolicyRequired``.
``solve_selection`` absorbs it like any other pillar 1 refusal, so through
``optimize_plan`` alone a misspelt policy arrives looking exactly like
infeasibility, and the ladder would "relax" a typo into a plan. The policy is
therefore checked against ``BYPRODUCT_POLICIES`` before the first solve.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Final

from clockspeed.data.registry import Registry
from clockspeed.solve.exact import audit_exact
from clockspeed.solve.optimize import (
    NoFeasibleSelectionError,
    OptimizeRequest,
    OptimizeResult,
    optimize_plan,
    registry_order,
)
from clockspeed.solve.ratio import (
    BYPRODUCT_BALANCED,
    BYPRODUCT_POLICIES,
    BYPRODUCT_SINKABLE,
    ByproductPolicyRequired,
)

__all__ = [
    "RELAXATION_LADDER",
    "RUNG_ADMIT_LOCKED",
    "RUNG_BYPRODUCT_SINKABLE",
    "LadderExhaustedError",
    "RelaxationRecord",
    "RelaxationStep",
    "RelaxedResult",
    "Rung",
    "optimize_with_relaxation",
]

#: The rung that vents unconsumed byproducts instead of balancing them.
RUNG_BYPRODUCT_SINKABLE: Final = "byproduct-sinkable"

#: The rung that admits every candidate the request named but had not unlocked.
RUNG_ADMIT_LOCKED: Final = "admit-locked"


@dataclass(frozen=True)
class RelaxationStep:
    """One constraint loosened, in exact terms.

    Uniform across rungs so a consumer reads every step the same way: the
    request field that changed, and precisely which values left it and which
    entered it.

    Attributes:
        rung: The rung's name, as :data:`RELAXATION_LADDER` lists it.
        field: The :class:`~clockspeed.solve.optimize.OptimizeRequest` field the
            rung changed.
        removed: The values that left that field. For a scalar field, its old
            value; for a set-like field, the members dropped.
        added: The values that entered it. For a scalar field, its new value;
            for a set-like field, the members added, in registry order.
    """

    rung: str
    field: str
    removed: tuple[str, ...]
    added: tuple[str, ...]


@dataclass(frozen=True)
class RelaxationRecord:
    """Every constraint the ladder loosened to reach the returned plan.

    Attributes:
        steps: The applied steps, in ladder order. Never empty: a request that
            needed no relaxation gets no record at all rather than an empty one.
    """

    steps: tuple[RelaxationStep, ...]

    @property
    def first(self) -> RelaxationStep:
        """The first constraint given up - the one the ladder reached first."""
        return self.steps[0]


@dataclass(frozen=True)
class Rung:
    """One rung of the ladder: a named, pure transform loosening ONE field.

    Attributes:
        name: The rung's stable name, recorded on every step it produces.
        field: The request field this rung loosens, and the only one it touches.
        loosens: One sentence saying what the rung gives up, for a reader of the
            table.
        apply: The transform. Pure: it reads the registry and the request and
            returns the loosened request with the step describing the change,
            or None when the rung would change nothing.
    """

    name: str
    field: str
    loosens: str
    apply: Callable[[Registry, OptimizeRequest], tuple[OptimizeRequest, RelaxationStep] | None]


@dataclass(frozen=True)
class RelaxedResult:
    """A plan, and what had to be given up to get it.

    Attributes:
        result: The optimizer's result for the request actually solved.
        record: What was loosened, or None when the request was feasible as
            stated and nothing was.
    """

    result: OptimizeResult
    record: RelaxationRecord | None


class LadderExhaustedError(NoFeasibleSelectionError):
    """No rung of the ladder - nor all of them together - yields a plan.

    A subclass of :class:`~clockspeed.solve.optimize.NoFeasibleSelectionError`,
    so a caller already handling "no plan" handles this without change.

    Attributes:
        tried: The names of every rung that was applied, in ladder order. A rung
            that would have changed nothing was skipped and is not listed.
    """

    def __init__(self, tried: tuple[str, ...], message: str) -> None:
        """Record the rungs tried alongside the message.

        Args:
            tried: The applied rung names, in ladder order.
            message: The full explanation.
        """
        super().__init__(message)
        self.tried = tried


def _vent_byproducts(
    _registry: Registry, request: OptimizeRequest
) -> tuple[OptimizeRequest, RelaxationStep] | None:
    """Loosen ``byproduct_policy`` from balanced to sinkable.

    Args:
        _registry: Unused; every rung takes the same arguments.
        request: The request.

    Returns:
        The loosened request and its step, or None when the policy is not
        ``balanced`` and there is nothing to loosen.
    """
    if request.byproduct_policy != BYPRODUCT_BALANCED:
        return None
    step = RelaxationStep(
        rung=RUNG_BYPRODUCT_SINKABLE,
        field="byproduct_policy",
        removed=(BYPRODUCT_BALANCED,),
        added=(BYPRODUCT_SINKABLE,),
    )
    return replace(request, byproduct_policy=BYPRODUCT_SINKABLE), step


def _admit_locked(
    registry: Registry, request: OptimizeRequest
) -> tuple[OptimizeRequest, RelaxationStep] | None:
    """Widen ``unlocked`` to admit every candidate it did not already hold.

    Args:
        registry: The built registry, for registry order.
        request: The request.

    Returns:
        The loosened request and its step, or None when every candidate is
        already unlocked. The admitted keys are listed in registry order, so a
        permuted candidate tuple produces the same step.
    """
    held = set(request.unlocked)
    admitted = registry_order(registry, (key for key in request.candidates if key not in held))
    if not admitted:
        return None
    step = RelaxationStep(rung=RUNG_ADMIT_LOCKED, field="unlocked", removed=(), added=admitted)
    return replace(request, unlocked=(*request.unlocked, *admitted)), step


#: THE ladder. One table, fixed order, least severe first; see the module
#: docstring for the order's reasoning and for the rung deliberately left out.
#: ``tests/solve/test_relax.py`` pins this order and reddens on a reorder.
RELAXATION_LADDER: Final[tuple[Rung, ...]] = (
    Rung(
        name=RUNG_BYPRODUCT_SINKABLE,
        field="byproduct_policy",
        loosens="an unconsumed byproduct may be vented and reported instead of balanced",
        apply=_vent_byproducts,
    ),
    Rung(
        name=RUNG_ADMIT_LOCKED,
        field="unlocked",
        loosens="a candidate recipe the player has not unlocked may be used",
        apply=_admit_locked,
    ),
)


def optimize_with_relaxation(registry: Registry, request: OptimizeRequest) -> RelaxedResult:
    """Solve as stated; if infeasible, climb the ladder until a plan appears.

    Args:
        registry: The built registry.
        request: The problem, as the caller stated it.

    Returns:
        The result with no record when the request is feasible as stated;
        otherwise the result of the first cumulative ladder prefix that solves,
        with the record of every step in that prefix. Audited exact.

    Raises:
        ByproductPolicyRequired: The policy is not one ratio.py accepts - refused
            at the door, never relaxed.
        LadderExhaustedError: The request and every applicable rung on top of it
            are infeasible; names every rung tried.
        ValueError, ObjectiveUndefinedError, PowerNotComparableError,
            SearchSpaceTooLargeError, UnknownBackendError: As
            :func:`~clockspeed.solve.optimize.optimize_plan` raises them, at
            whichever rung they arise. None of them means infeasible.
    """
    if request.byproduct_policy not in BYPRODUCT_POLICIES:
        raise ByproductPolicyRequired(
            request.byproduct_policy,
            f"byproduct_policy must be one of {', '.join(BYPRODUCT_POLICIES)}, not "
            f"{request.byproduct_policy!r}; an unusable policy is a malformed request, and "
            "relaxing it would turn a typo into a plan",
        )

    try:
        relaxed = RelaxedResult(result=optimize_plan(registry, request), record=None)
    except NoFeasibleSelectionError:
        pass
    else:
        audit_exact(relaxed, path="relaxed")
        return relaxed

    current = request
    steps: list[RelaxationStep] = []
    for rung in RELAXATION_LADDER:
        applied = rung.apply(registry, current)
        if applied is None:
            continue
        current, step = applied
        steps.append(step)
        try:
            result = optimize_plan(registry, current)
        except NoFeasibleSelectionError:
            continue
        relaxed = RelaxedResult(result=result, record=RelaxationRecord(steps=tuple(steps)))
        audit_exact(relaxed, path="relaxed")
        return relaxed

    tried = tuple(step.rung for step in steps)
    raise LadderExhaustedError(
        tried,
        "the request is infeasible as stated and stays infeasible with every applicable rung "
        f"of the relaxation ladder applied on top of it. Tried, in order: "
        f"{', '.join(tried) or 'none - no rung would change this request'}",
    )
