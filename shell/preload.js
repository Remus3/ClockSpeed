"use strict";

// CS-602 slice S4 - the preload script, which is deliberately inert.
//
// THIS FILE EXPOSES NOTHING, AND THAT IS THE FINISHED STATE RATHER THAN AN
// UNFINISHED ONE. There is no contextBridge call here, no ipcRenderer, and no
// object reachable from the page.
//
// WHY THERE IS NOTHING TO EXPOSE. The dashboard is an ordinary web page served
// over the local HTTPS surface, and it already has everything it needs through
// that surface: it fetches from the API and renders the answer. Nothing it does
// requires a capability the browser does not already give it. A bridge would
// therefore be an API invented to justify a file - and every method on it would
// be a permanently reachable hole from page context into the main process,
// bought with no capability the page was missing.
//
// WHY THE FILE EXISTS AT ALL. It is a declared seam, in the same sense that the
// OVERLAY entry in lib/window.js is a declared mode: the place a later slice
// puts a channel, with the security posture already settled around it. The
// window is built with contextIsolation on, nodeIntegration off and sandbox on,
// all three stated explicitly in lib/window.js rather than inherited from
// electron's defaults. A preload added later under those settings runs in an
// isolated world and can only reach the page through an explicit bridge, which
// is the arrangement that makes such a channel auditable. Adding the file after
// the fact, in a hurry, next to a window whose posture nobody re-checked, is
// how that arrangement gets skipped.
//
// IF YOU ARE ABOUT TO ADD SOMETHING HERE. Expose a named function per
// capability, never an object with a method the page can walk, and never
// ipcRenderer itself. `contextBridge.exposeInMainWorld` copies across the
// isolation boundary, so anything handed over must be a value or a function
// with a fixed signature - passing a module hands the page everything reachable
// from it. The zero-language-model and never-write rules in CLAUDE.md section 7
// apply on this side of the bridge exactly as they do on the other.
