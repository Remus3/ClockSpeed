---
name: a-proof-can-require-the-defect
description: A check that derives its cases from today's tree goes RED when the defect is fixed, so green certifies the defect is still present.
metadata:
  type: reference
---

# A proof can require the defect it certifies against

**Filed 2026-08-25 (session 39), from three items refuted independently in one session.**

A guard or a proof that DERIVES ITS OWN TEST CASES from the current state of the tree
encodes today's defects as its passing condition. Repairing the defect turns the proof RED,
so a green run is evidence that the defect is still present. This is the inverse of the
usual failure: the check is not too weak, it is ANTI-CORRELATED WITH SUCCESS.

## The three measured instances

- **Derived from live findings.** A privacy guard built its forced-failure arms from the
  set of LIVE leaks it had found. Fixing a leak removed an arm and broke the proof. Measured:
  3 live modules green, 2 red, 1 red, 0 red. A green run certified that at least three
  modules still leaked.
- **Fitted to today's data.** An equality bound (`x == CEILING`) was set to the value
  measured on one machine's save library at one instant. Two of three LEGITIMATE library
  subsets reddened it, in BOTH directions, with no shipped code touched - autosave rotation
  alone would have broken it. Its failure message also misdiagnosed its own condition,
  calling a widening a narrowing.
- **Rules selected by their false-positive score.** Three analysis rules were kept because
  each measured ZERO findings on the current tree. Four of eight genuinely correct idioms
  reddened once probed with code the tree did not happen to contain, and one rule scored
  zero only because the tree contains no `match` statement at all.

## How to tell, before shipping

Ask: **what does this proof do when the thing it grades is perfect?** If the answer is
"goes red", "selects nothing", or "cannot find a case", the proof is measuring the defect
rather than the property. Derive test cases from DECLARATIONS, from SYNTHETIC fixtures, or
from the SHAPES the checker claims to catch - never from the findings, the failures, or the
current population. Then run it against a tree where the defect is absent and require green.

A rule kept because it scores zero today is a rule fitted to today. Choose by stated
SEMANTICS and REPORT the cost, whatever it turns out to be; a cost of 129 findings that is
disclosed is worth more than a cost of 0 that was selected for.

## The sibling lesson

**A defect repaired at its site RELOCATES rather than dying.** In the same session one
defect was refuted, repaired, and refuted again at the next function upstream - three times
running - and another moved one function and stayed inside its own module. After repairing,
SWEEP THE WHOLE STRUCTURE for the same shape instead of re-testing the site. The one slice
that swept its entire module against a defect-free tree, rather than fixing the named arm,
is the one that survived.

Related: [[verification-failure-classes]], [[test-quality-failure-classes]],
[[a-guard-can-be-green-by-accident]], [[orchestrated-multi-agent-is-the-default]].
