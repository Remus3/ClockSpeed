"""CS-1026 - no panel module leaves a helper in the page's shared global scope.

THE FAULT IS SILENT, WHICH IS WHY IT NEEDS A BEHAVIOURAL ARM. The dashboard's
scripts are classic scripts sharing ONE global scope. A panel that declares
``var FIELDS`` or ``function textOf`` at top level publishes that binding to
every other script on the page, and a later script declaring the same name
REPLACES it without a word: a ``var`` or ``function`` redeclaration across
scripts is not an error. A mount closes over the BINDING rather than a
snapshot, so the replaced helper is what the panel calls on its next mount -
and ``mountPanel``'s ``try`` fires only on a throw, so the page shows a
normal-looking panel that is quietly wrong.

WHAT THE ARMS BELOW MEASURE, AND WHY THERE ARE TWO COLLISION RUNS.

- :func:`test_no_panel_module_adds_a_global` loads the SHIPPED scripts in the
  page's own order and records, per script, every global name it added. Every
  panel module must add none. Its detector is proved able to fire by
  :func:`test_the_global_census_fires_on_a_planted_top_level_helper`.
- :func:`test_a_planted_collision_corrupts_an_unwrapped_solve_bench` is the
  PROOF THAT THE PLANT BITES. It loads ``panel_solve.js`` with its wrapper
  removed, then a planted module that redeclares the solve bench's ``FIELDS``
  and ``vocabularyLine``, and asserts all three halves of the silent fault:
  nothing threw, the panel was NOT marked failed, AND the solve bench built the
  PLANTED module's field ids. Without the third clause an arm reading "nothing
  threw and it mounted" passes whether or not the collision did anything.
- :func:`test_a_planted_collision_leaves_the_wrapped_solve_bench_whole` runs the
  SAME plant against the SHIPPED module and asserts the bench built its own
  field ids, with the plant proved loaded into the global scope beside it.

The first collision run is what makes the second one evidence: the identical
plant is shown to corrupt the one byte-level difference - the wrapper - so a
green second run is the wrapper working rather than a plant that never landed.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.surface import config, server
from clockspeed.surface.api import solve

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The asset directory, read from the module that owns the answer.
WEB_DIR: Final = config.default_web_dir()

#: The seam's own script, loaded first on the page.
SEAM_SCRIPT: Final = "app.js"

#: The three modules CS-1026 wraps. The other four were wrapped before it.
WRAPPED_BY_THIS_ITEM: Final = ("panel_solve.js", "panel_map.js", "panel_scope.js")

#: The module the collision runs are about.
SOLVE_MODULE: Final = "panel_solve.js"

#: The ids the solve bench builds for its own four inputs, in page order. Read
#: off the endpoint's own parameter names, so a renamed parameter is a red arm
#: here rather than an expectation that follows it.
SOLVE_FIELD_IDS: Final = tuple(
    f"solve-{name}"
    for name in (
        solve.PARAM_TARGETS,
        solve.PARAM_RECIPES,
        solve.PARAM_RAW_ITEMS,
        solve.PARAM_BYPRODUCT_POLICY,
    )
)

#: The field names the planted module declares, and the ids the solve bench
#: would build from them if the collision reached it.
PLANTED_FIELD_NAMES: Final = ("planted_alpha", "planted_beta")
PLANTED_FIELD_IDS: Final = tuple(f"solve-{name}" for name in PLANTED_FIELD_NAMES)

#: The text the planted ``vocabularyLine`` answers, so a run can see which
#: helper the bench actually called.
PLANTED_VOCABULARY: Final = "planted vocabulary line"

#: The planted module. It redeclares a TABLE and a HELPER the solve bench uses,
#: the two shapes a real collision would take, and raises a flag on load so an
#: arm can prove the plant was in the global scope rather than assume it.
PLANT_SOURCE: Final = (
    '"use strict";\n'
    "var FIELDS = [\n"
    + "".join(
        f'  {{ name: "{name}", source: "policy", grammar: "planted." }},\n'
        for name in PLANTED_FIELD_NAMES
    )
    + "];\n"
    "function vocabularyLine(field, registry) {\n"
    f'  return "{PLANTED_VOCABULARY}";\n'
    "}\n"
    "globalThis.plantedCollisionLoaded = true;\n"
)

#: The opener and the closer every wrapped panel module carries.
IIFE_OPEN: Final = "(function () {\n"
IIFE_CLOSE: Final = "}());"

#: A JavaScript block comment.
_BLOCK_COMMENT: Final = re.compile(r"/\*[\s\S]*?\*/")

#: A classic script tag in ``index.html``, capturing its source.
_SCRIPT_TAG: Final = re.compile(r'<script src="([^"]+)"')

#: The panel state markers ``app.js`` writes onto a section.
STATE_MOUNTED: Final = "mounted"
STATE_FAILED: Final = "failed"

#: How long one node run may take before it is a failure rather than a slow box.
NODE_TIMEOUT_SECONDS: Final = 60.0

#: A CommonJS harness: the minimal DOM stand-in the seam touches, the SHIPPED
#: ``app.js``, then each named script in order, each through
#: ``vm.runInThisContext`` - which is what makes them share ONE global scope the
#: way classic scripts on a page do. It records what each script added to that
#: scope, whether anything threw, and what every panel section built.
HARNESS_SOURCE: Final = r""""use strict";

var fs = require("node:fs");
var path = require("node:path");
var vm = require("node:vm");

var request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
var webDir = request.web_dir;
var known = Object.create(null);

function makeNode(tag) {
  var node = {
    tagName: String(tag).toUpperCase(),
    className: "",
    id: "",
    hidden: false,
    childNodes: [],
    attributes: Object.create(null)
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
  createTextNode: function (value) {
    var node = makeNode("#text");
    node.textContent = value;
    return node;
  },
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

/* The page's load-time probes park forever, so nothing repaints behind a run. */
globalThis.fetch = function () {
  return new Promise(function () {
    return undefined;
  });
};

function describe(failure) {
  return failure && failure.message ? String(failure.message) : String(failure);
}

function load(file) {
  var source = fs.readFileSync(file, "utf8");
  vm.runInThisContext(source, { filename: path.basename(file) });
}

load(path.join(webDir, "app.js"));

/* Every mount throw is recorded, then re-thrown so the seam behaves as shipped. */
var mountThrows = {};
var realRegister = registerPanel;
globalThis.registerPanel = function (id, mountFn) {
  var wrapped = mountFn;
  if (typeof mountFn === "function") {
    wrapped = function (root, data) {
      try {
        return mountFn(root, data);
      } catch (failure) {
        mountThrows[String(id)] = describe(failure);
        throw failure;
      }
    };
  }
  return realRegister(id, wrapped);
};

var loads = [];
request.scripts.forEach(function (file) {
  var before = Object.getOwnPropertyNames(globalThis);
  var threw = null;
  try {
    load(file);
  } catch (failure) {
    threw = describe(failure);
  }
  var seen = Object.create(null);
  before.forEach(function (name) {
    seen[name] = true;
  });
  var added = Object.getOwnPropertyNames(globalThis).filter(function (name) {
    return !seen[name];
  });
  loads.push({ script: path.basename(file), threw: threw, added: added.sort() });
});

var mountPanelsThrew = null;
try {
  mountPanels({});
} catch (failure) {
  mountPanelsThrew = describe(failure);
}

function inputIds(node, into) {
  if (node.tagName === "INPUT") {
    into.push(node.id);
  }
  node.childNodes.forEach(function (child) {
    inputIds(child, into);
  });
  return into;
}

var host = lookup("panels");
process.stdout.write(
  JSON.stringify({
    loads: loads,
    mount_panels_threw: mountPanelsThrew,
    mount_throws: mountThrows,
    plant_loaded: globalThis.plantedCollisionLoaded === true,
    sections: host.childNodes.map(function (section) {
      return {
        id: section.id,
        state: section.getAttribute("data-panel-state"),
        inputs: inputIds(section, []),
        text: section.textContent
      };
    })
  })
);
"""


def read_module(name: str) -> str:
    """Read one shipped asset as text, decoded strictly as ASCII.

    Args:
        name: A filename inside the web directory.

    Returns:
        The file's text.
    """
    return (WEB_DIR / name).read_bytes().decode("ascii")


def page_script_order() -> tuple[str, ...]:
    """The classic scripts ``index.html`` loads, in the order it loads them.

    Returns:
        Every script source the page names, seam first.
    """
    return tuple(_SCRIPT_TAG.findall(read_module("index.html")))


def panel_scripts() -> tuple[str, ...]:
    """The panel modules in the page's own load order, the seam excluded.

    Returns:
        Every script after ``app.js`` that ``index.html`` loads.
    """
    order = page_script_order()
    assert order, "index.html names no script at all"
    assert order[0] == SEAM_SCRIPT, f"index.html does not load {SEAM_SCRIPT} first: {order}"
    return order[1:]


def unwrap(source: str) -> str:
    """The module with its IIFE opener and closer removed - the pre-CS-1026 shape.

    Args:
        source: A wrapped panel module's text.

    Returns:
        The same text with the wrapper's two lines taken out.

    Raises:
        AssertionError: If the wrapper is not there exactly once, in which case
            the unwrapped control would be the shipped module under another
            name and its red would prove nothing.
    """
    opens = source.count(IIFE_OPEN)
    assert opens == 1, f"the IIFE opener appears {opens} time(s); the unwrap is unsafe"
    body = source.rstrip()
    assert body.endswith(IIFE_CLOSE), "the module does not end on the IIFE closer"
    unwrapped = body[: -len(IIFE_CLOSE)].replace(IIFE_OPEN, "", 1) + "\n"
    assert IIFE_OPEN not in unwrapped, "the unwrap did not apply"
    return unwrapped


def run_page(tmp_path: Path, scripts: Sequence[Path]) -> Mapping[str, Any]:
    """Load ``app.js`` then ``scripts`` into one global scope and mount every panel.

    Args:
        tmp_path: Where the harness and its request are written.
        scripts: The scripts to load after ``app.js``, in order.

    Returns:
        The harness report: per-script load records, mount throws, whether the
        plant loaded, and one entry per panel section.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so no script was loaded and nothing was graded. "
            "This FAILS rather than skipping: a gate that skips its checks reports "
            "PASS while measuring nothing."
        )
    harness = tmp_path / "global_scope_harness.cjs"
    harness.write_bytes(HARNESS_SOURCE.encode("ascii"))
    request = tmp_path / "global_scope_request.json"
    request.write_bytes(
        json.dumps(
            {"web_dir": str(WEB_DIR), "scripts": [str(script) for script in scripts]}
        ).encode("ascii")
    )
    # Fixed argv, no shell; the interpreter is resolved off PATH.
    completed = subprocess.run(
        [node, str(harness), str(request)],
        capture_output=True,
        text=True,
        timeout=NODE_TIMEOUT_SECONDS,
        check=False,
    )
    assert completed.returncode == 0, (
        f"the global scope harness exited {completed.returncode}: {completed.stderr.strip()}"
    )
    report: Mapping[str, Any] = json.loads(completed.stdout)
    return report


def collision_run(tmp_path: Path, solve_source: str) -> Mapping[str, Any]:
    """Every shipped panel in page order with ``solve_source`` in solve's slot, then the plant.

    Args:
        tmp_path: Where the scripts and the harness are written.
        solve_source: The text loaded in place of ``panel_solve.js``.

    Returns:
        The harness report.
    """
    staged = tmp_path / "staged"
    staged.mkdir()
    scripts: list[Path] = []
    for name in panel_scripts():
        target = staged / name
        text = solve_source if name == SOLVE_MODULE else read_module(name)
        target.write_bytes(text.encode("ascii"))
        scripts.append(target)
    assert SOLVE_MODULE in {path.name for path in scripts}, "the page does not load the solve bench"
    plant = staged / "planted_collision.js"
    plant.write_bytes(PLANT_SOURCE.encode("ascii"))
    scripts.append(plant)
    return run_page(tmp_path, scripts)


def solve_section(report: Mapping[str, Any]) -> Mapping[str, Any]:
    """The solve bench's section out of a report.

    Args:
        report: A harness report.

    Returns:
        The one section the solve panel was mounted into.
    """
    hits: list[Mapping[str, Any]] = [
        section for section in report["sections"] if section["id"] == "panel-solve"
    ]
    assert len(hits) == 1, [section["id"] for section in report["sections"]]
    return hits[0]


def assert_nothing_threw(report: Mapping[str, Any]) -> None:
    """No script load, no ``mountPanels`` call and no single mount threw.

    Args:
        report: A harness report.
    """
    load_throws = {row["script"]: row["threw"] for row in report["loads"] if row["threw"]}
    assert not load_throws, load_throws
    assert report["mount_panels_threw"] is None, report["mount_panels_threw"]
    assert report["mount_throws"] == {}, report["mount_throws"]


# ---------------------------------------------------------------------------
# a. The three are wrapped, statically
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", WRAPPED_BY_THIS_ITEM)
def test_the_module_is_wrapped_in_an_iife(module: str) -> None:
    """The module opens an IIFE in its code and ends by closing it.

    The shape the four earlier-wrapped panels already carry. This is the static
    half; the census below is the behavioural half, and it is the one that says
    what the wrapper is FOR.
    """
    source = read_module(module)
    code = _BLOCK_COMMENT.sub(" ", source)
    opens = code.count(IIFE_OPEN)
    assert opens == 1, f"{module} opens {opens} IIFE(s) in its code, not 1"
    assert source.rstrip().endswith(IIFE_CLOSE), f"{module} does not close its IIFE last"


# ---------------------------------------------------------------------------
# b. No panel module adds a global - the census, and its proof of life
# ---------------------------------------------------------------------------


def test_no_panel_module_adds_a_global(tmp_path: Path) -> None:
    """Every shipped panel, loaded in the page's order, adds no global name.

    ``registerPanel`` is the seam's one door; a panel needs nothing else in the
    shared scope, so anything it puts there is a binding a later script can
    silently replace.
    """
    scripts = [WEB_DIR / name for name in panel_scripts()]
    assert {path.name for path in scripts} >= set(WRAPPED_BY_THIS_ITEM), scripts
    report = run_page(tmp_path, scripts)
    assert_nothing_threw(report)
    graded = [row["script"] for row in report["loads"]]
    assert graded == [path.name for path in scripts], graded
    leaks = {row["script"]: row["added"] for row in report["loads"] if row["added"]}
    total = len(leaks)
    assert total == 0, f"{total} panel module(s) put names in the shared global scope: {leaks}"


def test_the_global_census_fires_on_a_planted_top_level_helper(tmp_path: Path) -> None:
    """The census is proved able to see a global, on the same run shape.

    A census that recorded nothing would pass the arm above on a page full of
    leaks. The plant declares a table and a helper at top level, and both are
    named against the plant and against nothing else.
    """
    plant = tmp_path / "planted_leak.js"
    plant.write_bytes(PLANT_SOURCE.encode("ascii"))
    report = run_page(tmp_path, [plant])
    added = {row["script"]: row["added"] for row in report["loads"]}
    assert added[plant.name] == ["FIELDS", "plantedCollisionLoaded", "vocabularyLine"], added
    assert report["plant_loaded"] is True, report


def test_the_census_names_the_helpers_of_an_unwrapped_solve_bench(tmp_path: Path) -> None:
    """The pre-CS-1026 solve bench is seen leaking exactly what it used to leak.

    This is the census graded on the real module rather than a synthetic plant:
    the unwrapped text is derived from the shipped bytes, so the only difference
    between this run and the clean one is the wrapper itself.
    """
    unwrapped = tmp_path / SOLVE_MODULE
    unwrapped.write_bytes(unwrap(read_module(SOLVE_MODULE)).encode("ascii"))
    report = run_page(tmp_path, [unwrapped])
    added = set(report["loads"][0]["added"])
    for name in ("FIELDS", "textOf", "approximateDecimal", "vocabularyLine"):
        assert name in added, f"{name} was not seen leaking from the unwrapped bench: {added}"


# ---------------------------------------------------------------------------
# c. The planted collision - proved to bite, then proved to be refused
# ---------------------------------------------------------------------------


def test_a_planted_collision_corrupts_an_unwrapped_solve_bench(tmp_path: Path) -> None:
    """Unwrapped, the plant silently rebuilds the solve bench from ITS fields.

    ALL THREE HALVES OF THE SILENT FAULT, ASSERTED TOGETHER: nothing threw, the
    panel was NOT marked failed, AND the bench built the PLANTED module's field
    ids and called the planted helper. The third half is what makes this a
    proof: without it, "nothing threw and it mounted" is also what a plant that
    never reached the bench would produce.
    """
    report = collision_run(tmp_path, unwrap(read_module(SOLVE_MODULE)))
    assert report["plant_loaded"] is True, "the plant never loaded; this run grades nothing"
    assert_nothing_threw(report)

    section = solve_section(report)
    assert section["state"] == STATE_MOUNTED, section["state"]
    assert section["state"] != STATE_FAILED
    assert tuple(section["inputs"]) == PLANTED_FIELD_IDS, section["inputs"]
    assert PLANTED_VOCABULARY in section["text"], section["text"]


def test_a_planted_collision_leaves_the_wrapped_solve_bench_whole(tmp_path: Path) -> None:
    """Shipped, the same plant sits in the global scope and the bench ignores it.

    The plant is proved loaded - its flag is up - so a green here is the wrapper
    refusing the collision rather than a plant that never landed. Every other
    panel on the page is proved still mounted beside it.
    """
    report = collision_run(tmp_path, read_module(SOLVE_MODULE))
    assert report["plant_loaded"] is True, "the plant never loaded; this run grades nothing"
    assert_nothing_threw(report)

    section = solve_section(report)
    assert section["state"] == STATE_MOUNTED, section["state"]
    assert tuple(section["inputs"]) == SOLVE_FIELD_IDS, section["inputs"]
    assert PLANTED_VOCABULARY not in section["text"], section["text"]

    states = {row["id"]: row["state"] for row in report["sections"]}
    expected = {f"panel-{name[len('panel_') : -len('.js')]}" for name in panel_scripts()}
    assert set(states) == expected, states
    unmounted = {panel for panel, state in states.items() if state != STATE_MOUNTED}
    assert not unmounted, unmounted


def test_the_page_loads_every_published_panel_module() -> None:
    """The load order read off ``index.html`` covers every module the server serves.

    The collision and census runs take their script list from the page, so a
    module the server publishes and the page never loads would be graded by
    neither - this pins the two lists to each other.
    """
    published = {name for name in server.ASSET_NAMES if name.startswith("panel_")}
    loaded = set(panel_scripts())
    assert loaded == published, {"page_only": loaded - published, "server_only": published - loaded}
