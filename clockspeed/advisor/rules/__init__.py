"""One module per rule family, data-driven: node siting, transport, gaps, power.

Owns (BOOTSTRAP.md sections 5.3 and 6): the four v1 advice domains - D1 node
siting and claim order, D2 process onsite versus transport and by what method,
D3 milestone gap analysis against any target, and D4 power and fuel planning.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# A rule consumes only the inputs it DECLARES, handed to it by the trace
# engine. It opens no file of its own. Reading an undeclared input is a bug
# and a test catches it, because the trace - and therefore the tier-3
# derivation the operator reads - is generated from that declaration. An
# undeclared read produces a derivation that lies.
#
# Three further constraints (BOOTSTRAP.md section 5.4):
#   - Rules are DATA-DRIVEN. A game patch that changes recipes, buildings or
#     milestones is absorbed by re-running the extractor and moving a version
#     pin. If a patch forces a rule edit, that rule encoded a fact it should
#     have read from data - fix the rule, not just the symptom.
#   - Every rule declares which unlocks it requires, so it cannot suggest
#     something the player cannot build. No rule may recommend an action whose
#     preconditions are unmet: that is an invariant with a property test over
#     generated world states, not a code review item.
#   - Every rule is testable against a synthetic world fixture with no save
#     file and no game install present. The rule suite runs on a clean machine.
