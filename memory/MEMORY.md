# Memory Index

Durable cross-session facts for Clockspeed. One file per fact, one line per file here.
Markdown is the single source of truth; any semantic store is a mirror, never the source.

**Rules:** this index NEVER holds memory content - only a title, a link and a short hook.
Every leaf must be reachable from here; a drift guard enforces reachability, and unindexing
a file to save bytes is forbidden. Hooks are short because the index is scanned, not read.
Budgets: this file under 20 KB (CI hard fail), each leaf under 6 KB (CI warn).

## How to work

- [Operator attention is the budget](operator-attention-is-the-budget.md) - scarcest
  resource; main session stays usable; operator does only what Claude cannot.
- [Orchestrated multi-agent is the default](orchestrated-multi-agent-is-the-default.md) -
  default session shape, not an escalation; producers never grade their own work.

## Hard rules and mechanisms

- [7-bit ASCII is a hard rule](seven-bit-ascii-is-a-hard-rule.md) - the PowerShell 5.1
  ANSI-decode parse failure behind it; commit messages via `git commit -F`.
- [Hook presence is not hook firing](hook-presence-is-not-hook-firing.md) - four ways a
  hook silently does nothing; only an end-to-end block test counts.
- [A guard can be accepted and unscoped](a-guard-can-be-accepted-and-unscoped.md) - a tool
  taking your key is not proof of where it applies; probe inside AND outside the scope.

## Project invariants

- [Save files carry PII](save-files-carry-pii.md) - header embeds platform and player
  identity; redact by default, never commit a save.
- [World token is the ledger key](world-token-is-the-ledger-key.md) - 22-char base64url
  world token keys the ledger, never a filename or world name; honest limits recorded.
- [Never write to the game](never-write-to-the-game.md) - read-only invariant; copy saves
  to a work directory before parsing.
- [No language model in the advice path](no-language-model-in-the-advice-path.md) - fully
  deterministic and local; tier 3 is generated from the rule trace.
- [Unknown content is flagged, not fatal](unknown-content-is-flagged-not-fatal.md) - skip
  and flag unknown classes; never a crash, never a silently wrong number.
- [Game data is publisher-owned](game-data-is-publisher-owned.md) - read at runtime,
  gitignore, ship extraction code plus synthetic fixtures only.

## Failure classes

- [Test-quality failure classes](test-quality-failure-classes.md) - the ways a suite is
  green and proves nothing, with mechanisms.
- [A proof can require the defect](a-proof-can-require-the-defect.md) - a check that
  derives its cases from today's tree goes RED when the defect is fixed; green means
  the defect is still there.
- [An empty population satisfies every zero](an-empty-population-satisfies-every-zero.md) -
  `assert count == 0` passes when the property holds AND when nothing was measured;
  the two are byte-identical. Assert the population, not just the zero.
- [Verification failure classes](verification-failure-classes.md) - ways a check looks
  convincing and proves nothing, with mechanisms.
- [Moving an assert can create the leak](moving-an-assert-can-create-the-leak.md) - a
  static finding names a SCOPE, not a disclosure; the remedy that relocates the assertion
  changes which frame unwinds, and the new frame has its own locals.
- [A guard can measure spelling](a-guard-can-measure-spelling.md) - and its REPAIR can
  measure a different spelling; gate a clearance on a positive fact. A guard that
  matches on a NAME reports a population zero about the wrong question; and a false
  clearance is a worse defect than a silence.
- [A probe can validate the wrong channel](a-probe-can-validate-the-wrong-channel.md) -
  a check that validates one channel while its consumer reads another proves nothing;
  a harness that cannot reach that channel cannot grade it.
