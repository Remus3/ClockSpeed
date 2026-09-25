"""The Optimize bench - the door onto a route that answered 200 and nobody called.

What is covered, and the authority for each arm:

a. THE DEFECT THIS PANEL CLOSES, STATED AS AN ARM. ``/api/optimize`` was live
   and answered 200 against real data for as long as nothing on the page ever
   asked it. A route nobody can reach is indistinguishable from a route that was
   never built. :func:`test_the_page_publishes_an_optimize_door` is the arm that
   goes red if the door is ever removed again.
b. THE SEAM ARMS RUN THE SHIPPED MODULE through ``tests/surface/panel_harness.py``
   against the all-null payload every panel must survive. That harness passes
   ``data`` as JSON, so no door can be present in it - which is exactly the
   state the seam grader mounts every panel in.
c. THE DOOR ARMS RUN THE SHIPPED MODULE TOO, under a small local driver that can
   put a FUNCTION on the payload. Written out here rather than shared with
   ``tests/surface/test_panel_power.py``'s or
   ``tests/surface/test_panel_solve.py``'s: importing one test module into
   another makes a collection-order dependency out of a stand-in, and the seam
   being exercised is the published one either way.
d. NO DIVISION IN THE RENDER PATH, WHICH IS CS-962'S ACCEPTANCE IN AS MANY
   WORDS. Graded STRUCTURALLY, by parsing the shipped source for a division
   operator, rather than by checking that one rendered value looks right - a
   value arm passes on every input where the quotient happens to be exact, and
   the whole point is the inputs where it is not.
e. THE EXACT PAIR REACHES THE SCREEN. The fixture is the REAL endpoint's output
   over the REAL synthetic corpus, so the rendered text is graded against what
   the serializer actually emits rather than against a shape this file believes
   in.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar and asserted before it is iterated, and every detector used to
prove an absence is run against a planted POSITIVE and against a control that
would false-positive a naive implementation.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.solve import optimize, ratio
from clockspeed.surface import server
from clockspeed.surface.api import contract, solve
from tests.surface import panel_harness
from tests.surface.test_panel_solve import (
    TRUNCATION_CASES,
    division_sites,
    truncated_decimal,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

#: The shipped module this file grades.
MODULE: Final = "panel_optimize.js"

#: The seam file that publishes the door.
SEAM: Final = "app.js"

#: The id it registers with the seam.
PANEL_ID: Final = "optimize"

#: The door name this panel reaches for on the payload.
DOOR_NAME: Final = "requestOptimize"

#: The seven inputs the bench builds - the six required and the one optional.
FIELD_IDS: Final = (
    "optimize-targets",
    "optimize-candidates",
    "optimize-unlocked",
    "optimize-raw_items",
    "optimize-byproduct_policy",
    "optimize-objective",
    "optimize-backend",
)

#: How many fields the bench must build.
EXPECTED_FIELDS: Final = 7

#: How long the driver may take before it is a hang rather than a run.
NODE_TIMEOUT_SECONDS: Final = 60.0

#: Every way a browser script reaches the network. A panel that used any of
#: these would be issuing its own request, which the seam forbids.
NETWORK_PRIMITIVES: Final = (
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "navigator.sendBeacon",
    "import(",
)

#: A division operator applied to something, outside a comment and outside a
#: string. Matched as an operator rather than as the character, so the "/" in a
#: rendered num/den separator and the "/" inside a route path do not fire it.
#: The tail admits "=" for a compound ``x /= y`` and a unary sign or negation for
#: ``x / -y`` - CS-1027, the two spellings the earlier ``[(\w]`` tail missed.
DIVISION: Final = re.compile(r"[)\]\w\s]/(?!/|\*)\s*[(\w=+\-!~]")

#: The division spellings the planted-positive arm plants, one case each. CS-1027
#: added the last two: an adversarial probe found the detector's tail class
#: missed a compound assignment (``x /= y``) and a negated divisor (``x / -y``),
#: neither of which starts its right-hand side with a word character or a paren.
PLANTED_QUOTIENTS: Final = (
    "var leak = rational.num / rational.den;",
    "var leak = rational.num;\nleak /= rational.den;",
    "var leak = rational.num / -rational.den;",
)

#: One readable id per planting, in the same order.
PLANTED_QUOTIENT_IDS: Final = ("quotient", "compound-assignment", "negated-divisor")

#: A comment or a string literal, blanked before every source scan so a "/" in
#: prose or in a path cannot read as an operator - and so a paragraph SAYING
#: "no innerHTML" cannot read as an innerHTML. Block comments and strings come
#: first in the alternation, because a "//" inside either is not a line comment.
NON_CODE: Final = re.compile(
    r"/\*[\s\S]*?\*/" r'|"(?:[^"\\\n]|\\.)*"' r"|'(?:[^'\\\n]|\\.)*'" r"|//[^\n]*",
    re.MULTILINE,
)

#: The minimum DOM stand-in this panel touches, plus a recording door. It is
#: deliberately NOT a browser: nothing here lays anything out, and no arm below
#: claims anything about focus or about pixels.
_DRIVER: Final = r""""use strict";
const fs = require("fs");
const path = require("path");
const request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function makeNode(tag) {
  const node = {
    tagName: String(tag).toUpperCase(),
    childNodes: [],
    attributes: {},
    listeners: {},
    id: "",
    className: "",
    _text: "",
    get firstChild() {
      return this.childNodes.length ? this.childNodes[0] : null;
    },
    get textContent() {
      if (this.childNodes.length) {
        return this.childNodes.map((child) => child.textContent).join("");
      }
      return this._text;
    },
    set textContent(value) {
      this.childNodes = [];
      this._text = String(value);
    },
    appendChild(child) {
      this.childNodes.push(child);
      return child;
    },
    removeChild(child) {
      const at = this.childNodes.indexOf(child);
      if (at >= 0) {
        this.childNodes.splice(at, 1);
      }
      return child;
    },
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attributes, name)
        ? this.attributes[name]
        : null;
    },
    removeAttribute(name) {
      delete this.attributes[name];
    },
    addEventListener(kind, handler) {
      this.listeners[kind] = this.listeners[kind] || [];
      this.listeners[kind].push(handler);
    }
  };
  return node;
}

globalThis.document = { createElement: makeNode };

let mount = null;
globalThis.registerPanel = function (id, fn) {
  mount = { id: id, fn: fn };
};

const calls = [];
function recordingDoor(params, onSettled) {
  calls.push({ params: params, settle: onSettled });
  return request.door_accepts;
}

const source = fs.readFileSync(path.join(request.web_dir, request.module), "utf8");
let loadThrew = null;
try {
  (0, eval)(source);
} catch (failure) {
  loadThrew = String(failure && failure.message);
}

const data = JSON.parse(JSON.stringify(request.data));
if (request.door_present) {
  data.actions = data.actions || {};
  data.actions[request.door_name] = recordingDoor;
}

const root = makeNode("section");
let mountThrew = null;
if (mount) {
  try {
    mount.fn(root, data);
  } catch (failure) {
    mountThrew = String(failure && failure.message);
  }
}

function walk(node, rows, depth) {
  rows.push({
    depth: depth,
    tag: node.tagName,
    id: node.id,
    class: node.className,
    text: node._text,
    listens: Object.keys(node.listeners)
  });
  node.childNodes.forEach((child) => walk(child, rows, depth + 1));
  return rows;
}

function fill(id, value) {
  let hit = 0;
  (function hunt(node) {
    if (node.id === id) {
      node.value = value;
      hit += 1;
    }
    node.childNodes.forEach(hunt);
  })(root);
  return hit;
}

function press() {
  const found = [];
  (function hunt(node) {
    if (node.tagName === "BUTTON") {
      found.push(node);
    }
    node.childNodes.forEach(hunt);
  })(root);
  if (found.length !== 1) {
    return found.length;
  }
  (found[0].listeners.click || []).forEach((handler) => handler());
  return 1;
}

const steps = [];
request.steps.forEach((step) => {
  if (step.fill) {
    steps.push({ kind: "fill", filled: fill(step.fill.id, step.fill.value) });
  }
  if (step.press) {
    steps.push({ kind: "press", buttons: press(), text: root.textContent });
  }
  if (step.settle) {
    const at = calls[step.settle.call];
    if (at) {
      at.settle(step.settle.outcome);
    }
    steps.push({ kind: "settle", text: root.textContent });
  }
});

process.stdout.write(
  JSON.stringify({
    registered: mount !== null,
    panel_id: mount ? mount.id : null,
    load_threw: loadThrew,
    mount_threw: mountThrew,
    text: root.textContent,
    nodes: walk(root, [], 0),
    calls: calls.map((call) => call.params),
    steps: steps
  })
);
"""


# ---------------------------------------------------------------------------
# Helpers
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
    """The source with comments and string literals blanked out.

    A scan over raw text cannot tell a division operator from the slash in a
    route path, nor an ``innerHTML`` sink from a paragraph promising there is
    none. A detector that cannot tell them apart is one whose silence means
    nothing.

    Args:
        source: The shipped module text.

    Returns:
        The same length of text with every comment and string literal replaced
        by spaces, so offsets are preserved and nothing new is introduced.
    """
    return NON_CODE.sub(lambda match: " " * len(match.group(0)), source)


def drive(
    tmp_path: Path,
    data: Mapping[str, Any],
    *,
    door: bool = True,
    accepts: bool = True,
    steps: Sequence[Mapping[str, Any]] = (),
) -> Mapping[str, Any]:
    """Mount the shipped module under the local driver and run the steps.

    Args:
        tmp_path: A directory the driver may write scratch files into.
        data: The payload handed to the mount, before the door is added.
        door: Whether to put a recording door on ``data.actions``.
        accepts: What that door returns - False models the page refusing.
        steps: ``fill``, ``press`` and ``settle`` entries, applied in order.

    Returns:
        The driver's report.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so no panel was mounted and nothing was graded. "
            "This FAILS rather than skipping: a gate that skips its checks reports "
            "PASS while measuring nothing."
        )

    scratch = tmp_path / "optimize_bench"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "sliceA_optimize_driver.cjs"
    script.write_bytes(_DRIVER.encode("ascii"))
    payload = scratch / "request.json"
    payload.write_bytes(
        json.dumps(
            {
                "web_dir": str(panel_harness.WEB_DIR),
                "module": MODULE,
                "data": dict(data),
                "door_present": door,
                "door_name": DOOR_NAME,
                "door_accepts": accepts,
                "steps": [dict(step) for step in steps],
            }
        ).encode("ascii")
    )

    completed = subprocess.run(
        [node, str(script), str(payload)],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"the optimize bench driver exited {completed.returncode}: {completed.stderr}")
    report: Mapping[str, Any] = json.loads(completed.stdout)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["mount_threw"] is None, report["mount_threw"]
    return report


def envelope(data: Mapping[str, Any]) -> dict[str, Any]:
    """A 200 outcome carrying one real ``/api/optimize`` body.

    Args:
        data: The endpoint's data object.

    Returns:
        The outcome shape ``app.js`` hands a settled callback.
    """
    return {"reached": True, "http": contract.HTTP_OK, "body": {"status": "ok", "data": data}}


def real_body() -> dict[str, Any]:
    """The C5 result, produced by the REAL endpoint over the REAL corpus.

    A hand-typed fixture agrees with whatever this module believes the shape is,
    by construction, and stays green through the exact serializer defect it is
    meant to catch - CONVENTIONS.md section 7.2.

    Returns:
        The ``data`` object of the endpoint's 200.
    """
    from tests.solve import synthetic as corpus  # noqa: PLC0415

    class _Provider:
        def registry(self) -> Any:
            return corpus.solve_registry()

    response = solve.optimize_handler(_Provider())(
        {
            "targets": f"{corpus.SOLVE_TRINKET_ITEM}=30",
            "candidates": f"{corpus.ALT_GADGET_RECIPE},{corpus.STD_GADGET_RECIPE}",
            "unlocked": f"{corpus.ALT_GADGET_RECIPE},{corpus.STD_GADGET_RECIPE}",
            "raw_items": corpus.SOLVE_ORE_ITEM,
            "byproduct_policy": ratio.BYPRODUCT_SINKABLE,
            "objective": f"{optimize.OBJECTIVE_BUILDINGS}=1",
        }
    )
    assert response.http_status == contract.HTTP_OK, response.payload
    body = response.payload["data"]
    assert isinstance(body, dict)
    return body


# ---------------------------------------------------------------------------
# (a) the door exists at all
# ---------------------------------------------------------------------------


def test_the_page_publishes_an_optimize_door() -> None:
    """THE ARM THE WHOLE PANEL EXISTS FOR.

    ``/api/optimize`` answered 200 against real data for as long as nothing on
    this page called it, and the page's own route table said "not probed"
    beside it - true, and not the same thing as unaskable. The seam now
    publishes ``requestOptimize`` and this is what goes red if it is removed.
    """
    seam = read_asset(SEAM)
    # THE DOOR NAME IS READ OUT OF THE CODE, with comments and strings blanked,
    # so a paragraph merely DISCUSSING the door cannot stand in for one.
    assert DOOR_NAME in code_only(seam), f"{SEAM} publishes no {DOOR_NAME} door"
    # THE REQUEST TARGET IS READ OUT OF THE RAW TEXT, because it IS a string
    # literal - the same stripper that makes the check above meaningful would
    # blank the very thing this half is looking for.
    assert '"/api/optimize?"' in seam, f"{SEAM} names no /api/optimize request target"


def test_the_module_is_published_by_the_server() -> None:
    # A panel module the server does not name is a file the page cannot load,
    # and STATIC_ROUTES is a literal by design, so the name has to be added on
    # purpose. This is what turns forgetting it into a red suite.
    assert MODULE in server.ASSET_NAMES


# ---------------------------------------------------------------------------
# (b) the seam arms, through the shared harness
# ---------------------------------------------------------------------------


def test_the_panel_mounts_against_an_all_null_payload(tmp_path: Path) -> None:
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["registered"] is True
    assert report["panel_id"] == PANEL_ID
    assert report["load_threw"] is None
    assert report["threw"] is None
    assert report["state"] == panel_harness.STATE_MOUNTED


def test_the_bench_builds_every_field_even_with_no_registry(tmp_path: Path) -> None:
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    built = tuple(
        row["id"] for row in report["nodes"] if row["id"] and row["id"].startswith("optimize-")
    )
    count = len(built)
    assert count == EXPECTED_FIELDS
    assert sorted(built) == sorted(FIELD_IDS)


def test_the_bench_declares_every_name_the_endpoint_requires() -> None:
    # Reconciled against the endpoint's own frozenset rather than against a list
    # typed here, so a rename shows up as one red arm naming both sides.
    source = read_asset(MODULE)
    missing = tuple(
        name for name in sorted(solve.OPTIMIZE_REQUIRED) if f'name: "{name}"' not in source
    )
    count = len(missing)
    assert count == 0, missing
    optional = tuple(
        name for name in sorted(solve.OPTIMIZE_OPTIONAL) if f'name: "{name}"' not in source
    )
    optional_count = len(optional)
    assert optional_count == 0, optional


def test_the_panel_issues_no_request_of_its_own() -> None:
    source = read_asset(MODULE)
    reached = tuple(name for name in NETWORK_PRIMITIVES if name in source)
    count = len(reached)
    assert count == 0, reached


def test_the_panel_builds_no_markup() -> None:
    # COMMENTS COME OUT FIRST. This file's own header says "NO innerHTML", and a
    # scan over raw text would find that sentence and call it a sink - the
    # mirror of the fault the sweep exists for.
    code = code_only(read_asset(MODULE))
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert sink not in code, sink


def test_the_markup_sink_scan_survives_the_comment_stripper() -> None:
    assert "innerHTML" in read_asset(MODULE), "the header no longer mentions the sink at all"
    planted = code_only("/* NO innerHTML here */\nnode.innerHTML = value;\n")
    occurrences = planted.count("innerHTML")
    assert occurrences == 1, planted


def test_the_panel_is_wrapped_so_it_cannot_capture_a_siblings_globals() -> None:
    """The bench's helpers must not land in the page's shared global scope.

    THE FAULT THIS CLOSES IS SILENT AND WOULD NOT THROW. These are classic
    scripts sharing one scope, and ``panel_solve.js`` declared ``FIELDS``,
    ``textOf`` and a dozen more at top level until CS-1026 wrapped it too.
    Declared globally in both, the last script ``index.html`` loads would win
    every one of them - and a mount closes over the BINDING rather than a
    snapshot, so the solve bench would start building this bench's fields on
    the next repaint. ``tests/surface/test_panel_global_scope.py`` measures the
    whole page for that fault behaviourally; this arm is the static shape pin.
    """
    source = read_asset(MODULE)
    assert "(function () {" in source, f"{MODULE} is not wrapped in an IIFE"
    assert source.rstrip().endswith("}());"), f"{MODULE} does not close its IIFE"


# ---------------------------------------------------------------------------
# (d) no division anywhere in the render path
# ---------------------------------------------------------------------------


def test_nothing_in_the_render_path_divides() -> None:
    code = code_only(read_asset(MODULE))
    offences = tuple(match.group(0) for match in DIVISION.finditer(code))
    count = len(offences)
    assert count == 0, offences


@pytest.mark.parametrize("quotient", PLANTED_QUOTIENTS, ids=PLANTED_QUOTIENT_IDS)
def test_the_division_detector_fires_on_a_planted_quotient(quotient: str) -> None:
    # A detector that matched nothing would make the arm above green over a
    # panel that divided in every line. Every spelling is planted on its own,
    # so a detector that saw one of them cannot pass for one that sees all.
    planted = code_only(read_asset(MODULE)) + "\n" + quotient + "\n"
    offences = tuple(match.group(0) for match in DIVISION.finditer(planted))
    count = len(offences)
    assert count == 1, offences


def test_the_tokenizer_sweep_finds_no_bare_slash_in_the_module() -> None:
    """The INDEPENDENT control: a tokenizer that counts every slash, not a pattern.

    ``tests/surface/test_panel_solve.py::executable_source`` blanks block comments
    and string literals and :func:`~tests.surface.test_panel_solve.division_sites`
    counts every slash that survives, operator or not. It shares no code with
    :data:`DIVISION`, so the two agreeing on zero is two readings rather than one
    read twice - and CS-1027 was found exactly where the pattern had a blind
    spot the character count does not.
    """
    sites = division_sites(read_asset(MODULE))
    assert sites == (), f"{len(sites)} bare slash(es) survive: {sites}"


@pytest.mark.parametrize("quotient", PLANTED_QUOTIENTS, ids=PLANTED_QUOTIENT_IDS)
def test_the_tokenizer_sweep_fires_on_every_planted_spelling(quotient: str) -> None:
    """The control is proved able to fire, on each spelling the detector must see."""
    sites = division_sites(read_asset(MODULE) + "\n" + quotient + "\n")
    count = len(sites)
    assert count == 1, sites


def test_the_division_detector_does_not_fire_on_the_pair_separator() -> None:
    # The control that keeps the arm above from being a rule about the CHARACTER
    # "/" - which the panel prints between a numerator and a denominator, and
    # which appears in every route path in the file's prose.
    offences = tuple(DIVISION.finditer(code_only('var PAIR_MARK = "/";\n// see /api/optimize\n')))
    count = len(offences)
    assert count == 0


# ---------------------------------------------------------------------------
# (e) the rendered answer, driven through the real endpoint
# ---------------------------------------------------------------------------


def test_the_chosen_selection_and_the_exact_pairs_reach_the_screen(tmp_path: Path) -> None:
    body = real_body()
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]

    selection = body["selection"]
    assert isinstance(selection, list)
    chosen = len(selection)
    assert chosen > 0, "the corpus stopped producing a selection, so this arm grades nothing"
    for name in selection:
        assert str(name) in text, text

    plan = body["plan"]
    assert isinstance(plan, dict)
    steps_out = plan["steps"]
    assert isinstance(steps_out, list)
    step_count = len(steps_out)
    assert step_count > 0
    for row in steps_out:
        machines = row["machines"]
        assert f"{machines['num']}/{machines['den']}" in text, text

    score = body["score"]
    assert isinstance(score, dict)
    assert f"{score['num']}/{score['den']}" in text, text


def test_no_rendered_amount_stands_alone_as_a_decimal(tmp_path: Path) -> None:
    # A decimal standing alone would be a rounded number presented as an exact
    # one, which is the single rendering this panel is forbidden to produce.
    body = real_body()
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    decimals = tuple(re.findall(r"\d+\.\d+", text))
    count = len(decimals)
    assert count > 0, "no reading aid was rendered at all, so this arm grades nothing"
    for decimal in decimals:
        at = text.index(decimal)
        assert "display only" in text[at : at + len(decimal) + 20], (decimal, text)


def test_every_approximation_is_the_exact_truncation_of_its_pair(tmp_path: Path) -> None:
    """CS-1028: this panel's copy of ``approximateDecimal`` is graded for its DIGITS.

    The arms above prove a decimal is labelled and that nothing divides; neither
    notices a decimal whose digits are wrong, and a digit-corrupting mutant of
    this copy was measured surviving every arm in this file. The oracle is the
    solve bench's own table and truncation, imported rather than restated, so
    one case added there grades every copy. Each pair must render EXACTLY ONCE,
    so a matching rendering from some other leaf of the body cannot stand in for
    the row under test.
    """
    body = real_body()
    plan = body["plan"]
    assert isinstance(plan, dict)
    plan["targets"] = {
        f"Desc_Case{index}_C": {"num": num, "den": den}
        for index, (num, den) in enumerate(TRUNCATION_CASES)
    }
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    for num, den in TRUNCATION_CASES:
        # A digit or a sign may not precede the pair, or "120/1" would count as "0/1"
        # and "-22/7" as "22/7".
        opened = re.compile(rf"(?<![\d-]){num}/{den} \(approx ")
        renderings = len(opened.findall(text))
        assert renderings == 1, f"{num}/{den} rendered {renderings} time(s): {text}"
        rendered = f"{num}/{den} (approx {truncated_decimal(num, den)}, display only)"
        assert rendered in text, f"expected {rendered!r} on the page: {text}"


def test_the_bench_omits_a_blank_backend_rather_than_sending_it_empty(
    tmp_path: Path,
) -> None:
    # An empty backend name is not a backend the endpoint knows, so sending one
    # would turn "let the endpoint choose" into a refusal.
    report = drive(tmp_path, panel_harness.null_payload(), steps=[{"press": True}])
    calls = report["calls"]
    count = len(calls)
    assert count == 1, calls
    assert sorted(calls[0]) == sorted(solve.OPTIMIZE_REQUIRED), calls[0]


def test_a_stated_backend_is_sent(tmp_path: Path) -> None:
    # The other direction, so the omission above is not just a bench that can
    # never send the optional name at all.
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"fill": {"id": "optimize-backend", "value": "exact"}}, {"press": True}],
    )
    filled = [step for step in report["steps"] if step["kind"] == "fill"][-1]
    assert filled["filled"] == 1, "the backend field was not found, so nothing was filled"
    calls = report["calls"]
    count = len(calls)
    assert count == 1, calls
    assert calls[0][solve.PARAM_BACKEND] == "exact", calls[0]


def test_a_bench_with_no_door_says_so_rather_than_looking_dead(tmp_path: Path) -> None:
    report = drive(tmp_path, panel_harness.null_payload(), door=False, steps=[{"press": True}])
    assert report["steps"][-1]["buttons"] == 1
    assert "published no optimize door" in report["steps"][-1]["text"]


def test_a_refused_request_is_reported_rather_than_waited_on(tmp_path: Path) -> None:
    report = drive(tmp_path, panel_harness.null_payload(), accepts=False, steps=[{"press": True}])
    assert "the page refused the request" in report["steps"][-1]["text"]


def test_a_refusal_envelope_is_rendered_and_not_swallowed(tmp_path: Path) -> None:
    # The reason and the detail sit OUTSIDE data, which is why app.js hands the
    # panel the whole envelope; a bench that read only data would render every
    # 400 as silence.
    refusal = contract.bad_request(solve.OPTIMIZE_ENDPOINT, contract.REASON_OBJECTIVE_UNDEFINED)
    outcome = {"reached": True, "http": refusal.http_status, "body": dict(refusal.payload)}
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": outcome}}],
    )
    text = report["steps"][-1]["text"]
    assert contract.REASON_OBJECTIVE_UNDEFINED in text, text
    assert "refused with 400" in text
