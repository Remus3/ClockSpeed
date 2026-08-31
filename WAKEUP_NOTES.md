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

## Session 52 - 2026-08-31 - CS-863 CLOSED. The second tag reading stopped consulting the shipped ceiling, so a strictly worse reader can no longer buy a green module; and two independent adversaries defeated CS-862's central claim with a one-line memo

- **Shipped: CS-863.** Detail in `docs/LEDGER.md`, not here. CS-866 filed from the
  adversarial pass. CS-829 stays GATED behind CS-G05 - this was PREP and PREP never
  closes a gated item. CS-864 and CS-865 stay OPEN.

- **THE HEADLINE: A SHARED CEILING IS A SHARED DECISION ABOUT WHO LEAVES THE
  POPULATION.** Both tag walks ran `range(objects._MAX_TAGS_PER_PAYLOAD)`, so a stricter
  ceiling deleted the same records from the numerator and the denominator and every
  equality held while the population shrank. Reproduced at `bde34ec` before anything was
  touched, pair-shaped: at 12 the module showed ONE failing arm, at 0 - which refuses
  everything 12 refuses and more - it showed NONE and exited 0. The repair takes the loop
  bound from the EXTENT, which cannot lose a real tag by arithmetic rather than by
  observation. After it, every ceiling from 0 to 31 reddens the module and 32 and above
  leave it green, the boundary sitting exactly at the corpus's own observed maximum of 31.

- **A CONSTANT IS NOT AUTOMATICALLY SAFE TO SHARE, AND THAT IS THE DOCTRINE TO CARRY.**
  The seam rule was "constants yes, readers no", and it was wrong in one direction: a
  shared WIDTH is data two readings of one format must agree on, but a shared CEILING is a
  shared verdict. Widths and names stayed; the ceiling left.

- **ALL TEN SHARED SYMBOLS WERE PLANTED, because the item note said two of them never had
  been and that expecting them to behave like the ceiling is not evidence.** Only the
  ceiling shows the anti-monotone signature. `MAX_STRING_BYTES` and `MAX_OBJECTS` KILL
  rather than degrade - `parse_body` raises and the sweep's refusal guard catches it - so
  whether a stricter value could instead have improved the grade is recorded UNESTABLISHED
  rather than disproved. `UTF16_CHAR_SIZE` at a wrong value moves NOTHING at all, which is
  a different hole and is named rather than claimed closed.

- **THE SHARED SURFACE IS NOW DERIVED, NOT SAMPLED.** What the two readings shared lived
  in a docstring naming four symbols "among them", and the only one disclosed anywhere was
  `BODY_LAYOUT_BY_PAIR`. `TAG_READING_SHARED_SYMBOLS` records nine, an AST closure derives
  them from source, and five mutants redden the arm that holds the two together.

- **Surprises: CS-862'S CENTRAL CLAIM IS REFUTED, by two adversaries that produced none of
  it and worked from different briefs, then reproduced a third time by the merger.** A
  ONE-LINE MEMO over a `getattr` wrapper of `objects.parse_body` passes all 15 dynamic
  arms in module order - 15 failed recomputing, 63 passed memoised - because each arm calls
  `independent_records` once, AFTER the plant, on bodies earlier arms already read while
  pristine. Moving the ground truth from the pristine reading to the fixture fixed
  PROVENANCE and buys nothing against a cache, because the cache returns the
  fixture-correct answer too. The recorded 15 of 15 holds only when those arms run ALONE.
  Filed as CS-866. Nothing contradicted `BOOTSTRAP.md`.

- **A PIPELINE ATE PYTEST'S EXIT CODE AND I REPORTED A RED SUITE AS GREEN.**
  `pytest ... 2>&1 | tail -20` returns `tail`'s status, and the harness reported exit 0
  while the very output I was reading said "2 failed". Both failures were mine, in
  `tests/test_docs_citations.py`. Every suite verdict from now on is read from a LOG FILE
  with `echo PYTEST_EXIT=$?` written into it, never from a piped command's status.

- **AND ONE OF THOSE FAILURES WAS A SUBAGENT'S PARAPHRASE TRANSCRIBED AS A CITATION.** An
  adversary abbreviated an arm name to its first four words and a trailing ellipsis; it
  went into a note verbatim and the citation guard caught it as an identifier bound
  nowhere. The real arm is
  `test_the_reading_agrees_with_the_shipped_table_on_a_synthetic_body`. The FINDING the
  adversary carried was real and independently reproduced - the identifier was not. NOTE
  THAT WRITING THE DEAD NAME DOWN TO EXPLAIN IT FAILS THE SAME GUARD A SECOND TIME, which
  is why this bullet describes the shorthand instead of spelling it.

- **Decisions: none recorded as an ADR.**

- **Failed paths: none abandoned.** The pair-shaped plant harness needed an int-alike with
  `__index__` armed from a `parse_body` wrapper, because a plain global plant is loud - it
  breaks the synthetic fixtures and never reaches the quiet loss class.

- **Next action: CS-866**, and take it before CS-864. It is the same seam CS-864 is about,
  it now has a measured counter-example rather than a predicted one, and CS-864's residue -
  a reading rebuilt from shipped `_Cursor` primitives - was MEASURED green this session and
  belongs to the same repair.

- **STILL OUTSTANDING FROM SESSION 49, UNTOUCHED:** the six manual checks in
  `docs/OPERATIONS.md` section 8.3 all still read NOT RUN. They need a human at a real
  display and a real Electron, and `shell/node_modules` still does not exist in this clone.

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

- **AND THE PROSE AROUND THAT REPAIR WAS NOT FULLY RE-READ.** Adding the third plant left
  three sentences in the CS-862 ledger entry still saying "two plants". Caught during
  `/done`, corrected by a NEW append-only record rather than by editing - `docs/LEDGER.md`
  says nothing in it is ever edited once written. Commit `10c5777`. The arms, the shipped
  code and the entry's own mutant table were right throughout; only the prose was stale,
  which is the same fault the correction is about.

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

