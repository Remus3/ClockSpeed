---
name: test-quality-failure-classes
description: Ways a test suite can be green and prove nothing, each with the mechanism that makes it happen.
metadata:
  type: reference
---

Failure classes for tests, each recorded with its MECHANISM. A failure class without its
mechanism is folklore - it gets quoted and not applied, because nobody can tell whether the
case in front of them is an instance of it.

- **A mutation that fails to apply looks GREEN.** The harness reports "mutant killed" when
  in fact the substitution never landed, so the untouched code passed its own tests. Assert
  that the anchor text was actually replaced. When a mutant survives, suspect the harness
  before weakening the test.
- **A surviving mutant may be an EQUIVALENT mutant** - a change that provably cannot alter
  observable behavior, so no test can kill it. Weakening the test to catch it makes the
  suite worse for nothing. Swap the mutant instead.
- **Beating a naive alternative is not soundness.** A test derived from what a lazy
  implementation would get wrong only proves you are not lazy. Derive attacks from the
  MECHANISM under test, not from an imagined weaker rival.
- **A negative assertion rules out without pinning down.** "Field X is absent" passes for
  the correct output and equally for a totally collapsed one - an empty object satisfies
  every absence check ever written. Assert what IS there.
- **A raising spy is vacuous under fail-soft code.** If production catches broad exceptions,
  a spy that raises `AssertionError` gets swallowed, and the guard passes whether or not the
  behavior is right. Use a recording spy and assert on the record afterwards.
- **A guard on a non-default call path is untested.** Nothing in the suite reaches it, so it
  is decoration that reads as protection. Delete the guard; if the suite stays green, it was
  never exercised - then either test it or leave it deleted.
- **Fixtures built parallel to the implementation stay green through the real defect.** When
  the fixture encodes the same assumption as the code, both are wrong together and the test
  confirms the assumption rather than the behavior. Build fixtures from real captured data,
  not from the code's own model of the data.
- **The unrun gate is where the bug hides.** A skipped suite is not a passing suite, and a
  skip is invisible in a green summary line. Check what ran, not what reported.
- **The author's own suite tests the guard they MEANT to write.** The arms exercise the
  property the author had in mind; the guard's COMMENT states a stronger property; and
  nothing tests the gap. Measured on CS-823: the hook claimed "a banner anywhere but the
  final line is refused" and no arm exercised it, so a mutant that kept the declared pattern
  BYTE-IDENTICAL and changed only which line it was applied to - `grep -F ... | tail -n 1` -
  passed every arm while letting a forbidden byte commit. It had no dead code and looked
  exactly like a routine "make it less brittle" edit. **A comment is not a test.** Read the
  guard's own prose as a list of claims, and require an arm per claim.
- **"Zero bad rows" is relative to a SET.** The same file is clean under one filter and
  filthy under another, so the number means nothing without its scope. State the set every
  time the count is reported.

- **A recorded demonstration of a gap can OUTLIVE the gap.** An item's note carries a
  one-command proof - "patch this constant and only synthetic fixtures redden" - later work
  closes it, nobody re-runs the command, and the note goes on reading as a live gap. The
  cost is a session rebuilding machinery that already exists. Measured on CS-421: the cited
  flip now reddens FIVE library-backed tests, and the false sentence was sitting in the
  docstring of one of the tests that refutes it. Re-run a cited demonstration before taking
  the item it justifies. The same applies to a share or a percentage quoted beside it - on
  CS-421 the population had not moved at all, the EVIDENCE TABLE had, and a headline of
  "60.1 per cent" was 2.6 per cent by the time anyone re-measured it.

- **N RED TESTS IS NOT N INDEPENDENT DETECTIONS.** A mutant that reddens five tests reads as
  five detections, and the count then gets used to argue a sixth arm would be redundant. Trace
  the reds to their PREDICATE first. Measured on CS-421: five library-backed reds were ONE
  single-owner predicate consumed at five sites, and FOUR of the five disclaimed their own
  result in their failure text - each reported that its baseline was red, so its comparison
  meant nothing. One detection, four guard trips. **Read the failure TEXT of every red, not
  just the summary line**, and treat shared-predicate reds as one piece of evidence.

Related: [[verification-failure-classes]], [[orchestrated-multi-agent-is-the-default]],
[[unknown-content-is-flagged-not-fatal]].
