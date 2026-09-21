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
## Session 110 - 2026-09-20 - the inbox turned into a credential incident, and four guards that could not fail

Operator directed: read the moon-sync inbox and implement, reply, monitor, loop. Mid-session
the operator granted the standing shape - caveman-ultra, batched checklist, adjudicate
rather than ask, always deliver a reply - and reaffirmed full authority. Both are filed in
`memory/full-authority-adjudicate-do-not-ask.md`.

CLOSED: CS-1159, CS-1161, CS-1162, CS-1164.

**CS-1159 - the hook that took every shell down with it.** `.claude/settings.json` wired
both hooks by a CWD-RELATIVE path. One `cd` into `moon_sync_inbox` to read notes denied
every Bash and PowerShell call in the main session AND in four dispatched subagents, which
inherit the cwd. They each lost their shell for a whole run and returned UNVERIFIABLE.
`cd <root> && <cmd>` was refused too - the hook fires before the command, so the shell
cannot recover itself. It DEFEATED the gate's own written contract, which promises exit 0
on its own error precisely so this cannot happen: that branch is unreachable when the
script is never entered. RC broadcast this exact defect, mechanism and fix to all five
trees on 2026-09-13. CS did not act on it. Seven days later it cost a day of measurement.

**CS-1162 - citation rot, and it was a recurrence against a shipped guard.** CS-1159's own
adjudicator record says "a line pointer into a living document is a citation with a shelf
life" - and a later record under the same ID did it three more times. The rule now lives in
`docs/LEDGER.md`'s Entry-shape table. CS-1163 files what the guard still cannot SEE: a bare
continuation pointer following a full citation is invisible to `LINE_POINTER_RE`, 67 of them
across 8 files, 47 in two carriers whose own rules forbid editing them in place.

**CS-1164 - CHANNEL v2.** CS reopened the v1 pin at 1447 naming RC as author, then lagged
its own round while four trees moved, and was the LAST outstanding carrier. Vendored at
`fc22e86e...`, 25425 bytes, hashing equal. The round caught a latent defect in CS's arms,
not just its prose: CS had conflated PARTICIPANT with PIN-HOLDER, and at v1 the two counts
were equal so the wording read correctly. A sentence that is accidentally true is not a
guarded sentence.

**THE CREDENTIAL INCIDENT.** LL asked CS to look at one file in the shared git-install
scratch bucket. CS looked at the directory and found an Anthropic ADMIN-family key in
plaintext, ten days old, in a world-readable location, in CS's own litter - plus 17 world
names, the account name in 19 files, and the operator's email in two. The operator rotated;
persistence verified at MACHINE scope by hash. The render defect was HISTORICAL, closed by
CS-1156 the day before. What was LIVE was that no control could have caught it: CS's secret
scanner has NO rule for that family and its coverage is ACCIDENTAL and spelling-dependent;
the outbound canary is ONE family certifying ten; every credential population is
repo-scoped, so nothing sees a file that is never committed; and `PLACEHOLDER_RE` can
silently neuter any rule and already has. Filed CS-1166 through CS-1169. All four siblings
answered CS's ACTION note and all four said they have no never-committed control either.

**THE REUSABLE LESSON, and it is against CS.** Three trees swept that bucket - RSC, LW,
CS - and all three measured SIZE. CS had the directory open twice and read not one file.
A sweep that measures a directory without reading it produces a number, not a verdict.

**CS-946 - joined the lane bucket**, reversing ADR-0017 by operator ruling. Two frozen-file
grants, both recorded BEFORE their edits. The second turned on a fact nobody had: ruff
resolves `exclude` and `per-file-ignores` against THE INVOCATION'S WORKING DIRECTORY, so a
gate that lints a temp copy can never honour a project exemption - exit 0 on the real path
and exit 1 on identical bytes in temp, same minute. The section 14 licence gate CLEARED,
with two uncomfortable facts in the register row rather than smoothed over.

**CS-1165 - the roster is DERIVED now**, and it immediately found a SECOND unregistered
vendoring nobody knew was owed. The old hand-maintained dict could only grade what somebody
remembered to add, so it reported green over both files for their entire lifetimes. Its
acceptance is NOT met and it stays open: a lift with no byte pin AND no register row is
still invisible.

**WHAT CS PUBLISHED AND THEN WITHDREW, four times.** "51/14 copies" (carrier count is 4 -
the figure counted worktree duplicates with no declared population). "Narrowing
`max_concurrent_lanes` is a visibility cap, not an appetite cap" - FALSE, it is both, and
SS's document was right; CS corrected a correct document with a wrong denial. "210 files /
6,245,048 bytes" - does not reproduce under the marker set CS can write down (169 /
5,986,621); an attribution count is a function of its marker set and one published without
its regex is unfalsifiable. And the routing of `rm339_dangling.json` to RC.

Twelve notes delivered, privacy gate CLEAN on every one. 44 inbox notes read in the second
sweep alone.

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
