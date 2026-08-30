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
// lib/verdict.js is that place, and THIS FILE CONTAINS NO INTEGER VOCABULARY AT
// ALL on the verification path - not even a fallback.
//
// THE MAP USED TO LIVE HERE, AND THAT WAS THE DEFECT. Because this file imports
// electron, nothing could load it, so no test in either language graded the
// argument handed to callback. Changing it to a literal 0 - a blanket accept
// for every host - left the whole gate green. The map now lives one file over,
// where shell/test/verdict.test.js can load it without electron and pin all
// five mappings by value.

const fs = require("node:fs");
const path = require("node:path");

const { app, BrowserWindow, screen, session } = require("electron");

const endpoint = require("./lib/endpoint.js");
const trust = require("./lib/trust.js");
const state = require("./lib/state.js");
const geometry = require("./lib/geometry.js");
const windowLib = require("./lib/window.js");
const verdicts = require("./lib/verdict.js");

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
    callback(verdicts.codeForOrRefuse(verdict));
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
