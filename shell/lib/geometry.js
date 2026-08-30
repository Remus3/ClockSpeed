"use strict";

// CS-602 slice S3 - where the companion window should open.
//
// PURE BY CONTRACT. This module requires nothing at all: no electron, no
// filesystem, no clock. Work areas arrive as plain rectangles, and in the real
// application the caller obtains them from
// screen.getAllDisplays().map((d) => d.workArea) - but nothing here knows that.
// That is deliberate and load bearing: it is what lets the whole of this file
// be graded in CI on a machine with no display server, no game install and no
// electron binary, which is the machine BOOTSTRAP.md section 5.4 requires the
// rule suite to run on.
//
// Every answer carries a reason. Two different faults can produce the very same
// rectangle - a missing saved state and an unplugged monitor both end up with
// the defaults centred on the primary - so the rectangle alone cannot show
// which branch ran. The reason can, which is what makes this module testable
// rather than merely exercised.

/** Why the returned bounds are what they are. */
const REASONS = Object.freeze({
  // Saved bounds were usable as they stood.
  RESTORED: "RESTORED",
  // Saved bounds were moved so the window can actually be reached.
  NUDGED: "NUDGED",
  // Saved bounds did not fit the work area and were shrunk.
  CLAMPED: "CLAMPED",
  // Saved bounds were valid but named a monitor that is not attached now.
  DISPLAY_GONE: "DISPLAY_GONE",
  // There were no usable saved bounds to start from.
  DEFAULTED: "DEFAULTED",
});

// How much of the window must remain on a work area, measured per axis rather
// than as an area. An area threshold is the wrong shape: 10000 square pixels is
// satisfied by a 2 pixel wide sliver 5000 tall, which is invisible in practice.
// Per axis, 48 pixels is about a title bar's worth - enough to see and grab.
const MIN_VISIBLE = 48;

// Used only when a caller supplies nothing usable. A window has to open
// somewhere, and refusing to return bounds would leave the shell with no way
// forward at all.
const FALLBACK_DEFAULTS = Object.freeze({ width: 1100, height: 800 });
const FALLBACK_MINIMUM = Object.freeze({ width: 640, height: 480 });

/**
 * True for a plain object carrying four integer fields and a positive size.
 *
 * Integers specifically, not merely finite numbers: electron rejects
 * fractional bounds, so a half pixel that survived to here would fail later
 * and further away from its cause. Number.isInteger already excludes NaN and
 * both infinities, so those need no separate test.
 */
function isRect(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  for (const key of ["x", "y", "width", "height"]) {
    if (!Number.isInteger(value[key])) {
      return false;
    }
  }
  return value.width > 0 && value.height > 0;
}

/** A width and height pair, without caring where it sits. */
function isSize(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Number.isInteger(value.width) &&
    Number.isInteger(value.height) &&
    value.width > 0 &&
    value.height > 0
  );
}

/** Overlap of two closed intervals, in pixels, never negative. */
function overlap(startA, lengthA, startB, lengthB) {
  const low = Math.max(startA, startB);
  const high = Math.min(startA + lengthA, startB + lengthB);
  return Math.max(0, high - low);
}

/**
 * Slide a window of `size` so it sits inside `[origin, origin + extent)`.
 *
 * When the window is wider than the space - which happens where a work area is
 * smaller than the caller's stated minimum - it is pinned to the origin rather
 * than pushed off the near edge. Losing the far edge is recoverable by
 * resizing; losing the near edge takes the title bar with it.
 */
function slideInto(value, size, origin, extent) {
  const highest = Math.max(origin, origin + extent - size);
  return Math.min(Math.max(value, origin), highest);
}

/** Centre `size` on `area`, shrinking it to fit but never below `minimum`. */
function centreOn(size, area, minimum) {
  const width = Math.max(Math.min(size.width, area.width), minimum.width);
  const height = Math.max(Math.min(size.height, area.height), minimum.height);
  return {
    x: slideInto(area.x + Math.round((area.width - width) / 2), width, area.x, area.width),
    y: slideInto(area.y + Math.round((area.height - height) / 2), height, area.y, area.height),
    width,
    height,
  };
}

/**
 * Decide where the companion window should open.
 *
 * @param {object} [options]
 * @param {object|null} [options.saved] Bounds remembered from last time, or null.
 * @param {Array<object>} [options.workAreas] Plain work area rectangles.
 * @param {object} [options.defaults] Fallback window size.
 * @param {object} [options.minimum] Smallest window this shell will produce.
 * @returns {{bounds: {x: number, y: number, width: number, height: number}, reason: string}}
 */
function resolveBounds(options) {
  const opts = options !== null && typeof options === "object" ? options : {};
  const defaults = isSize(opts.defaults) ? opts.defaults : FALLBACK_DEFAULTS;
  const minimum = isSize(opts.minimum) ? opts.minimum : FALLBACK_MINIMUM;

  // A malformed entry is dropped rather than being allowed to poison the list.
  // A caller that hands over one bad display should still get the good ones.
  const areas = (Array.isArray(opts.workAreas) ? opts.workAreas : []).filter(isRect);

  if (areas.length === 0) {
    // Nothing to place against. Hand back a usable size at the origin so the
    // shell has something to open with.
    return {
      bounds: { x: 0, y: 0, width: defaults.width, height: defaults.height },
      reason: REASONS.DEFAULTED,
    };
  }

  const saved = opts.saved;
  if (!isRect(saved)) {
    return { bounds: centreOn(defaults, areas[0], minimum), reason: REASONS.DEFAULTED };
  }

  // Home is the work area holding the most of the window. Comparing overlapping
  // AREA rather than merely finding the first intersecting monitor is what
  // makes a window straddling two displays resolve against the one actually
  // showing it.
  let home = null;
  let best = 0;
  for (const area of areas) {
    const covered =
      overlap(saved.x, saved.width, area.x, area.width) *
      overlap(saved.y, saved.height, area.y, area.height);
    if (covered > best) {
      best = covered;
      home = area;
    }
  }

  if (home === null) {
    // Well formed bounds that land on no attached display. Distinct from
    // DEFAULTED: the saved state was fine, the monitor is simply not here.
    return { bounds: centreOn(defaults, areas[0], minimum), reason: REASONS.DISPLAY_GONE };
  }

  const width = Math.max(Math.min(saved.width, home.width), minimum.width);
  const height = Math.max(Math.min(saved.height, home.height), minimum.height);
  const resized = width !== saved.width || height !== saved.height;

  // Two independent reasons to move the window.
  //
  // The asymmetry between the axes is intentional. Too little visible on either
  // axis makes the window hard to find at all. But a window whose top edge is
  // above the work area is a separate and worse fault even when most of it is
  // visible, because the title bar goes with it and the window can then be
  // neither dragged nor closed by mouse. There is no matching rule for x: a
  // window hanging off the left with plenty showing is still draggable.
  const stranded =
    Math.min(
      overlap(saved.x, width, home.x, home.width),
      overlap(saved.y, height, home.y, home.height)
    ) < MIN_VISIBLE;
  const aboveTop = saved.y < home.y;

  if (!resized && !stranded && !aboveTop) {
    // A fresh object rather than `saved` itself, so a caller mutating what it
    // passed in cannot move the window afterwards.
    return {
      bounds: { x: saved.x, y: saved.y, width: saved.width, height: saved.height },
      reason: REASONS.RESTORED,
    };
  }

  const bounds = {
    x: slideInto(saved.x, width, home.x, home.width),
    y: slideInto(saved.y, height, home.y, home.height),
    width,
    height,
  };

  // CLAMPED outranks NUDGED. A window that had to be resized was almost always
  // repositioned as well, and reporting the move while staying silent about the
  // resize would name the smaller of the two changes.
  return { bounds, reason: resized ? REASONS.CLAMPED : REASONS.NUDGED };
}

module.exports = { resolveBounds, REASONS, MIN_VISIBLE };
