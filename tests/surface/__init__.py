"""Tests for the surface layer: the response contract, the server, the endpoints.

A package for the same reason ``tests/data``, ``tests/solve`` and ``tests/save``
are - a unique dotted name per module, so a ``test_contract.py`` here can never
collide during collection with a ``test_contract.py`` added elsewhere later.

Three rules bind every module in this directory.

- **Nothing here may require a game install, a save file or a listening
  socket.** The rule suite runs green on a machine that has never had the game
  on it (BOOTSTRAP.md section 8.1), and a test that binds the allocated port
  fails on any machine already running the dashboard. The response contract is
  pure data and is tested as pure data.
- **No real world content, ever.** Not a world name, not an account id, not a
  token, not a save path (non-negotiables 3 and 11). Every endpoint template
  here is one this repository authored, and every payload value is invented.
- **An assertion binds a SCALAR before it fires.** pytest renders the asserted
  EXPRESSION independently of the message, so ``assert not leaked`` prints the
  leaked values. Compute the count, then assert on the count. This project
  shipped a leak inside its own privacy guard exactly that way, and
  ``memory/test-quality-failure-classes.md`` records the class.

The surface layer is the last place a value can escape this machine, so a test
here that proves a shape without proving what the shape EXCLUDES has proven the
cheaper half.
"""
