"""Game data extraction and normalization: locate, docs_extract, registry, version.

Owns (BOOTSTRAP.md section 6): finding the install, the save root and the
account directory by auto-detection; reading the shipped English docs file
once; emitting the normalized item, recipe, building and milestone registry;
and the build-string pin plus drift guard that detect a game patch.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# This layer is the BOTTOM of the stack. Below it is the game install on disk,
# opened read-only and never written to. Above it, nothing may touch the raw
# 10 MB docs file: every consumer reads the normalized registry emitted here.
# A module outside clockspeed.data that opens a locale JSON is a design bug.
#
# Two further constraints this layer carries alone:
#   - Nothing extracted from the install is ever committed. The generated
#     registry goes to the gitignored /data/ directory; only the small content
#     hash and build-string pin are tracked (BOOTSTRAP.md section 8.1).
#   - The install path, the save root, the account directory and the world
#     name are DETECTED, never hardcoded. The account directory name is a
#     platform account id and is personal data (BOOTSTRAP.md section 2.2).
