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
