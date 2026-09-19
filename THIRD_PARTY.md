# Third-party code register

**Owner file for: every piece of third-party source considered for or used by this
project, and the license verdict recorded for each.** This is the register the license
gate in `CONVENTIONS.md` section 14 writes into. It exists from the first commit
(`CONVENTIONS.md` section 17) because retrofitting provenance later means reconstructing
it from memory, and memory is not evidence.

Rules live in `CONVENTIONS.md` section 14. This file records verdicts. If the two ever
disagree, `CONVENTIONS.md` wins and this file is wrong.

---

## Current state

**Exactly one file in this repository is vendored: `docs/CHANNEL.md`.** It is a
byte-identical, unmodified copy of the cross-repo channel conventions document from the
`Remus3/Amberstone` repository, taken under Apache-2.0 with sole holder `Moonbeam`. The
vendored-files table below owns that fact and carries the attribution Apache-2.0 section 4
asks a redistributor to retain - it has to live in a row, because the copy is byte-pinned
by `tests/test_channel_doc.py` and may not be edited to carry a notice of its own.

**Nothing else in this tree was copied from an external codebase, and one adaptation that
lifted no text is recorded rather than left silent** - the doctrine behind
`docs/hud_doctrine.md`. Both are rows below.

Two things that are NOT vendorings, stated because both get mistaken for one:

- **A runtime or development dependency is not a vendoring and gains no row here.** ruff,
  pytest, mypy, pytest-xdist and PyYAML are named in `pyproject.toml` and no line of their
  source is in this tree. This register is for LIFTED code.
- **Electron is a dependency, not a lift.** `shell/` is authored against the documented
  API rather than seeded from a quickstart template, and its package tree is gitignored,
  so no Electron-owned text is tracked here. The three-scope licence verdict lives in
  `docs/adr/0013-electron-licence-gate.md`.

An entry is written BEFORE the lift, not after. The one row below whose gate ran after its
lift says so in the row, because a late gate that reads like a timely one teaches the
wrong lesson to the next person who reads the register.

There is also no third-party runtime dependency in the advice path. The optimizer in
pillar 2 ships dependency-free behind a pluggable interface; an external linear or
integer programming library is a later decision and is gated on this file
(`BOOTSTRAP.md` section 4, pillar 2, and the section 11 decision log).

---

## The gate: what to do before lifting anything external

Run every step. Record the verdict in the register below before the code is used, not
after it is working. A gate run after the fact is not a gate, it is a rationalization.

1. **Read the LICENSE file.** The actual file, in the actual repository, at the actual
   revision you intend to take code from.
2. **Read the package manifest as well** - `package.json`, `pyproject.toml`, `setup.py`,
   `Cargo.toml`, whatever the ecosystem uses. **A repo can contradict itself**: an MIT
   LICENSE file alongside a manifest declaring `UNLICENSED` and `private: true`, or GPL-3
   in one and ISC in the other. One source alone gives the wrong answer. Read both, and
   record both.
3. **Read the copyright LINE, not just the SPDX name.** A LICENSE file can name NOBODY.
   An unrendered MIT template reading `Copyright (c) {{ year }} {{ organization }}` is a
   grant with no grantor, and both files "agree on MIT" while an SPDX grep passes clean.
   If the copyright line names no one, there is no grant. Stop.
4. **Check for multiple copyright holders.** A repo that credits prior authors, carries a
   `NOTICE`, or has an `AUTHORS` file has more than one holder, and its current maintainer
   cannot unilaterally relicense it. The person who cleared it may not own it.
5. **Check the warranty clause is intact.** A truncated license - warranty or liability
   paragraph missing - is not the license it claims to be. Diff it against the canonical
   text of that license.
6. **Record the verdict here** with the date, the exact revision or version examined, and
   both readings from steps 1 and 2. Then use the code. Not before.

---

## Standing rules

These do not get re-decided per case. They are the answer.

- **GPL and any copyleft license are DO-NOT-VENDOR, regardless of verbal clearance.**
  Vendoring copyleft relicenses this project. There is no version of this that is fine
  because someone said it was fine.
- **Source-available is not open source.** BUSL and its relatives may carry an
  additional-use grant that permits running the software internally. That is not
  permission to vendor it. Do not vendor it.
- **Absence of a LICENSE file is not permission.** It is the opposite: no grant was made,
  so the default applies and the default is all rights reserved.
- **Verbal clearance is not written clearance.** A maintainer's message, an issue comment,
  a chat reply - none of these is a license. If it is not in the repository's license
  terms, it did not happen.
- **The always-legal path is re-implementation.** Techniques, protocol facts and file
  formats are not copyrightable; source is. Reading how a thing works and writing this
  project's own implementation from observed behavior is always available and is the
  default answer when a gate comes back red.

---

## Register

One row per item. Rows are never deleted - a rejected item stays so the rejection is not
re-litigated, and `CONVENTIONS.md` section 15.1 warns that a decline reason goes stale
before the count does, so re-read the row before citing it.

The register is in two tables because the two questions have different answers. The first
names FILES that sit in this tree and were not authored here, so every row carries a path
and a live redistribution obligation. The second names items CONSIDERED, which name no
file in this tree at all. `tests/test_third_party_register.py` grades the first table in
both directions: a file this tree byte-pins as vendored and does not list here is red, and
so is a row naming a file the tree no longer tracks.

### Vendored files

| File | Upstream | License read (LICENSE / manifest) | Copyright line names a holder | Verdict | Gate run | Also recorded in |
|---|---|---|---|---|---|---|
| `docs/CHANNEL.md` | the cross-repo channel conventions document, taken byte-identical from the `Remus3/Amberstone` repository, whose LICENSE scope block puts authored Markdown inside the grant and carves out only its data tree | **Apache-2.0.** LICENSE, the README licence paragraph and NOTICE agree, and no manifest contradicts them; 219 lines with the warranty clause intact, and no source-available reservation anywhere in them | Yes - `Moonbeam`, sole holder, named in both LICENSE and NOTICE, and rendered rather than left as a template | **CLEARED for vendoring.** Permissive and one-way compatible with this tree's outbound licence. The copy is unmodified, so there are no changes to state. This row IS the retained attribution, because the bytes are pinned by `tests/test_channel_doc.py` and a notice may not be added to them | 2026-09-16, AFTER the lift rather than before it | `docs/LEDGER.md` under CS-1095; `CLAUDE.md` section 4 |

**On that row specifically, and it is the uncomfortable half.** The gate ran five days
late and only because a sibling project refused the same file at its own gate. An operator
instruction moves the DECISION, not the GATE. The verdict stands on the source
repository's own LICENSE, README and NOTICE read trap by trap rather than on the sending
tree's summary of them, and the named holder is also this repository's own commit
identity - stated here rather than left to be noticed, because a reader who found that out
later would be right to discount a verdict that had hidden it.

### Items considered

| Item | Why it was considered | License read (LICENSE / manifest) | Copyright line names a holder | Verdict | Date | Also recorded in |
|---|---|---|---|---|---|---|
| **Asset-parsing library for resource-node extraction** (`BOOTSTRAP.md` section 8.3, the S4 fallback) | If the save file does not carry resource-node actors with transforms, node coordinates must come from the shipped game assets, and that path typically wants an external asset-parsing library | NOT YET READ | NOT YET CHECKED | **PENDING - gate not run. Do not take this dependency until this row is completed.** | - | `docs/GATED.md` |
| **The source doctrine behind `docs/hud_doctrine.md`** - a UI/UX doctrine the operator supplied from a different project on this machine | The companion and the overlay needed an operating law, and one already existed for a companion-plus-overlay pair | NOT READ, and there is nothing to read: the source is not in this tree and names no repository | NOT CHECKED, same reason | **NOT A VENDORING - adapted, not lifted.** `docs/hud_doctrine.md`'s own Provenance section records what transfers, what does not, and that this repository's settled decisions win where the two disagree, which is the re-implementation path the standing rules above call always-legal. Recorded so the adaptation is not mistaken for authored-here work. UNVERIFIED AND STATED AS SUCH: the claim that no text was lifted rests on that section, since the source is absent from this tree and was never diffed against it | 2026-09-05 | `docs/hud_doctrine.md`, `BACKLOG.md` |

**On the asset-parsing row specifically.** `BOOTSTRAP.md` section 8.3 makes the sequencing
explicit: the library goes through this gate FIRST, and the result is stated explicitly.
Concretely that means:

- The gate runs **before** any evaluation spike that imports the library, not after a
  prototype already works. A working prototype creates pressure to pass the gate.
- The verdict is recorded **here and in `docs/GATED.md`**, in both places, because this
  file owns the license verdict and `docs/GATED.md` owns the fact that the work is blocked
  on an external condition.
- Spike S8 runs before any of this. If node placement or purity turns out to be
  seed-dependent, the static-asset path is invalid outright and no library is needed
  because the save becomes the only correct source. Do not run a license gate on a
  dependency the spike may delete.
- **Community-compiled node datasets are already refused** by the section 11 decision log
  and are not a candidate for this gate. The refusal is about provenance risk, and a
  license gate cannot repair unknown provenance.

---

## Game data, save files and extracted assets

This is a separate question from source licensing and it has its own settled answer.

**Game data files, save files and anything extracted from the game install are owned by
their publisher. They are read from the local install at runtime, they are gitignored, and
they are never committed.** Not as a sample, not as a fixture, not as an attachment on an
issue, not "temporarily".

What that means in practice:

- **Tracked:** extraction code, normalization code, the save reader, and a small content
  hash plus build-string pin used by the drift guard.
- **Tracked:** small, hand-authored synthetic fixtures. They are written by this project,
  they contain no publisher content, and they are what lets the test suite run on a machine
  with no game installed.
- **Never tracked:** the locale documentation dumps, the property mapping file, packaged
  content, the shipped headers archive, and any slice or excerpt of any of them.
- **Never tracked:** save files, in any form. A save is additionally a personal-data-
  bearing artifact - its header carries a platform account identifier and the player's
  display name in plaintext - so it fails on privacy grounds as well as on ownership
  grounds. See `BOOTSTRAP.md` section 2.2.

`.gitignore` enforces all of the above from before the first commit, and CI tier 3 checks
it again over the full history at the public-flip gate (`CONVENTIONS.md` section 17,
item 4). Neither check replaces the rule; both exist because history is what leaks.
