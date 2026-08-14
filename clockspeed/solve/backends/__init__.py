"""Pluggable optimizer implementations behind the OptimizerBackend interface.

Owns (BOOTSTRAP.md section 6): one module per optimizer strategy - the
dependency-free searches that ship first, and any later gated third-party solver
that slots in behind the same interface. This file itself owns nothing but the
name to factory MAPPING and :func:`available_backends`; the objective, the
request and result shapes and the interface all live in
``clockspeed/solve/optimize.py``.

THE TWO SHIPPED BACKENDS ARE DIFFERENT MECHANISMS, NOT TWO WRITINGS OF ONE
---------------------------------------------------------------------------
That is a correctness requirement rather than variety for its own sake.
CLAUDE.md section 5: agreement between two implementations is NOT evidence,
because two implementations derived from the same idea are wrong the same way.
Two backends that both enumerated subsets and both ranked them the same way
would agree on every input including the ones where both are wrong.

- :data:`BACKEND_EXHAUSTIVE` enumerates the COMPLETE subset lattice of the
  candidate set, evaluates every member, and takes the global minimum under a
  stated tie-break. Exponential, obviously correct, and the oracle.
- :data:`BACKEND_GREEDY` never enumerates the lattice at all. It first prunes by
  a monotone REACHABILITY fixed point - an item is reachable if it is raw or
  some candidate produces it from reachable inputs - which eliminates a
  candidate on FEASIBILITY before any objective is computed for it. It then
  grows one selection incrementally, at each step scoring only the additions
  that already probed feasible. Polynomial, and a heuristic: it takes a locally
  best step and never backtracks, so it can miss a global optimum the exhaustive
  backend finds.

They therefore fail differently. The registry-order trap in the C5 fixture
catches a search that trusts declaration order; the strictly-better-but-
infeasible alternate catches a search that scores before it checks. Neither
backend can pass C5 by accident, and their agreement there is about the search
rather than about the shared evaluation.

WHY THE FACTORIES IMPORT LATE
-------------------------------
``clockspeed/solve/optimize.py`` imports this module to read the mapping, and
both backend modules import ``optimize`` for the request, result and objective
shapes. That is a genuine cycle at the seam, and the only import order that is
safe in BOTH directions is the one below: nothing here touches ``optimize`` at
module level, so this file loads standalone whichever module a caller imports
first, and each factory pulls its backend in at the moment it is selected. The
PLC0415 suppressions are coded and carry this reason, so neither can absorb an
unrelated finding on the same line.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# A backend is handed a fully formed problem and returns a solution. It reads
# no file: not a registry, not a save, not a config, not the game install. It
# is the narrowest seam in the project and it stays that way, because that is
# what makes backends interchangeable and what makes "identical results on a
# degenerate case" a meaningful test (BOOTSTRAP.md section 10, phase 3).
#
# Adding a third-party solver here is GATED: it passes the CONVENTIONS.md
# section 14 license gate first, the result is recorded in docs/LEDGER.md, and
# it must not change a single caller.

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from clockspeed.solve.optimize import OptimizerBackend

__all__ = [
    "BACKEND_EXHAUSTIVE",
    "BACKEND_FACTORIES",
    "BACKEND_GREEDY",
    "available_backends",
]

#: The complete enumeration of the candidate subset lattice. Exact and slow.
BACKEND_EXHAUSTIVE: Final = "exhaustive"

#: The reachability-pruned incremental search. Fast and heuristic.
BACKEND_GREEDY: Final = "greedy"


def _exhaustive() -> OptimizerBackend:
    """Construct the complete-enumeration backend.

    Returns:
        A fresh instance.
    """
    from clockspeed.solve.backends.exhaustive import ExhaustiveBackend  # noqa: PLC0415

    return ExhaustiveBackend()


def _greedy() -> OptimizerBackend:
    """Construct the reachability-pruned incremental backend.

    Returns:
        A fresh instance.
    """
    from clockspeed.solve.backends.greedy import GreedyBackend  # noqa: PLC0415

    return GreedyBackend()


#: Every backend this build has, by name. The ONE place a name is bound to an
#: implementation: ``optimize.select_backend`` reads it and refuses anything
#: absent from it rather than falling back, so registering a new backend here is
#: the whole cost of adding one and no caller changes.
#:
#: A read-only proxy rather than a plain dict. A caller mutating this at runtime
#: would make ``available_backends()`` disagree with what a later solve actually
#: ran, which is the same class of defect as a silent fallback.
BACKEND_FACTORIES: Mapping[str, Callable[[], OptimizerBackend]] = MappingProxyType(
    {
        BACKEND_EXHAUSTIVE: _exhaustive,
        BACKEND_GREEDY: _greedy,
    }
)


def available_backends() -> tuple[str, ...]:
    """Name every backend this build can select.

    Returns:
        The names in sorted order, so the list a refusal prints and the list a
        caller enumerates are the same on every run and on every machine.
    """
    return tuple(sorted(BACKEND_FACTORIES))
