# Clockspeed

[![tier1](https://github.com/Remus3/Clockspeed/actions/workflows/tier1.yml/badge.svg)](https://github.com/Remus3/Clockspeed/actions/workflows/tier1.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)
![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

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
away, generated from the rule trace rather than written by hand. The card above shows the
intended format; `/api/advice` serves cards in it today, and the dashboard does not draw
them yet - see Status.

---

## At a glance

| Property | |
|---|---|
| **Runs** | Entirely on your machine. No account, no API key, no network service. |
| **Reads** | Your game install and your newest save, both found automatically. |
| **Writes** | Nothing. Not to the install, not to a save. Ever. |
| **Arithmetic** | Exact rational. No floating point in the solve path. |
| **Language models** | None, anywhere in the advice path. |
| **Interface** | A local HTTPS dashboard, plus an optional Electron companion window. |

## Why

**It reads your install, not a wiki.** Community datasets and calculator sites drift from
the game with every patch. Clockspeed extracts items, recipes and buildings from the
shipped files at runtime, so a patch that changes a recipe changes the answer.

**It never writes.** Saves are copied to a work directory before parsing, so a running
autosave cannot be disturbed. This is an invariant covered by tests, not a promise in a
readme.

**It is reproducible.** No language model computes, ranks, explains or renders any
recommendation. Two runs on the same save that disagree are a bug, and the full derivation
is generated from the rule trace rather than composed as prose.

**It is exact.** Ratios are solved in rational arithmetic and the solve path asserts that
no float reaches it, so a fractional building count is reported exactly rather than as a
rounded approximation.

**It is not a mod, a cheat, or an overlay into the running game.** Nothing is installed
into the game, no mod loader is required, and the game process is never injected into,
hooked or read from memory.

---

## Status

Pre-release, Windows only, under active development. `/api/health` reports the live route
table and what is wired to it; that endpoint is the authoritative answer to "what works
today", and this section is a summary of it.

**Working today**

- **Target-rate ratio solve** (`/api/solve`). Ask for an output per minute and get the
  whole production tree: every intermediate, exact building counts, byproduct handling and
  raw input totals.
- **Alternate recipe selection under constraints** (`/api/optimize`). Pick the recipe set
  that minimizes raw resource use, power draw or building count, over whichever recipe set
  you declare available. Those three objectives are the complete list, and anything outside
  it is refused rather than quietly ignored. Reading your unlocked recipes out of the save
  is part of the milestone work, so for now the available set is supplied to the solver
  rather than inferred from your progress.
- **Power and clock speed mathematics** (`/api/power`). Overclock and underclock cost
  curves, including the variable-power buildings whose draw is a bounded range rather than
  a single number.
- **Your world, read** (`/api/world`, `/api/registry`). Clockspeed locates the install and
  the most recent save on its own, copies the save before parsing it, and serves header
  facts, world inventory counts and the normalized item and recipe registry.
- **A map of what you have built** (`/api/map`). Placements with exact translation,
  rotation and scale, read straight from the save file.
- **Advice cards** (`/api/advice`). `GET /api/advice` lists the current cards for your
  world with their headline and one-line reason, and `GET /api/advice/<id>/derivation`
  returns one card's full derivation. `POST /api/advice/<id>/state` records a card's state
  for that world, and refuses with 403 any request that lacks the dashboard's same-origin
  header. The rules written so far cover power headroom, and the dashboard does not draw
  the cards yet. Without a save or without a game install the route answers 503.

**Built, not yet wired to the dashboard**

- **Whole-world audit.** Idle and starved machines with the upstream cause named, overclock
  waste, belt and pipe throughput saturation with the binding segment identified, power
  headroom and brownout risk, under-extracted resource nodes and extractor tier
  mismatches. The computation is written and tested, and the advice cards already read its
  power balance; `/api/audit` itself answers a documented 501 naming the open work item
  that will publish its body.

**Next**

- **Milestone routing against any target** is specified and seam-fixed, and not yet
  written. Point the router at the next milestone or one several tiers out and it returns
  a dependency-ordered plan: what to add, what to upgrade, what to redesign, what to tear
  down, with "replace this" called out separately from "build more of this". `/api/plan`
  answers 501 today and names the work item that will build it.
- **Advice rules for the other domains** - node siting and claim order, onsite processing
  versus transport, and the milestone gap - are not yet written.

---

## How it works

```
 your game install            your save file (copied first, never opened in place)
        |                                |
  clockspeed/data/                clockspeed/save/
  locate, extract,                header, chunks, property
  normalized registry             mappings, world-state model
        |                                |
        +---------------+----------------+
                        |
                 clockspeed/solve/        exact ratios, recipe optimizer,
                        |                 power and clock math
           +------------+-------------+
           |                          |
   clockspeed/audit/          clockspeed/progress/
   whole-world audit          milestone routing
           |                          |
           +------------+-------------+
                        |
                clockspeed/advisor/       deterministic rules -> one-line cards
                        |                 with a trace-generated derivation
                clockspeed/surface/       local HTTPS API and dashboard
                        |                 (computes nothing)
                     shell/               optional Electron companion window
```

Each layer consumes only the layer below it through a stated model: the solver never reads
a save, the advisor never reads the raw game files, and the dashboard never computes. The
full module map and the seams are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), and
each architectural decision has its own record in [`docs/adr/`](docs/adr/).

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
| **Python** | The minimum declared by `requires-python` in [`pyproject.toml`](pyproject.toml); `scripts/verify_env.py` asserts it and prints the version it found |
| **git** | Git for Windows |
| **openssl** | For `scripts/make_cert.py`, and for the test suite. Git for Windows ships one, but not on PATH by default - see that step below; the suite needs more of Git's tools on PATH, as [`docs/OPERATIONS.md`](docs/OPERATIONS.md) section 2 states. `scripts/verify_env.py` reports it as SOFT |
| **Python packages** | The `dev` extra in `pyproject.toml`, installed below. Of it, `pytest` and `ruff` are the two `scripts/verify_env.py` counts as HARD |
| **Node** | For the optional companion window, and to run the full test suite - without Node the dashboard panel tests fail rather than skip. Running Clockspeed itself does not need it |

### Installing the prerequisites

On a machine that has none of them yet, install from the official sources:

1. **Python** from [python.org](https://www.python.org/downloads/windows/), in a release
   that meets the `requires-python` floor in [`pyproject.toml`](pyproject.toml) - that
   file is where the version is pinned. That page lists the Python install manager first
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

`python --version` must print a version that meets `requires-python`. If it does not,
`python` is not reaching a suitable install - follow python.org's official Windows guide,
<https://docs.python.org/3/using/windows.html>, then re-run the check.

## Install and run

Run every command below from the root of the clone, in the order given.

**Two kinds of clone, two starting points.** If you only want to run Clockspeed, this
section is the whole procedure and you can skip `docs/OPERATIONS.md`. If you will commit
from the clone, do the virtual-environment step below, then run the bootstrap in
[`docs/OPERATIONS.md`](docs/OPERATIONS.md) - it runs the same hook and environment
commands as the next two steps here, plus the contributor tooling - and continue here at
`python scripts/make_cert.py`.

Create a virtual environment, activate it, and install the project with its `dev` extra:

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

The activation line is the Windows `cmd` form; in Git Bash it is
`source .venv/Scripts/activate`. A stock Windows PowerShell refuses it - running scripts
is disabled under its default execution policy, and `python` then stays the base
interpreter, so the install lands outside the virtual environment. In PowerShell, run this
before the activation line; it lasts only for that terminal and changes no machine
setting:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
```

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
where `<Git install>` is the folder Git was installed into (`git --exec-path` prints a path
that starts with it), but a default Git install does not put that folder on PATH, and the
script then exits 1 saying openssl is not on PATH. Unless `openssl version` already
answers, append the folder to PATH for this terminal first. In `cmd`:

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

Its options, all optional (`python -m clockspeed.surface --help` lists them):

| Option | Does |
|---|---|
| `--port PORT` | Binds this port instead of the recorded one |
| `--cert-dir CERT_DIR` | Reads the certificate pair from this folder |
| `--no-world` | Skips looking for a save; `/api/world` then answers 503 |

**First result.** Open `https://localhost:<port>/`, where `<port>` is that
`allocations` entry. The certificate is self-signed and your system does not trust it,
so the browser shows a certificate warning to accept before the page titled "Clockspeed
dashboard" loads. `https://localhost:<port>/api/health` answers a compact JSON object
whose top-level `status` field is `ok`.

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

### Pointing it at your game and saves

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

## How it is built

Clockspeed is developed with Claude Code working as a set of cooperating agents, under
rules that are written down and enforced by the repository rather than left to habit.

- **Defined agent roles.** Planner, builder, verifier, adversary, adjudicator,
  researcher, doc-sync and UI-auditor roles are defined in `.claude/agents/`. Work is
  test-first: the failing test lands before the code, and an adversarial pass tries to
  break a change before it is called done.
- **Gates a commit cannot skip.** Tier-0 git hooks in `.githooks/` refuse non-ASCII
  content, secrets, personal data and publisher-owned files at commit time, and the
  `tier1` and `tier2` workflows in `.github/workflows/` run the suites in CI.
- **A headless background lane.** Queued work rows are picked up by an unattended worker
  running in its own git worktree, driven by `ops/loop/queue_loop.py` with its prompt in
  `tools/headless-queue.md`, so routine items progress without an open interactive
  session. The runbook is in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).
- **A cross-repository note channel.** This project is one of several on the same machine
  that exchange plain-text notes through a file-based channel with hash-verified delivery;
  its conventions are vendored in [`docs/CHANNEL.md`](docs/CHANNEL.md).

None of this tooling is in the advice path. The product itself contains no language model
and makes no network call.

## Documentation

| File | Covers |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Module map, data flow, layer seams |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Bootstrap, commands, runbooks |
| [`docs/adr/`](docs/adr/) | One file per architectural decision |
| [`ROADMAP.md`](ROADMAP.md) | Open work, one line per item |
| [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) | How to contribute, and the rules a change must keep |
| [`.github/SECURITY.md`](.github/SECURITY.md) | How to report a vulnerability privately |
| [`THIRD_PARTY.md`](THIRD_PARTY.md) | Vendored files and their licences |

---

## License

MIT - see [`LICENSE`](LICENSE). A small number of vendored files carry their own licence;
[`THIRD_PARTY.md`](THIRD_PARTY.md) lists each one.

Clockspeed is an independent project. It is not affiliated with, endorsed by, or connected
to Coffee Stain Studios. Satisfactory and its data files are the property of their
publisher; nothing extracted from a local installation is redistributed here.
