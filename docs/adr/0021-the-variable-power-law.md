# 0021 - The variable-power law is two bounds, and the building estimate is their envelope

## Status

`accepted` - filed 2026-09-14 under CS-301.

Relates to `0020`, which adopted `CommunityResources/Headers.zip` as this project's
declaration-grade oracle and built `clockspeed/data/assets.py` to query it. This ADR is the
first decision to USE that instrument for a question about meaning rather than about
serialization. It supersedes nothing.

## Decision in one line

**The variable-power law is adopted as `draw = constant + factor * curve`, which bounds a
recipe at `[constant, constant + factor]` at the reference clock; the estimated range
declared on the BUILDING is the ENVELOPE over its recipes, so the cross-check between the
two is CONTAINMENT and never equality; and no scalar average is published, because the
curve is a separate asset the shipped document does not carry.**

## Context

`clockspeed/solve/power.py` has reported the variable-power shape unmodeled since phase 3,
and said so in as many words: the semantics of `mVariablePowerConsumptionConstant` and
`mVariablePowerConsumptionFactor` had never been measured by this project, so the module
handed the four operands back verbatim and applied no law. That was the right call under
non-negotiable 7 while the meaning was unknown. It is also the reason the three hungriest
buildings in the game contribute nothing to a power plan.

The refusal was never a decision that the meaning was UNKNOWABLE. It was a decision not to
guess, taken before anything in this tree had opened the publisher's own headers. ADR 0020
changed what is available: the headers are now a queryable index.

## Evidence

Read-only probe run 2026-09-14 against the pinned build, resolved at runtime. The install
path is not recorded here and is never hardcoded. Nothing under the install was created,
modified or deleted.

**(1) The header declares the relation in prose.** Through `clockspeed/data/assets.py`,
over an index of 8024 reflected property declarations:

| Property | Owner | Declared type | Specifiers |
|---|---|---|---|
| `mVariablePowerConsumptionConstant` | `UFGRecipe` | `float` | `EditDefaultsOnly`, `Category = "Recipe|Variable Power"` |
| `mVariablePowerConsumptionFactor` | `UFGRecipe` | `float` | `EditDefaultsOnly`, `Category = "Recipe|Variable Power"` |
| `mEstimatedMininumPowerConsumption` | `AFGBuildableManufacturerVariablePower` | `float` | `EditDefaultsOnly`, `Category = "Power"` |
| `mEstimatedMaximumPowerConsumption` | `AFGBuildableManufacturerVariablePower` | `float` | `EditDefaultsOnly`, `Category = "Power"` |
| `mPowerConsumptionCurve` | `AFGBuildableManufacturerVariablePower` | `TObjectPtr<UCurveFloat>` | `EditDefaultsOnly`, `Category = "Power"` |

The two recipe members carry doc comments stating the law. The constant is "added to the
variable power consumption" and, with the curve range normalized to `[0.0, 1.0]`, "can be
thought of as a power-consumption minimum". The factor is "multiplied into the variable
power consumption" and, under the same normalization, "this value added to the
power-consumption constant can be thought of as a power-consumption maximum". The buildable
header states the curve's domain must cover `[0.0, 1.0]` and that its range SHOULD also
cover it, and names the two recipe members as the reason.

So the law is `constant + factor * curve(progress)`, and the two endpoints are exact
rationals the document already carries.

**(2) The endpoints are corroborated on the shipped document, and the first reading of the
corroboration was WRONG.** Four entries report `is_variable_power`; three declare a real
scalar zero and are the variable-power buildings, and the fourth is the struct-range entry,
which declares no scalar and is produced in nothing.

The obvious cross-check is equality - does the recipe's `constant` equal the building's
estimated minimum, and `constant + factor` its estimated maximum. Measured over the recipes
each building actually produces, that holds on 25 of 25 for one building and 6 of 6 for a
second, and on **0 of 12** for the third, whose recipes carry two distinct bands. Equality
is therefore refused by the document itself.

What does hold is the envelope. Taking the minimum of `constant` and the maximum of
`constant + factor` across each building's own recipes reproduces its declared estimated
range on **3 of 3** buildings, exactly. And every individual pairing lies inside its
building's envelope: **43 of 43**.

**(3) Containment is not vacuous.** Asked against every building-and-recipe pairing the
document does NOT declare, containment rejects **1705 of 2573** mispairings. A check that
accepted everything would be worth nothing; this one carries most of the population.

**(4) The curve is not in the docs data, so no scalar average is recoverable.** The cycle
average is the integral of `mPowerConsumptionCurve`, a `UCurveFloat` asset reference. The
headers declare the member; they carry no curve values, and the docs document exports none.
The header's own normalization claim is a SHOULD rather than a MUST, so even the endpoints
are exact only under the normalization the same sentence assumes - which the two
independent corroborations above are what make it safe to adopt.

## Decision

1. `clockspeed/solve/power.py` gains `bounded_draw`, which answers the two shapes that
   declare no scalar with two exact `Fraction` bounds at the reference clock. The
   variable shape takes its bounds from the recipe through the law; the struct-range shape
   reads both bounds off the declaration and consults no recipe.

2. **The cross-check against the building's estimated range is CONTAINMENT.** It is
   published as `BoundedDraw.within_estimate`, re-measured on every call rather than
   trusted from this ADR, and `None` where there is no independent second source. Equality
   is refused, and the reason is written into the code beside the check so nobody
   re-tightens it.

3. **No scalar is published, and `BoundedDraw` has no field that could hold one** - the
   same fence `ClockCeiling` carries. A midpoint would be an invented number in the right
   units, indistinguishable from a measured one, for the three biggest loads in the game.

4. The bounds are at the reference clock only. Away from it the irrational term
   `draw_at_clock` defers multiplies both bounds, and this type deliberately does not carry
   it.

5. `variable_power_inputs` keeps its shape and its `modeled` of False. It is the
   uncollapsed view of the four operands; its reason now names `bounded_draw` as the
   function that applies the law, because "no law is applied here" read as "no law anywhere"
   is exactly how a caller re-invents one.

## Consequences

- The advice path can bound the draw of the three variable-power buildings and the
  struct-range entry instead of dropping them. It still cannot total them into a single
  megawatt figure, and `clockspeed/audit/balance.py` continues to report them as gaps - a
  bounded gap is narrower than an unmodeled one, but converting the world draw into an
  interval is a change to that module's published shape and is filed separately.

- If a future patch ships a curve whose range is not normalized to `[0.0, 1.0]`, the
  endpoints stop being the bounds. The tripwire already exists and needs no new mechanism:
  `within_estimate` goes False across a building's own recipes, and the envelope relation
  in the evidence above stops reproducing the declared estimate.

- This ADR does NOT license reading the widely-known figures for these buildings out of
  general knowledge, and it does not touch ADR 0005's ceiling question. The two operands
  were measured; nothing else was.
