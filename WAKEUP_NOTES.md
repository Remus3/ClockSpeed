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

## Session 12 - 2026-08-16 - FOUR OF FOUR slices refuted, plus the merger; CS-448 root-caused

- **Shipped: NOTHING CLOSED, DELIBERATELY.** Four tier-1 slices were built, merged and then REFUTED
  by independent adversaries, so CS-440, CS-441, CS-443 and CS-444 all STAY OPEN, each with a ledger
  record declaring the non-closure BY NAME. The code stays: every slice is a net improvement and the
  suite is green. Filed CS-449 through CS-454. Suite 1952 -> **1993 passed, 3 skipped**, mypy clean
  over 79 files, ruff clean, drift guard 9 guards PASS 8 WARN 1 (the doc budget). Six commits,
  `0377a29..280eacc`. Detail in `docs/LEDGER.md`.

- **CS-448 IS THE SESSION, AND IT REFUTED THE MERGER'S OWN MEASUREMENT.** I measured 32 runs across
  four contention profiles - `-n auto`, `-n 32`, a 4-core affinity-confined tree, and the original
  SHA in its own verified worktree - got zero failures, and concluded it did not reproduce. **AN
  ADVERSARY REPRODUCED IT SIX TIMES at both cited revisions.** Every one of my 32 runs was taken in
  one of the two locations on this machine where the failure is STRUCTURALLY IMPOSSIBLE. They were a
  control that read like a null result, and I did not know the difference.
  **THE REAL CHAIN, and it is neither party's earlier story:** a checkout sharing a large ancestor
  with the system temp root makes pytest's rootdir for the innermost probe climb to that root, so
  collection walks the entire temp tree - **0.4s from three ordinary locations against 42.7s from a
  clone under the temp root, with only the cwd varied**. A sibling xdist worker deleting a
  `clockspeed_gate_*` temp directory mid-walk makes `os.lstat` raise, collection is Interrupted, the
  level-2 child exits 1. **xdist supplies only the concurrent deleter - it is NOT CPU contention, and
  the walk is single-process.** My contention account was wrong, and so was my count of the sandbox
  spawns in that file (12, not seven). What survived: the CI-history reading, independently
  confirmed. Still open: whether a hosted workspace shares that ancestor. Measure `rootdir` in a job.

- **THE INSTRUCTION I WAS GIVEN WAS FALSE AND I MEASURED IT RATHER THAN OBEYING IT.** The session
  prompt and `WAKEUP_NOTES` both said `ROADMAP.md` was at 97 per cent of "the budget that HARD-FAILS
  CI" and that any sizeable edit "goes red". `ROADMAP.md`'s budget is severity **WARN**:
  `doc_budget.py` returns non-zero only on a HARD failure and drift guard (a) returns WARN and exits
  0, and those two are the only CI consumers. It prints loudly and passes. I did the relocate pass
  anyway, and deleted the false sentence from the file rather than hedging it.

- **THE MERGER SHIPPED A FALSE UNIVERSAL AND AN ADVERSARY CAUGHT IT.** My own seam fix claimed every
  exempted class must be a frozen dataclass, "which a resolver is not". A planted frozen dataclass
  carrying `__call__` - an ordinary resolver shape, and one this codebase is actively moving toward -
  walked straight through. Deleted rather than hedged; the check now tests inertness too and is
  graded by the exact shape that broke it.

- **A SECOND MERGER ERROR, AND THE LESSON GENERALISES.** I reported "four of four worktrees cut from
  the correct base". The reflogs show ALL FOUR were cut STALE and each fast-forwarded itself because
  the dispatch ordered the check - nine of nine across sessions. **`git log -1` after the fact cannot
  distinguish "cut correctly" from "cut stale and self-corrected"; the two states are byte-identical
  at HEAD.** Only the reflog separates them. Committing before dispatch does NOT prevent it.

- **Surprises**, each measured:
  1. **A GENUINELY NEW CRASH FOUND BY A BUILDER SWEEPING ITS OWN FILE.** `local_config` raised
     `UnicodeDecodeError` on a non-UTF-8 config - a `ValueError`, not an `OSError`, so it escaped a
     function whose docstring promises it never raises. Confirmed independently against the pre-fix
     blob before it was accepted.
  2. **A SHIPPED CHANNEL WITH NO CONSUMER.** CS-443's reporting channel is passed by nothing in
     `clockspeed/`, `tools/` or `scripts/`, so `verify_env.py` against a malformed config still exits
     0 saying nothing. The acceptance says "reported rather than silent"; end to end it is silent.
  3. **AN OPERATOR-FACING SENTENCE WITH NO CONTROL.** Replacing all six of CS-443's `detail`
     sentences with a nonsense sentence left the module suite green. Only truthiness is asserted.
  4. **A PRIVACY CONTROL BLIND IN THE SAME PLACE AS ITS SUBJECT.** CS-443's redaction oracle reads
     the same and only sources the redactor reads, so it passes vacuously in exactly the environment
     where the redactor fails open. Separately, CS-444's redaction control has an all-digit fixture -
     the one shape the backstop catches unconditionally - so gutting the redactor left it green.
  5. **A LIVE PRE-EXISTING PII LEAK, filed as CS-454.** An account directory that is not all digits
     - Epic, MS Store, or operator-renamed - renders in plaintext once saves are relocated.
  6. **THE ITEM PLAN INHERITED A WRONG CLOSURE.** CS-425 is listed as closed in the session prompt
     and in session 9's notes; its only ledger record is a grant that says it does NOT close it, so
     it is OPEN. Session 10 recorded this class in the other direction.
  7. **AN ADVERSARY WAS PARTLY WRONG AND WAS NARROWED RATHER THAN RELAYED.** The `purge_work_dir`
     finding is real but bounded by two naming conditions, so it was filed at tier 2, not tier 1.

- **Failed paths - do not retry:**
  - **Measuring a location-dependent flake in one location.** 32 runs in an immune tree is a control,
    not a null result. Vary the thing the defect might depend on, including the checkout path.
  - **Running the authoritative suite while adversaries mutate the tree.** It produced five phantom
    failures that vanished on a clean re-run.
  - **`git log -1` as a staleness probe.** It cannot see a self-correction. Use the reflog.
  - **A fixture whose value is the one case the implementation handles.** Two separate privacy
    controls this session, both green while the thing they guard was gutted.

- **Next action:** **CS-454**, the live PII leak, then **CS-449**, whose reachability is now
  reproduced end to end. Both are tier 1 and both sit on non-negotiables. **BEFORE EITHER, do the
  `ROADMAP.md` relocate pass** - it is at 119 per cent of its WARN budget and the cause is structural
  rather than incidental: its entries have become essays while the topology table says one line per
  item. That is a real refactor, not a trim.

## Session 11 - 2026-08-16 - six items close; FIVE OF FIVE slices refuted; ADR 0008 accepted

- **Shipped: CS-211, CS-428, CS-435, CS-436, CS-437, CS-438 CLOSED.** ADR 0008 ACCEPTED with four
  conditions, all applied. CS-420's acceptance RESTATED. Filed CS-439 through CS-448. Suite
  1846 -> **1952 passed, 3 skipped**, exit 0, serial AND under `-n auto`. mypy 79 files clean, ruff
  clean, drift guard **CLEAN 9/9** (a ninth guard now exists), doc budget PASS. Eight commits,
  `76f6c82..b5cad1a`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THE HIT RATE AND IT GOT WORSE: FIVE OF FIVE FIRST BUILDS WERE REFUTED, plus
  merged `main` itself.** But the useful finding is that FOUR OF THE FIVE HAD ONE SHAPE - a builder
  MEASURED SOMETHING TRUE AND STATED SOMETHING WIDER:
  1. **CS-436:** the budget cannot bound one slow open, therefore it is decorative. It is 5.0s and
     breaks the loop - at 0.4s/read it stops the scan at 13 of 24 while the removal read all 24.
     Removing it was a COVERAGE REDUCTION the grant forbids.
  2. **CS-438:** the handler is unreachable on 3.14, therefore it was unreachable. The DECLARED
     FLOOR is 3.13, where `PathBase.is_file` re-raises outside the ignored errnos, and CI pins 3.14
     at four sites so nothing here would catch it.
  3. **CS-435:** five happy-path indices are flagged, therefore every index is. False at FOUR sites,
     two of which make `parse_usmap` raise and publish NOTHING.
  4. **CS-211:** the parse works on the current sentence, therefore the set is derived. Its fixture
     restated the real doctrine sentence VERBATIM, so the derived and hardcoded paths agreed BY
     CONSTRUCTION and the mutant produced a byte-identical suite result.
  **THAT IS ADR 0008's OWN THESIS ARRIVING IN CODE RATHER THAN PROSE.** The ADR fences the
  sentences; nothing fences the INFERENCE, and the inference is where it landed five times.

- **CS-428's was different and is the one to remember: A PRIVACY CONTROL THAT FAILS OPEN, TRIGGERED
  BY THIS REPO'S OWN TEST SUITE.** Its redaction rules were `lru_cache`d and seeded LAZILY by the
  first report carrying content. `tests/data/test_locate.py:432` patches `USERPROFILE` to a temp dir
  named `home`, so "home" became a session-wide token AND THE REAL SPELLINGS WERE LOST. The grading
  module could not see it: every arm was a cold subprocess with an empty cache. Fixed by building
  the rules once at import.

- **A LIVE CI LEAK WAS FOUND AND CLOSED.** Tier-2 runs `-n auto`; xdist composes its worker line
  AFTER the worker's `makereport`, so the parallel lane leaked a home path on EVERY failure. Fixed
  controller-side - 259 force-failed tests give 259 worker lines and 0 markers against a control
  showing 518.

- **THE FINAL AUDIT REFUTED MERGED `main`, AND ONE FINDING WAS THE MERGER'S.** Three false sentences
  in `tests/conftest.py`. The count "195 test functions" measures **247** by AST and **341** by the
  claim's own wording, and was 325 when written - it was NEVER true, copied from a stale roadmap
  note. **THE MERGER THEN RESTATED IT A THIRD TIME in the ledger entry closing the item, in the same
  session in which it twice flagged other agents for exactly that.** A number arriving inside a
  well-evidenced report reads as evidence rather than as a claim needing its own measurement.
  Deleted, not corrected. The scope list was also wrong in the dangerous direction: it claimed a
  child process's output is NOT reached, and inherited stdout IS.

- **Decisions: ADR 0008 is `accepted`**, adjudicated by an agent that wrote no part of it, with four
  conditions all applied: tier 3's stated ground was REFUTED (two measured-false sentences that
  never rotted - they shipped false); `WAKEUP_NOTES.md` was misclassified as an immutable record and
  the rule now keys on a DATED HEADING, not a filename; the living-text refinement RELOCATES its
  residual to phrasing rather than dissolving it; and Consequences overstated and is narrowed.
  **CS-420's "tension" WAS A MISDIAGNOSIS - do not reopen it.** ADR 0008 SCOPE governs BREADTH,
  CS-420's acceptance governs DEPTH in one module, and that module is already fenced, so the two
  texts never disagreed. Five rounds were spent against a dilemma that was not there. Its acceptance
  is restated on a coverage axis, with its weakest clause LABELLED weaker.
  **A FROZEN-FILE GRANT was issued by the operator for CS-436 alone**, recorded BEFORE any edit;
  `git diff --name-only` confirms no other frozen path on every merge.

- **Surprises**, each measured:
  1. **THE NEW GUARD WENT RED ON THE MERGER'S OWN DOC EDIT, MINUTES AFTER MERGING.** CS-211's
     ownership guard read the CS-420 correction record as a closure, because a record that declines
     to close an item must say so BY NAME and that one did not. Its failure message prescribed the
     fix. Real input, not a planted duplicate.
  2. **THE COMMIT GATE BLOCKED THE MERGER** for writing a literal Linux home path into CS-447 - the
     entry describing a home-path leak. Recorded in the entry rather than quietly fixed.
  3. **THREE REPAIRS APPLIED ADR 0008 TO THEMSELVES**, each deleting detection claims or restated
     counts its OWN repair had just written, one of them three lines below the constants deciding
     the numbers.
  4. **A REPAIR FOUND ITS FINDING WORSE THAN THE ADVERSARY DID, TWICE.** CS-435 found two further
     counter-examples, which changed the fix from reordering to deletion. CS-438 found the same
     false-detail defect at a sibling site nobody had named. CS-211 found F2 covered three clauses,
     not one.
  5. **AN ADVERSARY WAS PARTLY WRONG AND THE REPAIR SAID SO.** CS-428's rule-count figures did not
     reproduce (6/4 not 4/2) while the substance was confirmed and SHARPENED. A "four control
     assertions" figure the merger ordered corrected turned out never to exist in a tracked file.
  6. **CS-435's KEY FOR MECHANICAL SILENT-LOSS DETECTION FAILED ITS FIRST MEASUREMENT AND SAID SO.**
     Keying on a reporting verb anywhere in scope matches 292 of 298 functions. The narrower key
     gets 298 -> 12 and independently rediscovers CS-438, filed by a DIFFERENT agent. That is
     CS-439 and it is evidence rather than argument.
  7. **THE WRITE-LIST BOUNDARY HELD ON EVERY SLICE.** Every agent that found a defect outside its
     list reported it; ten became filed items.

- **Failed paths - do not retry:**
  - **Generalising a narrow measurement into a universal.** Four of five. State the scope you
    measured, including the interpreter and the platform.
  - **A fixture that restates the real input verbatim.** It makes the derived and hardcoded paths
    agree by construction. Declare fixture values DISJOINT from the real ones and test that.
  - **Lazily caching a privacy rule set.** Whatever runs first defines it, and a test that patches
    the environment poisons it. Build at import.
  - **Grading a fence by a constant's NAME.** A renamed equivalent mutant walks through. Find the
    construct by AST and learn the name from it.
  - **Grading session state with cold subprocesses.** Structurally blind to it.
  - **Writing a measured count into prose.** Third instance this session, one of them the merger's.

- **HOUSEKEEPING THAT WILL BLOCK YOU: `ROADMAP.md` IS AT 97 PER CENT OF ITS HARD BUDGET.** It
  PASSES today and `tools/doc_budget.py` FAILS CI above 60 KB, so the next roadmap edit of any size
  goes red. Relocate before you file anything: the superseded dated STATUS blocks inside CS-400 and
  CS-413 are the candidates, and CS-400's entry already marks one of them as no longer the state.
  Relocate to `docs/history_notes.md`, never delete, and leave a one-line pointer.

- **Next action:** **CS-448**, the `-n auto` flake in the no-install save-suite gate - tier-2 CI
  runs that lane and it fails 1 run in 3, measured at BOTH this session's base and head, so it is
  pre-existing and unfiled rather than new. Then **CS-439**, mechanical silent-loss detection, whose
  key is already measured. **CS-420 is now takeable** - its acceptance is restated and its governing
  ADR is accepted, and the two never conflicted; read CS-435's two new derived fences in
  `clockspeed/save/usmap.py` first, they are a worked example of what its clause (2) asks for.

