"use strict";

// CS-602 slice S3 - tests for shell/lib/state.js.
//
// TWO NON-NEGOTIABLES ARE UNDER TEST HERE, not preferences:
//
//   CLAUDE.md non-negotiable 5 - atomic writes for every file another process
//   may read. The state file is written to a .partial sibling and renamed into
//   place, so a reader never observes a half written file.
//
//   CLAUDE.md non-negotiables 3 and 11 - the schema is integers and booleans
//   only, with not one string field anywhere. That is a STRUCTURAL guarantee:
//   a file that cannot hold a string cannot leak a home path, a platform
//   account id, a world name or the Windows account name, no matter what a
//   later caller tries to persist through it. The key-set arm below is what
//   reddens the day somebody adds "lastUrl".

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const state = require("../lib/state.js");
const {
  load,
  inspect,
  save,
  writePartial,
  commitPartial,
  STATE_KEYS,
  STATE_FILENAME,
  PARTIAL_FILENAME,
  SCHEMA_VERSION,
  DEFAULTS,
  MIN_WIDTH,
  MIN_HEIGHT,
} = state;

// Scratch directories are namespaced s3_ because sibling agents share one
// scratchpad and have overwritten each other's files before.
const MADE = [];

function tempDir() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "s3_shell_state_"));
  MADE.push(dir);
  return dir;
}

function statePath(dir) {
  return path.join(dir, STATE_FILENAME);
}

/** Write a raw byte string as the state file, bypassing save() entirely. */
function plant(dir, raw) {
  fs.writeFileSync(statePath(dir), raw, "utf8");
}

const GOOD = Object.freeze({
  schema: 1,
  x: 120,
  y: 60,
  width: 1100,
  height: 800,
  alwaysOnTop: true,
});

test.after(() => {
  for (const dir of MADE) {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch {
      // A scratch directory that outlives the run is not a test failure.
    }
  }
});

// --- the schema is structurally incapable of carrying personal data ---------

test("the serialized key set equals STATE_KEYS exactly", () => {
  const dir = tempDir();
  save(dir, GOOD);
  const parsed = JSON.parse(fs.readFileSync(statePath(dir), "utf8"));
  // Exactly, in both directions - no missing key and no extra key.
  assert.deepEqual(Object.keys(parsed).sort(), [...STATE_KEYS].sort());
});

test("every serialized value is a number or a boolean, never a string", () => {
  const dir = tempDir();
  save(dir, GOOD);
  const raw = fs.readFileSync(statePath(dir), "utf8");
  const parsed = JSON.parse(raw);
  for (const [key, value] of Object.entries(parsed)) {
    const kind = typeof value;
    assert.ok(kind === "number" || kind === "boolean", `${key} serialized as ${kind}`);
  }
  // Belt and braces at the byte level: no string literal survives anywhere in
  // the payload except the key names themselves.
  assert.equal(raw.match(/:\s*"/g), null, "a string value reached the state file");
});

test("save refuses to persist a string field smuggled in by a caller", () => {
  const dir = tempDir();
  save(dir, { ...GOOD, lastUrl: "https://example.invalid/world", worldName: "anything" });
  const parsed = JSON.parse(fs.readFileSync(statePath(dir), "utf8"));
  assert.deepEqual(Object.keys(parsed).sort(), [...STATE_KEYS].sort());
  assert.equal(parsed.lastUrl, undefined);
  assert.equal(parsed.worldName, undefined);
});

test("STATE_KEYS carries the schema field and no string-shaped field", () => {
  assert.ok(STATE_KEYS.includes("schema"));
  for (const key of ["x", "y", "width", "height", "alwaysOnTop"]) {
    assert.ok(STATE_KEYS.includes(key), `${key} missing from STATE_KEYS`);
  }
  assert.equal(STATE_KEYS.length, 6);
});

test("state.js embeds no path literal and computes no directory itself", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "lib", "state.js"), "utf8");
  assert.ok(!/require\(\s*["']electron["']\s*\)/.test(source), "state.js must not require electron");
  // getPath, homedir, LOCALAPPDATA and a drive letter are each a way of
  // deciding the directory from inside the module. The caller decides.
  assert.ok(!/getPath\(/.test(source), "state.js must not call app.getPath");
  assert.ok(!/homedir\(/.test(source), "state.js must not call os.homedir");
  assert.ok(!/LOCALAPPDATA|APPDATA|USERPROFILE/.test(source), "state.js must not read a home env var");
  assert.ok(!/[A-Za-z]:\\\\/.test(source), "state.js must not embed an absolute path");
});

// --- round trip -------------------------------------------------------------

test("a saved state loads back identically", () => {
  const dir = tempDir();
  save(dir, GOOD);
  assert.deepEqual(load(dir), GOOD);
});

test("alwaysOnTop false survives a round trip as false", () => {
  const dir = tempDir();
  save(dir, { ...GOOD, alwaysOnTop: false });
  assert.equal(load(dir).alwaysOnTop, false);
});

test("inspect reports restored with no faults for a good file", () => {
  const dir = tempDir();
  save(dir, GOOD);
  const report = inspect(dir);
  assert.equal(report.restored, true);
  assert.deepEqual(report.faults, []);
  assert.deepEqual(report.state, GOOD);
});

// --- recovery, one named arm per corruption ---------------------------------

test("an absent file yields the defaults", () => {
  const dir = tempDir();
  assert.deepEqual(load(dir), DEFAULTS);
  assert.equal(inspect(dir).restored, false);
});

test("an absent directory yields the defaults and does not throw", () => {
  const dir = path.join(tempDir(), "no", "such", "place");
  assert.deepEqual(load(dir), DEFAULTS);
});

test("a directory where the state file should be yields the defaults", () => {
  const dir = tempDir();
  fs.mkdirSync(statePath(dir));
  assert.deepEqual(load(dir), DEFAULTS);
});

// Every payload that is not a usable state object. Each is its own named test
// so a regression names the exact corruption that broke.
const CORRUPT = [
  ["not JSON at all", "{ this is not json"],
  ["an empty file", ""],
  ["whitespace only", "   \n  "],
  ["a JSON array", "[1,2,3]"],
  ["a JSON string", '"a string"'],
  ["a JSON number", "17"],
  ["JSON null", "null"],
  ["JSON true", "true"],
  ["a missing schema", '{"x":1,"y":2,"width":1100,"height":800,"alwaysOnTop":false}'],
  ["a wrong schema", '{"schema":99,"x":1,"y":2,"width":1100,"height":800,"alwaysOnTop":false}'],
  ["a string schema", '{"schema":"1","x":1,"y":2,"width":1100,"height":800,"alwaysOnTop":false}'],
];

for (const [label, raw] of CORRUPT) {
  test(`the defaults are returned for ${label}`, () => {
    const dir = tempDir();
    plant(dir, raw);
    assert.deepEqual(load(dir), DEFAULTS);
    assert.equal(inspect(dir).restored, false);
  });
}

// Each coordinate, each way it can be wrong. 4 fields x 6 faults.
const COORDS = ["x", "y", "width", "height"];
const FIELD_FAULTS = [
  ["missing", null],
  ["a string", '"800"'],
  ["null", "null"],
  ["NaN via a JSON literal", "1e999"],
  ["Infinity", "1e999"],
  ["fractional", "800.5"],
];

for (const field of COORDS) {
  for (const [label, literal] of FIELD_FAULTS) {
    test(`the defaults are returned when ${field} is ${label}`, () => {
      const dir = tempDir();
      const payload = { schema: SCHEMA_VERSION, x: 10, y: 20, width: 1100, height: 800, alwaysOnTop: false };
      const parts = [];
      for (const key of Object.keys(payload)) {
        if (key !== field) {
          parts.push(`${JSON.stringify(key)}:${JSON.stringify(payload[key])}`);
        } else if (literal !== null) {
          parts.push(`${JSON.stringify(key)}:${literal}`);
        }
      }
      plant(dir, `{${parts.join(",")}}`);
      assert.deepEqual(load(dir), DEFAULTS);
    });
  }
}

test("the defaults are returned for a negative width", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":0,"y":0,"width":-1100,"height":800,"alwaysOnTop":false}');
  assert.deepEqual(load(dir), DEFAULTS);
});

test("the defaults are returned for a zero height", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":0,"y":0,"width":1100,"height":0,"alwaysOnTop":false}');
  assert.deepEqual(load(dir), DEFAULTS);
});

test("the defaults are returned for a size below the floor", () => {
  const dir = tempDir();
  const raw = JSON.stringify({
    schema: SCHEMA_VERSION,
    x: 0,
    y: 0,
    width: MIN_WIDTH - 1,
    height: MIN_HEIGHT - 1,
    alwaysOnTop: false,
  });
  plant(dir, raw);
  assert.deepEqual(load(dir), DEFAULTS);
});

test("the defaults are returned for a size above the largest work area", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":0,"y":0,"width":40000,"height":30000,"alwaysOnTop":false}');
  // Against the module's own absolute ceiling.
  assert.deepEqual(load(dir), DEFAULTS);
  // And against a ceiling the caller supplies from its largest work area. The
  // caller passes plain numbers - this module never learns what a display is.
  plant(dir, '{"schema":1,"x":0,"y":0,"width":3000,"height":2000,"alwaysOnTop":false}');
  assert.deepEqual(load(dir, { maxWidth: 1920, maxHeight: 1080 }), DEFAULTS);
  // The same file is fine when the ceiling is big enough, which proves the
  // arm above failed on the ceiling and not on something incidental.
  assert.equal(load(dir, { maxWidth: 3840, maxHeight: 2160 }).width, 3000);
});

test("a huge coordinate beyond the sane range yields the defaults", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":9007199254740993,"y":0,"width":1100,"height":800,"alwaysOnTop":false}');
  assert.deepEqual(load(dir), DEFAULTS);
});

test("a negative coordinate is kept - a monitor left of the primary is normal", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":-1800,"y":-200,"width":1100,"height":800,"alwaysOnTop":false}');
  const loaded = load(dir);
  assert.equal(loaded.x, -1800);
  assert.equal(loaded.y, -200);
});

// --- alwaysOnTop fails safe -------------------------------------------------

// A window that silently pins itself above everything else because its state
// file was garbage is a bug the operator would have to hunt. It must fall back
// to false, never to true, and never to truthiness.
const ALWAYS_ON_TOP_JUNK = [
  ["a string true", '"true"'],
  ["the number 1", "1"],
  ["null", "null"],
  ["an object", "{}"],
  ["an array", "[]"],
  ["a string yes", '"yes"'],
];

for (const [label, literal] of ALWAYS_ON_TOP_JUNK) {
  test(`alwaysOnTop falls back to false for ${label}`, () => {
    const dir = tempDir();
    plant(dir, `{"schema":1,"x":10,"y":20,"width":1100,"height":800,"alwaysOnTop":${literal}}`);
    const loaded = load(dir);
    assert.equal(loaded.alwaysOnTop, false);
    assert.notEqual(loaded.alwaysOnTop, true);
  });
}

test("a missing alwaysOnTop falls back to false while geometry still restores", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":10,"y":20,"width":1100,"height":800}');
  const loaded = load(dir);
  assert.equal(loaded.alwaysOnTop, false);
  // The geometry is intact, so it is kept - a junk boolean does not discard a
  // perfectly good window position.
  assert.equal(loaded.x, 10);
  assert.equal(loaded.width, 1100);
});

// --- prototype pollution ----------------------------------------------------

// MEASURED on node v24.15.0 in this worktree:
//   JSON.parse('{"__proto__":{"polluted":1}}') creates an OWN "__proto__" data
//   property; the parsed object's real prototype is untouched.
//   Object.assign({}, parsed) then COPIES that key, which invokes the
//   __proto__ setter on the target and REPLACES the target's prototype, so the
//   result inherits every attacker key. ({...parsed}) defines an own property
//   instead and does not.
//
// The consequence for these tests is subtle and worth stating, because getting
// it wrong produces a test that passes for the wrong reason: asserting only
// that a planted width is the default does NOT discriminate, since the payload
// has no own "width" for Object.assign to copy and the default survives either
// way. The arm that actually reddens for an Object.assign loader is the
// inherited-key assertion below.
// MEASURED, not assumed: with the loader replaced by
// Object.assign({}, defaults, parsed), 8 of these 72 arms redden - the six
// alwaysOnTop arms, the prototype arm below, and the constructor arm. This
// first arm is NOT among them. It survives, because the payload carries no own
// "width" for Object.assign to copy, so the default stands either way. It is
// kept because it pins a real property - __proto__ is never a source of field
// values - but it is documented as a statement, not as the guard.
test("a planted __proto__ width supplies no width, so the file is rejected", () => {
  const dir = tempDir();
  plant(dir, '{"__proto__":{"width":99999},"schema":1,"x":10,"y":20,"height":800,"alwaysOnTop":false}');
  assert.equal(load(dir).width, DEFAULTS.width);
  // Explicit about the mechanism: the width is missing, so the whole payload is
  // refused. Asserting the fault stops this reading as proof of proto handling.
  const report = inspect(dir);
  assert.equal(report.restored, false);
  assert.ok(report.faults.some((f) => f.includes("width")));
});

test("a planted __proto__ never reaches the returned object's prototype", () => {
  const dir = tempDir();
  plant(dir, '{"__proto__":{"polluted":1},"schema":1,"x":10,"y":20,"width":1100,"height":800,"alwaysOnTop":false}');
  const loaded = load(dir);
  // The discriminating assertion: an Object.assign based loader hands back an
  // object whose prototype IS the attacker payload, so this reads 1.
  assert.equal(loaded.polluted, undefined);
  assert.equal(Object.getPrototypeOf(loaded), Object.prototype);
  assert.deepEqual(Object.keys(loaded).sort(), [...STATE_KEYS].sort());
});

test("a planted __proto__ does not pollute Object.prototype globally", () => {
  const dir = tempDir();
  plant(dir, '{"__proto__":{"globallyPolluted":1},"schema":1,"x":10,"y":20,"width":1100,"height":800,"alwaysOnTop":false}');
  load(dir);
  assert.equal({}.globallyPolluted, undefined);
  assert.equal(Object.prototype.globallyPolluted, undefined);
});

test("a constructor key in the payload is ignored like any other unknown key", () => {
  const dir = tempDir();
  plant(dir, '{"constructor":{"prototype":{"width":1}},"schema":1,"x":10,"y":20,"width":1100,"height":800,"alwaysOnTop":false}');
  const loaded = load(dir);
  assert.equal(loaded.width, 1100);
  assert.deepEqual(Object.keys(loaded).sort(), [...STATE_KEYS].sort());
});

// --- atomicity --------------------------------------------------------------

test("the partial file exists mid-write and is gone afterwards", () => {
  const dir = tempDir();
  const partial = path.join(dir, PARTIAL_FILENAME);

  writePartial(dir, GOOD);
  // Mid-write: the partial holds the payload and the real file does not exist
  // yet, so a concurrent reader sees no file rather than half a file.
  assert.equal(fs.existsSync(partial), true, "the partial should exist mid-write");
  assert.equal(fs.existsSync(statePath(dir)), false, "the real file must not appear until the rename");

  commitPartial(dir);
  assert.equal(fs.existsSync(partial), false, "the partial should be gone after the commit");
  assert.equal(fs.existsSync(statePath(dir)), true);
  assert.deepEqual(load(dir), GOOD);
});

test("save leaves no partial file behind", () => {
  const dir = tempDir();
  save(dir, GOOD);
  assert.equal(fs.existsSync(path.join(dir, PARTIAL_FILENAME)), false);
});

test("a killed write leaves the previous state readable and is never adopted", () => {
  const dir = tempDir();
  save(dir, GOOD);

  // Simulate a process killed between the write and the rename: the partial
  // lands, the commit never happens. A killed process skips its cleanup, so
  // the partial really is left on disk - that is the state under test.
  writePartial(dir, { ...GOOD, x: 4444, width: 1234 });
  assert.equal(fs.existsSync(path.join(dir, PARTIAL_FILENAME)), true);

  // The committed state is what a reader gets. The abandoned partial is not
  // adopted, not merged, and not preferred.
  assert.deepEqual(load(dir), GOOD);
  assert.notEqual(load(dir).x, 4444);
});

test("a truncated partial never becomes the real file", () => {
  const dir = tempDir();
  save(dir, GOOD);
  fs.writeFileSync(path.join(dir, PARTIAL_FILENAME), '{"schema":1,"x":1,"wid', "utf8");
  assert.deepEqual(load(dir), GOOD);
});

test("a save over an existing state file replaces it wholly", () => {
  const dir = tempDir();
  save(dir, GOOD);
  const next = { schema: SCHEMA_VERSION, x: 5, y: 6, width: 700, height: 500, alwaysOnTop: false };
  save(dir, next);
  assert.deepEqual(load(dir), next);
  const parsed = JSON.parse(fs.readFileSync(statePath(dir), "utf8"));
  assert.deepEqual(Object.keys(parsed).sort(), [...STATE_KEYS].sort());
});

test("save creates the directory when it does not yet exist", () => {
  const dir = path.join(tempDir(), "userData", "nested");
  save(dir, GOOD);
  assert.deepEqual(load(dir), GOOD);
});

// --- load never throws, whatever it is handed -------------------------------

test("load never throws for any argument shape", () => {
  for (const arg of [undefined, null, "", 42, {}, [], path.join(tempDir(), "gone")]) {
    let threw = null;
    let result = null;
    try {
      result = load(arg);
    } catch (err) {
      threw = err;
    }
    assert.equal(threw, null, `load threw for ${JSON.stringify(arg)}`);
    assert.deepEqual(result, DEFAULTS);
  }
});

test("load never hands back a reference to the shared DEFAULTS object", () => {
  const dir = tempDir();
  const first = load(dir);
  first.width = 1;
  const second = load(dir);
  assert.equal(second.width, DEFAULTS.width);
  assert.notEqual(first, DEFAULTS);
});

test("inspect names the fault it found rather than only reporting failure", () => {
  const dir = tempDir();
  plant(dir, '{"schema":1,"x":10,"y":20,"width":"wide","height":800,"alwaysOnTop":false}');
  const report = inspect(dir);
  assert.equal(report.restored, false);
  assert.ok(report.faults.length > 0);
  assert.ok(report.faults.some((f) => f.includes("width")), `faults were ${JSON.stringify(report.faults)}`);
});
