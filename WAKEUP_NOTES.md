# Wakeup notes

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

## Session 15 - 2026-08-16 - CS-454 built, merged, and REFUTED on clause 1; the fence it shipped is refuted too

- **Shipped: NOTHING CLOSED. CS-454 STAYS OPEN** with a ledger record declaring the non-closure by
  name. Clause 2 MET, clause 3 MET, **clause 1 NOT MET**. The code stays - it is a real improvement.
  Filed CS-462, CS-464, CS-465, CS-466, CS-467, CS-468. Suite 2007 -> **2018 passed, 3 skipped,
  exit 0**, serial, baseline measured by the merger at `bb7a236` in a real checkout BEFORE merging.
  Two commits, `60068a9` and `02523f9`, merged at `9c30fd9` and `758888d`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT THE FIX WORKS AND THE ITEM STILL DOES NOT CLOSE.** The relocated-path form
  is closed in all four resolution states, the 8.3 form is closed, and three independent vacuity
  reasons were removed from the controls. Then an independent adversary found a leak the merger, the
  planner and the builder had all missed, and it is in the NEW design rather than pre-existing.

- **THE JUNCTION DEFECT, and it is the session's real result.** `_remember_save_root` stores
  `_path_forms(str(path))` and never resolves; `clockspeed/save/workdir.py`'s `_resolved()`
  deliberately DOES resolve, and its docstring says so. So whenever the save root is reached through
  a junction the two halves of the same package cannot agree on spelling, no anchor matches, and a
  hex account directory renders WHOLE through the production refusal in `_refuse_if_forbidden`.
  Reproduced by the merger with a real `mklink /J`, all self-checks passing first. Junctioning a save
  folder onto another drive is the ordinary way to relocate one.

- **PLACEHOLDER INJECTION DEFEATS THE POSITIONAL RULE, and it fires WITH THE MARKER PRESENT.** The
  environment pass runs first and rewrites a matching needle to a token, injecting `<` into the
  account segment; `_PATH_SEGMENT_CLASS` excludes `<>` so position cannot match, and the remembered
  name pass then hunts a literal the text no longer contains. `USERNAME=Ada`, account directory
  `Ada4f3a...` -> 30 of 33 characters in plaintext. Pre-existing, unchanged from `bb7a236`.
  **RULED: a pre-existing instance of the exact defect an item names does NOT excuse that item**, and
  the reason is in CS-454's own detail entry, which opens by calling the leak pre-existing.

- **THE FENCE THIS SESSION SHIPPED IS ITSELF REFUTED, filed as CS-465.** The redact-cycle pin walks
  the transitive closure to unbounded DEPTH but grades against `RESOLVER_NAMES`, `locate`'s PUBLIC
  surface, while four of the seven hops in the cycle are private. Confirmed by the merger with the
  fence's own helper: a private-hop plant closes the cycle and the fence reports GREEN while the same
  tree raises `RecursionError`. Its own comment says it reads the closure precisely because "a single
  private wrapper would defeat a body-only check".

- **Surprises**, each measured:
  1. **A NON-DIGIT FIXTURE ALREADY EXISTED AND PROVED NOTHING.** `ACCOUNT_DIR_SHAPES` shipped four
     shapes, three already non-digit - but every path carried the marker, so position caught all
     four. Neutering the DIGIT BACKSTOP left **0 of 4** leaking; neutering POSITION left 3 of 4. So
     clause 2 read naively was ALREADY SATISFIED while the leak was live. A control must be a
     CONJUNCTION: non-digit AND a layout where position cannot fire AND a named mutation.
  2. **THE CONTROLS WERE CARRIED BY A NEIGHBOUR TEST.** `test_workdir.py` had no reset of
     `_RESOLVED_ACCOUNT_NAMES`; one test seeded the needle for the whole process. Measured ON THE
     PRE-FIX TREE at `bb7a236` and quoted here only as session history - alone 1 failed, full module
     73 passed. **Neither figure reproduces at `758888d` and neither should be carried forward.**
     Under `-n auto` that made it vacuous NONDETERMINISTICALLY, which is the shape that survives.
  3. **THE NAIVE IMPLEMENTATION WOULD HAVE BEEN INERT ON THE ORDINARY MACHINE.** Appending the new
     pass after the env pass leaks everything, because the env pass has already rewritten the path
     out from under the needle. Live only in the relocated case - the inverse of the filed one. The
     builder demonstrated the counterfactual rather than asserting the three-form design was needed.
  4. **THE MERGER CITED A VACUOUS CONTROL.** "The recursion does not occur even with a collector
     wired through `_override`" tests only half the counterfactual: with the shipped code calling no
     resolver, wiring a collector cannot recurse, trivially. The adjudicator built the real one and
     got `RecursionError`. The conclusion held; the evidence did not.
  5. **THE MERGER'S OWN FOUR-STATE MATRIX WAS THE COMMON-MODE RISK.** It varies override,
     digit-neighbour and resolution order and varies NOTHING about link indirection, username
     collision or whitespace - so three surviving channels are invisible to it by construction, and
     the junction defect sits exactly in that blind spot. Every agent inherited those blind spots.
  6. **BOTH BUILDERS LEFT THEIR WORK UNCOMMITTED** on branches whose `git diff` against the base was
     EMPTY. Merging the branch names as reported would have merged nothing.

- **Failed paths - do not retry:**
  - **Reading "use a NON-digit fixture" as sufficient.** Three of four shipped shapes were already
    non-digit and the leak was live.
  - **Widening `_PATH_SEGMENT_CLASS` to close the whitespace tail.** Three variants measured, all
    worse; one eats the diagnostic prose, one leaves the terminal segment fully intact.
  - **Calling a resolver from inside `redact()`.** Latent infinite recursion that CS-443 detonates.
  - **Feeding `_RESOLVED_ACCOUNT_NAMES` from every save-root subdirectory.** Breaks a shipped
    assertion against the game's own `common` directory.
  - **Trusting a branch name from a builder.** Check the diff against the base before merging.

- **Next action:** **CS-454 again, and it is now four named things** - the junction defect, the
  placeholder-injection defect, the whitespace tail and a stated exemption for the bare segment. All
  four are INSIDE the item; do not file them as follow-ups. The adjudicator's six closure conditions
  are in `docs/LEDGER.md`. **Take CS-465 in the same pass** - it is the fence that was supposed to
  protect the recursion rationale and it does not.

## Session 14 - 2026-08-16 - CS-420 closes on the seventh round; CS-421 and CS-422 both REFUTED

- **Shipped: CS-420 CLOSED.** CS-421 and CS-422 were ADJUDICATED AND REFUTED and both STAY OPEN, each
  with a ledger record withdrawing the previous record's evidence by name. Filed CS-458, CS-459, CS-460,
  CS-461. CS-455's acceptance CORRECTED against a measurement; CS-456 rescoped from one type word to the
  family. Suite 2001 -> **2007 passed, 3 skipped, exit 0**, serial, observed this session. mypy clean
  over 28 files, ruff check and format clean, drift guard **CLEAN 9/9**, doc budget PASS. Detail in
  `docs/LEDGER.md`.

- **THE HEADLINE IS THAT INDEPENDENT GRADING CHANGED THE OUTCOME ON ALL THREE ITEMS, IN BOTH
  DIRECTIONS.** Two items that read as done were refuted; one item that had failed five rounds closed.
  The session prompt offered the adjudication as the CHEAPER alternative to CS-420. It was not cheaper
  and it was the more valuable half.

- **CS-421's int32 oracle passes green on bytes that are not the int32.** Displace the `IntProperty`
  value start by +4 - reading the next tag's name-length prefix - and it scores **75136 of 75136**
  against the correct read's 70669, because a name-length prefix is a small little-endian count and
  carries a CLEANER signature than real values do. Only synthetic fixtures notice. **The as-read
  majority survives at -2, -1, +2, +3 and +4**, so a rotation control testing only plus or minus one
  would pass and prove nothing. `FloatProperty` is NOT refuted - it collapses at every non-zero delta,
  and that asymmetry is a finding. Both cited mutants reproduced digit for digit and the
  non-circularity defence held under three attacks: what failed is ANCHORING, not independence.

- **CS-422's partition assertion compares a set with itself.** `CURSOR_WIDTHS | EXTENT_WIDTHS` is built
  from the same four sources the test builds its own `shipped` set from, so `ungoverned` and `phantom`
  are structurally empty. Confirmed by the merger from source with no mutation needed. Replacing
  `WIDTH_SHIPPING_RULE` with "ship any width you feel like, no evidence needed", emptying
  `DECLINED_VALUE_READINGS`, or gutting all three cited tests each leaves the save suite GREEN, and
  neither symbol has a production consumer. Two of the three tests do not run without a save library,
  so on CI the rule is graded by nothing at all. What survived: `at = value_start + size` is the only
  tag-walk advance in the package, so an extent width genuinely cannot move the cursor.

- **CS-420 WAS REFUTED AT ROUND SIX AND CLOSED AT ROUND SEVEN, and the shape of the failure is the
  item's own signature.** Clause 3's comment half had no liveness floor and could be reduced to probing
  nothing with the full suite green. The prose audit found two false sentences, **one of them CREATED
  by the commit whose stated purpose was stripping false measurements**. The repair DELETED rather than
  reworded, found a third false sentence nobody had listed, and tied both probes to the census
  population. The second clause-5 pass could not break clauses 1 to 4 across 25 injection shapes, 7
  deletion trials, 13 mutants and a 279-position attribution sweep.

- **Surprises**, each measured:
  1. **THE MERGER'S OWN MUTANT LOOP WAS INVALID AND CONTRADICTED TWO AGENTS.** Looping constants inside
     ONE process reported everything red, because the decode sweep is MEMOISED and every iteration after
     the first silently replays the first mutant's verdict. One process per constant: 0 red, **1 / 255 /
     1000 / 65535 / 1000000 GREEN**, 16777216 red. That falsified CS-455's stated premise that a large
     constant goes red, so its acceptance was rewritten.
  2. **THE HARNESS EDIT TOOL WRITES CRLF**, converting whole tracked files. `git status` stays CLEAN
     because `.gitattributes` normalises the blob on commit, so nothing catches it. `git checkout --`
     does NOT fix it - git thinks the file matches. Delete then check out. Recorded in the harness
     memory store as `edit-tool-writes-crlf`.
  3. **THE MERGER REPRODUCED CS-448's MECHANISM BY ACCIDENT.** Removing an agent worktree WHILE the
     authoritative suite was collecting starved that run past twice its normal wall clock. It is the
     concurrent-deleter half of CS-448 arriving from a hand rather than from xdist.
  4. **A BUILDER DISAGREED WITH ITS DISPATCH AND WAS RIGHT.** Told the `monkeypatch` symbol names were
     data, it read them as prose instead - over-reading costs nothing when the string carries no
     marker, and every exemption is a hole to defend. That collapsed the design to ONE string exemption
     class.
  5. **THE CLAUSE-5 ADVERSARY MISSED A FALSE SENTENCE THAT THE BUILDER THEN CAUGHT** - a suite outcome
     the builder had never measured, in its own new prose. Checking one flagged sentence also exposed a
     sibling of the same shape. Where one instance of a shape is found, the family is worth a sweep.
  6. **TextProperty WAS NOT THE ONE HONEST EXCEPTION.** Four type words share the split; three are
     declined in a DIFFERENT table on sample size. The admitted exception was simply the one that got
     transcribed.

- **Failed paths - do not retry:**
  - **Looping mutants inside one process against a memoised sweep.** The first verdict is the only one.
  - **Editing a tracked file with the harness Edit tool and trusting `git status`.** It reports clean
    on a working tree that violates the LF rule.
  - **Deleting a worktree while the authoritative suite runs.** That is CS-448's own mechanism.
  - **Re-wording a false measured sentence.** Every attempt in this project's history produced another
    false one, including one four hours old. Delete, or derive in the run that prints it.
  - **Reading a follow-up item as satisfying the clause it was filed against.** CS-456's existence does
    not make CS-422's exception clause met.

- **Next action:** **CS-454**, the live PII leak on `main` - tier 1, non-negotiables 3 and 12. Then
  **CS-449** (fail-open below CS-444, reachability measured and reproduced end to end, tier 1), then
  **CS-455**, whose acceptance was corrected this session and must NOT be closed with a synthetic
  fixture. **CS-421 and CS-422 both need real work, not re-grading** - CS-421 needs a value-start
  rotation control built knowing +4 does not collapse today, and CS-422 needs its partition derived
  from INDEPENDENT sources (that half is filed as CS-458).

## Session 13 - 2026-08-16 - CS-421 and CS-422 land unadjudicated; ROADMAP.md refactored

- **Shipped: NOTHING CLOSED.** CS-421's clauses 1 and 2 are met and clause 3 is met for two of five
  types; CS-422's acceptance reads as met on every clause. **Neither was adjudicated and no adversary
  ran** - I built them and I graded them, which this project does not accept, so both STAY OPEN with
  ledger records declaring the non-closure by name. Filed CS-455, CS-456, CS-457. Suite
  1993 -> **2001 passed, 3 skipped**, mypy clean over 28 files, ruff check and format clean, drift
  guard 9 guards PASS 8 WARN 1 FAIL 0, doc budget **PASS** (was WARN). Detail in `docs/LEDGER.md`.

- **THE ROADMAP REFACTOR IS DONE AND IT WAS THE REFACTOR, NOT A TRIM.** 119 per cent of budget to 57.
  Every oversized entry keeps its line, acceptance, tier, a one-sentence lead and a pointer; 21 full
  bodies relocated VERBATIM to `docs/history_notes.md` with 21 matching anchors and zero dangling
  pointers. **The five entries whose CURRENT STATE is load-bearing - CS-440, CS-441, CS-443, CS-444,
  CS-448 - got hand-written leads**, because an algorithmic first-sentence lead rendered CS-440 as
  "filed as the remainder of CS-435" and buried "built and refuted". A cold session reading that would
  redo refuted work, which is the exact failure this file exists to prevent.

- **THE ENDIANNESS QUESTION IS SETTLED FOR THE TWO TYPES PILLAR 3 NEEDS, against the game's data rather
  than our own writer.** The premise is a fact about the GAME - save int32s are counts and indices, so
  the stored high byte is usually zero - so no fixture this project packs can satisfy it by
  construction. The pivot is half the population, so **no measured constant appears in any assertion**,
  which is deliberate: `_JOIN_WORD_FLOOR = 13` sitting at its observed value is why CS-432 exists.
  Mutants: `">i"` reddens the int oracle at 7926 of 75136 and leaves the float oracle green; `">f"`
  reverses it at 4425 of 31318. The counters EXCHANGE values rather than drifting.

- **A SHIPPED COMMENT CLAIMED THE ENCODING WAS MEASURED AND NOTHING EXECUTABLE CHECKED IT.** Four
  percentages in prose. Its int figures reproduced exactly; **its float figures did not**, because the
  predicate behind "plausible" was written down nowhere - unreproducible by construction. Deleted per
  ADR 0008 rather than corrected.

- **CS-422's INCONSISTENCY DISSOLVED RATHER THAN GOT EXCUSED.** Widths split into two classes needing
  two oracles: a CURSOR width moves `value_start`; an EXTENT width cannot move the cursor at all,
  because the walk advances by `at = value_start + size`. That is STRUCTURAL - I read the advance before
  letting the word "cannot" stand - not a corpus accident. **Sample size was never the operative
  criterion**, so shipping at n=9 and declining at n=11976 was never actually inconsistent.

- **Surprises**, each measured:
  1. **A SPELLING-KEYED TYPE DISPATCH.** `_decode_fixed_width` chose float-vs-int with `code == "<f"`,
     so a float in any other byte order fell into the integer branch where `int(NaN)` raises. Nothing
     was broken on the shipped table - the invariant "the float code is spelled exactly this way" was
     simply never stated. It is also what made the `">f"` mutant unreachable, so fixing it is what let
     the float oracle be proven at all.
  2. **MY OWN DOCSTRING SHIPPED A FALSE ATTRIBUTION AND MY OWN ADVERSARIAL PASS CAUGHT IT.** I wrote
     that the rotation control covers the constant-fabrication gap. Under a constant-1 mutant that
     control stays GREEN - it perturbs the WALK, and a fabricated value does not move the walk. 8 tests
     red, 7 synthetic plus the nested gate. Deleted and replaced with the measurement; the gap is
     CS-455.
  3. **THE CITATION CHECKER IS BLIND TO `#:` DOC-COMMENTS.** Four citations naming real tests resolved
     to TRUNCATED names and `test_oracle_citations.py` PASSED. The underscore-wrap rejoin applies to
     column-0 `#` blocks only. Failure direction is the dangerous one - unreadable reads as absent,
     not as an error. Worked around by moving them; the channel is CS-457.
  4. **A KEY COLLISION IN MY OWN FIRST DRAFT.** `ArrayProperty` ships a tag-extra width AND has its
     value reading declined, so keying the declined table by bare type word read as though the whole
     word were declined. Caught by printing the sets to look for exactly that.
  5. **`git checkout --` TO REVERT A MUTANT DESTROYED MY OWN FIX** in the same file. Invert mutants by
     targeted replace, never by checking out a file that also holds your work.

- **Failed paths - do not retry:**
  - **Trusting a measured number written in prose.** The float percentages did not reproduce and their
    predicate was unrecorded. Derive, or delete.
  - **Attributing a gap to a named control without running it.** The mechanism said it could not fire.
  - **Writing a `path::test_name` citation into a `#:` doc-comment.** It is not read.
  - **An algorithmic first-sentence lead for an entry whose state is the point.** It buried "refuted".

- **Next action:** **CS-420**, the last of the three CS-413 closes through, and the hardest - five
  failed rounds, acceptance restated on a coverage axis, ADR 0008 accepted. **Before building, read
  CS-435's two derived fences in `clockspeed/save/usmap.py`** - they are the worked example its clause
  (2) asks for. **Failing that, get CS-421 and CS-422 ADJUDICATED** - both are built, both are graded
  only by the agent that built them, and neither can close until an independent pass runs.
