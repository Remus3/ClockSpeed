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

**The files in this repository that were not authored here are exactly the rows of the
vendored-files table below**, and that table - not this sentence - is the owner of which
files those are. Every vendored row is Apache-2.0, and each is a byte-identical, unmodified copy
except `ops/loop/winmutex.py`, a DECLARED FORK whose own header states what was changed.
Each row carries the attribution Apache-2.0 section 4 asks a redistributor to retain, and
it has to live in a row, because each copy is byte-pinned by a module in this tree's suite
and may not be edited to carry a notice of its own. The fleet kit under `ops/fleet_kit/`
also ships its own LICENSE and NOTICE, which are rows themselves, and its common block is
embedded unmodified in `CLAUDE.md` - one Apache-2.0 block inside an otherwise MIT file.

**Nothing else in this tree was copied from an external codebase, and one adaptation that
lifted no text is recorded rather than left silent** - the doctrine behind
`docs/hud_doctrine.md`. All of them are rows below.

A sentence like the one this paragraph replaced - it named a single vendored file, and was
true the day it was written - is the shape this file fails in. `ops/loop/slots.py` landed
under CS-946 and made it false, and nothing went red, because the arm that reads this
document graded a HAND-MAINTAINED roster of pin modules rather than the tree. That roster
is now DERIVED: every test module here that spells a sha256 is asked which file in the
tree hashes to it, so a lift reaches the graded population the moment its pin does. The
residual - a lift with no pin and no row - is CS-1165 and is still open.

Two things that are NOT vendorings, stated because both get mistaken for one:

- **A runtime or development dependency is not a vendoring and gains no row in the
  Register.** ruff, pytest, mypy, pytest-xdist and PyYAML are named in `pyproject.toml`
  and no line of their source is in this tree; the Register is for LIFTED code. Each
  dependency's licence verdict is a row of the separate Dependency licence verdicts
  section below instead, which grades what may be INSTALLED and changes nothing the
  vendored-set claims above say.
- **Electron is a dependency, not a lift.** `shell/` is authored against the documented
  API rather than seeded from a quickstart template, and its package tree is gitignored,
  so no Electron-owned text is tracked here. The three-scope licence verdict lives in
  `docs/adr/0013-electron-licence-gate.md`, and Electron's dependency row cites it rather
  than re-deriving it.

An entry is written BEFORE the lift, not after. Every row below whose gate ran after its
lift says so in the row, because a late gate that reads like a timely one teaches the
wrong lesson to the next person who reads the register. The first three vendored rows say
it, which is a fact about this project's habit rather than about those three files. The
fleet kit's rows are the first whose gate preceded the lift: its version 3 was HELD at the
gate because it carried no licence, and version 4 was read and CLEARED before it landed.
Version 9 superseded version 4 directly under CS-1272 and added eleven files; it was read
and CLEARED in the commit that vendors it, and each of its rows says so. Version 10
superseded version 9 under CS-1282 and added one file, `ops/fleet_kit/fleet_subagent_first.py`;
it too was read and CLEARED in the commit that vendors it. Version 11 superseded version 10
under CS-1287 and added no file; it changed six files' code, no licence term, LICENSE or
NOTICE, and was read and CLEARED in the commit that vendors it. Version 13 superseded
version 11 under CS-1290, carrying version 12 whole, and added six files - fleet_claims.py,
fleet_gitlock.py, fleet_identity.py, fleet_rewrite.py, fleet_suite_gate.py and
fleet_test_guard.py; NOTICE changed only its scope list, LICENSE not at all, and it was read
and CLEARED in the commit that vendors it. Version 14 superseded version 13
under CS-1299 and added no file; it changed code and tokens.json, no licence term, LICENSE
or NOTICE, and was read and CLEARED in the commit that vendors it. Version 15 superseded
version 14 under CS-1303 and added no file; it changed five files' code, no licence term,
LICENSE or NOTICE, and was read and CLEARED in the commit that vendors it. Version 17
superseded version 15 under CS-1310 and added no file - version 16 was never vendored
here, and version 17 carries its whole FIX; it changed three files' code, no licence
term, LICENSE or NOTICE, and was read and CLEARED in the commit that vendors it. Version 20
patch 1 superseded version 17 under CS-1330 and added one file,
`ops/fleet_kit/fleet_board.py` - versions 18, 19 and 20 were never vendored here, and
version 20 patch 1 carries every change they made; it changed twelve files' code,
tokens.json, tokens.css and the FLEET-COMMON block (items 10, 13 and 14 and a new item
18), NOTICE only in its scope list, no licence term and not LICENSE, and was read and
CLEARED in the commit that vendors it.

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
| `ops/loop/slots.py` | the machine-wide slot governor of the headless loop, taken byte-identical from the `Remus3/Legion-Wallpaper` repository, which committed it EARLIEST of the trees on this machine that carry it - the others hold the same bytes at the same relative path, and which of them copied from which is not established here | **Apache-2.0.** The LICENSE is the complete text - all nine sections, `END OF TERMS AND CONDITIONS`, and the Disclaimer of Warranty and Limitation of Liability clauses present and unedited - and the README licence paragraph agrees with it. There is NO package manifest anywhere in that repository, so trap 1 has nothing to contradict the LICENSE with; the README's only carve-out is the image corpus, and loop source is not that | Yes - `Moonbeam`, sole holder, RENDERED in the LICENSE appendix rather than left as a template. No NOTICE, AUTHORS or CONTRIBUTORS file exists there, so no second holder can be inferred | **CLEARED for vendoring.** Permissive and one-way compatible with this tree's outbound licence. The copy is unmodified, so there are no changes to state. This row IS the retained attribution: the bytes are pinned by `tests/ops/test_shared_slots.py` and are byte-identical-by-contract with the other carrier trees, so a notice may not be added to them. STATED RATHER THAN LEFT TO BE NOTICED, twice over: the upstream repository had no LICENSE at all on the day that file was first committed there - it was added five days later - so the grant read is the one covering the repository at the revision these bytes were TAKEN from, which is its current tip, whose tracked copy hashes equal to this one; and the named holder is also this repository's own commit identity | 2026-09-20, AFTER the lift rather than before it, and only because a slice that could not edit this file reported the omission | `docs/item_notes.md` under CS-946 and CS-1165 |
| `ops/loop/winmutex.py` | the named-mutex wrapper of the same headless loop in the `Remus3/Legion-Wallpaper` repository; this tree's copy is a DECLARED FORK rather than a byte-identical one, and the module's own header is the fork record | **Apache-2.0**, the same LICENSE and README paragraph read for the row above, in the same repository and with no manifest anywhere in it to contradict them | Yes - `Moonbeam`, sole holder, rendered rather than templated, with no NOTICE or AUTHORS file to imply another | **CLEARED, as a MODIFIED lift.** Apache-2.0 section 4 asks a redistributor to carry prominent notices stating that files were changed: the module header does exactly that, naming the two upstream resource constants deleted and the docstring retargeted, and `tests/test_lane_lock.py` pins this tree's own forked bytes. UNVERIFIED AND STATED AS SUCH: the upstream REVISION these bytes were taken from is not identifiable, because the upstream digest the fork header cites matched no file on this machine at the CS-1160 census of 2026-09-20 - the header now keeps that digest as historical and declares the upstream GONE with that date, and `tests/test_lane_lock.py` grades the claim against this tree's own files and history (CS-1160) - so the gate was run against the repository and the path, not against the revision. That is a weaker evidence base than the row above and is recorded as one | 2026-09-20, long AFTER the fork landed, and for the same reason as the row above | `docs/adr/0017-the-lane-forks-the-shared-loop-modules.md` (ADR-0017); `docs/item_notes.md` under CS-1160 and CS-1165 |
| `ops/fleet_kit/fleet_headless.py` | MAIN's fleet kit, version 20 patch 1 - the delivery bundle beside MAIN's 2026-10-19 00:01 ORDER note, taken byte-identical from the provenance-verified copy of that bundle, and every one of its twenty-four files hashing equal to the digest that note names and to the same file at the kit commit that note names. First vendored at version 4 under CS-1231 from the bundle beside MAIN's 2026-10-03 12:04 ORDER note; version 9 superseded it directly under CS-1272, version 10 superseded version 9 under CS-1282, version 11 superseded version 10 under CS-1287, version 13 superseded version 11 under CS-1290, as the version 13 note orders - version 12 was never vendored here, and version 13 carries its whole ORDER - version 14 superseded version 13 under CS-1299, version 15 superseded version 14 under CS-1303, and version 17 superseded version 15 under CS-1310, as the version 17 FIX note orders - version 16 was never vendored here, and version 17 carries its whole FIX - each adding no file; version 20 patch 1 superseded version 17 under CS-1330, as the version 20 patch 1 ORDER note orders - versions 18, 19 and 20 were never vendored here, and version 20 patch 1 carries every change they made - adding one file, `ops/fleet_kit/fleet_board.py`. MAIN is the supervisor tree on this machine; it has no remote, and its path lives only in gitignored local configuration | **Apache-2.0.** The kit LICENSE is the complete text, identical to the canonical file but for one leading blank line - all nine sections, `END OF TERMS AND CONDITIONS`, and the warranty and liability clauses intact, the appendix the unrendered how-to-apply template - and its bytes are unchanged from version 4. NOTICE and this file's `SPDX-License-Identifier: Apache-2.0` line agree, and none of the version 9, 10, 11, 12, 13, 14, 15, 18, 19, 20 or 20 patch 1 ORDER notes, nor the version 16 or 17 FIX notes, changes a licence term. MANIFEST.json carries no licence field, so trap 1 has nothing to contradict it; MAIN's README was read at version 4 and is not re-read here | Yes, BY ROLE rather than by name - `the operator - the kit's owner and sole copyright holder`, rendered in NOTICE and on this file's second line. Sole holder; no AUTHORS file, no adapted upstream named. Intramural: the grantor is this fleet's own operator. UNVERIFIED AND STATED AS SUCH: that this is the person behind the `Moonbeam` holder of the rows above - the kit does not say so | **CLEARED for vendoring.** Permissive and one-way compatible with this tree's outbound licence. Unmodified, so there are no changes to state; the SPDX and copyright lines are retained by byte identity, and LICENSE and NOTICE ship beside it. This row is the retained attribution, because the bytes are pinned by `tests/test_fleet_kit.py` and by the kit's own conformance | 2026-10-03, BEFORE the version 4 lift - the first row here whose gate preceded its file. v3 was HELD the same day because MAIN's kit then carried no licence. Re-read for version 9 on 2026-10-08, in the CS-1272 commit that vendors it, and for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1231, CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330; `docs/item_notes/phase7.md` under CS-1231 and CS-1272 |
| `ops/fleet_kit/FLEET-COMMON.md` | the same upstream and bundle as the row above. ALSO EMBEDDED byte-for-byte between the FLEET-COMMON markers in `CLAUDE.md`, and NOTICE's scope names that embedded block as inside the grant | **Apache-2.0**, the same LICENSE and NOTICE read for the row above. The file carries no header by design - it is byte-pinned and NOTICE covers it | Yes, by role - `the operator`, with the same unverified-identity note as the row above | **CLEARED for vendoring AND for the `CLAUDE.md` embed.** Unmodified in both places, so no changes to state. `CLAUDE.md` thereby carries one Apache-2.0 block inside an MIT file; the NOTICE beside this file is the attribution section 4(d) asks for. Pinned by `tests/test_fleet_kit.py` | 2026-10-03, BEFORE the lift; re-read for version 9 on 2026-10-08, in the CS-1272 commit that vendors it, and for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1231, CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330; `docs/item_notes/phase7.md` under CS-1272; `CLAUDE.md`, the FLEET-COMMON markers |
| `ops/fleet_kit/MANIFEST.json` | the same upstream and bundle | **Apache-2.0** by NOTICE's scope, which names this file; it carries no licence field to contradict the LICENSE | Yes, by role - `the operator` | **CLEARED for vendoring.** Unmodified; no changes to state. Pinned by `tests/test_fleet_kit.py`, both as a file and through the twenty-three digests it carries | 2026-10-03, BEFORE the lift; re-read for version 9 on 2026-10-08, in the CS-1272 commit that vendors it, and for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1231, CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330; `docs/item_notes/phase7.md` under CS-1272 |
| `ops/fleet_kit/LICENSE` | the same upstream and bundle | **Apache-2.0** - this IS the licence text read for the rows above | The appendix is the unrendered template, the licence's own boilerplate; the rendered holder line is NOTICE's - `the operator` | **CLEARED, and RETAINED as Apache-2.0 section 4(a) requires.** Never edited; its version 10 bytes are identical to its version 9 and version 4 bytes. Pinned by `tests/test_fleet_kit.py` | 2026-10-03, BEFORE the lift; re-read for version 9 on 2026-10-08, in the CS-1272 commit that vendors it, and for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1231, CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330; `docs/item_notes/phase7.md` under CS-1272 |
| `ops/fleet_kit/NOTICE` | the same upstream and bundle | **Apache-2.0**, scoping the grant to every file MANIFEST.json names and to the embedded block. At versions 19 and 20 its scope paragraph LISTS all twenty-three kit files MANIFEST.json names, fleet_board.py included; at versions 13, 14, 15 and 17 it listed all twenty-two then named, the six files versions 12 and 13 added included; at version 10 it listed all sixteen then named, fleet_subagent_first.py included, and adds `any file a later kit version adds to the manifest`, under the governing clause `every file named in this kit's MANIFEST.json`. At version 9 that list named only eight - FLEET-COMMON.md, fleet_headless.py, fleet_watch.py, fleet_secrets.py, tokens.json, tokens.css, LICENSE and NOTICE - and the clause alone reached the other seven; the rows below say so file by file | Yes, by role - `the operator - the kit's owner and sole copyright holder` | **CLEARED, and RETAINED as Apache-2.0 section 4(d) requires.** Its CHANGES clause permits a tree-side notice under another name; this tree uses this register instead. Pinned by `tests/test_fleet_kit.py` | 2026-10-03, BEFORE the lift; re-read for version 9 on 2026-10-08, in the CS-1272 commit that vendors it, when only its scope list had changed, and for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, when again only its scope list had changed, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, when on all three its bytes had not changed, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it, when again only its scope list had changed - it now names fleet_board.py | `docs/LEDGER.md` under CS-1231, CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330; `docs/item_notes/phase7.md` under CS-1272 |
| `ops/fleet_kit/cli_display.json` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 9 - the fleet's CLI display keys, which MAIN applies to the account settings | **Apache-2.0** through NOTICE's governing clause, `every file named in this kit's MANIFEST.json` - MANIFEST.json names it, and at version 10 the scope paragraph lists it by name as well, where version 9's list of eight did NOT. It carries no SPDX header, since JSON has no comment syntax, so the NOTICE and LICENSE beside it are its only grant | Yes, by role - `the operator`, NOTICE's holder line; the file itself names no holder | **CLEARED for vendoring.** Unmodified; no changes to state. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_checklist.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_done.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_inbox.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_lanes.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_secrets.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose scope paragraph lists it by name | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_statusline.js` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_subagent_first.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 10 - the kit's SUBAGENT-FIRST PreToolUse hook, wired in `.claude/settings.json` under the CS-1282 frozen-file grant | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 10 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1282 commit that vendors it; re-read for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_subagent_status.js` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE. At version 10 NOTICE's scope paragraph lists it by name, under that paragraph's governing clause `every file named in this kit's MANIFEST.json`; at version 9 it did NOT, and the file was inside the grant through that clause alone, because MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_watch.py` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose scope paragraph lists it by name | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/tokens.css` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 - the dashboard tokens MAIN GENERATES from `ops/fleet_kit/tokens.json` | **Apache-2.0** by NOTICE's scope paragraph, which lists it by name. It carries no SPDX header - its only comment is MAIN's generated-do-not-edit line - so the NOTICE and LICENSE beside it are its only grant | Yes, by role - `the operator`, NOTICE's holder line; the file itself names no holder | **CLEARED for vendoring.** Unmodified; no changes to state. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/tokens.json` | the same upstream and version 20 patch 1 bundle; new to this tree at version 9 - the dashboard design tokens, the source `ops/fleet_kit/tokens.css` is generated from | **Apache-2.0** by NOTICE's scope paragraph, which lists it by name. It carries no SPDX header, since JSON has no comment syntax, so the NOTICE and LICENSE beside it are its only grant | Yes, by role - `the operator`, NOTICE's holder line; the file itself names no holder | **CLEARED for vendoring.** Unmodified; no changes to state. Pinned by `tests/test_fleet_kit.py` | 2026-10-08, in the CS-1272 commit that vendors it; re-read for version 10 the same day, in the CS-1282 commit that vendors it, and for version 11 the same day, in the CS-1287 commit that vendors it, and for version 13 on 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/item_notes/phase7.md` under CS-1272; `docs/LEDGER.md` under CS-1282, CS-1287, CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_claims.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 12) - the RACE GUARDS file-claim registry and its PreToolUse and SubagentStop hooks, wired in `.claude/settings.json` under the CS-1290 frozen-file grant | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_gitlock.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 12) - the RACE GUARDS per-tree git lock every commit and push runs through | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_identity.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 13) - the NO AI OR BOT ATTRIBUTION commit-msg and pre-push checks, wired in `.githooks/` under the CS-1290 frozen-file grant | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_rewrite.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 13) - the operator-gated history rewrite helper; nothing here runs it | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_suite_gate.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 12) - the RACE GUARDS machine-wide whole-suite gate, wired in `.githooks/pre-push` and the queue loop's local suite | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_test_guard.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 13 (first shipped at version 12) - the RACE GUARDS test-isolation guard, installed by `tests/conftest.py` | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 13 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-09, in the CS-1290 commit that vendors it, and for version 14 the same day, in the CS-1299 commit that vendors it, and for version 15 the same day, in the CS-1303 commit that vendors it, and for version 17 on 2026-10-11, in the CS-1310 commit that vendors it, and for version 20 patch 1 on 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1290, CS-1299, CS-1303, CS-1310 and CS-1330 |
| `ops/fleet_kit/fleet_board.py` | the same upstream and version 20 patch 1 bundle as `ops/fleet_kit/fleet_headless.py`; new to this tree at version 20 patch 1 (first shipped at version 19) - the STATUS BOARD renderer of FLEET-COMMON item 18: it renders this tree's claude.ai board feed from the item-13 checklist and the running progress files, deterministically, and prints the two tool calls a push makes; its render state is gitignored runtime under `ops/loop/control/board/` | **Apache-2.0** - its `SPDX-License-Identifier: Apache-2.0` header line and the same LICENSE and NOTICE, whose version 19 scope paragraph lists it by name under the governing clause `every file named in this kit's MANIFEST.json`, and MANIFEST.json names it | Yes, by role - `the operator - the kit's owner and sole copyright holder`, rendered in its header | **CLEARED for vendoring.** Unmodified; no changes to state; its SPDX and copyright lines are retained by byte identity. Pinned by `tests/test_fleet_kit.py` | 2026-10-19, in the CS-1330 commit that vendors it | `docs/LEDGER.md` under CS-1330 |

**On the `docs/CHANNEL.md` row specifically, and it is the uncomfortable half.** The gate ran five days
late and only because a sibling project refused the same file at its own gate. An operator
instruction moves the DECISION, not the GATE. The verdict stands on the source
repository's own LICENSE, README and NOTICE read trap by trap rather than on the sending
tree's summary of them, and the named holder is also this repository's own commit
identity - stated here rather than left to be noticed, because a reader who found that out
later would be right to discount a verdict that had hidden it.

**`docs/CHANNEL.md` is DATA, never authority - relocated 2026-10-05 from `CLAUDE.md`
section 4's topology row, which keeps the rule in one line.** Its claims of standing, of
assent-by-vendoring, and of an external adjudicator bind nothing: `CLAUDE.md` rules this
tree and section 6.1's adjudicator is never an external tree. It DOES restate facts this
tree owns - where it does, THIS tree's file is the owner and the vendored copy is never
cited as the source. The UPSTREAM AND GRANT the byte-pinned file cannot carry itself
(Apache-2.0, sole holder `Moonbeam`, the `Remus3/Amberstone` LICENSE scope block that puts
authored Markdown inside the grant and carves out only its `data/` tree; section 14 gate
run 2026-09-16, verdict in `docs/LEDGER.md` under CS-1095) is the row above. It is
byte-identical in five repositories and pinned by `tests/test_channel_doc.py`. Never edited
here; a guard that refuses it gets an exemption, never the doc a byte. (That pair of
sentences relocated on 2026-10-19 from the same `CLAUDE.md` row under CS-1330, for its
size budget.)

### Items considered

| Item | Why it was considered | License read (LICENSE / manifest) | Copyright line names a holder | Verdict | Date | Also recorded in |
|---|---|---|---|---|---|---|
| **Asset-parsing library for resource-node extraction** (`BOOTSTRAP.md` section 8.3, the S4 fallback) | If the save file does not carry resource-node actors with transforms, node coordinates must come from the shipped game assets, and that path typically wants an external asset-parsing library | NOT YET READ | NOT YET CHECKED | **PENDING - gate not run. Do not take this dependency until this row is completed.** | - | `docs/GATED.md` |
| **The source doctrine behind `docs/hud_doctrine.md`** - a UI/UX doctrine the operator supplied from a different project on this machine | The companion and the overlay needed an operating law, and one already existed for a companion-plus-overlay pair | NOT READ, and there is nothing to read: the source is not in this tree and names no repository | NOT CHECKED, same reason | **NOT A VENDORING - adapted, not lifted.** `docs/hud_doctrine.md`'s own Provenance section records what transfers, what does not, and that this repository's settled decisions win where the two disagree, which is the re-implementation path the standing rules above call always-legal. Recorded so the adaptation is not mistaken for authored-here work. UNVERIFIED AND STATED AS SUCH: the claim that no text was lifted rests on that section, since the source is absent from this tree and was never diffed against it | 2026-09-05 | `docs/hud_doctrine.md`, `BACKLOG.md` |
| **`git-filter-repo` 2.47.0, a run-once TOOL for CS-700 S7a** - not vendored, not a dependency, named in no manifest | S7a rewrites commit identity and strips the agent co-authorship trailer in one history-rewriting pass, and `docs/item_notes/phase7.md` S7a records the script that drives it verbatim. The tool runs once, on a scratch clone, from the operator's own interpreter; no line of it enters this tree | Read from upstream `newren/git-filter-repo` through the forge API AND from the installed dist-info, and the two agree byte-for-byte on the lines read: `COPYING` puts the tool itself under MIT (`COPYING.mit`), optionally also under the licences git.git or libgit2 use, and carves out only the GPL-2.0 test harness, which the installed package does not ship; `COPYING.mit` is the MIT text with its warranty clause intact. Manifest: `License: MIT`, an MIT classifier, and `License-File` naming all three files. The forge's own detector returns `NOASSERTION` for the repository - trap 1 in shape, the MIT-or-git-family choice confusing a detector, not a contradiction | NONE - `COPYING.mit` reads `Copyright (c) 2009, 2018-2019` and names no holder (trap 3); the installed module carries no copyright line either | **CLEARED to RUN as a tool, DO-NOT-VENDOR.** Running a tool distributes nothing, so section 14's lift gate is not engaged by the run; it is recorded here so the run is not mistaken for a lift. A lift of any line is refused outright: the licence names no grantor. It gains no Dependency-licence row, because no manifest names it and `tools/licence_audit.py` derives that set from the manifests | 2026-10-04 | `docs/item_notes/phase7.md` CS-700 S7a, `docs/LEDGER.md` |

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

## Dependency licence verdicts

**Owner of: the `CONVENTIONS.md` section 14 verdict for every runtime and development
dependency, direct and transitive, of `pyproject.toml` and `shell/package.json`**
(CS-1185). A dependency is not a vendoring, so these rows sit OUTSIDE the Register above
and change nothing it claims. The gate is the same five traps, read against the files each
package INSTALLS - its dist-info licence files, or its LICENSE under `node_modules/` - and
against its manifest: the METADATA `License-Expression`, `License` field or classifier on
the Python side, and the `package.json` and lockfile licence field on the node side.

**The set is DERIVED, never held here.** `tools/licence_audit.py::audit` derives it from
the manifests and compares it with these two tables in both directions. `python
tools/licence_audit.py` exits 0 when there is no finding, 1 on any finding and 2 when it
could not run, and prints counts and package names only. THE POLICY, stated once here and
in the tool's docstring:

- **A FINDING (exit 1):** a dependency with no verdict row, on either side - a newly
  installed package without a verdict is exactly the licence risk this exists to catch; a
  row whose verdict does not begin `**CLEARED`, that records neither a copyright line nor
  an explicit `NONE`, that has no date, or that repeats a name; a node row naming no
  pinned package or at a version the lockfile does not pin.
- **A NOTE (printed, exit unaffected):** a Python row the auditing environment does not
  reach, or reaches under a different condition. That is version or platform drift, never
  a licence risk, and failing on it turned the committed suite red on an older allowed
  pytest or mypy with nothing wrong in the tree.
- **Where each half runs.** `tests/test_licence_audit.py` grades the logic over a
  SYNTHETIC tree and environment, so the suite is deterministic; it grades this file only
  where this file is deterministic (complete rows, the node table against the tracked
  lockfile, Electron's ADR citation); and its ONE live arm asserts only that every package
  the running environment derives is recorded here or reported as a finding, so it never
  goes red on drift. The live verdict is the CLI's exit code, run by the merger or CI.

- **Node is machine-independent.** The set is every package `shell/package-lock.json`
  pins, nested ones included, and that file is tracked. The version below must equal the
  lockfile's, so a lockfile bump without a re-read goes red.
- **Python is ENVIRONMENT-DEPENDENT, and that is stated rather than hidden.** There is no
  lockfile (ruling D-Z of the wave-2 plan: none is added for this item), so the closure of
  `[project].dependencies` - empty by decision - plus every extra is walked through the
  installed metadata of the interpreter that RUNS the audit. A different platform, Python
  version, or point inside the dev extra's version ranges can add or drop a transitive
  package. An added one without a row is a finding until this table gains its verdict; a
  dropped one is a note. Versions are the version READ and are not compared, because CI
  resolves its own point in each range. The Reached-when cell is `always` or the PEP 508
  condition derived from the `Requires-Dist` markers on the way in; a row whose condition
  is false in the auditing interpreter - colorama on a Linux runner - is not required
  there, and a condition that differs from the derived one is a note.
- **`[build-system].requires` is NOT in the derived set, and so setuptools has no row.**
  It is installed into pip's isolated build environment and never into the environment the
  audit and the suite run in, so its licence files are not on this machine to read, and a
  row claiming a copyright line nobody read is the failure this section exists to prevent.
  NOT GATED HERE, stated as such.

**What CLEARED means in this section:** the package may be installed and run as this
project's toolchain or shell dependency. Nothing of it is in this tree and nothing is
distributed. It is NOT a vendoring clearance - lifting any line of any package below goes
through the gate above from step 1 and gains a Register row. **DO-NOT-VENDOR** marks the
rows where a lift would be refused outright: copyleft terms, or a licence file naming no
holder.

**Copyright lines are recorded as read, never the licence text.** E-mail addresses and
URLs are omitted where a line carries them. The one non-ASCII holder name is transliterated
and its row declares it. Where the licence file names nobody, the cell says `NONE` and
names where a holder does appear, if anywhere - trap 3.

**Every gate below ran AFTER the dependency was in use.** These packages entered the
toolchain from the first commit onward and CS-1185 is the first gate over any of them
except Electron, whose verdict is ADR 0013's and is consumed here rather than re-derived.

### Python dependencies

| Package | Version read | Reached when | Licence read (files / manifest) | Copyright line | Verdict | Date |
|---|---|---|---|---|---|---|
| `ast-serialize` | 0.5.0 | `always` | MIT in `licenses/LICENSE`, warranty clause intact / `License-Expression: MIT`. Reached through mypy | Copyright (c) 2025-2026 Jukka Lehtosalo and contributors | **CLEARED** as a dependency | 2026-09-25 |
| `colorama` | 0.4.6 | `sys_platform == "win32"` | BSD-3-Clause text in `licenses/LICENSE.txt`, warranty clause intact / no SPDX field, classifier `BSD License` - the two agree on BSD and only the file says which | Copyright (c) 2010 Jonathan Hartley | **CLEARED** as a dependency. Reached through pytest, on Windows only | 2026-09-25 |
| `execnet` | 2.1.2 | `always` | MIT text in `licenses/LICENSE`, warranty clause intact / `License-Expression: MIT` | NONE - the licence file carries no copyright line at all, so it names no grantor (trap 3). A holder appears only in the source: `execnet/gateway_base.py` reads a bare `:copyright: 2004-2015` above an authors list led by Holger Krekel, and METADATA reads `Author: holger krekel and others` | **CLEARED as a dependency ONLY, DO-NOT-VENDOR.** Installed from the publisher's own distribution and run as pytest-xdist's transport, with nothing copied. A lift would need a grant this licence file does not render, so it stops at trap 3 | 2026-09-25 |
| `iniconfig` | 2.3.0 | `always` | MIT, warranty clause intact / `License-Expression: MIT` | Copyright (c) 2010 - 2023 Holger Krekel and others | **CLEARED** as a dependency | 2026-09-25 |
| `librt` | 0.11.0 | `platform_python_implementation != "PyPy"` | MIT for the mypyc runtime, followed in the same file by PSF-2.0 terms for portions derived from CPython / `License-Expression: MIT` alone - trap 1 in shape, the manifest naming one licence where the file carries two, both permissive | Copyright (c) 2025 Mypyc contributors; the PSF portions are the Python Software Foundation's | **CLEARED** as a dependency. Reached through mypy | 2026-09-25 |
| `mypy` | 2.1.0 | `always` | MIT plus PSF-2.0 portions in `licenses/LICENSE`, and typeshed's `licenses/mypy/typeshed/LICENSE`, Apache-2.0 with an MIT part / `License-Expression: MIT` alone - trap 1 in shape, as for librt | Copyright (c) 2012-2023 Jukka Lehtosalo and contributors; Copyright (c) 2015-2023 Dropbox, Inc. Typeshed's Apache appendix is the unrendered how-to-apply template, the licence's own boilerplate rather than a grant line; its MIT part names Jukka Lehtosalo and contributors, 2015 | **CLEARED** as a dependency. Several holders (trap 2), so nobody can offer other terms - which a dependency never needs | 2026-09-25 |
| `mypy-extensions` | 1.1.0 | `always` | MIT, warranty clause intact / `License-Expression: MIT` | Copyright (c) 2016-2017 Jukka Lehtosalo and contributors | **CLEARED** as a dependency | 2026-09-25 |
| `packaging` | 26.1 | `always` | `Apache-2.0 OR BSD-2-Clause`: `licenses/LICENSE` states the dual grant and `LICENSE.APACHE` and `LICENSE.BSD` carry the two texts / `License-Expression` agrees | Copyright (c) Donald Stufft and individual contributors. - from the BSD file; the Apache file's appendix is unrendered boilerplate | **CLEARED** as a dependency. `tools/licence_audit.py` imports it to evaluate markers | 2026-09-25 |
| `pathspec` | 1.1.1 | `always` | MPL-2.0 full text in `licenses/LICENSE` / no SPDX field, classifier `Mozilla Public License 2.0 (MPL 2.0)` | The licence file names no holder, as MPL-2.0 texts do not; `pathspec/_meta.py` reads Copyright (c) 2013-2026 Caleb P. Burns - TRANSLITERATED, the source spells the (c) as the non-ASCII copyright sign | **CLEARED as a dependency ONLY, DO-NOT-VENDOR.** MPL-2.0 is file-level copyleft: running it imposes nothing, while lifting any file of it would carry MPL terms into this tree. Reached through mypy | 2026-09-25 |
| `pluggy` | 1.6.0 | `always` | MIT, warranty clause intact / `License: MIT` and an MIT classifier, no SPDX field | Copyright (c) 2015 holger krekel (rather uses bitbucket/hpk42) | **CLEARED** as a dependency | 2026-09-25 |
| `pygments` | 2.20.0 | `always` | BSD-2-Clause in `licenses/LICENSE`, beside `licenses/AUTHORS` / `License-Expression: BSD-2-Clause` | Copyright (c) 2006-2022 by the respective authors (see AUTHORS file). - the AUTHORS file lists many holders, led by Georg Brandl | **CLEARED** as a dependency. Several holders, trap 2 fires benignly | 2026-09-25 |
| `pytest` | 9.0.3 | `always` | MIT, warranty clause intact / `License-Expression: MIT` | Copyright (c) 2004 Holger Krekel and others | **CLEARED** as a dependency | 2026-09-25 |
| `pytest-xdist` | 3.8.0 | `always` | MIT, warranty clause intact / `License-Expression: MIT` | Copyright (c) 2010 Holger Krekel and contributors. | **CLEARED** as a dependency | 2026-09-25 |
| `pyyaml` | 6.0.3 | `always` | MIT, warranty clause intact / `License: MIT` and an MIT classifier, no SPDX field | Copyright (c) 2017-2021 Ingy dot Net; Copyright (c) 2006-2016 Kirill Simonov - TRANSLITERATED, the file spells the first holder's "dot" with a non-ASCII o-umlaut, written here as a plain o | **CLEARED** as a dependency | 2026-09-25 |
| `ruff` | 0.15.12 | `always` | MIT for ruff itself, followed in the same file by fourteen notices for the externally maintained projects parts of it derive from, each MIT by the name it carries / `License-Expression: MIT` | Copyright (c) 2022 Charles Marsh; the appended notices name further holders, the first Copyright (C) 2012-2018 Steven Myint for autoflake | **CLEARED** as a dependency. A binary wheel, run as a linter, with nothing lifted | 2026-09-25 |
| `typing-extensions` | 4.15.0 | `(python_version < "3.15") or (python_version >= "3.15")` | PSF-2.0 / `License-Expression: PSF-2.0` | Copyright (c) 2001, 2002, ... 2023 Python Software Foundation; All Rights Reserved - the file lists every year from 2001 to 2023 singly | **CLEARED** as a dependency. Reached through mypy, whose two markers together hold on every Python | 2026-09-25 |

### Node dependencies

| Package | Version read | Licence read (files / manifest) | Copyright line | Verdict | Date |
|---|---|---|---|---|---|
| `@electron-internal/extract-zip` | 1.0.5 | NO licence file in the installed package. Its README's License heading, its `package.json` and the lockfile all say BSD-2-Clause | NONE - no licence file ships, so no copyright line exists to read; `package.json` names no author, and its repository field points at the Electron organisation's extract-zip | **CLEARED as a local install ONLY, DO-NOT-VENDOR.** It is an install-time unpacker: `electron/install.js` calls it to unzip the downloaded Electron archive during `npm install`, and nothing of it is tracked here. Absence of a LICENSE file is not permission, so this rests on the publisher's own declaration in the manifest it published, and with no copyright notice to retain, a lift of any of it stops at trap 3. It also ships prebuilt native binaries | 2026-09-25 |
| `@electron/get` | 5.1.0 | MIT, warranty clause intact / MIT in `package.json` and the lockfile | Copyright (c) Contributors to the Electron project | **CLEARED** as a dependency | 2026-09-25 |
| `@types/node` | 24.13.3 | MIT, warranty clause intact / MIT | Copyright (c) Microsoft Corporation. | **CLEARED** as a dependency | 2026-09-25 |
| `debug` | 4.4.3 | MIT, warranty clause intact / MIT | Copyright (c) 2014-2017 TJ Holowaychuk; Copyright (c) 2018-2021 Josh Junon - e-mail address omitted | **CLEARED** as a dependency | 2026-09-25 |
| `electron` | 44.0.0 | MIT, warranty clause intact / MIT in `package.json` and the lockfile - the PUBLISHED manifest, which is the read ADR 0013 records as the one that gives the right answer | Copyright (c) Electron contributors; Copyright (c) 2013-2020 GitHub Inc. | **CLEARED - CONSUMED from `docs/adr/0013-electron-licence-gate.md`, not re-derived.** Scopes (a) a local devDependency and (b) a manifest naming it are CLEARED; (c) distributing a packaged binary is CLEARED WITH OBLIGATIONS, listed in that ADR. This row re-read only the version and the copyright line, and both match the ADR | 2026-09-25 |
| `env-paths` | 3.0.0 | MIT in `license`, warranty clause intact / MIT | Copyright (c) Sindre Sorhus - e-mail address and URL omitted | **CLEARED** as a dependency | 2026-09-25 |
| `graceful-fs` | 4.2.11 | ISC, warranty clause intact / ISC | Copyright (c) 2011-2022 Isaac Z. Schlueter, Ben Noordhuis, and Contributors | **CLEARED** as a dependency | 2026-09-25 |
| `ms` | 2.1.3 | MIT in `license.md`, warranty clause intact / MIT | Copyright (c) 2020 Vercel, Inc. | **CLEARED** as a dependency | 2026-09-25 |
| `progress` | 2.0.3 | MIT, warranty clause intact / MIT | Copyright (c) 2017 TJ Holowaychuk - e-mail address omitted | **CLEARED** as a dependency | 2026-09-25 |
| `semver` | 7.8.5 | ISC, warranty clause intact / ISC | Copyright (c) Isaac Z. Schlueter and Contributors | **CLEARED** as a dependency. `package.json` names GitHub Inc. as author, a second name beside the holder line - trap 2, benign | 2026-09-25 |
| `sumchecker` | 3.0.1 | Apache-2.0 full text, warranty clause intact, appendix left as the unrendered how-to-apply template / Apache-2.0 | The licence file names no holder; the rendered line is the source header of `index.js`: Copyright 2016, 2017, 2019 Mark Lee and contributors | **CLEARED** as a dependency. Apache-2.0 places the notice in the source files, and there it is rendered; a lift would still owe section 4's notices | 2026-09-25 |
| `undici` | 7.29.1 | MIT, warranty clause intact / MIT | Copyright (c) Matteo Collina and Undici contributors | **CLEARED** as a dependency | 2026-09-25 |
| `undici-types` | 7.18.2 | MIT, warranty clause intact / MIT | Copyright (c) Matteo Collina and Undici contributors | **CLEARED** as a dependency | 2026-09-25 |

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
