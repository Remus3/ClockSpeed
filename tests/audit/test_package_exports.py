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


#: Nodes that open a NEW scope. A name bound inside one is not a module
#: constant, so the walk does not descend into them.
_NESTED_SCOPES: Final = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def defined_warning_names(source: str) -> frozenset[str]:
    """Return every ``WARN_*`` name a module's source binds at module scope.

    ANY STORE AT MODULE SCOPE COUNTS, whatever statement makes it - a plain or
    annotated assignment, a tuple unpack, a binding inside an ``if`` or ``try``
    block, a loop or ``with`` target, an augmented assignment or a walrus -
    because each one leaves a module constant behind. Reading only top-level
    ``Assign`` nodes was the first draft and an adversary named two holes in
    it. An ``import`` or ``from ... import`` binding is deliberately NOT
    counted: its binding is an alias node, never a stored ``Name``, and the
    module that assigns a code owns it while a module that imports one only
    uses it.

    Args:
        source: The module's source text.

    Returns:
        The names.
    """
    names: set[str] = set()
    pending: list[ast.AST] = [ast.parse(source)]
    while pending:
        node = pending.pop()
        if isinstance(node, _NESTED_SCOPES):
            continue
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id.startswith(WARNING_PREFIX)
        ):
            names.add(node.id)
        pending.extend(ast.iter_child_nodes(node))
    return frozenset(names)


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
        }
    )
