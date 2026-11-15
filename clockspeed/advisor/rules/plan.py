"""CS-1346, CS-1351, CS-1371, CS-1373, CS-1379 and CS-1382: the plan family.

Two rules that read a plan.

WHAT THIS MODULE OWNS. Two rules and the adapters that feed them:

- :data:`ADOPT_RULE` (``plan.adopt``) reads one ranked plan - the
  :class:`~clockspeed.solve.ratio.ProductionPlan` and the
  :class:`~clockspeed.solve.strategy.StrategyBadge` that one
  :func:`~clockspeed.solve.strategy.rank_plans` call published for it - and,
  when the badge records at least one cleared rung, recommends building the
  plan for its targets. A plan that cleared NO rung against its reference is
  worse than that reference on every claim it could be compared on, so it is
  rejected, never advised, and the rejection settles the rule. Its trace carries the
  badge.
- :data:`REDESIGN_RULE` (``plan.redesign``) reads the one route a no-plan derives and
  solves, and recommends planning toward its targets. See THE MARKED ROUTE below.
- :func:`plan_inputs` offers one :class:`~clockspeed.solve.strategy.RankedPlan`
  as ``plan.adopt``'s inputs, each sourced to the ranked-plan field it came from,
  beside the unlock keys its recipes, their machines and its raw items' extractors need,
  the backend that ran the search, the display names of its targets and what the search
  left out.
  :func:`status_inputs` and :func:`refused_inputs` say
  why no plan is offered. :func:`redesign_inputs` and :func:`redesign_status_inputs`
  offer the route, or why there is none, and :func:`plan_outcome_of` projects the offer
  for a surface to transcribe. ``clockspeed/advisor/plans.py`` ranks the plan, solves
  the route and calls them; this module solves nothing.

THE BADGE IS TIER 3 ONLY. ``plan.adopt`` reads the badge through the engine, so the
trace carries it as an ``input-read`` step, and
:func:`clockspeed.advisor.cards.render_value` renders it field by field into
the derivation - the strongest rung, every cleared rung, and each rung's
verdict with both scores and the bound - generated from the trace and never
hand-written (non-negotiable 8). The headline is built from the labels of the
plan's target items alone (CS-1379, below) and the reason from those labels, their
rates, its machine total, what the search left out and, always last, the build caveat,
so tier 1 carries nothing of the badge and a different badge on the same plan moves
tier 3 alone.
``clockspeed/advisor/cards.py::Card`` gains no field: the badge reaches the card
only through the trace it is built from.

THE BACKEND IS TIER 3 ONLY, THE SAME WAY. A derivation differs by backend, and a rung
cleared against a heuristic's reference is not the claim an exact one makes, so
``plan.adopt`` reads ``plan.backend`` on the ranked path. It is the name the result itself
carries, never the environment value, and a name outside the closed vocabulary is a
rule error. It never reaches tier 1, tier 2 or the card id: on one plan the name moves
none of them; a different backend can rank a different plan, which moves tier 2.

A TARGET READS BY ITS DISPLAY NAME AND IS KEYED BY ITS CLASSNAME (CS-1379). A ClassName
is an internal identifier, and it can name a different item from the one a player knows,
so where a rule's tier 1 or tier 2 says a target it says that target's label. When the
display name is printable ASCII with a visible character, the engine's own test of a card's
text, is whitespace-normal, with no leading or trailing space and no run of two, and is at
most :data:`~clockspeed.advisor.rules.display_names.MAX_NAME_LENGTH` characters, the label is
that name inside double quotes, a double quote or backslash in it escaped by a backslash, so a
semicolon or a comma in it,
which a tier reads as its own clause and target separators, reads as part of one name and
the quote that closes it cannot be forged. Otherwise the label is the ClassName, unquoted, so
a quoted label is always a display name; a card's tiers collapse every whitespace run, so a
name that is not whitespace-normal would read as one the registry does not hold, and the cap
stays because a quoted name the length of a page would still read as the whole headline. A
rule reads only through the
engine, so the names arrive as an input sourced to the registry field, :data:`IN_TARGET_NAMES`
on the ranked path and :data:`IN_REDESIGN_TARGET_NAMES` on the route, which
``clockspeed/advisor/plans.py`` fills, and a mapping whose keys are not exactly the plan's
targets is a rule error. A fallback records one indeterminate step and never a rejection,
which would settle the rule, and it records that on the firing path alone, because a step
beside a rejection would unsettle it. The subject key, the card id and the order of the
targets stay by ClassName, so a renamed item orphans no recorded card. Tier 3 keeps every
ClassName in its steps; only its Advice and Because lines, which quote tiers 1 and 2, read
a label, so the derivation stays generated from the trace (non-negotiable 8).

WHY THE ENGINE ADMITS THESE TYPES. The solve layer declares its plan and badge
dataclasses frozen but without slots, which
:meth:`clockspeed.advisor.trace.RuleContext.read` refused outright before this
item. The engine admits exactly the five named in
:data:`clockspeed.advisor.trace.PLAN_TYPES`, by exact type, and only when an
instance holds nothing beyond its declared fields - see that module's
docstring.

ONE RANKING, ONE PAIR. The adapter takes a ``RankedPlan``, never a loose plan
and badge: :func:`~clockspeed.solve.strategy.rank_plans` publishes the two
together, so a caller passing its entries straight through cannot pair one
plan with another plan's badge. That stays true when the ranking grades each
rung against a reference of its own. A hand-built ``RankedPlan`` is not checked
against a ranking here; the badge's own consistency is (below).

A BADGE THAT DISAGREES WITH ITSELF IS A RULE ERROR. Its checks must name
every rung of :data:`~clockspeed.solve.strategy.STRATEGY_LADDER` in ladder
order, ``cleared`` must be exactly the cleared checks' rung names in that
order, and ``strongest`` the last of them or None - the shape
:func:`~clockspeed.solve.strategy.badge_for` publishes. A badge that breaks
any of these raises, which the engine records as a ``rule-error`` and no
card: advice is never built on a forged claim.

UNLOCKS TRAVEL THROUGH THE ENGINE. A plan names recipes by registry ClassName,
and the unlock state holds asset paths. The join between the two is
``clockspeed/advisor/plans.py``, which fills ``plan.requires`` with each recipe's key,
the key of a machine the world holds to run it and, for each raw item the plan consumes,
the key of a machine the world holds to extract it (CS-1382), and that is why it is a
REQUIRED keyword of :func:`plan_inputs` with no default: inventing an empty tuple here
would advise a plan over recipes nobody checked. The rule reads the keys and hands them to
``Recommendation.requires``, where :func:`clockspeed.advisor.trace.run_rule` checks
each against the world's unlocks, so a plan over a locked recipe, over a machine the world
does not hold or over an extractor it does not hold yields a ``precondition-unmet`` step
and no card. From ``advise_world`` no such plan reaches ``plan.adopt``, because the search
excludes the recipe and takes no such raw item first; the engine's check is the second
gate, and it does not trust the first. The rule itself declares no unlock, because what a
plan needs depends on that plan: "build this plan" needs what the plan's own recipes, the
machines that run them and the machines that extract its raw items need, and the join says
so per plan.

THE MARKED ROUTE (CS-1371). A no-plan speaks only for what the search kept, so
``clockspeed/advisor/plans.py`` then derives one route over every automated recipe the
join could check and solves it once. :data:`REDESIGN_RULE` reads the result. What it
requires is doable now, because its ``requires`` holds only the held recipes the solve
gives a machine count, a machine the world holds for each, and a machine the world holds
for each raw item the route consumes where it holds one, so the engine's check still
applies. Locked recipes do reach this rule, a recipe held with no machine held among
them, by ClassName, under :data:`IN_REDESIGN_LOCKED`, an input of their own: tier 3 reads
them, and tier 1, tier 2 and ``requires`` name none of them, so no locked stage reads as
buildable. A machine the route needs to extract a raw item the world cannot, and must
unlock first, travels the same way under :data:`IN_REDESIGN_LOCKED_EXTRACTORS`. Tier 2
says the targets by label, counts the stages and those machines and names none of them, and
says what the route is: the stated direction did not choose it, and it was never compared
with what is built. ONLY A ROUTE WITH NO LOCKED STAGE AND NO LOCKED EXTRACTOR says it needs
no unlock (CS-1382), and only then is everything it names in ``requires``, which the engine
checks, so the sentence cannot read over something the world does not hold. The card carries
no badge, because no ranking saw the route. A list that disagrees with the plan's own machines, a
status outside the closed vocabulary, and a status that disagrees with ``plan.status`` are
each a rule error. Its inputs stay out of :data:`PLAN_INPUTS`, so the ranked path and the
route never share a name.

A RAW ITEM NO EXTRACTOR JOINS IS SAID, NOT DROPPED (non-negotiable 7). The join leaves such
an item out of the search and off the route, so :data:`IN_RAW_UNKNOWN` names it wherever
:data:`IN_UNCHECKED` names a recipe the join could not check, and each rule reads it on the
same paths, a count in tier 2 and the names in tier 3.

EVERY FIGURE IS PRICED AT THE PINNED BUILD (CS-1288). A plan's machine counts
are solved from registry recipes, and the registry is the pinned build's. So
each rule declares :data:`clockspeed.advisor.build.BUILD_INPUTS` ahead of its
own inputs and calls :func:`clockspeed.advisor.build.build_caveat` FIRST, on
every path: off the pin its reason names both builds, last, and it settles nothing,
exactly as every registered rule does.

REGISTERED, AND THEY FIRE ONLY WHERE A CALLER STATES A TARGET (CS-1351). The family
is in ``clockspeed/advisor/rules/__init__.py::_FAMILIES``, and
``clockspeed/advisor/advise.py::inputs_of`` offers its inputs on every world, so
the CS-1285 slice C ruling G6 holds: no registered rule runs on a world that lacks
them. A caller states a target through ``plan_request``, as the advice routes of
``clockspeed/surface/api/advice.py`` do when asked (CS-1371). With none stated each
rule records why it is silent and yields no card.

NO TARGET IS NOT A MISSING INPUT, AND NO PLAN IS NOT A VERDICT. Every world offers
:data:`IN_STATUS` and :data:`REDESIGN_INPUTS`. A status other than :data:`STATUS_RANKED`
records one ``verdict-indeterminate`` step with a reason from a closed vocabulary and no
``plan.adopt`` card, and a route status other than :data:`REDESIGN_ROUTED` does the same
for ``plan.redesign``, never an ``input-missing`` step, and never a rejection, which would
settle the rule and let ``Ledger.reconcile`` complete a card whose target was merely
cleared. A status outside its vocabulary is a rule error.

THE FIRING PATH SETTLES NOTHING EITHER. A plan is ranked for a stated target, and a route
derived for one, and neither is compared with the world, so a card going away says
nothing about the world: the player may only have asked about something else. So firing
records one indeterminate step too, as :func:`clockspeed.advisor.build.build_caveat` does
off the pin, and a recorded card is never completed by a target that moved. Only a
rejection settles either rule: of a plan that cleared no rung, and of a route with no
machine on any step. From a world both are unreachable, because the top plan is one rung's
own optimum and a stated rate is above zero.

A PLAN MAY BE STATED FOR A SCHEMATIC (CS-1373). The question is still one :class:`PlanRequest`
whose targets are the schematic's cost items at the rates ``milestone_requirement`` publishes,
so both rules above answer it unchanged and a no-plan reads ONE marked route, never one per
item. What the schematic adds is :data:`IN_SCHEMATIC`, one input ``clockspeed/advisor/plans.py``
offers on every world: None where the caller stated no schematic, else a
:class:`SchematicStatement` naming it, its tier, each cost item's amount, the completion budget
and each derived rate. Both rules read it, so tier 3 names every one of them from the trace and
nothing is hand-written (non-negotiable 8), and a firing card takes the schematic's ClassName as
its ``target_milestone``, which is the third member of the BOOTSTRAP.md section 5.2 card id: the
same schematic reads the same id over any save, and an item statement at the same targets and
rates, with no milestone, reads another. A statement whose rates are not exactly the plan's
targets is a rule error, so a card cannot name a schematic it was not planned for. A schematic
with no rates reads :data:`STATUS_SCHEMATIC_UNPLANNABLE` before any join: both rules record why
they are silent, and :func:`plan_outcome_of` carries the reason word and names any cost
item off ``plan_targets`` in it, so no item is dropped from a request to make it plannable.

NO WORLD TOKEN, NO SAVE PATH, NO FLOAT. Every source names the field a value came
from, every unlock key is built from the registry's string rather than a save's, and
every figure is a ``Fraction``, the one count an ``int``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import BUILD_INPUTS, build_caveat
from clockspeed.advisor.cards import render_value
from clockspeed.advisor.rules.display_names import quoted, usable_name
from clockspeed.advisor.trace import InputValue, Recommendation, RuleContext, RuleSpec
from clockspeed.solve.backends import available_backends
from clockspeed.solve.ratio import ProductionPlan
from clockspeed.solve.strategy import STRATEGY_LADDER, StrategyBadge

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.solve.strategy import RankedPlan

#: The advice domain of this family.
DOMAIN: Final = "plan"

#: Why a plan is or is not on offer. Every world offers it.
IN_STATUS: Final = "plan.status"

#: What the join and the bound left out, offered wherever a join ran.
IN_UNCHECKED: Final = "plan.unchecked"
IN_RAW_UNKNOWN: Final = "plan.raw_unknown"
IN_UNMATCHED: Final = "plan.unmatched_unlocks"
IN_TRIMMED: Final = "plan.trimmed"

#: Input names offered only beside a ranked plan, by :func:`plan_inputs`.
IN_PLAN: Final = "plan.production"
IN_BADGE: Final = "plan.badge"
IN_REQUIRES: Final = "plan.requires"
IN_BACKEND: Final = "plan.backend"
IN_TARGET_NAMES: Final = "plan.target_names"

#: The schematic a plan was stated for (CS-1373): None when none was. Every adapter that offers
#: a status offers it beside, so a world offers it whatever it was asked, and both rules read it
#: where :data:`PLAN_INPUTS` lists it: after the join's words and before the plan.
IN_SCHEMATIC: Final = "plan.schematic"

#: Every input :data:`ADOPT_RULE` adds to the build inputs, in the order it reads them.
PLAN_INPUTS: Final = (
    IN_STATUS,
    IN_UNCHECKED,
    IN_RAW_UNKNOWN,
    IN_UNMATCHED,
    IN_TRIMMED,
    IN_SCHEMATIC,
    IN_PLAN,
    IN_BADGE,
    IN_REQUIRES,
    IN_BACKEND,
    IN_TARGET_NAMES,
)

#: Input names of the marked route, offered on every world and read by
#: :data:`REDESIGN_RULE` alone.
IN_REDESIGN_STATUS: Final = "plan.redesign.status"
IN_REDESIGN_PLAN: Final = "plan.redesign.plan"
IN_REDESIGN_HELD: Final = "plan.redesign.held"
IN_REDESIGN_LOCKED: Final = "plan.redesign.locked"
IN_REDESIGN_LOCKED_EXTRACTORS: Final = "plan.redesign.locked_extractors"
IN_REDESIGN_REQUIRES: Final = "plan.redesign.requires"
IN_REDESIGN_UNMADE: Final = "plan.redesign.unmade"
IN_REDESIGN_TARGET_NAMES: Final = "plan.redesign.target_names"

#: What unlocks each locked stage of the route (CS-1374): a :class:`RedesignUnlocks`, or None where
#: no route was solved or no schematic catalog was read.
IN_REDESIGN_UNLOCKS: Final = "plan.redesign.unlocks"

#: The route compared with what is built (CS-1375): a :class:`RedesignBuilt`, or None where no
#: route was solved or no machines model was handed to the plan offer.
IN_REDESIGN_BUILT: Final = "plan.redesign.built"

#: Every input the marked route offers, in the order the rule reads them. Apart from
#: :data:`PLAN_INPUTS`: the ranked path and the route never share a name.
REDESIGN_INPUTS: Final = (
    IN_REDESIGN_STATUS,
    IN_REDESIGN_PLAN,
    IN_REDESIGN_HELD,
    IN_REDESIGN_LOCKED,
    IN_REDESIGN_LOCKED_EXTRACTORS,
    IN_REDESIGN_REQUIRES,
    IN_REDESIGN_UNMADE,
    IN_REDESIGN_TARGET_NAMES,
    IN_REDESIGN_UNLOCKS,
    IN_REDESIGN_BUILT,
)

#: The search did not read no-plan, so no route was derived. Every world but a no-plan.
REDESIGN_NOT_REACHED: Final = "not-reached"

#: The route was derived and pillar 1 solved it, so it is on offer.
REDESIGN_ROUTED: Final = "routed"

#: The count found no route to some target, over every automated recipe the join could check.
REDESIGN_NO_ROUTE: Final = "no-route"

#: A route was derived and pillar 1 refused it, under the stated byproduct policy.
REDESIGN_ROUTE_REFUSED: Final = "route-refused"

#: A plan was ranked and is on offer.
STATUS_RANKED: Final = "ranked"

#: The caller stated no target, which is every request that does not name the four.
STATUS_NO_TARGET: Final = "no-target"

#: The caller stated a schematic whose requirement publishes no rates, or whose cost names an
#: item no plan can be stated for (CS-1373). Reached before any join, so no search ran.
STATUS_SCHEMATIC_UNPLANNABLE: Final = "schematic-unplannable"

#: Why a schematic is unplannable, each a word of this closed vocabulary. The first three are
#: ``clockspeed/progress/milestones.py``'s own reason words, spelled here so a rule reads no
#: progress module; a test holds each equal to its owner's.
REASON_COST_UNREADABLE: Final = "cost-unreadable"
REASON_NONPOSITIVE_COST: Final = "nonpositive-cost"
REASON_UNRESOLVED_COST_ITEM: Final = "unresolved-cost-item"
#: The schematic costs nothing, so there is nothing to plan.
REASON_EMPTY_COST: Final = "empty-cost"
#: A cost item is a raw resource, or no automated recipe makes it: off
#: ``clockspeed/data/registry.py::plan_targets``. The items are named beside it.
REASON_ITEM_NOT_PLANNABLE: Final = "item-not-plannable"

#: Every reason word a statement may carry.
UNPLANNABLE_REASONS: Final = (
    REASON_COST_UNREADABLE,
    REASON_NONPOSITIVE_COST,
    REASON_UNRESOLVED_COST_ITEM,
    REASON_EMPTY_COST,
    REASON_ITEM_NOT_PLANNABLE,
)

#: The question cannot be asked: bad targets, a bad rate, direction, policy or raw
#: items, or a refusal that says the request is malformed rather than unanswerable.
STATUS_REQUEST_MALFORMED: Final = "request-malformed"

#: The search found no plan over the unlocked automated recipes it kept, from the raw
#: items a held extractor supplies, under the stated byproduct policy. Nothing beyond that:
#: what the cap dropped is on :data:`IN_TRIMMED`, and a capped no-plan and an uncapped one
#: are this one status.
STATUS_NO_PLAN: Final = "no-plan"

#: The search refused for a reason that is no statement about the target.
STATUS_SOLVE_REFUSED: Final = "solve-refused"

#: Asked for by power, and some recipe the search reached has no exact draw.
STATUS_POWER_NOT_COMPARABLE: Final = "power-not-comparable"

_SOURCE_PREFIX: Final = "solve.strategy.ranked_plan."

#: The source of the status and of what the join left out.
_OFFER_SOURCE_PREFIX: Final = "advisor.plans."

#: The source of the unlock keys: the join, never a solve field.
_REQUIRES_SOURCE: Final = _OFFER_SOURCE_PREFIX + "recipe_unlock_join"

#: The source of what the bound dropped.
_TRIMMED_SOURCE: Final = "solve.bound.trim_record.removed"

#: The source of the backend's name: the result's own field, never the environment.
_BACKEND_SOURCE: Final = "solve.optimize.optimize_result.backend"

#: The source of a target's display name: the registry field it is read from.
_TARGET_NAME_SOURCE: Final = "registry.items.display_name"

#: The label of the one number the rule computes.
LABEL_MACHINES: Final = "plan machine equivalents"

#: The alternative a plan that cleared no rung loses as, and the one a status
#: other than ranked leaves undecided.
_ADOPT_ALTERNATIVE: Final = "build the ranked plan"

#: Why each status but ranked offers no plan: the closed vocabulary a trace reads.
_STATUS_REASONS: Final = MappingProxyType(
    {
        STATUS_NO_TARGET: "no target was stated, so no plan was ranked",
        STATUS_REQUEST_MALFORMED: "the stated request cannot be asked as a question",
        STATUS_NO_PLAN: (
            "the search found no plan over the unlocked automated recipes it kept,"
            " from the raw items a held extractor supplies, under the stated byproduct policy"
        ),
        STATUS_SOLVE_REFUSED: "the search refused, which says nothing about the target",
        STATUS_POWER_NOT_COMPARABLE: "the power search reached a recipe with no exact draw",
        STATUS_SCHEMATIC_UNPLANNABLE: (
            "the stated schematic publishes no rates a plan can be stated for, so no search ran"
        ),
    }
)

#: The two statuses whose reason needs nothing else read. No target is reached before
#: any join; a malformed request is too, unless a refusal after the join says so, as a
#: target declared raw does, and then what is offered beside it stays unread.
_UNJOINED_STATUSES: Final = (
    STATUS_NO_TARGET,
    STATUS_REQUEST_MALFORMED,
    STATUS_SCHEMATIC_UNPLANNABLE,
)

#: The comparison the firing path records as undecided.
_COMPARE_ALTERNATIVE: Final = "compare the plan with what is built"
_COMPARE_REASON: Final = "a plan is ranked for a stated target and never compared with the world"

#: Subject keys are this prefix and the plan's sorted target items, so a card's
#: identity names WHAT the plan makes and never a figure or a display name that may move.
SUBJECT_PREFIX: Final = "plan:"

#: What a target with no usable display name records, whichever target and however many. Fixed,
#: so it names no value.
_NAME_ALTERNATIVE: Final = "name every target by its display name"
_NAME_REASON: Final = "a target has no usable display name, so its ClassName names it"

#: The rung names in ladder order, which every badge's checks must follow.
_LADDER_NAMES: Final = tuple(strategy.name for strategy in STRATEGY_LADDER)

#: The source of the marked route's status and of the two lists it sorts its stages into.
_REDESIGN_SOURCE_PREFIX: Final = _OFFER_SOURCE_PREFIX + "redesign."

#: The source of the route's plan: the function that solved it, which no ranking touched.
_ROUTE_PLAN_SOURCE: Final = "solve.ratio.solve_for_targets"

#: The source of the route's unlock keys: the join, as on the ranked path.
_ROUTE_REQUIRES_SOURCE: Final = _REDESIGN_SOURCE_PREFIX + "recipe_unlock_join"

#: The source of what the route's closure reached that nothing makes.
_ROUTE_UNMADE_SOURCE: Final = "solve.bound.derived_route.unmade"

#: The source of the route's unlockers: the join of the schematic catalog and the registry.
_ROUTE_UNLOCKS_SOURCE: Final = _REDESIGN_SOURCE_PREFIX + "schematic_unlock_join"

#: The source of the route's comparison with what is built (CS-1375): the audit machines model
#: read against the solved route.
_ROUTE_BUILT_SOURCE: Final = _REDESIGN_SOURCE_PREFIX + "built_comparison"

#: The alternative the marked route records as undecided or, with no machine, as lost.
_REDESIGN_ALTERNATIVE: Final = "offer the derived route"

#: Why each status but routed offers no route: the closed vocabulary a trace reads, and a
#: surface too on :data:`_EXPLAINED_REDESIGN_STATUSES`.
_REDESIGN_REASONS: Final = MappingProxyType(
    {
        REDESIGN_NOT_REACHED: "the search did not read no-plan, so no route was derived",
        REDESIGN_NO_ROUTE: (
            "the count found no route to the target from the raw items, over every"
            " automated recipe with an unlock path to check, which does not prove no plan exists"
        ),
        REDESIGN_ROUTE_REFUSED: (
            "pillar 1 refused the derived route, solved once under the stated byproduct policy,"
            " which does not prove no plan exists"
        ),
    }
)

#: The two statuses whose reason :class:`PlanOutcome` carries beside the word (CS-1380). A
#: search read no-plan on each and no card follows, so a bare word would read as proof that no
#: plan exists, which neither status is.
_EXPLAINED_REDESIGN_STATUSES: Final = (REDESIGN_NO_ROUTE, REDESIGN_ROUTE_REFUSED)

#: The comparison the firing path records as undecided.
_ROUTE_COMPARE_ALTERNATIVE: Final = "compare the route with what is built"
_ROUTE_COMPARE_REASON: Final = (
    "a route is derived for a stated target and never compared with the world"
)

#: The rejection only a hand-built offer reaches: a stated rate is above zero.
_NO_MACHINE_REASON: Final = "the route gives no recipe a machine"

#: What a route's reason says about unlocking: its stages, its extractors, or neither.
_MUST_UNLOCK_CLAUSE: Final = (
    "; the locked recipes or the machines that run them must unlock first on this route"
)
_EXTRACTOR_UNLOCK_CLAUSE: Final = "; the locked extractors must unlock first on this route"

#: What it says with neither locked where the bound dropped nothing (CS-1382 F1), so no cap is
#: named. Of the cap it claims only that no recipe was dropped to fit it: the door has already
#: excluded a held recipe of zero duration, which the bound never saw. Where the bound dropped
#: some, :func:`_route_unlock_clause` names the cap and the count instead. Either way the clause
#: names the search's own starting point: the route may take as raw an item the world extracts
#: nothing for, which the search treats as an ordinary item, not a raw one.
_UNCAPPED_NO_UNLOCK_CLAUSE: Final = (
    "; this route needs no unlock and the search, which dropped no recipe to fit its cap,"
    " did not find it from the raw items a held extractor supplies"
)

#: What a route's reason says on every path: a count chose it, and no comparison did.
_NOT_CHOSEN_CLAUSE: Final = (
    "; the stated direction did not choose this route and it was never compared with what is built"
)

#: What it says instead wherever a machines model was handed to the offer (CS-1375): the
#: direction still did not choose the route, and the counts of the comparison follow.
_DIRECTION_ONLY_CLAUSE: Final = "; the stated direction did not choose this route"

#: Said beside those counts where the comparison ran and no machine names any recipe, so it
#: read unmeasured throughout. It ran, so the route was compared and the reading is unknown.
_UNMEASURED_CLAUSE: Final = "; the comparison read unmeasured, as no machine names a recipe"

#: The one clause naming a replace as the expensive change, said only where one reads.
_REPLACE_COSTS_CLAUSE: Final = "; replacing a built recipe is the expensive change"

#: The step the firing path records where the route was compared with what is built: the card
#: still settles nothing, because the target is the caller's and moves with a question.
_BUILT_COMPARE_ALTERNATIVE: Final = "settle the route's card on what is built"
_BUILT_COMPARE_REASON: Final = (
    "a route is derived for a stated target,"
    " so its card going away says nothing about what is built"
)


#: What one locked stage's unlockers read as (CS-1374). ``named``: at least one schematic unlocks
#: it, and the schematics are listed. ``none``: no schematic of a catalog every one of whose
#: unlock lists was read in full unlocks it. ``unknown``: no schematic read unlocks it, and some
#: schematic's unlocks could not be read in full, so one of those may.
UNLOCK_NAMED: Final = "named"
UNLOCK_NONE: Final = "none"
UNLOCK_UNKNOWN: Final = "unknown"

#: Every word an unlock reading may carry.
UNLOCK_READINGS: Final = (UNLOCK_NAMED, UNLOCK_NONE, UNLOCK_UNKNOWN)


@dataclass(frozen=True, slots=True)
class UnlockingSchematic:
    """One schematic that unlocks a recipe, with its tech tier (CS-1374).

    Slotted, so the engine admits it.

    Attributes:
        schematic: The schematic's ClassName.
        tech_tier: Its tier, or None when the catalog read none: an unknown tier is never zero.
    """

    schematic: str
    tech_tier: int | None


@dataclass(frozen=True, slots=True)
class LockedUnlock:
    """What unlocks one locked stage of the marked route (CS-1374).

    Attributes:
        recipe: The locked stage, by ClassName.
        machine: None when the schematics unlock the recipe itself. The ClassName of the machine
            when the world holds the recipe and no machine that runs it, and the schematics
            unlock that machine's build recipe.
        reading: One of :data:`UNLOCK_READINGS`.
        schematics: Every schematic unlocking it, lowest tier first, an unknown tier last, then
            by ClassName. Empty unless the reading is ``named``.
    """

    recipe: str
    machine: str | None
    reading: str
    schematics: tuple[UnlockingSchematic, ...]


@dataclass(frozen=True, slots=True)
class RedesignUnlocks:
    """What unlocks every locked stage of the marked route, and what the join left out (CS-1374).

    Attributes:
        locked: One entry per locked stage, in ascending order of the lowest tier among the
            schematics naming it, an entry naming no known tier last, then the route's registry
            order.
        unmatched: How many distinct recipe paths a schematic unlocks that join no recipe of the
            registry. A count, never dropped.
    """

    locked: tuple[LockedUnlock, ...]
    unmatched: int


#: What one row of the route-against-built comparison reads (CS-1375). ``more``: the route's
#: machine count for the stage exceeds the built capacity on its recipe, by the exact shortfall.
#: ``enough``: it does not. ``unmeasured``: the capacity of some machine on that recipe is
#: unknown, or no machine names any recipe at all. ``replace``: a recipe off the route that built
#: machines run makes an output of a route stage.
BUILT_MORE: Final = "more"
BUILT_ENOUGH: Final = "enough"
BUILT_UNMEASURED: Final = "unmeasured"
BUILT_REPLACE: Final = "replace"

#: Every word a comparison row may carry.
BUILT_READINGS: Final = (BUILT_MORE, BUILT_ENOUGH, BUILT_UNMEASURED, BUILT_REPLACE)


@dataclass(frozen=True, slots=True)
class BuiltRow:
    """One row of the route compared with what is built (CS-1375).

    Slotted, so the engine admits it. Every figure is an exact ``Fraction`` or a count.

    Attributes:
        recipe: The recipe's ClassName.
        reading: One of :data:`BUILT_READINGS`.
        route_machines: The route's machine count for a stage, at clock 1, or None on a
            ``replace`` row, which is no stage of the route.
        built_machines: How many built machines name this recipe, whatever their capacity.
        built_capacity: The sum of those machines' exact capacities, on ``more`` and ``enough``
            alone: None where any capacity is unknown, and on ``replace``.
        shortfall: ``route_machines`` minus ``built_capacity``, on ``more`` alone, so above zero.
        unknown_capacity: How many of those machines have an unknown capacity: an overclock
            that was never read, or a production boost tagged.
    """

    recipe: str
    reading: str
    route_machines: Fraction | None
    built_machines: int
    built_capacity: Fraction | None
    shortfall: Fraction | None
    unknown_capacity: int


@dataclass(frozen=True, slots=True)
class RedesignBuilt:
    """The marked route compared with what is built, dependency-ordered (CS-1375).

    Attributes:
        rows: The ``replace`` rows first, then one row per stage of the route with a nonzero
            machine count, producers first.
        measured: Whether any built machine names a recipe at all. False reads every stage
            ``unmeasured`` and offers no ``replace`` row.
        cycles: Each loop among the stages, its members in registry order. A stage in one is
            listed after every predecessor outside it.
        refused_recipe_tags: How many recipe tags the machines reader refused, counted.
        unregistered_machines: How many machines name a recipe the registry does not hold.
        untagged_machines: How many machines carry no recipe tag.
    """

    rows: tuple[BuiltRow, ...]
    measured: bool
    cycles: tuple[tuple[str, ...], ...]
    refused_recipe_tags: int
    unregistered_machines: int
    untagged_machines: int


@dataclass(frozen=True)
class PlanOutcome:
    """What one stated request came to, as a surface may transcribe it (CS-1371).

    A refused trace yields no card, so this is the only word a reader gets when nothing
    fired. Built from the offer alone by :func:`plan_outcome_of`. Every field is the
    closed vocabulary's or the registry's, never a string read out of a save.

    Attributes:
        status: The ``plan.status`` word.
        reason: Why that status offers no plan, or None on ``ranked``. Where status is
            ``schematic-unplannable`` it is the statement's reason word (CS-1373) and nothing
            else, except on ``item-not-plannable``, where it is that word, a colon and a space,
            then each cost item off ``plan_targets`` by ClassName, sorted and comma-separated:
            a cost item is named and never dropped from the request to make it plannable.
        redesign: The ``plan.redesign.status`` word.
        redesign_reason: Why that word offers no route, on ``no-route`` and ``route-refused``
            alone, and None on every other status (CS-1380). The sentence the trace records,
            which says neither word proves no plan exists.
        trimmed: What the bound dropped, by ClassName, or None when this offer carries no
            such word because no search ran. Empty says the bound dropped nothing.
        unmade: What the target's closure reached that no recipe in it makes and the raw
            items lack, on ``no-route`` alone, and None on every other status. Empty on
            ``no-route`` where the gap is a loop no raw item enters.
        raw_unknown: The declared raw items no extractor joins, which neither the search
            nor the route may start from, by ClassName, or None when this offer carries no
            such word because no join ran (CS-1382). Empty says every one joined.
    """

    status: str
    reason: str | None
    redesign: str
    redesign_reason: str | None
    trimmed: tuple[str, ...] | None
    unmade: tuple[str, ...] | None
    raw_unknown: tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class SchematicStatement:
    """The schematic a plan was stated for, as a rule may read it (CS-1373).

    Slotted, so the engine admits it, and every part an exact value. Built by
    ``clockspeed/advisor/plans.py`` from one ``milestone_requirement``; this module reads it
    and computes none of it.

    Attributes:
        schematic: The schematic's ClassName, which is the card's target milestone.
        tech_tier: The tier the catalog read, or None when it read none.
        cost: Item ClassName to its total amount as written, or None when the requirement
            publishes none.
        budget_minutes: The completion budget the rates were derived over.
        rates: Item ClassName to the rate a minute the requirement published, or None when it
            published none. The plan's targets, exactly, on a plannable statement.
        unplannable: None on a plannable statement, else one of :data:`UNPLANNABLE_REASONS`.
        unplannable_items: The items named by ``item-not-plannable``, sorted, else empty.
    """

    schematic: str
    tech_tier: int | None
    cost: MappingProxyType[str, Fraction] | None
    budget_minutes: Fraction
    rates: MappingProxyType[str, Fraction] | None
    unplannable: str | None
    unplannable_items: tuple[str, ...]


def schematic_inputs(statement: SchematicStatement | None) -> dict[str, InputValue]:
    """Offer the stated schematic, or None where none was stated.

    Args:
        statement: What the caller stated, or None.

    Returns:
        A fresh dict holding :data:`IN_SCHEMATIC`.
    """
    return {IN_SCHEMATIC: InputValue(statement, _OFFER_SOURCE_PREFIX + "schematic")}


def _status_input(status: str) -> dict[str, InputValue]:
    """Offer the one status word.

    Args:
        status: One word of the closed vocabulary.

    Returns:
        A fresh dict holding that word.
    """
    return {IN_STATUS: InputValue(status, _OFFER_SOURCE_PREFIX + "status")}


def redesign_status_inputs(status: str, *, unmade: tuple[str, ...] | None) -> dict[str, InputValue]:
    """Offer a marked-route status that carries no route.

    Args:
        status: One word of the marked route's closed vocabulary, never routed.
        unmade: What the closure reached that nothing makes, on no-route. REQUIRED, with
            no default: None says this status has no such word, and an empty tuple says
            the closure found no such item, which is a different claim.

    Returns:
        A fresh dict of every input of :data:`REDESIGN_INPUTS`. What was never solved
        reads None, because empty would read as a route with nothing locked on it, and so
        do the target names, which name a plan's targets, and here there is no plan.
    """
    return {
        IN_REDESIGN_STATUS: InputValue(status, _REDESIGN_SOURCE_PREFIX + "status"),
        IN_REDESIGN_PLAN: InputValue(None, _ROUTE_PLAN_SOURCE),
        IN_REDESIGN_HELD: InputValue(None, _REDESIGN_SOURCE_PREFIX + "held"),
        IN_REDESIGN_LOCKED: InputValue(None, _REDESIGN_SOURCE_PREFIX + "locked"),
        IN_REDESIGN_LOCKED_EXTRACTORS: InputValue(
            None, _REDESIGN_SOURCE_PREFIX + "locked_extractors"
        ),
        IN_REDESIGN_REQUIRES: InputValue(None, _ROUTE_REQUIRES_SOURCE),
        IN_REDESIGN_UNMADE: InputValue(unmade, _ROUTE_UNMADE_SOURCE),
        IN_REDESIGN_TARGET_NAMES: InputValue(None, _TARGET_NAME_SOURCE),
        IN_REDESIGN_UNLOCKS: InputValue(None, _ROUTE_UNLOCKS_SOURCE),
        IN_REDESIGN_BUILT: InputValue(None, _ROUTE_BUILT_SOURCE),
    }


def redesign_inputs(
    plan: ProductionPlan,
    *,
    held: tuple[str, ...],
    locked: tuple[str, ...],
    locked_extractors: tuple[str, ...],
    requires: tuple[str, ...],
    target_names: MappingProxyType[str, str | None],
    unlocks: RedesignUnlocks | None = None,
    built: RedesignBuilt | None = None,
) -> dict[str, InputValue]:
    """Offer one solved route as rule inputs, each sourced to where it came from.

    Args:
        plan: The plan pillar 1 solved for the route.
        held: The route's recipes the solve gives a machine count and the world holds,
            with a machine to run them, by ClassName. REQUIRED, with no default: empty
            says none is held.
        locked: The route's recipes the solve gives a machine count and the world does
            not hold, a recipe with no machine held among them, by ClassName. REQUIRED,
            with no default: empty says none is locked.
        locked_extractors: For each raw item the route consumes and no held machine extracts,
            the machine that must unlock first, by ClassName, each once. REQUIRED, with no
            default: empty says the world extracts everything this route consumes, which is
            half of what lets its reason say it needs no unlock.
        requires: The unlock keys of ``held``, of the machine each one runs on and of a held
            machine for each raw item the route consumes where it holds one. REQUIRED, for the
            reason :func:`plan_inputs` gives: an invented empty tuple would advise recipes
            nobody checked. A locked stage and a locked extractor never reach it.
        target_names: Each of the plan's targets by ClassName, to its display name or None.
            REQUIRED, for the reason :func:`plan_inputs` gives.
        unlocks: What unlocks each locked stage, or None where no schematic catalog was read,
            which says nothing about any stage and is not an empty list.
        built: The route compared with what is built, or None where no machines model was
            handed to the offer, which says nothing about any stage (CS-1375).

    Returns:
        A fresh dict of every input of :data:`REDESIGN_INPUTS`.
    """
    return {
        **redesign_status_inputs(REDESIGN_ROUTED, unmade=None),
        IN_REDESIGN_PLAN: InputValue(plan, _ROUTE_PLAN_SOURCE),
        IN_REDESIGN_HELD: InputValue(held, _REDESIGN_SOURCE_PREFIX + "held"),
        IN_REDESIGN_LOCKED: InputValue(locked, _REDESIGN_SOURCE_PREFIX + "locked"),
        IN_REDESIGN_LOCKED_EXTRACTORS: InputValue(
            locked_extractors, _REDESIGN_SOURCE_PREFIX + "locked_extractors"
        ),
        IN_REDESIGN_REQUIRES: InputValue(requires, _ROUTE_REQUIRES_SOURCE),
        IN_REDESIGN_TARGET_NAMES: InputValue(target_names, _TARGET_NAME_SOURCE),
        IN_REDESIGN_UNLOCKS: InputValue(unlocks, _ROUTE_UNLOCKS_SOURCE),
        IN_REDESIGN_BUILT: InputValue(built, _ROUTE_BUILT_SOURCE),
    }


def status_inputs(status: str) -> dict[str, InputValue]:
    """Offer a status reached before any join ran: no search, so no route either.

    Args:
        status: One word of the closed vocabulary.

    Returns:
        A fresh dict holding the status, and the marked route's inputs reading
        :data:`REDESIGN_NOT_REACHED`, so a world with no target still offers them.
    """
    return {
        **_status_input(status),
        **redesign_status_inputs(REDESIGN_NOT_REACHED, unmade=None),
        **schematic_inputs(None),
    }


def refused_inputs(
    status: str,
    *,
    trimmed: tuple[str, ...],
    unchecked: tuple[str, ...],
    raw_unknown: tuple[str, ...],
    unmatched_unlocks: int,
) -> dict[str, InputValue]:
    """Offer a status a search reached without a plan, and what the search left out.

    A no-plan speaks only for what the search kept, and the one route may be among
    what the join or the bound left out, so the trace says what was left out on this
    path as well.

    Args:
        status: One word of the closed vocabulary.
        trimmed: The recipes the bound dropped, by ClassName in registry order.
            REQUIRED, with no default: empty says the cap dropped nothing.
        unchecked: The automated recipes the join could not check, carrying no asset path
            or no machine joining a build recipe with one, by ClassName.
        raw_unknown: The declared raw items no extractor joining a build recipe with a path
            extracts, by ClassName. REQUIRED, with no default: empty says every one joined.
        unmatched_unlocks: How many of the world's unlocked paths joined no recipe.
            A count, because each one is a string read out of a save.

    Returns:
        A fresh dict, so a caller may add inputs from another layer. The caller adds the
        marked route's: the search ran, so only the caller knows what it read.
    """
    return {
        **_status_input(status),
        IN_UNCHECKED: InputValue(unchecked, _OFFER_SOURCE_PREFIX + "unchecked"),
        IN_RAW_UNKNOWN: InputValue(raw_unknown, _OFFER_SOURCE_PREFIX + "raw_unknown"),
        IN_UNMATCHED: InputValue(unmatched_unlocks, _OFFER_SOURCE_PREFIX + "unmatched_unlocks"),
        IN_TRIMMED: InputValue(trimmed, _TRIMMED_SOURCE),
        **schematic_inputs(None),
    }


def plan_inputs(
    ranked: RankedPlan,
    *,
    requires: tuple[str, ...],
    trimmed: tuple[str, ...],
    unchecked: tuple[str, ...],
    raw_unknown: tuple[str, ...],
    unmatched_unlocks: int,
    backend: str,
    target_names: MappingProxyType[str, str | None],
) -> dict[str, InputValue]:
    """Offer one ranked plan as rule inputs, each sourced to the field it came from.

    Args:
        ranked: One entry of a :func:`~clockspeed.solve.strategy.rank_plans`
            result. Its plan and its badge are offered together.
        requires: The unlock keys the plan's recipes, their machines and its raw items'
            extractors need, in the form
            :func:`clockspeed.advisor.trace.unlock_keys` builds. REQUIRED, with no
            default: ``clockspeed/advisor/plans.py`` holds the join from a recipe
            ClassName to its asset path, and inventing an empty tuple here would
            advise a plan over recipes nobody checked.
        trimmed: The recipes the bound dropped to reach the plan, by ClassName.
        unchecked: The automated recipes the join could not check, carrying no asset path
            or no machine joining a build recipe with one, by ClassName.
        raw_unknown: As :func:`refused_inputs` takes it.
        unmatched_unlocks: How many of the world's unlocked paths joined no recipe.
            A count, because each one is a string read out of a save.
        backend: The name of the backend that ran the search, as the result
            carries it. REQUIRED, with no default: a derivation differs by backend,
            so one that names none cannot be reproduced from what it shows.
        target_names: Each of the plan's targets by ClassName, to its display name or None.
            REQUIRED, with no default: a rule reads no registry, so a default here would say
            no target has a name when nobody looked.

    Returns:
        A fresh dict, so a caller may add inputs from another layer.
    """
    return {
        **refused_inputs(
            STATUS_RANKED,
            trimmed=trimmed,
            unchecked=unchecked,
            raw_unknown=raw_unknown,
            unmatched_unlocks=unmatched_unlocks,
        ),
        IN_PLAN: InputValue(ranked.plan, _SOURCE_PREFIX + "plan"),
        IN_BADGE: InputValue(ranked.badge, _SOURCE_PREFIX + "badge"),
        IN_REQUIRES: InputValue(requires, _REQUIRES_SOURCE),
        IN_BACKEND: InputValue(backend, _BACKEND_SOURCE),
        IN_TARGET_NAMES: InputValue(target_names, _TARGET_NAME_SOURCE),
    }


def _check_badge(badge: StrategyBadge) -> None:
    """Refuse a badge whose summary disagrees with its own checks.

    Raises:
        ValueError: The checks do not name every ladder rung in ladder order,
            ``cleared`` is not exactly the cleared checks' names in order, or
            ``strongest`` is not the last of them (None when none cleared).
    """
    if tuple(check.strategy for check in badge.checks) != _LADDER_NAMES:
        raise ValueError("a badge's checks do not follow the strategy ladder")
    cleared = tuple(check.strategy for check in badge.checks if check.cleared is True)
    if badge.cleared != cleared:
        raise ValueError("a badge's cleared rungs disagree with its checks")
    if badge.strongest != (cleared[-1] if cleared else None):
        raise ValueError("a badge's strongest rung is not the last one it cleared")


def _names(value: object, what: str) -> tuple[str, ...]:
    """Refuse a value that is not exactly a tuple of str.

    Args:
        value: The value read.
        what: The fixed name the refusal uses, never a value.

    Returns:
        The tuple.

    Raises:
        TypeError: It is anything else.
    """
    if type(value) is not tuple or not all(type(key) is str for key in value):
        raise TypeError(what + " are not a tuple of str")
    return value


def _checked_target_names(value: object, targets: tuple[str, ...]) -> Mapping[str, str | None]:
    """Refuse names that are not exactly one str or None for each of a plan's targets.

    Args:
        value: The value read.
        targets: The plan's targets, sorted.

    Returns:
        The mapping.

    Raises:
        TypeError: It is not a read-only mapping, or a name in it is neither a str nor None.
        ValueError: Its keys are not exactly the plan's targets, so a name is missing or is
            some other item's.
    """
    if type(value) is not MappingProxyType:
        raise TypeError("a plan's target names are not a read-only mapping")
    if tuple(sorted(value)) != targets:
        raise ValueError("a plan's target names disagree with its targets")
    if not all(name is None or type(name) is str for name in value.values()):
        raise TypeError("a plan's target name is neither a str nor None")
    return value


def _target_labels(
    ctx: RuleContext, names: Mapping[str, str | None], targets: tuple[str, ...]
) -> tuple[str, ...]:
    """Say what tiers 1 and 2 call each target: its display name quoted, or else its ClassName.

    A name must pass the engine's own test of a card's text, printable ASCII with a visible
    character, because :func:`clockspeed.advisor.trace.run_rule` would otherwise drop the
    whole card as a rule error, be whitespace-normal, because a card's tiers collapse every
    whitespace run and would say a name the registry does not hold, and stay short, because a
    mod's name would otherwise read as the whole headline. A usable name is quoted and
    escaped, so a tier's own separators in it
    read as part of one name, never as a clause or a second target; a ClassName stays bare,
    so a quoted label always says a display name. Any fallback records one indeterminate step.

    Args:
        ctx: The rule's context. Called on the firing path alone, because a step recorded
            beside a rejection would unsettle it.
        names: The checked names.
        targets: The plan's targets, sorted.

    Returns:
        One label per target, in the order of ``targets``, whatever the names sort as.
    """
    labels: list[str] = []
    fell_back = False
    for key in targets:
        name = names[key]
        if usable_name(name):
            labels.append(quoted(name))
        else:
            labels.append(key)
            fell_back = True
    if fell_back:
        ctx.indeterminate(_NAME_ALTERNATIVE, _NAME_REASON)
    return tuple(labels)


def _read_statement(ctx: RuleContext) -> SchematicStatement | None:
    """Read the stated schematic, which must be None or exactly a statement.

    Args:
        ctx: The rule's context. Reads :data:`IN_SCHEMATIC` once.

    Returns:
        The statement, or None when none was stated.

    Raises:
        TypeError: The input is neither None nor a :class:`SchematicStatement`.
    """
    statement = ctx.read(IN_SCHEMATIC)
    if statement is not None and type(statement) is not SchematicStatement:
        raise TypeError("a plan's schematic is not a SchematicStatement")
    return statement


def _milestone_of(statement: SchematicStatement | None, plan: ProductionPlan) -> str | None:
    """Say which milestone a card serves, after checking the statement against its plan.

    Args:
        statement: What :func:`_read_statement` read.
        plan: The plan the card is for.

    Returns:
        The schematic's ClassName, or None when none was stated.

    Raises:
        TypeError: The schematic's name is not a str.
        ValueError: The statement is unplannable, or its rates are not exactly the plan's
            targets, so the card would name a schematic it was not planned for.
    """
    if statement is None:
        return None
    if statement.unplannable is not None or statement.rates is None:
        raise ValueError("an unplannable schematic reached a plan")
    if type(statement.schematic) is not str:
        raise TypeError("a plan's schematic name is not a str")
    if dict(statement.rates) != dict(plan.targets):
        raise ValueError("a schematic's rates disagree with the plan's targets")
    return statement.schematic


def _evaluate_adopt(ctx: RuleContext) -> Recommendation | None:
    caveat = build_caveat(ctx)
    status = ctx.read(IN_STATUS)
    if type(status) is not str:
        raise TypeError("a plan status is not a str")
    if status != STATUS_RANKED and status not in _STATUS_REASONS:
        raise ValueError("a plan status is outside the closed vocabulary")
    unchecked: tuple[str, ...] = ()
    raw_unknown: tuple[str, ...] = ()
    trimmed: tuple[str, ...] = ()
    if status not in _UNJOINED_STATUSES:
        unchecked = _names(ctx.read(IN_UNCHECKED), "a plan's unchecked recipes")
        raw_unknown = _names(ctx.read(IN_RAW_UNKNOWN), "a plan's raw items with no extractor")
        if type(ctx.read(IN_UNMATCHED)) is not int:
            raise TypeError("a plan's unmatched unlock count is not an int")
        trimmed = _names(ctx.read(IN_TRIMMED), "a plan's trimmed recipes")
    if status != STATUS_RANKED:
        ctx.indeterminate(_ADOPT_ALTERNATIVE, _STATUS_REASONS[status])
        return None
    statement = _read_statement(ctx)
    plan = ctx.read(IN_PLAN)
    if type(plan) is not ProductionPlan:
        raise TypeError("a plan input is not a ProductionPlan")
    badge = ctx.read(IN_BADGE)
    if type(badge) is not StrategyBadge:
        raise TypeError("a badge input is not a StrategyBadge")
    _check_badge(badge)
    requires = _names(ctx.read(IN_REQUIRES), "a plan's unlock keys")
    if ctx.read(IN_BACKEND) not in available_backends():
        raise ValueError("a plan's backend is outside the closed vocabulary")
    targets = tuple(sorted(plan.targets))
    if not targets:
        raise ValueError("a plan names no target")
    names = _checked_target_names(ctx.read(IN_TARGET_NAMES), targets)
    milestone = _milestone_of(statement, plan)
    machines = ctx.compute(
        LABEL_MACHINES, sum((step.machines for step in plan.steps), start=Fraction(0))
    )
    if badge.strongest is None:
        ctx.reject(_ADOPT_ALTERNATIVE, "the plan cleared no strategy rung against its reference")
        return None
    ctx.indeterminate(_COMPARE_ALTERNATIVE, _COMPARE_REASON)
    labels = _target_labels(ctx, names, targets)
    rates = ", ".join(
        f"{render_value(plan.targets[item])} per minute of {label}"
        for item, label in zip(targets, labels, strict=True)
    )
    # Counts only: tier 3 names them. The caveat stays last, whatever precedes it.
    trim = f"; the search dropped {len(trimmed)} recipe(s) to fit its cap" if trimmed else ""
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Build the planned production chain for " + ", ".join(labels),
        reason=(
            f"It makes {rates} with {render_value(machines)} machine equivalents"
            f"{trim}{_unchecked_clause(unchecked)}{_raw_unknown_clause(raw_unknown)}{caveat}"
        ),
        target_milestone=milestone,
        requires=requires,
    )


def _check_no_route_offered(status: str, *, offered: tuple[object, ...], unmade: object) -> None:
    """Refuse a status with no route that nonetheless carries one.

    Args:
        status: The marked route's status, never routed.
        offered: The plan, held, locked, locked extractors, requires and target names values
            read.
        unmade: The unmade value read.

    Raises:
        TypeError: Anything was offered beside it but what that status says, which is
            nothing, and on no-route the items.
    """
    if any(value is not None for value in offered):
        raise TypeError("a plan.redesign status with no route carries a route")
    if status == REDESIGN_NO_ROUTE:
        _names(unmade, "a route's unmade items")
    elif unmade is not None:
        raise TypeError("a plan.redesign status other than no-route names unmade items")


def _check_stages(plan: ProductionPlan, held: tuple[str, ...], locked: tuple[str, ...]) -> None:
    """Refuse lists that are not exactly the plan's stages with a machine, each once.

    Args:
        plan: The route's plan.
        held: The stages offered as held.
        locked: The stages offered as locked.

    Raises:
        ValueError: A machine count is negative, or the two lists disagree with the plan.
            A count of stages that are not the plan's is a forged claim.
    """
    if any(step.machines < 0 for step in plan.steps):
        raise ValueError("a route's plan runs a recipe backwards")
    stages = sorted(step.recipe_key for step in plan.steps if step.machines != 0)
    if sorted((*held, *locked)) != stages:
        raise ValueError("a route's held and locked recipes disagree with its plan")


def _check_unlocks(value: object, locked: tuple[str, ...]) -> RedesignUnlocks | None:
    """Refuse an unlock reading that is not exactly one honest entry per locked stage.

    A short list passing for the whole is the failure this exists to refuse (non-negotiable 7):
    an entry missing for a locked stage, or one for a stage the route does not lock, is a
    forged claim.

    Args:
        value: What :data:`IN_REDESIGN_UNLOCKS` read.
        locked: The route's locked stages.

    Returns:
        The reading, or None where no catalog was read.

    Raises:
        TypeError: A part is not exactly the type this module declares, or a name is not a str.
        ValueError: The entries are not exactly the locked stages, each once and in the
            locked list's own order, a word is outside
            :data:`UNLOCK_READINGS`, an entry's schematics disagree with its word, or the
            unmatched count is negative.
    """
    if value is None:
        return None
    if type(value) is not RedesignUnlocks:
        raise TypeError("a route's unlocks are not a RedesignUnlocks")
    entries = value.locked
    if type(entries) is not tuple or not all(type(entry) is LockedUnlock for entry in entries):
        raise TypeError("a route's unlock entries are not a tuple of LockedUnlock")
    if type(value.unmatched) is not int or value.unmatched < 0:
        raise ValueError("a route's unmatched unlock count is not a whole number")
    if tuple(entry.recipe for entry in entries) != locked:
        raise ValueError("a route's unlock entries disagree with its locked recipes")
    for entry in entries:
        if type(entry.reading) is not str or entry.reading not in UNLOCK_READINGS:
            raise ValueError("a route's unlock reading is outside the closed vocabulary")
        if entry.machine is not None and type(entry.machine) is not str:
            raise TypeError("a route's unlock machine is not a str")
        if type(entry.schematics) is not tuple or not all(
            type(named) is UnlockingSchematic
            and type(named.schematic) is str
            and (named.tech_tier is None or type(named.tech_tier) is int)
            for named in entry.schematics
        ):
            raise TypeError("a route's unlocking schematics are not a tuple of UnlockingSchematic")
        if bool(entry.schematics) != (entry.reading == UNLOCK_NAMED):
            raise ValueError("a route's unlock reading disagrees with its schematics")
    return value


#: The fewest stages a loop can have: one stage feeding itself is no loop (CS-1375).
_MIN_LOOP: Final = 2


def _is_count(value: object) -> bool:
    """Whether a value is exactly an int that is not negative."""
    return type(value) is int and value >= 0


def _check_built_figures(row: BuiltRow) -> None:
    """Refuse a comparison row whose parts are not the types this module declares.

    Args:
        row: A row, already known to be a BuiltRow.

    Raises:
        TypeError: A name is not a str, a count is not a whole number or a figure is not an
            exact Fraction.
        ValueError: The reading is outside the closed vocabulary, or more machines have an
            unknown capacity than were built.
    """
    if type(row.recipe) is not str or type(row.reading) is not str:
        raise TypeError("a route's built row names a recipe or reading that is not a str")
    if row.reading not in BUILT_READINGS:
        raise ValueError("a route's built reading is outside the closed vocabulary")
    if not _is_count(row.built_machines) or not _is_count(row.unknown_capacity):
        raise TypeError("a route's built row counts machines that are not whole numbers")
    if row.unknown_capacity > row.built_machines:
        raise ValueError("a route's built row has more unknown machines than machines")
    for figure in (row.route_machines, row.built_capacity, row.shortfall):
        if figure is not None and type(figure) is not Fraction:
            raise TypeError("a route's built figure is not an exact Fraction")


def _check_stage_row(row: BuiltRow, count: Fraction, *, measured: bool) -> None:
    """Refuse a stage's row whose reading disagrees with its own figures (CS-1375).

    Args:
        row: A row for a stage of the route, whose parts have the declared types.
        count: The route's machine count for that stage.
        measured: Whether the comparison says some machine names a recipe.

    Raises:
        ValueError: The reading and the figures disagree: an unmeasured row that carries a
            figure, a measured row that carries none, or a shortfall that is not exactly the
            route's count minus the built capacity.
    """
    capacity = row.built_capacity
    if row.reading == BUILT_UNMEASURED:
        if capacity is not None or row.shortfall is not None:
            raise ValueError("a route's unmeasured row carries a figure")
        if (row.unknown_capacity == 0) != (not measured):
            raise ValueError("a route's unmeasured row disagrees with its comparison")
        return
    if capacity is None or row.unknown_capacity != 0 or not measured:
        raise ValueError("a route's measured row carries no capacity")
    gap = count - capacity
    more = row.reading == BUILT_MORE
    if more != (gap > 0) or row.shortfall != (gap if more else None):
        raise ValueError("a route's built row disagrees with its own figures")


def _check_built_row(row: object, counts: Mapping[str, Fraction], *, measured: bool) -> BuiltRow:
    """Refuse one comparison row that is not honest, and return it as a row.

    Args:
        row: One member of the comparison's rows.
        counts: The route's stages with a machine count, by ClassName.
        measured: Whether the comparison says some machine names a recipe.

    Returns:
        The row.

    Raises:
        TypeError: A part is not exactly the type this module declares.
        ValueError: The row disagrees with the plan, with its own reading, or with the
            comparison it sits in. A forged claim is refused (non-negotiable 7).
    """
    if type(row) is not BuiltRow:
        raise TypeError("a route's built rows are not BuiltRow entries")
    _check_built_figures(row)
    if row.reading == BUILT_REPLACE:
        if (
            row.recipe in counts
            or row.route_machines is not None
            or row.built_capacity is not None
            or row.shortfall is not None
            or row.built_machines == 0
        ):
            raise ValueError("a route's replace row is not an off-route recipe with machines")
        return row
    if row.recipe not in counts or row.route_machines != counts[row.recipe]:
        raise ValueError("a route's built row disagrees with its plan")
    _check_stage_row(row, counts[row.recipe], measured=measured)
    return row


def _check_built(value: object, plan: ProductionPlan) -> RedesignBuilt | None:
    """Refuse a comparison that is not exactly one honest row per stage of its plan (CS-1375).

    Args:
        value: What :data:`IN_REDESIGN_BUILT` read.
        plan: The route's plan, whose stages with a machine count the rows must be.

    Returns:
        The comparison, or None where no machines model was handed to the offer.

    Raises:
        TypeError: A part is not exactly the type this module declares.
        ValueError: A row is missing or invented, a reading disagrees with its figures, a
            replace row follows another kind, or a loop names a recipe that is no stage.
    """
    if value is None:
        return None
    if type(value) is not RedesignBuilt:
        raise TypeError("a route's built comparison is not a RedesignBuilt")
    if type(value.rows) is not tuple or type(value.cycles) is not tuple:
        raise TypeError("a route's built rows and cycles are not tuples")
    if type(value.measured) is not bool:
        raise TypeError("a route's built comparison says neither measured nor not")
    if not all(
        _is_count(count)
        for count in (
            value.refused_recipe_tags,
            value.unregistered_machines,
            value.untagged_machines,
        )
    ):
        raise TypeError("a route's built counts are not whole numbers")
    counts = {step.recipe_key: step.machines for step in plan.steps if step.machines != 0}
    rows = tuple(_check_built_row(row, counts, measured=value.measured) for row in value.rows)
    replaced = [row for row in rows if row.reading == BUILT_REPLACE]
    staged = [row for row in rows if row.reading != BUILT_REPLACE]
    if rows != (*replaced, *staged):
        raise ValueError("a route's replace rows do not come first")
    if not value.measured and replaced:
        raise ValueError("a route's comparison reads replace with nothing measured")
    if sorted(row.recipe for row in staged) != sorted(counts):
        raise ValueError("a route's built rows disagree with its stages")
    if len({row.recipe for row in rows}) != len(rows):
        raise ValueError("a route's built rows name a recipe twice")
    for loop in value.cycles:
        if (
            type(loop) is not tuple
            or len(loop) < _MIN_LOOP
            or not all(name in counts for name in loop)
        ):
            raise ValueError("a route's built loops disagree with its stages")
    return value


def _built_counts(built: RedesignBuilt) -> tuple[int, int, int]:
    """Count the rows of a checked comparison that read more, replace and unmeasured.

    Args:
        built: A comparison :func:`_check_built` returned.

    Returns:
        How many stages read more, how many recipes read replace and how many stages read
        unmeasured.
    """
    more = sum(1 for row in built.rows if row.reading == BUILT_MORE)
    replaced = sum(1 for row in built.rows if row.reading == BUILT_REPLACE)
    return more, replaced, sum(1 for row in built.rows if row.reading == BUILT_UNMEASURED)


def _built_clause(built: RedesignBuilt | None) -> str:
    """Say what the route's reading of what is built came to, from the checked comparison.

    Args:
        built: The checked comparison, or None where none was offered.

    Returns:
        Where no machines model was handed over, the clause that says the route was never
        compared. Wherever one was, that the direction did not choose the route, that the
        comparison read unmeasured where no machine names a recipe, how many stages read more,
        how many recipes read replace and how many stages read unmeasured, and that a replace
        is the expensive change where one reads. Counts only: tier 3 names the recipes.
    """
    if built is None:
        return _NOT_CHOSEN_CLAUSE
    more, replaced, unmeasured = _built_counts(built)
    return (
        f"{_DIRECTION_ONLY_CLAUSE}{'' if built.measured else _UNMEASURED_CLAUSE}"
        f"; against what is built {more} stage(s) read more,"
        f" {replaced} recipe(s) read replace and {unmeasured} stage(s) read unmeasured"
        f"{_REPLACE_COSTS_CLAUSE if replaced else ''}"
    )


def _unchecked_clause(unchecked: tuple[str, ...]) -> str:
    """Say how many automated recipes no plan could be asked about, or nothing.

    Args:
        unchecked: The automated recipes the join could not check.

    Returns:
        A count and no name, because tier 3 names them, or the empty string.
    """
    if not unchecked:
        return ""
    return (
        f"; {len(unchecked)} automated recipe(s) carry no unlock path to check"
        " and were never planned"
    )


def _raw_unknown_clause(raw_unknown: tuple[str, ...]) -> str:
    """Say how many declared raw items no extractor joins, or nothing.

    KNOWN MEANS JOINED. The sentence's known extractor is one the docs name whose build recipe
    has a path an unlock key can carry, so an item whose every extractor's path is not
    printable ASCII counts here beside one the docs name no extractor for.

    Args:
        raw_unknown: The raw items, which neither a search nor a route may start from.

    Returns:
        A count and no name, because tier 3 names them, or the empty string.
    """
    if not raw_unknown:
        return ""
    return f"; {len(raw_unknown)} raw item(s) have no known extractor and were never supplied"


def _route_unlock_clause(
    ctx: RuleContext, locked: tuple[str, ...], locked_extractors: tuple[str, ...]
) -> str:
    """Say what a route needs unlocked first: its stages, its extractors, or nothing at all.

    Args:
        ctx: The rule's context. What the bound dropped is read here, on the one path a
            sentence rests on it, so the derivation shows the word the sentence says.
        locked: The route's locked stages.
        locked_extractors: The machines the route needs to extract a raw item.

    Returns:
        The clause. It says no unlock is needed only when both lists are empty. Beside that it
        states what the bound did and claims no cause (CS-1382): how many held recipes it
        dropped to fit its cap and that the search found no route within it, or that it
        dropped none. A dropped recipe the route never runs can still be the one a plan
        needed, and the search can still find no plan over a route whose every stage the bound
        kept, so only a second search past the cap could tell, which is the cost the cap exists
        to bound.
    """
    clause = (_MUST_UNLOCK_CLAUSE if locked else "") + (
        _EXTRACTOR_UNLOCK_CLAUSE if locked_extractors else ""
    )
    if clause:
        return clause
    trimmed = _names(ctx.read(IN_TRIMMED), "a plan's trimmed recipes")
    if not trimmed:
        return _UNCAPPED_NO_UNLOCK_CLAUSE
    return (
        f"; this route needs no unlock and the search, which dropped {len(trimmed)} held"
        " recipe(s) to fit its cap, found no route within it from the raw items a held"
        " extractor supplies"
    )


def _evaluate_redesign(ctx: RuleContext) -> Recommendation | None:
    caveat = build_caveat(ctx)
    status = ctx.read(IN_REDESIGN_STATUS)
    if type(status) is not str:
        raise TypeError("a plan.redesign status is not a str")
    if status != REDESIGN_ROUTED and status not in _REDESIGN_REASONS:
        raise ValueError("a plan.redesign status is outside the closed vocabulary")
    plan = ctx.read(IN_REDESIGN_PLAN)
    held = ctx.read(IN_REDESIGN_HELD)
    locked = ctx.read(IN_REDESIGN_LOCKED)
    extractors = ctx.read(IN_REDESIGN_LOCKED_EXTRACTORS)
    requires = ctx.read(IN_REDESIGN_REQUIRES)
    unmade = ctx.read(IN_REDESIGN_UNMADE)
    names = ctx.read(IN_REDESIGN_TARGET_NAMES)
    unlocks = ctx.read(IN_REDESIGN_UNLOCKS)
    built = ctx.read(IN_REDESIGN_BUILT)
    if (ctx.read(IN_STATUS) == STATUS_NO_PLAN) == (status == REDESIGN_NOT_REACHED):
        raise ValueError("a plan.redesign status disagrees with the plan status")
    if status != REDESIGN_ROUTED:
        _check_no_route_offered(
            status,
            offered=(plan, held, locked, extractors, requires, names, unlocks, built),
            unmade=unmade,
        )
        ctx.indeterminate(_REDESIGN_ALTERNATIVE, _REDESIGN_REASONS[status])
        return None
    if type(plan) is not ProductionPlan:
        raise TypeError("a route's plan is not a ProductionPlan")
    held = _names(held, "a route's held recipes")
    locked = _names(locked, "a route's locked recipes")
    extractors = _names(extractors, "a route's locked extractors")
    requires = _names(requires, "a route's unlock keys")
    _check_unlocks(unlocks, locked)
    compared = _check_built(built, plan)
    if unmade is not None:
        raise TypeError("a routed offer names unmade items")
    unchecked = _names(ctx.read(IN_UNCHECKED), "a plan's unchecked recipes")
    raw_unknown = _names(ctx.read(IN_RAW_UNKNOWN), "a plan's raw items with no extractor")
    statement = _read_statement(ctx)
    targets = tuple(sorted(plan.targets))
    if not targets:
        raise ValueError("a route's plan names no target")
    target_names = _checked_target_names(names, targets)
    milestone = _milestone_of(statement, plan)
    _check_stages(plan, held, locked)
    ctx.compute(LABEL_MACHINES, sum((step.machines for step in plan.steps), start=Fraction(0)))
    if not held and not locked:
        ctx.reject(_REDESIGN_ALTERNATIVE, _NO_MACHINE_REASON)
        return None
    if compared is not None:
        ctx.indeterminate(_BUILT_COMPARE_ALTERNATIVE, _BUILT_COMPARE_REASON)
    else:
        ctx.indeterminate(_ROUTE_COMPARE_ALTERNATIVE, _ROUTE_COMPARE_REASON)
    # The targets' labels and counts of stages and extractors, so no locked recipe or machine
    # reads as buildable: tier 3 names them under inputs of their own. The caveat stays last,
    # whatever precedes it.
    labels = ", ".join(_target_labels(ctx, target_names, targets))
    needs = f" and needs {len(extractors)} locked extractor(s)" if extractors else ""
    return Recommendation(
        subject_key=SUBJECT_PREFIX + "+".join(targets),
        action="Plan toward " + labels,
        reason=(
            f"This route to {labels} runs {len(locked)} locked and {len(held)} held recipe(s)"
            f"{needs}{_route_unlock_clause(ctx, locked, extractors)}{_built_clause(compared)}"
            f"{_unchecked_clause(unchecked)}{_raw_unknown_clause(raw_unknown)}{caveat}"
        ),
        target_milestone=milestone,
        requires=requires,
    )


def _outcome_reason(values: Mapping[str, InputValue], status: str) -> str | None:
    """The reason an outcome carries (CS-1373).

    Args:
        values: A world's inputs.
        status: The checked plan status.

    Returns:
        Where the schematic is unplannable, its reason word, with the items named after it on
        ``item-not-plannable``; otherwise the status's own sentence, or None on ranked.

    Raises:
        ValueError: The statement is missing, is not a statement, or carries a reason outside
            :data:`UNPLANNABLE_REASONS`. The message names no value.
    """
    if status == STATUS_RANKED:
        return None
    if status != STATUS_SCHEMATIC_UNPLANNABLE:
        return _STATUS_REASONS[status]
    statement = values[IN_SCHEMATIC].value
    if (
        type(statement) is not SchematicStatement
        or statement.unplannable not in UNPLANNABLE_REASONS
    ):
        raise ValueError("an unplannable schematic carries no reason word")
    if statement.unplannable != REASON_ITEM_NOT_PLANNABLE:
        return statement.unplannable
    items = _names(statement.unplannable_items, "a schematic's items")
    return statement.unplannable + ": " + ", ".join(items)


def plan_outcome_of(values: Mapping[str, InputValue]) -> PlanOutcome:
    """Project one offer's inputs into what a surface may transcribe (CS-1371).

    Args:
        values: A world's inputs, as :func:`clockspeed.advisor.plans.plan_offer` offers
            them. Read by name; nothing else in them is touched.

    Returns:
        The outcome.

    Raises:
        ValueError: Either status is outside its closed vocabulary. The message names no
            value.
    """
    status = values[IN_STATUS].value
    if type(status) is not str or (status != STATUS_RANKED and status not in _STATUS_REASONS):
        raise ValueError("a plan status is outside the closed vocabulary")
    redesign = values[IN_REDESIGN_STATUS].value
    if type(redesign) is not str or (
        redesign != REDESIGN_ROUTED and redesign not in _REDESIGN_REASONS
    ):
        raise ValueError("a plan.redesign status is outside the closed vocabulary")
    trimmed = values.get(IN_TRIMMED)
    raw_unknown = values.get(IN_RAW_UNKNOWN)
    unmade = values[IN_REDESIGN_UNMADE].value
    return PlanOutcome(
        status=status,
        reason=_outcome_reason(values, status),
        redesign=redesign,
        redesign_reason=(
            _REDESIGN_REASONS[redesign] if redesign in _EXPLAINED_REDESIGN_STATUSES else None
        ),
        trimmed=None if trimmed is None else _names(trimmed.value, "a plan's trimmed recipes"),
        unmade=None if unmade is None else _names(unmade, "a route's unmade items"),
        raw_unknown=(
            None
            if raw_unknown is None
            else _names(raw_unknown.value, "a plan's raw items with no extractor")
        ),
    )


ADOPT_RULE: Final = RuleSpec(
    rule_id="plan.adopt",
    domain=DOMAIN,
    inputs=(*BUILD_INPUTS, *PLAN_INPUTS),
    unlocks=(),
    evaluate=_evaluate_adopt,
)

REDESIGN_RULE: Final = RuleSpec(
    rule_id="plan.redesign",
    domain=DOMAIN,
    inputs=(
        *BUILD_INPUTS,
        *REDESIGN_INPUTS,
        IN_STATUS,
        IN_UNCHECKED,
        IN_RAW_UNKNOWN,
        IN_TRIMMED,
        IN_SCHEMATIC,
    ),
    unlocks=(),
    evaluate=_evaluate_redesign,
)

#: Every rule in this family, registered in ``_FAMILIES``.
RULES: Final = (ADOPT_RULE, REDESIGN_RULE)
