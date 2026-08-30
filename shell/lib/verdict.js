"use strict";

// CS-602 repair slice R1 - the only place a verdict becomes a number.
//
// WHAT THIS IS. shell/lib/trust.js answers in WORDS, never in integers, so that
// no edit there can quietly become an unconditional accept - the blanket bypass
// has no vocabulary in that file in which to be written. Electron's verify
// callback takes an integer, so something has to translate. This module is that
// something, and it is a separate file for one reason: it can be loaded and
// graded without electron, without a display and without a binary.
//
// WHY IT IS NOT IN main.js ANY MORE. It was, and the consequence was measured
// rather than argued. main.js imports electron, so no test in either language
// could load the mapping, and every one of these edits left the entire gate
// green - the Python shell suite at 63 passed, node --test at 174 passing, the
// drift guard clean and the commit gate passing:
//
//   callback(codeFor(verdict))   ->  callback(0)      blanket accept, every host
//   [trust.DEFER, -3]            ->  [trust.DEFER, 0]
//   [trust.REFUSE_NO_PIN, -2]    ->  [trust.REFUSE_NO_PIN, 0]
//
// The mapping was never hard to test. It is a total function from five strings
// to three integers - no I/O, no clock, no configuration. It was untested
// because of WHERE IT LIVED, and moving it is the whole repair.
//
// WHAT THIS FILE MAY NOT ACQUIRE. Any import of electron, the filesystem or a
// path module puts it back on the far side of that line and silently mutes
// shell/test/verdict.test.js. That suite asserts the absence directly rather
// than trusting this paragraph.

const trust = require("./trust.js");

// ---------------------------------------------------------------------------
// The map
// ---------------------------------------------------------------------------

// WHAT IS TYPE-CHECKED HERE AND WHAT IS NOT. Electron 44.0.0's shipped typings
// state only that 0 accepts the certificate and -2 rejects it. They contain no
// occurrence of -3, and no mention of Certificate Transparency anywhere. Both
// of those come from the published API page and from nothing else. They are
// therefore NOT type-checked, and neither has been observed against a running
// electron by anyone who wrote this file. That distinction is recorded rather
// than smoothed over: the typings agreeing with the docs page would have been
// evidence, and the typings being silent is not the same thing.
//
// THE ACCEPTING CODE IS DOCUMENTED TO DO MORE THAN ACCEPT. The API page states
// that it also switches Certificate Transparency verification off for the
// session. That is the documented reason exactly one verdict may reach it.
// DEFER pointedly does not share it: deferring hands the decision back to
// Chromium with its full validation still switched on, which is the right
// answer for every host that is not ours.
//
// IF DEFER'S CODE IS NOT HONOURED AS DOCUMENTED, THIS FAILS CLOSED - and that
// argument does not rest on the docs page either. The parameter is a Chromium
// net error code, a space in which 0 is the only success value and every
// negative is an error; -3 with no special handling is a failed load. So a
// value electron did not interpret as documented refuses the connection rather
// than trusting it. The residual exposure is functional, not a trust one, and
// it is small: DEFER is reached only for a host that is not ours, and this
// shell loads exactly one origin - the local dashboard, which requests no
// remote resource of any kind.
//
// All three refusals share a single code. They are separate verdicts because
// they are separate faults worth telling apart when reading a trace, not
// because electron has more than one way to say no.
const VERDICT_CODES = new Map([
  [trust.TRUST, 0],
  [trust.DEFER, -3],
  [trust.REFUSE_NO_PIN, -2],
  [trust.REFUSE_NO_CERT, -2],
  [trust.REFUSE_MISMATCH, -2],
]);

/**
 * Raised when a verdict reaches this module that the map does not hold.
 *
 * IT CARRIES NO CODE PROPERTY, deliberately. An error object holding an integer
 * would be a second place a number could reach the callback, which is the one
 * property the split into this module exists to keep.
 */
class UnknownVerdictError extends Error {
  /**
   * @param {unknown} verdict What arrived instead of a known verdict.
   */
  constructor(verdict) {
    super("clockspeed: an unrecognised trust verdict reached the code map");
    this.name = "UnknownVerdictError";
    // The offending value is exposed for a caller that wants to log it, as a
    // string, so that an object with a hostile toString cannot make a consumer
    // throw a second time. It is a verdict word and never a certificate, a
    // hostname or a path, so nothing personal can arrive by this route.
    this.verdict = typeof verdict === "string" ? verdict : typeof verdict;
  }
}

/**
 * Turn a verdict into the integer electron's verify callback expects.
 *
 * THROWS RATHER THAN DEFAULTING. A silent default here would be the blanket
 * bypass wearing a different hat: whichever integer it chose, a sixth verdict
 * added to trust.js would start receiving it without anyone deciding that it
 * should. The refusal that a real callback needs is codeForOrRefuse's job, and
 * it reads its answer back out of this same map rather than writing a literal.
 *
 * @param {unknown} verdict One of the five words shell/lib/trust.js returns.
 * @returns {number} The code for that verdict.
 * @throws {UnknownVerdictError} If the map does not hold the verdict.
 */
function codeFor(verdict) {
  const code = VERDICT_CODES.get(verdict);
  if (code === undefined) {
    throw new UnknownVerdictError(verdict);
  }
  return code;
}

/**
 * The same mapping, for a caller that must not be allowed to throw.
 *
 * WHY THIS EXISTS AS WELL. A verify callback that throws never calls back at
 * all, so the page HANGS instead of being refused - shell/lib/trust.js records
 * that hazard in its own header and ADR 0014 records it again. A hang is worse
 * than the bug that produced it, because a refusal is legible and a hang is
 * not. So the strict function above is what a reviewer reads and what the
 * suite grades, and this is the one the callback consumes.
 *
 * The fallback is a REFUSAL and it is read out of the map, never spelled as a
 * number. A literal here would be a second, quieter place an integer reaches
 * the callback.
 *
 * @param {unknown} verdict One of the five words shell/lib/trust.js returns.
 * @returns {number} The code for that verdict, or the refusal code.
 */
function codeForOrRefuse(verdict) {
  try {
    return codeFor(verdict);
  } catch {
    return VERDICT_CODES.get(trust.REFUSE_MISMATCH);
  }
}

module.exports = {
  VERDICT_CODES,
  UnknownVerdictError,
  codeFor,
  codeForOrRefuse,
};
