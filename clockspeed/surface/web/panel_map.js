"use strict";

/*
  CS-977 - the Map panel. Where things are, what is in the containers, and how
  fast the extractors could run.

  THE OPERATOR ASKED THREE QUESTIONS AND THEY HAVE THREE DIFFERENT SHAPES.
  "What resources do I have" is a count and is exact. "Where is everything" is
  geometry and is exact. "How fast" is a rate that depends on a field the game
  never writes to a save, so it is three cases and not an answer. A panel that
  rendered all three in the same voice would be telling the reader that the
  third is as solid as the first two.

  WHY NO NODE ON THIS MAP IS LABELLED WITH A RESOURCE.
  docs/adr/0003-s4-node-actors-in-save.md measured mPurity, mResourceNodeType
  and mResourceClass at zero occurrences across three worlds and four builds: a
  save stores deltas from the level defaults and a node's type never changes
  from the level asset, so those bytes are simply not in the file. The node
  CLASS is available - the closed five-name vocabulary in
  clockspeed/save/world.py - and that is the whole of what a node can be called
  here. The page says so in a sentence rather than leaving a reader to infer
  iron from a dot, which is non-negotiable 7 applied to a surface: unknown
  content is flagged, never silently wrong.

  WHY THE BUTTONS ARE THE MECHANISM AND THE WHEEL IS THE EXTRA.
  This project has measured a browser automation pane silently faking wheel,
  resize, focus and default key scrolling - three false findings came out of
  one session that trusted it. A panel whose only zoom were a wheel handler
  would therefore be unverifiable by any instrument here AND unusable by a
  keyboard reader. So every capability - zoom in, zoom out, reset, and pan on
  four sides, plus one toggle per plotted class - is a real button carrying a
  real click handler, and tests/surface/test_panel_map.py drives those buttons.
  The wheel and pointer-drag handlers are attached on top, for a pointer in a
  real browser, and nothing depends on them.

  WHY PAN AND ZOOM ARE A viewBox REWRITE AND NOTHING ELSE.
  It is the simplest correct answer in SVG - one attribute holds the whole
  camera - and it is the only one the stand-in DOM in
  tests/surface/panel_harness.py can express: that harness offers no classList,
  no dataset, no children, no focus(), deliberately, because it must never be
  wider than the gate at tests/surface/test_panel_seam.py that mounts every
  shipped panel. A transform-based camera would be green in a browser and
  ungraded here.

  WHY THE NAMESPACE-AWARE CREATOR IS GUARDED.
  An SVG element has to be created in the SVG namespace or a browser builds an
  unknown HTML element that never paints. document.createElementNS is what does
  that, and the stand-in publishes createElement alone. The guard therefore
  takes the namespace path in every browser and the plain path only under the
  test stand-in, where nothing paints anyway - so the tree an arm reads is the
  same tree, tag for tag and attribute for attribute, as the one a browser
  renders. The namespace string is a NAME and never a request: no user agent
  dereferences it, and tests/surface/test_web_assets.py admits it by name in
  exactly that one position and nowhere else.

  WHY EVERY COORDINATE IS PRINTED VERBATIM.
  The wire ships coordinates as decimal strings - the shortest round-trip
  spelling of the stored float32 widened to a double - precisely so the reader
  can reconstruct the exact stored value. Reformatting one here would throw
  that away silently. So geometry is computed from the parsed numbers and every
  coordinate a reader SEES is the string this panel was handed, unaltered.
  There is therefore no rounding on this page to disclose.

  IT MUST NOT REQUEST ANYTHING. app.js owns every request the page makes. The
  second argument is what those requests already returned, and a null payload
  means the route did not answer with a body - which on a machine with no save
  loaded is its ordinary state, not a fault.
*/

registerPanel("map", function mountMap(root, data) {
  /* How much of the current extent one zoom press takes, and one pan press moves. */
  var NARROW = 0.5;
  var WIDEN = 2;
  var PAN_FRACTION = 0.2;

  /* A mark's radius and a built square's side, as a fraction of the home width. */
  var NODE_RADIUS_FRACTION = 120;
  var BUILT_SIDE_FRACTION = 90;

  /*
    The view width a pointer drag is measured against where the element has not
    been laid out yet. The stand-in reports clientWidth 0, and dividing by it
    would send the camera to infinity on the first move.
  */
  var DRAG_REFERENCE = 1000;

  /* The margin added round the world extent so an edge mark is not clipped. */
  var MARGIN_FRACTION = 0.04;

  /* The smallest extent a degenerate world is given, in the wire's own units. */
  var MIN_EXTENT = 1000;

  /* The purity cases the wire carries, in the order the game orders them. */
  var PURITIES = ["impure", "normal", "pure"];

  function add(parent, tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== null && text !== undefined) {
      node.textContent = String(text);
    }
    parent.appendChild(node);
    return node;
  }

  function svgEl(tag) {
    /*
      A namespaced element wherever the document can make one, which is every
      browser. See the preamble for why the fallback exists and why it changes
      no attribute of the tree.
    */
    if (typeof document.createElementNS === "function") {
      /*
        THE NAMESPACE IS SPELLED HERE AND IN NO OTHER POSITION IN THIS FILE, and
        that is a requirement rather than a preference.
        tests/surface/test_web_assets.py bans every absolute URL in a shipped
        asset and admits this one string INSIDE a createElementNS call - a
        position, not a spelling, so that the same characters in an href, a src
        or a CSS url() are still a finding. Bound to a named constant it would
        sit outside that position and the ban would fire, which is the guard
        working rather than the guard being in the way.
      */
      return document.createElementNS("http://www.w3.org/2000/svg", tag);
    }
    return document.createElement(tag);
  }

  function svgChild(parent, tag, className) {
    var node = svgEl(tag);
    if (className) {
      /*
        setAttribute AND NOT className. An SVG element's className is an
        SVGAnimatedString in a real browser and assigning a string to it does
        nothing at all, so the class would be silently absent on the one path
        that renders.
      */
      node.setAttribute("class", className);
    }
    parent.appendChild(node);
    return node;
  }

  function isArray(value) {
    /* Array.isArray, spelled out so a non-array payload is a branch. */
    return Object.prototype.toString.call(value) === "[object Array]";
  }

  function arrayOf(value) {
    return isArray(value) ? value : [];
  }

  function objectOf(value) {
    return value && typeof value === "object" && !isArray(value) ? value : {};
  }

  function number(value) {
    /*
      A finite number out of a wire string, or null. NEVER a default: a
      coordinate this panel cannot parse is a mark it does not draw and says it
      did not draw, rather than a mark it puts at the origin.
    */
    if (value === null || value === undefined || value === "") {
      return null;
    }
    var parsed = Number(value);
    if (parsed !== parsed || parsed === Infinity || parsed === -Infinity) {
      return null;
    }
    return parsed;
  }

  function spell(value) {
    /*
      A wire value exactly as it arrived, or a named absence. NEVER String() on
      its own: String(undefined) is the word "undefined", which reads to an
      operator as a value this panel computed rather than a key the body omitted.
    */
    if (value === null || value === undefined) {
      return "not served";
    }
    return String(value);
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function extent(low, high) {
    /*
      The span between two bounds, widened to MIN_EXTENT when the world is flat
      on that axis. A zero-width viewBox renders nothing and reads as an empty
      map, which is the confident wrong answer this panel exists to avoid.
    */
    var span = high - low;
    if (!(span > 0)) {
      return MIN_EXTENT;
    }
    return span;
  }

  var heading = document.createElement("h2");
  heading.id = "h-panel-map";
  heading.textContent = "Map - where everything is, and what the geometry cannot say";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  add(
    root,
    "p",
    "lede",
    "Placement comes out of the save exactly: every coordinate below is printed"
      + " in the spelling the wire carried, so nothing on this panel is rounded."
      + " What a resource node CONTAINS is a different matter - see the note"
      + " under the map."
  );

  var payload = data && data.map ? data.map : null;

  if (!payload) {
    /*
      A REFUSAL IS NAMED, NEVER DRAWN AS AN EMPTY MAP. The seam reduces a
      refusal envelope to a null body before a mount sees it, so this panel
      cannot read the reason code off the wire and does not pretend to. What it
      can say is which route did not answer and what the ordinary cause is.
    */
    add(
      root,
      "p",
      "note",
      "/api/map did not answer with a body, so nothing is drawn. On a machine"
        + " with no save loaded that route refuses with 503 and this is its"
        + " normal state rather than a fault. Press Refresh once a world is"
        + " loaded."
    ).id = "map-note";
    return;
  }

  var bounds = objectOf(payload.bounds);
  var nodes = arrayOf(payload.nodes);
  var built = arrayOf(payload.built);
  var nodeCounts = objectOf(payload.node_counts);
  var builtCounts = objectOf(payload.built_counts);
  var inventory = arrayOf(payload.inventory);
  var throughput = arrayOf(payload.throughput);
  var warnings = arrayOf(payload.warnings);
  var units = payload.coordinate_units ? String(payload.coordinate_units) : "unstated units";

  var minX = number(bounds.min_x);
  var maxX = number(bounds.max_x);
  var minY = number(bounds.min_y);
  var maxY = number(bounds.max_y);
  var boundsKnown = minX !== null && maxX !== null && minY !== null && maxY !== null;

  var worldWidth = boundsKnown ? extent(minX, maxX) : MIN_EXTENT;
  var worldHeight = boundsKnown ? extent(minY, maxY) : MIN_EXTENT;
  var marginX = worldWidth * MARGIN_FRACTION;
  var marginY = worldHeight * MARGIN_FRACTION;

  var home = {
    x: (boundsKnown ? minX : -MIN_EXTENT / 2) - marginX,
    y: (boundsKnown ? minY : -MIN_EXTENT / 2) - marginY,
    w: worldWidth + marginX * 2,
    h: worldHeight + marginY * 2
  };
  var view = { x: home.x, y: home.y, w: home.w, h: home.h };

  /* Which plotted classes the reader has hidden. Absent means shown. */
  var hiddenClasses = {};

  var svg = svgEl("svg");
  /*
    id IS SET AS A PROPERTY AND class THROUGH setAttribute, and the difference is
    not a style. Element.id is a plain string on every element including an SVG
    one; Element.className is an SVGAnimatedString on an SVG element and takes no
    string assignment at all.
  */
  svg.id = "map-svg";
  svg.setAttribute("class", "map-canvas");
  svg.setAttribute("role", "img");
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.setAttribute(
    "aria-label",
    "Plan view of the loaded world. Circles are resource nodes and squares are"
      + " built machines. The same figures are listed as text under the map."
  );

  var marks = svgChild(svg, "g", "map-marks");

  function viewBox() {
    return String(view.x) + " " + String(view.y) + " " + String(view.w) + " " + String(view.h);
  }

  function applyView() {
    /*
      THE ONE MECHANISM. Pan, zoom and reset all end here, so there is exactly
      one place the camera is written and exactly one attribute to read it back
      from.
    */
    svg.setAttribute("viewBox", viewBox());
  }

  function plot(records, tag, className, radius) {
    var drawn = 0;
    for (var index = 0; index < records.length; index += 1) {
      var record = records[index];
      var recordClass = record && record.class_name ? String(record.class_name) : "";
      if (hiddenClasses[recordClass]) {
        continue;
      }
      var x = number(record ? record.x : null);
      var y = number(record ? record.y : null);
      if (x === null || y === null) {
        continue;
      }
      var mark = svgChild(marks, tag, className);
      if (tag === "circle") {
        mark.setAttribute("cx", String(x));
        mark.setAttribute("cy", String(y));
        mark.setAttribute("r", String(radius));
      } else {
        mark.setAttribute("x", String(x - radius));
        mark.setAttribute("y", String(y - radius));
        mark.setAttribute("width", String(radius * 2));
        mark.setAttribute("height", String(radius * 2));
      }
      /*
        THE COORDINATE IS PRINTED VERBATIM, out of the record rather than out
        of the parsed number, so a reader hovering a mark sees the exact string
        the wire carried and this panel has rounded nothing.
      */
      var title = svgChild(mark, "title", null);
      title.textContent =
        (recordClass || "unnamed class")
          + " at x="
          + spell(record.x)
          + " y="
          + spell(record.y)
          + " z="
          + spell(record.z)
          + " "
          + units;
      drawn += 1;
    }
    return drawn;
  }

  function renderMarks() {
    clear(marks);
    plot(nodes, "circle", "map-node", home.w / NODE_RADIUS_FRACTION);
    plot(built, "rect", "map-built", home.w / BUILT_SIDE_FRACTION / 2);
  }

  function zoom(factor) {
    var centreX = view.x + view.w / 2;
    var centreY = view.y + view.h / 2;
    view.w = view.w * factor;
    view.h = view.h * factor;
    view.x = centreX - view.w / 2;
    view.y = centreY - view.h / 2;
    applyView();
  }

  function pan(stepX, stepY) {
    /*
      THE SENSE IS SCREEN SENSE. The SVG y axis grows DOWNWARDS, so panning
      south raises the y origin and panning north lowers it. Saying that here,
      at the one place it is applied, is cheaper than a reader deriving it from
      four call sites.
    */
    view.x = view.x + view.w * PAN_FRACTION * stepX;
    view.y = view.y + view.h * PAN_FRACTION * stepY;
    applyView();
  }

  function reset() {
    view.x = home.x;
    view.y = home.y;
    view.w = home.w;
    view.h = home.h;
    applyView();
  }

  function control(parent, label, handler) {
    var node = document.createElement("button");
    node.className = "map-control";
    node.setAttribute("type", "button");
    node.textContent = label;
    node.addEventListener("click", handler);
    parent.appendChild(node);
    return node;
  }

  add(root, "h3", null, "VIEW");
  add(
    root,
    "p",
    "lede",
    "Every capability here is a button, so it is reachable from a keyboard and"
      + " is gradable without a browser. Dragging and the wheel work too, in a"
      + " browser, and nothing depends on them."
  );

  var controls = add(root, "div", "map-controls", null);
  controls.id = "map-controls";
  control(controls, "Zoom in", function onZoomIn() {
    zoom(NARROW);
  });
  control(controls, "Zoom out", function onZoomOut() {
    zoom(WIDEN);
  });
  control(controls, "Reset view", function onReset() {
    reset();
  });
  control(controls, "Pan west", function onPanWest() {
    pan(-1, 0);
  });
  control(controls, "Pan east", function onPanEast() {
    pan(1, 0);
  });
  control(controls, "Pan north", function onPanNorth() {
    pan(0, -1);
  });
  control(controls, "Pan south", function onPanSouth() {
    pan(0, 1);
  });

  /*
    THE POINTER AFFORDANCES. A drag pans by the fraction of the view the pointer
    crossed; the wheel zooms. Every read off the event is guarded, because the
    stand-in dispatches an event object carrying four members and a handler that
    assumed a browser Event would throw inside a mount rather than in a browser.
  */
  var dragging = null;

  svg.addEventListener("wheel", function onWheel(event) {
    if (event && typeof event.preventDefault === "function") {
      event.preventDefault();
    }
    var delta = event && typeof event.deltaY === "number" ? event.deltaY : 0;
    zoom(delta > 0 ? WIDEN : NARROW);
  });
  svg.addEventListener("pointerdown", function onPointerDown(event) {
    if (!event || typeof event.clientX !== "number" || typeof event.clientY !== "number") {
      return;
    }
    dragging = { x: event.clientX, y: event.clientY };
  });
  svg.addEventListener("pointermove", function onPointerMove(event) {
    if (!dragging || !event || typeof event.clientX !== "number") {
      return;
    }
    var acrossX = event.clientX - dragging.x;
    var acrossY = event.clientY - dragging.y;
    dragging = { x: event.clientX, y: event.clientY };
    var pixels = svg.clientWidth > 0 ? svg.clientWidth : DRAG_REFERENCE;
    view.x = view.x - acrossX * (view.w / pixels);
    view.y = view.y - acrossY * (view.h / pixels);
    applyView();
  });
  svg.addEventListener("pointerup", function onPointerUp() {
    dragging = null;
  });

  root.appendChild(svg);

  add(
    root,
    "p",
    "note",
    "World extent, printed as the wire spelled it: x from "
      + spell(bounds.min_x)
      + " to "
      + spell(bounds.max_x)
      + ", y from "
      + spell(bounds.min_y)
      + " to "
      + spell(bounds.max_y)
      + ", z from "
      + spell(bounds.min_z)
      + " to "
      + spell(bounds.max_z)
      + " "
      + units
      + "."
  ).id = "map-note";

  /* --- the legend, derived from what this world actually holds ----------- */

  function legendEntries(list, counts, shape, kind) {
    var names = Object.keys(counts);
    var entries = [];
    for (var index = 0; index < names.length; index += 1) {
      var name = names[index];
      entries.push(
        add(
          list,
          "li",
          null,
          shape + " - " + kind + " - " + name + " - " + String(counts[name]) + " plotted"
        )
      );
    }
    return entries;
  }

  /*
    ONE LIST, TWO ROLES. This was a LEGEND and, forty lines further down, a
    second list under "WHAT THE MAP SHOWS, AS TEXT" built from the same two
    count maps by the same function - identical text, rendered twice, which a
    browser pass showed plainly and no arm could see because each list was
    graded on its own. A sighted reader read the same eleven lines twice and a
    screen reader announced them twice. The legend IS the text alternative, so
    it says so and the SVG points at it.
  */
  add(root, "h3", null, "LEGEND - AND THE MAP AS TEXT");
  add(
    root,
    "p",
    "note",
    "Every mark on the map is listed here, off the same counts the marks are"
      + " drawn from rather than a second tally. A reader who cannot see the"
      + " map loses nothing by reading this instead."
  );
  var legend = add(root, "ul", "map-legend", null);
  legend.id = "map-legend";
  svg.setAttribute("aria-describedby", legend.id);
  legendEntries(legend, nodeCounts, "circle", "resource node");
  legendEntries(legend, builtCounts, "square", "built machine");
  if (!Object.keys(nodeCounts).length && !Object.keys(builtCounts).length) {
    add(root, "p", "note", "this world reports no resource node and nothing built.");
  }
  if (!nodes.length) {
    add(root, "p", "note", "no resource node was served for this world.");
  }
  if (!built.length) {
    add(root, "p", "note", "nothing built was served for this world.");
  }

  add(
    root,
    "p",
    "note",
    "A node's purity and its resource type are NOT in a save file: the game"
      + " stores deltas from the level defaults and a node's type never changes"
      + " from the level asset, so those fields were measured at zero"
      + " occurrences across three worlds. This map can therefore say where a"
      + " node is and which of the five node classes it belongs to, and cannot"
      + " say what comes out of it."
  );

  /* --- filters, one per plotted class ----------------------------------- */

  add(root, "h3", null, "SHOW AND HIDE");
  var filters = add(root, "div", "map-controls", null);
  filters.id = "map-filters";

  function filter(name) {
    var node = document.createElement("button");
    node.className = "map-control map-filter";
    node.setAttribute("type", "button");
    node.textContent = "Hide " + name;
    node.setAttribute("aria-pressed", "false");
    node.addEventListener("click", function onToggle() {
      var nowHidden = !hiddenClasses[name];
      hiddenClasses[name] = nowHidden;
      node.textContent = (nowHidden ? "Show " : "Hide ") + name;
      node.setAttribute("aria-pressed", nowHidden ? "true" : "false");
      renderMarks();
    });
    filters.appendChild(node);
    return node;
  }

  var plottedClasses = Object.keys(nodeCounts).concat(Object.keys(builtCounts));
  for (var filterIndex = 0; filterIndex < plottedClasses.length; filterIndex += 1) {
    filter(plottedClasses[filterIndex]);
  }
  if (!plottedClasses.length) {
    add(root, "p", "note", "there is no population to filter.");
  }

  if (!plottedClasses.length) {
    add(legend, "li", null, "nothing to list: this world plotted no mark at all.");
  }

  /* --- what I have ------------------------------------------------------ */

  add(root, "h3", null, "WHAT I HAVE");
  var haveList = add(root, "ul", "paths", null);
  haveList.id = "map-inventory";
  for (var itemIndex = 0; itemIndex < inventory.length; itemIndex += 1) {
    var item = inventory[itemIndex];
    add(
      haveList,
      "li",
      null,
      (item && item.display_name ? String(item.display_name) : "unnamed item")
        + " - "
        + spell(item ? item.count : null)
    );
  }
  if (!inventory.length) {
    /*
      AN EMPTY INVENTORY NEEDS ITS REASON FOR THE SAME REASON AN EMPTY
      THROUGHPUT DOES. "No item was served" reads as "you are holding
      nothing", which on this project's own pinned world is false - the
      container payloads do not decode, and the wire says which layer flagged
      that and why. Printing the bare sentence made the page state a confident
      wrong answer, and a browser pass is where that became obvious.
    */
    add(haveList, "li", null, "no item total was served for this world.");
    var why = [];
    for (var reasonIndex = 0; reasonIndex < warnings.length; reasonIndex += 1) {
      var flagged = warnings[reasonIndex];
      if (flagged && flagged.code) {
        why.push(String(flagged.source) + ": " + String(flagged.code));
      }
    }
    add(
      haveList,
      "li",
      null,
      why.length
        ? "that is not a claim that you hold nothing. The reason served with it: "
          + why.join(", ")
        : "no reason was served with the empty answer, so this is an unexplained"
          + " empty result rather than a reading of an empty world."
    );
  }

  /* --- how fast, in three cases because purity is unmeasurable ---------- */

  add(root, "h3", null, "THROUGHPUT");
  add(
    root,
    "p",
    "note",
    "The rate on each row is EXACT and derived from the game's own shipped"
      + " numbers, and it is the rate at NORMAL purity. Purity is not in a save"
      + " file, so which case applies to any one machine is unknown, and the"
      + " multipliers shown beside the rate are an ASSUMPTION this project has"
      + " not measured from any file on this machine - the wire says so on every"
      + " row and this panel repeats it rather than quietly rounding it off."
  );

  function rateName(entry) {
    if (entry && entry.display_name) {
      return String(entry.display_name);
    }
    if (entry && entry.class_name) {
      return String(entry.class_name);
    }
    return "unnamed machine";
  }

  var rates = add(root, "ul", "paths", null);
  rates.id = "map-throughput";
  for (var rateIndex = 0; rateIndex < throughput.length; rateIndex += 1) {
    var entry = throughput[rateIndex];
    /*
      THE WIRE CARRIES ONE MEASURED RATE AND A SCALING IT DECLARES UNMEASURED,
      and this renders them as two different kinds of statement on purpose. An
      earlier draft printed three equal-looking figures, which presented an
      assumption in the same voice as a derivation.
    */
    var normal = entry ? entry.per_minute_normal : null;
    var scaling = objectOf(entry ? entry.purity_scaling : null);
    var measured = entry ? entry.purity_scaling_measured === true : false;
    var unit = entry && entry.per_minute_unit ? String(entry.per_minute_unit) : "per minute";
    var line = rateName(entry) + " - " + spell(entry ? entry.built : null) + " built - ";

    if (normal === null || normal === undefined) {
      /*
        A NULL RATE IS NOT A ZERO. The registry carries no extraction rate for
        this class, and printing a zero here would be a confident figure a plan
        cannot detect as wrong - the same argument the registry's own model
        makes for refusing to default an absent value.
      */
      line += "no rate is published for this machine, so none is shown";
    } else {
      line += String(normal) + " " + unit + " each at NORMAL purity";
      var others = [];
      for (var purityIndex = 0; purityIndex < PURITIES.length; purityIndex += 1) {
        var purity = PURITIES[purityIndex];
        if (purity !== "normal" && scaling[purity] !== undefined) {
          others.push(purity + " x" + String(scaling[purity]));
        }
      }
      if (others.length) {
        line += "; " + others.join(", ")
          + (measured ? " (scaling measured)" : " (scaling ASSUMED, not measured)");
      }
    }

    add(rates, "li", null, line);
  }

  if (!throughput.length) {
    /*
      AN EMPTY SECTION WOULD READ AS "YOU HAVE NO EXTRACTORS". The wire carries
      a warning saying why the array is empty, and that is what goes here. A
      body that carried no warning is reported as carrying none rather than
      rendered as an empty box.
    */
    var reasons = [];
    for (var warnIndex = 0; warnIndex < warnings.length; warnIndex += 1) {
      var record = warnings[warnIndex];
      /*
        EVERY SOURCE, NOT JUST "map". The layers below author their own source -
        "placement" and "inventory" - and the endpoint serves those verbatim
        rather than remapping them, because the source field is the one thing
        that says which layer flagged it. Filtering on one source here dropped
        exactly the warnings that explain an empty answer.
      */
      if (record && record.code) {
        reasons.push(String(record.code));
      }
    }
    if (reasons.length) {
      add(
        rates,
        "li",
        null,
        "no throughput was served, and /api/map gives the reason: " + reasons.join(", ")
      );
    } else {
      add(
        rates,
        "li",
        null,
        "no throughput was served and the body carried no reason for it. This is"
          + " not a claim that nothing extracts: it is an unexplained empty"
          + " answer, and it is reported as one."
      );
    }
  }

  renderMarks();
  applyView();
});
