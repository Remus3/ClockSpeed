"""CS-962 slice S5 - the solve bench asks what a target rate costs.

WHAT THIS MODULE GRADES, AND THE GAP IT HAD TO SOLVE FIRST
==========================================================

``panel_solve.js`` is the only panel that does not merely render a payload. It
reads what a person typed, asks ``data.actions.requestSolve`` for a plan, and
writes the answer into nodes it holds by closure. Its whole contract is
therefore what it does with that callback - so an arm that never drives one
would grade nothing at all.

**THE SHARED HARNESS CANNOT DRIVE IT, AND THAT IS NOT A DEFECT IN THE
HARNESS.** ``tests/surface/panel_harness.py`` hands ``data`` across the process
boundary as JSON (its ``request.json``). A JavaScript FUNCTION does not survive
that trip, so no caller of :func:`panel_harness.mount` or
:func:`panel_harness.run` can put a stub ``requestSolve`` on the payload. The
harness is right to stay as it is: the other three panels read payloads and
nothing else, and widening it for one member would put a door on every panel's
test surface.

So this module carries its OWN node driver, :data:`_DRIVER_SOURCE`. It is the
harness's driver plus exactly three things the harness has no business
carrying: a stub ``requestSolve`` that records its calls, a ``fill`` step that
puts a value into an input the way a reader's keyboard would, and a ``settle``
step that invokes a recorded callback later - which is the only way to have a
request be IN FLIGHT while a second click arrives.

**THE STAND-IN IS THE GRADER'S, AND THAT IS MEASURED RATHER THAN CLAIMED.**
The risk of a second driver is that it is WIDER than the real gate - a panel
green here and red in ``test_panel_seam.py``, in an arm this slice does not
own, discovered only after a merge.
:func:`test_the_driver_stand_in_is_exactly_the_shared_harnesses_surface` pins
the measured member lists against :data:`panel_harness.STANDIN_NODE_SURFACE`
and :data:`panel_harness.STANDIN_DOCUMENT_SURFACE`, so a widening is a red arm
here rather than a surprise there. The all-null mount arm additionally goes
through the SHARED harness, so the shipped gate's own path is exercised too.

**THE EXACT RATIONAL IS THE SUBJECT, NOT A DETAIL.** Non-negotiable 6 is exact
rational arithmetic and it does not stop at the browser. Every numeric leaf
``/api/solve`` puts on the wire is a ``num``/``den`` pair (spec section 1.1),
so the bench renders the PAIR, and a decimal may sit beside it only where it is
labelled an approximation for display.

**AND THE PANEL NOW DIVIDES NOWHERE AT ALL.** An earlier draft kept one
quotient to build that label and argued a reading aid may be a float; an
adjudicator rejected it against CS-962's acceptance - no division anywhere in
the render path - and against the unguarded precision loss ``toFixed`` carries.
:func:`test_the_panel_holds_no_division_operator_at_all` measures the claim
structurally, counting division SITES in the code with comments and string
literals blanked;
:func:`test_the_no_division_arm_would_fire_on_a_module_that_divided` proves
that counter can be non-zero on this module's own text, because a detector that
cannot fire grades nothing; and
:func:`test_every_approximation_is_the_exact_truncation_of_its_pair` walks a
table of ratios whose oracle is recomputed per row, because one memorised
constant would pass a single-ratio arm without the arithmetic being right.

**THE FIXTURES ANSWER TO THE SERVER, NOT TO A SPEC DOCUMENT.** Every driving
arm below feeds the panel a payload typed by hand. Section j reconciles those
payloads against ``clockspeed.surface.api.solve`` and
``clockspeed.surface.api.contract`` themselves, so a field this file spelled
wrong - or one the endpoint later renames - is a red arm rather than a page
that renders ``not an exact rational`` forever while the suite stays green.

**THE REGISTRY'S PROVENANCE IS SAID BEFORE THE MACHINES (CS-1315 slice B).**
Section o drives REAL ``/api/solve`` bodies - the shipped handler over the
synthetic solve corpus stamped with one source hash - so the bench is graded on
the ``build_state`` and the audit code the endpoint actually serves: UNVERIFIED
and the code verbatim ahead of the first figure, verified with no code, and a
body with no build state never read as verified.
"""

from __future__ import annotations

import itertools
import json
import re
import shutil
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.audit import build as build_model
from clockspeed.solve import ratio
from clockspeed.surface.api import contract, solve
from tests.advisor.build_fixtures import OFF_PIN_DOCS_SHA256, docs_pin
from tests.surface import panel_harness

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

#: The module this slice owns.
MODULE: Final = "panel_solve.js"

#: The panel id it registers under, and the section id ``app.js`` builds for it.
PANEL_ID: Final = "solve"

#: The four names ``/api/solve`` requires (spec section 1.6, solve.py:143-145).
#: Spelled here rather than imported so a silent rename of the endpoint's own
#: tuple shows up as a red arm rather than as a test that follows it.
SOLVE_PARAMS: Final = ("byproduct_policy", "raw_items", "recipes", "targets")

#: The policy the bench preselects (operator ruling; ratio.py:161-170).
DEFAULT_POLICY: Final = "balanced"

#: The class names ``app.css`` declares for the bench. A panel that invents
#: another gets an unstyled, unsized control.
BENCH_CLASSES: Final = ("bench", "bench-field", "bench-label", "bench-input", "bench-result")

#: The exported name a panel module calls, spelled as a CALL so a prose mention
#: in a comment does not read as one.
REGISTER_CALL: Final = "registerPanel("

#: Every way a browser script reaches the network (test_panel_seam.py:70-77).
#: Duplicated rather than imported: importing from the seam grader would make
#: this module depend on the arm it is trying not to break.
NETWORK_SINKS: Final = (
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "EventSource",
    "WebSocket",
    "import(",
)

#: How many presses the re-entry arms drive.
TWO_PRESSES: Final = 2

#: The three doors :func:`drive` can hand a mount. Named rather than spelled as
#: two booleans, because "door=False, live_door=True" is a state that means
#: nothing and a signature that allows it invites a run nobody can read back.
DOOR_STUB: Final = "stub"
DOOR_NONE: Final = "none"
DOOR_LIVE: Final = "live"

#: The HTTP status a solved plan comes back under.
OK_STATUS: Final = 200

#: The HTTP status a refused solve comes back under.
REFUSED_STATUS: Final = 400

#: Renderings that mean a value reached the page without being read.
NON_RENDERINGS: Final = ("undefined", "[object Object]", "NaN", "null")

#: How long one driver run may take before it is a failure rather than a slow box.
#: A RUN limit: it counts from the start marker, never from the spawn (CS-1329).
NODE_TIMEOUT_SECONDS: Final = 60.0

#: Distinguishes the scratch files of repeated calls sharing one tmp_path.
_RUN_COUNTER: Final[Iterator[int]] = itertools.count()

# ---------------------------------------------------------------------------
# The node driver - the shared harness plus a door, a fill and a settle
# ---------------------------------------------------------------------------

_DRIVER_SOURCE: Final = r""""use strict";

var fs = require("node:fs");
var path = require("node:path");
var vm = require("node:vm");

var request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
var webDir = request.web_dir;

/* Handlers live OUTSIDE the node, so the property surface stays the grader's. */
var listeners = new WeakMap();
var known = Object.create(null);

function makeNode(tag) {
  var node = {
    tagName: String(tag).toUpperCase(),
    className: "",
    id: "",
    hidden: false,
    childNodes: [],
    attributes: Object.create(null),
    scrollWidth: 0,
    clientWidth: 0
  };
  var ownText = "";
  node.appendChild = function (child) {
    node.childNodes.push(child);
    if (child && child.id) {
      known[child.id] = child;
    }
    return child;
  };
  node.removeChild = function (child) {
    var at = node.childNodes.indexOf(child);
    if (at >= 0) {
      node.childNodes.splice(at, 1);
    }
    return child;
  };
  node.setAttribute = function (name, value) {
    node.attributes[name] = String(value);
  };
  node.getAttribute = function (name) {
    return name in node.attributes ? node.attributes[name] : null;
  };
  node.removeAttribute = function (name) {
    delete node.attributes[name];
  };
  node.addEventListener = function (type, handler) {
    if (typeof handler !== "function") {
      return undefined;
    }
    var held = listeners.get(node);
    if (!held) {
      held = [];
      listeners.set(node, held);
    }
    held.push({ type: String(type), handler: handler });
    return undefined;
  };
  Object.defineProperty(node, "firstChild", {
    get: function () {
      return node.childNodes.length ? node.childNodes[0] : null;
    }
  });
  Object.defineProperty(node, "textContent", {
    get: function () {
      if (node.childNodes.length) {
        return node.childNodes
          .map(function (child) {
            return child.textContent;
          })
          .join(" ");
      }
      return ownText;
    },
    set: function (value) {
      node.childNodes.length = 0;
      ownText = String(value);
    }
  });
  return node;
}

function makeText(value) {
  var node = makeNode("#text");
  node.textContent = value;
  return node;
}

var markup = fs.readFileSync(path.join(webDir, "index.html"), "utf8");
var declared = Object.create(null);
var idPattern = /\bid="([^"]+)"/g;
var seenId = idPattern.exec(markup);
while (seenId !== null) {
  declared[seenId[1]] = true;
  seenId = idPattern.exec(markup);
}

function lookup(id) {
  if (known[id]) {
    return known[id];
  }
  if (!declared[id]) {
    return null;
  }
  var node = makeNode("div");
  node.id = id;
  known[id] = node;
  return node;
}

globalThis.document = {
  createElement: makeNode,
  createTextNode: makeText,
  getElementById: lookup,
  querySelectorAll: function () {
    return [];
  },
  activeElement: null
};

globalThis.window = {
  addEventListener: function () {
    return undefined;
  }
};

/*
  A PROMISE THAT NEVER SETTLES, for the reason the shared harness gives: the
  load-time repaint would otherwise overwrite the caller's payload with its
  own. The bench's own request never comes near this - it goes through the
  recording stub installed below, which is the whole point of this driver.

  UNLESS THE RUN ASKED FOR A LIVE DOOR, and then exactly one thing changes:
  liveFetch is raised AFTER app.js has loaded, so the page's own load-time
  probes stay parked on the never-settling promise above and only requests
  issued from a step are answerable. A live-door run is how the SEAM's own
  delivery path is graded rather than a stand-in for it - the recording stub
  below never enters app.js at all, so no arm built on it can say anything
  about what app.js does with an answer that arrives late.
*/
var liveFetch = false;
var fetchCalls = [];
var pendingFetches = [];

globalThis.fetch = function (target, init) {
  if (!liveFetch) {
    return new Promise(function () {
      return undefined;
    });
  }
  fetchCalls.push({
    url: String(target),
    method: init && init.method ? String(init.method) : "GET",
    has_body: Boolean(init && Object.prototype.hasOwnProperty.call(init, "body"))
  });
  return new Promise(function (resolve, reject) {
    pendingFetches.push({ resolve: resolve, reject: reject });
  });
};

/*
  LET EVERY PENDING MICROTASK RUN. Resolving a fetch only queues the
  continuation inside app.js; a step that read the page straight afterwards
  would read it before the answer had been delivered and would pass whatever
  the delivery does. setImmediate is a macrotask, so each turn drains the whole
  microtask queue behind it.
*/
async function drain() {
  for (var turn = 0; turn < 5; turn += 1) {
    await new Promise(function (done) {
      setImmediate(done);
    });
  }
}

function load(file) {
  var source = fs.readFileSync(file, "utf8");
  vm.runInThisContext(source, { filename: path.basename(file) });
}

function describe(failure) {
  if (failure && failure.message) {
    return String(failure.message);
  }
  return String(failure);
}

load(path.join(webDir, "app.js"));

if (typeof registerPanel !== "function" || typeof mountPanel !== "function") {
  throw new Error("app.js published no registerPanel/mountPanel seam");
}
if (typeof mountPanels !== "function" || typeof panelData !== "function") {
  throw new Error("app.js published no mountPanels/panelData seam");
}

/*
  WHAT THE SEAM PUBLISHES WITH NOTHING REGISTERED YET. Read HERE, before the
  module under test loads, because "an empty array rather than absent or null"
  is a claim about exactly this moment and about no later one. panelData has no
  side effects - it reads the probes it is handed and builds an object - so
  asking it costs the run nothing.
*/
var emptySeam = panelData({});
var panelsKeyWhenEmpty = Object.prototype.hasOwnProperty.call(emptySeam, "panels");
var panelsWhenEmpty = panelsKeyWhenEmpty ? emptySeam.panels : null;

var captured = null;
var mountThrew = null;
var realRegister = registerPanel;

globalThis.registerPanel = function (id, mountFn) {
  var wrapped = mountFn;
  if (typeof mountFn === "function") {
    wrapped = function (root, data) {
      try {
        return mountFn(root, data);
      } catch (failure) {
        mountThrew = describe(failure);
        throw failure;
      }
    };
  }
  var accepted = realRegister(id, wrapped);
  if (accepted) {
    captured = { id: id, mount: wrapped };
  }
  return accepted;
};

var loadThrew = null;
try {
  load(request.module);
} catch (failure) {
  loadThrew = describe(failure);
}

/*
  EXTRA PANELS, REGISTERED AFTER THE MODULE UNDER TEST AND THROUGH THE REAL
  REGISTRAR. Registration ORDER is the whole claim data.panels makes, and a
  one-member list cannot show an order at all.
*/
(request.extra_panels || []).forEach(function (id) {
  realRegister(id, function (root) {
    root.appendChild(document.createElement("p"));
  });
});

/* --- the door, recorded --------------------------------------------------- */

var solveCalls = [];
var callbacks = [];
var accepts = request.accepts || [];

function stubRequestSolve(params, onSettled) {
  var at = solveCalls.length;
  var readable = params && typeof params === "object";
  var accepted = at < accepts.length ? Boolean(accepts[at]) : false;
  var record = {
    index: at,
    param_keys: readable ? Object.keys(params).sort() : null,
    params: null,
    types: null,
    callback_is_function: typeof onSettled === "function",
    accepted: accepted
  };
  if (readable) {
    var copy = {};
    var types = {};
    Object.keys(params).forEach(function (name) {
      copy[name] = String(params[name]);
      types[name] = typeof params[name];
    });
    record.params = copy;
    record.types = types;
  }
  solveCalls.push(record);
  callbacks.push(typeof onSettled === "function" ? onSettled : null);
  return accepted;
}

var delivered = [];
var data = request.data;
if (request.live_door) {
  /*
    THE SEAM'S OWN DOOR, AND THE DRIVER LOWERS repainting TO REACH IT. app.js
    refuses a solve while a repaint is in flight, and the load-time repaint is
    parked forever on the never-settling promise above - so without this it
    would refuse every request for a reason that is a property of THIS DRIVER
    and not of the page. Lowered here, once, and reported after every step so
    an arm can see the page's own flags rather than trusting this comment.
  */
  globalThis.repainting = false;
  liveFetch = true;
  data.actions = { requestSolve: requestSolve };
} else if (request.door) {
  data.actions = { requestSolve: stubRequestSolve };
}

/* --- stepping ------------------------------------------------------------- */

function attributesOf(node) {
  var copy = {};
  Object.keys(node.attributes).forEach(function (name) {
    copy[name] = node.attributes[name];
  });
  return copy;
}

function listenTypes(node) {
  var held = listeners.get(node) || [];
  return held.map(function (entry) {
    return entry.type;
  });
}

function section() {
  return captured ? lookup("panel-" + captured.id) : null;
}

function dump(root, collect) {
  var rows = [];
  var next = 0;
  function walk(node, depth, parent) {
    var at = next;
    next += 1;
    if (collect) {
      collect.push(node);
    }
    rows.push({
      index: at,
      depth: depth,
      parent: parent,
      tag: node.tagName,
      id: node.id || "",
      "class": node.className || "",
      attributes: attributesOf(node),
      text: node.textContent,
      listens: listenTypes(node),
      value: typeof node.value === "string" ? node.value : null
    });
    node.childNodes.forEach(function (child) {
      walk(child, depth + 1, at);
    });
  }
  if (root) {
    walk(root, 0, null);
  }
  return rows;
}

function stateOf() {
  var host = section();
  return host ? host.getAttribute("data-panel-state") : null;
}

/*
  THE NODE A hold STEP PINNED, AND WHETHER THE SECTION STILL HOLDS IT.

  This pair is what makes "delivered into a node that is not in the document"
  an observable fact rather than an inference. dump(section()) can only ever
  show what the CURRENT tree holds, so a plan written into a node the seam
  already discarded is invisible to it - the arm would read a clean page and
  call the fault fixed. A hold step keeps the node itself, and the report
  carries both its text and whether it is still reachable from the section.
*/
var heldNode = null;

function containsNode(root, target) {
  if (!root || !target) {
    return false;
  }
  if (root === target) {
    return true;
  }
  for (var index = 0; index < root.childNodes.length; index += 1) {
    if (containsNode(root.childNodes[index], target)) {
      return true;
    }
  }
  return false;
}

function seamState(step) {
  /* The page's own flags and the held node, recorded after one step. */
  step.solving = Boolean(globalThis.asking);
  step.repainting = Boolean(globalThis.repainting);
  step.generation =
    typeof globalThis.panelGeneration === "number" ? globalThis.panelGeneration : null;
  var payloads = globalThis.panelPayloads;
  /*
    null RATHER THAN ABSENT. JSON.stringify drops a key whose value is
    undefined, so a seam that published no roster would leave the report without
    the field at all and an arm reading it would die of a KeyError instead of
    reporting what it measured.
  */
  step.panels =
    payloads && Object.prototype.hasOwnProperty.call(payloads, "panels") ? payloads.panels : null;
  step.held = dump(heldNode, null);
  step.held_in_section = containsNode(section(), heldNode);
  return step;
}

function matches(row, match) {
  var keys = Object.keys(match);
  for (var index = 0; index < keys.length; index += 1) {
    var key = keys[index];
    var want = String(match[key]);
    var got = key === "tag" ? String(row.tag) : String(row[key]);
    if (key === "tag") {
      want = want.toUpperCase();
    }
    if (got !== want) {
      return false;
    }
  }
  return keys.length > 0;
}

function select(match) {
  var nodes = [];
  var rows = dump(section(), nodes);
  var hits = [];
  rows.forEach(function (row) {
    if (matches(row, match)) {
      hits.push(nodes[row.index]);
    }
  });
  return { rows: rows, hits: hits };
}

var steps = [];

async function drive() {
  if (!captured) {
    return;
  }
  mountPanel(captured, data);
  steps.push(
    seamState({
      kind: "mount",
      state: stateOf(),
      threw: mountThrew,
      matched: 1,
      nodes: dump(section(), null)
    })
  );

  for (var at = 0; at < request.steps.length; at += 1) {
    var spec = request.steps[at];
    var step = { kind: null, threw: null, matched: null, state: stateOf() };
    if (spec.fill) {
      step.kind = "fill";
      step.match = spec.fill.match;
      var found = select(spec.fill.match);
      step.matched = found.hits.length;
      if (found.hits.length === 1) {
        found.hits[0].value = String(spec.fill.value);
      }
    } else if (spec.click) {
      step.kind = "click";
      step.match = spec.click;
      var clicked = select(spec.click);
      step.matched = clicked.hits.length;
      step.handlers = 0;
      if (clicked.hits.length === 1) {
        var target = clicked.hits[0];
        var held = (listeners.get(target) || []).filter(function (entry) {
          return entry.type === "click";
        });
        step.handlers = held.length;
        var event = {
          type: "click",
          target: target,
          preventDefault: function () {
            return undefined;
          },
          stopPropagation: function () {
            return undefined;
          }
        };
        held.forEach(function (entry) {
          try {
            entry.handler.call(target, event);
          } catch (failure) {
            step.threw = describe(failure);
          }
        });
      }
    } else if (spec.hold) {
      step.kind = "hold";
      step.match = spec.hold;
      var pinned = select(spec.hold);
      step.matched = pinned.hits.length;
      if (pinned.hits.length === 1) {
        heldNode = pinned.hits[0];
      }
    } else if (spec.remount) {
      /*
        A REPAINT'S OWN REMOUNT, THROUGH THE SHIPPED FUNCTION. mountPanels is
        what refresh() calls, so this is the same door the fault arrived by
        rather than a re-creation of it. The probes are empty because what is
        under test is the teardown and not the payload.
      */
      step.kind = "remount";
      step.matched = 1;
      try {
        mountPanels({});
      } catch (failure) {
        step.threw = describe(failure);
      }
    } else if (spec.ask) {
      /*
        A REQUEST MADE BY THE DRIVER RATHER THAN BY THE BENCH, which is the
        only way to grade an onSettled that THROWS - the panel's own never
        does, and a claim about that exit path needs a caller that can.
      */
      step.kind = "ask";
      step.matched = 1;
      step.tag = String(spec.ask.tag);
      step.accepted = false;
      var thrower = Boolean(spec.ask.throws);
      var tag = String(spec.ask.tag);
      try {
        step.accepted = requestSolve(spec.ask.params, function (outcome) {
          delivered.push({
            tag: tag,
            reached: outcome ? Boolean(outcome.reached) : null,
            http: outcome && typeof outcome.http === "number" ? outcome.http : null
          });
          if (thrower) {
            throw new Error("the caller threw");
          }
        });
      } catch (failure) {
        step.threw = describe(failure);
      }
    } else if (spec.resolve) {
      step.kind = "resolve";
      step.call = spec.resolve.call;
      step.matched = 1;
      var slot = pendingFetches[spec.resolve.call];
      if (!slot) {
        step.matched = 0;
      } else if (spec.resolve.reject) {
        slot.reject(new Error("the connection was refused"));
      } else {
        slot.resolve({
          status: spec.resolve.status,
          json: function () {
            if (spec.resolve.bad_json) {
              return Promise.reject(new Error("the body is not JSON"));
            }
            return Promise.resolve(spec.resolve.body);
          }
        });
      }
      await drain();
    } else {
      step.kind = "settle";
      step.call = spec.settle.call;
      step.matched = 1;
      var settle = callbacks[spec.settle.call];
      if (typeof settle !== "function") {
        step.matched = 0;
      } else {
        try {
          settle(spec.settle.outcome);
        } catch (failure) {
          step.threw = describe(failure);
        }
      }
    }
    step.state = stateOf();
    step.nodes = dump(section(), null);
    steps.push(seamState(step));
  }
}

function report() {
  var last = steps.length ? steps[steps.length - 1] : null;
  return {
    module: path.basename(request.module),
    registered: Boolean(captured),
    panel_id: captured ? captured.id : null,
    load_threw: loadThrew,
    state: stateOf(),
    threw: mountThrew,
    nodes: last ? last.nodes : [],
    steps: steps,
    solve_calls: solveCalls,
    fetch_calls: fetchCalls,
    delivered: delivered,
    solving: Boolean(globalThis.asking),
    repainting: Boolean(globalThis.repainting),
    panels_key_when_empty: panelsKeyWhenEmpty,
    panels_when_empty: panelsWhenEmpty,
    standin_surface: {
      node: Object.getOwnPropertyNames(makeNode("div")).sort(),
      document: Object.keys(globalThis.document).sort()
    }
  };
}

/*
  THE REPORT IS WRITTEN AFTER THE STEPS HAVE FINISHED, AND A THROW INSIDE THEM
  IS STILL FATAL. A driver that swallowed one here would print a report about a
  run that stopped halfway and every arm reading it would grade a truncated
  page as a whole one.
*/
drive().then(
  function () {
    process.stdout.write(JSON.stringify(report()));
  },
  function (failure) {
    process.stderr.write("the stepping loop threw: " + describe(failure));
    process.exitCode = 1;
  }
);
"""


def drive(
    tmp_path: Path,
    data: Mapping[str, Any],
    *,
    module: str | Path = MODULE,
    door: str = DOOR_STUB,
    accepts: Sequence[bool] = (),
    steps: Sequence[Mapping[str, Any]] = (),
    extra_panels: Sequence[str] = (),
    web_dir: Path | None = None,
) -> Mapping[str, Any]:
    """Mount ``panel_solve.js`` with a recording door and drive the given steps.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        data: The six-key payload. Use :func:`panel_harness.null_payload`.
        module: A shipped asset name, or a path to a planted module.
        door: Which ``data.actions.requestSolve`` a mount is handed.
            :data:`DOOR_STUB` installs the recording stub; :data:`DOOR_NONE`
            installs no ``actions`` key at all, which models the seam grader's
            own harness; :data:`DOOR_LIVE` installs ``app.js``'s OWN
            ``requestSolve`` and makes the driver's ``fetch`` answerable from a
            ``resolve`` step. Only the live door grades what the SEAM does with
            an answer, because the stub never enters ``app.js``.
        accepts: What the stub returns for call 0, call 1 and so on. A call
            past the end of this sequence is REFUSED, so an unexpected extra
            call is refused loudly rather than quietly served.
        steps: In order, ``{"fill": {"match": {...}, "value": "..."}}``,
            ``{"click": {...}}``, ``{"hold": {...}}`` (pin the one matching
            node so a later step can read it even once the seam has discarded
            it), ``{"remount": true}`` (call the shipped ``mountPanels``, which
            is what a repaint calls), ``{"ask": {"tag": ..., "params": {...},
            "throws": bool}}`` (ask the seam directly, so an ``onSettled`` that
            throws can be graded), ``{"resolve": {"call": 0, "status": 200,
            "body": {...}}}`` - or ``"reject"`` / ``"bad_json"`` - or
            ``{"settle": {"call": 0, "outcome": {...}}}``.
        extra_panels: Ids registered through the real registrar AFTER the module
            under test, so a registration ORDER has more than one member.
        web_dir: A copy of the web directory to load ``app.js`` from. Used to
            plant a defect back into the SEAM rather than into a panel.

    Returns:
        The report described on :func:`panel_harness.run`, plus ``solve_calls``
        - one record per stub call carrying ``param_keys``, ``params``,
        ``types``, ``callback_is_function`` and ``accepted``. Node rows carry
        an extra ``value``, which is what a reader would have typed. Every step
        additionally carries ``solving``, ``repainting``, ``generation``,
        ``panels``, ``held`` and ``held_in_section``, and the report carries
        ``fetch_calls``, ``delivered``, ``panels_key_when_empty`` and
        ``panels_when_empty``.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so the solve bench was never mounted and "
            "nothing was graded. This FAILS rather than skipping: a gate that "
            "skips its checks reports PASS while measuring nothing."
        )

    root = panel_harness.WEB_DIR if web_dir is None else web_dir
    target = root / module if isinstance(module, str) else module
    if not target.is_file():
        pytest.fail(f"there is no panel module at {target}")

    scratch = tmp_path / f"solve_driver_{next(_RUN_COUNTER)}"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "solve_driver.cjs"
    script.write_bytes(_DRIVER_SOURCE.encode("ascii"))
    request = scratch / "request.json"
    request.write_bytes(
        json.dumps(
            {
                "web_dir": str(root),
                "module": str(target),
                "data": dict(data),
                "door": door == DOOR_STUB,
                "live_door": door == DOOR_LIVE,
                "accepts": list(accepts),
                "steps": [dict(step) for step in steps],
                "extra_panels": list(extra_panels),
            }
        ).encode("ascii")
    )

    # Fixed argv, no shell. The interpreter is resolved off PATH because an
    # absolute interpreter path may not be written into a tracked file.
    completed = panel_harness.run_node(
        node,
        script,
        str(request),
        label=f"the solve driver mounting {target.name}",
        run_timeout=NODE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"the solve driver exited {completed.returncode} mounting "
            f"{target.name}: {completed.stderr.strip()}"
        )

    report: Mapping[str, Any] = json.loads(completed.stdout)
    for step in report["steps"]:
        if step["matched"] != 1:
            pytest.fail(
                f"the {step['kind']} step {step.get('match', step.get('call'))} "
                f"selected {step['matched']} nodes in {target.name}; a step "
                f"must name exactly one. The tree held: "
                f"{[row['tag'] + '#' + row['id'] for row in step['nodes']]}"
            )
    return report


# ---------------------------------------------------------------------------
# Reading the report
# ---------------------------------------------------------------------------


def read_module(name: str = MODULE) -> str:
    """One shipped asset as text, decoded strictly as ASCII.

    Args:
        name: A filename inside the web directory.

    Returns:
        The file's text.
    """
    return (panel_harness.WEB_DIR / name).read_bytes().decode("ascii")


def panel_text(report: Mapping[str, Any]) -> str:
    """Every character the panel's section renders, as one string.

    Args:
        report: A report from :func:`drive` or :func:`panel_harness.mount`.

    Returns:
        The section's joined ``textContent``, or the empty string if nothing
        mounted.
    """
    rows = report["nodes"]
    return str(rows[0]["text"]) if rows else ""


def text_after_kind(report: Mapping[str, Any], kind: str) -> str:
    """The panel's rendered text as it stood after the LAST step of one kind.

    FOUND BY KIND RATHER THAN BY INDEX, because a step list that grows a fill
    shifts every later position - and an index that silently pointed at the
    wrong step would read the page before the moment the arm means to grade.

    Args:
        report: A report from :func:`drive`.
        kind: ``"mount"``, ``"fill"``, ``"click"`` or ``"settle"``.

    Returns:
        The section's joined ``textContent`` after that step.

    Raises:
        ValueError: If the run holds no step of that kind.
    """
    matching = [step for step in report["steps"] if step["kind"] == kind]
    if not matching:
        drove = [step["kind"] for step in report["steps"]]
        raise ValueError(f"the run drove no {kind} step; it drove {drove}")
    rows = matching[-1]["nodes"]
    return str(rows[0]["text"]) if rows else ""


def input_values(report: Mapping[str, Any]) -> dict[str, str]:
    """What every bench input held, keyed by the input's ``name`` attribute.

    Args:
        report: A report from :func:`drive`.

    Returns:
        One entry per ``INPUT`` row carrying a ``name`` attribute.
    """
    found: dict[str, str] = {}
    for row in report["nodes"]:
        if str(row["tag"]) == "INPUT" and "name" in row["attributes"]:
            found[str(row["attributes"]["name"])] = str(row["value"] or "")
    return found


# ---------------------------------------------------------------------------
# The division-site counter, and its own proof
# ---------------------------------------------------------------------------

#: A JavaScript block comment.
_BLOCK_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")

#: A JavaScript string literal, either quoting style, escapes honoured.
_STRING_LITERAL: Final = re.compile(r"\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'")

#: A top-level function declaration.
_FUNCTION_DECL: Final = re.compile(r"^\s*function\s+([A-Za-z_$][\w$]*)\s*\(")


def _blank(match: re.Match[str]) -> str:
    """Replace a match with spaces, keeping its newlines so lines do not move.

    Args:
        match: The span to blank.

    Returns:
        The same length of text with every non-newline replaced by a space.
    """
    return re.sub(r"[^\n]", " ", match.group(0))


def executable_source(text: str) -> str:
    """The script with block comments and string literals blanked in place.

    WHY BOTH, AND WHY BLANKED RATHER THAN REMOVED. A slash is a division
    operator, a comment delimiter and an ordinary character inside a string -
    and ``panel_solve.js`` legitimately holds the last two. Blanking rather
    than deleting keeps every line number, so a surviving slash can be
    attributed to the function it sits in.

    Args:
        text: The script's full text.

    Returns:
        The text with comments and string literals replaced by spaces.
    """
    return _STRING_LITERAL.sub(_blank, _BLOCK_COMMENT.sub(_blank, text))


def division_sites(text: str) -> tuple[tuple[int, str], ...]:
    """Every division operator in the script, as ``(line number, function)``.

    Args:
        text: The script's full text.

    Returns:
        One entry per slash surviving :func:`executable_source`, carrying the
        1-based line number and the name of the nearest function declaration
        at or above it - or the empty string where there is none.
    """
    lines = executable_source(text).split("\n")
    found: list[tuple[int, str]] = []
    enclosing = ""
    for number, line in enumerate(lines, start=1):
        declared = _FUNCTION_DECL.match(line)
        if declared:
            enclosing = declared.group(1)
        found.extend((number, enclosing) for _ in range(line.count("/")))
    return tuple(found)


def test_the_division_counter_sees_an_operator_and_ignores_a_slash_in_text() -> None:
    """The counter is proved on both halves of its job before it is trusted.

    A counter that saw every slash would red-flag the exact pair's own
    separator; a counter that saw none would let a real division through. The
    arm that measures the panel is only as good as this.
    """
    assert division_sites('var mark = "/";') == ()
    assert division_sites("/* a / b */\nvar x = 1;") == ()
    assert division_sites("function only(a, b) {\n  return a / b;\n}") == ((2, "only"),)

    two = division_sites("function pair(a, b) {\n  return a / b + a / b;\n}")
    assert two == ((2, "pair"), (2, "pair")), two

    across = division_sites("function first() {\n  return 1;\n}\nvar q = 4 / 2;")
    assert across == ((4, "first"),), across


# ---------------------------------------------------------------------------
# a. The module is a panel, and it is not a network client
# ---------------------------------------------------------------------------


def test_the_module_registers_the_solve_panel_exactly_once() -> None:
    """One ``registerPanel`` call, under the id the section is built for."""
    code = _BLOCK_COMMENT.sub(" ", read_module())
    calls = code.count(REGISTER_CALL)
    assert calls == 1, f"{MODULE} makes {calls} registration call(s), not 1"
    assert f'"{PANEL_ID}"' in code, f"{MODULE} does not register under {PANEL_ID!r}"


def test_the_panel_names_no_network_primitive() -> None:
    """``app.js`` owns every request; the bench asks it and opens nothing.

    THE BAN COVERS COMMENTS TOO, because the seam grader strips BLOCK comments
    only - a line comment naming a sink would redden an arm this slice does not
    own.
    """
    raw = read_module()
    found = tuple(sink for sink in NETWORK_SINKS if sink in raw)
    assert not found, f"{MODULE} reaches the network: {found}"


def test_the_panel_uses_only_the_class_names_the_sheet_declares() -> None:
    """Every bench class the panel writes is one ``app.css`` sizes.

    The panel slice writes no CSS. A class name invented here would render an
    unstyled, unsized control - which no arm on the stylesheet would catch,
    because the stylesheet would be perfectly consistent with itself.
    """
    sheet = (panel_harness.WEB_DIR / "app.css").read_bytes().decode("ascii")
    missing = tuple(name for name in BENCH_CLASSES if f".{name} " not in sheet)
    assert not missing, f"the sheet declares no rule for: {missing}"

    code = _BLOCK_COMMENT.sub(" ", read_module())
    unused = tuple(name for name in BENCH_CLASSES if f'"{name}"' not in code)
    assert not unused, f"the bench never writes these declared classes: {unused}"


def test_the_panel_declares_no_timer() -> None:
    """No ``setTimeout`` and no ``setInterval``: the page repaints on a press."""
    raw = read_module()
    for banned in ("setTimeout", "setInterval"):
        assert banned not in raw, f"{MODULE} names {banned}"


# ---------------------------------------------------------------------------
# b. The driver is the gate's stand-in, not a wider one
# ---------------------------------------------------------------------------


def test_the_driver_stand_in_is_exactly_the_shared_harnesses_surface(tmp_path: Path) -> None:
    """This module's driver offers a panel no member the real gate withholds.

    A TEST HARNESS MAY BE NARROWER THAN PRODUCTION; IT MUST NEVER BE WIDER
    THAN THE GATE IT FEEDS. If this driver offered, say, ``classList``, a panel
    written against it would be green here and red in
    ``test_panel_seam.py::test_the_seam_mounts_every_registered_panel`` - an
    arm this slice does not own, discovered only after a merge. So the surface
    is MEASURED against the shared harness's pinned lists rather than asserted
    in prose.
    """
    report = drive(tmp_path, panel_harness.null_payload(), door=DOOR_NONE)
    surface = report["standin_surface"]
    assert tuple(surface["node"]) == panel_harness.STANDIN_NODE_SURFACE, surface["node"]
    assert tuple(surface["document"]) == panel_harness.STANDIN_DOCUMENT_SURFACE, surface["document"]


# ---------------------------------------------------------------------------
# c. It mounts against nothing, which is what the seam grader hands it
# ---------------------------------------------------------------------------


def test_the_panel_mounts_against_an_all_null_payload(tmp_path: Path) -> None:
    """Through the SHARED harness, where ``data.actions`` is absent entirely.

    This is the arm that proves the panel survives the gate it does not own:
    ``panel_harness`` passes ``data`` as JSON, so no door can be present, and
    four of the six payload keys are null under the seam grader's canned probes
    anyway.
    """
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["load_threw"] is None, report["load_threw"]
    assert report["registered"] is True
    assert report["panel_id"] == PANEL_ID
    assert report["threw"] is None, report["threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED


def test_the_panel_says_so_when_the_seam_published_no_door(tmp_path: Path) -> None:
    """No ``data.actions`` means the bench cannot ask, and it says which.

    A bench that rendered a button it could never honour would be a control
    that does nothing on a press - the exact fault the refusal arm below exists
    to prevent, wearing a different hat.
    """
    report = drive(tmp_path, panel_harness.null_payload(), door=DOOR_NONE)
    assert report["state"] == panel_harness.STATE_MOUNTED
    after = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_NONE,
        steps=[{"click": {"tag": "button"}}],
    )
    assert after["steps"][1]["threw"] is None, after["steps"][1]["threw"]
    assert after["solve_calls"] == []
    text = panel_text(after).lower()
    assert "cannot" in text or "no solve" in text, panel_text(after)


# ---------------------------------------------------------------------------
# d. The bench itself - empty, vocabulary beside it, policy preselected
# ---------------------------------------------------------------------------


def _registry(**overrides: Any) -> dict[str, Any]:
    """A small synthetic registry payload, hand-authored, never a real slice.

    Args:
        **overrides: Keys to replace on the default payload.

    Returns:
        A registry ``data`` object of the shape spec section 1.2 pins.
    """
    payload: dict[str, Any] = {
        "items": [
            {"key": "Desc_IronRod_C", "display_name": "Iron Rod"},
            {"key": "Desc_IronIngot_C", "display_name": "Iron Ingot"},
            {"key": "Desc_OreIron_C", "display_name": "Iron Ore"},
        ],
        "recipes": [
            {"key": "Recipe_IronRod_C", "display_name": "Iron Rod"},
            {"key": "Recipe_IngotIron_C", "display_name": "Iron Ingot"},
        ],
        "buildings": [],
        "counts": {"items": 3, "recipes": 2, "buildings": 0, "warnings": 0, "unknown_groups": 0},
        "warnings": [],
        "unknown_groups": [],
    }
    payload.update(overrides)
    return payload


def test_the_bench_offers_the_four_fields_and_starts_empty(tmp_path: Path) -> None:
    """Four labelled inputs, one per required parameter, none prefilled.

    THE BENCH STARTS EMPTY rather than carrying a game identifier - merger's
    ruling. The vocabulary is listed BESIDE the field instead, so a first-time
    reader still knows what a legal value looks like.
    """
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    values = input_values(report)
    assert tuple(sorted(values)) == SOLVE_PARAMS, values
    for name in ("targets", "recipes", "raw_items"):
        assert values[name] == "", f"{name} arrived prefilled with {values[name]!r}"

    labels = panel_harness.nodes_matching(report, {"class": "bench-label"})
    assert len(labels) == len(SOLVE_PARAMS), [row["text"] for row in labels]
    assert tuple(sorted(str(row["text"]) for row in labels)) == SOLVE_PARAMS


def test_the_policy_field_is_preselected_balanced_and_stays_editable(tmp_path: Path) -> None:
    """``byproduct_policy`` is an editable input carrying ``balanced``.

    OPERATOR RULING. The page makes the modelling choice visibly rather than
    making the player answer it before their first result - so it is neither
    hidden nor hardcoded out of reach.
    """
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    values = input_values(report)
    assert values["byproduct_policy"] == DEFAULT_POLICY, values

    policy = panel_harness.nodes_matching(report, {"id": "solve-byproduct_policy"})
    assert len(policy) == 1, [row["id"] for row in report["nodes"]]
    assert str(policy[0]["tag"]) == "INPUT"
    assert policy[0]["attributes"].get("type") == "text", policy[0]["attributes"]

    typed = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=[
            {"fill": {"match": {"id": "solve-byproduct_policy"}, "value": "sinkable"}},
            {"fill": {"match": {"id": "solve-targets"}, "value": "Desc_IronRod_C=50"}},
            {"click": {"tag": "button"}},
        ],
    )
    assert typed["solve_calls"][0]["params"]["byproduct_policy"] == "sinkable"


def test_the_bench_lists_the_accepted_vocabulary_beside_each_field(tmp_path: Path) -> None:
    """Item keys beside the item fields, recipe keys beside the recipe field."""
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    text = panel_text(report)
    for key in ("Desc_IronRod_C", "Desc_OreIron_C", "Recipe_IronRod_C"):
        assert key in text, f"{key} is not listed anywhere beside a field"
    assert "sinkable" in text, "the policy field does not name its second value"


def test_the_bench_survives_a_registry_that_did_not_answer(tmp_path: Path) -> None:
    """With ``data.registry`` null the fields still mount and say what is missing."""
    report = drive(tmp_path, panel_harness.null_payload())
    assert report["state"] == panel_harness.STATE_MOUNTED
    assert tuple(sorted(input_values(report))) == SOLVE_PARAMS
    assert "registry" in panel_text(report).lower()


# ---------------------------------------------------------------------------
# e. The door - asked once, with exactly four string parameters
# ---------------------------------------------------------------------------


def _filled(**values: str) -> list[dict[str, Any]]:
    """Fill steps for the named fields, in a stable order.

    Args:
        **values: Field name to the value a reader typed.

    Returns:
        One fill step per named field.
    """
    return [
        {"fill": {"match": {"id": f"solve-{name}"}, "value": values[name]}}
        for name in sorted(values)
    ]


def test_a_press_asks_the_door_once_with_exactly_the_four_parameters(tmp_path: Path) -> None:
    """One call, four string keys, and the values the reader typed.

    A FIFTH KEY OR A MISSING ONE IS REFUSED BY ``app.js`` OUTRIGHT (its
    ``solveQuery``), so a bench that assembled the wrong object would get a
    false return and never a result. This arm reads the object the door was
    actually handed rather than the request that would have gone out.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=[
            *_filled(
                targets="Desc_IronRod_C=50",
                recipes="Recipe_IronRod_C",
                raw_items="Desc_OreIron_C",
            ),
            {"click": {"tag": "button"}},
        ],
    )
    assert len(report["solve_calls"]) == 1, report["solve_calls"]
    call = report["solve_calls"][0]
    assert tuple(call["param_keys"]) == SOLVE_PARAMS, call["param_keys"]
    assert set(call["types"].values()) == {"string"}, call["types"]
    assert call["callback_is_function"] is True
    assert call["params"] == {
        "targets": "Desc_IronRod_C=50",
        "recipes": "Recipe_IronRod_C",
        "raw_items": "Desc_OreIron_C",
        "byproduct_policy": DEFAULT_POLICY,
    }, call["params"]


def test_the_button_is_the_only_thing_carrying_a_click_listener(tmp_path: Path) -> None:
    """One control, and it is a ``button``: the only target the sheet sizes."""
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    listening = tuple(row for row in report["nodes"] if "click" in row["listens"])
    assert len(listening) == 1, [row["tag"] for row in listening]
    assert str(listening[0]["tag"]) == "BUTTON"


def test_the_panel_builds_no_form_element(tmp_path: Path) -> None:
    """CSP is ``form-action none``; the bench is inputs plus a button."""
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    forms = tuple(row for row in report["nodes"] if str(row["tag"]) == "FORM")
    assert not forms, forms
    assert "<form" not in read_module()


# ---------------------------------------------------------------------------
# f. A settled 200 - every rational as its exact pair
# ---------------------------------------------------------------------------

#: The success envelope ``/api/solve`` puts on the wire (spec section 1.6).
PLAN_OUTCOME: Final = {
    "reached": True,
    "http": 200,
    "body": {
        "status": "ok",
        "endpoint": "/api/solve",
        "data": {
            "steps": [{"recipe_key": "Recipe_IronRod_C", "machines": {"num": 10, "den": 3}}],
            "targets": {"Desc_IronRod_C": {"num": 50, "den": 1}},
            "raw_inputs": {"Desc_OreIron_C": {"num": 100, "den": 7}},
            "byproducts": {"Desc_Water_C": {"num": 0, "den": 1}},
            "excluded": [{"recipe_key": "Recipe_Alt_C", "reason": "zero-duration"}],
            "byproduct_policy": "balanced",
        },
    },
}

#: The refusal envelope, whose reason and detail live OUTSIDE ``data``.
REFUSAL_OUTCOME: Final = {
    "reached": True,
    "http": 400,
    "body": {
        "status": "error",
        "endpoint": "/api/solve",
        "reason": "chain_underdetermined",
        "detail": "more than one recipe chain reaches the target",
        "blocked_by": None,
    },
}


def _envelope(outcome: Mapping[str, Any]) -> dict[str, Any]:
    """The response envelope out of one canned outcome, as a fresh mapping.

    Read through a narrowing check rather than indexed straight into a driver
    step, because the outcome tables are inferred as mappings of ``object`` and
    a step spelling has to hand the driver a real mapping.

    Args:
        outcome: :data:`PLAN_OUTCOME` or :data:`REFUSAL_OUTCOME`.

    Returns:
        A copy of that outcome's ``body``.
    """
    body = outcome["body"]
    assert isinstance(body, Mapping), body
    return dict(body)


def _settled(outcome: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A filled, pressed and settled run, as steps.

    Args:
        outcome: What the door hands the panel's callback.

    Returns:
        The fill, click and settle steps in order.
    """
    return [
        *_filled(
            targets="Desc_IronRod_C=50",
            recipes="Recipe_IronRod_C",
            raw_items="Desc_OreIron_C",
        ),
        {"click": {"tag": "button"}},
        {"settle": {"call": 0, "outcome": dict(outcome)}},
    ]


def test_a_settled_plan_renders_every_rational_as_its_exact_pair(tmp_path: Path) -> None:
    """Machines, targets, raw inputs and byproducts, each as ``num/den``.

    NON-NEGOTIABLE 6 DOES NOT STOP AT THE BROWSER. The wire carries two
    integers per numeric leaf (spec section 1.1) and the page renders both. A
    rounded decimal is allowed beside the pair and never instead of it.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    text = panel_text(report)
    for pair in ("10/3", "50/1", "100/7", "0/1"):
        assert pair in text, f"the exact pair {pair} is not rendered: {text}"
    assert "Recipe_IronRod_C" in text
    assert "Desc_OreIron_C" in text
    assert "Recipe_Alt_C" in text
    assert "zero-duration" in text
    assert "balanced" in text


def test_the_decimal_is_rendered_only_beside_the_pair_and_marked_approximate(
    tmp_path: Path,
) -> None:
    """``10/3`` carries ``3.3333`` next to it, under a word saying approximate.

    THE FLOAT NEVER ENTERS A DECISION PATH; it is a reading aid and is labelled
    as one. A decimal standing alone is refused outright - see the planted arm
    below, which proves this one is load-bearing rather than decorative.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    text = panel_text(report)
    assert "10/3" in text, text
    assert "3.3333" in text, text
    assert "approx" in text.lower(), text

    decimals = re.findall(r"\d+\.\d+", text)
    assert decimals, text
    unlabelled = tuple(value for value in decimals if f"approx {value}" not in text)
    assert not unlabelled, f"decimals rendered without the approximate label: {unlabelled}"


def test_a_plant_that_renders_the_decimal_alone_goes_red(tmp_path: Path) -> None:
    """The exact-pair arm is proved load-bearing rather than assumed to be.

    A TEST THAT HAS NEVER BEEN RED PROVES NOTHING. This plants the mutation the
    operator ruling exists to forbid - the pair separator dropped, so only the
    approximation survives - and asserts the arm above would have caught it.
    """
    source = read_module()
    mark = 'var PAIR_MARK = "/";'
    assert mark in source, "the pair separator is not spelled where this plant expects it"
    planted = tmp_path / "panel_solve_decimal_only.js"
    planted.write_bytes(source.replace(mark, 'var PAIR_MARK = "";').encode("ascii"))

    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        module=planted,
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    text = panel_text(report)
    assert "3.3333" in text, f"the plant did not even render: {text}"
    assert "10/3" not in text, f"the plant was expected to drop the pair: {text}"


def test_a_settled_plan_renders_nothing_that_reads_as_a_missing_value(
    tmp_path: Path,
) -> None:
    """No ``undefined``, no ``[object Object]``, no bare ``NaN`` on the page."""
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    text = panel_text(report)
    found = tuple(marker for marker in NON_RENDERINGS if marker in text)
    assert not found, f"{found} reached the page: {text}"


# ---------------------------------------------------------------------------
# g. A settled refusal - reason and detail live outside data
# ---------------------------------------------------------------------------


def test_a_settled_refusal_renders_its_reason_and_its_detail(tmp_path: Path) -> None:
    """A 400 body carries no ``data``; the bench reads the envelope instead.

    THIS IS WHY THE SEAM HANDS BACK THE FULL ENVELOPE rather than ``bodyData``:
    a bench that could only see ``data`` would render every refusal as silence.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(REFUSAL_OUTCOME),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    text = panel_text(report)
    assert "chain_underdetermined" in text, text
    assert "more than one recipe chain reaches the target" in text, text
    assert "400" in text, text
    found = tuple(marker for marker in NON_RENDERINGS if marker in text)
    assert not found, f"{found} reached the page: {text}"


def test_an_unreached_request_says_so_rather_than_rendering_a_blank(
    tmp_path: Path,
) -> None:
    """``reached`` false carries no status and no body, and is still readable."""
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled({"reached": False, "http": None, "body": None}),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    text = panel_text(report)
    assert "did not reach" in text.lower(), text
    found = tuple(marker for marker in NON_RENDERINGS if marker in text)
    assert not found, f"{found} reached the page: {text}"


# ---------------------------------------------------------------------------
# h. Refusal and re-entry - a press must never look like it did nothing
# ---------------------------------------------------------------------------


def test_a_refused_request_is_shown_and_leaves_no_stale_result(tmp_path: Path) -> None:
    """A false return means the callback NEVER fires, so the panel must speak.

    ``requestSolve`` refuses while a repaint is in flight, while another solve
    is in flight, and on bad parameters. Nothing arrives afterwards. A bench
    that only wrote on settle would answer that press with a page that did not
    change - indistinguishable from a dead button.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True, False],
        steps=[
            *_filled(
                targets="Desc_IronRod_C=50",
                recipes="Recipe_IronRod_C",
                raw_items="Desc_OreIron_C",
            ),
            {"click": {"tag": "button"}},
            {"settle": {"call": 0, "outcome": dict(PLAN_OUTCOME)}},
            {"click": {"tag": "button"}},
        ],
    )
    assert len(report["solve_calls"]) == TWO_PRESSES, report["solve_calls"]
    assert report["solve_calls"][1]["accepted"] is False

    settled = text_after_kind(report, "settle")
    assert "10/3" in settled, settled

    after = panel_text(report)
    assert "refus" in after.lower(), after
    assert "10/3" not in after, f"a stale result survived the refusal: {after}"


def test_a_second_press_while_one_is_in_flight_asks_the_door_only_once(
    tmp_path: Path,
) -> None:
    """The bench holds its own in-flight flag rather than leaning on the seam.

    ``requestSolve`` would refuse the second call anyway - but a bench that
    relied on that would spend a press learning something it already knew, and
    would show the reader a refusal where the truthful answer is "the one you
    asked for is still running".
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=[
            *_filled(
                targets="Desc_IronRod_C=50",
                recipes="Recipe_IronRod_C",
                raw_items="Desc_OreIron_C",
            ),
            {"click": {"tag": "button"}},
            {"click": {"tag": "button"}},
        ],
    )
    assert len(report["solve_calls"]) == 1, report["solve_calls"]
    text = panel_text(report)
    assert "already" in text.lower(), text


def test_a_press_after_a_settle_asks_again(tmp_path: Path) -> None:
    """The in-flight flag is released on settle, so the bench is reusable.

    A FLAG RAISED AND NEVER LOWERED IS A DEAD BENCH, recoverable only by a
    reload - the fault ``app.js`` documents on its own flag's ``finally``.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True, True],
        steps=[
            *_filled(
                targets="Desc_IronRod_C=50",
                recipes="Recipe_IronRod_C",
                raw_items="Desc_OreIron_C",
            ),
            {"click": {"tag": "button"}},
            {"settle": {"call": 0, "outcome": dict(PLAN_OUTCOME)}},
            {"click": {"tag": "button"}},
        ],
    )
    assert len(report["solve_calls"]) == TWO_PRESSES, report["solve_calls"]
    assert report["solve_calls"][1]["accepted"] is True


def test_the_bench_says_something_before_the_first_press(tmp_path: Path) -> None:
    """The result region is never an empty box with no explanation."""
    report = drive(tmp_path, panel_harness.null_payload(registry=_registry()))
    results = panel_harness.nodes_matching(report, {"class": "bench-result"})
    assert len(results) == 1, [row["class"] for row in report["nodes"]]
    assert str(results[0]["text"]).strip(), "the result region mounted empty"


# ---------------------------------------------------------------------------
# i. The arithmetic discipline, measured structurally
# ---------------------------------------------------------------------------


def test_the_panel_holds_no_division_operator_at_all(tmp_path: Path) -> None:
    """Zero division sites in the whole module, label builder included.

    NON-NEGOTIABLE 6, ENFORCED IN THE RENDER PATH, AND CS-962'S ACCEPTANCE
    TAKEN LITERALLY. An earlier draft kept one quotient in
    ``approximateDecimal`` and argued a reading aid may be a float. That
    argument was adjudicated and rejected: the decimal is reached by repeated
    subtraction now, so there is no place in this file where a float is made.

    The count alone would pass on a module that rendered nothing, so the panel
    is driven here too - a zero that comes with a rendered decimal beside a
    rendered pair is a zero about live code.
    """
    sites = division_sites(read_module())
    assert sites == (), f"{len(sites)} division site(s) survive: {sites}"

    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    text = panel_text(report)
    assert "10/3" in text, text
    assert "3.3333" in text, text


def test_the_no_division_arm_would_fire_on_a_module_that_divided(tmp_path: Path) -> None:
    """The zero above is proved capable of being non-zero, on THIS module's text.

    A DETECTOR THAT CANNOT FIRE GRADES NOTHING, and this repo has measured a
    gate that skipped its own checks and still reported PASS. The synthetic
    strings in the counter's own arm prove the regex; this proves the whole
    pipeline end to end on the real file - a quotient put back into
    ``approximateDecimal`` is seen, attributed to that function, and the
    planted module still mounts and renders, so what is being seen is live
    code rather than a dead line.
    """
    source = read_module()
    subtraction = "      remainder -= divisor;"
    assert subtraction in source, "the long division is not spelled where this plant expects it"

    quotient = "  var quotientPlant = num / den;\n  void quotientPlant;\n"
    anchor = "  var negative = num < 0 !== den < 0;\n"
    assert anchor in source, "the plant anchor moved"
    mutated = source.replace(anchor, quotient + anchor)
    assert mutated != source, "the plant did not apply"

    planted = tmp_path / "panel_solve_divides.js"
    planted.write_bytes(mutated.encode("ascii"))

    sites = division_sites(mutated)
    assert len(sites) == 1, f"the detector did not fire on a module that divides: {sites}"
    assert sites[0][1] == "approximateDecimal", sites[0]

    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        module=planted,
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    assert "3.3333" in panel_text(report), panel_text(report)


#: Ratios the truncation arm walks, chosen so a rounding implementation parts
#: company with a truncating one. ``22/7`` and ``2/3`` both round UP at the
#: fourth place, so the ``toFixed`` spelling this repair removed would render
#: ``3.1429`` and ``0.6667`` and go red here.
#:
#: CS-1028: THIS TABLE AND :func:`truncated_decimal` ARE THE ONE DIGIT ORACLE
#: for every panel copy of ``approximateDecimal``. ``tests/surface/
#: test_panel_optimize.py`` and ``tests/surface/test_panel_power.py`` import both
#: rather than restating them, so a case added here grades every copy.
#:
#: THE TWO NEGATIVE ROWS carry the sign on either integer. No shipped endpoint
#: was measured putting a negative leaf on the wire, and none was proved unable
#: to - ``solve.RATIONAL_PATTERN`` admits a leading minus - so the sign branch of
#: every copy is graded rather than left to a path nobody has walked. A copy
#: that dropped the minus rendered every other row correctly and passed this
#: table without them.
TRUNCATION_CASES: Final = (
    (1, 8),
    (100, 7),
    (10, 3),
    (22, 7),
    (2, 3),
    (7, 1),
    (0, 1),
    (-22, 7),
    (5, -8),
)

#: Places the panel's approximation carries (panel_solve.js APPROX_PLACES).
APPROX_PLACES: Final = 4


def truncated_decimal(num: int, den: int) -> str:
    """The exact truncation of ``num/den`` toward zero, to :data:`APPROX_PLACES` places.

    Computed with integer arithmetic only. A float here would make the oracle
    share the defect it exists to catch. The magnitude is truncated and the sign
    is prefixed when the two integers' signs differ, which is the panels' own
    rule - floor division on a negative ratio would round AWAY from zero.

    Args:
        num: The numerator.
        den: The denominator, non-zero.

    Returns:
        The truncated decimal, always carrying every place.
    """
    scale = 10**APPROX_PLACES
    whole, fraction = divmod(abs(num) * scale // abs(den), scale)
    sign = "-" if (num < 0) != (den < 0) else ""
    return f"{sign}{whole}.{fraction:0{APPROX_PLACES}d}"


def test_every_approximation_is_the_exact_truncation_of_its_pair(tmp_path: Path) -> None:
    """A table of ratios, each rendered as its pair and its exact truncation.

    ONE HARDCODED CONSTANT PASSING ONE CASE IS AN EQUIVALENT MUTANT - a module
    that answered ``3.3333`` to everything would satisfy the single-ratio arm
    above. The oracle is recomputed per row from the two integers, so the
    arithmetic is graded rather than one memorised answer.
    """
    outcome = json.loads(json.dumps(PLAN_OUTCOME))
    outcome["body"]["data"]["targets"] = {
        f"Desc_Case{index}_C": {"num": num, "den": den}
        for index, (num, den) in enumerate(TRUNCATION_CASES)
    }
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(outcome),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    text = panel_text(report)
    for num, den in TRUNCATION_CASES:
        rendered = f"{num}/{den} (approx {truncated_decimal(num, den)}, display only)"
        assert rendered in text, f"expected {rendered!r} on the page: {text}"


def test_a_denominator_past_the_safe_bound_yields_the_pair_and_no_decimal(
    tmp_path: Path,
) -> None:
    """The precision guard the adjudicator found missing, measured on both sides.

    ``toFixed`` had no bound at all: it would have answered a confident
    ``0.0000`` for the first row below and an ``Infinity`` for the second had
    the zero check not caught it. The long division declares the largest
    denominator it stays exact for and answers nothing past it, so the reader
    gets the exact pair alone rather than a decimal nobody checked.
    """
    outcome = json.loads(json.dumps(PLAN_OUTCOME))
    plan = outcome["body"]["data"]
    plan["targets"] = {
        "Desc_TooBig_C": {"num": 1, "den": 900000000000001},
        "Desc_ZeroDen_C": {"num": 5, "den": 0},
    }
    # Every other rational leaf is emptied, so a decimal found below can only
    # have come from one of the two rows this arm is about.
    plan["steps"] = []
    plan["raw_inputs"] = {}
    plan["byproducts"] = {}
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(outcome),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    text = panel_text(report)
    assert "1/900000000000001" in text, text
    assert "5/0" in text, text
    assert "Infinity" not in text, text
    decimals = re.findall(r"\d+\.\d+", text)
    assert not decimals, f"a decimal was rendered for an unsafe pair: {decimals} in {text}"


def test_a_rational_the_wire_should_never_carry_is_rendered_as_text(
    tmp_path: Path,
) -> None:
    """A malformed leaf is named, not turned into a float or an exception.

    ``contract.encode`` refuses a float on the wire, so this shape cannot come
    from the shipped endpoint. It can come from a proxy, a stale build or a
    hand-typed URL, and non-negotiable 7 says unknown content is flagged and
    skipped rather than fatal.
    """
    broken = json.loads(json.dumps(PLAN_OUTCOME))
    broken["body"]["data"]["steps"][0]["machines"] = {"num": 1.5, "den": None}
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(broken),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    assert report["state"] == panel_harness.STATE_MOUNTED
    text = panel_text(report)
    found = tuple(marker for marker in NON_RENDERINGS if marker in text)
    assert not found, f"{found} reached the page: {text}"
    assert "1.5" not in text, f"a float was rendered as a value: {text}"


# ---------------------------------------------------------------------------
# j. The fixtures answer to the server, not to a spec document
# ---------------------------------------------------------------------------


def _real_plan_data() -> Mapping[str, Any]:
    """The ``data`` object the SHIPPED endpoint builds for a solved plan.

    WHY THE PRIVATE SERIALIZER AND NOT THE ROUTE. ``solve._plan_data`` is the
    one place the wire names are written down; the route only wraps what it
    returns in an envelope. Driving the route instead would need a whole
    registry and a real solve, and would grade the solver rather than the
    names. A leading underscore is a caller-discipline marker, and the caller
    here is the test that exists to notice when those names move.

    Returns:
        The serialized plan, keys as the server publishes them.
    """
    plan = ratio.ProductionPlan(
        steps=(ratio.PlanStep(recipe_key="Recipe_IronRod_C", machines=Fraction(10, 3)),),
        targets={"Desc_IronRod_C": Fraction(50, 1)},
        raw_inputs={"Desc_OreIron_C": Fraction(100, 7)},
        byproducts={"Desc_Water_C": Fraction(0, 1)},
        excluded=(ratio.ExclusionNote(recipe_key="Recipe_Alt_C", reason="zero-duration"),),
        byproduct_policy="balanced",
    )
    return solve._plan_data(plan)  # noqa: SLF001


def test_the_plan_fixture_carries_exactly_the_keys_the_server_publishes() -> None:
    """The hand-typed success fixture is reconciled against the real serializer.

    THE COMMON-MODE HOLE THIS CLOSES. Every other arm in this module drives a
    payload this file typed from a spec document. If a name in that document
    were wrong, or the endpoint renamed a field, every one of those arms would
    stay green while the live page rendered ``not an exact rational`` or a
    silent blank forever - degradation with no red test anywhere. Nothing here
    trusts the spec or the fixture: the envelope key sets come from
    ``contract``, the parameter names from ``solve.SOLVE_REQUIRED``, and the
    data names from the serializer that actually runs in the server.
    """
    body = PLAN_OUTCOME["body"]
    assert isinstance(body, Mapping)
    assert set(body) == set(contract.PAYLOAD_KEYS_OK), set(body)
    assert body["status"] == contract.STATUS_OK
    assert body["endpoint"] == solve.SOLVE_ENDPOINT

    published = _real_plan_data()
    fixture = body["data"]
    assert isinstance(fixture, Mapping)
    assert set(fixture) == set(published), (set(fixture), set(published))

    step_names = {name for row in published["steps"] for name in row}
    assert set(fixture["steps"][0]) == step_names, set(fixture["steps"][0])

    note_names = {name for row in published["excluded"] for name in row}
    assert set(fixture["excluded"][0]) == note_names, set(fixture["excluded"][0])

    leaf = set(contract.rational(Fraction(10, 3)))
    for pair in (
        fixture["steps"][0]["machines"],
        fixture["targets"]["Desc_IronRod_C"],
        fixture["raw_inputs"]["Desc_OreIron_C"],
        fixture["byproducts"]["Desc_Water_C"],
    ):
        assert set(pair) == leaf, set(pair)


def test_the_refusal_fixture_carries_exactly_the_keys_the_server_publishes() -> None:
    """The hand-typed 400 fixture is reconciled against the contract layer.

    A refusal body carries no ``data`` at all - its reason and detail sit
    beside it - which is the shape the render arm above depends on. If that
    shape moved, the bench would render every refusal as silence and no arm
    here would notice.
    """
    body = REFUSAL_OUTCOME["body"]
    assert isinstance(body, Mapping)
    assert set(body) == set(contract.PAYLOAD_KEYS_REFUSAL), set(body)
    assert body["endpoint"] == solve.SOLVE_ENDPOINT
    assert body["status"] != contract.STATUS_OK


def test_the_benchs_four_parameters_are_the_four_the_endpoint_requires() -> None:
    """``SOLVE_PARAMS`` is reconciled against the endpoint's own frozenset.

    The constant stays spelled out above so a rename shows up HERE as one red
    arm naming both sides, rather than as a module that silently follows the
    endpoint wherever it goes.

    THE BENCH SENDS THE REQUIRED SET AND DELIBERATELY NONE OF THE OPTIONAL ONE,
    which is a statement about the bench rather than about the endpoint. This
    arm used to read ``assert not solve.SOLVE_OPTIONAL`` - a claim that the door
    accepted nothing beyond the four - and that claim stopped being about the
    bench the moment the door grew a second direction. ``mode`` is optional
    there and defaults to ``targets``, so the bench asks the forward question by
    sending nothing; asserting the SET rather than its emptiness keeps the same
    fence - a fifth name reaching the door still goes red here - while letting
    the door say what it actually accepts.
    """
    assert set(SOLVE_PARAMS) == set(solve.SOLVE_REQUIRED), (
        set(SOLVE_PARAMS),
        set(solve.SOLVE_REQUIRED),
    )
    assert set(solve.SOLVE_OPTIONAL) == {solve.PARAM_MODE}, solve.SOLVE_OPTIONAL
    assert solve.PARAM_MODE not in SOLVE_PARAMS, SOLVE_PARAMS


def test_the_panel_module_spells_the_four_parameters_the_endpoint_requires() -> None:
    """The JavaScript itself names each required parameter, not just the test.

    The arm above reconciles two Python objects. This one reaches into the
    shipped panel, so a rename that got past both would still be caught before
    it reached a reader as a refused request.
    """
    source = read_module()
    for name in sorted(solve.SOLVE_REQUIRED):
        assert f'name: "{name}"' in source, f"the bench declares no {name} field"


# ---------------------------------------------------------------------------
# l. A SUPERSEDED SOLVE. The answer must never be written into a dead node
# ---------------------------------------------------------------------------

#: The four values an ``ask`` step hands the seam. Any four strings will do -
#: what is under test is the delivery, not the query - but they have to be
#: exactly the four names or ``requestSolve`` refuses before a fetch is made.
_ASK_PARAMS: Final = {
    "targets": "Desc_IronPlate_C=10",
    "recipes": "Recipe_IronPlate_C",
    "raw_items": "Desc_OreIron_C",
    "byproduct_policy": DEFAULT_POLICY,
}

#: A bench filled and pressed, with the result region pinned before a repaint.
#: ``hold`` comes AFTER the press so the node it pins is the one carrying the
#: "asking ..." line, which is the node the answer would land in.
_IN_FLIGHT_STEPS: Final = (
    {"fill": {"match": {"id": "solve-targets"}, "value": "Desc_IronPlate_C=10"}},
    {"click": {"tag": "button"}},
    {"hold": {"class": "bench-result"}},
)


def _seam_copy(tmp_path: Path, *, plant: tuple[str, str] | None = None) -> Path:
    """A copy of the whole web directory, optionally with ``app.js`` mutated.

    THE PLANT GOES INTO THE SEAM, NOT INTO A PANEL, because the guard under test
    lives in ``app.js``. Every other asset is copied verbatim so the copy is the
    shipped page in every respect but the one being measured.

    Args:
        tmp_path: A directory the copy may live under.
        plant: ``(before, after)``, an exact substitution applied to ``app.js``.
            ``None`` copies it unchanged, which is the control.

    Returns:
        The copied web directory.
    """
    into = tmp_path / f"web_{next(_RUN_COUNTER)}"
    shutil.copytree(panel_harness.WEB_DIR, into)
    if plant is not None:
        before, after = plant
        source = (into / "app.js").read_bytes().decode("ascii")
        # A MUTANT THAT NEVER APPLIED LOOKS EXACTLY LIKE A SURVIVING ONE, so the
        # substitution is counted rather than attempted.
        assert source.count(before) == 1, (
            f"the plant anchor is not in app.js exactly once: {source.count(before)}"
        )
        (into / "app.js").write_bytes(source.replace(before, after).encode("ascii"))
    return into


def _held_text(report: Mapping[str, Any], kind: str) -> str:
    """Every character the PINNED node held after the last step of one kind.

    Args:
        report: A report from :func:`drive`.
        kind: The step kind to read after.

    Returns:
        The pinned node's joined ``textContent``, or the empty string if no node
        was pinned.

    Raises:
        ValueError: If the run holds no step of that kind.
    """
    matching = [step for step in report["steps"] if step["kind"] == kind]
    if not matching:
        drove = [step["kind"] for step in report["steps"]]
        raise ValueError(f"the run drove no {kind} step; it drove {drove}")
    rows = matching[-1]["held"]
    return str(rows[0]["text"]) if rows else ""


def _superseded_run(tmp_path: Path, *, web_dir: Path) -> Mapping[str, Any]:
    """Press Solve, repaint, then answer the request that the repaint outran.

    THE INTERLEAVING IS THE SUBJECT. A ``resolve`` after a ``remount`` is
    exactly the sequence a reader produces by pressing Solve and then Refresh
    before the answer lands.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        web_dir: The web directory to load the seam from.

    Returns:
        The driver report.
    """
    return drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        door=DOOR_LIVE,
        web_dir=web_dir,
        steps=[
            *_IN_FLIGHT_STEPS,
            {"remount": True},
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
        ],
    )


def test_a_press_through_the_live_door_issues_one_post_and_is_answered(
    tmp_path: Path,
) -> None:
    """The KNOWN-GOOD CONTROL for this whole section.

    With no repaint interleaved, the same steps deliver: one POST to
    ``/api/solve`` carrying no body, and the plan rendered where the reader is
    looking. Without this, "the answer did not arrive" would be satisfied by a
    driver that never asked for one.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        door=DOOR_LIVE,
        steps=[
            *_IN_FLIGHT_STEPS,
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
        ],
    )
    calls = report["fetch_calls"]
    assert len(calls) == 1, calls
    assert calls[0]["method"] == "POST", calls[0]
    assert calls[0]["url"].startswith("/api/solve?"), calls[0]
    assert calls[0]["has_body"] is False, calls[0]

    text = text_after_kind(report, "resolve")
    assert "solved" in text, text
    assert "10/3" in text, text
    assert report["solving"] is False, "the seam left its solve flag raised"


def test_a_superseded_solve_is_never_rendered_into_a_dead_node(tmp_path: Path) -> None:
    """Press Solve, press Refresh, then let the answer land. It lands nowhere.

    THE FAULT THIS ARM EXISTS FOR. ``waiting`` is per-mount closure state inside
    the panel and the seam's own flag is per-page, so a repaint between the
    request and its delivery used to destroy the bench, build a fresh one saying
    no solve had been asked for, and then write the plan into the RESULT NODE OF
    THE BENCH THAT NO LONGER EXISTS. The reader's answer was computed, returned
    and rendered into nothing, with no message and no error.

    IT IS GRADED ON THE PINNED NODE AND NOT ON THE SECTION, because a plan
    written into a discarded node is invisible to a dump of the live tree - an
    arm reading only the section would call the fault fixed while it stood.
    ``test_the_dead_node_arm_fires_on_a_seam_with_no_generation_gate`` runs these
    same steps against an ``app.js`` with the guard planted out, where the
    pinned node DOES receive the plan, so this arm is known able to go red.
    """
    report = _superseded_run(tmp_path, web_dir=panel_harness.WEB_DIR)

    remounted = [step for step in report["steps"] if step["kind"] == "remount"][-1]
    assert remounted["held_in_section"] is False, (
        "the pinned result node is still in the section, so the repaint never "
        "discarded it and this arm is measuring nothing"
    )

    dead = _held_text(report, "resolve")
    assert "solved" not in dead, f"the plan was written into a discarded node: {dead}"
    assert "10/3" not in dead, f"a rate was written into a discarded node: {dead}"

    live = text_after_kind(report, "resolve")
    assert "no solve has been asked for yet" in live, live
    assert report["solving"] is False, "the seam left its solve flag raised"


def test_the_dead_node_arm_fires_on_a_seam_with_no_generation_gate(
    tmp_path: Path,
) -> None:
    """The guard is planted out of ``app.js`` and the arm above must go red.

    A TEST THAT HAS NEVER BEEN RED PROVES NOTHING, and this is the one plant
    that matters here: the generation comparison is turned into a tautology, so
    every late answer is delivered exactly as it was before the repair. The
    pinned node then carries the plan, which is the defect stated as a
    measurement.
    """
    planted = _seam_copy(
        tmp_path,
        plant=("if (generation !== panelGeneration) {", "if (generation === null) {"),
    )
    report = _superseded_run(tmp_path, web_dir=planted)

    remounted = [step for step in report["steps"] if step["kind"] == "remount"][-1]
    assert remounted["held_in_section"] is False, remounted

    dead = _held_text(report, "resolve")
    assert "solved" in dead, (
        "the planted seam delivered nothing either, so the arm above is not "
        f"known able to fire: {dead}"
    )
    assert "10/3" in dead, dead


def test_the_dead_node_arm_fires_on_a_seam_that_never_advances_its_generation(
    tmp_path: Path,
) -> None:
    """The OTHER half of the mechanism, planted out on its own.

    THE COMPARISON AND THE ADVANCE ARE TWO SITES AND EITHER ONE CAN BE LOST. A
    gate that compares faithfully against a counter nothing ever moves answers
    "same generation" forever, so the plant above would not have caught this.
    The advance is removed here and the same steps must deliver into the
    discarded node again.
    """
    planted = _seam_copy(tmp_path, plant=("  panelGeneration += 1;\n", ""))
    report = _superseded_run(tmp_path, web_dir=planted)

    remounted = [step for step in report["steps"] if step["kind"] == "remount"][-1]
    assert remounted["held_in_section"] is False, remounted
    assert "solved" in _held_text(report, "resolve"), (
        "removing the generation advance changed nothing, so the advance is not "
        "what the suppression rests on"
    )


def test_the_flag_arms_fire_on_a_seam_that_never_lowers_the_solve_flag(
    tmp_path: Path,
) -> None:
    """``solving`` is planted into a latch and the exit-path arms must go red.

    A LATCHED FLAG LEAVES THE SOLVE BUTTON DEAD FOR THE LIFE OF THE PAGE and
    this page never reloads itself, so the arms above are only worth their words
    if they can see it. The release is moved behind a condition that is never
    true - the query reaching this point is always a string - which latches every
    exit path at once.
    """
    planted = _seam_copy(
        tmp_path,
        plant=(
            "  } catch (networkFailure) {\n"
            "    outcome = { reached: false, http: null, body: null };\n"
            "  } finally {\n",
            "  } catch (networkFailure) {\n"
            "    outcome = { reached: false, http: null, body: null };\n"
            "  }\n"
            "  if (query === null) {\n",
        ),
    )
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        web_dir=planted,
        steps=[
            {"ask": {"tag": "first", "params": dict(_ASK_PARAMS)}},
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
            {"ask": {"tag": "second", "params": dict(_ASK_PARAMS)}},
        ],
    )
    settled = [step for step in report["steps"] if step["kind"] == "resolve"][-1]
    assert settled["solving"] is True, (
        "the planted latch did not latch, so the flag arms are not known able to fire"
    )
    asks = [step for step in report["steps"] if step["kind"] == "ask"]
    assert asks[1]["accepted"] is False, asks


def test_a_repaint_rebuilds_the_bench_and_drops_typed_values(tmp_path: Path) -> None:
    """A repaint replaces every field node, so what the reader typed is gone.

    THIS IS THE MEASUREMENT ``app.js``'s SEAM COMMENT NOW CITES. That comment
    used to say panel sections are "refilled, never rebuilt" so that whatever a
    keyboard reader was standing on survives a repaint, and that was false in
    the way that matters: no reader stands on a SECTION, they stand on its
    CHILDREN, and the seam empties every child on every repaint.

    WHAT IS MEASURED HERE IS NODE IDENTITY AND VALUES, NOT FOCUS. No browser
    runs in this suite, so real focus behaviour is unmeasured and the comment
    says so rather than claiming a guarantee nothing here can check.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        door=DOOR_LIVE,
        steps=[
            {"fill": {"match": {"id": "solve-targets"}, "value": "Desc_IronPlate_C=10"}},
            {"hold": {"id": "solve-targets"}},
            {"remount": True},
        ],
    )
    filled = [step for step in report["steps"] if step["kind"] == "fill"][-1]
    assert input_values({"nodes": filled["nodes"]})["targets"] == "Desc_IronPlate_C=10"

    remounted = [step for step in report["steps"] if step["kind"] == "remount"][-1]
    assert remounted["held_in_section"] is False, (
        "the field the reader typed into is still in the section, so this arm "
        "is not measuring a rebuild at all"
    )
    assert input_values({"nodes": remounted["nodes"]})["targets"] == "", (
        "the rebuilt bench kept a typed value, so the comment this arm backs is "
        "now understating what the seam does"
    )


# ---------------------------------------------------------------------------
# m. The solve flag never latches, on any exit path
# ---------------------------------------------------------------------------

#: Every way a solve can settle, and how a ``resolve`` step spells it. A flag
#: raised and not lowered leaves the Solve button dead for the life of the page,
#: and this page never reloads itself - so each path is walked rather than
#: argued about.
_EXIT_PATHS: Final = (
    ("a plan", {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}),
    ("a refusal", {"call": 0, "status": REFUSED_STATUS, "body": _envelope(REFUSAL_OUTCOME)}),
    ("a body that is not JSON", {"call": 0, "status": OK_STATUS, "bad_json": True}),
    ("a network rejection", {"call": 0, "reject": True}),
)


@pytest.mark.parametrize(("name", "resolution"), _EXIT_PATHS, ids=[row[0] for row in _EXIT_PATHS])
def test_the_solve_flag_is_lowered_on_every_settled_outcome(
    tmp_path: Path, name: str, resolution: Mapping[str, Any]
) -> None:
    """Each exit path lowers ``solving``, and a later press is accepted.

    THE SECOND ASK IS THE PART THAT CANNOT BE FAKED. A report saying the flag
    reads false could be true of a driver looking at the wrong global; a second
    request that the seam ACCEPTS and puts on the wire can only be true of a
    seam that is genuinely free again.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        name: Which exit path this row walks, for the failure message.
        resolution: The ``resolve`` step spelling that path.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        steps=[
            {"ask": {"tag": "first", "params": dict(_ASK_PARAMS)}},
            {"resolve": dict(resolution)},
            {"ask": {"tag": "second", "params": dict(_ASK_PARAMS)}},
        ],
    )
    asks = [step for step in report["steps"] if step["kind"] == "ask"]
    assert asks[0]["accepted"] is True, f"the seam refused the first ask on {name}"

    settled = [step for step in report["steps"] if step["kind"] == "resolve"][-1]
    assert settled["solving"] is False, f"solving latched on {name}"
    assert asks[1]["accepted"] is True, (
        f"the seam refused a later solve after {name}, so the flag latched"
    )
    assert len(report["fetch_calls"]) == TWO_PRESSES, report["fetch_calls"]


def test_the_solve_flag_is_lowered_when_the_caller_itself_throws(tmp_path: Path) -> None:
    """A panel whose ``onSettled`` throws costs itself a result and nothing else.

    THE ONE EXIT PATH THE BENCH CANNOT DRIVE, which is why the driver can ask
    the seam directly. A throw out of the callback must not take the flag with
    it, and nothing from the exception may reach the page.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        steps=[
            {"ask": {"tag": "thrower", "params": dict(_ASK_PARAMS), "throws": True}},
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
            {"ask": {"tag": "after", "params": dict(_ASK_PARAMS)}},
        ],
    )
    assert [row["tag"] for row in report["delivered"]] == ["thrower"], report["delivered"]

    settled = [step for step in report["steps"] if step["kind"] == "resolve"][-1]
    assert settled["threw"] is None, "the throw escaped the seam"
    assert settled["solving"] is False, "solving latched on a throwing callback"

    asks = [step for step in report["steps"] if step["kind"] == "ask"]
    assert asks[1]["accepted"] is True, "the seam refused a later solve after a throw"


def test_a_delivery_the_repaint_outran_is_dropped_and_still_lowers_the_flag(
    tmp_path: Path,
) -> None:
    """The suppression is a gate on the CALLBACK and never on the flag.

    A guard that suppressed the delivery by refusing to leave the in-flight
    state would trade a silent fault for a dead button. This walks both halves
    at once: the outran callback never fires, and the very next ask is accepted.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        steps=[
            {"ask": {"tag": "outran", "params": dict(_ASK_PARAMS)}},
            {"remount": True},
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
            {"ask": {"tag": "after", "params": dict(_ASK_PARAMS)}},
        ],
    )
    assert report["delivered"] == [], (
        f"an answer the repaint outran was still delivered: {report['delivered']}"
    )

    settled = [step for step in report["steps"] if step["kind"] == "resolve"][-1]
    assert settled["solving"] is False, "the suppression latched the solve flag"

    asks = [step for step in report["steps"] if step["kind"] == "ask"]
    assert asks[1]["accepted"] is True, "a suppressed delivery left the seam busy"


def test_a_delivery_with_no_repaint_between_is_not_suppressed(tmp_path: Path) -> None:
    """The control the suppression arm needs: without a repaint, it arrives.

    AGREEMENT BETWEEN TWO NEGATIVE MEASUREMENTS IS NOT EVIDENCE. A gate that
    dropped EVERY delivery would satisfy both arms above, so this one pins the
    positive case through the same steps minus the remount.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        steps=[
            {"ask": {"tag": "arrives", "params": dict(_ASK_PARAMS)}},
            {"resolve": {"call": 0, "status": OK_STATUS, "body": _envelope(PLAN_OUTCOME)}},
        ],
    )
    assert [row["tag"] for row in report["delivered"]] == ["arrives"], report["delivered"]
    assert report["delivered"][0]["http"] == OK_STATUS, report["delivered"]


# ---------------------------------------------------------------------------
# n. The seam publishes the registered panel ids
# ---------------------------------------------------------------------------

#: ``registerPanel``'s whole body, from its declaration to the brace that
#: closes it at column zero.
_REGISTRAR_BLOCK: Final = re.compile(r"function registerPanel\([\s\S]*?\n\}\n")

#: An id registered after the panel under test, so an ORDER has two members.
_EXTRA_PANEL: Final = "x1probe"


def test_the_seam_publishes_the_panel_ids_in_registration_order(tmp_path: Path) -> None:
    """``data.panels`` is an array of id strings, in the order they registered.

    THE ANTI-DRIFT REASON THIS KEY EXISTS. No route serves the panel list, so a
    panel that wanted it had either to read the host's own global or to carry a
    typed copy that goes stale the moment a panel is added or renamed. The seam
    publishes it instead, beside the payloads a mount already receives.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        extra_panels=[_EXTRA_PANEL],
        steps=[{"remount": True}],
    )
    published = [step for step in report["steps"] if step["kind"] == "remount"][-1]["panels"]
    assert published == [PANEL_ID, _EXTRA_PANEL], published
    assert all(isinstance(entry, str) for entry in published), published


def test_the_seam_publishes_an_empty_array_when_nothing_is_registered(
    tmp_path: Path,
) -> None:
    """With no panel registered the key is PRESENT and is ``[]``.

    ABSENT AND NULL ARE BOTH REFUSED. A reader of this key has to be able to
    iterate it without asking whether it exists, or the anti-drift gain is spent
    on a guard at every call site.
    """
    report = drive(tmp_path, panel_harness.null_payload())
    assert report["panels_key_when_empty"] is True, (
        "the seam omits the panels key entirely before anything registers"
    )
    assert report["panels_when_empty"] == [], report["panels_when_empty"]


def test_a_late_registration_is_mounted_against_a_list_holding_itself(
    tmp_path: Path,
) -> None:
    """A panel registering after a repaint sees a list that includes it.

    THE SEAM HOLDS THE LAST REPAINT'S PAYLOAD AND MOUNTS A LATE MODULE AGAINST
    IT. A list built once and never refreshed would hand that module a roster
    missing the only member it is certain of - itself - which is the drift this
    key exists to remove, reappearing one layer down.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=DOOR_LIVE,
        extra_panels=[_EXTRA_PANEL],
        steps=[{"remount": True}],
    )
    published = [step for step in report["steps"] if step["kind"] == "remount"][-1]["panels"]
    assert _EXTRA_PANEL in published, published

    source = (panel_harness.WEB_DIR / "app.js").read_bytes().decode("ascii")
    registrar = re.search(_REGISTRAR_BLOCK, source)
    assert registrar is not None, "registerPanel is not where this arm expects it"
    assert "panelIds()" in registrar.group(0), (
        "registerPanel mounts a late panel without refreshing the published id "
        "list, so that panel is handed a roster that does not include it"
    )


# ---------------------------------------------------------------------------
# k. Character set
# ---------------------------------------------------------------------------


def test_this_module_and_the_panel_hold_only_seven_bit_ascii() -> None:
    """Both files this slice writes decode as ASCII and carry no carriage return.

    Windows PowerShell 5.1 ANSI-decodes a BOM-less script and a UTF-8 em-dash
    inside a double-quoted string becomes a string terminator. The rule is a
    mechanism, not a style preference.
    """
    for path in (panel_harness.WEB_DIR / MODULE, Path(__file__)):
        raw = path.read_bytes()
        raw.decode("ascii")
        assert b"\r" not in raw, f"{path.name} holds a carriage return"


# ---------------------------------------------------------------------------
# o. The registry's provenance, said before the machines (CS-1315 slice B)
# ---------------------------------------------------------------------------

#: What the bench says over a registry the audit did not verify, over one it
#: did, and over a body that carried no state at all.
UNVERIFIED_MARK: Final = "registry: UNVERIFIED"
VERIFIED_MARK: Final = "registry: verified"
NO_STATE_MARK: Final = "carried no build state"

#: The first figure group the bench renders, which the provenance line precedes.
FIRST_FIGURE: Final = "machines"

#: The two registries the audit does not verify: other docs bytes, and none.
UNVERIFIED_SOURCES: Final = ("other-docs-bytes", "no-byte-source")


def _served_outcome(source_sha256: str | None) -> dict[str, Any]:
    """A settled 200 carrying one REAL ``/api/solve`` body over a stamped registry.

    Args:
        source_sha256: The hash the registry claims it was built from, or None.

    Returns:
        The outcome the door hands the panel's callback.
    """
    import dataclasses  # noqa: PLC0415

    from tests.solve import synthetic as corpus  # noqa: PLC0415

    stamped = dataclasses.replace(corpus.solve_registry(), source_sha256=source_sha256)

    class _Provider:
        def registry(self) -> Any:
            return stamped

    response = solve.solve_handler(_Provider())(
        {
            solve.PARAM_TARGETS: f"{corpus.SOLVE_ROD_ITEM}=50",
            solve.PARAM_RECIPES: f"{corpus.ROD_RECIPE},{corpus.PLATE_RECIPE}",
            solve.PARAM_RAW_ITEMS: corpus.SOLVE_ORE_ITEM,
            solve.PARAM_BYPRODUCT_POLICY: ratio.BYPRODUCT_SINKABLE,
        }
    )
    assert response.http_status == contract.HTTP_OK, response.payload
    return {"reached": True, "http": response.http_status, "body": dict(response.payload)}


def _settled_text(tmp_path: Path, outcome: Mapping[str, Any]) -> str:
    """The bench's text once one outcome has settled.

    Args:
        tmp_path: The driver's scratch directory.
        outcome: What the door hands the callback.

    Returns:
        The rendered text.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(outcome),
    )
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    return panel_text(report)


@pytest.mark.parametrize("case", UNVERIFIED_SOURCES)
def test_an_unverified_registry_is_said_before_the_machines_with_its_served_code(
    tmp_path: Path, case: str
) -> None:
    outcome = _served_outcome(OFF_PIN_DOCS_SHA256 if case == "other-docs-bytes" else None)
    rows = outcome["body"]["data"]["warnings"]
    codes = [str(row["code"]) for row in rows]
    expected = (
        build_model.WARN_REGISTRY_MISMATCH
        if case == "other-docs-bytes"
        else build_model.WARN_REGISTRY_UNVERIFIED
    )
    assert codes == [expected], rows

    text = _settled_text(tmp_path, outcome)

    assert UNVERIFIED_MARK in text, text
    assert expected in text, text
    assert VERIFIED_MARK not in text
    assert text.index(UNVERIFIED_MARK) < text.index(FIRST_FIGURE), text


def test_a_verified_registry_is_said_to_be_verified_and_names_no_code(tmp_path: Path) -> None:
    outcome = _served_outcome(docs_pin())
    assert outcome["body"]["data"]["warnings"] == []

    text = _settled_text(tmp_path, outcome)

    assert VERIFIED_MARK in text, text
    assert UNVERIFIED_MARK not in text
    assert build_model.WARN_REGISTRY_MISMATCH not in text
    assert build_model.WARN_REGISTRY_UNVERIFIED not in text


def test_a_body_without_a_build_state_is_never_read_as_verified(tmp_path: Path) -> None:
    outcome = _served_outcome(docs_pin())
    data = outcome["body"]["data"]
    del data["build_state"]
    del data["warnings"]

    text = _settled_text(tmp_path, outcome)

    assert NO_STATE_MARK in text, text
    assert VERIFIED_MARK not in text
