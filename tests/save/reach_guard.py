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
#: refutation pass on CS-495 and reproduced by the merger: ``fchmod`` added to
#: :data:`_FILESYSTEM_PRIMITIVES` and classified nowhere left the partition test
#: GREEN, because the reach set was DERIVED as the locators unioned with the
#: vocabulary minus the exclusions - so the assertion reduced to ``A <= B | A``
#: and held for any vocabulary whatever. An unclassified name was not caught; it
#: was silently made a reach primitive.
#:
#: **CS-497 MADE THOSE SENTENCES TRUE RATHER THAN DELETING THEM.** Inclusion is
#: now DECLARED in :data:`_REACHES_THE_LIBRARY` instead of falling out of a set
#: subtraction, and :func:`_reach_primitives` INTERSECTS rather than subtracts,
#: so a name in neither map reaches nothing and is reported by name. The record
#: of what was false stays because the mechanism that made it false is the one
#: worth recognising again, not because the claim is still wrong.
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
#: vocabulary, and only the vocabulary needs a partition. ``ranked_saves`` is the
#: bounded newest-first ranking ``latest_save`` is the head of, and yields real
#: save paths exactly as that does.
_LIBRARY_LOCATORS: Final = frozenset(
    (
        "resolve_save_root",
        "resolve_account_dir",
        "latest_save",
        "ranked_saves",
        "_library_save_paths",
    )
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
#: Vocabulary members that ARE library reach, name by name.
#:
#: DECLARED, NOT DERIVED, AND THAT IS CS-497. Deriving this as "the vocabulary
#: minus the exclusions" meant a name classified nowhere landed here by
#: arithmetic, and every assertion over it reduced to a tautology. Both halves
#: are written down now, and :func:`_reach_primitives` intersects, so the cost
#: of forgetting a name is that it reaches nothing and a test says so by name.
#:
#: THIS IS NOT CS-433's DEFECT COMING BACK, and the difference is the reason it
#: is safe. That defect was two lists in two FILES, neither aware of the other,
#: drifting until a guard named none of the path-bearing primitives its sibling
#: enumerated. These two sit in one file over one vocabulary and are asserted to
#: PARTITION it exactly - neither can gain or lose a name without the other
#: disagreeing.
_REACHES_THE_LIBRARY: Final = frozenset(
    (
        "open",
        "read_bytes",
        "glob",
        "rglob",
        "iterdir",
        "scandir",
        "listdir",
        "resolve",
        "expanduser",
        "home",
        "cwd",
        "stat",
    )
)


def _reach_primitives(vocabulary: frozenset[str]) -> frozenset[str]:
    """The reach set this module derives from a filesystem vocabulary.

    A FUNCTION SO THE DERIVATION CAN BE GRADED WITH A VOCABULARY IT HAS NOT
    SEEN. Asked only about the shipped constant, a derivation that absorbs an
    unclassified name is indistinguishable from one that rejects it.

    Args:
        vocabulary: Filesystem names to classify.

    Returns:
        The locators plus the vocabulary members DECLARED to reach the library.
        A name in neither declaration reaches nothing, which is what makes
        forgetting one visible instead of free.
    """
    return _LIBRARY_LOCATORS | (frozenset(vocabulary) & _REACHES_THE_LIBRARY)


_LIBRARY_PRIMITIVES: Final = _reach_primitives(_FILESYSTEM_PRIMITIVES)

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

    IT IS ASKED ONLY WHERE A CALL IS BEING MADE, and that bound belongs to the
    CALLER rather than to a parameter here. CS-492 tried giving this a switch so
    a hand-back could ask it without the string channel; the switch was set
    correctly at one of three sites, and then the ARGUMENT channel manufactured
    false reachers anyway, because this vocabulary holds path constants as well
    as locators. :func:`_hands_back_a_primitive` now reads no call at all and
    records why. Nothing here changed as a result - this question was always
    right for a callee - and the switch is gone rather than left for the next
    caller to set wrong.

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


def _imported_module_names(tree: ast.Module) -> frozenset[str]:
    """Every name this module binds by importing something.

    ``from clockspeed.data import locate`` binds ``locate``; ``import
    pathlib`` binds ``pathlib``; either may be aliased. What matters to the
    caller is only that the name arrived through an import statement rather
    than through a parameter or a local, which is what separates
    ``locate.resolve_save_root`` from ``page.home``.

    IT DOES NOT ASK WHETHER THE NAME IS REALLY A MODULE. ``from x import
    helper`` binds a function and is counted here too. That over-approximates
    in the safe direction - it admits a receiver rather than refusing one - and
    deciding otherwise would mean resolving what every import target actually
    is, which is the analysis this repo has declined.

    Args:
        tree: The parsed module.

    Returns:
        The bound names, aliases resolved to the name actually bound.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            found |= {one.asname or one.name.split(".")[0] for one in node.names}
    return frozenset(found)


def _hands_back_a_primitive(
    value: ast.expr,
    names: frozenset[str],
    attributes: frozenset[str],
    imported: frozenset[str],
) -> bool:
    """Whether an expression HANDS BACK a primitive rather than the RESULT of calling one.

    THE DISTINCTION IS THE WHOLE POINT AND IT IS WHY THIS IS NOT
    :func:`_stands_for_a_primitive`. That one reads any MENTION anywhere inside
    the expression, deliberately, because a name bound to
    ``locate.resolve_save_root()`` is one this package never calls again. Here
    the bound name IS called, by construction - this exists to decide whether a
    function is itself a stand-in for a primitive - so ``return
    locate.resolve_save_root`` and ``return locate.resolve_save_root()`` have to
    part company. Reading a mention would make every graded sweep in the package
    a primitive and put a reach requirement on all of their callers, which is
    the false-reason failure CS-471 already had to repair once. It was measured
    before it was rejected: the companion in
    ``tests/save/test_reach_guard.py`` returns ``sorted(... .glob(...))`` and a
    mention rule calls that a primitive.

    IT IS :func:`_callee_resolves` MINUS ONE ARM AND PLUS THE CONTAINERS. The
    missing arm is the one that reads THROUGH a call to its callee: that arm is
    right when the expression sits in callee position, where ``partial(prim)()``
    really does call the primitive, and wrong here, where ``prim()`` hands back
    a path and not a locator. Everything else - a dispatch subscript, a
    conditional, an override-with-fallback, a wrapper that takes the name as an
    argument - answers the same way in both.

    THE CONTAINER ARMS WERE ADDED AFTER A REFUTATION PASS MEASURED THEIR
    ABSENCE, and the defect was an asymmetry rather than a missing shape.
    :func:`_stands_for_a_primitive` WALKS a container, so a module-scope
    ``_TABLE = {"save": locate.resolve_save_root}`` followed by
    ``_TABLE["save"]()`` is caught; without these arms the same table handed
    back from a function - ``return {"save": locate.resolve_save_root}`` then
    ``_locators()["save"]()`` - was not. One mechanism applied to part of its
    population, in the population this item is named for. The call-through arm
    is still the only thing left out, and it is left out for a stated reason.

    INSIDE A CONTAINER, ONLY A SPELLED PRIMITIVE COUNTS, and this bound was
    MEASURED rather than reasoned to. The container arms above and the CALL arm
    below compose into a false reacher, and the tree already had one:
    ``tests/save/test_phase4_gate.py``'s ``_child_pytest_args`` returns a list
    of pytest ARGV holding ``str(SAVE_TESTS)``. ``SAVE_TESTS`` is a module
    constant derived from ``__file__``, which :func:`_stands_for_a_primitive`
    treats as standing for a primitive under its deliberate over-approximation,
    so :func:`_resolves_by_string` read that ``str(...)`` call as handing back a
    locator, and every caller of the argv builder acquired a library-reach
    requirement. Two tests that reach nothing were flagged. That is the
    thirteen-function false-reason failure recorded in
    :func:`_callee_resolves`, reached from the other side, and the repair is the
    same one: refuse the receiver-ish channel rather than widen the vocabulary.

    THE DISTINCTION IS BETWEEN A CONTAINER OF CALLABLES AND A CONTAINER OF
    RESULTS. ``{"save": locate.resolve_save_root}`` holds a locator, spelled.
    ``[str(path), "-q"]`` holds strings that were COMPUTED, and a computed
    element is data. So a container recurses into a spelled name or attribute
    and into further containers, and stops at a call - while a call handed back
    DIRECTLY is still read, because ``return functools.partial(locate.resolve_save_root)``
    really does hand back a locator. THE BOUND, STATED: a container holding a
    wrapper rather than a spelling - ``[functools.partial(prim)]`` - is not
    read.

    A LAMBDA IS READ THROUGH ITS BODY'S CALLEE. ``self.finder = lambda:
    locate.resolve_save_root()`` holds something that reaches when called,
    which is this question exactly, and the body is where the callee is.

    A HAND-BACK RESOLVES A SPELLING AND NOTHING ELSE, and it took FOUR rounds
    and three separate false reachers on the real tree to arrive at a rule that
    short. Each round narrowed one channel and left the identical value flowing
    through the next one:

    - The store arm read a MENTION anywhere, so ``monkeypatch.setattr(mod,
      "banner", _label("home"))`` made ``banner`` a locator. ``home`` is a
      locator name and that was a caption.
    - Switching the string channel off PER CALLER set it correctly at one of
      three sites, so the same caption handed back by a ``return`` still made a
      locator server out of a module touching no filesystem.
    - Removing the switch left the ARGUMENT channel, and the vocabulary is full
      of PATH CONSTANTS: ``env["PYTHONPATH"] = str(_HERE)`` and
      ``setitem(env, "label", str(_HERE))`` both manufactured an attribute, and
      a ``lambda`` delegating to :func:`_callee_resolves` re-admitted the string
      channel one layer down.

    THE ROOT CAUSE IS THAT THE VOCABULARY DOES NOT SEPARATE A CALLABLE FROM A
    VALUE. :func:`_stands_for_a_primitive` treats the RESULT of a primitive as
    standing for one, deliberately, and says that is safe because such a name is
    never CALLED. A hand-back is precisely the place that stops being true, so
    NO CALL is read here at all: ``partial(prim)`` and ``str(_HERE)`` are the
    same shape, one argument already in the vocabulary, and nothing syntactic
    separates them. Four rounds of tuning arms is the evidence that nothing
    will, short of splitting the vocabulary - which is a change to that
    function's contract and not to this one.

    A LAMBDA IS THE ONE CALL THAT IS UNWRAPPED, and it is unwrapped rather than
    delegated. ``lambda: locate.resolve_save_root()`` reaches when called, so
    one layer comes off and the SAME spelling question is asked of the callee -
    which answers True for ``locate.resolve_save_root`` and False for
    ``_label``. Delegating to :func:`_callee_resolves` instead is what
    re-admitted the string channel, measured.

    WHAT THAT COSTS, STATED: ``self.finder = functools.partial(prim)``,
    ``return operator.methodcaller("glob")`` and ``self.finder =
    getattr(account, "glob")`` are not read as handing a locator back. All three
    are real, all three are a NARROWING rather than a repair, and they are filed
    rather than papered over. The same wrappers in CALLEE position are still
    read in full, because that is where a call is actually being made.

    EVERY COMPOUND SHAPE IS REFUSED, AND THE LAST OF THEM WENT BECAUSE A
    MUTATION PASS COULD NOT TELL IT FROM ``return False``. A subscript, a
    conditional and an override-with-fallback were each read by taking the
    expression apart and asking about the pieces. No control exercised any of
    them, and all three carry the path-constant hazard this docstring has
    already described twice: ``return _PATHS[0]`` where ``_PATHS`` holds
    resolved paths is the argv defect one shape further out. An arm that no test
    can distinguish from ``False`` is already deleted and does not know it, so
    it is deleted here, where the deletion is visible and the cost is written
    down. THE COST: a locator handed back through a dispatch subscript, a
    conditional or a fallback is not read. Filed, not papered over.

    A CONTAINER IS REFUSED FOR THE SAME REASON, AND THAT REFUSAL IS A
    MEASUREMENT RATHER THAN AN OVERSIGHT. Reading one was tried, shipped into
    an intermediate build, and manufactured a FALSE REACHER on this tree TWICE,
    from two different channels. ``tests/save/test_phase4_gate.py``'s ``_child_pytest_args``
    returns pytest ARGV holding ``str(SAVE_TESTS)``; narrowing the arm to a
    SPELLED element then let ``tests/save/test_workdir.py``'s builder through
    instead, because its argv holds the bare name ``_MODULE_NODE_ID``. Both
    flagged tests that reach nothing.

    THE ROOT CAUSE IS NOT IN THIS FUNCTION AND IS WORTH NAMING, because it
    bounds what any future widening here can do.
    :func:`_stands_for_a_primitive` deliberately treats the RESULT of a
    primitive as standing for one, and its docstring says that is safe because
    "it costs a flag only where the bound name is itself CALLED, which no module
    in this package does". The vocabulary is therefore full of PATH CONSTANTS -
    ``THIS_MODULE``, ``SAVE_TESTS``, ``_MODULE_NODE_ID`` - which are values and
    not locators. This function asks whether something handed back is a
    CALLABLE, so every one of those constants is a false answer waiting for a
    caller, and a container of argv strings is where they all live. Reading a
    container safely needs the vocabulary split into callables and results,
    which is a change to that function's contract and not to this one.

    THE COST OF THE REFUSAL, STATED: ``return {"save": locate.resolve_save_root}``
    followed by ``_locators()["save"]()`` is NOT read, while the same table
    written at module scope IS - :func:`_stands_for_a_primitive` walks a
    container and this does not. That asymmetry is real, it is a residual rather
    than a repair, and it is filed rather than papered over.

    THE RECEIVER IS READ IN THIS ONE PLACE, AND ONLY HERE - CS-492 round five,
    measured. Everywhere else in this guard a receiver is discarded, because
    deciding what an expression is an instance of is the type resolution this
    repo has declined; and for a CALLEE that is right, since ``account.glob(...)``
    reaches whatever ``account`` is. A STORE is different. This vocabulary
    contains ordinary English words - ``home``, ``open``, ``stat``, ``cwd``,
    ``resolve`` - so a receiver-blind rule read ``monkeypatch.setattr(page,
    "banner", page.home)`` as storing a locator, and every ``.banner()`` call in
    the module acquired a reach requirement. Three such false reachers were
    measured on planted modules that touch no filesystem, and a refutation pass
    put the shipped tree "one ordinary line" from one.

    A PROJECT LOCATOR NEEDS NO RECEIVER, and leaving it needing one was the
    receiver rule applied to a population wider than its own reason. The reason
    is that the VOCABULARY holds ordinary English - ``home``, ``open``,
    ``stat``. :data:`_LIBRARY_LOCATORS` holds none: ``resolve_save_root`` and
    ``resolve_account_dir`` are project names, which is why they are kept in a
    separate constant whose docstring says only the vocabulary needs a
    partition. Requiring an import for them cost seven measured routes -
    ``data.locate.resolve_save_root`` through a dotted receiver, a module-scope
    alias of the module itself, a module handed in as a parameter - every one of
    them classed SILENT, so the suite-wide sweep never ran on them. The clause
    was measured to cost nothing on the shipped tree.

    SO AN ATTRIBUTE HAND-BACK COUNTS THREE WAYS AND NOT ONE. It counts when the
    attribute is ALREADY a known reaching attribute, receiver-blind, which is
    what carries a hold-and-serve chain; and it counts when the primitive is
    spelled on a receiver this file IMPORTED, which is how a locator actually
    arrives - ``locate.resolve_save_root``. A primitive spelled on a parameter
    is neither, and ``page.home`` is a caption.

    THE COST, STATED: a bound method of a real path stored on an attribute -
    ``self.finder = account.glob`` where ``account`` is a ``Path`` - is not read
    as handing a locator back. That is a NARROWING rather than a repair, it is
    filed, and it is the price of not manufacturing declarations about where
    personal data flows.

    Args:
        value: The expression handed back.
        names: The reach vocabulary.
        attributes: The attribute vocabulary, per :func:`_reaching_attributes`.
            An attribute already known to hold a locator resolves whatever its
            receiver is.
        imported: The names this module binds by importing, per
            :func:`_imported_module_names`.

    Returns:
        True when the value SPELLS one of ``names`` in one of those two ways,
        or is a lambda whose body calls something that does. Everything else is
        False, including every shape this function used to take apart.
    """
    if isinstance(value, ast.Name):
        return value.id in names
    if isinstance(value, ast.Attribute):
        if value.attr in attributes:
            return True
        if value.attr in _LIBRARY_LOCATORS:
            return True
        receiver = value.value
        return value.attr in names and isinstance(receiver, ast.Name) and receiver.id in imported
    if isinstance(value, ast.Lambda):
        inner = value.body
        return _hands_back_a_primitive(
            inner.func if isinstance(inner, ast.Call) else inner, names, attributes, imported
        )
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
    scope: ast.AST,
    names: frozenset[str],
    *,
    inside_functions: bool,
    also: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Expand a primitive set by every name a scope binds that stands for one.

    Resolved to a fixpoint so a chain of aliases cannot outrun it, and bounded
    by the number of bindings so a self-referential assignment cannot spin.

    Args:
        scope: The subtree to read.
        names: The primitives to start from.
        inside_functions: Passed through to :func:`_bindings_in`.
        also: Names that RESOLVE a primitive but are never returned as ones -
            the attribute vocabulary of :func:`_reaching_attributes`. ``local =
            self.finder`` binds a local to an attribute that stands for a
            locator, and without this the local resolves to nothing. They are
            read and not added, so an attribute name cannot escape into the
            bare-name namespace and flag an unrelated call.

    Returns:
        ``names`` plus every alias the scope binds.
    """
    bindings = _bindings_in(scope, inside_functions=inside_functions)
    effective = set(names)
    for _round in range(len(bindings) + 1):
        grew = False
        for bound, value in bindings:
            if not _stands_for_a_primitive(value, frozenset(effective) | also):
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


def _resolves_to_a_name(node: ast.expr) -> str | None:
    """The function name a KEY expression stands for, when it states one exactly.

    TWO SPELLINGS, BOTH EXACT AND NEITHER A GUESS. A string constant IS the
    name; ``f.__name__`` names ``f``. Anything else returns None rather than a
    best effort, which is the whole repair CS-493 needed a second round for.

    Args:
        node: The key expression.

    Returns:
        The name, or None when the expression does not state one.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "__name__"
        and isinstance(node.value, ast.Name)
    ):
        return node.value.id
    return None


def _comprehension_key_names(node: ast.DictComp, constants: Mapping[str, ast.expr]) -> set[str]:
    """The names a dict comprehension's KEY expression takes from its iterable.

    THE ONE INDIRECTION THIS PACKAGE ACTUALLY WRITES, resolved by position
    rather than by evaluation. ``{call.__name__: label for label, call in
    _TABLE}`` binds ``call`` to element 1 of every tuple in ``_TABLE``, so the
    key names whatever sits at that index - which is read off the constant's
    own literal tuples.

    IT RESOLVES NOTHING IT CANNOT PLACE. A key naming a variable this cannot
    locate in the target, an iterable that is not a module constant, or a
    constant that is not a tuple of tuples, all contribute nothing.

    Args:
        node: The comprehension.
        constants: Module-scope bindings, for the iterable.

    Returns:
        The function names the key expression resolves to.
    """
    if len(node.generators) != 1:
        return set()
    generator = node.generators[0]
    if generator.ifs:
        # A FILTER IS NOT RESOLVED, IT IS REFUSED. This reads the table by
        # POSITION and cannot see which rows an ``if`` clause drops, so a
        # filtered comprehension would name helpers the module does not
        # declare. Over-reading is the direction that MANUFACTURES a reacher -
        # see :func:`_declared_graded_names` - so the answer here is nothing,
        # and the exactness control reports the module rather than this
        # guessing on its behalf.
        return set()
    table = constants.get(generator.iter.id) if isinstance(generator.iter, ast.Name) else None
    if not isinstance(table, ast.Tuple | ast.List):
        return set()

    # WHERE THE KEY'S VARIABLE SITS IN EACH ROW. A bare target is column 0 of a
    # one-column table; a tuple target places it by position. A target of any
    # other shape, or a name appearing twice in it, resolves to nothing.
    if not (
        isinstance(node.key, ast.Attribute)
        and node.key.attr == "__name__"
        and isinstance(node.key.value, ast.Name)
    ):
        return set()
    wanted = node.key.value.id
    elements = (
        generator.target.elts if isinstance(generator.target, ast.Tuple) else [generator.target]
    )
    columns = [
        index
        for index, element in enumerate(elements)
        if isinstance(element, ast.Name) and element.id == wanted
    ]
    if len(columns) != 1:
        return set()
    column = columns[0]

    return {cell.id for row in table.elts if isinstance(cell := _cell(row, column), ast.Name)}


def _cell(row: ast.expr, column: int) -> ast.expr | None:
    """One column of a table row, when the row states it.

    Args:
        row: The row expression.
        column: Which element to take.

    Returns:
        The element, or None when the row cannot supply it.
    """
    if isinstance(row, ast.Tuple | ast.List):
        return row.elts[column] if column < len(row.elts) else None
    return row if column == 0 else None


def _mapping_key_names(value: ast.expr, constants: Mapping[str, ast.expr]) -> set[str]:
    """The names a declaration's KEY POSITIONS state, and nothing else.

    KEYS ONLY, WHICH IS CS-493's SECOND ROUND. The first repair walked the whole
    declaration for anything that looked like a function name, and a refutation
    pass measured what that costs: a reason string naming a second helper, a
    filtered comprehension, and a tuple assignment binding the graded and exempt
    maps together all put names into the graded set that the module does not
    declare. That is not a harmless over-approximation - see
    :func:`_declared_graded_names` for why it manufactures reachers.

    Args:
        value: The declaration's bound value.
        constants: Module-scope bindings, for a comprehension's iterable.

    Returns:
        The names the key positions state exactly.
    """
    found: set[str] = set()
    for node in ast.walk(value):
        if isinstance(node, ast.Dict):
            # A ``**other`` entry has NO key, which is why the keys are
            # optional. It contributes nothing rather than being followed.
            found |= {
                name
                for key in node.keys
                if key is not None and (name := _resolves_to_a_name(key)) is not None
            }
        elif isinstance(node, ast.DictComp):
            found |= _comprehension_key_names(node, constants)
    return found


def _module_scope_values(tree: ast.Module, name: str) -> list[ast.expr]:
    """Every value bound to ``name`` at a module's own scope, paired exactly.

    PAIRED, NOT COLLECTED. ``_GRADED_LIBRARY_REACH, _EXEMPT_LIBRARY_REACH = a, b``
    binds two names in one statement, and a reader that took the whole statement's
    value for either name read the exempt map as graded - measured.

    Args:
        tree: The parsed module.
        name: The declaration name to look for.

    Returns:
        The values bound to it, outermost scope only.
    """
    inside = _nodes_inside_functions(tree)
    found: list[ast.expr] = []
    for node in ast.walk(tree):
        if id(node) in inside:
            continue
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name and node.value:
                found.append(node.value)
        elif isinstance(node, ast.Assign):
            for target, value in _paired_targets(node):
                if isinstance(target, ast.Name) and target.id == name:
                    found.append(value)
    return found


def _declared_graded_names(tree: ast.Module) -> frozenset[str]:
    """The functions a module's graded-reach declaration names, read out of its source.

    READ FROM THE TREE RATHER THAN IMPORTED. The classifier runs over every file
    in the package before anything has established that they all import, and a
    guard that imports what it is judging has a cycle waiting in it - this
    module is imported BY most of the package it scans. It also runs over
    PLANTED modules under ``tmp_path``, which are not importable at all.

    WHAT IT READ, AND WHY THAT WAS THE PERMISSIVE FAILURE. It read ``ast.Dict``
    constant keys and nothing else, so a declaration built any other way read as
    EMPTY. The sibling export is filtered by this set, so a module whose
    declaration could not be read exported no reaching helper, every importer of
    it was classed silent, and the guard never ran on them. **Two tracked
    modules were measured in exactly that state**, one keying on ``f.__name__``
    and one building the map with a comprehension over a table of
    ``(label, function)`` pairs.

    **THE FIRST REPAIR WIDENED THIS TO WALK THE WHOLE DECLARATION FOR ANYTHING
    NAME-SHAPED, AND JUSTIFIED IT WITH A SENTENCE THAT WAS FALSE.** That sentence
    said an over-read "can never manufacture a reacher", because
    :func:`_reaching_names_of` returns ``graded & (direct | indirect)``. A
    refutation pass measured the circularity: ``indirect`` is computed from
    ``propagating``, and ``propagating`` is computed from ``graded``. Widening
    ``graded`` widens the very set it is then intersected with. Reproduced end to
    end - a module where NO function calls any primitive exported a reacher, and
    an importer of it was told to declare a library reach for a function that
    touches nothing. A false reason forced by a guard is the defect this package
    has already shipped eight of.

    SO IT READS KEY POSITIONS AND REFUSES EVERYTHING ELSE. A string key, an
    ``f.__name__`` key, and a comprehension key resolved through its iterable by
    POSITION. A spelling it cannot place contributes nothing and is caught by
    ``test_every_graded_declaration_in_this_package_is_readable_from_the_source``,
    which compares this against what the module holds at runtime.

    Args:
        tree: The sibling's parsed module.

    Returns:
        The functions its ``_GRADED_LIBRARY_REACH`` names, empty when it
        declares none.
    """
    constants = {
        bound[0]: value
        for bound, value in _bindings_in(tree, inside_functions=False)
        if len(bound) == 1
    }
    found: set[str] = set()
    for value in _module_scope_values(tree, _REACH_DECLARATIONS[0]):
        found |= _mapping_key_names(value, constants)
    return frozenset(found)


#: How many module hops the sibling resolution follows.
#:
#: THE BOUND IN DATA, WHICH IS CS-493. It was stated in three docstrings and
#: nowhere else, so nothing measured it and nothing would have noticed it
#: drifting. It is a parameter now, defaulted from here, and
#: ``test_the_sibling_resolution_bound_is_the_number_this_module_declares``
#: plants a chain one hop longer than this and requires it to go unresolved at
#: this value and resolved at one more. A number a control moves is a number
#: that means something.
#:
#: ONE IS DELIBERATE AND IS NOT A LIMITATION OF THE CODE. Raising it resolves
#: longer chains and costs a parse of every module on every hop, and the wider
#: analysis has been declined before. What changed here is that the cost of
#: raising it is now a one-character edit with a control that proves the effect,
#: rather than an argument about what the guard might do.
_SIBLING_RESOLUTION_HOPS: Final = 1


@cache
def _reaching_names_of(
    sibling: Path, names: frozenset[str], hops: int = _SIBLING_RESOLUTION_HOPS
) -> frozenset[str]:
    """The helpers a sibling module defines that reach the SAVE LIBRARY.

    THE HOP COUNT IS A PARAMETER AND ITS DEFAULT IS
    :data:`_SIBLING_RESOLUTION_HOPS`. At one hop the sibling is scanned with the
    base vocabulary and its OWN aliases and NOT with its own sibling imports, so
    a helper reaching the library only through a THIRD module is not resolved -
    which is the bound CS-493 moved out of prose and into a number a control can
    move. At more than one it resolves the sibling's siblings too, recursively,
    with the budget spent one hop at a time.

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
        hops: How many further module hops to follow from this one. At one, the
            sibling's own imports are not resolved.

    Returns:
        The names of its graded helpers that reach the library directly or
        through another of its graded helpers, methods keyed ``Class.method``
        as :func:`_scanned_functions` keys them.
    """
    tree = ast.parse(sibling.read_text(encoding="utf-8"))
    base = names
    if hops > 1:
        # THE NEXT HOP, spent from this one's budget. Guarded on the count
        # rather than on a visited set because the budget is what bounds it:
        # a cycle cannot outlast a strictly decreasing integer. It is folded in
        # BEFORE the fixpoint rather than after it, so a name reached through a
        # further hop can still be aliased here; the old order resolved aliases
        # first and left anything the next hop contributed unaliased.
        base = base | _sibling_reaching_names(tree, sibling, names, hops=hops - 1)
    # THE SAME VOCABULARY THE GUARD ITSELF USES, and this is CS-492's round-two
    # hole rather than a tidying. This walk built its own with the alias half
    # ALONE, so neither of that item's new mechanisms reached it: a sibling
    # whose declared sweep reaches through a HELD ATTRIBUTE exported nothing,
    # and its importer was classed silent - while the identical sibling
    # spelling the reach directly exported the sweep and got its importer
    # caught. Measured side by side. Three call sites ask which of a module's
    # functions reach, two of them were given the new vocabulary and this one
    # was not, which is the same one-mechanism-part-of-its-population shape
    # this item is made of, reached at the module seam.
    primitives, attributes = _reach_vocabulary(tree, base)
    functions = _scanned_functions(tree)
    graded = _declared_graded_names(tree)
    direct = frozenset(
        name for name, node in functions.items() if _calls_any(node, primitives, attributes)
    )
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
    tree: ast.Module,
    source: Path,
    names: frozenset[str],
    hops: int = _SIBLING_RESOLUTION_HOPS,
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
        hops: The remaining module-hop budget, passed to each sibling scan.

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
                reaching |= _reaching_names_of(named, names, hops)
    return frozenset(reaching)


def _sibling_reaching_names(
    tree: ast.Module,
    source: Path,
    names: frozenset[str],
    hops: int = _SIBLING_RESOLUTION_HOPS,
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
        hops: The remaining module-hop budget, spent one hop per module.

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
            exported = _reaching_names_of(sibling, names, hops)
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
                reaching |= _reaching_names_of(sibling, names, hops)

    return frozenset(reaching) | _runtime_named_siblings(tree, source, names, hops)


def _returned_values(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.expr]:
    """Every value a function hands back, its own nested definitions excluded.

    A NESTED ``def`` HAS ITS OWN RETURNS AND THEY ARE NOT THIS FUNCTION'S.
    :func:`_calls_any` walks a parent's whole body on purpose, because a nested
    def's reach IS its parent's, and the opposite is true of a return: an inner
    helper handing back a locator says nothing about what the outer function
    hands back to ITS caller.

    Args:
        node: The function.

    A ``yield`` HANDS BACK TOO - CS-492 round two, measured past the
    return-only read by a refutation pass. ``def _locators(): yield
    locate.resolve_save_root`` followed by ``next(_locators())()`` serves the
    locator exactly as a ``return`` does, and reading one statement and not the
    other is one mechanism applied to part of its population - which is the
    shape this whole item is made of.

    THE SENTENCE HERE SAID ``yield from`` WAS READ THE SAME WAY BECAUSE "a
    container of spellings is walked", AND THAT WAS MEASURED FALSE in the same
    round it was written. :func:`_hands_back_a_primitive` refuses a container,
    for reasons recorded there, so ``yield from (locate.resolve_save_root,)`` is
    NOT read and ``yield from _FINDERS`` - the value being a bare alias rather
    than a display - IS. The statement is collected here either way; what
    happens to its value is that function's business, and only the second
    spelling survives it. Corrected in place with the refutation beside it
    rather than rewritten back; the container half is filed as a residual.

    Returns:
        The expressions handed back, by ``return``, ``yield`` or ``yield from``.
        A bare ``return`` and a bare ``yield`` are excluded because neither
        hands back anything that can be called.
    """
    nested: set[int] = set()
    for statement in node.body:
        for child in ast.walk(statement):
            if isinstance(child, (*_ANY_FUNCTION, ast.Lambda)):
                nested |= {id(inner) for inner in ast.walk(child) if inner is not child}
    return [
        inner.value
        for statement in node.body
        for inner in ast.walk(statement)
        if isinstance(inner, ast.Return | ast.Yield | ast.YieldFrom)
        and inner.value is not None
        and id(inner) not in nested
    ]


def _handing_back_names(
    tree: ast.Module,
    names: frozenset[str],
    attributes: frozenset[str],
    imported: frozenset[str],
) -> frozenset[str]:
    """Module-scope function names that SERVE a primitive instead of calling one.

    CS-492's third route, and the shape that names it is the module-level
    ``__getattr__``: ``def __getattr__(name): return locate.resolve_save_root``
    makes every attribute of the module a locator, and the function itself
    CALLS nothing, so the guard read it as silent and the consumer's
    ``__getattr__("anything")()`` named no primitive in any callee position.

    KEYED ON HANDING ONE BACK, NEVER ON THE NAME ``__getattr__``. A vocabulary
    of one dunder would leave the ordinary factory - ``def _locator(): return
    locate.resolve_save_root`` - open while reading as though it did not, which
    is the fence CS-491 wrote and this item inherits.

    METHODS ARE NOT HERE. A method that hands one back binds an ATTRIBUTE name,
    not a module-scope one, so it belongs to :func:`_reaching_attributes` and is
    resolved there. Putting it here would let a method name flag an unrelated
    module-scope call of the same spelling, which is the inversion this guard's
    keying note records.

    Args:
        tree: The parsed module.
        names: The reach vocabulary resolved so far.
        attributes: The attribute vocabulary, passed through.
        imported: The imported receiver names, passed through.

    Returns:
        The module-scope function names that hand back a primitive.
    """
    return frozenset(
        name
        for name, node in _scanned_functions(tree).items()
        if "." not in name
        and any(
            _hands_back_a_primitive(value, names, attributes, imported)
            for value in _returned_values(node)
        )
    )


def _effective_primitives(
    tree: ast.Module,
    names: frozenset[str],
    *,
    source: Path | None = None,
    hops: int = _SIBLING_RESOLUTION_HOPS,
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

    THE THIRD HALF IS THE SERVE SHAPE - CS-492. A function that HANDS BACK a
    locator rather than calling one taught this nothing, so a module-level
    ``__getattr__`` returning ``locate.resolve_save_root`` made every attribute
    of that module a locator while the module itself read as silent.

    IT IS THE NAME HALF OF :func:`_reach_vocabulary` AND NOTHING ELSE. The
    attribute half is returned beside it there, and a caller that needs both
    calls that rather than this. This is kept because the controls that grade
    the vocabulary ask about names, and narrowing a caller to the half it uses
    is not the same as giving it a wrong answer.

    Args:
        tree: The parsed module.
        names: The primitives to start from.
        source: The module's own file, when the caller has it.
        hops: The module-hop budget for the sibling half.

    Returns:
        The primitives, plus every alias the module binds, every sibling helper
        it imports that reaches the library itself, and every module-scope
        function that serves one.
    """
    return _reach_vocabulary(tree, names, source=source, hops=hops)[0]


def _reach_vocabulary(
    tree: ast.Module,
    names: frozenset[str],
    *,
    source: Path | None = None,
    hops: int = _SIBLING_RESOLUTION_HOPS,
) -> tuple[frozenset[str], frozenset[str]]:
    """The NAME half and the ATTRIBUTE half of a module's reach, resolved TOGETHER.

    THE TWO HALVES ARE ONE FIXPOINT AND NOT TWO PASSES - CS-492 round two,
    measured by a refutation pass and reproduced by the merger. The first draft
    ran the name fixpoint and then :func:`_reaching_attributes` once, after it.
    Each of the item's two new mechanisms was therefore invisible to the other,
    and composing them defeated both at once:

        _HOLDER.finder = locate.resolve_save_root   # the attribute half
        def _serve(): return _HOLDER.finder         # the serve half
        def _reaches(): return _serve()()

    Neither half is short a shape; the serve half simply never learned that
    ``finder`` was an attribute worth serving, because the attribute half had
    not run yet. Both of those spellings ship as controls of this item
    INDIVIDUALLY, and their composition was green. Running them to a joint
    fixpoint is the whole repair.

    IT TERMINATES BECAUSE BOTH SETS ONLY GROW. Each round either adds a name or
    an attribute or stops, and the bound is the number of things there are to
    add, so a self-referential module cannot spin.

    Args:
        tree: The parsed module.
        names: The primitives to start from.
        source: The module's own file, when the caller has it. Its absence
            skips the sibling half rather than guessing at it.
        hops: The module-hop budget for the sibling half.

    Returns:
        The reach vocabulary and the attribute vocabulary. The second is
        consulted only where :func:`_callee_resolves` already discards a
        receiver, which is what keeps an attribute name out of the bare-name
        namespace.
    """
    effective = names
    if source is not None:
        effective = effective | _sibling_reaching_names(tree, source, names, hops)
    imported = _imported_module_names(tree)
    attributes = _reaching_attributes(tree, imported)
    for _round in range(len(_scanned_functions(tree)) + len(_attribute_stores(tree)) + 1):
        widened = _aliases_bound_in(tree, effective, inside_functions=False, also=attributes)
        serving = _serving_names(tree, attributes, imported)
        widened = widened | _handing_back_names(tree, serving, attributes, imported)
        grown = _reaching_attributes(tree, imported)
        if (widened, grown) == (effective, attributes):
            break
        effective, attributes = widened, grown
    return effective, attributes


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


def _callee_resolves(
    func: ast.expr, effective: frozenset[str], attributes: frozenset[str] = frozenset()
) -> bool:
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
        attributes: The ATTRIBUTE vocabulary, per :func:`_reaching_attributes`.
            Consulted in the ``Attribute`` arm ALONE - CS-492. That arm already
            reads ``func.attr`` and discards the receiver, so admitting these
            there resolves ``self.finder()`` and ``_HOLDER.finder()`` without
            putting ``finder`` into the bare-name namespace, where it would flag
            an unrelated local of that spelling. The default is empty so a
            caller that has not resolved a module's attributes gets the old,
            narrower answer rather than a wrong one.

    Returns:
        True when the callee resolves one of ``effective``, or one of
        ``attributes`` through an attribute step.
    """
    if isinstance(func, ast.Name):
        return func.id in effective
    if isinstance(func, ast.Attribute):
        return func.attr in effective or func.attr in attributes
    if isinstance(func, ast.Call):
        return _resolves_by_string(func, effective) or _callee_resolves(
            func.func, effective, attributes
        )
    if isinstance(func, ast.Subscript):
        return _callee_resolves(func.value, effective, attributes)
    if isinstance(func, ast.IfExp):
        return any(_callee_resolves(one, effective, attributes) for one in (func.body, func.orelse))
    return isinstance(func, ast.BoolOp) and any(
        _callee_resolves(one, effective, attributes) for one in func.values
    )


def _call_reaches_a_primitive(
    call: ast.Call, effective: frozenset[str], attributes: frozenset[str] = frozenset()
) -> bool:
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
        attributes: The attribute vocabulary, passed to :func:`_callee_resolves`.

    Returns:
        True when this call reaches one.
    """
    func = call.func
    if isinstance(func, ast.Name) and func.id == "getattr" and len(call.args) > 1:
        return _names_a_primitive(call.args[1], effective)
    return _callee_resolves(func, effective, attributes)


def _calls_any(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    names: frozenset[str],
    attributes: frozenset[str] = frozenset(),
) -> bool:
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

    AN ATTRIBUTE THAT STANDS FOR A PRIMITIVE IS CALLED THE SAME WAY - CS-492.
    ``self.finder = locate.resolve_save_root`` in ``__init__`` and
    ``self.finder()`` in a sibling method share no scope this function can see,
    because the binding is function-local to a DIFFERENT function and the name
    it binds is an attribute rather than a local. The attribute vocabulary is
    resolved once per module by :func:`_reaching_attributes` and handed down,
    and it is also handed to the local alias fixpoint as a lookup - so ``local =
    self.finder`` followed by ``local()`` resolves too - without any of those
    names being added to the bare-name vocabulary this function matches on.

    Args:
        node: The function.
        names: The names to look for.
        attributes: The module's attribute vocabulary, per
            :func:`_reaching_attributes`. Empty by default, which is the answer
            this function gave before CS-492.

    Returns:
        True when at least one call matches.
    """
    effective = _aliases_bound_in(node, names, inside_functions=True, also=attributes)
    return any(
        _call_reaches_a_primitive(inner, effective, attributes)
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

    IT IS THE PERSONAL-DATA WALK'S READER ALONE. CS-492's attribute vocabulary
    started out calling this and stopped: what that walk needs is the receiver
    step, because a field's ANNOTATION is a claim about one class, and what the
    reach vocabulary needs is the attribute NAMESPACE, which no receiver owns.
    :func:`_attribute_stores` records why in full.

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


def _attribute_stores(tree: ast.Module) -> list[tuple[str, ast.expr]]:
    """Every attribute name a module stores something under, with the value stored.

    RECEIVER-BLIND, AND THAT IS THE SIBLING SWEEP RATHER THAN A SIMPLIFICATION.
    The first draft of this read a store only inside a class method and only
    onto that method's own receiver, per :func:`_stores_on_receiver`. Two
    siblings of CS-492's own routes were then measured OPEN against it and are
    the same mechanism reached one step differently: ``_HOLDER.finder =
    locate.resolve_save_root`` written at MODULE scope, which is in no method
    and on no receiver; and ``setattr(self, "finder", locate.resolve_save_root)``,
    which is in a method and on the receiver but spells the attribute as a
    string, so no assignment target carries it. Reading the store shape in one
    of its three spellings is one mechanism applied to part of its population,
    which is the pattern this whole item is made of. What the guard consumes is
    the attribute NAMESPACE, and that namespace does not care which object the
    store landed on - :func:`_callee_resolves` discards the receiver anyway.

    ``_paired_targets`` IS REUSED RATHER THAN COPIED, so the tuple store
    ``self.finder, self.root = locate.resolve_save_root, None`` is read here for
    the same reason it is read for the personal-data walk, and cannot drift from
    it.

    THE THREE-ARGUMENT STORE SHAPE IS GONE, AND IT WAS REMOVED ON EVIDENCE
    RATHER THAN ON TASTE. It read ``f(target, "name", value)`` as a store, which
    is what ``setattr`` is - and is equally what ``getattr(spec, "reader",
    open)``, ``re.sub(pattern, "count", text)`` and ``OSError(13, "denied",
    path)`` are, none of which stores anything. Three separate refutation
    rounds produced FALSE REACHERS through this one door, each with a different
    payload, and the last of them defeated this module's own exclusion map:
    ``monkeypatch.setattr(os, "walk", os.scandir)`` put ``walk`` into the
    attribute vocabulary, and ``walk`` is excluded BY NAME because ``ast.walk``
    is how every AST guard in this package reads a tree. One ordinary
    three-line helper appended to ``tests/save/test_phase4_gate.py`` took it
    from nine flagged functions to twenty. A declaration is a written claim
    about where personal data flows; manufacturing eleven of them is worse than
    missing the route this door was opened for.

    WHAT IT COST, AND WHERE THAT WENT: ``setattr(self, "finder", prim)`` and a
    store through a helper of one's own are no longer read. Both were controls
    of CS-492 and both are now filed. The shape cannot be salvaged by keying on
    the callee instead - that was measured too, and it leaves every other store
    helper open while reading as though it did not.

    Args:
        tree: The parsed module.

    Returns:
        One entry per store, as the attribute name and the expression stored.
        Nothing here decides whether the value reaches anything -
        :func:`_reaching_attributes` asks that, so this stays vocabulary-free
        and can be read without one.
    """
    found: list[tuple[str, ast.expr]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            found.extend(
                (target.attr, value)
                for target, value in _paired_targets(node)
                if isinstance(target, ast.Attribute)
            )
        elif (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            and isinstance(node.target, ast.Attribute)
        ):
            found.append((node.target.attr, node.value))
    found.extend(_subscript_stores(tree))
    return found


def _subscript_stores(tree: ast.Module) -> list[tuple[str, ast.expr]]:
    """Every attribute stored through a SUBSCRIPT under a string literal.

    ``self.__dict__["finder"] = locate.resolve_save_root`` IS holding a
    primitive on an instance attribute - it is the acceptance sentence of
    CS-492 word for word - and the assignment-target read above cannot see it,
    because the target is a ``Subscript`` and not an ``Attribute``. Measured
    green by a refutation pass, end to end: the module was classed SILENT, so
    the suite-wide sweep never ran on it at all. ``vars(self)["finder"]`` is the
    same store spelled through a builtin and is read here too; before this it
    reddened by ACCIDENT, naming ``__init__`` because the target walk harvested
    the bare name ``vars``, and never naming the consumer.

    RECEIVER-BLIND like the rest of this walk, and keyed on the string literal
    rather than on ``__dict__``, so a mapping-backed attribute store under any
    other spelling is read the same way. THE BOUND, STATED: a subscript key that
    arrives through a variable is not read, for the same reason the string store
    above does not read one - resolving it is the alias analysis this repo has
    declined.

    Args:
        tree: The parsed module.

    Returns:
        One entry per store, as the attribute name and the expression stored.
    """
    found: list[tuple[str, ast.expr]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target, value in _paired_targets(node):
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.slice, ast.Constant)
                and isinstance(target.slice.value, str)
            ):
                found.append((target.slice.value, value))
    return found


def _serving_names(
    tree: ast.Module, attributes: frozenset[str], imported: frozenset[str]
) -> frozenset[str]:
    """The names that stand for a LOCATOR, as opposed to a path a locator produced.

    A SECOND, NARROWER NAME SET, AND THE REASON IT HAS TO EXIST IS ONE SENTENCE
    THIS MODULE HAS BEEN CIRCLING FOR SIX ROUNDS. :func:`_stands_for_a_primitive`
    treats the RESULT of a primitive as standing for one, deliberately, and
    justifies it by saying that costs a flag "only where the bound name is
    itself CALLED, which no module in this package does". The set it builds is
    therefore full of PATH CONSTANTS - ``THIS_MODULE``, ``SAVE_TESTS``,
    ``REPO_ROOT``, ``_MODULE_NODE_ID`` - and that is fine for a CALLEE question,
    which is the only question it was built for.

    A HAND-BACK IS THE ONE PLACE THAT JUSTIFICATION FAILS, because a hand-back
    makes the bound name callable through something else. Handing the callee set
    to :func:`_hands_back_a_primitive` meant ``sources["source"] = _HERE``
    stored a "locator" and flagged every ``.source()`` call, and
    ``def _source(): return _HERE`` - the ordinary extract-a-constant refactor -
    made ``_source`` a locator server. Both measured on planted modules that
    touch no filesystem.

    SO THIS SET IS BUILT BY THE HAND-BACK RULE ITSELF, from the primitives
    outward: a name is here when its module-scope binding hands back a locator,
    or when it is a function that serves one. ``_FINDERS =
    locate.resolve_save_root`` is here; ``_HERE = pathlib.Path(__file__).resolve()``
    is not, because a CALL is not a hand-back. The narrowing is exactly the
    callable-versus-value split the container and call arms were removed for
    want of, applied where it can actually be computed.

    IT SEEDS FROM :data:`_LIBRARY_PRIMITIVES` AND NOT FROM THE CALLER'S SET,
    which is the whole point and was got wrong once: seeding from the callee
    vocabulary admits every path constant in it on the first round, and the
    fixpoint then propagates them. The seed is the primitives themselves.

    Args:
        tree: The parsed module.
        attributes: The attribute vocabulary, passed through.
        imported: The imported receiver names, passed through.

    Returns:
        The primitives plus every module-scope name that hands one back, to a
        fixpoint so a chain of servers cannot outrun it.
    """
    bindings = _bindings_in(tree, inside_functions=False)
    serving = set(_LIBRARY_PRIMITIVES)
    for _round in range(len(bindings) + len(_scanned_functions(tree)) + 1):
        grew = False
        frozen = frozenset(serving)
        for bound, value in bindings:
            if _hands_back_a_primitive(value, frozen, attributes, imported):
                for name in bound:
                    if name not in serving:
                        serving.add(name)
                        grew = True
        for name in _handing_back_names(tree, frozen, attributes, imported):
            if name not in serving:
                serving.add(name)
                grew = True
        if not grew:
            break
    return frozenset(serving)


def _reaching_attributes(tree: ast.Module, imported: frozenset[str]) -> frozenset[str]:
    """The ATTRIBUTE names a module makes stand for a primitive.

    CS-492's first two routes, and a SECOND VOCABULARY rather than a wider
    first, which is the whole design. ``self.finder = locate.resolve_save_root``
    bound in ``__init__`` and called from ``account`` was invisible because
    :func:`_aliases_bound_in` holds module scope and function-local scope apart
    - and it must, since a local ``finder`` in one function says nothing about a
    name ``finder`` in the next. The binding is not a local, though. It binds a
    name in the ATTRIBUTE namespace, which no function-local scope owns and no
    module scope owns either, and that is the namespace this returns.

    KEEPING IT SEPARATE IS WHAT AVOIDS THE INVERSION. These names are consulted
    only where :func:`_callee_resolves` already refuses to look at a receiver -
    the ``Attribute`` arm, which asks ``func.attr`` and nothing else - so a bare
    local ``finder()`` in an unrelated function is untouched by them. Folding
    them into the primitive set instead would flag exactly that call, which is
    the inversion the keying note records, pointed a fourth way.

    RECEIVER-BLIND, DELIBERATELY, AND THIS IS THE TRADE. ``self.finder()`` and
    ``_HOLDER.finder()`` and ``whatever.finder()`` all answer the same, because
    deciding WHICH class an expression is an instance of is the type resolution
    :func:`_callee_resolves` already refuses for ``_TABLE.entries["root"]()``.
    Scoping per class would answer the first two and would have to guess at the
    third; answering all three costs a flag only where a module binds a locator
    to an attribute name and then calls something else of that name.

    :data:`_NOT_LIBRARY_REACH` GOVERNS THIS NAMESPACE AS WELL, and it did not
    until a refutation pass walked straight through the gap. That map names
    what does NOT reach, and :func:`_reach_primitives` enforces it by
    INTERSECTING rather than subtracting - CS-497 - so a name in neither
    declaration reaches nothing. This vocabulary had no partition, no map and no
    intersection, so an excluded name re-entered by the back door: a store under
    the name ``walk`` made every ``ast.walk`` call in the module a reach site,
    and ``walk`` is excluded BY NAME for exactly that collision. An exclusion
    that holds in one namespace and not the other is not an exclusion.

    A METHOD THAT HANDS ONE BACK IS HERE TOO, per :func:`_hands_back_a_primitive`,
    because a method name is an attribute name. Reading the store shape and not
    the serve shape would be one mechanism applied to part of its population,
    which is the pattern this item kept turning up.

    A STORE RESOLVES BY SPELLING AND NOT BY MENTION - CS-492 round two. This
    asked :func:`_stands_for_a_primitive`, which reads a mention ANYWHERE inside
    the stored expression, and a refutation pass broke the cost bound this
    docstring used to state. The counter-example holds no locator and touches no
    filesystem: ``monkeypatch.setattr(mod, "banner", _label("home"))`` stores a
    rendered caption, and ``"home"`` is a locator name, so ``banner`` became a
    locator and every ``.banner()`` call in the module acquired a reach
    requirement. Asking :func:`_hands_back_a_primitive` with the string channel
    OFF is the repair: it is the callable question rather than the mention
    question, which is what a store of a locator actually is.

    WHAT THAT COSTS, STATED HONESTLY: a store whose value only MENTIONS a
    primitive - ``self.root = locate.resolve_save_root()``, the RESULT - is no
    longer an attribute that reaches. It never should have been. A store of a
    wrapper naming the primitive as a STRING - ``self.finder =
    operator.methodcaller("glob")`` - is no longer read either, and that one is
    a real narrowing rather than a repair.

    Args:
        tree: The parsed module.
        imported: The names this module binds by importing, per
            :func:`_imported_module_names`, which is what separates a primitive
            spelled on its own module from one spelled on a parameter.

    Returns:
        The attribute names that resolve a primitive, to a fixpoint so a store
        of another such attribute cannot outrun it.
    """
    refused = frozenset(_NOT_LIBRARY_REACH)
    stores = _attribute_stores(tree)
    serves = [
        (name.rsplit(".", 1)[1], node)
        for name, node in _scanned_functions(tree).items()
        if "." in name
    ]
    attributes: set[str] = set()
    for _round in range(len(stores) + len(serves) + 1):
        known = frozenset(attributes)
        # THE HAND-BACK SET, NOT THE CALLEE SET - see :func:`_serving_names`.
        # The callee set holds path constants by design, and a hand-back is the
        # one question for which that is a wrong answer rather than a wide one.
        # It is recomputed each round because the two sets feed each other: a
        # server can hand back a HELD attribute, and an attribute can hold what
        # a server hands back. Both only grow, so the pair still terminates.
        serving = _serving_names(tree, known, imported)
        grew = False
        for attribute, value in stores:
            if attribute in attributes or attribute in refused:
                continue
            if _hands_back_a_primitive(value, serving, known, imported):
                attributes.add(attribute)
                grew = True
        for attribute, node in serves:
            if attribute in attributes or attribute in refused:
                continue
            if any(
                _hands_back_a_primitive(value, serving, known, imported)
                for value in _returned_values(node)
            ):
                attributes.add(attribute)
                grew = True
        if not grew:
            break
    return frozenset(attributes)


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


def _module_scope_reaches(
    tree: ast.Module, primitives: frozenset[str], attributes: frozenset[str] = frozenset()
) -> bool:
    """Whether a primitive is called outside every function in a module.

    Args:
        tree: The parsed module.
        primitives: The reach vocabulary.
        attributes: The attribute vocabulary, per :func:`_reaching_attributes`.
            Handed down for the same reason the function scan gets it: a
            module-scope ``_HOLDER.finder()`` is the same route one indentation
            level out, and every previous half of this guard that read one
            population and not the other was reopened by exactly that move.

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
        _call_reaches_a_primitive(node, primitives, attributes)
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
    primitives, attributes = _reach_vocabulary(tree, _LIBRARY_PRIMITIVES, source=module_path)
    personal = _personal_data_names(tree, source=module_path)
    declared_names = frozenset(graded) | frozenset(exempt)

    direct = frozenset(
        name for name, node in functions.items() if _calls_any(node, primitives, attributes)
    )
    if _module_scope_reaches(tree, primitives, attributes):
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
    primitives, attributes = _reach_vocabulary(tree, _LIBRARY_PRIMITIVES, source=path)
    touched = any(_calls_any(node, primitives, attributes) for node in functions.values())
    return touched or _module_scope_reaches(tree, primitives, attributes)


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
