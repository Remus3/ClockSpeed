"""CS-1288: build-input fixtures for advisor tests - the save's build beside the pin.

WHAT THIS MODULE OFFERS. Every advice rule that prices a figure from a
nameplate reads the three build inputs
:data:`clockspeed.advisor.build.BUILD_INPUTS`, so every synthetic world an
advisor test builds has to carry them. The helpers here build them the way
production does: a synthetic ``WorldModel`` whose header declares one build,
handed to :func:`clockspeed.audit.build.build_check_of` with a pin, flattened
by :func:`clockspeed.advisor.build.build_inputs`. Nothing is forged, so a
fixture's warning code and detail line are the audit's own and cannot drift
from them.

THE PIN IS READ AT TEST TIME, NEVER TYPED. :func:`game_pin` reads
``clockspeed.data.version.GAME_CHANGELIST`` when it is called and asserts it
parsed (the session 134 ruling in ``docs/history_notes.md`` section CS-1288,
relocated there from ``docs/item_notes/phase5.md`` on the item's close). An
off-pin fixture declares the pin plus or minus one - the build
after it or the build before it, :data:`OFF_PIN_OFFSETS` (the session 138
ruling F8 as amended by the fix round 1 adjudication) - so no changelist
literal appears here or in any caller.

TESTS ONLY. This module lives under ``tests/`` so no production module can
depend on it; ``clockspeed/advisor/build.py`` imports nothing from here.

The world token below is an invented 22-character literal. No world here was
cut from a real save.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.advisor.build import build_inputs
from clockspeed.audit.build import BuildCheck, build_check_of
from clockspeed.data import version
from clockspeed.save import objects
from clockspeed.save.header import SaveHeader
from clockspeed.save.world import EMPTY_UNLOCK_STATE, WorldModel

if TYPE_CHECKING:
    from clockspeed.advisor.trace import InputValue

__all__ = [
    "OFF_PIN_OFFSETS",
    "build_check",
    "game_pin",
    "off_pin_build_inputs",
    "pinned_build_inputs",
    "synthetic_world",
    "uncompared_build_inputs",
]

# An invented 22-character base64url literal. Never a real world token.
SYNTHETIC_TOKEN: Final = "BuildFixtureToken22chr"  # noqa: S105 - an invented marker, not a secret

#: The two off-pin offsets every off-pin census runs at: the build after the
#: pin and the build before it (CS-1288 fix round 1). Steps, never changelists.
OFF_PIN_OFFSETS: Final = (1, -1)


def game_pin() -> int:
    """Read the pinned build's changelist now, and require that it parsed.

    Returns:
        ``clockspeed.data.version.GAME_CHANGELIST`` as it reads at call time.
    """
    pin = version.GAME_CHANGELIST
    assert pin is not None, "the pinned build did not parse, so no build fixture can be built"
    return pin


def synthetic_world(build_changelist: int) -> WorldModel:
    """Build a synthetic world model whose header declares one build and nothing else.

    Args:
        build_changelist: The build the synthetic header declares.

    Returns:
        The model, holding no record, no node, no unlock and no warning.
    """
    header = SaveHeader(
        header_version=14,
        save_version=52,
        build_changelist=build_changelist,
        map_name="SyntheticMap",
        world_token=SYNTHETIC_TOKEN,
        play_duration=0,
        datetime_ticks=0,
        byte_after_datetime_ticks=0,
        editor_object_version=0,
        is_modded=0,
        body_offset=0,
        warnings=(),
    )
    return WorldModel(
        token=SYNTHETIC_TOKEN,
        header=header,
        objects=objects.ObjectTable(
            records=(),
            unknown_classes=(),
            warnings=(),
            declared_body_length=0,
            body_consumed=0,
            body_prefix_width=8,
            transform_delta=0,
            save_version=52,
            header_version=14,
        ),
        unlocks=EMPTY_UNLOCK_STATE,
        nodes=(),
        warnings=(),
    )


def build_check(save_changelist: int, pinned_changelist: int | None) -> BuildCheck:
    """Run the audit's own build check over a synthetic save of one build.

    Args:
        save_changelist: The build the synthetic save declares.
        pinned_changelist: The pin to compare it with, or None for no pin.

    Returns:
        The audit's check, warnings and all.
    """
    world = synthetic_world(save_changelist)
    return build_check_of(world, pinned_changelist=pinned_changelist)


def pinned_build_inputs(pin: int) -> dict[str, InputValue]:
    """The build inputs of a save written by the pinned build itself.

    Args:
        pin: The pinned changelist, from :func:`game_pin`.

    Returns:
        A fresh dict of the three build inputs, carrying no warning.
    """
    return build_inputs(build_check(pin, pin))


def off_pin_build_inputs(pin: int, offset: int = 1) -> dict[str, InputValue]:
    """The build inputs of a save written ``offset`` builds away from the pin.

    BOTH SIDES OF THE PIN MATTER (CS-1288 fix round 1, the adjudicated
    amendment of ruling F8): a save OLDER than the pin is the item's
    motivating case, and a caveat comparing builds by order rather than by
    equality passes on one side alone. :data:`OFF_PIN_OFFSETS` holds both.

    Args:
        pin: The pinned changelist, from :func:`game_pin`.
        offset: How far the save's build sits from the pin: ``1`` for the
            build after it (the default), ``-1`` for the build before it.
            Never zero.

    Returns:
        A fresh dict of the three build inputs, carrying the mismatch code.
    """
    assert offset != 0, "an off-pin save is never written by the pinned build"
    save = pin + offset
    assert save > 0, "the off-pin save build is not a positive changelist"
    return build_inputs(build_check(save, pin))


def uncompared_build_inputs(save_changelist: int) -> dict[str, InputValue]:
    """The build inputs of a save compared with no pin at all.

    Args:
        save_changelist: The build the synthetic save declares.

    Returns:
        A fresh dict of the three build inputs, carrying the uncompared code.
    """
    return build_inputs(build_check(save_changelist, None))
