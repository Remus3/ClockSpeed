# Clockspeed - Project Bootstrap

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**Read this first, then read `CONVENTIONS.md` in this same folder, then start.**

This is the complete specification for a project that does not exist yet. Nothing has
been built. The folder currently contains exactly two files: this one and
`CONVENTIONS.md`. Every decision below is already made and is not open for
re-litigation - see section 11 for the decision log and the fences around it.

---

## 1. What Clockspeed is

**A local, deterministic planning and advisory system for a single-player factory-building
game.** It reads the game's own shipped data files and the player's save file, computes
exact production mathematics, and issues terse, context-aware, actionable advice about
what to build next.

Four properties define it:

- **Deterministic.** No language model, no cloud service, no API key, anywhere in the
  advice path. Every recommendation is reproducible from the same inputs. If two runs on
  the same save disagree, that is a bug.
- **Local.** Everything runs on this machine. Nothing is uploaded.
- **Terse.** The operator does not want to read an essay to learn what to build next.
  Advice is one line by default. The full derivation is available on demand and is
  genuinely complete when requested.
- **Read-only against the game.** Clockspeed never writes to the game install and never
  modifies a save file. Ever.

**What it is NOT:** a mod, a cheat, a wiki, a chat interface, or anything that injects
into or reads the game process memory.

---

## 2. Verified ground truth

Everything in this table was **probed live on this machine on 2026-08-13**. It is fact,
not assumption. Re-probe before relying on it if significant time has passed.

**Re-probe 2026-08-13 (session 1).** All rows re-verified live. One correction applied:
the Docs directory holds **55** locale JSON files, not 57 (measured: 55 entries, 0
subdirectories, 0 non-JSON files). The original 57 was an overcount. No design decision
depends on it - only `en-US.json` is ever read - so the correction is recorded and
nothing downstream changes. Build string, install path, save location and the port band
(see `config/ports.json`) all confirmed unchanged as of that pass; the band has since
MOVED to 8920-8939, see section 7.1. Additional finding not in the original table: the save
directory holds **three** worlds, not one - the pinned development world (build 502094)
plus two older worlds (~149 KB and ~1.2 MB), which supplies real cross-world and
cross-save-version material for spikes S8 and S4. World names are operator-chosen personal
data and are deliberately absent here; see section 2.2.

| Fact | Value |
|---|---|
| Project root | `E:\Clockspeed` |
| Python | 3.14.4. Resolved at runtime, never hardcoded - see 2.2. **Warning: `py -3` is the WRONG interpreter on this machine** (see 2.5) |
| Node | `C:\Program Files\nodejs\node.exe` (present) |
| GitHub CLI | `C:\Program Files\GitHub CLI\gh.exe` (present) |
| Game install | `C:\Program Files (x86)\Steam\steamapps\common\Satisfactory` |
| Game build string | `++FactoryGame+rel-main-anniversary-2026-CL-502094` |
| Game version | `1.2.4.0 CL#502094` (confirmed twice: executable metadata and the in-game menu) |
| Changelist | `502094` (Anniversary 2026 release) |
| Data docs | `CommunityResources\Docs\<locale>.json` - **per locale, 55 files**, not one file |
| English docs | `CommunityResources\Docs\en-US.json`, **10,640,180 bytes** |
| Property mappings | `CommunityResources\FactoryGame.usmap`, 2,683,556 bytes |
| Save-version data | `CommunityResources\CustomVersions.json`, 20,370 bytes |
| Server API docs | `CommunityResources\DedicatedServerAPIDocs.md`, 58,094 bytes |
| C++ headers | `CommunityResources\Headers.zip`, 1,949,168 bytes |
| Save directory | `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\<numeric account dir>\` |
| Save present | Yes - three worlds, spanning save versions 52 and 60 (corrected by the session 1 re-probe) |
| Save naming | `<world name>_<DDMMYY>-<HHMMSS>.sav`, autosaves `<world name>_autosave_<N>.sav` |
| Mod loader | **Not installed.** No `FactoryGame\Mods`, no loader shim. Vanilla install. |
| Port band | 8920-8939, per `config/ports.json`. Do NOT re-derive this by probing for a free listener - that is how the original 8900-8911 band was chosen, and it collided with LegionWallpaper's 8900-8919 |

### 2.1 Three findings that shape the build

1. **`FactoryGame.usmap` ships with the game.** This is the Unreal property-mapping file.
   Modern Unreal saves serialize properties without embedded type information, and the
   usmap is what makes them parseable. Its presence on disk turns save parsing from a
   reverse-engineering project into an engineering one. **This is the single most
   important fact in this document.** Build the save reader around it.

2. **The docs are per-locale and large.** Only `en-US.json` is ever read. It is 10.6 MB
   and it must be parsed once into a compact normalized artifact that everything else
   consumes. Nothing downstream ever touches the raw file.

3. **`DedicatedServerAPIDocs.md` and `Headers.zip` are on disk.** Neither is a v1
   dependency, but both are free, local, first-party reference material. The headers in
   particular are the authoritative answer to "what is the real shape of this struct"
   when the save parser disagrees with an assumption.

### 2.2 Privacy note, non-negotiable

The save directory is named after a numeric platform account id. **That id is personal
data and must never appear in a tracked file, a commit message, a log, a fixture, or a
test.** Auto-detect it by globbing for numeric directories under the save root. If more
than one exists, pick by most-recently-modified and make it overridable by config.

The same applies to the world name, the Windows account name, and any absolute path
containing a home directory. Configure them; never hardcode them.

**Measured, and worse than assumed:** the save header of a current-version save embeds the
platform name, a platform account identifier, and the player's **display name** as
plaintext hex inside an options string. Decoding a real header yields the literal strings
`STEAM`, `None`, an account id blob, and the player's display name.

Consequences, all mandatory:

- A save file is a **personal-data-bearing artifact**. Never commit one, never attach one
  to an issue, never place one in a fixture directory.
- **Any code path that echoes raw header bytes leaks PII** - error messages, debug dumps,
  hex previews, log lines, exception context. The header parser must redact the options
  string by default and require an explicit opt-in flag to render it.
- Add the decoded display name and account id to the tier-3 PII scan patterns (run locally - ADR 0025).
- The world name is operator-chosen and may be anything; treat it as data, never as an
  identifier and never as a filename component in a tracked file.

### 2.3 The pinned development world

The operator has designated a specific world as the project's reference world. It was
created 2026-08-13 and is effectively empty, which makes it an ideal first parse target.

| Property | Value |
|---|---|
| Session / world name | Operator-chosen. Personal data - never recorded in a tracked file (section 2.2) |
| Starting area | Dune Desert (the game labels it "recommended for advanced pioneers") |
| Skip Onboarding | No - the world starts inside the onboarding objective chain |
| Creative Mode | No |
| Game Modes (modifiers) | No |
| Session type | Single Player |
| Saves present | A manual save (103,405 bytes) and an autosave (102,008 bytes) |
| Play duration at capture | Under one minute |

**Why this world is an asset, not just a target:**

- **A near-empty world is inspectable ground truth.** Nothing is built, so anything the
  parser reports as a built object is either a level-baked actor or a bug. That is the
  cleanest possible baseline for validating the save reader.
- **102 KB with nothing built** means the file is dominated by level-resident actors
  rather than player construction. That is a positive signal for spike S4 (resource-node
  coordinates), though it is a signal and not proof.
- **The world will grow as the operator plays**, producing a natural progression of
  fixtures - empty, early, mid, late - against the same world identity. Snapshot copies at
  milestones into a gitignored corpus directory and use them as regression inputs.
- **Creative and modifiers are both off**, so this world is a clean vanilla baseline with
  no rule-distorting settings.
- **Onboarding is ACTIVE.** Early unlock and schematic state will look unusual compared to
  a skipped-onboarding world. Do not treat this world's early unlock shape as the general
  case when settling spike S6.

### 2.4 Save header facts already measured

Measured directly from the operator's local save library. This substantially de-risks the
save reader and settles one open design question outright.

**The library is not uniform, and that is the central fact.** Fourteen saves carry four
distinct combinations of the three leading version fields:

| Header ver | Save ver | Build changelist | Saves |
|---|---|---|---|
| 10 | 36 | 211839 | 3 |
| 13 | 42 | 273254 | 1 |
| 14 | 52 | 463028 | 8 |
| 14 | 60 | 502094 | 2 |

**Header layout is HEADER-VERSION DEPENDENT. There is no single fixed layout**, and an
earlier revision of this section stated one. See `docs/adr/0007`.

Every header version opens with the same three int32 fields:

| Offset | Type | Meaning |
|---|---|---|
| 0 | int32 | header version |
| 4 | int32 | save version |
| 8 | int32 | build changelist - on the newest saves this matches the installed game exactly |

**The string block that follows differs by header version, in COUNT and in ORDER:**

| Header ver | Strings, in file order | Count | Verified on |
|---|---|---|---|
| 10 | map name, map options, session name | 3 | 3 of 3 saves |
| 13 | map name, map options, session name | 3 | 1 of 1 save |
| 14 | save name, map name, map options, session name | 4 | 10 of 10 saves |

**How the labelling was established - by property, never by value.** On header versions 10
and 13 the FIRST string equals `Persistent_Level` and the SECOND contains `?`. On header
version 14 the SECOND string equals `Persistent_Level` and the THIRD contains `?`. The map
name is a fixed game constant and the options string is a query string, so each field is
identifiable without reading a single personal-data value. **Do not identify these fields
by reading them** - section 2.2 and `docs/adr/0007` explain why the shifting order makes a
field-name-targeted redactor unsafe.

**After the string block every header version agrees**, in this order: int32 play duration,
int64 datetime ticks, **one int8 whose MEANING is unverified**, int32 editor object version,
a length-prefixed mod metadata string, int32 is-modded flag, then the length-prefixed save
identifier - which is the world token.

**That int8 is measured in POSITION and unverified in MEANING, and the distinction is not
pedantic.** An earlier revision of this section labelled it "session visibility", which
implies a flag. It is not one. Measured across all 14 saves: the value is `0x00` on header
versions 10 and 13 and on header 14 / save 60, and one of `0x10`, `0x50`, `0x90` or `0xD0`
on the eight header 14 / save 52 saves. A parser treating it as a 0/1 flag is wrong on 8 of
14 of the operator's own files. Its POSITION is nonetheless solid, and independently
anchored: the int32 immediately after it reads `40` on all 14 saves, so the alignment either
side of it is confirmed rather than assumed. Read it, carry it, do not interpret it. The
local authority for settling what it means is `CustomVersions.json` or `Headers.zip`, per
the note at the end of section 3.

**The header tail after the save identifier is version dependent too:**

| Header ver | Tail bytes before the chunk magic |
|---|---|
| 10 | 0 - the chunk magic begins immediately |
| 13 | 28 |
| 14 | 28 |

**The 28 bytes' internal structure is UNVERIFIED.** Only the total length was measured. Do
not invent a field breakdown for it - skip it by length, and if a parser ever needs a field
inside it, measure it first and record the measurement here.

Strings are **length-prefixed with an int32 count that includes the trailing null**.
Confirmed twice: a 15-character save name measured 16, and `Persistent_Level`, which is
16 characters, measured 17.

**The world identity key is SOLVED.** The header carries a 22-character base64url token
(16 bytes). Measured across four saves spanning three worlds:

| Save | Save ver | Build | Token |
|---|---|---|---|
| a manual save of world A | 60 | 502094 | token A |
| an autosave of world A | 60 | 502094 | token A - IDENTICAL to the row above |
| a save of world B, older | 52 | 463028 | token B |
| a save of world C, older | 52 | 463028 | token C |

Tokens are 22 characters of base64url (16 bytes). The literal values are world-identity
personal data and are deliberately not recorded here (section 2.2); what matters to the
design is the relation between them, which the table preserves.

**Two different saves of the same world share the token; different worlds do not.** That
is exactly the stable, filename-independent world key section 5.2 requires. Use it.

**Honest limits on that claim - UPDATED by the session 1 re-probe.** The original sample
was four saves across three worlds, and the stated open question was whether the token
survives a game version upgrade of the same world. **It does.** Re-measured across the
full local library - 14 saves, grouped by token rather than by filename - there are
exactly 3 distinct worlds, and one of them carries an identical token across 5 saves
spanning THREE different game builds and three different save versions. Token stability
across a version upgrade is therefore measured, not assumed.

Whether it is a world seed or a session GUID remains unknown and still does not matter for
the ledger's purposes. **Phase 4 must still assert token stability across a save/reload
cycle as a test**, and the ledger must still tolerate a key it has never seen by treating
it as a new world rather than failing.

**Method warning, learned the expensive way in session 1:** do NOT group saves by
filename. Autosaves rotate and timestamped saves of one world look like distinct worlds to
a filename heuristic. A first grouping attempt in session 1 inflated 3 worlds into 6 and
would have produced a false result for spike S8. The token is the only sound key - which
is exactly what section 5.2 already requires for the ledger.

**Version dispatch is a day-one requirement, not a future concern.** The library table at
the top of this section spans four builds and three header versions. A parser written
against header version 14 alone fails outright on the operator's own oldest saves - not
subtly, and not later. An earlier revision of this section claimed header version was
stable at 14; the re-probe disproved it.

### 2.5 Interpreter trap - measured session 1

**There are four Python installations on this machine and `py -3` selects the wrong one.**

| Invocation | Resolves to | pytest / ruff / mypy |
|---|---|---|
| `py -3` | a `pythoncore-3.14-64` install | **absent** |
| `python` | the `Programs\Python\Python314` install | present |

Both report version 3.14.4, which is exactly why this is dangerous - a version check
passes and the toolchain is still missing. The `py` launcher does not even register the
Python314 install, so `py -3` can never reach it.

Consequences, all mandatory:

- **Never resolve the interpreter as `py -3`.** Resolution order is `$CLOCKSPEED_PYTHON`,
  then `python`, then `python3`, then `py -3` as a last resort.
- `scripts/verify_env.py` must assert that the RESOLVED interpreter can import pytest and
  ruff, and must HARD-fail if it cannot. Reporting the version alone is not sufficient and
  would have passed this machine while the pre-push suite was unrunnable.
- This is a concrete instance of the `CONVENTIONS.md` section 16 lesson: a hook can be
  correctly wired, syntactically valid and still do nothing, because it resolved an
  interpreter that cannot run the check it invokes.

---

## 3. Unverified assumptions - session 1 spike list

These are stated as expectations, not facts. **Each one is a spike with a binary
acceptance criterion. Verify before building on it.** Do not let an assumption here
silently become a foundation.

| # | Assumption | How to settle it | If false |
|---|---|---|---|
| **S1** | `en-US.json` is UTF-16 LE with a BOM | Read the first 4 bytes. **Strong hint it is:** `io.json` is 5,181,010 bytes against the family's uniform ~10.64 MB - almost exactly half, which is what a UTF-8 sibling among UTF-16 files looks like. Sniff, never assume. | Detect encoding at read time; support both |
| **S2** | The docs file is a JSON array of `{NativeClass, Classes[]}` groups, with recipes carrying ingredient/product/duration/produced-in fields and descriptors carrying display name, form, energy and sink-point values | Parse it and dump the distinct `NativeClass` values plus one sample of each | Derive the real schema from the dump; the normalizer is written against what is there, not what was expected |
| **S3** | Numeric fields are embedded in string blobs needing a secondary parse (Unreal serializes struct arrays as text) | Inspect ingredient and product fields directly | Write a dedicated blob parser with its own test suite |
| **S4** | **The `.sav` contains resource-node actors with world coordinates** | Parse a save, enumerate actor class names, grep for resource-node classes, and check for a transform on each | **This is the one that matters.** Fall back to extracting node data from the shipped game assets. That fallback is a large task with a third-party-tool license gate on it - see section 8.3 |
| **S5** | **Settled, and settled as VERSION DEPENDENT - see sections 2.4 and 3.1.** Header layout, string count and order, the tail size, the world key and the chunk framing are all measured, and each of them varies by version | Done. What remains open is only the 28-byte header tail's internal structure, and whether the framing keys on header or save version | Follow the actual bytes; `CustomVersions.json` and `Headers.zip` are the local authority. **Do not assume any single fixed layout** - that assumption was made once and was wrong |
| **S6** | Unlock state (milestones, tiers, alt-recipes purchased, scanned resources) is recoverable from the save | Locate the schematic-manager and unlock-subsystem actors | **The advisor cannot ship without this.** Everything in section 5 is gated on knowing what the player has unlocked. If it is unrecoverable, add a manual unlock-state entry surface as a stopgap and file the real fix |
| **S7** | Power-consumption scaling under overclock follows a fixed exponent found in the docs data | Extract the exponent field from building classes rather than hardcoding a constant | Take the value from data; never hardcode a magic number that the game can patch |

| **S8** | Resource node placement and purity are FIXED across all worlds, so node data is a static property of the map rather than of the save | The main menu exposes a **"Show Seed"** control for the current session, which proves a per-world seed exists. Determine what that seed actually varies. Compare node-relevant data between two worlds with different seeds | **If node placement or purity is seed-dependent, any static node table is wrong for this world and section 8.3 collapses to a single option: read nodes from the save.** That would make S4 not merely important but load-bearing |

**S4, S6 and S8 are the spikes that can change the shape of the product. Run them
FIRST, before any solver work.** Report all three results explicitly before proceeding.

### 3.1 Spike results - session 1, 2026-08-13

All three shape-changing spikes are SETTLED against live data. Full reasoning and stated
limits are in the ADRs; this is the summary.

| Spike | Binary answer | ADR |
|---|---|---|
| **S8** | **NO** - node placement is NOT seed-dependent. Two distinct worlds on the same build have byte-identical node sets: 626 nodes, zero differences. Node data is a property of the MAP. | `docs/adr/0002` |
| **S4** | **YES for geometry, NO for semantics.** 626 node actors, 626 with a valid transform. But nodes carry no property payload, and purity / resource type are absent from every save examined. | `docs/adr/0003` |
| **S6** | **YES.** A mature world carries purchased schematics, 246 schematic paths including alt-recipes, game phase, research trees, scanned resources and the feature-unlock booleans. | `docs/adr/0004` |

**S5 is measured, and the framing is VERSION DEPENDENT.** An earlier revision of this
section stated the framing below without a version qualifier. That unqualified claim is
wrong: a parser built from it fails on 3 of the operator's 14 saves and looks correct on
the other 11 - the worst available failure shape. Corrected:

| | Header ver 13 and 14 | Header ver 10 |
|---|---|---|
| magic | `0x9E2A83C1` | `0x9E2A83C1` |
| marker | `0x22222222` | `0x00000000` |
| int64 max chunk size | 131072 | 131072 |
| int8 compression algorithm | 3 (zlib) | **absent - no such byte at all** |
| compressed and uncompressed sizes | each written TWICE, in the order `c, u, c, u` | each written TWICE, in the order `c, u, c, u` |
| zlib stream begins at | magic + 49 | magic + 48 |

**The size-block ORDER is measured, not assumed, and the distinction mattered.** The four
int64s are `compressed, uncompressed, compressed, uncompressed` - NOT
`compressed, compressed, uncompressed, uncompressed`. Measured across all 14 saves and all
three header versions: the first and third values agree, the second and fourth agree, the
first value is the compressed size, and inflating exactly that many bytes yields exactly the
declared uncompressed size. The alternative reading is ruled out because the first two values
differ on every real chunk. A parser that guessed the other order would be wrong on every
real save while passing a synthetic corpus that encoded the same guess.

**Also version scoped, and measured on real bodies rather than on fixtures:** the decompressed
body opens with an int64 length on header versions 13 and 14, where that int64 equals the
body length minus 8. On header version 10 / save version 36 it does NOT: there the leading
**int32** equals the body length minus 4. Both were confirmed by decompressing a real save of
every version through the shipped walker.

**Real bodies are much larger and much more chunked than any fixture.** Measured: 11 chunks
and 1,440,651 bytes on the newest save version, and 138 chunks and just over 18 MB on the two
oldest. A walker validated only against a small corpus has not been shown to handle either.

**UNDETERMINED - whether the framing variant keys on HEADER version or on SAVE version.**
The two covary across the entire local library (10 with 36, 13 with 42, 14 with 52 and 60),
so **no local file can separate them.** This is recorded as undetermined rather than
resolved by picking the likelier one. Detect the variant from the marker word, which is
directly observable, and cross-check it against both version fields. See `docs/adr/0007`.

**The actor header layout is save-version dependent.** The transform block sits at +8 after
the instance-name string on save versions 52 and 60, and at +4 on versions 36 and 42. This
confirms section 2.4's warning that version dispatch is a day-one requirement.

### 3.2 Data-layer spike results - session 1

Full report: `docs/_archive/spike-report-s1-s2-s3-s7.md`.

| Spike | Binary answer |
|---|---|
| **S1** | **YES** - `en-US.json` is UTF-16 LE with a BOM (`FF FE 5B 00`). But the family is MIXED: 54 of 55 files are UTF-16 LE, `io.json` alone is UTF-8 with no BOM. Sniff per file. |
| **S2** | **YES**, with corrections below. 114 `NativeClass` groups, 2,868 entries, `ClassName` unique document-wide. |
| **S3** | **YES** - ingredients and products are Unreal text-serialized struct blobs needing a second parser. Every scalar in the document is a string, including durations. |
| **S7** | **YES for the exponent, NO for "fixed"** - see the refutation below. |

**S7 is PARTIALLY REFUTED.** The assumption said a fixed exponent. The data carries
`mPowerConsumptionExponent` on 62 entries with **two distinct values** - `1.321929` on
manufacturers and extractors, `1.600000` on fixed-draw infrastructure. A single hardcoded
constant would be wrong for 42 of 62 buildings. Read it per building class. Separately,
S7 is **incomplete for the power model**: the overclock ceiling is absent from the docs
file entirely (every entry reports `mMaxPotential` of 1.0), so the ceiling must come from
elsewhere - `Headers.zip` is the next place to look. S7 is YES for the exponent and OPEN
for the ceiling.

**S2 corrections that will silently break a normalizer:**

- The duration key is **misspelled in the game data**: `mManufactoringDuration`. It sits
  beside the correctly spelled `mManufacturingMenuPriority` in the same record. Use the
  misspelling verbatim. `mEstimatedMininumPowerConsumption` is likewise misspelled.
- **All 547 `FGBuildingDescriptor` entries have an EMPTY `mDisplayName`.** Building names
  live on the `FGBuildable*` entries. A normalizer that reads names from the descriptor
  gets 547 nameless buildings and passes its own tests - a section 7.2 fixture failure.
- `mResourceSinkPoints` is present on only 191 entries across 11 groups, not on descriptors
  generally, and 4 of 122 `FGItemDescriptor` entries lack it.
- Only 291 of 872 recipes name an automated production building. Pillar 1 must filter on
  `mProducedIn`, not on group membership.

**S3 grammar traps:**

- The delimiter is the double quote and a single quote appears INSIDE the value. Split on
  the double quote first or every asset path corrupts.
- `mProducedIn` uses a DIFFERENT grammar from `mIngredients` and needs its own parser.
- **Fluid amounts are litres, x1000 against solids, and the scale factor is NOT uniform.**
  Two of 100 sampled liquid pairs are not multiples of 1000, and **both live in the SAME
  recipe, one on each side**: that recipe takes an acid at 2500 as an INGREDIENT and emits
  water at 1500 as a PRODUCT. Integer division by 1000 silently loses half a cubic metre
  per cycle. The unit depends on the ITEM's `mForm`, which lives in a different group, so
  the blob parser cannot determine units on its own.
  **Corrected 2026-08-13 by live re-probe (session 2).** The session 1 spike report put
  both fractional amounts on the ingredient side. That is wrong about the side, not about
  the counts. It matters because a fixture written from the original wording exercises
  ingredient rounding only and never touches the product side - which is where the only
  other fractional fluid in the entire document actually is. Fixtures must carry a
  fractional amount on BOTH sides.

**Two traps beyond the spike questions:**

- **Trial-decode encoding sniffing is unsound.** Python's `utf-16` codec decodes the UTF-8
  `io.json` WITHOUT raising and returns mojibake. Only the BOM-byte test is valid. The
  failure is asymmetric, so a sniffer that tries UTF-16 first is silently wrong.
- The English display strings contain U+2014, smart quotes and 1,305 occurrences of U+202F.
  The generated registry is gitignored so it may hold them, but any tracked doc, test or
  fixture quoting a display name will trip the character-set gate - correctly.

S8 was raised by the presence of a "Show Seed" button in the game's own session menu. It
is cheap to answer and it determines whether section 8.3 has a fallback at all, so answer
it before committing to the S4 fallback path.

---

## 4. The product: five pillars

All five ship. Pillars 1 and 2 are the engine; pillar 3 is the world reader; pillars 4
and 5 are what the operator actually looks at.

### Pillar 1 - Target-rate ratio solve

Given "I want N per minute of item X", emit the complete production tree: every
intermediate, exact building counts, exact clock speeds, byproduct handling, raw input
totals, total power draw, and total build cost.

- **Exact rational arithmetic.** Use `fractions.Fraction` end to end. Floating point
  drift in a ratio calculator is a correctness bug, not a rounding nuisance.
- Handle recipe loops and byproducts (a byproduct that feeds back into its own chain is
  the classic hard case; get it right and test it explicitly).
- Solve both directions: "I want N of X" and "I have this raw input, what is the best
  output".

### Pillar 2 - Alt-recipe selection under constraints

Given an objective and the set of unlocked recipes, choose the recipe set that optimizes
it. This is the hard, differentiating problem.

Objectives, each selectable and combinable with weights: minimize raw resource
consumption, minimize power draw, minimize building count, minimize footprint proxy,
maximize sink points per unit of raw input.

- **Start dependency-free.** Implement exact ratio solve plus a branch-and-bound or
  weighted-greedy search behind a **pluggable optimizer interface**.
- An external linear/integer programming library is a **later, gated** decision. It goes
  through the section 14 license gate in `CONVENTIONS.md` first, and it must slot behind
  the existing interface without changing a single caller. Do not take the dependency in
  phase 2.
- Constrain by what is genuinely unlocked, not by what exists in the data.

### Pillar 3 - Whole-world audit from the save

Diff what is actually built against what should be. Report:

- Idle or starved machines, and the upstream cause of the starvation.
- Overclock waste: machines clocked above what their input supply can feed.
- Belt and pipe throughput saturation, and which segment is the binding constraint.
- Power headroom, brownout risk, and fuel-chain sizing against actual consumption.
- Resource nodes claimed but under-extracted, and extractor tier mismatches.
- Sink-point throughput actually achieved.

### Pillar 4 - Milestone and progression routing

Point the system at **the current milestone OR any future milestone or phase target** and
get what must be added, upgraded, redesigned or torn down to reach it from the current
world state.

- The target is a free choice, not a fixed pointer at "next". Selecting a target three
  tiers out and getting a redesign plan is an explicitly required capability.
- Output is a dependency-ordered plan, not an unordered list of gaps.
- Distinguish "you need more of this" from "you need to replace this" - the second is the
  expensive one and must be called out as such.

### Pillar 5 - The advisor

The synthesizing layer. Everything above feeds it. Specified in full in section 5.

---

## 5. The advisor specification

The advisor is the product's face. Get this right and the rest is plumbing.

### 5.1 Advice card contract

Every piece of advice is a **card** with a stable identity and three rendering tiers:

| Tier | Content | Default |
|---|---|---|
| **1 - Headline** | One line. Imperative. What to do. No reasoning. | Always shown |
| **2 - Reason** | One line. The binding constraint or trigger. Example shape: "coal line saturated at 780/min". | Shown inline |
| **3 - Derivation** | The complete chain: every input read with its source, every rule that fired, every number computed, every alternative considered and **why each was rejected**. | On expand only |

Tier 3 is a **learning surface**, not a debug dump. It is written to be read by a human
who wants to understand the how and why so they can reason it out themselves next time.
It is generated from the same rule execution trace that produced tiers 1 and 2, so it can
never drift from them. **Do not write three separate renderings by hand** - one trace,
three projections.

### 5.2 Card identity and persistence

Cards need stable identity so state survives recomputation.

- **Card ID** is a deterministic hash of `(rule_id, subject_key, target_milestone)`.
  Recomputing on a changed save must produce the SAME id for the same underlying advice,
  or all persisted state is lost on every reload.
- **`subject_key`** is the stable identity of the thing the advice is about (a node, a
  factory region, a recipe, a milestone). It must not encode anything volatile.

Two persistence layers, both durable across game sessions, reloads and patches:

1. **Per-world ledger**, keyed to the 22-character base64url world token in the save
   header (section 2.4), **never to a save filename** - filenames change on every save and
   autosaves rotate. The token was measured stable across two saves of the same world and
   distinct across three worlds. States: `new`, `accepted`, `dismissed`, `snoozed(until)`,
   `pinned`, `completed`. `completed` is set automatically when the world state satisfies
   the advice, and that transition is itself worth surfacing.
2. **Global per-rule mute.** Any rule type can be silenced across all worlds, forever,
   from the card itself. This is the "stop telling me about power, I know" control.

The ledger is a plain JSON file in the project data directory, written atomically. It is
gitignored. Include a schema version field from the first write.

### 5.3 Advice domains, all four in v1

**D1 - Node siting and claim order.**
Which raw resource nodes to take next and in what order, given purity, distance to the
player's chosen hub, current extractor tier, current logistics unlocks, and what the
current or selected target milestone actually demands. Output is an ordered list with a
reason per entry.

**D2 - Process onsite versus transport, and by what method.**
For a given node or cluster, decide whether to refine at the source or ship raw, then
select the transport method from what is genuinely unlocked - belts, pipes, trains,
vehicles, drones. The decision must account for throughput per unit of transport, power
cost of the transport itself, build cost, and the ratio compression that onsite
processing buys. **This is the highest-value advice in the product** because it is the
decision players most often get wrong and most expensively.

**D3 - Milestone gap analysis against any target.**
Pillar 4, surfaced as cards. The target selector is a first-class control.

**D4 - Power and fuel planning.**
Generation headroom against actual and projected draw, fuel chain sizing, brownout risk
ranked by how close each is, and when the next generation tier becomes worth the
transition rather than merely available.

### 5.4 Rule engine design constraints

- **Rules are data-driven and modular.** A game patch that changes recipes, buildings or
  milestones must be absorbable by re-running the extractor and updating a version pin.
  It must NOT require editing rule logic. If a patch forces a rule edit, that rule
  encoded a fact it should have read from data - fix the rule, not just the symptom.
- **Every rule declares its inputs explicitly.** The trace, and therefore tier 3, is
  generated from that declaration. A rule that reads an undeclared input is a bug and a
  test should catch it.
- **Every rule declares which unlocks it requires** so it cannot suggest something the
  player cannot build.
- **Rules are individually testable** against a synthetic world fixture with no save file
  and no game install present. The rule suite must run in CI on a clean machine.
- **No rule may recommend an action whose preconditions are unmet.** This is an invariant
  with a property test over generated world states, not a code review item.

---

## 6. Architecture

```
E:\Clockspeed\
  clockspeed/
    data/           game data extraction and normalization
      locate.py       find install, saves, account dir - all auto-detected
      docs_extract.py read en-US.json, emit the normalized registry
      registry.py     the normalized item/recipe/building/milestone model
      version.py      build-string pin, patch detection, drift guard
    save/           save file reading
      header.py       save header parse
      chunks.py       decompression and chunk walk
      usmap.py        property mapping loader
      objects.py      actor and component deserialization
      world.py        the world-state model the rest of the app consumes
    solve/          the deterministic engine
      exact.py        Fraction arithmetic primitives
      ratio.py        pillar 1 target-rate solve
      optimize.py     pillar 2, behind OptimizerBackend
      backends/       pluggable optimizer implementations
      power.py        power and clock mathematics
    audit/          pillar 3 whole-world audit
    progress/       pillar 4 milestone routing
    advisor/        pillar 5
      rules/          one module per rule family, data-driven
      trace.py        rule execution trace, the source of all three tiers
      cards.py        card identity, rendering tiers
      ledger.py       per-world state + global mutes, atomic writes
    surface/
      server.py       local HTTPS API and dashboard, port 8920
      api/            JSON endpoints
      web/            dashboard assets
  shell/            Electron companion window
  tests/
  tools/            gates, guards, sync, probes
  scripts/          install_hooks.py, verify_env.py
  docs/
  memory/
  data/             generated artifacts - GITIGNORED
```

**Seam discipline.** Each layer consumes only the layer below it through a stated model.
`solve/` never reads a save. `advisor/` never reads the raw docs file. `surface/` never
computes. A layer that reaches past its neighbor is a design bug.

---

## 7. Surfaces

### 7.1 Local HTTPS dashboard - port 8920

The primary surface. Self-signed certificate, generated by a tracked script into a
gitignored location. Serves the JSON API and the dashboard.

Endpoints, minimum: `/api/health`, `/api/world` (current parsed state),
`/api/registry` (the item, recipe and building vocabulary the solver doors take),
`/api/advice` (cards with tier 1 and 2), `/api/advice/<id>/derivation` (tier 3),
`/api/advice/<id>/state` (accept, dismiss, snooze, pin), `/api/solve` (pillar 1),
`/api/optimize` (pillar 2), `/api/audit`, `/api/plan?target=<milestone>`,
`/api/map` (node and built-actor placement, item totals and extractor throughput),
`/api/power` (declared draw, draw at a clock, and what is known about the ceiling).

`/api/power` was added on the same word again: `clockspeed/solve/power.py` was
written, tested and reachable from no route at all, so MEASURED ZERO of the
templates then published named a megawatt figure, a clock or the un-sharded base
in any response body. A capability nobody can ask for is indistinguishable from
one that was never built.

`/api/map` was added under CS-977 on the same word: `/api/world` counts nodes and
never lists them, so MEASURED ZERO of the templates then published named a single
coordinate, and no surface could draw the world the operator asked to see.

`/api/registry` was added under CS-912 and is what the word "minimum" above was
for. `/api/solve` and `/api/optimize` both require `targets`, `recipes` and
`raw_items`, and every value in all three is a registry ClassName - so with no
route publishing that vocabulary, MEASURED ZERO of the routes then published
named a single item or recipe identifier in any response body, and both solver
doors were live and unreachable at the same time.

### 7.2 Electron companion window - v1

Frameless, always-on-top-optional, resizable, remembers position and size. It loads the
local dashboard. It must handle the self-signed certificate cleanly rather than
disabling certificate validation wholesale.

**It is a companion window, not an overlay.** Designed for a second monitor or alt-tab.

### 7.3 In-game overlay - built later, behind a flag

A transparent, click-through, always-on-top window bound to the game window. Deliberately
deferred until the data layer is proven, but the companion is architected so this is a
mode of the same shell rather than a rewrite.

Two facts that make this viable and worth doing later: **the game has no anti-cheat**, and
**it supports borderless-windowed**, which is the display mode an overlay needs.

The overlay is a **flagged mode, default off**, and it must degrade to the companion
window if window binding fails for any reason. It never blocks input it did not intend
to receive.

### 7.4 OCR and CV - a later ingestion lane, not v1

Reading the in-game HUD by screen capture is a legitimate future data source for anything
the save file cannot provide (live rates, transient state). It is explicitly allowed and
out of scope for v1. If it is built: capture stage, region registry, cheap deterministic
recognizer first with escalation only on miss, and a confidence score on every field.

---

## 8. Data layer detail

### 8.1 Game docs extraction

- Read from the local install at runtime. **Never commit the docs file, never commit any
  file extracted from the game install, and never commit a save file.** Add these to
  `.gitignore` before the first commit.
- Sniff the encoding (spike S1). Parse once. Emit a compact normalized registry into
  `data/` (gitignored) plus a small **content hash and build-string pin** that IS tracked.
- The tracked pin is what the drift guard checks. When the game patches, the hash changes,
  the guard goes red, and the re-extract runs. That is the intended workflow and it should
  be one command.
- Test fixtures are **small synthetic registries hand-authored in the repo**, never slices
  of real game data. This keeps the repo clean of publisher-owned content and makes the
  rule suite runnable on a machine with no game installed.

### 8.2 Save reading

- **Copy the save to a work directory before parsing.** The game holds handles during
  autosave; parsing in place will eventually hit a locked file or a half-written one.
- Never write to the save directory. Not once, not for anything.
- Build around `FactoryGame.usmap`. Load it from the install, cache the parsed form.
- Parse defensively. **An unknown actor class is logged and skipped, never fatal.** This
  single decision is what makes mod tolerance (section 9) nearly free.
- Support both manual saves and autosaves; default to most-recently-modified across both.

### 8.3 Resource node coordinates - the S4 decision tree

**RESOLVED in session 1. The tree below is kept for its reasoning; the outcome is stated
here.** S8 answered NO (placement is map-fixed, not seed-derived), so steps 2 and 3 stay
valid. S4 answered YES for geometry and NO for semantics. **Step 1 as originally written
was wrong** - it said transforms in the save meant "done, zero external dependency", and
that is only true for positions. Node resource type and purity are NOT in the save, so
step 2 is still required for the semantics half. See `docs/adr/0002` and `docs/adr/0003`.

0. Run spike S8 first. **If node data is seed-dependent, steps 2 and 3 are invalid and
   the save is the only correct source** - S4 then has no fallback and must succeed.
   ANSWERED: not seed-dependent. Steps 2 and 3 remain available.
1. Run spike S4. If the save carries resource-node actors with transforms, that settles
   POSITIONS only - zero external dependency for geometry, use it. **It does not settle
   what each node contains.** Nodes carry no serialized property payload, because resource
   type and purity are level-asset defaults and a save stores only deltas from defaults.
   Positions alone cannot order a claim list, so D1 is not complete at this step.
2. If not, the fallback is extracting node data from the shipped game assets. This is a
   significantly larger task and typically wants a third-party asset-parsing library.
   **That library goes through the license gate in `CONVENTIONS.md` section 14 before it
   is used, and the result is stated explicitly in the ledger.**
3. Do not lift a community-compiled node dataset. It carries provenance risk that a later
   public flip makes worse, and the two paths above are both cleaner.
4. If both paths stall, D1 ships degraded - siting advice restricted to nodes the player
   has already discovered - and the full version is filed as a gated item. **Say so
   loudly rather than shipping quiet partial coverage.**

---

## 9. Mod stance

**Architecturally first-class, content backlogged.** Concretely:

- **Now:** all identifiers are namespaced so modded content cannot collide with vanilla.
  The save parser tolerates unknown classes without crashing. The registry tolerates
  unknown recipes and buildings, flags them, and marks any solve that touched one as
  `contains_unmodeled_content`. A feature-flag registry exists from phase 0 so per-mod
  behavior can be switched on and off individually. The mod-loader presence check is part
  of environment detection even though no loader is currently installed.
- **Backlogged:** actual mod-specific recipe modelling, mod-aware advice rules, and any
  per-mod compatibility work. These are `BACKLOG.md` items with conditional triggers.

**The invariant:** a modded save must never produce a crash or a silently wrong number. It
may produce an explicit "this world contains content I do not model" and a reduced answer.
That is acceptable; a confident wrong answer is not.

---

## 10. Build phases

Each phase has a testable acceptance criterion. Do not advance on a phase whose criterion
is unmet. Phases 0-3 are one working unit each; 4-5 are larger.

### Phase 0 - Scaffold
Repo init, `.gitignore` first, LICENSE, `CLAUDE.md`, `README.md` stub, the doc topology
from `CONVENTIONS.md` section 2, `memory/`, `.githooks/` plus `install_hooks.py`,
`.claude/` settings and agents and commands, `verify_env.py`, CI tier 1 and 2 workflows,
doc size budgets, port allocation recorded.
**Acceptance:** staging a banned character and attempting a real commit leaves HEAD
unchanged. `verify_env.py` exits zero. A clean clone plus `install_hooks.py` reproduces
the gate.

### Phase 1 - Spikes
Order: **S8, S4, S6** first (they can change the product shape), then S1, S2, S3, S7.
S5 is mostly settled by section 2.4 - only the body framing remains.
**Acceptance:** a written spike report with a binary answer per spike, and the S4, S6 and
S8 decisions recorded in `docs/LEDGER.md` and as ADRs.

### Phase 2 - Data layer
Docs extraction, normalized registry, version pin, drift guard, synthetic fixtures.
**Acceptance:** registry built from the live install; a synthetic-fixture test suite runs
green on a machine with no game installed; the drift guard goes red when the pin is
manually corrupted and green when re-extracted.

### Phase 3 - Solver core
Pillar 1 exact ratio solve, then pillar 2 behind the optimizer interface.
**Acceptance:** hand-verified ratios for a set of known chains including one with a
byproduct loop; zero floating-point arithmetic anywhere in the solve path (assert it);
optimizer swappable by config with identical results on a degenerate case.

### Phase 4 - Save reader
Header, chunks, usmap, objects, world model. Unknown classes skipped and logged.
**Acceptance:** the operator's real world parses; a corrupted and a truncated save both
produce a clean error rather than a crash; parsing is read-only and provably never opens
the save directory for write.

### Phase 5 - Advisor and audit
Trace engine first, then rules, then cards, then the ledger, then pillars 3 and 4.
**Acceptance:** every rule has a synthetic-fixture test; the precondition invariant holds
under a property test; a card's id is stable across a save reload; tier 3 is generated
from the trace and cannot be authored by hand.

### Phase 6 - Surfaces
Dashboard on 8920, then the Electron companion.
**Acceptance:** the 5-phase visual audit from `CONVENTIONS.md` section 13.2 passes before
the page is committed; the companion handles the self-signed certificate without
disabling validation.

### Phase 7 - Public flip gate
The tier-3 checklist from `CONVENTIONS.md` section 17.
**Acceptance:** all seven items pass, including the full-history secret and PII scan and
the clean-checkout probe.

---

## 11. Decision log - settled, do not re-litigate

Each of these was decided deliberately. Recorded here with the fence, not just the
conclusion, so the argument is not rebuilt from scratch.

- **Name is Clockspeed.** Root is `E:\Clockspeed` (ADR 0026). Not up for renaming.
- **Repo is private first, public later.** Hygiene is enforced from the first commit
  anyway (section 17 of `CONVENTIONS.md`). Do not defer the hygiene on the grounds that
  it is private.
- **Python core.** Not a rewrite candidate. Node exists solely for the Electron shell.
- **Advisor is fully deterministic and local. Zero language-model or API dependency in
  the advice path.** Do not propose an LLM-backed explainer, summarizer or ranker for
  advice. The tier-3 derivation is generated from the rule trace, which is exactly why no
  model is needed.
- **Three explain tiers, not two and not four.** Headline, one-line reason, full
  derivation.
- **Persistence is per-world ledger PLUS global per-rule mute.** Both layers, not one.
- **All four advice domains ship in v1.** D1 node siting, D2 onsite-vs-transport and
  method, D3 milestone gap against any target, D4 power and fuel.
- **Milestone target is a free selector**, not a fixed pointer at "next".
- **Companion window in v1; in-game overlay is a later flagged mode of the same shell**,
  default off, degrading to the companion on bind failure.
- **Mods: architecture now, content later** (section 9). Do not open mod content work
  before phase 6 completes.
- **Dedicated Server API is out of scope for v1.** The docs are on disk and free to read,
  but single-player saves are the world-state source. Revisit only if the operator starts
  running a dedicated server.
- **No external optimizer dependency in phase 3.** Interface first, dependency later and
  gated.
- **No community-compiled datasets.** Section 8.3.
- **The reference world is the pinned development world** (section 2.3). Vanilla, no
  creative, no modifiers, onboarding active. Snapshot it into a gitignored corpus as it
  grows; do not switch reference worlds without recording why.
- **The advice ledger is keyed by the save header's world token**, not by filename, not by
  world name. Measured, section 2.4.
- **Never write to the game install or a save file.** Not a preference. An invariant.

---

## 12. Non-negotiables

1. Never write to the game install directory or the save directory.
2. Never commit game data, save files, or anything extracted from the install.
3. Never hardcode the account id, the world name, the Windows user, or a home path.
4. 7-bit ASCII in all authored content. No em-dashes, en-dashes, or smart quotes.
5. Atomic writes for every file another process may read.
6. Exact rational arithmetic in the solve path. Assert the absence of floats.
7. Unknown game content is flagged and skipped, never fatal, never silently wrong.
8. Every advice card's tier-3 derivation is generated from the trace, never hand-written.
9. TDD: the failing test comes first, and it must fail for the right reason.
10. The main session stays responsive - heavy work goes to subagents and worktrees.

---

## 13. The opening move for session 1

Do these in order. Do not skip ahead to building.

1. Read `CONVENTIONS.md` in this folder, end to end. It is the operating doctrine and it
   is not optional context.
2. Re-probe the section 2 table. It was measured on 2026-08-13; confirm the game build
   string and the port availability still hold, and report any drift.
3. Set up the section 5 shape from `CONVENTIONS.md`: orchestrated, multi-agent,
   self-adjudicating, self-adversarial. Decompose phase 0 into disjoint slices before
   writing anything.
4. Execute phase 0. Prove the hook gate end to end - stage a violation, attempt a real
   commit, assert HEAD is unchanged. A hook that exists but does not fire is worse than
   no hook, because it is trusted.
5. Execute phase 1. **S8, S4 and S6 first**, in that order. Report each binary result
   explicitly and record the S4, S6 and S8 decisions as ADRs. Do not re-derive the save
   header - section 2.4 measured it.
6. Do not begin phase 2 until phase 1 is reported and the results are written down.
7. End with the `/done` ritual and print the full next-session continuation prompt.

**If a spike result contradicts something in this document, the spike wins.** Update this
file, record what changed and why in the ledger, and say so plainly in the session report.
This document is a specification written from probed ground truth plus stated assumptions.
The assumptions are labelled. Ground truth beats all of it.
