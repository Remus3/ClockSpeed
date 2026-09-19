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
## Session 108 - 2026-09-19 - the walk that pruned by luck, and two secrets-in-the-open the adversaries found on the way

- Shipped: CS-1153, CS-1155 (filed), CS-1156, CS-1157. Detail in docs/LEDGER.md, not here.

- CS-1153 WAS THE FILED NEXT ACTION AND IT WENT AS FILED. `tools/drift_guard.py::_walk`
  prunes by its own rule now - a relative-path set with a reason per entry, the `.git`
  boundary marker, and git's worktree registration. The adversarial pass REFUTED the first
  build on three counts, and the third is the one worth carrying: a SUPERSET assertion over
  skip records cannot see an OVER-BROAD prune, so widening an entry to `ops` or `shell` -
  tracked, authored, guard-graded trees - left every arm green. The repair asks git about
  every entry in the real tree and grades the WEAKEST member.

- THE TRAILER RULE WAS BEING DEFENDED BY HAND, EVERY SESSION, AND NOBODY HAD NOTICED.
  CS-1157. `.githooks/commit-msg` has always REFUSED a `Co-authored-by` trailer, so one
  never landed - but the harness injects an attribution instruction into every session, and
  the only thing between that instruction and a refused commit was a model reading a memory
  note and declining. Sibling LL set the two settings keys on 2026-09-06 and does not have
  the problem. Both keys are set now, at repo scope AND user scope, and the effect was
  MEASURED live: the injected instruction flipped polarity in-session, no restart.

- Decisions: no ADR. One frozen-file grant, adjudicated and recorded in docs/LEDGER.md
  BEFORE the edit, per CLAUDE.md section 6.

- Surprises: nothing contradicted BOOTSTRAP.md. Three measurement traps did bite, and all
  three are the kind that make a green mean nothing.
  (1) A pytest traceback renders a `subprocess.run(env=...)` frame's WHOLE environment dict,
  and this machine's `sk-ant-` admin key printed in full in a suite log. That is CS-1156.
  (2) pytest TRUNCATES a long dict repr, so a variable added last falls outside the rendered
  portion - the first CS-1156 arms planted there and measured nothing while passing.
  (3) A child pytest whose rootdir sits deep under the home directory renders stdlib frames
  as RELATIVE paths, so no home path is emitted at all. An arm using the home placeholder as
  its control was therefore measuring how deep a temp directory happened to be.

- Failed paths: `pytest_collectreport` written as a `hookimpl(wrapper=True)` raises
  INTERNALERROR - that hook is HANDED a report rather than building one, so the yield gives
  the hook's combined result, a list. Use `tryfirst` and mutate in place. Also: a
  `Start-Process ... -NoNewWindow` suite dies with the tool call that launched it, and so
  does one launched and awaited in the SAME call once the 10-minute cap fires - launch in
  one call, wait in the next, `-WindowStyle Hidden`.

- THE ONE THAT COST A CI CYCLE. A CS-1156 control asserted `ALLUSERSPROFILE` appeared in a
  child report, to prove the environment dict had reached it. That variable exists on every
  Windows machine and on no ubuntu runner, so the whole suite was green here at 9143 passed
  and tier 1 went red on three arms for a reason with nothing to do with redaction. A
  control naming a platform-specific VALUE grades the platform, not the mechanism. The
  marker is a frame local's NAME now - the channel the secret travels through.

- Next action: pick up CS-1155, whose note already carries a measured reproduction.

---
## Session 107 - 2026-09-19 - an operator-directed machine stray-work sweep, and the one defect it turned up

- Shipped: CS-1154, closed. CS-1153 filed and left OPEN. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing half-done. The sweep report is delivered to all four sibling inboxes as
  `2026-09-19-1430-from-CS-REVIEW-e085b4a92ab2-machine-stray-work-sweep.md`; RC merges the five
  reports and the operator adjudicates before any deletion pass. NOTHING was deleted, moved or
  renamed anywhere on this box by this session.
- Decisions: no ADR. The sweep proposed a PRUNE / MOVE / KEEP / UNKNOWN class per row and
  actioned none of them; that is the operator's call after the merge.
- Surprises: THE SWEEP FOUND A LIVE DEFECT IN THE SUITE, not in the tree it was inventorying.
  `git -c core.hooksPath=.githooks push` exports its override through `GIT_CONFIG_PARAMETERS`,
  every git child inherits it, and a command-line override OUTRANKS repository configuration -
  so every throwaway repo in `tests/test_precommit_gate.py` lost the `core.hooksPath` it had
  just set and NO HOOK RAN. The world-name PII arm accepted the commit it exists to block,
  three pushes running, with `returncode=0` and an EMPTY stderr. The empty stderr is what
  settled it: that gate prints a PASS line on every run it completes, so silence is a hook that
  never fired, not a gate that approved. CS-1154 is the repair.
- Failed paths: the FIRST diagnosis was wrong and the ledger entry says so rather than quietly
  replacing it. The failure was attributed to a contended box - 21 python and 47 node processes
  from concurrent sibling sweeps - purely because it did not reproduce standalone. It
  reproduced three pushes running and never once outside the hook, which contention does not
  explain. Do not reach for load as an explanation before checking what the hook environment
  carries. Also measured and discarded: GIT_DIR contamination, both relative and absolute, and
  `-n auto` over `tests/test_precommit_gate.py` alone. None reproduce it.
- Process change, operator directive: the handoff is a FILE plus a Desktop shortcut, not a
  chat fence. `CS-NEXT-SESSION.txt` is tracked at the repo root, rewritten whole by every
  `/done`, rowed in `CLAUDE.md` section 4 and exempted from tier-1 budget guard (k) for the
  reason this file is. LL, LW and RC already carried that shape; CS was the one that did not.
- Next action: read `docs/item_notes/phase7.md` section CS-1153 and prune the gitignored and
  PII-bearing roots in `tools/drift_guard.py::_walk` by rule rather than by never being reached.

---

## Session 106 - 2026-09-19 - two rows ran, one closed and one was refuted by an adversary, and the publication gate got its first real closure scan

**CLOSED: CS-1147, CS-1146. REFUTED AND STILL OPEN: CS-900. FILED: CS-1152.**

**CS-1147 - the ration arm no longer races the child it measures.** The child called
`ration.release()` and THEN wrote its released marker, so a parent acquiring in that
window saw two of three protocol signals. Reproduced FIRST by widening the gap to 0.5s,
which gave the byte-identical CI assertion; the same widening passes after the reorder.
Then an adversary refuted my own done-claim on the first commit: I had verified teeth with
a LIVE never-releasing child (red in 124.89s) and called the clause discharged, but the
CANONICAL mutant - delete the release call, change nothing else - was GREEN in 0.15s both
before and after. The child EXITED the instant it stopped holding and the ration correctly
reclaims a dead holder's slot, so nothing in the arm told a release from a death. The child
now waits for a `parent_done` dismissal written after the measurement, so it is alive across
the parent's acquire. That mutant now fails in 120.33s. The same pass found a SECOND race of
the same family: `_await_file` returned the instant a path existed, and `write_text`
truncates before it writes, so both process arms could read an empty marker and die in
`int()` with an uncaught ValueError. It waits for a byte now.

**CS-1146 - and session 105's caveat against itself was WRONG ON ITS OWN NUMBER.** That
caveat de-ranked the row because "the very next tier 1 run had the guard shard at 230s".
Measured from the jobs API: that run was 413s and the next was 441s. With the record's 11
readings at 426-464, that is 12 of 13 known readings at or over the 420s budget, spread 38s.
The caveat's METHOD was right - measure the spread before ranking - and following it
reversed its own conclusion. `tools/tier1_growth.py` now grades `B >= M` per job as a verdict
distinct from the band-versus-jitter one, names each job with its own margin, and prints
BUDGET BREACHED by 44s over the shipped record. No level moved.

**CS-900 SHIPPED ITS TOOL AND STILL FAILED, on an adversary and not on my reading.** Two
counter-examples. (1) The save shard WARNS at both ends of the profile with the SAME top
test across four commits that touched only another job, so branch one closes only by
electing the LOOSER of two stated shares - and the 18.9 per cent concentration that FILED
the item passes the 50 per cent hard level. A level under which the filed defect passes
cannot be the level the close rests on. (2) The hard level's derivation was FALSE: the
`t_max <= T/W` criterion is against the SERIAL TOTAL and the tool divides by the STEP WALL
CLOCK, which agree only at one worker. Corrected in the docstring, not dropped. `T` is not
obtainable from a block printing only the top 15 phases over 5s, so that criterion cannot be
graded by this tool at all.

**THE PUBLICATION GATE GOT ITS FIRST REAL CLOSURE SCAN, and six of seven axes are CLEAR.**
Over everything reachable from `main`: 1059 commits, 3255 blobs, 461 DISTINCT HISTORICAL
PATH STRINGS - 42 more than HEAD, which is the half that leaks. No account id, no standalone
world name, no home paths, no save bytes, no game assets, no `data/` or inbox payload, in
ANY commit. The one finding is the plan's own credential allowlist drifting against its own
synthetic canaries, and the plan sentence asserting the real token prefixes return zero is
now the only carrier of those prefixes. The pre-rewrite safety bundle is taken, lives outside
the tree, and was graded by RESTORING rather than by verifying.

**PROCESS FINDINGS - MEASURED, DO NOT REDISCOVER.**

- A CONTENDED xdist SUITE REPORTS A SHORT GREEN, NOT A CRASH. Beside a running lane,
  `-n 4` reported 6407 passed and EXIT 0 while `--collect-only` said 9055 collected: 2641
  tests silently never ran, no MemoryError, no non-zero exit. The memory note predicted a
  MemoryError; the real signature this time was a clean short pass. A SERIAL run beside the
  same lane returned the full 9048. Check the count against a collect, always.
- THE PATTERN-LANGUAGE TRAP FIRED TWICE BEFORE THE SCAN EVEN STARTED. `git for-each-ref`
  with a globbed `refs/backup/*` returned 0 where the bare prefix `refs/backup` returned 71,
  and `git bundle list-heads` reported 242 refs where a bare `git clone` restored 144 and
  ZERO of the 53 wip refs. A bundle that VERIFIES is not a bundle that RESTORES.
- THE REPOSITORY'S OWN PII GUARD CAUGHT A PII DEFECT INSIDE PUBLICATION-PREP WORK. The
  pre-push hook refused the register slice because it rendered a caught exception OBJECT
  into an f-string, which is an echo path under non-negotiable 12.
- A NEW TEST MODULE CITED IN A GUARDED DOC READS AS A DEAD BARE PATH until it is at least
  intent-added, because `tests/test_docs_citations.py` resolves against the tracked file
  list. It cost a false red once.
- THE COMMUNITY-PROFILE ENDPOINT READS THE DEFAULT BRANCH ONLY, so a community-health
  acceptance cannot be graded from a slice branch. Its `issue_template` row reads null even
  though `.github/ISSUE_TEMPLATE/` exists with two files.

**A CORRECTION I OWE THE RECORD.** I told the operator mid-session that the publication
decision was "publish from a fresh squashed or orphan history". That is the 2026-08-13
record. The LATER ruling - CS-700 section 6, 2026-09-08, with ADR 0018 - is that the commit
graph is KEPT, IDENTITY ALONE is rewritten to the noreply address, the remote is deleted and
recreated, and `main` alone is pushed. Squash and accept-as-is were both put and DECLINED.
