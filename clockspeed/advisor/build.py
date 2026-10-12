"""CS-1288 slice C0: the build inputs, and the build caveat every priced rule reads.

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
- :func:`build_caveat` is what a rule calls FIRST. It reads the three inputs,
  cross-checks the warning codes against the two builds, and returns the text
  the rule appends to its reason - empty on the pin.

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
the uncompared code alone with no pin. Anything else - a code the builds do not
imply, a missing or extra code, a bool posing as an int, a value of any other
exact type - raises, and the engine records a ``rule-error`` and drops the
card (non-negotiable 7). The detail line is checked only for its type here;
the engine refuses one that is not printable ASCII text.

THE PIN IS A PARAMETER, NEVER AN IMPORT (``clockspeed/audit/build.py`` states
it, and ruling F2 carries it into this layer). Nothing here imports
``clockspeed.data``; the caller hands the audit the pin and this module reads
the check. Nothing here imports ``clockspeed.advisor.rules`` either (ruling
F3): every rule family imports this module, never the reverse.

NO WORLD VALUE, NO PATH, NO ENVIRONMENT VALUE IN TEXT. The returned text names
a warning code and two changelists, both ints, rendered by ``str``; the
indeterminate step carries the audit's fixed detail, which is never built from
anything read out of a save.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.advisor.trace import InputValue
from clockspeed.audit.build import WARN_BUILD_MISMATCH, WARN_BUILD_UNCOMPARED

if TYPE_CHECKING:
    from clockspeed.advisor.trace import RuleContext
    from clockspeed.audit.build import BuildCheck

__all__ = [
    "BUILD_INPUTS",
    "IN_PINNED_CHANGELIST",
    "IN_SAVE_CHANGELIST",
    "IN_WARNINGS",
    "build_caveat",
    "build_inputs",
]

#: The save's build changelist, an ``int``.
IN_SAVE_CHANGELIST: Final = "build.save_changelist"

#: The pinned build's changelist, an ``int``, or None when no pin parsed.
IN_PINNED_CHANGELIST: Final = "build.pinned_changelist"

#: The audit's warnings: a ``MappingProxyType`` of code to its fixed detail line.
IN_WARNINGS: Final = "build.warnings"

#: Every input :func:`build_caveat` reads, in the order it reads them. A rule
#: that calls it declares all three.
BUILD_INPUTS: Final = (IN_SAVE_CHANGELIST, IN_PINNED_CHANGELIST, IN_WARNINGS)

_SOURCE_PREFIX: Final = "audit.build."

#: The alternative an off-pin run records as indeterminate.
_NAMEPLATE_ALTERNATIVE: Final = "present a nameplate figure as the save build's own"


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


def build_caveat(ctx: RuleContext) -> str:
    """Read the build inputs, record what an off-pin build leaves undecided, and say so.

    Call it FIRST, before any other read, from a rule that declares every name
    in :data:`BUILD_INPUTS`: tier 3 then opens with the three build reads, each
    with its source.

    Args:
        ctx: The rule's context.

    Returns:
        The empty string on the pin, recording nothing beyond the three reads.
        Off the pin, ``"; build-mismatch: priced at the pinned build <pin>,
        not the save build <save>"``; with no pin, ``"; build-uncompared: the
        save build <save> was never compared, as no pinned build exists"`` -
        each after recording ONE indeterminate step that carries the audit's
        detail line. The rule appends it to its reason.

    Raises:
        TypeError: A changelist is not exactly an ``int`` (the pin may be
            None), or the warnings are not a read-only mapping of text to text.
        ValueError: The warning codes are not exactly the one the two builds
            imply - none when they are equal.
    """
    save = _changelist(ctx.read(IN_SAVE_CHANGELIST), absent_allowed=False)
    pin = _changelist(ctx.read(IN_PINNED_CHANGELIST), absent_allowed=True)
    warnings = _warnings(ctx.read(IN_WARNINGS))

    if pin is None:
        implied: str | None = WARN_BUILD_UNCOMPARED
    elif save != pin:
        implied = WARN_BUILD_MISMATCH
    else:
        implied = None

    expected = set() if implied is None else {implied}
    if set(warnings) != expected:
        raise ValueError("the build warnings disagree with the two builds")
    if implied is None:
        return ""

    ctx.indeterminate(_NAMEPLATE_ALTERNATIVE, warnings[implied])
    if implied == WARN_BUILD_MISMATCH:
        return (
            f"; {WARN_BUILD_MISMATCH}: priced at the pinned build {pin}, not the save build {save}"
        )
    return (
        f"; {WARN_BUILD_UNCOMPARED}: the save build {save} was never compared,"
        " as no pinned build exists"
    )
