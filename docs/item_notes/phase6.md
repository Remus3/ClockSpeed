# Clockspeed - live per-item detail, phase 6 - surfaces

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the leaf membership rule routing every OPEN item, the verbatim
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

### Acceptance

the spellings are derived from what the running platform can actually produce, or the collapse is recorded at the point of use so a reader of a green run knows what went unmeasured


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

### Acceptance

a gutted suite reddens, proven by an arm that stubs the suites and fails, with the expected count derived from a recorded per-suite declaration rather than a literal that drifts


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

### Acceptance

the session-scope question is settled against a running Electron and the three statements reconciled, or the claim is withdrawn from all three places and recorded as unverifiable in the detail


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

### Acceptance

no fault string can quote file content, proven by a planted canary arm that reddens when the redaction is removed, matching the closed-vocabulary idiom `clockspeed/surface/config.py` states


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

### Acceptance

the gap is closed for whichever parts are pure, and what remains is recorded in a work-item file rather than only in a CI comment, with ADR 0014 no longer framing the ungraded set as display-bound


## CS-872

### Relocated from `ROADMAP.md` 2026-09-01

The composed page opens with no default keyboard scrolling, because a NON-ROOT SCROLLER
is not the default scroll target.

**WHY THIS NEEDS A REAL ELECTRON RUN TO GRADE.** The acceptance asks for a cold key press
to scroll the composed page with the band still covering no content. The band is a DRAG
REGION THE OS DRAWS OUTSIDE THE WEB CONTENTS, so no headless or in-page harness can
observe both halves of that condition at once - the scroll is observable in the web
contents and the band is not. Grading it means running the shell.

### Acceptance

a cold key press scrolls the composed page with the band still covering no content, graded by a REAL ELECTRON RUN and not by a static arm


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

### Acceptance

no argparse usage error exits a code the runbook documents as a specific refusal, with the codes DERIVED from the two modules' own declarations rather than restated, proven by an arm that goes RED when a usage error and a documented refusal share a code


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

### Acceptance

one double-click of a generated shortcut opens the companion against a live dashboard whether or not one was already running, and leaves a tray presence where closing the window HIDES it and Quit stops only the dashboard that launch itself started, with the spawn, adopt and stop-what-you-started decisions graded by `node --test` and the tray, the hide and the shortcut graded by a REAL ELECTRON RUN from a real shortcut rather than by a static arm


## CS-1435

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-058. Class: product. Lane flag: false (not eligible: U-058.2 edits the hub file shell/main.js; clause 12 is an operator observation). Planned minutes: 300 (3 parts (U-058.1 120, U-058.2 120, U-058.3 60)).
Depends on: CS-1440 part 1 (U-131.1); CS-1440 part 3 (U-131.3); CS-619.1.
Wave: W5, W6 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-058.2 in W6: `shell/main.js` 1/2.
Write-list:
- U-058.1 (W5-G2-S1, 120 min): `scripts/` `make_icon`, `tests/` `test-make_icon`, `shell/lib/` `identity`, `shell/test/` `identity.test`
- U-058.2 (W6-G1-S1, 120 min): `shell/lib/window.js`, `shell/test/window.test.js`, `shell/main.js`, `tests/shell/test_shell_assets.py`, `shell/lib/endpoint.js`, `shell/test/endpoint.test.js`
- U-058.3 (W6-G2-S1, 60 min): `docs/adr/0015-the-shell-may-start-the-surface.md`

### Acceptance

Fixed values: sizes 16, 20, 24, 32, 40, 48, 64 (32-bit BGRA DIB entries) and 256 (PNG entry); face `2f7fd0`, hands `f5f7f9`; file name `clockspeed.ico`; clone default `<repo>/data/icons/clockspeed.ico`, with a data root `<root>/data/icons/clockspeed.ico`; `APP_USER_MODEL_ID = "Clockspeed.Companion"`; `ICON_RELATIVE = ["data", "icons", "clockspeed.ico"]`.
Fixed geometry, on a 32-unit grid scaled by size / 32: the disc is centred at (16, 16) with radius 15; the long hand is the rectangle x 14 to 18, y 4 to 18; the short hand is x 14 to 25, y 14 to 18 (at 32 px: pixel columns 14-17 by rows 4-17, and columns 14-24 by rows 14-17). Each pixel takes 16 subsamples (4 x 4, at the odd eighths of the pixel) and counts n, those inside the disc. At 32 px alpha is 255 when n is 8 or more and 0 otherwise, and a pixel is hands or face whole. At every other size alpha is `(n * 255 + 8) // 16` and the colour is the integer blend of face and hands by the hand subsample count, stored unpremultiplied. "Opaque" means alpha 255; a pixel with alpha 1 to 254 is an edge pixel.
1. `test-the_output_parses_as_an_ico_with_exactly_the_eight_declared_sizes` in `tests/` test-make_icon.py - header reserved 0, type 1, count 8; the size set is exactly the eight values; every entry's offset and length lie inside the file and no two overlap; the 256 entry opens with the PNG signature, every other entry with a 40-byte bitmap header declaring 32 bits.
2. `test-the_32_px_entry_is_two_opaque_colours_and_full_transparency` (every alpha is 0 or 255; exactly 632 face, 84 hands and 308 clear pixels, the counts decoded from the embedded picture); `test-every_other_size_holds_only_blends_of_the_two_colours_and_clear_corners` (each opaque pixel lies on the straight blend between face and hands; every edge pixel carries the face colour exactly and its centre lies within 1 px of the disc's circle; the four corner pixels have alpha 0); `test-the_face_colour_clears_three_to_one_on_black_and_on_white` (computed on the unblended face colour).
3. `test-the_32_px_entry_equals_the_embedded_tray_png_pixel_for_pixel` - the test reads the base64 lines out of shell/lib/tray.js text and decodes them itself. `test-every_other_size_matches_the_declared_geometry` - opaque-pixel centroid within 0.5 px of the centre, disc radius within 1 px of size x 15 / 32, long-hand pixels above the centre, short-hand pixels right of it. Fallback, only if exact reproduction fails: the same geometric test at 32 px plus at most 4 percent of pixels differing, and the ledger record says the fallback was taken.
4. `test-two_runs_are_byte_identical` (same process, two calls, and two subprocess runs).
5. `test-the_file_is_published_atomically` - written to a temp name in the target directory then `os.replace`; a replace that raises leaves no file at the target and no temp file. `test-the_default_path_follows_the_data_root` - `default_out_path()` is `<repo>/data/icons/clockspeed.ico` when `locate.data_root()` is None and `<root>/data/icons/clockspeed.ico` when it is set; `--out` beats both. NEGATIVE `test-a_failed_write_names_the_flag_and_never_the_path` - exit 1, one fixed line, no path text (assert on booleans). NEGATIVE `test-a_malformed_data_root_is_refused_without_echoing_it` - with `locate.data_root()` raising `DataRootError` (U-131.1) and no `--out`, exit 1, one fixed line naming the variable, no fragment of its value, and no file written.
6. shell/test/identity.test.js: "APP_USER_MODEL_ID is Clockspeed.Companion, by value"; "ICON_RELATIVE is spelled out by value"; "iconPath joins the data root when one is given and the repo root otherwise"; NEGATIVE "iconPath refuses a relative or empty base and quotes nothing" (throws `IdentityError`); "identity.js exports no relaunch property and requires only node:path"; the two ASCII and no-carriage-return arms every shell module carries.
7. shell/test/window.test.js: "icon is overridable and lands only as a non-empty absolute path" - `OVERRIDABLE_KEYS` includes `icon`; an absolute string lands as `options.icon`; absent, empty, non-string and relative values leave no `icon` key. The existing arm at :190 gains `icon`.
8. tests/shell/test_shell_assets.py: `REQUIRED_MAIN_WIRING` gains `require("./lib/identity.js")`, `identity.iconPath(`, `endpoint.dataRoot(` and `nativeImage.createFromPath(` (`WIRING_TABLE_SIZE` +4); `MAIN_MODULE_BINDINGS` gains `("identity", 'const identity = require("./lib/identity.js");')` (`MODULE_BINDING_COUNT` +1); `REQUIRED_NAMES` gains shell/lib/identity.js and shell/test/identity.test.js. shell/test/endpoint.test.js: "dataRoot answers null when the variable is unset or blank and the declared drive path otherwise"; NEGATIVE "dataRoot refuses a malformed root with the named fault and never echoes it" (`EndpointError` carrying U-131.3's `DATA_ROOT_SHAPE`; assert on booleans). `dataRoot(env)` reads `DATA_ROOT_ENV` through the same shape check `certDir` uses after U-131.3: one reader, no second rule. NEGATIVE, by command: `git grep -c "CLOCKSPEED_DATA_ROOT" -- shell/main.js shell/lib/identity.js` prints nothing.
9. NEW `test-the_tray_keeps_the_embedded_picture_as_its_fallback` - main.js code holds `nativeImage.createFromPath(` and `nativeImage.createFromDataURL(trayLib.ICON_DATA_URL)`, exactly one `new Tray(`, and the `isEmpty()` refusal still guards the image handed to it. NEGATIVE NEW `test-main_does_not_set_the_app_user_model_id` - zero code occurrences of `setAppUserModelId(`. U-061.2 must remove or invert this arm in the change that adds the process call and both links; U-061's spec does not name the arm yet (reported to the merger), so the U-061.2 brief names it.
10. `git ls-files data/icons` prints nothing and git check-ignore -q data/icons/clockspeed.ico exits 0; the byte arms of tests/shell/test_shell_assets.py stay green (no shell byte above 0x7E).
11. docs/adr/0015-the-shell-may-start-the-surface.md gains one section `## Addendum - filed <date>: the companion as a desktop app` (`grep -c "^## Addendum" <file>` prints 1; the heading is generic because D63 puts start with Windows, U-063, in the same addendum) recording: the icon may be a generated, untracked file resolved through the data-root resolver; the ASCII data URL stays as the fallback; no tracked binary and tracked shell bytes stay ASCII; `Clockspeed.Companion` is published in shell/lib/identity.js and set by no code in this item.
12. docs/OPERATIONS.md 8.4 names `python scripts/make_icon.py` as the step before the shortcut; 8.5 gains one check "The window, the taskbar button, Alt-Tab and the tray show the clock glyph" whose shipped line is `Observed: NOT RUN`. It is appended after the six checks at HEAD (docs/OPERATIONS.md lines 769-798) under one sentence saying checks 1 to 6 alone grade CS-909 (D87 closes CS-909 on those six) and the later ones grade the rows that added them; the merger assigns its number at landing, because sibling units append 8.5 checks too. The row closes only when that line carries a dated observation (operator act, batched into the one ask); the parts land without it.

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

### Acceptance

the four frozen sites carry an adjudicator grant recorded in `docs/LEDGER.md` before any edit, every remaining INDIRECT delegation is graded by a runtime arm that observes the argv actually built rather than a counted subset of it, and the 31 ungraded findings under `tests/` are either routed or exempted with a stated reason


## CS-604

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`docs/OPERATIONS.md` restates the base port and the band that `config/ports.json` owns, and the file is absent from `tools/doc_budget.py`'s measured population so neither fault is caught

### Acceptance

no tracked file outside `config/ports.json` spells a port number in the allocated band, proven by a guard that reads the band FROM the record rather than from a literal, and the file is either budgeted or recorded as deliberately unbudgeted


## CS-606

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`clockspeed/surface/__main__.py`'s success path is unexercised because it installs a process-wide SIGINT handler that would replace pytest's, so only its refusal branches are graded

### Acceptance

the serve-and-shut-down path is driven end to end in a subprocess and its exit code read, or the gap is recorded with the reason


## CS-607

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`tests/test_mypy_gate.py::test_the_oracle_reproduces_the_real_runs_discovered_set` fails INTERMITTENTLY in a full-suite run and blocked a real push, while passing every time in isolation

### Acceptance

the arm is green across five consecutive full-suite runs, or the state it depends on is identified and pinned so the arm fails for a stated reason rather than by luck


## CS-610

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`tests/conftest.py` leaves a skip report unredacted because a skip's `longrepr` is a tuple its redactor declines to touch, so a skip reason that ever interpolates a machine value leaks with nothing to catch it

### Acceptance

a planted machine value in a skip reason is redacted or is caught by a guard, proven by an arm that fails when the redaction is removed


## CS-611

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`allow_reuse_address = False` is justified by a Windows measurement, but on POSIX the same setting makes a rebind of the FIXED allocated port fail through the TIME_WAIT window, and every arm binds an ephemeral port so the divergence is graded by nothing

### Acceptance

the fixed-port rebind path is exercised on POSIX, or the divergence is recorded with the reason it cannot be


## CS-612

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

`test_the_generated_key_is_restricted_to_this_account` may be tautological on the only platform that runs it, because openssl may already open the key file 0600 and leave `_restrict` doing nothing

### Acceptance

`_restrict` is proven load-bearing by a control that reddens when it is a no-op, or the arm is recorded as grading the artifact rather than the call


## CS-620

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the Node behaviour suite runs only in tier 2, so a `shell/lib` regression merges green and stays invisible until the nightly, while two commit subjects invite the reading that both lanes cover every push

### Acceptance

the Node suite runs on the every-push lane, or the split is recorded where a reader of a green push would find it


## CS-621

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the tier-2 syntax step enumerates `git ls-files -- shell` while the Python guard uses `--cached --others --exclude-standard`, so an untracked `.js` under `shell/` is graded by one gate and skipped by the other

### Acceptance

both gates grade the same population, or the divergence is recorded at both sites with the reason


## CS-622

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

the forbidden-token sweep is a substring test over eleven literals, so any string concatenation defeats all eleven at once, and `appendArgument`, `setSSLConfig` and the command-line switch spellings are absent from the table entirely

### Acceptance

the sweep's ceiling is recorded at the point of use, and each named gap is either closed or listed as out of reach with its reason


## CS-623

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

two arms grade the same 7-bit-ASCII property with different boundaries: `shell/test/window.test.js` accepts any byte at or below 0x7F while `tests/shell/test_shell_assets.py` caps at 0x7E, so a DEL byte passes the Node lane and reddens the Python one

### Acceptance

one boundary owns the rule and the other reads it, proven by an arm planting DEL that both lanes agree on


## CS-913

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

unlock state is EMPTY for every save and the cause filed with it is REFUTED by the code: `clockspeed/save/world.py::_read_unlocks` takes ZERO arguments and returns `EMPTY_UNLOCK_STATE` unconditionally, so the emptiness is a property of the producer rather than of any save, while `clockspeed/save/objects.py::read_properties` is a complete tagged-property decoder with no production caller - the grammar was measured and the plumbing was never built

### Acceptance

`/api/world` reports non-empty unlock state for a save known to carry it, read through the shipped decoder against the six carriers named in `docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md`, graded by a synthetic `PropertyMap` so the suite still runs with no game installed, with `UnlockState.current_game_phase` retyped off `int | None` first because the value is an asset reference, and the CONTROL is SYNTHETIC and DIFFERENTIAL rather than a world - two hand-authored `PropertyMap` payloads over the same carriers at different progression, the lesser a strict subset of the greater, decoding to DIFFERENT and correctly ordered `purchased_schematics` and `recipes` and to different `current_game_phase` assets, plus a decoy payload carrying `mPurchasedSchematics` on a NON-carrier class that must contribute nothing, so that a reader returning a constant, ignoring content, or matching a property name without its owning class each fails an arm; the absent-array arm at `tests/save/test_world.py::test_an_absent_unlock_array_is_an_empty_set_rather_than_an_error` is retained but is explicitly NOT the control, because a reader returning `EMPTY_UNLOCK_STATE` unconditionally - which is this item's own defect - passes every assertion in it; whether a real save agrees is an OPERATOR-LOCAL check the suite does not run and that stays gated on `CS-G06` - blocked on `CS-G06`


## CS-915

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

two guards report zero findings for a reason that is not the absence of findings: the overlay arm in `tests/surface/test_web_assets.py` declares tokens with `[A-Za-z0-9-]` and compares their values with `[a-z0-9-]`, so an uppercase custom property drifts silently past the check, and `test_the_harness_answers_every_route_it_publishes_as_live` discards the METHOD on both sides, so re-keying every canned answer to `TRACE` leaves it green - both LATENT today and both demonstrated by mutation

### Acceptance

each arm reddens on its demonstrated mutant, with the method carried through from `routes.py` rather than collapsed away


## CS-916

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. Relocated verbatim, never deleted:

three separate features are gated on ONE prerequisite and nothing files it: node semantics, where `/api/world` carries 797 placements and says in its own warning that purity and resource type are level defaults a save never writes; icons, which can never be committed because non-negotiable 2 forbids anything extracted from the install and the CSP publishes no `img-src` so every image is blocked today; and a to-scale factory planner, for which `/api/registry` publishes recipes and `is_fluid` but `BUILDING_KEYS` carries only `key` and `display_name` - no footprint, no port count, no port side, no power draw, so not one building can be drawn to scale

### Acceptance

an extraction path reads the shipped assets into gitignored `data/` at first run, is skipped cleanly on a machine with no install, commits nothing it produced, and answers all three questions from one pass with the registry route widened to carry the building geometry


## CS-603

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

`tests/test_scaffold.py` excludes `clockspeed/surface/web` on a reason that has expired, so the file asserting the package topology now states something false about it

### Acceptance

that directory is either graded as a non-package directory that must exist, or its exclusion carries a reason that is true on the day it is read, and a test fails if the directory is emptied


## CS-608

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

`tests/surface/test_web_assets.py`'s personal-data sweep matches only Windows-shaped paths, so on the every-push lane it grades three of its six shapes while its own control stays green

### Acceptance

every path shape the sweep claims is either matched by a POSIX-shaped planted value or recorded as Windows-only with the reason, and the control fails when a shape is removed


## CS-613

### RELOCATED 2026-09-06 from the ROADMAP item line, for the CS-926 budget pass

The headline this item carried before its line was cut to the one-liner the
`ROADMAP.md` header asks for. This item had no section, so its reasoning lived on
the line alone. Relocated verbatim, never deleted:

every TLS arm sits behind `cert_pair`, which skips when openssl cannot be run, so a runner without openssl loses the whole TLS path as a skip rather than as a failure

### Acceptance

an absent openssl either fails the surface suite loudly or leaves a stated skip whose reason names what went ungraded


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

### Acceptance

a population whose size decides what a suite measures is graded by EQUALITY against an independently derived expectation rather than by a floor, and a module's own collected arm count is asserted against a derived expectation so a silent drop cannot pass, proven by a use-site narrowing of a producer that reddens where a floor still holds AND by a planted arm-count drop that reddens

### Full headline

a value that decides what a POPULATION MEASURES is narrowable at its use site while the floor guarding it stays satisfied, and every repair of one instance created a fresh one ONE LEVEL OUT - measured FOUR times inside CS-929 alone: the corpus root, then the anchor introduced to pin the root, then that anchor's use site reachable by string concatenation, then the plant producer's own return statement sliced to `[:3]` against a floor of 3 met exactly - each one silently dropping arms from a green run (476 to 466, and one widening to 478)

### Recorded 2026-11-19 by wave 0 unit U-052.4: CS-995 folded into this row (plan ruling D88), NOT A COMPLETION RECORD

The folded row CS-995 (headline: the converse leg of `unpinned_eligibility_faults` is itself ungraded for BREADTH in
both detection and naming) was folded into CS-988 by wave 0 unit U-052.4. Its ROADMAP line is gone and its leaf
section is in `docs/history_notes.md` under its id. Its acceptance, quoted verbatim, and graded separately at this
row's close with its own ledger record (D88):

> dropping any SINGLE key from the converse leg's detection set or from its naming reddens a named arm, with the expectation DERIVED from a source the leg does not itself read and the arm exercising the leg at a breadth ABOVE ONE, proven by a mutation per direction - NEVER by a floor over the finding count, which is the CS-988 shape and is forbidden here by name

### Recorded 2026-11-19 by wave 0 unit U-052.4: CS-998 folded into this row (plan ruling D88), NOT A COMPLETION RECORD

The folded row CS-998 (headline: `INDEPENDENT_CASE_COUNTS` membership is uncertified: the header asserts that every
entry re-derives its size from a DIFFERENT source than the mark reads) was folded into CS-988 by wave 0 unit U-052.4.
Its ROADMAP line is gone and its leaf section is in `docs/history_notes.md` under its id. Its acceptance, quoted
verbatim, and graded separately at this row's close with its own ledger record (D88):

> each key in the registry is graded by a per-key equality between its re-derivation and a source the mark does not read, an entry whose callable ignores its own population reddens, and the prose claim is either machine-checked or deleted


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

### Acceptance

an arm in `tests/surface/test_world.py` asserts the published value's type is the type `UnlockState` declares for that field, derived from the model's annotation rather than from a literal, and reddens when the harness value and the declared type disagree; and a second arm asserts the harness's key set equals the published key set in BOTH directions so a field added to one and not the other is caught

### Full headline

`tests/surface/audit_harness.py::SYNTHETIC_UNLOCKS` hand-builds the published world dict and hardcodes `current_game_phase` to the integer 2, so the surface suite asserts a type the model does not declare and 1478 arms pass without one of them observing the field's type - the harness is a fixture that drifted off the model it stands in for, and a retype in `save/` changes the wire silently


## CS-1046

### Filed 2026-09-13

**TWO PUBLISHED DOORS THAT REFUSE, AND A PATTERN THAT CANNOT NAME A MODERN ITEM.**
`/api/plan` and `/api/audit` are published in the endpoint table and answer 501. CS-500 closed
on 2026-10-04 and stopped being their blocker: `clockspeed/surface/api/pending.py::BLOCKERS`
now names CS-1046 itself for both, because what is missing is the published body this item
writes. `/api/plan` additionally waits on CS-1043 - `clockspeed/progress/` still holds no code.
Separately `contract.BLOCKER_PATTERN` admitted `CS-` followed by exactly three digits, applied
with `fullmatch`; that half was widened to three or four digits on 2026-10-04 (the CS-1270
progress record in `docs/LEDGER.md`), and the acceptance arm below is what still grades it.

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

### Acceptance

an arm in `tests/surface/test_contract.py` asserts the blocker pattern's four-digit boundary in BOTH directions, a new arm module beside it asserts the served plan key set equals the plan module's own `DATA_KEYS` in both directions and that `contract.encode` accepts the body, and an arm in `tests/surface/test_pending_route_count.py` asserts the unbacked set is the partition complement rather than a literal count

### Full headline

`/api/plan` and `/api/audit` are published in the endpoint table and answer 501 naming CS-1046 because their bodies are unpublished, and `clockspeed/surface/api/contract.py`'s `BLOCKER_PATTERN` admitted `CS-` followed by exactly three digits until it was widened on 2026-10-04, while `/api/plan` also waits on CS-1043


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

### Acceptance

an arm in `tests/surface/test_panel_map.py` asserts the class attribute set the panel emits EQUALS the category set the wire declared, derived from the payload rather than a literal, a second arm there asserts a mined node and a bare node differ in an attribute the stand-in DOM can actually observe, and an arm in `tests/surface/test_web_assets.py` asserts a poll whose world token is unchanged issues NO fetch

### Full headline

the map draws bare dots on no underlay with no category, no elevation ordering, no need-vibrance and no mined-versus-unmined distinction, the page has no plan panel and no world power panel, its CSP carries no `img-src` so it could not render an underlay if one existed, and nothing but the header button repaints it


## CS-1065

### NOTE - filed 2026-09-14 under CS-301

`within_estimate` is a TRI-STATE and the null is load-bearing: None means there was no independent
second source to check against, which is the struct-range shape, where the declaration and the
estimate are the same two numbers. Collapsing it to a boolean at the wire edge turns "nothing to
check" into "checked and failed", and the dashboard has no way to tell those apart afterwards. The
refusal vocabulary ADR 0012 fixed is where the wire form for this belongs; read it before choosing a
spelling.

### Acceptance

the endpoint publishes the bounded draw beside the operands with both bounds as the wire rational form and `within_estimate` carried through as a tri-state rather than collapsed to a boolean, proven by an arm asserting the served body equals the layer result field for field and by an arm asserting the null case is served as null rather than false

### Full headline

the power endpoint serves `variable_power_inputs` and nothing else, so a dashboard reading it still sees `modeled` false and four loose operands for the three variable-power buildings CS-301 can now bound


## CS-600

### Acceptance

the 5-phase visual audit from CONVENTIONS section 13.2 passes before the page is committed

## CS-1254

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Surface renders only what the API computed (seam rule).

### Acceptance

the dashboard renders only API-computed cells; the shortfall row is empty when the target is met; a shortfall cell opens that card's derivation

## CS-1255

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Applies to target-rate and clock inputs in dashboard and companion.

### Acceptance

a browser test types a two-digit value one key at a time and the field holds it; a fraction input reaches the API as an exact value

## CS-1256

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. The display string comes from CS-1239's rounding function; clients never round and never re-derive.

### Acceptance

a schema test asserts both forms exist for every numeric field; the shell renders the display string verbatim

## CS-1257

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Selected target, strategy, filters and open card only.

### Acceptance

a test round-trips state through the fragment; a test asserts no world token, world name, account id or path appears in the encoded string

## CS-1258

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Keyboard navigation, landmarks, dialog focus trap, labelled states, reduced motion, forced colours, AA contrast.

### Acceptance

an automated accessibility probe in the existing dashboard probe flow reports no serious violation; a keyboard-only path reaches every card's tier 3

## CS-1436

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-084. Class: product. Lane flag: false (not eligible: a new row beside CS-1258, which the dashboard scope excludes at `config/lane_scopes.json` line 86; the new row gets its own exclusion row at filing, see ROADMAP line; `app.css` is a hub file). Planned minutes: 140 (2 parts (70 + 70)).
Depends on: none.
Wave: W3, W20 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): none; no part shares a file with another unit of its wave.
Write-list:
- U-084.1 (W3-G3-S1, 70 min): `clockspeed/surface/web/app.css`, `tests/surface/` `test-web_palette`
- U-084.2 (W20-G3-S1, 70 min): `tests/surface/` `test-web_palette`

### Acceptance

All arms live in NEW `tests/surface/` test-web_palette.py, stdlib only. Ratios are WCAG 2 relative luminance, compared unrounded; quoted figures are rounded to two places.
1. Helper fixed points: `contrast_ratio("#000000", "#ffffff")` is 21.0 and of a colour with itself 1.0, to 1e-9. Arm: ``test-the_luminance_helper_reproduces_the_two_fixed_points``.
2. The `.bench-input` boundary is 3:1 or better against `--surface` AND against its own fill `--surface-alt`, in light and dark. The arm reads the token from the rule's own `border` declaration. Arm: ``test-the_bench_input_boundary_clears_three_to_one_on_both_grounds`` (parametrized light, dark). Red on today's tree at 1.41 and 1.24 (light), 1.40 and 1.26 (dark); green after at 3.94, 3.48, 3.68, 3.31.
3. The `.map-filter[aria-pressed="true"]` boundary is 3:1 or better against its own fill `--idle-bg` and against `--surface`, in light and dark. Arm: ``test-the_pressed_map_filter_boundary_clears_three_to_one``. Red today at 1.14 (light) and 1.17 (dark) on the fill; green after at 3.20 and 3.06.
4. Both rules read `--hud-rule` and no token is added: `clockspeed/surface/web/app.css` `.bench-input` and `.map-filter[aria-pressed="true"]` each hold `border: 1px solid var(--hud-rule);`. Arm: ``test-both_boundaries_read_the_hud_rule_token`` (it grades the two declarations only). Builder check, not an arm (a test sees no base): `git diff <base> -- clockspeed/surface/web/app.css` shows no added line beginning `--`.
5. Negative: the same check run on the sheet text with `var(--hud-rule)` put back to `var(--border)` inside the `.bench-input` block reports four failing pairings (two grounds, two schemes), with the substitution asserted as applied. Arm: ``test-the_boundary_arm_fires_on_the_token_it_replaced``.
6. Every declared text pairing is 4.5:1 or better in `light`, `dark` and `overlay`. Declared text pairings are (a) each rule that sets both `color` and `background` or `background-color` to a token, and (b) each token read by `color` in a rule that sets no background, against each of `--bg`, `--surface`, `--surface-alt`. Arm: ``test-every_declared_text_pairing_clears_four_and_a_half_to_one`` (parametrized by scheme).
7. Control: the lowest pairing of kind (a) reads 5.03 in light (`--status-throttled` on `--status-throttled-bg`) and 5.30 in dark and in overlay (`--btn-fg` on `--btn-bg`). Arm: ``test-the_derivation_reproduces_the_recorded_floors``.
8. Every declared non-text boundary is 3:1 or better in all three schemes: `--focus`, `--hud-rule`, `--btn-border` and each token read by a `border-left-color` declaration (the status edge), each against `--bg`, `--surface` and `--surface-alt`. Arm: ``test-every_declared_boundary_clears_three_to_one`` (parametrized by scheme). Lowest at HEAD: 3.48 light and 3.31 dark, both `--hud-rule` on `--surface-alt`.
9. Planted colour: with `--muted: #777777;` substituted in the light `:root`, the text arm's finder reports three failing pairings (`--muted` on `--bg` 4.17, `--surface` 4.48, `--surface-alt` 3.95); the arm asserts that the `--surface` member at 4.48 is AMONG them, never that it is the whole report, and that the substitution was applied. Arm: ``test-a_planted_colour_turns_the_text_arm_red``.
10. Swap mutant: with the light values of `--status-starved` and `--status-starved-bg` exchanged, the boundary finder reports `--status-starved` on `--surface` at 1.34; the arm asserts the mutated text holds `--status-starved: #f7d7da;`. Arm: ``test-swapping_two_status_colours_turns_the_edge_arm_red``.
11. Not vacuous, not silently wrong: each scheme yields at least one pairing of each kind; a pairing member whose value is not a six-digit hex colour is REPORTED, never skipped (`--shadow` is `rgba(...)` and is a member of no pairing). Arms: ``test-no_scheme_derives_an_empty_pairing_set``, ``test-a_pairing_member_that_is_not_a_hex_colour_is_reported``.
12. The token source is a parameter: every css-reading helper (all but `relative_luminance` and `contrast_ratio`, which take colours, clause 1) takes the stylesheet TEXT as its first argument and none reads a file; only the arms call `test_web_assets.read_asset`. Arm: ``test-the_helpers_grade_a_sheet_passed_as_text`` (a three-rule synthetic sheet in the test body).
13. Comments are stripped before any rule or declaration is parsed: `/* ... */` blocks are removed from the sheet text first, so a comment holding a brace or a `color:` cannot become a rule. At HEAD the sheet's 42 comments hold neither, so the plant is what proves it. Arm: ``test-a_rule_planted_inside_a_comment_is_never_parsed`` (a synthetic sheet whose comment holds `.x { color: var(--muted); }` yields the same palette and pairings as the sheet without it).

## CS-1259

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Reinforces the local property.

### Acceptance

with networking disabled the dashboard renders; a test scans the built page for external URLs and finds none

## CS-1260

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Palette values stay out of `docs/hud_doctrine.md` per the topology table.

### NOTE - filed 2026-11-25 by the session 159 plan

1. `test-no_surface_source_outside_the_token_file_carries_a_colour_literal` in `tests/surface/test_web_assets.py` passes. Population, derived with `git ls-files --cached --others --exclude-standard` (the form of tests/shell/test_shell_assets.py line 147): every file under clockspeed/surface/web/ except app.css, and every file under shell/ except shell/test/, shell/package.json and shell/package-lock.json. A colour literal is: a hex value (`#` plus 3, 4, 6 or 8 hex digits), any colour function (rgb, rgba, hsl, hsla, hwb, lab, lch, oklab, oklch, color, color-mix, light-dark), a named or system colour as the VALUE of a colour-bearing property inside a CSS or style context (a style attribute, a `.style.x =` write, a setAttribute of fill, stroke, color or style, an insertCSS string), or any `backgroundColor` value. THE DETECTOR IS DEFINED, NOT JUDGED: (i) comments are removed first by a STRING-AWARE stripper (the form of `code_of`, tests/shell/test_shell_assets.py line 418; `code_only` at tests/surface/test_web_assets.py line 2327 removes block comments only and is not enough, because shell/lib/tray.js holds a base64 string whose `/` characters a naive stripper would cut), and HTML comments by `_HTML_COMMENT` (tests/surface/test_web_assets.py line 1300), so the colour words in comments (shell/lib/tray.js:129-132) are never read; (ii) a hex value or a colour function is reported ANYWHERE in what remains, string or code; (iii) a named or system colour is reported only as the value of a `property: value` pair whose property is in `_COLOUR_BEARING` (tests/surface/test_web_assets.py line 722), found inside ANY string literal or style attribute - so `DRAG_STRIP_CSS` is graded where it is defined (shell/lib/window.js:234), not where it is passed to insertCSS (shell/main.js:712) - or as the right-hand side of a `.style.<colour property> =` write or of a setAttribute of fill, stroke or color; (iv) any `backgroundColor` value.
2. `test-the_colour_literal_detector_fires_on_each_planted_shape` in `tests/surface/test_web_assets.py` passes and plants at least: a hex inside a JS string, `color: black` inside an HTML style attribute (both named by D57), `rgb(0, 0, 0)` in an insertCSS string, and `backgroundColor: "#000000"`; each is reported. NEGATIVE controls reported as clean: the word `black` in a JS comment, `currentColor`, `var(--bg)`.
3. Exemptions are by NAME and exactly one: the constant `ICON_PNG_BASE64` in shell/lib/tray.js (line 135; its decoded-pixel test in shell/test/tray.test.js holds it). The arm's ONLY assertion about it is that the constant still exists, so the exemption cannot outlive it. The exemption is inert at HEAD - a base64 payload holds no `#` and no parenthesis, so removing it changes no result - and NO negative control is claimed for it; it is kept because D57 rules it by name. No forced-colors exemption is written here (R-accessibility-9's slice owns it, D57). The ledger closure record names app.css as the token file and cites clauses 1 and 2 by test name.

### Acceptance

both surfaces import the same token file with light and dark variants; no hard-coded colour literal remains in either surface outside it

## CS-1261

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. Non-negotiable 13: never echo a value.

### Acceptance

binding a non-loopback address without an explicit local flag fails fast; no query-string token is accepted; refusal reasons are logged server-side and the caller gets a generic refusal; two generated certs differ in subject

## CS-1437

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-089. Class: product. Lane flag: false (not eligible: hub file clockspeed/surface/server.py; a real-display reading and check). Planned minutes: 305 (4 parts (75 + 75 + 115 + 40), plus a 15-minute agent-run real-display check inside part 4, plus a conditional 30-minute fallback reading inside part 3 (taken only when the M7 verdict is absent; the 30 is an UNVERIFIED estimate)).
Depends on: none.
Wave: W3, W4 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-089.2 in W4: `clockspeed/surface/server.py` 1/2, `tests/surface/` `test-admission` 1/2; U-089.3 in W4: `clockspeed/surface/server.py` 2/2, `tests/surface/` `test-admission` 2/2.
Write-list:
- U-089.1 (W3-G2-S1, 75 min): `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `tests/surface/` `test-admission`, `clockspeed/surface/api/health.py`
- U-089.2 (W4-G1-S1, 75 min): `clockspeed/surface/api/contract.py`, `tests/surface/test_contract.py`, `clockspeed/surface/server.py`, `tests/surface/` `test-admission`
- U-089.3 (W4-G2-S1, 115 min): `clockspeed/surface/api/routes.py`, `tests/surface/` `test-admission`, `clockspeed/surface/server.py`
- U-089.4 (W4 merger landing after U-089.3, 40 min): `docs/OPERATIONS.md`, `docs/item_notes/phase6.md`, `BACKLOG.md`; close step: `docs/LEDGER.md`, `ROADMAP.md`, `docs/history_notes.md`

### Acceptance

The leaf `### Acceptance` text, verbatim (chapter clause (a); the non-loopback and token clauses are NOT carried, D59): "every request must carry exactly one Host header naming the loopback address or localhost with the bound port; every /api route that does not declare itself open refuses a Sec-Fetch-Site other than same-origin or none and, when that header is absent, refuses an Origin that is not this origin, null included; a mutating route also refuses a foreign or null Origin whenever one is present; every such refusal is the one generic 403 and the server log names the cause from a closed set; stated residual: a cross-site GET carrying neither header is admitted."

Graded by these arms (all in `tests/surface/` test-admission.py unless a file is named; every live arm builds its server from SPY routes, never from the bound handlers):
1. `test-a_request_without_exactly_one_admitted_host_is_refused`: Host `evil.example:<bound port>`, Host `127.0.0.1:<another port>`, no Host, and two Host headers each answer 403 on `/`, on one static asset and on `/api/world`; the body is byte-equal to `contract.encode(contract.forbidden(contract.ENDPOINT_UNROUTED, contract.REASON_CROSS_ORIGIN_REFUSED).payload)` and holds no request byte.
2. `test-both_loopback_host_spellings_are_admitted`: `127.0.0.1:<bound port>` and `localhost:<bound port>` answer 200; `localhost` with no port is 403.
3. `test-a_foreign_fetch_site_is_refused_before_the_handler`: `Sec-Fetch-Site: cross-site` and `same-site`, and the header sent twice, are 403 on GET /api/advice, POST /api/solve, POST /api/optimize, GET /api/world, GET /api/map, GET /api/power, GET /api/registry; the spy was never called. `OPTIONS /api/advice` under `cross-site` is 403, not 405 (the gate runs before the method check; `do_OPTIONS`, clockspeed/surface/server.py line 1084).
4. `test-a_foreign_or_null_origin_without_a_fetch_site_is_refused`: with no Sec-Fetch-Site, `Origin: https://evil.example`, `Origin: http://127.0.0.1:<port>` (wrong scheme), `Origin: null` and two Origin headers are 403 on POST /api/solve, POST /api/optimize and GET /api/advice, spy not called; `test-this_origin_is_admitted`: `https://127.0.0.1:<port>` and `https://localhost:<port>` are admitted.
5. `test-health_stays_open_under_hostile_site_and_origin_headers`: the header sets of 3 and 4 on GET and HEAD /api/health are 200 (a foreign Host there is still 403).
6. `test-a_request_with_neither_header_is_admitted_on_a_read`; and `tests/surface/test_server.py::test_a_get_needs_no_proof` (:3362) and `::test_a_post_to_a_route_that_does_not_mutate_needs_no_proof` (:3412) stay green with their bodies unedited.
7. `test-a_proven_mutation_with_a_foreign_or_null_origin_writes_nothing`: the proof header (which IS `Sec-Fetch-Site: same-origin`, clockspeed/surface/server.py lines 298-301, so this arm is the 'whenever one is present' case and needs no further site row) plus `Origin: https://evil.example` or `null` is 403 and the ledger file is byte-identical before and after; `test-a_proven_mutation_from_this_origin_records`.
8. `test-no_page_fetch_sets_a_mode`: no `fetch(` call in clockspeed/surface/web/app.js carries a `mode` key; a planted `mode: "no-cors"` copy makes the same scanner report it (negative control).
9. `test-each_refusal_logs_its_cause_word_and_no_request_byte`: each refusal writes exactly `<METHOD> <label> 403 refused=<cause>` with cause in `host`, `site`, `origin`, `proof`; `<label>` is asserted: `contract.ENDPOINT_UNROUTED` for `host`, the matched template for `site`, `origin` and `proof`; a canary placed in Host, Origin, Sec-Fetch-Site, path and query appears in no log line (the sweep is shown to find a canary a control handler prints).
10. `test-every_refusal_body_is_the_published_envelope`: `contract.contract_problems` is empty for each refusal the reason is `cross_origin_refused` for all four causes, and the body's endpoint field equals the label arm 9 names for that cause.
11. `test-a_route_is_not_open_by_default` in `tests/surface/test_contract.py` (the ONLY arm of this clause in that file; the four below are in `tests/surface/` test-admission.py, so part 3 writes no test_contract.py); `test-routing_refuses_an_open_route_that_mutates`; `test-routing_refuses_a_template_that_mixes_open_and_closed_routes`; `test-only_the_health_template_is_open` (over `routes.SERVING_ROUTES`, the set equals `{health.ENDPOINT}`); `test-the_server_names_no_endpoint_module` (an ast walk of server.py finds no import of `clockspeed.surface.api.health`, `.routes` or any other endpoint module).
12. `test-a_route_registered_with_no_flags_is_refused_cross_site`; `test-head_takes_the_class_of_its_get`: HEAD /api/health under a hostile site header is 200; HEAD /api/advice and HEAD /api/world under `Sec-Fetch-Site: cross-site` are 403 and the spy is not called.
13. `test-every_serving_route_and_static_path_answers_by_class`: one table over every (method, template) of `routes.SERVING_ROUTES` (handlers replaced by spies, `mutates` and `open` copied) and every key of `server.STATIC_ROUTES`, against five header sets (foreign Host; cross-site; foreign Origin with no site header; null Origin with no site header; clean, with the proof header added on mutating pairs). Expected: static and open = 403, 200, 200, 200, 200; every other /api pair = 403, 403, 403, 403, not 403. Every GET pair is walked again under HEAD with the same class.
14. docs/item_notes/phase6.md `## CS-NEW` carries the clause above, the stated residual and the measured header values; `## CS-1261` is byte-unchanged (`git diff` shows no hunk inside :1151-1159).
15. The Origin and Sec-Fetch-Site values the companion page's four POSTs, its GETs and the supervisor probe really send are recorded in the leaf section BEFORE the commit that refuses `Origin: null` (part 3 entry rule).
Commands: `.venv/Scripts/python.exe -m pytest `tests/surface/` test-admission.py tests/surface/test_server.py tests/surface/test_contract.py tests/surface/test_advice_act.py -q` exits 0. `tools/provenance_stamp.py check` is the landing slice's command, never the builder's (D99 item 9).

## CS-1262

### Filed 2026-10-04 by the inspiration ingest

From the inspiration ingest of 2026-10-04 - an untracked external survey whose items are IDEAS ONLY; nothing was fetched, copied or lifted, and every part is re-derived here under section 3 and section 7 of `CLAUDE.md`. The product form of non-negotiables 11 and 12.

### Acceptance

a fixture with planted personal strings produces an archive containing none of them; the header options string never appears

## CS-1434

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-053. Class: product. Lane flag: false (not eligible). Planned minutes: 310 (3 parts (U-053.1 120, U-053.2 120, U-053.3 70)).
Depends on: CS-1439 part 3 (U-107.3).
Wave: W4, W5 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-053.2 in W5: `tests/surface/test_web_assets.py` 1/2.
Write-list:
- U-053.1 (W4-G1-S2, 120 min): `clockspeed/surface/web/index.html`, `clockspeed/surface/web/app.js`, `clockspeed/surface/web/app.css`, `tests/surface/` `test-views`, `tests/surface/test_web_assets.py`, `tests/surface/test_panel_seam.py`, `tests/surface/panel_harness.py`, `tests/surface/test_panel_global_scope.py`
- U-053.2 (W5-G1-S1, 120 min): `clockspeed/surface/web/app.css`, `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py`, `clockspeed/surface/web/app.js`, `tests/surface/` `test-views`, `tests/surface/test_web_assets.py`, `tests/surface/panel_harness.py`, `tests/surface/test_panel_global_scope.py`
- U-053.3 (W5 merger landing after U-053.2, 70 min): `docs/item_notes/phase6.md`, `docs/item_notes/phase4-followups-960.md`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`; wording returned to its hub slice, not edited: `docs/hud_doctrine.md`

### Acceptance

1. Nav (`test-the_nav_holds_exactly_four_view_buttons_in_order` in `tests/surface/` test_views.py): index.html holds exactly one `<nav id="views" aria-label="Views">` with exactly four `<button type="button" data-view="...">` labelled Play, Plan, Map, System in that order; exactly one carries `aria-current="page"`. `test-the_frame_adds_no_anchor_tab_role_tabindex_or_disclosure` pins occurrence COUNTS over the raw text, comments included, because `tabindex` is already present at HEAD: app.js holds `tabindex` exactly 4 times (clockspeed/surface/web/app.js:346, :357, :383, :395) and index.html exactly once (clockspeed/surface/web/index.html:58), and `<a `, `role="tab"`, `<details` and `<summary` occur 0 times in both files. The arm asserts those ten counts as literals, so a new comment holding one of the tokens is red too; U-107.3 lands first, so re-read the counts in the landed tree before pinning and record any difference in the build note.
2. Default view: with an empty fragment `#view-play` is the only one of `#view-play`, `#view-plan`, `#view-map`, `#view-system` without the `hidden` attribute. Negative: `#view=nope`, `#card=7` and `#view=play&x=1` each show Play and none is written back or rendered.
3. One table: app.js holds `VIEWS = ["play", "plan", "map", "system"]` and one `PANEL_VIEWS = { advice: "play", map: "map" }`; a panel id absent from the table mounts in `#panels`, which now sits inside `#view-system`. Every key is a panel registered on the shipped page and every value is a member of VIEWS (both directions on the shipped page; a planted dead key reddens). `registerPanel(id, mountFn)` keeps two arguments and `git diff --stat <base>..HEAD -- clockspeed/surface/web/panel_*.js` prints nothing.
4. Fragment: pressing a view button sets `location.hash` to exactly `view=<name>`; loading with `#view=map` shows Map; the fragment round-trips through `hashchange`. The writer has ONE assignment site and emits only the literal `view=` plus a VIEWS member. Privacy arm: with a canned world carrying planted world-token, world-name, account-id and path canaries, after every view press the fragment equals `view=<name>` and holds no canary and no card id (D105: view state only).
5. Keyboard: the view buttons are plain buttons (Tab order, Enter and Space by the platform); app.js still contains no `keydown`, `keyup` or `keypress` (0 at HEAD) and adds no arrow-key model.
6. Ids kept: every member of `REQUIRED_NODE_IDS` (tools/dashboard_probe.py line 294, as U-107.3 left it) and the ids `panels`, `refresh`, `pin`, `badge-registry`, `badge-world` still exist exactly once; tests/test_dashboard_probe.py::test_the_required_nodes_are_all_declared_by_the_page_it_grades and tests/surface/test_web_assets.py stay green.
7. Rule-7 slot (D52): the app bar holds one `<p id="flag-count">` outside every view host. Text: `load warnings: <N> | unmodelled classes: <M>` when either served count is non-zero, `no load warnings, no unmodelled classes` when both are zero, `load flags unknown: no world answered` when the world payload is null. N and M are `data.world.counts.warnings` and `data.world.counts.unknown_classes` rendered as served (clockspeed/surface/api/world.py lines 215-216); the page counts nothing. The slot carries no status or warn class and is visible with each of the four views active (`test-a_non_zero_flag_count_is_visible_on_every_view`).
8. Empty view: `#view-plan` ships one static, dim, non-heading line `no plan panel is mounted yet`, removed by the first panel mounted there; no other view ships a placeholder heading.
9. Heights come from a percent chain off `html` and `body`; the frame rules (html, body, the app bar, main, the four view hosts) declare no `vh`, `vw`, `dvh`, `svh` or `lvh` (`test-the_frame_declares_no_viewport_unit`; `.map-canvas` at clockspeed/surface/web/app.css:993 is outside the frame and untouched).
10. A view not yet fitted scrolls inside its own view host, never the document, and its name is listed in `data-fit-inner`. The SOURCE of that list is the sheet, measured: app.css gives `#view-plan`, `#view-map` and `#view-system` `overflow-y: auto`, and `#view-play` declares `overflow: visible` in every mode, so Play content past its box overflows the document and is caught by `data-fit`; app.js lists a view exactly when `getComputedStyle` of its host reads `overflow-y` `auto` or `scroll`, and holds no list of names of its own. `test-the_play_host_never_declares_an_inner_scroller` (static, over app.css: no rule matching `#view-play` sets `overflow`, `overflow-x` or `overflow-y` to `auto`, `scroll`, `hidden` or `clip`); `play` is never listed, and a page that lists it fails the fit stage.
11. Fit publication: after every paint, view change and `resize`, app.js writes on `<html>`: `data-view` (active view), `data-fit-mode` (the value of the CSS custom property `--fit-mode`: `fixed` at or above 1100x772, else `reading`; no size threshold number appears in app.js), `data-fit-box` (`<innerWidth>x<innerHeight>`), `data-fit` (`fits` or `over`, measured on BOTH `document.scrollingElement` and `body`), `data-fit-x` (`fits` or `over`), `data-fit-inner`, `data-fit-clipped` (count of elements past the right edge, a `.scroll-x` box excepted), `data-fit-id` (id of the first offending element, else empty), `data-fit-pane` (`absent`, `fits` or `over` for the one element marked `data-fit-exempt="tier3"`, D112). The block calls no `setTimeout`, `setInterval` or `requestAnimationFrame`.
12. Probe stage (tests/test_dashboard_probe.py): `EXIT_FIT == 10`; STAGE_CODES order is port, launch, transport, json, dom, fit, cleanup (9 is left for the a11y stage, D54); with no browser every fit arm's verdict is UNAVAILABLE, the count is printed and the exit code is what it was without the stage; `--require-fit` turns UNAVAILABLE into exit 10. Sibling edits, all in tools/dashboard_probe.py: `__all__` (tools/dashboard_probe.py line 173) gains `EXIT_FIT`; the exit-code list in the module docstring and the epilog (tools/dashboard_probe.py line 2041) each gain a row for 10; the law, which at HEAD is the comment at tools/dashboard_probe.py line 238 and the epilog sentence and is NOT in the module docstring, gains the words `the fit stage decides only on a browser that ran`. `test-the_fit_law_and_exit_code_are_written_where_the_probe_documents_itself` asserts `"EXIT_FIT" in __all__`, that the docstring and `EPILOG` each name `10`, and that `EPILOG` holds that sentence.
13. Control: before any verdict the stage asserts `data-fit-box` equals the requested size and `data-view` equals the requested view; a mismatch is EXIT_CONTROL (7), not 10 (`test-a_fit_box_mismatch_is_a_control_failure_not_a_fit_failure`).
14. By default the stage grades the probe's own child through the existing plain-HTTP bridge; `--fit-url <url>` grades a running audit harness; `--fit-size WxH:mode` (repeatable) replaces the default sizes `1100x772:fixed`, `550x386:reading`, `320x226:reading`; `mode` is the word expected on Play, and any other view may read either that word or `reading` (then it is graded by the reading arms). The defaults hold only until the narrow block exists: 550x386 lies inside U-056's narrow range (at least 360 x 240, below 640 x 452), so U-056.2 re-pins the default to `550x386:narrow` with its arm in the commit that adds the block; `320x226` is below the narrow floor and stays `reading`. An AST arm finds no import of `tests` in tools/dashboard_probe.py; it is a FENCE that passes at HEAD (the probe imports nothing from tests today), so it is proved red once with a planted `import tests` and the red output goes in the build note.
15. Rendered: `.venv/Scripts/python.exe tools/dashboard_probe.py --require-fit` exits 0 and prints, for each of the four views, at 1100x772 `data-fit=fits` with `play` absent from `data-fit-inner` and `data-fit-pane` not `over`; at 550x386 and 320x226 `data-fit-mode=reading`, `data-fit-x=fits`, `data-fit-clipped=0`. No arm reads UNAVAILABLE in a run cited as acceptance. Pane (D112): `data-fit-pane=over` is a fit failure (exit 10) at every size whose expected Play mode is not `reading`, in the default run and in any `--fit-size` run - `fixed` here, `compact` and `narrow` once U-056 adds them; the compact-floor size 640x452 is supplied by U-056 clause 7, because no compact mode exists before it. Control is not a pass: a browser that cannot honour a requested size (a minimum window width above 320 or 550) fails clause 13 with exit 7, and a size that ended in exit 7 or UNAVAILABLE is never cited as fitting. The fallback order is fixed: the default headless mode, then `--headless=old`, then a CDP device-metrics override on the same browser; if none yields the requested `data-fit-box` at all three sizes, U-053.3 stays OPEN and says which size failed. UNVERIFIED on this box: the adversary reports the local Chromium crashing in every headless mode, so no viewport size has been measured here.
16. Plant, proven once and recorded in the leaf build note: in a throwaway worktree a 2000px block appended to `#view-play` makes the same command exit 10 naming `play`, and the output shows `data-fit=over` (the plant applied).
17. Doctrine (wording ruled per D111, landed before part 1): docs/hud_doctrine.md section 1 states no document scroll at or above the default window size, Play fitting down to the compact floor, a reading mode below a view's threshold, the tier-3 pane as the one inner scroller (D112) and the compact companion shape with its limits and NO px value (D53: opaque, focusable, never click-through, never queries or binds to the game window or process, never repositions itself, changes no display mode, not visible over exclusive fullscreen and says so, Compact and always-on-top both off on a fresh install); section 2 bullet 1 states the count governs the cards and names the nav, one two-line status block and the detail pane as outside it.
18. Notes: a dated NOTE in `## CS-962` of docs/item_notes/phase4-followups-960.md records the D52 reading ("the page states plainly" is graded on the Scope panel in plain words, one press from every view, not on where it sits at first paint; acceptance not reworded). OPERATIONS line, quoted for the wave doc slice (section 7): `Fit check: python tools/dashboard_probe.py --require-fit (exit 10 = a view does not fit; UNAVAILABLE = no browser ran, never a pass).`

## CS-1438

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-096. Class: product. Lane flag: false (not eligible: a registry fetch, a runtime re-install in the MAIN checkout and a real-display acceptance run; none is a lane act). Planned minutes: 120 (1 part).
Depends on: none.
Wave: W3, group 1, slice W3-G1-S2.
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): none; no part shares a file with another unit of its wave.
Write-list:
- U-096 (W3-G1-S2, 120 min): `shell/package.json`, `shell/package-lock.json`, `tests/shell/test_shell_dependency_floor.py`

### Acceptance

1. Target named on the build day by the D22 minimum-age rule: the newest 44.x release at least 7 days old whose successor, if any, was published more than 72 hours after it (`npm view electron time --json`); an advisory whose range includes that target moves it upward and the override is recorded. The ledger entry states the target, the date read, the support schedule as read, the advisory database result for the target, and a summary of the release notes from 44.9.1 to the target.
2. shell/package.json `devDependencies.electron` is exactly the target (no range): tests/shell/test_shell_dependency_floor.py::test_the_manifest_pins_electron_exactly_at_or_above_the_floor and ::test_the_locked_electron_meets_the_advisory_floor green.
3. The lock resolves the target with a sha512 integrity that an adversary agent re-reads equal to `npm view electron@<target> dist.integrity`; `git diff --stat` for the bump names only shell/package.json and shell/package-lock.json, and no lock entry moves except electron and what the new version requires.
4. `ELECTRON_FLOOR` (tests/shell/test_shell_dependency_floor.py line 28) stays `(44, 9, 1)`. It is raised ONLY to the highest fixed version of an advisory that affects the 44 line and is above the present floor; then the comparator literals at :112-115 and the docstrings at :4 and :69 move with it. Negative: it is never raised to the pin by habit (D22).
5. The THIRD_PARTY.md electron row (line 336) reads the target version with the licence file and published manifest re-read and the re-read date; any difference is recorded in the row.
6. `npm audit` run in shell/ prints `found 0 vulnerabilities`.
7. One refresh in the MAIN checkout with the companion closed: `npm ci`, then the explicit install command of clause 8. Read-back command, run from the repository root, prints `True True`: `.venv/Scripts/python.exe -c "import json;m=json.load(open('shell/package.json'));print(open('shell/node_modules/electron/dist/version').read().strip()==m['devDependencies']['electron'],json.load(open('shell/node_modules/undici/package.json'))['version']==m['overrides']['undici'])"`. Red first: the same command prints `False False` at HEAD (installed electron 44.0.0 and undici 7.29.0, both below the lock). Sub-step (plan-rulings common-mode risk security#1), agent-run after the refresh: the desktop shortcut's target is read and compared with the refreshed `shell/node_modules/electron/dist/electron.exe` of the main checkout (the default target, scripts/make_shortcut.py line 199); the check prints only `True` or `False`, never a path, and the ledger records the word, or `NOT RUN` with the reason when no shortcut exists.
8. docs/OPERATIONS.md section 8.1 step 3 (lines 600-623) reads `npm ci`, then `npx install-electron --no`, then `npx electron .`. The builder MEASURES that `dist/version` exists after the first two commands and that no prompt appeared; if the measured command prompts or leaves no `dist/version`, the step is written as node node_modules/electron/install.js instead (the file the `install-electron` bin maps to) and the ledger records the measurement. The lazy-fetch paragraph is re-measured at the target and reworded to what was seen.
9. The section 8.3 manual acceptance (docs/OPERATIONS.md line 641) is run ONCE on the refreshed runtime by an agent with real-display tooling; every Observed line it ran carries the date and what was seen; a step it could not run keeps the literal `NOT RUN`.
10. docs/OPERATIONS.md gains `### 12.8 Moving the Electron pin` (after 12.7, before `## 13.`), and section 12.5 gains one closing pointer to it. It records, as rules and commands: exact pin, devDependency only; stay on the middle supported major; an advisory or Dependabot alert in range triggers a patch move at the next session; a Dependabot PR is never merged (12.5); the minimum-age rule of clause 1; the 45.x move is due by 2027-02-02 (the 44 end-of-life date minus four weeks, re-read on the day, never past the actual end of life). Two rules come from the recommendation (R-electron-hardening-2), NOT from D22's ruling text, and the section marks them so: with no trigger, the first session of each calendar month takes the newest suitable patch; a security-triggered pin move is followed by an explicit version tag. The section then lists eight verification steps, each read back, written out here because the source list sits only in planning scratch: (1) the manifest and the lock move only electron and what the new version requires; (2) the integrity hash is re-read equal to the registry by an adversary agent; (3) `ELECTRON_FLOOR` is raised ONLY if an advisory demands it (clause 4), never to the pin by habit - this replaces the recommendation's "floor raised"; (4) the THIRD_PARTY.md row is re-read; (5) `npm audit` reads 0 vulnerabilities; (6) `node --test` and `tests/shell` are green; (7) on EVERY move the main checkout's runtime is refreshed with the companion closed and the clause 7 read-back prints `True True`; (8) for a MAJOR move only, never for a patch move and not exercised by this unit: the breaking-changes page is read for every API in the `require("electron")` list at shell/main.js:32-42, and one real run is made (U-099.3 adds the fuse re-probe to this step).
11. Negative (D23): no launch-time runtime check exists - `git diff --name-only` for the unit names no file under shell/lib/, shell/main.js, shell/preload.js or scripts/. No ADR is added and no line is added to CS-NEXT-SESSION.txt for the policy. No tray label, shortcut refusal, shell/.npmrc, pin module or verify_env row. The remedy text scripts/make_shortcut.py prints when the runtime is absent (lines 765-767: `npm install`, then `node -e "require('electron')"`) therefore stays as it is, although it differs from the clause 8 wording; the ledger entry records that it was left, why (no scripts/ edit under D23) and whether the measured clause 8 command makes it wrong.
12. Commands: bare `node --test` from inside shell/ ends `fail 0`; `tests/shell` whole through fleet_suite_gate.py ends 0 failed; `tools/drift_guard.py` exits 0.

## CS-1439

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-107. Class: process. Lane flag: false (not eligible: the web owner lane builds all three parts, serially; U-107.1 is NOT parallel-safe, see Data corrections; D94 hub-component rule). Planned minutes: 330 (3 parts (120 + 115 + 95; the record says 110 + 115 + 95)).
Depends on: none.
Wave: W2 by ruling P4F-1 (the plan's wave lists place U-107.1 and U-107.2 in W1 and U-107.3 in W2; P4F-1 and P4F-21 hold U-107.1 and U-107.2 out of wave 1, filed or not: one builder builds U-107.1, U-107.2 and U-107.3 in that order in U-107.3's slice, as three local commits, and the landing slice lands them together).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): U-107.1 in W1: `clockspeed/surface/web/app.js` 1/2, `tests/surface/` `test-panel_diagnostics` 1/2; U-107.2 in W1: `clockspeed/surface/server.py` 3/3, `clockspeed/surface/web/app.js` 2/2, `tests/surface/` `test-panel_diagnostics` 2/2, `tests/surface/test_server.py` 3/3.
Write-list:
- U-107.1 (W1-G1-S1 in the plan's wave list, held by P4F-1: built in U-107.3's slice, 120 min): `clockspeed/surface/web/` `panel_diagnostics`, `tests/surface/` `test-panel_diagnostics`, `clockspeed/surface/web/app.js`
- U-107.2 (W1-G2-S1 in the plan's wave list, held by P4F-1: built in U-107.3's slice, 115 min): `clockspeed/surface/web/index.html`, `clockspeed/surface/server.py`, `tests/surface/test_server.py`, `clockspeed/surface/web/app.js`, `tests/surface/test_web_assets.py`, `tests/surface/` `test-panel_diagnostics`
- U-107.3 (W2-G1-S1, 95 min): `tools/dashboard_probe.py`, `tests/test_dashboard_probe.py`
Slice 0 of the frame row (D68, D94; the spec's ROADMAP line): filed in the same commit as the frame row, CS-1434 (plan key U-053), whose first part depends on U-107.3. Landing rule: clause 12 below.
Departure, recorded in the leaf as the spec requires (the plan's Data corrections, verbatim):
DEPARTURE from D68 item 1 and from R-structure-1 acceptance 2, recorded here and in the leaf because NO ruling carries it (UNVERIFIED as ruled; it needs the adjudicator's confirmation before dispatch). Decision: part 1 (0A) also edits `app.js` additively and the panel reads `data.probes` and `data.world`, not `data.health`. Alternatives: (a) 0A writes only the two new files and the panel reads `data.health` and `data.world` - it cannot show the same Endpoints rows, because `bodyData` drops the HTTP code, status word, `blocked_by` and `detail` (first trap); (b) the panel fetches for itself - refused by `test_no_panel_module_issues_its_own_fetch`. Why: clause (b) of the recommendation ("the same Endpoints rows") is only reachable through a new seam key. Consequence: U-107.1 writes a hub file, so it is a web-lane slice and is not built beside another `app.js` writer.

### Acceptance

`MOD` is `clockspeed/surface/web/panel_diagnostics.js`; `TPD` is `tests/surface/` test-panel_diagnostics.py; `app.js` and `index.html` are the files under `clockspeed/surface/web/`. Fixed values: panel id `diagnostics`; seam key `probes`; sentinel id `panels-reading`; sentinel text `reading ...`.
1. (a) `TPD::test_the_page_holds_no_section_between_the_header_and_the_panel_host`: comment-stripped `index.html` holds zero `<section`, zero `<table`, and none of the nine ids `probe-note endpoint-rows world-note world-facts count-scroller count-table count-rows unmodeled-note unmodeled-list`; it still holds `pin`, `refresh`, `badge-registry`, `badge-world`, `panels`.
2. (b) `TPD::test_the_seam_publishes_one_fact_row_per_route`: under node, `panelData(probes).probes` is an array with one row per `ROUTES` row, in `ROUTES` order, each row holding exactly the keys `template, method, http, status, pill, blocked_by, source, detail`. `http` is the code as text, `unreachable` or `not probed`; `source` is `probed` or `/api/health`; `blocked_by` is `-` when the body names none; `detail` is the body's `detail` when it is a string, else null. `panelData({})` yields every row `not probed` and does not throw.
3. (b) `TPD::test_the_panel_renders_one_endpoint_row_per_fact_row`, ``test-the_note_counts_follow_the_rows`` and ``test-the_panel_renders_the_world_facts_counts_and_unmodelled_note``: mounted through `panel_harness.mount`, the panel shows the six columns (Route, Method, HTTP, Status, Blocked by, Read from) per row, the note sentence clockspeed/surface/web/app.js:289-296 builds today with its three numbers computed from the rows, the masked token plus the five scalars (clockspeed/surface/web/app.js:135-141), the five counts (clockspeed/surface/web/app.js:126-132) and the two unmodelled note wordings (clockspeed/surface/web/app.js:461-474), from `data.probes` and `data.world` only.
4. (c) `TPD::test_the_seam_script_holds_no_diagnostic_renderer`: comment-stripped `app.js` holds none of `renderEndpoints`, `renderWorld`, `COUNT_LABELS`, `WORLD_SCALARS`.
5. (d) `TPD::test_every_probe_failing_renders_the_refusal_text`: every row `unreachable` and `data.world` null gives state `mounted`, the World note `unreachable - /api/world did not answer`, the line `no world loaded`, a hidden count scroller. `tests/surface/test_panel_seam.py::test_a_panel_that_throws_does_not_stop_the_others` passes unedited. NEGATIVE `TPD::test_an_all_null_payload_mounts_and_says_no_probe_result`: `panel_harness.null_payload()` (no `probes` key) mounts and prints `no probe result was handed to this panel`.
6. (e) `TPD::test_swapping_two_script_tags_changes_the_section_order_and_nothing_else`: in a tmp copy of the web dir, swap the `panel_diagnostics.js` and `panel_advice.js` tags; the host's child ids swap `panel-diagnostics` and `panel-advice`, every other position and every `data-panel-state` is unchanged.
7. (f) `tests/surface/test_panel_global_scope.py::test_no_panel_module_adds_a_global`, `::test_the_module_is_wrapped_in_an_iife` and `::test_no_shipped_panel_module_holds_a_regular_expression_literal` pass unedited with MOD present; `tests/surface/test_panel_seam.py::test_no_panel_module_issues_its_own_fetch` passes unedited.
8. (g) `TPD::test_the_host_ships_one_non_heading_reading_line`: `<div id="panels">` holds exactly `<p class="note" id="panels-reading">reading ...</p>` and no heading; `TPD::test_the_seam_removes_the_reading_line_where_it_creates_a_section`: the brace-matched body of `panelSection` names `PANEL_SENTINEL` and calls `removeChild`. BEHAVIOUR, under node with a private stand-in whose nodes set `parentNode` on `appendChild`: `TPD::test_the_first_section_removes_the_reading_line` (the sentinel is no child of the host after the first `panelSection` call, and a second call does not throw) and `TPD::test_an_absent_reading_line_does_not_stop_a_mount` (a host with no sentinel: `mountPanels` mounts every panel, none `failed`). The comment at clockspeed/surface/web/index.html:130-140 no longer says `EMPTY AT REST` and states the slot is reserved by that one line. Clause (g) also needs the 5-phase visual audit (CONVENTIONS 13.2), handed over in the part 3 report for the landing slice's ledger entry: no panel above the diagnostics slot moves when the rows replace the sentinel, and the audit records the keyboard route at first paint (none to the endpoint table until the first mount; Tab reaches it after).
9. (h) `tools/dashboard_probe.py::REQUIRED_NODE_IDS` is byte-identical to HEAD (294-306, eleven literals). `tests/test_dashboard_probe.py::test_the_required_nodes_are_the_ones_the_page_script_asks_for` reads `app.js` plus MOD; `::test_the_required_nodes_are_all_declared_by_the_page_it_grades` grades `document_ids(index.html) | script_ids(MOD)`; NEW ``test-a_planted_missing_id_reddens_the_asked_for_arm`` and ``test-a_planted_missing_id_reddens_the_declared_arm`` plant `clockspeed-probe-planted-missing` and read it back as the one failure. `dom_stage` fetches `/panel_diagnostics.js` as a second exchange and grades each id against the union; a dead or wrong-typed module exchange is one FAIL finding naming `/panel_diagnostics.js` (the form `_exchange_finding` gives the document, tools/dashboard_probe.py line 1045) and the ids are then graded against the document alone. `TPD::test_the_panel_builds_every_diagnostic_id_by_literal_assignment` finds exactly twelve `.id = "<literal>"` assignments in MOD, and `script_ids(MOD)` equals that set: the nine ids of clause 1 plus the three heading ids `h-endpoints`, `h-world`, `h-unmodeled`.
10. (i) In `tests/surface/test_web_assets.py`, six arms: `test_the_wide_table_scrolls_inside_its_own_container` requires zero tables in `index.html` and, in comment-stripped MOD, two `"table"` and two `"scroll-x"` literals; `test_every_tabindex_is_a_scroll_container_at_the_default` adds that MOD holds no `tabindex`; `test_every_focusable_scroller_carries_its_own_accessible_name` reads the stems `Endpoint routes` and `World counts` off MOD's `setAttribute("data-scroll-label", ...)` calls; `test_a_numeric_column_header_shares_the_alignment_of_its_cells` finds the `th` built with class `count` in MOD; `test_the_script_renders_the_blocking_item_id_as_text` requires `body.blocked_by` and `blocked_by: blockedFor(` in app.js and a `.textContent = <name>.blocked_by` assignment in MOD; `test_the_page_shows_the_masked_token_and_the_world_scalars` (tests/surface/test_web_assets.py line 2430) reads comment-stripped `app.js` plus MOD for the quoted keys `world`, `counts`, `unknown_classes`, `header_version`, `save_version`, `build_changelist`, `body_offset`. Each is shown red once on a MOD copy with the graded literal (for the sixth, one key) removed.
11. `PANEL_MODULES` (tests/surface/test_web_assets.py lines 77-87), the script tags (clockspeed/surface/web/index.html:157-165), `STATIC_ROUTES` (clockspeed/surface/server.py lines 208-221) and the name list (tests/surface/test_server.py lines 2933-2945) each gain `panel_diagnostics.js`; it is FIRST after `app.js` in the page and in `PANEL_MODULES`. NEGATIVE: `tests/surface/test_panel_scope.py` passes with zero edits (`git diff --stat` names it nowhere); `TPD::test_the_panel_reads_no_refusal_envelope` finds no `body.` or `refusal.` member read in MOD; `TPD::test_the_panel_types_no_blocking_item_id` finds no `pending.BLOCKERS` value in MOD.
12. Landing (D99 items 8 and 9, D-SEQ-8): the three parts are three LOCAL commits and no builder push. The part 3 report lists the two NEW tracked files by path. The wave's landing slice, not a builder, stamps their `tools/provenance.tsv` rows, writes the ledger entry, and runs once: the whole suite through `fleet_suite_gate.py run`, `.venv/Scripts/python.exe tools/dashboard_probe.py` (exit 0) and `.venv/Scripts/python.exe tools/provenance_stamp.py check` (exit 0). 0A lands with 0B in the same wave (D68).

## CS-1440

### Filed 2026-11-25 by the session 161 wave 0 filing

Plan key: U-131. Class: product. Lane flag: false (not eligible). Planned minutes: 310 (3 parts (110 + 110 + 90; the record agrees)).
Depends on: none.
Wave: W3, W4, W5 (each part's wave or slice is in its Write-list line).
Hub chains (order read from the plan's wave lists; U-141 fills the annex chain column): none; no part shares a file with another unit of its wave.
Write-list:
- U-131.1 (W3-G2-S2, 110 min): `clockspeed/data/locate.py`, `tests/data/test_locate.py`, `clockspeed/advisor/ledger.py`, `tests/advisor/test_ledger.py`, `clockspeed/save/workdir.py`, `tests/save/test_workdir.py`, `tests/conftest.py`, `tests/data/` `test-data_root`
- U-131.2 (W4-G2-S2, 110 min): `clockspeed/surface/config.py`, `tests/surface/test_config.py`, `clockspeed/data/assets.py`, `tests/data/test_assets.py`, `clockspeed/surface/__main__.py`, `tests/surface/test_routes.py`, `tests/data/` `test-data_root`
- U-131.3 (W5-G1-S2, 90 min): `shell/lib/endpoint.js`, `shell/test/endpoint.test.js`, `tests/data/` `test-data_root`

### Acceptance

Names fixed here. In clockspeed/data/locate.py: `ENV_DATA_ROOT = "CLOCKSPEED_DATA_ROOT"`; `DATA_ROOT_FOLDERS = ("data", "work", "certs", "config", "logs", "run", "shell")`; `DATA_ROOT_REFUSAL` (one fixed line naming the variable); `DataRootError(ValueError)`; `data_root(env: Mapping[str, str] | None = None) -> Path | None`. In clockspeed/save/workdir.py: `refuse_forbidden_root(path: Path) -> None`. Sites under a set root: ledger `<root>/data`, work `<root>/work`, certificates `<root>/certs`, local config `<root>/config/local.json`, header index `<root>/data/header_index.json`.
1. `test-data_root_is_none_when_the_variable_is_unset_or_blank` in `tests/data/test_locate.py` and `test-data_root_returns_the_declared_absolute_drive_path`.
2. `test-a_relative_driveless_unc_or_drive_root_data_root_is_refused_without_echoing_it` - parametrised; each raises `DataRootError` whose text equals `DATA_ROOT_REFUSAL` and holds no fragment of the value (assert on a boolean). Shape only: a drive of the form letter plus colon, absolute, not the drive root. Further arms in the same table: a value holding a `..` segment is refused; a trailing separator and a lower-case drive letter are accepted and give the same path as the plain form (compare booleans).
3. `test-the_data_root_resolver_imports_nothing_above_the_data_layer` (AST of locate.py) and `test-data_root_creates_nothing`.
4. `test-local_config_path_is_config_local_json_under_the_data_root` and `test-the_local_config_variable_beats_the_data_root` (`ENV_LOCAL_CONFIG`, clockspeed/data/locate.py line 95).
5. `test-the_default_store_dir_is_data_under_the_data_root` in `tests/advisor/test_ledger.py`; the existing ::test_the_default_store_dir_is_the_gitignored_data_dir (:360) and ::test_the_default_store_dir_uses_no_private_import (:724) stay green unedited.
6. `test-work_root_is_work_under_the_data_root_below_the_variable_and_the_config_key` in `tests/save/test_workdir.py` - order: `ENV_WORK_ROOT`, then the `work_root` key of local config, then the data root, then `<repo>/work`.
7. `test-refuse_forbidden_root_refuses_a_root_inside_the_game_install` in `tests/save/test_workdir.py`, ::..._inside_the_save_root, ::..._inside_a_relocated_account_directory (the fixtures of :296-:320), `test-refuse_forbidden_root_refuses_nothing_on_a_machine_with_no_game`, `test-refuse_forbidden_root_refuses_when_a_present_root_will_not_resolve`, `test-refuse_forbidden_root_creates_nothing`, `test-refuse_forbidden_root_refuses_a_root_equal_to_the_game_install_or_the_save_root`, `test-refuse_forbidden_root_refuses_a_case_variant_and_a_dot_dot_path_into_a_forbidden_root`. Each refusal is the existing `DestinationRefusedError` (:148).
8. `test-the_suite_runs_with_the_data_root_variable_removed` in `tests/data/test_locate.py` - the test starts a child `python -m pytest` on one probe arm of the same module with the variable SET in the child's environment (to a tmp_path value, never printed); the probe asserts the name is absent from `os.environ`, and the outer test asserts the child's exit code is 0. Red before the edit: the child exits 1 because conftest leaves the variable in place; asserting absence in the parent alone is vacuous, since a builder's environment never holds it. tests/conftest.py removes the variable at import (one line at the foot, placed like the import-time idiom at :1644, which is an assignment and not a removal), so no machine setting can move the suite's writes.
9. `test-the_certificate_directory_is_certs_under_the_data_root` in `tests/surface/test_config.py` and `test-the_certificate_variable_beats_the_data_root` (through the `env` mapping of `cert_dir`, clockspeed/surface/config.py line 368).
10. `test-the_artifact_lands_under_data_in_the_data_root` in `tests/data/test_assets.py`; the existing arm at :299 stays green.
11. `test-a_forbidden_data_root_stops_the_service_with_a_fixed_line_and_the_config_exit_code` in `tests/surface/test_routes.py`, `test-a_malformed_data_root_stops_the_service_without_echoing_it`, `test-an_unset_data_root_never_calls_the_forbidden_root_check`, `test-the_forbidden_root_check_runs_once_and_before_the_configuration_loads`. Exit code is the existing `EXIT_CONFIG`; stderr is a fixed line naming the variable, never `str(exc)`.
12. NEGATIVE, by command: `git grep -l "refuse_forbidden_root" -- clockspeed` prints exactly clockspeed/save/workdir.py and clockspeed/surface/__main__.py; `git grep -c "CLOCKSPEED_DATA_ROOT" -- shell/main.js` prints nothing (the shell never pins userData from the bare variable; that pin is U-132's).
13. shell/test/endpoint.test.js (`node --test` in shell/): "the certificate directory is certs under the declared data root", "the declared certificate directory beats the data root", "a malformed data root is a named refusal and never a fallback" (a new `EndpointFault` member, `DATA_ROOT_SHAPE`; LIBRARY LEVEL ONLY: shell/main.js:647-651 calls `certPath()` inside a bare catch and folds any throw into its certificate-unreadable path, and main.js is not written here), "the data root variable name matches the Python module" (read from clockspeed/data/locate.py, extraction asserted before comparison).
14. `test-the_precedence_matrix_holds_at_every_site` in `tests/data/` test-data_root.py - one table, five sites by four levels (explicit argument, specific variable, data root, clone default); a level a site does not have is written `n/a` in the table, never skipped. `test-every_site_equals_its_clone_default_with_the_root_unset`, `test-every_site_sits_under_the_root_with_only_the_root_set`, `test-resolution_alone_creates_no_directory` (the tmp root is still empty after all five are asked). `test-every_site_resolver_propagates_the_malformed_root_refusal` - with a malformed value set and no higher level set, `default_store_dir`, `work_root`, `cert_dir`, `artifact_path` and `local_config_path` each raise `DataRootError` whose text equals `DATA_ROOT_REFUSAL`, never a fallback to the clone default. The matrix module and its potency control (swap two levels in a copy of the table and assert the arm reports it) land in U-131.1 with the rows of the sites that part moves; each later part adds its sites' rows in the part that moves them, so no site lands without its precedence row.
15. Docs: `grep -c "CLOCKSPEED_DATA_ROOT" docs/OPERATIONS.md` prints at least 1 (a row in the table at :226-238); docs/ARCHITECTURE.md names the seam; tests/test_architecture_attributions.py, tests/test_docs_citations.py and `python tools/drift_guard.py` pass.
