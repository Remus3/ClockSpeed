"use strict";

// CS-602 slice S4 - the electron main process.
//
// WIRING ONLY. Every decision this file appears to make was made somewhere
// testable and is only being carried here: where the dashboard is and where its
// certificate lives is endpoint.js, whether a presented certificate is the
// pinned one is trust.js, what is remembered between launches is state.js,
// where the window opens is geometry.js, and what the window IS - its frame,
// its floor, its security posture and its drag strip - is lib/window.js. None
// of those can be graded with electron in the way, which is exactly why none of
// them live here. What is left is the part that cannot be tested without a
// display server, and it is deliberately the least interesting part.
//
// THE ONE RULE THIS FILE ADDS. The trust module answers in words, never in
// numbers, so that no edit there can quietly become a blanket accept. That only
// holds if the words are turned into electron's integers in exactly one place.
// VERDICT_CODES below is that place, and it is the only integer vocabulary in
// this file's verification path.

const fs = require("node:fs");
const path = require("node:path");

const { app, BrowserWindow, screen, session } = require("electron");

const endpoint = require("./lib/endpoint.js");
const trust = require("./lib/trust.js");
const state = require("./lib/state.js");
const geometry = require("./lib/geometry.js");
const windowLib = require("./lib/window.js");

// ---------------------------------------------------------------------------
// The only place a verdict becomes a number
// ---------------------------------------------------------------------------

// electron's verify callback takes an integer, and this map is the only place
// in this file that writes one down.
//
// WHAT IS TYPE-CHECKED HERE AND WHAT IS NOT. electron 44.0.0's shipped typings
// state only that 0 accepts the certificate and -2 rejects it. They contain no
// occurrence of -3, and no mention of Certificate Transparency anywhere. Both
// of those come from the published API page and from nothing else. They are
// therefore NOT type-checked, and neither has been observed against a running
// electron by anyone who wrote this file. That distinction is recorded rather
// than smoothed over: the typings agreeing with the docs page would have been
// evidence, and the typings being silent is not the same thing.
//
// THE ACCEPTING CODE IS DOCUMENTED TO DO MORE THAN ACCEPT. The API page states
// that it also switches Certificate Transparency verification off for the
// session. That is the documented reason exactly one verdict may reach it.
// DEFER pointedly does not share it: deferring hands the decision back to
// Chromium with its full validation still switched on, which is the right
// answer for every host that is not ours.
//
// IF DEFER'S CODE IS NOT HONOURED AS DOCUMENTED, THIS FAILS CLOSED - and that
// argument does not rest on the docs page either. The parameter is a Chromium
// net error code, a space in which 0 is the only success value and every
// negative is an error; -3 with no special handling is ERR_ABORTED, a failed
// load. So a value electron did not interpret as documented refuses the
// connection rather than trusting it. The residual exposure is functional, not
// a trust one, and it is small: DEFER is reached only for a host that is not
// ours, and this shell loads exactly one origin - the local dashboard, which
// requests no remote resource of any kind.
//
// All three refusals share a single code. They are separate verdicts because
// they are separate faults worth telling apart when reading a trace, not
// because electron has more than one way to say no.
const VERDICT_CODES = new Map([
  [trust.TRUST, 0],
  [trust.DEFER, -3],
  [trust.REFUSE_NO_PIN, -2],
  [trust.REFUSE_NO_CERT, -2],
  [trust.REFUSE_MISMATCH, -2],
]);

/**
 * Turn a verdict into the integer electron expects.
 *
 * An unrecognised verdict cannot happen - trust.decide returns one of five
 * strings for any input whatsoever - but if it ever did, the answer is a
 * refusal and it is read back out of the map rather than written as a literal.
 * A default written as a number here would be a second, quieter place an
 * integer reaches the callback, which is the one property this file exists to
 * keep.
 */
function codeFor(verdict) {
  const code = VERDICT_CODES.get(verdict);
  return code === undefined ? VERDICT_CODES.get(trust.REFUSE_MISMATCH) : code;
}

// ---------------------------------------------------------------------------
// Refusals - fixed text, and never a path
// ---------------------------------------------------------------------------

// CLOCKSPEED_CERT_DIR may point anywhere, including inside a home directory,
// and a home path carries the Windows account name. Non-negotiable 3 puts that
// out of every log line, so these name the remedy and quote nothing. The
// remedy is a repository-relative script, which is not personal data.
const CERT_UNREADABLE =
  "clockspeed: the pinned certificate could not be read. " +
  "Generate it with: python scripts/make_cert.py";

const ENDPOINT_UNRESOLVED = "clockspeed: the dashboard endpoint could not be resolved.";

const STATE_NOT_SAVED = "clockspeed: the window position could not be saved.";

const PAGE_NOT_LOADED =
  "clockspeed: the dashboard did not load. Is the local surface running?";

// How long a burst of move or resize events is allowed to settle before the
// state file is rewritten. Dragging a window emits these continuously, and
// state.save fsyncs and renames on every call - persisting each event would
// mean hundreds of synchronous disk flushes across one drag.
const PERSIST_DEBOUNCE_MS = 400;

// ---------------------------------------------------------------------------
// Startup
// ---------------------------------------------------------------------------

function installVerifyProc(pinnedDer) {
  const expectedHost = endpoint.expectedHost();

  // WHAT THIS DOES NOT DO. There is no second path to this decision. Chromium
  // also emits an application-level event after its own verification has
  // already failed, and pinning from there would be strictly weaker - it never
  // sees a certificate Chromium accepted, so it cannot refuse one. Registering
  // both would mean two places deciding the same thing, one of them blind.
  //
  // ITS ANSWER IS CACHED BY THE NETWORK SERVICE - stated in the shipped
  // typings, and omitted from the published API page, so a reader who checked
  // only the docs will not know it. A verdict reached for a host is reused
  // rather than recomputed, so re-minting the certificate while the shell is
  // running does not reliably produce a visible refusal: a previously accepted
  // verdict can still be serving from that cache. Restart the shell before
  // concluding anything from what this path did or did not refuse.
  session.defaultSession.setCertificateVerifyProc((request, callback) => {
    // certificate.data is a PEM-encoded string, not DER bytes, so it is
    // converted before any comparison. pemToDer answers null rather than
    // throwing on anything unparseable, which matters here: an exception
    // escaping this callback means it never fires, and the page hangs instead
    // of being refused.
    const verdict = trust.decide({
      hostname: request.hostname,
      expectedHost,
      presentedDer: trust.pemToDer(request.certificate?.data),
      pinnedDer,
    });
    callback(codeFor(verdict));
  });
}

function openWindow(saved) {
  const placement = geometry.resolveBounds({
    saved: { x: saved.x, y: saved.y, width: saved.width, height: saved.height },
    workAreas: screen.getAllDisplays().map((display) => display.workArea),
    defaults: { width: state.DEFAULTS.width, height: state.DEFAULTS.height },
    minimum: { width: windowLib.MIN_WIDTH, height: windowLib.MIN_HEIGHT },
  });

  const options = windowLib.buildWindowOptions(windowLib.MODES.COMPANION, {
    x: placement.bounds.x,
    y: placement.bounds.y,
    width: placement.bounds.width,
    height: placement.bounds.height,
    alwaysOnTop: windowLib.resolveAlwaysOnTop({
      persisted: saved.alwaysOnTop,
      argv: process.argv,
      env: process.env,
    }),
    preload: path.join(__dirname, "preload.js"),
  });

  return new BrowserWindow(options);
}

/**
 * Remember where the window is, without writing on every pixel of a drag.
 *
 * THE PERSISTED PREFERENCE IS CARRIED THROUGH UNCHANGED. A launch flag or the
 * environment can pin the window for one session, and neither rewrites the
 * remembered preference: an operator who used the flag once to get an
 * in-the-way window out of the way has not asked for that to become permanent,
 * and there is no runtime toggle that could put it back.
 */
function wirePersistence(win, directory, persistedAlwaysOnTop) {
  let timer = null;
  let closing = false;

  const persist = () => {
    try {
      // getNormalBounds rather than getBounds: while a window is maximized or
      // minimized, getBounds reports the maximized rectangle, and remembering
      // that would restore a window that fills the screen and has forgotten the
      // size the operator actually chose.
      const bounds = win.getNormalBounds();
      state.save(directory, {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        alwaysOnTop: persistedAlwaysOnTop,
      });
    } catch {
      // A window that cannot write its position is a window that opens
      // somewhere unremarkable next time. That is a far better outcome than a
      // main process that dies mid-drag, so this is reported and swallowed.
      // The message quotes no path for the same reason the others do not.
      console.error(STATE_NOT_SAVED);
    }
  };

  const schedule = () => {
    if (closing) {
      return;
    }
    if (timer !== null) {
      clearTimeout(timer);
    }
    timer = setTimeout(() => {
      timer = null;
      persist();
    }, PERSIST_DEBOUNCE_MS);
  };

  win.on("move", schedule);
  win.on("resize", schedule);

  // close fires while the window still exists, so its bounds are still
  // readable. The pending timer is cleared first: were it left to fire after
  // the window was destroyed, it would read bounds off a destroyed object and
  // throw from a timer callback, where nothing is left to catch it.
  win.on("close", () => {
    closing = true;
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
    persist();
  });
}

function start() {
  let url;
  try {
    url = endpoint.dashboardUrl();
  } catch (err) {
    // EndpointError carries a fixed reason built from a fault code and quotes
    // nothing the caller wrote. Anything else gets this file's fixed line,
    // because an arbitrary error's message is not something known to be clean.
    console.error(err instanceof endpoint.EndpointError ? `clockspeed: ${err.reason}` : ENDPOINT_UNRESOLVED);
    app.exit(1);
    return;
  }

  // A missing file and an unparseable one end at the same refusal and the same
  // remedy: pemToDer answers null rather than throwing, and regenerating the
  // pair is the fix for both.
  let pinnedDer = null;
  try {
    pinnedDer = trust.pemToDer(fs.readFileSync(endpoint.certPath(), "utf8"));
  } catch {
    pinnedDer = null;
  }
  if (pinnedDer === null) {
    // NO WINDOW IS CREATED ON THIS PATH. Opening one and letting it fail to
    // load would put the operator in front of a blank frameless window with no
    // title bar and no error, which is a worse way to learn the certificate is
    // missing than a line on stderr naming the script that makes it.
    console.error(CERT_UNREADABLE);
    app.exit(1);
    return;
  }

  installVerifyProc(pinnedDer);

  const directory = app.getPath("userData");
  const saved = state.load(directory);
  const win = openWindow(saved);

  wirePersistence(win, directory, saved.alwaysOnTop === true);

  // Re-injected on every load rather than once: injected styles do not survive
  // a navigation or a reload, and a reloaded dashboard with no drag strip is a
  // frameless window the operator can no longer move.
  win.webContents.on("did-finish-load", () => {
    win.webContents.insertCSS(windowLib.DRAG_STRIP_CSS).catch(() => {});
  });

  win.loadURL(url).catch(() => {
    console.error(PAGE_NOT_LOADED);
  });
}

app.whenReady().then(start);
