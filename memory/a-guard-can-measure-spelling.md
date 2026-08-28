---
name: a-guard-can-measure-spelling
description: A guard that matches on a NAME reports a population zero about the wrong question; and a false clearance is a worse defect than a silence.
metadata:
  type: reference
---

Two failure classes for GUARDS specifically - a guard being a test whose subject is the
shipped tree rather than one function. Both were measured twice in a single session, by
different authors, against different channels, and neither author found their own.

## A syntactic match standing in for a semantic property

A guard needs to know whether a value is safe. Deciding that properly needs a semantic
question answered, so the implementation quietly substitutes a SPELLING - the name a
binding has, or the name a callee has - and then reports the count of what it matched as
though the count were about the property.

**The zero is real. It is about the wrong question.**

Two instances, both measured:

- CS-855's detector asked whether a handler's bound name appeared in an assert. One
  statement - `kept = exc` - moved the value to a name it was not watching. Four planted
  leaks rendered while every arm passed. The module pinned as a non-finding a shape the
  same file separately declared as rendering.
- CS-852's vocabulary proof resolved a callee BY BARE NAME, so a function merely NAMED
  `_checked_field`, whose body only decoded its argument, earned the strongest clearance
  the guard could issue.

**THE TELL: the population is derived from a SPELLING while the acceptance is written
about a BEHAVIOUR.** Read the two side by side; they will not be about the same thing.

**THE TEST: ask what an adversary would have to RENAME to escape.** If the answer is a
local variable or a helper function, the guard is measuring spelling.

**A POSITIVE CONTROL DOES NOT CATCH THIS.** Both modules shipped working ones. A positive
control proves the detector fires on the shape it already models, which is exactly the
shape an evasion avoids. What catches it is planting the evasion, not the instance.

## A false clearance is worse than a silence

These are different defects and the distinction decides how urgently to fix one.

A guard that finds no channel reports NOTHING, and a later reader may still go and look.
A guard that reports `proven-*`, `verified`, `clean` or any positive verdict has issued a
CLEARANCE, and the next session cites it as evidence the thing is safe. The second is how
a wrong belief becomes load-bearing.

Measured on CS-852: nine paths returned a POSITIVE PROOF over a value that reached the
exception's `args`. One graded a joined list of arbitrary content as "an annotation whose
whole value space is numbers and flags" - and that shape is live house style at four
shipped sites, so the guard was one refactor away from waving through the exact leak it
existed to catch.

**THE RULE THAT FOLLOWS: when a rule cannot model a shape soundly, return unproven.**
Given a choice between a narrower rule that reports more and a broader one that proves
more, take the narrower one. An over-reporting guard costs a reader some time; an
over-proving guard costs them the belief that they need to look at all.

Related: [[test-quality-failure-classes]], [[verification-failure-classes]],
[[an-empty-population-satisfies-every-zero]], [[a-probe-can-validate-the-wrong-channel]],
[[orchestrated-multi-agent-is-the-default]].
