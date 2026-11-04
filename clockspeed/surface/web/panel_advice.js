"use strict";

/*
  CS-1371 - the Advice panel. The cards this world's advice holds, and the plan a
  stated target asks for.

  THE SELECTOR IS FREE, AND THAT IS WHY NOTHING STARTS FILLED IN. CLAUDE.md section
  7 settles the milestone target as a free selector and rejects a fixed pointer at
  the next milestone, so every control here starts empty and the panel has no
  opinion about what to ask. The one thing this file refuses is an empty field,
  and it refuses that by leaving the press inert and naming the field. Everything
  else about a statement is the server's to refuse.

  NOTHING IS COMPUTED HERE. plan_targets arrives on the registry body in the order
  it was served and is listed in that order. A card's headline and reason are tier
  1 and tier 2 as the listing carries them, and tier 3 is shown as the text the
  derivation route answered, never parsed. The rate is what the reader typed, in
  the spelling the API takes - an integer, an exact decimal or num/den, per minute
  - and it stays text the whole way, because a value parsed here would be a binary
  float in the answer path, which non-negotiable 6 bans outright.

  THE TWO CLOSED VOCABULARIES ARE SPELLED BELOW BECAUSE NO ROUTE SERVES THEM, and
  tests/surface/test_panel_advice.py binds each one to the Python constant it
  copies, which nothing does for panel_optimize.js's two lists.

  NO FETCH IN THIS FILE. data.actions.requestAdvice and
  data.actions.requestDerivation are the only ways out, and app.js builds both
  queries from its own tables, so this panel chooses the values and never the
  names, the path or the verb.

  A CARD REMEMBERS THE STATEMENT THAT PRODUCED IT. The bench stays editable after an
  answer lands, and a card id only means something under the statement it was
  listed for, so a derivation button closes over those four and never reads the
  fields again. A card a repaint listed was produced by no statement and asks with
  none, which is the question the route answered before this item.

  NO FORM ELEMENT. The page's content security policy sets form-action to none, so
  a form here would be a control that cannot submit.

  NO innerHTML. A headline, a reason and a derivation are built from game or mod
  authored names, so every value reaches the page through textContent and renders
  as TEXT whatever characters it holds.

  A REFUSAL IS NAMED, NEVER ECHOED. The reason on a refusal envelope is a word from
  a closed vocabulary and the detail is a fixed line looked up from that word, so
  neither can carry what was typed. This file prints those two and the transport
  code, and never the refused value.

  WRAPPED IN AN IIFE, AS EVERY PANEL MODULE IS. These are classic scripts sharing
  one global scope; tests/surface/test_panel_global_scope.py takes the census.
*/
(function () {
/* --- the two closed vocabularies ---------------------------------------- */

/* clockspeed/solve/optimize.py, OBJECTIVES. */
var DIRECTION_VALUES = ["buildings", "power", "raw"];

/* clockspeed/solve/ratio.py, BYPRODUCT_POLICIES. */
var POLICY_VALUES = ["balanced", "sinkable"];

/* --- the lines this panel can write ------------------------------------- */

/*
  EVERY STATUS LINE FITS THE RESERVED SLOT: two lines at the narrowest width the
  page is audited at, which .bench-status in app.css holds open. That is why they
  are this short, and a line that grew would move what it sits above.
*/
var IDLE_LINE = "no request yet. The cards below are this world's own.";
var ASKING_LINE = "asking; what is below stays until the answer lands.";
/* In the past tense because nothing rewrites it when that other request settles. */
var BUSY_LINE = "that press found a request running; nothing was sent.";
var NOT_SENT_LINE = "nothing was sent: a repaint or a request was running.";
var NO_ADVICE_DOOR_LINE = "this page published no advice door; nothing was sent.";
var NO_READ_DOOR_LINE = "this page published no derivation door; nothing was sent.";
var UNREACHABLE_LINE = "no answer: unreachable.";
var NO_OUTCOME_LINE = "the page returned no outcome at all, so nothing landed.";

var READING_LINE = "reading the derivation ...";
var UNREAD_LINE = "derivation not read.";
var READ_LINE = "derivation read.";

var NO_CARD_STATED = "no visible card answered this request.";
var NO_CARD_HELD = "this world's advice holds no visible card.";
var NO_OUTCOME_KEY = "this answer carried no plan outcome, so nothing here says what the search did.";

/* --- building and clearing nodes ---------------------------------------- */

function clearNode(node) {
  /* Empty a node the way app.js empties a section: child by child. */
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function textOf(value) {
  /* Any leaf as display text, with a dash standing in for an absent one. */
  if (value === null || value === undefined) {
    return "-";
  }
  return String(value);
}

function addLine(parent, tag, className, message) {
  /* One element holding one piece of text, as text and never as markup. */
  var line = document.createElement(tag);
  line.className = className;
  line.textContent = message;
  parent.appendChild(line);
  return line;
}

function addNote(parent, message) {
  return addLine(parent, "p", "note", message);
}

function addGroup(parent, label, lines) {
  /* A labelled list of keys, in the order the body served them. */
  addNote(parent, label + ":");
  var list = document.createElement("ul");
  list.className = "paths";
  for (var index = 0; index < lines.length; index += 1) {
    addLine(list, "li", "", lines[index]);
  }
  parent.appendChild(list);
}

function isPresent(value) {
  /* The wire omits a field that has nothing to say; null reads the same way. */
  return value !== null && value !== undefined;
}

function objectOrNull(value) {
  return value && typeof value === "object" ? value : null;
}

/* --- the bench's controls ----------------------------------------------- */

function addField(bench, name, labelText) {
  /* One labelled slot, and the id its control takes. */
  var wrap = document.createElement("div");
  wrap.className = "bench-field";
  var domId = "advice-" + name;
  var label = addLine(wrap, "label", "bench-label", labelText);
  label.setAttribute("for", domId);
  bench.appendChild(wrap);
  return { wrap: wrap, domId: domId };
}

function addOption(control, value, labelText) {
  var option = document.createElement("option");
  option.value = value;
  option.setAttribute("value", value);
  option.textContent = labelText;
  control.appendChild(option);
}

function addSelect(bench, name, labelText, choices) {
  /*
    A closed list, BLANK FIRST AND WITH NOTHING MARKED SELECTED, so what a user
    agent shows at rest is the blank one. The blank option carries no prompt text
    either: a prompt is one more thing this panel would be saying about the choice,
    and the label above already names it.
  */
  var slot = addField(bench, name, labelText);
  var control = document.createElement("select");
  control.id = slot.domId;
  control.className = "bench-input";
  control.setAttribute("name", name);
  control.setAttribute("autocomplete", "off");
  control.setAttribute("aria-required", "true");
  addOption(control, "", "");
  for (var index = 0; index < choices.length; index += 1) {
    addOption(control, choices[index].value, choices[index].label);
  }
  slot.wrap.appendChild(control);
  return control;
}

function addRateInput(bench, name, labelText) {
  var slot = addField(bench, name, labelText);
  var input = document.createElement("input");
  input.id = slot.domId;
  input.className = "bench-input";
  input.setAttribute("type", "text");
  input.setAttribute("name", name);
  input.setAttribute("autocomplete", "off");
  input.setAttribute("spellcheck", "false");
  input.setAttribute("aria-required", "true");
  input.value = "";
  slot.wrap.appendChild(input);
  return input;
}

function readField(control) {
  /* What the reader stated, as a string and only ever as a string. */
  return typeof control.value === "string" ? control.value : "";
}

function plainChoices(values) {
  var choices = [];
  for (var index = 0; index < values.length; index += 1) {
    choices.push({ value: values[index], label: values[index] });
  }
  return choices;
}

function displayNames(registry) {
  /*
    The registry's display name for each item key. A null prototype, so a key
    that happens to spell a member of Object.prototype finds no name rather than
    a function.
  */
  var names = Object.create(null);
  var rows = Array.isArray(registry.items) ? registry.items : [];
  for (var index = 0; index < rows.length; index += 1) {
    var row = rows[index];
    if (row && typeof row.display_name === "string" && row.display_name !== "") {
      names[row.key] = row.display_name;
    }
  }
  return names;
}

function nameOf(names, key) {
  /* The display name where the registry holds one, the key where it does not. */
  return names[key] === undefined ? String(key) : names[key];
}

function targetChoices(targets, names) {
  /* The served list in its served order. No sort, no filter, no default. */
  var choices = [];
  for (var index = 0; index < targets.length; index += 1) {
    choices.push({ value: String(targets[index]), label: nameOf(names, targets[index]) });
  }
  return choices;
}

/* --- reading one settled outcome ---------------------------------------- */

function dataOf(outcome) {
  /* The data object of a 200, or null. A refusal carries none. */
  var body = outcome && typeof outcome === "object" ? outcome.body : null;
  return body && typeof body === "object" ? objectOrNull(body.data) : null;
}

function refusalWord(outcome) {
  /*
    Why this outcome holds no data, as one short line naming the code and the word,
    or null when it does hold data.

    THE WHOLE ENVELOPE ARRIVES HERE, which is why app.js hands a door's callback the
    whole body: the reason sits outside data, and a panel reading only data would
    render every refusal as silence.
  */
  if (!outcome || typeof outcome !== "object") {
    return NO_OUTCOME_LINE;
  }
  if (!outcome.reached) {
    return UNREACHABLE_LINE;
  }
  if (dataOf(outcome)) {
    return null;
  }
  var body = outcome.body;
  if (body && typeof body === "object" && isPresent(body.reason)) {
    return "the endpoint refused with " + textOf(outcome.http) + ": " + textOf(body.reason) + ".";
  }
  return "the endpoint answered " + textOf(outcome.http) + " with no data.";
}

function refusalDetail(outcome) {
  /* The one fixed line the contract looks up for a reason, or null. */
  var body = outcome && typeof outcome === "object" ? outcome.body : null;
  return body && typeof body === "object" && isPresent(body.detail) ? textOf(body.detail) : null;
}

/* --- rendering a plan outcome ------------------------------------------- */

function addFieldLine(parent, label, value) {
  if (isPresent(value)) {
    addNote(parent, label + ": " + textOf(value));
  }
}

function addFieldList(parent, label, value) {
  if (!isPresent(value)) {
    return;
  }
  /*
    EMPTY IS AN ANSWER AND ABSENT IS A DIFFERENT ONE. An empty trimmed says the bound
    dropped nothing, where an absent one says no search ran, and an empty list under
    its label would read as a list that failed to arrive.
  */
  var values = Array.isArray(value) ? value : [value];
  if (values.length === 0) {
    addNote(parent, label + ": none");
    return;
  }
  var lines = [];
  for (var index = 0; index < values.length; index += 1) {
    lines.push(textOf(values[index]));
  }
  addGroup(parent, label, lines);
}

function renderPlanOutcome(region, planOutcome) {
  /*
    What the search did, including when it made no card. A refused trace yields no
    card, so for a no-plan this block is the whole of the answer, and each field
    appears only when the body carried it.
  */
  addLine(region, "h3", "", "Plan outcome");
  if (!objectOrNull(planOutcome)) {
    addNote(region, NO_OUTCOME_KEY);
    return;
  }
  addFieldLine(region, "plan status", planOutcome.status);
  addFieldLine(region, "reason", planOutcome.reason);
  addFieldLine(region, "redesign", planOutcome.redesign);
  addFieldList(region, "trimmed recipes", planOutcome.trimmed);
  addFieldList(region, "unmade items", planOutcome.unmade);
}

registerPanel("advice", function mountAdvice(root, data) {
  /*
    data is the resolved payloads plus the doors. Any payload may be null, and the
    doors may be absent entirely: the seam grader's harness hands a mount no actions
    key at all, and a panel assuming one would throw there and be marked failed.
  */
  var advice = objectOrNull(data ? data.advice : null);
  var registry = objectOrNull(data ? data.registry : null);
  var actions = objectOrNull(data ? data.actions : null);
  var askDoor = actions && typeof actions.requestAdvice === "function" ? actions.requestAdvice : null;
  var readDoor =
    actions && typeof actions.requestDerivation === "function" ? actions.requestDerivation : null;

  var heading = document.createElement("h2");
  heading.id = "h-panel-advice";
  heading.textContent = "Advice";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  addLine(
    root,
    "p",
    "lede",
    "What the advisor says about this world, and what it says to a target you state. Nothing on this panel is computed in the page."
  );

  /*
    A NAMED REFUSAL AND NO BENCH. Each missing body is named on its own, because
    the two have different remedies: no save is not no install. A bench here would
    be a control that could only be refused.
  */
  if (!advice) {
    addNote(root, "/api/advice did not answer, so this panel lists no card and offers no bench.");
  }
  if (!registry) {
    addNote(root, "/api/registry did not answer, so this panel has no target list and no bench.");
  }
  if (!advice || !registry) {
    return;
  }

  /*
    Whether this panel is waiting on an answer. THE PANEL HOLDS ITS OWN FLAG rather
    than leaning on the seam's, which would refuse the second request anyway: a
    press would spend itself learning what the panel already knew, and the reader
    would read "refused" where the truth is that their answer is still coming.
  */
  var waiting = false;

  function ask(control, say, askingLine, call, settle) {
    /*
      One request through one door, from the press that made it to what landed.

      THE LINE IS WRITTEN BEFORE THE DOOR IS CALLED, because a door that answered
      synchronously would settle inside this call and a line written afterwards
      would paint over the answer. aria-disabled and never disabled, for the reason
      refresh() in app.js gives: disabling a focused control drops its keyboard
      reader to the top of the document.
    */
    if (waiting) {
      say(BUSY_LINE);
      return;
    }
    function release() {
      waiting = false;
      control.removeAttribute("aria-disabled");
    }
    waiting = true;
    control.setAttribute("aria-disabled", "true");
    say(askingLine);

    var accepted = false;
    try {
      accepted = call(function (outcome) {
        release();
        settle(outcome);
      });
    } catch (doorFailure) {
      /*
        SWALLOWED, AND DELIBERATELY EMPTY. An exception's message on this machine
        can carry an absolute path under a home directory, and this page is what
        would publish it. A throw is a refusal, which is what it is from here.
      */
      accepted = false;
    }
    if (!accepted) {
      /*
        A FALSE RETURN MEANS THE CALLBACK NEVER FIRES, so the flag comes down here
        or this panel would refuse every later press over a request never made.
      */
      release();
      say(NOT_SENT_LINE);
    }
  }

  /* --- the cards -------------------------------------------------------- */

  function renderCard(region, card, position, statement) {
    var box = document.createElement("div");
    box.className = "hud-card advice-card";
    addLine(box, "p", "note advice-headline", textOf(card.headline));
    addLine(box, "p", "note", textOf(card.reason));

    var row = document.createElement("div");
    row.className = "advice-read";
    var read = document.createElement("button");
    read.id = "advice-read-" + String(position);
    read.setAttribute("type", "button");
    read.setAttribute("aria-label", "Read derivation: " + textOf(card.headline));
    read.textContent = "Read derivation";
    row.appendChild(read);
    box.appendChild(row);

    var status = addLine(box, "p", "lede", UNREAD_LINE);
    status.id = "advice-read-status-" + String(position);
    status.setAttribute("aria-live", "polite");

    /*
      HIDDEN UNTIL IT HOLDS ONE, AND THEN LEFT STANDING THROUGH A RE-READ: a press
      in flight says so on the line above and replaces nothing until it lands.
    */
    var tier3 = addLine(box, "pre", "advice-derivation", "");
    tier3.id = "advice-derivation-" + String(position);
    tier3.hidden = true;

    function say(message) {
      status.textContent = message;
    }

    function settle(outcome) {
      var refusal = refusalWord(outcome);
      if (refusal !== null) {
        /* An earlier reading under a refusal would read as this request's answer. */
        tier3.textContent = "";
        tier3.hidden = true;
        say(refusal);
        return;
      }
      tier3.textContent = textOf(dataOf(outcome).derivation);
      tier3.hidden = false;
      say(READ_LINE);
    }

    read.addEventListener("click", function onRead() {
      if (!readDoor) {
        say(NO_READ_DOOR_LINE);
        return;
      }
      ask(
        read,
        say,
        READING_LINE,
        function (settled) {
          return readDoor(card.id, statement, settled);
        },
        settle
      );
    });

    region.appendChild(box);
  }

  function renderCards(region, listing, statement) {
    addLine(region, "h3", "", "Cards");
    var rows = Array.isArray(listing.cards) ? listing.cards : [];
    var shown = 0;
    for (var index = 0; index < rows.length; index += 1) {
      var card = objectOrNull(rows[index]);
      /* Strictly true. A hidden card is served so a surface can restore it, not list it. */
      if (card && card.visible === true) {
        renderCard(region, card, shown, statement || {});
        shown += 1;
      }
    }
    if (shown === 0) {
      addNote(region, statement ? NO_CARD_STATED : NO_CARD_HELD);
    }
  }

  /* --- the bench, where there is a list to offer ------------------------ */

  var names = displayNames(registry);
  var targets = Array.isArray(registry.plan_targets) ? registry.plan_targets : [];
  var region = document.createElement("div");
  region.id = "advice-answer";
  region.className = "bench-result";
  region.setAttribute("aria-live", "polite");

  /*
    NO LIST, NO BENCH, AND THE WORLD'S OWN CARDS STILL LIST. A registry body with no
    plan_targets can only come from a server older than this page, and an empty one
    leaves nothing to select. Neither is a reason to hide advice already held.
  */
  if (targets.length === 0) {
    addNote(root, "/api/registry served no plan_targets, so there is no target to state here.");
    root.appendChild(region);
    renderCards(region, advice, null);
    return;
  }

  addLine(
    root,
    "p",
    "lede",
    "All four are required and none starts filled in: there is no default target and no pointer at the next milestone. The rate is per minute: an integer, an exact decimal or num/den."
  );

  var bench = document.createElement("div");
  bench.className = "bench";
  root.appendChild(bench);

  var targetControl = addSelect(bench, "target", "target", targetChoices(targets, names));
  var rateControl = addRateInput(bench, "rate", "rate per minute");
  var directionControl = addSelect(bench, "direction", "direction", plainChoices(DIRECTION_VALUES));
  var policyControl = addSelect(
    bench,
    "byproduct_policy",
    "byproduct policy",
    plainChoices(POLICY_VALUES)
  );

  var button = document.createElement("button");
  button.id = "advice-ask";
  button.setAttribute("type", "button");
  button.textContent = "Ask for advice";
  bench.appendChild(button);

  var statusLine = addLine(bench, "p", "note bench-status", IDLE_LINE);
  statusLine.id = "advice-status";
  statusLine.setAttribute("aria-live", "polite");

  bench.appendChild(region);

  function sayStatus(message) {
    statusLine.textContent = message;
  }

  function fillAnswer(outcome, statement) {
    /* What one settled answer writes into the emptied region and onto the status line. */
    var refusal = refusalWord(outcome);
    if (refusal !== null) {
      sayStatus(refusal);
      var detail = refusalDetail(outcome);
      addNote(region, detail === null ? "no card was read, so none is listed." : detail);
      return;
    }
    var listing = dataOf(outcome);
    sayStatus("the endpoint answered " + textOf(outcome.http) + ".");
    addNote(
      region,
      "answering: "
        + nameOf(names, statement.target)
        + " at "
        + statement.rate
        + " per minute, direction "
        + statement.direction
        + ", byproduct policy "
        + statement.byproduct_policy
        + "."
    );
    renderCards(region, listing, statement);
    renderPlanOutcome(region, listing.plan_outcome);
  }

  function renderAnswer(outcome, statement) {
    /*
      THE REGION IS ONLY EVER REWRITTEN HERE, ON A SETTLED ANSWER, so a request in
      flight moves nothing it is about to replace. A refusal replaces it too: a card
      left standing under a refusal would read as that request's answer.

      A READER STANDING IN THE REGION IS NOT DROPPED WITH IT. A reader may tab onto a
      card's button while a request runs, and emptying the region then removes the
      focused node, which sends them to the top of the document: the fault refresh() in
      app.js records. Asked before the region empties, because afterwards the answer is
      always no. They land on the button that asked, and a reader standing anywhere else,
      typing the next rate say, is not moved at all.
    */
    var keepFocus = region.contains(document.activeElement);
    region.removeAttribute("aria-busy");
    clearNode(region);
    fillAnswer(outcome, statement);
    if (keepFocus) {
      button.focus();
    }
  }

  button.addEventListener("click", function onAsk() {
    /* A statement is read fresh on every press and is never changed afterwards. */
    var statement = {
      target: readField(targetControl),
      rate: readField(rateControl),
      direction: readField(directionControl),
      byproduct_policy: readField(policyControl)
    };
    var missing = [];
    if (statement.target === "") {
      missing.push("target");
    }
    if (statement.rate === "") {
      missing.push("rate");
    }
    if (statement.direction === "") {
      missing.push("direction");
    }
    if (statement.byproduct_policy === "") {
      missing.push("byproduct policy");
    }
    if (missing.length) {
      sayStatus("still empty: " + missing.join(", ") + ".");
      return;
    }
    if (!askDoor) {
      sayStatus(NO_ADVICE_DOOR_LINE);
      return;
    }
    ask(
      button,
      sayStatus,
      ASKING_LINE,
      function (settled) {
        region.setAttribute("aria-busy", "true");
        return askDoor(statement, settled);
      },
      function (outcome) {
        renderAnswer(outcome, statement);
      }
    );
    if (!waiting) {
      /* Refused, or settled synchronously: either way nothing is outstanding. */
      region.removeAttribute("aria-busy");
    }
  });

  renderCards(region, advice, null);
});
}());
