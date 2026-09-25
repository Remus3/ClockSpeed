"""CS-1023: the warning codes the audit package re-exports, and the rule choosing them.

THE RULE. ``clockspeed/audit/__init__.py`` re-exports EVERY ``WARN_*`` constant
that a module inside the ``clockspeed.audit`` package DEFINES - a module-scope
binding of that name in that module's own source, every form of which
``defined_warning_names`` enumerates as counted or refused - and no other
``WARN_*`` name at all. The set is DERIVED here by walking the package and parsing each
module's source, never listed by hand, so a code added to any module in the
package reddens the arm until the package re-exports it.

EXPOSURE IS THE CONTRACT, not ``__all__`` alone. ``from clockspeed.audit import``
reads the package namespace, so the ``WARN_*`` names a freshly imported package
EXPOSES must equal the ``WARN_*`` members of ``__all__``, which must equal the
derived set. A save-layer code imported into ``__init__.py`` is exposed, so it
must be in ``__all__`` - and there it is not a code the package defines, so it
is red either way. ``vars`` IS exposure only because the three ways a module
can serve a name its namespace lacks - a ``__getattr__`` or ``__dir__`` hook
and a ``__class__`` swap - are refused in the source AND measured absent at run
time: every audit module, imported fresh, is exactly ``types.ModuleType``,
holds neither hook, and lists through ``dir()`` exactly its ``vars`` codes.

WHY "DEFINES" AND NOT "HAS IN ITS NAMESPACE". ``placement.py`` imports
``WARN_NODE_SEMANTICS_UNAVAILABLE`` from ``clockspeed.save.world`` and raises it,
so the name is reachable as ``placement.WARN_NODE_SEMANTICS_UNAVAILABLE``. That
code is OWNED by the save layer; re-exporting it from the audit layer would make
the audit package a second publisher of a save-layer fact. A walk over module
namespaces would sweep it in, which is why the walk reads each module's source
and counts a binding, never an import.

Before this arm the package re-exported three of the five codes ``placement.py``
defines and none of the codes the other five modules define, with nothing saying
why - the omission was the arbitrary thing, not any one missing name.
"""

from __future__ import annotations

import ast
import functools
import importlib
import json
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import Final, TypedDict

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

    COUNTED - every ``Name`` STORED at module scope: a plain or annotated
    assignment, a tuple or starred unpack, a binding inside an ``if``,
    ``else``, ``try`` or ``except`` block, a ``for`` or ``with`` target, an
    augmented assignment, a ``type`` alias, and a walrus - including a walrus
    inside a comprehension at module scope, nested or not, because PEP 572
    binds that in the enclosing scope. Also the NAME of a module-scope
    ``def``, ``async def`` or ``class``, and a walrus in any part of a def,
    class or lambda that the module scope evaluates - its decorators, its
    defaults, its bases and its class keywords; only the body opens a new scope.

    NOT COUNTED - a ``from M import WARN_X`` under the same name (the module
    that binds a code owns it, a module that imports one only uses it); a
    comprehension's own loop variable; an ``except ... as`` target, which
    Python unbinds at the end of the clause; and anything bound inside the
    BODY of a function, a class or a lambda. That last exclusion is sound only
    because :func:`refused_binding_forms` refuses the ``global`` statement, the
    one way a body binds a module name statically.

    REFUSED, not counted - every other static binding form: ``global``, a
    ``match`` capture, a star import, and any import binding a ``WARN_*`` name
    other than a same-name ``from M import WARN_X``. :func:`refused_binding_forms`
    reddens its own arm on each, anywhere in the package, so none can leave an
    uncounted constant.

    GRADED - :func:`test_the_static_count_matches_what_the_interpreter_binds`
    executes a source holding every counted form and requires this count to
    equal the ``WARN_*`` names the interpreter leaves in the namespace.

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
    namespace and the ``exec`` that a call-shaped detector let through. A
    fourth named ``global`` and a ``match`` capture, both static, and a def or
    class named ``WARN_*``; the census above is the answer.

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
            # A def or class statement binds its OWN name in the enclosing
            # scope, and the enclosing scope evaluates every part but the body
            # - decorators, defaults, bases, keywords - so a walrus there binds
            # here. Only the body opens the new scope.
            named = getattr(node, "name", "")
            if not walrus_only and named.startswith(WARNING_PREFIX):
                names.add(named)
            for field, value in ast.iter_fields(node):
                if field == "body":
                    continue
                children = value if isinstance(value, list) else [value]
                pending.extend(
                    (child, walrus_only) for child in children if isinstance(child, ast.AST)
                )
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


#: The PEP 562 module hooks. Either one lets a module expose a name that
#: neither its source nor its namespace holds.
MODULE_HOOKS: Final = frozenset({"__getattr__", "__dir__"})


def _hooks_bound(node: ast.AST) -> list[str]:
    """The members of :data:`MODULE_HOOKS` one node binds in its own scope.

    Args:
        node: Any node.

    Returns:
        The hook names it binds - by def or class name, a stored ``Name``, or
        an import alias.
    """
    bound: list[str] = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        bound.append(node.name)
    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        bound.append(node.id)
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        bound.extend(alias.asname or alias.name.split(".")[0] for alias in node.names)
    return [name for name in bound if name in MODULE_HOOKS]


def refused_binding_forms(source: str) -> list[str]:
    """Every binding form a module's source uses that the census refuses.

    FAIL CLOSED, over the WHOLE module, because each of these binds a name the
    static count in :func:`defined_warning_names` does not read. Each finding is
    ``line N: <form>``, in line order, for:

    - a ``global`` statement, anywhere - it lets a function or class body bind
      a module name, which is why that count may skip every body;
    - a ``match`` statement, anywhere - its capture patterns bind names;
    - a star import - it binds names no source line spells;
    - an import whose BOUND name is ``WARN_*``, unless it is
      ``from M import WARN_X`` (or ``as WARN_X``) under the same name - the
      one import form that serves a code owned by another module unchanged;
    - a module hook - a ``def``, ``async def``, ``class``, stored name or import
      binding a name in :data:`MODULE_HOOKS` outside every def, class and
      lambda body. PEP 562 lets a module ``__getattr__`` serve an attribute no
      namespace holds, so a code it serves is exposed yet absent from both the
      source count and ``vars`` of the module. A method of that name, or a
      function local, is not a module hook and is not refused;
    - a store to (or delete of) any ``__class__`` attribute, anywhere - a
      module whose class is swapped to a ModuleType subclass serves names
      through that class, the third mechanism beside the two hooks. A read of
      ``__class__`` is not refused.

    NOT refused: ``nonlocal``, which names an enclosing FUNCTION scope and can
    never reach the module; and ``except ... as WARN_X``, which Python unbinds
    at the end of the clause, so it leaves no module name behind.

    Args:
        source: The module's source text.

    Returns:
        The findings.
    """
    tree = ast.parse(source)
    in_a_body = {
        id(inner)
        for scope in ast.walk(tree)
        if isinstance(scope, _OWN_SCOPES)
        for statement in (scope.body if isinstance(scope.body, list) else [scope.body])
        for inner in ast.walk(statement)
    }
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.stmt, ast.expr)) and id(node) not in in_a_body:
            found.extend((node.lineno, f"module hook {name}") for name in _hooks_bound(node))
        if isinstance(node, ast.Global):
            found.append((node.lineno, "global statement"))
        elif isinstance(node, ast.Match):
            found.append((node.lineno, "match statement"))
        elif (
            isinstance(node, ast.Attribute)
            and node.attr == "__class__"
            and not isinstance(node.ctx, ast.Load)
        ):
            found.append((node.lineno, "store to attribute __class__"))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    found.append((node.lineno, "star import"))
                    continue
                bound = alias.asname or alias.name.split(".")[0]
                same_name = isinstance(node, ast.ImportFrom) and bound == alias.name
                if bound.startswith(WARNING_PREFIX) and not same_name:
                    found.append((node.lineno, f"import bound to {bound}"))
    return [f"line {line}: {form}" for line, form in sorted(found)]


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
    assert save_owned not in vars(audit_package)


#: Run in a FRESH interpreter: import the audit package and every submodule,
#: and report, per module, what it EXPOSES beside what its namespace holds.
_FRESH_PROBE: Final = """
import importlib, json, pkgutil, types
import clockspeed.audit as package
names = [package.__name__] + [
    info.name for info in pkgutil.walk_packages(package.__path__, package.__name__ + '.')
]
report = {}
for name in names:
    module = importlib.import_module(name)
    report[name] = {
        'file': module.__file__,
        'plain_module': type(module) is types.ModuleType,
        'hooks': sorted(hook for hook in ('__getattr__', '__dir__') if hook in vars(module)),
        'vars': sorted(key for key in vars(module) if key.startswith('WARN_')),
        'dir': sorted(
            key for key in dir(module) if key.startswith('WARN_') and hasattr(module, key)
        ),
    }
print(json.dumps(report))
"""


class ModuleReport(TypedDict):
    """What the fresh child reports for one module - see :func:`fresh_module_report`."""

    file: str
    plain_module: bool
    hooks: list[str]
    vars: list[str]
    dir: list[str]


@functools.cache
def fresh_module_report() -> dict[str, ModuleReport]:
    """Import ``clockspeed.audit`` and its submodules in a FRESH interpreter.

    Fresh, so no test in this process that set an attribute on a module can
    add or hide a name. The child runs from the repository root this test was
    collected from, and reports each module's file so the caller can check it
    read this tree and not an installed copy.

    Returns:
        Per dotted module name: its ``file``; ``plain_module``, whether its
        type is exactly ``types.ModuleType``; ``hooks``, the members of
        :data:`MODULE_HOOKS` in its namespace; ``vars``, the ``WARN_*`` keys of
        its namespace; and ``dir``, the ``WARN_*`` names ``dir()`` lists that
        attribute access resolves.
    """
    root = Path(audit_package.__file__).parents[2]
    result = subprocess.run(
        [sys.executable, "-B", "-c", _FRESH_PROBE],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    report: dict[str, ModuleReport] = json.loads(result.stdout.strip().splitlines()[-1])
    return report


def test_the_package_exposes_exactly_the_codes_it_re_exports() -> None:
    # EXPOSURE IS THE CONTRACT. ``from clockspeed.audit import WARN_X`` reads
    # the package namespace, never ``__all__``, so a code the package exposes
    # is published whether ``__all__`` lists it or not. Every ``WARN_*`` key of
    # a freshly imported package must therefore be in ``__all__``, and the
    # re-export arm above holds ``__all__`` to the derived set - so a
    # save-layer code imported into ``__init__.py``, or a code assigned there,
    # is red either way: unlisted it fails here, listed it fails there. A
    # module ``__getattr__`` serves names no namespace holds, which is why
    # :func:`refused_binding_forms` refuses that hook outright, and the arm
    # below proves at run time that the namespace IS what each module exposes.
    package = fresh_module_report()[audit_package.__name__]
    exposed = frozenset(package["vars"])
    declared = frozenset(name for name in audit_package.__all__ if name.startswith(WARNING_PREFIX))

    assert Path(package["file"]) == Path(audit_package.__file__)
    unlisted = sorted(exposed - declared)
    unexposed = sorted(declared - exposed)
    assert unlisted == []
    assert unexposed == []
    # Anti-vacuity: the namespace holds the whole derived set, not nothing.
    assert exposed == frozenset(defining_modules())


def test_every_audit_module_exposes_exactly_its_namespace() -> None:
    # The exposure arm above reads ``vars``; this arm makes ``vars`` equal
    # exposure. Python has three ways for a module to serve an attribute its
    # namespace does not hold - a ``__getattr__`` or ``__dir__`` in the
    # namespace (PEP 562), and a ``__class__`` swapped to a ModuleType
    # subclass. With the type exactly ``types.ModuleType`` and neither hook in
    # the namespace, attribute access on a module resolves its namespace and
    # ModuleType's own members only - so no ``WARN_*`` code can be served from
    # anywhere but ``vars``. Checked in a fresh interpreter, for the package
    # and every submodule, whatever the static refusal missed.
    report = fresh_module_report()
    walked = {
        info.name
        for info in pkgutil.walk_packages(audit_package.__path__, audit_package.__name__ + ".")
    }

    assert set(report) == walked | {audit_package.__name__}
    swapped = sorted(name for name, entry in report.items() if not entry["plain_module"])
    hooked = sorted(f"{name} {hook}" for name, entry in report.items() for hook in entry["hooks"])
    unlisted = sorted(name for name, entry in report.items() if entry["dir"] != entry["vars"])
    assert swapped == []
    assert hooked == []
    assert unlisted == []


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


#: An EXECUTABLE source binding a ``WARN_*`` name through every form the
#: static read counts, beside the look-alikes that bind no module name. It is
#: run by the interpreter as the oracle, so the static count is graded against
#: what Python actually leaves in the module namespace, not against a list.
_ORACLE_SOURCE: Final = (
    "import contextlib\n"
    "WARN_O_PLAIN = 'plain'\n"
    "WARN_O_A, *WARN_O_REST = 'a', 'b'\n"
    "for WARN_O_FOR in ('f',):\n"
    "    pass\n"
    "with contextlib.nullcontext('w') as WARN_O_WITH:\n"
    "    pass\n"
    "(WARN_O_WALRUS := 'w')\n"
    "_ = [WARN_O_IN_COMP := v for v in ('c',)]\n"
    "type WARN_O_ALIAS = int\n"
    "class WARN_O_CLASS:\n"
    "    WARN_O_CLASS_ATTRIBUTE = 'attribute, not module'\n"
    "def WARN_O_FUNCTION() -> None:\n"
    "    WARN_O_FUNCTION_LOCAL = 'local, not module'\n"
    "async def WARN_O_ASYNC() -> None:\n"
    "    pass\n"
    "@(WARN_O_DECORATOR := (lambda f: f))\n"
    "def _decorated(a=(WARN_O_DEFAULT := 1), *, b=(WARN_O_KW_DEFAULT := 2)) -> None:\n"
    "    (WARN_O_BODY_WALRUS := 'local, not module')\n"
    "class _Based((WARN_O_BASE := object), metaclass=(WARN_O_KEYWORD := type)):\n"
    "    pass\n"
    "_lam = lambda a=(WARN_O_LAMBDA_DEFAULT := 3): (WARN_O_LAMBDA_BODY := a)\n"
    "_lam()\n"
    "_decorated()\n"
    "try:\n"
    "    raise ValueError\n"
    "except ValueError as WARN_O_EXCEPT_TARGET:\n"
    "    pass\n"
)


#: How many ``WARN_*`` names :data:`_ORACLE_SOURCE` leaves bound when run.
_ORACLE_BINDS: Final = 17


def test_the_static_count_matches_what_the_interpreter_binds() -> None:
    # The re-adjudication's holes were forms the walk skipped: a def or class
    # NAMED ``WARN_*``, and a walrus in the parts of a def, class or lambda
    # that the ENCLOSING scope evaluates - decorators, defaults, bases and
    # class keywords. The interpreter is the oracle: every ``WARN_*`` key it
    # leaves in a fresh module namespace must be counted, and nothing else.
    # The except target is the control that Python binds and then UNBINDS at
    # the end of the clause, so it leaves no module name and is not counted.
    namespace: dict[str, object] = {}
    exec(compile(_ORACLE_SOURCE, "<oracle>", "exec"), namespace)  # noqa: S102 - a literal oracle
    bound = frozenset(name for name in namespace if name.startswith(WARNING_PREFIX))
    counted = defined_warning_names(_ORACLE_SOURCE)

    uncounted = sorted(bound - counted)
    overcounted = sorted(counted - bound)
    assert uncounted == []
    assert overcounted == []
    # Anti-vacuity: the oracle binds every counted form, so neither side is empty.
    assert len(bound) == _ORACLE_BINDS


#: The refusal detector's planted source: one refused form per finding line,
#: then controls that bind a ``WARN_*`` name no other way than is counted or
#: owned elsewhere.
_REFUSED_PLANTS: Final = (
    "def bind() -> None:\n"  # 1
    "    global WARN_G\n"  # 2
    "match subject:\n"  # 3
    "    case WARN_M:\n"  # 4
    "        pass\n"  # 5
    "from os.path import *\n"  # 6
    "import os as WARN_IMPORT_AS\n"  # 7
    "import WARN_BARE_MODULE\n"  # 8
    "from os import sep as WARN_RENAMED\n"  # 9
    "from elsewhere import WARN_OTHER as WARN_RENAMED_CODE\n"  # 10
    "from elsewhere import WARN_OWNED_ELSEWHERE\n"  # 11 - controls from here on
    "from elsewhere import WARN_SAME as WARN_SAME\n"  # 12
    "import package.WARN_SUBMODULE\n"  # 13 - binds ``package``, not the code
    "def outer() -> None:\n"  # 14
    "    value = 1\n"  # 15
    "    def inner() -> None:\n"  # 16
    "        nonlocal value\n"  # 17 - names a function scope, never the module
    "def __getattr__(name: str) -> str:\n"  # 18 - a module hook serves names lazily
    "    return name\n"  # 19
    "async def __dir__() -> list[str]:\n"  # 20
    "    return []\n"  # 21
    "if True:\n"  # 22
    "    __getattr__ = print\n"  # 23 - a hook bound by assignment, in a block
    "from os import getcwd as __dir__\n"  # 24 - a hook bound by import
    "class Proxy:\n"  # 25 - controls: a method hook serves an INSTANCE only
    "    def __getattr__(self, name: str) -> str:\n"  # 26
    "        return name\n"  # 27
    "    __dir__ = object.__dir__\n"  # 28
    "def local() -> None:\n"  # 29
    "    __getattr__ = print\n"  # 30 - a function local, never the module
    "module.__class__ = Lazy\n"  # 31 - a module class swap serves any name
    "kind = value.__class__\n"  # 32 - control: a read swaps nothing
)

#: What the refusal detector must report for :data:`_REFUSED_PLANTS`, in order.
_REFUSED_FINDINGS: Final = [
    "line 2: global statement",
    "line 3: match statement",
    "line 6: star import",
    "line 7: import bound to WARN_IMPORT_AS",
    "line 8: import bound to WARN_BARE_MODULE",
    "line 9: import bound to WARN_RENAMED",
    "line 10: import bound to WARN_RENAMED_CODE",
    "line 18: module hook __getattr__",
    "line 20: module hook __dir__",
    "line 23: module hook __getattr__",
    "line 24: module hook __dir__",
    "line 31: store to attribute __class__",
]


def test_the_refusal_detector_names_every_refused_binding_form() -> None:
    # Each refused form is planted on a line whose only finding it is, so
    # dropping any one refusal from the detector removes that line.
    assert refused_binding_forms(_REFUSED_PLANTS) == _REFUSED_FINDINGS


def test_no_audit_source_uses_a_refused_binding_form() -> None:
    found: list[str] = []
    root = Path(audit_package.__file__).parents[2]
    for path in package_sources():
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        found.extend(f"{relative} {finding}" for finding in refused_binding_forms(source))

    assert found == []


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
