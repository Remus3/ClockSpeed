"use strict";

// CS-602 slice S3 - tests for shell/lib/geometry.js.
//
// WHY THE reason FIELD IS ASSERTED EVERYWHERE: a test that only checks the
// returned numbers passes for the wrong reason. Centring the defaults on the
// primary work area produces the SAME rectangle whether the saved state was
// absent (DEFAULTED) or whether it named a monitor that has since been
// unplugged (DISPLAY_GONE). Only the reason separates them, so only the reason
// can prove the branch under test actually ran.
//
// This module is pure by contract - no filesystem, no electron. The work areas
// arrive as plain rectangles. In the real application they come from
// screen.getAllDisplays().map((d) => d.workArea), but geometry.js never knows
// that, and that purity is what makes this file runnable in CI on a machine
// with no display server at all.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const geometry = require("../lib/geometry.js");
const { resolveBounds, REASONS, MIN_VISIBLE } = geometry;

// A 1920x1080 primary at the origin, and a second monitor to its right. The
// second one exists so that "picks the work area with the largest overlap" can
// be told apart from "always uses workAreas[0]".
const WA_PRIMARY = Object.freeze({ x: 0, y: 0, width: 1920, height: 1080 });
const WA_SECOND = Object.freeze({ x: 1920, y: 0, width: 1920, height: 1080 });
// A smaller secondary, used where the chosen monitor has to change the answer.
const WA_SMALL_SECOND = Object.freeze({ x: 1920, y: 0, width: 1280, height: 720 });

const DEFAULTS = Object.freeze({ width: 1100, height: 800 });
const MINIMUM = Object.freeze({ width: 640, height: 480 });

// Centring 1100x800 on the primary: (1920-1100)/2 = 410, (1080-800)/2 = 140.
// Spelled out rather than recomputed, so that a bug in the centring arithmetic
// cannot be mirrored by the same bug in the expectation.
const CENTRED_ON_PRIMARY = Object.freeze({ x: 410, y: 140, width: 1100, height: 800 });

function resolve(saved, workAreas) {
  return resolveBounds({
    saved,
    workAreas: workAreas || [WA_PRIMARY],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
}

// --- the exported vocabulary ------------------------------------------------

test("REASONS exports exactly the six documented outcomes", () => {
  assert.deepEqual(
    Object.keys(REASONS).sort(),
    ["CLAMPED", "DEFAULTED", "DISPLAY_GONE", "NUDGED", "RESTORED"].sort()
  );
  // Each reason is its own distinct string, so a test asserting one cannot
  // accidentally be satisfied by another.
  const values = Object.values(REASONS);
  assert.equal(new Set(values).size, values.length);
});

test("MIN_VISIBLE is a positive integer number of pixels", () => {
  assert.equal(typeof MIN_VISIBLE, "number");
  assert.ok(Number.isInteger(MIN_VISIBLE));
  assert.ok(MIN_VISIBLE > 0);
});

// --- DEFAULTED: there was no usable saved rectangle at all ------------------

test("DEFAULTED when saved is null - defaults centred on the primary", () => {
  const result = resolve(null);
  assert.equal(result.reason, REASONS.DEFAULTED);
  assert.deepEqual(result.bounds, CENTRED_ON_PRIMARY);
});

// Every shape that is not a usable rectangle. Each gets its own named test so
// that a regression names the exact input that broke, rather than collapsing
// eleven distinct faults into one red line.
const INVALID_SAVED = [
  ["undefined", undefined],
  ["a number", 42],
  ["a string", "1100x800"],
  ["an array", [0, 0, 1100, 800]],
  ["an empty object", {}],
  ["missing width", { x: 0, y: 0, height: 800 }],
  ["missing y", { x: 0, width: 1100, height: 800 }],
  ["a NaN coordinate", { x: NaN, y: 0, width: 1100, height: 800 }],
  ["an Infinite coordinate", { x: Infinity, y: 0, width: 1100, height: 800 }],
  ["a fractional coordinate", { x: 1.5, y: 0, width: 1100, height: 800 }],
  ["a string coordinate", { x: "0", y: 0, width: 1100, height: 800 }],
  ["a zero width", { x: 0, y: 0, width: 0, height: 800 }],
  ["a negative height", { x: 0, y: 0, width: 1100, height: -800 }],
];

for (const [label, saved] of INVALID_SAVED) {
  test(`DEFAULTED when saved is ${label}`, () => {
    const result = resolve(saved);
    assert.equal(result.reason, REASONS.DEFAULTED);
    assert.deepEqual(result.bounds, CENTRED_ON_PRIMARY);
  });
}

// --- DISPLAY_GONE: a valid rectangle, but its monitor is not here -----------

test("DISPLAY_GONE when saved intersects no work area at all", () => {
  // A perfectly well formed rectangle, off to the lower right of everything.
  // This is the arm that DEFAULTED must not be allowed to swallow: the input
  // is valid, so the distinction is entirely carried by the reason.
  const result = resolve({ x: 3000, y: 2000, width: 800, height: 600 });
  assert.equal(result.reason, REASONS.DISPLAY_GONE);
  assert.deepEqual(result.bounds, CENTRED_ON_PRIMARY);
});

test("DISPLAY_GONE when the monitor that held the window has been unplugged", () => {
  // Saved on the second monitor, then resolved with only the primary present.
  const saved = { x: 2100, y: 100, width: 1100, height: 800 };
  const stillThere = resolve(saved, [WA_PRIMARY, WA_SECOND]);
  assert.equal(stillThere.reason, REASONS.RESTORED);

  const unplugged = resolve(saved, [WA_PRIMARY]);
  assert.equal(unplugged.reason, REASONS.DISPLAY_GONE);
  assert.deepEqual(unplugged.bounds, CENTRED_ON_PRIMARY);
});

test("DISPLAY_GONE touching an edge only is not a real intersection", () => {
  // The right edge of the window lands exactly on the left edge of the work
  // area. Zero overlapping pixels, so this is DISPLAY_GONE and not NUDGED.
  const result = resolve({ x: -1100, y: 100, width: 1100, height: 800 });
  assert.equal(result.reason, REASONS.DISPLAY_GONE);
});

// --- NUDGED: on screen, but not usefully so ---------------------------------

test("NUDGED when fewer than MIN_VISIBLE pixels remain on screen", () => {
  // 20 columns of the window overlap the primary - a real intersection, so not
  // DISPLAY_GONE, but far below the visibility floor.
  const result = resolve({ x: 1900, y: 100, width: 1100, height: 800 });
  assert.equal(result.reason, REASONS.NUDGED);
  // "Shift fully into that work area": x is pulled back to the rightmost
  // position that still fits, 1920 - 1100 = 820. y already fits and is left be.
  assert.deepEqual(result.bounds, { x: 820, y: 100, width: 1100, height: 800 });
});

test("NUDGED when saved.y sits above the work area top", () => {
  // 770 of 800 rows are visible, which is far more than MIN_VISIBLE, so the
  // visibility rule alone would leave this alone. It is still nudged, because
  // a title bar above the top of the work area cannot be grabbed. This arm is
  // what separates the y rule from the MIN_VISIBLE rule.
  const result = resolve({ x: 400, y: -30, width: 1100, height: 800 });
  assert.equal(result.reason, REASONS.NUDGED);
  assert.deepEqual(result.bounds, { x: 400, y: 0, width: 1100, height: 800 });
  assert.ok(800 - 30 > MIN_VISIBLE, "the y arm must not be reachable via MIN_VISIBLE");
});

test("NUDGED shifts x left as well when the window hangs off the right", () => {
  const result = resolve({ x: 1890, y: 100, width: 1100, height: 800 });
  assert.equal(result.reason, REASONS.NUDGED);
  assert.equal(result.bounds.x, 820);
});

// --- CLAMPED: it simply does not fit ----------------------------------------

test("CLAMPED when saved is larger than its work area", () => {
  const small = { x: 0, y: 0, width: 1280, height: 720 };
  const result = resolveBounds({
    saved: { x: 0, y: 0, width: 1600, height: 900 },
    workAreas: [small],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(result.reason, REASONS.CLAMPED);
  assert.deepEqual(result.bounds, { x: 0, y: 0, width: 1280, height: 720 });
});

test("CLAMPED outranks NUDGED when a window is both oversized and adrift", () => {
  // Oversized AND mostly off the right hand edge. Resizing is the larger of
  // the two changes, so CLAMPED is the reported reason - but the position must
  // still be corrected, which is what the bounds assertion pins.
  const small = { x: 0, y: 0, width: 1280, height: 720 };
  const result = resolveBounds({
    saved: { x: 1270, y: 0, width: 1600, height: 900 },
    workAreas: [small],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(result.reason, REASONS.CLAMPED);
  assert.deepEqual(result.bounds, { x: 0, y: 0, width: 1280, height: 720 });
});

test("CLAMPED never shrinks a window below the stated minimum", () => {
  // A work area smaller than the minimum window size. Clamping to the work
  // area would produce an unusable window, so the minimum wins.
  const tiny = { x: 0, y: 0, width: 400, height: 300 };
  const result = resolveBounds({
    saved: { x: 0, y: 0, width: 1600, height: 900 },
    workAreas: [tiny],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(result.reason, REASONS.CLAMPED);
  assert.equal(result.bounds.width, MINIMUM.width);
  assert.equal(result.bounds.height, MINIMUM.height);
});

// --- RESTORED: the ordinary case --------------------------------------------

test("RESTORED returns saved unchanged when it fits and is visible", () => {
  const saved = { x: 100, y: 100, width: 1100, height: 800 };
  const result = resolve(saved);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, saved);
});

test("RESTORED on a non-primary monitor uses that monitor, not workAreas[0]", () => {
  // Fully inside the second work area. An implementation that always reasons
  // about workAreas[0] would report DISPLAY_GONE or NUDGED here.
  const saved = { x: 2000, y: 100, width: 1100, height: 800 };
  const result = resolve(saved, [WA_PRIMARY, WA_SECOND]);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, saved);
});

test("RESTORED does not hand back the caller's own saved object", () => {
  // The caller must be free to mutate what it passed in without the resolved
  // bounds changing underneath the window.
  const saved = { x: 100, y: 100, width: 1100, height: 800 };
  const result = resolve(saved);
  assert.notEqual(result.bounds, saved);
  saved.x = 9999;
  assert.equal(result.bounds.x, 100);
});

test("a straddling window that is amply visible is left where it is", () => {
  // 100 columns on the primary, 1000 on the second. A window spanning two
  // monitors is ordinary and perfectly usable, so it is NOT herded onto one of
  // them. Dragging it back every launch would be the bug, not the fix.
  const result = resolve({ x: 1820, y: 100, width: 1100, height: 800 }, [WA_PRIMARY, WA_SECOND]);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, { x: 1820, y: 100, width: 1100, height: 800 });
});

test("a straddling window is sized against the monitor holding most of it", () => {
  // A 1400x900 window with 20 columns on the big primary and 1280 on the small
  // secondary. The secondary holds the bulk, and the window does not fit there.
  //
  // This is the arm that pins home selection. Picking workAreas[0] instead
  // would find 1400x900 fits the 1920x1080 primary, report NUDGED, and land x
  // at 520 - a different reason AND a different rectangle, so the assertion
  // cannot be satisfied by the wrong monitor.
  const result = resolveBounds({
    saved: { x: 1900, y: 0, width: 1400, height: 900 },
    workAreas: [WA_PRIMARY, WA_SMALL_SECOND],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(result.reason, REASONS.CLAMPED);
  assert.deepEqual(result.bounds, { x: 1920, y: 0, width: 1280, height: 720 });
});

// --- degenerate inputs ------------------------------------------------------

test("resolveBounds never throws on an empty or absent work area list", () => {
  for (const workAreas of [[], undefined, null, "not a list"]) {
    const result = resolveBounds({
      saved: { x: 100, y: 100, width: 1100, height: 800 },
      workAreas,
      defaults: DEFAULTS,
      minimum: MINIMUM,
    });
    assert.equal(result.reason, REASONS.DEFAULTED);
    assert.ok(Number.isInteger(result.bounds.width));
  }
});

test("resolveBounds ignores malformed entries in the work area list", () => {
  const saved = { x: 100, y: 100, width: 1100, height: 800 };
  const result = resolve(saved, [null, { x: 0, y: 0, width: NaN, height: 1080 }, WA_PRIMARY]);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, saved);
});

test("resolveBounds never throws when called with no argument at all", () => {
  const result = resolveBounds();
  assert.equal(typeof result.reason, "string");
  assert.ok(Number.isInteger(result.bounds.width));
});

test("every returned bound is an integer", () => {
  // Electron rejects fractional bounds. Odd-sized work areas are the usual way
  // a half pixel sneaks in through the centring division.
  const odd = { x: 0, y: 0, width: 1367, height: 769 };
  for (const saved of [null, { x: 3000, y: 3000, width: 801, height: 601 }]) {
    const result = resolveBounds({ saved, workAreas: [odd], defaults: DEFAULTS, minimum: MINIMUM });
    for (const key of ["x", "y", "width", "height"]) {
      assert.ok(Number.isInteger(result.bounds[key]), `${key} was ${result.bounds[key]}`);
    }
  }
});

// --- the purity contract ----------------------------------------------------

test("geometry.js does not require electron and touches no filesystem", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "lib", "geometry.js"), "utf8");
  assert.ok(!/require\(\s*["'](electron|node:fs|fs)["']\s*\)/.test(source));
});
