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
