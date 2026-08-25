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

WHAT THIS GUARD COVERS, STATED AS A BOUNDARY RATHER THAN AS A CLAIM. It detects
ONE class of defect: an assertion that renders a field a class DECLARED unsafe
by shipping a hand-written ``__repr__`` that withholds it. That is a structural
property, and it is NOT the same population as "a save-derived name, a home path
or an account directory". A personal value whose holder never declared a
redacting ``__repr__`` is invisible here, because there is no declaration to
bypass. The shapes that are therefore NOT covered are measured and pinned by
``test_the_uncovered_shapes_are_pinned_rather_than_silently_absent``, and they
include a default-``repr`` dataclass, a bare ``str`` holding a world name, a
``Path`` from ``tmp_path``, a plain dict, list or set, a ``NamedTuple`` with no
hand-written repr, and a value returned straight from a fixture with no class at
all. Reading a green run here as "no assertion can render personal data" is
reading it as something it does not say.

WITHIN THAT BOUNDARY THE POPULATION IS DERIVED, and that half is real. There is
no list of modules, classes or fields. This module derives:

  1. every class in the tree that ships a ``__repr__``;
  2. from each, the fields that ``__repr__`` actually renders (disclosed) and
     the fields it does not (withheld) - read out of the ``__repr__`` body by
     walking each ``self.<field>`` read UP to the returned expression;
  3. of the withheld ones, those whose own annotation is repr-TRANSPARENT, that
     is, not composed entirely of other redacting classes;
  4. every assertion in the tree whose rewritten explanation reaches one.

Fields are found both as class-level annotations AND as ``self.<field>``
assignments in ``__init__``, because reading only the first graded a
hand-written ``__repr__`` over an unannotated field as withholding nothing.

WHAT COUNTS AS WITHHOLDING, and this is where the guard was wrong. A wrapper is
a MASK only when it cannot carry its argument's contents into the rendering.
``len(self.words)`` and ``sum(self.tags.values())`` are masks.
``dict(sorted(self.tags.items()))``, ``sorted(self.words)`` and
``", ".join(self.words)`` are NOT - each prints every element. Reading any
wrapping call as a mask made this guard report SEVEN leaks in one class whose
own docstring reads "COUNTS ONLY. No field here can hold a path, a name, a word
or a value", and all seven were wrong: 64 per cent of the entire live tier was
false. A tier 1 guard that reports leaks which are not leaks trains its reader
to ignore it. The two vocabularies below PARTITION the wrappers this tree uses,
and a project mask like ``masked_token`` is DERIVED rather than named - a
module-level function whose returns never reach a parameter except through a
reduction is a reduction itself.

WHY THE EXPLAINED SET IS COMPUTED RATHER THAN GUESSED. Which sub-expressions
pytest reprs is a property of ``_pytest.assertion.rewrite.AssertionRewriter``,
not of intuition. :func:`explained` mirrors its dispatch exactly, and falls back
to ``generic_visit`` - which reprs a node WHOLE - for everything else. Which
sub-expressions such a rendering actually CONTAINS was measured under real
pytest rather than assumed, because the shapes look alike in the source:
``f"{sweep.words}"``, ``len(words := sweep.words)`` and ``[sweep.words]`` each
print the field, while ``any(x in n for n in sweep.words)`` prints a memory
address and ``lambda: sweep.words`` prints a function. :func:`rendered_parts`
carries the measured answer, and it is why a comprehension contributes its
ITERABLE and a generator contributes nothing.

THE THREE CASES THAT MUST NOT BE FLAGGED, and this half is load-bearing.

  ``assert sweep.saves <= 0``       a DISCLOSED field. The class chose to
                                    render it, so rendering it again discloses
                                    nothing the repr did not.
  ``assert sweep == other``         the WHOLE OBJECT. The redacting ``__repr__``
                                    is exactly what runs here, which is what it
                                    was written for. Measured, not assumed.
  ``assert count <= CEILING``       the REMEDY: the aggregate reduced to a plain
                                    scalar BEFORE the assert, so the rendered
                                    expression holds a number and nothing else.

THE BINDING-TARGET FAMILY, all fixed in one place because they were one bug.
Every shape below hands a withheld field to a local, and each failed for the
same reason - the scan read only a single bare ``Name`` target::

    words = sweep.words                  single target, the only one covered
    first = second = sweep.words         multiple targets
    words, other = sweep.words, None     tuple unpack
    mutated, applied = _sweep()          tuple unpack of a returning call
    for sweep in (one, two): ...         loop target
    with opened() as sweep: ...          context-manager target
    len(words := sweep.words)            walrus

Measured on this tree, the tuple-unpack form alone walked four assertions past
the guard in one file. It is a BINDING problem and not a naming one: isolating
it with the variable name held constant across both arms flagged only the
single-target form.

WHAT IS STILL NOT TRACKED, named rather than implied away. A subscript or
attribute assignment target - ``holder["w"] = sweep.words`` - binds nothing this
can follow, so a later read of ``holder["w"]`` is invisible. And an alias is ONE
HOP: a field routed through a helper and rendered from that helper's RETURN is
not flagged, because the class made no declaration about the helper's return.

LIVE AND LATENT, a partition and not a severity opinion, and LIVE IS THE DEFAULT.
The same construct is a DISCLOSURE when the holder was built from the real save
library, from a machine fixture or from a caller one frame up, and a LATENT
defect when it was built from a synthetic fixture in the process. Latent is a
CLAIM, and the only thing that earns it is a module's own readable
``_GRADED_LIBRARY_REACH`` declaration. A module that ships none, misspells the
binding, or writes one this cannot read - a ``{**BASE}`` merge, whose ``**``
entry has key ``None`` - gets LIVE for every finding. Measured before that rule
existed: each of those three demoted a live leak to latent, silently, in the
direction that hides a disclosure.
"""

from __future__ import annotations

import ast
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

#: A function definition of either colour. ``ast.AsyncFunctionDef`` is NOT a
#: subclass of ``ast.FunctionDef``, and a guard that forgets it covers half its
#: population while reporting a count for all of it.
ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)

#: Wrappers that CARRY their argument's contents into the rendering. A field
#: appearing only inside one of these is DISCLOSED, not withheld.
#:
#: ``dict``, ``sorted`` and ``join`` are the three this tree actually uses, and
#: reading them as masks is what produced a 64 per cent false rate in the live
#: tier. ``str``, ``repr``, ``ascii`` and ``format`` are here rather than in a
#: separate set because they are the most transparent wrappers of all.
CONTENT_TRANSPARENT: Final = frozenset(
    {
        "ascii",
        "dict",
        "enumerate",
        "format",
        "frozenset",
        "items",
        "join",
        "keys",
        "list",
        "repr",
        "reversed",
        "set",
        "sorted",
        "str",
        "tuple",
        "values",
        "zip",
    }
)

#: Wrappers that CANNOT carry their argument's contents through - the result is
#: a number, a flag or a digest whatever the input was.
#:
#: ``min`` AND ``max`` ARE DELIBERATELY ABSENT, and the choice is free rather
#: than cautious: each returns an ELEMENT, so over a set of struct words it
#: prints one of them, and a sweep of every ``__repr__`` in this tree finds
#: neither used in one. Excluding them changes no verdict today and is the safe
#: answer the day somebody writes ``f"{max(self.words)}"``.
CONTENT_REDUCERS: Final = frozenset(
    {
        "abs",
        "all",
        "any",
        "bit_length",
        "blake2b",
        "bool",
        "count",
        "hexdigest",
        "id",
        "len",
        "md5",
        "ord",
        "round",
        "sha1",
        "sha256",
        "sum",
    }
)

#: Types whose whole value space is numbers and flags. Rendering one prints a
#: number, so it cannot carry a save-derived name, a home path or an account
#: directory whatever the class decided about it.
#:
#: WITHHELD IS NOT THE SAME CLAIM AS DISCLOSING. A ``__repr__`` may leave an
#: ``int`` field out for brevity, for stability of the rendering, or because it
#: is noise - none of which makes an assertion over it a leak. Before this set
#: existed the guard reported ``assert table.body_consumed ==
#: table.declared_body_length`` - two integers - as a live disclosure, which is
#: the same false-positive family as reading a container transform for a mask.
#: ``bytes`` IS DELIBERATELY ABSENT: on this project that is the decompressed
#: world body and its repr renders the content.
SCALAR_TYPES: Final = frozenset({"Decimal", "Fraction", "bool", "complex", "float", "int"})

#: Type words that only WRAP. The repr of one of these calls the repr of what it
#: holds, so a container of redacting classes renders redacted reprs and
#: discloses nothing.
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
#: user profile AND embeds ``getpass.getuser()`` in its own name.
#:
#: ``monkeypatch`` IS DELIBERATELY NOT HERE. It delivers no machine state; it is
#: how a test DETACHES from this machine, and in this tree that is what it is
#: used for. Counting it as machine reach inverted the partition on ten arms
#: whose every rendered value is a constant hand-authored beside them.
MACHINE_FIXTURES: Final = frozenset({"tmp_path", "tmp_path_factory"})

#: The declaration each module uses to name the helpers that genuinely read the
#: real save library. Owned by ``tests/save/reach_guard.py`` and asserted live
#: there; read here rather than restated, so the two cannot drift.
REACH_DECLARATION: Final = "_GRADED_LIBRARY_REACH"

#: Discovery entry points that yield a real save path directly, mirroring
#: ``reach_guard._LIBRARY_LOCATORS``. Spelled again rather than imported so the
#: whole tree's guard does not depend on the save package importing cleanly;
#: ``test_the_locator_seeds_match_the_reach_guard`` asserts the two agree.
LIBRARY_LOCATORS: Final = frozenset(
    {"resolve_save_root", "resolve_account_dir", "latest_save", "_library_save_paths"}
)

#: The filesystem primitives through which real data can enter a module,
#: mirroring ``reach_guard._REACHES_THE_LIBRARY``. What they decide here is
#: narrow and specific: whether a module was REQUIRED to declare its reach at
#: all. ``test_the_reach_primitives_match_the_reach_guard`` asserts the two
#: spellings agree, so a name added there cannot shrink this silently.
#:
#: A module that calls none of these had nothing to declare, so its silence is
#: not under-declaration and must not be read as one. Reading it as one graded
#: 24 assertions in one module LIVE whose every holder is parsed from bytes
#: hand-authored beside them - the same false-positive family as reading a
#: container transform for a mask, arriving by a different road.
REACH_PRIMITIVES: Final = frozenset(
    {
        "cwd",
        "expanduser",
        "glob",
        "home",
        "iterdir",
        "listdir",
        "open",
        "read_bytes",
        "resolve",
        "rglob",
        "scandir",
        "stat",
    }
)

#: How deep the derived-mask check follows one helper into another before giving
#: up and calling it transparent. One hop covers every mask in this tree and
#: bounds the walk on a tree that grows one.
MASK_RESOLUTION_HOPS: Final = 2


@dataclass(frozen=True)
class Redacting:
    """A class that ships a ``__repr__`` in order to withhold its own fields.

    Attributes:
        module: Repo-relative path of the file defining it.
        name: The class name.
        lineno: Where the class starts.
        disclosed: Fields the ``__repr__`` actually renders.
        withheld: Fields it does not render AND whose own annotation is
            repr-transparent, so rendering one renders its contents rather than
            another redacting repr.
        fields: Every field found, to the single class word its annotation
            resolves to. This is what lets a CHAINED receiver resolve -
            ``model.header.world_token`` needs ``header``'s own type.
    """

    module: str
    name: str
    lineno: int
    disclosed: frozenset[str]
    withheld: frozenset[str]
    fields: Mapping[str, str | None]


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
        live: True when the holder was built from the real save library, from a
            machine fixture or from a caller, OR when the module made no
            readable claim to the contrary. Latent has to be earned.
    """

    module: str
    lineno: int
    holder: str
    field: str
    source: str
    live: bool


def describe(findings: Sequence[Finding]) -> str:
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


def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    """Child-node identity to its parent, for one tree.

    Args:
        tree: The root.

    Returns:
        The mapping.
    """
    return {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


# ---------------------------------------------------------------------------
# The mask rule: which wrappers stop contents reaching a rendering
# ---------------------------------------------------------------------------


def _callee_name(call: ast.Call) -> str | None:
    """The bare name of whatever a call calls.

    Args:
        call: The call node.

    Returns:
        The function name, the method name, or None.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_reduction(
    call: ast.Call,
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
    hops: int,
) -> bool:
    """Whether a call cannot carry its argument's contents through.

    Args:
        call: The wrapping call.
        functions: Module-level functions, for resolving a project mask.
        hops: How much further the derived check may recurse.

    Returns:
        True for a declared reducer or a module function that reduces; False for
        a declared content-transparent wrapper and for anything unresolved -
        the direction that reports fewer findings, because a guard reporting
        leaks that are not leaks is the failure this rule was rewritten for.
    """
    name = _callee_name(call)
    if name is None:
        return False
    if name in CONTENT_REDUCERS:
        return True
    if name in CONTENT_TRANSPARENT:
        return False
    target = functions.get(name)
    if target is None or hops <= 0:
        return False
    return _function_reduces(target, functions, hops - 1)


def _function_reduces(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
    hops: int,
) -> bool:
    """Whether a helper's returns never carry a parameter's contents out.

    THIS IS WHAT MAKES A PROJECT MASK DERIVED RATHER THAN NAMED.
    ``masked_token`` in ``clockspeed/save/header.py`` returns a prefix and a
    sha256 digest; its parameter reaches a ``return`` through nothing but a
    hashing primitive, so it reduces. A rule that knew only builtins would call
    the world token disclosed and stop grading the one field that matters most.

    Args:
        node: The helper.
        functions: Module-level functions, for one more hop.
        hops: Remaining recursion budget.

    Returns:
        True when no parameter reaches a returned expression unmasked.
    """
    args = node.args
    names = {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if not names:
        return False
    kin = _parent_map(node)
    returned = {
        id(stmt.value)
        for stmt in ast.walk(node)
        if isinstance(stmt, ast.Return) and stmt.value is not None
    }
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Name) or inner.id not in names:
            continue
        if _reaches_unmasked(inner, kin, returned, functions, hops):
            return False
    return True


def _reaches_unmasked(
    node: ast.AST,
    kin: Mapping[int, ast.AST],
    targets: frozenset[int] | set[int],
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
    hops: int,
) -> bool:
    """Whether a value read here reaches a target expression with no reduction.

    Walks UP the parent chain. A call in FUNC position is stepped over rather
    than judged - in ``self.tags.values()`` the attribute is the callee, not an
    argument, and treating it as one would call every method access a mask.

    Args:
        node: Where the value is read.
        kin: Parent map for the enclosing tree.
        targets: Node identities that count as "rendered".
        functions: Module-level functions, for resolving a project mask.
        hops: Recursion budget for the derived mask check.

    Returns:
        True when it arrives unmasked.
    """
    current: ast.AST = node
    while True:
        if id(current) in targets:
            return True
        parent = kin.get(id(current))
        if parent is None:
            return False
        if (
            isinstance(parent, ast.Call)
            and current is not parent.func
            and _is_reduction(parent, functions, hops)
        ):
            return False
        current = parent


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

    A STRING annotation is parsed rather than skipped. An annotation this cannot
    read yields ``?``, which belongs to no known class and therefore counts as
    transparent - the conservative direction.

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


def declared_fields(node: ast.ClassDef) -> dict[str, ast.expr | None]:
    """Every field of a class, to its annotation node.

    BOTH SPELLINGS, and the second one is a repair. Reading only class-level
    ``name: T`` graded a class whose ``__repr__`` withholds an
    ``__init__``-assigned attribute as withholding nothing at all, so the whole
    class dropped out of the population while still looking covered.

    Args:
        node: The class.

    Returns:
        Field name to its annotation, which is None when only an assignment was
        found. An unknown annotation reads as transparent, which is the
        conservative direction.
    """
    fields: dict[str, ast.expr | None] = {}
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields[item.target.id] = item.annotation
    for method in node.body:
        if not isinstance(method, ANY_FUNCTION) or not method.args.args:
            continue
        receiver = method.args.args[0].arg
        for name, annotation in _receiver_assignments(method, receiver).items():
            fields.setdefault(name, annotation)
    return fields


def _receiver_assignments(
    method: ast.FunctionDef | ast.AsyncFunctionDef, receiver: str
) -> dict[str, ast.expr | None]:
    """Fields a method assigns onto its own receiver.

    Args:
        method: The method.
        receiver: Its first parameter's name.

    Returns:
        Field name to the annotation of the parameter it was assigned from,
        where that is readable, else None.
    """
    parameters = {
        arg.arg: arg.annotation
        for arg in (
            *method.args.posonlyargs,
            *method.args.args,
            *method.args.kwonlyargs,
        )
    }
    found: dict[str, ast.expr | None] = {}
    for stmt in ast.walk(method):
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            targets = [stmt.target]
            value = stmt.annotation
        for target in targets:
            if not isinstance(target, ast.Attribute):
                continue
            if not (isinstance(target.value, ast.Name) and target.value.id == receiver):
                continue
            hint = value if isinstance(stmt, ast.AnnAssign) else None
            if hint is None and isinstance(value, ast.Name):
                hint = parameters.get(value.id)
            found[target.attr] = hint
    return found


def disclosed_fields(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    functions: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> frozenset[str]:
    """The fields a ``__repr__`` actually renders.

    Each ``self.<field>`` read is walked UP to the method's returned
    expressions. It is DISCLOSED when it arrives with no reduction on the way,
    whatever the syntax in between - so ``f"{self.x}"``,
    ``f"{dict(sorted(self.x.items()))}"``, ``f"{sorted(self.x)}"`` and
    ``", ".join(self.x)`` are all disclosure, and ``f"{len(self.x)}"``,
    ``f"{sum(self.x.values())}"`` and ``f"{masked_token(self.x)!r}"`` are not.

    STATED LIMIT: a read that never reaches a ``return`` - one inside an ``if``
    test, say - discloses nothing and is not counted either way, so a field
    mentioned only there stays withheld.

    Args:
        method: The class's ``__repr__``.
        functions: Module-level functions, for resolving a project mask.

    Returns:
        The disclosed field names.
    """
    if not method.args.args:
        return frozenset()
    receiver = method.args.args[0].arg
    kin = _parent_map(method)
    returned = {
        id(stmt.value)
        for stmt in ast.walk(method)
        if isinstance(stmt, ast.Return) and stmt.value is not None
    }
    out: set[str] = set()
    for node in ast.walk(method):
        if not isinstance(node, ast.Attribute):
            continue
        if not (isinstance(node.value, ast.Name) and node.value.id == receiver):
            continue
        if _reaches_unmasked(node, kin, returned, functions, MASK_RESOLUTION_HOPS):
            out.add(node.attr)
    return frozenset(out)


def module_functions(
    tree: ast.Module,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Every function defined at module scope, by name.

    Args:
        tree: The parsed module.

    Returns:
        The mapping. Methods are excluded: a project mask is a free function.
    """
    return {node.name: node for node in tree.body if isinstance(node, ANY_FUNCTION)}


def redacting_classes(
    module: str,
    tree: ast.Module,
    opaque: frozenset[str],
    known: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef] | None = None,
) -> list[Redacting]:
    """Every class in one module that ships a redacting ``__repr__``.

    Args:
        module: Repo-relative path, carried onto each record.
        tree: The parsed module.
        opaque: Names of classes that ship a ``__repr__`` anywhere in the tree.
        known: Tree-wide module functions, behind this module's own, so an
            IMPORTED mask resolves. MEASURED: ``masked_token`` is defined in
            ``clockspeed/save/header.py`` and imported by
            ``clockspeed/save/world.py``, so a same-module-only reader called
            ``WorldModel.token`` DISCLOSED - and a re-introduced leak over the
            world token then survived the sweep silently. A mutation that
            survives and a mutation that never applied look identical, which is
            the only reason this was caught.

    Returns:
        One record per such class.
    """
    functions = {**(known or {}), **module_functions(tree)}
    out: list[Redacting] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        method = repr_method(node)
        if method is None:
            continue
        shown = disclosed_fields(method, functions)
        fields = declared_fields(node)
        withheld = frozenset(
            name
            for name, annotation in fields.items()
            if name not in shown and not _cannot_disclose(annotation_names(annotation), opaque)
        )
        tails = {name: annotation_tail(annotation) for name, annotation in fields.items()}
        out.append(Redacting(module, node.name, node.lineno, shown, withheld, tails))
    return out


def _cannot_disclose(types: frozenset[str], opaque: frozenset[str]) -> bool:
    """Whether rendering a value of this annotation can carry nothing personal.

    Two ways to qualify, and both are about what the RENDERING contains rather
    than about what the class said. ``tuple[ResourceNode, ...]`` is safe because
    a tuple's repr calls each element's and ``ResourceNode`` withholds its own
    instance name. ``int`` is safe because it is a number. ``Mapping[str,
    Schema]`` is NEITHER, because the KEYS are bare strings and a mapping
    renders those directly.

    An annotation this could not read carries ``?``, which is in neither set, so
    an unreadable annotation stays disclosing - the direction that keeps
    grading.

    Args:
        types: The annotation's type words.
        opaque: Class names that ship a ``__repr__``.

    Returns:
        True only when at least one real type is named and every one is either a
        scalar or a class that redacts itself.
    """
    meaningful = types - PASS_THROUGH_TYPES
    return bool(meaningful) and meaningful <= (opaque | SCALAR_TYPES)


# ---------------------------------------------------------------------------
# Deriving the channel: which sub-expressions pytest reprs
# ---------------------------------------------------------------------------


def explained(node: ast.expr) -> Iterator[ast.expr]:
    """Every sub-expression pytest's rewriter reprs for an asserted expression.

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
    displays the result, or falls to ``generic_visit``, which does exactly that.

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
    operands: list[ast.expr]
    match node:
        case ast.BoolOp(values=values):
            operands = list(values)
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


def rendered_parts(node: ast.expr) -> Iterator[ast.expr]:
    """Sub-expressions whose VALUE a node's own repr embeds verbatim.

    ``generic_visit`` reprs a node whole, and for some shapes that rendering
    contains the sub-expression's value and for others it does not. Which is
    which was MEASURED under real pytest rather than reasoned about, because the
    two look identical in the source::

        f"{sweep.words}"                 renders frozenset({'<a word>'})
        len(words := sweep.words)        renders frozenset({'<a word>'})
        [sweep.words]                    renders [frozenset({'<a word>'})]
        [n.path for n in sweep.words]    renders the DERIVED list, which
                                         carries what the field held
        any(x in n for n in sweep.words) renders <generator object ...>
        lambda: sweep.words              renders <function <lambda> at 0x...>

    A GENERATOR IS OPAQUE AND A LIST COMPREHENSION IS NOT, and reading them
    alike cost three false findings in one file - all three of the shape
    ``not any(x in name for name in parsed.names)``, whose rendering carries a
    memory address and nothing else. So a comprehension contributes its
    ITERABLE, a generator contributes nothing, and neither contributes its body.

    STATED LIMIT: derivation is followed exactly one step, into a comprehension's
    iterable. ``list(name for name in sweep.words)`` renders the resulting list
    and is NOT flagged, because the value that reaches the report came out of a
    call this guard does not follow into.

    Args:
        node: The node rendered whole.

    Yields:
        Each sub-expression whose value the rendering embeds.
    """
    for part in _embedded_parts(node):
        yield part
        yield from rendered_parts(part)


def _embedded_parts(node: ast.expr) -> list[ast.expr]:
    """One level of :func:`rendered_parts`.

    Args:
        node: The node rendered whole.

    Returns:
        Its directly embedded sub-expressions, empty for a shape whose repr
        carries none of them.
    """
    parts: list[ast.expr]
    match node:
        case ast.JoinedStr(values=values):
            parts = list(values)
        case ast.FormattedValue(value=value) | ast.NamedExpr(value=value):
            parts = [value]
        case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
            parts = list(elts)
        case ast.Dict(keys=keys, values=values):
            parts = [key for key in keys if key is not None] + list(values)
        case ast.IfExp(body=body, orelse=orelse):
            parts = [body, orelse]
        case (
            ast.ListComp(generators=generators)
            | ast.SetComp(generators=generators)
            | ast.DictComp(generators=generators)
        ):
            parts = [generator.iter for generator in generators]
        case _:
            parts = []
    return parts


def scope_statements(scope: ast.AST) -> Iterator[ast.stmt]:
    """Every statement lexically inside one scope, in source order.

    Descends through ``if``, ``for``, ``with`` and ``try`` bodies - a binding
    made in one of those is visible to an assert after it - and STOPS at a
    nested function or class.

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


def _borrowed_declaration_reader() -> object:
    """``reach_guard``'s own reader for the graded-reach declaration, if it loads.

    BORROWED RATHER THAN RE-DERIVED, because that module OWNS this declaration's
    grammar and has already been refuted twice over it. It reads a string key,
    an ``f.__name__`` key and a comprehension key resolved through its iterable
    by position, and a sibling test asserts what it reads matches what the
    module holds at runtime. A second reader here would be CS-433's defect - two
    lists of the same kind of thing in two files, drifting - and it was: the
    literal-only reader below called a module UNDER-DECLARED whose declaration
    is a comprehension over a shipped table of (label, function) pairs, and
    graded 36 of its assertions live on the strength of it.

    Returns:
        The reader, or None when the save test package will not import. A
        failure to load leaves the literal reader in charge, which reports MORE
        modules under-declared rather than fewer.
    """
    try:
        # DELIBERATELY LAZY. This module is imported by a test at the repo ROOT
        # and grades the whole tree; importing the save test package at module
        # scope would make every module's grade depend on that package
        # importing cleanly on a machine with no game installed.
        from tests.save import reach_guard  # noqa: PLC0415
    except Exception:
        return None
    return getattr(reach_guard, "_declared_graded_names", None)


def reach_seeds(tree: ast.Module) -> tuple[frozenset[str], bool]:
    """The helpers a module DECLARES as reaching the real save library.

    Args:
        tree: The parsed module.

    Returns:
        The declared helper names plus the locators, and whether the
        declaration was READABLE. A declaration that is present but that
        NEITHER reader can extract a name from - a frozenset value, a merge
        whose ``**`` entry carries key ``None`` - returns False, and so does an
        absent one. Every finding in a module that OWED a declaration and
        returned False is then graded LIVE: latent is a claim, and a module that
        made no readable claim has not made it.
    """
    declared: ast.expr | None = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if _assigned_names(node) == [REACH_DECLARATION] and node.value is not None:
            declared = node.value
            break
    if declared is None:
        return (frozenset(LIBRARY_LOCATORS), False)

    literal = _mapping_key_names(declared)
    borrowed = _borrowed_declaration_reader()
    names: set[str] = set(literal or ())
    if borrowed is not None:
        names |= set(borrowed(tree))  # type: ignore[operator]
    readable = literal is not None or bool(names)
    return (frozenset(LIBRARY_LOCATORS) | names, readable)


def must_declare_reach(tree: ast.Module) -> bool:
    """Whether a module touches anything that could hand it real data.

    Mirrors ``reach_guard._module_reaches``: a module calling a filesystem
    primitive or a discovery locator is one whose reach has to be declared, and
    a module calling none had nothing to declare. Only the first kind can
    UNDER-declare, and only the first kind is graded live for staying silent.

    Args:
        tree: The parsed module.

    Returns:
        True when a declaration was required.
    """
    wanted = REACH_PRIMITIVES | LIBRARY_LOCATORS
    return any(
        isinstance(node, ast.Call) and _callee_name(node) in wanted for node in ast.walk(tree)
    )


def _assigned_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    """Every bare name a binding statement assigns to.

    Args:
        node: The assignment.

    Returns:
        The names, flattening a tuple or list target. A subscript or attribute
        target contributes nothing, because nothing here can follow one.
    """
    targets = [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)
    out: list[str] = []
    for target in targets:
        out += _target_names(target)
    return out


def _target_names(target: ast.expr) -> list[str]:
    """The bare names one assignment target binds.

    Args:
        target: The target expression.

    Returns:
        Its names, flattened through tuple and list targets.
    """
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for element in target.elts for name in _target_names(element)]
    return []


def _mapping_key_names(value: ast.expr) -> set[str] | None:
    """The key names of a dict literal, through a one-call wrapper.

    Args:
        value: The assigned expression, possibly ``MappingProxyType({...})``.

    Returns:
        Every key spelled as a string literal or as ``something.__name__``, or
        None when the declaration cannot be read - a non-dict value, or a
        ``{**BASE}`` merge, whose ``**`` entry carries key ``None`` and would
        otherwise be dropped in silence.
    """
    if isinstance(value, ast.Call) and value.args:
        value = value.args[0]
    if not isinstance(value, ast.Dict):
        return None
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
        else:
            return None
    return out


def live_functions(tree: ast.Module, seeds: frozenset[str]) -> frozenset[str]:
    """Every function in a module whose return value carries real data.

    A FIXPOINT rather than a single pass, because the shape this tree ships puts
    the declared reader one call behind the caller. The fixture hop is part of
    the same fixpoint: a ``@pytest.fixture`` taking ``tmp_path`` and returning a
    holder makes every test that names it live.

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
        The parameters, excluding ``*args`` and ``**kwargs``.
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

    Args:
        node: The function.
        live: Names already known live.

    Returns:
        True when it does.
    """
    from_live: set[str] = set()
    for stmt in scope_statements(node):
        if isinstance(stmt, ast.Assign) and _calls_any(stmt.value, live):
            from_live.update(_assigned_names(stmt))
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
        if isinstance(node, ast.Call) and _callee_name(node) in live:
            return True
    return False


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


class _ModuleScan:
    """One module's assertions, graded against the tree's declarations."""

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
                a FALLBACK behind this module's own, so calling a producer
                through its module is not a one-word evasion.
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
        seeds, readable = reach_seeds(tree)
        # UNDER-DECLARED, not merely undeclared. A module that reaches a
        # primitive and then says nothing readable about it has withheld the
        # only thing that can earn a latent grade, so every finding in it is
        # LIVE. A module that reaches nothing had nothing to declare.
        self.under_declared = must_declare_reach(tree) and not readable
        self.live = live_functions(tree, seeds)

    def lookup(self, name: str | None) -> Redacting | None:
        """Resolve a class word to the declaration it names.

        A class defined in THIS module wins. Two same-named classes elsewhere
        are merged by UNIONING their withheld fields, which over-reports rather
        than under-reports.

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
        fields: dict[str, str | None] = {}
        for entry in entries:
            fields.update(entry.fields)
        return Redacting("<several>", name, 0, frozenset(), merged, fields)

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
        """Bind the scope's parameters and prepare to walk its statements.

        Args:
            owner: The module scan holding the derived tables.
            scope: A module or function definition.
        """
        self.owner = owner
        self.scope = scope
        self.holders: dict[str, Redacting] = {}
        self.aliases: dict[str, tuple[str, str]] = {}
        # LIVE IS THE DEFAULT when the module owed a claim and did not make one.
        self.live = owner.under_declared
        if isinstance(scope, ANY_FUNCTION):
            self.live = self.live or _takes_a_machine_fixture(scope)
            self.live = self.live or _takes_a_live_fixture(scope, set(owner.live))
            for arg in _parameter_names(scope):
                declared = owner.lookup(annotation_tail(arg.annotation))
                if declared is None:
                    continue
                self.holders[arg.arg] = declared
                # CS-441's rule, applied to this channel. A holder that arrived
                # as a PARAMETER came from outside this scope, so nothing here
                # can say it was built from a synthetic fixture.
                self.live = True

    def holder_of(self, expr: ast.expr) -> Redacting | None:
        """The redacting class an expression evaluates to, if any.

        A CHAINED receiver resolves through the inner holder's own field
        annotations: ``model.header.world_token`` needs ``header``'s type, and
        without that step every chained read walked free.

        Args:
            expr: The receiver of an attribute read.

        Returns:
            Its declaration, or None.
        """
        match expr:
            case ast.Name(id=name):
                return self.holders.get(name)
            case ast.Call(func=ast.Name(id=name)):
                return self.owner.lookup(name) or self.owner.lookup(self.owner.returns.get(name))
            case ast.Call(func=ast.Attribute(attr=attr)):
                return self.owner.lookup(self.owner.returns.get(attr))
            case ast.Attribute(value=inner, attr=field):
                holder = self.holder_of(inner)
                if holder is None:
                    return None
                return self.owner.lookup(holder.fields.get(field))
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

    def _subtree_hit(self, expr: ast.expr) -> tuple[ast.expr, tuple[str, str]] | None:
        """The first withheld read whose VALUE a node rendered whole embeds.

        Args:
            expr: The node rendered whole.

        Returns:
            The offending inner node and its finding, or None.
        """
        for inner in rendered_parts(expr):
            found = self.hit(inner)
            if found is not None:
                return (inner, found)
        return None

    def _bind(self, target: ast.expr, value: ast.expr | None, annotation: ast.expr | None) -> None:
        """Record what one assignment target now holds.

        A rebinding CLEARS a stale alias, so a name reused for something safe
        stops carrying the finding of what it held before.

        Args:
            target: The target expression.
            value: The assigned expression, if there is one.
            annotation: Its declared type, if there is one.
        """
        if isinstance(target, (ast.Tuple, ast.List)):
            self._bind_unpacked(target, value)
            return
        if not isinstance(target, ast.Name):
            # A subscript or attribute target binds nothing this can follow.
            return
        declared = self.owner.lookup(annotation_tail(annotation))
        if declared is None and value is not None:
            declared = self.holder_of(value)
        if declared is not None:
            self.holders[target.id] = declared
        carried = self.hit(value) if value is not None else None
        if carried is not None:
            self.aliases[target.id] = carried
        else:
            self.aliases.pop(target.id, None)
        if value is not None and _calls_any(value, set(self.owner.live)):
            self.live = True

    def _bind_unpacked(self, target: ast.Tuple | ast.List, value: ast.expr | None) -> None:
        """Bind a tuple or list target, pairing elementwise where it can.

        ``mutated, applied = _sweep_with_a_wrong_partition()`` is the shape that
        walked four assertions past this guard in one file. The pair cannot be
        split, so BOTH names take the call's own holder - over-reporting rather
        than under-reporting.

        Args:
            target: The tuple or list target.
            value: The assigned expression, if there is one.
        """
        if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts):
            for element, item in zip(target.elts, value.elts, strict=True):
                self._bind(element, item, None)
            return
        for element in target.elts:
            self._bind(element, value, None)

    def _bind_statement(self, stmt: ast.stmt) -> None:
        """Apply every binding one statement establishes.

        Args:
            stmt: The statement.
        """
        if isinstance(stmt, ast.AnnAssign):
            self._bind(stmt.target, stmt.value, stmt.annotation)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                self._bind(target, stmt.value, None)
        elif isinstance(stmt, (ast.For, ast.AsyncFor)):
            self._bind_loop(stmt)
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                if item.optional_vars is not None:
                    self._bind(item.optional_vars, item.context_expr, None)
        for inner in ast.walk(stmt):
            if isinstance(inner, ast.NamedExpr):
                self._bind(inner.target, inner.value, None)

    def _bind_loop(self, stmt: ast.For | ast.AsyncFor) -> None:
        """Bind a loop target from whichever element of its iterable resolves.

        ``for run in (guarded, control):`` walks two ``SandboxRun`` fixtures,
        and every read of ``run.output`` inside renders captured output whose
        own docstring says it carries the account name. The target was bound by
        nothing before this.

        Args:
            stmt: The loop.
        """
        source = stmt.iter
        candidates: list[ast.expr] = (
            list(source.elts) if isinstance(source, (ast.Tuple, ast.List, ast.Set)) else [source]
        )
        for candidate in candidates:
            if self.holder_of(candidate) is not None:
                self._bind(stmt.target, candidate, None)
                return

    def findings(self) -> list[Finding]:
        """Walk the scope in source order, collecting findings.

        Returns:
            One finding per rendered withheld field.
        """
        out: list[Finding] = []
        for stmt in scope_statements(self.scope):
            self._bind_statement(stmt)
            if isinstance(stmt, ast.Assert):
                out += self._assert_findings(stmt)
        return out

    def _assert_findings(self, stmt: ast.Assert) -> list[Finding]:
        """Findings from one assert statement.

        Args:
            stmt: The assert.

        Returns:
            One finding per explained sub-expression that reaches a withheld
            field, including one reached inside a node rendered whole.
        """
        out: list[Finding] = []
        seen: set[tuple[int, str, str]] = set()
        for node in explained(stmt.test):
            found = self.hit(node)
            offender = node
            if found is None and not _recursed_operands(node) and not isinstance(node, ast.Name):
                deeper = self._subtree_hit(node)
                if deeper is not None:
                    offender, found = deeper
            if found is None:
                continue
            key = (offender.lineno, found[0], found[1])
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Finding(
                    module=self.owner.module,
                    lineno=offender.lineno,
                    holder=found[0],
                    field=found[1],
                    source=ast.unparse(offender),
                    live=self.live,
                )
            )
        return out


def tracked_python_files() -> list[str]:
    """Every tracked or untracked-but-not-ignored ``*.py`` path in the repo.

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

    known: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for tree in trees.values():
        known.update(module_functions(tree))

    registry: dict[str, list[Redacting]] = {}
    declarations: list[Redacting] = []
    for relative, tree in trees.items():
        for entry in redacting_classes(relative, tree, opaque, known):
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
    """Run the detector over ONE synthetic module, against its own registry.

    The control path: a sweep that finds nothing in the tree is
    indistinguishable from a sweep that looks for nothing.

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
