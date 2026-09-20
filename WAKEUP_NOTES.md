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
## Session 109 - 2026-09-19 - the file half of the walk, and a table that turned out to be a second authority

- Shipped: CS-1155 (closed), CS-1158 (filed). Detail in docs/LEDGER.md, not here - and that
  file carries TWO records for CS-1155, the second correcting the first, because it is
  append-only and the first record's central sentence was disproved hours after it landed.

- CS-1155 WAS THE FILED NEXT ACTION AND IT WENT AS FILED, then took three rounds. The note
  carried a measured reproduction, so the first move was a failing test rather than an
  investigation, and `tools/drift_guard.py::_walk` had a file half within the hour. Every
  round after that came from an adversary or the adjudicator, and each one found the
  previous round's stated REASON false rather than its behaviour wrong.

- THE FIRST BUILD WAS A RESTATEMENT AND ALL THREE ADVERSARIES SAID SO. It answered with a
  table of three shapes copied out of `.gitignore` - which were exactly the three ignored
  files lying on this machine's disk that day. `.gitignore` carries some thirty more. The
  grading was one-directional: every arm asked whether each table entry was ignored by git,
  none asked whether git ignored a shape the table lacked, so the table could fall
  arbitrarily far behind its source and stay green. Parity was a SNAPSHOT, not a property.
  `_git_ignored` asks git directly now - `git ls-files --others --ignored
  --exclude-standard --directory`, which answers with NO COMMITS AT ALL, and the empty
  index is precisely the case the walk exists for.

- THEN THE ADJUDICATOR DISPROVED THE SENTENCE THAT JUSTIFIED KEEPING THE TABLE. "It is only
  the floor for a tree with no git" was the whole answer to the section-4 objection, and it
  was false: the floor was consulted FIRST, so on a tree where `build.log` was TRACKED and
  git ignored nothing, the walk dropped it anyway. The repair is a three-state answer -
  NONE for a git that could not be asked, an EMPTY SET for a git that said nothing is
  ignored, and NOT PASSED for "ask git yourself". The first build collapsed the first two,
  which is exactly how a floor becomes a second authority.

- Decisions: no ADR, no frozen-file grant. CS-1158 filed rather than absorbed, and its note
  says why: whether a FILENAME is personal data under this repository's own classification
  is not something CLAUDE.md answers in either direction, and that answer belongs in an ADR
  rather than in a redaction call site.

- Surprises: nothing contradicted BOOTSTRAP.md. What did surprise: a `.log` is NOT read by
  the character-set guard - `_classify` refuses it unopened - and this module has no secret
  reader at all. The item's own filed motive sentence was false on both halves, and it had
  been copied into three authored places before anyone measured it.

- Failed paths: a multi-edit patch script that asserts part-way writes NOTHING, so the
  follow-up patch lands on the original file. Four edits went silently missing that way and
  the half-repair passed ruff, ruff format and mypy at 276 files. Only a behavioural arm the
  adjudicator had demanded caught it. Also: a detached suite redirected into the REPOSITORY
  ROOT left two untracked files there and reddened four whole-suite arms as if they were
  defects - including the new parity arm, which was doing its job.

- THE ONE THAT REPEATS. A CS-1156 arm went red on ubuntu last session because its control
  named a Windows-only value. This session the SAME fault arrived inverted: the case arm
  asserted agreement with git, which is right, but on a case-sensitive checkout git says
  not-ignored and a walk that pruned NOTHING satisfied both the assertion and its own
  control. tier 1 is ubuntu only, so the arm written to stop a platform-specific control was
  itself dead on the only runner that grades it. It is parametrized over `core.ignorecase`
  now - a config value, not a filesystem property, so both halves run everywhere.

- Next action: pick up CS-1158. Its note carries the measurement and names the open
  question the fix must settle first.

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
