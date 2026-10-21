"""CS-1043: the milestone requirement model over a synthetic schematic document.

Every fixture here is hand-built in this module. Nothing below opens a save, a
docs file or the install - ``tests/progress/__init__.py`` carries the four rules
that bind every module in this directory, and each of them shapes an arm here.

THE BUDGET IS THE CLAUSE, AND THE CLAUSE IS ABOUT REDDENING. A required rate is
a cost over a completion budget, and a budget written as a literal at the
division site cannot be moved by a test - so an arm that only checked the
arithmetic would pass unchanged against an implementation nobody can perturb.
That is the CS-1039 vacuity shape by name. The second arm below MOVES the budget
through the module attribute and requires the rate to follow it, which is only
possible while the budget is a named constant READ IN THE FUNCTION BODY. A
default argument value binds at def time and would leave that arm green against
a frozen budget.

THE JOIN IS THE RESOLVED CONTENT ASSET PATH AND NOTHING ELSE. The unlock state
holds whole asset paths, the document carries the same path inside its FullName,
and the fourth arm feeds two entries whose paths differ while their trailing
token is identical. Any reducer to a bare class name makes those two entries
indistinguishable and reddens that arm - which is the point of writing it that
way rather than with two obviously different names.

A SILENT EMPTY ANSWER IS THE OTHER DEFECT. An unreadable cost that is quietly
dropped, an unread HUB tier and a machine with no document at all all publish
the same empty shape as a target that genuinely requires nothing, so each is
graded for the WARNING that separates the two rather than for the emptiness.

EVERY ASSET PATH BELOW IS INVENTED. Nothing under the synthetic root names
anything that exists in any shipped build, and no arm here needs a real one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

import pytest

from clockspeed.progress import milestones
from clockspeed.save.world import UnlockState
from clockspeed.solve import exact

# ---------------------------------------------------------------------------
# The synthetic document. Three pieces rather than one literal so that no
# string here needs a backslash escape: the item-amount grammar nests a single
# quote inside a double-quoted field, and clockspeed/data/blobs.py owns it.
# ---------------------------------------------------------------------------

#: Opening of one item-amount entry, type wrapper included.
COST_ENTRY_HEAD: Final = '(ItemClass="BlueprintGeneratedClass'

#: The single quote that closes the Unreal ``Type'Path'`` wrapper.
QUOTE_SINGLE: Final = "'"

#: Everything between the wrapped path and the amount digits.
COST_ENTRY_TAIL: Final = '",Amount='

#: What a FullName leads with, ahead of the space. Any word would do - the
#: reader keeps what follows the first space and never looks at this half.
FULL_NAME_TYPE_PREFIX: Final = "BlueprintGeneratedClass"

#: Invented asset paths. The two TWIN paths differ only in the directory above
#: the asset, so their trailing tokens are byte-identical.
ALPHA_PATH: Final = (
    "/Game/Synthetic/Milestones/Schematic_Synthetic_Alpha.Schematic_Synthetic_Alpha_C"
)
TWIN_UNLOCKED_PATH: Final = (
    "/Game/Synthetic/MilestonesEast/Schematic_Synthetic_Twin.Schematic_Synthetic_Twin_C"
)
TWIN_LOCKED_PATH: Final = (
    "/Game/Synthetic/MilestonesWest/Schematic_Synthetic_Twin.Schematic_Synthetic_Twin_C"
)
BROKEN_COST_PATH: Final = (
    "/Game/Synthetic/Milestones/Schematic_Synthetic_Broken.Schematic_Synthetic_Broken_C"
)
NON_STRING_COST_PATH: Final = (
    "/Game/Synthetic/Milestones/Schematic_Synthetic_Untyped.Schematic_Synthetic_Untyped_C"
)
WIDGET_PATH: Final = "/Game/Synthetic/Items/Desc_SyntheticWidget.Desc_SyntheticWidget_C"

#: The one cost amount every rate assertion below is derived from.
WIDGET_AMOUNT: Final = 50

#: The tier as the document spells it - a string, like every docs scalar.
TIER_TEXT: Final = "3"

#: A tier value that is a float, which is admissible because an entry value is
#: ``object``. It is the INPUT CONTROL for the no-float arm: the walk has to be
#: able to see a float somewhere before its absence downstream means anything.
TIER_FLOAT: Final = 3.0

#: The rate the shipped budget yields, and the rate the moved budget yields.
#: Written as literals rather than recomputed from the module constant, so a
#: budget that moves cannot move the expectation with it.
EXPECTED_RATE: Final = Fraction(50, 120)
MOVED_BUDGET_MINUTES: Final = Fraction(60)
MOVED_EXPECTED_RATE: Final = Fraction(50, 60)

#: A cost blob that is not the measured grammar at all.
UNPARSEABLE_COST: Final = "(ItemClass=unquoted,Amount=nope)"

#: A cost value that is not a string. A present non-string is new content, not
#: an absent field, and the two must stay distinguishable.
NON_STRING_COST: Final = 7

#: How many entries the trailing-token arm feeds in. Named because a bare
#: literal in that comparison is a magic value the linter rejects outright.
TWIN_ENTRY_COUNT: Final = 2


def cost_blob(*entries: tuple[str, int]) -> str:
    inner = ",".join(
        COST_ENTRY_HEAD + QUOTE_SINGLE + path + QUOTE_SINGLE + COST_ENTRY_TAIL + f"{amount})"
        for path, amount in entries
    )
    return "(" + inner + ")"


def entry(
    asset_path: str,
    *,
    cost: object = None,
    tier: object = TIER_TEXT,
    schematic_type: object = milestones.TYPE_MILESTONE,
) -> Mapping[str, object]:
    built: dict[str, object] = {
        milestones.KEY_FULL_NAME: FULL_NAME_TYPE_PREFIX
        + milestones.FULL_NAME_SEPARATOR
        + asset_path,
        milestones.KEY_TYPE: schematic_type,
        milestones.KEY_TECH_TIER: tier,
    }
    if cost is not None:
        built[milestones.KEY_COST] = cost
    return MappingProxyType(built)


def alpha_entry(*, tier: object = TIER_TEXT) -> Mapping[str, object]:
    return entry(ALPHA_PATH, cost=cost_blob((WIDGET_PATH, WIDGET_AMOUNT)), tier=tier)


@dataclass(frozen=True)
class FakeSource:
    """A hand-built stand-in for whatever supplies the schematic entries.

    It implements the protocol the module declares and imports nothing from the
    data layer, which is the whole point of that protocol being generic over the
    ENTRY type rather than over a document.

    Attributes:
        entries: The entries to hand over, or None for a machine that has no
            document to read at all.
    """

    entries: tuple[Mapping[str, object], ...] | None

    def schematics(self) -> tuple[Mapping[str, object], ...] | None:
        """Hand over the hand-built entries.

        Returns:
            The entries, or None.
        """
        return self.entries


def source_of(*entries: Mapping[str, object]) -> FakeSource:
    return FakeSource(entries=entries)


def unlocks(*purchased: str) -> UnlockState:
    return UnlockState(
        purchased_schematics=frozenset(purchased),
        recipes=frozenset(),
        current_game_phase=None,
        feature_flags=MappingProxyType({}),
        scanned_resources=frozenset(),
        trading_post_level=None,
    )


def reachable(value: object, seen: set[int] | None = None) -> list[object]:
    """Every value reachable from one object, the object itself included.

    STRUCTURAL on purpose - an assertion naming today's field names passes
    unchanged the day a field is added, which is rule three of this package.
    Re-authored here rather than imported because each module that needs this
    walk owns its own copy; there is no shared helper to reach for.

    Args:
        value: The root.
        seen: Identities already walked, to survive a cycle.

    Returns:
        Every reachable value.
    """
    seen = set() if seen is None else seen
    if id(value) in seen:
        return []
    seen.add(id(value))
    found: list[object] = [value]
    if is_dataclass(value) and not isinstance(value, type):
        for member in fields(value):
            found.extend(reachable(getattr(value, member.name), seen))
        return found
    if isinstance(value, (str, bytes, bytearray)):
        return found
    if isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(reachable(key, seen))
            found.extend(reachable(item, seen))
        return found
    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            found.extend(reachable(item, seen))
    return found


def rates_of(result: milestones.MilestoneRequirements) -> list[Fraction]:
    return [cost.required_per_minute for item in result.milestones for cost in item.costs]


def warning_codes_of(result: milestones.MilestoneRequirements) -> set[str]:
    return {warning.code for warning in result.warnings}


# ---------------------------------------------------------------------------
# ARM ONE: the rate is the exact cost over the budget
# ---------------------------------------------------------------------------


def test_each_required_rate_is_the_exact_fraction_cost_over_budget() -> None:
    """Catches a rate taken through float, and a rate over the wrong budget.

    The type check beside the equality is not decoration: Fraction compares
    equal to the float that happens to share its value, so equality alone would
    pass against a float-derived rate.
    """
    result = milestones.requirements_of(source_of(alpha_entry()), unlocks())

    rates = rates_of(result)
    published = len(rates)
    assert published == 1, "one synthetic entry with one cost must publish one rate"
    rate = rates[0]
    assert rate == EXPECTED_RATE
    exactly_a_fraction = type(rate) is Fraction
    assert exactly_a_fraction, "a value equal to the expected rate may still be a float"


# ---------------------------------------------------------------------------
# ARM TWO: the clause the acceptance names - the budget MOVES
# ---------------------------------------------------------------------------


def test_the_required_rate_reddens_when_the_named_budget_moves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches a budget that cannot be perturbed - a literal, or a def-time default.

    Before the named constant exists this fails at ``monkeypatch.setattr`` with
    an AttributeError, and that is the right reason: the clause is unsatisfiable
    without the name.
    """
    before = rates_of(milestones.requirements_of(source_of(alpha_entry()), unlocks()))[0]

    monkeypatch.setattr(milestones, "MILESTONE_BUDGET_MINUTES", MOVED_BUDGET_MINUTES)
    after = rates_of(milestones.requirements_of(source_of(alpha_entry()), unlocks()))[0]

    assert before == EXPECTED_RATE
    assert after == MOVED_EXPECTED_RATE
    moved = after != before
    assert moved, "the rate did not follow the budget, so the budget is not read at call time"


# ---------------------------------------------------------------------------
# ARM THREE: no float reaches the model, with the input as the control
# ---------------------------------------------------------------------------


def test_no_float_reaches_any_milestone_output_field() -> None:
    """Catches a float carried through from an entry value into a published field.

    The entry's tier is a float, which an entry value's ``object`` annotation
    admits. The control assertion is what makes the second half mean anything: a
    walk that cannot see a float in the INPUT proves nothing by not finding one
    in the output.
    """
    document = source_of(alpha_entry(tier=TIER_FLOAT))

    control = [value for value in reachable(document.entries) if type(value) is float]
    assert control, "the walk cannot see a float in the INPUT, so its absence proves nothing"

    result = milestones.requirements_of(document, unlocks())

    rates = rates_of(result)
    carried = len(rates)
    assert carried == 1, "the arm must publish a rate, or the clean walk below is about nothing"
    leaked = len([value for value in reachable(result) if type(value) is float])
    assert leaked == 0, "a float reached a published field"
    exact.audit_exact(result, path="requirements")


# ---------------------------------------------------------------------------
# ARM FOUR: the join is the whole asset path
# ---------------------------------------------------------------------------


def test_the_join_is_the_resolved_asset_path_and_not_a_name_match() -> None:
    """Catches a join reduced to a trailing class token instead of the whole path.

    The two entries share a trailing token and differ only above it, and the
    unlock state holds exactly one of the two whole paths. A reducer to the bare
    name marks both purchased and reddens this arm; a reducer that compares the
    bare names marks both too. Only the whole-path join answers one.
    """
    result = milestones.requirements_of(
        source_of(
            entry(TWIN_UNLOCKED_PATH, cost=cost_blob((WIDGET_PATH, WIDGET_AMOUNT))),
            entry(TWIN_LOCKED_PATH, cost=cost_blob((WIDGET_PATH, WIDGET_AMOUNT))),
        ),
        unlocks(TWIN_UNLOCKED_PATH),
    )

    modelled = len(result.milestones)
    assert modelled == TWIN_ENTRY_COUNT, "both entries are milestones and both must be modelled"
    purchased = [item.asset_path for item in result.milestones if item.purchased]
    matched = len(purchased)
    assert matched == 1, "exactly one of the two twin paths is in the unlock state"
    correct = purchased[0] == TWIN_UNLOCKED_PATH
    assert correct, "the purchased milestone is not the one whose whole path was unlocked"


# ---------------------------------------------------------------------------
# ARM FIVE: an unreadable cost is NAMED, never silently dropped
# ---------------------------------------------------------------------------


def test_an_unreadable_cost_is_flagged_and_skipped_rather_than_summed() -> None:
    """Catches a dropped cost that leaves an empty list and no warning behind it.

    Two faults, one entry each: a cost that is not a string at all, and a cost
    string that is not the measured grammar. Asserting only the empty collection
    would pass on the silently-wrong defect, because a target that genuinely
    costs nothing publishes the same empty list.
    """
    result = milestones.requirements_of(
        source_of(
            entry(NON_STRING_COST_PATH, cost=NON_STRING_COST),
            entry(BROKEN_COST_PATH, cost=UNPARSEABLE_COST),
        ),
        unlocks(),
    )

    published = len(rates_of(result))
    assert published == 0, "an unreadable cost must contribute no number at all"
    flagged = milestones.WARN_MILESTONE_COST_UNREADABLE in warning_codes_of(result)
    assert flagged, "two unreadable costs were dropped with nothing said about either"


# ---------------------------------------------------------------------------
# ARM SIX and ARM SEVEN: the two other ways this model can say nothing.
# Package rule four requires each of them to be graded for its WARNING rather
# than for the empty shape it shares with an honest nothing.
# ---------------------------------------------------------------------------


def test_the_unread_hub_tier_is_flagged_rather_than_reported_as_absent() -> None:
    """Catches a null HUB tier published as if it were a reading of the save.

    No carrier for the trading post level has been measured, so the field is
    always null today. Null with no warning is indistinguishable from a world
    whose HUB is genuinely at no tier.
    """
    result = milestones.requirements_of(source_of(alpha_entry()), unlocks())

    unread = result.hub_tier is None
    assert unread, "nothing in this fixture can have supplied a HUB tier"
    flagged = milestones.WARN_MILESTONE_HUB_TIER_UNREAD in warning_codes_of(result)
    assert flagged, "the null HUB tier was published with nothing said about it"


def test_a_machine_with_no_schematic_document_gets_an_empty_model_and_a_warning() -> None:
    """Catches a refusal where a value belongs, and a silent empty model.

    No document on this machine is a true answer about a working system, so it
    is a value and not an exception - and it must not read as a world that needs
    no milestones.
    """
    result = milestones.requirements_of(FakeSource(entries=None), unlocks())

    modelled = len(result.milestones)
    assert modelled == 0
    flagged = milestones.WARN_MILESTONE_SCHEMATICS_UNAVAILABLE in warning_codes_of(result)
    assert flagged, "an absent document published an empty model and said nothing"


# ---------------------------------------------------------------------------
# The repr guard: a model that holds asset paths may not render one
# ---------------------------------------------------------------------------


def test_the_requirements_model_renders_no_asset_path() -> None:
    """Catches an asset path reaching a repr, a log line or a failure report.

    Graded against a POPULATED model rather than an empty one, which is the only
    version of this arm that can fail.
    """
    result = milestones.requirements_of(source_of(alpha_entry()), unlocks(ALPHA_PATH))

    rendered = repr(result)
    leaks = len([path for path in (ALPHA_PATH, WIDGET_PATH) if path in rendered])
    assert leaks == 0, "an invented asset path reached the repr of the requirements model"
