---
name: an-empty-population-satisfies-every-zero
description: An assertion that a count is zero is satisfied by a broken measurement, because the success condition and the total-failure condition are the same output.
metadata:
  type: reference
---

# An empty population satisfies every assertion of zero

**Filed 2026-08-25 (session 40), from three refutations and two tooling traps that all
turned out to be one shape.**

`assert count == 0` is the standard way this project asserts that a bad thing does not
happen. It has a defect that is invisible from the outside: **the assertion passes when the
property holds, AND it passes when nothing was measured at all.** Those two states produce
byte-identical output. A reader of a green run cannot tell them apart, and neither can the
suite.

This is the mirror of [[a-proof-can-require-the-defect]]. That one is green because the
defect is present. This one is green because the DETECTOR IS SILENT - and a detector is
silent both when there is nothing to find and when it is broken, misaimed or unreachable.

## The five measured instances, in one session

- **A reader that graded nothing.** A test module's independent second reading of the save
  grammar omitted a 16-byte step that the shipped reader performs. It desynchronised at the
  FIRST struct tag in every record and refused everything after it: 87302 records accepted,
  **ZERO** struct sites found, against a shipped walk finding 45208. The arm asserting
  `refused_but_independent == 0` passed for roughly forty sessions, because its population
  was empty. It was sold in prose as independent corroboration of a refusal, and it covered
  zero per cent of the population the item is about.
- **A rule that matched nothing.** A liveness guard asserted `vacuous_grading == []`. Three
  of its four rules scored zero on the tree - not because the tree is clean, but because one
  rule tested two literal spellings of a semantic class, one had zero live effect (0 members
  added over 1986), and one fired only on idioms this tree happens not to contain.
- **A fixture that pinned silence.** A privacy guard recorded seven binding forms as safe,
  "graded BEHAVIOURALLY" at zero findings. Four of the seven LEAK under a real forced run.
  The zero being asserted was the scanner's silence, which is true BY CONSTRUCTION for a
  form the scanner has no code for.
- **An identity that cannot fail.** An accounting closure summed per-class counts over a
  contiguous, non-overlapping tiling and asserted the total. `sum(hits over a partition) ==
  hits over the whole` is arithmetic, not evidence. It survived nine independent
  degradations, including one that drove every count to zero.
- **Two tools that answer an unasked question.** `gh run list --commit <SHORT-sha>` returns
  `[]` and exits 0 while CI is green - it needs the full SHA. `precommit_gate --staged`
  reports PASS with **0 CHECKED** when nothing is staged. Both read as a negative finding.

## The sixth instance, added the same day: the population can be empty because of WHO IS
## RUNNING THE CHECK

A source-echo rule ran the project's runtime redactor over every source line and flagged any
line the redactor rewrote. Its note claimed it "cannot false-positive, because it fires on an
ACTUAL VALUE rather than on a shape". The whole local suite passed - 2892 tests - and CI
FAILED on the same commit with 33 findings.

The redactor's rules are built from the machine's own account name. On the authoring machine
that name appears in no source, so the rule found nothing and its zero looked like proof. On
the CI runner the account is `runner` - an ordinary English substring sitting inside
identifiers like `..._is_reached_by_its_runner` and `run_all` across the tree.

**AN ACTUAL VALUE IS STILL A SHAPE WHEN THE VALUE IS A COMMON WORD.** And more generally: a
check whose RULES are derived from the environment returns a verdict about that environment,
not about the tree. A green run on one machine is evidence about one machine.

The repair is the discrimination the neighbouring rule already stated - apply the redactor to
the PATH-SHAPED TOKENS of a line rather than to the line, because a backstop belongs to
runtime output where the surrounding path has been lost, while authored source still carries
its context. Measured with a CI-shaped redactor: 70 hits over 33 files before, 0 after, still
firing on a planted absolute home path.

## The rule

**Never assert a zero without asserting the population that produced it.** Every
counts-only arm needs a companion that fails when the measurement collapses:

- assert the DENOMINATOR is non-empty, or SKIP with a reason naming what was missing - `no
  evidence is a SKIP, not a RED` is a standing decision here, and an arm that FAILS on a
  small corpus is the same defect inverted;
- assert the detector FIRED at least once on something it should catch, using a synthetic
  positive derived from the shapes the checker claims - never from live findings;
- for a second, corroborating reading, assert it AGREES with the first on the population
  both accept, not merely that it found no disagreements.

## The tell

Ask of any green assertion: **what else would produce this exact output?** If "the
measurement never ran", "the walk refused every record", "the rule matched nothing" or "the
query named a thing that does not exist" are on that list, the assertion is not yet
evidence. A count of zero is a claim about a population, and a claim about a population is
worthless until the population is itself asserted.

Related: [[test-quality-failure-classes]], [[verification-failure-classes]],
[[a-probe-can-validate-the-wrong-channel]], [[a-proof-can-require-the-defect]].
