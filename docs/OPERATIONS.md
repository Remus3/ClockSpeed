# Clockspeed - Operations

**Owner file for:** the full install procedure (section 1.2; `README.md` keeps only the
quickstart and first result), commands, the fresh-clone bootstrap, verification policy in
operator terms, ports, MCP re-wire, and runbooks.

**This file never contains:** architecture or rationale (those are
`docs/ARCHITECTURE.md` and `docs/adr/`), and never restates a measured value that a
machine already checks. Where a number is machine-owned, this file points at the owner.

Commands below use `python`, and that is not interchangeable with `py -3`. **On the
maintainer's machine the two resolve to DIFFERENT installations and only `python` can
import ruff, pytest or mypy** - `BOOTSTRAP.md` section 2.5 measured it there, and CS-806
was filed when a session ran the tier-0 lint gate as written and read the module error as
not-applicable. Elsewhere it can differ: a fresh machine may hold several Pythons, and
`py -3` takes the newest, which can be above the supported range. To use the launcher
there, select a supported release explicitly - `py -3.14 -m venv .venv` - and inside the
activated virtual environment `python` is that release.
`scripts/verify_env.py` now HARD-fails under an interpreter that cannot import them, so
run it to settle which one you are on rather than trusting a version string - on the
maintainer's machine both report the same version. Never write the interpreter's absolute
path into a tracked file.

---

## 1. Fresh-clone bootstrap - run this after the 1.2 venv step, in this exact order

Create, activate and install the virtual environment first, as
[section 1.2](#12-install-and-run-from-scratch) does: `verify_env.py` counts `pytest` and
`ruff`, which the `dev` extra installs, as HARD.

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

Installation is not proof. The only valid test is end to end. It makes a real commit, and
on a machine with no git identity `git commit` stops at "Author identity unknown" before
any hook runs, which proves nothing - so if `git config user.email` prints nothing, run
`git config user.name "<name>"` and `git config user.email "<email>"` in the clone first.

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

### 1.2 Install and run from scratch

The full procedure behind the README's Quickstart, for a machine that has never run
Clockspeed. What it needs is the Requirements table in
[`README.md`](../README.md#requirements).

#### Installing the prerequisites

On a machine that has none of them yet, install from the official sources:

1. **Python** 3.13 or 3.14 - take the newest 3.14.x - from
   [python.org](https://www.python.org/downloads/windows/). The supported range is
   `requires-python` in [`pyproject.toml`](../pyproject.toml), and python.org's newest
   release can lie above it. The download page lists the Python install manager first
   and the releases below it. Take a release's "Windows installer (64-bit)" rather than
   the install manager: the install manager refused to install on Windows 10 build 19041,
   where the installer worked. On the installer page that carries **Install Now**, tick
   **Add python.exe to PATH** before you click it - the box is unticked by default, and
   without it the `python --version` check below fails.
   [python.org's Windows guide](https://docs.python.org/3/using/windows.html) marks that
   installer deprecated from 3.14 and says it will not be produced for 3.16 or later.
2. **Git** from [git-scm.com](https://git-scm.com/download/win). The installer defaults are
   fine.
3. **Node** from [nodejs.org](https://nodejs.org/), the LTS installer, only if you want the
   companion window or will run the test suite.

Open a new terminal afterwards and check:

```
python --version
git --version
```

`python --version` must print a version inside the `requires-python` range. If it does
not, `python` is not reaching a suitable install - follow python.org's official Windows
guide, <https://docs.python.org/3/using/windows.html>, then re-run the check.

**Interpreter:** `requires-python` in `pyproject.toml`; `scripts/verify_env.py` asserts
its floor, the toolchain and the game build, which `clockspeed/data/version.py` pins. Do not
restate a version or a build string in prose - read it from the pin, and let
`tools/drift_guard.py` catch drift. (Relocated on 2026-10-19 from `CLAUDE.md` section 2
under CS-1330, for its size budget.)

#### Install and run

Run every command below from the root of the clone, in the order given.

**Two kinds of clone, two starting points.** If you only want to run Clockspeed, this
section is the whole procedure and you can skip the rest of this file. If you will commit
from the clone, do the virtual-environment step below, then run the bootstrap in
section 1 above - it runs the same hook and environment
commands as the next two steps here, plus the contributor tooling - and continue here at
`python scripts/make_cert.py`.

Create a virtual environment, activate it, and install the project with its `dev` extra:

```
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

The block is the PowerShell form. A stock Windows PowerShell refuses the activation line
without the `Set-ExecutionPolicy` line before it - running scripts is disabled under its
default execution policy, and `python` then stays the base interpreter, so the install
lands outside the virtual environment. That line lasts only for that terminal and changes
no machine setting. In `cmd`, leave it out; in Git Bash, leave it out and activate with
`source .venv/Scripts/activate`.

`.venv/` is gitignored. The core itself has no runtime dependencies; the `dev` extra is
the toolchain the next steps check for.

Then:

```
python scripts/install_hooks.py
```

Points this clone's `core.hooksPath` at the tracked `.githooks/`. The next command counts
that setting as a HARD dependency, so in a fresh clone it fails until this has run.

```
python scripts/verify_env.py
```

Prints every dependency found and missing, split into HARD and SOFT. It exits non-zero
only on a HARD one. A missing game or save is SOFT: it is reported and does not fail the
check. Its `config/ports.json` row prints the dashboard's port.

`scripts/make_cert.py` needs `openssl`. Git for Windows ships it in `<Git install>\usr\bin`,
where `<Git install>` is the folder Git was installed into - the part before `/mingw64/`,
`/ucrt64/` or `/clangarm64/` in the path `git --exec-path` prints - but a default Git
install does not put that folder on PATH, and the script then exits 1 saying openssl is
not on PATH.
Unless `openssl version` already answers, append the folder to PATH for this terminal
first. In `cmd`:

```
set "PATH=%PATH%;<Git install>\usr\bin"
```

In PowerShell the same line is `$env:Path += ";<Git install>\usr\bin"`. Then:

```
python scripts/make_cert.py
```

The dashboard is HTTPS only and will not start without a certificate pair. The pair is
gitignored, so every fresh clone needs this once. Skip it and the next command exits 3 and
says why.

```
python -m clockspeed.surface
```

Starts the dashboard on the port recorded in `config/ports.json` - the entry under
`allocations`, which `scripts/verify_env.py` also prints - bound to this machine only. With no arguments it finds the newest save on
this machine and serves it. It prints nothing on startup, then logs one line per request,
and keeps the terminal until you stop it.

Its options, all optional, are the flag table in section 7.2
(`python -m clockspeed.surface --help` lists them).

**First result.** What a working start shows is the README's
[First result](../README.md#first-result).

A machine with no save and no game still starts and still binds; the absence is reported
as a status, not an error - `/api/health` reports the registry and the world as `absent`.
If the port is taken the process exits and names it. No second port is ever tried.

**A first ratio.** With a game installed, ask the solver for 30 Iron Ingot per minute
from iron ore. The parameters travel in the query string of a POST; `-k` accepts the
self-signed certificate and `-s` keeps curl's progress output out of the answer:

```
curl.exe -s -k -X POST "https://localhost:<port>/api/solve?targets=Desc_IronIngot_C=30&recipes=Recipe_IngotIron_C&raw_items=Desc_OreIron_C&byproduct_policy=balanced"
```

Type `curl.exe`, not `curl`: in Windows PowerShell `curl` is an alias for
`Invoke-WebRequest`, which refuses `-k`. `curl.exe` is the curl Windows ships, and the
line runs unchanged in `cmd`.

The answer lists each recipe with its exact machine count and the raw input per minute,
every rate as a `{"num", "den"}` pair. `/api/registry` lists the item and recipe
identifiers to ask about. Without a game there is no registry, and the route answers 503.

#### Pointing it at your game and saves

The install, the save folder and the account folder beneath it are found automatically.
To point Clockspeed somewhere else, set any of these environment variables before running
the commands above:

| Variable | Points at |
|---|---|
| `CLOCKSPEED_GAME_DIR` | The game install folder, such as `<your game folder>` |
| `CLOCKSPEED_SAVE_ROOT` | The folder holding the account folders, such as `<your SaveGames folder>` |
| `CLOCKSPEED_ACCOUNT_DIR` | The one account folder to read - a full path, or a folder name inside the save root |
| `CLOCKSPEED_LOCAL_CONFIG` | A JSON file whose `game_dir`, `save_root` and `account_dir` keys are read when the matching variable is unset |
| `CLOCKSPEED_CERT_DIR` | The folder holding the dashboard's certificate pair, instead of `certs/` in the clone. `scripts/make_cert.py` writes there and the dashboard reads there; `--cert-dir` beats it |
| `CLOCKSPEED_DASHBOARD_PORT` | The port the dashboard binds, instead of the recorded one; `--port` beats it |

A variable naming a folder that does not exist is reported as not found; it does not fall
back to automatic detection.

To check that an override resolved, run `python scripts/verify_env.py`: each location row
names the source it was resolved by, or reports it not found. The dashboard cannot tell
you - an override pointing at an empty folder and no game at all both show there as no
game installation found.

---

## 2. Command table

| Task | Command |
|---|---|
| Install git hooks (idempotent) | `python scripts/install_hooks.py` |
| Verify environment | `python scripts/verify_env.py` |
| Verify environment, machine-readable | `python scripts/verify_env.py --json` |
| Run the commit gate over the staged set | `python tools/precommit_gate.py --staged` |
| Run the commit gate over specific files | `python tools/precommit_gate.py --files <path> [<path> ...]` |
| Run the commit gate over a commit message on stdin - charset and secrets only | `python tools/precommit_gate.py --text-stdin` |
| Grade OUTBOUND text before it leaves this machine - personal data and credentials | `python tools/outbound_gate.py` |
| Lint the files just edited | `python tools/edit_lint_check.py --files <path> [<path> ...]` |
| Run all drift guards | `python tools/drift_guard.py` |
| Check documentation size budgets | `python tools/doc_budget.py` |
| Mirror markdown memory into the recall store | `python tools/memory_sync.py` |
| Stamp a NEW tracked file into the provenance manifest | `python tools/provenance_stamp.py add <path> --class authored --item CS-NNNN` |
| Record a rename or a removal in the manifest | `python tools/provenance_stamp.py mv <old> <new>` / `rm <path>` |
| Check every tracked file is accounted for | `python tools/provenance_stamp.py check` |
| Live-state probe (SessionStart injection) | `python tools/facts_probe.py` |
| Tier 1 tests - one area | `python -m pytest tests/<area> -q` |
| Tier 2 tests - full suite | `python -m pytest tests -q` |

Gate exit codes: **0 = pass, 1 = block.** Anything else is a gate malfunction and is
itself a blocking condition - do not interpret a crash as a pass.

**That legend is the COMMIT gate's, and `--text-stdin` is not an outbound check.** It
grades charset and secrets and reaches no personal-data class, so a pass from it says
nothing about a home path, an account name, an account id, a world name or a world
token in the same bytes. Text that is about to LEAVE this machine goes to
`tools/outbound_gate.py`, which answers safe-to-send rather than safe-to-commit and
returns its own closed exit set - documented in that module's docstring, and never
restated here.

**Every new tracked file needs a manifest row (CS-1165).** `tools/provenance.tsv` must
account for every tracked and untracked-unignored file, and `tests/test_provenance_manifest.py` reddens pre-push and CI for any file it does not
list. Stamp it with the tool in the same commit; never hand-edit the TSV, and never
answer a near-duplicate refusal by rewording the file - a refusal is the guard doing
its job. `bootstrap` is a one-time seed that refuses once the manifest exists, and refuses
too wherever HEAD's history or any ref ever held one (CS-1176). A deleted manifest is
restored with `git checkout <rev> -- tools/provenance.tsv` - restore BEFORE editing
any file - and never re-seeded, because a re-seed classifies every unstamped file as
authored.

**An edit committed while the manifest was absent (CS-1179).** If a file whose row
carries a `first-add:` basis was edited and committed while `tools/provenance.tsv` was
gone, the restore above leaves the re-seed arm red for that path, and that first-add row
stays red: its bytes changed across the gap, which is exactly the shape of a lift, and
forgiving it would forgive one. The recovery replaces the row, in one commit:

1. Copy PATH somewhere outside the repository, then `git rm -q -- PATH` - the tool's
   `rm` refuses a path that is still tracked or untracked-unignored.
2. `python tools/provenance_stamp.py rm PATH`
3. `git rm` deletes a directory it leaves empty, so recreate PATH's parent first -
   `mkdir -p "$(dirname PATH)"` in Git Bash, or
   `New-Item -ItemType Directory -Force (Split-Path PATH)` in PowerShell - then copy
   the bytes back to PATH and `git add -- PATH`.
4. `python tools/provenance_stamp.py add PATH --class authored --item CS-NNNN`, where
   CS-NNNN is the item the recovery commit is made under. The id is traceability, not
   evidence: `add` checks only that it is `CS-` and digits and appears in `ROADMAP.md`
   or `docs/LEDGER.md`, and refuses otherwise.
5. `git add -- tools/provenance.tsv` and commit, citing that same item.

What it does NOT do: it never turns the first-add row green - it swaps it for a
`stamped` row, which the re-seed arm does not grade. That row is a declaration with an
item id and a commit on it, the residual the module docstring of
`tests/test_provenance_manifest.py` already names (a hand-written row with basis
`stamped` passes that arm), so the recipe adds no capability a hand edit of the basis
cell lacked. The near-duplicate arm and `add`'s own refusals still grade the bytes. Run it
only for a file you authored; on anything else it is a false declaration on the record.

**Never run a bare recursive test invocation from the repo root.** Always name the target
directory explicitly. A bare sweep from the root can walk runtime state directories and
destroy live locks or data.

**The test suite needs Git for Windows' `usr\bin` on PATH.** It runs `openssl`, `bash`,
`sh` and other tools that Git for Windows ships in `<Git install>\usr\bin` - `<Git install>`
being the part before `/mingw64/`, `/ucrt64/` or `/clangarm64/` in the path
`git --exec-path` prints - and a default Git install leaves that folder off PATH, so part
of the suite then fails rather than skips. APPEND it, never prepend it, so the
Windows tools that share a name with one there (`find`, `sort`, `timeout`) keep
precedence: `set "PATH=%PATH%;<Git install>\usr\bin"` in `cmd`,
`$env:Path += ";<Git install>\usr\bin"` in PowerShell. Type it on its own line: chained
after the activation line with `&&`, `cmd` expands `%PATH%` before the activation runs,
and the suite then runs under the base interpreter.

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
2. Re-measure the live install and rewrite the pin. **This is one command.**
   ```
   python tools/drift_guard.py --re-extract
   ```
3. Re-run the tier-appropriate suite. A recipe or building change is a tier 2 change.
4. Record what moved in `docs/LEDGER.md` with an item ID and a verification pointer.

Two rules that govern this runbook:

- **If absorbing a patch requires editing rule logic, that is a defect in the rule.** The
  rule encoded a fact it should have read from data. Fix the rule to read the fact, do
  not patch the symptom.
- Never commit the extracted registry, the docs file, or anything else lifted out of the
  game install. The pin and the hash are the only tracked artifacts of this process.

Step 2's command is the committed shape of the workflow. It reads the installed build
string and the docs file, read-only, and rewrites only the generated pin block in
`clockspeed/data/version.py`; `clockspeed/data/docs_extract.py` has no command line of its
own.

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
   - Observed: 2026-09-05, at a real display - RAISES as specified. Launched with
     `--always-on-top`, the companion was still the window at its own centre point after
     another application - a browser, Opera - had been given focus. BOTH CONTROLS PASSED,
     and neither is optional: the centre point resolved to the companion while the
     companion itself held focus, which shows the probe can see the companion at all; and
     focus demonstrably moved away to the other application, which shows something else
     could have been on top. Without the second control this check cannot tell "stays
     above a focused window" from "nothing ever took focus from it".
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
   - Observed: 2026-09-05 - SURVIVES. The window was moved, the process was HARD-KILLED so
     that no close handler could run, and the companion was launched again; it reopened at
     its saved bounds, x 3024 and y 238 logical. THE KILL IS WHAT MAKES THIS EVIDENCE. A
     clean exit would have passed this check on the strength of the close handler alone,
     leaving the debounced write that runs while the window MOVES completely ungraded -
     and that write is the one an operator's geometry actually depends on, because a
     process that dies without warning is the case a close handler cannot cover. Geometry
     recovered after a kill can only have been persisted before it.
5. **The drag strip drags.** With no OS frame, the injected drag region is the only way to
   move the window. Confirm the window follows the pointer.
   - Observed: 2026-09-05 - DRAGS, REPORTED BY THE OPERATOR, who moved the window by its
     drag strip and confirmed it follows the pointer. Attributed to a person rather than
     to a measurement on purpose: a real pointer drag against a frameless window is not
     something anything in this project can generate, and a synthesised event that the
     window manager quietly declines to treat as a drag would look from the inside exactly
     like a passing check.
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

**Two environment variables also move what it does, and a flag always beats one.**
`CLOCKSPEED_DESKTOP_DIR` moves where the shortcut is written; `CLOCKSPEED_SHELL_DIR` moves
where the Electron runtime is looked for. The destination resolves in this order -
`--desktop-dir`, then `CLOCKSPEED_DESKTOP_DIR`, then the desktop Windows itself records,
then the conventional spelling under the profile - and `CLOCKSPEED_SHELL_DIR` has no flag
above it. **The script owns that order and states it**; what is written here is which
variables exist and which flag outranks which, because a variable nobody has heard of
cannot be reached for at all. Reach for `CLOCKSPEED_SHELL_DIR` when the clone you want a
shortcut for is not the clone you are running the script from.

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

### 8.5 Checks that no machine performs - the shortcut, the tray and the dashboard

**The rules of 8.3 apply here unchanged, and for the same reasons.** CI has no display,
never installs Electron, and cannot double-click anything. Nothing in this list is graded
by any test, any guard or any CI job, and no CI job may be shaped to imply that it was.
Every step carries an Observed line whose shipped value is the literal token `NOT RUN`; a
step still reading it HAS NOT BEEN RUN - not passed, not waived, not evidence of anything -
and the token is replaced with what was seen and the date it was seen, never deleted to
leave a blank.

**Why this list is separate from 8.3 rather than appended to it.** 8.3 grades CS-602's
acceptance, which is about the window itself. Everything below grades CS-909's, which is
about the tray, what closing means, and which dashboard a launch owns. CS-909's acceptance
clause demands a REAL ELECTRON RUN FROM A REAL SHORTCUT, and no arm in the suite can
perform one, so this is where that evidence lives. Until it existed, a reader working
through 8.3 would have concluded the only outstanding manual work was CS-602's four
remaining checks, because nothing in this document mentioned the rest.

**The ownership checks are the sharp ones.** 5 and 6 are a matched pair, and each is
nearly worthless alone: a Quit that stopped EVERYTHING would pass 5, and a Quit that
stopped NOTHING would pass 6. Only the two together say that the shell stops what it
started and leaves what it did not.

1. **The tray icon appears.** After a launch, the companion has a visible entry in the
   system tray, and its menu opens.
   - Observed: 2026-09-05 - PRESENT, CONFIRMED BY THE OPERATOR, who saw the tray entry and
     opened its menu. Attributed to a person: the notification area is drawn by the Windows
     shell, and nothing in this project can read back what it actually displayed.
2. **Closing the window hides it instead of exiting.** Closing the companion must leave the
   process alive with its window hidden, not terminate it.
   - Observed: 2026-09-05 - HIDES. A real close was delivered to the window, and all three
     of the following held afterwards: the process was still alive, the window was hidden
     rather than destroyed, and the dashboard was still answering. All three are recorded
     because any one alone is consistent with an outcome this check is meant to exclude -
     a process that survived with no window is not the same as a window that was hidden.
3. **A real double-click starts a dashboard and opens the window.** From a shortcut written
   by 8.4, with nothing answering beforehand.
   - Observed: 2026-09-05 - STARTS AND OPENS. With no dashboard answering, the shortcut was
     double-clicked; a dashboard was started by that launch and the companion window opened
     against it. This is the run CS-909's acceptance clause asks for: a real shortcut, a
     real Electron process, no terminal in the path.
4. **A second launch ADOPTS rather than spawning a second dashboard.** With a dashboard
   already answering, a shortcut launch must load that one and start nothing.
   - Observed: 2026-09-05 - ADOPTED. A dashboard was started by hand first, then the
     shortcut was launched; the companion loaded the dashboard that was already there and
     NO SECOND ONE WAS SPAWNED. The absence of the second listener is the measurement - a
     launch that spawned one and displayed it would have looked identical from the window.
5. **Quit stops a dashboard this launch started.** The tray menu's Quit, after a launch that
   started its own dashboard.
   - Observed: 2026-09-05 - STOPPED, CONFIRMED BY THE OPERATOR, who quit from the tray menu
     after a launch of the kind check 3 describes and found the dashboard no longer
     answering.
6. **Quit LEAVES a dashboard it merely adopted.** The tray menu's Quit, after a launch of
   the kind check 4 describes.
   - Observed: 2026-09-05 - LEFT RUNNING, CONFIRMED BY THE OPERATOR AND VERIFIED BY PROCESS
     ID. The hand-started dashboard was still answering after Quit, under the SAME process
     id it held before. The identity check is the whole of it: "still answering" alone
     cannot distinguish a dashboard that was left alone from one that was stopped and
     restarted, and only the first is the documented behaviour.

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

### 9.3 A load harness on this machine

Moved on 2026-10-21 from the CS-1307 section of `docs/item_notes/phase7.md` when that item
closed; binding since the session 145 /done, after a 32-spinner run saturated the machine and
caused the operator's session 144 CPU stop.

A load harness - CPU-bound spinner processes run beside a test to measure it under sibling
load - runs at most 6 spinners, and never beside another suite.

---

## 10. Runbook: the headless `queue` lane

**Filed 2026-09-06 with CS-918.** The lane executes ONE work item per worker process and
exits; `ops/loop/queue_loop.py` is what repeats it. Read that file's docstring before
changing anything here - it carries the measurements the design is built on.

### 10.1 What runs where

| Piece | Path | Job |
|---|---|---|
| lane lock | `ops/loop/lanes.py` | Decides who may run. FREE / RUNNING / RECLAIMABLE, by PROBING the pid |
| launcher | `ops/loop/lane_launcher.py` | Turns a claim into a worker in a git worktree |
| runner | `ops/loop/run_lane.ps1` | Starts the worker through the fleet kit's `spawn` command line, prompt piped on stdin; the kit starts `claude -p` |
| driver | `ops/loop/queue_loop.py` | Repeats the cycle, and OWNS EVERY WAIT |
| detached launcher | `ops/loop/launch_queue_loop.ps1` | Starts the driver hidden, for a night |
| worker prompt | `tools/headless-queue.md` | What the worker is told to do. TRACKED - a worktree is a fresh checkout and carries no gitignored file |

A lane runs in the fleet kit's per-index worktree `cs-worktrees/lane-<i>`, a directory
beside the main checkout - under the main checkout's PARENT, derived from the repo root by
`fleet_lanes.worktree_path` and written down nowhere. `<i>` is the index its claim took,
the same `<i>` as its lock `ops/loop/control/lanes/<i>.lock`; a lane tries its roster
position first and takes any free index when that one is held. The kit prepares the tree
DETACHED at `origin/main`, so the worker pushes `HEAD:main` and falls back to a fresh
`lane/<lane>-<short sha>` branch (`tools/headless-queue.md`).
**It may NEVER run against the main checkout itself** - two writers in one working directory
is index corruption that retrying does not fix. That is enforced three times: in the lock,
again in the launcher, and again at spawn time.

### 10.2 THE DIVISION OF WAITING, and why it is not a style choice

**The driver waits. The worker never does.** The worker does its row, pushes, and exits.
The driver then blocks until CI has graded that push, and only then starts the next cycle.

The reason is measured, in the tree this was ported from. The rule was first written as
PROSE in the worker's prompt - "block until your own run completes" - and over six cycles
the worker complied twice and bailed early four times. Each early exit let the next cycle's
push cancel the run the previous cycle was being graded on. **An instruction a worker can
rationalize past is not a mechanism.** The driver cannot rationalize: it is the only thing
that starts the next cycle, so while it is waiting there exists nothing that could cancel
the run.

Against this repo's CI specifically:

- `tier1.yml` fires on every branch push and sets `cancel-in-progress: true`, so the
  self-cancelling trap is live here. The driver waits it out.
- `tier2.yml` does NOT fire on a branch push - only on the nightly cron, on a `v*` tag, and
  on `workflow_dispatch`. So the full suite does not exist for a worker's commit unless
  something asks for it. **The driver dispatches it and waits for that too.** tier2 sets
  `cancel-in-progress: false`, so a dispatched run cannot be cancelled by the next cycle.

Both verdicts land in the SAME ledger row as the cycle that caused them.

### 10.3 Prove one cycle before firing a night

```bash
python ops/loop/queue_loop.py --once --local-suite
```

That claims the lane, launches one worker, waits for it, releases, runs the full local
suite, and writes exactly one row to `ops/loop/reports/queue_loop.jsonl`. Read the row
before doing anything else:

```bash
python -c "import json,pathlib; print(json.dumps(json.loads(pathlib.Path('ops/loop/reports/queue_loop.jsonl').read_text().splitlines()[-1]), indent=2))"
```

**Grade it on the summary line AND the exit code, never on either alone.** A crashed
parallel run leaves no summary line at all, and `grep -c FAILED` over that log returns 0 -
which reads exactly like a green run. The row therefore carries `suite.summary` verbatim
and `suite.exit_code` as an integer, and `suite.ok` is true only when a line was parsed
and the code is zero.

### 10.4 Fire a night

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ops\loop\launch_queue_loop.ps1 -Cycles 12
```

It refuses, printing no success banner, when a stop sentinel is already present, and exits
2 - the same number the driver itself uses for that condition. `-Force` gets past THIS
script only; the driver re-checks the same files before cycle 1 and will still run zero
cycles while they exist.

### 10.5 Stop it

Three files, checked before EVERY cycle including the first, and again before EVERY claim
attempt inside a cycle - a stop dropped while a claim waits to retry ends the night there,
with nothing claimed and no row written:

| File | Stops |
|---|---|
| `ops/loop/control/STOP` | everything on this box |
| `ops/loop/control/lanes/QUEUE_STOP` | EVERY lane - the roster carries more than one and this file is not per-lane |
| `ops/loop/control/lanes/QUEUE_DRAINED` | written by the WORKER when the queue is empty |

Creating one stops the loop at the next cycle boundary; it does not kill a worker that is
already running. To stop a running driver and its worker:

```bash
taskkill /F /T /PID <driver pid>
```

**Never the PowerShell process-stopping cmdlet** - CLAUDE.md hard rule, it hangs the MCP
pipe. `/T` is required: the recorded pid is the powershell wrapper and `claude` is its
child, so killing only the wrapper orphans a live worker inside the lane worktree.

### 10.6 Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | Cycles ran, or the queue drained mid-run | Nothing. Read the ledger |
| 2 | A stop sentinel was there before any cycle claimed a lane - zero cycles ran | Delete the file the message names |
| 3 | Another driver holds the mutex | Stop that one first. Two drivers interleave rows into one ledger |
| 4 | A worker OUTLIVED its kill | **Act on this one.** Treat the lane worktree as having a possible live writer and check by hand before firing again |
| 5 | The same fault repeated until the loop gave up | Read the last rows; whatever broke cycle 3 will break cycle 4 |
| 6 | A gating CI job went red on a pushed sha | Fix the red before firing again |
| 7 | The driver's own local suite went red | Same |
| 8 | Consecutive cycles whose launch failed - the lane was claimed, then the launch refused or returned no pid - reached the launch-failure limit | Read the last rows' `launch_reason` and `detail`. A claim, worktree or command-doc reason is this tree's to fix; `spawn_failed` and `runner_exited_early` mean the start itself refused - a missing or refused headless route or proxy is one such cause, outside this tree - so read the runner's log first |
| 9 | Either consecutive cycles that did not both complete and advance the lane HEAD reached the no-progress limit (`no_progress`), whatever earlier cycles shipped; or no cycle both completed and advanced the lane HEAD and the night ended on `max_cycles`, or on a stop sentinel once at least one cycle had run (a sentinel there before any cycle is exit 2) | Read each row's commit: commit=no -> the worker log; commit=unreadable -> the git state |
| 10 | A stop word in no table - never read as success | A driver defect. The console ALERT line names the word; add it to `_STOP_EXIT` or to `_SUCCESS_STOPS` |
| 11 | The account said no - a usage limit or a spent run budget. Either a one-cycle run's first such refusal, with no back-off; or consecutive such refusals reaching their limit, backing off between them, whatever earlier cycles shipped; or a night that ran no cycle and was refused at least once - by the usage limit or a spent run budget - whatever then stopped it | Wait it out; it is the account saying no, not a fault in this tree. The `usage_refused` and `budget_spent` rows say which |

### 10.7 Checks that no machine performs

Each of these is a real property that no test in the suite covers, and the reason is
stated rather than left as an omission.

1. **The refusal path, end to end.** Create `ops/loop/control/lanes/QUEUE_STOP`, run the
   launcher WITHOUT `-Force`, and confirm it prints the refusal, prints NO success banner,
   and that `$LASTEXITCODE` is 2. The suite grades this statically because running it would
   spawn a real driver against the real lane.
2. **A worker actually starts and writes its log.** Fire `--once` and confirm
   `ops/loop/reports/lane_queue_<run_id>.log` exists and carries its `lane start`
   header. This is the property `DETACHED_PROCESS` silently destroys: a real pid,
   exit 0, and a log that is never written.

   **BUT LOG SIZE IS NOT A PROGRESS SIGNAL ON THIS LANE, and mistaking it for one
   wastes an hour.** MEASURED on the first real cycle: the file sat at its 175-byte
   header for 31 minutes and then gained everything at once. `claude -p` writes its
   output when it finishes, so a log that is not growing says nothing at all about
   whether the worker is working. The signals that DO answer it:

   - the worker's process tree - `claude.exe` accumulating CPU and holding a few
     hundred MB is work; a bare `powershell.exe` with nothing under it is not;
   - `git -C ../cs-worktrees/lane-<i> status --short`, run from the main checkout with
     `<i>` read off the lane's lock (its `index` field, or the `<i>` of `<i>.lock`) - a
     worker doing a row changes files in its worktree long before it writes a word to
     the log.

   The log's LAST line is the one that matters when it ends: `lane exit ... code=N`
   is written by the runner, so a log without it belonged to a worker that was
   killed rather than one that finished.
3. **The lock re-points at the WORKER and keeps the DRIVER as its holder.** While a cycle
   is running, read the lane's `ops/loop/control/lanes/<i>.lock` and confirm its `pid` is
   the powershell wrapper's and its `holder_pid` the driver's. The lane stays RUNNING
   until the driver releases it, and reads RECLAIMABLE only once both are gone.
4. **The lane worktree is the worktree.** Confirm the worker's commits reach `main` (or a
   `lane/<lane>-<short sha>` fallback branch) from `../cs-worktrees/lane-<i>`, and that
   the main checkout is untouched while a cycle runs.

## 11. A row that will not come back

**Symptom.** A `ROADMAP.md` row is never offered to either lane. `python -m ops.loop.scope`
lists it, but every cycle skips it, and no cycle is working it.

**Read the claim before doing anything.** From the MAIN checkout:

```
python -c "from ops.loop import claims; print(claims.claim_states())"
```

A row in that mapping whose `anchor` is `lane_lock_unproven` is the case this section is
about. `lane_lock` means a cycle really is running it - leave it alone. `pid` means the
claim is anchored on a process rather than a cycle and expires on its own.

**What `lane_lock_unproven` means.** The row is held on the authority of a lane lock that
reads RUNNING but cannot prove the process behind it is the one it recorded. That happens
when a driver dies without releasing AND the operating system reissues its pid AND the
start time cannot be read - the last of which is unconditional where `psutil` is not
installed. The claim store believes the lane lock deliberately: guessing the other way
would hand a live cycle's row to a second lane, which has no undo. The lane is stale too,
and `try_acquire_lane` is refusing it for the same reason, so this is a lane to recover
rather than a row.

**The fix is to clear the stale LANE LOCK.** The slot files live under the main checkout's
lane lock root, `ops/loop/control/lanes/`, one per lane, named by slot index. Confirm the
lane is genuinely dead first:

```
python -c "from ops.loop import lanes; print(lanes.lane_states())"
```

Then delete that lane's slot file. The row is reclaimed automatically on the next fire -
nothing else is required and no claim file is touched.

**NEVER DELETE A CLAIM RECORD BY HAND.** Records under `ops/loop/control/claims/` are not
the thing to clear. If the holder is really gone the next `first_takeable` already offers
the row; if it is not, deleting the record puts a second lane into a worktree that already
has one, which is the concurrent-index corruption class and is not recoverable by retrying.
The lane lock is the safe thing to remove because removing it also frees the lane, which is
the actual fault.

## 12. Runbook: the fleet kit channel - MAIN's notes, the status board, the stop sentinels

### 12.1 Is this note MAIN's

Relocated on 2026-10-19 from `CLAUDE.md` section 6.1 under CS-1330, when the kit version
20 patch 1 common block took that file's last bytes of budget; `CLAUDE.md` keeps the rule
and its floors and points here.

MAIN SPEAKS FOR THE OPERATOR - granted by the operator in this repository's own session,
2026-10-02, superseding the narrower 2026-09-22 stand-in scope. MAIN's notes carry the
operator's authority as if typed here; MAIN never commits in this tree. The operator's
words, quoted verbatim: `docs/LEDGER.md`, the 2026-10-05 CS-1225 relocation record.

Provenance: a note is MAIN's only if its SHA-256 equals the same-named file in MAIN's
outbox and that file is tracked and unmodified in MAIN's history; MAIN's path lives only
in gitignored local configuration. Detail in `docs/LEDGER.md` under 2026-10-02. The check
is one command, `python tools/main_provenance.py <note>`, which exits 0 only then and
prints the note's sha256. From kit version 18 on MAIN ships no outbox bundle: the ORDER note is checked
that way, and every kit file in the payload folder beside it against the sha256 list the
note itself carries.

### 12.2 The status board - FLEET-COMMON item 18, kit version 19

This tree's board URL, and the dataset version its first push pins, are in
`ops/status_board.json`. An interactive session pushes the board at session start, after
every item-13 b reprint, and once at /done with `--final`; a headless run never pushes
(the kit prints `no push: headless` and writes nothing).

The main session runs no Bash (the SUB-AGENT FIRST banner), so ONE sub-agent makes each
push:

1. Pipe the checklist block the session just printed into
   `python ops/fleet_kit/fleet_board.py calls --session <n>` (`--final` at /done).
2. Make the first call it prints: an Artifact publish of the rendered status.json with
   `asset: true`, which returns the blob url.
3. Make the second: an ArtifactData update of `datasets/board`, pinned with the printed
   `if_version`, its data's `__URL__` replaced by that blob url.
4. On a version mismatch, `python ops/fleet_kit/fleet_board.py pushed --version <current>`,
   then redo the second call once.

A failed push is a line in the hand-off, never a ritual failure. The render state lives in
the gitignored `ops/loop/control/board/`. MAIN's v19 ORDER asks this tree to read its
board's `datasets/board` version before the first push; the version-mismatch path above
corrects a stale pin either way.

### 12.3 The stop sentinels the kit spawn reads

`ops/stop_sentinels.json` declares this tree's stop sentinels for the kit's `spawn()` (kit
version 19): while ANY declared path exists - a dangling link included - a kit spawn into
this tree refuses `halted` before anything starts, and an unreadable declaration refuses
too; a declared path that is absent halts nothing. It declares the three stops MAIN's v19
ORDER named - `STOP` in the loop control directory, and `INBOX_STOP` and `QUEUE_STOP` in
its lanes subdirectory - and the main-spawn hold, `HOLD_MAIN_SPAWN` in the loop control
directory. `QUEUE_DRAINED`, the worker's queue-empty marker in the lanes subdirectory that
the queue loop also stops on, is deliberately NOT declared: declared, it would halt every
kit spawn into this tree whenever the queue drains. The inbox status file's own `halted`
state is not a trigger.

The hold halts EVERY kit spawn into this tree while its file exists - this tree's own inbox
responder included, not only MAIN's - and so does a standing `QUEUE_STOP`, because the
kit's sentinels are tree-wide. The responder reads every one of them itself, before its lock
and before it lists the channel: `STOP` and `INBOX_STOP` directly, and every declared path
through the kit's own `stop_sentinel_hit`, so the two cannot part (CS-1234). Any standing one
halts it quietly - status `halted`, exit 0, no log line - dated from the oldest standing
sentinel; an unreadable declaration halts it too (fail closed, as the kit's spawn does), and no
declaration lifts `STOP` or `INBOX_STOP`. So `QUEUE_STOP` and `HOLD_MAIN_SPAWN` no longer reach
the kit: no `kit_refused` line, no `refused` / Idle and no exit 3 while either file stands. A
sentinel placed after that check, which the kit then reads, also shows `halted` and exits 0.
The queue lane honours the hold too (CS-1231 slice C): its driver reads every declared path
through the kit's own `stop_sentinel_hit` before each cycle and each claim, and stops the night
on `kit_halted` - an unreadable declaration stops it too, fail closed. A hold placed after that
read meets the kit, which refuses the start with code `halted`, and the driver stops on the
same word. The declaration is permanent: LIFTING THE HOLD
removes the hold FILE only, never its line in the declaration, so lifting it needs no
commit. When to lift it is the hand-off's to say (CS-1330).

### 12.4 The session checklist counter

Relocated on 2026-10-19 from `CLAUDE.md` section 2.3.1 under CS-1330, for the same budget;
`CLAUDE.md` keeps the checklist rules and points here.

**Here:** n is the `SESSION: <n>` line of `CS-NEXT-SESSION.txt`; `/done` writes n+1 and
its last act is `python ops/fleet_kit/fleet_done.py mark` (`.claude/commands/done.md`);
the session-start hand-off read prints the block. Kit helper:
`ops/fleet_kit/fleet_checklist.py`. Board pushes (FLEET item 18): section 12.2.

### 12.5 Landing a Dependabot PR

Moved on 2026-10-21 from the CS-700 section of `docs/item_notes/phase7.md` when that item closed;
binding since MAIN's 2026-10-08 22:46 ORDER, section 4.

Never merge a Dependabot PR with the merge button or `gh pr merge`; apply it locally as an operator
commit (cherry-pick `--reset-author`) and push.

### 12.6 The trailer-shaped census

Moved on 2026-10-21 from the CS-700 section of `docs/history_notes.md`, where that item's
close had carried it and which holds nothing current. It is live: `tools/trailer_census.py`
computes it, and the tier-1 census step and `tools/flip_checks.py` run that tool.

**THE TRAILER-SHAPED CENSUS - defined here and ONLY here; every other file points at this
paragraph.** Walk every commit message reachable from the tip being measured and
count the lines that sit at column zero, carry a colon, and whose token before the
first colon - trailing whitespace trimmed - folds case-insensitively to
`co-authored-by`. That is the shape git's own trailer parser reads and the shape
`.githooks/commit-msg` refuses. A plain substring search is NOT this census: it also
matches prose naming the trailer.

## 13. Runbook: cutting a milestone tag

Filed on 2026-10-21 under CS-1335, from posture item 1a of MAIN's PUBREPO ORDER (CS-1328
(g)), AFTER `v0.1.0` was cut, so the next milestone does not rediscover the rules. This
section is the policy's one owner. `v0.1.0` met it on the annotated tag, the one-line
message, the operator tagger, the ancestry of `main`, the hand-written notes and the final
release, with ONE EXCEPTION: its tag message was given inline with `-m`, not from a gated
message file, and the record of its tag message and release body (`docs/LEDGER.md`, the
CS-700 close) shows only a count-only needle probe of each, never an outbound gate pass.

**What a milestone tag is.** An ANNOTATED tag - never a lightweight one - named in semver
0.x, `v0.MINOR.PATCH`: MINOR moves for a milestone, PATCH for a fix to one that adds no
capability. Leaving 0.x is outside this policy. Its release notes are hand-written.

**Who cuts it.** An interactive session, by hand, through ONE sub-agent - the main session
runs no Bash (the SUB-AGENT FIRST banner in `CLAUDE.md`). The call to cut one comes from the
operator's own words, a MAIN ORDER (FLEET item 6) or an adjudicator's ruling (`CLAUDE.md`
section 6.1), never from a question put to the operator. NO lane, loop tick, inbox
responder or other headless run cuts, pushes, moves or deletes a tag; one that is asked to
leaves it for the next interactive session. This is a written rule: no hook enforces it.

**The commit it goes on - never an unreviewed or an unpushed one.** REVIEWED: a distinct
adjudicator ruled on that exact commit, frozen at its SHA (`CLAUDE.md` section 5), and a
ruling covers only the SHA it read, so a commit landed after it needs its own. PUSHED: it is
an ancestor of the published `main` - never a local-only commit or a worktree branch tip.
The control, read before the tag is made, must exit 0:

```
git fetch origin main
git merge-base --is-ancestor <full-sha> origin/main
```

**The tag message.** One subject line, no body, no trailer, ASCII only:
`Clockspeed v0.MINOR.PATCH - <the milestone in a few words>`; the first reads
`Clockspeed v0.1.0 - first public release`. The tagger is the operator identity commits
carry (FLEET item 17). Write the message to a file outside the checkout, gate it (below),
and tag from that same file, so the bytes gated are the bytes tagged:

```
git tag -a v0.MINOR.PATCH -F <message-file> <full-sha>
```

**The notes, and the outbound gate.** The release notes are written by hand, in a file
OUTSIDE the checkout - the session scratchpad - so they are never committed and never sit
where a whole-tree guard reads them. Generated notes stay OFF: never `--generate-notes`.
The tag message and the release body are public once pushed and created, and no commit hook
reads either, so both files pass `tools/outbound_gate.py --file <path>` first. Anything but
CLEAN stops the cut; edit the text, never the gate. Its exit codes are that module's
docstring's and are not restated here.

**Push the one ref.** Only that tag ref, through the kit's lock (FLEET item 16 a), never
`--tags`, `--mirror` or `--follow-tags`:

```
python ops/fleet_kit/fleet_gitlock.py run --owner <session_id>.<agent_id> -- git push origin refs/tags/v0.MINOR.PATCH
```

Read back: `git ls-remote --tags origin` lists the tag, and its peeled `^{}` line names the
commit the ancestor control passed.

**The release.** Made from the pushed tag, final - neither `--draft` nor `--prerelease`:

```
gh release create v0.MINOR.PATCH --verify-tag --title "Clockspeed v0.MINOR.PATCH" --notes-file <notes-file>
```

`--verify-tag` aborts when the tag is not already on the remote, so the release can never
mint a tag of its own on whatever `main` is then. Read back:
`gh release view v0.MINOR.PATCH --json tagName,isDraft,isPrerelease` - both flags false.

**Tier 2 on the tag.** The tag push starts `.github/workflows/tier2.yml`, which fires on
`v*` tags (section 10.2). Read it to completion:

```
gh run list --workflow tier2.yml --commit <full-sha> --json databaseId,event,headBranch,attempt,status,conclusion
```

The tag's run is the one whose `headBranch` is the tag name. Give the FULL SHA: a short one
returns an empty list and exits 0, which reads as no run at all. Read a re-run's earlier
attempts too, with `gh run view <databaseId> --attempt <n>`. A red run never moves the tag;
it is recorded, and its fix ships as the next PATCH.

**A pushed tag is never moved.** Never re-pointed, force-pushed, or deleted and re-cut: a
clone that fetched it keeps the old object, so a moved tag names two commits. A wrong tag is
superseded by the next PATCH.

**The record.** One `docs/LEDGER.md` entry per cut, under the item it was cut for: the tag,
the tagged commit's full SHA, the ancestor control's exit code, the `ls-remote` read-back,
the outbound gate's verdict on both files, the release's draft and prerelease flags, and the
tier 2 run's id and conclusion.

## 14. Cross-references

- Module map, seams, card contract: `docs/ARCHITECTURE.md`
- Decisions and their fences: `docs/adr/README.md`
- Blocked outside the repo: `docs/GATED.md`
- Completion records: `docs/LEDGER.md`
