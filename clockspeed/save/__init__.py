"""Save file reading: header, chunks, usmap, objects, and the world-state model.

Owns (BOOTSTRAP.md section 6): the save header parse, chunk decompression and
walk, the property-mapping (usmap) loader, actor and component
deserialization, and world.py - the single world-state model that everything
above this layer consumes.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# Below this layer is a COPY of a save file plus the usmap from the install.
# The copy is not optional: the game holds handles during autosave, so parsing
# in place eventually hits a locked or half-written file (BOOTSTRAP.md
# section 8.2). The save directory is never opened for write.
#
# Above this layer, nothing sees save bytes. The stated model is world.py.
# A module outside clockspeed.save that reads a .sav is a design bug.
#
# Three invariants this layer carries alone:
#   - An unknown actor class is logged and SKIPPED, never fatal. That single
#     decision is what makes mod tolerance nearly free (BOOTSTRAP.md
#     section 9), and a modded save must never crash or produce a silently
#     wrong number.
#   - The header options string is PII-bearing: it embeds the platform name, a
#     platform account identifier and the player's display name as plaintext
#     hex. It is redacted by default, and rendering it requires an explicit
#     opt-in flag. Any path that echoes raw header bytes - error messages,
#     debug dumps, hex previews, log lines, exception context - leaks it.
#   - Version dispatch is a day-one requirement, not a future concern: the
#     operator's own library already spans two save versions.
