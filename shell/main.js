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

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const {
  app,
  BrowserWindow,
  Menu,
  Tray,
  dialog,
  nativeImage,
  net,
  screen,
  session,
} = require("electron");

const endpoint = require("./lib/endpoint.js");
const trust = require("./lib/trust.js");
const state = require("./lib/state.js");
const geometry = require("./lib/geometry.js");
const windowLib = require("./lib/window.js");
const verdicts = require("./lib/verdict.js");
const supervisor = require("./lib/supervisor.js");
const trayLib = require("./lib/tray.js");

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

const SURFACE_NOT_SPAWNED =
  "clockspeed: the dashboard could not be started. " +
  "Start it yourself with: python -m clockspeed.surface";

const SURFACE_NEVER_ANSWERED =
  "clockspeed: the dashboard was started but never answered. " +
  "Start it yourself with: python -m clockspeed.surface and read what it prints.";

// WHY AN EXIT CODE AND NOT THE CHILD'S OUTPUT. The surface prints a good
// diagnosis when it refuses to start - but its messages can name a path, and a
// path carries the Windows account name, which non-negotiable 3 keeps out of
// every line this shell emits. So its OUTPUT is discarded and its EXIT CODE is
// kept: the code is the surface's documented contract (docs/OPERATIONS.md
// section 7.3), it is an integer rather than personal data, and the rendering
// below is this file's own fixed text.
//
// MEASURED, not imagined: the first real shortcut launch of this shell hit
// exactly this. The port was in TIME_WAIT from a forced kill moments earlier,
// the surface exited rather than binding, and the operator was told to go read
// something that had already been thrown away. A refusal that names an action
// the operator cannot perform is worse than one that says less.
const SURFACE_EXIT_REASONS = new Map([
  [1, "its configuration would not resolve"],
  [2, "the port it needs is already held by something else"],
  [3, "the certificate pair would not load"],
]);

/** The never-answered refusal, told why when the child's exit code says why. */
function surfaceNeverAnswered(exitCode) {
  const reason = SURFACE_EXIT_REASONS.get(exitCode);
  if (reason === undefined) {
    return SURFACE_NEVER_ANSWERED;
  }
  return `clockspeed: the dashboard stopped before answering, because ${reason}.`;
}

// WHY EVERY REFUSAL ABOVE NOW ALSO OPENS A DIALOG. Until CS-909 the only way to
// launch this shell was from a terminal, where a line on stderr is exactly the
// right output. A desktop shortcut has no terminal attached, so console.error
// writes into a stream nobody will ever read, and app.exit(1) then looks
// identical to nothing happening at all - the operator double-clicks an icon
// and gets silence. The console line is KEPT because the terminal launch is
// still supported and still the better diagnostic; the dialog is added on top.
//
// showErrorBox is used rather than the async dialog because these paths run
// BEFORE any window exists, and several run before app.whenReady has resolved.
// It quotes only the fixed text above, so no path reaches it.
function refuse(message) {
  console.error(message);
  try {
    dialog.showErrorBox("Clockspeed", message);
  } catch {
    // A dialog is a courtesy on top of the console line, never the mechanism.
    // If the toolkit cannot show one - too early, no display - the refusal has
    // already been reported and must not be turned into a second failure.
  }
}

// How long a burst of move or resize events is allowed to settle before the
// state file is rewritten. Dragging a window emits these continuously, and
// state.save fsyncs and renames on every call - persisting each event would
// mean hundreds of synchronous disk flushes across one drag.
const PERSIST_DEBOUNCE_MS = 400;

// ---------------------------------------------------------------------------
// The dashboard process - CS-909, and see ADR 0015
// ---------------------------------------------------------------------------

// Set once, and read on the way out. `quitting` separates "the operator pressed
// the close button" from "the operator chose Quit": the first HIDES to the tray
// and the second is the only one that ends the process. `startedSurface` is the
// entire memory behind the only-stop-what-you-started rule - a dashboard that
// was already answering when this shell launched is NOT ours to kill.
let quitting = false;
let startedSurface = null;

// Held at module scope so the tray is never collected - see createTray.
let trayRef = null;

// The exit code of a surface WE started, if it has already exited. null means
// either that it has not exited or that we never started one.
let surfaceExitCode = null;

// The companion window, once it exists. Held so a SECOND launch can raise this
// one rather than building another - see the single-instance lock at the foot
// of this file.
let windowRef = null;

/**
 * Ask the dashboard whether it is there, once.
 *
 * THIS GOES THROUGH ELECTRON'S NET MODULE, NOT NODE'S HTTPS, AND THAT IS A
 * MEASURED DECISION RATHER THAN A STYLISTIC ONE. It was written first with
 * `https.get` and a `ca` option holding the pinned certificate. That works
 * under stock Node - verified directly, status 200 - and FAILS under electron,
 * which builds its Node against BoringSSL and does not honour that option the
 * same way. Every probe came back `UNABLE_TO_VERIFY_LEAF_SIGNATURE` while the
 * surface was demonstrably listening on the right address and port, so the
 * companion spawned a dashboard, refused to see it, and gave up. No test caught
 * that, and no test could have: the pure suites cannot load this file, and the
 * behaviour only differs INSIDE the runtime this file is the only user of.
 *
 * Using net also removes a duplicate trust decision rather than merely moving
 * it. net requests run through the default session, which means they reach
 * `setCertificateVerifyProc` and are judged by trust.js - the SAME pinning the
 * window is subject to. The probe and the page can no longer disagree about
 * what is trusted, because there is now one answer and one place that gives it.
 *
 * ORDERING THIS DEPENDS ON: installVerifyProc must have run before the first
 * call, or this is judged by electron's default verification instead of by the
 * pin. start() does that, and the ordering is load-bearing.
 *
 * Resolves false rather than rejecting, for every failure. A refused connection
 * before the surface binds is the EXPECTED case on the spawn path, not an
 * error, and an exception there would abort the wait on its first turn.
 */
function probeOnce(healthUrl) {
  return new Promise((resolve) => {
    let settled = false;
    const settle = (answered) => {
      if (!settled) {
        settled = true;
        resolve(answered);
      }
    };

    const request = net.request({ url: healthUrl, session: session.defaultSession });

    // net has no timeout option of its own, so the deadline is held here. It is
    // cleared on every exit path: a timer left running past a resolved probe
    // would abort the NEXT attempt's socket rather than this one's.
    const deadline = setTimeout(() => {
      request.abort();
      settle(false);
    }, supervisor.PROBE_TIMEOUT_MS);

    request.on("response", (response) => {
      // The body is drained rather than read. Nothing here parses it: the
      // question is whether a listener the pin vouches for answered, and
      // reading its content would invite deciding on that content.
      response.on("data", () => {});
      response.on("end", () => {});
      clearTimeout(deadline);
      settle(response.statusCode === 200);
    });
    request.on("error", () => {
      clearTimeout(deadline);
      settle(false);
    });
    request.end();
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Wait for the dashboard to answer, letting supervisor.js decide when to stop.
 *
 * THE LOOP BOUND IS A GUARD RAIL, NOT THE DECISION. decideProbeOutcome is what
 * ends this wait; the bound only ensures a supervisor that somehow never said
 * GIVE_UP cannot spin forever. Any word that is neither READY nor RETRY ends
 * the wait, so a refusal word added to that module later fails CLOSED here
 * rather than being silently treated as "keep trying".
 *
 * ELAPSED TIME IS MEASURED HERE AND JUDGED THERE. The attempt ceiling alone
 * bounded the wait at nearly three minutes, because a listener that accepts and
 * never speaks makes every probe burn its full timeout rather than failing
 * fast. That is the shortcut launch with no window and no tray yet drawn, so
 * the operator has an icon that did nothing for three minutes. The wall-clock
 * budget is what actually bounds it now; the ceiling remains as the second of
 * two independent bounds.
 *
 * THE CHILD'S DEATH ALSO ENDS THE WAIT. A dashboard that exits at 0.3 seconds
 * used to cost the operator the entire remaining budget before saying so, and
 * the exit code that explains it was already in hand the whole time.
 */
async function waitForSurface(healthUrl) {
  const startedAt = Date.now();
  for (let attempt = 1; attempt <= supervisor.PROBE_ATTEMPT_CEILING; attempt += 1) {
    const answered = await probeOnce(healthUrl);
    const elapsedMs = Date.now() - startedAt;
    const outcome = supervisor.decideProbeOutcome({ attempt, answered, elapsedMs });
    if (outcome === supervisor.READY) {
      return true;
    }
    if (outcome !== supervisor.RETRY) {
      return false;
    }
    // Checked AFTER the verdict, so a surface that answered on the same turn it
    // exited is still READY rather than being failed for having died.
    if (surfaceExitCode !== null) {
      return false;
    }
    await delay(supervisor.PROBE_INTERVAL_MS);
  }
  return false;
}

/**
 * Start the dashboard as a child of this process.
 *
 * THE INTERPRETER IS SPAWNED AS AN ABSOLUTE PATH, AND THAT IS A SECURITY FIX
 * RATHER THAN A TIDINESS ONE. Spawning the bare name "python" was measured to be
 * a local code-execution vector on Windows: libuv searches the spawn's working
 * directory BEFORE PATH, that directory is the repository root, and the root
 * grants Modify to Authenticated Users on this machine. Any local user could
 * leave a binary of that name there and own the next double-click of the
 * shortcut - silently, because this spawn hides its window and discards its
 * output. supervisor.resolveInterpreter walks PATH itself, refuses any entry
 * that is not rooted, and never considers the working directory.
 *
 * NEITHER THE INTERPRETER NOR THE MODULE IS SPELLED HERE. supervisor.js owns
 * both names and the resolution rule, where a test can read them without
 * electron in the way. No absolute path is written into this file either; the
 * one used is computed at runtime from the environment, because a spelled path
 * would carry the account name of whoever authored it - non-negotiable 3.
 *
 * The repository root is DERIVED from this file's location rather than spelled,
 * mirroring endpoint.js.
 *
 * Returns the child, or null if it could not be started.
 */
function spawnSurface() {
  const interpreter = supervisor.resolveInterpreter({
    pathValue: process.env.PATH,
    pathExt: process.env.PATHEXT,
    // The only filesystem touch on this path, injected so the resolver itself
    // stays pure and gradable. Answers false rather than throwing, because an
    // unreadable candidate is one to skip, not one to fail the whole search on.
    isExecutable: (candidate) => {
      try {
        return fs.statSync(candidate).isFile();
      } catch {
        return false;
      }
    },
  });

  // A refusal word rather than a path. Fail closed: spawning the bare name as a
  // fallback is exactly the vector the resolver exists to close.
  if (!path.isAbsolute(interpreter)) {
    return null;
  }

  let child = null;
  try {
    child = spawn(interpreter, supervisor.serverArgv(), {
      cwd: path.join(__dirname, ".."),
      // Inherited pipes would fill and block the child once nobody drains them,
      // and under a shortcut launch nobody ever does.
      stdio: "ignore",
      windowsHide: true,
    });
  } catch {
    return null;
  }
  // ENOENT arrives as an event rather than a throw, so the synchronous catch
  // above does not cover a missing interpreter. Swallowed deliberately: the
  // wait below is what decides the outcome, and it reports one refusal rather
  // than racing this handler to report a second.
  child.on("error", () => {});

  // The code is REMEMBERED rather than acted on. A surface that exits early is
  // reported by the wait, which is the one place that decides this outcome;
  // this handler only makes sure the reason it needs is still available by the
  // time it asks.
  child.on("exit", (code) => {
    surfaceExitCode = code;
  });
  return child;
}

/** Stop the dashboard, but ONLY if this launch is the one that started it. */
function stopSurfaceIfOurs() {
  const verdict = supervisor.decideStop({ started: startedSurface !== null });
  if (verdict !== supervisor.STOP) {
    return;
  }
  try {
    startedSurface.kill();
  } catch {
    // Already gone. Nothing to report and nothing to do.
  }
  startedSurface = null;
}

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

  // WHY `closing` IS NOT SET WHEN THE WINDOW MERELY HIDES. It exists to stop a
  // debounced write firing against a destroyed window. Hiding destroys nothing,
  // and setting it there would be permanent: schedule() returns early forever
  // after, so every move and resize following the first hide would be dropped
  // and the window would restore to wherever it happened to be that one time.
  // The close handler below therefore returns BEFORE touching it on the hide
  // path. Nothing else in this file writes it.

  // CS-1124 - EVERY CALLER NAMES ITS RENAME BUDGET. save() blocks this thread
  // while a held state file is retried. The debounced save runs behind a live
  // window and can afford state.RENAME_DEADLINE_MS; the two close paths below
  // run while the operator waits for the window to go, and pass
  // state.RENAME_CLOSE_DEADLINE_MS so a stuck file cannot hold a close longer
  // than the old retry loop already did.
  const persist = (renameDeadlineMs) => {
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
      }, { renameDeadlineMs });
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
      persist(state.RENAME_DEADLINE_MS);
    }, PERSIST_DEBOUNCE_MS);
  };

  win.on("move", schedule);
  win.on("resize", schedule);

  // close fires while the window still exists, so its bounds are still
  // readable. The pending timer is cleared first: were it left to fire after
  // the window was destroyed, it would read bounds off a destroyed object and
  // throw from a timer callback, where nothing is left to catch it.
  win.on("close", (event) => {
    // The pending timer is cleared on BOTH paths: on the quit path because it
    // would otherwise read bounds off a destroyed window from inside a timer
    // callback, where nothing is left to catch it, and on the hide path because
    // it has just been superseded by the write below.
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }

    // CLOSE MEANS HIDE (CS-909) - BUT ONLY WHILE THERE IS A TRAY TO COME BACK
    // FROM. The tray is the sole route back to a hidden frameless window: it
    // has no taskbar button to click and no title bar to restore. If createTray
    // returned null, hiding here would strand the operator with a running
    // process they cannot see, cannot reach and cannot quit. So the absence of
    // a tray falls back to close MEANING close, which is a worse companion and
    // a far better outcome than an unreachable one.
    if (!quitting && trayRef !== null) {
      // The position is still written on this path: an operator may leave it
      // hidden for days and never quit at all, and a hidden window that forgot
      // where it was is the same defect as a closed one that did.
      persist(state.RENAME_CLOSE_DEADLINE_MS);
      event.preventDefault();
      win.hide();
      return;
    }

    closing = true;
    persist(state.RENAME_CLOSE_DEADLINE_MS);
  });
}

/**
 * Build the tray presence, and keep it alive.
 *
 * THE REFERENCE IS HELD AT MODULE SCOPE ON PURPOSE. A Tray that becomes
 * unreachable is collected, and the icon then vanishes from the notification
 * area while the process keeps running - leaving a hidden window with nothing
 * left that can bring it back.
 *
 * The menu is REBUILT rather than mutated on every state change, because the
 * template is a pure function of the two flags and rebuilding is the only way
 * the labels cannot drift from what the window is actually doing.
 */
function createTray(win) {
  let tray;
  try {
    const icon = nativeImage.createFromDataURL(trayLib.ICON_DATA_URL);

    // AN EMPTY IMAGE IS REFUSED HERE, AND OBJECT-NULLNESS IS NOT THE TEST.
    // MEASURED: `new Tray()` handed an image that decoded to nothing does NOT
    // throw - it returns a perfectly ordinary, non-null Tray carrying an
    // INVISIBLE icon. Checking only that the constructor returned something
    // therefore answers a different question from the one that matters, and the
    // hazard it misses is the one lib/tray.js names in its own header: once the
    // window hides instead of closing, an invisible tray icon is an application
    // the operator can neither reopen nor quit.
    if (icon.isEmpty()) {
      return null;
    }
    tray = new Tray(icon);
  } catch {
    // A tray is the ONLY way a hidden window comes back. If the toolkit will
    // not give us one, returning null leaves close meaning close, which is
    // worse than a tray and far better than a window the operator has hidden
    // and can never see again.
    return null;
  }

  tray.setToolTip(trayLib.tooltip());

  const onClick = (id) => {
    if (id === trayLib.MENU_IDS.SHOW_HIDE) {
      if (win.isVisible()) {
        win.hide();
      } else {
        win.show();
        win.focus();
      }
      return;
    }
    if (id === trayLib.MENU_IDS.ALWAYS_ON_TOP) {
      // Deliberately NOT written back to the state file. The persisted
      // preference is the operator's standing choice; a toggle used once to
      // get the window out of the way has not asked to change it, matching
      // what wirePersistence already does with the launch flag.
      win.setAlwaysOnTop(!win.isAlwaysOnTop());
      refresh();
      return;
    }
    if (id === trayLib.MENU_IDS.QUIT) {
      quitting = true;
      app.quit();
    }
  };

  function refresh() {
    const entries = trayLib.menuTemplate({
      visible: win.isVisible(),
      alwaysOnTop: win.isAlwaysOnTop(),
    });
    const template = entries.map((entry) =>
      entry.type === "separator" ? entry : { ...entry, click: () => onClick(entry.id) },
    );
    tray.setContextMenu(Menu.buildFromTemplate(template));
  }

  // The labels are a function of window state, so they are rebuilt whenever
  // that state moves - including when something other than the menu moved it.
  win.on("show", refresh);
  win.on("hide", refresh);
  tray.on("click", () => {
    win.show();
    win.focus();
  });

  refresh();
  return tray;
}

async function start() {
  let url;
  try {
    url = endpoint.dashboardUrl();
  } catch (err) {
    // EndpointError carries a fixed reason built from a fault code and quotes
    // nothing the caller wrote. Anything else gets this file's fixed line,
    // because an arbitrary error's message is not something known to be clean.
    refuse(err instanceof endpoint.EndpointError ? `clockspeed: ${err.reason}` : ENDPOINT_UNRESOLVED);
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
    refuse(CERT_UNREADABLE);
    app.exit(1);
    return;
  }

  installVerifyProc(pinnedDer);

  // CS-909. Whether a dashboard is already answering decides everything that
  // follows, including whether Quit is allowed to stop one. See ADR 0015.
  // AFTER installVerifyProc, never before - see probeOnce. Probing first would
  // ask electron's default verification about a self-signed certificate, which
  // refuses it, and the companion would then spawn a second dashboard on a port
  // the first one already holds.
  const healthUrl = new URL("/api/health", url).toString();
  const startVerdict = supervisor.decideStart({ healthy: await probeOnce(healthUrl) });

  if (startVerdict === supervisor.START) {
    const child = spawnSurface();
    if (child === null) {
      refuse(SURFACE_NOT_SPAWNED);
      app.exit(1);
      return;
    }
    // Recorded BEFORE the wait, so a dashboard that starts and then dies is
    // still stopped by us rather than left behind as an orphan.
    startedSurface = child;
    if (!(await waitForSurface(healthUrl))) {
      // Read AFTER the wait, never before: a surface that refuses to bind does
      // so within the first probe or two, so by the time the wait gives up the
      // exit code is already there to be reported.
      const why = surfaceNeverAnswered(surfaceExitCode);
      stopSurfaceIfOurs();
      refuse(why);
      app.exit(1);
      return;
    }
  } else if (startVerdict !== supervisor.ADOPT) {
    // Neither word. FAIL CLOSED rather than guess: a refusal word added to
    // supervisor.js later must not be read here as permission to spawn.
    refuse(supervisor.supervisorRefusal(startVerdict));
    app.exit(1);
    return;
  }

  const directory = app.getPath("userData");
  const saved = state.load(directory);
  const win = openWindow(saved);
  windowRef = win;

  wirePersistence(win, directory, saved.alwaysOnTop === true);

  // Re-injected on every load rather than once: injected styles do not survive
  // a navigation or a reload, and a reloaded dashboard with no drag strip is a
  // frameless window the operator can no longer move.
  win.webContents.on("did-finish-load", () => {
    win.webContents.insertCSS(windowLib.DRAG_STRIP_CSS).catch(() => {});
  });

  trayRef = createTray(win);

  // Quit is the ONLY path that ends the process, and it is the only path that
  // may stop a dashboard. before-quit also covers Ctrl-C in a terminal launch.
  //
  // TWO THINGS IT DOES NOT COVER, corrected here because this comment claimed
  // both and the shipped typings contradict it. A WINDOWS LOGOUT OR SHUTDOWN
  // emits none of before-quit, will-quit or quit, so a dashboard this launch
  // started outlives the session that started it; that is left standing rather
  // than papered over, because the alternative is a shutdown handler racing the
  // operating system. A TASKBAR CLOSE is not a quit either - the window is
  // frameless but `skipTaskbar` is never set, so it has a taskbar button, and
  // closing from there sends WM_CLOSE, which reaches the close handler above
  // and HIDES like any other close.
  app.on("before-quit", () => {
    quitting = true;
  });
  app.on("will-quit", stopSurfaceIfOurs);

  // WITHOUT THIS HANDLER Windows would end the app when its last window closes.
  // With it, the app survives - which is what a tray application wants, and is
  // also how this produced a zombie. MEASURED: when createTray returns null the
  // close handler correctly lets the window close for real, this fires with
  // `quitting` false, nothing called app.quit(), and merely HAVING registered a
  // listener suppressed the default quit - leaving an electron process with no
  // window, no tray icon and a live dashboard it had started, reachable only
  // through Task Manager.
  //
  // So the tray is what decides. A companion with a tray keeps running when its
  // window closes, because the tray can bring it back. A companion WITHOUT one
  // has nothing left to be, and quits - which also runs will-quit, and so stops
  // the dashboard it started rather than abandoning it.
  app.on("window-all-closed", () => {
    if (quitting || trayRef === null) {
      app.quit();
    }
  });

  win.loadURL(url).catch(() => {
    refuse(PAGE_NOT_LOADED);
  });
}

// ---------------------------------------------------------------------------
// One companion, not several
// ---------------------------------------------------------------------------

// A TRAY APPLICATION MUST BE SINGLE-INSTANCE, AND THIS WAS MEASURED THE HARD
// WAY: the operator double-clicked the shortcut a second time while the first
// was running and got a second window and a second tray icon. Three faults
// follow from that, and only the first is cosmetic.
//
//   - Two tray icons, of which only one belongs to the window in front of you.
//   - Two writers on ONE window-state.json. state.js stages through a partial
//     file with a FIXED name and opens it truncating, so an interleave publishes
//     a ZERO-BYTE state file over a good one. That falsifies its own atomicity
//     header and non-negotiable 5, and it is not a race this file can fix from
//     the outside - it can only decline to create the second writer.
//   - Two claims on the dashboard's lifetime. Adopt happens to save it today:
//     the second instance finds the first one's dashboard answering and adopts
//     rather than spawning a competitor onto a held port. That is luck, not
//     design, and it is not a property to lean on.
//
// THE LOCK IS TAKEN BEFORE whenReady, and therefore before any probe, spawn or
// window. A second instance that got as far as probing would already have had
// the chance to spawn.
if (!app.requestSingleInstanceLock()) {
  // Not an error. The operator asked for the companion and the companion is
  // already there; the running instance is about to be shown by the handler
  // below. Exit 0 and say nothing - a dialog here would be noise on a
  // double-click that did exactly what was wanted.
  app.exit(0);
} else {
  // Electron delivers this to the FIRST instance when a later one is refused
  // the lock. Showing the existing window is the whole point: an operator who
  // double-clicks a second time wants the companion in front of them, and the
  // window may well be hidden in the tray at that moment.
  app.on("second-instance", () => {
    if (windowRef === null) {
      return;
    }
    if (windowRef.isMinimized()) {
      windowRef.restore();
    }
    windowRef.show();
    windowRef.focus();
  });

  // start() is async now, so a throw inside it lands here rather than crashing
  // the process. Without this it would surface as an unhandled promise
  // rejection: no window, no message, and under a shortcut launch no console to
  // carry it - which is indistinguishable from the icon doing nothing at all.
  app.whenReady().then(start).catch(() => {
    refuse(PAGE_NOT_LOADED);
    app.exit(1);
  });
}
