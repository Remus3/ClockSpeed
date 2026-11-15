"""Pillar 5 on the wire: ``/api/advice`` and ``/api/advice/<id>/derivation``.

Owns (BOOTSTRAP.md section 7.1): the READ routes of the advisor.
``/api/advice`` carries every card with explain tier 1 (the headline) and tier
2 (the one-line reason), plus the card's resolved per-world ledger state and
its global mute flag, and what a stated plan request came to.
``/api/advice/<id>/derivation`` carries tier 3, the full derivation, for one
card.

THIS MODULE TRANSCRIBES; IT DOES NOT COMPUTE. Every field is read off an
:class:`clockspeed.advisor.advise.Advice` that the layer below produced. The
rules ran, the cards were projected from their traces and both stores were
consulted before this module sees anything, through the :class:`AdviceSource`
the server binds in. Tier text is the card's own projection - never written,
trimmed or reworded here (non-negotiable 8).

HIDDEN CARDS ARE SERVED, FLAGGED. A dismissed, completed, actively snoozed or
muted card is listed with ``visible`` false and its state, because the advisor
keeps it precisely so a surface can offer to restore it. Dropping it here would
make "dismissed" and "never advised" the same answer.

THE REFUSALS ARE THE OTHER ROUTES' REFUSALS. No world is 503 ``no_save``; no
install is 503 ``no_game_install`` - the power balance prices built machines
against the registry, and pricing them against nothing would be silently wrong;
a store the source could not read is 503 ``advice_store_unreadable``. A
parameter a route does not take is 400, and a card id the current advice
does not carry is 400 ``invalid_parameter``. No 400 reflects what it refused.

A STATED TARGET (CS-1371). Every route here takes :data:`TARGET_PARAMETER`,
:data:`RATE_PARAMETER`, :data:`DIRECTION_PARAMETER` and
:data:`BYPRODUCT_POLICY_PARAMETER`, all four or none. Stated, the source asks the advisor
for that plan, so a plan card is on the listing, its id hits the derivation route and the
state route records it; the listing also carries ``plan_outcome``, because a refused trace
yields no card and a reader has nothing else to read why from. It is copied field by field
off :attr:`clockspeed.advisor.advise.Advice.plan_outcome`, absent rather than null when
no target was stated, so that body is what it was before this item. On ``no-route`` and
``route-refused`` it carries that word's reason as ``redesign_reason`` (CS-1380), because a
bare word would read as proof that no plan exists, and it names any raw item no extractor
joins as ``raw_unknown`` (CS-1382). Not stated, the derivation
and state routes answer as they did before it, so a plan card's id is 400 there.

THE ORDER OF A REFUSAL IS THE CONTRACT. An unknown name is 400 ``unknown_parameter``; any of
the four without the other three is 400 ``missing_parameter``; a rate, direction or policy
the source refuses is 400 ``invalid_parameter``. All of that comes before any provider is
read, as ``clockspeed/surface/api/solve.py`` refuses a request's shape first. Then no world
and no install answer their 503s, so a missing save still says so however the request was
worded, and only then is the target tested against the registry and refused 400
``invalid_parameter``, before any advice is computed. THIS ROUTE REFUSES AN UNKNOWN KEY ON
PURPOSE, which ``clockspeed/surface/api/solve.py`` leaves to the solve layer: what may be
stated is published on ``/api/registry``, so a key off that list is a malformed request and
never a question for a search, and it reaches no solve. Which values pass is the advisor's
to say, through the source: this module tests no vocabulary, and parses no rate, which stays
text until the advisor reads it, so no float can come of it. It catches no exception, so it
reads no exception's message.

A STATED SCHEMATIC (CS-1373). :data:`SCHEMATIC_PARAMETER` with :data:`DIRECTION_PARAMETER` and
:data:`BYPRODUCT_POLICY_PARAMETER` states a plan for a schematic's whole cost, in place of
:data:`TARGET_PARAMETER` and :data:`RATE_PARAMETER`: a schematic states no rate, because each
cost item's rate is the one its requirement publishes, which the advisor reads and this module
never sees. A ``target`` or a ``rate`` beside ``schematic`` is 400 ``invalid_parameter``, and a
direction or policy missing is 400 ``missing_parameter``, both before any provider is read. Then
no world and no install answer their 503s, and a catalog the schematic source publishes none of
is 503 ``no_game_install``; only then is the schematic put to the advisor through
:meth:`SchematicAdviceSource.schematic_request`, and one the catalog does not hold is 400
``invalid_parameter``. The catalog arrives through a :class:`SchematicCatalogs` provider the
routes are bound with, a source that publishes none when it is not. One request is handed to
the advisor whatever the schematic costs, so the listing carries one plan card, never one per
cost item. A schematic whose requirement publishes no rates reads ``plan_outcome`` status
``schematic-unplannable`` with its reason word in ``reason``, which names after the word any cost
item no plan can be stated for, and no plan card.

PRIVACY. The world token is handed to the source with the world and is not
read here at all. No field below is the token, a save path or a world name.

IN THE ROUTE TABLE SINCE CS-1270. ``clockspeed/surface/api/routes.py`` binds
:func:`routes` to ``clockspeed/surface/providers.py``'s ``StoreAdviceSource``,
which hands the world and the registry to the advisor's own
``clockspeed.advisor.advise.advise_world``. Composing the audit models is the
advisor's job: no surface module may reach the audit machines model (CS-1189),
and none imports the audit layer at all.

THE STATE ROUTE IS HERE SINCE CS-1269. ``POST /api/advice/<id>/state`` records
one card's state in the per-world ledger: ``accepted``, ``dismissed``,
``pinned``, ``new`` (which restores a hidden card) or ``snoozed`` with an
``until`` instant that must lie after now. The state and the instant arrive as
query parameters, because a handler is handed query parameters and the path
capture only. The card must be one the CURRENT advice lists, the stated advice when
the four are stated, so the advice is resolved first and the id compared against it; the
write itself is the bound
:class:`AdviceStore`'s, which hands it to the advisor's ledger. ``completed`` is
not recordable here - a card is completed by the world, not by a click.

WHY A GET ON IT IS 405 RATHER THAN 404 OR 501. The path is real and only the
verb is wrong, so :func:`method_boundary_routes` publishes a GET route that
answers ``contract.method_not_allowed``. It is published apart from
:func:`routes` because the aggregate table is read keyed by template, and a
second entry under one template would be silently dropped by that read.

THE CROSS-ORIGIN REFUSAL IS NOT HERE. A handler sees query parameters only and
cannot tell the dashboard from a cross-site form posting to the loopback port.
``clockspeed/surface/server.py`` refuses every mutating request that carries no
same-origin proof BEFORE a handler runs, so this handler is reached only by a
request the server has already admitted.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# The stated models consumed here are clockspeed.advisor.advise.Advice and the two
# clockspeed.advisor.plans request models, named under TYPE_CHECKING only. This
# module opens no file, imports no store and calls no advisor function: the source
# bound in is what reads the ledger and the mutes and what checks a stated request.

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable

from clockspeed.surface.api import contract, flow_view

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.advisor.advise import Advice, AdvisedCard
    from clockspeed.advisor.plans import PlanParameters, PlanRequest, SchematicParameters
    from clockspeed.advisor.rules.plan import PlanOutcome
    from clockspeed.data.registry import Registry
    from clockspeed.data.schematics import SchematicCatalog
    from clockspeed.save.world import WorldModel

__all__ = [
    "BYPRODUCT_POLICY_PARAMETER",
    "CARD_KEYS",
    "DATA_KEYS",
    "DERIVATION_ENDPOINT",
    "DERIVATION_KEYS",
    "DIRECTION_PARAMETER",
    "ENDPOINT",
    "ID_PARAMETER",
    "MAX_UNTIL_DIGITS",
    "METHOD_GET",
    "METHOD_POST",
    "PLAN_OUTCOME_KEYS",
    "PLAN_PARAMETERS",
    "RATE_PARAMETER",
    "RECORDABLE_STATES",
    "SCHEMATIC_PARAMETER",
    "SNOOZED",
    "STATED_DATA_KEYS",
    "STATE_ENDPOINT",
    "STATE_KEYS",
    "STATE_PARAMETER",
    "TARGET_PARAMETER",
    "UNTIL_PARAMETER",
    "AdviceSource",
    "AdviceStore",
    "SchematicAdviceSource",
    "SchematicCatalogs",
    "make_derivation_handler",
    "make_handler",
    "make_state_handler",
    "method_boundary_routes",
    "routes",
]

#: The card listing, tiers 1 and 2.
ENDPOINT: Final = "/api/advice"

#: One card's full derivation, tier 3.
DERIVATION_ENDPOINT: Final = "/api/advice/<id>/derivation"

#: Accept, dismiss, snooze, pin or restore one card (CS-1269). MUTATING.
STATE_ENDPOINT: Final = "/api/advice/<id>/state"

#: The listing and the derivation are reads.
METHOD_GET: Final = "GET"

#: The state route mutates the ledger.
METHOD_POST: Final = "POST"

#: The state route's query parameter naming the state to record.
STATE_PARAMETER: Final = "state"

#: The state route's query parameter carrying a snooze's end instant, in whole
#: seconds since the epoch - the unit the advice source's clock answers in.
UNTIL_PARAMETER: Final = "until"

#: What a stated plan is for, one item key off ``/api/registry``'s ``plan_targets``.
TARGET_PARAMETER: Final = "target"

#: How much of it a minute: an integer, an exact decimal or ``num/den``, read as text.
RATE_PARAMETER: Final = "rate"

#: Which rung the stated plan is graded under.
DIRECTION_PARAMETER: Final = "direction"

#: What the stated plan may do with a byproduct.
BYPRODUCT_POLICY_PARAMETER: Final = "byproduct_policy"

#: The four that state a plan, on every route here: all of them or none.
PLAN_PARAMETERS: Final = (
    TARGET_PARAMETER,
    RATE_PARAMETER,
    DIRECTION_PARAMETER,
    BYPRODUCT_POLICY_PARAMETER,
)

#: A schematic a plan is stated for (CS-1373): one ClassName off the catalog, in place of
#: ``target`` and ``rate``, which are refused beside it.
SCHEMATIC_PARAMETER: Final = "schematic"

#: What a schematic statement carries beside the schematic itself.
SCHEMATIC_COMPANIONS: Final = (DIRECTION_PARAMETER, BYPRODUCT_POLICY_PARAMETER)

#: The one recordable kind that carries an ``until``.
SNOOZED: Final = "snoozed"

#: The kinds a client may record. ``new`` forgets the card, which restores a
#: hidden one; ``completed`` is absent because the world completes a card, not a
#: click. Membership is checked here so an unknown kind is refused before any
#: world is read.
RECORDABLE_STATES: Final = frozenset({"accepted", "dismissed", "pinned", "new", SNOOZED})

#: The longest ``until`` accepted, in decimal digits. Bounds the parse so a
#: caller cannot hand the int constructor an arbitrarily long string.
MAX_UNTIL_DIGITS: Final = 18

#: The state route's success body keys.
STATE_KEYS: Final = frozenset({"id", "state", "snoozed_until"})

#: The path capture naming the card. The server writes it from the path and it
#: overwrites any query parameter of the same name.
ID_PARAMETER: Final = "id"

#: The listing body's keys with no plan stated.
DATA_KEYS: Final = frozenset({"new_world", "cards"})

#: The listing body's keys with a plan stated.
STATED_DATA_KEYS: Final = DATA_KEYS | {"plan_outcome"}

#: The keys ``plan_outcome`` may carry. ``status`` and ``redesign`` always; each of the others
#: only where the outcome holds it, and absent rather than null where it does not, and
#: ``raw_unknown`` only where it names an item.
PLAN_OUTCOME_KEYS: Final = frozenset(
    {"status", "redesign", "reason", "redesign_reason", "trimmed", "unmade", "raw_unknown"}
)

#: One listed card's keys. ``headline`` is tier 1 and ``reason`` tier 2;
#: ``snoozed_until`` is the snooze instant, null for every other state.
CARD_KEYS: Final = frozenset(
    {
        "id",
        "rule_id",
        "domain",
        "headline",
        "reason",
        "state",
        "snoozed_until",
        "muted",
        "visible",
    }
)

#: The derivation body's keys. ``derivation`` is tier 3. ``flow`` is the CS-1360 boundary
#: flow view of the plan the card's trace holds, or null for a card whose trace holds none.
DERIVATION_KEYS: Final = frozenset({"id", "rule_id", "derivation", "flow"})


@runtime_checkable
class AdviceSource(Protocol):
    """Whatever turns one world and one registry into resolved advice.

    :meth:`advice` returns None when the advice stores could not be read - the endpoint
    turns that into a 503 rather than an empty listing that would read as "no advice".
    :meth:`plan_parameters` and :meth:`plan_request` are the advisor's own checks on what a
    caller stated, so this module holds no opinion on which values pass. Each answers None
    to refuse, with no text, so nothing a caller typed can come back out of one.
    """

    def advice(
        self, world: WorldModel, registry: Registry, *, plan_request: PlanRequest | None = None
    ) -> Advice | None:
        """Run the advisor over one world, or None when a store is unreadable."""
        ...

    def plan_parameters(
        self, *, rate: str, direction: str, byproduct_policy: str
    ) -> PlanParameters | None:
        """Check a stated rate, direction and policy, reading no provider, or refuse them."""
        ...

    def plan_request(
        self, registry: Registry, target: str, parameters: PlanParameters
    ) -> PlanRequest | None:
        """Build the request a target and checked parameters ask, or refuse the target."""
        ...


@runtime_checkable
class SchematicAdviceSource(AdviceSource, Protocol):
    """An advice source that can also state a plan for a schematic (CS-1373).

    Apart from :class:`AdviceSource` so a source written before it stays an advice source.
    Each answers None to refuse, with no text.
    """

    def schematic_parameters(
        self, *, direction: str, byproduct_policy: str
    ) -> SchematicParameters | None:
        """Check a stated direction and policy beside a schematic, or refuse them."""
        ...

    def schematic_request(
        self,
        catalog: SchematicCatalog,
        registry: Registry,
        world: WorldModel,
        schematic: str,
        parameters: SchematicParameters,
    ) -> PlanRequest | None:
        """Build the one request a schematic asks, or refuse a schematic the catalog lacks."""
        ...


class SchematicCatalogs[CatalogT](Protocol):
    """Whatever hands an endpoint the schematic catalog, or says there is not one.

    Generic for the same reason :class:`contract.RegistryProvider` is, and ``None`` means the
    same thing: no game installation was found, which is a 503 rather than a failure.
    """

    def catalog(self) -> CatalogT | None:
        """The normalized catalog, or None when this machine has no install."""
        ...


class _StatedSchematic(tuple[str, "SchematicParameters"]):
    """A stated schematic and its checked direction and policy, as the pair (schematic, parameters).

    Index 0 is the ClassName as received, tested against the catalog and never rendered, and
    index 1 is what the source's door checked. A tuple, so it reads as the item statement's
    pair does, and a class of its own only so :func:`_request_for` can tell the two apart; it
    declares no field, so no generated ``__repr__`` and no census population member is made.
    """

    __slots__ = ()


type _Stated = tuple[str, PlanParameters] | _StatedSchematic


@runtime_checkable
class AdviceStore(AdviceSource, Protocol):
    """An advice source that can also record one card's state (CS-1269).

    :meth:`record` answers True when the state was written, False when the
    ledger refused the value - a snooze that does not end after now - and None
    when the store could not be read or written. The endpoint has already
    checked the kind and that the card is listed; the instant comparison is the
    ledger's, because ``surface/`` never computes.
    """

    def record(self, world: WorldModel, card_id: str, kind: str, until: int | None) -> bool | None:
        """Record one card's state in the world's ledger."""
        ...


def _card(advised: AdvisedCard) -> dict[str, object]:
    """Transcribe one resolved card, tiers 1 and 2 only.

    Args:
        advised: The card and its resolved state.

    Returns:
        The card, keyed by :data:`CARD_KEYS`.
    """
    card = advised.card
    return {
        "id": card.id,
        "rule_id": card.rule_id,
        "domain": card.domain,
        "headline": card.tier1,
        "reason": card.tier2,
        "state": advised.state.kind,
        "snoozed_until": advised.state.until,
        "muted": advised.muted,
        "visible": advised.visible,
    }


def _outcome(outcome: PlanOutcome) -> dict[str, object]:
    """Transcribe what a stated request came to, field by field.

    Args:
        outcome: The advisor's own projection. Every word in it is the advisor's.

    Returns:
        The outcome, keyed by :data:`PLAN_OUTCOME_KEYS`. A field the outcome does not hold
        is absent, never null, so "no such word" cannot read as an empty one. ``raw_unknown``
        is absent when it is empty too, so a body stays what it was until the docs name a raw
        item no extractor joins, which the pinned docs do not.
    """
    body: dict[str, object] = {"status": outcome.status, "redesign": outcome.redesign}
    if outcome.reason is not None:
        body["reason"] = outcome.reason
    if outcome.redesign_reason is not None:
        body["redesign_reason"] = outcome.redesign_reason
    if outcome.trimmed is not None:
        body["trimmed"] = list(outcome.trimmed)
    if outcome.unmade is not None:
        body["unmade"] = list(outcome.unmade)
    if outcome.raw_unknown:
        body["raw_unknown"] = list(outcome.raw_unknown)
    return body


def _listing(found: Advice) -> dict[str, object]:
    """Transcribe the listing body.

    THE LIST ORDER IS THE ADVISOR'S SHOWING ORDER (CS-1246):
    :attr:`clockspeed.advisor.advise.Advice.ranked`, quick wins first with an aged
    card brought to the top, not the identity order of ``cards``. Every card is
    listed either way - a hidden one with ``visible`` false - so the order changes
    what a reader meets first and never what the body holds.

    Args:
        found: The advice.

    Returns:
        The body, keyed by :data:`DATA_KEYS`, or by :data:`STATED_DATA_KEYS` when the advice
        carries an outcome, which the advisor sets exactly when a request was stated.
    """
    body: dict[str, object] = {
        "new_world": found.new_world,
        "cards": [_card(advised) for advised in found.ranked],
    }
    if found.plan_outcome is not None:
        body["plan_outcome"] = _outcome(found.plan_outcome)
    return body


def _stated_plan(
    endpoint: str,
    query: Mapping[str, str],
    source: AdviceSource,
    *,
    own: tuple[str, ...],
) -> _Stated | contract.Response | None:
    """Refuse what can be refused before any provider is read, and name what was stated.

    Args:
        endpoint: The template the refusal names.
        query: The path capture and the query parameters.
        source: The advice source, whose door checks the rate, the direction and the policy.
        own: The route's own parameters, beside the four and the schematic's.

    Returns:
        The target and the checked parameters, or the schematic and its checked parameters;
        None when no plan is stated; or the 400 that refuses the request, which names nothing
        it refused.
    """
    if any(
        name not in own and name not in PLAN_PARAMETERS and name != SCHEMATIC_PARAMETER
        for name in query
    ):
        return contract.bad_request(endpoint, contract.REASON_UNKNOWN_PARAMETER)
    if SCHEMATIC_PARAMETER in query:
        return _stated_schematic(endpoint, query, source)
    stated = sum(1 for name in PLAN_PARAMETERS if name in query)
    if stated == 0:
        return None
    if stated != len(PLAN_PARAMETERS):
        return contract.bad_request(endpoint, contract.REASON_MISSING_PARAMETER)
    parameters = source.plan_parameters(
        rate=query[RATE_PARAMETER],
        direction=query[DIRECTION_PARAMETER],
        byproduct_policy=query[BYPRODUCT_POLICY_PARAMETER],
    )
    if parameters is None:
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    return query[TARGET_PARAMETER], parameters


def _stated_schematic(
    endpoint: str, query: Mapping[str, str], source: AdviceSource
) -> _StatedSchematic | contract.Response:
    """Refuse what can be refused of a stated schematic before any provider is read.

    Args:
        endpoint: The template the refusal names.
        query: The path capture and the query parameters, ``schematic`` among them.
        source: The advice source, whose door checks the direction and the policy.

    Returns:
        The schematic and the checked parameters, or the 400 that refuses the request. A
        ``target`` or a ``rate`` beside the schematic is ``invalid_parameter``, a companion
        missing is ``missing_parameter``, and a source that cannot state a schematic refuses
        it as it refuses any value it does not take.
    """
    if TARGET_PARAMETER in query or RATE_PARAMETER in query:
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    if any(name not in query for name in SCHEMATIC_COMPANIONS):
        return contract.bad_request(endpoint, contract.REASON_MISSING_PARAMETER)
    if not isinstance(source, SchematicAdviceSource):
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    parameters = source.schematic_parameters(
        direction=query[DIRECTION_PARAMETER],
        byproduct_policy=query[BYPRODUCT_POLICY_PARAMETER],
    )
    if parameters is None:
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    return _StatedSchematic((query[SCHEMATIC_PARAMETER], parameters))


class _SeenRegistry:
    """A registry provider that remembers the one registry it handed over.

    The derivation handler needs the items' verbatim forms for the flow view, and
    :func:`_resolve_in_world` already reads the registry once and warns against a
    second provider read. This wrapper is that one read: it forwards the call and
    keeps the answer, so the handler reads the forms off what the resolution saw
    and the provider is asked exactly once per request.
    """

    def __init__(self, provider: contract.RegistryProvider[Registry]) -> None:
        """Hold the provider.

        Args:
            provider: The registry provider the handler was bound with.
        """
        self._provider = provider
        self._seen: Registry | None = None

    def registry(self) -> Registry | None:
        """Forward the read and remember its answer.

        Returns:
            The registry, or None when this machine has no install.
        """
        self._seen = self._provider.registry()
        return self._seen

    def forms(self) -> dict[str, str] | None:
        """Item key to verbatim ``mForm`` over the registry the read returned.

        Returns:
            The mapping, or None when no registry was read - every transport then
            reads unknown.
        """
        if self._seen is None:
            return None
        return {key: item.form for key, item in self._seen.items.items()}


def _resolve(
    endpoint: str,
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
    stated: _Stated | None,
    schematics: SchematicCatalogs[SchematicCatalog] | None,
) -> Advice | contract.Response:
    """Fetch the advice, or the refusal that stands in for it.

    Args:
        endpoint: The template the refusal names.
        worlds: The world provider.
        registries: The registry provider.
        source: The advice source.
        stated: What :func:`_stated_plan` read, or None when no plan is stated.
        schematics: The catalog provider, or None for one that publishes none.

    Returns:
        The advice, or the refusal naming what was missing or off the list.
    """
    resolved = _resolve_in_world(endpoint, worlds, registries, source, stated, schematics)
    if isinstance(resolved, contract.Response):
        return resolved
    return resolved[1]


def _resolve_in_world(
    endpoint: str,
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
    stated: _Stated | None,
    schematics: SchematicCatalogs[SchematicCatalog] | None,
) -> tuple[WorldModel, Advice] | contract.Response:
    """Fetch the world and its advice together, or the refusal for either.

    The state route needs the SAME world the advice was resolved over, so the
    record lands in the ledger of the world whose card was checked rather than
    of whatever a second provider read would hand back. A stated target is tested
    here, after both providers and before the advice, because the list it is tested
    against is the registry's and a missing save or install still says so first.

    Args:
        endpoint: The template the refusal names.
        worlds: The world provider.
        registries: The registry provider.
        source: The advice source.
        stated: What :func:`_stated_plan` read, or None when no plan is stated.
        schematics: The catalog provider, or None for one that publishes none. Read only for
            a stated schematic, and only after the world and the registry.

    Returns:
        (world, advice), or a 503 naming what was missing, or the 400 refusing a target or a
        schematic off the list, which names nothing it refused.
    """
    model = worlds.world()
    if model is None:
        return contract.unavailable(endpoint, contract.REASON_NO_SAVE)
    registry = registries.registry()
    if registry is None:
        return contract.unavailable(endpoint, contract.REASON_NO_GAME_INSTALL)
    plan_request = None
    if stated is not None:
        asked = _request_for(endpoint, stated, model, registry, source, schematics)
        if isinstance(asked, contract.Response):
            return asked
        plan_request = asked
    found = source.advice(model, registry, plan_request=plan_request)
    if found is None:
        return contract.unavailable(endpoint, contract.REASON_ADVICE_STORE_UNREADABLE)
    return model, found


def _request_for(
    endpoint: str,
    stated: _Stated,
    model: WorldModel,
    registry: Registry,
    source: AdviceSource,
    schematics: SchematicCatalogs[SchematicCatalog] | None,
) -> PlanRequest | contract.Response:
    """Put a stated target or schematic to the advisor, or refuse it.

    Args:
        endpoint: The template the refusal names.
        stated: What :func:`_stated_plan` read.
        model: The world, read already. Handed on and not read here.
        registry: The normalized registry, read already.
        source: The advice source.
        schematics: The catalog provider, or None for one that publishes none.

    Returns:
        The request, or the 400 refusing a target or schematic off the list, or the 503 when
        a stated schematic meets no catalog.
    """
    if not isinstance(stated, _StatedSchematic):
        target, parameters = stated
        asked = source.plan_request(registry, target, parameters)
    else:
        catalog = None if schematics is None else schematics.catalog()
        if catalog is None:
            return contract.unavailable(endpoint, contract.REASON_NO_GAME_INSTALL)
        if not isinstance(source, SchematicAdviceSource):
            return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
        asked = source.schematic_request(catalog, registry, model, stated[0], stated[1])
    if asked is None:
        return contract.bad_request(endpoint, contract.REASON_INVALID_PARAMETER)
    return asked


def _instant(raw: str) -> int | None:
    """Parse an ``until`` parameter, or None when it is not a bounded decimal.

    ASCII decimal digits only: ``str.isdigit`` alone admits other scripts'
    digits and superscripts, a sign or a point would make the value something
    other than a whole second, and the length bound keeps the parse cheap.

    Args:
        raw: The parameter as received.

    Returns:
        The instant, or None.
    """
    if not raw or len(raw) > MAX_UNTIL_DIGITS:
        return None
    if not (raw.isascii() and raw.isdigit()):
        return None
    return int(raw)


def _state_request(
    query: Mapping[str, str], source: AdviceSource
) -> tuple[str, str, int | None, _Stated | None] | contract.Response:
    """Validate a state request's parameters before any world is read.

    Args:
        query: The path capture and the query parameters.
        source: The advice source, whose door checks a stated plan's values.

    Returns:
        (card id, kind, until, what :func:`_stated_plan` read), or the 400 that
        refuses the request. No 400 names the value it refused.
    """
    stated = _stated_plan(
        STATE_ENDPOINT,
        query,
        source,
        own=(ID_PARAMETER, STATE_PARAMETER, UNTIL_PARAMETER),
    )
    if isinstance(stated, contract.Response):
        return stated
    card_id = query.get(ID_PARAMETER)
    kind = query.get(STATE_PARAMETER)
    if card_id is None or kind is None:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_MISSING_PARAMETER)
    if kind not in RECORDABLE_STATES:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
    until = _until_for(kind, query.get(UNTIL_PARAMETER))
    if isinstance(until, contract.Response):
        return until
    return card_id, kind, until, stated


def _until_for(kind: str, raw_until: str | None) -> int | None | contract.Response:
    """The ``until`` a kind needs: required for a snooze, refused on anything else.

    Args:
        kind: A recordable kind.
        raw_until: The ``until`` parameter as received, or None when absent.

    Returns:
        The instant for a snooze, None for any other kind, or the 400 refusing
        a missing, misplaced or malformed ``until``.
    """
    if kind != SNOOZED:
        if raw_until is None:
            return None
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
    if raw_until is None:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_MISSING_PARAMETER)
    until = _instant(raw_until)
    if until is None:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
    return until


def make_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
    schematics: SchematicCatalogs[SchematicCatalog] | None = None,
) -> contract.Handler:
    """Bind the providers and return the listing handler.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor and reads the stores.
        schematics: Whatever hands over the schematic catalog, or None for a source that
            publishes none, which makes a stated schematic 503 ``no_game_install``.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request. Takes the four of a stated plan, or nothing at all."""
        stated = _stated_plan(ENDPOINT, query, source, own=())
        if isinstance(stated, contract.Response):
            return stated
        found = _resolve(ENDPOINT, worlds, registries, source, stated, schematics)
        if isinstance(found, contract.Response):
            return found
        return contract.ok(ENDPOINT, _listing(found))

    return handle


def make_derivation_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
    schematics: SchematicCatalogs[SchematicCatalog] | None = None,
) -> contract.Handler:
    """Bind the providers and return the derivation handler.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor and reads the stores.
        schematics: As :func:`make_handler` takes it.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request: the ``id`` capture, and the four of a stated plan or none."""
        stated = _stated_plan(DERIVATION_ENDPOINT, query, source, own=(ID_PARAMETER,))
        if isinstance(stated, contract.Response):
            return stated
        wanted = query.get(ID_PARAMETER)
        if wanted is None:
            return contract.bad_request(DERIVATION_ENDPOINT, contract.REASON_MISSING_PARAMETER)
        seen = _SeenRegistry(registries)
        found = _resolve(DERIVATION_ENDPOINT, worlds, seen, source, stated, schematics)
        if isinstance(found, contract.Response):
            return found
        for advised in found.cards:
            card = advised.card
            if card.id == wanted:
                return contract.ok(
                    DERIVATION_ENDPOINT,
                    {
                        "id": card.id,
                        "rule_id": card.rule_id,
                        "derivation": card.tier3,
                        "flow": flow_view.view_of(card.trace, forms=seen.forms()),
                    },
                )
        return contract.bad_request(DERIVATION_ENDPOINT, contract.REASON_INVALID_PARAMETER)

    return handle


def make_state_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceStore,
    schematics: SchematicCatalogs[SchematicCatalog] | None = None,
) -> contract.Handler:
    """Bind the providers and return the state-recording handler (CS-1269).

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor, reads the stores and records a state.
        schematics: As :func:`make_handler` takes it.

    Returns:
        The handler. It is reached only through a request the server admitted
        past its same-origin refusal.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request: the ``id`` capture, ``state``, maybe ``until``, and the four."""
        asked = _state_request(query, source)
        if isinstance(asked, contract.Response):
            return asked
        wanted, kind, until, stated = asked
        resolved = _resolve_in_world(STATE_ENDPOINT, worlds, registries, source, stated, schematics)
        if isinstance(resolved, contract.Response):
            return resolved
        model, found = resolved
        listed = [advised.card.id for advised in found.cards if advised.card.id == wanted]
        if not listed:
            return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
        recorded = source.record(model, listed[0], kind, until)
        if recorded is None:
            return contract.unavailable(STATE_ENDPOINT, contract.REASON_ADVICE_STORE_UNWRITABLE)
        if not recorded:
            return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
        return contract.ok(
            STATE_ENDPOINT,
            {"id": listed[0], "state": kind, "snoozed_until": until},
        )

    return handle


def method_boundary_routes() -> tuple[contract.Route, ...]:
    """The GET on the state template, answering 405 rather than 404.

    Published apart from :func:`routes` - see the module docstring for why.
    Provider-free, so every route table shares it.

    Returns:
        The one method-boundary route.
    """

    def handle(_query: Mapping[str, str]) -> contract.Response:
        return contract.method_not_allowed(STATE_ENDPOINT)

    return (contract.Route(method=METHOD_GET, template=STATE_ENDPOINT, handler=handle),)


def routes(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceStore,
    schematics: SchematicCatalogs[SchematicCatalog] | None = None,
) -> tuple[contract.Route, ...]:
    """Publish the listing, derivation and state routes, with the providers bound in.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor, reads the stores and records a state.
        schematics: Whatever hands over the schematic catalog, or None for a source that
            publishes none (CS-1373).

    Returns:
        The listing route, the derivation route, then the state route.
    """
    return (
        contract.Route(
            method=METHOD_GET,
            template=ENDPOINT,
            handler=make_handler(worlds, registries, source, schematics),
        ),
        contract.Route(
            method=METHOD_GET,
            template=DERIVATION_ENDPOINT,
            handler=make_derivation_handler(worlds, registries, source, schematics),
        ),
        contract.Route(
            method=METHOD_POST,
            template=STATE_ENDPOINT,
            handler=make_state_handler(worlds, registries, source, schematics),
            mutates=True,
        ),
    )
