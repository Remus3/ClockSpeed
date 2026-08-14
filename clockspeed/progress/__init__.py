"""Pillar 4: milestone and progression routing to any selected target.

Owns (BOOTSTRAP.md sections 4 and 6): the dependency-ordered plan of what must
be added, upgraded, redesigned or torn down to reach a chosen milestone or
phase target from the current world state.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer are the world model from clockspeed.save.world, the
# normalized registry from clockspeed.data, and clockspeed.solve. This layer
# never opens a .sav and never opens the raw docs file.
#
# Two product constraints this layer carries alone:
#   - The target is a FREE selector, not a fixed pointer at "next". Selecting
#     a target three tiers out and getting a redesign plan is a required
#     capability, not a stretch goal (BOOTSTRAP.md section 11).
#   - Output is dependency-ORDERED, and it distinguishes "you need more of
#     this" from "you need to REPLACE this". The second is the expensive one
#     and must be called out as such.
