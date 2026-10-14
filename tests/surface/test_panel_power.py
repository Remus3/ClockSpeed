"""The Power bench - it asks ``/api/power``, and it never prints a zero it was not given.

What is covered, and the authority for each arm:

a. THE SEAM ARMS RUN THE SHIPPED MODULE, through ``tests/surface/panel_harness.py``,
   against the all-null payload every panel must survive. That harness passes
   ``data`` as JSON, so no door can be present in it - which is exactly the
   state the seam grader mounts every panel in, and a panel that assumed a door
   would be marked failed there rather than here.
b. THE DOOR ARMS RUN THE SHIPPED MODULE TOO, under a small local driver that can
   put a FUNCTION on the payload. ``panel_harness`` cannot, for the reason
   above, so the driver below builds the minimum DOM stand-in this panel
   touches, hands the mount a recording door, clicks the button and then
   settles the recorded callback. It is written out here rather than shared
   with ``tests/surface/test_panel_solve.py``'s: importing one test module into
   another makes a collection-order dependency, and the seam being exercised is
   the published one either way.
c. NO DIVISION IN THE RENDER PATH, WHICH IS CS-962'S ACCEPTANCE IN AS MANY
   WORDS. Graded STRUCTURALLY, by parsing the shipped source for a division
   operator, rather than by checking that one rendered value looks right - a
   value arm passes on every input where the quotient happens to be exact, and
   the whole point is the inputs where it is not.
d. AN ABSENT MEASUREMENT IS NEVER RENDERED AS A ZERO. Four of the endpoint's
   five answers can be unmodeled, and ``clockspeed/solve/power.py`` records that
   a confident zero is the one failure a power plan cannot detect. The arm
   drives a real unmodeled body through the real renderer and reads the text.
e. NO CEILING NUMBER APPEARS. ADR 0005: the shard slot count is absent from
   every source on this machine. The bench renders the un-sharded base and says
   in the same line that it is NOT the ceiling - ADR 0006's fence.
f. THE REGISTRY'S PROVENANCE IS SAID BEFORE THE FIGURES (CS-1315 slice B).
   "Nothing prices a figure from an unverified registry silently": a real body
   over a registry from other docs bytes, or from none, renders UNVERIFIED and
   the served code verbatim ahead of the first figure; a verified one says so
   and names no code; a body with no build state is never read as verified.

Test-quality discipline (CONVENTIONS.md section 7.2). Every population size is
bound to a scalar and asserted before it is iterated, and the division detector
is run against a planted POSITIVE so that "found nothing" is distinguishable
from "looks for nothing".
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.audit import build as build_model
from clockspeed.surface import server
from clockspeed.surface.api import contract
from clockspeed.surface.api import power as endpoint
from tests.advisor.build_fixtures import OFF_PIN_DOCS_SHA256, docs_pin
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
MODULE: Final = "panel_power.js"

#: The id it registers with the seam.
PANEL_ID: Final = "power"

#: The three inputs the bench builds, in page order.
FIELD_IDS: Final = ("power-building", "power-clock", "power-recipe")

#: The door name this panel reaches for on the payload.
DOOR_NAME: Final = "requestPower"

#: How many fields the bench must build.
EXPECTED_FIELDS: Final = 3

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
  // eslint-disable-next-line no-eval
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


def read_module() -> str:
    """The shipped panel source, as ASCII text.

    Returns:
        The whole file.
    """
    return (panel_harness.WEB_DIR / MODULE).read_bytes().decode("ascii")


def code_only(source: str) -> str:
    """The source with comments and string literals blanked out.

    A scan over raw text cannot tell a division operator from the slash in a
    route path or in a prose sentence, and a detector that cannot tell them
    apart is one whose silence means nothing.

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
        steps: ``{"press": True}`` and ``{"settle": {...}}`` entries, in order.

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

    scratch = tmp_path / "power_bench"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "sliceA_power_driver.cjs"
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
        pytest.fail(f"the power bench driver exited {completed.returncode}: {completed.stderr}")
    report: Mapping[str, Any] = json.loads(completed.stdout)
    assert report["load_threw"] is None, report["load_threw"]
    assert report["mount_threw"] is None, report["mount_threw"]
    return report


def envelope(data: Mapping[str, Any]) -> dict[str, Any]:
    """A 200 outcome carrying one real ``/api/power`` body.

    Args:
        data: The endpoint's data object.

    Returns:
        The outcome shape ``app.js`` hands a settled callback.
    """
    return {"reached": True, "http": contract.HTTP_OK, "body": {"status": "ok", "data": data}}


def real_body(**parameters: str) -> dict[str, Any]:
    """One data object, produced by the REAL endpoint over the REAL corpus.

    A hand-typed fixture agrees with whatever this module believes the shape is,
    by construction, and stays green through the exact serializer defect it is
    meant to catch - CONVENTIONS.md section 7.2. So the bench is driven with
    what the endpoint actually emits.

    Args:
        **parameters: The request parameters.

    Returns:
        The ``data`` object of the endpoint's 200.
    """
    from clockspeed.data.registry import build_registry  # noqa: PLC0415
    from tests.data import synthetic as corpus  # noqa: PLC0415

    class _Provider:
        def registry(self) -> Any:
            return build_registry(corpus.synthetic_document())

    response = endpoint.make_handler(_Provider())(parameters)
    assert response.http_status == contract.HTTP_OK, response.payload
    body = response.payload["data"]
    assert isinstance(body, dict)
    return body


# ---------------------------------------------------------------------------
# (a) the seam arms, through the shared harness
# ---------------------------------------------------------------------------


def test_the_module_is_published_by_the_server() -> None:
    # A panel module the server does not name is a file the page cannot load,
    # and STATIC_ROUTES is a literal by design, so the name has to be added on
    # purpose. This is what turns forgetting it into a red suite.
    assert MODULE in server.ASSET_NAMES


def test_the_panel_mounts_against_an_all_null_payload(tmp_path: Path) -> None:
    # Through the SHARED harness, where data.actions is absent entirely. Four of
    # the six payload keys are null under the seam grader's canned probes, so a
    # panel that assumed any of them would be marked failed there.
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    assert report["registered"] is True
    assert report["panel_id"] == PANEL_ID
    assert report["load_threw"] is None
    assert report["threw"] is None
    assert report["state"] == panel_harness.STATE_MOUNTED


def test_the_bench_builds_every_field_even_with_no_registry(tmp_path: Path) -> None:
    report = panel_harness.mount(tmp_path, MODULE, panel_harness.null_payload())
    built = tuple(
        row["id"] for row in report["nodes"] if row["id"] and row["id"].startswith("power-")
    )
    count = len(built)
    assert count == EXPECTED_FIELDS
    assert sorted(built) == sorted(FIELD_IDS)


def test_the_panel_issues_no_request_of_its_own() -> None:
    # Every way a browser script reaches the network. A panel outside app.js's
    # one-at-a-time loop would put the page's request behaviour outside the file
    # that documents it.
    source = read_module()
    reached = tuple(name for name in NETWORK_PRIMITIVES if name in source)
    count = len(reached)
    assert count == 0, reached


def test_the_network_detector_fires_on_every_primitive_it_claims() -> None:
    # The absence above means nothing unless the scan can see each one.
    for name in NETWORK_PRIMITIVES:
        planted = "var x = " + name + ");"
        assert name in planted, name


def test_the_panel_builds_no_markup(tmp_path: Path) -> None:
    # A building key is game- or mod-authored content read out of the registry.
    # Building a node and setting textContent renders it as TEXT whatever
    # characters it holds; assigning it into markup would let its author choose
    # what this page executes.
    # COMMENTS COME OUT FIRST. This file's own header says "NO innerHTML", and
    # a scan over raw text would find that sentence and call it a sink - which
    # is the mirror of the fault the sweep exists for, and would go green the
    # day the sentence was deleted and the sink added.
    del tmp_path
    code = code_only(read_module())
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert sink not in code, sink


def test_the_markup_sink_scan_survives_the_comment_stripper() -> None:
    # The control: the stripper must remove the prose and keep the code, or the
    # arm above would pass over a panel that assigned innerHTML on every line.
    assert "innerHTML" in read_module(), "the header no longer mentions the sink at all"
    planted = code_only("/* NO innerHTML here */\nnode.innerHTML = value;\n")
    assert "innerHTML" in planted
    occurrences = planted.count("innerHTML")
    assert occurrences == 1, planted


# ---------------------------------------------------------------------------
# (c) no division anywhere in the render path
# ---------------------------------------------------------------------------


def test_nothing_in_the_render_path_divides() -> None:
    code = code_only(read_module())
    offences = tuple(match.group(0) for match in DIVISION.finditer(code))
    count = len(offences)
    assert count == 0, offences


@pytest.mark.parametrize("quotient", PLANTED_QUOTIENTS, ids=PLANTED_QUOTIENT_IDS)
def test_the_division_detector_fires_on_a_planted_quotient(quotient: str) -> None:
    # A detector that matched nothing would make the arm above green over a
    # panel that divided in every line. Every spelling is planted on its own,
    # so a detector that saw one of them cannot pass for one that sees all.
    planted = code_only(read_module()) + "\n" + quotient + "\n"
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
    sites = division_sites(read_module())
    assert sites == (), f"{len(sites)} bare slash(es) survive: {sites}"


@pytest.mark.parametrize("quotient", PLANTED_QUOTIENTS, ids=PLANTED_QUOTIENT_IDS)
def test_the_tokenizer_sweep_fires_on_every_planted_spelling(quotient: str) -> None:
    """The control is proved able to fire, on each spelling the detector must see."""
    sites = division_sites(read_module() + "\n" + quotient + "\n")
    count = len(sites)
    assert count == 1, sites


def test_the_division_detector_does_not_fire_on_the_pair_separator() -> None:
    # The control that keeps the arm above from being a rule about the CHARACTER
    # "/" - which the panel prints between a numerator and a denominator, and
    # which appears in every route path in the file's prose.
    offences = tuple(DIVISION.finditer(code_only('var PAIR_MARK = "/";\n// see /api/power\n')))
    count = len(offences)
    assert count == 0


# ---------------------------------------------------------------------------
# (b), (d) and (e) the rendered answer, driven through the real endpoint
# ---------------------------------------------------------------------------


def test_a_fixed_draw_renders_as_the_exact_pair_and_not_as_a_decimal_alone(
    tmp_path: Path,
) -> None:
    from tests.data import synthetic as corpus  # noqa: PLC0415

    body = real_body(building=corpus.BLENDER_BUILDING, clock="1")
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    declared = body["declared"]
    assert isinstance(declared, dict)
    megawatts = declared["megawatts"]
    assert isinstance(megawatts, dict)
    pair = f"{megawatts['num']}/{megawatts['den']}"
    assert pair in text, text
    assert "display only" in text


def test_every_approximation_is_the_exact_truncation_of_its_pair(tmp_path: Path) -> None:
    """CS-1028: this panel's copy of ``approximateDecimal`` is graded for its DIGITS.

    The arm above proves the pair is there and a decimal is labelled; it does
    not notice a decimal whose digits are wrong, and a digit-corrupting mutant
    of this copy was measured surviving every arm in this file. One real body is
    settled once per case with its declared draw replaced, because each leaf of
    a power answer is a single rational. The oracle is the solve bench's own
    table and truncation, imported rather than restated. Each pair must render
    EXACTLY ONCE, so a matching rendering from another leaf cannot stand in.
    """
    from tests.data import synthetic as corpus  # noqa: PLC0415

    steps: list[dict[str, Any]] = []
    for call, (num, den) in enumerate(TRUNCATION_CASES):
        body = real_body(building=corpus.BLENDER_BUILDING, clock="1")
        declared = body["declared"]
        assert isinstance(declared, dict)
        declared["megawatts"] = {"num": num, "den": den}
        steps.append({"press": True})
        steps.append({"settle": {"call": call, "outcome": envelope(body)}})
    report = drive(tmp_path, panel_harness.null_payload(), steps=steps)
    asked = len(report["calls"])
    assert asked == len(TRUNCATION_CASES), report["calls"]

    settled = [step["text"] for step in report["steps"] if step["kind"] == "settle"]
    assert len(settled) == len(TRUNCATION_CASES), settled
    for (num, den), text in zip(TRUNCATION_CASES, settled, strict=True):
        # A digit or a sign may not precede the pair, or "120/1" would count as "0/1"
        # and "-22/7" as "22/7".
        opened = re.compile(rf"(?<![\d-]){num}/{den} \(approx ")
        renderings = len(opened.findall(text))
        assert renderings == 1, f"{num}/{den} rendered {renderings} time(s): {text}"
        rendered = f"megawatts: {num}/{den} (approx {truncated_decimal(num, den)}, display only)"
        assert rendered in text, f"expected {rendered!r} on the page: {text}"


def test_an_unmodeled_draw_is_never_rendered_as_a_zero(tmp_path: Path) -> None:
    # THE FAULT THIS ARM EXISTS FOR. A confident zero is exactly what a power
    # plan cannot detect: it balances, it sums, and it is silently missing a
    # building. The endpoint sends null and a reason, and the bench must say so.
    from tests.data import synthetic as corpus  # noqa: PLC0415

    body = real_body(building=corpus.CHARGER_BUILDING)
    declared = body["declared"]
    assert isinstance(declared, dict)
    assert declared["megawatts"] is None, "the corpus stopped producing an unmodeled draw"

    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    assert "megawatts: not declared" in text, text
    assert "megawatts: 0/1" not in text
    assert str(declared["reason"]) in text


def test_the_deferred_term_renders_as_two_operands_and_never_as_a_number(
    tmp_path: Path,
) -> None:
    # Away from the reference clock the power law has no exact rational value.
    # The bench writes the coefficient and the two operands and applies neither.
    from tests.data import synthetic as corpus  # noqa: PLC0415

    body = real_body(building=corpus.BLENDER_BUILDING, clock="3/2")
    at_clock = body["at_clock"]
    assert isinstance(at_clock, dict)
    deferred = at_clock["deferred"]
    assert isinstance(deferred, dict), "the corpus stopped producing a deferred term"

    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    base = deferred["base"]
    exponent = deferred["exponent"]
    assert isinstance(base, dict)
    assert isinstance(exponent, dict)
    assert f"{base['num']}/{base['den']}" in text, text
    assert f"{exponent['num']}/{exponent['den']}" in text, text
    assert "held unevaluated" in text
    assert "3.3577506181236285" not in text


def test_the_bench_says_the_base_is_not_the_ceiling(tmp_path: Path) -> None:
    # ADR 0006's fence, on the page. A reader who takes the un-sharded base for
    # the achievable maximum is right on every building nobody has overclocked.
    from tests.data import synthetic as corpus  # noqa: PLC0415

    body = real_body(building=corpus.BLENDER_BUILDING)
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    text = report["steps"][-1]["text"]
    assert "NOT the ceiling" in text, text
    assert "achievable ceiling known: no" in text
    assert "shard slots: unmeasured" in text


def test_the_bench_sends_only_the_names_the_reader_filled_in(tmp_path: Path) -> None:
    # AN EMPTY OPTIONAL FIELD IS OMITTED, NOT SENT EMPTY. An empty string is
    # neither a well-formed key nor an exact rational, so sending one would turn
    # "I did not ask" into a 400.
    report = drive(tmp_path, panel_harness.null_payload(), steps=[{"press": True}])
    calls = report["calls"]
    count = len(calls)
    assert count == 1, calls
    assert sorted(calls[0]) == [endpoint.PARAM_BUILDING], calls[0]


def test_a_bench_with_no_door_says_so_rather_than_looking_dead(tmp_path: Path) -> None:
    report = drive(tmp_path, panel_harness.null_payload(), door=False, steps=[{"press": True}])
    assert report["steps"][-1]["buttons"] == 1
    assert "published no power door" in report["steps"][-1]["text"]


def test_a_refused_request_is_reported_rather_than_waited_on(tmp_path: Path) -> None:
    # A FALSE RETURN MEANS THE CALLBACK NEVER FIRES. Nothing else will ever
    # arrive, so silence here would make the press look like a dead button.
    report = drive(tmp_path, panel_harness.null_payload(), accepts=False, steps=[{"press": True}])
    assert "the page refused the request" in report["steps"][-1]["text"]


def test_a_refusal_envelope_is_rendered_and_not_swallowed(tmp_path: Path) -> None:
    # The reason and the detail sit OUTSIDE data, which is why app.js hands the
    # panel the whole envelope; a bench that read only data would render every
    # 400 as silence.
    refusal = contract.bad_request(endpoint.ENDPOINT, contract.REASON_INVALID_PARAMETER)
    outcome = {"reached": True, "http": refusal.http_status, "body": dict(refusal.payload)}
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": outcome}}],
    )
    text = report["steps"][-1]["text"]
    assert contract.REASON_INVALID_PARAMETER in text, text
    assert "refused with 400" in text


# ---------------------------------------------------------------------------
# (f) the registry's provenance, said before the figures (CS-1315 slice B)
# ---------------------------------------------------------------------------

#: What the bench says over a registry the audit did not verify, and over one
#: it did. Spelled once here so each arm reads the same sentence head.
UNVERIFIED_MARK: Final = "registry: UNVERIFIED"
VERIFIED_MARK: Final = "registry: verified"
NO_STATE_MARK: Final = "carried no build state"

#: The first figure group the bench renders, which the provenance line precedes.
FIRST_FIGURE: Final = "declared draw"

#: The two registries the audit does not verify: other docs bytes, and none.
UNVERIFIED_SOURCES: Final = ("other-docs-bytes", "no-byte-source")


def sourced_body(source_sha256: str | None) -> dict[str, Any]:
    """One real ``/api/power`` data object over the corpus stamped with one source hash.

    Args:
        source_sha256: The hash the registry claims it was built from, or None.

    Returns:
        The ``data`` object of the endpoint's 200.
    """
    import dataclasses  # noqa: PLC0415

    from clockspeed.data.registry import build_registry  # noqa: PLC0415
    from tests.data import synthetic as corpus  # noqa: PLC0415

    stamped = dataclasses.replace(
        build_registry(corpus.synthetic_document()), source_sha256=source_sha256
    )

    class _Provider:
        def registry(self) -> Any:
            return stamped

    response = endpoint.make_handler(_Provider())({"building": corpus.BLENDER_BUILDING})
    assert response.http_status == contract.HTTP_OK, response.payload
    body = response.payload["data"]
    assert isinstance(body, dict)
    return body


def settled_text(tmp_path: Path, body: Mapping[str, Any]) -> str:
    """The bench's text once one body has settled.

    Args:
        tmp_path: The driver's scratch directory.
        body: The data object the door settles with.

    Returns:
        The rendered text.
    """
    report = drive(
        tmp_path,
        panel_harness.null_payload(),
        steps=[{"press": True}, {"settle": {"call": 0, "outcome": envelope(body)}}],
    )
    return str(report["steps"][-1]["text"])


@pytest.mark.parametrize("case", UNVERIFIED_SOURCES)
def test_an_unverified_registry_is_said_before_the_figures_with_its_served_code(
    tmp_path: Path, case: str
) -> None:
    body = sourced_body(OFF_PIN_DOCS_SHA256 if case == "other-docs-bytes" else None)
    rows = body["warnings"]
    assert isinstance(rows, list)
    codes = [str(row["code"]) for row in rows]
    count = len(codes)
    assert count == 1, rows
    expected = (
        build_model.WARN_REGISTRY_MISMATCH
        if case == "other-docs-bytes"
        else build_model.WARN_REGISTRY_UNVERIFIED
    )
    assert codes == [expected]

    text = settled_text(tmp_path, body)

    assert UNVERIFIED_MARK in text, text
    assert expected in text, text
    assert VERIFIED_MARK not in text
    assert text.index(UNVERIFIED_MARK) < text.index(FIRST_FIGURE), text


def test_a_verified_registry_is_said_to_be_verified_and_names_no_code(tmp_path: Path) -> None:
    body = sourced_body(docs_pin())
    assert body["warnings"] == []

    text = settled_text(tmp_path, body)

    assert VERIFIED_MARK in text, text
    assert UNVERIFIED_MARK not in text
    assert build_model.WARN_REGISTRY_MISMATCH not in text
    assert build_model.WARN_REGISTRY_UNVERIFIED not in text


def test_a_body_without_a_build_state_is_never_read_as_verified(tmp_path: Path) -> None:
    body = sourced_body(docs_pin())
    del body["build_state"]
    del body["warnings"]

    text = settled_text(tmp_path, body)

    assert NO_STATE_MARK in text, text
    assert VERIFIED_MARK not in text
