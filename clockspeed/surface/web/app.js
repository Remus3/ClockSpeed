"use strict";

/*
  CS-601 - the dashboard's only script.

  WHY THERE IS NO innerHTML ANYWHERE IN THIS FILE, and it is two reasons rather
  than one.

    1. A class path arriving in unknown_classes is content this project does not
       model - game or mod authored - and it reaches this page as a string read
       out of a save. Building a node and setting textContent renders it as
       TEXT, whatever characters it holds. Assigning it into markup would let a
       mod author choose what this page executes.

    2. CONVENTIONS.md section 13.3 records that a repaint through innerHTML
       destroys keyboard focus: the focused element is discarded and recreated,
       so a keyboard reader loses their place on every refresh. Building nodes
       and swapping children has the same cost and not that fault.

  AND NOT USING innerHTML IS NOT ON ITS OWN ENOUGH TO AVOID THAT FAULT, which
  is what this comment used to imply and what the CS-600 audit measured false.
  The rows are built as nodes exactly as described above, and a repaint still
  emptied the document of focus - through the button, not through the table.
  See refresh() at the foot of this file for the door it came in by and for the
  measurement. The rule that survives is about the OUTCOME, not the API: after a
  repaint, whatever the reader was on is still what the reader is on.

  WHY THERE IS NO TIMER. CONVENTIONS.md section 13.3 again: "A timer-rebuilt
  panel becomes mouse-only, invisibly." Refresh is the button in the header and
  nothing else repaints this page.

  WHY THIS PAGE ISSUES EXACTLY THREE ON-DEMAND REQUESTS, WHICH IS A COUNT AND
  NOT AN ABSENCE. This block used to say the page issued none at all and that
  the question did not arise; then it said exactly one POST. Both were true when
  written. The honest answer is a BOUND rather than a zero, and the bound is now
  three: the solve bench asks /api/solve, the optimize bench asks /api/optimize
  and the power bench asks /api/power. Two are POSTs and one is a GET, because
  the verb belongs to the route rather than to this page.

  WHAT THE BOUND BUYS IS UNCHANGED BY THE COUNT. Each is reachable only from a
  panel's own click handler; each can ask for one path and no other, because
  app.js - never the panel - builds the query string from a fixed table of the
  names that endpoint takes; and one shared flag means at most one of the three
  is ever outstanding. A panel cannot smuggle an unnamed parameter through any
  of them, cannot redirect one, and cannot start a second while one is running.

  AND THE PARAMETERS RIDE IN THE QUERY STRING, NOT IN A BODY. The server splits
  the request path at the question mark and parses only what follows it; no code
  path under clockspeed/surface reads a request body at all. A body sent here
  would be ignored on arrival, and an unread body on a kept-alive HTTP/1.1
  connection desyncs whatever request follows it on that socket. The fetch
  therefore carries no body key, which sends Content-Length: 0.

  WHY FIVE ROWS SAY "not probed". The two /api/advice/<id>/... routes need a
  card id. /api/advice now answers 200 with a card list and this page probes
  it on a repaint, but the probe table takes no id from that body, so there is
  no id to put in the path. Asking with an invented one would be asking about
  a card that does not exist. The other three take a parameter this page has nothing to put in
  on a repaint, and the table below is a map of what this page may safely ask
  for on a REPAINT: /api/solve, /api/optimize and /api/power are each asked on
  a click and answer into the panel that clicked, so their rows still have no
  transport code of their own to print.
  AN EARLIER VERSION OF THIS SENTENCE SAID THE TWO SOLVER ROWS "take a body
  this page will not send", and both halves of that were false - they take a
  query string, and the page now sends one to each of them.
  /api/power IS A GET AND IS STILL NOT PROBED, which is the reason this
  paragraph is about PARAMETERS rather than about verbs: it requires a building
  identifier, and a repaint has no building to name. Inventing one would ask
  about a building the operator did not choose.
  For those five the page prints what /api/health says and names that as the
  source, rather than inventing a transport code it never observed.

  WHY /api/registry IS PROBED EVEN THOUGH ITS BODY IS LARGE. The four rows
  above say "not probed" because the page cannot ask on a repaint - it has no
  card id, or the route is one a repaint has no parameters to ask it with.
  Cost is not that reason, and
  making it one would quietly turn a rule about ABILITY into a rule about
  taste. /api/registry is a parameterless GET, so the page asks. Its body is the
  largest this page fetches - /api/world is the next largest - and the figures
  are deliberately NOT restated here: they are a property of the installed
  documents, they cannot be re-measured on a machine with no game, and
  CLAUDE.md section 4 names a hardcoded measurement in prose as a lie with a
  timestamp on it. What was measured is that the delay is invisible: it lands
  after first paint, which draws the headings and the "reading ..." row before
  any fetch is issued. If the registry ever grows enough for that to stop being
  true, the answer is a cheaper liveness question on the route, not a fifth
  silent reason for a row to go unprobed.

  AN EARLIER VERSION OF THIS PARAGRAPH GAVE A DIFFERENT REASON - that the
  router matched paths exactly and refused to register a template carrying a
  path parameter. Both halves were true when written and are now false: the
  router matches templates and both /api/advice/<id>/... routes answer over the
  wire. The behaviour above did not change, only the reason for it, which is
  exactly the kind of stale justification that reads as verified.
*/

/*
  The routes BOOTSTRAP.md section 7.1 publishes, in that section's order,
  each with the verb its own endpoint module registers and the concrete path -
  if there is one - this page may safely ask for with a GET.
*/
var ROUTES = [
  { template: "/api/health", method: "GET", probe: "/api/health" },
  { template: "/api/world", method: "GET", probe: "/api/world" },
  { template: "/api/registry", method: "GET", probe: "/api/registry" },
  { template: "/api/advice", method: "GET", probe: "/api/advice" },
  { template: "/api/advice/<id>/derivation", method: "GET", probe: null },
  { template: "/api/advice/<id>/state", method: "POST", probe: null },
  { template: "/api/solve", method: "POST", probe: null },
  { template: "/api/optimize", method: "POST", probe: null },
  { template: "/api/audit", method: "GET", probe: "/api/audit" },
  { template: "/api/plan", method: "GET", probe: "/api/plan" },
  { template: "/api/map", method: "GET", probe: "/api/map" },
  { template: "/api/power", method: "GET", probe: null }
];

/* The five collections /api/world counts rather than lists, and their labels. */
var COUNT_LABELS = [
  ["objects", "object records"],
  ["levels", "levels"],
  ["nodes", "resource nodes"],
  ["unknown_classes", "unmodeled classes"],
  ["warnings", "load warnings"]
];

/* The scalar header facts, in the order the response carries them. */
var WORLD_SCALARS = [
  ["header_version", "header version"],
  ["save_version", "save version"],
  ["build_changelist", "build changelist"],
  ["body_offset", "body offset"],
  ["is_modded", "modded"]
];

var DASH = "-";
var READING = "reading ...";
var UNREACHABLE = "unreachable";
var NOT_PROBED = "not probed";
var FROM_HEALTH = "/api/health";
var FROM_PROBE = "probed";

/* --- node construction, the only two primitives this file uses ---------- */

function el(tag, className, text) {
  var node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== null && text !== undefined) {
    node.textContent = String(text);
  }
  return node;
}

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function byId(id) {
  return document.getElementById(id);
}

/* --- reading the wire --------------------------------------------------- */

function statusClass(word) {
  if (word === "ok" || word === "live" || word === "present" || word === "loaded") {
    return "pill-ok";
  }
  if (word === "not_implemented") {
    return "pill-pending";
  }
  if (word === "unavailable" || word === "absent") {
    return "pill-warn";
  }
  if (word === "error") {
    return "pill-bad";
  }
  return "pill-idle";
}

async function probeRoute(path) {
  /*
    One GET, and every failure folded into the same shape. A refused connection,
    a TLS fault and a body that is not JSON are all "this page could not read
    that route", and a row that distinguishes them teaches nothing the operator
    can act on differently.
  */
  try {
    var response = await fetch(path, {
      method: "GET",
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
    var payload = null;
    try {
      payload = await response.json();
    } catch (parseFailure) {
      payload = null;
    }
    return { reached: true, http: response.status, body: payload };
  } catch (networkFailure) {
    return { reached: false, http: null, body: null };
  }
}

function bodyData(result) {
  if (result && result.body && result.body.data && typeof result.body.data === "object") {
    return result.body.data;
  }
  return null;
}

function blockedFor(result) {
  /*
    The open item a 501 names. Read off the wire on every repaint and never
    typed into this file: an id spelled here would render the same characters
    whether or not the server agreed, which is a page that cannot go wrong and
    therefore cannot be right either.
  */
  if (result && result.body && typeof result.body.blocked_by === "string") {
    return result.body.blocked_by;
  }
  return DASH;
}

/* --- the endpoint table ------------------------------------------------- */

function renderEndpoints(liveness, probes) {
  var tbody = byId("endpoint-rows");
  clear(tbody);

  var probed = 0;
  var pending = 0;

  for (var index = 0; index < ROUTES.length; index += 1) {
    var route = ROUTES[index];
    var result = route.probe ? probes[route.probe] : null;
    var word = liveness[route.template] || "unknown";
    var code = NOT_PROBED;
    var source = FROM_HEALTH;

    if (result) {
      probed += 1;
      source = FROM_PROBE;
      code = result.reached ? String(result.http) : UNREACHABLE;
      if (result.body && typeof result.body.status === "string") {
        word = result.body.status;
      } else if (!result.reached) {
        word = UNREACHABLE;
      }
    }
    if (word === "not_implemented") {
      pending += 1;
    }

    var row = document.createElement("tr");
    row.appendChild(el("td", "route", route.template));
    row.appendChild(el("td", "route", route.method));
    row.appendChild(el("td", "route", code));

    var statusCell = document.createElement("td");
    statusCell.appendChild(el("span", "pill " + statusClass(word), word));
    row.appendChild(statusCell);

    var blockedCell = document.createElement("td");
    blockedCell.className = "route";
    /* blocked_by, rendered as text. See blockedFor above for why it is read. */
    blockedCell.textContent = blockedFor(result);
    row.appendChild(blockedCell);

    row.appendChild(el("td", "dim", source));
    tbody.appendChild(row);
  }

  var note = byId("probe-note");
  clear(note);
  note.appendChild(
    document.createTextNode(
      probed +
        " of " +
        ROUTES.length +
        " routes answered a direct GET from this page; the remaining " +
        (ROUTES.length - probed) +
        " report the liveness /api/health publishes for them. " +
        pending +
        " have no layer beneath them yet."
    )
  );
}

/* --- the header line and the two presence badges ------------------------ */

function renderHeader(result) {
  var data = bodyData(result);
  var pin = byId("pin");
  clear(pin);

  if (!data) {
    pin.appendChild(document.createTextNode("/api/health did not answer"));
    setBadge("badge-registry", "registry", UNREACHABLE);
    setBadge("badge-world", "world", UNREACHABLE);
    return {};
  }

  pin.appendChild(
    document.createTextNode(
      "clockspeed " + data["app_version"] + "  |  game build " + data["game_build_pin"]
    )
  );
  setBadge("badge-registry", "registry", data["registry"]);
  setBadge("badge-world", "world", data["world"]);

  var liveness = data["endpoints"];
  return liveness && typeof liveness === "object" ? liveness : {};
}

function setBadge(id, label, word) {
  var badge = byId(id);
  badge.className = "badge " + (statusClass(word) === "pill-ok" ? "badge-live" : "badge-absent");
  clear(badge);
  badge.appendChild(document.createTextNode(label + ": " + word));
}

/* --- the world panel ---------------------------------------------------- */

function fact(label, value) {
  var cell = document.createElement("div");
  cell.appendChild(el("dt", null, label));
  cell.appendChild(el("dd", null, value));
  return cell;
}

/*
  GIVE EVERY SCROLLER A TAB STOP EXACTLY WHILE IT HAS SOMETHING TO SCROLL.

  The markup used to declare tabindex, role and aria-label unconditionally, and
  the CONVENTIONS 13.2 audit measured that claim false twice: the World scroller
  reports scrollWidth === clientWidth at 1574, 375 and 320px - it never scrolls
  at any tested width - and it kept its stop even when a failed /api/world hid
  its table, leaving a 1.33px empty box that took focus and announced itself as
  a scrollable region of world counts.

  A LABEL IS A CLAIM AND THIS ONE IS NOW DERIVED FROM THE MEASUREMENT IT ASSERTS.
  The name says "scrolls sideways" only where the box does, so a reader who
  reaches the stop finds the capability it was promised.

  A STOP IS NEVER TAKEN FROM UNDER A READER STANDING ON IT. Removing tabindex
  from the focused element blurs it exactly as button.disabled does, and the
  re-audit measured this code doing it: focus the scroller at 375px, widen to
  1574, and activeElement finished at BODY with only blur and focusout fired and
  nothing announced. THAT IS THE SAME FAULT refresh() DOCUMENTS AT LENGTH a few
  hundred lines below, reintroduced through a different door - so the rule it
  states is enforced here too: after any repaint or resize, whatever the reader
  was on is still what the reader is on. The stop is left in place while the box
  holds focus and withdrawn when focus leaves.

  THE LABEL IS STILL CORRECTED IMMEDIATELY in that held state, because the box no
  longer scrolls and a name saying it does would be the exact false claim this
  function exists to stop making.
*/
function syncScrollRegions() {
  var boxes = document.querySelectorAll(".scroll-x");
  for (var i = 0; i < boxes.length; i += 1) {
    var box = boxes[i];
    /*
      A hidden box measures 0 for both, so hidden is already not-overflowing and
      needs no separate branch - but reading it explicitly keeps the intent
      legible rather than resting on a coincidence of the box model.
    */
    var scrolls = !box.hidden && box.scrollWidth > box.clientWidth;
    var stem = box.getAttribute("data-scroll-label") || "Content";
    if (scrolls) {
      box.setAttribute("tabindex", "0");
      box.setAttribute("role", "region");
      box.setAttribute("aria-label", stem + ", scrolls sideways");
    } else if (document.activeElement === box) {
      /*
        Adding the identical listener twice is a no-op - the DOM compares type,
        callback and capture and ignores once - so a burst of resize events
        cannot pile these up.
      */
      box.setAttribute("aria-label", stem);
      box.addEventListener("blur", syncScrollRegions, { once: true });
    } else {
      box.removeAttribute("tabindex");
      box.removeAttribute("role");
      box.removeAttribute("aria-label");
    }
  }
}

function renderWorld(result) {
  var facts = byId("world-facts");
  var note = byId("world-note");
  var table = byId("count-table");
  var scroller = byId("count-scroller");
  var rows = byId("count-rows");
  var list = byId("unmodeled-list");
  var listNote = byId("unmodeled-note");

  clear(facts);
  clear(note);
  clear(rows);
  clear(list);
  clear(listNote);
  table.hidden = true;
  scroller.hidden = true;

  var data = bodyData(result);
  if (!data) {
    var refusal = result && result.body ? result.body : null;
    var line = refusal && refusal.detail ? refusal.detail : "/api/world did not answer";
    var code = result && result.reached ? String(result.http) : UNREACHABLE;
    note.appendChild(document.createTextNode(code + " - " + line));
    listNote.appendChild(document.createTextNode("no world loaded"));
    return;
  }

  note.appendChild(document.createTextNode("200 - parsed and serialized by an allow-list"));
  facts.appendChild(fact("world token (masked)", data["world"]));
  for (var s = 0; s < WORLD_SCALARS.length; s += 1) {
    facts.appendChild(fact(WORLD_SCALARS[s][1], data[WORLD_SCALARS[s][0]]));
  }

  var counts = data["counts"] || {};
  table.hidden = false;
  scroller.hidden = false;
  for (var c = 0; c < COUNT_LABELS.length; c += 1) {
    var countRow = document.createElement("tr");
    countRow.appendChild(el("td", null, COUNT_LABELS[c][1]));
    countRow.appendChild(el("td", "count", counts[COUNT_LABELS[c][0]]));
    rows.appendChild(countRow);
  }

  var unknown = data["unknown_classes"] || [];
  if (!unknown.length) {
    listNote.appendChild(
      document.createTextNode(
        data["contains_unmodeled_content"]
          ? "this world carries content this build does not model"
          : "every class in this world resolved against the registry"
      )
    );
    return;
  }
  listNote.appendChild(
    document.createTextNode(unknown.length + " class path(s) this build does not model:")
  );
  for (var u = 0; u < unknown.length; u += 1) {
    list.appendChild(el("li", null, unknown[u]["type_path"] + "  x" + unknown[u]["count"]));
  }
}

/* --- the panel seam ----------------------------------------------------- */

/*
  CS-962 - WHY THIS SEAM EXISTS, AND WHAT IT IS NOT.

  Every panel this page will grow wants to touch two files: this one and
  index.html. That makes a queue out of work that has no reason to be ordered -
  two panels written at once collide in the same function, in the same file, for
  no better reason than that the page has only one script. The seam breaks that:
  a panel is its own module, it calls registerPanel once at load, and it never
  edits this file again.

  THIS FILE STILL OWNS ALL I/O, AND THAT IS THE WHOLE POINT OF PASSING data IN.
  refresh() probes the routes ONE AT A TIME, on a button and never on a timer,
  and both of those are properties of a single loop a reader can find. A panel
  that opened its own fetch would sit outside that loop, so the page's request
  behaviour would stop being readable in the file that documents it - and there
  would be nothing stopping ten panels from issuing ten concurrent requests on
  every repaint. A mount is handed what was ALREADY FETCHED and asks for
  nothing.

  A PANEL IS UNTRUSTED CODE AS FAR AS THIS LOOP IS CONCERNED. A mount that
  throws must cost its own panel and nothing else: without the guard below, one
  bad module empties the page of every panel registered after it, and the
  failure looks like "the dashboard is blank" rather than "one panel is
  broken". Each mount is therefore called inside its own try, and the failure is
  rendered where that panel would have been.

  NOTHING FROM THE EXCEPTION REACHES THE DOM. An error's message and stack on
  this machine can carry an absolute path, and a path here carries the Windows
  account name - non-negotiable 3. The failure note is built from the panel's
  own id, which is a string this repo authored.

  THE SECTIONS ARE KEPT; THEIR CONTENTS ARE NOT, AND THIS PARAGRAPH USED TO
  CLAIM OTHERWISE. It said the sections are "refilled, never rebuilt" so that
  whatever a keyboard reader was standing on inside a panel survives a repaint,
  and that was false in the way that matters: NO READER EVER STANDS ON A
  SECTION, they stand on its CHILDREN, and mountPanel empties every child
  before the mount runs. So a repaint replaces every control inside every
  panel, and a bench field a reader had typed into is a node no longer in the
  document with its value gone.

  WHAT IS ACTUALLY TRUE is narrower and is worth having on its own: the SECTION
  survives, so its id, its order on the page and its aria-labelledby target are
  stable across a repaint, and a panel that fails on one press does not lose its
  place on the next. KNOWN LIMITATION, recorded rather than papered over:
  whatever a reader was standing on INSIDE a panel does not survive a repaint.
  What this suite can measure of that is node identity and typed values, in
  tests/surface/test_panel_solve.py::test_a_repaint_rebuilds_the_bench_and_drops_typed_values
  - no browser runs here, so the focus consequence is reasoned from the audit
  refresh() records below and is NOT measured by any arm. The seam's job is
  therefore to make sure a repaint costs a reader only their input, and never
  an ANSWER it already paid for; see panelGeneration below.
*/

/* The element every panel's section is appended to, and the marker each carries. */
var PANEL_HOST = "panels";
var PANEL_STATE = "data-panel-state";
var PANEL_MOUNTED = "mounted";
var PANEL_FAILED = "failed";

/*
  Registered panels, in registration order, which is the order they render in.
  NAMED panelEntries AND NOT panels because the host element's id IS "panels",
  and a user agent exposes an id as a property of window - a top-level var of
  the same name shadows it, which works and reads as a bug forever after.
*/
var panelEntries = [];

/*
  The payloads of the last completed repaint, or null before the first one.
  A panel registering AFTER a repaint has landed is mounted immediately against
  this rather than waiting for the next press - a module that loaded late would
  otherwise leave a silent gap on the page until someone clicked Refresh.
*/
var panelPayloads = null;

function registerPanel(id, mountFn) {
  /*
    A registration is refused rather than half-accepted. A duplicate id would
    take a second slot pointing at the same section, so the two mounts would
    overwrite each other every repaint and the loser would be whichever
    happened to run first.
  */
  if (typeof id !== "string" || !id) {
    return false;
  }
  if (typeof mountFn !== "function") {
    return false;
  }
  for (var index = 0; index < panelEntries.length; index += 1) {
    if (panelEntries[index].id === id) {
      return false;
    }
  }

  var entry = { id: id, mount: mountFn };
  panelEntries.push(entry);
  if (panelPayloads) {
    /*
      THE PUBLISHED ID LIST IS REFRESHED BEFORE THE LATE MOUNT, or this module
      would be handed a roster missing the only member it is certain of -
      itself. panelPayloads is the payload of a repaint that finished before
      this registration, so its list was built without it.
    */
    panelPayloads.panels = panelIds();
    mountPanel(entry, panelPayloads);
  }
  return true;
}

function panelIds() {
  /*
    The registered ids, in registration order, as a FRESH array of strings.

    FRESH RATHER THAN THE LIVE ARRAY, because panelEntries holds this file's own
    bookkeeping - a mount handed it could splice a panel out of the page. What a
    panel gets is a copy of the ids and nothing else.
  */
  var ids = [];
  for (var index = 0; index < panelEntries.length; index += 1) {
    ids.push(panelEntries[index].id);
  }
  return ids;
}

function panelSection(id) {
  /* The section for one panel, created on first use and kept thereafter. */
  var host = byId(PANEL_HOST);
  var domId = "panel-" + id;
  var existing = byId(domId);
  if (existing) {
    return existing;
  }
  var section = el("section", "panel", null);
  section.id = domId;
  host.appendChild(section);
  return section;
}

function mountPanel(entry, data) {
  /* One panel, mounted into its own emptied section, with its throw contained. */
  var section = panelSection(entry.id);
  clear(section);
  try {
    entry.mount(section, data);
    section.setAttribute(PANEL_STATE, PANEL_MOUNTED);
  } catch (mountFailure) {
    clear(section);
    section.setAttribute(PANEL_STATE, PANEL_FAILED);
    section.appendChild(el("p", "note", "panel " + entry.id + " did not render"));
  }
}

function panelData(probes) {
  /*
    What a mount is handed: the parsed data object of each route this page
    probed, or null where that route did not answer with one. Keyed by the part
    of the path that names the domain, so a panel reads data.world rather than
    a path a future router could re-spell.
  */
  return {
    health: bodyData(probes["/api/health"]),
    world: bodyData(probes["/api/world"]),
    registry: bodyData(probes["/api/registry"]),
    advice: bodyData(probes["/api/advice"]),
    audit: bodyData(probes["/api/audit"]),
    plan: bodyData(probes["/api/plan"]),
    /*
      CS-977 - the Map panel's supply line. A parameterless GET like the five
      above it, so the page asks for it on a repaint and the panel is handed the
      answer; a panel issues no request of its own. NULL IS THE ORDINARY CASE
      HERE rather than an edge one: /api/map refuses with 503 whenever no world
      is loaded, and the Map panel renders that as a named refusal.
    */
    map: bodyData(probes["/api/map"]),
    /*
      THE PANEL ROSTER, WHICH IS NOT A PAYLOAD EITHER AND IS HERE FOR AN
      ANTI-DRIFT REASON. No route serves the list of panels this page carries,
      so a panel that needed it had two options and both were worse: read
      panelEntries out of this file's scope, which makes a private of this
      module part of every panel's contract, or carry a typed copy, which goes
      stale the first time a panel is added or renamed and goes stale SILENTLY.
      Publishing it here means there is exactly one place the list is derived
      and it is derived from the registrations themselves.

      ALWAYS AN ARRAY, NEVER ABSENT AND NEVER null. A reader has to be able to
      iterate it without first asking whether it exists, or the drift this
      removes comes back as a guard at every call site.
    */
    panels: panelIds(),
    /*
      THE SEVENTH KEY IS NOT A PAYLOAD AND IS NAMED SO IT CANNOT BE READ AS
      ONE. The six above are data a repaint already fetched; these are doors a
      panel may knock on. Calling the key "solve" would have put a verb in
      a list of nouns and invited the next reader to expect a solve RESULT
      here, which no repaint has and no repaint will.

      THREE DOORS AND NOT ONE, because three published routes take a parameter
      a repaint cannot supply: /api/solve and /api/optimize want a target
      basket, /api/power wants a building. Each was reachable from this page
      only by adding its door - /api/optimize answered 200 against real data for
      as long as the page never called it, which is the same "written and
      unreachable" fault /api/power's whole route was filed for.
    */
    actions: {
      requestSolve: requestSolve,
      requestOptimize: requestOptimize,
      requestPower: requestPower
    }
  };
}

/*
  HOW MANY TIMES THIS PAGE HAS TORN ITS PANELS DOWN AND BUILT THEM AGAIN.

  THE FAULT IT EXISTS TO CLOSE. A solve is asked for on a click and answered
  later; a repaint in between empties every panel's section. The bench holds its
  result region by closure - it has to, for the reason requestSolve documents -
  so when the answer arrived the seam handed it to a callback writing into nodes
  the repaint had already discarded. The reader's plan was computed, returned,
  and rendered into a node that is not in the document: no plan, no message, no
  error. A generation is captured when a request is accepted and compared before
  the answer is delivered, so an answer the repaint outran is DROPPED rather
  than written somewhere nobody can see it. The fresh bench says no solve has
  been asked for yet, which is the truth about the bench now on the page.

  WHY NOT REFUSE A REPAINT WHILE A SOLVE IS IN FLIGHT, which is the other shape
  this could take and reads simpler. Because there is no timeout anywhere on
  this page and no AbortController - by design, since the only thing that could
  fire one is a timer, and a timer-rebuilt panel is the mouse-only fault
  CONVENTIONS 13.3 records. So a request that never settles is possible, and
  under that rule it would freeze Refresh - the page's ONLY control - for the
  life of the page, with no reload of its own. That trades a silent wrong answer
  for a visible deadlock, which is not an improvement: the reader loses the
  whole page instead of one answer. Dropping the superseded answer costs the
  reader one press and leaves every control working.

  ADVANCED ONCE PER REPAINT, IN mountPanels, AND NOT ONCE PER MOUNT. mountPanel
  is also reached from registerPanel, where it empties the newly registered
  panel's own section and touches no other - advancing there would invalidate an
  in-flight request belonging to a panel whose nodes are all still in the
  document, which is the same silent drop wearing the opposite sign.
*/
var panelGeneration = 0;

function mountPanels(probes) {
  /* Every registered panel, in registration order, each isolated from the rest. */
  panelGeneration += 1;
  panelPayloads = panelData(probes);
  for (var index = 0; index < panelEntries.length; index += 1) {
    mountPanel(panelEntries[index], panelPayloads);
  }
}

/* --- the one request that is not a repaint ------------------------------ */

/*
  THE NAMES EACH ASKABLE ROUTE TAKES, SPELLED HERE AND NOWHERE ELSE. These
  tables are the reason a panel cannot widen a request: the door builder reads
  the names OUT OF THESE ARRAYS and copies the caller's values across, so a key
  the table does not name is not encoded - it makes the whole call refuse. Each
  endpoint answers 400 unknown_parameter to one anyway; what this buys is that a
  bad request is refused HERE, where the panel that made it can be told, rather
  than spent on a round trip.

  AN OPTIONAL NAME IS STILL A NAME FROM THIS TABLE. A panel may omit one and may
  not invent one, so the fence is exactly where it was when every door required
  everything: the panel chooses WHICH of these to send and never WHAT.
*/
var SOLVE_PARAMS = ["targets", "recipes", "raw_items", "byproduct_policy"];
var OPTIMIZE_PARAMS = [
  "targets",
  "candidates",
  "unlocked",
  "raw_items",
  "byproduct_policy",
  "objective"
];
var OPTIMIZE_OPTIONAL = ["backend"];
var POWER_PARAMS = ["building"];
var POWER_OPTIONAL = ["clock", "recipe"];

/*
  One row per door a panel may knock on: where it goes, what verb it answers,
  and which names it takes. THE VERB IS PER ROUTE AND NOT PER PAGE - the two
  solver doors answer POST because a request carries a target basket, and
  /api/power answers GET because it carries one building identifier.
*/
var REQUESTS = {
  solve: { path: "/api/solve", method: "POST", required: SOLVE_PARAMS, optional: [] },
  optimize: {
    path: "/api/optimize",
    method: "POST",
    required: OPTIMIZE_PARAMS,
    optional: OPTIMIZE_OPTIONAL
  },
  power: { path: "/api/power", method: "GET", required: POWER_PARAMS, optional: POWER_OPTIONAL }
};

/*
  Whether a request is already in flight. ONE FLAG FOR ALL THREE DOORS, not one
  each. The sibling of repainting below, and it exists for the same reason: one
  request at a time, refused rather than queued. A flag per door would let three
  panels have three requests outstanding at once, which is the concurrency this
  page's whole sequential-probe discipline exists to avoid.
*/
var asking = false;

function nameIsTaken(spec, name) {
  /* Whether this door's table names the parameter at all. */
  return spec.required.indexOf(name) >= 0 || spec.optional.indexOf(name) >= 0;
}

function requestQuery(spec, params) {
  /*
    The query string for one door, or null if the caller's object does not fit
    that door's table.

    EXACTLY, IN BOTH DIRECTIONS. Every name the caller states must be one this
    door takes, and every REQUIRED name must be stated, so neither a superset
    nor a short request gets encoded. An OPTIONAL name may be present or
    absent and nothing else may be either.

    THE ORDER IS THE TABLE'S, NOT THE CALLER'S OBJECT'S. Two identical requests
    therefore produce byte-identical query strings whatever order a panel built
    its keys in, which is the determinism property applied to the one thing on
    this page that leaves it.

    encodeURIComponent is applied to the NAME as well as the value - the names
    here are literals and need no escaping today, which is precisely why
    encoding them costs nothing and stops mattering only if someone later
    builds these tables from something that is not a literal.
  */
  if (!params || typeof params !== "object") {
    return null;
  }

  var stated = Object.keys(params);
  var index;
  for (index = 0; index < stated.length; index += 1) {
    if (!nameIsTaken(spec, stated[index])) {
      return null;
    }
  }
  for (index = 0; index < spec.required.length; index += 1) {
    if (!Object.prototype.hasOwnProperty.call(params, spec.required[index])) {
      return null;
    }
  }

  var ordered = spec.required.concat(spec.optional);
  var parts = [];
  for (index = 0; index < ordered.length; index += 1) {
    var name = ordered[index];
    if (!Object.prototype.hasOwnProperty.call(params, name)) {
      continue;
    }
    var value = params[name];
    if (typeof value !== "string") {
      return null;
    }
    parts.push(encodeURIComponent(name) + "=" + encodeURIComponent(value));
  }
  return parts.join("&");
}

function requestFetch(spec, query) {
  /*
    THE THREE REQUESTS THIS PAGE CAN ISSUE, EACH WRITTEN OUT WITH ITS PATH AND
    ITS VERB AS LITERALS. Every one of them could be reached from spec.path and
    spec.method in a single call, and that shape was written first and rejected:
    it makes "which URLs can this page reach, with which verbs" a question only
    answerable by following a table indirection, and it defeats the static arm
    in tests/surface/test_web_assets.py that counts the page's non-GET requests
    and pins each to a path. A security-relevant control that a refactor
    silently blinds is worse than three visible lines.

    NO BODY KEY ON ANY OF THEM. clockspeed/surface/server.py parses the query
    string and reads a request body nowhere at all, so a body would be ignored
    on arrival - and an unread body on a kept-alive HTTP/1.1 connection desyncs
    whatever request follows it on that socket. Omitting the key sends
    Content-Length: 0.
  */
  if (spec === REQUESTS.solve) {
    return fetch("/api/solve?" + query, {
      method: "POST",
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
  }
  if (spec === REQUESTS.optimize) {
    return fetch("/api/optimize?" + query, {
      method: "POST",
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
  }
  return fetch("/api/power?" + query, {
    method: "GET",
    headers: { "Accept": "application/json" },
    cache: "no-store"
  });
}

async function runRequest(spec, query, onSettled, generation) {
  /*
    The requests this page issues that are not repaints, folded into the same
    outcome shape probeRoute returns - with one difference that is load-bearing.
    The body handed back is the FULL parsed envelope and not bodyData, because a
    refusal carries its reason and its detail OUTSIDE data and a panel that
    could not read them would have to render a 400 as silence.
  */
  var outcome = { reached: false, http: null, body: null };
  try {
    var response = await requestFetch(spec, query);
    var payload = null;
    try {
      payload = await response.json();
    } catch (parseFailure) {
      payload = null;
    }
    outcome = { reached: true, http: response.status, body: payload };
  } catch (networkFailure) {
    outcome = { reached: false, http: null, body: null };
  } finally {
    /*
      IN THE finally FOR THE REASON refresh() RELEASES ITS OWN FLAG THERE. A
      request that throws once is a bad request; one that throws once and then
      refuses every later one is a dead bench, recoverable only by a reload.
    */
    asking = false;
  }

  if (generation !== panelGeneration) {
    /*
      THE PANELS WERE TORN DOWN AND REBUILT WHILE THIS WAS IN FLIGHT, so the
      nodes onSettled would write into are no longer in the document. Dropped
      HERE, after the flag above was lowered and never instead of lowering it:
      a gate that suppressed the answer by staying busy would leave the Solve
      button dead for the life of the page. See panelGeneration for why a
      superseded answer is dropped rather than a repaint refused.
    */
    return;
  }

  try {
    onSettled(outcome);
  } catch (settleFailure) {
    /*
      CONTAINED EXACTLY AS mountPanel CONTAINS A MOUNT, and swallowed rather
      than rendered. A panel is untrusted code as far as this loop is
      concerned, and an exception's message and stack on THIS machine carry an
      absolute path under a home directory - so putting one on the page would
      publish the operator's account name to whoever is looking at the screen.
      The flag is already lowered above, so a thrower costs its own panel a
      result and costs the bench nothing. The block is empty ON PURPOSE: there
      is no safe thing to do with what is in settleFailure.
    */
  }
}

function makeDoor(spec) {
  /*
    Build the one function a panel is handed for one route.

    Ask that route on behalf of a panel, and hand that panel the outcome when
    it settles. Returns true if the request was accepted, false if it was
    refused - and a false return means onSettled is NEVER called, so a caller
    that ignores the return value waits forever rather than seeing a fabricated
    answer.

    WHY A CALLBACK AND NOT A REPAINT. mountPanel empties a panel's section and
    mounts it again, so repainting the bench to show its result would discard
    the input the reader is standing in - verbatim the focus fault this file's
    header and refresh() both document. The callback lets the panel write into
    nodes it already holds, and nothing is torn down.

    REFUSED WHILE A REPAINT IS IN FLIGHT, because a repaint is about to empty
    and remount every section including the one that would receive this answer.

    ONE BUILDER RATHER THAN THREE HAND-WRITTEN DOORS. Each door differs only in
    its row of REQUESTS, so writing them out separately would be three copies of
    the generation gate, three copies of the busy flag and three chances for one
    of them to drift out of step with the other two - and the one that drifted
    would be the one that silently wrote an answer into a discarded node.
  */
  return function door(params, onSettled) {
    if (repainting || asking) {
      return false;
    }
    if (typeof onSettled !== "function") {
      return false;
    }

    var query = requestQuery(spec, params);
    if (query === null) {
      return false;
    }

    asking = true;
    /*
      THE GENERATION IS READ NOW AND COMPARED LATER. Captured at acceptance
      rather than at delivery, because the question the gate answers is whether
      the nodes this caller was holding WHEN IT ASKED are the nodes still on the
      page.
    */
    runRequest(spec, query, onSettled, panelGeneration);
    return true;
  };
}

var requestSolve = makeDoor(REQUESTS.solve);
var requestOptimize = makeDoor(REQUESTS.optimize);
var requestPower = makeDoor(REQUESTS.power);

/* --- one repaint, on demand, never on a schedule ------------------------ */

/*
  Whether a repaint is already in flight. Re-entry is refused against THIS, and
  the alternative it replaces is the subject of the comment inside refresh().
*/
var repainting = false;

async function refresh() {
  /*
    THE BUSY STATE IS aria-disabled AND A FLAG, NEVER button.disabled, and this
    is the CS-600 audit's finding rather than a preference.

    WHAT WAS MEASURED. This function used to set button.disabled = true for the
    length of the fetches. A user agent blurs a focused element the instant it
    becomes disabled, and nothing here put the focus back. On a genuine click,
    with the repaint confirmed landed - five fetches issued at the time, six
    since /api/registry joined the table, and a row node held
    from before the click no longer connected to the document - the focus
    events read focus, focusin, blur, focusout on the button and activeElement
    finished at BODY. Refresh is the ONLY control this page has, so every press
    dropped a keyboard reader to the top of the document and the second press
    meant tabbing back in from there.

    WHY NOT RESTORE FOCUS INSTEAD. Because a restore has to answer a question it
    cannot answer well: the fetches are asynchronous, and by the time they land
    the reader may have tabbed to a scroller or left the window entirely. A
    restore guarded on "only if nothing else took focus" is a race with a reader
    for a state that never needed disturbing. Not taking the focus away has no
    such state, and disabled costs one more thing besides - it removes the
    control from the tab order outright, so a reader tabbing during the fetches
    passes through a page whose only control has vanished.

    WHAT aria-disabled DOES AND DOES NOT DO. It announces the busy state and
    changes nothing else: the control stays focused, stays tabbable, and stays
    clickable. It is therefore a statement, and the flag below is what makes the
    statement true. A guard that lived only in the attribute would be a label on
    a door that still opens.
  */
  if (repainting) {
    return;
  }
  repainting = true;

  var button = byId("refresh");
  button.setAttribute("aria-disabled", "true");
  clear(button);
  button.appendChild(document.createTextNode(READING));

  try {
    var probes = {};
    for (var index = 0; index < ROUTES.length; index += 1) {
      var target = ROUTES[index].probe;
      if (target && !probes[target]) {
        probes[target] = await probeRoute(target);
      }
    }

    var liveness = renderHeader(probes["/api/health"]);
    renderEndpoints(liveness, probes);
    renderWorld(probes["/api/world"]);
    /*
      AFTER THE PROBES HAVE RESOLVED AND NEVER BEFORE. A panel is handed data,
      not a promise, so there is nothing for it to mount against until the
      loop above has finished. mountPanels cannot throw - every mount it makes
      is individually guarded - so it needs no try of its own here.
    */
    mountPanels(probes);
  } finally {
    /*
      A throw anywhere above must still give the button back. Without this the
      flag would latch and the page would be dead until a reload - a repaint
      that fails once is a bad repaint, and a repaint that fails once and then
      refuses to run again is a bad page.
    */
    clear(button);
    button.appendChild(document.createTextNode("Refresh"));
    button.removeAttribute("aria-disabled");
    repainting = false;
    /*
      IN THE finally AND NOT THE try, for the reason the button above is: a throw
      in any renderer must not leave the page permanently without a keyboard
      route to its scrollers while the button is cheerfully handed back.
    */
    syncScrollRegions();
  }
}

byId("refresh").addEventListener("click", refresh);
/*
  A SCROLLER'S OVERFLOW IS A FUNCTION OF THE VIEWPORT, so the tab stop has to be
  recomputed when the viewport changes and not only when the data does. Without
  this, widening the window from 375px leaves a stop on a box that no longer
  scrolls, and narrowing it leaves the only route to the right-hand columns
  unreachable from the keyboard.
*/
window.addEventListener("resize", syncScrollRegions);
/*
  BEFORE THE FIRST FETCH, NOT AFTER IT. The endpoint table overflows at 375px on
  its headings alone, so it needs a keyboard route from first paint. Deriving the
  stop only at the end of refresh() left it unreachable for a MEASURED 14641ms
  while the probes of the day resolved - there are more of them now, and the
  figure is left as measured rather than rescaled to a run nobody made; the
  count is not restated here because the ROUTES table below owns it and
  renderEndpoints recomputes it - the static markup this replaced carried the
  stop
  immediately, so a derived affordance that waits is a regression against it.
*/
syncScrollRegions();
refresh();
