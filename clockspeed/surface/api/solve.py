"""``/api/solve`` and ``/api/optimize``: pillar 1 and pillar 2, serialized.

Owns (BOOTSTRAP.md section 7.1): the request grammar for the two backed solver
endpoints, the JSON spelling of a ``ProductionPlan`` and an ``OptimizeResult``,
and the transcription of a solver refusal into the frozen envelope.

EVERY RATE LEAVES AS ``{"num": n, "den": d}``, AND THAT IS NON-NEGOTIABLE 6 AT
THE SURFACE. C1's answer is 10/3 machines. As a bare JSON number a browser reads
that as an IEEE double and renders 3.3333333333333335 - a different number,
wearing a plausible face, arriving through the one layer that has no arithmetic
of its own to catch it with. A two-field object cannot be misread as a number by
accident, so the whole answer path stays exact right up to the client's parser.
The transcription runs through ``contract.rational``, which reads
``.numerator`` and ``.denominator`` and divides nothing: ``surface/`` never
computes, and a division here would manufacture the exact float this spelling
exists to prevent.

THE REQUEST GRAMMAR ADMITS NO FLOAT EITHER, WHICH IS THE SAME RULE POINTED
INBOUND. A rate is spelled as an integer, an exact decimal or ``num/den``, and
the text is handed to ``Fraction`` UNMODIFIED - never through ``float``. That is
the property ``clockspeed/solve/exact.py``'s ``to_exact`` exists to state:
``Fraction(0.1)`` returns 3602879701896397/36028797018963968, an exact reading
of the binary approximation and a wrong reading of the decimal, and exact-and-
wrong is invisible to every downstream exactness check. An exponent form is
refused outright rather than parsed, so the one shape whose value depends on a
floating-point reading never enters.

A SOLVER REFUSAL IS ROUTED BY ITS CLASS NAME AND ITS MESSAGE IS NEVER READ.
``contract.SOLVER_REFUSALS`` is keyed on ``type(exc).__name__``, and this module
looks up nothing else. That is two rules in one lookup. It is the anti-
computation rule, because the surface decides nothing about a refusal it did not
raise - it transcribes a verdict the solver already reached. And it is the anti-
echo rule: ``UnsolvableChain`` interpolates the unsatisfiable ITEM into its
message and ``PowerNotComparableError`` interpolates the unpriceable RECIPE KEY,
so a surface that matched on message text would have to hold that text, and one
that rendered it would publish registry content in a response body.

THE 501/503 SPLIT DOES NOT COLLAPSE HERE. ``build_registry`` needs a document
read from the game install, so on a machine with no game there is no registry.
That is a WRITTEN layer with an ABSENT input - 503 - and it is a different truth
with a different remedy from "this layer has not been built yet". Answering 501
would report pillar 1 as unwritten when it is written and merely un-fed, and
would send an operator to a roadmap item instead of to their game installation.

``/api/solve`` ANSWERS PILLAR 1 IN BOTH DIRECTIONS, THROUGH ONE TEMPLATE. The
solve layer publishes ``solve_for_targets`` - rates in, machine counts out - and
``solve_for_supply`` - a cap in, the rate it buys out - and both return the same
``ProductionPlan``, because the reverse direction re-solves FORWARDS at the rate
the cap sustains rather than scaling a unit plan. One answer shape means one
serializer, so the supply mode adds no field to the response and no second
opinion about what a plan looks like. ``mode`` selects the direction, defaults to
``targets`` so no caller written before this existed changed meaning, and cannot
answer the wrong question silently: the two required sets are disjoint in the
names that matter, so a supply request that omits ``mode`` is refused as an
unknown parameter rather than solved as a forward one.

WHY A MALFORMED REQUEST IS REFUSED BEFORE THE PROVIDER IS CONSULTED. A request
that does not satisfy the grammar fails identically on every machine, and saying
so does not depend on any machine state. Consulting the provider first would
make the answer to one bad request depend on whether a game happens to be
installed, which is the determinism property (CLAUDE.md section 1) given away
for nothing.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this module is clockspeed.solve, and that is the ONLY layer it names at
# runtime. It opens no file: not a save, not the raw docs, not the game
# install. The registry arrives from a provider the SERVER bound into the
# handler by closure, so this module never imports the server, never learns how
# a registry was obtained, and stays testable without an HTTPS listener.
#
# clockspeed.data.registry.Registry is named ONLY under TYPE_CHECKING, to
# parameterise contract.RegistryProvider at the use site the way that protocol's
# docstring directs. It is the type clockspeed.solve's own published signatures
# spell, so spelling it here is naming the neighbour's parameter rather than
# reaching past it - and a typing-only import costs no runtime reach at all.

from __future__ import annotations

import re
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.solve import optimize, ratio
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from clockspeed.data.registry import Registry

__all__ = [
    "ASSIGNMENT",
    "KEY_PATTERN",
    "METHOD_POST",
    "MODES",
    "MODE_SUPPLY",
    "MODE_TARGETS",
    "OPTIMIZE_ENDPOINT",
    "OPTIMIZE_OPTIONAL",
    "OPTIMIZE_REQUIRED",
    "PARAM_BACKEND",
    "PARAM_BYPRODUCT_POLICY",
    "PARAM_CANDIDATES",
    "PARAM_MODE",
    "PARAM_OBJECTIVE",
    "PARAM_RAW_ITEMS",
    "PARAM_RECIPES",
    "PARAM_SUPPLY",
    "PARAM_TARGETS",
    "PARAM_TARGET_ITEM",
    "PARAM_UNLOCKED",
    "RATIONAL_PATTERN",
    "SEPARATOR",
    "SOLVE_ENDPOINT",
    "SOLVE_OPTIONAL",
    "SOLVE_REQUIRED",
    "SOLVE_SUPPLY_REQUIRED",
    "optimize_handler",
    "routes",
    "solve_handler",
]


# ---------------------------------------------------------------------------
# The route templates and the request grammar
# ---------------------------------------------------------------------------

#: Pillar 1. Given target rates and a chosen recipe set, the machine counts.
SOLVE_ENDPOINT: Final = "/api/solve"

#: Pillar 2. Given candidates and an objective, which recipes and the plan.
OPTIMIZE_ENDPOINT: Final = "/api/optimize"

#: Both are POST. Neither mutates anything - this project never writes to a save
#: or a game install - but a request carries a target basket, a candidate set
#: and an objective, which is a body rather than something to spell in a URL a
#: browser will log, cache and put in a history file.
METHOD_POST: Final = "POST"

PARAM_TARGETS: Final = "targets"
PARAM_RECIPES: Final = "recipes"
PARAM_RAW_ITEMS: Final = "raw_items"
PARAM_BYPRODUCT_POLICY: Final = "byproduct_policy"
PARAM_CANDIDATES: Final = "candidates"
PARAM_UNLOCKED: Final = "unlocked"
PARAM_OBJECTIVE: Final = "objective"
PARAM_BACKEND: Final = "backend"
PARAM_MODE: Final = "mode"
PARAM_SUPPLY: Final = "supply"
PARAM_TARGET_ITEM: Final = "target_item"

#: Solve forwards: requested rates in, machine counts out.
#: ``clockspeed/solve/ratio.py::solve_for_targets``.
MODE_TARGETS: Final = "targets"

#: Solve backwards: a supply cap in, the rate it buys out.
#: ``clockspeed/solve/ratio.py::solve_for_supply``.
MODE_SUPPLY: Final = "supply"

#: The two directions the solve layer publishes, and a CLOSED vocabulary: a
#: value outside it is refused rather than resolved to the nearest one.
#:
#: EACH MODE IS NAMED FOR THE PARAMETER THAT DISTINGUISHES IT, which is not a
#: collision with :data:`PARAM_TARGETS` and :data:`PARAM_SUPPLY` but the point.
#: The two request grammars are disjoint in exactly one name apiece, so a reader
#: who knows which parameter they are holding knows which mode to state.
MODES: Final = (MODE_TARGETS, MODE_SUPPLY)

#: Exactly what ``/api/solve`` requires IN THE TARGETS MODE. ``byproduct_policy``
#: is here rather than defaulted because ``clockspeed/solve/ratio.py`` has no
#: default for it and this module must not invent one: the third reading of an
#: unconsumed byproduct - assume it vanishes - produces the same machine counts
#: as sinking it with the byproduct nowhere in the output, so a default would be
#: a silent policy choice wearing the caller's name.
SOLVE_REQUIRED: Final = frozenset(
    {PARAM_TARGETS, PARAM_RECIPES, PARAM_RAW_ITEMS, PARAM_BYPRODUCT_POLICY}
)

#: Exactly what ``/api/solve`` requires IN THE SUPPLY MODE. It differs from the
#: set above in two names and no more: a basket of target rates becomes a basket
#: of available supply plus the SINGLE item to make from it.
#:
#: ONE TARGET ITEM AND NOT A BASKET, because ``ratio.SupplyRequest`` takes one
#: and says why: maximizing a basket needs an objective to trade its members off
#: against, and choosing that objective is pillar 2's call rather than this
#: door's. Accepting a basket here would mean inventing one at the surface.
SOLVE_SUPPLY_REQUIRED: Final = frozenset(
    {PARAM_SUPPLY, PARAM_TARGET_ITEM, PARAM_RECIPES, PARAM_RAW_ITEMS, PARAM_BYPRODUCT_POLICY}
)

#: ``mode`` is the one name ``/api/solve`` accepts in either direction, and it is
#: OPTIONAL rather than required so that every caller written before the supply
#: mode existed still asks the question it asked. Anything else is REFUSED rather
#: than ignored, on the rule ``clockspeed/solve/optimize.py`` states for an
#: unknown objective weight: an ignored parameter is one the caller believes is
#: in force and is not.
#:
#: WHY A DEFAULT HERE IS NOT THE SIN ``byproduct_policy`` REFUSES TO COMMIT. That
#: one is a SOLVE-layer parameter with a published owner and no default, and
#: guessing it changes the ANSWER while the request still looks answered. This
#: one is a SURFACE-layer discriminator with no owner below - the solve layer
#: publishes two functions and no selector between them - and it cannot answer
#: the wrong question silently, because the two required sets above are disjoint
#: in the names that matter: a supply request that omits ``mode`` names ``supply``
#: and ``target_item``, which the targets set does not accept, so it is refused
#: as an unknown parameter rather than solved as something else.
SOLVE_OPTIONAL: Final = frozenset({PARAM_MODE})

OPTIMIZE_REQUIRED: Final = frozenset(
    {
        PARAM_TARGETS,
        PARAM_CANDIDATES,
        PARAM_UNLOCKED,
        PARAM_RAW_ITEMS,
        PARAM_BYPRODUCT_POLICY,
        PARAM_OBJECTIVE,
    }
)

#: ``backend`` is the one optional parameter anywhere in this module. Omitted, it
#: falls through the precedence ``select_backend`` publishes; stated and
#: unrecognized, it is refused there rather than replaced by the default, which
#: is that function's own decision and not this one's.
OPTIMIZE_OPTIONAL: Final = frozenset({PARAM_BACKEND})

#: What separates the members of a list-valued or mapping-valued parameter.
SEPARATOR: Final = ","

#: What separates a key from its value inside one member.
ASSIGNMENT: Final = "="

#: An item or recipe ClassName. Permissive enough for the namespaced identifiers
#: mod content uses (BOOTSTRAP.md section 11) and tight enough that neither
#: separator can hide inside a key. A key naming nothing in the registry is NOT
#: refused here - that is the solve layer's ValueError to raise, and pre-empting
#: it would mean this module holding an opinion about registry content.
KEY_PATTERN: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")

#: An exact rate: an integer, an exact decimal, or ``num/den``. THE EXPONENT FORM
#: IS ABSENT ON PURPOSE. ``1e3`` has no reading that does not pass through a
#: binary float, and admitting one shape whose value depends on that reading
#: would undo the whole exactness argument for the sake of a spelling nobody
#: needs. Applied with ``fullmatch``, so a trailing newline cannot smuggle
#: anything past it.
RATIONAL_PATTERN: Final = re.compile(r"-?\d+(?:\.\d+|/\d+)?")


class _ParameterError(Exception):
    """One request-shape refusal, carrying a REASON CODE and no caller text.

    A code rather than a message, and this is the anti-echo rule applied to this
    module's own internals: an exception that carried the offending value would
    put that value one ``str(exc)`` away from a response body, and on this
    machine a caller-supplied string can be a save path or an account directory.
    The rendered line comes out of ``contract.REASONS`` whole.

    Attributes:
        reason: A key of ``contract.REASONS`` whose status is
            ``contract.STATUS_ERROR``.
    """

    def __init__(self, reason: str) -> None:
        """Record the reason code.

        Args:
            reason: The closed-vocabulary reason code, authored in the contract
                module and never built from caller text.
        """
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# Parsing. Every refusal is a closed-vocabulary code and quotes nothing.
# ---------------------------------------------------------------------------


def _check_names(
    parameters: Mapping[str, str], required: frozenset[str], optional: frozenset[str]
) -> None:
    """Refuse a request whose parameter NAMES are not the ones this door takes.

    Args:
        parameters: The request parameters.
        required: Names that must all be present.
        optional: Names that may be present.

    Raises:
        _ParameterError: A required name is absent, or a name outside both sets
            is present.
    """
    offered = frozenset(parameters)
    if required - offered:
        raise _ParameterError(contract.REASON_MISSING_PARAMETER)
    if offered - required - optional:
        raise _ParameterError(contract.REASON_UNKNOWN_PARAMETER)


def _rate(text: str) -> Fraction:
    """Read one exact rate, never through a float.

    Args:
        text: The verbatim parameter text.

    Returns:
        The exact value. The string is handed to ``Fraction`` unmodified, which
        is what keeps ``0.1`` reading as 1/10 rather than as the binary
        approximation ``float("0.1")`` substitutes.

    Raises:
        _ParameterError: The text is not a shape :data:`RATIONAL_PATTERN`
            admits, or is a ratio with a zero denominator.
    """
    if RATIONAL_PATTERN.fullmatch(text) is None:
        raise _ParameterError(contract.REASON_INVALID_PARAMETER)
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise _ParameterError(contract.REASON_INVALID_PARAMETER) from exc


def _rates(text: str) -> dict[str, Fraction]:
    """Read a ``key=rate,key=rate`` parameter.

    Args:
        text: The verbatim parameter text.

    Returns:
        Key to exact rate.

    Raises:
        _ParameterError: The text is empty, a member states no key or no value,
            a key is malformed, a key repeats, or a rate is unreadable. A repeat
            is refused rather than resolved: last-wins and first-wins are both
            defensible, so silently picking one answers a different question
            from the one that was asked.
    """
    if not text:
        raise _ParameterError(contract.REASON_INVALID_PARAMETER)
    found: dict[str, Fraction] = {}
    for member in text.split(SEPARATOR):
        key, stated, value = member.partition(ASSIGNMENT)
        malformed = not stated or ASSIGNMENT in value or KEY_PATTERN.fullmatch(key) is None
        if malformed or key in found:
            raise _ParameterError(contract.REASON_INVALID_PARAMETER)
        found[key] = _rate(value)
    return found


def _keys(text: str) -> tuple[str, ...]:
    """Read a ``key,key`` parameter.

    Args:
        text: The verbatim parameter text. Empty means an empty set, which is a
            request the solve layer answers rather than a malformed one.

    Returns:
        The keys, in the order stated. Order and repeats are both passed through
        untouched: ``clockspeed/solve/ratio.py`` states that variables run in
        registry order regardless, so normalising here would be this module
        computing something its neighbour already decided.

    Raises:
        _ParameterError: A member is not a well-formed key.
    """
    if not text:
        return ()
    members = tuple(text.split(SEPARATOR))
    if any(KEY_PATTERN.fullmatch(member) is None for member in members):
        raise _ParameterError(contract.REASON_INVALID_PARAMETER)
    return members


def _key(text: str) -> str:
    """Read a parameter that is one bare key and nothing else.

    Args:
        text: The verbatim parameter text.

    Returns:
        The key, unchanged. A key naming nothing in the registry is NOT refused
        here - that is the solve layer's ValueError to raise, exactly as
        :data:`KEY_PATTERN` records for the list-valued parameters.

    Raises:
        _ParameterError: The text is empty, or is not a well-formed key. Both
            separators are outside the pattern, so a comma-joined list and a
            ``key=value`` pair are refused rather than silently truncated to
            their first member.
    """
    if KEY_PATTERN.fullmatch(text) is None:
        raise _ParameterError(contract.REASON_INVALID_PARAMETER)
    return text


def _mode(parameters: Mapping[str, str]) -> str:
    """Read which direction this request asks for.

    Args:
        parameters: The request parameters, before the name check - the mode
            decides WHICH name check applies, so it has to be read first.

    Returns:
        The stated mode, or :data:`MODE_TARGETS` when none was stated.

    Raises:
        _ParameterError: A mode was stated and is not one of :data:`MODES`.
            Refused rather than resolved to the default: a caller who spelled
            ``Supply`` asked for the supply direction and must be told they did
            not get it, not handed a forward solve that looks like an answer.
    """
    stated = parameters.get(PARAM_MODE)
    if stated is None:
        return MODE_TARGETS
    if stated not in MODES:
        raise _ParameterError(contract.REASON_INVALID_PARAMETER)
    return stated


def _ratio_request(parameters: Mapping[str, str]) -> ratio.RatioRequest:
    """Build the pillar 1 request from the parsed parameters.

    Args:
        parameters: The request parameters, names already checked.

    Returns:
        The request. ``byproduct_policy`` is passed through VERBATIM rather than
        validated here: ``ratio._check_policy`` is the published owner of that
        vocabulary, and a second copy at the surface is a fact restated in two
        places (CLAUDE.md section 4).

    Raises:
        _ParameterError: A value is unreadable.
    """
    return ratio.RatioRequest(
        targets=_rates(parameters[PARAM_TARGETS]),
        recipes=_keys(parameters[PARAM_RECIPES]),
        raw_items=_keys(parameters[PARAM_RAW_ITEMS]),
        byproduct_policy=parameters[PARAM_BYPRODUCT_POLICY],
    )


def _supply_request(parameters: Mapping[str, str]) -> ratio.SupplyRequest:
    """Build the reverse-direction request from the parsed parameters.

    Args:
        parameters: The request parameters, names already checked.

    Returns:
        The request. ``supply`` is read by the SAME reader ``targets`` is, so
        the two directions cannot disagree about what an exact rate is spelled
        like, and ``byproduct_policy`` is passed through verbatim for the reason
        :func:`_ratio_request` states.

    Raises:
        _ParameterError: A value is unreadable.
    """
    return ratio.SupplyRequest(
        supply=_rates(parameters[PARAM_SUPPLY]),
        target_item=_key(parameters[PARAM_TARGET_ITEM]),
        recipes=_keys(parameters[PARAM_RECIPES]),
        raw_items=_keys(parameters[PARAM_RAW_ITEMS]),
        byproduct_policy=parameters[PARAM_BYPRODUCT_POLICY],
    )


def _optimize_request(parameters: Mapping[str, str]) -> optimize.OptimizeRequest:
    """Build the pillar 2 request from the parsed parameters.

    Args:
        parameters: The request parameters, names already checked.

    Returns:
        The request. The objective is ASSEMBLED rather than built through
        ``weighted_objective``, so a weight keyed to a direction outside
        ``OBJECTIVES`` reaches ``check_objective`` and is refused as
        ``ObjectiveUndefinedError`` - the solver's verdict. Routing it through
        the keyword-argument door instead would make an unknown direction a
        ``TypeError`` this module had to interpret, which is the surface
        deciding something its neighbour already decides.

    Raises:
        _ParameterError: A value is unreadable.
    """
    return optimize.OptimizeRequest(
        targets=_rates(parameters[PARAM_TARGETS]),
        candidates=_keys(parameters[PARAM_CANDIDATES]),
        unlocked=_keys(parameters[PARAM_UNLOCKED]),
        raw_items=_keys(parameters[PARAM_RAW_ITEMS]),
        byproduct_policy=parameters[PARAM_BYPRODUCT_POLICY],
        objective=optimize.Objective(weights=MappingProxyType(_rates(parameters[PARAM_OBJECTIVE]))),
        config=optimize.SolveConfig(backend=parameters.get(PARAM_BACKEND)),
    )


# ---------------------------------------------------------------------------
# Serialization. Transcription only - nothing here computes.
# ---------------------------------------------------------------------------


def _rational_map(values: Mapping[str, Fraction]) -> dict[str, dict[str, int]]:
    """Render a mapping of exact rates as a mapping of num/den objects.

    Args:
        values: Key to exact rate.

    Returns:
        Key to ``{"num": n, "den": d}``.
    """
    return {key: contract.rational(value) for key, value in values.items()}


def _exclusions(notes: tuple[ratio.ExclusionNote, ...]) -> list[dict[str, str]]:
    """Render the exclusion notes.

    Args:
        notes: The notes, in registry order.

    Returns:
        One object per note. The reason is one of the solve layer's own
        ``EXCLUDED_*`` constants - a closed vocabulary authored there - so it is
        passed through rather than translated.
    """
    return [{"recipe_key": note.recipe_key, "reason": note.reason} for note in notes]


def _plan_data(plan: ratio.ProductionPlan) -> dict[str, object]:
    """Render a solved plan as the endpoint's ``data`` object.

    Field names mirror the dataclass exactly. A renamed field on the wire would
    be a second name for one fact, and the two would drift.

    Args:
        plan: The plan, straight from pillar 1.

    Returns:
        The data object. Every numeric leaf is a num/den object; there is no
        bare number anywhere in it.
    """
    return {
        "steps": [
            {"recipe_key": step.recipe_key, "machines": contract.rational(step.machines)}
            for step in plan.steps
        ],
        "targets": _rational_map(plan.targets),
        "raw_inputs": _rational_map(plan.raw_inputs),
        "byproducts": _rational_map(plan.byproducts),
        "excluded": _exclusions(plan.excluded),
        "byproduct_policy": plan.byproduct_policy,
    }


def _result_data(result: optimize.OptimizeResult) -> dict[str, object]:
    """Render an optimize result as the endpoint's ``data`` object.

    Args:
        result: The result, straight from pillar 2.

    Returns:
        The data object, carrying the chosen plan whole. The plan is nested
        rather than flattened because ``OptimizeResult`` holds a real
        ``ProductionPlan``, and flattening it would make the two endpoints
        disagree about the shape of one model.
    """
    return {
        "backend": result.backend,
        "selection": list(result.selection),
        "plan": _plan_data(result.plan),
        "score": contract.rational(result.score),
        "objective": {"weights": _rational_map(result.objective.weights)},
        "excluded": _exclusions(result.excluded),
    }


# ---------------------------------------------------------------------------
# Refusal routing
# ---------------------------------------------------------------------------


def _solver_refusal(
    endpoint: str, exc: ratio.RatioError | optimize.OptimizeError
) -> contract.Response:
    """Transcribe a solver refusal into the envelope, reading only its type name.

    ``str(exc)`` IS NEVER READ, AND THAT IS THE POINT OF THE WHOLE FUNCTION. Half
    the solver's refusals interpolate a game-content key into their message, so
    reading one here would put registry content on a path that ends in a
    response body.

    The walk is over the MRO rather than a single lookup so an exception class a
    later solver change adds without publishing a row still lands on a published
    refusal - its module's base class, whose line says plainly that the envelope
    does not name the case apart. That is true, and it is what
    ``contract.SOLVER_REFUSALS`` puts both base classes in the table FOR: the
    alternative is a ``KeyError`` escaping the surface as an unhandled error,
    which non-negotiable 7 forbids. The first iteration IS the exact-name lookup,
    so every published class is routed by its own row and nothing else.

    Args:
        endpoint: The route template.
        exc: The refusal, which must derive from one of the two solver base
            classes - both of which are published rows.

    Returns:
        The 503 for a refusal about this machine's build, the 400 for every
        refusal about the request.

    Raises:
        BaseException: The original refusal, re-raised, if no ancestor of it is
            published. Unreachable while both base classes are in the table,
            which ``tests/surface/test_contract.py`` pins. Re-raised rather than
            guessed: an invented verdict would render an unmodelled refusal as a
            named one, which is worse than a loud failure.
    """
    for ancestor in type(exc).__mro__:
        row = contract.SOLVER_REFUSALS.get(ancestor.__name__)
        if row is not None:
            status, reason = row
            if status == contract.STATUS_UNAVAILABLE:
                return contract.unavailable(endpoint, reason)
            return contract.bad_request(endpoint, reason)
    raise exc


# ---------------------------------------------------------------------------
# The handlers
# ---------------------------------------------------------------------------


def _bound_solve(parameters: Mapping[str, str]) -> Callable[[Registry], ratio.ProductionPlan]:
    """Read the whole request and return the solve it asks for, registry apart.

    THE MODE IS READ BEFORE THE NAMES, because it decides WHICH name check
    applies. Checking names first would measure every request against the
    targets grammar and report a supply request as four missing parameters,
    which names the wrong fault.

    THE REGISTRY IS THE ONE THING NOT BOUND IN, and that is the whole reason
    this returns a callable rather than a plan. The grammar must be checked
    before the provider is consulted - see the module docstring - and the solve
    must run after it, so the two halves cannot sit in one function without the
    provider check falling between them. Handing back the chosen call lets the
    handler keep that order with no flag to carry and no branch to repeat.

    Args:
        parameters: The request parameters, unchecked.

    Returns:
        The solve-layer call this request asks for, wanting only a registry.

    Raises:
        _ParameterError: The mode, the parameter names, or a value is not one
            this door accepts.
    """
    if _mode(parameters) == MODE_SUPPLY:
        _check_names(parameters, SOLVE_SUPPLY_REQUIRED, SOLVE_OPTIONAL)
        supply = _supply_request(parameters)
        return lambda registry: ratio.solve_for_supply(registry, supply)

    _check_names(parameters, SOLVE_REQUIRED, SOLVE_OPTIONAL)
    targets = _ratio_request(parameters)
    return lambda registry: ratio.solve_for_targets(registry, targets)


def solve_handler(provider: contract.RegistryProvider[Registry]) -> contract.Handler:
    """Build the ``/api/solve`` handler around a bound registry provider.

    ONE DOOR, TWO DIRECTIONS, AND THE SAME ANSWER SHAPE OUT OF BOTH. The solve
    layer publishes ``solve_for_targets`` and ``solve_for_supply``, and both
    return a ``ProductionPlan`` - the reverse direction re-solves forwards at the
    rate the supply buys rather than scaling a unit plan, so the plan a caller
    gets back is a plan the forward path produced and audited. Serializing the
    two through :func:`_plan_data` is therefore transcription of one model and
    not two, which is why the supply mode adds no field to the response.

    A SECOND TEMPLATE WOULD HAVE BEEN THE OTHER SHAPE, AND IT COSTS MORE THAN IT
    LOOKS. ``BOOTSTRAP.md`` section 7.1 owns the published template set and
    ``clockspeed/surface/api/health.py`` mirrors it, so a route is a
    specification edit; a direction is not. Pillar 1 is one question asked two
    ways round, and the ANSWER is byte-identical in shape either way.

    Args:
        provider: Whatever hands this endpoint the registry. Bound by the server
            before registration, so this module never imports the server.

    Returns:
        The handler.
    """

    def handler(parameters: Mapping[str, str]) -> contract.Response:
        try:
            bound = _bound_solve(parameters)
        except _ParameterError as exc:
            return contract.bad_request(SOLVE_ENDPOINT, exc.reason)

        registry = provider.registry()
        if registry is None:
            return contract.unavailable(SOLVE_ENDPOINT, contract.REASON_NO_GAME_INSTALL)

        try:
            plan = bound(registry)
        except (ratio.RatioError, optimize.OptimizeError) as exc:
            # UnboundedSupply arrives here and is routed by name like every
            # other solver verdict - nothing about the reverse direction is
            # decided at this layer.
            return _solver_refusal(SOLVE_ENDPOINT, exc)
        except ValueError:
            # A caller SHAPE bug the solve layer names as such: a recipe key
            # that models nothing here, or an item declared both raw and a
            # target. Caught by TYPE alone - the message names the offending
            # keys, so reading it would echo registry content.
            return contract.bad_request(SOLVE_ENDPOINT, contract.REASON_INVALID_PARAMETER)

        return contract.ok(SOLVE_ENDPOINT, _plan_data(plan))

    return handler


def optimize_handler(provider: contract.RegistryProvider[Registry]) -> contract.Handler:
    """Build the ``/api/optimize`` handler around a bound registry provider.

    Args:
        provider: Whatever hands this endpoint the registry.

    Returns:
        The handler.
    """

    def handler(parameters: Mapping[str, str]) -> contract.Response:
        try:
            _check_names(parameters, OPTIMIZE_REQUIRED, OPTIMIZE_OPTIONAL)
            request = _optimize_request(parameters)
        except _ParameterError as exc:
            return contract.bad_request(OPTIMIZE_ENDPOINT, exc.reason)

        registry = provider.registry()
        if registry is None:
            return contract.unavailable(OPTIMIZE_ENDPOINT, contract.REASON_NO_GAME_INSTALL)

        try:
            result = optimize.optimize_plan(registry, request)
        except (ratio.RatioError, optimize.OptimizeError) as exc:
            return _solver_refusal(OPTIMIZE_ENDPOINT, exc)
        except ValueError:
            # As on the solve door: a candidate naming no recipe in this
            # registry is a caller shape bug, and its message names the keys.
            return contract.bad_request(OPTIMIZE_ENDPOINT, contract.REASON_INVALID_PARAMETER)

        return contract.ok(OPTIMIZE_ENDPOINT, _result_data(result))

    return handler


def routes(provider: contract.RegistryProvider[Registry]) -> tuple[contract.Route, ...]:
    """Every route this module publishes, with the provider already bound.

    Args:
        provider: Whatever hands these endpoints the registry.

    Returns:
        The two POST routes, in a stable order.
    """
    return (
        contract.Route(
            method=METHOD_POST, template=SOLVE_ENDPOINT, handler=solve_handler(provider)
        ),
        contract.Route(
            method=METHOD_POST, template=OPTIMIZE_ENDPOINT, handler=optimize_handler(provider)
        ),
    )
