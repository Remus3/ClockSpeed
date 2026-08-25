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

## Save reader - CS-831 residuals too small to file

All measured 2026-08-23 by the CS-831 review rounds, none blocking its close. **Trigger for
the first: a consumer actually needs to follow a component to its parent.**

- A component's `parent` is a cross-reference that resolves for every component in the
  library and nothing follows it - the join already exists, only a consumer is missing;
  the strongest sibling CS-831 found - conditional on a consumer needing it.
- `ReferenceResolution.targets` is keyed by PROPERTY NAME, so two reference tags sharing a
  name would collapse and one target would silently become unreachable - measured zero
  occurrences across the whole library, so a latent shape hazard rather than a live defect,
  and `PropertyResult.references` argues against exactly this collapse - conditional on a
  record appearing that bears two references under one name.
- `_ReferenceSweep` is the one new frozen dataclass without `repr=False`, safe today only
  because every field is an int or a tuple of exception type names - conditional on any
  string-bearing field being added to it.
- The CS-831 module's ledger-recording test cannot fail unless another test in the same
  module also fails, so it grades nothing of its own - conditional on someone touching that
  module.
- CS-831's ambiguity margin - how many resolutions land on a name borne by more than one
  record - is asserted but never recorded anywhere a reader sees it without running pytest.
- `read_properties` returns early on a zero-length payload, a third abandon condition the
  CS-831 second join does not mirror; measured zero such payloads, and both passes
  contribute zero from it either way.
- `clockspeed/save/objects.py` is now the largest module in the package by a wide margin
  and is a splitting candidate - conditional on a change that would grow it again.

## CI and toolchain

- `actions/checkout@v4` and `actions/setup-python@v5` target Node 20, which GitHub has
  deprecated; the runner currently FORCES them onto Node 24 and prints a warning on every
  run, so nothing is broken and the warning is the only signal - eight pin sites across
  `.github/workflows/tier1.yml` and `.github/workflows/tier2.yml`, and neither file is on
  the frozen list, so no adjudicator grant is needed - conditional on the forcing being
  withdrawn, or on the warning becoming a failure.

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

**BOTH ITEMS HERE WERE RULED ON BY THE OPERATOR 2026-08-23 AND ARE ANSWERED. Nothing below
is a live trigger; this is the record of a decision already made, kept so the two defects
are not re-filed.** The ruling created `docs/item_notes.md`, which now OWNS live per-item
detail, and `docs/upstream_watch.md`, which owns the CS-486 upstream watch list. Both are
named in the `CLAUDE.md` section 4 and `CONVENTIONS.md` section 2 topology tables and both
carry a doc budget.

**Relocated 2026-08-25, and the record below is left as it was written.** `docs/item_notes.md`
outgrew its budget and was SPLIT: it is now an INDEX over `docs/item_notes/`, one leaf per
phase, and the bodies moved into the leaves byte-for-byte. Where the record below says a body
lives in `docs/item_notes.md`, it lives in the leaf that file's routing table names. The
ruling itself is undisturbed - what it created still owns what it was given.

- **RULED: `ROADMAP.md` structurally at its ceiling.** The answer is not a bigger number -
  CS-495 settled that and the ruling did not disturb it - and not a manual relocate pass per
  session either. The NOTE BODIES MOVE OUT. `ROADMAP.md` keeps the item LINE alone, plus a
  short pointer where a NOTE was, and every NOTE body lives in `docs/item_notes.md` keyed by
  item ID. The topology tables were amended so a NOTE body is now something `ROADMAP.md`
  never contains, which is what makes this durable rather than another pass.
- **RULED: `docs/history_notes.md` was doing two contradictory jobs.** Its header says the
  file holds nothing current and that was the TRUE half; the live instruction blocks were the
  false half, so they moved rather than the header. Every block whose item is OPEN moved to
  `docs/item_notes.md`. A block whose item is CLOSED stayed, because a closed item's detail
  IS history - that is the rule that keeps the header true from here on, and it is recorded
  in both topology tables.

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
