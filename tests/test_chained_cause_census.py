"""CS-857 - the arms over ``tests/chained_cause_guard.py``.

THE MEASUREMENTS COME FIRST AND EVERYTHING ELSE RESTS ON THEM. The guard's
verdicts are claims about what CPython renders, so this module renders each
shape with a SYNTHETIC MARKER and reads the result, rather than reasoning about
the interpreter from memory. ``from None`` around a locally-declared class is
one of the two shapes measured NOT to render, and it was the guard's only
positive clearance until CS-884.

CS-884 ADDED THE SECOND, and it is measured the same way and then some. A
callee whose every return builds a builtin ``OSError`` out of ``errno`` and
``strerror`` alone carries no path, in the cause slot of an explicit chain and
as the raised expression of a ``from None`` alike. That clearance and every
shape that only looks like it are decided TWICE - statically here, and by a
CHILD INTERPRETER whose default excepthook renders the plant - because this
module's subject is the tree's SOLE enumerator of the population and a second
static reader would be wrong the same way it is.

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

import ast
import json
import re
import socket
import ssl
import subprocess
import sys
import traceback
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests import chained_cause_guard
from tests.assertion_rendering_guard import REPO_ROOT
from tests.chained_cause_guard import (
    ACTIVE_CAUSE,
    ADVICE_LAYER,
    BARE_RAISE,
    BUCKET_CONTROL,
    BUCKET_FROZEN,
    BUCKET_GRADED,
    BUCKET_UNCLASSIFIED,
    BUCKETS,
    CLOSED_PATHLESS,
    CLOSED_SUPPRESSED,
    CONTROL_MODULES,
    EXEMPT,
    EXEMPT_RECORDED,
    FORM_BARE,
    FORM_EXPLICIT,
    FORM_IMPLICIT,
    FORM_SUPPRESSED,
    FORMS,
    IMPLICIT_CAUSE,
    MEASURED_LEAK,
    NO_CAUSE,
    NOTE_ATTRIBUTE,
    NOTE_CALL,
    RECORDED_BUCKETS,
    SWEPT_ROOTS,
    TYPE_OSERROR,
    TYPE_RESOLVED_OTHER,
    TYPE_UNRESOLVED,
    UNPROVEN,
    VERDICT_ORDER,
    ChainedCauseDerivationError,
    DeferredRaiseSite,
    NoteSite,
    Site,
    bucket_of,
    classify,
    deferred_findings,
    deferred_out_of_scope_record,
    deferred_raise_sites,
    deferred_raise_sites_in_tree,
    frozen_from_text,
    frozen_paths,
    is_frozen,
    note_census_modules,
    note_findings,
    note_sites,
    notes_in_tree,
    notes_out_of_scope_record,
    out_of_scope_record,
    raise_sites,
    sites_in_tree,
    stale_exemptions,
    store_reach,
    tracked_sources,
    verdict_distribution,
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

#: A transcribed count of the RAISE population in prose - the shape ``N of the
#: M raises``. ``CLAUDE.md`` section 4 forbids a hardcoded count in a doc, and
#: this is the one spelling of it the two owned files actually grew: filed
#: once, never re-derived, and stale in BOTH halves by the time an adjudicator
#: read it.
#:
#: THE ARM CHECKS RATHER THAN MERELY FORBIDS, which is why the two numbers are
#: CAPTURED. A count that agrees with the live derivation is not a lie; one
#: that disagrees is. A rule that forbade the digits outright would be
#: satisfied by deleting the sentence and would say nothing at all about a pair
#: written tomorrow.
#:
#: WHAT IT DOES NOT COVER, stated rather than left to be discovered. It reads
#: the word ``raises`` and nothing else, so a count of MODULES or of SITES
#: written the same way is not checked - and two such pairs exist in these
#: files today. Both are PAST-TENSE records of what one closed item measured,
#: which is provenance rather than a live claim about the tree; the pair this
#: catches was written in the present tense about the tracked tree, and that is
#: the difference the section-4 rule turns on. A regex cannot read tense, so
#: the narrower word is the honest scope.
#:
#: THE PATTERN DOES NOT MATCH ITS OWN SOURCE, for the reason
#: :data:`_TRANSCRIBED_SITE` records: the regex text carries a literal
#: backslash then the letter d, and a letter is not a digit.
_TRANSCRIBED_RAISE_COUNT: Final = re.compile(r"(\d+) of (?:the )?(\d+) raises")

#: The planted module's path. Deliberately outside :data:`SWEPT_ROOTS`, so a
#: planted arm can never be confused with a live finding. CS-879 turned that
#: from a convention into an enforced fact: this path buckets
#: :data:`BUCKET_UNCLASSIFIED`, which is what the sensitivity arm below reads.
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

    MEASURED EQUIVALENT ON THE SIX SHAPES THIS MODULE PLANTS, AND NOT BEYOND
    THEM. For explicit, suppressed, implicit, bare, aliased and noted, this
    string and a full ``format_exception`` agree on whether the marker is
    present; the full one additionally carried an absolute path and this one
    did not.

    TWO SHAPES OUTSIDE THAT SET DO NOT HOLD, both measured by a CS-857
    adversary. A ``SyntaxError`` anywhere in the chain renders a ``File`` line
    that SURVIVES ``limit=0``, because that line belongs to the exception
    rather than to a frame - and a real one carries an absolute path. And an
    exception whose ``__str__`` is non-deterministic breaks the subset property
    outright, since the two renderings then disagree on their own text. Neither
    is reachable from any shipped site today. The claim is scoped to the
    planted set rather than widened, because widening it is what made it false.

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


def _suppressed_binding_chain() -> None:
    """Re-raise the handler's OWN binding with the context suppressed.

    THE SHAPE RESIDUAL 1 IS ABOUT. ``from None`` closes ``__context__``; it
    says nothing about the exception being raised, which here IS the caught
    ``OSError`` and renders its own ``filename``.
    """
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError as exc:
        raise exc from None


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
    """THE FIRST POSITIVE CLEARANCE, measured rather than assumed.

    ``closed-suppressed`` rests entirely on these three lines. The context is
    asserted to still BE there and to still be suppressed, so the arm cannot
    pass merely because nothing was caught in the first place.

    IT WAS THE ONLY CLEARANCE UNTIL CS-884, which is why this docstring used to
    say so. The second is ``closed-pathless`` and its measurement lives in the
    CS-884 block far below, in a child interpreter rather than here.
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


def test_from_none_reraising_the_binding_still_renders_the_marker() -> None:
    """RESIDUAL 1, MEASURED - the clearance is reachable while the path renders.

    ``tests/test_chained_cause_census.py`` already measures ``from None`` on a
    fixture that raises a WRAPPER, and that arm is correct. It was generalised
    to the FORM, and this arm is the counterexample: same ``from None``, same
    suppressed context, and the marker renders anyway - because the object
    being raised is the handler's own binding rather than a wrapper.

    The chain length is asserted at :data:`_UNCHAINED` on purpose: the context
    IS suppressed, so this is not a chaining failure. One link renders, and
    that one link carries the marker.
    """
    with pytest.raises(OSError, match=MARKER) as caught:
        _suppressed_binding_chain()
    failure = caught.value
    assert failure.__suppress_context__, "from None did not set __suppress_context__"
    chain = _chain_of(failure)
    assert len(chain) == _UNCHAINED, f"the context was walked after all: {len(chain)}"
    rendered = _rendered_chain(failure)
    assert MARKER in rendered, (
        "the binding re-raised under from None did not render its own filename, "
        f"so residual 1 does not reproduce and this arm is wrong: {rendered!r}"
    )


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
# The two surface EXEMPT entries, RE-MEASURED every run.
#
# NEITHER RENDERING IS EVER INTERPOLATED INTO A FAILURE MESSAGE. These arms
# build real paths under a temporary directory, which on this machine sits
# below a home directory - so a message quoting the rendering would itself be
# the echo path CLAUDE.md non-negotiable 12 forbids. Each arm reduces to a
# BOOLEAN and reports the exception CLASS NAME, which carries nothing.
# ---------------------------------------------------------------------------

#: A malformed PEM body. Well-formed armour, unusable content, so the failure
#: comes from the parser rather than from the file being absent.
_BAD_PEM: Final = b"-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"

#: The bracketed code every platform's socket error opens with - ``[WinError
#: 10048]`` here, ``[Errno 98]`` elsewhere. Used as the ``pytest.raises``
#: match so the arm names the failure it expects instead of accepting any
#: OSError at all, and it doubles as a claim: the message leads with an
#: INTERPRETER-GENERATED code rather than with anything the caller supplied.
_ERROR_CODE: Final = r"\[(?:Win)?Err(?:or|no) \d+\]"


def _cert_failure(cert: Path) -> BaseException:
    """Drive ``load_cert_chain`` at one path and hand back what it raised.

    Args:
        cert: The path to offer as both the certificate and the key.

    Returns:
        The caught failure.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with pytest.raises((OSError, ssl.SSLError)) as caught:
        context.load_cert_chain(cert, cert)
    return caught.value


def test_the_cert_measurement_would_have_seen_a_filename(tmp_path: Path) -> None:
    """POSITIVE CONTROL, and the three arms below mean nothing without it.

    An absent marker also describes a marker that never reached the call. This
    reads the SAME errno through a path that DOES attach a filename, so the
    instrument is proven to detect one before it is used to report none.
    """
    missing = tmp_path / f"{MARKER}.pem"
    with pytest.raises(FileNotFoundError) as caught:
        missing.read_bytes()
    carried = MARKER in str(caught.value)
    assert carried, (
        "read_bytes did NOT render the filename, so these arms cannot tell a "
        "safe rendering from a marker that never arrived; the class raised was "
        f"{type(caught.value).__name__}"
    )


def test_load_cert_chain_renders_no_path_for_a_missing_file(tmp_path: Path) -> None:
    """The TLS entry's first measured leg."""
    failure = _cert_failure(tmp_path / f"{MARKER}.pem")
    carried = MARKER in str(failure) or MARKER in _rendered_chain(failure)
    assert not carried, f"str() carried the path; the class was {type(failure).__name__}"


def test_load_cert_chain_renders_no_path_for_a_malformed_pem(tmp_path: Path) -> None:
    """The TLS entry's second measured leg - the SSLError branch."""
    bad = tmp_path / f"{MARKER}.pem"
    bad.write_bytes(_BAD_PEM)
    failure = _cert_failure(bad)
    carried = MARKER in str(failure) or MARKER in _rendered_chain(failure)
    assert not carried, f"str() carried the path; the class was {type(failure).__name__}"


def test_load_cert_chain_renders_no_path_for_an_unopenable_file(tmp_path: Path) -> None:
    """The TLS entry's third measured leg - the PERMISSION branch.

    A DIRECTORY is used rather than an ACL edit: it is the portable way to make
    the open fail with an OSError that is neither ENOENT nor a PEM parse error,
    and it needs no privileged call. On this machine it raises PermissionError;
    the arm asserts the RENDERING rather than the subclass, so a platform
    answering IsADirectoryError still measures the thing that matters.
    """
    blocked = tmp_path / f"{MARKER}-dir"
    blocked.mkdir()
    failure = _cert_failure(blocked)
    carried = MARKER in str(failure) or MARKER in _rendered_chain(failure)
    assert not carried, f"str() carried the path; the class was {type(failure).__name__}"


def test_a_bind_collision_renders_no_path_under_str() -> None:
    """The BindError entry's measured claim.

    Binds an ephemeral loopback port, then binds it again. Loopback only, and
    the listener is closed on every path.

    THE FAILURE IS READ THROUGH ``pytest.raises`` RATHER THAN AN ``except ...
    as exc`` BLOCK, and that is not a style choice. ``str(exc)`` on a caught
    binding is the exact shape ``tests/test_exception_rendering.py`` forbids
    tree-wide - it flagged an earlier draft of this very arm, which is the
    guard working. The named FIELDS are what the claim actually rests on:
    ``OSError.__str__`` appends ``: 'filename'`` only when the interpreter set
    one, so both being None IS the no-path property rather than evidence for
    it.
    """
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        holder.bind(("127.0.0.1", 0))
        holder.listen(1)
        taken = holder.getsockname()[1]
        second = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with pytest.raises(OSError, match=_ERROR_CODE) as caught:
                second.bind(("127.0.0.1", taken))
            rendered = str(caught.value)
            has_filename = caught.value.filename is not None
            has_filename2 = caught.value.filename2 is not None
        finally:
            second.close()
    finally:
        holder.close()
    assert not has_filename, "the bind collision attached a filename"
    assert not has_filename2, "the bind collision attached a second filename"
    assert "\\" not in rendered, "the bind message carried a backslash path separator"


# ---------------------------------------------------------------------------
# The planted module - every shape the guard claims to model.
# ---------------------------------------------------------------------------

PLANTED_SOURCE: Final = '''"""Every shape tests/chained_cause_guard.py claims to model."""

import json


class Wrapped(Exception):
    """The wrapper."""


def _make(exc):
    return exc


def _pathless(exc):
    return OSError(exc.errno, exc.strerror)


def _rebind(exc):
    exc = OSError(exc.errno, exc.strerror)
    return exc


def _closure(exc):
    def _inner():
        return exc

    return OSError(exc.errno, exc.strerror)


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


def suppressed_binding(path):
    try:
        open(path)
    except OSError as exc:
        raise exc from None


def suppressed_alias(path):
    try:
        open(path)
    except OSError as exc:
        kept = exc
        raise kept from None


def suppressed_walrus(path):
    try:
        open(path)
    except OSError as exc:
        raise (kept := exc) from None


def suppressed_subscript(path):
    try:
        open(path)
    except OSError as exc:
        held = [exc]
        raise held[0] from None


def suppressed_builtin(path):
    try:
        open(path)
    except OSError as exc:
        raise OSError(exc.errno, exc.strerror) from None


def rebind_expression_cause(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from _rebind(exc)


def closure_expression_cause(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from _closure(exc)


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


def clone_expression_cause(path):
    try:
        open(path)
    except OSError as exc:
        raise Wrapped("failed") from _pathless(exc)


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
#: unmeasured, which is the pooled-assertion form recorded in
#: ``memory/a-guard-can-be-green-by-accident.md``.
_PLANTED_EXPECTATIONS: Final = [
    ("explicit_oserror", FORM_EXPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    ("implicit_oserror", FORM_IMPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    ("suppressed_oserror", FORM_SUPPRESSED, TYPE_UNRESOLVED, CLOSED_SUPPRESSED),
    ("suppressed_binding", FORM_SUPPRESSED, TYPE_OSERROR, MEASURED_LEAK),
    ("suppressed_alias", FORM_SUPPRESSED, TYPE_UNRESOLVED, UNPROVEN),
    ("suppressed_walrus", FORM_SUPPRESSED, TYPE_UNRESOLVED, UNPROVEN),
    ("suppressed_subscript", FORM_SUPPRESSED, TYPE_UNRESOLVED, UNPROVEN),
    # CS-884. THE INLINE CONSTRUCTION IS NOT CLEARED. It is filename-free and
    # safe; the pathless predicate is about a CALLEE, and widening it to the
    # raise itself was never measured. Limit 12 states the under-report, and
    # this row is what keeps the boundary where the code puts it.
    ("suppressed_builtin", FORM_SUPPRESSED, TYPE_UNRESOLVED, UNPROVEN),
    # CS-884. A clone written IN PLACE returns a NAME, so neither the
    # forwarding rule nor the pathless predicate reads it as a construction and
    # it stays UNPROVEN - an under-report, stated in limit 12.
    ("rebind_expression_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, UNPROVEN),
    # CS-884. The nested def's return belongs to the nested def; the ONLY
    # return in this function's own scope IS the pathless construction, so it
    # is cleared. The cause type is unchanged, which is what this row was
    # originally about.
    ("closure_expression_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, CLOSED_PATHLESS),
    ("bare_oserror", FORM_BARE, TYPE_OSERROR, MEASURED_LEAK),
    ("aliased_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, UNPROVEN),
    ("call_expression_cause", FORM_EXPLICIT, TYPE_OSERROR, MEASURED_LEAK),
    # CS-884. THE ROW THIS ITEM WAS OPENED FOR. Until it, the shipped repair
    # and the no-op above it were graded the same word, and the pair sitting
    # side by side in this table is what made the conflation legible.
    ("clone_expression_cause", FORM_EXPLICIT, TYPE_UNRESOLVED, CLOSED_PATHLESS),
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
    assert graded, f"the sweep found {len(sites)} sites and none graded"


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
        Every site in :data:`BUCKET_GRADED`, ordered.
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

    ASSERTS NOTHING ABOUT THE COUNT OF LEAKS, so repairing a site cannot
    redden it. It DOES assert the graded population is non-empty, which is a
    different claim: an empty leak list and a broken derivation are otherwise
    byte-identical from outside, and that is how this signal stopped firing
    silently once the last leak was repaired.

    CS-884 FOLDED THE WHOLE DISTRIBUTION IN, on BOTH exits. The report used to
    name one verdict, so a repair moving sites between the other four was
    invisible in the run output - which is how 24 of 38 graded sites sat in a
    conflated bucket for three sessions with the reporter reading correct.
    """
    graded = _graded_sites()
    assert graded, (
        "the graded population is EMPTY, so this arm measured nothing. An empty "
        "result and a broken derivation are byte-identical from outside - "
        "memory/an-empty-population-satisfies-every-zero.md"
    )
    spread = ", ".join(verdict_distribution(graded))
    leaks = [site for site in graded if classify(site) == MEASURED_LEAK]
    if not leaks:
        warnings.warn(
            f"CS-857 census: {len(graded)} chained raise(s) in the "
            f"{BUCKET_GRADED} bucket, none classified {MEASURED_LEAK} this "
            f"run. Verdicts: {spread}.",
            stacklevel=1,
        )
        return
    body = "\n".join(f"  {site.key} line {site.lineno}" for site in leaks)
    warnings.warn(
        f"CS-857 measured-leak, {len(leaks)} of {len(graded)} chained raise(s) in "
        f"the {BUCKET_GRADED} bucket render a builtin OSError's str() beside a "
        f"redacted message. Verdicts: {spread}.\n{body}",
        stacklevel=1,
    )


def test_the_census_reports_even_when_no_leak_is_found() -> None:
    """M4. THE SIGNAL MUST FIRE ON A CLEAN TREE, OR IT IS NOT A SIGNAL.

    The reporter above returned early on an empty leak list, so the moment the
    last site was repaired it went silent - indistinguishable from a
    derivation that had broken. A mutation restoring that early return SURVIVED
    the whole module, which is what this arm exists to stop.
    """
    with pytest.warns(UserWarning, match="CS-857"):
        test_the_graded_leaks_are_reported_every_run()


@pytest.mark.parametrize("site", _graded_sites(), ids=lambda site: site.key)
def test_no_graded_site_is_cleared_by_anything_but_from_none(site: Site) -> None:
    """INVARIANT 3. EVERY CLEARANCE IS STRUCTURAL.

    ``closed-suppressed`` may be reached only from the ``from None`` form. No
    redaction result, no type, no exemption may produce it.

    SCOPED TO ``closed-suppressed`` ALONE, AND THAT IS NOW A NARROWING RATHER
    THAN A TAUTOLOGY. CS-884 added a second clearance, so this arm no longer
    covers the whole positive half of the taxonomy and must not be cited as if
    it did; ``test_no_graded_site_is_cleared_pathless_without_constructing_
    one`` is its counterpart, written as the same biconditional for the same
    reason. Both clearances remain structural - one rests on the interpreter
    setting ``__suppress_context__`` over a locally-declared class, the other
    on what a callee CONSTRUCTS - and neither rests on a value or a spelling.

    ASSERTED AS A BICONDITIONAL, and the first draft was not. It read ``if
    cleared: assert suppressed``, so a mutation that stopped ANY site being
    cleared left every member taking the empty branch and the whole arm passed
    on a guard that had lost its clearance. That is the shape recorded in
    ``memory/an-empty-population-satisfies-every-zero.md``, inside the arm
    written to enforce it. Every site now takes one branch or the other.
    """
    if site.form == FORM_SUPPRESSED and site.raises_local_class:
        assert classify(site) == CLOSED_SUPPRESSED, (
            f"{site.key} writes from None and constructs a class its own module "
            "declares, and was not cleared by it"
        )
        assert site.cause_expr == NO_CAUSE
    elif site.form == FORM_SUPPRESSED:
        assert classify(site) != CLOSED_SUPPRESSED, (
            f"{site.key} writes from None but does not CONSTRUCT a class its "
            "module declares, so what it raises may be the handler's own "
            "exception under another spelling - the 15 shapes adversary L2 "
            "measured reaching the clearance while rendering a filename"
        )
    else:
        assert classify(site) != CLOSED_SUPPRESSED, (
            f"{site.key} was cleared without a from None clause, so something "
            "other than the interpreter's own suppression issued a clearance"
        )


def test_both_branches_of_the_clearance_arm_have_a_live_member() -> None:
    """The arm above is exercised in EVERY direction, or it says so.

    A branch with no member is a branch nobody measured. This SKIPS rather than
    fails when the tree stops carrying one, because an arm that reddens when a
    site is repaired is anti-correlated with success.

    SPLIT ON THE AXIS THE CLEARANCE TURNS ON, WHICH IS NOT THE FORM. Round 1
    narrowed the clearance and left this arm splitting `suppressed` against
    `other` - the PRE-narrowing binary. The new branch had zero live members
    and this arm passed anyway, which is
    ``memory/an-empty-population-satisfies-every-zero.md`` reproduced inside
    the arm named after it. The `withheld` branch is reported even when empty
    so the skip message says which branch was unmeasured.
    """
    graded = _graded_sites()
    cleared = [s for s in graded if s.form == FORM_SUPPRESSED and s.raises_local_class]
    withheld = [s for s in graded if s.form == FORM_SUPPRESSED and not s.raises_local_class]
    other = [site for site in graded if site.form != FORM_SUPPRESSED]
    if not cleared or not other:
        pytest.skip(
            f"{len(cleared)} cleared, {len(withheld)} withheld and {len(other)} other "
            "graded sites, so a branch of the clearance arm has no live member this run"
        )
    assert {classify(site) for site in cleared} == {CLOSED_SUPPRESSED}
    assert CLOSED_SUPPRESSED not in {classify(site) for site in withheld}
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


def test_the_uncensused_raise_partition_is_derived_not_written() -> None:
    """INVARIANT 1'S SIBLING. A COUNT IN PROSE IS A LIE WITH A TIMESTAMP ON IT.

    :func:`chained_cause_guard._form_of` answers None for a raise that opens no
    chain, and its docstring said in the present tense how many of the tracked
    tree's raises that was. Nothing derived the pair and nothing guarded it, so
    it went stale in both halves and the gap WIDENED every round the tree grew.
    That is exactly the ``CLAUDE.md`` section 4 failure - a measured number
    restated in prose with no machine-checked owner.

    THE TOTAL IS COUNTED BY ``ast.walk`` AND NOT BY THE GUARD'S OWN WALK, which
    is the point of the arm rather than an implementation detail. Deriving both
    halves from :func:`chained_cause_guard._walk` would make this two readings
    of one traversal, and two readers of the same walk are wrong the same way -
    ``CONVENTIONS.md`` section 5.2. ``ast.walk`` descends everything
    unconditionally, so it is an independent census of the denominator.

    IT REPORTS RATHER THAN PINS. No literal appears in any assertion: the arm
    asserts the SHAPE - both halves populated, the uncensused half the larger,
    and any pair still written in prose agreeing with what the tree holds - and
    emits the derived numbers as a warning so a reader gets a live count.
    """
    sources = tracked_sources()
    total = sum(
        1
        for module, source in sources.items()
        for node in ast.walk(ast.parse(source, filename=module))
        if isinstance(node, ast.Raise)
    )
    censused = len(raise_sites())
    uncensused = total - censused
    assert censused, "no raise reached the Site population, so the split has collapsed"
    assert uncensused, (
        "every raise in the tree reached the Site population, so the None form "
        "is empty and the sentence this arm guards describes nothing"
    )
    assert uncensused > censused, (
        f"the uncensused half is no longer the majority - {uncensused} answer "
        f"None against {censused} censused - so the word MAJORITY in "
        f"_form_of's docstring is now wrong. The repair is that SENTENCE, not "
        f"this arm and not the tree"
    )
    for relative in _OWNED_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for written_part, written_whole in _TRANSCRIBED_RAISE_COUNT.findall(text):
            assert (int(written_part), int(written_whole)) == (uncensused, total), (
                f"{relative} writes a raise count in prose that the tree does "
                f"not hold: it says {written_part} of {written_whole} and the "
                f"live derivation is {uncensused} of {total}"
            )
    warnings.warn(
        f"CS-857 raise partition, derived this run: {total} raise statement(s) "
        f"in the tracked tree, {censused} in the Site population and "
        f"{uncensused} answering None - the plain raise outside every handler "
        f"that _form_of deliberately leaves out.",
        stacklevel=1,
    )


# ---------------------------------------------------------------------------
# The __notes__ census - a zero with a live positive control, over the SAME
# population the chained-raise census grades. CS-883.
#
# THE DENOMINATOR IS THE GRADED BUCKET, NOT THE GRADED RAISE SITES. A module
# holding a note and no chained raise is invisible to the site population, and
# on this tree that describes most of the bucket. Asserting over modules from
# the sweep is the shape ``test_every_advice_layer_module_is_graded`` already
# uses, and for the same stated reason.
# ---------------------------------------------------------------------------

#: A planted module in the GRADED bucket and OUTSIDE :data:`ADVICE_LAYER` -
#: which is exactly the region CS-883 widened the census into. Never touched on
#: disk: :func:`notes_in_tree` reads a mapping, so this is a key and not a file.
PLANTED_WIDENED_PATH: Final = "tools/planted_notes.py"

#: A planted module in the graded bucket and INSIDE the advice layer, so the
#: widening arm can show the old scope caught this one and missed its sibling.
PLANTED_ADVICE_PATH: Final = "clockspeed/planted_notes.py"

#: One ``add_note`` call. The payload is a PARAMETER, never a literal, so no
#: arm below can be read as planting a path.
PLANTED_NOTE_SOURCE: Final = "def f(exc, detail):\n    exc.add_note(detail)\n    raise exc\n"

#: Named so no bare number sits in an assertion.
_ONE_NOTE: Final = 1
_PLANTED_NOTE_PAIR: Final = 2


def _homeless_notes(notes: Sequence[NoteSite]) -> list[str]:
    """The note sites in NEITHER population, rendered.

    THE ONE CODE PATH BOTH DIRECTIONS OF THE ARM RUN, for the reason
    :func:`_homeless` records one census over.

    MATCHES THE RECORD LINE ON THE MODULE AND LINE TOGETHER, so a module whose
    path is a strict prefix of another's cannot be found inside that other
    module's line and read as recorded.

    Args:
        notes: Any derived note population, live or planted.

    Returns:
        One ``module:line qualname`` string per note site that is neither
        censused nor on the out-of-scope record, sorted.
    """
    censused = note_findings(notes)
    recorded = notes_out_of_scope_record(notes)

    def _placed(note: NoteSite) -> bool:
        """Whether one note site reached either population.

        Args:
            note: The site to look for.

        Returns:
            True when a censused line or a recorded line carries it.
        """
        at = f"{note.module}:{note.lineno} "
        return any(line.startswith(f"note-finding {at}") for line in censused) or any(
            f" {at}" in line for line in recorded
        )

    return sorted(
        f"{note.module}:{note.lineno} {note.qualname}" for note in notes if not _placed(note)
    )


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


def _assert_module_holds_no_note(module: str, notes: Sequence[NoteSite]) -> None:
    """Assert one censused module attaches no note, and that it IS censused.

    THE ONE CODE PATH BOTH DIRECTIONS RUN, for the reason :func:`_homeless`
    records: the live arms assert this finds nothing, and the sensitivity arm
    asserts it finds a planted note. Two separately written checks could drift
    apart and then agree by accident, which ``CLAUDE.md`` section 5 rules out
    as evidence.

    Args:
        module: The censused module path.
        notes: The derived note population to read.

    Raises:
        AssertionError: The module is not in the censused population, or it
            holds a note site.
    """
    bucket = bucket_of(module)
    assert bucket == BUCKET_GRADED, (
        f"{module} is on the note census's member list and buckets {bucket!r}, "
        f"so the denominator and the classifier disagree about it"
    )
    found = [line for line in note_findings(notes) if line.startswith(f"note-finding {module}:")]
    count = len(found)
    assert count == 0, (
        f"{module} attaches {count} note(s) to an exception. A note renders in "
        f"the formatted traceback under the exception it is attached to and is "
        f"INVISIBLE to a cause walk, so nothing else in this census sees it:\n"
        + "\n".join(f"  {line}" for line in found)
    )


@pytest.mark.parametrize("module", note_census_modules(tracked_sources()), ids=lambda m: m)
def test_every_censused_module_attaches_no_note_to_an_exception(module: str) -> None:
    """CS-883. THE ZERO, ONE ARM PER MEMBER RATHER THAN OVER A POOLED TOTAL.

    A pooled zero reports one line for a whole population and gives a later
    reader no way to see which members were actually measured -
    ``memory/a-guard-can-be-green-by-accident.md``. One arm per member makes
    the denominator something pytest itself counts and prints, and makes a new
    note redden an arm that NAMES the module it is in.

    THE MEMBER LIST IS MODULES FROM THE SWEEP, NOT SITES. Most of the graded
    bucket chains no raise at all, so a note-census keyed on the raise
    population would cover a fraction of it and report the same clean zero.
    """
    _assert_module_holds_no_note(module, note_sites())


def test_the_note_census_covers_every_module_the_raise_census_grades() -> None:
    """CS-883. THE DENOMINATOR, ASSERTED RATHER THAN ASSUMED.

    The arms above are zeroes, and a zero over an absent member proves nothing
    - ``memory/an-empty-population-satisfies-every-zero.md``. This arm is what
    says WHICH members were measured: every module the chained-raise census
    grades, no fewer.

    THE TWO CENSUSES SAT IN ONE FILE MEASURING DIFFERENT POPULATIONS. The note
    zero was asserted over :data:`ADVICE_LAYER` while CS-879 widened grading to
    whatever :func:`bucket_of` calls :data:`BUCKET_GRADED`, so a note attached
    in a ``scripts/``, ``tools/`` or test-support module was graded by nothing.
    No count is quoted here on purpose: a number in prose is a fact with no
    owner and it drifts.
    """
    swept = tracked_sources()
    assert len(swept) > 1, "the git sweep read nothing, so this arm measured nothing"
    graded = {module for module in swept if bucket_of(module) == BUCKET_GRADED}
    assert graded, (
        "the sweep found no graded module, so the note census has an empty "
        "denominator - memory/an-empty-population-satisfies-every-zero.md"
    )
    uncovered = sorted(graded - set(note_census_modules(swept)))
    count = len(uncovered)
    assert count == 0, (
        f"{count} of {len(graded)} module(s) the chained-raise census GRADES "
        f"are outside the note census, so a note attached in one of them is "
        f"graded by nothing and reported by nothing:\n"
        + "\n".join(f"  {module}" for module in uncovered)
    )


def test_the_note_census_reaches_past_the_advice_layer() -> None:
    """CS-883. THE WIDENING IS A LIVE FACT, NOT A SENTENCE ABOUT ONE.

    The arm above would still pass if :data:`ADVICE_LAYER` and the graded
    bucket happened to name the same modules, and then a later narrowing back
    to the advice layer would cost nothing. This arm asserts the census is
    STRICTLY wider, so re-scoping it to the shipped directory reddens.
    """
    swept = tracked_sources()
    censused = set(note_census_modules(swept))
    advice = {module for module in swept if module.startswith(ADVICE_LAYER)}
    assert advice, f"the sweep found no module under {ADVICE_LAYER}"
    assert advice < censused, (
        f"the note census covers {len(censused)} module(s) and the advice layer "
        f"holds {len(advice)}, so the census is no wider than the scope CS-883 "
        f"was filed to widen it past"
    )


def test_a_note_outside_the_advice_layer_is_censused_and_would_not_have_been() -> None:
    """CS-883. THE PLANTED POSITIVE, AIMED AT THE WIDENED REGION SPECIFICALLY.

    The live zero above is a zero over a population with NO positive member -
    the tree attaches no note in any graded module - so on its own it is
    exactly what a detector scoped to nothing returns. This plants a note in
    the region the widening added and asserts BOTH directions of the change on
    one input: the census reports it, and the scope it replaced does not.

    THE SECOND ASSERTION IS THE ONE THAT MATTERS. Without it this arm passes
    against the old, narrow census too, and the widening would rest on a
    sentence again.
    """
    planted = notes_in_tree(
        {PLANTED_WIDENED_PATH: PLANTED_NOTE_SOURCE, PLANTED_ADVICE_PATH: PLANTED_NOTE_SOURCE}
    )
    assert len(planted) == _PLANTED_NOTE_PAIR, (
        f"the plant did not derive one note per module: {planted}"
    )
    assert bucket_of(PLANTED_WIDENED_PATH) == BUCKET_GRADED, (
        f"{PLANTED_WIDENED_PATH} does not bucket {BUCKET_GRADED}, so this arm "
        f"is not planting in the region CS-883 widened the census into"
    )
    assert not PLANTED_WIDENED_PATH.startswith(ADVICE_LAYER), (
        f"{PLANTED_WIDENED_PATH} is inside {ADVICE_LAYER}, so the old scope "
        f"would have caught it and this arm measures nothing"
    )

    censused = note_findings(planted)
    widened = [line for line in censused if PLANTED_WIDENED_PATH in line]
    assert len(widened) == _ONE_NOTE, (
        f"the note census did not report the plant in {PLANTED_WIDENED_PATH}, "
        f"which is a graded module: {censused}"
    )
    would_have_been = [note for note in planted if note.module.startswith(ADVICE_LAYER)]
    assert len(would_have_been) == _ONE_NOTE, (
        "the premise is wrong: the advice-layer scope this census replaced sees "
        f"a different number of the two plants than the one inside it: {would_have_been}"
    )
    assert would_have_been[0].module == PLANTED_ADVICE_PATH, (
        "the advice-layer scope caught the wrong plant, so this arm is not "
        "measuring the scope it claims to"
    )


def test_the_per_member_note_arm_reddens_on_a_planted_note() -> None:
    """CS-883. THE SECOND DIRECTION OF THE PER-MEMBER ARM.

    Every live arm above asserts a zero, and a zero is what a broken detector
    returns too. This feeds the SAME assert helper the live arms run a planted
    note in a graded module and asserts it fails, so the green above rests on a
    helper measured to fire rather than on one that was never exercised.
    """
    planted = notes_in_tree({PLANTED_WIDENED_PATH: PLANTED_NOTE_SOURCE})
    with pytest.raises(AssertionError, match="attaches"):
        _assert_module_holds_no_note(PLANTED_WIDENED_PATH, planted)


def test_every_derived_note_site_is_either_censused_or_recorded() -> None:
    """CS-883. NO NOTE SITE IS SWEPT UP AND THEN DROPPED ON THE FLOOR.

    The mirror of ``test_every_derived_site_is_either_graded_or_recorded``, and
    it closes a hole the per-member arms cannot see: they iterate the CENSUSED
    modules, so a note in a module outside :data:`SWEPT_ROOTS` - which reaches
    :data:`BUCKET_UNCLASSIFIED` and therefore no member list at all - would be
    derived and then measured by nothing.
    """
    notes = note_sites()
    assert notes, (
        "the live derivation found no note site at all, so this arm measured "
        "nothing - memory/an-empty-population-satisfies-every-zero.md"
    )
    homeless = _homeless_notes(notes)
    count = len(homeless)
    assert count == 0, (
        f"{count} derived note site(s) are in neither population - not "
        f"censused, not recorded, so nothing measures them and nothing "
        f"reports them:\n" + "\n".join(f"  {line}" for line in homeless)
    )


def test_the_note_exhaustiveness_arm_reddens_on_a_note_no_bucket_claims() -> None:
    """CS-883. THE SECOND DIRECTION, on the one shape that falls through both.

    :data:`PLANTED_PATH` sits outside :data:`SWEPT_ROOTS`, so it buckets
    :data:`BUCKET_UNCLASSIFIED` - censused by nothing because it is not graded,
    recorded by nothing because :data:`RECORDED_BUCKETS` is not a catch-all.
    That hole is deliberate, and this arm is the proof it is still open in the
    direction that reddens.
    """
    planted = notes_in_tree({PLANTED_PATH: PLANTED_NOTE_SOURCE})
    assert bucket_of(PLANTED_PATH) == BUCKET_UNCLASSIFIED, (
        f"{PLANTED_PATH} now buckets {bucket_of(PLANTED_PATH)!r}, so this arm "
        f"no longer feeds the sentinel it was written for"
    )
    assert note_findings(planted) == (), "an unclassified note site was censused"
    assert notes_out_of_scope_record(planted) == (), (
        "an unclassified note site was swept onto the record, so the record is "
        "acting as a catch-all and the exhaustiveness arm cannot fail"
    )
    assert _homeless_notes(planted) == [
        f"{PLANTED_PATH}:{planted[0].lineno} {planted[0].qualname}"
    ], "a note site no bucket claims was not reported as being in neither population"


@pytest.mark.parametrize("bucket", RECORDED_BUCKETS, ids=list(RECORDED_BUCKETS))
def test_each_recorded_note_bucket_renders_its_own_line(bucket: str) -> None:
    """CS-883. THE RECORD CARRIES BOTH ITS BUCKETS, PER MEMBER.

    A record filtering on one bucket and claiming two is the defect
    :func:`out_of_scope_record` was widened for one census over. Proven on a
    planted note in each bucket rather than on the live tree, so repairing or
    moving a live fixture cannot redden it.
    """
    module = _recorded_bucket_probe(bucket)
    planted = notes_in_tree({module: PLANTED_NOTE_SOURCE})
    assert bucket_of(module) == bucket, (
        f"the probe path {module} buckets {bucket_of(module)!r}, not {bucket!r}"
    )
    rendered = notes_out_of_scope_record(planted)
    assert len(rendered) == _ONE_NOTE, f"the record did not carry the {bucket} note: {rendered}"
    assert bucket.upper() in rendered[0], (
        f"the {bucket} line does not name its own bucket: {rendered[0]}"
    )


#: The attachments the walk does NOT derive, because the attribute name is a
#: STRING rather than an ``ast.Attribute``. Each is a stated under-report of
#: the CHANNEL, which CS-883 did not widen - it widened the POPULATION.
_STRING_NAMED_ATTACHMENTS: Final = (
    ("setattr", 'def f(exc, detail):\n    setattr(exc, "__notes__", [detail])\n    raise exc\n'),
    (
        "getattr-call",
        'def f(exc, detail):\n    getattr(exc, "add_note")(detail)\n    raise exc\n',
    ),
    (
        "methodcaller",
        "import operator\n\n\ndef f(exc, detail):\n"
        '    operator.methodcaller("add_note", detail)(exc)\n    raise exc\n',
    ),
)


@pytest.mark.parametrize(
    ("label", "source"),
    _STRING_NAMED_ATTACHMENTS,
    ids=[row[0] for row in _STRING_NAMED_ATTACHMENTS],
)
def test_a_note_attached_through_a_string_name_is_not_derived(label: str, source: str) -> None:
    """CS-883. THE CHANNEL LIMIT, MEASURED PER SHAPE RATHER THAN ASSERTED.

    The zero this census ships is over a population that CS-883 widened and a
    channel it did not. Naming that in prose is what the guard's own docstring
    calls a sentence rather than an artifact, so each escape is planted and the
    silence is read back off the derivation.

    A RED ARM HERE IS GOOD NEWS, NOT A REGRESSION. It means the walk grew to
    see the shape, and the fix is to delete the row - after checking what it
    now reports about the three shipped modules that read ``__notes__`` at
    RUNTIME to measure a redaction, which are not attachments at all.
    """
    planted = notes_in_tree({PLANTED_WIDENED_PATH: source})
    assert planted == (), (
        f"the {label} shape is now derived, so the stated channel limit in "
        f"note_findings is out of date: {planted}"
    )


def test_the_note_channel_the_walk_does_derive_still_fires() -> None:
    """CS-883. THE LIMIT ARMS ABOVE NEED A CONTROL THAT IS NOT A ZERO.

    Three zeroes in a row are also what a derivation that stopped working
    returns. This runs the SAME entry point over the spelling the walk DOES
    model, in the SAME planted module, so the zeroes above are a statement
    about the shape rather than about the plumbing.
    """
    planted = notes_in_tree({PLANTED_WIDENED_PATH: PLANTED_NOTE_SOURCE})
    assert len(planted) == _ONE_NOTE, f"the modelled spelling derived nothing: {planted}"
    assert planted[0].channel == NOTE_CALL


def test_the_live_note_record_accounts_for_this_censuss_own_fixtures() -> None:
    """CS-883. THE FIXTURES ARE EXCLUDED BY THE TAXONOMY, NOT BY A LIST.

    :data:`CONTROL_MODULES` is what keeps this module's own planted notes out
    of the census, and it is the SAME constant that keeps its planted chained
    raises out of the graded site population. Nothing here names a file to
    ignore; the exclusion is read back off :func:`bucket_of`, and the record
    prints it every run so it is a visible decision rather than a silence.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    recorded = notes_out_of_scope_record(note_sites())
    assert recorded, "the live record carries no note site, so it accounts for nothing"
    mine = [line for line in recorded if f"{_THIS_MODULE}:" in line]
    assert mine, f"the live record does not account for this module's own note fixture: {recorded}"
    assert all(BUCKET_CONTROL.upper() in line for line in mine), (
        f"this module's note fixture is recorded under a bucket other than {BUCKET_CONTROL}: {mine}"
    )


def test_the_live_sweep_finds_this_modules_own_chain_fixtures() -> None:
    """THE IMPLICIT FORM HAS A LIVE MEMBER, which the shipped tree does not.

    The tracked tree contains zero implicit-context sites under
    :data:`ADVICE_LAYER`, so that zero rests on the detector working. This arm
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
    """The two scopes cannot overlap, so nothing frozen is ever asked to change.

    HELD BY CONSTRUCTION SINCE CS-879 and kept anyway. :func:`bucket_of` tests
    frozenness in its first branch, so this can no longer fail against the
    current implementation - it fails against a FUTURE one that reintroduces a
    graded predicate deciding scope independently, which is the arrangement
    that produced the CS-879 defect. Retained as the consistency check on the
    derivation, not as a live measurement.
    """
    for site in raise_sites():
        if is_frozen(site.module):
            assert not site.is_graded, f"{site.key} is both frozen and graded"


def test_the_out_of_scope_sites_are_recorded_and_reported_every_run() -> None:
    """DERIVED, CLASSIFIED, PRINTED. Never edited.

    ``CLAUDE.md`` section 6 routes a frozen-file edit through an adjudicator
    with the grant recorded in ``docs/LEDGER.md``. This module only reads, so
    the frozen sites are surfaced as a warning on every run rather than being
    fixed or hidden. The record is asserted non-empty so the report cannot
    quietly become a report about nothing.

    CS-879 WIDENED THE RECORD from the frozen sites to every site this module
    declines to grade, each line naming the bucket that excluded it. Reporting
    only the frozen half left this module's own fixtures in neither
    population, which is the same defect CS-879 was opened for one bucket over.
    """
    record = out_of_scope_record(raise_sites())
    assert record, (
        "the out-of-scope record is empty; either nothing outside the graded "
        "bucket chains a raise any more or the derivation stopped reaching it"
    )
    body = "\n".join(f"  {line}" for line in record)
    warnings.warn(
        f"CS-857 out-of-scope-recorded, {len(record)} chained raise(s) this "
        f"module does not grade, NOT edited:\n{body}",
        stacklevel=1,
    )


@pytest.mark.parametrize("bucket", RECORDED_BUCKETS, ids=list(RECORDED_BUCKETS))
def test_each_recorded_bucket_has_a_line_of_its_own(bucket: str) -> None:
    """ONE ARM PER RECORDED BUCKET, so neither half hides inside the other.

    A single non-empty assertion over the pooled record is met by whichever
    bucket happens to be populated while the other goes unmeasured, which is
    the pooled-assertion form of ``memory/a-guard-can-be-green-by-accident.md``.
    Each bucket asserts its own denominator instead.
    """
    record = out_of_scope_record(raise_sites())
    mine = [line for line in record if f" {bucket.upper()} " in line]
    assert mine, (
        f"the record carries {len(record)} line(s) and none for {bucket}, so "
        f"that bucket's half of the report measured nothing"
    )


# ---------------------------------------------------------------------------
# CS-879 - the taxonomy is EXHAUSTIVE, and its split is derived from the
# frozen list rather than from a directory prefix.
# ---------------------------------------------------------------------------


def _homeless(sites: tuple[Site, ...]) -> list[str]:
    """The sites in NEITHER population, rendered.

    THE ONE CODE PATH BOTH DIRECTIONS OF THE ARM RUN. The live arm asserts
    this returns nothing; the sensitivity arms assert it returns the synthetic
    site they were handed. Two separately written checks could drift apart and
    then agree by accident, which ``CLAUDE.md`` section 5 rules out as
    evidence.

    SHARING CUTS BOTH WAYS, AND CS-879 ROUND 2 MEASURED THE COST. One bug
    here disables the enforcement AND the proof of it at the same time, so
    the predicate below needs a probe for EACH of its two halves, not one
    probe for the function. The bucket half is proven by
    ``test_the_exhaustiveness_arms_redden_on_a_site_no_bucket_claims`` and
    the record half by
    ``test_a_bucketed_site_the_record_drops_is_reported_homeless``.

    MATCHES THE RECORD LINE'S EXACT TAIL, NOT A SUBSTRING. A key that is a
    strict prefix of another key would be found inside that other site's line
    by an ``in`` test, and this arm would report a homeless site as recorded -
    a false negative in the one check CS-879 ships.

    Args:
        sites: Any derived population, live or planted.

    Returns:
        One ``module:line qualname`` string per site that is neither graded
        nor on the out-of-scope record, sorted.
    """
    recorded = out_of_scope_record(sites)
    return sorted(
        f"{site.module}:{site.lineno} {site.qualname}"
        for site in sites
        if not site.is_graded
        and not any(line.endswith(f"{site.key} line {site.lineno}") for line in recorded)
    )


def _assert_site_is_bucketed(site: Site) -> None:
    """Assert one site reaches a named bucket, and that the two seams agree.

    SHARED BY THE LIVE ARM AND THE SENSITIVITY ARM for the same reason
    :func:`_homeless` is.

    Args:
        site: The site to check.

    Raises:
        AssertionError: The module reaches no bucket in
            :data:`chained_cause_guard.BUCKETS`, or the grading predicate and
            the classifier disagree about it.
    """
    bucket = bucket_of(site.module)
    assert bucket in BUCKETS, (
        f"no bucket claims it: {site.module}:{site.lineno} {site.qualname} "
        f"buckets {bucket!r}, which is not one of {list(BUCKETS)}. The census "
        f"derived this site and then had nothing to say about it. Extend the "
        f"taxonomy in tests/chained_cause_guard.py with a STATED reason "
        f"rather than widening a catch-all."
    )
    assert site.is_graded is (bucket == BUCKET_GRADED), (
        f"{site.key} buckets {bucket!r} but its is_graded property says "
        f"{site.is_graded}, so the predicate and the classifier disagree"
    )


@pytest.mark.parametrize("site", raise_sites(), ids=lambda site: site.key)
def test_every_derived_site_reaches_a_named_bucket(site: Site) -> None:
    """CS-879. ONE ARM PER MEMBER, so no site hides behind a populous bucket.

    ASSERTS MEMBERSHIP, NEVER A VERDICT. Which bucket a particular live file
    lands in is not pinned: repairing, moving or deleting one must not redden
    this arm, only leaving one unaccounted for may.
    """
    _assert_site_is_bucketed(site)


def test_every_derived_site_is_either_graded_or_recorded() -> None:
    """CS-879. NO SITE IS SWEPT UP AND THEN DROPPED ON THE FLOOR.

    The derivation reads every tracked ``*.py`` in the repo, so a site it finds
    and then classifies as neither graded nor recorded is a site the census
    paid to derive and then said nothing about. Before CS-879 that was the
    live state: the graded predicate was a flat ``clockspeed/`` prefix and the
    record filtered on frozenness, so every site in a NON-FROZEN ``scripts/``
    or ``tools/`` file, and every site in this module's own fixtures, was
    graded by nothing and reported by nothing - while a comment in the guard
    asserted the opposite of both halves. No count is quoted here on purpose:
    a number in prose is a fact with no owner and it drifts.
    """
    sites = raise_sites()
    assert sites, (
        "the live derivation found no chained raise at all, so this arm "
        "measured nothing - memory/an-empty-population-satisfies-every-zero.md"
    )
    homeless = _homeless(sites)
    count = len(homeless)
    assert count == 0, (
        f"{count} derived site(s) are in neither population - not graded, not "
        f"recorded, so nothing measures them and nothing reports them:\n"
        + "\n".join(f"  {line}" for line in homeless)
    )


def test_the_exhaustiveness_arms_redden_on_a_site_no_bucket_claims() -> None:
    """CS-879. THE SECOND DIRECTION. A ONE-SIDED ARM PROVES NOTHING.

    Both arms above assert a ZERO over the live tree, and a zero is what a
    broken detector returns too. This arm feeds the SAME two code paths a
    synthetic site at a path outside :data:`SWEPT_ROOTS` and asserts each one
    fires, so the green above rests on a detector measured to work rather than
    on one measured to be silent -
    ``memory/an-empty-population-satisfies-every-zero.md``.

    COVERS ONE OF THE TWO ROUTES INTO HOMELESSNESS, AND ONLY ONE. For a site
    outside :data:`SWEPT_ROOTS`, "unclassified" and "in neither population"
    are the same predicate, so this arm cannot see a site that DOES reach a
    bucket and is dropped from the record anyway. That route is
    ``test_a_bucketed_site_the_record_drops_is_reported_homeless``, and
    without it a one-line change to :func:`_homeless` measured green.

    SYNTHETIC, NEVER A LIVE FINDING. The site is derived from an authored
    source fragment through :func:`chained_cause_guard.sites_in_tree`, so
    nothing in the tracked tree can repair this arm into passing vacuously.
    """
    assert not PLANTED_PATH.startswith(SWEPT_ROOTS), (
        f"{PLANTED_PATH} is inside {list(SWEPT_ROOTS)}, so it now reaches a "
        f"real bucket and this arm no longer plants the shape it claims to"
    )
    assert BUCKET_UNCLASSIFIED not in BUCKETS, (
        "the sentinel was added to BUCKETS, so an unclassified module now "
        "counts as classified and the whole check is vacuous"
    )
    derived = sites_in_tree({PLANTED_PATH: A3_WITH_CAUSE})
    assert len(derived) == 1, f"the planted fragment derived {len(derived)} sites, expected 1"
    unswept = derived[0]
    assert bucket_of(unswept.module) == BUCKET_UNCLASSIFIED, (
        f"{unswept.module} was expected to reach no bucket and reached "
        f"{bucket_of(unswept.module)!r}"
    )

    with pytest.raises(AssertionError, match="no bucket claims it"):
        _assert_site_is_bucketed(unswept)

    assert not unswept.is_graded, "an unclassified site was graded"
    assert out_of_scope_record((unswept,)) == (), (
        "the record swallowed an unclassified site, so it is a catch-all and "
        "the graded-or-recorded arm would pass on the shape it exists to fail"
    )
    assert _homeless((unswept,)) == [f"{unswept.module}:{unswept.lineno} {unswept.qualname}"], (
        "the homeless check did not report a site that is in neither population"
    )


def test_the_two_populations_partition_the_taxonomy() -> None:
    """CS-879. GRADED PLUS RECORDED IS EXACTLY THE SET OF NAMED BUCKETS.

    Without this, ``graded or recorded`` could be exhaustive over the live
    tree by luck - a third named bucket nothing currently populates would sit
    outside both populations and no arm would notice until it filled up.
    """
    assert BUCKET_GRADED not in RECORDED_BUCKETS, "the graded bucket is also recorded"
    assert BUCKET_UNCLASSIFIED not in RECORDED_BUCKETS, (
        "the sentinel is recorded, so an unclassified site lands in a "
        "population and the exhaustiveness arms stop biting"
    )
    assert {BUCKET_GRADED, *RECORDED_BUCKETS} == set(BUCKETS), (
        f"the two populations cover {sorted({BUCKET_GRADED, *RECORDED_BUCKETS})} "
        f"while the named buckets are {sorted(BUCKETS)}"
    )


def test_the_split_is_derived_from_the_frozen_list_and_not_from_a_directory() -> None:
    """CS-879. TWO FILES IN ONE DIRECTORY, TWO BUCKETS.

    The acceptance is that the graded and recorded populations are split by
    the frozen list ``CLAUDE.md`` section 6 owns, not by a directory prefix.
    That is proven here by taking each frozen path FROM THE PARSED LIST and
    showing a same-directory neighbour takes a different bucket, so the only
    thing separating them is frozenness.

    NAMES NO LIVE UNFROZEN FILE. The neighbour is a probe path that does not
    exist, so deleting, renaming or repairing any real file cannot redden this.
    """
    probed = 0
    for pattern in frozen_paths():
        if pattern.endswith("*") or "/" not in pattern:
            continue
        directory = pattern.rsplit("/", 1)[0] + "/"
        if not directory.startswith(SWEPT_ROOTS):
            continue
        assert bucket_of(pattern) == BUCKET_FROZEN, (
            f"{pattern} is on the parsed frozen list and buckets {bucket_of(pattern)!r}"
        )
        neighbour = f"{directory}cs879_unfrozen_probe.py"
        expected = BUCKET_CONTROL if neighbour in CONTROL_MODULES else BUCKET_GRADED
        assert bucket_of(neighbour) == expected, (
            f"{neighbour} sits in the same directory as the frozen "
            f"{pattern} and buckets {bucket_of(neighbour)!r}, expected "
            f"{expected!r}; the split is reading the directory, not the "
            f"frozen list"
        )
        probed += 1
    assert probed, (
        "no frozen path in the parsed list named a file inside a swept root, "
        "so this arm compared nothing - "
        "memory/an-empty-population-satisfies-every-zero.md"
    )


def _recorded_bucket_probe(bucket: str) -> str:
    """A module path that reaches one named bucket in :data:`RECORDED_BUCKETS`.

    DERIVED, NEVER HARDCODED. The frozen probe comes from the parsed frozen
    list and the control probe from :data:`CONTROL_MODULES`, so renaming a
    frozen file or a control module cannot leave this arm planting a shape it
    no longer describes.

    Args:
        bucket: The bucket the returned path must reach.

    Returns:
        A repo-relative module path in that bucket.
    """
    if bucket == BUCKET_FROZEN:
        frozen_py = [path for path in frozen_paths() if path.endswith(".py")]
        assert frozen_py, "the parsed frozen list names no .py file to probe with"
        return frozen_py[0]
    assert bucket == BUCKET_CONTROL, f"no probe is defined for bucket {bucket!r}"
    assert CONTROL_MODULES, "no control module is declared to probe with"
    return CONTROL_MODULES[0]


@pytest.mark.parametrize("bucket", RECORDED_BUCKETS, ids=list(RECORDED_BUCKETS))
def test_a_bucketed_site_the_record_drops_is_reported_homeless(
    bucket: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-879 ROUND 2, DEFECT 1. THE SECOND ROUTE INTO HOMELESSNESS.

    THE FIRST SENSITIVITY ARM PROBED ONLY ONE ROUTE AND THAT WAS THE DEFECT.
    It planted a site outside :data:`SWEPT_ROOTS`, where "unclassified" and "in
    neither population" are the SAME predicate, so it never exercised the case
    the graded-or-recorded clause is actually about: a site that DOES reach a
    named bucket and that the record nonetheless omits. Measured on the
    unrepaired module: replacing the record-membership half of
    :func:`_homeless` with a bucket test, and dropping one module from the
    record, put a real site in neither population with the suite still green.
    One bug in the shared helper disabled both the enforcement and its proof.

    THE ANSWER IS NOT TO UNSHARE THE HELPER - sharing is what stops the live
    arm and its proof drifting apart - but to probe BOTH routes through it.

    THE BEFORE/AFTER IS THE ISOLATION. With the real record the planted site
    is NOT homeless; the only thing changed between the two assertions is the
    record, so a green pair can only mean the record half is being read.
    """
    probe = _recorded_bucket_probe(bucket)
    assert bucket_of(probe) == bucket, (
        f"{probe} was chosen as the {bucket} probe and buckets "
        f"{bucket_of(probe)!r}, so this arm plants the wrong shape"
    )
    derived = sites_in_tree({probe: A3_WITH_CAUSE})
    assert len(derived) == 1, f"the planted fragment derived {len(derived)} sites, expected 1"
    site = derived[0]
    assert not site.is_graded, f"{probe} is in {bucket} and was graded"
    assert _homeless(derived) == [], (
        f"the real record already omits this {bucket} site, so stubbing the "
        f"record below would prove nothing about the record half"
    )

    monkeypatch.setitem(globals(), "out_of_scope_record", lambda _sites: ())

    assert _homeless(derived) == [f"{site.module}:{site.lineno} {site.qualname}"], (
        f"a site in the {bucket} bucket that the record does not carry was not "
        f"reported as being in neither population, so the record half of the "
        f"homeless check is not being read"
    )


@pytest.mark.parametrize("module", CONTROL_MODULES, ids=list(CONTROL_MODULES))
def test_each_declared_control_module_earns_its_exclusion(module: str) -> None:
    """CS-879 ROUND 2, DEFECT 2. THE EXCLUSION MUST EARN ITSELF, PER MEMBER.

    :data:`CONTROL_MODULES` is a hand-declared list, so without this arm it is
    a free parameter: anything added to it silently stops being graded on a
    stated reason that may be false of it. That is precisely what the previous
    ``tests/`` prefix did to five modules.

    THE REASON IS CHECKED, NOT ASSUMED. A planted control lives in a pytest
    TEST module, because that is where this census's arms plant them, and it
    must actually plant something - an excluded module that chains no raise is
    an exclusion covering nothing.
    """
    if module not in tracked_sources():
        pytest.skip(f"{module} is not in the git sweep; run git add -N first")
    assert module.rsplit("/", 1)[-1].startswith("test_"), (
        f"{module} is excluded from grading as a planted control but is not a "
        f"test module; a control is planted BY an arm, so a non-test module "
        f"here is real code being excused by a sentence written about fixtures"
    )
    planted = [site for site in raise_sites() if site.module == module]
    assert planted, (
        f"{module} is excluded from grading on the grounds that it plants "
        f"chained raises as this census's positive controls, and it plants "
        f"none, so the exclusion covers nothing"
    )
    assert bucket_of(module) == BUCKET_CONTROL, (
        f"{module} is declared a control module and buckets {bucket_of(module)!r}"
    )


def test_every_advice_layer_module_is_graded() -> None:
    """CS-879 ROUND 2, DEFECT 3. THE ADVICE PATH CANNOT BE RELABELLED AWAY.

    The layer constants are hand-declared, and before this arm nothing stopped
    one swallowing the shipped tree: extending the excluded list to cover
    ``clockspeed/save/`` - the module ``CLAUDE.md`` non-negotiable 12 is
    written about - dropped the save header parser out of grading and the
    suite stayed green. A taxonomy is only safe to edit if the edit that
    matters most reddens.

    ASSERTED OVER MODULES, NOT SITES, so a shipped module that chains nothing
    today is still covered the day it starts.
    """
    swept = tracked_sources()
    assert len(swept) > 1, "the git sweep read nothing, so this arm measured nothing"
    advice = sorted(module for module in swept if module.startswith(ADVICE_LAYER))
    assert advice, (
        f"the sweep found no module under {ADVICE_LAYER}, so this arm graded "
        "nothing - memory/an-empty-population-satisfies-every-zero.md"
    )
    misfiled = sorted(
        f"{module} -> {bucket_of(module)}"
        for module in advice
        if bucket_of(module) != BUCKET_GRADED
    )
    count = len(misfiled)
    assert count == 0, (
        f"{count} of {len(advice)} module(s) in the shipped advice path are no "
        f"longer graded, so a taxonomy edit has excused the code this project "
        f"exists to keep clean:\n" + "\n".join(f"  {line}" for line in misfiled)
    )


@pytest.mark.parametrize("root", SWEPT_ROOTS, ids=list(SWEPT_ROOTS))
def test_every_declared_swept_root_holds_tracked_python(root: str) -> None:
    """CS-879 ROUND 2, DEFECT 3. THE ADDITION DIRECTION OF :data:`SWEPT_ROOTS`.

    The sentinel reddens on a root MISSING from the tuple. It says nothing
    about a root ADDED to it, so adding ``shell/`` - the worked example in the
    constant's own comment - passed silently while widening the domain to a
    scope nobody had reviewed.

    A ROOT THAT HOLDS NO TRACKED PYTHON IS A DOMAIN WIDENED FOR FREE. It
    cannot be answering a real file, because there is no file; it can only be
    pre-authorising whatever lands there later, which is the decision the
    sentinel exists to force someone to make deliberately.
    """
    swept = tracked_sources()
    assert len(swept) > 1, "the git sweep read nothing, so this arm measured nothing"
    inhabitants = [module for module in swept if module.startswith(root)]
    assert inhabitants, (
        f"{root} is declared a swept root and holds no tracked Python, so it "
        f"classifies nothing that exists and pre-authorises everything that "
        f"arrives; remove it until a file needs it"
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


# ---------------------------------------------------------------------------
# CS-857 residual 2 - a raise in a CALLEE of a handler.
#
# WHAT THIS SECTION CLAIMS, AND THE NUMBER IS DELIBERATELY SMALL. The detector
# resolves ONE level, a BARE-NAME callee, in the SAME module. Every other route
# to the same leak is measured below to leak IDENTICALLY and to be invisible to
# it. The findings are therefore an UNDER-report and never a clearance, and
# limit 8 in the guard's docstring keeps saying so.
# ---------------------------------------------------------------------------

#: The fewest POSITIVE rows the planted expectation table may hold. Every
#: negative row would pass against a detector that reported nothing at all, so
#: the table needs more than one shape it must actually FIND.
_MIN_POSITIVE_ROWS: Final = 2


class _CalleeHolder:
    """A method callee, which the detector cannot follow. Blind, and measured."""

    def blow_up(self) -> None:
        """Raise with no ``from``, from a method rather than a function."""
        raise _SyntheticError(_REDACTED)


def _callee_raises_plainly() -> None:
    """Raise with no ``from`` clause, in a function of its own."""
    raise _SyntheticError(_REDACTED)


def _callee_suppresses() -> None:
    """Raise with ``from None``, which closes the context channel."""
    raise _SyntheticError(_REDACTED) from None


def _callee_chains_a_parameter(other: BaseException) -> None:
    """Raise with an explicit cause, which displaces the caller's context."""
    raise _SyntheticError(_REDACTED) from other


def _callee_inner_level() -> None:
    """The second level down. The detector resolves one level and stops."""
    raise _SyntheticError(_REDACTED)


def _callee_outer_level() -> None:
    """Call the second level without raising itself."""
    _callee_inner_level()


def _calls_a_raising_callee() -> None:
    """THE SHAPE. The raise that leaks is in another function entirely."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        _callee_raises_plainly()


def _calls_a_suppressing_callee() -> None:
    """The callee closes the channel with ``from None``."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        _callee_suppresses()


def _calls_a_parameter_chaining_callee(other: BaseException) -> None:
    """The callee chains something else, displacing the caller's context."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        _callee_chains_a_parameter(other)


def _calls_two_levels_down() -> None:
    """The raise is two calls away. MEASURED to leak, and not derived."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        _callee_outer_level()


def _calls_a_method_callee(holder: _CalleeHolder) -> None:
    """The callee is dotted. MEASURED to leak, and not derived."""
    try:
        raise OSError(_ERRNO, _STRERROR, MARKER)
    except OSError:
        holder.blow_up()


# ---------------------------------------------------------------------------
# THE CHANNEL ITSELF, MEASURED. The detector is worth having only if the shape
# it looks for actually renders the caller's value, and worth bounding only if
# the shapes it misses render it too. Both are measured here, not argued.
# ---------------------------------------------------------------------------


def test_a_raise_in_a_callee_renders_the_callers_exception() -> None:
    """THE GROUND UNDER RESIDUAL 2.

    CPython sets ``__context__`` from the THREAD's exception state, not from
    lexical scope, so a helper CALLED from a handler chains exactly as a
    lexical ``raise`` in the handler body does.
    """
    with pytest.raises(_SyntheticError) as caught:
        _calls_a_raising_callee()
    rendered = _rendered_chain(caught.value)
    links = len(_chain_of(caught.value))
    assert MARKER in rendered, "a raise in a callee did NOT render the caller's exception"
    assert links == _CHAINED, f"expected a two-link chain, got {links}"


def test_a_callee_raising_from_none_closes_the_channel() -> None:
    """NEGATIVE CONTROL, and the reason the rule reads ``cause is None``."""
    with pytest.raises(_SyntheticError) as caught:
        _calls_a_suppressing_callee()
    rendered = _rendered_chain(caught.value)
    links = len(_chain_of(caught.value))
    assert MARKER not in rendered, "from None in the callee still rendered the caller's value"
    assert links == _UNCHAINED, f"expected a one-link chain, got {links}"


def test_a_callee_chaining_a_parameter_displaces_the_callers_context() -> None:
    """SECOND NEGATIVE CONTROL. An explicit cause sets ``__suppress_context__``.

    A detector asking only "does the callee raise" would report this shape, and
    the caller's value is measured ABSENT from it.
    """
    with pytest.raises(_SyntheticError) as caught:
        _calls_a_parameter_chaining_callee(_SyntheticError("a parameter"))
    rendered = _rendered_chain(caught.value)
    assert MARKER not in rendered, "an explicit cause still rendered the caller's context"


def test_a_raise_two_levels_down_leaks_and_is_not_derived() -> None:
    """THE ONE-LEVEL BOUND IS A REAL UNDER-REPORT, measured on both halves.

    The value renders; the detector derives nothing. Stating the bound is the
    deliverable - a detector that implied it covered this would be the false
    clearance CS-857 has already produced once.
    """
    with pytest.raises(_SyntheticError) as caught:
        _calls_two_levels_down()
    rendered = _rendered_chain(caught.value)
    links = len(_chain_of(caught.value))
    assert MARKER in rendered, "the two-level shape did not leak, so this bound is overstated"
    assert links == _CHAINED, f"expected a two-link chain, got {links}"
    derived = chained_cause_guard.callee_sites_in_tree({PLANTED_PATH: _PLANTED_TWO_LEVEL_SOURCE})
    assert derived == (), f"the detector claimed to see two levels down: {derived}"


def test_a_method_callee_leaks_and_is_not_derived() -> None:
    """THE BARE-NAME BOUND IS A REAL UNDER-REPORT, measured on both halves."""
    with pytest.raises(_SyntheticError) as caught:
        _calls_a_method_callee(_CalleeHolder())
    rendered = _rendered_chain(caught.value)
    assert MARKER in rendered, "the method shape did not leak, so this bound is overstated"
    derived = chained_cause_guard.callee_sites_in_tree({PLANTED_PATH: _PLANTED_METHOD_SOURCE})
    assert derived == (), f"the detector claimed to see a dotted callee: {derived}"


# ---------------------------------------------------------------------------
# The planted module - every shape the detector claims to decide.
# ---------------------------------------------------------------------------

_PLANTED_TWO_LEVEL_SOURCE: Final = '''"""A raise two calls below the handler."""


class Wrapped(Exception):
    """The wrapper."""


def _inner():
    raise Wrapped("failed")


def _outer():
    _inner()


def calls_two_levels_down(path):
    try:
        open(path)
    except OSError:
        _outer()
'''

_PLANTED_METHOD_SOURCE: Final = '''"""A raise reached through a dotted callee."""


class Holder:
    """The holder."""

    def blow_up(self):
        raise RuntimeError("failed")


def calls_a_method(path, holder):
    try:
        open(path)
    except OSError:
        holder.blow_up()
'''

PLANTED_CALLEE_SOURCE: Final = '''"""Every callee shape the detector decides - CS-857 residual 2."""


class Wrapped(Exception):
    """The wrapper."""


def _raises_plainly():
    raise Wrapped("failed")


def _reraises_bare():
    raise


def _suppresses():
    raise Wrapped("failed") from None


def _chains_a_parameter(other):
    raise Wrapped("failed") from other


def _stays_quiet():
    return None


def _only_raises_in_a_nested_def():
    def _inner():
        raise Wrapped("failed")

    return _inner


def calls_a_raising_helper(path):
    try:
        open(path)
    except OSError:
        _raises_plainly()


def calls_a_bare_reraiser(path):
    try:
        open(path)
    except OSError:
        _reraises_bare()


def calls_a_suppressing_helper(path):
    try:
        open(path)
    except OSError:
        _suppresses()


def calls_a_parameter_chainer(path, other):
    try:
        open(path)
    except OSError:
        _chains_a_parameter(other)


def calls_a_quiet_helper(path):
    try:
        open(path)
    except OSError:
        _stays_quiet()


def calls_a_constructor(path):
    try:
        open(path)
    except OSError:
        raise Wrapped("failed") from None


def calls_a_helper_from_a_value_error(text):
    try:
        int(text)
    except ValueError:
        _raises_plainly()


def calls_a_helper_whose_raise_is_nested(path):
    try:
        open(path)
    except OSError:
        _only_raises_in_a_nested_def()


def calls_a_helper_in_a_nested_def(path):
    try:
        open(path)
    except OSError:

        def _inner():
            _raises_plainly()

        _inner()
'''


def _planted_callees() -> dict[str, str]:
    """Derive the planted callee module, indexed by the HANDLER's scope.

    Returns:
        Qualified name of the enclosing function to the callee it reported.
    """
    return {
        site.qualname: site.callee
        for site in chained_cause_guard.callee_sites_in_tree({PLANTED_PATH: PLANTED_CALLEE_SOURCE})
    }


#: One row per shape, EACH ITS OWN ARM - the pooled-guard rule again. The
#: callee is the name the detector must report, or None when it must report
#: nothing. EVERY None ROW IS A DIFFERENT REASON, and they are not
#: interchangeable: two are measured NON-leaks, three are measured LEAKS the
#: detector cannot see, and one is a constructor the Site population owns.
_CALLEE_EXPECTATIONS: Final = [
    ("calls_a_raising_helper", "_raises_plainly"),
    ("calls_a_bare_reraiser", "_reraises_bare"),
    ("calls_a_suppressing_helper", None),
    ("calls_a_parameter_chainer", None),
    ("calls_a_quiet_helper", None),
    ("calls_a_constructor", None),
    ("calls_a_helper_from_a_value_error", None),
    ("calls_a_helper_in_a_nested_def", None),
    ("calls_a_helper_whose_raise_is_nested", None),
]


@pytest.mark.parametrize(
    ("qualname", "callee"), _CALLEE_EXPECTATIONS, ids=[row[0] for row in _CALLEE_EXPECTATIONS]
)
def test_each_planted_callee_shape_is_decided_on_its_own_arm(
    qualname: str, callee: str | None
) -> None:
    """One planted shape, one arm, one decision."""
    planted = _planted_callees()
    assert planted.get(qualname) == callee, (
        f"{qualname} reported {planted.get(qualname)!r}, expected {callee!r}"
    )


def test_the_planted_callee_module_is_not_decided_by_a_single_shape() -> None:
    """THE DENOMINATOR OF THE ARMS ABOVE.

    Every row could pass against a detector that reported nothing at all if the
    positive rows were removed, so the count of POSITIVE rows is asserted here
    rather than left implicit in the table.
    """
    positives = [row for row in _CALLEE_EXPECTATIONS if row[1] is not None]
    negatives = [row for row in _CALLEE_EXPECTATIONS if row[1] is None]
    assert len(positives) >= _MIN_POSITIVE_ROWS, f"only {len(positives)} positive row(s)"
    assert negatives, "no negative row, so the detector is never asked to decline"


# ---------------------------------------------------------------------------
# The live sweep - a ZERO in the graded bucket, with a live positive control
# and a derived denominator beside it.
# ---------------------------------------------------------------------------


def test_the_live_callee_sweep_finds_this_modules_own_fixtures() -> None:
    """THE LIVE POSITIVE CONTROL, and the zero below is worthless without it.

    The graded bucket holds no residual-2 finding, and a detector that read
    nothing reports the same. This module's own fixtures are real handlers
    calling real raising helpers, so the live git sweep must find them.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    mine = sorted(
        site.callee for site in chained_cause_guard.callee_sites() if site.module == _THIS_MODULE
    )
    assert "_callee_raises_plainly" in mine, (
        f"the live sweep did not find this module's own callee fixture: {mine}"
    )


def test_the_graded_bucket_holds_no_residual_two_finding() -> None:
    """THE MEASURED ZERO, and it asserts its own denominator.

    A zero from a detector that resolved nothing is not a measurement. The
    denominator is the count of OSError-typed handlers whose callee this
    detector actually FOLLOWED to a function in the same module.
    """
    reach = [seen for seen in chained_cause_guard.handler_reach() if seen.resolved]
    assert reach, (
        "the detector resolved NO callee anywhere in the tree, so the zero "
        "below measured nothing - memory/an-empty-population-satisfies-every-zero.md"
    )
    graded = [
        site
        for site in chained_cause_guard.callee_sites()
        if bucket_of(site.module) == BUCKET_GRADED
    ]
    if graded:
        body = "\n".join(
            f"  {site.key} callee defined line {site.callee_lineno}" for site in graded
        )
        warnings.warn(
            f"CS-857 residual 2: {len(graded)} handler(s) call a same-module "
            f"function that raises without a from clause, which renders the "
            f"handler's own exception:\n{body}",
            stacklevel=1,
        )


def test_a_dotted_callee_is_recorded_opaque_and_never_resolved() -> None:
    """THE SPLIT IS GRADED ON A PLANTED SOURCE, not on the live tree.

    The live tree happens to contain opaque callees for other reasons, so a
    live-only arm stays green even when the dotted branch is misfiled - a
    mutation moving a non-Name callee into ``resolved`` SURVIVED the whole
    module until this arm existed. Here the planted handler has exactly one
    callee and it is dotted, so the two populations cannot both be satisfied.
    """
    reach = chained_cause_guard.handler_reach_in_tree({PLANTED_PATH: _PLANTED_METHOD_SOURCE})
    assert len(reach) == 1, f"expected one examined handler, got {len(reach)}"
    seen = reach[0]
    assert seen.opaque == ("holder.blow_up",), f"the dotted callee was not recorded: {seen.opaque}"
    assert seen.resolved == (), f"a dotted callee was reported resolved: {seen.resolved}"


def test_a_nested_def_callee_is_recorded_opaque_and_never_resolved() -> None:
    """THE SCOPE RULE, GRADED DIRECTLY RATHER THAN THROUGH ITS CONSEQUENCE.

    :func:`chained_cause_guard._chaining_functions` and
    :func:`chained_cause_guard._defined_functions` both walk module level only,
    and a mutation to EITHER ALONE is inert - the other still gates, so the
    false positive needs both to be wrong before any shape-based arm notices.
    Measured: both single mutations SURVIVED the whole module. This arm reads
    the rule itself, so the resolvability of a nested ``def`` is asserted
    rather than inferred from a finding that happens not to appear.
    """
    reach = {
        seen.qualname: seen
        for seen in chained_cause_guard.handler_reach_in_tree({PLANTED_PATH: PLANTED_CALLEE_SOURCE})
    }
    seen = reach["calls_a_helper_in_a_nested_def"]
    assert "_inner" in seen.opaque, f"a nested def was not recorded opaque: {seen.opaque}"
    assert "_inner" not in seen.resolved, f"a nested def was reported resolved: {seen.resolved}"


def test_a_constructor_callee_is_recorded_opaque_and_never_resolved() -> None:
    """A class call is the ``Site`` population's business, not this one's."""
    reach = {
        seen.qualname: seen
        for seen in chained_cause_guard.handler_reach_in_tree({PLANTED_PATH: PLANTED_CALLEE_SOURCE})
    }
    seen = reach["calls_a_constructor"]
    assert "Wrapped" in seen.opaque, f"the constructor was not recorded opaque: {seen.opaque}"
    assert "Wrapped" not in seen.resolved, f"a constructor was reported resolved: {seen.resolved}"


def test_the_residual_two_denominator_records_what_it_could_not_follow() -> None:
    """THE (b) HALF - the under-report is DERIVED, not transcribed.

    Every callee the detector could not follow is recorded per handler, so the
    bound is a measurement rather than a sentence. A tree where every callee
    were opaque would still produce a zero, and this is what distinguishes it.
    """
    reach = chained_cause_guard.handler_reach()
    assert reach, "the detector examined NO handler at all"
    opaque = sum(len(seen.opaque) for seen in reach)
    resolved = sum(len(seen.resolved) for seen in reach)
    assert resolved, "no callee was resolved anywhere, so the denominator is vacuous"
    assert opaque, (
        "no callee anywhere was recorded opaque, which would mean this "
        "detector follows every callee shape - it does not, and the arms above "
        "measure two it cannot"
    )


# ---------------------------------------------------------------------------
# CS-884 - THE SHAPE A REPAIR TAKES, AND THE SHAPES THAT ONLY LOOK LIKE ONE.
#
# THE COMMON-MODE RISK THIS BLOCK EXISTS TO BREAK, named by an adjudicator and
# not by this module's author. ``tests/chained_cause_guard.py`` is the SOLE
# enumerator of the chained-cause population, so a bug in a CLEARANCE it issues
# would silently forgive real leaks and nothing else in the tree would notice -
# a second reader of the same AST would agree with it and be wrong the same
# way. Every shape below is therefore decided TWICE, by two instruments that
# share nothing: the census grades it statically, and a CHILD INTERPRETER runs
# the identical plant to completion and the DEFAULT excepthook renders it. A
# static verdict cross-checked against CPython's own printer is the only thing
# that breaks the common mode.
#
# THE CHILD'S STDERR NEVER BECOMES A FIELD, A MESSAGE OR A LOCAL. It carries an
# absolute frame path per stack level, so it is reduced to booleans and counts
# the moment it is read - the same rule ``tests/surface/test_server.py``
# already obeys with :class:`ChildRendering`, for the reason CLAUDE.md
# non-negotiable 12 gives.
# ---------------------------------------------------------------------------

#: The CS-884 payload. Distinct from :data:`MARKER` on purpose: two
#: instruments sharing one marker cannot tell a leak in one from a leak in the
#: other. Not a path, not personal data, not derived from any machine.
CLONE_MARKER: Final = "CS884-SYNTHETIC-MARKER"

#: What CPython's default excepthook opens every rendered exception with.
_TRACEBACK_HEADER: Final = "Traceback (most recent call last):"

#: The failure a construction that cannot be built reports. ``OSError`` takes
#: no keyword arguments, so the keyword spelling of the clone raises this
#: instead of returning anything - measured, not assumed.
_CONSTRUCTION_FAILURE: Final = "TypeError"

#: A child that fails renders at least this many exceptions. Named so no bare
#: number sits in an assertion.
_ONE_TRACEBACK: Final = 1

#: Exactly one, named so no bare number sits in a comparison.
_ONE_VERDICT: Final = 1

#: Exactly one differing line between the control and its subject.
_ONE_DIFFERENCE: Final = 1

#: Seconds a child may take. Generous: it is a floor against a hang, not a
#: performance assertion.
_CLONE_CHILD_TIMEOUT: Final = 120.0

#: Everything every CS-884 plant shares. THE MARKER'S VALUE APPEARS IN NO LINE
#: THE TRACEBACK CAN PRINT, and that is load-bearing rather than tidy: a
#: traceback echoes the SOURCE of every frame on the stack, so a plant with the
#: marker written as a literal inside ``_fail`` would render it through the
#: source-echo channel and every marker-present arm below would pass without
#: measuring the exception at all. Every value is a module-level constant, and
#: module-level assignment lines are not frames.
_CLONE_PLANT_HEAD: Final = f'''"""One CS-884 shape, runnable and derivable from the same text."""

_MARKER = "{CLONE_MARKER}"
_ERRNO = 13
_STRERROR = "Permission denied"
_LEAK_PATH = "dir/" + _MARKER + "/file"
_OTHER = OSError(_ERRNO, _MARKER)


class Wrapped(Exception):
    """The wrapper. Its own message carries nothing."""


def _fail():
    """Raise an OSError whose filename is the field OSError.__str__ appends."""
    raise OSError(_ERRNO, _STRERROR, _LEAK_PATH)


'''

#: The clone the four shipped copies of the idiom actually write.
_CANONICAL_CALLEE: Final = "def c(e):\n    return OSError(e.errno, e.strerror)\n"

#: A no-op, planted beside the real repair because the two were graded
#: identically until CS-884 and the whole item is about telling them apart.
_NOOP_CALLEE: Final = "def c(e):\n    return e\n"


@dataclass(frozen=True)
class _CloneShape:
    """One CS-884 plant, graded statically and run in a child.

    Attributes:
        label: The arm id, and the child script's basename.
        callee: The helper the site calls, as source.
        slot: The raise statement, as written inside the handler body.
        verdict: What :func:`classify` must return for it.
        clone: What :attr:`Site.constructs_pathless_clone` must be.
        marker: Whether :data:`CLONE_MARKER` must reach the child's stderr.
    """

    label: str
    callee: str
    slot: str
    verdict: str
    clone: bool
    marker: bool


@dataclass(frozen=True)
class _ChildChain:
    """What one child printed, reduced to scalars before anything asserts.

    THE RAW STDERR IS NEVER A FIELD, for the reason the block comment above
    gives. Nothing here can put an absolute path into a failure report.

    Attributes:
        exit_code: The child's exit code. Non-zero is what proves the plant
            actually failed; a child that quietly succeeded renders no marker
            for reasons having nothing to do with any clearance.
        marker_rendered: Whether :data:`CLONE_MARKER` appeared at all.
        tracebacks: How many exceptions the excepthook rendered.
        construction_failed: Whether the clone could not be built.
    """

    exit_code: int
    marker_rendered: bool
    tracebacks: int
    construction_failed: bool


def _clone_plant(shape: _CloneShape) -> str:
    """Assemble one plant, MECHANICALLY rather than by transcription.

    Args:
        shape: The row to build.

    Returns:
        A module that both parses into one :class:`Site` and runs to a failure.
    """
    return (
        _CLONE_PLANT_HEAD
        + shape.callee
        + "\n\ndef site():\n"
        + '    """The censused site."""\n'
        + "    try:\n"
        + "        _fail()\n"
        + "    except OSError as exc:\n"
        + f"        {shape.slot}\n"
        + "\n\nsite()\n"
    )


def _clone_site(shape: _CloneShape) -> Site:
    """Derive the one site a plant contains.

    Args:
        shape: The row to derive.

    Returns:
        The site for ``site``.
    """
    derived = {
        found.qualname: found for found in sites_in_tree({PLANTED_PATH: _clone_plant(shape)})
    }
    assert "site" in derived, (
        f"{shape.label}: the derivation found no site at all, so this arm "
        f"graded nothing; it found {sorted(derived)}"
    )
    return derived["site"]


#: ONE ROW PER SHAPE, and the pooled-guard rule governs this table exactly as
#: it governs :data:`_PLANTED_EXPECTATIONS`: every row gets its own static arm
#: AND its own execution arm, because a single arm over the table would be met
#: by whichever member happened to be strongest.
#:
#: THE ``marker`` COLUMN IS NOT DERIVABLE FROM THE ``verdict`` COLUMN, and that
#: is the point of having both. Several rows carry a verdict the execution
#: contradicts, always in the conservative direction: ``nested_shadow_
#: forwarder`` and ``redefined_callee`` report a leak the interpreter does not
#: produce, which is the over-report :data:`VERDICT_ORDER` buys, and the six
#: limit-10 rows report ``unproven`` on shapes that DO leak, which is the
#: under-report limit 10 states. A table computing one column from the other
#: could show neither, and the two directions are partitioned and asserted
#: separately by :data:`_LEAKING_REFUSALS` and :data:`_CLEAN_REFUSALS`.
_CLONE_SHAPES: Final = (
    _CloneShape(
        label="explicit_canonical",
        callee=_CANONICAL_CALLEE,
        slot="raise Wrapped('failed') from c(exc)",
        verdict=CLOSED_PATHLESS,
        clone=True,
        marker=False,
    ),
    _CloneShape(
        label="suppressed_canonical",
        callee=_CANONICAL_CALLEE,
        slot="raise c(exc) from None",
        verdict=CLOSED_PATHLESS,
        clone=True,
        marker=False,
    ),
    _CloneShape(
        label="control_raw_binding",
        callee=_CANONICAL_CALLEE,
        slot="raise Wrapped('failed') from exc",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="implicit_canonical",
        callee=_CANONICAL_CALLEE,
        slot="raise c(exc)",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="noop_forward",
        callee=_NOOP_CALLEE,
        slot="raise Wrapped('failed') from c(exc)",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="arbitrary_strerror",
        callee="def c(e):\n    return OSError(_ERRNO, _MARKER)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="four_positional_args",
        callee="def c(e):\n    return OSError(e.errno, e.strerror, e.filename, e.errno)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="keyword_construction",
        callee="def c(e):\n    return OSError(errno=e.errno, strerror=e.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="one_bad_return",
        callee=(
            "def c(e):\n"
            "    if not e.errno:\n"
            "        return OSError(e.errno, e.strerror)\n"
            "    return e\n"
        ),
        slot="raise Wrapped('failed') from c(exc)",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="filename_field",
        callee="def c(e):\n    return OSError(e.errno, e.filename)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="different_object",
        callee="def c(e):\n    return OSError(_OTHER.errno, _OTHER.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="keyword_call_site",
        callee=_NOOP_CALLEE,
        slot="raise Wrapped('failed') from c(e=exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="lambda_callee",
        callee="def _unused(e):\n    return OSError(e.errno, e.strerror)\n\n\nc = lambda e: e\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="dotted_callee",
        callee=(
            "class Holder:\n"
            '    """A callee reached through a dot."""\n'
            "\n"
            "    @staticmethod\n"
            "    def c(e):\n"
            "        return e\n"
        ),
        slot="raise Wrapped('failed') from Holder.c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="two_step_forward",
        callee="def _inner(e):\n    return e\n\n\ndef c(e):\n    return _inner(e)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="conditional_return",
        callee="def c(e):\n    return e if e.errno else _OTHER\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="container_return",
        callee="def c(e):\n    return (e,)[0]\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="nested_shadow_forwarder",
        callee=(
            "def c(e):\n"
            "    return OSError(e.errno, e.strerror)\n"
            "\n"
            "\n"
            "def elsewhere():\n"
            "    def c(e):\n"
            "        return e\n"
            "\n"
            "    return c\n"
        ),
        slot="raise Wrapped('failed') from c(exc)",
        verdict=MEASURED_LEAK,
        clone=True,
        marker=False,
    ),
    _CloneShape(
        label="no_return_callee",
        callee="def c(e):\n    pass\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=False,
    ),
    _CloneShape(
        label="decorated_callee",
        callee=(
            "def _deco(f):\n"
            "    return f\n"
            "\n"
            "\n"
            "@_deco\n"
            "def c(e):\n"
            "    return OSError(e.errno, e.strerror)\n"
        ),
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=False,
    ),
    _CloneShape(
        label="async_callee",
        callee="async def c(e):\n    return OSError(e.errno, e.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="rebound_parameter",
        callee="def c(e):\n    e = _OTHER\n    return OSError(e.errno, e.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    _CloneShape(
        label="redefined_callee",
        callee=(
            "def c(e):\n    return e\n\n\ndef c(e):\n    return OSError(e.errno, e.strerror)\n"
        ),
        slot="raise Wrapped('failed') from c(exc)",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=False,
    ),
    _CloneShape(
        label="not_an_oserror",
        callee="def c(e):\n    return ValueError(e.errno, e.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=False,
    ),
    _CloneShape(
        label="single_argument",
        callee="def c(e):\n    return OSError(e.errno)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=False,
    ),
    # THE ROW THAT ISOLATES THE ARITY CHECK, and it exists because a mutation
    # battery found nothing else did. ``four_positional_args`` is refused by
    # the FIELD set - its third argument is a filename read - so widening the
    # arity test from "exactly two" to "at least two" left every other row
    # unchanged and the mutant SURVIVED. Here every argument is a clone field
    # and only the count is wrong, so the arity test is the one thing deciding
    # it. It renders no marker on this plant, because errno and strerror carry
    # none; that a third positional argument IS the filename slot, and leaks
    # when a real path goes into it, is what ``four_positional_args`` measures.
    _CloneShape(
        label="three_clone_field_args",
        callee="def c(e):\n    return OSError(e.errno, e.strerror, e.strerror)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=False,
    ),
    # THE ROW THAT ISOLATES THE KEYWORD CHECK, found the same way.
    # ``keyword_construction`` passes NO positional argument, so the arity test
    # refuses it and dropping the keyword test changed nothing. This one
    # carries exactly two positional clone-field reads AND a keyword, so only
    # the keyword test stands between it and a clearance - of a construction
    # that raises TypeError, with the caught original rendered as its context.
    _CloneShape(
        label="mixed_keyword_construction",
        callee="def c(e):\n    return OSError(e.errno, e.strerror, filename=e.filename)\n",
        slot="raise Wrapped('failed') from c(exc)",
        verdict=UNPROVEN,
        clone=False,
        marker=True,
    ),
    # THE IMPOSTOR. It wears the exact name all four shipped copies of the
    # idiom are spelled with, over a body that forwards the caught exception
    # unchanged. A predicate that recognised the NAME would clear it; this one
    # reports it as a leak. Half of the acceptance's "rather than any name it
    # is spelled with" is discharged here and the other half by
    # ``test_renaming_the_callee_changes_no_verdict``.
    _CloneShape(
        label="impostor_named_clone",
        callee="def _pathless_cause(e):\n    return e\n",
        slot="raise Wrapped('failed') from _pathless_cause(exc)",
        verdict=MEASURED_LEAK,
        clone=False,
        marker=True,
    ),
)

#: The six shapes limit 10 enumerates as escaping the forwarding rule. NAMED
#: rather than counted, so deleting one breaks an arm instead of shrinking a
#: number nobody reads. The acceptance for CS-884 requires each to be REFUSED
#: the new clearance, proven per shape.
_LIMIT_TEN_ESCAPES: Final = (
    "keyword_call_site",
    "lambda_callee",
    "dotted_callee",
    "two_step_forward",
    "conditional_return",
    "container_return",
)

#: The rows the new clearance must reach. Asserted rather than counted for the
#: same reason.
_CLEARED_SHAPES: Final = ("explicit_canonical", "suppressed_canonical")

#: The rows REFUSED because the shape genuinely leaks: the caught exception, or
#: a value carrying the marker, reaches the rendered chain. Every one is
#: measured to render.
_LEAKING_REFUSALS: Final = (
    "control_raw_binding",
    "implicit_canonical",
    "noop_forward",
    "arbitrary_strerror",
    "four_positional_args",
    "keyword_construction",
    "one_bad_return",
    "filename_field",
    "different_object",
    "async_callee",
    "rebound_parameter",
    "mixed_keyword_construction",
    "impostor_named_clone",
    *_LIMIT_TEN_ESCAPES,
)

#: The rows REFUSED although the shape does NOT leak. THIS POPULATION IS NAMED
#: RATHER THAN HIDDEN, and it is the honest half of the CS-884 report. Two
#: kinds sit here. An UNDER-report: the shape is safe and this module cannot
#: prove it - a callee with no return, a decorated one, a builtin that is not
#: an OSError, a one-argument construction. And an OVER-report: the leak leg
#: fires on a shape execution shows to be clean, because a nested or an earlier
#: same-named ``def`` put the name in the forwarding map. Neither is a false
#: clearance, which is the only direction that would be a defect - and saying
#: "every refused shape leaks" would have been false of six of them.
_CLEAN_REFUSALS: Final = (
    "no_return_callee",
    "decorated_callee",
    "redefined_callee",
    "not_an_oserror",
    "single_argument",
    "three_clone_field_args",
    "nested_shadow_forwarder",
)


def _shape(label: str) -> _CloneShape:
    """Look one row up by label.

    Args:
        label: The row's label.

    Returns:
        The row.
    """
    found = {row.label: row for row in _CLONE_SHAPES}
    assert label in found, f"{label} is not a planted CS-884 shape; there are {sorted(found)}"
    return found[label]


@pytest.fixture(scope="module")
def clone_renderings(tmp_path_factory: pytest.TempPathFactory) -> dict[str, _ChildChain]:
    """Run every CS-884 plant in a child and reduce each stderr to scalars.

    MODULE SCOPED so the children run once. Each child DIES from its plant, so
    what is read is the interpreter's own default excepthook rather than
    anything this module formatted - which is exactly the independence the
    cross-check needs.

    Args:
        tmp_path_factory: Where the child scripts are written.

    Returns:
        Label to rendering. The stderr itself is discarded here.
    """
    room = tmp_path_factory.mktemp("cs884")
    rendered: dict[str, _ChildChain] = {}
    for shape in _CLONE_SHAPES:
        child = room / f"clone_{shape.label}.py"
        child.write_text(_clone_plant(shape), encoding="utf-8")
        finished = subprocess.run(
            [sys.executable, "-I", str(child)],
            capture_output=True,
            text=True,
            timeout=_CLONE_CHILD_TIMEOUT,
            check=False,
        )
        written = finished.stderr
        rendered[shape.label] = _ChildChain(
            exit_code=finished.returncode,
            marker_rendered=CLONE_MARKER in written,
            tracebacks=written.count(_TRACEBACK_HEADER),
            construction_failed=_CONSTRUCTION_FAILURE in written,
        )
    return rendered


@pytest.mark.parametrize("shape", _CLONE_SHAPES, ids=[row.label for row in _CLONE_SHAPES])
def test_each_clone_shape_is_graded_on_its_own_arm(shape: _CloneShape) -> None:
    """THE STATIC HALF. One planted shape, one arm, one verdict."""
    site = _clone_site(shape)
    assert site.constructs_pathless_clone is shape.clone, (
        f"{shape.label}: the pathless predicate answered "
        f"{site.constructs_pathless_clone}, expected {shape.clone}"
    )
    assert classify(site) == shape.verdict, (
        f"{shape.label} graded {classify(site)}, expected {shape.verdict}"
    )


@pytest.mark.parametrize("shape", _CLONE_SHAPES, ids=[row.label for row in _CLONE_SHAPES])
def test_each_clone_shape_renders_or_does_not_in_a_real_interpreter(
    shape: _CloneShape, clone_renderings: dict[str, _ChildChain]
) -> None:
    """THE EXECUTION HALF, and it is the one that breaks the common mode.

    The census is the tree's only enumerator of this population, so a bug in
    its clearance would forgive real leaks unnoticed. This arm asks CPython
    instead: the plant runs to a failure and the DEFAULT excepthook renders it.
    """
    seen = clone_renderings[shape.label]
    assert seen.exit_code != 0, (
        f"{shape.label}: the child exited zero, so nothing was rendered and "
        "this arm measured no traceback at all"
    )
    assert seen.tracebacks >= _ONE_TRACEBACK, (
        f"{shape.label}: the child printed {seen.tracebacks} traceback(s), so "
        "it failed somewhere the excepthook never reached"
    )
    assert seen.marker_rendered is shape.marker, (
        f"{shape.label}: the marker rendered={seen.marker_rendered} in the "
        f"default traceback, expected {shape.marker}"
    )


def test_the_marker_is_one_that_would_render_if_it_were_there(
    clone_renderings: dict[str, _ChildChain],
) -> None:
    """THE KNOWN-GOOD CONTROL. Every marker-absent verdict rests on this.

    ``explicit_canonical`` proves nothing on its own: a marker that never
    renders under ANY shape would satisfy it, and so would a plant that failed
    before it reached the raise. ``control_raw_binding`` is the SAME plant with
    the SAME wrapper, differing only in what sits in the cause slot, and it
    renders. The pair is the measurement; either alone is not.
    """
    control = clone_renderings["control_raw_binding"]
    cleared = clone_renderings["explicit_canonical"]
    assert control.marker_rendered is True, (
        "the control did not render the marker, so every marker-absent arm in "
        "this block is measuring a marker that never shows up at all"
    )
    assert cleared.marker_rendered is False, (
        "the cleared shape rendered the marker the control was built to prove "
        "visible, so the clearance is false"
    )
    assert control.exit_code != 0, "the control did not fail"
    assert cleared.exit_code != 0, "the cleared plant did not fail"


def test_the_control_and_the_cleared_plant_differ_only_in_the_cause_slot() -> None:
    """THE CONTROL IS A CONTROL, and this is what makes that a fact.

    A control that differed from its subject in two places would measure two
    things at once. The two plants are diffed as text so the claim is derived
    rather than asserted in prose.
    """
    cleared = _shape("explicit_canonical")
    control = _shape("control_raw_binding")
    assert cleared.callee == control.callee, "the two plants do not share a callee"
    cleared_lines = _clone_plant(cleared).splitlines()
    control_lines = _clone_plant(control).splitlines()
    assert len(cleared_lines) == len(control_lines), "the two plants are different lengths"
    differing = [index for index, line in enumerate(cleared_lines) if line != control_lines[index]]
    assert len(differing) == _ONE_DIFFERENCE, (
        f"the control differs from the cleared plant on {len(differing)} lines, "
        "so it is not a control for the cause slot alone"
    )
    assert cleared_lines[differing[0]].strip() == cleared.slot


@pytest.mark.parametrize("label", _CLEARED_SHAPES)
def test_each_cleared_slot_is_cleared_and_renders_nothing(
    label: str, clone_renderings: dict[str, _ChildChain]
) -> None:
    """BOTH REPAIR SHAPES, ONE ARM EACH, AND BOTH HALVES ON THE SAME ARM.

    CS-884 rules on two shapes and clears both. The clone in the CAUSE slot -
    ``raise Local(...) from clone(exc)`` - is the shape six shipped sites
    write; ``raise X from Y`` sets ``__suppress_context__``, so the caught
    original is not printed underneath either, which is measured here and not
    reasoned about. The clone as the RAISED expression under ``from None`` is
    the shape two shipped sites write, and the context is suppressed outright.
    Neither rests on the callee's NAME.
    """
    site = _clone_site(_shape(label))
    assert classify(site) == CLOSED_PATHLESS, f"{label} did not reach the clearance"
    assert clone_renderings[label].marker_rendered is False, (
        f"{label} is cleared by the census and renders the marker in a real "
        "interpreter, which is a false clearance"
    )
    assert clone_renderings[label].tracebacks == _ONE_TRACEBACK, (
        f"{label} rendered more than one exception, so a chain this module "
        "believed suppressed was printed after all"
    )


@pytest.mark.parametrize("label", _LIMIT_TEN_ESCAPES)
def test_each_limit_ten_escape_is_still_refused_the_clearance(
    label: str, clone_renderings: dict[str, _ChildChain]
) -> None:
    """PROVEN PER SHAPE, which is the acceptance's own wording.

    Limit 10 names six shapes that escape the forwarding rule and grade
    ``unproven``. CS-884 must not clear any of them: each still forwards the
    caught exception unchanged, and each is measured here to render the marker.
    A pooled count over the six would be met by whichever one happened to be
    refused while another was quietly cleared.
    """
    site = _clone_site(_shape(label))
    assert site.constructs_pathless_clone is False, (
        f"{label} was read as constructing a pathless clone; it forwards the "
        "caught exception unchanged"
    )
    assert classify(site) == UNPROVEN, f"{label} graded {classify(site)}, expected unproven"
    assert clone_renderings[label].marker_rendered is True, (
        f"{label} did not render the marker, so this arm proved nothing about "
        "an escape it is supposed to measure leaking"
    )


#: The rename applied to the canonical shape. A string nothing in the tree is
#: spelled with, so the renamed plant cannot accidentally resolve to anything.
_RENAMED_CALLEE: Final = "zqx884_clone"


def test_renaming_the_callee_changes_no_verdict() -> None:
    """THE ACCEPTANCE'S OWN CLAUSE - "rather than any name it is spelled with".

    APPLIED MECHANICALLY RATHER THAN TRANSCRIBED. A second hand-written plant
    could differ from the first in ways nobody noticed; renaming the callee in
    the canonical plant and asserting the verdict is unchanged is a proof about
    the RENAME. Together with ``impostor_named_clone`` - the shipped name over
    a forwarding body, reported as a leak - the clearance is shown to move with
    what the callee builds and not at all with what it is called.

    ``memory/a-guard-can-measure-spelling.md`` records the round of this item
    that gated a clearance on a spelling and lost fifteen escapes to it.
    """
    canonical = _shape("explicit_canonical")
    renamed = _CloneShape(
        label=canonical.label,
        callee=canonical.callee.replace("def c(", f"def {_RENAMED_CALLEE}("),
        slot=canonical.slot.replace("from c(", f"from {_RENAMED_CALLEE}("),
        verdict=canonical.verdict,
        clone=canonical.clone,
        marker=canonical.marker,
    )
    assert renamed.callee != canonical.callee, "the rename did not reach the callee"
    assert renamed.slot != canonical.slot, "the rename did not reach the call site"
    plain = _clone_site(canonical)
    moved = _clone_site(renamed)
    assert moved.raised == plain.raised, "the rename changed what is raised, so it changed more"
    assert moved.cause_expr != plain.cause_expr, "the cause expression did not change"
    assert moved.constructs_pathless_clone is plain.constructs_pathless_clone
    assert classify(moved) == classify(plain) == CLOSED_PATHLESS, (
        "renaming the callee changed the verdict, so the clearance is reading a "
        "spelling rather than what the callee constructs"
    )


def test_the_shipped_name_over_a_forwarding_body_is_not_cleared() -> None:
    """THE OTHER HALF, AND THE ONE A SPELLING GATE WOULD FAIL.

    ``impostor_named_clone`` is spelled exactly as all four shipped copies of
    the idiom are, and returns its argument unchanged. A predicate keyed on the
    name would clear it; this one reports it as a measured leak, and a child
    interpreter renders the marker to prove the report right.
    """
    site = _clone_site(_shape("impostor_named_clone"))
    assert site.constructs_pathless_clone is False, (
        "a callee wearing the shipped name was read as constructing a clone "
        "while returning its argument unchanged"
    )
    assert classify(site) != CLOSED_PATHLESS, "the impostor reached the clearance"


@pytest.mark.parametrize("label", _LEAKING_REFUSALS)
def test_each_leaking_refusal_is_refused_and_measured_to_leak(
    label: str, clone_renderings: dict[str, _ChildChain]
) -> None:
    """ONE ARM PER SHAPE THAT IS REFUSED BECAUSE IT ACTUALLY LEAKS.

    This is the population the clearance must never grow to cover: each of
    these puts the caught exception, or a value carrying the marker, into the
    rendered chain, and each is measured doing it in a child interpreter.
    """
    site = _clone_site(_shape(label))
    assert site.constructs_pathless_clone is False, (
        f"{label} was read as constructing a pathless clone and it leaks"
    )
    assert classify(site) != CLOSED_PATHLESS, f"{label} reached the clearance and it leaks"
    assert clone_renderings[label].marker_rendered is True, (
        f"{label} did not render the marker, so it is not the leaking shape "
        "this arm claims it is and the table is stale"
    )


@pytest.mark.parametrize("label", _CLEAN_REFUSALS)
def test_each_clean_refusal_is_refused_although_it_does_not_leak(
    label: str, clone_renderings: dict[str, _ChildChain]
) -> None:
    """ONE ARM PER SHAPE REFUSED WITHOUT LEAKING, WHICH IS THE HONEST HALF.

    Saying "every refused shape leaks" would be a claim about this table that
    is false of six of its rows. Each of these is safe at runtime and refused
    anyway - four because this module cannot prove them, two because the leak
    leg fires on evidence execution contradicts. Both are the fail-closed
    direction and neither is a clearance, which is what makes them acceptable
    and what makes stating them mandatory.
    """
    site = _clone_site(_shape(label))
    assert classify(site) != CLOSED_PATHLESS, f"{label} reached the clearance"
    assert clone_renderings[label].marker_rendered is False, (
        f"{label} rendered the marker, so it belongs in the leaking population "
        "and this arm is measuring the wrong thing about it"
    )


def test_neither_refusal_population_is_empty_and_together_they_are_the_table() -> None:
    """A PARTITION, ASSERTED. Neither half may quietly become a zero.

    An empty leaking half would mean no arm above measures a real escape; an
    empty clean half would mean the honest disclosure has nothing behind it.
    And a row in neither half is a row whose execution nobody decided about,
    which is the hole a catch-all always leaves.
    """
    assert _LEAKING_REFUSALS, "no refused shape is measured to leak"
    assert _CLEAN_REFUSALS, "no refused shape is recorded as a conservative refusal"
    overlap = set(_LEAKING_REFUSALS) & set(_CLEAN_REFUSALS)
    assert not overlap, f"a shape is in both refusal populations: {sorted(overlap)}"
    decided = set(_LEAKING_REFUSALS) | set(_CLEAN_REFUSALS) | set(_CLEARED_SHAPES)
    planted = {row.label for row in _CLONE_SHAPES}
    assert decided == planted, (
        f"the populations and the table disagree; only in the table "
        f"{sorted(planted - decided)}, only in a population {sorted(decided - planted)}"
    )


def test_the_keyword_construction_cannot_be_built_at_all(
    clone_renderings: dict[str, _ChildChain],
) -> None:
    """THE ONE REFUSED SHAPE WHOSE EXECUTION SAYS SOMETHING ELSE, SAID PLAINLY.

    ``OSError`` takes no keyword arguments. The keyword spelling of the clone
    therefore does not construct a safe object that this module declines to
    recognise - it raises ``TypeError`` at the raise statement, and the caught
    original renders as that failure's own context. So it is refused twice, for
    two different reasons, and only the static one is about the predicate.

    RECORDED HERE RATHER THAN LEFT IMPLIED, because a plant that KILLS instead
    of DEGRADING is the shape that quietly turns a coverage claim into nothing:
    the shape stops exercising the field it was planted for, the arm goes green
    on a different failure, and only the arm's own prose would ever say so. The
    marker still renders on this one, so the row belongs in
    :data:`_LEAKING_REFUSALS` - but for the interpreter's reason and not for
    the predicate's, and that distinction is what this arm exists to keep.
    """
    seen = clone_renderings["keyword_construction"]
    assert seen.construction_failed is True, (
        "the keyword construction did not fail, so this arm's stated reason for "
        "the shape being refused is no longer what the interpreter does"
    )
    assert seen.marker_rendered is True


def test_the_implicit_form_is_never_cleared_however_good_the_clone(
    clone_renderings: dict[str, _ChildChain],
) -> None:
    """A PERFECT CLONE WITH NO ``from`` CLAUSE STILL LEAKS.

    ``raise clone(exc)`` inside a handler leaves ``__context__`` pointing at
    the caught original, which the formatter prints in full underneath "During
    handling of the above exception" - both filename fields intact, on an
    exception whose own are empty. ``scripts/make_cert.py`` records having
    measured that before its sites were written; this re-measures it, and it is
    why :func:`chained_cause_guard._constructs_pathless_clone` reads only two
    of the four forms.
    """
    site = _clone_site(_shape("implicit_canonical"))
    assert site.form == FORM_IMPLICIT
    assert site.constructs_pathless_clone is False, (
        "the implicit form was read as a cleared slot, and it is the one shape "
        "where a perfect clone changes nothing"
    )
    seen = clone_renderings["implicit_canonical"]
    assert seen.marker_rendered is True, "the implicit form did not leak, so this arm is stale"
    assert seen.tracebacks > _ONE_TRACEBACK, (
        "only one exception rendered, so the context this arm is about was not "
        "printed and the measurement is about something else"
    )


# ---------------------------------------------------------------------------
# CS-884 - VERDICT_ORDER. A positive verdict placed ahead of a leak LAUNDERS
# it, and the two predicates collide on a shape the tree could grow tomorrow.
# ---------------------------------------------------------------------------


def _applicable_verdicts(site: Site, exempt: Mapping[str, str]) -> tuple[str, ...]:
    """Every verdict whose CONDITION holds, computed without consulting order.

    DELIBERATELY A SECOND SPELLING OF :func:`classify`'s branch conditions, and
    that is what makes it evidence. Reading the verdict back out of
    ``classify`` and comparing it to ``classify`` proves nothing about
    precedence; deciding applicability independently and then asking whether
    the published order picks the same winner does. A drift between this copy
    and the real conditions is caught by the per-shape arms above, which grade
    ``classify`` and never this.

    Args:
        site: The site.
        exempt: The exemption record to consult.

    Returns:
        The applicable verdicts, ordered by :data:`VERDICT_ORDER`.
    """
    holds = [UNPROVEN]
    if site.cause_type == TYPE_OSERROR:
        holds.append(MEASURED_LEAK)
    if site.form == FORM_SUPPRESSED and site.raises_local_class:
        holds.append(CLOSED_SUPPRESSED)
    if site.constructs_pathless_clone:
        holds.append(CLOSED_PATHLESS)
    if site.key in exempt:
        holds.append(EXEMPT_RECORDED)
    return tuple(sorted(holds, key=VERDICT_ORDER.index))


def test_the_new_verdict_is_tested_after_the_measured_leak_on_a_real_collision() -> None:
    """THE ORDER ARM, AND IT IS NOT VACUOUS.

    ``nested_shadow_forwarder`` defines a module-level clone AND a nested
    function of the same name that forwards its argument. The forwarding map
    walks every scope, so the name is in it; the clone map walks module level,
    so the name is in that too. BOTH conditions hold on one site, which is the
    only thing that makes an ordering question answerable rather than
    hypothetical - an order arm over a site where one branch cannot apply is
    the empty-population defect wearing a different hat.
    """
    site = _clone_site(_shape("nested_shadow_forwarder"))
    assert site.cause_type == TYPE_OSERROR, "the leak leg does not apply, so nothing collides"
    assert site.constructs_pathless_clone is True, (
        "the clearance leg does not apply, so this arm is not measuring a collision"
    )
    applicable = _applicable_verdicts(site, {})
    assert len(applicable) > _ONE_VERDICT, (
        f"only {applicable} applies, so there is no precedence to test here"
    )
    assert applicable[0] == MEASURED_LEAK, "VERDICT_ORDER no longer puts the leak first"
    assert classify(site) == MEASURED_LEAK, (
        "a site where both the leak leg and the clearance leg apply was CLEARED, "
        "so the new verdict is laundering a measured leak"
    )


def test_the_collision_shape_is_an_over_report_and_says_so(
    clone_renderings: dict[str, _ChildChain],
) -> None:
    """WHAT THE ORDERING COSTS, MEASURED RATHER THAN ASSUMED.

    On the collision shape the module-level clone is the function actually
    called, so the child renders no marker. The census reports a leak anyway.
    That is a proxy-positive of exactly the kind limit 5 already names, and the
    honest statement is that the ordering buys safety at the price of this
    over-report - not that the shape leaks.
    """
    seen = clone_renderings["nested_shadow_forwarder"]
    assert seen.marker_rendered is False, (
        "the collision shape rendered the marker, so it is a real leak rather "
        "than the over-report this arm documents, and the docstring is stale"
    )
    assert seen.exit_code != 0


@pytest.mark.parametrize("site", _graded_sites(), ids=lambda site: site.key)
def test_classify_takes_the_first_applicable_verdict_for_every_graded_site(site: Site) -> None:
    """ONE ARM PER LIVE MEMBER over the same independent applicability rule.

    The planted collision proves the order holds where the branches fight. This
    proves the published order and the implemented order agree on every site
    the tree actually contains, so a future reordering of :func:`classify`'s
    branches alone reddens here.
    """
    assert classify(site) == _applicable_verdicts(site, EXEMPT)[0], (
        f"{site.key} takes {classify(site)} while the first applicable verdict "
        f"in VERDICT_ORDER is {_applicable_verdicts(site, EXEMPT)[0]}"
    )


@pytest.mark.parametrize("site", _graded_sites(), ids=lambda site: site.key)
def test_no_graded_site_is_cleared_pathless_without_constructing_one(site: Site) -> None:
    """INVARIANT 3, FOR THE SECOND CLEARANCE. ASSERTED AS A BICONDITIONAL.

    Every graded site takes one branch or the other, so a change that stopped
    ANY site reaching the new verdict cannot leave every member in an empty
    branch with the arm still green - the defect
    ``memory/an-empty-population-satisfies-every-zero.md`` records, which this
    module has already reproduced once inside an arm named after it.
    """
    outranked = site.cause_type == TYPE_OSERROR or (
        site.form == FORM_SUPPRESSED and site.raises_local_class
    )
    if site.constructs_pathless_clone and not outranked:
        assert classify(site) == CLOSED_PATHLESS, (
            f"{site.key} calls a same-module function whose every return builds "
            "a filename-free OSError, and was not cleared by it"
        )
        assert site.form in (FORM_EXPLICIT, FORM_SUPPRESSED), (
            f"{site.key} was cleared on a form that has no cause slot to clear"
        )
    else:
        assert classify(site) != CLOSED_PATHLESS, (
            f"{site.key} was cleared without constructing a pathless clone, so "
            "something other than what the callee BUILDS issued a clearance"
        )


def test_both_slots_of_the_pathless_clearance_have_a_live_member() -> None:
    """A BRANCH WITH NO MEMBER IS A BRANCH NOBODY MEASURED.

    CS-884 rules on two slots and the live tree carries both: the clone in the
    cause slot of an explicit chain, and the clone as the raised expression of
    a ``from None``. SKIPS rather than fails when the tree stops carrying one,
    because an arm that reddens the moment a site is repaired is
    anti-correlated with success.
    """
    cleared = [site for site in _graded_sites() if classify(site) == CLOSED_PATHLESS]
    explicit = [site for site in cleared if site.form == FORM_EXPLICIT]
    suppressed = [site for site in cleared if site.form == FORM_SUPPRESSED]
    if not explicit or not suppressed:
        pytest.skip(
            f"{len(explicit)} explicit and {len(suppressed)} suppressed pathless "
            "clearances live this run, so a slot has no live member"
        )
    assert {site.form for site in cleared} == {FORM_EXPLICIT, FORM_SUPPRESSED}
    assert all(site.constructs_pathless_clone for site in cleared)


def test_the_two_clearances_are_disjoint_by_construction() -> None:
    """NEITHER CLEARANCE CAN EVER STAND IN FOR THE OTHER.

    :attr:`Site.raises_local_class` reads names a ``ClassDef`` declares;
    :func:`chained_cause_guard._pathless_clone_functions` reads module-level
    ``def`` names and subtracts every name bound at module level by anything
    else - a ``class`` included. So a name cannot be in both maps, and the
    precedence between the two positive verdicts can never decide a verdict.
    Planted rather than argued.
    """
    source = (
        '"""A name declared as a class AND as a function."""\n\n\n'
        "def c(e):\n    return OSError(e.errno, e.strerror)\n\n\n"
        "class c:\n"
        '    """The later binding, which is what the name means."""\n\n\n'
        "def site(path):\n"
        "    try:\n"
        "        open(path)\n"
        "    except OSError as exc:\n"
        "        raise c(exc) from None\n"
    )
    derived = {found.qualname: found for found in sites_in_tree({PLANTED_PATH: source})}
    site = derived["site"]
    assert site.raises_local_class is True, "the class declaration was not seen"
    assert site.constructs_pathless_clone is False, (
        "a name bound by a class at module level was still read as a clone "
        "function, so the last binding is not what the clone map resolves"
    )
    assert classify(site) == CLOSED_SUPPRESSED


# ---------------------------------------------------------------------------
# CS-884 - the live layer, and the report that has to name the new verdict.
# ---------------------------------------------------------------------------


def test_the_new_verdict_is_published_in_the_verdict_order() -> None:
    """A VERDICT ABSENT FROM :data:`VERDICT_ORDER` IS ONE NO ARM ENUMERATES."""
    assert CLOSED_PATHLESS in VERDICT_ORDER, "the new verdict is not published"
    assert VERDICT_ORDER.index(MEASURED_LEAK) < VERDICT_ORDER.index(CLOSED_PATHLESS), (
        "a positive verdict is ordered ahead of the measured leak, which "
        "launders every leak the new predicate also matches"
    )
    assert VERDICT_ORDER.index(CLOSED_PATHLESS) < VERDICT_ORDER.index(UNPROVEN)
    assert len(set(VERDICT_ORDER)) == len(VERDICT_ORDER), "a verdict is listed twice"


def test_the_verdict_distribution_names_every_verdict_every_run() -> None:
    """THE REPORTER HANDLES THE NEW VERDICT, and would handle the next one.

    The census reports its findings as a warning rather than a failure. A
    reporter that enumerated verdicts by hand would have gone silent about
    CS-884's the moment it was added, so the distribution is derived from
    :data:`VERDICT_ORDER` and every member is named even at zero - a verdict
    printed only when non-empty cannot be told from one nobody computes.
    """
    lines = verdict_distribution(_graded_sites())
    assert len(lines) == len(VERDICT_ORDER), (
        f"the distribution carries {len(lines)} line(s) for {len(VERDICT_ORDER)} verdicts"
    )
    named = " ".join(lines)
    for verdict in VERDICT_ORDER:
        assert verdict in named, f"the distribution does not name {verdict}"
    assert CLOSED_PATHLESS in named


def test_the_pathless_clearance_has_live_members_and_reports_them() -> None:
    """THE DENOMINATOR FOR THE LIVE HALF, and the report that carries it.

    Every zero below the new verdict would be satisfied by a predicate that
    matched nothing at all, so the live count is asserted non-zero alongside
    the graded population it is drawn from. SKIPS rather than fails if the tree
    ever stops carrying the idiom, for the anti-correlation reason above.
    """
    graded = _graded_sites()
    assert graded, "the graded population is empty, so this arm measured nothing"
    cleared = [site for site in graded if classify(site) == CLOSED_PATHLESS]
    if not cleared:
        pytest.skip("no live site reaches the pathless clearance this run")
    body = "\n".join(f"  {site.key} line {site.lineno}" for site in cleared)
    warnings.warn(
        f"CS-857 {CLOSED_PATHLESS}, {len(cleared)} of {len(graded)} chained "
        f"raise(s) in the {BUCKET_GRADED} bucket chain a clone the callee "
        f"CONSTRUCTS from errno and strerror alone:\n{body}",
        stacklevel=1,
    )


# ---------------------------------------------------------------------------
# CS-881 - THE DEFERRED RAISE. The SECOND known way out of the ``Site``
# population altogether, and unlike limit 8 it needs no second function.
#
# THE SHAPE. A handler stores its OWN binding into a local - ``last = exc`` -
# and the raise happens AFTER the handler has exited: outside every handler,
# with no ``from`` clause. ``chained_cause_guard._form_of`` answers None for
# it, nothing enters :class:`Site`, and every counts-only arm over that
# population reads a zero it did not earn -
# ``memory/an-empty-population-satisfies-every-zero.md``. The RENDERING is a
# graded site's: the stored object IS the caught ``OSError``, so its ``str()``
# still appends ``filename`` - MEASURED here in this process, and again by a
# child interpreter's own excepthook.
#
# THE SPELLING TRAP IS THE ITEM. The two live sites in the graded bucket do
# not share a raised-expression KIND: one raises a bare ``ast.Name`` and one
# raises an ``ast.IfExp``. A leg keyed on ``raise <Name>`` derives the first
# and is silent about the second - a spelling silence inside the item filed
# against a spelling silence, which ``memory/a-guard-can-measure-spelling.md``
# records the first round of. The derivation therefore keys on the POSITIVE
# fact, that the raised expression READS a name a handler in the same scope
# stored, and reads nothing at all about the raise node's kind. Both spellings
# are planted and each gets its own arm, because a pooled arm over the table
# would be met by whichever member happened to be strongest.
# ---------------------------------------------------------------------------

#: The CS-881 payload. A THIRD marker, distinct from :data:`MARKER` and from
#: :data:`CLONE_MARKER` for the reason that one is distinct from the first: two
#: instruments sharing a marker cannot tell a leak in one from a leak in the
#: other. Not a path, not personal data, not derived from any machine.
DEFERRED_MARKER: Final = "CS881-SYNTHETIC-MARKER"

#: A planted module in the GRADED bucket. Never touched on disk - every
#: derivation entry point reads a mapping, so this is a key and not a file.
PLANTED_DEFERRED_PATH: Final = "tools/planted_deferred.py"

#: How many times the live fixtures below go round their retry loop. Named so
#: no bare number sits in the fixture, and small because the loop is the SHAPE
#: rather than a timing test.
_DEFERRED_ATTEMPTS: Final = 2

#: Exactly one derived record, named so no bare number sits in a comparison.
_ONE_DEFERRED: Final = 1

#: The live fixture functions this module contributes to the sweep, by the
#: qualname the derivation reports for each. THE LIVE POSITIVE CONTROL: the
#: shipped sites may be repaired at any time and these cannot, because this
#: module owns them.
#:
#: THE THIRD ONE EXERCISES A DIFFERENT BRANCH OF THE STORE WALK, which is the
#: only reason it is here rather than being a fourth planted string. The first
#: two store through ``ast.Assign``; CS-881 residual 2 widened
#: :func:`chained_cause_guard._stored_binding` to four more statement forms,
#: and without a live fixture the widened branch would be proven over a mapping
#: and never over the git sweep the guard actually reads.
_LIVE_DEFERRED_FIXTURES: Final = (
    "_deferred_bare_name_raise",
    "_deferred_conditional_raise",
    "_deferred_annotated_store_raise",
)


def _deferred_bare_name_raise() -> None:
    """Store the handler's binding, then raise it after the handler exits.

    THE SPELLING THE SHIPPED RETRY LOOP IN ``clockspeed/save/workdir.py``
    USES. A real raise, so the LIVE git sweep derives it and the derivation is
    proven against the tree rather than only against a string.

    Raises:
        OSError: Always, carrying :data:`DEFERRED_MARKER` as its filename.
    """
    last: OSError | None = None
    for _attempt in range(_DEFERRED_ATTEMPTS):
        try:
            raise OSError(_ERRNO, _STRERROR, DEFERRED_MARKER)
        except OSError as exc:
            last = exc
    if last is None:
        last = OSError("nothing was recorded")
    raise last


def _deferred_conditional_raise() -> None:
    """The same shape, raised through an ``ast.IfExp`` rather than a name.

    THE SPELLING ``clockspeed/data/version.py`` USES, and the one a leg keyed
    on ``raise <Name>`` would be silent about.

    Raises:
        OSError: Always, carrying :data:`DEFERRED_MARKER` as its filename.
    """
    last: OSError | None = None
    for _attempt in range(_DEFERRED_ATTEMPTS):
        try:
            raise OSError(_ERRNO, _STRERROR, DEFERRED_MARKER)
        except OSError as exc:
            last = exc
    raise last if last is not None else OSError("nothing was recorded")


def _deferred_annotated_store_raise() -> None:
    """The same shape with the store ANNOTATED rather than plain.

    THE SPELLING THAT ESCAPED THE WALK ENTIRELY UNTIL CS-881 RESIDUAL 2. It is
    an ``ast.AnnAssign`` whose target IS a bare name, so the refusal that used
    to cover it - "target is not a bare name" - was false of it, and in a tree
    this heavily annotated it is ordinary house style rather than an
    adversarial spelling. A real raise, so the LIVE git sweep must derive it.

    Raises:
        OSError: Always, carrying :data:`DEFERRED_MARKER` as its filename.
    """
    for _attempt in range(_DEFERRED_ATTEMPTS):
        try:
            raise OSError(_ERRNO, _STRERROR, DEFERRED_MARKER)
        except OSError as exc:
            last: OSError = exc
    raise last


@pytest.mark.parametrize(
    ("label", "fixture"),
    [
        ("bare-name", _deferred_bare_name_raise),
        ("conditional", _deferred_conditional_raise),
        ("annotated-store", _deferred_annotated_store_raise),
    ],
)
def test_a_deferred_raise_renders_the_caught_value_with_no_chain_at_all(
    label: str, fixture: Callable[[], None]
) -> None:
    """CS-881 THE MEASUREMENT, and it is what makes the rest of this facts.

    The stored object IS the caught ``OSError``, so ``OSError.__str__``
    appends the ``filename`` the interpreter attached. And the chain is ONE
    link: the handler has exited, so there is no ``__context__`` and no
    ``__cause__`` for a chain walk to follow. That is the whole reason the
    chained-cause census cannot see the shape while the rendering is identical
    to a graded site's.
    """
    with pytest.raises(OSError, match=DEFERRED_MARKER) as caught:
        fixture()
    chain = _chain_of(caught.value)
    rendered = _rendered_chain(caught.value)
    assert len(chain) == _UNCHAINED, (
        f"{label}: the deferred raise chained {len(chain)} link(s); a chain "
        "would mean this shape is visible to a cause walk after all"
    )
    assert DEFERRED_MARKER in rendered, (
        f"{label}: the caught value's filename did not reach the rendering, "
        "so this shape is not the leak the item is about"
    )


# ---------------------------------------------------------------------------
# THE PLANTED TABLE. Each row is assembled MECHANICALLY from three source
# fields, so no row is a transcription of another, and each is graded twice:
# statically by the derivation, and by a CHILD INTERPRETER whose default
# excepthook renders the plant. The census is the tree's only enumerator of
# this population, so a second static reader here would be wrong the same way
# the first one is.
#
# THE CHILD'S STDERR NEVER BECOMES A FIELD, A MESSAGE OR A LOCAL. It carries an
# absolute frame path per stack level, so it is reduced to booleans and counts
# the moment it is read - CLAUDE.md non-negotiable 12.
# ---------------------------------------------------------------------------

#: Everything every CS-881 plant shares. THE MARKER APPEARS IN NO LINE A
#: TRACEBACK CAN PRINT, for the reason :data:`_CLONE_PLANT_HEAD` records: a
#: traceback echoes the SOURCE of every frame, so a marker written as a literal
#: inside a function would render through the source-echo channel and every
#: marker-present arm would pass without measuring an exception at all.
_DEFERRED_PLANT_HEAD: Final = f'''"""One CS-881 shape, runnable and derivable from the same text."""

_MARKER = "{DEFERRED_MARKER}"
_ERRNO = 13
_STRERROR = "Permission denied"
_LEAK_PATH = "dir/" + _MARKER + "/file"
_ATTEMPTS = 2


class Wrapped(Exception):
    """The wrapper. Its own message carries nothing."""


class Holder:
    """A settable ATTRIBUTE target, so a store into one is RUN and not only refused."""


def _fail():
    """Raise an OSError whose filename is the field OSError.__str__ appends."""
    raise OSError(_ERRNO, _STRERROR, _LEAK_PATH)


'''


@dataclass(frozen=True)
class _DeferredShape:
    """One CS-881 plant, derived statically and run in a child.

    Attributes:
        label: The arm id, and the child script's basename.
        setup: Lines at the top of the site function, indented for it.
        store: Lines inside the handler body, indented for it.
        raised: The raise statement, indented for the site function.
        derived: Whether the deferred population must derive a record.
        marker: Whether :data:`DEFERRED_MARKER` must reach the child's stderr.
    """

    label: str
    setup: str
    store: str
    raised: str
    derived: bool
    marker: bool


def _deferred_plant(shape: _DeferredShape) -> str:
    """Assemble one plant from its three source fields.

    Args:
        shape: The row to build.

    Returns:
        A module that both derives and runs to a failure.
    """
    return (
        _DEFERRED_PLANT_HEAD
        + "def site():\n"
        + '    """The censused site."""\n'
        + f"{shape.setup}\n"
        + "    for _attempt in range(_ATTEMPTS):\n"
        + "        try:\n"
        + "            _fail()\n"
        + "        except OSError as exc:\n"
        + f"{shape.store}\n"
        + f"{shape.raised}\n"
        + "\n\nsite()\n"
    )


#: The store the two shipped sites and most of this table share.
_STORE_THE_BINDING: Final = "            last = exc"

#: ONE ROW PER SHAPE. The ``derived`` and ``marker`` columns are INDEPENDENT
#: and neither is computed from the other, which is the point of carrying both:
#: one row is derived and does not leak, and two rows leak and are not derived.
#: Both directions are partitioned below and asserted separately, because a
#: table that could show only one of them would be a table about nothing.
_DEFERRED_SHAPES: Final = (
    _DeferredShape(
        label="bare_name",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    raise last",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="conditional",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    raise last if last is not None else OSError(_ERRNO, _STRERROR)",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="or_default",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    raise last or OSError(_ERRNO, _STRERROR)",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="wrapped_argument",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    raise Wrapped(last)",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="field_read_only",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    raise OSError(last.errno, last.strerror)",
        derived=True,
        marker=False,
    ),
    _DeferredShape(
        label="a_fresh_error",
        setup="    last = None",
        store="            last = OSError(_ERRNO, _STRERROR)",
        raised="    raise last",
        derived=False,
        marker=False,
    ),
    _DeferredShape(
        label="nothing_stored",
        setup="    last = None",
        store="            pass",
        raised="    raise OSError(_ERRNO, _STRERROR)",
        derived=False,
        marker=False,
    ),
    _DeferredShape(
        label="two_step_store",
        setup="    last = None",
        store="            kept = exc\n            last = kept",
        raised="    raise last",
        derived=False,
        marker=True,
    ),
    _DeferredShape(
        label="container_store",
        setup="    held = []",
        store="            held.append(exc)",
        raised="    raise held[0]",
        derived=False,
        marker=True,
    ),
    # ----------------------------------------------------------------------
    # CS-881 residual 2. FOUR STORE SPELLINGS THAT ARE NOT ``ast.Assign``.
    # Every one binds a BARE LOCAL, in the SAME scope, to the handler's own
    # binding - which is the POSITIVE fact DeferredRaiseSite says it keys on -
    # and every one derived ZERO while rendering the marker, measured by two
    # independent agents before this round. The first is ordinary house style
    # in a tree this heavily annotated, which is what makes it the one to read
    # first; the walrus pair and the loop target are what an adversary reaches
    # for once the annotated form is closed.
    # ----------------------------------------------------------------------
    _DeferredShape(
        label="annotated_store",
        setup="    last = None",
        store="            last: OSError | None = exc",
        raised="    raise last",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="walrus_condition",
        setup="    last = None",
        store="            if (last := exc) is not None:\n                pass",
        raised="    raise last",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="walrus_sink",
        setup="    last = None",
        store="            _sink = (last := exc)",
        raised="    raise last",
        derived=True,
        marker=True,
    ),
    _DeferredShape(
        label="loop_target_store",
        setup="    last = None",
        store="            for last in (exc,):\n                pass",
        raised="    raise last",
        derived=True,
        marker=True,
    ),
    # ----------------------------------------------------------------------
    # CS-881 residual 3. THE THREE ROWS THE LIMIT CALLED "refused by
    # construction, NOT MEASURED" WHILE ``_handler_stores``'S OWN TABLE CALLED
    # THE SAME FAMILY "MEASURED to leak". Two tables contradicting each other
    # is worse than either being wrong alone, because a reader who finds one
    # has no reason to look for the other. They are MEASURED here, in a child
    # interpreter, so both tables can say the same measured thing.
    # ----------------------------------------------------------------------
    _DeferredShape(
        label="attribute_store",
        setup="    holder = Holder()",
        store="            holder.last = exc",
        raised="    raise holder.last",
        derived=False,
        marker=True,
    ),
    _DeferredShape(
        label="subscript_store",
        setup="    held = [None]",
        store="            held[0] = exc",
        raised="    raise held[0]",
        derived=False,
        marker=True,
    ),
    _DeferredShape(
        label="cross_scope_store",
        setup="    last = None",
        store=_STORE_THE_BINDING,
        raised="    def _later():\n        raise last\n    _later()",
        derived=False,
        marker=True,
    ),
)

#: The row DERIVED although the shape carries no path. AN OVER-REPORT, named
#: rather than hidden: the raised expression reads a FIELD off the stored
#: exception rather than the exception itself, and the derivation does not
#: model the difference. Between over-reporting a site and going silent about
#: one this population takes the first, which is the trade
#: :data:`VERDICT_ORDER` records one census over.
_DEFERRED_OVER_REPORTS: Final = ("field_read_only",)

#: The rows that LEAK and are NOT derived. AN UNDER-REPORT, and the honest half
#: of the CS-881 report: the store must be the handler's own binding written to
#: a plain local name, so a two-step forward, a store into a container, a store
#: through an attribute or a subscript, and a store the raise cannot reach
#: because it crosses a scope are all silences. Each is planted, run, and
#: MEASURED to render the marker - none is refused on paper alone, which is the
#: CS-881 residual-3 correction: the guard's two tables disagreed about exactly
#: this family, one calling it measured and the other calling it unmeasured.
_DEFERRED_UNDER_REPORTS: Final = (
    "two_step_store",
    "container_store",
    "attribute_store",
    "subscript_store",
    "cross_scope_store",
)

#: Seconds a child may take. Generous: a floor against a hang, not a
#: performance assertion.
_DEFERRED_CHILD_TIMEOUT: Final = 120.0


def _deferred_shape(label: str) -> _DeferredShape:
    """Look one row up by label.

    Args:
        label: The row's label.

    Returns:
        The row.
    """
    found = {row.label: row for row in _DEFERRED_SHAPES}
    assert label in found, f"{label} is not a planted CS-881 shape; there are {sorted(found)}"
    return found[label]


def _deferred_record(shape: _DeferredShape) -> tuple[DeferredRaiseSite, ...]:
    """Derive one plant's deferred population.

    Args:
        shape: The row to derive.

    Returns:
        Every record the plant yields, which is zero or one row.
    """
    return deferred_raise_sites_in_tree({PLANTED_DEFERRED_PATH: _deferred_plant(shape)})


@pytest.fixture(scope="module")
def deferred_renderings(tmp_path_factory: pytest.TempPathFactory) -> dict[str, _ChildChain]:
    """Run every CS-881 plant in a child and reduce each stderr to scalars.

    MODULE SCOPED so the children run once. Each child DIES from its plant, so
    what is read is the interpreter's own default excepthook rather than
    anything this module formatted.

    Args:
        tmp_path_factory: Where the child scripts are written.

    Returns:
        Label to rendering. The stderr itself is discarded here.
    """
    room = tmp_path_factory.mktemp("cs881")
    rendered: dict[str, _ChildChain] = {}
    for shape in _DEFERRED_SHAPES:
        child = room / f"deferred_{shape.label}.py"
        child.write_text(_deferred_plant(shape), encoding="utf-8")
        finished = subprocess.run(
            [sys.executable, "-I", str(child)],
            capture_output=True,
            text=True,
            timeout=_DEFERRED_CHILD_TIMEOUT,
            check=False,
        )
        written = finished.stderr
        rendered[shape.label] = _ChildChain(
            exit_code=finished.returncode,
            marker_rendered=DEFERRED_MARKER in written,
            tracebacks=written.count(_TRACEBACK_HEADER),
            construction_failed=_CONSTRUCTION_FAILURE in written,
        )
    return rendered


@pytest.mark.parametrize("shape", _DEFERRED_SHAPES, ids=[row.label for row in _DEFERRED_SHAPES])
def test_each_deferred_shape_is_derived_or_not_on_its_own_arm(shape: _DeferredShape) -> None:
    """CS-881 THE STATIC HALF. One planted shape, one arm, one answer.

    THE ``conditional`` ROW IS THE ONE TO READ FIRST. Its raised expression is
    an ``ast.IfExp``, so a leg keyed on ``raise <Name>`` answers False here and
    True on ``bare_name`` - and the tracked tree holds one live site of each.
    """
    records = _deferred_record(shape)
    assert (len(records) == _ONE_DEFERRED) is shape.derived, (
        f"{shape.label}: the derivation returned {len(records)} record(s), "
        f"expected derived={shape.derived}"
    )
    if shape.derived:
        assert records[0].qualname == "site", f"{shape.label}: derived the wrong scope"
        assert records[0].stored_type == TYPE_OSERROR, (
            f"{shape.label}: the storing handler's type resolved "
            f"{records[0].stored_type}, so the record says nothing about what renders"
        )


@pytest.mark.parametrize("shape", _DEFERRED_SHAPES, ids=[row.label for row in _DEFERRED_SHAPES])
def test_each_deferred_shape_renders_or_does_not_in_a_real_interpreter(
    shape: _DeferredShape, deferred_renderings: dict[str, _ChildChain]
) -> None:
    """CS-881 THE EXECUTION HALF, and it is what breaks the common mode.

    This module and the guard are one instrument. Asking CPython instead is
    what makes ``derived`` a claim about a real channel rather than a claim
    about the derivation agreeing with itself.
    """
    seen = deferred_renderings[shape.label]
    assert seen.exit_code != 0, (
        f"{shape.label}: the child exited zero, so nothing was rendered and "
        "this arm measured no traceback at all"
    )
    assert seen.tracebacks >= _ONE_TRACEBACK, (
        f"{shape.label}: the child printed {seen.tracebacks} traceback(s), so "
        "it failed somewhere the excepthook never reached"
    )
    assert not seen.construction_failed, (
        f"{shape.label}: the plant failed to CONSTRUCT rather than to raise, "
        "so what rendered is not the shape this row is about"
    )
    assert seen.marker_rendered is shape.marker, (
        f"{shape.label}: the marker rendered={seen.marker_rendered} in the "
        f"default traceback, expected {shape.marker}"
    )


@pytest.mark.parametrize("shape", _DEFERRED_SHAPES, ids=[row.label for row in _DEFERRED_SHAPES])
def test_the_site_population_derives_nothing_for_any_deferred_plant(
    shape: _DeferredShape,
) -> None:
    """CS-881 THE DEFECT, STATED AS AN ARM RATHER THAN AS A SENTENCE.

    Every row above is invisible to :func:`sites_in_tree`, the four that render
    the marker included. That disjointness is what the two populations rest on,
    and it is what an arm counting graded sites was reading a zero about.

    A RED ARM HERE IS NOT A REGRESSION: it means the ``Site`` walk grew to see
    the shape, and the repair is to decide which population owns it rather than
    to let both count it.
    """
    assert sites_in_tree({PLANTED_DEFERRED_PATH: _deferred_plant(shape)}) == (), (
        f"{shape.label}: the Site population now derives this plant, so the "
        "two populations overlap and one raise is counted twice"
    )


def test_the_over_and_under_report_rows_are_both_populated() -> None:
    """CS-881. A TABLE THAT COULD SHOW ONLY ONE DIRECTION SHOWS NEITHER.

    ``derived`` and ``marker`` are carried as independent columns precisely so
    the two honest failures can be seen. If either partition empties, the table
    has stopped being able to express one of them, and the arms above would
    then agree with a derivation that had collapsed into "derived iff leaks".
    """
    by_label = {row.label: row for row in _DEFERRED_SHAPES}
    assert set(_DEFERRED_OVER_REPORTS) <= set(by_label), "an over-report row was renamed away"
    assert set(_DEFERRED_UNDER_REPORTS) <= set(by_label), "an under-report row was renamed away"
    for label in _DEFERRED_OVER_REPORTS:
        assert by_label[label].derived, f"{label} is listed as an over-report and is not derived"
        assert not by_label[label].marker, f"{label} is listed as an over-report and it leaks"
    for label in _DEFERRED_UNDER_REPORTS:
        assert by_label[label].marker, f"{label} is listed as an under-report and does not leak"
        assert not by_label[label].derived, f"{label} is listed as an under-report and is derived"


def test_a_planted_deferred_raise_is_reported_as_a_graded_finding() -> None:
    """CS-881 ACCEPTANCE, THE RED HALF. A planted site makes the guard report.

    The plant sits in the GRADED bucket, so the finding reaches
    :func:`deferred_findings` rather than the out-of-scope record - which is
    the difference between a guard that reports and a guard that files.
    """
    assert bucket_of(PLANTED_DEFERRED_PATH) == BUCKET_GRADED, (
        f"{PLANTED_DEFERRED_PATH} buckets {bucket_of(PLANTED_DEFERRED_PATH)}, "
        f"not {BUCKET_GRADED}, so this arm plants outside the reported population"
    )
    findings = deferred_findings(_deferred_record(_deferred_shape("bare_name")))
    assert len(findings) == _ONE_DEFERRED, f"the plant was not reported: {findings}"
    assert PLANTED_DEFERRED_PATH in findings[0], f"the finding does not name the module: {findings}"


def test_a_tree_without_the_shape_is_reported_clean() -> None:
    """CS-881 ACCEPTANCE, THE GREEN HALF. No plant, no finding.

    The SAME entry point over a module that stores nothing of the handler's
    own. Without it the red arm above is satisfied by a detector that reports
    every raise it sees.
    """
    findings = deferred_findings(_deferred_record(_deferred_shape("nothing_stored")))
    assert findings == (), f"a tree with no deferred raise still reported: {findings}"


# ---------------------------------------------------------------------------
# The live layer. NOTHING HERE ASSERTS A PARTICULAR SHIPPED FINDING: the two
# live sites may be repaired at any time and an arm naming one would then be a
# proof requiring the defect it certifies against. What is asserted is the
# DENOMINATOR, this module's OWN fixtures found through the live git sweep, and
# the totality of the two rendered populations.
# ---------------------------------------------------------------------------


def test_the_live_sweep_finds_this_modules_own_deferred_fixtures() -> None:
    """CS-881. THE LIVE POSITIVE CONTROL, AND IT CANNOT BE REPAIRED AWAY.

    The planted arms above run the derivation over a string. This one runs it
    over the git sweep, against fixtures this module owns, so the derivation is
    proven on the tree it actually reads.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    mine = {site.qualname for site in deferred_raise_sites() if site.module == _THIS_MODULE}
    missing = set(_LIVE_DEFERRED_FIXTURES) - mine
    assert not missing, (
        f"the live sweep did not derive this module's own deferred fixtures: "
        f"{sorted(missing)}; it found {sorted(mine)}"
    )


def test_the_live_record_accounts_for_this_censuss_own_deferred_fixtures() -> None:
    """CS-881. THE FIXTURES ARE EXCLUDED BY THE TAXONOMY, NOT BY A LIST.

    :data:`CONTROL_MODULES` keeps this module's own plants out of the reported
    findings, and the out-of-scope record prints them every run so the
    exclusion is a visible decision rather than a silence - the shape
    :func:`out_of_scope_record` and :func:`notes_out_of_scope_record` already
    hold for their own populations.
    """
    if _THIS_MODULE not in tracked_sources():
        pytest.skip(f"{_THIS_MODULE} is not in the git sweep; run git add -N first")
    recorded = deferred_out_of_scope_record(deferred_raise_sites())
    mine = [line for line in recorded if f"{_THIS_MODULE}:" in line]
    assert mine, f"the live record does not account for this module's own fixtures: {recorded}"
    assert all(BUCKET_CONTROL.upper() in line for line in mine), (
        f"a fixture is recorded under a bucket other than {BUCKET_CONTROL}: {mine}"
    )


def test_every_derived_deferred_site_is_reported_or_recorded() -> None:
    """CS-881 EXHAUSTIVENESS. Nothing the sweep paid to derive is dropped.

    The two rendered populations filter on :data:`BUCKET_GRADED` and on
    :data:`RECORDED_BUCKETS`, which leaves a HOLE for
    :data:`BUCKET_UNCLASSIFIED` to fall through - deliberately, so a module
    outside :data:`SWEPT_ROOTS` reddens this arm rather than being absorbed by
    a catch-all.
    """
    derived = deferred_raise_sites()
    reported = len(deferred_findings(derived)) + len(deferred_out_of_scope_record(derived))
    assert reported == len(derived), (
        f"{len(derived)} deferred site(s) were derived and {reported} rendered, "
        "so one is in neither population and its bucket is unclassified"
    )


def test_the_deferred_denominator_is_not_empty() -> None:
    """CS-881. AN EMPTY POPULATION SATISFIES EVERY ZERO, INCLUDING THIS ONE.

    :func:`store_reach` is what the derivation actually LOOKED at - every
    handler in the tree that stores its own binding into a local. A derivation
    that read nothing reports the same finding count as one that read the whole
    tree, and this is what separates the two.

    AND THE FIRST TWO ASSERTIONS WERE THIS MODULE'S OWN FILED DEFECT, ONE LEVEL
    UP. A denominator satisfied by CONTROL fixtures is a denominator that never
    reaches the bucket the findings come from, which is the pooled-assertion
    form of ``memory/a-guard-can-be-green-by-accident.md`` in the exact shape
    CS-881 was opened against. MEASURED, by two independent agents, two
    different triggers: drop the two graded modules from the sweep, or widen
    ``CLAUDE.md``'s frozen list by two bullets - a DOC edit, no code change -
    and the live findings go from two to zero while this arm stays GREEN,
    because the surviving thirteen members all come from
    :data:`CONTROL_MODULES` and both assertions above still hold. Two sibling
    guards reddened on the same drop and this one did not.

    SO THE THIRD ASSERTION READS THE BUCKET, NOT THE MODULE. It is deliberately
    NOT a live finding: pinning one would be a proof requiring the defect it
    certifies against, which the block comment above this section refuses for
    stated reasons. The DENOMINATOR survives the repair the findings ask for -
    the repair is to raise a filename-free clone of ``last``, which leaves the
    ``last = exc`` store exactly where it is - so a graded member here is a
    fact about the sweep's REACH rather than about any site's verdict.
    """
    reach = store_reach()
    assert reach, "the store denominator is empty, so every deferred count means nothing"
    assert any(seen.module == _THIS_MODULE for seen in reach), (
        "the denominator does not include this module's own fixtures, so the "
        "sweep is not reading the tree this census is written against"
    )
    assert any(bucket_of(seen.module) == BUCKET_GRADED for seen in reach), (
        f"the denominator reaches no {BUCKET_GRADED} module, so every deferred "
        f"finding count is drawn from a bucket this sweep never read; "
        f"{len(reach)} member(s) were derived and their buckets are "
        f"{sorted({bucket_of(seen.module) for seen in reach})}"
    )


def test_every_deferred_key_is_distinct() -> None:
    """CS-881. TWO SITES SHARING A KEY ARE ONE SITE TO EVERY READER OF IT.

    The key carries no line number, for the dead-citation reason
    :attr:`Site.key` records. Two deferred raises of the same stored name, in
    the same scope, written the same way, would therefore collide - and that is
    reported as something to restructure rather than absorbed.
    """
    keys = [site.key for site in deferred_raise_sites()]
    assert len(set(keys)) == len(keys), f"two deferred sites share a key: {sorted(keys)}"


def test_the_live_deferred_findings_are_reported() -> None:
    """CS-881. THE FINDINGS ARE PRINTED, and the count is asserted against them.

    The census reports rather than fails: repairing a shipped site is not this
    module's to make. SKIPS rather than fails when the tree carries none, so a
    repair does not turn a report into a red arm.
    """
    findings = deferred_findings(deferred_raise_sites())
    if not findings:
        pytest.skip("no live deferred raise reaches the graded bucket this run")
    graded = [site for site in deferred_raise_sites() if bucket_of(site.module) == BUCKET_GRADED]
    assert len(findings) == len(graded), (
        f"{len(graded)} graded deferred site(s) derived and {len(findings)} reported"
    )
    body = "\n".join(f"  {line}" for line in findings)
    warnings.warn(
        f"CS-881 deferred raise, {len(findings)} site(s) in the {BUCKET_GRADED} "
        f"bucket raise a value a handler in the same scope stored, so the caught "
        f"exception's own str() renders with no chain to see it by:\n{body}",
        stacklevel=1,
    )
