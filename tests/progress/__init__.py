"""Tests for the progression layer: the milestone and phase models (pillar 4).

A package for the same reason ``tests/solve`` and ``tests/audit`` are one - a
unique dotted name per module, so a ``test_phases.py`` here can never collide
during collection with a module of the same name added elsewhere later.

Three rules bind every module in this directory.

- **Nothing here may require a game install or a save file.** Every fixture is
  a SMALL SYNTHETIC schematic document, registry or unlock state hand-authored
  in the test module that uses it, and loaded through the same seams the
  shipped code reads (CLAUDE.md section 7). Every class name and amount below
  is invented and obviously synthetic.
- **No tolerance comparison, anywhere.** The rates and counts are exact
  Fractions, so equality is paired with a type audit - ``type(x) is Fraction``
  - because ``Fraction(1, 2) == 0.5`` is ``True`` and equality alone passes
  against a float that happens to land on the same value.
- **An unknown is asserted as None WITH ITS NAMED REASON, never as a falsy
  value.** Zero is a real onboarding tier and an empty mapping is a real
  free schematic, so ``not value`` cannot tell an unavailable figure from a
  measured one and no arm here uses it.
"""
