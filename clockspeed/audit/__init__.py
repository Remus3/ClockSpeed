"""Pillar 3: the whole-world audit of what is built against what should be.

Owns (BOOTSTRAP.md sections 4 and 6): idle and starved machines with their
upstream cause, overclock waste, belt and pipe saturation with the binding
segment, power headroom and brownout risk, under-extracted claimed nodes, and
achieved sink-point throughput.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer are two stated models: the world model from
# clockspeed.save.world and the results of clockspeed.solve. This layer never
# opens a .sav and never opens the raw docs file - it diffs one model against
# the other and reports findings.
#
# A finding is a fact with a cause attached. "This machine is idle" is half an
# audit; "this machine is idle because the segment upstream is saturated" is
# the whole one. Reporting the symptom without the binding constraint pushes
# the work onto the operator, which is the one budget this project spends
# against (CONVENTIONS.md section 0).
