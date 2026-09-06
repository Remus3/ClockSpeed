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

## Session 63 - 2026-09-05 - CS-911 and CS-912 CLOSED; the HUD style layer took SEVEN audit rounds and none returned CLEAR; CS-910's done-claim was REFUTED TWICE and three of four adversaries returned REFUTED

**CLOSED.** CS-911 - every stage takes a unique filename and opens `"wx"`, so the
truncation primitive is gone rather than made unlikely. CS-912 - `/api/registry` publishes
the registry as a tenth route, and 731 of 731 producible items built a solve request naming
only published identifiers.

**OPEN, and both for reasons worth reading.** CS-910 routed seven spawn sites and its commit
message claimed the remainder was all frozen. That was FALSE TWICE: `scripts/verify_env.py`
is not frozen, was on the write-list, and still put a bare `git` into three argv; and the
remainder is FIVE indirect delegations, not three. CS-913's filed cause is REFUTED by the
code and its line is rewritten.

**FILED.** CS-914 (the CS-911 shape in Python, on the DEFAULT production path), CS-915 (two
latent guard holes), CS-916 (one asset-extraction prerequisite that three separate features
are all gated on), CS-G06 (the mature-world corpus, an operator action).

**SEVEN CS-600 AUDIT ROUNDS ON ONE STYLE LAYER AND NOT ONE RETURNED CLEAR.** Rounds 1 to 4
each found the same fault one selector further out - the rule's own `color`, then its
`border`, then the nested `.hud-*` descendants, then every OTHER descendant - because every
repair defined its boundary as "the tokens something I can see reads". Round 4 named it:
each repair closed the set the previous auditor named and drew the new boundary exactly
where the previous finding stopped. WHAT ENDED IT WAS A MEASUREMENT, NOT A BETTER REPAIR:
the four `--overlay-*` tokens were byte-identical to the DARK values of `--bg`, `--text`,
`--accent-hud` and `--hud-rule`, so the overlay palette had been the dark palette all along.
Rounds 5 to 7 then left the palette entirely - `color-scheme` is not a custom property;
round 6 found the round-5 fix had landed on `.hud-overlay`, which renders ZERO times, while
`:root` had none; round 7 defeated the repaired guard with an OPTIONAL TRAILING SEMICOLON.
Round 7 graded the RENDERED page PASS on all five phases with zero live defects, and THE
OPERATOR RULED TO COMMIT on that evidence. Every finding is repaired and each is proven by
a planted mutation.

**THE MEASUREMENTS WORTH KEEPING.** #FA9549 scores 2.22 / 2.07 / 1.96 on this page's own
LIGHT grounds - it fails even the large-text threshold there, not merely over a game pixel,
because a light theme IS a white pixel that is always on screen. Contrast over a scrim is
NOT MONOTONIC: it falls from 2.22 at no scrim to 1.02 near alpha 0.35, where the composited
ground crosses the accent's own luminance, then climbs to 8.38 opaque. A light scrim lands
at the WORST legibility available.

**THREE OF FOUR ADVERSARIES RETURNED REFUTED, WITH DISTINCT LENSES.** Security found three
live bare-name spawns in a non-frozen file plus both guards blind to them. Does-it-reproduce
found CS-912's paired control vacuous - it SUBSTITUTED the foreign key into a request naming
one recipe, so it also removed the target's own producer, and proved it with a live mutant
that kept the arm green while `tests/solve` went red. Completeness found four guards each
reporting zero findings because they could not SEE findings. Scope confirmed the
`workdir.py` race is reachable on the default path and measured 31 of 240 concurrent copies
failing. FOUR LENSES, FOUR DIFFERENT CLASSES - repeated skeptics would have found one.

**OPERATOR RULINGS THIS SESSION.** Commit on audit round 7 rather than iterate to CLEAR.
Wiki and community sources are READ-AND-CITE ONLY - CS-485 stands, no dataset is lifted, no
crawl is run. The local `Satisfactory Designs` downloads are REVIEW ONLY and nothing derived
from them is committed.

**A UI/UX DOCTRINE FROM ANOTHER PROJECT WAS INGESTED** and adapted into
`docs/hud_doctrine.md`, which is now the owner file for the two surfaces. It records what
does NOT transfer as carefully as what does, and names THREE SHIPPED ARMS an overlay will
collide with: the no-timer arm, the one-clickable-target arm, and the 7-bit ASCII arm, which
with a CSP publishing no `img-src` leaves an overlay with neither a glyph nor an image.

**TRAPS MEASURED THIS SESSION.** `dict(os.environ)` UPPER-CASES KEYS ON WINDOWS, so popping
a mixed-case variable removes nothing and the probe reports clean while measuring nothing -
it produced a GREEN result on genuinely defective code. A `;` CHAIN ENDING IN `tail` EATS
PYTEST'S EXIT CODE exactly as a pipe does: a red suite was reported as exit 0 twice, once to
me and once to a slice. AND I BROKE A FREEZE I DECLARED THREE TIMES - three separate agents
caught it independently; one recovered the start bytes and diffed to prove its verdict still
stood.

**NAMED AND NOT CLOSED.** ROADMAP.md is at 112 PER CENT of its soft budget and this session
made it worse; a relocate pass is owed. The HUD layer renders ZERO times today - it is a
published vocabulary waiting on `/api/plan` and `/api/advice`. Two design questions are open
and recorded in `docs/hud_doctrine.md`: whether the overlay keeps the companion's warm accent
when the game's own world is warm, and whether item identity and production status can share
the colour channel.

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
