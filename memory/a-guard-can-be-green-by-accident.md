---
name: a-guard-can-be-green-by-accident
description: A guard can pass because a DIFFERENT mechanism silently covers the case under test, so deleting the mechanism the arm names changes nothing and the arm never notices.
metadata:
  type: reference
---

A guard is green. Every arm passes. Delete the mechanism the arm exists to grade, and it
is STILL green - because something else in the tree happens to cover the same case.

The arm was never measuring what its name says. It was measuring a coincidence.

## The measured instance

Session 46 widened the pytest report redactor to cover a home path in its escaped
spellings, because a chained `OSError` renders `filename` through `%r` and doubles every
separator. Three escaped spellings were added: the doubled one, and two URL-quoted ones.

The doubled spelling got its own arm. The two quoted ones did not - they were covered only
by a region-level check that asserted the home placeholder appeared SOMEWHERE in the
rendered failure.

Deleting `quote` from `_HOME_SPELLING_TRANSFORMS` in `tests/conftest.py` left the whole
suite green. The quoted spellings were still redacted, by the ACCOUNT-NAME rule, because
on this machine the account name is the only personal component of the home prefix.

**That is the exact defect the item was filed to remove, reproduced one level up inside
the guard written to prevent it.** The item existed because containment rested on a naming
accident rather than on a control. The guard proving the fix rested on the same accident.

Found by two reviewers independently, using different mutations - one deleted a single
transform, the other reverted the whole tuple. Neither the author nor the merger found it.

## Why the pooled check could not catch it

The region-level assertion asks: does the placeholder appear in the rendered region? The
NATIVE spelling already puts it there. So the assertion is satisfied before the escaped
spellings are considered at all, and no escaped spelling can ever fail it.

A threshold summed over a population is met by its strongest member, and the weakest goes
unmeasured while the acceptance clause still passes. Here the population is a set of
SPELLINGS, and the member nobody doubted is what satisfied the check for all of them.

## The test

**Delete the mechanism the arm names. If nothing goes red, the arm does not grade it.**

Not "does the suite pass" - it does. Not "is the behaviour correct" - it was. The question
is whether the ARM is attached to the MECHANISM, or whether both merely happen to be true
at the same time on this machine today.

Two forms of the same fault, both measured in that session:

- **A pooled assertion satisfied by a sibling case.** Fixed by one arm per member, each
  naming its own member, in `tests/test_report_redaction_classes.py::test_each_home_path_spelling_reaches_the_home_rules_alone`.
- **A registration checked structurally rather than behaviourally.** A class registered
  with a pattern that matched nothing, and an arm whose body was `pass`, satisfied every
  completeness check - because those checked that an id occupied a tuple slot and that a
  function NAME existed. Swapping two rules' class tags also changed nothing; the tags were
  decorative. Fixed by requiring each class to have a rule that demonstrably rewrites a
  planted string of its own class, in
  `tests/test_report_redaction_classes.py::test_every_covered_class_has_tagged_rules_that_rewrite_its_own_planted_string`.

## How to write the arm so it cannot be green by accident

- **Assert the SPECIFIC placeholder, not the absence of a leak.** A leak scan is satisfied
  by any rule that fires. Only a per-mechanism fingerprint distinguishes which one did.
- **One arm per member of the population**, each naming its member, so a pooled pass cannot
  hide a member that never ran. See [[an-empty-population-satisfies-every-zero]].
- **Grade behaviour, never a tag or a name.** A structural check answers "is it declared",
  which is a different question from "does it work". See [[a-guard-can-measure-spelling]].
- **Prove the arm by deletion, not by authorship.** Remove the mechanism, watch the named
  arm go red, restore by hash. A repair is not evidence of itself.

## Why this is worth a durable note

This was the FIFTH consecutive session to produce a false clearance inside the guard
written to prevent the previous one. It was the first caught before anything was reported
closed, and it was caught only because reviewers who did not author the work were told to
refute it and defaulted to REFUTED when uncertain.

The author's own testing does not find this class. It cannot: the author writes the arm
and the mechanism together, so they are true together, and the coincidence that couples
them is invisible from inside. See [[orchestrated-multi-agent-is-the-default]].
