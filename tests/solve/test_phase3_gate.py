"""The CS-300 phase 3 gate: properties the solve layer must be FORCED to have.

Every other module under ``tests/solve`` tests what a solver module DOES. This
one tests what the solver and its own test suite must never start doing. The
headline clause of the CS-300 acceptance criterion - "no floating-point
arithmetic anywhere in the solve path" - is a claim about code that was never
written as much as about code that was, and the only instrument that can make
that kind of claim is a scan that fails when the forbidden construct appears.

THE MECHANISM
-------------
Six sections, each a separate block below:

a. No ``*.py`` under ``clockspeed/solve/`` contains a float or complex literal,
   a reference to ``float`` or ``complex``, an exponentiation operator, a call
   to ``pow``/``round``/``divmod``, or an import of ``math``, ``cmath``,
   ``statistics``, ``decimal``, ``random``, ``numpy`` or ``scipy``. The same
   predicates hold over the pinned audit modules that decide on exact figures
   (``EXACT_AUDIT_SOURCES``, CS-1285).
b. Every one of those predicates is fed a synthetic source string containing
   exactly the construct it forbids, and asserted to flag it.
c. Importing any solve module pulls in no layer it may not reach, measured in a
   CHILD interpreter.
d. No solve module names a forbidden data-layer module in an ``import``
   statement, measured from source.
e. Nothing under ``tests/solve`` uses a tolerance.
f. The whole ``tests/solve`` suite passes with the install unresolvable.

THE SCAN IS OVER THE AST, NEVER OVER THE FILE TEXT, AND THAT IS LOAD-BEARING
----------------------------------------------------------------------------
``clockspeed/solve/exact.py`` and ``clockspeed/solve/power.py`` both quote the
measurement ``Fraction(5, 2) ** Fraction(exponent)`` VERBATIM in their module
docstrings, as the evidence for why the ban exists. The quotation is
digit-free because the exponent's one owner is the pin in
``clockspeed/data/version.py`` (CS-1030). A text sweep for ``**``
flags its own evidence: measured on this tree, a regex sweep for the banned
spellings reports 47 hits in ``exact.py`` alone, every one of them prose, and
zero of them defects. A guard that fires on the documentation explaining the
guard gets deleted within a week, and it deserves to be.

Under ``ast.parse`` a docstring is a single ``ast.Constant`` holding a ``str``.
Its contents are never parsed as operators, so the same file scans clean. A
comment is not in the tree at all. Both directions are pinned by
``test_the_scan_ignores_the_docstring_that_quotes_the_banned_measurement``,
which asserts against the REAL modules rather than against a synthetic stand-in.

WHAT THIS STATIC CHECK CANNOT SEE
---------------------------------
Stated plainly, because a gate whose limits are not written down gets read as
covering more than it does. Every construct below is invisible here:

- **A float arriving as a caller ARGUMENT.** ``ratio_solve(target=0.5)`` puts a
  float into the solve path without a single banned token appearing in
  ``clockspeed/solve/``. Nothing in this module can see across a call boundary.
- **A float returned by a stdlib call that is not on the ban list.** The list
  names the numeric modules; it cannot enumerate every function anywhere that
  happens to return a float.
- **Dynamic dispatch.** ``getattr(builtins, "flo" + "at")`` and any ``eval`` or
  ``exec`` construct resolve a name at runtime, and a name that does not exist
  until runtime is not an ``ast.Name``.
- **Operator overloading, which is the largest gap by far.** Measured on
  CPython 3.14.4: ``Fraction(1) / 0.5`` returns the float ``2.0`` and
  ``Fraction(1) * 1.0`` returns the float ``1.0``. One float operand converts
  the whole expression. ``/`` and ``*`` therefore CANNOT be banned - they are
  the arithmetic this layer exists to perform - so a float that reaches an
  operand poisons every value derived from it while every token in sight stays
  legal. Only a ``/`` whose two operands are ints by their spelling is banned
  (section (a)'s table says which spellings); a ``/`` over names is invisible.

WHICH INDEPENDENT SIGNAL COVERS EACH GAP
----------------------------------------
- ``clockspeed.solve.exact.audit_exact`` covers the argument gap, the unlisted
  stdlib gap and the overloading gap, at runtime and at the seams: it asserts
  ``type(value) is Fraction`` positively, so a float that arrived by any route
  fails the moment a seam audits it. Positive typing is deliberate -
  ``isinstance(True, int)`` is ``True``, so a negative ``not isinstance(x,
  float)`` audit admits a bool where a number belongs.
- The strict mypy rung on ``clockspeed.solve.*`` (``pyproject.toml``) covers the
  argument gap statically and earlier: it catches a ``float`` declared in a
  signature and flowing in from an annotated caller, which is the case neither
  the AST scan nor the runtime audit can see - the scan because the annotation
  lives in the CALLER, the audit because it only fires where a seam calls it.

THE RESIDUAL, WHICH NOTHING COVERS
----------------------------------
A float that enters through an unannotated or ``Any``-typed caller, flows only
through ``*`` and ``/``, and reaches a result that no seam passes to
``audit_exact``. All three conditions must hold at once. Adding an
``audit_exact`` call at each new seam is what keeps this residual shrinking;
there is no static instrument that closes it.

THIS MODULE'S OWN BOUNDARY
--------------------------
Section (b) needs synthetic source strings that CONTAIN the banned constructs,
and section (e) needs the banned tolerance words as data in order to hunt them.
Both are ordinary ``ast.Constant`` values and identifiers in THIS file. So:

- The section (a) scan is scoped to ``clockspeed/solve/`` plus the pinned
  ``EXACT_AUDIT_SOURCES`` under ``clockspeed/audit/``, and does not walk
  ``tests/``. If it were ever extended to cover the test tree it would flag this
  module, and the correct response would be to exclude this file explicitly, not
  to soften the predicates.
- The section (e) scan DOES cover ``tests/solve``, so it excludes this file by
  path - and that exclusion is not taken on trust.
  ``test_this_gate_is_excluded_from_the_tolerance_scan_and_would_otherwise_trip_it``
  runs the detector on this very file and asserts it produces hits, which turns
  the self-exclusion into a second detector proof against a real file instead of
  a hole (CONVENTIONS.md section 15.1: a guard can be green while self-excusing).

WHY THIS DUPLICATES tests/data/test_phase2_gate.py's CHILD-PROCESS HELPERS
-------------------------------------------------------------------------
``no_install_env`` and ``run_child`` are re-derived here rather than imported
from the phase 2 gate. That is deliberate. A shared helper between two gates is
a single point of failure that makes both wrong the same way, and agreement
between two checks that derive from one source is not evidence (CLAUDE.md
section 5). Each gate stands on its own.

Nothing here requires a game install and nothing here writes to one. Child
interpreters are launched through ``sys.executable`` so they inherit the running
interpreter rather than whatever a bare name resolves to on PATH.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from functools import cache
from pathlib import Path

import pytest

from clockspeed.data.locate import (
    ENV_ACCOUNT_DIR,
    ENV_GAME_DIR,
    ENV_LOCAL_CONFIG,
    ENV_SAVE_ROOT,
)

# ---------------------------------------------------------------------------
# Paths, derived rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SOLVE_PACKAGE = REPO_ROOT / "clockspeed" / "solve"
SOLVE_TESTS = REPO_ROOT / "tests" / "solve"

# This module's own path. The child pytest run below MUST exclude it or the gate
# re-runs itself forever, and the section (e) scan must exclude it for the reason
# given in the module docstring. Both exclusions are derived from __file__ and
# never from a literal filename, so a rename cannot leave either one pointing at
# a path that no longer exists - which would look green right up to the moment
# the machine ran out of processes.
THIS_MODULE = Path(__file__).resolve()


# ---------------------------------------------------------------------------
# The module set, pinned
# ---------------------------------------------------------------------------

# "Zero violations" is a claim relative to a SET. Listing the set makes the gate
# a stated contract rather than a description of whatever happened to be on disk
# when it ran, and test_the_scanned_module_set_is_exactly_the_solve_package
# asserts the list against the filesystem so that a new module, a rename or a
# deletion fails the gate instead of silently shrinking its coverage.
SOLVE_SOURCES: tuple[str, ...] = (
    "__init__.py",
    "backends/__init__.py",
    "backends/exhaustive.py",
    "backends/greedy.py",
    "exact.py",
    "optimize.py",
    "power.py",
    "ratio.py",
    "relax.py",
)

# The same set under tests/solve, excluding this module. Pinned for the same
# reason: section (e) asserting "no tolerance found" means nothing without a
# statement of where it looked.
SOLVE_TEST_SOURCES: tuple[str, ...] = (
    "__init__.py",
    "synthetic.py",
    "test_ceiling_fence.py",
    "test_display_rounding.py",
    "test_exact.py",
    "test_exponent_owner.py",
    "test_golden.py",
    "test_optimize.py",
    "test_power.py",
    "test_ratio.py",
    "test_relax.py",
    "test_synthetic.py",
)


def _relative_python_sources(root: Path, *, exclude: Path | None = None) -> tuple[str, ...]:
    """List every Python source under a root, as posix paths relative to it.

    Args:
        root: Directory to walk.
        exclude: An absolute path to omit, or None.

    Returns:
        Sorted relative posix paths, bytecode caches skipped.
    """
    return tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts and (exclude is None or path.resolve() != exclude)
        )
    )


def _dotted_name(relative: str) -> str:
    """Convert a path relative to the solve package into its importable name.

    Args:
        relative: A posix path such as ``backends/greedy.py``.

    Returns:
        The dotted module name, with a package ``__init__.py`` mapping to the
        package itself rather than to a submodule named ``__init__``.
    """
    stem = relative.removesuffix(".py")
    if stem == "__init__":
        return "clockspeed.solve"
    stem = stem.removesuffix("/__init__")
    return "clockspeed.solve." + stem.replace("/", ".")


# Derived from the pinned file list rather than written out a second time: two
# hand-maintained lists of the same fact drift, and the derivation is exercised
# by test_the_dotted_module_names_derive_from_the_pinned_file_set.
SOLVE_MODULES: tuple[str, ...] = tuple(_dotted_name(name) for name in SOLVE_SOURCES)


def test_the_scanned_module_set_is_exactly_the_solve_package() -> None:
    """The pinned file list matches what is actually on disk, in both directions.

    A gate that scans "whatever it finds" reports zero violations just as
    happily when it finds nothing. Asserting equality means a module added to
    the solve package fails this test until someone adds it to the list, at
    which point every scan below starts covering it.
    """
    assert _relative_python_sources(SOLVE_PACKAGE) == SOLVE_SOURCES, (
        "the solve package no longer matches SOLVE_SOURCES; a module was added, renamed "
        "or removed and the phase 3 scans are no longer covering what they claim to"
    )


def test_the_scanned_solve_test_set_is_exactly_the_solve_test_package() -> None:
    """The pinned test-file list matches what is on disk, this module aside."""
    discovered = _relative_python_sources(SOLVE_TESTS, exclude=THIS_MODULE)
    assert discovered == SOLVE_TEST_SOURCES, (
        "tests/solve no longer matches SOLVE_TEST_SOURCES; the tolerance scan in section "
        "(e) is no longer covering what it claims to"
    )


def test_the_dotted_module_names_derive_from_the_pinned_file_set() -> None:
    """A package __init__ maps to the package, not to a submodule called __init__.

    Importing ``clockspeed.solve.__init__`` would succeed and register a SECOND
    module object for the same file, so the import-graph measurements in section
    (c) would be taken against a module nothing else in the process is using.
    """
    assert _dotted_name("__init__.py") == "clockspeed.solve"
    assert _dotted_name("backends/__init__.py") == "clockspeed.solve.backends"
    assert _dotted_name("exact.py") == "clockspeed.solve.exact"
    assert _dotted_name("backends/greedy.py") == "clockspeed.solve.backends.greedy"
    assert "clockspeed.solve.__init__" not in SOLVE_MODULES


# ===========================================================================
# a. No floating-point arithmetic anywhere in the solve path
# ===========================================================================
#
# The CS-300 acceptance criterion, enforced as a static AST walk.
#
# Each predicate below names a MEASURED failure rather than a stylistic
# preference. All measurements are on CPython 3.14.4:
#
#   float/complex literal   the only way to write an inexact constant.
#   float / complex         one rule covering four spellings at once - the call
#                           float("2.5"), the annotation "x: float", the
#                           isinstance argument, and the cast target. All four
#                           reduce to an ast.Name (or Attribute) holding the
#                           identifier, so one predicate catches the lot.
#   **                      Fraction(5, 2) ** Fraction('1.321929') returns the
#                           float 3.3577506181236285. It does not raise and does
#                           not warn. The defect is DATA-DEPENDENT: the same
#                           operator with Fraction(2, 1) returns a Fraction, so a
#                           test written with a whole-number exponent passes
#                           while the shipped exponent silently returns a float.
#   pow                     the same operation spelled as a call.
#   round                   round(Fraction(3, 2)) returns the int 2 - measured.
#                           Exactness is lost with no error and no float in
#                           sight, which is why banning floats alone is not
#                           enough.
#   divmod                  divmod(Fraction(7, 2), Fraction(2)) returns
#                           (1, Fraction(3, 2)) - measured. The quotient is
#                           floored to an int, so the same loss as round.
#   math, cmath, statistics these are float libraries end to end.
#   decimal                 Decimal is not a Fraction: it is exact in base ten
#                           only, so 1/3 is as lossy there as in binary.
#   random                  nondeterminism in a path whose defining property is
#                           that two runs on the same input agree.
#   numpy, scipy            float64 arrays, and also a dependency this project
#                           has decided it does not have (BOOTSTRAP.md 11).

#   int / int               Fraction(5, 2).numerator / Fraction(5, 2).denominator
#                           returns the float 2.5, and so does len(x) / int(y) -
#                           measured. Python 3's true division of two ints is a
#                           float, so a "/" whose BOTH operands are ints by their
#                           spelling - an int literal, .numerator, .denominator,
#                           int(...) or len(...) - is banned. A "/" over names
#                           is NOT: Fraction / Fraction is exact and is the
#                           arithmetic itself, and an operand's type is not in
#                           the tree. Banning "/" wherever neither operand is a
#                           Fraction(...) construction was measured against
#                           clockspeed/audit/fuel.py: it flags all three of the
#                           module's divisions, every one exact, so it is not
#                           used - the behavioural arm
#                           tests/audit/test_fuel.py::
#                           test_a_shortfall_below_float_resolution_still_fires
#                           guards a float decision there instead.
#   truediv, __truediv__,   operator.truediv(5, 2), (5).__truediv__(2) and
#   __rtruediv__, __float__ Fraction(5, 2).__float__() each return a float -
#                           measured: the same divisions and conversion spelled
#                           so that neither the "/" rule nor the float rule sees
#                           them.

_BANNED_CONSTANT_TYPES: tuple[type, ...] = (float, complex)
_BANNED_NUMERIC_NAMES = frozenset({"complex", "float"})
_BANNED_CALL_NAMES = frozenset({"divmod", "pow", "round"})
_BANNED_MODULE_ROOTS = frozenset(
    {"cmath", "decimal", "math", "numpy", "random", "scipy", "statistics"}
)
_BANNED_DIVISION_NAMES = frozenset({"__float__", "__rtruediv__", "__truediv__", "truediv"})
_INT_ATTRIBUTES = frozenset({"denominator", "numerator"})
_INT_CALL_NAMES = frozenset({"int", "len"})


def _identifier_of(node: ast.AST) -> str | None:
    """Return the bare identifier a node names, ignoring how it was reached.

    ``float(x)`` and ``builtins.float(x)`` are the same defect, so both reduce
    to ``float``.

    Args:
        node: Any AST node.

    Returns:
        The identifier, or None for a node that names nothing simple.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _line_of(node: ast.AST) -> int:
    """Return a node's line number, or 0 for a node that carries no position.

    Args:
        node: Any AST node.

    Returns:
        The 1-based line number.
    """
    return getattr(node, "lineno", 0)


def _flag_inexact_literal(node: ast.AST) -> str | None:
    """Flag a float or complex literal.

    ``type(...) is`` rather than ``isinstance``: ``isinstance(True, int)`` is
    True, and an isinstance-shaped membership test would drag subclasses in.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    if isinstance(node, ast.Constant) and type(node.value) in _BANNED_CONSTANT_TYPES:
        return f"{type(node.value).__name__} literal"
    return None


def _flag_inexact_name(node: ast.AST) -> str | None:
    """Flag a reference to ``float`` or ``complex`` in any position.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    identifier = _identifier_of(node)
    if identifier in _BANNED_NUMERIC_NAMES:
        return f"reference to '{identifier}'"
    return None


def _flag_exponentiation(node: ast.AST) -> str | None:
    """Flag ``**`` as an operator, whether plain or augmented.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    if isinstance(node, ast.BinOp | ast.AugAssign) and isinstance(node.op, ast.Pow):
        return "exponentiation operator"
    return None


def _flag_inexact_call(node: ast.AST) -> str | None:
    """Flag a call to ``pow``, ``round`` or ``divmod``.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    if isinstance(node, ast.Call):
        identifier = _identifier_of(node.func)
        if identifier in _BANNED_CALL_NAMES:
            return f"call to '{identifier}'"
    return None


def _imported_roots(node: ast.AST) -> list[str]:
    """Return the top-level package names an import statement names.

    ``from scipy import optimize`` and ``import numpy as np`` both reduce to
    their root package, which is the level the ban is stated at.

    Args:
        node: Any AST node.

    Returns:
        Root package names, empty for a node that is not an import.
    """
    if isinstance(node, ast.Import):
        return [alias.name.partition(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module.partition(".")[0]]
    return []


def _flag_inexact_import(node: ast.AST) -> str | None:
    """Flag an import of a float, decimal or nondeterministic numeric module.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    banned = sorted(set(_imported_roots(node)) & _BANNED_MODULE_ROOTS)
    if banned:
        return f"import of '{banned[0]}'"
    return None


def _is_int_spelled(node: ast.AST) -> bool:
    """Whether a node is an int by its spelling alone, whatever the names hold.

    Args:
        node: Any AST node.

    Returns:
        True for an int literal (never a bool), a ``.numerator`` or
        ``.denominator`` read, or a call to ``int`` or ``len``.
    """
    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.Attribute):
        return node.attr in _INT_ATTRIBUTES
    if isinstance(node, ast.Call):
        return _identifier_of(node.func) in _INT_CALL_NAMES
    return False


def _flag_int_true_division(node: ast.AST) -> str | None:
    """Flag ``/`` whose two operands are both ints by their spelling.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Div)
        and _is_int_spelled(node.left)
        and _is_int_spelled(node.right)
    ):
        return "true division of two ints"
    return None


def _flag_division_spelling(node: ast.AST) -> str | None:
    """Flag ``truediv``, ``__truediv__``, ``__rtruediv__`` and ``__float__``.

    Any position counts - a call, an attribute read, a bare reference or a
    ``from operator import`` - since each spells a float division or
    conversion that neither the ``/`` rule nor the float rule sees.

    Args:
        node: Any AST node.

    Returns:
        A description, or None.
    """
    identifiers = [_identifier_of(node)]
    if isinstance(node, ast.ImportFrom):
        identifiers += [alias.name for alias in node.names]
    for identifier in identifiers:
        if identifier in _BANNED_DIVISION_NAMES:
            return f"reference to '{identifier}'"
    return None


_INEXACT_CHECKS = (
    _flag_inexact_literal,
    _flag_inexact_name,
    _flag_exponentiation,
    _flag_inexact_call,
    _flag_inexact_import,
    _flag_int_true_division,
    _flag_division_spelling,
)


def inexact_violations(source: str) -> list[str]:
    """Report every banned inexact-arithmetic construct in a module's AST.

    Walks the parsed tree, never the text. A docstring is one ``ast.Constant``
    holding a ``str`` and its contents are never parsed as operators; a comment
    does not survive parsing at all. That is what lets the two modules whose
    docstrings quote the banned measurement scan clean.

    Args:
        source: Module source text.

    Returns:
        Human-readable violation descriptions, in traversal order.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        for check in _INEXACT_CHECKS:
            described = check(node)
            if described is not None:
                found.append(f"line {_line_of(node)}: {described}")
    return found


@pytest.mark.parametrize("relative", SOLVE_SOURCES)
def test_no_solve_module_contains_inexact_arithmetic(relative: str) -> None:
    """The CS-300 acceptance criterion, asserted per module.

    Non-negotiable 6: exact rational arithmetic in the solve path, with the
    ABSENCE of floats asserted rather than assumed. A ratio calculator that
    drifts does not return a visibly wrong answer - it returns a building count
    of 3.9999999999999996 that floors to 3, with the right type, a plausible
    value and no error attached.
    """
    violations = inexact_violations((SOLVE_PACKAGE / relative).read_text(encoding="utf-8"))
    listed = "\n  ".join(violations)
    assert not violations, f"inexact arithmetic in clockspeed/solve/{relative}:\n  {listed}"


# The measurement both modules quote verbatim as evidence for the ban. Held here
# so the negative control asserts against the REAL files: a synthetic stand-in
# would prove only that the scanner handles a string this module wrote itself.
_QUOTED_MEASUREMENT = "Fraction(5, 2) ** Fraction(exponent)"


@pytest.mark.parametrize("relative", ["exact.py", "power.py"])
def test_the_scan_ignores_the_docstring_that_quotes_the_banned_measurement(relative: str) -> None:
    """A module documenting why ``**`` is banned is not itself a violation.

    Both halves are asserted. If the quotation is ever removed the first
    assertion fails and this control stops being vacuous; if the scanner ever
    regresses to a text sweep the second fails. A guard that fires on the
    documentation explaining the guard is a guard that gets switched off.
    """
    source = (SOLVE_PACKAGE / relative).read_text(encoding="utf-8")
    assert _QUOTED_MEASUREMENT in source, (
        f"clockspeed/solve/{relative} no longer quotes the measurement, so this negative "
        "control no longer proves the scan is AST-based rather than text-based"
    )
    assert not inexact_violations(source), (
        f"clockspeed/solve/{relative} scans dirty, and the only banned spelling in it is "
        "inside a docstring - the scan has regressed to reading text"
    )


# The scan's scope extended past the package (CS-1285): an audit module that
# DECIDES by comparing exact Fractions is held to the same predicates. The
# runtime audit_exact walk on its results cannot see a float that is used and
# discarded - ``float(pooled) < float(demand)`` flips a verdict and leaves every
# published figure a Fraction - which is the case only a static scan reaches.
AUDIT_PACKAGE = REPO_ROOT / "clockspeed" / "audit"
EXACT_AUDIT_SOURCES: tuple[str, ...] = ("fuel.py",)


@pytest.mark.parametrize("relative", EXACT_AUDIT_SOURCES)
def test_no_exact_audit_module_contains_inexact_arithmetic(relative: str) -> None:
    """Non-negotiable 6 over the audit modules that decide on exact figures."""
    violations = inexact_violations((AUDIT_PACKAGE / relative).read_text(encoding="utf-8"))
    listed = "\n  ".join(violations)
    assert not violations, f"inexact arithmetic in clockspeed/audit/{relative}:\n  {listed}"


@pytest.mark.parametrize(
    ("anchor", "spliced"),
    [
        ("if pooled < demand:", "if float(pooled) < float(demand):"),
        ("supply = max(net, Fraction(0))", "supply = max(net, 0.0)"),
        ("from fractions import Fraction", "from fractions import Fraction\nimport math"),
        (
            "if pooled < demand:",
            "if pooled.numerator / pooled.denominator < demand.numerator / demand.denominator:",
        ),
        ("if pooled < demand:", "if pooled.__float__() < demand.__float__():"),
        (
            "if pooled < demand:",
            "if operator.truediv(pooled.numerator, pooled.denominator) < demand:",
        ),
    ],
    ids=[
        "float-comparison",
        "float-literal",
        "math-import",
        "int-division",
        "dunder-float",
        "truediv",
    ],
)
def test_the_scan_sees_a_float_spliced_into_the_real_fuel_audit(anchor: str, spliced: str) -> None:
    """The extended scope is live: the real module, one construct spliced in, scans dirty.

    Asserted against the REAL file, so a scan that stopped reading it - or an
    anchor that drifted out of it - fails here instead of passing vacuously.
    """
    source = (AUDIT_PACKAGE / "fuel.py").read_text(encoding="utf-8")
    assert source.count(anchor) == 1, f"the anchor {anchor!r} is no longer unique in fuel.py"
    assert inexact_violations(source.replace(anchor, spliced))


# ===========================================================================
# b. The gate is proven to detect
# ===========================================================================
#
# CONVENTIONS.md section 7.2: a gate nobody has watched fail is an unrun gate.
# This one IS the phase acceptance criterion, so if it is vacuous the phase is
# ungraded rather than merely under-tested. Every predicate gets a synthetic
# source string containing exactly the construct it forbids.

# A module whose entire body is a docstring quoting every banned spelling. The
# single most important negative control in this file: it is the shape of
# clockspeed/solve/exact.py's own header, and a text-based scanner flags it.
_DOCSTRING_EVIDENCE = (
    '"""Why the exponent cannot be applied exactly.\n'
    "\n"
    "Measured on CPython 3.14: ``Fraction(5, 2) ** Fraction('1.321929')`` returns\n"
    "a float, ``float('0.1')`` succeeds while reading the wrong value, and\n"
    "``round(Fraction(3, 2))`` returns the int 2. Neither ``math`` nor\n"
    "``decimal`` is imported anywhere in this layer, and ``pow`` is not called.\n"
    '"""\n'
)

_DETECTOR_POSITIVES: tuple[tuple[str, str, str], ...] = (
    ("float literal", "rate = 2.5\n", "float literal"),
    ("complex literal", "rate = 2j\n", "complex literal"),
    ("float call", "rate = float('2.5')\n", "reference to 'float'"),
    (
        "float annotation",
        "def draw(rate: float) -> None:\n    return None\n",
        "reference to 'float'",
    ),
    (
        "float isinstance argument",
        "def check(value):\n    return isinstance(value, float)\n",
        "reference to 'float'",
    ),
    (
        "float cast target",
        "from typing import cast\n\nrate = cast(float, 1)\n",
        "reference to 'float'",
    ),
    (
        "float reached through an attribute",
        "import builtins\n\nrate = builtins.float('2.5')\n",
        "reference to 'float'",
    ),
    (
        "complex isinstance argument",
        "def check(value):\n    return isinstance(value, complex)\n",
        "reference to 'complex'",
    ),
    ("exponentiation operator", "value = base ** exponent\n", "exponentiation operator"),
    ("augmented exponentiation", "value **= exponent\n", "exponentiation operator"),
    ("pow builtin", "value = pow(base, exponent)\n", "call to 'pow'"),
    ("round builtin", "value = round(ratio)\n", "call to 'round'"),
    ("divmod builtin", "whole, rest = divmod(total, size)\n", "call to 'divmod'"),
    ("import math", "import math\n", "import of 'math'"),
    ("from math import", "from math import sqrt\n", "import of 'math'"),
    ("import cmath", "import cmath\n", "import of 'cmath'"),
    ("import statistics", "import statistics\n", "import of 'statistics'"),
    ("import decimal", "from decimal import Decimal\n", "import of 'decimal'"),
    ("import random", "import random\n", "import of 'random'"),
    ("import numpy aliased", "import numpy as np\n", "import of 'numpy'"),
    ("import scipy submodule", "from scipy import optimize\n", "import of 'scipy'"),
    (
        "numerator over denominator",
        "flag = value.numerator / value.denominator < limit\n",
        "true division of two ints",
    ),
    ("int literal over int literal", "half = 1 / 2\n", "true division of two ints"),
    ("len over int call", "share = len(parts) / int(total)\n", "true division of two ints"),
    (
        "operator.truediv",
        "import operator\n\nrate = operator.truediv(left, right)\n",
        "reference to 'truediv'",
    ),
    (
        "truediv imported by name",
        "from operator import truediv\n",
        "reference to 'truediv'",
    ),
    ("dunder truediv", "rate = left.__truediv__(right)\n", "reference to '__truediv__'"),
    ("dunder rtruediv", "rate = right.__rtruediv__(left)\n", "reference to '__rtruediv__'"),
    ("dunder float", "rate = value.__float__()\n", "reference to '__float__'"),
)

_DETECTOR_NEGATIVES: tuple[tuple[str, str], ...] = (
    (
        "exact Fraction arithmetic",
        "from fractions import Fraction\n\nrate = Fraction(5, 2) * Fraction(3)\n",
    ),
    ("integer, bool and None literals", "count = 5\nflag = True\nnothing = None\n"),
    ("division and multiplication, which ARE the arithmetic", "rate = numerator / denominator\n"),
    ("a Fraction divided by an int literal", "rate = total / 2\n"),
    (
        "a Fraction built from two ints",
        "from fractions import Fraction\n\nrate = Fraction(value.numerator, value.denominator)\n",
    ),
    (
        "floor division of two ints, which is exact",
        "whole = value.numerator // value.denominator\n",
    ),
    ("a Fraction over a name scaled by sixty", "supply_mw = supply * energy / SIXTY\n"),
    ("a string that merely spells a banned name", "label = 'float'\n"),
    ("docstring quoting every banned spelling", _DOCSTRING_EVIDENCE),
    (
        "comment quoting the banned measurement",
        "# Fraction(5, 2) ** Fraction('1.321929') returns a float, so ** is banned.\n",
    ),
)


@pytest.mark.parametrize(("label", "source", "expected"), _DETECTOR_POSITIVES, ids=lambda v: v)
def test_the_inexact_detector_flags_each_banned_construct(
    label: str, source: str, expected: str
) -> None:
    """Every predicate is watched catching the construct it exists to catch.

    Parametrized one construct per case rather than asserted over a single
    combined sample, because a combined sample goes green as soon as ANY
    predicate fires and would hide a predicate that never fires at all.
    """
    violations = inexact_violations(source)
    assert any(expected in violation for violation in violations), (
        f"the detector did not flag {label}; it reported {violations}"
    )


@pytest.mark.parametrize(("label", "source"), _DETECTOR_NEGATIVES, ids=lambda v: v)
def test_the_inexact_detector_leaves_the_legitimate_cases_alone(label: str, source: str) -> None:
    """The detector does not fire on exact arithmetic, prose or comments.

    The negatives are the half that decides whether this gate survives. A
    scanner that flags ``Fraction(5, 2) * Fraction(3)``, or the docstring
    explaining why ``**`` is banned, is a scanner someone turns off - and a
    turned-off gate is worse than none, because the phase still claims it.
    """
    violations = inexact_violations(source)
    assert not violations, f"the detector false-positived on {label}: {violations}"


# ===========================================================================
# c. The import-graph seam, measured in a child interpreter
# ===========================================================================
#
# docs/ARCHITECTURE.md section 3: solve/ never reads a save; it takes a registry
# and a request. Section 3.1 states that layering reduces to an allowed-import
# matrix and that walking the import graph makes it mechanically checkable.
#
# This MUST run in a child. By the time this module executes, the parent's
# sys.modules already holds whatever the rest of the suite imported - including
# clockspeed.data.locate, which this file imports for its env var names. A check
# against the parent's sys.modules would measure the test session, not the seam.

ABSENT = REPO_ROOT / "no-such-path-phase-3-gate"

_CHILD_TIMEOUT_SECONDS = 300

FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "clockspeed.advisor",
    "clockspeed.audit",
    "clockspeed.data.docs_extract",
    "clockspeed.data.locate",
    "clockspeed.progress",
    "clockspeed.save",
    "clockspeed.surface",
)

# THE CARVE-OUT, AND WHY IT IS NOT A HOLE.
#
# Measured on this tree: importing clockspeed.solve.ratio loads
# clockspeed.data.docs_extract. Solve does not import it - solve imports
# clockspeed.data.registry and clockspeed.data.version, and BOTH of those import
# docs_extract at module level. tests/data/test_phase2_gate.py's ALLOWED_IMPORTS
# does not merely permit that, it REQUIRES it: the required half of
# test_importing_a_data_module_pulls_in_only_its_permitted_neighbours asserts
# registry -> {blobs, docs_extract} and version -> {docs_extract}. So a literal
# "no solve module may load docs_extract" rule cannot be satisfied by any solve
# module that consumes the registry, which is every one of them that does work.
#
# The carve-out is therefore scoped to exactly that transitive route, and it is
# self-verifying rather than assumed:
#   - test_the_docs_extract_carve_out_is_real_and_not_a_standing_excuse measures
#     each carrier in its own child and asserts it really does load docs_extract.
#     If a carrier stops importing it, that test fails and the carve-out must be
#     narrowed rather than silently continuing to excuse a real violation.
#   - Section (d) forbids a DIRECT import of docs_extract from solve with no
#     carve-out at all, which is the violation this one has to tolerate.
#
# Residual, stated rather than papered over: if a solve module acquired some
# THIRD import that pulled docs_extract in while a carrier was also loaded, the
# subtraction would absorb it. Section (d) catches that only if the third import
# is docs_extract itself. Nothing here catches a new intermediary.
DOCS_EXTRACT_CARRIERS: tuple[str, ...] = (
    "clockspeed.data.registry",
    "clockspeed.data.version",
)
CARRIED_TRANSITIVELY = frozenset({"clockspeed.data.docs_extract"})

# The required half of the seam. A negative assertion rules out without pinning
# down (CONVENTIONS.md section 7.2): "imports nothing forbidden" would pass just
# as happily for a module that had collapsed to importing nothing at all.
REGISTRY_MODULE = "clockspeed.data.registry"
REGISTRY_CONSUMERS: tuple[str, ...] = (
    "clockspeed.solve.backends.exhaustive",
    "clockspeed.solve.backends.greedy",
    "clockspeed.solve.optimize",
    "clockspeed.solve.power",
    "clockspeed.solve.ratio",
)


def no_install_env() -> dict[str, str]:
    """Build a child environment in which no install, save root or account resolves.

    All four override variables are set, not just the two naming an install:
    leaving ``CLOCKSPEED_SAVE_ROOT`` unset would let a child fall through to
    ``%LOCALAPPDATA%`` and find the operator's real save directory, which is
    exactly the machine dependence this module exists to forbid.

    Returns:
        A copy of the current environment with the overrides applied.
    """
    env = dict(os.environ)
    env[ENV_GAME_DIR] = str(ABSENT / "install")
    env[ENV_SAVE_ROOT] = str(ABSENT / "saves")
    env[ENV_ACCOUNT_DIR] = str(ABSENT / "account")
    env[ENV_LOCAL_CONFIG] = str(ABSENT / "local.json")
    # CONVENTIONS.md section 10: pin the child's text encoding so its output
    # decodes the same way on every machine.
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_child(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run a child interpreter from the repo root and capture its output.

    ``sys.executable`` is the only correct way to name the interpreter here. A
    bare ``python`` would resolve off PATH to whatever happens to be first, and
    an absolute interpreter path in a tracked file is forbidden outright
    (CONVENTIONS.md section 10).

    Every caller binds ``returncode`` to a local before asserting on it, and
    that is not style. ``assert child.returncode == 0`` makes pytest repr the
    whole CompletedProcess in its "where" clause, and ``args[0]`` is the
    absolute interpreter path - which on a default Windows install sits under
    the operator's home directory and carries their account name into the CI
    log. Asserting on a plain int prints a plain int.

    Args:
        args: Arguments after the interpreter.
        env: The child environment.

    Returns:
        The completed process, decoded as text. A non-zero exit is returned
        rather than raised so the caller can assert on it.
    """
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHILD_TIMEOUT_SECONDS,
        env=env,
        check=False,
    )


def test_the_forced_absent_path_really_is_absent() -> None:
    """The path every child points at must not exist, or the module is vacuous.

    If ``ABSENT`` ever became a real directory the overrides would resolve to
    something and every "no install" assertion below would be testing the
    opposite of what it says.
    """
    assert not ABSENT.exists(), (
        f"{ABSENT.name} exists, so the no-install overrides resolve to something real"
    )


_PROBE_IMPORT = """
import importlib
import json
import sys

importlib.import_module(sys.argv[1])
print(json.dumps(sorted(name for name in sys.modules if name.startswith("clockspeed"))))
"""


@cache
def _import_probe(module: str) -> subprocess.CompletedProcess[str]:
    """Import one module in a fresh interpreter with no install resolvable.

    Cached because several tests ask different questions of the same run, and a
    child interpreter per question would multiply the cost of this module for no
    extra coverage.

    Args:
        module: Dotted module name.

    Returns:
        The completed child process.
    """
    return run_child(["-c", _PROBE_IMPORT, module], no_install_env())


def loaded_clockspeed_modules(module: str) -> frozenset[str]:
    """Report every clockspeed module that importing ``module`` pulled in.

    Args:
        module: Dotted module name.

    Returns:
        The clockspeed entries of the child's sys.modules.
    """
    probe = _import_probe(module)
    exit_code = probe.returncode
    assert exit_code == 0, f"importing {module} with no install failed:\n{probe.stderr}"
    return frozenset(json.loads(probe.stdout.strip().splitlines()[-1]))


def _under_prefix(name: str, prefix: str) -> bool:
    """Report whether a dotted name is the prefix itself or lives beneath it.

    A bare ``startswith`` would make ``clockspeed.saved_thing`` look like a
    module under ``clockspeed.save``.

    Args:
        name: Dotted module name.
        prefix: Dotted package prefix.

    Returns:
        True if ``name`` is at or below ``prefix``.
    """
    return name == prefix or name.startswith(prefix + ".")


def seam_violations(loaded: frozenset[str]) -> list[str]:
    """Report which loaded modules are layers the solve package may not reach.

    Split out from the test so the set arithmetic - including the carve-out,
    which is the subtle part - can be watched catching a violation rather than
    only ever being exercised on data that happens to be clean.

    Args:
        loaded: The clockspeed entries of a child's sys.modules.

    Returns:
        Sorted names of forbidden modules that were reached.
    """
    reached = {
        name
        for name in loaded
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if _under_prefix(name, prefix)
    }
    if any(carrier in loaded for carrier in DOCS_EXTRACT_CARRIERS):
        reached -= CARRIED_TRANSITIVELY
    return sorted(reached)


@pytest.mark.parametrize("module", SOLVE_MODULES)
def test_importing_a_solve_module_reaches_no_layer_it_may_not_reach(module: str) -> None:
    """No solve module drags in a save reader, a consumer layer, or the locator.

    The claims that matter, all of them measured rather than reviewed: solve
    imports nothing from ``clockspeed.save``, so a caller that wants "solve
    against my world" must read the world itself and hand this layer plain
    quantities; solve imports nothing from ``advisor``, ``surface``, ``audit``
    or ``progress``, which are all ABOVE it; and solve never imports
    ``clockspeed.data.locate``, so the engine cannot depend on where - or
    whether - the game is installed.
    """
    reached = seam_violations(loaded_clockspeed_modules(module))
    assert not reached, (
        f"importing {module} also loaded {reached} - a layer reaching past its "
        "neighbour (docs/ARCHITECTURE.md section 3)"
    )


def test_the_seam_detector_actually_finds() -> None:
    """The seam arithmetic catches each forbidden layer, and the carve-out stays narrow.

    The last two assertions are the ones that matter. They pin the carve-out
    from both sides: docs_extract is excused ONLY when a carrier that explains
    it is also loaded, and excusing it never spreads to anything else reached at
    the same time. A carve-out that widened silently would leave this whole
    section green while the seam it guards had gone.
    """
    for forbidden in ("clockspeed.save.header", "clockspeed.advisor.rules"):
        assert seam_violations(frozenset({"clockspeed.solve.ratio", forbidden})) == [forbidden]

    assert seam_violations(frozenset({"clockspeed.data.locate"})) == ["clockspeed.data.locate"]

    # A module whose name merely begins with a forbidden package name.
    assert not seam_violations(frozenset({"clockspeed.saved_state"}))

    # docs_extract with no carrier present is NOT excused: nothing explains it,
    # so it is a direct reach and is reported.
    assert seam_violations(frozenset({"clockspeed.data.docs_extract"})) == [
        "clockspeed.data.docs_extract"
    ]

    # With a carrier present it is excused - and nothing else is.
    with_carrier = frozenset(
        {"clockspeed.data.registry", "clockspeed.data.docs_extract", "clockspeed.save.header"}
    )
    assert seam_violations(with_carrier) == ["clockspeed.save.header"]


@pytest.mark.parametrize("carrier", DOCS_EXTRACT_CARRIERS)
def test_the_docs_extract_carve_out_is_real_and_not_a_standing_excuse(carrier: str) -> None:
    """The carve-out's premise is measured, so it cannot outlive its reason.

    CONVENTIONS.md section 15.1 records that a guard can be green while
    self-excusing. This is the assertion that stops that happening here: the
    carve-out above subtracts docs_extract only because these data-layer
    modules import it, and that is checked rather than assumed. If a carrier
    stops importing docs_extract, this fails and the carve-out must be narrowed
    instead of quietly continuing to excuse a genuine violation.
    """
    loaded = loaded_clockspeed_modules(carrier)
    assert loaded >= CARRIED_TRANSITIVELY, (
        f"{carrier} no longer loads {sorted(CARRIED_TRANSITIVELY)}, so the docs_extract "
        "carve-out in FORBIDDEN_IMPORT_PREFIXES has lost its justification and must be "
        "narrowed - it is now excusing something nothing explains"
    )


def test_the_exact_primitives_import_nothing_from_clockspeed() -> None:
    """The bottom of the solve layer depends on nothing inside the project.

    ``clockspeed/solve/exact.py`` states this in its own docstring - "imports
    nothing from ``clockspeed`` at all, which is what lets the arithmetic be
    reasoned about and tested on its own". Asserted on the FULL clockspeed
    namespace rather than on a forbidden list, because that is the actual claim:
    an import of anything at all would satisfy the per-prefix check above and
    still break the property.
    """
    loaded = loaded_clockspeed_modules("clockspeed.solve.exact")
    assert loaded == {"clockspeed", "clockspeed.solve", "clockspeed.solve.exact"}, (
        f"importing clockspeed.solve.exact loaded {sorted(loaded)}; it is the bottom of "
        "the solve layer and must depend on nothing inside the project"
    )


@pytest.mark.parametrize("module", REGISTRY_CONSUMERS)
def test_the_registry_consumers_really_consume_the_registry(module: str) -> None:
    """The required half: the seam solve is supposed to use, it actually uses.

    Without this, every negative assertion in this section would pass for a
    solve layer that had been gutted to import nothing. The stated model is that
    solve takes a Registry, so consuming ``clockspeed.data.registry`` is the
    contract, not an implementation detail.
    """
    assert REGISTRY_MODULE in loaded_clockspeed_modules(module), (
        f"{module} no longer imports {REGISTRY_MODULE}; either the seam moved or this "
        "gate's negative assertions have quietly become vacuous"
    )


# ===========================================================================
# d. Source-level forbidden imports, a second and independent signal
# ===========================================================================
#
# NEITHER SECTION SUBSUMES THE OTHER, and that is the whole reason both exist.
#
#   (c) catches a TRANSITIVE pull - solve importing some module that itself
#       reaches a forbidden layer. That edge appears nowhere in solve's own
#       source text, so no source scan can see it.
#   (d) catches a DIRECT import that happens not to EXECUTE - one guarded by
#       "if TYPE_CHECKING:", one inside a function body that no test calls, one
#       behind a conditional that is False on this machine. None of those put a
#       module into sys.modules, so the child probe reports nothing at all.
#
# The second case is live here rather than hypothetical:
# clockspeed/solve/backends/__init__.py imports its two backends from INSIDE
# function bodies, deliberately, so that importing the package does not import
# every backend. Measured: importing clockspeed.solve.backends loads only the
# package shell. A source scan sees those imports; the import graph does not.
#
# This section applies the forbidden list with NO carve-out. A direct import of
# clockspeed.data.docs_extract from solve is a real violation regardless of what
# registry and version do, which is exactly the case section (c) has to tolerate.


def source_level_forbidden_imports(source: str) -> list[str]:
    """Report every import statement naming a module the solve layer may not name.

    Walks the whole tree rather than the module's top-level statements, so an
    import nested in a function body, a ``TYPE_CHECKING`` block or a conditional
    is caught alongside a plain one.

    Args:
        source: Module source text.

    Returns:
        Human-readable violation descriptions.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        named: list[str] = []
        if isinstance(node, ast.Import):
            named = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            named = [node.module]
        found.extend(
            f"line {_line_of(node)}: {name}"
            for name in named
            for prefix in FORBIDDEN_IMPORT_PREFIXES
            if _under_prefix(name, prefix)
        )
    return found


@pytest.mark.parametrize("relative", SOLVE_SOURCES)
def test_no_solve_module_names_a_forbidden_module_in_an_import(relative: str) -> None:
    """No solve source directly imports a save reader, a consumer layer or a raw reader.

    ``clockspeed.data.locate`` and ``clockspeed.data.docs_extract`` are the two
    that matter most here: solve takes an already-normalized Registry, so
    reaching for the locator would make the engine depend on where the install
    is, and reaching for the raw docs reader would make it depend on the shipped
    file's own format - the single highest-churn surface in the project.
    """
    violations = source_level_forbidden_imports(
        (SOLVE_PACKAGE / relative).read_text(encoding="utf-8")
    )
    assert not violations, (
        f"clockspeed/solve/{relative} imports a module outside its permitted set:\n  "
        + "\n  ".join(violations)
    )


def test_the_source_level_import_detector_actually_finds() -> None:
    """The source scan catches the two shapes the import graph cannot see.

    Both are the reason this section is not redundant with section (c): a
    ``TYPE_CHECKING`` import never executes, and an import inside a function
    body executes only if something calls it. Neither reaches sys.modules during
    a bare import, so the child probe reports a clean graph for both.
    """
    type_checking_only = (
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from clockspeed.save.header import Header\n"
    )
    deferred_in_a_function = (
        "def load():\n    from clockspeed.data.docs_extract import DocsDocument\n\n    return 1\n"
    )
    plain = "import clockspeed.advisor.rules\n"

    assert source_level_forbidden_imports(type_checking_only), (
        "the source scan missed a TYPE_CHECKING import, which is invisible to the "
        "import-graph probe because it never executes"
    )
    assert source_level_forbidden_imports(deferred_in_a_function), (
        "the source scan missed an import inside a function body, which reaches "
        "sys.modules only if something calls the function"
    )
    assert source_level_forbidden_imports(plain)
    assert not source_level_forbidden_imports(
        "from clockspeed.data.registry import Registry\n"
        "from clockspeed.solve.exact import audit_exact\n"
    ), "the source scan flagged a permitted import"
    assert not source_level_forbidden_imports("import clockspeed.saved_state\n"), (
        "the source scan matched on a bare string prefix, so a module whose name merely "
        "starts with a forbidden package name is misreported"
    )


# ===========================================================================
# e. No tolerance anywhere under tests/solve
# ===========================================================================
#
# tests/solve/__init__.py states the rule; this enforces it. A tolerance here
# would not be a loose test - it would be a test that CANNOT fail on the defect
# it exists to catch, because every float defect in this layer lands within an
# epsilon of the right answer. That is the whole difficulty: the wrong value is
# 3.9999999999999996, not 40.
#
# WHAT THIS SECTION DOES NOT AND CANNOT COVER.
# ``==`` alone is not sufficient evidence of exactness. Measured:
# ``Fraction(1, 2) == 0.5`` is True, so an equality assertion passes against a
# float that happens to land on the same value. The remedy is a positive type
# audit next to the equality - ``type(x) is Fraction`` rather than
# ``isinstance``, since ``isinstance(True, int)`` is True - and that is a
# property of each individual assertion in each test module, not something a
# scan over identifiers can see. This section makes no claim about it. What
# covers it is review plus tests/solve/__init__.py stating the rule, and the
# helpers the suites already define for the purpose.

_TOLERANCE_SUBSTRINGS = ("atol", "epsilon", "rtol", "tolerance")

# "eps" needs component matching, not substring matching: "steps" contains it.
_TOLERANCE_COMPONENT = re.compile(r"(?:^|_)eps(?:_|$)")

# Matched as identifiers rather than as text. Measured on this tree: the string
# "approx" occurs 8 times under tests/solve and every occurrence is the prose
# word "approximates" or "approximation" inside a docstring. A grep would report
# 8 violations; the AST reports none, because prose is not an identifier.
_TOLERANCE_HELPER_NAMES = frozenset({"approx", "isclose"})

# THE ALLOWLIST, narrow and self-verifying.
#
# These two test NAMES contain "epsilon" because they are the tests proving that
# an epsilon rule would be WRONG - they assert that a coefficient smaller than
# any usable epsilon is still carried exactly. Flagging them would be the same
# defect as a text sweep flagging the docstring that explains the float ban:
# the gate firing on its own evidence.
#
# A function NAME cannot hold a tolerance value, so allowing these costs no
# coverage. Value-bearing positions are scanned with no allowlist at all.
# test_the_allowlisted_test_names_still_exist stops this list outliving the
# tests it names.
_TOLERANCE_NAMES_ALLOWED = frozenset(
    {
        "test_pivot_row_accepts_an_exact_coefficient_smaller_than_any_usable_epsilon",
        "test_solve_linear_keeps_an_exact_coefficient_too_small_for_any_epsilon",
    }
)


def _is_tolerance_shaped(identifier: str) -> bool:
    """Report whether an identifier reads as a tolerance.

    Args:
        identifier: A bare Python identifier.

    Returns:
        True if it contains a tolerance word or an ``eps`` component.
    """
    lowered = identifier.lower()
    if any(word in lowered for word in _TOLERANCE_SUBSTRINGS):
        return True
    return _TOLERANCE_COMPONENT.search(lowered) is not None


def _value_identifier(node: ast.AST) -> str | None:
    """Return the identifier a node uses in a value-bearing position.

    Variables, attributes, parameters and keyword arguments - every position in
    which an identifier can HOLD or PASS a tolerance value.

    Args:
        node: Any AST node.

    Returns:
        The identifier, or None.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.arg):
        return node.arg
    if isinstance(node, ast.keyword):
        return node.arg
    return None


def _declared_identifier(node: ast.AST) -> str | None:
    """Return the name a definition statement declares.

    Args:
        node: Any AST node.

    Returns:
        The declared name, or None.
    """
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name
    return None


def tolerance_violations(source: str) -> list[str]:
    """Report every tolerance-shaped identifier and approximate-comparison helper.

    Args:
        source: Module source text.

    Returns:
        Human-readable violation descriptions.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        used = _value_identifier(node)
        if used is not None:
            if _is_tolerance_shaped(used):
                found.append(f"line {_line_of(node)}: tolerance-shaped identifier '{used}'")
            if used in _TOLERANCE_HELPER_NAMES:
                found.append(f"line {_line_of(node)}: approximate comparison via '{used}'")
        declared = _declared_identifier(node)
        if (
            declared is not None
            and _is_tolerance_shaped(declared)
            and declared not in _TOLERANCE_NAMES_ALLOWED
        ):
            found.append(f"line {_line_of(node)}: tolerance-shaped definition '{declared}'")
    return found


@pytest.mark.parametrize("relative", SOLVE_TEST_SOURCES)
def test_no_solve_test_uses_a_tolerance(relative: str) -> None:
    """No module under tests/solve compares approximately or names a tolerance.

    Non-negotiable 6 is asserted from both sides: section (a) forbids the solve
    layer from producing an inexact value, and this forbids the suite from
    being written so that it could not notice one.
    """
    violations = tolerance_violations((SOLVE_TESTS / relative).read_text(encoding="utf-8"))
    listed = "\n  ".join(violations)
    assert not violations, f"tolerance comparison in tests/solve/{relative}:\n  {listed}"


def test_the_allowlisted_test_names_still_exist() -> None:
    """Every allowlisted name still names a real test, so the list cannot go stale.

    An allowlist that outlives its entries is an exemption for whatever gets
    written next under the same name.
    """
    corpus = "\n".join(
        (SOLVE_TESTS / relative).read_text(encoding="utf-8") for relative in SOLVE_TEST_SOURCES
    )
    missing = sorted(name for name in _TOLERANCE_NAMES_ALLOWED if f"def {name}(" not in corpus)
    assert not missing, (
        f"allowlisted names that no longer exist under tests/solve: {missing}. Remove them "
        "rather than leaving a standing exemption behind"
    )


def test_this_gate_is_excluded_from_the_tolerance_scan_and_would_otherwise_trip_it() -> None:
    """The self-exclusion is turned into a detector proof against a real file.

    This module must NAME the banned words in order to hunt them, so it is
    excluded from its own scan - and an unexamined self-exclusion is exactly the
    self-excusing guard CONVENTIONS.md section 15.1 warns about. Both halves are
    asserted: that the exclusion is in force, and that it is load-bearing
    because the detector genuinely does fire on this file's own identifiers.
    """
    assert THIS_MODULE.name not in SOLVE_TEST_SOURCES, (
        "this gate is inside its own scan set, so it is about to report itself"
    )
    own = tolerance_violations(THIS_MODULE.read_text(encoding="utf-8"))
    assert own, (
        "the tolerance detector found nothing in the one file guaranteed to be full of "
        "tolerance-shaped identifiers, so it is not detecting anything at all"
    )


_TOLERANCE_POSITIVES: tuple[tuple[str, str], ...] = (
    ("bare eps binding", "eps = 1\n"),
    ("upper-case epsilon constant", "EPSILON = 1\n"),
    ("eps as a leading component", "eps_value = 1\n"),
    ("eps as a trailing component", "relative_eps = 1\n"),
    ("tolerance parameter", "def compare(left, right, tolerance):\n    return tolerance\n"),
    ("atol keyword argument", "compare(left, right, atol=1)\n"),
    ("rtol keyword argument", "compare(left, right, rtol=1)\n"),
    ("tolerance attribute", "limit = config.tolerance\n"),
    ("pytest.approx", "import pytest\n\nassert value == pytest.approx(other)\n"),
    ("math.isclose", "import math\n\nassert math.isclose(value, other)\n"),
    ("bare approx import", "from pytest import approx\n\nassert value == approx(other)\n"),
    ("tolerance-shaped helper definition", "def within_tolerance(a, b):\n    return a == b\n"),
)

_TOLERANCE_NEGATIVES: tuple[tuple[str, str], ...] = (
    ("'steps', which merely contains eps", "steps = 3\ntotal_steps = steps\n"),
    ("a step counter attribute", "count = plan.steps\n"),
    ("exact equality against a Fraction", "assert value == Fraction(1, 2)\n"),
    ("a positive type audit", "assert type(value) is Fraction\n"),
    (
        "prose using the word approximation",
        '"""Fraction compares equal to the float it approximates."""\n',
    ),
    (
        "an allowlisted test name",
        "def test_solve_linear_keeps_an_exact_coefficient_too_small_for_any_epsilon():\n"
        "    return None\n",
    ),
)


@pytest.mark.parametrize(("label", "source"), _TOLERANCE_POSITIVES, ids=lambda v: v)
def test_the_tolerance_detector_flags_each_approximate_construct(label: str, source: str) -> None:
    """Every way of introducing a tolerance is watched being caught."""
    assert tolerance_violations(source), f"the tolerance detector did not flag {label}"


@pytest.mark.parametrize(("label", "source"), _TOLERANCE_NEGATIVES, ids=lambda v: v)
def test_the_tolerance_detector_leaves_the_exact_cases_alone(label: str, source: str) -> None:
    """The detector does not fire on exact assertions, prose, or "steps".

    ``steps`` is the case that decides whether the ``eps`` rule can be
    substring-based. It cannot: "steps" contains "eps", and a detector that
    flagged every step counter in the suite would be turned off immediately.
    """
    violations = tolerance_violations(source)
    assert not violations, f"the tolerance detector false-positived on {label}: {violations}"


# ===========================================================================
# f. The solve suite passes with the install unresolvable
# ===========================================================================
#
# CLAUDE.md section 7: "The rule suite must run on a machine with no game
# installed." That is a gate, not a property the suite happens to have. On a
# clean CI runner this child run is what CI does anyway; on the operator's
# machine, where the game IS installed, it is the only thing that reproduces
# CI's environment - and therefore the only place a test that quietly reaches
# for the real install can be caught, because there it passes.


def _child_pytest_args() -> list[str]:
    """Build the argv for the child pytest run over the solve suite.

    The recursion guard is explicit and not incidental: without ``--ignore``,
    the child collects this module, which launches its own child, forever.

    ``-p no:cacheprovider`` keeps the child from writing a .pytest_cache that
    the parent run would then read.

    Returns:
        Arguments after the interpreter.
    """
    return [
        "-m",
        "pytest",
        str(SOLVE_TESTS),
        f"--ignore={THIS_MODULE}",
        "-p",
        "no:cacheprovider",
        "-q",
    ]


def test_the_solve_suite_passes_with_the_install_unresolvable() -> None:
    """The whole solve suite exits zero with the install forced unresolvable.

    A test that reaches for the real shipped docs file, the real save root or
    the operator's config/local.json turns this red on the machine where the
    game IS installed. A test that genuinely needs an install is not forbidden;
    it must skip with a reason, and a skip keeps the exit code at zero.
    """
    child = run_child(_child_pytest_args(), no_install_env())
    exit_code = child.returncode
    assert exit_code == 0, (
        "the solve suite does not pass without a game install.\n"
        f"exit code: {exit_code}\n"
        f"stdout:\n{child.stdout}\n"
        f"stderr:\n{child.stderr}"
    )
    # Exit 0 with nothing collected is impossible (pytest exits 5), but the
    # count is asserted anyway rather than inferred: "the unrun gate is where
    # the bug hides" applies to this gate as much as to the ones it guards.
    passed = re.search(r"(\d+) passed", child.stdout)
    assert passed is not None, f"the child run reported no passing tests:\n{child.stdout}"
    assert int(passed.group(1)) > 0


def test_the_child_run_excludes_this_module_so_the_gate_cannot_recurse() -> None:
    """The recursion guard is verified against pytest's own collection, not assumed.

    ``--ignore`` silently accepts a path it does not match, so the guard working
    is a claim until pytest is asked what it collected. Both halves matter: this
    module absent, and the rest of the solve suite present. A guard that
    excluded everything would also make the test above pass.
    """
    child = run_child([*_child_pytest_args(), "--collect-only"], no_install_env())
    exit_code = child.returncode
    assert exit_code == 0, f"collection failed:\n{child.stdout}\n{child.stderr}"

    collected = child.stdout
    assert THIS_MODULE.name not in collected, (
        f"{THIS_MODULE.name} is collected by its own child run, so the gate recurses"
    )
    for sibling in SOLVE_TEST_SOURCES:
        if sibling.startswith("test_"):
            assert sibling in collected, (
                f"the child run collects no {sibling}; the ignore is too wide and the gate "
                "would pass by testing nothing"
            )
