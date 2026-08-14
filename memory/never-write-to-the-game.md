---
name: never-write-to-the-game
description: Clockspeed never writes to the game install or a save file - saves are copied to a work directory before parsing.
metadata:
  type: project
---

Clockspeed never writes to the game install directory and never modifies a save file. This
is not a preference and not a default that a flag may relax - it is an invariant.

The operational form of the invariant:

- **Saves are COPIED to a work directory before parsing.** Nothing is ever parsed in place.
- The save directory - `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\<auto-detected account
  dir>` - is opened for read only, and never opened for write for any reason.
- The game install directory is read-only material: the shipped docs, the property mapping
  file, the custom-versions data and the headers are read where they lie and never touched.
- Parsing must be provably read-only, not merely intended to be. Phase 4 acceptance
  includes asserting that the save directory is never opened for write.

**The mechanism behind the copy rule.** The game holds file handles during autosave. Parsing
in place will eventually hit a locked file or a half-written one - not on the first run,
which is what makes it dangerous, but on the run that happens to overlap an autosave. The
failure is intermittent, timing-dependent and looks like a corrupt-save bug rather than a
concurrency bug. Copying first turns a race into a snapshot.

Support both manual saves and autosaves, defaulting to the most-recently-modified across
both, and take the copy before doing anything else with the file.

**Why:** The operator's world is irreplaceable and the product's entire value proposition
depends on being safe to point at a live game. One corrupted save would end the project's
usefulness regardless of how good the advice is. Stating it as an invariant rather than a
policy is deliberate: an invariant is something a test asserts, and a preference is
something a later session negotiates away.

**How to apply:** Any new code path that touches a game or save path opens it read-only and
operates on the work-directory copy. If a feature seems to need a write - an in-place fix,
a repair, a migration, a marker file - it is out of scope by definition; produce advice
about it instead. Assert the invariant in tests rather than trusting review to catch it.

Related: [[save-files-carry-pii]], [[game-data-is-publisher-owned]],
[[world-token-is-the-ledger-key]].
