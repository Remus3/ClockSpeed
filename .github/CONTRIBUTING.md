# Contributing to Clockspeed

Clockspeed is a local, deterministic planning and advisory system for a single-player
factory-building game. `README.md` says what it is and how to get a first result;
`CLAUDE.md` is the operating law of this tree.

**This page points at owner files rather than restating them.** Every fact in this
repository has exactly one owner, and a restated fact is a fact that will drift. Where a
rule below is summarised in a sentence, the owner named beside it is authoritative and
this page is not.

---

## 1. Wire the clone before you touch anything

**A fresh clone runs zero protection until someone wires it.** Git hooks are configured
through local git config, which is not tracked, so cloning this repository gets you the
hook scripts in `.githooks/` and none of the enforcement. Until the bootstrap has run in
your clone, every gate here is inert - and an inert gate is worse than an absent one,
because it is trusted.

The bootstrap order is owned by `docs/OPERATIONS.md` section 1 and the ordering is not
arbitrary: `scripts/install_hooks.py` first, so protection exists before anything can be
committed; `scripts/verify_env.py` second, so a missing hard dependency is found before
any work starts; `tools/memory_sync.py` third. Run them from the repository root.

**Installation is not proof that a hook fires.** `docs/OPERATIONS.md` section 1.1 gives
the only valid test: stage a file containing a banned character, attempt a real commit,
and assert that HEAD is unchanged. If HEAD moved, the gate did not fire.

---

## 2. The non-negotiables a drive-by change would otherwise break

These reject a patch outright. They are summarised here because a contributor who reads
only this page must not be able to miss them.

- **7-bit ASCII in all authored content** - code, comments, docstrings, markdown, commit
  messages, shell scripts. No em-dash, no en-dash, no smart quotes. Use a spaced hyphen
  for a clause break. This is a mechanism, not a style preference: Windows PowerShell 5.1
  ANSI-decodes a BOM-less script and a multi-byte dash inside a double-quoted string
  becomes a character the tokenizer treats as a string terminator. Owner: `CLAUDE.md`
  non-negotiable 4, enforced by `tools/precommit_gate.py`.
- **LF line endings only.** Many editors and tooling harnesses write CRLF on Windows and
  git then normalises the blob and reports the tree clean, so the violation is invisible
  to a text-mode read. Write bytes explicitly when it matters.
- **No lifted datasets from any wiki or community source.** Reading a wiki page and
  citing its URL is fine and carries no obligation. Copying a table, a node dataset or a
  data dump out of one is not: the official wiki is share-alike and non-commercial, so
  vendoring any part of it would relicense this project against `LICENSE`. Owner:
  `CLAUDE.md` section 7; the licence gate every external lift must clear first is
  `CONVENTIONS.md` section 14, and its verdicts are recorded in `THIRD_PARTY.md`.
- **Never write to the game install directory or a save file.** An invariant, not a
  preference, and not negotiable behind an opt-in flag or a backup-then-write. Owner:
  `CLAUDE.md` non-negotiable 1.
- **A save file is personal-data-bearing.** Its header carries platform, account and
  player-display-name strings in plaintext. Never commit one, never attach one to an
  issue or a pull request, never place one in a fixture directory, and never add a code
  path that echoes raw header bytes. Owner: `CLAUDE.md` non-negotiables 11 and 12.
- **Never hardcode a machine's identity** - an account name, a numeric platform account
  id, a world name, a host name, or any absolute path under a user home directory.
  Detect at runtime and make it config-overridable. Owner: `CLAUDE.md` non-negotiable 3.
- **The failing test comes first, and it must fail for the right reason.** A test that
  passes before the fix is a test about nothing. Owner: `CLAUDE.md` non-negotiable 9;
  the full loop is `CONVENTIONS.md` section 7.
- **No language model anywhere in the advice path.** The advisor is deterministic and
  local by design - no model, no cloud service, no API key where advice is computed,
  ranked, explained or rendered. The full derivation is generated from the rule trace,
  which is exactly why no model is needed. Owner: `CLAUDE.md` section 7, and it is
  settled rather than open.
- **Exact rational arithmetic in the solve path**, with floats asserted absent. Owner:
  `CLAUDE.md` non-negotiable 6.

---

## 3. Tests

Write the failing test first, run it, and read the failure before you implement
anything. Then classify the change and run that tier: a cosmetic edit needs a syntax
check, local logic needs that module's tests, and a schema, engine, core-algorithm,
version-bump or public-interface change needs the whole suite. `CONVENTIONS.md` owns the
tiers and `docs/OPERATIONS.md` section 3 owns the operator-facing policy.

Fixtures are small synthetic registries hand-authored in the repository. A trimmed real
game data file or a trimmed real save is never an acceptable fixture, even "just for
tests" - the suite must run on a machine with no game installed.

Run the linter and the formatter check before you open a pull request. A pipe eats the
exit code, so read the status of the test command itself rather than of whatever you
piped it into.

---

## 4. Commits

- Subject line at most 72 characters, ASCII, imperative, and naming the item it belongs
  to where there is one.
- **No co-authorship trailer of any kind.** This is an operator decision recorded in
  `docs/GATED.md` under CS-G03: a trailer is publication metadata, it is trivial to
  reintroduce by default, and it is impossible to remove later without a history
  rewrite. The commit-msg hook rejects one, so a tool that adds a trailer by default
  needs its default turned off rather than worked around.
- Commit messages containing special characters on Windows have a written procedure in
  `docs/OPERATIONS.md` section 9.1. Use it; the shell will otherwise mangle them.
- Never skip a hook. If a gate fails, the gate is the thing to understand.

---

## 5. Work items

Open work is one line in `ROADMAP.md`, with its detail and its acceptance clause in a
leaf under `docs/item_notes/` - the index over those leaves is `docs/item_notes.md`.
Completed work is an append-only record in `docs/LEDGER.md`. Aspirational ideas go to
`BACKLOG.md`, and work blocked on something outside the repository goes to
`docs/GATED.md`. An architectural decision gets a file in `docs/adr/`.

Item IDs carry a `CS-` prefix, are permanent, and are never reused. A typo fix needs no
item; anything with substance does.

---

## 6. Pull requests

The template in `.github/PULL_REQUEST_TEMPLATE.md` asks for the item ID, the acceptance
conjunct the change discharges, and the evidence - because those three are what this
repository reviews on. A description of what the diff does is not evidence that it
works.

Claims about test counts, a green build or a file existing are checked rather than
taken, so state the command you ran, its exit code and the counts you observed on that
run. An uncertainty reported as an uncertainty costs nothing; one rounded up to a claim
costs a review cycle.

---

## 7. Reporting a vulnerability

Do not open a public issue for a security problem. The route is in
[SECURITY.md](SECURITY.md).

---

## 8. Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
