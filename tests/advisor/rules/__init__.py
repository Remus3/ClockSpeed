"""Tests for the advisor rule families - synthetic fixtures only, no save and no game install."""

from typing import Final

#: ``CS420_FENCED`` subjects this module's prose to the unbounded-quantifier
#: rule in ``tests/save/test_absolute_claims.py``, on the same terms as
#: ``tests/advisor/__init__.py``: declared because the scan reports no finding
#: here, so the fence records a reached state and stops it regressing.
#: Unfencing takes two edits, this marker and the tuple entry there.
CS420_FENCED: Final = True
