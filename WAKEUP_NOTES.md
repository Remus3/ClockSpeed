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
