"use strict";

// CS-602 slice S3 - remembering the companion window across launches.
//
// THE DIRECTORY IS THE CALLER'S BUSINESS. This module is handed a directory and
// never works one out. It reads no environment variable, calls no app.getPath,
// and contains no path literal. Keeping that decision outside means the whole
// of this file runs against a scratch directory in CI, and means no absolute
// path under a user home can ever be baked into a tracked file (CLAUDE.md
// non-negotiable 3).
//
// THE SCHEMA IS INTEGERS AND BOOLEANS, WITH NO STRING FIELD ANYWHERE. That is
// not tidiness. A save file, a world name, a platform account id and a Windows
// account name are all personal data (CLAUDE.md non-negotiables 3 and 11), and
// a file that structurally cannot hold a string cannot leak any of them - not
// through a careless caller, not through a later feature, not through a
// debugging field somebody meant to remove. serialize() below rebuilds the
// payload key by key from a fixed list, so an extra field a caller passes in is
// dropped rather than persisted.
//
// WRITES ARE ATOMIC, AND THE CLAIM HOLDS FOR MANY WRITERS (CLAUDE.md
// non-negotiable 5). The payload is written to a staging sibling, flushed, and
// renamed into place. A reader therefore sees either the previous file or the
// new one, never a half written one.
//
// CS-911 - THE DECISION WAS TO WIDEN THE IMPLEMENTATION, NOT TO NARROW THE
// CLAIM. Until this item the staging file had a FIXED name and was opened
// truncating, so the paragraph above was true of one writer and false of two.
// MEASURED against this module: writer A stages, writer B opens the same fixed
// path truncating, writer A renames, and what lands over a good state file is
// ZERO BYTES. In the same arms a large minority of concurrent saves also failed
// outright with ENOENT, each writer's rename finding that another had already
// taken its partial. NO RATIO IS SPELLED HERE ON PURPOSE: it is a load-dependent
// race count, an earlier draft of this comment gave 91 of 240, and five
// re-measurements on one machine observed 60, 68, 74, 76 and 81. A number no
// guard can check and no run reproduces is exactly the hardcoded measurement
// CLAUDE.md section 4 forbids; the ARM is the record, not this sentence. Narrowing the header to "one writer only" was the cheaper option
// and was rejected: a single-writer atomicity guarantee is not what
// non-negotiable 5 asks for, and the single-instance lock that removes today's
// only known second writer lives in another file and can be removed there,
// which would silently un-fix this one. A guarantee that holds only while a
// caller elsewhere keeps behaving is not a guarantee this module can state.
//
// SO EVERY STAGE GETS ITS OWN FILENAME. Two writers stage into two different
// files and race only at the rename, where the loser is superseded by a whole,
// self-consistent payload from the winner. What is deliberately NOT offered is
// any ordering between concurrent writers: save() takes a complete state rather
// than mutating one it read, so last-rename-wins loses no update that was not
// already stale.
//
// The bounded rename retry began as the idiom used at
// clockspeed/save/workdir.py::_replace_with_retry - on Windows a scanner or an
// indexer can hold a handle on a file closed microseconds ago, and the rename
// then fails with a sharing violation that a retry turns into a completed
// write. CS-1124 bounds it here by a deadline rather than an attempt count;
// the reason and the CI measurement sit beside RENAME_DEADLINE_MS below.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

/** Bumped only when the meaning of a field changes. A mismatch is a reset. */
const SCHEMA_VERSION = 1;

const STATE_FILENAME = "window-state.json";

// A staging file is named "<state file>.<unique>.partial". THE UNIQUE SEGMENT
// IS THE WHOLE OF CS-911 - a fixed name is a shared mutable resource, and two
// writers holding one is how a zero-byte file came to be published over a good
// one. STATE_FILENAME itself does not carry the separating dot, so the real
// file can never be taken for a staging file by the sweep below.
const PARTIAL_PREFIX = `${STATE_FILENAME}.`;
const PARTIAL_SUFFIX = ".partial";

// A stage abandoned by a killed process is never renamed and never read, and
// under a unique name one would accumulate per crash, forever, in the
// operator's userData directory. A successful commit therefore clears siblings
// old enough that no live writer could still own one. The threshold is more
// than twenty times the longest a stage can legitimately take - one fsync plus
// at most RENAME_DEADLINE_MS of rename retry - so sweeping a stage still in
// flight is not a window this reaches.
const PARTIAL_STALE_MS = 60 * 1000;

/** Every key the file may contain, in the order it is written. */
const STATE_KEYS = Object.freeze(["schema", "x", "y", "width", "height", "alwaysOnTop"]);

/** The four that describe the rectangle. */
const GEOMETRY_KEYS = Object.freeze(["x", "y", "width", "height"]);

// A window smaller than this is not usable, and a state file asking for one is
// corrupt rather than merely unusual.
const MIN_WIDTH = 480;
const MIN_HEIGHT = 360;

// An absolute ceiling, independent of any attached display. A caller that knows
// its largest work area should pass maxWidth and maxHeight as well - as plain
// numbers, because this module never learns what a display is.
const MAX_DIMENSION = 30000;

// Coordinates may be negative: a monitor arranged left of or above the primary
// produces them routinely, so a negative x is ordinary and must survive. What
// is not ordinary is a coordinate no desktop could produce, which is how an
// overflowed or garbage value shows itself.
const MAX_COORDINATE = 100000;

const DEFAULTS = Object.freeze({
  schema: SCHEMA_VERSION,
  x: 0,
  y: 0,
  width: 1100,
  height: 800,
  alwaysOnTop: false,
});

// CS-1124 - THE RETRY IS BOUNDED BY TIME, NOT BY AN ATTEMPT COUNT. The loop
// this replaces made five attempts with a linear 50ms pause, so its last
// attempt came about 500ms after the first refusal and it then slept a further
// 250ms before giving up. MEASURED on windows-latest CI: that budget lost to a
// held handle on 2 of 240 concurrent saves in the 768f2b8 tier2 run and 1 of
// 240 in scheduled run 35201300783, each as "save failed with EPERM". How long
// the runner's holder actually keeps the file is NOT measured - only that it
// sometimes outlasts half a second. The deadline is therefore four times the
// window that lost, and the backoff starts short and doubles to a cap, so a
// brief hold costs milliseconds while a long one is still probed every
// RENAME_BACKOFF_CAP_MS until the deadline. A rename still refused at the
// deadline raises its own error: a genuinely stuck file fails loudly, and
// nothing ever falls back to writing the state file in place.
//
// THE COST IS BOUNDED AND PAID ONLY ON CONTENTION. save() is synchronous, so a
// hold that never ends blocks its caller for the deadline and then surfaces as
// a failed save, which main.js reports and swallows. TWO BUDGETS, because the
// callers differ. The debounced save runs while the window is live and gets
// RENAME_DEADLINE_MS. The two close paths - hide, and quit - run while the
// operator waits on a window that has not yet gone, and get
// RENAME_CLOSE_DEADLINE_MS: the old loop's own attempt window, which keeps a
// failing close inside the 750ms that loop already blocked it for.
//
// THE DEADLINE IS READ OFF A MONOTONIC CLOCK. MEASURED by the CS-1124
// adversary: read off Date.now, a wall clock stepped back 5s during a held
// rename stretched a 2000ms deadline to about 7s.
const RENAME_DEADLINE_MS = 2000;
const RENAME_CLOSE_DEADLINE_MS = 500;
const RENAME_BACKOFF_FIRST_MS = 5;
const RENAME_BACKOFF_CAP_MS = 200;

/** Milliseconds on a clock that a wall-clock step cannot move. */
function monotonicMs() {
  return performance.now();
}

/** The caller's rename budget, or the background default. Refuses a bad one loudly. */
function renameDeadlineFrom(options) {
  if (options === undefined || options === null || !Object.hasOwn(options, "renameDeadlineMs")) {
    return RENAME_DEADLINE_MS;
  }
  const value = options.renameDeadlineMs;
  if (!Number.isInteger(value) || value < 0 || value > RENAME_DEADLINE_MS) {
    throw new RangeError(`renameDeadlineMs must be an integer from 0 to ${RENAME_DEADLINE_MS}`);
  }
  return value;
}

// Error codes that mean "somebody else is holding this file right now" and are
// worth waiting out. Anything else is a real fault and is raised immediately
// rather than being retried into a slower failure.
//
// ENOENT IS DELIBERATELY NOT ON THIS LIST, and CS-911 is why it had to be
// decided rather than left unstated. Under the old fixed-name staging it was
// the DOMINANT failure - a large minority of concurrent saves, varying by load -
// because a second writer renamed the first writer's stage away before the first
// could commit. Adding
// it here would have been the wrong repair twice over: a rename whose source
// does not exist does not become possible by waiting, so every retry is dead
// time before the same failure; and it would have converted a corruption bug
// into a latency bug while still publishing zero bytes. The unique staging
// name removes the cause instead. What ENOENT now means is that something
// outside this module deleted a stage mid-write, which the caller must see
// rather than sit through.
const TRANSIENT_CODES = new Set(["EPERM", "EBUSY", "EACCES"]);

/**
 * Block the calling thread briefly.
 *
 * fs.renameSync is synchronous, so the retry pause has to be too. Atomics.wait
 * on a throwaway buffer is the way to do that without a dependency and without
 * a busy loop burning a core.
 */
function sleepSync(milliseconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, milliseconds);
}

/**
 * Rename, waiting out a transient Windows sharing violation until a deadline.
 *
 * Always makes at least one attempt, never sleeps past the deadline, and makes
 * a final attempt at it - so the time spent is the deadline plus at most one
 * rename, and the error raised is the last one the rename itself reported.
 *
 * superseded() is asked after every pause and before the next attempt. When it
 * answers true a newer payload has already been published while this one
 * waited, and the rename is abandoned rather than put over it.
 *
 * @returns {boolean} true once published, false when abandoned as superseded.
 */
function renameWithRetry(from, to, deadlineMs, superseded) {
  const deadline = monotonicMs() + deadlineMs;
  let pause = RENAME_BACKOFF_FIRST_MS;
  for (;;) {
    try {
      fs.renameSync(from, to);
      return true;
    } catch (err) {
      if (!TRANSIENT_CODES.has(err.code)) {
        throw err;
      }
      const remaining = deadline - monotonicMs();
      if (remaining <= 0) {
        throw err;
      }
      sleepSync(Math.min(pause, remaining));
      pause = Math.min(pause * 2, RENAME_BACKOFF_CAP_MS);
      if (superseded()) {
        return false;
      }
    }
  }
}

/** A usable directory argument, or null. */
function directoryOf(dir) {
  return typeof dir === "string" && dir.length > 0 ? dir : null;
}

/** A monotonic tiebreak, so two stages from ONE process cannot collide either. */
let partialSequence = 0;

/** True for a staging filename this module could have made, and only for those. */
function isPartialFilename(name) {
  return (
    typeof name === "string" &&
    name.length > PARTIAL_PREFIX.length + PARTIAL_SUFFIX.length &&
    name.startsWith(PARTIAL_PREFIX) &&
    name.endsWith(PARTIAL_SUFFIX)
  );
}

/**
 * A staging path no other writer can be holding.
 *
 * Random bytes carry the guarantee ACROSS processes, where a counter cannot -
 * two processes both start theirs at zero. The counter carries it WITHIN one
 * process, where it is exact rather than merely overwhelmingly likely. Neither
 * alone covers both cases, which is why both are here.
 */
function partialPathFor(directory) {
  partialSequence += 1;
  const unique = `${partialSequence.toString(36)}-${INSTANCE_TOKEN}-${crypto.randomBytes(8).toString("hex")}`;
  return path.join(directory, `${PARTIAL_PREFIX}${unique}${PARTIAL_SUFFIX}`);
}

// CS-1124 - AN OLDER SAVE MUST NOT LAND OVER A NEWER ONE. The sequence above
// already orders every stage this module instance makes, so it doubles as a
// generation: the token below marks a stage as this instance's own, and
// publishedSequence is the newest generation this instance has published. A
// stage older than that is abandoned rather than committed.
//
// ACROSS PROCESSES THERE IS NO SHARED SEQUENCE. In the shipped app the
// single-instance lock in main.js means there is no second process to race;
// the cross-process case is still narrowed, not closed, by the retry-time check
// in commitPartial, which abandons a stage when the published file was
// REPLACED while this commit waited AND the replacement was staged later.
const INSTANCE_TOKEN = crypto.randomBytes(6).toString("hex");
let publishedSequence = 0;

/** The generation of a stage this module instance made, or null for any other. */
function sequenceOf(partialPath) {
  const name = path.basename(partialPath);
  const parts = name.slice(PARTIAL_PREFIX.length, name.length - PARTIAL_SUFFIX.length).split("-");
  if (parts.length !== 3 || parts[1] !== INSTANCE_TOKEN || !/^[0-9a-z]+$/.test(parts[0])) {
    return null;
  }
  return parseInt(parts[0], 36);
}

/** What identifies the published file right now, or null if there is none. */
function identityOf(target) {
  try {
    const stat = fs.statSync(target);
    return { ino: stat.ino, size: stat.size, mtimeMs: stat.mtimeMs, ctimeMs: stat.ctimeMs };
  } catch {
    return null;
  }
}

function sameIdentity(a, b) {
  return (
    a !== null && b !== null &&
    a.ino === b.ino && a.size === b.size && a.mtimeMs === b.mtimeMs && a.ctimeMs === b.ctimeMs
  );
}

/** Remove a stage this commit is giving up on. A failure here changes nothing. */
function discardStage(partialPath) {
  try {
    fs.unlinkSync(partialPath);
  } catch {
    // Already gone, or held. The minute-old sweep is the backstop.
  }
}

/**
 * Remove staging files old enough that no live writer could still own one.
 *
 * Housekeeping, and nothing more. It runs only AFTER a payload is published,
 * and every fault it meets is swallowed - a directory that cannot be listed, a
 * file another writer swept first, a file still held open. None of those is a
 * reason to report a write that already succeeded as failed.
 */
function sweepStalePartials(directory) {
  let names;
  try {
    names = fs.readdirSync(directory);
  } catch {
    return;
  }
  const cutoff = Date.now() - PARTIAL_STALE_MS;
  for (const name of names) {
    if (!isPartialFilename(name)) {
      continue;
    }
    try {
      const candidate = path.join(directory, name);
      if (fs.statSync(candidate).mtimeMs <= cutoff) {
        fs.unlinkSync(candidate);
      }
    } catch {
      // Gone already, or held by a writer that is still using it. Either way it
      // is not this write's business.
    }
  }
}

/** A fresh copy of the defaults. Never the frozen original, which callers mutate. */
function defaultsFrom(options) {
  const supplied = options && typeof options === "object" ? options.defaults : null;
  const base = supplied && typeof supplied === "object" && !Array.isArray(supplied) ? supplied : DEFAULTS;
  return {
    schema: SCHEMA_VERSION,
    x: Number.isInteger(base.x) ? base.x : DEFAULTS.x,
    y: Number.isInteger(base.y) ? base.y : DEFAULTS.y,
    width: Number.isInteger(base.width) ? base.width : DEFAULTS.width,
    height: Number.isInteger(base.height) ? base.height : DEFAULTS.height,
    alwaysOnTop: base.alwaysOnTop === true,
  };
}

/**
 * Rebuild the payload from a fixed key list.
 *
 * Structural, not advisory: an unknown key a caller passes in has nowhere to go
 * and is dropped, which is what keeps a string out of the file for good.
 */
function serialize(input) {
  const source = input !== null && typeof input === "object" && !Array.isArray(input) ? input : {};
  const out = { schema: SCHEMA_VERSION };
  for (const key of GEOMETRY_KEYS) {
    const value = Object.hasOwn(source, key) ? source[key] : DEFAULTS[key];
    out[key] = Number.isInteger(value) ? value : DEFAULTS[key];
  }
  // Strict identity, never truthiness. "false" and 0 and null must all land on
  // false rather than on whatever a loose check would make of them.
  out.alwaysOnTop = Object.hasOwn(source, "alwaysOnTop") && source.alwaysOnTop === true;
  return out;
}

/**
 * Validate a parsed payload into a state object, or report why it cannot be.
 *
 * NEVER Object.assign, and never a spread of the parsed payload onto defaults.
 *
 * MEASURED on node v24.15.0: JSON.parse('{"__proto__":{"polluted":1}}') creates
 * an OWN "__proto__" data property and leaves the parsed object's real
 * prototype alone. Object.assign({}, parsed) then copies that key, which
 * invokes the __proto__ setter on the TARGET and replaces the target's
 * prototype wholesale, so the returned object silently inherits every key the
 * attacker put there. Reading each field explicitly by name, off a fixed list,
 * cannot do that: "__proto__" is not on the list, so it is never read and never
 * copied, and the object handed back is an ordinary literal.
 */
function validate(parsed, defaults, options) {
  const faults = [];

  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { state: defaults, restored: false, faults: ["the state file did not contain a JSON object"] };
  }

  const schema = Object.hasOwn(parsed, "schema") ? parsed.schema : undefined;
  if (schema !== SCHEMA_VERSION) {
    return {
      state: defaults,
      restored: false,
      faults: [`schema was ${JSON.stringify(schema)}, expected ${SCHEMA_VERSION}`],
    };
  }

  const geometry = {};
  for (const key of GEOMETRY_KEYS) {
    const value = Object.hasOwn(parsed, key) ? parsed[key] : undefined;
    // Number.isInteger rejects undefined, null, a string, NaN and both
    // infinities in one test, so each of those faults is caught here.
    if (!Number.isInteger(value)) {
      faults.push(`${key} was not an integer`);
      continue;
    }
    if (Math.abs(value) > MAX_COORDINATE) {
      faults.push(`${key} was outside the plausible desktop range`);
      continue;
    }
    geometry[key] = value;
  }

  if (faults.length === 0) {
    const maxWidth = options && Number.isInteger(options.maxWidth) ? options.maxWidth : MAX_DIMENSION;
    const maxHeight = options && Number.isInteger(options.maxHeight) ? options.maxHeight : MAX_DIMENSION;
    if (geometry.width < MIN_WIDTH || geometry.height < MIN_HEIGHT) {
      faults.push("width or height was below the usable floor");
    }
    if (geometry.width > Math.min(maxWidth, MAX_DIMENSION) || geometry.height > Math.min(maxHeight, MAX_DIMENSION)) {
      faults.push("width or height was larger than the largest work area");
    }
  }

  if (faults.length > 0) {
    // Geometry is taken whole or not at all. Half a remembered rectangle -
    // last time's width at this launch's default position - is a window in a
    // place it has never actually been.
    return { state: defaults, restored: false, faults };
  }

  // A junk alwaysOnTop does NOT discard a good rectangle. It falls back to
  // false, and false specifically: a window that silently pins itself above
  // everything else because its state file was garbage is a bug the operator
  // would have to hunt, and the safe direction is unmistakably down.
  const rawOnTop = Object.hasOwn(parsed, "alwaysOnTop") ? parsed.alwaysOnTop : undefined;
  const softFaults = [];
  if (typeof rawOnTop !== "boolean") {
    softFaults.push("alwaysOnTop was not a boolean and fell back to false");
  }

  return {
    state: {
      schema: SCHEMA_VERSION,
      x: geometry.x,
      y: geometry.y,
      width: geometry.width,
      height: geometry.height,
      alwaysOnTop: rawOnTop === true,
    },
    restored: true,
    faults: softFaults,
  };
}

/**
 * Read the remembered window state, reporting what was wrong with it.
 *
 * @param {string} dir Directory holding the state file. Chosen by the caller.
 * @param {object} [options] Optional `defaults`, `maxWidth`, `maxHeight`.
 * @returns {{state: object, restored: boolean, faults: Array<string>}}
 */
function inspect(dir, options) {
  const defaults = defaultsFrom(options);
  const directory = directoryOf(dir);
  if (directory === null) {
    return { state: defaults, restored: false, faults: ["no state directory was supplied"] };
  }

  let text;
  try {
    // The .partial sibling is never read. An abandoned partial from a killed
    // write is left strictly alone, so a process that died mid-save loses the
    // new state rather than corrupting the old.
    text = fs.readFileSync(path.join(directory, STATE_FILENAME), "utf8");
  } catch (err) {
    return { state: defaults, restored: false, faults: [`the state file could not be read (${err.code || "unknown"})`] };
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    return { state: defaults, restored: false, faults: ["the state file was not valid JSON"] };
  }

  return validate(parsed, defaults, options);
}

/**
 * Read the remembered window state. NEVER throws - a corrupt file yields the
 * defaults, because failing to open the window is a far worse outcome than
 * opening it somewhere unremarkable.
 */
function load(dir, options) {
  try {
    return inspect(dir, options).state;
  } catch {
    // Belt and braces. inspect is written not to throw, but load is the
    // function the shell's startup path depends on, and an unforeseen fault
    // here must not be what stops the window appearing.
    return defaultsFrom(options);
  }
}

/**
 * Write the payload to a staging sibling and flush it to disk.
 *
 * Half of an atomic write, exposed on its own so that the intermediate state is
 * observable - a test can assert the stage exists and the real file does not,
 * and can simulate a killed process by simply never committing.
 *
 * @returns {string} The staging path, which the caller must hand to
 *   commitPartial. It is DIFFERENT on every call, and that is the point.
 */
function writePartial(dir, state) {
  const directory = directoryOf(dir);
  if (directory === null) {
    throw new Error("no state directory was supplied");
  }
  fs.mkdirSync(directory, { recursive: true });

  const payload = `${JSON.stringify(serialize(state), null, 2)}\n`;
  const target = partialPathFor(directory);
  // "wx" rather than "w": exclusive create. A name collision should be
  // impossible, and if the unique segment ever stopped being unique this fails
  // loudly here instead of silently truncating another writer's staged payload,
  // which is precisely the fault CS-911 was filed on.
  const handle = fs.openSync(target, "wx");
  try {
    fs.writeFileSync(handle, payload, "utf8");
    // Flushed before the rename, so the rename publishes bytes that are
    // actually on the disk rather than bytes still sitting in a cache.
    fs.fsyncSync(handle);
  } finally {
    fs.closeSync(handle);
  }
  return target;
}

/**
 * Rename a staged file over the real one. The other half.
 *
 * @param {string} dir The directory writePartial was given.
 * @param {string} partialPath Exactly what that writePartial call returned.
 * @param {object} [options] Optional `renameDeadlineMs`, from 0 to
 *   RENAME_DEADLINE_MS. The close paths pass RENAME_CLOSE_DEADLINE_MS.
 * @returns {string|null} The published path, or null when the stage was
 *   abandoned because a newer payload had already been published.
 */
function commitPartial(dir, partialPath, options) {
  const directory = directoryOf(dir);
  if (directory === null) {
    throw new Error("no state directory was supplied");
  }
  // REQUIRED, and never defaulted to a well-known name. A default would put the
  // fixed shared name back one layer up, where it would be harder to see.
  if (typeof partialPath !== "string" || partialPath.length === 0) {
    throw new Error("no staged file was supplied - pass back what writePartial returned");
  }
  // And it must be a staging file of this module's own shape, sitting in the
  // directory this call names. Accepting an arbitrary path would let a caller
  // rename anything at all over the state file - a hole the fixed name did not
  // have, and one this item must not open while closing another.
  if (
    !isPartialFilename(path.basename(partialPath)) ||
    path.dirname(path.resolve(partialPath)) !== path.resolve(directory)
  ) {
    throw new Error("the staged file does not belong to this state directory");
  }

  const deadlineMs = renameDeadlineFrom(options);
  const target = path.join(directory, STATE_FILENAME);

  const sequence = sequenceOf(partialPath);
  const olderThanPublished = () => sequence !== null && sequence < publishedSequence;
  if (olderThanPublished()) {
    discardStage(partialPath);
    return null;
  }

  // The retry-time check, for a writer this instance has no sequence for. It
  // asks whether the published file was REPLACED since this commit began, and
  // only then whether the replacement is newer than this stage. A timestamp
  // alone is never enough: a wall clock stepped back after a save leaves a
  // state file that looks newer than every stage to come, and comparing
  // against that unconditionally would abandon them all.
  let stagedMtimeMs = null;
  try {
    stagedMtimeMs = fs.statSync(partialPath).mtimeMs;
  } catch {
    // The rename below reports a missing stage in its own words.
  }
  const before = identityOf(target);
  const superseded = () => {
    if (olderThanPublished()) {
      return true;
    }
    const now = identityOf(target);
    if (now === null || sameIdentity(now, before)) {
      return false;
    }
    return stagedMtimeMs !== null && now.mtimeMs > stagedMtimeMs;
  };

  let published;
  try {
    published = renameWithRetry(partialPath, target, deadlineMs, superseded);
  } catch (err) {
    // A save that failed leaves nothing behind to be swept a minute later.
    discardStage(partialPath);
    throw err;
  }
  if (!published) {
    discardStage(partialPath);
    return null;
  }
  if (sequence !== null && sequence > publishedSequence) {
    publishedSequence = sequence;
  }
  // Only once the payload is published. A sweep that ran first could delete a
  // stage this call is about to need.
  sweepStalePartials(directory);
  return target;
}

/**
 * Persist the window state atomically.
 *
 * @param {object} [options] Optional `renameDeadlineMs`; see commitPartial.
 * @returns {string|null} As commitPartial.
 */
function save(dir, state, options) {
  // Validated BEFORE staging, so a bad budget writes nothing at all.
  renameDeadlineFrom(options);
  return commitPartial(dir, writePartial(dir, state), options);
}

module.exports = {
  load,
  inspect,
  save,
  writePartial,
  commitPartial,
  serialize,
  isPartialFilename,
  STATE_KEYS,
  GEOMETRY_KEYS,
  STATE_FILENAME,
  // No PARTIAL_FILENAME. There is no longer one staging filename to name, and
  // exporting a representative one would invite a caller to build the fixed
  // shared path this item exists to remove.
  PARTIAL_PREFIX,
  PARTIAL_SUFFIX,
  PARTIAL_STALE_MS,
  RENAME_DEADLINE_MS,
  RENAME_CLOSE_DEADLINE_MS,
  SCHEMA_VERSION,
  DEFAULTS,
  MIN_WIDTH,
  MIN_HEIGHT,
  MAX_DIMENSION,
  MAX_COORDINATE,
};
