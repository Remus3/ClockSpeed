"""The frozen JSON response envelope every endpoint in this package returns.

Owns (BOOTSTRAP.md section 7.1): the wire shape of an API response - the status
vocabulary, the response constructors, the reason-to-detail table, the byte
encoder, the exact-rational spelling and the solver-refusal routing - plus the
two provider protocols an endpoint consumes its inputs through.

WHY THE PROTOCOLS LIVE HERE AND NOT IN THE SERVER MODULE. An endpoint needs to
name the shape of whatever hands it a world or a registry. If that name lived in
the server, every endpoint would import the server and the server would import
every endpoint - a cycle, and a seam that makes one endpoint untestable without
standing up an HTTPS listener. Naming the shapes here inverts the dependency:
the server depends on the endpoints, the endpoints depend on this module, and
this module depends on the standard library alone.

THIS MODULE OPENS NO FILE AND NAMES NO LAYER BELOW ITS NEIGHBOUR. The package
docstring forbids the first outright - "an endpoint that reaches for the
filesystem has reached past two neighbours at once". The second is why
:class:`WorldProvider` is GENERIC rather than annotated with the save layer's
world model: ``clockspeed/surface/__init__.py`` enumerates what sits below this
layer - advisor, audit, progress, solve - and the save layer is not among them,
so importing a save-layer type here would reach past three neighbours to spell
one annotation. The endpoint that actually holds a world parameterises the
protocol at its own use site, where naming the model is that module's business.

THE 501/503 SPLIT IS LOAD-BEARING AND MUST NOT COLLAPSE. "Pillar 3 has not been
written" and "there is no game installed on this machine, so there is no
registry" are different truths with different remedies, and an envelope that
renders them identically teaches an operator to ignore both. 501 says the layer
beneath does not exist yet and is REQUIRED to name the open item that would
build it; 503 says the layer exists and its input is absent here.

A 501 REFUSAL CANNOT OUTLIVE ITS REASON. ``blocked_by`` is validated twice - the
``CS-nnn`` or ``CS-nnnn`` form, and membership in :data:`OPEN_BLOCKERS`, the closed set this
repository authored - and ``tests/surface/test_contract.py`` pins that set to
the OPEN item lines of ``ROADMAP.md``. When the named item closes and leaves the
roadmap, that arm goes red, so an honest refusal has to be revisited rather than
quietly outliving the work it points at. THE SET IS GRADED IN BOTH DIRECTIONS: a
second arm asks the published routes which items they actually name, so a member
no endpoint cites is a finding rather than a silence, and the vocabulary cannot
declare a blocking this package does not perform. THE MEMBERSHIP CHECK IS A
CLOSED VOCABULARY AND NOT A FILE READ, because a runtime read of the roadmap
would be exactly the filesystem reach the package docstring forbids.

``detail`` IS LOOKED UP, NEVER BUILT. Every refusal line comes out of
:data:`REASONS` whole, keyed by a closed-vocabulary reason code. That is the
idiom ``clockspeed/save/world.py`` and ``clockspeed/data/locate.py`` already
state for their own warning types - "one fixed line naming the consequence,
never built from content" - and it is what structurally prevents a world name, a
save path or an account directory reaching an error body. The module holds no
f-string, no ``str.format`` call and no percent-formatting ANYWHERE, so there is
no interpolation site for such a value to land in; the test module asserts that
on the AST rather than trusting this paragraph.

THE ENDPOINT FIELD IS A ROUTE TEMPLATE AND NEVER A REQUEST PATH. Every value
that reaches it is checked against :data:`ENDPOINT_PATTERN`, which admits the
lowercase ``/api/...`` templates this repository authors and refuses a query
string, a fragment, a percent escape, an uppercase segment and a drive letter -
the shapes a raw request path takes and a template cannot. A 404 has no template
at all, so it renders :data:`ENDPOINT_UNROUTED` rather than reflecting what was
asked for.

THE WIRE BYTES ARE DETERMINISTIC AND 7-BIT. ``sort_keys`` plus fixed separators
make two encodes of one payload byte-identical, which is this project's
determinism property (CLAUDE.md section 1) applied at the surface.
``ensure_ascii`` is load-bearing rather than cosmetic: a modded class path can
carry a byte above 0x7E, and escaping it keeps the wire inside non-negotiable
4's character set. A float is REFUSED outright, because a bare JSON number is
read by a browser as an IEEE double and non-negotiable 6 bans exactly that from
the answer path - an exact ratio goes out through :func:`rational` instead.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# This module is the narrowest point of that seam: it is the one thing every
# endpoint imports, so anything it reaches for, every endpoint reaches for. It
# imports the standard library and nothing else, deliberately, and the test
# module asserts that on the import statements rather than on this comment.

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Final, Protocol, runtime_checkable

__all__ = [
    "BLOCKER_MALFORMED",
    "BLOCKER_NOT_OPEN",
    "BLOCKER_PATTERN",
    "ENDPOINT_PATTERN",
    "ENDPOINT_UNROUTED",
    "ENDPOINT_UNSPELLABLE",
    "FLOAT_ON_THE_WIRE",
    "HTTP_BAD_REQUEST",
    "HTTP_METHOD_NOT_ALLOWED",
    "HTTP_NOT_FOUND",
    "HTTP_NOT_IMPLEMENTED",
    "HTTP_OK",
    "HTTP_UNAVAILABLE",
    "MAX_ASCII_BYTE",
    "OPEN_BLOCKERS",
    "PAYLOAD_KEYS_OK",
    "PAYLOAD_KEYS_REFUSAL",
    "PROBLEM_BLOCKED_BY_ABSENT",
    "PROBLEM_BLOCKED_BY_PRESENT",
    "PROBLEM_CODES",
    "PROBLEM_DETAIL_MISMATCH",
    "PROBLEM_ENDPOINT_UNSPELLABLE",
    "PROBLEM_KEYS_UNEXPECTED",
    "PROBLEM_REASON_UNKNOWN",
    "PROBLEM_STATUS_MISMATCH",
    "PROBLEM_UNKNOWN_CODE",
    "REASONS",
    "REASON_ADVICE_STORE_UNREADABLE",
    "REASON_BACKEND_UNAVAILABLE",
    "REASON_BYPRODUCT_POLICY_REQUIRED",
    "REASON_CHAIN_INFEASIBLE",
    "REASON_CHAIN_UNDERDETERMINED",
    "REASON_CHAIN_UNSOLVABLE",
    "REASON_INVALID_PARAMETER",
    "REASON_MALFORMED_QUERY",
    "REASON_METHOD_NOT_ALLOWED",
    "REASON_MISSING_PARAMETER",
    "REASON_NOT_IMPLEMENTED",
    "REASON_NO_FEASIBLE_SELECTION",
    "REASON_NO_GAME_INSTALL",
    "REASON_NO_SAVE",
    "REASON_NO_SUCH_ROUTE",
    "REASON_OBJECTIVE_UNDEFINED",
    "REASON_OPTIMIZE_REFUSED",
    "REASON_POWER_NOT_COMPARABLE",
    "REASON_RATIO_REFUSED",
    "REASON_SAVE_UNREADABLE",
    "REASON_SEARCH_SPACE_TOO_LARGE",
    "REASON_SUPPLY_UNBOUNDED",
    "REASON_UNKNOWN_PARAMETER",
    "SOLVER_REFUSALS",
    "STATUSES",
    "STATUS_ERROR",
    "STATUS_FOR_CODE",
    "STATUS_NOT_IMPLEMENTED",
    "STATUS_OK",
    "STATUS_UNAVAILABLE",
    "UNPUBLISHED_REASON",
    "Handler",
    "RegistryProvider",
    "Response",
    "Route",
    "WorldProvider",
    "bad_request",
    "contract_problems",
    "encode",
    "method_not_allowed",
    "no_such_route",
    "not_implemented",
    "ok",
    "rational",
    "unavailable",
]


# ---------------------------------------------------------------------------
# The status vocabulary
# ---------------------------------------------------------------------------

#: A real answer, computed below this layer and serialized here.
STATUS_OK: Final = "ok"

#: The layer beneath has not been built yet. Always names its blocking item.
STATUS_NOT_IMPLEMENTED: Final = "not_implemented"

#: The layer exists; its input is absent on THIS machine. Nothing to build.
STATUS_UNAVAILABLE: Final = "unavailable"

#: The request did not satisfy the contract, in any of the ways it can fail.
STATUS_ERROR: Final = "error"

#: The whole vocabulary. There is deliberately no fifth entry: a body status a
#: client has never seen is one it will render as a crash.
STATUSES: Final = (STATUS_OK, STATUS_NOT_IMPLEMENTED, STATUS_UNAVAILABLE, STATUS_ERROR)

HTTP_OK: Final = 200
HTTP_BAD_REQUEST: Final = 400
HTTP_NOT_FOUND: Final = 404
HTTP_METHOD_NOT_ALLOWED: Final = 405
HTTP_NOT_IMPLEMENTED: Final = 501
HTTP_UNAVAILABLE: Final = 503

#: The one binding between the transport code and the body word. A response
#: whose code and body disagree is a response two readers describe differently -
#: a proxy reads the code, a dashboard reads the body - so the disagreement is a
#: contract violation rather than a cosmetic one. Three codes share
#: :data:`STATUS_ERROR` on purpose: 400, 404 and 405 are all "the request did
#: not satisfy the contract", and the REASON is what separates them.
STATUS_FOR_CODE: Final[Mapping[int, str]] = MappingProxyType(
    {
        HTTP_OK: STATUS_OK,
        HTTP_BAD_REQUEST: STATUS_ERROR,
        HTTP_NOT_FOUND: STATUS_ERROR,
        HTTP_METHOD_NOT_ALLOWED: STATUS_ERROR,
        HTTP_NOT_IMPLEMENTED: STATUS_NOT_IMPLEMENTED,
        HTTP_UNAVAILABLE: STATUS_UNAVAILABLE,
    }
)


# ---------------------------------------------------------------------------
# The reason vocabulary and its fixed detail lines
# ---------------------------------------------------------------------------

REASON_NOT_IMPLEMENTED: Final = "not_implemented"

REASON_NO_SUCH_ROUTE: Final = "no_such_route"
REASON_METHOD_NOT_ALLOWED: Final = "method_not_allowed"
REASON_MALFORMED_QUERY: Final = "malformed_query"
REASON_MISSING_PARAMETER: Final = "missing_parameter"
REASON_UNKNOWN_PARAMETER: Final = "unknown_parameter"
REASON_INVALID_PARAMETER: Final = "invalid_parameter"

REASON_NO_GAME_INSTALL: Final = "no_game_install"
REASON_NO_SAVE: Final = "no_save"
REASON_SAVE_UNREADABLE: Final = "save_unreadable"
REASON_BACKEND_UNAVAILABLE: Final = "backend_unavailable"
REASON_ADVICE_STORE_UNREADABLE: Final = "advice_store_unreadable"

REASON_CHAIN_UNSOLVABLE: Final = "chain_unsolvable"
REASON_CHAIN_UNDERDETERMINED: Final = "chain_underdetermined"
REASON_CHAIN_INFEASIBLE: Final = "chain_infeasible"
REASON_BYPRODUCT_POLICY_REQUIRED: Final = "byproduct_policy_required"
REASON_SUPPLY_UNBOUNDED: Final = "supply_unbounded"
REASON_RATIO_REFUSED: Final = "ratio_refused"
REASON_NO_FEASIBLE_SELECTION: Final = "no_feasible_selection"
REASON_SEARCH_SPACE_TOO_LARGE: Final = "search_space_too_large"
REASON_OBJECTIVE_UNDEFINED: Final = "objective_undefined"
REASON_POWER_NOT_COMPARABLE: Final = "power_not_comparable"
REASON_OPTIMIZE_REFUSED: Final = "optimize_refused"

#: Every refusal this envelope can carry: the reason code, the body status it
#: belongs to, and the ONE FIXED LINE that renders as ``detail``.
#:
#: THE STATUS TRAVELS WITH THE LINE RATHER THAN IN A SECOND TABLE, so a reason
#: cannot be attached to the wrong code. ``bad_request`` refusing
#: ``no_game_install`` would render a machine's missing install as the caller's
#: mistake, and a second table keyed the same way is a fact restated in two
#: places, which CLAUDE.md section 4 names as a fact that will drift.
#:
#: EVERY LINE IS AUTHORED HERE, IN THIS REPOSITORY, AND HOLDS NO SUBSTITUTION
#: POINT. That is the whole anti-echo mechanism: a detail built from content
#: would publish whatever it was built from, and a save path, a world name and a
#: platform account id are all one interpolation away from a caller's hand.
REASONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        REASON_NOT_IMPLEMENTED: (
            STATUS_NOT_IMPLEMENTED,
            "The layer that computes this answer has not been built yet.",
        ),
        REASON_NO_SUCH_ROUTE: (
            STATUS_ERROR,
            "No route on this server matches the request.",
        ),
        REASON_METHOD_NOT_ALLOWED: (
            STATUS_ERROR,
            "The route exists but does not accept the request method.",
        ),
        REASON_MALFORMED_QUERY: (
            STATUS_ERROR,
            "The request query string did not parse.",
        ),
        REASON_MISSING_PARAMETER: (
            STATUS_ERROR,
            "The request omitted a parameter this endpoint requires.",
        ),
        REASON_UNKNOWN_PARAMETER: (
            STATUS_ERROR,
            "The request named a parameter this endpoint does not accept.",
        ),
        REASON_INVALID_PARAMETER: (
            STATUS_ERROR,
            "A request parameter carried a value this endpoint does not accept.",
        ),
        REASON_NO_GAME_INSTALL: (
            STATUS_UNAVAILABLE,
            "No game installation was found on this machine, so there is no registry to read.",
        ),
        REASON_NO_SAVE: (
            STATUS_UNAVAILABLE,
            "No save file was found on this machine, so there is no world to answer about.",
        ),
        REASON_SAVE_UNREADABLE: (
            STATUS_UNAVAILABLE,
            "The save that was found could not be read, so there is no world to answer about.",
        ),
        REASON_BACKEND_UNAVAILABLE: (
            STATUS_UNAVAILABLE,
            "The optimizer backend that was named is not present in this build.",
        ),
        REASON_ADVICE_STORE_UNREADABLE: (
            STATUS_UNAVAILABLE,
            "The advice ledger or the rule mute store could not be read, so no advice resolved.",
        ),
        REASON_CHAIN_UNSOLVABLE: (
            STATUS_ERROR,
            "The item balances contradict each other, so no plan exists at any scale.",
        ),
        REASON_CHAIN_UNDERDETERMINED: (
            STATUS_ERROR,
            "The request admits infinitely many solutions, so it does not name a plan.",
        ),
        REASON_CHAIN_INFEASIBLE: (
            STATUS_ERROR,
            "The only solution would require running a recipe backwards.",
        ),
        REASON_BYPRODUCT_POLICY_REQUIRED: (
            STATUS_ERROR,
            "The request states no byproduct policy, and this chain cannot be solved without one.",
        ),
        REASON_SUPPLY_UNBOUNDED: (
            STATUS_ERROR,
            "No supplied item limits the target, so every rate satisfies the request.",
        ),
        REASON_RATIO_REFUSED: (
            STATUS_ERROR,
            "The ratio solve refused this request for a reason the envelope does not name apart.",
        ),
        REASON_NO_FEASIBLE_SELECTION: (
            STATUS_ERROR,
            "No selection of the usable recipes yields a plan at all.",
        ),
        REASON_SEARCH_SPACE_TOO_LARGE: (
            STATUS_ERROR,
            "A complete search of this request would take longer than anyone will wait.",
        ),
        REASON_OBJECTIVE_UNDEFINED: (
            STATUS_ERROR,
            "The stated objective does not name a direction to minimize in.",
        ),
        REASON_POWER_NOT_COMPARABLE: (
            STATUS_ERROR,
            "This plan's power draw has no exact value, so plans cannot be ranked by it.",
        ),
        REASON_OPTIMIZE_REFUSED: (
            STATUS_ERROR,
            "The optimizer refused this request for a reason the envelope does not name apart.",
        ),
    }
)


# ---------------------------------------------------------------------------
# Solver refusals, keyed by CLASS NAME
# ---------------------------------------------------------------------------

#: Every exception class ``clockspeed.solve.ratio`` and
#: ``clockspeed.solve.optimize`` export, mapped to the body status and reason the
#: surface renders it as.
#:
#: KEYED ON THE CLASS NAME AND NEVER ON ``str(exc)``, WHICH IS BOTH RULES AT
#: ONCE. It is the anti-computation rule, because the surface decides nothing
#: about a refusal it did not raise - it transcribes a verdict the solver already
#: reached. And it is the anti-echo rule, because several of those exceptions
#: interpolate a game-content key into their message, so a surface that matched
#: on message text would have to hold that text to compare it.
#:
#: A STRING KEY RATHER THAN THE CLASS OBJECT, so this module keeps its promise to
#: import nothing from another layer. The lookup a caller performs is
#: ``SOLVER_REFUSALS[type(exc).__name__]``, which needs no import at all.
#:
#: THE TWO BASE CLASSES ARE HERE ON PURPOSE. They are exported, so they can be
#: raised, and a base class absent from this table is a refusal that falls
#: through the surface as an unhandled error - the silent-wrongness
#: non-negotiable 7 forbids. Their lines say plainly that the envelope does not
#: name the case apart, which is true and is better than a guess.
SOLVER_REFUSALS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "ByproductPolicyRequired": (STATUS_ERROR, REASON_BYPRODUCT_POLICY_REQUIRED),
        "InfeasibleChain": (STATUS_ERROR, REASON_CHAIN_INFEASIBLE),
        "NoFeasibleSelectionError": (STATUS_ERROR, REASON_NO_FEASIBLE_SELECTION),
        "ObjectiveUndefinedError": (STATUS_ERROR, REASON_OBJECTIVE_UNDEFINED),
        "OptimizeError": (STATUS_ERROR, REASON_OPTIMIZE_REFUSED),
        "PowerNotComparableError": (STATUS_ERROR, REASON_POWER_NOT_COMPARABLE),
        "RatioError": (STATUS_ERROR, REASON_RATIO_REFUSED),
        "SearchSpaceTooLargeError": (STATUS_ERROR, REASON_SEARCH_SPACE_TOO_LARGE),
        "UnboundedSupply": (STATUS_ERROR, REASON_SUPPLY_UNBOUNDED),
        "UnderdeterminedChain": (STATUS_ERROR, REASON_CHAIN_UNDERDETERMINED),
        "UnknownBackendError": (STATUS_UNAVAILABLE, REASON_BACKEND_UNAVAILABLE),
        "UnsolvableChain": (STATUS_ERROR, REASON_CHAIN_UNSOLVABLE),
    }
)


# ---------------------------------------------------------------------------
# What a 501 is allowed to blame
# ---------------------------------------------------------------------------

#: The item-id form: ``CS-`` and three digits, or four with no leading zero -
#: the spelling ``docs/LEDGER.md`` uses, zero-padded below 1000. FOUR DIGITS
#: SINCE CS-1046 named it: the three-digit form could not name any item at
#: CS-1000 or above, and every item filed since is one. Applied with
#: ``fullmatch`` rather than with ``^...$`` and ``match``: ``$`` also matches
#: immediately before a trailing newline, so the anchored pattern accepts
#: ``"CS-400\n"`` and ``fullmatch`` does not.
BLOCKER_PATTERN: Final = re.compile(r"CS-(?:\d{3}|[1-9]\d{3})")

#: The only items a 501 may name. A CLOSED VOCABULARY AUTHORED HERE, not a
#: roadmap read: this package opens no file, so the durability arms live in
#: ``tests/surface/test_contract.py``, and there are TWO of them because one
#: direction is not a grade. The forward arm,
#: ``tests/surface/test_contract.py::test_every_open_blocker_is_an_open_roadmap_item_line``,
#: asserts every member is still an OPEN item line in ``ROADMAP.md``, so the
#: refusal and the reason for it fall together. The converse arm,
#: ``tests/surface/test_contract.py::test_every_open_blocker_is_cited_by_a_published_route``,
#: asserts every member is NAMED by some published route's refusal, measured by
#: calling the handlers. The forward arm ALONE was green over a member that no
#: endpoint anywhere cited.
#:
#:   CS-1046  ``/api/audit`` and ``/api/plan``: the item that publishes their
#:            bodies.
#:   CS-1269  ``/api/advice/<id>/state``: recording a card state through the
#:            ledger, behind a cross-origin refusal this server does not yet
#:            make.
#:
#: Both are named through ``clockspeed/surface/api/pending.py``, which
#: holds the only ``not_implemented`` call site in this package. CS-500 LEFT
#: THIS SET WHEN IT CLOSED, and CS-1270 left it when the advisor gained
#: ``advise_world`` and both advice reads moved into the route table.
#:
#: THE STANDARD FOR MEMBERSHIP IS THE ONE THIS MODULE'S DOCSTRING STATES - "the
#: layer beneath does not exist yet" - and it is NOT "the layer beneath is
#: unfinished". Those are different tests, and the looser one would take
#: ``/api/health`` with it, since health reports save-layer state and does not
#: refuse. A layer that exists and is incomplete ANSWERS, and says what it could
#: not read in a flagged warning inside the body - which is what
#: ``clockspeed/surface/api/world.py`` already renders.
#:
#: CS-400 IS DELIBERATELY ABSENT. Re-adding it means re-deciding ADR 0012
#: (``docs/adr/0012-dashboard-refusal-vocabulary-and-wire-form.md``) rather than
#: editing this literal. The phase 4 save layer ships and parses a real world;
#: CS-400 closed 2026-10-04 on building inventory, clock speed was already
#: decoded, and connection state is a BACKLOG line. ``/api/world`` serves
#: enumeration only, so it answers 200 or 503 and never 501. While it sat
#: here it was a member no route named, under a comment that described a
#: routing this package does not perform.
OPEN_BLOCKERS: Final = frozenset({"CS-1046", "CS-1269"})


# ---------------------------------------------------------------------------
# What an endpoint field may spell
# ---------------------------------------------------------------------------

#: A route TEMPLATE this repository authors: lowercase ``/api`` segments, with
#: ``<name>`` for a path parameter. It refuses a query string, a fragment, a
#: percent escape, an uppercase segment, a dot segment and a drive letter -
#: every shape a raw request path can take and a template cannot. Applied with
#: ``fullmatch``.
ENDPOINT_PATTERN: Final = re.compile(r"/api(?:/(?:<[a-z_]+>|[a-z][a-z0-9_-]*))+")

#: What a 404 renders instead of the path that was asked for. A LITERAL, because
#: the alternative is reflecting caller-chosen text into a response body, and on
#: this machine that text can be a save path or an account directory.
ENDPOINT_UNROUTED: Final = "/api/<unrouted>"


# ---------------------------------------------------------------------------
# Fixed refusal lines for the module's own argument checks
# ---------------------------------------------------------------------------

#: The highest byte the wire admits (non-negotiable 4).
MAX_ASCII_BYTE: Final = 0x7E

BLOCKER_MALFORMED: Final = (
    "a 501 blocked_by must be spelled CS- and three digits, or four with no leading zero"
)
BLOCKER_NOT_OPEN: Final = "a 501 blocked_by must name an item this surface still has open"
ENDPOINT_UNSPELLABLE: Final = "an endpoint must be a route template this repository authored"
UNPUBLISHED_REASON: Final = "a refusal must name a reason from the published vocabulary"
FLOAT_ON_THE_WIRE: Final = "a response payload carried a float; the wire admits only exact ratios"


# ---------------------------------------------------------------------------
# Payload shapes
# ---------------------------------------------------------------------------

#: Exactly the keys a success body carries.
PAYLOAD_KEYS_OK: Final = frozenset({"status", "endpoint", "data"})

#: Exactly the keys EVERY non-success body carries, whatever its code. One shape
#: for all four refusal codes, so a client writes one error path rather than
#: four. ``blocked_by`` is present and null on the three that cannot have one,
#: rather than absent: an absent key and a null key are distinguishable in
#: JavaScript and a client should not have to know which this is.
PAYLOAD_KEYS_REFUSAL: Final = frozenset({"status", "endpoint", "reason", "detail", "blocked_by"})


# ---------------------------------------------------------------------------
# Contract violations
# ---------------------------------------------------------------------------

PROBLEM_UNKNOWN_CODE: Final = "http-code-not-admitted"
PROBLEM_STATUS_MISMATCH: Final = "status-disagrees-with-http-code"
PROBLEM_KEYS_UNEXPECTED: Final = "payload-keys-are-not-the-shape-for-this-status"
PROBLEM_ENDPOINT_UNSPELLABLE: Final = "endpoint-is-not-a-route-template"
PROBLEM_REASON_UNKNOWN: Final = "reason-is-outside-the-published-vocabulary"
PROBLEM_DETAIL_MISMATCH: Final = "detail-is-not-the-reason-s-own-line"
PROBLEM_BLOCKED_BY_ABSENT: Final = "a-501-names-no-open-blocking-item"
PROBLEM_BLOCKED_BY_PRESENT: Final = "a-non-501-names-a-blocking-item"

#: Every problem :func:`contract_problems` can report. Published so a caller can
#: assert its own handling is exhaustive, and so the count can be graded.
PROBLEM_CODES: Final = (
    PROBLEM_UNKNOWN_CODE,
    PROBLEM_STATUS_MISMATCH,
    PROBLEM_KEYS_UNEXPECTED,
    PROBLEM_ENDPOINT_UNSPELLABLE,
    PROBLEM_REASON_UNKNOWN,
    PROBLEM_DETAIL_MISMATCH,
    PROBLEM_BLOCKED_BY_ABSENT,
    PROBLEM_BLOCKED_BY_PRESENT,
)


# ---------------------------------------------------------------------------
# The types every endpoint is written against
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Response:
    """One serialized answer: the transport code and the body that goes with it.

    NO ``Path`` AND NO ``bytes`` FIELD, WHICH IS A DECISION RATHER THAN AN
    OMISSION. ``tests/repr_rendering_guard.py`` grades a shipped dataclass
    holding either one, because a generated ``__repr__`` renders a ``Path`` in
    full - account directory included - and a ``bytes`` field verbatim. Keeping
    both out of the type means the channel cannot open here at all, which is
    stronger than a hand-written ``__repr__`` that a later field can outgrow.
    The encoded bytes are produced by :func:`encode` on demand and are never
    held.

    Attributes:
        http_status: The transport code, one of :data:`STATUS_FOR_CODE`'s keys.
        payload: The body, exactly as it will be encoded. A plain mapping rather
            than a ``MappingProxyType`` because ``json.dumps`` refuses a
            mappingproxy outright, and an envelope whose own encoder cannot read
            it is worse than one a caller could in principle mutate -
            :func:`contract_problems` is what catches the mutation. WITHHELD
            FROM THE REPR (CS-1024): it is the serialised world answer, and a
            generated repr rendered it in full - every save-derived string in
            the body included.
    """

    http_status: int
    payload: Mapping[str, object] = field(repr=False)


#: What the server calls once a route matches. The parsed query parameters go
#: in, a :class:`Response` comes out. Providers are NOT parameters here: the
#: server binds them into the handler before registering it, so an endpoint
#: module never imports the server and never learns how a world was obtained.
type Handler = Callable[[Mapping[str, str]], Response]


@dataclass(frozen=True)
class Route:
    """One method-and-template pair, and what answers it.

    Attributes:
        method: The HTTP method, uppercase.
        template: The route template, matching :data:`ENDPOINT_PATTERN`.
        handler: What answers a request that matches both. WITHHELD FROM THE
            REPR (CS-1024): a handler is a closure or a partial over whatever
            the server bound into it, and a partial renders its bound
            arguments in full.
    """

    method: str
    template: str
    handler: Handler = field(repr=False)


@runtime_checkable
class WorldProvider[WorldT](Protocol):
    """Whatever hands an endpoint the current world, or says there is not one.

    GENERIC RATHER THAN ANNOTATED WITH THE SAVE LAYER'S MODEL, and the module
    docstring records why: naming that type here would make this module import
    three layers down. The endpoint that holds a world writes
    ``WorldProvider[WorldModel]`` at its own use site.

    ``None`` IS THE 503 CASE AND IS NOT AN ERROR. "There is no save on this
    machine" is a true answer about a working system, so it is spelled as a
    value rather than as an exception.
    """

    def world(self) -> WorldT | None:
        """The current world, or None when this machine has no save to read.

        Returns:
            The world model, or None.
        """
        ...


@runtime_checkable
class RegistryProvider[RegistryT](Protocol):
    """Whatever hands an endpoint the normalized registry, or says there is not one.

    Generic for the same reason :class:`WorldProvider` is, and ``None`` means
    the same thing: no game installation was found on this machine, which is a
    503 rather than a failure.
    """

    def registry(self) -> RegistryT | None:
        """The normalized registry, or None when this machine has no install.

        Returns:
            The registry, or None.
        """
        ...


# ---------------------------------------------------------------------------
# Argument checks. Each raises a FIXED line and never echoes what it rejected.
# ---------------------------------------------------------------------------


def _checked_endpoint(endpoint: str) -> str:
    """Return the endpoint, or refuse a value that is not a route template.

    Args:
        endpoint: The candidate.

    Returns:
        The endpoint, unchanged.

    Raises:
        ValueError: When it does not match :data:`ENDPOINT_PATTERN`. The message
            is a fixed line and does NOT quote the value: quoting it would
            publish the very request path this check exists to keep out of a
            response body.
    """
    if ENDPOINT_PATTERN.fullmatch(endpoint) is None:
        raise ValueError(ENDPOINT_UNSPELLABLE)
    return endpoint


def _refusal(status: str, endpoint: str, reason: str, blocked_by: str | None) -> dict[str, object]:
    """Build the one body shape every non-success response carries.

    Args:
        status: The body status word.
        endpoint: The route template.
        reason: A key of :data:`REASONS`.
        blocked_by: The blocking item for a 501, None everywhere else.

    Returns:
        The payload.

    Raises:
        ValueError: When the reason is outside the vocabulary, or belongs to a
            different status than the one being built. The second half is what
            stops a machine-state refusal being rendered as the caller's
            mistake, or the other way round.
    """
    entry = REASONS.get(reason)
    if entry is None or entry[0] != status:
        raise ValueError(UNPUBLISHED_REASON)
    return {
        "status": status,
        "endpoint": _checked_endpoint(endpoint),
        "reason": reason,
        "detail": entry[1],
        "blocked_by": blocked_by,
    }


# ---------------------------------------------------------------------------
# The constructors
# ---------------------------------------------------------------------------


def ok(endpoint: str, data: Mapping[str, object]) -> Response:
    """A real answer, computed below this layer.

    Args:
        endpoint: The route template that produced it.
        data: The serialized model. Copied shallowly, so a caller mutating its
            own mapping afterwards does not alter a response already built.

    Returns:
        The 200 response.
    """
    return Response(
        http_status=HTTP_OK,
        payload={"status": STATUS_OK, "endpoint": _checked_endpoint(endpoint), "data": dict(data)},
    )


def not_implemented(endpoint: str, blocked_by: str) -> Response:
    """The layer beneath this endpoint has not been built yet.

    Args:
        endpoint: The route template.
        blocked_by: The open item that would build it, spelled ``CS-nnn``.

    Returns:
        The 501 response.

    Raises:
        ValueError: When ``blocked_by`` is malformed, or is well formed but
            names nothing this surface still has open. Two distinct fixed lines,
            so the two rejection paths stay tellable apart; neither quotes the
            value.
    """
    if BLOCKER_PATTERN.fullmatch(blocked_by) is None:
        raise ValueError(BLOCKER_MALFORMED)
    if blocked_by not in OPEN_BLOCKERS:
        raise ValueError(BLOCKER_NOT_OPEN)
    return Response(
        http_status=HTTP_NOT_IMPLEMENTED,
        payload=_refusal(STATUS_NOT_IMPLEMENTED, endpoint, REASON_NOT_IMPLEMENTED, blocked_by),
    )


def unavailable(endpoint: str, reason: str) -> Response:
    """The layer exists; its input is absent on this machine.

    Args:
        endpoint: The route template.
        reason: A :data:`REASONS` key whose status is :data:`STATUS_UNAVAILABLE`.

    Returns:
        The 503 response.

    Raises:
        ValueError: When the reason is unknown or belongs to another status.
    """
    return Response(
        http_status=HTTP_UNAVAILABLE,
        payload=_refusal(STATUS_UNAVAILABLE, endpoint, reason, None),
    )


def bad_request(endpoint: str, reason: str) -> Response:
    """The request did not satisfy the contract.

    Args:
        endpoint: The route template.
        reason: A :data:`REASONS` key whose status is :data:`STATUS_ERROR`.

    Returns:
        The 400 response.

    Raises:
        ValueError: When the reason is unknown or belongs to another status.
    """
    return Response(
        http_status=HTTP_BAD_REQUEST,
        payload=_refusal(STATUS_ERROR, endpoint, reason, None),
    )


def no_such_route() -> Response:
    """No route matches the request.

    TAKES NO ENDPOINT, DELIBERATELY. There is no template to name, and the only
    other candidate is the path that was asked for - which is caller-chosen text
    this layer must not reflect back.

    Returns:
        The 404 response.
    """
    return Response(
        http_status=HTTP_NOT_FOUND,
        payload=_refusal(STATUS_ERROR, ENDPOINT_UNROUTED, REASON_NO_SUCH_ROUTE, None),
    )


def method_not_allowed(endpoint: str) -> Response:
    """The route exists; the method does not.

    Args:
        endpoint: The route template that matched. Unlike a 404 there IS one,
            because the path resolved and only the method was wrong.

    Returns:
        The 405 response.
    """
    return Response(
        http_status=HTTP_METHOD_NOT_ALLOWED,
        payload=_refusal(STATUS_ERROR, endpoint, REASON_METHOD_NOT_ALLOWED, None),
    )


# ---------------------------------------------------------------------------
# The wire
# ---------------------------------------------------------------------------


def _carries_float(value: object) -> bool:
    """Whether a float sits anywhere inside a payload, at any depth.

    Keys are walked as well as values: a float key becomes a JSON string and the
    exactness is lost silently, which is the same defect wearing a disguise.

    Args:
        value: Any part of a payload.

    Returns:
        True when a float is reachable.
    """
    if isinstance(value, float):
        return True
    if isinstance(value, Mapping):
        return any(_carries_float(key) or _carries_float(item) for key, item in value.items())
    if isinstance(value, str | bytes | bytearray):
        return False
    if isinstance(value, Sequence):
        return any(_carries_float(item) for item in value)
    return False


def encode(payload: Mapping[str, object]) -> bytes:
    """Render a payload as the exact bytes that go on the wire.

    Every keyword is load-bearing. ``sort_keys`` and the fixed separators make
    two encodes of one payload byte-identical, which is this project's
    determinism property applied at the surface - two runs on the same inputs
    must not disagree, down to the byte. ``ensure_ascii`` escapes anything above
    0x7E, so a modded class path carrying a high byte still leaves as 7-bit
    (non-negotiable 4); the ``ascii`` codec on the result is what turns a broken
    promise into an exception instead of a silent widening.

    Args:
        payload: The body.

    Returns:
        The encoded bytes.

    Raises:
        ValueError: When the payload carries a float. A bare JSON number is read
            by a browser as an IEEE double, which is the float non-negotiable 6
            keeps out of the answer path; an exact ratio goes out through
            :func:`rational`. The message names the consequence and never the
            value.
    """
    if _carries_float(payload):
        raise ValueError(FLOAT_ON_THE_WIRE)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


def rational(value: Fraction) -> dict[str, int]:
    """Render an exact ratio as a numerator and a denominator.

    THIS FUNCTION TRANSCRIBES AND DOES NOT COMPUTE, and the test module asserts
    that on its AST: its body holds no ``ast.BinOp`` at all. A division here
    would produce the IEEE double this spelling exists to avoid, and a surface
    that divides has started computing, which the layer above forbids.

    Args:
        value: The exact ratio. Already in lowest terms - ``Fraction`` normalises
            on construction - so nothing is reduced here either.

    Returns:
        ``{"num": <numerator>, "den": <denominator>}``.
    """
    return {"num": value.numerator, "den": value.denominator}


# ---------------------------------------------------------------------------
# The checker
# ---------------------------------------------------------------------------


def contract_problems(response: Response) -> tuple[str, ...]:
    """Every way this response disagrees with the contract, in both directions.

    EXISTS BECAUSE THE CONSTRUCTORS ARE NOT THE ONLY WAY A RESPONSE IS BUILT.
    A payload is a plain mapping, so a later layer can edit one; and a test that
    only proves conforming responses pass is green when this checker is broken.
    Both halves are graded - a planted disagreement is asserted REJECTED.

    Args:
        response: The response to grade.

    Returns:
        The problem codes, from :data:`PROBLEM_CODES`. Empty when it conforms.
        CODES ONLY, NEVER A VALUE: this result reaches a log line and a failure
        report, so it is a closed vocabulary authored here for the same reason
        ``detail`` is.
    """
    expected_status = STATUS_FOR_CODE.get(response.http_status)
    if expected_status is None:
        return (PROBLEM_UNKNOWN_CODE,)

    payload = response.payload
    found: list[str] = []

    if payload.get("status") != expected_status:
        found.append(PROBLEM_STATUS_MISMATCH)

    endpoint = payload.get("endpoint")
    unspellable = not isinstance(endpoint, str) or ENDPOINT_PATTERN.fullmatch(endpoint) is None
    if unspellable:
        found.append(PROBLEM_ENDPOINT_UNSPELLABLE)

    shape = PAYLOAD_KEYS_OK if expected_status == STATUS_OK else PAYLOAD_KEYS_REFUSAL
    if frozenset(payload) != shape:
        found.append(PROBLEM_KEYS_UNEXPECTED)

    if expected_status == STATUS_OK:
        return tuple(found)

    reason = payload.get("reason")
    entry = REASONS.get(reason) if isinstance(reason, str) else None
    if entry is None or entry[0] != expected_status:
        found.append(PROBLEM_REASON_UNKNOWN)
    elif payload.get("detail") != entry[1]:
        found.append(PROBLEM_DETAIL_MISMATCH)

    blocked_by = payload.get("blocked_by")
    if expected_status == STATUS_NOT_IMPLEMENTED:
        named = isinstance(blocked_by, str) and blocked_by in OPEN_BLOCKERS
        if not named:
            found.append(PROBLEM_BLOCKED_BY_ABSENT)
    elif blocked_by is not None:
        found.append(PROBLEM_BLOCKED_BY_PRESENT)

    return tuple(found)
