# ADR 0017 - The lane FORKS the cross-repo loop modules rather than joining their pin

## Status

`accepted` 2026-09-06.

## Context

`ops/loop/` (CS-918) is ported from a headless lane that has been running in a sibling
repository on this machine. Two files in that lane's directory are not ordinary source:

- `slots.py` - a machine-wide concurrency governor.
- `winmutex.py` - a Win32 named-mutex wrapper.

Both are **BYTE-IDENTICAL-BY-CONTRACT across three separate repositories**, and the
contract is mechanically enforced: a `SHARED_SHA256` table in the sibling's own suite
hashes each file and fails when either moves. The pinned digests at the time of this
decision are:

    slots.py     5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6
    winmutex.py  f1b4b011112685efb88616c52752657cf896fbb0993b2d2d264e7b3edde8b4f4

Copying either file here creates a FOURTH copy that the pin does not cover. That is the
whole of the problem: a pin that names three trees and describes four is a pin that has
quietly stopped meaning anything, and the failure is silent by construction - every
existing test in every existing tree still passes.

Three options were on the table.

**Join the pin.** Vendor both files byte-identical and assert the same digests here, so
all four trees hash equal. Attractive because it is the smallest diff and it keeps one
implementation.

It was rejected because **joining the pin means joining the PROTOCOL, and the protocol is
not ours to join unilaterally.** `slots.py` sets its default bucket to a single shared
directory under `C:\ProgramData`, and that bucket is a token bucket: the three repositories
ration a fixed number of concurrent worker slots between themselves through it, because
they share one metered account. A fourth participant consumes one of THEIR slots. That is a
behavioural change to three trees, made by editing a file in a fourth, with nothing in any
of them recording that it happened - which is a worse version of the exact drift the pin
exists to prevent.

`winmutex.py` fails a second, independent test: it ships two module constants naming
resources this project has nothing to do with, and its docstring names two foreign
repositories. Vendoring that text here would put foreign prose and dead constants in a tree
whose doc topology (CLAUDE.md section 4) says every fact has exactly one owner.

**Edit the sibling copies to accommodate this project.** Rejected outright. Those trees are
outside this repository and this session had no mandate over them; re-pinning is a JOINT
act, and a note in one tree claiming agreement from three is not one.

**Fork explicitly.** Take the code, say so, and pin our own bytes.

## Decision

**Fork, and make the fork legible from inside each file.**

1. **`ops/loop/winmutex.py` is an explicitly FORKED copy.** Its header states that it is a
   fork, names the upstream sha256 it was taken from, says what changed (the two foreign
   resource constants removed, the docstring retargeted, this project's own mutex names
   added) and says why a byte-identical join was refused. Clockspeed's own bytes are then
   pinned by a digest in Clockspeed's own suite, so this copy cannot drift silently either.

2. **`slots.py` is NOT copied at all.** The lane needs exactly two things from it - a
   liveness probe and an exclusive-create bucket at one slot - and both are implemented
   directly in `ops/loop/lanes.py`, whose header records that they are DERIVED from the
   upstream file at the digest above and states that a copy was refused so that this
   project does not join the shared token bucket.

3. **Neither sibling copy is read at test time as a gate.** A cross-tree comparison is
   green-by-skip on any machine without all the trees, which is every CI runner, so it can
   never be the acceptance. The acceptance is our own digest pin.

## Consequences

**Easier.** The lane can be shaped to this project's rules - 7-bit ASCII, its own mutex
names, its own control directory - without negotiating a four-way byte-identical edit. A
change here cannot break a sibling's night, and a change there cannot break ours.

**Harder.** A genuine upstream bug fix no longer arrives for free. Whoever notices one has
to port it deliberately, and the fork header is the only thing that will tell them where to
look. That cost is accepted knowingly: it is paid once per real fix, whereas the silent
alternative charges an unbounded amount at an unpredictable time.

**Foreclosed.** This project must not write into the shared slot bucket, and must not be
added to the sibling `SHARED_SHA256` table on the strength of this ADR alone. Doing either
would restore the coupling this decision removed while leaving the fork headers claiming
otherwise, which is worse than either state on its own.

**Revisit if:** the shared governor stops being a shared token bucket, or the three trees
adopt a published package instead of copied files. Either would remove the reason above,
and at that point joining is the cheaper answer.
