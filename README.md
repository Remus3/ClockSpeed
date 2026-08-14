# Clockspeed

A local, deterministic planning and advisory system for a single-player factory-building
game.

Clockspeed reads the game's own shipped data files and your save file, computes exact
production mathematics, and tells you what to build next in one line - with the complete
derivation available on demand.

> **Status: phase 0 scaffold. Nothing is built yet.** This repository currently contains
> the project scaffold and its specifications. There is no working program to run. The
> sections below describe what Clockspeed is being built to be and how it will be used.

---

## What it does

- **Target-rate ratio solve.** Ask for a given output per minute and get the complete
  production tree: every intermediate, exact building counts, exact clock speeds,
  byproduct handling, raw input totals, total power draw and total build cost. The
  arithmetic is exact rational arithmetic, not floating point.
- **Alternate-recipe selection under constraints.** Choose the recipe set that minimizes
  raw resource use, power draw, building count or footprint - or maximizes sink points per
  unit of raw input - constrained to what you have actually unlocked.
- **Whole-world audit from your save.** Idle and starved machines with the upstream cause,
  overclock waste, belt and pipe saturation with the binding segment, power headroom and
  brownout risk, under-extracted nodes and extractor tier mismatches.
- **Milestone routing against any target.** Point it at the current milestone or any
  future one and get a dependency-ordered plan of what to add, upgrade, redesign or tear
  down - with "you need to replace this" called out separately from "you need more of
  this".
- **The advisor.** All of the above surfaced as advice cards: one imperative line, one
  line of reason, and a full derivation on expand that shows every input read, every rule
  that fired, every number computed and why each alternative was rejected.

## What it is not

- **Not a mod.** It installs nothing into the game and requires no mod loader.
- **Not a cheat.** It changes nothing in the game. It reads and computes.
- **Not a wiki.** Everything it knows comes from the data files your own installation
  ships with, so it matches the version you are actually running.
- **Not a chat interface.** There is no language model anywhere in the advice path. Every
  recommendation is reproducible from the same inputs; two runs on the same save that
  disagree are a bug.
- **It does not touch the game process.** No injection, no memory reading, no hooking, no
  overlay into the running executable.

## The read-only guarantee

**Clockspeed never writes to the game install directory and never modifies a save file.**
Saves are copied to a work directory before they are parsed, so a running autosave cannot
be disturbed. This is an invariant enforced by tests, not a promise in a readme.

Everything runs on your own machine. Nothing is uploaded anywhere, and there is no account
to create, no API key to supply and no network service to depend on.

## Your data stays yours

- You supply your own copy of the game. Clockspeed reads it where it is installed.
- **Game data files, extracted assets and save files are never redistributed** and are
  never committed to this repository. They belong to the game's publisher.
- Save files contain personal data in their headers. Clockspeed redacts it by default and
  never writes it to a log, a fixture or a test.
- The tests ship with small hand-written synthetic data, so the test suite runs on a
  machine with no game installed at all.

---

## Requirements

- Windows.
- A local installation of the game, kept up to date.
- Python 3. The exact required interpreter version, along with every other external
  dependency, is asserted by `scripts/verify_env.py` - run it and it prints what is found
  and what is missing.
- Node is needed only for the optional companion window, not for the core.

## Install

Nothing is installable yet at phase 0. When there is something to install, the path will
be: obtain a copy of the repository, then run the environment check.

```
python scripts/verify_env.py
```

It exits non-zero and names the missing item if a hard dependency is absent. Contributors
run one additional step to wire the local git hooks; see `docs/OPERATIONS.md`.

## Running it

**Not yet available.** When the surfaces land, Clockspeed will run as a local HTTPS
dashboard on this machine, on a port recorded in `config/ports.json`, with an optional
desktop companion window that loads the same dashboard on a second monitor.

## What the first result looks like

Clockspeed finds your game installation and your most recent save automatically - you do
not tell it where anything is. It parses the save, audits the world, and shows a short
ordered list of advice cards. A card looks like this in shape:

```
Build a second smelter line on the north iron node
  coal line saturated at its belt limit, upstream of the smelter bank
  [expand for the full derivation]
```

One line of instruction, one line of reason, and the complete chain of reasoning one
keystroke away. Cards can be accepted, dismissed, snoozed or pinned, and that state
survives reloading the world and patching the game.

---

## License

See `LICENSE`.

Clockspeed is an independent project. It is not affiliated with, endorsed by, or connected
to the publisher or developer of any game it reads.
