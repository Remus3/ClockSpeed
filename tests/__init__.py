"""The Clockspeed test suite.

This is a real package rather than a loose directory of files, on purpose:

- It gives every test module a unique dotted name, so two modules named
  test_scaffold.py in different directories can never collide during
  collection - a silent, confusing failure when it happens.
- It makes the repo root the import root under pytest's default import mode,
  which is how ``import clockspeed`` resolves from a source checkout with
  nothing installed.

Suite conventions:

- Run from the repo root with an explicit target, never a bare recursive
  invocation - pyproject.toml pins ``testpaths`` for exactly that reason
  (CONVENTIONS.md section 7.1).
- Fixtures are dependency-free: standard library plus pytest. A test harness
  that needs a dependency installed is a harness that does not run on a clean
  machine, and the rule suite must run on a clean machine with no game
  installed (BOOTSTRAP.md section 5.4).
- Fixtures are never allowed to touch the game install or a save file.
  Test data is small synthetic material hand-authored in the repo, never a
  slice of real game data and never a real save (BOOTSTRAP.md section 8.1).
"""
