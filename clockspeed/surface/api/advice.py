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

THE STATE ROUTE IS NOT HERE. ``/api/advice/<id>/state`` mutates the ledger and
stays in ``clockspeed/surface/api/pending.py`` until CS-1269 lands.
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
    "METHOD_GET",
    "AdviceSource",
    "make_derivation_handler",
    "make_handler",
    "routes",
]

#: The card listing, tiers 1 and 2.
ENDPOINT: Final = "/api/advice"

#: One card's full derivation, tier 3.
DERIVATION_ENDPOINT: Final = "/api/advice/<id>/derivation"

#: Both routes are reads.
METHOD_GET: Final = "GET"

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
    model = worlds.world()
    if model is None:
        return contract.unavailable(endpoint, contract.REASON_NO_SAVE)
    registry = registries.registry()
    if registry is None:
        return contract.unavailable(endpoint, contract.REASON_NO_GAME_INSTALL)
    found = source.advice(model, registry)
    if found is None:
        return contract.unavailable(endpoint, contract.REASON_ADVICE_STORE_UNREADABLE)
    return found


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


def routes(
    worlds: contract.WorldProvider[WorldModel],
    registries: contract.RegistryProvider[Registry],
    source: AdviceSource,
) -> tuple[contract.Route, ...]:
    """Publish the listing and derivation routes, with the providers bound in.

    Args:
        worlds: Whatever hands over the current world, or says there is not one.
        registries: Whatever hands over the registry, or says there is not one.
        source: Whatever runs the advisor and reads the stores.

    Returns:
        The listing route, then the derivation route.
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
    )
