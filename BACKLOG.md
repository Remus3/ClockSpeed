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
- GitHub's notice, read in session 137 and filed 2026-10-11: `ubuntu-latest` moves to Ubuntu 26
  from 2026-10-19, and every tier1 job and the ubuntu leg of each tier2 matrix run on
  `ubuntu-latest`, so the image changes under an unchanged workflow - TRIGGER: the first tier1
  or tier2 run on Ubuntu 26 fails, or 2026-10-19 passes: re-read tier1 and tier2.

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
lives in `docs/item_notes.md`, it lives in the leaf that file's leaf membership rule names. The
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

## Lane - driver log retention, filed 2026-09-25

- CS-1192 - the per-night driver logs `ops/loop/queue_loop.py::night_log` writes since
  CS-1018 are retained without bound, roughly 4 KB a night; add pruning by age or by count
  - conditional on the log directory growing past 1 MB.

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
- Re-measure tier-1 and tier-2 on the Ubuntu 26 runner image - GitHub's notice on run
  36269312405 says `ubuntu-latest` migrates from 2026-10-19; every ubuntu-only arm and the
  420/480 shard budgets were measured on the old image - TRIGGER: the first tier-1 run whose
  runner reports the new image, or a red on an ubuntu job after 2026-10-19.

## Session 122 residuals - filed 2026-10-03 under product before process

None blocks a product item or reddens a suite.

- `tools/main_provenance.py::read_note` opens a note that was never placed with a plain
  blocking open, so a FIFO outside the inbox would hang it on POSIX - predates CS-1232,
  whose pin now refuses a non-regular file inside the inbox - TRIGGER: any POSIX consumer
  that runs the tool over an untrusted path.
- The CS-815 probe's nonce draw fails closed, but a failed `od` draw is reported as "no
  usable python interpreter found" - diagnosis only, never fail-open - TRIGGER: a hook
  refusal on a host where python is present.
- CS-400 S2 join: the identity keying of record positions is unpinned by a test (a
  value-equality mutant survives, equivalent while payload offsets are distinct);
  `ReferenceTarget` has no state-against-indices check; the top-level placement of a
  building's inventory references rests on the CS-830 measurement of 2026-08-23 - TRIGGER:
  two records equal field for field, or a building whose inventory reference is nested.
- Decode the InventoryItem state block, counted undecoded by CS-400 - TRIGGER: an advice
  rule that needs item state.
- CS-400 S2b attribution: a carrier whose parent is a component lands in unattributed
  with no counter of its own; where the reference rule names an actor while the parent
  is ambiguous, the carrier is attributed although it may be a conflict; a future
  buildable without a `Build_` prefix silently counts as non-building - TRIGGER: a save
  showing any of the three.

## Inspiration ingest - process and evaluation items, filed 2026-10-04 under product before process

Ideas only, from an untracked external survey; nothing lifted. The product directives went to
`ROADMAP.md` as CS-1235 through CS-1262.

- A local-only advice regression over the gitignored development-world corpus, diffing card
  sets by card identity, outputs inside the gitignored data tree, world names and account ids
  redacted - TRIGGER: the advisor emits its first card (CS-500).
- A rule census derived from the rule registry: every rule id has a tier-3 renderer, a firing
  fixture, a mute key and a card identity - TRIGGER: the first advisor rule lands (CS-500).
- Confirm and fill test doubles for install and save discovery (fake install tree, obviously
  synthetic numeric account directory, config override) - TRIGGER: the next change to
  `clockspeed/data/locate.py` or save discovery.
- Release tags carry our version and the pinned game build read from the pin, and release
  notes ship inside the artifact - TRIGGER: a release is actually being cut.
- EVALUATE a headless top-down map of buildings, nodes and claims rendered server-side - spike
  on the synthetic map fixture under a second with approved dependencies only, go or no-go in
  an ADR - TRIGGER: node-siting advice is being built (CS-1243).
- EVALUATE a save-to-save diff attributing each audit-metric change to the built objects that
  changed - TRIGGER: CS-1235's flow audit has landed and a consumer asks what changed.
- EVALUATE measured-versus-nominal throughput: probe which per-machine state fields the save
  exposes, record the result, no write to the save - TRIGGER: CS-1235's nominal flow audit
  has landed.
- EVALUATE exact value iteration over discrete unlock states for routing, against the greedy
  router on synthetic targets; adopt only if it wins on a stated metric and stays
  deterministic - TRIGGER: a milestone router exists (CS-1043).
- EVALUATE player-tunable ranking weights per world, stored as exact rationals in the ledger,
  shown in tier 3 - TRIGGER: CS-1244 lands.
- EVALUATE an asynchronous far-target solve with a progress field - TRIGGER: the slowest
  synthetic far-target solve, measured first, exceeds an agreed latency budget.
- EVALUATE per-card before-and-after history in the per-world ledger, never merged with the
  global mutes - TRIGGER: CS-500's ledger lands.
- EVALUATE local config schema validation failing loud on unknown keys, never echoing a value
  - TRIGGER: a product item hits a config bug.
- EVALUATE a pre-release channel that never replaces stable, plus upgrade notes for store
  migrations - TRIGGER: v1 ships.
- Small lessons, each to be applied when its module is next touched - TRIGGER: that module
  changes: card triggers compute from save state at fixture-tested boundaries, never from a
  timer; inventory math reads per-instance capacity; every save field read has a fixture
  proving it is not a neighbour; never assume index zero exists in a save array; advice says
  when it falls back to a default; save-version dispatch flags and skips an unknown future
  version; the save reader records whether a read completed, was truncated or was refused,
  without echoing header bytes; ledger writes are idempotent per card identity and save
  timestamp; writable state lives only in the gitignored data tree; profile registry load and
  ledger writes once and record the number in a generated census; exclude any input not
  reproducible from save, docs and local config; power planning shows supply and demand
  trajectories, never one side; a retired route or surface is announced in
  `docs/OPERATIONS.md`; an API route census test; README states measured save sizes and
  target distances from the census.
- Ingest residuals, adversary findings below blocking - TRIGGER: the owning module is next
  touched: CS-1235 - a lone-machine shortfall names the item but not the recipe (the flow
  audit could name candidate producers from the recipe mapping), and repeated item keys or
  an item on both sides of one recipe are unexercised; CS-1237 - pin by test that caller
  errors (ValueError, ObjectiveUndefinedError, PowerNotComparableError,
  SearchSpaceTooLargeError) pass the ladder unrelaxed, and that a multi-recipe admit records
  every admitted recipe in registry order; CS-1239 - grade the plan-power goldens through the
  optimizer's own total, refuse an unknown clock-case kind, and add tie cases beyond three
  places and just below a tie.
- Decode building connection state (belt and pipe links between buildings) - out of scope of
  CS-400 by its grammar ruling - TRIGGER: an audit or advice rule that needs throughput between
  buildings rather than what each one holds.

## Stale docstrings - filed 2026-10-04 by the CS-500 integration

- `clockspeed/save/header.py` masked_token docstring says the ledger holds the real token -
  stale since CS-500 S3 keys by sha256 digest - TRIGGER: that module is next touched.
- `clockspeed/save/world.py::WorldModel` docstring says unlocks are empty on every path -
  stale since CS-1039 - TRIGGER: that module is next touched.

## Session 124 residuals - filed 2026-10-04 under product before process

- The CS-400 phase 4 gate shards: per-shard CI time unmeasured, round-robin deal uneven about
  1.8x - TRIGGER: a shard nears `_CHILD_TIMEOUT_SECONDS` in a tier2 log.
- The advisor ledger lock is exercised across threads only, never across processes - TRIGGER: a
  second process writes the ledger (CS-500 S6 wiring or the surface).

## Session 125 residuals - filed 2026-10-04 under product before process

- `scripts/verify_env.py` output, from the CS-1186 README walk: a nonexistent override reads
  `not resolved (tried env, ...)`, which suggests a fallback README says never happens; and
  the account-dir redaction over-matches a numeric non-account path segment as
  `<account-dir>` - TRIGGER: `scripts/verify_env.py` is next touched, or a README re-walk.
- `clockspeed/surface/api/map.py` imports `clockspeed.audit` (since CS-977), the one surface
  module that does; its composition could move behind the advisor/audit seam. And the
  importer detector in `tests/surface/test_advice_source.py` misses a relative import
  (`from ..audit import x`) - TRIGGER: `api/map.py` is next touched, or a surface module
  gains a relative import.

## Session 126 residuals - filed 2026-10-04 under product before process

- `README.md` carries no clone command - TRIGGER: the CS-700 flip; add it then, with the
  public address.
- A clone from the GitHub remote was never walked; both Sandbox walks used a bundle because
  the remote is private - TRIGGER: the CS-700 flip makes the remote public.
- A generator class a future build adds to the registry but not to
  `clockspeed/audit/placement.py::BUILT_CLASS_ALLOWLIST` is dropped silently from the
  production capacity - TRIGGER: a game build bump, or a new generator group in the docs file.
- CS-1269's same-origin refusal was probed without TLS and without a real browser, and the
  dashboard JS sending the proof header was not checked - TRIGGER: the dashboard gains a
  control that records a card state.

## Session 127 residuals - filed 2026-10-05 under product before process

- `tests/advisor/rules/test_power.py` names its CS-1271 arms "reject" for steps that now record
  the verdict-indeterminate kind; node ids are never rewritten, so the fix is a docstring note,
  not a rename - TRIGGER: that module is next touched.
- An omitted clock is priced at the class default and counted complete inside
  `clockspeed/advisor/rules/power.py::_evaluate_headroom`'s draw read - pre-existing, under the
  CS-1263 ruling - TRIGGER: a measured save where an untagged machine runs off-default.
- `clockspeed/advisor/advise.py::advise_and_record` still has no product caller; GET /api/advice
  runs the read-only advise() - TRIGGER: an item or ruling that names its write path.

## Session 128 residuals - filed 2026-10-07 under product before process

- MAIN 2026-10-05 0300 supply-chain ORDER, measured NOT DONE in session 128: no
  `dependabot.yml`, 0 of 19 workflow `uses:` lines SHA-pinned, unhashed `pip install` lines and
  no CI requirements file, no `codeql.yml`, no fuzzing ruled-out record, `SECURITY.md` without
  the advisories-page link, and no Scorecard before/after ever run (token permissions already
  met) - held here by `CLAUDE.md` section 7 "Product before process", which no MAIN note
  reverses - TRIGGER: one of them blocks a product item or turns a suite red, or the
  operator's own words.

## Session 129 residuals - filed 2026-10-08 under product before process

- The CS-1272 project Stop hook runs `ops/fleet_kit/fleet_done.py`, which
  `tests/test_hook_env_echo.py` never scans - its hook population roots at `tools/` only - and
  the cwd-independence arms of `tests/test_pretooluse_gate.py` cover PreToolUse and PostToolUse,
  not the Stop command - the residual the 2026-10-08 FLEET-KIT v9 grant in `docs/LEDGER.md`
  owes here. The CS-1282 PreToolUse SUBAGENT-FIRST hook, `ops/fleet_kit/fleet_subagent_first.py`,
  sits outside the same env-echo population; it renders only its closed mode word, never an
  env value - TRIGGER: the Stop or SUBAGENT-FIRST command or either kit file changes, or either
  guard goes red.
- `tests/ops/test_headless_spawn_paths.py` `direct_starts()` misses
  `npx @anthropic-ai/claude-code`, `cmd /c claude`, `Start-Process -FilePath claude`, nohup and
  timeout prefixes, `start /b` and aliases, and never scans `.ts`, `.yml`, `.vbs` or
  `package.json` - no such start exists today - TRIGGER: a start path in one of those shapes
  or file types lands, or that scan is next touched.
- `tests/ops/test_shared_slots.py`'s formatter-exclusion check matches a kit entry to the kit
  MANIFEST by file NAME only, never by full path or hash - TRIGGER: two kit files share a
  basename, or a tree-owned module takes a vendored file's name.
- `ops/loop/inbox_responder.py` logs a `retired_skip` line on every pass while a retired
  sibling's note stays unread - TRIGGER: that log grows enough to matter, or the note's owner
  is ruled to acknowledge it.
- CS-1274 lane residual: `ops/loop/claims.py` and `ops/loop/ration.py` delete their lock files
  in one attempt with no retry - TRIGGER: a lock file measured left behind, or either module
  next touched.
- CS-1274 lane residual, pre-existing: an interrupt while the driver waits on a live worker
  releases the lane in the `finally` of `ops/loop/queue_loop.py` `run_cycle`, though
  `holder_pid` now makes holding it safe - TRIGGER: a lane measured FREE behind a live worker,
  or that release next touched.
- CS-1274 lane residual: an undeletable pid-0 lock on a lane's home index refuses the claim as
  `lane_held` although other indexes are free, where the kit's acquirer skips to the next
  index - TRIGGER: such a refusal measured with an index free, or the acquirer next touched.
- CS-1274 lane residual: a lock held open in read-only sharing makes the in-place neutralise
  fail too, leaving the lane RUNNING for the driver's life; the kit shares the gap - TRIGGER:
  a lane measured stuck RUNNING behind a dead worker, or kit v10 changes `_release`.
- CS-1274 lane residual, older than CS-1274: `tests/ops/test_driver_module_binding.py` writes
  its probe file into `ops/loop` while the a6 walk in `tests/ops/test_lane_inbox_surface.py`
  reads that directory - a parallel race failing 22-24 of 25 isolated three-test runs at both
  the pre-CS-1274 base and the CS-1274 tip, while `tests/ops -n 3` was green 10 of 10 -
  TRIGGER: the race reddens a real suite run, or either module next touched.
- CS-1272 responder residual, round 3 - the adversary loop stopped by cost against risk, 0 of
  511 live names affected: `ops/loop/inbox_responder.py` `is_damped` matches "terminal" and
  "noreply" as a substring and damps a MAIN ORDER or FIX whose name carries either, while the
  kit never skips an ORDER, FIX or RULING - TRIGGER: a live MAIN note so named, or `is_damped`
  next touched.
- CS-1272 responder residual, round 3: the kit's `note_sender` in
  `ops/fleet_kit/fleet_headless.py` also reads a title line (`# From LL - ORDER`) when the
  filename names no sender; the responder judges the filename only - TRIGGER: a live note
  whose sender only its title line names.
- CS-1272 responder residual, round 3: a judge word outside the vocabulary is treated as live
  (fail open; unreachable with the real verdict, and pinned by no arm) - TRIGGER: the verdict
  vocabulary changes, or the responder's judge next touched.
- CS-1272 responder residual, round 3: a sender-leading MAIN ORDER name gets sonnet, not the
  code model, because the kit finds no ORDER class there - TRIGGER: a live MAIN ORDER so
  named, or the responder's model choice next touched.
- The `docs/ARCHITECTURE.md` row of the `CLAUDE.md` section 4 table, and its copies in
  `.claude/agents/doc-sync.md`, `.claude/commands/sync-docs.md` and `CONVENTIONS.md`, still read
  "Module map, data flow, seams, ownership" and do not name the tooling map CS-1272 moved to
  that file's section 6, which its own header already claims - TRIGGER: the next edit to any of
  those rows, or a doc-sync run that routes a tooling fact by the table.
- `tests/test_subprocess_timeouts.py` keeps its own uncached `scan_repository()`, called about
  six times per run - the per-file floor CS-1277 cached away in `tests/toolpath_guard.py` -
  TRIGGER: the hook shard nears its tier-1 budget, or that module is next touched.
- The responder's item 13a printed checklist is not wired - only the progress-file checklist
  is - and printing the U+2610 box to a redirected cp1252 stdout can raise an encode error -
  TRIGGER: the headless path is ordered to print it (a kit v10 or a MAIN note), or the
  responder's output is next touched.

## Session 131 residuals - filed 2026-10-08 under product before process

- README says verify_env's `config/ports.json` row prints the dashboard's port and calls
  `<port>` "that `allocations` entry"; the row prints only base and band, and the port table
  names the dashboard (walk 2, R2) - TRIGGER: the R1 clone-command edit after the CS-700 flip,
  or `README.md` or `scripts/verify_env.py` next touched.
- README's openssl hint "`git --exec-path` prints a path that starts with it" is ambiguous: Git
  prints `<Git install>/ucrt64/libexec/git-core`, two leading folders qualify, and only the
  outer one has `usr\bin` (walk 2, R3) - TRIGGER: the R1 edit after the flip, or `README.md` next
  touched.
- `docs/OPERATIONS.md` section 1 has no venv or pip step, so a reader arriving from
  `.github/CONTRIBUTING.md` runs the bootstrap under the base interpreter and verify_env fails
  loudly (walk 2, O1) - TRIGGER: the R1 edit after the flip, or either file next touched.
- No walk has exercised a real browser's certificate warning, Python at the requires-python
  floor, or Windows 11; all four used `curl.exe -k`, the newest Python and Windows 10 build
  19041 - TRIGGER: the post-flip public-clone walk.
- A property-body walk that stops with bytes left over drops records from the object table
  entirely, so the clocked draw can still read complete - TRIGGER: a library save logs that
  warning.
- The adversaries' save-library sweeps copied real saves into the session scratchpad, recycled
  by the merger; an adversary brief must keep save copies under the gitignored `work/`
  directory - TRIGGER: the next adversary brief that sweeps the library.

## Session 132 residuals - filed 2026-10-08 under product before process

- The pre-push hook runs no ruff, while tier1's `Lint (ruff check)` step runs
  `python -m ruff check .` over the whole tree, so a lint fault the push passes reddens tier1:
  CS-1282's adoption pushed an I001 import order in `tests/test_claude_hook.py`, repaired by a
  second commit. Builder briefs now name the command - TRIGGER: a second tier1 red on lint
  alone, or the frozen pre-push hook next touched under a grant.
- Two stubbed diagnostic responder passes wrote zero-duration inbox lines into the gitignored
  headless usage log, which the weekly build-versus-inbox split reads - TRIGGER: that split is
  next computed, or a diagnostic pass is next run against the live log.

## Session 135 residuals - filed 2026-10-09 under product before process

- CS-1305 - `child_failure` in `tests/test_cs1172_branch_canaries.py` and
  `tests/test_cs1175_rule_narrowing.py` joins its redaction pattern from the canaries in
  their own order, not longest-first, so where one canary is a prefix (2 pairs) or a
  substring (5 pairs) of another a shorter match can win and leave a tail unredacted;
  unreachable today (CS-1301 adversary pass) - TRIGGER: a canary added, or `child_failure`
  rendering more than identifiers.

## Session 136 residuals - filed 2026-10-10 under product before process

The first five are residuals an adversary or MAIN named against slices of the unpushed
landing branch `s136-land`; the last is a process finding. None blocks a product item or
reddens a suite.

- From the TIER2-RED and CS-1300 concurrency adversary: the 5 s live-sibling retry in the quiet barrier can hide a sibling
  that stops inside it; it cannot turn a failing run green - TRIGGER: a tier2 or pre-push red
  traced to a sibling the barrier did not wait for.
- From the CS-1280 adversary: the end-to-end arm in `tests/surface/test_advice_source.py` does not check the
  4.00 MW figure in the card's reason (`tests/audit/test_balance.py` does) - TRIGGER: the
  reason text of that card next changes.
- From the CS-1285 slice A rounds: the A11 detail text can name the wrong field (cosmetic); a non-string
  ClassName in an unmodeled group is not flagged - TRIGGER: a registry with a non-string
  ClassName, or slice B v2 reading that detail.
- From the CS-1292 lenses: the SHA citation gate does not see a citation added and removed in a commit behind
  HEAD, a `..` spelling of the checkout path, or a forged commit-graph; only git 2.53 was
  tested; the docs tests match exact strings, so a rewording passes them; the banner text
  reads "no LLM in the advice path" - TRIGGER: the CS-700 S7a history rewrite, a git upgrade,
  or the README or banner next edited.
- MAIN's note that the repository description is about 300 characters, where GitHub shows
  about 160, is unaddressed - TRIGGER: the CS-700 S12a settings re-apply.
- 67 tests fail rather than skip when the shell's PATH lacks Git's usr/bin (openssl, sh): the
  session 136 landing suite, run from an agent shell, read them red; they pass with it -
  TRIGGER: a clean-machine walk or CI image without Git's usr/bin, or a third such red.
- Process: agents of one session shared the session scratchpad and overwrote each other's
  `prog.py`, `msg.txt` and possibly `freeze.json` - the session 135 shared-helper trap one
  level wider. Every agent brief names unique scratch file names - TRIGGER: a progress file,
  commit message or freeze witness read back with another agent's content.

## Session 137 - filed 2026-10-11 under product before process

Three conditional items from session 137: two from its rulings and one CS-1309 residual. None
blocks a product item or reddens a suite.

- CS-1311 - pin one diagnosed third-party save out of the library sweeps by content, size AND
  SHA-256, in a strict expected-refusal control; moved here under Ruling 4's reversal clause when
  the refused file left the library before the pin was built - TRIGGER: a refused library save
  reddens the sweeps again. The pin design and its precondition evidence: `docs/LEDGER.md`, the
  2026-10-11 CS-1311 record.
- Fuel derating, CS-1285's option C, deferred by Ruling 5: a derated fluid supply in place of the
  `supply-input-uncovered` indeterminate wherever every chain leaf is rated, its solver in
  `clockspeed/solve/` - TRIGGER: a measured source for extractor rates (CS-1048). The ruling:
  `docs/LEDGER.md`, the 2026-10-11 CS-1285 slice B v2 record.
- CS-1309 residual (a): save file paths, which can carry a world name, sit in the world
  provider's memo keys and in the fallback walk's frame locals. They are reachable only through
  a repr of the provider's attribute dict or a traceback rendered with its locals, and nothing
  renders either today; the base held one such path, the slice one per refused or identified
  save - TRIGGER: a locals- or vars-rendering path reaches a log, report or response. The
  close: `docs/LEDGER.md`, the 2026-10-11 CS-1309 CLOSED record.

## Session 138 residuals - filed 2026-10-12 under product before process

The CS-1285 close's residuals: the slice C rulings G1 to G6, the two adversary refutations and
the verifier are its records in `docs/LEDGER.md`, 2026-10-12. None blocks a product item or
reddens a suite.

- From the CS-1285 slice C rulings: the fuel demand card's subject is the sorted set of its fired
  classes (G1), so a dismissed demand card shows again whenever that set changes - TRIGGER: the
  engine issues one card per subject per rule (G1's reversal), or a dismissed fuel card is
  reported back.
- From the CS-1285 slice C rulings: a world with a built solid burner never auto-completes the
  fuel supply card, since `power.fuel_supply` records an indeterminate step for every
  indeterminate class and solid fuels are never measured (G2) - TRIGGER: a measured source for
  solid supply, or per-subject settlement in the ledger.
- COMMON-MODE, from the CS-1285 close: the fuel supply FIRE path has one reachable vanilla class,
  the liquid-fuel burner, and no library save builds one, so no real save has driven a fuel FIRE
  or REJECT; the rule's recomputation shares the fuel audit's formulas, so their agreement
  catches wiring faults, not formula faults; and the v2 ruling's `Desc_LiquidFuel_C` residual
  check is unmeasured for the same reason - TRIGGER: the first library save with a liquid-fuel
  generator built: probe both fuel cards read-only.
- From the CS-1285 adversaries: the fuel demand card's tier-2 "N built generators were never
  read" sums over every fired class without naming the class - TRIGGER: that reason text next
  changes, or a reader asks which class.
- From the CS-1285 adversaries: which reason the fuel demand card's tier-2 detail cites when a
  class carries several is not ruled (the rulings are silent) - TRIGGER: a ruling on reason
  precedence, or that detail text next changes.
- From the CS-1285 adversaries: a known demand beside an `instances-omitted` reason fires a
  settled fuel demand card, reachable from synthetic inputs only - TRIGGER: the fuel audit lets a
  class with an omitted instance keep a known demand.
- From the CS-1285 adversaries: the import detector in `tests/surface/test_advice_source.py`
  misses relative imports, and none exist today - TRIGGER: the first relative import in the code
  it scans.

The CS-1288 close's residuals: the slice C rulings F1 to F9, the F8 amendment, the /api/map scope
decision, the adversary refutation and the verifier are its records in `docs/LEDGER.md`, 2026-10-12.
None blocks a product item or reddens a suite. Its common-mode residual is CS-1315 and its /api/map
residual CS-1316, so neither has a line here.

- From the CS-1288 slice C rulings: tier 1 carries no build marker (ruling F5), so any renderer
  that shows headlines only - the overlay among them - must still show the build-mismatch state, or
  it presents an off-pin card as the save build's own - TRIGGER: a headline-only surface ships (F5's
  reversal), or the overlay mode is built.
- From the CS-1288 adversary: the F7 arm 2 census in `tests/advisor/test_every_rule_fires.py`
  counts `Recommendation(` calls by callee name, so a rule module binding `Recommendation` under
  another name could add a return site without the build caveat that no arm counts; decided a
  residual, not hardened - TRIGGER: the next rule module added to `RULE_MODULES`, or any rule module
  binding `Recommendation` under another name.
- From the CS-1288 adversary: with no pin, a card's tier 2 says the save build was never compared
  "as no pinned build exists", while its tier 3 carries the audit's `build-uncompared` detail, which
  says every nameplate figure is priced at the pinned build; reachable only if the pin fails to
  parse - TRIGGER: `GAME_CHANGELIST` in `clockspeed/data/version.py` reads None, or either text next
  changes.
- From the CS-1288 adversary: `tests/advisor/test_build.py`'s adapter arm, exactness-walk arm and
  forged-input rows run only at the pin plus one, while fix 1 put its off-pin caveat arms on both
  sides of the pin - TRIGGER: the next edit to `clockspeed/advisor/build.py`.
- From the CS-1288 adversary: an off-pin run reopens a completed card, completed back to new,
  until the next on-pin run, since an off-pin rule never settles (ruling F1); `advise_and_record` in
  `clockspeed/advisor/advise.py` has no production caller - TRIGGER: `advise_and_record` gains a
  production caller.
- From the CS-1288 adversary: the build caveat checks the warning detail's type only; the audit's
  detail table is private to `clockspeed/audit/build.py`, so a forged detail is not reachable from a
  real input - TRIGGER: a build warning detail built from anything but that table, or the table made
  public.

The CS-1298, CS-1313 and CS-1314 closes' residuals: the rulings Q1 to Q3, the Q3(a) amendment, the
batch adversary, both fixes and the verifier are their records in `docs/LEDGER.md`, 2026-10-12.
None blocks a product item or reddens a suite.

- From the CS-1313 batch adversary (its F4): the closed equipment-group list in
  `clockspeed/data/registry.py` is held to the game's own docs only by the two installed-document
  arms of `tests/data/test_registry.py`, which skip where no game is installed, so CI never checks
  it; a patch adding an equipment group, or giving a second equipment class a power field, reddens
  only on a machine with the game - TRIGGER: a pin move.
- COMMON-MODE, from the session 138 rulings: `Desc_Locomotive_C`, a vehicle descriptor the registry
  carries in its consumer namespace with no power figure, is not equipment under ruling A1, so a
  record of it would count as a built consumer through a draw gap; no library save holds one, 0 of
  41 read - TRIGGER: the first library save holding a locomotive record.
- From the session 138 rulings, the dropped-recipe blind spot: a recipe the registry dropped hides
  its producer class from the flow and from starvation, so a record of that class is not named and
  the flow can read complete; pinned as current behaviour by
  `tests/audit/test_flow.py::test_residual_a_recipe_the_registry_dropped_hides_its_producer_class_from_the_flow` -
  TRIGGER: a registry change to which recipes it keeps or drops, or that arm reddening.
- From the session 138 rulings: the hover-pack save shape is unmeasured - no library save holds an
  `Equip_HoverPack_C` record, 0 of 41 read, so its exclusion is proved on synthetic records only,
  while every other equipment record the library holds reads as a top-level actor - TRIGGER: the
  first library save with a hover-pack record: confirm it is an actor record and still excluded.
- From the CS-1314 fix verifier, two text leftovers: the CS-1314 starvation section comment in
  `tests/audit/test_balance.py` still says "a built record of a class that runs recipes", and the
  CS-1313 equipment text in `clockspeed/audit/balance.py` still calls equipment records "built
  records" - TRIGGER: the next edit to `clockspeed/audit/balance.py`.

## Session 139 residuals - filed 2026-10-12 under product before process

The CS-1318 repair's residuals; its record and the session 139 rulings are in `docs/LEDGER.md`,
2026-10-12. Neither blocks a product item or reddens a suite.

- From the CS-1318 refutation: `tools/freeze_witness.py` counts untracked bytecode in its digest, so
  it can report MOVED while every tracked byte is unchanged - TRIGGER: a witness reads MOVED on a
  candidate whose tracked bytes are unchanged, or the next edit to `tools/freeze_witness.py`.
- From the CS-1318 adversary: the reap check in `tests/test_hook_probe_bound.py` falls back to a
  one-shot `kill -0` where there is no proc filesystem (macOS), so a zombie there still reads as a
  survivor; latent while no CI job runs on macOS - TRIGGER: the first CI job on macOS.

The CS-1323 close's residuals; its record and its stop ruling are in `docs/LEDGER.md`, 2026-10-12.
None blocks a product item or reddens a suite.

- From the CS-1323 adversaries: the KEEP RULE's Recycle Bin call in `.claude/commands/done.md`
  passes `OnlyErrorDialogs`, which can block a headless run on a dialog, and a relative folder path
  resolves against the .NET working directory, not the shell's; both fail safe, keeping the folder -
  TRIGGER: the KEEP RULE next runs at S12a, or the next edit to its recycle step.
- From the CS-1323 adversaries: `tests/test_done_ritual_arms.py` pins done.md's step order by
  position and some clauses by phrase, so mutants survive: "but only the records" in KEEP RULE step
  (1), dropping "recorded deletion is still absent" in step (4), and "unless the reset already
  ran" - TRIGGER: the next edit to the KEEP RULE or to those arms.
- From the CS-1323 6.1 ruling: `memory/full-authority-adjudicate-do-not-ask.md` still states
  `CLAUDE.md` section 6.1's push rule as absolute, without the /done cases done.md names - TRIGGER:
  the next memory staleness scan, or the next edit to that leaf.

## Session 140 residuals - filed 2026-10-13 under product before process

The game patch's residuals; the CS-1315 and CS-1316 R3 reversal record and the CS-1324 re-pin
record are in `docs/LEDGER.md`, 2026-10-13. Neither blocks a product item or reddens a suite.

- From the session 140 R3 narrowing: install-side inputs other than the docs file moved with the
  patch and carry no pinned digest - the usmap read from the install
  (`clockspeed/save/usmap.py::USMAP_RELATIVE`) and Headers.zip
  (`clockspeed/data/assets.py::HEADERS_ARCHIVE_PARTS`, 104 bytes larger than at ADR 0005); with no
  earlier digest, whether saves written at the previous build now decode differently is unknown -
  TRIGGER: a change in parse warnings on a save written at the previous build.
- From the session 140 R3 narrowing: `tools/drift_guard.py::_live_differences` prints "only the
  bytes moved" whenever the census is unchanged, which is false when only the build string moved -
  TRIGGER: the next guard (h) work.
- From CS-1325: `scripts/verify_env.py::MIN_PYTHON` asserts only the Python floor, not the
  `requires-python` ceiling in `pyproject.toml` - TRIGGER: the next `scripts/verify_env.py` work,
  or the cap moving.
- From CS-1325, a residual: `README.md` is at its 220-line budget and its Quickstart at its 10-line
  budget; the deferred clone command (the Session 126 residuals line above, added at S12a) will
  push both over, and its `git clone` line must sit in its own fenced block or
  `tools/flip_checks.py::command_lines` (check 5 reads python-only blocks) finds 0 commands again -
  TRIGGER: S12a.
- From the CS-1315 slice A review (g2): `clockspeed/surface/providers.py::InstalledRegistryProvider`
  rebuilds the registry and re-hashes the whole multi-megabyte docs file (the pin's docs_bytes owns
  its size) on every request, and `clockspeed/data/registry.py::build_registry_from_bytes` keeps the
  raw bytes alive through decode, parse and normalize - TRIGGER: a measured latency or memory
  regression, or a cache item.
- From the CS-1315 slice A review (g3): `clockspeed/data/version.py::DOCS_SHA256` turns a null
  docs_sha256 in the pin into the string "None", which reads as registry-mismatch, not
  registry-unverified (it fails loud) - TRIGGER: a generator that can write a null docs_sha256.
- From the CS-1315 and CS-1316 close (K4): `tests/surface/audit_harness.py::_canned` serves the
  /api/solve and /api/optimize stand-in bodies with no build_state and no warnings, under a stale
  docstring, and no guard pins their key set to what the real doors serve - TRIGGER: the next
  `tests/surface/audit_harness.py` work.
- From the CS-1315 and CS-1316 close (K4): `registryLine` in
  `clockspeed/surface/web/panel_power.js`, `clockspeed/surface/web/panel_solve.js` and
  `clockspeed/surface/web/panel_optimize.js` prints "UNVERIFIED" with the served code for a
  registry-mismatch, less specific than the map panel's "bytes DIFFER" - TRIGGER: the next panel
  wording pass.
- From the CS-1315 and CS-1316 close (K4): `tests/surface/test_power.py::bare_rate_paths` would
  pass a top-level key spelled literally "warnings[0].count", since its exemption matches the path
  string, and passes a float anywhere (pre-existing) - TRIGGER: the next edit to that walker.
- From the CS-1315 and CS-1316 close (K4): the empty-throughput line in `mountMap`
  (`clockspeed/surface/web/panel_map.js`) lists every served warning code, the build codes
  included, as "the reason" no throughput was served - TRIGGER: the next
  `clockspeed/surface/web/panel_map.js` edit.
