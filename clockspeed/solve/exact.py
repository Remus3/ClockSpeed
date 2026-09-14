"""Exact rational primitives, and the invariant that no float enters the solve path.

Per docs/ARCHITECTURE.md this module owns non-negotiable 6 - exact rational
arithmetic, with the ABSENCE of floats asserted rather than assumed. It sits at
the bottom of the solve layer and imports nothing from ``clockspeed`` at all,
which is what lets the arithmetic be reasoned about and tested on its own,
independently of the shape of the game data it is eventually applied to.

WHY THIS IS A CORRECTNESS PROBLEM AND NOT A ROUNDING ONE
---------------------------------------------------------
A ratio calculator that drifts does not report a slightly wrong number. It
reports a building count that is 3.9999999999999996 and gets floored to 3, or a
belt that is 0.4 items per minute short of saturated, and every one of those is
a confident answer with no signal attached. The failures below are all of that
shape: they produce the right TYPE, a plausible VALUE, and no error.

THE MEASURED TRAPS
------------------
- **``Fraction ** Fraction`` SILENTLY RETURNS A FLOAT.** Measured on CPython
  3.14: ``Fraction(5, 2) ** Fraction('1.321929')`` returns ``<class 'float'>``
  ``3.3577506181236285``. It does not raise and it does not warn, because
  x^(1321929/1000000) is irrational for essentially every rational x and there
  is no exact rational answer to return. This matters because
  ``draw * clock ** exponent`` is the most natural way anyone would write the
  power law, it reads as exact, and it cannot be.
  Worse, the defect is DATA-DEPENDENT: ``Fraction(5, 2) ** Fraction(2, 1)``
  returns a Fraction, so a test written with a whole-number exponent passes
  while the shipped 1.321929 exponent quietly returns a float. That is why this
  module contains no ``**``, no ``pow`` and no ``math`` import, offers no helper
  that invites one, and publishes :class:`DeferredPowerTerm` as a SYMBOLIC
  record instead - a caller that wants a number out of it has to confront the
  fact that there is no exact one.

- **``float()`` succeeds on every decimal string the game ships.**
  ``Fraction(0.1)`` also succeeds, and yields
  3602879701896397/36028797018963968 - an exact reading of the binary
  approximation and a wrong reading of the decimal. It is exact AND wrong, so no
  downstream exactness check can detect it. :func:`to_exact` therefore refuses a
  non-string outright rather than converting it, which is the only point at
  which the mistake is visible. The same conversion discipline is already in
  force one layer down in ``clockspeed/data/registry.py``.

- **Mixed arithmetic returns a float without complaint.** ``Fraction(60) / 0.5``
  is the float ``120.0``. One float operand anywhere in an expression converts
  the whole result, so a single unaudited input poisons every value derived from
  it while looking entirely correct.

- **``int / int`` is a float.** ``1 / 2`` is ``0.5``. An all-int matrix contains
  no floats and MANUFACTURES them the moment a pivot row is normalized, so
  "there are no floats in the input" is not the same claim as "the arithmetic
  will stay exact". :func:`solve_linear` requires Fraction entries specifically.

WHY THE AUDIT ASSERTS POSITIVELY
--------------------------------
:func:`audit_exact` tests ``type(value) is Fraction`` and never
``not isinstance(value, float)``. Two measured reasons, and each closes a hole
the other leaves open:

- ``isinstance(True, int)`` is ``True``, so an isinstance-based audit admits a
  bool wherever a number belongs. The same asymmetry admits any int subclass -
  an ``IntEnum`` member passes ``isinstance(x, int)`` and fails
  ``type(x) is int``.
- A negative float check admits ``Decimal``, a numpy scalar, and a plain ``int``
  where a Fraction was promised. ``Decimal`` is the sharpest of those: it is
  exact for decimal fractions, cannot represent 1/3, and so rounds silently
  inside a ratio solve - arriving through the exact hole a float check leaves.

Leaves are admitted by TYPE IDENTITY; containers are recognized by
``isinstance``. That looks inconsistent and is not. A container gets traversed,
so nothing can hide inside one - its contents are audited individually. A leaf
is where a wrong type actually hides, so a leaf is admitted only on its own
exact identity. Anything matching neither list is REFUSED rather than skipped:
an unrecognized shape fails loudly instead of being walked past, which is the
safe direction for a guard.

The rejection names the PATH to the offending leaf - ``plan.steps[2].rate`` -
because the values that matter arrive inside a plan object rather than as bare
scalars, and a rejection that says only "a float is in here somewhere" is a
rejection nobody can act on.

WHY THE PIVOT RULE IS WHAT IT IS
--------------------------------
:func:`solve_linear` selects the LOWEST ROW INDEX with a nonzero entry, scanning
columns left to right. Two rules, both load-bearing, both about what the
alternatives silently destroy.

- **The only admissible pivot test is ``entry != 0``, exact.** An
  ``abs(entry) > eps`` test is unsound here rather than merely loose: fluid
  amounts normalize through a division by 1000 and a chain compounds it, so a
  genuinely small exact coefficient is ordinary input. Any epsilon large enough
  to be useful discards one, and discarding a coefficient does not produce a
  small error - it drops the entire equation and reports the thinner system
  under a confident name.

- **Never pivot by magnitude.** Partial pivoting exists solely to control
  floating-point roundoff, and there is no roundoff. What a magnitude rule buys
  instead is an output that depends on value comparisons, so an
  equivalent-but-differently-scaled input eliminates in a different order.
  Determinism is a product property (CLAUDE.md section 1: two runs on the same
  input disagreeing is a bug), and this is the rule that keeps it a property of
  the arithmetic rather than of the caller's units.

Note that with exact arithmetic the reduced row echelon form is UNIQUE, so a
magnitude rule computes the identical answer by different work. That makes the
rule invisible in this function's return value and testable only at the
selector, which is why ``_pivot_row`` exists as a named function rather than as
an inline loop. A contract with no test is the CONVENTIONS.md section 7.2 unrun
gate, and this one cannot be tested any other way.

THREE OUTCOMES, NEVER COLLAPSED
-------------------------------
``unique``, ``inconsistent`` and ``underdetermined`` are distinguished by name
and :attr:`LinearSolution.values` is None for the latter two. Returning a vector
for an underdetermined system is the failure mode that renders as a
correct-looking factory plan: pinning the free variables to zero produces a full
vector of exact Fractions that satisfies every equation and is one arbitrary
member of an infinite family. Nothing downstream can tell it from the answer.

Inconsistent outranks underdetermined when a system is both, because an
inconsistent system has ZERO solutions while an underdetermined one has
infinitely many. Reporting the first as the second sends the caller looking for
the best member of an empty set.

:class:`LinearSolution` deliberately publishes NO row index. Every field it does
publish - the solution vector, the rank, the pivot and free columns - is a
property of the system rather than of the row order, so a row-permuted or
row-scaled copy of the same system produces byte-identical output. A row index
is the one thing a permutation moves. It would also be arbitrary: an
inconsistency is a property of the row SPACE, and any one of the dependent rows
could equally be blamed for it.

WHY NEITHER ERROR IS A ValueError
---------------------------------
:func:`to_exact` raises ValueError for a malformed string, so a caller will
reasonably wrap it in ``except ValueError``. If :class:`InexactValueError` were
in that hierarchy, the handler written for bad text would silently absorb the
one signal that says the solve path has been poisoned. This is the same
reasoning that keeps ``RegistryIntegrityError`` out of the ValueError hierarchy
in ``clockspeed/data/registry.py``, and it is the difference between a guard and
a guard someone else's ``except`` clause turns off.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from types import NoneType
from typing import Final

__all__ = [
    "OUTCOME_INCONSISTENT",
    "OUTCOME_UNDERDETERMINED",
    "OUTCOME_UNIQUE",
    "SECONDS_PER_MINUTE",
    "DeferredPowerTerm",
    "ExactArithmeticError",
    "InexactValueError",
    "LinearSolution",
    "UndefinedRateError",
    "audit_exact",
    "isolating_rows",
    "per_minute",
    "solve_linear",
    "to_exact",
]

# ---------------------------------------------------------------------------
# Unit definitions
# ---------------------------------------------------------------------------

#: Seconds in a minute. A UNIT DEFINITION and not a balance value, which is why
#: it is a constant here rather than a configurable: no game patch can change
#: it, and nothing downstream may restate it. Recipe durations are shipped in
#: seconds and every rate this project reports is per minute, so this factor
#: appears in the middle of the single most common conversion in the codebase -
#: exactly the number that gets typed inline in six places and mistyped in one.
SECONDS_PER_MINUTE: Final = 60

# ---------------------------------------------------------------------------
# Linear solve outcomes
# ---------------------------------------------------------------------------

#: Exactly one solution. :attr:`LinearSolution.values` carries it.
OUTCOME_UNIQUE: Final = "unique"

#: No solution at all - a row whose coefficients are all zero over a nonzero
#: right-hand side. The equations contradict each other.
OUTCOME_INCONSISTENT: Final = "inconsistent"

#: Infinitely many solutions - rank below the variable count.
#: :attr:`LinearSolution.free_variables` names which columns are unconstrained.
OUTCOME_UNDERDETERMINED: Final = "underdetermined"

# ---------------------------------------------------------------------------
# The exactness allow-list
# ---------------------------------------------------------------------------

#: The types a leaf may be. Membership is tested by IDENTITY, never by
#: ``isinstance``, so no subclass slips through: a bool is admitted as a bool
#: and never by way of int, and an IntEnum member is admitted as neither.
#:
#: ``Fraction`` is the exact numeric type. ``int`` is exact and is what counts,
#: indices and ranks are. ``bool`` is a flag. ``str`` is a key or a name.
#: ``NoneType`` is a modeled absence, which this project keeps distinct from
#: zero throughout. ``float`` and ``Decimal`` are absent on purpose.
_EXACT_LEAF_TYPES: Final[frozenset[type]] = frozenset({Fraction, int, bool, str, NoneType})


class ExactArithmeticError(Exception):
    """Base class for every failure this module raises.

    Deliberately NOT a :class:`ValueError`. See the module docstring: a caller
    catching ValueError around :func:`to_exact` is catching a malformed string,
    and it must not also catch the exactness canary.
    """


class InexactValueError(ExactArithmeticError):
    """A value that must be exact is not, or is not exact in the required way.

    Raised for a float, a Decimal, an int where a Fraction was promised, or any
    type outside the module's allow-list. The message names the PATH to the
    offending leaf so the caller can find it inside a nested plan object.
    """


class UndefinedRateError(ExactArithmeticError):
    """A rate was requested for a cycle of zero duration.

    A real input rather than a defensive branch: ``clockspeed/data/registry.py``
    keeps a MEASURED zero on ``Recipe.duration`` deliberately, skipping only an
    ABSENT duration, precisely so that a genuine zero stays distinguishable from
    a defaulted one. Build-gun recipes carry it.
    """


@dataclass(frozen=True)
class DeferredPowerTerm:
    """A power law held symbolically, because it has no exact rational value.

    The overclock power law is ``draw * clock ** exponent`` and the shipped
    exponent is 1.321929, so the middle term is irrational for essentially every
    clock speed. This record exists so that a caller who needs that term has
    something to REACH FOR other than the ``**`` operator, which would silently
    hand back a float (see the module docstring for the measured value).

    It models only ``base ** exponent`` - the sub-expression that cannot be
    exact. Whatever multiplies it stays an ordinary Fraction in the caller,
    where it is still exact.

    It carries no evaluation method, and that is the whole point: publishing an
    evaluable term would reintroduce the defect behind a nicer name. Deciding
    what to do with an irrational term - carry it symbolically, bound it, or
    round it once at the presentation edge with the rounding recorded - belongs
    to the layer that knows what the number is for, not here.

    Attributes:
        base: The quantity being raised, exact.
        exponent: The power it is raised to, exact. Exact as an operand; the
            RESULT of applying it is what has no exact value.
    """

    base: Fraction
    exponent: Fraction


@dataclass(frozen=True)
class LinearSolution:
    """The outcome of one exact linear solve, with the three cases never collapsed.

    Every field is invariant under row permutation and row scaling, so two
    writings of the same system produce byte-identical output. That is not a
    coincidence - it is why no row index is published. See the module docstring.

    Attributes:
        outcome: One of :data:`OUTCOME_UNIQUE`, :data:`OUTCOME_INCONSISTENT` or
            :data:`OUTCOME_UNDERDETERMINED`.
        values: The solution in column order, or None. None for both non-unique
            outcomes, and None rather than a zero-filled vector: an
            underdetermined system pinned to zero yields exact Fractions that
            satisfy every equation and are one arbitrary member of an infinite
            family, which nothing downstream could tell from the answer. The
            empty tuple is a real value - the unique solution over zero
            variables - and is therefore not usable as the absent signal.
        free_variables: Column indices with no pivot, in ascending order.
            Populated only for :data:`OUTCOME_UNDERDETERMINED`: free variables
            describe a solution FAMILY, and an inconsistent system has none.
        rank: The number of pivots found, which is the rank of the coefficient
            matrix.
    """

    outcome: str
    values: tuple[Fraction, ...] | None
    free_variables: tuple[int, ...]
    rank: int


def _reject_inexact(value: object, path: str) -> None:
    """Refuse anything that is not exactly a :class:`~fractions.Fraction`.

    Stricter than :func:`audit_exact`, and the two answer different questions.
    This one is asked at a specific arithmetic operand, where ``int`` is not
    good enough: ``1 / 2`` is the float 0.5, so an int operand does not merely
    fail to be a Fraction, it MANUFACTURES a float out of an input that
    contained none.

    Args:
        value: The operand to check.
        path: How to name it in the message.

    Raises:
        InexactValueError: The value is not exactly a Fraction. Identity, not
            ``isinstance``, so a Fraction subclass is refused too - it may have
            overridden the arithmetic this module depends on.
    """
    if type(value) is not Fraction:
        raise InexactValueError(
            f"{path} is {type(value).__name__} {value!r}, not a Fraction; the solve path is "
            "exact rational arithmetic end to end and mixed arithmetic silently returns a float"
        )


def _audit(value: object, path: str, seen: set[int]) -> None:
    """Walk one value, refusing the first inexact leaf and naming where it is.

    Args:
        value: The value or container to walk.
        path: The dotted and indexed path reached so far.
        seen: Ids of the containers already walked, so a self-referential
            structure terminates instead of exhausting the stack. Ids are safe
            to compare here because every container reached is held alive by the
            root for the whole traversal, so none can be collected and have its
            id reused mid-walk.

    Raises:
        InexactValueError: A leaf is not an admitted exact type, or a container
            is of a shape this module does not model.
    """
    if type(value) in _EXACT_LEAF_TYPES:
        return

    if id(value) in seen:
        return
    seen.add(id(value))

    if is_dataclass(value) and not isinstance(value, type):
        for member in fields(value):
            _audit(getattr(value, member.name), f"{path}.{member.name}", seen)
        return

    if isinstance(value, Mapping):
        for index, (key, item) in enumerate(value.items()):
            _audit(key, f"{path}.keys()[{index}]", seen)
            _audit(item, f"{path}[{key!r}]", seen)
        return

    if isinstance(value, tuple | list):
        for index, item in enumerate(value):
            _audit(item, f"{path}[{index}]", seen)
        return

    raise InexactValueError(
        f"{path} is {type(value).__name__} {value!r}, which the solve path does not admit; "
        "leaves may be Fraction, int, bool, str or None, and containers may be dataclasses, "
        "mappings, tuples or lists"
    )


def audit_exact(value: object, *, path: str = "value") -> None:
    """Assert that nothing inexact is reachable from a value, and say where if it is.

    The runtime half of non-negotiable 6. Recurses into dataclasses, mappings,
    tuples and lists because the values that matter arrive inside a plan object
    rather than as bare scalars, and reports the full path to the offending leaf
    so the caller can find it.

    Leaves are admitted by type IDENTITY and containers by ``isinstance``. See
    the module docstring for why that asymmetry is deliberate, and for the
    measured reasons a negative ``not isinstance(x, float)`` check is not a
    substitute.

    This asks "is anything inexact reachable from here". It does NOT ask "is
    this particular field a Fraction" - ``int`` is an admitted leaf, since
    counts and ranks are legitimately ints. Where a specific operand must be a
    Fraction, the check is ``type(x) is Fraction`` at that operand, which is
    what :func:`per_minute` and :func:`solve_linear` do.

    Args:
        value: Any value or structure.
        path: What to call the root in a failure message. Pass the name the
            caller knows it by - ``audit_exact(plan, path="plan")`` reports
            ``plan.steps[2].rate`` rather than ``value.steps[2].rate``.

    Raises:
        InexactValueError: Naming the path to the first offending leaf.
    """
    _audit(value, path, set())


def to_exact(text: str) -> Fraction:
    """Convert a decimal string straight to an exact Fraction, never via float.

    Straight, meaning the string is handed to :class:`~fractions.Fraction`
    unmodified. ``float('1.321929')`` succeeds and substitutes the nearest
    binary approximation, and 1.321929 is not representable in binary floating
    point.

    A non-string argument is REFUSED rather than converted, and that refusal is
    the whole reason this function exists as more than an alias.
    ``Fraction(0.1)`` succeeds and returns 3602879701896397/36028797018963968:
    an exact reading of the binary approximation and a wrong reading of the
    decimal. Exact and wrong is invisible to every downstream exactness check,
    so the front door is the only place it can be caught.

    Args:
        text: The verbatim decimal string, exactly as the shipped game data or a
            caller stated it.

    Returns:
        The exact value.

    Raises:
        InexactValueError: The argument is not a ``str``.
        ValueError: The string is not a number. Deliberately propagated from
            Fraction rather than rewrapped, so "you gave me bad text" stays a
            different class of event from "you gave me a float".
        ZeroDivisionError: The string is a ratio with a zero denominator.
    """
    if type(text) is not str:
        raise InexactValueError(
            f"to_exact takes a decimal string, not {type(text).__name__} {text!r}; converting a "
            "float here would read its binary approximation exactly and the decimal wrongly"
        )
    return Fraction(text)


def per_minute(amount: Fraction, duration: Fraction) -> Fraction:
    """Convert an amount per cycle into an exact amount per minute.

    Args:
        amount: The amount produced or consumed per cycle.
        duration: The cycle length in seconds, as the shipped recipe states it.

    Returns:
        ``amount * SECONDS_PER_MINUTE / duration``, exact.

    Raises:
        InexactValueError: Either operand is not exactly a Fraction. A float
            duration is the case that matters: ``Fraction(60) / 0.5`` returns
            the float 120.0, which is the right number with the invariant
            already lost, and nothing downstream raises on it.
        UndefinedRateError: The duration is zero. A rate per cycle of no
            duration is not a large number, it is undefined, and the registry
            keeps measured zeros rather than discarding them.
    """
    _reject_inexact(amount, "amount")
    _reject_inexact(duration, "duration")
    if duration == 0:
        raise UndefinedRateError(
            "a cycle of zero duration has no rate per minute; the registry keeps a measured "
            "zero duration deliberately, so this is real input and not a defensive branch"
        )
    return amount * SECONDS_PER_MINUTE / duration


def _pivot_row(work: Sequence[Sequence[Fraction]], start_row: int, column: int) -> int | None:
    """Select the pivot row for one column: lowest row index with a nonzero entry.

    A named function rather than an inline loop because with exact arithmetic
    the reduced row echelon form is unique, so a magnitude rule produces the
    identical answer by different work and is invisible in
    :func:`solve_linear`'s output. This is the only place the rule can be
    tested, and an untested rule is one somebody optimizes away.

    The test is ``!= 0``, exact. See the module docstring for why an epsilon is
    unsound rather than merely loose, and why magnitude ordering would trade
    determinism for a roundoff protection that has nothing to protect against.

    Args:
        work: The coefficient rows being eliminated.
        start_row: The first row still available as a pivot. Rows above it are
            already pivoted and must not be disturbed.
        column: The column to find a pivot in.

    Returns:
        The lowest available row index whose entry in ``column`` is nonzero, or
        None when the column is entirely zero from ``start_row`` down - which
        makes it a free variable rather than an error.
    """
    for row in range(start_row, len(work)):
        if work[row][column] != 0:
            return row
    return None


def _validate_system(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> int:
    """Check the shape and the exactness of a system before eliminating anything.

    Args:
        matrix: The coefficient rows.
        rhs: The right-hand side, one constant per row.

    Returns:
        The number of columns, which is zero for a system with no rows.

    Raises:
        ValueError: The rows are ragged, or the right-hand side is not one
            constant per equation. Both are caller bugs, and truncating to the
            shorter of the two would silently solve a system nobody described.
        InexactValueError: Any entry is not exactly a Fraction, naming its
            position. An all-int matrix is refused for a reason that is not
            pedantry: normalizing a pivot row of ints uses ``/``, and
            ``1 / 2`` is the float 0.5.
    """
    if len(rhs) != len(matrix):
        raise ValueError(
            f"the right-hand side has {len(rhs)} constants for {len(matrix)} equations; "
            "there must be exactly one per equation"
        )
    column_count = len(matrix[0]) if matrix else 0
    for row_index, row in enumerate(matrix):
        if len(row) != column_count:
            raise ValueError(
                f"the matrix is ragged: row {row_index} has {len(row)} coefficients and row 0 "
                f"has {column_count}"
            )
        for column_index, entry in enumerate(row):
            _reject_inexact(entry, f"matrix[{row_index}][{column_index}]")
    for row_index, constant in enumerate(rhs):
        _reject_inexact(constant, f"rhs[{row_index}]")
    return column_count


def solve_linear(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> LinearSolution:
    """Solve a linear system by exact Gauss-Jordan elimination over Fraction.

    Reduces to row echelon form with the pivot rule in :func:`_pivot_row`:
    columns scanned left to right, and within a column the LOWEST available row
    index with a nonzero entry. No epsilon and no magnitude comparison anywhere.

    The three outcomes are reported by name and are never collapsed. Both
    non-unique outcomes carry ``values=None`` rather than a vector, because a
    plausible-looking vector for a system that does not have one is the failure
    mode that renders as a correct-looking factory plan.

    Args:
        matrix: The coefficient rows. Every entry must be exactly a Fraction.
        rhs: One constant per equation, each exactly a Fraction.

    Returns:
        The solution. ``unique`` carries the vector in column order;
        ``inconsistent`` and ``underdetermined`` carry None, and the latter
        names the free columns. A system with no equations is vacuously unique
        over zero variables and returns an empty vector, which is a real answer
        rather than an absent one.

    Raises:
        ValueError: The system is ragged or the right-hand side is the wrong
            length.
        InexactValueError: An entry is not exactly a Fraction.
    """
    column_count = _validate_system(matrix, rhs)
    row_count = len(matrix)

    work = [list(row) for row in matrix]
    constants = list(rhs)
    pivot_columns: list[int] = []
    free_columns: list[int] = []
    next_row = 0

    for column in range(column_count):
        # No special case for "every row is already pivoted": the range in
        # _pivot_row is empty then, it reports None, and the column is free -
        # which is exactly right.
        found = _pivot_row(work, next_row, column)
        if found is None:
            free_columns.append(column)
            continue

        work[next_row], work[found] = work[found], work[next_row]
        constants[next_row], constants[found] = constants[found], constants[next_row]

        scale = work[next_row][column]
        work[next_row] = [entry / scale for entry in work[next_row]]
        constants[next_row] = constants[next_row] / scale

        for other in range(row_count):
            if other == next_row:
                continue
            factor = work[other][column]
            if factor == 0:
                continue
            work[other] = [
                entry - factor * pivot
                for entry, pivot in zip(work[other], work[next_row], strict=True)
            ]
            constants[other] = constants[other] - factor * constants[next_row]

        pivot_columns.append(column)
        next_row += 1

    # Tested over every row rather than only the rows below the last pivot: the
    # definition of an inconsistency is a row that constrains nothing and
    # demands something, and reading it off a row index would make it depend on
    # where elimination happened to leave things.
    inconsistent = any(
        constants[row] != 0 and all(entry == 0 for entry in work[row]) for row in range(row_count)
    )

    if inconsistent:
        # Ranked above underdetermined deliberately: a system that is both has
        # ZERO solutions, and reporting a solution family would send the caller
        # looking for the best member of an empty set.
        return LinearSolution(
            outcome=OUTCOME_INCONSISTENT, values=None, free_variables=(), rank=next_row
        )

    if free_columns:
        return LinearSolution(
            outcome=OUTCOME_UNDERDETERMINED,
            values=None,
            free_variables=tuple(free_columns),
            rank=next_row,
        )

    # Reachable only when every column took a pivot, so every entry below is
    # written from a pivot row and none of the initial zeros survives. The
    # initializer is a placeholder for the loop, never a pinned free variable.
    values = [Fraction(0)] * column_count
    for row, column in enumerate(pivot_columns):
        values[column] = constants[row]
    return LinearSolution(
        outcome=OUTCOME_UNIQUE, values=tuple(values), free_variables=(), rank=next_row
    )


def isolating_rows(
    matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]
) -> tuple[int, ...]:
    """Row indices whose removal leaves a consistent system, ascending.

    THE ONE FUNCTION HERE THAT PUBLISHES ROW INDICES, and the reason it may is
    that it answers a different question from :func:`solve_linear`. That function
    answers "does this system have a solution", which is a property of the row
    SPACE and is invariant under permutation - publishing an index there would
    hand the caller an answer that moved when the equations were reordered. This
    one answers "which of the equations YOU wrote could be struck out to make the
    rest satisfiable", which is a question ABOUT the caller's rows and has no
    permutation-invariant form at all. Two questions, two functions, and the
    indices never leak from this one into that one.

    WHY THIS IS NOT A LOOP OF SOLVES - CS-302. The obvious implementation drops
    one row at a time and re-solves, which is one full elimination per row. That
    was measured against the live registry, where the system is 750 rows by 872
    columns: one elimination there takes seconds, and seven hundred and fifty of
    them take an hour to explain a refusal the solve itself reached in seconds.
    So the elimination runs ONCE here, carrying the transform that produced it.

    WHAT THE TRANSFORM GIVES. Every row whose coefficients vanish under
    elimination is a left null vector ``y`` of the matrix, written in ORIGINAL
    row order, and the constant beside it is ``y . rhs``. Those vectors are
    independent, because the accumulated transform is a product of elementary
    row operations and is therefore invertible, so they are a BASIS of the left
    null space ``N``.

    THE TEST EACH ROW IS PUT TO. Write ``f(y) = y . rhs``, a linear functional on
    ``N``. The system is inconsistent exactly when ``f`` is not identically zero.
    Striking row ``i`` leaves ``N_i = {y in N : y[i] == 0}``, and the reduced
    system is consistent exactly when ``f`` vanishes on ``N_i``. Both ``N_i`` and
    the kernel of ``f`` have codimension at most one in ``N``, so that happens
    exactly when the coordinate functional ``y -> y[i]`` is a NONZERO multiple of
    ``f`` on ``N``. That is a column comparison against the constants - no solve.
    The zero multiple is excluded deliberately: it is the case where row ``i``
    takes no part in any contradiction, and striking it changes nothing.

    Args:
        matrix: The coefficient rows. Every entry must be exactly a Fraction.
        rhs: One constant per equation, each exactly a Fraction.

    Returns:
        The isolating row indices, ascending. EMPTY for a system that already
        has a solution, and empty for one whose contradiction no single row
        isolates - three or more mutually dependent rows do that, and the caller
        is left to say so rather than handed an arbitrary index.

    Raises:
        ValueError: The system is ragged or the right-hand side is the wrong
            length.
        InexactValueError: An entry is not exactly a Fraction.
    """
    column_count = _validate_system(matrix, rhs)
    row_count = len(matrix)

    work = [list(row) for row in matrix]
    constants = list(rhs)
    # The transform, accumulated beside the coefficients. Row i starts as one
    # times original row i, which is the identity, and every operation below is
    # applied to it in lockstep with the row it came from.
    transform = [
        [Fraction(1) if source == row else Fraction(0) for source in range(row_count)]
        for row in range(row_count)
    ]
    next_row = 0

    for column in range(column_count):
        found = _pivot_row(work, next_row, column)
        if found is None:
            continue

        work[next_row], work[found] = work[found], work[next_row]
        constants[next_row], constants[found] = constants[found], constants[next_row]
        transform[next_row], transform[found] = transform[found], transform[next_row]

        scale = work[next_row][column]
        work[next_row] = [entry / scale for entry in work[next_row]]
        constants[next_row] = constants[next_row] / scale
        transform[next_row] = [entry / scale for entry in transform[next_row]]

        for other in range(row_count):
            if other == next_row:
                continue
            factor = work[other][column]
            if factor == 0:
                continue
            work[other] = [
                entry - factor * pivot
                for entry, pivot in zip(work[other], work[next_row], strict=True)
            ]
            constants[other] = constants[other] - factor * constants[next_row]
            transform[other] = [
                entry - factor * pivot
                for entry, pivot in zip(transform[other], transform[next_row], strict=True)
            ]

        next_row += 1

    # Tested over every row rather than from the last pivot down, for the reason
    # solve_linear states about the same scan: a row that constrains nothing is
    # defined by its contents, and reading it off an index would make the answer
    # depend on where elimination happened to leave things.
    vanished = [row for row in range(row_count) if all(entry == 0 for entry in work[row])]
    basis = [tuple(transform[row]) for row in vanished]
    witnessed = [constants[row] for row in vanished]

    if all(constant == 0 for constant in witnessed):
        return ()

    return tuple(index for index in range(row_count) if _is_isolating(basis, witnessed, index))


def _is_isolating(
    basis: Sequence[Sequence[Fraction]], witnessed: Sequence[Fraction], index: int
) -> bool:
    """Whether striking row ``index`` would leave the system consistent.

    The criterion is stated in :func:`isolating_rows`: the coordinate ``y[index]``
    must be one FIXED nonzero multiple of ``y . rhs`` across the whole basis. A
    basis vector whose constant is zero constrains the multiple not at all, so
    its coordinate has to be zero too - otherwise the two functionals disagree on
    that vector and no multiple exists.

    Args:
        basis: Left null vectors of the coefficient matrix, in original row
            order.
        witnessed: Each basis vector dotted with the right-hand side.
        index: The row to test.

    Returns:
        True when striking that row removes every contradiction.
    """
    multiple: Fraction | None = None
    for vector, constant in zip(basis, witnessed, strict=True):
        if constant == 0:
            if vector[index] != 0:
                return False
            continue
        here = vector[index] / constant
        if multiple is None:
            multiple = here
        elif multiple != here:
            return False
    return multiple is not None and multiple != 0
