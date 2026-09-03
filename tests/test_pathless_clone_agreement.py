"""CS-885 - the arms over the four path-free clone copies.

WHAT IS BEING GRADED, and it is three separate propositions rather than one:

  (a) THE POPULATION IS DERIVED, and derived from something the defect cannot
      shrink. Section (a) plants the two evasions - a rename and a break - and
      asserts the member stays.
  (b) THE COPIES AGREE. Section (b) is the acceptance arm, plus the planted
      disagreements that prove it fires and the planted non-differences that
      prove it does not fire on them.
  (c) THE COPIES ARE STILL ACCEPTED BY THE CENSUS. Section (c) closes the
      silence measured under this item: a copy that drifts into an unsafe shape
      reports ``unproven`` and the census's own live arms SKIP over it.

NO ARM HERE SKIPS. The census skips when a clearance loses its live members, on
the stated grounds that an arm reddening when a site is repaired is
anti-correlated with success. That reasoning does not carry over: this module's
population is derived from CALL SITES, so it empties only when the tree stops
chaining through a helper at all - which is a topology change that must be
noticed, not tolerated. ``memory/a-skip-can-mute-the-defect.md`` is the class.
"""

from __future__ import annotations

import ast
import warnings
from typing import Final

import pytest

from tests.chained_cause_guard import (
    BUCKET_GRADED,
    CLOSED_PATHLESS,
    bucket_of,
    classify,
    raise_sites,
    sites_in_tree,
    tracked_sources,
)
from tests.pathless_clone_guard import (
    Copy,
    canonical_body,
    copies,
    copies_in_sources,
    disagreements,
    graded_sources,
    reliances,
    reliances_in_sources,
    unqualified,
)

#: The census's own planted-control module. Named here because an arm asserts
#: this module is EXCLUDED, which needs the name; nothing is graded from it.
CONTROL: Final = "tests/test_chained_cause.py"

#: How many modules the disagreement plants carry. Spelled once so the arms
#: compare against a name rather than a bare literal.
PLANTED_PAIR: Final = 2

# ---------------------------------------------------------------------------
# Planted material
# ---------------------------------------------------------------------------

#: One module carrying a helper and a site that chains through it. The body and
#: the helper name are parameters so an arm can plant a rename or a break
#: WITHOUT touching the call site, which is the whole point of the derivation.
MODULE = '''"""A planted module."""


class Wrapped(Exception):
    """The wrapper."""


def {name}({param}):
    """{doc}"""
    return {body}


def read(path):
    """Read it."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise Wrapped("failed") from {name}(exc)
'''

SAFE_BODY = "OSError({param}.errno, {param}.strerror)"


def _module(
    *,
    name: str = "_pathless_cause",
    param: str = "exc",
    body: str = SAFE_BODY,
    doc: str = "Clone it.",
) -> str:
    """Render one planted module.

    Args:
        name: The helper's name.
        param: Its parameter name.
        body: Its returned expression, with ``{param}`` interpolated.
        doc: Its docstring.

    Returns:
        The module source.
    """
    return MODULE.format(name=name, param=param, doc=doc, body=body.format(param=param))


# ---------------------------------------------------------------------------
# (a) The population, and the two evasions it must survive
# ---------------------------------------------------------------------------


def test_the_live_population_is_derived_and_not_empty() -> None:
    live = copies()
    count = len(live)
    assert count > 0, "the copy population is empty, so every arm below measured nothing"
    sites = len(reliances())
    assert sites >= count, f"{sites} relying sites cannot support {count} copies"


def test_renaming_the_helper_does_not_remove_it_from_the_population() -> None:
    """AN ADVERSARY MUST NOT ESCAPE BY RENAMING.

    ``memory/a-guard-can-measure-spelling.md``: a population derived from a
    spelling reports a clean zero about the wrong question. Membership here is
    the call site's shape, so the name is free to be anything.
    """
    plain = copies_in_sources({"a.py": _module()})
    renamed = copies_in_sources({"a.py": _module(name="zzz_unrelated")})
    assert len(plain) == 1, "the control module produced no member"
    found = len(renamed)
    assert found == 1, "renaming the helper removed it from the population"
    assert renamed[0].name == "zzz_unrelated"
    assert renamed[0].body == plain[0].body, "the rename changed the canonical body"


def test_breaking_the_helper_does_not_remove_it_from_the_population() -> None:
    """THE ANTI-CORRELATION ARM, and it is the one that decides the design.

    A population derived from the census's qualification walk would DROP a copy
    the moment that copy became unsafe, leaving the survivors in agreement and
    the arm green. Membership must therefore be blind to the body.
    """
    broken = _module(body="OSError({param}.errno, {param}.strerror, {param}.filename)")
    found = copies_in_sources({"a.py": broken})
    count = len(found)
    assert count == 1, "the broken copy fell out of the population"
    assert not found[0].qualifies, "the census still accepts a copy that carries filename"


def test_a_helper_reached_by_a_shape_the_census_cannot_clear_is_not_a_member() -> None:
    """THE TWO POPULATIONS MUST NOT DIVERGE.

    A member this module watches but the census cannot clear, or the reverse, is
    a copy whose drift one of the two would miss. The slot rules are mirrored,
    so an implicit chain - which the census deliberately never clears - is not a
    member here either.
    """
    implicit = MODULE.replace("from {name}(exc)", "").format(
        name="_pathless_cause", param="exc", doc="Clone it.", body=SAFE_BODY.format(param="exc")
    )
    found = copies_in_sources({"a.py": implicit})
    count = len(found)
    assert count == 0, "an implicit chain was counted as a reliance"


#: A helper NAMED in a slot but never CALLED there. The census clears a slot
#: only when it is a ``ast.Call``, so a bare name must not be a member here -
#: nothing was invoked, and the object that reaches the chain is the function
#: itself rather than anything it builds.
UNCALLED = '''"""A helper named in the slot rather than called in it."""


class Wrapped(Exception):
    """The wrapper."""


def _pathless_cause(exc):
    """Clone it."""
    return OSError(exc.errno, exc.strerror)


def suppressed(path):
    """Raise the function object itself."""
    try:
        return path.read_bytes()
    except OSError:
        raise _pathless_cause from None


def explicit(path):
    """Chain to the function object itself."""
    try:
        return path.read_bytes()
    except OSError:
        raise Wrapped("failed") from _pathless_cause
'''


def test_a_helper_named_in_a_slot_but_not_called_is_not_a_member() -> None:
    """THE SLOT MUST BE A CALL, IN BOTH FORMS.

    Accepting a bare name would widen this population past the one the census
    can clear, and a member the owner never rules on is a copy graded by only
    one of the two walks. Planted in both slots because they are selected by
    different branches and a single plant would leave one unmeasured.
    """
    found = copies_in_sources({"a.py": UNCALLED})
    count = len(found)
    assert count == 0, f"a helper that was named but never called became {count} member(s)"
    watched = len(reliances_in_sources({"a.py": UNCALLED}))
    assert watched == 0, f"{watched} uncalled slot(s) were counted as reliances"
    cleared = [
        site for site in sites_in_tree({"a.py": UNCALLED}) if classify(site) == CLOSED_PATHLESS
    ]
    census = len(cleared)
    assert census == 0, "the census cleared an uncalled slot, so the two walks now disagree"


# ---------------------------------------------------------------------------
# (b) Agreement
# ---------------------------------------------------------------------------


def test_a_planted_disagreement_between_two_copies_is_detected() -> None:
    """THE ACCEPTANCE, PLANTED. Two copies, two bodies, and it must go red."""
    sources = {
        "a.py": _module(),
        "b.py": _module(body="OSError({param}.errno, {param}.strerror, {param}.filename)"),
    }
    found = copies_in_sources(sources)
    reached = len(found)
    assert reached == PLANTED_PAIR, "the planted pair did not both reach the population"
    split = disagreements(found)
    count = len(split)
    assert count == PLANTED_PAIR, (
        f"a planted disagreement went undetected, {count} distinct bodies reported"
    )


def test_two_copies_that_agree_report_no_disagreement() -> None:
    sources = {"a.py": _module(), "b.py": _module()}
    split = disagreements(copies_in_sources(sources))
    count = len(split)
    assert count == 0, f"identical copies were reported as disagreeing, {count} bodies"


def test_a_differing_docstring_is_not_a_disagreement() -> None:
    """THE FOUR LIVE COPIES ALREADY DIFFER HERE, ON PURPOSE."""
    sources = {"a.py": _module(doc="One reason."), "b.py": _module(doc="A quite different one.")}
    split = disagreements(copies_in_sources(sources))
    count = len(split)
    assert count == 0, f"a docstring difference was graded as drift, {count} bodies"


def test_a_differing_parameter_name_is_not_a_disagreement() -> None:
    sources = {"a.py": _module(param="exc"), "b.py": _module(param="error")}
    split = disagreements(copies_in_sources(sources))
    count = len(split)
    assert count == 0, f"a parameter rename was graded as drift, {count} bodies"


def test_a_body_that_binds_the_canonical_token_still_compares_correctly() -> None:
    """THE NORMALISATION MUST NOT MANUFACTURE AN AGREEMENT.

    Canonicalising onto a fixed token would let a body that already binds that
    token reduce to the same text as a body that does not.
    """
    collided = canonical_body(_definition(_module(param="_p0")))
    plain = canonical_body(_definition(_module(param="exc")))
    assert collided == plain, "a parameter already spelled like the token broke the reduction"
    different = canonical_body(_definition(_module(param="_p0", body="OSError({param}.errno)")))
    assert different != plain, "two different bodies reduced to the same text"


def _definition(source: str) -> ast.FunctionDef:
    """The first module-level function in a planted module.

    Args:
        source: The module source.

    Returns:
        Its first ``def``.
    """
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name != "read":
            return node
    pytest.fail("the planted module carried no helper")


def test_the_live_copies_all_agree() -> None:
    """THE LIVE ARM. RED, not skipped, the moment any two stop agreeing."""
    live = copies()
    split = disagreements(live)
    count = len(split)
    keys = ", ".join(copy.key for copy in live)
    assert count == 0, f"{count} distinct bodies across {len(live)} copies: {keys}"


# ---------------------------------------------------------------------------
# (c) Still accepted by the census
# ---------------------------------------------------------------------------


def test_every_live_copy_still_qualifies_under_the_census() -> None:
    """THE SILENCE THIS ITEM MEASURED, CLOSED.

    A copy that drifts into an unsafe shape reports ``unproven`` - beside every
    shape nobody has looked at - and the census's live arms SKIP. This one does
    not.
    """
    failing = unqualified(copies())
    count = len(failing)
    assert count == 0, f"{count} relied-upon copies no longer build a path-free clone: {failing}"


def test_the_qualification_leg_reddens_on_a_broken_copy() -> None:
    broken = _module(body="OSError({param}.errno, str({param}))")
    failing = unqualified(copies_in_sources({"a.py": broken}))
    count = len(failing)
    assert count == 1, f"a copy rebuilding from str(exc) was not reported, {count} findings"


def test_the_population_covers_every_site_the_census_cleared() -> None:
    """NEITHER WALK MAY SEE A SITE THE OTHER DOES NOT.

    Scoped to the graded bucket on BOTH sides, because that is the scope this
    module's live population is derived over. Comparing a graded population
    against an unscoped one would redden on the census's own planted controls.
    """
    cleared = {
        (site.module, site.lineno)
        for site in raise_sites()
        if site.is_graded and classify(site) == CLOSED_PATHLESS
    }
    watched = {(site.module, site.lineno) for site in reliances()}
    missed = sorted(f"{module}:{line}" for module, line in cleared - watched)
    count = len(missed)
    assert count == 0, f"{count} cleared sites are outside this module's population: {missed}"
    covered = len(cleared)
    assert covered > 0, "the census cleared no graded site, so this arm compared nothing"


def test_the_scope_filter_drops_the_census_own_controls_and_nothing_else() -> None:
    """THE FILTER MUST DO EXACTLY ITS DOCUMENTED WORK.

    A scope filter is a place a real finding can be made to disappear, so this
    arm proves both directions: the control module IS dropped, it WOULD have
    contributed a member had it not been, and every module that survives is one
    the census itself grades.
    """
    everything = tracked_sources()
    graded = graded_sources()
    assert CONTROL in everything, "the control module is not tracked, so this arm proved nothing"
    assert CONTROL not in graded, "the census's own planted control reached the graded population"
    ungraded = sorted(name for name in graded if bucket_of(name) != BUCKET_GRADED)
    count = len(ungraded)
    assert count == 0, f"{count} modules survived the filter that the census does not grade"
    planted = copies_in_sources({CONTROL: everything[CONTROL]})
    contributed = len(planted)
    assert contributed > 0, "the control module contributes nothing, so the filter is untested"
    unsafe = len(unqualified(planted))
    assert unsafe > 0, "the control module's planted leak would not have been a finding"


def test_a_helper_shadowed_at_module_level_is_not_a_member() -> None:
    """FAIL CLOSED ON A NAME THIS MODULE CANNOT RESOLVE."""
    shadowed = _module() + "\n\n_pathless_cause = None\n"
    found = copies_in_sources({"a.py": shadowed})
    count = len(found)
    assert count == 0, "a helper rebound at module level was still resolved"


def test_a_helper_defined_twice_is_not_a_member() -> None:
    doubled = _module() + '\n\ndef _pathless_cause(exc):\n    """Later."""\n    return exc\n'
    found = copies_in_sources({"a.py": doubled})
    count = len(found)
    assert count == 0, "a name defined twice was resolved to one of its definitions"


def test_the_live_population_is_reported_so_a_reader_sees_its_members() -> None:
    """A COUNT NOBODY CAN READ THE MEMBERS OF IS A COUNT NOBODY CAN CHECK."""
    live = copies()
    body = "\n".join(f"  {copy.key} line {copy.lineno} qualifies={copy.qualifies}" for copy in live)
    warnings.warn(
        f"CS-885: {len(live)} path-free clone copies are relied on by "
        f"{len(reliances())} censused raise(s):\n{body}",
        stacklevel=1,
    )
    assert body, "the population rendered no report"


def test_the_reported_key_names_the_module_and_the_function() -> None:
    sample = Copy(module="a/b.py", name="_c", lineno=1, body="pass", qualifies=True)
    assert sample.key == "a/b.py::_c"


def test_no_reported_path_is_absolute() -> None:
    """A FINDING MUST NOT LEAK WHAT THIS TREE GRADES."""
    rooted = [copy.key for copy in copies() if copy.module.startswith("/") or ":" in copy.module]
    count = len(rooted)
    assert count == 0, f"{count} population members are named by an absolute path"


def test_a_module_that_does_not_parse_is_loud_rather_than_skipped() -> None:
    with pytest.raises(Exception, match="did not parse") as caught:
        reliances_in_sources({"a.py": "def broken(:\n"})
    named = "a.py" in str(caught.value)
    assert named, "the failure did not name the module it could not parse"
