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

  WHY THIS PAGE ISSUES NO POST AT ALL. Two of the nine routes take a body and
  one takes a state change. Exercising any of them from here would put a
  state-changing request on a page an operator leaves open, which is the whole
  precondition for request forgery. Their liveness is read from the endpoint map
  /api/health already publishes, so the skeleton stays GET-only and the question
  does not arise.

  WHY FOUR ROWS SAY "not probed". The server's router matches a request path
  against registered templates EXACTLY and refuses to register a template
  carrying a path parameter, so the two /api/advice/<id>/... routes have no
  concrete path to ask for. The other two take a body this page will not send.
  For those four the page prints what /api/health says and names that as the
  source, rather than inventing a transport code it never observed.
*/

/*
  The nine routes BOOTSTRAP.md section 7.1 publishes, in that section's order,
  each with the verb its own endpoint module registers and the concrete path -
  if there is one - this page may safely ask for with a GET.
*/
var ROUTES = [
  { template: "/api/health", method: "GET", probe: "/api/health" },
  { template: "/api/world", method: "GET", probe: "/api/world" },
  { template: "/api/advice", method: "GET", probe: "/api/advice" },
  { template: "/api/advice/<id>/derivation", method: "GET", probe: null },
  { template: "/api/advice/<id>/state", method: "POST", probe: null },
  { template: "/api/solve", method: "POST", probe: null },
  { template: "/api/optimize", method: "POST", probe: null },
  { template: "/api/audit", method: "GET", probe: "/api/audit" },
  { template: "/api/plan", method: "GET", probe: "/api/plan" }
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

function renderWorld(result) {
  var facts = byId("world-facts");
  var note = byId("world-note");
  var table = byId("count-table");
  var rows = byId("count-rows");
  var list = byId("unmodeled-list");
  var listNote = byId("unmodeled-note");

  clear(facts);
  clear(note);
  clear(rows);
  clear(list);
  clear(listNote);
  table.hidden = true;

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
    with the repaint confirmed landed - five fetches issued, and a row node held
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
  }
}

byId("refresh").addEventListener("click", refresh);
refresh();
