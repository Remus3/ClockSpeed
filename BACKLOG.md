# Backlog - aspirational and conditional-trigger items

**Section status: LIVE.** A dated heading in this file records provenance - when a
direction was filed or measured - and never that the section itself is historical.
Nothing here has happened yet; that is what the file is for.

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

- Nothing reddens if the `/moon_sync_inbox/` line is removed from `.gitignore`: the
  cross-project channel would go back to untracked and visible, and only the
  pre-commit gate's PII arm would stand between a sibling's note and a commit - which
  is the arm that already fired once, so the missing guard costs visibility rather
  than protection - conditional on a second unguarded ignore entry appearing, at which
  point the arm is worth writing once for the class instead of for the line.

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

- **RESOLVED 2026-08-29 - the band moved to 8920-8939, and the diagnosis in this row was
  wrong.** It read: port 8901 "has been held since 2026-08-16 by an unrelated process", with
  `scripts/verify_env.py` soft-failing every run. The holder was not unrelated and 8901 was
  never this project's to hold: the whole 8900-8919 range is LegionWallpaper's reserved
  block, negotiated and confirmed in writing on 2026-08-01, and 8901 is its monitor while
  8900 is its rundash. This project allocated 8900-8911 by PROBING for a free listener,
  recorded as "8900-8911 all free and unbound on this machine" - and LW's monitor is an
  operator-launched GUI that is unbound most of the time, so the probe reported a reserved
  block as free. Nothing here had bound a port yet, so the move cost nothing. **The durable
  rule: verify a band against the owning project's registry in SOURCE, never against a live
  scan.** Machine-wide blocks AS RECORDED ON 2026-08-29: RM 8770-8789, LL 8810-8819,
  DS 8860-8879, RC 8888-8895 plus 2999, LW 8900-8919, CS 8920-8939. That list has since
  grown and this copy is NOT maintained - `config/ports.json` owns the record and is the
  only place to read it current. Dated here rather than updated, because a second list
  kept in step by hand is the drift the topology rule exists to prevent.

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

## Dashboard as a telemetry HUD - an operator design direction, filed 2026-09-05

**Trigger: the producing endpoint exists.** The two components the direction names cannot be
built before then, and scaffolding against an assumed API surface is ruled out in
`CLAUDE.md` section 5.

- A milestone objective tracker - text progress bar, estimated time to completion, tier-3
  shortfall derivation - conditional on `/api/plan` existing AND on unlock state being
  readable, which `/api/world` currently reports empty because the grammar is unmeasured.
- A live throughput comparison node - stark demand-versus-supply delta, health-shifting
  borders, click to expand the upstream stall trace - conditional on `/api/advice` existing,
  or on some route publishing a recipe set the page can name.
- A shared card style layer - custom properties, monospace alignment, thin geometric
  borders, semantic status colours for optimal, throttled and starved - NOT conditional on
  either, because it does not depend on any payload shape and the overlay problem below is
  worth solving before there is content to lose to it.
- Overlay text isolation, measured 2026-09-05 and the reason the style layer is worth doing
  early: the operator's proposed industrial-orange accent scores 5.88 to 8.51 against every
  candidate dark slate and passes body-text contrast on all of them, but scores 2.22 over a
  white game pixel, which fails even the large-text threshold. A shadow raises perceived
  legibility without changing the measured ratio, so overlay text needs a real backing
  surface rather than a shadow alone.

**The style layer landed, measured 2026-09-05.** `clockspeed/surface/web/app.css` now
declares `--accent-hud`, the three `--status-*` colours with their fills, `--hud-rule` and
`--overlay-ground`, in both schemes, plus `.hud`, `.hud-card`, `.hud-status`, `.hud-figure`,
`.hud-accent` and `.hud-overlay`. NO COMPONENT CONSUMES THEM YET and that is deliberate -
the two named components still wait on their producers. Three things were measured while
building it that whoever writes those components will otherwise re-discover the hard way:

- **The accent fails on the LIGHT SCHEME, not only over a game pixel.** The direction above
  frames #FA9549's 2.22 as an overlay problem. Measured against this page's own light
  grounds it scores 2.22 on `--surface`, 2.07 on `--bg` and 1.96 on `--surface-alt` - it
  fails even the 3:1 large-text threshold on all three, on the page as it ships today. A
  light theme is a white game pixel that is always on screen. The light half holds hue at
  25.8deg and saturation at 0.947 and moves lightness only, to #9f4704.
- **A status colour must be measured on its own tinted fill as well as on the page.** The
  first candidate cleared all three page grounds at 4.56 and then scored 4.18 on the fill it
  was drawn for. The floor across all four is what selects a value, not the page grounds.
- **Overlay contrast is NOT MONOTONIC in scrim opacity.** Accent over `--overlay-ground` over
  a white pixel falls from 2.22 at no scrim to 1.02 near alpha 0.35, where the composited
  ground crosses the accent's own luminance, then climbs back to 8.38 at full opacity. A
  light scrim chosen to keep the game visible lands at the WORST legibility available,
  strictly worse than no scrim. Body text clears 4.5:1 at alpha 0.65, the accent at 0.80.

**The surface law now has an owner file, filed 2026-09-05.** `docs/hud_doctrine.md`
holds what the companion and the overlay are each FOR, which channel may carry what, and
the three shipped arms an overlay will collide with. It was adapted from a doctrine the
operator supplied from another project and records what does NOT transfer as carefully as
what does.

**Three-tier disclosure cannot use `details` or `summary`, measured 2026-09-05.**
`tests/surface/test_web_assets.py::test_the_page_offers_exactly_one_kind_of_clickable_target`
bans `a`, `input`, `select`, `textarea`, `details` and `summary` outright: the only clickable
target the page admits is a `button`, which is what makes the 24px hit-target arm a claim
about the whole page rather than about one selector. So the direction's "click to expand the
upstream stall trace" is a button toggling `hidden`, never a disclosure element.

## Lane - the suite grader does not check how much of the tree was collected

Filed 2026-09-06 out of CS-918's proving work. **Trigger: a run that collects a SUBSET of
the tree and still exits 0.**

- `ops/loop/queue_loop.py::summarize_pytest` grades a run on its summary line AND its exit
  code, which is what catches a truncated run (no summary) and a crashed one (exit 3, and
  `INTERNALERROR> MemoryError` was measured this session). Neither half looks at HOW MANY
  tests ran, so `3402 passed in 826.38s` with exit 0 would grade green even though the tree
  collects far more - the same "nothing failed, so it must be fine" shape one level over.
  The fix must DERIVE the expected count rather than record one: a `--collect-only -q` pass
  before the run, compared against the total the run reports. A number written into a file
  would be a restated measurement and would drift on the next test added.

- THREE LIVE DOC LINE POINTERS ARE STALE AND NO GUARD COVERS THEM, measured 2026-09-09
  during the CS-960 re-check and stale at that item's BASE commit, so nothing this project
  did broke them. `docs/item_notes/phase4.md` cites two declarations in
  `clockspeed/save/objects.py` and `docs/LEDGER.md` cites a third; all three now land
  elsewhere, one of them on a bare comment marker. None is in `UNVERIFIED_LINE_POINTERS`
  or in a disposition, so the citation guard checks only that the line is in RANGE and is
  silent on where it points. Repairing them is NOT the repointing CS-960 did: those five
  moved to byte-identical content and the unchanged digest proved it, whereas these need
  somebody to read each sentence and adjudicate which declaration it MEANT. Deriving the
  target from today's tree instead would bake in whatever the pointer happens to hit and
  ship green on the very defect it was filed for - the objection already recorded against
  a content-anchored resolver.

- THE PUBLISHED PROPERTY MODEL RETAINS ABOUT 7.4x THE BODY IT WAS DECODED FROM, measured
  2026-09-10 under CS-961 S4 and recorded in `docs/LEDGER.md` as that date's MEASUREMENT
  RECORD. One world load holds about 133 MB against an 18 MB decompressed body, agreeing
  to 16 bytes across three `tracemalloc` drops. The dominant site is `ContainerEntry` at
  about 1.08M live instances and about 103 MB - 78 percent of the retained total. The
  decode itself is about 90 percent of a 2.0 s load, roughly nine to ten times the walk.
  **THE AXIS IS THE CONTAINER FAN-OUT AND NOT THE EAGER CHOICE**, which is the whole
  reason this is filed rather than acted on: eager versus lazy was settled by CS-961's
  acceptance, because lazy means retaining the payload buffer, and a session reading only
  the headline number would reopen exactly the wrong decision. A shared or interned
  representation for container entries is the shape to look at first.
  CONDITIONAL TRIGGER: nothing holds a `WorldModel` today, so nothing pays this cost yet.
  Revisit when a consumer above the save layer holds one for the life of a session - the
  companion, the dashboard, or an audit pass over a real world - or when a real load is
  measured against a machine with less headroom than the development box. Until then this
  is a measured fact and not a defect, and it must not be optimised on speculation.

## External agent tooling - ideas kept from the CS-1099 and CS-1100 declines, filed 2026-09-16

The declines themselves are recorded in `docs/LEDGER.md`. Nothing here is started early.

- Revisit `context-mode`, declined with nothing installed - TRIGGER: upstream ships a
  project-scoped, network-free mode, with no writes to user-level Claude configuration, no npm
  registry call on start and no platform-bridge egress; the section 14 gate and the install checks
  are then re-run at a new pinned SHA, never inherited from the decline record.
- An own-words voice-rules skill - the idea observed in the declined pack's plainspoken and
  writing-for-humans skills, ZERO bytes copied, bounded by `CLAUDE.md` section 2.3 and
  non-negotiable 4 - TRIGGER: a `CLAUDE.md` section 4 owner row for it lands first.
- A Windows media-ingest skill - the idea observed in the declined pack's ingest skill, which is
  macOS-only, ZERO bytes copied - TRIGGER: a work item needs audio or video turned into a text
  note on this machine, and a `CLAUDE.md` section 4 owner row for it lands first.
