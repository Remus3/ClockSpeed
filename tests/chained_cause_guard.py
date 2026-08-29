"""CS-857 - the CHAINED-CAUSE channel, derived from ``ast.Raise`` on every run.

WHAT THIS GRADES. ``raise Wrapper(...) from exc`` makes the CAUSE's own text
part of the formatted traceback. The wrapper's message can be perfectly
redacted while the cause renders a raw path beside it, on the same failure.
CS-852's guard grades what reaches ``args``; this grades what reaches the
TRACEBACK WITHOUT reaching ``args``, which is why that guard correctly declines
it. ``tests/test_redaction_scope.py`` declares the same channel out of scope in
writing. Nothing said "me" until this module.

THE POPULATION IS FOUR FORMS, AND A ONE-FORM POPULATION IS THE DEFECT THIS
MODULE EXISTS TO AVOID. An adversary escaping a ``.cause``-keyed detector does
not rename anything. They DELETE TWO WORDS, and a ``.cause``-only detector then
reports a SYNTAX-TOKEN COUNT as a population zero:

  ``from exc`` deleted       ``.cause`` is None, so a cause-only walk counts
                             ZERO - and the value still renders, now through
                             ``__context__``. :data:`FORM_IMPLICIT`.
  ``kept = exc; from kept``  ``.cause`` is a ``Name`` the handler does not
                             bind, so the TYPE leg cannot resolve. Graded
                             :data:`UNPROVEN`, never cleared.
  ``from make()``            ``.cause`` is a ``Call``. Same: graded, unproven.
  ``exc.add_note(path)``     invisible to ``.cause`` entirely. Censused
                             separately by :func:`note_sites`.

Every one of the six shapes above was MEASURED to render a synthetic marker,
and ``from None`` measured NOT to, in
``tests/test_chained_cause_census.py``. Those arms are what make the verdicts
below facts about CPython rather than sentences about it.

THE FOUR VERDICTS, AND THE ORDER IS LOAD-BEARING.

  :data:`CLOSED_SUPPRESSED`  ``from None``. The one POSITIVE clearance, and it
                             rests on a STRUCTURAL fact - the interpreter sets
                             ``__suppress_context__`` and prints no chain -
                             rather than on any property of the value.
  :data:`MEASURED_LEAK`      the exception in flight resolves statically to a
                             builtin ``OSError`` subclass, whose ``str()``
                             renders ``filename``. Measured on a shipped path
                             in the CS-857 note.
  :data:`EXEMPT_RECORDED`    :data:`EXEMPT` records a measured reason for this
                             exact site expression.
  :data:`UNPROVEN`           everything else, including every project-defined
                             cause class and every cause this module cannot
                             resolve.

MEASURED_LEAK IS ORDERED BEFORE EXEMPT_RECORDED ON PURPOSE, so an exemption can
only ever silence an :data:`UNPROVEN` site and can NEVER launder a measured
leak. That is stricter than the sibling guards and it is deliberate: the cost is
that a genuinely-safe ``OSError`` site must be closed with ``from None`` rather
than argued away.

THERE IS NO CLEAN VERDICT, AND THAT IS THE POINT. ``redact(str(cause)) ==
str(cause)`` proves only that the redactor found nothing on THIS machine, whose
needles are built from one account's resolved spellings. A negative redaction
result maps to :data:`UNPROVEN`, never to a clearance. A guard that finds no
channel reports nothing and a later reader still goes and looks; a guard that
reports "clean" has issued a CLEARANCE and the next session cites it as
evidence. Where a narrower rule reports more and a broader one proves more,
this module takes the narrower one.

---------------------------------------------------------------------------
WHAT THIS GUARD CANNOT MODEL. Read this before citing any verdict.
---------------------------------------------------------------------------

1. CLASS RESOLUTION IS BY BARE NAME. ``except OSError as exc`` is resolved by
   looking ``OSError`` up in ``builtins``. A module that binds that name itself
   defeats the leg, so :func:`_shadowed` subtracts every builtin name a module
   binds at module level and the site falls to :data:`UNPROVEN`. A name bound
   in an enclosing FUNCTION, or rebound after import, is NOT subtracted and the
   leg would resolve against the builtin it no longer means.

2. A DOTTED HANDLER TYPE IS NEVER RESOLVED. ``except json.JSONDecodeError``
   and ``except tomllib.TOMLDecodeError`` come back :data:`UNPROVEN` rather
   than being followed to their modules. A dotted name that IS an OSError
   subclass - ``socket.error`` is OSError itself - is therefore UNDER-reported
   as unproven rather than reported as a leak.

3. A CAUSE SET IN A THIRD MODULE IS NOT STATICALLY REACHABLE. The type leg
   fires only when the exception in flight IS the handler's own: the implicit,
   bare and suppressed forms by construction, and the explicit form only when
   the cause expression is exactly the handler's bound name. An exception
   stored on an object, returned from a call, or passed in as a parameter is
   unresolved by construction.

4. CALL SITES OUTSIDE THE TRACKED POPULATION ARE UNSWEPT. The sweep is
   ``tests.assertion_rendering_guard.tracked_python_files()``: tracked and
   untracked-but-not-ignored ``*.py``. A gitignored module, a generated one, or
   a dependency is not read at all.

5. THE VERDICT IS ABOUT THE CHANNEL, NOT ABOUT THE VALUE. :data:`MEASURED_LEAK`
   says the traceback renders the cause's ``str()`` and that an ``OSError``'s
   ``str()`` carries ``filename`` when the interpreter set one. It does NOT
   say a personal path reached that site on any given run. Conversely
   :data:`UNPROVEN` does not say a site is safe.

6. ``except*`` IS WALKED AS AN ORDINARY HANDLER. Under ``except*`` the
   exception in flight is an ``ExceptionGroup`` wrapping the named type, so the
   type leg would answer about the member rather than the group. The tracked
   tree contains no ``except*`` today, which is exactly why this is stated
   rather than measured.

7. ONLY ``str()`` IS MODELLED. ``traceback`` renders a final exception line
   with ``str()``. A rendering path that reaches for ``repr()`` discloses more -
   ``repr(UnicodeDecodeError)`` carries the whole decoded operand and its
   ``str()`` does not, MEASURED in the census - and the two :data:`EXEMPT`
   entries below are scoped to ``str()`` for that reason.

8. THE KEY CANNOT SEPARATE TWO IDENTICAL SITES IN ONE FUNCTION. Two raises of
   the SAME class, from the SAME handler type, in the SAME function, chaining
   the SAME expression, produce one key between them. The tracked tree has no
   such pair today - every live key is distinct, which
   ``test_every_site_key_is_distinct`` asserts - and if one ever appears that
   arm goes RED rather than letting one exemption quietly forgive both. The
   line number is deliberately NOT in the key: it would make every key drift on
   any edit above it, which is the dead-citation failure this item was filed
   against. A collision is therefore reported as something to restructure, not
   absorbed.

WHAT AN ADVERSARY WOULD HAVE TO DO TO ESCAPE. Not a rename: every rename in the
table at the top lands in :data:`UNPROVEN`, which is not a clearance. To get a
CLEARANCE they would have to write ``from None`` - which genuinely closes the
channel - or shadow a builtin exception name at module level, which downgrades
a measured leak to unproven and is reported, not cleared. To vanish from the
POPULATION entirely they would have to move the raise outside every handler AND
drop the ``from`` clause, at which point there is no chain to render.
"""

from __future__ import annotations

import ast
import builtins
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Final

from tests.assertion_rendering_guard import REPO_ROOT, tracked_python_files

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

#: ``raise X(...) from exc`` - an explicit ``__cause__``.
FORM_EXPLICIT: Final = "explicit"

#: ``raise X(...) from None`` - ``__suppress_context__`` is set and no chain is
#: printed. The ``ast`` shape is a cause that is ``Constant(None)``, which is
#: NOT the same node as an absent cause and must never be folded into it.
FORM_SUPPRESSED: Final = "suppressed"

#: ``raise X(...)`` lexically inside a handler body - an implicit
#: ``__context__``. THE FORM A CAUSE-ONLY DETECTOR CANNOT SEE.
FORM_IMPLICIT: Final = "implicit"

#: A bare ``raise`` inside a handler body. Not a chain at all: it re-raises the
#: handler's own exception, whose text renders directly. In the population
#: because the channel it opens is the same one.
FORM_BARE: Final = "bare"

#: Every form, in the order :func:`_form_of` decides them.
FORMS: Final = (FORM_EXPLICIT, FORM_SUPPRESSED, FORM_IMPLICIT, FORM_BARE)

#: The exception in flight resolves to a builtin ``OSError`` subclass.
TYPE_OSERROR: Final = "oserror-rooted"

#: It resolves to a builtin exception that is not an ``OSError``.
TYPE_RESOLVED_OTHER: Final = "resolved-other"

#: It does not resolve. NOT a statement that the site is safe - see limit 3 in
#: the module docstring. Every unresolved site is graded :data:`UNPROVEN`.
TYPE_UNRESOLVED: Final = "unresolved"

#: ``from None``. The only positive clearance, and structural.
CLOSED_SUPPRESSED: Final = "closed-suppressed"

#: The cause is a builtin ``OSError`` subclass, whose ``str()`` renders the
#: ``filename`` the interpreter attached.
MEASURED_LEAK: Final = "measured-leak"

#: :data:`EXEMPT` records a measured reason for this exact site expression. The
#: constant is spelled apart from the mapping because the mapping owns the bare
#: name, house style; the VALUE is the word the verdict is reported under.
EXEMPT_RECORDED: Final = "exempt"

#: Nothing in the tree proves what this chain can carry.
UNPROVEN: Final = "unproven"

#: The verdicts, strongest first. :data:`MEASURED_LEAK` PRECEDES
#: :data:`EXEMPT_RECORDED` so an exemption cannot silence a measured leak.
VERDICT_ORDER: Final = (CLOSED_SUPPRESSED, MEASURED_LEAK, EXEMPT_RECORDED, UNPROVEN)

#: Scopes a handler body does not execute in line. A statement inside a nested
#: function runs in ITS frame with its own ``sys.exc_info()``, so it is not this
#: handler's chain. THE SEED IS FILTERED TOO: seeding a walk with an unfiltered
#: ``handler.body`` descends into a ``def`` written directly in the handler
#: while skipping the same ``def`` one level deeper, making the rule depend on
#: nesting depth rather than on scope. Lesson carried from
#: ``tests/test_handler_exception_rendering.py::NESTED_SCOPES``.
NESTED_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

#: Scopes that also contribute a name to a site's qualified name.
_NAMED_SCOPES: Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

#: Placeholders, so that no field is ever empty and every key segment is read
#: as data rather than as an absence.
NO_HANDLER: Final = "<none>"
NO_CAUSE: Final = "<none>"
IMPLICIT_CAUSE: Final = "<context>"
ACTIVE_CAUSE: Final = "<active>"
BARE_RAISE: Final = "<bare>"
MODULE_SCOPE: Final = "<module>"

#: The layer this module GRADES. Everything else in the sweep is derived and
#: reported, never graded - ``scripts/`` and ``tools/`` because they are frozen
#: (``CLAUDE.md`` section 6), ``tests/`` because a guard's own fixtures are not
#: the shipped advice path.
GRADED_LAYER: Final = "clockspeed/"

#: The heading in ``CLAUDE.md`` that owns the frozen-file list. The list itself
#: is PARSED from there rather than restated here: ``CLAUDE.md`` is its single
#: owner and a second copy is a copy that will drift.
FROZEN_HEADING: Final = re.compile(r"^#+\s*6\.\s+Frozen files\s*$", re.MULTILINE)

#: A bullet naming one frozen path.
_FROZEN_BULLET: Final = re.compile(r"^-\s+`([^`]+)`\s*$", re.MULTILINE)

#: Any markdown heading, used to bound the section.
_ANY_HEADING: Final = re.compile(r"^#+\s", re.MULTILINE)


class ChainedCauseDerivationError(RuntimeError):
    """The population could not be derived.

    RAISED RATHER THAN SWALLOWED, and that is the whole reason the class
    exists. A guard that returns an empty tuple when it cannot read the tree
    reports the same output as a guard that read the tree and found nothing,
    and every arm asserting a zero passes. Precedent:
    ``tests/assertion_rendering_guard.py::tracked_python_files``.

    The message carries the REPO-RELATIVE module and the failure's class name
    only. A ``SyntaxError``'s own ``str()`` renders the absolute filename it
    was handed, and an ``OSError``'s renders the path it failed on, so neither
    is interpolated and both are dropped with ``from None`` rather than chained
    (``CLAUDE.md`` non-negotiables 3 and 12).
    """


# ---------------------------------------------------------------------------
# The records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Site:
    """One raise that can render an exception the graded message did not.

    Attributes:
        module: Repo-relative path, forward-slashed by git.
        lineno: The ``ast.Raise`` STATEMENT line. NOT the closing ``) from
            exc`` line, which differs by two or three at half the live sites.
        qualname: Dotted enclosing scope, :data:`MODULE_SCOPE` at module level.
            Part of the key because it survives line drift, and four live sites
            collide on every other segment without it.
        form: One of :data:`FORMS`.
        raised: The raised callee as written, :data:`BARE_RAISE` when there is
            no raised expression.
        cause_expr: THE SOURCE EXPRESSION of the cause, or the placeholder for
            the form. Renaming it - ``exc`` to ``kept`` - renames the key, so an
            exemption stops covering the site and the arm reddens.
        handler_type: The ``except`` clause type as written, or
            :data:`NO_HANDLER`.
        handler_name: The ``as`` binding, empty when the handler binds nothing.
        cause_type: One of :data:`TYPE_OSERROR`, :data:`TYPE_RESOLVED_OTHER`,
            :data:`TYPE_UNRESOLVED`. A TRI-state on purpose: a boolean would be
            False both for "resolved, and not an OSError" and for "could not
            resolve", and reading the second as the first is a clearance this
            module must never issue.
    """

    module: str
    lineno: int
    qualname: str
    form: str
    raised: str
    cause_expr: str
    handler_type: str
    handler_name: str
    cause_type: str

    @property
    def key(self) -> str:
        """The site expression this module is keyed on.

        Returns:
            ``module::qualname::raised::handler_type::cause_expr``.
        """
        return (
            f"{self.module}::{self.qualname}::{self.raised}::{self.handler_type}::{self.cause_expr}"
        )

    @property
    def is_graded(self) -> bool:
        """Whether the site is in :data:`GRADED_LAYER`.

        Returns:
            True for a shipped module, False for a frozen, tool or test one.
        """
        return self.module.startswith(GRADED_LAYER)


@dataclass(frozen=True)
class NoteSite:
    """One place a note is attached to an exception.

    ``__notes__`` render in the traceback under the exception they are attached
    to, and they are INVISIBLE to a ``.cause`` walk, so they are censused
    separately rather than folded into :class:`Site`.

    Attributes:
        module: Repo-relative path.
        lineno: The statement line.
        qualname: Dotted enclosing scope.
        channel: ``add-note`` for an ``add_note`` call, ``notes-attribute``
            for any other touch of ``__notes__``.
        source: The expression as written.
    """

    module: str
    lineno: int
    qualname: str
    channel: str
    source: str


#: An ``exc.add_note(...)`` call.
NOTE_CALL: Final = "add-note"

#: Any other reference to ``__notes__``.
NOTE_ATTRIBUTE: Final = "notes-attribute"


# ---------------------------------------------------------------------------
# EXEMPT - keyed on the SITE EXPRESSION, house style
# ---------------------------------------------------------------------------

#: Sites where the chained cause was MEASURED and the measurement is recorded
#: rather than turned into a proof form.
#:
#: THE KEY IS THE SITE EXPRESSION, NOT THE CLASS. A per-class exemption would
#: forgive every site that class ever grows. Keying on the expression as
#: written means the adversary's rename - ``from exc`` to ``from kept`` - is a
#: new key with no entry, and reddens; so is moving the raise to another
#: function, changing what is caught, or changing what is raised. That is the
#: property which makes recording a mitigation safe.
#:
#: AN ENTRY HERE CAN ONLY EVER SILENCE AN :data:`UNPROVEN` SITE.
#: :data:`VERDICT_ORDER` puts :data:`MEASURED_LEAK` first, so no exemption can
#: launder a measured leak; closing one needs ``from None`` at the site.
#:
#: Both entries below were measured by running the constructor and reading the
#: rendered traceback, not by reading the class. The arms that re-measure them
#: on every run are named in ``tests/test_chained_cause_census.py``.
EXEMPT: Final[Mapping[str, str]] = {
    "clockspeed/data/docs_extract.py::decode_docs_bytes::DocsDecodeError"
    "::UnicodeDecodeError::exc": (
        "MEASURED by decoding a byte string carrying a synthetic marker and "
        "reading traceback.format_exc(): a UnicodeDecodeError's str() renders "
        "the codec, the offending byte, its position and the reason, all "
        "interpreter-generated, and the DECODED OPERAND is absent. The marker "
        "appears in repr() and not in str() nor in the formatted traceback, "
        "which is why this exemption is scoped to str() and why limit 7 in "
        "the module docstring exists. NOT CLEARED, RECORDED: a rendering path "
        "reaching for repr() would disclose the operand, and the operand here "
        "is docs bytes read from the game install rather than from a save."
    ),
    "clockspeed/data/docs_extract.py::_parse_document::DocsStructureError"
    "::json.JSONDecodeError::exc": (
        "MEASURED by parsing a document carrying a synthetic marker and "
        "reading traceback.format_exc(): a JSONDecodeError's str() renders "
        "msg, line, column and character offset, and the DOCUMENT is absent. "
        "The dotted handler type would come back unresolved in any case - "
        "limit 2 in the module docstring - so this entry records what was "
        "measured rather than relying on that silence."
    ),
}


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------


def _shadowed(tree: ast.Module) -> frozenset[str]:
    """Builtin names this module binds itself, so they are not builtins here.

    Args:
        tree: The parsed module.

    Returns:
        The shadowing names. Subtracting these downgrades a site from
        :data:`TYPE_OSERROR` to :data:`TYPE_UNRESOLVED`, which is a move from
        one non-clearance to another and so cannot create a false clearance in
        either direction.
    """
    bound: set[str] = set()
    for node in tree.body:
        if isinstance(node, _NAMED_SCOPES):
            bound.add(node.name)
        elif isinstance(node, ast.Assign):
            bound |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            bound |= {alias.asname or alias.name.split(".")[0] for alias in node.names}
    return frozenset(bound & frozenset(dir(builtins)))


def _resolve_builtin_exception(name: str, shadowed: frozenset[str]) -> type[BaseException] | None:
    """Resolve a bare name to a builtin exception class.

    Args:
        name: The name as written.
        shadowed: Builtin names this module binds itself.

    Returns:
        The class, or None when the name is shadowed, absent from builtins, or
        bound to something that is not an exception class.
    """
    if name in shadowed:
        return None
    found = getattr(builtins, name, None)
    if isinstance(found, type) and issubclass(found, BaseException):
        return found
    return None


def _name_type(node: ast.Name, shadowed: frozenset[str]) -> str:
    """Classify a bare-name ``except`` clause type.

    Args:
        node: The name as written.
        shadowed: Builtin names this module binds itself.

    Returns:
        One of the three ``TYPE_`` constants.
    """
    resolved = _resolve_builtin_exception(node.id, shadowed)
    if resolved is None:
        return TYPE_UNRESOLVED
    return TYPE_OSERROR if issubclass(resolved, OSError) else TYPE_RESOLVED_OTHER


def _tuple_type(node: ast.Tuple, shadowed: frozenset[str]) -> str:
    """Classify a tuple ``except`` clause type by its WORST member.

    ``except (OSError, SubprocessError)`` puts an OSError in flight on one of
    its two paths, and a verdict met by a population's strongest member
    measures nothing about its weakest - the pooled-guard defect.

    Args:
        node: The tuple as written.
        shadowed: Builtin names this module binds itself.

    Returns:
        One of the three ``TYPE_`` constants.
    """
    members = [_type_of(element, shadowed) for element in node.elts]
    if TYPE_OSERROR in members:
        return TYPE_OSERROR
    if not members or TYPE_UNRESOLVED in members:
        return TYPE_UNRESOLVED
    return TYPE_RESOLVED_OTHER


def _type_of(node: ast.expr | None, shadowed: frozenset[str]) -> str:
    """Classify an ``except`` clause type expression.

    A DOTTED NAME IS NEVER FOLLOWED - limit 2 in the module docstring - so
    ``except json.JSONDecodeError`` comes back unresolved rather than being
    resolved through an import this module does not model.

    Args:
        node: The clause type as written, or None for a bare ``except``.
        shadowed: Builtin names this module binds itself.

    Returns:
        One of :data:`TYPE_OSERROR`, :data:`TYPE_RESOLVED_OTHER`,
        :data:`TYPE_UNRESOLVED`.
    """
    if isinstance(node, ast.Tuple):
        return _tuple_type(node, shadowed)
    if isinstance(node, ast.Name):
        return _name_type(node, shadowed)
    return TYPE_UNRESOLVED


def _form_of(node: ast.Raise, handler: ast.ExceptHandler | None) -> str | None:
    """Decide which of :data:`FORMS` a raise is, if any.

    Args:
        node: The raise.
        handler: The innermost handler whose body it sits in, or None.

    Returns:
        The form, or None when the raise opens no chain at all - a plain
        ``raise X(...)`` outside every handler, which is 158 of the 192 raises
        in the tracked tree and is deliberately not in the population.
    """
    if node.cause is not None:
        if isinstance(node.cause, ast.Constant) and node.cause.value is None:
            return FORM_SUPPRESSED
        return FORM_EXPLICIT
    if node.exc is None:
        return FORM_BARE
    return FORM_IMPLICIT if handler is not None else None


def _cause_expression(node: ast.Raise, form: str) -> str:
    """Render the cause channel for a raise.

    Args:
        node: The raise.
        form: Its form.

    Returns:
        The source expression for :data:`FORM_EXPLICIT`, and the form's
        placeholder otherwise.
    """
    if form == FORM_EXPLICIT and node.cause is not None:
        return ast.unparse(node.cause)
    if form == FORM_IMPLICIT:
        return IMPLICIT_CAUSE
    if form == FORM_BARE:
        return ACTIVE_CAUSE
    return NO_CAUSE


def _raised_expression(node: ast.Raise) -> str:
    """Render what is raised.

    Args:
        node: The raise.

    Returns:
        The callee of a constructor call, the expression itself otherwise, and
        :data:`BARE_RAISE` when nothing is raised.
    """
    if node.exc is None:
        return BARE_RAISE
    if isinstance(node.exc, ast.Call):
        return ast.unparse(node.exc.func)
    return ast.unparse(node.exc)


def _in_flight_type(form: str, cause_expr: str, handler_name: str, handler_type: str) -> bool:
    """Whether the exception the traceback renders IS the handler's own.

    The implicit, bare and suppressed forms carry the handler's exception by
    construction. The explicit form does so ONLY when the cause expression is
    exactly the handler's bound name - which is what sends ``from kept`` and
    ``from make()`` to :data:`TYPE_UNRESOLVED` instead of inheriting a verdict
    they have not earned.

    Args:
        form: The site's form.
        cause_expr: The cause channel as written.
        handler_name: The handler's ``as`` binding, empty when unbound.
        handler_type: The handler clause type, :data:`NO_HANDLER` when there is
            no handler.

    Returns:
        True when the handler's clause type describes what will render.
    """
    if handler_type == NO_HANDLER:
        return False
    if form == FORM_EXPLICIT:
        return bool(handler_name) and cause_expr == handler_name
    return True


def _dispatch(
    child: ast.AST, scope: tuple[str, ...], handler: ast.ExceptHandler | None
) -> Iterator[tuple[ast.AST, tuple[str, ...], ast.ExceptHandler | None]]:
    """Route one child, applying the scope filter to it.

    THE HANDLER BODY IS ROUTED THROUGH HERE TOO, AND THAT IS THE WHOLE POINT.
    Iterating ``handler.body`` and recursing directly would descend into a
    ``def`` written at the TOP of a handler body while the same ``def`` one
    level deeper was filtered, making the rule depend on nesting depth rather
    than on scope. That defect was measured on a sibling guard and is recorded
    at ``tests/test_handler_exception_rendering.py::NESTED_SCOPES``; routing
    the seed through the same dispatch as every other child is what closes it.

    Args:
        child: The node to route.
        scope: The enclosing scope path.
        handler: The innermost handler whose body it sits in.

    Yields:
        The node, its scope path, and its active handler, then its descendants.
    """
    if isinstance(child, _NAMED_SCOPES):
        yield child, scope, handler
        yield from _walk(child, (*scope, child.name), None)
    elif isinstance(child, ast.Lambda):
        yield child, scope, handler
        yield from _walk(child, (*scope, "<lambda>"), None)
    elif isinstance(child, ast.ExceptHandler):
        for statement in child.body:
            yield from _dispatch(statement, scope, child)
    else:
        yield child, scope, handler
        yield from _walk(child, scope, handler)


def _walk(
    node: ast.AST, scope: tuple[str, ...], handler: ast.ExceptHandler | None
) -> Iterator[tuple[ast.AST, tuple[str, ...], ast.ExceptHandler | None]]:
    """Yield every node with its scope path and its innermost active handler.

    A nested scope resets the handler to None: the statement runs in ITS frame,
    with its own ``sys.exc_info()``, so it is not this handler's chain. An
    INNER handler replaces an outer one, which is what CPython does to
    ``__context__``. A ``finally`` or ``else`` block keeps the outer handler,
    because it is still executing inside it.

    Args:
        node: The node to descend from.
        scope: The enclosing scope path so far.
        handler: The innermost handler whose body this node sits in.

    Yields:
        Each child node, its scope path, and its active handler.
    """
    for child in ast.iter_child_nodes(node):
        yield from _dispatch(child, scope, handler)


def _parse(module: str, source: str) -> ast.Module:
    """Parse one module, loudly.

    Args:
        module: The repo-relative path, used as the parse filename so that a
            leaked message could only ever carry a relative path.
        source: Its text.

    Returns:
        The parsed tree.

    Raises:
        ChainedCauseDerivationError: It did not parse. Never swallowed: a
            skipped module is a silently smaller population.
    """
    try:
        return ast.parse(source, filename=module)
    except SyntaxError as exc:
        raise ChainedCauseDerivationError(f"{module} did not parse: {type(exc).__name__}") from None


def _module_sites(module: str, tree: ast.Module) -> Iterator[Site]:
    """Derive every on-channel raise in one parsed module.

    Args:
        module: The repo-relative path.
        tree: The parsed module.

    Yields:
        One :class:`Site` per raise that opens a chain.
    """
    shadowed = _shadowed(tree)
    for node, scope, handler in _walk(tree, (), None):
        if not isinstance(node, ast.Raise):
            continue
        form = _form_of(node, handler)
        if form is None:
            continue
        handler_type = NO_HANDLER
        if handler is not None and handler.type is not None:
            handler_type = ast.unparse(handler.type)
        handler_name = (handler.name or "") if handler is not None else ""
        cause_expr = _cause_expression(node, form)
        in_flight = _in_flight_type(form, cause_expr, handler_name, handler_type)
        cause_type = TYPE_UNRESOLVED
        if in_flight and handler is not None:
            cause_type = _type_of(handler.type, shadowed)
        yield Site(
            module=module,
            lineno=node.lineno,
            qualname=".".join(scope) or MODULE_SCOPE,
            form=form,
            raised=_raised_expression(node),
            cause_expr=cause_expr,
            handler_type=handler_type,
            handler_name=handler_name,
            cause_type=cause_type,
        )


def _module_notes(module: str, tree: ast.Module) -> Iterator[NoteSite]:
    """Derive every ``__notes__`` touch in one parsed module.

    Args:
        module: The repo-relative path.
        tree: The parsed module.

    Yields:
        One :class:`NoteSite` per touch.
    """
    for node, scope, _ in _walk(tree, (), None):
        found: ast.expr
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr != "add_note":
                continue
            found, channel = node, NOTE_CALL
        elif isinstance(node, ast.Attribute) and node.attr == "__notes__":
            found, channel = node, NOTE_ATTRIBUTE
        else:
            continue
        yield NoteSite(
            module=module,
            lineno=found.lineno,
            qualname=".".join(scope) or MODULE_SCOPE,
            channel=channel,
            source=ast.unparse(found),
        )


def sites_in_tree(sources: Mapping[str, str]) -> tuple[Site, ...]:
    """Derive the chained-raise population from a mapping of module to source.

    THE ONE DERIVATION. :func:`raise_sites` is this function over the live
    tree, and every behavioural arm in the census is this function over a
    planted synthetic module, so no arm is fitted to what the tree happens to
    contain today.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every on-channel site, ordered by module then line.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    found: list[Site] = []
    for module in sorted(sources):
        found.extend(_module_sites(module, _parse(module, sources[module])))
    return tuple(sorted(found, key=lambda site: (site.module, site.lineno)))


def notes_in_tree(sources: Mapping[str, str]) -> tuple[NoteSite, ...]:
    """Derive the ``__notes__`` census from a mapping of module to source.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every note site, ordered by module then line.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    found: list[NoteSite] = []
    for module in sorted(sources):
        found.extend(_module_notes(module, _parse(module, sources[module])))
    return tuple(sorted(found, key=lambda site: (site.module, site.lineno)))


@cache
def tracked_sources() -> Mapping[str, str]:
    """Read every tracked ``*.py`` in the repo.

    Returns:
        Repo-relative module path to source text.

    Raises:
        ChainedCauseDerivationError: A file could not be read. Never swallowed:
            an unread file is a silently smaller population, and an OSError's
            own message renders the path it failed on, so it is dropped with
            ``from None`` and only the relative path is reported.
        RuntimeError: git is unavailable or reported failure, propagated
            unchanged from ``tests/assertion_rendering_guard.py``.
    """
    sources: dict[str, str] = {}
    for relative in tracked_python_files():
        try:
            sources[relative] = (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ChainedCauseDerivationError(
                f"{relative} could not be read: {type(exc).__name__}"
            ) from None
    return sources


@cache
def raise_sites() -> tuple[Site, ...]:
    """The live chained-raise population, derived on every run.

    Returns:
        Every on-channel site in the tracked tree.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return sites_in_tree(tracked_sources())


@cache
def note_sites() -> tuple[NoteSite, ...]:
    """The live ``__notes__`` census, derived on every run.

    Returns:
        Every note site in the tracked tree.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return notes_in_tree(tracked_sources())


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def classify(site: Site, exempt: Mapping[str, str] = EXEMPT) -> str:
    """Grade one site.

    THERE IS NO CLEAN VERDICT AND NO REDACTION LEG. The only positive clearance
    is :data:`CLOSED_SUPPRESSED`, which rests on the interpreter setting
    ``__suppress_context__`` rather than on any property of the value.

    Args:
        site: The site.
        exempt: The exemption record, injectable so the census can grade the
            reporter on a fabricated record rather than on the live one.

    Returns:
        Exactly one of :data:`VERDICT_ORDER`.
    """
    if site.form == FORM_SUPPRESSED:
        return CLOSED_SUPPRESSED
    if site.cause_type == TYPE_OSERROR:
        return MEASURED_LEAK
    if site.key in exempt:
        return EXEMPT_RECORDED
    return UNPROVEN


def stale_exemptions(sites: Sequence[Site], exempt: Mapping[str, str]) -> tuple[str, ...]:
    """Exemption keys naming no live site.

    Args:
        sites: The derived population.
        exempt: The exemption record.

    Returns:
        The keys with nothing behind them, sorted.
    """
    live = {site.key for site in sites}
    return tuple(sorted(key for key in exempt if key not in live))


# ---------------------------------------------------------------------------
# The frozen list, PARSED from its owner
# ---------------------------------------------------------------------------


def frozen_from_text(text: str) -> tuple[str, ...]:
    """Parse the frozen-file list out of the owning document's text.

    A SEPARATE SEAM FROM :func:`frozen_paths` SO ITS DEFENSIVE BRANCHES CAN BE
    GRADED. Both raises below fire only against a document the live tree does
    not contain, so folding this into the reader left them measured by nothing:
    a mutation deleting the empty-list check SURVIVED the whole census. An
    unexercised defensive branch is the same "nothing was measured" shape the
    rest of this module exists to refuse, one level down.

    Args:
        text: The document's full text.

    Returns:
        The patterns as written, in document order.

    Raises:
        ChainedCauseDerivationError: The section is missing or lists nothing.
            NEVER an empty tuple: a frozen list that silently came back empty
            would let this module grade a frozen file as in scope and ask an
            agent to edit one.
    """
    opened = FROZEN_HEADING.search(text)
    if opened is None:
        raise ChainedCauseDerivationError("CLAUDE.md has no frozen-files section 6 heading")
    rest = text[opened.end() :]
    closing = _ANY_HEADING.search(rest)
    block = rest[: closing.start()] if closing is not None else rest
    listed = tuple(_FROZEN_BULLET.findall(block))
    if not listed:
        raise ChainedCauseDerivationError("CLAUDE.md frozen-files section 6 lists no path")
    return listed


@cache
def frozen_paths() -> tuple[str, ...]:
    """The frozen-file patterns, read from ``CLAUDE.md`` section 6.

    PARSED RATHER THAN RESTATED. ``CLAUDE.md`` owns the list; a second copy in
    this file is a copy that will drift, and a drifted copy would let this
    module grade a frozen file as in scope. If the section is renamed this
    raises, which is the loud direction.

    Returns:
        The patterns as written, in file order.

    Raises:
        ChainedCauseDerivationError: The section is missing or lists nothing.
    """
    return frozen_from_text((REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8", errors="replace"))


def is_frozen(module: str) -> bool:
    """Whether a module is on the frozen list.

    Args:
        module: A repo-relative, forward-slashed path.

    Returns:
        True when it matches a frozen pattern. A trailing ``*`` matches a
        directory's contents; every other pattern is an exact path.
    """
    for pattern in frozen_paths():
        if pattern.endswith("*"):
            if module.startswith(pattern[:-1]):
                return True
        elif module == pattern:
            return True
    return False


def out_of_scope_record(sites: Sequence[Site]) -> tuple[str, ...]:
    """Render the frozen sites as lines, classified but never graded.

    Derived and reported on every run so that a frozen file's chained raises
    stay visible without any agent editing one. ``CLAUDE.md`` section 6 routes
    a frozen-file edit through an adjudicator; this module only reads.

    Args:
        sites: The derived population.

    Returns:
        One line per frozen site, sorted.
    """
    return tuple(
        f"out-of-scope-recorded FROZEN {classify(site)} {site.key} line {site.lineno}"
        for site in sites
        if is_frozen(site.module)
    )
