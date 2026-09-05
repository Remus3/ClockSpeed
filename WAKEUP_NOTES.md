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

## Session 62 - 2026-09-05 - THE COMPANION RAN FOR THE FIRST TIME EVER and a real shortcut now launches it; the round that shipped it was REFUTED FIVE TIMES including a LOCAL CODE-EXECUTION VECTOR, and the repair brief's own premise was refuted too

NOTHING CLOSED. CS-909 is OPEN and both its commits say so. Suite 5066 -> see the
final report; the shell lanes moved 203 -> 307 node tests and 77 -> 134 asset arms.

**WHAT EXISTS NOW THAT DID NOT.** A desktop shortcut launches the Electron
companion with no terminal. It starts the dashboard if nothing answers, ADOPTS one
that already does, keeps a tray icon, hides rather than exits on close, and on Quit
stops only the dashboard that launch started. All of that was exercised at a real
display, some of it by the operator.

**IT HAD NEVER BEEN EXECUTED BEFORE THIS SESSION.** `shell/node_modules` did not
exist. Every check in `docs/OPERATIONS.md` section 8.3 read `NOT RUN`; five of six
are now filled and check 6 is not.

**THE TWELVE-OF-TWELVE PATTERN HELD, AND THEN SOME.** The first round shipped with
five defects its own suites were green against. All five were found by agents that
wrote none of it, on FOUR DISTINCT LENSES - and the lenses did not overlap:
adjudication found the overclaimed commit message and the common-mode risk;
does-it-reproduce found thirteen of fifteen mutations surviving; security found the
spawn vector; resource-lifetime found the zombie and the state-file corruption.
Repeated skeptics would have found one of those, not four.

**THE COMMON-MODE RISK, NAMED BY THE ADJUDICATOR AND STILL LIVE.** `healthy` is a
boolean `shell/lib/supervisor.js` is graded on exhaustively and DOES NOT COMPUTE.
Its derivation lives in `probeOnce`, inside the one file no test in either language
can load. Every slice inherited that framing from the brief and encoded it as an
input. It has already fired once - the BoringSSL probe bug was wrong for an entire
session with both lanes green.

**FIVE THINGS MEASURED THAT CONTRADICTED A DOCUMENT OR A CLAIM. THE SPIKE WINS.**

1. The pinned Electron ships NO `scripts` block, so `npm install` fetches no binary
   and exits 0 in about half a second; the runtime downloads lazily on first
   `require`. `docs/OPERATIONS.md` section 8.1 said otherwise and now does not.
2. `shutil.which` does NOT exclude the current directory on this interpreter - it
   returned a RELATIVE path to a planted file. The repair brief asserted the
   opposite and used it to justify the design. `scripts/make_cert.py` has the same
   exposure. FILED AS CS-910.
3. The recorded 2.217s-2.227s cold start does not reproduce. Through the shipped
   path it is 0.46s-0.53s, every sample answering on attempt 1. The ten-millisecond
   spread was a fixed constant, not a process start.
4. `new Tray()` handed an empty image does NOT throw; it returns a non-null Tray
   with an invisible icon. `trayRef !== null` was therefore the wrong question.
5. Registering a `window-all-closed` listener SUPPRESSES electron's default quit,
   which is what turned the no-tray fallback into a zombie holding a live child.

**A CORRECTION THIS SESSION OWES TO ITS OWN FIRST COMMIT.** `8210a3c`'s message
claims section 8.3 checks 1 to 5 were observed. The file at that commit records
only 1 and 3. The observations were real; they were never written down. The tracked
note was correct throughout - the COMMIT MESSAGE was the wrong artifact. Repaired.

**DECISIONS - DO NOT RE-LITIGATE.**

1. THE PROBE USES ELECTRON `net`, NOT NODE `https`. Node's `ca` option is not
   honoured under electron's BoringSSL build. `net` also deletes a second trust
   decision rather than moving it. The install-before-probe ORDERING is load-bearing
   and is graded by NOTHING - probing first poisons the verdict cache permanently.
2. THE INTERPRETER IS RESOLVED TO AN ABSOLUTE PATH BEFORE SPAWNING. Do not
   re-pitch spawning a bare name with a fallback; the fallback IS the vector.
3. THE TRAY DECIDES WHETHER CLOSE MEANS HIDE. No tray means quit, which runs
   `will-quit` and stops what the launch started.
4. ADR 0015 EXTENDS THE SEAM: the shell MAY start the surface, and stops only what
   it started. It does not re-litigate the never-write rule.
5. THE ICON IS AN ASCII DATA URL, NOT A TRACKED BINARY. This repository has zero
   tracked binaries and the shell byte sweep would redden on one. 16x16 is
   IMPOSSIBLE to encode alphanumerically - the fixed IHDR constant at that size
   contains a solidus - which is why it is 32x32.

**NAMED AND NOT CLOSED.**

- CS-909's manual half now has a home (`docs/OPERATIONS.md` section 8.5) and one
  check in 8.3 is still `NOT RUN`.
- CS-910 and CS-911 were filed this session and are untouched.
- ROADMAP.md is at 107 per cent of its soft budget. A RELOCATE PASS IS OWED and
  this session made it worse by three lines.
- `main.js` is still loaded by no test (CS-619). Everything in it is graded by
  text arms over its source, which cannot prove a call GOVERNS - only that it
  exists and is reachable by name.
- The `.lnk` carries a TrackerDataBlock with COMPUTERNAME and a MAC-derived UUID.
  Recorded in the script's PRIVACY section, not stripped - it is untracked and
  operator-requested.

**WORKTREE AGENTS STARTED STALE IN THREE OF THREE REPAIR DISPATCHES**, all at
`7ba2df8` rather than the stated `8210a3c`. Every one fast-forwarded because the
brief ordered the check. The running tally is now overwhelming: ORDER IT EVERY TIME.

## Session 61 - 2026-09-05 - CS-896 MEASURED AND NOT CLOSED: the lane's SERIAL MEAN is ABOVE its own cutoff, so the cancellation was the distribution; BOTH repairs were REFUTED, both were then repaired and MERGED

- **Shipped: CS-908 only.** Filed CS-900, CS-906 and CS-907 and opened the `CS-9nn` block on an
  operator decision. **CS-896 IS NOT CLOSED** - its acceptance needs a run that reports the
  comparison and no such run exists. No acceptance clause was rewritten, a THIRTEENTH
  consecutive session.

- **THE MEASUREMENT THE ITEM ASKED FOR THREE SESSIONS AGO WAS TAKEN ON THE RUNNER.** The serial
  job MEAN is 606.5s against a 600s cutoff, from two runs of a byte-identical tree at 582s and
  631s. So roughly half of all runs would be cancelled and the cancellation was never flakiness.
  `-n auto` is worth 1.222x mean to mean (range 1.121x to 1.393x, do NOT quote the flattering
  end), and all six runs reported 4784 passed and 117 skipped, so the verdict does not change.

- **In flight: NOTHING is uncommitted, and CI is the open question.** Both repairs landed. The
  CS-896 one was refuted with 18 of 26 mutants surviving, repaired, and re-proved at 53 mutants
  run and 53 killed. **CS-896's acceptance needs a run that REPORTS THE COMPARISON**, so read the
  tier 1 run on the pushed head before deciding anything about that item.

- **Decisions: the `CS-9nn` block is open and CS-901 through CS-905 are NOT allocatable** - they
  are synthetic fixture ids in the drift-guard corpus. The handoff said CS-903 and CS-904 were
  clean; both measured FALSE. A frozen-file grant for `.githooks/pre-push` was issued with
  THIRTEEN conditions and NO EDIT WAS MADE UNDER IT, because two conditions cannot be honestly
  met on a machine another project held at 84 to 99 per cent.

- **Surprises: the CS-896 note's own premise was half wrong.** It said the three slowest local
  tests are library-backed and cost nothing on the runner. True of ONE. The other two got MORE
  expensive - 51.5s local to 111.4s on the runner, and 25.8s to 50.5s. The runner is about 2x
  SLOWER for subprocess-heavy work. Recorded under CS-900.

- **Failed paths.** My brace-matching scan reported ELEVEN unbounded subprocess sites; NINE are
  real, and a builder corrected me - one was comment prose, one a `Popen` already bounded. My
  first two speedup figures, 1.774x inherited from an adversary and 1.335x from single samples,
  were both wrong; the controlled six-sample figure is 1.222x. I also framed the ledger
  line-pointer question as a two-way choice and an adjudicator refuted both options and produced
  a third.

- **THE MECHANISM SHIPPED AND PROVED ITSELF ON ITS FIRST REAL RUN, by reporting the lane OVER
  BUDGET.** Run 33981934085 printed `tier 1 took 565s - over budget (budget 540s, ceiling 570s)`.
  CS-896's clause has two halves: the lane REPORTS its duration against a stated budget, and it
  does NOT complete inside it. **CS-896 STAYS OPEN on the first half.**

- **THE FINDING THAT MATTERS, and it is worse than a missed budget.** The runner's spread on a
  BYTE-IDENTICAL tree is 49s, so a ceiling that does not fire on noise must sit about 49s above
  the observed 565 - roughly 614, which is ABOVE the 600s cutoff. **AT THIS LANE'S COST THERE IS
  NO VALID CEILING.** The one in the tree sits 5 seconds above the lane and WILL fire on noise,
  so the next push may turn tier 1 RED at a number. That is loud rather than silent, which is
  the property the item wanted, but it is not a healthy lane.

- **WHY THE BUDGET WAS ALREADY STALE WHEN IT SHIPPED.** It came from four parallel samples whose
  worst job was about 519s, on a tree the runner counted at 4784 passed. The merged tree counts
  4953 - this session added 169 - and the unit step went 483s to 530s. **A speedup measured
  before the session's own work is not a speedup the session delivers.**

- **Next action: decide the ceiling. Either make the lane faster (CS-900 is the unblocker and
  names the concentration) or move both levels through guard (k)'s two-way ratchet with a
  stated reason. DO NOT re-derive them from one sample - that is the error this session made.**

## Session 60 - 2026-09-04 - CS-891 CLOSED AS AN HONEST PARTIAL after FIVE refutations; the round's repair reproduced its own filed fault a FIFTH consecutive session and its own adversaries caught every instance, and the repair then would not fit under a data-hygiene ceiling

- **Shipped: CS-891 CLOSED AS AN HONEST PARTIAL**, the unmet conjunct named in the ledger in
  those words. Filed CS-897, CS-898 and CS-899, each measured before filing. Suite 4721 -> 4887;
  the citation guard alone went 162 -> 326 arms across two modules. **No acceptance clause was rewritten - an ELEVENTH consecutive session.**

- **THE PATTERN HELD A FIFTH TIME AND THE ROUND CAUGHT IT ITSELF.** The bare-path arm
  shipped green at 302 passed and was then refuted five ways: a unique suffix hit resolved a
  dead citation into `tests/` and into `.claude/` while DOCUMENTING that it needed no
  ratchet; the reason ceiling could be written as the length of its own table, making the
  budget a tautology with no number left in the diff; a forgiveness table named with a
  leading double underscore escaped the walk written to make escaping impossible; three
  non-vacuity floors could each be set to zero with nothing going red; and two legs the
  shape's own prose NAMES could be deleted without an arm noticing. All five repaired, each
  original mutant now dies.

- **THE SHARPEST ONE IS THAT THE SOURCE DENIED THE HOLE RATHER THAN OMITTING IT.** The
  suffix rung was documented as "a RESOLUTION rather than a forgiveness, so it needs no
  ratchet". Exactly one hit proves a path names A file and never THE intended file, which is
  the property the module's own trap 2 says a bare path does not carry. A false clearance is
  worse than a silence, and this one left no trace in a diff.

- **THE REPAIR DID NOT FIT.** It took `tests/test_docs_citations.py` to 273753 bytes against
  a 262144 ceiling that exists to catch a trimmed real game-data file. The builder REFUSED
  to raise it, correctly. The module was split into a derivation and its arms with the
  collected test-id list identical across the split, and the class-closing walks now run
  over a DERIVED module closure - a table relocated into the new module without registration
  reddens, while the old single-module walk stays blind. That is filed as CS-898 because the
  gate's own claim that it never trips on ordinary test code is now false and a second
  module sits at 96 per cent of the same ceiling.

- **Decisions: the guarded doc set went 21 -> 39 and it was a merger call, ruled legitimate
  by an adjudicator that verified the mechanism rather than the argument.** It is FORCED,
  not chosen: a new judged pattern must join the membership contract, which widens what
  counts as a carrier. Measured cost zero, and the seven flagship docs it adds - `CLAUDE.md`
  and `BOOTSTRAP.md` among them - carry no citation at all under the four pre-existing
  shapes. The standing consequence is real: a dead backticked path in `CLAUDE.md` now
  reddens the suite.

- **Surprises: THE ROADMAP BUDGET IS A WARN, NOT A HARD FAIL.** The previous handoff said
  the next item line breaks it. `tools/doc_budget.py` returns non-zero only on a HARD
  failure and says why in its own header - a warn that blocks a commit gets disabled and
  then enforces nothing. So three items were filed and the relocate pass is handed forward
  as measurably owed rather than suppressed to protect a soft number.

- **Failed paths, and four of them are mine.** My "independent" ladder control IMPORTED the
  module it graded and consumed its population boundary, so it was independent only in the
  rungs - which is exactly why it and the shipped arm agreed on seven AND both missed the
  same dead citation. I dismissed that citation early as out of population without asking
  whether the exemption's stated reason covered it; it does not, and it is now CS-897. I
  briefed a builder that a path root was untracked when the package carries it nested, and
  the builder measured me wrong and said so. And my own sweep regex made backticks OPTIONAL
  while I was arguing in the same session that the backtick was load-bearing.

- **In flight: nothing uncommitted.** Do NOT prune worktrees on a dirty reading - the count
  grew again this session and every sampled file in a dirty worktree is byte-identical to
  main at a stale base. Only a diff against main decides.

- **The repair was RE-ADJUDICATED from a frozen SHA and STANDS.** A first adjudicator ruled
  at `c5c3947`, I kept building, and it correctly refused to certify repairs it had not
  watched land - so a second pass was dispatched scoped to the three commits it could not
  see. Thirteen of thirteen filed mutants now die, each against a pre-repair control proving
  it was genuinely silent before. Tier 1 CI on the pushed head: SUCCESS in 8m44s.

- **THE SIGNATURE FAULT REPRODUCED A SEVENTH TIME, INSIDE THE SPLIT.** A ceiling in the
  module the split created can be rewritten as the length of its own table and survives -
  the exact tautology the repair closed two commits earlier. It is LATENT, not live, and it
  is recorded with three other residuals in `docs/LEDGER.md` under the session 60 entry.

- **THE NEXT ITEM ID FORCES A DECISION NOBODY HAS MADE, and that is why those four residuals
  carry no `CS-` id.** CS-899 was the last id the `CS-8nn` block holds. ADR 0011 says
  reaching CS-900 is "a `ROADMAP.md` ID-block question rather than a doc-topology one" and
  explicitly declines to answer it. **SETTLE THE ID BLOCK BEFORE FILING ANYTHING ELSE** -
  allocating CS-900 in passing answers by accident a question the project deferred on
  purpose.

- **The session ran on past that point, HEADLESS, and closed CS-897 too - also an HONEST
  PARTIAL.** The archive exemption's reason now rests on three claims the archive makes about
  itself, checked both ways, and its rot is pinned per arm. An adjudicator confirmed the
  population at 28 by reimplementing all six arms rather than calling the module's code -
  which mattered, because two earlier derivations of that number were wrong, mine included.

- **SEVEN findings against that repair are RECORDED, NOT FIXED, and the reason is a hard
  limit.** `tests/test_docs_citations.py` is 260661 bytes against a 262144 data-hygiene
  ceiling: **1483 bytes left**. Seven fixes and their arms do not fit, and that ceiling must
  not be raised. Two of the seven are CS-897's own defect class in text CS-897 authored.

- **THE MODULE IS NOW THE BINDING CONSTRAINT ON THE PROJECT.** CS-899 extends this same file
  and has under 1.5 KB to do it in, and CS-898 exists because the gate's own claim that it
  never trips ordinary test code is false. **The relocate pass is the precondition for
  everything downstream, not a tidy-up.**

- **The `CS-8nn` id block is FULL at 100 of 100** - measured, with 64 still open. Creating the
  next block is an OPERATOR decision with a recorded precedent: `CS-4nn` filled at 98 of 100
  and the operator created `CS-8nn` on 2026-08-21. ADR 0011 anticipated CS-900 and declined it
  in terms. **Only FILING is blocked; work on existing items continues.**

- **CI ON THE FINAL COMMIT RAN 9m55s - FIVE SECONDS UNDER THE CUTOFF**, the tightest
  margin ever recorded. CS-896 is no longer a lane inside the noise band; it is a lane AT
  its cutoff, and the sixth data point already proved the variance is runner-side rather
  than workload. Expect a cancellation with nothing failing, and do not read it as
  flakiness. Detail in the CS-896 note.

- **THE RELOCATE PASS IS DONE.** The citation guard went 260661 -> 234638 bytes, 99.4 per
  cent -> 89, headroom 1483 -> 27506. The archive-rot machinery has its own guard and arms
  pair. Behaviour unchanged arm for arm; no test id vanished. **The split exposed a LIVE
  import cycle the suite was green over** - four entry orders imported cleanly and the
  fifth raised ImportError, and pytest never enters through a non-test module. Fixed, with
  an arm that re-enters from every side in a fresh interpreter.

- **CI ON THE FINAL COMMIT WAS CANCELLED AT 10m19s, NINETEEN SECONDS OVER THE CUTOFF, AND
  NOTHING FAILED.** The same tree ran 4897 passed / 4 skipped / exit 0 in the pre-push hook
  minutes earlier, and the only cancelled step is the unit-test step. CS-896 predicted this
  one run earlier and it landed. **DO NOT read it as flakiness and do not re-run hoping for
  green** - the variance is runner-side and the lane is now over its cutoff, so a re-run
  only re-samples a distribution whose mean has crossed the line. CS-896 IS NOW THE TOP
  ITEM.

- **Next action: CS-896, because tier 1 no longer completes.** Then the seven recorded
  findings against CS-897, which now fit. Two are that
  item's own defect class in text it authored: a floor whose stated property holds for two
  of five shapes, and a coverage proxy that admits the exact case its message says it
  prevents. Detail in the CS-897 ledger entry. Then CS-899, which also needed this room., because it gates
  CS-898, CS-899 and the seven recorded findings alike. Then the operator's id-block call.
  `ROADMAP.md` is also over its soft budget and owes its own relocate pass.
