"""CS-1288 slice C0 and CS-1315: the build inputs, and the build caveat every priced rule reads.

WHAT THIS MODULE OWNS. The seam between ``clockspeed/audit/build.py`` and the
advice rules. Every nameplate figure the audit prices is the PINNED build's
nameplate, and a save written by another build is priced at it whether or not
it was the save build's own. So every advice card computed from such a figure
has to say so (the CS-1288 acceptance in ``docs/history_notes.md`` section
CS-1288, relocated there from ``docs/item_notes/phase5.md`` on the item's close:
"no figure is silently presented as the save build's own"). Two functions:

- :func:`build_inputs` flattens the audit's
  :class:`clockspeed.audit.build.BuildCheck` into the three rule inputs
  :data:`BUILD_INPUTS`, each sourced to the audit field it came from, so tier 3
  shows every one as a read with its source (session 138 ruling F4).
- :func:`registry_inputs` (CS-1315) flattens the audit's
  :class:`clockspeed.audit.build.RegistryCheck` into the three rule inputs
  :data:`REGISTRY_INPUTS` - the registry's source hash, the pinned docs hash
  and the registry warnings - each sourced to its audit field on the same
  terms. :data:`BUILD_INPUTS` is the build check's three followed by these.
- :func:`build_caveat` is what a rule calls FIRST. It reads all six inputs,
  cross-checks each group's warning codes against the facts beside them, and
  returns the text the rule appends to its reason - empty on the pin with a
  verified registry.

THE REGISTRY'S SOURCE IS THE SAME CAVEAT ONE LAYER DOWN (CS-1315). Every
nameplate figure is priced from the registry, and the registry is built from
the INSTALLED docs file. A registry built from bytes other than the pinned
build's records one more ``verdict-indeterminate`` step under
:data:`clockspeed.audit.build.WARN_REGISTRY_MISMATCH`, and a registry with no
byte source - or no pinned docs hash - does so under
:data:`clockspeed.audit.build.WARN_REGISTRY_UNVERIFIED`, so nothing is priced
from an unverified registry silently and such a run settles nothing. The
comparison is of content hashes only: a build-only difference with equal bytes
raises no registry code (the session 140 ruling).

OFF THE PIN THE VERDICT IS INDETERMINATE, AND THE CARD STILL FIRES (ruling
F1). A run whose builds differ records ONE ``verdict-indeterminate`` step,
right after the three reads, carrying the audit's own fixed detail line; it is
recorded whether the rule then fires or stays silent. That step kind is outside
``clockspeed/advisor/advise.py::SETTLED_STEP_KINDS``, so an off-pin run never
settles its rule and ``Ledger.reconcile`` never completes a card on figures
priced at another build. A run with NO pin takes the same path under
:data:`clockspeed.audit.build.WARN_BUILD_UNCOMPARED`, and its text never uses
the mismatch wording: with no pin there is no pinned build to name.

A DISAGREEMENT IS A RULE ERROR, NEVER A GUESS. The warnings must be EXACTLY
what the two builds imply - none on the pin, the mismatch code alone off it,
the uncompared code alone with no pin - and the registry warnings EXACTLY what
the two hashes imply - none when they are equal, the registry mismatch code
alone when they differ, the unverified code alone when either is absent or
empty. Anything else - a code the facts do not imply, a missing or extra code,
a code of the other group, a bool posing as an int, a hash that is not text, a
value of any other exact type - raises, before any indeterminate step is
recorded, and the engine records a ``rule-error`` and drops the card
(non-negotiable 7). The detail line is checked only for its type here;
the engine refuses one that is not printable ASCII text.

THE PIN IS A PARAMETER, NEVER AN IMPORT (``clockspeed/audit/build.py`` states
it, and ruling F2 carries it into this layer). Nothing here imports
``clockspeed.data``; the caller hands the audit the pin and this module reads
the check. Nothing here imports ``clockspeed.advisor.rules`` either (ruling
F3): every rule family imports this module, never the reverse.

NO WORLD VALUE, NO PATH, NO ENVIRONMENT VALUE IN TEXT. The returned text names
a warning code and two changelists, both ints, rendered by ``str``, and the
registry text names its code alone - the two hashes are shown by tier 3's
reads, never written into the reason; the indeterminate step carries the
audit's fixed detail, which is never built from anything read out of a save.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.trace import InputValue
from clockspeed.audit.build import (
    WARN_BUILD_MISMATCH,
    WARN_BUILD_UNCOMPARED,
    WARN_REGISTRY_MISMATCH,
    WARN_REGISTRY_UNVERIFIED,
)

if TYPE_CHECKING:
    from clockspeed.advisor.trace import RuleContext
    from clockspeed.audit.build import BuildCheck, RegistryCheck

__all__ = [
    "BUILD_CHECK_INPUTS",
    "BUILD_INPUTS",
    "IN_PINNED_CHANGELIST",
    "IN_PINNED_DOCS_SHA256",
    "IN_REGISTRY_SHA256",
    "IN_REGISTRY_WARNINGS",
    "IN_SAVE_CHANGELIST",
    "IN_WARNINGS",
    "REGISTRY_INPUTS",
    "build_caveat",
    "build_inputs",
    "registry_inputs",
]

#: The save's build changelist, an ``int``.
IN_SAVE_CHANGELIST: Final = "build.save_changelist"

#: The pinned build's changelist, an ``int``, or None when no pin parsed.
IN_PINNED_CHANGELIST: Final = "build.pinned_changelist"

#: The audit's warnings: a ``MappingProxyType`` of code to its fixed detail line.
IN_WARNINGS: Final = "build.warnings"

#: The sha256 of the docs bytes the registry was built from, a ``str``, or None
#: when the registry had no byte source (CS-1315).
IN_REGISTRY_SHA256: Final = "build.registry_sha256"

#: The pinned docs hash, a ``str``, or None when the pin carries none.
IN_PINNED_DOCS_SHA256: Final = "build.pinned_docs_sha256"

#: The registry check's warnings: a ``MappingProxyType`` of code to detail line.
IN_REGISTRY_WARNINGS: Final = "build.registry_warnings"

#: The build check's three inputs, as :func:`build_inputs` offers them.
BUILD_CHECK_INPUTS: Final = (IN_SAVE_CHANGELIST, IN_PINNED_CHANGELIST, IN_WARNINGS)

#: The registry check's three inputs, as :func:`registry_inputs` offers them.
REGISTRY_INPUTS: Final = (IN_REGISTRY_SHA256, IN_PINNED_DOCS_SHA256, IN_REGISTRY_WARNINGS)

#: Every input :func:`build_caveat` reads, in the order it reads them. A rule
#: that calls it declares all six.
BUILD_INPUTS: Final = (*BUILD_CHECK_INPUTS, *REGISTRY_INPUTS)

_SOURCE_PREFIX: Final = "audit.build."

#: Where the registry inputs are sourced: the registry check in the same module.
_REGISTRY_SOURCE_PREFIX: Final = "audit.build.registry."

#: The alternative an off-pin run records as indeterminate.
_NAMEPLATE_ALTERNATIVE: Final = "present a nameplate figure as the save build's own"

#: The alternative a run over an unchecked registry records as indeterminate.
_REGISTRY_ALTERNATIVE: Final = "present a nameplate figure as the pinned build's own"


def build_inputs(check: BuildCheck) -> dict[str, InputValue]:
    """Offer one world's build check as rule inputs, each sourced to its audit field.

    The caller merges the result beside the other families' inputs; a fresh
    dict is returned so it may.

    Args:
        check: The audit's build check.

    Returns:
        Exactly the three inputs of :data:`BUILD_INPUTS`.
    """
    warnings = MappingProxyType({warning.code: warning.detail for warning in check.warnings})
    fields: tuple[tuple[str, str, object], ...] = (
        (IN_SAVE_CHANGELIST, "save_changelist", check.save_changelist),
        (IN_PINNED_CHANGELIST, "pinned_changelist", check.pinned_changelist),
        (IN_WARNINGS, "warnings", warnings),
    )
    return {name: InputValue(value, _SOURCE_PREFIX + field) for name, field, value in fields}


def registry_inputs(check: RegistryCheck) -> dict[str, InputValue]:
    """Offer one registry check as rule inputs, each sourced to its audit field.

    The caller merges the result beside :func:`build_inputs`'s; a fresh dict is
    returned so it may.

    Args:
        check: The audit's registry check.

    Returns:
        Exactly the three inputs of :data:`REGISTRY_INPUTS`.
    """
    warnings = MappingProxyType({warning.code: warning.detail for warning in check.warnings})
    fields: tuple[tuple[str, str, object], ...] = (
        (IN_REGISTRY_SHA256, "source_sha256", check.source_sha256),
        (IN_PINNED_DOCS_SHA256, "pinned_sha256", check.pinned_sha256),
        (IN_REGISTRY_WARNINGS, "warnings", warnings),
    )
    return {
        name: InputValue(value, _REGISTRY_SOURCE_PREFIX + field) for name, field, value in fields
    }


def _digest(value: object) -> str | None:
    """Return a hash read from an input, or None when it is absent or empty.

    Args:
        value: The value read.

    Returns:
        The hash, or None for None or the empty string - absent, as the audit
        reads it.

    Raises:
        TypeError: The value is neither None nor exactly a ``str``.
    """
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError("a docs hash input is not exactly a str")
    return value or None


def _changelist(value: object, *, absent_allowed: bool) -> int | None:
    """Return a changelist read from an input, refusing anything but an exact int.

    Args:
        value: The value read.
        absent_allowed: Whether None is admitted - the pin only.

    Returns:
        The changelist, or None when admitted and absent.

    Raises:
        TypeError: The value is not exactly an ``int`` (a bool is refused) or
            an admitted None.
    """
    if value is None and absent_allowed:
        return None
    if type(value) is not int:
        raise TypeError("a build changelist input is not exactly an int")
    return value


def _warnings(value: object) -> dict[str, str]:
    """Return the warnings read from an input as code to detail, refusing any other shape.

    Args:
        value: The value read.

    Returns:
        A plain copy of the mapping.

    Raises:
        TypeError: The value is not exactly a ``MappingProxyType`` of ``str``
            to ``str``.
    """
    if type(value) is not MappingProxyType:
        raise TypeError("the build warnings input is not a read-only mapping")
    copied: dict[object, object] = dict(value)
    if not all(type(key) is str and type(item) is str for key, item in copied.items()):
        raise TypeError("the build warnings input does not map text codes to text details")
    return {str(key): str(item) for key, item in copied.items()}


def _implied(codes: dict[str, str], implied: str | None, disagreement: str) -> None:
    """Refuse warning codes that are not exactly the one the facts imply.

    Args:
        codes: The warnings read, code to detail.
        implied: The one code the facts imply, or None for none.
        disagreement: The refusal message - fixed text, never a value.

    Raises:
        ValueError: The codes are not exactly ``{implied}``, or empty for None.
    """
    expected = set() if implied is None else {implied}
    if set(codes) != expected:
        raise ValueError(disagreement)


def build_caveat(ctx: RuleContext) -> str:
    """Read the build inputs, record what an off-pin build or registry leaves undecided, and say so.

    Call it FIRST, before any other read, from a rule that declares every name
    in :data:`BUILD_INPUTS`: tier 3 then opens with the six build reads, each
    with its source.

    Args:
        ctx: The rule's context.

    Returns:
        The empty string on the pin over a verified registry, recording
        nothing beyond the six reads. Off the pin, ``"; build-mismatch: priced
        at the pinned build <pin>, not the save build <save>"``; with no pin,
        ``"; build-uncompared: the save build <save> was never compared, as no
        pinned build exists"``. Then, over a registry built from other bytes,
        ``"; registry-mismatch: priced from a registry whose docs differ from
        the pinned build's"``; over one with no byte source or no pinned docs
        hash, ``"; registry-unverified: priced from a registry never checked
        against the pinned docs"``. Each part follows ONE indeterminate step
        that carries the audit's detail line, build first. The rule appends
        the whole to its reason.

    Raises:
        TypeError: A changelist is not exactly an ``int`` (the pin may be
            None), a hash is neither None nor exactly a ``str``, or a warnings
            input is not a read-only mapping of text to text.
        ValueError: A group's warning codes are not exactly the one its facts
            imply - none when they agree.
    """
    save = _changelist(ctx.read(IN_SAVE_CHANGELIST), absent_allowed=False)
    pin = _changelist(ctx.read(IN_PINNED_CHANGELIST), absent_allowed=True)
    warnings = _warnings(ctx.read(IN_WARNINGS))
    source = _digest(ctx.read(IN_REGISTRY_SHA256))
    pinned_docs = _digest(ctx.read(IN_PINNED_DOCS_SHA256))
    registry_warnings = _warnings(ctx.read(IN_REGISTRY_WARNINGS))

    if pin is None:
        implied: str | None = WARN_BUILD_UNCOMPARED
    elif save != pin:
        implied = WARN_BUILD_MISMATCH
    else:
        implied = None

    if source is None or pinned_docs is None:
        implied_registry: str | None = WARN_REGISTRY_UNVERIFIED
    elif source != pinned_docs:
        implied_registry = WARN_REGISTRY_MISMATCH
    else:
        implied_registry = None

    _implied(warnings, implied, "the build warnings disagree with the two builds")
    _implied(
        registry_warnings, implied_registry, "the registry warnings disagree with the two hashes"
    )

    text = ""
    if implied is not None:
        ctx.indeterminate(_NAMEPLATE_ALTERNATIVE, warnings[implied])
        if implied == WARN_BUILD_MISMATCH:
            text += (
                f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin},"
                f" not the save build {save}"
            )
        else:
            text += (
                f"; {WARN_BUILD_UNCOMPARED}: the save build {save} was never compared,"
                " as no pinned build exists"
            )
    if implied_registry is not None:
        ctx.indeterminate(_REGISTRY_ALTERNATIVE, registry_warnings[implied_registry])
        if implied_registry == WARN_REGISTRY_MISMATCH:
            text += (
                f"; {WARN_REGISTRY_MISMATCH}: priced from a registry whose docs differ"
                " from the pinned build's"
            )
        else:
            text += (
                f"; {WARN_REGISTRY_UNVERIFIED}: priced from a registry never checked"
                " against the pinned docs"
            )
    return text
