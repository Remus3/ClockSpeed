"""CS-500: a seeded generator of synthetic world states, plus naive rules to run on them.

WHY A SEEDED GENERATOR AND NOT A PROPERTY-TESTING LIBRARY. The merger ruled
for an in-repo generator over ``random.Random(seed)``: no new dependency, and
the same seed yields the same worlds on every machine, so a failure reproduces
from its seed alone.

THE RULES HERE ARE DELIBERATELY NAIVE. Each one recommends whenever its numeric
condition holds and never looks at the unlock set itself. That is the point:
the property test grades the ENGINE's precondition gate, so a rule that checked
its own unlocks would make the invariant hold for a reason the test cannot see.

Every name and value is invented. No world here was cut from a real save.
"""

from __future__ import annotations

import random
from fractions import Fraction

from clockspeed.advisor.trace import (
    InputValue,
    Recommendation,
    RuleContext,
    RuleSpec,
    WorldInputs,
)

#: The synthetic unlock keys a generated world draws its unlock set from.
UNLOCK_UNIVERSE: tuple[str, ...] = (
    "feature:synthetic-overclock",
    "recipe:/Synthetic/Recipe_AltPlate",
    "recipe:/Synthetic/Recipe_AltRod",
    "schematic:/Synthetic/Schematic_TierTwo",
    "schematic:/Synthetic/Schematic_Trains",
)

#: The synthetic input names a generated world may carry, with their source.
INPUT_SOURCES: tuple[tuple[str, str], ...] = (
    ("synthetic.headroom", "synthetic.power"),
    ("synthetic.draw", "synthetic.power"),
    ("synthetic.purity", "synthetic.nodes"),
    ("synthetic.distance", "synthetic.nodes"),
)

#: The recipe a data-driven recommendation names, chosen by an input value.
_RECIPE_BY_PARITY: tuple[str, str] = (
    "recipe:/Synthetic/Recipe_AltPlate",
    "recipe:/Synthetic/Recipe_AltRod",
)


def generate_world(rng: random.Random) -> WorldInputs:
    """Draw one world: a random unlock subset and a random subset of inputs.

    An input may be absent, so the engine's missing-input path is exercised by
    the same population as its precondition gate. Every value is an exact
    Fraction drawn from integers - the generator never touches a float.
    """
    unlocks = frozenset(key for key in UNLOCK_UNIVERSE if rng.randrange(2))
    values: dict[str, InputValue] = {}
    for name, source in INPUT_SOURCES:
        if rng.randrange(5) == 0:
            continue
        values[name] = InputValue(Fraction(rng.randrange(0, 1000), rng.randrange(1, 60)), source)
    return WorldInputs(values=values, unlocks=unlocks)


def generate_worlds(seed: int, count: int) -> tuple[WorldInputs, ...]:
    """Draw ``count`` worlds from one seed, reproducibly."""
    rng = random.Random(seed)  # noqa: S311 - reproducible fixtures, not secrets
    return tuple(generate_world(rng) for _ in range(count))


def _overclock(ctx: RuleContext) -> Recommendation | None:
    headroom = ctx.read_exact("synthetic.headroom")
    draw = ctx.read_exact("synthetic.draw")
    spare = ctx.compute("spare", headroom - draw)
    if spare <= 0:
        ctx.reject("overclock", "no spare generation")
        return None
    return Recommendation(
        subject_key="synthetic-grid",
        action="Overclock the synthetic line",
        reason="spare generation available",
    )


def _claim_node(ctx: RuleContext) -> Recommendation | None:
    purity = ctx.read_exact("synthetic.purity")
    distance = ctx.read_exact("synthetic.distance")
    if purity < distance:
        ctx.reject("claim", "too far for its purity")
        return None
    return Recommendation(
        subject_key="synthetic-node",
        action="Claim the synthetic node",
        reason="purity outweighs distance",
    )


def _switch_recipe(ctx: RuleContext) -> Recommendation | None:
    """Recommend a recipe chosen from DATA, so its unlock is per-recommendation."""
    purity = ctx.read_exact("synthetic.purity")
    recipe = _RECIPE_BY_PARITY[purity.numerator % 2]
    return Recommendation(
        subject_key="synthetic-recipe",
        action="Switch to the alternate synthetic recipe",
        reason="the purity favours it",
        requires=(recipe,),
    )


def _rebalance(ctx: RuleContext) -> Recommendation | None:
    draw = ctx.read_exact("synthetic.draw")
    if draw == 0:
        return None
    return Recommendation(
        subject_key="synthetic-grid",
        action="Rebalance the synthetic grid",
        reason="draw is nonzero",
    )


#: Naive rules over the synthetic inputs - see the module docstring.
SYNTHETIC_RULES: tuple[RuleSpec, ...] = (
    RuleSpec(
        rule_id="synthetic.overclock",
        domain="power",
        inputs=("synthetic.headroom", "synthetic.draw"),
        unlocks=("feature:synthetic-overclock",),
        evaluate=_overclock,
    ),
    RuleSpec(
        rule_id="synthetic.claim-node",
        domain="nodes",
        inputs=("synthetic.purity", "synthetic.distance"),
        unlocks=("schematic:/Synthetic/Schematic_TierTwo", "schematic:/Synthetic/Schematic_Trains"),
        evaluate=_claim_node,
    ),
    RuleSpec(
        rule_id="synthetic.switch-recipe",
        domain="transport",
        inputs=("synthetic.purity",),
        unlocks=(),
        evaluate=_switch_recipe,
    ),
    RuleSpec(
        rule_id="synthetic.rebalance",
        domain="power",
        inputs=("synthetic.draw",),
        unlocks=(),
        evaluate=_rebalance,
    ),
)
