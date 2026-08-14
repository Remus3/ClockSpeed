---
name: world-token-is-the-ledger-key
description: The save header's 22-character base64url world token keys the advice ledger, never a filename and never a world name.
metadata:
  type: project
---

The save header carries a 22-character base64url token (16 bytes) that identifies the
world. Measured 2026-08-13 across four saves spanning three worlds: two saves of the same
world carry the SAME token, and saves of different worlds carry DIFFERENT tokens. No token
value is recorded here, deliberately.

**The advice ledger is keyed to that token.** Not to a save filename - filenames change on
every save and autosaves rotate through a numbered set. Not to a world name - the world
name is operator-chosen, mutable and treated as data rather than identity. The card
identity and all persisted per-world state (accepted, dismissed, snoozed, pinned,
completed) hang off the token, so state survives a reload, a rename and a new save.

**The honest limit on the claim, which must travel with it:**

- The sample is four saves across three worlds. That is strong evidence the token is
  world-scoped; it is not proof.
- It has NOT been proven to survive a game version upgrade of the same world. The library
  that was measured spans two save versions across different worlds, not one world before
  and after an upgrade.
- Whether the token is a world seed or a session GUID is unknown, and does not matter for
  the ledger's purposes.
- Phase 4 must assert token stability across a save/reload cycle as a test. That test is
  the mechanism that converts the evidence into a checked invariant.
- The ledger must tolerate a key it has never seen by treating it as a NEW WORLD rather
  than failing. An unrecognised token is the expected outcome of a fresh world, and it may
  also be the symptom of the upgrade case above.

**Why:** Persisted advice state is worthless if its key is unstable - every reload would
orphan the ledger and the operator would re-triage advice they already dismissed, which is
a direct tax on the scarcest resource. Filename keying looks like it works right up until
the first autosave rotation. Recording the limit alongside the finding is what stops a
later session from treating "measured" as "proven" and building an upgrade-fragile
assumption on top of it.

**How to apply:** Read the token from the header, key the ledger on it, and never let a
filename or a world name reach the key path. When the ledger meets an unknown token, create
a fresh world entry and continue. If a same-world upgrade is ever observed to change the
token, that is a spec-beating measurement - record it and re-key rather than patching
around it.

Related: [[save-files-carry-pii]], [[never-write-to-the-game]],
[[verification-failure-classes]].
