# ADR 0013 - Electron clears the licence gate for local use, with obligations only on distribution

## Status

`accepted` - 2026-08-30.

## Context

CS-602 builds the companion window and needs Electron. `CLAUDE.md`'s Settled section
already says "Node exists solely for the Electron shell", but that is an ARCHITECTURAL
choice and not a licence verdict. `CONVENTIONS.md` section 14 requires the licence be
checked and stated, and records that verbal clearance is not written clearance.

The five traps were applied rather than an SPDX grep.

**Trap 1 fires in shape and is the finding worth keeping.** Electron's repository-root
`package.json` is `@electron-ci/dev-root` carrying `"private": true`, sitting beside an
MIT `LICENSE` - exactly the self-contradicting manifest section 14 warns about. It
resolves benign only because that manifest is the CI workspace root rather than the
published artifact; the published package manifest is `electron`, MIT, with no `private`
field. **The literal procedure section 14 prescribes - read the LICENSE and the manifest -
returns the WRONG answer on this repository unless the manifest read is the PUBLISHED
one.** That is a correction to how the gate is run, not only to what it concluded here.

Trap 2 fires benignly: two holders, "Electron contributors" and GitHub Inc for 2013-2020,
so the MIT grant is good but nobody can grant different terms. Traps 3, 4 and 5 do not
fire; the copyright line names real grantors and the warranty and liability clauses are
intact in the published tarball.

**What travels inside a shipped binary is not all MIT.** Chromium is BSD-3-Clause, and
FFmpeg is LGPL 2.1 or later - shipped as a separate replaceable `ffmpeg.dll` precisely so
the relink requirement stays satisfiable. Those obligations are triggered by
REDISTRIBUTION and by nothing else.

## Decision

Three scopes, three verdicts, and they are recorded separately because a future reader who
sees only "Electron: MIT, cleared" will not know the third was never cleared
unconditionally.

- **(a) Electron as a local devDependency, nothing committed: CLEARED.** MIT grants use
  without condition; the notice condition is met inherently because the tarball ships its
  own `LICENSE` into `node_modules/`, which is gitignored.
- **(b) A public repository whose manifest merely NAMES electron: CLEARED.** Naming a
  dependency is a reference, not a copy. A manifest entry contains no Electron code.
- **(c) Distributing a packaged binary embedding Electron: CLEARED WITH OBLIGATIONS.**
  Permitted, and every obligation lands here at once.

**No Electron-owned text is copied into the tracked tree.** `shell/` is authored against
the documented API rather than seeded from a quickstart template, which is section 14's
always-legal path and keeps (b) free of any notice-retention duty.

## Consequences

CS-602 may proceed. Nothing it builds reaches scope (c): it is a local window and
distributes nothing.

The obligations that attach if distribution is ever contemplated: ship the `LICENSE`
already present in the distribution rather than overwriting it with the project's own;
ship `LICENSES.chromium.html`; keep FFmpeg a replaceable shared library and be able to
offer its source; retain Node's notices. Separately, the default prebuilt carries
proprietary codecs (H.264, AAC) and Electron publishes a patent-free alternate per
release - PATENT exposure is not a copyright question and is deliberately NOT resolved
here.

`docs/GATED.md` CS-G03's third-party licence audit clause cites this ADR.

**Revisit if** distribution is contemplated, or if any Electron-owned text is copied into
the tracked tree - that converts (b) into a notice-retention obligation immediately.

**Recorded as unresolved rather than rounded up:** whether `LICENSES.chromium.html` also
covers Node's bundled dependency notices; whether the default prebuilt enables proprietary
codecs, treated as YES until measured; and a 2016 claim that Electron is "actually GPL",
whose resolution could not be read because the repository holding it is archived, and
which the primary sources contradict.

**Operational, and not a licence matter:** installing electron runs a postinstall that
downloads a prebuilt binary from Electron's releases, so it is a network dependency at
INSTALL time. It is a download and not an upload, so the "nothing is uploaded" property
holds, and Electron sits wholly outside the advice path, so the zero-language-model rule
is untouched.
