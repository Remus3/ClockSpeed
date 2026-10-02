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

## CS-953

### FILED 2026-09-07 (session 73), from a sibling's measured failure

RC ran a history rewrite with a rename table keyed on each file's path AS IT
EXISTS AT HEAD. The filter callback receives the path belonging to whichever
COMMIT it is filtering, so every file that had ever been MOVED went unrenamed at
each of its earlier paths. Result: 2195 vendor-name hits in the rewritten
history, **none of them in a blob** - all in tree objects, which is where
filenames live. A content scrub can be complete and still publish the names.

THE PREVIOUS PASS HAD VERIFIED "ALL PURGED PATHS ZERO" AND THAT WAS TRUE AND
USELESS. It checked eleven named path patterns and no vendor name was among
them. The check confirmed the absence of things already known to be absent.
Widening it also surfaced 27 scraped images and two scraped JSON files that
appeared in no plan - dropped rather than renamed, because renaming scraped
third-party data keeps the data and hides only whose it is.

**THIS BITES CS SPECIFICALLY** because CS-700's phase-7 gate is a going-public
checklist and this project is going public. Two further surfaces from the same
report: a mirror clone DOES fetch `refs/pull/*/head` (531 commits existed on no
other ref), and deleting a repository deletes its LFS store. The git object
store is not the whole surface.

### Acceptance

the phase-7 scrub verifies the whole path list against the whole name list rather than a list of paths already known to worry about, proven by a probe over a synthetic history containing a renamed file that goes RED when only HEAD paths are checked

### Full headline

a history scrub keyed on paths as they exist at HEAD leaves every PRE-MOVE path unrenamed, because the filter callback receives each commit's own paths


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
count, not S1's, is the pre-rewrite count.

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
allowlist. **S8 scans exactly S7a's recorded output tip, and first asserts that
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
so no later commit can ride along. The tip check above runs first.

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
turn on the security features that were all off, and re-enter by hand the 20
topics, 10 labels, description and homepage that deletion discarded.

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
SEQUENCE, three acts in order, each recorded in the note before it is issued:
(i) S10b's rulesets are removed and read back gone; (ii) the post-S12 ledger commit,
whose SHA and whose single parent - the adjudicated SHA - are recorded first, is
pushed to `main`; (iii) S7q lifts. The EXPECTED HEAD is the adjudicated SHA until
act (ii) is recorded issued, and from then on either the adjudicated SHA or the
recorded ledger commit - both are legitimate until (ii) is read back landed.

HALT AT S12a, FLIP DID NOT TAKE: the anonymous read still returns 404 with its
positive control passing - the remote is private and unchanged, nothing is
published, and the resume is S12's tip check under a new confirmation. HALT AT
S12a, INSIDE THE CLOSING SEQUENCE: the repository is public, holds exactly the
expected head and nothing else, and the note shows which acts were issued. The
reads settle each issued act - rulesets present or gone, `main` at the adjudicated
SHA or at the recorded ledger commit - and the resume is the FIRST act they do not
show done; act (i) and act (ii) are each idempotent against those reads, so
re-issuing one that took is never needed. HALT AT S12a, STRAY REF: any ref beside
the expected head is PUBLISHED - including one that landed after act (i) removed
the rulesets. It is a POST-PUBLICATION EVENT, never a silent pass: record it and its
window in the note, fetch it into an evidence bundle, scan its reachable history on
S1's axes, and put the scan result in `docs/LEDGER.md` in the post-S12 commit. Its
removal is an in-session adjudicator's ruling - which, while the rulesets stand,
needs the deletion rule lifted for that one act - and the closing sequence does not
advance past the act it halted at until that ruling is made.

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

#### 7. What this plan does NOT discharge

**CS-953 stays open on its own terms.** A filename is not content. ADR 0018
removes the NEED for a scrub rather than proving one correct.

**CS-954 stays TIER 1 and outranks this item.** A push that can ship an ungraded
ref is a defect in the mechanism S10 depends on.

**The 53 wip refs are DISCARDED, not cleared.** Nothing here measures them; that
is deliberate, and it is sound only because S3 and S4 preserve them first.
Any one may be recovered from the bundle and pushed later, **only after it is
measured on all six axes in its own right**, one at a time and on the record.

### Acceptance

every item on that checklist passes, including the full-history secret scan, the PII scan across tracked files and commit messages, the third-party license audit, and the clean-checkout probe on a machine that has never seen the project

## CS-1032

### Acceptance

one end-to-end control renders a known panel in a real browser and is compared against the stand-in's verdict for the same payload, with the comparison recorded whichever way it falls, and the stand-in's DIVERGENCES from the browser are enumerated rather than assumed empty

### Full headline

`tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo, and every panel verdict in the project rests on it: all 37 arms added for the optimize and power panels, plus every existing panel arm, run under `drive()` against a stand-in that nothing compares to a real browser, so "the page renders X" is a claim about the stand-in and not about the page - this project has already recorded that the dashboard's self-signed HTTPS defeats automation browsers and that browser-pane resize, focus and default key scrolling are silently faked, which is why the gap is unclosed rather than merely unnoticed

## CS-1186

### Acceptance

an agent given only a fresh clone and README.md, on a machine with no game
installed, reaches the stated first result using only the commands README gives;
every deviation is recorded and fixed in README, and the walk is repeated clean.

### Full headline

README.md has never been walked from zero to a first result

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

Gate item 5. CS-700 S6 names it and no open item performs it.

### FILED 2026-09-25, from the wave-2 adjudicator ruling (session 113)

**THE NO-GAME HALF OF THIS ACCEPTANCE IS GATED UNDER CS-G08 IN `docs/GATED.md`. THE ITEM
STAYS OPEN, AND THE CLAUSE ABOVE IS UNCHANGED.** "On a machine with no game installed" needs
the same disposable environment CS-G08 waits for, and the true run happens there.

The override approximation is ACCEPTED as the vehicle for walking and fixing README now,
and it does NOT discharge the no-game clause, so this item does not close on it. Its
conditions: point `CLOCKSPEED_GAME_DIR`, `CLOCKSPEED_SAVE_ROOT` and
`CLOCKSPEED_ACCOUNT_DIR` at NONEXISTENT paths and `CLOCKSPEED_LOCAL_CONFIG` at a
nonexistent file - never at empty directories, because `clockspeed/data/locate.py`
resolves an existing empty directory as FOUND and `scripts/verify_env.py` then prints the
game install as present, which is a hollow install rather than no game. Record a positive
control as booleans and resolver labels only, never paths: without the overrides this box
resolves a game; with them the verify_env game-install and save-root rows read
not-resolved. The walk record labels the overrides as an approximation outside README,
not a README step, and records that auto-detection's registry and Steam-library branches
were never exercised in their no-game state.

`docs/GATED.md` classifies this id MENTIONED, not BLOCKED, so the walk stays takeable.

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

Twelve repair rounds sit on branch `worktree-agent-ace624231ac7fd814` at `1ee41a5`,
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

## CS-1214

### Acceptance

the next slow-mode CI reading of the tier-1 guard shard in `.github/workflows/tier1.yml`
is at or under `TIER1_BUDGET_SECONDS` (420s), by moving files or speeding them up, with
every moved file still run by exactly one tier-1 shard and no shard over the 480s
ceiling; neither level is raised. The fill shard, which read 200s, is the first
candidate receiver.

### Full headline

the tier-1 guard shard read 443s at `788695d`, over its 420s budget and in the WARN band

### FILED 2026-09-26, read at the CS-1198 landing (session 116)

Run 36260379206 at `788695d`: guard 443, save 397, gates 332, hook 320 (fast mode; its
slow-mode re-run read 355), fill 200. The guard shard's membership did not change in
CS-1198; it read 407 and 413 on earlier slow runners and holds the CS-814 and CS-815
hook-driving modules for room.

### MEASURED 2026-09-27, the ceiling breached at a docs-only tip (session 117)

Run 36288873612 at `61bce0b`: the guard shard read 480.19s with 2228 passed, 3 skipped,
over the 480s ceiling, so tier 1 went red on a push that changed only docs. The fill
shard's job took about 3.4 minutes end to end in run 36269312405.

### MEASURED 2026-10-02, three files moved guard -> fill (session 118)

THE MOVE, in `.github/workflows/tier1.yml`: `tests/test_liveness.py`,
`tests/test_mypy_gate.py` and `tests/test_probe_refusal_output.py` left the `guards`
step and joined the `fill` step. `FILL_FROM_GUARDS` in `tests/test_tier1_budget.py` is
the new membership pin and `FILL_SHARD_FILES` is now the concatenation of three groups.
NOTHING ELSE MOVED. Neither level was touched, no `timeout-minutes` was touched, and the
38 `--ignore=` lines on the catch-all shard are BYTE-IDENTICAL to `06b8029` - checked by
diffing the sorted ignore lists, not assumed. The file carries 39 in all; the thirty-ninth
is the save shard's own governed deletion and is not a catch-all line, which is the
off-by-one an independent re-derivation of the partition caught in the first wording. The reason that holds in general: both
`guards` and `fill` are non-catch-all shards, so the union of non-catch-all targets is
unchanged and the catch-all's one-ignore-per-target set equality still holds. The arms
that enforce it are the partition arm's clause (3) and the `miscounted` block in
`test_the_fill_shard_runs_exactly_the_moved_files_and_no_other_shard_does`.

THE MODEL, re-derived from the per-file measurements rather than carried forward.
`-n auto` gives W = 2 on `ubuntu-latest` (`tools/tier1_concentration.py` reads
`RUNNER_WORKERS` 2, measured on the runner at the CS-1133 echo). `--dist loadfile` makes
each file atomic and xdist 3.8 sorts the queue by descending test count on every job but
`hooks`, so the schedule is greedy list scheduling of files onto two workers. Both shards
are schedule-BALANCED, so removing weight w buys about w/2, not w - which is why these
are makespans and not subtractions. Local serial seconds scaled at f = 2.05 for
guard-family files and f = 1.65 for fill natives; the worst reading on record implies
1.957 and 1.62 respectively, so both factors over-predict.

PREDICTIONS, which are arithmetic and NOT observations. Guard: 9 files, 688.8s modelled,
makespan 349.3s, self-measured reading about 363s - a 57s margin under the 420s budget and
117s under the 480s ceiling. It holds to f = 2.38, 22 per cent slower than any runner yet
read on this lane. Fill: 14 files, 659.2s modelled, makespan 338.7s, reading about 353s -
a 67s margin. Population: guard loses 100 + 48 + 25 = 173 collected, 2231 -> 2058; fill
1395 -> 1568; the pair's total is 3626 before and after. A changed five-shard total is a
dropped or doubled test.

CONCENTRATION: THE PREDICTED WARN DID NOT REPRODUCE, and the reason is worth keeping.
`python tools/tier1_concentration.py` run against this edited tree reports PASS and the
guard shard CLEAR in both profiled runs - "tests (guard shard): step 437s, top test
29.84s = 6.83 per cent - CLEAR" before and "step 434s, top test 30.16s = 6.95 per cent -
CLEAR" after - against a 14.29 per cent warn level. The reader grades the SHIPPED profile
and not the live workflow, so this edit alone moves no share and no level was touched,
lowered or excluded.

WHAT THE PROFILE CANNOT ANSWER, stated as unverified rather than predicted. The guard
shard's recorded top test in BOTH profiled runs is
`tests/test_liveness.py::test_every_detector_module_is_reached_from_the_graded_population`
- a test this item moved OFF the shard. So the shipped profile no longer names the guard
shard's most expensive test, and it records only the single top test per job rather than a
ranking, so the post-move share cannot be derived from it. A WARN at the next refresh
would need a surviving single test above about 50s at the modelled step. Nothing in this
tree establishes that one exists; the heaviest surviving FILE is
`tests/test_assertion_rendering.py` at 74.22s serial across 69 tests. THE NEXT PROFILE
REFRESH IS THE MEASUREMENT. Until it is read, the guard shard's post-move concentration
is UNKNOWN, not CLEAR and not WARN. WARN is reported and not refused in any case
(`tools/tier1_concentration.py`), and the fill shard is on `PENDING_PROFILE`, so no test
goes red either way.

JITTER, stated honestly. `tools/tier1_growth.py` records the widest measured step between
readings at 129s, so a 57s margin is inside the jitter and one green reading would not
settle it. No guard-and-fill rebalance can clear the jitter: the combined modelled weight
is 1348s over two jobs and two workers, so the best achievable worse-job reading is about
351s. Clearing it needs a sixth shard or a third destination, which is the CS-1133
remainder.

SEQUENCED FOLLOW-UPS, none of them part of this item. `tools/tier1_growth.py` names the
guard shard in `BUDGET_UNMET`; that is computed from the shipped readings record, so the
workflow edit turns nothing red, and the name comes out only at the refresh that records
five green under-budget readings. `PENDING_PROFILE` and `PENDING_READINGS` already name
the fill shard, so adding files to it breaks neither.

MERGE NOTE FOR CS-1207. `tests/test_hook_env_echo.py` was deliberately NOT moved - it is
reserved to CS-1207, which is halted. The halted branch edits the same guards comment
block and the same `FILL_SHARD_FILES`, so it rebases onto this. And the fill shard is now
the wrong destination for it: at 119s modelled it would leave fill near a 30s margin. The
hook shard is the destination that fits - about 128s of room, and its membership is
defined as every file that DRIVES A SHIPPED HOOK, which is exactly what the guards
comment says that file does. That would be the first destination chosen for kinship
rather than for room.

PRE-EXISTING LOCAL RED, NOT CAUSED HERE.
`tests/test_hook_env_echo.py::test_no_account_name_skip_renders_the_name[generic-account-names]`
fails on the operator's box at `06b8029`, before this edit. It is CS-1207's, not this
item's, and no adjudicator should attribute it here.

ALTERNATIVES MEASURED AND REJECTED, so they are not re-pitched. Two files alone
(liveness + mypy_gate) leaves a 37s margin, far inside the jitter. Swapping the third for
`tests/test_sphinx_roles.py` scores 0.3s better and is refused anyway: that file is a
member of `REBALANCED_TO_GUARDS`, so moving it edits a CLOSED item's historical record.
`tests/test_docs_citations.py` or `tests/test_claude_hook.py` as the third overloads fill.
The three rendering files stay together on guard because they share cached helpers.
Adding `--no-loadscope-reorder` to the guard shard is refused: the CS-1198 ruling scoped
it to the hook job alone and an arm asserts no other job carries it.

STILL OPEN. The acceptance is a RUNNER reading, which no local command supplies. Until a
slow-mode CI reading of the guard shard is read at or under budget with no shard over the
ceiling, this is PROGRESS and not CLOSED, and every number above is arithmetic rather
than an observation.

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

## CS-1216

### Acceptance

the `ops/loop/slots.py` release fallback no longer claims a torn in-place write reads
stale: either the neutralising write goes through a temp file and `os.replace` where
the platform allows it, or the docstring states the measured behaviour - a torn record
is unreadable, `is_stale` falls back to mtime, and a fresh write's mtime reads HELD
until `stale_after` elapses; an arm drives `is_stale` on a truncated record with a
fresh mtime and pins the verdict the docstring states, red first.

### Full headline

the slots release fallback docstring says a torn in-place write reads stale; its fresh
mtime makes it read held

### FILED 2026-09-26, an inbox hazard (write before validate) checked against the tree (session 117)

A read-only verifier found every other writer uses temp-then-replace or
create-exclusive-then-fill. The in-place write is a documented Windows workaround; the
effect is benign (the lane holds until `stale_after`), the defect is the false claim.

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

## CS-1219

### Acceptance

a tracked witness records the candidate an adjudication was dispatched over and refuses a
verdict taken over a tree that moved under it: the witness records the candidate's tree
object rather than its commit, so a commit that leaves the tree identical is not a move
and an uncommitted edit is, and it covers compiled bytecode as well as tracked files,
because `__pycache__/` is gitignored and a porcelain check is blind to a swapped `.pyc`.
Shown by two arms, red first: one that edits a tracked file under a recorded freeze and
asserts the witness reddens, and one that leaves every tracked file byte-identical while
swapping a reachable `.pyc` and asserts the witness reddens for that reason alone. The
prose in `tools/headless-queue.md` and `CLAUDE.md` section 5 then points at the witness
rather than carrying the rule alone, and neither file restates what the witness measures.

### Full headline

the adjudication candidate freeze is prose with no mechanical witness, and a porcelain one would be blind to a swapped `.pyc`

### FILED 2026-10-02, an inbox-derived finding that survived refutation (session 118)

`tools/headless-queue.md`, under its "Freeze the candidate before dispatching an
adjudicator" bullet, and `CLAUDE.md` section 5 both order the candidate frozen
before dispatch. A sweep of `tools/`, `tests/`, `ops/` and `.githooks/` for the rule found
only prose: every `freeze`-shaped hit is a `frozenset`, a `drift_guard` frozen-files
report, or the doctrine itself. Nothing records an adjudication's subject and nothing
re-checks it at verdict time. The harm is already MEASURED rather than hypothetical -
`CLAUDE.md` section 5 records that the tree moved under an adjudicator four times in
session 45 and that three whole-suite runs were spent proving a run straddling an edit
says nothing. The bytecode half is live too: `.gitignore` excludes `__pycache__/`, so a
porcelain-based witness reports a clean tree while a stale or swapped `.pyc` sits on disk
and is what the interpreter loads.

## CS-1220

### Acceptance

`tools/measurement_record.py` never reports two readings comparable when either was taken
over a tree whose state is unrecorded: a reading records the tree it was taken over, the
grader refuses a new locally-sourced reading that omits it, and `comparability()` returns a
distinct non-comparable verdict naming the unrecorded tree rather than `comparable`. The
sixteen rows already in `tools/measurements.json` are NOT re-seeded or re-dated - each
keeps its value and is marked as carrying no tree witness, which is what the new verdict
names. Shown by arms red first: one that grades a new local reading with no tree field and
asserts the refusal, and one that asks `comparability()` about a pair where exactly one
side carries no witness and asserts the verdict is not `comparable`.

### Full headline

`tools/measurement_record.py` grades a reading's commit spelling but records no clean-tree witness

### FILED 2026-10-02, an inbox-derived finding that survived refutation (session 118)

`tools/measurement_record.py` grades the `commit` field for spelling only - a lowercase hex
sha of 7 to 40 digits - and carries no notion of tree state; `porcelain`, `dirty` and
`clean_tree` appear nowhere in the module, and
`tests/test_measurement_record.py::test_the_tracked_record_grades_clean` is a schema arm,
not a tree witness. The live field set is `commit, contended, date, method, metric, source,
superseded_by, unit, value, workers`, with no tree-state key. Reachability is bounded but
not zero: of sixteen rows, seven `ci_job` and six `derived` rows are clean by the runner's
own checkout, but two `profile` rows and one `unpaired` row were taken locally and their
tree state is unrecorded. So two `profile` rows agreeing on method, workers and contention
compare as `comparable` when one of them measured uncommitted code, and the delta is
published as fact. This bears directly on CS-1214, whose readings are the kind this record
holds.
