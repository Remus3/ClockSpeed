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

## Session 10 - 2026-08-16 - eight items close; three of four slices refuted; CS-420 fails a fifth time

- **Shipped: CS-403, CS-209, CS-423, CS-429, CS-430, CS-431 CLOSED, plus CS-433 and CS-434 which
  are repairs of this session's own refuted work. CS-204's RECORD corrected - it had closed on
  2026-08-14 and its ROADMAP line outlived it by two days. CS-420 STAYS OPEN.** Filed CS-211,
  CS-435, CS-436, CS-437, CS-438. Suite 1733 -> **1846 passed, 3 skipped**, exit 0; skips fell
  from 7 to 3 because CS-423 removed four silent ones. mypy 78 files clean, ruff clean, drift
  guard CLEAN 8/8, doc budget PASS. Nine commits, `995cf0b..4e6b19a`. Detail in `docs/LEDGER.md`.

- **THE HEADLINE IS THE HIT RATE AGAIN, AND IT DID NOT IMPROVE. THREE OF FOUR SLICES WERE REFUTED
  BY INDEPENDENT ADVERSARIES, EVERY FINDING INVISIBLE TO A GREEN 1819-TEST SUITE.** Not one was a
  style quibble:
  1. **The commit gate FAILED OPEN AT 513 ENTRIES.** `MAX_SAVE_ROOT_ENTRIES` truncated SILENTLY at
     two of its three sites, ALPHABETICALLY, before the newest-first sort - so the saves dropped
     were exactly the recently-played ones. At 511 and 512 the gate blocked an undeclared world
     token; at 513 it exited 0, the commit landed with the token in the blob, and the operator was
     told "no world token is discoverable on this machine". Not silence - a false statement. The
     function's own docstring said "Truncating alphabetically would silently drop the recent ones"
     while doing exactly that. Test coverage of the constant was zero. **It needs no attacker,
     only time**: autosave rotation grows one directory forever.
  2. **CS-423 SHIPPED A FALSE GUARANTEE.** `objects.py` was graded `retains-no-save-bytes` while
     `_Cursor.__init__` binds the decompressed body to `self._data`. The checker inspected only
     `@dataclass` fields. A green oracle asserting a property the module lacks is worse than the
     silent skip the item was filed to remove.
  3. **THE CONTAINMENT GUARD WAS BLIND TO ONE KEYWORD.** `ast.AsyncFunctionDef` is not a subclass
     of `ast.FunctionDef`, so an `async def` helper with a body BYTE-IDENTICAL to the existing
     splice control passed cleanly. Seven of eight spliced shapes escaped. **The same commit
     enumerated the path-bearing primitives in a neighbouring file** while the reach guard listed
     none of them - guard inversion re-shipping inside the guard built to prevent it, two sessions
     running.
  4. **CS-430's WARNING DETAIL WAS FALSE.** It said a skipped node record's "placement is
     unrecoverable from this save". `transform is None` implies a levelled COMPONENT, and a
     component closes with a parent path: 27865 of 27865 transform-less records carry a non-empty
     parent, 27420 of those naming a placed record. **The defect the item exists to fix, reproduced
     inside its own fix** - moved from the subject key to the detail text, where nothing looked.

- **CS-420 FAILED FOR THE FIFTH CONSECUTIVE ROUND, and the fence it shipped is why it stays open.**
  The mechanical check exists, reads three prose channels, is proven to fire against the real tree,
  and gutting it is visible. It still does not fence: an adversary inserted three genuine ADR-0008
  tier-1 universal claims into the fenced module, byte-verified, and the suite stayed
  byte-identically green. 19 of 22 real universal phrasings carry no listed marker; ten prose
  channels are unread; **571 of 573 sentences (99.7 per cent) are not read by the rule**;
  `FENCED_MODULES` is a hand-written tuple whose deletion leaves the suite green. Round five also
  shipped five false sentences, two contradicted by the module's own passing tests, and **the fence
  flagged 0 of the 5**. They were DELETED rather than rewritten, per ADR 0008's own remedy.

- **Decisions:** no new ADR. **ADR 0008 REMAINS `proposed` and STILL NEEDS AN ADJUDICATOR** - none
  was run this session. A NEW TENSION IS RECORDED FOR IT: ADR 0008 SCOPE says the mechanical fence
  "is scoped to where such claims actually cluster, and widening that scan is separate work", which
  the shipped fence matches word for word, while CS-420's acceptance says EVERY DECLARATIVE
  SENTENCE. Both readings are evidenced; neither was resolved. **A FROZEN-FILE GRANT WAS USED AND
  NOT WIDENED:** `tools/precommit_gate.py` under the 2026-08-15 grant, with zero exposure of any
  other frozen path, verified by diff on every merge.

- **Surprises**, each measured rather than reasoned about:
  1. **AN ITEM ON THE SESSION PLAN WAS ALREADY CLOSED, AND THE PLAN INHERITED THAT FROM A STALE
     LINE.** CS-204 closed 2026-08-14 in `e17ba59` - one commit carrying implementation, tests AND
     its own ledger entry - and its ROADMAP line was never removed. The 2026-08-15 operator grant
     then scoped itself to "the three OPEN items", which is exactly
     `grep -c "NEEDS ITS OWN FROZEN-FILE GRANT" ROADMAP.md` returning 3. **One stale line, read
     three times, by three readers who each had reason to think the previous one had checked.**
     Filed as CS-211: nothing in `tools/` reads ROADMAP.md's content at all.
  2. **SEVEN OF SEVEN WORKTREE AGENTS STARTED STALE**, up to five commits behind. Every one caught
     it only because the dispatch ORDERED the check. This is now unambiguous, not a fluke.
  3. **THE MERGER'S OWN `cd` PERSISTED AND PUT A MERGE ON THE WRONG BRANCH.** A squash-merge of
     slice D landed on slice B's branch. Nothing was lost - D's work was safe on its own branch and
     B's uncommitted work survived a `--mixed` reset plus a targeted checkout - but the fix cost a
     detour. Use `git -C <path>` for every git call; the shell's cwd is not a safe assumption.
  4. **AN ADVERSARY DISCARDED ITS OWN FIRST MEASUREMENT** after finding its extraction had silently
     produced head content in the base directory. A second discarded a gutting run after finding a
     stray `.git` in the control tree. Both caught it by hashing rather than by trusting the copy.
  5. **A BUILDER CHECKED THE MERGER AND WAS RIGHT TO.** Told a second sentence was probably also
     false, it measured, found it TRUE as written, and left it alone - noting that deleting a true
     sentence to be safe is its own defect.
  6. **A BUILDER'S FIRST SPLICE SHAPES DEFEATED THEMSELVES.** Four of eight named the locator, so
     the guard caught them on that rather than on the gap they were written for; it found and fixed
     that before reporting.
  7. **TWO REPAIRS SELF-ALLOCATED THE SAME NEW ID.** Both chose CS-433. Resolved by giving the
     merged one CS-433 and the other CS-434 at merge time. IDs are permanent and never reused, so
     an agent inventing one is a collision waiting to happen.
  8. **A PER-SITE MEASUREMENT NARROWED A RELAYED CLAIM.** "Both positional mutants survive" became
     three of five die, two survive - measured site by site rather than accepted.
  9. **THE MERGER STATED A SEVERITY THAT WAS WRONG AND A BUILDER CAUGHT THE SAME ERROR IN ITS OWN
     PROSE.** Both said CS-430's false detail is "rendered verbatim to the operator by the
     advisor". The advisor is a 32-line stub; that render path does not exist. The string reaches
     `WorldModel` verbatim and would surface once pillar 5 ships - latent, not live.

- **Failed paths - do not retry:**
  - **A hand-written marker list as a prose fence.** It misses 19 of 22 real universals. The list
    is the thing that rots, which is what the artifact was built to stop.
  - **Scoping a fence to a hand-written module tuple.** That is an allowlist with the sign flipped;
    deleting the entry deletes the coverage silently.
  - **Grading a module against a redaction oracle when no path reaches it.** It asserts something
    false. Name why absence-of-value is the mitigation and assert THAT.
  - **A blanket assertion over modules that do not share a justification.** Generalise the QUESTION,
    keep the ANSWERS distinct.
  - **Reading a verdict from an interpreter or a tree you did not verify.** Two adversaries lost a
    full pass to a silently wrong extraction this session.

- **Next action:** **CS-211**, the mechanical one-owner guard. It is cheap, it is tier 1, and it is
  the only item this session that would have PREVENTED a defect this session actually suffered -
  a builder dispatched to re-implement shipped work. Then **CS-435**, the fourth instance of the
  silent-loss family, which is the strongest argument that family needs mechanical detection rather
  than a fifth hand-fix. **Do NOT take CS-420 next** unless the ADR 0008 adjudication happens first:
  its acceptance and its governing ADR now disagree in writing, and building against an unresolved
  disagreement is how this item has failed five times.

## Session 9 - 2026-08-16 - four items close, and every single first build was refuted

- **Shipped: CS-419, CS-424, CS-425, CS-427 CLOSED. CS-420 WAS CLOSED AND THEN REOPENED THE SAME
  SESSION** - see the final audit below. ADR 0008 recorded (`proposed`). Filed CS-428, CS-429,
  CS-430, CS-431, CS-432, CS-701. Suite 1619 -> **1733 passed, 7 skipped**, exit 0. mypy clean,
  drift guard CLEAN 8/8, doc budget PASS. Detail in `docs/LEDGER.md`, including the CORRECTION
  entry that supersedes the CS-420 closure.

- **THE HEADLINE IS NOT A DELIVERABLE, IT IS A HIT RATE. FOUR OF FOUR FIRST BUILDS WERE REFUTED
  BY AN INDEPENDENT ADVERSARY, AND EVERY REFUTATION WAS INVISIBLE TO A GREEN SUITE.** Not one
  was a style quibble; each was a defect that would have shipped:
  1. **CS-420's derived test derived nothing.** Its attribution folded through `any()`, which
     short-circuits. With the reach oracle first and red on all six widths, the other two were
     consulted ONLY in the pristine control - invocation census 7/7/1/1 - and **gutting both to
     green no-ops left the suite passing.**
  2. **CS-419's fix introduced a behaviour regression.** The new warning reused the enum-name
     warning's `(code, subject)` key and was added first; `_WarningLog` keeps the FIRST detail,
     so a true "the enum was skipped" was REPLACED by a false "the enum is shorter than the file
     declares" while the enum was absent entirely.
  3. **CS-424 satisfied its acceptance against seven invented names**, and its tests said
     "shipped name" while meaning fixture name - **the acceptance READ as met because the test
     borrowed the acceptance's own word.** Its positive assertions were also a zero-iteration
     loop under an empty name table.
  4. **CS-427's new privacy guards were INVERTED.** They keyed on the CONTAINED routes, so a
     helper using an uncontained route never entered the graded set. Splicing the known-bad
     shape into a new helper left **13 graders passing while it leaked all three markers** - the
     ungraded-containment defect re-shipped inside the guard built to prevent it.

- **BOTH IN-FLIGHT AGENTS LANDED. Neither result was what the optimistic reading expected.**
  - **CS-425 CLOSED, and the main session proved the half the builder could not.** The builder built a
    NEW unfrozen `tools/pretooluse_gate.py` that parses the hook envelope, walks EVERY string in
    `tool_input` rather than an allowlist, and runs the frozen gate's charset and secret checks BY
    IMPORT. `tools/precommit_gate.py` is byte-identical - sha256 equal at base, worktree and HEAD, and
    `git diff --name-only` over every frozen path returns zero lines - so the grant it did NOT hold was
    never needed. **I then made the harness fire its own hook, which no subagent can do: a Bash call
    carrying a literal em dash was DENIED, naming the character and the column, and did not run.**
  - **`pythonw` IS PROVEN SAFE AND IS SHIPPED.** The builder measured it byte-identical across 13 probe
    cases but deliberately declined to ship it, because whether Claude Code's own spawn WAITS on a
    GUI-subsystem child was an inference rather than a measurement - and it was right to refuse. I
    settled it directly: under `pythonw` the em-dash probe is still DENIED with an identical diagnostic,
    and a clean ASCII call still runs. So the console flash goes away with the gate intact. **That
    judgement call - refusing to trade a verified gate for an unverified cosmetic win - was correct
    even though the answer came back favourable.**
  - **THE FINAL PROSE ADVERSARY RETURNED REFUTED, AND CS-420 IS REOPENED.** Six false sentences on
    merged `main`, THREE WRITTEN BY THIS SESSION'S OWN COMMITS. `IT NEVER RAISES` is false by execution
    on a forced `KeyboardInterrupt` - and CS-427 repaired that exact absolute in three sibling
    docstrings the same day while the fourth survived. The join mechanism sentence is false under both
    readings: `ByteProperty -1` rots 5359 payloads with `join.tags` at exactly 55496 and `join.words` at
    exactly 13, because **ByteProperty is not one of the 13 joined words at all**. And
    `_JOIN_WORD_FLOOR = 13` is a UNION over a growing library, not an engine constant - per-save counts
    run 8 to 12 and NOT ONE SAVE REACHES 13, so the floor can go red on a correct grammar. What the
    audit could NOT break: the derived test's structure, the two-copy common-mode claim, the
    bare-CI-box claim, the SystemExit residual, and the repaired no-install gating.

- **Decisions: ADR 0008, `proposed`** - a detection claim is DERIVED by the suite, never written.
  Three tiers by quantifier scope: universal claims DELETED (unverifiable by construction),
  existential claims DERIVED at runtime, mechanistic claims about adjacent code may stay prose.
  **It needs an adjudicator that wrote no part of it and no part of the implementing slices.**
  **A FROZEN-FILE BOUNDARY WAS ENFORCED RATHER THAN ASSUMED:** the recorded grant for
  `tools/precommit_gate.py` is scoped to CS-403/CS-209/CS-204 and **does NOT extend to CS-425**,
  per CS-204's own precedent. CS-425 was designed around it instead of self-granting.

- **Surprises**, each measured rather than reasoned about:
  1. **AN ADVERSARY WAS WRONG, AND I RELAYED IT AS FACT.** The CS-424 adversary reported a live
     invariant violation - `subject='post-schema-Object'` on the real usmap. The builder refuted
     it; I measured directly and the real file yields `subject='post-schema'`, with `names[0] ==
     'Object'` NOT a suffix of any subject. It had read its own name-interpolating mutant's
     output as pristine. **An adversary's quoted command output needs re-measurement exactly as
     much as a builder's claim.** I passed it on because it looked like evidence.
  2. **I CITED A DOCUMENT THAT DID NOT EXIST.** ADR 0008 was authored in the main checkout and
     left uncommitted, then cited as "in force" to three builders working in worktrees that
     could not see it. A builder ran `git log --all`, found nothing, and said so. Committed as
     `921e6d6`.
  3. **THE ADR CONTRADICTED ITSELF AND A BUILDER FOUND IT.** FORECLOSED banned superlatives in
     commit messages while SCOPE permitted recording "what a measurement found at a stated time"
     - and a power-control transcript is both. Resolved in `eeabbd2` on a principle: the ADR
     binds LIVING TEXT (read as describing the current tree, can rot) and not an IMMUTABLE
     TIMESTAMPED RECORD (commit message, ledger entry, wakeup note). The test is the tense the
     reader supplies - if deleting the sentence later would be a CORRECTION it was living text;
     if it would be FALSIFYING THE RECORD it was a record.
  4. **A BUILDER REFUSED MY GLOSS OF MY OWN ADR AS SELF-GRADING**, read the committed file, and
     audited against four requirements the gloss omitted. All four already passed - one of them
     only because an adversary had earlier forced it.
  5. **MY OWN DISPATCH SPECIFIED A VACUOUS ASSERTION.** I told a builder to assert "every width
     is caught by at least one detector". Taken literally that is TRUE BY ARITHMETIC, because
     `test_both_tag_grammar_transcriptions_agree` compares the two constant copies and reddens on
     any single-copy mutant without reading a byte of library. The builder excluded it and
     asserted its sensitivity separately.
  6. **A CLEVER ARGUMENT FOR WHY A CHECK COULD NOT BE BUILT WAS REFUTED BY BUILDING IT.** CS-424
     argued no sound install-gated repr oracle existed. An adversary wrote one in a single pass:
     **a withholding repr emits no string literal at all, so the oracle is "the rendering quotes
     nothing"** - neither substring nor skeleton, live against the real 57985-name table.
  7. **A MUTANT THAT FAILS TO APPLY LOOKS EXACTLY LIKE A TEST THAT FAILS TO CATCH.** A harness
     "reverted" a repr by deleting `repr=False`, which does NOT overwrite a `__repr__` defined in
     the class body, and reported three mutants SURVIVED when the mutation never landed. Harnesses
     must now prove the text actually changed before trusting a verdict.
  8. **`SystemExit` IS A NON-`OSError` AND WAS LIVE DISCLOSURE.** It escaped every repaired site
     and rendered the REAL Windows account name under `-q` alone. `KeyboardInterrupt` renders
     NOTHING without `--full-trace`. **The inherited residual note had the two exactly backwards,
     in the dangerous direction** - the abortability defence was protecting the type that does
     not disclose while the type that does got none.
  9. **A REAL BUG HID BEHIND FALSE PROSE.** Library-backed tests gated their skip on the SAVE
     library while the usmap comes from the INSTALL, so on a machine with saves and no install
     they FAILED rather than skipped. Nobody had run that configuration.
  10. **A FIX FALSIFIED PROSE IN TWO FILES IT DID NOT OWN.** CS-424's repr change made the stated
     reason for two `del` statements false. Both were REPORTED rather than widened into, and
     repaired by the merger once the owning slices had landed. This is ADR 0008 tier 3 behaving
     exactly as predicted - a mechanistic claim rots precisely when the code beside it changes.
  11. **THE BOUNDARY HELD EVERY TIME IT WAS TESTED.** Four separate builders found defects outside
     their write-lists and reported instead of widening. Every one became a filed item.

- **Failed paths - do not retry:**
  - **`any()` in a derived attribution.** It short-circuits, so a saturating first term hides
    every later one. Evaluate all members, then reduce.
  - **Keying a containment guard on the SAFE routes.** It detects safe helpers and is blind to
    unsafe ones - it is inverted by construction. Key on the RISKY primitives, plus a rule that
    follows return annotations for helpers that call no primitive themselves.
  - **A hand-maintained list of helpers to grade.** The list is what rots; derive it.
  - **Rewording a universal detection claim into a hedge.** ADR 0008 FORECLOSED names it: the
    hedge has the same falsification surface and reads as evidence.
  - **Substring matching to prove a repr withholds names.** Unsound - the shipped table contains
    the implementation's own field labels as standalone names.
  - **Repairing prose and self-auditing it.** Four consecutive rounds, fourteen false sentences.

- **Next action:** **CS-420, and NOT by hand.** Four rounds of prose repair have now each shipped a
  false sentence, several written by the commit correcting the previous one, and round four was caught
  only because an adversary read merged `main` after the items were closed and pushed. ADR 0008 states
  the rule and the artifacts exist to enforce it; what is missing is a MECHANICAL check that a
  declarative sentence in that module is backed by execution, plus a fix for the paragraph-citation gap
  that let a renamed heading go on being cited. Delete every sentence such a check cannot back. Then
  **CS-403, CS-209, CS-204** as ONE slice under the recorded `tools/precommit_gate.py` grant.
