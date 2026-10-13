"""Which game build wrote the save, held beside the build this project is pinned to.

WHAT THIS MODULE OWNS
-----------------------
One pure function over one ``clockspeed.save.world.WorldModel`` and one pinned
changelist, returning a frozen :class:`BuildCheck` that holds BOTH builds side
by side and says whether they were compared and whether they agree. It is the
first half of CS-1288: every nameplate figure the audit layer computes -
``clockspeed/audit/balance.py`` prices draw and clocked draw from the registry -
is the PINNED build's nameplate, and a save written by another build is priced
at that nameplate whether or not it was the save build's own.

IT PRICES NOTHING AND INFERS NOTHING. No registry is read here, no figure is
recomputed, and no older build's nameplate is guessed. This model states the
two builds and the relation between them; a consumer that presents a
nameplate-derived figure carries :data:`WARN_BUILD_MISMATCH` beside it so the
figure reads as priced at the pinned build rather than as the save build's own.

THE PIN IS A PARAMETER, NEVER AN IMPORT. ``clockspeed/data/version.py`` owns the
pin, and the audit layer consumes the save model and the solve results only
(``clockspeed/audit/__init__.py`` states the seam). So the caller passes the
pinned changelist in, and a pin that did not parse arrives as None.

THREE OUTCOMES, AND NONE IS FOLDED INTO ANOTHER
-------------------------------------------------
- The builds differ: :data:`WARN_BUILD_MISMATCH`.
- The pin is None: :data:`WARN_BUILD_UNCOMPARED`, and :attr:`BuildCheck.matches`
  reads False. An absent pin is NEVER a match - reading it as one would present
  every nameplate figure as the save build's own on exactly the run where
  nothing checked, which is the silent-wrong answer non-negotiable 7 forbids.
- The builds are equal: no warning at all.

A pin that is not an int is REFUSED with ``TypeError`` rather than compared: a
string spelling of the save's own build compares unequal to it and would raise
the mismatch code over two equal builds, and a bool is an int subclass that
would compare equal to 0 or 1.

THE DETAIL IS FIXED; THE BUILDS ARE FIELDS. Each code carries one fixed detail
line, keyed rather than formatted, on the terms ``clockspeed/audit/network.py``
states - so a detail is never built from something read out of a save. The two
changelists a consumer states travel on :attr:`BuildCheck.save_changelist` and
:attr:`BuildCheck.pinned_changelist`.

THE REGISTRY'S OWN SOURCE, ONE LAYER DOWN (CS-1315)
-----------------------------------------------------
The build check compares the SAVE's build with the pin. :func:`registry_check_of`
compares the REGISTRY's source with it: every nameplate figure is priced from
the registry, and the registry is built from the INSTALLED docs file, which a
game patch can change before the pin moves. The data layer records the sha256
of the bytes it built from on ``Registry.source_sha256``; this check holds it
beside the pinned docs hash, which arrives as a PARAMETER on the same terms as
the pinned changelist. CONTENT HASHES ONLY (the session 140 ruling): a patch
that moves the build string and leaves the docs bytes equal prices nothing
differently, so no build reaches this check and it raises nothing there.

Three outcomes again, none folded into another:

- The hashes differ: :data:`WARN_REGISTRY_MISMATCH`.
- Either hash is absent - a registry with no byte source, or no pinned docs
  hash - :data:`WARN_REGISTRY_UNVERIFIED`, and :attr:`RegistryCheck.matches`
  reads False. An empty string is absent: ``clockspeed/data/version.py``
  reads its docs hash as empty when the pin carries none, and an empty pin
  names no hash for the source to differ from.
- The hashes are equal: no warning at all.

A hash that is not text is REFUSED with ``TypeError``: the bytes spelling of a
digest compares unequal to its own text and would raise the mismatch code over
two equal hashes. The detail lines are fixed, as above, and neither hash is
ever written into one; both travel on :class:`RegistryCheck`.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from clockspeed.save.world import WorldWarning

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from collections.abc import Mapping

    from clockspeed.data.registry import Registry
    from clockspeed.save.world import WorldModel

__all__ = [
    "SOURCE_BUILD",
    "WARN_BUILD_MISMATCH",
    "WARN_BUILD_UNCOMPARED",
    "WARN_REGISTRY_MISMATCH",
    "WARN_REGISTRY_UNVERIFIED",
    "BuildCheck",
    "RegistryCheck",
    "build_check_of",
    "registry_check_of",
]

#: Which layer noticed a warning raised here, for ``WorldWarning.source``.
SOURCE_BUILD: Final = "build"

#: The save's header declares a build changelist other than the pinned one. Every
#: figure that depends on a nameplate is priced at the PINNED build's nameplate,
#: so it is not the save build's own figure; nothing here infers what the save
#: build's nameplate was.
WARN_BUILD_MISMATCH: Final = "build-mismatch"

#: No pinned changelist was available to compare with, so the save's build was
#: never compared. NOT a match: every nameplate figure is still priced at the
#: pinned build whatever build wrote the save.
WARN_BUILD_UNCOMPARED: Final = "build-uncompared"

#: The registry was built from docs bytes whose sha256 differs from the pinned
#: docs hash (CS-1315). Every figure that depends on a nameplate is priced from
#: that registry, so it is not the pinned build's own figure.
WARN_REGISTRY_MISMATCH: Final = "registry-mismatch"

#: The registry's source was never compared with the pinned docs hash: the
#: registry carries no hash of its source bytes, or no pinned docs hash was
#: available. NOT a match (CS-1315).
WARN_REGISTRY_UNVERIFIED: Final = "registry-unverified"

#: One fixed line per warning code raised here. Keyed rather than formatted, so
#: a detail can never be built from something read out of a save.
_WARNING_DETAIL: Final[Mapping[str, str]] = MappingProxyType(
    {
        WARN_BUILD_MISMATCH: (
            "the save was written by a game build other than the pinned build; every"
            " figure that depends on a nameplate is priced at the pinned build and is not"
            " the save build's own, and no older build's nameplate is inferred; the save"
            " build and the pinned build are both carried on the build check"
        ),
        WARN_BUILD_UNCOMPARED: (
            "no pinned build changelist was available, so the save's build was never"
            " compared with it; this is not a match, and every figure that depends on a"
            " nameplate is priced at the pinned build whatever build wrote the save"
        ),
        WARN_REGISTRY_MISMATCH: (
            "the registry was built from docs bytes whose content hash differs from the"
            " pinned docs hash; every figure that depends on a nameplate is priced from"
            " that registry and is not the pinned build's own, and no pinned value is"
            " inferred; both hashes are carried on the registry check"
        ),
        WARN_REGISTRY_UNVERIFIED: (
            "the registry's source docs were never compared with the pinned docs hash,"
            " as the registry carries no hash of its source bytes or no pinned docs hash"
            " was available; this is not a match, and every figure that depends on a"
            " nameplate is priced from an unverified registry"
        ),
    }
)


@dataclass(frozen=True, repr=False)
class BuildCheck:
    """The save's build and the pinned build, and the relation between them.

    ``repr`` is hand written and renders the two changelists and a warning
    count, on the terms ``clockspeed/audit/network.py`` ``WorldNetwork`` gives:
    a test runner reprs a value before a human chooses what to print.

    Attributes:
        save_changelist: The build the save's header declares, carried verbatim
            from ``clockspeed.save.header.SaveHeader.build_changelist``.
        pinned_changelist: The pinned build's changelist as the caller passed
            it, or None when the pin did not parse.
        warnings: Everything flagged, in the ``WorldWarning`` idiom. Empty
            exactly when the two builds were compared and are equal.
    """

    save_changelist: int
    pinned_changelist: int | None
    warnings: tuple[WorldWarning, ...]

    @property
    def compared(self) -> bool:
        """Whether a pinned changelist was available to compare with.

        Returns:
            False when the pin is None.
        """
        return self.pinned_changelist is not None

    @property
    def matches(self) -> bool:
        """Whether the two builds were compared AND are equal.

        Returns:
            False when they differ, and False when the pin is None - an
            uncompared build is never a match.
        """
        return self.pinned_changelist is not None and (
            self.save_changelist == self.pinned_changelist
        )

    def __repr__(self) -> str:
        """Render the two changelists and the warning count.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(save_changelist={self.save_changelist}, "
            f"pinned_changelist={self.pinned_changelist}, "
            f"warnings={len(self.warnings)})"
        )


def _warning(code: str) -> WorldWarning:
    """Build one warning from this module's own fixed detail table.

    Args:
        code: One of this module's ``WARN_*`` constants.

    Returns:
        The warning.
    """
    return WorldWarning(source=SOURCE_BUILD, code=code, detail=_WARNING_DETAIL[code])


def build_check_of(model: WorldModel, *, pinned_changelist: int | None) -> BuildCheck:
    """Hold the save's build beside the pinned build, and flag any difference.

    PURE. Reads one scalar off the model's header and prices nothing.

    Args:
        model: The world model, for its header's build changelist.
        pinned_changelist: The pinned build's changelist, or None when the pin
            did not parse. Keyword-only, so a caller names which build it is.

    Returns:
        The check: both builds, and :data:`WARN_BUILD_MISMATCH` when they
        differ, :data:`WARN_BUILD_UNCOMPARED` when the pin is None, or no
        warning when they are equal.

    Raises:
        TypeError: When ``pinned_changelist`` is neither None nor an int, or is
            a bool.
    """
    if pinned_changelist is not None and (
        isinstance(pinned_changelist, bool) or not isinstance(pinned_changelist, int)
    ):
        kind = type(pinned_changelist).__name__
        message = "pinned_changelist must be an int or None, not " + kind
        raise TypeError(message)

    save_changelist = model.header.build_changelist
    if pinned_changelist is None:
        warnings: tuple[WorldWarning, ...] = (_warning(WARN_BUILD_UNCOMPARED),)
    elif save_changelist != pinned_changelist:
        warnings = (_warning(WARN_BUILD_MISMATCH),)
    else:
        warnings = ()

    return BuildCheck(
        save_changelist=save_changelist,
        pinned_changelist=pinned_changelist,
        warnings=warnings,
    )


@dataclass(frozen=True, repr=False)
class RegistryCheck:
    """The registry's source hash and the pinned docs hash, and their relation.

    ``repr`` is hand written on :class:`BuildCheck`'s terms. Both hashes are
    digests of the shipped docs file, never of anything read out of a save.

    Attributes:
        source_sha256: ``Registry.source_sha256`` verbatim - the sha256 of the
            bytes the registry was built from, or None with no byte source.
        pinned_sha256: The pinned docs hash as the caller passed it, or None.
        warnings: Everything flagged, in the ``WorldWarning`` idiom. Empty
            exactly when both hashes are present and equal.
    """

    source_sha256: str | None
    pinned_sha256: str | None
    warnings: tuple[WorldWarning, ...]

    @property
    def compared(self) -> bool:
        """Whether both hashes were present to compare.

        Returns:
            False when either is None or empty.
        """
        return bool(self.source_sha256) and bool(self.pinned_sha256)

    @property
    def matches(self) -> bool:
        """Whether both hashes were compared AND are equal.

        Returns:
            False when they differ, and False when either is absent - an
            unverified registry is never a match.
        """
        return self.compared and self.source_sha256 == self.pinned_sha256

    def __repr__(self) -> str:
        """Render the two hashes and the warning count.

        Returns:
            The safe rendering.
        """
        return (
            f"{type(self).__name__}(source_sha256={self.source_sha256}, "
            f"pinned_sha256={self.pinned_sha256}, "
            f"warnings={len(self.warnings)})"
        )


def _hash_or_refuse(value: object, name: str) -> str | None:
    """Return a hash that is None or text, refusing anything else.

    Args:
        value: The hash.
        name: What it is, for the refusal message - never its value.

    Returns:
        The hash unchanged.

    Raises:
        TypeError: The hash is neither None nor a ``str``.
    """
    if value is not None and not isinstance(value, str):
        raise TypeError(name + " must be a str or None, not " + type(value).__name__)
    return value


def registry_check_of(registry: Registry, *, pinned_docs_sha256: str | None) -> RegistryCheck:
    """Hold the registry's source hash beside the pinned docs hash, and flag any difference.

    PURE. Reads one field off the registry and prices nothing. No build is a
    parameter: a build-only difference with equal bytes is not a mismatch.

    Args:
        registry: The registry, for its ``source_sha256``.
        pinned_docs_sha256: The pinned docs hash, or None when the pin carries
            none. Keyword-only, so a caller names which hash it is.

    Returns:
        The check: :data:`WARN_REGISTRY_MISMATCH` when both hashes are present
        and differ, :data:`WARN_REGISTRY_UNVERIFIED` when either is None or
        empty, or no warning when they are equal.

    Raises:
        TypeError: Either hash is neither None nor a ``str``.
    """
    pinned = _hash_or_refuse(pinned_docs_sha256, "pinned_docs_sha256")
    source = _hash_or_refuse(registry.source_sha256, "source_sha256")
    if not source or not pinned:
        warnings: tuple[WorldWarning, ...] = (_warning(WARN_REGISTRY_UNVERIFIED),)
    elif source != pinned:
        warnings = (_warning(WARN_REGISTRY_MISMATCH),)
    else:
        warnings = ()
    return RegistryCheck(source_sha256=source, pinned_sha256=pinned, warnings=warnings)
