---
name: game-data-is-publisher-owned
description: Game data dumps, saves and extracted resources belong to their publisher - read at runtime, gitignore, ship only extraction code and synthetic fixtures.
metadata:
  type: reference
---

Game and application data assets - data dumps, save files, extracted resources, shipped
docs files, property mappings, headers - are owned by their publisher. Ownership does not
change because the files sit on the local disk or because the operator bought the game.

The rule that follows:

- **Read them from the local install at runtime.** Never vendor them into the repo.
- **Gitignore them**, along with every artifact derived from them by extraction, before the
  first commit. Retrofitting this after a commit means rewriting history.
- **Ship only extraction code plus small hand-authored synthetic fixtures.** The tracked
  artifact is the code that reads the data and a content hash plus version pin that proves
  which data was read - not the data.

**Test fixtures are never slices of real game data.** They are small registries authored by
hand in the repo. This buys two things at once, which is why it is worth the effort of
writing them:

1. The repo stays clean of publisher-owned content, so the public-flip gate has nothing to
   find in the tree or in history.
2. The rule suite runs on a machine with no game installed. A suite that needs the game
   present is a suite that does not run in CI, and an unrun gate is where the bug hides.

**The always-legal path when something must be reproduced:** re-implement the mechanic in
the project's own code from observed behavior. Techniques and protocol facts are not
copyrightable; source is. So a format, a layout, an exponent or a serialization convention
may be learned by observation and reimplemented freely, while lifting the publisher's files
or a third party's source may not.

Two adjacent traps from the same license neighbourhood: a community-compiled dataset
carries provenance risk that a later public flip makes worse, and any third-party
asset-parsing library goes through the license gate BEFORE use with the result stated
explicitly in the ledger. Verbal clearance is not written clearance, and absence of a
LICENSE file is not permission.

Related: [[save-files-carry-pii]], [[never-write-to-the-game]],
[[unknown-content-is-flagged-not-fatal]].
