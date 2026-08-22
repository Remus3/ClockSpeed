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

- **Base port: 8901** - the local HTTPS dashboard and JSON API.
- **Reserved band: 8900-8911** - held for this project.

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

## 7. Windows discipline that bites operationally

### 7.1 Commit messages with special characters

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

### 7.2 The rest of the Windows list

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

## 8. Cross-references

- Module map, seams, card contract: `docs/ARCHITECTURE.md`
- Decisions and their fences: `docs/adr/README.md`
- Blocked outside the repo: `docs/GATED.md`
- Completion records: `docs/LEDGER.md`
