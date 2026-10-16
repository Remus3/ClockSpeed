"""CS-962 slice S0 - the dashboard's panel seam, graded statically and by running it.

WHAT THE SEAM IS. ``clockspeed/surface/web/app.js`` publishes one global,
``registerPanel(id, mountFn)``. A panel module calls it once at load and is
handed ``mountFn(root, data)`` later: ``root`` is a DOM node the seam owns and
``data`` is the payloads ``app.js`` ALREADY FETCHED. A panel issues no request
of its own, so the page's sequential-probe discipline stays in one file and a
new panel is a NEW FILE rather than another edit to the one script every panel
would otherwise queue behind.

WHY HALF OF THIS MODULE RUNS NODE RATHER THAN READING BYTES. Two of the four
properties the seam claims are BEHAVIOURAL - a panel whose mount throws must
not stop the others, and a panel must actually receive the fetched payloads -
and no amount of grepping the shipped characters settles either. A spelling
control would assert that a ``try`` appears near a ``mount``, which is a claim
about typography. So the shipped ``app.js`` and the shipped panel modules are
executed against a small DOM stand-in, with a THROWING MOUNT PLANTED IN THE
MIDDLE of the registration order, and the arms read what the seam actually
built.

THE PLANT IS PROVED TO HAVE APPLIED. ``test_the_planted_thrower_is_recorded_as
_failed`` reads the failed marker off the run that carries the plant, and the
clean run is asserted to carry none. A mutation that never applied and a
mutation that survived produce the same green otherwise.

NODE IS REQUIRED, NOT SKIPPED AROUND. ``scripts/verify_env.py`` files node as a
SOFT dependency needed by phase 6, and the shell suite already depends on it.
An arm that skipped itself where node is absent would report PASS while
grading nothing, so the arms below FAIL loudly instead and name what is
missing.
"""

from __future__ import annotations

import contextlib
import json
import re
import shutil
import subprocess
import threading
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Final

import pytest

from clockspeed.surface import config, server

if TYPE_CHECKING:
    from collections.abc import Mapping

#: The asset directory, read from the module that owns the answer.
WEB_DIR: Final = config.default_web_dir()

#: The seam's own file. Named apart from the panels because it holds the seam
#: rather than being mounted by it.
SCRIPT: Final = "app.js"

#: Every panel module the server publishes, derived from the server's own table
#: rather than listed here, so a module added there is graded here without an
#: edit. SORTED FOR A STABLE ORDER, WHICH IS NOT THE PAGE'S LOAD ORDER - that
#: claim was true until CS-977 added a module that sorts first and loads last.
#: Every consumer here compares sets or iterates all of them, so a stable
#: order is all this needs; a consumer that wants load order must read
#: index.html, which owns it.
PANEL_MODULES: Final = tuple(
    sorted(name for name in server.ASSET_NAMES if name.startswith("panel_"))
)

#: The module the network detector is proved clean against, NAMED rather than
#: taken positionally. It was ``PANEL_MODULES[0]`` until CS-977, where a new
#: panel module sorted ahead of the intended baseline and silently moved what
#: this arm grades - the failure the pin in ``tests/surface/test_panel_registry.py``
#: was written to catch, and did. A name cannot be moved by a sibling
#: slice adding a file, so the pin now grades a fact instead of an ordering.
NETWORK_BASELINE_MODULE: Final = "panel_registry.js"


#: The exported name every panel module calls, spelled as a CALL so a prose
#: mention in a comment explaining the seam does not read as one.
REGISTER_CALL: Final = "registerPanel("

#: Every way a browser script reaches the network. A panel that used any of
#: them would duplicate the probe discipline ``app.js`` owns, and would do it
#: outside the one place that serialises the probes.
_NETWORK_SINKS: Final = (
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "EventSource",
    "WebSocket",
    "import(",
)

#: A JavaScript block comment.
_BLOCK_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")

#: How long the node run may take before it is a failure rather than a slow box.
#: A RUN limit: it counts from the start marker, never from the spawn (CS-1329).
NODE_TIMEOUT_SECONDS: Final = 60.0

#: How long node may take to REACH a driver - spawn to start marker - before
#: that is a failure. A cold start on a loaded runner is node's time, not the
#: driver's, so it is budgeted here and never charged to a site's run limit.
NODE_START_TIMEOUT_SECONDS: Final = 120.0

#: The one stderr line the preload writes when node reaches user code.
NODE_START_MARKER: Final = "clockspeed-node-start"

#: A PASS whose start-up reached this many seconds still leaves a warning line
#: in the log, because a slow start that passes is the red's own precursor.
#: PROVISIONAL: no start-up reading existed before CS-1329 split the phases.
#: The figures it was picked from are WHOLE-SPAWN times, start-up and run
#: together - the tier2 spawn that failed read 6.31 s and then 19.40 s before
#: it timed out, the slowest other spawn in that job 9.73 s - so they bound
#: start-up from above and say nothing of its share. Recalibrate it from the
#: first tier2 start-up readings this helper reports.
NODE_SLOW_START_SECONDS: Final = 15.0

#: The panel id the harness plants a throwing mount under.
PLANTED_ID: Final = "planted-thrower"

#: The panel id the harness registers to record what a mount is handed.
PROBE_ID: Final = "payload-probe"

#: The marker ``app.js`` writes onto a panel root that mounted, and the one it
#: writes when that panel's mount threw.
STATE_MOUNTED: Final = "mounted"
STATE_FAILED: Final = "failed"


def code_only(text: str) -> str:
    """The script with its block comments removed.

    An arm that means "the code does this" has to be given the code. The
    stripper is proved to do both halves of its job in
    :func:`test_the_comment_stripper_removes_a_comment_and_keeps_the_code`.

    Args:
        text: The script's full text.

    Returns:
        The text with every block comment replaced by a space.
    """
    return _BLOCK_COMMENT.sub(" ", text)


def read_module(name: str) -> str:
    """Read one shipped asset as text, decoded strictly as ASCII.

    Args:
        name: A filename inside the web directory.

    Returns:
        The file's text.
    """
    return (WEB_DIR / name).read_bytes().decode("ascii")


def network_sinks(text: str) -> tuple[str, ...]:
    """Every network primitive used in one module's text.

    Args:
        text: The module's code, comments already stripped.

    Returns:
        One finding per primitive present, in the order they are listed.
    """
    return tuple(sink for sink in _NETWORK_SINKS if sink in text)


# ---------------------------------------------------------------------------
# The DOM stand-in and the run harness
# ---------------------------------------------------------------------------

#: A CommonJS harness that loads the SHIPPED ``app.js`` and the SHIPPED panel
#: modules into one global scope over a minimal DOM stand-in, then reports what
#: the seam built. It is written to a temporary directory rather than tracked
#: as an asset, because it is test scaffolding and an asset it is not.
#:
#: WHY A HAND-WRITTEN STAND-IN RATHER THAN A HEADLESS BROWSER. The seam touches
#: ``createElement``, ``textContent``, ``appendChild``, ``removeChild`` and
#: ``setAttribute`` and nothing else, and a stand-in that implements exactly
#: those cannot quietly satisfy an arm through a behaviour nobody meant to rely
#: on. Layout, styling and focus are NOT modelled here and no arm below reads
#: them; ``tests/surface/audit_harness.py`` driven by a real Chromium is what
#: covers those, and it is a different control.
HARNESS_SOURCE: Final = r""""use strict";

var fs = require("node:fs");
var path = require("node:path");
var vm = require("node:vm");

var webDir = process.argv[2];
var plantThrower = process.argv[3] === "plant";
var moduleNames = process.argv.slice(4);

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
      APPENDING IS WHAT PUTS A NODE IN THE DOCUMENT, so it is what makes an id
      resolvable. Without this the seam would append a panel section, fail to
      find it on the next repaint, and append a second one - which is a real
      fault this stand-in has to be able to see rather than paper over.
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
  node.addEventListener = function () {
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
  getElementById ANSWERS null FOR AN ID THE DOCUMENT DOES NOT DECLARE, exactly
  as a real one does. A stand-in that minted a node for any id asked of it
  would make the seam's "does this panel already have a section" check answer
  yes on the first repaint, so no section would ever be appended to the host
  and the arms would read an empty page as a mounting failure - or worse, read
  a full one as success while nothing was ever in the document.

  The declared set is parsed out of the SHIPPED index.html rather than listed
  here, so an id the page stops declaring stops resolving here too.
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

var CANNED = {
  "/api/health": {
    status: "ok",
    data: {
      app_version: "0.0.0-harness",
      game_build_pin: "harness-build",
      registry: "loaded",
      world: "present",
      endpoints: {}
    }
  },
  "/api/world": {
    status: "ok",
    data: {
      world: "cs1-harness",
      header_version: "1",
      save_version: "1",
      build_changelist: "1",
      body_offset: "1",
      is_modded: "false",
      counts: {},
      unknown_classes: []
    }
  }
};

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

globalThis.fetch = function (target) {
  var body = Object.prototype.hasOwnProperty.call(CANNED, target)
    ? CANNED[target]
    : { status: "not_implemented", blocked_by: "CS-HARNESS" };
  return Promise.resolve({
    status: 200,
    json: function () {
      return Promise.resolve(body);
    }
  });
};

function load(name) {
  var source = fs.readFileSync(path.join(webDir, name), "utf8");
  vm.runInThisContext(source, { filename: name });
}

function tick() {
  return new Promise(function (done) {
    setImmediate(done);
  });
}

var seen = null;

async function main() {
  load("app.js");

  /*
    THE PLANT SITS IN THE MIDDLE OF THE REGISTRATION ORDER ON PURPOSE. A
    thrower registered last would leave "the rest still mounted" satisfied by
    panels that ran BEFORE it, which proves nothing about isolation.
  */
  var half = Math.floor(moduleNames.length / 2);
  moduleNames.slice(0, half).forEach(load);
  if (plantThrower) {
    registerPanel("planted-thrower", function () {
      throw new Error("planted mount failure");
    });
  }
  moduleNames.slice(half).forEach(load);

  registerPanel("payload-probe", function (root, data) {
    seen = {
      rootIsElement: Boolean(root) && typeof root.appendChild === "function",
      dataIsObject: Boolean(data) && typeof data === "object",
      keys: data && typeof data === "object" ? Object.keys(data).sort() : [],
      healthPresent: Boolean(data && data.health),
      appVersion: data && data.health ? String(data.health.app_version) : null
    };
    root.appendChild(document.createTextNode("probe mounted"));
  });

  await tick();
  await tick();
  await refresh();

  var host = lookup("panels");
  process.stdout.write(
    JSON.stringify({
      registered: typeof registerPanel === "function",
      probe: seen,
      sections: host.childNodes.map(function (section) {
        return {
          id: section.id,
          state: section.getAttribute("data-panel-state"),
          text: section.textContent
        };
      })
    })
  );
}

main().catch(function (failure) {
  process.stderr.write("harness failed: " + String(failure && failure.stack) + "\n");
  process.exitCode = 1;
});
"""


# ---------------------------------------------------------------------------
# The node spawn every panel suite shares (CS-1329)
# ---------------------------------------------------------------------------
#
# It lives in the grader because the grader may import nothing from
# ``panel_harness.py``; the harness re-exports it, so there is one copy.

#: The preload that writes the marker. ``fs.writeSync`` and not
#: ``process.stderr.write``: a stream write to a pipe may be queued, and a
#: driver that then spun would never flush it - reading a hang as a slow start.
_START_MARKER_SOURCE: Final = (
    '"use strict";\nrequire("node:fs").writeSync(2, "' + NODE_START_MARKER + '\\n");\n'
)

#: The preload's file name, written beside the driver it precedes.
_START_MARKER_NAME: Final = "node_start_marker.cjs"

#: How much of each stream a diagnosis quotes - the TAIL, where a run stopped.
_PARTIAL_CHARS: Final = 2000

#: How long a killed or exited node gets to die and close its pipes.
_REAP_SECONDS: Final = 10.0


class NodeStartupWarning(UserWarning):
    """A passing node run's start-up reading, left in the log on purpose."""


@dataclass(frozen=True)
class NodeRun:
    """One finished node run: its exit, its output, and each phase's seconds."""

    returncode: int
    stdout: str
    stderr: str
    startup_seconds: float
    run_seconds: float


class _Pipes:
    """Drains node's stdout and stderr on threads and notes the start marker."""

    def __init__(self, process: subprocess.Popen[str]) -> None:
        self.marker_at: float | None = None
        #: Set on the marker, or when stderr closes without one.
        self.settled = threading.Event()
        self._out: list[str] = []
        self._err: list[str] = []
        self._threads = (
            threading.Thread(target=self._drain_out, args=(process.stdout,), daemon=True),
            threading.Thread(target=self._drain_err, args=(process.stderr,), daemon=True),
        )
        for thread in self._threads:
            thread.start()

    def _drain_out(self, stream: IO[str]) -> None:
        self._out.append(stream.read())

    def _drain_err(self, stream: IO[str]) -> None:
        for line in stream:
            if self.marker_at is None and line.rstrip("\r\n") == NODE_START_MARKER:
                self.marker_at = time.monotonic()
                self.settled.set()
            else:
                self._err.append(line)
        self.settled.set()

    def join(self, timeout: float) -> bool:
        """Wait for both drains; True when both reached end of stream."""
        deadline = time.monotonic() + timeout
        for thread in self._threads:
            thread.join(max(0.0, deadline - time.monotonic()))
        return not any(thread.is_alive() for thread in self._threads)

    @property
    def stdout(self) -> str:
        return "".join(self._out)

    @property
    def stderr(self) -> str:
        return "".join(self._err)


def _reap(process: subprocess.Popen[str], pipes: _Pipes) -> None:
    """Kill node and collect whatever it had written."""
    process.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=_REAP_SECONDS)
    pipes.join(_REAP_SECONDS)


def _diagnosis(
    label: str,
    phase: str,
    *,
    started: float,
    ended: float,
    marker_at: float | None,
    run_timeout: float,
    pipes: _Pipes,
) -> str:
    """The failure text: elapsed seconds, the marker's fate, the partial output."""
    if marker_at is None:
        fate = (
            "start marker arrived: no - node never reached the driver inside its "
            f"{NODE_START_TIMEOUT_SECONDS:g} s start budget, so the time went to "
            "node's own start-up, not to the driver"
        )
    else:
        fate = (
            f"start marker arrived: yes, {marker_at - started:.2f} s after the spawn - "
            f"the driver then ran {ended - marker_at:.2f} s against its "
            f"{run_timeout:g} s run limit, so the driver itself did not finish"
        )
    out, err = pipes.stdout, pipes.stderr
    return (
        f"{label} timed out in its {phase} phase: elapsed {ended - started:.2f} s; "
        f"{fate}. partial stdout ({len(out)} chars, tail): {out[-_PARTIAL_CHARS:]!r}; "
        f"partial stderr ({len(err)} chars, tail): {err[-_PARTIAL_CHARS:]!r}"
    )


def run_node(
    node: str,
    script: Path,
    *args: str,
    label: str,
    run_timeout: float,
    report_startup: bool = False,
) -> NodeRun:
    """Run one node driver in two separately budgeted phases.

    START runs from the spawn to the start marker a preload writes when node
    reaches user code, against :data:`NODE_START_TIMEOUT_SECONDS`. RUN runs
    from the marker to the exit, against ``run_timeout`` - the calling site's
    own ``NODE_TIMEOUT_SECONDS``, which this never raises. A timeout in either
    phase fails with :func:`_diagnosis` rather than a bare ``TimeoutExpired``,
    so the next reading tells node's cold start from a driver that hung.

    A run that PASSES warns :class:`NodeStartupWarning` with its start-up
    seconds when they reached :data:`NODE_SLOW_START_SECONDS`, or always when
    ``report_startup`` is set, so a green log still carries the reading.

    Args:
        node: The interpreter, as the caller resolved it off PATH.
        script: The driver. The preload is written beside it.
        *args: The driver's own arguments.
        label: Names the driver in a failure, e.g. "the seam harness".
        run_timeout: The site's run limit, in seconds.
        report_startup: Warn the start-up reading even under the slow line.

    Returns:
        The exit code, the output (the marker line removed) and both phases.
    """
    marker = script.parent / _START_MARKER_NAME
    marker.write_bytes(_START_MARKER_SOURCE.encode("ascii"))
    started = time.monotonic()
    # Fixed argv, no shell: the caller's PATH lookup, then paths the caller and
    # this function wrote.
    process = subprocess.Popen(
        [node, "--require", str(marker), str(script), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    pipes = _Pipes(process)
    try:
        if not pipes.settled.wait(NODE_START_TIMEOUT_SECONDS):
            ended = time.monotonic()
            _reap(process, pipes)
            pytest.fail(
                _diagnosis(
                    label,
                    "start",
                    started=started,
                    ended=ended,
                    marker_at=None,
                    run_timeout=run_timeout,
                    pipes=pipes,
                )
            )
        marker_at = pipes.marker_at
        run_from = time.monotonic() if marker_at is None else marker_at
        try:
            process.wait(timeout=max(0.0, run_from + run_timeout - time.monotonic()))
        except subprocess.TimeoutExpired:
            ended = time.monotonic()
            _reap(process, pipes)
            pytest.fail(
                _diagnosis(
                    label,
                    "run",
                    started=started,
                    ended=ended,
                    marker_at=marker_at,
                    run_timeout=run_timeout,
                    pipes=pipes,
                )
            )
        ended = time.monotonic()
        if not pipes.join(_REAP_SECONDS):
            pytest.fail(
                f"{label} exited {process.returncode} but its output pipes were "
                f"still open {_REAP_SECONDS:g} s later"
            )
    finally:
        if process.poll() is None:
            _reap(process, pipes)
        if pipes.join(0.0):
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
    if marker_at is None and process.returncode == 0:
        pytest.fail(
            f"{label} exited 0 without the start marker, so the preload that "
            f"writes it never ran: {pipes.stderr.strip()!r}"
        )
    startup = run_from - started
    if marker_at is not None and (report_startup or startup >= NODE_SLOW_START_SECONDS):
        side = "past" if startup >= NODE_SLOW_START_SECONDS else "under"
        warnings.warn(
            NodeStartupWarning(
                f"{label} reached its start marker in {startup:.2f} s, {side} the "
                f"{NODE_SLOW_START_SECONDS:g} s slow-start line; its run took "
                f"{ended - run_from:.2f} s"
            ),
            stacklevel=2,
        )
    return NodeRun(
        returncode=process.returncode,
        stdout=pipes.stdout,
        stderr=pipes.stderr,
        startup_seconds=startup,
        run_seconds=ended - run_from,
    )


def run_seam(tmp_path: Path, *, plant: bool) -> Mapping[str, Any]:
    """Run the shipped seam under node and return what it built.

    Args:
        tmp_path: A directory to write the harness into.
        plant: Whether to register a mount that throws, mid-order.

    Returns:
        The harness report: the registration flag, the probe record and one
        entry per panel section the seam built.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so the behavioural half of the panel seam was "
            "not graded. This arm FAILS rather than skipping: a skipped gate "
            "reports PASS while measuring nothing."
        )

    harness = tmp_path / "panel_seam_harness.cjs"
    harness.write_bytes(HARNESS_SOURCE.encode("ascii"))

    # Fixed argv, no shell, and nothing on it comes from outside this file:
    # the interpreter is resolved off PATH, the harness path is pytest's own
    # temporary directory and the module names come from the server's table.
    completed = run_node(
        node,
        harness,
        str(WEB_DIR),
        "plant" if plant else "clean",
        *PANEL_MODULES,
        label="the seam harness",
        run_timeout=NODE_TIMEOUT_SECONDS,
    )
    assert completed.returncode == 0, (
        f"the seam harness exited {completed.returncode}: {completed.stderr.strip()}"
    )
    report: Mapping[str, Any] = json.loads(completed.stdout)
    return report


# ---------------------------------------------------------------------------
# a. The seam exists, and every panel module joins it exactly once
# ---------------------------------------------------------------------------


def test_there_is_at_least_one_panel_module_to_grade() -> None:
    """The module set below is non-empty.

    THIS IS THE PRECONDITION FOR EVERY STATIC ARM IN THIS FILE. Each of them
    iterates :data:`PANEL_MODULES`, and an empty tuple would make all of them
    vacuously green while the seam had no members at all.
    """
    assert PANEL_MODULES, "the server publishes no panel_*.js module"


def test_every_panel_module_on_disk_is_published_by_the_server() -> None:
    """A ``panel_*.js`` sitting in the asset directory is one the server serves.

    THIS IS THE ANTI-VACUITY ARM FOR EVERY OTHER ARM IN THIS MODULE.
    :data:`PANEL_MODULES` is derived from ``server.ASSET_NAMES``, which is the
    right direction - a module added to the served table is graded here with no
    edit - and it has one blind spot in the other direction: a panel module that
    exists on disk and is NOT in that table is excluded from every arm above and
    below, silently. It registers on no page, it is mounted by no harness, its
    bytes are scanned by no character-set or network check, and the suite is
    green.

    THAT IS THE SAME FAULT AS AN UNTRACKED FILE BEING INVISIBLE TO A REPO GUARD,
    and the repair is the same: compare the table against the directory rather
    than reading only one of them. ``STATIC_ROUTES`` is a literal by deliberate
    design - CS-962 records that a glob over the directory would publish
    whatever a working tree happened to hold - so the name must be added on
    purpose, and this arm is what turns forgetting it into a red suite instead of
    a panel nobody can load.
    """
    on_disk = tuple(sorted(path.name for path in WEB_DIR.glob("panel_*.js")))
    assert on_disk, f"there is no panel module in {WEB_DIR.name} at all"

    unpublished = tuple(name for name in on_disk if name not in PANEL_MODULES)
    assert not unpublished, (
        f"{len(unpublished)} panel module(s) exist but are not in "
        f"clockspeed/surface/server.py STATIC_ROUTES, so the page cannot load "
        f"them and no arm in this module grades them: {unpublished}"
    )

    missing = tuple(name for name in PANEL_MODULES if name not in on_disk)
    assert not missing, f"the server publishes panel module(s) with no file: {missing}"


def test_the_script_publishes_the_registration_seam() -> None:
    """``app.js`` defines ``registerPanel`` in its code, not only in its prose."""
    code = code_only(read_module(SCRIPT))
    assert "function registerPanel(" in code, "app.js declares no registerPanel"


def test_every_panel_module_registers_exactly_once() -> None:
    """Each panel module calls ``registerPanel`` once and no more.

    ONCE RATHER THAN AT LEAST ONCE. A module registering twice would take two
    slots in a list every repaint walks, and the second registration is either
    a duplicate id the seam refuses or a second panel hiding inside a file
    named for one.
    """
    assert PANEL_MODULES, "no panel module to grade; this arm would be vacuously green"
    counts = {name: code_only(read_module(name)).count(REGISTER_CALL) for name in PANEL_MODULES}
    wrong = {name: found for name, found in counts.items() if found != 1}
    total = len(wrong)
    assert total == 0, f"{total} panel module(s) do not register exactly once: {wrong}"


def test_the_registration_counter_is_not_fooled_by_a_comment() -> None:
    """The count is taken over code, so prose naming the seam does not register.

    Without this the arm above would pass on a module that only TALKED about
    registering, which is the exact failure ``code_only`` exists for.
    """
    prose_only = "/* this module calls registerPanel( one day */\nvar x = 1;\n"
    real = '/* see registerPanel( above */\nregisterPanel("x", function () { return 1; });\n'
    assert code_only(prose_only).count(REGISTER_CALL) == 0, prose_only
    assert code_only(real).count(REGISTER_CALL) == 1, real


def test_the_comment_stripper_removes_a_comment_and_keeps_the_code() -> None:
    """The stripper is proved to do both halves of its job."""
    sample = "var a = 1; /* fetch( lives here */ node.textContent = a;"
    stripped = code_only(sample)
    assert "fetch(" not in stripped, stripped
    assert "node.textContent" in stripped, stripped


# ---------------------------------------------------------------------------
# b. A panel never issues its own request
# ---------------------------------------------------------------------------


def test_no_panel_module_issues_its_own_fetch() -> None:
    """``app.js`` owns all I/O; a panel is handed what was already fetched.

    THE PAGE PROBES SEQUENTIALLY AND ON A BUTTON, NEVER ON A TIMER, and both
    properties are properties of ONE loop in ``app.js``. A panel that opened
    its own request would sit outside that loop, so the page's request
    behaviour would stop being readable in the file that documents it.
    """
    assert PANEL_MODULES, "no panel module to grade; this arm would be vacuously green"
    findings = {
        name: network_sinks(code_only(read_module(name)))
        for name in PANEL_MODULES
        if network_sinks(code_only(read_module(name)))
    }
    total = len(findings)
    assert total == 0, f"{total} panel module(s) reach the network: {findings}"


def test_the_network_detector_fires_on_every_primitive_it_claims() -> None:
    """Each member of :data:`_NETWORK_SINKS` is proved to make the detector fire.

    A detector that cannot fire is a detector that grades nothing, and the arm
    above would be the same green either way.
    """
    assert NETWORK_BASELINE_MODULE in PANEL_MODULES, (
        f"the baseline {NETWORK_BASELINE_MODULE} is not published, so this arm "
        "would grade a file the server does not serve"
    )
    clean = code_only(read_module(NETWORK_BASELINE_MODULE))
    assert network_sinks(clean) == ()

    silent = tuple(sink for sink in _NETWORK_SINKS if not network_sinks(clean + "\n" + sink + "\n"))
    assert not silent, f"the network detector did not fire on: {silent}"


# ---------------------------------------------------------------------------
# c. Running the seam - the control, then the plant
# ---------------------------------------------------------------------------


def test_the_seam_mounts_every_registered_panel(tmp_path: Path) -> None:
    """With nothing planted, every registered panel gets a root and mounts.

    THIS IS THE KNOWN-GOOD CONTROL THE ISOLATION ARM NEEDS. An isolation arm
    reading "the others still mounted" proves nothing unless it is known that
    the others mount at all under this harness.
    """
    report = run_seam(tmp_path, plant=False)
    assert report["registered"] is True, report

    states = {section["id"]: section["state"] for section in report["sections"]}
    expected = {f"panel-{name[len('panel_') : -len('.js')]}" for name in PANEL_MODULES}
    expected.add(f"panel-{PROBE_ID}")

    assert set(states) == expected, states
    failed = {panel for panel, state in states.items() if state != STATE_MOUNTED}
    assert not failed, f"panels that did not mount in a clean run: {failed}"


def test_a_panel_receives_a_dom_root_and_the_already_fetched_payloads(
    tmp_path: Path,
) -> None:
    """``mountFn(root, data)`` is handed a node and the resolved payloads.

    The probe panel records what it was given rather than asserting on the
    shipped panels' own output, so this arm stays true of a seam whose members
    all change.
    """
    probe = run_seam(tmp_path, plant=False)["probe"]
    assert probe is not None, "the probe panel never mounted"
    assert probe["rootIsElement"] is True, probe
    assert probe["dataIsObject"] is True, probe
    assert probe["healthPresent"] is True, probe
    assert probe["appVersion"] == "0.0.0-harness", probe


def test_a_panel_that_throws_does_not_stop_the_others(tmp_path: Path) -> None:
    """One mount throwing leaves every other panel mounted.

    THE THROWER IS PLANTED IN THE MIDDLE OF THE REGISTRATION ORDER, so the
    panels this arm reads include ones registered AFTER it. A seam that let the
    throw escape its loop would leave those unmounted and this arm would name
    them.
    """
    report = run_seam(tmp_path, plant=True)
    states = {section["id"]: section["state"] for section in report["sections"]}

    survivors = {panel: state for panel, state in states.items() if panel != f"panel-{PLANTED_ID}"}
    stopped = {panel for panel, state in survivors.items() if state != STATE_MOUNTED}
    assert not stopped, f"a planted throw stopped {len(stopped)} other panel(s): {stopped}"

    expected_survivors = {f"panel-{name[len('panel_') : -len('.js')]}" for name in PANEL_MODULES}
    expected_survivors.add(f"panel-{PROBE_ID}")
    assert set(survivors) == expected_survivors, survivors


def test_the_planted_thrower_is_recorded_as_failed(tmp_path: Path) -> None:
    """The plant is proved to have applied, and the clean run to carry none.

    A mutation that never applied and a mutation that survived produce the same
    output, so the arm above is only evidence once this one holds: the planted
    run carries exactly one failed panel and the clean run carries none.
    """
    planted = {
        section["id"]: section["state"] for section in run_seam(tmp_path, plant=True)["sections"]
    }
    clean = {
        section["id"]: section["state"] for section in run_seam(tmp_path, plant=False)["sections"]
    }

    assert planted.get(f"panel-{PLANTED_ID}") == STATE_FAILED, planted
    assert f"panel-{PLANTED_ID}" not in clean, clean
    assert STATE_FAILED not in clean.values(), clean


def test_a_failed_panel_says_so_where_the_panel_would_have_been(tmp_path: Path) -> None:
    """A throw leaves a note naming the panel, never an empty box and never a trace.

    NOTHING FROM THE EXCEPTION REACHES THE DOM. An exception message on this
    page can carry a file path, and a path on this machine carries the Windows
    account name - non-negotiable 3. The note is built from the panel's own id,
    which is a string this repo authored.
    """
    sections = {
        section["id"]: section["text"] for section in run_seam(tmp_path, plant=True)["sections"]
    }
    note = sections[f"panel-{PLANTED_ID}"]
    assert note.strip(), "a failed panel rendered nothing at all"
    assert PLANTED_ID in note, note
    assert "planted mount failure" not in note, note
    assert "Error" not in note, note
