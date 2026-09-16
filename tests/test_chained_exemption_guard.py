"""CS-857 - arms over the static chaining-adjudicator sweep.

WHAT IS BEING GRADED. ``tests/chained_exemption_guard.py`` derives every tracked
module that decides, at parse time, what a chained raise means - by reading the
``cause`` field CPython gives ``ast.Raise`` - and requires each one to be the
census or to carry a recorded reason. These arms prove the sweep fires, prove it
stays silent on the two shapes that look similar and are not the defect, and
re-measure each recorded reason rather than believing it.

EVERY POSITIVE HERE IS SYNTHETIC. ``memory/an-empty-population-satisfies-every-zero.md``
records why: a sweep that has only ever seen clean input is a sweep nobody has
proved fires, and a green run over an empty population satisfies every zero. The
plants are source STRINGS rather than files, so the sweep is exercised on input
that cannot drift when the tree does, and no arm here depends on a live finding
staying live.

THE DEFERRAL PATH IS GONE, AND THIS NOTE RECORDS THE CHANGE RATHER THAN BEING
OVERTAKEN BY IT. It used to say the path was exercised live as well as
synthetically, because CS-885 added ``tests/pathless_clone_guard.py``, which
reads a Raise node's cause and hands the question of what that cause MEANS to
the census by importing it. CS-888 then measured what that import actually
bought: blanket, permanent, module-wide immunity for the SIX modules importing
it at the time, five of which read no cause at all, and an identical four-line
planted cause read that was a finding in one module and invisible in all six.
Those are the numbers of that measurement rather than a live count - the arm
below derives its subject set every run, and the set has already grown past six
with this very module among the new members. The clearance is abolished and
``tests/pathless_clone_guard.py`` now carries a recorded reason instead.
``test_importing_the_owner_confers_no_immunity_from_the_sweep`` replaced the arm
that used to grade the deferral branch: it plants the same four lines into every
LIVE importer and into a SYNTHETIC one, and asserts every single subject is
reported. The synthetic subject is what stops the arm going vacuous if the live
importer set ever empties.

THIS MODULE IS ITSELF ONE OF THOSE IMPORTERS, deliberately rather than by
oversight. It imports the census to reach ``_form_of`` and
``_constructs_pathless_clone`` for the mirror probe at the foot of this file, so
it lands in its own derived subject set and is planted into like every other
importer. Under the abolished rule this would have been a module grading
immunity from inside the immune set.

AND THE CLEARANCE ITSELF CARRIED CS-888'S SHAPE ONE LEVEL DOWN, which an adjudicator measured
against the first repair rather than reading. Abolishing import-immunity moved
``tests/pathless_clone_guard.py`` into :data:`tests.chained_exemption_guard.EXEMPT`, and the record
was keyed by MODULE PATH ALONE - so a reason written about the ``_slot`` mirror silently forgave any
further cause read that module ever gained. Measured: the identical four-line plant went unreported
in BOTH recorded modules while being named at once in every other. Immunity earned by holding a
reason about something else is the same fault as immunity earned by importing a name. Each entry
records WHICH reads it answers, and the arm that keeps it honest is
``test_a_second_cause_read_in_an_already_exempt_module_is_reported``.

AND THE FIRST REPAIR FOR THAT WAS A COUNT, WHICH ANSWERS HOW MANY AND NEVER WHICH - CS-893. A count
is blind to a COMPENSATING SWAP: delete one recorded read and add an unrelated adjudicating one in
the same edit, and the cardinality is unchanged while the new read rides under a reason written
about the old one. An adversary demonstrated it on the live tree and
``test_a_compensating_swap_that_keeps_the_count_is_reported`` reproduces it here, over BOTH recorded
modules, against the LIVE record. Each entry now answers an IDENTITY per read -
``qualname::receiver``, the shape ``Site.key`` and ``Copy.key`` in this tree already use - kept as a
multiset, so the cardinality the count carried is carried too and nothing the old key caught is
lost. The identical fault in the ``Disposition`` table ``tests/test_citation_tables.py`` owns is
unrepaired and is filed as CS-1121.

THE CENSUS ARMS THEMSELVES ARE STILL NOT IN THE POPULATION AT ALL. They read
``__cause__`` on live exceptions, which is measurement rather than adjudication,
and the separation between the two names is what keeps them out.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from tests import chained_exemption_guard as guard
from tests.chained_cause_guard import (
    FORM_BARE,
    FORM_EXPLICIT,
    FORM_IMPLICIT,
    FORM_SUPPRESSED,
    _constructs_pathless_clone,
    _form_of,
)
from tests.pathless_clone_guard import _called_name, _slot
from tests.test_verify_env import rendered_exception_lines

MAX_ASCII_BYTE: Final = 0x7E

#: The modules that read a raise's ``cause`` field in the live tree: the census
#: that owns the question, the module whose slot rule MIRRORS it, and the one
#: whose read is scoped to a different channel. PINNED so that ADDING a recorded
#: reason is a deliberate act - the unrecorded arm below already reddens on a
#: new finding, but a new EXEMPT entry would otherwise slip in silently.
LIVE_ADJUDICATORS: Final = 3

#: A detector that decides for itself that a chained raise is clean, in the
#: shape the live defect wore: a Raise node's cause fed into a suppression set.
PLANTED_ADJUDICATOR: Final = '''"""A planted detector that exempts the chained shape."""

import ast


def scan(tree):
    """Collect the cause slots this detector refuses to report."""
    safe = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.cause, ast.Name):
            safe.add(id(node.cause))
    return safe
'''

#: The same plant, importing the census instead of answering alone. IT IS A
#: POSITIVE NOW, NOT A NEGATIVE, and CS-888 is why: the import used to clear it
#: and now buys it nothing, so the only thing separating it from the plant above
#: is an import that decides nothing. The source is unchanged from when it was a
#: negative, which is what makes the inversion legible.
PLANTED_DEFERRING: Final = '''"""A planted detector that defers to the census."""

import ast

from tests import chained_cause_guard


def scan(tree):
    """Collect cause slots, then let the owner grade them."""
    found = [node.cause for node in ast.walk(tree) if isinstance(node, ast.Raise)]
    return chained_cause_guard.classify, found
'''

#: Reading a LIVE exception's chain link. Measurement, not adjudication - the
#: shape tests/save/test_world.py and tests/save/test_header.py wear.
PLANTED_RUNTIME_CHAIN: Final = '''"""A planted module measuring a live chain."""


def check(caught):
    """Assert what the raised exception actually carried."""
    assert caught.value.__cause__ is None
'''

#: Reasoning about Raise WITHOUT reaching the cause - the shape
#: tests/test_handler_exception_rendering.py wears, where a raise is one of the
#: constructs that lets control escape a handler. Never the defect.
PLANTED_RAISE_ONLY: Final = '''"""A planted module treating raise as a control-flow escape."""

import ast

ESCAPING_NODES = (ast.Call, ast.Raise, ast.Assert)


def escapes(node):
    """Whether this node can move control out of the handler."""
    return isinstance(node, ESCAPING_NODES)
'''

#: The cause field reached through getattr rather than attribute syntax.
PLANTED_GETATTR: Final = '''"""A planted detector reaching the cause through getattr."""

import ast


def scan(tree):
    """Collect cause slots without attribute syntax."""
    return [getattr(node, "cause") for node in ast.walk(tree) if isinstance(node, ast.Raise)]
'''

#: The synthetic importer's key in the CS-888 subject set. Never a real path -
#: the sweep takes a sources MAPPING, so no plant reaches disk.
SYNTHETIC_IMPORTER: Final = "planted/deferring_module.py"

#: The identical static cause read appended to a live module, to measure whether
#: that module is still IN the population. Held as a source STRING, so carrying
#: it does not put THIS module in the population: ast.parse sees a Constant.
APPENDED_CAUSE_READ: Final = '''

def planted_static_cause_read(node):
    """Planted: decide, at parse time, what this chained raise means."""
    return node.cause
'''


def _flagged(source: str) -> tuple[str, ...]:
    """Run the sweep over one planted source and return the unrecorded modules.

    Args:
        source: The planted module source.

    Returns:
        The unrecorded findings, against an EMPTY exemption record so a plant
        cannot be silenced by an entry written for the live tree.
    """
    sites = guard.adjudicators_in_sources({"planted/module.py": source})
    return guard.unrecorded(sites, {})


def _planted_raise(source: str) -> tuple[ast.Raise, ast.ExceptHandler | None]:
    """The single raise in a mirror plant, with the handler it sits in.

    THIS IS NOT THE CENSUS'S SCOPE WALK, and the difference is deliberate rather
    than overlooked. ``_walk`` decides which raises are censused at all; the
    question here is which SLOT two selectors pick once a raise and a form are
    already in hand, so each plant carries exactly one raise and at most one
    handler and the pairing is unambiguous. The FORM is still derived by the
    census's own ``_form_of`` rather than assumed.

    Args:
        source: One plant from ``guard.mirror_probe_sources``.

    Returns:
        The raise and its enclosing handler, or None when there is none.
    """
    tree = ast.parse(source)
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
    raises = [node for node in ast.walk(tree) if isinstance(node, ast.Raise)]
    return raises[0], (handlers[0] if handlers else None)


# ---------------------------------------------------------------------------
# The sweep fires - proven on plants, never on a live finding
# ---------------------------------------------------------------------------


def test_a_planted_static_exemption_of_the_chained_shape_is_flagged() -> None:
    """The defect shape is caught: a Raise node's cause fed to a suppression."""
    findings = _flagged(PLANTED_ADJUDICATOR)

    assert len(findings) == 1, "the sweep missed a planted static chaining adjudicator"


def test_the_cause_field_is_caught_through_getattr_too() -> None:
    """Attribute syntax is not the only way to name the field."""
    findings = _flagged(PLANTED_GETATTR)

    assert len(findings) == 1, "the sweep reads attribute syntax only"


def test_a_planted_adjudicator_that_imports_the_census_is_still_flagged() -> None:
    """CS-888 - the import that used to clear this plant now buys it nothing.

    This plant and the flagged plant above differ by an import and nothing
    else, which is exactly what makes it the isolating arm for the abolished
    clearance. It asserted ``not findings`` until CS-888 measured what the
    import was worth.
    """
    findings = _flagged(PLANTED_DEFERRING)

    assert len(findings) == 1, "importing the census still clears a planted cause read"


# ---------------------------------------------------------------------------
# The two shapes that look similar and are not the defect
# ---------------------------------------------------------------------------


def test_a_runtime_chain_read_is_not_an_adjudicator() -> None:
    """Reading __cause__ on a live exception is evidence, not adjudication.

    This is the shape the save suites wear. Flagging it would put the project's
    own chain MEASUREMENTS in the population, which is the direction that gets a
    guard switched off.
    """
    findings = _flagged(PLANTED_RUNTIME_CHAIN)

    assert not findings, "a runtime __cause__ read was treated as adjudication"


def test_a_raise_with_no_cause_read_is_not_an_adjudicator() -> None:
    """Reasoning about raise is not reasoning about chaining.

    tests/test_handler_exception_rendering.py holds ast.Raise in a tuple of
    control-flow escapes and never reaches a cause. It must stay out.
    """
    findings = _flagged(PLANTED_RAISE_ONLY)

    assert not findings, "a raise-only module was treated as a chaining adjudicator"


def test_the_two_negatives_differ_from_the_positives_only_where_intended() -> None:
    """The negatives are not silent for some accidental shared reason.

    Each negative is checked to parse and to be non-empty, so "not flagged"
    cannot be an artifact of an unparseable or trivial plant. The deferring
    plant left this list when CS-888 made it a positive.
    """
    parsed = [len(ast.parse(source).body) for source in (PLANTED_RUNTIME_CHAIN, PLANTED_RAISE_ONLY)]

    assert min(parsed) > 0, "a negative plant is empty, so its silence proves nothing"


# ---------------------------------------------------------------------------
# The live tree
# ---------------------------------------------------------------------------


def test_the_tracked_tree_records_every_chaining_adjudicator() -> None:
    """No tracked module decides the chaining question with no reason on file."""
    sites = guard.adjudicators()
    offending = guard.unrecorded(sites)

    assert not offending, (
        "module(s) statically decide what a chained raise means without a recorded "
        f"reason in {guard.OWNER}'s exemption record: {offending}"
    )


def test_the_owner_adjudicates_rather_than_being_excused_over_nothing() -> None:
    """The owner is in the population, so its pass is a pass over real reads.

    An owner that read no causes would be excused over an empty set, and the
    arm above would be green having graded nothing on the one module the whole
    design routes through.
    """
    owning = [site for site in guard.adjudicators() if site.module == guard.OWNER]
    reads = sum(len(site.lines) for site in owning)

    assert reads > 0, f"{guard.OWNER} reads no cause field, so it owns nothing"


def test_the_recorded_module_is_in_the_population_it_is_recorded_for() -> None:
    """Every recorded reason describes a module that still adjudicates.

    An exemption outliving its code silently widens: the next module to take
    that path inherits a reason nobody wrote for it.
    """
    stale = guard.stale_exemptions(guard.adjudicators())

    assert not stale, f"exemption(s) outlived the code they describe: {stale}"


def test_a_reason_for_a_module_that_left_the_population_is_reported() -> None:
    """CS-894 - the stale leg carries a planted positive, not a live zero.

    THE ARM ABOVE IS SATISFIED BY A LEG THAT REPORTS NOTHING AT ALL. It asserts
    the live tree is clean, and a clean tree is what an empty return also looks
    like; measured before this arm existed, :func:`guard.stale_exemptions`
    replaced by an empty return left every arm in this module green. That is
    the shape ``memory/an-empty-population-satisfies-every-zero.md`` records,
    and its sibling :func:`guard.mismatched` was given a fabricated positive in
    the same commit while this leg was not.

    THE PLANT IS A RECORDED REASON FOR A MODULE THAT DOES NOT EXIST, so no live
    finding is depended on and the subject cannot drift when the tree does. Its
    absence from the population is ASSERTED rather than assumed, because a plant
    that accidentally names a live adjudicator is a plant the leg is right to
    stay silent about.
    """
    live = guard.adjudicators()
    departed = "tests/planted_departed_adjudicator.py"

    assert departed not in {site.module for site in live}, (
        f"the plant {departed} is a live adjudicator, so the leg is right to "
        f"stay silent and this arm proves nothing"
    )

    planted = guard.Exemption(reads=("planted::node",), why="planted")

    stale = guard.stale_exemptions(live, {departed: planted})

    assert stale == (departed,), (
        f"a recorded reason for a module that adjudicates nothing went "
        f"unreported; stale_exemptions() answered {stale}"
    )


def test_a_reason_for_a_module_still_in_the_population_is_not_reported() -> None:
    """CS-894 - the negative direction of the same leg.

    Without this, the positive above is met by a leg that reports every key it
    is handed. Graded on a record naming a module the live population DOES
    hold, so the two arms together pin both answers rather than one.
    """
    live = guard.adjudicators()
    assert live, "the population is empty, so this arm grades nothing"
    resident = sorted(site.module for site in live)[0]

    planted = guard.Exemption(reads=("planted::node",), why="planted")

    stale = guard.stale_exemptions(live, {resident: planted})

    assert stale == (), (
        f"{resident} still adjudicates and its recorded reason was reported "
        f"stale anyway; stale_exemptions() answered {stale}"
    )


def test_the_population_holds_the_mirroring_module_and_nothing_unaccounted_for() -> None:
    """CS-888 - the population is pinned, and the mirror is in it.

    ``tests/pathless_clone_guard.py`` reads a cause inside ``_slot`` and held
    blanket immunity for importing the census until CS-888. Its membership is
    asserted by NAME rather than by count alone, because a count can be
    satisfied by the wrong three modules.

    THE COUNT IS PINNED IN CODE AND NOWHERE ELSE, which is what CLAUDE.md
    section 4 asks for. The unrecorded arm above already reddens on a new
    FINDING; what this adds is that a new RECORDED reason cannot be added
    silently either. Re-derive it deliberately when the population genuinely
    moves.
    """
    population = guard.adjudicators()
    modules = sorted(site.module for site in population)

    count = len(population)
    assert count == LIVE_ADJUDICATORS, (
        f"the static chaining-adjudicator population is {count}, pinned at "
        f"{LIVE_ADJUDICATORS}. A module joined or left the set that reads a raise's "
        f"cause: {modules}"
    )
    assert "tests/pathless_clone_guard.py" in modules, (
        "the module whose slot rule MIRRORS the census left the population; if its "
        f"cause read is gone, retire its exemption with it. Population: {modules}"
    )


# ---------------------------------------------------------------------------
# CS-888 - an import buys nothing
# ---------------------------------------------------------------------------


def test_importing_the_owner_confers_no_immunity_from_the_sweep() -> None:
    """CS-888 - an import is not a fact about how a module reads a cause.

    THE SUBJECT SET IS DERIVED LIVE, NOT PINNED. Every module that imports the
    census gets the identical four-line static cause read appended to it, and
    every one of them must be reported. A pinned set was the other candidate
    repair and it fails the same way the abolished clearance did: a plant
    inside an already-pinned module does not change the set, so the pin reddens
    on a seventh importer and stays silent on the read that matters.

    THE SYNTHETIC SUBJECT IS WHY THIS IS NOT VACUOUS. If the live importer set
    ever empties, a derived-set arm would pass over nothing;
    :data:`SYNTHETIC_IMPORTER` carries the same plant in a module that exists
    only as a string, so the branch is exercised regardless of the live tree.

    Graded against an EMPTY exemption record, so a plant cannot be silenced by
    a reason written for the live module underneath it.
    """
    sources = dict(guard.tracked_sources())
    importers = sorted(
        module for module, source in sources.items() if guard.defers_to_owner(ast.parse(source))
    )
    planted = dict(sources)
    for module in importers:
        planted[module] = sources[module] + APPENDED_CAUSE_READ
    planted[SYNTHETIC_IMPORTER] = PLANTED_DEFERRING
    targets = [*importers, SYNTHETIC_IMPORTER]

    reported = {
        entry.split(":", 1)[0]
        for entry in guard.unrecorded(guard.adjudicators_in_sources(planted), {})
    }
    missed = sorted(module for module in targets if module not in reported)

    count = len(missed)
    assert count == 0, (
        f"{count} of {len(targets)} module(s) hold blanket immunity from the "
        f"chaining-adjudicator population for the mere act of importing "
        f"{guard.OWNER}; an identical planted cause read is invisible in each: {missed}"
    )


def test_the_live_subject_set_of_the_immunity_arm_is_not_empty() -> None:
    """CS-894 - the derived subject set is asserted, not assumed.

    THE ARM ABOVE DERIVES ITS SUBJECTS LIVE AND CARRIES A SYNTHETIC ONE SO IT
    IS NEVER VACUOUS. That is what stops it passing over nothing - and it is
    also what lets it pass while the LIVE half of the derivation returns
    nothing: measured before this arm existed, :func:`guard.defers_to_owner`
    forced False left every arm in this module green, the subject set having
    silently degraded to its one synthetic member.

    NO COUNT IS PINNED HERE, DELIBERATELY. The set is derived every run
    precisely so a seventh importer joins it without an edit, and pinning its
    size would put a measured number in a second place to drift. Non-empty is
    the property the flagship arm actually depends on.
    """
    sources = dict(guard.tracked_sources())
    importers = sorted(
        module for module, source in sources.items() if guard.defers_to_owner(ast.parse(source))
    )

    count = len(importers)
    assert count > 0, (
        "no tracked module imports the census, so "
        "test_importing_the_owner_confers_no_immunity_from_the_sweep grades "
        "its synthetic subject alone and the live derivation is unmeasured"
    )


def test_the_owner_import_detector_answers_both_ways_on_planted_sources() -> None:
    """CS-894 - the planted positive for the subject derivation itself.

    The arm above reddens when the detector answers False for everything, and
    a detector answering True for everything would satisfy it just as well
    while making the subject set the whole tracked tree.

    THE PAIR IS BUILT HERE RATHER THAN TAKEN FROM THE TWO MODULE CONSTANTS, and
    the difference matters enough that a verifier refuted the first draft of
    this arm over it. :data:`PLANTED_DEFERRING` and :data:`PLANTED_ADJUDICATOR`
    are both real detector plants and they differ in their docstring, their
    whole ``scan`` body and their return expression as well as in the import.
    Only one of those differences is one :func:`guard.defers_to_owner` can
    READ - it walks ``Import`` and ``ImportFrom`` and nothing else - but an arm
    graded on that pair is satisfied by any detector keyed on the other three,
    so the positive here is :data:`PLANTED_ADJUDICATOR` with the owner import
    SPLICED IN and nothing else changed. The import is composed from
    :data:`guard.OWNER_MODULE`, so renaming the owner moves the plant with it
    instead of leaving a plant that imports a module nobody has.
    """
    negative = PLANTED_ADJUDICATOR
    positive = negative.replace(
        "import ast\n",
        f"import ast\n\nfrom tests import {guard.OWNER_MODULE}\n",
        1,
    )

    assert positive != negative, "the splice landed nowhere, so the pair is one source twice"

    assert guard.defers_to_owner(ast.parse(positive)), (
        "the planted module differs from its twin by the census import alone "
        "and the detector did not see it"
    )
    assert not guard.defers_to_owner(ast.parse(negative)), (
        "the planted module imports no census and the detector claimed it did"
    )
    assert guard.defers_to_owner(ast.parse(PLANTED_DEFERRING)), (
        "the live-shaped deferring plant imports the census and the detector did not see it"
    )


def test_the_failure_renderer_names_the_module_and_every_line_it_is_given() -> None:
    """CS-894 sibling sweep - the renderer is exercised on a green run too.

    :func:`guard.describe` builds the text every finding here is reported
    THROUGH, and it is reached only when an arm is already failing - so on a
    green tree nothing runs it. Measured alongside the two legs this item
    names: the renderer replaced by an empty string left every arm in this
    module green, which is the same "deleted without a single arm noticing"
    shape and is swept here rather than filed.

    ITS FAILURE MODE IS A DEGRADED MESSAGE RATHER THAN A MISSED FINDING, which
    is why it is one arm and not three. What the arm pins is that a reported
    site can be traced back to a module and a line - a renderer that drops
    either turns every finding in this file into an unactionable one.
    """
    sites = guard.adjudicators_in_sources({"planted/rendered.py": PLANTED_ADJUDICATOR})

    assert len(sites) == 1, f"the plant yielded {len(sites)} adjudicator(s), expected 1"

    rendered = guard.describe(sites)

    assert sites[0].module in rendered, (
        f"the renderer dropped the module of the site it was given: {rendered!r}"
    )
    missing = [line for line in sites[0].lines if str(line) not in rendered]
    count = len(missing)
    assert count == 0, (
        f"the renderer dropped {count} of the {len(sites[0].lines)} line(s) it "
        f"was given: {rendered!r}"
    )


def test_the_planted_cause_read_is_what_the_subject_arm_is_measuring() -> None:
    """The plant appended above genuinely creates a cause read, and only one.

    Without this the arm above could pass because the plant is inert and every
    subject was already in the population for its own reasons. Measured on a
    module with NO cause read of its own, so the delta is the plant.
    """
    before = guard.adjudicators_in_sources({"planted/inert.py": PLANTED_RAISE_ONLY})
    after = guard.adjudicators_in_sources(
        {"planted/inert.py": PLANTED_RAISE_ONLY + APPENDED_CAUSE_READ}
    )

    assert not before, "the base plant already reads a cause, so the delta proves nothing"

    reads = sum(len(site.lines) for site in after)
    assert reads == 1, f"the appended plant contributed {reads} static cause read(s), expected 1"


# ---------------------------------------------------------------------------
# The recorded reasons are re-measured, never believed - ADR 0008
# ---------------------------------------------------------------------------


def test_the_recorded_scope_is_re_measured_rather_than_believed() -> None:
    """The recorded reason for tests/test_verify_env.py claims a narrow scope.

    The reason on record says its cause read exempts the ``from`` slot ALONE,
    because an object in the cause slot is not in the new message's args - and
    NOT that a chained cause goes unrendered. Those two claims are different
    and they are told apart by measurement here, not by reading the sentence:

      * a chained raise whose args carry no handler binding is silent, which is
        the exemption doing its job on that module's own channel;
      * a chained raise whose args DO carry the binding is still flagged, which
        a wholesale belief that chaining is safe could not produce.

    Widen that exemption to the whole raise and the second probe goes silent
    while the recorded sentence still reads correct. That is the failure this
    arm exists to make impossible - the fence CS-857 first built was a comment
    nothing enforced, and a later session hunting this exact shape found neither
    live record.
    """
    probes = dict(guard.probe_sources())
    cause_slot_only = rendered_exception_lines(probes["cause-slot-only"])
    object_in_args = rendered_exception_lines(probes["object-in-args"])

    assert not cause_slot_only, (
        "the recorded reason says the cause slot is exempt on that module's channel, "
        "but a chained raise with a clean message is now flagged"
    )
    assert len(object_in_args) > 0, (
        "the recorded scope has WIDENED: the exception object now reaches the raised "
        "message's args on a chained raise and is no longer flagged, which is the "
        "wholesale chaining exemption the recorded reason denies being"
    )


def test_the_mirrored_slot_rule_is_re_measured_rather_than_believed() -> None:
    """The recorded reason for tests/pathless_clone_guard.py claims a MIRROR.

    CS-888 put that module in the population and its reason says its cause read
    mirrors ``chained_cause_guard._constructs_pathless_clone`` deliberately -
    that the two select the SAME slot for the same form. This measures that
    rather than reading it.

    HOW THE CENSUS'S CHOICE IS RECOVERED. Its predicate answers a boolean, not
    a slot name, so it is asked one clone name at a time: the plants put a
    DIFFERENT bare-name call in each candidate slot where the form permits one,
    so whichever name comes back True identifies the slot the census selected.
    The mirror's choice is read straight off ``_slot``.

    WIDEN THE MIRROR AND THIS REDDENS while the recorded sentence still reads
    correct - swap the two slots on a form and the names disagree; hand back a
    slot for the implicit form, which the census deliberately gives none, and
    the mirror names one where the census names nothing.

    THE FORMS ARE DERIVED BY THE CENSUS'S OWN ``_form_of``, so a plant that
    stops being the form it was written as fails here rather than quietly
    grading a different question.
    """
    expected = {
        "explicit-two-calls": FORM_EXPLICIT,
        "suppressed-clone": FORM_SUPPRESSED,
        "implicit-clone": FORM_IMPLICIT,
        "bare-reraise": FORM_BARE,
    }
    disagreed: list[str] = []
    selecting = 0
    for label, source in guard.mirror_probe_sources():
        node, handler = _planted_raise(source)
        form = _form_of(node, handler)
        assert form == expected[label], (
            f"the {label} plant no longer derives as {expected[label]}: {form}"
        )
        assert form is not None, f"the {label} plant derives no chained form at all"
        mirror = _called_name(_slot(node, form))
        census = next(
            (
                name
                for name in guard.PROBE_CLONE_NAMES
                if _constructs_pathless_clone(node, form, frozenset({name}))
            ),
            None,
        )
        selecting += 1 if mirror is not None else 0
        if mirror != census:
            disagreed.append(f"{label} ({form}): mirror picked {mirror}, census picked {census}")

    count = len(disagreed)
    assert count == 0, (
        f"the MIRROR the recorded reason for tests/pathless_clone_guard.py rests on has "
        f"broken on {count} form(s); the two select different slots, so the clone guard "
        f"is watching sites the census is not: {disagreed}"
    )
    assert selecting > 0, (
        "no plant produced a slot at all, so the agreement above is an agreement about "
        "nothing - memory/an-empty-population-satisfies-every-zero.md"
    )


# ---------------------------------------------------------------------------
# House rules
# ---------------------------------------------------------------------------


def test_this_test_module_is_seven_bit_ascii() -> None:
    """CLAUDE.md non-negotiable 4, asserted on the raw bytes of this file."""
    raw = Path(__file__).resolve().read_bytes()

    offending = sum(1 for byte in raw if byte > MAX_ASCII_BYTE)

    assert offending == 0, f"{offending} byte(s) above 0x{MAX_ASCII_BYTE:02X}"


def test_the_guard_module_is_seven_bit_ascii() -> None:
    """The guard it grades obeys the same rule."""
    raw = (guard.REPO_ROOT / "tests" / "chained_exemption_guard.py").read_bytes()

    offending = sum(1 for byte in raw if byte > MAX_ASCII_BYTE)

    assert offending == 0, f"{offending} byte(s) above 0x{MAX_ASCII_BYTE:02X}"


def test_a_second_cause_read_in_an_already_exempt_module_is_reported() -> None:
    """CS-888 residual - a reason answers SITES, not a module forever.

    THIS IS THE ARM THE SITE COUNT EXISTS FOR; without it the count is
    decoration. Every recorded module gets the SAME four-line plant the subject
    arm above uses, and each must be reported - against the LIVE exemption
    record rather than an empty one, because an empty record would report them
    whatever the clearance rule was and prove nothing about it.

    THE SUBJECT SET IS DERIVED FROM :data:`guard.EXEMPT` ITSELF, so an entry
    added later is planted into without anyone remembering to extend a list.

    Measured before the repair: both recorded modules absorbed the plant in
    silence, while the same four lines in any module with no entry were named
    at once. The clearance had become immunity earned by holding a reason about
    a different read - CS-888's own shape, one level down from the import.
    """
    sources = dict(guard.tracked_sources())
    absorbed: list[str] = []
    for module in sorted(guard.EXEMPT):
        planted = dict(sources)
        planted[module] = sources[module] + APPENDED_CAUSE_READ
        reported = {
            entry.split(":", 1)[0]
            for entry in guard.unrecorded(guard.adjudicators_in_sources(planted))
        }
        if module not in reported:
            absorbed.append(module)

    count = len(absorbed)
    assert count == 0, (
        f"{count} recorded module(s) absorbed a SECOND, unrelated static cause read "
        f"under a reason written for a different one: {absorbed}"
    )


def test_the_recorded_reads_are_the_ones_the_live_tree_has() -> None:
    """Every entry answers exactly the reads its module actually has."""
    off = guard.mismatched(guard.adjudicators())

    assert not off, (
        "exemption entr(ies) answer reads the live tree does not have, or miss "
        f"reads it does; re-derive them and check the reason still covers each: {off}"
    )


def _perturbed(delta: int) -> Mapping[str, guard.Exemption]:
    """The live record with one read added to, or removed from, every entry.

    Args:
        delta: 1 to append an identity nothing live carries, -1 to drop the
            first answered read.

    Returns:
        The fabricated record.
    """
    fabricated = {}
    for module, entry in guard.EXEMPT.items():
        reads = (*entry.reads, "fabricated::absent") if delta == 1 else entry.reads[1:]
        fabricated[module] = guard.Exemption(why=entry.why, reads=reads)
    return fabricated


def test_a_recorded_read_set_that_no_longer_matches_is_reported_both_ways() -> None:
    """The record is checked in BOTH directions, proven on fabricated records.

    A comparison that only ever reddens on an ARRIVAL would let an entry keep
    answering reads that are gone, which is the silent widening
    :func:`guard.stale_exemptions` catches one step later, once the module has
    left the population entirely.

    Fabricated rather than planted, because what is being graded here is the
    comparison itself rather than the sweep that feeds it.
    """
    population = guard.adjudicators()
    verdicts = [(delta, guard.mismatched(population, _perturbed(delta))) for delta in (1, -1)]

    silent = [delta for delta, found in verdicts if not found]
    assert not silent, (
        "a recorded read set that does not match the live tree went unreported "
        f"for delta(s) {silent}, so the record is checked in one direction only"
    )

    still_cleared = [
        delta for delta, _ in verdicts if not guard.unrecorded(population, _perturbed(delta))
    ]
    assert not still_cleared, (
        "a module whose recorded reads no longer match was still CLEARED for "
        f"delta(s) {still_cleared}; mismatched() reported it but classify() did not act"
    )


def _swap_one_cause_read(source: str, lines: Sequence[int]) -> str:
    """Rewrite the first recorded cause read into a read of another field.

    The rewrite is textual and touches ONE line, so the module still parses and
    every other read on it is left exactly as written. ``exc`` is chosen because
    :func:`guard.static_cause_reads` matches on the field NAME, so the rewritten
    attribute leaves the population while the statement around it does not move.

    Args:
        source: The module source.
        lines: The recorded read lines, ascending.

    Returns:
        The source with one fewer static cause read.
    """
    rows = source.splitlines(keepends=True)
    index = lines[0] - 1
    rows[index] = rows[index].replace(f".{guard.CAUSE_FIELD}", ".exc", 1)
    return "".join(rows)


def test_a_compensating_swap_that_keeps_the_count_is_reported() -> None:
    """CS-893 - a reason answers IDENTIFIED reads, never a cardinality.

    A COUNT SAYS HOW MANY READS A REASON FORGIVES AND NEVER WHICH. Delete one
    recorded read and add an unrelated adjudicating one in the same edit, and
    the cardinality is unchanged - so the verdict stays ``recorded`` and a read
    nobody adjudicated rides under a reason written about something else. That
    is CS-888's own thesis one level down from the site count that answered it.

    THE PLANT IS THE SWAP RATHER THAN THE APPEND, and the arm above is what
    makes the difference legible: it appends alone, which a count DOES catch.
    Here the append is paid for by a deletion, and the count cannot see it.

    GRADED AGAINST THE LIVE RECORD rather than an empty one, because an empty
    record reports every module whatever the clearance rule is and would prove
    nothing about this one. The parity control asserts the count really is
    unchanged, so the arm cannot pass because the swap failed to balance.
    """
    sources = dict(guard.tracked_sources())
    live = {site.module: site for site in guard.adjudicators_in_sources(sources)}
    absorbed: list[str] = []
    unbalanced: list[str] = []
    for module in sorted(guard.EXEMPT):
        before = live[module]
        swapped = dict(sources)
        swapped[module] = _swap_one_cause_read(sources[module], before.lines) + APPENDED_CAUSE_READ
        after = {site.module: site for site in guard.adjudicators_in_sources(swapped)}[module]
        if len(after.lines) != len(before.lines):
            unbalanced.append(f"{module}: {len(before.lines)} -> {len(after.lines)}")
            continue
        reported = {
            entry.split(":", 1)[0]
            for entry in guard.unrecorded(guard.adjudicators_in_sources(swapped))
        }
        if module not in reported:
            absorbed.append(module)

    assert not unbalanced, (
        "the swap did not preserve the read count, so this arm would grade a "
        f"plain append rather than a compensating swap: {unbalanced}"
    )
    count = len(absorbed)
    assert count == 0, (
        f"{count} recorded module(s) absorbed a COMPENSATING SWAP - one recorded "
        "read deleted and an unrelated adjudicating one added - with the site "
        f"count unchanged, so the reason answers a cardinality: {absorbed}"
    )
