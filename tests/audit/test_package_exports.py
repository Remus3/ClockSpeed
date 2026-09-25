"""CS-1023: the warning codes the audit package re-exports, and the rule choosing them.

THE RULE. ``clockspeed/audit/__init__.py`` re-exports EVERY ``WARN_*`` constant
that a module inside the ``clockspeed.audit`` package DEFINES - a module-level
assignment to that name in that module's own source - and no other ``WARN_*``
name at all. The set is DERIVED here by walking the package and parsing each
module's source, never listed by hand, so a code added to any module in the
package reddens the arm until the package re-exports it.

WHY "DEFINES" AND NOT "HAS IN ITS NAMESPACE". ``placement.py`` imports
``WARN_NODE_SEMANTICS_UNAVAILABLE`` from ``clockspeed.save.world`` and raises it,
so the name is reachable as ``placement.WARN_NODE_SEMANTICS_UNAVAILABLE``. That
code is OWNED by the save layer; re-exporting it from the audit layer would make
the audit package a second publisher of a save-layer fact. A walk over module
namespaces would sweep it in, which is why the walk reads each module's source
and counts an assignment, never an import.

Before this arm the package re-exported three of the five codes ``placement.py``
defines and none of the codes the other five modules define, with nothing saying
why - the omission was the arbitrary thing, not any one missing name.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path
from typing import Final

import clockspeed.audit as audit_package
from clockspeed.audit import placement
from clockspeed.save import world

#: The prefix every warning-code constant carries.
WARNING_PREFIX: Final = "WARN_"


#: Nodes that open a NEW scope for every binding made inside them. A name bound
#: inside one is not a module constant, so the walk does not descend into them.
_OWN_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

#: Comprehensions: their loop variables are their own, but a walrus inside one
#: binds in the ENCLOSING scope (PEP 572), so the walk descends into them and
#: counts a walrus target alone.
_COMPREHENSIONS: Final = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def defined_warning_names(source: str) -> frozenset[str]:
    """Return every ``WARN_*`` name a module's source binds at module scope.

    COUNTED - every ``Name`` STORED at module scope, whatever statement makes
    it: a plain or annotated assignment, a tuple or starred unpack, a binding
    inside an ``if``, ``else``, ``try`` or ``except`` block, a ``for`` or
    ``with`` target, an augmented assignment, and a walrus - including a walrus
    inside a comprehension at module scope, nested or not, because PEP 572
    binds that in the enclosing scope.

    NOT COUNTED - an ``import`` or ``from ... import`` binding (an alias node,
    never a stored ``Name``: the module that assigns a code owns it, a module
    that imports one only uses it); a comprehension's own loop variable; and
    anything bound inside a function, a class body or a lambda, none of which
    is a module constant.

    FAILS CLOSED, BUT NOT HERE - a name bound at run time through a door into
    a module namespace (``globals()[...] =``, an aliased ``_ns = globals()``,
    ``exec``, ``setattr`` on a module, a ``__dict__`` store, and the rest) is
    one no static read can recover. :func:`namespace_doors` refuses every
    REFERENCE to each door in :data:`NAMESPACE_DOORS` - not only a call, so an
    alias is caught where it is taken - plus any store to a ``WARN_*``
    attribute, and an arm holds every source file of the package,
    ``__init__.py`` included, free of them. So the derived set here cannot be
    short by one through any door that arm names without that arm reddening.

    RESIDUAL, stated so it is not read as covered: a door reached only through
    a name built from a string at run time, with no member of
    :data:`NAMESPACE_DOORS` referenced - for example ``operator.attrgetter``
    over a concatenated dunder - is invisible to any static read and is not
    refused - a limit of every static read, named here rather than closed.

    The first draft read top-level ``Assign`` nodes only; two adversary passes
    named the holes this docstring now lists, and a third named the aliased
    namespace and the ``exec`` that a call-shaped detector let through.

    Args:
        source: The module's source text.

    Returns:
        The names.
    """
    names: set[str] = set()
    pending: list[tuple[ast.AST, bool]] = [(ast.parse(source), False)]
    while pending:
        node, walrus_only = pending.pop()
        if isinstance(node, _OWN_SCOPES):
            continue
        if isinstance(node, _COMPREHENSIONS):
            walrus_only = True
        if walrus_only:
            target = node.target if isinstance(node, ast.NamedExpr) else None
            if isinstance(target, ast.Name) and target.id.startswith(WARNING_PREFIX):
                names.add(target.id)
        elif (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id.startswith(WARNING_PREFIX)
        ):
            names.add(node.id)
        pending.extend((child, walrus_only) for child in ast.iter_child_nodes(node))
    return frozenset(names)


#: Every name that opens a door into a module namespace a static read cannot
#: follow. Refused on ANY reference - a load, a store, an attribute, an import
#: name - not only on a call, so ``_ns = globals()`` is caught at ``globals``
#: before the alias ever writes. The ruled seven (``globals``, ``vars``,
#: ``exec``, ``eval``, ``setattr``, ``__dict__`` and ``sys.modules`` - the last
#: as the ``modules`` attribute or import name, so an aliased ``sys`` is caught
#: too) plus their siblings: ``locals`` is the module namespace at module scope,
#: ``compile`` feeds ``exec``, ``getattr`` reaches ``__dict__`` by string,
#: ``__import__``, ``__builtins__``, ``builtins`` and ``importlib`` hand back a
#: module or the builtins whole, ``__globals__`` is a function's module
#: namespace, ``__setattr__`` is ``setattr`` by another name, and
#: ``f_globals`` and ``f_locals`` are a frame's.
NAMESPACE_DOORS: Final = frozenset(
    {
        "globals",
        "vars",
        "exec",
        "eval",
        "setattr",
        "__dict__",
        "modules",
        "locals",
        "compile",
        "getattr",
        "__import__",
        "__builtins__",
        "builtins",
        "importlib",
        "__globals__",
        "__setattr__",
        "f_globals",
        "f_locals",
    }
)


def namespace_doors(source: str) -> list[str]:
    """Every reference in a module's source to a door into a module namespace.

    FAIL CLOSED, over the WHOLE module rather than module scope alone, because
    ``globals()`` inside a function still writes the module. Each finding is
    ``line N: <name>``, in line order, for:

    - a ``Name`` whose identifier is in :data:`NAMESPACE_DOORS`, in any context;
    - an ``Attribute`` whose attribute is in :data:`NAMESPACE_DOORS`;
    - an ``import`` or ``from ... import`` that spells one as a dotted part of
      the module, the imported name or the alias;
    - a store to a ``WARN_*`` attribute of any object, which is how one module
      binds a code in ANOTHER module's namespace without that module's source
      spelling it.

    Args:
        source: The module's source text.

    Returns:
        The findings.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name) and node.id in NAMESPACE_DOORS:
            found.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute):
            if node.attr in NAMESPACE_DOORS:
                found.append((node.lineno, node.attr))
            elif isinstance(node.ctx, ast.Store) and node.attr.startswith(WARNING_PREFIX):
                found.append((node.lineno, f"store to attribute {node.attr}"))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            spelled = [alias.name for alias in node.names]
            spelled += [alias.asname for alias in node.names if alias.asname]
            if isinstance(node, ast.ImportFrom) and node.module:
                spelled.append(node.module)
            doors = {part for dotted in spelled for part in dotted.split(".")} & NAMESPACE_DOORS
            found.extend((node.lineno, door) for door in doors)
    return [f"line {line}: {name}" for line, name in sorted(found)]


def package_sources() -> list[Path]:
    """Every Python source file of the audit package, ``__init__.py`` included.

    Read from the package directory rather than from ``pkgutil``, which walks
    submodules only and would leave ``__init__.py`` unscanned.

    Returns:
        The paths, sorted.
    """
    package_dir = Path(audit_package.__file__).parent
    return sorted(path for path in package_dir.rglob("*.py") if "__pycache__" not in path.parts)


def defining_modules() -> dict[str, str]:
    """Walk the audit package and map each defined ``WARN_*`` name to its module.

    Returns:
        Name to the dotted name of the one module that defines it.
    """
    owners: dict[str, str] = {}
    collisions: list[str] = []
    for info in pkgutil.walk_packages(audit_package.__path__, audit_package.__name__ + "."):
        module = importlib.import_module(info.name)
        source_path = module.__file__
        assert source_path is not None, info.name
        for name in defined_warning_names(Path(source_path).read_text(encoding="utf-8")):
            if name in owners:
                collisions.append(name)
            owners[name] = info.name
    # Two modules defining one name would make the re-export ambiguous about
    # which value the package serves, so a collision is itself a failure.
    assert collisions == []
    return owners


def test_the_package_re_exports_exactly_the_codes_its_modules_define() -> None:
    expected = frozenset(defining_modules())
    exported = frozenset(name for name in audit_package.__all__ if name.startswith(WARNING_PREFIX))

    missing = sorted(expected - exported)
    extra = sorted(exported - expected)
    assert missing == []
    assert extra == []


def test_every_re_exported_code_is_bound_to_its_defining_module_value() -> None:
    wrong: list[str] = []
    for name, owner in sorted(defining_modules().items()):
        served = getattr(audit_package, name, None)
        if served is None or served != getattr(importlib.import_module(owner), name):
            wrong.append(name)

    assert wrong == []


def test_the_walk_reaches_every_module_file_in_the_package() -> None:
    # A walk that silently skipped a module would derive a short expected set
    # and the equality arm above would pass against a short re-export.
    package_dir = Path(audit_package.__file__).parent
    on_disk = frozenset(path.stem for path in package_dir.glob("*.py") if path.stem != "__init__")
    walked = frozenset(
        info.name.rsplit(".", 1)[-1]
        for info in pkgutil.walk_packages(audit_package.__path__, audit_package.__name__ + ".")
    )

    assert walked == on_disk


def test_the_walk_is_not_vacuous_and_counts_the_placement_codes() -> None:
    # Control: the derivation must see the five codes placement.py assigns,
    # including the two the package omitted before CS-1023. A parser that
    # returned nothing would make the equality arm pass against an empty set.
    owners = defining_modules()
    placement_codes = sorted(
        name for name, owner in owners.items() if owner == "clockspeed.audit.placement"
    )

    assert placement_codes == [
        "WARN_BUILT_CLASS_NOT_PLOTTED",
        "WARN_BUILT_TRANSFORM_ABSENT",
        "WARN_PLACEMENT_BOUNDS_UNDEFINED",
        "WARN_PLACEMENT_COORDINATE_NON_FINITE",
        "WARN_PLACEMENT_ORIENTATION_NON_FINITE",
    ]


def test_an_imported_save_layer_code_is_not_counted_as_defined_here() -> None:
    # Control for the "defines, not imports" half of the rule: placement.py
    # holds the save layer's code in its namespace and must not own it.
    save_owned = "WARN_NODE_SEMANTICS_UNAVAILABLE"
    assert getattr(placement, save_owned) == getattr(world, save_owned)
    assert save_owned not in defining_modules()
    assert save_owned not in audit_package.__all__


def test_the_source_parser_separates_an_assignment_from_an_import() -> None:
    source = (
        "from elsewhere import WARN_IMPORTED\n"
        "import WARN_MODULE\n"
        "WARN_PLAIN = 'plain'\n"
        "WARN_ANNOTATED: str = 'annotated'\n"
        "NOT_A_WARNING = 'other'\n"
        "def inner() -> None:\n"
        "    WARN_LOCAL = 'local'\n"
    )

    assert defined_warning_names(source) == frozenset({"WARN_PLAIN", "WARN_ANNOTATED"})


def test_the_source_parser_reaches_every_module_scope_binding_form() -> None:
    # An adversary named two holes in a top-level-Assign-only parser: a code
    # bound by tuple unpacking and a code bound inside an ``if`` block. Either
    # would define a module constant the derivation cannot see, so the
    # expected set would come up short and the equality arm would pass against
    # a short re-export. Every module-scope binding form is graded here; the
    # nested scopes - a function, a class body, a comprehension - are not
    # module constants and stay out.
    source = (
        "WARN_UNPACK_A, (WARN_UNPACK_B, *WARN_STARRED) = 'a', ('b', 'c')\n"
        "if True:\n"
        "    WARN_IN_IF = 'if'\n"
        "else:\n"
        "    WARN_IN_ELSE = 'else'\n"
        "try:\n"
        "    WARN_IN_TRY = 'try'\n"
        "except ValueError:\n"
        "    WARN_IN_EXCEPT = 'except'\n"
        "with open('x') as WARN_WITH_TARGET:\n"
        "    pass\n"
        "for WARN_LOOP_TARGET in ():\n"
        "    pass\n"
        "WARN_AUGMENTED += 'x'\n"
        "(WARN_WALRUS := 'w')\n"
        "class Holder:\n"
        "    WARN_CLASS_BODY = 'class'\n"
        "_ = [WARN_COMPREHENSION for WARN_COMPREHENSION in ()]\n"
        "_ = [WARN_WALRUS_IN_COMPREHENSION := v for v in ('x',)]\n"
        "_ = {k: [WARN_WALRUS_NESTED := k for _ in ()] for k in ()}\n"
        "_ = (lambda: (WARN_WALRUS_IN_LAMBDA := 1))\n"
        "def later() -> None:\n"
        "    _ = [WARN_WALRUS_IN_FUNCTION := v for v in ()]\n"
        "del WARN_DELETED\n"
    )

    assert defined_warning_names(source) == frozenset(
        {
            "WARN_UNPACK_A",
            "WARN_UNPACK_B",
            "WARN_STARRED",
            "WARN_IN_IF",
            "WARN_IN_ELSE",
            "WARN_IN_TRY",
            "WARN_IN_EXCEPT",
            "WARN_WITH_TARGET",
            "WARN_LOOP_TARGET",
            "WARN_AUGMENTED",
            "WARN_WALRUS",
            # A walrus inside a comprehension binds in the ENCLOSING scope (PEP
            # 572), so at module level it leaves a module constant behind -
            # the re-adversary's second hole. A comprehension's own loop
            # variable, a lambda's walrus and a function's do not.
            "WARN_WALRUS_IN_COMPREHENSION",
            "WARN_WALRUS_NESTED",
        }
    )


#: The detector's planted source: one door per line, then controls.
_DOOR_PLANTS: Final = (
    "_ns = globals()\n"  # 1
    "exec(\"WARN_EXEC = 'x'\")\n"  # 2
    "vars()\n"  # 3
    "eval('1')\n"  # 4
    "setattr(obj, 'WARN_C', 'c')\n"  # 5
    "obj.__dict__\n"  # 6
    "import sys as s\n"  # 7 - no finding: sys alone opens nothing
    "s.modules\n"  # 8
    "locals()\n"  # 9
    "compile('', '', 'exec')\n"  # 10
    "getattr(obj, 'name')\n"  # 11
    "__import__('os')\n"  # 12
    "__builtins__\n"  # 13
    "import builtins\n"  # 14
    "from importlib import import_module\n"  # 15
    "later.__globals__\n"  # 16
    "object.__setattr__(obj, 'a', 1)\n"  # 17
    "frame.f_globals\n"  # 18
    "frame.f_locals\n"  # 19
    "from sys import modules as mods\n"  # 20
    "from builtins import print as run\n"  # 21
    "other.WARN_INJECTED = 'x'\n"  # 22
    "def later() -> None:\n"  # 23
    "    run = exec\n"  # 24 - inside a function still counts
    "table = {}\n"  # 25 - the controls: nothing from here on is a door
    "table['WARN_NOT_A_NAMESPACE'] = 'fine'\n"  # 26
    "value = other.WARN_READ\n"  # 27
    "value.attribute = 1\n"  # 28
)

#: What the detector must report for :data:`_DOOR_PLANTS`, in order.
_DOOR_FINDINGS: Final = [
    "line 1: globals",
    "line 2: exec",
    "line 3: vars",
    "line 4: eval",
    "line 5: setattr",
    "line 6: __dict__",
    "line 8: modules",
    "line 9: locals",
    "line 10: compile",
    "line 11: getattr",
    "line 12: __import__",
    "line 13: __builtins__",
    "line 14: builtins",
    "line 15: importlib",
    "line 16: __globals__",
    "line 17: __setattr__",
    "line 18: f_globals",
    "line 19: f_locals",
    "line 20: modules",
    "line 21: builtins",
    "line 22: store to attribute WARN_INJECTED",
    "line 24: exec",
]


def test_the_namespace_door_detector_names_every_reference() -> None:
    # FAIL CLOSED. A name written through a module namespace at run time
    # cannot be read statically, so the derivation cannot count it - the only
    # honest answer is a red finding naming the line. The first two lines are
    # the adjudicator's two escapes from the call-shaped detector this arm
    # replaced: an aliased namespace and an ``exec``. Every door in the set is
    # planted on at least one line whose only door it is, so dropping any one
    # from the set removes that line from the findings.
    assert namespace_doors(_DOOR_PLANTS) == _DOOR_FINDINGS


def test_the_door_set_holds_the_ruled_seven_and_no_ungraded_member() -> None:
    # Anti-shrink control. The ruling names seven doors, and every member of
    # the set must be one the detector test above plants and expects - a door
    # added without a planted line would go ungraded, and one dropped from
    # the set would leave an expected line the detector no longer reports.
    ruled = {"globals", "vars", "exec", "eval", "setattr", "__dict__", "modules"}
    planted = {
        finding.split(": ", 1)[1]
        for finding in _DOOR_FINDINGS
        if not finding.split(": ", 1)[1].startswith("store to attribute")
    }
    assert ruled <= NAMESPACE_DOORS
    assert planted == NAMESPACE_DOORS, sorted(planted ^ NAMESPACE_DOORS)


def test_the_scan_reaches_every_source_file_including_the_package_init() -> None:
    # pkgutil walks submodules only; the door arm reads the directory, so the
    # package's own ``__init__.py`` is scanned too.
    scanned = frozenset(path.stem for path in package_sources())
    walked = frozenset(
        info.name.rsplit(".", 1)[-1]
        for info in pkgutil.walk_packages(audit_package.__path__, audit_package.__name__ + ".")
    )

    assert scanned == walked | {"__init__"}
    assert "placement" in scanned


def test_no_audit_source_references_a_namespace_door() -> None:
    found: list[str] = []
    root = Path(audit_package.__file__).parents[2]
    for path in package_sources():
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        found.extend(f"{relative} {finding}" for finding in namespace_doors(source))

    assert found == []
