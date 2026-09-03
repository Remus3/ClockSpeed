"""CS-857 - arms over the static chaining-adjudicator sweep.

WHAT IS BEING GRADED. ``tests/chained_exemption_guard.py`` derives every tracked
module that decides, at parse time, what a chained raise means - by reading the
``cause`` field CPython gives ``ast.Raise`` - and requires each one to be the
census, to defer to it, or to carry a recorded reason. These arms prove the
sweep fires, prove it stays silent on the three shapes that look similar and are
not the defect, and re-measure the one recorded reason rather than believing it.

EVERY POSITIVE HERE IS SYNTHETIC. ``memory/an-empty-population-satisfies-every-zero.md``
records why: a sweep that has only ever seen clean input is a sweep nobody has
proved fires, and a green run over an empty population satisfies every zero. The
plants are source STRINGS rather than files, so the sweep is exercised on input
that cannot drift when the tree does, and no arm here depends on a live finding
staying live.

THE DEFERRAL PATH IS NOW EXERCISED LIVE AS WELL AS SYNTHETICALLY, and this note
records the change rather than being overtaken by it. It read "synthetically
only" until CS-885 added ``tests/pathless_clone_guard.py``, which reads a Raise
node's cause to derive which same-module helper each chained site leans on, and
hands the question of what that cause MEANS to the census by importing it. The
arm that reddened on the change is preserved below as
``test_every_live_deferring_module_actually_defers``: it no longer asserts the
set is empty - that claim is simply false now - but it still holds the property
the empty assertion was standing in for, which is that a module in that set both
reads a cause AND imports the owner, and is therefore absent from the findings.

THE CENSUS ARMS THEMSELVES ARE STILL NOT IN THE POPULATION AT ALL. They read
``__cause__`` on live exceptions, which is measurement rather than adjudication,
and the separation between the two names is what keeps them out.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

from tests import chained_exemption_guard as guard
from tests.test_verify_env import rendered_exception_lines

MAX_ASCII_BYTE: Final = 0x7E

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

#: The same plant, handing the question to the census instead of answering it.
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


def test_a_planted_adjudicator_that_defers_to_the_census_is_not_flagged() -> None:
    """Handing the question to the owner is the sanctioned route out.

    The plant still reads a cause; only the import distinguishes it from the
    flagged plant above, so this arm isolates the deferral branch.
    """
    findings = _flagged(PLANTED_DEFERRING)

    assert not findings, "deferring to the census did not clear the plant"


# ---------------------------------------------------------------------------
# The three shapes that look similar and are not the defect
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


def test_the_three_negatives_differ_from_the_positive_only_where_intended() -> None:
    """The negatives are not silent for some accidental shared reason.

    Each negative is checked to parse and to be non-empty, so "not flagged"
    cannot be an artifact of an unparseable or trivial plant.
    """
    parsed = [
        len(ast.parse(source).body)
        for source in (PLANTED_RUNTIME_CHAIN, PLANTED_RAISE_ONLY, PLANTED_DEFERRING)
    ]

    assert min(parsed) > 0, "a negative plant is empty, so its silence proves nothing"


# ---------------------------------------------------------------------------
# The live tree
# ---------------------------------------------------------------------------


def test_the_tracked_tree_records_every_chaining_adjudicator() -> None:
    """No tracked module decides the chaining question with no reason on file."""
    sites = guard.adjudicators()
    offending = guard.unrecorded(sites)

    assert not offending, (
        "module(s) statically decide what a chained raise means without deferring to "
        f"{guard.OWNER} and without a recorded reason: {offending}"
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


def test_every_live_deferring_module_actually_defers() -> None:
    """The deferral branch, measured on whatever live modules take it.

    THIS ARM REPLACED AN ASSERTION THAT THE SET WAS EMPTY, and the replacement
    is deliberately not "assert it is non-empty" - that would redden the day the
    last deferring module is removed, which is a repair rather than a defect.
    What it holds instead is the property the empty assertion was standing in
    for: a module the guard treats as deferring must genuinely read a cause AND
    genuinely import the owner, and must therefore NOT be reported as an
    unrecorded adjudicator. An empty set passes that vacuously, so the count is
    reported rather than asserted, and the synthetic plants above remain the
    proof that the branch fires at all.
    """
    sources = guard.tracked_sources()
    trees = {module: ast.parse(source) for module, source in sources.items()}
    deferring = sorted(
        module
        for module, tree in trees.items()
        if guard.static_cause_reads(tree) and guard.defers_to_owner(tree)
    )
    reported = {finding.module for finding in guard.adjudicators()}
    leaked = sorted(module for module in deferring if module in reported)

    count = len(leaked)
    assert count == 0, f"{count} deferring module(s) were still reported as adjudicators: {leaked}"

    doubly = sorted(module for module in deferring if module in guard.EXEMPT)
    assert not doubly, (
        "a deferring module also carries an exemption entry; the entry records a reason "
        f"nothing needs and is free to rot: {doubly}"
    )
    assert guard.OWNER not in deferring, "the owner was counted as deferring to itself"


# ---------------------------------------------------------------------------
# The recorded reason is re-measured, never believed - ADR 0008
# ---------------------------------------------------------------------------


def test_the_recorded_scope_is_re_measured_rather_than_believed() -> None:
    """The one recorded reason claims a narrow scope; this measures it.

    The reason on record for tests/test_verify_env.py says its cause read
    exempts the ``from`` slot ALONE, because an object in the cause slot is not
    in the new message's args - and NOT that a chained cause goes unrendered.
    Those two claims are different and they are told apart by measurement here,
    not by reading the sentence:

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
