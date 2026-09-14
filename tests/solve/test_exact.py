"""Tests for the exact rational primitives and the no-float invariant.

Three properties carry this module, and each is here because the defect it
catches is INVISIBLE in ordinary output.

- **Exactness is not provable by equality.** ``Fraction(1, 2) == 0.5`` is
  ``True``, so an equality assertion passes against the float that poisoned the
  value it was supposed to catch. Every numeric assertion below pairs the value
  with ``type(x) is Fraction``.
- **The pivot rule is invisible in the result.** With exact arithmetic the
  reduced row echelon form of a matrix is UNIQUE, so a magnitude-pivoting
  implementation computes the same answer by different work and no assertion on
  ``solve_linear``'s return value can tell the two apart. That is precisely why
  ``_pivot_row`` is imported and tested directly: the rule is a contract, and a
  contract with no test is the CONVENTIONS.md section 7.2 unrun gate.
- **No tolerance, anywhere.** No ``pytest.approx``, no ``math.isclose``, no
  epsilon - see ``tests/solve/__init__.py`` for why a tolerance here would be a
  test that cannot fail on the defect it exists to catch. This module also
  imports no ``math`` and writes no ``**``, so it can never accidentally
  demonstrate the operator it forbids.

``cast`` appears several times below and always for the same reason: the runtime
type guards exist for values that arrive through an untyped boundary, and the
only way to drive them from an annotated test is to hand the checker a value its
signature forbids on purpose.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum
from fractions import Fraction
from itertools import permutations
from pathlib import Path
from typing import Final, cast

import pytest

from clockspeed.solve import exact as exact_module
from clockspeed.solve.exact import (
    OUTCOME_INCONSISTENT,
    OUTCOME_UNDERDETERMINED,
    OUTCOME_UNIQUE,
    SECONDS_PER_MINUTE,
    DeferredPowerTerm,
    InexactValueError,
    UndefinedRateError,
    _pivot_row,
    audit_exact,
    isolating_rows,
    per_minute,
    solve_linear,
    to_exact,
)

# Shorthand for the wider systems below. Writing Fraction() out in full there
# makes the shape of the matrix impossible to see at a glance, and the shape is
# the whole point of those cases.
F0 = Fraction(0)
F1 = Fraction(1)
F3 = Fraction(3)

# ---------------------------------------------------------------------------
# Fixtures for the recursion tests, hand-authored rather than borrowed
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Step:
    """One step of a stand-in plan object, holding the value that gets poisoned."""

    rate: object


@dataclass(frozen=True)
class _Plan:
    """A stand-in for the shape real advice will arrive in: nested, not scalar."""

    steps: tuple[_Step, ...]


class _Tier(IntEnum):
    """An int-like value that is not an int, for the positive-typing test."""

    FIRST = 1


# ===========================================================================
# a. to_exact - the decimal string never passes through float
# ===========================================================================


def test_to_exact_converts_a_decimal_string_without_passing_through_float() -> None:
    """The overclock exponent converts to its exact rational value.

    1.321929 is not representable in binary floating point, so this is the
    string on which a ``float()`` in the conversion path is detectable at all.
    The type assertion is not decoration: equality alone would pass against the
    float, because Fraction compares equal to the float it approximates.
    """
    value = to_exact("1.321929")

    assert value == Fraction(1321929, 1000000)
    assert type(value) is Fraction


def test_to_exact_refuses_a_float_because_the_binary_value_is_not_the_decimal_one() -> None:
    """A float argument is rejected rather than converted.

    ``Fraction(0.1)`` SUCCEEDS and yields 3602879701896397/36028797018963968 -
    an exact reading of the binary approximation and a wrong reading of the
    decimal 0.1. It is exact and wrong, which no downstream assertion on
    exactness can detect. The refusal is the only place the mistake is visible.
    """
    assert Fraction(0.1) != Fraction(1, 10)

    with pytest.raises(InexactValueError, match="float"):
        to_exact(cast("str", 0.1))


def test_to_exact_rejects_a_string_that_is_not_a_number() -> None:
    """A non-numeric string raises ValueError rather than returning a guess."""
    with pytest.raises(ValueError, match="not-a-number"):
        to_exact("not-a-number")


def test_the_module_errors_are_not_value_errors_so_a_handler_cannot_swallow_them() -> None:
    """Neither error subclasses ValueError, which is what keeps the canary audible.

    ``to_exact`` raises ValueError for a malformed string, so a caller will
    reasonably wrap it in ``except ValueError``. If the float refusal shared
    that hierarchy, the handler written for bad text would silently absorb the
    one signal that says the solve path has been poisoned - the same reasoning
    that keeps RegistryIntegrityError out of the ValueError hierarchy in
    clockspeed/data/registry.py.
    """
    assert not issubclass(InexactValueError, ValueError)
    assert not issubclass(UndefinedRateError, ValueError)


# ===========================================================================
# b. per_minute and the unit definition
# ===========================================================================


def test_seconds_per_minute_is_the_unit_definition() -> None:
    """The one place the minute is defined, pinned so nothing else restates it."""
    one_minute_in_seconds = 60

    assert one_minute_in_seconds == SECONDS_PER_MINUTE
    assert type(SECONDS_PER_MINUTE) is int


def test_per_minute_is_exact_for_a_duration_that_does_not_divide_a_minute() -> None:
    """A seven second cycle produces 60/7 per minute and never 8.571428571428571."""
    rate = per_minute(Fraction(1), Fraction(7))

    assert rate == Fraction(60, 7)
    assert type(rate) is Fraction


def test_per_minute_raises_on_a_zero_duration_rather_than_reporting_an_infinite_rate() -> None:
    """A measured zero duration is a real input, not a defensive branch.

    clockspeed/data/registry.py keeps a measured zero on ``Recipe.duration``
    deliberately - it skips an ABSENT duration precisely so a real zero stays
    distinguishable. So a zero arrives here, and the only two options are a
    named refusal or ZeroDivisionError from inside an arithmetic expression.
    """
    with pytest.raises(UndefinedRateError, match="zero"):
        per_minute(Fraction(1), Fraction(0))


def test_per_minute_refuses_a_float_duration_that_would_otherwise_return_a_float() -> None:
    """A float duration is rejected before it can turn the whole rate into a float.

    ``Fraction(60) / 0.5`` returns the float 120.0, not a Fraction. Nothing
    downstream raises on that, the number even looks right, and the exactness
    invariant has already been lost by the time anyone reads the result.
    """
    assert type(Fraction(60) / 0.5) is float

    with pytest.raises(InexactValueError, match="duration"):
        per_minute(Fraction(1), cast("Fraction", 0.5))

    with pytest.raises(InexactValueError, match="amount"):
        per_minute(cast("Fraction", 0.5), Fraction(1))


# ===========================================================================
# c. audit_exact - the positive audit, and the path it names
# ===========================================================================


def test_audit_exact_accepts_the_legitimate_leaf_types_nested_arbitrarily() -> None:
    """A clean structure passes silently.

    A rejection test alone would pass for an audit that rejected everything,
    which is the CONVENTIONS.md section 7.2 "negative assertion rules out
    without pinning down" class. This pins the accepting half.
    """
    audit_exact(
        _Plan(steps=(_Step(rate=Fraction(1, 3)), _Step(rate=None))),
        path="plan",
    )
    audit_exact({"count": 4, "enabled": True, "label": "smelter", "rate": Fraction(1, 1000)})
    audit_exact([(Fraction(1), Fraction(2)), []])


def test_audit_exact_rejects_a_bare_float_and_names_the_path() -> None:
    """The simplest rejection, and the root path label is the caller's to choose."""
    with pytest.raises(InexactValueError, match=re.escape("plan is float")):
        audit_exact(0.5, path="plan")


def test_audit_exact_rejects_a_decimal_that_a_negative_float_check_would_admit() -> None:
    """Decimal is the value that proves the audit is positive rather than negative.

    ``not isinstance(value, float)`` is True for a Decimal, so a negative check
    admits it. Decimal is exact for decimal fractions and CANNOT represent 1/3,
    so it silently rounds inside a ratio solve - the exact defect this module
    exists to prevent, arriving through the one hole a float check leaves open.
    """
    assert not isinstance(Decimal("0.1"), float)

    with pytest.raises(InexactValueError, match="Decimal"):
        audit_exact(Decimal("0.1"))


def test_audit_exact_rejects_an_int_enum_because_the_test_is_identity_not_isinstance() -> None:
    """An int subclass is not an int here, and that is the whole design.

    ``isinstance(_Tier.FIRST, int)`` is True while ``type(_Tier.FIRST) is int``
    is False. The same asymmetry is what makes ``isinstance(True, int)`` admit a
    bool where a number belongs, and identity is the only test that closes both.
    """
    assert isinstance(_Tier.FIRST, int)
    assert type(_Tier.FIRST) is not int

    with pytest.raises(InexactValueError, match="_Tier"):
        audit_exact(_Tier.FIRST)


def test_audit_exact_admits_a_bool_as_a_bool_and_never_by_way_of_int() -> None:
    """A bool is a legitimate flag, admitted on its own identity."""
    audit_exact(True)
    audit_exact({"automated": False})


def test_audit_exact_rejects_a_float_nested_in_a_frozen_dataclass_and_names_the_leaf() -> None:
    """The path reaches through a dataclass and an index to the exact offending leaf.

    This is the shape the values actually arrive in - inside a plan object, not
    as a bare scalar - and a rejection that says only "a float is in here
    somewhere" is a rejection nobody can act on.
    """
    plan = _Plan(steps=(_Step(rate=Fraction(1)), _Step(rate=Fraction(2)), _Step(rate=0.75)))

    with pytest.raises(InexactValueError, match=re.escape("plan.steps[2].rate is float")):
        audit_exact(plan, path="plan")


def test_audit_exact_rejects_a_float_inside_a_tuple_inside_a_mapping_and_names_the_leaf() -> None:
    """Mapping then tuple then index, with the key rendered into the path."""
    with pytest.raises(InexactValueError, match=re.escape("value['iron'][1] is float")):
        audit_exact({"iron": (Fraction(1), 2.5)})


def test_audit_exact_rejects_a_float_used_as_a_mapping_key() -> None:
    """Keys are audited too - a float key is exactly as inexact as a float value."""
    with pytest.raises(InexactValueError, match=re.escape("value.keys()[0] is float")):
        audit_exact({0.25: Fraction(1)})


def test_audit_exact_rejects_a_container_type_it_does_not_model() -> None:
    """An unrecognized container is refused rather than skipped.

    A set iterates in an order the audit cannot state, so admitting one would
    make the path label - and anything a caller rendered from it - depend on
    something other than the input. Refusing is the safe direction: it fails
    loudly on a shape nobody considered instead of walking past its contents.
    """
    with pytest.raises(InexactValueError, match="set"):
        audit_exact({Fraction(1), Fraction(2)})


def test_audit_exact_terminates_on_a_self_referential_container() -> None:
    """A cycle is visited once rather than recursing until the stack runs out."""
    looped: list[object] = [Fraction(1)]
    looped.append(looped)

    audit_exact(looped)

    poisoned: list[object] = [0.5]
    poisoned.append(poisoned)
    with pytest.raises(InexactValueError, match=re.escape("value[0] is float")):
        audit_exact(poisoned)


# ===========================================================================
# d. The pivot rule, tested where it is visible
# ===========================================================================


def test_pivot_row_picks_the_lowest_row_index_and_never_the_largest_magnitude() -> None:
    """Partial pivoting is refused, and this is the only place it is detectable.

    Partial pivoting exists to control floating-point roundoff and there is no
    roundoff here, so with exact arithmetic it produces an identical reduced row
    echelon form by different work. That makes it invisible in
    ``solve_linear``'s output and testable only at the selector. A magnitude
    rule would return row 2 below, whose entry is 900 times larger.
    """
    column = [
        [Fraction(1, 1000)],
        [Fraction(-9, 10)],
    ]

    assert _pivot_row(column, 0, 0) == 0


def test_pivot_row_accepts_an_exact_coefficient_smaller_than_any_usable_epsilon() -> None:
    """The only admissible test is ``entry != 0``, and an epsilon rule fails this.

    Fluid amounts normalize through a division by 1000 and a chain compounds it,
    so a genuinely small exact coefficient is ordinary input rather than noise.
    Any epsilon big enough to absorb roundoff discards it, and discarding a
    coefficient silently drops the whole equation.
    """
    tiny = Fraction(1, 1_000_000_000_000)

    assert tiny != 0
    assert _pivot_row([[Fraction(0)], [tiny]], 0, 0) == 1


def test_pivot_row_reports_no_pivot_rather_than_inventing_one() -> None:
    """An all-zero column below the current row has no pivot, and says so."""
    assert _pivot_row([[Fraction(0)], [Fraction(0)]], 0, 0) is None
    assert _pivot_row([[Fraction(5)], [Fraction(0)]], 1, 0) is None


# ===========================================================================
# e. solve_linear - three outcomes, never collapsed
# ===========================================================================

# x = 2, y = 3, z = -1. Small enough to verify by hand and non-trivial enough
# that a sign slip in the elimination changes the answer.
_MATRIX: tuple[tuple[Fraction, ...], ...] = (
    (Fraction(2), Fraction(1), Fraction(-1)),
    (Fraction(-3), Fraction(-1), Fraction(2)),
    (Fraction(-2), Fraction(1), Fraction(2)),
)
_RHS: tuple[Fraction, ...] = (Fraction(8), Fraction(-11), Fraction(-3))


def test_solve_linear_reports_a_unique_solution_exactly() -> None:
    """The unique case, with every published field pinned rather than just the values."""
    solution = solve_linear(_MATRIX, _RHS)

    assert solution.outcome == OUTCOME_UNIQUE
    assert solution.values == (Fraction(2), Fraction(3), Fraction(-1))
    assert solution.free_variables == ()
    assert solution.rank == len(_MATRIX)
    assert solution.values is not None
    for value in solution.values:
        assert type(value) is Fraction


def test_solve_linear_solves_a_system_whose_answer_is_not_a_whole_number() -> None:
    """A one third solution stays one third, which is the case float cannot hold."""
    solution = solve_linear(((Fraction(3),),), (Fraction(1),))

    assert solution.outcome == OUTCOME_UNIQUE
    assert solution.values == (Fraction(1, 3),)
    assert solution.values is not None
    assert type(solution.values[0]) is Fraction


def test_solve_linear_reports_inconsistent_by_name_and_publishes_no_values() -> None:
    """A zero coefficient row with a nonzero right hand side has no solution at all."""
    solution = solve_linear(
        ((Fraction(1), Fraction(1)), (Fraction(2), Fraction(2))),
        (Fraction(1), Fraction(5)),
    )

    assert solution.outcome == OUTCOME_INCONSISTENT
    assert solution.values is None


def test_solve_linear_reports_underdetermined_and_names_which_variables_are_free() -> None:
    """Rank below the variable count is reported, never solved.

    Returning a solution here is the failure mode that renders as a
    correct-looking factory plan, and pinning the free variables to zero is the
    plausible wrong answer - it produces a full vector of exact Fractions that
    satisfies every equation and is one arbitrary member of an infinite family.
    """
    solution = solve_linear(
        ((Fraction(1), Fraction(1), Fraction(1)),),
        (Fraction(6),),
    )

    assert solution.outcome == OUTCOME_UNDERDETERMINED
    assert solution.free_variables == (1, 2)
    assert solution.rank == 1
    assert solution.values is None


def test_solve_linear_prefers_inconsistent_over_underdetermined() -> None:
    """A system that is both has ZERO solutions, not infinitely many.

    Collapsing the two here would report a solution family for a system that
    admits no solution whatsoever, which is the more dangerous of the two
    misreadings: the caller would go looking for the best member of an empty set.
    """
    solution = solve_linear(
        ((Fraction(1), Fraction(0), Fraction(1)), (Fraction(2), Fraction(0), Fraction(2))),
        (Fraction(1), Fraction(7)),
    )

    assert solution.outcome == OUTCOME_INCONSISTENT
    assert solution.values is None
    assert solution.free_variables == ()


def test_the_three_outcome_names_are_distinct() -> None:
    """Three names, never two. A collapsed pair is a distinction nobody can act on."""
    names = (OUTCOME_UNIQUE, OUTCOME_INCONSISTENT, OUTCOME_UNDERDETERMINED)

    assert len(set(names)) == len(names)


def test_solve_linear_keeps_an_exact_coefficient_too_small_for_any_epsilon() -> None:
    """A tiny exact leading coefficient still carries its equation.

    Under ``abs(entry) > eps`` this column has no pivot, the equation is dropped
    and the system reports underdetermined - a silently thinner system reported
    with a confident name.
    """
    tiny = Fraction(1, 1_000_000_000_000)
    solution = solve_linear(((tiny,),), (Fraction(1),))

    assert solution.outcome == OUTCOME_UNIQUE
    assert solution.values == (Fraction(1_000_000_000_000),)


# ---------------------------------------------------------------------------
# Determinism, proven by permutation rather than asserted
# ---------------------------------------------------------------------------


def _row_permuted() -> tuple[list[list[Fraction]], list[Fraction]]:
    """Reorder the reference system without changing what it says.

    Returns:
        The same equations in the order 2, 0, 1.
    """
    order = (2, 0, 1)
    return [list(_MATRIX[i]) for i in order], [_RHS[i] for i in order]


def _row_scaled() -> tuple[list[list[Fraction]], list[Fraction]]:
    """Multiply each equation by a different nonzero factor.

    Every factor is a different sign and a different magnitude, so an
    implementation that chose its pivot by magnitude would eliminate in a
    different order on this input than on the reference one.

    Returns:
        An equivalent system with every row scaled.
    """
    factors = (Fraction(1, 3), Fraction(7), Fraction(-5, 11))
    return (
        [[entry * factor for entry in row] for row, factor in zip(_MATRIX, factors, strict=True)],
        [value * factor for value, factor in zip(_RHS, factors, strict=True)],
    )


def test_solve_linear_output_is_byte_identical_under_row_permutation_and_row_scaling() -> None:
    """Determinism is a product property, so it is measured on bytes and not on ==.

    CLAUDE.md section 1: two runs on the same input disagreeing is a bug. The
    three inputs here are the same system written three ways, and every
    published field is invariant by construction - the solution vector, the rank
    and the pivot columns are all properties of the system rather than of the
    row order. That invariance is the reason LinearSolution publishes no row
    index: a row index is the one thing a permutation moves, and a field a
    permuted-but-equivalent input changes would break exactly this assertion.
    """
    reference = repr(solve_linear(_MATRIX, _RHS)).encode("ascii")

    permuted_matrix, permuted_rhs = _row_permuted()
    permuted = repr(solve_linear(permuted_matrix, permuted_rhs)).encode("ascii")

    scaled_matrix, scaled_rhs = _row_scaled()
    scaled = repr(solve_linear(scaled_matrix, scaled_rhs)).encode("ascii")

    assert permuted == reference
    assert scaled == reference
    assert b"unique" in reference


def test_the_permutation_helpers_really_do_permute_and_scale() -> None:
    """Without this the determinism test above would pass on three identical inputs.

    CONVENTIONS.md section 7.2: a mutation that fails to apply looks GREEN. The
    helpers are the mutation here, so they are asserted to have applied.
    """
    permuted_matrix, permuted_rhs = _row_permuted()
    scaled_matrix, scaled_rhs = _row_scaled()

    assert permuted_matrix != [list(row) for row in _MATRIX]
    assert permuted_rhs != list(_RHS)
    assert scaled_matrix != [list(row) for row in _MATRIX]
    assert scaled_rhs != list(_RHS)
    assert sorted(permuted_rhs) == sorted(_RHS)


@pytest.mark.parametrize(
    ("matrix", "rhs", "expected"),
    [
        (
            ((F1, F1, F1), (Fraction(2), Fraction(2), Fraction(2)), (F3, F3, F3)),
            (Fraction(6), Fraction(12), Fraction(18)),
            OUTCOME_UNDERDETERMINED,
        ),
        (
            ((F1, F0, F1), (Fraction(2), F0, Fraction(2)), (Fraction(4), F0, Fraction(4))),
            (F1, Fraction(7), Fraction(9)),
            OUTCOME_INCONSISTENT,
        ),
        (
            ((F1, Fraction(2), F0), (F0, F0, F3), (Fraction(2), Fraction(4), Fraction(6))),
            (F1, F3, Fraction(8)),
            OUTCOME_UNDERDETERMINED,
        ),
    ],
    ids=["rank-deficient", "contradictory", "mixed-rank"],
)
def test_the_non_unique_outcomes_are_byte_identical_under_every_row_permutation(
    matrix: tuple[tuple[Fraction, ...], ...],
    rhs: tuple[Fraction, ...],
    expected: str,
) -> None:
    """Determinism is claimed for all three outcomes, so all three are measured.

    The unique case above is the easy one - its solution vector is obviously a
    property of the system. The claim that carries the design is that the
    non-unique reports are too, and that is not obvious: it holds because the
    set of pivot columns in a reduced row echelon form is unique for a given
    matrix, so ``free_variables`` and ``rank`` cannot move when the rows do.
    Every permutation is exercised rather than one, because a single sample
    would be evidence about that sample.
    """
    outputs = {
        repr(solve_linear([list(matrix[i]) for i in order], [rhs[i] for i in order])).encode(
            "ascii"
        )
        for order in permutations(range(len(matrix)))
    }

    assert len(outputs) == 1, f"row order changed the answer: {sorted(outputs)}"
    assert expected.encode("ascii") in outputs.pop()


# ---------------------------------------------------------------------------
# solve_linear input refusal
# ---------------------------------------------------------------------------


def test_solve_linear_refuses_a_float_entry_and_names_its_position() -> None:
    """One float anywhere in the matrix poisons every value derived from it."""
    matrix = cast("list[list[Fraction]]", [[Fraction(1), 0.5], [Fraction(0), Fraction(1)]])

    with pytest.raises(InexactValueError, match=re.escape("matrix[0][1] is float")):
        solve_linear(matrix, (Fraction(1), Fraction(1)))


def test_solve_linear_refuses_an_int_entry_because_int_division_returns_a_float() -> None:
    """An all-int matrix is the trap that a "no floats present" check walks straight past.

    ``1 / 2`` is the float 0.5. Normalizing a pivot row of ints therefore
    produces floats from an input that contained none, so admitting int here
    would manufacture the very thing the module forbids.
    """
    assert type(1 / 2) is float

    matrix = cast("list[list[Fraction]]", [[1, 2], [3, 4]])
    rhs = cast("list[Fraction]", [1, 1])

    with pytest.raises(InexactValueError, match=re.escape("matrix[0][0] is int")):
        solve_linear(matrix, rhs)


def test_solve_linear_rejects_a_ragged_matrix() -> None:
    """Rows of different widths are a caller bug, not a system to guess at."""
    with pytest.raises(ValueError, match="ragged"):
        solve_linear(((Fraction(1), Fraction(1)), (Fraction(1),)), (Fraction(1), Fraction(1)))


def test_solve_linear_rejects_a_right_hand_side_of_the_wrong_length() -> None:
    """One constant per equation, asserted rather than truncated."""
    with pytest.raises(ValueError, match="right-hand side"):
        solve_linear(((Fraction(1),), (Fraction(1),)), (Fraction(1),))


def test_solve_linear_handles_a_system_with_no_equations() -> None:
    """An empty system is vacuously unique over zero variables rather than an error."""
    solution = solve_linear((), ())

    assert solution.outcome == OUTCOME_UNIQUE
    assert solution.values == ()
    assert solution.rank == 0


# ===========================================================================
# f. The module may not contain the operator it forbids
# ===========================================================================


def _exact_source() -> str:
    """Read the module under test as text.

    Returns:
        The source of clockspeed/solve/exact.py.
    """
    root = Path(__file__).resolve().parents[2]
    return (root / "clockspeed" / "solve" / "exact.py").read_text(encoding="ascii")


def test_the_module_contains_no_power_operator_no_pow_and_no_math_import() -> None:
    """The one line nobody should be able to write here is fenced off by the AST.

    ``draw * clock ** exponent`` is the most natural rendering of the power law,
    it reads as exact, and it cannot be: ``Fraction(5, 2) ** Fraction('1.321929')``
    returns the FLOAT 3.3577506181236285. A grep would also match the operator
    inside a docstring, where naming it is the point; the AST sees only code.
    """
    tree = ast.parse(_exact_source())

    powers = [
        node
        for node in ast.walk(tree)
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow))
        or (isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Pow))
    ]
    assert not powers, (
        f"the exponent operator appears in exact.py at lines {[node.lineno for node in powers]}"
    )

    pow_calls = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "pow"
    ]
    assert not pow_calls, f"pow() appears in exact.py at lines {pow_calls}"

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    assert "math" not in imported, "exact.py imports math, which is a float library"


def test_the_module_imports_nothing_from_clockspeed() -> None:
    """Isolation is what lets the exactness primitives be reasoned about alone.

    docs/ARCHITECTURE.md section 3.1 makes the seam an allowed-import matrix.
    This module sits at the bottom of the solve layer, so its permitted set is
    empty: an import of the registry would tie the arithmetic to the shape of
    the game data it happens to be applied to.
    """
    tree = ast.parse(_exact_source())

    reached: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            reached.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            reached.add(node.module)

    assert not [name for name in reached if name.startswith("clockspeed")]


def test_the_deferred_power_term_is_symbolic_and_carries_no_evaluation() -> None:
    """The stand-in for a power law holds its operands and refuses to fold them.

    Publishing an evaluable term would reintroduce the defect behind a nicer
    name, so the term is a record and nothing more. A caller that wants a number
    out of it has to confront the fact that there is no exact one.
    """
    term = DeferredPowerTerm(base=Fraction(5, 2), exponent=to_exact("1.321929"))

    assert term.base == Fraction(5, 2)
    assert term.exponent == Fraction(1321929, 1000000)
    assert type(term.exponent) is Fraction

    methods = [
        name for name in dir(term) if not name.startswith("_") and callable(getattr(term, name))
    ]
    assert not methods, f"DeferredPowerTerm exposes {methods}; it must stay a record"

    audit_exact(term, path="term")


# ===========================================================================
# f. isolating_rows - CS-302, the refusal diagnosis without a solve per row
# ===========================================================================

#: Row counts the scaling arm compares. The lower one is small enough to read
#: by hand; the upper one is far enough above it that a cost linear in the row
#: count cannot be mistaken for a constant one.
_SMALL_CHAIN: Final = 6
_LARGE_CHAIN: Final = 96

#: The attribute the elimination counter hooks. Named as a STRING so the hook is
#: installed through ``monkeypatch.setattr`` rather than by reaching into the
#: module under test - the patch is temporary, and spelling it this way is what
#: makes pytest responsible for removing it again.
_VALIDATE: Final = "_validate_system"

#: The corpus generator. An explicit recurrence, so the systems it yields are a
#: property of this file rather than of the interpreter's random module.
_LCG_MULTIPLIER: Final = 1103515245
_LCG_INCREMENT: Final = 12345
_LCG_MODULUS: Final = 2147483648

#: One row in ``_DEPENDENT_ROW_ODDS`` is drawn fresh; the rest are scaled copies
#: of an earlier row. Copies are the majority on purpose - see the generator.
_DEPENDENT_ROW_ODDS: Final = 2

#: What a fresh row's entries and a copy's scale factor are drawn from. Zeros are
#: over-represented so the matrices are sparse, which is the shape a production
#: chain actually has.
_ENTRIES: Final = (0, 0, 1, -1, 2)
_SCALES: Final = (-2, -1, 1, 2, 3)

#: How much of the corpus must turn out inconsistent before the equivalence arm
#: is worth anything. A generator that drifted into producing solvable systems
#: would otherwise pass by checking almost nothing.
_MIN_INCONSISTENT: Final = 60


def _eliminations_during(monkeypatch: pytest.MonkeyPatch, work: Callable[[], object]) -> int:
    """How many elimination passes ``work`` ran, counted at the one shared gate.

    Every entry point here that eliminates - :func:`solve_linear` and
    :func:`isolating_rows` alike - validates its system exactly once, at the top,
    before touching a coefficient. That call is therefore a faithful counter for
    passes over the matrix, and counting it needs no hook inside the arithmetic
    itself. A wall clock would measure this machine; this measures the work, so
    the arm says the same thing on a slow machine as on a fast one.

    Args:
        monkeypatch: The fixture that installs and removes the counter. Used
            rather than a hand-rolled try/finally so a failing assertion inside
            ``work`` cannot leave the counter installed for the next test.
        work: The call to measure. Its return value is discarded.

    Returns:
        The number of elimination passes performed.
    """
    original = getattr(exact_module, _VALIDATE)
    passes = 0

    def counting(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> int:
        nonlocal passes
        passes += 1
        return int(original(matrix, rhs))

    monkeypatch.setattr(exact_module, _VALIDATE, counting)
    work()
    monkeypatch.undo()
    return passes


def _pseudo_random_system(seed: int) -> tuple[list[list[Fraction]], list[Fraction]]:
    """One system from a deterministic corpus dense with DEPENDENT rows.

    Roughly half the rows are exact scalar multiples of an earlier one, which is
    what drives the left null space above a single dimension. A criterion that
    happens to work when the contradiction has one witness passes a corpus of
    independent rows and fails here, so the duplication is the point of this
    generator rather than an economy in it.

    The generator is an explicit linear congruential recurrence rather than the
    standard library's, so the corpus is a property of this file: the same seed
    yields the same system on every interpreter, forever, and a case that once
    caught a defect cannot silently stop being generated.

    Args:
        seed: Selects the system.

    Returns:
        The matrix and the right-hand side.
    """
    state = seed * 2 + 1

    def draw(bound: int) -> int:
        nonlocal state
        state = (state * _LCG_MULTIPLIER + _LCG_INCREMENT) % _LCG_MODULUS
        return state % bound

    rows = 3 + draw(6)
    columns = 1 + draw(6)
    matrix: list[list[Fraction]] = []
    for _ in range(rows):
        if matrix and draw(_DEPENDENT_ROW_ODDS) != 0:
            scale = Fraction(_SCALES[draw(len(_SCALES))])
            matrix.append([scale * entry for entry in matrix[draw(len(matrix))]])
            continue
        matrix.append([Fraction(_ENTRIES[draw(len(_ENTRIES))]) for _ in range(columns)])
    return matrix, [Fraction(draw(3) - 1) for _ in range(rows)]


def _brute_force_isolating(
    matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]
) -> tuple[int, ...]:
    """The leave-one-out loop, as an ORACLE rather than as an implementation.

    This is the O(rows) formulation CS-302 measured and replaced. It is kept
    here, in the test, precisely because the replacement's whole claim is that it
    answers the same question - and a claim of equivalence needs the thing it is
    equivalent TO, written out independently of the code under test rather than
    remembered from a commit message.

    Args:
        matrix: The coefficient rows.
        rhs: One constant per equation.

    Returns:
        Every row index whose removal leaves a consistent system, ascending.
    """
    found: list[int] = []
    for drop in range(len(matrix)):
        reduced = [row for index, row in enumerate(matrix) if index != drop]
        constants = [value for index, value in enumerate(rhs) if index != drop]
        if solve_linear(reduced, constants).outcome != OUTCOME_INCONSISTENT:
            found.append(drop)
    return tuple(found)


def _closed_loop(length: int) -> tuple[list[list[Fraction]], list[Fraction]]:
    """A closed production loop of ``length`` steps, asked for a net output.

    Every item is produced by one step and consumed by the next, so the loop can
    balance at any scale and can yield NOTHING. Demanding output from it is
    therefore inconsistent, and no row is all-zero - which is what puts the
    system on the expensive path rather than on the cheap all-zero check that
    precedes it in the caller.

    Args:
        length: How many steps the loop has. One row per step, plus the demand.

    Returns:
        The matrix and the right-hand side.
    """
    matrix: list[list[Fraction]] = []
    for step in range(length):
        row = [F0] * length
        row[step] += F1
        row[(step + 1) % length] -= F1
        matrix.append(row)
    demand = [F0] * length
    demand[0] += F1
    demand[1 % length] -= F1
    matrix.append(demand)
    return matrix, [F0] * length + [Fraction(10)]


def test_isolating_rows_answers_exactly_what_the_leave_one_out_loop_answered() -> None:
    """The equivalence the replacement rests on, against the loop it replaced.

    The corpus is deliberately dense with DEPENDENT rows - scaled copies of
    earlier ones - because that is what makes the left null space more than one
    dimensional, and a criterion that happens to work on a single dependency is
    not the same as one that works. A system nobody can fix by striking one row
    is a real case here, not a hypothetical: both answers must be empty.
    """
    checked = 0
    for seed in range(240):
        matrix, rhs = _pseudo_random_system(seed)
        if solve_linear(matrix, rhs).outcome != OUTCOME_INCONSISTENT:
            continue
        checked += 1
        assert isolating_rows(matrix, rhs) == _brute_force_isolating(matrix, rhs), (
            f"seed {seed} disagrees with the oracle"
        )
    assert checked >= _MIN_INCONSISTENT, (
        f"only {checked} of the corpus was inconsistent; the arm is too thin to mean anything"
    )


def test_isolating_rows_reports_nothing_for_a_system_that_has_a_solution() -> None:
    """A consistent system has no row worth striking, and says so by being empty.

    Returning a row here would be worse than useless: the caller reads a
    non-empty answer as "this is the equation that cannot be met".
    """
    assert isolating_rows(_MATRIX, _RHS) == ()


def test_isolating_rows_is_empty_when_no_single_row_isolates_the_contradiction() -> None:
    """TWO independent contradictions, so striking either one leaves the other.

    ``x = 1`` beside ``x = 2`` is one contradiction and ``y = 1`` beside ``y = 2``
    is a second, and they share no variable. Remove any single row and the other
    pair is still there, so no row isolates anything and the honest answer is
    empty rather than an arbitrary index.

    THE FIRST FIXTURE WRITTEN HERE DID THE OPPOSITE AND A VERIFIER CAUGHT IT.
    It was ``x + y = 1``, ``y + z = 1``, ``x + z = 1`` and ``x + y + z = 2``,
    described as a contradiction no single row isolates. It is the reverse: each
    of those rows CAN be struck to leave a satisfiable system, so every index is
    isolating and the arm was measuring ``(0, 1, 2, 3)`` while its name and its
    docstring both said empty. It passed anyway, because its only assertion was
    equality with the oracle - which is exactly why the case below asserts the
    empty tuple DIRECTLY as well. An arm whose whole claim is delegated to an
    oracle cannot notice that it is pointed at the wrong system.
    """
    matrix = [[F1, F0], [F1, F0], [F0, F1], [F0, F1]]
    rhs = [F1, Fraction(2), F1, Fraction(2)]

    assert solve_linear(matrix, rhs).outcome == OUTCOME_INCONSISTENT
    assert isolating_rows(matrix, rhs) == ()
    assert isolating_rows(matrix, rhs) == _brute_force_isolating(matrix, rhs)


def test_isolating_rows_names_every_row_when_every_row_isolates() -> None:
    """The opposite end of the same axis, and the fixture that taught it.

    Three rows that are pairwise satisfiable and jointly impossible - ``x + y``,
    ``y + z`` and ``x + z`` each one, against ``x + y + z`` two - are contradicted
    as a SET. Striking any one of the four leaves a system with a solution, so
    EVERY index is isolating and the answer is the full tuple.

    This is the case the empty-answer arm above was mistakenly written against.
    Keeping it, under a name that says what it does, is worth more than deleting
    it: it is the only fixture here whose answer is every row rather than none or
    one, and it pins the end of the range the criterion has to span.
    """
    matrix = [
        [F1, F1, F0, F0],
        [F0, F1, F1, F0],
        [F1, F0, F1, F0],
        [F1, F1, F1, F0],
    ]
    rhs = [F1, F1, F1, Fraction(2)]

    assert solve_linear(matrix, rhs).outcome == OUTCOME_INCONSISTENT
    assert isolating_rows(matrix, rhs) == (0, 1, 2, 3)
    assert isolating_rows(matrix, rhs) == _brute_force_isolating(matrix, rhs)


def test_isolating_rows_holds_on_rows_that_have_no_coefficients_at_all() -> None:
    """A system of zero-width rows is a real shape, not a degenerate one to guard.

    ``ratio.py`` builds exactly this when every selected recipe is excluded: no
    recipe means no variable means no column, and what is left is a demand with
    nothing at all on the other side. The rows carry no coefficients, so every
    one of them is trivially a left null vector and the whole question falls to
    the constants - which is the thinnest the criterion ever gets and therefore
    the place an off-by-one in it would show first.

    The oracle answers each case beside the implementation, so the arm states no
    expected tuple of its own and cannot drift away from the definition.
    """
    cases: tuple[tuple[list[list[Fraction]], list[Fraction]], ...] = (
        ([[]], [F1]),
        ([[], []], [F0, F1]),
        ([[], []], [F1, F1]),
        ([[], [], []], [F1, F0, Fraction(2)]),
        ([[F1, F0], [F0, F0]], [F1, Fraction(5)]),
    )
    for matrix, rhs in cases:
        assert solve_linear(matrix, rhs).outcome == OUTCOME_INCONSISTENT, (
            f"{matrix} over {rhs} is not on the refusal path, so this case proves nothing"
        )
        assert isolating_rows(matrix, rhs) == _brute_force_isolating(matrix, rhs), (
            f"{matrix} over {rhs} disagrees with the oracle"
        )


def test_isolating_rows_is_empty_for_a_system_with_no_equations() -> None:
    """No equations cannot contradict, so there is no row to strike.

    The oracle is NOT consulted here, and the reason is the whole of why it is
    guarded everywhere else: it defines an isolating row as one whose removal
    leaves a consistent system, which every row of an ALREADY consistent system
    satisfies vacuously. It is an oracle for inconsistent systems only.
    """
    assert isolating_rows([], []) == ()
    assert isolating_rows([[F1]], [F3]) == ()


def test_isolating_rows_does_not_grow_its_work_with_the_row_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE CS-302 acceptance, stated as a count rather than as a clock.

    A wall-clock bound on this machine is a statement about this machine. What
    the item actually measured is that the old diagnosis ran ONE FULL
    ELIMINATION PER ROW, so the property to pin is that the new one runs a fixed
    number of them regardless of how many rows there are. The oracle beside it
    is the old cost, and it is asserted to grow so that the comparison cannot
    quietly become a comparison of two constants.
    """
    small_matrix, small_rhs = _closed_loop(_SMALL_CHAIN)
    large_matrix, large_rhs = _closed_loop(_LARGE_CHAIN)

    assert solve_linear(small_matrix, small_rhs).outcome == OUTCOME_INCONSISTENT
    assert solve_linear(large_matrix, large_rhs).outcome == OUTCOME_INCONSISTENT

    small_cost = _eliminations_during(monkeypatch, lambda: isolating_rows(small_matrix, small_rhs))
    large_cost = _eliminations_during(monkeypatch, lambda: isolating_rows(large_matrix, large_rhs))
    assert small_cost == large_cost == 1, (
        f"isolating_rows eliminated {small_cost} and {large_cost} times; it must be one each"
    )

    old_small = _eliminations_during(
        monkeypatch, lambda: _brute_force_isolating(small_matrix, small_rhs)
    )
    old_large = _eliminations_during(
        monkeypatch, lambda: _brute_force_isolating(large_matrix, large_rhs)
    )
    assert old_large > old_small, (
        "the oracle did not get more expensive with the row count, so this arm is comparing two "
        "constants and would pass against the very implementation it exists to reject"
    )
