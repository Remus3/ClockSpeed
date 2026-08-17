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

## Session 16 - 2026-08-17 - CS-422 CLOSES; CS-421's anchoring half lands and clause 3 still fails

- **Shipped: CS-422 CLOSED.** CS-421 STAYS OPEN with its anchoring half fixed and a ledger record
  declaring the non-closure by name. Filed CS-469, CS-470, CS-471, CS-472, CS-473, CS-474. Suite
  2018 -> **2035 passed, 3 skipped, exit 0**, serial, baseline measured by the merger itself at
  `f20411c` before any slice ran. Drift guard **CLEAN 9/9**. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THAT THE GRADING PASS REFUTED THE MERGER THREE TIMES AND CHANGED THE RECORD EACH
  TIME.** Builders and graders were right against the merger on the seam, on the reason CS-421 cannot
  close, and on a repair instruction that would have destroyed a live check. Every one of those
  corrections landed BEFORE the ledger was written rather than after.

- **CS-421 IS NOT DATA-BLOCKED AND THE MERGER'S RULING THAT IT WAS IS THE SESSION'S WORST NEAR-MISS.**
  The merger ruled clause 3 unsettleable because only **17 of 75136** int32 values carry differing
  middle bytes, so no oracle over this corpus could separate the identity from the middle swap. An
  adjudicator took the measurement the merger had not: **30304 of 31318 FLOAT32 values do carry them.**
  The evidence is in the library in quantity and the shipped float oracle's magnitude band is simply
  too wide to use it - a weakness of the ORACLE. Had that reasoning reached the ledger it would have
  fenced off the one open route. Filed as CS-469 and it is the next action.

- **THE ANCHORING HALF IS REAL AND IT IS THE ITEM'S ONE SOLID GAIN.** `tests/save/test_value_anchoring.py`
  compares the shipped decoder reading in place against the same declared extent in a poison-padded
  buffer: 0 mismatches shipped, **75136 of 75136** under the +4 displacement that leaves the old
  oracle GREEN. The contrast is DERIVED rather than asserted - a test computes which displacements the
  old oracle tolerates and requires that set to be exactly the one this module controls at.

- **CS-422 CLOSED ON SIX EXECUTABLE CONSEQUENCES WHERE SESSION 14 MEASURED ZERO.** The E1 mutant that
  used to leave the whole save suite green now reddens, and with it applied the rest of `tests/save`
  still passes at 1014 - so the new module is the only thing that catches it. Library-free proven with
  an audit hook: 9 passed, 0 skipped, access count 0, with every discovery root pointed at an empty
  directory. `WIDTH_SHIPPING_GROUNDS` is hand-authored and injecting a fifth width turns it RED.

- **Surprises**, each measured:
  1. **THE MERGER SEEDED A FALSE SENTENCE INTO ITS OWN DISPATCH.** It told a builder that a
     plus-or-minus-one rotation control "would pass and prove nothing". The oracle is a CONJUNCTION
     and is RED at -2, -1, +2 and +3, GREEN only at +4. The upstream ROADMAP sentence was true of the
     majority half alone; the dispatch widened it, the builder shipped it at two sites, an adversary
     caught it, and the replacement is a derivation rather than another sentence.
  2. **THE MERGER'S VOCABULARY WIDENING DID NOT DO WHAT IT CLAIMED.** Widening the decline codes was
     meant to make `WIDTH_RULE_EXCEPTIONS` fail on a mis-classified entry. It guards RE-TRANSCRIPTION
     only: the shipped constant and the test evaluate the same comprehension over the same mapping.
  3. **A MODULE-LEVEL COMPREHENSION IS EVALUATED AT IMPORT, so mutating its source in process leaves
     the derived constant STALE** - which a real source edit does not. That flipped one mutant's
     verdict from DETECTED to MISSED and made a per-entry deletion sweep read 4 of 5, not 5 of 5.
  4. **THE ANCHOR CONTROL IS GREEN FOR ANY PURE FUNCTION OF THE DECLARED EXTENT.** A decoder zeroing
     one stored byte of every int32 leaves the whole module green with 4484 values wrong, and across
     the save suite the only catchers are SYNTHETIC-FIXTURE tests - CS-421's own circularity one layer
     along. It establishes WHICH BYTES are read, not WHAT FUNCTION they go through.
  5. **A BUILDER REFUTED A REPAIR INSTRUCTION AND SAVED A LIVE CHECK.** Told the partition assertions
     in `test_properties.py` compare a set with itself, it measured first: the two TABLES cancel but
     the test's own transcribed literals do NOT, so renaming `GUID_BYTES` turns `ungoverned` RED.
     Deleting them would have removed a real transcription check. CS-458's note is corrected.
  6. **THE FALSE SENTENCE WAS IN TWO PARAGRAPHS, NOT THE ONE THE ADVERSARY QUOTED.** The repair
     instruction named one site because that is what was quoted; the builder swept and found the
     duplicate, which a fix scoped to the quotation would have left standing.
  7. **A SUBAGENT'S "no save library on this machine" WAS THE NESTED GATE'S INNER RUN**, which forces
     discovery empty by design. `tests/save` on main is 1007 passed 0 skipped. Taken at face value it
     would have condemned a slice as unmeasurable.
  8. **WORKTREE STALENESS FIRED IN 3 OF 4 BUILDERS**, including one dispatched explicitly against a
     post-merge commit that found itself two merges behind.

- **Failed paths - do not retry:**
  - **Recording CS-421 clause 3 as blocked by the corpus.** The float32 population carries the
    evidence; the oracle cannot use it.
  - **Deleting the partition assertions in `test_properties.py`.** They still catch a literal rename.
  - **Mutating a table in process and reading a constant derived from it at import.** Re-derive, or
    the verdict is about a stale value.
  - **Leaving mutation harnesses in a gitignored directory.** A caveat in a destroyed scratch file is
    not a caveat in the artifact - the limits had to be re-derived by a verifier and then written into
    the module.
  - **Trusting a substring scan to grade prose.** A rule text naming every code while inverting the
    rule passes it, and so does one that names every code and governs nothing.

- **Next action: CS-469**, the float32 discriminator over the values whose middle stored bytes differ.
  It is the only open route to CS-421 clause 3, which is the last of the three items CS-413 closes
  through - and CS-413 is the phase-4 depth gate that CS-400, then CS-500, then the dashboard sit
  behind. **Do NOT close it with a band narrowed until it separates today's corpus** - that is the
  `_JOIN_WORD_FLOOR` shape CS-432 exists to remove. After it, CS-471 is tier 1 and privacy-adjacent.

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

- **THE SAVE LIBRARY GREW THIS SESSION AND CS-G05 MOVED, THOUGH NOT ALL THE WAY.** The operator
  played the pinned world forward and saved. The version-60 pair went from two files that were
  byte-identical over the measured region - ONE observation - to FIVE files of differing sizes
  where 10 of 10 pairs diverge. **BUT the earliest divergence is at offset 12 and the latest at
  offset 30, which is header metadata, so what is proven is that they are distinct FILES and NOT
  that the property payload is independently sampled.** The merger's first probe treated five
  digests as five observations, which is precisely the file-count-as-independence-count error
  CS-G05's own entry warns about; a second probe caught it. Full status in `docs/GATED.md`.
  The PREP harness still passes, which is correct - it pins a negative.

- **Next action: OPERATOR-DIRECTED 2026-08-16 - TAKE CS-421 AND CS-422, NOT CS-454 AND NOT CS-465.**
  The reason is the critical path to a usable surface: `CS-413`'s own entry names CS-420, CS-421 and
  CS-422 as the gap between "the values were produced and are self-consistent with our own writer"
  and "correctly decoded". CS-420 closed in session 14, so CS-421 and CS-422 are the last two, and
  CS-413 is the phase-4 depth gate that CS-400, then CS-500, then the dashboard all sit behind.
  `IntProperty` and `FloatProperty` are inventory counts and clock speeds, which is exactly what
  pillar 3 reads, so this is the audit's own evidence base rather than abstract rigour.
  **CS-454 and CS-465 STAY OPEN and are deferred, not dropped** - CS-454 has four named blockers in
  its ROADMAP entry and CS-465 is this session's own porous fence.

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
