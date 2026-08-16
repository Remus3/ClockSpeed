# 0008 - a detection claim is derived by the suite, never written in prose

## Status

`proposed` - 2026-08-16

Written by the merger that made the decision. Per `CLAUDE.md` section 5 the producing agent
does not grade its own output, so this stays `proposed` until an adjudicator that wrote no
part of it, and no part of the slices implementing it, re-derives the claims below from the
tree and flips it.

## Context

A DETECTION CLAIM is a sentence about which test goes red under which fault. Examples from
the tree: "the reach test is the only one of the three that discriminates the widths"; "this
join does not guard the common mode"; "it is contained in `test_properties` on every mutant
measured so far".

`tests/save/test_decode_oracles.py` accumulated four such sentences that were measurably
false at `8b3fb9d`, and `clockspeed/save/objects.py` carried a fifth of the same family that
no item had listed. That is not a lapse of care. THREE CONSECUTIVE ROUNDS OF PROSE REPAIR
EACH SHIPPED A FALSE SENTENCE, one of them written specifically to correct its predecessor,
and the last was falsified BY ITS OWN COMMIT: adding the `_JOIN_WORD_FLOOR` diversity floor
changed what the join test measures, which made four sentences in the same commit false.
Three failures by three careful authors is a property of the medium, not of the authors.

THE MECHANISM, stated as the thing that generalises. A detection claim is a MEASURED FACT
about the suite. `CLAUDE.md` section 4 already governs measured facts - they live in exactly
one machine-checked place and are never restated in prose, because "a hardcoded count in a
doc is a lie with a timestamp on it". The rule was already written. What nobody had noticed
is that A SENTENCE CAN BE A MEASURED NUMBER. "Only the reach test grades the widths" is a
measurement of the whole suite, restated in prose, with no guard - the identical failure
class as a hardcoded count, wearing different clothes.

WHY QUANTIFIER SCOPE IS THE DISCRIMINATOR, and not tone or confidence. What separates the
sentences that rotted from the sentences that survived three rounds is the size of their
FALSIFICATION SURFACE:

- An EXISTENTIAL claim - "mutating the shipped tag cap reddens this test while the agreement
  test stays green" - is falsified only by a change to its own subject. It is local, one
  measurement checks it, and it stays true when a test is added elsewhere.
- A UNIVERSAL claim - "the only one", "nothing else", "does not guard", "on every mutant
  measured so far" - is falsified by ANY change ANYWHERE in the suite, including additions
  that have nothing to do with the file. No local edit can be reviewed against it. This is
  not theoretical: adding one assertion to one test falsified four sentences at once.

Universal detection claims are therefore UNVERIFIABLE BY CONSTRUCTION. A mutant-to-detector
table cannot rescue them either - a table covers the mutants in the table, while "the only
one" quantifies over every test for all time. Checking one would mean running the entire
suite against every conceivable fault on every commit.

WHAT MADE THE ALTERNATIVE AFFORDABLE, measured at `8b3fb9d` on the operator's machine
against the live save library. `objects._TAG_EXTRA_STRINGS` is read as a module global at
call time, so a monkeypatch of the SHIPPED constant is a genuine mutant with no subprocess,
no repo copy and no stale-`__pycache__` hazard. One oracle sweep costs about 1.6 seconds and
all six widths cost about 12.9 seconds. Deriving the relation at runtime is cheaper than the
prose was to maintain.

That derivation also CORRECTED the claim it replaced rather than merely policing it. Against
single-copy width mutants the join's BIJECTION assertions are blind to all six widths, while
the join's WORD-DIVERSITY FLOOR fires on all but one. Both follow from one mechanism read at
two quantities: a wrong width breaks the walk, a broken walk contributes fewer pairs, and
every surviving pair is still correct - so a bijection over a shrinking population of correct
pairs stays pristine while a diversity count over that same population does not. The prose
had the mechanism right and OVER-APPLIED it from the bijection to the whole test. A machine
check found a real error that three rounds of careful reading did not.

Alternatives considered and rejected:

- KEEP REPAIRING THE PROSE. Rejected by track record. Three rounds, three false sentences.
- WRITE THE MUTANT-TO-DETECTOR TABLE DOWN as data in the repo. Rejected: a written table is a
  restated measurement, which is the thing section 4 forbids, and it rots the first time an
  assertion changes - the exact failure being fixed.
- DELETE ALL DETECTION COMMENTARY. Rejected as too wide. Mechanistic claims about the code
  beside them are what make a test reviewable, and they do not share the failure mode.

## Decision

**A detection claim is a measured fact and is governed by `CLAUDE.md` section 4. It is
derived by the suite at runtime, or it is deleted. It is not written down.**

Three tiers, discriminated by quantifier scope:

1. **UNIVERSALLY-QUANTIFIED detection claims are DELETED, and are not written again.**
   Markers: "the only one that", "only X grades", "does not guard", "nothing else catches",
   "on every mutant measured so far". They are unverifiable by construction, so no machine
   check rescues them and no rewording makes them safe. Deleting is the whole remedy.
2. **EXISTENTIAL detection claims are DERIVED BY THE SUITE, never stated.** The
   mutant-to-detector relation is computed at runtime and asserted structurally - "every
   width is caught by at least one detector" - with no absolute count written anywhere.
3. **MECHANISTIC claims about the code beside them REMAIN PROSE.** They rot only when that
   code changes, they sit next to what they describe, and a reader checks them by reading.

A derived detection test carries the vacuity controls this project already requires: it
asserts its own population is non-empty, and it distinguishes a mutant that was DETECTED
from one that merely CRASHED.

## Consequences

EASIER. A detection claim can no longer silently rot, because there is no longer a place to
write one that nothing checks. Adding a width extends the derived loop instead of
invalidating a paragraph. The commit that adds an assertion cannot falsify its own prose,
because the prose no longer states what the assertions detect.

HARDER. A derived detection test costs a real mutation sweep, so it is library-backed
wherever the oracle is. On a clone with no game installed it SKIPS. **This ADR does not close
that gap and must not be read as closing it - `CS-426` owns the CI half and stays open.**
Writing a detection claim now costs code rather than a sentence, which is the intended
price.

FORECLOSED. Re-pitching any of these: a prose detection claim "just this once" because the
measurement is fresh; a written mutant-to-detector table in the repo; a superlative or
universal negative about which test catches what, in a docstring, a comment, a commit
message or a roadmap entry; and rewording a universal claim into a hedge ("believed to be
the only", "so far the only") rather than deleting it - the hedge has the same falsification
surface and reads as evidence.

REVISIT IF. The premise that a shipped grammar constant is monkeypatchable in process stops
holding - if a constant is inlined, frozen at import, or read into a local at module load,
the cheap in-process mutant disappears and tier 2 gets materially more expensive. Re-measure
before assuming the sweep is still seconds rather than minutes.

SCOPE, stated so this is not read as wider than it is. This ADR governs DETECTION claims -
statements about which test catches which fault. It does not govern claims about what code
does, what a measurement found at a stated time, or what an item decided. It applies
repository-wide as a rule for authors; the mechanical fence for it is scoped to where such
claims actually cluster, and widening that scan is separate work.
