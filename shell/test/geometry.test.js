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
const { resolveBounds, REASONS, MIN_VISIBLE, USABLE_FRACTION } = geometry;

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

// CS-1361. The same two monitors as above, but addressed BY DISPLAY ID, which
// is what electron's screen.getAllDisplays() actually hands over. The ids are
// deliberately not 0, 1, 2 and deliberately not in order: an implementation
// that reached for displays[savedId] instead of matching on the id field would
// index out of the list rather than quietly finding the wrong monitor.
const DISPLAY_PRIMARY = Object.freeze({ id: 3, workArea: WA_PRIMARY, primary: true });
const DISPLAY_SMALL_SECOND = Object.freeze({ id: 4, workArea: WA_SMALL_SECOND, primary: false });

function resolveWith(saved, displays, workAreas) {
  return resolveBounds({
    saved,
    displays,
    workAreas,
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
}

// --- the exported vocabulary ------------------------------------------------

test("REASONS exports exactly the six documented outcomes", () => {
  // CS-1361: this comment claimed six while the array listed five. The sixth,
  // DISPLAY_ID_GONE, is the one the comment was always describing - a SAVED
  // DISPLAY ID naming a monitor that is not attached, which is a different
  // fault from well formed bounds landing on no attached display.
  assert.deepEqual(
    Object.keys(REASONS).sort(),
    ["CLAMPED", "DEFAULTED", "DISPLAY_GONE", "DISPLAY_ID_GONE", "NUDGED", "RESTORED"].sort()
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

test("USABLE_FRACTION is a number strictly between 0 and 1", () => {
  // Exported so main.js and this file name the same margin rather than each
  // carrying its own 0.96. Strictly inside 0 and 1 in both directions: at 1 it
  // would stop being a margin at all, and at 0 it would collapse every window
  // to the stated minimum.
  assert.equal(typeof USABLE_FRACTION, "number");
  assert.ok(USABLE_FRACTION > 0, `USABLE_FRACTION was ${USABLE_FRACTION}`);
  assert.ok(USABLE_FRACTION < 1, `USABLE_FRACTION was ${USABLE_FRACTION}`);
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
  // CS-1361 changed this expectation. It used to be the work area's own
  // 1280x720; the cap is now 96 percent of it, so a clamped window never
  // exactly covers the work area and can always be grabbed at an edge.
  // 1280 * 0.96 = 1228.8, floor 1228. 720 * 0.96 = 691.2, floor 691.
  // Position: x slides into the FULL area, highest = 1280 - 1228 = 52, and
  // saved x of 0 is already at or below that, so x stays 0. Same for y.
  assert.deepEqual(result.bounds, { x: 0, y: 0, width: 1228, height: 691 });
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
  // CS-1361 changed this expectation, from { x: 0, y: 0, 1280, 720 }.
  // Size: floor(1280 * 0.96) = 1228 by floor(720 * 0.96) = 691.
  // x: the window is slid into the FULL 1280 wide area, so the rightmost
  // position that still fits is 1280 - 1228 = 52, and saved x of 1270 is
  // pulled back to 52 rather than to 0 - it no longer has to leave room for a
  // full width window. y: 720 - 691 = 29 is the highest, and saved y of 0 is
  // already inside, so y stays 0. The move proves CLAMPED did not skip the
  // repositioning.
  assert.deepEqual(result.bounds, { x: 52, y: 0, width: 1228, height: 691 });
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
  // CS-1361 changed the size here, from the secondary's own 1280x720 to 96
  // percent of it: floor(1280 * 0.96) = 1228 by floor(720 * 0.96) = 691.
  // x is still 1920 - the window is slid into the full secondary work area,
  // whose leftmost position is its own origin, 1920. y: 720 - 691 = 29 is the
  // highest y that fits, and saved y of 0 is already inside, so y stays 0.
  assert.deepEqual(result.bounds, { x: 1920, y: 0, width: 1228, height: 691 });
});

// --- CS-1361: the 96 percent usable clamp -----------------------------------

test("the 96 percent clamp applies to the centred defaults as well", () => {
  // The DEFAULTED path sizes the window by centring the defaults, and it caps
  // the same way the saved-size path does. Without this the two paths would
  // disagree about how big a window the same monitor can hold.
  //
  // 1000 * 0.96 = 960 exactly, floor 960. 700 * 0.96 = 672 exactly, floor 672.
  // The defaults are 1100x800, so the width is capped to 960 and the height to
  // 672. Position centres on the FULL area: (1000 - 960) / 2 = 20 and
  // (700 - 672) / 2 = 14.
  const area = { x: 0, y: 0, width: 1000, height: 700 };
  const result = resolveBounds({
    saved: null,
    workAreas: [area],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(result.reason, REASONS.DEFAULTED);
  assert.deepEqual(result.bounds, { x: 20, y: 14, width: 960, height: 672 });
});

test("a window flush against a work area edge is left flush - only size is capped", () => {
  // SIZE is capped at 96 percent; POSITION is not. 1920 * 0.96 = 1843.2, floor
  // 1843, and 1920 - 1843 = 77, so this window is exactly the largest allowed
  // and sits hard against the right edge of the primary. It is RESTORED
  // untouched.
  //
  // Why there is no matching position clamp: the margin exists so a window can
  // never exactly cover the work area and can always be grabbed at an edge. A
  // window 1843 wide already leaves 77 pixels showing somewhere. Clamping the
  // POSITION as well would additionally forbid a flush window the operator
  // deliberately dragged there, and would drag it back on every launch - which
  // is the bug, not the fix.
  const flush = { x: 77, y: 0, width: 1843, height: 1036 };
  const result = resolve(flush);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, flush);
  assert.equal(77 + 1843, 1920, "the fixture must actually be flush right");
});

test("the 96 percent clamp is DPI aware - the same physical cap at scaleFactor 1 and 2", () => {
  // A real 4K panel, 3840x2160 physical, seen both ways. Electron reports
  // display.workArea in DEVICE INDEPENDENT PIXELS, and BrowserWindow bounds
  // are device independent pixels too, so the scale factor cancels: a cap of
  // 96 percent in that space is a cap of 96 percent of the physical panel at
  // every scale factor.
  //
  // NO scaleFactor IS PASSED TO THE MODULE, and that is correct rather than an
  // omission. There is nothing for one to do - rescaling the remembered size
  // by savedScale / currentScale would double count, because raising a
  // display's scale factor already shrinks its DIP work area by that same
  // ratio. geometry.js records that rejection next to the clamp.
  const oversized = { x: 0, y: 0, width: 4000, height: 2400 };

  // scaleFactor 1: the DIP work area is the whole 3840x2160.
  // 3840 * 0.96 = 3686.4, floor 3686. 2160 * 0.96 = 2073.6, floor 2073.
  const at1 = resolveBounds({
    saved: oversized,
    displays: [{ id: 1, workArea: { x: 0, y: 0, width: 3840, height: 2160 }, primary: true }],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(at1.reason, REASONS.CLAMPED);
  assert.deepEqual(at1.bounds, { x: 0, y: 0, width: 3686, height: 2073 });

  // scaleFactor 2: Windows reports the SAME panel as a 1920x1080 DIP work area.
  // 1920 * 0.96 = 1843.2, floor 1843. 1080 * 0.96 = 1036.8, floor 1036.
  const at2 = resolveBounds({
    saved: oversized,
    displays: [{ id: 1, workArea: { x: 0, y: 0, width: 1920, height: 1080 }, primary: true }],
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  assert.equal(at2.reason, REASONS.CLAMPED);
  assert.deepEqual(at2.bounds, { x: 0, y: 0, width: 1843, height: 1036 });

  // The invariant that makes it DPI aware: 1843 DIP at scale 2 is 3686
  // physical pixels, the same cap the scale 1 panel got. The heights differ by
  // one physical pixel (2072 against 2073) because the floor loses half a
  // pixel before the doubling, not because the scale leaked in.
  assert.equal(1843 * 2, 3686);
  assert.equal(1036 * 2, 2072);
  assert.equal(2073 - 2072, 1);

  // Each cap is the largest integer at or below 96 percent of its own work
  // area. Written as literal ratios rather than with the module's own floor
  // expression, so a bug in that expression cannot be mirrored here.
  assert.ok(3686 / 3840 <= 0.96 && 3687 / 3840 > 0.96, "3686 is the width cap at 3840");
  assert.ok(2073 / 2160 <= 0.96 && 2074 / 2160 > 0.96, "2073 is the height cap at 2160");
  assert.ok(1843 / 1920 <= 0.96 && 1844 / 1920 > 0.96, "1843 is the width cap at 1920");
  assert.ok(1036 / 1080 <= 0.96 && 1037 / 1080 > 0.96, "1036 is the height cap at 1080");
});

test("every returned bound is an integer on an odd sized work area under the clamp", () => {
  // The clamp multiplies by 0.96, which is the obvious new way a fractional
  // bound could reach electron. An odd work area makes it worst case on both
  // axes: 1367 * 0.96 = 1312.32, floor 1312, and 769 * 0.96 = 738.24,
  // floor 738.
  const odd = { id: 2, workArea: { x: 0, y: 0, width: 1367, height: 769 }, primary: true };

  // Saved size path: capped on both axes.
  const clamped = resolveWith({ x: 0, y: 0, width: 2000, height: 1500, displayId: 0 }, [odd]);
  assert.equal(clamped.reason, REASONS.CLAMPED);
  assert.deepEqual(clamped.bounds, { x: 0, y: 0, width: 1312, height: 738 });

  // Centred defaults path: the width fits under 1312 and is left at 1100, the
  // height is capped to 738. Centring: (1367 - 1100) / 2 = 133.5, rounded to
  // 134, and (769 - 738) / 2 = 15.5, rounded to 16.
  const defaulted = resolveWith(null, [odd]);
  assert.equal(defaulted.reason, REASONS.DEFAULTED);
  assert.deepEqual(defaulted.bounds, { x: 134, y: 16, width: 1100, height: 738 });

  for (const result of [clamped, defaulted]) {
    for (const key of ["x", "y", "width", "height"]) {
      assert.ok(Number.isInteger(result.bounds[key]), `${key} was ${result.bounds[key]}`);
    }
  }
});

// --- CS-1361: home is chosen by saved display id ----------------------------

test("CS-1361 acceptance - a missing saved display lands the window on the primary inside its work area", () => {
  // MAIN ORDER 2026-10-31 22:15 item 8, the acceptance clause itself.
  //
  // THE PRIMARY IS DELIBERATELY NOT INDEX 0. "It fell back to the primary"
  // would otherwise be satisfied by "it took the first entry in the list",
  // which is a different claim and the one that was true before display ids
  // existed.
  const displays = [
    { id: 11, workArea: { x: 0, y: 0, width: 1280, height: 720 }, primary: false },
    { id: 22, workArea: { x: 1280, y: 0, width: 1920, height: 1080 }, primary: true },
  ];
  const result = resolveWith({ x: 100, y: 100, width: 1100, height: 800, displayId: 99 }, displays);

  // Silent: a reason, not a throw and not a warning.
  assert.equal(result.reason, REASONS.DISPLAY_ID_GONE);

  // The defaults centred on the primary work area, which begins at x 1280.
  // Width 1100 is under the cap of floor(1920 * 0.96) = 1843 and height 800 is
  // under floor(1080 * 0.96) = 1036, so neither is reduced. Centring:
  // 1280 + (1920 - 1100) / 2 = 1280 + 410 = 1690, and (1080 - 800) / 2 = 140.
  assert.deepEqual(result.bounds, { x: 1690, y: 140, width: 1100, height: 800 });

  // Wholly inside the primary's work area, by its own four edges. Asserted
  // separately from the rectangle because this is the clause's actual promise:
  // the operator can see and grab the window.
  const primary = displays[1].workArea;
  const b = result.bounds;
  assert.ok(b.x >= primary.x, `left edge ${b.x} against ${primary.x}`);
  assert.ok(b.y >= primary.y, `top edge ${b.y} against ${primary.y}`);
  assert.ok(
    b.x + b.width <= primary.x + primary.width,
    `right edge ${b.x + b.width} against ${primary.x + primary.width}`
  );
  assert.ok(
    b.y + b.height <= primary.y + primary.height,
    `bottom edge ${b.y + b.height} against ${primary.y + primary.height}`
  );

  // And explicitly NOT centred on index 0, which is the 1280x720 monitor and
  // would have produced { x: 90, y: 15, width: 1100, height: 691 }.
  assert.notDeepEqual(result.bounds, { x: 90, y: 15, width: 1100, height: 691 });
});

test("a saved display id with zero overlap still wins - the window slides back onto it", () => {
  // This is the whole point of saving by id. The monitor at 5000,4000 was
  // rearranged out from under the window, so the remembered rectangle now
  // overlaps it by nothing at all and overlaps the primary completely. It is
  // still the monitor the operator chose, so the window slides back onto it
  // rather than being declared adrift and dumped on the primary.
  const far = { id: 8, workArea: { x: 5000, y: 4000, width: 1920, height: 1080 }, primary: false };
  const result = resolveWith(
    { x: 100, y: 100, width: 1100, height: 800, displayId: 8 },
    [DISPLAY_PRIMARY, far]
  );

  // NUDGED, not DISPLAY_GONE: the display is here, the window merely is not on
  // it. Both of the gone reasons are ruled out by name, because both would
  // produce a rectangle on the primary instead.
  assert.equal(result.reason, REASONS.NUDGED);
  assert.notEqual(result.reason, REASONS.DISPLAY_GONE);
  assert.notEqual(result.reason, REASONS.DISPLAY_ID_GONE);

  // Size is untouched - 1100x800 is well under floor(1920 * 0.96) = 1843 by
  // floor(1080 * 0.96) = 1036. Position is pinned to the near corner of that
  // work area, 5000,4000, because the saved 100,100 is below both origins.
  assert.deepEqual(result.bounds, { x: 5000, y: 4000, width: 1100, height: 800 });
});

test("a saved display id outranks the largest overlap winner", () => {
  // The arm that proves selection is by ID, not by index and not by
  // coordinates. The saved rectangle sits wholly inside the primary, so the
  // overlap rule would restore it untouched. Display 4 is the small secondary
  // and is neither index 0 nor anywhere near the saved coordinates.
  const saved = { x: 100, y: 100, width: 1100, height: 800 };
  const displays = [DISPLAY_PRIMARY, DISPLAY_SMALL_SECOND];

  // By id: home is the 1280x720 secondary at x 1920. Cap is
  // floor(1280 * 0.96) = 1228 by floor(720 * 0.96) = 691, so the width of
  // 1100 survives and the height is cut to 691 - a resize, so CLAMPED. x is
  // slid to that work area's own origin, 1920; y is slid to the highest that
  // fits, 720 - 691 = 29.
  const byId = resolveWith({ ...saved, displayId: 4 }, displays);
  assert.equal(byId.reason, REASONS.CLAMPED);
  assert.deepEqual(byId.bounds, { x: 1920, y: 29, width: 1100, height: 691 });

  // By overlap, with no id recorded: home is the primary and nothing changes.
  const byOverlap = resolveWith({ ...saved, displayId: 0 }, displays);
  assert.equal(byOverlap.reason, REASONS.RESTORED);
  assert.deepEqual(byOverlap.bounds, saved);

  // The two answers differ in BOTH reason and rectangle, so neither assertion
  // above can be satisfied by the other branch having run.
  assert.notEqual(byId.reason, byOverlap.reason);
  assert.notDeepEqual(byId.bounds, byOverlap.bounds);
});

test("displayId 0 falls through to the overlap path", () => {
  // A state file written before the field existed, read back after an upgrade
  // wrote a 0 into it. 0 means "no display was recorded", never display 0.
  const result = resolveWith({ x: 2000, y: 100, width: 1100, height: 800, displayId: 0 }, [
    DISPLAY_PRIMARY,
    { id: 4, workArea: WA_SECOND, primary: false },
  ]);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, { x: 2000, y: 100, width: 1100, height: 800 });
});

test("an absent displayId falls through to the overlap path", () => {
  // The legacy state file proper: the field is simply not there. The answer
  // must be identical to the displayId 0 case above.
  const result = resolveWith({ x: 2000, y: 100, width: 1100, height: 800 }, [
    DISPLAY_PRIMARY,
    { id: 4, workArea: WA_SECOND, primary: false },
  ]);
  assert.equal(result.reason, REASONS.RESTORED);
  assert.deepEqual(result.bounds, { x: 2000, y: 100, width: 1100, height: 800 });
});

// Everything that is not a positive integer is "no display was recorded".
// Each gets its own named test so a regression names the exact input. The
// string "4" is chosen on purpose: display 4 is in the fixture list, so an
// implementation that coerced with Number() would find it and report CLAMPED
// on the secondary instead of RESTORED on the primary.
const NOT_RECORDED_IDS = [
  ["a negative", -1],
  ["a fractional", 1.5],
  ["a string naming a real display", "4"],
  ["null", null],
  ["NaN", NaN],
  ["Infinity", Infinity],
  ["a boolean", true],
  ["an object", { id: 4 }],
];

for (const [label, displayId] of NOT_RECORDED_IDS) {
  test(`${label} displayId is treated as not recorded`, () => {
    const saved = { x: 100, y: 100, width: 1100, height: 800, displayId };
    let result;
    assert.doesNotThrow(() => {
      result = resolveWith(saved, [DISPLAY_PRIMARY, DISPLAY_SMALL_SECOND]);
    });
    // Fell through to the overlap path and found the primary, rather than
    // reporting DISPLAY_ID_GONE on an id it could not read.
    assert.equal(result.reason, REASONS.RESTORED);
    assert.deepEqual(result.bounds, { x: 100, y: 100, width: 1100, height: 800 });
  });
}

test("DISPLAY_GONE and DISPLAY_ID_GONE are distinct faults with the same rectangle", () => {
  // Precisely the case the file's doctrine was written for: two different
  // faults, one identical rectangle, and only the reason to tell them apart.
  const displays = [DISPLAY_PRIMARY, DISPLAY_SMALL_SECOND];
  const adrift = { x: 9000, y: 9000, width: 800, height: 600 };

  // Well formed bounds, no recorded id, landing on no attached display.
  const noOverlap = resolveWith({ ...adrift, displayId: 0 }, displays);
  assert.equal(noOverlap.reason, REASONS.DISPLAY_GONE);
  assert.deepEqual(noOverlap.bounds, CENTRED_ON_PRIMARY);

  // A recorded id naming a monitor that is not attached.
  const noSuchId = resolveWith({ ...adrift, displayId: 77 }, displays);
  assert.equal(noSuchId.reason, REASONS.DISPLAY_ID_GONE);
  assert.deepEqual(noSuchId.bounds, CENTRED_ON_PRIMARY);

  assert.notEqual(noOverlap.reason, noSuchId.reason);
  assert.deepEqual(noOverlap.bounds, noSuchId.bounds);
});

// --- CS-1361: normalising the displays list ---------------------------------

test("displays entries with a malformed workArea are dropped", () => {
  // One bad display must not poison the list, exactly as for workAreas. Note
  // that the entry CLAIMING to be primary is the malformed one, so dropping it
  // has to move the primary as well - the first surviving entry becomes it.
  const displays = [
    null,
    "not a display",
    { id: 1, workArea: { x: 0, y: 0, width: NaN, height: 1080 }, primary: true },
    { id: 5, workArea: WA_PRIMARY, primary: false },
    { id: 6 },
  ];

  const restored = resolveWith({ x: 100, y: 100, width: 1100, height: 800, displayId: 5 }, displays);
  assert.equal(restored.reason, REASONS.RESTORED);
  assert.deepEqual(restored.bounds, { x: 100, y: 100, width: 1100, height: 800 });

  // Display 5 is the only survivor, so it is the primary despite not claiming
  // it, and the defaults centre there.
  const defaulted = resolveWith(null, displays);
  assert.equal(defaulted.reason, REASONS.DEFAULTED);
  assert.deepEqual(defaulted.bounds, CENTRED_ON_PRIMARY);

  // Display 1 was dropped, so saving against it now reads as gone.
  const gone = resolveWith({ x: 100, y: 100, width: 1100, height: 800, displayId: 1 }, displays);
  assert.equal(gone.reason, REASONS.DISPLAY_ID_GONE);
  assert.deepEqual(gone.bounds, CENTRED_ON_PRIMARY);
});

test("a displays list of nothing but malformed entries falls back to the workAreas path", () => {
  // displays is additive. A caller that hands over an unusable list still gets
  // the plain rectangles it also passed, which is what keeps main.js free to
  // send both without branching.
  const displays = [null, "x", 7, { id: 1, workArea: null, primary: true }];

  const restored = resolveWith({ x: 100, y: 100, width: 1100, height: 800 }, displays, [
    WA_PRIMARY,
  ]);
  assert.equal(restored.reason, REASONS.RESTORED);
  assert.deepEqual(restored.bounds, { x: 100, y: 100, width: 1100, height: 800 });

  // A plain rectangle carries no id, so no saved id can ever match one. Any
  // recorded id therefore reads as gone rather than silently matching the
  // first rectangle in the list.
  const gone = resolveWith({ x: 100, y: 100, width: 1100, height: 800, displayId: 1 }, displays, [
    WA_PRIMARY,
  ]);
  assert.equal(gone.reason, REASONS.DISPLAY_ID_GONE);
  assert.deepEqual(gone.bounds, CENTRED_ON_PRIMARY);
});

test("a malformed displays list with no workAreas behind it is DEFAULTED at the origin", () => {
  // Nothing usable to place against at all, from either argument. A usable
  // size at 0,0 - refusing to return bounds would leave the shell with no way
  // to open a window.
  const result = resolveWith({ x: 100, y: 100, width: 1100, height: 800, displayId: 4 }, [null], []);
  assert.equal(result.reason, REASONS.DEFAULTED);
  assert.deepEqual(result.bounds, { x: 0, y: 0, width: DEFAULTS.width, height: DEFAULTS.height });
});

test("a displays list where no entry claims primary uses the first valid entry", () => {
  // This is what keeps the plain-rectangle path identical to its old
  // behaviour, where workAreas[0] was the fallback target. The second entry
  // sets primary to the TRUTHY STRING "yes" rather than true, which must not
  // count: electron sets no primary flag of its own, so a caller inventing one
  // loosely should not be able to move the fallback by accident.
  const displays = [
    { id: 9, workArea: { x: 0, y: 0, width: 1280, height: 720 } },
    { id: 10, workArea: { x: 1280, y: 0, width: 1920, height: 1080 }, primary: "yes" },
  ];
  const result = resolveWith(null, displays);
  assert.equal(result.reason, REASONS.DEFAULTED);
  // Centred on display 9, the 1280x720 one. Cap is floor(1280 * 0.96) = 1228
  // by floor(720 * 0.96) = 691, so the width of 1100 survives and the height
  // is cut to 691. Centring on the full area: (1280 - 1100) / 2 = 90, and
  // (720 - 691) / 2 = 14.5, rounded to 15.
  assert.deepEqual(result.bounds, { x: 90, y: 15, width: 1100, height: 691 });
});

test("a single entry claiming primary at the end of the list is still the primary", () => {
  // The mirror of the test above, so "first entry whose primary is true" is
  // pinned from both sides and cannot be satisfied by "always the first
  // entry".
  const displays = [
    { id: 9, workArea: { x: 0, y: 0, width: 1280, height: 720 }, primary: false },
    { id: 10, workArea: WA_PRIMARY, primary: true },
  ];
  const result = resolveWith(null, displays);
  assert.equal(result.reason, REASONS.DEFAULTED);
  assert.deepEqual(result.bounds, CENTRED_ON_PRIMARY);
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

// --- CS-1361 slice C: the live seam in shell/main.js ------------------------
//
// WHY THESE ARMS READ main.js AS TEXT. main.js requires electron, so nothing in
// CI can load it - that is the same reason verdict.js exists as its own module,
// and shell/test/state.test.js already grades one main.js decision this way.
// The arms matter here because the module contract above can be entirely
// correct while the single caller never exercises it: before this slice landed,
// openWindow rebuilt `saved` with exactly four keys and passed plain
// workAreas, so DISPLAY_ID_GONE could not fire in the running application no
// matter what this file proved.
//
// BOTH HALVES OF THE ROUND TRIP ARE GRADED IN ONE PLACE, deliberately. The read
// half forwards the saved id into resolveBounds and the write half records the
// id the window ended up on; split across two test files, either half could rot
// while the other kept passing, and a remembered id nothing writes is worth
// exactly as little as one nothing reads.

function mainSource() {
  return fs.readFileSync(path.join(__dirname, "..", "main.js"), "utf8");
}

// WHY THESE ARMS ARE GRADED AGAINST A SABOTAGED SOURCE, and this is the whole
// reason this block was rewritten. The first version of it was three loose
// regexes, and the CS-1361 VERIFIER MEASURED THEM WORTHLESS: it built a main.js
// that passed every one while passing `undefined` as the primary id - leaving a
// bare getPrimaryDisplay() in a COMMENT to satisfy an unanchored whole-file
// match - and whose saved id was always 0. That file would fall back to the
// first display in the list rather than the primary, which is precisely what
// this item's acceptance forbids, and would remember no display id at all.
//
// A SOURCE-TEXT ARM THAT IS NEVER SHOWN A BROKEN SOURCE IS NOT A TEST, IT IS A
// SPELLING CHECK. So the predicate is factored out, run against the real file,
// and then run against each sabotage the verifier actually built - the arm has
// to FAIL on each of those or it has graded nothing.

/** Every way main.js can fail to wire the display id, as a list of faults. */
function seamFaults(source) {
  const faults = [];

  // The whole resolveBounds call, so an option cannot be satisfied by text
  // belonging to some other call - or by prose anywhere in the file.
  const openAt = source.indexOf("geometry.resolveBounds({");
  if (openAt === -1) {
    return ["main.js makes no geometry.resolveBounds call"];
  }
  const call = source.slice(openAt, source.indexOf("\n  });", openAt));
  if (!/displayId:\s*saved\.displayId\b/.test(call)) {
    faults.push("the saved display id is not forwarded into resolveBounds");
  }
  // Exact, not a loose match: the mapping has to be fed the live display list
  // AND the primary's own id. Passing undefined for either is the sabotage.
  if (!call.includes("displays: geometry.displaysFrom(screen.getAllDisplays(), screen.getPrimaryDisplay()?.id)")) {
    faults.push("displays is not built from the live display list and the primary id");
  }

  // The write half, inside the one state.save call.
  const saveAt = source.indexOf("state.save(directory, {");
  if (saveAt === -1) {
    return faults.concat(["main.js makes no state.save call"]);
  }
  const save = source.slice(saveAt, source.indexOf("}, { renameDeadlineMs });", saveAt));
  if (!/displayId:\s*geometry\.displayIdFrom\(screen\.getDisplayMatching\(bounds\)\)/.test(save)) {
    faults.push("the display id of the persisted window is not recorded");
  }
  return faults;
}

test("main.js wires the display id through both halves of the round trip", () => {
  assert.deepEqual(seamFaults(mainSource()), []);
});

test("the main.js seam arms fail on each sabotage the verifier built", () => {
  const real = mainSource();

  // 1. The primary id dropped, with a bare getPrimaryDisplay() left in a
  //    comment - the sabotage that passed all three of the original arms.
  const noPrimary = real.replace(
    "displays: geometry.displaysFrom(screen.getAllDisplays(), screen.getPrimaryDisplay()?.id)",
    "displays: geometry.displaysFrom(screen.getAllDisplays(), undefined) // was screen.getPrimaryDisplay()"
  );
  assert.notEqual(noPrimary, real, "sabotage 1 did not apply");
  assert.ok(seamFaults(noPrimary).length > 0, "a dropped primary id went ungraded");

  // 2. The saved id never read, so every launch takes the overlap path.
  const noRead = real.replace("displayId: saved.displayId", "");
  assert.notEqual(noRead, real, "sabotage 2 did not apply");
  assert.ok(seamFaults(noRead).length > 0, "a dropped saved id went ungraded");

  // 3. The id never written, so nothing is ever remembered to read back.
  const noWrite = real.replace(
    "displayId: geometry.displayIdFrom(screen.getDisplayMatching(bounds))",
    "displayId: 0"
  );
  assert.notEqual(noWrite, real, "sabotage 3 did not apply");
  assert.ok(seamFaults(noWrite).length > 0, "an unrecorded display id went ungraded");

  // 4. The options present but on no call at all - the shape an unanchored
  //    whole-file regex cannot tell from the real thing.
  assert.ok(
    seamFaults("// displayId: saved.displayId\n// state.save(directory, {").length > 0,
    "prose alone satisfied the seam arms"
  );
});

// --- displaysFrom: the pure half of the electron mapping --------------------
//
// The mapping lives here rather than in main.js for the reason every other
// decision was moved out of that file: a line in main.js is a line no test can
// reach. What is left at the call site is one function call, which the source
// arms above can grade by name.

test("displaysFrom maps electron displays onto the id, work area and primary", () => {
  const { displaysFrom } = geometry;
  const mapped = displaysFrom(
    [
      { id: 4, workArea: WA_SMALL_SECOND, bounds: WA_SMALL_SECOND, scaleFactor: 2 },
      { id: 3, workArea: WA_PRIMARY, bounds: WA_PRIMARY, scaleFactor: 1 },
    ],
    3
  );
  // The primary is NOT first in the input, so an implementation that marked
  // entry 0 as primary would land on the small secondary here.
  assert.deepEqual(mapped, [
    { id: 4, workArea: WA_SMALL_SECOND, primary: false },
    { id: 3, workArea: WA_PRIMARY, primary: true },
  ]);
});

test("displaysFrom drops scaleFactor and every other electron field", () => {
  // The module is DPI aware by working in device independent pixels, so a
  // scaleFactor reaching resolveBounds could only tempt someone into the
  // double-counting rescale that USABLE_FRACTION's comment rejects. It is not
  // forwarded, and this arm is what keeps it unforwarded.
  const mapped = geometry.displaysFrom([{ id: 9, workArea: WA_PRIMARY, scaleFactor: 1.5 }], 9);
  assert.deepEqual(Object.keys(mapped[0]).sort(), ["id", "primary", "workArea"]);
});

test("displaysFrom survives everything electron could hand back", () => {
  const { displaysFrom } = geometry;
  // No argument, a non-list, a list of junk: each answers a list, never throws.
  for (const input of [undefined, null, "not a list", {}, [null, 7, "x"]]) {
    assert.ok(Array.isArray(displaysFrom(input, 3)), `${JSON.stringify(input)} did not map`);
  }
  // An entry with no usable work area is kept rather than dropped - dropping is
  // resolveBounds's own job, and it already has the test for it, so doing it
  // twice would put the rule in two places.
  assert.equal(displaysFrom([{ id: 3 }], 3).length, 1);
  // A primary id electron could not supply marks nothing primary, which leaves
  // resolveBounds on its documented first-valid-entry fallback.
  assert.equal(displaysFrom([{ id: 3, workArea: WA_PRIMARY }], undefined)[0].primary, false);
});

test("displaysFrom output is accepted by resolveBounds as displays", () => {
  // The seam itself: the two functions are only useful together, and a shape
  // mismatch between them would be invisible to either one's own arms.
  const displays = geometry.displaysFrom(
    [
      { id: 4, workArea: WA_SMALL_SECOND },
      { id: 3, workArea: WA_PRIMARY },
    ],
    3
  );
  const result = resolveBounds({
    saved: { x: 2000, y: 100, width: 1100, height: 800, displayId: 77 },
    displays,
    defaults: DEFAULTS,
    minimum: MINIMUM,
  });
  // Display 77 is not attached, so the window lands on display 3 - the primary
  // - and NOT on the small secondary that happens to be first in the list.
  assert.equal(result.reason, REASONS.DISPLAY_ID_GONE);
  assert.deepEqual(result.bounds, CENTRED_ON_PRIMARY);
});

// --- displayIdFrom: the pure half of the write side -------------------------
//
// CS-1361 sibling sweep. The read half's mapping was moved into this module so
// a test could reach it, and the write half's was left in main.js - the same
// fault, one line apart, found by the verifier. Only the electron call and its
// try/catch stay at the call site now.

test("displayIdFrom takes the id off a display electron matched", () => {
  assert.equal(geometry.displayIdFrom({ id: 3, workArea: WA_PRIMARY }), 3);
  // 0 is state.js's "no display was recorded" sentinel, so an id that cannot be
  // trusted answers 0 rather than throwing: a toolkit that will not name the
  // display costs the operator a remembered id, never the whole saved position.
  for (const junk of [undefined, null, "3", 3.5, NaN, -1, Infinity, {}, [], true]) {
    assert.equal(geometry.displayIdFrom({ id: junk }), 0, `${String(junk)} was taken as an id`);
  }
  for (const absent of [undefined, null, "not a display", 7, []]) {
    assert.equal(geometry.displayIdFrom(absent), 0, `${String(absent)} was taken as a display`);
  }
});

test("displayIdFrom and displaysFrom agree on what an id is", () => {
  // One rule, one place. Were these two to drift, a window could be saved with
  // an id that resolveBounds would then refuse to match, and the symptom would
  // be a window that silently forgets its monitor every other launch.
  //
  // THE INVARIANT IS ACCEPTANCE, NOT EQUALITY, and the first version of this
  // arm got that wrong: it asserted displayIdFrom({id}) === id wherever an
  // entry was marked primary, which is false at id 0 for a correct reason. 0
  // is the "not recorded" sentinel, so displayIdFrom({id: 0}) answers 0 - the
  // input unchanged, and yet a REFUSAL - while displaysFrom must never mark
  // that entry primary. What the two must agree on is which ids they accept.
  for (const id of [0, -1, 1, 3, 3.5, 2528732444]) {
    const accepted = geometry.displayIdFrom({ id }) !== 0;
    const marked = geometry.displaysFrom([{ id, workArea: WA_PRIMARY }], id)[0].primary;
    assert.equal(accepted, marked, `id ${id} was accepted by one and not the other`);
  }
  // And the sentinel specifically, spelled out so the loop above cannot pass by
  // rejecting everything.
  assert.equal(geometry.displayIdFrom({ id: 0 }), 0);
  assert.equal(geometry.displaysFrom([{ id: 0, workArea: WA_PRIMARY }], 0)[0].primary, false);
  assert.equal(geometry.displayIdFrom({ id: 3 }), 3);
  assert.equal(geometry.displaysFrom([{ id: 3, workArea: WA_PRIMARY }], 3)[0].primary, true);
});
