"""The hand-authored synthetic solve corpus every phase 3 slice tests against.

WHY THIS IS BUILT THROUGH THE REAL SEAM AND NEVER HAND-CONSTRUCTED
-------------------------------------------------------------------
Everything below is docs TEXT, loaded through the real
``clockspeed.data.docs_extract.load_document`` into the real
``clockspeed.data.registry.build_registry``. Hand-constructing a
:class:`~clockspeed.data.registry.Registry` object would be faster and would be
worthless: CONVENTIONS.md section 7.2 records that a fixture built parallel to
the implementation stays green through the real defect, and
``tests/data/synthetic.py`` states the same rule for the data layer. It binds
here too. The unit normalization in C2 and C3 is the concrete case - a corpus
that assembled ``RecipeIO`` objects by hand would carry whatever cubic metres
its author typed, and could never catch the litre conversion happening twice or
not at all.

WHY THE BLOB HELPERS ARE IMPORTED RATHER THAN REWRITTEN
--------------------------------------------------------
``amount_blob`` and ``class_path_blob`` come from ``tests/data/synthetic.py``,
where ``ANCHOR_INGREDIENTS_BLOB`` pins them against a hand-written literal that
``tests/data/test_registry.py`` asserts on. ``item_path`` is reused too, through
``amount_blob``, which builds every item reference with it. A second
implementation of Unreal's blob grammar in this file would be a copy that drifts,
and drifts silently, because both copies would parse under the same parser.

The ``KEY_*`` spellings are imported from the same place for the same reason.
Two of them are MISSPELLED in the shipped game data - ``mManufactoringDuration``
and ``mEstimatedMininumPowerConsumption`` - and the rule that matters is that a
fixture must not import them from the MODULE UNDER TEST, since an
autocomplete-driven "correction" in the registry would then correct the fixture
too. Importing from the sibling fixture preserves that property exactly: those
literals are independently anchored against the registry's constants by
``tests/data/test_registry.py``.

HOW THIS CORPUS DIFFERS FROM ``tests/data/synthetic.py``
---------------------------------------------------------
That one is a PARSER-TRAP corpus: duplicate ClassNames, missing forms,
unparsable numbers, an unknown group, a malformed group. It owns all of that.

This one is a SOLVER corpus and must build with EMPTY warnings and no unknown
groups, because a solve test handed a registry with something quietly missing
from it - an unresolved produced-in token, an item with no descriptor - would be
solving a different factory than the one described here. The ``Desc_Solve*`` /
``Build_Solve*`` / ``R_*`` naming keeps the two visibly distinct.

THE CHAINS
----------
Each is a shape that breaks a solver which passes its own tests.

- **C1** linear two-stage. The answer is ``Fraction(10, 3)`` machines, which no
  float represents - it renders as 3.3333333333333335.
- **C2** a fluid, and the do-not-divide-twice trap. The registry ALREADY
  converts litres to cubic metres, so a path that divides again reports 1600
  machines where 8/5 is right, and one that reads raw litres reports 8/5000.
  Both are finite, positive and plausible.
- **C3** the byproduct loop, and the load-bearing case for the whole phase.
  Gadget needs Fluid, Fluid comes back from Residue, Residue comes from Gadget.
  Naive topological recursion does not terminate on it.
- **C4** the same loop driven backwards from a raw-input cap. Its power total
  cross-checks C3's exactly, which is independent evidence about C3.
- **C5** a degenerate optimizer case whose feasible set has exactly ONE member.
- **C6** a zero duration that is MEASURED rather than defaulted.
- **C7** an inconsistent demand. **C8** an underdetermined one.
- **C9** the loop's plausible wrong answer - a negative machine count. Built as
  a VARIANT through :func:`registry_with`, never in the main corpus, which must
  build cleanly.
- **C10** a byproduct reclaimed into an intermediate, whose first solve is not
  its best, by a recipe with no building to price a draw from. A VARIANT,
  through :func:`reclaim_registry`.

WHERE THIS CORPUS DEPARTS FROM ITS BRIEF, AND WHY
---------------------------------------------------
C5's two competing recipes were specified as producing the C3 Gadget. They
produce :data:`SOLVE_TRINKET_ITEM` instead, and the reason is arithmetic rather
than taste. Sharing the product would give Gadget a second producing recipe, and
C3's published machine counts would stop being THE answer: the plan
``Std_Gadget x 2`` also satisfies every balance at 20 Gadget/min, draws 30 MW
against C3's 436/3 MW, and uses fewer machines. A minimizing solver would return
it, so C3's stated answer would be wrong rather than merely non-unique, and every
suite built on this fixture would agree with the wrong number.
``tests/solve/test_synthetic.py::test_c3_gadget_has_exactly_one_producing_recipe``
is the fence that keeps the collision from being reintroduced.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any, Final

from clockspeed.data.docs_extract import DocsDocument, load_document
from clockspeed.data.registry import Registry, build_registry
from tests.data.synthetic import (
    KEY_CLASS_NAME,
    KEY_CLASSES,
    KEY_DISPLAY_NAME,
    KEY_DURATION,
    KEY_FORM,
    KEY_INGREDIENTS,
    KEY_MAX_POTENTIAL,
    KEY_NATIVE_CLASS,
    KEY_POWER_CONSUMPTION,
    KEY_POWER_EXPONENT,
    KEY_PRODUCED_IN,
    KEY_PRODUCT,
    amount_blob,
    class_path_blob,
)

# ---------------------------------------------------------------------------
# Units and scales
# ---------------------------------------------------------------------------

#: Rates throughout this corpus are per machine per MINUTE, while every duration
#: in the document is in seconds. rate = amount * 60 / duration_seconds.
SECONDS_PER_MINUTE: Final = 60

#: The registry's fluid scale. Named here ONLY so a test can express the
#: divide-twice trap without restating 1000; nothing in this file divides by it.
#: The registry has already done that conversion by the time anything here reads
#: an amount.
LITRES_PER_CUBIC_METRE: Final = 1000

# ---------------------------------------------------------------------------
# Group short names - all inside the docs_extract known set, so the corpus
# reports no unknown groups
# ---------------------------------------------------------------------------

ITEM_GROUP: Final = "FGItemDescriptor"
RESOURCE_GROUP: Final = "FGResourceDescriptor"
BUILDING_DESCRIPTOR_GROUP: Final = "FGBuildingDescriptor"
MANUFACTURER_GROUP: Final = "FGBuildableManufacturer"
RECIPE_GROUP: Final = "FGRecipe"

# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

#: The one declared raw input. Every chain bottoms out here.
SOLVE_ORE_ITEM: Final = "Desc_SolveOre_C"

SOLVE_PLATE_ITEM: Final = "Desc_SolvePlate_C"
SOLVE_ROD_ITEM: Final = "Desc_SolveRod_C"

#: RF_LIQUID. Its amounts are litres in the document and cubic metres by the
#: time the registry publishes them.
SOLVE_FLUID_ITEM: Final = "Desc_SolveFluid_C"

SOLVE_GADGET_ITEM: Final = "Desc_SolveGadget_C"

#: RF_LIQUID, and a BYPRODUCT - the output that closes the C3 loop.
SOLVE_RESIDUE_ITEM: Final = "Desc_SolveResidue_C"

#: C5. It has a DESCRIPTOR, so every amount referencing it is unit-resolvable and
#: the corpus still builds clean, but it has no producing recipe and is not raw.
#: What makes Alt_Gadget infeasible is the absence of a ROUTE, not of a
#: descriptor - a corpus that simply omitted the descriptor would be testing the
#: registry's unknown-item warning instead.
SOLVE_RARE_ITEM: Final = "Desc_SolveRare_C"

#: C5's product. Deliberately NOT SOLVE_GADGET_ITEM - see the module docstring.
SOLVE_TRINKET_ITEM: Final = "Desc_SolveTrinket_C"

#: C7. Demanded by R_Orphan, produced by nothing, and not raw.
SOLVE_ORPHAN_ITEM: Final = "Desc_SolveOrphan_C"

#: C7's product, reachable only through the unproducible item above.
SOLVE_RELIC_ITEM: Final = "Desc_SolveRelic_C"

#: C8. Two recipes produce it and nothing tells them apart.
SOLVE_TWIN_ITEM: Final = "Desc_SolveTwin_C"

#: C6's product: a BUILDING DESCRIPTOR at Amount=1 with form RF_INVALID, which
#: is the measured shape of a build-gun recipe's product side. RF_INVALID is a
#: third case and not a synonym for solid.
SOLVE_SMELTER_DESCRIPTOR: Final = "Desc_SolveSmelter_C"

#: The declared raw inputs. A solver treats these as available without bound;
#: anything outside this set and outside SOLVE_PRODUCED is unreachable.
SOLVE_RAW_ITEMS: Final = frozenset({SOLVE_ORE_ITEM})

#: Every item at least one recipe in the main corpus produces. Stated here and
#: VERIFIED against the built registry by test_synthetic.py rather than derived,
#: so that a recipe accidentally losing its product turns this into a finding
#: instead of quietly shrinking a derived set.
SOLVE_PRODUCED: Final = frozenset(
    {
        SOLVE_PLATE_ITEM,
        SOLVE_ROD_ITEM,
        SOLVE_FLUID_ITEM,
        SOLVE_GADGET_ITEM,
        SOLVE_RESIDUE_ITEM,
        SOLVE_TRINKET_ITEM,
        SOLVE_RELIC_ITEM,
        SOLVE_TWIN_ITEM,
        SOLVE_SMELTER_DESCRIPTOR,
    }
)

# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------

SOLVE_SMELTER_BUILDING: Final = "Build_SolveSmelter_C"
SOLVE_ASSEMBLER_BUILDING: Final = "Build_SolveAssembler_C"
SOLVE_REFINERY_BUILDING: Final = "Build_SolveRefinery_C"

SOLVE_BUILDINGS: Final = (
    SOLVE_SMELTER_BUILDING,
    SOLVE_ASSEMBLER_BUILDING,
    SOLVE_REFINERY_BUILDING,
)

SMELTER_POWER_MW: Final = Fraction(4)
ASSEMBLER_POWER_MW: Final = Fraction(15)
REFINERY_POWER_MW: Final = Fraction(30)

#: The clock exponent, as the document carries it and as the registry publishes
#: it. Not representable in binary floating point, which is the point: float()
#: accepts this string and silently substitutes a different number.
POWER_EXPONENT_TEXT: Final = "1.321929"
POWER_EXPONENT: Final = Fraction(1321929, 1000000)

#: ``mMaxPotential``. It is the UN-SHARDED BASE and is NOT the overclock ceiling
#: (ADR 0005, ADR 0006); reading it as one caps every solve at 100 percent. It is
#: carried in the corpus text so a slice that reads it has synthetic data to read.
#:
#: ASSERTED against Building.unsharded_clock_base in test_synthetic.py by
#: test_every_building_carries_the_unsharded_clock_base. The field landed in
#: clockspeed/data/registry.py under ADR 0006, so the assertion this comment
#: once deferred is now owed and paid.
UNSHARDED_CLOCK_BASE_TEXT: Final = "1.000000"
UNSHARDED_CLOCK_BASE: Final = Fraction(1)

# ---------------------------------------------------------------------------
# Recipes. ORDER MATTERS - see ALT_GADGET_RECIPE.
# ---------------------------------------------------------------------------

#: C5, and declared FIRST in the whole recipe group on purpose. A stub that
#: picks by registry order must pick the INFEASIBLE candidate, or it passes and
#: the feasibility check never gets written.
ALT_GADGET_RECIPE: Final = "Alt_Gadget"

#: C5, the only feasible member of that pair.
STD_GADGET_RECIPE: Final = "Std_Gadget"

PLATE_RECIPE: Final = "R_Plate"
ROD_RECIPE: Final = "R_Rod"
FLUID_RECIPE: Final = "R_Fluid"
GADGET_RECIPE: Final = "R_Gadget"
RECOVER_RECIPE: Final = "R_Recover"

#: C6. Zero duration, no automated producer, product is a building descriptor.
ZERO_DURATION_RECIPE: Final = "R_BuildGun"

#: C7. Its only ingredient is produced by nothing and is not raw.
ORPHAN_RECIPE: Final = "R_Orphan"

#: C8. Byte-for-byte equivalent in every objective.
TWIN_A_RECIPE: Final = "R_TwinA"
TWIN_B_RECIPE: Final = "R_TwinB"

#: C9, and deliberately NOT in the main corpus. Reach it through
#: :func:`rich_recovery_registry`.
RICH_RECOVER_RECIPE: Final = "R_RecoverRich"

#: C10, and deliberately NOT in the main corpus. Reach both through
#: :func:`reclaim_registry`.
SCRAP_ROD_RECIPE: Final = "R_ScrapRod"
RECLAIM_RECIPE: Final = "R_Reclaim"

SOLVE_RECIPES: Final = (
    ALT_GADGET_RECIPE,
    STD_GADGET_RECIPE,
    PLATE_RECIPE,
    ROD_RECIPE,
    FLUID_RECIPE,
    GADGET_RECIPE,
    RECOVER_RECIPE,
    ZERO_DURATION_RECIPE,
    ORPHAN_RECIPE,
    TWIN_A_RECIPE,
    TWIN_B_RECIPE,
)

# ---------------------------------------------------------------------------
# Durations, in seconds per cycle
# ---------------------------------------------------------------------------

PLATE_DURATION_S: Final = Fraction(2)
ROD_DURATION_S: Final = Fraction(4)
FLUID_DURATION_S: Final = Fraction(6)
GADGET_DURATION_S: Final = Fraction(6)
RECOVER_DURATION_S: Final = Fraction(4)
TRINKET_DURATION_S: Final = Fraction(6)
ORPHAN_DURATION_S: Final = Fraction(6)
TWIN_DURATION_S: Final = Fraction(6)

#: C6. Exactly zero, and MEASURED: the registry keeps a declared zero and skips
#: a recipe whose duration key is absent, so this really is an input the solve
#: path receives rather than a defensive branch. Its rate is undefined and
#: nothing may divide by it.
ZERO_DURATION: Final = Fraction(0)

# ---------------------------------------------------------------------------
# C1 - LINEAR TWO-STAGE
#
#   R_Plate  1 Ore   -> 1 Plate, 2 s, Smelter   ->  60/2 = 30 Plate/machine/min
#   R_Rod    1 Plate -> 1 Rod,   4 s, Smelter   ->  60/4 = 15 Rod/machine/min
#
#   Target 50 Rod/min:  rod machines   50 / 15 = 10/3
#                       plate demand   (10/3) * 15 = 50/min
#                       plate machines 50 / 30 = 5/3
#                       ore            (5/3) * 30 = 50/min
#                       power          (10/3 + 5/3) * 4 MW = 20 MW exactly
# ---------------------------------------------------------------------------

C1_PLATE_PER_MACHINE: Final = Fraction(30)
C1_ROD_PER_MACHINE: Final = Fraction(15)

#: Plate consumed by ONE R_Rod machine per minute. Equal to the Rod output rate
#: here only because the recipe is one-for-one; it is named separately so a
#: change to the ratio cannot hide behind the coincidence.
C1_PLATE_DEMAND_PER_MACHINE: Final = Fraction(15)

C1_ROD_TARGET: Final = Fraction(50)
C1_ROD_MACHINES: Final = Fraction(10, 3)
C1_PLATE_DEMAND: Final = Fraction(50)
C1_PLATE_MACHINES: Final = Fraction(5, 3)
C1_ORE_DEMAND: Final = Fraction(50)
C1_POWER_MW: Final = Fraction(20)

#: What ``repr(float(Fraction(10, 3)))`` produces. The float is not a rounded
#: 10/3, it is a different number, and it renders as a perfectly plausible one.
C1_ROD_MACHINES_FLOAT_REPR: Final = "3.3333333333333335"

# ---------------------------------------------------------------------------
# C2 - FLUID, THE DO-NOT-DIVIDE-TWICE TRAP
#
#   R_Fluid  1 Ore -> 2500 L Fluid (RF_LIQUID), 6 s, Refinery
#
#   The registry ALREADY converts litres to cubic metres and publishes
#   Fraction(2500, 1000) = 5/2 per cycle. NOTHING in this fixture or its tests
#   divides by 1000 again.
#
#   10 cycles/min -> 25 m3/min.  Target 40 m3/min: 40 / 25 = 8/5 refineries,
#   ore 10 * 8/5 = 16/min, power (8/5) * 30 = 48 MW.
# ---------------------------------------------------------------------------

#: The verbatim litre amount the document carries, before the registry's join.
C2_FLUID_LITRES_PER_CYCLE: Final = 2500

#: What the registry publishes: cubic metres, converted exactly ONCE.
C2_FLUID_PER_CYCLE_M3: Final = Fraction(5, 2)

C2_CYCLES_PER_MINUTE: Final = Fraction(10)
C2_FLUID_PER_MACHINE: Final = Fraction(25)
C2_FLUID_TARGET: Final = Fraction(40)
C2_REFINERY_MACHINES: Final = Fraction(8, 5)
C2_ORE_DEMAND: Final = Fraction(16)
C2_POWER_MW: Final = Fraction(48)

#: The answer a path that divides the already-normalized amount AGAIN produces.
#: A thousand times too many machines, and it renders as a whole number.
C2_DIVIDED_TWICE_MACHINES: Final = Fraction(1600)

#: The answer a path that reads the raw litre figure produces. A thousand times
#: too few, and still finite and positive.
C2_READ_AS_LITRES_MACHINES: Final = Fraction(8, 5000)

# ---------------------------------------------------------------------------
# C3 - THE BYPRODUCT LOOP, the load-bearing case for the whole phase
#
#   R_Gadget   2 Plate + 3000 L Fluid -> 1 Gadget + 1000 L Residue, 6 s, Refinery
#   R_Recover  2000 L Residue         -> 1000 L Fluid,              4 s, Refinery
#   plus R_Fluid (C2) and R_Plate (C1).
#
#   The cycle is REAL: Gadget needs Fluid, Fluid comes from Residue, Residue
#   comes from Gadget. Naive topological recursion does not terminate.
#
#   Per machine per minute:
#     R_Gadget   Gadget +10, Plate -20, Fluid -30, Residue +10
#     R_Recover  Residue -30, Fluid +15
#     R_Fluid    Fluid +25,  Ore -10
#     R_Plate    Plate +30,  Ore -30
#
#   Target 20 Gadget/min, with a=R_Gadget, b=R_Recover, c=R_Fluid, d=R_Plate:
#     Gadget   10a = 20              -> a = 2
#     Residue  10a - 30b = 0         -> b = 2/3
#     Fluid    -30a + 15b + 25c = 0  -> -60 + 10 + 25c = 0 -> c = 2
#     Plate    -20a + 30d = 0        -> d = 4/3
#     Ore      10c + 30d = 20 + 40   = 60/min
#     Power    30*(2 + 2/3 + 2) + 4*(4/3) = 140 + 16/3 = 436/3 MW
# ---------------------------------------------------------------------------

C3_GADGET_YIELD: Final = Fraction(10)
C3_GADGET_PLATE_DRAW: Final = Fraction(-20)
C3_GADGET_FLUID_DRAW: Final = Fraction(-30)
C3_GADGET_RESIDUE_YIELD: Final = Fraction(10)
C3_RECOVER_RESIDUE_DRAW: Final = Fraction(-30)
C3_RECOVER_FLUID_YIELD: Final = Fraction(15)
C3_FLUID_YIELD: Final = Fraction(25)
C3_FLUID_ORE_DRAW: Final = Fraction(-10)
C3_PLATE_YIELD: Final = Fraction(30)
C3_PLATE_ORE_DRAW: Final = Fraction(-30)

C3_GADGET_TARGET: Final = Fraction(20)
C3_GADGET_MACHINES: Final = Fraction(2)
C3_RECOVER_MACHINES: Final = Fraction(2, 3)
C3_FLUID_MACHINES: Final = Fraction(2)
C3_PLATE_MACHINES: Final = Fraction(4, 3)
C3_ORE_DEMAND: Final = Fraction(60)
C3_POWER_MW: Final = Fraction(436, 3)

#: What ``repr(float(Fraction(436, 3)))`` produces.
C3_POWER_FLOAT_REPR: Final = "145.33333333333334"

# ---------------------------------------------------------------------------
# C4 - THE LOOP, REVERSE DIRECTION
#
#   Raw input capped at 45 Ore/min, maximize Gadget. C3 consumed 60 Ore/min for
#   20 Gadget/min, so the scale factor is 45/60 = 3/4.
#
#     Gadget 15/min, a = 3/2, b = 1/2, c = 3/2, d = 1
#     Ore check   10*(3/2) + 30*1 = 45
#     Power       30*(7/2) + 4*1 = 109 MW
#
#   Cross-check: 436/3 * 3/4 = 109 EXACTLY. That is an independent confirmation
#   of C3, because the two chains were derived from opposite directions.
# ---------------------------------------------------------------------------

C4_ORE_CAP: Final = Fraction(45)
C4_SCALE: Final = Fraction(3, 4)
C4_GADGET_RATE: Final = Fraction(15)
C4_GADGET_MACHINES: Final = Fraction(3, 2)
C4_RECOVER_MACHINES: Final = Fraction(1, 2)
C4_FLUID_MACHINES: Final = Fraction(3, 2)
C4_PLATE_MACHINES: Final = Fraction(1)
C4_POWER_MW: Final = Fraction(109)

# ---------------------------------------------------------------------------
# C5 - THE DEGENERATE OPTIMIZER CASE
#
#   Alt_Gadget  1 Ore + 1 Rare -> 3 Trinket, 6 s, Assembler   [declared FIRST]
#   Std_Gadget  4 Ore          -> 1 Trinket, 6 s, Assembler
#
#   Desc_SolveRare_C has NO producing recipe and is not a declared raw input, so
#   every plan using Alt_Gadget is INFEASIBLE. The feasible set is the singleton
#   {Std_Gadget}.
#
#   Alt_Gadget is declared first, so a registry-order stub picks the wrong one,
#   AND it wins on every objective, so a score-before-feasibility greedy picks
#   the wrong one too. Both stubs must fail.
#
#   Target 30 Trinket/min -> Std_Gadget x 3, ore 120/min, power 45 MW.
# ---------------------------------------------------------------------------

C5_TRINKET_TARGET: Final = Fraction(30)

C5_STD_PER_MACHINE: Final = Fraction(10)
C5_STD_ORE_DRAW: Final = Fraction(-40)
C5_STD_MACHINES: Final = Fraction(3)
C5_ORE_DEMAND: Final = Fraction(120)
C5_POWER_MW: Final = Fraction(45)

C5_ALT_PER_MACHINE: Final = Fraction(30)
C5_ALT_ORE_DRAW: Final = Fraction(-10)
C5_ALT_RARE_DRAW: Final = Fraction(-10)

#: What Alt_Gadget WOULD cost if its Rare input were reachable. Named with the
#: conditional in the name on purpose: these are the numbers a greedy that
#: scores before it checks feasibility will report, and they are strictly better
#: than the correct answer on every axis.
C5_ALT_MACHINES_IF_FEASIBLE: Final = Fraction(1)
C5_ALT_ORE_IF_FEASIBLE: Final = Fraction(10)
C5_ALT_POWER_MW_IF_FEASIBLE: Final = Fraction(15)

# ---------------------------------------------------------------------------
# C6 zero duration, C7 inconsistent, C8 underdetermined
# ---------------------------------------------------------------------------

#: C6. Plate consumed per cycle by the build-gun-shaped recipe. There is no
#: per-minute figure for it, and that is the whole point.
C6_PLATE_PER_CYCLE: Final = Fraction(10)

#: C7. Orphan consumed per cycle. No per-minute demand is published because the
#: chain is unsatisfiable, and publishing one would imply it could be met.
C7_ORPHAN_PER_CYCLE: Final = Fraction(2)

#: C8. Both twins produce exactly this, from exactly the same input, in exactly
#: the same building. There is no tie-break, by construction.
C8_TWIN_PER_MACHINE: Final = Fraction(10)
C8_TWIN_ORE_DRAW: Final = Fraction(-10)

# ---------------------------------------------------------------------------
# C9 - NEGATIVE SOLUTION, the loop's plausible wrong answer
#
#   R_RecoverRich  2000 L Residue -> 9000 L Fluid, 4 s  ->  135 m3/min out
#
#   With a = 2 and b = 2/3 unchanged from C3, the Fluid balance becomes
#   -60 + 90 + 25c = 0 -> c = -6/5.
#
#   A raw linear solve returns a NEGATIVE machine count - a recipe run backwards
#   - and a confident-looking plan around it. This variant exists so a later
#   slice can prove it REFUSES. It is deliberately not in the main corpus.
# ---------------------------------------------------------------------------

C9_RICH_FLUID_LITRES_PER_CYCLE: Final = 9000
C9_RICH_FLUID_YIELD: Final = Fraction(135)
C9_FLUID_MACHINES: Final = Fraction(-6, 5)

# ---------------------------------------------------------------------------
# C10 - A FIRST SOLVE THAT IS NOT THE BEST, AND A STEP NO DRAW CAN PRICE
#
#   R_ScrapRod  1 Plate -> 1 Rod + 1000 L Residue, 4 s, Assembler
#   R_Reclaim   2000 L Residue -> 1 Plate,         4 s, NO automated producer
#   plus C1's R_Plate.
#
#   Per machine per minute:
#     R_Plate     Ore -30, Plate +30                 Smelter, 4 MW
#     R_ScrapRod  Plate -15, Rod +15, Residue +15    Assembler, 15 MW
#     R_Reclaim   Residue -30, Plate +15             no building, so no draw
#
#   Target 30 Rod/min, byproducts sinkable; p, s, r the machine counts:
#     {R_Plate, R_ScrapRod}             Rod 15s = 30 -> s = 2; Plate 30p - 30 = 0
#                                       -> p = 1; Residue vented at 30.
#                                       Ore 30, machines 3, power 4 + 30 = 34 MW
#     {R_Plate, R_ScrapRod, R_Reclaim}  s = 2; Residue 30 - 30r = 0 -> r = 1;
#                                       Plate 30p - 30 + 15 = 0 -> p = 1/2.
#                                       Ore 15, machines 7/2, power UNPRICEABLE
#
#   No other subset solves: R_ScrapRod is the only Rod producer, and without
#   R_Plate the Plate balance -15s + 15r = 0 and the Residue balance
#   15s - 30r = 0 contradict each other at s = 2. So raw prefers the three
#   recipes, buildings prefers the two, and power cannot be answered at all -
#   the three-recipe subset solves and R_Reclaim has no draw. A VARIANT, built
#   through :func:`reclaim_registry`; the main corpus builds without it.
# ---------------------------------------------------------------------------

C10_DURATION_S: Final = Fraction(4)

#: Residue on the wire, in LITRES. The registry converts; nothing here does.
C10_SCRAP_ROD_RESIDUE_LITRES: Final = 1000
C10_RECLAIM_RESIDUE_LITRES: Final = 2000

C10_ROD_TARGET: Final = Fraction(30)

#: {R_Plate, R_ScrapRod}.
C10_FIRST_PLATE_MACHINES: Final = Fraction(1)
C10_SCRAP_ROD_MACHINES: Final = Fraction(2)
C10_FIRST_ORE_DEMAND: Final = Fraction(30)
C10_FIRST_MACHINE_TOTAL: Final = Fraction(3)
C10_FIRST_POWER_MW: Final = Fraction(34)

#: {R_Plate, R_ScrapRod, R_Reclaim}. R_ScrapRod runs 2 machines here too.
C10_RECLAIMED_PLATE_MACHINES: Final = Fraction(1, 2)
C10_RECLAIM_MACHINES: Final = Fraction(1)
C10_RECLAIMED_ORE_DEMAND: Final = Fraction(15)

# ---------------------------------------------------------------------------
# Document construction
# ---------------------------------------------------------------------------


def building_path(class_name: str) -> str:
    """Build the bare object path an ``mProducedIn`` entry carries.

    A DIFFERENT grammar from an item-amount path: no ``Type'...'`` wrapper and
    no embedded single quote. :func:`class_path_blob` adds the quoting.

    Args:
        class_name: A building ClassName, e.g. ``Build_SolveSmelter_C``.

    Returns:
        The path, whose trailing token after the final ``.`` is what the
        registry resolves against its modeled buildings.
    """
    return f"/Game/Solve/{class_name.removesuffix('_C')}.{class_name}"


def _group(short_name: str, entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Wrap entries in the ``{NativeClass, Classes}`` shape the document uses.

    Args:
        short_name: The group's trailing class token, e.g. ``FGRecipe``.
        entries: The group's Classes entries.

    Returns:
        The group as a plain dict, ready for :func:`json.dumps`.
    """
    return {
        KEY_NATIVE_CLASS: f"/Script/CoreUObject.Class'/Script/FactoryGame.{short_name}'",
        KEY_CLASSES: list(entries),
    }


def _item_entry(class_name: str, display_name: str, form: str = "RF_SOLID") -> dict[str, str]:
    """Build one item descriptor entry.

    Args:
        class_name: The entry's ClassName.
        display_name: Its mDisplayName. NEVER empty - an empty one is flagged,
            and this corpus must build with no warnings at all.
        form: Its mForm. RF_LIQUID is what makes an amount litres.

    Returns:
        The entry mapping, every value a string as in the real document.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: display_name,
        KEY_FORM: form,
    }


def _building_entry(class_name: str, display_name: str, power_mw: Fraction) -> dict[str, str]:
    """Build one power-consuming buildable entry.

    Args:
        class_name: The entry's ClassName - the token an mProducedIn path
            resolves to.
        display_name: Its mDisplayName, on the BUILDABLE entry rather than on
            the building descriptor.
        power_mw: The draw. Rendered to six decimal places, matching the
            document's own formatting, and read back as an exact Fraction.

    Returns:
        The entry mapping.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: display_name,
        KEY_POWER_CONSUMPTION: f"{int(power_mw)}.000000",
        KEY_POWER_EXPONENT: POWER_EXPONENT_TEXT,
        KEY_MAX_POTENTIAL: UNSHARDED_CLOCK_BASE_TEXT,
    }


def _recipe_entry(
    class_name: str,
    duration: Fraction,
    ingredients: Sequence[tuple[str, int]],
    products: Sequence[tuple[str, int]],
    building: str | None,
) -> dict[str, str]:
    """Build one recipe entry.

    Args:
        class_name: The entry's ClassName.
        duration: Seconds per cycle. Rendered to six decimals, as the document
            does. A zero here is a MEASURED zero and the registry keeps it.
        ingredients: ``(item ClassName, verbatim amount)`` pairs. Fluid amounts
            are LITRES - the registry converts, and nothing here does.
        products: The product side, byproducts included.
        building: The producing building, or None for no automated producer -
            which yields an empty mProducedIn blob, a real and valid value.

    Returns:
        The entry mapping.
    """
    return {
        KEY_CLASS_NAME: class_name,
        KEY_DISPLAY_NAME: class_name.removeprefix("R_"),
        KEY_DURATION: f"{int(duration)}.000000",
        KEY_INGREDIENTS: amount_blob(ingredients),
        KEY_PRODUCT: amount_blob(products),
        KEY_PRODUCED_IN: class_path_blob([building_path(building)] if building else []),
    }


_ITEM_ENTRIES: Final = [
    _item_entry(SOLVE_PLATE_ITEM, "Solve Plate"),
    _item_entry(SOLVE_ROD_ITEM, "Solve Rod"),
    _item_entry(SOLVE_FLUID_ITEM, "Solve Fluid", "RF_LIQUID"),
    _item_entry(SOLVE_GADGET_ITEM, "Solve Gadget"),
    _item_entry(SOLVE_RESIDUE_ITEM, "Solve Residue", "RF_LIQUID"),
    _item_entry(SOLVE_RARE_ITEM, "Solve Rare"),
    _item_entry(SOLVE_TRINKET_ITEM, "Solve Trinket"),
    _item_entry(SOLVE_ORPHAN_ITEM, "Solve Orphan"),
    _item_entry(SOLVE_RELIC_ITEM, "Solve Relic"),
    _item_entry(SOLVE_TWIN_ITEM, "Solve Twin"),
]

_RESOURCE_ENTRIES: Final = [
    _item_entry(SOLVE_ORE_ITEM, "Solve Ore"),
]

# The build-gun product side. Its display name is NON-empty here, unlike the 547
# measured FGBuildingDescriptor entries: tests/data/synthetic.py owns that trap,
# and this corpus must build with no warnings.
_BUILDING_DESCRIPTOR_ENTRIES: Final = [
    _item_entry(SOLVE_SMELTER_DESCRIPTOR, "Solve Smelter", "RF_INVALID"),
]

_BUILDING_ENTRIES: Final = [
    _building_entry(SOLVE_SMELTER_BUILDING, "Solve Smelter", SMELTER_POWER_MW),
    _building_entry(SOLVE_ASSEMBLER_BUILDING, "Solve Assembler", ASSEMBLER_POWER_MW),
    _building_entry(SOLVE_REFINERY_BUILDING, "Solve Refinery", REFINERY_POWER_MW),
]

# ORDER IS LOAD-BEARING: Alt_Gadget first, so a registry-order stub picks the
# infeasible candidate. See ALT_GADGET_RECIPE.
_RECIPE_ENTRIES: Final = [
    _recipe_entry(
        ALT_GADGET_RECIPE,
        TRINKET_DURATION_S,
        [(SOLVE_ORE_ITEM, 1), (SOLVE_RARE_ITEM, 1)],
        [(SOLVE_TRINKET_ITEM, 3)],
        SOLVE_ASSEMBLER_BUILDING,
    ),
    _recipe_entry(
        STD_GADGET_RECIPE,
        TRINKET_DURATION_S,
        [(SOLVE_ORE_ITEM, 4)],
        [(SOLVE_TRINKET_ITEM, 1)],
        SOLVE_ASSEMBLER_BUILDING,
    ),
    _recipe_entry(
        PLATE_RECIPE,
        PLATE_DURATION_S,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_PLATE_ITEM, 1)],
        SOLVE_SMELTER_BUILDING,
    ),
    _recipe_entry(
        ROD_RECIPE,
        ROD_DURATION_S,
        [(SOLVE_PLATE_ITEM, 1)],
        [(SOLVE_ROD_ITEM, 1)],
        SOLVE_SMELTER_BUILDING,
    ),
    # LITRES on the wire. The registry publishes 5/2 cubic metres.
    _recipe_entry(
        FLUID_RECIPE,
        FLUID_DURATION_S,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_FLUID_ITEM, C2_FLUID_LITRES_PER_CYCLE)],
        SOLVE_REFINERY_BUILDING,
    ),
    # The loop's forward half: consumes Fluid, emits Residue as a BYPRODUCT.
    _recipe_entry(
        GADGET_RECIPE,
        GADGET_DURATION_S,
        [(SOLVE_PLATE_ITEM, 2), (SOLVE_FLUID_ITEM, 3000)],
        [(SOLVE_GADGET_ITEM, 1), (SOLVE_RESIDUE_ITEM, 1000)],
        SOLVE_REFINERY_BUILDING,
    ),
    # The loop's return half: turns the byproduct back into the input.
    _recipe_entry(
        RECOVER_RECIPE,
        RECOVER_DURATION_S,
        [(SOLVE_RESIDUE_ITEM, 2000)],
        [(SOLVE_FLUID_ITEM, 1000)],
        SOLVE_REFINERY_BUILDING,
    ),
    # C6. Zero duration and NO automated producer, which is the build-gun shape.
    # The produced-in blob is empty rather than naming an unresolvable token,
    # because an unresolved token would flag a warning and this corpus builds
    # clean - tests/data/synthetic.py owns the unresolvable-token case.
    _recipe_entry(
        ZERO_DURATION_RECIPE,
        ZERO_DURATION,
        [(SOLVE_PLATE_ITEM, int(C6_PLATE_PER_CYCLE))],
        [(SOLVE_SMELTER_DESCRIPTOR, 1)],
        None,
    ),
    # C7. Its only ingredient is produced by nothing and is not raw, so nothing
    # downstream can satisfy a demand for Relic at any rate at all.
    _recipe_entry(
        ORPHAN_RECIPE,
        ORPHAN_DURATION_S,
        [(SOLVE_ORPHAN_ITEM, int(C7_ORPHAN_PER_CYCLE))],
        [(SOLVE_RELIC_ITEM, 1)],
        SOLVE_ASSEMBLER_BUILDING,
    ),
    # C8. Identical in duration, ingredients, products and building. Any split
    # between them satisfies every constraint equally.
    _recipe_entry(
        TWIN_A_RECIPE,
        TWIN_DURATION_S,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_TWIN_ITEM, 1)],
        SOLVE_ASSEMBLER_BUILDING,
    ),
    _recipe_entry(
        TWIN_B_RECIPE,
        TWIN_DURATION_S,
        [(SOLVE_ORE_ITEM, 1)],
        [(SOLVE_TWIN_ITEM, 1)],
        SOLVE_ASSEMBLER_BUILDING,
    ),
]

#: C9's replacement for R_Recover. Published so a downstream slice names the
#: mutation rather than rebuilding it.
RICH_RECOVERY_ENTRY: Final = _recipe_entry(
    RICH_RECOVER_RECIPE,
    RECOVER_DURATION_S,
    [(SOLVE_RESIDUE_ITEM, 2000)],
    [(SOLVE_FLUID_ITEM, C9_RICH_FLUID_LITRES_PER_CYCLE)],
    SOLVE_REFINERY_BUILDING,
)

#: C10's two additions, published so a downstream slice names them rather than
#: rebuilding them.
SCRAP_ROD_ENTRY: Final = _recipe_entry(
    SCRAP_ROD_RECIPE,
    C10_DURATION_S,
    [(SOLVE_PLATE_ITEM, 1)],
    [(SOLVE_ROD_ITEM, 1), (SOLVE_RESIDUE_ITEM, C10_SCRAP_ROD_RESIDUE_LITRES)],
    SOLVE_ASSEMBLER_BUILDING,
)

#: No automated producer: an empty produced-in blob, a real and valid value, and
#: the shape the power objective cannot price.
RECLAIM_ENTRY: Final = _recipe_entry(
    RECLAIM_RECIPE,
    C10_DURATION_S,
    [(SOLVE_RESIDUE_ITEM, C10_RECLAIM_RESIDUE_LITRES)],
    [(SOLVE_PLATE_ITEM, 1)],
    None,
)


def _document(recipes: Sequence[Mapping[str, Any]]) -> list[Any]:
    """Assemble the whole corpus around a recipe list.

    Args:
        recipes: The recipe entries to carry.

    Returns:
        The top-level group list. Every group name is inside the docs_extract
        known set, so nothing here reports as unknown content.
    """
    return [
        _group(ITEM_GROUP, _ITEM_ENTRIES),
        _group(RESOURCE_GROUP, _RESOURCE_ENTRIES),
        _group(BUILDING_DESCRIPTOR_GROUP, _BUILDING_DESCRIPTOR_ENTRIES),
        _group(MANUFACTURER_GROUP, _BUILDING_ENTRIES),
        _group(RECIPE_GROUP, list(recipes)),
    ]


#: The corpus as docs TEXT, which is what ``load_document`` consumes. Built once
#: at import: the corpus is data and nothing mutates it in place.
DOCS_TEXT: Final = json.dumps(_document(_RECIPE_ENTRIES))


def solve_document() -> DocsDocument:
    """Load the corpus through the real docs_extract seam.

    Returns:
        The loaded document.
    """
    return load_document(DOCS_TEXT)


def document_from_groups(groups: Iterable[Any]) -> DocsDocument:
    """Load an arbitrary group list through the same seam.

    Args:
        groups: Top-level groups, as :func:`_group` builds them.

    Returns:
        The loaded document.
    """
    return load_document(json.dumps(list(groups)))


def solve_registry() -> Registry:
    """Build the main solve corpus through the real seam.

    Loaded and built rather than hand-constructed on purpose - see the module
    docstring. This is the registry every phase 3 slice tests against.

    Returns:
        The registry. It carries NO warnings and NO unknown groups;
        ``tests/solve/test_synthetic.py`` asserts both.
    """
    return build_registry(solve_document())


def registry_with(
    *,
    replace: Mapping[str, Mapping[str, Any]] | None = None,
    add: Sequence[Mapping[str, Any]] = (),
    drop: frozenset[str] = frozenset(),
) -> Registry:
    """Build a VARIANT registry with the recipe list mutated.

    Modeled on ``tests/data/synthetic.py``'s ``grammar_change_document``: the
    variant is assembled as text and loaded through the same seam, so a mutated
    corpus is exercised by exactly the parser and join the real one is. A
    variant that patched a built Registry object would be testing the mutation
    against a model nothing produced.

    The main corpus must build cleanly, so every shape that would flag a warning
    or return an impossible plan lives here instead - C9 above all.

    Args:
        replace: Recipe ClassName to the entry that supersedes it, in place, so
            the substitute keeps the original's REGISTRY ORDER. That matters:
            C5 turns on Alt_Gadget being first, and a replace that appended
            would silently reorder the corpus.
        add: Extra recipe entries, appended after the existing ones.
        drop: Recipe ClassNames to remove entirely.

    Returns:
        The built variant registry.
    """
    replacements = replace or {}
    recipes: list[Mapping[str, Any]] = []
    for entry in _RECIPE_ENTRIES:
        key = entry[KEY_CLASS_NAME]
        if key in drop:
            continue
        recipes.append(replacements.get(key, entry))
    recipes.extend(add)
    return build_registry(document_from_groups(_document(recipes)))


def rich_recovery_registry() -> Registry:
    """Build C9: the variant whose recovery recipe drives the solve negative.

    ``R_Recover`` is REPLACED rather than joined by ``R_RecoverRich``, so the
    Fluid balance has one return path and the negative answer is forced rather
    than merely available. Keeping both would let a solver dodge the case by
    using the ordinary one.

    Returns:
        The variant registry. It builds cleanly - the defect is in the
        arithmetic it implies, not in the data.
    """
    return registry_with(replace={RECOVER_RECIPE: RICH_RECOVERY_ENTRY})


def reclaim_registry() -> Registry:
    """Build C10: the main corpus plus R_ScrapRod and an unpriceable R_Reclaim.

    Appended, so both sort after R_Plate in registry order. Shared by the
    solve-layer arms and the HTTP arms, so the two grade one fixture.

    Returns:
        The variant registry.
    """
    return registry_with(add=[SCRAP_ROD_ENTRY, RECLAIM_ENTRY])
