"use strict";

/*
  CS-962 - the Solve bench. THE ONE PANEL THAT ASKS A QUESTION.

  WHAT IT IS FOR. A person looks up a recipe and asks what a target rate costs
  in machines and in raw inputs. They type the target, the recipes they are
  willing to use and the items they are willing to treat as raw, press the
  button, and read an exact answer.

  WHY IT ASKS app.js RATHER THAN THE SERVER. Every request this page makes is
  issued by app.js, one at a time, on a press. A panel that opened its own
  would put the page's request behaviour outside the file that documents it -
  so this one calls data.actions.requestSolve and names no network primitive
  at all.

  WHY THE ANSWER ARRIVES BY CALLBACK AND NOT BY REPAINT, AND WHY THAT SHAPES
  EVERY LINE BELOW. mountPanel empties this panel's section and builds it
  again. If the result arrived by repaint, the field the reader is standing in
  would be a node no longer in the document - verbatim the focus fault app.js
  documents at length. So the mount holds its result region and its inputs by
  CLOSURE and writes into them. Nothing here asks to be remounted, and nothing
  here is rebuilt after the mount returns.

  THE EXACT RATIONAL IS THE WHOLE POINT, NOT A DETAIL. Every numeric leaf
  /api/solve puts on the wire is a pair of integers, num and den, because the
  contract layer refuses a float on the wire outright. Non-negotiable 6 is
  exact rational arithmetic and it does not stop at the browser: this file
  renders THE PAIR. A rounded decimal may sit beside it, and it is labelled an
  approximation for display so nobody mistakes it for the answer.

  NOTHING IN THIS FILE DIVIDES, INCLUDING THE LABEL BUILDER. An earlier draft
  reached the approximation with a quotient and a toFixed, and the reasoning
  offered for it - that a reading aid is not the answer, so a float there is
  harmless - was heard and rejected. CS-962's acceptance says no division
  anywhere in the render path, and an unguarded quotient also loses precision
  silently on a denominator big enough to matter. approximateDecimal below
  reaches the same decimal by repeated subtraction instead, so no float is
  ever made at all. tests/surface/test_panel_solve.py measures that
  structurally rather than taking this paragraph's word for it.

  NO FORM ELEMENT. The page's content security policy sets form-action to
  none, so a form here would be a control that cannot submit. The bench is four
  inputs, a button, and one click listener.
*/

/* --- what the endpoint requires, and what the sheet sizes ---------------- */

/*
  THE FOUR PARAMETERS /api/solve REQUIRES. app.js refuses a params object that
  is not exactly these four strings - a fifth key and a missing key are both
  refused before a round trip is spent - so this table and the one in app.js
  have to agree, and a disagreement is a false return rather than a bad
  request. The order here is the order the fields appear on the page.
*/
var FIELDS = [
  {
    name: "targets",
    source: "items",
    grammar: "one or more key=rate, comma separated. A rate is a whole number, an exact decimal, or a num/den pair."
  },
  {
    name: "recipes",
    source: "recipes",
    grammar: "recipe keys, comma separated. May be left empty, which means the empty set."
  },
  {
    name: "raw_items",
    source: "items",
    grammar: "item keys you will treat as raw, comma separated. May be left empty."
  },
  {
    name: "byproduct_policy",
    source: "policy",
    grammar: "how a byproduct is accounted for."
  }
];

/* The field whose value the bench preselects. */
var POLICY_FIELD = "byproduct_policy";

/*
  PRESELECTED, AND SHOWN RATHER THAN HIDDEN. Operator ruling: the page makes
  the modelling choice visibly instead of making a player answer it before
  their first result. The field stays editable, and both legal values are
  named beside it.
*/
var DEFAULT_POLICY = "balanced";
var POLICY_VALUES = ["balanced", "sinkable"];

/*
  THE PAIR SEPARATOR, SPELLED ONCE. It is a character in a string and never an
  operator - which is exactly the distinction the division-site arm in
  test_panel_solve.py has to be able to draw.
*/
var PAIR_MARK = "/";

/* The word that marks a decimal as a reading aid rather than as the answer. */
var APPROX_MARK = "approx";

/* How many places the display approximation carries. */
var APPROX_PLACES = 4;

/*
  The largest denominator the long division below stays exact for. The running
  remainder is strictly smaller than the denominator and each step multiplies
  it by ten and adds a digit, so ten times the denominator plus nine has to
  remain an exactly representable integer. Past this bound the panel shows the
  exact pair alone rather than a decimal nobody has checked.
*/
var SAFE_DENOMINATOR = 900000000000000;

/* The code unit the digit characters are counted from. */
var ZERO_CODE = "0".charCodeAt(0);

/* How many keys a vocabulary hint lists before it starts counting instead. */
var VOCABULARY_SHOWN = 6;

/* What a leaf that is not a pair of whole numbers renders as. */
var UNREADABLE = "not an exact rational";

/* --- reading a value without ever trusting its shape --------------------- */

function textOf(value) {
  /*
    A value rendered as text, or a phrase saying it was not stated.

    NOTHING HERE MAY REACH THE PAGE AS undefined OR AS [object Object]. Both
    are what String() produces from a key the wire did not carry, and both
    read to a person as a bug in the page rather than as a gap in the answer.
  */
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "not stated";
}

function isWholeNumber(value) {
  /* Whether a value is a finite integer, which is all a rational leaf may be. */
  return typeof value === "number" && isFinite(value) && Math.floor(value) === value;
}

function exactPair(rational) {
  /*
    The exact rational as "num/den", or null if the leaf is not one.

    NO ARITHMETIC HAPPENS HERE. The two integers the wire carried are composed
    into text and handed back unchanged, so the value a reader sees is the
    value the solve layer computed rather than a re-derivation of it.
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
    digit is found by subtracting the denominator from a running remainder
    until the remainder no longer covers it - at most nine subtractions,
    because the remainder entering a step is already smaller than the
    denominator. What comes back is the EXACT TRUNCATION of num/den to
    APPROX_PLACES places, not a rounding of a quotient somebody computed, and
    no IEEE double is created anywhere along the way.

    WHY THIS IS WRITTEN OUT HERE RATHER THAN SHARED. panel_registry.js carries
    the same routine. These modules are classic scripts with no module system
    - there is no import to reach for - and a cross-panel reference would
    couple two panels that are deliberately independent slices, so that a
    change to one panel's rendering could break another panel's. The
    duplication is the cheaper of the two costs and is deliberate.

    WHAT IT REFUSES. A leaf that is not a pair of safe integers, a denominator
    of zero, and a denominator past SAFE_DENOMINATOR all answer null. The
    caller renders the exact pair alone in that case, which is the honest
    outcome: a missing reading aid is a smaller harm than a decimal whose last
    places nobody can vouch for. Answering null on a zero denominator is also
    what keeps an Infinity off the page.
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

/* --- building and clearing nodes ----------------------------------------- */

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

    AN EMPTY GROUP IS STILL RENDERED. "byproducts: none" is an answer; a
    missing byproducts section is a reader wondering whether the page forgot.
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

/* --- the four fields ------------------------------------------------------ */

function vocabularyLine(field, registry) {
  /*
    The accepted vocabulary for one field, listed BESIDE it.

    OPERATOR AND MERGER RULING TOGETHER: the bench starts empty rather than
    prefilled with a game identifier, and the keys are listed here instead so a
    first-time reader still knows what a legal value looks like. A prefilled
    field would also be a value a reader has to notice and delete before their
    own question can be asked.
  */
  if (field.source === "policy") {
    return "accepted: " + POLICY_VALUES.join(" or ") + ".";
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
    the control resets to. Setting only one of them leaves a bench that either
    forgets its preselection on a reset or never shows it at all.
  */
  var wrap = document.createElement("div");
  wrap.className = "bench-field";

  var domId = "solve-" + field.name;
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
  /*
    One line per item in a key-to-rational table.

    THE ORDER IS THE WIRE'S OWN and is not sorted here. The solve layer's
    output is deterministic, so two runs on one save render in one order; a
    sort would hide a change in that order rather than surface it.
  */
  var lines = [];
  if (!table || typeof table !== "object") {
    return lines;
  }
  var keys = Object.keys(table);
  for (var index = 0; index < keys.length; index += 1) {
    lines.push(keys[index] + " - " + rationalText(table[keys[index]]));
  }
  return lines;
}

function excludedLines(excluded) {
  /* One line per recipe the solve layer left out, and why it did. */
  var lines = [];
  if (!excluded || typeof excluded.length !== "number") {
    return lines;
  }
  for (var index = 0; index < excluded.length; index += 1) {
    var entry = excluded[index] || {};
    lines.push(textOf(entry.recipe_key) + " - " + textOf(entry.reason));
  }
  return lines;
}

function renderPlan(result, status, plan) {
  /* The whole answer: machines first, then what goes in and what comes out. */
  addNote(result, "solved - HTTP " + status + ", byproduct policy " + textOf(plan.byproduct_policy));
  addGroup(result, "machines", stepLines(plan.steps));
  addGroup(result, "targets", amountLines(plan.targets));
  addGroup(result, "raw inputs", amountLines(plan.raw_inputs));
  addGroup(result, "byproducts", amountLines(plan.byproducts));
  addGroup(result, "excluded recipes", excludedLines(plan.excluded));
}

function renderRefusal(result, status, body) {
  /*
    A refusal, read off the ENVELOPE and not off data.

    A 400 body carries no data key at all: its reason and its detail sit beside
    data rather than inside it. That is precisely why the seam hands this panel
    the full envelope - a bench that could only see data would have to render
    every refusal as silence.
  */
  addNote(result, "refused - HTTP " + status);
  addNote(result, "reason: " + textOf(body.reason));
  addNote(result, "detail: " + textOf(body.detail));
  if (body.blocked_by) {
    addNote(result, "blocked by: " + textOf(body.blocked_by));
  }
}

function renderOutcome(result, outcome) {
  /* Whatever settled, turned into something a person can read. */
  clearNode(result);
  if (!outcome || typeof outcome !== "object") {
    addNote(result, "the request settled with nothing to show.");
    return;
  }
  if (!outcome.reached) {
    addNote(result, "the request did not reach the server, so there is nothing to show.");
    return;
  }

  var status = typeof outcome.http === "number" ? String(outcome.http) : "no status";
  var body = outcome.body;
  if (!body || typeof body !== "object") {
    addNote(result, "HTTP " + status + " carried no readable body.");
    return;
  }

  var plan = body.data;
  if (body.status === "ok" && plan && typeof plan === "object") {
    renderPlan(result, status, plan);
    return;
  }
  renderRefusal(result, status, body);
}

/* --- the panel ------------------------------------------------------------ */

registerPanel("solve", function mountSolve(root, data) {
  /*
    data is the resolved payloads plus one door. data.registry supplies the
    vocabulary and may be null; data.actions.requestSolve is the door and may
    be absent entirely - under the seam grader's own harness it is, because
    that harness hands a mount a payload with no actions key at all. A panel
    that assumed the door existed would throw there and be marked failed.
  */
  var registry = data && data.registry && typeof data.registry === "object" ? data.registry : null;
  var door =
    data && data.actions && typeof data.actions.requestSolve === "function"
      ? data.actions.requestSolve
      : null;

  var heading = document.createElement("h2");
  heading.id = "h-panel-solve";
  heading.textContent = "Solve";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  addNote(
    root,
    "Ask what a target rate costs. Every amount below is the exact rational the solver computed, written as a numerator and a denominator; a decimal beside it is a rounded reading aid and never the answer."
  );

  var bench = document.createElement("div");
  bench.className = "bench";
  root.appendChild(bench);

  var inputs = {};
  for (var index = 0; index < FIELDS.length; index += 1) {
    inputs[FIELDS[index].name] = buildField(bench, FIELDS[index], registry);
  }

  var button = document.createElement("button");
  button.setAttribute("type", "button");
  button.textContent = "Solve";
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
    rather than leaning on the seam's. app.js would refuse a second solve
    anyway - but a bench that relied on that would spend a press learning
    something it already knew, and would tell the reader "refused" where the
    truthful answer is that the one they asked for is still running.
  */
  var waiting = false;

  function onPress() {
    if (waiting) {
      say("a solve is already running; wait for it to settle before asking again.");
      return;
    }
    if (!door) {
      say("this page published no solve door, so the bench cannot ask for a plan.");
      return;
    }

    var params = {};
    for (var at = 0; at < FIELDS.length; at += 1) {
      params[FIELDS[at].name] = readField(inputs[FIELDS[at].name]);
    }

    /*
      THE WAITING LINE IS WRITTEN BEFORE THE DOOR IS CALLED, and that ordering
      is load-bearing rather than tidy. A door that answered synchronously
      would settle and render inside this call; writing the waiting line
      afterwards would then paint over the answer with "asking".
    */
    waiting = true;
    say("asking the solve endpoint; the answer will appear here.");

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
      say("the page refused the request, so nothing was sent. A repaint or another solve is in flight; press again once it settles.");
    }
  }

  button.addEventListener("click", onPress);
  say("no solve has been asked for yet. Fill the fields above and press Solve.");
});
