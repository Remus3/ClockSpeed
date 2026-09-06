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
