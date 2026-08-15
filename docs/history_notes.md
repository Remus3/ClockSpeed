# Clockspeed - History notes

**Deep archive. Pruned session notes and retired ledger entries live here.**

**This file holds NOTHING current.** Nothing in it may be cited as the present state of
the project, and nothing may be acted on without re-verifying it live against the source
of truth first. Everything here has already been superseded, pruned, or archived out of a
living file - that is the only reason a line is in this file at all.

Where current truth actually lives:

| Looking for | Read |
|---|---|
| Current rules, constraints, settled decisions | `CLAUDE.md` |
| The last few sessions at full fidelity | `WAKEUP_NOTES.md` |
| Closed work, newest first | `docs/LEDGER.md` |
| Open work | `ROADMAP.md` |
| Blocked outside the repo | `docs/GATED.md` |
| Module map and seams | `docs/ARCHITECTURE.md` |
| Commands and runbooks | `docs/OPERATIONS.md` |

---

## Rules for this file

- **Relocate, never delete.** When a living file hits its size budget or a note ages out
  of `WAKEUP_NOTES.md`, the content moves here and the living file keeps a one-line
  pointer. Content is not dropped.
- **Append only, newest first.** Archived material is not edited after it lands. It is a
  record of what was believed at the time, including the parts that were wrong.
- **Every archived block carries the date it was archived and where it came from**, so a
  reader can tell how stale it is without reconstructing the history.
- **A dated heading marks its own section historical.** Every section in this file is
  dated for exactly that reason, and the drift guard treats dated sections as
  non-current so they are never audited as live truth.
- **Check a row's AGE before building on anything here.** An archived note may describe
  code that no longer exists, a decision since superseded, or a count long out of date.
- This file is excluded from searches for current truth. Do not resolve a question by
  grepping here.

---

## Archive

<!-- Newest first. Each block: date archived, source file, then the content. -->

_No entries yet._

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
