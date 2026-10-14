"use strict";

/*
  The optimize bench - pillar 2, asked from the page for the first time.

  WHY THIS FILE EXISTS. /api/optimize was live and answered 200 against real
  data for as long as nothing on this page ever called it. A route nobody can
  reach is indistinguishable from a route that was never built, and the page's
  own route table said "not probed" beside it - true, and not the same thing as
  "unaskable". This bench is the door being opened.

  NO FETCH ANYWHERE IN THIS FILE. The panel seam hands a mount the payloads
  app.js already fetched plus data.actions.requestOptimize, and that door is the
  only way out of this module. app.js - never this file - builds the query
  string from a fixed table of the names the endpoint takes, so this bench
  cannot widen the request and cannot redirect it.

  THE EXACT RATIONAL IS THE WHOLE POINT, NOT A DETAIL. Every numeric leaf
  /api/optimize puts on the wire is a pair of integers, num and den, because the
  contract layer refuses a float on the wire outright. Non-negotiable 6 does not
  stop at the browser: this file renders THE PAIR. A rounded decimal may sit
  beside it, and it is labelled an approximation for display so nobody mistakes
  it for the answer.

  NOTHING IN THIS FILE DIVIDES, INCLUDING THE LABEL BUILDER. CS-962's acceptance
  says no division anywhere in the render path, and an unguarded quotient also
  loses precision silently on a denominator big enough to matter.
  approximateDecimal below reaches the same decimal by repeated subtraction, so
  no float is ever made at all. The routine is written out here rather than
  shared with panel_solve.js: these are classic scripts with no module system,
  and a cross-panel reference would couple two deliberately independent slices
  so that a change to one panel's rendering could break another's.

  NO FORM ELEMENT. The page's content security policy sets form-action to none,
  so a form here would be a control that cannot submit.

  NO innerHTML. A recipe key is content this project does not model - game or
  mod authored - so every value is written with textContent and renders as
  TEXT whatever characters it holds.
*/

/*
  WRAPPED IN AN IIFE, AS EVERY PANEL MODULE IS, AND FOR A FAULT THIS FILE WOULD
  OTHERWISE CAUSE. These are classic scripts sharing ONE global scope, and
  panel_solve.js uses FIELDS, textOf, addNote, approximateDecimal and a dozen
  more of the names this bench needs - inside its own IIFE since CS-1026, and
  at top level before it. Declared globally in any two panels, the LAST script
  index.html loads would win every one of them - and because a mount closes
  over the BINDING rather than over a snapshot, the solve bench would then
  build the optimize bench's fields on the next repaint. Nothing would throw;
  the page would just be wrong. tests/surface/test_panel_global_scope.py takes
  the census of every panel module's shared-scope names.
*/
(function () {
  /* --- what the endpoint takes ------------------------------------------- */

  /*
  THE SIX NAMES /api/optimize REQUIRES AND THE ONE IT ACCEPTS BESIDES. app.js
  refuses a params object naming anything outside its own table and refuses one
  missing a required name, so this list and the one there have to agree - and a
  disagreement is a false return rather than a bad request. The order here is
  the order the fields appear on the page.
*/
var FIELDS = [
  {
    name: "targets",
    source: "items",
    grammar:
      "one or more key=rate, comma separated. A rate is a whole number, an exact decimal, or a num/den pair."
  },
  {
    name: "candidates",
    source: "recipes",
    grammar: "the recipe keys the optimizer may choose from, comma separated."
  },
  {
    name: "unlocked",
    source: "recipes",
    grammar: "the recipe keys this world has unlocked, comma separated."
  },
  {
    name: "raw_items",
    source: "items",
    grammar: "the item keys available without bound, comma separated."
  },
  {
    name: "byproduct_policy",
    source: "policy",
    grammar: "how an unconsumed byproduct is treated. There is no default at the solver."
  },
  {
    name: "objective",
    source: "objective",
    grammar: "one or more direction=weight, comma separated. A weight is an exact rational."
  }
];

/* The one optional parameter. Left blank, it is NOT SENT AT ALL rather than
   sent empty: the endpoint falls through the precedence select_backend
   publishes, which is that function's decision and not this bench's. */
var OPTIONAL_FIELD = {
  name: "backend",
  source: "backend",
  grammar: "leave blank to let the endpoint choose. A name it does not know is refused there."
};

/* The field whose vocabulary is a closed list rather than a registry read. */
var POLICY_FIELD = "byproduct_policy";
var DEFAULT_POLICY = "balanced";
var POLICY_VALUES = ["balanced", "sinkable"];

/* The objective directions the solve layer publishes. A closed list, spelled
   here because no route serves it and inventing one would be worse. */
var OBJECTIVE_VALUES = ["buildings", "power", "raw"];

/* What separates a numerator from a denominator on the page. */
var PAIR_MARK = "/";

/* How a rounded reading aid is labelled, so it is never read as the answer. */
var APPROX_MARK = "approx";

/* How many places the reading aid carries. */
var APPROX_PLACES = 4;

/* Past this the repeated-subtraction loop stops being cheap, and a decimal
   nobody can vouch for is worse than no decimal at all. */
var SAFE_DENOMINATOR = 900000000000000;

/* The character code of "0", so a digit is read without parsing. */
var ZERO_CODE = "0".charCodeAt(0);

/* How many vocabulary keys are listed beside a field. */
var VOCABULARY_SHOWN = 6;

/* What a leaf that is not an exact rational renders as. */
var UNREADABLE = "not an exact rational";

/* --- reading the wire's numbers, without dividing ------------------------- */

function textOf(value) {
  /* Any leaf as display text, with a dash standing in for an absent one. */
  if (value === null || value === undefined) {
    return "-";
  }
  return String(value);
}

function isWholeNumber(value) {
  /* Whether a value is a finite integer, which is all a rational leaf may be. */
  return typeof value === "number" && isFinite(value) && Math.floor(value) === value;
}

function exactPair(rational) {
  /*
    The exact rational as "num/den", or null if the leaf is not one.

    NO ARITHMETIC HAPPENS HERE. The two integers the wire carried are composed
    into text and handed back unchanged, so the value a reader sees is the value
    the solve layer computed rather than a re-derivation of it.
  */
  if (!rational || typeof rational !== "object") {
    return null;
  }
  if (!isWholeNumber(rational.num) || !isWholeNumber(rational.den)) {
    return null;
  }
  return String(rational.num) + PAIR_MARK + String(rational.den);
}

function absoluteValue(value) {
  /* Magnitude, without asking a library and without an operator that divides. */
  return value < 0 ? -value : value;
}

function approximateDecimal(num, den) {
  /*
    THE DISPLAY DECIMAL, PRODUCED WITHOUT DIVIDING ANYTHING.

    The numerator's own decimal digits are consumed left to right. Each output
    digit is found by subtracting the denominator from a running remainder until
    the remainder no longer covers it - at most nine subtractions, because the
    remainder entering a step is already smaller than the denominator. What
    comes back is the EXACT TRUNCATION of num/den to APPROX_PLACES places, not a
    rounding of a quotient somebody computed, and no IEEE double is created
    anywhere along the way.
  */
  if (!isWholeNumber(num) || !isWholeNumber(den)) {
    return null;
  }
  if (!Number.isSafeInteger(num) || !Number.isSafeInteger(den)) {
    return null;
  }
  var divisor = absoluteValue(den);
  if (divisor === 0 || divisor > SAFE_DENOMINATOR) {
    return null;
  }

  var negative = num < 0 !== den < 0;
  var digits = String(absoluteValue(num));
  var whole = "";
  var remainder = 0;
  var index;
  var digit;

  for (index = 0; index < digits.length; index += 1) {
    remainder = remainder * 10 + (digits.charCodeAt(index) - ZERO_CODE);
    digit = 0;
    while (remainder >= divisor) {
      remainder -= divisor;
      digit += 1;
    }
    whole += String(digit);
  }
  while (whole.length > 1 && whole.charAt(0) === "0") {
    whole = whole.substring(1);
  }

  var fraction = "";
  for (index = 0; index < APPROX_PLACES; index += 1) {
    remainder = remainder * 10;
    digit = 0;
    while (remainder >= divisor) {
      remainder -= divisor;
      digit += 1;
    }
    fraction += String(digit);
  }

  return (negative ? "-" : "") + whole + "." + fraction;
}

function rationalText(rational) {
  /*
    The exact pair, with a labelled approximation beside it where one exists.

    THE PAIR IS NEVER OMITTED. A decimal standing alone would be a rounded
    number presented as an exact one, which is the single rendering this panel
    is forbidden to produce.
  */
  var pair = exactPair(rational);
  if (pair === null) {
    return UNREADABLE;
  }
  var approximate = approximateDecimal(rational.num, rational.den);
  if (approximate === null) {
    return pair;
  }
  return pair + " (" + APPROX_MARK + " " + approximate + ", display only)";
}

/* --- building and clearing nodes ------------------------------------------ */

function clearNode(node) {
  /* Empty a node the way app.js empties a section: child by child. */
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function addNote(parent, message) {
  /* One line of prose, appended as text and never as markup. */
  var line = document.createElement("p");
  line.className = "note";
  line.textContent = message;
  parent.appendChild(line);
  return line;
}

function addGroup(parent, label, lines) {
  /*
    A labelled group of result lines, or the label alone saying it is empty.

    AN EMPTY GROUP IS STILL RENDERED. "excluded: none" is an answer; a missing
    section is a reader wondering whether the page forgot.
  */
  if (!lines.length) {
    addNote(parent, label + ": none");
    return;
  }
  addNote(parent, label + ":");
  var list = document.createElement("ul");
  for (var index = 0; index < lines.length; index += 1) {
    var item = document.createElement("li");
    item.textContent = lines[index];
    list.appendChild(item);
  }
  parent.appendChild(list);
}

/* --- the fields ----------------------------------------------------------- */

function vocabularyLine(field, registry) {
  /*
    The accepted vocabulary for one field, listed BESIDE it.

    The bench starts empty rather than prefilled with a game identifier, and the
    keys are listed here instead, so a first-time reader still knows what a
    legal value looks like without having to notice and delete one.
  */
  if (field.source === "policy") {
    return "accepted: " + POLICY_VALUES.join(" or ") + ".";
  }
  if (field.source === "objective") {
    return "accepted directions: " + OBJECTIVE_VALUES.join(", ") + ".";
  }
  if (field.source === "backend") {
    return "the endpoint owns the list; a name it does not know is refused there.";
  }
  var rows = registry ? registry[field.source] : null;
  if (!rows || typeof rows.length !== "number" || rows.length === 0) {
    return "the registry did not answer, so no key list can be shown here.";
  }
  var shown = [];
  for (var index = 0; index < rows.length && index < VOCABULARY_SHOWN; index += 1) {
    shown.push(textOf(rows[index] ? rows[index].key : null));
  }
  var line = "accepted keys include " + shown.join(", ");
  if (rows.length > VOCABULARY_SHOWN) {
    line = line + " and " + String(rows.length - VOCABULARY_SHOWN) + " more";
  }
  return line + ".";
}

function buildField(bench, field, registry) {
  /*
    One labelled input, its hint, and the value it starts at.

    THE VALUE IS SET AS A PROPERTY AND AS AN ATTRIBUTE. The property is what a
    user agent reads back after the reader types; the attribute is the default
    the control resets to.
  */
  var wrap = document.createElement("div");
  wrap.className = "bench-field";

  var domId = "optimize-" + field.name;
  var label = document.createElement("label");
  label.className = "bench-label";
  label.setAttribute("for", domId);
  label.textContent = field.name;
  wrap.appendChild(label);

  var input = document.createElement("input");
  input.id = domId;
  input.className = "bench-input";
  input.setAttribute("type", "text");
  input.setAttribute("name", field.name);
  input.setAttribute("autocomplete", "off");
  input.setAttribute("spellcheck", "false");
  input.value = field.name === POLICY_FIELD ? DEFAULT_POLICY : "";
  input.setAttribute("value", input.value);
  wrap.appendChild(input);

  addNote(wrap, field.grammar + " " + vocabularyLine(field, registry));
  bench.appendChild(wrap);
  return input;
}

function readField(input) {
  /*
    What the reader typed, as a string and only ever as a string.

    app.js refuses a params object carrying a non-string, so a control that
    answered something else would cost a press and produce no result at all.
  */
  return typeof input.value === "string" ? input.value : "";
}

/* --- rendering one settled outcome ---------------------------------------- */

function stepLines(steps) {
  /* One line per production step: which recipe, and how many machines. */
  var lines = [];
  if (!steps || typeof steps.length !== "number") {
    return lines;
  }
  for (var index = 0; index < steps.length; index += 1) {
    var step = steps[index] || {};
    lines.push(textOf(step.recipe_key) + " - " + rationalText(step.machines) + " machines");
  }
  return lines;
}

function amountLines(table) {
  /* One line per key in a rate map, each carrying the exact pair. */
  var lines = [];
  if (!table || typeof table !== "object") {
    return lines;
  }
  var keys = Object.keys(table);
  keys.sort();
  for (var index = 0; index < keys.length; index += 1) {
    lines.push(keys[index] + " - " + rationalText(table[keys[index]]) + " per minute");
  }
  return lines;
}

function nameLines(names) {
  /* One line per chosen recipe key, in the order the optimizer returned. */
  var lines = [];
  if (!names || typeof names.length !== "number") {
    return lines;
  }
  for (var index = 0; index < names.length; index += 1) {
    lines.push(textOf(names[index]));
  }
  return lines;
}

function excludedLines(excluded) {
  /* One line per exclusion note: which recipe, and the solver's own reason. */
  var lines = [];
  if (!excluded || typeof excluded.length !== "number") {
    return lines;
  }
  for (var index = 0; index < excluded.length; index += 1) {
    var note = excluded[index] || {};
    lines.push(textOf(note.recipe_key) + " - " + textOf(note.reason));
  }
  return lines;
}

function servedCodes(warnings) {
  /* Every warning code the body served, verbatim and in the body's order. */
  var codes = [];
  if (!warnings || typeof warnings.length !== "number") {
    return codes;
  }
  for (var index = 0; index < warnings.length; index += 1) {
    var row = warnings[index];
    if (row && typeof row === "object" && row.code) {
      codes.push(textOf(row.code));
    }
  }
  return codes;
}

function registryLine(data) {
  /*
    WHICH REGISTRY PRICED THE SCORE AND THE PLAN BELOW - CS-1315. The endpoint
    copies the audit layer's registry check into build_state and serves its
    code under the "build" source; this bench compares NOTHING. It reads one
    flag and prints what it says, AHEAD of the first figure, because "nothing
    prices a figure from an unverified registry silently":

    - registry_verified true: the registry was built from the docs this
      project pins, and the line says so.
    - registry_verified anything else: UNVERIFIED, with every served code.
    - no build_state at all: said in as many words, and never read as the
      verified case, which would be a confident claim nothing checked.

    Read off the TOP of data and never off the nested plan, which carries none.
  */
  var state = data.build_state && typeof data.build_state === "object"
    ? data.build_state
    : null;
  var codes = servedCodes(data.warnings);
  var served = codes.length ? " Served: " + codes.join(", ") + "." : "";
  if (state === null) {
    return "registry: this answer carried no build state, so nothing here says whether the"
      + " registry that priced it was verified." + served;
  }
  if (state.registry_verified === true) {
    return "registry: verified - built from the docs this project pins." + served;
  }
  return "registry: UNVERIFIED - every figure below is priced from a registry not shown to"
    + " be built from the docs this project pins." + served;
}

function renderResult(result, status, data) {
  /*
    A settled 200, rendered whole.

    THE SELECTION COMES FIRST because it is the answer pillar 2 exists to give -
    which recipes - and the plan beneath it is the consequence of that choice.
    Only the registry line precedes it, because every figure here is priced
    from that registry.
  */
  clearNode(result);
  addNote(result, "the endpoint answered " + String(status) + ".");
  addNote(result, registryLine(data));
  addNote(result, "backend: " + textOf(data.backend));
  addNote(result, "score: " + rationalText(data.score));
  addGroup(result, "selection", nameLines(data.selection));
  addGroup(result, "excluded", excludedLines(data.excluded));

  var plan = data.plan && typeof data.plan === "object" ? data.plan : {};
  addNote(result, "byproduct policy: " + textOf(plan.byproduct_policy));
  addGroup(result, "steps", stepLines(plan.steps));
  addGroup(result, "targets", amountLines(plan.targets));
  addGroup(result, "raw inputs", amountLines(plan.raw_inputs));
  addGroup(result, "byproducts", amountLines(plan.byproducts));
}

function renderRefusal(result, status, body) {
  /*
    A settled non-200.

    THE REASON AND THE DETAIL SIT OUTSIDE data, which is why app.js hands this
    panel the whole envelope. A bench that read only data would render every
    refusal as silence.
  */
  clearNode(result);
  addNote(result, "the endpoint refused with " + String(status) + ".");
  if (body && typeof body === "object") {
    addNote(result, "reason: " + textOf(body.reason));
    addNote(result, "detail: " + textOf(body.detail));
    if (body.blocked_by) {
      addNote(result, "blocked by: " + textOf(body.blocked_by));
    }
  }
}

function renderOutcome(result, outcome) {
  /* Whatever settled, rendered into the region the bench already holds. */
  if (!outcome || typeof outcome !== "object") {
    clearNode(result);
    addNote(result, "the page returned no outcome at all, so there is nothing to render.");
    return;
  }
  if (!outcome.reached) {
    clearNode(result);
    addNote(result, "the endpoint could not be reached, so no answer arrived.");
    return;
  }
  var body = outcome.body;
  var data = body && typeof body === "object" ? body.data : null;
  if (data && typeof data === "object") {
    renderResult(result, outcome.http, data);
    return;
  }
  renderRefusal(result, outcome.http, body);
}

registerPanel("optimize", function mountOptimize(root, data) {
  /*
    data is the resolved payloads plus the doors. data.registry supplies the
    vocabulary and may be null; data.actions.requestOptimize is the door and may
    be absent entirely - under the seam grader's own harness it is, because that
    harness hands a mount a payload with no actions key at all. A panel that
    assumed the door existed would throw there and be marked failed.
  */
  var registry = data && data.registry && typeof data.registry === "object" ? data.registry : null;
  var door =
    data && data.actions && typeof data.actions.requestOptimize === "function"
      ? data.actions.requestOptimize
      : null;

  var heading = document.createElement("h2");
  heading.id = "h-panel-optimize";
  heading.textContent = "Optimize";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  addNote(
    root,
    "Ask which recipes to choose, not just what a chosen set costs. Every amount below is the exact rational the solver computed, written as a numerator and a denominator; a decimal beside it is a rounded reading aid and never the answer."
  );

  var bench = document.createElement("div");
  bench.className = "bench";
  root.appendChild(bench);

  var inputs = {};
  var index;
  for (index = 0; index < FIELDS.length; index += 1) {
    inputs[FIELDS[index].name] = buildField(bench, FIELDS[index], registry);
  }
  inputs[OPTIONAL_FIELD.name] = buildField(bench, OPTIONAL_FIELD, registry);

  var button = document.createElement("button");
  button.setAttribute("type", "button");
  button.textContent = "Optimize";
  bench.appendChild(button);

  var result = document.createElement("div");
  result.className = "bench-result";
  result.setAttribute("aria-live", "polite");
  bench.appendChild(result);

  function say(message) {
    /* Replace whatever the region held with one line. */
    clearNode(result);
    addNote(result, message);
  }

  /*
    Whether this bench is waiting on an answer. THE PANEL HOLDS ITS OWN FLAG
    rather than leaning on the seam's. app.js would refuse a second request
    anyway - but a bench that relied on that would spend a press learning
    something it already knew, and would tell the reader "refused" where the
    truthful answer is that the one they asked for is still running.
  */
  var waiting = false;

  function onPress() {
    if (waiting) {
      say("a request is already running; wait for it to settle before asking again.");
      return;
    }
    if (!door) {
      say("this page published no optimize door, so the bench cannot ask for a result.");
      return;
    }

    var params = {};
    for (var at = 0; at < FIELDS.length; at += 1) {
      params[FIELDS[at].name] = readField(inputs[FIELDS[at].name]);
    }

    /*
      AN EMPTY OPTIONAL FIELD IS OMITTED, NOT SENT EMPTY. An empty backend name
      is not a backend the endpoint knows, so sending one would turn "let the
      endpoint choose" into a refusal. Omitting the key is how a caller says
      nothing, and app.js's table is what stops this bench inventing a name.
    */
    var backend = readField(inputs[OPTIONAL_FIELD.name]);
    if (backend !== "") {
      params[OPTIONAL_FIELD.name] = backend;
    }

    /*
      THE WAITING LINE IS WRITTEN BEFORE THE DOOR IS CALLED, and that ordering
      is load-bearing rather than tidy. A door that answered synchronously would
      settle and render inside this call; writing the waiting line afterwards
      would then paint over the answer with "asking".
    */
    waiting = true;
    say("asking the optimize endpoint; the answer will appear here.");

    var accepted = false;
    try {
      accepted = door(params, function (outcome) {
        waiting = false;
        renderOutcome(result, outcome);
      });
    } catch (doorFailure) {
      /*
        SWALLOWED, AND DELIBERATELY EMPTY. An exception's message and stack on
        this machine carry an absolute path under a home directory, so putting
        one on the page would publish the operator's account name to whoever is
        looking at the screen - non-negotiable 3. A throw is treated as a
        refusal, which is what it is from this bench's side.
      */
      accepted = false;
    }

    if (!accepted) {
      /*
        A FALSE RETURN MEANS THE CALLBACK NEVER FIRES. Nothing else will ever
        arrive, so if the panel stayed silent here the press would look like a
        dead button. The flag comes back down in the same breath, or the bench
        would refuse every later press on the strength of a request that was
        never made.
      */
      waiting = false;
      say("the page refused the request, so nothing was sent. A repaint or another request is in flight; press again once it settles.");
    }
  }

  button.addEventListener("click", onPress);
  say("no optimize has been asked for yet. Fill the fields above and press Optimize.");
});
}());
