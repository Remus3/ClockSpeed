# Wakeup notes

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**The last two to three sessions at full fidelity, newest first. Nothing older.** When a
fourth session lands, the oldest entry is moved to `docs/history_notes.md` - relocated,
never deleted.

This file is read at session start, alongside `CLAUDE.md`, the memory index, `ROADMAP.md`
and `docs/ARCHITECTURE.md`. It is refreshed by the `/done` ritual at the end of every
session, not written incrementally during one.

It holds what a fresh session cannot recover from the code and the git log: what was
actually in flight, what was tried and abandoned, and what the very next action is. It
does not hold per-item completion records - those are ledger entries and belong in
`docs/LEDGER.md`.

## Entry format

```
## Session <n> - <YYYY-MM-DD> - <one-line focus>

- Shipped: item IDs closed this session. Detail in docs/LEDGER.md, not here.
- In flight: what was left mid-work, where it stands, and what it is blocked behind.
- Decisions: ADRs recorded this session, by id. Detail in docs/adr/.
- Surprises: anything that contradicted a spec, and which file was updated as a result.
- Failed paths: what was tried and abandoned, and why - so it is not retried next session.
- Next action: the single first thing the next session does.
```

Keep every entry to that shape. If an item needs a paragraph, it needs its own file and
the line becomes a pointer.

---

## Session 49 - 2026-08-30 - CS-602 CLOSED and the shell-suite job ran for the first time on both platforms; six graders found two ways to make the certificate clause green while trusting everything, and BOTH were the guard rather than the code

- **Shipped: CS-602.** tier2 run `33300238437` at `4b5de1e`, `shell suite` GREEN on ubuntu
  AND windows, `# tests 196 / pass 196 / fail 0 / skipped 0 / todo 0`; tier1 run
  `33300227008` at the same SHA, `success`. Detail in `docs/LEDGER.md`, not here. Ten
  follow-ups filed, CS-614 to CS-623.

- **THE HEADLINE: A GUARD THAT COUNTS A TOKEN DOES NOT CONSTRAIN WHAT THE TOKEN DOES.** The
  arm asserted `shell/main.js` holds exactly one `callback(`. It never looked at the
  argument. So `callback(0)` - accept every certificate ever presented - passed 63 static
  arms, 174 node tests, drift_guard CLEAN and precommit_gate PASS, and so did four
  one-token edits to the verdict map, and so did a single call site answering the wrong
  integer for every non-TRUST verdict. **The root cause was PLACEMENT.** `codeFor` is a pure
  function from five strings to three integers - no electron, no display - and it had been
  moved out of a file with fourteen tests into one with zero, which is exactly what made it
  ungradable. ADR 0014 asserted "mapping words onto integers is a separate module's job" as
  though it were already true.

- **ONE REGEX LITERAL BLINDED EVERY TEXT-SCANNING ARM AT ONCE.** `/[/*]/` is valid
  JavaScript and opens a block comment in the stripper, so everything up to the next `*/`
  vanishes from what the guard reads. Live `ignore-certificate-errors`, the Node TLS kill
  switch and a `certificate-error` handler were invisible while `node --check` called the
  file valid. **The stripper's own docstring named two arms as the alarm; both were measured
  against the attack and both stayed green** - idempotence cannot fire because the second
  strip re-derives the same deletion, and never-grows cannot fire because deleting is
  shrinking. The mitigation had been built parallel to the stripper's assumptions. Repaired
  by scanning RAW text with an allow-list of documented mentions, so the stripper is not
  consulted for that sweep at all.

- **EVERY ONE OF EIGHT SLICES FOUND A REAL DEFECT IN THE BRIEF THAT DISPATCHED IT.** The
  worst was a test the merger specified that PASSES ON THE VULNERABLE CODE: plant
  `{"__proto__":{"width":99999}}` and assert width is the default - which it is either way,
  because `JSON.parse` makes `__proto__` an own property and leaves the prototype intact.
  The discriminating assertion is `Object.getPrototypeOf(loaded) === Object.prototype`.
  Also: a precedence table that returned TRUST when both hostnames were absent; a repair
  that would have MOVED the defect to a tier-2-only lane; and a mandated `throw` that would
  have reintroduced a hang, because a verify callback that throws never fires.

- **THE PUSH GATE WAS PROVEN END TO END ON A REAL VIOLATION.** The merger merged a slice on
  its INTERIM report, verified with a subset that did not include the guard the change
  broke, and committed a failing test. The push was attempted and BLOCKED - `1 failed, 3057
  passed`, `Nothing was pushed`, origin unmoved. Acting on an interim report is the error.

- **THE PIPELINE EXIT-CODE TRAP BIT THREE TIMES IN ONE SESSION.** A backgrounded
  `cmd | tail` reports tail's status. It masked a failing baseline suite, masked four
  failures in a slice's full run, and reported the BLOCKED push as "exit code 0". Capture
  `PIPESTATUS` or do not report an exit code.

- **Decisions: ADR 0013 and ADR 0014 ACCEPTED.** The Electron licence gate split into three
  scopes, and the pin-one-certificate decision with `setCertificateVerifyProc` chosen over
  the strictly weaker `certificate-error`.

- **Failed paths: a `start` script was added and BACKED OUT.** The static guard merged nine
  minutes earlier caught it - electron may be named nowhere in the manifest outside
  `devDependencies`. The guard could have been narrowed; it was not, because `npm start` and
  `npx electron .` are functionally identical and widening a bright-line check for a
  convenience is a bad trade.

- **Next action: run the six manual checks in `docs/OPERATIONS.md` section 8.3.** They all
  read `NOT RUN`, they need a real display and a real Electron, and until they are filled in
  nobody has seen the companion window work. Then CS-615 - the count floor is one test
  pooled over five suites.

---

## Session 48 - 2026-08-30 - CS-605 CLOSED and tier-1 CI is GREEN on ubuntu; the first repair of the home-path arm built a guard that muted itself, and an adversary caught it with a mutant the old assert had killed

- **Shipped: CS-605.** tier1 run `33289681747` at `90d2956`, `ubuntu-latest`, conclusion
  `success`, 15 steps, ZERO non-success steps, `3755 passed, 114 skipped`. Exactly one arm
  skips across `tests/surface/` and `tests/test_make_cert.py` there, with its reason in the
  log. Detail in `docs/LEDGER.md`, not here. Six follow-ups filed, CS-608 to CS-613.

- **THE HEADLINE: A SKIP CONDITIONED ON THE CODE UNDER TEST IS A MUTE BUTTON THE DEFECT GETS
  TO PRESS.** The first repair turned a precondition into a skip on `home in body`, which is
  exactly what a non-escaping encoder produces, so the alarm switched itself off in the one
  case it existed for. MEASURED by an adversary with `contract.encode` mutated to stop
  doubling: `tests/surface/` reported `527 passed, 1 skipped, exit 0` WITH THE LEAK LIVE, and
  the deleted assert had killed that mutant. The skip reason blamed the PLATFORM, so it
  misdirected rather than merely falling silent. Doctrine in
  `memory/a-skip-can-mute-the-defect.md`. **THE WRONG INSTRUCTION WAS THE MERGER'S**: the
  brief said to ask the skip OF THE ENCODER and explicitly not to test for a separator.

- **ONE OF THE THREE "PLATFORM-DIVERGENT" FAILURES WAS NOT PLATFORM-DIVERGENT.** The
  verify_env arm demanded exit 0, which holds only where `core.hooksPath` is wired.
  Reproduced in a plain clone ON WINDOWS: `HARD: 6/7`, exit 1. `tier2.yml`'s
  `clean-checkout-probe` already asserts that unset state, so the repo had recorded the fact
  the arm contradicted. **Verify a claim of platform-divergence by reproducing it on the
  other platform.**

- **CS-605's OWN SECOND NAMED ITEM WAS GRADED BY NOTHING, ON ANY PLATFORM.** The certificate
  key's 0600 chmod had no arm at all, so no CI run could ever have revealed it. It now runs
  green on ubuntu. Closing the item on its acceptance clause alone would have left its stated
  gap open.

- **EVERY TOKEN IN THE ASSET ALLOW-LIST WAS AN EQUIVALENT MUTANT.** Emptying the tuple killed
  the arm, but each single-token deletion survived, so the proof showed only that at least one
  of four fired. Each token now has its own subject. The parametrization is over the test
  file's OWN table - over the source tuple it would delete the case on a deletion and stay
  green.

- **MERGER ERROR: THE CANDIDATE WAS NOT FROZEN.** Three adversaries were dispatched against
  `016fc15` and the tree moved to `5738da3` while they ran. Two findings of one adversary were
  repaired mid-verdict. It reported the violation itself. Its remaining findings stood.

- **Decisions: no ADR.** Nothing contradicted `BOOTSTRAP.md`.

- **Failed paths: none abandoned.** Every finding was either fixed or filed with its
  measurement.

- **Next action: ask the operator whether to take CS-602**, the Electron companion, which
  closes phase 6 together with CS-600 - **or CS-829**, still the head of the product path and
  untouched for six sessions. CS-603, CS-604 and CS-606 are tier-1 and cheap if a warm-up is
  wanted first.

---

## Session 47 - 2026-08-29 - CS-601 CLOSED. Phase 6 opened ahead of phase 5 by operator ruling, and there is a working dashboard; the port band moved after nine sessions of blaming a squatter that was never one

- **Shipped: CS-601.** The local HTTPS dashboard and JSON API answer all nine BOOTSTRAP 7.1
  endpoints - four with computed data, five with a machine-readable refusal naming CS-500.
  Detail in `docs/LEDGER.md` and ADR 0012, not here. **CS-600 STAYS OPEN**: it is the phase
  gate and CS-602, the companion window, is unstarted.

- **PHASE 6 OPENED AHEAD OF PHASE 5, BY OPERATOR RULING, AND IT IS A RECORDED DEPARTURE.**
  `advisor/`, `audit/` and `progress/` hold a docstring each. `CLAUDE.md` says not to advance
  past a phase whose acceptance is unmet. The operator was given the choice and took the
  walking skeleton over the four layers that already exist. Do not re-litigate it; do not
  treat it as precedent for skipping a gate without a ruling.

- **THE PORT BAND MOVED, AND THE NINE-SESSION DIAGNOSIS WAS WRONG.** `docs/LEDGER.md` recorded
  8901 as held by "an unrelated third-party process". It was not unrelated and 8901 was never
  this project's: the whole 8900-8919 block belongs to LegionWallpaper, and Clockspeed's band
  was chosen by PROBING for a free listener. LW's monitor is an operator-launched GUI that is
  unbound most of the time, so a live scan reported a fully reserved block as free. Band is
  now 8920-8939 and `verify_env.py` reports 20/20 free. **Verify a band against the owning
  registry in source, never against a scan.**

- **THE MERGER'S BRIEFS WERE MEASURABLY WRONG SEVEN TIMES AND EVERY ONE WAS CAUGHT BY A
  SLICE.** A `*Error` name rule that would have graded 2 of 12 exception classes, then a
  correction that was also wrong (5 carry no suffix, not 8). The wrong file named as owning
  the repr records. An `EXEMPT` remedy that would have fixed neither red arm. An example port
  from inside the allocated band, caught by the repo's own guard. A canary brief that looked
  at handlers when the reflection lived in the DISPATCHER. A harness option measured to change
  nothing. A disjointness precondition checked on FILE PATHS while two slices were coupled
  through a TYPE SIGNATURE.

- **Decisions: ADR 0012 ACCEPTED.** The 501/503 split, `detail` looked up by reason and never
  built from content, the exact-rational `{"num","den"}` wire form, and the ruling that
  `/api/world` is BACKED.

- **Surprises: nothing contradicted `BOOTSTRAP.md`.** But the browser pane REFUSES HTTPS with a
  self-signed certificate, denied before the TLS handshake, while BOOTSTRAP 7.1 mandates HTTPS.
  The five-phase visual audit is therefore run against a test-only plain-HTTP harness serving
  the real assets. Production stays HTTPS-only and the harness never ships.

- **Failed paths: the harness routing all five refusals.** Measured A/B: the page's probe set is
  fixed in `app.js`, not by the harness, and the rendered output was identical. It routes three.

- **`C:` WAS 100 PER CENT FULL - 40 MB of 953 GB.** A session from 2026-08-22 reproducing the
  CS-819 heredoc failure dropped `python` into interactive mode in a BACKGROUND command; it
  looped its banner into a 58 GB scratch file while the harness captured another 58 GB of the
  same stdout. Nothing in that transcript looked wrong. 117 GB recovered. Never background a
  command that can reach an interactive prompt.

- **A PUSH-BLOCKING FLAKE IS FILED AS CS-607 AND IS NOT DIAGNOSED.**
  `test_the_oracle_reproduces_the_real_runs_discovered_set` failed in full-suite run 1, passed
  in isolation three times, passed in run 2, FAILED in the first pre-push run and blocked the
  push, then passed after `.mypy_cache` was deleted. Ruled OUT by measurement: order
  randomisation (no `pytest-randomly`, xdist inactive), untracked `.py` files (zero outside
  dot-directories - all 736 sit under `.claude/worktrees`, which mypy skips), and
  `tests/test_doc_budget.py`'s worktree (it targets a throwaway scratch checkout, not this
  repo). The cache was being written while `C:` was at zero bytes free, which is a hypothesis
  and NOT a diagnosis. **Do not cite the cache as the cause.**

- **Next action: take CS-602, the Electron companion**, which closes phase 6 with CS-600 - or
  take CS-829, still the head of the product path and untouched for five sessions. Ask the
  operator which; the surface is now real enough that either is defensible.
