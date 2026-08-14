"""Tests for the data layer: install location, docs extraction, registry.

A package for the same reason ``tests`` itself is one - a unique dotted name
per module, so a ``test_version.py`` here can never collide during collection
with a ``test_version.py`` added under ``tests/save`` later.

Two rules bind every module in this directory, and both come from the phase 2
acceptance criterion rather than from taste:

- **Nothing here may require a game install.** The criterion for CS-200 is that
  this suite runs green on a machine that has never had the game on it, so a
  test that reaches for the real ``en-US.json`` fails the gate it is supposed
  to prove. Tests that describe live-install behaviour construct their inputs
  from the synthetic corpus in ``tests/data/synthetic.py`` instead, and the
  handful that genuinely need the real file skip explicitly and say why.
- **Fixtures are hand-authored synthetic material, never a slice of real game
  data** (BOOTSTRAP.md section 8.1). This is not only a licensing position. A
  fixture cut from the real file is a fixture built parallel to the
  implementation, and CONVENTIONS.md section 7.2 records that those stay green
  through the real defect. The synthetic corpus is written from the MEASURED
  grammar in BOOTSTRAP.md section 3.2 - including the cases that grammar makes
  awkward, such as a fluid amount that is not a multiple of 1000 and a
  ``/Script/`` token carrying no ``.`` separator.
"""
