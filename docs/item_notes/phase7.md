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


## CS-811

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-811 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) by the verifier of the CS-809 repair, MEASURED with proven-landed mutants. The walk is `name.endswith("_RE") and isinstance(value, re.Pattern)` over module globals, so it sees ONE shape; a pattern named without the suffix, held in a dict or a list, compiled at call time, or an arm judging by substring all escape it, and all five were measured green. Its docstring claims it sees anything the module compiles, which is wider than what it enforces. SECOND HALF, same file: `carries_a_citation` decides carrier-hood by SHAPE, so a doc that merely names a tracked test module becomes a carrier and must be guarded or recorded even when nothing in it can rot - 31 currently-clean tracked docs are one pytest-invocation line away, and `docs/OPERATIONS.md` is the likeliest next. That is the intended forcing function but it is an undisclosed recurring hand edit.

### Acceptance

a judging pattern added in any of the five measured escaping shapes turns `tests/test_docs_citations.py` RED, or each escaping shape is recorded with the reason it cannot be caught


## CS-812

### NOTE - relocated from `ROADMAP.md` 2026-08-23

NOTE: filed 2026-08-22 (session 31). Detail in this file under **CS-812 - detail**; read it before taking this item.

### detail - relocated from `docs/history_notes.md` 2026-08-23

Relocated from `ROADMAP.md` 2026-08-22 (session 31) for budget, not deleted. The item itself
stays OPEN in `ROADMAP.md`.

filed 2026-08-22 (session 31) as the CS-810 repair's disclosed residual plus one PRE-EXISTING defect its verifier found. The arms de-duplicate by name and cannot say which site is new, which is why the site pin sits in a contract test; the consequence is that `bare_name_problems` and `unresolved_citations` return empty on a genuinely new dead citation of a forgiven name. LATENT rather than live - this module is imported by nothing today, measured. SEPARATELY AND PRE-EXISTING, inherited unchanged from `f938062`: a BARE disposition whose forgiven name later becomes LIVE is never reported stale, because the now-resolves-on-its-own branch is gated on the key containing a path separator and so never fires for a bare key. Four bare-keyed entries are affected. Proven by resurrecting a forgiven name as a real def and observing the module stay green.

### Acceptance

an extra site for an already-forgiven citation, and a bare disposition whose name has become live again, are both reported BY THE ARM rather than only by a module-level assertion, or the split is recorded with the reason


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

### Acceptance

a forced failure of a test holding such a mapping renders no value matching a credential shape, asserted on COUNTS rather than values


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

### Acceptance

every item on that checklist passes, including the full-history secret scan, the PII scan across tracked files and commit messages, the third-party license audit, and the clean-checkout probe on a machine that has never seen the project

## CS-955

### Acceptance

either a commit cannot carry an index the gate did not grade, or the hook refuses when the index moves under it, proven by a real commit whose index is advanced mid-hook and which is BLOCKED rather than committed

### Full headline

the pre-commit gate has CS-954's shape one level down: it grades THE INDEX at hook time and git then commits from the index, so a stage that lands while the hook runs is committed ungraded - the window is far narrower than pre-push's suite but the mechanism is identical

## CS-956

### Acceptance

each of the three is measured end to end on a real clone with a positive control proving the instrument can see the opposite answer, and the results are recorded whichever way they fall

### Full headline

three hook properties this project relies on are unmeasured anywhere in it, and CS-952 refused a frozen-file grant on the strength of two of them: whether a hook declared in a TRACKED project settings file fires at all in an untrusted fresh clone, whether a hook's stdout reaches the transcript when it exits NON-ZERO, and whether `python` in a hook command resolves to the toolchain-bearing interpreter, which is guarded for `PreToolUse` and for nothing else

## CS-1014

### Acceptance

an arm drives a path-shaped `pid` through the refusal seam and asserts it reaches neither `detail` nor the written row, and the arm reddens under `return pid`, with a control proving the plant is potent

### Full headline

`queue_loop._holder_pid`'s type guard is ungraded and the mutation `return pid` survives every arm in the file: the guard exists and is correct, but nothing measures it, and `pid` is interpolated bare into the durable JSONL as `(pid {pid})`, so a path-shaped pid off a hand-edited or older lock file reaches the row - this is the same field-by-field shape as the privacy oracle that passed while a row carried an account name, one field over

## CS-1015

### Acceptance

an arm asserts `set(queue_loop._ACQUIRE_REFUSALS)` covers every `refused` word `ops/loop/lanes.py` can emit, DERIVED from lanes rather than restated, reddening when lanes grows or renames one

### Full headline

the lane refusal vocabulary is an unpinned cross-module string contract: `ops/loop/lanes.py` emits `worktree_in_use`, `ops/loop/queue_loop.py` hardcodes the same literal in `_ACQUIRE_REFUSALS`, and four test fakes spell it again, with no import, no shared constant and no contract arm - measured, renaming the word at the emitter alone leaves all 141 queue-loop arms passing, so a coherent rename silently un-fixes CS-1011

## CS-1016

### Acceptance

one arm acquires a lane for real, has a second lane collide on the same worktree, and asserts the WRITTEN row names the fault and the occupying lane, discharging CS-1015 at the same time

### Full headline

no arm drives a real `lanes.try_acquire_lane` worktree collision into `run_cycle`, so the whole CS-1011 proof rests on hand-built dicts and row fidelity against a real refusal is untested end to end - this matters more than an ordinary coverage gap because CS-1011 exists precisely because the row said one thing while the driver decided another

## CS-1017

### Acceptance

the row carries the consumed wait and the reason word, and an arm shows an early exit and a post-grace kill are one field apart in the written row rather than inferred from a total

### Full headline

a lane cycle row records neither the seconds `proc.wait` actually consumed nor the refusal reason, which is why the 2026-09-11 diagnosis had to invent a duration argument that was then refuted: `runner_exited_early` and a post-grace `repoint_refused` kill are indistinguishable in the record, and `duration_s` is the driver cycle clock while the 2.0s liveness grace is measured from the `Popen`, so the two cannot be compared at all

## CS-1018

### Acceptance

the 262.5s gap is attributed to a named cause or the row is shown to be a different failure from the other eleven, with the evidence recorded either way

### Full headline

lane run `62f29b90` on the 2026-09-10 night started 262.5s after its predecessor where every other gap is 47.9 to 70.4s, and left no worker log at all while being the LONGEST failing row at 3.151s - `_log_path` creates only the directory and the runner creates the file, so an absent log does not place the failure before the spawn, and a pre-spawn failure would be the fastest row rather than the slowest

## CS-1019

### Acceptance

a save-layer arm packs a distinct quaternion into an actor record's bytes and asserts the returned `ResourceNode` carries it, reddening when `_node_or_none` substitutes an identity

### Full headline

`clockspeed/save/world.py::_node_or_none`'s rotation and scale carry-through has no arm in its own layer: its only grader is `tests/surface/test_map.py::test_a_node_row_carries_its_own_orientation_off_the_real_parser`, two seams away, and the audit-layer arm is structurally blind to it because it builds `ResourceNode` through a test helper

## CS-1021

### Acceptance

the comments are corrected to say deliberately-not-unit or the values are made unit, and it is decided on the record whether a unit-norm assertion belongs in the save layer's own arms

### Full headline

the rotation constants in `tests/surface/audit_harness.py`, `tests/surface/test_map.py` and `tests/audit/test_placement.py` are NON-UNIT quaternions documented as real factory values: `_MAP_QUARTER_TURNS` calls `(0,0,0.5,0.5)` one of "the four quarter turns about the vertical axis" and "the four spellings a factory actually contains" when its norm-squared is 0.5 and a real quarter turn is `(0,0,+-0.70710678,0.70710678)`, and no arm anywhere asserts unit norm - the shipped code is unaffected because it transcribes and must not normalise, but a panel developed against this fixture is developed against a value the game does not produce

## CS-1022

### Acceptance

`_map_body` is bound to the same two-way guard, proven by a mutant that drops a key from a canned row and fails collection at the named raise

### Full headline

`tests/surface/test_panel_map.py::_map_body` claims to be "shaped exactly as the contract froze it" while carrying 4-key placement rows and no `node_orientation_available`, imports the map endpoint not at all, and binds to neither `PLACEMENT_KEYS` nor `DATA_KEYS` - CS-1013 built `_assert_rows_match` for exactly this drift and left the identical unguarded fixture next door

## CS-1023

### Acceptance

the set is completed or the selection rule is written down and enforced by an arm

### Full headline

`clockspeed/audit/__init__.py` re-exports an arbitrary subset of the placement warning codes: `WARN_PLACEMENT_ORIENTATION_NON_FINITE`, `WARN_NODE_SEMANTICS_UNAVAILABLE` and `WARN_BUILT_CLASS_NOT_PLOTTED` are absent while two siblings are present, and the omission predates CS-1013 - so the package `__init__` is the arbitrary thing rather than any one slice

## CS-1024

### Acceptance

the census reaches every model on the published path, proven by planting a disclosing `str` field on `Placement` and showing the guard reddens

### Full headline

`clockspeed/audit/placement.py::Placement` carries a GENERATED dataclass repr, now rendering six fields, and is invisible to both PII censuses: R1 in `tests/repr_rendering_guard.py` covers only `clockspeed/save/`, and R2 fires only on a `bytes` or `Path` annotation, so `scan_tree()` holds no `Placement` entry at all - no leak today because the six fields are a class name and decimal strings, but this is the one model on the published path whose repr no guard grades, and the next `str` field added there is unmeasured

## CS-1026

### Acceptance

the three are wrapped, proven by a planted-collision arm asserting nothing threw, the panel was NOT marked failed, AND the solve bench built the planted module's field ids - the third clause is what separates a real proof from an arm that passes because the collision silently did nothing; the measured note is reproduced in the CS-1026 ledger citation, which is where it stays - this line carries no routing field because the item has no section

### Full headline

`panel_solve.js`, `panel_map.js` and `panel_scope.js` declare their helpers in the page's SHARED GLOBAL SCOPE while only `panel_registry.js`, `panel_warnings.js`, `panel_optimize.js` and `panel_power.js` are IIFE-wrapped, leaving the unwrapped three one name collision away from a SILENT wrong-render rather than an error: a redeclaration is silent, a mount closes over the binding rather than a snapshot, and `mountPanel`'s `try` only fires on a throw, so the symptom is a normal-looking bench whose request is permanently refused with a message naming the wrong cause

## CS-1027

### Acceptance

both spellings are added to the planted-positive arm and the arm reddens on each, with the tokenizer sweep kept as the independent control

### Full headline

the panel division detectors miss two real spellings: the `DIVISION` pattern in `tests/surface/test_panel_power.py` and `tests/surface/test_panel_optimize.py` fired on 8 of 10 realistic plantings under an adversarial probe and MISSED `x /= y` and `x / -y`, so the arm that enforces non-negotiable 6 in the render path has two holes in its oracle - neither spelling is present today, proven by an independently written JS tokenizer that found zero bare slashes across both panels and `app.js`, so this is an oracle gap rather than a live defect

## CS-1028

### Acceptance

one owner for the routine or a digit-correctness oracle over every copy, proven by a mutant that corrupts a digit and reddens an arm for each panel

### Full headline

`approximateDecimal` now exists in FOUR panel files and only one copy is graded for correctness: `panel_solve.js`'s copy has a digit oracle in `tests/surface/test_panel_solve.py`, while the copies in `panel_registry.js`, `panel_optimize.js` and `panel_power.js` are graded only for "does not divide" and never for "produces the right digits" - so a silently wrong reading aid in the power bench passes today, which is the silently-wrong half of non-negotiable 7 wearing a helper

## CS-1029

### Acceptance

the name states what the arm asserts, and a guard or a review note covers the general case of a renamed assertion keeping its old name

### Full headline

`tests/surface/test_web_assets.py::test_the_page_issues_exactly_one_post_and_no_form` now asserts TWO posts: the docstring was updated when `/api/optimize` gained its door and the FUNCTION NAME was not, so the name states a property the body contradicts and a later reader greps the name rather than reading the body

## CS-1030

### Acceptance

the exponent has ONE owner that the other six cite, or the restatement is placed under a drift guard that reddens when the owner moves

### Full headline

`clockspeed/surface/api/power.py` restates the shipped exponent `1.321929` and its measured float in prose, making a SIXTH tracked copy of a measured number: five modules already do this so it is within precedent rather than a new fault, but CLAUDE.md section 4 says a restated number is a number that will drift and a hardcoded count in a doc is a lie with a timestamp on it

## CS-1031

### Acceptance

every reason in the canned body is read from the module that publishes it, proven by a mutant that changes a published reason and reddens the fixture guard

### Full headline

`tests/surface/audit_harness.py::_power_data` binds ONE reason string to its owner and hand-authors the other four: `ceiling.reason` reads `power.ceiling_reason(None)` while four sibling `reason` values are invented prose, so a panel arm graded against the canned body can pass while the real endpoint says something else - partial binding is the shape CS-1013 was refuted over, one field at a time rather than one row at a time

## CS-1032

### Acceptance

one end-to-end control renders a known panel in a real browser and is compared against the stand-in's verdict for the same payload, with the comparison recorded whichever way it falls, and the stand-in's DIVERGENCES from the browser are enumerated rather than assumed empty

### Full headline

`tests/surface/panel_harness.py`'s DOM stand-in has no known-good browser control anywhere in the repo, and every panel verdict in the project rests on it: all 37 arms added for the optimize and power panels, plus every existing panel arm, run under `drive()` against a stand-in that nothing compares to a real browser, so "the page renders X" is a claim about the stand-in and not about the page - this project has already recorded that the dashboard's self-signed HTTPS defeats automation browsers and that browser-pane resize, focus and default key scrolling are silently faked, which is why the gap is unclosed rather than merely unnoticed

## CS-1034

### Acceptance

every path-shaped privacy needle is asserted through an oracle proven potent by a planted positive that the arm FINDS, and the four arms above redden on a body carrying the reflected path

### Full headline

four anti-leak privacy arms hunt a needle the encoder can never produce: `tests/surface/test_health.py::test_health_answers_200_even_when_a_parameter_it_does_not_accept_arrives` and `::test_a_present_registry_and_world_render_as_words_not_as_what_they_are`, `tests/surface/test_world.py::test_an_unknown_parameter_is_a_400_that_reflects_nothing` and `tests/surface/test_registry.py::test_a_request_naming_a_parameter_is_refused_and_reflects_nothing` each assert a home-shaped path is ABSENT from an encoded body using `needle.encode("ascii") in blob`, but `clockspeed/surface/api/contract.py::encode` is `json.dumps`, which doubles every backslash, so the needle cannot match under any circumstances and a body that genuinely reflects a refused path passes all four - measured, a reflecting body returns True for the not-in assertion - none of the four carries a planted positive, and these guard non-negotiables 3 and 12 - the repo already does it right twice, at `tests/surface/test_registry.py::test_the_body_carries_no_path_shaped_value` which hunts a lone backslash character and `tests/surface/test_map.py::test_an_unknown_parameter_is_a_400_that_reflects_nothing` which uses a JSON-safe canary, so this is a gap and not a limitation

## CS-1035

### Acceptance

the count-carrying raises are graded by an arm that reddens when the count argument is dropped, for the unread raise and the undecoded raise both

### Full headline

`clockspeed/audit/inventory.py` carries CS-1020's ungraded-count shape in the module named beside `placement.py`: `_warning` defaults `count=1` and the two raises inside `inventory_of` pass `unread` and `undecoded`, and NO arm anywhere grades any inventory warning's `.count` - the only arm driving the code, `tests/audit/test_inventory.py::test_the_unread_payload_count_travels_as_the_honest_denominator`, asserts presence alone, so deleting the `unread` argument from that raise takes the served count from 2 to 1 under a fixture where `unread == 2` and the whole suite stays green - the `containers_read` and `undecoded` model FIELDS are properly count-graded by `tests/audit/test_inventory.py::test_the_container_count_actually_read_travels_beside_the_total` and `::test_an_undecoded_container_entry_is_counted_rather_than_dropped`, so the defect is confined to the warning counts

## CS-1036

### Acceptance

both sets are DERIVED - the population set from the `*_placements` fields of `WorldPlacement`, the orientation count from the served rows rather than the constants - each reddening when the shipped model grows, which is the shape CS-1015 already filed for the lane vocabulary

### Full headline

both CS-1025 and CS-1020 enforce their sweeps over a HAND-ENUMERATED population rather than one derived from the shipped model, which is the exact defect class they were filed over: `tests/audit/test_placement.py::POPULATIONS` is the literal pair node and built with nothing binding it to `WorldPlacement`'s own fields, and `tests/surface/test_map.py::EXPECTED_ORIENTATION_COMPONENTS = 14` is asserted against the length of four fixture tuples that exist in no other file - measured, no mutation of shipped code can fail that assertion, so it is a fixture-integrity guard and grades nothing about behaviour - CS-1020 exists precisely because `placement_of` grew a second loop and the test population did not follow it, so a third population would repeat it with every arm green

## CS-1037

### Acceptance

the uniqueness enforcement covers every needle-eligible fixture family rather than the orientation family alone, and the colliding planted pair is either re-picked or documented on the record as safe because its arms compare whole tuples

### Full headline

the fixture collision CS-1025 was filed over survives in two places the repair did not reach: `tests/audit/test_placement.py` still holds, at module level, `PLANTED_ROTATION = (0.5, -0.25, 0.125, 0.8125)` and `PLANTED_SCALE = (2.0, 0.5, -1.5)`, byte-identical to the pre-fix constants and colliding on the same rendering, feeding the membership-based anti-vacuity control inside `test_no_orientation_component_reaches_the_model_as_a_float` where one of seven needles is non-load-bearing; and in `tests/surface/test_map.py` the TRANSLATION components are needle-eligible but unswept, with `BUILT_TRANSLATION[0]` deliberately ambiguous at a count of two - no mutant was found for either, so both are weakened rather than defeated, but a future author writing an anti-vacuity control off a translation walks into the identical trap and the new uniqueness sweep will not see it


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
## CS-1160

### Acceptance

the fork record for `ops/loop/winmutex.py` either cites an upstream digest that some file
on this machine actually carries, or states in the file that the upstream it was forked
from is GONE and gives the date that was measured - and a test grades the claim rather
than the string, so a provenance line that has rotted cannot read as green. The test must
distinguish the two states it can be in: an upstream that is REACHABLE and matches, and an
upstream that is UNREACHABLE from this tree, which is not a failure. It must NOT assert
merely that the digest string appears in the file, which is what the two arms present
today do and is why the rot was invisible.

### Full headline

the fork record for `ops/loop/winmutex.py` cites an UPSTREAM digest no file on this machine carries, and the two arms that mention it assert the string is present rather than that the upstream matches - the constant is
`UPSTREAM_WINMUTEX_DIGEST = f1b4b011112685efb88616c52752657cf896fbb0993b2d2d264e7b3edde8b4f4`
in the fork-record docstring of `ops/loop/winmutex.py` and at
`tests/test_lane_lock.py::UPSTREAM_WINMUTEX_DIGEST`, recorded as the upstream
this tree forked from, and it matches ZERO files on this machine. Measured 2026-09-20 by a census over
every reachable copy: 51 copies carry `0b112a4f6bfa88cf5f537f8869225c1821ebfe97428b1e899979797ddd71a61e`,
14 carry this tree's own fork digest `e0d3ac7d9ba0be16dbe27e95354820393b9bf4edd335c97c98b39dfafb662d3f`,
and none carries `f1b4b011...`. The carriers moved their shared file and this tree's fork
record still names the version it was cut from, which no longer exists anywhere to compare
against. A sixth repository published `0b112a4f...` on the note channel on 2026-09-20 as
the current shared value, which is what prompted the census.

NO ARM BREAKS, AND THAT IS THE POINT. Nothing hashes the upstream. The two arms that
mention it - `tests/test_lane_lock.py::test_the_forked_mutex_wrapper_names_the_upstream_it_forked_from`
and `::test_the_derived_bucket_records_the_file_it_was_derived_from` - assert that the digest STRING
appears in the file's text, which is a presence check on prose. Both stay green while the
thing the prose describes ceases to exist. This is the same class as a docstring whose
behavioural claim rotted across a repair: the assertion grades the sentence, not the world
the sentence is about.

WHAT IS NOT WRONG, recorded so a reader does not go looking for a second defect. The fork
itself is sound and its own pin is correct: `sha256` of `ops/loop/winmutex.py` computed
2026-09-20 equals `tests/test_lane_lock.py::FORKED_WINMUTEX_DIGEST`, and
`python -m pytest tests/test_lane_lock.py -q` is 59 passed, exit 0. The slots digest is
also fine and was briefly mis-transcribed during this investigation: the derivation
docstring of `ops/loop/lanes.py`
and `tests/test_lane_lock.py::UPSTREAM_SLOTS_DIGEST` carry `71fa2a683f2eaa04...`, which is BYTE-EQUAL to the
value the sixth repository published, and byte-equal to the file that repository carries.
There is no slots divergence to reconcile.

THE DECISION THE FIX MUST TAKE FIRST, and why this is not a one-line digest bump. Bumping
`UPSTREAM_WINMUTEX_DIGEST` to `0b112a4f...` would be a LIE of a different shape: this tree
did not fork from that version, it forked from `f1b4b011...`. A fork record is a statement
about history, not about the present. The candidate answers are to keep the historical
digest and add a measured note that it is unreachable, or to record both - what it was cut
from, and what the carriers hold now - and say which is which. ADR 0017 owns the fork
decision and is where the answer belongs if it changes that decision's basis.
## CS-1163

### Acceptance

the citation guard sees a BARE continuation pointer - the `` `:NNN` `` form that follows a
full `path.ext:NNN` citation in the same sentence - or the repository records, in one
place with a measured count, that it deliberately does not and why. A test plants a bare
continuation beside a full pointer and asserts the guard's finding count RISES, with a
control proving the same run still detects the full pointer, so a guard that silently
stopped matching either form cannot pass. Widening the pattern is acceptable only with a
route for every site it newly reddens - the count is 67 and the largest carrier is
append-only - so the acceptance is met by a widened guard PLUS a discharged census, or by
a recorded declination that names the number.

### Full headline

the citation guard's `LINE_POINTER_RE` requires a full `path.ext:NNN`, so the BARE
continuation pointer that follows a full citation in the same sentence is invisible to it,
and 67 of them sit in the corpus today - the form is `` `:NNN` ``. Confirmed by MEASUREMENT rather
than by reading, 2026-09-20, during CS-1162: the `## CS-1160` section wrote
a full pointer at `tests/test_lane_lock.py` followed by a bare continuation, and the
guard reported the full one and NOT the continuation - while the continuation named a
live arm, `tests/test_lane_lock.py::test_the_derived_bucket_records_the_file_it_was_derived_from`.
The two offending pointers are NOT reproduced here in their original form, deliberately:
this section would otherwise carry the defect it describes, which is one of the ways the
corpus grew the other 67.
Both were repaired to symbol form under CS-1162, so the instance is gone and the BLIND
SPOT is not.

THE CENSUS, measured independently of the slice that found it, over every tracked markdown
file excluding `.git`, the channel directories and worktrees:

    42  docs/LEDGER.md                                   APPEND-ONLY, unrepairable in place
    11  docs/_scratch/cs1087_spec.md
     5  docs/history_notes.md                            HISTORICAL, unrepairable in place
     4  docs/item_notes/lane-start-failure-record.md
     2  docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md
     1  docs/adr/0005-overclock-ceiling-source.md
     1  docs/item_notes/phase4-followups-850.md
     1  docs/item_notes/phase4-followups.md
    67  TOTAL across 8 files

**WIDENING THE REGEX WITHOUT A ROUTE FOR THOSE 67 CONVERTS A BLIND SPOT INTO AN UNPAYABLE
BILL**, which is why this is filed rather than fixed inside CS-1162. Forty-seven of the 67
are in the two carriers whose own rules forbid editing them in place, so they cannot simply
be repaired the way CS-1162 repaired the live ones. Every `ARCHIVE_ROT` pin would move at
the same time, and a pin that moves to accommodate rot is the exemption-by-convenience this
repository has already recorded against itself.

THE NUMBER IS ALSO A CORRECTION. The slice that found the blind spot reported the census as
41 in the ledger, 5 in the archive and 4 in one item-notes leaf - three files, about 50
sites. Re-measured here it is 67 across EIGHT files, and the three the slice did not name
include two ADRs and a scratch spec carrying 11 on its own. A census quoted from the file
the finder happened to be reading is not a census.

WHY THE FORM EXISTS AT ALL, because the fix is not simply "ban it". The bare continuation
is a genuine readability idiom - a full citation followed by a bare line number reads
better than repeating the path - and it is used deliberately in prose written by this project. A widened guard would
be asking authors to stop writing English. The candidate answers are therefore to widen the
pattern and require a full citation, to widen it and resolve a bare `:NNN` against the
nearest preceding path in the same sentence, or to declare the form out of scope with the
count recorded. The middle option is the only one that keeps the idiom, and it is also the
one that can mis-attribute when two different paths are cited in one sentence - which needs
its own arm.

RELATED AND DELIBERATELY NOT CLOSED BY THIS ITEM. CS-1144 is open on line-pointer rot in
`docs/LEDGER.md` for a different carrier. CS-1162 closed the symbol-citation rule into the
ledger's Entry-shape table and repaired the live instances. This item is about what the
guard can SEE, not about what the rule requires.



## CS-1165

### Acceptance

a lift that arrives with NO byte pin and NO register row REDDENS an arm, and the arm's
oracle is not a list anybody maintains. The candidate oracles are a comparison of this
tree's tracked files against the carrier trees that hold the same paths, or a produced
provenance manifest that every tracked file has to be accounted for in; whichever is
chosen, the arm is proven by MUTATION rather than by running green - a file copied in
from a sibling tree with nothing added anywhere goes RED naming that file, and the same
arm is green on the tree as it stands

### Full headline

the third-party register's byte-pin roster was hand-maintained, so a lift with no byte
pin at all and no register row is still invisible - the derivation that replaced the
roster grades only files something already pins

### FILED 2026-09-20, on a measured defect in the arm that was supposed to catch it

**WHAT WAS MEASURED.** `ops/loop/slots.py` was vendored byte-identical from the headless
loop of a sibling repository under CS-946, and `THIRD_PARTY.md` went on saying that one
file in this tree was vendored. Nothing went red. The arm that owned the
question in `tests/test_third_party_register.py` - since renamed, so it is deliberately
not named here - read a hand-written `BYTE_PIN_ROSTER` naming one pin module and nothing
else: an ALLOWLIST wearing a guard's clothes, which can only ever grade the files
somebody remembered to add. That is the exact complement of the failure case, so the arm
could never fail for the file that needed it.

**WHAT THE SAME SLICE FIXED, so this item is the residual and not the whole class.** The
roster is now DERIVED: every test module under `tests/` is scanned for a sha256 literal,
and each module that spells one is asked which repo-relative `Path` it binds whose bytes
actually hash to it. The oracle is the BYTES, so a vendoring joins the graded population
the moment its pin does, and the default for an unregistered pin is RED rather than
silence. It found `ops/loop/winmutex.py` as well, which no register row had ever named,
and the register now carries rows for both. The arms are
`tests/test_third_party_register.py::test_every_byte_pinned_file_is_registered` and
`tests/test_third_party_register.py::test_every_registered_vendored_file_is_byte_pinned`,
graded in both directions and each proven by a mutation of the register.

**WHAT IS LEFT, and it is the reason this item exists.** The derivation's oracle is the
PIN. A file lifted into this tree that nobody pinned AND nobody registered is invisible to
it, because there is no digest anywhere for its bytes to agree with. Both files found this
time happened to carry pins written for other reasons - a cross-repo byte-identity contract
and a fork record - which is luck, not coverage. The register's own gate says an entry is
written BEFORE the lift; nothing in this tree enforces that, and the two rows filed today
were both gated after the fact.

**THE SAME SHAPE IS ALREADY ON THE ROADMAP TWICE**, which is why the class matters more
than the instance: CS-1036 records two sweeps enforced over a HAND-ENUMERATED population
rather than one derived from the shipped model. A guard whose population is typed by hand
is green about whatever was typed.

**WHAT WOULD SETTLE IT, and what would not.** Adding a second hand-maintained list of
expected vendorings would reproduce the defect one file later and must not be accepted as
the answer. Two oracles are real: a comparison against the sibling trees that carry the
same relative paths on this machine - which is green-by-skip on a CI runner and so can
only ever be an advisory second opinion - or a provenance manifest that every tracked file
must be accounted for in, which is the only form that runs anywhere. The acceptance above
takes either, and takes neither on a green run alone.

### MEASURED 2026-09-22 - progress: the branded half is graded, the de-branded half is not

`tests/test_unregistered_lift.py::test_no_unaccounted_file_spells_a_sibling_namespace_marker`
reddens any tracked or untracked-unignored file that spells a sibling repository's item id
or resource prefix and is neither registered nor the pin module of a registered file. The
sibling codes are read at run time from the `docs/CHANNEL.md` roster. Proven by
`test_a_verbatim_sibling_lift_at_a_fresh_path_is_named`, and by an adjudicator plant of
`ops/loop/slots.py` at a fresh path, which went red naming it. A copy of
`ops/loop/winmutex.py` at a fresh path stays GREEN - a lift whose header names no sibling
is still invisible, so the acceptance is NOT met. The remaining oracle is the
whole-population provenance manifest the acceptance already names; it is not a list of
expected vendorings and is not forbidden. The branded arm stays after it lands, because it
also catches a lift that was entered in the manifest as authored here.

## CS-1168

### Acceptance

the question is SETTLED IN WRITING before any sweep widens, and the settlement names the
boundary as a RULE rather than as a list of directories. Either outcome closes it: a
widened sweep, or a recorded declination that states what stays invisible and why. A
widened sweep must carry an arm that plants a synthetic fragment-assembled credential in
an uncommitted file INSIDE the boundary and asserts it is DETECTED, a second arm that
plants one OUTSIDE the boundary and asserts the run reports it as NOT COVERED rather than
passing silently, and a control proving the same run still detects a staged one - because
a widened population that quietly stopped reading the old one is a regression wearing a
feature's clothes. The boundary must not read a sibling tree's files. The cost must be
MEASURED and recorded, not estimated, and the fleet half must be routed outbound rather
than implemented here.

### Full headline

every credential-scanning population in this tree is REPO-SCOPED - the commit gate grades
the staged set and the repo-wide sweep grades the tracked set, so nothing here can see a
credential sitting in a file that is never committed, which is exactly where the key found
on this machine sat for ten days

### FILED 2026-09-20, as the population half of the plaintext-key incident

**THE DISTINCTION THAT MAKES THIS THE ONLY DETECTING CONTROL.** CS-1166 makes the rules
able to recognise the family. CS-1167 makes the coverage row honest about which rules are
alive. Neither would have found the key, because neither changes WHICH BYTES ARE READ. The
commit gate's population is the staged set and the sweep's is the tracked set; the exposed
files were in neither for ten days. Widening the population is the only proposed control
that would have DETECTED the incident rather than prevented a different one.

**WHY IT IS FILED RATHER THAN DONE.** The obvious fix - point the sweep at the shared
scratch directory - crosses two lines this tree holds. That directory is not this
project's: it is shared across the fleet, and a sweep that reads it reads files other
trees wrote, which collides directly with the rule that a tree does not read a sibling's
files. And a boundary drawn as a path is a boundary that rots the first time a tool writes
somewhere else, which is the same defect as an allowlist wearing a guard's clothes. So the
item has to decide the RULE - what makes a directory in scope - before it decides any
path.

**THE HALF THAT IS NOT OURS.** A machine-wide credential sweep is a fleet control with one
owner and several beneficiaries. Implementing it five times, once per repository, produces
five populations that disagree and five places to forget. The split this item must
propose: this tree owns the detection RULES and the arms that grade them, and the fleet
owns the population and the schedule. The outbound half goes to the sync inboxes as a
note, and this item does not close on the note being sent - only on the boundary being
written down here.

**THE COST IS REAL AND MUST BE MEASURED.** A tracked-set sweep is bounded by the index. An
unbounded filesystem walk is not, and this machine has already recorded a runaway process
filling a disk and a walk that descended into directories it should have stopped at. Any
widening arrives with a measured runtime and a stated stopping rule, or it does not
arrive.


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

## CS-1175

### Acceptance

a narrowing of any `SECRET_PATTERNS` rule that is not an alternation branch - dropping
the case-insensitive flag, dropping or shortening a word-prefix quantifier, raising a
length quantifier's minimum, or removing a member range from a character class - reddens
the credential row naming the rule and what narrowed, proven by mutation on at least one
rule per narrowing kind with the pristine tree green in the same run; OR, where a kind
cannot be graded by canaries without a hand list, an arm pins each rule's compiled
flags and quantifier bounds against a DERIVED fingerprint so any change reddens and
must be re-recorded deliberately. Separately, no canary value renders under
`--showlocals`, proven by forcing an arm red with that flag and grepping; and the
comment in `tools/outbound_gate.py` about a missing private regex parser states what
actually happens, measured.

### Full headline

a secret rule narrowed by its flags, a quantifier or a character class keeps every
canary green, and `--showlocals` still renders canary values

### FILED 2026-09-22, from the adversary pass that could not refute CS-1172

Measured on the frozen CS-1172 candidate. The most consequential single case is the
flag: without it the quoted-assignment and high-entropy rules stop catching an
upper-case assignment spelling, and nothing reddens. The rules live in the frozen
`tools/precommit_gate.py`, but nothing here requires editing it - the grading side is
`tools/outbound_gate.py` and the tests.
