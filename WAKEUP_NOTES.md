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

## Session 76 - 2026-09-08 - the repaired sender was refuted on all four lenses, and the second cut's fault was the evidence rather than the code

- Shipped: nothing CLOSED. CS-958's slice S1 merged and the item stays OPEN.
  CS-959 FILED. Detail in `docs/LEDGER.md`, not here.

- In flight: nothing. Tree clean, no worktrees, no stash.

- THE SESSION DID EXACTLY WHAT SESSION 75 HANDED IT AND THE ANSWER WAS YES.
  Four adversaries, four REFUTED verdicts, nine defects in a tool this project
  had already called repaired once. Four demonstrated defects in a first cut is
  a reason to expect the second cut is not clean; it was not.

- THE SEVERE FINDING INVERTS THE TOOL'S PURPOSE. `grade()` takes bytes only, so
  a note's FILENAME and a destination's NAME were never graded. The value the
  gate REFUSES in content ships as a filename into every sibling inbox and is
  recorded `gate_verdict: CLEAN`. The gate was in front of the payload and
  beside everything else.

- S1 MERGED AND ITS OWN FIRST CUT WAS REFUTED FIRST. The mechanism held against
  a junction, a two-deep chain, an inbox-level junction, a subst drive and a UNC
  root. The suite did not: three of four subtle mutants shipped a green 40 of
  40, two restoring a measured finding of this item verbatim.

- TWO EVIDENCE FAILURES WORTH CARRYING PAST THIS ITEM. A fixture built parallel
  to the implementation is the shape that makes an arm agree with a bug - the
  `.resolve()` mutant survived because pytest resolves `basetemp`. And a
  monkeypatch that supplies the value under test converts an integration
  property into a unit tautology - both arms patched `REPO_ROOT`, so the clause
  was graded and the binding never was, while a copy running from a worktree
  still delivered into the real inbox.

- Decisions: none needing an ADR. F1/F2/F3 were decomposed as TWO ORDERED slices
  rather than three parallel ones; the fence is in the ledger entry.

- Surprises: none contradicting `BOOTSTRAP.md`. No spec update is owed.

- Failed paths: `cd` into `moon_sync_inbox` to read a note bricked every shell
  call for the rest of the turn, because the hooks resolve their own script path
  from cwd. The memory that covers it named worktree removal as the trigger and
  recommended a shim recovery that would have meant writing into a sibling's
  inbox. Both corrected.

- Next action: REFUTE THE S1 REPAIR. It answered an adversary and has had no
  adversarial pass of its own, and it introduced an asymmetry it named but did
  not resolve.

## Session 75 - 2026-09-08 - the grant was refused on a measurement, and every artifact this session built was refuted before it was believed

- Shipped: CS-952 CLOSED. CS-956 and CS-958 FILED. CS-957 and CS-958 built and
  hardened but OPEN by design. Detail in `docs/LEDGER.md`, not here.

- In flight: nothing. Tree clean, no worktrees, no stash, nothing unpushed.

- THE SESSION'S SHAPE WAS BUILD-THEN-REFUTE AND EVERY REFUTATION PAID. Seven
  graders ran. Not one returned empty, and three found the defect in the
  EVIDENCE rather than in the artifact - which is the part to carry forward.

- CS-952: A FROZEN-FILE GRANT WAS ISSUED AND DELIBERATELY NOT SPENT. An
  adjudicator granted the edit to `.claude/settings.json` with conditions. An
  adversary then refuted the PREMISE: `moon_sync_inbox/` is itself gitignored,
  so a fresh clone has no channel, the watcher answers that with exit 3, and a
  `SessionStart` hook exiting non-zero has its stdout dropped. The tracked
  wiring would have fired, failed and said nothing. A GRANT IS PERMISSION, NOT
  AN INSTRUCTION. The claim was corrected instead - which this ledger already
  recorded twice, under CS-928 and CS-931, and the proposal cited neither.

- THE CHANNEL HALF WAS SENT. One note, 3712 bytes, to four sibling inboxes,
  operator-authorised, bytes checked for ASCII and personal data BEFORE the send
  was reported. Its only record is the ledger entry, which is CS-951
  demonstrated rather than argued.

- CS-957, the outbound leak gate: REFUTED THREE TIMES. The exclusion hatch it
  relied on was consumed inside `discover_world_names`, which `PiiMatchers`
  builds for BOTH gates - so silencing an outbound false positive would have
  blinded the frozen commit gate to that real world name, permanently. Measured
  1 to 0 diagnostics, blocklist 25 to 17. Split into its own key.

- A MUTATION PASS THEN REFUTED THE SUITE, NOT THE CODE. Ten mutants, two shipped
  green: `_canary_measured` hardcoded True, and the oracle reconciliation
  no-op'd. The second was silently backstopping two other arms. FOURTEEN PASSING
  ARMS WERE NOT EVIDENCE THEY GRADED ANYTHING.

- CS-958, the send path: the gate had ZERO call sites, so it was an instrument
  beside the channel rather than a gate in front of it. An adversary then
  demonstrated four defects in the sender, including a real partial delivery
  reported as "nothing was sent", and a TOCTOU window that delivered ungraded
  bytes recorded as CLEAN.

- Decisions: none needing an ADR. The CS-952 branch choice is recorded in the
  ledger with its fence.

- Surprises: nothing contradicted `BOOTSTRAP.md`. No spec update is owed.

- Failed paths: tracking the watcher wiring (refused on measurement, do not
  re-pitch); a higher length floor for the world-name class (the commit gate
  already denied it by measurement - 8 of 25 real names would drop out of the
  COMMIT gate too).

- MY OWN FAULTS, KEPT VISIBLE BECAUSE THEY ARE THE TRANSFERABLE PART. A stash
  used to attribute a test-count change reverted the tree BEFORE I snapshotted
  it, so my "working copy" snapshot was already HEAD and restoring from it
  restored HEAD - the whole repair sat in `stash@{0}` while the tree read clean.
  Recovered by luck, not design. And twice I wrote a probe helper that accepted
  an `env` argument and never passed it to the subprocess, which produced a
  false negative I nearly banked as a verified fix, and wrote a real delivery
  record into the repository's default location.

- Next action: **REFUTE THE REPAIRED SENDER.** CS-958's four fixes answer the
  pass against the PREVIOUS commit and have had no adversarial pass of their
  own. Four demonstrated defects in the first cut is a reason to expect the
  second cut is not clean.

---

## Session 74 - 2026-09-08 - the flip plan chose its branch, and CS-954's repair introduced the hang its own refutation caught

- Shipped: CS-954 CLOSED. CS-700's PLAN produced and CS-700 stays OPEN by design.
  ADR 0018 accepted. CS-955 filed. Detail in `docs/LEDGER.md`, not here.

- In flight: nothing. Tree clean, no worktrees, no stash.

- THE SESSION'S SHAPE WAS PLAN-THEN-REFUTE, TWICE, AND BOTH REFUTATIONS PAID.
  Each deliverable was committed to freeze it, graded by an agent that did not
  write it, and repaired. Both times the adversary found a defect in the
  author's own evidence rather than only in the artifact, which is the part
  worth carrying forward.

- CS-700's PLAN: the CONVENTIONS 17 clause is CONDITIONAL and its antecedent
  does not fire. The publishable graph is clean of CONTENT on six axes, so no
  rewrite is owed for the reason section 17 contemplates. What is dirty is
  off-main and never pushed. The exposure is what the FORGE accreted: 53
  `refs/wip` refs, 233 Actions run logs of which 21 are failed runs, 17
  artifacts, 534 MiB of caches - all surviving a force-push. ADR 0018 therefore
  recreates the remote and pushes `main` alone, which makes the deletion the
  verification.

- TWO OF MY OWN CLAIMS WERE FALSIFIED BY THE ADVERSARY, and both are kept
  visible in the documents rather than smoothed away. I asserted the wip refs
  were invisible to REST; paginated REST returns all 53, and my "11" came from
  an unpaginated query that answered short without erroring - trap (b) firing
  inside the evidence offered as proof trap (b) was handled. And the plan's
  first bundle step would have preserved nothing, because the wip refs exist
  only on the remote, so its control compared two empty local counts and 0 == 0
  would have passed green.

- THE FOURTH CHANNEL NOBODY HAD LOOKED AT: commit author and committer identity.
  520 of 521 commits carry a real personal email in both fields. CONVENTIONS 17
  gate item 2 does not reach it. The operator RULED: rewrite to noreply.

- CS-954: THE REPRODUCTION REFUTED THE FILED MECHANISM AND THE ITEM WAS REPAIRED
  ANYWAY. Two controlled runs - plain local path and `file://` - advanced the
  local ref mid-hook and BOTH shipped exactly the SHA the hook was handed, with
  a control proving the ref had really moved. The incident is nonetheless REAL:
  no CI run has ever existed for the SHA the hook graded, and one push-event run
  exists for the later commit created three seconds after the ref update. So the
  repair was built MECHANISM-AGNOSTIC on purpose.

- THE REPAIR INTRODUCED A HANG AND THE REFUTATION CAUGHT IT. Reading stdin
  unconditionally makes the hook wait forever for an EOF a terminal never sends,
  so hand-running it wedged where it used to exit. The arm meant to cover that
  asserted only CLOSED stdin while its docstring claimed to cover the debugging
  case - which is the terminal case, and was the one that hung. Also caught: a
  condition implemented but ungraded, proven by a mutant that survived all four
  arms while changing real behaviour.

- Next action: read the CS-700 plan section in `docs/item_notes/phase7.md`. It
  is the implementing session's brief and it is now step-by-step. Its step S0 is
  to write the needle set and the allowlist into the plan before S1 runs.

- Watch out for: `/clear` survival is STILL not measured across five repos. The
  three same-second lines in the invocation log are session 73 exercising the
  instrument by hand via `--source`, not hook fires. CS-952 is a hard blocker on
  the flip and needs a frozen-file grant. ROADMAP.md is over its soft budget.
