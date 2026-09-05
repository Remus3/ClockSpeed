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
 * WHY IT RESOLVES THE INTERPRETER, AND WHY THE CURRENT DIRECTORY IS EXCLUDED.
 * `resolveInterpreter` exists because naming the interpreter and letting the
 * spawn find it is a local code-execution vector on Windows. MEASURED on this
 * machine, with a copy of another executable renamed to the interpreter's name
 * and placed in the spawn's working directory:
 *
 *   - libuv resolves that directory BEFORE it scans PATH, so the planted binary
 *     wins and the real interpreter is never reached. The spawn is windowsHide
 *     with its output discarded, so nothing is shown when it happens.
 *   - The gate is `NeedCurrentDirectoryForExePath`, which libuv consults in the
 *     PARENT process. It is quietened by an environment variable that is set at
 *     NEITHER machine NOR user scope here - some shells set it for themselves,
 *     which is why a first test of this came back clean and meant nothing. An
 *     Explorer-launched companion, which is what the shortcut produces, has the
 *     search live.
 *   - The repository root grants Modify to Authenticated Users, so planting the
 *     file needs no privilege the attacker does not already have.
 *
 * So the interpreter is resolved to an ABSOLUTE path here, from PATH alone, and
 * the caller spawns that rather than a name. A relative PATH entry is discarded
 * for the same reason the current directory is - "." is how the current
 * directory arrives inside a PATH, and an entry that is not rooted is one whose
 * meaning depends on where the process happens to be standing.
 *
 * NOT MODELLED ON `shutil.which`, WHICH WAS MEASURED AND DOES NOT DO THIS.
 * `scripts/make_cert.py` resolves openssl through it, and this module was
 * originally to be described as the same doctrine. It is not: on the pinned
 * interpreter, with that same environment variable absent, `shutil.which`
 * returned a RELATIVE path to a planted file in the current directory. The
 * doctrine being mirrored is therefore the one make_cert.py STATES - resolve
 * the tool from PATH by name, never from a spelled absolute path - and not the
 * behaviour of the function it happens to call. That gap is filed as its own
 * finding rather than silently worked around here.
 *
 * WHAT THE RESOLVER DOES NOT DEFEND AGAINST, stated rather than implied: a PATH
 * whose own entries are attacker-controlled, and an absolute entry containing
 * parent-directory segments. Both require the attacker to already control the
 * environment the companion is launched with, at which point the interpreter is
 * not the weakest thing they can reach.
 *
 * A PATH MAY BE COMPUTED HERE, BUT NONE MAY BE SPELLED HERE. Every path this
 * module produces is built from what the caller supplied on the call; no
 * directory, drive, interpreter location or account-bearing string is written
 * into this file. The refusal lines quote none of it either - see above.
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

/** How long the wait has run was not a duration, so no budget can be applied. */
const REFUSE_UNKNOWN_ELAPSED = "REFUSE_UNKNOWN_ELAPSED";

/** There was no list of directories to search for the interpreter. */
const REFUSE_UNSEARCHABLE_PATH = "REFUSE_UNSEARCHABLE_PATH";

/** There was no list of the suffixes an executable may carry. */
const REFUSE_UNKNOWN_EXTENSIONS = "REFUSE_UNKNOWN_EXTENSIONS";

/** There was no way to ask whether a candidate is executable. */
const REFUSE_UNTESTABLE_CANDIDATE = "REFUSE_UNTESTABLE_CANDIDATE";

/** The search finished and found no interpreter. */
const REFUSE_NO_INTERPRETER = "REFUSE_NO_INTERPRETER";

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
const UNKNOWN_ELAPSED =
  "how long the companion has been waiting was not a duration, so the wait cannot be bounded";
const UNSEARCHABLE_PATH =
  "the companion was given no directories to search, so it will not resolve an interpreter";
const UNKNOWN_EXTENSIONS =
  "the companion was given no executable suffixes, so it will not resolve an interpreter";
const UNTESTABLE_CANDIDATE =
  "the companion was given no way to test a candidate, so it will not resolve an interpreter";
const NO_INTERPRETER =
  "no interpreter was found on the search path, so the companion will not start a dashboard";

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
    [REFUSE_UNKNOWN_ELAPSED, UNKNOWN_ELAPSED],
    [REFUSE_UNSEARCHABLE_PATH, UNSEARCHABLE_PATH],
    [REFUSE_UNKNOWN_EXTENSIONS, UNKNOWN_EXTENSIONS],
    [REFUSE_UNTESTABLE_CANDIDATE, UNTESTABLE_CANDIDATE],
    [REFUSE_NO_INTERPRETER, NO_INTERPRETER],
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
 * THIS IS NO LONGER THE ONLY BOUND ON THE WAIT, and reading it as one is what
 * went wrong before. `WAIT_BUDGET_MS` below bounds the wait by elapsed time,
 * and it is the bound that binds in the bad case; this one bounds the number of
 * probes. Both are applied, and either can end the wait.
 *
 * MEASURED. Cold start through the ACTUAL shipped path - electron, the same
 * transport, this module's own wait, a real spawn - answered on ATTEMPT 1 in
 * every sample: 0.462s, 0.464s and 0.531s over three runs, with an independent
 * probe outside electron putting the same start at 0.708s to 0.736s. Take the
 * slowest of those, roughly three quarters of a second, as the honest figure.
 *
 * MEASURED, AND A CORRECTION. An earlier version of this comment recorded
 * "2.217s minimum, 2.221s median, 2.227s maximum" for the same start and
 * reasoned from it. That does not reproduce, and the shape of it says why: a
 * 10ms spread across five samples is the signature of a fixed constant rather
 * than of a process starting, and PROBE_TIMEOUT_MS plus PROBE_INTERVAL_MS is
 * 2250ms - 29ms above the recorded median. Those samples were almost certainly
 * timing one whole missed probe and its gap, not a start. The margin that
 * comment described as four-and-a-half times at the old ceiling of 40 was in
 * fact roughly twenty times. The number it justified was not wrong; the
 * justification was, which is the more dangerous of the two to leave standing.
 *
 * ALSO A CORRECTION. This comment used to claim that "a dashboard that is never
 * going to come up fails its probes immediately rather than by timing out, so
 * the common bad case is the fast one". That is false - a probe to a port
 * nothing is listening on was measured at 2016ms, which is the full timeout -
 * and it was the assumption that made an attempt-count-only bound look
 * sufficient. It is deleted rather than replaced: the shape of a failing probe
 * is not measured here, and `WAIT_BUDGET_MS` is written so that it does not
 * need to be.
 *
 * JUDGED, NOT MEASURED - the value itself. 80 is kept because raising it is
 * harmless now that elapsed time is bounded independently, and because a probe
 * count is the wrong instrument for the bad case anyway. Against a measured
 * start of about three quarters of a second, 80 probes is margin of a size no
 * measurement supports or refutes; it is chosen for a machine under contention,
 * on the judgement that the two failure directions are not symmetric. Too tight
 * refuses a WORKING system on the operator's first double click, which reads as
 * a broken shortcut. Too loose no longer costs the operator a long wait,
 * because the wall-clock budget ends it first.
 *
 * WHAT THE MEASUREMENT DOES NOT COVER: no sample was cold in the operating
 * system cache sense, because the surface had already run in that session. A
 * first start after a reboot could be slower.
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

/**
 * How long the companion may wait in total, in milliseconds, however many
 * probes that turns out to be.
 *
 * WHY A SECOND BOUND EXISTS AT ALL. MEASURED at the shipped constants: a
 * listener that accepts a connection and never speaks makes every probe burn
 * the FULL timeout rather than failing fast, so the attempt ceiling alone
 * permits 80 probes of 2000ms plus 79 gaps of 250ms - 179.75s - and the
 * adoption probe before them adds another 2s. That is just over three minutes
 * in which the operator has double-clicked a shortcut and been shown no window,
 * no tray icon and no message. The attempt ceiling cannot fix this, because the
 * quantity it counts is not the quantity that hurts.
 *
 * JUDGED, NOT MEASURED - the value. 30s is roughly forty times the slowest
 * measured start (see PROBE_ATTEMPT_CEILING), and no measurement was taken of
 * how far a heavily loaded machine stretches that, so the multiple is a
 * judgement about contention and not a derived figure. Two things bound it from
 * either side:
 *
 *   - Below: it must not refuse a dashboard that is merely slow. At 30s a
 *     working system has room for many times its measured start, and the
 *     failure that costs an operator most is a WORKING system refused.
 *   - Above: about half a minute is as long as a double-clicked shortcut can
 *     show nothing before the operator concludes it is broken and double-clicks
 *     again. That second launch probes, finds nothing listening yet, and starts
 *     a SECOND dashboard onto a port the first is about to take. Bounding the
 *     wait below the operator's patience is what keeps that from happening.
 *
 * IT DOES NOT REPLACE THE ATTEMPT CEILING. Both are applied and either can end
 * the wait: this one binds when probes are slow, the ceiling when they are fast.
 */
const WAIT_BUDGET_MS = 30000;

// ---------------------------------------------------------------------------
// How the companion spawns
// ---------------------------------------------------------------------------

/** The interpreter switch that runs a module rather than a script file. */
const MODULE_FLAG = "-m";

/**
 * The interpreter, as a NAME and never as a location.
 *
 * OWNED HERE, THE WAY SERVER_MODULE IS. It used to be spelled in main.js, where
 * no test in either language can read it because that file imports electron.
 * A name is what BOOTSTRAP.md section 2.5 requires - never `py -3` - and a name
 * is all this is: where it lives is discovered at run time by
 * `resolveInterpreter`, from a PATH the caller supplies.
 */
const INTERPRETER_NAME = "python";

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
// Where the interpreter is - resolved, never guessed
// ---------------------------------------------------------------------------

/** How PATH and the executable-suffix list separate their entries on Windows. */
const LIST_SEPARATOR = ";";

/** What joins a directory to a file name. */
const DIRECTORY_SEPARATOR = "\\";

/**
 * What a directory has to look like before it is searched at ALL.
 *
 * Drive-rooted, or a UNC share. Everything else is discarded, and the two
 * near-misses are the point of writing it as a pattern rather than as a test
 * for a leading separator: `C:name` is rooted on a DRIVE but relative to that
 * drive's own current directory, and a leading separator with no drive is
 * relative to the current drive. Both read as absolute and neither is, and both
 * would reintroduce exactly the dependency on where the process is standing
 * that this whole function exists to remove.
 */
const ABSOLUTE_DIRECTORY = /^(?:[A-Za-z]:[\\/]|\\\\[^\\/])/;

/** A trailing separator on a PATH entry, which a hand-written PATH often has. */
const TRAILING_SEPARATORS = /[\\/]+$/;

/**
 * Split a raw list value into its usable entries, or null if there are none.
 *
 * @param {unknown} value The raw environment value.
 * @returns {Array<string>|null} The trimmed non-empty entries, or null.
 */
function listEntries(value) {
  if (typeof value !== "string") {
    return null;
  }
  const entries = value
    .split(LIST_SEPARATOR)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
  return entries.length > 0 ? entries : null;
}

/**
 * Find the interpreter, as an absolute path, searching PATH and only PATH.
 *
 * THE CURRENT DIRECTORY IS NEVER CONSULTED, and no relative PATH entry is
 * either. See this module's header for the measurement that makes that the
 * whole point of the function rather than a nicety.
 *
 * PURE, AND THE PROBE IS INJECTED FOR THAT REASON. Asking the filesystem
 * directly would mean importing it, which would end this module's independence
 * from a runtime and make the property above ungradable on a machine with no
 * interpreter installed. The caller supplies the question; this decides what to
 * ask it about, in what order, and what the answer means.
 *
 * ORDER IS DIRECTORY-MAJOR - every suffix in one directory before moving to the
 * next - which is the order Windows itself searches in. Getting it backwards
 * would let a suffix earlier in the list win from a directory later in PATH.
 *
 * A BARE NAME IS NEVER OFFERED. On Windows an extension-less file is not
 * launchable by the call that spawns it, so a candidate with no suffix could
 * only ever be a false positive.
 *
 * @param {object} [options]
 * @param {string} [options.pathValue] The raw PATH value.
 * @param {string} [options.pathExt] The raw executable-suffix list.
 * @param {function(string): boolean} [options.isExecutable] Whether a candidate
 *   path names something runnable. Called with absolute paths only.
 * @returns {string} An absolute path, or one of four named refusals.
 */
function resolveInterpreter(options) {
  const opts = optionsOf(options);

  const directories = listEntries(opts.pathValue);
  if (directories === null) {
    return REFUSE_UNSEARCHABLE_PATH;
  }

  // A suffix that does not begin with a separator dot cannot name an extension,
  // so it is dropped here rather than concatenated into a candidate that could
  // never match anything.
  const rawSuffixes = listEntries(opts.pathExt);
  const suffixes = rawSuffixes === null ? null : rawSuffixes.filter((s) => s.startsWith("."));
  if (suffixes === null || suffixes.length === 0) {
    return REFUSE_UNKNOWN_EXTENSIONS;
  }

  const isExecutable = opts.isExecutable;
  if (typeof isExecutable !== "function") {
    return REFUSE_UNTESTABLE_CANDIDATE;
  }

  for (const directory of directories) {
    // THE FILTER IS HERE AND NOT IN A PRIOR PASS, so that a directory which
    // fails it is skipped rather than repaired into something searchable.
    if (!ABSOLUTE_DIRECTORY.test(directory)) {
      continue;
    }
    const base = directory.replace(TRAILING_SEPARATORS, "") + DIRECTORY_SEPARATOR;
    for (const suffix of suffixes) {
      const candidate = base + INTERPRETER_NAME + suffix;
      if (isExecutable(candidate) === true) {
        return candidate;
      }
    }
  }

  // Searched, and nothing answered. A refusal rather than a name, so a caller
  // that spawned the return value without checking would spawn a word that
  // cannot resolve rather than silently running whatever is nearest.
  return REFUSE_NO_INTERPRETER;
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
 * True only for a real, non-negative duration in milliseconds.
 *
 * `Number.isFinite` does not coerce, so a numeric string, a boolean, null and
 * undefined are all excluded by it alone, as are NaN and both infinities. Zero
 * is ALLOWED - the first probe of a wait genuinely has elapsed nothing - and so
 * is a fraction, which is what a high-resolution clock yields. A negative
 * duration is a clock that went backwards, which is bookkeeping this module
 * will not reason from.
 */
function isDuration(value) {
  return Number.isFinite(value) && value >= 0;
}

/**
 * After one probe: load the window, wait and probe again, or stop waiting.
 *
 * ALL THREE INPUTS ARE VALIDATED BEFORE ANY IS USED. An attempt that is not a
 * count cannot be compared against the ceiling and mean anything, so a malformed
 * one refuses even when the probe was answered - a caller whose loop bookkeeping
 * is corrupt does not know how many attempts remain, and saying READY would hide
 * that. The attempt is checked first so that a caller repairing the loop is told
 * which of the three values to look at, and the elapsed time last because it is
 * the newest and the least likely to be the one confusing a reader.
 *
 * THE ELAPSED TIME IS REQUIRED, NOT OPTIONAL, and that is the point of it. A
 * bound a caller can omit is a bound that will be omitted; making it a refusal
 * means the wall-clock budget cannot be dropped by forgetting a field. It fails
 * CLOSED, because the caller ends its wait on any word that is neither READY
 * nor RETRY.
 *
 * AN ANSWER IS STILL AN ANSWER, at or beyond EITHER bound. The ceiling and the
 * budget bound how long the companion WAITS, not whether a reply counts, so
 * `answered` is read before either is compared. A dashboard that replied as the
 * budget expired has started, and throwing that away on a stopwatch would
 * refuse a working system.
 *
 * @param {object} [options]
 * @param {number} [options.attempt] Which probe just finished, counting from one.
 * @param {boolean} [options.answered] Whether the dashboard answered it.
 * @param {number} [options.elapsedMs] How long the wait has run in total.
 * @returns {string} READY, RETRY, GIVE_UP, or one of three refusals.
 */
function decideProbeOutcome(options) {
  const opts = optionsOf(options);
  const attempt = opts.attempt;
  const answered = opts.answered;
  const elapsedMs = opts.elapsedMs;

  // Number.isInteger already excludes NaN and both infinities, so neither needs
  // a separate test. The lower bound is one rather than zero: attempt zero names
  // a probe that never ran.
  if (!Number.isInteger(attempt) || attempt < 1) {
    return REFUSE_UNKNOWN_ATTEMPT;
  }
  if (!isAnswer(answered)) {
    return REFUSE_UNKNOWN_ANSWER;
  }
  if (!isDuration(elapsedMs)) {
    return REFUSE_UNKNOWN_ELAPSED;
  }

  if (answered) {
    return READY;
  }

  // THE BUDGET IS COMPARED BEFORE THE CEILING, because it is the bound that
  // binds in the case this pair exists for: probes that each burn a full
  // timeout reach the budget long before they reach the eightieth attempt.
  // `>=` for the same reason as below - the budget is the last instant a probe
  // may be made at, so reaching it ends the wait.
  if (elapsedMs >= WAIT_BUDGET_MS) {
    return GIVE_UP;
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
  INTERPRETER_NAME,
  LEAVE,
  MODULE_FLAG,
  NOT_A_REFUSAL,
  PROBE_ATTEMPT_CEILING,
  PROBE_INTERVAL_MS,
  PROBE_TIMEOUT_MS,
  READY,
  REFUSALS,
  REFUSE_NO_INTERPRETER,
  REFUSE_UNKNOWN_ANSWER,
  REFUSE_UNKNOWN_ATTEMPT,
  REFUSE_UNKNOWN_ELAPSED,
  REFUSE_UNKNOWN_EXTENSIONS,
  REFUSE_UNKNOWN_HEALTH,
  REFUSE_UNKNOWN_OWNERSHIP,
  REFUSE_UNSEARCHABLE_PATH,
  REFUSE_UNTESTABLE_CANDIDATE,
  RETRY,
  SERVER_MODULE,
  START,
  STOP,
  WAIT_BUDGET_MS,
  decideProbeOutcome,
  decideStart,
  decideStop,
  resolveInterpreter,
  serverArgv,
  supervisorRefusal,
};
