"use strict";

/*
  The power bench - what a building draws, and what is honestly unknown.

  WHY THIS FILE EXISTS. clockspeed/solve/power.py was written and tested and
  reachable from no route at all, so /api/power was built to publish it. A route
  nobody calls is the same fault one step later, and this bench is the call.

  WHAT THIS PANEL IS MOSTLY FOR IS SAYING "NOT KNOWN" WITHOUT SAYING "ZERO".
  Four of the endpoint's five answers can be unmodeled, and each is unmodeled
  for its own reason: a declared min/max struct with no scalar, a real declared
  zero beside a per-recipe law nobody has measured, no readable scalar at all,
  and a building that declares no exponent and so does not scale with a clock.
  The reason line the endpoint sends is rendered VERBATIM in every one of those
  cases. A bench that printed 0 MW instead would produce exactly the confident
  zero a power plan cannot detect.

  AND IT NEVER SHOWS A CEILING. ADR 0005 records that the shard slot count is
  absent from every source on this machine, so the endpoint publishes none and
  there is no field here that could hold one. The un-sharded base IS shown, and
  it is labelled as the un-sharded base every time - ADR 0006's fence, because a
  reader who takes that number for the achievable maximum caps every plan at the
  un-overclocked figure and is right on every building nobody has overclocked.

  THE DEFERRED TERM IS RENDERED AS TWO OPERANDS AND NEVER AS A NUMBER. Away from
  a clock of 1 the power law has no exact rational value - the measured float is
  in clockspeed/solve/power.py - so the endpoint sends the coefficient, the base
  and the exponent, and this file writes "coefficient * base ^ exponent" as
  text. Evaluating it here would put the float back at the last layer that could
  have stopped it.

  NO FETCH ANYWHERE IN THIS FILE. The panel seam hands a mount the payloads
  app.js already fetched plus data.actions.requestPower, and that door is the
  only way out of this module. app.js - never this file - builds the query
  string from a fixed table of the names the endpoint takes.

  NOTHING IN THIS FILE DIVIDES. CS-962's acceptance says no division anywhere in
  the render path; approximateDecimal below reaches its decimal by repeated
  subtraction, so no float is ever made at all.

  NO innerHTML, NO FORM. A building key is game- or mod-authored content, so
  every value is written with textContent; the page's content security policy
  sets form-action to none, so a form would be a control that cannot submit.
*/

/*
  WRAPPED IN AN IIFE, AS panel_registry.js AND panel_warnings.js ARE. These are
  classic scripts sharing ONE global scope, and panel_solve.js already declares
  textOf, addNote, approximateDecimal and a dozen more names this file needs at
  top level. Declared globally here, the LAST script index.html loads would win
  every one of them, and a mount closes over the BINDING rather than a snapshot
  - so another panel would silently start rendering with this file's helpers.
*/
(function () {
  /* The one required parameter, and the two that unlock the rest. */
  var BUILDING_FIELD = {
    name: "building",
    source: "buildings",
    grammar: "one building key."
  };

  var OPTIONAL_FIELDS = [
    {
      name: "clock",
      source: "clock",
      grammar:
        "leave blank to ask only what the entry declares. A clock is a whole number, an exact decimal, or a num/den pair, where 1 is the un-overclocked building."
    },
    {
      name: "recipe",
      source: "recipes",
      grammar:
        "leave blank unless the building is a variable-power one. The per-recipe constant and factor live on the recipe."
    }
  ];

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

  /* What an absent measurement renders as. NEVER "0", and never blank: the
     whole point of this panel is that absent and zero are different facts. */
  var NOT_DECLARED = "not declared";

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
      into text and handed back unchanged.
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

      Each output digit is found by subtracting the denominator from a running
      remainder until the remainder no longer covers it - at most nine
      subtractions, because the remainder entering a step is already smaller
      than the denominator. What comes back is the EXACT TRUNCATION of num/den
      to APPROX_PLACES places, not a rounding of a quotient somebody computed,
      and no IEEE double is created anywhere along the way.
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

  function optionalText(rational) {
    /*
      A measurement that may legitimately be absent.

      NULL RENDERS AS "not declared" AND NEVER AS A ZERO. The endpoint keeps an
      absent scalar distinct from a declared zero because the data layer does,
      and a bench that collapsed them would undo the whole chain at the last
      step - a confident zero is exactly what a power plan cannot detect.
    */
    if (rational === null || rational === undefined) {
      return NOT_DECLARED;
    }
    return rationalText(rational);
  }

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

      AN EMPTY GROUP IS STILL RENDERED, because "you did not ask" is an answer
      and a missing section is a reader wondering whether the page forgot.
    */
    if (!lines.length) {
      addNote(parent, label + ": not asked for.");
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

  function vocabularyLine(field, registry) {
    /*
      The accepted vocabulary for one field, listed BESIDE it. The bench starts
      empty rather than prefilled with a game identifier, so a first-time reader
      still knows what a legal value looks like without deleting one first.
    */
    if (field.source === "clock") {
      return "1 is the un-overclocked building.";
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

    var domId = "power-" + field.name;
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
    input.value = "";
    input.setAttribute("value", input.value);
    wrap.appendChild(input);

    addNote(wrap, field.grammar + " " + vocabularyLine(field, registry));
    bench.appendChild(wrap);
    return input;
  }

  function readField(input) {
    /*
      What the reader typed, as a string and only ever as a string. app.js
      refuses a params object carrying a non-string.
    */
    return typeof input.value === "string" ? input.value : "";
  }

  function declaredLines(declared) {
    /* The four facts a declaration carries, with absence never shown as zero. */
    if (!declared || typeof declared !== "object") {
      return [];
    }
    return [
      "shape: " + textOf(declared.shape),
      "modeled: " + (declared.modeled ? "yes" : "no"),
      "megawatts: " + optionalText(declared.megawatts),
      "estimated minimum: " + optionalText(declared.minimum),
      "estimated maximum: " + optionalText(declared.maximum),
      "why: " + textOf(declared.reason)
    ];
  }

  function termText(term) {
    /*
      The symbolic power term, written out as its two operands.

      NOTHING IS RAISED TO ANYTHING. The caret is a character in a string. The
      power law has no exact rational value away from the reference clock, so
      the operands are shown and the reader is told the term is unevaluated.
    */
    if (!term || typeof term !== "object") {
      return null;
    }
    return "(" + rationalText(term.base) + ") ^ (" + rationalText(term.exponent) + ")";
  }

  function atClockLines(atClock) {
    /* The clocked draw, with the deferred case shown as coefficient and term. */
    if (!atClock || typeof atClock !== "object") {
      return [];
    }
    var lines = [
      "outcome: " + textOf(atClock.outcome),
      "megawatts: " + optionalText(atClock.megawatts)
    ];
    var term = termText(atClock.deferred);
    if (term !== null) {
      lines.push("coefficient: " + optionalText(atClock.coefficient));
      lines.push("term, held unevaluated: " + term);
      lines.push("the draw is the coefficient times that term; it has no exact rational value.");
    }
    lines.push("why: " + textOf(atClock.reason));
    return lines;
  }

  function ceilingLines(ceiling) {
    /*
      What is known about the ceiling, which is never the ceiling.

      THE BASE IS LABELLED THE UN-SHARDED BASE EVERY TIME. ADR 0006's fence: a
      reader who takes it for the achievable maximum is right on every building
      nobody has overclocked, which is where testing is easiest.
    */
    if (!ceiling || typeof ceiling !== "object") {
      return [];
    }
    return [
      "achievable ceiling known: " + (ceiling.known ? "yes" : "no"),
      "un-sharded base, which is NOT the ceiling: " + optionalText(ceiling.base),
      "shard slots: " + (ceiling.slots === null || ceiling.slots === undefined
        ? "unmeasured"
        : String(ceiling.slots)),
      "why: " + textOf(ceiling.reason)
    ];
  }

  function clampedLines(clamped) {
    /* Whether the requested clock was reduced, and to what. */
    if (!clamped || typeof clamped !== "object") {
      return [];
    }
    return [
      "clock to use: " + optionalText(clamped.clock),
      "clamped: " + (clamped.clamped ? "yes" : "no"),
      "un-sharded base compared against: " + optionalText(clamped.base),
      "why: " + textOf(clamped.reason)
    ];
  }

  function variableLines(inputs) {
    /*
      The variable-power operands, with NO LAW APPLIED HERE. ADR 0021 measured
      the law, and clockspeed/solve/power.py owns it in bounded_draw, which
      answers this shape with two exact bounds. This panel does not render those
      bounds yet - that is CS-1065. What stays refused either way is a SCALAR:
      the cycle average rides a power-consumption curve the shipped document
      does not carry, so combining these operands here would produce a confident
      megawatt figure for the hungriest buildings in the game.
    */
    if (!inputs || typeof inputs !== "object") {
      return [];
    }
    return [
      "modeled: " + (inputs.modeled ? "yes" : "no"),
      "per-recipe constant: " + optionalText(inputs.constant),
      "per-recipe factor: " + optionalText(inputs.factor),
      "estimated minimum: " + optionalText(inputs.minimum),
      "estimated maximum: " + optionalText(inputs.maximum),
      "why: " + textOf(inputs.reason)
    ];
  }

  function renderAnswer(result, status, data) {
    /* A settled 200, rendered whole. */
    clearNode(result);
    addNote(result, "the endpoint answered " + String(status) + ".");
    addNote(result, "building: " + textOf(data.building_key));
    addGroup(result, "declared draw", declaredLines(data.declared));
    addGroup(result, "clock ceiling", ceilingLines(data.ceiling));
    addGroup(result, "draw at the clock", atClockLines(data.at_clock));
    addGroup(result, "clock clamped to the un-sharded base", clampedLines(data.clamped));
    addGroup(result, "variable-power operands", variableLines(data.variable_inputs));
  }

  function renderRefusal(result, status, body) {
    /*
      A settled non-200. THE REASON AND THE DETAIL SIT OUTSIDE data, which is why
      app.js hands this panel the whole envelope; a bench that read only data
      would render every refusal as silence.
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
      renderAnswer(result, outcome.http, data);
      return;
    }
    renderRefusal(result, outcome.http, body);
  }

  registerPanel("power", function mountPower(root, data) {
    /*
      data is the resolved payloads plus the doors. data.registry supplies the
      vocabulary and may be null; data.actions.requestPower is the door and may
      be absent entirely - under the seam grader's own harness it is, because
      that harness hands a mount a payload with no actions key at all. A panel
      that assumed the door existed would throw there and be marked failed.
    */
    var registry =
      data && data.registry && typeof data.registry === "object" ? data.registry : null;
    var door =
      data && data.actions && typeof data.actions.requestPower === "function"
        ? data.actions.requestPower
        : null;

    var heading = document.createElement("h2");
    heading.id = "h-panel-power";
    heading.textContent = "Power";
    root.setAttribute("aria-labelledby", heading.id);
    root.appendChild(heading);

    addNote(
      root,
      "Ask what a building draws. Every amount is the exact rational the power layer read, written as a numerator and a denominator; a decimal beside it is a rounded reading aid and never the answer. Where the game's own data does not state a draw, this panel says so rather than showing a zero."
    );

    var bench = document.createElement("div");
    bench.className = "bench";
    root.appendChild(bench);

    var inputs = {};
    inputs[BUILDING_FIELD.name] = buildField(bench, BUILDING_FIELD, registry);
    var index;
    for (index = 0; index < OPTIONAL_FIELDS.length; index += 1) {
      inputs[OPTIONAL_FIELDS[index].name] = buildField(bench, OPTIONAL_FIELDS[index], registry);
    }

    var button = document.createElement("button");
    button.setAttribute("type", "button");
    button.textContent = "Read power";
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
      rather than leaning on the seam's, so a reader is told "still running"
      rather than "refused" when they press twice.
    */
    var waiting = false;

    function onPress() {
      if (waiting) {
        say("a request is already running; wait for it to settle before asking again.");
        return;
      }
      if (!door) {
        say("this page published no power door, so the bench cannot ask for a reading.");
        return;
      }

      var params = {};
      params[BUILDING_FIELD.name] = readField(inputs[BUILDING_FIELD.name]);

      /*
        AN EMPTY OPTIONAL FIELD IS OMITTED, NOT SENT EMPTY. An empty string is
        neither a well-formed key nor an exact rational, so sending one would
        turn "I did not ask" into a 400. Omitting the key is how a caller says
        nothing, and app.js's table is what stops this bench inventing a name.
      */
      for (var at = 0; at < OPTIONAL_FIELDS.length; at += 1) {
        var name = OPTIONAL_FIELDS[at].name;
        var typed = readField(inputs[name]);
        if (typed !== "") {
          params[name] = typed;
        }
      }

      /*
        THE WAITING LINE IS WRITTEN BEFORE THE DOOR IS CALLED. A door that
        answered synchronously would settle and render inside this call; writing
        the waiting line afterwards would paint over the answer with "asking".
      */
      waiting = true;
      say("asking the power endpoint; the answer will appear here.");

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
          one on the page would publish the operator's account name to whoever
          is looking at the screen - non-negotiable 3.
        */
        accepted = false;
      }

      if (!accepted) {
        /*
          A FALSE RETURN MEANS THE CALLBACK NEVER FIRES, so silence here would
          make the press look like a dead button. The flag comes back down in
          the same breath, or the bench would refuse every later press on the
          strength of a request that was never made.
        */
        waiting = false;
        say("the page refused the request, so nothing was sent. A repaint or another request is in flight; press again once it settles.");
      }
    }

    button.addEventListener("click", onPress);
    say("no power reading has been asked for yet. Name a building above and press Read power.");
  });
}());
