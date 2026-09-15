# Clockspeed

[![tier1](https://github.com/Remus3/Clockspeed/actions/workflows/tier1.yml/badge.svg)](https://github.com/Remus3/Clockspeed/actions/workflows/tier1.yml)

**A local, deterministic production planner, ratio calculator and advisor for Satisfactory.**

Clockspeed reads the data files your own installation ships with and your own save file,
computes exact production mathematics, and tells you what to build next.

It carries no item, recipe or building dataset of its own. Every fact comes out of your
install at runtime, so the answer matches the patch you are actually playing rather than
whatever version a hand-maintained table was last updated against.

```
Build a second smelter line on the north iron node
  coal line saturated at its belt limit, upstream of the smelter bank
  [expand for the full derivation]
```

One line of instruction. One line of reason. The complete chain of reasoning one keystroke
away, generated from the rule trace rather than written by hand.

---

## At a glance

| Property | |
|---|---|
| **Runs** | Entirely on your machine. No account, no API key, no network service. |
| **Reads** | Your game install and your newest save, both found automatically. |
| **Writes** | Nothing. Not to the install, not to a save. Ever. |
| **Arithmetic** | Exact rational. No floating point in the solve path. |
| **Language models** | None, anywhere in the advice path. |
| **Interface** | A local HTTPS dashboard, plus an optional companion window. |

---

## Working today

**Target-rate ratio solve.** Ask for an output per minute and get the whole production
tree: every intermediate, exact building counts, byproduct handling and raw input totals.
This is the calculator at the centre of the project.

**Alternate recipe selection under constraints.** Pick the recipe set that minimizes raw
resource use, power draw or building count, over whichever recipe set you declare
available. Those three objectives are the complete list, and anything outside it is
refused rather than quietly ignored. Reading your unlocked recipes out of the save is part
of the milestone work below, so for now the available set is supplied to the solver rather
than inferred from your progress.

**Power and clock speed mathematics.** Overclock and underclock cost curves, including the
variable-power buildings whose draw is a bounded range rather than a single number.

**Your world, read.** Clockspeed locates the install and the most recent save on its own,
copies the save before parsing it, and serves header facts, world inventory counts and the
normalized item and recipe registry over the dashboard.

**A map of what you have built.** Placements with exact translation, rotation and scale,
read straight from the save file.

## Built, not yet wired to the dashboard

**Whole-world audit.** Idle and starved machines with the upstream cause named, overclock
waste, belt and pipe throughput saturation with the binding segment identified, power
headroom and brownout risk, under-extracted resource nodes and extractor tier mismatches.
The computation is written and tested; `/api/audit` answers a documented 501 until the
advisor layer above it exists.

## Next

**Milestone routing against any target** and **the advice card surface** are specified and
seam-fixed, and not yet written. Point the router at the next milestone or one several
tiers out and it returns a dependency-ordered plan: what to add, what to upgrade, what to
redesign, what to tear down, with "replace this" called out separately from "build more of
this". The cards render that as one imperative line each, with state that survives a world
reload and a game patch. `/api/plan` and the advice routes answer 501 today and name the
work item that will build them.

`/api/health` reports the live route table and what is wired to it. That endpoint is the
authoritative answer to "what works today"; this page is a summary of it.

---

## What makes it different

**It reads your install, not a wiki.** Community datasets and calculator sites drift from
the game with every patch. Clockspeed extracts items, recipes and buildings from the
shipped files at runtime, so a patch that changes a recipe changes the answer.

**It never writes.** Saves are copied to a work directory before parsing, so a running
autosave cannot be disturbed. This is an invariant covered by tests, not a promise in a
readme.

**It is reproducible.** No language model computes, ranks, explains or renders any
recommendation. Two runs on the same save that disagree are a bug, and the full derivation
is generated from the rule trace rather than composed as prose.

**It is not a mod, a cheat, or an overlay into the running game.** Nothing is installed
into the game, no mod loader is required, and the game process is never injected into,
hooked or read from memory.

## Your data stays yours

- You supply your own copy of the game. Clockspeed reads it where it is installed.
- Game data, extracted assets and save files are never redistributed and never committed
  to this repository. They belong to the game's publisher.
- Save headers carry personal data. The header this project parses has no field to hold a
  save name, an options string or a session name, so the ordinary path cannot leak one.
  Reading those strings at all takes a separate call and an explicit opt-in argument, and
  the object it returns withholds every value from `repr`, because test runners and
  loggers repr an object before a human chooses what to print.
- The test suite ships small hand-written synthetic data and runs on a machine with no
  game installed.

---

## Requirements

| Component | Needs |
|---|---|
| **OS** | Windows |
| **Game** | A local installation, kept current |
| **Python** | 3.x, at or above the floor `scripts/verify_env.py` asserts |
| **Also** | `git` and `openssl` |
| **Node** | Only for the optional companion window, not for the core |

## Install and run

```
python scripts/verify_env.py
```

Prints every dependency found and missing, split into HARD and SOFT. It exits non-zero
only on a HARD one.

```
python scripts/make_cert.py
```

The dashboard is HTTPS only and will not start without a certificate pair. The pair is
gitignored, so every fresh clone needs this once. Skip it and the next command exits 3 and
says why.

```
python -m clockspeed.surface
```

Starts the dashboard on the port recorded in `config/ports.json`. It takes no arguments:
it finds the newest save on this machine and serves it.

A machine with no save and no game still starts and still binds; the absence is reported
as a status, not an error. If the port is taken the process exits and names it. No second
port is ever tried.

`docs/OPERATIONS.md` owns the full bootstrap order and should be run first in a fresh
clone.

---

## Direction

The data layer, the solver core, the save reader and the local dashboard are built, tested
and running. The audit engine is written and waiting on the layer above it. The work ahead
is that layer: the milestone router, and the advice surface that presents both it and the
audit.

Open work is tracked as one line per item in [`ROADMAP.md`](ROADMAP.md), which is a working
file rather than a narrative. Architectural decisions live in [`docs/adr/`](docs/adr/) and
completed work in [`docs/LEDGER.md`](docs/LEDGER.md).

## Documentation

| File | Covers |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Module map, data flow, layer seams |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Bootstrap, commands, runbooks |
| [`docs/adr/`](docs/adr/) | One file per architectural decision |
| [`ROADMAP.md`](ROADMAP.md) | Open work |

---

## License

See [`LICENSE`](LICENSE).

Clockspeed is an independent project. It is not affiliated with, endorsed by, or connected
to Coffee Stain Studios. Satisfactory and its data files are the property of their
publisher; nothing extracted from a local installation is redistributed here.
