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

## Session 5 - 2026-08-15 - CS-407 closes for all four pairs; the save reader reads the whole library

- **Shipped:** **CS-406**, **CS-407**, **CS-408** and **CS-402**. New items filed: CS-411
  (repo-wide mypy does not cover `scripts/`) and CS-412 (record the remaining opaque spans as
  data, not prose). Suite 1463 -> **1490 passed, 4 skipped**, exit 0. Detail in
  `docs/LEDGER.md`.

- **ALL 14 OF 14 REAL SAVES NOW LOAD END TO END.** It was 3 of 14. Verified by the merger
  against the live library, not taken from a builder report: 14 found, 14 loaded, zero
  failures, zero warnings, 131607 records across 6171 levels, 3 distinct masked world tokens -
  which independently confirms the recorded fact that this library holds exactly three worlds.

- **In flight:** nothing half-done; the tree is committed and pushed. **CS-400 STILL MUST NOT
  CLOSE, and the reason CHANGED from coverage to DEPTH.** Coverage is now complete; what
  closed is a SKELETON grammar. 69.5 to 77.7 per cent of every body is opaque property payload
  and `read_properties` decodes NO property value, so the reader reaches every record and can
  read nothing inside one. Pillar 3 needs inventory, clock speed and connection state, and all
  three live in the payload. **Whether "a real world parses" is satisfied by a skeleton walk
  is an OPERATOR DECISION and was deliberately not taken by the merger.**

- **Decisions:** no ADR this session. A frozen-file GRANT for `scripts/install_hooks.py` was
  adjudicated and recorded in `docs/LEDGER.md` BEFORE the edit, per CLAUDE.md section 6.

- **Surprises**, each measured rather than reasoned about:
  1. **The inherited resume notes named the WRONG UNKNOWN on two of three pairs.** Save 42's
     note blamed the transform delta; the delta was never wrong, its LEVEL GRAMMAR differed.
     Save 60's note described a fixed 78-byte separator; it is a variable-width counted
     structure taking three widths. Every prior attempt swept the parameter it had been told
     was unknown while holding the wrong thing fixed.
  2. **ALL THREE ADVERSARIES RETURNED REFUTED - AS WRITTEN, NOT IN SUBSTANCE.** No rival broke
     a byte landing or a skeleton. They killed over-claiming, and the shipped grammar is
     narrower and better than the measured one.
  3. **One narrowing was a REGRESSION AGAINST A SHIPPED ADR, caught just in time.** Actor
     pre-runs of 0, 4, 8 and 12 bytes ALL land 8 of 8 on save 52 - byte arithmetic is blind
     even to that run's width. `objects.py` already modelled it correctly as one opaque span
     per ADR 0003. Splitting it into named fields would have been a step backwards.
  4. **A recorded reason was refuted by RUNNING it.** `objects.py` said delta 4 was declined
     because it held only if save 42's declared header size also excluded the collectable
     count. That grammar stops inside level 0. One thing changed, not two.
  5. **A test was GREEN WHILE FALSE.** The corpus still named save 42 as its unmeasured save
     version, so a refusal test kept passing while its own example had stopped being true.
     Green because the corpus table was incomplete, not because the claim held.
  6. **`ROADMAP.md` claimed both CS-406 leak sites were on the sweep's live residual list.**
     Measured FALSE for the wiring line by running `scan_repo()` directly - it appears in
     neither list and was guarded by nothing at all.
  7. **`redact()` is a NO-OP on the pinned project root.** It maps `C:\Clockspeed` to itself,
     because that root is not under a home directory while the test oracle still matches it.
     A redaction-based CS-406 fix would have passed on a clone under a home directory and
     silently failed on this machine.
  8. **The stale-worktree problem RECURRED and the mandated check caught it.** The CS-407
     integration builder's worktree was cut from its base's parent; it reported ANCESTOR-FAIL,
     fast-forwarded, and re-measured before building.
  9. **18 of 28 commits carry an agent co-authorship trailer** although `docs/GATED.md` CS-G03
     records an operator decision against it. Operator reaffirmed on 2026-08-15: keep
     committing without it. The existing history is not worth rewriting - CS-G03 already
     generates a fresh history at the flip, which strips them.
  10. **THE PATH-LEAK ORACLE WAS INERT ON POSIX, and CI is what proved it.** `ABSOLUTE_PATH`
     in `tests/test_exception_rendering.py` was a DRIVE-LETTER regex, so on the Linux runner
     it could not match an absolute path at all - every `not ABSOLUTE_PATH.search(...)`
     assertion in that module had been passing VACUOUSLY on every CI run since it was
     written. **The thing that caught it was the NON-VACUITY assertion added by CS-406** -
     "the sandbox root really is a path the oracle WOULD match" - which went red on CI while
     every sibling assertion stayed green. That is exactly the job it exists to do. CI went
     RED on `a0da3b7` with a green local suite and GREEN on `1ad0db8` after the widening.
     `docs/LEDGER.md` had already recorded this residual under CS-205 - "POSIX behaviour
     unobserved, settled only by a Linux runner" - and the runner settled it.
     Known and deliberately NOT fixed: the Windows branch also matches the `s:/` inside
     `https:/`, so it over-fires on a URL. That is pre-existing and fail-closed, and
     tightening it can only make a `not search` assertion pass MORE easily, which is the
     direction that hides a leak.

- **Failed paths - do not retry:**
  - **The tag-driven collectable rule.** "Present iff the level's data entries are tagged 42"
    is UNDEFINED on 229 of 2244 levels of the very file it came from, and both outcomes occur
    among them. Use the SIZE-DRIVEN rule - and know that it is an a-priori delimiter argument
    rather than a measurement, because "always read a block" also lands byte-exact on 7 of 8
    save-52 files.
  - **Reading an 8-byte section size as an int64.** Undecidable now and permanently. An int64
    reader silently computes an astronomical size if that word ever goes non-zero, then
    misdiagnoses the WRONG FIELD.
  - **Claiming a breakdown inside a constant blob.** Save 60's 70-byte run has no observable
    boundary at all - not 4+6, not 8+2, not 16+10.
  - **Reading "8 real files" as an independence count.** The save-52 preamble is byte-identical
    across all 8 and is the static world-partition grid, so n=1 is a CEILING, not a sampling
    accident more saves would fix.

- **A measurement that leaves no artifact is not resumable.** The prior session's note said the
  (13,42) grid preamble "is measured"; that measurement was recorded NOWHERE in the tree, so
  the resuming slice re-derived it from scratch. Filed as CS-412. Record the GRAMMAR, never an
  adjective about it.

- **Next action:** get an operator ruling on **CS-400** - coverage is met and depth is not, and
  the merger deliberately did not take that decision. If CS-400 stays open, the natural
  successor to CS-407 is measuring the OBJECT PAYLOAD GRAMMAR, which is the three quarters of
  every body still opaque and the thing pillar 3 needs. **CS-405 is now UNBLOCKED** but note it
  may need the payload grammar first, and saying so is the correct outcome rather than forcing
  a YES or NO.

## Session 4 - 2026-08-14 - ADR 0006 adjudicated, four tier-1 fixes, phase 4 waves 0 and 1

- **Shipped:** ADR 0006 flipped to `accepted`; **CS-204**, **CS-206**, **CS-207** closed;
  **CS-208 DENIED** and replaced by CS-209; **ADR 0007** written and accepted; and
  **phase 4 waves 0 and 1** - the version-qualified spec, the synthetic save corpus, and
  `clockspeed/save/{header,chunks,usmap,workdir}.py`. Suite 734 -> 1067, exit 0. Detail in
  `docs/LEDGER.md`.

- **Also shipped, after the first `/done` ran:** CS-205, CS-404 part 1, and phase 4 waves 2
  and 3 in full - `objects.py`, `world.py`, the phase-4 acceptance gate, CS-407 and CS-409.
  Suite 734 -> **1462 passed, 5 skipped**, exit 0. CI green on `f3f26ba`.

- **A REAL WORLD PARSES.** Verified by the merger against the live library, not taken from a
  builder report: 3 of 14 real saves load end to end through `load_world` into a `WorldModel`
  - 25769, 25769 and 25725 records, 202 levels, 2774 nodes - and the other 11 are refused
  with a clean `WorldLoadError`. All three render the SAME masked token digest with DIFFERENT
  record counts, which is CS-401's token-stability claim confirmed on the game's own output.

- **In flight:** nothing half-done; the tree is committed and pushed. **CS-400 IS STILL NOT
  CLOSED, and the gate itself says so.** Clauses 2, 3 and 4 are MET and gated. Clause 1 is met
  for ONE of four version pairs only - three of the four real pairs cannot be read at all
  (CS-407), and CS-402 is separately unmet because save version 42's transform delta is
  unmeasured (CS-408). The open follow-ups are CS-406, CS-407, CS-408 and the remaining parts
  of CS-404.

- **Decisions:** ADR 0007, `accepted` - the save header layout and the chunk framing are
  version dependent. Its adjudication returned NEEDS-REVISION and four defects were fixed
  before the flip. Operator ruled that an INCONCLUSIVE `mInventoryPotential` result is an
  acceptable outcome, filed as CS-405 rather than converted into an answer.

- **Surprises**, every one measured rather than reasoned about:
  1. **The chunk framing in `BOOTSTRAP.md` was TRUE ONLY FOR HEADER VERSIONS 13 AND 14.** On
     header 10 the marker is `0x00000000` and there is NO compression-algorithm byte at all,
     with zlib at magic+48 rather than +49. A walker built from the unqualified fact fails on
     3 of 14 saves and looks correct on the other 11. The session prompt called this settled;
     the probe won. Section 3.1 corrected, ADR 0007 records it.
  2. **The header string ORDER is header-version dependent, and that is a PII mechanism.**
     Header 14 carries four leading strings, headers 10 and 13 carry three. So on 10 and 13
     the THIRD string is the operator's world name and on 14 it is the options string - a
     redactor targeting a NAMED FIELD is defeated by a version-dependent field ORDER. A
     planner probe demonstrated it by leaking one world name into its own agent transcript.
     `header.py` therefore makes the PII strings ABSENT from the returned type, not redacted.
  3. **`docs/adr/0003` is `accepted` and states the refuted framing verbatim**, so the stale
     claim held the HIGHER status and a reader searching for "chunk framing" hits it first.
     Found by the ADR 0007 adjudicator. Corrected by pointer in both directions, since
     neither an accepted ADR nor an append-only ledger entry may be edited.
  4. **CS-208 was REFUTED BY MEASUREMENT, not deferred.** 16 matchable world names exist here
     and the shortest is 4 characters, so any floor at or above 5 drops exactly one REAL name
     and it then commits. The false positive it feared does not exist - the gate over every
     tracked file exits 0. And a floor of 4, 5, 6 or 8 turns ZERO of the 65 gate tests red,
     which proves the suite is BLIND to the change rather than that the change is safe.
  5. **The int8 after the datetime ticks is not "session visibility".** It reads `0x00` on
     header 10, 13 and 14/60 and one of `0x10/0x50/0x90/0xD0` on the eight header-14/save-52
     saves. Position is anchored (the int32 after it reads 40 on all 14); meaning is not.
  6. **The synthetic corpus diverges from real bytes on the header-10 body prefix**, and a
     builder reported the FIXTURE value as a measurement. Real header 10 opens with an int32
     equal to body length minus 4. Filed as CS-404 before it could reach wave 2.
  7. **The size block is `(c, u, c, u)`, measured** - W1-CHK named the alternative as the one
     thing that could make its module wrong on every real save while every synthetic test
     passed. It had guessed right, but it was a guess until the merger measured it.
  8. **`os.open(p, os.O_WRONLY)` is invisible to a text-level write scan.** The static
     single-writer check returns empty for it, so the phase-4 AST gate must cover `os.open`
     and the runtime audit hook is what catches flag-based writes.

- **Failed paths - do not retry:**
  - **Trusting a builder's measurement of a FIXTURE as a measurement of the FORMAT.** Two
    separate builders did this, on the body prefix and nearly on the size order. The fix is
    not more review - it is that any claim about the byte format gets re-measured against a
    real save before anything is built on it.
  - **A shape-based check for a leaked token or world name.** A 22-character base64url regex
    matches `Build_SyntheticSmelter`, and a 3-character-run check against a whole `repr`
    matches the FIELD NAME `world_token=`. Both produced false positives for the merger this
    session. Scope the check to the value, never to the rendering.
  - **`grep -P` as a PII scan on this machine.** It errors with "supports only unibyte and
    UTF-8 locales", and a `||` fallback then prints a clean result for a grep that never ran.
    W0-DOC caught its own false pass and wrote a real scanner instead.

- **Two more surprises, both after the first `/done`:**
  9. **A real save body is a LIST OF LEVELS, not an object table.** Nothing downstream could
     ever have parsed a real world by fixing an offset - the shape was wrong, not the number.
     Header 10 / save 36 is now derived and confirmed on all three real files of that pair,
     each landing on its exact final byte. The other three pairs are refused eagerly.
  10. **pytest renders the ARGUMENTS of every frame in a failing traceback**, with no
     `--showlocals` and no opt-in. Measured with a planted marker: it appeared twice. So a
     test passing real save bytes into a frame that can raise prints the HEAD of the file,
     which is exactly the PII-bearing header. Three live sites found and guarded. This class
     is invisible to every green run BY CONSTRUCTION, because it only fires on failure.

- **Also failed and worth not retrying:** interpolating save version 42's transform delta.
  TWO separate builders reached a plausible number and BOTH discarded it - one because its
  method failed to recover the known deltas for 36 and 60 when validated against them, the
  other because the reading needed two unmeasured assumptions propping each other up. With 36
  giving 4 and 52 giving 8, the value 4 is exactly what "looks derived" produces.

- **Closing note, after the second `/done`:** the phase-4 gate's clause-1 test went from
  SKIPPED to PASSING. Lifting that skip surfaced a trap worth remembering - the gate author
  wrote "delete the skip marker and this becomes a real assertion with no other edit", and
  that would have FAILED, because the test used `latest_save()` and the newest save here is
  an UNMEASURED pair the reader refuses by design. A correct refusal would have read as a
  defect. It now selects the newest save of a MEASURED pair. Suite closed at 1463 passed,
  4 skipped, exit 0.

- **Next action:** **CS-407** - derive the body layout for the remaining three version pairs.
  Header 14 / save 52 is the nearest: all 134 named levels walk and the persistent level's
  FIRST COMPONENT record is the single blocker. Each unfinished pair has its stopping point
  recorded in `LEVELLED_LAYOUT_UNMEASURED` so a slice resumes from evidence rather than from
  scratch.

## Session 3 - 2026-08-14 - phase 2 follow-ups, then the phase 3 solver core

- **Shipped:** CS-105, CS-201, CS-202, CS-203 and **CS-300, the phase 3 gate**, all four
  waves. `solve/{exact,ratio,power,optimize}.py`, `solve/backends/`, the C1-C9 corpus, the
  registry seam plus ADR 0006, and the mypy ratchet. Detail in `docs/LEDGER.md`.

- **In flight:** nothing half-done; the working tree is committed and pushed. Phase 3 is
  CLOSED and phase 4 (CS-400, the save reader) is next and unblocked. Two phase-3 follow-ups
  were filed rather than absorbed: CS-301 (the variable-power law is unmeasured, so
  `power.py` refuses to model it, and two branches have no fixture to exercise them) and
  CS-302 (`ratio.py`'s refusal-path diagnosis is O(rows) extra solves and was never measured
  at real-registry scale). Five phase-2 follow-ups are also open, CS-204 to CS-208, all
  found by this session's own process rather than inherited.

- **Decisions:** ADR 0006, status `proposed`, needs an adjudicator to flip it. It records
  how the un-sharded clock base enters the model, which ADR 0005 specified but could not
  implement. It supersedes nothing and ADR 0005 is unedited.

- **Surprises**, each measured rather than reasoned about:
  1. **`strict = true` does not work in a mypy per-module override.** It is accepted with no
     complaint and applied GLOBALLY - the `clockspeed.solve.*` rung alone produced 25 errors
     in `tests/data/test_blobs.py`, a file its pattern cannot match. Written out as its
     twelve scoped constituents instead. Acceptance of a key is not evidence of scoping.
  2. **`Fraction ** Fraction` returns a FLOAT** for a non-integer exponent, and the defect is
     DATA-DEPENDENT: the same operator with `Fraction(2,1)` returns a Fraction, so a test
     written with a whole-number exponent passes while the shipped 1.321929 degrades
     silently. `**` is banned outright in `solve/`.
  3. **ADR 0005 contradicted the shipped registry** and a test enforced the contradiction.
     Resolved in data by S0-REG; see ADR 0006.
  4. **The planner's C5 chain shared C3's product**, which gave that item a second producer
     and destroyed C3's uniqueness - a rival plan satisfies every balance at 30 MW against
     C3's 436/3 MW, so a minimizing solver would have returned it and C3's hand-verified
     answer would have been wrong. Caught by the fixture slice, fenced with two tests.
  5. **A shape-only world-token detector is not viable.** Measured over all 99 tracked files:
     a naive 22-char regex matches 2082 times, and even at its tightest still matches 5 game
     class names. CS-201 detection is value-based as a result.
  6. **`.claude/worktrees/` was untracked but UNIGNORED** - one `git add -A` would have
     committed a duplicate tree - and it inflated local `ruff format` from 38 files to 187,
     reporting a builder's scratch copy as a main-tree failure. Now gitignored.

- **Failed paths - do not retry:**
  - **`git reset --hard` to undo a probe commit.** It discarded every tracked modification in
    the working tree in one step, including four merged slices. Recovered in full because the
    agent worktrees still held the builder output and the new files were untracked, but it
    cost a full recovery cycle. Use `git reset --soft HEAD~1`. A trailing `--` does NOT make
    `--hard` respect a pathspec; it is accepted as a whole-tree reset.
  - **Slicing `pyproject.toml` at the first literal `[[tool.mypy.overrides]]`.** That string
    appears in a COMMENT above the real blocks, so every generated test config was truncated
    mid-comment and silently set the option globally. Six bisect results were measuring the
    broken fixture rather than the thing under test.
  - **Trusting a builder's baseline count.** Worktrees are cut from HEAD, so a builder that
    started before a merge reports a baseline that is real for it and wrong for the tree.
    Two builders reported honestly that their dependencies were absent; re-run post-merge.
  - **Auditing a fence with a cruder check than the fence itself.** A first pass at the
    ADR-0006 audit walked ALL string constants including docstrings and reported four false
    failures, because the operand names legitimately appear in explanatory prose.

  7. **Flipping the mypy gate to blocking immediately caught a PRE-EXISTING CI failure that
     `continue-on-error` had been hiding.** mypy analyses for the platform it is RUNNING on,
     so `if sys.platform != "win32": return` makes the rest of the function unreachable on
     Linux and not on Windows - three `unreachable` errors in `clockspeed/data/locate.py`
     off identical source, green locally and red on the runner. The previous CI run reports
     `success` only because the failed step was allowed to pass the job. Fixed by pinning
     `platform = "win32"` in the mypy config so the config means the same thing everywhere;
     the cost, three unchecked non-Windows early returns, is stated in `pyproject.toml`
     rather than hidden. **A green local gate is not evidence about CI when the tool's
     behaviour depends on the host.**
  8. **A merger instruction was refuted by the agent executing it, and the refutation was
     right.** The wave-4 dispatch required that no solve module pull in
     `clockspeed.data.docs_extract`. That is unsatisfiable - `registry.py:206` and
     `version.py` import it at module level and `tests/data/test_phase2_gate.py:775-781`
     REQUIRES those edges - and `docs/ARCHITECTURE.md:136-138` scopes the raw-docs
     prohibition to `advisor/`, not to `solve/`, whose clause is "never reads a save".
     Writing it as dispatched would have made the phase red against correct code.

- **Next action:** get ADR 0006 adjudicated from `proposed` to `accepted` by an agent that
  did not write it - it is the only unadjudicated artifact from this session - then begin
  phase 4 (CS-400, the save reader). Phase 4 is unblocked and is where the two oldest
  deferred questions land: whether `mInventoryPotential` serialization carries the overclock
  slot count (ADR 0005's one remaining unknown, which would let `power.py` publish a real
  ceiling), and the world-token half of CS-201, which cannot work until a header parser
  exists. Note BOOTSTRAP.md section 3.1: the actor header layout is save-version dependent,
  +8 on save versions 52 and 60 and +4 on version 36, so version-dispatch from day one.
