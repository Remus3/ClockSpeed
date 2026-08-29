"""CS-857 - the arms over ``tests/chained_cause_guard.py``.

THE MEASUREMENTS COME FIRST AND EVERYTHING ELSE RESTS ON THEM. The guard's
verdicts are claims about what CPython renders, so this module renders each
shape with a SYNTHETIC MARKER and reads the result, rather than reasoning about
the interpreter from memory. ``from None`` is the only shape measured NOT to
render, and it is the only positive clearance the guard issues.

THREE RULES THIS MODULE IS BUILT TO OBEY.

  AN EMPTY POPULATION SATISFIES EVERY ZERO. The tracked tree contains ZERO
  implicit-context sites and ZERO ``__notes__`` sites, so both zeroes mean
  nothing on their own: the detector being broken produces the same output. The
  implicit detector is proven twice - on a planted synthetic module and on this
  module's OWN fixtures found through the live git sweep - and the note census
  is proven the same way. Every counts-only arm also asserts its denominator.

  A PROOF CAN REQUIRE THE DEFECT IT CERTIFIES AGAINST. Every behavioural arm
  runs :func:`chained_cause_guard.sites_in_tree` over a PLANTED source, never
  over the live findings, so repairing a live site cannot redden an arm. The
  live-tree arms assert the DENOMINATOR and the totality of the verdict, never
  a particular finding.

  A POOLED GUARD HIDES ITS WORST MEMBER. Every planted shape and every live
  graded site is parametrized onto its OWN arm. A single arm over the pooled
  population would be satisfied by its strongest member.

WHAT THIS MODULE DELIBERATELY PUTS INTO THE LIVE SWEEP. The rendering fixtures
below are real ``raise`` statements, so the guard derives sites for this file
and grades some of them ``measured-leak``. That is correct and it is the point:
they are the live positive control proving the detector fires on the git sweep
and not only on a string. Their only payload is :data:`MARKER`, an authored
constant that is not a path and not personal data.
"""

from __future__ import annotations

import json
import re
import traceback
import warnings
from pathlib import Path
from typing import Final

import pytest

from tests import chained_cause_guard
from tests.assertion_rendering_guard import REPO_ROOT
from tests.chained_cause_guard import (
    ACTIVE_CAUSE,
    BARE_RAISE,
    CLOSED_SUPPRESSED,
    EXEMPT,
    EXEMPT_RECORDED,
    FORM_BARE,
    FORM_EXPLICIT,
    FORM_IMPLICIT,
    FORM_SUPPRESSED,
    FORMS,
    GRADED_LAYER,
    IMPLICIT_CAUSE,
    MEASURED_LEAK,
    NO_CAUSE,
    NOTE_ATTRIBUTE,
    NOTE_CALL,
    TYPE_OSERROR,
    TYPE_RESOLVED_OTHER,
    TYPE_UNRESOLVED,
    UNPROVEN,
    VERDICT_ORDER,
    ChainedCauseDerivationError,
    Site,
    classify,
    frozen_from_text,
    frozen_paths,
    is_frozen,
    note_sites,
    notes_in_tree,
    out_of_scope_record,
    raise_sites,
    sites_in_tree,
    stale_exemptions,
    tracked_sources,
)

# ---------------------------------------------------------------------------
# The synthetic payload. NOT a path, NOT personal data, NOT derived from any
# machine's configuration - CLAUDE.md non-negotiables 3 and 11.
# ---------------------------------------------------------------------------

#: The only value the rendering fixtures ever carry.
MARKER: Final = "CS857-SYNTHETIC-MARKER"

#: Stand-ins for what a real site would build. Named so no bare number or bare
#: string sits in an assertion.
_ERRNO: Final = 13
_STRERROR: Final = "Permission denied"
_REDACTED: Final = "<redacted>"

#: This module, as the live git sweep names it.
_THIS_MODULE: Final = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

#: The two guard files CS-857 slice S2 owns, checked for transcribed sites.
_OWNED_FILES: Final = ("tests/chained_cause_guard.py", _THIS_MODULE)

#: A module path followed by a colon and a line number. Invariant 1 forbids a
#: transcribed site list, and a transcribed LINE is also a dead citation the
#: moment the tree grows - the CS-857 note's own cited lines had drifted by
#: eighteen before this slice started.
#:
#: THE PATTERN IS DELIBERATELY NOT SPELLED OUT IN PROSE ANYWHERE ABOVE. Writing
#: an EXAMPLE of the forbidden form here made this arm fail against its own
#: comment on the first run, which is the arm working. The pattern still does
#: not match its own source: the regex text carries a literal backslash then
#: the letter d, and a letter is not a digit.
_TRANSCRIBED_SITE: Final = re.compile(r"\.py:\d+")

#: The planted module's path. Deliberately outside :data:`GRADED_LAYER`, so a
#: planted arm can never be confused with a live finding.
PLANTED_PATH: Final = "synthetic/planted_chains.py"


# ---------------------------------------------------------------------------
# The rendering fixtures. REAL raises, so the live sweep sees them.
# ---------------------------------------------------------------------------


class _SyntheticError(Exception):
    """The wrapper raised by this module's fixtures and by nothing else."""


def _chain_of(failure: BaseException) -> tuple[BaseException, ...]:
    """Every exception the interpreter would render, in the order it renders.

    THE THREE ATTRIBUTES THE FORMATTER ITSELF CONSULTS, and no others:
    ``__cause__`` wins; failing that ``__context__`` is followed unless
    ``__suppress_context__`` is set, which is what ``from None`` sets. The
    identity set stops a self-referential chain from looping.

    Args:
        failure: The exception that reached the caller.

    Returns:
        The chain, the failure itself first.
    """
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = failure
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        if current.__cause__ is not None:
            current = current.__cause__
        elif current.__suppress_context__:
            current = None
        else:
            current = current.__context__
    return tuple(chain)


def _rendered_chain(failure: BaseException) -> str:
    """The exception lines the interpreter would print, WITHOUT the frames.

    WHY THE FRAMES ARE NOT RENDERED, and it is not to dodge a guard.
    ``traceback.format_exc`` and ``format_exception`` emit an absolute path per
    frame, which is an echo path under ``CLAUDE.md`` non-negotiable 12 - and
    this module would then embed one in every failure message. ``tests/
    test_exception_rendering.py`` holds exactly that rule and records the
    files allowed to render a full traceback; this module does not need to be
    one of them, because the frames were never the subject. The subject is
    which EXCEPTIONS get rendered and what their text says, and
    ``format_exception_only`` answers that with no frame at all.

    MEASURED EQUIVALENT ON ALL SIX SHAPES. For explicit, suppressed, implicit,
    bare, aliased and noted, this string and a full ``format_exception`` agree
    on whether the marker is present; the full one additionally carried an
    absolute path and this one did not.

    WHAT IS THEREFORE NOT MEASURED HERE: the formatter's own connector lines -
    "The above exception was the direct cause" and "During handling of the
    above exception" - and the frame rendering. ``tests/save/test_world.py``
    is the recorded residual that renders the complete surface for the save
    layer, so the end-to-end claim is not unowned.

    Args:
        failure: The exception that reached the caller.

    Returns:
        The concatenated exception-only lines for the whole chain.
    """
    return "".join(
        line
        for link in _chain_of(failure)
        for line in traceback.format_exception_only(type(link), link)
    )


def _explicit_chain() -> None:
    """Raise a wrapper with an explicit cause carrying the marker."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError as exc:
        raise _SyntheticError(_REDACTED) from exc


def _suppressed_chain() -> None:
    """Raise a wrapper with the context suppressed."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        raise _SyntheticError(_REDACTED) from None


def _implicit_chain() -> None:
    """Raise a wrapper inside a handler with no ``from`` clause at all."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        # B904 SUPPRESSED WITH A REASON, NOT AS TIDINESS. B904 asks for a
        # `from` clause, and the ABSENCE of one is the entire subject of this
        # fixture: it is the adversary's two-word deletion, and the arm it
        # feeds measures that the value still renders through __context__.
        # Satisfying the rule here would delete the shape under test.
        raise _SyntheticError(_REDACTED)  # noqa: B904


def _bare_reraise() -> None:
    """Re-raise the handler's own exception."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        raise


def _aliased_chain() -> None:
    """Chain from a name the handler does not bind."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError as exc:
        kept = exc
        raise _SyntheticError(_REDACTED) from kept


def _noted_failure() -> None:
    """Attach the marker as a note, reaching no cause at all."""
    failure = _SyntheticError(_REDACTED)
    failure.add_note(MARKER)
    raise failure


# ---------------------------------------------------------------------------
# THE MEASUREMENTS. Each raises one shape and reads what would be rendered.
#
# EVERY ARM ASSERTS THE CHAIN LENGTH AS WELL AS THE TEXT. A substring check
# alone passes when the chain is walked wrongly but the marker turns up anyway,
# and it cannot tell a two-link chain from a one-link chain whose single link
# happens to carry the marker. The length is what separates them.
# ---------------------------------------------------------------------------

#: A wrapper plus its cause.
_CHAINED = 2

#: One exception, no chain rendered.
_UNCHAINED = 1


def test_an_explicit_chain_renders_the_cause() -> None:
    """``from exc`` puts the cause's own text in what gets rendered."""
    with pytest.raises(_SyntheticError) as caught:
        _explicit_chain()
    chain = _chain_of(caught.value)
    rendered = _rendered_chain(caught.value)
    assert len(chain) == _CHAINED, f"the cause was not chained at all: {len(chain)} link(s)"
    assert isinstance(chain[1], OSError), "the second link is not the caught OSError"
    assert MARKER in rendered, (
        "an explicit chain did not render its cause, which would make the "
        f"whole guard about nothing: {rendered!r}"
    )
    assert _REDACTED in rendered, "the wrapper's own message should render too"


def test_from_none_does_not_render_the_suppressed_context() -> None:
    """THE ONE POSITIVE CLEARANCE, measured rather than assumed.

    ``closed-suppressed`` is the only verdict this guard issues that says a
    site is safe, and it rests entirely on these three lines. The context is
    asserted to still BE there and to still be suppressed, so the arm cannot
    pass merely because nothing was caught in the first place.
    """
    with pytest.raises(_SyntheticError) as caught:
        _suppressed_chain()
    failure = caught.value
    assert failure.__context__ is not None, "nothing was in flight, so nothing was suppressed"
    assert failure.__suppress_context__, "from None did not set __suppress_context__"
    chain = _chain_of(failure)
    rendered = _rendered_chain(failure)
    assert len(chain) == _UNCHAINED, f"the suppressed context was still walked: {len(chain)}"
    assert MARKER not in rendered, (
        "from None rendered the suppressed context, so CLOSED_SUPPRESSED is "
        f"not a clearance and the guard must be rewritten: {rendered!r}"
    )
    assert _REDACTED in rendered, "the wrapper itself must still render"


def test_an_implicit_context_renders_the_cause() -> None:
    """DELETING ``from exc`` DOES NOT CLOSE THE CHANNEL.

    This is the measurement that makes a ``.cause``-only population a
    syntax-token count rather than a population.
    """
    with pytest.raises(_SyntheticError) as caught:
        _implicit_chain()
    failure = caught.value
    assert failure.__cause__ is None, "the fixture set a cause, so it is not the implicit shape"
    chain = _chain_of(failure)
    rendered = _rendered_chain(failure)
    assert len(chain) == _CHAINED, f"__context__ was not walked: {len(chain)} link(s)"
    assert MARKER in rendered, f"an implicit __context__ did not render its cause: {rendered!r}"


def test_a_bare_reraise_renders_the_original() -> None:
    """A bare ``raise`` propagates the handler's exception, text and all."""
    with pytest.raises(OSError, match=MARKER) as caught:
        _bare_reraise()
    rendered = _rendered_chain(caught.value)
    assert len(_chain_of(caught.value)) == _UNCHAINED, "a bare re-raise built a chain"
    assert MARKER in rendered, f"a bare re-raise did not render: {rendered!r}"


def test_an_aliased_cause_still_renders() -> None:
    """Moving the value to another name changes nothing about the render.

    The adversary's edit from the guard's own escape table, measured.
    """
    with pytest.raises(_SyntheticError) as caught:
        _aliased_chain()
    chain = _chain_of(caught.value)
    rendered = _rendered_chain(caught.value)
    assert len(chain) == _CHAINED, f"the aliased cause was not chained: {len(chain)} link(s)"
    assert MARKER in rendered, f"an aliased cause did not render: {rendered!r}"


def test_an_added_note_renders() -> None:
    """``add_note`` reaches the rendered text while reaching no cause at all."""
    with pytest.raises(_SyntheticError) as caught:
        _noted_failure()
    failure = caught.value
    rendered = _rendered_chain(failure)
    assert failure.__cause__ is None, "the note fixture also set a cause"
    assert len(_chain_of(failure)) == _UNCHAINED, "the note fixture built a chain"
    assert MARKER in rendered, (
        f"an added note did not render, so the __notes__ census grades a "
        f"channel that discloses nothing: {rendered!r}"
    )


def _linked(
    cause: BaseException | None, context: BaseException | None, suppress: bool
) -> Exception:
    """Build a wrapper with the chain attributes set exactly as named.

    Args:
        cause: What ``__cause__`` is set to.
        context: What ``__context__`` is set to.
        suppress: What ``__suppress_context__`` is set to.

    Returns:
        The wrapper.
    """
    wrapper = _SyntheticError(_REDACTED)
    wrapper.__cause__ = cause
    wrapper.__context__ = context
    wrapper.__suppress_context__ = suppress
    return wrapper


_INNER: Final = ValueError("inner")
_OTHER: Final = ValueError("other")

#: THE WALK IS NOW LOAD-BEARING, so its rule is graded directly rather than
#: only through the six fixtures. Every combination of the three attributes the
#: formatter consults, one row each.
_CHAIN_RULES: Final = [
    ("cause-only", _INNER, None, False, 2),
    ("context-only", None, _INNER, False, 2),
    ("context-suppressed", None, _INNER, True, 1),
    ("cause-wins-over-context", _INNER, _OTHER, False, 2),
    ("cause-survives-suppression", _INNER, _OTHER, True, 2),
    ("nothing-at-all", None, None, False, 1),
]


@pytest.mark.parametrize(
    ("label", "cause", "context", "suppress", "length"),
    _CHAIN_RULES,
    ids=[row[0] for row in _CHAIN_RULES],
)
def test_the_chain_walk_follows_the_attributes_the_formatter_consults(
    label: str,
    cause: BaseException | None,
    context: BaseException | None,
    suppress: bool,
    length: int,
) -> None:
    """One rule per arm, including the one that is easy to get backwards.

    ``__suppress_context__`` suppresses the CONTEXT and never the CAUSE, so
    ``cause-survives-suppression`` still walks two links. A walk that dropped
    the cause there would report ``from exc`` as closed.
    """
    walked = _chain_of(_linked(cause, context, suppress))
    assert len(walked) == length, f"{label} walked {len(walked)} link(s), expected {length}"


def test_the_chain_walk_terminates_on_a_self_referential_chain() -> None:
    """A cycle must end the walk rather than hang the suite."""
    wrapper = _SyntheticError(_REDACTED)
    wrapper.__context__ = wrapper
    assert len(_chain_of(wrapper)) == _UNCHAINED


def test_an_oserror_renders_the_filename_the_interpreter_attached() -> None:
    """THE GROUND UNDER ``measured-leak``.

    The verdict says a builtin ``OSError``'s ``str()`` discloses the filename
    the interpreter attached. Measured here rather than asserted from the class.
    """
    failure = OSError(_ERRNO, _STRERROR, MARKER)
    assert MARKER in str(failure), (
        f"an OSError did not render its filename under str(): {str(failure)!r}"
    )


# ---------------------------------------------------------------------------
# The exemption claims, RE-MEASURED every run.
# ---------------------------------------------------------------------------


def test_a_unicode_decode_error_renders_no_operand_under_str() -> None:
    """The first EXEMPT entry's measured claim."""
    with pytest.raises(UnicodeDecodeError) as caught:
        (MARKER.encode() + b"\xff").decode("utf-8")
    rendered = str(caught.value)
    assert MARKER not in rendered, f"str() carried the operand: {rendered!r}"
    assert MARKER not in _rendered_chain(caught.value), "the rendered line carried the operand"


def test_a_unicode_decode_error_repr_does_carry_the_operand() -> None:
    """LIMIT 7 IS REAL, not a hedge.

    The exemption is scoped to ``str()`` because ``repr()`` discloses the whole
    operand. A rendering path reaching for ``repr()`` is outside the guard.
    """
    with pytest.raises(UnicodeDecodeError) as caught:
        (MARKER.encode() + b"\xff").decode("utf-8")
    rendered = repr(caught.value)
    assert MARKER in rendered, (
        "repr() did NOT carry the operand, so limit 7 in the guard's docstring "
        f"overstates the risk and should be corrected: {rendered!r}"
    )


def test_a_json_decode_error_renders_no_document_under_str() -> None:
    """The second EXEMPT entry's measured claim."""
    with pytest.raises(json.JSONDecodeError) as caught:
        json.loads('{"' + MARKER + '": }')
    rendered = str(caught.value)
    assert MARKER not in rendered, f"str() carried the document: {rendered!r}"
    assert MARKER not in _rendered_chain(caught.value), "the rendered line carried the document"


# ---------------------------------------------------------------------------
# The planted module - every shape the guard claims to model.
# ---------------------------------------------------------------------------

PLANTED_SOURCE: Final = '''"""Every shape tests/chained_cause_guard.py claims to model."""

import json


class Wrapped(Exception):
    """The wrapper."""


def _make(exc):
    return exc


def redact(value):
    return value


def explicit_oserror(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from exc


def implicit_oserror(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed")


def suppressed_oserror(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from None


def bare_oserror(path):
    try:
        open(path)
    except OSError:
        raise


def aliased_cause(path):
    try:
        open(path)
    except OSError as exc:
        kept = exc
        raise Wrapped("failed") from kept


def call_expression_cause(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from _make(exc)


def explicit_valueerror(text):
    try:
        int(text)
    except ValueError as exc:
        raise Wrapped("failed") from exc


def tuple_with_oserror(text):
    try:
        int(text)
    except (ValueError, OSError) as exc:
        raise Wrapped("failed") from exc


def dotted_handler(text):
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        raise Wrapped("failed") from exc


def redacted_message(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped(redact(path)) from exc


def outside_any_handler():
    raise Wrapped("failed")
'''


def _planted() -> dict[str, Site]:
    """Derive the planted module and index it by qualified name.

    Returns:
        Qualified name to site.
    """
    return {site.qualname: site for site in sites_in_tree({PLANTED_PATH: PLANTED_SOURCE})}


#: One row per shape, EACH ITS OWN ARM. A single arm over the pooled planted
#: module would be met by its strongest member while a weaker one went
#: unmeasured, which is the defect recorded in
#: ``memory/pooled-guard-hides-its-worst-member.md``.
_PLANTED_EXPECTATIONS: Final = [
    ("explicit_oserror", FORM_EXPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    ("implicit_oserror", FORM_IMPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    ("suppressed_oserror", FORM_SUPPRESSED, TYPE_OSERROR, CLOSED_SUPPRESSED),
    ("bare_oserror", FORM_BARE, TYPE_OSERROR, MEASURED_LEAK),
    ("aliased_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, UNPROVEN),
    ("call_expression_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, UNPROVEN),
    ("explicit_valueerror", FORM_EXPLICIT, TYPE_RESOLVED_OTHER, UNPROVEN),
    ("tuple_with_oserror", FORM_EXPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    ("dotted_handler", FORM_EXPLICIT, TYPE_UNRESOLVED, UNPROVEN),
    ("redacted_message", FORM_EXPLICIT, TYPE_OSERROR, MEASURED_LEAK),
]


@pytest.mark.parametrize(
    ("qualname", "form", "cause_type", "verdict"),
    _PLANTED_EXPECTATIONS,
    ids=[row[0] for row in _PLANTED_EXPECTATIONS],
)
def test_each_planted_shape_is_classified_on_its_own_arm(
    qualname: str, form: str, cause_type: str, verdict: str
) -> None:
    """One planted shape, one arm, one verdict."""
    planted = _planted()
    assert qualname in planted, (
        f"the derivation did not find {qualname} at all, so this arm graded "
        f"nothing; it found {sorted(planted)}"
    )
    site = planted[qualname]
    assert site.form == form, f"{qualname} derived form {site.form}, expected {form}"
    assert site.cause_type == cause_type, (
        f"{qualname} derived cause type {site.cause_type}, expected {cause_type}"
    )
    assert classify(site) == verdict, f"{qualname} graded {classify(site)}, expected {verdict}"


def test_a_raise_outside_every_handler_is_not_in_the_population() -> None:
    """A plain raise opens no chain, so it is not this guard's business.

    Widening the population to every ``ast.Raise`` would sweep in the great
    majority of the tree and dilute every per-member arm.
    """
    assert "outside_any_handler" not in _planted(), (
        "a raise with no handler and no cause was counted as a chained raise"
    )


def test_a_redacted_message_does_not_clear_the_cause() -> None:
    """INVARIANT 3. A redaction on the MESSAGE says nothing about the CAUSE.

    ``redacted_message`` wraps its path in a redactor and still chains the raw
    OSError. The guard must grade it exactly as it grades the unredacted site.
    """
    planted = _planted()
    redacted = planted["redacted_message"]
    plain = planted["explicit_oserror"]
    assert classify(redacted) == classify(plain) == MEASURED_LEAK, (
        "a redaction wrapper on the message changed the cause's verdict"
    )


# ---------------------------------------------------------------------------
# A3 - deleting two words must not shrink the graded population.
# ---------------------------------------------------------------------------

A3_WITH_CAUSE: Final = '''"""One site, chained."""


class Wrapped(Exception):
    """The wrapper."""


def touched(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from exc
'''

#: The adversary's edit, applied mechanically rather than transcribed.
A3_WITHOUT_CAUSE: Final = A3_WITH_CAUSE.replace(" from exc", "")


def test_the_two_a3_sources_actually_differ() -> None:
    """The A3 pair is a real edit, not a no-op replace.

    Without this, a replacement that matched nothing would leave two identical
    sources and the A3 arm would compare a population with itself.
    """
    assert A3_WITHOUT_CAUSE != A3_WITH_CAUSE, "the from-exc deletion matched nothing"
    assert " from exc" not in A3_WITHOUT_CAUSE, "the cause clause survived the deletion"


def test_deleting_from_exc_does_not_reduce_the_graded_population() -> None:
    """A3. THE ESCAPE THAT DEFEATS A CAUSE-ONLY DETECTOR, measured.

    The site moves from explicit to implicit and KEEPS its verdict. A detector
    keyed on ``ast.Raise.cause`` would report the population dropping to zero
    and read that as a clean tree.
    """
    before = sites_in_tree({PLANTED_PATH: A3_WITH_CAUSE})
    after = sites_in_tree({PLANTED_PATH: A3_WITHOUT_CAUSE})

    assert len(before) == 1, f"the chained source derived {len(before)} sites, expected 1"
    assert len(after) == len(before), (
        f"deleting two words shrank the population from {len(before)} to {len(after)}"
    )
    assert before[0].form == FORM_EXPLICIT
    assert after[0].form == FORM_IMPLICIT, (
        f"the site did not move to the implicit form: {after[0].form}"
    )
    assert classify(after[0]) == classify(before[0]) == MEASURED_LEAK, (
        "the verdict did not survive the deletion"
    )


def test_a_cause_only_count_would_have_collapsed_on_the_same_edit() -> None:
    """The defect this design avoids, shown rather than described.

    A ``.cause``-keyed population really does go to zero on that edit. This arm
    is what stops the paragraph above from being an unchecked claim.
    """
    after = sites_in_tree({PLANTED_PATH: A3_WITHOUT_CAUSE})
    cause_only = [site for site in after if site.form == FORM_EXPLICIT]
    assert cause_only == [], (
        "the premise is wrong: a cause-only walk still sees the site, so the "
        "four-form population is not justified by this edit"
    )
    assert len(after) == 1, "the four-form population must still hold the site"


# ---------------------------------------------------------------------------
# A7 - green on a tree with no such site.
# ---------------------------------------------------------------------------


def test_an_empty_tree_derives_no_site() -> None:
    """A7. No population, no crash, no verdict."""
    assert sites_in_tree({}) == ()
    assert notes_in_tree({}) == ()
    assert out_of_scope_record(()) == ()


def test_a_tree_with_no_raise_at_all_derives_no_site() -> None:
    """A7. The absence of the defect is not a failure of the derivation."""
    assert sites_in_tree({"clean/module.py": "VALUE = 1\n"}) == ()
    assert notes_in_tree({"clean/module.py": "VALUE = 1\n"}) == ()


def test_a_tree_of_handlers_that_do_not_raise_derives_no_site() -> None:
    """A7. A handler that swallows opens no chain."""
    source = "def f(p):\n    try:\n        open(p)\n    except OSError:\n        return None\n"
    assert sites_in_tree({"clean/module.py": source}) == ()


def test_the_stale_exemption_reporter_is_empty_against_an_empty_record() -> None:
    """A7. An empty record cannot be stale."""
    assert stale_exemptions((), {}) == ()


# ---------------------------------------------------------------------------
# The scope filter - the seed-filter lesson, at BOTH depths.
# ---------------------------------------------------------------------------

_NESTED_AT_SEED: Final = '''"""A def written at the TOP of a handler body."""


class Wrapped(Exception):
    """The wrapper."""


def outer(path):
    try:
        open(path)
    except OSError as exc:
        def inner():
            raise Wrapped("failed")
        return inner
'''

_NESTED_ONE_DEEPER: Final = '''"""The same def, one level deeper."""


class Wrapped(Exception):
    """The wrapper."""


def outer(path):
    try:
        open(path)
    except OSError as exc:
        if path:
            def inner():
                raise Wrapped("failed")
            return inner
    return None
'''


@pytest.mark.parametrize(
    ("label", "source"),
    [("at-the-seed", _NESTED_AT_SEED), ("one-level-deeper", _NESTED_ONE_DEEPER)],
    ids=["at-the-seed", "one-level-deeper"],
)
def test_a_raise_in_a_nested_def_is_not_the_handlers_site(label: str, source: str) -> None:
    """BOTH DEPTHS, because the measured defect was depth-dependent.

    A statement in a nested ``def`` runs in ITS frame with its own
    ``sys.exc_info()``, so it is not the handler's chain. A walk seeded with an
    unfiltered ``handler.body`` catches the deeper one and misses the seeded
    one, making the rule about nesting depth rather than about scope.
    """
    derived = sites_in_tree({PLANTED_PATH: source})
    assert derived == (), (
        f"a raise inside a nested def {label} was attributed to the handler: "
        f"{[site.key for site in derived]}"
    )


def test_an_inner_handler_replaces_the_outer_one() -> None:
    """CPython sets ``__context__`` from the INNERMOST active handler."""
    source = (
        "def f(p):\n"
        "    try:\n"
        "        open(p)\n"
        "    except OSError as exc:\n"
        "        try:\n"
        "            int(p)\n"
        "        except ValueError as inner:\n"
        "            raise RuntimeError('failed')\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert len(derived) == 1, f"expected one site, derived {len(derived)}"
    assert derived[0].handler_type == "ValueError", (
        f"the outer handler was used instead of the inner: {derived[0].handler_type}"
    )
    assert derived[0].cause_type == TYPE_RESOLVED_OTHER


def test_a_finally_block_inside_a_handler_keeps_the_handler() -> None:
    """A ``finally`` still executes inside the handler it is nested in."""
    source = (
        "def f(p):\n"
        "    try:\n"
        "        open(p)\n"
        "    except OSError as exc:\n"
        "        try:\n"
        "            int(p)\n"
        "        finally:\n"
        "            raise RuntimeError('failed')\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert len(derived) == 1, f"expected one site, derived {len(derived)}"
    assert derived[0].handler_type == "OSError", (
        f"the enclosing handler was lost in the finally block: {derived[0].handler_type}"
    )


# ---------------------------------------------------------------------------
# The type leg, and the shadowing subtraction.
# ---------------------------------------------------------------------------


def test_a_module_shadowing_oserror_falls_to_unproven_not_to_a_clearance() -> None:
    """LIMIT 1. Resolution is by bare name, so shadowing must be subtracted.

    The failure direction is checked as well as the fact: the site must land on
    :data:`UNPROVEN`, which is not a clearance, rather than on
    :data:`CLOSED_SUPPRESSED`.
    """
    source = (
        "class OSError(Exception):\n"
        "    pass\n"
        "\n"
        "\n"
        "def f(p):\n"
        "    try:\n"
        "        pass\n"
        "    except OSError as exc:\n"
        "        raise RuntimeError('failed') from exc\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert len(derived) == 1, f"expected one site, derived {len(derived)}"
    assert derived[0].cause_type == TYPE_UNRESOLVED, (
        "a shadowed OSError still resolved against the builtin"
    )
    assert classify(derived[0]) == UNPROVEN, (
        f"a shadowed name produced {classify(derived[0])}, which is not a "
        "non-clearance; the failure direction is wrong"
    )


def test_an_unshadowed_control_still_resolves() -> None:
    """The shadowing arm above is not green because nothing resolves.

    Same source without the shadowing class, so the two differ in exactly the
    subtraction under test.
    """
    source = (
        "def f(p):\n"
        "    try:\n"
        "        pass\n"
        "    except OSError as exc:\n"
        "        raise RuntimeError('failed') from exc\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert len(derived) == 1
    assert derived[0].cause_type == TYPE_OSERROR, (
        "the control did not resolve, so the shadowing arm measures nothing"
    )


def test_a_tuple_handler_takes_its_worst_member_not_its_first() -> None:
    """A verdict summed over a population is met by its strongest member."""
    for clause in ("(ValueError, OSError)", "(OSError, ValueError)"):
        source = (
            "def f(p):\n"
            "    try:\n"
            "        pass\n"
            f"    except {clause} as exc:\n"
            "        raise RuntimeError('failed') from exc\n"
        )
        derived = sites_in_tree({PLANTED_PATH: source})
        assert derived[0].cause_type == TYPE_OSERROR, (
            f"{clause} did not take its worst member: {derived[0].cause_type}"
        )


def test_a_tuple_of_unresolved_members_does_not_become_a_clearance() -> None:
    """An unresolved member poisons the tuple rather than being dropped."""
    source = (
        "def f(p):\n"
        "    try:\n"
        "        pass\n"
        "    except (ValueError, mod.Thing) as exc:\n"
        "        raise RuntimeError('failed') from exc\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert derived[0].cause_type == TYPE_UNRESOLVED
    assert classify(derived[0]) == UNPROVEN


def test_a_handler_binding_no_name_still_resolves_for_the_implicit_form() -> None:
    """``except OSError:`` with no ``as`` still puts an OSError in flight."""
    source = (
        "def f(p):\n"
        "    try:\n"
        "        pass\n"
        "    except OSError:\n"
        "        raise RuntimeError('failed')\n"
    )
    derived = sites_in_tree({PLANTED_PATH: source})
    assert derived[0].form == FORM_IMPLICIT
    assert derived[0].handler_name == ""
    assert derived[0].cause_type == TYPE_OSERROR
    assert classify(derived[0]) == MEASURED_LEAK


# ---------------------------------------------------------------------------
# The exemption record.
# ---------------------------------------------------------------------------


def test_an_exemption_cannot_silence_a_measured_leak() -> None:
    """THE ORDER IN :data:`VERDICT_ORDER` IS LOAD-BEARING.

    An exemption that could launder a measured leak would let a future session
    close this channel with a paragraph instead of with ``from None``.
    """
    site = _planted()["explicit_oserror"]
    fabricated = {site.key: "a reason that must not be allowed to clear this"}
    assert classify(site, fabricated) == MEASURED_LEAK, "an exemption silenced a measured leak"


def test_an_exemption_silences_only_the_exact_site_expression() -> None:
    """Renaming the cause renames the key, so the exemption stops covering it.

    That property is what makes recording a mitigation safe: the adversary's
    ``kept = exc`` edit is a new key with no entry.
    """
    planted = _planted()
    unproven = planted["explicit_valueerror"]
    aliased = planted["aliased_cause"]
    fabricated = {unproven.key: "measured, and recorded"}
    assert classify(unproven, fabricated) == EXEMPT_RECORDED
    assert classify(aliased, fabricated) == UNPROVEN, (
        "an exemption for one site expression covered a different one"
    )


def test_every_exemption_reason_says_what_was_measured() -> None:
    """A reason that states no measurement is an opinion with a key."""
    for key, reason in EXEMPT.items():
        assert "MEASURED" in reason, f"{key} states no measurement"
        assert len(reason) > len(key), f"{key} has a reason shorter than its key"


def test_the_stale_exemption_reporter_reports_a_fabricated_key() -> None:
    """The reporter is graded on a fabricated record, then run on the live one.

    A clean result on the live record is also what a broken reporter produces,
    so the fabricated key comes first. The live result WARNS rather than fails:
    an arm that reddens when a site is repaired is anti-correlated with success.
    """
    fabricated = {"clockspeed/save/nowhere.py::f::E::OSError::exc": "names nothing"}
    reported = stale_exemptions(raise_sites(), fabricated)
    assert reported == ("clockspeed/save/nowhere.py::f::E::OSError::exc",), (
        f"the reporter did not report a fabricated key: {reported}"
    )

    stale = stale_exemptions(raise_sites(), EXEMPT)
    if stale:
        lines = "\n".join(f"  stale EXEMPT key, remove it: {key!r}" for key in stale)
        warnings.warn(f"{len(stale)} exemption(s) no longer needed:\n{lines}", stacklevel=1)


# ---------------------------------------------------------------------------
# A1 - the live population, its denominator, and one arm per member.
# ---------------------------------------------------------------------------


def test_the_live_population_is_derived_and_not_empty() -> None:
    """A1. THE DENOMINATOR. Every zero below is worthless without this."""
    swept = tracked_sources()
    assert len(swept) > 1, f"the git sweep read {len(swept)} files"
    sites = raise_sites()
    assert sites, "the live derivation found no chained raise at all"
    graded = [site for site in sites if site.is_graded]
    assert graded, f"the sweep found {len(sites)} sites and none in {GRADED_LAYER}"


def test_every_site_key_is_distinct() -> None:
    """A COLLIDING KEY WOULD LET ONE EXEMPTION FORGIVE SEVERAL SITES.

    Four live sites collide on every key segment except the qualified name,
    which is why the qualified name is in the key.
    """
    sites = raise_sites()
    keys = [site.key for site in sites]
    assert len(set(keys)) == len(keys), (
        "two sites share a key, so an exemption for one would cover the other: "
        f"{sorted(key for key in keys if keys.count(key) > 1)}"
    )


def _graded_sites() -> list[Site]:
    """The live sites this module grades.

    Returns:
        Every site under :data:`GRADED_LAYER`, ordered.
    """
    return [site for site in raise_sites() if site.is_graded]


@pytest.mark.parametrize("site", _graded_sites(), ids=lambda site: site.key)
def test_every_graded_site_carries_exactly_one_verdict(site: Site) -> None:
    """A1. ONE ARM PER MEMBER, and the verdict is computed, never looked up.

    A single arm over the pooled graded population would be satisfied by its
    strongest member while its weakest went unmeasured.
    """
    verdict = classify(site)
    assert verdict in VERDICT_ORDER, f"{site.key} graded {verdict!r}, not a known verdict"
    assert site.form in FORMS, f"{site.key} carries form {site.form!r}"
    assert site.cause_type in (TYPE_OSERROR, TYPE_RESOLVED_OTHER, TYPE_UNRESOLVED)
    applicable = [
        candidate
        for candidate in VERDICT_ORDER
        if classify(site, EXEMPT if candidate == EXEMPT_RECORDED else {}) == candidate
    ]
    assert applicable[0] == verdict, (
        f"{site.key} takes {verdict} while {applicable} also apply, so the "
        "precedence in VERDICT_ORDER is not what classify() implements"
    )


def test_the_graded_leaks_are_reported_every_run() -> None:
    """THE FINDING IS SURFACED, and deliberately does not redden the suite.

    A ``measured-leak`` site is a real channel: the traceback renders a builtin
    ``OSError``'s ``str()``, filename included, beside a message this project
    took care to redact. Whether to CLOSE those sites - with ``from None``, or
    by narrowing what is caught - is a decision above this guard, which only
    measures. Failing here would also make the arm anti-correlated with
    success: it would go green only once every site was repaired and red again
    the moment a new one appeared, which is the same signal a warning gives
    without blocking the merge that introduces the guard.

    ASSERTS NOTHING ABOUT THE COUNT, so repairing a site cannot redden it.
    """
    leaks = [site for site in _graded_sites() if classify(site) == MEASURED_LEAK]
    if not leaks:
        return
    body = "\n".join(f"  {site.key} line {site.lineno}" for site in leaks)
    warnings.warn(
        f"CS-857 measured-leak, {len(leaks)} chained raise(s) under {GRADED_LAYER} render a "
        f"builtin OSError's str() beside a redacted message:\n{body}",
        stacklevel=1,
    )


@pytest.mark.parametrize("site", _graded_sites(), ids=lambda site: site.key)
def test_no_graded_site_is_cleared_by_anything_but_from_none(site: Site) -> None:
    """INVARIANT 3. THE ONLY CLEARANCE IS STRUCTURAL.

    ``closed-suppressed`` may be reached only from the ``from None`` form. No
    redaction result, no type, no exemption may produce it.

    ASSERTED AS A BICONDITIONAL, and the first draft was not. It read ``if
    cleared: assert suppressed``, so a mutation that stopped ANY site being
    cleared left every member taking the empty branch and the whole arm passed
    on a guard that had lost its clearance. That is the shape recorded in
    ``memory/an-empty-population-satisfies-every-zero.md``, inside the arm
    written to enforce it. Every site now takes one branch or the other.
    """
    if site.form == FORM_SUPPRESSED:
        assert classify(site) == CLOSED_SUPPRESSED, (
            f"{site.key} writes from None and was not cleared by it"
        )
        assert site.cause_expr == NO_CAUSE
    else:
        assert classify(site) != CLOSED_SUPPRESSED, (
            f"{site.key} was cleared without a from None clause, so something "
            "other than the interpreter's own suppression issued a clearance"
        )


def test_both_branches_of_the_clearance_arm_have_a_live_member() -> None:
    """The biconditional above is exercised in BOTH directions, or it says so.

    A branch with no member is a branch nobody measured. This SKIPS rather than
    fails when the tree stops carrying one, because an arm that reddens when a
    site is repaired is anti-correlated with success.
    """
    graded = _graded_sites()
    suppressed = [site for site in graded if site.form == FORM_SUPPRESSED]
    other = [site for site in graded if site.form != FORM_SUPPRESSED]
    if not suppressed or not other:
        pytest.skip(
            f"{len(suppressed)} suppressed and {len(other)} other graded sites, so "
            "one branch of the clearance arm has no live member this run"
        )
    assert {classify(site) for site in suppressed} == {CLOSED_SUPPRESSED}
    assert CLOSED_SUPPRESSED not in {classify(site) for site in other}


def test_the_placeholders_never_collide_with_a_real_expression() -> None:
    """A placeholder that could be written as source would be ambiguous.

    ``<context>`` and its siblings are not valid Python, so no authored cause
    expression can ever be mistaken for one.
    """
    for placeholder in (IMPLICIT_CAUSE, ACTIVE_CAUSE, BARE_RAISE, NO_CAUSE):
        assert placeholder.startswith("<"), f"{placeholder!r} could be authored source"
        assert placeholder.endswith(">"), f"{placeholder!r} could be authored source"


def test_neither_guard_file_transcribes_a_site() -> None:
    """INVARIANT 1. NO TRANSCRIBED SITE LIST, and no dead citation either.

    The CS-857 note's own cited line numbers had drifted by eighteen before
    this slice started, which is exactly what a transcribed list does.
    """
    for relative in _OWNED_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        found = _TRANSCRIBED_SITE.findall(text)
        assert found == [], f"{relative} transcribes a line-numbered site: {found}"


# ---------------------------------------------------------------------------
# The __notes__ census - a zero with a live positive control.
# ---------------------------------------------------------------------------


def test_the_note_census_fires_on_a_planted_add_note() -> None:
    """POSITIVE CONTROL. The zero below means nothing without this."""
    source = "def f(exc, detail):\n    exc.add_note(detail)\n    raise exc\n"
    found = notes_in_tree({PLANTED_PATH: source})
    assert len(found) == 1, f"the census missed a planted add_note: {found}"
    assert found[0].channel == NOTE_CALL
    assert found[0].qualname == "f"


def test_the_note_census_fires_on_a_planted_notes_attribute() -> None:
    """POSITIVE CONTROL for the second channel."""
    source = "def f(exc, detail):\n    exc.__notes__ = [detail]\n    raise exc\n"
    found = notes_in_tree({PLANTED_PATH: source})
    assert len(found) == 1, f"the census missed a planted __notes__: {found}"
    assert found[0].channel == NOTE_ATTRIBUTE


def test_the_live_note_census_finds_this_modules_own_fixture() -> None:
    """A LIVE POSITIVE CONTROL, not only a synthetic one.

    A planted string proves the detector fires on a string. This proves it
    fires on the git sweep, which is the population the zero is about. If this
    module is not yet in the sweep the arm SKIPS with a reason - an untracked
    file is invisible to a git-backed guard, and no evidence is a skip.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    mine = [note for note in note_sites() if note.module == _THIS_MODULE]
    assert mine, "the live census did not find this module's own add_note fixture"
    assert any(note.channel == NOTE_CALL for note in mine)


def test_no_shipped_module_attaches_a_note_to_an_exception() -> None:
    """THE ZERO, with its denominator and its detector both asserted.

    Scoped to :data:`GRADED_LAYER`: this module's own fixture is a note site by
    design, and counting it would make the zero unreachable.
    """
    assert len(tracked_sources()) > 1, "the sweep read nothing, so the zero is vacuous"
    shipped = [note for note in note_sites() if note.module.startswith(GRADED_LAYER)]
    assert shipped == [], (
        "a shipped module attaches a note to an exception, which renders in the "
        f"traceback and is invisible to a cause walk: {shipped}"
    )


def test_the_live_sweep_finds_this_modules_own_chain_fixtures() -> None:
    """THE IMPLICIT FORM HAS A LIVE MEMBER, which the shipped tree does not.

    The tracked tree contains zero implicit-context sites under
    :data:`GRADED_LAYER`, so that zero rests on the detector working. This arm
    is the live proof, alongside the planted one.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    mine = {site.form for site in raise_sites() if site.module == _THIS_MODULE}
    missing = set(FORMS) - mine
    assert not missing, (
        f"the live sweep did not find these forms in this module's fixtures: "
        f"{sorted(missing)}; it found {sorted(mine)}"
    )


# ---------------------------------------------------------------------------
# The frozen files - derived, classified, recorded, never edited.
# ---------------------------------------------------------------------------


def test_the_frozen_list_is_parsed_from_claude_md_and_is_not_empty() -> None:
    """PARSED, NOT RESTATED. A second copy of the list is a copy that drifts."""
    listed = frozen_paths()
    assert listed, "CLAUDE.md section 6 yielded no frozen path"
    assert any(path.endswith(".py") for path in listed), (
        f"no frozen path is a Python file, so this guard can never record one: {listed}"
    )


_FROZEN_MARKDOWN: Final = (
    "## 5. Something else\n\n- `not/frozen.py`\n\n"
    "## 6. Frozen files\n\nThese require explicit operator approval to modify:\n\n"
    "- `.githooks/*`\n- `scripts/example.py`\n\n"
    "**The rule:** the grant is recorded in `docs/LEDGER.md` before the edit.\n\n"
    "## 7. Settled\n\n- `also/not/frozen.py`\n"
)


def test_the_frozen_parser_reads_a_well_formed_section() -> None:
    """POSITIVE CONTROL, on synthetic markdown rather than on the live file."""
    assert frozen_from_text(_FROZEN_MARKDOWN) == (".githooks/*", "scripts/example.py")


def test_the_frozen_parser_stops_at_the_next_heading() -> None:
    """A bullet in a neighbouring section is not a frozen path.

    Both neighbours in the fixture carry a backticked path, so a parser that
    ran past either boundary would return them.
    """
    parsed = frozen_from_text(_FROZEN_MARKDOWN)
    assert "not/frozen.py" not in parsed, "the parser read the preceding section"
    assert "also/not/frozen.py" not in parsed, "the parser ran past the section end"
    assert "docs/LEDGER.md" not in parsed, "a backticked path in prose read as a bullet"


@pytest.mark.parametrize(
    ("label", "document"),
    [
        ("no-such-heading", "## 6. Something else\n\n- `scripts/example.py`\n"),
        ("heading-lists-nothing", "## 6. Frozen files\n\nNothing here.\n\n## 7. Next\n"),
    ],
    ids=["no-such-heading", "heading-lists-nothing"],
)
def test_the_frozen_parser_raises_rather_than_returning_an_empty_list(
    label: str, document: str
) -> None:
    """A FROZEN LIST THAT CAME BACK EMPTY WOULD OPEN EVERY FROZEN FILE.

    ``is_frozen`` would answer False for everything and this module would grade
    a frozen file as in scope. These two arms exist because a mutation removing
    the empty-list check survived the entire census before they were written.
    """
    with pytest.raises(ChainedCauseDerivationError) as caught:
        frozen_from_text(document)
    assert "frozen" in str(caught.value), (
        f"the {label} failure does not say what it could not read: {caught.value}"
    )


def test_a_frozen_path_is_matched_and_a_neighbour_is_not() -> None:
    """The matcher is graded on both directions, not only on a hit."""
    listed = frozen_paths()
    for pattern in listed:
        probe = pattern[:-1] + "any_file" if pattern.endswith("*") else pattern
        assert is_frozen(probe), f"{probe} was not matched by its own pattern {pattern}"
    assert not is_frozen("clockspeed/save/world.py"), "a shipped module read as frozen"
    assert not is_frozen("tools/edit_lint_check.py"), "an unfrozen tool read as frozen"


def test_no_frozen_site_is_in_the_graded_layer() -> None:
    """The two scopes cannot overlap, so nothing frozen is ever asked to change."""
    for site in raise_sites():
        if is_frozen(site.module):
            assert not site.is_graded, f"{site.key} is both frozen and graded"


def test_the_frozen_sites_are_recorded_and_reported_every_run() -> None:
    """DERIVED, CLASSIFIED, PRINTED. Never edited.

    ``CLAUDE.md`` section 6 routes a frozen-file edit through an adjudicator
    with the grant recorded in ``docs/LEDGER.md``. This module only reads, so
    the frozen sites are surfaced as a warning on every run rather than being
    fixed or hidden. The record is asserted non-empty so the report cannot
    quietly become a report about nothing.
    """
    record = out_of_scope_record(raise_sites())
    assert record, (
        "the frozen record is empty; either the frozen files stopped chaining "
        "raises or the derivation stopped reaching them"
    )
    body = "\n".join(f"  {line}" for line in record)
    warnings.warn(
        f"CS-857 out-of-scope-recorded, {len(record)} chained raise(s) in frozen "
        f"files, NOT edited:\n{body}",
        stacklevel=1,
    )


# ---------------------------------------------------------------------------
# The derivation must RAISE, never return an empty population.
# ---------------------------------------------------------------------------


def _clear_caches() -> None:
    """Drop every cached derivation so the next call re-runs."""
    tracked_sources.cache_clear()
    raise_sites.cache_clear()
    note_sites.cache_clear()


def test_a_git_failure_raises_rather_than_returning_an_empty_population() -> None:
    """Silence here would make an empty sweep indistinguishable from a clean one.

    Monkeypatching by hand rather than with the fixture, so the caches are
    cleared in a ``finally`` and a failure cannot leave a poisoned cache behind
    for every later arm.
    """

    def boom() -> list[str]:
        raise RuntimeError("git could not be run: OSError")

    original = chained_cause_guard.tracked_python_files
    chained_cause_guard.tracked_python_files = boom
    _clear_caches()
    try:
        with pytest.raises(RuntimeError, match="git could not be run"):
            raise_sites()
    finally:
        chained_cause_guard.tracked_python_files = original
        _clear_caches()


def test_a_read_failure_raises_rather_than_shrinking_the_population() -> None:
    """An unread file is a silently smaller population."""

    def missing() -> list[str]:
        return ["no/such/module/anywhere.py"]

    original = chained_cause_guard.tracked_python_files
    chained_cause_guard.tracked_python_files = missing
    _clear_caches()
    try:
        with pytest.raises(ChainedCauseDerivationError, match="could not be read"):
            raise_sites()
    finally:
        chained_cause_guard.tracked_python_files = original
        _clear_caches()


def test_a_parse_failure_raises_rather_than_shrinking_the_population() -> None:
    """A skipped module is a silently smaller population."""
    with pytest.raises(ChainedCauseDerivationError, match="did not parse"):
        sites_in_tree({"broken/module.py": "def (\n"})
    with pytest.raises(ChainedCauseDerivationError, match="did not parse"):
        notes_in_tree({"broken/module.py": "def (\n"})


def test_the_derivation_error_carries_no_absolute_path() -> None:
    """NON-NEGOTIABLES 3 AND 12. The error is itself an echo path.

    A ``SyntaxError``'s own ``str()`` renders the filename it was handed and an
    ``OSError``'s renders the path it failed on, so neither is interpolated and
    both are dropped with ``from None``.
    """
    with pytest.raises(ChainedCauseDerivationError) as caught:
        sites_in_tree({"broken/module.py": "def (\n"})
    message = str(caught.value)
    assert "broken/module.py" in message, "the error does not say which module"
    assert str(REPO_ROOT) not in message, "the error carries an absolute repo path"
    assert not re.search(r"[A-Za-z]:[\\/]", message), (
        f"the error carries an absolute path: {message!r}"
    )
    assert caught.value.__cause__ is None, "the parse failure was chained rather than dropped"
    assert caught.value.__suppress_context__, "the parse failure's context was not suppressed"


def test_the_guard_does_not_chain_its_own_derivation_failures() -> None:
    """The guard obeys its own rule, checked through the guard itself.

    Every site the guard derives for its own module must be ``from None``, so a
    derivation failure cannot render the absolute path that caused it.
    """
    guard = "tests/chained_cause_guard.py"
    if guard not in tracked_sources():
        pytest.skip(f"{guard} is not in the git sweep; run git add -N first")
    own = [site for site in raise_sites() if site.module == guard]
    assert own, "the guard derived no site for itself"
    for site in own:
        assert classify(site) == CLOSED_SUPPRESSED, (
            f"the guard's own {site.key} is not closed with from None"
        )
