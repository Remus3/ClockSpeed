"""Tests for the save layer: header parse, chunk walk, usmap load, actor deserialization.

A package for the same reason ``tests/data`` and ``tests/solve`` are - a unique
dotted name per module, so a ``test_header.py`` here can never collide during
collection with a ``test_header.py`` added elsewhere later.

Four rules bind every module in this directory.

- **Nothing here may require a game install or a save file.** The suite runs
  green on a machine that has never had the game on it. Every byte a phase 4
  test parses is built by ``tests/save/synthetic.py``. The one test that looks
  at a real save SKIPS WITH A REASON when none is present, and compares shapes
  rather than values even when one is.
- **No real save data, ever.** Not a slice, not a trimmed copy, not a hex
  excerpt, not a world name, not an account id, not a token (non-negotiables 3
  and 11, CLAUDE.md section 7). Every string in the corpus is invented and
  obviously synthetic, and every world token is a made-up 22-character
  base64url literal.
- **Nothing here may echo raw header bytes.** Non-negotiable 12: the header
  carries platform, account and player-display-name strings in plaintext inside
  its options string, so a debug dump, a hex preview, an exception message or a
  pytest assertion repr all count as echo paths. Assertions that touch a real
  save bind derived SCALARS to locals and compare those, never the decoded text
  - the same discipline ``tests/data/test_phase2_gate.py::run_child`` records
  for the interpreter path.
- **The builder is verified, not trusted.** ``tests/save/test_synthetic.py``
  cross-checks it with a minimal reader written from scratch in that module.
  A fixture checked with the parser it feeds would be checked by the code most
  likely to share its mistake.

That last rule is the reason this corpus exists as its own slice, ahead of any
parser. Every phase 4 module is written against these bytes, so a wrong byte
layout here does not fail: it teaches every suite above it to expect the wrong
layout, and all of them agree. CLAUDE.md section 5 names why that is invisible
- agreement between two agents is not evidence - and
``memory/test-quality-failure-classes.md`` names the mechanism: a fixture built
parallel to the implementation stays green through the real defect.
"""
