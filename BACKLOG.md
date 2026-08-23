# Backlog - aspirational and conditional-trigger items

One line each. No acceptance criteria, no schedule, no narrative. Nothing here is being
worked on right now - work in progress lives in `ROADMAP.md`.

An item moves out of this file in one of two directions: to `ROADMAP.md` with an ID and an
acceptance criterion once its trigger has fired and it is genuinely next, or to
`docs/GATED.md` once it is actually attempted and found blocked on a specific external
condition.

**A conditional item is not started early because it looks cheap.** The trigger is the
whole point of writing it down here instead of doing it.

---

## Mod content support

Architecture is first-class from phase 0 - namespaced identifiers, unknown classes
tolerated, unmodeled content flagged, feature-flag registry present. The content work
below is deliberately deferred. **Trigger for all three: phase 6 completes.**

- Mod-specific recipe modelling, so modded chains solve rather than merely flag as
  unmodeled - conditional on phase 6 completing.
- Mod-aware advice rules, so advice can reason about modded buildings and logistics -
  conditional on phase 6 completing.
- Per-mod compatibility work, switched individually through the feature-flag registry -
  conditional on phase 6 completing.

## Surfaces

- In-game overlay: transparent, click-through, always-on-top, bound to the game window, as
  a flagged mode of the companion shell - default off, degrading to the companion window
  if window binding fails for any reason, and never blocking input it did not intend to
  receive.

- Port 8901, this project's allocated dashboard port, has been held since 2026-08-16 by an
  unrelated process, and `scripts/verify_env.py` reports it as a SOFT failure on every run -
  decide whether to move the band or accept it and re-record `config/ports.json`; conditional
  on CS-601 actually trying to bind, and an operator call either way.

## Doc topology

- `ROADMAP.md` needed TWO relocate passes in one day - 9 bytes of margin, then 97 after two
  filings - so it is structurally at its 61440 ceiling rather than occasionally near it, and
  the budget is severity WARN so CI never says so; find a durable answer other than a manual
  pass per session, noting CS-495 settled that raising the number is not it - conditional on
  ROADMAP.md hit its budget a third time, or on an operator call.
- `docs/history_notes.md` opens with "This file holds NOTHING current" and is now the home of
  the LIVE instructions for CS-442, CS-456, CS-460, CS-465, CS-468, CS-472, CS-479, CS-500,
  CS-825, CS-826,
  CS-484, CS-492, CS-702, CS-806 and CS-807, which `ROADMAP.md` points at with "MUST BE READ
  BEFORE TAKING THIS ITEM" - the file is doing two contradictory jobs and its header is the
  half that is false; conditional on an operator ruling, the same shape as the WAKEUP_NOTES
  ordering ruling of session 26.

## Ingestion lanes

- OCR and CV ingestion lane for live and transient state the save file cannot provide -
  built as a real lane if built at all: capture stage, region registry, cheap
  deterministic recognizer first with escalation only on a miss, and a confidence score on
  every extracted field.
- Dedicated server API lane as an alternative world-state source - conditional on the
  operator actually running a dedicated server; the API docs ship with the game and are
  free to read in the meantime.

## Engine

- External linear or integer programming optimizer behind the existing `OptimizerBackend`
  interface - conditional on passing the `CONVENTIONS.md` section 14 license gate, and on
  slotting in without changing a single caller.
