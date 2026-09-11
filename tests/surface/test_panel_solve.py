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
:func:`test_the_panel_divides_once_and_only_inside_the_approximation` measures
that claim structurally - it counts division SITES in the code with comments
and string literals blanked, and requires the single survivor to sit inside the
function that builds the approximate label.
"""

from __future__ import annotations

import itertools
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from tests.surface import panel_harness

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

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

#: Renderings that mean a value reached the page without being read.
NON_RENDERINGS: Final = ("undefined", "[object Object]", "NaN", "null")

#: How long one driver run may take before it is a failure rather than a slow box.
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

var data = request.data;
if (request.door) {
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

if (captured) {
  mountPanel(captured, data);
  steps.push({
    kind: "mount",
    state: stateOf(),
    threw: mountThrew,
    matched: 1,
    nodes: dump(section(), null)
  });

  request.steps.forEach(function (spec) {
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
    steps.push(step);
  });
}

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
    solve_calls: solveCalls,
    standin_surface: {
      node: Object.getOwnPropertyNames(makeNode("div")).sort(),
      document: Object.keys(globalThis.document).sort()
    }
  })
);
"""


def drive(
    tmp_path: Path,
    data: Mapping[str, Any],
    *,
    module: str | Path = MODULE,
    door: bool = True,
    accepts: Sequence[bool] = (),
    steps: Sequence[Mapping[str, Any]] = (),
) -> Mapping[str, Any]:
    """Mount ``panel_solve.js`` with a recording door and drive the given steps.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        data: The six-key payload. Use :func:`panel_harness.null_payload`.
        module: A shipped asset name, or a path to a planted module.
        door: Whether to install ``data.actions.requestSolve``. False models
            the seam grader's own harness, where ``actions`` is absent.
        accepts: What the stub returns for call 0, call 1 and so on. A call
            past the end of this sequence is REFUSED, so an unexpected extra
            call is refused loudly rather than quietly served.
        steps: In order, ``{"fill": {"match": {...}, "value": "..."}}``,
            ``{"click": {...}}`` or
            ``{"settle": {"call": 0, "outcome": {...}}}``.

    Returns:
        The report described on :func:`panel_harness.run`, plus ``solve_calls``
        - one record per stub call carrying ``param_keys``, ``params``,
        ``types``, ``callback_is_function`` and ``accepted``. Node rows carry
        an extra ``value``, which is what a reader would have typed.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so the solve bench was never mounted and "
            "nothing was graded. This FAILS rather than skipping: a gate that "
            "skips its checks reports PASS while measuring nothing."
        )

    target = panel_harness.WEB_DIR / module if isinstance(module, str) else module
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
                "web_dir": str(panel_harness.WEB_DIR),
                "module": str(target),
                "data": dict(data),
                "door": door,
                "accepts": list(accepts),
                "steps": [dict(step) for step in steps],
            }
        ).encode("ascii")
    )

    # Fixed argv, no shell. The interpreter is resolved off PATH because an
    # absolute interpreter path may not be written into a tracked file.
    completed = subprocess.run(
        [node, str(script), str(request)],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_SECONDS,
        check=False,
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
    report = drive(tmp_path, panel_harness.null_payload(), door=False)
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
    report = drive(tmp_path, panel_harness.null_payload(), door=False)
    assert report["state"] == panel_harness.STATE_MOUNTED
    after = drive(
        tmp_path,
        panel_harness.null_payload(),
        door=False,
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


def test_the_panel_divides_once_and_only_inside_the_approximation(tmp_path: Path) -> None:
    """Exactly one division site in the whole module, inside the label builder.

    NON-NEGOTIABLE 6, ENFORCED IN THE RENDER PATH. Every other value on this
    page is a pair of integers rendered as a pair of integers. The one
    exception is the decimal the operator ruled may sit beside a pair when it
    is labelled an approximation - so there is exactly one place a float may be
    made, and this arm says which.
    """
    sites = division_sites(read_module())
    assert len(sites) == 1, f"{len(sites)} division site(s): {sites}"
    assert sites[0][1] == "approximateDecimal", sites[0]

    # The panel was driven for its side effect on the arm above being about a
    # module that actually renders - a module that divided nowhere because it
    # rendered nothing would pass the count and mean nothing.
    report = drive(
        tmp_path,
        panel_harness.null_payload(registry=_registry()),
        accepts=[True],
        steps=_settled(PLAN_OUTCOME),
    )
    assert "3.3333" in panel_text(report), panel_text(report)


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
# j. Character set
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
