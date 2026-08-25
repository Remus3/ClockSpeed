---
name: moving-an-assert-can-create-the-leak
description: A static finding names a scope, not a disclosure; relocating the assertion changes which frame unwinds, and the new frame has its own locals.
metadata:
  type: reference
---

# Moving an assert to clear a finding can create the leak it was clearing

**Filed 2026-08-25 (session 42), from a CS-852 adversary measuring a repair the merger had already merged.**

**A static finding names a SCOPE, not a disclosure.** The remedy that moves the assertion
somewhere else changes which frame unwinds, and the new frame has its own locals. Clearing
the finding and reducing the disclosure are different outcomes that look identical in a
green suite.

## The instance

CS-851 flagged `tests/save/test_properties.py` for holding the raw decompressed save body
in a local at an assert. The merger hoisted the assert - which was loop-invariant - out of
the per-save loop.

Both halves of that were wrong, and an adversary measured both:

- **The original could never disclose anything.** It sat inside a `try` whose handler is
  `except (Exception, SystemExit)`, and `AssertionError` is an `Exception`. The failure was
  swallowed one line later and recorded as the bare word `AssertionError` in a failures
  list, which `@lru_cache` then cached. **The CS-851 finding was a STATIC FALSE POSITIVE**,
  because the sweep does not model the enclosing handler.
- **The hoisted copy did disclose.** Outside every `try` it propagated, unwinding through
  a frame where `saves` held the real library save paths - the Windows account name, the
  numeric platform account id and the world name. Forced under `-l`: one marker occurrence
  hoisted, zero inside the try.

And the new leak was invisible to the guard that prompted the move: CS-851 keys on a local
holding a WITHHELD FIELD OF A REDACTING CLASS, and `saves` is a bare `tuple[Path, ...]`.
So the trade was a guard-visible non-leak for a guard-invisible real one.

## How to apply

- **Before moving an assert, read what the destination frame HOLDS**, and read every
  enclosing handler at the source. A finding inside a broad `except` may already be inert.
- **The fix is usually neither placement.** Here the check belonged in its own test
  function, where the frame holds only what the check needs. That version also runs
  unconditionally, propagates, and keeps its message - it grades MORE than either original.
- **A guard's finding is a claim about a shape, not proof of a disclosure.** Confirm the
  disclosure by forcing the failure and grepping the rendered output before designing the
  remedy - the same standard [[a-proof-can-require-the-defect]] demands of the proof.
- Relates to [[an-empty-population-satisfies-every-zero]]: both are cases where the
  observable - a green arm, a cleared finding - is produced equally by the good state and
  by a state nobody measured.
