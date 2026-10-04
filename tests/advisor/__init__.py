"""Tests for the advisor layer: the rule trace, cards and the ledger.

A package for the same reason ``tests/audit`` is - a unique dotted name per
module, so a ``test_trace.py`` here never collides during collection with one
added elsewhere later.

Nothing here may require a game install or a save file (BOOTSTRAP.md section
5.4). Every world is a small synthetic literal or comes from the seeded
generator in ``tests/advisor/worlds.py``; every string in a fixture is invented
and obviously synthetic.
"""
