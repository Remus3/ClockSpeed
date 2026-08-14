---
name: unknown-content-is-flagged-not-fatal
description: Unknown actors, recipes and buildings are logged, skipped and flagged - never fatal and never silently wrong.
metadata:
  type: project
---

Unknown game content is flagged and skipped. It is never fatal, and it is never silently
absorbed into a number.

Concretely:

- **An unknown actor class is logged and skipped** by the save parser, never fatal. This
  single decision is what makes mod tolerance nearly free rather than a separate project.
- **The registry tolerates unknown recipes and buildings**, flags them, and marks any solve
  that touched one as containing unmodeled content. The flag propagates with the result; it
  does not stop at the layer that noticed.
- All identifiers are namespaced so modded content cannot collide with vanilla.

**The invariant: a modded save must never produce a crash or a silently wrong number.** An
explicit "this world contains content I do not model" plus a reduced answer is acceptable.
A confident wrong answer is not. Those are the only two outcomes worth distinguishing, and
the second is the one that destroys trust, because the operator has no way to detect it.

The asymmetry is the point. A skipped actor costs the operator some coverage and they know
it. An unmodeled recipe quietly treated as absent costs them a factory rebuild and they
find out from the game, not from the tool.

**Why:** The advisor's value is entirely a function of whether its numbers can be trusted
without re-deriving them by hand. A tool that is loudly incomplete stays useful; a tool that
is quietly wrong is worse than no tool, because the operator stops checking. Flagging also
keeps mod support architecturally first-class while the actual per-mod content work stays
backlogged - the architecture absorbs unknown content today, and modelling it is a later,
separately triggered piece of work.

**How to apply:** Every parse and solve path needs a defined behavior for content it does
not recognise, chosen at write time rather than discovered by an exception in the field.
When adding a lookup, decide what happens on a miss: log, skip, flag the enclosing result,
and carry the flag outward to the surface. Never let a miss raise, and never let a miss
silently degrade to a zero, an empty list or a default that reads as real data.

Related: [[no-language-model-in-the-advice-path]], [[game-data-is-publisher-owned]],
[[test-quality-failure-classes]].
