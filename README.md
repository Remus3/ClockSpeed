# Clockspeed

A local, deterministic planning and advisory system for a single-player factory-building
game.

Clockspeed reads the game's own shipped data files and your save file, computes exact
production mathematics, and tells you what to build next in one line - with the complete
derivation available on demand.

> **Status: the foundations are built and the advisor is not.** The data layer, the
> solver core, the save reader and the local dashboard exist, run and are covered by the
> test suite. The advice layer that sits on top of them is still being built, so the
> endpoints that would serve advice, audits and milestone plans answer a documented
> pending status rather than a result. `/api/health` reports the route table and what is
> wired to it, which is the authoritative answer to "what works today" - this paragraph
> is a summary of it and the code is what settles any disagreement.

---

## What it does

**Working today.**

- **Target-rate ratio solve.** Ask for a given output per minute and get the complete
  production tree: every intermediate, exact building counts, exact clock speeds,
  byproduct handling, raw input totals, total power draw and total build cost. The
  arithmetic is exact rational arithmetic, not floating point.
- **Alternate-recipe selection under constraints.** Choose the recipe set that minimizes
  raw resource use, power draw, building count or footprint - or maximizes sink points per
  unit of raw input - constrained to what you have actually unlocked.
- **Reading your world.** Clockspeed locates your install and your most recent save on its
  own, copies the save before parsing it, and serves the resulting world state and the
  normalized item and recipe registry over a local dashboard.

**Being built.**

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

Obtain a copy of the repository, then check the environment:

```
python scripts/verify_env.py
```

It exits non-zero and names the missing item if a hard dependency is absent. Contributors
run one additional step to wire the local git hooks; see `docs/OPERATIONS.md`, which owns
the bootstrap order and should be run first thing in a fresh clone.

## Running it

```
python -m clockspeed.surface
```

That starts the local HTTPS dashboard on the port recorded in `config/ports.json`. It
takes no arguments: it finds the newest save on this machine and serves it, because a
dashboard that has to be told where to look is a dashboard you have to be taught to use.

A machine with **no save and no game still starts and still binds**. The absence is
reported as a status by the endpoint that serves your world, and in the health body, which
is a true statement about a working system rather than a failure of one.

If the port is already taken the process exits and names it. No second port is ever tried
- an operator who asked for a port and silently got a different one has a dashboard they
cannot find and a companion window that will not connect.

An optional desktop companion window loads the same dashboard on a second monitor.

## What the first result looks like

Clockspeed finds your game installation and your most recent save automatically - you do
not tell it where anything is. It parses the save and serves your world state, the item
and recipe registry, and the solver.

When the advice layer lands, the same dashboard will show a short ordered list of advice
cards. A card looks like this in shape:

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
