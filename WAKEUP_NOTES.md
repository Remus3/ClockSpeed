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
## Session 101 - 2026-09-16 - the moon-sync adoption, and three of three slices refuted before merge

CLOSED: CS-1095 (the cross-repo channel contract, all nine items of the operator's
adoption instruction), CS-1103 (a blind inbox read that wrote).
FILED: CS-1101, CS-1102, CS-1103, CS-1104.

**EVERY SLICE WAS REFUTED ON ITS FIRST PASS. THREE OF THREE.** Not one survived its
adversary, and none of the findings was a matter of taste - each was measured. The
spawn-site arm's own docstring claimed a property it did not have, and five spawn shapes
passed it blind including one whose expression evaluates to zero. Arm 7 of the channel pin
did not grade the table it names as the grammar's vector source: a flipped verdict and two
swapped vectors both passed. The watcher's highest-consequence invariant - SHOWING NEVER
ACKNOWLEDGES - was graded one layer below the door the hook enters, so an acknowledgement
added at the entry point survived a green suite.

**ONE SHIPPED DEFECT, FOUND BY AN ADVERSARY AND BY NO ARM.** An inbox that exists but
cannot be listed printed the affirmative clean line with notes sitting in it. A sibling
then reproduced it under a real access-control denial, found it was THREE defects rather
than one, and the two CS had missed were the WRITE halves - a fabricated withdrawal, and
an acknowledgement that erased the watermark. That became CS-1103.

**THE WHOLE SUITE CAUGHT WHAT SCOPED SUITES COULD NOT, THREE TIMES, AND IT WAS RUN BEFORE
THE PUSH FOR THAT REASON.** Session 100 recorded the opposite ordering as a merger error.
Two stale toolpath exemptions, an unbounded subprocess child, and one arm that was
NON-DETERMINISTIC ACROSS CHECKOUTS.

**THE ARM THAT PASSED WHERE IT WAS WRITTEN AND FAILED WHERE IT WAS MERGED.** Arm 6 recorded
a gitignored directory as non-resolving - true in a worktree, false in the primary
checkout. Existence is the wrong property to assert about a gitignored path; being IGNORED
is the right one. THE TRAILING SLASH ON THAT CHECK IS LOAD-BEARING: the rule is a
directory-only pattern, so `git check-ignore` without the slash answers from the filesystem
and reproduces the defect it was written to remove. Measured 5 of 5 each way.

**THE HARNESS REPORTED EXIT 0 OVER A RED SUITE TWICE.** Both times the log said
`PYTEST_EXIT=1`. The log is the evidence; the notification is not.

**THE CHANNEL ROUND: four notes out, four replies back, full reciprocity.** Both published
findings reproduced in every tree holding the core. Two divergences came back that neither
side would have found alone, and BOTH structural arms of the portable core now differ
materially between trees that ported the same prose - which is a statement about porting by
description, not about two arms.

**TWO CONCESSIONS MADE TO THIS TREE, not by it.** The "not urgent while the digest pin
holds" framing is FALSE for any tree porting the arms without the document. And a sibling
refused the same document at its licence gate for naming no licence - a refusal that
applied to this copy, because THIS TREE HAD SKIPPED ITS OWN SECTION 14 GATE. It has now
been run, trap by trap, and CLEARED. The lesson filed with it: AN OPERATOR INSTRUCTION
MOVES THE DECISION, NOT THE GATE.

**A LINE-PIN FAMILY WENT STALE FOR THE SECOND TIME IN TWO SESSIONS**, moved by an edit
ABOVE a site rather than at it. Re-cited by symbol where possible; CS-1102 carries the rest.

## Session 100 - 2026-09-15/16 - CS-1093, CS-1086's domain half, CS-1087

**CLOSED.** CS-1093 - the 7-bit walk names every offending module rather than the
first, the count bound to a scalar so pytest's rewriting cannot render the
population. CS-1087 - a world token carried only by an unparseable header is
matchable WITHOUT parsing that header, by scanning the FRAMING the engine writes
around it.

**DISCHARGED, NOT CLOSED.** CS-1086's domain half. All nine `detail:`-field
disagreements resolved under ONE rule rather than nine judgements: the field is
present exactly when the item has a routing row AND a section in the leaf that
row names. Both directions now measure zero. What remains open is deriving the
leaf half. This unblocks CS-971's blocker by half.

**FILED.** CS-1095 (BACKLOG, the inbox watcher `--strict` flip), CS-1096 (the
bounds enumeration nothing grades), CS-1097 (the save-name false positive),
CS-1098 archify, CS-1099 context-mode, CS-1100 the skills pack.

**GRANTS RECORDED BEFORE THE EDIT.** Two, both in `docs/LEDGER.md`. CS-1087's
frozen-file grant for `tools/precommit_gate.py`, with `.githooks/pre-commit`
DENIED because the hook maps every non-zero status to BLOCKED, which is the wedge
the item forbids. And the console-flash grant for the same file, operator-granted
and recorded AS A DEPARTURE from section 6.1's adjudicator route so no later agent
cites it as precedent.

### What the graders changed, which is the session's real result

CS-1087's shipped fix is materially different from the one first written, and
every difference came from an agent that did not produce the work.

- An ADJUDICATOR sent the first cut back: a bound truncated the world-token
  population without reaching the exit status - CS-1083's defect class recurring
  inside CS-1087's own fix.
- An ADVERSARY found the cap SILENTLY LOSING REAL TOKENS two ways: it counted raw
  hits BEFORE de-duplication, so a value repeated to the cap followed by a
  DIFFERENT value discarded the second; and `hits` was shared across both
  framings, so a full narrow population starved the wide scan entirely.
- The same adversary broke clause 6: `scan_framed_tokens` bound the prefix BARE -
  the first bare holder of a save prefix in the module - and the arm claiming
  otherwise monkeypatched THE VERY FUNCTION HOLDING THE BUFFER, so it was blind by
  construction.
- On RE-GRADE it caught the repair to the bounds sentence PRESERVING the off-by-one:
  "All four" over five became "All FIVE" over six. Incrementing was mistaken for
  correcting because nothing grades that sentence. CS-1096 files the arm.

### Process findings that cost real time

- A NARROWED DEFINITION EMPTIES THE POPULATION. Measuring CS-1086's marker by its
  TARGET string instead of its FIELD POSITION gave 8 disagreements against the
  filed 9. The filed count was right and reproduces at every commit since filing;
  the missing member was CS-1026, whose field points at prose. Keep the count in an
  acceptance - it is the anti-narrowing control - and enumerate the roster beside
  it, because ids go absent where a count miscounts. Memory written.
- THE WHOLE SUITE CAUGHT WHAT THE SCOPED SUITE COULD NOT. Three failures landed
  after the CS-1087 merge, in `tests/test_toolpath.py` and
  `tests/test_assertion_rendering.py`, both outside the scope the merger gave the
  builder. One was a PII LEAK IN THE ARM THAT PROVED THE READER ALIVE: asserting on
  `read_header(readable).world_token` renders a field whose class withholds it. A
  change to a file as widely referenced as the gate needs the WHOLE suite before
  the merge, not after.
- A LINE-PINNED REFERENCE BROKE THREE TIMES IN ONE SESSION - the docs-citation
  guard rejected six line pointers in a ledger entry the merger wrote, and two
  toolpath exemptions went stale when the gate grew 233 lines. Cite by SYMBOL.
- TWO RUNNERS LIED ABOUT A SUITE. One reported exit code 0 over `3 failed`; another
  died silently at 98 per cent with no verdict and zero surviving processes. Write
  `PYTEST_EXIT=` INTO the log and read the log, never the status line.
- `Path.write_text` and the harness heredoc both corrupt payloads - the heredoc
  collapses `\n` inside a quoted body. Write payload scripts with the Write tool.

### Measured, and worth keeping

On the live library this run: 31 save files, ONE unreadable header, and it
recovered NOTHING - it is the truncated-before-the-identifier shape. CS-1083 cited
0 of 28; the grant ordered the re-measure and this is it. So CS-1087's coverage
limb is 0-for-1 on real data today. That is a floor on the item's value, not a
defect in it.

---

## Session 99 - 2026-09-15 - the handoff's single next action was the FOURTH filing over one wall, and the clause guarding it forbade its own remedy

- Shipped: CS-1085 and CS-1066 CLOSED on their own work; CS-1057 and CS-1088 CLOSED AS
  SUPERSEDED; CS-898 NARROWED. CS-1089, CS-1090, CS-1091, CS-1092, CS-1093 and CS-1094
  filed. `main` at 1471779, clean and pushed, whole suite green through the pre-push hook
  and again at `/done` - 7791 passed, 7 skipped, exit 0, `python -m mypy` exit 0.
- In flight: nothing. Tree clean, local equals origin.
- THE SESSION'S ONE RESULT: `tests/test_docs_citations.py` came off its ceiling, 100 per
  cent to 73.94, headroom 21 bytes to about 68000. The ceiling was NOT raised, no
  disposition row deleted, no pin forgiven.
- THE HANDOFF'S SINGLE NEXT ACTION WAS NOT SAFE TO DISPATCH AS WRITTEN. CS-1088 was the
  FOURTH open filing over one file and one ceiling - CS-1057, CS-1066, CS-1088 and
  CS-898 - and two of them carried DIFFERENT triggers for the same guard, 96.875 per cent
  against 90. Grepping the roadmap for siblings before dispatching an item cost minutes
  and saved building the wrong guard twice.
- AN ACCEPTANCE CLAUSE FORBADE ITS OWN REMEDY. "Collected-arm count EQUAL before and
  after" is unreachable for ANY relocation into a new file, because a census arm is
  parametrized over the tracked-module population and gains one node for any new module.
  AMENDED under CLAUDE.md section 8 to a full node-id comparison in both directions,
  which is strictly stronger: a simultaneous loss and gain passes a scalar and fails it.
- A LEDGER SENTENCE WENT STALE INSIDE THE COMMIT THAT CARRIED IT. A slice recorded
  CS-1057's detail relocation as an undischarged seam because those files were off its
  write-list; the merger discharged it minutes later in the same commit. The file is
  append-only so the sentence stands, and it had ALREADY MISLED AN ADJUDICATOR before the
  correction was written. A slice that leaves a seam must have its record checked by
  whoever closes the seam.
- ESTIMATES LOST TO MEASUREMENT THREE TIMES. Dead citations: a planner said 6 names over
  8 sites, an adjudicator said 3 over 4 after filtering to uppercase names and missing
  three FUNCTION citations, and the in-slice measurement was 5 over 7. Self-spelled
  sites: estimated 60 to 28, measured 60 to 37. NEVER carry a count across a slice
  boundary - the acceptance now says so in words.
- A TREE-WIDE GUARD SHIPS RED, and that is the finding not the obstacle. The approach
  band was red on THREE files the item never touched, at 99.9, 95.9 and 95.0 per cent.
  The answer was a baseline residual pinned in BOTH directions with a spelled shrink-only
  ceiling and an item id per row, not a hand-list of one - a hand-list of one is a
  threshold met by its strongest member.
- A PLANT KILLED INSTEAD OF DEGRADING, found by mutation and not by review. A non-ASCII
  byte planted to prove the ASCII arm raised an unnamed `UnicodeDecodeError` that
  destroyed the `closure` fixture, so the arm DIED rather than reporting.
  `namespace_closure` now decodes with `errors="replace"`.
- THE HARNESS WRITES CRLF THROUGH `Path.write_text`. A relocation script silently
  converted three tracked docs to CRLF. It was caught by BYTE ARITHMETIC - the routing
  index grew 203 bytes while a row was being REMOVED - not by a CR check, because
  `grep -c $'\r'` returns the TOTAL line count on a pure-LF file and reads as "all CRLF"
  either way. Pass `newline="\n"` and assert on the bytes.
- Decisions: no ADR recorded. Two acceptances amended under CLAUDE.md section 8 - CS-1066's
  collected-count clause, and CS-1088's approach-arm clause folded into it. CS-898's
  stated-policy half struck as discharged.
- Surprises: no spike contradicted `BOOTSTRAP.md`.
- Failed paths: none abandoned. The widening of `derived_bound_problems` to `ast.Attribute`
  was adjudicated PERMITTED rather than a breach of "the same guard", because the clause
  names the guard's IDENTITY and its two-way property, not its node-type set.
- Next action: work CS-1087 - the unreadable-header residue CS-1083 declined. Do NOT
  close it by simply making an unreadable header block; that declination was adjudicated
  SOUND under non-negotiable 7.

---
