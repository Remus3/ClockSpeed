---
name: test-quality-failure-classes
description: Nine ways a test suite can be green and prove nothing, each with the mechanism that makes it happen.
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
- **"Zero bad rows" is relative to a SET.** The same file is clean under one filter and
  filthy under another, so the number means nothing without its scope. State the set every
  time the count is reported.

Related: [[verification-failure-classes]], [[orchestrated-multi-agent-is-the-default]],
[[unknown-content-is-flagged-not-fatal]].
