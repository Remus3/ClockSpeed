"use strict";

// CS-602 slice S4 - tests for shell/lib/window.js.
//
// WHY THIS FILE NEVER REQUIRES ELECTRON. electron 44.0.0 declares no
// postinstall step, so the package carries no binary until something asks for
// one, and the first require("electron") starts a large lazy download at run
// time. A test that imported it would either hang or pull hundreds of
// megabytes in CI. window.js is therefore built so that the entire window
// CONTRACT - the frame, the security posture, the floor, the mode slot and the
// drag strip - is a plain object and a plain string, gradable on a machine with
// no electron binary, no display server and no game install.
//
// WHY THE SECURITY KEYS ARE ASSERTED AS PRESENT AND NOT MERELY AS TRUE.
// contextIsolation already defaults to true, nodeIntegration to false and
// sandbox to true. Asserting only the VALUES would pass just as well against a
// window.js that omitted all three and let the defaults carry them - and would
// keep passing on the day an upstream release moved one of those defaults.
// Object.hasOwn is what separates "this window states its posture" from "this
// window inherited someone else's".

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const state = require("../lib/state.js");
const windowModule = require("../lib/window.js");
const {
  MODES,
  DEFAULT_MODE,
  MIN_WIDTH,
  MIN_HEIGHT,
  DRAG_STRIP_CSS,
  DRAG_STRIP_HEIGHT,
  OVERRIDABLE_KEYS,
  ALWAYS_ON_TOP_ENV,
  ALWAYS_ON_TOP_FLAG,
  NO_ALWAYS_ON_TOP_FLAG,
  ModeNotImplementedError,
  UnknownModeError,
  buildWindowOptions,
  resolveAlwaysOnTop,
} = windowModule;

// Every mode the shell declares, as a list, so a mode added later is swept by
// the control arm below without anyone remembering to add it there.
const ALL_MODES = Object.freeze(Object.values(MODES));

// assert.throws returns undefined rather than the error it caught, so a
// `const e = assert.throws(...)` reads as a captured exception and is in fact
// always undefined - every instanceof asserted against it would then be
// asserting about nothing. This captures the error itself.
function caught(fn) {
  try {
    fn();
  } catch (err) {
    return err;
  }
  throw new Error("expected a throw, and nothing was thrown");
}

// Overrides chosen to be hostile rather than representative. Each one names a
// field that, if it were writable from outside, would undo a decision this
// module exists to make.
const HOSTILE_OVERRIDES = Object.freeze([
  { frame: true },
  { resizable: false },
  { minWidth: 0, minHeight: 0 },
  { webPreferences: { contextIsolation: false, nodeIntegration: true, sandbox: false } },
  { webPreferences: null },
]);

// ---------------------------------------------------------------------------
// The window contract
// ---------------------------------------------------------------------------

test("frame is false - the companion window carries no OS title bar", () => {
  assert.equal(buildWindowOptions().frame, false);
});

test("resizable is true", () => {
  assert.equal(buildWindowOptions().resizable, true);
});

test("alwaysOnTop defaults to false", () => {
  assert.equal(buildWindowOptions().alwaysOnTop, false);
  assert.equal(buildWindowOptions(MODES.COMPANION, {}).alwaysOnTop, false);
});

test("alwaysOnTop is true when the caller asks for it", () => {
  assert.equal(buildWindowOptions(MODES.COMPANION, { alwaysOnTop: true }).alwaysOnTop, true);
});

test("minWidth and minHeight sit at the declared floor, which is above zero", () => {
  const options = buildWindowOptions();
  assert.ok(MIN_WIDTH > 0, "the width floor must be above electron's default of 0");
  assert.ok(MIN_HEIGHT > 0, "the height floor must be above electron's default of 0");
  assert.equal(options.minWidth, MIN_WIDTH);
  assert.equal(options.minHeight, MIN_HEIGHT);
});

// The two floors are different facts and are deliberately not the same
// constant. state.js's floor is a CORRUPTION threshold - a state file asking
// for something smaller is junk. This module's floor is what the operating
// system will let the operator drag the window down to. What must hold is the
// ORDER between them: a window resized to this shell's floor has to read back
// as valid rather than as corrupt, which is false the moment this floor drops
// below state.js's. Asserting the relation rather than the values is what lets
// either side move without silently breaking restore.
test("the window floor is at or above the floor state.js calls corrupt", () => {
  assert.ok(
    MIN_WIDTH >= state.MIN_WIDTH,
    `window floor ${MIN_WIDTH} must not be under state floor ${state.MIN_WIDTH}`
  );
  assert.ok(
    MIN_HEIGHT >= state.MIN_HEIGHT,
    `window floor ${MIN_HEIGHT} must not be under state floor ${state.MIN_HEIGHT}`
  );
});

test("the three security webPreferences are stated explicitly, never defaulted", () => {
  const prefs = buildWindowOptions().webPreferences;
  for (const key of ["contextIsolation", "nodeIntegration", "sandbox"]) {
    assert.ok(Object.hasOwn(prefs, key), `${key} must be written down, not inherited`);
  }
  assert.equal(prefs.contextIsolation, true);
  assert.equal(prefs.nodeIntegration, false);
  assert.equal(prefs.sandbox, true);
});

// ---------------------------------------------------------------------------
// The mode slot
// ---------------------------------------------------------------------------

test("MODES declares OVERLAY, and building it throws a named error", () => {
  assert.ok(Object.hasOwn(MODES, "OVERLAY"));
  assert.ok(Object.hasOwn(MODES, "COMPANION"));
  assert.equal(DEFAULT_MODE, MODES.COMPANION);

  const thrown = caught(() => buildWindowOptions(MODES.OVERLAY));
  assert.ok(thrown instanceof ModeNotImplementedError);
  assert.equal(thrown.name, "ModeNotImplementedError");
  assert.equal(thrown.mode, MODES.OVERLAY);
});

test("an unknown mode is refused rather than quietly treated as the default", () => {
  const thrown = caught(() => buildWindowOptions("FULLSCREEN_KIOSK"));
  assert.ok(thrown instanceof UnknownModeError);
  assert.equal(thrown.name, "UnknownModeError");
});

// ---------------------------------------------------------------------------
// The control arm
// ---------------------------------------------------------------------------

// A per-field assertion proves the default path is right. It cannot prove that
// nothing REACHES the field from outside. This sweeps every declared mode
// against every hostile override and insists the answer is the same one every
// time: an implemented mode yields frame false, and the unimplemented mode
// throws. There is no third outcome and no input that produces one.
test("control table - no mode and no override ever yields a framed window", () => {
  let checked = 0;
  for (const mode of ALL_MODES) {
    for (const overrides of HOSTILE_OVERRIDES) {
      if (mode === MODES.OVERLAY) {
        assert.throws(() => buildWindowOptions(mode, overrides), ModeNotImplementedError);
        checked += 1;
        continue;
      }
      const options = buildWindowOptions(mode, overrides);
      assert.equal(options.frame, false, `frame escaped for mode ${mode}`);
      assert.equal(options.resizable, true, `resizable escaped for mode ${mode}`);
      assert.equal(options.minWidth, MIN_WIDTH, `minWidth escaped for mode ${mode}`);
      assert.equal(options.minHeight, MIN_HEIGHT, `minHeight escaped for mode ${mode}`);
      assert.equal(options.webPreferences.contextIsolation, true);
      assert.equal(options.webPreferences.nodeIntegration, false);
      assert.equal(options.webPreferences.sandbox, true);
      checked += 1;
    }
  }
  // Bound the sweep to the population it claims to cover. Were MODES or the
  // override table to come back empty, every assertion above would vacuously
  // hold and this test would pass having examined nothing at all.
  const expected = ALL_MODES.length * HOSTILE_OVERRIDES.length;
  assert.equal(checked, expected);
  assert.ok(checked > 0);
});

test("only the declared keys are overridable, and geometry is among them", () => {
  for (const key of ["alwaysOnTop", "x", "y", "width", "height", "preload"]) {
    assert.ok(OVERRIDABLE_KEYS.includes(key), `${key} must be overridable`);
  }
  for (const key of ["frame", "resizable", "minWidth", "minHeight", "webPreferences"]) {
    assert.ok(!OVERRIDABLE_KEYS.includes(key), `${key} must NOT be overridable`);
  }
});

test("geometry overrides are carried through onto the options", () => {
  const options = buildWindowOptions(MODES.COMPANION, {
    x: 12,
    y: 34,
    width: 1234,
    height: 900,
  });
  assert.equal(options.x, 12);
  assert.equal(options.y, 34);
  assert.equal(options.width, 1234);
  assert.equal(options.height, 900);
});

// A window narrower than its own minWidth is a self-contradicting options
// object. Electron is left to reconcile the pair, and which side wins is not
// something this module should be guessing about downstream of itself.
test("a width or height under the floor is raised to it rather than passed on", () => {
  const options = buildWindowOptions(MODES.COMPANION, { width: 1, height: 1 });
  assert.equal(options.width, MIN_WIDTH);
  assert.equal(options.height, MIN_HEIGHT);
  assert.ok(options.width >= options.minWidth);
  assert.ok(options.height >= options.minHeight);
});

test("the preload override lands inside webPreferences, not beside it", () => {
  const options = buildWindowOptions(MODES.COMPANION, { preload: "/somewhere/preload.js" });
  assert.equal(options.webPreferences.preload, "/somewhere/preload.js");
  assert.ok(!Object.hasOwn(options, "preload"));
});

test("each call returns a fresh object - mutating one cannot move the next", () => {
  const first = buildWindowOptions();
  first.frame = true;
  first.webPreferences.sandbox = false;
  const second = buildWindowOptions();
  assert.equal(second.frame, false);
  assert.equal(second.webPreferences.sandbox, true);
});

// ---------------------------------------------------------------------------
// Always on top - the precedence, which is a decision and so belongs here
// ---------------------------------------------------------------------------

test("resolveAlwaysOnTop - a launch flag outranks the environment and the file", () => {
  assert.equal(
    resolveAlwaysOnTop({ persisted: false, argv: [ALWAYS_ON_TOP_FLAG], env: {} }),
    true
  );
  assert.equal(
    resolveAlwaysOnTop({ persisted: true, argv: [NO_ALWAYS_ON_TOP_FLAG], env: {} }),
    false
  );
  // Both flags present. The negative wins, because the safe direction for a
  // window that pins itself over everything else is unmistakably down.
  assert.equal(
    resolveAlwaysOnTop({
      persisted: false,
      argv: [ALWAYS_ON_TOP_FLAG, NO_ALWAYS_ON_TOP_FLAG],
      env: {},
    }),
    false
  );
});

test("resolveAlwaysOnTop - the environment outranks the persisted preference", () => {
  assert.equal(
    resolveAlwaysOnTop({ persisted: false, argv: [], env: { [ALWAYS_ON_TOP_ENV]: "1" } }),
    true
  );
  assert.equal(
    resolveAlwaysOnTop({ persisted: true, argv: [], env: { [ALWAYS_ON_TOP_ENV]: "0" } }),
    false
  );
});

test("resolveAlwaysOnTop - the persisted preference is used when nothing overrides", () => {
  assert.equal(resolveAlwaysOnTop({ persisted: true, argv: [], env: {} }), true);
  assert.equal(resolveAlwaysOnTop({ persisted: false, argv: [], env: {} }), false);
});

test("resolveAlwaysOnTop - anything unusable falls to false, never to true", () => {
  const junk = [
    undefined,
    {},
    { persisted: "yes", argv: null, env: null },
    { persisted: 1, argv: [], env: {} },
    { persisted: null, argv: [], env: { [ALWAYS_ON_TOP_ENV]: "maybe" } },
    { persisted: false, argv: ["--always-on-top=1"], env: {} },
  ];
  for (const input of junk) {
    assert.equal(resolveAlwaysOnTop(input), false, `unusable input reached true: ${JSON.stringify(input)}`);
  }
});

// ---------------------------------------------------------------------------
// The drag strip
// ---------------------------------------------------------------------------

// A frameless window has no OS title bar, so it has no drag region at all and
// the operator cannot move it - which would make "remembers where you put it"
// vacuous. The shell injects this rather than the page carrying it, because the
// page is served to an ordinary browser too, where a drag strip means nothing.
test("the drag strip CSS carries both app-region spellings and a no-drag escape", () => {
  assert.equal(typeof DRAG_STRIP_CSS, "string");
  assert.ok(DRAG_STRIP_CSS.length > 0);

  // The prefixed spelling is what Chromium honours today; the unprefixed one is
  // the standard property. Matching the unprefixed spelling needs an anchor,
  // because "-webkit-app-region" CONTAINS "app-region" and a bare substring
  // test would pass on the prefixed declaration alone.
  assert.ok(/^\s*-webkit-app-region:\s*drag;/m.test(DRAG_STRIP_CSS), "missing -webkit- drag");
  assert.ok(/^\s*app-region:\s*drag;/m.test(DRAG_STRIP_CSS), "missing unprefixed drag");
  assert.ok(/^\s*-webkit-app-region:\s*no-drag;/m.test(DRAG_STRIP_CSS), "missing -webkit- no-drag");
  assert.ok(/^\s*app-region:\s*no-drag;/m.test(DRAG_STRIP_CSS), "missing unprefixed no-drag");

  // An explicit class the page or a later slice can hang on anything the strip
  // would otherwise swallow.
  assert.ok(/\.no-drag\b/.test(DRAG_STRIP_CSS), "missing the .no-drag escape class");
});

test("the drag strip insets the scrollport rather than covering the page", () => {
  assert.ok(Number.isInteger(DRAG_STRIP_HEIGHT));
  assert.ok(DRAG_STRIP_HEIGHT > 0);
  // Thin. A strip deep enough to hide a heading is not a title bar substitute,
  // it is a hole in the page.
  assert.ok(DRAG_STRIP_HEIGHT <= 40, "the strip must stay thin");

  // The height appears in the strip's own box AND in the padding that reserves
  // room for it. Both are generated from the one constant, so this asserts they
  // cannot drift apart rather than asserting a number.
  const occurrences = DRAG_STRIP_CSS.split(`${DRAG_STRIP_HEIGHT}px`).length - 1;
  assert.ok(occurrences >= 2, "the strip must both size itself and inset the scrollport");

  // THIS ASSERTION USED TO REQUIRE `padding-top:` AND SO ENCODED THE DEFECT.
  // A body padding reserves space in DOCUMENT flow while the band is fixed to
  // the VIEWPORT, so the two coincide only at scroll offset zero - CS-617
  // measured the band swallowing real content at a body scroll of 369. What
  // keeps the page clear is the scrollport starting below the band, which is
  // geometric rather than positional.
  assert.ok(
    !/padding-top:/.test(DRAG_STRIP_CSS),
    "a body padding-top reserves DOCUMENT space against a VIEWPORT-fixed band, " +
      "which holds only at scroll offset 0 - that is the CS-617 defect",
  );
  // THE VALUE SEPARATOR IS A CHARACTER CLASS AND NOT THE WHITESPACE SHORTHAND,
  // ON PURPOSE. Writing the shorthand straight after a hyphenated property name
  // puts a single letter, a colon and a backslash side by side with a
  // non-alphanumeric in front of the letter - which is the drive-lettered path
  // shape tests/shell/test_shell_assets.py sweeps for, and it reddened that arm
  // on this very file. The neighbouring app-region assertions escape it only
  // because a letter happens to precede theirs, so this is luck rather than a
  // rule anyone can rely on. The class is also the more accurate thing to
  // write: a CSS value is not separated from its property by a newline.
  assert.ok(/^[ \t]*overflow:[ \t]*hidden;/m.test(DRAG_STRIP_CSS), "html must stop scrolling");
  assert.ok(
    new RegExp(`^[ \\t]*top:[ \\t]*${DRAG_STRIP_HEIGHT}px;`, "m").test(DRAG_STRIP_CSS),
    "the scrollport must be inset by the strip's height",
  );
  assert.ok(
    /^[ \t]*overflow-y:[ \t]*auto;/m.test(DRAG_STRIP_CSS),
    "the inset body must scroll",
  );
});

// The repair deliberately left app-region alone. The rival fix was
// `pointer-events: none` on the band, and whether Chromium still honours a drag
// region on a pointer-transparent element is a question nothing here can answer
// - this module is graded without electron on purpose. A fix that CANNOT break
// dragging beat one that MIGHT, so the band has to keep hit-testing.
test("the drag band is not made pointer-transparent", () => {
  assert.ok(
    !/pointer-events/.test(DRAG_STRIP_CSS),
    "pointer-events on the band puts the drag region's survival in question and " +
      "no test in this suite can settle it - see CS-617",
  );
});

// ---------------------------------------------------------------------------
// The purity partition
// ---------------------------------------------------------------------------

// The same shape as the assertion geometry.js carries. This is what makes the
// module gradable in CI at all: no electron require means no lazy binary
// download, and no filesystem require means nothing here depends on a machine
// that has a game, a save or a certificate on it.
test("window.js requires electron nowhere, and touches no filesystem", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "lib", "window.js"), "utf8");
  assert.ok(!/require\(\s*["'](electron|node:fs|fs)["']\s*\)/.test(source));
});

test("window.js is 7-bit ASCII with no carriage returns", () => {
  const bytes = fs.readFileSync(path.join(__dirname, "..", "lib", "window.js"));
  assert.equal(bytes.includes(0x0d), false, "window.js must be LF, never CRLF");
  for (const byte of bytes) {
    assert.ok(byte <= 0x7f, `non-ASCII byte 0x${byte.toString(16)} in window.js`);
  }
});
