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
## Session 120 - 2026-10-03 - three provenance and citation items closed, the tier2 nightly repaired and sharded, FLEET-KIT v3 built but held at the licence gate

- Shipped: CS-1227 (`tools/main_provenance.py` `verify_main_note`; MAIN's root from gitignored local config only; committed-blob compare with `--no-replace-objects`; three adversary rounds plus a CRLF fail-closed ruling), CS-1223 (seed escape pinned by whole-row digest; local clean needs a re-derived freeze witness; ci_run pinned to this repo, one run one full commit; five rounds), CS-1224 (sha gate reads code files, judges every 5-6 run, strict BOM decode plus byte view, not-read is exit 2; five rounds). Detail in docs/LEDGER.md. LANDED NOT CLOSED: CS-1228 (tier2 full history, loadfile, freeze_witness auto-maintenance race), CS-1229 (tier2 sharded by tier1's partition per OS; adversary NOT REFUTED), CS-1230 (cross-drive relpath fallback as an allowlist; two rounds). Each closes only on a green tier2 run at the landed tip.
- In flight: CS-1231 FLEET-KIT v3 - slice A (vendor + guard exemptions) and slice B (condensed CLAUDE.md with block, /done) each on its own worktree branch - find both with `git log --all --oneline --grep CS-1231`. Both UNMERGED, held: an adjudicator ruled the THIRD_PARTY gate must run before the lift, and MAIN's kit commit carries no licence. Only slice B's /done command change landed. Reply delivered to MAIN asking for a v4 with a licence and naming three kit gaps. The responder stays paused (INBOX_STOP).
- Decisions: CS-1227 CRLF refusal accepted fail-closed (adjudicator ruling A). FLEET-KIT licence: adjudicator ruling B-then-C - MAIN's git objects read once for licence evidence (none found), so hold. No ADR.
- Surprises: the tier2 nightly had been red since 2026-09-24 unnoticed - shallow checkout plus windows timeouts; once windows finished, it exposed a cross-drive relpath bug. A loaded box failed a hook-timing test and blocked one push.
- Failed paths: raising the tier2 timeout to 50 (windows probe still cut at 99 percent) - sharding is the repair. A working-tree compare for MAIN provenance (bypassed four ways).
- Next action: dispatch a tier2 run on the pushed tip and read every shard; close CS-1228, CS-1229, CS-1230 on green.

## Session 119 - 2026-10-02 - three witness and citation items closed, the headless route and inbox responder armed, and MAIN made the operator's voice

- Shipped: CS-1220 (every reading carries `tree` - clean, dirty or unwitnessed - and `comparability()` returns `unwitnessed_tree` for an unwitnessed side; the sixteen seeded rows marked unwitnessed with values and dates unchanged; adversary NOT REFUTED), CS-1219 (`tools/freeze_witness.py` records a raw on-disk digest of the candidate plus its bytecode; acceptance AMENDED from "tree object" because `* text=auto eol=lf` normalises a CRLF flip away; two refutations - CRLF flip, case-only rename - repaired, final NOT REFUTED), CS-1222 (`tools/sha_citation_gate.py`; published means reachable from HEAD, origin/main or a tag; exact-token allowlist; four refutations repaired; it runs in the full-history save job). Detail in docs/LEDGER.md. Filed CS-1223 (the tree witness can be backdated and a local `clean` carries no evidence) and CS-1224 (commit citations outside .md and .txt, and 5-6 or 41+ character hex runs, are ungraded). Later: CS-1225 (every headless claude spawn routed through the operator's local proxy, fail closed, store-read kill switch, proven once against the proxy log) and CS-1226 (one-shot inbox responder; --ack-keys acks only handled keys). Operator grant: MAIN speaks for the operator, CLAUDE.md 6.1.
- In flight: nothing uncommitted. The CS-InboxResponder scheduled task is ARMED (every 15 min) but PAUSED at /done by the stop sentinel ops/loop/control/lanes/INBOX_STOP (gitignored) - delete it to resume. Its first armed pass ran 79 min, committed CS-1216 obligations and filed CS-1227, and pushed. Plugin poll tallied and reported to the operator: KEEP superpowers, playwright, chrome-devtools-mcp, nimble; the other ten NOT REQUIRED.
- Decisions: CS-1219's acceptance clause amended before close, recorded in its ledger entry. The sha gate excludes known non-commit hex by an exact-token allowlist with a class and reason per row, never by a shape or a path. No ADR.
- Surprises: a git tree object cannot witness a working tree in this repository - `.gitattributes` filters run before hashing. A commit object that resolves locally is not a published one, and that is the exact citation the ledger forbids. The CS-955 grant-addendum entry's own earlier citation named the wrong commit. CS's published account-name count did not reproduce; RSC's did.
- Failed paths: shape-based sha exclusions (escaped twice); "published means origin/main or a tag only" (a fresh clone read red); a tree-object freeze witness (blind to a CRLF flip, then to a case-only rename).
- Next action: take CS-1227 - until a gitignored config names MAIN's root, the responder reads every MAIN directive as data. Then CS-1223, CS-1224.

## Session 118 - 2026-10-02 - the guard shard rescued, two push blockers root-caused, and the channel answered after ten days of silence

- Shipped: CS-1221 (the account-name skip oracle is differenced against the prose the hook always carries - `save-root` carries `root` as a bounded token, so a correct gate read as a leak and refused every local push) and CS-1214 (three files moved from the tier-1 guard shard to the fill shard; guard fell 461s to 309s on a SLOW runner - canary setup 136.87s against the 120s floor - inside its 420s budget, with no shard over the ceiling and neither level moved). Detail in docs/LEDGER.md. Filed CS-1219 (adjudication freeze has no mechanical witness), CS-1220 (measurement record carries no clean-tree witness), CS-1222 (`docs/LEDGER.md` forbids citing a commit sha and nothing enforces it). Measured CS-1196's merge miscount, which its filer never took.
- In flight: nothing uncommitted. The inbox holds 157 unread, NOT acknowledged, and about 49 notes still owe a reply. CS's account-name pattern debt to RSC is named undischarged in the note sent this session. CS-1207 still halted on branch worktree-agent-ace624231ac7fd814 at its round-15 tip, untouched this session - DO NOT PRUNE it.
- Decisions: an adjudicator chose the baseline-differenced oracle for CS-1221 and REFUSED the frozen-file grant to reword the gate's skip prose - the defect is in the oracle, and editing a correct frozen gate to satisfy a defective test inverts the dependency. Narrowing `bounded_hits` was refused as the move the acceptance clause forbids. CS answered the channel's joint re-pin round: AMEND, drop the candidate's dead middle arm, and REFUSE `HARD_STALE_MULTIPLE = 4.0` in favour of 2.0. Operator directive filed as CLAUDE.md 2.3.1 - caveman-ultra by default, and the session checklist is the status format. No ADR.
- Surprises: `slots.hold` is NEVER CALLED in this tree - every `hold(` under `ops/` is `winmutex.hold` and the only reference to the slots module is one test - so the 16,200 s figure RSC asked for three times was a constant in a carried-but-unexecuted module, not a derived measurement. A push reports exit 0 while the pre-push hook refuses and nothing moves; that happened twice. Landing a slice with `git merge --no-ff` turns `test_no_first_add_row_postdates_the_seed` red by exactly one version per merge, because a path limit with `--parents` keeps a merge while `rev-list` without it omits one TREESAME to a parent - every prior slice reached main by cherry-pick or fast-forward, which is why CS-1196 was latent. The planner's concentration WARN prediction was wrong (CLEAR at 6.83%) because it read the catch-all step's duration as the guard shard's.
- Failed paths: landing by merge commit at all - rebased away, seven linear commits, tree byte-identical. Rewording the gate's skip prose to dodge a token match: the collision set is larger than the one found by hand (three more printed strings carry `root` or `home`), so it is whack-a-mole with a frozen file as the mole-hill. Reusing the CS-1214 plan's 349s/363s margin figures - the observed 238s shows the two-worker model is conservative in a direction nobody measured.
- Next action: answer the channel's remaining owed replies, starting with RSC's ask for CS's account-name PATTERN - CS published 32 occurrences, three trees measured 29, and the pattern itself has never been published.
