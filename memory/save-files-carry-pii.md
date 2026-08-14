---
name: save-files-carry-pii
description: A game save header embeds platform and player identity as plaintext hex, so a save file is a personal-data-bearing artifact.
metadata:
  type: project
---

Measured on 2026-08-13, and worse than assumed: the save header of a current-version save
embeds the platform name, a platform account identifier and the player's display name as
plaintext hex inside an options query string. Decoding a real header yields those values as
literal readable strings. No identifier is recorded here, deliberately.

Consequences, all mandatory:

- **A save file is a personal-data-bearing artifact.** Never commit one, never attach one
  to an issue, never place one in a fixture directory. Snapshot corpora live in a
  gitignored directory only.
- **Any code path that echoes raw header bytes leaks PII** - error messages, debug dumps,
  hex previews, log lines, exception context. The header parser therefore redacts the
  options string BY DEFAULT and requires an explicit opt-in flag to render it. Redaction is
  the default state of the parser, not a mode a caller has to remember to select.
- The decoded display name and the account identifier go into the CI tier-3 PII scan
  patterns, alongside the Windows account name, machine names and absolute home paths.
- The save directory itself is named after a numeric platform account id. Auto-detect it by
  globbing for numeric directories under
  `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\<auto-detected account dir>`, picking the
  most-recently-modified when several exist, and make the choice overridable by config.
  Never hardcode it.
- The world name is operator-chosen and may be anything. Treat it as data, never as an
  identifier and never as a filename component in a tracked file.

**Why:** The repo is private first and public later, and history is what leaks. A save file
committed once is in the history forever, and the flip gate scans history rather than the
working tree for exactly that reason. The redact-by-default rule exists because leaks
happen through the paths nobody designed - a stack trace with header context attached is a
disclosure just as much as a committed file is.

**How to apply:** Treat every render of header bytes as a disclosure decision. When adding
any error path, log line or debug surface in the save reader, ask what it would print on a
real save and assume it will end up in a transcript. Keep identifiers in config and
runtime detection, never in tracked text. When writing docs or memories about save
internals, describe the SHAPE of the data and never an instance of it.

Related: [[world-token-is-the-ledger-key]], [[never-write-to-the-game]],
[[game-data-is-publisher-owned]].
