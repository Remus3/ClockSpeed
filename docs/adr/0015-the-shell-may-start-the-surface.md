# ADR 0015 - The shell may start the surface, and stops only what it started

## Status

`accepted` - 2026-09-05.

## Context

**`docs/OPERATIONS.md` section 8 stated the constraint this decision breaks, in one
sentence: the companion LOADS the dashboard and does not start one.** That sentence was
true of the launch path it was written against. Section 8.1 is an order of operations in
which every step is a command typed into a shell, in two different directories, and
nothing in the shell has ever started a process.

**A one-click desktop shortcut cannot honour that sentence and still be one click.** The
operator double-clicks one icon and expects a loaded window. Something behind that icon
therefore has to decide whether a dashboard is already listening and start one when it is
not. The open question is not whether the sentence survives - it does not - but which side
of the seam owns the decision, and what that side is allowed to STOP.

**WHY ELECTRON OWNS IT AND NOT PYTHON, and the reason is a decision already recorded
rather than a preference.** The obvious alternative is a Python launcher that starts the
server, spawns Electron and supervises both. It founders on the tray.

- The tray is not optional here. It is what makes closing the window mean HIDE rather than
  QUIT, and that behaviour is most of what a desktop shortcut is being added to get.
- A tray in Python needs a GUI dependency. `pyproject.toml` declares `dependencies = []`
  and states that as a decision rather than an omission, so taking one on is not a small
  choice made inside this item - it is a re-litigation of that decision, and it would be
  made to obtain something the other side of the seam already has.
- Electron ships a tray, on a process that has to exist either way.

**ONCE THE TRAY OWNS QUIT, IT OWNS THE SERVER'S LIFETIME.** A Quit that closes the window
and leaves behind a server the same launch started is a leak the operator cannot see: no
window, no tray icon, and a port still held with nothing on screen to explain it. The
alternative that keeps the spawn in Python - the tray asking Python to quit over IPC - is
strictly worse than spawning. It adds a control channel into the server process, and a
channel that can stop the server is a larger thing to get right, and to keep closed, than
a child handle the parent already holds.

## Decision

**Electron owns application lifecycle and MAY spawn the surface. It stops ONLY what it
started.**

- On launch the shell asks whether a dashboard is answering. If one is, it is ADOPTED:
  nothing is spawned, and quitting the companion leaves that dashboard running exactly as
  it was found. If none is, the shell spawns one, OWNS it, and stops it on quit.
- **Adoption is the reading of the ambiguous case.** A dashboard the operator started is a
  dashboard the operator is using - possibly from a browser, possibly deliberately left
  running - and stopping it on quit would be the shell reaching outside its own launch to
  end something it never began.
- **The decisions live in `shell/lib/supervisor.js`, and `shell/main.js` stays wiring.**
  That is ADR 0014's repair applied before the fault rather than after it. `shell/main.js`
  imports Electron, so no test in either language can execute a line of it - which is
  CS-619 - and a decision written there is a decision nothing grades. A supervisor module
  that imports no Electron loads on a bare Node and is graded by `node --test`.
- The tray follows the same split, in `shell/lib/tray.js`. **Its icon may not be a tracked
  binary.** Measured 2026-09-05: no tracked file in this repository carries a NUL byte, and
  `tests/shell/test_shell_assets.py` holds every byte under `shell/` at or below 0x7E. The
  icon therefore ships as an ASCII data URL rather than as a file, and adding an image file
  to buy a nicer icon would be spending a property this repository currently has for free.

## Consequences

**`shell/` gains a runtime relationship to the Python side, which it did not have.** Until
now the seam was a URL: the shell loaded a page and knew nothing about the process serving
it. It now holds a child handle, an adoption verdict and a stop path, and each of those
can be wrong at runtime rather than at load. The mitigation is the split above - the parts
that DECIDE are graded on a bare Node, the parts that call Electron are wiring - and it is
a mitigation rather than a proof.

**REFUSAL PATHS THAT PRINT TO STDERR AND EXIT ARE INVISIBLE UNDER A SHORTCUT LAUNCH, AND
MUST BECOME DIALOGS.** Every refusal this shell can reach today was designed for an
operator watching a terminal, because the only documented launch ran inside one. A
shortcut has no terminal. A missing certificate, a port that will not bind, a spawn that
fails and a dashboard that never answers all collapse into the same thing: an icon that
was double-clicked and no window. That is worse than the fault it hides, on ADR 0014's own
ground that a refusal is legible and a hang is not.

**THE FIRST LAUNCH ON A COLD CLONE NEEDS THE NETWORK, AND THE RUNBOOK SAID OTHERWISE.**
Measured 2026-09-05 against the version `shell/package.json` pins: the `electron` package
ships no `scripts` block at all, so `npm install` runs no postinstall, fetches no runtime
binary and exits 0 in about half a second. The binary arrives lazily, on the first
`require("electron")`. Under a shell that is a long silence an operator can sit through;
under a shortcut it is an icon that does nothing for minutes, and an exception instead of a
window when the machine is offline. `docs/OPERATIONS.md` section 8.1 step 3 asserted that
the install downloads the binary until this date, and is corrected in the same change that
accepts this ADR.

**What this decision does NOT decide**, recorded rather than left to be assumed by whoever
implements it:

- **It does not decide HOW liveness is answered**, nor what happens when two launches race
  to answer it. The probe, any lock, and the window between deciding to spawn and having
  spawned are all open questions this ADR deliberately leaves open.
- **It does not decide how the surface is invoked** - which interpreter, from which
  directory, with which flags - and nothing here licenses a hardcoded one.
- **It does not decide anything about the certificate.** ADR 0014 stands unchanged, and a
  spawned dashboard is trusted by exactly the same pin as an adopted one.
- **It does not make the shortcut the only launch path.** The manual sequence in
  `docs/OPERATIONS.md` sections 7.2 and 8.1 stays, stays supported, and still starts
  nothing by itself.
- **It does not decide auto-start at login, and it does not touch the in-game overlay**,
  which remains a settled later mode of this same shell.
- **It does not weaken the never-write rule.** Spawning a reader is not writing: nothing
  here reaches the game install or the save directory.

**Revisit if** the surface grows a second process, if the shell needs to supervise
something it did not spawn, or if a Python-side tray stops costing a dependency.

ADR 0013 cleared Electron for this use and ADR 0014 decided what it trusts. This decision
consumes both verdicts and restates neither.
