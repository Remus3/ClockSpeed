"""CS-1340, CS-1348 round 5 - ONE repeated-key rule over every carrier this reader sees.

THE RULE. A carrier property or keyed element written more than once is never
last-wins and never first-wins: every copy is withheld - the reading is None,
or the element is left out - and the world raises
:data:`~clockspeed.save.world.WARN_REPEATED_KEY` once, carrying the number of
copies and naming the carrier as its subject. One helper,
``clockspeed.save.world._repeats``, finds the repeats for every carrier below.

WHERE IT CANNOT REACH, RECORDED RATHER THAN CLAIMED. A TOP-LEVEL property tag
written twice - ``mGamePhaseCosts``, ``mTargetGamePhasePaidOffCosts`` or
``mInventoryStacks`` - never reaches this layer twice: the payload reader one
layer down publishes values by NAME, so a repeated tag is already one value
when ``clockspeed/save/world.py`` sees it. ADR 0016 records that residual and
the reader change that would close it; no arm here pretends otherwise.

SYNTHETIC ONLY - every fixture comes from ``tests/save/elevator_synthetic.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

import pytest

from clockspeed.save import world
from tests.save import elevator_synthetic as es

#: A case: the save, the published value that must be withheld, the carrier
#: the flag must name, and how many copies it must count.
Case = tuple[bytes, Callable[[world.WorldModel], object], str, int]

_TWO: Final = 2

_CASES: Final[dict[str, Case]] = {
    "phase-cost-entry": (
        es.save_blob(
            manager_tags=(
                es.phase_costs_tag(
                    (
                        (es.OWED_PHASE, ((es.PART_A_PATH, 3),)),
                        (es.OWED_PHASE, ((es.PART_A_PATH, 9),)),
                    )
                ),
            )
        ),
        lambda model: (
            None if model.phase_costs is None else model.phase_costs.by_phase.get(es.OWED_PHASE)
        ),
        es.PHASE_COSTS_PROPERTY,
        _TWO,
    ),
    "phase-cost-entry-one-copy-unreadable": (
        # The second copy's lines do not read, and its phase token does: it is
        # still a second copy of the phase, so the readable one is not taken.
        es.save_blob(
            manager_tags=(
                es.phase_costs_tag(
                    (
                        (es.OWED_PHASE, ((es.PART_A_PATH, 3),)),
                        (es.OWED_PHASE, ((es.PART_A_PATH, -1),)),
                    )
                ),
            )
        ),
        lambda model: (
            None if model.phase_costs is None else model.phase_costs.by_phase.get(es.OWED_PHASE)
        ),
        es.PHASE_COSTS_PROPERTY,
        _TWO,
    ),
    "paid-off-element": (
        es.save_blob(
            manager_tags=(
                es.target_tag(),
                es.paid_off_tag(((es.PART_A_PATH, 1), (es.PART_A_PATH, 2))),
            )
        ),
        lambda model: model.paid_off,
        es.PAID_OFF_PROPERTY,
        _TWO,
    ),
    "target-phase-tag": (
        es.save_blob(manager_tags=(es.target_tag(), es.target_tag())),
        lambda model: model.target_phase,
        es.TARGET_PROPERTY,
        _TWO,
    ),
    "elevator-input-reference": (
        es.save_blob(slots=es.EMPTY_SLOTS, input_references=_TWO),
        lambda model: model.elevator_input,
        es.INPUT_PROPERTY,
        _TWO,
    ),
}


@pytest.mark.parametrize("case", list(_CASES), ids=list(_CASES))
def test_a_repeated_key_is_withheld_and_flagged_never_last_wins(case: str) -> None:
    """Every copy withheld, one flag naming the carrier and counting the copies.

    The same save written once is the control: the value publishes and no
    repeated-key flag is raised, so the None below is the repeat's doing.
    """
    blob, published, carrier, copies = _CASES[case]
    model = world.load_world_from_bytes(blob)
    flags = [
        (warning.subject, warning.count)
        for warning in model.warnings
        if warning.code == world.WARN_REPEATED_KEY
    ]

    assert published(model) is None
    assert flags == [(carrier, copies)]


def test_each_carrier_written_once_publishes_and_raises_no_repeated_flag() -> None:
    """The controls for every case above: one copy publishes, and is not flagged."""
    once = {
        "phase-cost-entry": es.save_blob(manager_tags=(es.phase_costs_tag(),)),
        "paid-off-element": es.save_blob(
            manager_tags=(es.target_tag(), es.paid_off_tag(((es.PART_A_PATH, 1),)))
        ),
        "target-phase-tag": es.save_blob(manager_tags=(es.target_tag(),)),
        "elevator-input-reference": es.save_blob(slots=es.EMPTY_SLOTS),
    }
    for case, blob in once.items():
        model = world.load_world_from_bytes(blob)
        published = _CASES[case][1](model)
        repeated = [w for w in model.warnings if w.code == world.WARN_REPEATED_KEY]
        assert published is not None, case
        assert repeated == [], case
