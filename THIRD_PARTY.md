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

**No third-party source is vendored in this project. Zero files in this repository were
copied, adapted or derived from an external codebase.**

That is the current fact, not an aspiration, and it is the state the register starts in.
It stops being true the moment anything is lifted, and the entry below must be written
BEFORE the lift, not after.

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

One row per item considered. Rows are never deleted - a rejected item stays so the
rejection is not re-litigated, and `CONVENTIONS.md` section 15.1 warns that a decline
reason goes stale before the count does, so re-read the row before citing it.

| Item | Why it was considered | License read (LICENSE / manifest) | Copyright line names a holder | Verdict | Date | Also recorded in |
|---|---|---|---|---|---|---|
| (none vendored) | - | - | - | - | - | - |
| **Asset-parsing library for resource-node extraction** (`BOOTSTRAP.md` section 8.3, the S4 fallback) | If the save file does not carry resource-node actors with transforms, node coordinates must come from the shipped game assets, and that path typically wants an external asset-parsing library | NOT YET READ | NOT YET CHECKED | **PENDING - gate not run. Do not take this dependency until this row is completed.** | - | `docs/GATED.md` |

**On that second row specifically.** `BOOTSTRAP.md` section 8.3 makes the sequencing
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
