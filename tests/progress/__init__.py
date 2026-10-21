"""Tests for the progress layer: the milestone and phase requirement models.

A package for the same reason ``tests/save`` and ``tests/solve`` are - a unique
dotted name per module, so a ``test_milestones.py`` here can never collide
during collection with a ``test_milestones.py`` added elsewhere later.

Four rules bind every module in this directory.

- **Nothing here may require a game install or a save file.** The suite runs
  green on a machine that has never had the game on it and on which no save
  has ever existed. Every fixture is a SMALL SYNTHETIC schematic document and a
  SMALL SYNTHETIC ``UnlockState`` hand-built in the test module that uses it
  (BOOTSTRAP.md section 8.1). A fixture cut from a real docs file is a fixture
  built parallel to the implementation, and CONVENTIONS.md section 7.2 records
  that those stay green through the real defect.
- **No real save or docs data, ever.** Not a slice, not a trimmed copy, not a
  hex excerpt, not a world name, not an account id, not a token
  (non-negotiables 3 and 11). Every asset path in a fixture here is invented
  and obviously synthetic.
- **A refusal is asserted STRUCTURALLY, never by naming the fields that are
  known to be safe today.** The thing this layer must never publish is a float
  in a rate, and it is graded by walking everything reachable from the returned
  model and asserting the forbidden shape is absent, with the input fixture as
  the control that the walk can see one when it is there. An assertion listing
  today's field names passes unchanged the day a field is added.
- **A model that says nothing must say so.** An empty cost list and an unread
  HUB tier are both indistinguishable from a target that genuinely requires
  nothing, so each is graded for the WARNING that separates the two
  (non-negotiable 7). A test that asserts only the empty collection is a test
  that passes on the silent-wrong-answer defect.

The layer under test consumes the shipped schematic entries through a protocol
and one ``clockspeed.save.world.UnlockState``, and computes. It never opens a
save and never opens the raw docs file.
"""
