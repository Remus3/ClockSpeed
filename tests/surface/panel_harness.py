"""CS-962 slice S2 - mount ONE dashboard panel under node and report what it built.

WHAT THIS IS FOR. Four panel slices each need the same thing: load the shipped
``app.js`` seam, load one shipped panel module, hand its mount a synthetic
``data`` payload, and read back the DOM it produced. Without a shared harness
each of those four test modules carries its own copy, and four copies of a DOM
stand-in drift into four different definitions of what a panel may do.

THE CONTRACT THIS FILE PUBLISHES, AND WHY IT IS THE SHAPE IT IS
===============================================================

**THE STAND-IN DOM IS DELIBERATELY NOT WIDENED.** It implements exactly what
``tests/surface/test_panel_seam.py`` implements (its stand-in is at lines
163-312 of that file) and nothing more. A panel therefore has:

    on the document   createElement, createTextNode, getElementById,
                      querySelectorAll, activeElement
    on a node         appendChild, removeChild, setAttribute, getAttribute,
                      removeAttribute, addEventListener, firstChild,
                      textContent, tagName, className, id, hidden, childNodes,
                      attributes, scrollWidth, clientWidth

and NOTHING else. In particular there is NO ``classList``, NO ``dataset``, NO
``children``, NO ``insertBefore``, NO ``remove()``, NO ``closest``, NO
``querySelector`` on a node, NO ``createDocumentFragment`` and NO ``focus()``.

THE REASON IS NOT MINIMALISM, IT IS THAT A WIDER HARNESS WOULD CERTIFY PANELS
THE REAL GRADER REJECTS. ``test_panel_seam.py::test_the_seam_mounts_every_
registered_panel`` mounts every shipped panel against the narrow stand-in and
requires state ``mounted``. If this harness offered ``classList`` and a panel
author used it, that panel would be green here and red there - in an arm no
panel slice owns, discovered only after the merge. A test harness may be
narrower than production; it must never be wider than the gate it feeds.

**THE ONE DELIBERATE DIFFERENCE: addEventListener RECORDS.** In the seam
grader ``addEventListener`` is a no-op (test_panel_seam.py:204-206). Here it
stores the handler in a ``WeakMap`` keyed by the node, so :func:`run` can
invoke it. This is safe in the only direction that matters: during MOUNT both
versions behave identically - both return ``undefined`` and neither fires
anything - so a panel that mounts green here mounts green there. The recorded
handler runs only when a caller explicitly asks for a click. The listener store
is a ``WeakMap`` and NOT a property on the node precisely so the property
surface a panel can see stays byte-for-byte the grader's; :func:`mount`
reports that surface in ``standin_surface`` so the claim is measured rather
than asserted in prose.

**THE EVENT OBJECT IS A STUB.** A driven handler is called with an object
carrying only ``type``, ``target``, ``preventDefault`` and ``stopPropagation``.
The grader has no event dispatch at all, so anything here is new ground; it is
kept to four members so a panel cannot lean on a browser Event it will never
be handed by the gate.

**THE PAGE'S OWN REPAINT IS FROZEN.** ``app.js`` calls ``refresh()`` at load
(its last line), which fetches every route and then mounts every registered
panel with ITS payloads. That would overwrite the caller's ``data``. So the
harness installs a ``fetch`` that returns a promise which never settles: the
load-time repaint parks at its first await, ``panelPayloads`` stays null, and
the only mount that ever happens is the one this harness drives with the
caller's payload. Panels issue no requests of their own - the seam forbids it -
so nothing else notices.

**THE MOUNT GOES THROUGH app.js, NOT AROUND IT.** The harness calls the seam's
own ``mountPanel(entry, data)`` with an ``{id, mount}`` entry of the shape
``app.js`` builds at its line 508. That means the section, its ``panel`` class,
its ``panel-<id>`` element id, the emptying, the try/catch containment and the
``data-panel-state`` marker are all the shipped behaviour rather than a second
description of it. The harness wraps the panel's mount function first, so a
throw is RECORDED before ``app.js`` swallows it - a harness that could not
report a failure would grade nothing.

**NODE IS REQUIRED, NOT SKIPPED AROUND.** :func:`run` calls ``pytest.fail``
when node is absent. A skipped gate reports PASS while measuring nothing.

DUPLICATION WITH THE SEAM GRADER IS INTENTIONAL, AND IT IS ENFORCED RATHER
THAN TRUSTED. ``test_panel_seam.py`` grades the seam; if it imported this
module it would depend on the thing it grades, so the dependency runs the other
way - this module imports the grader's stand-in TEXT and measures it. Every
:func:`run` executes the grader's own ``makeNode`` and ``document`` in a
separate vm context and asserts, as an EQUALITY and never a subset, that this
harness offers neither one member more nor one member less. A subset check
would pass forever while the harness grew permissive, which is exactly the
failure it has to catch: adding ``classList`` to the node above would leave all
four panel suites green while certifying panels the real grader rejects, and
four suites built on one widened input agree with each other and with nothing
else. NO MEMBER NAME IS TYPED INTO THIS FILE'S CHECK - a typed list is the copy
that goes stale, which is the fault rather than the repair. The pinned tuples
below are checked against the same measurement, so prose and code cannot drift
apart either. The one documented exception is named explicitly and narrowly by
:data:`RECORDING_MEMBER`: it is a member BOTH publish, so the difference is one
of behaviour and never of surface, and a node that has actually been listened
to is measured too - a listener store kept ON the node rather than in the
``WeakMap`` would show up there as an extra property.
"""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.surface import config
from tests.surface import test_panel_seam

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

#: The shipped asset directory, read from the module that owns the answer.
WEB_DIR: Final = config.default_web_dir()

#: The seam itself. Loaded before any panel module, because a panel calls
#: ``registerPanel`` at load.
SEAM_SCRIPT: Final = "app.js"

#: The markers ``app.js`` writes onto a panel section (app.js:470-471).
STATE_MOUNTED: Final = "mounted"
STATE_FAILED: Final = "failed"

#: The six payload keys ``app.js`` hands every mount (app.js:544-559). Every
#: one may be null, and under the seam grader's canned probes four of them
#: always are - so a panel that renders a null payload without throwing is the
#: acceptance rule, not a nicety.
PAYLOAD_KEYS: Final = ("health", "world", "registry", "advice", "audit", "plan")

#: Every own property a panel can see on a stand-in element. Pinned here so a
#: caller can assert against the contract, MEASURED at run time into the
#: report's ``standin_surface``, and checked by :func:`_check_standin` against
#: the surface the seam grader actually builds - so neither this tuple nor the
#: stand-in can drift away from the gate they feed.
STANDIN_NODE_SURFACE: Final = (
    "addEventListener",
    "appendChild",
    "attributes",
    "childNodes",
    "className",
    "clientWidth",
    "firstChild",
    "getAttribute",
    "hidden",
    "id",
    "removeAttribute",
    "removeChild",
    "scrollWidth",
    "setAttribute",
    "tagName",
    "textContent",
)

#: Every member of the stand-in document. There is no ``querySelector``.
#: Checked the same way :data:`STANDIN_NODE_SURFACE` is.
STANDIN_DOCUMENT_SURFACE: Final = (
    "activeElement",
    "createElement",
    "createTextNode",
    "getElementById",
    "querySelectorAll",
)

#: The seam grader's stand-in, taken as TEXT from the module that owns it. This
#: is the whole point of the check: the surface is derived by RUNNING the
#: grader's own ``makeNode``, so no member name is retyped here and there is no
#: second list to keep in step. The import direction is deliberate - the grader
#: must not import this module, because it grades the seam this module drives.
GRADER_STANDIN_SOURCE: Final = test_panel_seam.HARNESS_SOURCE

#: THE ONE DOCUMENTED DIFFERENCE, named so the exception is visible in the
#: check rather than being a hole in it. Here it records the handler into a
#: WeakMap; in the grader it is a no-op. Both PUBLISH it, so it is a difference
#: of behaviour and never of surface, and :func:`_check_standin` refuses to let
#: it become one.
RECORDING_MEMBER: Final = "addEventListener"

#: How long one node run may take before it is a failure rather than a slow box.
NODE_TIMEOUT_SECONDS: Final = 60.0

#: Distinguishes the scratch files of repeated calls sharing one tmp_path.
_RUN_COUNTER: Final[Iterator[int]] = itertools.count()

#: The node side of the harness. Written to the caller's temporary directory
#: rather than tracked as an asset, because scaffolding it is and an asset it
#: is not. It takes ONE argument: the path of a JSON request file carrying the
#: web directory, the panel module path, the payload and the click list.
_HARNESS_SOURCE: Final = r""""use strict";

var fs = require("node:fs");
var path = require("node:path");
var vm = require("node:vm");

var request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
var webDir = request.web_dir;

/* Handlers live OUTSIDE the node, so the property surface stays the grader's. */
var listeners = new WeakMap();

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
    /*
      Appending is what puts a node in the document, so it is what makes an id
      resolvable - the same rule the seam grader's stand-in follows.
    */
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
    /*
      THE ONE DELIBERATE WIDENING, and it is a widening of what the TEST can
      observe rather than of what the PANEL can do. The seam grader discards
      the handler; this records it so a caller can drive a button. During
      mount both behave identically, so a panel green here is green there.
    */
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

/*
  getElementById answers null for an id the page does not declare, exactly as a
  real one does. The declared set is parsed out of the SHIPPED index.html, so
  an id the page stops declaring stops resolving here too.
*/
var markup = fs.readFileSync(path.join(webDir, "index.html"), "utf8");
var declared = Object.create(null);
var idPattern = /\bid="([^"]+)"/g;
var seenId = idPattern.exec(markup);
while (seenId !== null) {
  declared[seenId[1]] = true;
  seenId = idPattern.exec(markup);
}

var known = Object.create(null);

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
  A PROMISE THAT NEVER SETTLES. app.js calls refresh() on its last line; left
  to run it would fetch every route and then remount every registered panel
  with ITS payloads, overwriting the caller's. Parking the repaint at its first
  await leaves panelPayloads null, so the only mount that happens is the one
  driven below. A rejection would NOT do - app.js catches it and repaints with
  an all-null payload, which is the same overwrite wearing a different hat.
*/
globalThis.fetch = function () {
  return new Promise(function () {
    return undefined;
  });
};

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
        /* RECORDED BEFORE app.js SWALLOWS IT, then rethrown so the seam's own
           containment and its failed marker are the shipped behaviour. */
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

function listenTypes(node) {
  var held = listeners.get(node) || [];
  return held.map(function (entry) {
    return entry.type;
  });
}

/*
  A FLAT PRE-ORDER DUMP starting AT the panel's own section, which is index 0.
  Text nodes are included, spelled #TEXT, so a caller can see exactly what was
  appended rather than inferring it from a parent's joined text. "text" is the
  stand-in's textContent: a leaf reports its own text, a parent reports its
  children's joined with a space.
*/
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
      listens: listenTypes(node)
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

var steps = [];

if (captured) {
  mountPanel(captured, request.data);
  steps.push({
    kind: "mount",
    state: stateOf(),
    threw: mountThrew,
    nodes: dump(section(), null)
  });

  request.clicks.forEach(function (match) {
    var nodes = [];
    var rows = dump(section(), nodes);
    var hits = rows.filter(function (row) {
      return matches(row, match);
    });
    var step = {
      kind: "click",
      match: match,
      matched: hits.length,
      handlers: 0,
      threw: null,
      state: stateOf(),
      nodes: rows
    };
    if (hits.length === 1) {
      var target = nodes[hits[0].index];
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
      step.state = stateOf();
      step.nodes = dump(section(), null);
    }
    steps.push(step);
  });
}

/*
  THE GRADER'S OWN STAND-IN, MEASURED RATHER THAN RETYPED. request.grader_source
  is the text of test_panel_seam.py's HARNESS_SOURCE, handed over by the Python
  side from the module that OWNS it. It runs in a SEPARATE vm context whose fs
  reads index.html and nothing else, so its main() dies at its first load() and
  its app.js never reaches vm.runInThisContext - which is THIS context, not the
  box. Its stdout, stderr and console are sinks, so the rejection it parks on
  cannot reach the JSON this script writes. What survives is exactly what is
  wanted: its makeNode and its document, measured the same way ours are.
*/
function graderStandin() {
  var box = {
    require: function (name) {
      if (name !== "node:fs") {
        return require(name);
      }
      return {
        readFileSync: function (target, encoding) {
          if (String(target).slice(-10) !== "index.html") {
            throw new Error("the surface probe reads index.html and nothing else");
          }
          return fs.readFileSync(target, encoding);
        }
      };
    },
    process: {
      argv: ["node", "grader_standin", webDir, "clean"],
      stdout: { write: function () { return undefined; } },
      stderr: { write: function () { return undefined; } }
    },
    console: {
      log: function () { return undefined; },
      warn: function () { return undefined; },
      error: function () { return undefined; }
    }
  };
  vm.createContext(box);
  vm.runInContext(request.grader_source, box, { filename: "grader_standin.cjs" });
  if (typeof box.makeNode !== "function" || !box.document) {
    throw new Error("the seam grader published no makeNode/document to measure");
  }
  return {
    node: Object.getOwnPropertyNames(box.makeNode("div")).sort(),
    document: Object.keys(box.document).sort()
  };
}

/*
  THE ONE DELIBERATE DIFFERENCE, MEASURED. addEventListener records into a
  WeakMap rather than onto the node, so a node that HAS been listened to must
  still carry exactly the grader's property names. A store kept on the node
  would appear here and nowhere else.
*/
function listenedSurface() {
  var probe = makeNode("div");
  probe.addEventListener("click", function () {
    return undefined;
  });
  return Object.getOwnPropertyNames(probe).sort();
}

var graderSurface = graderStandin();

var last = steps.length ? steps[steps.length - 1] : null;

process.stdout.write(
  JSON.stringify({
    module: path.basename(request.module),
    registered: Boolean(captured),
    panel_id: captured ? captured.id : null,
    load_threw: loadThrew,
    state: stateOf(),
    threw: mountThrew,
    nodes: last ? last.nodes : [],
    steps: steps,
    standin_surface: {
      node: Object.getOwnPropertyNames(makeNode("div")).sort(),
      document: Object.keys(globalThis.document).sort(),
      node_after_listener: listenedSurface(),
      grader_node: graderSurface.node,
      grader_document: graderSurface.document
    }
  })
);
"""


#: Why a wider stand-in is a defect, quoted into the failure so the reader of
#: a red arm does not have to find this module to learn what broke.
_WIDER_IS_WORSE: Final = (
    "A test harness may be narrower than the gate it feeds and must never be "
    "wider: a member offered here and not there certifies a panel that "
    "test_panel_seam.py rejects, and it does it in all four panel suites at "
    "once, so they agree with each other and with nothing else."
)

#: Why the pinned tuples are checked against the same measurement.
_PIN_IS_A_COPY: Final = (
    "This tuple is the only hand-typed list in the file and is therefore the "
    "one thing here that can go stale. It is checked against the measurement "
    "rather than trusted."
)


def _compare(
    measured_label: str,
    measured: tuple[str, ...],
    expected_label: str,
    expected: tuple[str, ...],
    why: str,
) -> None:
    """Fail unless two member lists are EQUAL - never a subset, in either direction.

    A subset check is what the mutant this guards against walks straight
    through: it passes forever while the harness grows more permissive.

    Args:
        measured_label: What the left-hand list is, for the failure message.
        measured: The member names measured on this harness.
        expected_label: What the right-hand list is.
        expected: The member names it must equal.
        why: The sentence explaining why the difference matters.
    """
    widened = sorted(set(measured) - set(expected))
    narrowed = sorted(set(expected) - set(measured))
    difference = (
        ""
        if measured == expected
        else (
            f"{measured_label} is not {expected_label}. "
            f"Offered here and not there: {widened}. "
            f"Offered there and not here: {narrowed}. "
            f"{why} "
            f"Measured {measured_label}: {list(measured)}. "
            f"Measured {expected_label}: {list(expected)}."
        )
    )
    # NO EARLY RETURN. tests/test_liveness.py refuses a grader carrying a bare
    # return before its assertions, because that is the shape a gutted check
    # wears - and this helper is the one that pins the stand-in surface, so it
    # of all things must not be able to exit without comparing. The difference
    # is bound to a scalar first so the rendered expression cannot say more
    # than the message does.
    assert not difference, difference


def _check_standin(report: Mapping[str, Any], module: str) -> None:
    """Fail unless the stand-in is member-for-member the seam grader's surface.

    THIS RUNS ON EVERY :func:`run`, not in one arm of one suite, because this
    module is not collected by pytest - it does not match ``test_*.py`` - so a
    test function written here would never be executed and would report PASS
    while measuring nothing. Riding on the call every panel suite already makes
    is what gives the check a chance to fire.

    Four equalities and one named exception:

    1. The node surface equals the grader's MEASURED node surface.
    2. The document surface equals the grader's MEASURED document surface.
    3. A node that has been listened to STILL equals the grader's node surface,
       which is what proves the recording store lives in the ``WeakMap`` rather
       than on the node.
    4. The pinned tuples in this file equal the same measurement, so the
       documentation cannot drift away from the code.

    And :data:`RECORDING_MEMBER` must be published by BOTH, so the documented
    exception stays a difference of behaviour and never becomes one of surface.

    Args:
        report: The node side's report, carrying ``standin_surface``.
        module: The panel module name, for the failure message.
    """
    surface = report["standin_surface"]
    here = tuple(surface["node"])
    there = tuple(surface["grader_node"])
    _compare(
        f"the stand-in node surface the harness measured mounting {module}",
        here,
        "the node surface tests/surface/test_panel_seam.py builds",
        there,
        _WIDER_IS_WORSE,
    )
    _compare(
        "the stand-in document surface the harness measured",
        tuple(surface["document"]),
        "the document surface tests/surface/test_panel_seam.py builds",
        tuple(surface["grader_document"]),
        _WIDER_IS_WORSE,
    )
    _compare(
        "the node surface measured AFTER a click listener was attached",
        tuple(surface["node_after_listener"]),
        "the node surface tests/surface/test_panel_seam.py builds",
        there,
        f"{RECORDING_MEMBER} is documented to record into a WeakMap precisely "
        f"so it leaves no trace on the node. A member here and not there is "
        f"that store leaking onto the node. " + _WIDER_IS_WORSE,
    )
    if RECORDING_MEMBER not in here or RECORDING_MEMBER not in there:
        pytest.fail(
            f"the one documented difference is that {RECORDING_MEMBER} RECORDS "
            f"in this harness and is a no-op in the seam grader - a difference "
            f"of behaviour inside a member they BOTH publish. One of them no "
            f"longer publishes it, so the exception has become a difference of "
            f"SURFACE, which is the widening this check refuses. "
            f"Harness: {list(here)}. Grader: {list(there)}."
        )
    _compare(
        "the node surface measured at run time",
        here,
        "the STANDIN_NODE_SURFACE tuple pinned in this module",
        STANDIN_NODE_SURFACE,
        _PIN_IS_A_COPY,
    )
    _compare(
        "the document surface measured at run time",
        tuple(surface["document"]),
        "the STANDIN_DOCUMENT_SURFACE tuple pinned in this module",
        STANDIN_DOCUMENT_SURFACE,
        _PIN_IS_A_COPY,
    )


#: The row fields a click match and :func:`nodes_matching` may name. Anything
#: else is a typo, and a typo that merely selected nothing would read as a
#: panel that never built the node.
MATCH_FIELDS: Final = ("class", "id", "tag", "text")


def _check_match(match: Mapping[str, str]) -> None:
    """Reject an empty or misspelled node match.

    Args:
        match: The fields a caller wants matched.

    Raises:
        ValueError: If the match is empty or names an unmatchable field.
    """
    if not match:
        raise ValueError(f"an empty match selects every node; name one of {list(MATCH_FIELDS)}")
    unknown = sorted(set(match) - set(MATCH_FIELDS))
    if unknown:
        raise ValueError(f"a node cannot be matched on {unknown}; matchable: {list(MATCH_FIELDS)}")


def null_payload(**overrides: Any) -> dict[str, Any]:
    """The six-key payload with every key null, then the given keys replaced.

    Every acceptance rule in CS-962 starts here: a panel must render an
    all-null payload without throwing, because four of the six keys are null
    under the seam grader's canned probes.

    Args:
        **overrides: Payload keys to set. Each must be one of
            :data:`PAYLOAD_KEYS`; anything else is a typo the caller wants to
            hear about rather than a key the panel will silently never read.

    Returns:
        A fresh dict carrying exactly the six keys ``app.js`` hands a mount.

    Raises:
        ValueError: If an override names a key the seam does not publish.
    """
    unknown = sorted(set(overrides) - set(PAYLOAD_KEYS))
    if unknown:
        raise ValueError(
            f"the panel seam publishes no payload key {unknown}; "
            f"it hands a mount exactly {list(PAYLOAD_KEYS)}"
        )
    payload: dict[str, Any] = dict.fromkeys(PAYLOAD_KEYS)
    payload.update(overrides)
    return payload


def run(
    tmp_path: Path,
    module: str | Path,
    data: Mapping[str, Any],
    clicks: Sequence[Mapping[str, str]] = (),
) -> Mapping[str, Any]:
    """Mount one panel module against ``data``, drive ``clicks``, report the DOM.

    Args:
        tmp_path: A directory the harness may write scratch files into.
            Repeated calls sharing one directory do not collide.
        module: A shipped asset name such as ``"panel_solve.js"``, resolved
            under the web directory, or a :class:`Path` to a module anywhere -
            which is how a caller plants a deliberately throwing stand-in.
        data: The payload handed to the mount. Use :func:`null_payload`.
        clicks: Zero or more match dicts, applied in order after the mount.
            A match names one or more of :data:`MATCH_FIELDS` and must select
            EXACTLY ONE node in the panel's current tree; anything else is a
            caller error and fails loudly.

    Returns:
        A report carrying:

        * ``module`` - the module's basename.
        * ``registered`` - whether the module registered a panel at load.
        * ``panel_id`` - the id it registered, or None.
        * ``load_threw`` - the message if merely LOADING the module threw.
        * ``state`` - ``"mounted"``, ``"failed"``, or None if nothing mounted.
        * ``threw`` - the mount's throw message, recorded before ``app.js``
          swallowed it, or None.
        * ``nodes`` - the flat pre-order dump after the last step. Each row
          carries ``index``, ``depth``, ``parent``, ``tag``, ``id``,
          ``class``, ``attributes``, ``text`` and ``listens``. Index 0 is the
          panel's own section.
        * ``steps`` - one entry per step: the mount, then one per click. A
          click entry adds ``match``, ``matched``, ``handlers`` and ``threw``.
        * ``standin_surface`` - the measured ``node`` and ``document`` member
          lists, so a caller can pin what a panel is allowed to touch, plus
          ``node_after_listener`` and the grader's own ``grader_node`` and
          ``grader_document``, which :func:`_check_standin` has already
          required this run to equal.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so no panel was mounted and nothing was "
            "graded. This FAILS rather than skipping: a gate that skips its "
            "checks reports PASS while measuring nothing."
        )

    target = WEB_DIR / module if isinstance(module, str) else module
    if not target.is_file():
        pytest.fail(f"there is no panel module at {target}")

    for match in clicks:
        _check_match(match)

    scratch = tmp_path / f"panel_harness_{next(_RUN_COUNTER)}"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "panel_harness.cjs"
    script.write_bytes(_HARNESS_SOURCE.encode("ascii"))
    request = scratch / "request.json"
    request.write_bytes(
        json.dumps(
            {
                "web_dir": str(WEB_DIR),
                "module": str(target),
                "data": dict(data),
                "clicks": [dict(match) for match in clicks],
                "grader_source": GRADER_STANDIN_SOURCE,
            }
        ).encode("ascii")
    )

    # Fixed argv, no shell. The interpreter is resolved off PATH because an
    # absolute interpreter path may not be written into a tracked file, and
    # every other argument is a path this function just wrote.
    completed = subprocess.run(
        [node, str(script), str(request)],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"the panel harness exited {completed.returncode} mounting "
            f"{target.name}: {completed.stderr.strip()}"
        )

    report: Mapping[str, Any] = json.loads(completed.stdout)
    _check_standin(report, target.name)
    for step in report["steps"]:
        if step["kind"] == "click" and step["matched"] != 1:
            pytest.fail(
                f"the click match {step['match']} selected {step['matched']} "
                f"nodes in {target.name}; a click must name exactly one. "
                f"The tree held: {[row['tag'] + '#' + row['id'] for row in step['nodes']]}"
            )
    return report


def mount(tmp_path: Path, module: str | Path, data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Mount one panel module against ``data`` and report the DOM it built.

    :func:`run` with no clicks. This is the call every panel slice makes for
    its null-payload arm.

    Args:
        tmp_path: A directory the harness may write scratch files into.
        module: A shipped asset name, or a path to a planted module.
        data: The payload handed to the mount.

    Returns:
        The report described on :func:`run`.
    """
    return run(tmp_path, module, data)


def nodes_matching(
    report: Mapping[str, Any], match: Mapping[str, str]
) -> tuple[Mapping[str, Any], ...]:
    """Every row of the report's final dump matching all the given fields.

    THE MATCH IS A DICT AND NOT KEYWORD ARGUMENTS because one of the four
    fields is spelled ``class``, which is a Python keyword and cannot be a
    keyword argument at all. One shape for both this and :func:`run`'s
    ``clicks`` is worth more than the shorter call.

    Args:
        report: A report from :func:`mount` or :func:`run`.
        match: Fields to match exactly, among :data:`MATCH_FIELDS`. ``tag``
            is compared case-insensitively.

    Returns:
        The matching rows, in document order.

    Raises:
        ValueError: If the match is empty or names a field that is not
            matchable - a typo would otherwise select nothing and read as a
            panel that never built the node.
    """
    _check_match(match)
    wanted = {key: value.upper() if key == "tag" else value for key, value in match.items()}
    return tuple(
        row
        for row in report["nodes"]
        if all(str(row[key]) == value for key, value in wanted.items())
    )
