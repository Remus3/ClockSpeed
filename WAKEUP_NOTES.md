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

## Session 33 - 2026-08-22 - CS-823 CLOSES and takes a SECOND, unfiled escape with it; then an adversary refuted this session's own suite and SIX wrong hooks passed it

- **Shipped: CS-823 CLOSED. Filed CS-824.** Three commits. Detail in `docs/LEDGER.md`, not here.
  One frozen-file grant was issued, adjudicated and recorded in its OWN commit BEFORE any edit.

- **THE ITEM WAS FILED AS ONE ESCAPE AND CLOSED TWO.** `.githooks/pre-commit` ran the gate and took
  its whole decision from `$?`. Re-measured rather than inherited: truncated to 2368 lines, to 1
  line, and emptied, a staged em dash COMMITTED every time - exit 0, HEAD moved, ZERO bytes of
  stderr - against an intact control refusing with exit 1 and 576 bytes. 1020 of 2396 line-boundary
  prefixes compile, because the gate ends in a `__main__` guard.

- **THE SECOND ESCAPE WAS LIVE ON `main` AND NOBODY HAD FILED IT.** The CS-703 probe validates the
  `-c` invocation shape; the gate is invoked as a FILE. A four-line `sh` wrapper that delegates `-c`
  and exits 0 otherwise answers BOTH probe halves HONESTLY - it prints the computed token and
  returns 97, both measured - and never runs the gate. With it set, the em dash COMMITTED through
  the tracked hook. **Found by the ADJUDICATOR, not the builder, and believed only after being
  reproduced here.** It is the pre-commit twin of CS-819's silent-interpreter defect, and CS-703
  neither closed it nor claimed to.

- **THEN AN ADVERSARY REFUTED MY OWN SUITE AND THAT IS THE SESSION'S REAL LESSON.** The claim was
  that no wrong implementation could pass the 14 arms. SIX did. The sharpest -
  `grep -F "$CS_GATE_PASS" | tail -n 1` - keeps the declared pattern BYTE-IDENTICAL and changes only
  which line it is applied to. It has NO DEAD CODE and is exactly what a "make it less brittle" edit
  looks like. **The hook's own comment asserted the property that mutant violates, and no arm
  exercised that sentence.** Two arms were added and PROVEN to kill the survivors in a mirror, each
  mutation asserted to have LANDED first. **A GUARD'S COMMENT IS NOT A TEST, and a suite written by
  the person who wrote the guard tests the guard they MEANT to write.**

- **Decisions: no ADR. Fenced.** The banner check is an ANCHORED `case` pattern, both ends, only the
  two counts wild - NOT a prefix and NOT containment; the prefix version was built first and three
  of five adversarial gates passed it. Exact equality is unavailable rather than declined, because
  the counts vary and the gate is frozen, so the CS-703 exact-equality fence is untouched and still
  governs the PROBE. The captured stdout is RE-EMITTED rather than consumed - the opposite of
  CS-819 - because it carries the CS-209 coverage-skip lines, the channel that says detection was
  REDUCED. The CR strip stays even though it is an EQUIVALENT MUTANT on this toolchain.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Three things contradicted ME.** The designed fix
  I inherited said "require the banner" and a plain prefix test was too weak - measured. My section
  banner called the `gate_compiles` assertions "why these arms mean anything"; ablation says they are
  INERT today, and the sentence is rewritten in the tree. And I told the operator CS-413 was the
  item that makes a save's properties readable; its detail says the decode ALREADY LANDED and what is
  open is evidence quality. All three corrections are in tracked files.

- **Failed paths, so they are not retried.** A PREFIX test on the last line - refuted by measurement.
  Judging that stdout is non-empty, or counting its bytes, or matching the gate's NAME - all three
  are live survivors an adversary demonstrated, and all three are now killed. And the harness bash
  heredoc ate backslash escapes AGAIN, on a python payload this time; the Write tool is the answer,
  every time, and this is the SIXTH session it has cost.

- **THE PRODUCT PATH IS SHORTER THAN THE ROADMAP MAKES IT LOOK, and this is the most useful thing
  here for the next session.** CS-500 - the advisor - is blocked on CS-413; CS-413's own detail says
  CS-420, CS-421 and CS-422 carry its acceptance; CS-420 and CS-422 are CLOSED. **CS-421 is the ONLY
  item between this repo and the advisor.** Its open clause is the endianness question settled
  against something that is not this project's own writer. It is NOT small - 5712 lines of
  byte-order and value-anchoring machinery already exist across
  `tests/save/test_byte_order_status.py` and `tests/save/test_value_anchoring.py`, it carries FOUR
  fences, and route (b) shipped without closing it.

- **In flight: NOTHING from this session.** Working tree clean. The four pre-existing worktrees
  (CS-492 rounds seven to nine and the two-site spike) and branch `cs807-attribute-half` are
  UNTOUCHED, exactly as sessions 31 and 32 left them.

- **Next action: read `docs/history_notes.md` under CS-421 - detail, - status history and - fences
  BEFORE touching anything, then take CS-421.** Or ask the operator to revise the 2026-08-15 ruling:
  it says phase 5 waits until a record's properties can be READ, and they can be - the blocker has
  quietly become decode CORRECTNESS, which is a different claim and theirs to weigh.

## Session 32 - 2026-08-22 - CS-703 and CS-819 both CLOSE after FOUR refutations, and the transferable finding is that a probe validated one channel while every gate read another

- **Shipped: CS-703 and CS-819 CLOSED. Filed CS-815, CS-816, CS-817, CS-818, CS-820, CS-821,
  CS-822, CS-823.** Detail in `docs/LEDGER.md`, not here. **TWO ITEMS CLOSED AND EIGHT FILED, and
  seven of the eight are defects in things already green and already reported done.** Two frozen-file
  grants were issued, adjudicated and recorded BEFORE any edit, in their own commit.

- **THE HEADLINE IS NOT THE ITEM AS FILED. CS-703 was reported as an environment-variable problem
  and it never was one.** The repaired probe's FIRST build validated STDOUT while every gate decision
  in every hook reads `$?`. A wrapper that forwards stdout faithfully and drops the exit status
  therefore answered the probe with the exact token and turned all three tier-0 gates into no-ops -
  and it reached that through the ladder's own `python` rung **with no environment variable set at
  all**. Two ordinary shapes do it and neither knows the token: a POSIX wrapper ending in `| cat`,
  and a Windows `.cmd` using `setlocal`/`endlocal`. **A PROBE THAT VALIDATES ONE CHANNEL WHILE THE
  CONSUMER READS ANOTHER PROVES NOTHING**, and that is the sentence to carry forward.

- **FOUR REFUTATIONS, NOT ONE FROM READING THE CODE.** Every one came from an agent RUNNING it, with
  real commits and real pushes. Round one: the stdout/exit-code split above. Round two: the
  commit-msg hook FAILS OPEN under MSYS2 dash, which became CS-819. Round three attacked the SUITE
  rather than the hooks and killed three mutants. Round four found CS-823 and one message defect.

- **THE MERGER'S OWN ORACLE SHARED THE SUITE'S BLIND SPOT, TWICE, AND THAT IS THE METHOD LESSON.**
  It graded the first build 15/15 while four escapes were live, because every substitution arm used
  `true` - which fails at the stdout comparison and never reaches the exit-code question. It also
  drives real git, which on Windows is bash, the one shell where the dash fail-open is invisible.
  **A harness that cannot reach a channel cannot grade it.** Both gaps are closed; it now runs 23
  arms, 6 of which fail against the pre-repair hooks.

- **Decisions: no ADR. Four that must not be reopened.** The probe demands BOTH a computed token and
  a returned failure code; a set-but-broken `CLOCKSPEED_PYTHON` is REFUSED rather than silently
  replaced, which exceeds the filed acceptance and was an OPERATOR instruction, recorded as such.
  Exact equality beats containment because **a loud false refusal beats a silent false accept in a
  gate**. CS-819 ships a SENTINEL rather than moving the program into a file, because an empty file
  exits 0 just as silently - it removes a cause without establishing the invariant. And no heredoc
  size guard: 4096 is one dash build's property, so a size assertion is a proxy for the property
  rather than the property.

- **Surprises: nothing contradicted `BOOTSTRAP.md`. Two things contradicted ME, and both corrections
  are in tracked files rather than only here.** I reported CS-819 as affecting "most Linux
  developers"; that is REFUTED by this project's own CI - `tier1` run `32601774702` at `32a982c`
  ran on ubuntu-latest, where `/bin/sh` IS dash, with the over-threshold body, and 23 commit-msg
  tests with no skip markers passed every violation class. It is MSYS2-only and LATENT. Separately
  the CS-703 detail block named `env` as passing the old probe; it does not on this toolchain, and
  `echo` does and was unnamed. Both corrected per CLAUDE.md section 8.

- **Failed paths, so they are not retried.** A probe that reads only stdout - refuted by measurement,
  above. A byte-identity check scoped to the probe alone leaves the refusal block unpinned, and two
  mutants survived in exactly that gap. Message-content arms hardwired to ONE hook let a grant
  condition be deleted from the other two with the suite green. And the harness bash heredoc ate
  backslash continuations AGAIN, silently, on a patch script - the Write tool is the answer, every
  time, and this is the fifth session it has cost.

- **CI CAUGHT A DEFECT THAT THE LOCAL SUITE AND THE PRE-PUSH HOOK BOTH PASSED, and it is the last
  lesson of the session.** `be5cd81` was green locally at 2464 passed and green through the whole-suite
  pre-push run, and `tier1` was RED on it: six failures, one cause. Both dash platform arms encoded
  **"dash truncates the heredoc"**, which is false - the truncation is a property of the MSYS2 BUILD,
  not of dash. On `ubuntu-latest` the program ARRIVED, every rule fired correctly and reported its own
  reason, and the arms read CORRECT BEHAVIOUR as a broken premise. The hooks were never wrong on either
  shell; the acceptance was. **A PLATFORM PREMISE BAKED INTO A TEST IS THE SAME DEFECT CLASS AS A HOOK
  THAT TRUSTS A NAME** - an assumption asserted rather than measured - and the fix is the same: measure
  the property at run time and branch on it. Fixed in `a2a89ed`; both branches now assert something
  true and neither is a skip.

- **THAT FAILURE DISCHARGED A RECORDED RESIDUAL, which is the one good thing about it.** The CS-819
  grant listed "whether glibc dash delivers a heredoc above 4096 is INFERRED, not measured" as open.
  The CI log measures it: **4535 delivered bytes**, against 0 on the MSYS2 build. The delivered-bytes
  control the adjudicator insisted on is what measured it, by FAILING LOUDLY rather than passing
  quietly, on the first CI run after it shipped.

- **A PROCESS MISTAKE WORTH NOT REPEATING: I pruned the builder's worktree before CI was green.** When
  CI went red the agent that knew the module could not be resumed - its worktree was gone and the
  fallback directory was outside the session's fences. **Do not prune a worktree until CI is green on
  the commit that merged it.** The repair was done in the main checkout instead, which was fine here
  only because the diagnosis was precise and the change was one file.

- **A DEVIATION RECORDED RATHER THAN CLAIMED MET.** Both grants ask that `scripts/install_hooks.py`
  run clean. Its `inspect_hook` was run over all three hooks and passed; the WHOLE script was not,
  because `install()` writes `core.hooksPath` RELATIVE where this machine holds it ABSOLUTE - from a
  worktree that repoints hook resolution to that worktree's own copy, which would let an agent
  editing a hook disarm the gate judging its own commit. Changing the operator's git configuration
  was not a side effect these items were entitled to take.

- **In flight: NOTHING from this session.** Working tree clean. The four pre-existing worktrees
  (CS-492 rounds seven to nine and the two-site spike) and branch `cs807-attribute-half` are
  UNTOUCHED and still unmerged, exactly as session 31 left them. One NEW worktree,
  `agent-ab7fcd5c63f9193ea`, is fully merged and prunable.

- **Next action: CS-823.** It is tier 1, the fix is already designed and measured, and it needs a
  frozen-file grant for `.githooks/pre-commit` before a line is written. `pre-commit` runs the gate
  with no proof of execution, so an empty or truncated `tools/precommit_gate.py` passes it silently -
  and 1019 of 2395 truncation points still compile.

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
