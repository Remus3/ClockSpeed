"use strict";

/**
 * CS-909 slice A - what the companion does about the dashboard process.
 *
 * WHAT THIS IS. Until now the Electron companion assumed the dashboard was
 * already listening, and an operator who opened the shortcut without first
 * starting the surface got a window pointed at nothing. CS-909 makes the
 * shortcut start one. Three questions follow: start a dashboard or adopt the
 * one already answering, keep waiting for it or give up, and on quit stop it
 * or leave it alone. This module answers all three and performs none of them.
 * `shell/main.js` spawns, probes and kills; every DECISION about whether it may
 * lives here.
 *
 * ONLY STOP WHAT YOU STARTED. This is the rule the module exists to hold, so it
 * is stated before anything else. A dashboard the companion did not spawn
 * belongs to whoever did - almost always the operator, in a terminal they are
 * reading. Killing it on quit would take that session down with the window, and
 * the operator would have no way to connect the two events. So the ONLY input
 * that reaches STOP is an explicit, unambiguous "we spawned this one". An
 * adopted dashboard is left running. An unknown answer is left running too: a
 * process that cannot say whether it created something has not earned the right
 * to destroy it. `test/supervisor.test.js` pins that property by name, by
 * sweep, and by counting the return sites in this file.
 *
 * WHY IT IS NOT IN main.js. main.js imports the electron package, so nothing in
 * either language loads it - CS-619 is open against exactly that, and
 * `shell/lib/verdict.js` exists because the same gap let three separate
 * one-line certificate bypasses through a fully green gate before anyone
 * noticed. A lifecycle decision left in main.js would be ungraded in the same
 * way, and its worst mistake is worse than a hung page.
 *
 * IT ANSWERS IN WORDS. `shell/lib/trust.js` returns verdict strings rather than
 * the integers its caller needs, so that no edit there can quietly become a
 * blanket accept - the bypass has no vocabulary in which to be written. The
 * same rule applies here for the same reason. No decision below is a boolean or
 * a number, so nothing in this file can become truthy by accident and no
 * `if (decision)` in a caller can silently authorise a kill. STOP has to be
 * spelled out to happen.
 *
 * EVERY DECISION IS TOTAL. There is no input for which a function here returns
 * nothing, throws, or falls through to the permissive branch. Anything absent,
 * unknown or malformed lands on a NAMED refusal, and each refusal renders as
 * one fixed line an operator can read.
 *
 * WHY THE LINES ARE FIXED. A refusal that quoted what it was handed would print
 * whatever the caller had - and a caller here holds a spawn target and a URL. A
 * path can carry the Windows account name, which is non-negotiable 3. So
 * `supervisorRefusal` is the only author of refusal text, it takes a member of
 * the closed vocabulary below and never a string of the caller's, and it quotes
 * nothing. That is the shape `shell/lib/endpoint.js` uses over its four faults.
 *
 * WHAT THIS FILE MAY NOT ACQUIRE. It imports nothing at all, and specifically
 * not the electron package, a child-process module, a transport module, the
 * filesystem or the platform module. Those are what would let a decision module
 * DO the thing it decides, which would put a spawn or a kill back on the far
 * side of the line that makes any of this gradable. The test suite asserts the
 * absence directly rather than trusting this paragraph.
 *
 * COMMONJS DELIBERATELY. The manifest carries no `type` field, and every
 * sibling under `shell/lib/` is read as CommonJS.
 */

// ---------------------------------------------------------------------------
// The vocabulary - decisions
// ---------------------------------------------------------------------------

/** Nothing answers, so the companion may start a dashboard of its own. */
const START = "START";

/** Something already answers. Use it, and never start a second one. */
const ADOPT = "ADOPT";

/** We spawned it, so it is ours to shut down. The ONLY word that permits a kill. */
const STOP = "STOP";

/** We did not spawn it. Leave it exactly as it was found. */
const LEAVE = "LEAVE";

/** The dashboard answered. Stop probing and load the window. */
const READY = "READY";

/** No answer yet, and attempts remain. Wait an interval and probe again. */
const RETRY = "RETRY";

/** No answer, and the attempts are used up. Stop waiting and say so. */
const GIVE_UP = "GIVE_UP";

// ---------------------------------------------------------------------------
// The vocabulary - refusals
// ---------------------------------------------------------------------------

// These are decisions too, in the sense that they come back from the same
// functions and are strings like the rest. They are listed apart because each
// one means "this module declined to answer", and because each renders to a
// fixed operator line through the single function below.

/** The health answer was neither true nor false. */
const REFUSE_UNKNOWN_HEALTH = "REFUSE_UNKNOWN_HEALTH";

/** Whether this process spawned the dashboard was neither true nor false. */
const REFUSE_UNKNOWN_OWNERSHIP = "REFUSE_UNKNOWN_OWNERSHIP";

/** The probe attempt was not a whole count starting at one. */
const REFUSE_UNKNOWN_ATTEMPT = "REFUSE_UNKNOWN_ATTEMPT";

/** Whether the probe was answered was neither true nor false. */
const REFUSE_UNKNOWN_ANSWER = "REFUSE_UNKNOWN_ANSWER";

// The lines themselves. No separator, no scheme, no file name, no fragment of
// anything a caller passed in - see the header. They read as statements about
// what the companion will not do, because that is what an operator needs to
// know when one of them appears.

const UNKNOWN_HEALTH =
  "the dashboard health answer was neither yes nor no, so the companion will not " +
  "decide whether to start one";
const UNKNOWN_OWNERSHIP =
  "the companion cannot tell whether it started the dashboard, so it will not stop one";
const UNKNOWN_ATTEMPT =
  "a probe attempt must be counted as a whole number starting at one";
const UNKNOWN_ANSWER =
  "a probe was recorded as neither answered nor unanswered, so the wait cannot be judged";

/**
 * What a caller who asked for the text of something outside the vocabulary is
 * told. A PROGRAMMING error rather than an operational one, so it raises - but
 * it is a fixed line for the same reason every line above is. Letting the
 * lookup fail and reporting its key would render whatever arrived, and the one
 * call this vocabulary exists to stop is a refusal built out of a caller's own
 * value. It quotes nothing it was handed.
 */
const NOT_A_REFUSAL = "a supervisor refusal must name one of this module's refusal words";

/** Refusal word to the one line it is spoken as. */
const REFUSALS = Object.freeze(
  new Map([
    [REFUSE_UNKNOWN_HEALTH, UNKNOWN_HEALTH],
    [REFUSE_UNKNOWN_OWNERSHIP, UNKNOWN_OWNERSHIP],
    [REFUSE_UNKNOWN_ATTEMPT, UNKNOWN_ATTEMPT],
    [REFUSE_UNKNOWN_ANSWER, UNKNOWN_ANSWER],
  ])
);

/**
 * The one line an operator reads when this module declined to decide.
 *
 * A MODULE-LEVEL FUNCTION RATHER THAN A METHOD, so the text has one author and
 * no caller has to render an object to reach it.
 *
 * @param {unknown} refusal One of this module's refusal words, never text.
 * @returns {string} The fixed line for that refusal.
 * @throws {TypeError} `refusal` is not a member. CHECKED EXPLICITLY rather than
 *   left to the lookup, because a lookup failure that reported its key would
 *   leak the caller's value through the guard rail's own failure path.
 */
function supervisorRefusal(refusal) {
  if (typeof refusal !== "string" || !REFUSALS.has(refusal)) {
    throw new TypeError(NOT_A_REFUSAL);
  }
  return REFUSALS.get(refusal);
}

// ---------------------------------------------------------------------------
// How the companion waits
// ---------------------------------------------------------------------------

/**
 * How long to wait between two probes, in milliseconds.
 *
 * The gap sits BETWEEN probes rather than between their start times, so a slow
 * probe and a fast one cannot overlap and the ceiling below counts real
 * attempts rather than timers that fired.
 */
const PROBE_INTERVAL_MS = 250;

/**
 * How many probes may go unanswered before the companion stops waiting.
 *
 * The product of this and the interval is how long an operator waits when
 * nothing is ever going to bind - deliberately not restated as a third number,
 * because a stated total is a number that drifts the moment either factor
 * changes. A dashboard that is never going to come up fails its probes
 * immediately rather than by timing out, so the common bad case is the fast one.
 *
 * MEASURED, NOT REASONED. This value was raised from 40 on 2026-09-05 against a
 * measurement rather than a hunch, and the measurement is recorded here because
 * the value means nothing without it. Five samples of a real spawn, timed from
 * process start to the first answered health probe over TLS: 2.217s minimum,
 * 2.221s median, 2.227s maximum with world detection on, which is what a
 * shortcut launch does. With detection off the median was 2.060s, so parsing the
 * save costs about a sixth of a second. Machine load was 4 per cent.
 *
 * WHY THE MARGIN IS SO MUCH WIDER THAN THAT SPREAD. The old value left roughly a
 * four-and-a-half times margin, which looks generous and is not: this machine is
 * shared, and an unrelated session has held it at 99 per cent CPU for most of a
 * session. A margin of that size does not survive a load swing of that size. The
 * two failure directions are not symmetric - too tight refuses a WORKING system
 * on the operator's first double click, which reads as a broken shortcut, while
 * too loose only lengthens an error nobody reaches at a 2.2 second start.
 *
 * WHAT THE MEASUREMENT DOES NOT COVER: none of those samples was cold in the
 * operating system cache sense, because the surface had already run in that
 * session. A first start after a reboot could be slower, which argues the same
 * direction this change already went.
 */
const PROBE_ATTEMPT_CEILING = 80;

/**
 * How long a single probe may take before it counts as unanswered.
 *
 * Larger than the interval on purpose. This bounds the case where something is
 * listening but not answering - a half-open socket, or a server still building
 * its route table - which is exactly the case a gap-sized timeout would call a
 * failure while the dashboard was seconds from working.
 */
const PROBE_TIMEOUT_MS = 2000;

// ---------------------------------------------------------------------------
// How the companion spawns
// ---------------------------------------------------------------------------

/** The interpreter switch that runs a module rather than a script file. */
const MODULE_FLAG = "-m";

/**
 * The surface's own composition root, named as a MODULE and never as a file.
 *
 * NO PATH APPEARS IN THIS FILE AND NONE MAY. A path can carry the Windows
 * account name, which is non-negotiable 3, and an interpreter spelled here
 * would be the hardcoded interpreter BOOTSTRAP.md section 2.5 forbids. Choosing
 * the interpreter and the working directory is main.js's job; this module says
 * only what comes after it. Matched against `clockspeed/surface/__main__.py`,
 * which is the module this names.
 */
const SERVER_MODULE = "clockspeed.surface";

const SERVER_ARGV = Object.freeze([MODULE_FLAG, SERVER_MODULE]);

/**
 * The argument vector the dashboard is spawned with, after the interpreter.
 *
 * A FRESH ARRAY EVERY CALL. A caller that appends a flag to what it was given
 * must not be able to change what the next caller receives; a shared literal is
 * a mutable global wearing a constant's name. `shell/lib/geometry.js` returns a
 * fresh object for the same reason.
 *
 * @returns {Array<string>} A new array holding the module invocation.
 */
function serverArgv() {
  return Array.from(SERVER_ARGV);
}

// ---------------------------------------------------------------------------
// The decisions
// ---------------------------------------------------------------------------

/**
 * True only for `true` and `false`, and for nothing else at all.
 *
 * STRICTLY A BOOLEAN, not merely truthiness. `0` and `1` are the realistic way
 * a count arrives where an answer belongs, and a truthy check would read one as
 * yes and the other as no while both mean the caller lost track of what it was
 * holding. The string "false" is the realistic way a value arrives from an
 * environment or a config file, and it is truthy.
 */
function isAnswer(value) {
  return value === true || value === false;
}

/** The options object a caller passed, or an empty one if it passed nothing usable. */
function optionsOf(input) {
  return input !== null && typeof input === "object" ? input : {};
}

/**
 * Start a dashboard, or adopt the one already running.
 *
 * @param {object} [options]
 * @param {boolean} [options.healthy] Whether something already answers.
 * @returns {string} ADOPT, START, or REFUSE_UNKNOWN_HEALTH.
 */
function decideStart(options) {
  const healthy = optionsOf(options).healthy;

  if (!isAnswer(healthy)) {
    // Neither branch is safe on a guess. Starting over a live dashboard ends in
    // a bind refusal and a window pointed at a process that just died; adopting
    // a dead one ends in a window pointed at nothing. Both are legible failures
    // only if the caller is told which question went unanswered.
    return REFUSE_UNKNOWN_HEALTH;
  }

  // Adoption is checked first because it is the answer that spawns nothing, and
  // an ordering where the doing branch comes first is one edit away from being
  // the fall-through.
  if (healthy) {
    return ADOPT;
  }
  return START;
}

/**
 * On quit: stop the dashboard, or leave it running.
 *
 * THE ONLY FUNCTION HERE THAT CAN AUTHORISE A KILL, and it does so from exactly
 * one site, reached only by an explicit `true`. Everything else - an adopted
 * dashboard, a missing flag, a caller that lost track - answers a word that
 * permits nothing. See this module's header for why that asymmetry is the whole
 * point rather than a convenience.
 *
 * @param {object} [options]
 * @param {boolean} [options.started] Whether THIS process spawned the dashboard.
 * @returns {string} STOP, LEAVE, or REFUSE_UNKNOWN_OWNERSHIP.
 */
function decideStop(options) {
  const started = optionsOf(options).started;

  if (!isAnswer(started)) {
    return REFUSE_UNKNOWN_OWNERSHIP;
  }

  // Written as "not ours, so leave it" rather than as "ours, so stop it",
  // because the refusal above and this branch both have to reach LEAVE and only
  // the single line below may reach the kill.
  if (!started) {
    return LEAVE;
  }
  return STOP;
}

/**
 * After one probe: load the window, wait and probe again, or stop waiting.
 *
 * BOTH INPUTS ARE VALIDATED BEFORE EITHER IS USED. An attempt that is not a
 * count cannot be compared against the ceiling and mean anything, so a malformed
 * one refuses even when the probe was answered - a caller whose loop bookkeeping
 * is corrupt does not know how many attempts remain, and saying READY would hide
 * that. The attempt is checked first so that a caller repairing the loop is told
 * which of the two values to look at.
 *
 * AN ANSWER AT OR BEYOND THE CEILING IS STILL AN ANSWER. The ceiling bounds how
 * long the companion WAITS, not whether a reply counts, so `answered` is read
 * before the ceiling is compared.
 *
 * @param {object} [options]
 * @param {number} [options.attempt] Which probe just finished, counting from one.
 * @param {boolean} [options.answered] Whether the dashboard answered it.
 * @returns {string} READY, RETRY, GIVE_UP, or one of two refusals.
 */
function decideProbeOutcome(options) {
  const opts = optionsOf(options);
  const attempt = opts.attempt;
  const answered = opts.answered;

  // Number.isInteger already excludes NaN and both infinities, so neither needs
  // a separate test. The lower bound is one rather than zero: attempt zero names
  // a probe that never ran.
  if (!Number.isInteger(attempt) || attempt < 1) {
    return REFUSE_UNKNOWN_ATTEMPT;
  }
  if (!isAnswer(answered)) {
    return REFUSE_UNKNOWN_ANSWER;
  }

  if (answered) {
    return READY;
  }

  // `>=` and not `>`. The ceiling is the last attempt that may be made, so
  // reaching it is the end of the wait rather than one more retry.
  if (attempt >= PROBE_ATTEMPT_CEILING) {
    return GIVE_UP;
  }
  return RETRY;
}

module.exports = {
  ADOPT,
  GIVE_UP,
  LEAVE,
  MODULE_FLAG,
  NOT_A_REFUSAL,
  PROBE_ATTEMPT_CEILING,
  PROBE_INTERVAL_MS,
  PROBE_TIMEOUT_MS,
  READY,
  REFUSALS,
  REFUSE_UNKNOWN_ANSWER,
  REFUSE_UNKNOWN_ATTEMPT,
  REFUSE_UNKNOWN_HEALTH,
  REFUSE_UNKNOWN_OWNERSHIP,
  RETRY,
  SERVER_MODULE,
  START,
  STOP,
  decideProbeOutcome,
  decideStart,
  decideStop,
  serverArgv,
  supervisorRefusal,
};
