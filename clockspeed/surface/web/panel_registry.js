"use strict";

/*
  CS-962 - the Registry panel. What the extraction found, named on the page.

  THE DEFECT THIS REPLACES. /api/registry was probed on every repaint and only
  its HTTP STATUS ever reached the DOM: a badge that said "registry: present"
  and not one item, recipe or building name beside it. The solve bench's whole
  vocabulary is the identifiers that route carries, so a caller had no way to
  learn one from the page and had to invent it. This panel makes a lookup
  possible: every key, every display name, and the exact measurements attached.

  IT DOES NOT ASK FOR ANYTHING. app.js owns every request this page makes and
  issues them one at a time on a button press. The second argument is what those
  requests already returned, and this module never opens one of its own - see
  the seam's own note in app.js. A panel outside that loop would put the page's
  request behaviour outside the file that documents it.

  THIS FILE IS THE NETWORK DETECTOR'S CLEAN BASELINE, and that is a property of
  its NAME. tests/surface/test_panel_seam.py takes PANEL_MODULES[0] - sorted,
  this file - as the text every network primitive is concatenated onto to prove
  the detector can fire. Two consequences that outlive whoever reads this next:
  a sink word anywhere in this file breaks the arm that grades ALL FOUR panels,
  and because the baseline is a concatenation PREFIX, a sink here would make the
  fire-check compute an empty set and report PASS while grading nothing. The
  stripper that builds the baseline removes BLOCK comments only, so a line
  comment is code as far as it is concerned. This file therefore documents
  itself in block comments exclusively, and tests/surface/test_panel_registry.py
  pins both that rule and the ordering that makes this file the baseline.

  EVERY MEASUREMENT IS RENDERED FROM THE PAIR THE WIRE CARRIED. A duration, an
  energy value and a recipe amount arrive as {num, den} exact integers, because
  non-negotiable 6 does not stop at the browser. The PAIR is the truth and is
  what is shown. A rounded decimal may sit beside it and does, because 10/3 is
  unreadable as a stopwatch reading - but it is labelled an approximation every
  single time, and it is computed by exact integer long division rather than by
  dividing: the digits come out of repeated subtraction, so no floating-point
  quotient exists anywhere in this file to be mistaken for the value.

  ABSENT IS NOT ZERO. energy_value and sink_points are both nullable, and the
  data layer states plainly that None and zero are different facts: one entry
  declares its energy content to be nothing, another declares nothing at all. A
  confident zero over the second is the one unacceptable rendering, so an absent
  measurement renders as words and never as a digit.

  A NULL PAYLOAD IS A STATE, NOT A FAILURE. A panel is handed data or null and
  never a reason - app.js reduces the envelope before the mount sees it - so the
  most this panel can truthfully say is that the route did not answer. It says
  exactly that, and renders no number at all in that state: a zero on screen
  cannot be told apart from "the registry holds nothing", and only one of those
  two is something the panel knows.
*/

(function () {
  /*
    Everything below is scoped to this call. Panel modules are evaluated in one
    shared global, so a top-level helper here would be a global other panels
    could silently shadow - and four of these modules are written in parallel.
  */

  /* How many rows of one collection are listed before the roster is cut. */
  var ROSTER_CAP = 25;

  /* Decimal places in the labelled approximation beside a ratio. */
  var DECIMAL_PLACES = 3;

  /*
    The largest denominator the long division below stays exact for. It carries
    a remainder strictly less than the denominator and multiplies it by ten, so
    ten times the denominator must remain an exactly representable integer.
  */
  var SAFE_DENOMINATOR = 900000000000000;

  var ZERO_CODE = "0".charCodeAt(0);

  /* The word that marks a decimal as not the value beside it. */
  var APPROX = "approx. ";

  /* What an absent measurement renders as. Never a digit. */
  var ABSENT = "not declared";

  /*
    THE WARNING STREAM IS GUARDED, AND THE REASON IS THE PAGE AND NOT THIS
    PANEL. panel_warnings.js renders the same KIND of record - a code, a
    subject, a consequence line and a count - and runs every field through a
    per-field allowlist, substituting a visible marker for anything outside it.
    This panel rendered its own warnings through a bare string check. So one
    value could be withheld in the Warnings table and printed in full in the
    Registry table, in the same document, in the same screenshot that
    tools/dashboard_probe.py writes to a file. Two sinks over one record class
    means the page is only as careful as the weaker of them, and a leak into an
    image file is what non-negotiables 3, 11 and 12 forbid.

    WHAT CAN ACTUALLY REACH THESE FIELDS - read, not assumed. Every
    RegistryWarning in the project is built at one site,
    clockspeed/data/registry.py::_WarningLog.emit, fed by sixteen log.add calls
    in that one module. Their subjects are a ClassName, a group short name from
    clockspeed/data/docs_extract.py::derive_short_name, an item key, a
    produced-in token from clockspeed/data/registry.py::_class_name_from_path,
    and a group index rendered with str(). Their details are f-strings over
    that module's own KEY_* constants, plus the four closed reasons whose first
    is clockspeed/data/docs_extract.py::REASON_NOT_A_MAPPING. THE VERDICT: this
    stream is publisher-owned. It is built from the shipped game data file and
    nothing save-derived, no header field, no account id and no world name can
    reach any of it. That is narrower than the world warning stream one panel
    over, and it is why no rule here treats a non-ASCII character as evidence of
    a player display name: there is no player anywhere in this provenance.

    A GUARD IS SHIPPED ANYWAY, AND IT IS AN ALLOWLIST. The verdict above is a
    statement about today's producers, and a sink that trusts an audit has no
    defence the day the audit goes stale. A denylist of bad substrings is not a
    defence either - one defect wears a different field each time. So a value is
    rendered only by being INSIDE a stated set, never by failing to match
    something bad.

    THE SUBJECT SET IS DELIBERATELY WIDER THAN THE SIBLING'S, and copying the
    sibling's would have been a defect of its own. Its token set excludes the
    forward slash and admits exactly one slash-bearing exception, digits over
    digits. But this stream carries slash-bearing subjects LEGITIMATELY:
    clockspeed/data/blobs.py::parse_class_paths returns whatever sits between
    two double quotes verbatim, and
    clockspeed/data/registry.py::_class_name_from_path returns the WHOLE path
    when the token holds no "." separator at all. That module says plainly that
    dropping such a token erases the evidence it was ever present - so
    withholding it here would hide the very thing flag-and-skip exists to
    publish. An object path is therefore accepted, but only as a whole shape:
    rooted, and every segment between separators a bare token.

    WHAT THAT SHAPE CANNOT WEAR is a path on this machine. A Windows path needs
    a drive colon or a reverse separator, and neither character is in any set
    here. THE ONE RESIDUAL, stated rather than argued away: a POSIX-style home
    path is rooted and its segments are bare tokens, so this shape would admit
    one. No producer read above can put one there, and the platform this runs on
    does not spell a home directory that way - but that is a claim about today,
    which is exactly the kind of claim the paragraph before this one refuses to
    rest on. Narrowing further would need a denylist, and a denylist is the
    thing that has already leaked four times.

    WITHHELD IS RENDERED, NOT DROPPED. A refused field leaves a visible marker
    and its warning's code and count still show, so a reader learns that
    something was flagged. Omitting the row would make a refusal and an absence
    indistinguishable, which is the collapse the data layer refuses one floor
    down when it insists that absent is not zero.
  */

  /* Letters and digits, shared by every set below. */
  var ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  /* A warning code: the WARN_* spellings are lowercase and hyphenated. */
  var SET_CODE = ALNUM + "-";

  /* One bare token: a ClassName, a group short name, an index. */
  var SET_TOKEN = ALNUM + "_.-";

  /* Authored prose. No separator of either hand, and no colon. */
  var SET_DETAIL = ALNUM + " ,.;'()_-";

  /* An authored line is short. A dumped buffer or a deep path is not. */
  var DETAIL_LIMIT = 400;
  var TOKEN_LIMIT = 120;

  /* What stands in for a value whose shape this panel does not accept. */
  var WITHHELD = "[withheld - unexpected shape]";

  function absolute(value) {
    return value < 0 ? -value : value;
  }

  function isCountable(value) {
    return typeof value === "number" && Number.isSafeInteger(value);
  }

  /*
    ONE DECIMAL, PRODUCED WITHOUT DIVIDING. The numerator's own decimal digits
    are consumed left to right; each output digit is found by subtracting the
    denominator until the running remainder no longer covers it, which is at
    most nine subtractions because the remainder entering each step is smaller
    than the denominator. The result is the exact truncation of the ratio to the
    requested number of places - not a rounding of a quotient somebody computed.
  */
  function longDivide(num, den, places) {
    if (!isCountable(num) || !isCountable(den)) {
      return null;
    }
    var d = absolute(den);
    if (d === 0 || d > SAFE_DENOMINATOR) {
      return null;
    }
    var negative = num < 0 !== den < 0;
    var digits = String(absolute(num));
    var whole = "";
    var remainder = 0;
    var index;
    var digit;
    for (index = 0; index < digits.length; index += 1) {
      remainder = remainder * 10 + (digits.charCodeAt(index) - ZERO_CODE);
      digit = 0;
      while (remainder >= d) {
        remainder -= d;
        digit += 1;
      }
      whole += String(digit);
    }
    while (whole.length > 1 && whole.charAt(0) === "0") {
      whole = whole.substring(1);
    }
    var fraction = "";
    for (index = 0; index < places; index += 1) {
      remainder = remainder * 10;
      digit = 0;
      while (remainder >= d) {
        remainder -= d;
        digit += 1;
      }
      fraction += String(digit);
    }
    return (negative ? "-" : "") + whole + "." + fraction;
  }

  function isPair(value) {
    return (
      value !== null &&
      typeof value === "object" &&
      isCountable(value["num"]) &&
      isCountable(value["den"])
    );
  }

  /* The exact ratio, which is the value. Never a decimal. */
  function pairText(value) {
    if (!isPair(value)) {
      return ABSENT;
    }
    return String(value["num"]) + "/" + String(value["den"]);
  }

  /*
    The approximation beside the ratio, carrying its own label. A pair the long
    division cannot render exactly gets no decimal at all rather than a decimal
    nobody checked - an unlabelled or unverified number is the failure mode this
    whole rendering rule exists to prevent.
  */
  function approximateText(value) {
    if (!isPair(value)) {
      return ABSENT;
    }
    var rendered = longDivide(value["num"], value["den"], DECIMAL_PLACES);
    if (rendered === null) {
      return "no approximation";
    }
    return APPROX + rendered;
  }

  function countText(value) {
    return isCountable(value) ? String(value) : ABSENT;
  }

  function textOf(value) {
    return typeof value === "string" ? value : "";
  }

  /*
    True when every character of value is in allowed and the length is inside
    limit. The scan is an allowlist: a character is accepted by being present in
    the set, never by failing to match something bad.
  */
  function withinSet(value, allowed, limit) {
    if (typeof value !== "string") {
      return false;
    }
    if (value.length === 0 || value.length > limit) {
      return false;
    }
    for (var index = 0; index < value.length; index += 1) {
      if (allowed.indexOf(value.charAt(index)) === -1) {
        return false;
      }
    }
    return true;
  }

  /*
    THE ONE SHAPE CARRYING A SEPARATOR THAT THIS PANEL ACCEPTS. An Unreal object
    path is rooted and every segment between separators is a bare token, so the
    whole string is checked as a shape rather than character by character. A
    drive-rooted path fails on its first segment, because a drive marker is a
    colon and a colon is in no set here.
  */
  function isObjectPath(value) {
    if (typeof value !== "string" || value.length > TOKEN_LIMIT) {
      return false;
    }
    var segments = value.split("/");
    if (segments.length < 2 || segments[0] !== "") {
      return false;
    }
    for (var index = 1; index < segments.length; index += 1) {
      if (!withinSet(segments[index], SET_TOKEN, TOKEN_LIMIT)) {
        return false;
      }
    }
    return true;
  }

  /* A warning code, out of the closed set the data layer declares. */
  function safeCode(value) {
    return withinSet(value, SET_CODE, TOKEN_LIMIT) ? value : WITHHELD;
  }

  /* A subject or an unknown-group name: a bare token, or a rooted path. */
  function safeToken(value) {
    if (withinSet(value, SET_TOKEN, TOKEN_LIMIT) || isObjectPath(value)) {
      return value;
    }
    return WITHHELD;
  }

  /* An authored consequence line. */
  function safeDetail(value) {
    return withinSet(value, SET_DETAIL, DETAIL_LIMIT) ? value : WITHHELD;
  }

  function listOf(value) {
    return value !== null && typeof value === "object" && value.length >= 0 ? value : [];
  }

  function mapOf(value) {
    return value !== null && typeof value === "object" ? value : {};
  }

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== null && text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  /*
    A CELL NAMES THE FIELD IT RENDERS. The name is an attribute rather than a
    class because the class carries presentation and one cell wants both, and
    because a test selecting on a class compares the whole class string - a
    two-token class would select nothing and read exactly like a cell that was
    never built.
  */
  function cell(field, className, text) {
    var node = element("td", className, text);
    node.setAttribute("data-field", field);
    return node;
  }

  function headerRow(labels) {
    var head = document.createElement("thead");
    var row = document.createElement("tr");
    for (var index = 0; index < labels.length; index += 1) {
      row.appendChild(element("th", null, labels[index]));
    }
    head.appendChild(row);
    return head;
  }

  /*
    EVERY TABLE GOES IN ITS OWN SCROLLER, AND EVERY SCROLLER NAMES ITSELF. The
    stylesheet gives .scroll-x the horizontal overflow, and app.js gives it a
    tab stop exactly while it overflows and announces it by data-scroll-label -
    falling back to "Content", which names nothing a reader could act on.
  */
  function scroller(label, table) {
    var box = element("div", "scroll-x", null);
    box.setAttribute("data-scroll-label", label);
    box.appendChild(table);
    return box;
  }

  function emptyRow(columns, message) {
    var row = document.createElement("tr");
    var note = element("td", "empty", message);
    note.setAttribute("colspan", String(columns));
    note.setAttribute("data-field", "empty");
    row.appendChild(note);
    return row;
  }

  /*
    THE ROSTER IS BOUNDED AND SAYS SO WHEN IT BOUNDS. A real registry runs to
    thousands of entries; a panel that listed all of them would stop being
    readable, and a panel that silently listed the first few would be lying by
    omission. The cut is declared with both numbers.
  */
  function rosterNote(shown, total) {
    if (total <= shown) {
      return null;
    }
    return element(
      "p",
      "note",
      "listing the first " + String(shown) + " of " + String(total) + "; the rest are " +
        "on the route itself."
    );
  }

  function section(root, title, label, headers, rows, message) {
    root.appendChild(element("h3", null, title));
    var total = rows.length;
    var shown = total > ROSTER_CAP ? ROSTER_CAP : total;
    var note = rosterNote(shown, total);
    if (note) {
      root.appendChild(note);
    }
    var table = document.createElement("table");
    table.appendChild(headerRow(headers));
    var body = document.createElement("tbody");
    if (total === 0) {
      body.appendChild(emptyRow(headers.length, message));
    }
    for (var index = 0; index < shown; index += 1) {
      body.appendChild(rows[index]);
    }
    table.appendChild(body);
    root.appendChild(scroller(label, table));
  }

  function itemRow(entry) {
    var record = mapOf(entry);
    var row = document.createElement("tr");
    row.appendChild(cell("item_key", "route", textOf(record["key"])));
    row.appendChild(cell("item_name", null, textOf(record["display_name"])));
    row.appendChild(cell("item_form", "dim", textOf(record["form"])));
    row.appendChild(cell("item_fluid", "dim", record["is_fluid"] === true ? "fluid" : "solid"));
    row.appendChild(cell("item_energy", "count", pairText(record["energy_value"])));
    row.appendChild(
      cell("item_energy_approx", "dim", approximateText(record["energy_value"]))
    );
    row.appendChild(cell("item_sink", "count", countText(record["sink_points"])));
    return row;
  }

  function sideText(sides) {
    var parts = [];
    var list = listOf(sides);
    for (var index = 0; index < list.length; index += 1) {
      var side = mapOf(list[index]);
      parts.push(pairText(side["amount"]) + " " + textOf(side["item_key"]));
    }
    return parts.length ? parts.join(", ") : "none";
  }

  function recipeRow(entry) {
    var record = mapOf(entry);
    var row = document.createElement("tr");
    row.appendChild(cell("recipe_key", "route", textOf(record["key"])));
    row.appendChild(cell("recipe_name", null, textOf(record["display_name"])));
    row.appendChild(cell("recipe_duration", "count", pairText(record["duration"])));
    row.appendChild(cell("recipe_duration_approx", "dim", approximateText(record["duration"])));
    row.appendChild(cell("recipe_inputs", "dim", sideText(record["inputs"])));
    row.appendChild(cell("recipe_outputs", "dim", sideText(record["outputs"])));
    row.appendChild(cell("recipe_produced_in", "dim", listOf(record["produced_in"]).join(", ")));
    return row;
  }

  function buildingRow(entry) {
    var record = mapOf(entry);
    var row = document.createElement("tr");
    row.appendChild(cell("building_key", "route", textOf(record["key"])));
    row.appendChild(cell("building_name", null, textOf(record["display_name"])));
    return row;
  }

  function warningRow(entry) {
    var record = mapOf(entry);
    var row = document.createElement("tr");
    row.appendChild(cell("warning_code", "route", safeCode(record["code"])));
    row.appendChild(cell("warning_subject", "route", safeToken(record["subject"])));
    row.appendChild(cell("warning_detail", null, safeDetail(record["detail"])));
    row.appendChild(cell("warning_count", "count", countText(record["count"])));
    return row;
  }

  function groupRow(name) {
    var row = document.createElement("tr");
    row.appendChild(cell("unknown_group", "route", safeToken(name)));
    return row;
  }

  function rowsOf(entries, build) {
    var list = listOf(entries);
    var rows = [];
    for (var index = 0; index < list.length; index += 1) {
      rows.push(build(list[index]));
    }
    return rows;
  }

  /* The five counts, as the cheap header the route serves them as. */
  var COUNT_LABELS = [
    ["items", "items"],
    ["recipes", "recipes"],
    ["buildings", "buildings"],
    ["warnings", "warnings"],
    ["unknown_groups", "unknown groups"]
  ];

  function counts(root, record) {
    var grid = element("dl", "facts", null);
    grid.id = "registry-counts";
    for (var index = 0; index < COUNT_LABELS.length; index += 1) {
      var box = document.createElement("div");
      box.appendChild(element("dt", null, COUNT_LABELS[index][1]));
      box.appendChild(element("dd", null, countText(record[COUNT_LABELS[index][0]])));
      grid.appendChild(box);
    }
    root.appendChild(grid);
  }

  registerPanel("registry", function mountRegistry(root, data) {
    var heading = element("h2", null, "Registry");
    heading.id = "h-panel-registry";
    root.setAttribute("aria-labelledby", heading.id);
    root.appendChild(heading);

    var registry = data ? data["registry"] : null;
    if (registry === null || registry === undefined) {
      /*
        No digit is rendered here on purpose. A panel sees data or null and
        never a reason, so "the registry holds nothing" and "nobody got an
        answer" are indistinguishable to it - and a zero on screen would settle
        that question in the reader's head without the panel knowing which way.
      */
      root.appendChild(
        element(
          "p",
          "note",
          "/api/registry did not answer, so nothing from the registry is shown here. " +
            "Press Refresh; if the badge above reads registry: absent, this machine " +
            "has no game install the extraction can read."
        )
      );
      return;
    }

    var record = mapOf(registry);
    root.appendChild(
      element(
        "p",
        "lede",
        "What the extraction found in the shipped game data. These identifiers are the " +
          "vocabulary every other route accepts, so a key listed here is a key the solve " +
          "bench will take."
      )
    );
    counts(root, mapOf(record["counts"]));
    root.appendChild(
      element(
        "p",
        "note",
        "A ratio is the exact value the wire carried. A decimal beside one is an " +
          "approximation for display only, and is labelled " + APPROX.replace(" ", "") +
          " wherever it appears."
      )
    );

    section(
      root,
      "Items",
      "Registry items",
      ["key", "name", "form", "state", "energy (exact)", "energy (approx.)", "sink points"],
      rowsOf(record["items"], itemRow),
      "the registry declared no items."
    );
    section(
      root,
      "Recipes",
      "Registry recipes",
      [
        "key",
        "name",
        "duration (exact)",
        "duration (approx.)",
        "inputs",
        "outputs",
        "produced in"
      ],
      rowsOf(record["recipes"], recipeRow),
      "the registry declared no recipes."
    );
    section(
      root,
      "Buildings",
      "Registry buildings",
      ["key", "name"],
      rowsOf(record["buildings"], buildingRow),
      "the registry declared no buildings."
    );
    section(
      root,
      "Warnings",
      "Registry warnings",
      ["code", "subject", "detail", "seen"],
      rowsOf(record["warnings"], warningRow),
      "nothing was flagged and skipped."
    );
    section(
      root,
      "Unknown groups",
      "Registry unknown groups",
      ["group"],
      rowsOf(record["unknown_groups"], groupRow),
      "every group the extraction met was modelled."
    );
  });
}());
