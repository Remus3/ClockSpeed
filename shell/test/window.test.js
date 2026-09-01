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

// ---------------------------------------------------------------------------
// CS-874 - grading the cascade the sheet composes, not tokens in a string
// ---------------------------------------------------------------------------

// WHAT WAS WRONG WITH THE ARM THIS REPLACES, which was green the whole time.
// Its three positive assertions were free-floating multiline regexes over the
// entire constant - a hidden overflow, a top at the strip's height, and an auto
// overflow-y - and not one of them was scoped to a rule. A token ANYWHERE in
// the sheet satisfied it, so it never asserted that any particular element was
// positioned, inset or scrollable, which is the only thing CS-617 is about.
// Four mutants were demonstrated to keep it green while restoring the very
// defect it exists to prevent:
//
//   1. delete `position` from the scrollport, which leaves its `top` inert and
//      un-insets the scrollport;
//   2. give the scrollport a zero top and the band the strip's height, which
//      walks the band down over content;
//   3. clip the scrollport to a sliver and park the surviving tokens on a
//      selector the page does not have;
//   4. put the tokens in a comment plus a media query that can never match, and
//      restore the band over unpadded content.
//
// Every one of those is a claim about WHICH ELEMENT declares WHAT, and no regex
// over an unparsed string can make that claim. So the sheet is parsed instead:
// comments stripped, split into rules, each rule's selector list read, and each
// selector's declarations composed in document order the way a cascade composes
// them. A token then has to be on the right element to count, which is what
// these assertions were claiming all along.

//: A declaration value that makes a box a scroller on that axis.
const SCROLLING_OVERFLOW = Object.freeze(["auto", "scroll"]);

//: A declaration value that hides overflow instead of offering it.
const CLIPPING_OVERFLOW = Object.freeze(["hidden", "clip"]);

//: The role each selector plays, named once so an assertion reads as a claim
//: about the scrollport or the band rather than about a string.
const ROOT_SELECTOR = "html";
const SCROLLPORT_SELECTOR = "body";
const BAND_SELECTOR = "body::before";

//: Every selector this sheet is permitted to name, in full. MUTANT 3 parked the
//: geometry on a selector the page does not have, which no per-property arm can
//: see - only an arm that knows the whole permitted population can. The sheet
//: is thirty lines and every rule in it is load-bearing, so enumerating it is
//: cheap and a future addition is meant to be a deliberate edit here.
const DECLARED_SELECTORS = Object.freeze([
  ROOT_SELECTOR,
  SCROLLPORT_SELECTOR,
  BAND_SELECTOR,
  "a",
  "button",
  "input",
  "select",
  "textarea",
  "summary",
  "label",
  '[role="button"]',
  '[role="link"]',
  "[contenteditable]",
  ".no-drag",
]);

function normalizeSpace(text) {
  return text.replace(/\s+/g, " ").trim().toLowerCase();
}

// `body:before` and `body::before` name the same pseudo-element and the legacy
// one-colon spelling is still valid CSS, so it must not be a way past the arm.
function normalizeSelector(text) {
  return normalizeSpace(text).replace(/([^:]):(before|after)\b/g, "$1::$2");
}

/**
 * Split a stylesheet into its top-level rules.
 *
 * Comments go first, so a token that is only ever mentioned in prose cannot
 * satisfy anything. Nesting is tracked by depth rather than assumed away, so a
 * conditional group keeps its own contents instead of leaking them into the
 * enclosing scope - which is exactly how MUTANT 4 smuggled its declarations
 * onto a selector that never received them at run time.
 */
function parseSheet(css) {
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = [];
  let malformed = false;
  let depth = 0;
  let prelude = "";
  let start = 0;
  for (let i = 0; i < stripped.length; i += 1) {
    const ch = stripped[i];
    if (ch === "{") {
      if (depth === 0) {
        start = i + 1;
      }
      depth += 1;
    } else if (ch === "}") {
      depth -= 1;
      if (depth < 0) {
        malformed = true;
        depth = 0;
        prelude = "";
      } else if (depth === 0) {
        rules.push({ prelude: normalizeSpace(prelude), body: stripped.slice(start, i) });
        prelude = "";
      }
    } else if (depth === 0) {
      prelude += ch;
    }
  }
  if (depth !== 0) {
    malformed = true;
  }
  const plain = rules.filter((rule) => !rule.prelude.startsWith("@"));
  const selectors = [];
  for (const rule of plain) {
    for (const one of rule.prelude.split(",")) {
      const named = normalizeSelector(one);
      if (named.length > 0) {
        selectors.push(named);
      }
    }
  }
  return {
    stripped,
    rules,
    malformed,
    selectors,
    atRulePreludes: rules
      .filter((rule) => rule.prelude.startsWith("@"))
      .map((rule) => rule.prelude),
  };
}

/** One rule's declarations, last-wins within the block as the cascade has it. */
function parseDeclarations(body) {
  const declared = new Map();
  for (const chunk of body.split(";")) {
    const at = chunk.indexOf(":");
    if (at < 0) {
      continue;
    }
    const property = normalizeSpace(chunk.slice(0, at));
    if (property.length > 0) {
      declared.set(property, normalizeSpace(chunk.slice(at + 1)));
    }
  }
  return declared;
}

/**
 * What one selector ends up declaring once this sheet has been composed.
 *
 * Rules are merged in document order so a later rule beats an earlier one, and
 * a conditional group contributes nothing at all - a media query that can never
 * match declares nothing, and one that always matches is still a condition this
 * sheet has no business expressing.
 *
 * @returns {{composed: Map<string,string>, matched: number}} The declarations,
 *   and how many top-level rules named the selector - which is what stops a
 *   whole missing rule reading as a rule that declares nothing.
 */
function composedFor(css, selector) {
  const wanted = normalizeSelector(selector);
  const composed = new Map();
  let matched = 0;
  for (const rule of parseSheet(css).rules) {
    if (rule.prelude.startsWith("@")) {
      continue;
    }
    if (!rule.prelude.split(",").map(normalizeSelector).includes(wanted)) {
      continue;
    }
    matched += 1;
    for (const [property, value] of parseDeclarations(rule.body)) {
      composed.set(property, value);
    }
  }
  return { composed, matched };
}

// THE GRADER IS ITSELF GRADED, against a synthetic sheet carrying all four
// dodges at once. Without this the arms below could every one of them be
// passing on an empty Map - a parser that returned nothing would satisfy every
// "must not be hidden" assertion in the file and fail no other.
test("the CSS grader sees through every dodge the token arm let past", () => {
  const planted = [
    "/* body { position: fixed; top: 28px; overflow-y: auto; } */",
    "@media (min-width: 99999px) {",
    "  body { position: fixed; top: 28px; overflow-y: auto; }",
    "}",
    "#no-element-has-this-id {",
    "  position: fixed;",
    "  top: 28px;",
    "  overflow-y: auto;",
    "}",
    "body {",
    "  top: 0;",
    "  overflow: hidden;",
    "}",
  ].join("\n");
  const sheet = parseSheet(planted);

  assert.equal(sheet.malformed, false, "the fixture is not what it claims");
  assert.ok(!sheet.stripped.includes("position: fixed; top: 28px; overflow-y: auto; } */"));
  assert.deepEqual(sheet.atRulePreludes, ["@media (min-width: 99999px)"]);
  // MUTANT 3 is visible as exactly what it is - a selector nothing matches.
  assert.ok(sheet.selectors.includes("#no-element-has-this-id"));

  const body = composedFor(planted, SCROLLPORT_SELECTOR);
  assert.equal(body.matched, 1, "only the unconditional rule composes onto body");
  // The planted body rule is read, so the grader is demonstrably not blind ...
  assert.equal(body.composed.get("top"), "0");
  assert.equal(body.composed.get("overflow"), "hidden");
  // ... and neither the comment, the dead media query nor the invented selector
  // put one declaration on it.
  assert.equal(body.composed.get("position"), undefined);
  assert.equal(body.composed.get("overflow-y"), undefined);

  // A selector no rule names is reported as absent rather than as empty.
  assert.equal(composedFor(planted, "html").matched, 0);
});

test("the injected sheet is unconditional and names only its declared selectors", () => {
  const sheet = parseSheet(DRAG_STRIP_CSS);
  assert.equal(sheet.malformed, false, "the sheet's braces do not balance");
  assert.ok(sheet.rules.length >= 4, `only ${sheet.rules.length} rule(s) parsed`);

  // MUTANT 4. A media query that can never match is indistinguishable from one
  // that always does when a sheet is graded as text. The shell injects this
  // into exactly one window whose size it chose itself, so there is no
  // condition here for an at-rule to express and its presence IS the fault.
  assert.deepEqual(
    sheet.atRulePreludes,
    [],
    "the drag strip's geometry must not be conditional on anything",
  );

  // MUTANT 3. Tokens parked on a selector the page does not have satisfied
  // every unscoped assertion while declaring nothing about any real element.
  const undeclared = sheet.selectors.filter((one) => !DECLARED_SELECTORS.includes(one));
  assert.deepEqual(undeclared, [], "the sheet names a selector this shell has not decided on");
});

test("the drag strip insets the scrollport rather than covering the page", () => {
  assert.ok(Number.isInteger(DRAG_STRIP_HEIGHT));
  assert.ok(DRAG_STRIP_HEIGHT > 0);
  // Thin. A strip deep enough to hide a heading is not a title bar substitute,
  // it is a hole in the page.
  assert.ok(DRAG_STRIP_HEIGHT <= 40, "the strip must stay thin");

  const found = composedFor(DRAG_STRIP_CSS, SCROLLPORT_SELECTOR);
  assert.equal(found.matched, 1, "exactly one rule may declare the scrollport");
  const scrollport = found.composed;

  // MUTANT 1. Deleting this one declaration leaves `top` inert - an unpositioned
  // box ignores it - so the scrollport goes back to starting at the viewport top
  // and the band goes back to covering the first rows of content. The old arm
  // matched `top` anywhere in the sheet and so could not tell the difference.
  assert.equal(
    scrollport.get("position"),
    "fixed",
    "an unpositioned scrollport ignores its own inset, which is CS-617 returning",
  );

  // MUTANT 2. The inset and the band's height are one constant, and the old arm
  // was satisfied by either of them appearing anywhere - so swapping them
  // passed. Both are asserted here against the element that has to carry them.
  assert.equal(
    scrollport.get("top"),
    `${DRAG_STRIP_HEIGHT}px`,
    "the scrollport must start below the band, not at the viewport top",
  );
  assert.equal(scrollport.get("right"), "0");
  assert.equal(scrollport.get("bottom"), "0");
  assert.equal(scrollport.get("left"), "0");
  assert.equal(scrollport.get("margin"), "0");

  // MUTANT 3 clipped the scrollport to a sliver. A scrollport that does not
  // scroll is a hole in the page rather than a viewport.
  assert.ok(
    SCROLLING_OVERFLOW.includes(scrollport.get("overflow-y")),
    `the inset scrollport must scroll, and declares overflow-y ${scrollport.get("overflow-y")}`,
  );
  assert.ok(
    !CLIPPING_OVERFLOW.includes(scrollport.get("overflow")),
    "a clipping shorthand on the scrollport overrides the axis declarations after it",
  );

  // THIS USED TO REQUIRE A padding-top AND SO ENCODED THE DEFECT. A padding
  // reserves space in DOCUMENT flow while the band is fixed to the VIEWPORT, so
  // the two coincide only at scroll offset zero - CS-617 measured the band
  // swallowing real content at a body scroll of 369. What keeps the page clear
  // is the scrollport starting below the band, which is geometric rather than
  // positional. Asserted per element now, so a padding on some other selector
  // is not what this arm is talking about.
  assert.equal(scrollport.get("padding-top"), undefined);
  assert.equal(scrollport.get("padding"), undefined);
});

test("the drag band sits at the viewport top and is exactly the strip's height", () => {
  const found = composedFor(DRAG_STRIP_CSS, BAND_SELECTOR);
  assert.equal(found.matched, 1, "exactly one rule may declare the band");
  const band = found.composed;

  // A pseudo-element with no content property generates no box at all, and a
  // band that generates no box is a frameless window nobody can move.
  assert.ok(band.has("content"), "a pseudo-element with no content generates no box");
  assert.equal(band.get("position"), "fixed");
  assert.equal(band.get("top"), "0", "the band belongs at the viewport top");
  assert.equal(band.get("left"), "0");
  assert.equal(band.get("right"), "0");
  assert.equal(band.get("height"), `${DRAG_STRIP_HEIGHT}px`);
});

// MUTANT 2 STATED AS THE RELATION IT BREAKS. Both tops are present in the sheet
// either way round, so only their assignment to elements separates the repair
// from the defect - and the band's height and the scrollport's inset are one
// constant, which is what stops them drifting apart under a later edit.
test("the band's top and the scrollport's inset are not interchangeable", () => {
  const band = composedFor(DRAG_STRIP_CSS, BAND_SELECTOR).composed;
  const scrollport = composedFor(DRAG_STRIP_CSS, SCROLLPORT_SELECTOR).composed;

  assert.notEqual(
    band.get("top"),
    scrollport.get("top"),
    "a band and a scrollport sharing one top means one of them is in the wrong place",
  );
  assert.equal(
    band.get("height"),
    scrollport.get("top"),
    "the band's height and the scrollport's inset are generated from one constant",
  );
});

// MEASURED, not reasoned. Removing this declaration does not merely change
// which element scrolls - it stops ANYTHING scrolling. With the root's overflow
// left visible, the fixed body's overflow-y propagates to the viewport, the
// body's own used overflow becomes visible, and the viewport has no in-flow
// content to scroll because the body is out of flow. Driven in headless Chrome
// at the shell's own default window size: with this line the body scrolls to
// 223 of 447; with it deleted and nothing else changed, setting a scroll offset
// on any element in the document leaves every one of them at 0.
test("the root stops scrolling, which is what lets the inset scrollport scroll", () => {
  const found = composedFor(DRAG_STRIP_CSS, ROOT_SELECTOR);
  assert.equal(found.matched, 1, "exactly one rule may declare the root");
  assert.ok(
    CLIPPING_OVERFLOW.includes(found.composed.get("overflow")),
    "without a clipping root the body's overflow propagates to the viewport and " +
      "nothing in the document scrolls at all",
  );
});

// CS-873. clockspeed/surface/web/app.css records in capitals that there is
// DELIBERATELY no sideways clip on the body, because the scrollbar is the only
// signal a reader or an auditor gets that something has burst its container and
// clipping it swallows the evidence rather than the fault. That decision has a
// green named arm of its own - and the arm reads app.css, so an injected sheet
// arriving from the shell voids the decision across a seam no arm crosses.
// 896a682 did exactly that. This is the arm on the other side of the seam.
//
// Leaving the axis undeclared is not an oversight, it is the repair: a box with
// a scrolling overflow-y and no overflow-x computes the missing axis to `auto`,
// so sideways overflow gets a scrollbar rather than a clip. Measured on the
// composed page - the body's computed overflow-x reads `hidden` with the
// declaration present and `auto` with it gone.
test("the injected sheet does not clip the body's sideways overflow", () => {
  const scrollport = composedFor(DRAG_STRIP_CSS, SCROLLPORT_SELECTOR).composed;
  assert.ok(
    !CLIPPING_OVERFLOW.includes(scrollport.get("overflow-x")),
    "app.css keeps the body's sideways scrollbar as the only signal that " +
      "something has burst its container - the shell must not clip it away",
  );
  assert.ok(
    !CLIPPING_OVERFLOW.includes(scrollport.get("overflow")),
    "a clipping shorthand hides the sideways overflow just as thoroughly",
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
