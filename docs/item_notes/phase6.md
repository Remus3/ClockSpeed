# Clockspeed - live per-item detail, phase 6 - surfaces

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 6` heading.

**THIS LEAF IS YOUNGER THAN ITS SIBLINGS AND ITS BODIES DID NOT COME FROM THE SPLIT.**
Phase 6 carried no leaf until the sections below were written, so every one of them
arrived from an item LINE in `ROADMAP.md` rather than from `docs/item_notes.md` or
`docs/history_notes.md`. A body here is the text that used to sit on the line, moved
rather than deleted, and it is a LIVE INSTRUCTION for the same reason a sibling's is.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-609

### Relocated from `ROADMAP.md` 2026-09-01

The item line carried its counts and its second site inline. Both moved here so the line
holds the fault and the acceptance alone.

`_spellings_of()` produces FOUR spellings, and collapses them to ONE where the path
carries no backslash - which is every path on the every-push lane. The derivation now
records that collapse, so the fact is not lost at the point it happens.

**WHAT IS STILL UNRECORDED IS THE CONSUMPTION, AND THAT IS THE ITEM.** Two consumers
read the collapsed set - the detector, and the A6 production sweep - and each therefore
grades A QUARTER as much on that lane as a reader of a green run would assume. Neither
site records the collapse where it consumes it. The acceptance admits either remedy:
derive the spellings from what the running platform can actually produce, or record the
collapse at the point of use.

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`_spellings_of()` collapses its spellings where the path carries no backslash, and the detector and the production sweep grade less on the every-push lane with no record where they CONSUME it


## CS-614

### Relocated from `ROADMAP.md` 2026-09-01

The arm is
`test_run_exits_non_zero_on_a_bind_failure_and_binds_nothing_else`.

**THE MECHANISM.** It asserts over EVERY thread in the process whose name contains
`serve`, and CPython folds a target's function name into the DEFAULT thread name. So a
thread another test started with `serve_forever` as its target and never joined carries
`serve` in its name through no intent of anyone, and this arm counts it.

**WHY THE FAILURE IS WORSE THAN THE FLAKE.** The arm's message blames a failed bind. A
reader of the red therefore investigates the bind path, which is not where the fault is.
The acceptance asks the arm to count only the threads its own call created, or to
distinguish a pre-existing one and NAME it - either remedy makes the message true.

## CS-615

### Relocated from `ROADMAP.md` 2026-09-01

The counts moved off the line; they are measured values and the line is not their owner.

The tier-2 count floor is `tests > 0` POOLED over FIVE suites, and the per-file liveness
arm asks only for one `test(` in each file. A pooled floor is met by its strongest member,
so the two together admit a tree in which all five suites are one-test stubs: every lane
stays green with 169 of 174 arms gone.

**THE ACCEPTANCE DELIBERATELY REFUSES A LITERAL.** An expected count written as a number
in the guard is the same defect one level along - it drifts the first time a suite gains
an arm. The count has to come from a recorded per-suite declaration.

## CS-616

### Relocated from `ROADMAP.md` 2026-09-01

**THE THREE STATEMENTS, AND WHERE EACH ONE LIVES.**

- `shell/lib/trust.js` and `shell/main.js` both state that `callback(0)` switches
  Certificate Transparency off for the WHOLE SESSION.
- The same file states that DEFER leaves full validation on.
- ADR 0014 headlines that nothing is disabled wholesale.

**THEY CANNOT ALL HOLD.** TRUST fires on the only page load, so if `callback(0)` really
is session-scoped then the second and third statements are false from that moment on.
The question is a fact about a running Electron, not about the source: settle it against
one.

**IF IT CANNOT BE SETTLED, THE CLAIM COMES OUT OF ALL THREE PLACES** and the
unverifiability is recorded in THIS section. Do not leave one of the three standing on
the grounds that it is the one that happens to be written most carefully.

## CS-618

### Relocated from `ROADMAP.md` 2026-09-01

`shell/lib/state.js` interpolates untrusted state-file content VERBATIM into its fault
strings. The measured instance is the `schema` property: a planted `schema` value renders
a home path or a world name into a message, which non-negotiables 11 and 12 forbid
regardless of how the value got into the file.

**THE SIBLING ALREADY SHOWS THE SHAPE OF THE FIX.** `endpoint.js` makes the same property
a CONSTRUCTOR INVARIANT over a CLOSED FAULT SET, so no caller-supplied text reaches a
message at all. That is the same closed-vocabulary idiom `clockspeed/surface/config.py`
states, and the acceptance names it so the remedy is not re-derived from scratch.

## CS-619

### Relocated from `ROADMAP.md` 2026-09-01

`shell/main.js` and `shell/preload.js` are executed by NO test in either language. What
that leaves ungraded, enumerated so the acceptance's "whichever parts are pure" has
something to be measured against:

- the verify-proc installation
- the CSS injection
- the debounce
- the close flush
- the certificate refusal path

`node --check` and the static scans are the only things reading these files today, and
neither executes a line.

**ADR 0014 FRAMES THE UNGRADED SET AS DISPLAY-BOUND**, which the list above contradicts -
the certificate refusal path is not a display concern. The acceptance requires that
framing to change as part of closing this item, so the ADR stops arguing for a gap that
is wider than it says.

## CS-872

### Relocated from `ROADMAP.md` 2026-09-01

The composed page opens with no default keyboard scrolling, because a NON-ROOT SCROLLER
is not the default scroll target.

**WHY THIS NEEDS A REAL ELECTRON RUN TO GRADE.** The acceptance asks for a cold key press
to scroll the composed page with the band still covering no content. The band is a DRAG
REGION THE OS DRAWS OUTSIDE THE WEB CONTENTS, so no headless or in-page harness can
observe both halves of that condition at once - the scroll is observable in the web
contents and the band is not. Grading it means running the shell.
## CS-887

### NOTE - filed 2026-09-03 (session 57) by the merger, MEASURED BEFORE FILING, from a CS-882 builder

**THE SAME FAULT FAMILY AS CS-882, AND THIS ONE HAS A LIVE WRONG INSTRUCTION IN THE
RUNBOOK.** CS-882 fixed `scripts/make_cert.py`, whose colliding table was a module
docstring. This module's table is in `docs/OPERATIONS.md` section 7.3, which is what an
operator actually reads at a failure.

**MEASURED AT 528d5b6, NOT READ.** `python -m clockspeed.surface
--clockspeed-not-a-real-flag` exits 2. `docs/OPERATIONS.md` documents 2 as the port
refusal and instructs: find what holds it, or pass `--port`. A mistyped flag therefore
sends the reader to look for a process holding a port that was never bound. The same
sweep measured `--help` exiting 0 against a documented clean stop.

**THE TABLE CLAIMS COMPLETENESS**, which is what turns a gap into a false statement:
`docs/OPERATIONS.md` says anything outside it is a malfunction rather than a refusal. A
usage error is a refusal, is outside the table, and is not a malfunction.

**THE CODES ARE DECLARED, BUT ACROSS TWO MODULES.** `clockspeed/surface/__main__.py`
declares `EXIT_CONFIG`; `clockspeed/surface/server.py` declares `EXIT_OK`,
`EXIT_BIND_FAILED` and `EXIT_CERTIFICATE`. argparse owns 0 and 2 for its own outcomes and
neither module declares them for those outcomes, so a derivation over the declarations
alone cannot see the collision. That split is why the acceptance says the two modules.

**`--help` EXITING 0 IS DELIBERATELY OUT OF SCOPE.** The operator ruled in session 57,
on the CS-882 repair, that `--help` must exit 0 and that POSIX convention outranks a
distinctness universal for that one pair. Do not widen this item to move it, and do not
cite CS-882's arm as precedent for doing so - CS-882 ships that pair as a stated,
reasoned exemption rather than as a met universal.

**DO NOT FOLD THIS INTO CS-604.** That item is about `docs/OPERATIONS.md` restating the
port BAND that `config/ports.json` owns. Same file, different owner and different fact.

**A THIRD SITE WAS MEASURED AND IS NOT FILED.** `scripts/verify_env.py` also exits 2 on a
bad flag, but publishes no exit-code table, so nothing collides there today. Recorded so a
later reader knows it was looked at rather than missed.

## CS-909

### NOTE - filed 2026-09-05 by the merger, MEASURED BEFORE FILING

**THE COMPANION HAD NEVER BEEN EXECUTED UNTIL 2026-09-05.** `shell/node_modules` did not
exist, so every prior claim about the WINDOW was a claim about source. It was run at a real
display on that date, and checks 1 and 3 of `docs/OPERATIONS.md` section 8.3 are filled in
from that run. **Checks 2, 4, 5 and 6 still read `NOT RUN` and are still unrun** - do not
read the two filled-in lines as evidence about the other four.

**THE DECISION AND ITS FENCE ARE `docs/adr/0015-the-shell-may-start-the-surface.md`.** Read
it before arguing about where the spawn belongs; the Python-launcher alternative and the
IPC-to-quit alternative are both refused there with reasons, and re-deriving either is
wasted work.

**THE DESIGN SPLIT, AND WHY IT IS NOT TASTE.** Every decision this item makes goes in a
pure module under `shell/lib/` that imports no Electron - `shell/lib/supervisor.js` for
spawn, adopt and stop, `shell/lib/tray.js` for the tray's own choices - and `shell/main.js`
stays WIRING. The reason is CS-619, which is open in this same phase: `shell/main.js` and
`shell/preload.js` are executed by NO test in either language, because they import Electron
and no test can cross that import. A decision written in `shell/main.js` is therefore a
decision graded by `node --check` and a static scan, and by nothing that runs it. A module
that loads on a bare Node is graded by `node --test`. **This is the same trap ADR 0014
records paying for after the fact** - its verdict-to-integer map sat in `shell/main.js`,
survived three separate blanket-bypass mutations with every lane green, and had to be
lifted out into `shell/lib/verdict.js` afterwards. Do not re-earn that.

**ONLY STOP WHAT YOU STARTED.** If a dashboard is already answering when the shortcut
fires, it is ADOPTED - nothing is spawned and quitting leaves it running. If none is, the
launch spawns one, owns it, and stops it on quit. **The ambiguous case resolves to ADOPT**,
because a dashboard the operator started may be in use from a browser and killing it would
be the shell ending something it never began. The arm that matters is the negative one:
quit with an adopted dashboard, and assert it is STILL LISTENING afterwards. An arm that
only proves the owned one dies passes on a shell that kills both.

**THE TRAY ICON CANNOT BE A FILE, AND THAT IS A MEASURED CONSTRAINT RATHER THAN A STYLE
RULE.** Measured 2026-09-05: no tracked file in this repository carries a NUL byte, and
`tests/shell/test_shell_assets.py` holds every byte under `shell/` at or below 0x7E. A
`.png` or `.ico` committed for the tray would be the first tracked binary in the project
AND would redden that arm. The icon ships as an ASCII base64 data URL built at runtime.
Note the boundary CS-623 is open about while you are here - the Node arm accepts 0x7F and
the Python one caps at 0x7E - and do not pick the looser one for this asset.

**`npm install` DOES NOT GIVE YOU A RUNNABLE ELECTRON, AND THE RUNBOOK SAID IT DID.**
Measured 2026-09-05 against the version `shell/package.json` pins: that `electron` package
ships no `scripts` block at all, so there is no postinstall - the install resolves the tree,
fetches no runtime binary, and exits 0 in about half a second. The binary is fetched LAZILY,
by the package's own entry point on the first `require("electron")`. Under a shell that is a
long silence; **under a shortcut it is an icon that does nothing for minutes, and an
exception rather than a window when the machine is offline.** `docs/OPERATIONS.md` section
8.1 step 3 is corrected, and the shortcut runbook in 8.4 points at the correction.

**THE ACCEPTANCE IS DELIBERATELY NOT SATISFIABLE BY A STATIC ARM.** The tray, the
hide-on-close and the shortcut itself are display-bound in the same way CS-872 is: no
headless or in-page harness can observe a tray icon or an OS shortcut at all. What a static
arm CAN grade is the supervisor's decisions, and that is exactly why they are lifted out of
`shell/main.js`. Grading the pure half and calling the item done is the failure mode here;
the run at a real display is not optional.


## CS-910

**The tool a script runs is chosen by where the process is standing.**

`scripts/make_cert.py` resolves openssl through `shutil.which`, and its docstring
reasons that this is the safe shape because the alternative - a spelled absolute
path - would carry an account name. The first half of that reasoning is right and
the second half was never checked.

MEASURED 2026-09-05 on the pinned interpreter, in a directory containing a planted
executable and with `NoDefaultCurrentDirectoryInExePath` absent from the
environment: `shutil.which` returned a RELATIVE path to the planted file. CPython
gates that behaviour on `_win_path_needs_curdir`, which consults
`NeedCurrentDirectoryForExePath`. That variable is set at NEITHER machine nor user
scope on this machine, so a process launched from Explorer - or from anything that
does not set it for itself - has the current-directory search live. Some shells set
it, which is why a first probe of this class came back clean and meant nothing.

**WHY THIS IS NOT ONLY make_cert.py's PROBLEM.** The finding arrived while
repairing the same class in `shell/main.js`, where spawning a bare interpreter name
with the repository root as the child's working directory was a local
code-execution vector - the root grants Modify to Authenticated Users on this
machine. `shell/lib/supervisor.js::resolveInterpreter` now walks PATH itself,
refuses any entry that is not rooted, and never consults the working directory. The
question this item asks is whether every OTHER external tool this repository spawns
has had the same answer applied, not merely openssl.

**DO NOT FIX IT BY SPELLING A PATH.** Non-negotiable 3 still forbids an absolute
tool path in a tracked file. The resolution has to happen at runtime, from the
environment, with the current directory excluded - which is what the shell side
now does and is the shape to mirror.

**WHAT WOULD SETTLE IT:** an arm that plants a candidate in the working directory
and reddens if the resolver offers it, applied to every spawn site the repository
has, not only to the two known ones.

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the tool a script spawns must not be chosen by where the process happens to be standing, and `tools/toolpath.py` now answers that for seven sites - but the item's own acceptance asks it of EVERY external tool this repository spawns and four sites sit in FROZEN files, `scripts/install_hooks.py::run_git` and `::run_git_optional` plus `tools/precommit_gate.py::ruff_command` and `::git`, while `make_cert` and `make_shortcut` delegate their argv to a runtime arm that no census re-derives


## CS-604

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`docs/OPERATIONS.md` restates the base port and the band that `config/ports.json` owns, and the file is absent from `tools/doc_budget.py`'s measured population so neither fault is caught


## CS-606

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`clockspeed/surface/__main__.py`'s success path is unexercised because it installs a process-wide SIGINT handler that would replace pytest's, so only its refusal branches are graded


## CS-607

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`tests/test_mypy_gate.py::test_the_oracle_reproduces_the_real_runs_discovered_set` fails INTERMITTENTLY in a full-suite run and blocked a real push, while passing every time in isolation


## CS-610

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`tests/conftest.py` leaves a skip report unredacted because a skip's `longrepr` is a tuple its redactor declines to touch, so a skip reason that ever interpolates a machine value leaks with nothing to catch it


## CS-611

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`allow_reuse_address = False` is justified by a Windows measurement, but on POSIX the same setting makes a rebind of the FIXED allocated port fail through the TIME_WAIT window, and every arm binds an ephemeral port so the divergence is graded by nothing


## CS-612

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`test_the_generated_key_is_restricted_to_this_account` may be tautological on the only platform that runs it, because openssl may already open the key file 0600 and leave `_restrict` doing nothing


## CS-620

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the Node behaviour suite runs only in tier 2, so a `shell/lib` regression merges green and stays invisible until the nightly, while two commit subjects invite the reading that both lanes cover every push


## CS-621

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the tier-2 syntax step enumerates `git ls-files -- shell` while the Python guard uses `--cached --others --exclude-standard`, so an untracked `.js` under `shell/` is graded by one gate and skipped by the other


## CS-622

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the forbidden-token sweep is a substring test over eleven literals, so any string concatenation defeats all eleven at once, and `appendArgument`, `setSSLConfig` and the command-line switch spellings are absent from the table entirely


## CS-623

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

two arms grade the same 7-bit-ASCII property with different boundaries: `shell/test/window.test.js` accepts any byte at or below 0x7F while `tests/shell/test_shell_assets.py` caps at 0x7E, so a DEL byte passes the Node lane and reddens the Python one


## CS-913

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

unlock state is EMPTY for every save and the cause filed with it is REFUTED by the code: `clockspeed/save/world.py::_read_unlocks` takes ZERO arguments and returns `EMPTY_UNLOCK_STATE` unconditionally, so the emptiness is a property of the producer rather than of any save, while `clockspeed/save/objects.py::read_properties` is a complete tagged-property decoder with no production caller - the grammar was measured and the plumbing was never built


## CS-914

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`clockspeed/save/workdir.py` stages a copy through a partial whose name is a pure function of the destination and opens the destination truncating, which is the CS-911 shape in Python and reachable on the DEFAULT path: the dashboard is a `ThreadingHTTPServer`, `clockspeed/surface/providers.py` re-reads a world per call with no cache and no request lock, and `work_root()` falls back to a shared `<repo>/work` - MEASURED 31 of 240 concurrent copies failing at realistic save size, and the failure reaches the operator as a fact about their save because `providers.world()` answers None for a missing directory, an empty one and an unparseable save alike; `clockspeed/data/version.py` carries the same shape with a weaker trigger, and neither module has a single concurrency arm


## CS-915

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

two guards report zero findings for a reason that is not the absence of findings: the overlay arm in `tests/surface/test_web_assets.py` declares tokens with `[A-Za-z0-9-]` and compares their values with `[a-z0-9-]`, so an uppercase custom property drifts silently past the check, and `test_the_harness_answers_every_route_it_publishes_as_live` discards the METHOD on both sides, so re-keying every canned answer to `TRACE` leaves it green - both LATENT today and both demonstrated by mutation


## CS-916

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

three separate features are gated on ONE prerequisite and nothing files it: node semantics, where `/api/world` carries 797 placements and says in its own warning that purity and resource type are level defaults a save never writes; icons, which can never be committed because non-negotiable 2 forbids anything extracted from the install and the CSP publishes no `img-src` so every image is blocked today; and a to-scale factory planner, for which `/api/registry` publishes recipes and `is_fluid` but `BUILDING_KEYS` carries only `key` and `display_name` - no footprint, no port count, no port side, no power draw, so not one building can be drawn to scale


## CS-603

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

`tests/test_scaffold.py` excludes `clockspeed/surface/web` on a reason that has expired, so the file asserting the package topology now states something false about it


## CS-608

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

`tests/surface/test_web_assets.py`'s personal-data sweep matches only Windows-shaped paths, so on the every-push lane it grades three of its six shapes while its own control stays green


## CS-613

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

every TLS arm sits behind `cert_pair`, which skips when openssl cannot be run, so a runner without openssl loses the whole TLS path as a skip rather than as a failure

## CS-988

### FILED 2026-09-12 (session 87) after FOUR measured instances inside one item, not from a read

**THE SHAPE.** A value decides what a population MEASURES - which files are swept, which
sentences are planted, which arms are parametrized into existence. It is guarded by a
floor: `>= MINIMUM`, `> 0`, `count > 1`. The floor grades the BOTTOM of the range and
nothing else, so when the live value sits exactly at the floor, narrowing the producer at
its USE SITE satisfies the floor and deletes arms in silence. The run stays green and the
arm count drops.

**WHY A FLOOR MET EXACTLY IS AN INVITATION.** `MINIMUM_LIFTED_SUBSET_SENTENCES` was 3 and
the derivation yielded 8. Appending `[:3]` to the producer's return left the floor
satisfied and dropped five of eight plants. `[:2]` died. So the floor was the ONLY thing
holding it, and it held exactly one point of a range it was supposed to cover.

**THE FOUR INSTANCES, all inside CS-929, each found by an adversary AFTER the previous one
was repaired.** This is the part that makes it a class rather than a bug.

1. `POPULATION_ROOT_RELATIVE` narrowed from `clockspeed` to `clockspeed/surface`: 28 of 49
   files dropped out, all 155 arms green.
2. The ANCHOR introduced to pin that root: `SHIPPING_PACKAGE_ANCHOR` repointed, 452 arms
   green. The repair had moved the knob up one level rather than removing it.
3. That anchor's USE SITE: `SHIPPING_PACKAGE_ANCHOR + "/surface"` - reachable by string
   concatenation even though the anchor itself was now derived from the import system. A
   derived value does not protect its own use.
4. The plant PRODUCER's return: `_lifted(...)[:3]`, 476 arms to 466, exit 0. Ten arms gone
   in silence.

**WHAT ACTUALLY KILLED INSTANCES 1 THROUGH 3, and it is the fix to generalize.** Set
EQUALITY between the swept corpus and a second corpus walked by separately spelled rules.
Not a superset, not one-file-per-package: equality, reported as the symmetric difference.
No config change at any level can then shrink the corpus unless both derivations are wrong
the SAME way. Measured: the only shared symbol between the two walks is `REPO_ROOT`, which
is a single path, so an edit to it can only EMPTY both sides - and mutual emptiness is
killed by three independent arm families. **Two derivations that read the same knob are
one derivation wearing two hats**, so the second must not import the first's constants.

**THE CHEAP BACKSTOP THAT WOULD HAVE CAUGHT ALL FOUR.** Every instance was a silent
arm-count drop. A module that asserts its OWN collected arm count against an
independently derived expectation catches the whole class at once, including instances
nobody has thought of yet. It must be DERIVED rather than written, or it is simply knob
number five.

**WHERE ELSE TO LOOK, and this is the item's real scope.** CS-929's guard is one module.
Any arm parametrized over a derived population has this shape, and this project has many:
the vocabulary sweeps, the census modules, the citation tables, the exemption records.
`tools/drift_guard.py` already had to repair a version of it once - a vocabulary spelled as
data and never swept is one whose members can be deleted one at a time with the suite
staying green.

**DO NOT close this by pinning floors.** A floor is the defect. The two mechanisms that
work are equality against an independent derivation, and an asserted arm count. Anything
that grades only the bottom of a range reproduces the class at the next level out, which
this item measured four times before it was filed.

**RELATED, and distinct.** A pooled threshold summed over a population is met by its
strongest member while the weakest goes unmeasured - that is the same family one step
sideways, and the acceptance clause here should not be read as covering it.


### MEASURED 2026-09-12 (session 88) - the scope was REFUTED seven of eight, and the scoping document reproduced the defect class, which is instance FIVE

**NOTHING WAS IMPLEMENTED THIS SESSION AND THAT IS THE FINDING.** A scoping sweep was
commissioned to decide HOW WIDE to go before any code moved. An adversary with a
correctness-of-the-cut lens then refuted SEVEN of its EIGHT claims. The scope is NOT safe
to implement as written and no repair was built on it.

**THE INSTANCE THAT MATTERS, AND IT IS THIS ITEM'S OWN SHAPE ONE LEVEL OUT.** The document
proposed a SHARED arm-count backstop for eleven modules and argued it was safe because the
backstop "has no root, no prefix, no suffix and no width in it to narrow". Two bullets
later it mandated a PER-MODULE MAP OF INDEPENDENTLY-COUNTED ARGNAMES. **That map is a
shared width knob.** Delete one argname entry and that module's expectation falls in step
with its collected count, silently, eleven modules deep. The document anticipated a
sentinel-and-skip single point of failure and did NOT anticipate this one.

So the pattern recorded in the FILED section - each repair creating the next instance one
level out - now has a fifth instance, and it is the first found in an ANALYSIS rather than
in a repair. Recorded because it changes what this item has to defend against: the class
reaches prose about the class.

**WHAT SURVIVED THE PASS.** The eleven arm counts were re-measured exact this run: 856,
484, 341, 245, 135, 134, 100, 79, 70, 64, 54. The shortlist MEMBERSHIP is undisturbed -
eight sites the sweep missed were found, none at band-A severity. And the ruling
**NEVER SHARE THE SECOND DERIVATION** survives intact; it is only the shared-backstop half
that fell.

**WHAT WAS REFUTED, so none of it is rebuilt from the scoping document as written.**

- **THE FREE SECOND DERIVATION IS THE TRAP, NOT A WIN.** The document claimed FOUR modules
  spell an identical tree-enumeration argv and are therefore a second derivation already
  paid for. Only THREE do; the enumeration in `tests/liveness.py` spells a different command and the
  document contradicts itself one sentence later. The three that match are byte-identical
  copy-paste with near-identical docstrings - **one derivation wearing three hats**, and a
  single search-and-replace of the pathspec keeps an equality between them green. This is
  precisely the "two derivations reading the same knob are one derivation" trap this item
  was filed to name.
- **THE PROPOSED SECOND DERIVATION WOULD BE FALSE-RED BY CONSTRUCTION.** Measured: rglob
  214, git 207, walk-only 7, git-only 0. The document's population of 197 is its own
  `data/` component prune - the very trap it documents elsewhere - and the symmetric
  difference against git is 24, covering all of `clockspeed/data/` and `tests/data/`. The
  correct prune yields 207 exactly.
- **THREE OF THE SIX BAND-A SITES DO NOT BELONG THERE.** Their stated one-line narrowings
  would REDDEN an existing guard rather than pass it: one kills the `OWNER` literal that
  `test_the_owner_still_reads_the_field_so_the_fence_is_not_vacuous` reads, one kills
  every `EXEMPT` key that `test_every_exemption_names_a_file_git_actually_tracks` walks, one takes
  all four `SPAWN_ROOTS` to zero and reddens
  `test_every_spawn_root_is_reached_by_the_walk`, and one is filtered by
  `repr_rendering_guard.scan_tree` on `SHIPPED_ROOT` so the narrowing trips three named
  literals. A
  site whose guard already reddens is not an instance of this class.
- **THE CUT CRITERION IS NOT DECIDABLE AS WRITTEN.** Its criterion (2) - a silent drop
  makes a real defect class go unmeasured - is a judgement the author made and then
  described as a criterion; the document concedes in its own words that every severity in
  it "is an argument, not a measurement". And the three tests are CONJUNCTIVE, which
  excludes at least one site that fails only the filesystem-derived test while passing the
  other two badly: `DATA_MODULES` in `tests/data/test_phase2_gate.py`, whose sibling phase3
  and phase4 gates the document itself names as the in-repo template because they already
  carry the disk-equality arm phase2 lacks.

**ONE SIDE CLAIM IS LATENT RATHER THAN LIVE.** Two enumerations missing `--others` cannot
see untracked files, and the citations reproduce - but measured this run, `git ls-files
"*.py"` and the `--others` form both return 207, so there is no untracked `.py` for it to
miss today. Latent, and worth fixing on its own terms, not as evidence for this item.

**WHERE THIS LEAVES THE ITEM.** OPEN, and the acceptance is unchanged. What the next
attempt must NOT do: adopt the six-site band as given, adopt the shared backstop as
specified, or treat the identical-argv modules as an independent second derivation. What
it may keep: the arm counts, the shortlist membership, and the never-share-the-second-
derivation ruling. **The fence from the FILED section still holds and now has a fifth
witness - do not close this by pinning a floor, and check whatever you build for the knob
you just introduced.**


### MEASURED 2026-09-12 (session 88) - the cut line reworked BY MEASUREMENT, and the criterion is the only part that survived a second adversary

**THE CUT CRITERION IS SETTLED AND IS THE DELIVERABLE. THE BAND IS NOT, AND THE BACKSTOP
IS NOT.** Three successive analyses contradicted each other on this item in one session -
a scope, its refutation, and a measured rework - and an independent adversary then refuted
three of the rework's six claims. What converged is the CRITERION. Anyone continuing this
item adopts the criterion and re-derives everything else.

**THE CRITERION, and the reason it replaced the old one.** Version 1 ranked sites by an
argued severity and conceded in its own words that "every severity above is an argument,
not a measurement". That is why it lost. The replacement is mechanical and carries no
judgement call:

> A site is an instance of CS-988 if and only if, MEASURED ON DISK: a plausible one-line
> use-site narrowing of its knob REDUCES the collected arm count, AND the guard population
> that could object stays GREEN with the narrowing in place. If anything reddens, the site
> is already defended and is NOT an instance, however bad it looks by argument.

**THE OLD CRITERION SELECTED AGAINST THE REAL INSTANCES, WHICH IS WORSE THAN RANKING THEM
WRONG.** Measured across 23 sites by on-disk mutation in 29 runs: **all six of version 1's
band-A sites are DEFENDED**, not the three its refutation caught - the refutation was
itself wrong twice, and the objectors it missed are named in the rework. Band A was
selected by "the population is derived from the filesystem or the git index", and that
turns out to be the best-defended set in the repo, because a filesystem-derived population
is exactly the kind someone already thought to guard. **Every instance found was BELOW the
old cut line.**

**FOUR INSTANCES ARE CONFIRMED BY BOTH THE REWORK AND ITS ADVERSARY**, each verified to
exist at its cited site with its delta matching today's collection:
`DOCUMENTED_PATHS` in `tests/test_architecture_attributions.py` (-54 arms),
`DATA_MODULES` in `tests/data/test_phase2_gate.py` (-6 and -5, two independent
narrowings), `CLOCKSPEED_PACKAGES` in `tests/test_scaffold.py` (-9), and `LEVEL_KEYS` in
`tests/test_tier1_budget.py` (-2). All four names are module-local with zero external grep
hits, so no external objector exists for any of them. Three further sites are green with
ZERO arm drop - silent at runtime - and are deliberately kept OUT of the band rather than
counted.

**BUT FOUR IS A SAMPLE, NOT A BAND, AND THE REWORK OVERSTATED THIS.** An AST scan finds
368 parametrize sites, of which 48 are over module-level all-constant sequences across 36
distinct file-and-name pairs. Four measured instances out of roughly 36 candidates is a
sample. **Do not adopt "the corrected band" as a closed set.** Fifteen band-B rows were
correctly reported UNMEASURED rather than classified, and that conduct is right and should
continue - an unmeasured site classified by argument is the original defect.

**THE PRISTINE FLOOR DOES NOT UNDERWRITE THE REDS, AND THIS BOUNDS EVERY VERDICT ABOVE.**
The rework established a floor of 21 modules and 2125 arms before mutating, offered as
proof that every RED was a real objection. The floor is a STRICT SUBSET of the guard
populations actually exercised: one site's unmutated guard set is 22 modules and 1688
arms, another's is a disjoint 12 modules and 1349 arms, and the union lower bound is 33
modules and 2696 arms. A floor cannot license a conclusion about a mutation whose blast
radius falls outside it. Two of the four instances were graded against a guard set of ONE
module and should have included `tests/test_docs_citations.py`, `tests/liveness.py` and
`tests/test_liveness.py`. **The four instances stand; the confidence attached to them does
not.**

**THE BACKSTOP: THE SHARED-KNOB CHARGE IS ANSWERED, AND A WORSE ONE REPLACED IT.**
Measured, and this settles the version-1 dispute: a per-argname map IS a silent knob
wherever it lives - deleting one entry gives 1347 passed, exit 0, and zero arm change - so
the helper must take the expectation as an ARGUMENT and stay module-local, bounding the
blast radius to one module per edit. **"Expectation as an argument" was checked for being
the displaced knob one level out and it is NOT.** That question is closed.

What replaced it is sharper and is about code already shipped. `_declared_case_count` in
`tests/surface/test_aggregate_count_prose.py` computes
`total *= independent() if independent else len(list(argvalues))` - and `argvalues` is THE
SAME OBJECT being parametrized over. So where no independent re-derivation is supplied,
the expectation follows the population down. Observed by calling the shipped helper:
expected 4 unsliced, expected 2 after slicing `LEVEL_KEYS` to one, collected also 2,
**GREEN**. **The claim that a backstop alone suffices and needs no second derivation is
FALSE against shipped code**, and it is false in the one module this item has already
repaired. All four instances need a genuine second derivation; a map entry whose value is
not an independent re-derivation buys nothing.

**A HARNESS HAZARD THAT WOULD HAVE SHIPPED A FALSE RED, and it is the most transferable
finding here.** The walk-versus-git population is CHECKOUT-DEPENDENT. `.gitignore` line
282 ignores `/moon_sync_inbox/`, which exists in the primary checkout and in no worktree.
Measured in the primary checkout: git 207, rglob 214, walk-only 7, git-only 0, symmetric
difference 7; under a `data/` component prune, walk-only 7 and git-only 17 for a difference
of 24. Measured in a worktree: 207, 207, difference 0. All three passes reconcile once the
mechanism is known. **An equality arm developed in a worktree calibrates GREEN and ships a
FALSE RED to the primary checkout** - and because it depends on ignored content that comes
and goes, the false red is NON-DETERMINISTIC there and reads as a flake. Any equality-based
arm this item produces must be developed or at minimum re-measured in the primary checkout.

**THE ORDER OF WORK, from the adversary's recommendation and adopted here.** Adopt the
CRITERION - it is mechanical and unaffected by the unmeasured sites. Do NOT adopt the band.
**Repair the backstop FIRST**, because every instance depends on it and it is currently
vacuous wherever no independent re-derivation is passed. Then finish the sweep over the 15
named band-B rows plus the roughly 36-pair literal population, using the criterion.

**THE ITEM STAYS OPEN.** Nothing was built this session. The fence holds and is unchanged:
do not close this by pinning a floor.


### MEASURED 2026-09-13 (session 89) - the criterion swept over the whole 193-pair population, and SEVENTEEN instances are confirmed against a derived guard set

**THE BAND IS NO LONGER A SAMPLE OF FOUR.** The criterion was applied on disk to
every one of the 193 file-and-name pairs, re-derived here by an independent AST scan
that returned 193 pairs across 49 files. Leg 1 mutated each knob and compared
collect-only counts: 93 reduced the arm count, 43 did not, 48 could not be sliced at
all, 9 were the deferred module. Leg 2 then ran each of the 93 against an objector
set derived per candidate. **Seventeen sites are green end to end and are instances.
Thirty-two are DEFENDED. Forty-four are INDETERMINATE because the sweep ran out of
wall clock before their second phase, and they are left unranked rather than argued
into a band.**

**THE FOUR ON FILE ALL REPRODUCE, AND THE TWO DERIVED ONES RECONCILE AT AN OFFSET OF
EXACTLY ONE.** `DATA_MODULES` -6 and `LEVEL_KEYS` -2 land on the nose. The two DERIVED
knobs come out at -55 and -10 under a ONE-element truncation, against -54 and -9 on
file; under a TWO-element truncation they are -54 and -9 exactly. Measured, not
inferred - `[:2]` was run on both. **So the narrowing the prior pass applied to a
derived knob kept two members, and the record did not say so.** Neither population has
drifted: `tests/test_scaffold.py` has two commits in its entire history. The operator
this sweep used is therefore shape-directed and the split is forced by calibration,
not chosen for convenience: a literal display loses its last member, a derived
population is truncated.

**THE GUARD POPULATION MUST BE MEASURED, AND THE OBVIOUS GREP GETS IT BACKWARDS.** A
regex for a python-file enumeration plus a tests root nominated eleven modules as
all-source readers. An audit hook on `open` says six of them read nine files or fewer
- `tests/save/test_phase4_gate.py` opens FIVE - while three modules the regex never
nominated open all 143. Grading against the regex set cost 250 seconds per candidate
and spent most of it on modules that cannot see the mutation at all. The eight
measured readers are `test_liveness`, `test_docs_citations`, `test_toolpath`,
`save/test_absolute_claims`, `save/test_oracle_citations`, `test_chained_cause_census`,
`test_tier1_budget` and `test_scaffold`.

**EVERY DEFENDED VERDICT WAS SETTLED BY THE CANDIDATE'S OWN MODULE - ALL 32, WITH ZERO
EXTERNAL REDDENING NODES.** That is the cost lever for anyone continuing: run the own
module first and the expensive readers only for what survives. It is also a warning
against the opposite reading - it does NOT license dropping the readers, because a
green needs them and a red never did.

**THE BACKSTOP GRADES NONE OF THE SEVENTEEN.** `_declared_case_count` lives in
`tests/surface/test_aggregate_count_prose.py` and a repo-wide grep finds no other
module importing it. Six of the seventeen instance modules do carry an equality or
symmetric-difference arm somewhere in the file, but none of those arms is wired to the
knob that moved, and the run proves it rather than arguing it: a second derivation of
that population would have reddened, and none did. **So for all seventeen the answer
to "second derivation or backstop count" is neither.**

**WHAT THE SEVENTEEN ARE.** `DOCUMENTED_PATHS` -55, `MEASURED_PAIRS` -36,
`WITNESS_ROWS` -32, `TOPOLOGY` -31, `TOKENS` -17, `SAVE_MODULES` -12, `HOOK_NAMES` -10,
`CLOCKSPEED_PACKAGES` -10, `SOLVE_MODULES` -7, `DATA_MODULES` -6, `_INJECTIONS` -6,
`_FAILURE_PARAMS` -5, `_TRUNCATIONS` -4, `_FORCED_DISCOVERY_FAILURES` -4,
`_SOURCE_FILES` -4, `ATTRIBUTED_TOKENS` -4, `HEADER_VERSIONS` -3. Four of the seventeen
sit in `tests/test_architecture_attributions.py`, which is the densest single module
in the population and carries no arm-count assertion of any kind.

**EVERY LEG-2 VERDICT HERE CARRIES THE RE-MEASURE-IN-PRIMARY FLAG, GREEN AND RED
ALIKE.** No instance's arm COUNT depends on a filesystem or git walk, so the deltas are
checkout-independent and stand as measured. The guard set is not: it includes
`tests/test_liveness.py` and `tests/test_docs_citations.py`, both of which enumerate
the tree, and a worktree carries no `moon_sync_inbox/`.

**WHAT IS UNMEASURED, STATED AS UNMEASURED.** The 48 pairs whose knob is a Mapping, a
frozenset, a Fraction or an int - the slice raises at import, so the operator has
nothing to say about them and neither does this pass. The 9 pairs in the deferred
module. The 44 INDETERMINATE rows. The `-5` second `DATA_MODULES` narrowing, which is
arithmetic over six measured use sites rather than a run of its own. None of these is
ranked, banded or called likely-anything.

**THREE DEFENDED VERDICTS REST ON A FLOOR, WHICH IS THE SHAPE THIS ITEM'S FENCE
FORBIDS RELYING ON.** `_DEFERRED_SHAPES` is held by
`test_the_over_and_under_report_rows_are_both_populated`, and `_CLEAN_REFUSALS`,
`_CLEARED_SHAPES` and `_LIMIT_TEN_ESCAPES` by
`test_neither_refusal_population_is_empty_and_together_they_are_the_table`. Each of
those knobs is two or three members deep, so dropping one member empties a row and
trips the floor. **A DEFENDED verdict of that shape is defended by arithmetic, not by
design** - the same guard over a five-member population would pass the narrowing in
silence. They are correctly DEFENDED under the criterion and should NOT be counted as
evidence that a floor works.

**THE PER-SITE DATA IS IN `docs/item_notes/cs988-sweep-record.md`** - every instance with its delta and guard set, every DEFENDED verdict with the node id that reddened, and the 44 INDETERMINATE rows listed unranked. That annex is where the next pass starts; do not re-derive the population.

## CS-1051

### Filed 2026-09-14

**FOUND WHILE MERGING CS-1039, AND THE WAY IT WAS FOUND IS THE POINT.** CS-1039 retypes
`UnlockState.current_game_phase` from `int | None` to `str | None`, because the value is an
asset reference. `clockspeed/surface/api/world.py::_unlocks` publishes that field VERBATIM, so the
wire changed type. The surface suite stayed GREEN at 1478 passed. It did not notice, and it
could not have: `tests/surface/audit_harness.py::SYNTHETIC_UNLOCKS` hand-builds the published dict and
hardcodes `"current_game_phase": 2`, an integer, while `tests/surface/test_world.py`
asserts only that the KEY is present.

**SO THE HARNESS IS NOW A FIXTURE THAT CONTRADICTS THE MODEL IT STANDS IN FOR, AND NOTHING
GRADES THE CONTRADICTION.** A green surface suite is currently a statement about the
harness, not about the wire. This is the oracle-blind-to-its-subject class: the arm cannot
observe the value it names, so it passes for that reason alone.

**WHY THIS IS TIER 1 RATHER THAN A TIDY-UP.** The defect is not the one wrong value. It is
that ANY retype in `save/` can change the wire with the whole surface suite green, and the
dashboard is the consumer. The next retype gets no warning either.

**THE ACCEPTANCE MUST NOT BE MET BY RE-TYPING THE LITERAL.** Changing `2` to a string makes
today's arms pass and rebuilds the same blindness one edit later. The published type has to
be derived from `UnlockState`'s own annotation so the two sides share no constant, and the
key sets compared in BOTH directions so a field added to one alone is caught. A one-sided
subset is the floor shape this repo has measured leaking repeatedly.

**TWO DOCSTRINGS ON A PRIVACY INVARIANT ARE NOW FALSE AND THIS ITEM OWNS THEM.**
`clockspeed/surface/api/world.py` states at two places that it is "the ONE place a
`type_path` crosses the wire" and calls it "THE ONE DELIBERATE ASYMMETRY". CS-1039 makes a
second path cross, so both sentences are false. A doc that lies ON a privacy invariant is
worse than one that lies about a count: the next reader checking whether a new field may be
published will read it and get the wrong answer.

**DO NOT WIDEN CS-1039 TO COVER THIS.** `clockspeed/surface/` is not on its write-list, the
candidate is frozen, and the wire-shape question it raises is separately adjudicated. One
owner per item.

**RELATED MEASUREMENT, WORTH MORE THAN THIS ITEM.** During CS-1039's first cut the WHOLE
suite ran green - 3153 passed - while `UNLOCK_CARRIERS` was keyed on C++ declaring class
names that match ZERO records on every real save. No arm anywhere saw it. The two arms
added in the re-work, the ADR-table control and the declaring-class arm, are what close
that hole, and neither existed when the suite went green. A green suite is evidence about
what the suite can see.

## CS-1046

### Filed 2026-09-13

**TWO PUBLISHED DOORS THAT REFUSE, AND A PATTERN THAT CANNOT NAME A MODERN ITEM.**
`/api/plan` and `/api/audit` are published in the endpoint table and answer 501 blocked by
CS-500 while the layers beneath them now exist. Separately `contract.BLOCKER_PATTERN` admits
`CS-` followed by exactly three digits, applied with `fullmatch`, so no item at CS-1000 or
above could ever be named by a 501 even if one were needed.

**WRITE-LIST:** `clockspeed/surface/api/contract.py`, `.../plan.py`, `.../audit.py`,
`.../pending.py`, `.../routes.py`, `clockspeed/surface/providers.py`, and the six matching
surface test modules. **DEPENDS ON:** CS-1041, CS-1042, CS-1043, CS-1044, CS-1045.
**TIER 2, NO GAME NEEDED.** **PUBLISHES:** two backed routes, a concrete `SchematicSource`,
and a CHEAP world-change token on the audit body for the liveness poll to read.

**IT DOES NOT WRITE `health.py`, AND THAT IS WHY THE TWO EXISTING UNBACKED TEMPLATES ARE
REUSED RATHER THAN NEW ONES INVENTED.** No template is added or removed, so the endpoint
table is untouched and the page's route array stays equal to it in order. A new template
would force simultaneous edits to `health.py`, `routes.py`, `pending.py` AND `app.js`,
merging this item and the render item into one unslicable blob.

**`tests/surface/audit_harness.py` IS NOT IN THE WRITE-LIST.** CS-1031 is already open
against it; if it must change, that is a separate item routed to an adjudicator.

**ADDING AN `OPEN_BLOCKERS` MEMBER REQUIRES A PUBLISHED ROUTE TO NAME IT.** The converse arm
measured that a member no endpoint cited was green. This item widens the PATTERN and adds a
member only if it also publishes the route naming it, in the same change.

**`surface/` NEVER COMPUTES.** Every number a body carries is computed in `audit/`,
`progress/` or `solve/` and transcribed here. The withheld list stands: no instance name, no
record index, no byte offset and no path crosses the wire. Uniform refusals - no world is a
503 with the no-save reason, no registry is a 200 with a named warning rather than a
refusal, and an unknown parameter is a 400 reflecting NOTHING of what it refused.

## CS-1047

### Filed 2026-09-13

**WHY THIS IS ONE ITEM AND NOT TWO.** `server.py`'s static route table, `index.html`'s
script tags and the asset-existence arms in `tests/surface/test_web_assets.py` are a
three-way total-set guard: a new panel file must appear in all three at once or the suite is
red. Splitting the render would put the same three files in two write-lists, which is a
merge conflict already.

**DEPENDS ON:** CS-1046 for the bodies, CS-1061 for the underlay, and CS-1048 for the annotation
provenance. **TIER 2, NO GAME NEEDED** - canned bodies bound to the endpoints' own key
tuples.

**THE ORACLE LIMIT IS RECORDED, NOT ASSUMED AWAY.** CS-1032 is open: the DOM stand-in has no
known-good browser control anywhere in this repo, so "the map renders X" is a claim about
the stand-in. Every acceptance clause must be expressible in the stand-in's vocabulary or it
grades nothing, and the adjudicator's verdict must ENUMERATE the stand-in's divergences.
This project has already recorded browser-pane resize, focus and default key scrolling as
silently faked, with three false findings out of one session that trusted them. **ASSUMED,
NOT MEASURED:** that the stand-in can observe a per-category `class` attribute set at
creation. Check that BEFORE writing the acceptance.

**EVERY NEW PANEL IS IIFE-WRAPPED.** Three existing panels are not and CS-1026 is open over
exactly that; a new unwrapped panel would be a fourth instance of an open defect.
**NOTHING IN A PANEL DIVIDES** - CS-962, CS-1027 and CS-1028 are open over the division
detectors and over four ungraded `approximateDecimal` copies. Import the graded one or add
none.

**CS-1022 IS OPEN AGAINST THIS ITEM'S OWN FIXTURE.** `tests/surface/test_panel_map.py`'s
canned body claims to be the frozen contract shape while binding to neither the placement
key tuple nor the data key tuple. Binding it discharges CS-1022 incidentally; adding more
unbound canned keys makes it worse. The item must SAY which it did.

**THE CSP CHANGE IS ASSERTED, NOT MERELY TYPED.** `img-src 'self'` is added to the
`server.py` policy and graded by an arm. No absolute URL enters a shipped asset.

**THE UNDERLAY IS NEVER REGISTERED AGAINST `WorldBounds`.** That box bounds THIS world's
placements and moves every time the operator builds anything, so a transform fitted to it
drifts under the operator's own hands. Registration is CS-1061's declared config origin and
scale, carried through and labelled ESTIMATED on the page.

**NODES RENDER SHAPE-CODED BY CLASS AND UNLABELLED.** Purity is not derivable and is never
guessed; where the page shows one it shows an operator annotation and says so on the row.

---

## CS-1065

### NOTE - filed 2026-09-14 under CS-301

`within_estimate` is a TRI-STATE and the null is load-bearing: None means there was no independent
second source to check against, which is the struct-range shape, where the declaration and the
estimate are the same two numbers. Collapsing it to a boolean at the wire edge turns "nothing to
check" into "checked and failed", and the dashboard has no way to tell those apart afterwards. The
refusal vocabulary ADR 0012 fixed is where the wire form for this belongs; read it before choosing a
spelling.
