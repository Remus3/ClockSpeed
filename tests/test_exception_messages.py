"""CS-852 gap 1 - the exception channel, graded on the MESSAGE-BUILDING CODE PATH.

WHAT THIS GRADES AND WHY IT IS NOT THE REPR CHANNEL AGAIN.
``tests/repr_rendering_guard.py`` derives its population from shipped FIELD
ANNOTATIONS and grades what a GENERATED ``__repr__`` prints. Its
``KIND_INHERITED`` premise - a class with no ``__repr__`` inherits
``object.__repr__`` and discloses no field - is true for a plain class and
FALSE for every exception, because ``BaseException.__repr__`` renders ``args``
and ``BaseException.__str__`` renders it too. That module recorded the gap in
``UNGRADED_EXCEPTION_CHANNEL`` rather than closing it, because closing it needs
the code path that BUILDS the message and not the annotations on the fields.
This module is that analysis.

THE ARMS DO NOT DERIVE FROM THE FINDINGS. Every synthetic corpus below is
authored in this file and parsed on the spot; not one reads the live tree to
decide what to test. Items in this project have been refuted for proofs whose
cases came from the live population, so REPAIRING A LEAK TURNED THE PROOF RED
and a green run certified that the tree still leaked.
``test_a_corpus_whose_every_channel_is_a_constant_yields_no_finding`` pins the
green-on-a-clean-tree property directly.

THE POSITIVE CONTROL IS NOT OPTIONAL AND IT IS NOT THE OBVIOUS ONE.
``assert MARKER not in rendered`` passes when the rendering withholds AND when
the marker was never planted - byte-identical outcomes, and this project
shipped exactly that bug inside a module whose own docstring cited the memory
file about it. ``test_a_planted_marker_reaches_args_on_a_synthetic_error``
proves the detection channel can see a leak at all, and
``test_a_forced_subject_actually_carries_the_marker`` proves each real subject
was built carrying one.

THE RUNTIME ARMS MEASURE AN ASYMMETRY RATHER THAN ASSUMING IT AWAY. Two
proof forms in the live tree look alike statically and behave differently at
runtime: a channel narrowed by a closed-vocabulary check REFUSES a planted
marker, and a channel proven only by its call sites ACCEPTS one and renders it.
Both outcomes are asserted, so the weaker form cannot be read as the stronger.
"""

from __future__ import annotations

import ast
import re
import warnings
from typing import Final

import pytest

from clockspeed.save.chunks import REASON_BAD_MAGIC, ChunkError
from clockspeed.save.header import (
    REASON_DECLARED_LENGTH_ABOVE_CAP,
    HeaderFormatError,
    HeaderReadError,
    HeaderTruncatedError,
)
from clockspeed.save.objects import ObjectError
from clockspeed.save.usmap import UsmapFormatError
from clockspeed.save.world import WorldLoadError
from tests.exception_message_guard import (
    ARGS_ROOTS,
    COMPOSING_CALLS,
    EXEMPT,
    GRADED_LAYER,
    PROVEN_AT_SITES,
    PROVEN_LITERAL,
    PROVEN_SCALAR,
    PROVEN_VOCABULARY,
    REPO_ROOT,
    SHAPE_FREE_TEXT,
    SHAPE_STRUCTURED,
    SHAPE_UNRAISED,
    UNPROVEN,
    Channel,
    ambiguous_callees,
    ambiguous_error_names,
    build_index,
    colliding_class_names,
    describe,
    findings_in,
    graded_classes,
    live_index,
    resolved_callees,
    scan_channels,
    stale_exemptions,
    swept_modules,
    ungraded_layers,
)
from tests.repr_rendering_guard import exception_rendering_classes

#: The module whose free-text refusals carry most of the exemption record, so
#: the arms that measure those exemptions name it once.
WORKDIR_MODULE: Final = "clockspeed/save/workdir.py"

#: How many elements a ``(root, label)`` candidate pair carries. Named because
#: a bare 2 in a comparison says nothing about which pairing is meant.
_CANDIDATE_PAIR_WIDTH: Final = 2

#: A module path inside the graded layer, so a synthetic corpus is swept the
#: way a shipped one is. No file of this name exists - the derivation reads a
#: parsed tree, never a disk.
SYNTHETIC_MODULE: Final = f"{GRADED_LAYER}synthetic_corpus.py"

#: Planted into a real message channel and grepped for in the rendering.
#: Obviously synthetic: this is never a real token, path, world or account id.
MARKER: Final = "PLANTED_CS852G1_MARKER_zzz"

#: Shortest string that can carry a measured reason rather than a stamp. The
#: length is the FLOOR and never the test - forty literal characters passed
#: every exemption arm of the sibling module, which is how a reason shipped
#: citing a helper that has never existed in this repository. The content check
#: is ``test_every_identifier_an_exemption_cites_exists_in_the_module_it_names``.
MINIMUM_REASON_CHARS: Final = 40

#: Underscore-carrying words that are PROSE in an exemption reason rather than a
#: citation. Every addition widens the hole the identifier check exists to
#: close, so an entry has to be a real English compound.
_REASON_PROSE: Final[frozenset[str]] = frozenset({"free_text", "non_negotiables", "opt_in"})

#: Every save-layer class the derivation puts on the exception channel,
#: recorded so membership is asserted in BOTH directions.
#:
#: PINNING THIS IS NOT ANTI-MONOTONE. Repairing a class does not remove it from
#: the channel - an error that narrows its field is still an error that renders
#: ``args`` - so a repair moves its VERDICT and never its MEMBERSHIP. What the
#: record catches is a member LEAVING silently, which is also the only way to
#: evade this guard: move a save-layer error out of the layer and nothing else
#: would notice.
RECORDED_CHANNEL: Final[tuple[str, ...]] = (
    "clockspeed/save/chunks.py::ChunkBudgetExceededError",
    "clockspeed/save/chunks.py::ChunkDecompressError",
    "clockspeed/save/chunks.py::ChunkError",
    "clockspeed/save/chunks.py::ChunkFramingError",
    "clockspeed/save/chunks.py::ChunkTruncatedError",
    "clockspeed/save/header.py::HeaderError",
    "clockspeed/save/header.py::HeaderFormatError",
    "clockspeed/save/header.py::HeaderReadError",
    "clockspeed/save/header.py::HeaderTruncatedError",
    "clockspeed/save/header.py::PersonalDataOptInRequiredError",
    "clockspeed/save/header.py::UnsupportedHeaderVersionError",
    "clockspeed/save/objects.py::ObjectBudgetExceededError",
    "clockspeed/save/objects.py::ObjectError",
    "clockspeed/save/objects.py::ObjectFormatError",
    "clockspeed/save/objects.py::ObjectTruncatedError",
    "clockspeed/save/objects.py::UnsupportedBodyLayoutError",
    "clockspeed/save/objects.py::UnsupportedSaveVersionError",
    "clockspeed/save/usmap.py::UnsupportedUsmapCompressionError",
    "clockspeed/save/usmap.py::UsmapError",
    "clockspeed/save/usmap.py::UsmapFormatError",
    "clockspeed/save/workdir.py::DestinationRefusedError",
    "clockspeed/save/workdir.py::SourceUnreadableError",
    "clockspeed/save/workdir.py::WorkDirError",
    "clockspeed/save/world.py::WorldLoadError",
)


def _channels(source: str) -> tuple[Channel, ...]:
    """Every channel the derivation finds in one synthetic module.

    Args:
        source: The module text.

    Returns:
        One record per class-and-channel, whatever its verdict.
    """
    index = build_index({SYNTHETIC_MODULE: source})
    return scan_channels(index)


def _findings(source: str) -> tuple[Channel, ...]:
    """The unproven, unexempted channels of one synthetic module.

    Args:
        source: The module text.

    Returns:
        The findings.
    """
    return findings_in(_channels(source), {})


def _verdicts(source: str) -> dict[str, str]:
    """Each ``Class.channel`` in a synthetic module to its verdict.

    Args:
        source: The module text.

    Returns:
        The mapping.
    """
    return {f"{c.class_name}.{c.channel}": c.verdict for c in _channels(source)}


def _channels_across(sources: dict[str, str]) -> tuple[Channel, ...]:
    """Every channel across a synthetic corpus of more than one module.

    Needed because two of the unsound shapes this module fences are
    CROSS-MODULE by construction: a namesake helper in a second module, and a
    class name a later module reuses. Neither can be expressed in one file.

    Args:
        sources: Repo-relative module path to module text.

    Returns:
        The channels.
    """
    return scan_channels(build_index(sources))


def _findings_across(sources: dict[str, str]) -> tuple[Channel, ...]:
    """The unproven channels of a multi-module synthetic corpus.

    Args:
        sources: Repo-relative module path to module text.

    Returns:
        The findings.
    """
    return findings_in(_channels_across(sources), {})


# ---------------------------------------------------------------------------
# The rule, on corpora authored here
# ---------------------------------------------------------------------------

_FREE_TEXT_LEAK = '''
"""A free-text error handed a decoded value at the raise site."""


class ReaderError(Exception):
    """No __init__ of its own, so every raise site builds the message."""


def read(cursor: object) -> None:
    """Raise with a decoded name in the message."""
    name = cursor.string(64)
    raise ReaderError(f"cannot read {name}")
'''

_FREE_TEXT_CONSTANT = '''
"""A free-text error handed a module constant at the raise site."""

REASON_SHORT = "the buffer ended early"


class ReaderError(Exception):
    """No __init__ of its own."""


def read(cursor: object) -> None:
    """Raise with a fixed reason."""
    raise ReaderError(REASON_SHORT)
'''

_STRUCTURED_AT_SITES = '''
"""A structured error whose text parameter is a literal at every site."""


class ReaderError(Exception):
    """Builds its own message."""

    def __init__(self, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        super().__init__(f"field {field} at byte {offset}")


def read() -> None:
    """Raise with a literal field name."""
    raise ReaderError(field="magic", offset=0)
'''

_STRUCTURED_LEAKING_SITE = '''
"""A structured error one of whose sites passes a decoded value."""


class ReaderError(Exception):
    """Builds its own message."""

    def __init__(self, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        super().__init__(f"field {field} at byte {offset}")


def read(cursor: object) -> None:
    """Raise with a literal at one site and a decoded value at another."""
    raise ReaderError(field="magic", offset=0)


def read_again(cursor: object) -> None:
    """The second site is the leak."""
    raise ReaderError(field=cursor.string(64), offset=4)
'''

_STRUCTURED_INLINE_VOCABULARY = '''
"""A structured error narrowing its text parameter inline."""

FIELD_NAMES = frozenset({"magic", "marker"})


class ReaderError(Exception):
    """Builds its own message after a membership check."""

    def __init__(self, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        if field not in FIELD_NAMES:
            raise ValueError("field name is not one this module may report")
        super().__init__(f"field {field} at byte {offset}")


def read(cursor: object) -> None:
    """Raise with a decoded value the check will refuse."""
    raise ReaderError(field=cursor.string(64), offset=0)
'''

_STRUCTURED_HELPER_VOCABULARY = '''
"""A structured error narrowing its text parameter through a helper."""

FIELD_NAMES = frozenset({"magic", "marker"})


def _checked(name: str) -> str:
    """Refuse a name outside the closed vocabulary."""
    if name not in FIELD_NAMES:
        raise ValueError("field name is not one this module may report")
    return name


class ReaderError(Exception):
    """Builds its own message from a checked name."""

    def __init__(self, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        checked = _checked(field)
        super().__init__(f"field {checked} at byte {offset}")


def read(cursor: object) -> None:
    """Raise with a decoded value the helper will refuse."""
    raise ReaderError(field=cursor.string(64), offset=0)
'''

_INHERITED_INIT = '''
"""A subclass with no __init__ of its own, governed by its base."""


class ReaderError(Exception):
    """The base builds the message."""

    def __init__(self, *, field: str) -> None:
        """Render from the field."""
        super().__init__(f"field {field}")


class ReaderTruncatedError(ReaderError):
    """No __init__ of its own. Its args come from the base above."""


def read(cursor: object) -> None:
    """Raise the SUBCLASS with a decoded value."""
    raise ReaderTruncatedError(field=cursor.string(64))
'''

_MESSAGE_BUILDER = '''
"""A structured error whose message is built by a module-level helper."""


def _render(reason: str, field: str, offset: int) -> str:
    """Compose the one-line message."""
    parts = [f"field {field} at byte {offset} {reason}"]
    return "; ".join(parts)


class ReaderError(Exception):
    """Delegates its message to the helper above."""

    def __init__(self, reason: str, *, field: str, offset: int) -> None:
        """Render through the helper."""
        super().__init__(_render(reason, field, offset))


def read(cursor: object) -> None:
    """Raise with a decoded reason and a literal field."""
    raise ReaderError(cursor.string(64), field="magic", offset=0)
'''

_SCALAR_ONLY = '''
"""A structured error whose every channel is a number."""


class ReaderError(Exception):
    """Numbers only."""

    def __init__(self, *, offset: int, declared: int | None = None) -> None:
        """Render from the scalars."""
        super().__init__(f"at byte {offset}, declared {declared}")


def read() -> None:
    """Raise it."""
    raise ReaderError(offset=0, declared=4)
'''

_ALIASED_AND_CONTAINED = '''
"""A free-text error handed a value through an alias, a container and a handler."""


class ReaderError(Exception):
    """No __init__ of its own, so every raise site builds the message."""


def read(cursor: object) -> None:
    """Raise with a value that arrives by three routes the rule does not model."""
    name = cursor.string(64)
    kept = name
    holder = {"n": name}
    raise ReaderError(f"cannot read {kept} at {holder['n']}")


def open_it(path: object) -> None:
    """Raise with the handler binding aliased into a local."""
    try:
        path.open()
    except OSError as exc:
        held = exc
        raise ReaderError(f"cannot open: {held}") from None
'''

_OR_FALLBACK = '''
"""A free-text error whose message falls back with `or`."""


class ReaderError(Exception):
    """No __init__ of its own."""


def read(cursor: object) -> None:
    """Raise with a decoded name behind an `or` fallback."""
    name = cursor.string(64)
    raise ReaderError(f"cannot read {name or 'unnamed'}")
'''

_FORMAT_KEYWORDS = '''
"""A free-text error built with str.format and keyword arguments."""


class ReaderError(Exception):
    """No __init__ of its own."""


def read(cursor: object) -> None:
    """Raise with the decoded value passed as a format keyword."""
    name = cursor.string(64)
    raise ReaderError("cannot read {n}".format(n=name))
'''

_ASSIGNED_ARGS = '''
"""A structured error that assigns self.args instead of calling super()."""


class ReaderError(Exception):
    """Sets args by hand."""

    def __init__(self, *, field: str) -> None:
        """Record the field and set args directly."""
        self.field = field
        self.args = (f"field {field}",)


def read(cursor: object) -> None:
    """Raise with a decoded value."""
    raise ReaderError(field=cursor.string(64))
'''

_UNBOUND_BASE_INIT = '''
"""A structured error calling the base initialiser unbound."""


class ReaderError(Exception):
    """Calls Exception.__init__ directly rather than through super()."""

    def __init__(self, *, field: str) -> None:
        """Build the message through the unbound base initialiser."""
        Exception.__init__(self, f"field {field}")


def read(cursor: object) -> None:
    """Raise with a decoded value."""
    raise ReaderError(field=cursor.string(64))
'''

_NESTED_VOCABULARY_GUARD = '''
"""A structured error whose vocabulary check is nested under a condition."""

FIELD_NAMES = frozenset({"magic", "marker"})


class ReaderError(Exception):
    """The check only runs when strict is set."""

    def __init__(self, *, field: str, strict: bool = False) -> None:
        """Render from the field, checking it only sometimes."""
        if strict:
            if field not in FIELD_NAMES:
                raise ValueError("field name is not one this module may report")
        super().__init__(f"field {field}")


def read(cursor: object) -> None:
    """Raise without the check running."""
    raise ReaderError(field=cursor.string(64))
'''

_POOLED_SITE_WITH_NO_BINDING = '''
"""A raise site whose enclosing function is only ever called by a namesake."""


class ReaderError(Exception):
    """No __init__ of its own."""


def render(field: str) -> None:
    """Raise with the field this function was handed."""
    raise ReaderError(f"field {field}")


class Other:
    """Holds a namesake of the raising function."""

    def render(self) -> str:
        """Nothing binds `field` here."""
        return "x"


def use() -> None:
    """Call the namesake only."""
    Other().render()
'''

_SAVE_BODY_INTO_A_FALLBACK = '''
"""The headline refutation shape, reduced to a corpus authored here."""

REASON_UNMEASURED = "names a type this reader has no model for"


class ReaderError(Exception):
    """Builds its own message from a reason and a field."""

    def __init__(self, reason: str, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        super().__init__(f"save object field {field} at byte {offset} {reason}")


def read(cursor: object) -> None:
    """Raise with a body-read name standing in for the fixed reason."""
    instance_name = cursor.string("instance_name")
    raise ReaderError(instance_name or REASON_UNMEASURED, field="type_path", offset=0)
'''

#: A genuine narrower, and a NAMESAKE in a second module that validates
#: nothing. The two modules are the point: a bare-name lookup finds the real
#: one and clears the decoy's caller.
_DECOY_NARROWER: Final[dict[str, str]] = {
    f"{GRADED_LAYER}real_corpus.py": '''
"""A module shipping a genuine narrower."""

FIELD_NAMES = frozenset({"magic", "marker"})


def _checked_field(name: str) -> str:
    """Refuse a name outside the closed vocabulary."""
    if name not in FIELD_NAMES:
        raise ValueError("field name is not one this module may report")
    return name
''',
    f"{GRADED_LAYER}decoy_corpus.py": '''
"""A module shipping a namesake that validates nothing."""


def _checked_field(name: str) -> str:
    """Strip the name. It validates nothing at all."""
    return name.strip()


class ReaderError(Exception):
    """Routes its field through the namesake above."""

    def __init__(self, *, field: str) -> None:
        """Render from the namesake's result."""
        checked = _checked_field(field)
        super().__init__(f"field {checked}")


def read(cursor: object) -> None:
    """Raise with a decoded value."""
    raise ReaderError(field=cursor.string(64))
''',
}

#: A save-layer error and a LATER module reusing its class name.
_COLLIDING_CLASS_NAME: Final[dict[str, str]] = {
    f"{GRADED_LAYER}a_corpus.py": '''
"""A save-layer error that leaks."""


class ReaderError(Exception):
    """No __init__ of its own."""


def read(cursor: object) -> None:
    """Raise with a decoded value."""
    raise ReaderError(f"cannot read {cursor.string(64)}")
''',
    "clockspeed/data/z_corpus.py": '''
"""A later module declaring the same class name."""


class ReaderError(Exception):
    """A namesake above the graded layer."""
''',
}

_EARLY_RETURN_NARROWER = '''
"""A helper whose fast path hands the value back before it is checked."""

FIELD_NAMES = frozenset({"magic", "marker"})


def _checked(name: str, strict: bool = False) -> str:
    """Check the name only on the slow path."""
    if not strict:
        return name
    if name not in FIELD_NAMES:
        raise ValueError("field name is not one this module may report")
    return name


class ReaderError(Exception):
    """Routes its field through the helper above."""

    def __init__(self, *, field: str) -> None:
        """Render from the helper's result."""
        checked = _checked(field)
        super().__init__(f"field {checked}")


def read(cursor: object) -> None:
    """Raise with a decoded value the fast path never checks."""
    raise ReaderError(field=cursor.string(64))
'''

#: Two namesake renderers with the SAME parameter names and DIFFERENT
#: bodies. Only the second one shows the reason.
_TWO_NAMESAKE_BUILDERS: Final[dict[str, str]] = {
    f"{GRADED_LAYER}a_render.py": '''
"""A module whose renderer shows only the offset."""


def _render(reason: str, offset: int) -> str:
    """Compose a message from the offset alone."""
    return f"at byte {offset}"
''',
    f"{GRADED_LAYER}b_render.py": '''
"""A module whose namesake renderer shows the reason too."""


def _render(reason: str, offset: int) -> str:
    """Compose a message from both."""
    return f"at byte {offset}: {reason}"


class ReaderError(Exception):
    """Delegates its message to a renderer."""

    def __init__(self, reason: str, *, offset: int) -> None:
        """Render through the helper."""
        super().__init__(_render(reason, offset))


def read(cursor: object) -> None:
    """Raise with a decoded reason."""
    raise ReaderError(cursor.string(64), offset=0)
''',
}

_STRUCTURED_NEVER_BUILT = '''
"""A structured error with a text channel and no construction site at all."""


class ReaderError(Exception):
    """Builds its own message from a parameter nobody in the tree ever binds."""

    def __init__(self, *, field: str, offset: int) -> None:
        """Render from the taxonomy fields."""
        super().__init__(f"field {field} at byte {offset}")
'''

_NEVER_CONSTRUCTED = '''
"""A free-text error nothing in the tree ever builds."""


class ReaderError(Exception):
    """Never raised here, so no message-building path exists to read."""
'''

_NO_EXCEPTION_AT_ALL = '''
"""A corpus with no exception class in it."""


class Reader:
    """Not an exception."""

    def __init__(self, data: bytes) -> None:
        """Hold the buffer."""
        self._data = data
'''


def test_a_free_text_error_handed_a_decoded_value_is_a_finding() -> None:
    """THE CONTRACT for shape (b). Every raise site builds the message."""
    found = _findings(_FREE_TEXT_LEAK)
    named = [(c.class_name, c.channel) for c in found]
    assert named == [("ReaderError", "cursor.string(64)")], describe(found)
    assert found[0].shape == SHAPE_FREE_TEXT


def test_a_free_text_error_handed_a_module_constant_is_not_a_finding() -> None:
    """A constant authored in the repository cannot carry save content."""
    assert _findings(_FREE_TEXT_CONSTANT) == ()
    assert _verdicts(_FREE_TEXT_CONSTANT)["ReaderError.REASON_SHORT"] == PROVEN_LITERAL


def test_a_structured_parameter_is_proven_by_its_call_sites() -> None:
    """A text parameter every site binds to a literal cannot carry a value."""
    assert _findings(_STRUCTURED_AT_SITES) == ()
    verdicts = _verdicts(_STRUCTURED_AT_SITES)
    assert verdicts["ReaderError.field"] == PROVEN_AT_SITES
    assert verdicts["ReaderError.offset"] == PROVEN_SCALAR


def test_one_leaking_site_is_enough_to_break_the_call_site_proof() -> None:
    """A proof over the sites is only as strong as its WEAKEST site.

    The first site here passes a literal. Reading the sites as a disjunction
    rather than a conjunction would report nothing, which is the pooled-guard
    shape - a threshold met by the strongest member while the weakest goes
    unmeasured.
    """
    found = _findings(_STRUCTURED_LEAKING_SITE)
    named = [(c.class_name, c.channel) for c in found]
    assert named == [("ReaderError", "field")], describe(found)


def test_an_inline_membership_check_narrows_a_text_parameter() -> None:
    """A guard clause against a module-level literal collection is a proof."""
    assert _findings(_STRUCTURED_INLINE_VOCABULARY) == ()
    assert _verdicts(_STRUCTURED_INLINE_VOCABULARY)["ReaderError.field"] == PROVEN_VOCABULARY


def test_a_helper_the_value_is_routed_through_narrows_it_too() -> None:
    """The narrowing is DERIVED from the guard clause, not from the name.

    Nothing here is called ``_checked_field``. What makes the helper a
    narrower is that its parameter reaches its ``return`` only past a
    membership test against a module-level collection of string literals.
    """
    assert _findings(_STRUCTURED_HELPER_VOCABULARY) == ()
    verdicts = _verdicts(_STRUCTURED_HELPER_VOCABULARY)
    assert verdicts["ReaderError._checked(field)"] == PROVEN_VOCABULARY, verdicts


def test_a_subclass_with_no_init_is_graded_by_the_one_it_inherits() -> None:
    """READING ONLY A CLASS'S OWN BODY LEAVES LIVE CLASSES UNGRADED.

    Subclasses of ``ChunkError`` and of ``ObjectError`` ship no ``__init__``
    and are governed by their base. An analysis that stopped at the class body
    would report them as having no message-building path and pass them in
    silence. The live half of the claim is
    ``test_the_live_tree_has_a_class_governed_by_an_inherited_initialiser``;
    this arm is the rule on a corpus authored here. NO COUNT IS NAMED: an
    earlier wording carried one taken from a report rather than measured, and
    the tree does not hold that many.
    """
    verdicts = _verdicts(_INHERITED_INIT)
    assert "ReaderTruncatedError.field" in verdicts, sorted(verdicts)
    found = _findings(_INHERITED_INIT)
    leaking = sorted((c.class_name, c.channel) for c in found)
    assert leaking == [("ReaderError", "field"), ("ReaderTruncatedError", "field")], describe(found)


def test_a_message_builder_is_descended_into_and_its_parameters_are_the_channels() -> None:
    """A helper that composes the message is part of the path, not a wall.

    Treating ``_render(...)`` as one opaque channel would name the whole call
    and hide WHICH argument is at fault. Descending binds the helper's
    parameters back to the caller's expressions, so the channels are the
    initialiser's own.
    """
    verdicts = _verdicts(_MESSAGE_BUILDER)
    assert verdicts["ReaderError.field"] == PROVEN_AT_SITES, verdicts
    assert verdicts["ReaderError.reason"] == UNPROVEN, verdicts
    found = _findings(_MESSAGE_BUILDER)
    named = [(c.class_name, c.channel) for c in found]
    assert named == [("ReaderError", "reason")], describe(found)


def test_a_scalar_channel_is_proven_by_its_annotation() -> None:
    """A number cannot carry a name, a path or an account id."""
    assert _findings(_SCALAR_ONLY) == ()
    verdicts = _verdicts(_SCALAR_ONLY)
    assert verdicts["ReaderError.offset"] == PROVEN_SCALAR
    assert verdicts["ReaderError.declared"] == PROVEN_SCALAR


def test_an_alias_a_container_and_a_handler_binding_are_reported_not_skipped() -> None:
    """THE CS-855 REFUTATION SHAPE, MEASURED HERE RATHER THAN ASSERTED IN PROSE.

    A sibling slice in this project was refuted because its guard generalised
    a syntactic bare-name match into a claim that a population was EMPTY, and
    a single aliased binding defeated the detector while the arm stayed green.
    The routes are the same three this corpus carries: a local aliased from
    another local, a value fetched back out of a container, and an
    ``except ... as`` binding held in a local.

    The direction that matters is that NONE of them is silently dropped. The
    alias chain resolves through to the real source and is named by it; the
    container lookup and the handler binding are not modelled at all and are
    therefore graded UNPROVEN. Unmodelled must mean REPORTED, because
    unmodelled meaning skipped is what makes a zero meaningless.
    """
    found = _findings(_ALIASED_AND_CONTAINED)
    named = sorted(c.channel for c in found)
    assert named == ["cursor.string(64)", "exc", "holder['n']"], describe(found)


# ---------------------------------------------------------------------------
# Shapes that returned a POSITIVE FALSE PROOF, each measured before the repair
#
# A `proven-*` verdict is a CLEARANCE a later session will cite as evidence a
# channel is safe. A shape the rule cannot model soundly must therefore come
# back `unproven`, never `proven-*`. Every arm below was watched failing with
# the exact wrong verdict recorded in its docstring before the rule was
# changed - the failure was a clean claim about a channel that leaks.
# ---------------------------------------------------------------------------


def test_an_or_fallback_is_composed_rather_than_read_as_a_boolean() -> None:
    """WAS ``proven-scalar``. ``a or b`` YIELDS AN OPERAND, NOT A BOOLEAN.

    ``ast.Compare`` really does yield a bool, and grouping ``ast.BoolOp`` with
    it read ``{name or 'unnamed'}`` as an expression whose whole value space is
    numbers and flags. It renders ``name``.

    THIS IS LIVE HOUSE STYLE, not a hypothetical: ``clockspeed/solve/ratio.py``
    and both optimizer backends build refusals as
    ``{', '.join(...) or 'nothing'}``. None sits in the graded layer today, and
    nothing stopped the idiom arriving there with a clearance attached.
    """
    verdicts = _verdicts(_OR_FALLBACK)
    assert PROVEN_SCALAR not in verdicts.values(), verdicts
    found = _findings(_OR_FALLBACK)
    assert [c.channel for c in found] == ["cursor.string(64)"], describe(found)


def test_a_format_keyword_argument_is_a_channel() -> None:
    """WAS ``<no channel>``, WHICH IS A POSITIVE CLAIM THAT NOTHING RENDERS.

    ``"{n}".format(n=value)`` puts ``value`` in the message through a KEYWORD.
    The composition read only positional arguments, so the class came back with
    no channel at all - indistinguishable from an error whose message is a
    bare constant.
    """
    found = _findings(_FORMAT_KEYWORDS)
    assert [c.channel for c in found] == ["cursor.string(64)"], describe(found)


def test_assigning_self_args_is_a_channel() -> None:
    """WAS ``<no channel>``. ``super().__init__`` IS NOT THE ONLY WAY IN.

    ``self.args = (message,)`` sets the tuple ``__repr__`` and ``__str__``
    render, without calling any initialiser. Reading only ``super().__init__``
    graded such a class as rendering nothing.
    """
    found = _findings(_ASSIGNED_ARGS)
    assert [c.channel for c in found] == ["field"], describe(found)


def test_an_unbound_base_initialiser_call_is_a_channel() -> None:
    """WAS ``<no channel>``. ``Exception.__init__(self, m)`` SETS ``args`` TOO.

    The unbound spelling is ordinary Python and reaches ``args`` exactly as
    ``super().__init__(m)`` does. Matching only the ``super()`` spelling made
    the other one invisible.
    """
    found = _findings(_UNBOUND_BASE_INIT)
    assert [c.channel for c in found] == ["field"], describe(found)


def test_a_vocabulary_guard_under_a_condition_is_not_a_runtime_barrier() -> None:
    """WAS ``proven-vocabulary``, WHICH CLAIMS THE VALUE CANNOT REACH ``args``.

    The narrowing search walked the whole function, so a check nested under an
    unrelated condition counted. Here the check runs only when ``strict`` is
    set and the raise site never sets it, so the value reaches the message
    unchecked while carrying the strongest clearance the rule can issue.

    The repair is positional DOMINANCE: the guard has to be a direct statement
    of the function body, and has to come before the statement that builds the
    message.
    """
    verdicts = _verdicts(_NESTED_VOCABULARY_GUARD)
    assert PROVEN_VOCABULARY not in verdicts.values(), verdicts
    found = _findings(_NESTED_VOCABULARY_GUARD)
    assert [c.channel for c in found] == ["field"], describe(found)


def test_a_site_that_binds_nothing_does_not_prove_the_parameter() -> None:
    """WAS ``proven-at-sites`` OVER ZERO BINDINGS - THE TWIN OF MUTANT M6.

    ``test_a_call_site_proof_over_no_call_site_proves_nothing`` fixed the
    empty-SITE-LIST spelling and left the empty-BINDING-SET spelling live: a
    site that binds nothing was skipped with ``continue``, and a parameter
    every site skipped fell through to the strongest call-site clearance.

    Sites are pooled by callee name, so the namesake method here supplies a
    site that cannot bind ``field`` at all. Reaching the end of the loop
    having proven nothing is now UNPROVEN.
    """
    verdicts = _verdicts(_POOLED_SITE_WITH_NO_BINDING)
    assert PROVEN_AT_SITES not in verdicts.values(), verdicts
    assert [c.channel for c in _findings(_POOLED_SITE_WITH_NO_BINDING)] == ["field"]


def test_a_namesake_helper_does_not_inherit_a_real_narrowers_clearance() -> None:
    """WAS ``proven-vocabulary`` - THE SHAPE THAT DESTROYED THE SIBLING SLICE.

    A bare-name lookup accepted the FIRST shipped definition that narrowed and
    cleared a caller routing its value through a NAMESAKE that only calls
    ``strip``. That is a syntactic name match standing in for a semantic
    property, and ``_checked_field`` is a live resolved name in this tree.

    The repair requires EVERY shipped definition of the name to carry the
    property. Ambiguity now costs a clearance rather than granting one.
    """
    channels = _channels_across(_DECOY_NARROWER)
    verdicts = {c.verdict for c in channels}
    assert PROVEN_VOCABULARY not in verdicts, describe(channels)
    found = _findings_across(_DECOY_NARROWER)
    assert [c.channel for c in found] == ["_checked_field(field)"], describe(found)


def test_a_later_namesake_class_does_not_evict_a_save_layer_error() -> None:
    """WAS AN EMPTY POPULATION - the save-layer class vanished entirely.

    The class index was keyed by bare NAME, so a later module declaring the
    same name overwrote the save-layer entry and its channels were never
    graded. Findings went from one to zero with nothing to say so.

    The population is now built from every class DEFINITION. Base resolution
    is still by name and cannot be otherwise without resolving imports, so
    the collision is also CENSUSED - see
    ``test_no_shipped_class_name_collides``.
    """
    found = _findings_across(_COLLIDING_CLASS_NAME)
    assert [c.channel for c in found] == ["cursor.string(64)"], describe(found)


def test_the_headline_refutation_shape_is_a_finding() -> None:
    """THE ADVERSARY'S PLANTED LEAK, REDUCED TO A CORPUS AUTHORED HERE.

    A value read straight off the save body, standing in for a fixed reason
    behind an ``or``, interpolated into a shipped error message. Measured
    reaching ``args``, ``str`` and ``repr`` on the real class; measured as
    zero findings by this guard before the repair, with a byte-identical
    report.
    """
    found = _findings(_SAVE_BODY_INTO_A_FALLBACK)
    assert [c.channel for c in found] == ["reason"], describe(found)


def test_a_helper_that_returns_before_its_guard_is_not_a_narrower() -> None:
    """THE SUBJECT FOR THE RETURN-ORDERING RULE, and a mutant found it missing.

    Reverting the ordering requirement survived every arm, which means the
    requirement was a claim nothing supported. This corpus is the shape
    that makes it load-bearing: the helper's FAST PATH hands the value
    back before the membership test runs, and the raise site takes exactly
    that path. Matching a single guarded return would clear the helper on
    the strength of a branch the caller never enters.

    The positional requirement was REMOVED from the parameter rule at the
    same time, because there it had no subject: a direct-body guard that
    raises either lets the value through as vocabulary or discards the
    instance before a caller sees it. Keeping an untestable strictness
    reads as rigour and is really an unsupported claim.
    """
    verdicts = _verdicts(_EARLY_RETURN_NARROWER)
    assert PROVEN_VOCABULARY not in verdicts.values(), verdicts
    found = _findings(_EARLY_RETURN_NARROWER)
    # The helper is still descended into as a message builder - it returns a
    # parameter unchanged - so the channel is named for the caller's own
    # expression rather than for the call that failed to narrow it.
    assert [c.channel for c in found] == ["field"], describe(found)


def test_every_namesake_builder_is_descended_not_just_the_first() -> None:
    """I FOUND THIS ONE BY TURNING THE ROUND'S OWN PRINCIPLE ON THE REPAIR.

    The repair for the namesake shape requires every shipped definition of
    a name to build a message AND to agree on parameter names before the
    walk steps inside. Agreeing on parameter names does not make two
    bodies the same function, and descending only the first graded the
    call by one namesake's channels while the caller may have meant the
    other. Here the first renderer shows only the offset and the second
    shows the reason as well; taking the first alone reports nothing.

    ``_render`` is declared twice in the live tree, once per parser layer,
    so this is the shape the tree already carries rather than a
    hypothetical.
    """
    found = _findings_across(_TWO_NAMESAKE_BUILDERS)
    assert [c.channel for c in found] == ["reason"], describe(
        _channels_across(_TWO_NAMESAKE_BUILDERS)
    )


def test_a_call_site_proof_over_no_call_site_proves_nothing() -> None:
    """AN EMPTY SITE LIST IS NOT A CLEAN ONE, AND A MUTANT FOUND THIS ARM MISSING.

    The call-site proof walks every binding and passes when none of them
    discloses. Over ZERO bindings that is satisfied for free - the exact shape
    ``memory/an-empty-population-satisfies-every-zero.md`` records. Flipping
    the no-site branch from UNPROVEN to PROVEN_AT_SITES survived every other
    arm in this module, because no live class reaches it: a subclass that
    ships no initialiser inherits one whose sites come from the whole family,
    and the structured class nothing builds carries a constant. This corpus is
    where the branch has a subject.
    """
    verdicts = _verdicts(_STRUCTURED_NEVER_BUILT)
    assert verdicts["ReaderError.field"] == UNPROVEN, verdicts
    assert verdicts["ReaderError.offset"] == PROVEN_SCALAR, verdicts
    found = _findings(_STRUCTURED_NEVER_BUILT)
    named = [(c.class_name, c.channel) for c in found]
    assert named == [("ReaderError", "field")], describe(found)


def test_a_never_constructed_error_is_recorded_rather_than_passed() -> None:
    """AN EMPTY SITE LIST IS NOT A CLEAN ONE.

    A free-text class the tree never builds has no message-building path to
    read, so a rule that proved it by walking its sites would prove it by
    walking nothing. It is graded :data:`SHAPE_UNRAISED` and recorded.
    """
    channels = _channels(_NEVER_CONSTRUCTED)
    assert [c.shape for c in channels] == [SHAPE_UNRAISED], describe(channels)
    assert channels[0].verdict == PROVEN_LITERAL
    assert _findings(_NEVER_CONSTRUCTED) == ()


def test_a_corpus_whose_every_channel_is_a_constant_yields_no_finding() -> None:
    """GREEN ON A CLEAN TREE, proved directly rather than inferred.

    A rule that reported the constant corpus would make every green above a
    statement about the corpus rather than about the rule.
    """
    assert _findings(_NO_EXCEPTION_AT_ALL) == ()
    assert _channels(_NO_EXCEPTION_AT_ALL) == ()


def test_the_synthetic_corpora_are_not_all_silent() -> None:
    """A parse that failed would report nothing and pass every arm above.

    Both directions in one place: the leaking corpora yield findings and the
    clean ones do not, so a derivation that had stopped reading source
    entirely cannot satisfy the pair.
    """
    leaking = (
        _FREE_TEXT_LEAK,
        _STRUCTURED_LEAKING_SITE,
        _STRUCTURED_NEVER_BUILT,
        _ALIASED_AND_CONTAINED,
        _EARLY_RETURN_NARROWER,
        _INHERITED_INIT,
        _MESSAGE_BUILDER,
    )
    clean = (_FREE_TEXT_CONSTANT, _STRUCTURED_AT_SITES, _STRUCTURED_INLINE_VOCABULARY)
    assert all(_findings(source) for source in leaking)
    assert not any(_findings(source) for source in clean)


# ---------------------------------------------------------------------------
# The live tree
# ---------------------------------------------------------------------------


def test_the_graded_population_is_not_empty() -> None:
    """An equality over nothing is satisfied for free."""
    assert graded_classes(live_index()), "the exception census found nothing"


def test_the_population_is_pinned_in_both_directions() -> None:
    """A MEMBER MAY NOT JOIN OR LEAVE SILENTLY.

    Moving a save-layer error out of the layer is the one way to evade this
    guard without editing it, and the departure half is what catches that.
    """
    live = set(graded_classes(live_index()))
    recorded = set(RECORDED_CHANNEL)
    departed = sorted(recorded - live)
    arrived = sorted(live - recorded)
    assert departed == [], (
        f"error class(es) left the graded channel and are graded by nothing: {departed}"
    )
    assert arrived == [], (
        f"new save-layer error class(es); confirm each channel, then record them: {arrived}"
    )


def test_the_population_agrees_with_the_repr_channel_census() -> None:
    """TWO INDEPENDENT DERIVATIONS OF THE SAME SET, AND AGREEMENT IS A CHECK.

    ``tests/repr_rendering_guard.py`` reaches the same classes by walking
    bases from the class index it builds for its own sweep. This module walks
    them again to resolve the governing initialiser, which that module never
    needed. Agreement is not proof - both read the same tree - but a
    disagreement is a defect in one of them, and neither can drift quietly.
    """
    assert set(graded_classes(live_index())) == set(exception_rendering_classes())


def test_the_sweep_reaches_beyond_the_graded_layer() -> None:
    """THE SCOPE IS A CHOICE, AND A BROKEN WALK LOOKS THE SAME AS A NARROW ONE.

    Shipped errors above the save layer are found and NOT graded: their
    message channels are not fed by a save. Measuring that they were found is
    what separates "deliberately out of scope" from "the walk stopped early".
    """
    assert ungraded_layers(live_index()), "the walk found no error above the save layer"
    swept = swept_modules(live_index())
    assert any(not module.startswith(GRADED_LAYER) for module in swept), sorted(swept)[:5]


def test_no_shipped_error_builds_a_message_from_an_unproven_channel() -> None:
    """THE CONTRACT, AND ITS ZERO IS NARROWER THAN ITS NAME.

    What is measured: every channel the SYNTACTIC composition in
    ``tests/exception_message_guard.py`` finds is proven by one of the four
    forms, or carries a stated exemption. What is NOT measured: a value that
    reaches ``args`` by a route the composition does not model. Such a value
    is not a finding here - it is INVISIBLE here, and the two outcomes are the
    same green.

    The distinction is written down because the sibling slice on CS-855 was
    refuted for exactly this wording: its guard generalised a syntactic match
    into a claim that a population was EMPTY, and one aliased binding defeated
    the detector while the arm stayed green. The routes this composition does
    not model are listed in the guard's own docstring under WHAT THIS DOES NOT
    REACH; the count below is a statement about the channels it FOUND.
    """
    channels = scan_channels(live_index())
    assert channels, "the composition found no channel at all - this zero would be vacuous"
    found = findings_in(channels, EXEMPT)
    count = len(found)
    assert count == 0, f"{count} unproven message channel(s):\n{describe(found)}"


def test_every_exemption_names_a_channel_the_derivation_found() -> None:
    """An exemption for a channel that does not exist grades nothing."""
    known = {c.key for c in scan_channels(live_index())}
    unknown = sorted(set(EXEMPT) - known)
    assert unknown == [], f"exemption(s) naming no channel in the population: {unknown}"


def test_every_exemption_states_a_reason() -> None:
    """A blank reason is a rubber stamp with a key on it."""
    thin = sorted(
        key for key, reason in EXEMPT.items() if len(reason.strip()) < MINIMUM_REASON_CHARS
    )
    assert thin == [], f"exemption(s) with no stated reason: {thin}"


def test_every_identifier_an_exemption_cites_exists_in_the_module_it_names() -> None:
    """A REASON MAY NOT CITE CODE THAT DOES NOT EXIST.

    The length check above is satisfied by forty spaces. In the sibling module
    EVERY reason replaced with forty literal characters passed every arm,
    which is how a reason shipped citing a private helper that has never
    existed in this repository. Only tokens carrying an underscore are
    checked: that separates an identifier from an English word without needing
    a list of English words, and it is the class the fabricated citation
    belonged to.
    """
    identifier = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    missing: list[str] = []
    for key, reason in EXEMPT.items():
        module = key.split("::", 1)[0]
        source = (REPO_ROOT / module).read_text(encoding="utf-8")
        for token in identifier.findall(reason):
            if "_" not in token or token in _REASON_PROSE:
                continue
            if token not in source:
                missing.append(f"{key} cites {token!r}, absent from {module}")
    assert missing == [], "exemption(s) citing code that does not exist:\n" + "\n".join(missing)


def test_a_repaired_exemption_is_reported_rather_than_reddening() -> None:
    """BOTH DIRECTIONS, and this one WARNS.

    Failing here would need every exempted channel to still be unproven,
    which is the anti-monotone shape: repairing one would turn the proof red.
    The reporter is graded on a fabricated record, because a clean result on
    the live record is also what a reporter that returns nothing produces.
    """
    fabricated = {"clockspeed/save/nowhere.py::NoSuchError::field": "a key naming nothing"}
    reported = stale_exemptions(live_index(), fabricated)
    assert reported == ("clockspeed/save/nowhere.py::NoSuchError::field",), (
        f"the stale-exemption reporter does not report a fabricated key: {reported}"
    )
    assert stale_exemptions(live_index(), {}) == (), "an empty record cannot be stale"

    stale = stale_exemptions(live_index(), EXEMPT)
    if stale:
        lines = "\n".join(f"  stale EXEMPT key, remove it: {key!r}" for key in stale)
        warnings.warn(f"{len(stale)} exemption(s) no longer needed:\n{lines}", stacklevel=1)


def test_the_live_tree_has_a_class_governed_by_an_inherited_initialiser() -> None:
    """RULE E1 HAS A LIVE SUBJECT, and the base resolution is not decoration.

    A shipped error that ships no ``__init__`` of its own has its ``args``
    built by one it inherits. If the live tree held none of those, the base
    resolution would be exercised only by the corpus above and could be
    removed without any live class going ungraded - so the rule would be
    green while measuring nothing. Asserted NON-EMPTY rather than pinned to a
    number: a count in prose is the defect this arm's own docstring once
    carried, and adding a subclass must not redden anything.
    """
    governed = {
        c.class_key
        for c in scan_channels(live_index())
        if c.shape == SHAPE_STRUCTURED and c.governed_by != c.class_key
    }
    assert governed, (
        "no shipped error inherits its initialiser, so resolving the "
        "governing initialiser through the bases grades nothing live"
    )


def test_both_message_building_shapes_are_present_in_the_live_tree() -> None:
    """A RULE WITH NO SUBJECT IS NOT A RULE.

    The free-text half exists to grade classes whose message is built at the
    raise site. If every live class were structured, that half would be
    exercised only by the corpora above and could rot unnoticed.
    """
    shapes = {c.shape for c in scan_channels(live_index())}
    assert SHAPE_STRUCTURED in shapes, sorted(shapes)
    assert SHAPE_FREE_TEXT in shapes, sorted(shapes)


def test_the_proof_forms_in_use_are_recorded_in_both_directions() -> None:
    """THE ASYMMETRY IS MEASURED, NOT ARGUED.

    ``PROVEN_VOCABULARY`` is a RUNTIME barrier - the value is refused before
    it reaches the message. ``PROVEN_AT_SITES`` is a STATIC fact about today's
    call sites and nothing stops a new caller. Both are proofs and they are
    not the same proof, so the set in use is pinned: a class silently
    downgraded from the first to the second reddens here.
    """
    verdicts = {c.verdict for c in scan_channels(live_index())}
    assert PROVEN_VOCABULARY in verdicts, sorted(verdicts)
    assert PROVEN_AT_SITES in verdicts, sorted(verdicts)
    assert PROVEN_SCALAR in verdicts, sorted(verdicts)
    assert verdicts <= {
        PROVEN_AT_SITES,
        PROVEN_LITERAL,
        PROVEN_SCALAR,
        PROVEN_VOCABULARY,
        UNPROVEN,
    }, sorted(verdicts)


def test_the_vocabularies_the_rule_reads_are_not_empty() -> None:
    """An emptied vocabulary makes the whole derivation silently clean."""
    assert ARGS_ROOTS, "no exception root - nothing reaches BaseException.args"
    assert "Exception" in ARGS_ROOTS
    assert "OSError" in ARGS_ROOTS
    assert COMPOSING_CALLS, "no composing call - every f-string wrapper is opaque"
    assert "join" in COMPOSING_CALLS
    assert "str" in COMPOSING_CALLS


# ---------------------------------------------------------------------------
# Forced rendering - what the interpreter actually puts in args
# ---------------------------------------------------------------------------


class _LeakyError(Exception):
    """A synthetic error that interpolates whatever it is handed."""

    def __init__(self, value: str) -> None:
        """Build a message from the value.

        Args:
            value: Anything at all.
        """
        super().__init__(f"cannot read {value}")


def test_a_planted_marker_reaches_args_on_a_synthetic_error() -> None:
    """THE POSITIVE CONTROL, and without it every arm below proves nothing.

    ``BaseException.__repr__`` renders ``args`` and ``__str__`` renders it
    too, which is the whole premise of this module. Measuring it on a class
    authored here proves the DETECTION works before any real class is asked to
    withhold - ``assert MARKER not in rendered`` is satisfied by a subject
    that never carried one.
    """
    exc = _LeakyError(MARKER)
    assert MARKER in str(exc), "__str__ does not render args - the premise is wrong"
    assert MARKER in repr(exc), "__repr__ does not render args - the premise is wrong"
    assert MARKER in str(exc.args), "the marker never reached args"


#: Initialisers whose text channel is proven ONLY by its call sites, keyed by
#: the GOVERNING class and the keyword the channel arrives on, with the rest of
#: a valid construction. Hand-written because a constructor signature is not in
#: an annotation, and cross-checked against the derivation by
#: ``test_every_governing_class_with_an_at_site_channel_is_forced``.
FORCED_AT_SITES: Final[dict[str, tuple[type[Exception], str, dict[str, object]]]] = {
    "clockspeed/save/chunks.py::ChunkError::field": (
        ChunkError,
        "field",
        {"reason": REASON_BAD_MAGIC, "offset": 0},
    ),
    "clockspeed/save/header.py::HeaderReadError::reason": (
        HeaderReadError,
        "reason",
        {"redacted_path": "<work>/copy", "errno": 2},
    ),
    "clockspeed/save/objects.py::ObjectError::reason": (
        ObjectError,
        "reason",
        {"field": "object_count", "offset": 0},
    ),
    "clockspeed/save/usmap.py::UsmapFormatError::field": (
        UsmapFormatError,
        "field",
        {"offset": 0, "reason": "the file ends before this field"},
    ),
    "clockspeed/save/world.py::WorldLoadError::stage": (
        WorldLoadError,
        "stage",
        {"cause_type": "OSError"},
    ),
}

#: Initialisers whose text channel is narrowed by a closed vocabulary, keyed
#: the same way, with the refusal each one is expected to raise. The refusal
#: text is part of the record because two DIFFERENT vocabularies are in play
#: and a single expected message would let one of them pass on the other's
#: error.
FORCED_VOCABULARY: Final[dict[str, tuple[type[Exception], str, dict[str, object], str]]] = {
    "clockspeed/save/header.py::HeaderFormatError::field": (
        HeaderFormatError,
        "field",
        {"offset": 0, "reason": REASON_DECLARED_LENGTH_ABOVE_CAP},
        "field name is not one of the",
    ),
    "clockspeed/save/header.py::HeaderFormatError::reason": (
        HeaderFormatError,
        "reason",
        {"field": "header_version", "offset": 0},
        "reason is not one of this module's fixed format reasons",
    ),
    "clockspeed/save/header.py::HeaderTruncatedError::field": (
        HeaderTruncatedError,
        "field",
        {"offset": 0, "needed": 4, "available": 0},
        "field name is not one of the",
    ),
    "clockspeed/save/objects.py::ObjectError::field": (
        ObjectError,
        "field",
        {"reason": "extends past the end of the supplied body", "offset": 0},
        "field name is not one of the",
    ),
}


@pytest.mark.parametrize("key", sorted(FORCED_AT_SITES))
def test_a_channel_proven_only_at_its_sites_is_not_a_runtime_barrier(key: str) -> None:
    """THE ASYMMETRY, MEASURED ON THE SHIPPED CLASSES.

    A call-site proof says every caller in THIS tree passes an authored
    constant. It says nothing about a caller added tomorrow, and the
    interpreter enforces nothing: the planted value goes straight into
    ``args`` and out through ``__str__``. Asserting the disclosure here is
    what stops the weaker proof being read as the stronger one, and it is the
    positive control for the vocabulary arm below - the same planting that
    renders here is refused there.
    """
    kind, channel, rest = FORCED_AT_SITES[key]
    exc = kind(**{channel: MARKER}, **rest)
    assert MARKER in str(exc), (
        f"{key} was expected to render a planted {channel}; if it now refuses "
        "one, it gained a runtime check and belongs in FORCED_VOCABULARY"
    )
    assert MARKER in repr(exc), f"{key} renders the marker through __str__ but not __repr__"


@pytest.mark.parametrize("key", sorted(FORCED_VOCABULARY))
def test_a_channel_narrowed_by_a_vocabulary_refuses_a_planted_marker(key: str) -> None:
    """The runtime half of the narrowing, measured rather than read.

    The static rule sees a membership test in the syntax tree. This confirms
    the test actually RUNS, on the shipped class, before the message exists.
    """
    kind, channel, rest, refusal = FORCED_VOCABULARY[key]
    with pytest.raises(ValueError, match=re.escape(refusal)):
        kind(**{channel: MARKER}, **rest)


@pytest.mark.parametrize("key", sorted(FORCED_AT_SITES))
def test_a_forced_subject_actually_carries_the_marker(key: str) -> None:
    """A subject built without the marker satisfies every assertion about it.

    Read back off the CONSTRUCTED INSTANCE rather than off the dictionary that
    was passed, so a class that silently dropped the channel is caught instead
    of certified.
    """
    kind, channel, rest = FORCED_AT_SITES[key]
    exc = kind(**{channel: MARKER}, **rest)
    assert MARKER in repr(vars(exc)), f"{key} did not retain the planted {channel}"


@pytest.mark.parametrize("key", sorted(FORCED_VOCABULARY))
def test_a_vocabulary_subject_is_refused_on_the_marker_and_not_on_its_neighbours(
    key: str,
) -> None:
    """THE NEGATIVE HALF, without which the refusal arm proves nothing.

    ``pytest.raises`` is satisfied by a construction that would have failed
    anyway - a bad neighbouring argument, a wrong keyword, a typo in the
    record. Building the SAME subject with the marker replaced by a legitimate
    value has to SUCCEED, which is what pins the refusal on the planted
    channel rather than on the rest of the call.
    """
    kind, channel, rest, _ = FORCED_VOCABULARY[key]
    legitimate = {
        "field": {"clockspeed/save/objects.py": "object_count"}.get(
            key.split("::", 1)[0], "header_version"
        ),
        "reason": REASON_DECLARED_LENGTH_ABOVE_CAP,
    }[channel]
    exc = kind(**{channel: legitimate}, **rest)
    assert str(exc), f"{key} built cleanly from legitimate arguments but rendered nothing"


def test_every_governing_class_with_an_at_site_channel_is_forced() -> None:
    """The hand-written half cannot fall behind the derived half.

    Keyed on the GOVERNING class rather than on every class, because a class
    that ships no initialiser of its own shares a base's message path -
    forcing each subclass separately would measure the same path repeatedly
    while reading as broader coverage than it is.
    """
    derived = {c.governed_by for c in scan_channels(live_index()) if c.verdict == PROVEN_AT_SITES}
    forced = {key.rsplit("::", 1)[0] for key in FORCED_AT_SITES}
    missing = sorted(derived - forced)
    assert missing == [], f"at-site initialiser(s) the forced arm never constructs: {missing}"


def test_every_governing_class_with_a_vocabulary_channel_is_forced() -> None:
    """The same coverage requirement for the stronger proof form.

    Without it the vocabulary arms could measure two narrowings while a third
    was silently removed, and nothing would say so.
    """
    derived = {c.governed_by for c in scan_channels(live_index()) if c.verdict == PROVEN_VOCABULARY}
    forced = {key.rsplit("::", 1)[0] for key in FORCED_VOCABULARY}
    missing = sorted(derived - forced)
    assert missing == [], f"narrowing initialiser(s) the forced arm never exercises: {missing}"


# ---------------------------------------------------------------------------
# The measurements two exemptions rest on
# ---------------------------------------------------------------------------


def test_an_oserror_carries_its_errno_as_an_integer() -> None:
    """BACKS THE ``exc.errno`` EXEMPTIONS in ``tests/exception_message_guard.py``.

    Two shipped refusals render ``exc.errno`` beside ``type(exc).__name__``.
    An attribute read carries no annotation, so the static rule cannot prove
    the value is a number and the exemption asserts it in prose. This measures
    it instead, and it is machine-independent: the errno is set by the
    constructor rather than read off this filesystem.
    """
    raised = OSError(2, "no such file")
    assert isinstance(raised.errno, int), "errno is not an integer - the exemption is wrong"
    assert MARKER not in str(raised.errno)


def test_the_forbidden_root_label_is_a_module_constant_at_every_site() -> None:
    """BACKS THE ``root.label`` EXEMPTION in ``tests/exception_message_guard.py``.

    The refusal renders ``root.label``. The value arrives by iterating a list
    the producer returns, which is flow the syntactic rule does not model, so
    the exemption records a judgement. This is the measurement behind it: the
    producer's candidate list pairs each root with a MODULE-LEVEL name, every
    such name is bound to a literal in the same module, and every
    ``ForbiddenRoot`` built there takes its label from that pairing.
    """
    index = live_index()
    literals = index.literals[WORKDIR_MODULE]
    producers = [n for m, n in index.functions.get("_forbidden_roots", []) if m == WORKDIR_MODULE]
    assert len(producers) == 1, f"expected one producer of a forbidden root, found {len(producers)}"

    pairs = [
        element
        for node in ast.walk(producers[0])
        if isinstance(node, ast.List)
        for element in node.elts
        if isinstance(element, ast.Tuple) and len(element.elts) == _CANDIDATE_PAIR_WIDTH
    ]
    assert pairs, "the producer builds no candidate pairs - this arm is measuring nothing"
    labels = {second.id for pair in pairs if isinstance(second := pair.elts[1], ast.Name)}
    assert len(labels) == len(pairs), (
        f"a candidate pairs its root with something other than a bare name: {len(pairs)} pairs, "
        f"{sorted(labels)}"
    )
    outside = sorted(name for name in labels if name not in literals)
    assert outside == [], f"root label(s) that are not module-level literals: {outside}"

    carried = {
        node.target.elts[1].id
        for node in ast.walk(producers[0])
        if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
        if len(node.target.elts) == _CANDIDATE_PAIR_WIDTH
        if isinstance(node.target.elts[1], ast.Name)
    }
    assert len(carried) == 1, f"expected one loop carrying the pairs, found {sorted(carried)}"

    sites = [c for m, c, _ in index.calls.get("ForbiddenRoot", []) if m == WORKDIR_MODULE]
    assert sites, "no ForbiddenRoot is built in the module that renders its label"
    bound = {
        keyword.value.id
        for call in sites
        for keyword in call.keywords
        if keyword.arg == "label" and isinstance(keyword.value, ast.Name)
    }
    assert bound == carried, (
        "the label a ForbiddenRoot is built with is not the loop variable the "
        f"producer pairs a module constant into: built from {sorted(bound)}, "
        f"carried as {sorted(carried)}"
    )


def test_the_collision_census_reports_a_real_collision() -> None:
    """THE POSITIVE CONTROL for the census the arm below consumes.

    An empty result on the live tree is also what a census that looks at
    nothing returns. This runs it over a corpus built to collide.
    """
    index = build_index(_COLLIDING_CLASS_NAME)
    assert colliding_class_names(index) == ("ReaderError",), colliding_class_names(index)


def test_no_class_name_the_derivation_resolves_is_ambiguous() -> None:
    """A BASE IS A BARE WORD, so a duplicated class name makes it ambiguous.

    Resolving a base properly would mean resolving imports, which this
    module does not do. So a class name declared in two modules makes
    every answer about it ambiguous - which base a subclass reaches, which
    initialiser governs it, which construction sites are its own.

    MEASURED on this tree: two collisions exist and NEITHER is an error
    name or a base of one, so the ambiguity does not reach this module's
    answers today. The assertion is the narrow property rather than the
    wide census, because reddening on a correct tree is how a guard gets
    switched off - and the wide census is printed in the message so the
    reader sees what was tolerated.
    """
    index = live_index()
    ambiguous = ambiguous_error_names(index)
    assert ambiguous == (), (
        "class name(s) the derivation resolves are declared in more than "
        f"one module, so every answer about them is ambiguous: {ambiguous}. "
        f"Full collision census: {colliding_class_names(index)}"
    )


def test_no_resolved_callee_name_is_ambiguous() -> None:
    """CALL SITES ARE POOLED BY NAME, AND THE PRECONDITION IS MEASURED.

    Two shipped functions sharing a name pool their sites, and a positional
    argument is then bound against one of the two signatures. MEASURED on this
    tree: ``_render`` and ``_checked_field`` are each declared twice, once per
    parser layer, with identical parameter names - so the pooling is harmless
    today. This arm is what turns that into a fact the tree has to keep.

    THE ZERO IS OVER THE NAMES THE WALK RECORDED, not over every name in the
    tree. ``resolved_callees`` is filled while grading, by the syntactic
    callee word at each site, so a callee the walk never reached is not
    counted as unambiguous - it is not counted at all. The non-emptiness
    assertion below is what stops that from reading as a clean sweep.
    """
    index = live_index()
    scan_channels(index)
    resolved = resolved_callees(index)
    assert resolved, "the walk resolved through no callee at all - it is not following anything"
    assert ambiguous_callees(index) == (), (
        "callee name(s) whose shipped definitions disagree on parameter names, "
        f"so a pooled call site can bind the wrong argument: {ambiguous_callees(index)}"
    )
