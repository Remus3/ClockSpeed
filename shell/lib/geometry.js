"use strict";

// CS-602 slice S3 - where the companion window should open.
// CS-1361 - home is chosen by SAVED DISPLAY ID, and window size is capped at
// 96 percent of the work area.
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
  // The saved state NAMED a display by id, and no attached display carries it.
  //
  // Distinct from DISPLAY_GONE, and the distinction is not cosmetic. DISPLAY_GONE
  // means well formed bounds landed on no attached display, which happens with
  // every monitor still plugged in when the operator rearranges them. This one
  // means the monitor the operator chose is not here at all. The two produce the
  // same rectangle, so without separate reasons a caller would have nothing to
  // tell them apart - which is this file's whole doctrine.
  DISPLAY_ID_GONE: "DISPLAY_ID_GONE",
  // There were no usable saved bounds to start from.
  DEFAULTED: "DEFAULTED",
});

// How much of the window must remain on a work area, measured per axis rather
// than as an area. An area threshold is the wrong shape: 10000 square pixels is
// satisfied by a 2 pixel wide sliver 5000 tall, which is invisible in practice.
// Per axis, 48 pixels is about a title bar's worth - enough to see and grab.
const MIN_VISIBLE = 48;

// How much of a work area a window may COVER. MAIN ORDER 2026-10-31 22:15
// item 8 sets the number.
//
// The remaining 4 percent is not decoration. It guarantees the window never
// exactly covers its work area, so some edge always has desktop or another
// window showing beside it and the window can always be grabbed at an edge
// rather than being flush on all four at once.
//
// WHY THIS IS ALREADY DPI AWARE, WITH NO scaleFactor PARAMETER. Electron
// reports display.workArea in DEVICE INDEPENDENT PIXELS, and BrowserWindow
// bounds are device independent pixels too. Both sides of the multiplication
// are therefore in the same space and the scale factor cancels, which makes a
// 96 percent cap in that space a 96 percent cap in PHYSICAL pixels at every
// scale factor. On a 3840x2160 panel: at scaleFactor 1 the work area is 3840
// wide and the cap is 3686; at scaleFactor 2 Windows reports the same panel as
// 1920 wide, the cap is 1843, and 1843 x 2 = 3686 physical pixels - the same
// window either way.
//
// NOT TAKEN: rescaling the remembered size by savedScale / currentScale to
// preserve physical size across a scale change. It is a DIFFERENT FEATURE from
// the one the acceptance clause asks for, and it is not asked for anywhere.
//
// THIS COMMENT FIRST SAID THE RESCALE WOULD "DOUBLE COUNT" AND THAT WAS WRONG,
// MEASURED BY THE CS-1361 VERIFIER AND CORRECTED HERE RATHER THAN REWRITTEN
// AWAY. Below the cap the clamp does not act at all, so a rescale would be the
// only change, never a second one: a window saved at 1920 DIP on a 3840 panel
// at scaleFactor 1 is 50 percent of the work area, the cap leaves it alone,
// and the rescale alone would move it. At the cap the two agree - a rescale
// and a clamp both land on 1843 - so they are redundant there, never doubled.
// The false argument is recorded because a do-not-re-pitch fence built on
// reasoning nobody can reproduce is worse than no fence: the next reader
// disproves the sentence and then has no idea what the real reason was.
//
// THE REAL REASONS, BOTH STILL STANDING. The clause asks for a cap RELATIVE TO
// THE WORK AREA, which is what this is, and says nothing about preserving a
// physical size across a scale change. And taking a scaleFactor would cost
// this module its purity, since it is a display property no rectangle carries.
const USABLE_FRACTION = 0.96;

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

/**
 * True for a positive integer - the shape electron gives a display id.
 *
 * Zero is excluded on purpose and means "no display was recorded": electron
 * never issues 0, so it is free to stand for absence, and a state file written
 * before the field existed reads back as absent either way. Number.isInteger
 * rejects NaN, both infinities, fractions, strings, null and objects, so a
 * corrupt state file degrades to "not recorded" rather than throwing.
 */
function isDisplayId(value) {
  return Number.isInteger(value) && value > 0;
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
 * `extent` is always the FULL work area, never the usable 96 percent of it -
 * see fitSize. Only SIZE is capped, so a window may still sit flush against a
 * work area edge.
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

/**
 * The size a window may actually have on `area`.
 *
 * Three bounds, in priority order: the caller's own `size`, then the usable
 * extent of the work area, then the stated `minimum`.
 *
 * The usable extent is floored rather than rounded, so it can never exceed the
 * fraction and can never itself be fractional - electron rejects fractional
 * bounds, and 0.96 turns almost every real work area into one
 * (1920 * 0.96 = 1843.2).
 *
 * THE MINIMUM OUTRANKS THE CAP, deliberately. On a work area smaller than the
 * minimum window the cap would otherwise produce something unusable, and an
 * unusable window is a worse outcome than one covering its whole work area.
 *
 * POSITION IS NOT CAPPED THIS WAY - only size is. The margin already
 * guarantees the window cannot exactly cover the work area, so a position
 * clamp on top of it would buy nothing and would additionally forbid a flush
 * window the operator deliberately dragged to an edge, dragging it back on
 * every launch. That is the bug, not the fix.
 */
function fitSize(size, area, minimum) {
  const usableWidth = Math.floor(area.width * USABLE_FRACTION);
  const usableHeight = Math.floor(area.height * USABLE_FRACTION);
  return {
    width: Math.max(Math.min(size.width, usableWidth), minimum.width),
    height: Math.max(Math.min(size.height, usableHeight), minimum.height),
  };
}

/** Centre `size` on `area`, shrinking it to fit but never below `minimum`. */
function centreOn(size, area, minimum) {
  const { width, height } = fitSize(size, area, minimum);
  // Centred on the FULL work area, not on the usable 96 percent of it.
  // Centring inside a shrunken rectangle would push the window off centre by
  // 2 percent of the monitor for no reason the operator could see.
  return {
    x: slideInto(area.x + Math.round((area.width - width) / 2), width, area.x, area.width),
    y: slideInto(area.y + Math.round((area.height - height) / 2), height, area.y, area.height),
    width,
    height,
  };
}

/**
 * The attached displays as `{ id, workArea, primary }`, from either argument.
 *
 * `displays` is preferred; `workAreas` is the fallback, used when `displays` is
 * absent or yields no valid entry. A caller may pass both, and a caller written
 * before display ids existed keeps working untouched.
 *
 * A plain rectangle normalises to id 0, which means "no id" rather than
 * "display 0", so no saved id can ever match one. That is correct rather than a
 * limitation: a bare rectangle carries no identity to match against, and
 * silently matching the first rectangle in the list would be a guess dressed up
 * as a restore.
 *
 * A malformed entry is dropped rather than being allowed to poison the list. A
 * caller that hands over one bad display should still get the good ones. An
 * entry with a usable `workArea` but an unusable `id` is KEPT with its id
 * normalised to 0 - it is still a real monitor geometrically, and dropping a
 * place to put windows over a field that only ADDRESSING uses would lose more
 * than it protects.
 */
function normaliseDisplays(displays, workAreas) {
  const named = [];
  for (const entry of Array.isArray(displays) ? displays : []) {
    if (entry === null || typeof entry !== "object" || Array.isArray(entry)) {
      continue;
    }
    if (!isRect(entry.workArea)) {
      continue;
    }
    named.push({
      id: isDisplayId(entry.id) ? entry.id : 0,
      workArea: entry.workArea,
      // `=== true`, not merely truthy. electron carries no primary flag on the
      // display object itself, so the caller invents this field, and a loosely
      // truthy value from a caller guessing at it must not be able to move the
      // fallback target.
      primary: entry.primary === true,
    });
  }
  if (named.length > 0) {
    return named;
  }
  return (Array.isArray(workAreas) ? workAreas : [])
    .filter(isRect)
    .map((rect) => ({ id: 0, workArea: rect, primary: false }));
}

/**
 * Decide where the companion window should open.
 *
 * @param {object} [options]
 * @param {object|null} [options.saved] Bounds remembered from last time, or null.
 *   May carry `displayId`, the id of the display it was saved on. Read here,
 *   never written - this module does not own the state file.
 * @param {Array<object>} [options.displays] Attached displays as
 *   `{id, workArea, primary}`. Preferred over `workAreas`.
 * @param {Array<object>} [options.workAreas] Plain work area rectangles, used
 *   when `displays` is absent or yields nothing valid.
 * @param {object} [options.defaults] Fallback window size.
 * @param {object} [options.minimum] Smallest window this shell will produce.
 * @returns {{bounds: {x: number, y: number, width: number, height: number}, reason: string}}
 */
function resolveBounds(options) {
  const opts = options !== null && typeof options === "object" ? options : {};
  const defaults = isSize(opts.defaults) ? opts.defaults : FALLBACK_DEFAULTS;
  const minimum = isSize(opts.minimum) ? opts.minimum : FALLBACK_MINIMUM;

  const displays = normaliseDisplays(opts.displays, opts.workAreas);

  if (displays.length === 0) {
    // Nothing to place against. Hand back a usable size at the origin so the
    // shell has something to open with.
    //
    // This guard runs FIRST, ahead of the saved-bounds check, because every
    // other outcome below centres something on the primary and with no display
    // at all there is no primary to centre on.
    return {
      bounds: { x: 0, y: 0, width: defaults.width, height: defaults.height },
      reason: REASONS.DEFAULTED,
    };
  }

  // THE PRIMARY: the first entry claiming to be one, else the first entry at
  // all. The fallback half is what keeps the plain-rectangle path identical to
  // its old behaviour, where workAreas[0] was the target every fallback
  // centred the defaults on. Widening that to "the primary" is therefore a
  // widening and not a behaviour change for callers passing plain rectangles.
  const primary = displays.find((display) => display.primary) || displays[0];

  const saved = opts.saved;
  if (!isRect(saved)) {
    return { bounds: centreOn(defaults, primary.workArea, minimum), reason: REASONS.DEFAULTED };
  }

  // The remembered display id, or 0 for "no display was recorded".
  const savedId = isDisplayId(saved.displayId) ? saved.displayId : 0;

  let home = null;
  if (savedId > 0) {
    const named = displays.find((display) => display.id === savedId);
    if (named === undefined) {
      // The monitor the operator chose is not attached. SILENT: a reason, not
      // a throw and not a warning. Coming back to an unplugged monitor is an
      // ordinary thing, not a fault to escalate.
      return {
        bounds: centreOn(defaults, primary.workArea, minimum),
        reason: REASONS.DISPLAY_ID_GONE,
      };
    }
    // Home EVEN WITH ZERO OVERLAP, and that is the entire point of saving the
    // id. A monitor rearranged under the window is still the monitor the
    // operator chose, so the window slides back onto it rather than being
    // treated as adrift and dumped on the primary. Saving coordinates alone
    // could never tell those two cases apart.
    home = named.workArea;
  } else {
    // No id recorded, so fall back to geometry. Home is the work area holding
    // the most of the window. Comparing overlapping AREA rather than merely
    // finding the first intersecting monitor is what makes a window straddling
    // two displays resolve against the one actually showing it.
    let best = 0;
    for (const display of displays) {
      const area = display.workArea;
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
      // Distinct from DISPLAY_ID_GONE too: nothing named a monitor, so this is
      // a geometry fault and not an identity one.
      return {
        bounds: centreOn(defaults, primary.workArea, minimum),
        reason: REASONS.DISPLAY_GONE,
      };
    }
  }

  const { width, height } = fitSize(saved, home, minimum);
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
    // passed in cannot move the window afterwards. Note that `displayId` is
    // not copied across - this function answers with bounds, and the state
    // file's own fields are the caller's business.
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

/**
 * Map electron's own display objects onto the shape resolveBounds wants.
 *
 * WHY THIS LIVES HERE AND NOT AT THE CALL SITE. main.js requires electron, so
 * every line in it is a line no test can reach - that is why trust.js,
 * verdict.js and supervisor.js exist as their own modules, and the mapping of
 * a display list is the same kind of decision. What stays in main.js is one
 * call, which a source-text arm can grade by name.
 *
 * PURITY IS NOT BROKEN BY KNOWING THE SHAPE. This function never requires
 * electron; it reads two fields off plain objects a caller hands over. The
 * objects happen to be what screen.getAllDisplays() returns, and nothing here
 * can tell.
 *
 * `primary` IS COMPUTED, NOT READ, because electron carries no primary flag on
 * a display object. The caller supplies screen.getPrimaryDisplay().id and the
 * comparison happens once, here, rather than being repeated by every caller.
 *
 * scaleFactor IS DELIBERATELY NOT FORWARDED - see USABLE_FRACTION above. The
 * cap needs none, because work areas and window bounds are both device
 * independent pixels. The only use a scale factor could be put to is the
 * savedScale / currentScale rescale that comment declines, for its two
 * standing reasons: it preserves a physical size across a scale change, which
 * is a different feature from the work-area-relative cap the clause asks for,
 * and taking a scale factor would cost resolveBounds its purity.
 *
 * A malformed entry is PASSED THROUGH rather than dropped. resolveBounds
 * already drops an entry with no usable work area and has the test that pins
 * it; filtering here as well would put one rule in two places, where the two
 * can disagree.
 *
 * @param {Array<object>} allDisplays Typically screen.getAllDisplays().
 * @param {number} [primaryId] Typically screen.getPrimaryDisplay().id.
 * @returns {Array<{id: *, workArea: *, primary: boolean}>}
 */
function displaysFrom(allDisplays, primaryId) {
  const list = Array.isArray(allDisplays) ? allDisplays : [];
  const out = [];
  for (const display of list) {
    if (display === null || typeof display !== "object" || Array.isArray(display)) {
      continue;
    }
    out.push({
      id: display.id,
      workArea: display.workArea,
      // isDisplayId on the primary as well: an undefined primaryId must not
      // match an entry whose own id is also undefined and silently make a
      // junk display the fallback target.
      primary: isDisplayId(primaryId) && display.id === primaryId,
    });
  }
  return out;
}

/**
 * The id of a display electron matched, or 0 when it cannot be trusted.
 *
 * THE SIBLING OF displaysFrom, AND IT IS HERE FOR THE SAME REASON. The read
 * half's mapping was moved out of main.js so a test could reach it; this, the
 * write half's, was left behind at first and the CS-1361 verifier named the
 * inconsistency - one slice moving one half of a round trip out of the
 * ungradable file and leaving the other in it. What stays in main.js now is
 * the electron call and its try/catch, and nothing that decides anything.
 *
 * 0 RATHER THAN A THROW OR A NULL. 0 is state.js's "no display was recorded"
 * sentinel, and that module's schema is deliberately incapable of holding a
 * null or a string. So a toolkit that will not name the display costs the
 * operator a remembered id and nothing more: the saved rectangle still
 * restores through the overlap path above.
 *
 * THE PREDICATE IS isDisplayId, THE SAME ONE resolveBounds MATCHES WITH. An id
 * this function accepted but resolveBounds would not match would be saved and
 * then silently ignored, and the symptom - a window forgetting its monitor
 * every other launch - names neither side.
 *
 * @param {object} display Typically screen.getDisplayMatching(bounds).
 * @returns {number} The display id, or 0.
 */
function displayIdFrom(display) {
  if (display === null || typeof display !== "object" || Array.isArray(display)) {
    return 0;
  }
  return isDisplayId(display.id) ? display.id : 0;
}

module.exports = {
  resolveBounds,
  displaysFrom,
  displayIdFrom,
  REASONS,
  MIN_VISIBLE,
  USABLE_FRACTION,
};
