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

  CS-1396 - A SECOND FREE SELECTOR BESIDE THE TARGETS: plan_schematics, every ClassName the
  schematic catalog holds, in the order the registry body served it and starting empty like
  every other control. A press with a schematic chosen states the schematic, a direction and a
  policy and NEVER A RATE - each cost item's rate is the one its requirement publishes, which
  this page never sees. A schematic and a target chosen together leave the press inert and
  name both fields. A body serving no schematic says so by the key's name and offers no
  selector, and the target bench beside it stands.

  NOTHING IS COMPUTED HERE. plan_targets arrives on the registry body in the order
  it was served and is listed in that order, and plan_schematics the same. A card's headline and reason are tier
  1 and tier 2 as the listing carries them, and tier 3 is shown as the text the
  derivation route answered, never parsed. The rate is what the reader typed, in
  the spelling the API takes - an integer, an exact decimal or num/den, per minute
  - and it stays text the whole way, because a value parsed here would be a binary
  float in the answer path, which non-negotiable 6 bans outright.

  THE TWO CLOSED VOCABULARIES ARE SPELLED BELOW BECAUSE NO ROUTE SERVES THEM, and
  tests/surface/test_panel_advice.py binds each one to the Python constant it
  copies, which nothing does for panel_optimize.js's two lists.

  NO FETCH IN THIS FILE. data.actions.requestAdvice, data.actions.requestDerivation,
  (CS-1376) data.actions.requestState and (CS-1397) data.actions.requestAct are the
  only ways out, and app.js builds every query from its own tables, so this panel
  chooses the values and never the names, the path or the verb.

  CS-1397 - TWO PRESSES RECORD AN ACT, AND NO READ DOES. "Ask for advice" (a stated target)
  and "Advise on this world" (no statement) both go through requestAct, which POSTs
  /api/advice/act: the advisor runs and the ledger records what the run implies, once, which
  is the act the aging guard counts. The listing is a GET and writes nothing, so the first
  paint, the derivation reads and the listing asked again after a state was recorded stay
  reads. The act answers with the listing body, so it is drawn exactly as a listing is.

  CS-1376 - FOUR CONTROLS ON A STATED CARD: accept, dismiss, snooze and pin. Each posts
  one state through the state door with the card id and the four that PRODUCED the card,
  and a card no statement produced carries none. A SNOOZE NAMES A LENGTH AS A TOKEN, never
  an instant: the page reads no clock and adds nothing, and the advisor resolves the token
  against its own injected clock. A recorded state is not shown on the strength of the
  click: the panel asks the listing again under the same statement and draws what the advisor
  now resolves, so a card the advisor hides leaves the page and one it keeps reads its
  served state.

  A CARD REMEMBERS THE STATEMENT THAT PRODUCED IT. The bench stays editable after an
  answer lands, and a card id only means something under the statement it was
  listed for, so a derivation button closes over that statement - the four of an item or
  the three of a schematic - and never reads the fields again. A card a repaint listed was produced by no statement and asks with
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

/*
  clockspeed/advisor/ledger.py, SNOOZE_DURATIONS: the tokens a snooze may name, as the
  mapping's keys. A test binds this list to the mapping exactly, so a token added there
  and not here reads as a missing choice.
*/
var SNOOZE_CHOICES = [
  { value: "1h", label: "1 hour" },
  { value: "4h", label: "4 hours" },
  { value: "1d", label: "1 day" },
  { value: "1w", label: "1 week" }
];

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
var NO_ACT_DOOR_LINE = "this page published no act door; nothing was sent.";
var NO_READ_DOOR_LINE = "this page published no derivation door; nothing was sent.";
var NO_STATE_DOOR_LINE = "this page published no state door; nothing was sent.";
var UNREACHABLE_LINE = "no answer: unreachable.";
var NO_OUTCOME_LINE = "the page returned no outcome at all, so nothing landed.";
/* Names both fields, and fits the two reserved lines. */
var BOTH_CHOSEN_LINE = "choose a target or a schematic, not both; nothing was sent.";
var NO_SCHEMATICS_LINE =
  "/api/registry served no plan_schematics, so there is no schematic to state here.";

var STATE_IDLE_LINE = "state not changed.";
var RECORDING_LINE = "recording the state ...";
var RECORDED_LINE = "state recorded; reading the listing again.";
/* CS-1400: what that line becomes once the listing was read and the card stayed in place. */
var RECORDED_SHOWN_LINE = "state recorded.";
var NO_LENGTH_LINE = "still empty: snooze length.";

var READING_LINE = "reading the derivation ...";
var UNREAD_LINE = "derivation not read.";
var READ_LINE = "derivation read.";

/*
  CS-1400 S1: the flow block's own heading and the key to its leading star. The legend
  names the mark by what it measures, the highest rate, and says nothing about a limit.
*/
var FLOW_LABEL_TEXT = "Boundary flow";
var FLOW_LEGEND_TEXT = "* marks the edge with the highest rate.";
var SNOOZE_LABEL_TEXT = "Snooze length";

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

/*
  CS-1360 - THE BOUNDARY FLOW, AS TEXT. The derivation body's flow object is
  transcribed one line per edge and never re-derived: the rate is the num/den the
  server served, the transport is the server's word, and the starred edge is the one
  the server marked. The bar is presentation only - a run of one ASCII character whose
  length is the edge's width over the marked width, counted up by multiplying the served
  integers, so no float and no quotient enters. NO CAPACITY IS SHOWN OR IMPLIED: the mark means the
  highest rate, and this file says nothing about a limit.
*/
var FLOW_BAR_CELLS = 20;
var FLOW_BAR_CHAR = "#";

function rateText(rate) {
  /* A served {num, den} as text: a whole number bare, anything else as num/den. */
  var ratio = objectOrNull(rate);
  if (!ratio || !Number.isInteger(ratio.num) || !Number.isInteger(ratio.den) || ratio.den < 1) {
    return "-";
  }
  return ratio.den === 1 ? String(ratio.num) : String(ratio.num) + "/" + String(ratio.den);
}

function barOf(width, widest) {
  /*
    The longest run k, at most FLOW_BAR_CELLS, with k * widest <= cells * width, tried
    by multiplying and comparing the served integers. This panel parses no number and
    divides nothing (tests/surface/test_panel_advice.py sweeps for both), so the bar is
    counted up rather than quotiented, and a rate above zero always earns one cell.
  */
  var edge = objectOrNull(width);
  var top = objectOrNull(widest);
  if (!edge || !top || !Number.isInteger(edge.num) || !Number.isInteger(edge.den)) {
    return "";
  }
  if (!Number.isInteger(top.num) || !Number.isInteger(top.den) || top.num < 1 || edge.num < 1) {
    return "";
  }
  var cells = 1;
  while (
    cells < FLOW_BAR_CELLS &&
    (cells + 1) * edge.den * top.num <= FLOW_BAR_CELLS * edge.num * top.den
  ) {
    cells += 1;
  }
  return FLOW_BAR_CHAR.repeat(cells);
}

function flowLines(flow) {
  /* One text line per edge, or null when the body carries no flow or no edge. */
  var view = objectOrNull(flow);
  if (!view || !Array.isArray(view.edges) || view.edges.length === 0) {
    return null;
  }
  var widest = null;
  for (var seek = 0; seek < view.edges.length; seek += 1) {
    var candidate = objectOrNull(view.edges[seek]);
    if (candidate && candidate.marked === true) {
      widest = candidate.width;
    }
  }
  var lines = [];
  for (var index = 0; index < view.edges.length; index += 1) {
    var edge = objectOrNull(view.edges[index]);
    if (edge) {
      lines.push(
        (edge.marked === true ? "* " : "  ") +
          textOf(edge.item) + " " + textOf(edge.role) + " " + rateText(edge.width) +
          " per min on " + textOf(edge.transport) + " " + barOf(edge.width, widest)
      );
    }
  }
  return lines.length === 0 ? null : lines;
}

function hasStar(lines) {
  /* Whether any line of a flow starts with the mark flowLines writes for the marked edge. */
  for (var index = 0; index < lines.length; index += 1) {
    if (lines[index].charAt(0) === "*") {
      return true;
    }
  }
  return false;
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

function schematicChoices(schematics) {
  /* The served list in its served order, each its own ClassName. No sort, no filter. */
  var choices = [];
  for (var index = 0; index < schematics.length; index += 1) {
    choices.push({ value: String(schematics[index]), label: String(schematics[index]) });
  }
  return choices;
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
  addFieldLine(region, "redesign reason", planOutcome.redesign_reason);
  addFieldList(region, "trimmed recipes", planOutcome.trimmed);
  addFieldList(region, "unmade items", planOutcome.unmade);
  addFieldList(region, "raw items with no known extractor", planOutcome.raw_unknown);
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
  var stateDoor =
    actions && typeof actions.requestState === "function" ? actions.requestState : null;
  var actDoor = actions && typeof actions.requestAct === "function" ? actions.requestAct : null;

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

  /*
    CS-1400. WHAT THE REGION HOLDS, kept as references and compared by id only. standing is
    the cards the last renderCards wrote, each with its box and its state line; answerStands
    says whether the region holds a request's answer or refusal rather than the mount
    listing.
  */
  var standing = [];
  var answerStands = false;

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

  function addPlainControl(row, card, position, stem, label, onPress) {
    /* One state button, named for its card so a screen reader can tell four rows apart. */
    var control = document.createElement("button");
    control.id = "advice-" + stem + "-" + String(position);
    control.setAttribute("type", "button");
    control.setAttribute("aria-label", label + ": " + textOf(card.headline));
    control.textContent = label;
    control.addEventListener("click", onPress);
    row.appendChild(control);
    return control;
  }

  function renderControls(box, card, position, statement) {
    /*
      THE FOUR CONTROLS OF A STATED CARD, and the line they answer on. The statement is
      the one that produced the card and is copied field by field into every press, never
      read from the bench again.
    */
    var row = document.createElement("div");
    row.className = "advice-read advice-controls";
    var line = addLine(box, "p", "lede", STATE_IDLE_LINE);
    line.id = "advice-state-status-" + String(position);
    line.setAttribute("aria-live", "polite");

    function sayState(message) {
      line.textContent = message;
    }

    function record(control, kind, length) {
      if (!stateDoor) {
        sayState(NO_STATE_DOOR_LINE);
        return;
      }
      /*
        THE STATEMENT'S OWN NAMES, copied as they stand: the four of an item statement or
        the three of a schematic's, and never a name the card's statement did not state.
      */
      var params = {};
      var names = Object.keys(statement);
      for (var at = 0; at < names.length; at += 1) {
        params[names[at]] = statement[names[at]];
      }
      params.state = kind;
      if (length !== null) {
        params.duration = length;
      }
      ask(
        control,
        sayState,
        RECORDING_LINE,
        function (settled) {
          return stateDoor(card.id, params, settled);
        },
        function (outcome) {
          var refusal = refusalWord(outcome);
          if (refusal !== null) {
            sayState(refusal);
            return;
          }
          sayState(RECORDED_LINE);
          rereadStated(statement, function onShownInPlace() {
            sayState(RECORDED_SHOWN_LINE);
          });
        }
      );
    }

    var accept = addPlainControl(row, card, position, "accept", "Accept", function onAccept() {
      record(accept, "accepted", null);
    });
    var dismiss = addPlainControl(row, card, position, "dismiss", "Dismiss", function onDismiss() {
      record(dismiss, "dismissed", null);
    });
    var pin = addPlainControl(row, card, position, "pin", "Pin", function onPin() {
      record(pin, "pinned", null);
    });

    /*
      CS-1400 S2: THE SNOOZE LENGTH, ITS VISIBLE LABEL AND ITS BUTTON ARE ONE GROUP, so the
      three stay on one line and the select reads as the length the button uses. The
      accessible name still opens with the visible text, so a speech user who says what
      they see reaches it.
    */
    var group = document.createElement("div");
    group.className = "advice-snooze";
    var pickerId = "advice-snooze-for-" + String(position);
    var pickerLabel = addLine(group, "label", "bench-label", SNOOZE_LABEL_TEXT);
    pickerLabel.id = "advice-snooze-label-" + String(position);
    pickerLabel.setAttribute("for", pickerId);
    var picker = document.createElement("select");
    picker.id = pickerId;
    picker.className = "bench-input";
    picker.setAttribute("name", "duration");
    picker.setAttribute("autocomplete", "off");
    picker.setAttribute("aria-label", SNOOZE_LABEL_TEXT + ": " + textOf(card.headline));
    addOption(picker, "", "");
    for (var index = 0; index < SNOOZE_CHOICES.length; index += 1) {
      addOption(picker, SNOOZE_CHOICES[index].value, SNOOZE_CHOICES[index].label);
    }
    group.appendChild(picker);

    var snooze = addPlainControl(group, card, position, "snooze", "Snooze", function onSnooze() {
      var length = readField(picker);
      if (length === "") {
        sayState(NO_LENGTH_LINE);
        return;
      }
      record(snooze, "snoozed", length);
    });
    row.appendChild(group);
    box.appendChild(row);
  }

  function renderCard(region, card, position, statement, stated) {
    var box = document.createElement("div");
    box.className = "hud-card advice-card";
    addLine(box, "p", "note advice-headline", textOf(card.headline));
    addLine(box, "p", "note", textOf(card.reason));
    var stateLine = null;
    if (stated) {
      /* The state the advisor served, as served: the page decides nothing about it. */
      stateLine = addLine(box, "p", "note", "state: " + textOf(card.state));
    }

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

    /*
      CS-1360: the boundary flow, hidden until the body carries one. CS-1400 S1: it carries
      a heading of its own, which the block is labelled by, and under it the key to the
      leading star. The three show and hide together.
    */
    var flowLabel = addLine(box, "p", "note advice-flow-label", FLOW_LABEL_TEXT);
    flowLabel.id = "advice-flow-label-" + String(position);
    flowLabel.hidden = true;
    var flowBox = addLine(box, "pre", "advice-derivation", "");
    flowBox.id = "advice-flow-" + String(position);
    /* A pre has no role that takes a name, so aria-labelledby alone is ignored. */
    flowBox.setAttribute("role", "group");
    flowBox.setAttribute("aria-labelledby", flowLabel.id);
    flowBox.hidden = true;
    var flowLegend = addLine(box, "p", "note advice-flow-legend", FLOW_LEGEND_TEXT);
    flowLegend.id = "advice-flow-legend-" + String(position);
    flowLegend.hidden = true;

    function say(message) {
      status.textContent = message;
    }

    function settle(outcome) {
      var refusal = refusalWord(outcome);
      if (refusal !== null) {
        /* An earlier reading under a refusal would read as this request's answer. */
        tier3.textContent = "";
        tier3.hidden = true;
        flowBox.textContent = "";
        flowBox.hidden = true;
        flowLabel.hidden = true;
        flowLegend.hidden = true;
        say(refusal);
        return;
      }
      tier3.textContent = textOf(dataOf(outcome).derivation);
      tier3.hidden = false;
      var flow = flowLines(dataOf(outcome).flow);
      flowBox.textContent = flow === null ? "" : flow.join(String.fromCharCode(10));
      flowBox.hidden = flow === null;
      flowLabel.hidden = flow === null;
      /* The key to a star is shown only beside one: the first character of a starred line. */
      flowLegend.hidden = flow === null || !hasStar(flow);
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

    if (stated) {
      renderControls(box, card, position, statement);
    }

    region.appendChild(box);
    return { id: card.id, box: box, stateLine: stateLine };
  }

  function renderCards(region, listing, statement) {
    addLine(region, "h3", "", "Cards");
    var rows = Array.isArray(listing.cards) ? listing.cards : [];
    var shown = 0;
    /* The cards on the page now, in their order, so a re-read can be matched to them by id. */
    standing = [];
    for (var index = 0; index < rows.length; index += 1) {
      var card = objectOrNull(rows[index]);
      /* Strictly true. A hidden card is served so a surface can restore it, not list it. */
      if (card && card.visible === true) {
        standing.push(renderCard(region, card, shown, statement || {}, Boolean(statement)));
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
  var schematics = Array.isArray(registry.plan_schematics) ? registry.plan_schematics : [];
  var region = document.createElement("div");
  region.id = "advice-answer";
  region.className = "bench-result";
  region.setAttribute("aria-live", "polite");

  /*
    NO LIST, NO BENCH, AND THE WORLD'S OWN CARDS STILL LIST. A registry body with no
    plan_targets can only come from a server older than this page, and an empty one
    leaves nothing to select. Neither is a reason to hide advice already held.
  */
  if (targets.length === 0 && schematics.length === 0) {
    addNote(root, "/api/registry served no plan_targets, so there is no target to state here.");
    root.appendChild(region);
    renderCards(region, advice, null);
    return;
  }

  addLine(
    root,
    "p",
    "lede",
    schematics.length === 0
      ? "All four are required and none starts filled in: there is no default target and no pointer at the next milestone. The rate is per minute: an integer, an exact decimal or num/den."
      : "State a target with all four, or a schematic with a direction and a byproduct policy and no rate. None starts filled in: there is no default and no pointer at the next milestone. The rate is per minute: an integer, an exact decimal or num/den."
  );

  if (targets.length === 0) {
    addNote(root, "/api/registry served no plan_targets, so there is no target to state here.");
  }
  if (schematics.length === 0) {
    addNote(root, NO_SCHEMATICS_LINE);
  }

  var bench = document.createElement("div");
  bench.className = "bench";
  root.appendChild(bench);

  var targetControl = addSelect(bench, "target", "target", targetChoices(targets, names));
  var schematicControl = null;
  if (schematics.length > 0) {
    schematicControl = addSelect(bench, "schematic", "schematic", schematicChoices(schematics));
    /* One of target and schematic is stated, so neither is required on its own. */
    schematicControl.removeAttribute("aria-required");
  }
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

  var actButton = document.createElement("button");
  actButton.id = "advice-act";
  actButton.setAttribute("type", "button");
  actButton.textContent = "Advise on this world";
  bench.appendChild(actButton);

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
    if (!statement) {
      /* An act with no statement: this world's own cards, and no plan was asked for. */
      addNote(region, "answering: this world, with no target stated.");
      renderCards(region, listing, null);
      return;
    }
    if (isPresent(statement.schematic)) {
      addNote(
        region,
        "answering: schematic "
          + statement.schematic
          + ", direction "
          + statement.direction
          + ", byproduct policy "
          + statement.byproduct_policy
          + "."
      );
      renderCards(region, listing, statement);
      renderPlanOutcome(region, listing.plan_outcome);
      return;
    }
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

  function renderAnswer(outcome, statement, focusTarget) {
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
    answerStands = true;
    if (keepFocus) {
      (focusTarget || button).focus();
    }
  }

  function reconcileInPlace(outcome) {
    /*
      CS-1400 H2. A RE-READ AFTER A RECORDED STATE IS DRAWN WITHOUT REPAINTING THE ANSWER
      WHEN IT IS THE SAME CARDS, so the pressed control keeps focus and a derivation the
      reader opened stays open (hud_doctrine section 2: fixed positions, no reflow).
      Returns false when it cannot, and the caller draws the whole answer as before.

      EQUALITY ONLY. The re-read's visible ids must be exactly the standing ids that are
      still visible, in the standing order. A card the page does not hold, a changed order,
      a refusal or no visible card at all cannot be reconciled and is not tried. What changes
      in place is a kept card's state line, as served, and a card the advisor no longer
      lists leaves by removeChild of the box this panel built.
    */
    var listing = dataOf(outcome);
    if (refusalWord(outcome) !== null || !listing || standing.length === 0) {
      return false;
    }
    var rows = Array.isArray(listing.cards) ? listing.cards : [];
    var visible = [];
    for (var at = 0; at < rows.length; at += 1) {
      var row = objectOrNull(rows[at]);
      if (row && row.visible === true) {
        visible.push(row);
      }
    }
    if (visible.length === 0) {
      return false;
    }
    var listed = Object.create(null);
    for (var mark = 0; mark < visible.length; mark += 1) {
      listed[String(visible[mark].id)] = true;
    }
    var kept = [];
    for (var held = 0; held < standing.length; held += 1) {
      if (listed[String(standing[held].id)] === true) {
        kept.push(standing[held]);
      }
    }
    if (kept.length !== visible.length) {
      return false;
    }
    for (var same = 0; same < kept.length; same += 1) {
      if (String(kept[same].id) !== String(visible[same].id)) {
        return false;
      }
    }

    var keepFocus = region.contains(document.activeElement);
    var still = [];
    for (var each = 0; each < standing.length; each += 1) {
      if (listed[String(standing[each].id)] === true) {
        still.push(standing[each]);
      } else {
        region.removeChild(standing[each].box);
      }
    }
    for (var state = 0; state < still.length; state += 1) {
      if (still[state].stateLine) {
        still[state].stateLine.textContent = "state: " + textOf(visible[state].state);
      }
    }
    standing = still;
    region.removeAttribute("aria-busy");
    sayStatus("the endpoint answered " + textOf(outcome.http) + ".");
    /* The pressed card may be the one that left: a reader there lands on the button that asked. */
    if (keepFocus && !region.contains(document.activeElement)) {
      button.focus();
    }
    return true;
  }

  function rereadStated(statement, onShownInPlace) {
    /*
      THE LISTING ASKED AGAIN UNDER THE STATEMENT THAT PRODUCED THE CARDS, after a state
      was recorded. Drawn through renderAnswer like any answer, so what stays and what
      leaves is the advisor's visible flag and nothing this panel works out.
    */
    if (!askDoor) {
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
        if (reconcileInPlace(outcome)) {
          onShownInPlace();
          return;
        }
        renderAnswer(outcome, statement);
      }
    );
    if (!waiting) {
      region.removeAttribute("aria-busy");
    }
  }

  function dropStandingAnswer() {
    /*
      CS-1400 Y1. THE INERT PRESS SENDS NOTHING, SO NO EARLIER ANSWER OR REFUSAL MAY STAND
      BESIDE ITS LINE. What a request wrote is cleared and the mount listing is drawn again
      with no statement, which is the state the page was in before any press; no door is
      called. A region holding only the mount listing is left exactly as it is.
    */
    if (!answerStands) {
      return;
    }
    var keepFocus = region.contains(document.activeElement);
    region.removeAttribute("aria-busy");
    clearNode(region);
    renderCards(region, advice, null);
    answerStands = false;
    if (keepFocus) {
      button.focus();
    }
  }

  function askSchematic(schematic) {
    /*
      A SCHEMATIC STATEMENT: the schematic, a direction and a policy, and no rate and no
      target whatever the rate field holds. Read fresh on every press like the item's.
    */
    var stated = {
      schematic: schematic,
      direction: readField(directionControl),
      byproduct_policy: readField(policyControl)
    };
    var absent = [];
    if (stated.direction === "") {
      absent.push("direction");
    }
    if (stated.byproduct_policy === "") {
      absent.push("byproduct policy");
    }
    if (absent.length) {
      sayStatus("still empty: " + absent.join(", ") + ".");
      return;
    }
    if (!actDoor) {
      sayStatus(NO_ACT_DOOR_LINE);
      return;
    }
    ask(
      button,
      sayStatus,
      ASKING_LINE,
      function (settled) {
        region.setAttribute("aria-busy", "true");
        return actDoor(stated, settled);
      },
      function (outcome) {
        renderAnswer(outcome, stated);
      }
    );
    if (!waiting) {
      region.removeAttribute("aria-busy");
    }
  }

  button.addEventListener("click", function onAsk() {
    var schematic = schematicControl === null ? "" : readField(schematicControl);
    if (schematic !== "") {
      if (readField(targetControl) !== "") {
        dropStandingAnswer();
        sayStatus(BOTH_CHOSEN_LINE);
        return;
      }
      askSchematic(schematic);
      return;
    }
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
    if (!actDoor) {
      sayStatus(NO_ACT_DOOR_LINE);
      return;
    }
    ask(
      button,
      sayStatus,
      ASKING_LINE,
      function (settled) {
        region.setAttribute("aria-busy", "true");
        return actDoor(statement, settled);
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

  actButton.addEventListener("click", function onAct() {
    /*
      NO STATEMENT, so the door is handed an empty one and the answer is drawn with none: the
      cards this world holds, each carrying no statement of its own.
    */
    if (!actDoor) {
      sayStatus(NO_ACT_DOOR_LINE);
      return;
    }
    ask(
      actButton,
      sayStatus,
      ASKING_LINE,
      function (settled) {
        region.setAttribute("aria-busy", "true");
        return actDoor({}, settled);
      },
      function (outcome) {
        renderAnswer(outcome, null, actButton);
      }
    );
    if (!waiting) {
      region.removeAttribute("aria-busy");
    }
  });

  renderCards(region, advice, null);
});
}());
