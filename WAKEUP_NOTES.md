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

## Session 3 - 2026-08-14 - phase 2 follow-ups, then the phase 3 solver core

- **Shipped:** CS-105, CS-201, CS-202, CS-203. Phase 3 waves 0, 1 and 2 of CS-300 -
  the registry seam plus ADR 0006, the mypy ratchet, `solve/exact.py`, the C1-C9 solve
  corpus, `solve/power.py` and `solve/ratio.py`. Detail in `docs/LEDGER.md`.

- **In flight:** CS-300 is NOT closed and must not be recorded as closed. Two of its three
  acceptance criteria are met - hand-verified ratios including the byproduct loop, and the
  exponent-from-data guard. The third, "the optimizer swappable by config with identical
  results on a degenerate case", needs `solve/optimize.py` plus `solve/backends/` (wave 3),
  and the whole-path no-float assertion needs `tests/solve/test_phase3_gate.py` (wave 4),
  which by doctrine is written by an agent that authored no solve module.

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

- **Next action:** merge wave 3 (`solve/optimize.py`, `solve/backends/`) if it has landed,
  then dispatch wave 4 - `tests/solve/test_phase3_gate.py` - to an agent that authored no
  solve module. That gate is the remaining CS-300 acceptance criterion: an AST walk over an
  asserted-EQUAL module set (not merely non-empty) banning float literals, the `float` and
  `complex` names, `**`, `pow`, `round`, `divmod` and the float-manufacturing stdlib imports,
  plus a self-test proving each construct IS detected, plus the import-graph check. Note that
  `exact.py` and `power.py` both quote the `Fraction ** Fraction` measurement verbatim in
  their docstrings, so the gate must scan the AST rather than the file text or it will flag
  its own evidence.

## Session 2 - 2026-08-14 - three operator decisions, then phase 2 data layer

- **Shipped:** CS-007 (LICENSE holder ratified), CS-100, CS-101, CS-102, CS-103 (phase 1
  implementation work), CS-200 (phase 2 gate, all three acceptance criteria met and verified
  independently). Detail in `docs/LEDGER.md`.

- **In flight:** nothing half-done. Working tree is committed. **No remote exists yet** - the
  operator chose a private GitHub repo named `Clockspeed` receiving a SQUASHED orphan commit
  from the clean tree, NOT the existing history. That push had not been performed when this
  note was written; check `git remote -v` before assuming.

- **Decisions:**
  - ADR 0005, `accepted` - the overclock ceiling is NOT in `Headers.zip`, and the mechanism
    says it never will be: every relevant property is `EditDefaultsOnly`, so the value lives
    in a data asset, and the zip ships headers with no `.cpp`. It IS a schema oracle. The
    probe recovered the equation and the field name `mExtraPotential` (0.5, in the docs data
    all along), reducing the unknown to one integer, `mDefaultPotentialShardSlots`.
  - Operator decision recorded in `docs/GATED.md` CS-G03: the public flip ships from a FRESH
    history, with three preconditions - PII, author identity, and no agent co-authorship
    trailer.

- **Surprises**, all written back into the spec:
  1. **The spike report was wrong about a SIDE.** It said the fractional-fluid recipe "takes"
     water at 1500. Live re-probe: the water is a PRODUCT. Counts were right, side was wrong.
     `BOOTSTRAP.md` section 3.2 corrected and made authoritative; the report carries a
     correction block. This mattered - a fixture written from the original wording tests
     ingredient rounding only and never touches the product side.
  2. **The registry shipped a wrong number before adversarial review caught it.** Three
     biofuel recipes published litres where the contract said cubic metres, because a
     four-group descriptor whitelist missed `FGItemDescriptorBiomass`. Fixed by deriving the
     namespace from field presence instead of a name list.
  3. **`redact()` had a latent PII leak** that predated this session - it stripped home
     prefixes but not the account-id path segment. Fixing it revealed the fix itself was
     scoped to the 17-digit Steam shape only.
  4. **Two misspelled game keys confirmed live** and used verbatim.

- **Failed paths - do not retry:**
  - **Skipping worktree isolation because write-lists were proven disjoint.** The proof
    bounds DECLARED writes and says nothing about transient ones. Two builders broke files
    outside their lists to watch a test go red - correct TDD, restored correctly - and turned
    an unrelated suite red mid-verification. If a shared tree is used again, the dispatch
    must say every break-revert-observe cycle happens on a scratchpad COPY.
  - **`git ls-files | xargs grep` as evidence that a scrub is complete.** It reads
    WORKING-TREE contents, so it goes clean the instant you edit and proves nothing about
    what git stores. Use `git grep <pattern> HEAD` or `git log -S`.
  - **Trusting per-file `ruff`/`mypy` green.** CI runs them repo-wide; per-file green is a
    weaker and different claim, and it produced a false green this session.
  - **A redactor used as its own test oracle.** `redact(x) != x` as the test for "x holds
    PII" is blind exactly where the redactor is blind.

- **Next action:** create the private GitHub repo `Clockspeed`, push a squashed orphan commit
  from the clean tree, and confirm the tier-1 CI run status on it - CI has never executed
  against a hosted branch, so the `--no-verify` mitigation is still unproven.

## Session 1 - 2026-08-13 - phase 0 scaffold, then phase 1 spikes

- **Shipped:** CS-001 phase 0 scaffold, CS-002 tier-0 gate proven end to end, CS-003 S8,
  CS-004 S4, CS-005 S6, CS-006 ground-truth re-probe, CS-104 S5 body framing. S1, S2, S3
  and S7 also settled - report at `docs/_archive/spike-report-s1-s2-s3-s7.md`, so CS-101,
  CS-102, CS-103 and CS-105 are answered but their implementation work is still open.

- **In flight:** nothing blocking. Phase 2 has NOT been started, deliberately - the
  operator's instruction was to stop after phase 1 and report. No remote is configured, so
  nothing has been pushed; that is an operator decision, not an oversight.

- **Decisions:** ADR 0002 (S8, node data is not seed-dependent), ADR 0003 (S4, save carries
  node geometry but not node semantics), ADR 0004 (S6, unlock state is recoverable).

- **Surprises**, all four written back into the spec:
  1. `py -3` resolves to a DIFFERENT 3.14.4 install than `python`, with no pytest, ruff or
     mypy. Both report the same version, so a version check passes while the gate's lint
     step degrades and pre-push cannot run. Recorded as `BOOTSTRAP.md` section 2.5; hooks
     and `.claude/settings.json` now resolve `python` first and `py -3` last.
  2. S4 half-refuted: the save carries node transforms but NO purity or resource type, so
     `BOOTSTRAP.md` section 8.3 step 1 was wrong to call that "done". Section 8.3 corrected.
  3. S7 half-refuted: the overclock exponent IS in the data but is NOT fixed - two distinct
     values across 62 buildings. The overclock ceiling is absent from the docs entirely.
  4. Locale count is 55 not 57; the save library holds three worlds not one; header version
     is not stable at 14 (it is 10 on the oldest saves).

- **Failed paths - do not retry:**
  - Grouping saves by FILENAME to identify worlds. It inflated 3 worlds into 6 and would
    have produced a false S8 result. Group by the header world token, always.
  - A single fixed actor-header layout for the save parser. The transform offset is +8 on
    save versions 52 and 60 and +4 on version 36. Version-dispatch from day one.
  - Trial-decode encoding sniffing for the docs file. Python's `utf-16` codec decodes the
    UTF-8 `io.json` without raising and returns mojibake. Only the BOM-byte test is valid.
  - Using `AKIAIOSFODNN7EXAMPLE` as a secret-scanner test case. It is AWS's own documented
    example key and the placeholder allowlist correctly ignores it. A real-looking literal
    is blocked properly.

- **Next action:** operator ratifies the LICENSE copyright holder (currently the git author
  name), then decide the BOOTSTRAP.md PII question in `docs/GATED.md` before any public
  flip. After that, phase 2 (CS-200) begins with the docs extractor, written against the
  measured schema in `BOOTSTRAP.md` section 3.2 - NOT against the assumed one.
