# Clockspeed - live per-item detail, phase 7 - public flip gate

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
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

## CS-704

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-704 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the CS-702 bypass adversary, each route confirmed with a real commit. `git rebase` on BOTH backends, `git am`, `git cherry-pick`, `git revert` and `git commit --no-verify` all land a trailer git itself recognises while the hook stays silent - `git revert` was MISSED by the first enumeration and found later by an adversary, which is worth noting because it is a sequencer sibling of cherry-pick and the list was built by naming routes rather than by asking which hooks each route fires, and an unbootstrapped fresh clone runs no hook at all because `core.hooksPath` is machine-local and is never cloned. Remapping `core.commentChar` or `core.commentString` also defeats the comment-stripping premise. REBASE IS MORE ROUTINE THAN CHERRY-PICK in a worktree-slice workflow, so this class is reachable by accident rather than by evasion. CS-702 is forward-only and single-command by construction; this is the class it cannot cover. A range scan on pre-push or a check on the CI side is the route, and the first **NEEDS A FROZEN-FILE GRANT for `.githooks/pre-push`**.

## CS-811

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-811 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the verifier of the CS-809 repair, MEASURED with proven-landed mutants. The walk is `name.endswith("_RE") and isinstance(value, re.Pattern)` over module globals, so it sees ONE shape; a pattern named without the suffix, held in a dict or a list, compiled at call time, or an arm judging by substring all escape it, and all five were measured green. Its docstring claims it sees anything the module compiles, which is wider than what it enforces. SECOND HALF, same file: `carries_a_citation` decides carrier-hood by SHAPE, so a doc that merely names a tracked test module becomes a carrier and must be guarded or recorded even when nothing in it can rot - 31 currently-clean tracked docs are one pytest-invocation line away, and `docs/OPERATIONS.md` is the likeliest next. That is the intended forcing function but it is an undisclosed recurring hand edit.

## CS-812

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-812 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) as the CS-810 repair's disclosed residual plus one PRE-EXISTING defect its verifier found. The arms de-duplicate by name and cannot say which site is new, which is why the site pin sits in a contract test; the consequence is that `bare_name_problems` and `unresolved_citations` return empty on a genuinely new dead citation of a forgiven name. LATENT rather than live - this module is imported by nothing today, measured. SEPARATELY AND PRE-EXISTING, inherited unchanged from `f938062`: a BARE disposition whose forgiven name later becomes LIVE is never reported stale, because the now-resolves-on-its-own branch is gated on the key containing a path separator and so never fires for a bare key. Four bare-keyed entries are affected. Proven by resurrecting a forgiven name as a real def and observing the module stay green.

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

## CS-820

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 32), MEASURED. Detail in this file under **CS-820 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Filed 2026-08-22 (session 32); the item stays OPEN in `ROADMAP.md`.

**MEASURED, and reported as counts rather than values throughout - the finding is that this class of
output leaks, so the check for it must not leak in turn.** `tests/conftest.py` carries a redaction
hook that covers home paths and account names. It has NO rule for a secret, a token or a credential
of any shape. pytest renders a failing test's ARGUMENTS at the top of its report, so any test taking
an environment mapping as a parameter prints that mapping's values.

One forced failure of one arm rendered an Anthropic API-key-shaped credential IN FULL, together with
several other long opaque tokens. In CI that output goes to the run log.

**THIS IS CS-814's SHAPE ARRIVING THROUGH A SECOND DOOR.** Non-negotiable 12 already rules that error
messages, debug dumps, log lines and exception context ALL COUNT as echo paths; it is written for
save headers and, again, was never carried across. CS-814 records five live credentials in the hook
environment and an outstanding rotation; this item is the reason a test failure is also an exposure.

**THE POPULATION IS UNMEASURED AND THAT IS STATED RATHER THAN GUESSED.** One narrow scan matched two
tracked modules; a broader scan by a different agent reported more. Measuring it is part of the work.
The module that surfaced it, `tests/test_hook_interpreter_ladder.py`, was fixed in place at
`CS-703`'s merge by routing the mapping through a carrier whose repr withholds its contents - so the
instance is closed and the CLASS is this item.

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

## CS-824

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 33) by the CS-823 adjudicator as the SIBLING it found and was told not to widen into. The CS-823 shape does NOT transfer: pytest comes from site-packages, not the working tree, so there is no truncatable file, and the zero-collection case is already refused by the exit-5 guard. What is open is the analogue one level up - pytest exits 0 having run ONE test exactly as it does having run the whole suite, and the hook never reads the count. FROZEN FILE, needs its own grant. Distinct from CS-821, which is about a STUBBED pytest satisfying the presence check; this is about a REAL pytest doing almost nothing.

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

**S7 - Gate item 7, and CS-952 closes here.** See section 5.

**S7a - Rewrite commit identity across all 521 commits**, per the ruling in
section 6. Author and committer only; messages, trees, paths and dates
unchanged. Controls: assert the rewritten commit COUNT equals the pre-rewrite
count, assert every tree SHA is unchanged commit-for-commit - the rewrite must
touch identity and nothing else - and assert `git log --format='%ae %ce'` yields
exactly one address across the whole graph, with a pre-rewrite control showing
it yielded two. **The S3/S4 bundle must already exist and be proven restorable
before this runs**, because this step invalidates every SHA the remote holds.

**S8 - RE-RUN S1 AND S2 IN FULL.** S6, S7 and S7a all change `main`.
**S1 scanned a tree that no longer exists by push time**, and the first draft
said so in prose while omitting the step. It costs about 7 seconds. This is the
last check before anything irreversible.

**S9 - Delete the remote repository and RECREATE IT PRIVATE.** The first
irreversible step, and **it requires the operator's explicit go-ahead at the
moment of running, not this plan's existence.** The recreated repository is
created PRIVATE and explicitly asserted private before S10, so that S12 stays
the sole publication event; a repo created public would make S10 the publication
and strand S11's protections. Immediately before S9, re-confirm (1d) with its
controls - delete-and-recreate is only free while it holds.

**S10 - Push `main` alone.** No `--mirror`, no `--all`, no `--tags`.

**S11 - Verify by MIRROR CLONE, not by `ls-remote`.** Brief section 2(a) says
check what actually ARRIVED, never what the forge advertises. `ls-remote` reads
the advertisement, and after S9 there is no 6-heads control left to check a
pattern against - so the first draft's read-back was trap (b) relocated, not
removed. Clone the recreated remote `--mirror` into scratch and enumerate what
came back: assert exactly one head, zero tags, zero wip, zero of every other
namespace. Then set branch protection on `main`, which the old remote never had,
turn on the security features that were all off, and re-enter by hand the 20
topics, 10 labels, description and homepage that deletion discarded.

**S12 - Flip visibility. Last, and blocked by section 6.**

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
keeping every message, tree, path and date. ACCEPT-as-is and SQUASH-to-fresh-
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
