"""Tests for the solver core: exact primitives, ratio solve, power, optimizer.

A package for the same reason ``tests/data`` is one - a unique dotted name per
module, so a ``test_power.py`` here can never collide during collection with a
``test_power.py`` added under ``tests/audit`` later.

Three rules bind every module in this directory. The first two are inherited
from the phase 2 criterion; the third is what phase 3 adds and is the reason
this suite exists as its own package.

- **Nothing here may require a game install.** The rule suite runs green on a
  machine that has never had the game on it, so a test that reaches for the
  real ``en-US.json`` fails the gate it is supposed to prove. The solve corpus
  in ``tests/solve/synthetic.py`` is built for exactly this.
- **Fixtures are hand-authored synthetic material, never a slice of real game
  data** (BOOTSTRAP.md section 8.1). A fixture cut from the real file is a
  fixture built parallel to the implementation, and CONVENTIONS.md section 7.2
  records that those stay green through the real defect.
- **No tolerance comparison, anywhere.** Not ``pytest.approx``, not
  ``math.isclose``, not an epsilon. The solve path is exact rational arithmetic
  end to end (non-negotiable 6), so a tolerance here would not be a loose test -
  it would be a test that CANNOT fail on the defect it exists to catch. Note in
  particular that ``==`` alone is not sufficient evidence of exactness either:
  ``Fraction(1, 2) == 0.5`` is ``True``, so equality passes against a float that
  happens to land on the same value. Assertions pair structural equality with a
  positive type audit - ``type(x) is Fraction`` rather than ``isinstance`` -
  because ``isinstance(True, int)`` is also ``True``.

``tests/solve/test_phase3_gate.py`` enforces the third rule mechanically rather
than leaving it to review.
"""
