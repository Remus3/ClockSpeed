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

THE TRIM RULE, AND WHY A TARGET'S DERIVED ROUTE RANKS FIRST
-------------------------------------------------------------
The emitted rule is :data:`TRIM_ROUTE_FIRST`, which every step and every refusal
names. :data:`TRIM_RULES` is the closed vocabulary, so a rule cannot arrive
unnamed, and it still holds :data:`TRIM_TARGET_PRODUCERS_FIRST`, the rule CS-1245
shipped, which no path emits any more. The emitted rule ranks the usable candidates
by the key::

    (0, walk index, registry position)   a member of the derived route
    (1, walk depth, registry position)   the rest of the targets' backward closure
    (2, 0, registry position)            everything else

and keeps the first ``MAX_EXHAUSTIVE_CANDIDATES`` of that ranking. All three are
ints, no two candidates share a registry position, so the ranking is one strict order
and no float enters the key.

THE DERIVED ROUTE is :func:`derived_route`, over what
:func:`~clockspeed.solve.optimize.usable_candidates` lets through. Each item gets a
COUNT, an exact pair of ints compared as a tuple, ``(locked on the tree, recipes on
the tree)``. A raw item counts ``(0, 0)``, and any other item counts the least, over
its usable producers, of that producer's own cost plus the sum of its inputs' counts,
where a recipe costs ``(1 if a held set was stated and does not hold it else 0, 1)``.
With no held set, which is what the trim passes, the first int is always zero and the
count is recipes on a tree. A tie goes to the lower registry position, and that item's
CHOSEN PRODUCER is the recipe that won. The walk is breadth first from the targets in
sorted order, each recipe's inputs as listed, over chosen producers, stopping at raw
items and at items with no count, each recipe once.

THE COUNT IS THAT RULE'S LEAST FIXED POINT, reached by iterating to convergence from
nothing but the raw items, so a count only ever comes from a finished tree, each of
whose leaves is a raw item or a recipe with no inputs. An item no usable recipe reaches
that way never gets one, which is what makes a cycle safe: a loop no raw item enters has
no count and no chosen producer, and a loop with a way in takes the way in. A recipe's
own cost holds a recipe, so its sum sits strictly above each of its inputs' counts, and
every chosen producer's inputs therefore count strictly below the item it was chosen
for. Following chosen producers can never come back to an item, so the walk ends on any
cycle, and it names no recipe twice in any case. The same inequality bounds the
iteration. Counts only fall, and a least tree repeats no item along a path, so it is no
higher than the count of items; after that many passes every count is final, and one
more finds nothing to move. Tied producers are read off the converged counts in a
separate pass, so no tie is decided by which pass reached it first.

THE COUNT IS OF RECIPES ON A TREE: a recipe feeding two inputs counts twice. So the
route is deterministic and makes no claim of the fewest distinct recipes, which is a
harder question this module does not ask.

THE CLOSURE is the same kind of walk over EVERY usable producer rather than the chosen
one, stopping at raw items, and a recipe's walk depth is the depth of the nearest item
it makes, a target's producers at zero. It follows inputs and never byproducts. A
recipe reached only by consuming what a route member leaves over is outside it, so
under the balanced policy a route whose byproduct nothing kept consumes cannot solve
while that member runs a machine.
Unless other kept recipes answer the request that reads no-plan, which is scoped to the
kept set and the stated policy, and the player states the policy.

WHAT THIS KEEPS, AND WHAT THE CAP CAN STILL DROP. The tiers mean a derived route
within the cap is WHOLLY kept however large the closure around it, and a closure within
the cap is wholly kept, because each outranks what is outside it. That is the point of
the order. A bound that dropped a member of such a route can leave every prefix refused
and say "no plan" about a request a search over the route might well have answered - a
wrong answer dressed as an absence - and the shipped rule did that, keeping registry
order behind a target's direct producers whether or not it could feed them. But the cap
is still a cap, and these remain:

- A route over the cap loses its last members in walk order, so no prefix holds the
  whole route. Where every member is required that reads no-plan about the kept set, and
  the record names what fell. The cap does not move to cure it.
- The walk starts at the targets, so a counted target's chosen producer ranks ahead of
  every deeper member, and it falls only where the targets' own chosen producers
  outnumber the cap. A target's OTHER producers are ordinary closure members and can
  all fall, and so can every producer of a target with no count, once the members and
  closure ranking ahead of them fill the cap. So this module makes no claim that the
  bound never drops a target's last producer.
- Reachability is not feasibility. A route the count finds may still be refused, by a
  byproduct under the balanced policy above, and a loop with no count may still balance
  in pillar 1 if the kept set holds it. The count says which recipes to keep first and
  never whether they solve. That remains the ascent's to find out.

THE ORDER READS LITTLE, ON PURPOSE. The request's targets, by key, its raw items and
its usable candidates, and the registry. Never the objective, the byproduct policy, a
rate, a solve, a clock or a float. So one request has one ranking under every direction
and both policies, and :func:`trim_record` can state the cut before any search.

WHY EVERY ORDER HERE IS A TUPLE AND NEVER A SET
-------------------------------------------------
``clockspeed/advisor/trace.py`` records the reason in its own header: a set's
iteration order and its repr depend on PYTHONHASHSEED, so two runs would render
differently. A set is used below ONLY as a private membership test, and never to
decide an order; that includes a stated held set, which is never iterated. A mapping
below is read by key, or sorted before it is walked. :attr:`TrimStep.kept` and
:attr:`TrimStep.removed` are tuples, in registry order, both of them, and
:attr:`DerivedRoute.members` and :attr:`DerivedRoute.unmade` are tuples too, in walk
order and sorted.

THE ASCENT, AND WHY THE FIRST PREFIX THAT SOLVES IS THE SMALLEST
------------------------------------------------------------------
The ranking is computed once, before the ascent and from nothing a solve can move, so
it defines one chain of NESTED prefixes S_0 subset S_1 subset ... subset S_K, where
K is the smaller of the usable count and the cap, and S_k is the first k members
OF THE TRIM RANKING - not of registry order. The ascent runs k from 0 upwards
and returns the first prefix that yields a plan. Because the chain is nested,
that first k IS the smallest k whose prefix solves: every smaller prefix is a
SUBSET of it, and had any of them solved, the ascent would have reached that
smaller k first. That is a proof about the chain, not an early-exit heuristic, and
nothing in it depends on which rule ranked the chain.

What the rule adds is where the route sits in it. A route within the cap is exactly
the prefix of its own length, so under the exhaustive backend, whose search of a prefix
is complete, a route pillar 1 solves stops the ascent at that length or below. Below is
reachable: a member chosen for one item can make another as a byproduct, and a shorter
prefix can then solve, which is why the claim is about the smallest prefix and not about
the route. The greedy backend is a heuristic, and no such stop is promised under it.

S_0 is the empty prefix, an ordinary member of the chain and a subset of every
other one. ``exhaustive.py`` enumerates the empty selection as the answer to a
target rate of zero, so a well-formed request whose targets are all zero stops at
S_0 with the empty selection, whatever the usable set holds. When the usable set
is empty S_0 is the whole chain, and the plan it returns there is the one
``optimize_plan`` returns for the original request. A nonzero target in a
well-formed request is refused at S_0 with ``NoFeasibleSelectionError`` by both
shipped backends, which the ascent absorbs as it does at any prefix. So no request
needs a rule of its own, and the proof above and the arithmetic below hold with no
exemption.

WELL-FORMED is carrying weight there. An inexact rate, an item declared both raw
and a target, or an unregistered backend is refused at S_0 instead, as
:func:`optimize_within_bound` lists. An unrecognized byproduct policy is the odd
one out, because it does not surface as a shape refusal: pillar 1 raises a
``RatioError``, ``optimize.solve_selection`` reads every ``RatioError`` as "not
this selection", so every prefix refuses and the caller sees
:class:`BoundExhaustedError` even when every target is zero. The exception to that
is the greedy backend with no targets at all over a reachable candidate: its probe
solves under the sinkable policy whatever the request says, so the walk at size
one reaches pillar 1's crash, named under THE CONSEQUENCE below.

(Each narrowed request may hand its prefix over in any order, because
``optimize.usable_candidates`` sorts the door into registry order itself. The
prefix is passed in ranking order purely because that is the order it was built
in.)

Inside one prefix, the winner is whichever backend the request configured,
untouched - which for the exhaustive backend is the oracle's own
``optimize.result_ranking_key``, and for the greedy backend is the
lowest-ranking, by that same key, of the selections that heuristic's walk
reached (CS-1347). This module changes neither.

Only ``NoFeasibleSelectionError`` is absorbed as "not this
prefix", on exactly ``relax.py``'s reasoning: every other refusal says the
request is malformed or unanswerable as asked rather than infeasible, so it is a
shape bug rather than that prefix's answer, and swallowing it would turn one
into a plan.

THE COST BOUND, AS ARITHMETIC
-------------------------------
Prefix S_k has k members, so the exhaustive backend evaluates (1 << k) subsets
of it. The whole ascent therefore evaluates at most::

    (1 << 0) + (1 << 1) + ... + (1 << K)  ==  (1 << (K + 1)) - 1

subsets. The single capped search this replaces evaluates (1 << K). So bounding
by prefixes costs a factor of just under two, and never an unbounded run. For
K at the shipped cap of twelve that is 8191 subsets against 4096. An ascent that
stops at prefix k evaluates (1 << (k + 1)) - 1 of them. That arithmetic holds over any
ranking, because the bound is on the chain's length and not its order.

The ranking itself evaluates no subset and runs no solve. Its own cost is the count's
passes, at most one per item and one more as argued above, each over the usable recipes
and their inputs, one further such pass to read off the ties, then linear walks and a
sort.

THE CONSEQUENCE, STATED PLAINLY
---------------------------------
Because k dominates the order, this function CAN return a plan that scores WORSE
than the best plan over the whole trimmed set. The order it implements is
lexicographic ``(k: int, score: Fraction, positions: tuple[int, ...])`` with k
OUTERMOST, so a cheaper plan that needs one more recipe than the smallest
feasible prefix is not chosen. That is the specified behaviour rather than a
defect, and :class:`TrimRecord` plus :attr:`BoundedResult.chosen_size` are what
make the trade visible to the caller instead of silent, and a refusal carries the
same record on :attr:`BoundExhaustedError.record`, because no plan over the kept set
says nothing about what the cap dropped. :func:`trim_record` states that record
before any search, for a caller whose ascent ends some other way. A caller who wants
the whole-set optimum calls ``optimize_plan`` and gets the refusal.

Two narrower consequences, for the same honesty:

- The returned :attr:`~clockspeed.solve.optimize.OptimizeResult.excluded` notes
  describe the NARROWED request, so candidates the caller named but the door
  excluded - locked, or zero duration - are not listed on it, including on a
  request the door left empty, where the plan is the one ``optimize_plan`` returns
  and the notes are not. The trim record names what the BOUND dropped; what the
  DOOR dropped is read by calling ``optimize.usable_candidates`` on the original
  request.
- On ``targets={}`` over a non-empty usable set this function returns the empty
  plan at S_0 where ``optimize_plan`` can crash with a ``ValueError`` from
  ``ratio.py``'s ``_plan_from`` - under the greedy backend, or under the sinkable
  policy on either backend, once a selection leaves its system with no balance
  row - and the empty plan is the right answer and the crash is pillar 1's.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from typing import Final

from clockspeed.data.registry import Recipe, Registry
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
    "TRIM_ROUTE_FIRST",
    "TRIM_RULES",
    "TRIM_TARGET_PRODUCERS_FIRST",
    "BoundExhaustedError",
    "BoundedResult",
    "DerivedRoute",
    "TrimRecord",
    "TrimStep",
    "derived_route",
    "optimize_within_bound",
    "trim_record",
]

#: The trim rule CS-1245 shipped: direct producers of a requested item ahead of
#: everything else, then registry order. NO PATH EMITS THIS NAME ANY MORE. It stays
#: a member of :data:`TRIM_RULES` so the vocabulary still names everything it ever
#: held, and so nothing else can ever be given this name.
TRIM_TARGET_PRODUCERS_FIRST: Final = "target-producers-first"

#: The trim rule every record and every refusal now names: a target's derived route
#: first, then the rest of its backward closure, then everything else. The module
#: docstring states the order and what it keeps.
TRIM_ROUTE_FIRST: Final = "route-first"

#: THE closed vocabulary of trim rules, stated as a tuple so that a rule has to JOIN
#: it rather than arriving unnamed on a step. No path emits the first member any more;
#: see its own comment. ``tests/solve/test_bound.py`` pins the membership.
TRIM_RULES: Final[tuple[str, ...]] = (TRIM_TARGET_PRODUCERS_FIRST, TRIM_ROUTE_FIRST)

#: The trim rule's first tier: the recipe is a member of the derived route.
_TIER_ROUTE: Final = 0

#: Its second tier: the rest of the targets' backward closure, stopping at raw items.
_TIER_CLOSURE: Final = 1

#: Its third tier: everything else, which has no walk to rank by, so its middle key is
#: this one value and registry position alone decides.
_TIER_EVERYTHING_ELSE: Final = 2
_NO_DEPTH: Final = 0

#: A raw item's count: no locked recipe and no recipe on its tree. Every recipe's cost
#: holds a recipe, so this is below every other count and no recipe displaces it.
_RAW_COUNT: Final[tuple[int, int]] = (0, 0)


@dataclass(frozen=True)
class DerivedRoute:
    """One deterministic way to make a request's targets from its raw items.

    A statement about reachability, and never that the route solves: it reads no rate
    and no byproduct policy, so pillar 1 may still refuse it. It is one route chosen by
    a stated count and no claim of the fewest distinct recipes. The module docstring
    states the count, and :func:`derived_route` computes it.

    Attributes:
        members: The recipes on the route, each once, in breadth-first walk order from
            the targets in sorted order, each recipe's inputs as listed. Empty when no
            target has a route.
        complete: True when every target is a raw item or has a count, so the route
            reaches all of them. False says some target has none, and :attr:`unmade`
            names why only where the gap is an item nothing makes; a cycle no raw item
            enters leaves False here and nothing there.
        unmade: The items in the targets' backward closure that no usable recipe makes
            and the raw items lack, sorted. A tuple for the reason the module docstring
            gives. The closure walks every usable producer, on the route or not, so an
            item here need not be what a member of the route eats.
    """

    members: tuple[str, ...]
    complete: bool
    unmade: tuple[str, ...]


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
    """Every narrowing applied before the ascent, on a returned plan or on its refusal.

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
        chosen_size: The size of the winning prefix, 0 when the empty prefix
            answers the request. ALWAYS present, including when :attr:`record`
            is None, because it describes the ascent rather than the trim.
            Together with the record it is what makes the smallest-prefix trade
            visible instead of silent.
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
        tried: How many prefixes were evaluated, the empty prefix included, so
            never zero. Exactly one when the usable set was empty and at least
            two otherwise, which is a distinguishable and honest answer rather
            than the same refusal as an ascent over candidates that found
            nothing.
        record: What the bound dropped before the ascent ran, or None when every
            usable candidate fit under the cap. The refusal is a statement about
            the kept set only, so what was never asked about travels with it.
    """

    def __init__(
        self, cap: int, rule: str, tried: int, message: str, *, record: TrimRecord | None = None
    ) -> None:
        """Record the bound alongside the message.

        Args:
            cap: The cap the ascent was bounded by.
            rule: The trim rule's name.
            tried: How many prefixes were evaluated.
            message: The full explanation.
            record: What the bound dropped, or None when nothing was.
        """
        super().__init__(message)
        self.cap = cap
        self.rule = rule
        self.tried = tried
        self.record = record


def _tree_cost(
    recipe: Recipe, counts: dict[str, tuple[int, int]], held: frozenset[str] | None
) -> tuple[int, int] | None:
    """What one recipe's tree counts, at the counts known so far.

    Args:
        recipe: The recipe.
        counts: The count of every item that has one so far.
        held: The recipes not to be counted as locked, or None when none is locked. A
            membership test only.

    Returns:
        The exact ``(locked on the tree, recipes on the tree)`` pair: the recipe's own
        cost plus the sum of its inputs' counts. None while any input has no count.
    """
    locked = 1 if held is not None and recipe.key not in held else 0
    recipes = 1
    for entry in recipe.inputs:
        count = counts.get(entry.item_key)
        if count is None:
            return None
        locked += count[0]
        recipes += count[1]
    return (locked, recipes)


def _chosen_producers(
    registry: Registry,
    usable: tuple[str, ...],
    raw_items: tuple[str, ...],
    held: frozenset[str] | None,
) -> dict[str, str]:
    """Each counted item's chosen producer, at the count's least fixed point.

    Args:
        registry: The built registry.
        usable: The pool, in registry order.
        raw_items: The raw items, which count :data:`_RAW_COUNT` and get no producer.
        held: As :func:`derived_route` takes it.

    Returns:
        Item to chosen producer, for every item that has a count and is not raw. Read
        by key only; its insertion order decides nothing.
    """
    counts = dict.fromkeys(raw_items, _RAW_COUNT)
    moved = True
    while moved:
        moved = False
        for key in usable:
            recipe = registry.recipes[key]
            cost = _tree_cost(recipe, counts, held)
            if cost is None:
                continue
            for output in recipe.outputs:
                known = counts.get(output.item_key)
                if known is None or cost < known:
                    counts[output.item_key] = cost
                    moved = True

    # A second pass, over converged counts, so no tie can be decided by what a pass
    # happened to reach first. The pool is in registry order, so the first recipe
    # matching an item's count is that count's lowest registry position.
    chosen: dict[str, str] = {}
    for key in usable:
        recipe = registry.recipes[key]
        cost = _tree_cost(recipe, counts, held)
        if cost is None:
            continue
        for output in recipe.outputs:
            if output.item_key not in chosen and cost == counts[output.item_key]:
                chosen[output.item_key] = key
    return chosen


def _route_walk(
    registry: Registry, targets: tuple[str, ...], chosen: dict[str, str]
) -> tuple[str, ...]:
    """Walk the chosen producers back from the targets, breadth first.

    Args:
        registry: The built registry.
        targets: The targets, sorted.
        chosen: As :func:`_chosen_producers` returns it. A raw item and an item with no
            count are both absent from it, so the walk stops at each.

    Returns:
        The members in walk order, each recipe once. A chosen producer's inputs count
        strictly below the item it was chosen for, so no walk here can cycle, and the
        once-only membership would end one anyway.
    """
    members: list[str] = []
    named: set[str] = set()
    queue = deque(targets)
    while queue:
        key = chosen.get(queue.popleft())
        if key is None or key in named:
            continue
        named.add(key)
        members.append(key)
        queue.extend(entry.item_key for entry in registry.recipes[key].inputs)
    return tuple(members)


def _closure_walk(
    registry: Registry,
    usable: tuple[str, ...],
    targets: tuple[str, ...],
    raw: frozenset[str],
) -> tuple[dict[str, int], tuple[str, ...]]:
    """Walk every usable producer back from the targets, stopping at raw items.

    Follows inputs and never byproducts: nothing here reads what a recipe's other
    outputs might feed, so a recipe reached only through a byproduct is outside it.

    Args:
        registry: The built registry.
        usable: The pool, in registry order.
        targets: The targets, sorted.
        raw: The raw items. A membership test only.

    Returns:
        Recipe to its walk depth, the depth of the nearest item it makes, with a
        target's producers at zero; and the items reached that no usable recipe makes
        and raw items lack, sorted. The mapping is read by key only.
    """
    producers: dict[str, list[str]] = {}
    for key in usable:
        for output in registry.recipes[key].outputs:
            producers.setdefault(output.item_key, []).append(key)

    depths: dict[str, int] = {}
    unmade: list[str] = []
    visited: set[str] = set()
    level = list(targets)
    depth = 0
    while level:
        next_level: list[str] = []
        for item in level:
            if item in raw or item in visited:
                continue
            visited.add(item)
            makers = producers.get(item)
            if makers is None:
                unmade.append(item)
                continue
            for key in makers:
                if key not in depths:
                    depths[key] = depth
                    next_level.extend(entry.item_key for entry in registry.recipes[key].inputs)
        level = next_level
        depth += 1
    return depths, tuple(sorted(unmade))


def derived_route(
    registry: Registry, request: OptimizeRequest, *, held: frozenset[str] | None = None
) -> DerivedRoute:
    """Derive one deterministic route to a request's targets, running no search.

    The module docstring states the count and why it ends. The pool is what
    :func:`~clockspeed.solve.optimize.usable_candidates` lets through, so a recipe the
    door refuses counts for nothing here.

    Args:
        registry: The built registry.
        request: The problem. Only its targets, raw items, candidates and unlocked set
            are read, and of the targets only the keys.
        held: The recipes to count as not locked, or None when none is locked, which
            makes the first int of every count zero. A membership test only and never
            iterated, so it can decide no order but through the count itself. The trim
            omits it.

    Returns:
        The route.

    Raises:
        ValueError: A candidate names no recipe in this registry, as the door refuses it.
    """
    usable, _excluded = usable_candidates(registry, request)
    targets = tuple(sorted(request.targets))
    raw = frozenset(request.raw_items)
    chosen = _chosen_producers(registry, usable, request.raw_items, held)
    _depths, unmade = _closure_walk(registry, usable, targets, raw)
    return DerivedRoute(
        members=_route_walk(registry, targets, chosen),
        complete=all(item in raw or item in chosen for item in targets),
        unmade=unmade,
    )


def _trim_ranking(registry: Registry, request: OptimizeRequest) -> tuple[str, ...]:
    """Rank the usable candidates by :data:`TRIM_ROUTE_FIRST`.

    Reads the request's targets, by key, its raw items and its usable candidates, and
    the registry. It reads no objective, no byproduct policy and no rate, runs no solve,
    and asks for no held set, so one request has one ranking however it is then judged.

    Args:
        registry: The built registry.
        request: The problem, as the caller stated it.

    Returns:
        Every usable candidate exactly once, ranked: the route's members by walk order,
        then the rest of the targets' backward closure by walk depth, then everything
        else, registry position deciding within a depth and within the last tier. A
        tuple, and the only order this module's ascent reads.

    Raises:
        ValueError: A candidate names no recipe in this registry, raised by
            :func:`~clockspeed.solve.optimize.usable_candidates` at the door.
    """
    usable, _excluded = usable_candidates(registry, request)
    route = derived_route(registry, request).members
    # Both mappings are read by key only, and each builds from a tuple's order.
    walk_index = {key: index for index, key in enumerate(route)}
    depths, _unmade = _closure_walk(
        registry, usable, tuple(sorted(request.targets)), frozenset(request.raw_items)
    )
    positions = registry_positions(registry)

    def rank(recipe_key: str) -> tuple[int, int, int]:
        """Rank one candidate.

        Args:
            recipe_key: The candidate's recipe key.

        Returns:
            Its ``(tier, walk index or depth, registry position)`` key. All ints.
        """
        position = positions[recipe_key]
        walked = walk_index.get(recipe_key)
        if walked is not None:
            return (_TIER_ROUTE, walked, position)
        depth = depths.get(recipe_key)
        if depth is not None:
            return (_TIER_CLOSURE, depth, position)
        return (_TIER_EVERYTHING_ELSE, _NO_DEPTH, position)

    return tuple(sorted(usable, key=rank))


def _record_of(registry: Registry, ranked: tuple[str, ...]) -> TrimRecord | None:
    """Record what the cap drops from one ranking.

    Args:
        registry: The built registry.
        ranked: Every usable candidate, as :func:`_trim_ranking` ranks them.

    Returns:
        The record, or None when every candidate fits under the cap.
    """
    if len(ranked) <= MAX_EXHAUSTIVE_CANDIDATES:
        return None
    step = TrimStep(
        rule=TRIM_ROUTE_FIRST,
        cap=MAX_EXHAUSTIVE_CANDIDATES,
        kept=registry_order(registry, ranked[:MAX_EXHAUSTIVE_CANDIDATES]),
        removed=registry_order(registry, ranked[MAX_EXHAUSTIVE_CANDIDATES:]),
    )
    return TrimRecord(steps=(step,))


def trim_record(registry: Registry, request: OptimizeRequest) -> TrimRecord | None:
    """Say what :func:`optimize_within_bound` drops from a request, running no search.

    The trim reads the request's targets, raw items and usable candidates and the
    registry, and never a solve, so a caller can state it whichever way the ascent then
    ends: the refusals that are not :class:`BoundExhaustedError` propagate carrying no
    record.

    Args:
        registry: The built registry.
        request: The problem, as the caller stated it.

    Returns:
        The record that ascent would hold, or None when nothing is dropped.

    Raises:
        ValueError: A candidate names no recipe in this registry, as the ascent's
            own door refuses it.
    """
    return _record_of(registry, _trim_ranking(registry, request))


def optimize_within_bound(registry: Registry, request: OptimizeRequest) -> BoundedResult:
    """Trim to the cap by a named rule, then take the smallest prefix that solves.

    The module docstring holds the argument: why the trim is above the seam, why a
    target's derived route ranks first and what the cap can still drop, why the first
    solving prefix is provably the smallest, the cost bound as arithmetic, and the
    plans this order deliberately does not return.

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
            cap, the rule and how many prefixes were tried, the empty one
            included, and carries the record of what the bound dropped. An
            unrecognized byproduct policy reads this way too, for the reason the
            module docstring gives.
        ValueError: A candidate names no recipe in this registry, refused at the
            door before the ascent starts, or an item is declared both raw and a
            target, refused by pillar 1 at the empty prefix. Also pillar 1's
            crash, on the one unrecognized-policy request the module docstring
            names.
        InexactValueError, UnknownBackendError: As
            :func:`~clockspeed.solve.optimize.optimize_plan` raises them, at the
            empty prefix, which every request the door admits reaches - an empty
            usable set included, so neither reads as exhaustion there. Neither
            means infeasible, so neither is absorbed.
        ObjectiveUndefinedError, PowerNotComparableError: As ``optimize_plan``
            raises them, at whichever prefix they arise. Neither means
            infeasible, so neither is absorbed.
        SearchSpaceTooLargeError: Only reachable if the trim above were wrong,
            since every prefix is at most ``MAX_EXHAUSTIVE_CANDIDATES`` long. It
            is left to propagate deliberately - the module docstring's safety
            floor.
    """
    ranked = _trim_ranking(registry, request)
    limit = min(len(ranked), MAX_EXHAUSTIVE_CANDIDATES)
    record = _record_of(registry, ranked)

    # The nested chain, smallest first, from the empty prefix S_0 on every
    # request. One loop and no special case: the module docstring's proof and
    # cost bound both cover S_0 as an ordinary member of the chain.
    for size in range(limit + 1):
        try:
            result = optimize_plan(registry, replace(request, candidates=ranked[:size]))
        except NoFeasibleSelectionError:
            continue
        bounded = BoundedResult(result=result, record=record, chosen_size=size)
        audit_exact(bounded, path="bounded")
        return bounded

    raise BoundExhaustedError(
        MAX_EXHAUSTIVE_CANDIDATES,
        TRIM_ROUTE_FIRST,
        limit + 1,
        f"no prefix of the {TRIM_ROUTE_FIRST} ranking yields a plan. "
        f"{len(ranked)} usable candidate(s) were ranked, bounded to a cap of "
        f"{MAX_EXHAUSTIVE_CANDIDATES}, and all {limit + 1} nested prefix(es) from size 0 "
        "upwards were evaluated and refused. Under the exhaustive backend, whose search of "
        "each prefix is complete, that is the absence of any plan over the kept set; "
        "under the greedy backend, a heuristic, it is not proof that none exists. Either "
        "way it is a statement about the KEPT set only, and this refusal's record names what "
        "the cap dropped, None when it dropped nothing",
        record=record,
    )
