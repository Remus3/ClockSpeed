"""CS-601 slice S0 - the frozen response envelope every endpoint returns.

What is covered, and the authority for each arm:

a. THE REFUSAL CANNOT OUTLIVE ITS REASON. ``not_implemented`` validates its
   ``blocked_by`` twice - the CS-nnn form, and membership in the closed set of
   blockers this repository authored - and a separate arm pins that set to the
   OPEN item lines of ``ROADMAP.md``. When the named item closes and leaves the
   roadmap, that arm goes red and the honest refusal has to be revisited
   instead of quietly outliving the work it pointed at.
b. THE WIRE BYTES ARE DETERMINISTIC AND 7-BIT. Two encodes of one payload are
   byte-identical (CLAUDE.md section 1, the determinism property applied at the
   surface) and no byte above 0x7E leaves the encoder even when the payload
   carries one (non-negotiable 4, and a mod class path is the live route for
   such a byte).
c. AN EXACT RATIO IS TRANSCRIBED, NEVER COMPUTED. ``rational`` renders a
   ``Fraction`` as a numerator and a denominator, and an AST arm asserts its
   body holds no ``ast.BinOp`` at all - non-negotiable 6, and ``surface/ never
   computes`` from ``clockspeed/surface/__init__.py``.
d. THE CODE AND THE BODY CANNOT DISAGREE, IN BOTH DIRECTIONS. Each planted
   disagreement is asserted REJECTED by the checker, because an arm proving
   only that conforming responses pass is green when the checker is broken.
e. ``SOLVER_REFUSALS`` IS EXHAUSTIVE over the exception classes the two solver
   modules export, so a solver error added tomorrow cannot fall through the
   surface silently (non-negotiable 7).
f. ``detail`` IS NEVER BUILT FROM CONTENT. The whole module is asserted to hold
   zero f-strings, zero ``.format`` calls and zero percent-formatting, which is
   the structural version of the promise: there is no formatting site anywhere
   in the module where a caller-supplied value could land in a detail line.
   ``clockspeed/save/world.py`` and ``clockspeed/data/locate.py`` state the same
   idiom in prose - "one fixed line naming the consequence, never built from
   content" - and this arm is that sentence made checkable.

Test-quality discipline (CONVENTIONS.md section 7.2). Every sweep below binds
its population size to a scalar and asserts the expected count BEFORE it
iterates: a sweep over an empty collection passes vacuously and proves nothing.
Every detector used to prove an absence is also run against a planted POSITIVE,
so "found nothing" is distinguishable from "looks for nothing".
"""

from __future__ import annotations

import ast
import inspect
import re
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from clockspeed.solve import optimize, ratio
from clockspeed.surface.api import contract

if TYPE_CHECKING:
    from collections.abc import Iterable

# ---------------------------------------------------------------------------
# Populations, each with the count its sweep asserts before iterating
# ---------------------------------------------------------------------------

#: Every exception class the two solver modules EXPORT. Derived from ``__all__``
#: plus a subclass test rather than from a name suffix: the slice brief named
#: the population as "every ``*Error`` name", and five of the twelve exported
#: exception classes - ``UnsolvableChain``, ``UnderdeterminedChain``,
#: ``InfeasibleChain``, ``ByproductPolicyRequired`` and ``UnboundedSupply`` -
#: carry no ``Error`` suffix at all. ``clockspeed/solve/ratio.py`` records a
#: coded N818 suppression saying that naming is deliberate. A suffix rule would
#: have graded SEVEN of twelve and reported itself exhaustive; the two module
#: base classes DO carry the suffix and are not among the five.
#:
#: The counts above were measured, and an earlier version of this comment
#: carried two wrong ones - "eight of the ten" over a list of seven, and "two
#: of twelve" for what a suffix rule grades. Both came from the slice brief.
SOLVER_MODULES: Final = (ratio, optimize)

#: What the derivation above finds today. Asserted, not assumed: a derivation
#: that silently returns fewer names still satisfies a set-equality arm against
#: a table that shrank the same way.
EXPECTED_SOLVER_EXCEPTIONS: Final = 12

#: HTTP codes the envelope admits: 200, 400, 404, 405, 501 and 503.
EXPECTED_HTTP_CODES: Final = 6

#: Body status words: ok, not_implemented, unavailable, error.
EXPECTED_STATUSES: Final = 4

#: A floor, not a measurement. ``ROADMAP.md`` holds far more OPEN item lines
#: than this; the number exists so a scanner that silently matches nothing
#: cannot pass the arm that consumes it.
MIN_ROADMAP_ITEM_LINES: Final = 50

#: The ``ROADMAP.md`` item-line shape, from that file's own header: an ID, a
#: space-hyphen-space, then the line. An ID mentioned in prose is deliberately
#: NOT an item line - only a line that OPENS with the ID counts as open work.
ROADMAP_ITEM_LINE: Final = re.compile(r"^(CS-\d{3}) - ")

#: A well-formed CS id that appears nowhere in ``ROADMAP.md``. The negative half
#: of the blocked_by arm: the form check passes and the membership check must
#: not.
UNKNOWN_BLOCKER: Final = "CS-999"

#: Blocker spellings the form check must refuse. ``"CS-400\n"`` is the one that
#: matters: ``re.match`` with a trailing ``$`` accepts it, because ``$`` also
#: matches immediately before a final newline, so only ``fullmatch`` refuses it.
MALFORMED_BLOCKERS: Final = (
    "",
    "CS-4",
    "CS-4000",
    "cs-400",
    "CS400",
    "CS-400 ",
    "CS-400\n",
    " CS-400",
    "CS-abc",
    "CS-400 - and a title",
)

#: Endpoint templates this repository authors. Every one is a literal in the
#: shipped tree, never a path read off a request line.
SAMPLE_ENDPOINT: Final = "/api/health"
SAMPLE_TEMPLATE_WITH_PARAMETER: Final = "/api/advice/<id>/derivation"

#: A home-path-shaped sample, ASSEMBLED FROM FRAGMENTS rather than written out.
#: A tracked file may not carry an absolute path under a user home directory
#: (non-negotiable 3), and ``tests/test_scaffold.py`` asserts that across the
#: whole tree - it caught the first draft of the constant below, which is that
#: guard doing precisely its job. ``test_home_path_detector_actually_detects``
#: assembles its own samples the same way and says so.
_DRIVE_ROOT: Final = "C:/"
_HOME_DIR: Final = "Users"
_HOME_PATH_SAMPLE: Final = _DRIVE_ROOT + _HOME_DIR + "/an-account/a-world.sav"

#: Spellings ``_checked_endpoint`` must refuse. Each is a shape a RAW REQUEST
#: PATH can take and a route template cannot, which is the point: an endpoint
#: field that accepted the request path would reflect caller-chosen text - and
#: on this project a save path, an account directory or a world name - straight
#: back into a response body.
REFLECTED_PATHS: Final = (
    "/api/world?save=" + _HOME_PATH_SAMPLE,
    _HOME_PATH_SAMPLE,
    "/api/world#fragment",
    "/api/World",
    "/api/world%2fescaped",
    "../../etc/passwd",
    "",
    "/",
    "/notapi/world",
)


# ---------------------------------------------------------------------------
# Detectors. Each is exercised against a planted POSITIVE further down, so a
# detector that has stopped detecting cannot report a clean tree.
# ---------------------------------------------------------------------------


def _contract_source() -> str:
    """The shipped source of the module under test.

    Read from the module's own ``__file__`` rather than from a path literal, so
    this arm cannot drift from what was imported and cannot hardcode a path.

    Returns:
        The source text.
    """
    return Path(inspect.getfile(contract)).read_text(encoding="ascii")


def _node_count(source: str, kinds: tuple[type[ast.AST], ...]) -> int:
    """How many nodes of the given kinds the source holds.

    Args:
        source: Python source.
        kinds: The node types to count.

    Returns:
        The count.
    """
    return sum(1 for node in ast.walk(ast.parse(source)) if isinstance(node, kinds))


def _format_call_count(source: str) -> int:
    """How many ``<something>.format(...)`` calls the source holds.

    ``str.format`` is the interpolation route an f-string ban does not cover,
    and the exception-message guard records it as a shape that produced NO
    channel at all when it was missed.

    Args:
        source: Python source.

    Returns:
        The count.
    """
    return sum(
        1
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    )


def _percent_format_count(source: str) -> int:
    """How many percent-formatting expressions over a string the source holds.

    Args:
        source: Python source.

    Returns:
        The count.
    """
    found = 0
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mod):
            continue
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            found += 1
    return found


def _function_node(source: str, name: str) -> ast.FunctionDef:
    """The named module-level function's AST node.

    Args:
        source: Python source.
        name: The function name.

    Returns:
        The node.

    Raises:
        AssertionError: When the module declares no such function. An absent
            function and a clean one must not look alike.
    """
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("the module declares no function by that name")


def _open_roadmap_ids(text: str) -> frozenset[str]:
    """Every item ID that OPENS a line of the roadmap.

    Args:
        text: The roadmap text.

    Returns:
        The IDs.
    """
    return frozenset(
        match.group(1)
        for line in text.splitlines()
        if (match := ROADMAP_ITEM_LINE.match(line)) is not None
    )


def _exported_exception_names(modules: Iterable[object]) -> frozenset[str]:
    """Every exception class name the given modules export through ``__all__``.

    Args:
        modules: The modules.

    Returns:
        The names.
    """
    found: set[str] = set()
    for module in modules:
        for name in getattr(module, "__all__", ()):
            member = getattr(module, name)
            if isinstance(member, type) and issubclass(member, BaseException):
                found.add(name)
    return frozenset(found)


#: Sentinel meaning "delete this key" for :func:`_mutated`.
_DROP: Final = object()

#: A code the envelope does not admit, used to plant an unroutable response.
UNADMITTED_HTTP_CODE: Final = 418

#: Two distinct things, asserted as a SET SIZE rather than as ``a != b``. mypy's
#: ``strict_equality`` resolves a ``Final`` string to its literal type and calls
#: the direct comparison non-overlapping, so the honest arm has to be spelled in
#: a form the type checker cannot decide for it.
BOTH_REJECTION_PATHS: Final = 2


def _mutated(response: contract.Response, **changes: object) -> contract.Response:
    """A response with its payload edited - the planted non-conforming control.

    Args:
        response: A conforming response.
        **changes: Payload keys to set. A value of ``_DROP`` removes the key.

    Returns:
        The planted response.
    """
    payload = dict(response.payload)
    for key, value in changes.items():
        if value is _DROP:
            payload.pop(key, None)
        else:
            payload[key] = value
    return contract.Response(http_status=response.http_status, payload=payload)


# ===========================================================================
# a. The refusal cannot outlive its reason
# ===========================================================================


def test_the_blocker_set_is_not_empty() -> None:
    count = len(contract.OPEN_BLOCKERS)

    assert count > 0, "an empty blocker set makes every arm below it vacuous"


def test_every_open_blocker_is_an_open_roadmap_item_line(repo_root: Path) -> None:
    open_ids = _open_roadmap_ids((repo_root / "ROADMAP.md").read_text(encoding="ascii"))
    line_count = len(open_ids)
    assert line_count >= MIN_ROADMAP_ITEM_LINES, "the roadmap scanner matched almost nothing"

    blocker_count = len(contract.OPEN_BLOCKERS)
    assert blocker_count > 0

    absent = sorted(contract.OPEN_BLOCKERS - open_ids)
    absent_count = len(absent)

    assert absent_count == 0, (
        "a blocked_by id the surface still cites is no longer an OPEN roadmap "
        "item line, so a 501 refusal has outlived the work it points at"
    )


def test_the_roadmap_scanner_discriminates(repo_root: Path) -> None:
    open_ids = _open_roadmap_ids((repo_root / "ROADMAP.md").read_text(encoding="ascii"))

    assert UNKNOWN_BLOCKER not in open_ids, "the scanner accepts an id the roadmap never names"


def test_not_implemented_accepts_every_open_blocker() -> None:
    blockers = sorted(contract.OPEN_BLOCKERS)
    count = len(blockers)
    assert count > 0

    problems = [
        problem
        for blocker in blockers
        for problem in contract.contract_problems(
            contract.not_implemented(SAMPLE_ENDPOINT, blocker)
        )
    ]
    problem_count = len(problems)

    assert problem_count == 0


@pytest.mark.parametrize("blocker", MALFORMED_BLOCKERS)
def test_not_implemented_refuses_a_malformed_blocker(blocker: str) -> None:
    with pytest.raises(ValueError, match=re.escape(contract.BLOCKER_MALFORMED)):
        contract.not_implemented(SAMPLE_ENDPOINT, blocker)


def test_the_malformed_blocker_population_is_not_empty() -> None:
    count = len(MALFORMED_BLOCKERS)

    assert count > 0


def test_not_implemented_refuses_a_well_formed_blocker_that_is_not_open() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.BLOCKER_NOT_OPEN)):
        contract.not_implemented(SAMPLE_ENDPOINT, UNKNOWN_BLOCKER)


def test_the_two_blocker_refusals_are_distinguishable() -> None:
    lines: set[str] = {contract.BLOCKER_MALFORMED, contract.BLOCKER_NOT_OPEN}
    count = len(lines)

    assert count == BOTH_REJECTION_PATHS, (
        "one message for both rejection paths makes the two arms above indistinguishable"
    )


# ===========================================================================
# b. The wire bytes: deterministic, and 7-bit whatever the payload holds
# ===========================================================================


def test_encode_is_byte_identical_across_two_calls() -> None:
    payload = contract.ok(SAMPLE_ENDPOINT, {"b": 2, "a": [1, {"z": 0, "y": 1}]}).payload

    first = contract.encode(payload)
    second = contract.encode(payload)

    assert first == second
    assert type(first) is bytes


def test_encode_is_insensitive_to_the_order_the_payload_was_built_in() -> None:
    """Two encodes of ONE object cannot see ``sort_keys``; two builds can.

    MEASURED, NOT REASONED. In the S0 mutation pass, deleting ``sort_keys``
    left ``test_encode_is_byte_identical_across_two_calls`` green - a dict
    iterates in insertion order, so encoding the same object twice agrees
    whether or not the keys are sorted. The determinism property this project
    actually needs is that two runs which BUILT the payload differently still
    agree down to the byte, and only a second, differently-ordered payload
    grades it.
    """
    first = contract.encode({"a": 1, "b": 2, "c": 3})
    second = contract.encode({"c": 3, "b": 2, "a": 1})

    assert first == second


def test_encode_sorts_keys_and_uses_fixed_separators() -> None:
    raw = contract.encode({"b": 1, "a": {"d": 2, "c": 3}})

    assert raw == b'{"a":{"c":3,"d":2},"b":1}'


def test_encode_emits_only_seven_bit_bytes_from_a_non_ascii_payload() -> None:
    raw = contract.encode({"status": "ok", "endpoint": SAMPLE_ENDPOINT, "data": {"k": "a\u00e9b"}})
    byte_count = len(raw)
    assert byte_count > 0, "an empty encoding would satisfy the byte scan vacuously"

    high = [byte for byte in raw if byte > contract.MAX_ASCII_BYTE]
    high_count = len(high)

    assert high_count == 0
    assert b"\\u00e9" in raw, "the non-ascii character was dropped rather than escaped"


def test_the_high_byte_detector_detects() -> None:
    planted = "a\u00e9b".encode()

    high = [byte for byte in planted if byte > contract.MAX_ASCII_BYTE]
    high_count = len(high)

    assert high_count > 0, "the scan that proves the encoder clean cannot see a high byte"


def test_encode_refuses_a_payload_carrying_a_float() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.FLOAT_ON_THE_WIRE)):
        contract.encode({"status": "ok", "endpoint": SAMPLE_ENDPOINT, "data": {"rate": 7.5}})


def test_encode_refuses_a_float_nested_in_a_list() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.FLOAT_ON_THE_WIRE)):
        contract.encode({"a": [{"b": [0.5]}]})


def test_encode_admits_an_integer() -> None:
    raw = contract.encode({"a": 5})

    assert raw == b'{"a":5}'


# ===========================================================================
# c. An exact ratio is transcribed, never computed
# ===========================================================================


def test_rational_transcribes_the_numerator_and_the_denominator() -> None:
    assert contract.rational(Fraction(5, 2)) == {"num": 5, "den": 2}


def test_rational_transcribes_a_normalised_fraction_without_reducing_it_itself() -> None:
    assert contract.rational(Fraction(10, 4)) == {"num": 5, "den": 2}


def test_rational_renders_a_whole_number_as_a_ratio_not_a_bare_number() -> None:
    rendered = contract.rational(Fraction(3))

    assert rendered == {"num": 3, "den": 1}
    assert contract.encode(rendered) == b'{"den":1,"num":3}'


def test_rational_body_holds_no_binop() -> None:
    node = _function_node(_contract_source(), "rational")
    statement_count = len(node.body)
    assert statement_count > 0, "an empty body would satisfy the binop scan vacuously"

    binops = [child for child in ast.walk(node) if isinstance(child, ast.BinOp)]
    binop_count = len(binops)

    assert binop_count == 0, "rational computes; it is required to transcribe"


def test_the_binop_detector_detects() -> None:
    planted = "def rational(value):\n    return {'num': value.numerator + 1}\n"

    node = _function_node(planted, "rational")
    binops = [child for child in ast.walk(node) if isinstance(child, ast.BinOp)]
    binop_count = len(binops)

    assert binop_count == 1, "the scan that proves rational arithmetic-free cannot see arithmetic"


# ===========================================================================
# d. The code and the body cannot disagree - both directions
# ===========================================================================


def _conforming() -> tuple[contract.Response, ...]:
    """One conforming response per constructor.

    Returns:
        The responses.
    """
    return (
        contract.ok(SAMPLE_ENDPOINT, {"alive": True}),
        contract.not_implemented(SAMPLE_TEMPLATE_WITH_PARAMETER, sorted(contract.OPEN_BLOCKERS)[0]),
        contract.unavailable(SAMPLE_ENDPOINT, contract.REASON_NO_SAVE),
        contract.bad_request(SAMPLE_ENDPOINT, contract.REASON_MISSING_PARAMETER),
        contract.no_such_route(),
        contract.method_not_allowed(SAMPLE_ENDPOINT),
    )


def test_every_constructor_yields_a_conforming_response() -> None:
    responses = _conforming()
    count = len(responses)
    assert count == EXPECTED_HTTP_CODES, "one constructor per admitted http code, and no more"

    problems = [
        problem for response in responses for problem in contract.contract_problems(response)
    ]
    problem_count = len(problems)

    assert problem_count == 0


def test_every_admitted_code_is_reachable_from_a_constructor() -> None:
    produced = frozenset(response.http_status for response in _conforming())
    produced_count = len(produced)
    assert produced_count == EXPECTED_HTTP_CODES

    assert produced == frozenset(contract.STATUS_FOR_CODE)


def test_a_two_hundred_may_not_carry_a_status_other_than_ok() -> None:
    planted = _mutated(contract.ok(SAMPLE_ENDPOINT, {}), status=contract.STATUS_ERROR)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_STATUS_MISMATCH in problems


def test_a_five_oh_one_may_not_carry_status_ok() -> None:
    conforming = contract.not_implemented(SAMPLE_ENDPOINT, sorted(contract.OPEN_BLOCKERS)[0])
    planted = _mutated(conforming, status=contract.STATUS_OK)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_STATUS_MISMATCH in problems


def test_a_five_oh_one_may_not_carry_a_null_blocked_by() -> None:
    conforming = contract.not_implemented(SAMPLE_ENDPOINT, sorted(contract.OPEN_BLOCKERS)[0])
    planted = _mutated(conforming, blocked_by=None)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_BLOCKED_BY_ABSENT in problems


def test_a_five_oh_one_may_not_cite_a_blocker_that_is_not_open() -> None:
    conforming = contract.not_implemented(SAMPLE_ENDPOINT, sorted(contract.OPEN_BLOCKERS)[0])
    planted = _mutated(conforming, blocked_by=UNKNOWN_BLOCKER)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_BLOCKED_BY_ABSENT in problems


def test_a_five_oh_three_may_not_carry_a_blocked_by() -> None:
    conforming = contract.unavailable(SAMPLE_ENDPOINT, contract.REASON_NO_SAVE)
    planted = _mutated(conforming, blocked_by=sorted(contract.OPEN_BLOCKERS)[0])

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_BLOCKED_BY_PRESENT in problems


def test_a_two_hundred_must_carry_data() -> None:
    planted = _mutated(contract.ok(SAMPLE_ENDPOINT, {}), data=_DROP)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_KEYS_UNEXPECTED in problems


def test_a_two_hundred_may_not_carry_a_reason() -> None:
    planted = _mutated(contract.ok(SAMPLE_ENDPOINT, {}), reason=contract.REASON_NO_SAVE)

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_KEYS_UNEXPECTED in problems


def test_a_refusal_may_not_carry_a_detail_that_is_not_the_reason_s_own_line() -> None:
    conforming = contract.bad_request(SAMPLE_ENDPOINT, contract.REASON_MISSING_PARAMETER)
    planted = _mutated(conforming, detail="the world named Foo could not be read")

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_DETAIL_MISMATCH in problems


def test_a_refusal_may_not_carry_a_reason_outside_the_vocabulary() -> None:
    conforming = contract.bad_request(SAMPLE_ENDPOINT, contract.REASON_MISSING_PARAMETER)
    planted = _mutated(conforming, reason="something_invented")

    problems = contract.contract_problems(planted)

    assert contract.PROBLEM_REASON_UNKNOWN in problems


def test_an_unadmitted_http_code_is_rejected() -> None:
    planted = contract.Response(
        http_status=UNADMITTED_HTTP_CODE, payload={"status": contract.STATUS_OK}
    )

    problems = contract.contract_problems(planted)

    assert problems == (contract.PROBLEM_UNKNOWN_CODE,)


def test_bad_request_refuses_a_reason_that_belongs_to_another_status() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.UNPUBLISHED_REASON)):
        contract.bad_request(SAMPLE_ENDPOINT, contract.REASON_NO_SAVE)


def test_unavailable_refuses_a_reason_that_belongs_to_another_status() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.UNPUBLISHED_REASON)):
        contract.unavailable(SAMPLE_ENDPOINT, contract.REASON_MISSING_PARAMETER)


def test_a_constructor_refuses_a_reason_outside_the_vocabulary() -> None:
    with pytest.raises(ValueError, match=re.escape(contract.UNPUBLISHED_REASON)):
        contract.bad_request(SAMPLE_ENDPOINT, "something_invented")


def test_every_problem_code_the_module_publishes_is_distinct() -> None:
    codes = contract.PROBLEM_CODES
    count = len(codes)
    assert count > 0

    assert len(frozenset(codes)) == count


# ===========================================================================
# The endpoint field cannot become a reflection of the request path
# ===========================================================================


@pytest.mark.parametrize("path", REFLECTED_PATHS)
def test_a_raw_request_path_cannot_reach_the_endpoint_field(path: str) -> None:
    with pytest.raises(ValueError, match=re.escape(contract.ENDPOINT_UNSPELLABLE)):
        contract.ok(path, {})


def test_the_reflected_path_population_is_not_empty() -> None:
    count = len(REFLECTED_PATHS)

    assert count > 0


def test_a_route_template_is_accepted() -> None:
    response = contract.ok(SAMPLE_TEMPLATE_WITH_PARAMETER, {})

    assert response.payload["endpoint"] == SAMPLE_TEMPLATE_WITH_PARAMETER


def test_the_unrouted_sentinel_is_a_literal_and_not_the_requested_path() -> None:
    response = contract.no_such_route()

    assert response.payload["endpoint"] == contract.ENDPOINT_UNROUTED
    assert contract.ENDPOINT_UNROUTED in _contract_source()


# ===========================================================================
# e. SOLVER_REFUSALS is exhaustive over what the solver exports
# ===========================================================================


def test_the_exported_solver_exception_population_is_the_expected_size() -> None:
    names = _exported_exception_names(SOLVER_MODULES)
    count = len(names)

    assert count == EXPECTED_SOLVER_EXCEPTIONS


def test_solver_refusals_covers_every_exported_solver_exception() -> None:
    names = _exported_exception_names(SOLVER_MODULES)
    count = len(names)
    assert count == EXPECTED_SOLVER_EXCEPTIONS

    assert frozenset(contract.SOLVER_REFUSALS) == names


def test_the_exception_derivation_is_not_a_name_suffix_rule() -> None:
    names = _exported_exception_names(SOLVER_MODULES)

    suffixed = frozenset(name for name in names if name.endswith("Error"))
    unsuffixed_count = len(names - suffixed)

    assert unsuffixed_count > 0, (
        "the derivation now agrees with a *Error suffix rule, so the arm that "
        "exists to refuse that rule proves nothing"
    )


def test_every_solver_refusal_maps_to_a_known_status_and_reason() -> None:
    entries = sorted(contract.SOLVER_REFUSALS.items())
    count = len(entries)
    assert count == EXPECTED_SOLVER_EXCEPTIONS

    bad = [
        name
        for name, (status, reason) in entries
        if status not in contract.STATUSES
        or reason not in contract.REASONS
        or contract.REASONS[reason][0] != status
    ]
    bad_count = len(bad)

    assert bad_count == 0


def test_a_solver_refusal_is_found_by_class_name_and_not_by_message() -> None:
    message = "no plan for Desc_SyntheticItem_C at any scale"
    raised = ratio.UnsolvableChain(item="Desc_SyntheticItem_C", message=message)

    assert type(raised).__name__ in contract.SOLVER_REFUSALS
    assert message not in contract.SOLVER_REFUSALS, (
        "the table is keyed by message text, which is the echo channel keying "
        "on the class name exists to avoid"
    )
    assert str(raised) not in contract.SOLVER_REFUSALS


# ===========================================================================
# f. detail is never built from content
# ===========================================================================


def test_the_module_holds_no_f_string() -> None:
    source = _contract_source()
    assert len(source) > 0

    count = _node_count(source, (ast.JoinedStr,))

    assert count == 0, (
        "an f-string in this module is a site where a value could reach a detail line"
    )


def test_the_f_string_detector_detects() -> None:
    count = _node_count("x = f'{y}'\n", (ast.JoinedStr,))

    assert count == 1


def test_the_module_holds_no_format_call() -> None:
    count = _format_call_count(_contract_source())

    assert count == 0


def test_the_format_call_detector_detects() -> None:
    count = _format_call_count("x = '{a}'.format(a=y)\n")

    assert count == 1


def test_the_module_holds_no_percent_formatting() -> None:
    count = _percent_format_count(_contract_source())

    assert count == 0


def test_the_percent_format_detector_detects() -> None:
    count = _percent_format_count("x = '%s' % y\n")

    assert count == 1


def test_every_reason_carries_a_detail_line_and_a_status() -> None:
    entries = sorted(contract.REASONS.items())
    count = len(entries)
    assert count > 0

    bad = [
        reason
        for reason, (status, detail) in entries
        if status not in contract.STATUSES or not detail or not detail.endswith(".")
    ]
    bad_count = len(bad)

    assert bad_count == 0


def test_every_detail_line_is_unique() -> None:
    details = [detail for _status, detail in contract.REASONS.values()]
    count = len(details)
    assert count > 0

    assert len(frozenset(details)) == count, "two reasons sharing a line cannot be told apart"


def test_a_refusal_body_carries_the_table_s_line_verbatim() -> None:
    response = contract.unavailable(SAMPLE_ENDPOINT, contract.REASON_NO_SAVE)

    assert response.payload["detail"] == contract.REASONS[contract.REASON_NO_SAVE][1]


# ===========================================================================
# The vocabulary itself
# ===========================================================================


def test_the_status_vocabulary_is_closed_and_the_expected_size() -> None:
    count = len(contract.STATUSES)

    assert count == EXPECTED_STATUSES
    assert frozenset(contract.STATUS_FOR_CODE.values()) <= frozenset(contract.STATUSES)


def test_the_501_and_503_split_does_not_collapse() -> None:
    for_501 = contract.STATUS_FOR_CODE[contract.HTTP_NOT_IMPLEMENTED]
    for_503 = contract.STATUS_FOR_CODE[contract.HTTP_UNAVAILABLE]

    words: set[str] = {contract.STATUS_NOT_IMPLEMENTED, contract.STATUS_UNAVAILABLE}

    assert for_501 == contract.STATUS_NOT_IMPLEMENTED
    assert for_503 == contract.STATUS_UNAVAILABLE
    assert len(words) == BOTH_REJECTION_PATHS, (
        "the two truths - not built yet, and not present here - have collapsed into one word"
    )


def test_only_not_implemented_admits_a_blocked_by() -> None:
    with_blocker = [
        response for response in _conforming() if response.payload.get("blocked_by") is not None
    ]
    count = len(with_blocker)

    assert count == 1
    assert with_blocker[0].http_status == contract.HTTP_NOT_IMPLEMENTED


def test_every_public_name_resolves() -> None:
    names = sorted(contract.__all__)
    count = len(names)
    assert count > 0

    missing = [name for name in names if not hasattr(contract, name)]
    missing_count = len(missing)

    assert missing_count == 0


# ===========================================================================
# The provider protocols
# ===========================================================================


def test_a_structural_world_provider_satisfies_the_protocol() -> None:
    class _Stub:
        def world(self) -> None:
            return None

    assert isinstance(_Stub(), contract.WorldProvider)


def test_something_without_the_method_does_not_satisfy_the_world_protocol() -> None:
    class _Stub:
        def registry(self) -> None:
            return None

    assert not isinstance(_Stub(), contract.WorldProvider)


def test_a_structural_registry_provider_satisfies_the_protocol() -> None:
    class _Stub:
        def registry(self) -> None:
            return None

    assert isinstance(_Stub(), contract.RegistryProvider)


def test_something_without_the_method_does_not_satisfy_the_registry_protocol() -> None:
    class _Stub:
        def world(self) -> None:
            return None

    assert not isinstance(_Stub(), contract.RegistryProvider)


def test_a_route_carries_its_method_template_and_handler() -> None:
    def _handler(_query: object) -> contract.Response:
        return contract.ok(SAMPLE_ENDPOINT, {})

    route = contract.Route(method="GET", template=SAMPLE_ENDPOINT, handler=_handler)

    assert route.method == "GET"
    assert route.template == SAMPLE_ENDPOINT
    assert route.handler is _handler


def test_the_module_imports_no_layer_below_its_neighbour() -> None:
    tree = ast.parse(_contract_source())
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    count = len(imported)
    assert count > 0, "an empty import list would satisfy the seam scan vacuously"

    reaching = [name for name in imported if name.startswith("clockspeed.")]
    reaching_count = len(reaching)

    assert reaching_count == 0, (
        "the contract module reached into another clockspeed layer; the seam "
        "comment in clockspeed/surface/__init__.py enumerates what is below "
        "this one and the save and data layers are not among them"
    )
