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

#: Builtins whose return value IS a live module namespace when called at
#: module scope - and, for ``globals``, from anywhere in the module.
_NAMESPACE_CALLS: Final = frozenset({"globals", "vars"})

#: Mapping methods that write through the namespace they are called on.
_WRITING_METHODS: Final = frozenset({"update", "setdefault", "__setitem__"})


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

    FAILS CLOSED, BUT NOT HERE - a write through the module namespace at run
    time (``globals()[...] =``, ``vars()[...] =``, ``globals().update``,
    ``setattr(sys.modules[...], ...)``, ``...__dict__[...] =``) binds a name
    no static read can recover. :func:`dynamic_namespace_writes` reports each
    one by line and an arm holds the package free of them, so the derived set
    here can never be silently short by one.

    The first draft read top-level ``Assign`` nodes only; two adversary passes
    named the holes this docstring now lists.

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


def _is_namespace(node: ast.expr) -> bool:
    """Whether an expression evaluates to a live module namespace.

    Args:
        node: The expression.

    Returns:
        True for ``globals()``, ``vars()``, any ``...__dict__`` and any
        ``sys.modules[...]`` subscript.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in _NAMESPACE_CALLS and not node.args
    if isinstance(node, ast.Attribute) and node.attr == "__dict__":
        return True
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "modules"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "sys"
    )


def dynamic_namespace_writes(source: str) -> list[str]:
    """Every write through a module namespace that a static read cannot name.

    FAIL CLOSED, over the WHOLE module rather than module scope alone, because
    ``globals()`` inside a function still writes the module. Each form below is
    reported as ``line N: <form>``:

    - a subscript store into ``globals()``, ``vars()`` or any ``__dict__``;
    - ``update``, ``setdefault`` or ``__setitem__`` called on one of those;
    - ``setattr`` whose target is ``sys.modules[...]`` or ``globals()``.

    A store into an ordinary mapping and a ``setattr`` on an ordinary object
    are NOT reported: neither can reach a module namespace.

    Args:
        source: The module's source text.

    Returns:
        The findings, in line order.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
            if _is_namespace(node.value):
                found.append((node.lineno, "subscript store into a module namespace"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _WRITING_METHODS and _is_namespace(node.func.value):
                found.append((node.lineno, f"{node.func.attr} on a module namespace"))
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "setattr"
            and node.args
            and _is_namespace(node.args[0])
        ):
            found.append((node.lineno, "setattr on a module"))
    return [f"line {line}: {form}" for line, form in sorted(found)]


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


def test_the_dynamic_write_detector_names_every_form() -> None:
    # FAIL CLOSED. A name written through the module namespace at run time
    # cannot be read statically, so the derivation cannot count it - the only
    # honest answer is a red finding naming the line.
    source = (
        "import sys\n"
        "globals()['WARN_A'] = 'a'\n"
        "globals().update(WARN_B='b')\n"
        "setattr(sys.modules[__name__], 'WARN_C', 'c')\n"
        "vars()['WARN_D'] = 'd'\n"
        "sys.modules[__name__].__dict__['WARN_E'] = 'e'\n"
        "def later() -> None:\n"
        "    globals()['WARN_F'] = 'f'\n"
        "globals().setdefault('WARN_G', 'g')\n"
        "vars().update({'WARN_H': 'h'})\n"
        "table = {}\n"
        "table['WARN_NOT_A_NAMESPACE'] = 'fine'\n"
        "setattr(table, 'harmless', 1)\n"
    )

    assert [finding.split(":", 1)[0] for finding in dynamic_namespace_writes(source)] == [
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 8",
        "line 9",
        "line 10",
    ]


def test_no_audit_module_writes_its_namespace_dynamically() -> None:
    found: list[str] = []
    for info in pkgutil.walk_packages(audit_package.__path__, audit_package.__name__ + "."):
        source_path = importlib.import_module(info.name).__file__
        assert source_path is not None, info.name
        source = Path(source_path).read_text(encoding="utf-8")
        found.extend(f"{info.name} {finding}" for finding in dynamic_namespace_writes(source))

    assert found == []
