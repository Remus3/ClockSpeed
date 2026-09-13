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
## Session 90 - 2026-09-13 - the claim store measured against the way a worker actually calls it, and three release designs refuted before one held

- Shipped: CS-1009 and CS-1009's blocked dependent CS-991. Detail in docs/LEDGER.md, not here.
- In flight: nothing. The tree is clean and the merge is one commit.
- Decisions: no ADR. One adjudicated ruling, recorded inside the CS-1009 ledger entry: a lane lock
  that reads RUNNING anchors its claim whether or not its holder can be proven, because
  `lanes.holder_is_a_stranger` already ruled that trade one layer down and a row is a smaller unit
  than a lane.
- Surprises: nothing contradicted BOOTSTRAP.md, so no update is owed. What did surprise: a sha256
  receipt over a record's own bytes is not a credential, because every lane can read every claim
  file - and the worker prompt's only documented recovery path WAS the attack.
- Failed paths: authenticating a release with a caller-supplied run id (run ids are policed nowhere);
  authenticating it with a receipt (forgeable by any reader); and requiring a lock to prove its holder
  before anchoring a claim (inverts the item wherever a start time cannot be read, handing a live
  cycle's row to the other lane). None is to be retried.
- Next action: CS-1008 - `tests/test_queue_loop.py`'s `_drive` injects neither the permit seam nor the
  claim-states seam, so those arms read the LIVE store and flip non-deterministically against a real
  lane. It is tier 1 and it is the last thing reading live state in a suite.

## Session 89 - 2026-09-13 - the dashboard lane's five prerequisites, and five new instances of the class they were built to avoid

- Shipped: CS-1000, CS-992, CS-994, CS-1005 CLOSED. CS-988's sweep landed as a measurement and the
  item STAYS OPEN. CS-991 and CS-993 merged but STAY OPEN, each blocked on a residual its own slice
  disclosed. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing. Tree clean. Eleven worktrees remain and are prunable except
  `C:/cs-worktrees/cs-lane-queue`, which is live lane infrastructure.
- Decisions: no ADR. **The operator granted the frozen-file exception on `.githooks/pre-push` and an
  adjudicator ruled DENY on the EDIT, so the grant is recorded GRANTED AND UNSPENT** - the CS-972
  shape on the same file. Two grounds: no wait ceiling is both useful and non-hanging, and the only
  working mechanics move a tier-0 gate's exit-code fidelity into a non-frozen module.
- Surprises, and it is the session's substance. **FIVE new instances of the CS-988 class were found,
  every one of them inside a repair built to catch that class**, and one landed in a slice whose
  brief forbade a floor BY NAME. The class is not caught by knowing about it. What caught all five
  was measurement: narrow the knob, run the suite, watch it stay green.
- Surprises, second: **two independent slices rooted worker-side state at the importing file**, so
  each lane's worker read its own private store and the two lanes were structurally blind to each
  other. One shipped a claim store where both lanes granted the same row. `lanes.REPO_ROOT` already
  resolved the indirection and neither used it. The driver-side / worker-side asymmetry is now
  recorded in the modules themselves.
- Surprises, third: **an arm written to prove exclusion hardcoded the defect away** by passing the
  very root the production path derives. Every arm was green, every mutation killed its target, and
  the feature was inert in production.
- Failed paths: the frozen-file edit (denied, grounds recorded); `PYTEST_ADDOPTS` injection to reach
  the hook's pytest (fails open and silent); holding the suite ration across the whole worker cycle
  (45:1 against the window it protects, and it would undo CS-992).
- Next action: CS-1009. Establish whether a claim survives the exit of the process that made it.

---

## Session 88 - 2026-09-12 - five operator questions answered, and three artifacts refuted BEFORE they shipped rather than after

- Shipped: CS-957 and CS-989 closed. CS-989 filed, granted and spent in one session. CS-945
  measured but STILL OPEN - it wants an arm and this was a measurement. Six branches holding
  single-copy work pushed to `origin`. CS position on the fleet refutation-cost consensus
  DELIVERED to all four peers, gate CLEAN. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing. Working tree clean, suite 7105 passed / 7 skipped / 0 failed, drift
  guard CLEAN with the one pre-existing `ROADMAP.md` budget WARN. Two builder worktrees
  (`cs957-account-name`, `cs989-prepush`) are merged and prunable; `cs-lane-queue` is live
  lane infrastructure and stays.
- Decisions: no ADR. **New standing operator directive: do NOT ask the operator to authorise
  a send or pick a direction - route a choice to an adjudicator or lane it through the sync
  box; writing outbound is allowed, into the sync inboxes only.** Recorded in harness memory.
- Surprises, and it is the session's substance. **THREE artifacts were refuted by an
  adversarial pass BEFORE they were used, not after.** The CS-988 scoping document lost 7 of
  8 claims; the outbound census lost 4 of 7 and would have published two wrong claims into a
  fleet consensus; and the pre-push proposal's placement was too wide and would have created
  a class of push running ZERO checks. All three refutations were cheap and all three landed
  before the cost was paid. That is the shape the fleet lane is looking for.
- Surprises, second: **CS-988's SCOPING DOCUMENT reproduced CS-988.** It argued its proposed
  shared backstop had no narrowable knob, then mandated a per-module map of counts that is
  exactly one, eleven modules deep. Fifth instance of the pattern and the first found in an
  ANALYSIS rather than a repair - the class reaches prose about the class. **CS-988 was NOT
  implemented; the cut line needs rework and building on a refuted scope was declined.**
- Surprises, third: **a decayed record nearly bought a rebuild.** CS-957 arrived as a
  BLOCKER; five of its six clauses were already shipped. Every NUMBER in its line re-derived
  exactly - only re-grading the acceptance against the shipped tree exposed it. Its one live
  residue was ROUTING, buried inside the false premise.
- Surprises, fourth: two guards were reddened by THIS session's own docs commits, invisible
  to the commit gate because it does not run the suite. A non-closure phrase not bound to its
  id by name, and four line pointers at tracked Python modules in - of all things - the note
  about record decay.
- Failed paths, do not retry: pinning floors for CS-988 (the fence holds, now with a fifth
  witness); the "free second derivation" of four identical `ls-files` spellings, which is
  three copy-pasted spellings of ONE command and is the trap, not a win; and treating a
  branch's `git cherry` reading as sufficient - patch-id is undefined for merge commits and
  tree identity plus content presence is what decides.
- **Measured and worth carrying: a pure-delete push now costs 0.56 s against an ordinary
  push's 352.84 s (a LOWER BOUND - that run was blocked partway; the nearest honest full-run
  figure is 623.38 s). The 7m46s / 7m00s / 7m31s figures from the session 87 handoff are
  recorded in NO tracked file, are marked UNMEASURED, and must not be requoted.**
- LATE IN THE SESSION, after the questions were answered: CS-990 filed (the CI workflows
  pin actions on a deprecated Node 20 runtime, already force-run on Node 24). CS-988's cut
  line REWORKED BY MEASUREMENT and its backstop REPAIRED and merged - both recorded in
  `docs/LEDGER.md`, and CS-988 still OPEN with the sweep owed. The reworked criterion is
  mechanical and is the durable part: a site is an instance IF AND ONLY IF, measured on
  disk, a one-line use-site narrowing REDUCES the collected arm count AND the objecting
  guard population stays GREEN.
- Surprises, fifth, and it kept going: the backstop repair's FIRST CUT was itself instance
  SIX - its equality arm graded REGISTRATION and could not grade the JUSTIFICATION for
  registration, so four of ten names were certified as pinned while nothing pinned them.
  The repaired version leaves instance SEVEN IN SHAPE (moving a key between the two
  registries is a one-line edit the equality arm cannot see), needing a second edit to do
  harm. Recorded against the item rather than closed.
- Surprises, sixth, and it applies to EVERY slice this project dispatches: `python -m mypy
  clockspeed` CANNOT SEE `tests/`, because naming a target REPLACES the `pyproject.toml`
  discovery list rather than narrowing it. A slice reported exit 0 on bytes carrying four
  `arg-type` errors that the repo-wide gate caught. Every brief here asks for the scoped
  form, so a builder writing a test module gets a green that structurally cannot see its
  own work.
- A subagent STOPPED MID-TASK and returned "I'll wait for the completion notification"
  instead of a report, with 482 insertions uncommitted in its worktree. The notification
  read like an ordinary completion. Checking the worktree rather than trusting it is what
  caught it; the work was snapshotted and the agent resumed by id rather than re-dispatched.
- Next action: **CS-988's SWEEP, using the reworked criterion** - the 15 UNMEASURED band-B
  rows plus the roughly 36 file-and-name pairs an AST scan found, measuring each rather
  than arguing it. Any equality arm must be measured in the PRIMARY CHECKOUT, never only in
  a worktree. Then CS-948, the remaining half of the outbound path.

---
## Session 87 - 2026-09-12 - twenty-one worktrees pruned, and one defect found four times, each instance made by the previous repair

- Shipped: CS-929, CS-933, CS-987 closed. CS-964's seam merged and the item stays OPEN.
  CS-987 and CS-988 filed. Detail in `docs/LEDGER.md`, not here.
- In flight: nothing. Working tree clean, `main` at `95cdce0`, pushed, tier1 CI read as
  `completed success`. Two worktrees remain and both are deliberate: the repo itself and
  `cs-lane-queue`, which is live lane infrastructure.
- Decisions: no ADR. Four operator questions are carried in the continuation prompt and
  none of them were answered here.
- Surprises, and this is the session's substance. **CS-988, the displaced knob: a value
  that decides what a POPULATION MEASURES, narrowable at its use site, guarded by a floor
  met EXACTLY.** Found FOUR times inside CS-929, each instance created by the previous
  repair - corpus root, the anchor pinning it, that anchor's use site reachable by
  concatenation despite being derived, the plant producer's own return. Every instance was
  a SILENT ARM-COUNT DROP (155, 452, 466 green while arms vanished). What finally worked
  is set EQUALITY against a second derivation sharing no constant with the first, plus a
  module asserting its own collected arm count. **Do not close CS-988 by pinning floors -
  a floor IS the defect.**
- Surprises, second: THREE unrelated instances of "an instrument that cannot observe its
  subject reports success for that reason alone" in one day - CS-987's thread oracle
  counting a process-global population, CS-964's fixture whose wideness nothing graded,
  and a builder's mutation probe blind to five of its own mutations. The merger hit it too
  when a quoted heredoc ate the backslashes out of a plant and the unmutated run printed
  `2 passed`.
- Surprises, third: a slice's green is a statement about its OWN SCOPE. The forgiveness
  ceiling broke only where two branches met; mypy broke only outside the slice's modules.
  Four adversarial passes and every scoped run missed both. The merged-tree whole-suite run
  is what caught them.
- Failed paths: pinning knobs. Three repair rounds added pins and each displaced the defect
  one level out rather than removing it - do not retry that shape. Also refuted and not to
  be rebuilt: CS-964's load-bearing claim (the field-specific session-only leak mutant is
  SYMMETRIC, killed 3 of 3 at both encodings) and CS-929's original acceptance requiring
  the CS-927 detector be widened (seven false positives, zero hits, measured in session 70).
- Next action: answer the four operator questions in the continuation prompt before taking
  any new item, because the first one decides whether 39 branches are work or litter.

---
## Session 86 - 2026-09-12 - a gate's routing was one third false, and the save reader learned a flag it already knew

- Shipped: NOTHING CLOSED. CS-829, CS-981, CS-982 and CS-983 all stay OPEN. Two mechanism
  landings and one routing, all recorded in `docs/LEDGER.md` as NOT A COMPLETION RECORD.
- Filed: CS-983 (the CS-G05 half-move), CS-984 (the world model publishes no struct
  interior), CS-985 (the suite writes save copies into the live work directory), CS-986 (a
  native-serialize struct tag whose interior still reads is unmeasured).
- In flight: nothing mid-edit. Main is committed and the tree is clean.

- CS-981'S OWN ACCEPTANCE CLAUSE WAS ONE THIRD FALSE AND GREPPING IT TOOK TWO MINUTES. It
  named CS-829, CS-830 and CS-831 as gated behind CS-G05. Only CS-829 ever had a section in
  `docs/GATED.md`; CS-830 closed NARROWED and CS-831 closed, both on 2026-08-23, and
  `tools/headless-queue.md` already said so in terms. The false premise and its own
  contradiction were sitting in the tree at the same time. GREP A PREMISE; DO NOT INHERIT
  ONE, including from a continuation prompt.

- Surprises: BYTE-IDENTICAL RELOCATION IS NOT FAITHFUL RELOCATION. Two of CS-829's fences
  cited "the rule at the top of this file" and "this file's opening rule". At their old
  address that was `docs/GATED.md`'s rule against synthetic closure; at the new address they
  resolved to nothing. An adversary found both. A self-referential citation is exactly where
  a verbatim move breaks, and the fix is to make the pointer absolute and say it was relative.

- Surprises: a constant the module DEFINED, folded into its own mask and STEPPED OVER was
  read by no line in `clockspeed/` or `tests/`. `TAG_FLAG_NATIVE_SERIALIZE` partitions the
  (14,60) container population exactly - every derived-width container carries it, every
  grammar-closing one leaves it clear. Eleven values were published under a width derived as
  region over count, and the derived width was the TRUE width, so nothing looked wrong. That
  is non-negotiable 7 inverted, and the merger repeated the "flagged and skipped" claim in a
  commit message without measuring it.

- Surprises: the disagreement counter went 803 to 0 and the honest reading was NOT that the
  fix was good. An adversary established it properly by showing the tag population conserved
  at exactly 7058 across both trees, so the 803 were decoded rather than relabelled into
  another counter. A decoder that stops disagreeing may be a decoder that stopped checking.

- Surprises: four mutants survived the whole 1486-test save suite, one on the line whose own
  docstring calls itself "the whole discriminator" and which is the evidentiary basis of
  every newly accepted value. A green suite of that size is not coverage of the line the
  result rests on.

- Failed paths: the merger briefed `_read_array_struct_tag` as a fault site. It is not. A
  (14,60) array of struct carries NO inner tag at all - an inner-tag read accounts for the
  element region on 0 of 6198, established by an offset sweep fronted by a known-good control
  on a synthetic payload that does carry one. The builder refuted the brief and was right.

- Failed paths: a repair brief that asked for `ruff check` and `ruff format` and not for
  mypy. The slice ran what it was asked, honestly, and merged main went RED on four
  annotation errors with 1500 save tests green on both sides. RUFF AND MYPY ARE DIFFERENT
  GATES; a brief naming one is not asking for the other.

- Decisions: `StructValue.disagreed` is NOT folded into `disagreeing_value_count` - that
  counter partitions the top-level tag population and CS-831 grades an identity against it.
  `ContainerValue.struct_word` stays None at these pairs; digging the word out of the type
  name is CS-829's measurement, not a decode slice's, and no consumer branches on None.

- Next action: CS-984. Publish decoded struct interiors through
  `clockspeed.save.world.WorldModel` WITH the property name attached, because a flat tuple of
  interiors cannot answer "which property held this" and the inventory join needs exactly
  that. `/api/map` serves an empty inventory until it lands.
