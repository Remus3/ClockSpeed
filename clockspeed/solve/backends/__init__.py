"""Pluggable optimizer implementations behind the OptimizerBackend interface.

Owns (BOOTSTRAP.md section 6): one module per optimizer strategy - the
dependency-free branch-and-bound or weighted-greedy search that ships first,
and any later gated third-party solver that slots in behind the same
interface.
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
