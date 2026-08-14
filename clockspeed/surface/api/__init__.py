"""JSON endpoints: health, world, advice, derivation, state, solve, audit, plan.

Owns (BOOTSTRAP.md section 7.1): the serialization of models produced below
into the documented JSON endpoint set, and nothing else.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# An endpoint serializes a model and returns it. It performs no arithmetic, no
# ranking and no recipe choice - see the parent package. It also opens no
# file: not a save, not the raw docs, not the game install. An endpoint that
# reaches for the filesystem has reached past two neighbors at once.
#
# One privacy constraint this layer carries alone: an endpoint response is the
# easiest place for personal data to escape. The save header options string
# carries a platform account identifier and the player's display name, and the
# save directory is named after a numeric account id. Neither is ever
# serialized, logged in a request line, or echoed back in an error body
# (BOOTSTRAP.md section 2.2).
