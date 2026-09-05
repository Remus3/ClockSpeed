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
const { spawn } = require("node:child_process");
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
  isPartialFilename,
  STATE_KEYS,
  STATE_FILENAME,
  PARTIAL_PREFIX,
  PARTIAL_SUFFIX,
  PARTIAL_STALE_MS,
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

/**
 * Every staging file currently sitting in the directory, whatever it is named.
 *
 * Deliberately matches on SHAPE rather than asking the module which names it
 * would have produced, so a staging file the module forgot about is still seen.
 */
function partialsIn(dir) {
  return fs
    .readdirSync(dir)
    .filter((name) => name !== STATE_FILENAME && name.startsWith(`${STATE_FILENAME}.`))
    .sort();
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

  // The staging path comes BACK from writePartial rather than being rebuilt
  // here from a shared constant. Rebuilding it is what the fixed name allowed,
  // and CS-911 is what that cost.
  const partial = writePartial(dir, GOOD);
  // Mid-write: the partial holds the payload and the real file does not exist
  // yet, so a concurrent reader sees no file rather than half a file.
  assert.equal(fs.existsSync(partial), true, "the partial should exist mid-write");
  assert.equal(fs.existsSync(statePath(dir)), false, "the real file must not appear until the rename");

  commitPartial(dir, partial);
  assert.equal(fs.existsSync(partial), false, "the partial should be gone after the commit");
  assert.equal(fs.existsSync(statePath(dir)), true);
  assert.deepEqual(load(dir), GOOD);
});

test("save leaves no partial file behind", () => {
  const dir = tempDir();
  save(dir, GOOD);
  assert.deepEqual(partialsIn(dir), []);
});

test("a killed write leaves the previous state readable and is never adopted", () => {
  const dir = tempDir();
  save(dir, GOOD);

  // Simulate a process killed between the write and the rename: the partial
  // lands, the commit never happens. A killed process skips its cleanup, so
  // the partial really is left on disk - that is the state under test.
  const abandoned = writePartial(dir, { ...GOOD, x: 4444, width: 1234 });
  assert.equal(fs.existsSync(abandoned), true);

  // The committed state is what a reader gets. The abandoned partial is not
  // adopted, not merged, and not preferred.
  assert.deepEqual(load(dir), GOOD);
  assert.notEqual(load(dir).x, 4444);
});

test("a truncated partial never becomes the real file", () => {
  const dir = tempDir();
  save(dir, GOOD);
  const planted = path.join(dir, `${PARTIAL_PREFIX}planted${PARTIAL_SUFFIX}`);
  assert.equal(isPartialFilename(path.basename(planted)), true, "the plant must be partial-shaped to test anything");
  fs.writeFileSync(planted, '{"schema":1,"x":1,"wid', "utf8");
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

// --- CS-911: two writers on one directory -----------------------------------
//
// The atomicity arms above hold for ONE writer. They were measured NOT to hold
// for two: the module staged through a partial file with a FIXED name opened
// truncating, so a second writer's open ZEROED a first writer's already-staged
// payload, and the first writer's rename then published nothing at all over a
// good file. Non-negotiable 5 does not carve out a single-writer exception, and
// neither did this module's own header. These arms hold the claim to the case
// it actually makes.

const WRITER_A = Object.freeze({ schema: 1, x: 11, y: 22, width: 900, height: 700, alwaysOnTop: false });
const WRITER_B = Object.freeze({ schema: 1, x: 33, y: 44, width: 1000, height: 750, alwaysOnTop: true });

test("a second writer's staging cannot empty a first writer's staged payload", () => {
  const dir = tempDir();
  save(dir, GOOD);

  // Writer A stages a complete payload and has not committed it yet.
  const stagedA = writePartial(dir, WRITER_A);

  // Writer B begins to stage and dies between its open and its write. That is
  // the exact window this item was filed on, and injecting the death at
  // fs.writeFileSync is what makes it a deterministic interleave rather than a
  // race the arm would usually lose. The injection is ASSERTED to have fired,
  // so an implementation that stopped staging through this call could not leave
  // the arm quietly passing about nothing.
  const realWriteFileSync = fs.writeFileSync;
  fs.writeFileSync = () => {
    throw new Error("s1 injected: writer B died after its open and before its write");
  };
  try {
    assert.throws(() => writePartial(dir, WRITER_B), /s1 injected/);
  } finally {
    fs.writeFileSync = realWriteFileSync;
  }

  // Writer A commits what IT staged. Nothing writer B did may reach this file.
  commitPartial(dir, stagedA);

  const published = fs.readFileSync(path.join(dir, STATE_FILENAME));
  assert.notEqual(published.length, 0, "an empty file was published over a good state file");
  assert.deepEqual(JSON.parse(published.toString("utf8")), WRITER_A);
});

test("a whole save by a second writer leaves a first writer's stage committable", () => {
  const dir = tempDir();
  save(dir, GOOD);

  const stagedA = writePartial(dir, WRITER_A);
  // Writer B runs a complete save, start to finish, through the public API.
  save(dir, WRITER_B);
  // A's stage must still be A's. Under the fixed name B had renamed it away and
  // this commit failed with ENOENT - a code deliberately not retried, because a
  // rename with no source never becomes possible by waiting.
  commitPartial(dir, stagedA);

  assert.deepEqual(load(dir), WRITER_A);
});

// A standalone writer, run as its own OS process so the concurrency is real
// rather than simulated. Written to a scratch file at run time rather than
// committed as a fixture, because a fixture would be a third tracked file.
const WRITER_SOURCE = [
  '"use strict";',
  'const fs = require("node:fs");',
  'const nodePath = require("node:path");',
  "const dir = process.argv[2];",
  "const st = require(process.argv[3]);",
  "const rounds = Number(process.argv[4]);",
  "const seed = Number(process.argv[5]);",
  "const target = nodePath.join(dir, st.STATE_FILENAME);",
  "// A reader losing a race with a rename is ordinary on Windows and is not the",
  "// fault under test. A file that reads back EMPTY or unparseable is.",
  'const CONTENTION = new Set(["ENOENT", "EPERM", "EBUSY", "EACCES"]);',
  "let saveFaults = 0;",
  "let corrupt = 0;",
  'let first = "";',
  'const note = (why) => { corrupt += 1; if (first === "") { first = why; } };',
  "for (let i = 0; i < rounds; i += 1) {",
  "  try {",
  "    st.save(dir, { schema: st.SCHEMA_VERSION, x: seed, y: i, width: 900, height: 700, alwaysOnTop: false });",
  "  } catch (err) {",
  "    saveFaults += 1;",
  '    if (first === "") { first = "save failed with " + String(err.code || err.message); }',
  "  }",
  "  let raw = null;",
  "  try {",
  "    raw = fs.readFileSync(target);",
  "  } catch (err) {",
  '    if (!CONTENTION.has(err.code)) { note("read failed with " + String(err.code)); }',
  "  }",
  "  if (raw !== null) {",
  "    if (raw.length === 0) {",
  '      note("the published state file read back empty");',
  "    } else {",
  '      try { JSON.parse(raw.toString("utf8")); } catch { note("the published state file did not parse"); }',
  "    }",
  "  }",
  "}",
  "process.stdout.write(JSON.stringify({ saveFaults, corrupt, first }));",
  "",
].join("\n");

const CONCURRENT_WRITERS = 4;
const CONCURRENT_ROUNDS = 60;

test("real concurrent writers never publish an empty or truncated state file", async () => {
  const dir = tempDir();
  const script = path.join(tempDir(), "s1_concurrent_writer.js");
  fs.writeFileSync(script, WRITER_SOURCE, "utf8");
  const modulePath = require.resolve("../lib/state.js");

  save(dir, GOOD);

  const runs = await Promise.all(
    Array.from({ length: CONCURRENT_WRITERS }, (unusedValue, k) => new Promise((resolve) => {
      const child = spawn(
        process.execPath,
        [script, dir, modulePath, String(CONCURRENT_ROUNDS), String(1000 + k)],
        { stdio: ["ignore", "pipe", "pipe"] },
      );
      let out = "";
      let err = "";
      child.stdout.on("data", (chunk) => { out += chunk; });
      child.stderr.on("data", (chunk) => { err += chunk; });
      child.on("close", (code) => resolve({ code, out, err }));
    })),
  );

  for (const run of runs) {
    assert.equal(run.code, 0, `a writer exited ${run.code}: ${run.err}`);
  }

  // Bind the aggregates to scalars before asserting, so the message carries the
  // count rather than an expression rendering that hides it.
  const reports = runs.map((run) => JSON.parse(run.out));
  const corrupt = reports.reduce((sum, report) => sum + report.corrupt, 0);
  const saveFaults = reports.reduce((sum, report) => sum + report.saveFaults, 0);
  const attempts = CONCURRENT_WRITERS * CONCURRENT_ROUNDS;
  const firstNote = reports.map((report) => report.first).find((why) => why !== "") || "none";

  assert.equal(corrupt, 0, `${corrupt} corrupt observations across ${attempts} concurrent saves - first was: ${firstNote}`);
  assert.equal(saveFaults, 0, `${saveFaults} of ${attempts} concurrent saves failed outright - first was: ${firstNote}`);

  const finalKeys = Object.keys(JSON.parse(fs.readFileSync(path.join(dir, STATE_FILENAME), "utf8"))).sort();
  assert.deepEqual(finalKeys, [...STATE_KEYS].sort());
  assert.deepEqual(partialsIn(dir), [], "concurrent saves left staging files behind");
});

// --- CS-911: the fix must not reintroduce its own fault class ---------------

test("no two stages ever share a filename", () => {
  const dir = tempDir();
  const names = new Set();
  for (let i = 0; i < 200; i += 1) {
    names.add(path.basename(writePartial(dir, GOOD)));
  }
  // Bound to a scalar first: the message must carry the count, not an
  // expression rendering that hides which side came up short.
  const distinct = names.size;
  assert.equal(distinct, 200, `${distinct} distinct staging names across 200 stages`);
  assert.equal(partialsIn(dir).length, 200, "each stage should be its own file on disk");
  for (const name of names) {
    assert.equal(isPartialFilename(name), true, `${name} is not a staging name`);
  }
});

test("a staging name is never mistaken for the state file", () => {
  // The sweep unlinks whatever this predicate accepts, so it accepting the real
  // file would turn housekeeping into data loss.
  assert.equal(isPartialFilename(STATE_FILENAME), false);
  assert.equal(isPartialFilename(`${STATE_FILENAME}${PARTIAL_SUFFIX}`), false, "no unique segment is not a staging name");
  assert.equal(isPartialFilename(`${PARTIAL_PREFIX}${PARTIAL_SUFFIX}`), false, "an empty unique segment is not one either");
  assert.equal(isPartialFilename(`${PARTIAL_PREFIX}abc${PARTIAL_SUFFIX}`), true);
  for (const junk of [undefined, null, 42, {}, [], "", "other.partial", `${STATE_FILENAME}.abc`]) {
    assert.equal(isPartialFilename(junk), false, `${JSON.stringify(junk)} was accepted as a staging name`);
  }
});

test("a commit sweeps stages old enough that no writer could still own them", () => {
  const dir = tempDir();
  save(dir, GOOD);

  // An abandoned stage from a killed process, backdated past the threshold.
  const abandoned = writePartial(dir, GOOD);
  const old = (Date.now() - PARTIAL_STALE_MS - 60000) / 1000;
  fs.utimesSync(abandoned, old, old);
  // And a fresh one, which a live writer could still be holding.
  const inFlight = writePartial(dir, GOOD);

  save(dir, GOOD);

  assert.equal(fs.existsSync(abandoned), false, "a stale stage should have been swept");
  assert.equal(fs.existsSync(inFlight), true, "a fresh stage must never be swept from under a live writer");
  // The published file is untouched by any of it.
  assert.deepEqual(load(dir), GOOD);
});

test("commitPartial refuses a path it did not stage", () => {
  const dir = tempDir();
  save(dir, GOOD);

  // A caller that could name any path could rename anything over the state
  // file. The path argument is the new surface this item opened, so it is
  // fenced here rather than trusted.
  const outside = tempDir();
  const foreign = writePartial(outside, WRITER_B);
  assert.throws(() => commitPartial(dir, foreign), /does not belong/);

  const notAStage = path.join(dir, "something-else.json");
  fs.writeFileSync(notAStage, "{}", "utf8");
  assert.throws(() => commitPartial(dir, notAStage), /does not belong/);

  for (const junk of [undefined, null, "", 42, {}]) {
    assert.throws(() => commitPartial(dir, junk), /no staged file was supplied/, `${JSON.stringify(junk)} was accepted`);
  }

  // Through all of that the good state file is exactly as it was.
  assert.deepEqual(load(dir), GOOD);
});

test("a stage never truncates a file that already exists", () => {
  const dir = tempDir();
  fs.mkdirSync(dir, { recursive: true });

  // The unique name should make this unreachable. The exclusive open is what
  // makes it LOUD if it ever becomes reachable again, instead of silently
  // zeroing another writer's payload the way the fixed name did.
  const collision = path.join(dir, `${PARTIAL_PREFIX}collide${PARTIAL_SUFFIX}`);
  fs.writeFileSync(collision, "somebody else's staged payload", "utf8");

  const realOpenSync = fs.openSync;
  fs.openSync = (target, flags, ...rest) => realOpenSync(collision, flags, ...rest);
  let caught = null;
  try {
    writePartial(dir, GOOD);
  } catch (err) {
    caught = err;
  } finally {
    fs.openSync = realOpenSync;
  }

  assert.notEqual(caught, null, "a stage onto an existing file must throw");
  assert.equal(caught.code, "EEXIST", `the open flag is not exclusive - code was ${caught && caught.code}`);
  assert.equal(fs.readFileSync(collision, "utf8"), "somebody else's staged payload");
});
