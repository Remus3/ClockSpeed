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

## Session 31 - 2026-08-22 - THREE items close and SIX are filed; every first build was refuted, and the largest finding is that a substituted interpreter disarms every tier-0 gate

- **Shipped: CS-702, CS-809 and CS-810 CLOSED. Filed CS-703, CS-704, CS-811, CS-812, CS-813,
  CS-814.** Six commits, `f348d85..bfa64e7`. Suite 2393 passed, 3 skipped, exit 0 on the final
  bytes. Detail in `docs/LEDGER.md`, not here. **SIX NEW ITEMS CAME OUT OF TWO, and four of the six
  are defects in things that were already green and already reported done.**

- **EVERY FIRST BUILD THIS SESSION WAS REFUTED, and so was every second build of CS-702.** Not one
  refutation came from reading the code; every one came from an agent RUNNING it - real commits,
  proven-landed mutants, planted citations. Two builders reported green suites over live
  fail-opens. **The transferable form: a suite is evidence about the shapes it enumerates and about
  nothing else.** CS-702's suite was green through three fail-opens because every arm drove ONE
  commit path and one arm ASSERTED AN ESCAPE AS INTENDED BEHAVIOUR. CS-809's carrier check was
  blind to three of the four citation shapes its own module judges.

- **THE BIGGEST FINDING IS CS-703 AND IT IS NOT WHAT ANYONE WAS LOOKING FOR.** All three hooks
  share a byte-identical `cs_probe` that runs the candidate interpreter with `-c` and judges ONLY
  the exit code, so `true`, `:` and `env` all pass it. The heredoc is then handed to that program,
  which ignores it and exits 0, and the hook reports success. **`CLOCKSPEED_PYTHON=true` therefore
  disarms the character-set gate, the secret scan, the commit-msg checks and the whole-suite
  pre-push run, all at once.** Measured with a real commit that landed a forbidden trailer. This is
  the CS-806 shape a THIRD time - a rule already decided, never carried to where it also applies.

- **CS-702 CLOSED ON THE MATCHER ALONE, BY OPERATOR DECISION, AND THE PRE-FILTER REWRITE WAS
  DELIBERATELY NOT SHIPPED.** That is a result, not an unfinished attempt. The rewrite closed four
  escapes and was refuted anyway: reading the whole buffer is sound for a SCAN and unsound for a
  SELECTION, so it chose a different subject line from the one git stores, and it rejected
  `git commit --verbose` whenever the staged diff carried a byte above 0x7E - which blocks
  precisely the work of fixing such a byte. Its measurements are preserved against CS-813.

- **Decisions: no ADR. Four that must not be reopened as questions.** The trailer predicate is
  NAME-FREE and deliberately wider than the `docs/GATED.md` operator decision - adjudicated on the
  CS-209 precedent that narrowing a blocklist by default was DENIED BY MEASUREMENT. **A FENCE IS
  NOT A SHIELD** - git parses a fenced block whole when a generated trailer shares it, so skipping
  fences fails OPEN; indentation is the shield. `WAKEUP_NOTES.md` is now GUARDED rather than
  recorded unguarded, which is what makes CS-809's "stays the only one" clause literally true.
  Disposition SITES are pinned by COUNT, never by line number.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Two things contradicted an adjudicator and one
  contradicted a tracked file I wrote.** Ground truth won each time per CLAUDE.md section 8. The
  widened grant required reading `commit.cleanup` to license narrowing; measurement says a
  command-line `--cleanup=` outranks config and is INVISIBLE, so no observable can license it -
  worse, config `verbatim` plus flag `strip` makes the hook actively wrong in a direction it cannot
  detect. And **`docs/LEDGER.md` carried a wrong number I put there** - "215-character stored
  subject" where the measurement is 200 - corrected by a later record, never by a rewrite.

- **Failed paths, so they are not retried.** A resolver that inherits the last full citation seen
  manufactures 14 false findings. A config-driven cleanup prediction leaves 8 fail-open cells.
  `commit.verbose` as a truncation proxy reads `true` under `--no-verbose`. And a repair dispatched
  with worktree ISOLATION is pinned to a NEW worktree and cannot reach the one holding the work -
  it correctly refused rather than repairing the wrong copy.

- **A TRIPWIRE THE NEXT SESSION WILL HIT AND WILL NOT SEE COMING, and this bullet is deliberately
  written without spelling the name it is about.** `WAKEUP_NOTES.md` is GUARDED now, and
  `tests/test_docs_citations.py` carries a RENAMED disposition keyed to this file that pins its
  dead bare name at EXACTLY ONE site. Read the key out of the table rather than from here. That one
  site lives inside SESSION 30's entry below. **Archiving session 30 drops the count to zero and
  turns the suite RED on a correct doc-hygiene move.** When session 30 ages out, update that
  disposition in the SAME commit. Writing the name into a new session note also breaks it, by
  taking the count to two - which is how this bullet was first drafted, and the guard caught it.

- **OPERATOR ACTION OUTSTANDING, unrelated to the code: rotate the GitHub personal access token.**
  Five live credentials sit in the environment every git hook inherits, and an agent dumped that
  environment into a transcript during a probe. Nothing is committed and no git config key carries
  them, both checked. Filed as CS-814.

- **In flight: NOTHING from this session.** Working tree clean. The four pre-existing worktrees
  (CS-492 rounds seven to nine and the two-site spike) and branch `cs807-attribute-half` are
  UNTOUCHED and still unmerged, exactly as session 30 left them.

- **Next action: CS-703.** It needs a frozen-file grant for all three hooks, and it is tier 1 with
  a blast radius wider than the item that found it.

## Session 30 - 2026-08-22 - CS-806 and CS-442 both CLOSE; each was larger than filed, and each closed an unimplemented clause rather than the typo it was reported as

- **Shipped: CS-806 and CS-442, both CLOSED, both tier 1, both pushed with tier1 CI SUCCESS
  READ rather than predicted.** `6e37a11` and `ae25547`. This ends three consecutive sessions
  that closed nothing. Detail in `docs/LEDGER.md`, not here.

- **BOTH ITEMS WERE BIGGER THAN THEIR FILING, AND IN THE SAME WAY: a rule was already written
  down and simply never implemented.** That is worth carrying forward as a pattern rather than
  as two anecdotes. CS-806 was filed as a docs typo; `BOOTSTRAP.md` section 2.5 has required
  since the FIRST COMMIT that `verify_env` assert the RESOLVED interpreter can import pytest and
  ruff and HARD-fail if it cannot, and nothing did. CS-442 was filed on one dead citation; the
  item was that NOTHING IN THE REPOSITORY READ `docs/` at all.

- **CS-806's detail block was SUPERSEDED and the ledger says so.** It told the closer to "decide
  whether that contract is the right one" - but the contract had already been decided in
  `BOOTSTRAP.md` 2.5 before any code existed, so it was not a live design question. Both detail
  blocks now carry a CLOSED marker in `docs/history_notes.md` so neither reads as a live
  instruction again.

- **CS-442's population is EIGHT, not the recorded seven, and the eighth is the shape the item
  itself predicted would be missed.** `test_the_header_scan_advertises_no_bound_it_cannot_enforce`
  is cited by the CS-436 entry BARE, with no path, so a `path::name` scanner is structurally
  blind to it. Its target is not an inference: `ee36d0d`, the CS-436 commit, added it alongside
  the live sibling the same Verification field cites. The "seven is a FLOOR" caveat is discharged.

- **A NINTH CANDIDATE WAS REJECTED, and the near-miss is the lesson.**
  `clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES` reads dead to any resolver
  that looks for `def` alone, and is a live module-level CONSTANT. It was briefly counted as an
  eighth dead citation off a TRUNCATED `grep` whose first ten hits were all worktree copies.
  Checking the tracked file directly is what reversed it. Same artifact class the item already
  recorded on the `file:line` arm, arriving on the other one.

- **A TRAP FOUND THIS SESSION THAT WAS RECORDED NOWHERE: a citation can assert an ABSENCE.** The
  CS-411 correction record cites a dead name ON PURPOSE - `grep -c` returning 0 IS its evidence -
  so a checker that reddens on every dead name reddens on a record doing exactly the right thing.
  That is the `DELIBERATE` disposition in `tests/test_docs_citations.py` and it is load-bearing.

- **Decisions: no ADR. Two dispositions recorded that must not be re-opened as questions.**
  CS-442's class-3 citation gets NO TARGET, because CS-441 records 26 of 46 spliced shapes still
  escaping - assigning one would launder an aspirational claim into a verified pointer. And
  `docs/history_notes.md` is deliberately NOT guarded, because its detail blocks QUOTE dead names
  while discussing them; that is CS-809, not an oversight.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** The opposite - `BOOTSTRAP.md` 2.5 was
  RIGHT and the code was behind it. Two tracked docs were corrected against ground truth per
  CLAUDE.md section 8: `docs/OPERATIONS.md` claimed "`py -3` is equivalent on this machine",
  which was false and contradicted 2.5; and CS-806's own detail block, above.

- **Failed paths, so they are not retried:** a naive `path::name` census that resolves only `def`
  manufactures a false finding on a live constant. A `file:line` arm that judges an unqualified
  basename manufactures six. Neither is a checker bug to fix later - both are DECLINED-and-printed
  by design now. Also: the harness bash heredoc ate backslash escapes FOUR separate times this
  session, silently corrupting patch scripts; the working answer is the Write tool, every time.

- **In flight: NOTHING.** Working tree clean, nothing unpushed, both CI runs green. The four
  pre-existing worktrees (CS-492 rounds seven to nine and the two-site spike) and branch
  `cs807-attribute-half` are UNTOUCHED and still unmerged.

- **Next action: CS-702, but it is BLOCKED ON AN OPERATOR GRANT and must not be started without
  one** - `.githooks/commit-msg` is frozen. If the grant is not forthcoming, take CS-809 or
  CS-810, which are CS-442's residuals and need no grant.

## Session 29 - 2026-08-22 - CS-807's sweep is TAKEN and sizes the item at SIX; an attribute-half repair was built and REFUTED by three independent lenses

- **Shipped: NOTHING CLOSED. Third session running.** CS-807 stays OPEN, CS-492 was not
  touched, and CS-808 was FILED. Two commits, `77336e5` and `6547f9f`, both DOCUMENTATION
  ONLY - zero `.py` files were touched in `main`. `docs/LEDGER.md` carries a NON-CLOSURE
  record and says so in its heading.

- **THE SWEEP IS TAKEN, and it was the right first action because it changed the item's
  size.** CS-807's detail block named it the cheapest next step and recorded the answer as
  unmeasured. The answer is **SIX false declarations, not four, in TWO modules rather than
  one**: `backing_citations` and `dead_full_citations` in `tests/save/test_absolute_claims.py`
  are the new pair, and **both are HELPERS rather than tests**, so the population is not
  confined to test functions the way the first finding implied. 45 exemptions in 11 modules,
  20 graded entries in 7; the graded channel is CLEAN. No consumer of the guard exists
  outside `tests/save`. **Six is a FLOOR, not a total.** Full tables in
  `docs/history_notes.md` under **CS-807 - detail**.

- **TWO INDEPENDENT METHODS AGREED ON THE SAME SIX and the second never reads a reason
  string** - it takes the call node the guard trips on, resolves the callee one hop, and asks
  whether that target reaches. One phrase match was REJECTED on inspection:
  `test_workdir::test_latest_save_returns_none_when_nothing_resolves` matches "no path at
  all" but genuinely calls the locator.

- **In flight: branch `cs807-attribute-half` at `72f0f2c`, base `77336e5`, REFUTED and NOT
  MERGED.** +242/-25 across three files. The working tree is CLEAN and nothing is unpushed;
  the branch is the only artifact. The four pre-existing worktrees (CS-492 rounds seven to
  nine and the two-site spike) are UNTOUCHED.

- **Failed paths - the whole of the repair attempt, and the framing that produced it.** The
  sweep showed the six splitting by mechanism: four on the bare-name arm already measured
  irreducible, two on the ATTRIBUTE arm where `_callee_resolves` discards a receiver the
  import table resolves without type resolution. **That was reported as the tractable half
  and it is not.** Two narrowings were built and both were refuted, both for reading an
  ABSENCE as evidence of safety - the first that the sibling exported no reach, the second
  that a def's own body names no primitive. **Do not take a third of the same shape without
  an answer to that root cause.**

- **THE GRADING WAS DONE BY THREE AGENTS THAT DID NOT PRODUCE THE BUILD, and all three
  returned REFUTED.** Permissive-failure found seven escapes, each caught on the parent
  commit and silent on the build. Control-validity found the build's anti-vacuity control
  passes with `_assert_library_reach_is_declared` gutted to a bare `return`, with ZERO unique
  detection against a 16-mutant battery. Claim-accuracy found `_module_handles`' docstring
  stating the polarity of the REFUTED first spike, and a FOURTH reach-computation site.

- **Surprises: NO SPIKE CONTRADICTED `BOOTSTRAP.md` this session.** But two measured facts
  contradicted a TRACKED DOC and the doc was corrected per CLAUDE.md section 8: ROADMAP's
  CS-807 acceptance said "the four exemptions in `test_oracle_citations`" and the sweep says
  six across two modules; and this session's own claim that the attribute half was tractable
  was refuted by its own grading and is now fenced in the detail block.

- **Two defects worth carrying forward whatever happens to the direction.** The exoneration
  was keyed on a bare receiver name with NO SCOPE CHECK, so a PARAMETER spelled like a module
  handle silences `Path.resolve()` on a real account directory - and
  `tests/save/test_absolute_claims.py:192` already binds `citations` as a handle, so that is
  a rename away rather than contrived. And `_module_scope_reaches` asks the same reach
  question as the three sites `grep -n "_calls_any("` finds, so the identical call at module
  scope MANUFACTURED a `<module scope>` declaration on a module reaching nothing - the CS-807
  defect inside the CS-807 repair. **Count the sites from the source, not from that grep.**

- **THE CONTROL LESSON IS THE MOST TRANSFERABLE THING HERE: a control written to defeat
  vacuity was itself vacuous.** It swallowed the guard's own "vacuous" message through an
  `if "vacuous" in said: return` branch and so passed WITHOUT EVER OBSERVING THE GUARD REACH
  A VERDICT. The symmetric instrument it declined to use is
  `assert not _module_reaches(consumer)`, which a gutted guard cannot satisfy and which kills
  two of the surviving mutants. The companion escape control graded as a REAL instrument with
  a clean unique kill, so the pair was half sound.

- **What survived grading, and is reusable.** The two exemption deletions are CORRECT,
  verified by reading `backing_citations`, `dead_full_citations`, `citations.resolve` and
  `prose_paragraphs` end to end rather than by running the guard. No shipped module goes
  silent on the build today; every escape found is prospective.

- **Decisions: no ADR was recorded.** The fences are in `docs/history_notes.md` under
  **CS-807 - detail** and in the ledger entry.

- **Next action: CS-442 or CS-806, NOT a third narrowing of the attribute arm.** CS-807 has
  now consumed a sweep and two refuted builds, and the direction needs an operator decision
  about which side its acceptance buys before more work goes into it.
