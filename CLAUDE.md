# Clockspeed - operating rules

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

Auto-loaded every turn. Budget: under 40 KB, CI hard fail above it. Every byte here costs
context on every turn of every session.

This file owns rules, hard constraints, the frozen file list, settled decisions, paths and
topology. It NEVER contains per-item completion entries, counts, or ledger entries - those
go to `docs/LEDGER.md`.

The full specifications remain on disk and are authoritative where this file is a
summary: `BOOTSTRAP.md` (the project specification) and `CONVENTIONS.md` (the portable
operating doctrine). Read both when a rule here needs its rationale.

---

## 1. What Clockspeed is

A local, deterministic planning and advisory system for a single-player factory-building
game. It reads the game's own shipped data files and the player's save file, computes
exact production mathematics, and issues terse, context-aware, actionable advice about
what to build next.

Four properties define it:

- **Deterministic.** No language model, no cloud service, no API key, anywhere in the
  advice path. Every recommendation is reproducible from the same inputs. If two runs on
  the same save disagree, that is a bug.
- **Local.** Everything runs on this machine. Nothing is uploaded.
- **Terse.** Advice is one line by default. The full derivation is available on demand and
  is genuinely complete when requested.
- **Read-only against the game.** Clockspeed never writes to the game install and never
  modifies a save file. Ever.

It is NOT a mod, a cheat, a wiki, a chat interface, or anything that injects into or reads
the game process memory.

---

## 2. Paths and topology

**Project root:** `C:\Clockspeed`

**Game install: auto-detected.** Never hardcode the install path. `clockspeed/data/locate.py`
finds it at runtime and `scripts/verify_env.py` asserts the result.

**Save directory: auto-detected.** The root is `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\`
and the account subdirectory beneath it is found by globbing for numeric directories,
picking the most-recently-modified one, overridable by local config. **That subdirectory
name is a platform account id. It is personal data and is never written into a tracked
file, a commit message, a log, a fixture or a test.** The same applies to the world name,
the Windows account name and any absolute path containing a home directory.

**Interpreter, toolchain and game build:** asserted by `scripts/verify_env.py` and pinned
by `clockspeed/data/version.py`. Do not restate a version or a build string in prose -
read it from the pin, and let `tools/drift_guard.py` catch drift.

**Port allocation:** recorded in `config/ports.json`. That file is the owner; no other
file restates the numbers.

### 2.1 Module map - one line each, detail in `docs/ARCHITECTURE.md`

| Path | Owns |
|---|---|
| `clockspeed/data/` | Install and save location, docs extraction, normalized registry, version pin, drift guard |
| `clockspeed/save/` | Header parse, chunk walk, usmap load, actor deserialization, the world-state model |
| `clockspeed/solve/` | Exact Fraction primitives, target-rate ratio solve, optimizer behind `OptimizerBackend`, power and clock math |
| `clockspeed/audit/` | Whole-world audit against what is actually built (pillar 3) |
| `clockspeed/progress/` | Milestone and progression routing against any target (pillar 4) |
| `clockspeed/advisor/` | Rule trace, rules, card identity and rendering tiers, per-world ledger and global mutes (pillar 5) |
| `clockspeed/surface/` | Local HTTPS API and dashboard |
| `shell/` | Electron companion window |
| `ops/loop/` | The headless `queue` lane - lane lock, launcher, runner, and the driver that owns every wait |
| `tests/` | Test suites, synthetic fixtures only |
| `tools/` | Gates, guards, sync, probes |
| `scripts/` | `install_hooks.py`, `verify_env.py` |
| `config/` | Tracked local configuration, including the port allocation record |
| `docs/` | Architecture, operations, ledger, gated items, ADRs |
| `memory/` | Durable cross-session facts, markdown is the source of truth |
| `data/` | Generated artifacts - GITIGNORED, never tracked |

**Seam discipline.** Each layer consumes only the layer below it through a stated model.
`solve/` never reads a save. `advisor/` never reads the raw docs file. `surface/` never
computes. A layer that reaches past its neighbor is a design bug.

### 2.2 Tooling map

| Path | Does |
|---|---|
| `scripts/install_hooks.py` | Sets `core.hooksPath`, installs `.githooks/`. Idempotent. Fails loudly if it cannot set the path |
| `scripts/verify_env.py` | Asserts interpreter, toolchain, paths and ports. Prints found/missing, exits non-zero on a missing hard dependency |
| `tools/precommit_gate.py` | Character-set gate, secret scan, staged-line lint, syntax check |
| `tools/edit_lint_check.py` | `PostToolUse` syntax and lint check on an edited file |
| `tools/drift_guard.py` | Doc and pin drift detection |
| `tools/doc_budget.py` | File-size budget enforcement |
| `tools/facts_probe.py` | Live-state fact set. Run BY HAND from `/drift-guard` and `/sync-docs`; NOT a hook |
| `tools/inbox_watch.py` | Unread `moon_sync_inbox/` items, payloads included. Listing never acknowledges. Wired ONLY in gitignored local settings, so a fresh clone and every worktree run NO watcher - CS-952 |
| `tools/memory_sync.py` | Mirrors markdown memory into the recall store, idempotent |
| `tools/dashboard_probe.py` | The SCRIPTED answer to "does the dashboard run". Launch, poll, assert a JSON key and a DOM node, one screenshot, exit code decides |
| `tools/headless-queue.md` | The `queue` lane worker's prompt. TRACKED, because a worktree is a fresh checkout and carries no gitignored file |
| `ops/loop/queue_loop.py` | The lane driver. Repeats the one-row worker AND owns every wait, so nothing can cancel a run mid-grade |
| `ops/loop/launch_queue_loop.ps1` | Starts the driver detached. Refuses over a stop sentinel and prints no banner over a no-op |
| `.githooks/pre-commit`, `commit-msg`, `pre-push` | Tier-0 blocking gates. Authoritative; the Claude hooks are a convenience layer |

**A fresh clone runs zero protection until someone wires it.** The bootstrap order lives in
`docs/OPERATIONS.md` and runs first thing in any fresh clone. Never treat a hook's presence
as proof it fires - the only valid test is end to end: stage a violation, attempt a real
commit, assert HEAD is unchanged.

### 2.3 Output constraints - the transcript is a cost, not a scratchpad

**Keep each chat response under roughly 500 output tokens.** Break long work across turns,
or write verbose output to a file. Operator directive, 2026-09-06.

The operator watches several project sessions side by side, so prose in the main transcript
costs tokens on both ends AND buries the thing being decided. A quiet session is one where
the tool-call labels carry the narration.

- Speak to ask for a ruling, to notify, or to answer a direct question. Otherwise act.
- No narration between tool calls, and never restate what a tool just printed.
- Put the step description in the tool call's own `description` field - it renders as the
  visible label and costs nothing in the response body.
- Long findings go to a file, a ledger entry or an item note, never into chat.
- **Do NOT poll a background task in a loop of one-line turns.** Each poll is a whole turn.
  Wait for the completion notification.

---

## 3. Non-negotiables

The ten from `BOOTSTRAP.md` section 12:

1. Never write to the game install directory or the save directory.
2. Never commit game data, save files, or anything extracted from the install.
3. Never hardcode the account id, the world name, the Windows user, or a home path.
4. 7-bit ASCII in all authored content. No em-dashes, en-dashes, or smart quotes.
5. Atomic writes for every file another process may read.
6. Exact rational arithmetic in the solve path. Assert the absence of floats.
7. Unknown game content is flagged and skipped, never fatal, never silently wrong.
8. Every advice card's tier-3 derivation is generated from the trace, never hand-written.
9. TDD: the failing test comes first, and it must fail for the right reason.
10. The main session stays responsive - heavy work goes to subagents and worktrees.

Of equal rank, from `BOOTSTRAP.md` section 2.2 - the save header carries platform,
account and player-display-name strings in plaintext inside an options string:

11. A save file is a personal-data-bearing artifact. Never commit one, never attach one to
    an issue, never place one in a fixture directory.
12. Any code path that echoes raw header bytes leaks personal data. The header parser
    redacts the options string by default and requires an explicit opt-in flag to render
    it. Error messages, debug dumps, hex previews, log lines and exception context all
    count as echo paths.

Rule 4 has a mechanism, not just a preference behind it: Windows PowerShell 5.1
ANSI-decodes a `.ps1` with no BOM, and a UTF-8 em-dash inside a double-quoted string
becomes a character the tokenizer treats as a string terminator. One incident made it
permanent. Use a spaced hyphen ` - ` for a clause break.

---

## 4. Doc topology - which file owns which fact

Every fact has exactly ONE owner file. Other files link to it; they never restate it. A
restated fact is a fact that will drift. This table is the anti-drift control.

| File | Owns | Never contains |
|---|---|---|
| `CLAUDE.md` | Rules, hard constraints, frozen list, settled decisions, paths, topology | Per-item history, counts, ledger entries |
| `README.md` | Outsider-facing: what it is, install, run, first result | Internal process, roadmap, session notes |
| `ROADMAP.md` | OPEN work only - the item LINE alone, with its ID, acceptance and tier | Completed work, aspirational ideas, NOTE bodies |
| `docs/item_notes.md` | The INDEX over `docs/item_notes/` - the routing table plus the rules every leaf obeys | Any item body, item lines, completion records, history |
| `docs/item_notes/` | LIVE per-item detail for OPEN work, one leaf per phase, one section per item ID | Item lines, completion records, history, closed items |
| `BACKLOG.md` | Aspirational and conditional-trigger items, one line each | Anything currently being worked |
| `WAKEUP_NOTES.md` | Last two to three sessions at full fidelity | Anything older - archive it |
| `docs/LEDGER.md` | Append-only, newest-first per-item completion record | Rules, open work |
| `docs/ARCHITECTURE.md` | Module map, data flow, seams, ownership | Ops commands, counts |
| `docs/OPERATIONS.md` | Commands, restart, scheduled tasks, runbooks | Architecture, rationale |
| `docs/adr/` | One file per architectural decision, indexed in `docs/adr/README.md` | Anything not a decision |
| `docs/GATED.md` | Items blocked on something outside the repo | Items merely unstarted |
| `docs/hud_doctrine.md` | The operating law of the companion and the overlay surfaces | Palette values, build detail, open work |
| `docs/upstream_watch.md` | The upstream wiki watch list and the ordering it is read in | Lifted upstream content, the CS-485 licence verdict |
| `docs/history_notes.md` | Deep archive of pruned notes and retired ledger entries | Current state, live instructions for OPEN work |
| `memory/` | Durable cross-project and cross-session facts | Project state derivable from code |
| `config/ports.json` | The port allocation record | Anything not a port allocation |
| `clockspeed/data/version.py` | The game build pin and content hash | Advice, parsing, presentation |
| `BOOTSTRAP.md` | The full project specification | Portable doctrine |
| `CONVENTIONS.md` | The portable operating doctrine | Project-specific content |

Rules that follow from the table:

- **Never append a per-item completion entry to this file.** It is auto-loaded every turn
  and size-budgeted. Ledger entries go to `docs/LEDGER.md`.
- **Do not restate a measured number in prose.** Counts, coverage, versions and item
  totals belong in exactly one machine-checked place with a drift guard. A hardcoded count
  in a doc is a lie with a timestamp on it. If a doc must display one, generate it.
- Dated artifacts go to `docs/_archive/`, excluded from search, so they never pollute a
  search for current truth.
- A doc heading whose date LEADS the heading marks its own section historical; a date
  after a provenance verb records only when the text was filed, moved or measured, and
  marks status not at all - so a live document is free to carry one. **A file carrying
  dated headings declares its own status in its header** - `Section status: LIVE` or
  `HISTORICAL` - and a status date inside a file declaring itself LIVE is drift. The
  declaration lives inside the file it describes, so the two cannot drift apart the way
  a list held in code does. `tools/drift_guard.py` guard (g) owns the closed idiom
  vocabulary and FAILS on either fault.
- When a size budget is hit, **relocate, do not delete.** Move detail to a sub-index or an
  archive file and leave a one-line pointer.

---

## 5. Session shape - the default, not an escalation

**Every session is orchestrated, multi-agent, self-adjudicating and self-adversarial by
default.** Choosing this shape needs no justification. Departing from it does, and the
justification is recorded.

- **Orchestrated.** One merger holds the plan and the merge. Work is decomposed into
  disjoint slices BEFORE any of it starts. The merger's context stays small - it holds the
  plan and the seams, not the implementations.
- **Multi-agent.** Slices run in parallel on non-overlapping files, worktree-isolated
  wherever they write. Disjointness is a precondition checked before dispatch, not a hope.
- **Self-adjudicating.** A distinct agent decides between competing outputs against stated
  criteria. **The agent that produced a thing never grades it.** **THE CANDIDATE IS FROZEN
  BEFORE DISPATCH** - pin it at a SHA or a worktree, as read-only adversaries already are.
  A tree that edits itself mid-verdict makes the ruling a statement about no state at all,
  and any finding repaired while the adjudicator writes is one it cannot see it discharged.
  Measured in session 45: the tree moved under an adjudicator four times, and three
  whole-suite runs were spent proving that a run straddling an edit says nothing.
- **Self-adversarial.** Findings and done-claims get an independent pass whose job is to
  REFUTE them, defaulting to refuted when uncertain.

The only exception is genuinely trivial work: a one-line cosmetic edit, a doc typo, a
single string, a conversational answer. Substance decides, not file count. A one-file
engine change is substantive; a five-file rename is not.

Supporting facts that make it work:

- **Agreement between two agents is not evidence.** Two agents can be wrong the same way,
  especially when both derive from the same stale doc or the same fixture.
- Spawn refuters with distinct lenses - correctness, security, does-it-reproduce, resource
  lifetime - rather than several identical skeptics.
- **Never trust a subagent's claim about test counts, green CI, or file existence.** Probe
  independently: list the cited file, re-run the suite, read the exit code.
- Never fabricate or predict a pending agent's result. If asked before it lands, say it is
  still running.
- The spec comes before any code exists, and is verified against ground truth - grep every
  cited `file:line`, probe every cited endpoint - before a single file is scaffolded.

Work-item states, one per item, one file each: OPEN in `ROADMAP.md`, ASPIRATIONAL in
`BACKLOG.md`, GATED in `docs/GATED.md`, CLOSED in `docs/LEDGER.md` plus a Settled line
here if it must never reopen. Item IDs use the `CS-` prefix, are permanent, and are never
reused. Ledger entries cite the item ID, the merged file and the test name - not a slice
SHA, which often does not survive a cherry-pick.

---

## 6. Frozen files

These require explicit operator approval to modify:

- `.githooks/*`
- `scripts/install_hooks.py`
- `tools/precommit_gate.py`
- `.claude/settings.json`
- `LICENSE`

**The rule:** an agent proposing to touch a frozen file routes the proposal through an
adjudicator, and the grant is recorded in `docs/LEDGER.md` before the edit is made. No
agent grants itself the exception, and no agent widens the list without the same route.

---

## 6.1 Authority - filed 2026-09-13 by operator directive

**Full authority is granted by default, in every session shape.** Frozen files, full
computer use, OBS, computer vision, keyboard, mouse, window, browser, research, download,
install, terminal and settings access are granted, and restarting the server, the overlay
or the dashboard is allowed even mid-game.

**A blocked decision goes to an ADJUDICATOR, never to the operator.** Anything an agent
would have marked "not without operator approval" is adjudicated and the best
recommendation is taken immediately. Never ask the operator to authorise a send or to pick
a direction - they intervene by typing into the main session. Section 6's frozen-file route
is unchanged in shape: adjudicator grant, recorded in `docs/LEDGER.md` before the edit.
Only the grantor changed.

**This removes the operator from the approval path. It removes nothing else.** Section 3 is
untouched: no red suite ships, the failing test still comes first, and nothing is called
done that its acceptance says is not.

**Nothing stays uncommitted or unpushed.** Batch commits and pushes so CI waits overlap
with other work - remembering that CI runs only the TIP of a push, so a batch leaves its
intermediate commits untested.

**A status request is answered with the session checklist inline** - DONE, STILL OPEN,
added, retracted - not with prose. Every action, tool call and agent dispatch carries an
expected duration in its label.

Rationale and the operator's own evidence: `memory/full-authority-adjudicate-do-not-ask.md`.

---

## 7. Settled - decided, do not re-litigate

Each entry records what was decided AND specifically what not to re-pitch. A settled entry
that records only the conclusion invites someone to rebuild the argument. The fence is the
point.

**The two that matter most are the zero-language-model rule and the never-write rule.**

- **Zero language model in the advice path.** The advisor is fully deterministic and local
  - no model, no cloud service, no API key anywhere advice is computed, ranked, explained
  or rendered. *Do not re-pitch:* an LLM-backed explainer, summarizer, ranker, natural
  language front end, or a model used "only for the prose". The tier-3 derivation is
  generated from the rule trace, which is exactly why no model is needed.
- **Never write to the game install or a save file.** An invariant, not a preference.
  *Do not re-pitch:* an opt-in write mode, a backup-then-write, an in-place save edit, a
  "safe" patcher, or writing anything at all into the save directory.
- **Name is Clockspeed, root is `C:\Clockspeed`.** *Do not re-pitch:* a rename or a
  relocation of the root.
- **Repo is private first, public later.** Hygiene is enforced from the first commit
  anyway. *Do not re-pitch:* deferring hygiene work on the grounds that the repo is
  private.
- **Python core.** Node exists solely for the Electron shell. *Do not re-pitch:* a rewrite
  in another language, or moving core logic into the Node side.
- **Three explain tiers: headline, one-line reason, full derivation.** *Do not re-pitch:*
  collapsing to two, or adding a fourth.
- **Persistence is per-world ledger PLUS global per-rule mute.** Both layers. *Do not
  re-pitch:* dropping either one, or merging them into a single store.
- **All four advice domains ship in v1** - node siting and claim order, onsite processing
  versus transport and by what method, milestone gap against any target, and power and
  fuel planning. *Do not re-pitch:* cutting a domain to a later version.
- **Milestone target is a free selector.** *Do not re-pitch:* a fixed pointer at the next
  milestone. Selecting a target several tiers out and getting a redesign plan is required
  capability, not a stretch goal.
- **Companion window in v1; the in-game overlay is a later flagged mode of the same
  shell**, default off, degrading to the companion on bind failure. *Do not re-pitch:*
  building the overlay first, making it the default, or treating it as a separate app.
- **Mods: architecture now, content later.** Namespaced identifiers, unknown classes
  tolerated, unmodeled content flagged, feature-flag registry from phase 0. *Do not
  re-pitch:* opening mod content work before phase 6 completes.
- **Dedicated Server API is out of scope for v1.** The docs are on disk and free to read,
  but single-player saves are the world-state source. *Do not re-pitch:* it as a
  world-state source. Revisit only if the operator starts running a dedicated server.
- **No external optimizer dependency in phase 3.** Interface first, dependency later and
  gated. *Do not re-pitch:* an LP or ILP library before `OptimizerBackend` exists, before
  it slots behind the interface without changing a caller, and before the `CONVENTIONS.md`
  section 14 license gate passes.
- **No lifted datasets, including from the OFFICIAL wiki.** Both sanctioned paths - the
  save itself, or extraction from the shipped assets - are cleaner. The official wiki is
  CC BY-NC-SA 4.0, so vendoring any part of it would relicense this project and conflict
  with `LICENSE`; the gate result and the reasoning are in `docs/LEDGER.md` under CS-485.
  Reading it and citing a URL is CLEARED and carries no obligation. *Do not re-pitch:*
  lifting a node dataset, a table or a data dump from any wiki or community source; nor an
  automated poller against the wiki, which its platform terms appear to forbid. *Do not
  argue from "it is official":* that is the site's standing, not any page's authority, and
  its save-format pages are a major version stale and carry a byte label this project has
  already measured false.
- **The reference world is the operator-pinned development world** - vanilla, no creative
  mode, no modifiers, onboarding active - snapshotted into a gitignored corpus as it
  grows. *Do not re-pitch:* switching reference worlds without recording why. Its name
  stays out of every tracked file; refer to it as the pinned development world.
- **The advice ledger is keyed by the save header's world token**, not by filename and not
  by world name. *Do not re-pitch:* filename or world-name keying - filenames change on
  every save and autosaves rotate. The ledger tolerates a token it has never seen by
  treating it as a new world rather than failing.
- **Test fixtures are small synthetic registries hand-authored in the repo**, never slices
  of real game data. *Do not re-pitch:* checking in a trimmed real docs file or a trimmed
  real save "just for tests". The rule suite must run on a machine with no game installed.

Anything settled by an ADR is recorded in `docs/adr/` and indexed there; this list holds
the decisions that predate the first commit.

---

## 8. When a spike contradicts the spec

Ground truth beats every document, including this one. If a probe or a spike result
contradicts `BOOTSTRAP.md`, the probe wins: update `BOOTSTRAP.md`, record what changed and
why in `docs/LEDGER.md`, and say so plainly in the session report. `BOOTSTRAP.md` is a
specification written from probed ground truth plus labelled assumptions - the assumptions
are labelled precisely so this can happen without ceremony.
