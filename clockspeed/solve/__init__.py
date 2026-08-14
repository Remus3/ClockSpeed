"""The deterministic engine: exact arithmetic, ratio solve, optimize, power.

Owns (BOOTSTRAP.md section 6): Fraction primitives, the pillar 1 target-rate
production solve, pillar 2 recipe selection behind the OptimizerBackend
interface, and the power and clock-speed mathematics.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer is the normalized registry from clockspeed.data. That is
# the ONLY input. solve/ never reads a save: a caller that wants "solve
# against my world" reads the world model itself and hands this layer plain
# quantities. An import of clockspeed.save from anywhere under solve/ is the
# canonical example of a layer reaching past its neighbor.
#
# Two invariants this layer carries alone:
#   - Exact rational arithmetic end to end (fractions.Fraction). Floating
#     point drift in a ratio calculator is a correctness bug, not a rounding
#     nuisance. The absence of floats in the solve path is ASSERTED, not
#     assumed (BOOTSTRAP.md section 10, phase 3 acceptance).
#   - No external optimizer dependency. Search runs behind OptimizerBackend so
#     a gated dependency can later slot in without changing a single caller
#     (BOOTSTRAP.md section 11).
