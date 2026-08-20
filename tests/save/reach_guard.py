"""The library-reach guard: who may hold a real save path, and who says so.

THE IMPLEMENTATION LIVES HERE AND THE MODULES IT GRADES LIVE BESIDE IT. Every
module under ``tests/save`` that touches a filesystem primitive declares its
reach in ``_GRADED_LIBRARY_REACH`` and ``_EXEMPT_LIBRARY_REACH``, and
:func:`_assert_library_reach_is_declared` is what reads those declarations
against the module's own AST. :func:`_reaching_modules` walks the package
directory, so a module added tomorrow is in scope the moment it exists rather
than when someone remembers to opt it in.

WHY IT IS ITS OWN MODULE, CS-495. It was owned by ``test_properties``, which
reached the 256 KiB ceiling ``tests/data/test_phase2_gate.py`` puts on any file
under ``tests/`` - a crude check whose whole job is to catch a trimmed slice of
real game data dropped in "just for tests". CLAUDE.md section 4 says relocate
rather than delete when a budget is hit, and that ceiling's stated premise is
that every hand-authored module sits far below it: raising the number would
have made that sentence false. Session 24 moved the controls out first; this is
the implementation following them.

THE MOVE PRESERVES THE SELF-GUARDING PROPERTY RATHER THAN BREAKING IT, and that
is the objection CS-495 records as no longer holding.
``test_every_library_reaching_function_here_is_declared`` used to record that a
guard whose owner sits outside its own scope is the arrangement that let a
third sweep ship ungraded one file over. CS-471's package walk covers every
module in this directory, and this file is one of them - it is not named
``test_*``, and the walk globs ``*.py`` rather than test modules, so it is
graded by the guard it defines. Its own declarations are at the foot of this
file.

NOTHING HERE IS COLLECTED BY PYTEST. The claims about this guard are tests, and
they live in ``tests/save/test_reach_guard.py``; each consuming module also
carries a splice control forcing the guard to catch a planted uncontained
helper IN THAT MODULE. A helper that landed here by mistake would stop running
silently, which is why the move was measured by diffing the collected node ids
rather than by reading the count.
"""

from __future__ import annotations

import ast
import importlib
import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import Final

#: Every attribute or bare name through which a filesystem PATH can enter a
#: module. ONE VOCABULARY, OWNED HERE and consumed by both guards that need it:
#: this module's library-reach guard, and ``test_phase4_gate``'s
#: ``no-path-reaches-it`` grade over the shipped save modules.
#:
#: IT WAS TWO HAND-MAINTAINED LISTS IN TWO FILES, and that is the defect CS-433
#: repairs rather than a tidying. One commit enumerated the path-bearing names
#: for the save-module grade while the reach guard beside it named none of them,
#: so helpers walking a save root through ``rglob``, ``iterdir``, ``os.scandir``
#: and ``os.stat`` were passed by a guard whose whole subject was reach. Two
#: lists of the same kind of thing drift apart; one list with a declared
#: partition cannot.
_FILESYSTEM_PRIMITIVES: Final = frozenset(
    (
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
        "glob",
        "rglob",
        "iterdir",
        "scandir",
        "listdir",
        "walk",
        "resolve",
        "expanduser",
        "home",
        "cwd",
        "stat",
    )
)

#: Vocabulary members that are NOT library reach, name to why they are excluded.
#:
#: THE SENTENCE THAT USED TO SIT HERE SAID adding a name to the vocabulary
#: without classifying it "turns this module red", and that "a name can be
#: excluded, but it cannot be forgotten". BOTH WERE MEASURED FALSE by a
#: refutation pass on CS-495 and reproduced by the merger. ``fchmod`` added to
#: :data:`_FILESYSTEM_PRIMITIVES` and classified nowhere leaves
#: ``test_the_reach_primitives_partition_the_filesystem_vocabulary`` GREEN,
#: because :data:`_LIBRARY_PRIMITIVES` is DERIVED as the locators unioned with
#: the vocabulary minus the exclusions - so the test's subset assertion reduces
#: to ``A <= B | A`` and holds for any vocabulary whatever. An unclassified name
#: is not caught; it is silently made a reach primitive. The exclusion half of
#: the partition IS real - an exclusion naming something outside the vocabulary
#: reddens - and the inclusion half is the tautology. Repairing it is filed
#: separately; the claim is corrected here rather than left standing.
_NOT_LIBRARY_REACH: Final = MappingProxyType(
    {
        "read_text": (
            "flags repo-source reads rather than library reads. Every AST guard "
            "in this package reads its own module text, this one included, and "
            "no discovery primitive feeds any of them"
        ),
        "write_bytes": (
            "a write cannot hand its caller a path the caller did not already "
            "hold, so it adds no reach - and the only writes here are into "
            "tmp_path"
        ),
        "write_text": "the same as write_bytes, and the splice controls use it",
        "walk": (
            "NAME COLLISION, and it is excluded on that rather than on risk. "
            "``ast.walk`` is how every AST guard in this package reads a tree, "
            "this one included, so keying on the bare attribute flags them all "
            "and says nothing about a save root. It STAYS in the vocabulary "
            "because ``test_phase4_gate`` grades the shipped save modules with "
            "the same set, no save module imports ast, and ``os.walk`` there "
            "would be a real violation. THE RESIDUAL, NAMED RATHER THAN IMPLIED "
            "AWAY: a test helper walking a real save root with ``os.walk`` is "
            "not flagged by this guard, and nothing here claims otherwise"
        ),
    }
)

#: Discovery entry points, which are not filesystem primitives but yield a real
#: save path directly. Kept separate because they are project names rather than
#: vocabulary, and only the vocabulary needs a partition.
_LIBRARY_LOCATORS: Final = frozenset(
    ("resolve_save_root", "resolve_account_dir", "latest_save", "_library_save_paths")
)

#: Names through which a function can come to hold a REAL save path or the REAL
#: account directory, DERIVED rather than written down a second time.
#:
#: KEYED ON THE RISKY PRIMITIVES, NEVER ON THE CONTAINED ROUTE. An earlier
#: version of this guard keyed on ``_library_save_paths`` alone - the SAFE
#: route - so a function using the raw locators never entered the flagged set
#: and both the subset and the equality assertion stayed true. It detected safe
#: functions and was blind to unsafe ones, which is the inversion
#: ``test_the_guard_catches_a_spliced_uncontained_helper`` in each consuming
#: module now forces.
#:
#: ``glob`` and ``read_bytes`` are included even though neither yields a real
#: path on its own. Their whole cost is the ``_EXEMPT_LIBRARY_REACH`` map in each
#: consuming module, and that map is asserted LIVE - every exemption must still
#: touch a primitive - so the price is visible in the tree rather than argued for
#: here, and it cannot rot into a silent allowance.
_LIBRARY_PRIMITIVES: Final = _LIBRARY_LOCATORS | (
    _FILESYSTEM_PRIMITIVES - frozenset(_NOT_LIBRARY_REACH)
)

#: A function definition of either colour. ``ast.AsyncFunctionDef`` is NOT a
#: subclass of ``ast.FunctionDef``, which is the single fact behind two of the
#: shapes in ``test_properties._UNCONTAINED_SPLICES``. That matrix stayed with
#: the module whose source it splices when CS-495 moved this guard out.
_ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)


def _statement_children(node: ast.AST) -> list[ast.AST]:
    """The statement-bearing children of a compound statement.

    Covers ``if``, ``try``, ``with``, ``for``, ``while`` and ``match`` without
    naming their body attributes one at a time: ``orelse``, ``finalbody``, an
    ``ExceptHandler`` and a ``match_case`` are all just statement-bearing
    children. A list of attribute names is the shape that drifts.

    Args:
        node: The statement to read.

    Returns:
        Its statement children, empty for a simple statement.
    """
    return [
        child
        for child in ast.iter_child_nodes(node)
        if isinstance(child, ast.stmt | ast.ExceptHandler | ast.match_case)
    ]


def _scanned_functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Every function a module defines outside another function's body.

    THREE NODE KINDS, because the previous filter named one. It tested
    ``isinstance(node, ast.FunctionDef)`` over ``tree.body``, and
    ``ast.AsyncFunctionDef`` is not a subclass of it, so an ``async def`` helper
    with a body identical to a flagged one was invisible. A method on a
    module-scope class was invisible for the same reason - ``ast.ClassDef`` was
    not in the filter either, so its whole body went unread.

    THE WALK NOW DESCENDS THROUGH COMPOUND STATEMENTS - CS-491, and this was the
    worst hole the item turned up. Reading ``tree.body`` alone meant a ``def``
    under a module-scope ``if`` or ``try`` was not a scanned function, while
    :func:`_module_scope_reaches` excludes every child of a ``FunctionDef`` - so
    such a def fell BETWEEN the two halves and was invisible to the guard AND to
    the classifier at once. A refutation pass took the planted control now in
    ``tests/save/test_reach_guard.py`` from red to green by indenting it one
    level under ``if sys.platform == "win32":``, which is the ordinary
    platform-fallback idiom rather than a contrived one. That sentence read
    "THIS MODULE'S OWN planted control" while the guard lived beside the
    controls; this module plants nothing. Descending repairs the partition: a def is
    scanned, or its body is module scope, and now never neither.

    IT DOES NOT DESCEND INTO A FUNCTION BODY. A nested def is not separately
    declarable and its reach is already its parent's, which is why
    :func:`_calls_any` walks the whole parent.

    Methods are keyed ``Class.method`` rather than by their bare name, and a
    class nested in a class keys ``Outer.Inner.method``, so a method cannot
    collide with a module-scope function and a declaration naming one is
    unambiguous about which it means.

    Args:
        tree: The parsed module.

    Returns:
        The functions, keyed by name.
    """
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}

    def visit(nodes: Sequence[ast.AST], prefix: str) -> None:
        for node in nodes:
            if isinstance(node, _ANY_FUNCTION):
                found[f"{prefix}{node.name}"] = node
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{prefix}{node.name}.")
            else:
                visit(_statement_children(node), prefix)

    visit(tree.body, "")
    return found


#: This test package's own directory, where a sibling module named by an import
#: is looked for. Bounding the resolution to one directory is what keeps it from
#: wandering into site-packages, and it is why the resolution below can never
#: import anything: it reads a file and parses it.
_PACKAGE_DIR: Final = Path(__file__).parent


def _resolves_by_string(call: ast.Call, names: frozenset[str]) -> bool:
    """Whether a call HANDS BACK a primitive it was given the name of.

    ``operator.methodcaller("glob", "*.sav")`` and ``getattr(account, "glob")``
    both produce the primitive without spelling it as an attribute anywhere,
    which is how two of CS-491's measured routes crossed a guard matching
    spellings.

    KEYED ON THE ARGUMENT, NEVER ON THE CALLEE. This names neither
    ``methodcaller`` nor ``attrgetter`` nor ``partial`` nor whatever the next
    one is called, because a vocabulary of wrapper names is exactly what
    CS-491's fence forbids - it would leave the next wrapper open while reading
    as though it did not.

    THE BOUND, STATED: only a DIRECT argument counts. A primitive name buried
    inside a tuple or a dict literal does not, and that is deliberate rather
    than an oversight - this module's own vocabulary constants are tuples and
    dicts of primitive names, and counting those would make every reach
    declaration in the package resolve to a primitive.

    Args:
        call: The call node.
        names: The reach vocabulary.

    Returns:
        True when a positional argument is a string equal to a primitive name,
        or is a bare name or attribute that already stands for one.
    """
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value in names:
            return True
        if isinstance(arg, ast.Name) and arg.id in names:
            return True
        if isinstance(arg, ast.Attribute) and arg.attr in names:
            return True
    return False


def _stands_for_a_primitive(value: ast.expr, names: frozenset[str]) -> bool:
    """Whether a bound expression RESOLVES a primitive rather than merely running beside one.

    THREE CHANNELS, EACH MEASURED AS A LIVE ESCAPE by CS-491's refutation passes
    and none of them naming the wrapper it travels through:

    - The primitive is MENTIONED, as a bare name or a dotted attribute, anywhere
      inside the expression. This is the old rule with every enclosing shape
      folded into it at once: ``lambda: locate.resolve_save_root()`` and
      ``functools.partial(locate.resolve_save_root)`` differ only in what
      encloses the mention, so the mention is what this reads.
    - The primitive is named as a STRING to a call that hands it back, per
      :func:`_resolves_by_string`.
    - The expression IS that string, so ``_NAME = "glob"`` binds a name that
      ``getattr(account, _NAME)`` then resolves.

    THE OVER-APPROXIMATION IS DELIBERATE AND IS STATED HERE RATHER THAN
    DISCOVERED. ``root = locate.resolve_save_root()`` binds the RESULT and not
    the primitive, and this calls that a stand-in as well. It costs a flag only
    where the bound name is itself CALLED, which no module in this package does,
    and the alternative - deciding which mentions are invocations - is the alias
    analysis this repo has declined.

    Args:
        value: The bound expression.
        names: The reach vocabulary.

    Returns:
        True when the expression resolves one of ``names``.
    """
    if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value in names:
        return True
    for node in ast.walk(value):
        if isinstance(node, ast.Name) and node.id in names:
            return True
        if isinstance(node, ast.Attribute) and node.attr in names:
            return True
        if isinstance(node, ast.Call) and _resolves_by_string(node, names):
            return True
    return False


def _nodes_inside_functions(scope: ast.AST) -> set[int]:
    """The ids of every node sitting inside a function definition in a scope.

    Args:
        scope: The subtree to read.

    Returns:
        Node ids, not including the function definitions themselves.
    """
    inside: set[int] = set()
    for node in ast.walk(scope):
        if isinstance(node, _ANY_FUNCTION):
            inside |= {id(child) for child in ast.walk(node) if child is not node}
    return inside


def _bound_names(node: ast.AST) -> list[str]:
    """Every bare name a binding target introduces, tuple targets unpacked.

    Args:
        node: The target expression.

    Returns:
        The names, empty when the target binds none.
    """
    return [inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name)]


def _bindings_of(node: ast.AST) -> list[tuple[list[str], ast.expr]]:
    """Every name-to-value binding one statement introduces.

    ``=`` IS NOT THE ONLY BINDING STATEMENT, and reading only the ones that look
    like assignment is what a refutation pass measured past the round-two guard.
    ``for finder in _FINDERS``, ``with ... as finder``, ``[one() for one in
    _FINDERS]`` and ``def _f(finder=locate.resolve_save_root)`` all bind a name
    to something that stands for a primitive and then call it - the same
    ``bind then call`` family :func:`_aliases_bound_in` exists for, reached
    through a different statement. Reading four of them and not the rest is one
    mechanism applied to part of its population, which is the pattern this item
    kept turning up.

    THE ITERATION FORMS BIND AN ELEMENT, NOT THE ITERABLE, and this pairs the
    target with the ITERABLE anyway. That over-approximates in the same
    direction everything else here does: a name drawn from a table of primitives
    is treated as standing for one, which is what makes ``for finder in
    _FINDERS: finder()`` a reach site.

    ``ast.TypeAlias`` is here because ``type _Body = bytes`` binds a name to a
    type exactly as ``_Body = bytes`` does, and reading only the second let one
    spelling of the same declaration switch the wrapper walk off.

    Args:
        node: The statement to read.

    Returns:
        One entry per binding, as the names it introduces and the value they
        stand for. Empty when the statement binds nothing - a bare ``x: int``
        declaration binds nothing and stands for nothing.
    """
    if isinstance(node, ast.Assign):
        return [(_bound_names(target), node.value) for target in node.targets]
    if isinstance(node, ast.TypeAlias):
        return [(_bound_names(node.name), node.value)]
    if isinstance(node, ast.AnnAssign | ast.NamedExpr):
        return [] if node.value is None else [(_bound_names(node.target), node.value)]
    if isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
        return [(_bound_names(node.target), node.iter)]
    if isinstance(node, ast.withitem):
        return (
            []
            if node.optional_vars is None
            else [(_bound_names(node.optional_vars), node.context_expr)]
        )
    return _default_bindings(node) if isinstance(node, ast.arguments) else []


def _default_bindings(node: ast.arguments) -> list[tuple[list[str], ast.expr]]:
    """A parameter with a DEFAULT is a name bound to that default's value.

    ``def _f(finder=locate.resolve_save_root): return finder()`` names the
    primitive once, in a signature, and calls it through a parameter.

    Args:
        node: The argument list.

    Returns:
        One entry per defaulted parameter.
    """
    positional = [*node.posonlyargs, *node.args]
    defaulted = positional[len(positional) - len(node.defaults) :]
    pairs = list(zip(defaulted, node.defaults, strict=False))
    pairs += [
        (one, default)
        for one, default in zip(node.kwonlyargs, node.kw_defaults, strict=False)
        if default is not None
    ]
    return [([one.arg], default) for one, default in pairs]


def _bindings_in(scope: ast.AST, *, inside_functions: bool) -> list[tuple[list[str], ast.expr]]:
    """Every assignment in a scope, as the names it binds and the value bound to them.

    ``inside_functions`` is what holds the two scopes apart, and they must stay
    apart. A local ``finder = locate.resolve_save_root`` in one function says
    nothing whatever about a name ``finder`` in the next, so promoting it to a
    module-wide primitive would flag every unrelated function that happens to
    call something of that name - the inversion this guard's keying note
    records, pointed a third way.

    Args:
        scope: The subtree to read.
        inside_functions: Whether to read assignments sitting inside a nested
            function. False for a module walk, True for a single function.

    Returns:
        One entry per assignment, as the bare names it binds and its value.
    """
    skipped = set() if inside_functions else _nodes_inside_functions(scope)
    found: list[tuple[list[str], ast.expr]] = []
    for node in ast.walk(scope):
        if id(node) in skipped:
            continue
        found.extend((bound, value) for bound, value in _bindings_of(node) if bound)
    return found


def _aliases_bound_in(
    scope: ast.AST, names: frozenset[str], *, inside_functions: bool
) -> frozenset[str]:
    """Expand a primitive set by every name a scope binds that stands for one.

    Resolved to a fixpoint so a chain of aliases cannot outrun it, and bounded
    by the number of bindings so a self-referential assignment cannot spin.

    Args:
        scope: The subtree to read.
        names: The primitives to start from.
        inside_functions: Passed through to :func:`_bindings_in`.

    Returns:
        ``names`` plus every alias the scope binds.
    """
    bindings = _bindings_in(scope, inside_functions=inside_functions)
    effective = set(names)
    for _round in range(len(bindings) + 1):
        grew = False
        for bound, value in bindings:
            if not _stands_for_a_primitive(value, frozenset(effective)):
                continue
            for name in bound:
                if name not in effective:
                    effective.add(name)
                    grew = True
        if not grew:
            break
    return frozenset(effective)


def _sibling_module_file(stem: str, source: Path) -> Path | None:
    """The file a dotted import name refers to, when it names a module of this package.

    Looked for beside the importing module FIRST and in this package second, so
    a planted module in ``tmp_path`` can name a planted sibling and the real
    package still resolves the real one.

    Args:
        stem: The last component of the dotted module name.
        source: The importing module's own file.

    Returns:
        The sibling's file, or None when the name is not a module of this
        package - which is the answer for every standard-library and
        ``clockspeed`` import.
    """
    for directory in (source.parent, _PACKAGE_DIR):
        candidate = directory / f"{stem}.py"
        if candidate.is_file() and candidate != source:
            return candidate
    return None


def _declared_graded_names(tree: ast.Module) -> frozenset[str]:
    """The keys of a module's graded-reach declaration, read out of its source.

    READ FROM THE TREE RATHER THAN IMPORTED. The classifier runs over every file
    in the package before anything has established that they all import, and a
    guard that imports what it is judging has a cycle waiting in it - this
    module is imported BY most of the package it scans.

    Args:
        tree: The sibling's parsed module.

    Returns:
        The string keys of its ``_GRADED_LIBRARY_REACH`` mapping, empty when it
        declares none.
    """
    found: set[str] = set()
    for bound, value in _bindings_in(tree, inside_functions=False):
        if _REACH_DECLARATIONS[0] not in bound:
            continue
        for node in ast.walk(value):
            if not isinstance(node, ast.Dict):
                continue
            found |= {
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
    return frozenset(found)


@cache
def _reaching_names_of(sibling: Path, names: frozenset[str]) -> frozenset[str]:
    """The helpers a sibling module defines that reach the SAVE LIBRARY.

    ONE HOP, STATED RATHER THAN IMPLIED. The sibling is scanned with the base
    vocabulary and its OWN aliases, and NOT with its own sibling imports, so a
    helper reaching the library only through a third module is not resolved
    here. Two hops would need the whole-package fixpoint this repo has declined;
    what CS-491 closes is the hop that was measured open.

    THE SIBLING'S OWN GRADED DECLARATION IS THE FILTER, and that is a narrowing
    with a reason rather than a convenience. Touching a primitive is not the
    same as reaching the library, which is the whole point of the exempt map:
    ``test_oracle_citations._sources_under`` globs THIS REPOSITORY, and the
    first draft of this resolution exported it, which put a library-reach
    declaration on seven functions in a sibling that reach no library at all.
    A reason that describes something the code does not do is the defect CS-471
    shipped eight of, and generating seven more automatically is worse than
    writing one by hand.

    WHAT IS EXPORTED IS THE INTERSECTION of what the sibling's functions DO with
    what the sibling SAYS: a declaration cannot invent a name that reaches
    nothing, and a function cannot reach without the sibling having declared it,
    because the suite-wide guard reds on that sibling first.

    THE RESIDUAL IS THE EXEMPT REASON ITSELF, and it is not new trust. A module
    that files a genuine library reacher under ``_EXEMPT_LIBRARY_REACH`` with a
    false reason hides it from this resolution - and it already hid it from the
    guard in its own file. Nothing here makes that better or worse.

    Args:
        sibling: The sibling module's file.
        names: The base reach vocabulary.

    Returns:
        The names of its graded helpers that reach the library directly or
        through another of its graded helpers, methods keyed ``Class.method``
        as :func:`_scanned_functions` keys them.
    """
    tree = ast.parse(sibling.read_text(encoding="utf-8"))
    primitives = _aliases_bound_in(tree, names, inside_functions=False)
    functions = _scanned_functions(tree)
    graded = _declared_graded_names(tree)
    direct = frozenset(name for name, node in functions.items() if _calls_any(node, primitives))
    # THE INDIRECT HALF, mirroring the guard rather than approximating it. A
    # graded helper that takes its body from ANOTHER graded helper calls no
    # primitive itself, so an export keyed on the direct set alone left it
    # unexported and its importer classed silent. Handed over by the privacy
    # refutation pass, which found it outside its own lens and said so.
    personal = _personal_data_names(tree)
    propagating = frozenset(
        name
        for name in graded
        if name in functions and _returns_personal_data(functions[name], personal)
    )
    indirect = frozenset(name for name, node in functions.items() if _calls_any(node, propagating))
    return graded & (direct | indirect)


def _runtime_named_siblings(
    tree: ast.Module, source: Path, names: frozenset[str]
) -> frozenset[str]:
    """Reaching names of siblings a module names as a STRING rather than by import.

    ``importlib.import_module("tests.save.test_properties")`` resolves a sibling
    with no import statement to read, and this module spells it that way itself.
    Keyed on the string RESOLVING to a sibling file, so a string that merely
    looks like a module path resolves to nothing and contributes nothing.

    Args:
        tree: The importing module's tree.
        source: The importing module's own file.
        names: The base reach vocabulary.

    Returns:
        The reaching names of every sibling named by a string argument.
    """
    reaching: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in node.args:
            if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                continue
            named = _sibling_module_file(arg.value.rsplit(".", 1)[-1], source)
            if named is not None:
                reaching |= _reaching_names_of(named, names)
    return frozenset(reaching)


def _sibling_reaching_names(
    tree: ast.Module, source: Path, names: frozenset[str]
) -> frozenset[str]:
    """Names a module imports from a package sibling that reach the library themselves.

    THIS IS CS-491's CROSS-MODULE ROUTE, AND IT NEEDED THE CLASSIFIER RATHER
    THAN THE GUARD. A module with no primitive call of its own was classed
    SILENT by :func:`_reaching_modules`, so the suite-wide guard never ran on it
    at all - and importing a sibling's sweep and calling it is the ordinary way
    this package shares one, not a contrived shape. Resolving the import turns
    the imported NAME into a primitive for the importing module, so the
    classifier picks the module up and every assertion downstream applies with
    no change of its own.

    THREE SPELLINGS, because this package writes more than one. ``from
    tests.save.test_properties import _sweep_payload_tags`` binds the helper
    itself, and ``from tests.save import test_properties`` binds the MODULE,
    after which the call is spelled as an attribute - so that shape contributes
    the sibling's reaching function names, which :func:`_calls_any` then matches
    as attributes.

    THE ATTRIBUTE MATCH IS AN OVER-APPROXIMATION and is the same one the whole
    guard is built on: it is keyed on the NAME, so an unrelated object with a
    method of that name matches too. That is the trade this guard has always
    recorded, and it errs toward declaring.

    Args:
        tree: The importing module's tree.
        source: The importing module's own file.
        names: The base reach vocabulary.

    Returns:
        The local names that stand for a sibling helper which calls a primitive.
    """
    reaching: set[str] = set()
    for node in ast.walk(tree):
        stems: list[str] = []
        aliases: list[ast.alias] = []
        if isinstance(node, ast.ImportFrom):
            if node.module is not None:
                stems.append(node.module.rsplit(".", 1)[-1])
            aliases = list(node.names)
        elif isinstance(node, ast.Import):
            aliases = list(node.names)
        else:
            continue

        for stem in stems:
            sibling = _sibling_module_file(stem, source)
            if sibling is None:
                continue
            exported = _reaching_names_of(sibling, names)
            reaching |= {alias.asname or alias.name for alias in aliases if alias.name in exported}
            # A STAR IMPORT binds the sibling's whole namespace under its own
            # names, so every exported reacher arrives spelled exactly as the
            # sibling spells it.
            if any(alias.name == "*" for alias in aliases):
                reaching |= exported

        # The module-handle shape: the imported NAME is itself a sibling module,
        # so every reaching function it defines is reachable as an attribute.
        for alias in aliases:
            sibling = _sibling_module_file(alias.name.rsplit(".", 1)[-1], source)
            if sibling is not None:
                reaching |= _reaching_names_of(sibling, names)

    return frozenset(reaching) | _runtime_named_siblings(tree, source, names)


def _effective_primitives(
    tree: ast.Module, names: frozenset[str], *, source: Path | None = None
) -> frozenset[str]:
    """Expand a primitive set by the ALIASES and the SIBLING IMPORTS that stand for one.

    ``_alias = _library_save_paths`` at module scope makes ``_alias()`` a reach
    site that spells no primitive, which is how one of CS-433's measured splices
    got past a guard matching literal names. CS-491 widened the ALIAS half from
    a bare name or attribute to :func:`_stands_for_a_primitive`, and added the
    SIBLING half, after refutation passes measured six more routes past the
    narrow rule - a module-scope ``lambda``, a ``functools.partial``, a bound
    and an inline ``operator.methodcaller``, a ``getattr`` through a module
    constant, a function-local reference alias, and a sibling's helper imported
    and called.

    ``source`` IS OPTIONAL AND ITS ABSENCE IS THE NARROWER ANSWER, never a wrong
    one: without the importing module's own path there is no directory to
    resolve a sibling against, so the sibling half is skipped rather than
    guessed at.

    Args:
        tree: The parsed module.
        names: The primitives to start from.
        source: The module's own file, when the caller has it.

    Returns:
        The primitives, plus every alias the module binds and every sibling
        helper it imports that reaches the library itself.
    """
    effective = names
    if source is not None:
        effective = effective | _sibling_reaching_names(tree, source, names)
    return _aliases_bound_in(tree, effective, inside_functions=False)


def _names_a_primitive(node: ast.expr, effective: frozenset[str]) -> bool:
    """Whether an expression NAMES a primitive, as a string constant or a bare name.

    Args:
        node: The expression, typically ``getattr``'s second argument.
        effective: The reach vocabulary, aliases included.

    Returns:
        True when it names one of them.
    """
    if isinstance(node, ast.Constant):
        return node.value in effective
    return isinstance(node, ast.Name) and node.id in effective


def _callee_resolves(func: ast.expr, effective: frozenset[str]) -> bool:
    """Whether the expression in CALLEE position IS the primitive being called.

    STRUCTURAL, AND NOT A WALK, because a walk was tried and measured. Asking
    :func:`_stands_for_a_primitive` of the whole callee reads any MENTION
    anywhere inside it - and a RECEIVER is a mention. On the shipped tree that
    flagged ``THIS_MODULE.read_text()`` and ``REPO_ROOT.relative_to(...)``,
    because those constants are themselves aliases under the deliberate
    over-approximation in :func:`_stands_for_a_primitive`, and it put a
    library-reach requirement on thirteen functions that reach nothing. A guard
    that manufactures false reasons is the failure this item has already had to
    repair once, so the walk was reverted to this.

    RECURSIVE RATHER THAN A LIST OF SHAPES. Each arm asks the same question of a
    smaller callee, so a conditional callee, a fallback callee, a dispatch table
    and a partial all resolve without any of them being enumerated as a case
    with a name.

    THE BOUND, STATED: a dispatch reached through an ATTRIBUTE of a table -
    ``_TABLE.entries["root"]()`` - is not resolved, because the step from
    ``_TABLE`` to ``entries`` is a receiver step and this refuses to follow
    those. That is the same trade the receiver measurement above forced.

    Args:
        func: The callee expression.
        effective: The reach vocabulary, aliases included.

    Returns:
        True when the callee resolves one of ``effective``.
    """
    if isinstance(func, ast.Name):
        return func.id in effective
    if isinstance(func, ast.Attribute):
        return func.attr in effective
    if isinstance(func, ast.Call):
        return _resolves_by_string(func, effective) or _callee_resolves(func.func, effective)
    if isinstance(func, ast.Subscript):
        return _callee_resolves(func.value, effective)
    if isinstance(func, ast.IfExp):
        return any(_callee_resolves(one, effective) for one in (func.body, func.orelse))
    return isinstance(func, ast.BoolOp) and any(
        _callee_resolves(one, effective) for one in func.values
    )


def _call_reaches_a_primitive(call: ast.Call, effective: frozenset[str]) -> bool:
    """Whether ONE call node reaches a primitive.

    ONE QUESTION ABOUT THE CALLEE, NOT A LIST OF CALLEE NODE TYPES. An earlier
    draft enumerated the shapes a callee could take - an ``Attribute``, a bare
    ``Name``, a ``Call``, a ``Subscript`` - and a refutation pass answered with
    the shapes it had not enumerated: ``(locate.resolve_save_root if win32 else
    dict)()`` and ``(_OVERRIDE or locate.resolve_save_root)()``, the ordinary
    override-with-fallback idiom. A guard that names a population is the defect;
    this asks :func:`_callee_resolves` whether the callee EXPRESSION resolves
    one, which is the same question asked recursively and has no list in it.

    THE INVERSION IS STILL HELD, and it is held by the same fact it always was:
    only a CALL node is examined, and only its callee.
    ``monkeypatch.setattr(locate, "resolve_save_root", raiser)`` names the
    primitive in an ARGUMENT in order to break it, and its callee is
    ``monkeypatch.setattr``, which resolves nothing.

    ``getattr`` is answered first and separately, because the name it resolves
    is a string in an ARGUMENT rather than anything in the callee, so the
    callee question cannot see it.

    Args:
        call: The call node.
        effective: The reach vocabulary, aliases included.

    Returns:
        True when this call reaches one.
    """
    func = call.func
    if isinstance(func, ast.Name) and func.id == "getattr" and len(call.args) > 1:
        return _names_a_primitive(call.args[1], effective)
    return _callee_resolves(func, effective)


def _calls_any(node: ast.FunctionDef | ast.AsyncFunctionDef, names: frozenset[str]) -> bool:
    """Whether a function calls any of the named attributes or bare names.

    THE CALL REQUIREMENT IS DELIBERATE. The sentence that stood here said that
    matching a bare REFERENCE instead - any ``Name`` or ``Attribute`` node -
    "flags every forced-failure grader in this package", and CS-491 MEASURED
    THAT FALSE: of the 31 graders in this package that name a primitive as a
    string in order to break it, a bare-reference matcher would flag ONE. The
    reason is in the spelling those graders use.
    ``monkeypatch.setattr(locate, "resolve_save_root", raiser)`` names the
    primitive as a string CONSTANT, which is neither a ``Name`` node nor an
    ``Attribute`` node, so a reference matcher never sees it. The claim is
    corrected here rather than rewritten away, and the count is not restated in
    any other file.

    WHAT IS TRUE, AND IS WHAT THE DECISION NOW RESTS ON: those graders are the
    opposite of reach sites, and flagging them is the same inversion, pointed
    the other way, that the keying note above records. The protection is the
    CALLEE POSITION rather than the call requirement alone - a primitive named
    in an ARGUMENT to break it is not in callee position, which is why
    :func:`_callee_resolves` cannot see it.
    ``tests/save/test_reach_guard.py::test_the_widening_does_not_flag_a_module_that_only_names_a_primitive``
    holds that line against the CS-491 widening, which brought new ways to
    resolve a primitive from a string and could have swallowed it.

    THE FUNCTION'S OWN LOCAL ALIASES COUNT - CS-491. ``finder =
    locate.resolve_save_root`` followed by ``finder()`` was measured past the
    module-scope-only expansion, and it is the shortest alias there is. The
    locals are expanded with the SAME :func:`_aliases_bound_in` the module scope
    uses, and are confined to this function so a local name cannot flag a
    sibling.

    ``getattr`` is read because the name it resolves is a string constant rather
    than a spelled attribute, so a call through it matches nothing
    syntactically. Its second argument is resolved through the effective names
    as well as read as a literal, so ``_NAME = "glob"`` and ``getattr(account,
    _NAME)`` no longer part company.

    A CALL WHOSE CALLEE IS ITSELF A CALL is read through, which is the inline
    form of the wrapper routes: ``operator.methodcaller("glob", "*.sav")(account)``
    and ``functools.partial(locate.resolve_save_root)()`` name no primitive in
    any callee position at all.

    A CALLEE REACHED THROUGH A SUBSCRIPT is read the same way, and it is the
    ROUTE THIS PACKAGE ALREADY WRITES. ``_ROUTES["account"](_ROUTES["root"]())``
    dispatches through a module-scope table of function objects and names no
    primitive in any callee position; binding the same lookup to a local first
    was caught, so the guard graded the LONGER spelling and passed the shorter
    one. ``tests/save/test_phase4_gate.py`` writes both spellings, 130 lines
    apart, which is how a refutation pass found it.

    Args:
        node: The function.
        names: The names to look for.

    Returns:
        True when at least one call matches.
    """
    effective = _aliases_bound_in(node, names, inside_functions=True)
    return any(
        _call_reaches_a_primitive(inner, effective)
        for inner in ast.walk(node)
        if isinstance(inner, ast.Call)
    )


#: Every type word that carries a save body or a real path when a field holds
#: one, mapped to what it actually costs. Spelled here with a reason each, the
#: way :data:`_FILESYSTEM_PRIMITIVES` is, and asserted non-vacuous by
#: ``test_the_personal_data_vocabulary_is_not_vacuous``.
#:
#: THE REASONS ARE NOT ALL THE SAME REASON, and writing them as though they were
#: would be the false-reason defect CS-471 shipped eight of. ``bytes``,
#: ``bytearray`` and ``Path`` RENDER their content through ``repr``, so a frame
#: holding one discloses under default pytest flags. ``memoryview`` and
#: ``BytesIO`` do NOT - both render as an opaque object - and what they cost is
#: the HANDOVER: the caller holds the whole decompressed world and reaches it in
#: one call. Both are propagation, and this guard is about propagation, but only
#: the first three are also a rendering.
_PERSONAL_DATA_TYPES: Final = MappingProxyType(
    {
        "bytes": "the decompressed world verbatim, and its repr renders the content",
        "bytearray": "the same bytes, mutable, and its repr renders them too",
        "memoryview": (
            "a window onto those bytes. Its own repr is opaque, so the cost is "
            "the handover rather than a rendering - one call turns it back into "
            "the body"
        ),
        "BytesIO": (
            "a file object holding the body; getvalue hands the whole of it "
            "back, and its own repr is opaque for the same reason as memoryview"
        ),
        "Path": (
            "a real save path, which carries the platform account id, the "
            "Windows account name and the world name, and whose repr renders it"
        ),
    }
)


def _carries_personal_data(rendered: str, held: frozenset[str] | None = None) -> bool:
    """Whether a rendered annotation names a type that holds a body or a path.

    Args:
        rendered: The unparsed annotation.
        held: The type words to match, defaulting to
            :data:`_PERSONAL_DATA_TYPES` alone. A caller with the module's
            tree passes that vocabulary EXPANDED by the module's own type
            aliases - see :func:`_held_type_words`.

    THE MATCH IS ON A WORD BOUNDARY, NOT A SUBSTRING, and that is a false-reason
    repair rather than a refinement. A plain ``"Path" in rendered`` is true of
    ``PurePosixPath`` and of ``os.PathLike`` - the second is written inside the
    guarded package - so a graded helper returning either tainted every caller
    as holding a real save path, and :data:`_PERSONAL_DATA_TYPES` says of
    ``Path`` that it "carries the platform account id", which is false of a
    ``PurePosixPath``. Manufacturing a reason that describes something the code
    does not do is the defect this project has had to correct eight of at once.

    Args:
        rendered: The unparsed annotation.

    Returns:
        True when the annotation names one of them as a whole word.
    """
    words = frozenset(_PERSONAL_DATA_TYPES) if held is None else held
    return any(re.search(rf"\b{re.escape(word)}\b", rendered) for word in words)


def _held_type_words(tree: ast.Module) -> frozenset[str]:
    """The body-bearing type words a module names, INCLUDING its own aliases.

    THE SAME ROUTINE THE PRIMITIVE SIDE USES, and that symmetry is the repair
    rather than a tidying. :func:`_aliases_bound_in` resolved an alias for a
    PRIMITIVE to a fixpoint while nothing resolved an alias for a TYPE, so
    ``_Body = bytes``, ``_Body: TypeAlias = bytes`` and ``type _Body = bytes``
    each switched the whole wrapper walk off - ordinary typing hygiene, not an
    attack. A mechanism applied to one of two populations is the CS-477
    pattern, and a refutation pass measured all three spellings past it.

    Args:
        tree: The parsed module.

    Returns:
        :data:`_PERSONAL_DATA_TYPES` plus every module-scope alias of one.
    """
    return _aliases_bound_in(tree, frozenset(_PERSONAL_DATA_TYPES), inside_functions=False)


def _stores_on_receiver(target: ast.expr, receiver: str) -> bool:
    """Whether an assignment target stores an attribute on a method's own receiver.

    Args:
        target: The assignment target.
        receiver: The method's first parameter name.

    Returns:
        True for ``self.anything``.
    """
    return (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == receiver
    )


def _paired_targets(node: ast.Assign) -> Iterator[tuple[ast.expr, ast.expr]]:
    """Each target of an assignment paired with the value it actually receives.

    ``self.body, self.count = body, count`` binds the body to a target that a
    walk reading ``node.targets`` against ``node.value`` cannot see, because
    the value it compares against is the whole tuple. Measured past the
    single-target read by a refutation pass.

    Args:
        node: The assignment.

    Yields:
        Target and value, unpacked one level for a tuple-to-tuple assignment.
    """
    for target in node.targets:
        if isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
            yield from zip(target.elts, node.value.elts, strict=False)
        else:
            yield target, node.value


def _bound_parameter_annotations(node: ast.ClassDef) -> list[str]:
    """The annotations of parameters a class's own methods store on ``self``.

    CS-491's UNANNOTATED-ATTRIBUTE DEFEAT, and it is the ordinary shape rather
    than a contrived one. ``self.body = body`` declares nothing at the
    attribute, so a class holding the whole world through a plain ``__init__``
    read as clean while the one-line dataclass beside it did not - the same
    object, written the other ordinary way. The annotation has not gone
    anywhere; it is on the PARAMETER, which is where this reads it.

    THREE STORE SHAPES, because reading one of them is what a refutation pass
    measured past. ``self.body = body`` with an annotated parameter;
    ``self.body: object = body``, where the STORE's annotation widens the
    parameter's away and only the parameter still tells the truth; and
    ``self.body, self.count = body, count``, whose target a single-target read
    cannot pair with its value. Both annotations are collected for the second
    shape, so a widening store cannot launder what the signature declares.

    THE SIBLING GUARD ``test_phase4_gate._retained_body_attributes`` READS THE
    SAME POPULATION over the shipped save modules and enumerates three shapes
    of its own - it does NOT cover the tuple target. Two walks over one kind
    of thing is the drift ``_FILESYSTEM_PRIMITIVES`` was unified to prevent,
    and this one is recorded rather than left to be discovered.

    THE RESIDUAL IS NAMED RATHER THAN IMPLIED AWAY: a fully unannotated
    ``def __init__(self, body): self.body = body`` states the type nowhere at
    all, and no reader of this file can recover it. That shape is still not
    flagged, and nothing here claims otherwise.

    Args:
        node: The class.

    Returns:
        The rendered annotations of every parameter assigned to an attribute of
        its method's own first argument.
    """
    found: list[str] = []
    for member in node.body:
        if not isinstance(member, _ANY_FUNCTION):
            continue
        # A PROPERTY HANDS THE HELD THING OUT, and its return annotation states
        # the type in full. A refutation pass measured `@property def body(self)
        # -> bytes` read as nothing at all - which is not the documented
        # residual, because there the type is written nowhere and here it is
        # written plainly and simply not read.
        exposes = any("property" in ast.unparse(one) for one in member.decorator_list)
        if exposes and member.returns is not None:
            found.append(ast.unparse(member.returns))
        positional = [*member.args.posonlyargs, *member.args.args]
        if not positional:
            continue
        receiver = positional[0].arg
        annotated = {
            one.arg: ast.unparse(one.annotation)
            for one in [*positional[1:], *member.args.kwonlyargs]
            if one.annotation is not None
        }
        for inner in ast.walk(member):
            if (
                isinstance(inner, ast.AnnAssign)
                and inner.annotation is not None
                and _stores_on_receiver(inner.target, receiver)
            ):
                found.append(ast.unparse(inner.annotation))
                if isinstance(inner.value, ast.Name) and inner.value.id in annotated:
                    found.append(annotated[inner.value.id])
            if not isinstance(inner, ast.Assign):
                continue
            for target, value in _paired_targets(inner):
                if (
                    _stores_on_receiver(target, receiver)
                    and isinstance(value, ast.Name)
                    and value.id in annotated
                ):
                    found.append(annotated[value.id])
    return found


def _body_wrapping_classes(
    tree: ast.Module, *, held: frozenset[str] | None = None, source: Path | None = None
) -> frozenset[str]:
    """Every class in a module that HOLDS save bytes or a real path in a field.

    THIS IS CS-471's WRAPPER EVASION, CLOSED. :func:`_returns_personal_data`
    read the rendered return annotation and nothing else, so a helper handing
    its caller a dataclass with a ``body: bytes`` field propagated the whole
    decompressed world while annotating something the guard read as a scalar.
    The evasion needed no cunning - it is the ordinary shape of a helper that
    gathers a body and its extents together, and one such helper was already
    shipped.

    THE WALK IS TRANSITIVE THROUGH FIELDS AND THROUGH BASES, because a wrapper
    inside another is the same evasion with a step in it and so is a subclass of
    one. A DRAFT READ FIELDS ALONE and a refutation pass measured what that
    missed: a subclass declaring only a label, whose base declares the body, came
    back clean.

    THREE MORE DEFEATS WERE MEASURED OPEN AFTER CS-471 CLOSED, and CS-491 shuts
    them. The held type was matched against the two words ``bytes`` and
    ``Path``, so a field typed ``bytearray``, ``memoryview`` or ``BytesIO`` held
    the same world and read as a scalar - the vocabulary is now
    :data:`_PERSONAL_DATA_TYPES`, with a reason per entry. An attribute bound
    without an annotation read as nothing at all - the parameter's annotation is
    now read, per :func:`_bound_parameter_annotations`. And a wrapper class
    IMPORTED FROM A SIBLING was outside the fixed point, which took the module's
    own classes alone - the import is now resolved, one hop, when the caller
    supplies ``source``.

    THE REMAINING LIMIT IS STATED RATHER THAN IMPLIED. The sibling resolution is
    one hop and package-local: a wrapper imported from outside this package, or
    reached through two siblings, is not resolved and this reports nothing about
    it.

    Args:
        tree: The parsed module.
        held: The body-bearing type words, defaulting to
            :data:`_PERSONAL_DATA_TYPES` alone.
        source: The module's own file, when the caller has it, so a wrapper
            imported from a package sibling resolves.

    Returns:
        The names of the classes that hold personal data, directly, through
        another class in the same module, or through a sibling's class.
    """
    annotations: dict[str, list[str]] = {}
    bases: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        rendered = [
            ast.unparse(statement.annotation)
            for statement in node.body
            if isinstance(statement, ast.AnnAssign) and statement.annotation is not None
        ]
        rendered.extend(_bound_parameter_annotations(node))
        annotations[node.name] = rendered
        bases[node.name] = [ast.unparse(base) for base in node.bases]

    wrapping = {
        name
        for name, rendered in annotations.items()
        if any(_carries_personal_data(one, held) for one in rendered)
    }
    if source is not None:
        wrapping |= set(_sibling_wrapping_classes(tree, source))
    growing = True
    while growing:
        growing = False
        for name, rendered in annotations.items():
            if name in wrapping:
                continue
            held_in_a_field = any(held in one for one in rendered for held in wrapping)
            # INHERITED COUNTS - a refutation pass measured the gap. Reading the
            # field annotations alone missed a subclass of a wrapper, which holds
            # the body its base declares and declares nothing itself.
            inherited = any(held in one for one in bases[name] for held in wrapping)
            if held_in_a_field or inherited:
                wrapping.add(name)
                growing = True
    return frozenset(wrapping)


@cache
def _wrapping_names_of(sibling: Path) -> frozenset[str]:
    """The body-wrapping classes a sibling module defines, resolved one hop only.

    Args:
        sibling: The sibling module's file.

    Returns:
        Its wrapping class names, computed WITHOUT its own sibling imports so
        the resolution cannot recurse.
    """
    tree = ast.parse(sibling.read_text(encoding="utf-8"))
    return _body_wrapping_classes(tree, held=_held_type_words(tree))


def _personal_data_names(tree: ast.Module, *, source: Path | None = None) -> frozenset[str]:
    """Every NAME in a module that stands for a save body or a real path.

    THREE POPULATIONS, ONE ROUTINE, which is the whole point of the function.
    The base vocabulary :data:`_PERSONAL_DATA_TYPES`; the module's own
    body-wrapping classes; and every ALIAS of either, resolved with the same
    :func:`_aliases_bound_in` fixpoint the primitive side uses.

    WHAT FORCED IT: a refutation pass measured that ``_Body = bytes`` switched
    the wrapper walk off, and that ``_Alias = _Wrapped`` switched off the
    CONSEQUENCE while the walk still found the class - the guard resolved an
    alias for a primitive and not an alias for a type, which is one mechanism
    applied to one of two populations. The class alias is resolved AFTER the
    walk, because a class has to be found before an alias of it means anything.

    Args:
        tree: The parsed module.
        source: The module's own file, when the caller has it, so a wrapper
            imported from a package sibling resolves.

    Returns:
        The type words and class names whose appearance in a return annotation
        makes a helper a propagating one.
    """
    held = _held_type_words(tree)
    wrapping = _body_wrapping_classes(tree, held=held, source=source)
    return _aliases_bound_in(tree, held | wrapping, inside_functions=False)


def _sibling_wrapping_classes(tree: ast.Module, source: Path) -> frozenset[str]:
    """Wrapper classes a module imports by name from a package sibling.

    Args:
        tree: The importing module's tree.
        source: The importing module's own file.

    BOTH IMPORT SHAPES, matching the reach half. ``from pkg.mod import Wrapped``
    binds the class; ``from pkg import mod`` binds the MODULE, after which the
    class is spelled as an attribute of it - and the reach half resolved that
    shape while this one did not, which is one mechanism applied to one of two
    populations for the third time in this item.

    Returns:
        The local names - the ``as`` name where there is one - that stand for a
        sibling's body-wrapping class, plus the bare class names of any sibling
        imported as a module.
    """
    held: set[str] = set()
    for node in ast.walk(tree):
        # BOTH IMPORT NODES. ``import mod`` is ``ast.Import`` and carries no
        # module attribute at all, so a filter naming only ``ast.ImportFrom``
        # read one of the two ways this package spells a sibling - the control
        # for the module-handle shape caught that on its first run.
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            sibling = _sibling_module_file(node.module.rsplit(".", 1)[-1], source)
            if sibling is not None:
                wrapping = _wrapping_names_of(sibling)
                held |= {
                    alias.asname or alias.name for alias in node.names if alias.name in wrapping
                }
        # THE MODULE-HANDLE SHAPE, which the REACH half already resolved while
        # this one did not - the same asymmetry, one layer along. An annotation
        # spelled ``test_properties._TagSweep`` renders the class name as a
        # suffix and the wrapping match is a substring test, so contributing the
        # sibling's bare class names is enough.
        for alias in node.names:
            handle = _sibling_module_file(alias.name.rsplit(".", 1)[-1], source)
            if handle is not None:
                held |= _wrapping_names_of(handle)
    return frozenset(held)


#: The declaration name a module-scope reach is filed under. A reach spelled
#: OUTSIDE any def has no function name to report, and a refutation pass
#: measured that the scan could not see it at all: hoisting the two locator
#: calls of the planted control out one indentation level left the suite-wide
#: guard green while the module held the account directory as a global. Hoisting
#: is the ordinary way to build a pytest parametrize list, so this was the
#: likeliest shape to meet, not the least.
MODULE_SCOPE_REACH: Final = "<module scope>"


def _module_scope_reaches(tree: ast.Module, primitives: frozenset[str]) -> bool:
    """Whether a primitive is called outside every function in a module.

    Args:
        tree: The parsed module.
        primitives: The reach vocabulary.

    IT ASKS :func:`_call_reaches_a_primitive`, THE SAME QUESTION THE FUNCTION
    SCAN ASKS, and that is CS-491's twelfth hole rather than a tidying. This
    re-derived the callee name itself, reading an ``Attribute`` and a bare
    ``Name`` and nothing else - the pre-CS-491 test, hand-inlined - while
    :func:`_calls_any` had grown five channels. So EVERY route CS-491 closed
    reopened by moving it one indentation level out of its ``def``: a subscript
    dispatch, a ``functools.partial``, a ``getattr`` through a module constant
    and a conditional callee were all measured escaping the guard AND the
    classifier at module scope, on a tree where the same routes inside a
    function were caught. One mechanism applied to one of two populations, for
    the fourth time in this item.

    Returns:
        True when a call reaching one of ``primitives`` sits at module scope,
        inside a module-scope ``if`` or ``try``, or in a class body - anywhere
        that runs at import and that :func:`_scanned_functions` does not report.
    """
    inside = _nodes_inside_functions(tree)
    return any(
        _call_reaches_a_primitive(node, primitives)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and id(node) not in inside
    )


def _returns_personal_data(
    node: ast.FunctionDef | ast.AsyncFunctionDef, wrapping: frozenset[str] = frozenset()
) -> bool:
    """Whether a function's RETURN ANNOTATION carries a path or save bytes.

    Derived from the annotation rather than declared in a second list, so the
    set cannot drift from the signatures it describes. A helper returning a
    ``Path`` hands its caller the account directory; one returning ``bytes``
    hands it a save body. A helper returning a counts-only sweep or a tuple of
    scalars hands over nothing personal, so its callers are not reach sites.

    A NAMED CLASS COUNTS WHEN IT HOLDS ONE - CS-471. The SECOND argument is the
    module's own body-wrapping classes, from :func:`_body_wrapping_classes`, and
    a return annotation naming one propagates exactly as ``bytes`` does. The
    default is empty so a caller that has not resolved the module's classes gets
    the old, narrower answer rather than a wrong one.

    Args:
        node: The function.
        wrapping: Class names that hold personal data in a field.

    Returns:
        True when the annotation names one of :data:`_PERSONAL_DATA_TYPES`, or
        one of ``wrapping``.
    """
    if node.returns is None:
        return False
    rendered = ast.unparse(node.returns)
    return _carries_personal_data(rendered, frozenset(_PERSONAL_DATA_TYPES) | wrapping)


def _assert_library_reach_is_declared(
    module_path: Path, *, graded: Mapping[str, str], exempt: Mapping[str, str]
) -> None:
    """Assert every function in a module that can hold a real save path is declared.

    Two ways a function comes to hold one, and both are checked, because the
    first alone missed a helper that took its path from a sibling rather than
    from a primitive:

    - AT MODULE SCOPE, by calling one of :data:`_LIBRARY_PRIMITIVES` outside
      every ``def``. There is no function name to report, so it is filed under
      :data:`MODULE_SCOPE_REACH`. This half was ADDED BY CS-471 after a
      refutation pass measured its absence.
    - DIRECTLY, by calling one of :data:`_LIBRARY_PRIMITIVES`.
    - INDIRECTLY, by calling a declared helper whose return annotation carries a
      path or save bytes, per :func:`_returns_personal_data` against
      :func:`_personal_data_names`. Test functions are included in this half: a
      test holding a real body is a reach site whatever it is called.

    Args:
        module_path: The consuming module's own file.
        graded: Helper name to the reason it reaches the library. Each has a
            containment grader in the consuming module that forces a failure
            through it.
        exempt: Function name to the reason it reaches or touches WITHOUT being
            grader-able - a test function rather than a helper, or a primitive
            applied to something that is not the real library. Asserted still
            reaching, so an exemption cannot outlive the code it describes.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    functions = _scanned_functions(tree)
    primitives = _effective_primitives(tree, _LIBRARY_PRIMITIVES, source=module_path)
    personal = _personal_data_names(tree, source=module_path)
    declared_names = frozenset(graded) | frozenset(exempt)

    direct = frozenset(name for name, node in functions.items() if _calls_any(node, primitives))
    if _module_scope_reaches(tree, primitives):
        direct |= {MODULE_SCOPE_REACH}
    propagating = frozenset(
        name
        for name in graded
        if name in functions and _returns_personal_data(functions[name], personal)
    )
    indirect = frozenset(name for name, node in functions.items() if _calls_any(node, propagating))

    assert direct, "no function here touches a library primitive, so the guard is vacuous"
    assert direct <= declared_names, (
        f"undeclared functions touch a library primitive: {sorted(direct - declared_names)}"
    )
    assert indirect <= declared_names, (
        f"undeclared functions take a save path from a graded helper: "
        f"{sorted(indirect - declared_names)}"
    )
    # THE SENTINEL IS A NAME AND NOT A FUNCTION, so it is admitted here rather
    # than faked into the function map. A placeholder node was tried and is
    # deprecated from Python 3.15, which is a poor thing to hang a privacy guard
    # on.
    nameable = frozenset(functions) | (direct & {MODULE_SCOPE_REACH})
    assert declared_names <= nameable, (
        f"a declaration names a function that no longer exists: {sorted(declared_names - nameable)}"
    )
    assert frozenset(graded) <= direct | indirect, (
        f"a graded helper no longer reaches the library: "
        f"{sorted(frozenset(graded) - (direct | indirect))}"
    )
    assert frozenset(exempt) <= direct | indirect, (
        f"an exemption outlived the code it describes: "
        f"{sorted(frozenset(exempt) - (direct | indirect))}"
    )


#: A reach reason spelled ONCE, for the modules that cannot carry a string
#: literal of their own. ``tests/save/test_decode_oracles.py`` is censused by
#: CS-420 contract 6, under which a literal no prose channel reads is a finding,
#: so its declaration takes both halves from elsewhere: the key from the
#: function's own ``__name__`` and the reason from here.
REACH_READS_THE_LIBRARY: Final = (
    "reads each save in the library and reduces it to counts before returning"
)


#: Statements that end a function's straight-line body.
_TERMINATORS: Final = (ast.Return, ast.Raise, ast.Continue, ast.Break)


def _gutted_tests(tree: ast.Module) -> list[str]:
    """Every test in a module whose body is cut short by an early terminator.

    GUTTING A TEST TO AN EARLY ``return`` IS THE CHEAPEST WAY TO MAKE A SUITE
    LIE, and it leaves the assertions in the file where a reader and a diff both
    still see them. Measured on this tree, that shape IS caught today - mypy
    runs with ``warn_unreachable`` and ``tests/test_mypy_gate.py`` puts it in the
    suite, so the gutted copy goes red where an ungutted control stays green.

    This guard exists because that protection is a SILENT DEPENDENCY on one
    setting in one file that no assertion mentions. Turning the flag off, or
    moving a module out of the gate's reach, would remove it without reddening
    anything. Here the same property is local, derived from the module's own
    AST, and named.

    THE SHAPE IT COVERS IS THE EARLY TERMINATOR AND NOTHING WIDER. A test
    emptied to ``pass``, or one whose assertions are rewritten to ``assert
    True``, leaves no unreachable statement and is not detected here. That is
    stated rather than implied, because a guard read as covering all gutting
    would be the false-guarantee class this package already paid for once.

    Args:
        tree: The parsed module.

    Returns:
        ``name at line N`` for each test with unreachable statements after a
        top-level terminator.
    """
    found: list[str] = []
    for node in _scanned_functions(tree).values():
        if not node.name.startswith("test_"):
            continue
        for index, statement in enumerate(node.body[:-1]):
            if isinstance(statement, _TERMINATORS):
                found.append(f"{node.name} at line {node.body[index + 1].lineno}")
                break
    return found


def _assert_no_test_is_gutted(module_path: Path) -> None:
    """Assert no test in a module is cut short by an early terminator.

    Args:
        module_path: The consuming module's own file.
    """
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    tests = [name for name in _scanned_functions(tree) if name.startswith("test_")]
    assert tests, f"{module_path.name} defines no test, so this guard is vacuous"

    gutted = _gutted_tests(tree)
    assert not gutted, (
        f"these tests are cut short and everything after the cut is dead: {gutted}. "
        "A test that returns before it asserts passes for the same reason an empty "
        "one does"
    )


#: The two names a module under ``tests/save`` declares its library reach with.
#: Spelled once here because the suite-wide guard below looks them up by name on
#: every module in the package, and a second spelling would be the transcription
#: this whole guard exists to avoid.
_REACH_DECLARATIONS: Final = ("_GRADED_LIBRARY_REACH", "_EXEMPT_LIBRARY_REACH")


def _module_reaches(path: Path) -> bool:
    """Whether a module touches a library primitive anywhere the guard can see.

    OWNED HERE AND CALLED BY BOTH the package split and the controls that grade
    it. A control restating this decision would grade a COPY of the classifier's
    judgement rather than the judgement, which is the ADR 0008 shape CS-474
    records inside a control built to escape circularity.

    THREE HALVES, AND TWO OF THEM WERE ADDED AFTER A REFUTATION PASS MEASURED
    THEIR ABSENCE. Splitting on the function scan alone classed a module whose
    reach sits at module scope as SILENT, so the guard was never applied to it
    at all - the reach was invisible twice over, and the proof of concept was a
    module-scope parametrize list, which is the ordinary pytest idiom rather
    than a contrived one. The third half is the sibling resolution
    :func:`_effective_primitives` performs when it is given ``source``: a module
    calling a sibling's declared sweep names no primitive of its own, and was
    classed silent for that reason.

    Args:
        path: The module's file.

    Returns:
        True when a function in it, or its module scope, reaches a primitive.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = _scanned_functions(tree)
    primitives = _effective_primitives(tree, _LIBRARY_PRIMITIVES, source=path)
    touched = any(_calls_any(node, primitives) for node in functions.values())
    return touched or _module_scope_reaches(tree, primitives)


def _reaching_modules() -> tuple[list[Path], list[Path]]:
    """Split the package's modules by whether any function touches a primitive.

    Returns:
        The modules with at least one reach site, inside a function or at module
        scope, and the rest.
    """
    package = Path(__file__).parent
    reaching: list[Path] = []
    silent: list[Path] = []
    for path in sorted(package.glob("*.py")):
        if path.name == "__init__.py":
            continue
        (reaching if _module_reaches(path) else silent).append(path)
    return reaching, silent


def _imported_sibling(path: Path) -> object:
    """Import a module of this package by its file path.

    Args:
        path: The module's file, inside this package.

    Returns:
        The imported module.
    """
    return importlib.import_module(f"tests.save.{path.stem}")


def _declaration_verdicts(
    paths: Sequence[Path], load: Callable[[Path], object]
) -> tuple[list[str], list[tuple[Path, Mapping[str, str], Mapping[str, str]]]]:
    """Judge each module's declarations, taking its module object from a caller.

    THE LOADER IS A PARAMETER SO THIS CAN BE GRADED. It is named ``load``
    rather than ``resolve`` because the reach guard is keyed on NAMES, so a
    parameter called ``resolve`` reads as ``Path.resolve`` and flags this
    function as touching a primitive - measured, not guessed. Driving the real package
    is what the suite-wide test does; handing it a path outside the package and
    a stand-in module is what
    ``tests/save/test_reach_guard.py::test_the_suite_wide_guard_catches_a_module_that_declares_nothing``
    does, and without the seam that control would have to write a file into the
    tracked test package to say anything at all. The role was an unqualified
    ``:func:`` until CS-495 moved the control one file away from this docstring.

    Args:
        paths: The modules to judge.
        load: Maps a module file to the object carrying its declarations.

    THE GUARD'S OWN FAILURE IS NOT CAUGHT AND RENDERED HERE, and that is
    non-negotiable 12 rather than a style choice. An earlier draft collected
    ``f"{path.name}: {exc}"``, which renders a caught exception OBJECT into a
    message - ``str`` on an ``OSError`` appends the path it failed on, and that
    path carries the account name. ``tests/test_exception_rendering.py`` caught
    it, in a run of the WHOLE suite rather than of ``tests/save``. What is
    collected instead is the ARGUMENTS the guard was called with, so the caller
    can re-raise through the guard and let its own message be the one rendered.

    Returns:
        The modules declaring nothing, and the guard arguments of each module
        whose declarations the guard rejects.
    """
    undeclared: list[str] = []
    rejected: list[tuple[Path, Mapping[str, str], Mapping[str, str]]] = []
    for path in paths:
        module = load(path)
        graded = getattr(module, _REACH_DECLARATIONS[0], None)
        exempt = getattr(module, _REACH_DECLARATIONS[1], None)
        if graded is None or exempt is None:
            undeclared.append(path.name)
            continue
        try:
            _assert_library_reach_is_declared(path, graded=graded, exempt=exempt)
        except AssertionError:
            rejected.append((path, graded, exempt))
    return undeclared, rejected


# ---------------------------------------------------------------------------
# THIS MODULE'S OWN LIBRARY REACH, DECLARED.
#
# The guard defined above walks this package's directory, and this file is in
# it. So the guard grades its own source, on the same terms as every module it
# lends itself to, and an undeclared reach added here reddens the same test
# that catches one added to a sibling.
# ---------------------------------------------------------------------------

#: Helpers that genuinely reach the save library, name to why each reaches.
_GRADED_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType({})

#: Functions that touch a primitive WITHOUT consuming a real path, name to why.
#: Asserted still reaching, so a stale exemption reddens the guard.
_EXEMPT_LIBRARY_REACH: Final[Mapping[str, str]] = MappingProxyType(
    {
        "_reaching_modules": (
            "globs THIS TEST PACKAGE's own directory to enumerate the modules "
            "the suite-wide guard covers - a repo path, never a save root or an "
            "account directory. It is listed here rather than special-cased in "
            "the guard, so the guard covering the package also covers itself"
        ),
    }
)
