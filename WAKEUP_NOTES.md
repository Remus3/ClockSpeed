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

## Session 70 - 2026-09-06 - CS-924 CLOSED, then its own repair REFUTED and repaired again; six items closed; the inbox has a watcher that found 27 unread where the eye found 6

- **Shipped:** **CS-924, CS-925, CS-926, CS-927, CS-931, CS-932 CLOSED.**
  **Filed:** CS-928, CS-930, CS-933, plus CS-929 whose acceptance was rewritten
  after an adversary measured the filed one unachievable.

- **THE ITEM WAS WRONG, THEN THE FIX WAS WRONG, AND AGENTS THAT WROTE NEITHER
  CAUGHT BOTH.** CS-924 claimed no hook had ever been measured running on POSIX
  at any file mode. FALSE - three modules have driven real git through
  byte-identical tracked hooks since 2026-08-22, on ubuntu, every push. The
  decisive measurement: at `4b776f2`, hooks tracked at `100644`, tier1 run
  `34067366062` was GREEN on those same arms, because the sandboxes
  `chmod(0o755)` a byte copy and the index entry never reaches git.

- **THEN THE REPAIR ITSELF WAS REFUTED, and this is the reusable part.** The
  first arm claimed to measure firing "at its tracked index mode". It could
  not: `scripts/install_hooks.py::set_executable` ORs the exec bits in unconditionally
  during Bootstrap 1/3, hundreds of log lines BEFORE the arm's `-x` check. **A
  hook tracked at 100644 would have been repaired by the bootstrap and the arm
  would still have passed - zero signal.** Repaired by PLACEMENT, not by
  wording: a new step asserts the index mode after the clone and BEFORE the
  bootstrap, over all three hooks. **A CHECK'S POSITION IN A PIPELINE IS PART OF
  WHAT IT MEASURES.**

- **The counter-example the adversary named but could not run was executed
  here.** It had no POSIX host; the index-mode half needs none, because an index
  mode lives in git rather than on the filesystem.
  `git update-index --chmod=-x` gives exit 1, intact gives exit 0.

- **Verified live, not asserted:** tier2 `34079064351` seven of seven green,
  ubuntu `git 2.55.0` blocking a real commit with HEAD unchanged. tier1
  `34080228403` discharged CS-925's honest residual - `4317 passed, 24 skipped`
  with NO skip from `test_install_hooks.py`, so both exec-bit arms ran against a
  real POSIX kernel.

- **BUILD COST EXISTS AND THE LEDGER SAID IT DID NOT.** No `mBuildCost` key -
  the naive lookup that made it look absent - but 545 of 550 build-gun recipes
  carry it as `mIngredients`, the extractor already reads them, and all 550 are
  in the registry with `inputs` populated. `automated_recipes` filters them out.
  `BOOTSTRAP.md` needs NO correction; what remains is a join (CS-930). A
  CORRECTION record was appended rather than the entry edited.

- **Surprises:** `CLAUDE.md` named a `SessionStart` hook this repo does not have
  (CS-931), found only because a sibling asked how the inbox watcher is invoked.
  Third time this session an outside question beat the inside view.

- **A DATE ERROR I MADE ALL SESSION.** I wrote `2026-09-07` throughout while the
  clock and `git log` both said `2026-09-06`. Caught by a subagent that used the
  git-verifiable date rather than matching my prose. Ten headings and every
  delivered sibling note corrected. **Read the clock; do not infer the rollover.**

- **Failed paths:** none abandoned. Two self-inflicted detours, both instructive:
  new item notes used `module.py:NNN` pointers that
  `tests/test_docs_citations.py` forbids, all converted to the symbol form; and
  a heredoc collapsed `\n` escapes exactly as this project's own memory warns,
  so payloads with escapes now go through the Write tool.

- **A RULE I BROKE, RECORDED:** the premise adversary was dispatched against
  `32255a3` and I edited `tier2.yml` while it graded. It pinned its citations to
  the committed blob and its verdict stands, but CLAUDE.md section 5 says freeze
  the candidate before dispatch. It cost nothing because the agent was careful,
  which is luck rather than method.

- **WORKTREES: 18 audited, ZERO prunable** - every one held work. 12 committed
  onto their own branches, 18 directories removed with zero loss verified AFTER
  removal, 1 stray EMPTY directory `git worktree list` did not know about, 59
  branches pruned, 53 pushed to `refs/wip/*`. **That namespace is deliberate:
  `refs/heads/**` would have fired 53 metered tier1 runs; custom refs fire none,
  and zero were observed.** My own audit tool nearly deleted two trees - a
  failed `git hash-object` returned `None` on both sides and **two failed
  lookups compared EQUAL**. Four trees hold TWO COMPETING LINEAGES of one open
  item, so none of it was merged.

- **The inbox has a watcher** (`tools/inbox_watch.py`, CS-932). Design from two
  siblings, both reasons recorded. Listing NEVER acknowledges. Seen set on DISK,
  which is what makes it survive `/clear`. Wired in the gitignored local Claude settings file, which is NOT on the
  frozen list, so the wiring is machine-local and a fresh clone does not get it. **Not yet observed firing at
  SessionStart; that is presence, not firing, and it proves out next session.**

- **Next action:** take CS-928. `docs/ARCHITECTURE.md` restates BOOTSTRAP's
  spec-of-intent as SHIPPED capability under an `Implemented by:` line naming
  modules that implement no such thing. It is the session-69 README mechanism
  still live in the file that OWNS the module map, and `ProductionPlan` was
  already measured as carrying none of the six fields it promises.

## Session 69 - 2026-09-06 - CS-922 and CS-923 CLOSED: the GitHub public face is built, and an agent that did not write the README REFUTED seven of its claims

- **Shipped:** **CS-922 CLOSED.** Repository description, homepage (`docs/adr`) and 20
  topics set and re-read from the API rather than inferred from a silent success.
  `CITATION.cff` and `.github/ISSUE_TEMPLATE/` added. `README.md` refreshed - `tier1`
  badge, the game named, and seven false capability claims removed. **CS-923 CLOSED.**
  The three tracked hooks moved from mode `100644` to `100755` under a frozen-file grant.

- **THE FINDING OF THE SESSION, and it is not the metadata.** A read-only verifier was
  dispatched to check every claim in `README.md` against the code and returned
  **REFUTED**. Four claims of SHIPPED capability described things that do not exist:
  "exact clock speeds", "total power draw" and "total build cost" are produced by nothing
  (`ProductionPlan` has no such fields, and build-cost DATA does not exist in the
  registry at all); "footprint" and "maximizes sink points per unit of raw input" are not
  selectable objectives and would be REFUSED at runtime, because `OBJECTIVES` is a closed
  three-tuple and the optimizer has no maximize direction; "constrained to what you have
  actually unlocked" is inverted, because `unlocked` is caller-supplied and the save's
  unlock state is empty by construction (CS-913); and the card accept/dismiss/snooze/pin
  paragraph was PRESENT TENSE for a package with zero executable code.

- **THE MECHANISM, which is the reusable part.** Every one of those sentences was copied
  forward from `BOOTSTRAP.md`. **A specification sentence is a claim about the INTENDED
  build. Copying it into a README silently converts it into a claim about the SHIPPED
  one.** Nothing warns you. The README had been wrong this way for as long as it has
  existed, and the only thing that found it was pointing an agent that had not written it
  at the code with instructions to default to STALE.

- **The first command in the README exited 3 on a fresh clone and nobody knew.** The
  listener is HTTPS only and `/certs/` is gitignored, so `python -m clockspeed.surface`
  cannot start without `scripts/make_cert.py`, which the README never mentioned.
  Established by PROBE - `CLOCKSPEED_CERT_DIR` pointed at an empty directory - not by
  reading the code.

- **CS-923: the three tracked hooks were mode `100644`.** Git silently refuses to run a
  non-executable hook on POSIX and reports nothing. **Windows cannot show you this** -
  measured both arms on git 2.53, a `100644` hook FIRED and blocked a commit here exactly
  as `100755` did, because Git for Windows masks `X_OK`. Found by reading a sibling
  project's CI step, not by any local signal.

- **The hole was NARROWER than the first framing and an adjudicator refuted it.** A clone
  that never bootstraps is not a mode hole at all (`core.hooksPath` is unset, so
  `.githooks/` is never consulted), and `scripts/install_hooks.py::set_executable` chmods +x on POSIX so
  a bootstrapped clone is repaired. The real residual: a BOOTSTRAPPED POSIX clone that
  then pulls a REWRITTEN hook file gets it materialised at the index mode, destroying the
  exec bit while `core.hooksPath` stays set.

- **The aggravating half is worth more than the fix.** `set_executable` - the one function
  standing between this repo and a silently absent gate - is graded by NOTHING.
  `git grep set_executable -- tests/` returns zero hits, and its POSIX branch never runs
  on the operator's machine. Filed as CS-925. This is the CS-605 shape exactly.

- **Frozen-file route followed in full.** `.githooks/*` is frozen. Routed to an
  adjudicator that did not produce the proposal, operator-approved, grant recorded in
  `docs/LEDGER.md` BEFORE the edit. Scope proven held: the three blob SHAs are identical
  before and after, so no hook content byte moved.

- **NOT DONE, deliberately.** The repository is **still PRIVATE**. `CS-G03` gates the flip
  on seven checks plus operator sign-off AND records that the public artifact ships from a
  squashed or orphan history, because every existing commit carries a real-identity author
  line and the pre-scrub `BOOTSTRAP.md`. No release cut and no social-preview card - both
  reasoned, both in the CS-922 ledger entry.

- **Cross-project.** Hook modes measured in all five trees on this disk. RiotCommander,
  LegionWallpaper and ResinCompute are clean at `100755`. **Lanternlight is `100644` on
  both hooks AND its repository is PUBLIC**, so the exposed population that is merely
  prospective here exists for it today. Note delivered to four sibling inboxes, which also
  records why Clockspeed declined a `docs-guards` workflow: RC needs one because its
  `ci.yml` carries `paths-ignore` on `**/*.md`; Clockspeed has no path filter at all, so
  `tier1` already runs the doc guards on every push.

- **Filed:** CS-924 (no hook has ever been measured FIRING on POSIX - `tier2.yml` says so
  in its own comment), CS-925 (`set_executable` ungraded), CS-926 (`ROADMAP.md` at 117 per
  cent of its soft budget, so `doc_budget.py` is permanently amber), CS-927
  (`pending.py` says NINE route templates, `health.py` holds TEN, stale since CS-912).

- **A COUNT NOT CARRIED FORWARD.** The tier-2 suite this session started was STOPPED at
  22 per cent, deliberately: it began before the new test, the mode flip and the doc
  edits, so its count could not describe the final tree. The authoritative full-suite run
  is the pre-push hook on the final tree. The verifier's `2688 passed` covers four
  packages at a mid-session tree and is NOT a whole-suite figure. Do not quote either as
  the session's suite count.

## Session 68 - 2026-09-06 - CS-921 CLOSED: the cross-project inbox is gitignored and the world name is gone; one line added to a fallback list moved THREE pin populations

**NUMBERING: there is no Session 67 entry in this file and that gap is real, not a filing
error.** The session before this one labelled its commits `Session 65 handoff` while its
handoff prompt called this one 68. Nothing renumbers cleanly, so 68 is kept because it is
the operator's frame of reference. Do not "repair" the gap by renumbering.

- **Shipped:** **CS-921 CLOSED.** `moon_sync_inbox/` is gitignored as `/moon_sync_inbox/`,
  anchored, and the world name it carried in two places is gone. Detail in `docs/LEDGER.md`.

- **In flight:** nothing. The tree is clean, main is pushed, and CI was read rather than
  assumed. The suite was run SERIALLY because Riot Commander's lane was running eight
  pytest processes throughout - `-n auto` on top of that is the documented fork-exhaustion
  trap and would have produced false reds on unrelated subprocess tests.

- **Decisions:** no ADR. Three worth not re-litigating, all recorded with their fences in
  the ledger entry: the world name was NOT added to `world_name_exclusions` (repo-wide and
  permanent, to spare two words in one gitignored note - the same trade `precommit_gate.py`
  already refused once at CS-208); the pattern is ANCHORED rather than the bare form the
  sender asked for; and the citation pin was converted to the SYMBOL form rather than
  having its digest re-cut, which the guard refuses in terms worth keeping.

- **Surprises:**
  - **Nothing contradicted `BOOTSTRAP.md`.**
  - **`grep -c $'\r'` DOES NOT COUNT CARRIAGE RETURNS in this harness's Git Bash.** It
    returns the TOTAL line count on a pure-LF file. Measured with a control: 3 on a file
    with zero CRs, 3 on a file with three. It nearly caused a normalising pass over
    `.gitignore`, which was already clean - the false reading agreed exactly with the known
    `edit-tool-writes-crlf` fault. Count line endings in Python on raw bytes. Filed to the
    harness memory store as `grep-cr-count-matches-every-line`.
  - **A SIBLING READ ONE OF THIS PROJECT'S OWN PUBLISHED NUMBERS BACK STALE.** ResinCompute
    credited `config/ports.json` with "its own 8900-8911 allocation"; that band was vacated
    2026-08-29 and this project holds 8920-8939. The sentence was true about the historical
    allocation - what did not travel with the number was that it is former. **That is
    CS-920's thesis arriving from outside the repo**, and it is now a worked example rather
    than a hypothetical. CS-920 is NOT closed by it.
  - **A cross-project note can block this repo's commit gate by naming a sibling project.**
    The gate's world detection is value-based and whole-word, so a two-word project display
    name whose second word is a world on this machine trips it. Carried back to the channel
    with the fix: spell siblings in their closed-up directory form.

- **Failed paths:** adding one entry to `tests/conftest.py`'s no-git fallback list looked
  like a one-line sync and was not - it shifted every line below it by one and moved a
  line-number citation pin off its target, turning `tests/test_docs_citations.py` red. This
  is the **CS-500 defect class arriving from the other direction**, and it confirms the
  standing warning: a citation-pin repair MUST land in the same commit as the edit that
  moved the line. A partial commit is red by construction.
  **It moved THREE pin populations, not one, and the third only showed up in the FULL
  suite** - `UNVERIFIED_LINE_POINTERS`, `FORGIVEN_LINE_POINTER_CEILING`, and the deep
  archive's `ARCHIVE_ROT` in `tests/test_archive_rot.py`. A targeted run over the guards
  that consume the enumeration passed while the archive arm was still red. Budget for
  the full suite whenever a line is inserted into a module the docs pin by NUMBER.
  **AND THE REPAIR ITSELF WENT RED ON THE NEXT RUN.** The comment justifying the
  archive re-pin spelled the stale pointer out in the colon-number form, and the
  forbid arm counted it as a NEW line pointer in a tracked module. A note ABOUT a
  line pointer is a line pointer as far as the guard can see; it cannot tell the
  two apart and should not try. Name the symbol, say the number in prose. THREE
  full suite runs were spent on one line of test data, and only the third was
  green - budget accordingly.

- **Next action:** take **CS-919**. Its fence is unchanged and load-bearing - DO NOT RUN
  THE LANE FOR A NIGHT UNTIL IT IS CLOSED, because this session watched three other
  projects push to this box while it worked, which is exactly the condition that makes the
  lane's CI attribution wrong.
