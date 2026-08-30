# ADR 0014 - The shell trusts one pinned certificate and defers every other host

## Status

`accepted` - 2026-08-30.

## Context

CS-602's acceptance requires the companion window to handle the dashboard's self-signed
certificate "without disabling certificate validation wholesale". The dashboard is HTTPS
only and its pair is self-signed and gitignored, so Chromium will not trust it and
something in the shell has to say that one specific certificate is acceptable.

**The shortcut is the thing being refused.** A verify callback that answers success
unconditionally satisfies the literal goal - the window loads - while switching off
validation for every host that session ever reaches.

**Two Electron mechanisms could carry the decision, and they are not equivalent.**

- `app.on('certificate-error')` fires only when Chromium's own verification has ALREADY
  FAILED. A rogue certificate that Chromium happens to accept never reaches the handler,
  so pinning there can never refuse anything Chromium approved. It is strictly weaker,
  and the weakness is invisible: the handler looks like it sits in the trust path while
  actually sitting downstream of the only decision that matters.
- `session.setCertificateVerifyProc` is consulted on EVERY verification, accepted or
  rejected alike. Pinning there is strictly stronger.

Registering both would build a second, weaker path to the same decision, which is why one
of them has to be forbidden rather than merely left unused.

**Properties of the primitives shape the implementation, and three of these were measured
rather than assumed.**

- The certificate arrives as PEM - Electron's typings describe `certificate.data` as PEM
  encoded data. PEM is text, so a string compare is at the mercy of line-ending
  normalisation. This project has a recorded incident of tooling rewriting LF to CRLF
  while git reported the tree clean, which is exactly the accident that would turn a pin
  into a permanent mismatch.
- `crypto.timingSafeEqual` THROWS on differing lengths rather than returning false -
  measured here as `RangeError: Input buffers must have the same byte length`. A verify
  callback that throws never calls back at all, so the load HANGS instead of being
  refused. That outcome is worse than the bug that produced it, because a refusal is
  legible and a hang is not.
- `crypto.timingSafeEqual` reports two EMPTY buffers as EQUAL - measured. The order of the
  emptiness checks is therefore a security property rather than tidiness: a peer
  presenting nothing, against a pin that never loaded, would otherwise be trusted.
- `callback(0)` is not a neutral "yes". It is documented as carrying a side effect beyond
  accepting the certificate, which is why an unconditional one is not merely lazy.

## Decision

**The shell pins ONE certificate by byte identity in `session.setCertificateVerifyProc`,
and defers every other host to Chromium's own verification.** Nothing is disabled
wholesale, for any host, at any time.

- The comparison is over DER bytes, never PEM text. The PEM string is converted with
  `crypto.X509Certificate(...).raw` and compared with `crypto.timingSafeEqual`, behind a
  length check that keeps the throw unreachable.
- The decision is a pure function returning WORDS, in `shell/lib/trust.js`. The callback
  integers appear nowhere in it, so no edit there can quietly become an unconditional
  `callback(0)` - the blanket bypass has no vocabulary in that file in which to be
  written.
- Mapping words onto integers is a separate module's job, and that module is
  `shell/lib/verdict.js`: `TRUST` maps to `0`, `DEFER` to `-3`, and every `REFUSE_`
  verdict to `-2`. **This sentence was false when this ADR was first accepted** - the
  mapping was then inside `shell/main.js`, which imports Electron and is therefore
  unloadable by any test. The consequence is recorded under Consequences below rather
  than quietly repaired here.
- `shell/lib/verdict.js` imports `./trust.js` and nothing else - no Electron, no
  filesystem, no path module - so it loads on a bare Node. It exposes a strict `codeFor`
  that THROWS a named error on an unrecognised verdict, because a silent default is the
  blanket bypass wearing a different hat, and a `codeForOrRefuse` that the verify callback
  actually consumes, because a callback that throws never calls back at all and the page
  then hangs instead of being refused. The fallback in that wrapper is read back out of
  the same map rather than written as a literal, so there is still exactly one place in
  the shell where a verdict becomes a number.
- A host that is not the dashboard's DEFERS rather than refuses. Deferring leaves
  Chromium's full validation switched on, which is the correct answer for every host that
  is not ours, whereas refusing would break ordinary browsing and invite the bypass back
  as a fix.
- **`app.on('certificate-error')` is forbidden in this shell**, for the reason given in
  Context: it is a second and weaker path to the same decision.

## Consequences

**Re-minting the certificate does NOT produce an immediate visible refusal, and the
natural assumption to the contrary is false.** Electron's shipped typings note that the
result of the verify procedure is CACHED by the network service, so a verdict already
reached can persist in that cache after the underlying certificate has changed. The
protection that actually carries the weight is therefore `scripts/make_cert.py` refusing
to overwrite an existing pair without `--force`, and not any check made at load time.
Anyone reasoning about what happens when the pair is replaced must reason about the cache
rather than about the next handshake.

**The verdict-to-integer mapping was UNGRADED until the repair that added
`shell/lib/verdict.js`, and this section previously implied otherwise.** It said only that
the ungraded parts of this decision need a human at a display. That was true of the window
and false of the mapping: `codeFor` was a pure total function from five strings to three
integers, needing no display, no Electron and no binary - it was ungraded purely because
it sat in `shell/main.js`, on the far side of an Electron import that no test can cross.

The gap was measured rather than inferred. Against the tree that first carried this ADR,
each of these edits left the Python shell suite, `node --test`, the drift guard and the
commit gate ALL GREEN:

- `callback(codeFor(verdict))` changed to `callback(0)` - a blanket accept for every host
  in the session, which is precisely what the acceptance clause forbids.
- `[trust.DEFER, -3]`, `[trust.REFUSE_NO_PIN, -2]` or `[trust.REFUSE_MISMATCH, -2]`
  changed to map to `0`.
- A rewrite that kept exactly one `callback(` site and still answered `0` for every
  verdict.

The static guard counted the callback TOKEN and never read its ARGUMENT, so a call that
happened was indistinguishable from a call that carried the verdict.

**What grades it now.** `shell/test/verdict.test.js` loads the mapping without Electron and
pins all five verdicts by value, that only `TRUST` reaches the accepting code, that every
refusal is negative, and that an unknown verdict throws. `tests/shell/test_shell_assets.py`
pins the one call site's argument by exact expression, refuses any digit reaching that
callback, and pins the five map entries as text - the last of these because the Node suite
runs only on the tier-2 lane, while the Python one runs on every push. Each of the bypasses
listed above was re-applied after the repair and measured red.

What remains gradeable only by a human at a real display is the WINDOW - that it opens,
where it opens, and that the pinned certificate is accepted by a running Chromium. CI has
no display and never installs Electron, so no machine grades those at all. They are
enumerated as a manual list in `docs/OPERATIONS.md`, written so that an unrun step cannot
read as a passed one.

What becomes harder: the pin is byte identity, so ANY legitimate re-mint breaks the
companion until the new bytes are loaded. That is the intended trade - every looser
comparison is a hole, and a rotation story does not exist yet.

**Recorded as unresolved rather than rounded up.** The typings shipped with the Electron
version pinned in `shell/package.json` document `callback(0)` as accept and `callback(-2)`
as reject, and are SILENT on two claims this decision relies on: that `callback(-3)` means
use Chromium's own result, and that `callback(0)` additionally disables Certificate
Transparency verification. Both rest on Electron's prose documentation rather than on the
shipped typings, and are recorded here as documented but not type-checked. The `DEFER`
mapping is the part that would move if the `-3` claim were wrong.

**Revisit if** the shell needs to trust more than one certificate, if a rotation story is
added, or if Electron changes the verify-proc contract.

ADR 0013 cleared Electron for this use. This decision consumes that verdict and does not
restate it.
