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

The block between the FLEET-COMMON markers is NOT under this repository's MIT grant: it is
MAIN's fleet kit block, Apache-2.0, unmodified - see `ops/fleet_kit/NOTICE` and the
`THIRD_PARTY.md` row for `ops/fleet_kit/FLEET-COMMON.md`.

**Precedence - where this file and the FLEET-COMMON block differ, `CLAUDE.md` governs
this tree.** Specifically: (a) section 2.3's rule never to poll a background task in
one-line turns governs over FLEET item 12's periodic check - wait for the completion
notification; (b) retired at kit v9, whose item 13 carries the checklist section 2.3.1
applies; (c) FLEET item 10 has one stated exception until CS-1231 slice C finishes -
`ops/loop/run_lane.ps1` still starts `claude` directly; `ops/loop/inbox_responder.py`
goes through the kit's spawn; (d) FLEET item 5's rule that
every do-not-re-litigate entry states what would reverse it is met by the *Reversed by:*
clause on each section 7 entry. Section 6.1's repository-public/remote safety floor holds
whatever FLEET item 1 says.

<!-- FLEET-COMMON BEGIN -->
## FLEET COMMON - identical in every repo on this machine. Do not edit here.

################################################################################
#  SUB-AGENT FIRST. THE MAIN SESSION IS THE OPERATOR'S - KEEP IT CLEAR.        #
#  The main session ONLY dispatches (Agent, SendMessage), monitors and         #
#  reports. Every Bash, PowerShell, Read, Edit, Write, Grep, Glob and          #
#  NotebookEdit call runs inside a sub-agent (background by default) - no      #
#  quick-read or one-line-fix exception; the kit PreToolUse hook               #
#  fleet_subagent_first.py denies them in the main thread. Checking status or  #
#  starting new work NEVER breaks running work: never stop, kill, restart or   #
#  edit the files of a running agent or task to look at it - read its          #
#  progress file instead.                                                      #
################################################################################

Source of truth: MAIN's fleet kit. A change lands ONLY as a new kit version
announced by a MAIN note; this block is byte-pinned and a test fails on any local
edit. Tree-specific rules go BELOW this block, never inside it.

1. ACT, DON'T ASK. Operator acceptance of recommendations is ~100 percent. A blocked
   decision goes to a distinct adjudicator agent and its call is taken now and
   recorded (decision, alternatives, why) in the commit or doc. Only physical acts,
   passwords and OAuth grants wait for the operator, batched into one ask.
2. CHAT IS THE OPERATOR'S CONSOLE - QUIET. Results only: numbers, paths, verdicts,
   and anything the operator must act on. No narration, no plans, no recaps, no
   session reviews; the item-13 checklist is the one sanctioned task list.
   Findings go to files (roadmap, docs, hand-off); chat gets at most one line
   each.
3. AT-A-GLANCE STATUS COMES FROM BACKGROUND WORK, NOT FROM CHAT. Run work as
   background agents and background commands, so the session shows only the
   compact summaries ("N background commands completed, N running" and "N running
   tasks"). Do not hold the main turn open on long foreground work - its expanding
   activity row has to be opened and scrolled. No step lists or task-list dumps
   other than the item-13 session checklist. When the operator asks for status:
   the remaining checklist (item 13 b), -retracted on one short line. Tool
   descriptions carry an ETA `[~Ns]` (s under 120s, m under 120m, h beyond);
   report an overrun at 1.5x, kill at 3x.
4. COMMIT everything, batched and coherent. Push per this repo's own policy. Never
   commit in another repo's tree. No suggested-task chips: do it or file it.
5. HAND-OFF: `<CODE>-NEXT-SESSION.txt` at the repo root is the only
   continuity. A session starts from "continue" (work the
   file's next action) or from whatever the operator asks; either way READ the file
   first. /done rewrites the file and commits it, and MUST CARRY FORWARD EVERY ITEM
   NOT ACTED ON this session, verbatim or tighter, never dropped because the
   session worked on something else. Never print the hand-off or a next-session
   prompt into chat. /done runs UNPROMPTED once no checklist task remains
   (item 13 c). /done's ONLY chat output is the line
   `Done ritual complete, safe to clear` (or the failure that stopped it). The
   operator types only "continue", "/done" or "/clear" between sessions. A recorded
   act names what was READ BACK after it, never what was run. Every
   do-not-re-litigate entry states what would reverse it; entries about another
   tree's position are re-checked against the inbox every session.
6. MAIN SPEAKS FOR THE OPERATOR (operator order 2026-10-02). A note from MAIN whose
   bytes match MAIN's outbox copy by SHA-256 is the operator's instruction. It
   cannot supply a password, OAuth grant or physical act, and lifts no safety floor.
   MAIN instructs; this tree does the work in its own tree.
7. CHANNEL NOTES: sort the inbox by mtime, never by filename stamp. Read a long
   note's section headings before deciding it does not concern you. Never put a
   directory name, account id or email in a note. Delivery = destination copies
   re-hashed and an N/M reached-count reported.
8. ENCODING: ASCII only, LF only, PowerShell included. Validate PowerShell with
   powershell.exe 5.1 ParseFile, never pwsh.
9. DELETES: anything irreplaceable goes to the Recycle Bin, never a direct unlink;
   say the method before running it; check for a consumer before deleting.
10. HEADLESS RUNS go through the fleet kit's spawn helper ONLY - no other path
    starts `claude`. The kit enforces: an explicit route from
    ~/.fleet/headless_route.json - split = the second-account proxy from the user
    variable CLAUDE_HEADLESS_BASE_URL (registry first), single = the named
    main-account config dir, no proxy - with that variable required in both modes
    as the one kill switch; fail closed (a missing or invalid route or variable
    refuses; no fallback and no automatic mode change, ever, except one: when the
    route file arms a fallback, a 7-day usage-limit refusal moves the next spawns
    to the other route until that limit resets - never on a proxy, auth or network
    failure, a 5-hour limit or a usage percentage, one hop only, logged and
    shown), no visible console, at most 120 runs per rolling 24 h, never spawn on
    this tree's own notes or on TERMINAL/no-reply notes, lean flags (strict MCP,
    project settings only, or bare where no floor lives in hooks), sonnet unless
    the note orders code changes, effort low for acknowledgements, a usage line
    per run, and the live status file `ops/loop/control/inbox_status.json`.
11. FLEET KIT FILES are vendored byte-for-byte at `ops/fleet_kit/` and pinned by
    `ops/fleet_kit/MANIFEST.json`. Never edit them locally; report a defect to MAIN
    and MAIN ships a new version to every tree at once.
12. LONG WORK REPORTS AS IT GOES. Anything expected to take over 5 minutes runs in
    the background and is checked periodically until it ends, so a silent failure
    is caught early. Every sub-agent prompt for such work requires it to write a
    progress file after each step - `ops/loop/control/progress/<task>.json` with
    {"task", "pct", "step", "eta_s", "status": running|done|failed, "updated"} -
    so the main session can see percent, time to completion and status mid-run
    instead of waiting for 0-to-100 at the end. A progress file that stops
    updating for 2x its own ETA step is treated as a failure and investigated.
    The file lives in the MAIN checkout even when written from a linked
    worktree (resolved via the git common dir; `fleet_headless.write_progress`
    does it), and a worktree-isolated agent's only write outside its worktree
    is its own progress file there.
13. SESSION CHECKLIST (operator order 2026-10-05; it supersedes item 3's
    no-checklist rule for this one purpose). Every session kind: interactive,
    headless lane, loop tick, inbox responder. Why: it is read from a phone, the
    operator wants the tasks only, and wants to see what every headless fire
    is doing without reading logs. Kit helper: `fleet_checklist.py`.
    a. At session start, and every time a lane or loop fires, print
       `Session <n> checklist` (n = this tree's session counter, kept in its
       hand-off file; a headless fire uses its run count), then one line per
       task in execution order: `<box> <ID>: <imperative task, one line>`, plus
       `(<state>, <pct>% ~<rem>m of <total>m [<h:mmAM/PM>])` only while it is
       running (e.g. `builder running, 25% ~22.5m of 30m [2:25PM]`). Why: the
       operator forgets when an estimate was given. rem and total round UP
       to 0.5 min; total is re-estimated as elapsed / pct on each update; the
       bracket is the local finish time, recomputed on every start or update.
       The start time is the item-12 "started" field (optional: a file
       without it keeps `~ETA`). The status line and the agent panel show the
       same. <box> is U+2610. The last line is `<box> /done`. At most ONE
       trailing sentence, and only for an ordering constraint ("X waits until
       Y lands because ..."). NO summary, review, what-went-wrong or history.
    b. After every 4 or more completed tasks, print the REMAINING tasks only,
       newly added ones marked `+` before the ID. Never list completed ones.
    c. When no task remains, run /done automatically, without a prompt.
    d. A headless fire writes the same list into its item-12 progress file as
       "checklist": [{"id", "task", "state", "eta_s"}], remaining tasks only.
       A lane writes `progress/lane-<i>.json` (i = its lane-lock index) in the
       MAIN checkout, never in its worktree, so the lane widget reads one named
       file per live lane and shows the lane name, then its remaining items.
14. INBOX COST (operator order 2026-10-05). It changes COST, never AUTONOMY: the
    inbox is read and acted on AUTOMATICALLY every tick, unattended, with no
    operator prompt, ever. Why: about 60 percent of second-account spend was
    inbox chatter between trees, not build work. Kit helper: `fleet_inbox.py`.
    a. Inbox handling folds into this tree's existing lane / loop tick, which
       reads the inbox on every fire. No separate high-frequency responder
       where a lane loop exists; a tree without one keeps one responder.
    b. Triage first: `fleet_inbox.classify()` (free), then one sonnet run at
       effort low only for what it cannot classify. ACK / INFORMATION /
       TERMINAL / ANSWER notes get a mechanical ack (a ledger line, no note) or
       no reply. Only ORDER / FIX / RULING escalate to a real work lane.
    c. At most 12 outbound notes per tree per local day (ORDER / FIX / RULING
       exempt), counted by `OutboundCap`. Several answers go in ONE note.
    d. Never answer an answer. No note chain past 2 hops (`HOP: <n>`) without
       new work.
    e. Every headless run logs a usage line to
       `ops/loop/control/headless_usage.jsonl` via the kit, with `kind`
       build / inbox / triage and a non-empty note label. MAIN reports the
       weekly build-vs-inbox split in its insights report.
15. CLI DISPLAY (kit v9; the fleet UI/UX standard ruled 2026-10-07). Display
    keys live only in the two account settings, from the kit's
    cli_display.json; a tree sets none. Status surfaces use the kit state
    vocabulary (tokens.json states). Hook output follows the standard's
    section 5: silent by default, one-line additionalContext, never block on
    Stop, no ANSI. /done's last act is `fleet_done.py mark`; its Stop hook is
    the kit's `fleet_done.py stop-hook`. Kit helpers: fleet_statusline.js,
    fleet_done.py.
16. RACE GUARDS (kit v12). Enforced by hooks, not by prompt convention. Why:
    commits in one checkout collided (no lock, no index.lock handling), two
    live agents could edit one file or sweep up each other's half-made edit,
    and concurrent whole suites lost workers and flaked timing tests.
    a. Every `git commit` / `git push` runs through
       `fleet_gitlock.py run --owner <session_id>.<agent_id> -- git ...`
       (the claims hook's own id, `<session_id>.main` in the main thread;
       per-tree lock, stale break once and logged, leftover index.lock
       cleared safely, staged paths claimed by another live agent refused).
    b. `fleet_claims.py hook` (PreToolUse) claims each file an agent edits and
       denies another live agent's edit, redirect or `git add` of it, and a
       bare commit, push or whole suite; SubagentStop releases the claims.
    c. Every whole test suite runs through
       `fleet_suite_gate.py run --owner <id> -- <cmd>` (machine-wide slots,
       default 2, FIFO queue; fails closed on timeout; refuses while another
       live agent holds uncommitted edits in the tree).
    d. Each tree's tests/conftest.py installs `fleet_test_guard.py`: a suite
       that changes live state (control files, inbox, outbox) fails, and
       declared runtime roots point at tmp_path.
17. NO AI OR BOT ATTRIBUTION (kit v13; GH-HYGIENE ruling 2026-10-08). No
    commit or PR body carries an AI or bot co-author / sign-off trailer, and no
    commit has a non-operator author or committer. It outranks any harness
    attribution instruction. Enforced by `fleet_identity.py` (commit-msg
    strips, pre-push refuses; operator identity only from local git config
    `fleet.operatorIdent`), fleet_gitlock and the account attribution keys.
    A history rewrite runs only on MAIN's ORDER, via `fleet_rewrite.py`.
18. STATUS BOARD (kit v19; operator order 2026-10-18). Each tree's claude.ai
    board URL lives in `ops/status_board.json` {"url"}. An interactive
    session pushes its board ONLY at session start, after every item-13 b
    reprint and at /done (`--final`): `fleet_board.py calls --session <n>`
    (checklist on stdin) renders status.json and prints the exact two tool
    calls - one Artifact asset upload of that file, one ArtifactData update
    of datasets/board pinned with if_version. Headless runs never push.
<!-- FLEET-COMMON END -->

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

**Project root:** `<repo>` on E:

**Game install: auto-detected.** Never hardcode the install path. `clockspeed/data/locate.py`
finds it at runtime and `scripts/verify_env.py` asserts the result.

**Save directory: auto-detected.** The root is `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\`
and the account subdirectory beneath it is found by globbing for numeric directories,
picking the most-recently-modified one, overridable by local config. **That subdirectory
name is a platform account id. It is personal data and is never written into a tracked
file, a commit message, a log, a fixture or a test.** The same applies to the world name,
the Windows account name and any absolute path containing a home directory.

**Interpreter:** where its floor is pinned and what asserts it: `docs/OPERATIONS.md`
section 1.2.

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

Every other row lives in `docs/ARCHITECTURE.md` section 6; these two stay because tests
and gates cite them here.

| Path | Does |
|---|---|
| `tools/inbox_watch.py` | Unread `moon_sync_inbox/` items, payloads included. Listing never acknowledges. Wired ONLY in gitignored local settings, so a fresh clone and every worktree run NO watcher - CS-952 |
| `.githooks/pre-commit`, `commit-msg`, `pre-push` | Tier-0 blocking gates. Authoritative; the Claude hooks are a convenience layer |

**A fresh clone runs zero protection until someone wires it** - the bootstrap order, and
the end-to-end proof that a hook fires: `docs/OPERATIONS.md` sections 1 and 1.1.

### 2.3 Output constraints - the transcript is a cost, not a scratchpad

**Keep each chat response under roughly 500 output tokens.** Break long work across turns,
or write verbose output to a file. Operator directive, 2026-09-06.

- Speak to ask for a ruling, to notify, or to answer a direct question. Otherwise act.
- No narration between tool calls, and never restate what a tool just printed.
- Put the step description in the tool call's own `description` field - it renders as the
  visible label and costs nothing in the response body.
- Long findings go to a file, a ledger entry or an item note, never into chat.
- **Do NOT poll a background task in a loop of one-line turns.** Each poll is a whole turn.
  Wait for the completion notification.

Why: `docs/history_notes.md`, "From section 2.3".

### 2.3.1 The session checklist, and caveman-ultra as the default - filed 2026-10-02 by operator directive

**Every session is caveman-ultra.** The main session stays CLEAR for operator use: prose
terse AND detailed, never restating a tool's output, and every action, tool call and
dispatch carries an EXPECTED DURATION in its label - the panel shows elapsed only.

**THE CHECKLIST IS THE STATUS FORMAT, NOT PROSE - FLEET item 13 states it whole.** This
tree adds: plan it from the hand-off and the roadmap before any work; `<box>` is U+2610,
and tracked files name it by that text, never the glyph (section 3 rule 4). Section 6.1
owns adjudicate-do-not-ask and commit-and-push; keep the remaining context in mind when
planning `/done`.

**Here:** the counter, its kit helper and the board pushes (FLEET item 18):
`docs/OPERATIONS.md` section 12.4.

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

Owned here, with no `BOOTSTRAP.md` source - filed for CS-814, the same echo rule one
domain over:

13. The environment every hook inherits carries live credentials, so any path that
    renders it leaks them. No hook, gate, test assertion or error path echoes an
    environment value - name a variable, never its value. Debug dumps, `env` and
    `set -x` traces, exception context and assertion rendering all count as echo paths.

Rule 4 has a mechanism, not just a preference behind it: `CONVENTIONS.md` section 10.

---

## 4. Doc topology - which file owns which fact

Every fact has exactly ONE owner file. Other files link to it; they never restate it. A
restated fact is a fact that will drift. This table is the anti-drift control.

| File | Owns | Never contains |
|---|---|---|
| `CLAUDE.md` | Rules, hard constraints, frozen list, settled decisions, paths, topology | Per-item history, counts, ledger entries |
| `README.md` | Outsiders: what it is, quickstart, first result | Internal process, roadmap, session notes |
| `ROADMAP.md` | OPEN work only - the item LINE alone: its ID, a short headline, the `acceptance: in detail` pointer and the tier | Completed work, aspirational ideas, NOTE bodies, any PART of an acceptance clause |
| `docs/item_notes.md` | The INDEX over `docs/item_notes/` - the leaf membership rule plus the rules every leaf obeys | Any item body, item lines, a per-item routing row, completion records, history |
| `docs/item_notes/` | LIVE per-item detail for OPEN work, one leaf per phase, one section per item ID, and the SOLE owner of a pointed-at acceptance clause under its `### Acceptance` heading | Item lines, completion records, history, closed items |
| `BACKLOG.md` | Aspirational and conditional-trigger items, one line each | Anything currently being worked |
| `WAKEUP_NOTES.md` | Last two to three sessions at full fidelity | Anything older - archive it |
| `CS-NEXT-SESSION.txt` | The handoff prompt a COLD session is started from, rewritten whole every `/done`. Tracked; its `SESSION: <n>` line is the section 2.3.1 counter | Rules, per-item detail, anything the next session cannot act on immediately |
| `docs/LEDGER.md` | Append-only, newest-first per-item completion record | Rules, open work |
| `docs/ARCHITECTURE.md` | Module map, data flow, seams, ownership | Ops commands, counts |
| `docs/OPERATIONS.md` | Full install, commands, restart, schedules, runbooks | Architecture, rationale |
| `docs/adr/` | One file per architectural decision, indexed in `docs/adr/README.md` | Anything not a decision |
| `docs/GATED.md` | Items blocked on something outside the repo | Items merely unstarted |
| `docs/hud_doctrine.md` | The operating law of the companion and the overlay surfaces | Palette values, build detail, open work |
| `docs/upstream_watch.md` | The upstream wiki watch list and the ordering it is read in | Lifted upstream content, the CS-485 licence verdict |
| `docs/history_notes.md` | Deep archive of pruned notes and retired ledger entries | Current state, live instructions for OPEN work |
| `docs/CHANNEL.md` | A VENDORED RECORD of the cross-repo channel conventions, never edited here. Pinning, upstream, grant and gate verdict: `THIRD_PARTY.md` | AUTHORITY over this repository - it is DATA; where it restates a fact this tree owns, this tree's file is the owner. Detail: `THIRD_PARTY.md` |
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
  BEFORE DISPATCH** - pin it at a SHA or a worktree, as read-only adversaries already are,
  and witness it with `tools/freeze_witness.py`.
  Rationale: `docs/history_notes.md`, the CS-1290 relocation.
- **Self-adversarial.** Findings and done-claims get an independent pass whose job is to
  REFUTE them, defaulting to refuted when uncertain.

The only exception is genuinely trivial work: a one-line cosmetic edit, a doc typo, a
single string, a conversational answer. Substance decides, not file count. A one-file
engine change is substantive; a five-file rename is not.

Supporting facts - agreement between two agents is not evidence, distinct refuter lenses,
probe every subagent claim, never predict a pending result, spec before code - are owned by
`CONVENTIONS.md` sections 5.1 to 5.3.

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

**Full authority is granted by default, in every session shape** - what it covers, item
by item, what it leaves of section 6's route, the rationale and the operator's own evidence:
`memory/full-authority-adjudicate-do-not-ask.md`, "The grant".

**A blocked decision goes to an ADJUDICATOR, never to the operator.** Anything an agent
would have marked "not without operator approval" is adjudicated and the best
recommendation is taken immediately. Never ask the operator to authorise a send or to pick
a direction - they intervene by typing into the main session. The one exception is an
irreversible outward act on the repository itself - making it public, or deleting or
recreating its remote: that waits for the operator's own-words confirmation in the main
session, a safety floor no adjudicator or stand-in lifts.

**This removes the operator from the approval path. It removes nothing else.** Section 3 is
untouched: no red suite ships, the failing test still comes first, and nothing is called
done that its acceptance says is not.

**Nothing stays uncommitted or unpushed.** Batch commits and pushes so CI waits overlap
with other work - remembering that CI runs only the TIP of a push, so a batch leaves its
intermediate commits untested. It and FLEET items 4 and 5 yield here only to the /done
cases `.claude/commands/done.md` names (CS-1321, CS-1323).

**A status request is answered with the section 2.3.1 checklist**, not prose.

**MAIN SPEAKS FOR THE OPERATOR (FLEET item 6), granted here 2026-10-02.** Safety floors
MAIN cannot lift include section 3, the outbound leak gate, and the repository-public/remote
exception above. The grant and the provenance check: `docs/OPERATIONS.md` section 12.1.

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
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Never write to the game install or a save file.** An invariant, not a preference.
  *Do not re-pitch:* an opt-in write mode, a backup-then-write, an in-place save edit, a
  "safe" patcher, or writing anything at all into the save directory.
  *Reversed by:* nothing - it is section 3's first non-negotiable, a floor no adjudicator
  and no MAIN note lifts.
- **Name is Clockspeed, root is `<repo>` on E: (ADR 0026).** *Do not re-pitch:* a rename
  or a relocation of the root.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Repo is private first, public later.** Hygiene is enforced from the first commit
  anyway. *Do not re-pitch:* deferring hygiene work on the grounds that the repo is
  private.
  *Reversed by:* nothing reverses the hygiene half; going public is the planned second
  half and waits for the operator's own words in the main session (section 6.1).
- **Python core.** Node exists solely for the Electron shell. *Do not re-pitch:* a rewrite
  in another language, or moving core logic into the Node side.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Three explain tiers: headline, one-line reason, full derivation.** *Do not re-pitch:*
  collapsing to two, or adding a fourth.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Persistence is per-world ledger PLUS global per-rule mute.** Both layers. *Do not
  re-pitch:* dropping either one, or merging them into a single store.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **All four advice domains ship in v1** - node siting and claim order, onsite processing
  versus transport and by what method, milestone gap against any target, and power and
  fuel planning. *Do not re-pitch:* cutting a domain to a later version.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Milestone target is a free selector.** *Do not re-pitch:* a fixed pointer at the next
  milestone. Selecting a target several tiers out and getting a redesign plan is required
  capability, not a stretch goal.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Companion window in v1; the in-game overlay is a later flagged mode of the same
  shell**, default off, degrading to the companion on bind failure. *Do not re-pitch:*
  building the overlay first, making it the default, or treating it as a separate app.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Mods: architecture now, content later.** Namespaced identifiers, unknown classes
  tolerated, unmodeled content flagged, feature-flag registry from phase 0. *Do not
  re-pitch:* opening mod content work before phase 6 completes.
  *Reversed by:* phase 6 completing opens mod content work; the architecture half only by
  the operator's own words in the main session (section 6.1 - no adjudicator and no MAIN
  note stands in), then recorded as an ADR in `docs/adr/`.
- **Dedicated Server API is out of scope for v1.** The docs are on disk and free to read,
  but single-player saves are the world-state source. *Do not re-pitch:* it as a
  world-state source. Revisit only if the operator starts running a dedicated server.
  *Reversed by:* once the operator runs a dedicated server, only the operator's own words
  in the main session (section 6.1 - no adjudicator and no MAIN note stands in), then
  recorded as an ADR in `docs/adr/`.
- **No external optimizer dependency in phase 3.** Interface first, dependency later and
  gated. *Do not re-pitch:* an LP or ILP library before `OptimizerBackend` exists, before
  it slots behind the interface without changing a caller, and before the `CONVENTIONS.md`
  section 14 license gate passes.
  *Reversed by:* all three conditions above met, with a CLEARED gate row in
  `THIRD_PARTY.md`.
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
  *Reversed by:* a named source whose licence CLEARS the `CONVENTIONS.md` section 14
  gate in `THIRD_PARTY.md`, plus only the operator's own words in the main session (section
  6.1 - no adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/` -
  never the CC BY-NC-SA wiki under `LICENSE`.
- **The reference world is the operator-pinned development world** - vanilla, no creative
  mode, no modifiers, onboarding active - snapshotted into a gitignored corpus as it
  grows. *Do not re-pitch:* switching reference worlds without recording why. Its name
  stays out of every tracked file; refer to it as the pinned development world.
  *Reversed by:* a re-pin in only the operator's own words in the main session (section
  6.1 - no adjudicator and no MAIN note stands in), then recorded with its reason in
  `docs/LEDGER.md`.
- **The advice ledger is keyed by the save header's world token**, not by filename and not
  by world name. *Do not re-pitch:* filename or world-name keying - filenames change on
  every save and autosaves rotate. The ledger tolerates a token it has never seen by
  treating it as a new world rather than failing.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Test fixtures are small synthetic registries hand-authored in the repo**, never slices
  of real game data. *Do not re-pitch:* checking in a trimmed real docs file or a trimmed
  real save "just for tests". The rule suite must run on a machine with no game installed.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in), then recorded as an ADR in `docs/adr/`.
- **Product before process - filed 2026-10-03 by operator directive.** Measured over
  2026-09-19..10-03: of 371 commits, 8 touched `clockspeed/` or `shell/`. No NEW tooling,
  guard, CI, citation or provenance item is opened unless it blocks a product item or
  turns a suite red; such findings go to `BACKLOG.md`. The next work is CS-400, then the
  Phase 5 advisor. An adversary loop on low-risk hardening stops by cost against risk and
  records the residual. *Do not re-pitch:* a new guard as the session's main work.
  *Reversed by:* only the operator's own words in the main session (section 6.1 - no
  adjudicator and no MAIN note stands in).

Anything settled by an ADR is recorded in `docs/adr/` and indexed there; this list holds
the decisions that predate the first commit.

---

## 8. When a spike contradicts the spec

Ground truth beats every document, including this one. If a probe or a spike result
contradicts `BOOTSTRAP.md`, the probe wins - what to update, record and report: that file's
closing paragraph, the end of its section 13.
