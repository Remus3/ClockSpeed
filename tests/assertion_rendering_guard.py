"""CS-850 - the pytest assertion channel, and who declared what unsafe to render.

THE CHANNEL, NAMED PRECISELY, because the remedy depends on which one it is.
pytest rewrites ``assert TEST, MESSAGE`` so the failure report renders the
sub-expressions of TEST with THEIR OWN reprs, independently of MESSAGE. A
carefully counts-only MESSAGE does not control that channel and never did. The
shape measured on this tree three times, by three agents who did not know of
each other, is::

    assert len(sweep.miss_words) <= CEILING, f"{len(sweep.miss_words)} words"

which renders, past a message that says only a number::

    E   assert 3 <= 0
    E    +  where 3 = len(frozenset({'<a save word>', '<a home path>', ...}))
    E    +    where frozenset({...}) = Sweep(saves=1, miss_words=3).miss_words

The object's own ``__repr__`` FIRED - ``Sweep(saves=1, miss_words=3)`` - and was
bypassed one step later, because ``visit_Attribute`` reprs the ATTRIBUTE it
read, not the object it read it from. That is the whole mechanism.

WHAT DECLARES A VALUE UNSAFE, and why this needs no list. A class that ships a
hand-written ``__repr__`` in order to WITHHOLD its contents has already declared
that its own fields must not be rendered. Every one of them says so in its
docstring - "withhold every struct word", "render counts only", "render without
any path", "never the captured text". That declaration is the population, and it
is shipped, maintained and already guarded by other tests. So this module
DERIVES:

  1. every class in the tree that ships a ``__repr__``;
  2. from each, the fields that ``__repr__`` renders WHOLE (disclosed) and the
     fields it does not (withheld) - read out of the ``__repr__`` body itself,
     never written down;
  3. of the withheld ones, those whose own annotation is repr-TRANSPARENT, that
     is, not composed entirely of other redacting classes;
  4. every assertion in the tree whose rewritten explanation reaches one.

There is no module list, no field list and no class list anywhere below. A
redacting class added tomorrow is in scope the moment it exists, and a new
assertion over one of its withheld fields is red without anyone opting it in.
CS-205 records why: a hand-listed acceptance in this project went stale between
being written and being worked, every time.

WHY THE EXPLAINED SET IS COMPUTED RATHER THAN GUESSED. Which sub-expressions
pytest reprs is a property of ``_pytest.assertion.rewrite.AssertionRewriter``,
not of intuition. :func:`explained` mirrors its dispatch exactly -
``visit_Name``, ``visit_BoolOp``, ``visit_UnaryOp``, ``visit_BinOp``,
``visit_Call``, ``visit_Starred``, ``visit_Attribute``, ``visit_Compare`` - and
falls back to ``generic_visit``, which reprs a node WHOLE, for everything else.
That fallback is the half a guess gets wrong: a subscript, a comprehension and a
container display are each rendered entire.

THE THREE CASES THAT MUST NOT BE FLAGGED, and this half is load-bearing.

  ``assert sweep.saves <= 0``       a DISCLOSED field. The class chose to
                                    render it, so rendering it again discloses
                                    nothing the repr did not.
  ``assert sweep == other``         the WHOLE OBJECT. The redacting ``__repr__``
                                    is exactly what runs here, which is what it
                                    was written for. Measured, not assumed - see
                                    the third arm of the sandbox proof in
                                    ``tests/test_assertion_rendering.py``.
  ``assert count <= CEILING``       the REMEDY: the aggregate reduced to a plain
                                    scalar BEFORE the assert, so the rendered
                                    expression holds a number and nothing else.

A detector that flags any of them makes whoever sees the red either "fix"
correct code or loosen the guard until it is vacuous.

THE ONE-HOP ALIAS, and why it is here rather than a general taint walk. Binding
the field to a local first::

    words = sweep.miss_words
    assert len(words) <= CEILING, "counts only"

renders exactly the same frozenset, and it is the first thing anyone reaches for
when the direct form goes red. So a local bound DIRECTLY to a withheld field
carries the finding with it. It is deliberately ONE HOP and no further: a field
routed through a helper and rendered from that helper's RETURN is NOT flagged,
because the class made no declaration about the helper's return and this guard
grades declarations. That limit is stated rather than implied away, and it is
the honest boundary of what a green run here means.

LIVE AND LATENT, a partition and not a severity opinion. The same construct is a
DISCLOSURE when the holder was built from the real save library or from this
machine, and a LATENT defect when it was built from a synthetic fixture in the
process - the fixture holds nothing personal, and one fixture change turns it
into the first kind. Both are reported. The partition is DERIVED from two
declarations the tree already ships and other guards already keep live: each
module's own ``_GRADED_LIBRARY_REACH`` (``tests/save/reach_guard.py``), closed
under "a function that returns what a reaching function returned", and the
pytest fixtures through which this MACHINE enters a test. Nothing here decides
which fields are "really" personal; the class that withheld them decided that.

WHAT THIS DOES NOT COVER, so a green run is not read as more than it is. Frame
arguments and locals are a different channel with a different remedy and belong
to ``tests/test_tmp_path_privacy.py``; a rendered exception OBJECT belongs to
``tests/test_exception_rendering.py``, which keys on an AST shape inside a
handler and is structurally blind to this one. A value that is personal but
whose holder never declared a redacting ``__repr__`` is invisible here, because
there is no declaration to bypass.
"""

from __future__ import annotations

import ast
import subprocess
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: A function definition of either colour. ``ast.AsyncFunctionDef`` is NOT a
#: subclass of ``ast.FunctionDef``, and a guard that forgets it covers half its
#: population while reporting a count for all of it.
ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)

#: Builtins that render their whole argument as text. A field handed to one of
#: these inside ``__repr__`` is DISCLOSED as surely as one interpolated bare.
TEXT_BUILTINS: Final = frozenset({"str", "repr", "ascii", "format"})

#: Type words that only WRAP. The repr of one of these calls the repr of what it
#: holds, so a container of redacting classes renders redacted reprs and
#: discloses nothing. ``Final`` and ``ClassVar`` are here for the same reason:
#: they annotate without adding a rendering of their own.
PASS_THROUGH_TYPES: Final = frozenset(
    {
        "AbstractSet",
        "Annotated",
        "ClassVar",
        "Collection",
        "Final",
        "Iterable",
        "Iterator",
        "list",
        "Mapping",
        "MappingProxyType",
        "MutableMapping",
        "MutableSequence",
        "None",
        "Optional",
        "Sequence",
        "Union",
        "dict",
        "frozenset",
        "set",
        "tuple",
    }
)

#: pytest fixtures through which THIS MACHINE enters a test. Both DELIVER a real
#: directory, and on Windows the pytest base temporary directory sits under the
#: user profile AND embeds ``getpass.getuser()`` in its own name - so a value
#: built from one carries a home path and the account name.
#:
#: ``monkeypatch`` IS DELIBERATELY NOT HERE, and leaving it out is the
#: difference between a guard and a nuisance. It delivers no machine state; it
#: is how a test DETACHES from this machine, and in this tree that is exactly
#: what it is used for - pointing the install locator, the save root and the
#: environment at somewhere synthetic. Counting it as machine reach inverted the
#: partition on ten arms whose every rendered value is a constant hand-authored
#: in the module beside them.
MACHINE_FIXTURES: Final = frozenset({"tmp_path", "tmp_path_factory"})

#: The declaration each module under ``tests/save`` uses to name the helpers that
#: genuinely read the real save library. Owned by ``tests/save/reach_guard.py``
#: and asserted live there; read here rather than restated, so the two cannot
#: drift (CLAUDE.md section 4).
REACH_DECLARATION: Final = "_GRADED_LIBRARY_REACH"

#: Discovery entry points that yield a real save path directly, mirroring
#: ``reach_guard._LIBRARY_LOCATORS``. It is spelled again rather than imported
#: because this module is imported by a test at the repo ROOT and must not make
#: the whole tree's guard depend on the save package importing cleanly.
#: ``test_the_locator_seeds_match_the_reach_guard`` asserts the two agree, so a
#: name added there and forgotten here turns that test red rather than silently
#: shrinking this population.
LIBRARY_LOCATORS: Final = frozenset(
    {"resolve_save_root", "resolve_account_dir", "latest_save", "_library_save_paths"}
)


@dataclass(frozen=True)
class Redacting:
    """A class that ships a ``__repr__`` in order to withhold its own fields.

    Attributes:
        module: Repo-relative path of the file defining it.
        name: The class name.
        lineno: Where the class starts.
        disclosed: Fields the ``__repr__`` renders whole.
        withheld: Fields it does not render whole AND whose own annotation is
            repr-transparent, so rendering one renders its contents rather than
            another redacting repr.
    """

    module: str
    name: str
    lineno: int
    disclosed: frozenset[str]
    withheld: frozenset[str]


@dataclass(frozen=True)
class Finding:
    """One assertion whose rewritten explanation reaches a withheld field.

    Attributes:
        module: Repo-relative path of the asserting file.
        lineno: The line the rendered sub-expression sits on.
        holder: The redacting class that withheld the field.
        field: The withheld field name.
        source: The offending sub-expression, unparsed. Repo SOURCE TEXT, never
            a runtime value - nothing in this module reads a value.
        live: True when the holder was built from the real save library or from
            this machine; False when it was built from a synthetic fixture.
    """

    module: str
    lineno: int
    holder: str
    field: str
    source: str
    live: bool


def describe(findings: list[Finding]) -> str:
    """Render findings as file, line and shape.

    Args:
        findings: What to render.

    Returns:
        One indented line each, sorted, carrying source text only.
    """
    lines = sorted(
        f"  {f.module}:{f.lineno}  {f.holder}.{f.field}  renders `{f.source}`" for f in findings
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Deriving the declarations: which classes withhold which fields
# ---------------------------------------------------------------------------


def repr_method(node: ast.ClassDef) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """The hand-written ``__repr__`` a class ships, if it ships one.

    Args:
        node: The class.

    Returns:
        The method, or None for a class that inherits or generates its repr.
    """
    for item in node.body:
        if isinstance(item, ANY_FUNCTION) and item.name == "__repr__":
            return item
    return None


def annotation_names(node: ast.expr | None) -> frozenset[str]:
    """Every bare type word an annotation mentions.

    A STRING annotation is parsed rather than skipped: ``x: "Schema"`` under
    ``from __future__ import annotations`` is the same declaration as ``x:
    Schema``, and a walk that reads one and not the other grades half a
    population. An annotation this cannot read yields ``?``, which belongs to no
    known class and therefore counts as transparent - the conservative
    direction.

    Args:
        node: The annotation, or None.

    Returns:
        The type words.
    """
    found: frozenset[str]
    match node:
        case None:
            found = frozenset()
        case ast.Name(id=name):
            found = frozenset({name})
        case ast.Attribute(attr=attr):
            found = frozenset({attr})
        case ast.Subscript(value=value, slice=inner):
            found = annotation_names(value) | annotation_names(inner)
        case ast.Tuple(elts=elts):
            found = frozenset().union(*(annotation_names(elt) for elt in elts), frozenset())
        case ast.BinOp(left=left, right=right):
            found = annotation_names(left) | annotation_names(right)
        case ast.Constant(value=value):
            found = _constant_annotation_names(value)
        case _:
            found = frozenset({"?"})
    return found


def _constant_annotation_names(value: object) -> frozenset[str]:
    """The type words a constant annotation node stands for.

    Args:
        value: The constant's value.

    Returns:
        The parsed words for a string forward reference, ``None`` for the null
        type, nothing for the ``...`` of ``tuple[T, ...]``, and ``?`` otherwise.
    """
    if isinstance(value, str):
        try:
            return annotation_names(ast.parse(value, mode="eval").body)
        except SyntaxError:
            return frozenset({"?"})
    if value is None:
        return frozenset({"None"})
    if value is Ellipsis:
        return frozenset()
    return frozenset({"?"})


def declared_fields(node: ast.ClassDef) -> dict[str, frozenset[str]]:
    """The annotated fields of a class, field name to its type words.

    Args:
        node: The class.

    Returns:
        One entry per ``name: T`` in the class body.
    """
    return {
        item.target.id: annotation_names(item.annotation)
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    }


def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    """Child-node identity to its parent, for one tree.

    Args:
        tree: The root.

    Returns:
        The mapping.
    """
    return {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def disclosed_fields(method: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[str]:
    """The fields a ``__repr__`` renders WHOLE.

    A field is disclosed when it is interpolated bare - ``f"{self.x}"``, any
    conversion - or handed to a text builtin. It is NOT disclosed when it
    appears only under a reduction: ``f"{len(self.x)}"`` and
    ``f"{sum(self.x.values())}"`` are the two spellings this tree actually uses
    to render a count while withholding the contents, and reading either as
    disclosure would wave through the exact site CS-850 was opened on.

    Args:
        method: The class's ``__repr__``.

    Returns:
        The disclosed field names.
    """
    if not method.args.args:
        return frozenset()
    receiver = method.args.args[0].arg
    kin = _parent_map(method)
    out: set[str] = set()
    for node in ast.walk(method):
        if not isinstance(node, ast.Attribute):
            continue
        if not (isinstance(node.value, ast.Name) and node.value.id == receiver):
            continue
        if _renders_whole(node, kin.get(id(node))):
            out.add(node.attr)
    return frozenset(out)


def _renders_whole(node: ast.Attribute, parent: ast.AST | None) -> bool:
    """Whether this occurrence of ``self.field`` renders the field entire.

    Args:
        node: The attribute read.
        parent: Its immediate parent node.

    Returns:
        True for a bare interpolation or a text-builtin argument.
    """
    if isinstance(parent, ast.FormattedValue):
        return parent.value is node
    if isinstance(parent, ast.Call) and node in parent.args:
        return isinstance(parent.func, ast.Name) and parent.func.id in TEXT_BUILTINS
    return False


def redacting_classes(module: str, tree: ast.Module, opaque: frozenset[str]) -> list[Redacting]:
    """Every class in one module that ships a redacting ``__repr__``.

    Args:
        module: Repo-relative path, carried onto each record.
        tree: The parsed module.
        opaque: Names of classes that ship a ``__repr__`` anywhere in the tree,
            used to decide whether a withheld field's own type redacts itself.

    Returns:
        One record per such class.
    """
    out: list[Redacting] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        method = repr_method(node)
        if method is None:
            continue
        shown = disclosed_fields(method)
        fields = declared_fields(node)
        withheld = frozenset(
            name
            for name, types in fields.items()
            if name not in shown and not _renders_only_redacted(types, opaque)
        )
        out.append(Redacting(module, node.name, node.lineno, shown, withheld))
    return out


def _renders_only_redacted(types: frozenset[str], opaque: frozenset[str]) -> bool:
    """Whether rendering a value of this annotation renders only redacting reprs.

    ``tuple[ResourceNode, ...]`` is safe to render because a tuple's repr calls
    each element's, and ``ResourceNode`` withholds its own instance name.
    ``Mapping[str, Schema]`` is NOT, because the KEYS are bare strings and a
    mapping renders those directly.

    Args:
        types: The annotation's type words.
        opaque: Class names that ship a ``__repr__``.

    Returns:
        True only when at least one real type is named and every one redacts.
    """
    meaningful = types - PASS_THROUGH_TYPES
    return bool(meaningful) and meaningful <= opaque


# ---------------------------------------------------------------------------
# Deriving the channel: which sub-expressions pytest reprs
# ---------------------------------------------------------------------------


def explained(node: ast.expr) -> Iterator[ast.expr]:
    """Every sub-expression pytest's rewriter reprs for an asserted expression.

    Mirrors ``_pytest.assertion.rewrite.AssertionRewriter``: each ``visit_X``
    that recurses is recursed here, and the ``generic_visit`` fallback - which
    assigns the node and reprs it entire - is the final case. A ``Call`` yields
    itself AND recurses, because the rewriter reprs the result and every
    argument.

    Args:
        node: The asserted expression, or a sub-expression of one.

    Yields:
        Each node whose repr reaches the failure report.
    """
    if _reprs_its_own_value(node):
        yield node
    for operand in _recursed_operands(node):
        yield from explained(operand)


def _reprs_its_own_value(node: ast.expr) -> bool:
    """Whether the rewriter reprs this node's own value, not only its parts.

    ``visit_BoolOp``, ``visit_UnaryOp``, ``visit_BinOp``, ``visit_Starred`` and
    ``visit_Compare`` build an explanation out of their OPERANDS and never repr
    the node itself. Everything else either has a ``visit_`` that assigns and
    displays the result - ``Name``, ``NamedExpr``, ``Call``, ``Attribute`` - or
    falls to ``generic_visit``, which does exactly that.

    Args:
        node: The sub-expression.

    Returns:
        True when the node's own repr reaches the report.
    """
    return not isinstance(node, (ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Starred, ast.Compare))


def _recursed_operands(node: ast.expr) -> list[ast.expr]:
    """The sub-expressions the rewriter descends into.

    Args:
        node: The sub-expression.

    Returns:
        Its operands in the order the rewriter visits them, empty for a node it
        renders whole without descending.
    """
    match node:
        case ast.BoolOp(values=values):
            operands: list[ast.expr] = list(values)
        case ast.UnaryOp(operand=operand) | ast.Starred(value=operand):
            operands = [operand]
        case ast.BinOp(left=left, right=right):
            operands = [left, right]
        case ast.Call(func=func, args=args, keywords=keywords):
            operands = [func, *args, *(keyword.value for keyword in keywords)]
        case ast.Attribute(ctx=ast.Load(), value=value):
            operands = [value]
        case ast.Compare(left=left, comparators=comparators):
            operands = [left, *comparators]
        case _:
            operands = []
    return operands


def scope_statements(scope: ast.AST) -> Iterator[ast.stmt]:
    """Every statement lexically inside one scope, in source order.

    Descends through ``if``, ``for``, ``with`` and ``try`` bodies - a binding
    made in one of those is visible to an assert after it - and STOPS at a
    nested function or class, whose statements belong to their own scope.

    Args:
        scope: A module or a function definition.

    Yields:
        The statements.
    """
    for stmt in getattr(scope, "body", []):
        yield from _statements_under(stmt)


def _statements_under(stmt: ast.stmt) -> Iterator[ast.stmt]:
    """The statement itself, then any it nests that share its scope.

    Args:
        stmt: The statement.

    Yields:
        It, then its scope-sharing descendants in source order.
    """
    yield stmt
    if isinstance(stmt, (*ANY_FUNCTION, ast.ClassDef)):
        return
    for field in ("body", "orelse", "finalbody"):
        for inner in getattr(stmt, field, []):
            if isinstance(inner, ast.stmt):
                yield from _statements_under(inner)
    for handler in getattr(stmt, "handlers", []):
        for inner in handler.body:
            yield from _statements_under(inner)


def annotation_tail(node: ast.expr | None) -> str | None:
    """The single class word an annotation resolves to, if it resolves to one.

    Args:
        node: The annotation.

    Returns:
        The rightmost name, unwrapping subscripts, unions and forward
        references; None when there is nothing to read.
    """
    tail: str | None
    match node:
        case ast.Name(id=name):
            tail = name
        case ast.Attribute(attr=attr):
            tail = attr
        case ast.Subscript(value=value) | ast.BinOp(left=value):
            tail = annotation_tail(value)
        case ast.Constant(value=str() as text):
            tail = _forward_reference_tail(text)
        case _:
            tail = None
    return tail


def _forward_reference_tail(text: str) -> str | None:
    """The class word a STRING annotation stands for.

    Args:
        text: The forward reference.

    Returns:
        The rightmost name, or None when it does not parse as an expression.
    """
    try:
        parsed = ast.parse(text, mode="eval").body
    except SyntaxError:
        return None
    return annotation_tail(parsed)


# ---------------------------------------------------------------------------
# Deriving the partition: which holders carry real data
# ---------------------------------------------------------------------------


def reach_seeds(tree: ast.Module) -> frozenset[str]:
    """The helpers a module DECLARES as reaching the real save library.

    Read out of the module's own ``_GRADED_LIBRARY_REACH``, which
    ``tests/save/reach_guard.py`` already asserts is complete and still live.
    Both key spellings this tree uses are read - a string literal, and the
    ``_helper.__name__`` form that makes a rename move the key with it.

    Args:
        tree: The parsed module.

    Returns:
        The declared helper names, plus the locators every module may call.
    """
    out: set[str] = set(LIBRARY_LOCATORS)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if _assigned_name(node) != REACH_DECLARATION or node.value is None:
            continue
        out |= _mapping_key_names(node.value)
    return frozenset(out)


def _assigned_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    """The single bare name a statement assigns to, if it assigns to one.

    Args:
        node: The assignment.

    Returns:
        The name, or None for a tuple, attribute or subscript target.
    """
    targets = [node.target] if isinstance(node, ast.AnnAssign) else node.targets
    if len(targets) != 1 or not isinstance(targets[0], ast.Name):
        return None
    return targets[0].id


def _mapping_key_names(value: ast.expr) -> set[str]:
    """The key names of a dict literal, through a one-call wrapper.

    Args:
        value: The assigned expression, possibly ``MappingProxyType({...})``.

    Returns:
        Every key spelled as a string literal or as ``something.__name__``.
    """
    if isinstance(value, ast.Call) and value.args:
        value = value.args[0]
    if not isinstance(value, ast.Dict):
        return set()
    out: set[str] = set()
    for key in value.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            out.add(key.value)
        elif (
            isinstance(key, ast.Attribute)
            and key.attr == "__name__"
            and isinstance(key.value, ast.Name)
        ):
            out.add(key.value.id)
    return out


def live_functions(tree: ast.Module, seeds: frozenset[str]) -> frozenset[str]:
    """Every function in a module whose return value carries real data.

    A FIXPOINT rather than a single pass, because the shape this tree ships puts
    the declared reader one call behind the caller: ``_sweep_or_skip`` returns
    what ``_sweep_the_library`` returned, and only the second is declared. A
    one-pass reading of the declaration finds the caller safe and grades the
    live site as latent.

    THE FIXTURE HOP IS PART OF THE SAME FIXPOINT, and leaving it out was
    measured rather than reasoned about. A ``@pytest.fixture`` taking
    ``tmp_path`` and returning a holder makes every test that names it live,
    and without this hop two modules whose whole subject is a real temporary
    directory under the user profile were graded LATENT - the wrong answer, in
    the wrong direction, on the two files most exposed to it.

    Args:
        tree: The parsed module.
        seeds: The declared readers, from :func:`reach_seeds`.

    Returns:
        The seeds, every function taking a machine fixture, and everything that
        transitively returns or receives one of them.
    """
    functions = [node for node in ast.walk(tree) if isinstance(node, ANY_FUNCTION)]
    fixtures = {node.name for node in functions if _is_a_fixture(node)}
    live = {node.name for node in functions if _takes_a_machine_fixture(node)} | set(seeds)
    changed = True
    while changed:
        changed = False
        for node in functions:
            if node.name in live:
                continue
            if _returns_a_call_to(node, live) or _takes_a_live_fixture(node, live & fixtures):
                live.add(node.name)
                changed = True
    return frozenset(live)


def _is_a_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a function is declared a pytest fixture.

    Args:
        node: The function.

    Returns:
        True for any spelling of the decorator, bare or called.
    """
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr == "fixture":
            return True
        if isinstance(target, ast.Name) and target.id == "fixture":
            return True
    return False


def _parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.arg, ...]:
    """Every positional or keyword parameter of a function.

    Args:
        node: The function.

    Returns:
        The parameters, excluding ``*args`` and ``**kwargs``, which no pytest
        fixture is delivered through.
    """
    args = node.args
    return (*args.posonlyargs, *args.args, *args.kwonlyargs)


def _takes_a_machine_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a function receives this machine through a pytest fixture.

    Args:
        node: The function.

    Returns:
        True when any parameter names one of :data:`MACHINE_FIXTURES`.
    """
    return any(arg.arg in MACHINE_FIXTURES for arg in _parameter_names(node))


def _takes_a_live_fixture(
    node: ast.FunctionDef | ast.AsyncFunctionDef, live_fixtures: set[str]
) -> bool:
    """Whether a function names a fixture that was itself graded live.

    Args:
        node: The function.
        live_fixtures: Fixture names already known live.

    Returns:
        True when any parameter names one.
    """
    return any(arg.arg in live_fixtures for arg in _parameter_names(node))


def _returns_a_call_to(node: ast.FunctionDef | ast.AsyncFunctionDef, live: set[str]) -> bool:
    """Whether a function hands back what a live function produced.

    Covers the two shapes in this tree: returning the call directly, and binding
    it to a local that a later ``return`` names.

    Args:
        node: The function.
        live: Names already known live.

    Returns:
        True when it does.
    """
    from_live: set[str] = set()
    for stmt in scope_statements(node):
        if isinstance(stmt, ast.Assign):
            name = _assigned_name(stmt)
            if name is not None and _calls_any(stmt.value, live):
                from_live.add(name)
        elif isinstance(stmt, ast.Return) and stmt.value is not None:
            if _calls_any(stmt.value, live):
                return True
            if isinstance(stmt.value, ast.Name) and stmt.value.id in from_live:
                return True
    return False


def _calls_any(value: ast.expr, live: set[str]) -> bool:
    """Whether an expression calls one of the named functions.

    Args:
        value: The expression.
        live: The names to look for.

    Returns:
        True when a call to any of them appears anywhere inside it.
    """
    for node in ast.walk(value):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name in live:
            return True
    return False


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


class _ModuleScan:
    """One module's assertions, graded against the tree's declarations.

    Held as a class because the scan carries four derived tables at once - the
    class registry, the module's own classes, its return annotations and its
    live-function set - and threading all four through free functions turns
    every signature into a parameter list nobody reads.
    """

    def __init__(
        self,
        module: str,
        tree: ast.Module,
        registry: Mapping[str, list[Redacting]],
        returns: Mapping[str, str] | None = None,
    ) -> None:
        """Prepare the tables this module's scan reads.

        Args:
            module: Repo-relative path.
            tree: The parsed module.
            registry: Every redacting class in the tree, by simple class name.
            returns: Tree-wide function name to return-annotation word, used as
                a FALLBACK behind this module's own. ``world.load_world_from_bytes``
                hands back a redacting class from another file, and a scan that
                reads only local ``def``s cannot see it - which makes calling the
                producer through its module the one-word evasion of this guard.
        """
        self.module = module
        self.tree = tree
        self.registry = registry
        self.local = {
            entry.name: entry
            for entries in registry.values()
            for entry in entries
            if entry.module == module
        }
        self.returns = dict(returns or {})
        self.returns.update(
            {
                node.name: tail
                for node in ast.walk(tree)
                if isinstance(node, ANY_FUNCTION)
                and (tail := annotation_tail(node.returns)) is not None
            }
        )
        self.live = live_functions(tree, reach_seeds(tree))

    def lookup(self, name: str | None) -> Redacting | None:
        """Resolve a class word to the declaration it names.

        A class defined in THIS module wins, because a simple name resolves
        locally first in Python too. Two same-named classes elsewhere in the
        tree - and this tree ships two ``Sandbox`` classes - are merged by
        UNIONING their withheld fields, which over-reports rather than
        under-reports.

        Args:
            name: The class word, or None.

        Returns:
            The declaration, or None when nothing in the tree declares it.
        """
        if name is None:
            return None
        if name in self.local:
            return self.local[name]
        entries = self.registry.get(name)
        if not entries:
            return None
        if len(entries) == 1:
            return entries[0]
        merged = frozenset().union(*(entry.withheld for entry in entries))
        return Redacting("<several>", name, 0, frozenset(), merged)

    def findings(self) -> list[Finding]:
        """Every assertion in this module that reaches a withheld field.

        Returns:
            The findings, one per rendered sub-expression.
        """
        scopes: list[ast.AST] = [self.tree]
        scopes += [node for node in ast.walk(self.tree) if isinstance(node, ANY_FUNCTION)]
        out: list[Finding] = []
        for scope in scopes:
            out += _ScopeScan(self, scope).findings()
        return out


class _ScopeScan:
    """One lexical scope's bindings, and the assertions that render them."""

    def __init__(self, owner: _ModuleScan, scope: ast.AST) -> None:
        """Bind the scope's parameters and walk its statements in order.

        Args:
            owner: The module scan holding the derived tables.
            scope: A module or function definition.
        """
        self.owner = owner
        self.scope = scope
        self.holders: dict[str, Redacting] = {}
        self.aliases: dict[str, tuple[str, str]] = {}
        self.live = False
        if isinstance(scope, ANY_FUNCTION):
            self.live = _takes_a_machine_fixture(scope) or _takes_a_live_fixture(
                scope, set(owner.live)
            )
            for arg in _parameter_names(scope):
                declared = owner.lookup(annotation_tail(arg.annotation))
                if declared is None:
                    continue
                self.holders[arg.arg] = declared
                # CS-441's rule, applied to this channel. A holder that arrived
                # as a PARAMETER came from outside this scope, so nothing here
                # can say it was built from a synthetic fixture. The class
                # withheld those fields because they CAN carry personal data,
                # and a helper one call deeper gets the object intact.
                self.live = True

    def holder_of(self, expr: ast.expr) -> Redacting | None:
        """The redacting class an expression evaluates to, if any.

        Args:
            expr: The receiver of an attribute read.

        Returns:
            Its declaration, resolved through a local binding, a direct
            construction or a callee's return annotation.
        """
        match expr:
            case ast.Name(id=name):
                return self.holders.get(name)
            case ast.Call(func=ast.Name(id=name)):
                return self.owner.lookup(name) or self.owner.lookup(self.owner.returns.get(name))
            case ast.Call(func=ast.Attribute(attr=attr)):
                return self.owner.lookup(self.owner.returns.get(attr))
            case _:
                return None

    def hit(self, expr: ast.expr) -> tuple[str, str] | None:
        """The withheld field an explained sub-expression renders, if any.

        Args:
            expr: A node from :func:`explained`.

        Returns:
            Holder class and field name, or None.
        """
        if isinstance(expr, ast.Attribute):
            holder = self.holder_of(expr.value)
            if holder is not None and expr.attr in holder.withheld:
                return (holder.name, expr.attr)
        if isinstance(expr, ast.Name):
            return self.aliases.get(expr.id)
        return None

    def _bind(self, target: str, value: ast.expr | None, annotation: ast.expr | None) -> None:
        """Record what a local name now holds.

        A rebinding CLEARS a stale alias, so a name reused for something safe
        stops carrying the finding of what it held before.

        Args:
            target: The bound name.
            value: The assigned expression, if there is one.
            annotation: Its declared type, if there is one.
        """
        declared = self.owner.lookup(annotation_tail(annotation))
        if declared is None and value is not None:
            declared = self.holder_of(value)
        if declared is not None:
            self.holders[target] = declared
        carried = self.hit(value) if value is not None else None
        if carried is not None:
            self.aliases[target] = carried
        else:
            self.aliases.pop(target, None)
        if value is not None and _calls_any(value, set(self.owner.live)):
            self.live = True

    def findings(self) -> list[Finding]:
        """Walk the scope in source order, collecting findings.

        Returns:
            One finding per rendered withheld field.
        """
        out: list[Finding] = []
        for stmt in scope_statements(self.scope):
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                self._bind(stmt.target.id, stmt.value, stmt.annotation)
            elif isinstance(stmt, ast.Assign):
                name = _assigned_name(stmt)
                if name is not None:
                    self._bind(name, stmt.value, None)
            elif isinstance(stmt, ast.Assert):
                out += self._assert_findings(stmt)
        return out

    def _assert_findings(self, stmt: ast.Assert) -> list[Finding]:
        """Findings from one assert statement.

        Args:
            stmt: The assert.

        Returns:
            One finding per explained sub-expression that reaches a withheld
            field.
        """
        out: list[Finding] = []
        for node in explained(stmt.test):
            found = self.hit(node)
            if found is None:
                continue
            out.append(
                Finding(
                    module=self.owner.module,
                    lineno=node.lineno,
                    holder=found[0],
                    field=found[1],
                    source=ast.unparse(node),
                    live=self.live,
                )
            )
        return out


def tracked_python_files() -> list[str]:
    """Every tracked or untracked-but-not-ignored ``*.py`` path in the repo.

    ``--others --exclude-standard`` is what puts a file added THIS session in
    scope. A guard enumerating ``--cached`` alone is green locally on a new file
    and red at the commit that tracks it.

    Returns:
        Repo-relative paths, forward-slashed by git.

    Raises:
        RuntimeError: When git is unavailable or reports failure. Silence here
            would make an empty sweep indistinguishable from a clean one.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
            timeout=120,
        )
    except OSError as exc:
        raise RuntimeError(f"git could not be run: {type(exc).__name__}") from None
    if result.returncode != 0:
        raise RuntimeError(f"git ls-files exited {result.returncode}")
    listed = result.stdout.decode("utf-8", errors="replace").splitlines()
    return [line for line in listed if line.strip()]


@cache
def scan_repo() -> tuple[tuple[Redacting, ...], tuple[Finding, ...]]:
    """Derive every declaration in the tree, then every assertion bypassing one.

    Cached because the whole sweep parses every tracked module twice and several
    tests below consume it. The result is immutable, so the cache cannot be
    mutated by one caller into a lie told to the next.

    Returns:
        The redacting-class declarations, and the findings.
    """
    trees: dict[str, ast.Module] = {}
    for relative in tracked_python_files():
        source = (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        trees[relative] = ast.parse(source)

    opaque = frozenset(
        node.name
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and repr_method(node) is not None
    )

    registry: dict[str, list[Redacting]] = {}
    declarations: list[Redacting] = []
    for relative, tree in trees.items():
        for entry in redacting_classes(relative, tree, opaque):
            registry.setdefault(entry.name, []).append(entry)
            declarations.append(entry)

    returns = {
        node.name: tail
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, ANY_FUNCTION) and (tail := annotation_tail(node.returns)) is not None
    }

    findings: list[Finding] = []
    for relative, tree in trees.items():
        findings += _ModuleScan(relative, tree, registry, returns).findings()
    return (tuple(declarations), tuple(findings))


def scan_source(module: str, source: str) -> list[Finding]:
    """Run the detector over ONE synthetic module, against the tree's registry.

    The control path: a sweep that finds nothing in the tree is
    indistinguishable from a sweep that looks for nothing, so the tests below
    drive this with sources carrying one instance of each shape.

    Args:
        module: A label for the findings.
        source: Python source.

    Returns:
        The findings.
    """
    tree = ast.parse(source)
    opaque = frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and repr_method(node) is not None
    )
    registry: dict[str, list[Redacting]] = {}
    for entry in redacting_classes(module, tree, opaque):
        registry.setdefault(entry.name, []).append(entry)
    return _ModuleScan(module, tree, registry).findings()
