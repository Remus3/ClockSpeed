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

from tests import pathless_clone_guard
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
    CARDINALS,
    DOCSTRING_PINS,
    ORDINALS,
    PRICING_COPY,
    Copy,
    canonical_body,
    copies,
    copies_in_sources,
    copy_docstrings,
    disagreements,
    docstring_digest,
    flatten,
    graded_sources,
    missing_cost_phrases,
    names_its_ordinal,
    promising_copies,
    reliances,
    reliances_in_sources,
    restated_counts,
    stale_excuses,
    unpinned_docstrings,
    unqualified,
)

#: The census's own planted-control module. Named here because an arm asserts
#: this module is EXCLUDED, which needs the name; nothing is graded from it.
CONTROL: Final = "tests/test_chained_cause.py"

#: How many modules the disagreement plants carry. Spelled once so the arms
#: compare against a name rather than a bare literal.
PLANTED_PAIR: Final = 2

#: The live copy count the CS-886 prose is written about. The pricing docstring
#: calls itself the FOURTH copy, so a tree that grows a fifth has invalidated
#: that sentence; section (d) reddens on the move rather than letting the prose
#: rot quietly beside a population that no longer matches it.
LIVE_COPIES: Final = 4

#: The promise CS-886 was filed against, planted verbatim so the sweep is
#: proven against the sentence that actually shipped rather than a paraphrase.
PROMISE: Final = "A single shared owner is the correct repair."

#: THE SAME PROMISE, OUTSIDE THE VOCABULARY. :data:`PROMISE` carries two of the
#: four ``OWNER_PHRASES`` spellings verbatim, so a control planted with it
#: proves the phrase leg fires on the shape it already models - which is
#: precisely the shape an evasion avoids
#: (``memory/a-guard-can-measure-spelling.md``). This says the same thing in
#: other words and contains not one of the four. It is what the pin is measured
#: against, and the phrase leg's blindness to it is asserted rather than
#: described, so the disclosure on ``OWNER_PHRASES`` cannot quietly stop being
#: true.
PARAPHRASE: Final = "A single shared implementation is the right fix."

#: The digit that ends ``filename2``, and therefore the count every text on
#: this channel falsely reddens on. NOT :data:`PLANTED_PAIR`, which happens to
#: hold the same number for an unrelated reason - reusing it would be the same
#: accidental equality the derived restated-count control exists to remove.
FIELD_SUFFIX: Final = 2

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


# ---------------------------------------------------------------------------
# (d) CS-886 - what the pricing copy's docstring is allowed to claim
# ---------------------------------------------------------------------------
#
# The fourth copy's docstring called a single shared owner "the correct repair"
# and excused itself with a slice write-list. CS-885 then measured that repair
# and DECLINED it, so the text recommended to a later reader something this
# project had already rejected, and said nothing about the price. These arms
# hold the replacement to the live census instead of to a number typed into it.
#
# THE "NO OTHER COPY PROMISES IT" VERDICT RESTS ON TWO LEGS, and only the
# second one is fail-safe. ``promising_copies`` reads a CLOSED vocabulary of
# four phrases, so it names what it finds but an open set of paraphrases walks
# past it - measured, on a live copy, below. ``unpinned_docstrings`` asks the
# closed question instead: is this the text that was read and signed off. A
# paraphrase changes the bytes, so the pin catches what the phrases cannot, and
# the pair is planted with one sentence each down the same path so that the gap
# between them is asserted rather than assumed.

#: The would-be shared owner, in a module of its own.
OWNER_MODULE = '''"""The owner the collapse would create."""


def _pathless_cause(exc):
    """Clone it."""
    return OSError(exc.errno, exc.strerror)
'''

#: The live shape, rewritten to import that owner by a bare name. Nothing else
#: about the site moves - same handler, same wrapper, same slot.
IMPORTED_OWNER = '''"""The same site, routed through the owner by a bare imported name."""

from owner import _pathless_cause


class Wrapped(Exception):
    """The wrapper."""


def read(path):
    """Read it."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise Wrapped("failed") from _pathless_cause(exc)
'''

#: The same again, reached on the owner module by a dotted name.
DOTTED_OWNER = '''"""The same site, routed through the owner by a dotted name."""

import owner


class Wrapped(Exception):
    """The wrapper."""


def read(path):
    """Read it."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise Wrapped("failed") from owner._pathless_cause(exc)
'''


def _verdicts(sources: dict[str, str]) -> tuple[str, ...]:
    """The census's verdict on every raise the planted ``a.py`` carries.

    Args:
        sources: The planted tree.

    Returns:
        One verdict per site, in the order the census reports them.
    """
    return tuple(classify(site) for site in sites_in_tree(sources) if site.module == "a.py")


def _pricing_docstring() -> str:
    """The live docstring of the copy that owns the collapse decision.

    Returns:
        Its text as written.
    """
    population = copies()
    priced = [copy for copy in population if copy.module == PRICING_COPY]
    assert len(priced) == 1, f"{len(priced)} copies live in {PRICING_COPY}, expected exactly one"
    text = copy_docstrings(population, graded_sources()).get(priced[0].key)
    assert text, f"{PRICING_COPY} carries no helper docstring, so nothing below was graded"
    return text


def _with_line(source: str, copy: Copy, line: str) -> str:
    """Plant one sentence inside one helper's docstring.

    The line goes INSIDE the existing string literal, immediately after its
    opening line, so the ``def`` keeps the line number the population was
    derived at and nothing but the docstring changes.

    TAKES THE SENTENCE RATHER THAN SPELLING IT, so :data:`PROMISE` and
    :data:`PARAPHRASE` reach the detectors down the identical path. A separate
    planter per sentence is a place the two controls could differ by accident,
    and the whole point of the pair is that only the SENTENCE differs.

    Args:
        source: The module source.
        copy: The copy whose docstring is the target.
        line: The sentence to plant.

    Returns:
        The mutated source.
    """
    node = next(
        item
        for item in ast.parse(source).body
        if isinstance(item, ast.FunctionDef) and item.name == copy.name
    )
    doc = node.body[0]
    assert isinstance(doc, ast.Expr), "the target helper carries no docstring to plant into"
    lines = source.splitlines(keepends=True)
    return "".join([*lines[: doc.lineno], f"    {line}\n", *lines[doc.lineno :]])


def test_routing_a_site_through_a_shared_owner_loses_its_clearance() -> None:
    """THE COST, DERIVED BY EXECUTION RATHER THAN RESTATED.

    The docstring's claim is a claim about the census, so this measures the
    census. One site, three spellings of the same helper: defined beside it,
    imported from an owner module by a bare name, and reached on that module by
    a dotted one. BOTH DIRECTIONS ARE ASSERTED - a plant that could not be
    cleared even when written the live way would prove nothing at all about
    what the collapse costs, only that the plant was malformed.
    """
    kept = _verdicts({"a.py": _module()})
    assert kept == (CLOSED_PATHLESS,), f"the same-module control was not cleared, got {kept}"
    imported = _verdicts({"a.py": IMPORTED_OWNER, "owner.py": OWNER_MODULE})
    assert len(imported) == 1, f"the bare-import plant censused {len(imported)} sites, wanted one"
    assert CLOSED_PATHLESS not in imported, f"a bare imported owner kept the clearance: {imported}"
    dotted = _verdicts({"a.py": DOTTED_OWNER, "owner.py": OWNER_MODULE})
    assert len(dotted) == 1, f"the dotted plant censused {len(dotted)} sites, wanted one"
    assert CLOSED_PATHLESS not in dotted, f"a dotted owner kept the clearance: {dotted}"


def test_every_live_site_would_take_that_drop_at_once() -> None:
    """WHY THE COST IS AGGREGATE, AND THE NON-EMPTINESS THAT MAKES IT ONE.

    ``Reliance`` membership IS "a bare-name call to a module-level function of
    the same module" - the one shape the arm above proves the collapse
    destroys. So the population is exactly the set of sites the repair would
    drop, and "they all drop at once" is a statement about its size. It says
    nothing whatever if the set is empty
    (``memory/an-empty-population-satisfies-every-zero.md``), so the size is
    asserted here and never written into the prose.
    """
    sites = len(reliances())
    assert sites > 0, "no live site leans on a same-module helper, so the collapse prices nothing"
    carriers = {reliance.module for reliance in reliances()}
    modules = {copy.module for copy in copies()}
    assert carriers <= modules, f"a reliance names a module no copy lives in: {carriers - modules}"


def test_the_pricing_copy_states_what_the_shared_owner_would_cost() -> None:
    """THE ACCEPTANCE - THE CLAIM MUST PRICE THE REPAIR IT ONCE RECOMMENDED.

    It has to name the item that measured it, the verdict, what the sites drop
    to, and the shape of the aggregate. THE MAGNITUDE MAY NOT APPEAR: the only
    number the prose carries is the ordinal saying WHICH copy it is, and that
    word is held to ``len(copies())`` computed here rather than compared to a
    literal beside it.
    """
    total = len(copies())
    assert total == LIVE_COPIES, f"{total} copies now, so the docstring's ordinal is stale"
    sites = len(reliances())
    assert sites > 0, "the census reports no relying site, so the claim prices nothing"
    text = _pricing_docstring()
    absent = missing_cost_phrases(text)
    assert not absent, f"the docstring stopped stating the cost, missing {absent}"
    assert names_its_ordinal(text, total), f"the docstring does not call itself the {total}th copy"
    restated = restated_counts(text, sites)
    assert not restated, f"the docstring writes the live measurement down as {restated}"


def test_the_pricing_copy_defers_to_no_slice_write_list() -> None:
    """THE SECOND HALF OF THE DEFECT.

    "Creating one was not on this slice's write-list" is true for one dispatch
    and unreadable forever after: a later reader cannot see that slice, cannot
    check it, and cannot tell whether the work was declined or merely deferred.
    """
    found = stale_excuses(_pricing_docstring())
    assert not found, f"the docstring defers to a dispatch a reader cannot see: {found}"


def test_no_other_copy_promises_that_a_shared_owner_is_correct() -> None:
    """ONE DOCSTRING OWNS THE DECISION, AND IT IS THE ONE CARRYING THE PRICE.

    A second copy naming the collapse - to recommend it, or even to argue about
    it - hands a reader a live-looking question CS-885 already closed, with no
    reason to believe the price travelled with it.
    """
    population = copies()
    total = len(population)
    assert total == LIVE_COPIES, f"the copy population moved to {total}, so this sweep is stale"
    docstrings = copy_docstrings(population, graded_sources())
    read = len(docstrings)
    assert read == total, f"{total - read} copies carry no docstring, so the sweep skipped them"
    exempt = [key for key in docstrings if key.startswith(f"{PRICING_COPY}::")]
    assert len(exempt) == 1, f"{len(exempt)} copies claim the pricing exemption, wanted one"
    promising = promising_copies(population, graded_sources())
    count = len(promising)
    assert count == 0, f"{count} copies outside {PRICING_COPY} name the collapse: {promising}"


def test_the_sweep_reddens_on_a_promise_planted_in_a_live_copy() -> None:
    """THE MUTATION. A GREEN SWEEP OVER A CLEAN TREE PROVES NOTHING ALONE.

    Planted into a fabricated copy of a LIVE module's source, so the whole path
    the acceptance arm walks is exercised - population, re-parse, docstring lift
    and predicate - rather than the predicate on its own.
    """
    population = copies()
    victim = next(copy for copy in population if copy.module != PRICING_COPY)
    sources = dict(graded_sources())
    clean = promising_copies(population, sources)
    assert not clean, f"the tree already carries the promise, so the plant proves nothing: {clean}"
    sources[victim.module] = _with_line(sources[victim.module], victim, PROMISE)
    caught = promising_copies(population, sources)
    assert caught == (victim.key,), f"the planted promise went unreported, got {caught}"


def test_the_pricing_exemption_is_scoped_to_one_module() -> None:
    """AN EXEMPTION IS A PLACE A FINDING DISAPPEARS, SO BOTH DIRECTIONS ARE PROVEN.

    Two fabricated modules carrying the identical promise, one of them named
    like the pricing copy. Only the other may be reported, and the pair has to
    reach the population first or the arm compared nothing.
    """
    promised = _module(doc=PROMISE)
    sources = {PRICING_COPY: promised, "b.py": promised}
    population = copies_in_sources(sources)
    reached = len(population)
    assert reached == PLANTED_PAIR, f"{reached} of the planted pair reached the population"
    found = promising_copies(population, sources)
    assert found == ("b.py::_pathless_cause",), f"the exemption is not module-scoped: {found}"


def test_every_copy_outside_the_pricing_one_carries_the_docstring_it_was_read_with() -> None:
    """FINDING 1 - THE ACCEPTANCE, AND IT IS POSITIVE AND CLOSED.

    ``test_no_other_copy_promises_that_a_shared_owner_is_correct`` issues a
    verdict over an OPEN set: it reads four phrases and clears every other form
    of words, so its green says "none of four spellings" while reading as "no
    copy promises the collapse". This arm asks the closed question instead -
    is each of these docstrings the text that was read and signed off - and
    refuses everything else.

    THE TABLE MUST COVER EXACTLY THE POPULATION, asserted in both directions. A
    pin for a module no copy lives in is a reading of something that is no
    longer there, and a copy no pin covers is the fail-open case coming back.
    """
    population = copies()
    findings = unpinned_docstrings(population, graded_sources())
    assert not findings, (
        f"{len(findings)} copies do not carry the docstring they were read with: {findings}. "
        f"Re-read each, confirm it does not name the collapse, then update DOCSTRING_PINS."
    )
    graded = {copy.module for copy in population if copy.module != PRICING_COPY}
    assert graded, "no copy outside the pricing one, so the pin table graded nothing"
    assert set(DOCSTRING_PINS) == graded, (
        f"the pin table and the population disagree: "
        f"unpinned {sorted(graded - set(DOCSTRING_PINS))}, "
        f"orphaned {sorted(set(DOCSTRING_PINS) - graded)}"
    )
    assert PRICING_COPY not in DOCSTRING_PINS, (
        "the pricing copy is pinned, so its price cannot move"
    )


def test_the_pin_reddens_on_a_paraphrase_the_phrase_sweep_cannot_see() -> None:
    """FINDING 1 - THE MUTATION, AND THE TWO LEGS MEASURED AGAINST EACH OTHER.

    ONE PLANT, BOTH DETECTORS. :data:`PARAPHRASE` says what :data:`PROMISE`
    says and contains none of the four ``OWNER_PHRASES`` spellings. The phrase
    leg is asserted SILENT on it - that is the disclosure on ``OWNER_PHRASES``
    proven by execution rather than described, so it cannot quietly stop being
    true - and the pin is asserted to report exactly the copy it was planted
    in.

    Both plants go through :func:`_with_line` into a fabricated copy of a LIVE
    module's source, so the whole path is exercised and the only difference
    between the two controls is the sentence.
    """
    population = copies()
    victim = next(copy for copy in population if copy.module != PRICING_COPY)
    sources = dict(graded_sources())
    assert not unpinned_docstrings(population, sources), "the tree is already off its pins"
    sources[victim.module] = _with_line(sources[victim.module], victim, PARAPHRASE)
    blind = promising_copies(population, sources)
    assert blind == (), (
        f"the phrase leg reported {blind} on a paraphrase outside its vocabulary, so this "
        f"control no longer measures the gap the pin exists to cover - pick another paraphrase"
    )
    caught = unpinned_docstrings(population, sources)
    assert len(caught) == 1, f"the planted paraphrase moved {len(caught)} pins, wanted one"
    assert caught[0].startswith(f"{victim.key} "), f"the pin blamed the wrong copy: {caught}"


def test_the_pin_refuses_a_copy_it_has_no_reading_for() -> None:
    """A PIN THAT SILENTLY PASSES WHAT IT CANNOT READ IS THE DEFECT AGAIN.

    Three refusals, each of which would otherwise be a way past the verdict: a
    module the table has never seen, a copy carrying no docstring at all, and
    the pricing copy - which must go on being exempt, or the arm above is just
    a slower way of pinning everything.
    """
    unknown = copies_in_sources({"b.py": _module()})
    assert len(unknown) == 1, "the fabricated module produced no member"
    findings = unpinned_docstrings(unknown, {"b.py": _module()})
    assert len(findings) == 1, f"an unpinned module was cleared: {findings}"
    assert "unpinned" in findings[0], f"the finding does not say it was never read: {findings}"
    bare = _module().replace('    """Clone it."""\n', "")
    silent = copies_in_sources({"b.py": bare})
    assert len(silent) == 1, "the docstring-free helper fell out of the population"
    missing = unpinned_docstrings(silent, {"b.py": bare})
    assert len(missing) == 1, f"a copy with no docstring was cleared: {missing}"
    assert "no docstring" in missing[0], f"the finding does not name the cause: {missing}"
    exempt = copies_in_sources({PRICING_COPY: _module()})
    assert unpinned_docstrings(exempt, {PRICING_COPY: _module()}) == ()


def test_the_pin_is_taken_over_the_words_and_not_the_line_wrapping() -> None:
    """THE ONE EDIT THE PIN DELIBERATELY DOES NOT REDDEN ON.

    A pin sensitive to re-wrapping would be re-pinned unread often enough to
    stop being read at all, which is how a fail-safe control decays back into
    a fail-open one. Every WORD still moves it.
    """
    wrapped = "A single shared\n    owner is the CORRECT\n    repair"
    assert docstring_digest(wrapped) == docstring_digest(PROMISE.rstrip("."))
    assert docstring_digest(PROMISE) != docstring_digest(PARAPHRASE)


def test_the_restated_count_leg_fires_on_a_digit_and_on_a_word() -> None:
    """THE LEG THAT KEEPS THE MAGNITUDE OUT OF THE PROSE, AND ITS FALSE-RED CONTROL.

    THE COUNT IS THE LIVE ONE, DERIVED. This control used to spell it as a
    literal in all four cases, which equalled the live count only by accident:
    it proved the leg works at a number the tree happens to sit on today and
    would have kept passing unchanged while the tree walked away from it. The
    two acceptance arms call this predicate with ``len(reliances())``, so that
    is the count it has to be proven at.

    The last case is the one that matters: item ids on this channel carry an
    eight, and a leg that graded ``CS-885`` as a restatement of eight would be
    unusable on the very docstring it exists for. It holds at any single-digit
    count - both ids spell theirs with a digit on at least one side.
    """
    live = len(reliances())
    assert 0 < live < len(CARDINALS), (
        f"{live} relying sites is outside what this control can spell, so it graded nothing"
    )
    word = CARDINALS[live]
    assert restated_counts(f"all {live} sites drop at once", live) == (str(live),)
    assert restated_counts(f"all {word} sites drop at once", live) == (word,)
    assert restated_counts(f"{live} sites, {word} of them", live) == (str(live), word)
    assert restated_counts("CS-885 priced it and CS-857 measured it", live) == ()


def test_the_restated_count_leg_refuses_a_count_its_vocabulary_cannot_spell() -> None:
    """FINDING 3 - THE SILENT DEGRADATION, CLOSED.

    The word leg was gated on the same bound the table has, so past the end of
    :data:`CARDINALS` it simply did not run: the arm dropped from two legs to
    one and nothing said so, leaving ``assert not restated`` satisfied by a
    docstring that spelled the number in words. The live relying-site count is
    what gets passed in, so the tree only had to grow to reach it.

    BOTH SIDES OF THE EDGE ARE ASSERTED. A refusal that also fired one short of
    the bound would be a different bug wearing the same green.
    """
    edge = len(CARDINALS)
    with pytest.raises(ValueError, match="cannot spell"):
        restated_counts("all eleven sites drop at once", edge)
    with pytest.raises(ValueError, match="cannot spell"):
        restated_counts("a negative population is not a count", -1)
    inside = restated_counts(f"all {CARDINALS[edge - 1]} sites drop at once", edge - 1)
    assert inside == (CARDINALS[edge - 1],), (
        f"the leg stopped working inside its own table: {inside}"
    )


def test_the_restated_count_leg_discloses_the_counts_it_falsely_reddens_on() -> None:
    """FINDING 2 - THE UNDISCLOSED FALSE-RED BOUNDARY, MEASURED AND REPORTED.

    The disclosure named the count-of-one collision and stopped, which read as
    though it were the only one. It is not. This arm MEASURES the whole set
    over both texts the predicate is actually pointed at, warns it so a reader
    meets the current boundary rather than a sentence about it, and pins the
    two mechanisms that make the set permanent rather than incidental:

      * ``filename2`` puts a digit beside a LETTER, and the digit leg is
        bounded only against digits. Both live texts name that attribute -
        they exist because of it - so a count of two is a false red on this
        channel for as long as the channel is about what it is about.
      * The set is not written into any docstring. It is a measurement of the
        prose, and CLAUDE.md section 4 is why this arm reports it instead.

    A SET THAT CAME BACK EMPTY WOULD MEAN THE MEASUREMENT BROKE, not that the
    prose got clean, so non-emptiness is asserted rather than assumed
    (``memory/an-empty-population-satisfies-every-zero.md``).
    """
    texts = {
        "tests/pathless_clone_guard.py module": pathless_clone_guard.__doc__ or "",
        f"{PRICING_COPY} helper": _pricing_docstring(),
    }
    live = len(reliances())
    report: list[str] = []
    for label, text in texts.items():
        assert text, f"{label} carried no text, so this arm measured nothing"
        falsely = tuple(n for n in range(len(CARDINALS)) if restated_counts(text, n))
        report.append(f"  {label}: {falsely}")
        assert falsely, f"{label} reddens on no count at all, so the measurement broke"
        assert FIELD_SUFFIX in falsely, f"{label} does not name filename2, so it moved"
        assert live not in falsely, (
            f"{label} falsely reddens on the live count {live}, which is what the two "
            f"acceptance arms pass in - they are now measuring a collision, not a restatement"
        )
    warnings.warn(
        "CS-886: restated_counts falsely reddens on these counts, measured this run:\n"
        + "\n".join(report),
        stacklevel=1,
    )
    disclosure = flatten(restated_counts.__doc__ or "")
    assert "filename2" in disclosure, "the disclosure does not name the letter-adjacent digit"
    assert "hyphenated" in disclosure, "the disclosure does not name the hyphenated cardinal"


def test_the_guard_module_states_the_shape_without_restating_its_size() -> None:
    """THE SAME RULE, APPLIED TO THE MODULE THAT OWNS THE MEASUREMENT.

    ``tests/pathless_clone_guard.py`` argues the declined collapse in its own
    header, and until CS-886 that header spelled the population size as a word.
    A measured number written into prose is a lie with a timestamp on it
    wherever it appears, and the guard against that drift is the last place it
    should have been true of.
    """
    text = pathless_clone_guard.__doc__
    assert text, "the guard module carries no docstring, so this arm read nothing"
    sites = len(reliances())
    assert sites > 0, "the census reports no relying site, so there was no size to restate"
    restated = restated_counts(text, sites)
    assert not restated, f"the guard module writes the live measurement down as {restated}"
    assert "drop at once" in flatten(text), "the guard module stopped stating the shape"


def test_the_ordinal_leg_is_not_satisfied_by_the_shared_winerror_sentence() -> None:
    """MEASURED, NOT ASSUMED.

    All four live copies share a sentence about supplying ``winerror`` as "a
    fourth argument". A bare-ordinal test passes on every one of them, so it
    would have kept passing after the sentence it exists to hold was deleted.
    """
    assert not names_its_ordinal("supplying winerror as a fourth argument", LIVE_COPIES)
    assert names_its_ordinal("the fourth copy is a priced duplicate", LIVE_COPIES)
    assert not names_its_ordinal("the fourth copy", LIVE_COPIES + 1)
    assert not names_its_ordinal("the fourth copy", len(ORDINALS))


def test_a_copy_naming_a_module_the_sources_do_not_carry_is_loud() -> None:
    """FAIL CLOSED WHEN THE SWEEP CANNOT READ WHAT IT IS GRADING."""
    absent = Copy(module="nowhere.py", name="_c", lineno=1, body="pass", qualifies=True)
    with pytest.raises(Exception, match="not among the sources") as caught:
        copy_docstrings([absent], {})
    assert "nowhere.py" in str(caught.value), "the failure did not name the module it wanted"


def test_flatten_matches_a_phrase_a_line_wrap_split() -> None:
    """A WRAPPED PHRASE IS THE SAME PHRASE."""
    wrapped = "a single shared\n    owner is the CORRECT\n    repair"
    assert "shared owner" in flatten(wrapped)
    assert "correct repair" in flatten(wrapped)
