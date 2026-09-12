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


## Session 85 - 2026-09-11 - the operator asked for a map, and the save reader turned out to be the thing in the way

- Shipped: CS-977 (the `/api/map` endpoint and the Map panel), CS-978 (the placement and
  inventory models in `clockspeed/audit/`), CS-979 (extraction rates in the registry),
  CS-980 (the `(14,60)` property tag grammar, plus the license gate that ran before it).
  Detail in `docs/LEDGER.md`.
- Filed: CS-981 (route the three items gated behind a gate that is now discharged) and
  CS-982 (two flags bits pinned on almost no evidence).
- In flight: nothing mid-edit. The tree is committed.

- THE OPERATOR SUPPLIED GROUND TRUTH THAT REFUTED A DOCUMENTED GATE, AND THAT IS THE
  SESSION. `docs/GATED.md` recorded under CS-G05 that a `(14,60)` save decodes zero
  property tags and "cannot exercise the decoder at all - it is the CONTROL". The operator
  showed a third-party interactive map rendering container contents out of a save on this
  machine. Same file, same pair. The zero was real and reproduced on demand; the inference
  from it was wrong. A save that decodes nothing under ONE grammar is not a save that
  carries nothing. `CLAUDE.md` section 8 decided it: the probe wins, the gate is corrected.

- Surprises: the wall was BOTH candidates at once, which is why neither alone closed it -
  a lead byte the reader did not skip AND a tag grammar it did not know. Four readings were
  driven against the whole population before one read every record with no breaks. A
  plausible fix and a correct one look identical on a single record.

- Surprises: an adversary was dispatched to refute the zero-properties finding and did not
  refute it - but corrected its WORDING in the way that mattered. The finding had been
  stated as a defect on the production dashboard path; it was neither path-specific nor
  novel, and `docs/GATED.md` already held it. Being right about the fact and wrong about
  its standing is the failure mode to watch for here.

- Surprises: the built-class allowlist was seeded from the only `Build_*_C` spellings in
  the tree, which came out of an ARCHIVED spike report - and three of those nine were the
  only ones present in the operator's world. The map plotted 37 of 698 built actors. A
  read-only census of the world's own classes fixed it to 68 across 15 classes, and what is
  still skipped is counted and published rather than dropped.

- Surprises: a REAL BROWSER found three defects that no arm could see, including one that
  would have fired on every real save - the account-id leak detector matching the fractional
  tail of a coordinate. Nothing had driven a browser at this page since session 78. The
  instrument that worked was `tests/surface/audit_harness.py` over plain HTTP with
  Playwright; the in-app browser pane cannot scroll - programmatic and synthetic scrolls
  both leave `window.scrollY` at zero - so it can only ever screenshot the top viewport.

- Failed paths: filtering the panel's warning explainer on the endpoint's own source. It
  dropped exactly the warnings that explain an empty answer, because the emptiness and its
  reason arrive from different layers. The endpoint deliberately does NOT remap a warning's
  source; that field names the layer that flagged it.

- Failed paths: a positional pin. The seam's network-detector baseline was
  `PANEL_MODULES[0]`, ordered by `sorted()` over the server's asset names and stated
  nowhere. A new panel module sorted ahead of it and took the baseline. The arm that caught
  it was doing its job; the repair was to give the baseline a name.

- Decisions: the license gate ran BEFORE any format knowledge was acted on and its verdicts
  are in `docs/LEDGER.md`. The tool the operator demonstrated is the one source that may
  NOT be read - no LICENSE file, private manifest, and a README forbidding reuse in any
  case. Nothing was copied from anywhere; the grammar came from the bytes.

- Next action: CS-981. Route CS-829, CS-830 and CS-831 out of `docs/GATED.md` now that
  their condition is discharged, READING CS-829's fences first - inventory is three items
  and not one, and an operator ruling was once obtained on the premise that it was one.

## Session 84 - 2026-09-11 - the lane's refusal got a name, and a green suite was refuted four times

- Shipped: CS-970. Five commits, `aa5a828` through `03bcf1c`. Detail in docs/LEDGER.md.
- Filed: CS-974 (the `_CI_ROLLUP_BAD` denylist) and CS-975 (nothing reads the driver's
  exit code), both split out of CS-970 on an operator ruling rather than absorbed into it.
- In flight: nothing. The lane is still STOPPED by `ops/loop/control/lanes/QUEUE_STOP`,
  deliberately - see Next action.
- Decisions: two acceptance clauses AMENDED, both recorded in the CS-970 ledger entry
  because an adjudicator required the amendment be written rather than inferred. The
  dirty-worktree precondition does not exist in the code and was refused, not built; the
  eleven-failure threshold became three.
- Surprises: the suite was GREEN at every single refuted commit - 6224, 6241 and 6256
  passes against trees that each still held a live defect. Four adversarial rounds found
  the SAME defect wearing a different field each time, and the fourth was a regression
  this session's own fix had introduced. An allowlist over what counts as progress was
  the only shape that held; every denylist leaked.
- Surprises: `docs/LEDGER.md`'s own 2026-09-11 record is CORRECTED by the new entry. The
  eleven failures were not "a launcher meeting a bare repository" - every failing cycle
  left a worker log, and a bare-repo fault raises before any worker is spawned.
- Surprises: another session committed and PUSHED main mid-work, so three CS-970 commits
  reached `origin/main` before their repairs existed. Main is shared; unpushed is not a
  state this session controlled.
- Failed paths: keying progress on whether `origin/main` moved. It reads a worker that
  pushed the LANE BRANCH, which `tools/headless-queue.md` explicitly instructs on a
  rejected push, as a dead night and killed it at cycle 3. Do not retry that signal.
- Next action: the lane is STILL NOT SAFE TO RE-ARM BLIND, but for a new reason. The
  2026-09-11 trigger is still UNDIAGNOSED, and the row it will now print most likely reads
  `runner_exited_early` or `spawn_failed`, which names the proximate mechanism and points
  at the runner rather than at whatever actually refused. Decide whether one instrumented
  arming to READ that row is worth a night, knowing the row may mislead.
