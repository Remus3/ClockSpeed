"use strict";

/*
  CS-962 - the Scope panel. The page's statement about itself: which routes
  feed which panels, and what this dashboard cannot show at all.

  WHY A PANEL SPENDS ITS SPACE ON THIS. Every other panel answers a question
  about the factory. This one answers the question a reader cannot otherwise
  ask: where did that number come from, and what is missing from this screen?
  A registry figure is extracted from the game's shipped document, so a wrong
  one is wrong for everybody on this game build. A world figure is read out of
  this player's own save, so a wrong one is wrong for them alone. Those are
  different faults with different fixes, and a page that mixes them without
  saying so is a page whose every number has to be taken on trust.

  THE ABSENT FIGURE IS THE LARGER HAZARD. A reader who sees no power number
  and is told nothing concludes the power is zero. Non-negotiable 7 forbids
  that confident wrong answer in the data path; this panel applies the same
  rule to the surface. Every entry in the CANNOT-SHOW list names the place the
  thing is absent from, so a reader can send the request and see for
  themselves rather than take this file's word for it.

  TWO KINDS OF CLAIM, AND THEY ARE BUILT DIFFERENTLY. Anything a payload
  carries is READ - the unbacked route list comes off data.health.endpoints,
  the panel list comes off data.panels, presence comes off the health body.
  Anything no payload carries is STATED, and each stated sentence is pinned at
  the module that owns it by tests/surface/test_panel_scope.py, so a wire that
  starts serving one of these turns an arm red instead of leaving a sentence
  here to rot.

  A CLAIM ABOUT THE PAGE IS GRADED AGAINST THE PAGE, and it is graded that way
  because this file got one wrong. It used to tell the reader the page could not
  show a refusal's reason, its detail or its blocked_by, on the stated grounds
  that a panel is handed the reduced body and never the envelope. Two of the
  three were on screen as it said so: app.js reads blocked_by off every probe
  and prints it in the endpoint table, and prints a refusal detail in the World
  note. The premise was wrong too - the seam hands the solve bench's callback
  the WHOLE envelope, which is how that bench prints all three. A panel whose
  subject is verifiability may not assert something a sibling module on the same
  screen disproves, so the CANNOT-SHOW list now names only what no shipped asset
  renders, and test_no_envelope_member_the_seam_prints_is_called_absent derives
  that set from the assets rather than trusting this comment.

  IT NAMES NO OPEN ITEM ID. The id that blocks an unimplemented route rides on
  blocked_by, on the refusal envelope, which a repaint drops before a mount sees
  a body - and a panel may issue no request of its own, so nothing hands this
  module the id. The page does show it, read off the wire by app.js. Typing it
  HERE would be a claim this panel has no way of checking against the server, on
  a panel whose whole subject is what it can and cannot check.

  IT MUST NOT REQUEST ANYTHING. app.js owns every request this page makes and
  issues them one at a time on a button press. The second argument is what
  those requests already returned.
*/

/*
  WRAPPED IN AN IIFE, AS EVERY OTHER PANEL MODULE IS - CS-1026. Every helper
  here already lives inside the mount, so nothing leaks today; the wrapper is
  what keeps the next top-level helper added to this file out of the page's
  shared global scope, where a later script could silently replace it.
  tests/surface/test_panel_global_scope.py counts the names each module adds.
*/
(function () {
registerPanel("scope", function mountScope(root, data) {
  var UNKNOWN = "did not answer";

  function add(parent, tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== null && text !== undefined) {
      node.textContent = text;
    }
    parent.appendChild(node);
    return node;
  }

  function listOf(parent, domId, entries) {
    var list = add(parent, "ul", "paths", null);
    list.id = domId;
    for (var index = 0; index < entries.length; index += 1) {
      add(list, "li", null, entries[index]);
    }
    return list;
  }

  function group(heading, sources, note) {
    add(root, "h3", null, heading);
    add(root, "p", "lede", note);
    var list = add(root, "ul", "paths", null);
    for (var index = 0; index < sources.length; index += 1) {
      add(list, "li", null, sources[index]);
    }
  }

  function isArray(value) {
    /* Array.isArray, spelled out so a non-array payload is a branch. */
    return Object.prototype.toString.call(value) === "[object Array]";
  }

  /*
    THE PANEL LIST IS READ OFF THE SEAM, NOT TYPED. clockspeed/surface/
    server.py owns which panel modules are served; a second list written here
    would be the copy that goes stale. data.panels is what the seam actually
    registered on this load, in registration order, so this reports the page in
    front of the reader rather than the page somebody expected. An empty array
    is an answer and is printed as one - the seam publishes the key on every
    mount, so absent and empty are different facts.

    THE FALLBACK IS A BRIDGE AND IS MEANT TO BE DELETED. data.panels lands in
    app.js alongside this panel rather than before it, so a page served an older
    seam hands a payload with no such key. Reading panelEntries directly there
    is worse than reading the payload and better than printing an empty list,
    which would be this panel telling the reader that nothing registered while
    four panels are on the screen beside it. Remove this branch once no served
    app.js omits the key.
  */
  function registeredIds(payload) {
    var ids = [];
    var published = payload ? payload.panels : null;
    var index;
    if (!isArray(published)) {
      if (typeof panelEntries === "undefined" || !panelEntries) {
        return ids;
      }
      for (index = 0; index < panelEntries.length; index += 1) {
        ids.push(String(panelEntries[index].id));
      }
      return ids;
    }
    for (index = 0; index < published.length; index += 1) {
      ids.push(String(published[index]));
    }
    return ids;
  }

  /*
    THE UNBACKED ROUTES ARE READ OFF THE PAYLOAD. data.health.endpoints is the
    only thing a panel is handed that mentions them at all, and its values are
    narrowed by the server to two words. Anything not the live word is listed.
  */
  function unbackedRoutes(healthBody) {
    var routes = [];
    if (!healthBody || !healthBody.endpoints || typeof healthBody.endpoints !== "object") {
      return routes;
    }
    var templates = Object.keys(healthBody.endpoints);
    for (var index = 0; index < templates.length; index += 1) {
      var template = templates[index];
      if (healthBody.endpoints[template] !== "live") {
        routes.push(template + " - " + String(healthBody.endpoints[template]));
      }
    }
    return routes;
  }

  function presence(payload, healthWord, absentWord) {
    if (typeof healthWord === "string") {
      return healthWord + (payload ? ", and this page holds its body" : ", body not held");
    }
    return payload ? "body held" : absentWord;
  }

  var healthBody = data && data.health ? data.health : null;

  var heading = document.createElement("h2");
  heading.id = "h-panel-scope";
  heading.textContent = "Scope - what this page derives from, and what it cannot show";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  add(
    root,
    "p",
    "lede",
    "Each group below names a route and what it contributes. No count is written"
      + " beside them: the routes named are the tally, and a number typed next to"
      + " a list it does not come from has no way of staying right. A repaint"
      + " hands a panel a route's data object or null and drops the refusal"
      + " envelope; the one request that is not a repaint hands its envelope back"
      + " whole."
  );

  group(
    "REGISTRY-DERIVED",
    [
      "/api/registry - items, recipes and buildings extracted from the game's"
        + " shipped document. Registry: "
        + presence(data ? data.registry : null, healthBody ? healthBody.registry : null, UNKNOWN),
      "/api/solve - the ratio answer, computed from that same vocabulary and"
        + " returned as exact numerator and denominator pairs"
    ],
    "True for every player on this game build. Nothing here is read from a save."
  );

  group(
    "WORLD-DERIVED",
    [
      "/api/world - the header facts, the five collection sizes, the unlock"
        + " summary and the carried warnings. World: "
        + presence(data ? data.world : null, healthBody ? healthBody.world : null, UNKNOWN)
    ],
    "True for this save alone. A fault here is one player's, not the build's."
  );

  group(
    "HEALTH-DERIVED",
    [
      "/api/health - the version line, the two presence badges and the liveness"
        + " column of the endpoint table. Health: "
        + (healthBody ? "answered" : UNKNOWN)
    ],
    "What this server says about itself, which is not the same as what it does."
  );

  add(root, "h3", null, "PANELS REGISTERED ON THIS PAGE");
  var panelIds = registeredIds(data);
  listOf(root, "scope-panels", panelIds);
  if (!panelIds.length) {
    add(root, "p", "note", "the panel seam registered nothing this load.");
  }

  add(root, "h3", null, "ROUTES THIS SERVER REPORTS AS NOT IMPLEMENTED");
  var unbacked = unbackedRoutes(healthBody);
  listOf(root, "scope-pending", unbacked);
  if (!healthBody) {
    add(
      root,
      "p",
      "note",
      "/api/health " + UNKNOWN + ", so this list is unknown rather than empty."
    );
  } else if (!unbacked.length) {
    add(root, "p", "note", "every published route reports itself live.");
  }

  add(root, "h3", null, "CANNOT SHOW, AND WHERE IT IS ABSENT FROM");
  listOf(root, "scope-gaps", [
    "/api/world - objects and levels are counted and never listed: the body"
      + " carries the two sizes, no record and no level name.",
    "/api/world - nodes are counted and never listed: no node coordinate and no"
      + " node identity crosses the wire.",
    "the save file - node purity and resource type: a save stores deltas from"
      + " level defaults, so those bytes are never written to it at all.",
    "/api/world - purchased_schematics, recipes and scanned_resources are three"
      + " sizes: which schematic, which recipe and which resource is unlocked is"
      + " not served.",
    "/api/world - the world name, its filename and its path: only a one-way"
      + " masked token crosses, and it identifies a world without naming it.",
    "/api/registry - every building power figure and every recipe power term: a"
      + " building is served as an identifier and a display name and nothing"
      + " else.",
    "/api/registry - produced_in tokens that resolve to no modelled building:"
      + " the warning list carries them flagged instead.",
    "every route but /api/solve - the reason code of a refusal: a repaint"
      + " reduces a body to its data object before a panel sees it, and app.js"
      + " prints no reason of its own. Only the solve bench, which is handed a"
      + " whole envelope, prints one."
  ]);

  add(
    root,
    "p",
    "note",
    "An entry above is a thing the wire does not carry, not a thing this panel"
      + " chose to hide. Absent is not zero. A refusal that DOES reach the page"
      + " is printed where it lands: the blocked-by column of the endpoint table,"
      + " the World note, and the solve bench."
  );
});
}());
