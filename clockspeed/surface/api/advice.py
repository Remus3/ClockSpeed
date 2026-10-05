"""Pillar 5 on the wire: ``/api/advice`` and ``/api/advice/<id>/derivation``.

Owns (BOOTSTRAP.md section 7.1): the READ routes of the advisor.
``/api/advice`` carries every card with explain tier 1 (the headline) and tier
2 (the one-line reason), plus the card's resolved per-world ledger state and
its global mute flag. ``/api/advice/<id>/derivation`` carries tier 3, the full
derivation, for one card.

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
parameter this route does not take is 400, and a card id the current advice
does not carry is 400 ``invalid_parameter``. No 400 reflects what it refused.

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
capture only. The card must be one the CURRENT advice lists, so the advice is
resolved first and the id compared against it; the write itself is the bound
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
# The stated model consumed here is clockspeed.advisor.advise.Advice, named
# under TYPE_CHECKING only. This module opens no file and imports no store: the
# source bound in is what reads the ledger and the mutes.

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable

from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Mapping

    from clockspeed.advisor.advise import Advice, AdvisedCard
    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

__all__ = [
    "CARD_KEYS",
    "DATA_KEYS",
    "DERIVATION_ENDPOINT",
    "DERIVATION_KEYS",
    "ENDPOINT",
    "ID_PARAMETER",
    "MAX_UNTIL_DIGITS",
    "METHOD_GET",
    "METHOD_POST",
    "RECORDABLE_STATES",
    "SNOOZED",
    "STATE_ENDPOINT",
    "STATE_KEYS",
    "STATE_PARAMETER",
    "UNTIL_PARAMETER",
    "AdviceSource",
    "AdviceStore",
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

#: The listing body's keys.
DATA_KEYS: Final = frozenset({"new_world", "cards"})

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

#: The derivation body's keys. ``derivation`` is tier 3.
DERIVATION_KEYS: Final = frozenset({"id", "rule_id", "derivation"})


@runtime_checkable
class AdviceSource(Protocol):
    """Whatever turns one world and one registry into resolved advice.

    Returns None when the advice stores could not be read - the endpoint turns
    that into a 503 rather than an empty listing that would read as "no advice".
    """

    def advice(self, world: WorldModel, registry: Registry) -> Advice | None:
        """Run the advisor over one world, or None when a store is unreadable."""
        ...


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


def _resolve(
    endpoint: str,
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
) -> Advice | contract.Response:
    """Fetch the advice, or the refusal that stands in for it.

    Args:
        endpoint: The template the refusal names.
        worlds: The world provider.
        registries: The registry provider.
        source: The advice source.

    Returns:
        The advice, or a 503 naming what was missing.
    """
    resolved = _resolve_in_world(endpoint, worlds, registries, source)
    if isinstance(resolved, contract.Response):
        return resolved
    return resolved[1]


def _resolve_in_world(
    endpoint: str,
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
) -> tuple[WorldModel, Advice] | contract.Response:
    """Fetch the world and its advice together, or the refusal for either.

    The state route needs the SAME world the advice was resolved over, so the
    record lands in the ledger of the world whose card was checked rather than
    of whatever a second provider read would hand back.

    Args:
        endpoint: The template the refusal names.
        worlds: The world provider.
        registries: The registry provider.
        source: The advice source.

    Returns:
        (world, advice), or a 503 naming what was missing.
    """
    model = worlds.world()
    if model is None:
        return contract.unavailable(endpoint, contract.REASON_NO_SAVE)
    registry = registries.registry()
    if registry is None:
        return contract.unavailable(endpoint, contract.REASON_NO_GAME_INSTALL)
    found = source.advice(model, registry)
    if found is None:
        return contract.unavailable(endpoint, contract.REASON_ADVICE_STORE_UNREADABLE)
    return model, found


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


def _state_request(query: Mapping[str, str]) -> tuple[str, str, int | None] | contract.Response:
    """Validate a state request's parameters before any world is read.

    Args:
        query: The path capture and the query parameters.

    Returns:
        (card id, kind, until), or the 400 that refuses the request. No 400
        names the value it refused.
    """
    allowed = (ID_PARAMETER, STATE_PARAMETER, UNTIL_PARAMETER)
    if any(name not in allowed for name in query):
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
    card_id = query.get(ID_PARAMETER)
    kind = query.get(STATE_PARAMETER)
    if card_id is None or kind is None:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_MISSING_PARAMETER)
    if kind not in RECORDABLE_STATES:
        return contract.bad_request(STATE_ENDPOINT, contract.REASON_INVALID_PARAMETER)
    until = _until_for(kind, query.get(UNTIL_PARAMETER))
    if isinstance(until, contract.Response):
        return until
    return card_id, kind, until


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
) -> contract.Handler:
    """Bind the providers and return the listing handler.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor and reads the stores.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request. This endpoint accepts no parameter."""
        if query:
            return contract.bad_request(ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
        found = _resolve(ENDPOINT, worlds, registries, source)
        if isinstance(found, contract.Response):
            return found
        return contract.ok(
            ENDPOINT,
            {
                "new_world": found.new_world,
                "cards": [_card(advised) for advised in found.cards],
            },
        )

    return handle


def make_derivation_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
) -> contract.Handler:
    """Bind the providers and return the derivation handler.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor and reads the stores.

    Returns:
        The handler.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request. Takes exactly the ``id`` path capture."""
        if any(name != ID_PARAMETER for name in query):
            return contract.bad_request(DERIVATION_ENDPOINT, contract.REASON_UNKNOWN_PARAMETER)
        wanted = query.get(ID_PARAMETER)
        if wanted is None:
            return contract.bad_request(DERIVATION_ENDPOINT, contract.REASON_MISSING_PARAMETER)
        found = _resolve(DERIVATION_ENDPOINT, worlds, registries, source)
        if isinstance(found, contract.Response):
            return found
        for advised in found.cards:
            card = advised.card
            if card.id == wanted:
                return contract.ok(
                    DERIVATION_ENDPOINT,
                    {"id": card.id, "rule_id": card.rule_id, "derivation": card.tier3},
                )
        return contract.bad_request(DERIVATION_ENDPOINT, contract.REASON_INVALID_PARAMETER)

    return handle


def make_state_handler(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceStore,
) -> contract.Handler:
    """Bind the providers and return the state-recording handler (CS-1269).

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor, reads the stores and records a state.

    Returns:
        The handler. It is reached only through a request the server admitted
        past its same-origin refusal.
    """

    def handle(query: Mapping[str, str]) -> contract.Response:
        """Answer one request: the ``id`` capture, ``state`` and maybe ``until``."""
        asked = _state_request(query)
        if isinstance(asked, contract.Response):
            return asked
        wanted, kind, until = asked
        resolved = _resolve_in_world(STATE_ENDPOINT, worlds, registries, source)
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
) -> tuple[contract.Route, ...]:
    """Publish the listing, derivation and state routes, with the providers bound in.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor, reads the stores and records a state.

    Returns:
        The listing route, the derivation route, then the state route.
    """
    return (
        contract.Route(
            method=METHOD_GET,
            template=ENDPOINT,
            handler=make_handler(worlds, registries, source),
        ),
        contract.Route(
            method=METHOD_GET,
            template=DERIVATION_ENDPOINT,
            handler=make_derivation_handler(worlds, registries, source),
        ),
        contract.Route(
            method=METHOD_POST,
            template=STATE_ENDPOINT,
            handler=make_state_handler(worlds, registries, source),
            mutates=True,
        ),
    )
