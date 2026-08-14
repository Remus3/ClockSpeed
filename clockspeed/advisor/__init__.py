"""Pillar 5: the advisor - trace, cards, ledger, and the rule families.

Owns (BOOTSTRAP.md sections 5 and 6): the rule execution trace that is the
source of all three explain tiers, card identity and rendering, and the
per-world ledger plus global per-rule mutes written atomically.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer are clockspeed.audit, clockspeed.progress and
# clockspeed.solve, plus the normalized registry. advisor/ never reads the raw
# docs file, and it never opens a .sav.
#
# Four invariants this layer carries alone:
#   - ONE trace, THREE projections. Tier 1 headline, tier 2 reason and tier 3
#     derivation are all generated from the same rule execution trace, so they
#     cannot drift from each other. Tier 3 is never hand-written
#     (BOOTSTRAP.md section 12 item 8).
#   - Card identity is a deterministic hash of (rule_id, subject_key,
#     target_milestone). Recomputing on a changed save must produce the SAME
#     id for the same underlying advice, or every piece of persisted state is
#     lost on reload.
#   - The ledger is keyed by the world token carried in the save header, never
#     by a save filename and never by a world name. Filenames change on every
#     save and autosaves rotate. An unseen key is a NEW world, not a failure.
#   - Zero language model, zero cloud service, zero API key. The tier-3
#     derivation is generated from the trace, which is exactly why no model is
#     needed (BOOTSTRAP.md section 11 - settled, do not re-litigate).
