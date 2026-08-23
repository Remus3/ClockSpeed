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
