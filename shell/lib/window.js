"use strict";

// CS-602 slice S4 - what the companion window IS, as a plain object.
//
// PURE BY CONTRACT, and for the same reason geometry.js is. This module
// requires nothing at all - not electron, not the filesystem, not a clock.
// electron 44.0.0 declares no postinstall, so the package holds no binary until
// something asks for one, and the first import of it starts a large lazy
// download at run time. Keeping the window's whole contract in a plain object
// and a plain string is what lets it be graded in CI on a machine with no
// electron binary and no display server, which is the machine BOOTSTRAP.md
// section 5.4 requires the rule suite to run on.
//
// THE PURITY GUARD READS THIS FILE AS TEXT AND CANNOT TELL CODE FROM COMMENT,
// so the forbidden call is not spelled out anywhere above - naming it in prose,
// even to explain why it is absent, is enough to fail the scan. Anyone editing
// this header should describe the call rather than write it.
//
// WHY THE SECURITY PREFERENCES ARE WRITTEN DOWN THOUGH THEY ARE THE DEFAULTS.
// contextIsolation is true by default, nodeIntegration false, and sandbox true
// since electron 20. Relying on that makes this window's security posture a
// property of whichever electron is installed rather than of this file. An
// upstream release that moved one of those defaults would silently move this
// window with it, and nothing here or in the suite would have changed. Stating
// them costs three lines and converts an inherited default into a decision this
// project has made and can be held to.
//
// WHY OVERRIDES ARE AN ALLOW LIST AND NOT A MERGE. A caller hands in geometry
// and a preference, which vary per launch. The frame, the floor and the three
// preferences do not vary and are not the caller's to move. A spread merge
// would make every one of them reachable from outside - including from a state
// file, which is operator-editable and, being JSON, is exactly the kind of
// input that ends up carrying fields nobody meant it to carry.

/**
 * The window modes this shell declares.
 *
 * OVERLAY IS DECLARED AND NOT IMPLEMENTED, DELIBERATELY. BOOTSTRAP.md section
 * 7.3 settles the in-game overlay as a later flagged MODE of this same shell,
 * default off, degrading to the companion on bind failure - rather than as a
 * second application. Naming the slot now is what keeps that a mode. Leaving it
 * to throw is what stops it being half built: a slot that quietly returned
 * companion options would let the overlay path be "supported" by a window that
 * is not an overlay, and the day someone wired a flag to it the failure would
 * be a companion window appearing in the wrong place rather than a refusal.
 */
const MODES = Object.freeze({
  COMPANION: "COMPANION",
  OVERLAY: "OVERLAY",
});

const DEFAULT_MODE = MODES.COMPANION;

// The smallest window this shell will produce. Electron's own default for both
// is 0, which is a window that can be dragged shut into an invisible sliver.
//
// This is NOT the same fact as state.js's MIN_WIDTH / MIN_HEIGHT, and the two
// are deliberately not one constant. state.js's floor is a corruption
// threshold - a state file asking for something smaller is junk and is
// discarded. This floor is what the operating system lets the operator drag
// down to. What has to hold is the ORDER between them: a window resized to this
// floor must read back as valid rather than as corrupt. window.test.js asserts
// that relation, so either side can move without silently breaking restore.
const MIN_WIDTH = 640;
const MIN_HEIGHT = 480;

/** How deep the injected drag strip is, in CSS pixels. */
const DRAG_STRIP_HEIGHT = 28;

/**
 * What a caller may set. Everything absent from this list is this module's.
 *
 * `preload` is here because it is an absolute path, and this module has no
 * filesystem and no idea where it is installed. The caller that knows resolves
 * it; buildWindowOptions only decides where it lands.
 */
const OVERRIDABLE_KEYS = Object.freeze([
  "alwaysOnTop",
  "x",
  "y",
  "width",
  "height",
  "preload",
]);

const ALWAYS_ON_TOP_ENV = "CLOCKSPEED_ALWAYS_ON_TOP";
const ALWAYS_ON_TOP_FLAG = "--always-on-top";
const NO_ALWAYS_ON_TOP_FLAG = "--no-always-on-top";

// Exact tokens, compared lower case and trimmed. Anything else is not an
// answer and falls through to the next source rather than being guessed at.
const TRUTHY = Object.freeze(new Set(["1", "true", "yes", "on"]));
const FALSEY = Object.freeze(new Set(["0", "false", "no", "off"]));

/** A mode was named that this shell does not declare. */
class UnknownModeError extends Error {
  constructor(mode) {
    // The mode is caller-supplied text and is NOT interpolated into the
    // message. Every declared mode is a fixed identifier, so naming the
    // rejected one adds nothing a reader needs, and rendering caller text
    // through an error path is how a value nobody audited reaches a log.
    super("the window mode is not one this shell declares");
    this.name = "UnknownModeError";
    this.mode = mode;
  }
}

/** A declared mode that has not been built yet. */
class ModeNotImplementedError extends Error {
  constructor(mode) {
    super("the overlay window mode is declared but not implemented");
    this.name = "ModeNotImplementedError";
    this.mode = mode;
  }
}

/**
 * The CSS the shell injects to give a frameless window something to drag by.
 *
 * WHY THIS EXISTS AT ALL. `frame: false` removes the OS title bar, and with it
 * the only region the window manager treats as a drag handle. Without a
 * replacement the operator cannot move the window, which would make the whole
 * of state.js - remembering where it was put - describe a position that can
 * never be changed.
 *
 * WHY THE SHELL INJECTS IT RATHER THAN THE PAGE CARRYING IT. The dashboard is
 * served to an ordinary browser as well, where `app-region` means nothing and a
 * 28px dead strip across the top would be a defect. The strip is a property of
 * being hosted in a frameless window, so it belongs to the host.
 *
 * WHY IT MOVES THE SCROLLPORT INSTEAD OF PADDING THE PAGE. A drag region
 * swallows the pointer, so a strip sitting on top of the first 28px makes
 * whatever is up there unclickable - and the fault presents as "this control
 * does nothing sometimes" rather than as anything pointing here.
 *
 * THIS COMMENT USED TO SAY A body padding-top PUSHED THE PAGE CLEAR SO THE
 * STRIP COVERED NOTHING, AND THAT WAS FALSE FOR ANY SCROLLED PAGE (CS-617).
 * The padding reserves space in DOCUMENT flow; `body::before` is `position:
 * fixed` and stays at the VIEWPORT top. The two coincide only at scroll offset
 * zero. MEASURED on the composed page: at a body scroll of 369,
 * `document.elementFromPoint` returned the band for every y from 0 to 27, and
 * deleting only the `body::before` rule at the identical offset returned
 * `p.lede` - real page content, being swallowed.
 *
 * SO THE SCROLLPORT NOW STARTS BELOW THE BAND. `html` stops scrolling and the
 * body becomes a fixed scroller inset by the strip's height, which makes it
 * geometrically impossible for content to pass beneath the band at any offset
 * rather than merely unlikely. Re-measured the same way afterwards: with the
 * band deleted, the strip's area holds `html` and nothing else, at scroll 0,
 * mid and maximum, sweeping the full width at 1574 and at 375.
 *
 * THE ROOT'S CLIP IS LOAD BEARING AND IS NOT MERELY TIDINESS. Delete it and
 * nothing in the document scrolls at all: with the root's overflow left
 * visible, the fixed body's `overflow-y` propagates to the viewport, the body's
 * own used overflow becomes visible, and the viewport has no in-flow content to
 * scroll because the body is out of flow. Measured in headless Chrome at the
 * shell's default window size - with the clip the body scrolls to 223 of 447,
 * and with it deleted every element in the document stays pinned at 0.
 *
 * THERE IS DELIBERATELY NO SIDEWAYS CLIP ON THE BODY (CS-873). An earlier cut
 * of this rule carried one, which silently voided a decision the dashboard's
 * own stylesheet records in capitals: the sideways scrollbar is the only signal
 * a reader or an auditor gets that something has burst its container, and
 * clipping it swallows the evidence rather than the fault. That decision has a
 * green arm of its own and the arm reads the stylesheet, so a sheet injected
 * from HERE voided it across a seam no arm crossed. Leaving the axis undeclared
 * is the repair rather than an omission: a box with a scrolling `overflow-y`
 * and no `overflow-x` computes the missing axis to `auto`, so sideways overflow
 * gets a scrollbar. Measured on the composed page - the body's computed
 * sideways overflow reads `hidden` with the declaration present and `auto`
 * without it.
 *
 * WHAT THIS SHAPE COSTS, MEASURED AND STILL OWED (CS-872). A non-root scroller
 * is not the default keyboard scroll target. With nothing focused, Chromium
 * starts its scroll chain at the document element and walks UP, so the body
 * scroller - a descendant - is never reached and PageDown, Space and ArrowDown
 * all do nothing until a click, the wheel or one Tab moves focus into the page.
 * Measured on the composed page at the shell's default window size: the page
 * with no injected sheet scrolls 419 on a cold PageDown, and with this sheet 0.
 *
 * THE CSS-ONLY SPACE IS ARGUED SHUT, NOT MEASURED SHUT - THIS PARAGRAPH USED
 * TO CLAIM THE REVERSE AND SO CREDITED THE WRONG HALF. Seven shapes went
 * through one headless harness: every one that scrolled on a cold PageDown put
 * real page content back under the band at a nonzero offset, and every one that
 * kept the strip clear was keyboard-dead. That is seven failures, not a closed
 * design space.
 *
 * THE PART THAT GENERALIZES IS THE ARGUMENT. Making the ROOT the inset fixed
 * scroller cannot work, and not because it was tried: in standards mode the
 * root element's scrollTop, scrollHeight and clientHeight ARE the viewport's,
 * so positioning the root out of flow leaves the viewport with nothing in flow
 * to scroll. That is CSSOM View semantics, and it holds with no browser in the
 * room. The harness agreed at 705 of 705 - unscrollable both ways at once - but
 * agreement is a check on the argument, not its support.
 *
 * THE GAPS, PLAINLY. The harness IS NOT CHECKED IN: nothing tracked here
 * re-runs those seven shapes, so no later session and no CI can reproduce the
 * figures and this comment is the whole record. And what it measured is default
 * scrolling driven by a SYNTHETIC key - the mechanism behind three false
 * findings against this harness in the same cycle - so the mechanism is
 * harness-local too, not only the numbers.
 *
 * WHAT THE HEDGE DOES NOT REACH IS THE SIGN. The conclusion is NEGATIVE, and
 * the constraint the harness omitted - the drag region must keep working - can
 * only shrink the feasible set, so no false negative arrives by that route. The
 * cure is very probably not in this sheet: a drag region the OS draws OUTSIDE
 * the web contents, a window option rather than a stylesheet, which no test in
 * this repo can grade for the same reason the app-region declarations cannot
 * be. THAT REMAINS OWED, alongside the drag itself.
 *
 * THE app-region DECLARATIONS ARE DELIBERATELY UNTOUCHED BY THAT REPAIR. The
 * other candidate fix was `pointer-events: none` on the band, and whether
 * Chromium still honours a drag region on a pointer-transparent element is
 * exactly the question no test here can answer - shell/node_modules does not
 * exist in a fresh clone and this module is graded without electron on purpose.
 * A fix that cannot break dragging was preferred over a fix that might.
 * VERIFYING THE DRAG ITSELF AGAINST A REAL ELECTRON IS STILL OWED; it is one of
 * the checks docs/OPERATIONS.md section 8.3 lists as performed by no machine.
 *
 * THE no-drag RULES ARE BELT AND BRACES ON TOP OF THAT. The inset scrollport is
 * what stops the strip covering content. These rules are what stops an
 * interactive element being swallowed anyway if the page later grows something
 * that reaches into the band, and `.no-drag` is the escape any future markup
 * can name explicitly. NOTE WHAT THEY DO NOT DO: they set `app-region` on
 * elements BENEATH the band, and the band is a fixed pseudo-element painted
 * above them, so they were never able to release a point the band covers. That
 * is why adding `.scroll-x` to the list was rejected as the repair.
 *
 * BOTH SPELLINGS ARE PRESENT. `-webkit-app-region` is what Chromium honours
 * today; `app-region` is the standard property it is being renamed to. Shipping
 * only the prefixed one dates the file, and only the standard one would not
 * work at all right now.
 */
const DRAG_STRIP_CSS = [
  "/* Clockspeed companion shell - injected drag strip for a frameless window. */",
  "html {",
  "  height: 100%;",
  "  overflow: hidden;",
  "}",
  "body {",
  "  position: fixed;",
  `  top: ${DRAG_STRIP_HEIGHT}px;`,
  "  right: 0;",
  "  bottom: 0;",
  "  left: 0;",
  "  margin: 0;",
  "  overflow-y: auto;",
  "}",
  "body::before {",
  '  content: "";',
  "  position: fixed;",
  "  top: 0;",
  "  left: 0;",
  "  right: 0;",
  `  height: ${DRAG_STRIP_HEIGHT}px;`,
  "  z-index: 2147483647;",
  "  -webkit-app-region: drag;",
  "  app-region: drag;",
  "}",
  "a, button, input, select, textarea, summary, label,",
  '[role="button"], [role="link"], [contenteditable], .no-drag {',
  "  -webkit-app-region: no-drag;",
  "  app-region: no-drag;",
  "}",
  "",
].join("\n");

/** True only for an exact affirmative token. */
function readToken(value) {
  if (typeof value !== "string") {
    return null;
  }
  const token = value.trim().toLowerCase();
  if (TRUTHY.has(token)) {
    return true;
  }
  if (FALSEY.has(token)) {
    return false;
  }
  return null;
}

/**
 * Decide whether the window pins itself above everything else.
 *
 * THIS IS A DECISION AND SO IT LIVES HERE. main.js is wiring, and a precedence
 * order between three sources is not wiring - it is the kind of rule that grows
 * a fourth source and an off-by-one and has nowhere to be tested. Keeping it
 * pure means the whole precedence table is graded in CI without electron.
 *
 * The order is flag, then environment, then the remembered preference, then
 * false. A launch flag is the most deliberate thing the operator can do and so
 * outranks the file; the environment sits between them because it is set once
 * per shell rather than per launch.
 *
 * THE NEGATIVE FLAG BEATS THE POSITIVE. With both present the operator has
 * contradicted themselves and one of the two answers is recoverable while the
 * other is not: a window that failed to pin is a nuisance, and a window pinned
 * over everything on a machine whose input is misbehaving is the one you cannot
 * click your way out of. The safe direction is down.
 *
 * EVERYTHING UNUSABLE FALLS TO FALSE. Not to the default, not to the persisted
 * value - to false. This mirrors state.js, which forces a non-boolean
 * alwaysOnTop down to false for the same reason: a window that silently pins
 * itself because something upstream was garbage is a bug the operator has to
 * hunt with the window in the way.
 *
 * @param {object} [sources]
 * @param {boolean} [sources.persisted] The remembered preference.
 * @param {Array<string>} [sources.argv] Launch arguments, matched exactly.
 * @param {Object<string,string>} [sources.env] The environment to read.
 * @returns {boolean}
 */
function resolveAlwaysOnTop(sources) {
  const input = sources !== null && typeof sources === "object" ? sources : {};

  const argv = Array.isArray(input.argv) ? input.argv : [];
  // Exact equality, never a prefix or an includes(). "--always-on-top=1" is not
  // this flag, and a startsWith would also match "--always-on-top-never".
  if (argv.includes(NO_ALWAYS_ON_TOP_FLAG)) {
    return false;
  }
  if (argv.includes(ALWAYS_ON_TOP_FLAG)) {
    return true;
  }

  const env = input.env !== null && typeof input.env === "object" ? input.env : {};
  const fromEnv = readToken(env[ALWAYS_ON_TOP_ENV]);
  if (fromEnv !== null) {
    return fromEnv;
  }

  return input.persisted === true;
}

/**
 * Build the options for one BrowserWindow.
 *
 * @param {string} [mode] A member of `MODES`. Omitted means `DEFAULT_MODE`.
 * @param {object} [overrides] Only `OVERRIDABLE_KEYS` are read.
 * @returns {object} A fresh options object, safe for the caller to keep.
 * @throws {UnknownModeError} `mode` is not a declared mode.
 * @throws {ModeNotImplementedError} `mode` is declared but not built.
 */
function buildWindowOptions(mode, overrides) {
  const chosen = mode === undefined || mode === null ? DEFAULT_MODE : mode;

  // Unknown before unimplemented. A typo and a known-but-absent mode are
  // different faults and a caller handling one should not catch the other.
  if (!Object.hasOwn(MODES, chosen) || MODES[chosen] !== chosen) {
    throw new UnknownModeError(chosen);
  }
  if (chosen === MODES.OVERLAY) {
    throw new ModeNotImplementedError(chosen);
  }

  const given = overrides !== null && typeof overrides === "object" ? overrides : {};
  const taken = {};
  for (const key of OVERRIDABLE_KEYS) {
    if (Object.hasOwn(given, key)) {
      taken[key] = given[key];
    }
  }

  const options = {
    frame: false,
    resizable: true,
    minWidth: MIN_WIDTH,
    minHeight: MIN_HEIGHT,
    alwaysOnTop: taken.alwaysOnTop === true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  };

  for (const key of ["x", "y"]) {
    if (Number.isInteger(taken[key])) {
      options[key] = taken[key];
    }
  }

  // Raised to the floor rather than passed on as given. A width under minWidth
  // is a self-contradicting options object, and which half of the contradiction
  // electron honours is not something this module should be finding out about
  // one layer downstream of itself.
  if (Number.isInteger(taken.width)) {
    options.width = Math.max(taken.width, MIN_WIDTH);
  }
  if (Number.isInteger(taken.height)) {
    options.height = Math.max(taken.height, MIN_HEIGHT);
  }

  if (typeof taken.preload === "string" && taken.preload.length > 0) {
    options.webPreferences.preload = taken.preload;
  }

  return options;
}

module.exports = {
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
  UnknownModeError,
  ModeNotImplementedError,
  buildWindowOptions,
  resolveAlwaysOnTop,
};
