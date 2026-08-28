"""CS-852 gap 1 - the exception channel, derived from the MESSAGE-BUILDING PATH.

WHAT THIS GRADES AND WHY THE SIBLING MODULE COULD NOT.
``tests/repr_rendering_guard.py`` derives its population from shipped FIELD
ANNOTATIONS and asks what a GENERATED ``__repr__`` prints. Its
``KIND_INHERITED`` grade rests on a premise that was MEASURED for a plain
class - no ``__repr__`` means ``object.__repr__``, which discloses no field -
and that premise is FALSE for every exception: ``BaseException.__repr__``
renders ``args``, and ``BaseException.__str__`` renders it too. So an error
that interpolates a save-derived name into its message discloses it through
both channels while shipping no ``__repr__`` at all, and that module's own
docstring records the gap rather than closing it. Deciding whether a given
error leaks needs the code that BUILDS the message, which is a different
analysis over a different part of the tree. This module is that analysis.

THE POPULATION AND THE VERDICTS ARE DERIVED BY THREE MECHANICAL RULES.

  E1  THE GOVERNING INITIALISER. Every class under :data:`GRADED_LAYER` that
      reaches an :data:`ARGS_ROOTS` word through its bases is on the channel.
      For each, the ``__init__`` that governs its ``args`` is resolved through
      the BASES and not from the class body: a class that ships none inherits
      one, and live classes in two of the save modules are governed that way -
      ``test_the_live_tree_has_a_class_governed_by_an_inherited_initialiser``
      is what keeps that a fact rather than a sentence. An analysis reading
      only a class's own body scores every one of them as having no
      message-building path and passes them in silence. NO COUNT IS WRITTEN
      HERE: the first draft of this paragraph carried one, transcribed rather
      than measured, and it was wrong. A class whose whole ancestry ships no
      ``__init__`` inherits ``Exception.__init__``, so its message is built at
      every construction site instead - :data:`SHAPE_FREE_TEXT` - and one that is
      never constructed anywhere in the shipped tree is :data:`SHAPE_UNRAISED`,
      recorded rather than passed, because a proof by walking no sites is a
      proof over nothing.

  E2  THE CHANNELS. An expression reaching ``args`` is split into the CHANNELS
      it renders. Composition is transparent - an f-string, a ``+``, a
      conditional, a :data:`COMPOSING_CALLS` wrapper, and a call to a MESSAGE
      BUILDER, which is derived rather than named: a module-level function
      whose every returned value composes into its own parameters, module
      literals and measure reducers over them. Descending a builder rebinds its
      parameters to the caller's expressions, so the channels stay the
      initialiser's own instead of collapsing into one opaque call.

  E3  THE PROOF. A channel is proven when it is one of four forms, and every
      other channel is a finding unless :data:`EXEMPT` records a measured
      reason.
        :data:`PROVEN_LITERAL`     a constant, a module-level name bound to
                                   one, or an ``__name__`` - authored in this
                                   repository, so no save byte reaches it.
        :data:`PROVEN_SCALAR`      an annotation whose whole value space is
                                   numbers and flags, or a measure reducer. A
                                   number carries no name, path or account id.
        :data:`PROVEN_VOCABULARY`  the value passes a membership test against a
                                   module-level collection of string literals
                                   before it reaches the message. Derived from
                                   the GUARD CLAUSE, inline or inside a helper
                                   the value is routed through - never from the
                                   helper's name.
        :data:`PROVEN_AT_SITES`    every construction or call site in the
                                   shipped tree binds the parameter to a proven
                                   expression. Weakest of the four, and
                                   deliberately labelled apart from the others.

THE TWO PROOFS THAT LOOK ALIKE ARE NOT THE SAME PROOF, AND THE DIFFERENCE IS
MEASURED. :data:`PROVEN_VOCABULARY` is a RUNTIME barrier - the value is refused
before the message exists. :data:`PROVEN_AT_SITES` is a STATIC fact about
today's callers and stops nothing at runtime; the same planted value that one
form refuses, the other renders. Both outcomes are asserted in
``tests/test_exception_messages.py`` so the weaker cannot be read as the
stronger, and a class downgraded from the first to the second reddens.

REDACTION IS A MITIGATION AND IS DELIBERATELY NOT A PROOF FORM.
``clockspeed/data/locate.py`` builds its needles from THIS MACHINE'S resolved
home, account and save-root spellings, so whether a call covers a given value
is a runtime property of one machine's configuration rather than a closed
vocabulary a static rule can read. Blessing any call by that name would also
accept a helper that redacted nothing. A redacted channel is therefore reported
UNPROVEN and carries an exemption stating what was measured at the site, which
keeps the judgement visible instead of laundering it through a name.

WHAT THIS DOES NOT REACH, stated rather than left to be discovered. The rule is
SYNTACTIC: it follows names, parameters and call sites through the syntax tree
and does not model reassignment order, aliasing, or a value arriving through a
container. Call sites are matched by CALLEE NAME across the shipped tree, so
two methods sharing a name pool their sites - which adds sites to prove and so
errs toward reporting. :data:`REACH_HOPS` bounds the backward walk, and running
out of budget is UNPROVEN rather than proven.

A BARE ``raise SomeError`` IS NOT A CONSTRUCTION SITE HERE, and that is safe
rather than merely tolerated. The walk indexes call nodes, so the parenthesis
free form is invisible to it - but the interpreter builds the instance with NO
arguments, so ``args`` is empty and there is nothing to disclose. MEASURED on
this tree: one such raise exists and its class builds its message from a module
constant in its own initialiser, which this module grades on the structured
path regardless.

THE CHAINED CAUSE IS A DIFFERENT CHANNEL AND IS NOT GRADED HERE. ``raise X(...)
from exc`` sets ``__cause__``, not ``args``, and Python's traceback machinery
renders that cause - filename included - without consulting any expression this
module can read. ``tests/test_redaction_scope.py`` records the same exclusion
for the same reason.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

from tests.assertion_rendering_guard import (
    MEASURE_REDUCERS,
    REPO_ROOT,
    SCALAR_TYPES,
    tracked_python_files,
)

__all__ = [
    "ARGS_ROOTS",
    "COMPOSING_CALLS",
    "EXEMPT",
    "GRADED_LAYER",
    "PROVEN_AT_SITES",
    "PROVEN_LITERAL",
    "PROVEN_SCALAR",
    "PROVEN_VOCABULARY",
    "REACH_HOPS",
    "REPO_ROOT",
    "SHAPE_FREE_TEXT",
    "SHAPE_STRUCTURED",
    "SHAPE_UNRAISED",
    "SHIPPED_ROOT",
    "UNPROVEN",
    "Channel",
    "ambiguous_callees",
    "build_index",
    "channels_of",
    "describe",
    "findings_in",
    "graded_classes",
    "live_index",
    "resolved_callees",
    "scan_channels",
    "stale_exemptions",
    "swept_modules",
    "ungraded_layers",
]

#: The layer ``docs/ARCHITECTURE.md`` names as the one that reads a save.
#: Stated as a path prefix so a new module in the layer is graded on arrival
#: rather than on somebody remembering to add it.
GRADED_LAYER: Final = "clockspeed/save/"

#: Everything shipped. The walk reads all of it so the narrowing above is a
#: measurable scope choice; ``ungraded_layers`` reports what it found and
#: declined to grade.
SHIPPED_ROOT: Final = "clockspeed/"

#: Base words whose rendering comes from ``BaseException`` rather than from
#: ``object``. A class reaching any of these renders ``args`` through BOTH
#: ``__repr__`` and ``__str__``.
ARGS_ROOTS: Final = frozenset(
    {
        "ArithmeticError",
        "AttributeError",
        "BaseException",
        "Exception",
        "IndexError",
        "KeyError",
        "LookupError",
        "OSError",
        "RuntimeError",
        "TypeError",
        "ValueError",
    }
)

#: Annotation words whose whole value space is numbers and flags, plus the
#: ``None`` an optional scalar carries. Imported rather than transcribed:
#: ``tests/assertion_rendering_guard.py`` owns the set and records why ``bytes``
#: is deliberately absent from it.
SCALAR_ANNOTATIONS: Final = SCALAR_TYPES | {"None"}

#: Calls that COMPOSE their arguments into a string without changing what the
#: arguments disclose. A channel inside one of these is graded, not blessed.
COMPOSING_CALLS: Final = frozenset({"ascii", "format", "join", "repr", "str"})

#: Attribute reads that yield an identifier rather than content. ``type(exc).
#: __name__`` names a class, which is vocabulary the interpreter owns.
IDENTITY_ATTRIBUTES: Final = frozenset({"__name__", "__qualname__"})

#: How many times the backward walk may cross from a parameter to the sites
#: that bind it. MEASURED: the deepest live chain is two - a ``UsmapFormatError``
#: field name is a parameter of ``_take``, bound from a parameter of ``u32``,
#: bound from a literal at the reader's caller. The budget is set above the
#: measured depth so a tree that grows one more hop is still graded, and
#: exhausting it is UNPROVEN rather than proven.
REACH_HOPS: Final = 4

#: The class defines, or inherits from a shipped base, an ``__init__`` that
#: builds the message.
SHAPE_STRUCTURED: Final = "structured"

#: No shipped ancestor defines ``__init__``, so every construction site builds
#: the message itself.
SHAPE_FREE_TEXT: Final = "free-text"

#: Free text with no construction site anywhere in the shipped tree. There is
#: no message-building path to read, which is NOT the same as a clean one.
SHAPE_UNRAISED: Final = "unraised"

#: A constant, a module-level name bound to one, or an identifier attribute.
PROVEN_LITERAL: Final = "proven-literal"

#: An annotation whose value space is numbers and flags, or a measure reducer.
PROVEN_SCALAR: Final = "proven-scalar"

#: Narrowed to a module-level closed vocabulary before the message is built.
PROVEN_VOCABULARY: Final = "proven-vocabulary"

#: Every site in the shipped tree binds it to a proven expression.
PROVEN_AT_SITES: Final = "proven-at-sites"

#: Nothing in the shipped tree proves what this channel can carry.
UNPROVEN: Final = "unproven"

#: The four proofs, weakest last. Order is load-bearing: a channel resolving to
#: several sources takes the WEAKEST verdict among them, because a proof over
#: several sources is only as strong as its worst one.
PROOF_ORDER: Final = (PROVEN_LITERAL, PROVEN_SCALAR, PROVEN_VOCABULARY, PROVEN_AT_SITES, UNPROVEN)

#: Channels the four proof forms cannot clear, each with the reason and where
#: it was measured. EVERY ENTRY WAS CHECKED AT ITS OWN SITES.
#:
#: THE KEY IS THE SOURCE EXPRESSION, NOT THE CLASS. A per-class exemption would
#: forgive every channel the class ever grows; keying on the expression as
#: written means a new channel in an already-exempted class is a new key with
#: no entry, and reddens. It also means REMOVING a redaction wrapper renames the
#: channel - ``locate.redact(destination)`` becomes ``destination`` - so the
#: exemption stops covering it and the arm goes red, which is the property that
#: makes recording a mitigation safe.
#:
#: Reasons cite only identifiers declared in the module the key names, because
#: that is what ``test_every_identifier_an_exemption_cites_exists_in_the_module
#: _it_names`` can check. Cross-module evidence goes in this docstring instead.
EXEMPT: Final[Mapping[str, str]] = {
    "clockspeed/save/header.py::HeaderReadError::self.redacted_path": (
        "MEASURED at the one construction site, in read_header: the argument "
        "is redact(target) and the initialiser applies redact a SECOND time "
        "before building the message, so what reaches args has been through "
        "the project's single redactor twice and the underlying OSError is "
        "dropped with from None rather than chained. REDACTION IS A "
        "MITIGATION, NOT A PROOF - its needles are built from one machine's "
        "resolved home, account and save-root spellings, so no static rule "
        "can read what it covers, which is why this is recorded rather than "
        "cleared. What the guard still holds is the SHAPE: drop the wrapper "
        "and the channel is renamed to the bare path, an unexempted key."
    ),
    "clockspeed/save/usmap.py::UsmapError::redact(path)": (
        "MEASURED at the one construction site, in load_usmap: the path is "
        "the property mapping inside the GAME INSTALL rather than a save - "
        "default_usmap_path resolves it under the install directory - and it "
        "reaches the message only through the project's single redactor. An "
        "install path is not personal data on its own, but it can carry a "
        "home directory when the operator installed the game under one, which "
        "is what the redactor is there for. Recorded rather than cleared for "
        "the reason given on the HeaderReadError entry."
    ),
    "clockspeed/save/workdir.py::DestinationRefusedError::locate.redact(destination)": (
        "MEASURED at the site in _refuse_if_forbidden that fires when "
        "_resolved returns None: the destination is a caller-supplied "
        "directory that would not resolve, rendered only through the "
        "redactor. Recorded rather than cleared because redaction is a "
        "mitigation whose coverage is a property of one machine."
    ),
    "clockspeed/save/workdir.py::DestinationRefusedError::locate.redact(resolved)": (
        "MEASURED at the two remaining sites in _refuse_if_forbidden - the "
        "unresolvable-root refusal and the inside-a-forbidden-root refusal. "
        "Both render the RESOLVED destination through the redactor and "
        "nothing else. The resolved form is the one that can carry a home "
        "directory, which is exactly why the wrapper is there."
    ),
    "clockspeed/save/workdir.py::DestinationRefusedError::root.label": (
        "MEASURED at _forbidden_roots, the ONLY producer of a ForbiddenRoot "
        "in this module: label is one of LABEL_SAVE_ROOT, LABEL_ACCOUNT_DIR "
        "and LABEL_GAME_INSTALL, three module constants, and root.resolved is "
        "deliberately NOT rendered beside it. The guard cannot prove that "
        "statically because the value arrives by iterating a returned list, "
        "which is flow this syntactic rule does not model - so the sibling "
        "arm walks the ForbiddenRoot construction sites and measures it."
    ),
    "clockspeed/save/workdir.py::SourceUnreadableError::exc.errno": (
        "MEASURED at the two sites in copy_for_read and _readable_source: exc "
        "is bound by an except OSError handler and errno is the integer error "
        "number, rendered beside type(exc).__name__ and nothing else. The "
        "OSError's own message - which quotes the filename, and a save "
        "filename embeds the world name - is deliberately never rendered. An "
        "attribute read carries no annotation, so the integer cannot be "
        "proven the way a declared int parameter is; the sibling arm measures "
        "the type at runtime instead."
    ),
    "clockspeed/save/workdir.py::SourceUnreadableError::locate.redact(resolved)": (
        "MEASURED at the two sites in _readable_source: the resolved source "
        "path reaches the message only through the redactor. Recorded rather "
        "than cleared for the reason given on the HeaderReadError entry."
    ),
    "clockspeed/save/workdir.py::SourceUnreadableError::locate.redact(resolved_source)": (
        "MEASURED at the site in copy_for_read: the resolved source path "
        "reaches the message only through the redactor, beside "
        "type(exc).__name__ and an errno. Recorded rather than cleared for "
        "the reason given on the HeaderReadError entry."
    ),
    "clockspeed/save/workdir.py::WorkDirError::exc.errno": (
        "MEASURED at the two sites in _make_dir and copy_for_read: exc is "
        "bound by an except OSError handler and errno is the integer error "
        "number. Same shape and same reasoning as the SourceUnreadableError "
        "entry above, including that the OSError message is never rendered."
    ),
    "clockspeed/save/workdir.py::WorkDirError::locate.redact(destination)": (
        "MEASURED at the site in copy_for_read that reports a failed rename: "
        "the destination inside the work directory reaches the message only "
        "through the redactor. Recorded rather than cleared for the reason "
        "given on the HeaderReadError entry."
    ),
    "clockspeed/save/workdir.py::WorkDirError::locate.redact(path)": (
        "MEASURED at the site in _make_dir: the work directory path reaches "
        "the message only through the redactor. The work root is derived from "
        "work_root and sits outside the save library, but it is still an "
        "absolute path on this machine. Recorded rather than cleared for the "
        "reason given on the HeaderReadError entry."
    ),
}


@dataclass(frozen=True)
class Channel:
    """One rendering channel of one shipped error class.

    Attributes:
        module: Repo-relative path of the module declaring the class.
        class_name: The class.
        lineno: Where the class is declared.
        shape: :data:`SHAPE_STRUCTURED`, :data:`SHAPE_FREE_TEXT` or
            :data:`SHAPE_UNRAISED`.
        channel: The source expression that reaches ``args``, as written.
        verdict: One of :data:`PROOF_ORDER`.
        governed_by: ``<module>::<ClassName>`` of the initialiser that governs
            this channel, or the class itself when it builds its own message.
    """

    module: str
    class_name: str
    lineno: int
    shape: str
    channel: str
    verdict: str
    governed_by: str

    @property
    def key(self) -> str:
        """The :data:`EXEMPT` key for this channel.

        Returns:
            ``<module>::<ClassName>::<channel>``.
        """
        return f"{self.module}::{self.class_name}::{self.channel}"

    @property
    def class_key(self) -> str:
        """The class this channel belongs to.

        Returns:
            ``<module>::<ClassName>``.
        """
        return f"{self.module}::{self.class_name}"


#: A function of either colour. ``ast.AsyncFunctionDef`` is not a subclass of
#: ``ast.FunctionDef``, and a walk that forgets it covers half its population
#: while reporting a count for all of it.
_ANY_FUNCTION: Final = (ast.FunctionDef, ast.AsyncFunctionDef)

_Function = ast.FunctionDef | ast.AsyncFunctionDef
_Site = tuple[str, ast.Call, _Function | None]


class Index:
    """Every shipped module, parsed, with the maps the three rules read.

    Built from SOURCE TEXT rather than from a path so a synthetic corpus is
    graded by exactly the same code as the live tree. The proof arms in
    ``tests/test_exception_messages.py`` author their own corpora precisely so
    that repairing the live tree cannot turn them red.
    """

    def __init__(self, sources: Mapping[str, str]) -> None:
        """Parse the sources and derive the maps.

        Args:
            sources: Repo-relative module path to module text.
        """
        self.modules: dict[str, ast.Module] = {}
        self.classes: dict[str, tuple[str, ast.ClassDef]] = {}
        self.functions: dict[str, list[tuple[str, _Function]]] = {}
        self.calls: dict[str, list[_Site]] = {}
        self.literals: dict[str, frozenset[str]] = {}
        self.vocabularies: dict[str, frozenset[str]] = {}
        self.owner_of: dict[int, str] = {}
        self.resolved: set[str] = set()
        self._narrower: dict[int, bool] = {}
        self._builder: dict[int, bool] = {}
        for module, text in sources.items():
            tree = _parse(text)
            if tree is None:
                continue
            self.modules[module] = tree
            self.literals[module], self.vocabularies[module] = _module_names(tree)
            self._collect(module, tree)

    def _collect(self, module: str, tree: ast.Module) -> None:
        """Record every class, function and call in one module.

        Args:
            module: Repo-relative path.
            tree: The parsed module.
        """
        stack: list[_Function] = []

        def visit(node: ast.AST, owner: str | None) -> None:
            here = owner
            if isinstance(node, ast.ClassDef):
                self.classes[node.name] = (module, node)
                here = node.name
            if isinstance(node, _ANY_FUNCTION):
                self.functions.setdefault(node.name, []).append((module, node))
                if owner is not None:
                    self.owner_of[id(node)] = owner
                stack.append(node)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.Call) and (word := _callee(child)) is not None:
                    self.calls.setdefault(word, []).append(
                        (module, child, stack[-1] if stack else None)
                    )
                visit(child, here if isinstance(node, ast.ClassDef) else owner)
            if isinstance(node, _ANY_FUNCTION):
                stack.pop()

        visit(tree, None)


def build_index(sources: Mapping[str, str]) -> Index:
    """Build an index over module text.

    Args:
        sources: Repo-relative module path to module text.

    Returns:
        The index.
    """
    return Index(sources)


@cache
def live_index() -> Index:
    """Build the index over the shipped tree.

    Returns:
        The index.

    Raises:
        RuntimeError: When no shipped module could be read. An empty sweep and
            a clean one must not look alike.
    """
    sources: dict[str, str] = {}
    for relative in tracked_python_files():
        if not relative.startswith(SHIPPED_ROOT):
            continue
        try:
            sources[relative] = (REPO_ROOT / Path(relative)).read_text(encoding="utf-8")
        except OSError:
            continue
    if not sources:
        raise RuntimeError("no shipped module could be read - the sweep is vacuous")
    return Index(sources)


def _parse(text: str) -> ast.Module | None:
    """Parse module text.

    Args:
        text: The source.

    Returns:
        The tree, or None when it does not parse.
    """
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _callee(call: ast.Call) -> str | None:
    """The name a call names, whether plain or attribute.

    Args:
        call: The call.

    Returns:
        The word, or None.
    """
    return getattr(call.func, "id", None) or getattr(call.func, "attr", None)


def _base_words(node: ast.ClassDef) -> tuple[str, ...]:
    """The base names a class declares.

    Args:
        node: The class.

    Returns:
        One word per base it was possible to name.
    """
    return tuple(
        word
        for base in node.bases
        if (word := getattr(base, "id", None) or getattr(base, "attr", None))
    )


def _module_names(tree: ast.Module) -> tuple[frozenset[str], frozenset[str]]:
    """Module-level names bound to a literal, and to a closed string vocabulary.

    Args:
        tree: The parsed module.

    Returns:
        The literal names, and the names bound to a collection whose every
        element is a string literal.
    """
    bindings: list[tuple[str, ast.expr]] = []
    for statement in tree.body:
        target, value = _module_binding(statement)
        if target is not None and value is not None:
            bindings.append((target, value))
    literals = frozenset(target for target, value in bindings if isinstance(value, ast.Constant))
    # TWO PASSES, AND THE SECOND ONE IS NOT COSMETIC. ``FORMAT_REASONS`` in
    # ``clockspeed/save/header.py`` is a frozenset of module-constant NAMES
    # rather than of string literals, so a one-pass rule that demanded literal
    # elements read the header's reason check as no vocabulary at all and
    # graded a live runtime barrier as the weaker call-site proof.
    vocabularies = frozenset(
        target for target, value in bindings if _is_string_collection(value, literals)
    )
    return literals, vocabularies


def _module_binding(statement: ast.stmt) -> tuple[str | None, ast.expr | None]:
    """The single name and value a module-level assignment binds.

    Args:
        statement: The statement.

    Returns:
        The name and the value, or two Nones.
    """
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        return statement.target.id, statement.value
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        first = statement.targets[0]
        if isinstance(first, ast.Name):
            return first.id, statement.value
    return None, None


def _is_string_collection(value: ast.expr, literals: frozenset[str]) -> bool:
    """Whether a value is a non-empty closed collection of authored strings.

    A ``frozenset({...})`` and a ``MappingProxyType({...})`` are read through
    their single argument, which is the spelling this tree uses.

    Args:
        value: The bound expression.
        literals: Module-level names already known to hold a literal.

    Returns:
        True when every element - or every key - is a string constant or a
        module-level name bound to one.
    """
    inner = value.args[0] if isinstance(value, ast.Call) and value.args else value
    elements: list[ast.expr] = []
    if isinstance(inner, ast.Set | ast.List | ast.Tuple):
        elements = list(inner.elts)
    elif isinstance(inner, ast.Dict):
        elements = [key for key in inner.keys if key is not None]
    return bool(elements) and all(
        (isinstance(element, ast.Constant) and isinstance(element.value, str))
        or (isinstance(element, ast.Name) and element.id in literals)
        for element in elements
    )


def _annotation_words(node: ast.expr | None) -> frozenset[str]:
    """Every type word an annotation mentions.

    Args:
        node: The annotation, or None.

    Returns:
        The words, with ``None`` spelled as a word.
    """
    found: set[str] = set()
    if node is None:
        return frozenset()
    for inner in ast.walk(node):
        word = getattr(inner, "id", None) or getattr(inner, "attr", None)
        if word:
            found.add(word)
        if isinstance(inner, ast.Constant) and inner.value is None:
            found.add("None")
    return frozenset(found)


def _parameters(node: _Function) -> dict[str, ast.arg]:
    """Every named parameter of a function.

    Args:
        node: The function.

    Returns:
        Parameter name to its declaration.
    """
    args = node.args
    return {a.arg: a for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}


def _own_init(node: ast.ClassDef) -> _Function | None:
    """The ``__init__`` a class defines in its own body.

    Args:
        node: The class.

    Returns:
        The function, or None.
    """
    for item in node.body:
        if isinstance(item, _ANY_FUNCTION) and item.name == "__init__":
            return item
    return None


def _reaches_args(index: Index, word: str, seen: frozenset[str]) -> bool:
    """Whether a base word reaches ``BaseException`` through shipped classes.

    Args:
        index: The index.
        word: The base name.
        seen: Names already on the walk, so a cycle terminates.

    Returns:
        True when the class renders ``args``.
    """
    if word in ARGS_ROOTS:
        return True
    if word not in index.classes or word in seen:
        return False
    return any(
        _reaches_args(index, base, seen | {word}) for base in _base_words(index.classes[word][1])
    )


def _error_classes(index: Index) -> list[tuple[str, str, ast.ClassDef]]:
    """Every shipped class on the ``args`` rendering channel.

    Args:
        index: The index.

    Returns:
        Module, class name and node, sorted by key.
    """
    found = [
        (module, name, node)
        for name, (module, node) in index.classes.items()
        if any(_reaches_args(index, base, frozenset()) for base in _base_words(node))
    ]
    return sorted(found, key=lambda item: (item[0], item[1]))


def graded_classes(index: Index) -> tuple[str, ...]:
    """Every error class inside the graded layer.

    Args:
        index: The index.

    Returns:
        ``<module>::<ClassName>`` for each, sorted.
    """
    return tuple(
        f"{module}::{name}"
        for module, name, _ in _error_classes(index)
        if module.startswith(GRADED_LAYER)
    )


def ungraded_layers(index: Index) -> tuple[str, ...]:
    """Every error class the walk found ABOVE the graded layer.

    REPORTED RATHER THAN PINNED, and the distinction is deliberate. Their
    message channels are not fed by a save, so grading them is out of scope -
    but a walk that found none of them and a walk that stopped early return the
    same empty tuple, so the reach is measured instead of assumed. Moving a
    save-layer error out of the layer to escape this guard is caught by the
    DEPARTURE half of the population record, not here.

    Args:
        index: The index.

    Returns:
        ``<module>::<ClassName>`` for each, sorted.
    """
    return tuple(
        f"{module}::{name}"
        for module, name, _ in _error_classes(index)
        if not module.startswith(GRADED_LAYER)
    )


def swept_modules(index: Index) -> tuple[str, ...]:
    """Every module the sweep actually reads.

    Args:
        index: The index.

    Returns:
        Repo-relative module paths, sorted.
    """
    return tuple(sorted(index.modules))


def _governing_init(
    index: Index, name: str, seen: frozenset[str]
) -> tuple[str, str, _Function] | None:
    """The ``__init__`` that governs a class's ``args``, resolved through bases.

    Args:
        index: The index.
        name: The class name.
        seen: Names already on the walk.

    Returns:
        Module, owning class and the function, or None when the whole ancestry
        ships none and ``Exception.__init__`` governs instead.
    """
    if name not in index.classes or name in seen:
        return None
    module, node = index.classes[name]
    own = _own_init(node)
    if own is not None:
        return (module, name, own)
    for base in _base_words(node):
        found = _governing_init(index, base, seen | {name})
        if found is not None:
            return found
    return None


def _descends_from(index: Index, name: str, ancestor: str, seen: frozenset[str]) -> bool:
    """Whether one shipped class descends from another.

    Args:
        index: The index.
        name: The candidate.
        ancestor: The class it may descend from.
        seen: Names already on the walk.

    Returns:
        True when it does, including when the two are the same class.
    """
    if name == ancestor:
        return True
    if name not in index.classes or name in seen:
        return False
    return any(
        _descends_from(index, base, ancestor, seen | {name})
        for base in _base_words(index.classes[name][1])
    )


def _construction_sites(index: Index, name: str) -> list[_Site]:
    """Every site in the shipped tree that builds this class or a subclass.

    Args:
        index: The index.
        name: The class name.

    Returns:
        The call sites.
    """
    found: list[_Site] = []
    for other in index.classes:
        if _descends_from(index, other, name, frozenset()):
            found.extend(index.calls.get(other, []))
    return found


def _narrow_target(
    statement: ast.AST, names: frozenset[str], vocabularies: frozenset[str]
) -> str | None:
    """The parameter a guard clause narrows to a closed vocabulary.

    Reads the SHAPE - ``if <name> not in <MODULE_COLLECTION>: raise`` - so the
    proof comes from the check and never from the helper's name.

    Args:
        statement: The candidate statement.
        names: Parameter names in scope.
        vocabularies: Module-level names bound to a closed string collection.

    Returns:
        The narrowed parameter, or None.
    """
    if not isinstance(statement, ast.If) or not isinstance(statement.test, ast.Compare):
        return None
    test = statement.test
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.NotIn):
        return None
    if not isinstance(test.left, ast.Name) or test.left.id not in names:
        return None
    right = test.comparators[0]
    word = getattr(right, "id", None) or getattr(right, "attr", None)
    if word not in vocabularies:
        return None
    if not any(isinstance(inner, ast.Raise) for inner in ast.walk(statement)):
        return None
    return test.left.id


def _narrowed_parameters(index: Index, module: str, node: _Function) -> frozenset[str]:
    """Every parameter a function narrows to a closed vocabulary.

    Args:
        index: The index.
        module: The module the function is declared in.
        node: The function.

    Returns:
        The parameter names.
    """
    names = frozenset(_parameters(node))
    vocabularies = index.vocabularies.get(module, frozenset())
    found = {
        target
        for statement in ast.walk(node)
        if (target := _narrow_target(statement, names, vocabularies)) is not None
    }
    return frozenset(found)


def _is_narrower(index: Index, module: str, node: _Function) -> bool:
    """Whether a function returns a parameter it narrowed to a vocabulary.

    Args:
        index: The index.
        module: The module the function is declared in.
        node: The function.

    Returns:
        True when a narrowed parameter is what the function hands back.
    """
    cached = index._narrower.get(id(node))  # noqa: SLF001
    if cached is not None:
        return cached
    returned = {
        statement.value.id
        for statement in ast.walk(node)
        if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Name)
    }
    verdict = bool(_narrowed_parameters(index, module, node) & returned)
    index._narrower[id(node)] = verdict  # noqa: SLF001
    return verdict


def _returned(node: _Function) -> list[ast.expr]:
    """Every value a function returns.

    Args:
        node: The function.

    Returns:
        The returned expressions.
    """
    return [
        statement.value
        for statement in ast.walk(node)
        if isinstance(statement, ast.Return) and statement.value is not None
    ]


def _builds_a_message(index: Index, module: str, node: _Function) -> bool:
    """Whether a function composes its returns from its own inputs alone.

    THE DERIVATION OF A MESSAGE BUILDER, and it is structural rather than
    nominal. A builder's returned values decompose into its own parameters,
    module literals, constants and measure reducers over those - nothing else.
    A helper that substitutes over module state, as the project's redactor
    does, fails here and is graded as an opaque channel instead of walked into.

    Args:
        index: The index.
        module: The module the function is declared in.
        node: The function.

    Returns:
        True when the function may be descended into.
    """
    cached = index._builder.get(id(node))  # noqa: SLF001
    if cached is not None:
        return cached
    frame = _Frame(index, module, node, None, {})
    parameters = frozenset(_parameters(node))
    literals = index.literals.get(module, frozenset())
    verdict = True
    for value in _returned(node):
        for part in _compose(value, frame, 0):
            if not _is_simple_part(part[0], parameters, literals):
                verdict = False
                break
        if not verdict:
            break
    index._builder[id(node)] = verdict  # noqa: SLF001
    return verdict


def _is_simple_part(node: ast.expr, parameters: frozenset[str], literals: frozenset[str]) -> bool:
    """Whether one composed part is an input of the function it sits in.

    Args:
        node: The part.
        parameters: The enclosing function's parameter names.
        literals: Module-level literal names.

    Returns:
        True for a constant, an own parameter, a module literal or a measure
        reducer over any of those.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Name):
        return node.id in parameters or node.id in literals
    if isinstance(node, ast.Compare | ast.BoolOp | ast.UnaryOp):
        return True
    if isinstance(node, ast.Call):
        return _callee(node) in MEASURE_REDUCERS
    return isinstance(node, ast.Attribute) and node.attr in IDENTITY_ATTRIBUTES


@dataclass(frozen=True)
class _Frame:
    """Where one expression is being read.

    Attributes:
        index: The index.
        module: Repo-relative path of the module the expression sits in.
        scope: The function enclosing it, or None at module level.
        owner: The class name when ``scope`` is that class's ``__init__``.
        binds: Parameter name to the caller's expression and frame, filled in
            when a message builder is descended into.
        resolving: Names already being followed in this scope. A local
            reassigned from itself - ``out = re.sub(..., out)`` in the
            project's redactor is the live one - resolves forever without it,
            and the recursion is silent until the interpreter's own limit.
    """

    index: Index
    module: str
    scope: _Function | None
    owner: str | None
    binds: Mapping[str, tuple[ast.expr, _Frame]]
    resolving: frozenset[tuple[int, str]] = frozenset()

    def entered(self, name: str) -> _Frame:
        """This frame with one more name recorded as being followed.

        Args:
            name: The name being resolved.

        Returns:
            The new frame.
        """
        return _Frame(
            self.index,
            self.module,
            self.scope,
            self.owner,
            self.binds,
            self.resolving | {(id(self.scope), name)},
        )

    def following(self, name: str) -> bool:
        """Whether this name is already being followed in this scope.

        Args:
            name: The name being resolved.

        Returns:
            True when following it again would cycle.
        """
        return (id(self.scope), name) in self.resolving

    def local_sources(self, name: str) -> list[ast.expr]:
        """Every expression assigned to a local, including appended ones.

        A message helper builds a list and appends to it, so reading only the
        first assignment would grade the opening line and none of the parts
        added after it.

        Args:
            name: The local name.

        Returns:
            The expressions.
        """
        return _sources_for(self.scope, name, attribute=False)

    def attribute_sources(self, name: str) -> list[ast.expr]:
        """Every expression assigned to ``self.<name>`` in this scope.

        Args:
            name: The attribute name.

        Returns:
            The expressions.
        """
        return _sources_for(self.scope, name, attribute=True)


def _sources_for(scope: _Function | None, name: str, *, attribute: bool) -> list[ast.expr]:
    """Every expression bound to one name inside a scope.

    Args:
        scope: The function, or None.
        name: The name or attribute.
        attribute: Read ``self.<name>`` rather than a plain local.

    Returns:
        The assigned and appended expressions, in source order.
    """
    if scope is None:
        return []
    found: list[ast.expr] = []
    for statement in ast.walk(scope):
        found.extend(_assigned_here(statement, name, attribute=attribute))
        if not attribute:
            found.extend(_extended_here(statement, name))
    return found


def _assigned_here(statement: ast.AST, name: str, *, attribute: bool) -> list[ast.expr]:
    """The value one statement assigns to a name.

    Args:
        statement: The statement.
        name: The name or attribute.
        attribute: Read ``self.<name>`` rather than a plain local.

    Returns:
        A single-element list, or an empty one.
    """
    if isinstance(statement, ast.AnnAssign) and statement.value is not None:
        return [statement.value] if _binds(statement.target, name, attribute=attribute) else []
    if isinstance(statement, ast.Assign) and any(
        _binds(target, name, attribute=attribute) for target in statement.targets
    ):
        return [statement.value]
    return []


def _binds(target: ast.expr, name: str, *, attribute: bool) -> bool:
    """Whether an assignment target names the value being resolved.

    Args:
        target: The target expression.
        name: The name or attribute.
        attribute: Read ``self.<name>`` rather than a plain local.

    Returns:
        True when it binds.
    """
    if attribute:
        return isinstance(target, ast.Attribute) and target.attr == name
    return isinstance(target, ast.Name) and target.id == name


def _extended_here(statement: ast.AST, name: str) -> list[ast.expr]:
    """The values one statement appends or extends onto a local list.

    Args:
        statement: The statement.
        name: The local name.

    Returns:
        The appended expressions.
    """
    if isinstance(statement, ast.AugAssign) and _binds(statement.target, name, attribute=False):
        return [statement.value]
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return []
    call = statement.value
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr not in {"append", "extend"}:
        return []
    if not isinstance(func.value, ast.Name) or func.value.id != name:
        return []
    return list(call.args)


def _compose(node: ast.expr, frame: _Frame, hops: int) -> list[tuple[ast.expr, _Frame]]:
    """Split one expression into the channels it renders.

    Args:
        node: The expression.
        frame: Where it is read.
        hops: Remaining budget for descending a message builder.

    Returns:
        One pair per channel. A channel that composes nothing - a bare
        constant - yields nothing at all.
    """
    if isinstance(node, ast.Constant):
        return []
    if isinstance(node, ast.Call):
        return _compose_call(node, frame, hops)
    if isinstance(node, ast.Name):
        return _compose_name(node, frame, hops)
    parts = _composed_parts(node)
    if parts is None:
        return [(node, frame)]
    return [pair for part in parts for pair in _compose(part, frame, hops)]


def _composed_parts(node: ast.expr) -> list[ast.expr] | None:
    """The sub-expressions a purely compositional node renders.

    Args:
        node: The expression.

    Returns:
        The parts, or None when the node is not a composition and is therefore
        a channel in its own right.
    """
    if isinstance(node, ast.JoinedStr):
        return [value.value for value in node.values if isinstance(value, ast.FormattedValue)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return [node.left, node.right]
    if isinstance(node, ast.IfExp):
        # The TEST is consumed and never rendered; a BRANCH is what gets shown.
        return [node.body, node.orelse]
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return list(node.elts)
    return None


def _compose_name(node: ast.Name, frame: _Frame, hops: int) -> list[tuple[ast.expr, _Frame]]:
    """Split a name into the channels the value behind it renders.

    A LOCAL IS NOT A CHANNEL, IT IS A HOLDER, and reading it as one hides
    everything it holds. A message helper builds ``parts``, appends to it and
    joins it; an initialiser builds ``message`` and appends a clause. Stopping
    at the name would report ``parts`` and grade nothing inside it.

    Args:
        node: The name.
        frame: Where it is read.
        hops: Remaining budget for descending a message builder.

    Returns:
        One pair per channel, or the name itself when it holds nothing this
        walk can follow.
    """
    if node.id in frame.binds:
        bound, outer = frame.binds[node.id]
        return _compose(bound, outer, hops)
    if frame.following(node.id):
        # A SELF-REFERENCE CONTRIBUTES NOTHING NEW. ``message += f" ({errno})"``
        # and ``out = re.sub(..., out)`` both name the value being built, and
        # everything it already holds is enumerated by its other sources. The
        # first draft returned the bare name here, which graded a live class on
        # a local called ``message`` and reported it unproven - a finding about
        # the walk rather than about the code.
        return []
    if frame.scope is None:
        return [(node, frame)]
    if node.id in _parameters(frame.scope):
        return [(node, frame)]
    sources = frame.local_sources(node.id)
    if not sources:
        return [(node, frame)]
    inner = frame.entered(node.id)
    return [part for source in sources for part in _compose(source, inner, hops)]


def _compose_call(node: ast.Call, frame: _Frame, hops: int) -> list[tuple[ast.expr, _Frame]]:
    """Split a call into the channels it renders.

    Args:
        node: The call.
        frame: Where it is read.
        hops: Remaining budget for descending a message builder.

    Returns:
        One pair per channel.
    """
    word = _callee(node)
    if word in MEASURE_REDUCERS:
        return [(node, frame)]
    if word in COMPOSING_CALLS:
        parts = [part for arg in node.args for part in _compose(arg, frame, hops)]
        if isinstance(node.func, ast.Attribute):
            parts.extend(_compose(node.func.value, frame, hops))
        return parts
    if hops >= REACH_HOPS:
        return [(node, frame)]
    for module, target in frame.index.functions.get(word or "", []):
        if _is_narrower(frame.index, module, target):
            frame.index.resolved.add(target.name)
            return [(node, frame)]
        if not _builds_a_message(frame.index, module, target):
            continue
        frame.index.resolved.add(target.name)
        binds = {
            name: (bound, frame)
            for name in _parameters(target)
            if (bound := _bound_at(node, target, name)) is not None
        }
        inner = _Frame(frame.index, module, target, None, binds)
        return [part for value in _returned(target) for part in _compose(value, inner, hops + 1)]
    return [(node, frame)]


def _bound_at(call: ast.Call, node: _Function, parameter: str) -> ast.expr | None:
    """The expression a call site binds to one parameter.

    Args:
        call: The call site.
        node: The function being called.
        parameter: The parameter name.

    Returns:
        The bound expression, the declared default when the site omits it, or
        None when neither exists.
    """
    for keyword in call.keywords:
        if keyword.arg == parameter:
            return keyword.value
    order = [a.arg for a in (*node.args.posonlyargs, *node.args.args)]
    if parameter in order:
        offset = 1 if order and order[0] in {"self", "cls"} else 0
        index = order.index(parameter) - offset
        if 0 <= index < len(call.args):
            return call.args[index]
    return _default_of(node, parameter)


def _default_of(node: _Function, parameter: str) -> ast.expr | None:
    """The default a function declares for one parameter.

    Args:
        node: The function.
        parameter: The parameter name.

    Returns:
        The default expression, or None.
    """
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    if parameter in [a.arg for a in positional]:
        offset = len(positional) - len(args.defaults)
        index = [a.arg for a in positional].index(parameter) - offset
        if 0 <= index < len(args.defaults):
            return args.defaults[index]
    for candidate, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        if candidate.arg == parameter:
            return default
    return None


def _weakest(verdicts: Sequence[str]) -> str:
    """The weakest verdict among several sources.

    A value with more than one source is only as proven as its worst one.

    Args:
        verdicts: The verdicts.

    Returns:
        The weakest, or :data:`PROVEN_LITERAL` when there are none - a name
        with no source composes nothing into the message.
    """
    if not verdicts:
        return PROVEN_LITERAL
    return max(verdicts, key=PROOF_ORDER.index)


def _verdict(node: ast.expr, frame: _Frame, hops: int) -> str:
    """Grade one channel.

    Args:
        node: The channel expression.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        One of :data:`PROOF_ORDER`.
    """
    if isinstance(node, ast.Constant):
        return PROVEN_LITERAL
    if isinstance(node, ast.Compare | ast.BoolOp | ast.UnaryOp):
        return PROVEN_SCALAR
    if isinstance(node, ast.Name):
        return _verdict_name(node, frame, hops)
    if isinstance(node, ast.Attribute):
        return _verdict_attribute(node, frame, hops)
    if isinstance(node, ast.Call):
        return _verdict_call(node, frame)
    return UNPROVEN


def _verdict_name(node: ast.Name, frame: _Frame, hops: int) -> str:
    """Grade a bare name.

    Args:
        node: The name.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        One of :data:`PROOF_ORDER`.
    """
    if node.id in frame.binds:
        bound, outer = frame.binds[node.id]
        return _weakest(_grade(bound, outer, hops))
    if node.id in frame.index.literals.get(frame.module, frozenset()):
        return PROVEN_LITERAL
    if frame.scope is not None and node.id in _parameters(frame.scope):
        return _verdict_parameter(node.id, frame, hops)
    if frame.following(node.id):
        return UNPROVEN
    sources = frame.local_sources(node.id)
    if sources:
        inner = frame.entered(node.id)
        return _weakest([v for source in sources for v in _grade(source, inner, hops)])
    return UNPROVEN


def _verdict_parameter(name: str, frame: _Frame, hops: int) -> str:
    """Grade a parameter of the function the channel sits in.

    Args:
        name: The parameter name.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        One of :data:`PROOF_ORDER`.
    """
    scope = frame.scope
    if scope is None:
        return UNPROVEN
    words = _annotation_words(_parameters(scope)[name].annotation)
    if words and words <= SCALAR_ANNOTATIONS:
        return PROVEN_SCALAR
    if name in _narrowed_parameters(frame.index, frame.module, scope):
        return PROVEN_VOCABULARY
    return _verdict_at_sites(name, frame, hops)


def _verdict_at_sites(name: str, frame: _Frame, hops: int) -> str:
    """Grade a parameter by every site that binds it.

    Args:
        name: The parameter name.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        :data:`PROVEN_AT_SITES` when every site binds a proven expression,
        :data:`UNPROVEN` when one does not, when there is no site at all, or
        when the budget is spent.
    """
    if hops <= 0:
        return UNPROVEN
    scope = frame.scope
    if scope is None:
        return UNPROVEN
    sites = _origin_sites(frame)
    if not sites:
        return UNPROVEN
    for module, call, holder in sites:
        bound = _bound_at(call, scope, name)
        if bound is None:
            continue
        outer = _Frame(frame.index, module, holder, _owner_for(frame.index, holder), {})
        if _weakest(_grade(bound, outer, hops - 1)) == UNPROVEN:
            return UNPROVEN
    return PROVEN_AT_SITES


def _owner_for(index: Index, node: _Function | None) -> str | None:
    """The class a function is declared in, when it is one.

    Args:
        index: The index.
        node: The function, or None.

    Returns:
        The class name, or None.
    """
    return None if node is None else index.owner_of.get(id(node))


def _origin_sites(frame: _Frame) -> list[_Site]:
    """Every site that can bind the parameters of this frame's function.

    For a governing ``__init__`` those are the CONSTRUCTION sites of its class
    and every subclass; for any other function they are its call sites, matched
    by callee name across the shipped tree.

    Args:
        frame: The frame.

    Returns:
        The sites.
    """
    scope = frame.scope
    if scope is None:
        return []
    if scope.name == "__init__" and frame.owner is not None:
        return _construction_sites(frame.index, frame.owner)
    frame.index.resolved.add(scope.name)
    return list(frame.index.calls.get(scope.name, []))


def _verdict_attribute(node: ast.Attribute, frame: _Frame, hops: int) -> str:
    """Grade an attribute read.

    Args:
        node: The attribute.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        One of :data:`PROOF_ORDER`.
    """
    if node.attr in IDENTITY_ATTRIBUTES:
        return PROVEN_LITERAL
    held = f"self.{node.attr}"
    if isinstance(node.value, ast.Name) and node.value.id == "self" and not frame.following(held):
        sources = frame.attribute_sources(node.attr)
        if sources:
            inner = frame.entered(held)
            return _weakest([v for source in sources for v in _grade(source, inner, hops)])
    return UNPROVEN


def _verdict_call(node: ast.Call, frame: _Frame) -> str:
    """Grade a call that composition did not walk into.

    Args:
        node: The call.
        frame: Where it is read.

    Returns:
        One of :data:`PROOF_ORDER`.
    """
    word = _callee(node)
    if word in MEASURE_REDUCERS:
        return PROVEN_SCALAR
    for module, target in frame.index.functions.get(word or "", []):
        if _is_narrower(frame.index, module, target):
            frame.index.resolved.add(target.name)
            return PROVEN_VOCABULARY
    return UNPROVEN


def resolved_callees(index: Index) -> tuple[str, ...]:
    """Every callee name the walk resolved through during the last scan.

    Args:
        index: The index, after a scan.

    Returns:
        The names, sorted.
    """
    return tuple(sorted(index.resolved))


def ambiguous_callees(index: Index) -> tuple[str, ...]:
    """Resolved names whose shipped definitions do not agree on parameters.

    CALL SITES ARE POOLED BY NAME, WHICH IS A REAL FRAGILITY AND IS MEASURED
    RATHER THAN HOPED AWAY. Two shipped functions sharing a name pool their
    sites, and a positional argument is then bound against ONE of the two
    signatures. While the definitions agree on parameter names that is
    harmless - and ``_render`` and ``_checked_field`` are each declared twice
    in this tree, once per parser layer, with matching signatures. The moment
    they stop agreeing, a positional bind can read the wrong argument and
    prove the wrong expression, so the precondition reddens instead of
    silently degrading.

    Args:
        index: The index, after a scan.

    Returns:
        The names whose definitions disagree, sorted.
    """
    found: list[str] = []
    for name in index.resolved:
        signatures = {tuple(_parameters(node)) for _, node in index.functions.get(name, [])}
        if len(signatures) > 1:
            found.append(name)
    return tuple(sorted(found))


def _grade(node: ast.expr, frame: _Frame, hops: int) -> list[str]:
    """Every verdict one expression contributes.

    Args:
        node: The expression.
        frame: Where it is read.
        hops: Remaining budget for the backward walk.

    Returns:
        One verdict per channel the expression renders.
    """
    return [_verdict(part, part_frame, hops) for part, part_frame in _compose(node, frame, 0)]


def _args_expressions(index: Index, name: str) -> tuple[str, list[tuple[ast.expr, _Frame]]]:
    """The shape of a class's message path, and the expressions reaching ``args``.

    Args:
        index: The index.
        name: The class name.

    Returns:
        The shape word, and one pair per expression that reaches ``args``.
    """
    governing = _governing_init(index, name, frozenset())
    if governing is not None:
        module, owner, node = governing
        frame = _Frame(index, module, node, owner, {})
        return SHAPE_STRUCTURED, [(value, frame) for value in _super_arguments(node)]
    sites = index.calls.get(name, [])
    if not sites:
        return SHAPE_UNRAISED, []
    found: list[tuple[ast.expr, _Frame]] = []
    for module, call, holder in sites:
        frame = _Frame(index, module, holder, _owner_for(index, holder), {})
        found.extend((argument, frame) for argument in call.args)
    return SHAPE_FREE_TEXT, found


def _super_arguments(node: _Function) -> list[ast.expr]:
    """Every argument a ``super().__init__(...)`` call inside a function passes.

    Args:
        node: The initialiser.

    Returns:
        The argument expressions.
    """
    found: list[ast.expr] = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call) or _callee(inner) != "__init__":
            continue
        func = inner.func
        if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Call):
            continue
        if _callee(func.value) == "super":
            found.extend(inner.args)
    return found


def channels_of(index: Index, name: str) -> tuple[Channel, ...]:
    """Every rendering channel of one error class.

    Args:
        index: The index.
        name: The class name.

    Returns:
        One record per channel, deduplicated by channel text and keeping the
        weakest verdict where a channel appears at more than one site.
    """
    module, node = index.classes[name]
    shape, expressions = _args_expressions(index, name)
    governing = _governing_init(index, name, frozenset())
    governed = f"{governing[0]}::{governing[1]}" if governing else f"{module}::{name}"
    verdicts: dict[str, str] = {}
    for expression, frame in expressions:
        for part, part_frame in _compose(expression, frame, 0):
            label = ast.unparse(part)
            verdict = _verdict(part, part_frame, REACH_HOPS)
            verdicts[label] = _weakest([verdicts.get(label, PROVEN_LITERAL), verdict])
    if not verdicts:
        # A CLASS WITH NO CHANNEL STAYS IN THE POPULATION. Its message is a
        # bare constant, or nothing constructs it - both of which are facts
        # worth recording. Dropping it would shrink the census silently, which
        # is exactly the failure the population record exists to catch.
        empty = "<never constructed>" if shape == SHAPE_UNRAISED else "<no channel>"
        verdicts = {empty: PROVEN_LITERAL}
    return tuple(
        Channel(
            module=module,
            class_name=name,
            lineno=node.lineno,
            shape=shape,
            channel=label,
            verdict=verdict,
            governed_by=governed,
        )
        for label, verdict in sorted(verdicts.items())
    )


def scan_channels(index: Index) -> tuple[Channel, ...]:
    """Every channel of every graded error class.

    Args:
        index: The index.

    Returns:
        The records, sorted by key.
    """
    found: list[Channel] = []
    for module, name, _ in _error_classes(index):
        if module.startswith(GRADED_LAYER):
            found.extend(channels_of(index, name))
    return tuple(sorted(found, key=lambda c: c.key))


def findings_in(
    channels: Sequence[Channel], record: Mapping[str, str] | None = None
) -> tuple[Channel, ...]:
    """The unproven channels with no stated exemption.

    Args:
        channels: The records to filter.
        record: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        The findings.
    """
    exempt = EXEMPT if record is None else record
    return tuple(c for c in channels if c.verdict == UNPROVEN and c.key not in exempt)


def stale_exemptions(index: Index, record: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Exemption keys that no longer name an unproven channel.

    Reported rather than asserted. A repair moves a channel out of
    :data:`UNPROVEN`, and failing on that would make the proof require the
    defect.

    TAKES A RECORD SO THE MECHANISM CAN BE GRADED. Reading only the module
    global leaves the arm that consumes this with nothing to assert - a clean
    result on a clean record is also what a reporter that returns nothing
    produces.

    Args:
        index: The index.
        record: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        The keys, sorted.
    """
    needing = {c.key for c in scan_channels(index) if c.verdict == UNPROVEN}
    exempt = EXEMPT if record is None else record
    return tuple(sorted(set(exempt) - needing))


def describe(channels: Sequence[Channel]) -> str:
    """Render channels as a report.

    Args:
        channels: The records.

    Returns:
        One line per record. SOURCE EXPRESSIONS AND VERDICTS ONLY - never a
        runtime value, because this text reaches a failure report.
    """
    if not channels:
        return "none"
    return "\n".join(
        f"{c.module}:{c.lineno} {c.class_name} [{c.shape}, governed by {c.governed_by}]\n"
        f"      {c.channel}  ->  {c.verdict}"
        for c in sorted(channels, key=lambda c: c.key)
    )
