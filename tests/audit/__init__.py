"""Tests for the audit layer: the placement and inventory models over one world.

A package for the same reason ``tests/save`` and ``tests/solve`` are - a unique
dotted name per module, so a ``test_placement.py`` here can never collide during
collection with a ``test_placement.py`` added elsewhere later.

Four rules bind every module in this directory.

- **Nothing here may require a game install or a save file.** The suite runs
  green on a machine that has never had the game on it and on which no save
  has ever existed. Every fixture is a SMALL SYNTHETIC ``WorldModel`` literal
  hand-built in the test module that uses it (BOOTSTRAP.md section 8.1). A
  fixture cut from a real save or a real docs file is a fixture built parallel
  to the implementation, and CONVENTIONS.md section 7.2 records that those stay
  green through the real defect.
- **No real save data, ever.** Not a slice, not a trimmed copy, not a hex
  excerpt, not a world name, not an account id, not a token (non-negotiables 3
  and 11). Every string in a fixture here is invented and obviously synthetic,
  and every world token is a made-up 22-character base64url literal.
- **A refusal is asserted STRUCTURALLY, never by naming the fields that are
  known to be safe today.** The three things this layer must never publish - a
  float, an instance name, and a position (a record index, a byte offset or a
  filesystem path) - are each graded by walking everything reachable from the
  returned model and asserting the forbidden shape is absent, with the input
  fixture as the control that the walk can see one when it is there. An
  assertion listing today's field names passes unchanged the day a field is
  added.
- **A model that says nothing must say so.** An empty node list, an empty
  built list and an empty inventory total are all indistinguishable from a
  world that genuinely holds none of those, so each is graded for the WARNING
  that separates the two (non-negotiable 7). A test that asserts only the empty
  collection is a test that passes on the silent-wrong-answer defect.

The layer under test consumes ONE ``clockspeed.save.world.WorldModel`` and
computes. It never opens a save and never opens the raw docs file, which is why
no module here imports ``clockspeed.save.world.load_world``.
"""
