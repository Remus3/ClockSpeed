'use strict';

// CS-602 slice S2 - the certificate-pinning decision, and nothing else.
//
// WHAT THIS IS. The Electron shell talks to a local HTTPS surface that serves
// a self-signed certificate. Chromium will not trust it, so the shell has to
// say "this one specific certificate is fine". The dangerous way to do that is
// to hand Electron a verify callback that answers success unconditionally,
// because callback(0) does not merely accept the certificate - it also
// disables Certificate Transparency verification, for every request in that
// session. This module exists so that the decision can be read, reviewed and
// tested on its own.
//
// WHY IT RETURNS WORDS AND NOT NUMBERS. Electron's setCertificateVerifyProc
// takes an integer: 0 success, -2 failure, -3 use Chromium's own result. Those
// integers are deliberately absent from this file. Mapping a verdict onto them
// is a separate module's job. Keeping the numbers out means no edit here can
// quietly become an unconditional callback(0) - the blanket bypass has no
// vocabulary in which to be written.
//
// WHAT IT DOES NOT DO. It performs no I/O, reads no configuration, logs
// nothing, mutates nothing and consults no clock. It does not check expiry,
// chain, revocation or subject name. It answers exactly one question - are
// these bytes the bytes we pinned - and defers everything else to Chromium.

const crypto = require('node:crypto');

// The five verdicts. Strings, so that a stray verdict shows up legibly in a
// log or an assertion rather than as an integer that could be mistaken for a
// callback code.
const TRUST = 'TRUST';
const DEFER = 'DEFER';
const REFUSE_NO_PIN = 'REFUSE_NO_PIN';
const REFUSE_NO_CERT = 'REFUSE_NO_CERT';
const REFUSE_MISMATCH = 'REFUSE_MISMATCH';

// byteLength, never .length. A Uint16Array of n elements has n .length but 2n
// bytes, and timingSafeEqual compares bytes. Guarding on element count would
// let two views of differing byte size past the guard and into the throw.
function isNonEmptyBytes(value) {
  return ArrayBuffer.isView(value) && value.byteLength > 0;
}

function isNonEmptyString(value) {
  return typeof value === 'string' && value.length > 0;
}

// decide - pure. Returns one of the five verdicts above, always, for any input.
//
// The order of these checks is load-bearing and is not free to be rearranged:
//
//   1. No pin means there is nothing this module could possibly authorise, so
//      it refuses before looking at anything else.
//   2. A hostname that is not the one the pin was issued for defers. It does
//      NOT refuse: refusing would break ordinary browsing, while deferring
//      leaves Chromium's full validation switched on, which is the correct
//      answer for every host that is not ours.
//   3. Only then is the presented certificate considered.
//   4. The length check MUST precede timingSafeEqual, which throws a RangeError
//      on differing lengths rather than returning false. A verify callback that
//      throws never fires at all, so the page load hangs instead of being
//      refused - a worse outcome than either verdict.
//   5. The compare is constant-time. The pinned certificate is not secret, so
//      this is belt and braces rather than a strict necessity, but a
//      byte-by-byte early-exit compare here would be a needless side channel.
//
// Note that step 1 and step 3 also stand between an empty buffer and the
// compare, which matters more than it looks: timingSafeEqual reports two empty
// buffers as EQUAL. Were those checks moved below the compare, a peer that
// presented nothing against a pin that was never loaded would be trusted.
function decide(request) {
  const input = request !== null && typeof request === 'object' ? request : {};
  const hostname = input.hostname;
  const expectedHost = input.expectedHost;
  const pinnedDer = input.pinnedDer;
  const presentedDer = input.presentedDer;

  if (!isNonEmptyBytes(pinnedDer)) {
    return REFUSE_NO_PIN;
  }

  // A missing or non-string host on either side is treated as not-our-host and
  // defers. This can only ever turn a would-be trust into Chromium's own
  // verdict, never the reverse, so a caller that forgets to pass a hostname
  // loses the pin rather than silently widening it.
  if (!isNonEmptyString(hostname) || !isNonEmptyString(expectedHost)) {
    return DEFER;
  }
  if (hostname !== expectedHost) {
    return DEFER;
  }

  if (!isNonEmptyBytes(presentedDer)) {
    return REFUSE_NO_CERT;
  }

  if (pinnedDer.byteLength !== presentedDer.byteLength) {
    return REFUSE_MISMATCH;
  }

  // Both operands are now guaranteed to be ArrayBufferViews of equal, non-zero
  // byte length, which excludes both of timingSafeEqual's documented throw
  // conditions. The call is deliberately NOT wrapped in a try/catch: swallowing
  // an exception here would hide exactly the regression the suite asserts
  // against, and the safe-looking catch would be an uncoverable branch.
  if (crypto.timingSafeEqual(pinnedDer, presentedDer)) {
    return TRUST;
  }

  return REFUSE_MISMATCH;
}

// pemToDer - converts a PEM certificate string to its DER bytes.
//
// Electron hands the certificate over as a PEM-encoded STRING on
// certificate.data, not as a DER buffer, so something has to do this
// conversion before decide() can compare bytes.
//
// It returns null rather than throwing on anything it cannot parse. That is
// the whole point of the helper: a malformed certificate is a thing an
// attacker can send, and it has to end in a refusal, not in an exception
// escaping through a verify callback that then never fires.
function pemToDer(pem) {
  if (!isNonEmptyString(pem)) {
    return null;
  }
  try {
    const der = new crypto.X509Certificate(pem).raw;
    return isNonEmptyBytes(der) ? der : null;
  } catch (err) {
    return null;
  }
}

module.exports = {
  TRUST,
  DEFER,
  REFUSE_NO_PIN,
  REFUSE_NO_CERT,
  REFUSE_MISMATCH,
  decide,
  pemToDer,
};
