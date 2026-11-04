"""CS-1371 arm (7) - the Advice panel states a request and renders the server's answer.

THE CRITERION. ``docs/item_notes/phase5.md``, ``## CS-1371``, ``### Acceptance``: one
bench of labelled controls and one button, no form element, each required and none
prefilled, through new doors in ``clockspeed/surface/web/app.js``; the visible cards
``data.advice`` already holds before any request, tiers 1 and 2; the stated request's
cards and its ``plan_outcome`` after one; a button on a card reading tier 3 through the
derivation route; a null ``data.advice`` or ``data.registry`` a named refusal and no
bench.

HOW IT IS DRIVEN.

a. THE SHIPPED MODULE, UNDER A LOCAL DRIVER. ``tests/surface/panel_harness.py`` passes
   ``data`` as JSON, so it cannot hand a mount a door, and its stand-in gives a
   ``select`` no selection: a node there is a plain object, so reading ``value`` off a
   ``select`` answers undefined however the panel built it. An arm claiming "nothing is
   prefilled" needs the opposite - a ``select`` that answers what a browser would show,
   which is the LAST option marked selected and otherwise the FIRST. An arm claiming focus
   survives an answer needs ``contains`` and ``focus``, and a focused node that leaves the
   document dropping focus as a browser drops it. So this driver is the shared stand-in
   plus exactly those, and
   :func:`test_the_driver_widens_the_shared_stand_in_by_only_what_its_arms_read` measures
   that it stayed so. The shared harness is not touched: the panel reaches those two
   members only when an answer settles, and that harness hands it no door to settle.
b. THE SHARED HARNESS TOO, because it is narrower and it feeds the seam grader: a panel
   green only under the wider driver would be red in
   ``tests/surface/test_panel_seam.py``. The arms in section c run through it.
c. THE DOORS ARE GRADED TWICE. A recording stub for what the panel hands a door, and
   ``app.js``'s own door over an answerable ``fetch`` for what leaves the page.
d. THE REAL ROUTES, SO THE STUBS CANNOT DRIFT. The hand-built bodies in most arms are
   small on purpose, and a body this file believes in agrees with whatever this file
   believes. So every name and key is imported from
   ``clockspeed/surface/api/advice.py`` and ``clockspeed/surface/api/registry.py``, and
   section n drives the panel over bodies the real route table answers, with the real
   ``StoreAdviceSource``, the real advisor and the synthetic worlds
   ``tests/surface/test_advice_source.py`` already works by hand. It then replays the
   URLs the page actually fetched through the server's own matcher, so a door that sent
   anything the route would not take reads as a different body rather than as green.

Test-quality discipline (``CONVENTIONS.md`` section 7.2). Every negative has a control
proving the positive reached its assertion, and each detector used to prove an absence
is run against a planted positive.
"""

from __future__ import annotations

import json
import re
import shutil
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import parse_qsl

import pytest

from clockspeed.advisor.cards import card_id
from clockspeed.advisor.rules import plan as plan_rules
from clockspeed.solve import optimize, ratio
from clockspeed.surface import server
from clockspeed.surface.api import advice as advice_endpoint
from clockspeed.surface.api import contract
from clockspeed.surface.api import registry as api_registry
from tests.advisor import test_plan_redesign as redesign_fixtures
from tests.surface import audit_harness, panel_harness
from tests.surface import test_advice_source as source_fixtures
from tests.surface.test_panel_solve import division_sites

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

#: The shipped module this file grades.
MODULE: Final = "panel_advice.js"

#: The seam file that publishes the doors.
SEAM: Final = "app.js"

#: The stylesheet that reserves the status line.
STYLESHEET: Final = "app.css"

#: The id it registers with the seam.
PANEL_ID: Final = "advice"

#: The four names the route takes, in the order the bench shows them.
FIELD_NAMES: Final = advice_endpoint.PLAN_PARAMETERS

#: The bench's control for each name.
FIELD_IDS: Final[Mapping[str, str]] = {name: f"advice-{name}" for name in FIELD_NAMES}

#: The word each field's refusal names it by.
FIELD_LABELS: Final[Mapping[str, str]] = {
    advice_endpoint.TARGET_PARAMETER: "target",
    advice_endpoint.RATE_PARAMETER: "rate",
    advice_endpoint.DIRECTION_PARAMETER: "direction",
    advice_endpoint.BYPRODUCT_POLICY_PARAMETER: "byproduct policy",
}

#: The one bench button, the live line it answers on and the region an answer lands in.
ASK_ID: Final = "advice-ask"
STATUS_ID: Final = "advice-status"
ANSWER_ID: Final = "advice-answer"

#: How many labelled controls the bench builds.
EXPECTED_CONTROLS: Final = 4

#: The longest line the status region may carry while a request is in flight. Two lines
#: at the narrowest width the page is measured at, which is what the reserved height
#: holds; a longer line would move what sits under it.
STATUS_LINE_CEILING: Final = 60

#: How long the driver may take before it is a hang rather than a run.
#: A RUN limit: it counts from the start marker, never from the spawn (CS-1329).
NODE_TIMEOUT_SECONDS: Final = 60.0

#: The doors a mount can be handed: the recording stub, none at all, or app.js's own.
DOOR_STUB: Final = "stub"
DOOR_NONE: Final = "none"
DOOR_LIVE: Final = "live"

#: Every way a browser script reaches the network.
NETWORK_PRIMITIVES: Final = (
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "sendBeacon",
    "import(",
)

#: Every sink that turns a string into markup.
MARKUP_SINKS: Final = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")

#: Every spelling that would turn the rate's text into a binary number on this page.
NUMBER_PARSERS: Final = ("parseFloat", "parseInt", "Number(", "Math.", ".toFixed", "BigInt(")

#: A block comment or a string literal, blanked before a code scan so a paragraph SAYING
#: "no innerHTML" cannot read as an innerHTML.
NON_CODE: Final = re.compile(
    r"/\*[\s\S]*?\*/" r'|"(?:[^"\\\n]|\\.)*"' r"|'(?:[^'\\\n]|\\.)*'",
    re.MULTILINE,
)

#: A served target list NOT in sorted order, so a panel that sorted it reddens.
SERVED_TARGETS: Final = ("Desc_Zinc_C", "Desc_Alpha_C", "Desc_Unnamed_C", "Desc_Nulled_C")

#: The display names the fixture registry holds. Desc_Unnamed_C has no row at all and
#: Desc_Nulled_C has a row whose name is null: each falls back to its key.
DISPLAY_NAMES: Final[Mapping[str, str]] = {
    "Desc_Zinc_C": "Zinc Rod",
    "Desc_Alpha_C": "Alpha Plate",
}

#: One complete statement, in the spelling the door takes.
STATED: Final[Mapping[str, str]] = {
    advice_endpoint.TARGET_PARAMETER: "Desc_Alpha_C",
    advice_endpoint.RATE_PARAMETER: "1/3",
    advice_endpoint.DIRECTION_PARAMETER: optimize.OBJECTIVE_POWER,
    advice_endpoint.BYPRODUCT_POLICY_PARAMETER: ratio.BYPRODUCT_SINKABLE,
}

#: The one key a plan_outcome always carries that this file does not vary.
OUTCOME_STATUS_KEY: Final = "status"

#: The four keys a plan_outcome may carry beside its status, each with a value and the
#: label it renders under. Only ever rendered when present. An arm below binds the keys to
#: ``clockspeed/surface/api/advice.py::PLAN_OUTCOME_KEYS``.
OUTCOME_FIELDS: Final[Mapping[str, tuple[Any, str]]] = {
    "reason": ("reason-word-of-the-outcome", "reason"),
    "redesign": ("redesign-word-of-the-outcome", "redesign"),
    "trimmed": (["Recipe_TrimmedOne_C", "Recipe_TrimmedTwo_C"], "trimmed recipes"),
    "unmade": (["Desc_UnmadeOne_C"], "unmade items"),
}

#: The stand-in, the recording doors and the step loop. It is deliberately not a
#: browser: nothing here lays anything out, and no arm claims anything about pixels or
#: focus. See the module docstring for why a select gets a value here.
_DRIVER: Final = r""""use strict";

var fs = require("node:fs");
var path = require("node:path");
var vm = require("node:vm");

var request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
var webDir = request.web_dir;
var listeners = new WeakMap();
var known = Object.create(null);

function optionsOf(select) {
  return select.childNodes.filter(function (child) {
    return child.tagName === "OPTION";
  });
}

function optionValue(option) {
  /* A browser reads the value, then the attribute, then the option's text. */
  if (typeof option.value === "string") {
    return option.value;
  }
  var attribute = option.getAttribute("value");
  return attribute !== null ? attribute : option.textContent;
}

function giveSelectItsValue(node) {
  /*
    THE ONE WIDENING. A select shows the last option marked selected, else the
    first, and assigning a value picks the option carrying it, or none at all.
    A panel that prefilled through option.selected reads as prefilled here.
  */
  var assigned = null;
  Object.defineProperty(node, "value", {
    enumerable: true,
    get: function () {
      if (assigned !== null) {
        return assigned;
      }
      var options = optionsOf(node);
      var marked = options.filter(function (option) {
        return option.selected === true || option.getAttribute("selected") !== null;
      });
      var shown = marked.length ? marked[marked.length - 1] : options[0];
      return shown ? optionValue(shown) : "";
    },
    set: function (value) {
      var wanted = String(value);
      var held = optionsOf(node).some(function (option) {
        return optionValue(option) === wanted;
      });
      assigned = held ? wanted : "";
    }
  });
}

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
    /*
      A focused node leaving the document takes focus with it, to the body in a browser
      and to nothing here. This is the fault the focus arms exist to see.
    */
    if (child.contains(globalThis.document.activeElement)) {
      globalThis.document.activeElement = null;
    }
    return child;
  };
  node.contains = function (other) {
    if (!other) {
      return false;
    }
    if (other === node) {
      return true;
    }
    return node.childNodes.some(function (child) {
      return child.contains(other);
    });
  };
  node.focus = function () {
    globalThis.document.activeElement = node;
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
  if (node.tagName === "SELECT") {
    giveSelectItsValue(node);
  }
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
  PARKED UNTIL liveFetch IS RAISED, as tests/surface/test_panel_solve.py's driver
  does: the load-time repaint must not overwrite this run's payload, so only a
  request issued from a step can ever be answered.
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
    method: init && init.method ? String(init.method) : null,
    has_body: Boolean(init && Object.prototype.hasOwnProperty.call(init, "body"))
  });
  return new Promise(function (resolve, reject) {
    pendingFetches.push({ resolve: resolve, reject: reject });
  });
};

async function drain() {
  for (var turn = 0; turn < 5; turn += 1) {
    await new Promise(function (done) {
      setImmediate(done);
    });
  }
}

function load(file) {
  vm.runInThisContext(fs.readFileSync(file, "utf8"), { filename: path.basename(file) });
}

function describe(failure) {
  return failure && failure.message ? String(failure.message) : String(failure);
}

load(path.join(webDir, "app.js"));

var publishedDoors = Object.keys(panelData({}).actions).sort();

var captured = null;
var mountThrew = null;
var realRegister = registerPanel;

globalThis.registerPanel = function (id, mountFn) {
  var wrapped = function (root, data) {
    try {
      return mountFn(root, data);
    } catch (failure) {
      mountThrew = describe(failure);
      throw failure;
    }
  };
  var accepted = realRegister(id, wrapped);
  if (accepted) {
    captured = { id: id, mount: wrapped };
  }
  return accepted;
};

var loadThrew = null;
try {
  load(path.join(webDir, request.module));
} catch (failure) {
  loadThrew = describe(failure);
}

/* --- the doors, recorded ------------------------------------------------- */

var doorCalls = [];
var settlers = [];
var accepts = request.accepts;

function copyOf(params) {
  if (!params || typeof params !== "object") {
    return null;
  }
  var copy = {};
  Object.keys(params).forEach(function (name) {
    copy[name] = params[name];
  });
  return copy;
}

function answerOf() {
  var at = doorCalls.length - 1;
  if (request.door_throws) {
    throw new Error("planted-door-failure-text");
  }
  return at < accepts.length ? Boolean(accepts[at]) : true;
}

function stubAdvice(params, onSettled) {
  doorCalls.push({ door: "advice", params: copyOf(params) });
  settlers.push(onSettled);
  return answerOf();
}

function stubDerivation(id, params, onSettled) {
  doorCalls.push({ door: "derivation", id: id, params: copyOf(params) });
  settlers.push(onSettled);
  return answerOf();
}

var data = request.data;
if (request.door === "live") {
  /*
    app.js refuses a request while a repaint is in flight, and the load-time
    repaint is parked forever on the fetch above, so the flag is lowered here: a
    property of this driver and not of the page.
  */
  globalThis.repainting = false;
  liveFetch = true;
  data.actions = { requestAdvice: requestAdvice, requestDerivation: requestDerivation };
} else if (request.door === "stub") {
  data.actions = { requestAdvice: stubAdvice, requestDerivation: stubDerivation };
}

/* --- stepping ------------------------------------------------------------ */

function section() {
  return captured ? lookup("panel-" + captured.id) : null;
}

function attributesOf(node) {
  var copy = {};
  Object.keys(node.attributes).forEach(function (name) {
    copy[name] = node.attributes[name];
  });
  return copy;
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
      value: typeof node.value === "string" ? node.value : null,
      hidden: node.hidden === true,
      selected: node.selected === true,
      listens: (listeners.get(node) || []).map(function (entry) {
        return entry.type;
      })
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

function activeId() {
  var active = globalThis.document.activeElement;
  return active ? active.id || active.tagName : null;
}

function byId(id) {
  var nodes = [];
  dump(section(), nodes);
  return nodes.filter(function (node) {
    return node.id === id;
  });
}

function runStep(spec) {
  var step = { kind: null, matched: null, threw: null };
  if (spec.focus) {
    step.kind = "focus";
    var focused = byId(spec.focus);
    step.matched = focused.length;
    if (focused.length === 1) {
      focused[0].focus();
    }
    return Promise.resolve(step);
  }
  if (spec.fill) {
    step.kind = "fill";
    var filled = byId(spec.fill.id);
    step.matched = filled.length;
    if (filled.length === 1) {
      filled[0].value = String(spec.fill.value);
    }
    return Promise.resolve(step);
  }
  if (spec.click) {
    step.kind = "click";
    var clicked = byId(spec.click);
    step.matched = clicked.length;
    if (clicked.length === 1) {
      (listeners.get(clicked[0]) || [])
        .filter(function (entry) {
          return entry.type === "click";
        })
        .forEach(function (entry) {
          try {
            entry.handler.call(clicked[0], { type: "click", target: clicked[0] });
          } catch (failure) {
            step.threw = describe(failure);
          }
        });
    }
    return Promise.resolve(step);
  }
  if (spec.settle) {
    step.kind = "settle";
    var settler = settlers[spec.settle.call];
    step.matched = typeof settler === "function" ? 1 : 0;
    if (step.matched === 1) {
      settler(spec.settle.outcome);
    }
    return Promise.resolve(step);
  }
  if (spec.ask) {
    step.kind = "ask";
    step.matched = 1;
    step.accepted =
      spec.ask.door === "advice"
        ? requestAdvice(spec.ask.params, function () {
            return undefined;
          })
        : requestDerivation(spec.ask.id, spec.ask.params, function () {
            return undefined;
          });
    return Promise.resolve(step);
  }
  step.kind = "resolve";
  var slot = pendingFetches[spec.resolve.call];
  step.matched = slot ? 1 : 0;
  if (slot) {
    slot.resolve({
      status: spec.resolve.status,
      json: function () {
        return Promise.resolve(spec.resolve.body);
      }
    });
  }
  return drain().then(function () {
    return step;
  });
}

var steps = [];

async function drive() {
  if (!captured) {
    return;
  }
  mountPanel(captured, data);
  steps.push({
    kind: "mount",
    matched: 1,
    threw: mountThrew,
    active: activeId(),
    nodes: dump(section(), null)
  });
  for (var at = 0; at < request.steps.length; at += 1) {
    var step = await runStep(request.steps[at]);
    step.active = activeId();
    step.nodes = dump(section(), null);
    steps.push(step);
  }
}

drive().then(
  function () {
    process.stdout.write(
      JSON.stringify({
        registered: Boolean(captured),
        panel_id: captured ? captured.id : null,
        load_threw: loadThrew,
        mount_threw: mountThrew,
        steps: steps,
        nodes: steps.length ? steps[steps.length - 1].nodes : [],
        door_calls: doorCalls,
        fetch_calls: fetchCalls,
        published_doors: publishedDoors,
        surface: {
          node: Object.getOwnPropertyNames(makeNode("div")).sort(),
          select: Object.getOwnPropertyNames(makeNode("select")).sort()
        }
      })
    );
  },
  function (failure) {
    process.stderr.write("the stepping loop threw: " + describe(failure));
    process.exitCode = 1;
  }
);
"""


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def read_asset(name: str) -> str:
    """One shipped asset, as ASCII text.

    Args:
        name: The asset's filename.

    Returns:
        The whole file.
    """
    return (panel_harness.WEB_DIR / name).read_bytes().decode("ascii")


def code_only(source: str) -> str:
    """The source with its block comments and string literals blanked.

    Args:
        source: A shipped module's text.

    Returns:
        The same length of text, holding nothing a sentence could plant.
    """
    return NON_CODE.sub(lambda match: " " * len(match.group(0)), source)


def drive(
    tmp_path: Path,
    data: Mapping[str, Any],
    *,
    door: str = DOOR_STUB,
    accepts: Sequence[bool] = (),
    door_throws: bool = False,
    steps: Sequence[Mapping[str, Any]] = (),
) -> Mapping[str, Any]:
    """Mount the shipped module under the local driver and run the steps.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        data: The payload handed to the mount, before a door is added.
        door: :data:`DOOR_STUB`, :data:`DOOR_NONE` or :data:`DOOR_LIVE`.
        accepts: What a stub door returns for call 0, call 1 and so on. A call past
            the end of this sequence is accepted.
        door_throws: Whether a stub door throws rather than answering.
        steps: ``fill``, ``click``, ``settle``, ``ask`` and ``resolve`` entries.

    Returns:
        The driver's report. Every step named exactly one node or one call.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so no panel was mounted and nothing was graded. This "
            "FAILS rather than skipping: a gate that skips its checks reports PASS."
        )
    if not (panel_harness.WEB_DIR / MODULE).is_file():
        pytest.fail(f"there is no panel module at {MODULE}")

    scratch = tmp_path / "advice_bench"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "advice_driver.cjs"
    script.write_bytes(_DRIVER.encode("ascii"))
    payload = scratch / "request.json"
    payload.write_bytes(
        json.dumps(
            {
                "web_dir": str(panel_harness.WEB_DIR),
                "module": MODULE,
                "data": dict(data),
                "door": door,
                "accepts": list(accepts),
                "door_throws": door_throws,
                "steps": [dict(step) for step in steps],
            }
        ).encode("ascii")
    )

    completed = panel_harness.run_node(
        node,
        script,
        str(payload),
        label="the advice bench driver",
        run_timeout=NODE_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        pytest.fail(f"the advice bench driver exited {completed.returncode}: {completed.stderr}")
    report: Mapping[str, Any] = json.loads(completed.stdout)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["mount_threw"] is None, report["mount_threw"]
    unmatched = tuple(step["kind"] for step in report["steps"] if step["matched"] != 1)
    assert unmatched == (), unmatched
    return report


def card(headline: str, reason: str, *, visible: bool = True) -> dict[str, Any]:
    """One listed card, keyed as ``/api/advice`` keys it.

    The id is the real function's real shape, computed here and never written down: a
    64-hex literal in a tracked file is what the personal-data sweep reads as an
    account id.

    Args:
        headline: Tier 1.
        reason: Tier 2.
        visible: Whether the listing flags it visible.

    Returns:
        The card.
    """
    return {
        "id": card_id(plan_rules.ADOPT_RULE.rule_id, f"plan:{headline}", None),
        "rule_id": plan_rules.ADOPT_RULE.rule_id,
        "domain": plan_rules.ADOPT_RULE.domain,
        "headline": headline,
        "reason": reason,
        "state": "new" if visible else "dismissed",
        "snoozed_until": None,
        "muted": False,
        "visible": visible,
    }


def listing(*cards: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    """One ``/api/advice`` data object.

    Args:
        *cards: The cards it lists.
        **extra: Further keys, which is how a plan_outcome rides.

    Returns:
        The data object.
    """
    return {"new_world": False, "cards": [dict(row) for row in cards], **extra}


def registry_body() -> dict[str, Any]:
    """The part of ``/api/registry`` this panel reads, unsorted and with both fallbacks.

    Returns:
        The data object.
    """
    return {
        "items": [
            {"key": "Desc_Alpha_C", "display_name": "Alpha Plate"},
            {"key": "Desc_Nulled_C", "display_name": None},
            {"key": "Desc_Zinc_C", "display_name": "Zinc Rod"},
            {"key": "Desc_NeverATarget_C", "display_name": "Never A Target"},
        ],
        api_registry.PLAN_TARGETS_KEY: list(SERVED_TARGETS),
    }


def payload(*cards: Mapping[str, Any]) -> dict[str, Any]:
    """A six-key payload holding this listing and the fixture registry.

    Args:
        *cards: The cards ``data.advice`` holds.

    Returns:
        The payload.
    """
    return panel_harness.null_payload(advice=listing(*cards), registry=registry_body())


def answered(data: Mapping[str, Any]) -> dict[str, Any]:
    """A settled 200 carrying this data object, built by the shipped constructor.

    Args:
        data: The listing or derivation body.

    Returns:
        The outcome shape ``app.js`` hands a callback.
    """
    response = contract.ok(advice_endpoint.ENDPOINT, data)
    return {"reached": True, "http": response.http_status, "body": dict(response.payload)}


def delivered(response: contract.Response) -> dict[str, Any]:
    """A settled answer, whichever route or constructor produced it.

    Args:
        response: The response, a refusal or a 200.

    Returns:
        The outcome shape ``app.js`` hands a callback.
    """
    return {"reached": True, "http": response.http_status, "body": dict(response.payload)}


def fills(values: Mapping[str, str] = STATED) -> list[dict[str, Any]]:
    """The steps that state these values, in bench order.

    Args:
        values: Name to value.

    Returns:
        One ``fill`` step per name.
    """
    return [{"fill": {"id": FIELD_IDS[name], "value": value}} for name, value in values.items()]


def stated_query() -> str:
    """:data:`STATED` as the door must encode it: the route's own names, in its own order.

    Returns:
        The query string, with the rate's slash escaped and nothing else changed.
    """
    values = (*STATED.values(),)
    escaped = tuple(value.replace("/", "%2F") for value in values)
    return "&".join(f"{name}={value}" for name, value in zip(FIELD_NAMES, escaped, strict=True))


def press_ask() -> dict[str, Any]:
    """The step pressing the bench's one button.

    Returns:
        The step.
    """
    return {"click": ASK_ID}


def read_id(index: int) -> str:
    """The derivation button of the card at this listed position.

    Args:
        index: The card's position among the listed cards.

    Returns:
        Its element id.
    """
    return f"advice-read-{index}"


def card_status_id(index: int) -> str:
    """The status line of the card at this listed position.

    Args:
        index: The card's position among the listed cards.

    Returns:
        Its element id.
    """
    return f"advice-read-status-{index}"


def derivation_id(index: int) -> str:
    """The preformatted region of the card at this listed position.

    Args:
        index: The card's position among the listed cards.

    Returns:
        Its element id.
    """
    return f"advice-derivation-{index}"


def row_of(rows: Sequence[Mapping[str, Any]], node_id: str) -> Mapping[str, Any]:
    """The one row in this dump carrying this id.

    Args:
        rows: One step's node dump.
        node_id: The element id.

    Returns:
        The row.
    """
    hits = [row for row in rows if row["id"] == node_id]
    count = len(hits)
    assert count == 1, f"{count} node(s) carry the id {node_id}"
    return hits[0]


def text_of(report: Mapping[str, Any], node_id: str) -> str:
    """The text of the one node carrying this id, after the last step.

    Args:
        report: The driver's report.
        node_id: The element id.

    Returns:
        Its text.
    """
    return str(row_of(report["nodes"], node_id)["text"])


def panel_text(report: Mapping[str, Any]) -> str:
    """Everything the panel put on the page, after the last step.

    Args:
        report: The driver's report.

    Returns:
        The section's joined text.
    """
    return str(report["nodes"][0]["text"])


def tags(report: Mapping[str, Any]) -> frozenset[str]:
    """Every element kind in the panel, after the last step.

    Args:
        report: The driver's report.

    Returns:
        The upper-cased tag names.
    """
    return frozenset(str(row["tag"]) for row in report["nodes"])


def options_of(report: Mapping[str, Any], node_id: str) -> tuple[tuple[str, str], ...]:
    """The options of one select, as ``(value, text)`` in document order.

    Args:
        report: The driver's report.
        node_id: The select's id.

    Returns:
        The options.
    """
    parent = row_of(report["nodes"], node_id)["index"]
    return tuple(
        (str(row["value"]), str(row["text"]))
        for row in report["nodes"]
        if row["parent"] == parent and row["tag"] == "OPTION"
    )


def door_calls(report: Mapping[str, Any], door: str) -> tuple[Mapping[str, Any], ...]:
    """The calls one recording door received.

    Args:
        report: The driver's report.
        door: ``advice`` or ``derivation``.

    Returns:
        The calls, in order.
    """
    return tuple(call for call in report["door_calls"] if call["door"] == door)


# ---------------------------------------------------------------------------
# a. The fixtures and the driver are what they claim
# ---------------------------------------------------------------------------


def test_the_card_fixture_is_keyed_as_the_endpoint_serves_it() -> None:
    # A hand-typed fixture agrees with whatever this file believes the shape is, so it
    # is bound to the endpoint's own tables and the arms below read the real keys.
    assert set(card("h", "r")) == set(advice_endpoint.CARD_KEYS)
    assert set(listing()) == set(advice_endpoint.DATA_KEYS)
    assert set(listing(plan_outcome={})) == set(advice_endpoint.STATED_DATA_KEYS)
    assert {OUTCOME_STATUS_KEY, *OUTCOME_FIELDS} == set(advice_endpoint.PLAN_OUTCOME_KEYS)
    body = {"id": "x", "rule_id": plan_rules.ADOPT_RULE.rule_id, "derivation": "text"}
    assert set(body) == set(advice_endpoint.DERIVATION_KEYS)
    served = {*api_registry.DATA_KEYS, api_registry.PLAN_TARGETS_KEY}
    assert served == set(api_registry.BODY_KEYS), sorted(served)


def test_the_driver_widens_the_shared_stand_in_by_only_what_its_arms_read(tmp_path: Path) -> None:
    """Every node the shared surface plus two, and a select those plus ``value``.

    A harness wider than the gate it feeds certifies a panel the gate rejects, which is
    why ``tests/surface/panel_harness.py`` refuses to widen. This driver does widen,
    because no arm can say "nothing is prefilled" over a select that cannot answer what it
    shows, or "focus survives" over a node that cannot hold any. The same panel mounts and
    takes a press through the narrow harness in section c, where none of the three exists.
    """
    report = drive(tmp_path, panel_harness.null_payload())
    node = set(report["surface"]["node"])
    assert node - set(panel_harness.STANDIN_NODE_SURFACE) == {"contains", "focus"}, sorted(node)
    missing = set(panel_harness.STANDIN_NODE_SURFACE) - node
    assert missing == set(), sorted(missing)
    widened = set(report["surface"]["select"]) - node
    assert widened == {"value"}, sorted(widened)


# ---------------------------------------------------------------------------
# b. The page publishes the module and the doors
# ---------------------------------------------------------------------------


def test_the_module_is_published_by_the_server() -> None:
    assert MODULE in server.ASSET_NAMES


def test_the_seam_publishes_both_doors(tmp_path: Path) -> None:
    report = drive(tmp_path, panel_harness.null_payload(), door=DOOR_NONE)
    published = set(report["published_doors"])
    assert {"requestAdvice", "requestDerivation"} <= published, sorted(published)
    # THE CONTROL: the sibling doors read through the same key, so an empty report
    # cannot pass for a page that published nothing because nothing was read.
    assert "requestPower" in published, sorted(published)


# ---------------------------------------------------------------------------
# c. Through the shared harness, which is narrower and feeds the seam grader
# ---------------------------------------------------------------------------


def test_the_panel_mounts_against_an_all_null_payload(tmp_path: Path) -> None:
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["registered"] is True
    assert report["panel_id"] == PANEL_ID
    assert report["load_threw"] is None
    assert report["threw"] is None
    assert report["state"] == panel_harness.STATE_MOUNTED


def test_the_bench_survives_a_press_with_no_door_on_the_shared_stand_in(tmp_path: Path) -> None:
    """The narrow stand-in gives a select no value, and the press still says why.

    Its node is a plain object, so every select here reads undefined and no field can be
    stated. A bench that assumed a string would throw at the seam grader rather than here.
    """
    report = panel_harness.run(tmp_path, MODULE, payload(), clicks=[{"id": ASK_ID}])
    assert report["threw"] is None
    assert report["state"] == panel_harness.STATE_MOUNTED
    last = report["steps"][-1]
    assert last["handlers"] == 1, "the click reached no listener, so this grades nothing"
    assert last["threw"] is None, last["threw"]
    status = next(row for row in report["nodes"] if row["id"] == STATUS_ID)
    assert FIELD_LABELS["target"] in status["text"], status["text"]


# ---------------------------------------------------------------------------
# d. The bench: labelled, no form, nothing prefilled, no default
# ---------------------------------------------------------------------------


def test_the_bench_is_labelled_controls_and_one_button_and_no_form(tmp_path: Path) -> None:
    report = drive(tmp_path, payload())
    rows = report["nodes"]
    assert row_of(rows, FIELD_IDS["target"])["tag"] == "SELECT"
    assert row_of(rows, FIELD_IDS["direction"])["tag"] == "SELECT"
    assert row_of(rows, FIELD_IDS["byproduct_policy"])["tag"] == "SELECT"
    assert row_of(rows, FIELD_IDS["rate"])["tag"] == "INPUT"

    labels = tuple(row["attributes"].get("for") for row in rows if row["tag"] == "LABEL")
    label_count = len(labels)
    assert label_count == EXPECTED_CONTROLS, labels
    assert set(labels) == set(FIELD_IDS.values()), labels

    # ONE BUTTON BEFORE ANY CARD IS LISTED. This payload lists none, so every button in
    # the dump is the bench's.
    buttons = tuple(row["id"] for row in rows if row["tag"] == "BUTTON")
    assert buttons == (ASK_ID,), buttons
    assert "FORM" not in tags(report)
    # THE CONTROL: the tag scan does read the page, or it could not have seen these.
    assert {"SELECT", "INPUT", "BUTTON"} <= tags(report)


def test_every_control_carries_the_class_the_target_box_is_declared_on(tmp_path: Path) -> None:
    report = drive(tmp_path, payload())
    classes = {name: row_of(report["nodes"], FIELD_IDS[name])["class"] for name in FIELD_NAMES}
    wrong = {name: found for name, found in classes.items() if found != "bench-input"}
    assert wrong == {}, wrong


def test_every_control_is_marked_required(tmp_path: Path) -> None:
    report = drive(tmp_path, payload())
    marks = {
        name: row_of(report["nodes"], FIELD_IDS[name])["attributes"].get("aria-required")
        for name in FIELD_NAMES
    }
    assert marks == dict.fromkeys(FIELD_NAMES, "true"), marks


def test_nothing_is_prefilled_and_no_target_is_defaulted(tmp_path: Path) -> None:
    """Every control reads empty at mount, read through what a browser would show.

    A prefill through ``option.selected``, through a first option carrying a value, or
    through ``input.value`` each reads non-empty here. THE CONTROL IS THE LAST HALF: a
    value stated into each control reads back, so an empty read is the control's state
    rather than a stand-in that cannot answer.
    """
    report = drive(tmp_path, payload(), steps=fills())
    mounted = report["steps"][0]["nodes"]
    shown = {name: row_of(mounted, FIELD_IDS[name])["value"] for name in FIELD_NAMES}
    assert shown == dict.fromkeys(FIELD_NAMES, ""), shown

    selected = tuple(row["id"] for row in mounted if row["selected"])
    assert selected == (), selected
    marked = tuple(row["id"] for row in mounted if "selected" in row["attributes"])
    assert marked == (), marked

    stated = {name: row_of(report["nodes"], FIELD_IDS[name])["value"] for name in FIELD_NAMES}
    assert stated == dict(STATED), stated


def test_a_press_with_nothing_stated_reaches_no_door_and_names_all_four(tmp_path: Path) -> None:
    report = drive(tmp_path, payload(), steps=[press_ask()])
    assert report["door_calls"] == []
    status = text_of(report, STATUS_ID)
    named = tuple(label for label in FIELD_LABELS.values() if label not in status)
    assert named == (), status


@pytest.mark.parametrize("missing", FIELD_NAMES)
def test_one_empty_field_is_refused_by_its_name_and_reaches_no_door(
    missing: str, tmp_path: Path
) -> None:
    partial = {name: value for name, value in STATED.items() if name != missing}
    report = drive(tmp_path, payload(), steps=[*fills(partial), press_ask()])
    assert report["door_calls"] == []
    status = text_of(report, STATUS_ID)
    assert FIELD_LABELS[missing] in status, status
    present = tuple(FIELD_LABELS[name] for name in partial if FIELD_LABELS[name] in status)
    assert present == (), status


def test_a_whole_statement_is_not_refused_by_the_panel(tmp_path: Path) -> None:
    # The control for the two arms above: the same press with all four reaches the door.
    report = drive(tmp_path, payload(), steps=[*fills(), press_ask()])
    count = len(door_calls(report, "advice"))
    assert count == 1, report["door_calls"]


# ---------------------------------------------------------------------------
# e. The three lists are the served one and the two Python constants
# ---------------------------------------------------------------------------


def test_the_target_list_is_exactly_the_served_plan_targets(tmp_path: Path) -> None:
    assert list(SERVED_TARGETS) != sorted(SERVED_TARGETS), "this fixture cannot catch a sort"
    report = drive(tmp_path, payload())
    values = tuple(value for value, _text in options_of(report, FIELD_IDS["target"]))
    assert values == ("", *SERVED_TARGETS), values
    # NEVER A TARGET IS IN THE REGISTRY AND NOT IN plan_targets, so a list built from the
    # item rows rather than from the served key would have offered it.
    assert "Desc_NeverATarget_C" not in values, values


def test_a_target_is_labelled_by_display_name_where_the_registry_holds_one(
    tmp_path: Path,
) -> None:
    report = drive(tmp_path, payload())
    labels = dict(options_of(report, FIELD_IDS["target"]))
    assert labels[""] == ""
    for key, name in DISPLAY_NAMES.items():
        assert labels[key] == name, labels
    assert labels["Desc_Unnamed_C"] == "Desc_Unnamed_C", "a key with no row"
    assert labels["Desc_Nulled_C"] == "Desc_Nulled_C", "a key whose name is null"


def test_the_direction_list_is_the_solve_layers(tmp_path: Path) -> None:
    report = drive(tmp_path, payload())
    values = tuple(value for value, _text in options_of(report, FIELD_IDS["direction"]))
    assert values == ("", *optimize.OBJECTIVES), values


def test_the_policy_list_is_the_solve_layers(tmp_path: Path) -> None:
    report = drive(tmp_path, payload())
    values = tuple(value for value, _text in options_of(report, FIELD_IDS["byproduct_policy"]))
    assert values == ("", *ratio.BYPRODUCT_POLICIES), values


def test_a_registry_serving_no_target_list_offers_no_bench_and_says_so(tmp_path: Path) -> None:
    body = registry_body()
    del body[api_registry.PLAN_TARGETS_KEY]
    report = drive(
        tmp_path,
        panel_harness.null_payload(advice=listing(card("Held", "held reason")), registry=body),
    )
    assert not {"SELECT", "INPUT"} & tags(report), sorted(tags(report))
    assert api_registry.PLAN_TARGETS_KEY in panel_text(report), panel_text(report)
    # THE CONTROL, AND THE POINT OF NOT RETURNING EARLY: the world's own cards still list.
    assert "Held" in panel_text(report), panel_text(report)


# ---------------------------------------------------------------------------
# f. Before any request: the visible cards data.advice already holds
# ---------------------------------------------------------------------------


def test_visible_cards_are_listed_and_hidden_cards_are_absent_before_a_request(
    tmp_path: Path,
) -> None:
    shown = card("Headline shown", "Reason shown")
    hidden = card("Headline hidden", "Reason hidden", visible=False)
    report = drive(tmp_path, payload(shown, hidden))
    text = panel_text(report)
    assert "Headline shown" in text, text
    assert "Reason shown" in text, text
    assert "Headline hidden" not in text, text
    assert "Reason hidden" not in text, text
    assert report["door_calls"] == [], "the mount asked for something"


def test_the_hidden_card_is_absent_because_of_its_flag(tmp_path: Path) -> None:
    # The control: the same card with the flag up lists, so the arm above read the flag.
    report = drive(tmp_path, payload(card("Headline hidden", "Reason hidden")))
    assert "Headline hidden" in panel_text(report), panel_text(report)


def test_a_world_with_no_visible_card_says_so(tmp_path: Path) -> None:
    report = drive(tmp_path, payload(card("Gone", "gone reason", visible=False)))
    assert "no visible card" in text_of(report, ANSWER_ID), text_of(report, ANSWER_ID)


def test_no_plan_outcome_is_rendered_before_a_request(tmp_path: Path) -> None:
    report = drive(tmp_path, payload(card("Held", "held reason")))
    assert "plan status" not in panel_text(report), panel_text(report)


# ---------------------------------------------------------------------------
# g. A stated request
# ---------------------------------------------------------------------------


def test_a_stated_request_reads_through_one_door_call_with_exactly_four_parameters(
    tmp_path: Path,
) -> None:
    report = drive(tmp_path, payload(), steps=[*fills(), press_ask()])
    calls = door_calls(report, "advice")
    count = len(calls)
    assert count == 1, calls
    assert calls[0]["params"] == dict(STATED), calls[0]["params"]
    assert door_calls(report, "derivation") == ()


@pytest.mark.parametrize("rate", ["1/3", "007.50", " 3 ", "2.5e3", "not a number"])
def test_the_rate_reaches_the_door_as_the_text_typed(rate: str, tmp_path: Path) -> None:
    """No parse, no trim, no float: whatever was typed is the server's to refuse.

    A panel that parsed the rate would send ``0.333...`` for ``1/3``, and a panel that
    validated it would be a second, drifting copy of the server's grammar.
    """
    report = drive(tmp_path, payload(), steps=[*fills({**STATED, "rate": rate}), press_ask()])
    assert door_calls(report, "advice")[0]["params"]["rate"] == rate


def test_a_request_replaces_the_listing_with_its_own_visible_cards(tmp_path: Path) -> None:
    body = listing(
        card("Answer shown", "Answer reason"),
        card("Answer hidden", "Answer hidden reason", visible=False),
        plan_outcome={"status": "ranked", "redesign": "not-reached"},
    )
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[
            *fills(),
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(body)}},
        ],
    )
    text = panel_text(report)
    assert "Answer shown" in text, text
    assert "Answer reason" in text, text
    assert "Answer hidden" not in text, text
    assert "Before the request" not in text, text


def test_the_answer_says_which_statement_it_answers(tmp_path: Path) -> None:
    # The bench stays editable after an answer, so the region has to say what produced it.
    body = listing(plan_outcome={"status": "ranked", "redesign": "not-reached"})
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": answered(body)}}],
    )
    answer = text_of(report, ANSWER_ID)
    assert DISPLAY_NAMES[STATED["target"]] in answer, answer
    assert STATED["rate"] in answer, answer
    assert STATED["direction"] in answer, answer
    assert STATED["byproduct_policy"] in answer, answer


def test_the_status_of_a_plan_outcome_renders(tmp_path: Path) -> None:
    body = listing(plan_outcome={"status": "status-word-of-the-outcome"})
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": answered(body)}}],
    )
    assert "status-word-of-the-outcome" in text_of(report, ANSWER_ID)


@pytest.mark.parametrize("field", OUTCOME_FIELDS)
def test_each_plan_outcome_field_renders_only_when_present(field: str, tmp_path: Path) -> None:
    value, label = OUTCOME_FIELDS[field]
    words = value if isinstance(value, list) else [value]

    def settled(outcome: Mapping[str, Any]) -> str:
        scratch = tmp_path / ("with" if field in outcome else "without")
        report = drive(
            scratch,
            payload(),
            steps=[
                *fills(),
                press_ask(),
                {"settle": {"call": 0, "outcome": answered(listing(plan_outcome=dict(outcome)))}},
            ],
        )
        return text_of(report, ANSWER_ID)

    present = settled({"status": "ranked", field: value})
    assert label in present, present
    for word in words:
        assert word in present, present

    absent = settled({"status": "ranked"})
    assert f"{label}:" not in absent, absent
    for word in words:
        assert word not in absent, absent
    # THE CONTROL ON THE ABSENT HALF: the outcome was rendered, it just held no such field.
    assert "ranked" in absent, absent


@pytest.mark.parametrize(
    ("field", "label"), [("trimmed", "trimmed recipes"), ("unmade", "unmade items")]
)
def test_an_empty_list_the_outcome_carries_reads_none(
    field: str, label: str, tmp_path: Path
) -> None:
    """Empty is an answer on the wire, and a label over nothing would not say so.

    ``clockspeed/advisor/rules/plan.py::PlanOutcome`` spells it out: an empty trimmed says
    the bound dropped nothing, where an absent one says no search ran. So the two read
    differently here, and a ranked plan's ``trimmed: []`` is the ordinary case.
    """
    outcome = {"status": "ranked", "redesign": "not-reached", field: []}
    report = drive(
        tmp_path,
        payload(),
        steps=[
            *fills(),
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(listing(plan_outcome=outcome))}},
        ],
    )
    assert f"{label}: none" in text_of(report, ANSWER_ID), text_of(report, ANSWER_ID)


def test_a_no_card_outcome_renders_its_reason_and_says_there_is_no_card(tmp_path: Path) -> None:
    """A stated request with no card must say so, never a blank panel.

    A refused trace yields no card, so the outcome is the only thing the answer holds.
    The earlier card going away is what proves the region was rewritten, not left alone.
    """
    outcome = {"status": "no-plan", "redesign": "no-route", "reason": "reason-word-of-no-plan"}
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[
            *fills(),
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(listing(plan_outcome=outcome))}},
        ],
    )
    answer = text_of(report, ANSWER_ID)
    assert "no-plan" in answer, answer
    assert "reason-word-of-no-plan" in answer, answer
    assert "no-route" in answer, answer
    assert "no visible card" in answer, answer
    assert "Before the request" not in answer, answer


def test_an_answer_carrying_no_plan_outcome_says_so(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": answered(listing())}}],
    )
    assert "no plan outcome" in text_of(report, ANSWER_ID), text_of(report, ANSWER_ID)


# ---------------------------------------------------------------------------
# h. A refused or failed request names its word and echoes nothing
# ---------------------------------------------------------------------------


def test_a_400_renders_the_reason_word_and_no_value(tmp_path: Path) -> None:
    """The refused value went out to the door, and it does not come back onto the page.

    THE FIRST ASSERTION IS THE CONTROL. Without it the absence below would pass on a
    panel that never sent the value at all.
    """
    planted = "PLANTED-RATE-VALUE"
    response = contract.bad_request(advice_endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER)
    report = drive(
        tmp_path,
        payload(),
        steps=[
            *fills({**STATED, "rate": planted}),
            press_ask(),
            {"settle": {"call": 0, "outcome": delivered(response)}},
        ],
    )
    assert door_calls(report, "advice")[0]["params"]["rate"] == planted
    text = text_of(report, STATUS_ID) + text_of(report, ANSWER_ID)
    assert contract.REASON_INVALID_PARAMETER in text, text
    assert str(contract.HTTP_BAD_REQUEST) in text, text
    assert planted not in text, text


def test_a_503_renders_the_reason_word(tmp_path: Path) -> None:
    response = contract.unavailable(advice_endpoint.ENDPOINT, contract.REASON_NO_SAVE)
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": delivered(response)}}],
    )
    assert contract.REASON_NO_SAVE in text_of(report, STATUS_ID), text_of(report, STATUS_ID)


def test_a_refused_request_leaves_no_earlier_card_under_its_refusal(tmp_path: Path) -> None:
    # A card still on screen under a refusal reads as that request's answer.
    response = contract.bad_request(advice_endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER)
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": delivered(response)}}],
    )
    assert "Before the request" not in panel_text(report), panel_text(report)


def test_an_unreachable_endpoint_is_named(tmp_path: Path) -> None:
    outcome = {"reached": False, "http": None, "body": None}
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": outcome}}],
    )
    assert "unreachable" in text_of(report, STATUS_ID), text_of(report, STATUS_ID)


def test_an_answer_with_no_readable_body_is_not_called_a_refusal(tmp_path: Path) -> None:
    # A 200 whose body would not parse refused nothing, so the line says what it did do.
    outcome = {"reached": True, "http": contract.HTTP_OK, "body": None}
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": outcome}}],
    )
    status = text_of(report, STATUS_ID)
    assert str(contract.HTTP_OK) in status, status
    assert "no data" in status, status
    assert "refused" not in status, status


def test_a_door_that_refuses_says_so_and_a_later_press_still_asks(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(),
        accepts=[False, True],
        steps=[*fills(), press_ask(), press_ask()],
    )
    count = len(door_calls(report, "advice"))
    expected = 2
    assert count == expected, "the first refusal latched the bench"
    refusal_step = report["steps"][-2]["nodes"]
    line = row_of(refusal_step, STATUS_ID)["text"]
    assert "nothing was sent" in line, line
    # In the past tense, because this line outlives whatever was running.
    assert "is running" not in line, line


def test_a_door_that_throws_puts_none_of_its_text_on_the_page(tmp_path: Path) -> None:
    # An exception's text on this machine can carry an absolute path under a home directory.
    report = drive(tmp_path, payload(), door_throws=True, steps=[*fills(), press_ask()])
    assert report["steps"][-1]["threw"] is None, report["steps"][-1]["threw"]
    count = len(door_calls(report, "advice"))
    assert count == 1, "the door was never reached, so this grades nothing"
    assert "planted-door-failure-text" not in panel_text(report), panel_text(report)
    assert "nothing was sent" in text_of(report, STATUS_ID), text_of(report, STATUS_ID)


def test_a_page_with_no_door_says_so_at_the_press(tmp_path: Path) -> None:
    report = drive(tmp_path, payload(), door=DOOR_NONE, steps=[*fills(), press_ask()])
    assert "no advice door" in text_of(report, STATUS_ID), text_of(report, STATUS_ID)


# ---------------------------------------------------------------------------
# i. A request in flight shows its own state and moves nothing it replaces
# ---------------------------------------------------------------------------


def test_a_request_in_flight_keeps_what_it_replaces_and_shows_its_state(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[*fills(), press_ask()],
    )
    before = report["steps"][0]["nodes"]
    during = report["steps"][-1]["nodes"]

    answer_before = row_of(before, ANSWER_ID)["text"]
    answer_during = row_of(during, ANSWER_ID)["text"]
    assert answer_during == answer_before, "the answer region moved before an answer landed"
    assert "Before the request" in answer_during, "the region was empty, so it grades nothing"

    status_before = row_of(before, STATUS_ID)["text"]
    status_during = row_of(during, STATUS_ID)["text"]
    assert status_during != status_before, "the status line says nothing of the request"
    assert "asking" in status_during, status_during
    length = len(status_during)
    assert length <= STATUS_LINE_CEILING, status_during

    assert row_of(during, ASK_ID)["attributes"].get("aria-disabled") == "true"
    assert row_of(during, ANSWER_ID)["attributes"].get("aria-busy") == "true"


def test_the_status_line_reserves_its_height_in_the_sheet() -> None:
    # No browser runs here, so this is the declared half: the slot exists whatever line
    # sits in it. The rendered half belongs to the ui-auditor.
    sheet = read_asset(STYLESHEET)
    found = re.search(r"\.bench-status \{([^}]*)\}", sheet)
    assert found is not None, "no .bench-status rule"
    assert "min-height" in found.group(1), found.group(1)


def test_a_second_press_in_flight_asks_nothing_and_the_flag_comes_down(tmp_path: Path) -> None:
    body = listing(plan_outcome={"status": "ranked"})
    report = drive(
        tmp_path,
        payload(),
        steps=[
            *fills(),
            press_ask(),
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(body)}},
            press_ask(),
        ],
    )
    count = len(door_calls(report, "advice"))
    expected = 2
    assert count == expected, report["door_calls"]
    settled = report["steps"][-2]["nodes"]
    assert "aria-disabled" not in row_of(settled, ASK_ID)["attributes"]
    assert "aria-busy" not in row_of(settled, ANSWER_ID)["attributes"]


def test_a_press_refused_while_a_derivation_runs_stays_true_after_it_settles(
    tmp_path: Path,
) -> None:
    """The line a refused press leaves is still true once nothing is running.

    Nothing rewrites the status line when a card's derivation settles, so a line saying
    a request IS running would stand there as a false statement about an idle page.
    The press marks no region busy either: the answer region was never asked about.
    """
    held = card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "text"}
    report = drive(
        tmp_path,
        payload(held),
        steps=[
            *fills(),
            {"click": read_id(0)},
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(body)}},
        ],
    )
    # THE CONTROL: the derivation really was in flight, and the press really was refused.
    assert door_calls(report, "derivation") != ()
    assert door_calls(report, "advice") == ()
    status = text_of(report, STATUS_ID)
    assert "nothing was sent" in status, status
    assert "is running" not in status, status
    assert "aria-busy" not in row_of(report["nodes"], ANSWER_ID)["attributes"]


# ---------------------------------------------------------------------------
# j. Tier 3, through the derivation door
# ---------------------------------------------------------------------------


def test_a_derivation_button_calls_its_door_with_the_same_four_and_the_card_id(
    tmp_path: Path,
) -> None:
    """The four that PRODUCED the card, whatever the bench has been changed to since.

    The fill after the answer is the point of the arm. A button reading the live fields
    passes every other test and asks about a card this request never made, because the
    card id is only meaningful under the statement that produced it.
    """
    answer_card = card("Answer shown", "Answer reason")
    body = listing(answer_card, plan_outcome={"status": "ranked"})
    report = drive(
        tmp_path,
        payload(),
        steps=[
            *fills(),
            press_ask(),
            {"settle": {"call": 0, "outcome": answered(body)}},
            {"fill": {"id": FIELD_IDS["rate"], "value": "999"}},
            {"click": read_id(0)},
        ],
    )
    calls = door_calls(report, "derivation")
    count = len(calls)
    assert count == 1, calls
    assert calls[0]["id"] == answer_card["id"]
    assert calls[0]["params"] == dict(STATED), calls[0]["params"]


def test_a_card_held_before_any_request_reads_its_derivation_with_no_statement(
    tmp_path: Path,
) -> None:
    held = card("Held", "held reason")
    report = drive(tmp_path, payload(held), steps=[{"click": read_id(0)}])
    calls = door_calls(report, "derivation")
    count = len(calls)
    assert count == 1, calls
    assert calls[0]["id"] == held["id"]
    assert calls[0]["params"] == {}, calls[0]["params"]


def test_each_card_reads_its_own_derivation(tmp_path: Path) -> None:
    first, second = card("First", "first reason"), card("Second", "second reason")
    report = drive(tmp_path, payload(first, second), steps=[{"click": read_id(1)}])
    assert door_calls(report, "derivation")[0]["id"] == second["id"]


def test_a_derivation_is_shown_as_text_in_a_preformatted_region(tmp_path: Path) -> None:
    """Whole and unparsed: its lines, its spacing and its markup-shaped text survive."""
    tier3 = "line one\n  line two <b>not markup</b>\n\n\tline four"
    held = card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": tier3}
    report = drive(
        tmp_path,
        payload(held),
        steps=[{"click": read_id(0)}, {"settle": {"call": 0, "outcome": answered(body)}}],
    )
    region = row_of(report["nodes"], derivation_id(0))
    assert region["tag"] == "PRE"
    assert region["text"] == tier3, region["text"]
    assert region["hidden"] is False
    assert "B" not in tags(report), sorted(tags(report))


def test_a_derivation_region_is_hidden_until_it_holds_a_derivation(tmp_path: Path) -> None:
    report = drive(tmp_path, payload(card("Held", "held reason")))
    region = row_of(report["nodes"], derivation_id(0))
    assert region["hidden"] is True
    assert region["text"] == "", region["text"]


def test_a_derivation_in_flight_shows_its_state_and_keeps_the_text_it_replaces(
    tmp_path: Path,
) -> None:
    held = card("Held", "held reason")
    body = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "first reading"}
    report = drive(
        tmp_path,
        payload(held),
        steps=[
            {"click": read_id(0)},
            {"settle": {"call": 0, "outcome": answered(body)}},
            {"click": read_id(0)},
        ],
    )
    during = report["nodes"]
    assert row_of(during, derivation_id(0))["text"] == "first reading"
    status = row_of(during, card_status_id(0))["text"]
    assert "reading" in status, status
    assert row_of(during, read_id(0))["attributes"].get("aria-disabled") == "true"


def test_a_refused_derivation_names_its_word_and_shows_no_text(tmp_path: Path) -> None:
    held = card("Held", "held reason")
    good = {"id": held["id"], "rule_id": held["rule_id"], "derivation": "first reading"}
    response = contract.bad_request(
        advice_endpoint.DERIVATION_ENDPOINT, contract.REASON_INVALID_PARAMETER
    )
    report = drive(
        tmp_path,
        payload(held),
        steps=[
            {"click": read_id(0)},
            {"settle": {"call": 0, "outcome": answered(good)}},
            {"click": read_id(0)},
            {"settle": {"call": 1, "outcome": delivered(response)}},
        ],
    )
    status = text_of(report, card_status_id(0))
    assert contract.REASON_INVALID_PARAMETER in status, status
    region = row_of(report["nodes"], derivation_id(0))
    assert region["hidden"] is True
    assert region["text"] == "", "an earlier derivation stood under a refusal"
    # THE CONTROL: the earlier reading was on the page before the refusal landed.
    before = row_of(report["steps"][-2]["nodes"], derivation_id(0))
    assert before["text"] == "first reading", before["text"]


def test_a_derivation_door_that_refuses_says_so_on_the_card(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(card("Held", "held reason")),
        accepts=[False],
        steps=[{"click": read_id(0)}],
    )
    assert "nothing was sent" in text_of(report, card_status_id(0))


def test_a_page_with_no_derivation_door_says_so_on_the_card(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(card("Held", "held reason")),
        door=DOOR_NONE,
        steps=[{"click": read_id(0)}],
    )
    assert "no derivation door" in text_of(report, card_status_id(0))


def test_the_derivation_button_names_its_card_to_a_screen_reader(tmp_path: Path) -> None:
    # Every card's button reads the same, so a list of them announced by name is useless.
    report = drive(tmp_path, payload(card("First", "r"), card("Second", "r")))
    names = (
        row_of(report["nodes"], read_id(0))["attributes"].get("aria-label"),
        row_of(report["nodes"], read_id(1))["attributes"].get("aria-label"),
    )
    assert "First" in str(names[0]), names
    assert "Second" in str(names[1]), names
    # THE VISIBLE WORDS OPEN THE NAME, so a reader speaking what they see still reaches it.
    visible = row_of(report["nodes"], read_id(0))["text"]
    assert str(names[0]).startswith(visible), names


# ---------------------------------------------------------------------------
# k. A null payload is a named refusal and no bench
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("advice", "registry", "named"),
    [
        (None, registry_body(), "/api/advice"),
        (listing(card("Held", "held reason")), None, "/api/registry"),
    ],
    ids=["null-advice", "null-registry"],
)
def test_a_null_payload_renders_a_named_refusal_and_no_bench(
    advice: Mapping[str, Any] | None,
    registry: Mapping[str, Any] | None,
    named: str,
    tmp_path: Path,
) -> None:
    report = drive(tmp_path, panel_harness.null_payload(advice=advice, registry=registry))
    assert named in panel_text(report), panel_text(report)
    offered = {"SELECT", "INPUT", "BUTTON"} & tags(report)
    assert offered == set(), sorted(offered)
    assert "bench" not in {row["class"] for row in report["nodes"]}


def test_the_refusal_is_not_the_panels_ordinary_state(tmp_path: Path) -> None:
    # The control for the arm above: a whole payload builds the bench and names neither.
    report = drive(tmp_path, payload())
    assert {"SELECT", "INPUT", "BUTTON"} <= tags(report), sorted(tags(report))
    assert "did not answer" not in panel_text(report), panel_text(report)


def test_both_null_names_both(tmp_path: Path) -> None:
    report = drive(tmp_path, panel_harness.null_payload())
    text = panel_text(report)
    assert "/api/advice" in text, text
    assert "/api/registry" in text, text


# ---------------------------------------------------------------------------
# l. It computes nothing and writes no markup
# ---------------------------------------------------------------------------


def test_the_panel_issues_no_request_of_its_own() -> None:
    code = code_only(read_asset(MODULE))
    reached = tuple(name for name in NETWORK_PRIMITIVES if name in code)
    assert reached == (), reached


def test_the_request_scan_fires_on_a_planted_fetch() -> None:
    planted = code_only(read_asset(MODULE) + '\nfetch("/api/advice");\n')
    assert "fetch(" in planted


def test_the_panel_builds_no_markup() -> None:
    code = code_only(read_asset(MODULE))
    sunk = tuple(sink for sink in MARKUP_SINKS if sink in code)
    assert sunk == (), sunk


def test_the_markup_scan_reads_code_and_not_prose() -> None:
    # The header says "NO innerHTML" and is not a use of it; a planted one is.
    assert "innerHTML" in read_asset(MODULE), "the header no longer mentions the sink"
    planted = code_only("/* NO innerHTML here */\nnode.innerHTML = value;\n")
    count = planted.count("innerHTML")
    assert count == 1, planted


def test_a_cards_text_arrives_by_textcontent(tmp_path: Path) -> None:
    """Markup-shaped card text renders as itself, and builds no element.

    Under this stand-in an ``innerHTML`` write leaves ``textContent`` empty, so a panel
    using that sink reads as missing text here and not merely as an unsafe one.
    """
    headline = '<img src="x" onerror="1">Headline'
    reason = "<script>Reason</script>"
    report = drive(tmp_path, payload(card(headline, reason)))
    rows = report["nodes"]
    holding = tuple(row["tag"] for row in rows if row["text"] == headline)
    assert "P" in holding, rows
    holding_reason = tuple(row["tag"] for row in rows if row["text"] == reason)
    assert "P" in holding_reason, rows
    planted = {"IMG", "SCRIPT"} & tags(report)
    assert planted == set(), sorted(planted)


def test_nothing_in_the_panel_parses_a_number() -> None:
    code = code_only(read_asset(MODULE))
    parsed = tuple(name for name in NUMBER_PARSERS if name in code)
    assert parsed == (), parsed


def test_the_number_scan_fires_on_a_planted_parse() -> None:
    planted = code_only("var rate = parseFloat(text);\n")
    assert "parseFloat" in planted


def test_nothing_in_the_panel_divides() -> None:
    # Every slash outside a comment and a string, operator or not.
    sites = division_sites(read_asset(MODULE))
    assert sites == (), sites


def test_the_division_sweep_fires_on_a_planted_quotient() -> None:
    sites = division_sites(read_asset(MODULE) + "\nvar leak = rate / den;\n")
    count = len(sites)
    assert count == 1, sites


def test_the_panel_is_wrapped_so_it_cannot_capture_a_siblings_globals() -> None:
    source = read_asset(MODULE)
    assert "(function () {" in source, f"{MODULE} is not wrapped in an IIFE"
    assert source.rstrip().endswith("}());"), f"{MODULE} does not close its IIFE"


# ---------------------------------------------------------------------------
# m. What leaves the page, through app.js's own doors
# ---------------------------------------------------------------------------


def test_the_advice_door_asks_one_get_with_the_four_encoded(tmp_path: Path) -> None:
    """The rate leaves as encoded text, in the table's order, whatever the bench built."""
    report = drive(tmp_path, payload(), door=DOOR_LIVE, steps=[*fills(), press_ask()])
    calls = report["fetch_calls"]
    count = len(calls)
    assert count == 1, calls
    assert calls[0]["url"] == f"{advice_endpoint.ENDPOINT}?{stated_query()}", calls[0]["url"]
    assert calls[0]["method"] == "GET"
    assert calls[0]["has_body"] is False


def test_the_derivation_door_carries_the_id_in_the_path_and_the_query(tmp_path: Path) -> None:
    held = card("Held", "held reason")
    answer = answered(listing(held, plan_outcome={"status": "ranked"}))
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[
            *fills(),
            press_ask(),
            {"resolve": {"call": 0, "status": answer["http"], "body": answer["body"]}},
            {"click": read_id(0)},
        ],
    )
    calls = report["fetch_calls"]
    expected_calls = 2
    count = len(calls)
    assert count == expected_calls, calls
    card_key = held["id"]
    id_name = advice_endpoint.ID_PARAMETER
    assert calls[1]["url"] == (
        f"{advice_endpoint.ENDPOINT}/{card_key}/derivation?{id_name}={card_key}&{stated_query()}"
    ), calls[1]["url"]
    assert calls[1]["method"] == "GET"
    assert calls[1]["has_body"] is False


def test_a_card_held_before_any_request_asks_with_only_its_id(tmp_path: Path) -> None:
    held = card("Held", "held reason")
    report = drive(tmp_path, payload(held), door=DOOR_LIVE, steps=[{"click": read_id(0)}])
    card_key = held["id"]
    assert report["fetch_calls"][0]["url"] == f"/api/advice/{card_key}/derivation?id={card_key}"


def test_a_real_door_delivers_a_listing_and_a_derivation_into_the_panel(tmp_path: Path) -> None:
    """Through ``app.js``'s own delivery path, which the recording stub never enters."""
    held = card("Answer shown", "Answer reason")
    listed = answered(listing(held, plan_outcome={"status": "ranked"}))
    tier3 = answered({"id": held["id"], "rule_id": held["rule_id"], "derivation": "tier three"})
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[
            *fills(),
            press_ask(),
            {"resolve": {"call": 0, "status": listed["http"], "body": listed["body"]}},
            {"click": read_id(0)},
            {"resolve": {"call": 1, "status": tier3["http"], "body": tier3["body"]}},
        ],
    )
    assert "Answer shown" in text_of(report, ANSWER_ID), text_of(report, ANSWER_ID)
    assert text_of(report, derivation_id(0)) == "tier three"


def test_a_real_refusal_reaches_the_panel_with_its_envelope(tmp_path: Path) -> None:
    response = contract.unavailable(advice_endpoint.ENDPOINT, contract.REASON_NO_SAVE)
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[
            *fills(),
            press_ask(),
            {"resolve": {"call": 0, "status": response.http_status, "body": response.payload}},
        ],
    )
    assert contract.REASON_NO_SAVE in text_of(report, STATUS_ID), text_of(report, STATUS_ID)


@pytest.mark.parametrize(
    "params",
    [
        {"target": "x", "rate": "1", "direction": "power"},
        {**STATED, "objective": "power=1"},
        {**STATED, "rate": 1},
    ],
    ids=["short", "widened", "non-string"],
)
def test_the_advice_door_refuses_what_its_table_does_not_take(
    params: Mapping[str, Any], tmp_path: Path
) -> None:
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[{"ask": {"door": "advice", "params": dict(params)}}],
    )
    assert report["steps"][-1]["accepted"] is False
    assert report["fetch_calls"] == []


@pytest.mark.parametrize(
    ("card_key", "params"),
    [("abc", {"objective": "power=1"}), (7, {}), ("abc", None)],
    ids=["widened", "non-string-id", "no-params-object"],
)
def test_the_derivation_door_refuses_what_its_table_does_not_take(
    card_key: Any, params: Any, tmp_path: Path
) -> None:
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[{"ask": {"door": "derivation", "id": card_key, "params": params}}],
    )
    assert report["steps"][-1]["accepted"] is False
    assert report["fetch_calls"] == []


def test_the_derivation_door_accepts_what_its_table_does_take(tmp_path: Path) -> None:
    # The control for the two arms above: the same step through the same door fetches.
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[{"ask": {"door": "derivation", "id": "abc", "params": {}}}],
    )
    assert report["steps"][-1]["accepted"] is True
    count = len(report["fetch_calls"])
    assert count == 1, report["fetch_calls"]


def test_an_id_cannot_step_out_of_its_path_segment(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[{"ask": {"door": "derivation", "id": "../state?x=", "params": {}}}],
    )
    url = report["fetch_calls"][0]["url"]
    assert url.startswith("/api/advice/..%2Fstate%3Fx%3D/derivation?"), url


def test_the_new_doors_share_the_one_in_flight_flag(tmp_path: Path) -> None:
    # One request at a time across the whole page, or the sequential discipline is gone.
    report = drive(
        tmp_path,
        payload(),
        door=DOOR_LIVE,
        steps=[
            {"ask": {"door": "advice", "params": dict(STATED)}},
            {"ask": {"door": "derivation", "id": "abc", "params": {}}},
        ],
    )
    assert report["steps"][-2]["accepted"] is True
    assert report["steps"][-1]["accepted"] is False
    count = len(report["fetch_calls"])
    assert count == 1, report["fetch_calls"]


# ---------------------------------------------------------------------------
# m2. What the rendered audit found, pinned where no browser runs
# ---------------------------------------------------------------------------

#: Each rule the rendered audit measured a fault for, with the declaration that repaired it.
#: Declared values only: whether each one holds at a width is the auditor's to measure.
AUDIT_RULES: Final = (
    (".bench-result .note", "overflow-wrap: anywhere"),
    (".advice-headline", "font-size: 1.05rem"),
    (".advice-headline", "font-weight: 700"),
    (".advice-card .note:not(.advice-headline)", "font-weight: 400"),
    (".advice-derivation", "max-width: 75ch"),
    (".advice-read button", "font-size: 15px"),
    (".bench-result > h3:first-child", "margin-top: 0"),
    ("#panel-advice .bench-field", "flex: 1 1 11rem"),
)

#: A block comment in the sheet, out before a rule is looked for.
CSS_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")


def css_rule(selector: str) -> re.Match[str]:
    """The rule whose whole selector is this one, in the sheet with comments removed.

    Args:
        selector: The selector, spelled as the sheet spells it.

    Returns:
        The match: group 1 is the declarations, and its start is the rule's place.
    """
    sheet = CSS_COMMENT.sub(" ", read_asset(STYLESHEET))
    found = re.search(r"(?:^|[}{])\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", sheet)
    assert found is not None, f"no {selector} rule"
    return found


@pytest.mark.parametrize(("selector", "declaration"), AUDIT_RULES)
def test_the_sheet_declares_what_the_audit_repaired(selector: str, declaration: str) -> None:
    body = css_rule(selector).group(1)
    assert declaration in body, body


def test_the_headline_rule_follows_the_note_rule_it_overrides() -> None:
    # One class each, so the later one wins, and a headline carries both classes.
    assert css_rule(".note").start() < css_rule(".advice-headline").start()


def test_the_answer_region_is_announced_politely(tmp_path: Path) -> None:
    # As the sibling benches' result regions are. A reader waiting on an answer hears it.
    report = drive(tmp_path, payload())
    assert row_of(report["nodes"], ANSWER_ID)["attributes"].get("aria-live") == "polite"


def test_a_card_leads_and_the_outcome_stands_beneath_it(tmp_path: Path) -> None:
    body = listing(
        card("Answer shown", "Answer reason"),
        plan_outcome={"status": "ranked", "redesign": "not-reached"},
    )
    report = drive(
        tmp_path,
        payload(),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": answered(body)}}],
    )
    rows = report["nodes"]
    card_at = next(row["index"] for row in rows if row["text"] == "Answer shown")
    outcome_at = next(row["index"] for row in rows if str(row["text"]).startswith("plan status"))
    assert card_at < outcome_at, (card_at, outcome_at)


#: The two ways an answer rewrites the region, each of which empties it first.
LANDINGS: Final = (
    answered(listing(card("Answer shown", "r"), plan_outcome={"status": "ranked"})),
    delivered(contract.bad_request(advice_endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER)),
)


@pytest.mark.parametrize("landing", LANDINGS, ids=["answered", "refused"])
def test_an_answer_landing_under_a_readers_focus_leaves_it_on_the_ask_button(
    landing: Mapping[str, Any], tmp_path: Path
) -> None:
    """A reader tabbed onto a card while a request ran, and the answer removed that card.

    CONVENTIONS section 13.3: focus destroyed by a repaint drops a keyboard reader to the
    top of the document. THE MIDDLE ASSERTION IS THE CONTROL: focus really was inside the
    region when the answer landed, so the last one is not reading a focus nobody moved.
    """
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[
            *fills(),
            press_ask(),
            {"focus": read_id(0)},
            {"settle": {"call": 0, "outcome": landing}},
        ],
    )
    assert report["steps"][-2]["active"] == read_id(0)
    assert report["steps"][-1]["active"] == ASK_ID


def test_an_answer_landing_leaves_a_focus_outside_the_region_where_it_is(tmp_path: Path) -> None:
    # The reader is changing the rate for the next press. An answer may not take them off it.
    rate_id = FIELD_IDS[advice_endpoint.RATE_PARAMETER]
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[
            *fills(),
            press_ask(),
            {"focus": rate_id},
            {"settle": {"call": 0, "outcome": LANDINGS[0]}},
        ],
    )
    assert report["steps"][-1]["active"] == rate_id


def test_an_answer_landing_takes_no_focus_nobody_gave_it(tmp_path: Path) -> None:
    report = drive(
        tmp_path,
        payload(card("Before the request", "before reason")),
        steps=[*fills(), press_ask(), {"settle": {"call": 0, "outcome": LANDINGS[0]}}],
    )
    assert report["steps"][-1]["active"] is None


# ---------------------------------------------------------------------------
# n. Over the real routes, so nothing above can drift from what they answer
# ---------------------------------------------------------------------------

#: A world and a registry, built when an arm asks.
RealWorld = tuple["WorldModel", "Registry"]


def _ranked_world() -> RealWorld:
    return source_fixtures._ascent()  # noqa: SLF001


def _routed_world() -> RealWorld:
    return source_fixtures._three_locked()  # noqa: SLF001


def _no_route_world() -> RealWorld:
    model = source_fixtures._route_world(())  # noqa: SLF001
    return model, redesign_fixtures._orphan_registry()  # noqa: SLF001


def _route_refused_world() -> RealWorld:
    model = source_fixtures._route_world(())  # noqa: SLF001
    return model, redesign_fixtures._byproduct_registry()  # noqa: SLF001


def _trimmed_world() -> RealWorld:
    names = redesign_fixtures._chain_names()  # noqa: SLF001
    model = source_fixtures._route_world(names)  # noqa: SLF001
    return model, redesign_fixtures._chain_registry()  # noqa: SLF001


#: One synthetic world per state a stated request reaches, each worked by hand in
#: ``tests/surface/test_advice_source.py``, with the outcome and the rule that fires.
REAL_WORLDS: Final[Mapping[str, tuple[Callable[[], RealWorld], str, str, str | None]]] = {
    "ranked": (
        _ranked_world,
        plan_rules.STATUS_RANKED,
        plan_rules.REDESIGN_NOT_REACHED,
        plan_rules.ADOPT_RULE.rule_id,
    ),
    "routed": (
        _routed_world,
        plan_rules.STATUS_NO_PLAN,
        plan_rules.REDESIGN_ROUTED,
        plan_rules.REDESIGN_RULE.rule_id,
    ),
    "routed-and-trimmed": (
        _trimmed_world,
        plan_rules.STATUS_NO_PLAN,
        plan_rules.REDESIGN_ROUTED,
        plan_rules.REDESIGN_RULE.rule_id,
    ),
    "no-route": (
        _no_route_world,
        plan_rules.STATUS_NO_PLAN,
        plan_rules.REDESIGN_NO_ROUTE,
        None,
    ),
    "route-refused": (
        _route_refused_world,
        plan_rules.STATUS_NO_PLAN,
        plan_rules.REDESIGN_ROUTE_REFUSED,
        None,
    ),
}


def data_of(response: contract.Response) -> dict[str, Any]:
    """The data object of a response that must carry one.

    Args:
        response: A 200.

    Returns:
        Its data object.
    """
    data = response.payload["data"]
    assert isinstance(data, dict), response.payload
    return data


def real_table(case: str, directory: Path) -> Mapping[tuple[str, str], contract.Handler]:
    """The real route table over one case's world, with the real source and advisor.

    Args:
        case: A key of :data:`REAL_WORLDS`.
        directory: Where the advice stores live.

    Returns:
        ``(method, template)`` to handler.
    """
    model, registry = REAL_WORLDS[case][0]()
    return source_fixtures._table(directory, model, registry)  # noqa: SLF001


def real_payload(table: Mapping[tuple[str, str], contract.Handler]) -> dict[str, Any]:
    """What a repaint would hand a mount: both GETs of the real table, unstated.

    Args:
        table: The real route table.

    Returns:
        The six-key payload, with ``advice`` and ``registry`` as the routes answered.
    """
    listed = table["GET", advice_endpoint.ENDPOINT]({})
    registered = table["GET", api_registry.ENDPOINT]({})
    return panel_harness.null_payload(advice=data_of(listed), registry=data_of(registered))


def replay(table: Mapping[tuple[str, str], contract.Handler], url: str) -> contract.Response:
    """Answer a URL this page fetched as the server's own dispatch would.

    Split at the question mark, match by the server's matcher, parse strictly, let the path
    capture overwrite the query's name. The socket and the certificate are the only things
    left out, and neither reads a parameter.

    Args:
        table: The real route table.
        url: A URL out of the driver's ``fetch_calls``.

    Returns:
        What the route answers.
    """
    raw_path, _mark, raw_query = url.partition("?")
    by_template: dict[str, dict[str, contract.Handler]] = {}
    for (method, template), handler in table.items():
        by_template.setdefault(template, {})[method] = handler
    matched = server.match_route(by_template, raw_path)
    assert matched is not None, url
    template, captured = matched
    params = dict(
        parse_qsl(raw_query, keep_blank_values=True, strict_parsing=True, errors="strict")
    )
    params.update(captured)
    return table["GET", template](params)


def visible_cards(data: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    """The cards of a real listing body the wire flags visible.

    Args:
        data: The listing's data object.

    Returns:
        Those cards, in listed order.
    """
    return tuple(row for row in data["cards"] if row["visible"] is True)


@pytest.mark.parametrize("case", REAL_WORLDS)
def test_the_panel_renders_what_the_real_route_answers(case: str, tmp_path: Path) -> None:
    """One stated request per state, every word of the real answer on the page.

    THE FIRST THREE ASSERTIONS ARE THE CONTROL. Each says the synthetic world really reached
    the state this case is named for, so a word found below was the word of that state.
    """
    _world, status, redesign, rule = REAL_WORLDS[case]
    table = real_table(case, tmp_path)
    stated = source_fixtures._stated()  # noqa: SLF001
    response = table["GET", advice_endpoint.ENDPOINT](stated)
    data = data_of(response)
    assert set(data) == set(advice_endpoint.STATED_DATA_KEYS)
    outcome = data["plan_outcome"]
    assert (outcome["status"], outcome["redesign"]) == (status, redesign), outcome
    rules = {row["rule_id"] for row in visible_cards(data)}
    plan_family = {plan_rules.ADOPT_RULE.rule_id, plan_rules.REDESIGN_RULE.rule_id}
    assert rules & plan_family == ({rule} if rule else set()), sorted(rules)

    report = drive(
        tmp_path,
        real_payload(table),
        steps=[
            *fills(stated),
            press_ask(),
            {"settle": {"call": 0, "outcome": delivered(response)}},
        ],
    )

    answer = text_of(report, ANSWER_ID)
    for value in outcome.values():
        words = value if isinstance(value, list) else [value]
        absent = tuple(word for word in words if word not in answer)
        assert absent == (), answer
    for row in visible_cards(data):
        assert row["headline"] in answer, answer
        assert row["reason"] in answer, answer
    if not rules:
        assert "no visible card" in answer, answer


def test_a_real_ranked_answer_reads_nothing_trimmed_rather_than_an_empty_label(
    tmp_path: Path,
) -> None:
    # The body that found this: the published seam said trimmed was absent when none, and
    # the real ranked outcome carries it empty, which says the bound dropped nothing.
    table = real_table("ranked", tmp_path)
    stated = source_fixtures._stated()  # noqa: SLF001
    response = table["GET", advice_endpoint.ENDPOINT](stated)
    assert data_of(response)["plan_outcome"]["trimmed"] == []
    report = drive(
        tmp_path,
        real_payload(table),
        steps=[
            *fills(stated),
            press_ask(),
            {"settle": {"call": 0, "outcome": delivered(response)}},
        ],
    )
    assert "trimmed recipes: none" in text_of(report, ANSWER_ID), text_of(report, ANSWER_ID)


def test_the_target_list_is_the_one_the_real_registry_route_serves(tmp_path: Path) -> None:
    table = real_table("ranked", tmp_path)
    data = data_of(table["GET", api_registry.ENDPOINT]({}))
    assert set(data) == set(api_registry.BODY_KEYS), sorted(data)
    served = data[api_registry.PLAN_TARGETS_KEY]
    assert served, "the fixture serves no target, so this arm grades nothing"
    report = drive(tmp_path, real_payload(table))
    values = tuple(value for value, _text in options_of(report, FIELD_IDS[FIELD_NAMES[0]]))
    assert values == ("", *served), values


@pytest.mark.parametrize("case", ["ranked", "routed"])
def test_what_the_doors_send_is_what_the_real_routes_answer(case: str, tmp_path: Path) -> None:
    """The URLs the page fetched, replayed: the listing and tier 3, byte for byte.

    A door spelling a name the route does not take, dropping one of the four from the
    derivation or losing the id out of the path would answer a 400 or another body here,
    so this is what binds the two tables in ``clockspeed/surface/web/app.js`` to the route.
    """
    table = real_table(case, tmp_path)
    stated = source_fixtures._stated()  # noqa: SLF001
    listed = table["GET", advice_endpoint.ENDPOINT](stated)
    first = visible_cards(data_of(listed))[0]
    derivation = table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: first["id"], **stated}
    )
    assert derivation.http_status == contract.HTTP_OK, derivation.payload

    report = drive(
        tmp_path,
        real_payload(table),
        door=DOOR_LIVE,
        steps=[
            *fills(stated),
            press_ask(),
            {"resolve": {"call": 0, "status": listed.http_status, "body": listed.payload}},
            {"click": read_id(0)},
            {"resolve": {"call": 1, "status": derivation.http_status, "body": derivation.payload}},
        ],
    )

    urls = tuple(call["url"] for call in report["fetch_calls"])
    expected_urls = 2
    count = len(urls)
    assert count == expected_urls, urls
    assert contract.encode(replay(table, urls[0]).payload) == contract.encode(listed.payload)
    assert contract.encode(replay(table, urls[1]).payload) == contract.encode(derivation.payload)
    assert text_of(report, derivation_id(0)) == data_of(derivation)["derivation"]


def test_a_held_cards_door_reaches_the_real_route_with_only_its_id(tmp_path: Path) -> None:
    # The other half: a card a repaint listed asks with no statement, as the route requires.
    table = source_fixtures._table(tmp_path)  # noqa: SLF001
    held = real_payload(table)
    first = visible_cards(held["advice"])[0]
    derivation = table["GET", advice_endpoint.DERIVATION_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: first["id"]}
    )
    report = drive(tmp_path, held, door=DOOR_LIVE, steps=[{"click": read_id(0)}])
    url = report["fetch_calls"][0]["url"]
    assert contract.encode(replay(table, url).payload) == contract.encode(derivation.payload)


def test_a_real_route_refusal_renders_its_word_and_no_value(tmp_path: Path) -> None:
    # A rate the real door refuses, so the 400 is the route's own and not this file's.
    planted = source_fixtures.PLANTED
    table = real_table("ranked", tmp_path)
    stated = source_fixtures._stated(rate=planted)  # noqa: SLF001
    response = table["GET", advice_endpoint.ENDPOINT](stated)
    assert response.http_status == contract.HTTP_BAD_REQUEST, response.payload
    report = drive(
        tmp_path,
        real_payload(table),
        steps=[
            *fills(stated),
            press_ask(),
            {"settle": {"call": 0, "outcome": delivered(response)}},
        ],
    )
    # THE CONTROL: the value did go out, so its absence below is the refusal not echoing it.
    assert door_calls(report, "advice")[0]["params"][advice_endpoint.RATE_PARAMETER] == planted
    status = text_of(report, STATUS_ID)
    assert contract.REASON_INVALID_PARAMETER in status, status
    assert planted not in panel_text(report), panel_text(report)


def test_a_card_the_real_ledger_dismissed_is_absent(tmp_path: Path) -> None:
    table = source_fixtures._table(tmp_path)  # noqa: SLF001
    before = real_payload(table)
    first = visible_cards(before["advice"])[0]
    # THE CONTROL: it lists while it is visible.
    shown = drive(tmp_path, before)
    assert first["headline"] in text_of(shown, ANSWER_ID), text_of(shown, ANSWER_ID)

    recorded = table["POST", advice_endpoint.STATE_ENDPOINT](
        {advice_endpoint.ID_PARAMETER: first["id"], advice_endpoint.STATE_PARAMETER: "dismissed"}
    )
    assert recorded.http_status == contract.HTTP_OK, recorded.payload

    after = real_payload(table)
    flagged = [row for row in after["advice"]["cards"] if row["id"] == first["id"]]
    assert [row["visible"] for row in flagged] == [False], "the wire stopped serving it flagged"
    report = drive(tmp_path, after)
    assert first["headline"] not in panel_text(report), panel_text(report)


# ---------------------------------------------------------------------------
# o. The audit harness's own bodies, so what the auditor sees is what this file grades
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", audit_harness.AUDIT_TARGETS)
def test_each_audit_state_is_selectable_and_renders_through_the_panel(
    target: str, tmp_path: Path
) -> None:
    """The harness's registry offers the target, and its answer lands whole.

    A target the panel could not select would leave the auditor one state short, and a body
    the panel read as a refusal would show the auditor something else under the same name.
    """
    registered = audit_harness.CANNED["GET", api_registry.ENDPOINT]
    held = audit_harness.CANNED["GET", advice_endpoint.ENDPOINT]
    answer = audit_harness.STATED_ANSWERS[target]
    statement = {**STATED, advice_endpoint.TARGET_PARAMETER: target}
    report = drive(
        tmp_path,
        panel_harness.null_payload(advice=data_of(held), registry=data_of(registered)),
        steps=[
            *fills(statement),
            press_ask(),
            {"settle": {"call": 0, "outcome": delivered(answer)}},
        ],
    )
    assert door_calls(report, "advice")[0]["params"] == statement
    text = text_of(report, ANSWER_ID)
    outcome = data_of(answer)["plan_outcome"]
    for value in outcome.values():
        words = value if isinstance(value, list) else [value]
        absent = tuple(word for word in words if word not in text)
        assert absent == (), text
    for row in data_of(answer)["cards"]:
        assert row["headline"] in text, text


def test_the_audit_listing_shows_its_visible_cards_and_hides_the_dismissed_one(
    tmp_path: Path,
) -> None:
    held = data_of(audit_harness.CANNED["GET", advice_endpoint.ENDPOINT])
    report = drive(
        tmp_path,
        panel_harness.null_payload(
            advice=held, registry=data_of(audit_harness.CANNED["GET", api_registry.ENDPOINT])
        ),
    )
    text = text_of(report, ANSWER_ID)
    shown = tuple(row["headline"] for row in held["cards"] if row["visible"])
    hidden = tuple(row["headline"] for row in held["cards"] if not row["visible"])
    assert hidden, "the harness lists no hidden card, so this grades nothing"
    absent = tuple(headline for headline in shown if headline not in text)
    assert absent == (), text
    leaked = tuple(headline for headline in hidden if headline in text)
    assert leaked == (), text
