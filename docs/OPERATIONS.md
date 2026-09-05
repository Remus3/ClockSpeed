# Clockspeed - Operations

**Owner file for:** commands, the fresh-clone bootstrap, verification policy in operator
terms, ports, MCP re-wire, and runbooks.

**This file never contains:** architecture or rationale (those are
`docs/ARCHITECTURE.md` and `docs/adr/`), and never restates a measured value that a
machine already checks. Where a number is machine-owned, this file points at the owner.

Commands below use `python`, and that is not interchangeable with `py -3`. **The two
resolve to DIFFERENT installations on this machine and only `python` can import ruff,
pytest or mypy** - `BOOTSTRAP.md` section 2.5 measured it, and CS-806 was filed when a
session ran the tier-0 lint gate as written and read the module error as not-applicable.
`scripts/verify_env.py` now HARD-fails under an interpreter that cannot import them, so
run it to settle which one you are on rather than trusting a version string - both
report the same version. Never write the interpreter's absolute path into a tracked
file.

---

## 1. Fresh-clone bootstrap - run this first, in this exact order

> **A FRESH CLONE RUNS ZERO PROTECTION UNTIL SOMEONE WIRES IT.**
>
> Git hooks are configured through `core.hooksPath`, which is local git config and is
> **not tracked**. The MCP wiring and the local settings are untracked as well. Cloning
> this repo gets you the hook *scripts* and none of the *enforcement*. Until step 1 below
> has run in that clone, every gate in this project is inert - and an inert gate is worse
> than an absent one, because it is trusted.

```
python scripts/install_hooks.py        # sets core.hooksPath, installs .githooks/
python scripts/verify_env.py           # asserts interpreter, toolchain, paths, ports
python tools/memory_sync.py            # mirrors markdown memory into the recall store
```

The order is not arbitrary:

1. `install_hooks.py` first, so protection exists before anything else can be committed.
   It takes no arguments, is idempotent, and **fails loudly** if `core.hooksPath` cannot
   be set. A silent failure here is the exact scenario this ordering prevents.
2. `verify_env.py` second, so a missing hard dependency is found before any work starts.
   It takes no arguments, supports `--json`, and exits non-zero on any missing hard
   dependency.
3. `tools/memory_sync.py` third, because recall is only useful once the environment it
   describes is known good. It is idempotent - it updates in place by category plus key
   and never duplicates.

### 1.1 Prove the hooks fire - presence is not firing

Installation is not proof. The only valid test is end to end:

```
stage a file containing a banned character
attempt a REAL commit
assert HEAD is unchanged
```

If HEAD moved, the gate did not fire. Before concluding anything about why, eliminate the
four standard confounds: invalid JSON in the settings file (a single-backslash Windows
path is enough), an untrusted workspace silently discarding the permission allowlist,
per-path-string config keying (`C:\X`, `C:/X` and `C:/x` are three different keys, and
each worktree path is its own key), and the general case that presence is not firing.

---

## 2. Command table

| Task | Command |
|---|---|
| Install git hooks (idempotent) | `python scripts/install_hooks.py` |
| Verify environment | `python scripts/verify_env.py` |
| Verify environment, machine-readable | `python scripts/verify_env.py --json` |
| Run the commit gate over the staged set | `python tools/precommit_gate.py --staged` |
| Run the commit gate over specific files | `python tools/precommit_gate.py --files <path> [<path> ...]` |
| Run the commit gate over text on stdin (commit messages) | `python tools/precommit_gate.py --text-stdin` |
| Lint the files just edited | `python tools/edit_lint_check.py --files <path> [<path> ...]` |
| Run all drift guards | `python tools/drift_guard.py` |
| Check documentation size budgets | `python tools/doc_budget.py` |
| Mirror markdown memory into the recall store | `python tools/memory_sync.py` |
| Live-state probe (SessionStart injection) | `python tools/facts_probe.py` |
| Tier 1 tests - one area | `python -m pytest tests/<area> -q` |
| Tier 2 tests - full suite | `python -m pytest tests -q` |

Gate exit codes: **0 = pass, 1 = block.** Anything else is a gate malfunction and is
itself a blocking condition - do not interpret a crash as a pass.

**Never run a bare recursive test invocation from the repo root.** Always name the target
directory explicitly. A bare sweep from the root can walk runtime state directories and
destroy live locks or data.

---

## 3. Verification policy in operator terms (R5-R7)

Classify the change, then run **only** that tier. Running more is waste; running less is
the unrun gate where the bug hides.

| Tier | The change is | Run exactly this | Do NOT run |
|---|---|---|---|
| **0** | Cosmetic: a doc, a comment, a string, a non-runtime constant | The edit, plus a syntax check on the changed file | No suite. No restart. No visual audit. |
| **1** | Local logic inside one module | Syntax check, plus that module's tests only | The full suite. Other modules' tests. |
| **2** | Schema, engine, core algorithm, version bump, or a public interface | The full suite, plus a service restart, plus any mirror sync | Nothing is skipped at this tier. |

- **R5** - every change gets a tier before it gets a verification.
- **R6** - run the relevant suite ONCE and trust the exit code. Re-run only if you edited
  since, or the tool pipe demonstrably glitched. Never prophylactically.
- **R7** - **adversarial verification is the default, not the escalation.** Every
  substantive claim, including a single-threaded edit of your own, gets an independent
  refutation pass before it is called done. Tier 0 is the only exemption.

Two operational corollaries that have cost time before:

- Always syntax-check before restarting a background process. Under a windowless
  interpreter a syntax error crashes silently and presents as a hang.
- Never use a graceful process-stop cmdlet that can hang a tool pipe. Prefer a forced
  kill by PID.

---

## 4. Port allocation

**`config/ports.json` is the machine-checked source of the port record. Read it there.**

- **Base port: 8920** - the local HTTPS dashboard and JSON API.
- **Reserved band: 8920-8939** - held for this project.

Moved here from 8900-8911 on 2026-08-29. That band was wholly inside
LegionWallpaper's reserved 8900-8919 and its base 8901 was LW's monitor port.
It was picked by probing for a free listener, and LW's monitor is an
operator-launched GUI that is unbound most of the time, so the probe reported
the whole block free. A band is verified against the owning project's registry
in SOURCE, never against a live scan.

Free-or-bound status is **probed live by `scripts/verify_env.py`** and is deliberately
not written down as prose anywhere, here included. A port state recorded in a document is
a claim with a timestamp on it and no owner. If you need to know whether the band is
clear right now, run the probe.

The dashboard's certificate is self-signed and is generated by a tracked script into a
gitignored location. The certificate itself is never tracked.

---

## 5. MCP re-wire on a fresh clone

**`.mcp.json` is LOCAL and gitignored.** It does not arrive with a clone. Re-wire it
explicitly as part of setting up a new working copy:

```
claude mcp list                                  # what is wired right now
claude mcp add <name> -- <command> [args...]     # wire a stdio server
claude mcp remove <name>                         # unwire one
```

Wire only what this project actually needs. The typical set is the local semantic recall
store, a browser-automation server for UI work, a search or scraping server for research,
a language-server plugin, and a scheduled-task server if background jobs exist.

**Servers requiring interactive OAuth are unavailable in headless runs.** This is a
standing constraint, not an occasional annoyance:

- **No critical path may depend on an OAuth-gated server.** If a gate, a guard, a CI
  step, or a bootstrap step needs one, that step is broken by construction, because it
  cannot complete in an unattended session.
- Anything an OAuth-gated server provides must have a documented non-interactive
  fallback, or be classified as operator-only work.
- A headless run that reports an OAuth server as unavailable is behaving correctly. Do
  not "fix" it by embedding a token in a tracked file.

The recall store itself, its config and its wiring are local and gitignored; only
`tools/memory_sync.py` is tracked. A fresh clone therefore has no store until section 1
step 3 has run.

---

## 6. Runbook: the game patched

**Trigger:** the drift guard goes red on the build-string pin, or the game updates.

The pin and its content hash are tracked; the extracted registry is not. When the game
patches, the content hash changes, the guard goes red, and the re-extract runs. **That is
the intended workflow, not an incident.**

Steps:

1. Confirm the signal. `python tools/drift_guard.py` - it names the pin that moved.
2. Re-run the extractor and update the pin. **This is one command.**
   ```
   python -m clockspeed.data.docs_extract --reextract --update-pin
   ```
3. Re-run the tier-appropriate suite. A recipe or building change is a tier 2 change.
4. Record what moved in `docs/LEDGER.md` with an item ID and a verification pointer.

Two rules that govern this runbook:

- **If absorbing a patch requires editing rule logic, that is a defect in the rule.** The
  rule encoded a fact it should have read from data. Fix the rule to read the fact, do
  not patch the symptom.
- Never commit the extracted registry, the docs file, or anything else lifted out of the
  game install. The pin and the hash are the only tracked artifacts of this process.

Step 2's command is the committed shape of the workflow. The extractor itself is a phase
2 deliverable; when it lands it lands behind exactly that one-command interface.

---

## 7. Runbook: the local dashboard

**Trigger:** you want the JSON API and the dashboard running on this machine.

**The port is not written in this section.** `config/ports.json` is the owner and the
only place the number lives; section 4 says how to read it and
`python scripts/verify_env.py` probes whether it is free. A port restated in prose is a
claim with a timestamp on it and no owner.

### 7.1 Mint the certificate - once, before the first run

The listener is HTTPS only and refuses to start without a usable pair. The pair is
self-signed, generated by a tracked script into a gitignored location, and is never
committed.

```
python scripts/make_cert.py
```

It needs `openssl` on PATH - the one shipped with git will do. It refuses to overwrite an
existing pair unless given `--force`, because the companion window may already have been
told to trust the pair that is there. `--cert-dir <dir>` and `CLOCKSPEED_CERT_DIR` both
move where the pair is written.

**Its exit codes are not restated here.** `scripts/make_cert.py` owns them: one named
`EXIT_*` constant per outcome, with the table in its module docstring saying what each
means. This line used to carry a copy of that table and had already gone stale - the copy
was still listing the outcomes that existed before CS-878 added another one - which is
CLAUDE.md section 4 happening in slow motion. A runbook branching on the number reads it
from the script.

One behaviour worth knowing before you script around it: `--help` exits 0, the same status
a completed mint exits with, so a zero status ALONE does not tell you a certificate now
exists - you have to know which invocation produced it. That is the only shared status in
the script and it is deliberate rather than an oversight (CS-882): POSIX convention for a
successful `--help` was ruled to outrank giving every outcome a status of its own. Every
other outcome, a usage error included, has one to itself.

### 7.2 Start it

```
python -m clockspeed.surface
```

**The world is auto-detected on startup and no flag is needed to load it.** Detection is
lazy, so a machine with no save and no game installed still starts and still answers
every endpoint: the absence surfaces as a 503 from `/api/world` and as `absent` in the
`/api/health` body, never as a crash and never as a refusal to start.

| Flag | Does |
|---|---|
| `--port <n>` | Bind this port instead of the record's. Beats `CLOCKSPEED_DASHBOARD_PORT`, which beats the record. |
| `--cert-dir <dir>` | Read the pair from here. Beats `CLOCKSPEED_CERT_DIR`. |
| `--no-world` | Do not look for a save at all. `/api/world` then answers 503. |
| `--help` | Print the flags and exit 0. Works with no game installed and no save present. |

### 7.3 Exit codes

| Code | Means | Do this |
|---|---|---|
| `0` | Stopped cleanly - Ctrl-C, or the process was signalled. | Nothing. |
| `1` | The configuration would not resolve. | Read the message. A declared port that is not a base-ten integer, or that sits outside 0-65535, is refused rather than quietly ignored. |
| `2` | The port could not be bound. **No second port is ever attempted.** | The message names the port. Find what holds it, or pass `--port`. A dashboard silently moved elsewhere is one the operator cannot find and the companion window cannot reach, with nothing saying why. |
| `3` | The certificate pair would not load. | Mint it (7.1), or point `--cert-dir` at an existing pair. |

Anything else is a malfunction rather than a refusal, and is itself a blocking condition.

### 7.4 Stop it

Ctrl-C in the foreground. The listener is released on every exit path - including one
where the shutdown does not complete - so the port is free for the next start rather than
held by a process that has stopped answering on it.

---

## 8. Runbook: the companion window

**Trigger:** you want the Electron companion window running on this machine.

**Read section 7 first.** The certificate is minted by 7.1 and the dashboard is started by
7.2, and neither command is repeated here - a command restated in two places is a command
that will drift.

**The companion LOADS the dashboard and does not start one - EXCEPT from the desktop
shortcut in 8.4**, which starts one when none is answering and ADOPTS one that is. That
exception is the whole of `docs/adr/0015-the-shell-may-start-the-surface.md`, and it stops
only what it started. The manual order of operations in 8.1 starts nothing and never has.

### 8.1 Order of operations

1. **Mint the certificate**, if this clone has never minted one - section 7.1. **The
   companion pins the pair that is already there**, so re-minting is not a free action.
   Read the caching consequence in
   `docs/adr/0014-the-shell-trusts-one-pinned-certificate.md` before passing `--force`.
2. **Start the dashboard** - section 7.2. The companion has nothing to load until the
   listener answers.
3. **Install the shell's dependencies and launch the companion.** `shell/node_modules` is
   gitignored and does not arrive with a clone. The install is once per clone; the launch
   is every time.
   ```
   cd shell
   npm install
   npx electron .
   ```

   **`npm install` DOES NOT LEAVE YOU WITH A RUNNABLE ELECTRON, and this step said it did
   until 2026-09-05.** Measured on that date against the version `shell/package.json`
   pins: that `electron` package ships no `scripts` block at all, so there is no
   postinstall - the install resolves the dependency tree, fetches NO runtime binary, and
   exits 0 in about half a second. The binary is fetched LAZILY, by the package's own
   entry point on the first `require("electron")`, which means **the first `npx electron .`
   is the step that needs the network.** On a cold clone expect it to sit silently for
   minutes, and to THROW rather than open a window if the machine is offline. Re-measure
   if that pin moves. This matters more once a shortcut is the launch path - see 8.4,
   which has no terminal to be silent in.

   **There is no `npm start` here, and reaching for one fails.** `shell/package.json`
   declares a `test` script and no `start` script, so `npm start` reports a missing script
   rather than launching anything. Electron is invoked against the shell package directly
   instead, which is what that manifest's `main` field points at.

### 8.2 Where the window state lives

The companion remembers its position, its size and its always-on-top choice in a file
named `window-state.json`, written into Electron's `userData` directory for this
application.

**That directory is resolved at RUNTIME, and its absolute path is deliberately not written
down here.** It sits beneath the logged-in account's profile, so any path to it contains a
Windows account name - personal data under `CLAUDE.md` non-negotiable 3, which is why no
tracked file in this project spells one out. `shell/lib/state.js` is handed a directory
and never works one out for itself; ask Electron for `userData` if you need the location
on a particular machine.

Deleting that file is the supported reset. The next launch falls back to built-in defaults
rather than failing.

### 8.3 Checks that no machine performs

**CI has no display and never installs Electron. Nothing in this list is graded by any
test, any guard or any CI job, and no CI job may be shaped to imply that it was.** These
are the parts of CS-602's acceptance that only a human at a real display can settle.

**How to fill this in.** Every step carries an Observed line whose shipped value is the
literal token `NOT RUN`. Replace that token with what you actually saw, and the date you
saw it. A step whose Observed line still reads `NOT RUN` HAS NOT BEEN RUN - it is not
passed, not waived, and not evidence of anything. Do not delete the token to leave a
blank: an empty line is ambiguous and this one must not be. `docs/GATED.md` names closing
an item synthetically as a failure class, and recording an unrun check as a result is that
same failure wearing a different hat.

1. **Frameless.** The window has no OS title bar and no OS border.
   - Observed: 2026-09-05, at a real display - FRAMELESS as specified. No OS title bar and
     no OS border. This was the FIRST execution of the companion in this project's
     history: `shell/node_modules` did not exist until that day, so every claim about this
     window before it was a claim about source.
2. **Always-on-top raises.** With the option on, the window stays above other
   applications' windows when they are focused - not merely above its own siblings.
   - Observed: `NOT RUN`
3. **The pinned certificate is accepted over a real handshake.** The companion loads the
   running dashboard over TLS without a certificate warning and without any validation
   being disabled. A blank window, a hang, or a warning dialog each falsify this
   differently - record which one you saw.
   - Observed: 2026-09-05, at a real display, same run as check 1 - ACCEPTED. The companion
     loaded the running dashboard over TLS against the pinned certificate with no warning
     dialog, no blank frame and no hang, and with nothing disabled. None of the three
     falsifying outcomes occurred.
4. **Geometry survives a real restart.** Move and resize the window, fully exit the
   process, and launch it again. Reloading the window is NOT this check - the state is
   written on exit, so only a genuine process restart tests it.
   - Observed: `NOT RUN`
5. **The drag strip drags.** With no OS frame, the injected drag region is the only way to
   move the window. Confirm the window follows the pointer.
   - Observed: `NOT RUN`
6. **Deferral behaves as documented.** Navigate the companion to a host that is not the
   dashboard and confirm Chromium's own verification still applies - a bad certificate on
   that host must still be refused. This is the check that would catch a `callback(-3)`
   that does not mean what the prose documentation says; ADR 0014 records that the shipped
   typings do not state it.
   - Observed: `NOT RUN`

### 8.4 Launch it from the desktop

**Trigger:** you want the companion on one double-click rather than on the command
sequence in 8.1.

```
python scripts/make_shortcut.py
```

It writes a Windows shortcut onto the desktop pointing at this clone. `--desktop-dir <dir>`
writes it somewhere other than the desktop, `--name <name>` gives it a different name,
`--force` overwrites a shortcut that is already there, and `--help` prints the flags.

**Its exit codes are not restated here.** `scripts/make_shortcut.py` owns them, for the
same reason 7.1 gives about `scripts/make_cert.py`: a copy of a table is a table that goes
stale, and a runbook branching on a number reads it from the script.

**What one double-click does.** It opens the companion. If no dashboard is answering, the
launch starts one and OWNS it. If one IS answering - because you started it yourself in
7.2, or because an earlier double-click did - that dashboard is ADOPTED and left alone.
The decision and its fence are `docs/adr/0015-the-shell-may-start-the-surface.md`.

**Closing the window does not quit.** The companion keeps a system-tray presence and
closing the window HIDES it there. **Quit from the tray menu** is the exit: it closes the
window and stops the dashboard ONLY if this launch started it. A dashboard you started
yourself is still running afterwards, and 7.4 is still how you stop that one.

**A first double-click on a fresh clone may do nothing visible for minutes, or fail with
no window and no message.** Read step 3 of 8.1 before concluding the shortcut is broken:
the Electron runtime is downloaded on first use rather than at install time, and unlike
8.1 a shortcut has no terminal for that silence - or for a refusal - to appear in.

---

## 9. Windows discipline that bites operationally

### 9.1 Commit messages with special characters

**Write the message to a temp file and commit with `git commit -F <file>`.**

```
# 1. write the message to a temp file using a file tool, ASCII, LF endings
# 2. then:
git commit -F <path-to-message-file>
```

- **Never** a double-quoted here-string.
- **Never** a piped string.

Both carry BOM and ANSI mangling risk. The mechanism is worth remembering because it does
not present as an encoding error: PowerShell 5.1 ANSI-decodes a `.ps1` with no BOM, which
turns a UTF-8 dash inside a double-quoted string into a character the tokenizer treats as
a **string terminator**, and the failure surfaces later as a parse error somewhere
unrelated. One incident is enough to make the temp-file path permanent.

A single-quoted here-string is acceptable where a file is genuinely impractical. The
temp-file form is the default.

### 9.2 The rest of the Windows list

- **7-bit ASCII in all authored content** - code, comments, docstrings, markdown, commit
  messages, shell scripts, output. No em-dashes, en-dashes or smart quotes. Use a spaced
  hyphen ` - ` for a clause break. The commit gate enforces this; do not rely on noticing
  it yourself.
- **`write_text` converts LF to CRLF on Windows and `read_text` hides it**, so byte
  counts and hash comparisons taken through them lie. Write bytes explicitly whenever the
  byte count or the hash matters - which includes anything the drift guard checks.
- **Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`** in the environment so subprocess
  output does not mojibake.
- **Atomic writes for any file another process may read**: write a temp file, then
  replace the target. Retry the rename - on Windows it can transiently fail while another
  process holds a handle.
- **Never hardcode a machine name, a user account name, a numeric account id, a world
  name, or an absolute home path into a tracked file.** Auto-detect at runtime. These are
  simultaneously personal data and a drift source, and the tier-3 scan looks for them.
- Use a windowless interpreter for background daemons so no console window flashes.

---

## 10. Cross-references

- Module map, seams, card contract: `docs/ARCHITECTURE.md`
- Decisions and their fences: `docs/adr/README.md`
- Blocked outside the repo: `docs/GATED.md`
- Completion records: `docs/LEDGER.md`
