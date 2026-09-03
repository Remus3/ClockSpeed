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

AND THAT ``from None`` MEASUREMENT WAS GENERALISED ONE STEP TOO FAR. It was
taken on a fixture raising a WRAPPER, where it is correct, and read as a fact
about the FORM. It is not: ``raise exc from None`` suppresses the context and
still renders the binding. The counterexample is measured alongside the
original in the same module, and the verdict order was corrected to match.
CS-857 residual 1.

THE FIVE VERDICTS, AND THE ORDER IS LOAD-BEARING.

  :data:`CLOSED_PATHLESS`    the censused slot - the cause of an explicit
                             chain, or the raised expression of a ``from
                             None`` - is a CALL to a same-module function whose
                             every return builds a builtin ``OSError`` out of
                             ``errno`` and ``strerror`` alone. The second
                             positive clearance, added by CS-884, and it rests
                             on what the callee CONSTRUCTS. The name it is
                             spelled with is read by nothing.
  :data:`CLOSED_SUPPRESSED`  ``from None`` raising something OTHER than the
                             handler's own binding. The FIRST positive
                             clearance, and it rests on a STRUCTURAL fact -
                             the interpreter sets ``__suppress_context__`` and
                             prints no chain - rather than on any property of
                             the value. THE FORM ALONE IS NOT THE CLEARANCE:
                             ``raise exc from None`` prints no chain and
                             prints the binding, filename included. The
                             clearance requires the raise to CONSTRUCT a class
                             this module declares; every other suppressed
                             shape is :data:`UNPROVEN`.
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

AND IT IS ORDERED BEFORE BOTH CLEARANCES FOR THE SAME REASON, WHICH CS-884
MADE A LIVE QUESTION RATHER THAN A THEORETICAL ONE. Its predicate and
:func:`_forwarding_parameters` collide on a shape the tree could grow tomorrow -
a module-level clone function plus a NESTED function of the same name that
forwards its argument - so a positive verdict tested first would launder that
site. The collision is planted, graded and RUN in the census. On that shape the
verdict is a deliberate OVER-report: execution shows the module-level clone is
the one actually called and no marker renders, and the guard still reports the
leak, because between over-reporting and issuing a clearance it cannot prove,
this module takes the first.

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
   fires only when the exception in flight IS the handler's own: the implicit
   and bare forms by construction; the suppressed form only when the raise
   re-raises the handler's bound name; and the explicit form when the cause
   expression IS that name, or is a call to a module-local helper that returns
   that very parameter (:func:`_forwarding_parameters`). An exception stored on
   an object, or passed in as a parameter, is unresolved by construction.

   THE FIRST TWO CLAUSES USED TO READ "the implicit, bare and suppressed forms
   by construction" AND "returned from a call ... is unresolved by
   construction". CS-857 made both false in one session and neither sentence
   was updated with the code; an adjudicator found them. THE PROSE A LATER
   READER CITES IS PART OF THE REPAIR.

4. CALL SITES OUTSIDE THE TRACKED POPULATION ARE UNSWEPT. The sweep is
   ``tests.assertion_rendering_guard.tracked_python_files()``: tracked and
   untracked-but-not-ignored ``*.py``. A gitignored module, a generated one, or
   a dependency is not read at all.

5. THE VERDICT IS ABOUT THE CHANNEL, NOT ABOUT THE VALUE. :data:`MEASURED_LEAK`
   says the traceback renders the cause's ``str()`` and that an ``OSError``'s
   ``str()`` carries ``filename`` when the interpreter set one. It does NOT
   say a personal path reached that site on any given run. Conversely
   :data:`UNPROVEN` does not say a site is safe.

   SO THE VERDICT IS A CONSERVATIVE UPPER BOUND AND PRODUCES PROXY-POSITIVES.
   The leg is SYNTACTIC: it resolves the handler's clause type to a builtin
   ``OSError`` subclass. Nothing about that resolution can know whether the
   call the handler wraps ATTACHES a filename, and an ``OSError`` whose
   ``filename`` the interpreter left None renders no path at all. Two shipped
   sites were measured to be exactly that and are recorded in :data:`EXEMPT`
   with their measurements. THE RECORD CHANGES NO VERDICT - see the note on
   :data:`EXEMPT_RECORDED` - so a proxy-positive stays reported rather than
   being argued away, which is the fail-closed direction.

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

8. A RAISE IN A CALLEE OF A HANDLER IS NOT IN THE ``Site`` POPULATION AT ALL,
   AND IT REMAINS THE LARGEST KNOWN SILENCE. CPython sets ``__context__`` from
   the THREAD's exception state rather than from lexical scope, so a helper
   CALLED from a handler body chains and renders exactly as a graded ``from
   exc`` does - MEASURED at two links with the marker rendered - while this
   module, which walks lexically, derives no ``Site`` for it.

   A SECOND, NARROWER POPULATION NOW SEES PART OF IT, AND ONLY PART.
   :func:`callee_sites` reports an OSError-typed handler whose own scope calls
   a BARE-NAME function defined in the SAME module whose own scope raises with
   NO ``from`` clause. Everything else about the shape is still invisible, and
   each of these was MEASURED to leak and MEASURED not to be derived:

     two levels down            ``h()`` calling ``g()`` which raises. Renders
                                the caller's value at two links; derived: none.
     a dotted or method callee  ``holder.blow_up()``. Same rendering; none.
     an imported callee         not resolved, because this module follows no
                                import - the same silence as limit 2.
     a callee through a value   a variable, a container, a lambda, a decorator.
     ``from inner`` in the      the callee's OWN handler re-chains, and the
     callee's own handler       walk reaches the caller's exception at THREE
                                links. MEASURED, and not derived.

   THE LIVE COUNT IN THE GRADED BUCKET IS ZERO, and that zero is reported with
   its denominator beside it - the handlers whose callee was actually
   FOLLOWED - because a detector that resolved nothing reports the same zero.
   This module's own fixtures are the live positive control.

   CS-857 residual 2 still owns the remainder, and the item's acceptance - a
   universal over every shipped chained raise - is still NOT discharged by
   this. A partial detector narrows a silence; it does not close one.

9. AN ALIASED IMPORT UNDER-REPORTS. ``from builtins import OSError as Boom``
   leaves ``except Boom`` unresolved, because :func:`_resolve_builtin_exception`
   looks the written name up in ``builtins``. Limit 1 names module-level
   SHADOWING and limit 2 names dotted types; neither names ALIASING, and an
   under-report that is unstated is the defect CS-857 residual 4 was filed for.

10. THE FORWARDING RULE RESOLVES ONE SHAPE, NOT A CLASS OF THEM.
   :func:`_call_forwards_binding` matches a bare ``Name`` callee carrying the
   binding POSITIONALLY, whose definition returns that parameter unrebound. A
   keyword call site, a lambda, a dotted or imported callee, a two-step
   forward, a conditional return and a return through a container all still
   grade :data:`UNPROVEN` - measured, by two independent adversaries. So a
   no-op helper is distinguished from a genuine filename-stripping clone for
   the shapes above and NOT in general.

   WHAT CS-884 CHANGED HERE, AND WHAT IT DID NOT. It did NOT narrow this
   silence: all six shapes above still grade :data:`UNPROVEN`, and each is now
   planted, graded AND RUN one arm apiece, with the marker measured to render
   in every one. What changed is the other half of the sentence. Until CS-884
   a genuine clone graded :data:`UNPROVEN` as well, so this limit's six
   under-reports and every shipped REPAIR sat in one bucket and the bucket
   said nothing about either. The clone is now cleared by the positive
   predicate in limit 12 and the six are not, so :data:`UNPROVEN` here means
   "this module cannot tell" again rather than "this module did not look".

11. THE KEY CANNOT SEPARATE TWO IDENTICAL SITES IN ONE FUNCTION. Two raises of
   the SAME class, from the SAME handler type, in the SAME function, chaining
   the SAME expression, produce one key between them. The tracked tree has no
   such pair today - every live key is distinct, which
   ``test_every_site_key_is_distinct`` asserts - and if one ever appears that
   arm goes RED rather than letting one exemption quietly forgive both. The
   line number is deliberately NOT in the key: it would make every key drift on
   any edit above it, which is the dead-citation failure this item was filed
   against. A collision is therefore reported as something to restructure, not
   absorbed.

12. THE PATHLESS CLEARANCE RESOLVES ONE SHAPE OF REPAIR, NOT EVERY SAFE ONE,
   AND EVERY GAP BELOW IS AN UNDER-REPORT RATHER THAN A HOLE.
   :data:`CLOSED_PATHLESS` needs a CALL, in the cause slot or in the raised
   slot of a ``from None``, to a MODULE-LEVEL, UNDECORATED, non-async ``def``
   in the SAME module, every one of whose own-scope returns builds a builtin
   ``OSError`` from exactly two ``errno``/``strerror`` reads off its own
   unrebound parameters. Everything else stays :data:`UNPROVEN`, including
   several repairs that are genuinely safe:

     an INLINE construction     ``raise OSError(exc.errno, exc.strerror) from
                                None`` is filename-free and is NOT cleared.
                                The predicate is about a callee, and widening
                                it to the raise itself was not measured.
     a clone written in place   ``exc = OSError(exc.errno, exc.strerror);
                                return exc`` returns a NAME, so limit 10's
                                rebind rule and this one both decline it.
     a method, an import, a lambda, a nested ``def``
                                the callee must be a bare name defined at
                                module level here, for the reason
                                :func:`_pathless_clone_functions` records.
     a two-step clone           ``def a(e): return b(e)`` is a call, not a
                                construction, and is not followed.

   AND THE VERDICT IS ABOUT ONE SLOT, NOT ABOUT THE SITE. It says the cause
   channel carries no path. It says NOTHING about the wrapper's own ``args``,
   which ``tests/exception_message_guard.py`` owns, and nothing about a note
   attached later. A site can be :data:`CLOSED_PATHLESS` here and still leak
   through a channel this module does not census - limit 5's sentence about
   what a verdict is, one clearance over.

13. A RAISE OF A VALUE A HANDLER STORED, AFTER THAT HANDLER HAS EXITED, IS
   NOT IN THE ``Site`` POPULATION EITHER, AND IT IS THE SECOND WAY OUT OF IT.
   ``last = exc`` inside the handler, then ``raise last`` below the loop:
   :func:`_form_of` answers None - an expression, no ``from`` clause, no
   active handler - so nothing is derived and every count over that population
   reads a zero it did not earn
   (``memory/an-empty-population-satisfies-every-zero.md``). THE RENDERING IS
   A GRADED SITE'S: the stored object IS the caught exception, so its ``str()``
   still appends ``filename`` and ``filename2``, MEASURED in a child
   interpreter whose own excepthook did the rendering.

   :func:`deferred_raise_sites_in_tree` IS A THIRD POPULATION AND IT SEES PART
   OF THIS, exactly as :func:`callee_sites` sees part of limit 8. It reports a
   raise whose expression READS a local that a handler IN THE SAME SCOPE bound
   to its own exception - keyed on that POSITIVE fact and not on the raise
   node's kind, because the tracked tree holds one live ``raise <Name>`` and
   one live ``raise <IfExp>`` of the shape and a kind-keyed leg derives one of
   the two.

   THE STORE IS READ IN FIVE SPELLINGS, and until CS-881 residual 2 it was read
   in ONE. ``ast.Assign`` was the whole rule, so ``last: OSError | None = exc``
   escaped it - an ``ast.AnnAssign`` whose target IS a bare name, and ordinary
   house style in a tree this heavily annotated - and so did the walrus in both
   its spellings and a ``for`` target. All four bind a bare local, in the same
   scope, to the handler's own binding, which is the POSITIVE fact this
   population says it keys on; all four were planted, RUN, and MEASURED to
   render the marker while deriving nothing. :func:`_stored_binding` now reads
   ``ast.Assign``, ``ast.AnnAssign``, ``ast.NamedExpr``, ``ast.For`` and
   ``ast.AsyncFor``, and the refusal that used to cover them was recorded with
   a FALSE reason - "target is not a bare name" is not true of an annotated
   assignment - which is why it is named here rather than quietly deleted.

   The following stay invisible, and NONE of them is refused on paper alone:

     a two-step store           ``kept = exc`` then ``last = kept``. The
                                store's value must be the handler's OWN
                                binding. MEASURED to leak, planted and run.
     a store into a container   ``held.append(exc)`` then ``raise held[0]``.
                                MEASURED to leak, planted and run.
     an attribute target        ``holder.last = exc`` binds no local name.
                                MEASURED to leak, planted and run.
     a subscript target         ``held[0] = exc``. Same, and it is a distinct
                                AST shape rather than a spelling of the row
                                above. MEASURED to leak, planted and run.
     a store crossing a scope   the store and the raise must share a scope
                                path exactly, which is :func:`_walk`'s filter,
                                so a raise inside a nested ``def`` that closes
                                over the store derives nothing. MEASURED to
                                leak, planted and run.
     an augmented store         ``last += exc`` binds what ``__iadd__``
                                returned rather than the caught exception, so
                                it is refused DELIBERATELY - see
                                :func:`_stored_binding` - and not missed.
                                Refused by construction, not measured.
     any other iterable         ``for last in kept:`` and ``for last in (exc,
                                other):`` bind an element this walk cannot
                                name; only a one-element sequence literal is
                                resolved. Refused by construction, not
                                measured.

   THOSE LAST TWO ROWS ARE THE ONLY UNMEASURED ONES, AND THAT DISTINCTION IS
   THE CS-881 RESIDUAL-3 REPAIR. This table and the one in
   :func:`_handler_stores` disagreed about the attribute and subscript family -
   one calling it "refused by construction, not measured", the other calling it
   "MEASURED to leak" - and two tables contradicting each other is worse than
   either being wrong alone, because a reader who finds one has no reason to
   look for the other. Every row either carries a plant that RAN or says
   plainly that it does not.

   ONE SHAPE IS DELIBERATELY LEFT TO :class:`Site`: a deferred raise written
   inside ANOTHER handler, which is already a :data:`FORM_IMPLICIT` site. That
   site's type leg answers about the OTHER handler's clause rather than about
   the stored object, so it is graded and the grade is about the wrong
   exception. Stated here rather than repaired, because repairing it means
   widening :func:`_form_of`, which ``tests/pathless_clone_guard.py`` reads
   directly and derives its own population from.

   AND THE OVER-REPORT IS STATED TOO, because a population that only ever
   reported truly is not what this is. ``raise OSError(last.errno,
   last.strerror)`` reads the stored name, carries no path, and is reported
   anyway - planted, run and MEASURED not to leak. Between over-reporting a
   site and going silent about one this population takes the first.

WHAT AN ADVERSARY WOULD HAVE TO DO TO ESCAPE, CORRECTED TWICE AND STILL NOT A
GUARANTEE. Not a rename: every rename in the table at the top lands in
:data:`UNPROVEN`, which is not a clearance. And renaming the CLONE is not one
either - CS-884's predicate never reads the callee's name, only its returns.
To get a CLEARANCE they would have to write ``from None`` AND CONSTRUCT A CLASS
THIS MODULE DECLARES, which is the only shape whose rendered object is provably
not the caught exception; or write a callee whose EVERY return builds a
two-argument builtin ``OSError`` out of ``errno`` and ``strerror`` off its own
parameters, which is the repair itself and carries no path by construction; or
shadow a builtin exception name at module level, which downgrades a measured
leak to unproven and is reported, not cleared.

THIS PARAGRAPH SAID ``from None`` "genuinely closes the channel" UNTIL CS-857,
AND THAT WAS MEASURED FALSE - ``raise exc from None`` suppresses the CONTEXT
and renders the binding, filename included. The first repair then gated the
clearance on the raised expression not being SPELLED like the binding, and an
adversary measured fifteen spellings that escaped it. Both sentences were
retained one round longer than the code they described.

TO VANISH FROM THE ``Site`` POPULATION they do NOT have to leave every handler
and drop the ``from``, which is what this paragraph used to claim. They need
only put the raise in a CALLEE of the handler - limit 8 - or STORE the
handler's binding in a local and raise it after the handler exits, which needs
no second function at all - limit 13, and the tracked tree holds two of those.

THAT ESCAPE IS NOW NARROWED AND IS NOT CLOSED, AND THE DIFFERENCE MATTERS.
:func:`callee_sites` catches the one-level, bare-name, same-module spelling of
it. An adversary reaches the identical rendering by calling a METHOD, by
calling through an IMPORT, or by putting one more function between the handler
and the raise - all three MEASURED to leak and MEASURED not to be derived. So
this is a smaller silence with a stated shape, not a discharged one, and a
future reader must not cite :func:`callee_sites` as covering limit 8.
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

#: ``from None`` CONSTRUCTING a class the module itself declares. The only
#: positive clearance, and structural.
#:
#: THE SECOND HALF OF THAT SENTENCE IS LOAD-BEARING AND WAS ABSENT UNTIL
#: CS-857 RESIDUAL 1. ``from None`` sets ``__suppress_context__``, which closes
#: the CONTEXT channel. It says nothing about the object being raised. When
#: that object IS the handler's binding - ``raise exc from None`` inside
#: ``except OSError as exc`` - the interpreter prints no chain and prints the
#: binding's own ``str()``, ``filename`` included. Measured: the static verdict
#: read ``closed-suppressed`` while the rendered traceback read
#: ``FileNotFoundError: [Errno 2] No such file or directory: '<marker>'``.
#:
#: AND THE FIRST REPAIR WAS ITSELF INSUFFICIENT. Gating the clearance on the
#: raised expression not being spelled like the handler binding left 15
#: measured escapes. The gate is now :attr:`Site.raises_local_class`.
CLOSED_SUPPRESSED: Final = "closed-suppressed"

#: A CALL, in the cause slot or in the raised slot of a ``from None``, to a
#: same-module function whose every return CONSTRUCTS a filename-free builtin
#: ``OSError``. The second positive clearance, added by CS-884.
#:
#: WHAT IT ASSERTS. The object that reaches the rendered chain through THIS
#: slot was built by the callee out of :data:`CLONE_FIELDS` alone, so it
#: carries no ``filename`` and no ``filename2`` for ``OSError.__str__`` to
#: append. The whole verdict rests on the callee's own ``return`` statements -
#: :func:`_returns_only_pathless_clones` - and on nothing the callee or the
#: call site is SPELLED with. Rename ``_pathless_cause`` to anything and the
#: verdict is unchanged; keep the name and change what it builds and the
#: verdict is gone. ``memory/a-guard-can-measure-spelling.md`` records the
#: round of this item that got that backwards.
#:
#: WHAT IT DOES NOT ASSERT, and reading it as more is the error this module
#: keeps having to correct. It says nothing about the WRAPPER's own message -
#: that is ``args``, which ``tests/exception_message_guard.py`` owns - and
#: nothing about any OTHER channel the same site opens. It is a verdict on the
#: cause slot, which is the only channel this module censuses.
CLOSED_PATHLESS: Final = "closed-pathless"

#: The cause is a builtin ``OSError`` subclass, whose ``str()`` renders the
#: ``filename`` the interpreter attached.
MEASURED_LEAK: Final = "measured-leak"

#: :data:`EXEMPT` records a measured reason for this exact site expression. The
#: constant is spelled apart from the mapping because the mapping owns the bare
#: name, house style; the VALUE is the word the verdict is reported under.
#:
#: AN ENTRY WHOSE SITE RESOLVES TO :data:`TYPE_OSERROR` IS INERT, AND THAT IS
#: THE DESIGN RATHER THAN AN OVERSIGHT. :func:`classify` tests
#: :data:`MEASURED_LEAK` first, so such an entry never reaches this branch and
#: the site keeps reporting as a leak. Two of the four live entries are exactly
#: that: proxy-positives of the syntactic type leg (limit 5), measured not to
#: render a path, recorded so the measurement is not lost, and deliberately
#: NOT given the power to silence anything. Closing such a site needs ``from
#: None`` at the site itself. ``test_an_exemption_cannot_silence_a_measured_
#: leak`` is the arm that keeps this true against a future reordering.
EXEMPT_RECORDED: Final = "exempt"

#: Nothing in the tree proves what this chain can carry.
UNPROVEN: Final = "unproven"

#: The verdicts, strongest first. :data:`MEASURED_LEAK` PRECEDES
#: :data:`EXEMPT_RECORDED` so an exemption cannot silence a measured leak, and
#: it PRECEDES both clearances so a ``from None`` cannot either.
#:
#: THE SECOND PRECEDENCE WAS THE OTHER WAY ROUND UNTIL CS-857 RESIDUAL 1, and
#: that ordering was the defect: it is not enough for a verdict order to be
#: correct in the docstring, it must be correct in the order the CODE tests the
#: branches. Read :func:`classify` top to bottom, not this comment.
#:
#: CS-884 ADDED :data:`CLOSED_PATHLESS` AND PUT IT THIRD, WHICH IS THE WHOLE
#: DECISION IN THAT ITEM. Placing a new positive verdict AHEAD of
#: :data:`MEASURED_LEAK` would launder every real leak the new predicate also
#: happened to match, and the two predicates DO collide on a reachable shape: a
#: module-level clone function plus a NESTED function of the same name that
#: forwards its argument puts the name in :func:`_forwarding_parameters` and in
#: :func:`_pathless_clone_functions` at once. The collision is planted, graded
#: and executed in ``tests/test_chained_cause_census.py``. It is placed AFTER
#: :data:`CLOSED_SUPPRESSED` so that no site which already earned the older
#: clearance changes verdict, which makes the CS-884 delta purely additive.
VERDICT_ORDER: Final = (
    MEASURED_LEAK,
    CLOSED_SUPPRESSED,
    CLOSED_PATHLESS,
    EXEMPT_RECORDED,
    UNPROVEN,
)

#: The ONLY two ``OSError`` attributes a cleared construction may read. Both
#: are interpreter-generated diagnostics: ``errno`` is an integer code and
#: ``strerror`` is the platform's own text for it. Neither is a path, and
#: ``filename`` and ``filename2`` - the two that ARE - are absent by
#: construction rather than by redaction.
CLONE_FIELDS: Final = frozenset({"errno", "strerror"})

#: How many positional arguments a cleared construction carries. THE
#: TWO-ARGUMENT FORM IS LOAD-BEARING AND NOT A STYLE. ``OSError`` grows a
#: ``filename`` at the third position and a ``winerror`` at the fourth, so a
#: four-argument clone re-attaches the very field the clone exists to drop and
#: renders ``[WinError None]`` besides. Every shipped copy of the idiom records
#: having measured that.
_CLONE_ARITY: Final = 2

#: How many elements a sequence literal may hold before :func:`_sole_element`
#: stops being able to say which one a ``for`` target ends up bound to. Named
#: so no bare number sits in that predicate.
_ONE_ELEMENT: Final = 1

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

#: The shipped advice path, named for WHAT IT IS rather than for what this
#: module grades. IT IS NOT A POPULATION THIS MODULE MEASURES OVER, and it must
#: never be used as one: every population here is decided by :func:`bucket_of`
#: and each is wider than this prefix.
#:
#: IT WAS THE GRADED POPULATION UNTIL CS-879, AND THAT WAS THE DEFECT. A flat
#: prefix test made the split a statement about a directory name, so three
#: sites in non-frozen ``scripts/`` and ``tools/`` files were graded by nothing
#: and reported by nothing while a comment here asserted they were both.
#:
#: AND IT WAS STILL THE ``__notes__`` POPULATION UNTIL CS-883, WHICH IS THE
#: SAME DEFECT SURVIVING IN THE OTHER CENSUS IN THIS FILE. The comment here
#: read that the note zero was "legitimately scoped to the advice path, which
#: is the only claim this constant carries", and CS-879 had already made that
#: false: 101 of the 139 graded modules were outside the note census, so a note
#: attached in any of them rendered in a traceback that nothing looked at. The
#: two censuses now read one classifier. WHAT THE CONSTANT IS FOR NOW is the
#: opposite direction - ``test_every_advice_layer_module_is_graded`` asserts
#: the shipped path can never be relabelled OUT of a population - plus naming
#: the narrower scope the CS-883 arms measure the widening against.
ADVICE_LAYER: Final = "clockspeed/"

#: The modules whose chained raises are THIS CENSUS'S OWN PLANTED CONTROLS.
#: They are excluded from grading because their raises exist to prove the
#: detector fires on the live git sweep and not only on a string; grading
#: them would grade the instrument by its own readings.
#:
#: AN EXACT LIST, NOT A DIRECTORY PREFIX, AND CS-879 ROUND 2 IS WHY. This
#: was ``tests/``, which swept in five modules that plant nothing: the
#: census's own production logic, two synthetic-save builders and two other
#: guards. The stated reason was false of five of the seven modules it
#: excluded - a worse ratio than the false comment CS-879 was opened
#: against - and the seven sites it wrongly covered were real repairable
#: code excused by a sentence about fixtures. A prefix cannot tell a
#: planted control from a neighbour that merely shares its directory; an
#: exact list can, and adding to it is a deliberate act that
#: ``tests/test_chained_cause_census.py`` grades on both directions.
CONTROL_MODULES: Final = (
    "tests/test_chained_cause.py",
    "tests/test_chained_cause_census.py",
)

#: The roots this taxonomy has actually reasoned about. NOT a restatement of
#: the module map ``CLAUDE.md`` section 2.1 owns - it is this module's own
#: declaration of the domain over which its buckets carry a stated reason.
#:
#: THIS IS WHAT MAKES EXHAUSTIVENESS CHECKABLE RATHER THAN VACUOUS. A taxonomy
#: whose last branch is a catch-all is exhaustive by construction and therefore
#: proves nothing: a Python file appearing under a fifth root - ``shell/``,
#: say, which ``CLAUDE.md`` section 2.1 describes as Node - would be swept up
#: and silently graded although nobody had decided it should be. Naming the
#: domain turns that into a red arm and a decision.
#:
#: THE SENTINEL GUARDS THE OMISSION DIRECTION ONLY, and saying otherwise was
#: a CS-879 round 2 finding. A root MISSING from this tuple reddens, because
#: its files reach no bucket. A root ADDED to it does not, because widening
#: the domain is exactly the deliberate act this constant exists to record.
#: The addition direction is graded separately, by the arm asserting every
#: root declared here actually holds tracked Python: a root with nothing in
#: it is a domain widened for free, which is the shape that lets an
#: unreviewed scope in without a decision.
SWEPT_ROOTS: Final = ("clockspeed/", "scripts/", "tests/", "tools/")

#: Bucket 1. Code an agent may repair today whose raises are not this
#: census's own planted controls, so a verdict on it is ACTIONABLE. NOT
#: ``shipped``: that word was accurate while the bucket held only
#: ``clockspeed/``, and CS-879 round 2 widened it to test-support modules
#: that ship to nobody and are repairable all the same. What the bucket is
#: actually about is whether a verdict can be acted on. Everything a chained
#: raise can leak - a home path, an account id, a world name - leaks the
#: same way out of a tool or a guard as out of the advice path, and
#: ``CLAUDE.md`` non-negotiables 3, 11 and 12 are repo-wide rather than
#: scoped to ``clockspeed/``.
BUCKET_GRADED: Final = "graded"

#: Bucket 2. Shipped code an agent may NOT repair without an adjudicator grant
#: recorded in ``docs/LEDGER.md`` (``CLAUDE.md`` section 6). Derived and
#: reported on every run so the sites stay visible; never graded, because a
#: graded verdict is a request to edit and this module may not make one.
BUCKET_FROZEN: Final = "frozen-recorded"

#: Bucket 3. This census's own planted controls - see :data:`CONTROL_MODULES`.
#: Recorded rather than dropped, so the census accounts for every site it
#: derived.
BUCKET_CONTROL: Final = "control-excluded"

#: The buckets that carry a stated reason. A module reaching NONE of them is
#: :data:`BUCKET_UNCLASSIFIED`, which is deliberately absent from this tuple so
#: that ``bucket_of(module) in BUCKETS`` is a real question with a reachable
#: negative answer.
BUCKETS: Final = (BUCKET_GRADED, BUCKET_FROZEN, BUCKET_CONTROL)

#: The buckets :func:`out_of_scope_record` renders. DELIBERATELY NOT "every
#: bucket that is not graded": rendering on ``not is_graded`` would make the
#: record a catch-all, an unclassified site would land in it, and the census
#: arm asserting every site is graded-or-recorded would pass on exactly the
#: shape it exists to catch. The two populations must leave a hole for the
#: sentinel to fall through.
RECORDED_BUCKETS: Final = (BUCKET_FROZEN, BUCKET_CONTROL)

#: The sentinel for a module outside :data:`SWEPT_ROOTS`. NOT A BUCKET - it is
#: the absence of one, and the census reddens on it rather than guessing.
BUCKET_UNCLASSIFIED: Final = "unclassified"

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
        raises_local_class: Whether the raise CONSTRUCTS a class the module
            itself declares. THE FACT :data:`CLOSED_SUPPRESSED` RESTS ON, and
            it is a positive one - see :func:`_local_classes`.
        constructs_pathless_clone: Whether the slot this module censuses - the
            cause of an explicit chain, or the raised expression of a ``from
            None`` - is a CALL to a same-module function whose every return
            builds a filename-free builtin ``OSError``. THE FACT
            :data:`CLOSED_PATHLESS` RESTS ON, and it is positive in the same
            way: it reads what the callee CONSTRUCTS, never what it is called.
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
    raises_local_class: bool = False
    constructs_pathless_clone: bool = False

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
        """Whether this module grades the site.

        DERIVED FROM :func:`bucket_of`, WHICH DERIVES THE SPLIT FROM THE FROZEN
        LIST. It was a flat ``clockspeed/`` prefix test until CS-879, which
        made the split a claim about a directory name; frozenness, the fact the
        split is actually about, played no part in it.

        Returns:
            True when the site is in :data:`BUCKET_GRADED`.
        """
        return bucket_of(self.module) == BUCKET_GRADED


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
#: EVERY entry below was measured by RUNNING the failing call and reading the
#: rendering, not by reading the class, and every one is re-measured on every
#: run by an arm in ``tests/test_chained_cause_census.py``.
#:
#: THE FOUR ENTRIES ARE NOT FOUR OF A KIND. The two ``docs_extract.py`` entries
#: sit on sites the type leg does NOT resolve to an ``OSError``, so their
#: exemption is REACHED and does silence an :data:`UNPROVEN` site. The two
#: ``server.py`` entries sit on sites that DO resolve, so they are INERT by
#: construction - see the note on :data:`EXEMPT_RECORDED`. Both kinds are kept
#: here because the value of an entry is the measurement it records, and a
#: measurement that changes no verdict is still the thing a later session would
#: otherwise have to take on trust or repeat.
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


def _local_classes(tree: ast.Module) -> frozenset[str]:
    """Classes this module itself defines.

    THE CLEARANCE RESTS ON THIS AND ON NOTHING ELSE. ``from None`` closes the
    context channel; what remains open is the object being raised. Proving that
    object is not the handler's exception by SPELLING is what CS-857 round 1
    got wrong - ``kept = exc; raise kept from None`` spells differently and is
    the same object. Proving it POSITIVELY - the raise constructs a class
    declared in this very module, so it cannot be the caught builtin - holds
    however the binding is spelled, and is what round 2 tests instead.

    Args:
        tree: The parsed module.

    Returns:
        The declared class names.
    """
    return frozenset(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _raises_local_class(node: ast.Raise, local: frozenset[str]) -> bool:
    """Whether the raise CONSTRUCTS a class this module declares.

    Args:
        node: The raise.
        local: The declared class names.

    Returns:
        True only for ``raise LocalClass(...)``. A bare name, an attribute, a
        subscript, a walrus, a conditional and a builtin constructor all come
        back False and are therefore never cleared.
    """
    return (
        isinstance(node.exc, ast.Call)
        and isinstance(node.exc.func, ast.Name)
        and node.exc.func.id in local
    )


#: Statements that bind through a single ``target`` field. Grouped so
#: :func:`_rebound_names` reads them on one branch: they differ in what they
#: MEAN and not at all in where the bound name is written.
_TARGETED_STATEMENTS: Final = (
    ast.AnnAssign,
    ast.AugAssign,
    ast.NamedExpr,
    ast.For,
    ast.AsyncFor,
)


def _bound_by(node: ast.expr | None) -> frozenset[str]:
    """The names one assignment TARGET binds.

    Args:
        node: The target expression, or None for an absent one.

    Returns:
        Every bare name the target binds, unpacking tuples, lists and stars. An
        attribute or a subscript target binds no NAME at all and returns empty.
    """
    if isinstance(node, ast.Name):
        return frozenset({node.id})
    if isinstance(node, (ast.Tuple, ast.List)):
        found: set[str] = set()
        for element in node.elts:
            found |= _bound_by(element)
        return frozenset(found)
    if isinstance(node, ast.Starred):
        return _bound_by(node.value)
    return frozenset()


def _rebound_names(node: ast.AST) -> frozenset[str]:
    """Every name REBOUND anywhere beneath a node, nested scopes included.

    WIDER THAN :func:`_own_scope` ON PURPOSE, AND THAT DIRECTION IS THE SAFE
    ONE. This feeds :func:`_returns_only_pathless_clones`, where the question is
    whether the object a construction reads its fields off is still the
    parameter the caller handed in. A nested ``def`` declaring ``nonlocal exc``
    and assigning to it reaches the enclosing parameter, so a walk bounded to
    the outer scope would miss it; the assignment itself is visible to
    ``ast.walk`` wherever it is written, so scanning the whole subtree catches
    that shape without modelling ``nonlocal`` at all. Every extra name this
    returns can only WITHDRAW a clearance, never invent one.

    Args:
        node: The subtree to scan.

    Returns:
        The rebound names.
    """
    bound: set[str] = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Assign):
            for target in inner.targets:
                bound |= _bound_by(target)
        elif isinstance(inner, _TARGETED_STATEMENTS):
            bound |= _bound_by(inner.target)
        elif isinstance(inner, ast.withitem):
            bound |= _bound_by(inner.optional_vars)
        elif isinstance(inner, ast.ExceptHandler) and inner.name:
            bound.add(inner.name)
        elif isinstance(inner, (ast.Import, ast.ImportFrom)):
            bound |= {alias.asname or alias.name.split(".")[0] for alias in inner.names}
        elif isinstance(inner, _NAMED_SCOPES):
            bound.add(inner.name)
    return frozenset(bound)


def _module_level_rebindings(tree: ast.Module) -> frozenset[str]:
    """Names bound at module level by anything OTHER than a plain ``def``.

    WITHOUT THIS THE CLEARANCE IS DEFEATED BY ONE LINE. A module may declare
    ``def _clone(exc): return OSError(exc.errno, exc.strerror)`` and then write
    ``_clone = something_else`` - or ``class _clone``, or ``from x import
    _clone`` - below it. What the name means at import time is the LAST
    binding, so a map built from the ``def`` alone would clear a call to
    something this module never read. Every such name is subtracted rather
    than resolved, which is the fail-closed answer to a question this module
    does not model.

    Args:
        tree: The parsed module.

    Returns:
        The names to subtract from the clone map.
    """
    bound: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound |= _rebound_names(node)
    return frozenset(bound)


def _reads_clone_field(argument: ast.expr, parameters: frozenset[str]) -> bool:
    """Whether one argument is a :data:`CLONE_FIELDS` read off a parameter.

    Args:
        argument: The argument as written.
        parameters: The enclosing function's own unrebound parameter names.

    Returns:
        True only for ``<parameter>.errno`` and ``<parameter>.strerror``. A read
        off a module global, an attribute chain, a subscript, a call result and
        a starred argument all come back False, so a construction that reads its
        fields off a DIFFERENT object than the one the caller handed in is never
        cleared.
    """
    return (
        isinstance(argument, ast.Attribute)
        and argument.attr in CLONE_FIELDS
        and isinstance(argument.value, ast.Name)
        and argument.value.id in parameters
    )


def _is_pathless_construction(
    value: ast.expr | None, parameters: frozenset[str], shadowed: frozenset[str]
) -> bool:
    """Whether one returned expression BUILDS a filename-free builtin OSError.

    THE FOUR CLAUSES ARE FOUR MEASURED REFUSALS, not four ways of saying the
    same thing:

      a builtin OSError callee   ``OSError(...)`` and its subclasses only. A
                                 project class could carry anything in its
                                 ``str()``, and this module cannot read it.
      no keyword arguments       ``OSError`` takes none. The keyword spelling
                                 does not construct at all, so a site written
                                 that way fails at the raise rather than
                                 rendering something safe.
      exactly :data:`_CLONE_ARITY` positional arguments
                                 the third is ``filename`` and the fourth is
                                 ``winerror``, so a longer call re-attaches the
                                 path.
      every argument a :data:`CLONE_FIELDS` read off a parameter
                                 ``OSError(exc.errno, exc.filename)`` is
                                 refused by the field set, and
                                 ``OSError(other.errno, other.strerror)`` by
                                 the parameter set.

    Args:
        value: The returned expression, or None for a bare ``return``.
        parameters: The enclosing function's own unrebound parameter names.
        shadowed: Builtin names the module binds itself, so a module that
            rebinds ``OSError`` cannot have its rebinding cleared as one.

    Returns:
        True when the construction can carry no path.
    """
    if not isinstance(value, ast.Call) or value.keywords:
        return False
    if not isinstance(value.func, ast.Name):
        return False
    built = _resolve_builtin_exception(value.func.id, shadowed)
    if built is None or not issubclass(built, OSError):
        return False
    if len(value.args) != _CLONE_ARITY:
        return False
    return all(_reads_clone_field(argument, parameters) for argument in value.args)


def _returns_only_pathless_clones(node: ast.FunctionDef, shadowed: frozenset[str]) -> bool:
    """Whether EVERY return in a function's own scope builds a pathless clone.

    ``EVERY``, AND THE EMPTY CASE IS REFUSED RATHER THAN WON. A function with no
    ``return`` at all satisfies "every return is a clone" vacuously and returns
    ``None``, which in the cause slot is a different thing entirely. An empty
    population satisfying a universal is the defect this whole module is built
    against, so a function with no return and a function with no parameter both
    come back False.

    A DECORATED FUNCTION IS REFUSED OUTRIGHT. A decorator may return any object
    at all, so the ``def`` below it stops being evidence about what the name
    means. An ``async def`` is refused by the caller for the same class of
    reason: what it returns is a coroutine, not the exception the ``def`` body
    names.

    Args:
        node: The module-level function definition.
        shadowed: Builtin names the module binds itself.

    Returns:
        True when the function can only ever hand back a path-free clone.
    """
    if node.decorator_list:
        return False
    declared = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    parameters = frozenset(argument.arg for argument in declared) - _rebound_names(node)
    if not parameters:
        return False
    returns = [inner for inner in _own_scope(node) if isinstance(inner, ast.Return)]
    if not returns:
        return False
    return all(_is_pathless_construction(inner.value, parameters, shadowed) for inner in returns)


def _pathless_clone_functions(tree: ast.Module, shadowed: frozenset[str]) -> frozenset[str]:
    """Module-level functions that can only ever return a path-free clone.

    MODULE LEVEL ONLY, AND FOR THE OPPOSITE REASON TO
    :func:`_forwarding_parameters`. That map may union across scopes because a
    wider answer there can only make a verdict STRICTER. Here a wider answer
    issues a CLEARANCE, so a bare name resolved across scopes - a method, a
    nested ``def``, a same-named helper in another function - would clear a call
    that never reaches it. The cost is an under-report: a clone written as a
    method or inside a closure is not cleared, and that is stated in limit 12.

    A NAME DEFINED TWICE TAKES THE CONJUNCTION rather than the last definition.
    Only the last binding is live at import time, so the conjunction is
    strictly stricter than the truth, which is the direction a clearance must
    err in.

    Args:
        tree: The parsed module.
        shadowed: Builtin names the module binds itself.

    Returns:
        The qualifying function names.
    """
    verdicts: dict[str, bool] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        qualifies = isinstance(node, ast.FunctionDef) and _returns_only_pathless_clones(
            node, shadowed
        )
        verdicts[node.name] = verdicts.get(node.name, True) and qualifies
    rebound = _module_level_rebindings(tree)
    return frozenset(name for name, holds in verdicts.items() if holds and name not in rebound)


def _constructs_pathless_clone(node: ast.Raise, form: str, clones: frozenset[str]) -> bool:
    """Whether the censused slot is a CALL to a qualifying clone function.

    WHICH SLOT DEPENDS ON THE FORM, and only two forms have one:

      :data:`FORM_EXPLICIT`    ``raise Wrapper(...) from clone(exc)``. The cause
                               slot holds the clone, and ``raise X from Y`` sets
                               ``__suppress_context__``, so the caught original
                               is not rendered underneath either.
      :data:`FORM_SUPPRESSED`  ``raise clone(exc) from None``. The clone IS the
                               object raised and the context is suppressed
                               outright.

    :data:`FORM_IMPLICIT` IS DELIBERATELY ABSENT. ``raise clone(exc)`` with no
    ``from`` clause leaves ``__context__`` pointing at the caught original,
    which the formatter then prints in full underneath "During handling of the
    above exception" - both paths intact, on an exception whose own filename
    fields are empty. ``scripts/make_cert.py`` records having measured exactly
    that before its sites were written, and the census re-measures it.

    Args:
        node: The raise.
        form: Its form.
        clones: The qualifying function names in this module.

    Returns:
        True when the slot is a bare-name call to one of them. A dotted callee,
        an imported name, a call through a variable and a lambda are all False.
    """
    if form == FORM_EXPLICIT:
        candidate = node.cause
    elif form == FORM_SUPPRESSED:
        candidate = node.exc
    else:
        return False
    return (
        isinstance(candidate, ast.Call)
        and isinstance(candidate.func, ast.Name)
        and candidate.func.id in clones
    )


def _forwarding_parameters(tree: ast.Module) -> Mapping[str, frozenset[int]]:
    """Functions that RETURN one of their own parameters, by position.

    RESIDUAL 3. ``raise X(...) from _helper(exc)`` is a ``Call`` the type leg
    cannot resolve, so it graded :data:`UNPROVEN` - and so did
    ``from _identity(exc)``, a no-op an adversary planted beside the real
    repair. The census GRADED THE TWO IDENTICALLY, which is the whole defect.

    This resolves ONE direction only: a helper that hands its argument straight
    back carries the handler's exception, so the site inherits the handler's
    type and can reach :data:`MEASURED_LEAK`. A helper that does anything else
    stays :data:`UNPROVEN`. THAT ASYMMETRY IS DELIBERATE - this function can
    only ever make a verdict STRICTER, so it cannot invent a false clearance,
    which is the failure mode this module has produced three sessions running.
    The genuine repair therefore stays unproven to the census and is proven by
    the runtime arms instead; the two halves are named in the CS-857 note.

    A NAME COLLISION ACROSS SCOPES RESOLVES TO THE UNION OF POSITIONS, which
    is the strict direction ONLY AT EQUAL ARITY. A method and a function
    sharing a name do not collide usefully, because ``self`` shifts every
    index by one; round 1 claimed the union made every same-named callee
    suspect and adversary L2 measured that false. The union is kept because it
    can only ever add a position, and an added position can only make a
    verdict stricter - never a clearance.

    TWO SHAPES ARE DELIBERATELY NOT COUNTED, both measured as FALSE POSITIVES
    in round 1. A parameter REBOUND anywhere in the body is not forwarded by a
    later ``return`` of that name - which is how the genuine repair written in
    place, ``exc = OSError(exc.errno, exc.strerror); return exc``, was graded a
    leak. And a nested function's ``return`` belongs to the nested function,
    not to the enclosing one; walking the whole subtree attributed a closure's
    return to its parent. Both now fall to UNPROVEN, a silence rather than a
    verdict in either direction.

    Args:
        tree: The parsed module.

    Returns:
        Function name to the parameter positions it returns unchanged.
    """
    forwarding: dict[str, set[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        positional = [arg.arg for arg in node.args.posonlyargs + node.args.args]
        body = list(_own_scope(node))
        returned = {
            inner.value.id
            for inner in body
            if isinstance(inner, ast.Return) and isinstance(inner.value, ast.Name)
        }
        rebound: set[str] = set()
        for inner in body:
            if isinstance(inner, ast.Assign):
                rebound |= {t.id for t in inner.targets if isinstance(t, ast.Name)}
            elif isinstance(inner, (ast.AnnAssign, ast.AugAssign)) and isinstance(
                inner.target, ast.Name
            ):
                rebound.add(inner.target.id)
        hits = {
            index
            for index, name in enumerate(positional)
            if name in returned and name not in rebound
        }
        if hits:
            forwarding.setdefault(node.name, set()).update(hits)
    return {name: frozenset(hits) for name, hits in forwarding.items()}


def _own_scope(node: ast.AST) -> Iterator[ast.AST]:
    """Every node in a function's OWN scope, not descending into a nested one.

    Args:
        node: The function definition.

    Yields:
        Each node executing in this function's frame.
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        current = stack.pop()
        yield current
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(current))


def _call_forwards_binding(
    cause: ast.expr | None, handler_name: str, forwarding: Mapping[str, frozenset[int]]
) -> bool:
    """Whether a call cause hands the handler's own binding straight back.

    Args:
        cause: The cause expression as written.
        handler_name: The handler's ``as`` binding, empty when unbound.
        forwarding: The map from :func:`_forwarding_parameters`.

    Returns:
        True when the cause is ``helper(..., exc, ...)`` and ``helper`` returns
        that very parameter, so what chains IS the handler's exception.
    """
    if not handler_name or not isinstance(cause, ast.Call):
        return False
    if not isinstance(cause.func, ast.Name):
        return False
    positions = forwarding.get(cause.func.id)
    if not positions:
        return False
    return any(
        index in positions
        for index, argument in enumerate(cause.args)
        if isinstance(argument, ast.Name) and argument.id == handler_name
    )


def _form_of(node: ast.Raise, handler: ast.ExceptHandler | None) -> str | None:
    """Decide which of :data:`FORMS` a raise is, if any.

    Args:
        node: The raise.
        handler: The innermost handler whose body it sits in, or None.

    Returns:
        The form, or None when the raise opens no chain at all - a plain
        ``raise X(...)`` outside every handler. That answer is the MAJORITY of
        the tracked tree's raises and is deliberately not in the population.

        NO COUNT IS WRITTEN HERE, AND THE PAIR THAT USED TO BE WAS WRONG IN
        BOTH HALVES. It was filed by CS-857, was never derived again, and had
        drifted by more than eighty raises before an adjudicator re-measured it
        - a hardcoded count in a doc being a lie with a timestamp on it,
        ``CLAUDE.md`` section 4. The partition is DERIVED and reported on every
        run by ``test_the_uncensused_raise_partition_is_derived_not_written``,
        which also fails on any transcribed pair that has gone stale, so a
        future reader gets a live number rather than a dead one.
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


def _in_flight_type(
    form: str,
    raised: str,
    cause_expr: str,
    handler_name: str,
    handler_type: str,
    forwards: bool,
) -> bool:
    """Whether the exception the traceback renders IS the handler's own.

    THE IMPLICIT AND BARE FORMS carry the handler's exception by construction:
    one chains it through ``__context__``, the other re-raises it outright.

    THE EXPLICIT FORM does so when the cause expression is exactly the
    handler's bound name, which is what sends ``from kept`` to
    :data:`TYPE_UNRESOLVED` instead of a verdict it has not earned - or when
    the cause is a call that hands that binding straight back, which is
    ``forwards`` and is CS-857 residual 3.

    THE SUPPRESSED FORM DOES NOT, AND SAYING IT DID WAS CS-857 RESIDUAL 1.
    ``from None`` closes ``__context__`` and says nothing about the object
    being raised, so the handler's exception reaches the traceback only when
    the raise re-raises the binding itself. Reading this leg as "suppressed, so
    the type is in flight" cost nothing while it fed a branch that was tested
    after the clearance; it is load-bearing now that the clearance is tested
    second.

    Args:
        form: The site's form.
        raised: The raised callee as written.
        cause_expr: The cause channel as written.
        handler_name: The handler's ``as`` binding, empty when unbound.
        handler_type: The handler clause type, :data:`NO_HANDLER` when there is
            no handler.
        forwards: Whether a call cause returns the handler's own binding.

    Returns:
        True when the handler's clause type describes what will render.
    """
    if handler_type == NO_HANDLER:
        return False
    if form == FORM_EXPLICIT:
        return forwards or (bool(handler_name) and cause_expr == handler_name)
    if form == FORM_SUPPRESSED:
        return bool(handler_name) and raised == handler_name
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
    forwarding = _forwarding_parameters(tree)
    local = _local_classes(tree)
    clones = _pathless_clone_functions(tree, shadowed)
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
        raised = _raised_expression(node)
        forwards = _call_forwards_binding(node.cause, handler_name, forwarding)
        in_flight = _in_flight_type(form, raised, cause_expr, handler_name, handler_type, forwards)
        cause_type = TYPE_UNRESOLVED
        if in_flight and handler is not None:
            cause_type = _type_of(handler.type, shadowed)
        yield Site(
            module=module,
            lineno=node.lineno,
            qualname=".".join(scope) or MODULE_SCOPE,
            form=form,
            raised=raised,
            cause_expr=cause_expr,
            handler_type=handler_type,
            handler_name=handler_name,
            cause_type=cause_type,
            raises_local_class=_raises_local_class(node, local),
            constructs_pathless_clone=_constructs_pathless_clone(node, form, clones),
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
# RESIDUAL 2 - a raise in a CALLEE of a handler. A SECOND, NARROWER POPULATION.
#
# DELIBERATELY NOT FOLDED INTO :class:`Site`. A ``Site`` is a raise this module
# can grade; the records below are HANDLERS, and the raise that leaks is in
# another function entirely. Merging them would let a ``CalleeSite`` be counted
# by an arm that says "every graded site carries a verdict", and this detector
# issues NO verdict - it reports a shape and a denominator, nothing more.
# ---------------------------------------------------------------------------

#: What a callee raise must look like to render the CALLER's exception, and
#: every clause was MEASURED rather than reasoned about
#: (``tests/test_chained_cause_census.py``, the residual-2 arms).
#:
#:   ``raise X(...)`` no ``from``   2 links, the caller's marker RENDERED.
#:   bare ``raise``                 1 link, the caller's exception ITSELF.
#:   ``raise X(...) from None``     1 link, marker absent. NOT a finding.
#:   ``raise X(...) from param``    2 links, marker absent - the explicit cause
#:                                  displaces the context. NOT a finding, and
#:                                  the reason the rule reads ``cause is None``
#:                                  rather than "the callee raises".
#:
#: THE THIRD AND FOURTH ROWS ARE WHY THIS IS NOT "does the callee raise". A
#: detector asking only that would report both of them, and both were measured
#: NOT to render the caller's value.
CALLEE_CHAINS_WHEN: Final = "raise-without-from"

#: A callee this detector resolved to a plain function in the same module.
CALLEE_RESOLVED: Final = "resolved"

#: A callee it could not follow: a dotted or attribute callee, an imported
#: name, a local variable, or anything not a bare ``Name``. MEASURED to leak
#: identically - a method callee renders the caller's marker at 2 links - so
#: this is an UNDER-REPORT and never a clearance.
CALLEE_OPAQUE: Final = "opaque"


@dataclass(frozen=True)
class CalleeSite:
    """One handler that calls a same-module function whose body can chain.

    Attributes:
        module: Repo-relative path.
        handler_lineno: The ``except`` clause line. The raise that actually
            leaks is at :attr:`callee_lineno`, in another function.
        qualname: Dotted enclosing scope of the HANDLER.
        handler_type: The ``except`` clause type as written.
        callee: The called function's name as written.
        callee_lineno: Where that function is defined.
    """

    module: str
    handler_lineno: int
    qualname: str
    handler_type: str
    callee: str
    callee_lineno: int

    @property
    def key(self) -> str:
        """The site expression, keyed like :attr:`Site.key` and for one reason.

        Returns:
            ``module::qualname::handler_type::callee``. NO LINE NUMBER, so the
            key survives an edit above it - the dead-citation failure CS-857
            was filed against.
        """
        return f"{self.module}::{self.qualname}::{self.handler_type}::{self.callee}"


@dataclass(frozen=True)
class HandlerReach:
    """One OSError-typed handler this detector examined, and how far it saw.

    THE DENOMINATOR, AND IT EXISTS BECAUSE THE NUMERATOR IS ZERO. The tracked
    tree contains no live :class:`CalleeSite` today, and an empty population
    satisfies every zero: a detector that reads nothing reports the same count
    as one that read the tree and found nothing. Recording what was RESOLVED
    separates those two, and recording what was OPAQUE states the under-report
    instead of implying there is none.

    Attributes:
        module: Repo-relative path.
        handler_lineno: The ``except`` clause line.
        qualname: Dotted enclosing scope.
        handler_type: The clause type as written.
        resolved: Callees followed to a plain function in this module.
        opaque: Callees this detector cannot follow - see
            :data:`CALLEE_OPAQUE`.
    """

    module: str
    handler_lineno: int
    qualname: str
    handler_type: str
    resolved: tuple[str, ...]
    opaque: tuple[str, ...]


def _chaining_functions(tree: ast.Module) -> Mapping[str, int]:
    """MODULE-LEVEL functions whose OWN scope raises WITHOUT a ``from`` clause.

    ``cause is None`` covers both measured chaining forms and neither of the
    two measured non-chaining ones - see :data:`CALLEE_CHAINS_WHEN`.

    A raise inside a nested ``def`` belongs to that function, not to this one,
    so :func:`_own_scope` bounds the walk. That is the same rule
    :func:`_forwarding_parameters` learned the hard way.

    MODULE LEVEL ONLY, AND THAT IS A REPAIR RATHER THAN A SIMPLIFICATION. This
    walked the WHOLE tree and keyed by BARE NAME, so two functions sharing a
    name in different scopes were one entry. A planted module with a nested
    ``_inner`` that raises made an unrelated ``_inner()`` call in another
    function report a finding - a FALSE POSITIVE, which for a detector is the
    forbidden direction: it claims more than it sees.
    :func:`_forwarding_parameters` may union across scopes because a wider
    answer there can only make a verdict STRICTER; here a wider answer invents
    a finding, so the two cannot share a policy.

    THE GATE IS ACTUALLY :func:`_defined_functions`, AND SAYING OTHERWISE HERE
    WOULD BE THE DRIFT THIS FILE KEEPS CATCHING IN ITSELF.
    :func:`_module_callee_records` tests membership of ``defined`` FIRST and
    only then consults this mapping, so a name absent from ``defined`` never
    reaches these entries at all. Restricting THIS walk as well is therefore
    not the enforcement - it is what keeps the two from disagreeing about what
    a callee name means. Measured: mutating either walk ALONE to ``ast.walk``
    changes no output, and only mutating BOTH reproduces the false positive.
    ``test_a_nested_def_callee_is_recorded_opaque_and_never_resolved`` grades
    the rule directly for that reason.

    The cost is stated rather than hidden: a nested ``def`` is now unresolvable
    and its call is recorded :data:`CALLEE_OPAQUE`, an under-report.

    Args:
        tree: The parsed module.

    Returns:
        Function name to its definition line. A name bound twice at module
        level keeps the LAST definition, which is the one actually bound at
        import time.
    """
    chaining: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(isinstance(inner, ast.Raise) and inner.cause is None for inner in _own_scope(node)):
            chaining[node.name] = node.lineno
        else:
            chaining.pop(node.name, None)
    return chaining


def _module_class_names(tree: ast.Module) -> frozenset[str]:
    """Every class name the module declares.

    Calling one is a CONSTRUCTOR call, not a jump into a body that could raise
    into the caller's context - ``__init__`` is a nested scope with its own
    frame. Excluding them stops the detector reporting the wrapper construction
    that :class:`Site` already grades.

    Args:
        tree: The parsed module.

    Returns:
        The declared class names.
    """
    return frozenset(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _handlers_with_calls(
    tree: ast.Module, shadowed: frozenset[str]
) -> Iterator[tuple[ast.ExceptHandler, tuple[str, ...], list[ast.Call]]]:
    """Every OSError-typed handler, with the calls in its OWN scope.

    Reuses :func:`_walk`, so the scope filter is the one the rest of this
    module already obeys: a call inside a nested ``def`` runs in ITS frame with
    its own ``sys.exc_info()`` and is not this handler's chain.

    Args:
        tree: The parsed module.
        shadowed: Builtin names the module binds itself.

    Yields:
        The handler, its scope path, and the calls in its own scope.
    """
    scopes: dict[int, tuple[str, ...]] = {}
    calls: dict[int, list[ast.Call]] = {}
    handlers: dict[int, ast.ExceptHandler] = {}
    for node, scope, handler in _walk(tree, (), None):
        if handler is None:
            continue
        handlers.setdefault(id(handler), handler)
        scopes.setdefault(id(handler), scope)
        if isinstance(node, ast.Call):
            calls.setdefault(id(handler), []).append(node)
    for marker, handler in handlers.items():
        found = calls.get(marker, [])
        if found and _type_of(handler.type, shadowed) == TYPE_OSERROR:
            yield handler, scopes[marker], found


def _module_callee_records(
    module: str, tree: ast.Module
) -> tuple[list[CalleeSite], list[HandlerReach]]:
    """Derive both residual-2 populations for one parsed module.

    Args:
        module: The repo-relative path.
        tree: The parsed module.

    Returns:
        The findings and the handlers examined, in that order.
    """
    shadowed = _shadowed(tree)
    chaining = _chaining_functions(tree)
    classes = _module_class_names(tree)
    defined = _defined_functions(tree)
    found: list[CalleeSite] = []
    reach: list[HandlerReach] = []
    for handler, scope, calls in _handlers_with_calls(tree, shadowed):
        qualname = ".".join(scope) or MODULE_SCOPE
        handler_type = ast.unparse(handler.type) if handler.type is not None else NO_HANDLER
        resolved: list[str] = []
        opaque: list[str] = []
        for call in calls:
            written = ast.unparse(call.func)
            if not isinstance(call.func, ast.Name) or call.func.id in classes:
                opaque.append(written)
                continue
            name = call.func.id
            if name not in defined:
                opaque.append(written)
                continue
            resolved.append(written)
            if name in chaining:
                found.append(
                    CalleeSite(
                        module=module,
                        handler_lineno=handler.lineno,
                        qualname=qualname,
                        handler_type=handler_type,
                        callee=name,
                        callee_lineno=chaining[name],
                    )
                )
        reach.append(
            HandlerReach(
                module=module,
                handler_lineno=handler.lineno,
                qualname=qualname,
                handler_type=handler_type,
                resolved=tuple(sorted(set(resolved))),
                opaque=tuple(sorted(set(opaque))),
            )
        )
    return found, reach


def _defined_functions(tree: ast.Module) -> frozenset[str]:
    """Every function name the module defines, whether or not it raises.

    Separate from :func:`_chaining_functions` so a callee that IS resolved and
    does NOT chain still counts toward the denominator. Folding the two would
    make a resolved-and-safe callee indistinguishable from an unresolved one,
    and the denominator would then silently shrink to the findings.

    MODULE LEVEL ONLY, for the reason :func:`_chaining_functions` records: a
    bare name resolved across scopes is a name collision waiting to become a
    false positive. The two must agree on scope or a callee could be
    "resolved" here and absent there.

    Args:
        tree: The parsed module.

    Returns:
        The defined function names.
    """
    return frozenset(
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def callee_sites_in_tree(sources: Mapping[str, str]) -> tuple[CalleeSite, ...]:
    """Derive the residual-2 findings from a mapping of module to source.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every handler calling a same-module function that raises without a
        ``from`` clause, ordered by module then handler line.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    found: list[CalleeSite] = []
    for module in sorted(sources):
        found.extend(_module_callee_records(module, _parse(module, sources[module]))[0])
    return tuple(sorted(found, key=lambda site: (site.module, site.handler_lineno, site.callee)))


def handler_reach_in_tree(sources: Mapping[str, str]) -> tuple[HandlerReach, ...]:
    """Derive the residual-2 DENOMINATOR from a mapping of module to source.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every OSError-typed handler whose own scope contains a call, ordered by
        module then handler line.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    reach: list[HandlerReach] = []
    for module in sorted(sources):
        reach.extend(_module_callee_records(module, _parse(module, sources[module]))[1])
    return tuple(sorted(reach, key=lambda seen: (seen.module, seen.handler_lineno)))


@cache
def callee_sites() -> tuple[CalleeSite, ...]:
    """The live residual-2 findings, derived on every run.

    Returns:
        Every finding in the tracked tree. EXPECTED TO BE EMPTY today, which is
        why :func:`handler_reach` exists beside it.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return callee_sites_in_tree(tracked_sources())


@cache
def handler_reach() -> tuple[HandlerReach, ...]:
    """The live residual-2 denominator, derived on every run.

    Returns:
        Every OSError-typed handler with a call in its own scope.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return handler_reach_in_tree(tracked_sources())


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def classify(site: Site, exempt: Mapping[str, str] = EXEMPT) -> str:
    """Grade one site.

    THERE IS NO CLEAN VERDICT AND NO REDACTION LEG. There are TWO positive
    clearances and each rests on a structural fact rather than on a property of
    a value this module cannot see: :data:`CLOSED_SUPPRESSED` on the
    interpreter setting ``__suppress_context__`` for a raise that CONSTRUCTS a
    locally-declared class, and :data:`CLOSED_PATHLESS` on the callee in the
    censused slot CONSTRUCTING a builtin ``OSError`` out of
    :data:`CLONE_FIELDS` alone.

    THE BRANCHES ARE TESTED IN :data:`VERDICT_ORDER` AND THAT IS THE WHOLE
    CONTRACT. CS-857 residual 1 was not a missing detector and not a wrong
    name: every fact needed to grade the site correctly was already ON the
    site, and the clearance branch simply ran first and returned before anyone
    read them. THE TEST for any future branch that returns a positive verdict
    is to ask what is TRUE AT RUNTIME when that branch is taken - read the
    branches in the order the CODE tests them, never the order a docstring
    explains them. Recorded in ``memory/a-guard-can-measure-spelling.md``.

    AND THE FIRST REPAIR OF THAT DEFECT REPRODUCED IT ONE LEVEL DOWN. Round 1
    gated the clearance on ``raised == handler_name``, a COMPARISON OF
    SPELLINGS: an adversary measured 15 shapes - ``kept = exc``, a walrus, a
    subscript, an attribute, an outer handler's binding - that spell
    differently, name the same object, grade ``closed-suppressed`` and render
    the filename. Round 2 gates it on :attr:`Site.raises_local_class`, a
    POSITIVE fact about what is constructed rather than a negative one about
    what a name is not. A shape this cannot prove is UNPROVEN, which restores
    the doctrine in :data:`TYPE_UNRESOLVED` that an unresolved site is never
    cleared. DO NOT REPAIR A FUTURE ESCAPE BY ADDING SPELLINGS HERE.

    CS-884 ADDED THE THIRD BRANCH AND ITS PLACE IN THE ORDER IS THE DECISION.
    Until it existed, the remedy this project actually ships - chaining or
    raising a clone the callee builds from :data:`CLONE_FIELDS` - satisfied no
    clearance and graded :data:`UNPROVEN` alongside every shape nobody had
    looked at, so the bucket was a CONFLATION rather than a silence. The branch
    is written third, AFTER :data:`MEASURED_LEAK`, because the two predicates
    collide on a reachable shape and a positive verdict tested first would
    launder the leak; and after :data:`CLOSED_SUPPRESSED` so that no site which
    already held that verdict changes. It reads :attr:`Site.
    constructs_pathless_clone`, which is again a POSITIVE fact about what is
    built - the sentence above about spellings governs this branch too.

    Args:
        site: The site.
        exempt: The exemption record, injectable so the census can grade the
            reporter on a fabricated record rather than on the live one.

    Returns:
        Exactly one of :data:`VERDICT_ORDER`.
    """
    if site.cause_type == TYPE_OSERROR:
        return MEASURED_LEAK
    if site.form == FORM_SUPPRESSED and site.raises_local_class:
        return CLOSED_SUPPRESSED
    if site.constructs_pathless_clone:
        return CLOSED_PATHLESS
    if site.key in exempt:
        return EXEMPT_RECORDED
    return UNPROVEN


def verdict_distribution(sites: Sequence[Site]) -> tuple[str, ...]:
    """One line per verdict, with how many of these sites carry it.

    DERIVED FROM :data:`VERDICT_ORDER` RATHER THAN WRITTEN OUT, and every
    verdict is named EVEN AT ZERO. A reporter that enumerated the verdicts by
    hand would have gone silent about :data:`CLOSED_PATHLESS` the moment
    CS-884 added it, and one that printed only the non-empty rows reports the
    same thing for a verdict nobody can reach as for a verdict nobody computes.

    Args:
        sites: The population to summarise.

    Returns:
        One line per verdict, in :data:`VERDICT_ORDER`.
    """
    return tuple(
        f"{verdict} {sum(1 for site in sites if classify(site) == verdict)}"
        for verdict in VERDICT_ORDER
    )


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


def bucket_of(module: str) -> str:
    """The one bucket a module belongs to, with the reason each bucket states.

    THE SINGLE CLASSIFIER. Both the graded predicate and the out-of-scope
    record derive from this function, so the two cannot disagree about a site
    the way they did before CS-879, when a flat prefix decided grading and
    frozenness decided reporting and three sites fell between them.

    THE ORDER OF THE BRANCHES IS THE PRECEDENCE, and frozenness is tested
    FIRST because it is the strongest fact available about a file: it holds
    wherever the file lives, and answering anything else for a frozen path
    would be a request to edit one. Read the branches, not this sentence.

    Args:
        module: A repo-relative, forward-slashed path.

    Returns:
        One of :data:`BUCKETS`, or :data:`BUCKET_UNCLASSIFIED` when the module
        is outside every root in :data:`SWEPT_ROOTS`. The sentinel is NOT an
        error and NOT a bucket - it is this module declining to guess about a
        scope nobody has classified, and the census reddens on it.
    """
    if is_frozen(module):
        return BUCKET_FROZEN
    if not module.startswith(SWEPT_ROOTS):
        return BUCKET_UNCLASSIFIED
    if module in CONTROL_MODULES:
        return BUCKET_CONTROL
    return BUCKET_GRADED


def out_of_scope_record(sites: Sequence[Site]) -> tuple[str, ...]:
    """Render every site this module does NOT grade, each with its bucket.

    Derived and reported on every run so that nothing the sweep paid to find
    is dropped in silence. ``CLAUDE.md`` section 6 routes a frozen-file edit
    through an adjudicator; this module only reads, so a frozen site is
    surfaced rather than repaired.

    COVERS THE FIXTURE BUCKET TOO, AND NOT ONLY THE FROZEN ONE. Reporting just
    the frozen sites left this module's own fixtures in neither population -
    the same defect one bucket over from the one CS-879 was opened for. Every
    derived site IN A NAMED BUCKET is now either graded or on this list, which
    is what makes the pair of populations exhaustive rather than merely large.
    A site in NO named bucket is deliberately on neither, which is the next
    paragraph.

    FILTERS ON :data:`RECORDED_BUCKETS` RATHER THAN ON ``not is_graded``. The
    difference is the whole enforcement: a catch-all would sweep an
    unclassified module onto this list and the exhaustiveness arm would pass
    on the one shape it exists to fail.

    Args:
        sites: The derived population.

    Returns:
        One line per frozen or fixture site, sorted, each naming the bucket
        that excluded it so the reason is legible from the line alone.
    """
    return tuple(
        sorted(
            f"out-of-scope-recorded {bucket_of(site.module).upper()} "
            f"{classify(site)} {site.key} line {site.lineno}"
            for site in sites
            if bucket_of(site.module) in RECORDED_BUCKETS
        )
    )


# ---------------------------------------------------------------------------
# CS-883 - the __notes__ census's own population, derived from the SAME
# classifier the chained-raise census grades by.
#
# THE TWO CENSUSES SIT IN ONE FILE AND USED TO MEASURE DIFFERENT POPULATIONS.
# The note zero was asserted over :data:`ADVICE_LAYER` while CS-879 widened
# grading to whatever :func:`bucket_of` calls :data:`BUCKET_GRADED`, so a note
# attached in a ``scripts/``, ``tools/`` or test-support module was graded by
# nothing. Both derivations below read :func:`bucket_of` and nothing else, so
# the two cannot drift apart again without the classifier itself moving.
# ---------------------------------------------------------------------------


def note_census_modules(sources: Mapping[str, str]) -> tuple[str, ...]:
    """The modules the ``__notes__`` zero is asserted over, one per member.

    THE DENOMINATOR IS MODULES, NOT NOTE SITES, AND THAT IS THE WHOLE POINT.
    A population of note SITES is empty on a clean tree, so a zero over it is
    a zero over nothing; and a population of modules that already CHAIN a raise
    would miss every module that holds a note and chains nothing - which on
    this tree is most of them. The same reasoning
    ``test_every_advice_layer_module_is_graded`` records for the site census:
    asserted over modules from the sweep, so a module that attaches nothing
    today is still covered the day it starts.

    Args:
        sources: Repo-relative module path to source text, as
            :func:`tracked_sources` returns.

    Returns:
        Every censused module path, sorted. A module in any other bucket is
        absent by construction rather than by a hand-maintained list, which is
        what keeps this census's own planted fixtures out of it without anyone
        naming them: they are :data:`CONTROL_MODULES`, so :func:`bucket_of`
        answers :data:`BUCKET_CONTROL` and they never enter.
    """
    return tuple(sorted(module for module in sources if bucket_of(module) == BUCKET_GRADED))


def note_findings(notes: Sequence[NoteSite]) -> tuple[str, ...]:
    """Every note site inside the censused population, rendered.

    A ``__notes__`` string renders in the formatted traceback UNDER the
    exception it is attached to, and a ``.cause`` walk cannot see it, so this
    is a second disclosure channel rather than a variation on the first.

    WHAT THIS ZERO IS ABOUT, AND WHAT IT IS NOT. CS-883 widened the POPULATION
    to every module :func:`bucket_of` grades; it did not widen the CHANNEL, and
    the difference is where a note can still hide. :func:`_module_notes` walks
    for an ``add_note`` ATTRIBUTE CALL and for an ``__notes__`` ATTRIBUTE
    access, so a note attached through a name held as a STRING -
    ``setattr(exc, "__notes__", ...)``, ``getattr`` with a computed attribute,
    or ``add_note`` reached through ``operator.methodcaller`` - is derived by
    nothing and this zero says nothing about it. MEASURED, one arm apiece, in
    ``tests/test_chained_cause_census.py``.

    WIDENING THE CHANNEL WAS CONSIDERED AND DECLINED WITH A REASON. Arms in
    the save suite read ``getattr(exc, "__notes__", ())`` to MEASURE what a
    redacted exception carried, which is the RUNTIME act that
    ``tests/chained_exemption_guard.py`` separates from the static one, and a
    string-aware walk would report every one of them as an attachment. The
    escape from that is an exclusion list of files to ignore, which is the
    hand-maintained shape this census exists without. A stated, measured
    under-report is the fail-closed side of that trade; a clearance bought
    with a list of names is not.

    Args:
        notes: Any derived note population, live or planted.

    Returns:
        One line per censused note site, sorted, each naming the module, the
        line, the enclosing scope, the channel and the expression as written,
        so a red arm says what to go and read.
    """
    return tuple(
        sorted(
            f"note-finding {note.module}:{note.lineno} {note.qualname} {note.channel} {note.source}"
            for note in notes
            if bucket_of(note.module) == BUCKET_GRADED
        )
    )


def notes_out_of_scope_record(notes: Sequence[NoteSite]) -> tuple[str, ...]:
    """Render every note site this module does NOT census, each with its bucket.

    THE MIRROR OF :func:`out_of_scope_record`, AND FOR THE SAME REASON. The
    sweep pays to derive every note site in the tree; one that is neither
    censused nor recorded is a site the census found and then said nothing
    about. On this tree the record is what accounts for the census's own
    planted note fixtures, so their exclusion is legible on every run rather
    than being a property nobody prints.

    FILTERS ON :data:`RECORDED_BUCKETS` RATHER THAN ON "not censused", so a
    note in a module outside :data:`SWEPT_ROOTS` falls through BOTH populations
    and the exhaustiveness arm reddens on it instead of absorbing it.

    Args:
        notes: Any derived note population, live or planted.

    Returns:
        One line per frozen or control note site, sorted.
    """
    return tuple(
        sorted(
            f"note-out-of-scope-recorded {bucket_of(note.module).upper()} "
            f"{note.module}:{note.lineno} {note.qualname} {note.channel}"
            for note in notes
            if bucket_of(note.module) in RECORDED_BUCKETS
        )
    )


# ---------------------------------------------------------------------------
# CS-881 - THE DEFERRED RAISE. A THIRD POPULATION, and the SECOND known way
# out of the :class:`Site` population altogether.
#
# DELIBERATELY NOT FOLDED INTO :class:`Site`, for the reason the residual-2
# block gives one population up. A ``Site`` is a raise this module GRADES, and
# :func:`classify` reads fields - ``cause_type``, ``raises_local_class``,
# ``constructs_pathless_clone`` - that are answers about a CHAIN. The records
# below are not chains at all: nothing is chained, the rendered object IS the
# caught exception, and the channel is one link deep. Widening ``Site`` would
# also change what :func:`_form_of` answers for shapes that answer None today,
# and ``tests/pathless_clone_guard.py`` reads that function directly - so the
# widening would move a SIBLING's population without anyone deciding to.
#
# THE PRECEDENT IS LIMIT 8. When the census could see only part of a shape it
# grew a second, narrower population and stated what it still could not see,
# rather than widening the graded record and moving every verdict under it.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeferredRaiseSite:
    """One raise of a value a handler in the SAME SCOPE stored, after it exits.

    THE FACT THIS IS KEYED ON IS POSITIVE, and that is the whole design. It is
    NOT "the raise is a bare ``ast.Name``": the tracked tree holds one live
    site whose raised expression is an ``ast.IfExp``, and a leg keyed on the
    node kind would derive its sibling and go silent about it - the spelling
    silence ``memory/a-guard-can-measure-spelling.md`` records. What is read is
    that the raised expression READS a local a handler bound to its own
    exception, whatever the expression around that name happens to be.

    Attributes:
        module: Repo-relative path, forward-slashed by git.
        lineno: The ``ast.Raise`` STATEMENT line.
        qualname: Dotted enclosing scope, :data:`MODULE_SCOPE` at module level.
        raised: The raised expression AS WRITTEN, unparsed whole rather than
            reduced to a callee the way :attr:`Site.raised` is. A ``Site`` is
            always a construction, so its callee is the informative part; here
            the SHAPE of the expression is the thing a reader has to see.
        stored_name: The local the handler bound its own exception to.
        handler_lineno: The FIRST storing ``except`` clause's line.
        handler_types: Every storing handler's clause type as written, sorted
            and deduplicated. A TUPLE rather than one string because a scope
            may store into one name from more than one handler, and dropping
            all but the first would be a silent narrowing.
        stored_type: One of :data:`TYPE_OSERROR`, :data:`TYPE_RESOLVED_OTHER`
            or :data:`TYPE_UNRESOLVED`, taken over every storing handler by its
            WORST member for the reason :func:`_tuple_type` records: a verdict
            met by a population's strongest member measures nothing about its
            weakest.
    """

    module: str
    lineno: int
    qualname: str
    raised: str
    stored_name: str
    handler_lineno: int
    handler_types: tuple[str, ...]
    stored_type: str

    @property
    def key(self) -> str:
        """The site expression this population is keyed on.

        NO LINE NUMBER, for the reason :attr:`CalleeSite.key` records: a key
        carrying one drifts on any edit above it, which is the dead-citation
        failure CS-857 was filed against. The raised expression is IN the key,
        so the two live sites - one a name, one a conditional - do not collide.

        Returns:
            ``module::qualname::stored_name::raised``.
        """
        return f"{self.module}::{self.qualname}::{self.stored_name}::{self.raised}"

    @property
    def is_graded(self) -> bool:
        """Whether this module grades the site.

        Returns:
            True when the site is in :data:`BUCKET_GRADED`.
        """
        return bucket_of(self.module) == BUCKET_GRADED


@dataclass(frozen=True)
class StoreReach:
    """One handler that stores its own binding into a local. THE DENOMINATOR.

    IT EXISTS BECAUSE A COUNT WITHOUT ONE IS A COUNT ABOUT NOTHING. A
    derivation that read no source reports the same finding count as one that
    read the whole tree and found two, and the same reasoning
    :class:`HandlerReach` records one population up applies here whether the
    numerator is zero or not: the day both live sites are repaired, the finding
    count goes to zero and only this says whether the walk still works.

    Attributes:
        module: Repo-relative path.
        handler_lineno: The ``except`` clause line.
        qualname: Dotted enclosing scope.
        handler_type: The clause type as written, :data:`NO_HANDLER` for a bare
            ``except``.
        stored: The local names this handler bound its own exception to.
    """

    module: str
    handler_lineno: int
    qualname: str
    handler_type: str
    stored: tuple[str, ...]


def _written_handler_type(handler: ast.ExceptHandler) -> str:
    """Render an ``except`` clause type as written.

    Args:
        handler: The handler.

    Returns:
        The clause type, or :data:`NO_HANDLER` for a bare ``except``.
    """
    return ast.unparse(handler.type) if handler.type is not None else NO_HANDLER


def _sole_element(iterated: ast.expr) -> ast.expr | None:
    """The one element of a single-item sequence LITERAL, if it is one.

    THE ONLY ITERABLE A ``for`` TARGET CAN BE RESOLVED AGAINST STATICALLY.
    ``for last in (exc,):`` runs exactly once and binds ``last`` to ``exc``
    before the body executes, so the binding holds however the body ends -
    ``break`` and ``continue`` included. Anything else is refused: ``for last
    in kept:`` binds an element this walk cannot name, and ``for last in (exc,
    other):`` leaves the loop bound to whichever element it stopped on. Both
    are silences and are stated as such in limit 13 rather than guessed at.

    Args:
        iterated: The ``iter`` expression of a ``for`` or ``async for``.

    Returns:
        The single element, or None when the iterable is anything else.
    """
    if isinstance(iterated, (ast.Tuple, ast.List)) and len(iterated.elts) == _ONE_ELEMENT:
        return iterated.elts[0]
    return None


def _stored_binding(node: ast.AST) -> tuple[tuple[ast.expr, ...], ast.expr | None]:
    """The TARGETS one binding statement writes, and the value it writes there.

    FIVE STATEMENT FORMS BIND A NAME TO A VALUE THE WRITER NAMED, and reading
    only ``ast.Assign`` was the CS-881 residual-2 defect: an ``ast.AnnAssign``
    and an ``ast.NamedExpr`` each bind a BARE LOCAL to the handler's own
    binding, in the same scope, which is precisely the positive fact
    :class:`DeferredRaiseSite` says it keys on. Both were MEASURED to leak
    while deriving nothing, and ``last: OSError | None = exc`` is ordinary
    house style in a tree this heavily annotated rather than an adversarial
    spelling.

    ``ast.AugAssign`` IS DELIBERATELY ABSENT although :data:`_TARGETED_STATEMENTS`
    lists it, and the difference between the two tuples is the whole reason
    this is a separate function. That tuple answers "what names does this
    REBIND", where an extra member can only WITHDRAW a clearance and being wide
    is the safe direction. This one answers "is the stored value the handler's
    OWN binding", where a wrong member INVENTS a finding. ``last += exc``
    stores what ``__iadd__`` returned, which is not the caught exception, so
    reading it as a store would over-report a shape nobody writes.

    Args:
        node: Any node from the walk.

    Returns:
        The target expressions and the bound value. ``((), None)`` for a node
        this walk does not read as a binding at all. A caller must still check
        the value, because an annotation with no value - ``last: OSError`` -
        comes back with a target and a None beside it.
    """
    if isinstance(node, ast.Assign):
        return tuple(node.targets), node.value
    if isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
        return (node.target,), node.value
    if isinstance(node, (ast.For, ast.AsyncFor)):
        return (node.target,), _sole_element(node.iter)
    return (), None


def _handler_stores(tree: ast.Module) -> Iterator[tuple[tuple[str, ...], ast.ExceptHandler, str]]:
    """Every place a handler binds its OWN exception to a plain local name.

    WHAT IS FOLLOWED is :func:`_stored_binding`'s five forms - a plain
    assignment, an annotated one, a walrus, and a ``for`` or ``async for`` over
    a single-element sequence literal - written in the handler's own scope,
    whose value is the handler's binding and whose target is a bare name.

    THE FOUR REFUSALS ARE FOUR STATED SILENCES, not four spellings of one rule.
    Each is planted, RUN and measured in ``tests/test_chained_cause_census.py``,
    and every one that leaks is named there as an under-report rather than left
    to be discovered:

      value is not the binding    ``last = OSError(...)`` inside the handler
                                  binds a fresh error, and raising it later
                                  discloses nothing.
      value is a second local     ``kept = exc`` then ``last = kept``. A
                                  two-step forward is NOT followed, so a raise
                                  of ``last`` is derived by nothing. MEASURED
                                  to leak.
      target binds no local name  ``holder.last = exc`` writes through an
                                  attribute and ``held[0] = exc`` through a
                                  subscript; a store into a CONTAINER -
                                  ``held.append(exc)`` - is not an assignment
                                  at all. ALL THREE MEASURED to leak. A tuple
                                  unpack never reaches this leg: its value is
                                  a tuple rather than the handler's binding,
                                  so the value check above refuses it first.
      the handler binds nothing   ``except OSError:`` has no binding to store,
                                  so there is no object to defer.

    THE SCOPE FILTER IS :func:`_walk`'S, which is what makes "the same scope" a
    fact rather than a nesting depth: a statement inside a nested ``def`` runs
    in ITS frame and comes back with no active handler at all. A ``lambda``
    resets it the same way, so a walrus written inside one is not followed -
    correctly, because that walrus binds in the lambda's frame. A walrus inside
    a COMPREHENSION is followed, and that is correct too: PEP 572 binds it in
    the containing scope, which is the scope this walk reports for it.

    Args:
        tree: The parsed module.

    Yields:
        The enclosing scope path, the storing handler, and the local name.
    """
    for node, scope, handler in _walk(tree, (), None):
        if handler is None or not handler.name:
            continue
        targets, value = _stored_binding(node)
        if not isinstance(value, ast.Name) or value.id != handler.name:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                yield scope, handler, target.id


def _read_names(node: ast.expr) -> frozenset[str]:
    """Every bare name an expression READS.

    WIDER THAN "the expression IS a name", AND THAT IS THE POINT. Keying on the
    raised node's KIND is the defect this population was filed against: the
    tracked tree holds a ``raise <Name>`` and a ``raise <IfExp>`` of the same
    shape, and a kind-keyed leg derives one of them.

    THE COST IS AN OVER-REPORT AND IT IS STATED RATHER THAN HIDDEN.
    ``raise OSError(last.errno, last.strerror)`` reads ``last`` as the base of
    an attribute access, carries no path, and is derived anyway - planted, run
    and MEASURED not to leak in ``tests/test_chained_cause_census.py``. Between
    over-reporting a site and going silent about one, this population takes the
    first, which is the trade :data:`VERDICT_ORDER` records one census over.

    Args:
        node: The expression.

    Returns:
        The names read anywhere beneath it.
    """
    return frozenset(
        inner.id
        for inner in ast.walk(node)
        if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load)
    )


def _worst_stored_type(handlers: Sequence[ast.ExceptHandler], shadowed: frozenset[str]) -> str:
    """Classify a set of storing handlers by their WORST member.

    Args:
        handlers: Every handler that stored into one name in one scope.
        shadowed: Builtin names this module binds itself.

    Returns:
        One of the three ``TYPE_`` constants.
    """
    kinds = {_type_of(handler.type, shadowed) for handler in handlers}
    if TYPE_OSERROR in kinds:
        return TYPE_OSERROR
    if not kinds or TYPE_UNRESOLVED in kinds:
        return TYPE_UNRESOLVED
    return TYPE_RESOLVED_OTHER


def _module_deferred_sites(module: str, tree: ast.Module) -> Iterator[DeferredRaiseSite]:
    """Derive every deferred raise in one parsed module.

    THE RAISE IS SELECTED BY ``_form_of(...) is None``, WHICH IS EXACTLY THE
    GAP. That answer means the raise carries an expression, carries no ``from``
    clause, and sits inside NO handler - so :class:`Site` derives nothing for
    it and the two populations cannot double-count one statement. A deferred
    raise written inside ANOTHER handler is already a :data:`FORM_IMPLICIT`
    ``Site``, and is deliberately not derived twice; that ``Site``'s type leg
    answers about the OTHER handler's clause rather than about the stored
    object, which is a separate under-report and is stated as limit 13.

    Args:
        module: The repo-relative path.
        tree: The parsed module.

    Yields:
        One record per (raise, stored name) pair.
    """
    shadowed = _shadowed(tree)
    stores: dict[tuple[tuple[str, ...], str], list[ast.ExceptHandler]] = {}
    for scope, storing, name in _handler_stores(tree):
        stores.setdefault((scope, name), []).append(storing)
    for node, scope, handler in _walk(tree, (), None):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        if _form_of(node, handler) is not None:
            continue
        raised = ast.unparse(node.exc)
        for name in sorted(_read_names(node.exc)):
            found = stores.get((scope, name))
            if not found:
                continue
            yield DeferredRaiseSite(
                module=module,
                lineno=node.lineno,
                qualname=".".join(scope) or MODULE_SCOPE,
                raised=raised,
                stored_name=name,
                handler_lineno=min(one.lineno for one in found),
                handler_types=tuple(sorted({_written_handler_type(one) for one in found})),
                stored_type=_worst_stored_type(found, shadowed),
            )


def _module_store_reach(module: str, tree: ast.Module) -> Iterator[StoreReach]:
    """Derive the deferred DENOMINATOR for one parsed module.

    Args:
        module: The repo-relative path.
        tree: The parsed module.

    Yields:
        One record per handler that stores its own binding into a local.
    """
    handlers: dict[int, ast.ExceptHandler] = {}
    scopes: dict[int, tuple[str, ...]] = {}
    names: dict[int, set[str]] = {}
    for scope, handler, name in _handler_stores(tree):
        marker = id(handler)
        handlers.setdefault(marker, handler)
        scopes.setdefault(marker, scope)
        names.setdefault(marker, set()).add(name)
    for marker, handler in handlers.items():
        yield StoreReach(
            module=module,
            handler_lineno=handler.lineno,
            qualname=".".join(scopes[marker]) or MODULE_SCOPE,
            handler_type=_written_handler_type(handler),
            stored=tuple(sorted(names[marker])),
        )


def deferred_raise_sites_in_tree(sources: Mapping[str, str]) -> tuple[DeferredRaiseSite, ...]:
    """Derive the deferred-raise population from a mapping of module to source.

    THE ONE DERIVATION, on the pattern :func:`sites_in_tree` sets.
    :func:`deferred_raise_sites` is this function over the live tree and every
    behavioural arm is this function over a planted synthetic module, so no arm
    is fitted to what the tree happens to hold today.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every deferred raise, ordered by module then line then stored name.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    found: list[DeferredRaiseSite] = []
    for module in sorted(sources):
        found.extend(_module_deferred_sites(module, _parse(module, sources[module])))
    return tuple(sorted(found, key=lambda site: (site.module, site.lineno, site.stored_name)))


def store_reach_in_tree(sources: Mapping[str, str]) -> tuple[StoreReach, ...]:
    """Derive the deferred DENOMINATOR from a mapping of module to source.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        Every storing handler, ordered by module then handler line.

    Raises:
        ChainedCauseDerivationError: A module did not parse.
    """
    reach: list[StoreReach] = []
    for module in sorted(sources):
        reach.extend(_module_store_reach(module, _parse(module, sources[module])))
    return tuple(sorted(reach, key=lambda seen: (seen.module, seen.handler_lineno)))


@cache
def deferred_raise_sites() -> tuple[DeferredRaiseSite, ...]:
    """The live deferred-raise population, derived on every run.

    Returns:
        Every deferred raise in the tracked tree.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return deferred_raise_sites_in_tree(tracked_sources())


@cache
def store_reach() -> tuple[StoreReach, ...]:
    """The live deferred DENOMINATOR, derived on every run.

    Returns:
        Every handler in the tracked tree that stores its own binding.

    Raises:
        ChainedCauseDerivationError: The tree could not be read or parsed.
        RuntimeError: git is unavailable or reported failure.
    """
    return store_reach_in_tree(tracked_sources())


def deferred_findings(sites: Sequence[DeferredRaiseSite]) -> tuple[str, ...]:
    """Every deferred raise inside the graded population, rendered.

    REPORTED RATHER THAN GRADED. This population issues no verdict: there is no
    clearance it could earn, because the object that renders is the caught
    exception itself and nothing about the raise can make it otherwise. What a
    line says is "go and read this", and the repair is the one the four shipped
    copies of the idiom already use - build a filename-free clone.

    Args:
        sites: Any derived deferred population, live or planted.

    Returns:
        One line per graded site, sorted, each naming the module, the line, the
        scope, the resolved type of what was stored, the local, the storing
        handlers and the raised expression as written - so a reported line says
        what to go and read without anyone opening the tree.
    """
    return tuple(
        sorted(
            f"deferred-raise-finding {site.module}:{site.lineno} {site.qualname} "
            f"{site.stored_type} stored={site.stored_name} "
            f"handler={'|'.join(site.handler_types)} at line {site.handler_lineno} "
            f"raises {site.raised}"
            for site in sites
            if bucket_of(site.module) == BUCKET_GRADED
        )
    )


def deferred_out_of_scope_record(sites: Sequence[DeferredRaiseSite]) -> tuple[str, ...]:
    """Render every deferred raise this module does NOT report, with its bucket.

    THE MIRROR OF :func:`out_of_scope_record`, AND FOR THE SAME REASON. The
    sweep pays to derive every deferred raise in the tree; one that is neither
    reported nor recorded is a site the census found and then said nothing
    about. On this tree the record is what accounts for the census's own
    planted fixtures, so their exclusion is legible on every run.

    FILTERS ON :data:`RECORDED_BUCKETS` RATHER THAN ON "not graded", so a site
    in a module outside :data:`SWEPT_ROOTS` falls through BOTH populations and
    the exhaustiveness arm reddens on it instead of absorbing it.

    Args:
        sites: Any derived deferred population, live or planted.

    Returns:
        One line per frozen or control site, sorted.
    """
    return tuple(
        sorted(
            f"deferred-raise-out-of-scope-recorded {bucket_of(site.module).upper()} "
            f"{site.module}:{site.lineno} {site.qualname} stored={site.stored_name}"
            for site in sites
            if bucket_of(site.module) in RECORDED_BUCKETS
        )
    )
