---
name: a-skip-can-mute-the-defect
description: A skip whose condition is read from the code under test goes quiet in exactly the case that code is broken.
metadata:
  type: reference
---

A skip is a precondition, and a precondition READ FROM THE SUBJECT is a mute button the
defect gets to press. It goes quiet in exactly the case the subject is broken, which is
the one case the arm existed for.

**Measured on CS-605.** The arm proving a home path never reaches the wire unescaped had
its precondition turned into `if home in body: pytest.skip(...)`, and `home in body` is
precisely the condition a NON-ESCAPING encoder produces. With `contract.encode` mutated
to stop doubling the separator it writes - validation intact, output bytes only - the
whole of `tests/surface/` reported **527 passed, 1 skipped, exit 0, with the leak live**.
The assert that skip replaced had killed the same mutant. The one visible trace, the skip
reason, blamed the PLATFORM, so the guard did not merely fall silent - it misdirected.

**Why review did not catch it.** The skip read as the established platform-divergence
idiom, which is legitimate and is used elsewhere in this repo. The difference is invisible
in the SHAPE and lives entirely in what the condition READS.

**The two rules that follow.**

- Condition a skip on a STATIC PROPERTY OF THE INPUT, true or false before the code under
  test is ever called. On CS-605: whether the home string carries a separator at all. No
  defect in the encoder can flip that.
- Where an arm's subject is BORROWED FROM THE MACHINE - its home path, its filesystem, its
  account - the arm can only fire where that machine happens to supply one, so everywhere
  else the property is graded by nothing. PLANT A SYNTHETIC SUBJECT and the same arm grades
  every platform. On CS-605 no other test in the tree fed a separator-bearing string
  through that encoder, so its escaping was ungraded on every POSIX runner.

Related: [[a-guard-can-be-green-by-accident]], [[test-quality-failure-classes]],
[[an-empty-population-satisfies-every-zero]], [[a-proof-can-require-the-defect]].
