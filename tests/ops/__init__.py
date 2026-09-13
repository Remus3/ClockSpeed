"""Tests for the headless lane package, ``ops/``."""

from typing import Final

#: ``CS420_FENCED`` subjects this module's prose to the unbounded-quantifier
#: rule in ``tests/save/test_absolute_claims.py``. It is declared because the
#: scan already reports no finding here, so the fence costs no disposition on
#: prose already written - it records a state this module has REACHED and stops
#: it regressing. Unfencing takes two edits, this marker and the tuple entry
#: there, and neither is silent on its own.
CS420_FENCED: Final = True
