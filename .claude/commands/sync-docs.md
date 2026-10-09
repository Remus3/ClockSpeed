---
description: Reconcile every markdown doc against the canonical fact set - one owner per fact, no restated numbers, closed items relocated, budgets enforced.
argument-hint: [scope, e.g. all | docs/ | ROADMAP.md]
---

# /sync-docs

## WHO RUNS THIS - ONE SUB-AGENT, NEVER THE MAIN SESSION

FLEET-KIT v10, carried at v11 (MAIN's 2026-10-08 08:39 ORDER, item 4; the FLEET-COMMON banner; CS-1282, CS-1287):
the main session does NOT run these steps. It dispatches the WHOLE of this command -
every step below, with this file's text and the arguments as the prompt - to ONE
sub-agent (the Agent tool, in the background by default), waits for that sub-agent's
completion notification, and relays ONLY its final line, the command's one-line result,
to chat. The sub-agent runs every step itself and never re-dispatches the whole command.
The kit's PreToolUse hook `ops/fleet_kit/fleet_subagent_first.py` denies Bash,
PowerShell, Read, Edit, Write, Grep, Glob and NotebookEdit in the main thread once its
mode is deny, so a step run there stops at its first tool call.

Scope: $ARGUMENTS (default: every tracked markdown file)

Every fact has exactly ONE owner file. Other files LINK to it; they never restate it. **A
restated fact is a fact that will drift.**

## 1. Establish the CANONICAL fact set FIRST - from the artifact, never from another doc

- [ ] Read facts from ground truth only: the code, `git log`, `config/ports.json`, a live
      suite run, `python tools/facts_probe.py`, the tracked build-string and content-hash pin.
- [ ] PRINT the fact set. Every later edit cites a line of it.
- [ ] **Two docs agreeing is not evidence** - they may both have copied the same stale
      number. Only the artifact settles it.
- [ ] Re-derive every count you are about to write. A filed count is a hypothesis, not a fact.

## 2. Sweep and map ownership

For every fact found in every markdown file, record: the fact, the file it is in, and the
file that OWNS it.

| Owner | Owns | Never contains |
|---|---|---|
| `CLAUDE.md` | Rules, hard constraints, frozen list, `Settled`, paths, topology | Per-item history, counts, ledger entries |
| `README.md` | Outsider-facing: what it is, install, run, first result | Internal process, roadmap, session notes |
| `ROADMAP.md` | OPEN work only, with IDs and acceptance criteria | Completed work, aspirational ideas |
| `BACKLOG.md` | Aspirational and conditional-trigger items, one line each | Anything being worked |
| `docs/LEDGER.md` | Append-only, newest-first completion record | Rules, open work |
| `docs/ARCHITECTURE.md` | Module map, data flow, seams, ownership | Ops commands, counts |
| `docs/OPERATIONS.md` | Commands, restart, scheduled tasks, runbooks | Architecture, rationale |
| `docs/adr/` | One decision per file, indexed in `docs/adr/README.md` | Anything not a decision |
| `docs/GATED.md` | Items blocked OUTSIDE the repo, plus the exact unblocking condition | Items merely unstarted |
| `WAKEUP_NOTES.md` | Last 2-3 sessions at full fidelity | Anything older |
| `docs/history_notes.md` | Deep archive of pruned notes and old ledger items | Current state |
| `memory/` | Durable cross-session facts | State derivable from code |

## 3. Fix the drift

- [ ] A fact in a NON-OWNER file becomes a link to the owner. Never a copy.
- [ ] **Delete or generate every restated measured number.** Counts - tests, coverage,
      versions, item totals, file sizes - live in exactly one machine-checked place with a
      drift guard. **A hardcoded count in a doc is a lie with a timestamp on it.** If a doc
      must display one, GENERATE it.
- [ ] Closed items move from `ROADMAP.md` to `docs/LEDGER.md`.
- [ ] Items blocked on an EXTERNAL condition move to `docs/GATED.md` with the exact condition
      that unblocks them. Merely unstarted stays in `ROADMAP.md`. **Never close a gated item
      synthetically** - split it into a DRAIN half and a PREP half instead.
- [ ] Notes older than the last 2-3 sessions move to `docs/history_notes.md`.
- [ ] Narrative in an index file collapses to one line plus a pointer to its own file. Ban
      narrative in `ROADMAP.md`, `BACKLOG.md`, `docs/GATED.md` and `docs/LEDGER.md` - they
      are indexes, and an index that reads like an essay stops being scanned.
- [ ] A `Settled` entry states what was decided AND what specifically not to re-pitch. An
      entry recording only the conclusion invites someone to rebuild the argument. Record
      the fence.
- [ ] A heading whose DATE LEADS it marks its own section historical: do not audit it as
      current, do not update it. A date sitting AFTER a provenance verb records only when
      the text was filed, moved or measured - that section is LIVE content and is audited
      normally. Do not skip a section merely because its heading carries a date. The file
      header declares which kind it holds; `CLAUDE.md` section 4 owns the rule.
- [ ] Dated artifacts live in `docs/_archive/` and are excluded from ripgrep via `.rgignore`
      so they never pollute a search for current truth.

## 4. PII and character-set sweep

- [ ] Grep every tracked file for: the Windows account name, a numeric platform account id,
      a world name, a machine name, any absolute path under a user home directory, and any
      hardcoded interpreter path. Replace with the auto-detection wording and `python`.
- [ ] Assert 7-bit ASCII across every authored file. No em-dash, no en-dash, no smart quotes.
- [ ] Confirm no save file, no game data and no extracted asset is referenced as a tracked
      fixture.

## 5. Budgets - relocate, do not delete

- [ ] `CLAUDE.md` and every auto-loaded file under 40 KB - HARD fail.
- [ ] `memory/MEMORY.md` under 20 KB - HARD fail.
- [ ] Any `memory/*.md` leaf under 6 KB - warn.
- [ ] `ROADMAP.md` under 60 KB - warn, triggers a relocate pass.
- [ ] Over budget: move detail to `INDEX_<domain>.md` or an archive file and leave a one-line
      pointer. The top index keeps one line per domain plus the handful of entries too costly
      to ever miss.

## 6. Memory layer

- [ ] Every memory file is reachable from `memory/MEMORY.md` or an `INDEX_<domain>.md`. **Do
      not unindex a file to save bytes.**
- [ ] Frontmatter present and correct: `name`, `description`, `metadata.type` of
      `user` / `feedback` / `project` / `reference`.
- [ ] `feedback` and `project` entries carry **Why:** and **How to apply:** lines. A rule
      without its why gets re-litigated.
- [ ] Relative dates converted to ABSOLUTE dates.
- [ ] Delete memories that turned out to be wrong. Update rather than duplicate.
- [ ] Do not save what the repo already records - code structure, past fixes, git history,
      content already in `CLAUDE.md`.
- [ ] Re-run `python tools/memory_sync.py`. The markdown is the SOURCE; the store is a MIRROR.
      **Never fix a fact only in the mirror.** A "healthy" store status is NOT proof recall
      works - only `embedded == active` proves coverage.

## 7. Verify and report

- [ ] `python tools/drift_guard.py` and `python tools/doc_budget.py` - record both exit codes.
- [ ] Confirm all doc cross-references resolve; no orphaned or stale markdown.
- [ ] Report: the canonical fact set and its sources; every drift found as
      fact / wrong file / owner / action; every conflict left UNRESOLVED and flagged in
      place; every PII finding; both exit codes observed THIS run.
