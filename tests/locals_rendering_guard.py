#!/usr/bin/env python3
"""CS-851 - the locals channel: what the failing frame HOLDS, not what it asserts.

THE CHANNEL, NAMED PRECISELY. pytest's ``-l`` / ``--showlocals`` renders every
local of the failing frame, each with its OWN repr, whatever the assertion said.
So the remedy CS-850 asks for - bind the aggregate to a plain scalar before the
assert, so the rendered expression holds a number - closes that channel and
LEAVES THIS ONE OPEN, because the original binding is still in the frame::

    unexplained = sweep.words    # still a local
    count = len(unexplained)
    assert count == 0            # renders "assert 1 == 0" and nothing else
                                 # ... and, under -l, "unexplained = frozenset({...})"

MEASURED, NOT REASONED. Forcing an arm against the real save library: with
``--tb=long`` and no ``-l``, ZERO save-derived words rendered; with ``-l``, six
of twelve, none of which appears anywhere in that module's own source. Two live
sites were closed on main in session 39 by REMOVING THE BINDING - not by
``del``, because the name is live in the frame until the ``del`` executes and
an assert before it still renders the value. This module is the POPULATION that
finding belongs to.

WHY CS-850 CANNOT ABSORB IT, and this is a boundary rather than a bug in that
guard. Its subject is the sub-expressions of an ASSERTED EXPRESSION. A local
that is never asserted on is invisible to it BY CONSTRUCTION - not by a one-hop
limit and not by an oversight. ``test_the_canonical_shape_is_a_finding_here_and
_not_in_cs850`` asserts BOTH halves against the shipped guard on every run, so
the day CS-850 grows to cover this, that arm says so instead of two modules
quietly grading the same thing.

SEVERITY, STATED HONESTLY RATHER THAN MAXIMALLY. ``addopts`` is ``-ra
--strict-markers --strict-config``; ``-l`` is NOT on by default. The honest
severity is "a routine debugging flag leaks a save-derived word", not "every
failure leaks". It is tier 1 anyway, because CLAUDE.md non-negotiables 11 and 12
forbid the echo regardless of which flag opens it.

WHAT THIS GUARD DOES NOT RE-GRADE, because something else already does.
``tests/conftest.py`` redacts a rendered report at run time, and the docstring
of its ``_redact_report`` names the locals under ``-l`` as one of the channels
``longrepr`` carries - but ``redact_personal_data`` rewrites HOME PATHS and the
ACCOUNT NAME only. A decoded struct word passes straight through it, because
nothing on this machine can enumerate the words a save contains. So the runtime
redactor covers two of the three classes the acceptance names and this static
guard covers the third, and neither is the whole of it. A parameter such as
``tmp_path`` is a local too and IS rendered;
it is left to that redactor and to ``tests/test_tmp_path_privacy.py`` rather
than re-graded here.

THE POPULATION IS DERIVED FROM THE SHIPPED BINDINGS. There is no list of
suspect names. :func:`scan_sources` walks every scope of every module, follows
each binding form in :data:`FOLLOWED_FORMS`, and reports the locals holding an
unmasked read of a withheld field at the moment an ``assert`` in that scope
fails. :func:`shipped_binding_forms` re-derives the census of binding forms the
tree actually ships on every run;
``test_every_binding_form_the_tree_ships_is_a_form_this_module_knows`` grades it
against :data:`KNOWN_FORMS`, so a form arriving that nothing here has an opinion
about is RED, and
``test_every_recorded_form_is_present_or_absent_as_it_declares`` grades it
against :attr:`Recorded.in_tree`, so a form this module claimed the tree did not
ship is RED on the day it arrives.

THE SECOND ARM EXISTS BECAUSE THE FIRST ONE CANNOT CATCH THAT, and the gap was
not hypothetical. ``match-capture`` shipped here recorded as absent - "this tree
contains none" - while the census on the very same run counted the form, and
capture-bearing ``match`` statements sat IN THIS FILE. The first arm could never
redden on it, because a recorded form is inside :data:`KNOWN_FORMS` by
construction. So no presence claim is written in prose any more, and no count of
one either: presence is a MEASURED field on :class:`Recorded`, graded every run
against the census, and the number of occurrences is deliberately not pinned
because it moves on every edit and carries no privacy content.

WHAT IS RECORDED IS NOT THE SAME AS WHAT IS SAFE, and conflating the two is the
error this module shipped with. A recorded form is one the scan does not follow;
whether a local bound that way RENDERS is a separate question with a separate
answer, measured by a real ``pytest -l`` run over
:data:`tests.test_locals_rendering.RECORDED_SOURCES` and pinned in
:attr:`Recorded.renders`. Several recorded forms DO render, and their reasons
say so plainly - which ones is the field rather than a sentence here. An
admitted gap is worth more than an exemption whose reason is false.

WHAT COUNTS AS SAFE, and the standard is the one CS-850 paid 64 per cent false
positives to learn. Only a genuine REDUCTION withholds. ``count =
len(sweep.words)`` is safe; ``shown = sorted(sweep.words)``,
``table = dict(sorted(sweep.tags.items()))`` and ``line = ", ".join(sweep.words)``
are NOT - each renders every element. THE TWO VOCABULARIES ARE IMPORTED RATHER
THAN RESPELT, so the two channels cannot drift into two opinions about the same
wrapper; a second list of the same kind of thing in a second file is CS-433's
defect.

THE WALK ITSELF IS NOT BORROWED, AND THE ONE DIFFERENCE IS THE POINT. :func:`flows_into` decides
whether a read reaches the expression a local is BOUND to; CS-850's
:func:`tests.assertion_rendering_guard._reaches_unmasked` decides whether it reaches an expression
pytest RENDERS. They agree everywhere except at a call's ARGUMENT position: the rewriter reprs a
call's arguments as well as its result, so ``helper(sweep.words)`` renders the words on that channel
whatever ``helper`` returns - while a LOCAL bound from it holds only the result. See
:func:`_argument_carries` for the measurement, and
``test_the_two_channels_agree_except_at_a_call_argument`` for the pin, which runs the borrowed walk
beside this one on every run so a change over there is visible here rather than silent.

THREE SHAPES THAT MUST NOT BE FLAGGED, and this half is load-bearing.

  ``sweep = make_sweep()``      the WHOLE OBJECT. Under ``-l`` this renders the
                                class's own redacting ``__repr__``, which is
                                exactly what it was written for.
  ``n = len(sweep.words)``      the REDUCTION. The frame holds a number.
  ``saves = sweep.saves``       a DISCLOSED field. The class chose to render it,
                                so a local holding it discloses nothing new.

ORDER MATTERS, AND SO DOES THE SECOND ITERATION. A name assigned AFTER the
assert is not in ``frame.f_locals`` when the assert fails, so this walks each
scope in source order rather than collecting a scope's bindings as a set. The
exception is a loop: a binding made LATER in a loop body IS in the frame when
an earlier assert in that body runs again, so the state at the end of a loop
body is carried back onto every assert inside it. Omitting that would
under-report, and under-reporting is the direction that hides a leak.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Final

from tests.assertion_rendering_guard import (
    ANY_FUNCTION,
    CONTENT_REDUCERS,
    CONTENT_TRANSPARENT,
    MACHINE_FIXTURES,
    REPO_ROOT,
    Redacting,
    _parent_map,
    annotation_tail,
    live_functions,
    module_functions,
    must_declare_reach,
    reach_seeds,
    redacting_classes,
    repr_method,
    scope_statements,
    tracked_python_files,
)

#: The label a module-level scope carries in a finding. A module frame's locals
#: ARE its globals, so a module-level assert renders them; a function's frame
#: does not, which is why module-scope bindings are safe from a test's failure
#: and are not merged into any function's state.
MODULE_SCOPE: Final = "<module>"

# ---------------------------------------------------------------------------
# The binding forms. FOLLOWED is what the scan tracks; RECORDED is what it
# deliberately does not, each with the reason. KNOWN is the union, and a form
# outside it is the thing a census is for.
# ---------------------------------------------------------------------------

#: ``words = sweep.words``
ASSIGN: Final = "assign"
#: ``words: frozenset[str] = sweep.words``
ANNOTATED: Final = "annotated-assign"
#: ``first = second = sweep.words`` - one value, several targets.
CHAINED: Final = "chained-assign"
#: ``words, other = sweep.words, None`` - measured on CS-850's channel as the
#: form that walked four assertions past a guard that read only a bare target.
UNPACK: Final = "unpack"
#: ``len(words := sweep.words)`` - bound by the time the comparison fails.
WALRUS: Final = "walrus"
#: ``for word in sweep.words:`` - the target holds ONE decoded word, which is
#: a save-derived name however small.
FOR_TARGET: Final = "for-target"
#: ``with nullcontext(sweep.words) as words:``
WITH_TARGET: Final = "with-target"

#: ``total += sweep.words`` - RECORDED, AND IT LEAKS. The target IS a local and
#: renders every element it accumulated; measured under ``-l``. It is not
#: followed because the target's prior value is not resolvable here, and
#: flagging an unresolved read is the direction that produced CS-850's false
#: tier. An uncovered gap, not a safe shape.
AUGMENTED: Final = "augmented-assign"
#: ``holder["w"] = sweep.words`` - RECORDED, AND IT LEAKS. A subscript target
#: binds no NAME, so nothing here follows it - but the CONTAINER is already a
#: local, and a plain dict or list renders every element it was handed.
#: Measured: ``holder = {'w': frozenset({...})}``. What is missing is mutation
#: tracking on an already-bound container, not a reason to call it safe.
SUBSCRIPT_TARGET: Final = "subscript-target"
#: ``sink.words = sweep.words`` - RECORDED, AND IT LEAKS whenever the holder
#: renders its fields. Same missing mutation tracking as the subscript target.
#: A bare ``class Sink: pass`` reprs as ``<Sink object at 0x...>`` and hides it;
#: a plain ``@dataclass``, which this tree ships, prints every field. Measured
#: on the dataclass, which is the population's shape.
ATTRIBUTE_TARGET: Final = "attribute-target"
#: ``except OSError as exc:`` - RECORDED, AND THE FIXTURE LEAKS - but on a
#: DIFFERENT CHANNEL, which is the only reason it is not this module's. Measured
#: with the assert inside the handler: the marker reaches the report through the
#: ``E ValueError: ...`` line, WITH AND WITHOUT ``-l``, so it is the exception's
#: own rendering rather than the frame's locals. Python deletes the name on the
#: way out of the handler, and an assert after it renders nothing - measured.
#: ``tests/test_exception_rendering.py`` is NOT the hand-off: it is scoped to
#: CS-205, a tracked module rendering a caught exception into a MESSAGE, and
#: contains no occurrence of ``showlocals``, ``f_locals`` or ``show_locals``.
#: Nothing yet grades a handler name on this channel.
EXCEPT_TARGET: Final = "except-target"
#: ``case Sweep(words=w):`` - RECORDED, AND IT LEAKS. A capture target is a
#: plain local and renders in full; measured ``captured = frozenset({...})``.
#: It is not followed because :meth:`_LocalScan.bind_statement` has no
#: ``ast.Match`` branch. THIS FORM SHIPPED HERE RECORDED AS ABSENT while the
#: tree carried capture-bearing ``match`` statements, including ones in this
#: file, so its presence is now a measured field rather than a sentence.
MATCH_CAPTURE: Final = "match-capture"
#: ``[word for word in sweep.words]`` - RECORDED. Python gives a comprehension
#: its OWN frame, so its target is never a local of the asserting frame. This
#: is decidable rather than a judgement call, and measured not to render.
COMPREHENSION_TARGET: Final = "comprehension-target"
#: ``import ast`` - RECORDED. Binds a module or an alias to it. No field read
#: can reach an import target, so the pin is structural and there is nothing to
#: plant in it.
IMPORT: Final = "import"
#: ``def helper(): ...`` / ``class Holder: ...`` - RECORDED. Binds a function
#: or a class, whose repr is its own name. Structural, like the import.
DEFINITION: Final = "definition"
#: ``global TOTAL`` / ``nonlocal seen`` - RECORDED, AND THE TWO HALVES BEHAVE
#: OPPOSITELY, which is why one sentence covering both was wrong. A ``global``
#: target lives in the module namespace and is NOT in the function's frame, so
#: :meth:`_LocalScan._bind` must not record it - measured: a real forced run
#: renders nothing for it. A ``nonlocal`` target IS a cell in the declaring
#: frame and a free variable in the inner one, and pytest renders both - so
#: nothing is suppressed for it and a finding on one is a TRUE positive.
SCOPE_DECLARATION: Final = "scope-declaration"
#: ``type Words = frozenset[str]`` - RECORDED. Binds a ``TypeAliasType`` whose
#: repr is its own name, so no field read can reach the target. Found by
#: sweeping for the SHAPE the ``try`` gap was: a statement kind that binds a
#: name and that the census could not see.
TYPE_ALIAS: Final = "type-alias"
#: ``def test_it(sweep):`` - RECORDED. A parameter IS a local and IS rendered,
#: but it arrives as a WHOLE OBJECT, so the frame prints its own repr - the
#: case CS-850 measured as safe, and measured safe again here. The machine
#: fixtures are covered at render time by ``tests/conftest.py``.
PARAMETER: Final = "parameter"

#: The forms :class:`_LocalScan` actually tracks.
FOLLOWED_FORMS: Final = frozenset(
    {ASSIGN, ANNOTATED, CHAINED, UNPACK, WALRUS, FOR_TARGET, WITH_TARGET}
)


@dataclass(frozen=True)
class Recorded:
    """One binding form the scan does not follow, and what was MEASURED of it.

    EVERY FIELD BUT THE REASON IS GRADED ON EVERY RUN. A boundary written as
    prose is a claim that rots; the version of it that cannot is a value some
    arm compares against a measurement. This module shipped a reason asserting
    an absence the census refuted on the same run, so nothing here states what
    the tree holds or what pytest prints except as a field.

    Attributes:
        reason: Why the scan does not follow the form. Where the form LEAKS,
            the reason says so plainly - an admitted gap rather than an
            exemption, because an exemption whose reason is false is worse
            than no entry at all.
        renders: Whether a local bound by this form from a withheld field is
            printed under ``-l``. Graded by
            ``test_every_recorded_form_renders_exactly_as_it_declares``, which
            runs real pytest over the form's fixture. False for a form whose
            fixture plants nothing because the form CANNOT carry a field read.
        renders_by_default: The same, under the flags this project ships. The
            honest severity split: ``-l`` is a debugging flag, so a form true
            here is a strictly worse finding than one true only above.
        in_tree: Whether the census reports at least one occurrence. A form
            declared absent that ARRIVES is RED; a form declared present that
            leaves is reported and not asserted, because code disappearing is
            not a privacy defect and must not redden a repaired tree.
        plantable: Whether the form's fixture can carry a withheld field at
            all. False makes the two rendering fields structural rather than
            measured, and the grading arm skips it rather than reading its
            silence as evidence.
    """

    reason: str
    renders: bool
    renders_by_default: bool
    in_tree: bool
    plantable: bool = True


#: The forms this module has an opinion about and deliberately does not follow.
#: SEVERAL OF THEM LEAK - the ``renders`` field says which, and it is measured
#: rather than counted here. That is disclosed rather than engineered away:
#: widening the scan to cover them is a design problem, and a guard that says
#: "not covered" is honest where one that says "safe" is not.
RECORDED_FORMS: Final[Mapping[str, Recorded]] = {
    AUGMENTED: Recorded(
        reason=(
            "LEAKS, NOT COVERED: the target is a local and renders every element it "
            "accumulated. Unfollowed because the target's prior value is unresolvable "
            "here and flagging an unresolved read produced CS-850's false tier"
        ),
        renders=True,
        renders_by_default=False,
        in_tree=True,
    ),
    SUBSCRIPT_TARGET: Recorded(
        reason=(
            "LEAKS, NOT COVERED: the subscript binds no name, but the CONTAINER is "
            "already a local and a plain dict renders every element handed to it. "
            "What is missing is mutation tracking on an already-bound container"
        ),
        renders=True,
        renders_by_default=False,
        in_tree=True,
    ),
    ATTRIBUTE_TARGET: Recorded(
        reason=(
            "LEAKS, NOT COVERED, whenever the holder renders its fields - measured on "
            "a plain dataclass, which this tree ships. Same missing mutation tracking. "
            "A bare class hides it behind the default object repr and pins it safe by "
            "accident, which is why the fixture is not written that way"
        ),
        renders=True,
        renders_by_default=False,
        in_tree=True,
    ),
    EXCEPT_TARGET: Recorded(
        reason=(
            "LEAKS ON A DIFFERENT CHANNEL, NOT COVERED HERE, AND THE BINDING IS "
            "NOT WHAT LEAKS. The marker arrives through the exception's own "
            "rendering, with and without -l. MEASURED session 43: deleting the "
            "as-NAME leaves an UNNAMED handler that renders the marker just as "
            "readily, so this row is true of the FIXTURE and false of the FORM - "
            "what renders is chaining, which fires with a bare except. The "
            "genuinely name-keyed mechanism is a frame ARGUMENT, when the binding "
            "is handed to a callee that raises. Both are graded by CS-855 in "
            "tests/test_handler_exception_rendering.py; the earlier hand-off to "
            "tests/test_exception_rendering.py was wrong, that file being scoped "
            "to CS-205 and naming none of showlocals, f_locals or show_locals"
        ),
        renders=True,
        renders_by_default=True,
        in_tree=True,
    ),
    MATCH_CAPTURE: Recorded(
        reason=(
            "LEAKS, NOT COVERED: a capture target is a plain local and renders in "
            "full. Unfollowed because bind_statement has no ast.Match branch. Shipped "
            "here recorded as absent while the tree already carried the form"
        ),
        renders=True,
        renders_by_default=False,
        in_tree=True,
    ),
    COMPREHENSION_TARGET: Recorded(
        reason="a comprehension has its own frame, so it binds no local here",
        renders=False,
        renders_by_default=False,
        in_tree=True,
    ),
    IMPORT: Recorded(
        reason="binds a module or an alias to one; no field read can reach the target",
        renders=False,
        renders_by_default=False,
        in_tree=True,
        plantable=False,
    ),
    DEFINITION: Recorded(
        reason="binds a function or a class, whose repr is its own name",
        renders=False,
        renders_by_default=False,
        in_tree=True,
        plantable=False,
    ),
    SCOPE_DECLARATION: Recorded(
        reason=(
            "a global target lives in the module namespace and is NOT in the "
            "function's frame, so _bind does not record it. A nonlocal target IS "
            "rendered, in the declaring frame and the inner one alike, and nothing "
            "is suppressed for it"
        ),
        renders=False,
        renders_by_default=False,
        in_tree=True,
    ),
    TYPE_ALIAS: Recorded(
        reason="binds a TypeAliasType whose repr is its own name; no field read reaches it",
        renders=False,
        renders_by_default=False,
        in_tree=True,
        plantable=False,
    ),
    PARAMETER: Recorded(
        reason="arrives as a whole object, so the frame prints its own redacting repr",
        renders=False,
        renders_by_default=False,
        in_tree=True,
    ),
}

#: Every form this module can name. A census entry outside this is the signal
#: that the language or the tree grew a binding shape nobody here has graded.
KNOWN_FORMS: Final = FOLLOWED_FORMS | frozenset(RECORDED_FORMS)


@dataclass(frozen=True)
class LocalFinding:
    """One local alive in a failing frame that renders a withheld field.

    Attributes:
        module: Repo-relative path of the asserting file.
        lineno: The line of the assert the local is alive at - the earliest one
            in its scope, so one binding does not count once per assertion.
        scope: The enclosing function's name, or :data:`MODULE_SCOPE`.
        local: The name the frame renders.
        bound_at: The line the binding was made on.
        form: Which member of :data:`FOLLOWED_FORMS` made it.
        holder: The redacting class that withheld the field.
        field: The withheld field name.
        source: The binding expression, unparsed. Repo SOURCE TEXT, never a
            runtime value - nothing in this module reads a value.
        live: True when the holder carries real save or machine data, or when
            the module owed a reach declaration and made none. Latent is a
            claim and has to be earned.
    """

    module: str
    lineno: int
    scope: str
    local: str
    bound_at: int
    form: str
    holder: str
    field: str
    source: str
    live: bool


@dataclass(frozen=True)
class LocalSweep:
    """What one pass over a corpus read, and what it found.

    Attributes:
        modules: How many modules were parsed.
        scopes: How many lexical scopes were walked.
        asserts: How many ``assert`` statements were graded.
        declarations: How many redacting classes with a withheld field the
            corpus declares. Stable under a leak being repaired.
        forms: The binding-form census, form to count.
        findings: The findings.
    """

    modules: int
    scopes: int
    asserts: int
    declarations: int
    forms: Mapping[str, int]
    findings: tuple[LocalFinding, ...]


def describe_locals(findings: Sequence[LocalFinding]) -> str:
    """Render findings as file, line, local name and binding shape.

    Args:
        findings: What to render.

    Returns:
        One indented line each, sorted, carrying source text only.
    """
    lines = sorted(
        f"  {f.module}:{f.bound_at}  in {f.scope}  `{f.local} = {f.source}` "
        f"({f.form}) holds {f.holder}.{f.field} and is still in the frame at "
        f"the assert on line {f.lineno}"
        for f in findings
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The census: which binding forms the tree actually ships
# ---------------------------------------------------------------------------


def _target_form(target: ast.expr) -> str:
    """Which binding form one assignment target is.

    Args:
        target: The target expression.

    Returns:
        A member of :data:`KNOWN_FORMS`.
    """
    match target:
        case ast.Name():
            return ASSIGN
        case ast.Tuple() | ast.List() | ast.Starred():
            return UNPACK
        case ast.Subscript():
            return SUBSCRIPT_TARGET
        case _:
            return ATTRIBUTE_TARGET


def _pattern_captures(stmt: ast.stmt) -> bool:
    """Whether a ``match`` statement captures a name in any pattern.

    Args:
        stmt: The statement.

    Returns:
        True when at least one capture pattern names something.
    """
    for node in ast.walk(stmt):
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
            return True
        if isinstance(node, ast.MatchMapping) and node.rest is not None:
            return True
    return False


def _statement_targets(stmt: ast.stmt) -> list[str]:
    """The binding forms one statement's own TARGETS establish.

    Args:
        stmt: The statement.

    Returns:
        The form labels, possibly several, possibly none.
    """
    forms: list[str]
    match stmt:
        case ast.Assign(targets=targets):
            chained = [CHAINED] if len(targets) > 1 else []
            forms = chained + [_target_form(target) for target in targets]
        case ast.AnnAssign(target=target):
            forms = [ANNOTATED if isinstance(target, ast.Name) else _target_form(target)]
        case ast.AugAssign(target=target):
            forms = [AUGMENTED if isinstance(target, ast.Name) else _target_form(target)]
        case ast.For(target=target) | ast.AsyncFor(target=target):
            forms = [FOR_TARGET if isinstance(target, ast.Name) else _target_form(target)]
        case ast.With(items=items) | ast.AsyncWith(items=items):
            forms = [
                WITH_TARGET
                if isinstance(item.optional_vars, ast.Name)
                else _target_form(item.optional_vars)
                for item in items
                if item.optional_vars is not None
            ]
        case ast.Import() | ast.ImportFrom():
            forms = [IMPORT]
        case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
            forms = [DEFINITION]
        case ast.Global() | ast.Nonlocal():
            forms = [SCOPE_DECLARATION]
        case ast.Match() if _pattern_captures(stmt):
            forms = [MATCH_CAPTURE]
        case ast.Try(handlers=handlers) | ast.TryStar(handlers=handlers):
            # THE HANDLER NAME IS THE ONLY BINDING A ``try`` ESTABLISHES, and it
            # was missing here: no branch matched ``ast.Try``, so ``except E as
            # exc`` was invisible to a census that calls itself exhaustive over
            # statement kinds. A form the census can never see reads as ABSENT
            # for ever, which would have made this module's own arrival check
            # permanently vacuous on it.
            forms = [EXCEPT_TARGET for handler in handlers if handler.name is not None]
        case ast.TypeAlias():
            forms = [TYPE_ALIAS]
        case _:
            forms = []
    return forms


def _statement_expressions(stmt: ast.stmt) -> list[str]:
    """The binding forms one statement's EXPRESSIONS establish.

    Args:
        stmt: The statement.

    Returns:
        The form labels, possibly several, possibly none.
    """
    forms: list[str] = []
    for node in ast.walk(stmt):
        if isinstance(node, ast.NamedExpr):
            forms.append(WALRUS)
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            forms += [COMPREHENSION_TARGET] * len(node.generators)
    return forms


def statement_forms(stmt: ast.stmt) -> list[str]:
    """Every binding form one statement establishes.

    OVER STATEMENT KINDS RATHER THAN OVER THE FORMS THIS MODULE FOLLOWS. A
    census that could only see what the scan already tracks would report a
    clean sheet on a tree full of shapes nobody has graded, which is the
    failure mode of every hand-maintained list this project has retired.

    IT CLAIMED TO BE EXHAUSTIVE AND WAS NOT, which is why the claim is now a
    list instead of an adjective. ``ast.Try`` matched no branch, so ``except E
    as exc`` was invisible however many the tree shipped, and the form it binds
    could only ever read as absent because nothing could count it.
    ``ast.TypeAlias`` was missing the same way. Sweeping for the SHAPE rather
    than re-testing the site is what found the second one.

    WHAT IS STILL NOT COUNTED, disclosed rather than left to be discovered:

      lambda parameters   A lambda binds its parameters in its OWN frame, and a
                          lambda body cannot contain an ``assert`` statement,
                          so that frame is never one of this module's subjects.
      PEP 695 type params ``def f[T]()`` binds ``T`` in a dedicated annotation
                          scope, which likewise holds no assertion.

    Args:
        stmt: The statement.

    Returns:
        The form labels, possibly several, possibly none.
    """
    return _statement_targets(stmt) + _statement_expressions(stmt)


def _scope_forms(scope: ast.AST) -> Iterator[str]:
    """Every binding form one scope establishes, parameters included.

    Args:
        scope: A module or function definition.

    Yields:
        The form labels.
    """
    if isinstance(scope, ANY_FUNCTION):
        yield from [PARAMETER] * len(_parameters(scope))
    for stmt in scope_statements(scope):
        yield from statement_forms(stmt)


def census(trees: Mapping[str, ast.Module]) -> dict[str, int]:
    """The binding-form census over a whole corpus.

    Args:
        trees: Module path to its parsed tree.

    Returns:
        Form label to how many times it occurs.
    """
    counts: dict[str, int] = {}
    for tree in trees.values():
        for scope in _scopes(tree):
            for form in _scope_forms(scope):
                counts[form] = counts.get(form, 0) + 1
    return counts


@cache
def shipped_binding_forms() -> Mapping[str, int]:
    """The binding-form census over every tracked Python file in the repo.

    Called by ``test_every_binding_form_the_tree_ships_is_a_form_this_module
    _knows`` and by ``test_every_recorded_form_is_present_or_absent_as_it
    _declares``, which are the two arms that grade the census.

    Returns:
        Form label to count, read-only. Derived on every run; nothing here is
        listed. The mapping is a view rather than a fresh dict because the
        cache hands the SAME object to every caller, and one caller mutating
        it would silently re-grade the next.
    """
    return MappingProxyType(dict(scan_tree().forms))


# ---------------------------------------------------------------------------
# The residual record's arithmetic
# ---------------------------------------------------------------------------

#: What one accepted residual is keyed by: module, enclosing scope, local name.
#:
#: NOT A COUNT, AND NOT A LINE NUMBER. A per-module COUNT cannot tell "still
#: the same eight sites" from "eight different ones" - repair all eight, plant
#: eight brand-new leaky bindings at brand-new lines under brand-new names, and
#: the ceiling is still met. A LINE NUMBER churns on every edit above it and
#: turns the record into a maintenance tax. The triple moves only when the site
#: itself moves, which is exactly when a human should look at it again.
ResidualKey = tuple[str, str, str]


def residual_key(finding: LocalFinding) -> ResidualKey:
    """The stable identity of the site one finding names.

    Args:
        finding: The finding.

    Returns:
        Its module, scope and local name.
    """
    return (finding.module, finding.scope, finding.local)


def unrecorded_residuals(
    findings: Sequence[LocalFinding], record: Mapping[ResidualKey, str]
) -> list[ResidualKey]:
    """Which live findings the record does not admit.

    MONOTONE IN THE DIRECTION THAT MATTERS: repairing every recorded site
    empties the findings and empties this, so a guard built on it stays green
    on a tree where the defect is absent. Session 39 refuted three items for
    checks that went RED when a leak was fixed.

    Args:
        findings: The live partition of a sweep.
        record: Accepted residual key to the reason it is accepted.

    Returns:
        The keys with no entry, sorted, without repeats.
    """
    return sorted({residual_key(f) for f in findings} - set(record))


def stale_residuals(
    findings: Sequence[LocalFinding], record: Mapping[ResidualKey, str]
) -> list[ResidualKey]:
    """Which recorded residuals no longer name a live finding.

    REPORTED RATHER THAN ASSERTED, and that is a decision rather than an
    omission. Reddening here would mean the day somebody REPAIRS a recorded
    site this module goes red - the anti-monotone shape the fence forbids, and
    the reason the previous record only asserted one way. The staleness is
    still worth naming, so it is named, with the exact entry to delete.

    Args:
        findings: The live partition of a sweep.
        record: Accepted residual key to the reason it is accepted.

    Returns:
        The recorded keys nothing found, sorted.
    """
    return sorted(set(record) - {residual_key(f) for f in findings})


def describe_residual_keys(keys: Sequence[ResidualKey]) -> str:
    """Render residual keys as one deletable entry per line.

    Args:
        keys: The keys.

    Returns:
        One indented line each, sorted, carrying source text only.
    """
    return "\n".join(
        sorted(f"  ({module!r}, {scope!r}, {local!r})" for module, scope, local in keys)
    )


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------


def _parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.arg, ...]:
    """Every positional or keyword parameter of a function.

    Args:
        node: The function.

    Returns:
        The parameters, excluding ``*args`` and ``**kwargs``.
    """
    args = node.args
    return (*args.posonlyargs, *args.args, *args.kwonlyargs)


def _takes_machine_state(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a function receives this machine through a pytest fixture.

    Args:
        node: The function.

    Returns:
        True when any parameter names one of the machine fixtures.
    """
    return any(arg.arg in MACHINE_FIXTURES for arg in _parameters(node))


def _names_any(node: ast.FunctionDef | ast.AsyncFunctionDef, live: frozenset[str]) -> bool:
    """Whether a function names one of a set of live producers as a parameter.

    Args:
        node: The function.
        live: The names already known live.

    Returns:
        True when it does.
    """
    return any(arg.arg in live for arg in _parameters(node))


def callee_name(call: ast.Call) -> str | None:
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


def _calls_one_of(value: ast.expr, live: frozenset[str]) -> bool:
    """Whether an expression calls one of the named functions.

    Args:
        value: The expression.
        live: The names to look for.

    Returns:
        True when a call to any of them appears anywhere inside it.
    """
    return any(isinstance(node, ast.Call) and callee_name(node) in live for node in ast.walk(value))


def _argument_carries(call: ast.Call) -> bool:
    """Whether an ARGUMENT's contents survive into what a call returns.

    THIS IS THE ONE DECISION WHERE THIS CHANNEL AND CS-850's DIVERGE, and the
    divergence is the reason this walk is not simply theirs. pytest's rewriter
    reprs a call's result AND each of its arguments, so on the ASSERTION channel
    ``helper(sweep.words)`` renders the words whatever ``helper`` does with them.
    A LOCAL holds only the RESULT, and an unresolved call returns a new object.

    Measured on this tree before the distinction existed: reading every call as
    carrying its arguments reported a local holding a ``subprocess`` result, a
    byte string read off disk and a boolean as though each held the path it was
    derived from, and that family alone was the majority of the live tier. A
    tier 1 guard whose live tier is mostly wrong trains its reader to ignore it,
    which is CS-850's 64-per-cent refutation arriving by a different road.

    THE COST, STATED RATHER THAN HIDDEN: a project helper that hands its
    argument's contents straight back - ``def only(xs): return sorted(xs)`` -
    is a carrier this reads as a barrier, so a local bound from one is not
    flagged. The vocabularies are imported rather than respelt, so the set of
    names that DO carry cannot drift away from the other channel's.

    Args:
        call: The enclosing call.

    Returns:
        True only for a declared content-transparent wrapper.
    """
    name = callee_name(call)
    if name is None:
        return False
    if name in CONTENT_REDUCERS:
        return False
    return name in CONTENT_TRANSPARENT


def _carries_at(parent: ast.AST, current: ast.AST) -> bool:
    """Whether one step out of ``current`` keeps its contents in the value.

    Args:
        parent: The enclosing node.
        current: The node being stepped out of.

    Returns:
        True when the enclosing expression still holds what ``current`` held.
    """
    if isinstance(parent, ast.Call):
        # A method call on the value is stepped over rather than judged: in
        # ``tags.items()`` the attribute is the CALLEE, not an argument, and
        # treating it as one would read every method access as a barrier.
        return True if current is parent.func else _argument_carries(parent)
    if isinstance(parent, ast.Compare):
        return False
    if isinstance(parent, ast.UnaryOp):
        return not isinstance(parent.op, ast.Not)
    if isinstance(parent, ast.IfExp):
        # The TEST is consumed and never bound; a BRANCH is what is bound.
        return current is not parent.test
    return True


def flows_into(node: ast.AST, kin: Mapping[int, ast.AST], root: int) -> bool:
    """Whether a value read at ``node`` reaches the bound expression's root.

    Args:
        node: Where the value is read.
        kin: Parent map for the value expression.
        root: Identity of the expression the local is bound to.

    Returns:
        True when it arrives with its contents intact.
    """
    current: ast.AST = node
    while True:
        if id(current) == root:
            return True
        parent = kin.get(id(current))
        if parent is None or not _carries_at(parent, current):
            return False
        current = parent


def _scopes(tree: ast.Module) -> list[ast.AST]:
    """Every lexical scope of one module, module scope first.

    Args:
        tree: The parsed module.

    Returns:
        The module, then every function definition in it.
    """
    return [tree, *[node for node in ast.walk(tree) if isinstance(node, ANY_FUNCTION)]]


@dataclass(frozen=True)
class _Binding:
    """One local currently holding an unmasked read of a withheld field."""

    local: str
    bound_at: int
    form: str
    holder: str
    field: str
    source: str


class _ModuleLocals:
    """One module's derived tables, shared by every scope scan in it."""

    def __init__(
        self,
        module: str,
        tree: ast.Module,
        registry: Mapping[str, list[Redacting]],
        returns: Mapping[str, str],
    ) -> None:
        """Prepare the tables this module's scan reads.

        Args:
            module: Repo-relative path.
            tree: The parsed module.
            registry: Every redacting class in the corpus, by simple name.
            returns: Corpus-wide function name to return-annotation word.
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
        self.returns = dict(returns)
        self.returns.update(
            {
                node.name: tail
                for node in ast.walk(tree)
                if isinstance(node, ANY_FUNCTION)
                and (tail := annotation_tail(node.returns)) is not None
            }
        )
        seeds, readable = reach_seeds(tree)
        self.under_declared = must_declare_reach(tree) and not readable
        self.live = live_functions(tree, seeds)

    def lookup(self, name: str | None) -> Redacting | None:
        """Resolve a class word to the declaration it names.

        Args:
            name: The class word, or None.

        Returns:
            The declaration, or None when nothing in the corpus declares it. A
            class defined in THIS module wins; several same-named classes
            elsewhere merge by UNIONING their withheld fields, which
            over-reports rather than under-reports.
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


class _LocalScan:
    """One lexical scope's locals, walked in the order they come into being."""

    def __init__(self, owner: _ModuleLocals, scope: ast.AST) -> None:
        """Bind the scope's parameters and prepare to walk its statements.

        Args:
            owner: The module tables.
            scope: A module or function definition.
        """
        self.owner = owner
        self.scope = scope
        self.name = scope.name if isinstance(scope, ANY_FUNCTION) else MODULE_SCOPE
        self.holders: dict[str, Redacting] = {}
        self.aliases: dict[str, tuple[str, str]] = {}
        self.unsafe: dict[str, _Binding] = {}
        self.asserts = 0
        # A ``global`` declaration is a property of the WHOLE scope rather than
        # of the point it is written at - Python resolves it at compile time -
        # so it is collected up front rather than as the walk reaches it. Only
        # ``global`` qualifies: a ``nonlocal`` name is a cell in the declaring
        # frame and a free variable in the inner one, and pytest renders both.
        # AT MODULE SCOPE IT IS NOT A REDIRECTION: a module frame's locals ARE
        # its globals, so a ``global`` there names something the frame renders
        # and suppressing it would be a false NEGATIVE - the direction that
        # hides a leak.
        self.global_names: frozenset[str] = (
            frozenset(
                name
                for inner in scope_statements(scope)
                if isinstance(inner, ast.Global)
                for name in inner.names
            )
            if isinstance(scope, ANY_FUNCTION)
            else frozenset()
        )
        # LIVE IS THE DEFAULT when the module owed a reach claim and did not
        # make a readable one. CS-850 measured each way of failing to declare
        # demoting a real disclosure to latent, silently.
        self.live = owner.under_declared
        if isinstance(scope, ANY_FUNCTION):
            self.live = self.live or _takes_machine_state(scope) or _names_any(scope, owner.live)
            for arg in _parameters(scope):
                declared = owner.lookup(annotation_tail(arg.annotation))
                if declared is None:
                    continue
                self.holders[arg.arg] = declared
                # CS-441's rule on this channel: a holder that arrived as a
                # PARAMETER came from outside, so nothing in here can claim it
                # was built from a synthetic fixture.
                self.live = True

    def holder_of(self, expr: ast.expr) -> Redacting | None:
        """The redacting class an expression evaluates to, if any.

        Args:
            expr: The expression.

        Returns:
            Its declaration, or None. A CHAINED receiver resolves through the
            inner holder's own field annotations, so ``model.header.token``
            needs ``header``'s type to be read first.
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

    def _hit(self, node: ast.expr) -> tuple[str, str] | None:
        """The withheld field one read names, if it names one.

        Args:
            node: An attribute read or a bare name.

        Returns:
            Holder class and field, or None.
        """
        if isinstance(node, ast.Attribute):
            holder = self.holder_of(node.value)
            if holder is not None and node.attr in holder.withheld:
                return (holder.name, node.attr)
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id)
        return None

    def carried(self, value: ast.expr) -> tuple[str, str, str] | None:
        """The withheld field a binding's VALUE carries into the local, if any.

        The walk goes UP from each read to the value expression's own root: a
        read that arrives there with no reduction on the way is what the local
        will hold. ``sweep.words`` arrives; ``len(sweep.words)`` does not;
        ``sorted(sweep.words)`` does, because sorting prints every element.

        Args:
            value: The assigned expression.

        Returns:
            Holder class, field name and the offending sub-expression's source,
            or None when nothing survives to the root.
        """
        kin = _parent_map(value)
        root = id(value)
        for node in ast.walk(value):
            if not isinstance(node, (ast.Attribute, ast.Name)):
                continue
            found = self._hit(node)
            if found is None:
                continue
            if flows_into(node, kin, root):
                return (found[0], found[1], ast.unparse(node))
        return None

    def _bind(
        self,
        target: ast.expr,
        value: ast.expr | None,
        annotation: ast.expr | None,
        form: str,
    ) -> None:
        """Record what one assignment target now holds.

        A REBINDING CLEARS, so a name reused for something safe stops carrying
        the finding of what it held before - and a name reused for something
        unsafe starts carrying the new one.

        Args:
            target: The target expression.
            value: The assigned expression, if there is one.
            annotation: Its declared type, if there is one.
            form: Which member of :data:`FOLLOWED_FORMS` this is.
        """
        if isinstance(target, (ast.Tuple, ast.List)):
            self._bind_unpacked(target, value)
            return
        if isinstance(target, ast.Starred):
            self._bind(target.value, value, None, UNPACK)
            return
        if not isinstance(target, ast.Name):
            # A subscript or attribute target binds no name to follow.
            return
        declared = self.owner.lookup(annotation_tail(annotation))
        if declared is None and value is not None:
            declared = self.holder_of(value)
        if declared is not None:
            self.holders[target.id] = declared
        else:
            self.holders.pop(target.id, None)
        # THE WHOLE-OBJECT CASE, AND IT IS THE LARGEST FALSE-POSITIVE FAMILY ON
        # THIS TREE. A local bound to a value that resolves to a redacting class
        # renders THAT CLASS'S OWN ``__repr__``, which is the thing the class
        # ships in order to withhold its fields - so a withheld field appearing
        # inside the CONSTRUCTOR CALL never reaches the rendering. Measured:
        # ``box = Sandbox(work=work, env=isolated.variables, ...)`` and every
        # local aliased from it accounted for 30 of 45 live findings before this
        # step existed, and not one of them renders anything the repr withholds.
        found = self.carried(value) if value is not None and declared is None else None
        if found is None:
            self.aliases.pop(target.id, None)
            self.unsafe.pop(target.id, None)
        else:
            holder, field, source = found
            # THE ALIAS IS KEPT EVEN FOR A ``global`` NAME AND THE FINDING IS
            # NOT, and the split is the whole of the fix. ``aliases`` answers
            # "does this name currently carry a withheld field", which is a
            # question about VALUE FLOW and stays true through a redirection -
            # so ``global W; W = sweep.words; x = W`` still flags ``x``.
            # ``unsafe`` answers "is this name in the frame that renders", and
            # a global-declared target is not, measured. Dropping the alias
            # too would trade a false positive for a false negative.
            self.aliases[target.id] = (holder, field)
            if target.id in self.global_names:
                self.unsafe.pop(target.id, None)
            else:
                self.unsafe[target.id] = _Binding(
                    local=target.id,
                    bound_at=target.lineno,
                    form=form,
                    holder=holder,
                    field=field,
                    source=source,
                )
        if value is not None and _calls_one_of(value, self.owner.live):
            self.live = True

    def _bind_unpacked(self, target: ast.Tuple | ast.List, value: ast.expr | None) -> None:
        """Bind a tuple or list target, pairing elementwise where it can.

        Args:
            target: The tuple or list target.
            value: The assigned expression, if there is one.
        """
        if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts):
            for element, item in zip(target.elts, value.elts, strict=True):
                self._bind(element, item, None, UNPACK)
            return
        for element in target.elts:
            self._bind(element, value, None, UNPACK)

    def _bind_loop(self, stmt: ast.For | ast.AsyncFor) -> None:
        """Bind a loop target from whichever element of its iterable resolves.

        BOTH KINDS OF ITERABLE MATTER HERE, and only one of them mattered to
        CS-850. ``for run in (guarded, control):`` walks holder OBJECTS, whose
        own reprs are what the frame prints. ``for word in sweep.words:`` walks
        the CONTENTS of a withheld field, so the target holds one decoded word
        - smaller than the aggregate and just as forbidden.

        Args:
            stmt: The loop.
        """
        source = stmt.iter
        candidates: list[ast.expr] = (
            list(source.elts) if isinstance(source, (ast.Tuple, ast.List, ast.Set)) else [source]
        )
        for candidate in candidates:
            if self.holder_of(candidate) is not None or self.carried(candidate) is not None:
                self._bind(stmt.target, candidate, None, FOR_TARGET)
                return
        self._bind(stmt.target, None, None, FOR_TARGET)

    def bind_statement(self, stmt: ast.stmt) -> None:
        """Apply every binding one statement establishes.

        Args:
            stmt: The statement.
        """
        if isinstance(stmt, ast.AnnAssign):
            self._bind(stmt.target, stmt.value, stmt.annotation, ANNOTATED)
        elif isinstance(stmt, ast.Assign):
            form = CHAINED if len(stmt.targets) > 1 else ASSIGN
            for target in stmt.targets:
                self._bind(target, stmt.value, None, form)
        elif isinstance(stmt, (ast.For, ast.AsyncFor)):
            self._bind_loop(stmt)
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                if item.optional_vars is not None:
                    self._bind(item.optional_vars, item.context_expr, None, WITH_TARGET)
        for inner in ast.walk(stmt):
            if isinstance(inner, ast.NamedExpr):
                self._bind(inner.target, inner.value, None, WALRUS)

    def findings(self) -> list[LocalFinding]:
        """Every local this scope leaves in the frame at a failing assertion.

        Returns:
            One finding per BINDING, keyed to the earliest assert it is alive
            at - not one per assertion, which would multiply a single leaky
            binding by however many arms follow it.
        """
        statements = list(scope_statements(self.scope))
        visible: dict[int, dict[str, _Binding]] = {}
        after: dict[int, dict[str, _Binding]] = {}
        for stmt in statements:
            self.bind_statement(stmt)
            after[id(stmt)] = dict(self.unsafe)
            if isinstance(stmt, ast.Assert):
                self.asserts += 1
                visible[id(stmt)] = dict(self.unsafe)
        self._carry_loops(statements, visible, after)
        return self._collect(statements, visible)

    def _carry_loops(
        self,
        statements: Sequence[ast.stmt],
        visible: dict[int, dict[str, _Binding]],
        after: Mapping[int, dict[str, _Binding]],
    ) -> None:
        """Fold each loop body's end state back onto the asserts inside it.

        A binding made after an assert is not in the frame the first time
        through - and IS the second time. The state at the end of one pass over
        a loop body is exactly the state carried into the next, so unioning it
        onto every assert in that body is the second iteration, without needing
        a fixpoint.

        Args:
            statements: The scope's statements, in flattened source order.
            visible: Assert node identity to what is in the frame at it.
            after: Statement identity to the state just after it ran.
        """
        for loop in statements:
            if not isinstance(loop, (ast.For, ast.AsyncFor, ast.While)):
                continue
            body = list(scope_statements(loop))
            if not body:
                continue
            end = after.get(id(body[-1]), {})
            for stmt in body:
                if not isinstance(stmt, ast.Assert) or id(stmt) not in visible:
                    continue
                merged = dict(end)
                merged.update(visible[id(stmt)])
                visible[id(stmt)] = merged

    def _collect(
        self, statements: Sequence[ast.stmt], visible: Mapping[int, dict[str, _Binding]]
    ) -> list[LocalFinding]:
        """Turn the per-assert frame states into one finding per binding.

        Args:
            statements: The scope's statements, in flattened source order.
            visible: Assert node identity to what is in the frame at it.

        Returns:
            The findings.
        """
        seen: set[tuple[str, int, str, str]] = set()
        out: list[LocalFinding] = []
        for stmt in statements:
            if not isinstance(stmt, ast.Assert):
                continue
            for binding in sorted(visible.get(id(stmt), {}).values(), key=lambda b: b.local):
                key = (binding.local, binding.bound_at, binding.holder, binding.field)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    LocalFinding(
                        module=self.owner.module,
                        lineno=stmt.lineno,
                        scope=self.name,
                        local=binding.local,
                        bound_at=binding.bound_at,
                        form=binding.form,
                        holder=binding.holder,
                        field=binding.field,
                        source=binding.source,
                        live=self.live,
                    )
                )
        return out


def scan_sources(sources: Mapping[str, str]) -> LocalSweep:
    """Run the whole derivation over a corpus of modules.

    ONE ENTRY POINT FOR BOTH THE REAL TREE AND A SYNTHETIC ONE, deliberately.
    A green run over the repository proves nothing on its own - "found nothing"
    and "looked for nothing" are the same output - and the only cheap way to
    tell them apart is to run the SAME code over a corpus whose answer is known
    in advance. That is also what makes the green-on-a-clean-tree property
    provable rather than argued.

    Args:
        sources: Module label to Python source.

    Returns:
        The sweep.

    Raises:
        SyntaxError: When a member of the corpus does not parse.
    """
    trees = {label: ast.parse(text) for label, text in sources.items()}
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
    declarations = 0
    for label, tree in trees.items():
        for entry in redacting_classes(label, tree, opaque, known):
            registry.setdefault(entry.name, []).append(entry)
            declarations += entry.withheld != frozenset()
    returns = {
        node.name: tail
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, ANY_FUNCTION) and (tail := annotation_tail(node.returns)) is not None
    }
    findings: list[LocalFinding] = []
    scopes = 0
    asserts = 0
    for label, tree in trees.items():
        owner = _ModuleLocals(label, tree, registry, returns)
        for scope in _scopes(tree):
            scan = _LocalScan(owner, scope)
            findings += scan.findings()
            asserts += scan.asserts
            scopes += 1
    return LocalSweep(
        modules=len(trees),
        scopes=scopes,
        asserts=asserts,
        declarations=declarations,
        forms=census(trees),
        findings=tuple(findings),
    )


def scan_source_locals(module: str, source: str) -> list[LocalFinding]:
    """Run the detector over ONE synthetic module.

    Args:
        module: A label for the findings.
        source: Python source.

    Returns:
        The findings.
    """
    return list(scan_sources({module: source}).findings)


@cache
def scan_tree() -> LocalSweep:
    """Run the detector over every tracked Python file in the repository.

    Returns:
        The sweep.
    """
    sources = {
        relative: (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        for relative in tracked_python_files()
    }
    return scan_sources(sources)
