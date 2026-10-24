"use strict";

/*
  CS-1240 - the Unmodelled content panel. It renders data.world.unmodelled:
  every class in this save that this build does not model, one row each, keyed
  by its STABLE ID - the class path, exactly as the save names it - with its
  record count in this save, the save it was first read in, and the reason it
  was skipped. Non-negotiable 7 says unknown content is flagged and skipped,
  never fatal and never silently wrong; this is where "flagged" becomes a list
  a person can act on.

  THIS PANEL COMPUTES NOTHING. clockspeed/save/sightings.py orders the rows by
  stable id, counts the saves read and decides which save first carried each
  class; clockspeed/surface/api/world.py only names those fields. The rows are
  rendered in the order the body carries them, and "this save" is printed only
  where the body's own first_seen equals its own this_save - a comparison of
  two numbers it was handed, never a count of anything.

  "FIRST READ" HAS A SCOPE, AND THE PANEL STATES IT IN WORDS. The ordinals count
  the distinct saves of this world the server has read SINCE IT STARTED (the
  CS-1240 adjudication): a restart forgets them, and a save written while the
  server was not running is never read. A reader told "first seen in save 1"
  without that sentence would read it as the first save ever written, which is
  the silently wrong half of non-negotiable 7.

  WHAT IS NEVER RENDERED. No path, no file name, no save time and no digest
  reaches this panel: the body carries ordinals, counts, class paths and a
  fixed reason sentence, and nothing else is read. A class path is publisher
  content - game or mod authored, never personal data - and the World section's
  unknown_classes list has always shown the same strings. Each one is built as
  a TEXT node, never parsed as markup, because a mod author chooses what it
  holds.

  EVERY FIELD IS SHAPE-CHECKED BEFORE IT IS PRINTED. A field that is not the
  shape the endpoint publishes reads "withheld" rather than rendering as
  something else - a fractional count, a non-string id or a missing ordinal is
  a defect upstream, and the honest rendering of a defect is to say so.

  WRAPPED IN AN IIFE so nothing here lands in the page's shared global scope,
  where a second panel declaring the same helper name would silently replace
  one of them (docs/history_notes.md records that shape for three panels).
*/
(function () {
  /*
    The panel id is the literal in the registerPanel call at the foot of this
    file, where tests/surface/test_panel_scope.py reads every module's id from.
  */
  var HEADING_ID = "h-panel-unmodelled";
  var SCOPE_WORD = "since-server-start";
  var WITHHELD = "withheld";

  /* The longest class path or reason sentence rendered. Longer reads withheld. */
  var TEXT_LIMIT = 512;

  /* Printable 7-bit ASCII, the only text this panel renders verbatim. */
  var FIRST_PRINTABLE = 0x20;
  var LAST_PRINTABLE = 0x7e;

  function el(tag, className, text) {
    /* One element, built with createElement and filled with textContent. */
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== null && text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function isArray(value) {
    /* Array.isArray, spelled out so a non-array payload is a branch. */
    return Object.prototype.toString.call(value) === "[object Array]";
  }

  function isObject(value) {
    /* A plain JSON object: not null, not an array. */
    return value !== null && typeof value === "object" && !isArray(value);
  }

  function isWholeNumber(value) {
    /* A count or an ordinal: a finite, non-negative integer, never a float. */
    return (
      typeof value === "number" && isFinite(value) && Math.floor(value) === value && value >= 0
    );
  }

  function printable(value) {
    /* A non-empty string of printable ASCII within the limit, or withheld. */
    if (typeof value !== "string" || value.length === 0 || value.length > TEXT_LIMIT) {
      return WITHHELD;
    }
    for (var index = 0; index < value.length; index += 1) {
      var code = value.charCodeAt(index);
      if (code < FIRST_PRINTABLE || code > LAST_PRINTABLE) {
        return WITHHELD;
      }
    }
    return value;
  }

  function wholeNumberText(value) {
    /* A whole number as text, or withheld. */
    return isWholeNumber(value) ? String(value) : WITHHELD;
  }

  function scopeStated(report) {
    /*
      Whether the body names the one scope this panel knows how to word, for a
      save that names a world. keyed must be exactly true: a save naming no
      world has no ordinals at all, and a keyed flag of any other shape is a
      defect upstream, not a world.
    */
    return (
      report["keyed"] === true &&
      report["scope"] === SCOPE_WORD &&
      isWholeNumber(report["this_save"]) &&
      isWholeNumber(report["saves_read"])
    );
  }

  function firstReadText(entry, report) {
    /*
      "this save" where the body's two ordinals are equal; otherwise which
      save, out of how many read. Withheld when the scope is not the one
      worded above, because an ordinal with an unknown scope is a number a
      reader cannot place.
    */
    var first = entry["first_seen"];
    if (!scopeStated(report) || !isWholeNumber(first)) {
      return WITHHELD;
    }
    if (first === report["this_save"]) {
      return "this save";
    }
    return "save " + String(first) + " of " + String(report["saves_read"]);
  }

  function cell(field, className, text) {
    /* A cell named by the field it renders, so a reader of the DOM can find it. */
    var node = el("td", className, text);
    node.setAttribute("data-field", field);
    return node;
  }

  function classRow(entry, report) {
    /* One unmodelled class: stable id, count, first read, reason. */
    var record = isObject(entry) ? entry : {};
    var row = document.createElement("tr");
    row.appendChild(cell("stable_id", "stable-id", printable(record["stable_id"])));
    row.appendChild(cell("count", "count", wholeNumberText(record["count"])));
    row.appendChild(cell("first_seen", null, firstReadText(record, report)));
    row.appendChild(cell("reason", null, printable(record["reason"])));
    return row;
  }

  function headerRow() {
    var head = document.createElement("thead");
    var row = document.createElement("tr");
    var labels = [
      ["Class path (stable id)", null],
      ["Records", "count"],
      ["First read", null],
      ["Why skipped", null]
    ];
    for (var index = 0; index < labels.length; index += 1) {
      var header = el("th", labels[index][1], labels[index][0]);
      header.setAttribute("scope", "col");
      row.appendChild(header);
    }
    head.appendChild(row);
    return head;
  }

  function table(classes, report) {
    /*
      THE TABLE GOES IN ITS OWN SCROLLER AND THE SCROLLER NAMES ITSELF. A class
      path is long, monospace and unbroken; app.js gives a .scroll-x box a tab
      stop exactly while it overflows and announces it by data-scroll-label.
    */
    var grid = document.createElement("table");
    grid.appendChild(headerRow());
    var body = document.createElement("tbody");
    for (var index = 0; index < classes.length; index += 1) {
      body.appendChild(classRow(classes[index], report));
    }
    grid.appendChild(body);
    var box = el("div", "scroll-x", null);
    box.setAttribute("data-scroll-label", "Unmodelled classes");
    box.appendChild(grid);
    return box;
  }

  function scopeNote(report) {
    /* The scope of "first read", in words, with this save's own ordinal. */
    if (report["keyed"] === false) {
      return el(
        "p",
        "note",
        "This save names no world, so no save is counted with it and every first read is" +
          " withheld - two saves naming no world are never taken for one world."
      );
    }
    if (!scopeStated(report)) {
      return el("p", "note", "the body did not state what first read counts, so no save is named");
    }
    return el(
      "p",
      "note",
      "First read counts the distinct saves of this world read since this server started;" +
        " this save is read " + String(report["this_save"]) + " of " +
        String(report["saves_read"]) + ". A save written while the server was not" +
        " running is never read, and a restart forgets every count."
    );
  }

  registerPanel("unmodelled", function mountUnmodelled(root, data) {
    /* data.world is the /api/world body, or null where that route did not answer. */
    var heading = el("h2", null, "Unmodelled content");
    heading.id = HEADING_ID;
    root.setAttribute("aria-labelledby", HEADING_ID);
    root.appendChild(heading);
    root.appendChild(
      el(
        "p",
        "lede",
        "Classes in this save that this build does not model, each listed by its class" +
          " path - the stable id, never a display name. Each one is flagged and skipped;" +
          " none is guessed at."
      )
    );

    /*
      EVERY BRANCH BELOW IS A CLAIM, SO EACH ONE IS TAKEN ONLY ON ITS OWN EXACT
      SHAPE. "did not answer", "not checked" and "every class resolved" are
      positive statements about the world; a body that is merely the wrong
      shape supports none of them, so it reads withheld instead (non-negotiable
      7). An absent list is not an empty list, and a checked flag that is not
      false is not "no property map was found".
    */
    var world = data ? data["world"] : null;
    if (!isObject(world)) {
      root.appendChild(el("p", "note", "/api/world did not answer, so nothing is listed"));
      return;
    }
    var report = world["unmodelled"];
    if (!isObject(report)) {
      root.appendChild(
        el("p", "note", "withheld - the world arrived without its unmodelled report, so nothing is listed")
      );
      return;
    }
    if (report["checked"] === false) {
      root.appendChild(
        el(
          "p",
          "note",
          "not checked - no property map was found, so no class in this save is called" +
            " modelled or unmodelled"
        )
      );
      return;
    }
    if (report["checked"] !== true) {
      root.appendChild(
        el(
          "p",
          "note",
          "withheld - the report did not say whether this save was checked, so nothing is listed"
        )
      );
      return;
    }
    var classes = report["classes"];
    if (!isArray(classes)) {
      root.appendChild(
        el("p", "note", "withheld - the class list did not arrive as a list, so nothing is listed")
      );
      return;
    }
    if (classes.length === 0) {
      root.appendChild(
        el("p", "note", "every class in this save resolved against the property map")
      );
      return;
    }
    root.appendChild(
      el(
        "p",
        "note",
        String(classes.length) + " unmodelled class(es) in this save, each skipped, none guessed"
      )
    );
    root.appendChild(scopeNote(report));
    root.appendChild(table(classes, report));
  });
})();
