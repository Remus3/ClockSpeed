"""CS-885 - the path-free OSError clone exists four times, and they must agree.

THE SHAPE THIS GUARDS. ``raise X(...) from exc`` makes the CAUSE's own text part
of the formatted traceback, and ``OSError.__str__`` appends ``filename`` and
``filename2`` verbatim - the home directory, the account directory and the save
name. The project's remedy is a two-line helper that rebuilds the failure from
``errno`` and ``strerror`` alone. FOUR MODULES SHIP THAT HELPER SEPARATELY, and
``tests/chained_cause_guard.py`` clears each of their call sites independently.
Nothing compared the four to each other, so one could be repaired, hardened or
broken alone and the other three would keep their clearance in silence.

WHY THE COPIES WERE NOT COLLAPSED INTO ONE OWNER, which is the decision this
module records rather than a cost it merely absorbs. The owner's clearance is
STRUCTURALLY same-module: ``_constructs_pathless_clone`` clears a slot only when
it is a bare-name call to a function defined at module level in THAT module.
Measured on this tree: rewriting a site to call a shared owner through an import
- bare name or dotted - drops it from ``closed-pathless`` to ``unproven``, and
every live site is written that same way, so they all drop at once. Preserving
the verdict would mean teaching the clearance to resolve imported names across
modules, which is a WIDENING of the predicate that issues the clearance, over
aliases, dotted calls, re-exports, shadowing and untracked targets. A false
clearance on this channel is worse than a duplicate, so the duplication stays
and this module is what makes it safe. THE SIZE OF THAT COST IS NOT WRITTEN
DOWN HERE - CLAUDE.md section 4 - and :func:`restated_counts` is what keeps it
out of the prose that states the shape.

AND A SINGLE OWNER WOULD NOT HAVE CLOSED THE SILENCE ANYWAY. The failure that is
actually undetected today is not "the copies disagree" but "a copy stopped being
safe", and that one is indifferent to how many copies there are. Measured: a
copy that puts ``filename`` back - the exact leak the helper exists to prevent -
stops qualifying, its sites fall to ``unproven`` beside twenty-seven shapes
nobody has looked at, and the live-tree arms in the census SKIP rather than
fail. :func:`unqualified` is the leg that reddens on it.

THE MEMBERSHIP IS DERIVED FROM THE CALL SITES, AND THAT IS THE WHOLE DESIGN.
Two cheaper derivations were available and both are anti-correlated with the
defect:

  * BY NAME - every module-level ``def`` spelled ``_pathless_cause``. That is
    the spelling measure ``memory/a-guard-can-measure-spelling.md`` records: an
    adversary escapes by renaming, and the population reports a clean zero about
    the wrong question.
  * BY QUALIFICATION - every function the census's own
    ``_pathless_clone_functions`` walk accepts. That walk reads the callee's
    BODY, so a copy that drifts into something unsafe DROPS OUT of it. The
    surviving members would then agree with each other and the arm would pass,
    with the broken copy invisible. An assertion over a population that shrinks
    when the defect appears is ``memory/an-empty-population-satisfies-every-
    zero.md`` one level up.

So membership reads only what the CALL SITE is written as - a censused chained
raise whose privacy-bearing slot is a bare-name call to a module-level function
of the same module - and never what the callee does. Rename the helper and it
stays in the population; break its body and it stays in the population. Both are
planted and executed in ``tests/test_pathless_clone_agreement.py``.

WHAT THIS MODULE DOES NOT COVER, stated as a boundary rather than left implied:

  1. IT DECIDES NOTHING ABOUT WHETHER A COPY IS SAFE. :func:`unqualified` asks
     ``tests/chained_cause_guard.py``, the one owner of that question, and
     reports its answer. Agreement among four copies that are all wrong the same
     way is agreement, and this module would report it green - which is why the
     qualification leg is separate and not folded into the comparison.
  2. A HELPER REACHED BY ANY OTHER SPELLING - a dotted call, an imported name, a
     call through a variable, a method or a nested ``def``. The slot rules here
     mirror the owner's exactly so that the two populations cannot disagree, and
     ``test_the_population_covers_every_site_the_census_cleared`` pins that.
     Widening either without the other is the drift this module exists against.
  3. THE THREE SITES A HELPER MAY OPEN BESIDE ITS CAUSE. The wrapper's own
     message is ``args`` and belongs to ``tests/exception_message_guard.py``;
     the context channel belongs to the census. This module reads the cause and
     the raised slots only.
"""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Final

from tests.chained_cause_guard import (
    BUCKET_GRADED,
    FORM_EXPLICIT,
    FORM_SUPPRESSED,
    MODULE_SCOPE,
    _form_of,
    _module_level_rebindings,
    _parse,
    _pathless_clone_functions,
    _shadowed,
    _walk,
    bucket_of,
    tracked_sources,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The two forms whose slot can carry a clone, and they are the SAME two the
#: owner's ``_constructs_pathless_clone`` rules on. ``FORM_IMPLICIT`` is absent
#: here for the reason it is absent there: ``raise clone(exc)`` with no ``from``
#: leaves ``__context__`` pointing at the caught original, which the formatter
#: prints in full underneath, both paths intact.
CARRYING_FORMS: Final = (FORM_EXPLICIT, FORM_SUPPRESSED)


class PathlessCloneDerivationError(RuntimeError):
    """A tracked module could not be parsed, so the population is short."""


@dataclass(frozen=True)
class Reliance:
    """One censused raise that depends on a same-module helper for its privacy.

    Attributes:
        module: Repo-relative path, POSIX separators.
        lineno: The ``ast.Raise`` statement line.
        qualname: Dotted enclosing scope, :data:`MODULE_SCOPE` at module level.
        form: The form of the raise, one of :data:`CARRYING_FORMS`.
        callee: The bare name called in the privacy-bearing slot.
    """

    module: str
    lineno: int
    qualname: str
    form: str
    callee: str


@dataclass(frozen=True)
class Copy:
    """One helper a censused raise relies on, and what its body reduces to.

    Attributes:
        module: Repo-relative path, POSIX separators.
        name: The function name as written. Carried for the REPORT only -
            nothing here decides anything from it.
        lineno: The ``def`` line.
        body: The canonical body - see :func:`canonical_body`.
        qualifies: Whether the census's own walk still accepts it as building a
            path-free clone. READ FROM THE OWNER, never decided here.
    """

    module: str
    name: str
    lineno: int
    body: str
    qualifies: bool

    @property
    def key(self) -> str:
        """The identity this copy is reported under.

        Returns:
            ``module::name``.
        """
        return f"{self.module}::{self.name}"


def _slot(node: ast.Raise, form: str) -> ast.expr | None:
    """The expression whose value reaches the rendered chain through this raise.

    MIRRORS ``chained_cause_guard._constructs_pathless_clone`` DELIBERATELY. The
    two must select the same slot for the same form or the populations diverge,
    and a member this module does not watch is a copy free to drift.

    Args:
        node: The raise.
        form: Its form.

    Returns:
        The cause of an explicit chain, the raised expression of a ``from
        None``, and None for every other form.
    """
    if form == FORM_EXPLICIT:
        return node.cause
    if form == FORM_SUPPRESSED:
        return node.exc
    return None


def _called_name(candidate: ast.expr | None) -> str | None:
    """The bare function name a slot calls, if it calls one at all.

    A dotted callee, a call through a variable, a lambda and a bare name that is
    not called all come back None - the same shapes the owner declines to clear.

    Args:
        candidate: The slot expression, or None.

    Returns:
        The name, or None.
    """
    if not isinstance(candidate, ast.Call) or not isinstance(candidate.func, ast.Name):
        return None
    return candidate.func.id


def _module_functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    """Module-level plain ``def`` nodes, by name.

    MODULE LEVEL AND PLAIN ``def`` ONLY, matching the owner's resolution scope.
    A name bound at module level by anything else - a class, an import, an
    assignment below the ``def`` - is subtracted, because what the name means at
    import time is the LAST binding and this module does not resolve that.

    AN ``async def`` IS SUBTRACTED TOO, AND THE OWNER'S REASON IS NOT THIS ONE.
    ``_module_level_rebindings`` deliberately skips both kinds of definition, so
    it does not subtract an async name; the owner instead refuses it inside
    ``_pathless_clone_functions``, on the grounds that what an ``async def``
    returns is a coroutine rather than the exception the body names. Either
    route reaches "never cleared", but only subtracting it here keeps the two
    populations spelled the same way, and a member one walk holds while the
    other does not is exactly the drift this module exists against.

    A NAME DEFINED TWICE IS SUBTRACTED RATHER THAN RESOLVED TO THE LAST, for the
    fail-closed reason the owner states about the same shape.

    Args:
        tree: The parsed module.

    Returns:
        Name to definition, for names a call can be resolved to.
    """
    found: dict[str, ast.FunctionDef] = {}
    duplicated: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef):
            duplicated.add(node.name)
            continue
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in found:
            duplicated.add(node.name)
        found[node.name] = node
    rebound = _module_level_rebindings(tree) | duplicated
    return {name: node for name, node in found.items() if name not in rebound}


def _fresh_prefix(node: ast.FunctionDef, declared: frozenset[str]) -> str:
    """A parameter token that collides with no OTHER name the function uses.

    Canonicalising parameters onto a fixed token would let two different bodies
    reduce to the same text whenever one of them binds that token itself, and a
    false AGREEMENT is the one direction this module must never err in.

    THE PARAMETERS THEMSELVES ARE EXCLUDED FROM THE COLLISION SET, and getting
    that backwards produces the opposite fault - a false RED. A helper whose
    parameter is ALREADY spelled like the token would push the prefix one
    underscore along, so it reduced to ``__p0`` while an identical helper taking
    ``exc`` reduced to ``_p0``, and two functions that do exactly the same thing
    were reported as drift. Measured by
    ``test_a_body_that_binds_the_canonical_token_still_compares_correctly``
    before this argument existed.

    Args:
        node: The definition.
        declared: Its parameter names, which are about to be renamed and so
            cannot collide with what they become.

    Returns:
        A prefix no other ``ast.Name`` in the function starts with.
    """
    used = {
        inner.id
        for inner in ast.walk(node)
        if isinstance(inner, ast.Name) and inner.id not in declared
    }
    prefix = "_p"
    while any(name.startswith(prefix) for name in used):
        prefix = "_" + prefix
    return prefix


def canonical_body(node: ast.FunctionDef) -> str:
    """Reduce a function to what it DOES, dropping what it is merely called.

    THE NORMALISATION IS THE ARM'S DEFINITION OF AGREEMENT, so what it discards
    is a decision rather than a convenience:

      * THE DOCSTRING IS DROPPED. The four live copies already carry different
        docstrings on purpose - each states the reasoning its own module needs -
        and an arm red on that from the first run is an arm that gets switched
        off rather than read.
      * PARAMETER NAMES ARE CANONICALISED. A copy taking ``error`` instead of
        ``exc`` is the same helper; reddening on it would be the spelling
        measure this module is built against.
      * THE FUNCTION NAME AND ITS ANNOTATIONS ARE NOT READ AT ALL. Only
        statements survive, so agreement is about executable behaviour.

    Args:
        node: The definition to reduce.

    Returns:
        The canonical body text. Empty when the function is only a docstring.
    """
    clone = deepcopy(node)
    declared = clone.args.posonlyargs + clone.args.args + clone.args.kwonlyargs
    prefix = _fresh_prefix(clone, frozenset(argument.arg for argument in declared))
    mapping = {argument.arg: f"{prefix}{index}" for index, argument in enumerate(declared)}
    body = list(clone.body)
    if body and isinstance(body[0], ast.Expr):
        leading = body[0].value
        if isinstance(leading, ast.Constant) and isinstance(leading.value, str):
            body = body[1:]
    for statement in body:
        for inner in ast.walk(statement):
            if isinstance(inner, ast.Name) and inner.id in mapping:
                inner.id = mapping[inner.id]
    return "\n".join(ast.unparse(statement) for statement in body)


def reliances_in_sources(sources: Mapping[str, str]) -> tuple[Reliance, ...]:
    """Every censused raise that leans on a same-module helper for its privacy.

    READS THE CALL SITE AND NOTHING ELSE. The callee's body is never consulted
    here, which is what keeps a broken copy inside the population instead of
    quietly outside it.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        The reliances, ordered by module then line.

    Raises:
        PathlessCloneDerivationError: A module did not parse.
    """
    found: list[Reliance] = []
    for module in sorted(sources):
        tree = _parsed(module, sources[module])
        resolvable = _module_functions(tree)
        for node, scope, handler in _walk(tree, (), None):
            if not isinstance(node, ast.Raise):
                continue
            form = _form_of(node, handler)
            if form not in CARRYING_FORMS:
                continue
            name = _called_name(_slot(node, str(form)))
            if name is None or name not in resolvable:
                continue
            found.append(
                Reliance(
                    module=module,
                    lineno=node.lineno,
                    qualname=".".join(scope) or MODULE_SCOPE,
                    form=str(form),
                    callee=name,
                )
            )
    return tuple(sorted(found, key=lambda site: (site.module, site.lineno, site.callee)))


def copies_in_sources(sources: Mapping[str, str]) -> tuple[Copy, ...]:
    """The distinct helpers the reliances name, reduced to their bodies.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        One entry per distinct module-and-name, ordered by module then name.

    Raises:
        PathlessCloneDerivationError: A module did not parse.
    """
    wanted: dict[str, set[str]] = {}
    for reliance in reliances_in_sources(sources):
        wanted.setdefault(reliance.module, set()).add(reliance.callee)
    found: list[Copy] = []
    for module in sorted(wanted):
        tree = _parsed(module, sources[module])
        shadowed = _shadowed(tree)
        qualifying = _pathless_clone_functions(tree, shadowed)
        resolvable = _module_functions(tree)
        for name in sorted(wanted[module]):
            node = resolvable[name]
            found.append(
                Copy(
                    module=module,
                    name=name,
                    lineno=node.lineno,
                    body=canonical_body(node),
                    qualifies=name in qualifying,
                )
            )
    return tuple(found)


def _parsed(module: str, source: str) -> ast.Module:
    """Parse one module, naming it rather than the exception on failure.

    Args:
        module: The repo-relative path.
        source: Its text.

    Returns:
        The parsed tree.

    Raises:
        PathlessCloneDerivationError: It did not parse. The cause is dropped
            with ``from None`` and only the relative path is named: a
            SyntaxError renders the absolute path it failed on, and this module
            does not get to leak one while grading that channel.
    """
    try:
        return _parse(module, source)
    except Exception as exc:
        raise PathlessCloneDerivationError(
            f"{module} did not parse: {type(exc).__name__}"
        ) from None


def disagreements(population: Sequence[Copy]) -> tuple[str, ...]:
    """The distinct canonical bodies, when the copies do not all share one.

    AN EMPTY POPULATION REPORTS NO DISAGREEMENT, and that is deliberate rather
    than an oversight. This is a pure predicate over whatever it is handed; the
    question "was anything measured at all" is a DIFFERENT question and is
    asserted by its own arm, because folding the two would make a broken
    derivation and a clean tree produce the same output
    (``memory/an-empty-population-satisfies-every-zero.md``).

    Args:
        population: The copies to compare.

    Returns:
        Empty when every copy reduces to the same body, and the distinct
        bodies, ordered, otherwise.
    """
    bodies = {copy.body for copy in population}
    if len(bodies) <= 1:
        return ()
    return tuple(sorted(bodies))


def unqualified(population: Sequence[Copy]) -> tuple[str, ...]:
    """The copies a censused raise relies on that the census no longer accepts.

    THE LEG THAT REDDENS ON A DRIFT INTO UNSAFETY, which the census reports as
    ``unproven`` and its live-tree arms SKIP over.

    Args:
        population: The copies to check.

    Returns:
        The keys of the copies that no longer qualify, ordered.
    """
    return tuple(copy.key for copy in population if not copy.qualifies)


# ---------------------------------------------------------------------------
# CS-886 - what a copy's docstring is allowed to claim about the collapse
# ---------------------------------------------------------------------------
#
# THE DEFECT THIS SECTION EXISTS AGAINST. One copy's docstring called a single
# shared owner "the correct repair" and stopped there. That was honest when it
# was written and false the moment CS-885 priced the repair and declined it: it
# handed a later reader a recommendation this project had already measured and
# rejected, with no cost beside it. The remedy is not silence - it is that
# exactly ONE docstring owns the decision, states its price, and every other
# copy stays out of it.

#: The one copy whose docstring may name the collapse, because it is the one
#: that PRICES it. Spelled as a module rather than a ``Copy`` key because the
#: population is deliberately name-blind: rename the helper and the exemption
#: must follow it, which it does only if it is keyed on where it lives.
PRICING_COPY: Final = "clockspeed/surface/config.py"

#: Spellings that name the collapse into one owner. Deliberately TOPIC-shaped
#: rather than promise-shaped: a copy outside :data:`PRICING_COPY` that merely
#: raises the subject is already drift, because a reader who meets it there has
#: no way to tell a live proposal from a settled refusal with no price beside
#: it. Routing the reader to the one copy that carries the price is the point.
OWNER_PHRASES: Final = ("shared owner", "single owner", "one owner", "correct repair")

#: What :data:`PRICING_COPY`'s docstring must carry for its claim to be PRICED
#: rather than merely asserted - the item that measured it, the verdict, what
#: the sites drop to, and the shape of the aggregate. Not one of them is a
#: measurement: the magnitude lives in the live census and
#: :func:`restated_counts` forbids writing it down beside them.
COST_PHRASES: Final = ("cs-885", "declined", "unproven", "drop at once")

#: Excuses that go stale the instant the slice that wrote them ends. A
#: docstring deferring a decision to a write-list is telling a later reader
#: about a dispatch they cannot see, cannot check and cannot act on, which is
#: the second half of the CS-886 defect.
STALE_EXCUSES: Final = ("write-list", "this slice")

#: Ordinals indexed by the count they name. The pricing docstring identifies
#: WHICH copy it is with one, and an arm holds that word to ``len(copies())``
#: computed at run time rather than to a literal.
ORDINALS: Final = (
    "zeroth",
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
)

#: Cardinals indexed by the count they name - the spelling a restatement of a
#: measured population would most naturally take.
CARDINALS: Final = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
)


def flatten(text: str) -> str:
    """Reduce a docstring to one lower-case line for phrase matching.

    A phrase a line wrap split across two lines is the same phrase, and a
    predicate that missed it would hand an author an escape they did not even
    have to intend.

    Args:
        text: The docstring as written.

    Returns:
        The text lower-cased, with every run of whitespace collapsed to one
        space.
    """
    return " ".join(text.lower().split())


def copy_docstrings(population: Sequence[Copy], sources: Mapping[str, str]) -> dict[str, str]:
    """The docstring each copy carries, keyed by :attr:`Copy.key`.

    RE-PARSED FROM THE SOURCE RATHER THAN CARRIED ON :class:`Copy`.
    :func:`canonical_body` drops the docstring on purpose - the four copies are
    meant to differ there, and an agreement arm red on that from its first run
    is an arm that gets switched off rather than read - so a field the
    comparison must ignore has no business on the record it compares.

    A COPY WHOSE FUNCTION HAS NO DOCSTRING IS ABSENT rather than present as an
    empty string. Every caller asserts the result covers the whole population,
    so a missing docstring reddens instead of becoming a member that satisfies
    every phrase test for free by carrying no text
    (``memory/an-empty-population-satisfies-every-zero.md``).

    Args:
        population: The copies to read.
        sources: Repo-relative module path to source text.

    Returns:
        Copy key to docstring, as written.

    Raises:
        PathlessCloneDerivationError: A module did not parse, or a copy names a
            module the mapping does not carry. Only the relative path is named.
    """
    found: dict[str, str] = {}
    for copy in population:
        if copy.module not in sources:
            raise PathlessCloneDerivationError(f"{copy.module} is not among the sources given")
        tree = _parsed(copy.module, sources[copy.module])
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name != copy.name or node.lineno != copy.lineno:
                continue
            text = ast.get_docstring(node, clean=False)
            if text is not None:
                found[copy.key] = text
    return found


def promising_copies(population: Sequence[Copy], sources: Mapping[str, str]) -> tuple[str, ...]:
    """The copies outside :data:`PRICING_COPY` whose docstring names the collapse.

    THE SWEEP READS THE HELPER'S OWN DOCSTRING AND NOTHING ELSE, which is a
    boundary and not a shortcut. ``clockspeed/surface/config.py`` carries a
    SECOND and unrelated seam collision at module level - the certificate-pair
    literals it spells a second time, whose own repair CS-885 never priced.
    Letting this sweep reach module-level comments would attach this item's
    measurement to a claim it does not measure, which is the exact defect
    CS-886 is filed against.

    Args:
        population: The copies to sweep.
        sources: Repo-relative module path to source text.

    Returns:
        The keys of the offending copies, ordered.

    Raises:
        PathlessCloneDerivationError: A module did not parse.
    """
    exempt = f"{PRICING_COPY}::"
    return tuple(
        sorted(
            key
            for key, text in copy_docstrings(population, sources).items()
            if not key.startswith(exempt)
            and any(phrase in flatten(text) for phrase in OWNER_PHRASES)
        )
    )


def missing_cost_phrases(text: str) -> tuple[str, ...]:
    """The :data:`COST_PHRASES` a docstring does not carry.

    Args:
        text: The docstring as written.

    Returns:
        Empty when it states the cost, and the absent phrases in order
        otherwise.
    """
    flat = flatten(text)
    return tuple(phrase for phrase in COST_PHRASES if phrase not in flat)


def stale_excuses(text: str) -> tuple[str, ...]:
    """The :data:`STALE_EXCUSES` a docstring carries.

    Args:
        text: The docstring as written.

    Returns:
        The excuses found, in order. Empty is the passing answer.
    """
    flat = flatten(text)
    return tuple(phrase for phrase in STALE_EXCUSES if phrase in flat)


def names_its_ordinal(text: str, count: int) -> bool:
    """Whether a docstring calls itself the Nth copy, for the N it is handed.

    ANCHORED ON ``the <ordinal> copy`` RATHER THAN THE BARE ORDINAL, and that
    is a measurement rather than a preference: all four live copies share a
    sentence about supplying ``winerror`` as "a fourth argument", so a bare
    ``fourth`` test passes on every one of them and would keep passing after
    the sentence it exists to hold had been deleted.

    Args:
        text: The docstring as written.
        count: The live population size the ordinal has to match.

    Returns:
        True when it names itself the ``count``-th copy. False for a count no
        ordinal here spells, which is the fail-closed direction: a tree that
        grew past this table has moved out from under the prose.
    """
    if not 0 <= count < len(ORDINALS):
        return False
    return f"the {ORDINALS[count]} copy" in flatten(text)


def restated_counts(text: str, count: int) -> tuple[str, ...]:
    """The spellings of a live measurement that prose is not allowed to carry.

    CLAUDE.md section 4: a measured number written into a document is a lie
    with a timestamp on it. The magnitude of this item's cost lives in the
    census, so the docstring states the SHAPE - every relying site drops at
    once - and this reports any attempt to write the size down beside it.

    THE DIGIT TEST IS BOUNDED ON BOTH SIDES so an item id does not trip it:
    ``CS-885`` and ``CS-857`` each contain an eight and neither restates one.

    A SHARP EDGE, STATED RATHER THAN HIDDEN: the cardinal for a small count is
    an ordinary English word, so a population that fell to one would report the
    ``one`` inside ``one owner``. That is a false red on a tree whose topology
    has collapsed to a single relying site - a change that has to be looked at
    anyway - and it is the safe direction for a leg whose other failure mode is
    letting a stale number stand.

    Args:
        text: The docstring as written.
        count: The live measurement it must not spell.

    Returns:
        The spellings found, digit before word. Empty is the passing answer.
    """
    flat = flatten(text)
    found: list[str] = []
    if re.search(rf"(?<!\d){count}(?!\d)", flat):
        found.append(str(count))
    if 0 <= count < len(CARDINALS) and re.search(rf"\b{CARDINALS[count]}\b", flat):
        found.append(CARDINALS[count])
    return tuple(found)


def graded_sources() -> Mapping[str, str]:
    """The tracked tree, less the modules the census does not grade.

    THE SCOPE IS THE OWNER'S, NOT A SECOND ONE. ``bucket_of`` is the census's
    single classifier over frozen paths, its own planted controls and
    unclassified roots; deriving the split again here would be a second copy of
    a decision, which is the fault this whole item is about.

    THIS IS NOT A CONVENIENCE. ``tests/test_chained_cause.py`` plants
    ``_identity``, a helper that returns its argument unchanged, precisely so
    the census can prove it sees a call-expression cause that LEAKS. It is a
    module-level function reached from a censused slot, so it is a structurally
    perfect member of this population and it can never qualify. Measured: it
    was the one live finding before this filter existed. Grading a deliberate
    control as a defect is how a guard earns a permanent exemption entry it did
    not need.

    Returns:
        Repo-relative module path to source text, graded bucket only.

    Raises:
        RuntimeError: git is unavailable or reported failure.
    """
    return {
        module: text
        for module, text in tracked_sources().items()
        if bucket_of(module) == BUCKET_GRADED
    }


@cache
def reliances() -> tuple[Reliance, ...]:
    """The live reliance population, derived on every run.

    Returns:
        Every censused raise in the graded tree that leans on a same-module
        helper.

    Raises:
        PathlessCloneDerivationError: The tree could not be parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return reliances_in_sources(graded_sources())


@cache
def copies() -> tuple[Copy, ...]:
    """The live copy population, derived on every run.

    Returns:
        One entry per distinct helper the graded tree's censused raises rely
        on.

    Raises:
        PathlessCloneDerivationError: The tree could not be parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return copies_in_sources(graded_sources())
