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
  page's own order, with ``window`` as the global object, and records every
  global-object property each script added on load and every one the mounts
  added after it. It then takes :func:`census` of each module alone, which
  also sees a top-level ``let``, ``const`` or ``class``. Every panel module
  must add none. Each reading is proved able to fire by a planted arm below.
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
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from clockspeed.surface import config, server
from clockspeed.surface.api import solve
from tests.surface import panel_harness

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

#: The characters an ASCII identifier starts with, and those it continues with.
_IDENT_START: Final = frozenset(string.ascii_letters + "_$")
_IDENT_PART: Final = _IDENT_START | frozenset(string.digits)

#: An identifier's unicode escape, in either spelling JavaScript admits.
_UNICODE_ESCAPE: Final = re.compile(r"\\u(?:\{([0-9A-Fa-f]+)\}|([0-9A-Fa-f]{4}))")

#: Keywords after which a "/" opens a regular expression rather than dividing.
_REGEX_AFTER_KEYWORD: Final = frozenset(
    {
        "await",
        "case",
        "delete",
        "do",
        "else",
        "in",
        "instanceof",
        "new",
        "of",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }
)

#: A classic script tag in ``index.html``, capturing its source.
_SCRIPT_TAG: Final = re.compile(r'<script src="([^"]+)"')

#: The panel state markers ``app.js`` writes onto a section.
STATE_MOUNTED: Final = "mounted"
STATE_FAILED: Final = "failed"

#: How long one node run may take before it is a failure rather than a slow box.
#: A RUN limit: it counts from the start marker, never from the spawn (CS-1329).
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

/*
  window IS THE GLOBAL OBJECT, as it is in a browser. A separate stub would let
  a module hang a helper on window from inside its IIFE and pass the census.
*/
globalThis.addEventListener = function () {
  return undefined;
};
globalThis.window = globalThis;

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

/*
  THE GLOBAL OBJECT IS READ AGAIN AROUND THE MOUNTS. Loading a module runs its
  top level only; a helper published from inside a mount appears here and
  nowhere earlier.
*/
var beforeMount = Object.create(null);
Object.getOwnPropertyNames(globalThis).forEach(function (name) {
  beforeMount[name] = true;
});
var mountPanelsThrew = null;
try {
  mountPanels({});
} catch (failure) {
  mountPanelsThrew = describe(failure);
}
var mountAdded = Object.getOwnPropertyNames(globalThis)
  .filter(function (name) {
    return !beforeMount[name];
  })
  .sort();

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
    mount_added: mountAdded,
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


#: A CommonJS harness that takes the census of ONE script in a fresh realm. The
#: realm's ``window`` is its own global object and ``registerPanel`` is a stub,
#: which is all a panel module's top level may touch. See :func:`census`.
CENSUS_SOURCE: Final = r""""use strict";

var fs = require("node:fs");
var vm = require("node:vm");

var request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
var source = fs.readFileSync(request.script, "utf8");

function realm() {
  var context = vm.createContext({});
  vm.runInContext(
    "globalThis.window = globalThis;" +
      "globalThis.document = {};" +
      "globalThis.registerPanel = function () { return true; };",
    context
  );
  return context;
}

function propertiesOf(context) {
  return vm.runInContext("Object.getOwnPropertyNames(globalThis)", context);
}

function bound(context) {
  /* The names a "let" redeclaration refuses: already bound at script scope. */
  return request.names.filter(function (name) {
    try {
      vm.runInContext("let " + name + ";", context);
      return false;
    } catch (failure) {
      return true;
    }
  });
}

var baseline = bound(realm());
var loaded = realm();
var before = propertiesOf(loaded);
var threw = null;
try {
  vm.runInContext(source, loaded);
} catch (failure) {
  threw = failure && failure.message ? String(failure.message) : String(failure);
}
var added = propertiesOf(loaded).filter(function (name) {
  return before.indexOf(name) < 0;
});
var declared = bound(loaded).filter(function (name) {
  return baseline.indexOf(name) < 0;
});

process.stdout.write(
  JSON.stringify({ threw: threw, added: added.sort(), declared: declared.sort() })
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
    completed = panel_harness.run_node(
        node,
        harness,
        str(request),
        label="the global scope harness",
        run_timeout=NODE_TIMEOUT_SECONDS,
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

    # AND AFTER EVERY PANEL HAS MOUNTED, since a mount runs code a load does not.
    mounted = list(report["mount_added"])
    assert mounted == [], f"mounting the panels put names in the shared global scope: {mounted}"

    # THE ISOLATED CENSUS TOO, which alone sees a script-scope let, const or
    # class: the page run above reads global-object properties only.
    isolated = {path.name: sorted(census(tmp_path, path)) for path in scripts}
    leaking = {name: found for name, found in isolated.items() if found}
    count = len(leaking)
    assert count == 0, f"{count} panel module(s) bind names at script scope: {leaking}"


def test_the_global_census_fires_on_a_planted_top_level_helper(tmp_path: Path) -> None:
    """Both censuses are proved able to see a global, each on its own run shape.

    A census that recorded nothing would pass the arm above on a page full of
    leaks. The plant declares a table and a helper at top level and raises a
    flag through ``globalThis``, and exactly those three are named.
    """
    plant = tmp_path / "planted_leak.js"
    plant.write_bytes(PLANT_SOURCE.encode("ascii"))
    expected = ["FIELDS", "plantedCollisionLoaded", "vocabularyLine"]
    report = run_page(tmp_path, [plant])
    added = {row["script"]: row["added"] for row in report["loads"]}
    assert added[plant.name] == expected, added
    assert report["plant_loaded"] is True, report
    seen = sorted(census(tmp_path, plant))
    assert seen == expected, seen


def _read_identifier(source: str, at: int) -> tuple[str, int]:
    """One identifier starting at ``at``, with its unicode escapes decoded.

    Args:
        source: The script's full text.
        at: Where the identifier starts.

    Returns:
        The decoded name, and the index just past it.
    """
    chars: list[str] = []
    while at < len(source):
        char = source[at]
        if char in _IDENT_PART:
            chars.append(char)
            at += 1
            continue
        escape = _UNICODE_ESCAPE.match(source, at) if char == "\\" else None
        if escape is None:
            break
        chars.append(chr(int(escape.group(1) or escape.group(2), 16)))
        at = escape.end()
    return "".join(chars), at


def _skip_quoted(source: str, at: int, quote: str) -> int:
    """The index just past a string literal whose body starts at ``at``.

    Args:
        source: The script's full text.
        at: The first character after the opening quote.
        quote: The quote character that closes it.

    Returns:
        The index after the closing quote, or of the line end that leaves an
        unterminated literal (which the script could not have parsed with).
    """
    while at < len(source):
        char = source[at]
        if char == "\\":
            at += 2
            continue
        if char == quote:
            return at + 1
        if char == "\n":
            return at
        at += 1
    return at


def _skip_template(source: str, at: int) -> tuple[int, bool]:
    """Scan a template literal's text from ``at`` to its end or its next substitution.

    Args:
        source: The script's full text.
        at: The first character of template text.

    Returns:
        The index just past the closing backtick or the ``${`` opener, and
        whether a substitution - which is code - was entered.
    """
    while at < len(source):
        char = source[at]
        if char == "\\":
            at += 2
            continue
        if char == "`":
            return at + 1, False
        if source.startswith("${", at):
            return at + 2, True
        at += 1
    return at, False


def _skip_regex(source: str, at: int) -> int:
    """The index just past a regular-expression literal whose body starts at ``at``.

    Args:
        source: The script's full text.
        at: The first character after the opening slash.

    Returns:
        The index after the closing slash and any flags.
    """
    in_class = False
    while at < len(source):
        char = source[at]
        if char == "\\":
            at += 2
            continue
        if char == "\n":
            return at
        if in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "/":
            at += 1
            while at < len(source) and source[at] in _IDENT_PART:
                at += 1
            return at
        at += 1
    return at


def probe_names(source: str) -> tuple[str, ...]:
    r"""Every identifier in a script's code - the names the lexical probe tries.

    ONE LEFT-TO-RIGHT PASS, so each delimiter is read in the state it actually
    sits in: a ``//`` or ``/*`` inside a string is text, a quote inside a
    comment is prose, and a template literal's ``${ }`` substitutions are code
    while its text is not. Identifiers are collected in code only, with
    ``\uXXXX`` and ``\u{X}`` escapes decoded, so ``let leak`` is probed
    as ``leak``. A script-scope binding can only be named by such an
    identifier, so every binding the script declares is among the names
    returned - with ONE NAMED RESIDUAL: whether a ``/`` opens a regular
    expression or divides is decided from the token before it, the usual
    heuristic, which misreads a regular expression written directly after a
    ``)``, ``]`` or ``}`` - an ``if (x) /re/.test(y)``, say - as a division.
    :func:`test_no_shipped_panel_module_holds_a_regular_expression_literal`
    pins that no shipped panel module holds a regular expression literal at
    all, so the residual has no instance there.

    Args:
        source: The script's full text.

    Returns:
        Each distinct identifier in the script's code, sorted.
    """
    return tuple(sorted(_scan(source)[0]))


def regex_literal_count(source: str) -> int:
    """How many regular expression literals :func:`probe_names` read in a script.

    Args:
        source: The script's full text.

    Returns:
        The count.
    """
    return _scan(source)[1]


def _scan(source: str) -> tuple[frozenset[str], int]:
    """The one pass behind :func:`probe_names` and :func:`regex_literal_count`.

    Args:
        source: The script's full text.

    Returns:
        The identifiers in the script's code, and how many regular expression
        literals it read.
    """
    state = _ScanState()
    at = 0
    while at < len(source):
        skipped = _step_over_literal(source, at, state)
        at = _step_through_code(source, at, state) if skipped is None else skipped
    return frozenset(state.names), state.regexes


@dataclass
class _ScanState:
    """What the one pass carries between characters.

    Attributes:
        names: The identifiers collected so far.
        regexes: How many regular expression literals were read.
        substitutions: One entry per open brace, True where the brace opened a
            template substitution - so its closing brace resumes template text.
        regex_allowed: Whether a ``/`` here would open a regular expression.
    """

    names: set[str] = field(default_factory=set)
    regexes: int = 0
    substitutions: list[bool] = field(default_factory=list)
    regex_allowed: bool = True


def _resume_template(source: str, at: int, state: _ScanState) -> int:
    """Read template text from ``at`` and record whether a substitution opened.

    Args:
        source: The script's full text.
        at: The first character of template text.
        state: The pass's state, updated in place.

    Returns:
        The index the pass continues from.
    """
    at, entered = _skip_template(source, at)
    if entered:
        state.substitutions.append(True)
    state.regex_allowed = entered
    return at


def _step_over_literal(source: str, at: int, state: _ScanState) -> int | None:
    """Skip a comment, string, template text or regular expression starting at ``at``.

    Args:
        source: The script's full text.
        at: The current index, in code.
        state: The pass's state, updated in place.

    Returns:
        The index past the skipped span, or None when none starts here.
    """
    char = source[at]
    if source.startswith("//", at):
        end = source.find("\n", at)
        return len(source) if end < 0 else end
    if source.startswith("/*", at):
        end = source.find("*/", at + 2)
        return len(source) if end < 0 else end + 2
    if char in "\"'":
        state.regex_allowed = False
        return _skip_quoted(source, at + 1, char)
    if char == "`":
        return _resume_template(source, at + 1, state)
    if char == "/" and state.regex_allowed:
        state.regexes += 1
        state.regex_allowed = False
        return _skip_regex(source, at + 1)
    return None


def _step_through_code(source: str, at: int, state: _ScanState) -> int:
    """Consume one code token - an identifier, a number or one character.

    Args:
        source: The script's full text.
        at: The current index, in code.
        state: The pass's state, updated in place.

    Returns:
        The index past the token.
    """
    char = source[at]
    if char in _IDENT_START or source.startswith("\\u", at):
        name, end = _read_identifier(source, at)
        if name:
            state.names.add(name)
        state.regex_allowed = name in _REGEX_AFTER_KEYWORD
        return max(end, at + 1)
    if char in string.digits:
        while at < len(source) and (source[at] in _IDENT_PART or source[at] == "."):
            at += 1
        state.regex_allowed = False
        return at
    if char == "}" and state.substitutions and state.substitutions[-1]:
        state.substitutions.pop()
        return _resume_template(source, at + 1, state)
    if char == "{":
        state.substitutions.append(False)
    elif char == "}" and state.substitutions:
        state.substitutions.pop()
    if not char.isspace():
        state.regex_allowed = char not in ")]}"
    return at + 1


def census(tmp_path: Path, script: Path) -> set[str]:
    """Every name one script leaves in the shared scope, however it put it there.

    The script runs ALONE in a fresh realm whose ``window`` is its global object.
    Two readings are unioned: the global-object properties it added - a
    top-level ``var`` or ``function``, or anything assigned through ``window``
    or ``globalThis`` - and the script-scope bindings it declared, which a
    top-level ``let``, ``const`` or ``class`` makes WITHOUT a global property.
    The second is read by declaring ``let name`` for each identifier in the
    script: a redeclaration throws exactly when the name is already bound at
    script scope. The same probe on a realm that never loaded the script is the
    baseline, so a builtin or a keyword that throws either way is not counted.

    Args:
        tmp_path: Where the harness and its request are written.
        script: The script to take the census of.

    Returns:
        The names the script added.

    Raises:
        AssertionError: If the script threw on load, since a census of a script
            that stopped halfway grades only the half that ran.
    """
    node = shutil.which("node")
    if node is None:
        pytest.fail(
            "node is not on PATH, so no census was taken. This FAILS rather than "
            "skipping: a gate that skips its checks reports PASS while measuring nothing."
        )
    source = script.read_bytes().decode("ascii")
    scratch = tmp_path / f"census_{script.name}"
    scratch.mkdir(parents=True, exist_ok=True)
    harness = scratch / "census_harness.cjs"
    harness.write_bytes(CENSUS_SOURCE.encode("ascii"))
    request = scratch / "census_request.json"
    request.write_bytes(
        json.dumps({"script": str(script), "names": list(probe_names(source))}).encode("ascii")
    )
    completed = panel_harness.run_node(
        node,
        harness,
        str(request),
        label=f"the census harness for {script.name}",
        run_timeout=NODE_TIMEOUT_SECONDS,
    )
    assert completed.returncode == 0, (
        f"the census harness exited {completed.returncode}: {completed.stderr.strip()}"
    )
    report: Mapping[str, Any] = json.loads(completed.stdout)
    threw = report["threw"]
    assert threw is None, f"{script.name} threw on load: {threw}"
    return set(report["added"]) | set(report["declared"])


def _planted_copy(tmp_path: Path, name: str, anchor: str, insert: str) -> Path:
    """A copy of a shipped module with ``insert`` placed immediately before ``anchor``.

    Args:
        tmp_path: Where the copy is written.
        name: The shipped module to copy.
        anchor: Text that must occur exactly once in the module.
        insert: The text planted before it.

    Returns:
        The planted copy's path, under the shipped module's own file name.

    Raises:
        AssertionError: If the anchor is not there exactly once, in which case
            the plant never applied and a green run would grade nothing.
    """
    source = read_module(name)
    hits = source.count(anchor)
    assert hits == 1, f"the plant anchor occurs {hits} time(s) in {name}"
    planted = source.replace(anchor, insert + anchor, 1)
    assert insert in planted, "the plant did not apply"
    target = tmp_path / "planted" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(planted.encode("ascii"))
    return target


def test_the_census_sees_a_helper_published_on_window(tmp_path: Path) -> None:
    """A wrapped module that hangs a helper on ``window`` is still a leak.

    ``window`` IS the global object in a browser, so ``window.name = value``
    from inside an IIFE is exactly the shared-scope binding the wrapper exists
    to prevent. A harness whose ``window`` were a separate stub would let this
    through, which is how an adversary refuted the first census.
    """
    plant = _planted_copy(
        tmp_path,
        SOLVE_MODULE,
        'registerPanel("solve",',
        "window.approximateDecimal = approximateDecimal;\n",
    )
    seen = sorted(census(tmp_path, plant))
    assert "approximateDecimal" in seen, seen


@pytest.mark.parametrize(
    "declaration",
    ["let mapZoomState = 1;\n", "const mapZoomState = 1;\n", "class mapZoomState {}\n"],
    ids=["let", "const", "class"],
)
def test_the_census_sees_a_top_level_lexical_binding(tmp_path: Path, declaration: str) -> None:
    """A top-level ``let``, ``const`` or ``class`` beside the IIFE is a leak.

    A script-scope lexical binding is shared by every classic script on the
    page yet is NOT a property of the global object, so a census that lists
    global properties alone is blind to it - the second way the first census
    was refuted. Planted before ``panel_map.js``'s wrapper, outside it.
    """
    plant = _planted_copy(tmp_path, "panel_map.js", IIFE_OPEN, declaration)
    seen = sorted(census(tmp_path, plant))
    assert "mapZoomState" in seen, seen


def test_the_page_census_sees_a_global_a_mount_publishes(tmp_path: Path) -> None:
    """A helper published from INSIDE a mount is a leak, and only a mount shows it.

    Loading a module runs its top level and no more; ``window.leakL = data``
    written inside ``mountSolve`` runs when the seam mounts the panel. The page
    census therefore reads the global object again after ``mountPanels`` and
    names what the mounts added.
    """
    plant = _planted_copy(
        tmp_path,
        SOLVE_MODULE,
        "  var registry = data && data.registry",
        "  window.leakL = data;\n",
    )
    scripts = [plant if name == SOLVE_MODULE else WEB_DIR / name for name in panel_scripts()]
    report = run_page(tmp_path, scripts)
    assert_nothing_threw(report)
    seen = sorted(report["mount_added"])
    assert "leakL" in seen, seen


def test_probe_names_reads_past_a_url_inside_a_string() -> None:
    """A ``//`` inside a string is text, so the identifiers after it are collected.

    ``panel_map.js`` names the SVG namespace in a string literal on the same
    line as the ``tag`` argument after it. A scan that took the ``//`` for a
    line comment dropped the rest of that line - so a binding declared there
    would never have been probed.
    """
    lines = [line for line in read_module("panel_map.js").split("\n") if "http://" in line]
    assert len(lines) == 1, lines
    names = probe_names(lines[0])
    assert "tag" in names, names
    assert "createElementNS" in names, names
    planted = probe_names('var ns = "http://example.invalid/"; var leakA = 1;\n')
    assert "leakA" in planted, planted


def test_no_shipped_panel_module_holds_a_regular_expression_literal() -> None:
    """The scanner's one named residual has no instance in a shipped panel.

    :func:`probe_names` decides regex-versus-division from the token before a
    slash. Every slash in a shipped panel module is read as a division, so no
    module rests on that decision being right for a regular expression.
    """
    found = {name: regex_literal_count(read_module(name)) for name in panel_scripts()}
    holding = {name: count for name, count in found.items() if count}
    assert not holding, holding


def test_the_scanner_reads_a_regex_literal_as_one_token() -> None:
    """The control: a quote inside a regular expression opens no string."""
    source = 'var pattern = /a"b/g;\nvar leakR = 1;\n'
    assert regex_literal_count(source) == 1
    names = probe_names(source)
    assert "leakR" in names, names
    divided = "var half = total / 2;\nvar leakD = 1;\n"
    assert regex_literal_count(divided) == 0
    assert "leakD" in probe_names(divided)


def test_the_census_sees_a_binding_between_comment_markers_in_strings(tmp_path: Path) -> None:
    """Comment delimiters inside strings do not hide the code between them."""
    plant = _planted_copy(
        tmp_path, "panel_map.js", IIFE_OPEN, 'void "/*";\nlet leakJ = 2;\nvoid "*/";\n'
    )
    seen = sorted(census(tmp_path, plant))
    assert "leakJ" in seen, seen


def test_the_census_sees_a_binding_spelled_with_a_unicode_escape(tmp_path: Path) -> None:
    r"""``let leakK`` binds ``leakK``, and the probe decodes the escape to see it."""
    backslash = chr(92)
    plant = _planted_copy(
        tmp_path, "panel_map.js", IIFE_OPEN, "let " + backslash + "u006ceakK = 1;\n"
    )
    seen = sorted(census(tmp_path, plant))
    assert "leakK" in seen, seen


def test_the_census_names_the_helpers_of_an_unwrapped_solve_bench(tmp_path: Path) -> None:
    """The pre-CS-1026 solve bench is seen leaking exactly what it used to leak.

    This is the census graded on the real module rather than a synthetic plant:
    the unwrapped text is derived from the shipped bytes, so the only difference
    between this run and the clean one is the wrapper itself.
    """
    unwrapped = tmp_path / SOLVE_MODULE
    unwrapped.write_bytes(unwrap(read_module(SOLVE_MODULE)).encode("ascii"))
    added = census(tmp_path, unwrapped)
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
