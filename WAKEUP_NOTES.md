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

## Session 51 - 2026-08-31 - CS-862 CLOSED. A wrapper around the shipped record table finally goes RED, the route it goes red through is one no static arm can see, and the full suite caught a rename the module-level run had called clean

- **Shipped: CS-862.** Detail in `docs/LEDGER.md`, not here. CS-829 stays GATED behind
  CS-G05 - this was PREP and PREP never closes a gated item. CS-863, CS-864 and CS-865
  stay OPEN; CS-864's note gained a dated addendum narrowing what is left of it.

- **THE HEADLINE: AGREEMENT CANNOT SEPARATE A READING FROM THE THING IT AGREES WITH, SO
  THE ARM HAD TO DISAGREE ON PURPOSE.** Every library-backed claim about the second
  reading is an agreement claim, and a wrapper maximises all of them. The new arms degrade
  the shipped record table AT ITS SOURCE in process - `objects._KIND_BY_OBJECT_TYPE`
  relabelled, `objects._read_data_entries` slid one byte with the extent end held - and
  require the second reading to still match the FIXTURE's declaration and the BODY's own
  bytes. Ground truth is never the pristine reading: "did not move" is an equality between
  two calls of one function and a memoising reading satisfies it outright.

- **THE `getattr` ROUTE IS THE RESULT WORTH CARRYING.** Four mutants, the pristine floor
  re-run and verified green after each. STATIC is the four seam-guard arms; DYNAMIC is the
  15 cases of the two new arms. A direct `objects.parse_body(...)` wrapper reddens 2 of 4
  static and 15 of 15 dynamic. The SAME wrapper reached as
  `getattr(objects, "parse" + "_body")` reddens 0 of 4 static and 15 of 15 dynamic. A kind
  decision read as `objects._KIND_BY_OBJECT_TYPE.get(...)` - CS-864's two-level reach -
  reddens 0 of 4 static and every case its plant can reach. That third one also makes the
  discriminator re-transcription load-bearing for the first time: the anti-drift arm
  guarding it is an equality between two spellings, which a shared import satisfies.

- **A PLANT I DOCUMENTED AS A RELABEL WAS NOT ONE, and only a fourth mutant found it.**
  Swapping `objects._KIND_BY_OBJECT_TYPE` makes `parse_body` REFUSE rather than relabel -
  the kind decides how many bytes a record occupies. The field-coverage arm was crediting
  that wholesale kill with covering `is_actor` while NO plant moved that field at all. The
  repair added a third plant that wraps `objects._read_levelled_record` and flips the kind
  AFTER the real reader has consumed the right bytes, and stopped letting a kill count as
  field coverage. Found by making the shift plant inert and asking what stayed green.

- **THE PLANT THAT DID NOTHING, CAUGHT BY ITS OWN OBSERVABILITY ASSERTION.** The first
  plant written wrapped `objects._read_record` - the FLAT reader `parse_object_headers`
  uses. `parse_body` calls `_read_levelled_record` instead, so the shipped table never
  moved and the arm would have passed against every possible second reading including a
  verbatim wrapper. Every arm now proves the SHIPPED reading moved before concluding
  anything about this one.

- **Surprises: I WAS WRONG ABOUT WHICH GUARDS READ `docs/`, AND THE FULL SUITE IS WHAT
  SAID SO.** Before renaming the degradation arm I checked `test_oracle_citations` (scans
  `clockspeed/`) and `test_absolute_claims` (scans `tests/`) and concluded no guard reads
  `docs/`. `tests/test_docs_citations.py` does, and CS-442 exists because of exactly that
  gap. The rename went red on `docs/LEDGER.md` and on the item-notes leaf, and only the
  whole-suite run showed it - the two edited modules were green on their own. THIRD
  SESSION RUNNING that a module-level or subset run has been green while the package was
  not. The repair is the sanctioned one: a machine-checked `RENAMED` disposition, because
  the ledger is append-only and the record was RIGHT when written.

- **Decisions: none recorded as an ADR.** Nothing contradicted `BOOTSTRAP.md`.

- **Failed paths: none abandoned.** One plant target was replaced after measurement
  (`_read_record` -> `_read_levelled_record`, then `_read_levelled_record` ->
  `_KIND_BY_OBJECT_TYPE`, which needs no `ObjectRecord` reconstruction and is the shared
  DATA symbol the session-40 counter-example relabels).

- **DEPARTURE FROM `CLAUDE.md` SECTION 5, RECORDED AS THAT SECTION REQUIRES.** This
  session ran SINGLE-AGENT. The harness forbade dispatching subagents, so there was no
  adjudicator and no independent adversary; the refutation passes were three in-process
  mutants run by the same session that wrote the arms. **A PRODUCER GRADED ITS OWN WORK,
  which is the thing that section exists to prevent.** The mutants and their numbers are
  in `docs/LEDGER.md` and are re-runnable, so the claim is checkable - but it has not had
  an independent pass, and the next session should treat it as ungraded by anyone else.

- **Next action: CS-863** - the shipped SCALAR CONSTANTS both tag walks consult. It is the
  bigger prize and the harder one, and its measurement is already recorded so it does not
  need re-deriving. The plant mechanism CS-862 built - degrade a shared shipped symbol in
  process, assert observability first, grade against the bytes - is the same shape CS-863
  needs for `objects._MAX_TAGS_PER_PAYLOAD`.

- **STILL OUTSTANDING FROM SESSION 49, UNTOUCHED:** the six manual checks in
  `docs/OPERATIONS.md` section 8.3 all still read NOT RUN. They need a human at a real
  display and a real Electron, and `shell/node_modules` still does not exist in this
  clone.

---

## Session 50 - 2026-08-30 - CS-829 GATED behind CS-G05 by operator ruling. Round 4's demand was delivered and measured, four adversaries refuted it anyway, and the round's own headline arm turned out to be an equality between identical arguments

- **Shipped: NOTHING CLOSED.** CS-829 did NOT close; it moved to `docs/GATED.md`. PREP
  merged, DRAIN named. Four follow-ups filed, CS-862 to CS-865. Detail in `docs/LEDGER.md`
  and `docs/item_notes/phase4-followups.md` under CS-829, not here.

- **THE GATE, AND WHY IT IS REAL.** CS-829's acceptance names EVERY record carrying a struct
  type word. 23529 such words sit in records of the version pair CS-G05 exists to measure,
  which no reading opens. The clause cannot be satisfied inside this repo while that gate
  stands, and it had already been rewritten twice for unsatisfiability on the day it was
  filed. An adjudicator that produced none of the work ruled it word by word: two of five
  conjuncts FAIL. **Narrowing the population to the reachable sites is a SCOPE CHANGE with
  its own record, not this gate clearing** - `docs/GATED.md` names that move as the
  synthetic close it would be.

- **THE HEADLINE: A GUARD BUILT BY MAKING THE THING UNDER TEST UNREACHABLE FROM THE MUTATION
  IS NOT A GUARD, AND IT LOOKS EXACTLY LIKE ONE THAT WORKS.** The arm this whole round was
  built around hands the SAME `body` and the SAME independent record to both its passes, so
  it asserts `sum f(x) == sum f(x)`. Measured: every call pair received arguments identical
  by IDENTITY, zero differing, and the equality held under six deliberately garbage readings
  including one that was the shipped record table verbatim. **The entire `tests/save/` suite
  is green against an `independent_records` that wraps `objects.parse_body` and reads no byte
  for itself.** The merger PREDICTED this risk before wave 2 and mis-mitigated it, naming the
  library cross-check as the separator - but every library claim about that reading is an
  AGREEMENT claim, and agreement is what a wrapper maximises.

- **ROUND 4'S DEMAND WAS DELIVERED AND IT CLOSED NOTHING.** Under a degraded record table the
  shipped reading falls 30642 struct sites to 0 while the independent one holds at 30642;
  before the change both fell together. Real, measured three times independently. The
  signature then relocated a FIFTH time - to the shipped SCALAR CONSTANTS both tag walks
  consult. Making `objects._MAX_TAGS_PER_PAYLOAD` STRICTER takes the module from one failing
  arm to NONE while deleting 6204 of 45208 sites. On another pair it reproduces round 4's
  numbers exactly. **CS-863. Do not re-derive it.**

- **THE MERGER'S OWN STRENGTHENING WAS REFUTED.** The library equality was tightened from a
  subset claim plus a floor to `missing == 0` plus file-order agreement, proven against two
  plants - and still ranged only over the bodies the second reading chose not to decline.
  Declining one whole version pair removed 8 of 20 bodies and 18893 records with the suite
  green. Repaired: `bodies == saves`.

- **A REAL PRIVACY DEFECT, INTRODUCED THIS SESSION AND REPAIRED THIS SESSION.** Both reading
  calls sat OUTSIDE their containment handlers with `body` live in the frame. pytest renders
  a frame's ARGUMENTS with no opt-in flag - no `--showlocals` needed - and an adversary read
  240 characters of a real decompressed body out of a planted traceback, carrying a `/Game/`
  asset path on 3 of 20 saves. The docstring claimed the containment before the code had it.

- **Surprises: `BODY_LAYOUT_BY_PAIR` is GUARDED, and the commit message that conceded
  otherwise was wrong.** 53 of 56 layout plants make `parse_body` raise and
  `assert not sweep.failures` catches them; 3 are equivalent mutants; silent loss is zero.
  Nothing contradicted `BOOTSTRAP.md`.

- **Failed paths: none abandoned mid-flight.** Every finding was repaired with a measured
  counter-example or filed with its measurement.

- **PROCESS NOTES WORTH KEEPING.** A slice verified with a SUBSET went green while breaking
  the package-wide reach guard - caught only by the full suite, the same failure session 49
  recorded. The adjudicator proposed five follow-up IDs and ALL FIVE COLLIDED with live
  items; IDs must be checked against `ROADMAP.md`, `BACKLOG.md`, `docs/GATED.md` and
  `docs/LEDGER.md` before filing. Next free ID after this session is CS-866.

- **Next action: take CS-862** - make the independence claim gradable, or narrow it to what
  is graded. It is PREP for CS-829 and it is the item that stops the next round repeating
  this one. CS-863 is the bigger prize and the harder one.

---

## Session 49 - 2026-08-30 - CS-602 CLOSED and the shell-suite job ran for the first time on both platforms; six graders found two ways to make the certificate clause green while trusting everything, and BOTH were the guard rather than the code

- **Shipped: CS-602.** tier2 run `33300238437` at `4b5de1e`, `shell suite` GREEN on ubuntu
  AND windows, `# tests 196 / pass 196 / fail 0 / skipped 0 / todo 0`; tier1 run
  `33300227008` at the same SHA, `success`. Detail in `docs/LEDGER.md`, not here. Ten
  follow-ups filed, CS-614 to CS-623.

- **THE HEADLINE: A GUARD THAT COUNTS A TOKEN DOES NOT CONSTRAIN WHAT THE TOKEN DOES.** The
  arm asserted `shell/main.js` holds exactly one `callback(`. It never looked at the
  argument. So `callback(0)` - accept every certificate ever presented - passed 63 static
  arms, 174 node tests, drift_guard CLEAN and precommit_gate PASS, and so did four
  one-token edits to the verdict map, and so did a single call site answering the wrong
  integer for every non-TRUST verdict. **The root cause was PLACEMENT.** `codeFor` is a pure
  function from five strings to three integers - no electron, no display - and it had been
  moved out of a file with fourteen tests into one with zero, which is exactly what made it
  ungradable. ADR 0014 asserted "mapping words onto integers is a separate module's job" as
  though it were already true.

- **ONE REGEX LITERAL BLINDED EVERY TEXT-SCANNING ARM AT ONCE.** `/[/*]/` is valid
  JavaScript and opens a block comment in the stripper, so everything up to the next `*/`
  vanishes from what the guard reads. Live `ignore-certificate-errors`, the Node TLS kill
  switch and a `certificate-error` handler were invisible while `node --check` called the
  file valid. **The stripper's own docstring named two arms as the alarm; both were measured
  against the attack and both stayed green** - idempotence cannot fire because the second
  strip re-derives the same deletion, and never-grows cannot fire because deleting is
  shrinking. The mitigation had been built parallel to the stripper's assumptions. Repaired
  by scanning RAW text with an allow-list of documented mentions, so the stripper is not
  consulted for that sweep at all.

- **EVERY ONE OF EIGHT SLICES FOUND A REAL DEFECT IN THE BRIEF THAT DISPATCHED IT.** The
  worst was a test the merger specified that PASSES ON THE VULNERABLE CODE: plant
  `{"__proto__":{"width":99999}}` and assert width is the default - which it is either way,
  because `JSON.parse` makes `__proto__` an own property and leaves the prototype intact.
  The discriminating assertion is `Object.getPrototypeOf(loaded) === Object.prototype`.
  Also: a precedence table that returned TRUST when both hostnames were absent; a repair
  that would have MOVED the defect to a tier-2-only lane; and a mandated `throw` that would
  have reintroduced a hang, because a verify callback that throws never fires.

- **THE PUSH GATE WAS PROVEN END TO END ON A REAL VIOLATION.** The merger merged a slice on
  its INTERIM report, verified with a subset that did not include the guard the change
  broke, and committed a failing test. The push was attempted and BLOCKED - `1 failed, 3057
  passed`, `Nothing was pushed`, origin unmoved. Acting on an interim report is the error.

- **THE PIPELINE EXIT-CODE TRAP BIT THREE TIMES IN ONE SESSION.** A backgrounded
  `cmd | tail` reports tail's status. It masked a failing baseline suite, masked four
  failures in a slice's full run, and reported the BLOCKED push as "exit code 0". Capture
  `PIPESTATUS` or do not report an exit code.

- **Decisions: ADR 0013 and ADR 0014 ACCEPTED.** The Electron licence gate split into three
  scopes, and the pin-one-certificate decision with `setCertificateVerifyProc` chosen over
  the strictly weaker `certificate-error`.

- **Failed paths: a `start` script was added and BACKED OUT.** The static guard merged nine
  minutes earlier caught it - electron may be named nowhere in the manifest outside
  `devDependencies`. The guard could have been narrowed; it was not, because `npm start` and
  `npx electron .` are functionally identical and widening a bright-line check for a
  convenience is a bad trade.

- **Next action: run the six manual checks in `docs/OPERATIONS.md` section 8.3.** They all
  read `NOT RUN`, they need a real display and a real Electron, and until they are filled in
  nobody has seen the companion window work. Then CS-615 - the count floor is one test
  pooled over five suites.
