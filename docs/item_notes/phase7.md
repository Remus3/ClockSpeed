# Clockspeed - live per-item detail, phase 7 - public flip gate

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 7` heading.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, and arrived
there from `ROADMAP.md` and `docs/history_notes.md` before that. A body therefore
still reads as it did when it was written, including the parts a later session
measured false and corrected in place rather than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-701

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. FULL ENTRY relocated to this file under **CS-701 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

NOTE: filed 2026-08-16 by the CS-427 adversary, which hit it while scanning that slice's diff for leaked personal data and correctly classified it as a PRE-EXISTING FALSE POSITIVE rather than a finding against the slice. Measured: the operator git author line coincides with one 4-character world name on this machine, and it is present identically on `8b3fb9d` and `1009681` - `author-line hits: 1, body hits: 0` on every revision checked. **NOTHING IS LEAKED BY THIS TODAY** - the world name is not disclosed by the author line, the coincidence runs the other way. The problem is mechanical and arrives later: **a world-name-keyed PII scan will trip on EVERY COMMIT IN THE REPO**, and a scan that is red on correct history is a scan someone switches off. CS-700's checklist includes a full-history PII scan across tracked files and commit messages, so settle the exemption rule before that gate runs rather than while it is failing. Note the CS-209 precedent: narrowing a PII blocklist by default to pre-empt a collision was DENIED BY MEASUREMENT, so an exemption here must be a named, recorded exception rather than a shortened matcher.

### Identity axis hardening - filed 2026-10-04 from an adversary pass

Check `I` in `tools/flip_checks.py` reads the RAW commit objects: every git call there that
names no environment runs with replace objects off, and a shallow or grafted repository is
refused by name rather than walked - in the identity walk and in checks 1, 2 and 4. The arms
are multi-commit synthetic histories (tip-only, first-parent, malformed-skip and case-fold
mutants killed); the record is in `docs/LEDGER.md`. The trailer axis, check `T`, now gets the
same treatment in `tools/trailer_census.py`: every git call runs with replace objects off, and
`walk` refuses a shallow or grafted repository by name (exit 2). It is a mirror, not an import,
because `tools/flip_checks.py` imports the census. CI DEPTH: the tier-1 job that runs the
census checks out with `fetch-depth: 0`, so the refusal is unconditional and cannot redden it;
`tests/test_trailer_routes.py` already pins that depth. Arms: replace by content, replace
`--graft`, shallow and grafts over a three-commit history; the record is in `docs/LEDGER.md`.

### Acceptance

the tier-3 PII scan over tracked files AND commit messages runs clean, or the collision is recorded as a known-accepted false positive with the exact matching rule that exempts it

## CS-815

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); FROZEN FILE, needs its own grant. Detail in this file under **CS-815 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 adjudicator as the FOURTH site of that defect class, found by grepping for the
shape rather than by reasoning about it. `.claude/settings.json` names `pythonw tools/pretooluse_gate.py`
and `python tools/edit_lint_check.py` with NO resolution ladder and NO probe of any kind. By that
gate's own stated protocol - exit 2 denies and every other status is non-blocking - a missing or
substituted interpreter yields a non-2 status and the gate FAILS OPEN.

**IT IS MILDER THAN THE GIT HOOKS AND THAT IS RECORDED SO NOBODY RE-RATES IT UPWARDS.** CLAUDE.md
section 2.2 makes the Claude hooks a convenience layer and `.githooks` authoritative, so the tier-0
guarantee does not rest on this file. **IT IS ALSO NOT FIXABLE THE WAY CS-703 WAS,** because JSON
cannot express a probe: the fix has to live in the tools the JSON names, or in a wrapper.

`.claude/settings.json` is on the CLAUDE.md section 6 frozen list, so this needs its own operator
grant and its own adjudication. It was explicitly OUT of the CS-703 grant and is not claimed closed
by it.

### Acceptance

such a hook BLOCKS or is loudly reported, proven by pointing it at a program that ignores its arguments


### FILED 2026-09-25, landed with one check owed (session 115)

The wrapper and the two command values landed; see the CS-815 LANDED record in
`docs/LEDGER.md`. The ONLY remaining check: the operator confirms by eye that the
desktop app shows the `REFUSED (CS-815)` hook-error line for a failed probe. If it
does, CS-815 closes; if not, rebuild the report on the exit-0 JSON systemMessage route.

## CS-700

### FILED 2026-09-07 (session 73), queueing the plan session

**THE NEXT SESSION PRODUCES A PLAN AND EXECUTES NOTHING.** The session after it
implements. That split is the operator's instruction and it is also the right
shape: every trap in section 2 below was paid for by a sibling who wrote the
verdict before doing the act, and the deliverable that prevents a repeat is a
plan a second pair of eyes can refuse.

**WHERE THE PLAN GOES.** Into this section, as CS-700's detail. It gets no new
file, because a new owner file needs a row in the CLAUDE.md topology table and
the plan is not a new fact - it is this item's detail.

**THE ONE DECISION THE PLAN MUST MAKE, AND IT IS AN ADR.** CONVENTIONS section
17 ends with a clause this project has never answered: **if history is dirty,
the honest fix is a fresh-history public repo, not a rewrite that will be
incomplete.** RC ran the rewrite branch today and needed two passes plus a
delete-and-recreate; the plan must choose between the branches deliberately and
record the choice in `docs/adr/`, not discover it midway.

### 1. What is already measured, so the plan does not re-derive it

**`refs/pull` on this remote is ZERO, and it is armed.** Measured 2026-09-07:

    CONTROL   git ls-remote origin 'refs/heads/*'          -> 6 rows
              git ls-remote origin 'refs/pull/*/head'      -> 0 rows
    STRONGEST git fetch origin '+refs/pull/*/head:refs/remotes/pullcheck/*'
                                                            -> exit 0, 0 refs

The control is the load-bearing half and it is LL's practice, not this
project's: an empty result and a broken pattern print the same thing and
neither errors. RC measured 13 on its own remote by the same method, with 531
commits reachable from no other ref. **This project has no permanent
pull-request snapshots to purge.**

**Sibling names are CLEARED.** The operator ruled 2026-09-07 that cross-project
references are acceptable for all projects at this time. The plan does not
budget for scrubbing them and does not need a per-sibling consent round.

### 2. The four traps RC measured the hard way, none of them closed here

All four were measured by RC on 2026-09-07 and reported to this channel.

**(a) A mirror clone DOES fetch `refs/pull/*/head`.** Not a risk here given
section 1, but the plan must still state which refs it expects a mirror to
carry and check what actually arrived rather than reasoning about what GitHub
advertises.

**(b) A ref-pattern check can fail GREEN.** `for-each-ref` and `ls-remote` do
not take the same pattern language and neither errors on a pattern matching
nothing. RC's first deletion pass matched nothing while 13 refs existed and
then reported "remaining: 0" using the same broken pattern. **Every verification
step in the plan carries a positive control in the same command family, or it
is not a verification step.**

**(c) A content scrub can be COMPLETE and still publish the names, because a
filename is not content.** Filed separately as CS-953 and it is the trap aimed
at this project. Do not treat CS-953 as satisfied by anything in this item.
**REPOINTED, filed 2026-10-11:** CS-953 closed as MOOT, not satisfied - `docs/LEDGER.md`, the
2026-10-11 CS-953 record; the trap is covered by `tools/flip_checks.py::history_paths`.

**(d) Deleting a repository deletes its LFS store.** The plan enumerates what
the forge holds besides the object store - pull refs, LFS, releases, Actions
artifacts, caches, wikis, pages branches - and states the disposition of each.

### 3. What the plan must check IN HISTORY, not in the working tree

The working tree is the easy half and it is not the half that leaks. For each,
the plan states the command, its positive control, and the disposition:

- The platform account id, the world name, the Windows account name, and any
  absolute home path - non-negotiable 3.
- Any save file or save-derived artifact - non-negotiables 11 and 12. Including
  anything a header parser ever echoed into a fixture, a log or a test output.
- Publisher-owned game data, extracted or lifted, in any commit - the
  never-commit rule and CONVENTIONS 17 gate item 4.
- `data/` and `moon_sync_inbox/`, both gitignored NOW. Gitignored now says
  nothing about every commit since the first, and the inbox holds sibling notes
  and at least one delivered reference payload.
- Credentials and tokens, whole history - gate item 1.

### 4. The remaining CONVENTIONS 17 gate items, which are not scans

Gate items 3, 5, 6 and 7 - the third-party licence audit, README-gets-an-
outsider-to-a-first-result, all doc cross-references resolve, and a clean-
checkout probe on a machine that has never seen the project. **Gate item 7 is
the one this project will fail today and already knows why: CS-952 records that
the watcher wiring is gitignored, so a fresh clone runs no watcher.** The plan
sequences CS-952 relative to the flip rather than discovering the conflict
during it.

### 5. What the plan is NOT

Not the execution. Not a scrub run, not a mirror clone, not a visibility
change. **A session that produces the plan and also runs any part of it has
removed the second pair of eyes the split exists to buy**, which is CLAUDE.md
section 5's rule that the agent producing a thing never grades it.

### THE PLAN - filed 2026-09-08 (session 74), REPAIRED the same session after refutation

**This section is the deliverable CS-700 asked for.** The session that wrote it
ran no scrub, made no mirror clone, changed no visibility, and made no write of
any kind against the remote. Its reconnaissance was read-only.

**IT WAS REFUTED ONCE AND REPAIRED.** A read-only adversary graded the first
draft at its frozen SHA and returned REFUTED on all six lenses. Nine repairs were
named; eight are applied below and the ninth is an operator decision recorded in
section 6 as a hard blocker. **The corrections are kept visible rather than
smoothed away**, because two of them are instances of the very trap this item
exists to defend against.

**THE DECISION IS ADR 0018**. In one line: **the publishable commit graph is
clean of CONTENT and is kept unrewritten; the REMOTE is deleted and recreated,
and `main` alone is pushed to it.** Read the ADR before the steps.

#### 0. Two corrections to the first draft, both trap (b) firing on its own evidence

**CORRECTION 1 - "the 53 wip refs are invisible to REST and GraphQL" IS FALSE.**
The first draft asserted it from a listing that returned 11. Measured properly:

    BROKEN    gh api "repos/<owner>/Clockspeed/git/refs"        -> 11 (unpaginated)
    CORRECT   gh api --paginate ".../git/refs?per_page=100"     -> 64, INCLUDING all 53
    CONTROL   git ls-remote origin 'refs/wip/*'                 -> 53
              git ls-remote origin 'refs/heads/*'               -> 6

The refs are real and the count is right; the claim about their visibility was
produced by an unpaginated query that returned a short answer without erroring.
**That is trap (b) exactly, occurring inside the evidence offered as proof that
trap (b) had been designed out.** It is recorded here rather than deleted because
the lesson is the point: a control proves your pattern MATCHES, and it does not
prove your query is COMPLETE. Pagination is a second failure mode and it needs
its own control - compare two command families, not two patterns.

**CORRECTION 2 - the 53 wip refs do not exist locally.** `git for-each-ref
'refs/wip/*'` returns 0, because `remote.origin.fetch` is heads-only. The first
draft's S3 would have bundled nothing and its stated control - bundle count
against "the count going in" - computed both sides from the same empty local
pattern, so **0 == 0 would have passed green** while 53 refs went to the
deletion unpreserved. Repaired in S3 below.

**Counts are stated AS OF A SHA from here on.** The first draft wrote "520
commits" and it was 521 by the time the adversary read it, because the draft's
own commit landed in between. That is the session-73 ledger lesson repeating:
a count written into a record is true at the instant of writing and the session
does not stop there. Cite the SHA or cite nothing.

#### 1. The measurements this plan rests on

Taken 2026-09-08 at `4338fde`, read-only, each zero carrying a positive control
in its own command family and a negative control where a zero was possible.
Independently re-derived by an adversary with its own controls, which agreed.

**(1a) The publishable graph is clean of CONTENT on six axes.** Personal data,
save artifacts, publisher-owned game data, `data/` and `moon_sync_inbox/` paths,
credentials, and non-ASCII - in blob content, in tree paths and in commit
messages as three separate channels, per trap (c). Nothing reachable from `main`
hits any axis. **COST: about 7 seconds** over every object on disk.

**(1b) A FOURTH CHANNEL EXISTS AND IT IS NOT CLEAN: commit author and committer
identity.** At `c885879`, 520 of 521 commits on `main` carry a real personal
email address in BOTH the author and the committer field; one carries a GitHub
noreply address. **CONVENTIONS 17 gate item 2 does not cover it** - it says
"tracked files and commit messages", and identity is neither. Neither did the
first draft. See section 6: this is an operator decision and it blocks S9.

**(1c) The dirt that exists is off-main and has never been pushed.** The
4-commit local branch `archive/local-history` - the deliberately retained
pre-scrub history - carrying 3 blobs across 2 paths; plus ref-less commit
objects and pathless blobs that no push and no clone transfers and that
`git gc --prune` deletes.

**(1d) The forge holds nothing of value to lose.** Zero issues, PRs, releases,
assets, packages, LFS objects; no wiki content despite the toggle being on; no
Pages; one collaborator; no branch protection, rulesets, secrets, variables,
deploy keys or webhooks. **Trap (d) does not fire: the LFS store is empty,
confirmed with a control** - `text=auto` hit 60 of 60 tips, `filter=lfs` hit none.

**(1e) What survives a force-push, which is why there is no force-push.** All 53
`refs/wip` refs, 5 `salvage/*` tags, 5 non-`main` branches, 233 Actions run
records and their logs, 17 live artifacts of 35, and 11 caches totalling about
534 MiB. **21 of the 233 runs are FAILED runs, and a failed run's log is the
highest-risk surface on the forge for absolute paths.** Logs returned 200 on both
the oldest and newest run.

#### 2. Three limits that are NOT coverage, carried as work

- **Needles came from the save directory as it exists TODAY.** A leak naming a
  since-deleted world would not have been seen.
- **The save header's PLAYER DISPLAY NAME was not searched at all**, because
  deriving it requires parsing a save. Non-negotiable 12 names it as a plaintext
  personal-data field. **S2 searches it, or the ledger records that the flip
  shipped without searching it.** Those are the only two honest outcomes.
- **The credential axis needs an allowlist before S1 can abort on a hit.** An
  honest needle set returns 166 hits on `main` - `AKIA` 140, `github_pat_` 9,
  `AIza` 9, `BEGIN PRIVATE KEY` 8 - every one of them a FIXTURE. Mapped to
  paths over all main-reachable blobs, the allowlist is exactly SIX files:
  `tools/precommit_gate.py`, `tests/test_precommit_gate.py`,
  `tests/test_pretooluse_gate.py`, `tests/test_make_cert.py`,
  `docs/history_notes.md` and `WAKEUP_NOTES.md` - the scanner's own pattern
  table, its tests, and two notes quoting them. Real prefixes (`ghp_`, `gho_`,
  `sk-ant-`, `xoxb-`, RSA bodies) return 0, so **the credential axis is CLEAN and
  this is a FALSE-ABORT hazard, not a leak.** **Without a recorded
  allowlist, a literal S1 aborts the entire flip on this project's own secret
  scanner.** The allowlist is by PATH plus needle, is written into the plan
  before S1 runs, and follows the CS-209 precedent: a named recorded exception,
  never a shortened matcher.

#### 3. The steps. Every step states its command, its control, and its abort

**The rule for every step below: a step whose positive control does not return
non-zero is not a passed step, it is an UNMEASURED step, and it aborts the
sequence.** Where a zero is possible, a negative control runs on the same pass.
Where an API is paged, a second command FAMILY confirms the count - correction 1.

**S0 - Write the needle set and the allowlist into this section.** Commands,
needles, both controls, and the section-2 allowlist by path. **The first draft
recorded outcome counts and no commands, which is not reproducible**: a session
holding only that text would have invented its own needles and declared itself
clean. S0 exists so S1 is auditable by someone who was not here.

**S1 - Six-axis pass over the publishable closure.** Closure is everything
reachable from what S7 will push, computed as such rather than assumed.
Controls: a present token expected in the thousands, a synthetic absent token
expected at 0 on the same pass, path controls on `.md` and `.py`, a commit
message control. ABORT on any hit outside the S0 allowlist.

**A SEVENTH AXIS, filed 2026-09-24 by CS-1180 under the ADR 0018 amendment:** the
trailer-shaped census S7a defines, over the publishable closure. The six axes above
never looked for an agent co-authorship trailer. S1 runs BEFORE S7a strips them, so
here its hits ARE the population S7a removes: record that count as an EARLY WARNING
only, ABORT if it is zero, and ABORT unless every hit is a line S7a's strip removes -
the final body line of a non-merge commit's message, preceded by a blank line, one per
commit - so a census hit the strip would leave behind aborts here, before any SHA
changes. S1's count is NOT S7a's baseline: S6 and S7 change `main` between S1 and
S7a, so S7a takes its own baseline census immediately before it rewrites. At S8,
after the strip, ABORT on any hit at all; the positive control there is the same
census over the preservation bundle taken before S7a, returning the count S7a's
pre-rewrite baseline recorded.

**S2 - Search for the player display name.** Derive it without writing it
anywhere; report a count, never a value. ABORT on any hit.

**S3 - Preserve every non-`main` ref, REPAIRED.**
`git fetch origin '+refs/wip/*:refs/wip/*' '+refs/heads/*:refs/preserve/heads/*' '+refs/tags/*:refs/tags/*'`
FIRST - correction 2 - then bundle. **The control compares the bundled ref count
against `git ls-remote origin` output, NEVER against a local pattern**, because
the local pattern is what returned 0. Include `archive/local-history`.

**S4 - Verify the bundle is RESTORABLE, not merely well-formed.**
`git bundle verify` checks prerequisites against the repo it is run in and is
NOT a restore test. Clone the bundle into a scratch directory and assert its ref
count and every tip SHA equal the pre-deletion `ls-remote` set. **No irreversible
step runs until a second, independently readable copy has been proven to exist.**

**S5 - The bundle lives OUTSIDE the repo tree, or `*.bundle` is ignored first.**
Nothing ignores it today, and it carries `archive/local-history`, the one bucket
that must never be published. A bundle committed by accident publishes precisely
what the plan exists to withhold.

**S6 - Gate items 3, 5 and 6.** Licence audit against CONVENTIONS 14 over
`pyproject.toml` and `shell/package.json`; `README.md` gets an outsider from zero
to a first result; all doc cross-references resolve. **Gate item 6 needs a tool
BUILT - it does not exist.** `tools/drift_guard.py` has `link_targets` and
`_citation_findings`, but they are called only from `guard_memory` and scoped to
`memory/`. Nothing resolves markdown links in `docs/`, `CLAUDE.md`, `README.md`
or `ROADMAP.md`. Budget a build, not a run.

**CORRECTED 2026-09-24 by the N0 adjudicator ruling at `599528c`: the sentence above saying nothing resolves
markdown links is FALSE.** `.github/workflows/tier1.yml` step `Markdown link check`,
present since the first commit `9d24823`, resolves every relative markdown link in
every tracked `.md` file on every push. It strips fragments, never fetches a URL and
runs no orphan or staleness sweep. So gate item 6's real gap is narrower: the orphan
sweep, the staleness sweep and the anchor check, which CS-1184 owns. The build
budgeted here is that, not a link resolver.

**S7 - Gate item 7, and CS-952 closes here.** See section 5.

**S7q - QUIESCE EVERY PUSHER, filed 2026-09-25 by CS-1190.** Runs after S7 and
before S7a's baseline, and HOLDS THROUGH S12a. The lane worker pushes at
`tools/headless-queue.md` section 10 step 9 - to `main`, or to its lane branch when
`main` refuses it - on history S7a has not rewritten, and a clone or session the
flip cannot see can push as well. A push landing after S3 is a ref S9a destroys
unpreserved; a push landing after S9b is un-rewritten history on the remote S12
publishes. Nothing here was run when it was filed: these are the method and its
controls, and the results are recorded at run time in the companion note beside the
preservation bundle, outside the tree per S5. Four parts, in order, each aborting
the sequence on a failed or UNMEASURED control:

1. **STOP THE LANE.** Write the box-wide sentinel, the `STOP` entry of
   `ops/loop/queue_loop.py::STOP_RELPATHS`, into this checkout's control directory.
   Control: `ops/loop/queue_loop.py::stop_reason` returns that name afterwards. The
   sentinel is read at a cycle boundary and does not stop a cycle already running
   (`docs/OPERATIONS.md` section 10.5), and it is read only by drivers of THIS
   checkout - so it is not by itself the stop. Part 2 is.
2. **NO DRIVER AND NO WORKER VERIFIED RUNNING, box-wide, in three families.** A live
   one is waited out - the sentinel makes its cycle the last - or stopped per
   `docs/OPERATIONS.md` section 10.5, and then all three families re-run in full.
   - THE PROCESS TABLE: every process whose command line names `queue_loop.py` - a
     driver, under any interpreter, from any clone - or `run_lane.ps1` - a worker's
     wrapper, which a killed driver can orphan - read over `Win32_Process`
     command lines. Expected zero. A python or PowerShell image whose command line
     cannot be read COUNTS AS A HIT, because an elevated or scheduled driver is
     exactly what reads that way. Positive control, same pass: a stand-in started
     first, an interpreter that only sleeps and carries both strings as inert
     arguments, must be counted - then stopped with `taskkill`, never the
     PowerShell cmdlet.
   - THE DRIVER MUTEXES: for every lane in `ops/loop/lanes.py::LANES`,
     `ops/loop/winmutex.py::hold` with `timeout=0` on
     `ops/loop/queue_loop.py::driver_mutex` AND on
     `ops/loop/queue_loop.py::worktree_mutex` of that lane's worktree, released at
     once. `ops/loop/winmutex.py::MutexTimeout` is a live driver. The worktree
     mutex is the box-wide half: keyed on the working directory alone, it sees a
     driver another clone started, which the per-checkout driver mutex cannot. A log
     line carrying `winmutex: UNSERIALIZED` means the hold ran with no lock -
     fail-open, or off Windows - so the family measured nothing: UNMEASURED.
     Positive control, same pass: a stand-in holding one lane's driver mutex
     through `hold` makes the probe raise `MutexTimeout` on that name.
   - THE LANE LOCK: `ops/loop/lanes.py::lane_state` for every lane answers FREE or
     RECLAIMABLE, never RUNNING; it probes the recorded pid and mutates nothing,
     so it sees a worker whose driver is gone. Positive control, same pass: the
     same call pointed by its `root` argument at a scratch root holding a lock
     whose pid is the live stand-in answers RUNNING.
3. **STOP EVERY OTHER PUSHER AT THE FORGE.** The worktrees of this repository are
   enumerable - `git worktree list --porcelain` - and each is listed in the note
   and any session in it ended; other clones and other sessions are NOT
   enumerable, so no local probe can claim them stopped. The old remote is
   therefore ARCHIVED, `gh repo archive`, which makes it read-only to every pusher
   from every checkout. Archiving is reversible, so it is not one of the acts the
   own-words confirmation covers. Control: the REST read of the repository's
   `archived` field returns false before and true after; the before read is the
   positive control that the field is read at all. NOT MEASURED when filed: that
   an archived repository refuses a push is the forge's documented behaviour, not
   a measurement here - part 4 and S9a's precondition catch a push it failed to
   refuse, and S9a owns what happens if the archive also refuses the delete. The
   archive covers the OLD remote only; S10b closes the recreated one.
4. **RECORD THE REF SET THE QUIESCE FROZE.** Read the old remote's complete ref set
   in two families - `git ls-remote origin` and the paginated REST refs listing,
   per correction 1 - which must agree, and compare it with the S3 bundle's. Equal:
   record it in the note. Different: a push landed between S3 and the quiesce, so
   S3 and S4 re-run now, and the comparison again.

The quiesce is not re-run by a late-commit restart - it holds throughout, and S9a's
precondition re-measures it. It lifts only after S12a passes, or when the flip is
abandoned before S9a - unarchive, then remove the sentinel. After S12a, every lane
worktree is re-cut onto the published `main` before the sentinel is removed, and
every other checkout re-clones or resets onto it before its next push: a branch cut
from history S7a did not rewrite, pushed to the published repository, publishes
exactly the identity and the trailers S7a removed.

**S7a - Rewrite commit identity across every commit on `main`**, per the ruling
in section 6. No commit count is written here: the census and the count controls
below measure it at run time, and a count written into this plan is stale by the
time S7a runs. Author and committer, plus removal of the agent co-authorship trailer
line and its preceding blank line (ADR 0018, amended 2026-09-24); trees, paths,
dates, parent topology and every other message byte unchanged - each of those is
asserted by a control below, none is assumed. **BASELINE, immediately before the
rewrite and after S6 and S7 have landed:** bundle `main` at its current tip beside
the S3 bundle, placed per S5 and proven restorable per S4 - that is the
preservation bundle taken before S7a - and take the trailer-shaped census over it. That
count, not S1's, is the pre-rewrite count. The same baseline REGENERATES the SHA citation
gate's historical set - `python tools/sha_citation_gate.py --emit-historical` on the
un-rewritten tip, committed BEFORE the bundle is taken, so the set rides through the
rewrite inside the trees - and REQUIRES `python tools/sha_citation_gate.py
--flip-readiness` to exit 0 on that tip: no token in tracked text may name a published
commit outside the set. Any other exit ABORTS S7a. See "SHA citation gate across S7a"
below.

**THE TRAILER-SHAPED CENSUS - defined here and ONLY here; every other file points at this
paragraph.** Walk every commit message reachable from the tip being measured and
count the lines that sit at column zero, carry a colon, and whose token before the
first colon - trailing whitespace trimmed - folds case-insensitively to
`co-authored-by`. That is the shape git's own trailer parser reads and the shape
`.githooks/commit-msg` refuses. A plain substring search is NOT this census: it also
matches prose naming the trailer.

**THE IDENTITY ALLOWLIST** holds exactly one address, the ruled noreply address,
derived at run time from the operator's forge account and never written into a
tracked file, plus exactly one name, the operator's chosen author name, derived the
same way and never written into a tracked file either - CS-701 records why that
name must stay out of tracked text. Every author name and address and every
committer name and address in the rewritten graph must be on it; CS-701 covers the
same identity surface and is settled with it.

**FORBIDDEN, because each re-commits and restamps what S7a must keep:**
`--reset-author`, `--ignore-date`, `--committer-date-is-author-date`, any `--date`
override, and any rebase, amend, cherry-pick or re-commit route. The rewrite is one
history-rewriting pass that maps identity and message bytes only, and its tool and
exact invocation are recorded before it runs.

**THE S7a SCRIPT, RECORDED VERBATIM - filed 2026-10-04 by the CS-700 pre-S7a ruling.**
S7a is RECORDED HERE, not shipped as a tool: no tracked file runs it and no test imports
it. The tool is `git-filter-repo`, a run-once tool with its `CONVENTIONS.md` section 14
verdict in `THIRD_PARTY.md` under Items considered. Copy the fenced block byte-for-byte
into a file named `s7a_rewrite.py` OUTSIDE the tree (S5), as ASCII with LF line ends and
one final LF, and assert its SHA-256 before running it:

    SHA-256 of s7a_rewrite.py: 0625eab773323407ba7008a31b989eccf272d43fbe9696b728f1bd818a545a23

The command line, run with the working directory at the fresh `git clone --no-local` of
the primary tree that S7a rewrites - never the primary itself:

    python <path-to>/s7a_rewrite.py <primary-tree>

`<primary-tree>` is the repository root, whose path `CLAUDE.md` section 2 owns. The
script derives the one name from that tree's `git config user.name` and the one address
from `gh api user` at run time, aborts unless the tree's configured address equals the
derived one, and prints counts only - no identity value, home path or account id is in
its text. Measured on 2026-10-04: two fresh clones of `main` at `69d44c5`, the rehearsal
and an independent re-run of THIS text, each printed `commits seen 1527; messages
stripped 18`, passed every control below, and yielded the same output tip `389fe4a`, with
`c6f3687` mapped to `b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec`. Those are the counts at
that tip; S7a measures its own at run time. The rewrite writes its old-to-new commit map
inside the clone's git directory; the map and every bundle are kept OUTSIDE the tree per
S5 and never committed.

```python
"""CS-700 S7a rewrite. Run with cwd = the clone being rewritten; argv[1] = the primary tree.

Identity: name = git config user.name of the PRIMARY tree (the single author name
already on every main commit); email = <id>+<login>@users.noreply.github.com derived
from `gh api user`, asserted equal to the primary config email. Values never printed.
Strip: the one trailer-shaped census line (column zero, token before first colon,
rstripped, casefold == co-authored-by) that is the final line, plus the blank line
before it. Anything else shaped like a hit aborts.
"""

import json
import subprocess
import sys

import git_filter_repo as fr

if len(sys.argv) != 2:
    sys.exit("usage: python s7a_rewrite.py PRIMARY_TREE  (cwd = the clone to rewrite)")
PRIMARY = sys.argv[1]


def _out(args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


user = json.loads(_out(["gh", "api", "user"]))
NAME = _out(["git", "-C", PRIMARY, "config", "user.name"]).encode("utf-8")
EMAIL = f"{user['id']}+{user['login']}@users.noreply.github.com".encode("utf-8")
if _out(["git", "-C", PRIMARY, "config", "user.email"]).encode("utf-8") != EMAIL:
    sys.exit("ABORT: primary config email is not the derived noreply address")


def is_hit(line: bytes) -> bool:
    if b":" not in line or line[:1] in (b" ", b"\t"):
        return False
    tok = line.split(b":", 1)[0].rstrip()
    return tok.decode("utf-8", "replace").casefold() == "co-authored-by"


STATS = {"stripped": 0, "commits": 0}


def strip(msg: bytes) -> bytes:
    lines = msg.splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if is_hit(ln.rstrip(b"\n"))]
    if not hits:
        return msg
    if len(hits) != 1 or hits[0] != len(lines) - 1 or hits[0] < 1 or lines[hits[0] - 1] != b"\n":
        raise SystemExit("ABORT: a census hit the strip cannot remove cleanly")
    STATS["stripped"] += 1
    kept = lines[: hits[0] - 1]
    if lines[hits[0]].endswith(b"\n"):
        return b"".join(kept)
    # trailer carried no final LF: removing the two lines leaves the body's own LF
    return b"".join(kept)


def commit_cb(commit, _metadata):
    STATS["commits"] += 1
    commit.author_name = NAME
    commit.author_email = EMAIL
    commit.committer_name = NAME
    commit.committer_email = EMAIL
    commit.message = strip(commit.message)


args = fr.FilteringOptions.parse_args(
    [
        "--refs", "main",
        "--preserve-commit-hashes",
        "--preserve-commit-encoding",
        "--prune-empty", "never",
        "--prune-degenerate", "never",
        "--quiet",
    ]
)
fr.RepoFilter(args, commit_callback=commit_cb).run()
print(f"s7a: commits seen {STATS['commits']}; messages stripped {STATS['stripped']}")
```

Controls, each pairing a commit of the pre-S7a bundle with its image on the
rewritten `main` - by the rewrite tool's old-to-new commit map where it writes one,
otherwise by position in `git rev-list --topo-order --reverse` of each tip; the
parent control below fails a wrong pairing closed:

- COUNT: the rewritten commit count equals the pre-rewrite count.
- TREE: every paired commit's tree hash is byte-equal - only messages and identity
  change, so a single differing tree ABORTS.
- DATES: every paired commit's author date and committer date, read raw as epoch
  seconds plus timezone offset, are equal. Any difference ABORTS.
- PARENTS: every paired commit has the same parent count, and each new parent is
  the image of the corresponding old parent under the pairing, in order.
- MESSAGE: byte-exact, commit for commit, on the raw message - the bytes after the
  header's blank line in `git cat-file commit`, never `%B` or any `git log` format,
  which normalise trailing whitespace. A line here is its bytes INCLUDING its
  terminating LF when it has one. A commit with no census hit passes only if the new
  message is byte-equal to the old. A commit with a census hit passes only if the
  new message equals the old with exactly two lines removed - the trailer line and
  the blank separator line immediately before it - and nothing else, so
  `subject LF LF body LF LF trailer LF` must become `subject LF LF body LF`, and a
  trailer carrying no final LF removes the same two lines. A result that keeps the
  blank separator, loses or gains any other byte, or gains or loses a trailing LF
  ABORTS.
- CENSUS: the trailer-shaped census returns the pre-rewrite count, non-zero, BEFORE and
  zero AFTER, and exactly that many commits have a changed message.
- IDENTITY: `git log --format='%an%x09%ae%x09%cn%x09%ce'` over the rewritten graph
  yields exactly one name and one address, both on the identity allowlist, in the
  author AND the committer fields, with a pre-rewrite control showing the bundle
  yielded two addresses.
- CS-704 IMAGE: the commit-map entry for `c6f3687` must equal
  `b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec`, or ABORT. That pair is the CS-704 accept
  set the tier-1 trailer-census step pins (`.github/workflows/tier1.yml`, graded by
  `tests/test_trailer_routes.py`); any other image leaves the published `main` with no
  member of the set as an ancestor and every CI run red.
- OUTPUT TIP: once every control above passes, S7a RECORDS the rewritten `main` tip
  SHA. S8 scans exactly that SHA.

**The S3/S4 bundle must already exist and be proven restorable before this runs**,
because this step invalidates every SHA the remote holds.

**THE ONE LATE-COMMIT RULE: a commit landing on `main` after S7a and before S12
completes VOIDS S7a THROUGH S8a** - including a commit after S8a's ruling. Nothing
is re-adjudicated over a range, and no verdict is carried forward. Never re-run S7a on
already-rewritten history: its census would read zero before and its identity
control would find one address, so both of its positive controls would fail - and
rightly. Instead, restore `main` from the preservation bundle taken before S7a,
bring the new commit's change onto that un-rewritten tip, take a fresh preservation
bundle at the resulting tip (placed per S5, proven restorable per S4), which
replaces the earlier one as S7a's baseline, and run S7a, S8 and S8a again from the
top. A correct restart therefore sees S7a's census non-zero before and its identity
control yield two.

**S8 - RE-RUN S1 AND S2 IN FULL, AND S7a's IDENTITY CHECK.** S6, S7 and S7a all
change `main`. **S1 scanned a tree that no longer exists by push time**, and the
first draft said so in prose while omitting the step. It costs about 7 seconds.
This is the last check before anything irreversible. The re-run includes S1's
seventh axis, the trailer-shaped census, which must return zero here, and it re-runs S7a's
IDENTITY control against the identity allowlist: every author and committer address
and every author and committer name reachable from the scanned SHA is on the identity
allowlist. That half is `tools/flip_checks.py`'s identity axis, check `I`, counted in
the run's automated tally beside the seven checks and the trailer axis so a skip is
visible; it derives the allowlist at run time and prints counts only. **S8 scans exactly S7a's recorded output tip, and first asserts that
`main` still equals it** - a commit between S7a and S8 fails that assertion and
falls under the late-commit rule above. **S8 records the one `main` SHA it scanned;
S8a adjudicates exactly that SHA.** If `main` is not at that SHA when S8a freezes
it, the late-commit rule applies.

**S8a - READINESS ADJUDICATION, ANCHORED.** After S8 passes and before S9, an
in-session adjudicator that produced none of the flip's work freezes `main` at the
SHA S8 recorded - the same SHA, no other - and rules on readiness at that SHA, on
evidence re-run that session against all eight CS-G03 preconditions - the decide
half in `docs/GATED.md` CS-G03 (CS-1182).
**The adjudicated SHA is the SHA S9 onward operates on:** S10 pushes exactly it,
S11's mirror clone must return exactly it as the one head, and S12 publishes it.
Any commit to `main` after it falls under S7a's late-commit rule: S7a through S8a
are void and restart from the preservation bundle. **The ruling is recorded
OUTSIDE the adjudicated history:** it is written to a companion note beside the
preservation bundle, outside the repository tree per S5, and enters
`docs/LEDGER.md` only in a commit made after S12 completes. No commit records it
before then, so recording the ruling never moves `main` and never voids itself.

**TIP CHECK, immediately before EACH of S9, S10, S11 and S12.** Assert that the local
`main` tip equals the adjudicated SHA. From S11 on, also assert the remote side from
what ARRIVED, not from the advertisement: before S11 its own mirror clone does it,
and before S12 a fresh mirror clone of the recreated remote must return exactly one
head, at the adjudicated SHA. Before S10 the recreated remote must hold no ref at
all. A failed tip check HALTS the run at that step: a commit after S8a aborts before
S9 deletes anything, and a commit after S10 is caught before S12 publishes.

**BEFORE S12, THE WHOLE REF SET, filed 2026-09-25 by CS-1190.** The fresh mirror
clone the tip check takes before S12 runs S11's enumeration in full, every
namespace, not the head count alone. On the same pass: S9c's two families still read
private, S10b's rulesets read back as S10b left them, S7q part 1's control and S7q
part 2 pass. A failure halts before the flip with nothing published, and the halt
state is selected by the measured-state paragraph after S12a. This check narrows the
window to the flip itself; S10b is what closes it, within the limit S10b states,
and S12a is what measures it closed.

**ONE CONFIRMATION, ONE RUN, ONE SHA - and what a halt leaves behind.** The
operator's own-words confirmation covers S9 through S12 as one continuous run on the
one adjudicated SHA. Any halt - a failed control, a failed tip check, a session end -
spends it; it is never reused, and continuing needs a NEW own-words confirmation.
The remote's state at each halt point, so a halt is never a stall with no way on:

- Halt before S9: nothing outward has happened; the old remote is intact.
- Halt after S9, before S10: the old remote is GONE - the S3/S4 bundle is the only
  copy of its refs - and the recreated remote is private and empty.
- Halt after S10, before S12: the recreated remote is private and holds `main` at
  the adjudicated SHA, and nothing has been published, because S12 is the only
  publication event.

To continue after S9 has run: if `main` moved, apply S7a's late-commit rule first,
which yields a new adjudicated SHA. Then take a new confirmation covering the run
from the resume point to S12 on that one SHA. If the adjudicated SHA is unchanged,
resume at the step that halted. If it changed and S10 had already pushed, resume at
S9: delete and recreate the still-private remote, which holds nothing published, so
S10 again pushes one SHA to an empty remote.

**The halt states are owned by S9's sub-steps, S10b and S12a, filed 2026-09-25 by
CS-1190;** the three bullets above are now pointers, and the first one is
CORRECTED here: "nothing outward has happened" is FALSE once S7q part 3 has archived
the old remote, which is an outward act - reversible, and not one the own-words
confirmation covers, but outward. "Halt before S9" is S9a's OLD-REMOTE halt, which
S9a defines directly. "Halt after S9, before S10" is S9c's pass. "Halt after S10,
before S12" is S10b's halt or S10b's pass. "Resume at S9" above means S9a against
the recreated repository, under S9a's recreated-repository precondition.

**S9 - Delete the remote repository and RECREATE IT PRIVATE.** The first
irreversible step, and **it requires the operator's explicit go-ahead at the
moment of running, not this plan's existence.** The recreated repository is
created PRIVATE and explicitly asserted private before S10, so that S12 stays
the sole publication event; a repo created public would make S10 the publication
and strand S11's protections. Immediately before S9, re-confirm (1d) with its
controls - delete-and-recreate is only free while it holds. The tip check above
runs first.
Who decides and who confirms: `docs/GATED.md` CS-G03, "who decides the flip and who performs it" (CS-1182).

**S9's SUB-STEPS, filed 2026-09-25 by CS-1190.** S9 is three acts, and a halt can
fall between any two. Each sub-step below OWNS its halt state and its resume rule;
nothing else in this section restates them. Before S9a, record in the companion note
the `node_id` of the repository S9a is to delete, read in two families that must
agree - the REST repository read and the GraphQL `repository { id }` query. The id
tells the old remote from a recreated one when a halt leaves the name occupied; it
goes in the note, never in a tracked file.

- **S9a - DELETE.** The precondition is PER TARGET:
  - THE OLD REMOTE: the tip check, (1d) re-confirmed as S9 says, S7q part 1's
    control and S7q part 2, and the remote's ref set, read in S7q's two families,
    equal to the set S7q part 4 recorded. A difference is a push the archive did not
    refuse: S3, S4 and S7q part 4 re-run; if the set moves again between two reads,
    the archive is not refusing and the halt is TERMINAL, below.
  - A RECREATED REPOSITORY, on a resume: its `node_id` equals the one S9b recorded,
    S7q part 1's control and S7q part 2 pass, and (1d) is NOT re-run - S10b and
    S11 put rulesets and protection on it by design, so (1d) would refuse a correct
    state. Its current refs, read in S7q's two families, which must agree, are
    fetched into an EVIDENCE bundle beside the preservation bundle - nothing pushed
    is lost and the escape stays inspectable - and the precondition is that the
    evidence bundle's ref set equals that read, taken immediately before the
    delete. It is never compared with an earlier measurement, which an escape has
    by definition changed.

  Command: `gh repo delete` of exactly the repository whose recorded `node_id` the
  REST read still returns - never by name alone. Control: afterwards the REST read
  returns 404 and `git ls-remote` of the remote fails not-found; positive control,
  same pass and same two families, the same reads against a repository the same
  credentials can read and which exists, returning 200 and a ref list - so an
  expired token or a dead network cannot read as deleted.

  HALT AT S9a, OLD REMOTE: the old remote exists under its recorded `node_id`,
  private, archived by S7q part 3 unless the retry below unarchived it, and holding
  the ref set S7q part 4 recorded; the recreated repository does not exist and
  nothing is published. HALT AT S9a, RECREATED REPOSITORY: it exists under the
  `node_id` S9b recorded, private, and its refs are in the evidence bundle. Either
  way the target is INTACT. If the delete was REFUSED and the target reads
  `archived` true, unarchive it - reversible - read `archived` false back, re-run
  the old-remote precondition because unarchiving reopened it to pushers, and retry
  the delete ONCE. A SECOND REFUSAL, a refusal of an unarchived target, or a ref set
  that will not hold still is TERMINAL: the flip stops and hands to the operator
  with the recorded refusal, because a new confirmation cannot change a forge
  refusal and re-running S9a would loop. An unknown outcome resumes at S9a after the
  reads above settle which. A delete that TOOK leaves no repository under the name,
  which is S9b's halt state.
- **S9b - RECREATE, PRIVATE AND EMPTY.** Command: `gh repo create` with `--private`
  and none of `--public`, `--internal`, `--add-readme`, `--license`, `--gitignore`,
  `--description` or `--homepage` - an initialised repository holds a head before
  S10, and metadata is re-entered at S11 only once privacy is asserted. Record the
  new `node_id` as before; it must differ from the one S9a deleted. HALT AT S9b:
  the REST read returns 404, with S9a's positive control - NO repository holds the
  name, the old refs exist only in the S3/S4 bundle and the pre-S7a preservation
  bundle, and nothing is published. Resume at S9b; a second refused create is
  TERMINAL and hands to the operator on the same reasoning as S9a's. HALT AT S9b,
  UNRECORDED REPOSITORY: a repository holds the name though the create reported
  failure, so no `node_id` was recorded for it - it is private or public as S9c
  will measure, and unasserted. Resume by recording its `node_id` now, in the same
  two families, as S9b's own; then S9c, never S10.
- **S9c - ASSERT PRIVATE AND EMPTY.** Two families: the authenticated REST read
  returns `private` true and `visibility` private; and an ANONYMOUS read of the
  same endpoint, no credential sent, returns 404 - the outsider's view. Positive
  control for the anonymous family, same pass: the same anonymous request against
  a repository known to be public returns 200, so a blocked network cannot read as
  private. Then the before-S10 half of the tip check above: no ref at all. A pass
  is the state S10 starts from. HALT AT S9c, UNEXPECTED REF - THE ONE OWNER of a
  private recreated repository holding any ref the steps run so far did not leave
  there, found at S9c, at S10b, at S11 or at the check before S12: before S10 any
  ref at all, from S10 on anything beside the adjudicated head, INCLUDING a probe
  ref of S10b's that its own delete failed to remove. Nothing is published. Each
  such halt is recorded in the note as an ESCAPE. The FIRST escape: re-run S7q part
  1's control and part 2, and resume at S9a against THIS repository under S9a's
  recreated-repository precondition. A SECOND escape in one flip is TERMINAL and
  hands to the operator: the quiesce is not holding, and recreating the repository
  again would not make it hold. HALT AT S9c, NOT PROVEN PRIVATE: either family
  reads public, the two disagree, or a positive control failed. All three are the
  PUBLIC STATE below - uncertainty is not privacy.

**THE PUBLIC STATE IS A PUBLICATION EVENT, NOT A RESUMABLE HALT.** It is a
repository that came up world-readable BEFORE S12 was issued - never the public
repository S12 makes, which S12a owns. S9 exists so that S12 is the sole
publication, and a repository world-readable for an unmeasured window has already
broken that for itself: continuing would push the graph into it, and flipping it
private restores its visibility, not the guarantee. So: (1) S10 never runs against
it. (2) Measure what it exposed before touching it - a mirror clone into scratch,
enumerated as S11 does, and its metadata. Zero refs, as S9b's empty create
predicts, means the exposure was the repository's name and existence for the
window. ANY ref means history was published: it is scanned on S1's axes before
anything is deleted, because deletion destroys the evidence of what leaked.
(3) Record the event and its window, creation to deletion, in the companion note,
and in `docs/LEDGER.md` in the first commit made after the flip completes or is
abandoned. (4) Take a NEW own-words confirmation that names this state, then S9a
against this repository under its recreated-repository precondition, then S9b and
S9c again. A second PUBLIC STATE is TERMINAL and hands to the operator: the create
path is not doing what S9b says it does.

**S10 - Push `main` alone, BY SHA.** No `--mirror`, no `--all`, no `--tags`. Push
the S8a-adjudicated SHA itself - `git push origin <adjudicated-sha>:refs/heads/main`,
never a branch name - after a pre-push assertion that the local `main` tip equals
that SHA. If it does not, the late-commit rule in S7a applies and nothing is pushed,
so no later commit can ride along. The tip check above runs first. Exactly one ref is
pushed, `refs/heads/main`, and nothing else - no tag, no other head, no `refs/wip`. The
rewrite's commit map and every bundle stay outside the tree per S5.

**S10b - CLOSE THE RECREATED REMOTE TO EVERY PUSH, filed 2026-09-25 by CS-1190.**
Immediately after S10's push lands and before S11. It comes AFTER S10, never before,
because every pusher authenticates as the one collaborator account: the forge cannot
tell S10's push from an unseen clone's, so a rule with a bypass for S10 bypasses
them too, and the only enforceable rule is no push at all. Command: two repository
rulesets through the REST rulesets endpoint, enforcement active, NO bypass actors -
one targeting branches and one targeting tags, each including every name, each
carrying the creation, update, deletion and non-fast-forward rules.

WHAT IT MEASURES, AND ITS LIMIT. A ruleset targets branches and tags ONLY. No rule
covers any other namespace, and the old remote's `refs/wip` refs prove the forge
accepts pushes there. So the window from here to S12a is CLOSED for `refs/heads` and
`refs/tags` and only MEASURED for every other namespace, and the probes below say
which the forge actually does. NOT MEASURED when filed: whether this account's plan
offers rulesets on a private repository.

Controls: (a) both rulesets read back through REST - enforcement active, bypass list
empty, every name included. (b) REFUSAL PROBES from the flip session, each pushing
the adjudicated SHA and each expected REFUSED with a message naming a repository
rule, never a transport or authentication error: the branch `cs700-probe`, the tag
`cs700-probe`, and the ref `refs/wip/cs700-probe`. The third probe's namespace is
chosen because the old remote's `refs/wip` refs prove the forge ACCEPTS pushes
there, so a refusal is the forge's answer and not a reservation. A forge-reserved
namespace such as `refs/pull` is NEVER the probe: the forge refuses it whatever
the rulesets say, so its refusal clears nothing. Even `refs/wip`'s refusal measures
that one namespace, not every name outside `refs/heads` and `refs/tags`; S12a's
enumeration still reads them all. POSITIVE CONTROL, SAME PASS, immediately before
AND immediately after the three probes: a no-op push of the adjudicated SHA to
`refs/heads/main`, which reaches the forge's receive side with the same credential
and updates nothing, returns exit 0 and reports the ref up to date - so a dead
network or an expired token cannot read as a refusal. NOT MEASURED when filed: that
the forge authenticates a no-op push; a no-op push that exits 0 without reaching it
would leave the probes UNMEASURED, so the run records the transport trace of the
control. (c) A mirror clone enumerated as S11 does returns exactly what S10 left:
no probe landed. A pass is the state S11 starts from.

HALT AT S10b: the recreated remote is private and holds `main` at the adjudicated
SHA, and its rulesets are absent, partial or not yet measured; nothing is published.
A probe ref that LANDED is deleted by the flip session and the deletion read back by
a mirror clone; one that will not go is a ref beside the adjudicated head, which S9c
owns as an UNEXPECTED REF - S10b does not. If the ruleset call was refused, or the
branch or tag probe LANDED, the window cannot be closed as written: that halt is
TERMINAL for this run, an in-session adjudicator rules on another block - the
candidate is archiving the recreated repository, whose interaction with S12's
visibility change is NOT MEASURED - and that block is measured before it is relied
on. If only the `refs/wip` probe landed, the limit above is real on this forge: the
note records it, and the flip continues past S10b only on an in-session
adjudicator's ruling recorded there, with S12a's enumeration as the only check on
that namespace class - after publication, not before. Every other S10b failure - a
ruleset read back wrong, a probe or control unanswered - resumes at S10b. The
rulesets are removed only inside S12a's pass sequence.

**S11 - Verify by MIRROR CLONE, not by `ls-remote`.** The tip check above runs
first, and the mirror clone's one head must be the adjudicated SHA. Brief section 2(a) says
check what actually ARRIVED, never what the forge advertises. `ls-remote` reads
the advertisement, and after S9 there is no 6-heads control left to check a
pattern against - so the first draft's read-back was trap (b) relocated, not
removed. Clone the recreated remote `--mirror` into scratch and enumerate what
came back: assert exactly one head, zero tags, zero wip, zero of every other
namespace. Then set branch protection on `main`, which the old remote never had,
turn on the security features that work while the repository is private, and re-enter by
hand the 20 topics, 10 labels, description and homepage that deletion discarded.
**NARROWED, filed 2026-10-11 by the session 137 ruling below:** at S11 that security feature is
Dependabot alerts alone. Private vulnerability reporting, secret scanning and push protection
read 404 and null while private, so they are S12a's act (iii), after the flip.
**THE PROTECTION SHAPE, filed 2026-10-04 by the CS-700 pre-S7a ruling:** deletion and
non-fast-forward are blocked on `main` only - no required reviews and no required
checks, so the lane's fast-forward pushes still land. The same row is in
`docs/public-readiness.md`. If the plan refuses branch protection on a private
repository, this sub-step moves to just after S12; that is a PROBE OWED BEFORE S9, not
measured here.
**PROBE RESULT, measured 2026-10-04 by read-only GET against the current private
remote:** protection available while private. The branch-protection read on `main`
returned HTTP 404 "Branch not protected", not the 403 "Upgrade to GitHub Pro or make
this repository public" a plan refusal returns; the rulesets read returned 200 with an
empty list. S11's protection sub-step stays at S11. The plan name itself was not
readable with the current token scope; the 404 shape is the evidence. Re-probe if the
account's plan changes before S9.

**S12 - Flip visibility. Last, and blocked by section 6.** The tip check above runs first.
Covered by the confirmation taken before S9: `docs/GATED.md` CS-G03 (CS-1182).

**S12a - ENUMERATE AGAIN AFTER THE FLIP, filed 2026-09-25 by CS-1190.** Immediately
BEFORE issuing S12's visibility call, the flip session records in the companion note
that it is issuing it, with the time. That record is what tells the public
repository S12 made from one that came up public at S9b; without it a halt after a
flip that TOOK would read as the PUBLIC STATE and the plan would delete its own
intended result. Immediately AFTER the call: S9c's anonymous read, same request and
same positive control, now returns 200; a fresh mirror clone runs S11's enumeration
in full; S10b's rulesets read back as S10b left them. A pass starts the CLOSING
SEQUENCE, four acts in order, each recorded in the note before it is issued:
(i) S10b's rulesets are removed and read back gone; (ii) the post-S12 ledger commit,
whose SHA and whose single parent - the adjudicated SHA - are recorded first, is
pushed to `main`; (iii) once (ii) is read back landed, private vulnerability reporting,
then secret scanning, then push protection are turned on through `gh api` with the
existing token, each read back - a refusal is recorded in the note and the sequence
carries on, and the step-e ask's conditional line (4) hands it to the operator;
(iv) S7q lifts. Act (iii) was added by the session 137 ruling below, which is why the
S7q lift, act (iii) before it, is act (iv). The EXPECTED HEAD is the adjudicated SHA until
act (ii) is recorded issued, and from then on either the adjudicated SHA or the
recorded ledger commit - both are legitimate until (ii) is read back landed.

HALT AT S12a, FLIP DID NOT TAKE: the anonymous read still returns 404 with its
positive control passing - the remote is private and unchanged, nothing is
published, and the resume is S12's tip check under a new confirmation. HALT AT
S12a, INSIDE THE CLOSING SEQUENCE: the repository is public, holds exactly the
expected head and nothing else, and the note shows which acts were issued. The
reads settle each issued act - rulesets present or gone, `main` at the adjudicated
SHA or at the recorded ledger commit, each of the three security settings read on or
off - and the resume is the FIRST act they do not show done; act (i), act (ii) and
act (iii) are each idempotent against those reads, so re-issuing one that took is
never needed, and act (iii) is safe to repeat: its read-back is each setting's own
read, and a refusal is recorded again and carried on. HALT AT S12a, STRAY REF: any ref beside
the expected head is PUBLISHED - including one that landed after act (i) removed
the rulesets. It is a POST-PUBLICATION EVENT, never a silent pass: record it and its
window in the note, fetch it into an evidence bundle, scan its reachable history on
S1's axes, and put the scan result in `docs/LEDGER.md` in the post-S12 commit. Its
removal is an in-session adjudicator's ruling - which, while the rulesets stand,
needs the deletion rule lifted for that one act - and the closing sequence does not
advance past the act it halted at until that ruling is made.

**S12a KEEPS A WINDOW /done's RECORDS, filed 2026-10-12 by CS-1323.** A /done inside the window,
step b to S12a, commits nothing and leaves its records on disk, and S12a resets the main tree, so
S12a obeys the KEEP RULE in `.claude/commands/done.md`, which owns it: before the reset, copy every
dirty path into a new folder named for the session number under the tree's gitignored data
directory; restore every copied path immediately after the reset; read them back byte for byte;
and send the folder to the Recycle Bin only after the closing commit is read back. A halted S12a
keeps the folder for a distinct adjudicator. A crash between the reset and the restore leaves that
folder as the only copy, so the next session looks for it first. OPEN residuals, filed with it:
after a recovery the records sit uncommitted across sessions; after an abandonment nothing says how
the window closes; and a re-run's S5 porcelain-empty check would fail on the carried records.

**RESUME FROM THE MEASURED STATE, NEVER THE REMEMBERED ONE, filed 2026-09-25 by
CS-1190.** Any resume from S9 on first measures: the REST read and its `node_id`,
S9c's two families, a mirror clone enumerated as S11 does, the rulesets read back,
and the note's S12 issuing record. The facts select exactly one owned state, and
the resume is that state's own rule; this paragraph restates none of them:

- the old remote's recorded `node_id` reads back - S9a's OLD-REMOTE halt;
- no repository holds the name - S9b's halt;
- a repository whose `node_id` the note does not record - S9b's UNRECORDED
  REPOSITORY halt;
- the recreated `node_id`, S12 not issued, not proven private - the PUBLIC STATE;
- the recreated `node_id`, S12 issued, S7q's lift recorded done - the flip is
  complete and there is nothing to resume;
- the recreated `node_id`, S12 issued, anything else - S12a, whose four outcomes -
  pass, FLIP DID NOT TAKE, INSIDE THE CLOSING SEQUENCE, STRAY REF - its reads
  select;
- the recreated `node_id`, S12 not issued, private, holding any ref the steps run
  so far did not leave - S9c's UNEXPECTED REF halt, the one owner of that state;
- the recreated `node_id`, S12 not issued, private, no ref - S9c's pass;
- the recreated `node_id`, S12 not issued, private, exactly the adjudicated head,
  rulesets not as S10b left them - S10b's halt;
- the recreated `node_id`, S12 not issued, private, exactly the adjudicated head,
  rulesets as S10b left them, and the note
  recording S10b's controls passed or the adjudicator's ruling on its limit -
  S10b's pass.

Facts matching no row, or more than one, are a TERMINAL halt handed to the operator.
Every resume still needs the new own-words confirmation the halt rule above
requires, and if `main` moved the late-commit rule applies first.

#### 4. What deletion costs, stated so it is chosen and not discovered

LOST: 65 refs and their objects, 233 run records and logs, 17 artifacts, 11
caches, topics, labels, description, homepage, all traffic history, and the repo
`node_id`. PRESERVED by S3 and S4: every ref, in a verified restorable bundle.
NOT LOST, because it does not exist: issues, PRs, releases, packages, wiki
content, stars, forks, LFS objects.

#### 5. CS-952 is sequenced BEFORE the flip and is a hard blocker

**Gate item 7 - a clean-checkout probe on a machine that has never seen the
project - FAILS TODAY.** The entire `SessionStart` wiring lives in
`.claude/settings.local.json`, gitignored at `.gitignore:150`, so a fresh clone
runs no watcher - while this project published its fires-at-session-start
property to the channel as YES.

**Measured this session, and it narrows the repair:** `.claude/settings.json` IS
tracked and IS on the CLAUDE.md section 6 frozen list. So "track the wiring"
means editing a frozen file, and **that needs the section 6 grant, routed through
an adjudicator and recorded in `docs/LEDGER.md` BEFORE the edit.** No session
grants itself the exception. The correction half - fixing the published claim -
needs no grant and goes first. The content to be promoted was inspected: 697
bytes, one absolute path and it is the project root, no home path and no account
name, so the payload is benign; the frozen-file route is still mandatory.

**CS-952 closes before S7.** A public repo whose clean-checkout probe fails is a
public repo advertising a property it does not have.

#### 6. THE OPERATOR DECISION ON COMMIT IDENTITY - filed 2026-09-08 (session 74)

**520 of 521 commits on `main` carry a real personal email address in both the
author and the committer field.** Measured at `c885879`. Publishing under a real
identity is the ordinary default for a public repository and may well be exactly
what the operator wants - **but it has never been decided on the record here, and
it is the one exposure no step in this plan removes.**

It is genuinely an operator call and not an agent's: the only remedy is rewriting
every commit's identity, which ADR 0018 currently forecloses for content and
which this section explicitly does NOT foreclose for identity.

**RULED 2026-09-08: REWRITE IDENTITY TO NOREPLY.** Author and committer are
rewritten across all 521 commits to the operator's GitHub noreply address,
keeping every message, tree, path and date - AMENDED 2026-09-24 by the ADR
0018 amendment: every message byte except the agent co-authorship trailer line
and the blank line before it, which S7a strips. ACCEPT-as-is and SQUASH-to-fresh-
history were both put and both declined. **Do not re-pitch either**, and do not
re-pitch publishing under the real identity as a simplification.

**This reopens the rewrite branch on the IDENTITY axis only.** It is not the
content rewrite ADR 0018 rejects, and it does not disturb measurement 1.

**The consequence that must be sequenced, not discovered: every SHA changes.**
So the S3/S4 bundle holds refs pointing at the OLD SHAs, and after S7a not one
of the 53 wip refs or 5 salvage tags matches anything in the rewritten graph.
That is acceptable only because those refs are being discarded from the remote
anyway - but it means **the bundle is the sole copy of the pre-rewrite graph**,
and S5's placement rule and S4's restorability gate are now load-bearing for
the whole project's history, not just for 53 stray refs. Take the bundle before
S7a, never after.

**Related and already filed: CS-701** records that the operator git author line
coincides with a 4-character world name on this machine, and that a
world-name-keyed PII scan will therefore trip on every commit. **That item and
this decision are the same surface and should be settled together.**

**RESIDUAL, ACCEPTED - filed 2026-10-04 by the CS-700 confirmation-oracle ruling.**
The S7a rewrite hides only the old author email. Name, trees, dates, timezones and
messages are preserved and no commit is signed, so any single old commit SHA cited
in a commit message or in tracked text lets someone holding a GUESSED old address
recompute the old graph from the root and confirm the guess offline. The address
itself is not disclosed; only a guess can be confirmed. Mitigation is impossible
without a message rewrite or a squash: messages are byte-pinned by the MESSAGE
control and ADR 0018, and a squash is fenced by the operator above. Scrubbing the
tracked SHAs or shortening them to 7-hex is ineffective - one surviving citation in
any message suffices, and a 7-hex prefix still confirms a recomputed graph.
Adjudicated ACCEPT; the OPERATOR then confirmed in their own words in the main
session on 2026-10-04: "the adjudicators finding is fine, im not worried about".
**Do not re-pitch** a SHA scrub, a 7-hex shortening, a message rewrite or a squash
for this residual. *Reversed by:* only the operator's own words that the old address
must be unconfirmable, which reopens ADR 0018 and this section. Record:
`docs/LEDGER.md`, 2026-10-04 CS-700 DECISION RECORD.

#### 7. What this plan does NOT discharge

**CS-953 is not discharged by this plan.** A filename is not content. ADR 0018
removes the NEED for a scrub rather than proving one correct.
**REPOINTED, filed 2026-10-11:** CS-953 then closed as MOOT, not satisfied - `docs/LEDGER.md`,
the 2026-10-11 CS-953 record, and the dated amendment at the foot of ADR 0018.

**CS-954 stays TIER 1 and outranks this item.** A push that can ship an ungraded
ref is a defect in the mechanism S10 depends on.

**The 53 wip refs are DISCARDED, not cleared.** Nothing here measures them; that
is deliberate, and it is sound only because S3 and S4 preserve them first.
Any one may be recovered from the bundle and pushed later, **only after it is
measured on all six axes in its own right**, one at a time and on the record.

### SHA citation gate across S7a - filed 2026-10-04 by adjudicated design (d)

**Problem.** `tools/sha_citation_gate.py` reddens on any admitted citation that is not a
published commit. S7a replays every commit of `main`, so every sha the tree cites stops
resolving at once and the gate would turn the whole tree red the moment S7a lands.

**Decision - design (d), a state-witnessed historical set.** A GENERATED tracked file,
`tools/sha_citation_historical.json`, lists every token in tracked text that names a
published commit at generation time - tokens only, never an old-to-new pair - plus one
witness pair: `c6f3687` and its S7a image, the pair the CS-704 IMAGE control above pins.
The gate reads its state from the tree. PRE (the old witness published, the image not):
every listed token must name a published commit, and the image's allowlist row behaves as
before. POST (the reverse): no listed token may name a published commit - a new commit
answering an old citation is a collision and fails - and a listed token that is absent or
unpublished is historical and passes; an allowlist row naming the image, or `389fe4a`
(the rehearsal tip, which the real rewrite reproduces as the image of `69d44c5`), is not
overreach there. Both or neither witness published: exit 2. A token NOT on the list is
judged exactly as before, so an old sha nobody listed stays red. "Published" is unchanged:
reachable from `HEAD`, `refs/remotes/origin/main` or a tag. `--emit-historical` regenerates
the set, PRE only; `--flip-readiness` exits 0 only in PRE with no published citation
outside the set and no stale listed token. The S7a BASELINE above runs both.

**The set is PINNED by the gate - repaired 2026-10-04 after an adversary REFUTED the
first cut.** Nothing protected the set's contents, so a token added by hand laundered a
citation of it in POST (F1), and a swapped witness pair read a PRE tree as POST and passed
(F2). The gate now carries the set's SHA-256 as a constant, `HISTORICAL_SHA256`, written
only by `--emit-historical` in the PRE state into the gate that judges the tree (it refuses,
exit 2, a tree whose `tools/sha_citation_gate.py` is not itself), and requires the set's
witness pair to equal its own `WITNESS`. Both are checked on every run in every state; a
mismatch FAILS naming the file. The set's bytes ride through S7a unchanged, so the pin
survives the rewrite. The residual is stated, not hidden: whoever edits the gate's pin
line by hand can still launder, and that edit is a reviewed change to the gate itself.

**Alternatives set aside.** A tracked old-to-new commit map: it publishes the pairing of
every rewritten commit, and the S5 rule keeps the map outside the tree. Re-pointing every
citation after S7a: a commit after S7a voids S7a through S8a under the late-commit rule,
and it rewrites the record. Exempting every unresolved sha once the flip is detected, or
retiring the gate: fail-open - an old sha nobody listed, or a typo, would pass silently.

**Why (d).** It carries no pairing, its state is witnessed by the tree rather than asserted
by a flag a stale checkout could carry, it fails closed in every state it cannot read, and
it keeps an unlisted old sha red. The set file is excluded from the gate's code sweep, and
every token in it is judged by the PRE and POST arms instead.

### Relocated 2026-10-20 (session 150): four spent flip-block subsections

The session 129 Q2 scope ruling, the session 131 Part 2 re-run and flip-block rulings, and the
session 137 security-settings ruling are in `docs/history_notes.md`, verbatim, under
`CS-700 - spent flip-block subsections`: the block they governed ran and its S12a acts read back.

### Filed 2026-10-09 from MAIN's 2026-10-08 22:46 ORDER, sections 3 and 4

The operator APPROVED the history rewrite and the force push on 2026-10-08 (MAIN session
16), relayed by MAIN 2246 section 4: the 18 Claude co-author trailers stay folded into S7a
(strip) and S8 (prove zero), with no separate GH-HYGIENE rewrite; `fleet_rewrite.py` may be
used inside S7a. Dependabot local-landing rule, binding from now: never merge a Dependabot
PR with the merge button or `gh pr merge`; apply it locally as an operator commit
(cherry-pick `--reset-author`) and push. README-AUDIT item 1 joins this block: after the
flip, read back private vulnerability reporting and the social preview, the upload riding
the single operator ask; README items 2-7 are CS-1292, before the flip.

### Filed 2026-10-15 by the session 142 /done: MAIN's PUBREPO ORDER is CS-1328

MAIN's 2026-10-15 19:25 PUBREPO ORDER adds pre-flip work to this block; its body, its rules and
its acceptance are the CS-1328 section of this leaf. Three of its additions bind this block's own
steps: (a) the HEAD path scrub lands BEFORE the S7a baseline while none is taken - so before step
b, because no commit lands from step b to S12a (the /done adjudicator's residual: before the new
step a); (c) the read-only settings dump runs at S3, or at any time before S9; (d) the
fleet.operatorIdent change runs after S8 proves identity zero and before S10, config only, no
commit. No commit for that ORDER lands inside the window.

### Filed 2026-10-20 by the session 150 merger: CS-1332 precedes the close

This session's adjudication kept CS-700 OPEN on check 6's two binary skips at T2. The fix,
CS-1332, is CLOSED, and the CS-G03 record is written (`docs/LEDGER.md`, 2026-10-20, under each
ID). The CS-1332 section, which owned the order of the close, is in `docs/history_notes.md`,
relocated on its close. Next action: the one step that order leaves - a fresh CS-700 closing
adjudicator. CS-700 stays OPEN until it rules.

### Acceptance

every item on that checklist passes, including the full-history secret scan, the PII scan across tracked files and commit messages, the third-party license audit, and the clean-checkout probe on a machine that has never seen the project

## CS-1032

### Acceptance

one end-to-end control renders a known panel in a real browser and is compared against the stand-in's verdict for the same payload, with the comparison recorded whichever way it falls, and the stand-in's DIVERGENCES from the browser are enumerated rather than assumed empty

### Full headline

`tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo, and every panel verdict in the project rests on it: all 37 arms added for the optimize and power panels, plus every existing panel arm, run under `drive()` against a stand-in that nothing compares to a real browser, so "the page renders X" is a claim about the stand-in and not about the page - this project has already recorded that the dashboard's self-signed HTTPS defeats automation browsers and that browser-pane resize, focus and default key scrolling are silently faked, which is why the gap is unclosed rather than merely unnoticed

## CS-1194

### Acceptance

`tools/drift_guard.py` withholds, in the text report and the `--json` payload, any
rendered path with a component equal to a value this machine resolves locally as
the player's - the account directory name, the world name, the Windows account
name or the player display name - whatever its shape, and fails closed to the
withheld form when that value cannot be resolved; the values come from local
resolution, never a typed list in a tracked file. An arm plants a non-numeric
player-named directory holding no withheld-class file and asserts it is withheld,
and a control asserts a repository-chosen name still renders.

### Full headline

drift_guard prints a non-numeric player-named directory that holds no sensitive file

### FILED 2026-09-25, the ADR 0023 residual (session 113)

`docs/adr/0023-whether-a-filename-is-personal-data.md` rules this outside CS-1158: a
directory named for the player by a non-numeric name - a world name, a hex or GUID
account token - holding no withheld-class file is indistinguishable by shape from
any other directory, and renders. Rule 2's shape test catches only the digit-run
account id.

## CS-1196

### Acceptance

the history walk in `tests/test_provenance_manifest.py` (the CS-1176 arms) handles
a merge commit by a stated rule - first-parent, or an explicit rule for a row first
added on a side branch - and counts each first-add exactly once whichever way a slice
reaches `main`; an arm builds a real merge commit in `tmp_path`, with a side branch
adding a row, and asserts the walk counts the same first-adds as the equivalent
linear history.

### Full headline

the provenance manifest's history walk miscounts first-adds across a merge commit:
in the CS-1176 walk, a slice merged by `git merge` reads 14 first-adds where its
linear equivalent reads 13

### FILED 2026-09-25, found at the wave-3 close (session 113)

Found by the merger at the wave-3 close and reported with the counts above; the
filer did not re-measure them. Every slice this session reached `main` by
cherry-pick or fast-forward, so the walk has only ever graded linear history, and
no arm builds a merge commit.

### MEASURED 2026-10-02, the counts the filer never took (session 118)

This item blocked a push. Two slices were landed with `git merge --no-ff` rather than
by cherry-pick or fast-forward, and
`test_no_first_add_row_postdates_the_seed` went red on its ANTI-VACUITY equality, not on
a finding: `findings` was empty and `first_adds` was 441, while `versions` read 21 against
an independent count of 19.

THE COUNT RISES BY EXACTLY ONE PER MERGE COMMIT, measured at every commit of the session
with both counters re-implemented outside the module: 19 and 19 at the base and through
three linear commits, 20 against 19 from the first merge onward, 21 against 19 from the
second. The independent counter never moved.

THE MECHANISM IS TWO WALKS WITH DIFFERENT MERGE SEMANTICS, which is narrower than this
item's headline and is the part an arm has to pin. `_manifest_history` uses
`git log --full-history --parents`, and a path limit with `--parents` turns on parent
rewriting, which KEEPS a merge. `_independent_version_count` uses
`git rev-list --full-history` with no `--parents`, so there is no parent rewriting and a
merge TREESAME to a parent is OMITTED. A merge that does not itself modify the manifest is
therefore counted by one walk and not the other.

WHY THE 73 MERGES ALREADY IN THIS HISTORY DO NOT TRIP IT: they predate the manifest, so
their trees hold no copy of it, and the walk's own pruning step drops a node that has
neither rows nor a kept parent. The defect needs a merge whose tree HOLDS the manifest and
does not modify it - which is what landing a slice by merge produces, and what
cherry-pick and fast-forward never produce.

LANDED LINEAR INSTEAD, and the item stays open. The session's two merges were rebased away,
leaving seven commits whose combined tree is byte-identical to the merge-bearing one, and
the module then read 67 passed. That restores the practice the paragraph above records
rather than inventing a new one, and it fixes nothing: the next merge reproduces this.

## CS-1197

### Acceptance

the library sweep in `tests/save/test_trailing_run.py` (`_sweep_trailing_runs`) is
bounded by a stated rule - a sample, or a per-save cap - written in the module, and
its library arms finish under a stated seconds budget recorded beside that rule,
serially and under parallel workers, while still grading every save SHAPE the arms
name; an arm proves the bound holds as the library grows, and a control proves a
shape absent from the sample still reddens.

### Full headline

`tests/save/test_trailing_run.py` sweeps every real save, so its run time grows
with the save library: at the wave-3 close one test took 398s of a 400s per-test
cap, and it times out under parallel workers

### FILED 2026-09-25, found at the wave-3 close (session 113)

Found by the merger at the wave-3 close and reported with the timing above; the
filer did not re-measure it. The save library grows while the operator plays, so an
unbounded sweep drifts toward any per-test cap without a line of code changing.

## CS-1202

### Acceptance

it is MEASURED, in a live Claude Code session in this repository, whether the harness
sets `CLAUDE_FILE_PATHS` for the PostToolUse hook; if it does not, the hook command in
`.claude/settings.json` stops passing it (a frozen-file grant) and
`tools/edit_lint_check.py` reads the edited path from the stdin envelope alone, with an
arm proving an edited file with a violation is reported.

### Full headline

the PostToolUse lint hook's `--files "$CLAUDE_FILE_PATHS"` argument may always be empty
under the live harness

### FILED 2026-09-25, reported by the CS-815 shell adversary (session 115)

UNVERIFIED BY THE MERGER. The adversary read the harness binary and found no mention of
`CLAUDE_FILE_PATHS`, and counted 352 past PostToolUse hook errors in which
`edit_lint_check` reported `precommit_gate: BLOCKED`, mostly "could not read" the
file, cause not established. Predates CS-815 and is outside its grant.

## CS-1204

### Acceptance

`/api/health` answers without waiting on a save parse: its `world` field is derived
from what the world provider already holds or from a cheap presence check, never from
a fresh parse on the request path, so a cold first probe on a real world answers inside
the companion's `PROBE_TIMEOUT_MS`; an arm drives health with a world provider whose
load blocks and shows health still answering promptly.

### Full headline

`/api/health` still waits on a full save parse on a cold start

### FILED 2026-09-25, the CS-1203 closing adjudicator's residual (session 115)

After CS-1203 the first `world()` call on the pinned development world still takes about
2.58s, so the companion's first probe always aborts; the launch succeeds only because
the parse continues after the abort and the second probe finds it. Also recorded: the
import-time `ROUTES` table in `clockspeed/surface/api/routes.py` builds its own
`SaveWorldProvider`, which the launch path never serves.

## CS-1205

### Acceptance

the pre-push hook's pytest run is not reshaped by an inherited `PYTEST_ADDOPTS` (or the
hook refuses one it did not set), so an operator setting such as `-l` cannot make a
failing test render its locals through the hook; an arm plants `PYTEST_ADDOPTS=-l` and a
synthetic canary in a failing test's locals and shows no canary in the hook's output.
Needs its own frozen-file grant for `.githooks/pre-push`.

### Full headline

pre-push does not scrub `PYTEST_ADDOPTS`, so an operator `-l` renders test locals

### FILED 2026-09-25, the CS-814 repair adjudicator's ruling (session 115)

Found by the CS-814 vacuity adversary: the probe's pre-push sandbox stripped `PYTEST_*`,
so an inherited `PYTEST_ADDOPTS` was never exercised, and the hook does not scrub it.
Ruled a new item rather than CS-814 scope, because it is reachable only through the
operator's own environment and its fix edits the frozen pre-push file.

## CS-1206

### Acceptance

no module in the tests tree renders an environment value through a channel other than
an assert - a `print`, a `sys.stdout`/`sys.stderr` write, a logging call, captured
output echoed back, or a failure message built outside an assert - graded by a static
guard over the tests tree in the shape of the CS-1199 assert-rendering guard, with a
planted-mutant control per channel; the pre-push hook runs the whole tree, so its
output is a hook echo path under CLAUDE.md non-negotiable 13.

### Full headline

a test run by pre-push can print an environment value outside any assert

### FILED 2026-09-25, the CS-814 closing-bar adjudicator's ruling (session 115)

CS-814's static scope covers the programs the hooks run, but not the test modules
pre-push runs; the CS-1199 guard covers asserts only and the conftest redaction covers
known credential names only. Ruled a new item rather than CS-814 scope.

## CS-1207

### Acceptance

the READS rule in `tests/test_hook_env_echo.py` becomes an allowlist of the functions
permitted to touch the environment or OS-derived personal values, so an unlisted reader
is a finding: at least `os.path.expandvars`, `getpass`, `os.getlogin`, `Path.home` and
`expanduser`, `platform.node`, `socket.gethostname`, `tempfile.gettempdir` and
`os.environb`; keys passed to a reader across modules or through `map` or `partial` are
resolved; the command and dynamic rules catch PowerShell `Env:`, `node -e process.env`
and `capture_locals`; a driven arm reaches the short-name branch of
`precommit_gate.current_account_names`; the module docstring states what it grades.

### Full headline

the hook environment allowlist lists known readers, so an unlisted reader such as
`os.path.expandvars` escapes it

### FILED 2026-09-25, a condition of the CS-814 close (session 115)

The final CS-814 adversary rendered a synthetic personal marker through the real gate
with an `os.path.expandvars` skip message while every arm stayed green; no shipped hook
path uses any listed reader today, so CS-814 closed and this item carries the gap.


### MEASURED 2026-09-26, three adversary rounds against the landed inversion (session 116)

The inversion landed at `db87fff` and is NOT closed. Rounds one and two refuted it with
20 and 11 live escapes; both classes are closed and pinned by arms. Round three, at the
landed tree, rendered a synthetic marker live with no static finding through: attribute
walks inside `str.format` and `format_map` fields (`{0.__globals__[os].environ[K]}`);
`__import__` and `exec` bound to a name, stored in a container or passed to `map`;
`match` class patterns reading `__globals__` or a `home` attribute; `getattr` on
`pathlib.Path` with a literal `home`; reaching `os` through a scanned repository module
(`precommit_gate.os`); and `git difftool -x`, with `grep -O`, `rebase --exec`,
`clone -u` and `bisect run` passing statically. Probes and outputs sit in session 116's
scratchpad as `adv1207c_*`; the next builder re-derives them from this list.
DECLARED out of scope in the module docstring: `__file__` and `__spec__.origin`,
directory listings, `relpath` depth, `time.tzname`, `/proc` paths built at run time,
`git config user.email`, `git var`, personal `git log --format` fields, a python child
reading its program from stdin, `contextlib.chdir`, argparse `prog`, the gate's
`git(args)` pass-through, and `sys.argv`.

### MEASURED 2026-09-26, rounds four to sixteen on an unmerged branch (session 117)

Twelve repair rounds sit on branch `worktree-agent-ace624231ac7fd814` at its round-15 tip,
each recorded in that branch's copy of this section. Every adversary round refuted the
candidate with a new class; the saved probes of every earlier round stayed caught.
Round sixteen's open escape: pytest's config discovery reads a `pytest.ini` inside the `tests/` directory and a
root `.pytest.ini`, and neither is pinned or graded. The loop is HALTED, not closed: a
safety classifier stopped two adversary turns and the round-seventeen repair brief, and
the operator's ruling is owed on running round seventeen interactively, on declaring
pytest config discovery out of scope, and on landing the branch LANDED-NOT-CLOSED with
the module moved out of the guard shard.
## CS-1208

### Acceptance

a value-flow arm over every Python program the hooks run shows that no personal value a
program may read - including `CLOCKSPEED_ACCOUNT_DIR`, `CLOCKSPEED_WORLD_NAMES` and
`CLOCKSPEED_SAVE_ROOT` - reaches a print, log, report or exception sink, and that nothing
is echoed from inside a site the allowlist permits to read, with a planted-mutant
control per sink.

### Full headline

a personal value the hook allowlist lets a program read can still reach a print, log or
report

### FILED 2026-09-25, a condition of the CS-814 close (session 115)

The final CS-814 adversary printed allowlisted personal values and echoed from inside a
permitted site while every arm stayed green. The allowlist grades reads, never where a
read value goes.

## CS-1211

### Acceptance

`tests/test_hook_probe_bound.py::hangs`, the import-time precondition behind
`INSPECT_HANGS` and `NUL_STDIN_HANGS`, cannot read a slow-but-returning interpreter as
hung: under the load that reproduced CS-1201 (24 CPU spinners plus 32 process-spawning
threads) a POSIX box whose interpreter returns still skips the arms with their measured
reasons, shown red first on the current code with an injected slow-returning shim.

### Full headline

`tests/test_hook_probe_bound.py::hangs` reads a slow-but-returning interpreter as hung
under load, un-skipping an arm that then fails

### FILED 2026-09-26, the CS-1201 planner's residual C1 (session 116)

`hangs` waits `PRECONDITION_WAIT` (5s) and calls anything slower a hang. Not observed;
outside CS-1201's acceptance, filed as its spec directed rather than folded in.

## CS-1212

### Acceptance

the commit in `tests/test_hook_toolchain.py` that runs under `run_bounded` with
`harness_bound() + HARNESS_SLACK` no longer charges pre-hang start-up to that kill:
under the CS-1201 load it does not go red while green alone, using the CS-1201 call log
and hang-anchored window rather than a wider slack, shown red first with the 4s-per-call
shim.

### Full headline

`tests/test_hook_toolchain.py` kills its commit at a fixed bound plus slack that counts
pre-hang start-up under load, the CS-1201 defect one module over

### FILED 2026-09-26, the CS-1201 adversary's residual (session 116)

The CS-1201 adversary named the fixed kill in the module that imports
`tests/test_hook_probe_bound.py`; it was outside the item's write-list.

## CS-1213

### Acceptance

the save shard's named-first arm in `tests/test_tier1_budget.py` (the one asserting
`REBALANCED_FILE` is the save shard's FIRST target so loadfile starts it at once) grades
a claim that holds under the installed scheduler: either the save job carries
`--no-loadscope-reorder` as the hook job does since CS-1198, with the arm asserting both
the order and the flag, or the arm and its docstring are rewritten to state the measured
dispatch order; the save shard's next CI reading does not rise as a result.

### Full headline

the save shard's named-first arm in `tests/test_tier1_budget.py` asserts a dispatch order
that pytest-xdist 3.8 reorders away

### FILED 2026-09-26, the CS-1198 re-ruling's second finding (session 116)

pytest-xdist 3.8 sorts loadfile work by descending test count unless
`--no-loadscope-reorder` is given, so naming a file first no longer starts it first. S0
measured the same false claim at the hook shard's comment, repaired there by CS-1198.

## CS-1215

### Acceptance

no output of `tools/precommit_gate.py` - its `GitError` crash line, its handled INDEX
diagnostic reason, or any other rendering of a git child's stderr - carries a path
segment that locates a home directory or an account name, shown by arms that run the
gate by hand against a synthetic home path containing a space (git's dubious-ownership
refusal, a `GIT_DIR` naming a missing directory, a corrupt staged blob in a linked
worktree) and assert no marker fragment appears, each red first; the edit to the frozen
gate carries an adjudicator grant recorded in `docs/LEDGER.md` before it is made; the
`display_note` space-split (not reproduced end to end) is pinned by a direct-call arm.

### Full headline

the pre-commit gate run by hand echoes git's own stderr, home path included, through
its GitError crash line

### FILED 2026-09-26, the CS-1208 planner's lead H2, reproduced (session 116)

Reproduced with synthetic markers only, running `--staged` without `--verbose`: each of
the three triggers above rendered the marker. A real `git commit` failed before the hook
ran in the ownership and corrupt-blob cases, so the leak is reached when the gate is run
by hand or from another tool, not through the hook. Lead H1 (`display_note` splitting
on spaces under `--verbose`) reproduced only as a direct call.

## CS-1217

### Acceptance

a staged top-level `ruff.py` never runs when the pre-commit gate lints a staged unit:
with `ruff` absent from PATH the gate's `python -m ruff` fallback no longer starts in a
directory holding staged bytes, or runs with `-P` / `-I` (safe path) so the working
directory is not on `sys.path`, or refuses the fallback outright; an arm stages a
synthetic `ruff.py` that only writes a marker FILE into a temp directory, hides ruff
from PATH for the child alone, runs the gate under `--staged`, and asserts the marker
file is absent, red first; the edit to the frozen gate carries an adjudicator grant
recorded in `docs/LEDGER.md` before it is made.

### Full headline

with ruff off PATH the gate runs `python -m ruff` from the staging directory, so a
staged `ruff.py` runs in ruff's place

### FILED 2026-09-26, the CS-1207 round-7 builder's residual, reproduced (session 117)

`ruff_command()` falls back to `[sys.executable, "-m", "ruff"]`; `-m` puts the working
directory first on `sys.path`, and the ruff calls run with the staging temp directory
as `cwd`. A liveness adversary reproduced it end to end in a private tree: with ruff
hidden from PATH but importable, a staged synthetic `ruff.py` ran under `--staged` and
wrote its marker file. Declared as a residual in the CS-1207 scanner docstring.

## CS-1218

### Acceptance

the pre-commit gate never reports PASS for a staged Python unit whose lint did not run:
when ruff exits on a configuration it cannot load, or returns output the gate cannot
parse as its JSON report, the gate blocks with a finding that names the unit and says
lint did not run, shown by an arm that stages a synthetic unit under a temp repository
whose `pyproject.toml` carries an unloadable `[tool.ruff]` table and asserts a blocking
exit, red first; the edit to the frozen gate carries an adjudicator grant recorded in
`docs/LEDGER.md` before it is made.

### Full headline

a ruff config the gate cannot load makes the gate report PASS while lint did not run

### FILED 2026-09-27, a CS-1207 round-sixteen adversary side finding (session 117)

A private-tree commit whose `[tool.ruff]` table named an `extend` path ruff could not
resolve printed the gate's PASS line; the gate discards ruff's stderr, so the failure
was silent.

## CS-1231

### Acceptance

`ops/fleet_kit/` holds MAIN's current FLEET-KIT files byte-for-byte with a CLEARED
`THIRD_PARTY.md` row each, the gate dated before the lift; `CLAUDE.md` embeds the common
block between its markers and `fleet_headless.conformance(repo_root) == []` runs in the
suite; every headless spawn in this tree goes through the kit's `spawn`, or the reply to
MAIN names each path left out and why; MAIN's directives are still verified by
`tools/main_provenance.py`, the kit's `verify_main` being weaker than section 6.1.

### Full headline

adopt MAIN's FLEET-KIT (vendor the kit, embed the common block in CLAUDE.md, route
every headless spawn through it)

### FILED 2026-10-03, from MAIN's verified orders 0955, 1014 and 1016

Two slices are built and parked on their branches, unmerged: the vendoring with its guard
exemptions, and the condensed `CLAUDE.md` with the block embedded. Both HOLD at the
`THIRD_PARTY.md` section 14 gate: an adjudicator ruled the licence must be read before the
lift (an operator instruction moves the decision, not the gate), and MAIN's commit
holding the kit carries no LICENSE, NOTICE or manifest and no licence paragraph in its
README. The adjudicator's fallback is to hold and ask MAIN for a licence. The `/done`
command change the v2 order asked for is this tree's own text and landed separately.
Gaps reported to MAIN: `verify_main` hashes MAIN's working tree only; `claude_exe`
resolves through `shutil.which`; `check_url` admits any loopback port where CS-1225 pins
one.

### MEASURED 2026-10-03, v4 landed with slices A and B

MAIN shipped FLEET-KIT v4 under Apache-2.0 with a NOTICE naming the holder by role. The
section 14 gate ran and CLEARED before the lift (`docs/LEDGER.md` under CS-1231), and
slices A and B landed as one commit at v4. The condensation was dropped: an adversary
found it had moved binding rules into a non-binding history file, so `CLAUDE.md` keeps
its full text, adds a precedence paragraph, and gives each Settled entry a Reversed-by
clause that only the operator's own words satisfy. OPEN: slice C - route
`ops/loop/inbox_responder.py` and `ops/loop/run_lane.ps1` through the kit's `spawn`
with `floors_in_hooks=True`, then send MAIN the v4 ANSWER.

### Recorded 2026-10-08 by the session 129 /done

FLEET-KIT v9 landed under CS-1272. As read in session 129 it adds the xhigh and max efforts
but still carries no command-line entry and not the "Refused" task-name wording, so slice C's
second half - routing `ops/loop/run_lane.ps1` through the kit - still waits on a MAIN kit that
carries them. The inbox responder half already starts through the kit's spawn, as the
`CLAUDE.md` precedence clause (c) states.

### Recorded 2026-10-08 by the session 132 /done

FLEET-KIT v10 landed under CS-1282. It adds a `spawn` command line and the kit's
`REFUSED_TASK` wording, which the inbox responder now publishes on a refused start, so the
wording half of the wait is discharged. Slice C's second half - routing
`ops/loop/run_lane.ps1` through the kit - is still BLOCKED: the v10 `spawn` command line
passes no extra flag through, so the lane's permission flag cannot ride it. MAIN was asked,
in this tree's ONE ANSWER to MAIN 0839, for a kit v11 pass-through or a ruling to call
`launch()` or `spawn(extra=...)` from Python. Until one arrives the lane runner keeps
starting `claude` directly under precedence clause (c), and sets the SUBAGENT-FIRST hook
off for its worker. CS-1283 (ORDER item 5's `emit()` ruling) rides with this slice.

### Recorded 2026-10-08 by CS-1287

FLEET-KIT v11 (MAIN 2026-10-08 18:40 ORDER, ruling R2) landed under CS-1287 and UNHOLDS
slice C: the kit's `spawn` command line now passes ONE enumerated flag through,
`--permission-mode MODE` (MODE in `PERMISSION_MODES`). The target lane start line is
`python ops/fleet_kit/fleet_headless.py spawn ... --permission-mode bypassPermissions`, in
place of the direct start with `--dangerously-skip-permissions`. CS-1287 did NOT move
`ops/loop/run_lane.ps1`, by ruling: the kit's command line prints its own usage line, not
the CLI's `type: result` object that `ops/loop/queue_loop.py` parses, and its proxy and
budget checks collide with the lane's own loopback check and budget, so the move needs its
own slice. Precedence clause (c) of `CLAUDE.md` stands until that slice lands.

### Recorded 2026-10-17 by the session 145 /done

Slice C is PARKED by adjudication on its own branch, NOT on main (tip subject "CS-1231 - lane
runner starts its worker through the kit"; KEEP the branch and its agent worktree). Three distinct
adversaries REFUTED it: the kit's `--timeout` fires before the driver's own timer, so a timed-out
run records completed (HIGH); a kit budget refusal ends the night through launch_failed (MEDIUM);
and lower findings, listed in `docs/LEDGER.md`, the 2026-10-17 CS-1231 record. The kit-side
findings K1 to K5 went to MAIN in the session 145 REVIEW note. Carried locally, L1 to L6: plumb the
driver's timeout into the runner, or map the kit's exit 4 to timeout_killed; a budget refusal onto
the usage-limit wait path (after K5); the case-variant JSON keys PowerShell 5.1 reads; `CLAUDE.md`
wording that cites the landing commit, never a kit version; at landing, the merger rewrites this
section's lines that say slice C is open and clause (c) stands; the timeout test's docstring, which
overclaims. Until it lands, `ops/loop/run_lane.ps1` starts `claude` directly and `CLAUDE.md`
precedence clause (c) is accurate. CS-1283 no longer rides with this slice: it closed in session 145
on its keep-own-sink ruling. Next action: unpark on a MAIN kit answering K1 and K5, or a ruling
that they are won't-fix; fix L1 to L6; land only after a distinct adversary reads NOT REFUTED on
the combined tip.

### Recorded 2026-10-17 from MAIN's verified 13:16 RULING, item 4

K1, K5 WON'T-FIX in the kit; slice C UNPARKS. L1: treat kit exit 4 or JSON error "timeout"
as timeout; pass `--timeout` above the driver's timer, or drop that timer. L2: a budget
refusal is exit 3, JSON code "budget-spent" - back off until `cap_frees_at` in
`inbox_status.json`. Next: fix L1 to L6, land on a distinct adversary's NOT REFUTED.
Reversed by a kit exit 0 or no error for a killed run, or a refusal not exit 3 budget-spent.

## CS-1234

### Acceptance

The CS inbox responder writes its gitignored inbox-status file atomically
in MAIN 0915's schema 1 on every state change and at least once per tick, including on
its halted path; task names come only from the basic set; `task_eta_s` is the median of
the last ten completed instances of a task, null under three; at most 120 headless runs
start per rolling 24 hours, counted under a lock, and an unreadable counter refuses every
start.

### Full headline

the inbox responder publishes its inbox-status file (MAIN 0915) and caps headless
starts at 120 per rolling 24 hours

### FILED 2026-10-03, from MAIN orders 0915 and 0855, operator-approved in session

RC's lane widget reads every tree's status file and showed CS as "Sync: no signal".

## CS-1291

### Acceptance

Each of MAIN 2246 section 2 items 1-3 and 5-10 is DONE or carries a recorded reason it is
not, in `docs/LEDGER.md`: (1) pre-push tiered by the pushed diff - a doc or hand-off-only
range runs gates only, a code range runs `-m "not slow"` plus the mapped modules, the pass
floor scales to the subset, the full suite stays with tier1 CI - landed on a section 6
adjudicator grant recorded in `docs/LEDGER.md` before the edit, because `.githooks/pre-push`
is frozen; (2) a preflight of about 10 s (provenance manifest, sphinx roles, mypy on
changed files, ruff) runs first in pre-push; (3) `--durations=25` locally, every test over
about 2 s and every subprocess hook test marked `slow`, `tests/test_tier1_budget.py` fails
on an unmarked slow test, its stale header numbers updated; (5) tier1.yml `paths-ignore`
for docs, markdown and the hand-off, one shared budget script in place of the five copies,
and tier2 skipped when HEAD equals the last green tier2 SHA; (6) inbox runs classify first
then sonnet/low, one fire per note per tick, a 0-second Stop writes failed; (7) the
0-ahead agent worktrees and the old slice worktree Recycle-Binned after a consumer check
and merged `worktree-agent-*` branches pruned; (8) verifiers read the frozen-SHA run's
junit and exit code rather than re-running the whole suite; (9) progress files get status
failed on agent exit and a schema check on write, done files older than 7 days archived;
(10) is CS-1284, discharged there.

### Filed 2026-10-09 from MAIN's 2026-10-08 22:46 ORDER, section 2

MAIN's read-only perf audit, ranked; the measured numbers are in the note and are not
restated here. Item 4 (no suite gate) is section 1's kit v13 work, CS-1290. Item 10 is
already open as CS-1284. The note says fix inline; each numbered part may land as its own
slice. The section 8 review driver (CS-1295) folds this list in as known findings.

### Recorded 2026-10-17 from MAIN's verified 13:16 RULING, item 3

Part (1) and DONE-SLOW (CS-1321) compose; DONE-SLOW governs where they touch: a /done runs
at most ONE gated whole suite, on the HEAD it pushes; pre-push runs no whole suite by
default; a doc-only ritual may run none. Grant timing after CS-700 S12a unchanged. Reversed
by TEST-TIER replacing the ritual suite, or /done median still over 65 min after 5 rituals.

## CS-1295

### Acceptance

Quoting the note: "plan file + a findings file covering every top-level folder, each
finding DONE / FILED (row id) / NOT-APPLICABLE, and a file count reviewed equal to the
count on disk." The driver is ONE headless run started through the kit spawn path only
(FLEET-COMMON 10; kind build, a non-empty note label) and writes the item-12 progress file
named repo-review.json, with a checklist. It plans first, then reviews
100 percent of the files on disk - tracked, untracked and ignored - over the topics MAIN
2246 section 8 lists, folding in sections 2, 3, 5 and 6 as known findings (CS-1291,
CS-1292, CS-1293). Fixes land in slices through the git lock and the suite gate; anything
irreversible or operator-gated is listed, not done. The run label and progress file name
go in this tree's next ANSWER to MAIN.

### Filed 2026-10-09 from MAIN's 2026-10-08 22:46 ORDER, section 8

Queued after section 1 (CS-1290) per the note's order of work. It needs a session that may
spawn headless runs: a sub-agent slice cannot start it, so the main session or the lane
queues it.

## CS-1304

### Acceptance

The forced run's exit 2 under load in the forced-red arms of
`tests/test_cs1172_branch_canaries.py` and `tests/test_cs1175_rule_narrowing.py` is traced
to its cause, read from the run's own `child_failure` report, and fixed there; both files
then run 30 consecutive times under `-n 2 --dist loadfile` with no forced or control child
exit 2. A child that dies of a Windows status past 255 (shown in hex) is a box-resource
death, recorded with its reading and not counted as this defect. No leaky control is
weakened, no budget is raised and no case is skipped.

### Filed 2026-10-09 by the CS-1301 merge

CS-1301's builder recorded in its second commit ("CS-1301 - the forced runs name their own
failure, statuses in hex") that its first 30x loop under `-n 2 --dist loadfile`, on a box at
its commit limit, read a control child exit 3221225773 (0xC000012D, the paging file too
small) and a forced run that "did not fail: exit 2". That forced-run message was still bare,
so its cause was not recorded; both forced-run code assertions now report through
`child_failure`, so the next reading names the child's error types and frames. CS-1301 traced
the leaky control's exit 2 to a cross-drive collection walk and cut it with `--confcutdir`;
the forced run's paths are in the repo, so that cut does not reach it, and whether it shares
the cause is unmeasured. An exit 2 there reddens any suite that runs the files, so it is
filed under the `CLAUDE.md` section 7 suite-red exception.

### Session 135 ruling, recorded 2026-10-10

Retry-once is DENIED as masking. The narrowed alternative A governs: `child_failure` names the
withheld exception type, the failure stays red, and the fix waits for a measured reading. The
item may wait past the CS-700 flip unless a deciding suite before CS-700 step a shows this
failure class - then it blocks the flip block. Decision, alternatives, the unmeasured planner
spec and the reversal: `docs/LEDGER.md`, the 2026-10-09 CS-1304 DECISION RECORD.

## CS-1307

### Acceptance

Every git-hook arm in `tests/test_hook_env_echo.py` that drives the CS-815 interpreter ladder
either waits at the quiet barrier the TIER2-RED repair gives that module's wrapper arms, or is
shown by a measured run beside a CPU-bound sibling not to need it; the file then runs 30
consecutive times under `-n 2 --dist loadfile` with no "did not finish inside its bound"
refusal, and the guard shard's duration is re-read after the change. No budget or bound is
raised and no case is skipped.

### Filed 2026-10-10 by the session 135 /done

The TIER2-RED repair (the unmerged branch whose commit "CS-815 CS-1300 - one quiet waiter at a
time, a bound from evidence" states the residual in its body) gave the env-echo WRAPPER arms
the barrier and left the git-hook arms of the same module running the same probe ladder under
the same bound without waiting: making them wait serialises most of that file behind every
sibling, a guard-shard duration risk. The session 135 leak and vacuity adversary named it. A
ladder that cannot finish inside its bound under sibling load is the TIER2-RED failure class,
which reddens a suite, so it is filed under the `CLAUDE.md` section 7 suite-red exception. It
may land with the TIER2-RED merge or after it.

### Verifier verdict recorded 2026-10-11 (session 137): REFUTED, the item stays open

The TIER2-RED slice's commit "CS-815 CS-1300 - one-shot check sees past a probe, waiters stop
first" states that this item is not in scope and is untouched. A session 137 verifier read the
acceptance against the landing branch:

- Clause 1 UNMET: 7 git-hook-driving arms in `tests/test_hook_env_echo.py` run without waiting
  at the quiet barrier -
  `tests/test_hook_env_echo.py::test_no_pre_commit_path_echoes_a_canary`,
  `::test_no_commit_msg_path_echoes_a_canary`, `::test_no_push_hook_path_echoes_a_canary`,
  `::test_a_pre_commit_copy_that_dumps_the_environment_is_caught`,
  `::test_no_account_name_skip_renders_the_name`,
  `::test_the_skip_arm_separates_a_carried_token_from_a_rendered_one` and
  `::test_a_gate_copy_whose_skip_renders_the_name_is_caught`. They run git commit or git push
  through `tests/test_hook_env_echo.py::commit_through` and
  `tests/test_hook_env_echo.py::push_through`, and the hooks run the ladder. The guard,
  `tests/test_claude_hook.py::test_every_env_echo_arm_that_drives_the_wrapper_runs_alone`, scans
  only the callers of `tests/test_hook_env_echo.py::run_wrapper`. No measurement of the git-hook
  arms exists.
- Clause 2 (the 30 runs) and clause 3 (the guard shard re-read) UNMET: there is no change to
  measure. Clauses 4 and 5 are MET only because nothing changed.

**Acceptance wording faults**, recorded beside the clause and not amending it:

- The "did not finish inside its bound" text is printed only by `tools/claude_hook.sh`. The git
  hooks time each probe step for 10 s and print "the interpreter probe did not answer within",
  which is also the expected output of the pre-commit-under-pythoninspect arm. Grade the 30 runs
  on failures, not on text.
- A single file under `--dist loadfile` runs on one worker, so the 30 runs never have a busy
  sibling. The measured-beside-a-sibling run is the only evidence of load.

**Smallest remaining slice**, in order:

1. Measure each of the 7 git-hook arms beside a CPU-bound sibling worker, as the liar-arm
   measurement did (`tests/test_claude_hook.py::test_a_liar_on_every_rung_is_loudly_reported`).
2. Arms that stay inside the bound go into a named load-tolerant set citing the measurement;
   arms that overrun move to the file foot with the `alone` fixture.
3. Widen the `tests/test_claude_hook.py` guard to also scan the callers of `commit_through` and
   `push_through`, failing any arm that neither waits nor sits in the set.
4. Run the file 30 times, graded on failures.
5. Re-read the guard shard duration from tier1.

### Recorded 2026-10-17 by the session 145 /done

Sibling-load measurement, 16-CPU Windows box. The seven git-hook arms (30 cases) ran under -n 2
--dist loadfile beside a scratch sibling test that spawned CPU-bound spinner processes for the whole
burn. Quiet: 30 passed, 45.7 s. 32 spinners: 30 passed, summed call time 1500.22 s, inside the burn.
6 spinners: 30 passed in 50.73 s; a pass-through timeout script first on PATH called the real GNU
timeout with the same arguments and exit status and logged each call's elapsed ms, exit code and
bound: across 221 bounded hook steps the longest that answered took 75 ms (80 ms quiet) against the
10 s bound; the only expiry was the PYTHONINSPECT arm's expected probe hang. Both files serial: 370
passed in 96.77 s before, 371 passed in 90.81 s after. tests/test_hook_env_echo.py 30 consecutive
runs under -n 2 --dist loadfile: 30/30 green, 51-59 s each; a single file has no busy sibling, so
these runs are graded on failures only.

STATE: steps 1 to 4 of the smallest remaining slice are DONE, landed in session 145 as the commit
"CS-1307 - git-hook arms load-tolerant; guard covers commit/push callers": the seven arms sit in
`ENV_ECHO_LOAD_TOLERANT_ARMS` in `tests/test_claude_hook.py`, citing this measurement through
`CS1307_MEASURED_ARMS`, and
`tests/test_claude_hook.py::test_every_env_echo_arm_that_drives_a_git_hook_waits_or_was_measured_tolerant`
fails any arm reaching `commit_through` or `push_through` that neither waits nor sits in the set.
Evidence before the change: at 9bf60fd no git-hook case exceeded 6.87 s in the guard shard. Next
action: clause 3 READ in session 146, the item STAYS OPEN - clauses 1 and 2 owe an independent
re-measurement after S12a. LOAD CONSTRAINT: the 32-spinner run saturated the machine and caused
the operator's session 144 CPU stop - any load harness runs at most 6 spinners, never beside
another suite. Residual: `BACKLOG.md`, "Session 145 residuals" (callers followed by bare name only).
Rulings: `docs/LEDGER.md`, "2026-10-17 - CS-1307 - NOT A COMPLETION RECORD: clause 3 read; item
STAYS OPEN - clauses 1 and 2 owe an independent re-measurement".

## CS-1318

### Acceptance

The cause of the hook-shard failure of the pre-commit case of
`tests/test_hook_probe_bound.py::test_a_background_child_holding_stdout_is_refused_and_reaped`
("the background process outlived the refusal - it was not reaped") is measured. Either the arm
reproduces, and the reaping defect is fixed with the arm red first; or repeated runs on the ubuntu
runner and on a loaded box show a load flake, and the arm's wait is made load-tolerant without
raising the hook probe bound. A rerun alone never turns the red green, and no case is skipped.

### Filed 2026-10-12 by the session 138 /done

tier1 38262274792 at c7fc806 - a commit touching only `CS-NEXT-SESSION.txt`, `WAKEUP_NOTES.md`,
`docs/LEDGER.md` and `docs/history_notes.md` - failed its hook shard, which runs on ubuntu-latest,
on that one arm: 1 failed, 686 passed, 10 skipped. The same shard passed at 0e82056, the parent,
and at 923e30f and 5b22e08. No record in the tree names this arm as flaky before, and the /done did
not rerun the job. CS-1211, the same module's `hangs` reading a slow interpreter as hung under load,
is FROZEN and is a sibling, not this arm.

### Filed 2026-10-12 by the session 139 merger

Live state: measured as a load flake in the arm's `reap` liveness check, not a reaping defect; the
classification evidence and the adversary's residuals are the CS-1318 record in `docs/LEDGER.md`,
2026-10-12. The repair is on main: `outlives_the_reap_wait` in `tests/test_hook_probe_bound.py` polls
for up to `REAP_WAIT` and reads a zombie as dead where the proc filesystem shows its state; the hook
probe bound is unchanged and no case is skipped.

Next action: the rework the 2026-10-15 CS-1318 reap-replay REFUTED record in `docs/LEDGER.md` names, after the CS-700 window; it does not gate CS-1317's acceptance (ruling R2).

## CS-1328

### Acceptance

Every done criterion of MAIN's 2026-10-15 PUBREPO ORDER holds: the settings checklist re-applied
and read back after S12a; fleet.operatorIdent noreply-only, and user.email the noreply value in
every checkout; the v0.1.0 tag's ancestor check passed and its release read back; the HEAD
absolute-path count 0 outside an explicit allowlist; the accepted history residual recorded in the
ledger. And the ORDER's ONE ANSWER is sent after S12a, in one note: the read-backs, the closing
ledger commit hash and the census axis counts.

### Filed 2026-10-15 by the session 142 /done, from MAIN's ORDER

Filed from the MAIN note "2026-10-15-1925-from-MAIN-ORDER-to-CS-PUBREPO-CS-700-pre-flip-additions-ONE-ANSWER.md"
(ORDER, HOP 1, one destination), sha256
c733c36d9016c3a326c5e9b3e3e921d66dd7fd92677d806535d2c174c9bd1b77 - equal to MAIN's tracked,
unmodified outbox copy, read by the session 142 /done, so under FLEET item 6 it is the operator's
instruction (the operator's 2026-10-15 order: CS-700 done correctly before its public flip is fully
realized). It rests on MAIN's 2026-10-15 PUBREPO posture ruling, item 3 (item 1 after the flip), in
MAIN's tree. The inbox is gitignored, so this section is the only tracked copy here. In tighter
form:

0. WINDOW RULE: no commit for this ORDER inside the S7a..S12 window; every addition is placed so it
   never voids S7a (the late-commit rule). Record the ORDER in the closing ledger commit after
   S12a, and answer AFTER S12a.
1. CORRECTED BLOCKER LIST: (i) CS-1317's remaining step-b condition, step a's own tier1 run; (ii)
   the gh token lacks the delete_repo scope (S9a); (iii) the operator's own-words confirmation
   covering S9-S12 as one run. CS-1327 is closed and is not a blocker. MAIN carries (ii) and (iii)
   to the operator as ONE batched ask.
2. ADDITIONS.
   a. HEAD path scrub (about 44 lines naming this tree's absolute install root in both drive
      spellings and the sidecars root): land it BEFORE the S7a baseline if that baseline is not
      yet taken; otherwise it is the FIRST commit after S12a. The history residual (47/36/35 added
      lines) is ACCEPTED: layout, not identity. Cleaning history is an ADR 0018 reopen, not an S7a
      extension.
   b. A census axis for drive-root project paths and foreign host names, NON-aborting, counts
      recorded. Inside the window it runs as an uncommitted out-of-tree measurement (like the S7a
      script); the tracked axis ships after S12a.
   c. A settings dump at S3 (or now, if S3 has passed; read-only, any time before S9): the branch
      protection rule body, vulnerability alerts, private vulnerability reporting, secret scanning
      and push protection, topics, description, homepage, merge flags, CodeQL default setup,
      Dependabot config. S11 and S12a re-apply each item and read it back; re-measure plan 1d at
      run time (it drifted).
   d. fleet.operatorIdent: after S8 proves identity zero and before S10, remove the personal email
      value (--unset-all, then re-add the noreply value only); assert user.email equals the
      noreply value in the main checkout and in every worktree; read back. Config only, no commit.
   e. v0.1.0: an annotated tag on the S8a-adjudicated tip, cut AFTER S12a and the S7q lift, never
      inside S10. Positive control: the tag commit is an ancestor of published main and is in
      S7a's new-SHA map. Push the single tag ref only (never --tags or --mirror); gh release
      create v0.1.0 --verify-tag with a hand-written notes body (generated notes OFF).
   f. No commit for this ORDER inside the window (rule 0).
   g. Post-flip, MAIN's fleet posture items apply here: 1a (hand-cut annotated milestone tags,
      semver 0.x, hand-written notes); 1b (Conventional Commits subjects, the item id may sit in
      the scope, merge subjects carry no agent worktree names - only AFTER auditing every subject
      grep in this tree); 1d (a README section "How this repo is built": CLAUDE.md, .claude/,
      ops/, .githooks and the hand-off as documented process, the licence stated plainly); 1g
      (CodeQL triage, HIGH first, fix or dismiss with a written reason; Dependabot alerts ON,
      security-update PRs OFF; an outsider read of tracked agent and hand-off text; a 30-day
      failed-run Actions log sweep, counts only). A hashed lockfile is DROPPED here (dependencies
      = [] by recorded decision).
   MAIN's rejected alternatives: a blob scrub folded into S7a (fenced by ADR 0018; it invalidates
   S7a's controls); the tag at S10 (it changes S10's one-SHA control); trusting plan 1d (it
   drifted). Reverse if: the operator's own words reopen ADR 0018 (a history path scrub).
3. DONE CRITERIA: the Acceptance above.
4. ONE ANSWER: one note, after S12a - the read-backs above, the closing ledger commit hash and the
   census axis counts. ANSWER classes are recorded, not answered.

THE /done's DISPOSITION, ruled by a distinct read-only adjudicator of session 142 (option A): file
the ORDER as this item; point CS-700's section and the hand-off's flip block at it; write no
LEDGER entry for the ORDER before S12a (rule 0); send no reply; acknowledge the note by its key
alone (the watcher's key-file acknowledgement, never the acknowledge-everything flag, which can
swallow a note that arrives mid-pass), so the unattended responder stops re-firing on it - it had
spawned a headless opus run on it on every tick, nine by 22:11, none acknowledging it. Rejected:
leaving it unread (about four opus runs an hour against the tree's shared 120-run cap); the
INBOX_STOP sentinel (it halts every inbox note, an autonomy change FLEET item 14 forbids); folding
it into CS-700 (CS-700 closes at S12a, while this ORDER's tag, read-backs and answer come after
it). Runner-up: the fold - the flip runner reads CS-700's text, so (c) and (d) could be missed; the
pointers in CS-700's section and the hand-off cover that. COMMON-MODE RISK: every option assumed
the window signal CLOSED (the adjudicator read HEAD 74d895d itself). RESIDUAL: addition (a) must
land before session 143's new step a, or it slides to after S12a; the hand-off is one of the files
it scrubs. Reversed by: step b landing before the /done commits (the window OPEN - commit
nothing), or a MAIN note withdrawing the ORDER. AS IT FELL OUT: the responder's own tenth run on
the note acknowledged it by its key alone at 22:27 (the watcher's invocation log), before the
/done's records commit; the /done's own key-only ack then found nothing unread and stored nothing.

SESSION 143: addition (a) is built and adversary-passed, landing in the session 143 push with
CS-1329, one tier1 reading (the ruling: `docs/LEDGER.md`, 2026-10-16, under CS-700, CS-1317 and
CS-1329). The explicit allowlist's owner is `KEPT_CHECKOUT_LINES` in `tests/test_readme_audit.py`.
OPEN STEP before CS-1328 closes: 16 lines on 4 files still spell the old C:-drive sidecar paths
(`docs/LEDGER.md` 4, `docs/history_notes.md` 5, `tests/test_queue_loop.py` and
`tests/ops/test_multi_lane.py` 7); scrub them or allowlist them explicitly, because (b) only
measures. The path detector `ABSOLUTE_CHECKOUT_RE` matches only paths ending in this tree's folder
name, so it does not catch a sidecar-root spelling; no tracked file now spells the sidecar root.

SESSION 145: the open sidecar step above is DONE - LANDED by adjudication as the commit "CS-1328 -
sidecar-path detector and allowlist; scrub six test literals" (`docs/LEDGER.md`, 2026-10-17,
CS-1328; session 144 rulings R2 and R3). The six `tests/test_queue_loop.py` literals are scrubbed to
a parent placeholder; the ten records and detector lines stay byte-unchanged on a content-digest
allowlist, `KEPT_SIDECAR_LINES` in `tests/test_readme_audit.py`, beside `KEPT_CHECKOUT_LINES`;
`tests/test_readme_audit.py::test_no_drive_rooted_sidecar_path_in_any_tracked_file` and
`tests/test_readme_audit.py::test_every_sidecar_allowlist_row_matches_a_live_line` pin it. The
detector also covers the current sidecars root, so a tracked line spelling it turns the suite red -
write <sidecars>. Its residual spellings: `BACKLOG.md`, "Session 145 residuals".

Next action: (c) at S3 and (d) between S8 and S10 inside the block; (b) as an uncommitted
measurement in the window; (e), (g), the ledger record and the ONE ANSWER after S12a.
