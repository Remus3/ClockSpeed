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
reason about something else is the same fault as immunity earned by importing a name. Each entry now
records HOW MANY sites it answers, the shape ``tests/test_docs_citations.py`` already uses for its
``Disposition`` table, and ``test_a_second_cause_read_in_an_already_exempt_module_is_reported`` is
the arm that keeps it honest.

THE CENSUS ARMS THEMSELVES ARE STILL NOT IN THE POPULATION AT ALL. They read
``__cause__`` on live exceptions, which is measurement rather than adjudication,
and the separation between the two names is what keeps them out.
"""

from __future__ import annotations

import ast
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


def test_the_recorded_site_counts_match_the_live_tree() -> None:
    """Every entry answers exactly the reads its module actually has."""
    off = guard.miscounted(guard.adjudicators())

    assert not off, (
        "exemption entr(ies) record a site count the live tree does not have; "
        f"re-derive the count and check the reason still covers every read: {off}"
    )


def test_a_recorded_count_that_no_longer_matches_is_reported_both_ways() -> None:
    """The count is checked in BOTH directions, proven on fabricated records.

    A count that only ever reddens upward would let an entry keep answering
    reads that are gone, which is the silent widening
    :func:`guard.stale_exemptions` catches one step later, once the module has
    left the population entirely.

    Fabricated rather than planted, because what is being graded here is the
    comparison itself rather than the sweep that feeds it.
    """
    population = guard.adjudicators()
    verdicts = []
    for delta in (1, -1):
        fabricated = {
            module: guard.Exemption(why=entry.why, sites=entry.sites + delta)
            for module, entry in guard.EXEMPT.items()
        }
        verdicts.append((delta, guard.miscounted(population, fabricated)))

    silent = [delta for delta, found in verdicts if not found]
    assert not silent, (
        "a recorded site count that does not match the live tree went unreported "
        f"for delta(s) {silent}, so the count is checked in one direction only"
    )

    still_cleared = [
        delta
        for delta, _ in verdicts
        if not guard.unrecorded(
            population,
            {
                module: guard.Exemption(why=entry.why, sites=entry.sites + delta)
                for module, entry in guard.EXEMPT.items()
            },
        )
    ]
    assert not still_cleared, (
        "a module whose recorded count no longer matches was still CLEARED for "
        f"delta(s) {still_cleared}; miscounted() reported it but classify() did not act"
    )
