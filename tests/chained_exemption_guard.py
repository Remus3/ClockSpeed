"""CS-857 - who may decide, statically, that a chained raise is not a finding.

THE PROPOSITION THIS GRADES, and it is a proposition about CODE rather than
about prose. ``raise X(...) from exc`` makes the cause's own text part of the
formatted traceback, so a redacted message can render clean while the chained
``OSError`` renders the raw path beside it. The tree has exactly ONE owner of
the question "can a chained cause render": the chained-cause census at
``tests/chained_cause_guard.py``, which answers it by MEASUREMENT - running the
constructor and reading the rendered traceback. Any OTHER module that answers
it for itself is answering from a belief, and two of those beliefs shipped
false and survived repeated careful reading.

WHY THIS IS NOT A PHRASE SEARCH, and that distinction is the whole design.
``memory/a-guard-can-measure-spelling.md`` records what a spelling gate
produces: a previous CS-857 round gated a clearance on a spelling and an
adversary found fifteen escapes. "deliberately never rendered" has unbounded
paraphrases and every one of them is an escape. THE HANDLE HERE IS AN API NAME
INSTEAD. ``cause`` is the field CPython's own ASDL grammar gives ``ast.Raise``;
a module cannot ask whether a raise carries a cause without touching it, and it
cannot rename the field, because the name belongs to the interpreter rather
than to the author. A belief about chaining that is IMPLEMENTED has to spell
``cause``; a belief that is merely written down does not, and this guard says
so plainly in its residual list below rather than pretending otherwise.

THE STATIC READ AND THE RUNTIME READ ARE DIFFERENT ACTS. ``node.cause`` on an
``ast.Raise`` is a module DECIDING, at parse time, what a chained raise means -
that is adjudication. ``caught.value.__cause__`` on a live exception is a module
MEASURING what one actually carried - that is evidence, and it is the very thing
the census endorses. This guard separates them on the attribute name, so
``tests/save/test_world.py`` and ``tests/save/test_header.py``, which assert on
``__cause__`` at runtime, are never in the population at all.

THE RULE. Every tracked module that statically reads a raise's ``cause`` field
must be one of two things, and the third outcome is a finding:

  * THE OWNER itself, :data:`OWNER`;
  * RECORDED in :data:`EXEMPT` against a stated reason;
  * otherwise UNRECORDED, which is the finding.

IMPORTING THE OWNER WAS A THIRD ROUTE OUT AND CS-888 ABOLISHED IT. That branch
is recorded here rather than merely deleted, because a deleted clearance is the
kind a later reader reinvents. Deferral was decided by :func:`defers_to_owner`,
which asks only whether the importing module names the census ANYWHERE, and
that answer was treated as blanket, permanent, module-wide immunity. WHAT WAS
MEASURED WHEN CS-888 WAS FILED, and these are the numbers of THAT measurement
rather than a live count - the live subject set is derived by the sibling arm
every run and written down nowhere, CLAUDE.md section 4: an identical four-line
static cause read appended to any of the SIX modules then importing the census
changed the population by nothing and was reported by no arm, while the same
four lines in a module that happened not to import it were reported at once.
FIVE OF THOSE SIX READ NO CAUSE AT ALL, so they held unused immunity that would
arm the day they added one. AN IMPORT IS NOT A FACT ABOUT HOW THE IMPORTING
MODULE READS A CAUSE. It is a fact about a name, and this guard is about a read.

TWO NARROWER REPLACEMENTS WERE MEASURED AND BOTH ARE REFUTED, which is why the
clearance was abolished outright rather than tightened:

  * IMMUNITY FOR CONSUMING A VERDICT rather than importing a name. Three of
    those importers - ``tests/surface/test_server.py``,
    ``tests/test_chained_cause_census.py`` and
    ``tests/test_pathless_clone_agreement.py`` - already CALL
    ``chained_cause_guard.classify``, so they keep blanket immunity under it
    and a plant in any of them still goes unreported. The rule would ship green
    on much of the defect it was written for, which is the shape that filed
    CS-880.
  * A PINNED IMMUNE SET. A plant inside an already-pinned module does not
    change the set, so the pin reddens on a seventh importer and stays silent
    on the read that matters.

Clearance is :data:`EXEMPT` alone, with a stated reason the sibling arm
re-measures, and that is the whole list.

Reading a cause is enough to be in the population. This guard deliberately does
NOT try to model whether the read feeds a suppression: that needs dataflow, and
a dataflow rule keyed on a collection named ``safe`` is a spelling measure one
level down - rename it to ``ok`` and the rule is gone. Requiring a reason for
every static read is fail-closed and needs no such model. A module that reads a
cause innocently is cheap to record; a module that exempts chaining silently
cannot exist.

WHY THE RECORDED REASONS CANNOT ROT, which is the failure this item was filed
against. The fence CS-857 first built was a comment in
``tests/exception_message_guard.py`` forbidding any entry from stating the cause
is unrendered. NOTHING ENFORCED IT, and a later session hunting this exact shape
found neither live record. A sentence is not an artifact. So no entry here is
trusted for its own content: ``tests/test_chained_exemption_guard.py`` carries a
sibling arm that RE-MEASURES the property each reason asserts, by probing the
recorded module's own detector with planted sources. If the exemption widens,
the probe changes and the arm reddens with the reason still sitting there
reading correct. ``docs/adr/0008-detection-claims-are-derived-never-written.md``
owns this class.

WHAT THIS GUARD CANNOT SEE, stated as a boundary rather than left implied:

  1. PROSE. A docstring asserting that chaining does not render has no
     structural footprint whatsoever. ``tests/test_exception_rendering.py``
     carried exactly that claim, in a list of shapes under a heading declaring
     what is NOT a rendering, and its detector never modelled chaining at all -
     the shape was transparent to it rather than exempted by it. That record was
     corrected by hand under CS-857 and NOTHING HERE WOULD HAVE CAUGHT IT. The
     only detector for it is a phrase search, which is refuted above.
  2. A cause reached without naming it - iterating ``ast.iter_fields``, indexing
     ``_fields``, or building the attribute name at runtime. Named here so the
     residual is a measured boundary rather than an unexamined one.
  3. Whether a recorded reason is TRUE. Only the sibling arm's probes measure
     that, and only for the entries it probes.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Final

from tests.assertion_rendering_guard import REPO_ROOT, tracked_python_files

#: The field name CPython's ASDL grammar gives ``ast.Raise`` for the expression
#: after ``from``. Reading it is how a module adjudicates chaining statically.
CAUSE_FIELD: Final = "cause"

#: The chain link on a LIVE exception. Reading this is measurement rather than
#: adjudication, so a module that only ever touches this is out of population.
#: Spelled apart from :data:`CAUSE_FIELD` because the two names differ and the
#: whole separation rests on that.
RUNTIME_CHAIN_ATTR: Final = "__cause__"

#: The one module allowed to decide what a chained raise means, because it is
#: the only one that decides by measurement.
OWNER: Final = "tests/chained_cause_guard.py"

#: The owner's importable name. NOT A CLEARANCE since CS-888 - see
#: :func:`defers_to_owner`, which is kept only to derive the sibling arm's plant
#: subjects.
OWNER_MODULE: Final = "chained_cause_guard"

VERDICT_OWNER: Final = "owner"
VERDICT_RECORDED: Final = "recorded"

#: The finding: a module deciding the chaining question with no reason on file.
VERDICT_UNRECORDED: Final = "unrecorded"


@dataclass(frozen=True)
class Exemption:
    """One recorded reason for the static cause reads of one module.

    Attributes:
        why: The reason. The sibling arm re-measures what it asserts rather
            than trusting the sentence.
        sites: HOW MANY static cause reads this reason answers. WITHOUT IT THE
            KEY IS A MODULE PATH AND NOTHING ELSE, so a reason written for one
            adjudicated read silently forgives every further read that module
            ever gains. That measured true here: an identical planted cause
            read appended to EITHER recorded module went unreported, while the
            same four lines in any other module were named at once. It is
            CS-888's own shape one level down - immunity earned by holding a
            reason about something else instead of by importing a name - and it
            is closed the way ``tests/test_docs_citations.py`` closed the
            identical fault in its ``Disposition`` table. A COUNT IS THE
            CHEAPEST KEY THAT CLOSES IT and the only one that does not churn: a
            line number moves whenever anything above it is edited, and
            :func:`stale_exemptions` cannot see a second read arrive because
            the module never leaves the population.
    """

    why: str
    sites: int


#: Reasons for a static cause read outside the owner. AN ENTRY HERE IS NOT A
#: CLEARANCE. It records why one module reads a raise's cause, and the sibling
#: arm re-measures the property the reason asserts on every run.
#:
#: EACH ENTRY IS CHECKED IN THREE DIRECTIONS, and the third is the one an
#: exemption table is normally missing. An entry whose module has left the
#: population fails :func:`stale_exemptions`; an entry whose SITE COUNT no
#: longer matches the live tree fails :func:`miscounted`, in BOTH directions;
#: and the property each reason asserts is re-measured by its own probe arm.
#:
#: NO ENTRY MAY ASSERT THAT A CHAINED CAUSE IS UNRENDERED. That is the claim
#: CS-857 exists to correct, and it is false: the cause's own text is part of
#: the formatted traceback under default flags, which the census demonstrates on
#: the live tree every run. This sentence is a fence like the one that already
#: failed, so it is not relied upon - the arm measures instead.
EXEMPT: Final[Mapping[str, Exemption]] = {
    "tests/pathless_clone_guard.py": Exemption(
        sites=1,
        why=(
            "MIRRORING IS NOT DEFERRING, AND THE MIRROR IS RE-MEASURED. That "
            "module's cause read sits in ``_slot``, whose own docstring says it "
            "MIRRORS ``chained_cause_guard._constructs_pathless_clone`` "
            "DELIBERATELY: CS-885 requires the two to select the SAME slot for the "
            "same form, because a site the clone guard does not watch is a copy "
            "free to drift. It also imports SIX PRIVATE NAMES from the census - "
            "``_form_of``, ``_module_level_rebindings``, ``_parse``, "
            "``_pathless_clone_functions``, ``_shadowed`` and ``_walk`` - and "
            "CS-888 measured that those imports are worth nothing here: a module "
            "that copies the owner's slot rule into its own source is answering "
            "the question in its own body, whatever it imports. It is NOT a claim "
            "that the cause goes unrendered - the clone guard exists precisely "
            "because it does. The reason is not taken on trust. "
            "``test_the_mirrored_slot_rule_is_re_measured_rather_than_believed`` "
            "runs both selectors over planted sources and asserts they pick the "
            "same slot for every form. Widen the mirror and the probe reddens "
            "while this sentence still reads correct."
        ),
    ),
    "tests/test_verify_env.py": Exemption(
        sites=3,
        why=(
            "SCOPED TO THE CAUSE SLOT, AND RE-MEASURED. That module grades a "
            "DIFFERENT channel - whether the exception OBJECT reaches the message "
            "being built - and its cause read exempts the ``from`` slot alone, "
            "because an object in the cause slot is not in the new message's args. "
            "It is NOT a claim that the cause goes unrendered: the cause renders in "
            "the formatted traceback, on the channel this module's OWNER censuses. "
            "The reason is not taken on trust. "
            "``test_the_recorded_scope_is_re_measured_rather_than_believed`` probes "
            "that module's own detector with planted sources and asserts the "
            "exemption still covers the cause slot ONLY - the object reaching args "
            "on a chained raise must still be flagged. Widen the exemption and "
            "the probe reddens while this sentence still reads correct."
        ),
    ),
}


class ChainedExemptionDerivationError(RuntimeError):
    """A tracked module could not be read or parsed, so the population is short."""


@dataclass(frozen=True)
class Adjudicator:
    """One module that statically decides what a chained raise means.

    Attributes:
        module: Repo-relative path, POSIX separators.
        lines: Ascending line numbers of the static cause reads.
    """

    module: str
    lines: tuple[int, ...]


def _getattr_cause(node: ast.Call) -> bool:
    """Whether a call is ``getattr(x, "cause")``.

    Args:
        node: The call to inspect.

    Returns:
        True when the call reads the cause field by name through ``getattr``.
    """
    if not isinstance(node.func, ast.Name) or node.func.id != "getattr":
        return False
    return any(
        isinstance(argument, ast.Constant) and argument.value == CAUSE_FIELD
        for argument in node.args[1:2]
    )


def _names_cause_field(node: ast.expr) -> bool:
    """Whether this expression names a raise's ``cause`` field.

    Args:
        node: The expression to inspect.

    Returns:
        True for ``<expr>.cause`` and for ``getattr(<expr>, "cause")``.
    """
    if isinstance(node, ast.Attribute):
        return node.attr == CAUSE_FIELD
    if isinstance(node, ast.Call):
        return _getattr_cause(node)
    return False


def static_cause_reads(tree: ast.Module) -> tuple[int, ...]:
    """Line numbers where this module reads a raise's ``cause`` field statically.

    Matches ``<expr>.cause`` and ``getattr(<expr>, "cause")``. Deliberately does
    NOT match :data:`RUNTIME_CHAIN_ATTR`, which is a live exception's chain link
    and is evidence rather than adjudication.

    Args:
        tree: The parsed module.

    Returns:
        The line numbers, ascending, with duplicates preserved per node.
    """
    lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.expr) and _names_cause_field(node)
    ]
    return tuple(sorted(lines))


def defers_to_owner(tree: ast.Module) -> bool:
    """Whether this module imports the census. NOT A CLEARANCE - CS-888.

    THIS DECIDES NOTHING ABOUT THE POPULATION, and the name is kept only
    because the abolished clearance is easier to reason about under the name it
    had. :func:`adjudicators_in_sources` no longer consults it. What it is kept
    FOR is deriving the sibling arm's PLANT SUBJECTS: the arm appends an
    identical static cause read to every module this returns True for and
    asserts each one is reported, so the abolished clearance cannot creep back
    under another name. The subject set is derived live rather than pinned,
    because a pinned set does not grow when a seventh importer arrives - which
    is the same reason a pinned immune set was refuted as the repair.

    Covers ``import tests.chained_cause_guard``, ``from tests import
    chained_cause_guard`` and ``from tests.chained_cause_guard import X``. All
    three are facts about THIS module's syntax, so the owner's contents are
    never consulted and a sibling editing the census cannot move this answer.

    Args:
        tree: The parsed module.

    Returns:
        True when the module imports the owner in any of those forms.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[-1] == OWNER_MODULE for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[-1] == OWNER_MODULE:
                return True
            if any(alias.name == OWNER_MODULE for alias in node.names):
                return True
    return False


def _parse(module: str, source: str) -> ast.Module:
    """Parse one module, naming it rather than the exception on failure.

    Args:
        module: Repo-relative path, used in the failure message.
        source: The source text.

    Returns:
        The parsed module.

    Raises:
        ChainedExemptionDerivationError: The source did not parse. The cause is
            dropped with ``from None``: a SyntaxError renders the absolute path
            it failed on, and this module does not get to leak one while
            grading that channel.
    """
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        raise ChainedExemptionDerivationError(
            f"{module} did not parse: {type(exc).__name__}"
        ) from None


def adjudicators_in_sources(sources: Mapping[str, str]) -> tuple[Adjudicator, ...]:
    """Every module in the given sources that adjudicates chaining statically.

    READING A CAUSE IS THE WHOLE MEMBERSHIP TEST, and there is no import-shaped
    way out of it. CS-888 measured the one that existed: it excused six modules
    over an import, five of which read no cause at all, and an identical
    planted read was a finding in one module and invisible in six. Clearance is
    :data:`EXEMPT`, applied by :func:`classify` AFTER membership rather than
    instead of it, so an excused module is still counted, still listed and
    still reddens :func:`stale_exemptions` when its read goes away.

    Args:
        sources: Repo-relative module path to source text.

    Returns:
        The adjudicators, ordered by module path.

    Raises:
        ChainedExemptionDerivationError: A module did not parse.
    """
    found: list[Adjudicator] = []
    for module in sorted(sources):
        lines = static_cause_reads(_parse(module, sources[module]))
        if not lines:
            continue
        found.append(Adjudicator(module=module, lines=lines))
    return tuple(found)


def tracked_sources() -> Mapping[str, str]:
    """Read every tracked ``*.py`` in the repo.

    Returns:
        Repo-relative module path to source text.

    Raises:
        ChainedExemptionDerivationError: A file could not be read. Never
            swallowed - an unread file is a silently smaller population - and
            the cause is dropped with ``from None`` because an OSError renders
            the path it failed on.
    """
    sources: dict[str, str] = {}
    for relative in tracked_python_files():
        try:
            sources[relative] = (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ChainedExemptionDerivationError(
                f"{relative} could not be read: {type(exc).__name__}"
            ) from None
    return sources


@cache
def adjudicators() -> tuple[Adjudicator, ...]:
    """Every static chaining adjudicator in the tracked tree.

    Cached: the derivation walks every tracked module and several arms consume
    it.

    Returns:
        The adjudicators, ordered by module path.
    """
    return adjudicators_in_sources(tracked_sources())


def classify(site: Adjudicator, exempt: Mapping[str, Exemption] = EXEMPT) -> str:
    """The verdict for one adjudicator.

    A RECORDED VERDICT REQUIRES THE COUNT TO MATCH, and that is the whole of
    the CS-888 residual repair. Clearing on module membership alone hands a
    reason written for one read to every read the module later gains, so a
    module with more cause reads than its entry answers is UNRECORDED - the
    fail-closed direction. :func:`miscounted` is what says which way the count
    moved, because "unrecorded" alone would send a reader hunting for a missing
    entry that is in fact present.

    Args:
        site: The adjudicator to grade.
        exempt: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        One of :data:`VERDICT_OWNER`, :data:`VERDICT_RECORDED` or
        :data:`VERDICT_UNRECORDED`.
    """
    if site.module == OWNER:
        return VERDICT_OWNER
    recorded = exempt.get(site.module)
    if recorded is not None and recorded.sites == len(site.lines):
        return VERDICT_RECORDED
    return VERDICT_UNRECORDED


def unrecorded(
    sites: Sequence[Adjudicator], exempt: Mapping[str, Exemption] = EXEMPT
) -> tuple[str, ...]:
    """Modules deciding the chaining question with no reason on file.

    Args:
        sites: The adjudicators to grade.
        exempt: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        The offending module paths with their line numbers, ordered.
    """
    return tuple(
        f"{site.module}:{','.join(str(line) for line in site.lines)}"
        for site in sites
        if classify(site, exempt) == VERDICT_UNRECORDED
    )


def miscounted(
    sites: Sequence[Adjudicator], exempt: Mapping[str, Exemption] = EXEMPT
) -> tuple[str, ...]:
    """Recorded modules whose live read count is not the one on record.

    BOTH DIRECTIONS ARE A FINDING. More reads than the entry answers means a
    read nobody adjudicated is riding on a reason written for another one, and
    that is the fault this function exists for. FEWER means the entry now
    answers reads that are gone, which is the same silent widening
    :func:`stale_exemptions` catches when a module leaves the population
    outright - caught here one step earlier, while the module is still in it.

    Args:
        sites: The adjudicators to grade.
        exempt: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        One ``module: recorded N, live M`` entry per mismatch, ordered.
    """
    live = {site.module: len(site.lines) for site in sites}
    return tuple(
        f"{module}: recorded {entry.sites}, live {live[module]}"
        for module, entry in sorted(exempt.items())
        if module in live and entry.sites != live[module]
    )


def stale_exemptions(
    sites: Sequence[Adjudicator], exempt: Mapping[str, Exemption] = EXEMPT
) -> tuple[str, ...]:
    """Recorded modules that no longer adjudicate anything.

    An exemption outliving the code it describes is a silent widening: the next
    module to take that path inherits a reason nobody wrote for it.

    Args:
        sites: The adjudicators to grade.
        exempt: The exemption record. Defaults to :data:`EXEMPT`.

    Returns:
        The stale keys, ordered.
    """
    live = {site.module for site in sites}
    return tuple(sorted(key for key in exempt if key not in live))


def describe(sites: Sequence[Adjudicator]) -> str:
    """Render adjudicators for a failure message, paths only.

    Args:
        sites: The adjudicators to render.

    Returns:
        One ``module:lines`` entry per line.
    """
    return "\n".join(
        f"  {site.module}:{','.join(str(line) for line in site.lines)}" for site in sites
    )


def probe_sources() -> Iterator[tuple[str, str]]:
    """The planted sources the scope re-measurement probes a detector with.

    Yielded rather than held as a constant so a caller cannot mutate the set
    another arm depends on.

    Yields:
        A label and one planted source. ``cause-slot-only`` puts the handler
        binding in the ``from`` slot alone; ``object-in-args`` also puts it in
        the raised expression, which is a rendering on the args channel and must
        still be flagged by any detector claiming the narrow scope.
    """
    handler = "try:\n    pass\nexcept OSError as exc:\n"
    yield "cause-slot-only", handler + "    raise Boom(reason) from exc\n"
    yield "object-in-args", handler + "    raise Boom(exc) from exc\n"


#: The two bare names the mirror probe's plants call. One of them occupies the
#: slot the census selects and the other is a decoy in the slot it does not, so
#: which name comes back True identifies the slot.
PROBE_CLONE_NAMES: Final = ("_clone", "_wrap")


def mirror_probe_sources() -> Iterator[tuple[str, str]]:
    """The planted sources the MIRRORED slot rule is re-measured on.

    ``tests/pathless_clone_guard._slot`` is recorded in :data:`EXEMPT` against
    a reason claiming it selects the SAME slot as the census's
    ``_constructs_pathless_clone`` for the same form. These plants are what
    turns that sentence into a measurement.

    EACH PLANT PUTS A DIFFERENT BARE-NAME CALL IN EACH CANDIDATE SLOT WHERE THE
    FORM PERMITS ONE, and that is what makes the probe discriminating. The
    census's predicate answers a BOOLEAN rather than naming a slot, so the
    slot it chose is recovered by asking it one clone name at a time: a plant
    calling the same name in both slots would answer True either way and could
    not tell a mirror that agrees from one that has swapped them. ``suppressed``
    carries a literal ``None`` in the cause slot because the form requires it,
    so its decoy is probed for a False rather than for the other name.

    Yielded rather than held as a constant so a caller cannot mutate the set
    another arm depends on.

    Yields:
        A label and one planted source. The forms the labels stand for are
        derived by the census's own ``_form_of`` in the arm, never spelled
        here - the census owns those constants.
    """
    handler = "try:\n    pass\nexcept OSError as exc:\n"
    yield "explicit-two-calls", handler + "    raise _wrap(exc) from _clone(exc)\n"
    yield "suppressed-clone", handler + "    raise _clone(exc) from None\n"
    yield "implicit-clone", handler + "    raise _clone(exc)\n"
    yield "bare-reraise", handler + "    raise\n"
