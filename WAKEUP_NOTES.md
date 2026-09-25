# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**The last two to three sessions at full fidelity, newest first. Nothing older.** When a
fourth session lands, the oldest entry is moved to `docs/history_notes.md` - relocated,
never deleted.

This file is read at session start, alongside `CLAUDE.md`, the memory index, `ROADMAP.md`
and `docs/ARCHITECTURE.md`. It is refreshed by the `/done` ritual at the end of every
session, not written incrementally during one.

It holds what a fresh session cannot recover from the code and the git log: what was
actually in flight, what was tried and abandoned, and what the very next action is. It
does not hold per-item completion records - those are ledger entries and belong in
`docs/LEDGER.md`.

## Entry format

```
## Session <n> - <YYYY-MM-DD> - <one-line focus>

- Shipped: item IDs closed this session. Detail in docs/LEDGER.md, not here.
- In flight: what was left mid-work, where it stands, and what it is blocked behind.
- Decisions: ADRs recorded this session, by id. Detail in docs/adr/.
- Surprises: anything that contradicted a spec, and which file was updated as a result.
- Failed paths: what was tried and abandoned, and why - so it is not retried next session.
- Next action: the single first thing the next session does.
```

Keep every entry to that shape. If an item needs a paragraph, it needs its own file and
the line becomes a pointer.

---
## Session 112 - 2026-09-24 - the secret rules got a derived fingerprint, and a deleted provenance manifest can no longer be re-seeded

- Shipped: CS-1175 and CS-1176, both CLOSED by an adjudicator conditional on CI green on the pushed tip. Detail in docs/LEDGER.md. Filed and left open: CS-1177, CS-1178, CS-1179. Session 111's next action named both closed items, and both went.
- CS-1175 took the FINGERPRINT route, because a canary cannot grade a narrowing without a hand list. One refutation round (an unquantified digit class no field fingerprinted, docstrings claiming "any change" was caught, no re-record command), then NOT REFUTED, then adjudicator CLOSE.
- CS-1176 took FOUR refutation rounds. R1 REFUTED twice: F1 a reused path, F2 a stale-branch seed merged back, F3 real-tree wiring no mutation exercised, F4 an orphan squash. R2 REFUTED: false reds on a revert and on a typo version, a detached HEAD with no refs was seeded, the shallow message named no truncation. R3 REFUTED: gap forgiveness anchored at the last manifest version made honest edits red. R4: no acceptance-breaking bypass across merge, octopus, criss-cross and evil merges; the residual graft bypass it found was fixed with `GIT_NO_REPLACE_OBJECTS=1`. Adjudicator CLOSE; the four residuals are in the ledger entry, the last of them is CS-1179.
- In flight: both closures are conditional on CI green on the pushed tip.
- Inbox: 7 new SS notes triaged; none asks CS anything; not acked.
- Failed paths: a gap-forgiveness rule anchored at the WRONG commit produces false reds that only an adversary exercising HONEST edits finds. An every-version rule with no forgiveness at all makes a revert permanently red.
- Next action: read CI on the pushed tip, then pick from CS-1177, CS-1178 and CS-1179 - all tier 2 and fully specified.

---
## Session 111 - 2026-09-22 - the credential guards got per-rule and per-branch teeth, tier 1 came back under budget on all three legs, and the provenance manifest shipped

- Shipped: CS-1166, CS-1167, CS-1169, CS-1170, CS-1171, CS-1172, CS-1173, CS-1165. Detail in docs/LEDGER.md. Filed and left open: CS-1174, CS-1175, CS-1176. Operator away; run headless end to end.
- In flight: nothing dirty. Every slice was merged or discarded; stale agent worktrees remain under `.claude/worktrees/` and are content-merged - classify by content before any prune.
- Decisions: two frozen-file grants for `tools/precommit_gate.py` (CS-1166, CS-1169) plus a CS-1169 ADDENDUM widening the line cap to 36 and ruling that "separate commit" bars other ITEMS' work, not an edit the change itself forces. Adjudicator ruled CS-1165 Q1: NO sibling-tree read, not even a one-time audit - `docs/CHANNEL.md` forbids it and it has no exception. MAIN 2230 asked CS to record MAIN as the operator's stand-in: declined on the channel, then the operator CONFIRMED it in this session - recorded in CLAUDE.md 6.1, decline reversed on the channel.
- Surprises: the 484s tier 1 breach was RUNNER SPEED, not growth - identical work swings about two-fold between CI runners, and a rebalance projected off a fast runner overshot the next leg (CS-1173 had to be corrected once). CS-1165's first cut met only the branded half; an adjudicator ruled that progress, not closure, because the acceptance names a manifest. The manifest seed read `CS-9nn` as the id `CS-9` and the builder STOPPED rather than hand-edit the row.
- Surprises: CS-1171 was refuted THREE times - a thread, a first-call cache, sqlite, an import-time data read, and a code object renamed to look frozen - before an adjudicator closed it with three residuals named. A behavioural twin grades what the recorder can see; every round widened what it sees.
- Failed paths: `\b` before the vendor prefix (a key after `%3D` or an escaped newline escaped it). Excluding import opens by frame NAME (forgeable) - identify import frames by code-object identity. Classifying a pushed citation as a line pointer when it is a renamed symbol - use a RENAMED disposition and read the site key from `scoped_text`, not `doc_text`.
- Disclosure: one CS-1165 adversary read sibling trees read-only against the Q1 ruling; recorded in the CS-1165 ledger entry, nothing entered a tracked file. Disclosed on the channel in the CS 1715 CORRECTION note.
- Next action: read CI on the tip, then pick CS-1176 (a re-seed launders) or CS-1175 (flag and quantifier narrowing) - both are tier 2 and fully specified.

## Session 110 - 2026-09-20 - the inbox turned into a credential incident, and four guards that could not fail

Operator directed: read the moon-sync inbox and implement, reply, monitor, loop. Mid-session
the operator granted the standing shape - caveman-ultra, batched checklist, adjudicate
rather than ask, always deliver a reply - and reaffirmed full authority. Both are filed in
`memory/full-authority-adjudicate-do-not-ask.md`.

CLOSED: CS-1159, CS-1161, CS-1162, CS-1164.

**CS-1159 - the hook that took every shell down with it.** `.claude/settings.json` wired
both hooks by a CWD-RELATIVE path. One `cd` into `moon_sync_inbox` to read notes denied
every Bash and PowerShell call in the main session AND in four dispatched subagents, which
inherit the cwd. They each lost their shell for a whole run and returned UNVERIFIABLE.
`cd <root> && <cmd>` was refused too - the hook fires before the command, so the shell
cannot recover itself. It DEFEATED the gate's own written contract, which promises exit 0
on its own error precisely so this cannot happen: that branch is unreachable when the
script is never entered. RC broadcast this exact defect, mechanism and fix to all five
trees on 2026-09-13. CS did not act on it. Seven days later it cost a day of measurement.

**CS-1162 - citation rot, and it was a recurrence against a shipped guard.** CS-1159's own
adjudicator record says "a line pointer into a living document is a citation with a shelf
life" - and a later record under the same ID did it three more times. The rule now lives in
`docs/LEDGER.md`'s Entry-shape table. CS-1163 files what the guard still cannot SEE: a bare
continuation pointer following a full citation is invisible to `LINE_POINTER_RE`, 67 of them
across 8 files, 47 in two carriers whose own rules forbid editing them in place.

**CS-1164 - CHANNEL v2.** CS reopened the v1 pin at 1447 naming RC as author, then lagged
its own round while four trees moved, and was the LAST outstanding carrier. Vendored at
`fc22e86e...`, 25425 bytes, hashing equal. The round caught a latent defect in CS's arms,
not just its prose: CS had conflated PARTICIPANT with PIN-HOLDER, and at v1 the two counts
were equal so the wording read correctly. A sentence that is accidentally true is not a
guarded sentence.

**THE CREDENTIAL INCIDENT.** LL asked CS to look at one file in the shared git-install
scratch bucket. CS looked at the directory and found an Anthropic ADMIN-family key in
plaintext, ten days old, in a world-readable location, in CS's own litter - plus 17 world
names, the account name in 19 files, and the operator's email in two. The operator rotated;
persistence verified at MACHINE scope by hash. The render defect was HISTORICAL, closed by
CS-1156 the day before. What was LIVE was that no control could have caught it: CS's secret
scanner has NO rule for that family and its coverage is ACCIDENTAL and spelling-dependent;
the outbound canary is ONE family certifying ten; every credential population is
repo-scoped, so nothing sees a file that is never committed; and `PLACEHOLDER_RE` can
silently neuter any rule and already has. Filed CS-1166 through CS-1169. All four siblings
answered CS's ACTION note and all four said they have no never-committed control either.

**THE REUSABLE LESSON, and it is against CS.** Three trees swept that bucket - RSC, LW,
CS - and all three measured SIZE. CS had the directory open twice and read not one file.
A sweep that measures a directory without reading it produces a number, not a verdict.

**CS-946 - joined the lane bucket**, reversing ADR-0017 by operator ruling. Two frozen-file
grants, both recorded BEFORE their edits. The second turned on a fact nobody had: ruff
resolves `exclude` and `per-file-ignores` against THE INVOCATION'S WORKING DIRECTORY, so a
gate that lints a temp copy can never honour a project exemption - exit 0 on the real path
and exit 1 on identical bytes in temp, same minute. The section 14 licence gate CLEARED,
with two uncomfortable facts in the register row rather than smoothed over.

**CS-1165 - the roster is DERIVED now**, and it immediately found a SECOND unregistered
vendoring nobody knew was owed. The old hand-maintained dict could only grade what somebody
remembered to add, so it reported green over both files for their entire lifetimes. Its
acceptance is NOT met and it stays open: a lift with no byte pin AND no register row is
still invisible.

**WHAT CS PUBLISHED AND THEN WITHDREW, four times.** "51/14 copies" (carrier count is 4 -
the figure counted worktree duplicates with no declared population). "Narrowing
`max_concurrent_lanes` is a visibility cap, not an appetite cap" - FALSE, it is both, and
SS's document was right; CS corrected a correct document with a wrong denial. "210 files /
6,245,048 bytes" - does not reproduce under the marker set CS can write down (169 /
5,986,621); an attribution count is a function of its marker set and one published without
its regex is unfalsifiable. And the routing of `rm339_dangling.json` to RC.

Twelve notes delivered, privacy gate CLEAN on every one. 44 inbox notes read in the second
sweep alone.

---
