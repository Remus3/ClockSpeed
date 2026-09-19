# Security policy

## Supported versions

Clockspeed is pre-1.0 and ships no released binaries. The only supported version is the
current tip of the default branch. Fixes land there and nowhere else, so a report
against an older checkout is welcome but will be reproduced against the tip.

---

## Reporting a vulnerability

**Use GitHub private vulnerability reporting.** Open this repository's **Security** tab
on GitHub and choose **Report a vulnerability**. That opens a private advisory draft
visible only to you and the maintainers, which is the correct place for anything that
should not be public yet.

**Do not open a public issue for a security problem**, and do not send the report by any
other route. This policy deliberately names no address: reporting through the repository
means a report never has to be typed to a person, and the maintainer identity attached
to this project's commits is not a support channel.

Expect an acknowledgement on the advisory thread. If the report is accepted, the fix and
the disclosure are coordinated on that same thread.

---

## What to include, and what to leave out

**Never attach a save file, and never paste raw save header bytes.** A save file is a
personal-data-bearing artifact: its header carries platform, account and
player-display-name strings in plaintext. `CLAUDE.md` non-negotiables 11 and 12 forbid
committing one or placing one anywhere in this repository, and that applies to an
advisory thread as well. If a report needs a save to reproduce, say so and describe the
shape of the data rather than sending it; a synthetic reproducer built the way the
fixtures under `tests/` are built is always preferred.

Redact any account identifier, world name, host name or absolute path under a home
directory before you paste a log, a stack trace or a command line.

---

## Scope

This project reads the game's own shipped data files and the player's save file, runs a
local HTTPS surface and a companion window, and computes advice. Reports are in scope
when they concern:

- A path that **writes to the game install directory or to a save file**. The project
  never writes to either - `CLAUDE.md` non-negotiable 1 - so any path that does is a
  serious finding regardless of how it is reached.
- A path that **echoes save header bytes or any personal-data string** into a log, an
  error message, a hex preview, a debug dump or exception context. The header parser
  redacts by default and requires an explicit opt-in to render; a leak around that is in
  scope.
- The **local network surface** under `clockspeed/surface/` - its certificate handling,
  its bind address and port, and anything reachable on it that should not be.
- **Untrusted input handling** in the save and game-data readers, including path
  traversal, unbounded allocation and denial of service on a malformed file.
- Anything that would cause the project to **send data off this machine**. It is
  designed to send none.

Out of scope: the game itself and its publisher's services, third-party mods, and any
issue that requires an attacker to already have write access to the machine running
Clockspeed.

---

## Hardening this repository already relies on

The tier-0 gates described in `docs/OPERATIONS.md` section 1 include a secret scan and a
character-set gate, and they are inert in a clone where the bootstrap has not been run.
If you are reporting a problem with the gates themselves rather than with the code they
guard, say which of them you had wired - `tools/precommit_gate.py` and the scripts in
`.githooks/` are separate from the convenience layer that may or may not be installed.

Contribution rules, including the ones that exist for privacy reasons, are in
[CONTRIBUTING.md](CONTRIBUTING.md).
