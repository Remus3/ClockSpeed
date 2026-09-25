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


## CS-704

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-704 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the CS-702 bypass adversary, each route confirmed with a real commit. `git rebase` on BOTH backends, `git am`, `git cherry-pick`, `git revert` and `git commit --no-verify` all land a trailer git itself recognises while the hook stays silent - `git revert` was MISSED by the first enumeration and found later by an adversary, which is worth noting because it is a sequencer sibling of cherry-pick and the list was built by naming routes rather than by asking which hooks each route fires, and an unbootstrapped fresh clone runs no hook at all because `core.hooksPath` is machine-local and is never cloned. Remapping `core.commentChar` or `core.commentString` also defeats the comment-stripping premise. REBASE IS MORE ROUTINE THAN CHERRY-PICK in a worktree-slice workflow, so this class is reachable by accident rather than by evasion. CS-702 is forward-only and single-command by construction; this is the class it cannot cover. A range scan on pre-push or a check on the CI side is the route, and the first **NEEDS A FROZEN-FILE GRANT for `.githooks/pre-push`**.

### Acceptance

a trailer reaching `main` is caught by something that is not the commit-msg hook, proven by replaying a trailer-bearing commit through each named route and asserting each is caught


## CS-813

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-813 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A THIRD AXIS, added 2026-08-22 (session 32) by the fourth CS-703 adversary. The
acceptance text names cleanup mode and commit path; `core.commentChar` is a third and the
matrix is wider than filed.** Measured: with `core.commentChar` remapped, a line led by the
ordinary comment character is NOT a comment to git, survives cleanup into the stored
message, and the hook's pre-filter still drops it - a byte above 0x7E landed in the stored
message with HEAD moved and the hook silent. This does not change the item's direction, it
widens the matrix any acceptance suite has to cover.


Filed 2026-08-22 (session 31); the item stays OPEN in `ROADMAP.md`.

Filed 2026-08-22 (session 31) by the adjudicator of the widened CS-702 grant, which MEASURED the subject-cap escape that nothing else had named.

**THE ROOT FACT: cleanup runs AFTER the commit-msg hook.** On the editor path the hook sees the full
template while the stored message has it stripped, so every check in that hook PREDICTS the stored
bytes and never observes them. The pre-filter drops comment lines and truncates at the scissors
token unconditionally, so it models one mode out of five.

**MEASURED, with real commits and clean controls.** A 200-character comment line as the first line
becomes a 215-character STORED subject with the hook exiting 0 and HEAD moving. A comment line
carrying an em dash lands three bytes above 0x7E in the stored message. Both need only a comment
line - no scissors marker, no flags, no configuration.

**THE CLEANUP TABLE, measured.** `verbatim` and `whitespace` keep comments and keep everything below
the scissors marker. `strip` removes comments and KEEPS what is below the marker. `scissors`
truncates only on the editor path. `default` is `strip` when edited and `whitespace` when not.
Note the consequence: today's unconditional break is wrong on the ordinary editor path too.

**THE OBSERVABLE EXISTS.** Git sets `GIT_EDITOR` to the no-op colon in the hook environment exactly
when the editor was not used. `commit.cleanup` is readable too. What is NOT observable is an
explicit cleanup override combined with an editor, which is the admitted residual.

**WHY 78 GREEN TESTS COEXISTED WITH THREE FAIL-OPENS,** which is the transferable part: every arm
drove one commit path, and one arm ASSERTED THE ESCAPE AS INTENDED BEHAVIOUR. The defective mode
was simultaneously the only mode tested and the mode declared correct. Any suite for this item must
parameterize over cleanup mode by commit path, and must use GIT AS THE ORACLE FOR THE STORED BYTES
- read `git log -1` back from the landed commit and assert the gate blocked if and only if the
stored message violates - rather than asserting against its own model of what git will do.

The trailer half of the same defect is CS-702 and the routes no client-side hook can cover are
CS-704. This item owns the cleanup model, the ASCII escape and the subject-cap escape.

### Measured 2026-08-24 (session 38): the FOURTH leak, salvaged from an inherited worktree and re-derived

**SALVAGED, THEN RE-DERIVED RATHER THAN IMPORTED.** This was built in an inherited worktree
on 2026-08-22, never committed, and was the only record of it anywhere in the project. It was
re-measured from scratch on 2026-08-24 against git 2.53.0.windows.3 in a throwaway repository
before being written here, so what follows is a measurement and not a quotation.

**THE CLEANUP TABLE ABOVE IS INCOMPLETE IN ONE ROW.** `verbatim` additionally preserves
TRAILING WHITESPACE on every line. Under `whitespace`, `strip`, `default` and `scissors`, git
runs its trailing-whitespace pass BEFORE the commit-msg hook; under `verbatim` it does not run
at all. Measured with a first line of 70 characters followed by five spaces:

| cleanup mode | bytes the hook is handed | bytes the commit object stores |
|---|---|---|
| `verbatim` | 75 | 75 |
| `whitespace`, `strip`, `default`, `scissors` | 70 | 70 |

**THE FOURTH LEAK ITSELF.** A subject measured AFTER trimming reads 70 against a cap of 72 and
commits, while the object stores 75. The subject must be measured UNTRIMMED. This is a fourth
escape distinct from the three this item already owns, and it bites under `verbatim` and only
under `verbatim`.

**AND THE ORACLE THIS SECTION PRESCRIBES CANNOT SEE IT.** The paragraph above instructs any
acceptance suite to use git as the oracle by reading `git log -1` back from the landed commit.
MEASURED: `git log -1 --format=%s` renders 70 for the very commit whose object stores 75 - the
placeholder normalises the trailing run away. So the prescribed oracle is BLIND to exactly this
leak, and a suite built on it would stay green while the escape is live. Read the raw bytes
with `git cat-file commit HEAD` and split the header from the body instead. THIS WAS FOUND BY
FALLING INTO IT: the first probe run for this block used `%s`, reported 70 stored under
`verbatim`, and would have refuted a true claim. It is the standing "a probe can validate the
wrong channel" failure, landing on this item's own written instruction.

### Acceptance

a message whose STORED bytes carry a byte above 0x7E, or a stored subject over the cap, is BLOCKED whichever cleanup mode and commit path git actually uses, proven end to end across the mode-by-path matrix rather than on one path


## CS-814

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-814 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 31); the item stays OPEN in `ROADMAP.md`.

Filed 2026-08-22 (session 31). Found by an adjudicator that dumped the hook environment during an
unrelated probe, and CONFIRMED by the merger without echoing any value.

**MEASURED: five live credentials sit in the environment every git hook inherits** - a GitHub
personal access token, three third-party API keys and a harness messaging token. Confirmed by name
and length only. NOTHING IS COMMITTED: no tracked file and no git configuration key carries any of
them, checked. The exposure was into a session transcript, not into the repository.

**THE RULE THIS PROJECT ALREADY OWNS, ONE DOMAIN OVER.** Non-negotiable 12 rules that any code path
echoing raw header bytes leaks personal data, and that error messages, debug dumps, hex previews,
log lines and exception context ALL COUNT AS ECHO PATHS. A hook or a debug path that renders the
environment is exactly that shape for credentials. The reasoning is written down for save headers
and nowhere for the hooks, which is the gap.

**THIS IS THE CS-806 PATTERN AGAIN** - a rule already decided, never carried across to the place it
also applies. That makes three in three sessions, so treat the pattern as the finding rather than
the instance.

**WHAT THIS ITEM IS NOT.** It is not a request to rotate a credential - that is an operator action
and was raised directly. It is not a claim that any shipped hook echoes the environment today;
proving that none does is half the acceptance. The other half is writing the rule where the next
author of a hook will read it, so the third repetition of this pattern is the last.

**ASKED AGAIN AND ANSWERED 2026-08-23. The answer sits with the operator and is deliberately
NOT written here.** What this file records is only that the question has been PUT, so it stops
being carried forward every session as though unasked.

**THE ROTATION STATE OF A LIVE CREDENTIAL IS NEVER WRITTEN INTO A TRACKED FILE.** CS-G03 makes
this repository public eventually, and a tracked sentence asserting the current state of a live
credential is an adversary-useful standing fact that no phase-7 check would strip. A first
version of this paragraph wrote that state down; an adversary caught it and was right.

**THIS CHANGES NOTHING ABOUT THIS ITEM'S ACCEPTANCE**, which was never about rotation: the code
half is still to write the env-echo rule where the next author of a hook will read it, and to
prove no shipped hook path echoes the environment.

### Acceptance

the rule that a hook or debug path rendering the environment leaks credentials is written where the hooks' authors will read it, and a probe proves no shipped hook path echoes the environment


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


## CS-816

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), PRE-EXISTING in the old probe too. Detail in this file under **CS-816 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A THIRD HANG SHAPE, added 2026-08-22 (session 32) by the fourth CS-703 adversary.**
A wrapper of the form `exec python "$@" < /dev/null` answers BOTH probe halves exactly -
the token, then 97 - and then hangs `commit-msg` forever, measured at 124 under a 30 second
cap with HEAD unmoved. Root cause measured: under MSYS bash `/dev/null` maps to Windows
`NUL`, a CHARACTER DEVICE, so `isatty()` reports true, `python -` goes interactive, and the
3.14 REPL spins on an invalid handle. It is DISTINCT from the two shapes above - this
candidate spawns nothing and sets no environment variable - and it is further evidence that
the answer is a BOUND rather than an enumeration of causes.


Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

TWO SHAPES, both measured, one pre-existing and one introduced by CS-819's capture.

**Shape one, PRE-EXISTING in the old probe and unchanged by the repair.** `PYTHONINSPECT=1` makes the
candidate enter interactive mode after running the program, and it never returns. Measured at a
bounded six seconds returning 124 - **WITH stdin already redirected from `/dev/null`**, so closing
stdin does NOT close this. Neither the old probe nor the new one is timeout-bounded, and a hung hook
looks like frozen git rather than a refusal.

**Shape two, introduced by the CS-819 capture and disclosed in its grant.** Command substitution
waits for EOF on the pipe rather than for the child to exit, so a program that spawns a background
process holding stdout stalls the hook for that process's whole lifetime. Measured at 124 under a
bound. LATENT today: the program the hook delivers spawns nothing.

**The route, and its cost.** `timeout` exists at `/usr/bin/timeout` here and on a POSIX runner, but
adding it makes the hooks depend on a binary they currently do not need, and `CONVENTIONS.md` section
16 says such findings are version-specific. Whatever ships must FAIL CLOSED on a timeout - a probe
that times out and then proceeds is the CS-703 defect wearing a clock.

### Acceptance

a hook whose probe does not answer within a bounded time REFUSES rather than hanging, proven with PYTHONINSPECT=1 and a real commit asserting a non-zero exit inside the bound


## CS-817

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); the residual CS-703 explicitly did not close. Detail in this file under **CS-817 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

**This is the residual CS-703 explicitly did not close, and it is recorded so the two are never
confused.** CS-703's probe proves the candidate is a python that runs a program and can report a
failure. It proves NOTHING about what that python can import.

Measured: `py -3` PASSES the repaired probe and `py -3 -c "import pytest"` raises
`ModuleNotFoundError`. That is exactly the `BOOTSTRAP.md` section 2.5 trap - two installations both
reporting the same version, one carrying the toolchain and one not - arriving at a different door
from the one CS-806 closed.

**The exposure differs per hook and that is the part worth carrying.** `pre-push` DOES check
`import pytest` after resolution, and that check is sound now that the interpreter is proven. But
`pre-commit` never checks ruff at all, and `tools/precommit_gate.py` treats a missing ruff as
LINT SKIPPED rather than blocking - so a resolved python without ruff silently degrades the
character-set gate's sibling checks rather than refusing.

### Acceptance

a hook whose resolved interpreter cannot import the tools that hook needs REFUSES, proven with an interpreter that is genuinely python and genuinely missing them


## CS-818

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32); the CS-806 shape one door along. Detail in this file under **CS-818 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 adjudicator. `scripts/verify_env.py` asserts properties of `sys.executable` - the
interpreter RUNNING IT - and never reads `CLOCKSPEED_PYTHON` or performs the hooks' four-rung
resolution. So `verify_env` can pass while the hooks resolve a DIFFERENT interpreter, and a green
environment report is not evidence about the thing that will actually gate a commit.

**THIS IS THE CS-806 SHAPE ONE DOOR ALONG.** CS-806 closed by making this file assert the RESOLVED
interpreter instead of trusting a name; the assertion was never extended to the resolution the HOOKS
perform. Recorded that way deliberately: the pattern is now the finding rather than the instance,
and this is its fourth appearance.

The cheap route is for `verify_env` to run the same ladder and report the winner, failing when that
winner is not the interpreter it just graded.

### Acceptance

it runs the hooks' own ladder and reports the winner, failing when that winner differs from the interpreter it just graded


## CS-821

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), measured with a real push that landed a RED suite. Detail in this file under **CS-821 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

**A SECOND SHAPE, added 2026-08-22 (session 32) by the fourth CS-703 adversary and proven
with a real push that reached the remote: a suite that is 100 percent SKIPPED passes.**
The hook guards exit 5 - nothing collected - and nothing else, so tests that are collected
and then all skipped report 0 and the push proceeds. The hook's own header cites
`CONVENTIONS.md` section 7.2, "a skipped suite is not a passing suite", which is exactly
the sentence this misses. Any fix must judge what the run actually EXECUTED rather than the
code pytest chose to return.


Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Filed by the CS-703 escape adversary and confirmed with a real push that landed a RED suite on a
remote. `.githooks/pre-push` decides pytest is available with `cs_python -c "import pytest"`, judging
the EXIT CODE alone. A directory on `PYTHONPATH` holding a one-comment `pytest.py` satisfies that:
the import succeeds, and `-m pytest` then runs the stub, exits **0**, and collects nothing.

**THE INTERPRETER IS GENUINE, WHICH IS WHY THIS IS NOT CS-703.** The repaired probe correctly accepts
it - it is a real python that runs programs and reports failures. This is TOOLCHAIN SHADOWING, a
sibling of CS-817 rather than the same item: CS-817 is the tool being ABSENT, this is the tool being
REPLACED.

**THE EXISTING GUARD DOES NOT FIRE.** The hook treats exit 5 as "collected zero tests" and blocks on
it. The stub returns 0, not 5, so the empty-suite guard never runs. Any fix must refuse a run that
collected nothing whether it reports 5 or 0, rather than trusting the code pytest chose to return.

### Acceptance

a push whose suite did not actually run is BLOCKED, proven with a real python whose `PYTHONPATH` shadows pytest


## CS-822

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32) by the CS-819 adjudicator; PRE-EXISTING and excluded from that grant. Detail in this file under **CS-822 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

Noticed by the CS-819 adjudicator while reading the offender test, and confirmed to exit 0 under bash
with a real message. The commit-msg byte check builds its offender list with `b > 0x7E` only, so it
catches every byte ABOVE printable ASCII and nothing BELOW it. NUL and the rest of the C0 control
range are accepted into a commit message.

PRE-EXISTING, unrelated to CS-819, and EXPLICITLY EXCLUDED from that grant so the fix is not smuggled
in beside it. Any repair has to permit tab and newline deliberately rather than by omission, which is
the reason this is its own item rather than a one-character change to a comparison.

### Acceptance

a message carrying a control byte is REJECTED end to end with a real commit, with tab and newline explicitly permitted


## CS-824

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 33) by the CS-823 adjudicator as the SIBLING it found and was told not to widen into. The CS-823 shape does NOT transfer: pytest comes from site-packages, not the working tree, so there is no truncatable file, and the zero-collection case is already refused by the exit-5 guard. What is open is the analogue one level up - pytest exits 0 having run ONE test exactly as it does having run the whole suite, and the hook never reads the count. FROZEN FILE, needs its own grant. Distinct from CS-821, which is about a STUBBED pytest satisfying the presence check; this is about a REAL pytest doing almost nothing.

### Acceptance

the hook reads pytest's own collected/passed count and REFUSES below a floor, proven by a real push against a tests tree cut to a single passing test


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

**S9 - Delete the remote repository and RECREATE IT PRIVATE.** The first
irreversible step, and **it requires the operator's explicit go-ahead at the
moment of running, not this plan's existence.** The recreated repository is
created PRIVATE and explicitly asserted private before S10, so that S12 stays
the sole publication event; a repo created public would make S10 the publication
and strand S11's protections. Immediately before S9, re-confirm (1d) with its
controls - delete-and-recreate is only free while it holds. The tip check above
runs first.
Who decides and who confirms: `docs/GATED.md` CS-G03, "who decides the flip and who performs it" (CS-1182).

**S10 - Push `main` alone, BY SHA.** No `--mirror`, no `--all`, no `--tags`. Push
the S8a-adjudicated SHA itself - `git push origin <adjudicated-sha>:refs/heads/main`,
never a branch name - after a pre-push assertion that the local `main` tip equals
that SHA. If it does not, the late-commit rule in S7a applies and nothing is pushed,
so no later commit can ride along. The tip check above runs first.

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

## CS-955

### Acceptance

either a commit cannot carry an index the gate did not grade, or the hook refuses when the index moves under it, proven by a real commit whose index is advanced mid-hook and which is BLOCKED rather than committed

### Full headline

the pre-commit gate has CS-954's shape one level down: it grades THE INDEX at hook time and git then commits from the index, so a stage that lands while the hook runs is committed ungraded - the window is far narrower than pre-push's suite but the mechanism is identical

## CS-1018

### Acceptance

the 262.5s gap is attributed to a named cause or the row is shown to be a different failure from the other eleven, with the evidence recorded either way

**RE-SCOPED 2026-09-25 by the merger, on the slice G re-diagnosis filed below. The
clause above is kept as written and is SUPERSEDED by this paragraph.** The 262.5s gap
is UNDETERMINABLE from the evidence that survives: the one record that would settle it,
the driver's own stdout log for that night, was overwritten by a later night. The item
now requires instead that the driver's own log is RETAINED PER NIGHT, never overwritten,
so the next such gap can be diagnosed, proven by an arm in which two consecutive nights
of the driver leave two logs, each holding its own night's output.

### Full headline

lane run `62f29b90` on the 2026-09-10 night started 262.5s after its predecessor where every other gap is 47.9 to 70.4s, and left no worker log at all while being the LONGEST failing row at 3.151s - `_log_path` creates only the directory and the runner creates the file, so an absent log does not place the failure before the spawn, and a pre-spawn failure would be the fastest row rather than the slowest

### FILED 2026-09-25, from the slice G read-only re-diagnosis in wave 1 (session 113)

Filed verbatim except that its own subheadings are demoted one level to sit inside
this section, and its title line is replaced by the heading above.

Measured 2026-09-24, read-only, slice G, second attempt. The first attempt named host
memory exhaustion as the likely cause; an adversary refuted that on timing, and the
refutation is correct - see "Ruled out" below. Nothing was run against the lane.

#### Verdict

**UNDETERMINED. Neither acceptance clause is met.** The gap is not attributed to a named
cause, and the row is NOT shown to be a different failure from the other eleven - on every
measure available it is the same failure. What the evidence does settle is recorded below
so the next reader does not re-derive it.

#### Evidence read

- `ops/loop/reports/queue_loop.jsonl` (gitignored, primary checkout): the 2026-09-10 night
  is twelve rows. Cycle 1 completed; cycles 2-12 are `launch_failed`, detail
  `LaneLaunchError`, durations 2.165 to 3.151s. Run 62f29b90 is cycle 8: started
  23:25:52.394 local, ended 23:25:55.546, duration 3.151s. Cycle 7 ended 23:21:32.702.
- Gap split: start-to-start 262.5s; END of cycle 7 to START of cycle 8 is 259.7s.
- Worker logs `ops/loop/reports/lane_queue_<run_id>.log`: eleven of the twelve runs have
  one, each exactly 134 bytes (header only). 62f29b90 has none.
- Header-write latency (log mtime minus the row's `started_at`), cycles 2-12 in order:
  0.145, 0.152, 0.147, 0.220, 0.567, 2.037, (none), 1.984, 1.244, 1.289, 2.210s.
- Windows event logs, every log with records, 23:10-23:35 that night.
- Driver code in force that night: `ops/loop/queue_loop.py` at `dd182d7`,
  `ops/loop/lane_launcher.py` at `dd182d7`, `ops/loop/launch_queue_loop.ps1` at `e0523d8`.

#### What the driver code allows between two cycles

At `dd182d7`, between one cycle's `ended_at` and the next cycle's `started_at`, the driver
does only: `append_record` (the ledger mutex is bounded at `LEDGER_MUTEX_TIMEOUT_S` = 5.0s,
then fails open), one `print(..., flush=True)` to stdout, `sleep(settle_s)` with
`settle_s` = 45, `stop_reason` (three file-existence checks), a uuid, and `clock()`. The CI
gate's `head_sha()` runs INSIDE a cycle (after `started_at`) and after a cycle only when the
outcome is `completed`, so it is not in this interval for a `launch_failed` row. The code
therefore bounds the interval at about 50s. The observed 259.7s leaves about 214.7s that no
code path accounts for: the driver process was stalled or not scheduled.

#### Base rate

Across all 40 consecutive-cycle pairs in the ledger, unexplained time
(`next start - prev end - 45 - ci.waited_s`) is 0.7 to 1.7s on every other night, 4.7 to
22.4s in the back half of the 2026-09-10 night, and 214.7s for this one pair. It is unique.

#### Ruled out

- **Host memory exhaustion as the cause of THIS gap.** The Resource-Exhaustion-Detector
  events (System 2004, operational 1003; commit charge at 99.95 per cent of the commit
  limit), the out-of-virtual-memory popup (26) and the error-reporting service stopping on
  "paging file is too small" (7023) are at 23:28:32-33 and 23:34:36 - two minutes forty
  AFTER the gap closed, inside the gap before cycle 11. That later gap carries 22.4s of
  unexplained time, not 214.7s: heavier measured pressure produced a far smaller stall.
- **System sleep or standby.** No Kernel-Power or power-transition event in any log
  between 23:10 and 23:35.
- **A console QuickEdit freeze of the driver's output.** The driver was started by
  `launch_queue_loop.ps1` as `pythonw` with stdout and stderr redirected to files and a
  hidden window; there was no console to freeze.
- **A network wait.** No `gh` or `git` call is on the driver's path between two
  `launch_failed` cycles (see above).
- **A different failure for the row itself.** Its outcome, detail and duration match the
  other ten failed rows. Its missing log fits the same kill: header latency had already
  reached 2.04s at cycle 7 and 1.98s at cycle 9, against a kill that lands a little after
  the 2.0s grace, so a start slightly slower than its neighbours puts the kill before the
  header write. That is consistent with, not proof of, the same mechanism.

#### What remains, and why it cannot be settled now

- Events inside the gap window are only LiveId (23:23:23), Audio (23:23:59), Shell-Core
  (23:24:58), HelloForBusiness (23:25:11-12) and Crypto-NCrypt (23:25:12, 23:25:46) - signs
  of interactive activity at the machine, none of which names a stall. A lock or sign-in
  would be in the Security log, whose oldest record now postdates the night.
- A python.exe process started at 23:19:51 and was the second-largest committer at 23:28;
  header latency began climbing at cycle 6 (23:20:37). That is a correlation with rising
  load, not a cause of a 214s stall that the later, worse pressure did not reproduce.
- The one record that would settle it - the driver's own stdout log for that night - was
  overwritten; only a later driver log survives.

#### For the merger

The acceptance clause is UNMET on the evidence that exists. Either close CS-1018 as
undeterminable, recording the ruled-out list above, or re-scope it. CS-1017, merged in this
slice, makes the next such row self-describing (`launch_reason`, `launch_waited_s`), which
is the only instrument that would have discriminated this case.

## CS-1032

### Acceptance

one end-to-end control renders a known panel in a real browser and is compared against the stand-in's verdict for the same payload, with the comparison recorded whichever way it falls, and the stand-in's DIVERGENCES from the browser are enumerated rather than assumed empty

### Full headline

`tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo, and every panel verdict in the project rests on it: all 37 arms added for the optimize and power panels, plus every existing panel arm, run under `drive()` against a stand-in that nothing compares to a real browser, so "the page renders X" is a claim about the stand-in and not about the page - this project has already recorded that the dashboard's self-signed HTTPS defeats automation browsers and that browser-pane resize, focus and default key scrolling are silently faked, which is why the gap is unclosed rather than merely unnoticed

## CS-1158

### Acceptance

no path a skip record carries because it is PII-bearing or credential-bearing reaches a
rendered report or the `--json` payload in a form that names the artifact, and a test
plants one of each declared class and asserts the rendered bytes carry no leaf name, with
a control proving the same run DOES render an ordinary pruned path

### Full headline

a pruned save file's FILENAME reaches the rendered skip list and the `--json` payload of
`tools/drift_guard.py`, and a save filename carries the world name - CS-1155 made the walk
prune a save file, but the skip record it appends carries the path, `_skip_lines` prints
`skip["path"]` on every run rather than only under `--verbose`, and `--json` serialises
the skip list whole. Measured 2026-09-19 by an
adjudicator at `efb3753`: a synthetic tree containing a save file rendered its leaf name
under the `PII-bearing - a save file carries account and player-name strings` heading. A
save filename carries the WORLD NAME, which CLAUDE.md section 2 puts in the same class as
the account id, and non-negotiable 3 forbids writing it into a log line. Pruning stopped
the CONTENT being read and this is the NAME, which is a separate surface; the CS-1155
comment above `WALK_SKIP_FILE_PATTERNS` declares it rather than claiming otherwise. The
open question the fix must settle first, and the reason this is not a one-line redaction:
whether a FILENAME is personal data under this repository's own classification, which
CLAUDE.md does not say in either direction - if the answer is yes for a `.sav` it is
arguably yes for every path under a directory named for the player, and the answer belongs
in an ADR rather than in a redaction call site
## CS-1174

### Acceptance

the delimiter test in `tools/precommit_gate.py::PLACEHOLDER_RE` classifies a non-ASCII
letter as part of the run, not as a delimiter, so a member between two such letters is
REFUSED on every rule whose alphabet admits them; and a behavioural arm puts a digit on
each side of a member in turn and asserts refusal, so a mutant that lets digits delimit
is killed by behaviour and not only by the pattern-text pin. Both halves fail first, the
tracked-content census stays at zero escapes with both documented sites still forgiven,
and the change arrives under its own adjudicator grant recorded before the edit,
because the file is frozen.

### Full headline

`PLACEHOLDER_RE` treats a non-ASCII letter as a delimiter, and no behavioural arm puts a
digit beside a member

### FILED 2026-09-22, from the adversary pass that could not refute CS-1169

Both residuals were measured by that adversary on the frozen candidate. The non-ASCII
case reaches only the quoted-assignment rule today, because it is the only rule whose
alphabet admits such a letter, and this project's authored content is 7-bit ASCII by
rule - so the exposure is content arriving from outside, which is exactly what the
sweep and the outbound gate read. The digit case is a test-strength gap, not a live
escape: the shipped pattern refuses a digit-adjacent member today.

## CS-1183

### Acceptance

one manually dispatched entry point (CI workflow_dispatch or a tools script) runs
checks 1-7 against a NAMED ref and exits non-zero on any failure; every check
carries a positive control in its own command family and reports its skip count;
it never runs on push. It is the S1/S8 executor, so it includes the CS-1180
trailer axis.

### Full headline

the seven tier-3 flip checks have no runnable job

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

CS-G03's PREP half demands every one of the checks exist as a runnable job long
before the flip, and no open item built any of them - CS-700 names them only as an
umbrella, and an umbrella item hides its weakest member. The tail of
`.github/workflows/tier2.yml` defers tier 3 until phase 7, and phase 7 is now the
goal, so that deferral has expired.

## CS-1184

### Acceptance

a tool reports every tracked md file reachable from no other tracked file and not
on a named allowlist, and every fragment matching no heading in its target, each
proven RED on a synthetic orphan and a synthetic dead anchor; external URLs are
checked only in the tier-3 job, never on push.

### Full headline

no orphan or staleness sweep and no anchor check over tracked markdown

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

Relative-link resolution is ALREADY covered: `.github/workflows/tier1.yml` step
`Markdown link check`, present since the first commit, resolves every relative
markdown link in every tracked `.md` file. It strips fragments, never fetches a URL
and runs no orphan or staleness sweep. CS-700 S6's sentence saying nothing resolves
markdown links is false, and the correction is appended beneath it in CS-700. The
gap this item owns is the narrower remainder of gate item 6.

## CS-1185

### Acceptance

every runtime and dev dependency in pyproject.toml and shell/package.json, direct
and transitive, has a CONVENTIONS s14 verdict recorded with its copyright LINE
read; THIRD_PARTY.md matches that set exactly; a check goes RED on a synthetic
undeclared dependency. ADR 0013 is consumed, not re-derived.

### Full headline

the third-party licence audit covers Electron only

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

CS-G03 records `docs/adr/0013-electron-licence-gate.md` as the audit's first and
only verdict. CS-700 S6 names the audit as gate item 3 and no open item builds it.

## CS-1186

### Acceptance

an agent given only a fresh clone and README.md, on a machine with no game
installed, reaches the stated first result using only the commands README gives;
every deviation is recorded and fixed in README, and the walk is repeated clean.

### Full headline

README.md has never been walked from zero to a first result

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

Gate item 5. CS-700 S6 names it and no open item performs it.

## CS-1187

### Acceptance

in a disposable environment with no prior clone, no hooks path, no user-scope agent
settings and no project cache (e.g. Windows Sandbox), a fresh clone plus the
docs/OPERATIONS.md bootstrap yields verify_env exit 0, armed hooks proven by a
staged violation leaving HEAD unmoved, and a green tier-1 suite.

### Full headline

the clean-checkout probe has never run on a machine that has never seen the project

### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

Gate item 7. CS-700 section 5 records that it FAILS today; CS-938 is one known
cause, not the probe. The `clean-checkout-probe` job in
`.github/workflows/tier2.yml` says in its own comment that it is NOT a substitute,
because a runner is not a machine that has never seen the project.

## CS-1188

### Acceptance

the walk excludes the `.git` entry whether it is a file or a directory, with an arm
that builds a linked worktree in `tmp_path` and passes there, and a control that a
genuine untracked extra in the same worktree still reddens.

### Full headline

the tracked-file walk arm fails in every linked worktree, because `.git` is a FILE
there and the walk reports it as an extra entry

### FILED 2026-09-24, found in wave 1 (session 113)

The failing arm is `test_the_walk_reaches_every_tracked_file_in_this_repository` in
`tests/data/test_drift_guard_data.py`, and `tests/data/test_phase2_gate.py` reaches it
through its child run of the data-layer suite, so the gate reddens with it. Reproduced
at base `403e775` in a linked worktree; the same commit passes in a normal clone,
where `.git` is a directory.

## CS-1189

### Acceptance

item keys reaching any surface response are checked against the registry's closed
vocabulary - an unknown key is flagged per `CLAUDE.md` section 3 rule 7 and never
echoed raw; an arm plants a home-path-shaped key and an account-shaped key through
`tests/save/synthetic.py` and asserts neither reaches the `/api/map` body; and
`MachineState.class_name` gets the same treatment before any route serves it.

### Full headline

the map endpoint serves the save's `ItemTotal.item_key` text verbatim with no
closed-vocabulary check

### FILED 2026-09-24, found in wave 1 (session 113)

An adversary probe planted a synthetic save carrying a dotless ItemClass shaped like a
home path, and one shaped like an account id; both reached the map JSON and the repr of
the route's Response. `ItemTotal` is in `clockspeed/audit/inventory.py` and
`MachineState` in `clockspeed/audit/machines.py`.

## CS-1190

### Acceptance

the CS-700 plan stops the headless queue lane - stop sentinel written, and no driver
verified running - and every other pusher before S7a, and re-checks the remote's refs
immediately before S12; and S9 is split into named sub-steps, each stating the remote's
state on a halt at that sub-step and the rule for resuming from it.

### Full headline

the CS-700 flip plan does not quiesce other pushers, and a partial failure inside S9
leaves the remote in a state the plan does not name

### FILED 2026-09-24, found in wave 1 (session 113)

Nothing in S0 to S12 stops the lane, whose worker prompt `tools/headless-queue.md`
pushes lane branches at its step 9 on un-rewritten history, nor a push from another
clone landing after the mirror check before S12. Inside S9 the delete can succeed and
the recreate fail, or the repository can come up public, and the plan names neither
state.

## CS-1191

### Acceptance

the render-time redaction in `tests/conftest.py` covers the coloured and the
xdist-verbose report paths, with an arm that runs a child pytest under
`--color=yes -n 2 -vv` and asserts zero account-name renderings in its output beyond
the session header CS-447 declares.

### Full headline

under colour output or xdist at `-vv`, the pytest report renders the Windows account
name, because the highlighted assertion diff wraps each token in terminal escape
codes and splits a home path before the personal-data redaction reads it

### FILED 2026-09-25, found by the CS-820 closing adjudicator (session 113)

The adjudicator measured 81 account-name occurrences in the highlighted assertion diff
of an environment mapping, under `--color=yes -vv` and under `-n 2` with `-vv` or
`-vvv`, and zero credential shapes. The same count reproduced at base `403e775`, so the
defect is pre-existing and not introduced by CS-820, whose clause is credential shapes
only. The miss is in `tests/conftest.py::redact_personal_data`, which reads the text
after the escape codes have split the path; stripping or tolerating the escape codes
before it matches is the likely repair.
