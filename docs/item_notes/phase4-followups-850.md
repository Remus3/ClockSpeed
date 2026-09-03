# Clockspeed - live per-item detail, phase 4 - save reader, CS-850 to CS-899

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**THIS LEAF HOLDS CS-850 THROUGH CS-899 AND NOTHING ELSE.** Its sibling
`docs/item_notes/phase4-followups.md` holds CS-800 through CS-849. **THAT SIBLING'S NAME
DOES NOT SAY SO AND IT IS NOT THE WHOLE `CS-8nn` BLOCK**, so trust this sentence and the
routing table in `docs/item_notes.md`, never the filename: an ID below CS-850 is in the
sibling and is not here. The sibling kept the unsuffixed name because pointers in
`WAKEUP_NOTES.md` and `docs/LEDGER.md` already spell it; this file took the suffixed one
because it was the file that did not yet exist and so had no pointer to break.

**This is a leaf of `docs/item_notes.md`**, which owns the index and the rules this
file obeys. Read the index for the routing table over every OPEN item, the verbatim
rule, and what this family never contains. Do not restate any of it here.

**What lands in THIS leaf.** Every OPEN item ROADMAP.md files under its `Phase 4` heading whose ID is in
the `CS-8nn` block and AT OR ABOVE CS-850. That block exists because `CS-4nn` filled up at 98 of 100;
an ID still says which phase it came from. Operator decision 2026-08-21. The CS-850 seam
inside the block, and why it sits there rather than at CS-830 or CS-840, is recorded in
`docs/adr/0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md`.

**THIS IS THE LEAF THAT GROWS, WHICH IS WHY THE SEAM LEFT THE HEADROOM ON THIS SIDE.** A
newly filed CS-8nn item takes the next ID after the highest already allocated, so it lands
here rather than in the sibling. Measured at the split: this leaf carried fewer bytes than
the sibling and the larger share of the remaining budget. **MEASURED AGAIN AT THE END OF THE
SAME SESSION, THAT HAD ALREADY REVERSED** - the session-46 records pushed this leaf past the
sibling, so the headroom the seam left on this side was spent inside one session. Read both
figures from `tools/doc_budget.py`; do not trust either sentence for a current number.
**THAT IS NOT A PERMANENT FIX** -
the split divides a population and does not shrink it, and CLOSURE IS STILL THE ONLY
DESIGNED SHRINK, exactly as `docs/adr/0010-item-notes-is-an-index-over-per-phase-leaves.md`
said of the split before this one.

**Bodies are relocated VERBATIM.** Every section below arrived from
`docs/item_notes.md` unedited when that file was split on 2026-08-25, arrived there from
`ROADMAP.md` and `docs/history_notes.md` before that, and arrived here byte-for-byte from
`docs/item_notes/phase4-followups.md`. A body therefore still reads as it did when it was
written, including the parts a later session measured false and corrected in place rather
than rewriting.

**When an item CLOSES its section moves to `docs/history_notes.md`**, not to another
leaf. That move is what keeps this file live.

---

## CS-850

### NOTE - filed 2026-08-24 by the merger, from TWO agents independently

**FOUND TWICE IN ONE SESSION, IN DIFFERENT MODULES, BY AGENTS THAT DID NOT KNOW OF EACH
OTHER.** That is the evidence this is a channel rather than two bugs. The CS-829 builder hit
it first: a test whose every message string was carefully counts-only emitted a mapping keyed
by real save-derived names, because pytest rewrites the assertion and renders the asserted
EXPRESSION independently of the message. The CS-841 adversary hit the same channel from the
other side, on an absolute path rendered into a teardown assertion.

**THE TREE ALREADY KNEW AND SAID SO.** `tests/test_tmp_path_privacy.py`'s own docstring
records that this channel is uncovered - that it is not the assertion-message channel and not
a rendering of a caught exception, so the exception-rendering sweep is structurally blind to
it. The gap was documented and unowned.

**WHY TIER 1.** Non-negotiables 11 and 12 forbid echoing personal data, and this defeats them
on exactly the day a test fails, which is the day nobody is reading carefully. The CS-829
builder's fix is the shape of the remedy - bind every aggregate to a plain scalar BEFORE
asserting on it, so the rendered expression holds a number and nothing else - but the fix
must be applied to the DERIVED POPULATION of shipped assertions, not to the two instances
that happened to be found.

**PROVE IT BY THE RENDERED OUTPUT, NOT BY READING THE MESSAGE.** The message text is the part
that gets reviewed and is exactly the part that does not control this channel.

### CONFIRMED LIVE - recorded 2026-08-24 - RELOCATED 2026-08-25 (session 40)

The site it names was REPAIRED in session 40; see the block below. Full text in
`docs/history_notes.md` under CS-850.

### REFUTED TWICE, MERGED WITH ITS BOUNDARY STATED - recorded 2026-08-25

**FIRST REFUTATION - the derived population was a STRUCTURAL PROXY, not the acceptance's
population.** The acceptance names three kinds of DATA; the guard derived annotated fields
withheld by a hand-written `__repr__`. Seven probe modules carrying a save-derived name or a
home path - a default-`__repr__` dataclass, a bare `str`, a `Path`, a plain dict, a
`NamedTuple`, a fixture return - ALL returned ZERO findings.

**SECOND REFUTATION - THE PROOF REQUIRED THE DEFECT.** Forced arms derived from LIVE
findings, so repairing a leak turned the proof RED. Repaired - **and the same defect was then
found ONE FUNCTION AWAY**, in a partition test requiring the live side to be non-empty. A
tier 1 privacy guard whose green state requires a leak. Both are fixed, and the fix was
validated for real at the CS-829 merge: zero live is now a green state.

**SEVEN OF ELEVEN LIVE FINDINGS WERE FALSE POSITIVES** - 64 per cent of the live tier. A
repr rendering `dict(sorted(self.field.items()))` DISCLOSES that field; it does not mask it.
Only genuine REDUCTIONS withhold. `min` and `max` are NOT reductions in the safe direction:
excluding them makes the guard go SILENT on the whole container rather than louder.

**A DEFECT ITS OWN MUTATION CHECK FOUND THAT NO TEST WOULD HAVE:** `masked_token` is defined
in `clockspeed/save/header.py` and IMPORTED by `clockspeed/save/world.py`, so a
same-module-only mask reader graded `WorldModel.token` DISCLOSED and a re-introduced leak
over the real world token SURVIVED THE SWEEP SILENTLY. Masks now resolve tree-wide.

**WHY IT STAYS OPEN - THE GUARD'S SUBJECT IS STRICTLY SMALLER THAN THE ACCEPTANCE'S.** The
guard reasons about ASSERTED EXPRESSIONS. A failure report ALSO renders the frame's LOCALS
under `-l/--showlocals` and the failing function's own SOURCE LINES. Reproduced: 0
occurrences of a planted token by default, 1 under `-l`. Two live locals-channel leaks were
found and closed on main this session by removing the BINDING - and the sweep that found
them turned up ONE SITE MORE than the adversary had named. **The forced arms also execute
GENERATED STAND-INS, not shipped code,** so they prove a property of pytest's rewriter rather
than that any shipped arm is remedied.

### A LIVE LEAK FOUND AND CLOSED, AND THE GUARD THAT MISSED IT REPAIRED - recorded 2026-08-25 (session 40)

**A TIER-1 LEAK WAS LIVE ON `main` UNDER DEFAULT FLAGS, AND THIS GUARD DID NOT SEE IT.**
`tests/save/test_world.py::test_a_real_world_model_reprs_without_leaking_it` bound
`strings = [model.token, model.header.map_name]` plus every record's `type_path` and
`instance_name`, then asserted `len(checked) > _TRIPLE`. **Assertion rewriting renders the
ARGUMENT of an inline `len()`**, so the raw world token and map name reached the failure
report with NO FLAG AT ALL - on the pre-push hook and in both CI lanes.

Measured, planted tokens, four rows all forced:

    leaking  len(checked) > _TRIPLE      default 2   -l  6
    remedied checked_count > _TRIPLE     default 0   -l  0

The irony is exact: the test whose stated purpose is proving the world model reprs without
leaking, leaked. `tests/conftest.py`'s redactor does not save it - `_build_redaction_rules`
builds from home-path and account-name spellings ONLY, and no rule exists for a world token,
map name, type path or instance name.

**THE MECHANISM FIRST BLAMED WAS WRONG, AND THE CORRECTION MATTERS.** An adversary inferred
that the guard treats an inline `len(X)` as DISCHARGING X and LABELLED THAT UNVERIFIED; the
merger repeated it as fact. Measured false - `assert len(holder.words) == 0` yields a
finding today and that shape is already pinned. **The real cause was one line:**
`_ScopeScan._bind` used the SHALLOW `self.hit(value)`, which answers only for a bare
`Name`/`Attribute`, so every binding that WRAPPED the field dropped the alias. `checked =
[value for value in strings if value]` is a comprehension, hence invisible. Ten wrapping
shapes measured: **0 flagged before, 10 after** - list/tuple/set/dict literal,
comprehension, f-string, conditional, transparent call, element reducer, two-hop.

The rule is derived from semantics via `_carries_out_of`/`_carries_into`, reading the
already-declared vocabularies. **An over-reach was caught and reverted:** inheriting
`_is_reduction`'s "unresolved implies transparent" default gave 30 live findings, because
that default reports FEWER findings in the repr channel and MORE in the binding channel.
Tightened to follow only calls the vocabulary names: 30 -> 4, all ten shapes still caught.

**THE STATED DECORATOR BOUNDARY WAS FALSE.** `rendered_source_lines` claimed decorator lines
are excluded because "pytest starts its rendering at the `def`". Disproved with a literal
inside `@pytest.mark.skipif(False, reason=...)`, which neither the test id nor the argument
rendering can explain - pytest printed the decorator source line verbatim under default
flags. **357 decorated functions, 791 decorator lines, now inside the sweep, 0 new
findings.**

**`gained > 0` DIED ON A LEAK-FREE REFACTOR.** Margin was exactly 1, from
`WorldModel.token` alone. Inlining `masked_token` into `clockspeed/save/world.py` -
identical body, no privacy change - drove it to 0 and reddened the suite. Now SKIPS with a
reason; the retained assertion still catches a NEGATIVE margin, so it is not vacuous. Weaker
than the original defect and stated as such: a green run certified that a cross-module mask
EXISTS, not that a leak exists.

**A RESIDUAL WAS CORRECTED BY MEASUREMENT AFTER TWO AGENTS DISAGREED.**
`tests/save/test_usmap.py` is FLAGGED ON SHAPE, CLEAN ON CONTENT - it never loads a real
save, every `PropertyMap` comes from `synthetic.build_usmap`, and its only mention of
`load_world` is inside a comment. The shape is a true positive; no save-derived value
reaches that frame.

**WHY IT STAYS OPEN.** The guard's population is still derived from shipped DECLARATIONS -
classes shipping a redacting `__repr__` - rather than from the three kinds of DATA the
acceptance names, so a save-derived name, home path or account directory held by a class
that declared nothing stays invisible to both the assertion sweep and the source-echo
sweep. One live finding remains outside the repairing slice's write-list, recorded rather
than repaired. `REPR_RAISING_HOLDERS` is one bidirectionally-pinned allowance, not the
"0 exemptions" earlier prose implied.

## CS-851

### NOTE - filed 2026-08-25 by the merger, from the CS-829 adversary, MEASURED LIVE ON MAIN

**A THIRD ECHO PATH, AFTER THE ASSERTION CHANNEL AND THE SOURCE-ECHO CHANNEL.** CS-850
closed the first; `_arm_source` recorded the second in passing. This is the third and no
item owned it. pytest's `--showlocals` renders the failing frame's LOCALS, so a
save-derived frozenset or mapping bound to a local reaches the failure report even when
every asserted expression is a scalar - which is exactly the remedy CS-850 asks for.

**MEASURED, NOT REASONED.** Forcing an arm in `tests/save/test_struct_interior.py` against
the real save library: with `--tb=long` and no `-l`, ZERO save-derived words rendered; with
`-l`, SIX of twelve rendered, and none of the six appears anywhere in the module's own
source, so they came from a live repr past the counts-only `__repr__`. Independently
reproduced on a synthetic sandbox: 0 occurrences by default, 1 under `-l`.

**TWO LIVE SITES WERE CLOSED ON MAIN IN SESSION 39** by removing the BINDING - not by `del`,
because the name is live until then. **The sweep that found them turned up ONE SITE MORE
THAN THE ADVERSARY HAD NAMED**, which is the instance-versus-population lesson landing on
the finding itself. This item is the POPULATION.

**WHY CS-850 CANNOT ABSORB IT.** CS-850's guard reasons about sub-expressions of an ASSERTED
EXPRESSION. A local that is never asserted on is invisible to it BY CONSTRUCTION - not by a
bug and not by a one-hop limit. Verified against the shipped guard: the shape
`unexplained = sweep.words; count = len(unexplained); assert count == 0` yields ZERO
findings. CS-850's module now STATES this boundary rather than implying coverage; this item
is the discharge of that statement.

**SEVERITY, STATED HONESTLY RATHER THAN MAXIMALLY.** `addopts` is `-ra --strict-markers
--strict-config`, so `-l` is NOT on by default. The honest severity is "a routine debugging
flag leaks a save-derived word", not "every failure leaks". It is tier 1 because
non-negotiables 11 and 12 forbid the echo regardless of which flag opens it, and because
`tests/conftest.py`'s redactor covers home paths and the account name only - a struct word
passes straight through it.

**THE ACCEPTANCE CARRIES SESSION 39's FENCE, DELIBERATELY.** The check must STAY GREEN on a
tree with no such bindings. Three items were refuted this session for proofs that derived
their cases from the current tree and therefore went RED once the defect was fixed. See
`memory/a-proof-can-require-the-defect.md`. Do NOT derive this item's forced arms from the
findings.

### SHIPPED, REFUTED, REPAIRED - recorded 2026-08-25 (session 40)

**THE GUARD PROVED ITSELF ON DAY ONE AND WAS THEN REFUTED ON THREE COUNTS.** At the merge it
caught a genuinely NEW locals leak a sibling slice had just introduced in
`tests/save/test_struct_interior.py` - neither slice could have found it alone. That is the
item working. Then an adversary broke it:

- **The residual record was defeated by REPLACEMENT.** Keyed on a per-module COUNT, it could
  not distinguish "still the same 8" from "8 completely different ones". Measured: 8 real
  findings repaired and 8 BRAND-NEW leaky bindings planted at new lines under new names ->
  `22 passed, exit 0`. The module's own docstring claimed a new leaky binding in a recorded
  file is still red. It was false.
- **12 false negatives across 21 synthetic binding forms**, 9 outside any disclosed family,
  plus a structural caller-frame gap.
- **Four of its own seven pinning fixtures were false** - pinned SAFE while leaking under a
  real forced run. The zero being asserted was THE SCANNER'S SILENCE, true by construction
  for a form the scanner has no code for.

**THE REPAIR, AND IT FOUND MORE THAN THE REFUTATION DID.**

- **The census was blind to `ast.Try` entirely.** `except-target` went 0 -> **115**
  occurrences; sweeping for the same shape found `ast.TypeAlias` at 0 -> 1. Verified
  independently by the merger: 115 named except-handlers, 1 type-alias, 8 match statements.
  **Every count derived from that census before this repair was an UNDER-count, including
  the adversary's own false-negative analysis.** The `statement_forms` docstring claimed to
  be "EXHAUSTIVE OVER STATEMENT KINDS"; it now lists what it covers and discloses what it
  does not.
- **The record is re-keyed by `(module, scope, local)`** - stable identity, never a line
  number. A finding whose key is absent is RED, catching replacement; a key with no finding
  is reported STALE with the exact entry to delete. **It worked across slices on its first
  run**, naming three residuals that a different slice had repaired without knowing this
  record existed. The staleness direction is a WARNING, not an assertion, deliberately:
  asserting it would require the live population to still hold every recorded site, which is
  the anti-monotone shape the fence forbids.
- **It was FIVE false fixtures, not four.** Swapping `class Sink: pass` - whose repr is
  `<Sink object at 0x...>` - for a plain dataclass made `attribute-target` leak too. Each of
  the five is now an ADMITTED GAP opening with "LEAKS, NOT COVERED", not an exemption.
  `subscript-target`'s reason was PRECISELY BACKWARDS - a plain dict's repr IS the leak. The
  `except-target` hand-off to `tests/test_exception_rendering.py` was DELETED: that file has
  zero occurrences of `showlocals`/`f_locals` and is scoped to CS-205.
- `global` is fixed - it was a false positive whose own recorded reason said it should not
  fire. `nonlocal` was CHECKED and correctly left alone: suppressing it would have traded a
  false positive for a false negative.

**A TREE-CLAIM SWEEP FOUND 24 CHECKABLE CLAIMS, 11 MEASURABLY FALSE OR MISLEADING.** The
worst was the file stating `match-capture` was recorded "PRECISELY BECAUSE THIS TREE
CONTAINS NONE" while containing three of them itself. Presence is now a measured
`Recorded.in_tree` field and a declared-absent form that ARRIVES is reported. Four counts
the repair had itself written into prose were removed - restating a measured number is the
same defect it was sent to fix.

**WHY IT STAYS OPEN.** Five recorded forms remain measured-leaking and uncovered;
`except-target` leaks under DEFAULT flags and no module grades a handler name on this
channel; and the caller-frame gap is structural - `-l` renders locals for EVERY frame in the
traceback, while the scan emits only where an `Assert` sits in the same scope. 10
live-flagged scopes over 9 modules have no assert in scope, one of them
`clockspeed/save/world.py`.

## CS-852

### NOTE - filed 2026-08-25 (session 40) by the merger, from a CS-851 adversary, MEASURED ON MAIN

**A SHIPPED CLASS, NOT A TEST.** `clockspeed/save/chunks.py:474` declares
`DecompressedBody` as `@dataclass(frozen=True)`. Merger measured directly:
`grep -c "def __repr__" clockspeed/save/chunks.py` is **0**. Its default dataclass repr
renders `payload=b'...'` - the concatenated decompressed body of a real save, which carries
type paths and instance names. pytest's `saferepr` caps at roughly 240 characters, so the
leak is bounded but real.

**IT IS INVISIBLE TO EVERY GUARD THIS PROJECT SHIPS.** CS-850's sweep derives its population
from classes that ship a redacting `__repr__` - a class shipping NONE cannot enter that
population BY CONSTRUCTION. It is named in no doc. Every `body = ` local in the save test
sweep helpers renders it.

**DO NOT CLOSE THIS BY ADDING A `__repr__` TO ONE CLASS.** That is the instance-not-
population error this project keeps paying for. Derive the set from the shipped FIELD
ANNOTATIONS - any class whose fields can hold `bytes` off a save, or a save-derived name -
and grade every member.

**THE DERIVATION IS THE HARD PART AND IT IS WHY THIS IS NOT A CS-850 WIDENING.** CS-850
reasons about withholding declarations; this item's population is defined by what a field
CAN HOLD, which is a different question with a different failure mode. See
`memory/an-empty-population-satisfies-every-zero.md`: a guard whose population is derived
from declarations returns zero for classes that declared nothing, and zero is what a broken
derivation also returns.

### NOTE - filed 2026-08-25 (session 42) by the merger, AFTER FOUR ADVERSARIES, ALL FOUR REFUTED

**THE GUARD SHIPPED, FOUR LIVE LEAKS ARE CLOSED, AND THE ITEM STAYS OPEN.**
`tests/repr_rendering_guard.py` derives the population from shipped FIELD ANNOTATIONS by
two mechanical rules - R1 every generated-repr class under `clockspeed/save/` with a field
that is not provably non-disclosing, R2 every generated-repr class anywhere under
`clockspeed/` carrying a `bytes`/`Path` word. `tests/test_repr_rendering.py` grades it in
42 arms. Measured at merge: population 43, findings 0, exemptions 11, stale 0.

**THE DERIVATION FOUND MORE THAN THE NOTE ABOVE NAMED, WHICH IS THE POINT OF DERIVING IT.**
The note named `DecompressedBody`. The sweep also found `SaveListing.saves` - a tuple of
`.sav` paths, so the account id and the home directory - and `ForbiddenRoot.resolved`, an
absolute install path in a class whose own attribute docstring says `label` exists so a
refusal need not render a path. All three were confirmed leaking with a planted marker
before repair and silent after. All three now carry `repr=False` plus a withholding
`__repr__`.

**REPAIRING THEM EXPOSED A FOURTH LEAK THAT CS-851 WAS BLIND TO BY CONSTRUCTION.** Giving
`DecompressedBody` a `__repr__` moved it into CS-850's population - which is derived from
classes SHIPPING one - and CS-851 immediately flagged `tests/save/test_properties.py`
holding the raw decompressed body in a local at an assert. A class that declares nothing
is invisible to the guards, not just to readers.

**THE DISCRIMINATOR IS "GENERATED", NOT "ABSENT", AND IT WAS MEASURED.** A plain class with
no `__repr__` inherits `object.__repr__` and renders no field - both `_Cursor` types hold a
raw save buffer and leak nothing. A `@dataclass` with no `__repr__` renders every field.
Grading on "ships no `__repr__`" reports both cursors and buries the real findings.

**WHY IT STAYS OPEN. FOUR GAPS, EVERY ONE MEASURED BY AN ADVERSARY, NONE WITHDRAWN.**

1. **THE EXCEPTION CHANNEL IS RECORDED, NOT GRADED.** `BaseException.__repr__` is NOT
   `object.__repr__` - it renders `args`, and `__str__` renders it too. So the
   `KIND_INHERITED` grade is sound for a plain class and UNSOUND for every error class.
   An adversary added a save-derived `instance_name` to a shipped error, interpolated it
   into the message, and every arm stayed green. 24 save-layer error classes are pinned in
   `UNGRADED_EXCEPTION_CHANNEL` so the gap cannot grow silently, but they are NOT graded.
   Closing this needs the message-building CODE PATH, not field annotations - a different
   analysis from the one this item built. **That is the next round's work.**
2. **TWO CLASSES ARE OUTSIDE THE POPULATION AND SHOULD NOT BE.**
   `clockspeed/data/locate.py::LocalConfigWarning` takes a `pathlib.Path` at five of six
   `_note` sites into a field annotated `str`; it escapes R1 (not under `save/`) and R2
   (annotation is not a carrier). Its only protection is `redact()`, which this guard never
   reads. And `clockspeed/save/objects.py::Transform` renders exact save-derived world
   coordinates through a generated repr, invisible because `tuple[float, ...]` is scalar -
   yet `ObjectRecord.__repr__` deliberately withholds that very value as `transform=present`.
   **The derivation keys on the ANNOTATION and the leak is in the VALUE.**
3. **`UnknownClass` IS AN ACCEPTED DISCLOSURE, NOT A PROVEN-SAFE ONE.** `type_path` is
   `cursor.string(...)` read straight from the save body with nothing validating it is a
   class path; a planted marker rendered verbatim. BOOTSTRAP.md section 9 REQUIRES naming
   unmodelled content, so the disclosure is the type's purpose - but the same module 240
   lines away discards a level name for exactly this reason. The tension is recorded in the
   exemption rather than argued away.
4. **HYPOTHETICALS, MECHANICALLY VERIFIED, NO LIVE INSTANCE TODAY.** A dataclass SUBCLASS
   inheriting a carrier is missed - `declared_fields` reads only the class's own body, and
   `repr=False` does not inherit. So are an aliased decorator import (`dataclass as dc`),
   `TypedDict`, `Enum` member values, `attrs`, and `os.PathLike`/`BinaryIO`/`mmap`/PEP-695
   aliases. Also `opaque_class_names` matches BY BARE NAME across the whole tree including
   tests, and "opaque" means SHIPS a `__repr__`, not REDACTS one.

**DO NOT RE-PITCH FOLDING THIS INTO CS-850.** The note above already fenced it and four
adversaries confirmed the seam: a GENERATED repr made no per-field decision and is this
item's; a HAND-WRITTEN one did and is CS-850's. This module re-grades a hand-written repr
ONLY for carrier fields. Widening that re-grade to plain `str` reported six correctly
redacting classes, `ResourceNode` among them, whose repr shows the game `class_name` on
purpose.

**TRAPS THIS ROUND PAID FOR, ALL FOUR FOUND BY AN ADVERSARY AND NOT BY REVIEW.**
- **A HOISTED ASSERT CAN LEAK MORE THAN THE ONE IT REPLACED.** The merger moved a
  loop-invariant assert out of a per-save loop to escape a CS-851 finding. The original sat
  under `except (Exception, SystemExit)`, which CATCHES `AssertionError` - so it could never
  render anything and the CS-851 finding was a STATIC FALSE POSITIVE. The hoisted copy
  propagated through a frame holding the real library save paths. One marker occurrence
  hoisted, zero inside the try. It now lives in
  `test_the_two_width_classes_are_disjoint`, a frame that holds two dicts of width names
  and nothing else. **Check what a frame HOLDS before moving an assert into it.**
- **A REPR THAT RAISES IS WORSE THAN ONE THAT DISCLOSES.** Two drafts raised - first
  `is_complete` reading `problem.code` off every element, then `len()` on `payload=None`,
  where the GENERATED repr it replaced had been total. Lengths now go through a
  `Sized` check.
- **`assert MARKER not in rendered` PASSES WHEN THE MARKER WAS NEVER PLANTED.** The forced
  arms had no positive control; emptying one payload left the suite green while a genuinely
  leaking repr rendered a real type path. `test_a_forced_subject_actually_carries_the_marker`
  is the control. This is `memory/an-empty-population-satisfies-every-zero.md` AGAIN, in a
  module whose own docstring cites it.
- **A LENGTH CHECK ON A PROSE REASON ENFORCES NOTHING.** All 11 exemption reasons replaced
  with 40 literal characters passed every arm, which is how a reason shipped citing a
  private helper THAT HAS NEVER EXISTED in this repository, transcribed from a sibling
  module. `test_every_identifier_an_exemption_cites_exists_in_the_module_it_names` now
  checks every underscore-carrying token against the module the key names - and it caught a
  SECOND fabricated name on its first run, one the merger had copied from an adversary's
  report without verifying.

**WHAT A NEXT ROUND SHOULD NOT REDO.** The three repairs and the `test_properties`
relocation are merged and mutation-proven; 8 of 8 targeted mutants killed, including a true
revert of each repair. The population, the exemption record and the exception record are all
asserted in BOTH directions. Start at gap 1.

### NOTE - filed 2026-08-28 (session 43) by the merger, AFTER TWO ADVERSARIES, BOTH REFUTED, AND TWO REPAIR ROUNDS

**GAP 1 IS NOW GRADED RATHER THAN RECORDED, AND THE ITEM STAYS OPEN.**
`tests/exception_message_guard.py` grades the MESSAGE-BUILDING code path - what reaches
`BaseException.args` - in 68 arms. The 24 classes the prior round could only pin in
`UNGRADED_EXCEPTION_CHANNEL` are discharged FOR THAT CHANNEL. Measured at merge: 28
modules swept, 24 classes, 104 channels, 11 exemptions, 0 findings, 0 stale, 0 ambiguous.
An independent census confirmed 47 runtime `BaseException` subclasses = 24 graded + 23
above the layer, nothing unaccounted.

**THE RULES ARE DERIVED, NOT LISTED.** E1 resolves the governing initialiser THROUGH THE
BASES, so the nine classes governed by an inherited one - four `ChunkError` subclasses and
five `ObjectError` subclasses - are graded by the base rather than scored as ungraded.
(The merger's brief said five and five; the slice MEASURED four and five and corrected it.
Carried as a non-emptiness assertion, never as a count.) E2 splits an args-reaching
expression into channels. E3 offers four proof forms; anything else is a finding unless
`EXEMPT` records a measured reason.

**THE HEADLINE REFUTATION: NINE PATHS ISSUED POSITIVE FALSE PROOFS.** This is worse in
kind than reporting silence - a `proven-*` verdict is a CLEARANCE a later session will
cite. An adversary made a real save-body-derived value reach `args` in a real shipped
class - `instance_name` from `cursor.string` at `clockspeed/save/objects.py:1747`,
interpolated into `ObjectFormatError` - while all 51 arms passed and the report was
BYTE-IDENTICAL to pristine. The nine:
  - a BoolOp fallback `f"{name or 'unnamed'}"` graded `proven-scalar`. **THIS IS LIVE
    HOUSE STYLE** at `exhaustive.py:173`, `greedy.py:313`, `ratio.py:774` and `:846`;
    fed the unedited `ratio.py`, the guard graded `', '.join(...) or '...'` as an
    annotation whose whole value space is numbers and flags.
  - `.format(n=name)`, `self.args = (m,)` and an unbound `Exception.__init__` each found
    NO CHANNEL AT ALL, which the module then reported as clean. None is live today.
  - `proven-vocabulary` had NO DOMINANCE ANALYSIS - `ast.walk` found a guard clause
    anywhere in the function, including nested under an unrelated condition.
  - `proven-vocabulary` resolved a callee BY BARE NAME, so a function merely NAMED
    `_checked_field` whose body only decoded earned the proof. **THE SAME SHAPE THAT
    REFUTED CS-855 IN THE SAME SESSION.**
  - `proven-at-sites` returned its proof over ZERO bindings - the twin of the slice's own
    M6, in a defect class its own arm already named in writing.
  - a same-named class in a later module evicted the save class from the population.
All nine are closed and mutation-proven, 19 of 19 killed.

**WHAT THE ZERO MEANS NOW, AND IT IS STATED AT THE ASSERTION.** Every channel the
composition ENUMERATES is proven or exempt. It does NOT mean nothing discloses. A route
that produces no channel is INVISIBLE, not clean, and the module says so rather than
claiming unmodelled shapes surface as findings - the sentence that claimed that was
measured false five ways and is gone.

**THE SHIPPED REPAIR, BY OPERATOR RULING.** `chunks.py` and `usmap.py` DOCUMENTED a
closed-vocabulary guarantee they did not ENFORCE: `chunks.py:280` says the field is
"never a value read from the file", and `ChunkError(field=MARKER)` constructed and
rendered the marker while `ObjectError` refused. Both now ship `_checked_field`, derived
from their own sites - chunks 20 sites, 10 literals, 0 non-literal; usmap 8 sites, 7
literals plus a `_take` pass-through resolving to 33 names at hop two. Each test module
re-derives its OWN set and asserts equality both ways. The two sets share only `magic`
and `compressed_size`, so `FORCED_VOCABULARY` carries a legitimate value per entry:
`"header_version"` is legitimate to header and REFUSED by both new gates, and a
module-keyed lookup would have passed the negative half for the wrong reason. Six channels
upgraded `proven-at-sites` to `proven-vocabulary`; five parametrised arms reddened and
were repointed. The 2-2 split across the four parsers is closed.

**A DOC REPAIR THAT THE OBVIOUS FIX WOULD HAVE GOT WRONG.** `clockspeed/save/world.py`'s
safety paragraph - the stated justification for every `raise ... from exc` in the world
loader - claimed all four parsers "each pin it with a planted-marker test". False when
written. The slice checked before writing and found **header.py and objects.py have no
vocabulary-refusal test either**, so adding one to chunks would have left the sentence
false in a NEW way. It now states per module what is actually pinned and names usmap the
weakest. Docstring-only, proven by comparing the parsed module with its docstring stripped.
**The merger's evidence for this was a `grep "planted"` - a WORD search, not a PROPERTY
search - and `tests/save/test_chunks.py` already pinned three other clauses of the
guarantee. The conclusion held; the evidence was weaker than it read.**

**RESIDUALS - RECORDED, NOT RESOLVED.**
1. Class and callee resolution is still BY BARE NAME and cannot be otherwise without
   resolving imports. Censused: `colliding_class_names` reports `('_Cursor',
   '_WarningLog')`; `ambiguous_error_names` is empty and asserted. The wide census is
   deliberately NOT asserted empty - it would redden on a correct tree.
2. A route reaching `args` that the composition never enumerates is invisible. No proof
   exists that no such route does.
3. `ARGS_ROOTS` is an 11-word list TRANSCRIBED byte-for-byte from
   `tests/repr_rendering_guard.py`'s `EXCEPTION_ROOTS`, so
   `test_the_population_agrees_with_the_repr_channel_census` is ONE derivation run twice
   on the dimension that matters. A `class Foo(Warning)` under `save/` is invisible to
   both censuses AND to the departure half. Zero live instances - 47 of 47 covered. The
   cheap repair an adversary ran and verified: import each module and assert the runtime
   `BaseException` subclasses equal graded + ungraded.
4. Call sites outside `clockspeed/` are unswept. `add_note`/`__notes__`, `args` mutated
   after construction and a `__str__` override are silent rather than unproven - all zero
   occurrences today, and `__str__` is fenced by the repr guard.
5. `header.py` and `objects.py` still lack a direct vocabulary-refusal arm.
6. **THE CHAINED CAUSE IS NOW CS-857.** `raise X(...) from exc` sets `__cause__`, not
   `args`, so this guard correctly declines it - and NOTHING ELSE GRADES IT. 7 of the 11
   exemption keys sit on a chained raise and two of their reasons state a privacy
   conclusion the site does not deliver. Filed as its own item; do not fold it back here.

**GAPS 2, 3 AND 4 OF THE PRIOR ROUND ARE UNTOUCHED AND UNCLAIMED.** `LocalConfigWarning`
is confirmed NOT among the 23 above the layer - it is a frozen dataclass, not an
exception, so it never reaches `args` and remains a gap-2 repr-channel residual. Neither
new module mentions it, `Transform` or `UnknownClass`.

## CS-853

### NOTE - filed 2026-08-25 (session 40) by the merger, from the CS-850 repairing slice

**A FOURTH ECHO PATH.** After the assertion channel (CS-850), the locals channel (CS-851)
and the source-line channel (closed inside CS-850 this session), pytest renders a
FIXTURE'S VALUE in the failure header of every test that names it.

**MEASURED IN PASSING, NOT SOUGHT.** The slice repairing CS-850 observed that its sandbox
fixtures return captured pytest output whose header line carries a `tmp_path` rootdir under
the operator's profile. It mitigated that at source by redacting the captured text inside
its own helper before returning it, and its control confirms all ten planted tokens survive
that redaction - so the mitigation is bounded and local, not general.

**THE GENERAL CASE IS UNOWNED.** `tests/assertion_rendering_guard.py` declares the
frame-argument channel out of its scope at its own line ~134. An adversary incidentally
proved the channel live: a crashing arm rendered a planted dict into the report even though
the token was bound at MODULE scope, which the source channel's "module-scope binding
renders zero times" result does not cover.

**THE FENCE.** Derive the forced cases from shipped fixture RETURN ANNOTATIONS or from
synthetic fixtures - never from live findings - and the check must stay green on a tree with
no such fixture. Three items were refuted in session 39 for proofs that required the defect;
see `memory/a-proof-can-require-the-defect.md`.

## CS-855

### NOTE - filed 2026-08-25 (session 40) by the merger, from the CS-851 repairing slice

**THE ONLY BINDING FORM MEASURED TO LEAK UNDER DEFAULT FLAGS.** Of the five forms the
CS-851 guard now records as leaking-but-uncovered, `except-target` is the one that renders
WITHOUT `-l`, through the exception's own rendering rather than through the locals block.
Every other recorded form needs the flag.

**NOTHING GRADES IT.** The CS-851 guard's hand-off to `tests/test_exception_rendering.py`
was DELETED this session after measurement: that file holds **zero** occurrences of
`showlocals`, `f_locals` or `show_locals`, and its own docstring scopes it to CS-205, "no
tracked module renders a caught exception OBJECT into a message" - a different channel. The
hand-off pointed at a file that does not grade this.

**THE POPULATION IS LARGER THAN ANYONE THOUGHT.** The CS-851 census could not see `ast.Try`
at all until session 40; `except-target` went from 0 to **115** named handlers. Merger
verified independently: 115. Any earlier reasoning about this form rested on an empty
population - see `memory/an-empty-population-satisfies-every-zero.md`.

**ONE MEASURED SUBTLETY, DO NOT LOSE IT.** Python deletes the handler's name at the end of
the handler, so an assert AFTER the handler renders nothing - measured. The exposure is an
assert INSIDE the handler body, which is exactly where a test that grades an error path puts
it. A fixture that puts the assert outside the handler will validate a shape that does not
occur.

### NOTE - filed 2026-08-28 (session 43) by the merger, AFTER TWO ADVERSARIES, BOTH REFUTED, AND A REPAIR ROUND

**THE GUARD SHIPPED AND THE ITEM STAYS OPEN.**
`tests/test_handler_exception_rendering.py` grades the channel in 27 arms. The first
build was refuted by two adversaries on distinct lenses and repaired; what follows is
what is MEASURED, and every count was taken this session.

**THE HEADLINE: THE BINDING FORM IS NOT WHAT LEAKS, AND THIS ITEM'S OWN TITLE WAS
WRONG.** Deleting the `as NAME` from the shipped CS-851 fixture leaves an UNNAMED
handler that renders the marker just as readily. What renders is CHAINING, which fires
with a bare `except ValueError:`. So `tests/locals_rendering_guard.py`'s EXCEPT_TARGET
row was true of the FIXTURE and false of the FORM; its reason is corrected this session,
its FLAGS are not, because `renders_by_default=True` is right for the wrong reason.

**THREE MECHANISMS, MEASURED SEPARATELY, ALL UNDER DEFAULT FLAGS AND NONE NEEDING -l.**
`__context__` / `__cause__` chaining, which is NOT name-keyed. The rewritten assert,
which is. And a THIRD that no item had recorded: the callee FRAME ARGUMENT - an
exception handed to a helper renders as `problem = Boom('<marker>')` in that helper's
frame header, CHAIN-SUPPRESSION-PROOF, surviving `raise ... from None`. The merger
reproduced the frame-argument render independently before accepting it.

**THE FRAME ARGUMENT IS THE CONSTRUCT `tests/test_exception_rendering.py:75` CALLS "the
FIX".** That line names `helper(NAME)` as the remedy for CS-205. Live instances:
`clockspeed/save/workdir.py:688`, `tools/drift_guard.py:463`, `scripts/verify_env.py:370`
- the last with a comment saying it drops the discovered path, which is true of the
MESSAGE and false of the FRAME. **BUT THIS IS NOT A LIVE LEAK AND THE REASON MATTERS:**
`repr()` of an OSError OMITS `filename`; only `str()` carries it. Measured on the exact
shape - zero path bytes in the frame-argument line. The remaining candidate was the four
`ImportError` sites, whose repr CAN hold a path; the merger measured `locate.redact`
scrubbing that shape too.

**THE POPULATION IS 117, NOT 115, AND 115 WAS NOT A CATEGORY ERROR.** An adversary
parsed git objects at `f19d1f2`, the commit that closed the `ast.Try` census hole: named
was exactly 115 there, escape-capable-named 113. So 115 was CORRECT WHEN FILED and has
drifted by two. The slice's first report claimed 115 had always meant the escape-capable
subset; that claim is REFUTED and withdrawn. Today's coincidence that escape-capable-named
is also 115 is a coincidence. The disposition is "derive it", which is now what the
acceptance demands.

**ZERO NAMED HANDLERS HOLD AN ASSERT IN THE BODY** - measured lexically and by full
`ast.walk`, both zero. So a guard keyed on the shape this item's note originally named
grades an EMPTY POPULATION. That zero is now stated as a syntactic result over the
shipped AST, beside a detector proven able to find a planted one.

**WHY IT STAYS OPEN. THREE RESIDUALS, NONE WITHDRAWN.**
1. **THE SANDBOX DOES NOT RUN THE CONFIGURED PIPELINE.** `_sandbox` passes
   `--rootdir <tempdir>` and `cwd=<tempdir>`, so neither `pyproject.toml` nor
   `tests/conftest.py` loads - sandbox headers carry no `configfile:` line. The real
   pipeline sits behind `tests/conftest.py:665`, the CS-428 report redactor. So every
   `renders=True` here proves AN ARBITRARY STRING REACHES THE REPORT, **not that
   personal data does**, and only the second is what this item is about. Not repaired:
   the fixtures would have to sit inside the repo, where `tracked_python_files`
   enumerates untracked files, so the sandbox would perturb the census it derives.
2. **THE EVASION LIST HAS NO COMPLETENESS ARGUMENT.** Five constructs defeated the first
   detector - an intra-handler alias, a `Starred` argument, a shadowed builtin, an alias
   handed to a call, and an alias read in an assert. All five are now caught. Nothing
   proves the list closed, and an unthought-of construct renders while the zero looks
   identical.
3. **`_hands_over` counts an Attribute callee regardless of builtin status.** It
   over-reports, which is the safe direction, and all 42 callees are Python today.

**THE INDEPENDENCE VERDICT IS NARROWER THAN THE FIRST REPORT CLAIMED.** FRAME_ARGUMENT
renders `repr(exc)`, which for a standard exception shows `args` - the same producer
content the chained `E` line prints via `str()`. So this channel cannot carry what the
producer did not put in args. The channels ARE separable, but the separating construct
is a rewritten assert reading a NON-ARGS attribute, and that has ZERO LIVE INSTANCES.
The first report's Q1 arm did not prove otherwise: it raised `Boom(MARK)`, so the marker
WAS args, and its `'"inert"' in source` guard was a substring search satisfied by a
different string in the fixture.

**"THE ACCEPTANCE IS UNSATISFIABLE" IS WITHDRAWN.** It was report-only and never reached
a tracked file. Four constructs render ZERO markers with the assert inside the handler,
one of them using the `pytest_runtest_makereport` lever THIS PROJECT ALREADY SHIPS. The
correct verdict is "unsatisfied by the remedies considered". The merger had repeated the
stronger claim and was one step from restating a tier-1 acceptance on it.

**TRAPS THIS ROUND PAID FOR.**
- **A DECLARED-QUIET ARM RENDERED.** `assert len(exc.secret) == 0` renders via
  `E + where 15 = len('<marker>')`; binding the reduction first renders nothing. The
  slice shipped the finding rather than weakening the arm.
- **TWO REPAIRS SHIPPED WITH NO CONTROL PROVING THEM** - the `Starred` unwrap and the
  shadowed-builtin subtraction both survived mutation until planted controls were added.
  A repair is not evidence of itself.
- **WALKING THE WHOLE ARGUMENT SUBTREE IS WRONG.** It took the hand-off count 42 to 92 by
  absorbing `helper(str(exc))`, which is a STRING and CS-205's channel, not this one.

## CS-854

### NOTE - filed 2026-08-25 (session 40) by the merger, from the CS-829 repairing slice

**THREE UNSWEPT SIBLINGS OF A DEFECT REPAIRED ELSEWHERE.** The shape: selecting a tag by the
tag reader's REPORTED TYPE WORD after a walk, into a population an arm then asserts a zero
or an equality over. When the reader is wrong the population shrinks and the assertion gets
EASIER - the anti-monotone signature CS-829 has now been refuted for four times.

The CS-829 slice repaired `_fold_one_tag`, `_sample_one_record` and
`_uniform_width_struct_words` inside its own file, and reported these three as outside its
write-list:

    tests/save/test_container_elements.py:839
    tests/save/test_inventory_potential.py:316
    tests/save/test_reference_resolution.py:968

**TWO NEAR-MISSES ARE EXPLICITLY NOT SIBLINGS** and must not be "fixed":
`tests/save/test_container_elements.py:1168` is a validation assertion, and
`tests/save/test_value_anchoring.py:1082` is a deliberate privacy intersection.

**DERIVE, DO NOT WORK THE LIST.** Three line numbers in a note are the hand-maintained thing
this repo records as the thing that rots, and the CS-829 slice found one site the brief had
not named by sweeping rather than by working its list. Sweep for the SHAPE.

## CS-857

### NOTE - filed 2026-08-28 (session 43) by the merger, from a CS-852 adversary, MEASURED ON MAIN

**A CHANNEL NOTHING IN THE TREE GRADES, FOUND WHILE GRADING A DIFFERENT ONE.**
`raise X(...) from exc` makes the CAUSE's own text part of the formatted traceback. The
graded message can be perfectly redacted while the chained `OSError` renders the raw path
beside it, on the same failure.

**MEASURED, ON A REAL SHIPPED PATH, SYNTHETIC MARKER ONLY.** `usmap.load_usmap` against a
path that is a directory raises `PermissionError`, re-raised at the one chained site in
`clockspeed/save/usmap.py::load_usmap`. Default `traceback.format_exc()`, no flags: the graded
channel rendered `<localappdata>/...` REDACTED, and the cause rendered the raw path
including the Windows account name. `locate.redact` did its job and the traceback went
around it.

**THE SEVERITY FRAMING THAT STOOD HERE IS MEASURED FALSE.** Session 45 forced it; the
account id and world name render in full. Archived in `docs/history_notes.md`. See CS-860.

**NOBODY OWNS IT AND BOTH CANDIDATES SAY SO IN WRITING.**
`tests/test_redaction_scope.py:26-41` declares the chained cause out of scope and NAMED
`clockspeed/save/world.py` line 971 as the site - a pointer that had ITSELF drifted, that
statement having moved to `clockspeed/save/world.py:989`. It was REPOINTED in session 44
to `clockspeed/save/world.py:1109` rather than renumbered, because the claim it carries -
filename included - is FALSE at the STAGE_HEADER site: `parse_header` takes bytes, so the
`HeaderError` it raises has no filename to carry. STAGE_COPY and STAGE_USMAP are the two
of the five whose cause reaches an `OSError` that does. The CS-852 message guard declares
the channel out of scope because `from exc` sets `__cause__` rather than `args`. Both
guards say "not me"; CS-857 now says "me" and nothing yet grades it. Every `__cause__` assertion in the
suite grades the cause's TYPE or its nullity - SIX in `tests/save/test_world.py`, all
`isinstance`, and one asserting `None` at `tests/save/test_header.py:1048`. The first
filing said five; six was measured in session 44. None grades content.

**IT LANDS ON THE CS-852 EXEMPTION RECORD, NOT MERELY NEAR IT. 7 OF 11 EXEMPT KEYS SIT ON
A CHAINED RAISE** - measured by walking each key's construction site and testing
`ast.Raise.cause`: `clockspeed/save/usmap.py::UsmapError`, and
`clockspeed/save/workdir.py`'s `SourceUnreadableError` and `WorkDirError` at four sites.
The 11th, `clockspeed/save/header.py::HeaderReadError`, is `from None` at
`clockspeed/save/header.py:927` and is the one site that closes the channel. The other
three that do not chain are the three `DestinationRefusedError` keys.

**THE TWO FALSE EXEMPTION REASONS WERE CORRECTED IN SESSION 44**, re-verified in 45, and
archived in `docs/history_notes.md`. The one acceptance conjunct fully satisfied.

**THE LIVE SITES ARE OWNED BY `tests/chained_cause_guard.py`, NOT BY THIS PARAGRAPH.** It
derives them every run and reports a verdict per site. What is stable enough to write down
here is WHICH MODULES carry them and which are the exposure: `clockspeed/data/blobs.py`,
`clockspeed/data/docs_extract.py` (two) and `clockspeed/data/version.py` chain causes that
carry no path - a `ValueError` from `int()`, a `UnicodeDecodeError`, and a `json` decode
failure rendered as msg, lineno and colno. `clockspeed/save/world.py` chains project
exceptions and its own wrapper messages are structurally path-free.

**A CONVENTION HAS TO BE STATED OR IT DRIFTS BY TWO.** Half the raises span several lines,
so a grep for `) from exc` and an AST walk disagree by two or three on each of them. The
census uses `ast.Raise.lineno` - the STATEMENT line - and says so in its own docstring.
Any later reader comparing its output against a hand-written pointer must check which
convention that pointer used before calling it stale.

**THE FIRST FILING MISSED `clockspeed/data/blobs.py` AND `clockspeed/data/version.py`
ENTIRELY, AND THAT UNDERCOUNT IS ITSELF THE ARGUMENT FOR THE ACCEPTANCE'S `DERIVED`
CLAUSE** - a hand-listed population was short by two the day it was written. Both look
benign on inspection: `blobs.py` chains a `ValueError` from `int()`, and `version.py`
chains a `json.loads` failure rendered as msg, lineno and colno. Neither is confirmed.
Both are UNVERIFIED pending the derived sweep.

The two in `clockspeed/data/docs_extract.py` chain benign causes - `UnicodeDecodeError`
and `json.JSONDecodeError`, codec and offset only, no path, verified by reading both
message constructions. **The OSError-rooted ones in `clockspeed/save/usmap.py` and
`clockspeed/save/workdir.py`, re-wrapped by `clockspeed/save/world.py`, are the
exposure.**

**DO NOT FOLD THIS INTO CS-852 OR CS-855.** CS-852 gap 1 grades what reaches `args`; this
is what reaches the traceback WITHOUT reaching `args`, which is why that guard correctly
declines it. CS-855 grades three mechanisms by which a CAUGHT exception reaches a report;
this is the mechanism by which a RE-RAISED one does, and its severity profile is
different because it survives outside pytest where CS-428 does not run.

### WHAT SESSION 44 SHIPPED, AND THE FOUR RESIDUALS THAT KEEP IT OPEN

**SESSION 44'S MERGE RECORD IS ARCHIVED** in `docs/history_notes.md`.

**RESIDUAL 1 - CLOSED IN SESSION 45, IN TWO ROUNDS.** Archived in
`docs/history_notes.md`. The clearance must never again rest on a SPELLING.

**RESIDUAL 2 - THE LARGEST SILENCE: A RAISE IN A CALLEE OF A HANDLER.** CPython sets
`__context__` from the THREAD's exception state, not from lexical scope, so a helper called
from a handler body chains and renders identically to a graded `from exc` - and is not in
the population at all. Measured: 53 `except` handlers under `clockspeed/`, 27 whose body
contains a call, 10 of those OSError-typed. The guard's docstring claims escape requires
leaving every handler AND dropping the `from`; that is measured FALSE. It also refutes the
stated rationale for `NESTED_SCOPES`, which holds only when a nested def is RETURNED and
not when it is CALLED.

**RESIDUAL 3 - THE MEASURED HALF IS CLOSED IN SESSION 45.** Archived in
`docs/history_notes.md`. The genuine repair stays `unproven` ON PURPOSE.

**RESIDUAL 4 - AN ALIASED IMPORT UNDER-REPORTS AND IS NOT IN THE STATED LIMITS.** `from
builtins import OSError as Boom` grades `unproven`. The limits name module-level SHADOWING
and dotted handler types; they do not name ALIASING. Under-report, so a silence rather than
a clearance, but unstated.

**THAT UNMEASURED CLAIM WAS FORCED IN SESSION 45 AND IT DID NOT HOLD.** See the session-45
note below and CS-860. The sentence this paragraph used to end with - that the severity
framing was an inference rather than a measurement - was correct, and the measurement went
the other way.

### NOTE - session 45, 2026-08-29, AFTER FOUR ADVERSARIES - TWO ROUNDS, THE FIRST REFUTED

**ROUND 1 REPAIRED RESIDUAL 1 AND WAS ITSELF A FALSE CLEARANCE.** It gated the clearance on
`raised == handler_name` - A COMPARISON OF SPELLINGS. Adversary L2 measured 15 shapes that
name the handler's own exception by another spelling, reach `closed-suppressed`, and render
the filename: `kept = exc`, a walrus, a subscript, an attribute, a module-level name, an
outer handler's binding, `_identity(exc)`. The merger reproduced the headline before acting
on it. **THE FIRST REPAIR OF A SPELLING-MEASURING GUARD MEASURED A DIFFERENT SPELLING**, which
is `memory/a-guard-can-measure-spelling.md` reproduced one level down, in the fourth
consecutive session to produce a false clearance inside the guard built to prevent the last.

**ROUND 1 ALSO INVERTED THE MODULE'S OWN DOCTRINE.** `TYPE_UNRESOLVED` says in writing that
every unresolved site is graded `UNPROVEN`. Round 1 collapsed almost every suppressed site
to `TYPE_UNRESOLVED` and then cleared it, so 15 sites were unresolved AND cleared. And the
narrowed arm ASSERTED the escape must be cleared, which would have made a correct future
repair red first.

**ROUND 2 - THE CLEARANCE RESTS ON A POSITIVE, PROVABLE FACT.** `CLOSED_SUPPRESSED` is now
reachable only when the raise CONSTRUCTS a class the module itself declares
(`Site.raises_local_class`). Everything else suppressed is `UNPROVEN`. Measured: all of L2's
escape shapes fall out of the clearance, the genuine wrapper sites stay cleared, and NO LIVE
GRADED VERDICT CHANGES - all four raise a locally declared class. **DO NOT REPAIR A FUTURE
ESCAPE BY ADDING SPELLINGS**; that is what produced round 1.

**THE SEVERITY FRAMING OF THIS ITEM IS REFUTED, AND THAT IS THE SESSION'S BIGGEST RESULT.**
Adversary L3 FORCED the measurement three agents had only read. Under the project's own
pytest configuration - `configfile: pyproject.toml` in the header, so not the CS-855
unconfigured-pipeline trap - a chained cause reaches the FAILURES block and the PLATFORM
ACCOUNT ID AND THE WORLD NAME RENDER IN FULL. `tests/conftest.py` emits two rule families,
home-path spellings and account-name spellings, and neither covers them. Worse,
`OSError.__str__` renders `filename` through `%r`, which DOUBLES BACKSLASHES, and the
home-path rule holds only the single-separator and `as_posix` spellings - so on a chained
cause the primary rule CANNOT FIRE. It is contained on this machine only because the account
name happens to be the sole personal component of the home prefix, which is a naming
accident and not the designed control. **"This does not leak in the suite or either CI lane"
is MEASURED FALSE.** The redactor gap itself is not this item's - it is filed as CS-860.

**CORRECTED IN PLACE - measured 2026-08-29 (session 46). THE PARAGRAPH ABOVE IS NOW FALSE IN
ITS MECHANISM AND STILL TRUE IN ITS VERDICT.** The report redactor no longer holds only the
single-separator and `as_posix` home spellings, so "on a chained cause the primary rule
CANNOT FIRE" and "contained on this machine only because the account name happens to be the
sole personal component of the home prefix" have both stopped being true: the `%r`-doubled
spelling and both URL-quoted ones are covered now, each by its own arm. What has NOT changed
is the verdict - the platform account id and the world name still render, and they are now
uncovered DELIBERATELY, with a stated reason each rather than by silence. **The detail is
CS-860's and is not restated here.** Read that section before citing this paragraph for
anything, because the sentence it corrects is the one most worth quoting and the one most
likely to be quoted stale.

**WHAT IS MUTATION-PROVEN.** 7 of 7 targeted mutants killed, including a true revert to
round 1's own gate and a revert of the census reporter's early return - the mutant that
SURVIVED round 1 and was reported as surviving rather than rounded up.

**RESIDUALS 2 AND 4 ARE UNTOUCHED AND THE ITEM STAYS OPEN.** Residual 2 - a raise in a CALLEE
of a handler - is the reason the acceptance cannot be met: it quantifies over "no shipped
chained raise", and the population provably misses a shape. Two further silences were
measured this session and belong to residual 2's class: adversary L2 measured that the
residual-3 forwarding detector holds for ONE spelling of twelve (`_identity(exc=exc)`, a
lambda, a dotted callee, an imported helper and a two-step forward all still grade
`unproven`), and that `_call_forwards_binding` is consulted for `node.cause` only, never for
`node.exc`.

**TWO AUTHORED CLAIMS WERE MEASURED FALSE AND CORRECTED.** The privacy record in
`tests/test_exception_rendering.py` said the chained-cause module emits no frame line; it
renders the frame-bearing default at two of its four `format_exception` calls, deliberately,
because the faithful-subset claim is not measurable without it (adversary L4). And the
"measured equivalent on all six shapes" claim does not hold for a `SyntaxError` in the chain,
whose `File` line SURVIVES `limit=0`, nor for a non-deterministic `__str__` (adversary L3).

**WHAT A NEXT ROUND SHOULD NOT REDO.** Round 2 and its arms are merged and mutation-proven.
Start at residual 2, and derive a population that can see a raise in a callee.


### RULING - filed 2026-09-01 (session 56), operator asked, adversary REFUTED the premise

**THE "DELIBERATELY NEVER RENDERED" CONJUNCT STAYS. IT DOES NOT GRADE ZERO.** The premise the
ruling was requested on - that the conjunct is a universal over an empty set - holds only
inside `tests/exception_message_guard.py`'s own mapping, which is where session 44 looked.
TWO LIVE RECORDS ELSEWHERE ASSERT THE SAME PROPOSITION IN DIFFERENT WORDS, and neither has
ever been evaluated against this conjunct:

- `tests/test_exception_rendering.py` lists the chained-raise shape in a docstring block
  declaring what is NOT a rendering, calls that half load-bearing, and sweeps every tracked
  module.
- `tests/test_verify_env.py` states that chaining attaches the exception rather than
  rendering it, implements that as a branch in its scan, and an ARM asserts the shape is not
  flagged - with the message that flagging a sanctioned shape is how a guard gets switched
  off. It does not merely restate the false claim, it DEFENDS it, and its stated reason
  argues against the remedy this item shipped.

Both were filed 2026-08-14 and both survived two CS-857 commits, one of which edited the
first file. The fence meant to stop recurrence is a comment above the exemption mapping
forbidding any entry from saying the cause is unrendered; nothing enforces it, and its own
wording scopes it to the entries below it.

**DO NOT DELETE THIS CONJUNCT AND DO NOT RE-POINT IT.** It already points at something live.
The repair is a sweep whose population matches the quantifier the clause already uses, and
it MUST NOT be a search for the phrase - see `memory/a-guard-can-measure-spelling.md`, and
note that this exact failure class is already owned by
`docs/adr/0008-detection-claims-are-derived-never-written.md`, whose tier-3 correction
records two sentences that shipped false and survived repeated careful reading.

**THE FIRST CONJUNCT IS SEPARATELY UNMET AND THAT IS THE LARGER FACT.** The census reports
shipped `measured-leak` sites under the graded layer on every run, in two `clockspeed/surface/`
modules added AFTER the paragraph above was written - and that paragraph, which says in
capitals that the live sites are owned by the guard rather than by itself, then hand-writes a
module list that has not moved since. The derived half tracked the new layer; the written half
did not. Treat the module list above as provenance, not as current truth.

**A BY-PRODUCT DEFECT IS FILED AS CS-880** - the two exemption reasons session 44 corrected
now misstate the raise form they describe.

## CS-858

### NOTE - filed 2026-08-28 (session 44) by the merger, from the CS-857 census

The CS-857 derivation sweeps every tracked Python file and finds chained-raise sites in the
two FROZEN files under `scripts/` and `tools/` that `CLAUDE.md` section 6 names. Both are
frozen, so no CS-857 slice could touch them and none did. `tests/chained_cause_guard.py`
derives them, classifies them and PRINTS them as out-of-scope-recorded on every run - that
warning is one of exactly two the suite emits, and IT IS THE OWNER OF THE COUNT. Read the
number off that warning; do not write one here.

**CORRECTED AGAIN 2026-09-01 (session 56), by CS-879.** The record is no longer frozen-only
and its lines no longer carry a bare FROZEN label. It now spans two buckets, each named on
its own line - the frozen files this item owns, and the census's own planted control modules
- so the warning covers a wider population than this section describes. CS-858's own scope is
unchanged: it owns the frozen half, and only that half.

**CORRECTED 2026-09-01 (session 56). THE THREE FIGURES THAT STOOD HERE WERE RESTATED COUNTS
AND ALL THREE HAD ROTTED.** The tracked-file total was exact on the day it was filed and was
wrong four days later. The site total read as a count of everything outside the shipped
layer, which it never was - it is the count in the two frozen files, and the population
outside the shipped layer is several times larger. And the claim that those two files are
where the out-of-shipped-layer sites live was already incomplete when written: a third,
UNFROZEN file carried one then and carries two now, and a fourth was added the following day.
That mechanism is CS-879 and the leak it hides is CS-878. This paragraph now names the owner
instead of copying it, which is `CLAUDE.md` section 4's own remedy.

**RECORDED IS NOT GRADED.** No arm asserts anything about their rendering. They are visible
and ungraded, which is the honest state but not a closed one. The operator approved filing
this as its own item on 2026-08-28 rather than widening CS-857.

**THE FROZEN ROUTE IS THE WHOLE COST.** `CLAUDE.md` section 6 requires an adjudicator grant
recorded in `docs/LEDGER.md` BEFORE an edit, and no agent grants itself the exception. If
the verdict is that these sites need no repair, the exemption still has to be stated
somewhere a guard reads.

### RULING - filed 2026-09-01 (session 56), operator asked for ONE answer binding CS-847, CS-860 and CS-807

**THE COUNT-VERSUS-DERIVE TENSION IS A FALSE DILEMMA: NEITHER WORDING CAN FAIL.** Measured,
not argued. A count on an item line is read by nothing - `tools/drift_guard.py` does not
contain the word acceptance, and CS-807's "fifteen" was WRONG ON ARRIVAL, describing a table
that held nineteen entries on the commit that wrote the number and holds nineteen now. A NAME
on an item line is read only for existence - the citation guard's resolver stays GREEN when
the binding it names is replaced by `pass` or rebound to `None`, and a `path:line` pointer is
judged only for falling inside the file.

**SO THE RULING IS: NO CENSUS COUNT ON AN ITEM LINE, AND NO CLAUSE IS REWRITTEN TO AVOID
ONE.** The second half is the part with evidence behind it. SIX attempts to improve an
acceptance clause by rewriting it have each lowered its bar - three on CS-854 last session,
reverted byte-for-byte, and three this session across CS-847, CS-858 and CS-807. Every one
was produced by an agent trying to strengthen the clause; every one was caught only by an
agent that wrote none of it. A proposed name-anchoring rule was refuted on four grounds, the
decisive one being that an emptiness test cannot see an ANCHOR-SIZED population, which
satisfies every clause such a rule produces.

**WHAT THIS ITEM NEEDS IS A TWO-SIDED ARM**, in the idiom this tree already uses: RED when a
site is added, and GREEN on a tree that has none. That grades how a derivation RESPONDS TO
CHANGE, which is the property a transcription fails and an output-shape check cannot see.
The fail-closed precedent is `tools/drift_guard.py`'s work-item guard, which is the machine
check for a different `CLAUDE.md` section 4 rule and treats any reduction of its own coverage
as RED rather than quiet.

**THIS ITEM'S OWN SCOPE IS NARROWER THAN THE SILENCE IT SITS IN.** CS-858 is scoped to the
FROZEN files, and that scope is correct for what it owns. The sites in the UNFROZEN files
under the same two directories are a different mechanism and are now CS-879, with the leak
one of them carries filed as CS-878. Do not widen this item to absorb them.

## CS-859

### NOTE - filed 2026-08-28 (session 44) by the merger, measured before filing

`tests/save/test_absolute_claims.py` governs prose in the modules named by its
`FENCED_MODULES` tuple. `tests/test_redaction_scope.py` is NOT among them, and nothing else
reads its prose - `tools/drift_guard.py` does not, and `tests/test_docs_citations.py` scans
`docs/` only. That is the mechanism by which its `clockspeed/save/world.py` pointer sat dead
from 2026-08-16 until session 44 found it.

**THE COST WAS MEASURED BEFORE FILING, WITH THE FENCE'S OWN MACHINERY** - `unbacked_absolutes`
against the module reports 35 findings over 132 sentences. Contract 1 admits three remedies
per finding - delete it, narrow it until the quantifier is gone, or make it name a test that
resolves - and states that an exemption list is NOT a third option. Several findings are the
module quoting CS-454's own acceptance criterion, and the contract says a marker inside a
quoted fragment still counts.

**DO NOT RE-SCOPE THIS AS A ONE-LINE CHANGE.** Adding the module to `FENCED_MODULES` is one
line; that line is not the work. The operator chose on 2026-08-28 to do the rewrite rather
than only file it, and it was NOT reached in session 44 - the round ended with the
adversarial pass incomplete. It is unstarted, not half-done.


## CS-860

### NOTE - filed 2026-08-29 (session 45) by the merger, MEASURED BEFORE FILING, from CS-857 adversary L3

**THE REPORT REDACTOR COVERS TWO PERSONAL-DATA CLASSES AND THE PROJECT NAMES MORE THAN TWO.**
`tests/conftest.py`'s `_build_redaction_rules` emits exactly two rule families - home-path
spellings, and account-NAME spellings. Measured against synthetic stand-ins: a 17-digit
platform account id and a world name both render VERBATIM through `redact_personal_data`.
`CLAUDE.md` section 2 names the account subdirectory as personal data and non-negotiable 3
names the world name, so both are in scope and neither is covered.

**AND THE PRIMARY RULE IS STRUCTURALLY BLIND TO THE SHAPE AN OSError PRESENTS.**
`OSError.__str__` renders `filename` through `%r`, which doubles every backslash. The
home-path family holds the single-separator and `as_posix` spellings only. Measured: the
home rule fires on the single-separator spelling and NOT on the doubled one, while the
weaker account-name rule does fire. So a chained cause is contained on this machine only
because the account name happens to be the sole personal component of the home prefix. THAT
IS A NAMING ACCIDENT, NOT A CONTROL, and it does not transfer to a CI runner or another
machine.

**WHY IT IS NOT CS-857.** CS-857 owns the chained-cause CHANNEL. This is the REDACTOR, and
it applies to every value that reaches a pytest report by any route - the rewritten assert
and the frame argument as much as the chain. Folding it into CS-857 would hide a general
defect inside a specific one.

**THE TRAP THAT MUST NOT BE REPEATED.** A run with `--rootdir` pointed at a tempdir loads
neither `pyproject.toml` nor `tests/conftest.py`, so it measures an unconfigured pipeline
and proves nothing. That is a recorded residual on CS-855. L3's forcing run reported
`configfile: pyproject.toml` in its header, which is what makes its result about the shipped
pipeline.

**DO NOT WIDEN THE RULES BY GUESSING.** The needle set is derived from the machine. A world
name is not a fixed string and an account id is a shape, not a value, so the remedy is a
pattern plus a derivation, and the arm that proves it must plant a synthetic value rather
than this machine's own.

### REFUTED BY FIVE REVIEWERS, REPAIRED, AND CS-860 STAYS OPEN - recorded 2026-08-29 (session 46)

**READ THIS BEFORE TAKING THE ITEM. THE FIVE REFUTATIONS AND THE ROOT CAUSE MATTER MORE THAN
THE CODE THAT SHIPPED**, because the code that shipped is mostly a BACKOUT and the next
attempt has to avoid the same shape.

**THE FIRST ATTEMPT WIDENED THE REDACTOR FROM TWO CLASSES TO FOUR, AND THE WHOLE SUITE WAS
GREEN ON IT.** It added a POSITIONAL `account-id` rule and a `.sav`-anchored `world-name`
rule beside the two existing families, plus the escaped spellings for the home family. Green
was the state the tree was in while every finding below was already true of it. **NO PASS
COUNT IS WRITTEN HERE**: this recording pass did not run the suite, and a number carried
forward from another agent's report is exactly the kind of unverified figure `CLAUDE.md`
section 4 forbids restating.

**FIVE INDEPENDENT REVIEWERS - FOUR ADVERSARIES AND AN ADJUDICATOR - REFUTED IT.** The two
new SHAPE rules were measured simultaneously TOO NARROW and TOO GREEDY:

| Input | Rendered | Fault |
|---|---|---|
| `'Some Save Name.sav'` | `'Some Save <redacted-save>'` | a world name with a SPACE leaks its leading words |
| `'He said "Hi".sav'` | unchanged | LEAKS ENTIRELY |
| `'What?.sav'` | unchanged | LEAKS ENTIRELY |
| `'workdir.py:120: in copy_for_read(World.sav)'` | `'workdir.py:120: in <redacted-save>)'` | A FUNCTION NAME ERASED FROM A TRACEBACK FRAME LINE |

A real repo test rendered `assert '<redacted-save>' == '<redacted-save>'` - a diff whose two
sides are byte-identical, and therefore a failure report that cannot be diagnosed at all.

**ROOT CAUSE, AND THIS IS THE DURABLE LESSON.** The segment character class both shape rules
were built on was borrowed from `clockspeed/data/locate.py:187`, where it is CORRECT, because
that redactor receives PATHS. `redact_personal_data` receives WHOLE FAILURE REPORTS -
arbitrary prose. A path-segment class is safe on a path and destructive on arbitrary text.
**TOO NARROW AND TOO GREEDY ARE THE SAME KNOB HERE**: widening the class until it holds a
spaced world name is the same edit that widens what it eats out of a frame line. It cannot be
tuned into correctness, so do not try. It has to be replaced by a mechanism that does not
assume its input is a path.

**THE HEADLINE FINDING - THE GUARD WAS ITSELF GREEN BY ACCIDENT.** Deleting `quote` from the
home-spelling transforms left the WHOLE SUITE GREEN, because the URL-quoted home spellings
were rescued by the ACCOUNT-NAME rule. That is the exact "naming accident, not a control"
CS-860 was filed to eliminate, REPRODUCED ONE LEVEL UP, INSIDE THE GUARD WRITTEN TO PREVENT
IT. Two reviewers found it independently, by different methods, which is what makes it a
property of the design rather than one agent's slip. **THIS IS THE FIFTH CONSECUTIVE SESSION
TO PRODUCE A FALSE CLEARANCE INSIDE THE GUARD BUILT TO PREVENT THE PREVIOUS ONE - AND THE
FIRST IN WHICH IT WAS CAUGHT BEFORE THE OPERATOR WAS TOLD ANYTHING HAD CLOSED.**

**A SECOND GRADING DEFECT: REGISTRATION IMPLIED NOTHING BEHAVIOURAL.** A class registered
with a NEVER-MATCHING pattern and an EMPTY arm satisfied every oracle arm, because the arms
checked a TUPLE SLOT and a FUNCTION-NAME SUBSTRING and never whether a rule MATCHES anything.
Swapping two rules' class tags also left everything green - the tags were decorative.

**OPERATOR RULING.** Keep the home-path widening. BACK OUT the two shape rules. Register both
classes as KNOWN UNCOVERED with a stated reason each. Close the two grading defects.

**WHAT SHIPPED - RULE POPULATION MEASURED THIS SESSION FROM THE SHIPPED BUILDER.** 12 rules:
10 tagged `home-path`, 2 tagged `account-name`. Five distinct home spellings, and every one
redacts - `home-native`, `home-posix`, `home-doubled` and BOTH of `home-quoted-native` and
`home-quoted-posix`. **EACH SPELLING NOW HAS ITS OWN ARM**, rather than being covered by a
pooled fingerprint the native spelling already satisfied, which is what let the deleted
transform go unnoticed. Registration now carries a BEHAVIOURAL obligation: a class declared
covered must demonstrably rewrite its own planted string into its own placeholder using ONLY
its own tagged rules. The grading mutants that motivated the repair - a hollow registered
class, a swapped class tag, and a deleted `quote` transform - are reported by the slice that
built it as having each SURVIVED before and each been KILLED after; this recording pass did
not re-run them, and that is stated rather than rounded up.

**A LEAK WAS FOUND IN THE NEW ARM ITSELF, AND IT IS CS-850's DEFECT REPRODUCED INSIDE
CS-860's OWN GUARD.** The arm that kills the pooled-fingerprint mutant asserted on a value
DERIVED FROM THE REAL HOME, and pytest renders the asserted EXPRESSION independently of the
message attached to it. Measured with both rule families hollowed: the report carried the
bare account name VERBATIM. Fixed by binding a plain scalar in three arms before asserting.
**A GUARD AGAINST A LEAK IS NOT EXEMPT FROM THE LEAK IT GUARDS**, and this is the second item
in the family to learn that from its own output.

**THE PROSE REPAIRS FROM THE FIRST ATTEMPT WERE REVERTED**, because backing out the shape
rules makes the original sentences true again. The audit then found TWO sentences still false
- and PRE-EXISTING, false at `afd85bd` as well, so not this session's damage:
`tests/assertion_rendering_guard.py` claimed the report redactor recognises a MACHINE NAME.
Measured false - `_ACCOUNT_VARIABLES` at `tests/conftest.py:426` holds `USERNAME`, `USER` and
`LOGNAME` and reads `COMPUTERNAME` nowhere. `clockspeed/data/locate.py` redacts a machine
name; the conftest redactor that rule borrows does not. Two redactors, and only one of them
is behind that rule. Corrected in place.

**WHAT CS-860 STILL OWES - THIS IS THE ITEM'S LIVE STATE.** Two of the four personal-data
classes `CLAUDE.md` names are still not redacted from a failure report: the platform account
id and the world name. They are now uncovered in EVERY form, not merely the bare form the
item was filed on, because the escaped and spaced forms went out with the backout too.
**THE GAP IS NO LONGER SILENT, AND THAT IS THE SESSION'S ACTUAL GAIN.** Both classes stay
REGISTERED, `UNCOVERED_CLASSES` in `tests/conftest.py` carries a reason each, and arms assert
that NO rule serves either and that their planted probes pass through UNTOUCHED - so the gap
can neither close by accident nor widen unnoticed. What the item owes is a mechanism that
does not assume its input is a path.

**TWO COUNTER-EXAMPLES ARE PINNED AS STANDING REGRESSION GUARDS, AND A CORRECT REBUILD MUST
SURVIVE BOTH.** They are
`tests/test_report_redaction_classes.py::test_a_redaction_never_erases_the_frame_around_a_save_filename`
and `::test_a_redaction_never_leaves_half_a_spaced_save_filename`. The rule they encode: a
redaction MAY rewrite a filename inside a traceback frame line; it may NEVER eat the frame
around it, and it may NEVER rewrite half a spaced name. Both survived the backout deliberately
- they are the shape of the next attempt's acceptance, not scaffolding for the one that was
withdrawn.

## CS-861

### NOTE - filed 2026-08-29 (session 46) by the slice-B builder, MEASURED BEFORE FILING

**`redact()` NORMALISES ONE BACKSLASH TO ONE FORWARD SLASH, AND AN ESCAPED PATH CARRIES
TWO.** `clockspeed/data/locate.py`'s `redact()` opens with a single normalisation pass over
its input, and `_redaction_pairs` builds every path needle through that same single-slash
normalisation. A `%r` rendering - what `OSError.__str__` puts in front of `filename`, what
an f-string `!r` emits, and what a default `__repr__` of a path-bearing object emits -
DOUBLES each backslash, so the same path normalises to a doubled-forward-slash spelling
that no needle holds. Measured on this tree: the shipped builder produced 13 needle pairs,
8 of them carrying a forward slash and NONE carrying a backslash.

**FOUR RULES FAIL, NOT THREE, AND THE FOURTH IS THE ONE THAT MATTERS MOST.** Measured by
asking whether each rule's own placeholder token appears in `redact(rendering)`, for one
path in three renderings:

| Rule | Token | native | `as_posix` | ESCAPED |
|---|---|---|---|---|
| home | `<home>` | fires | fires | **DOES NOT FIRE** |
| LOCALAPPDATA | `<localappdata>` | fires | fires | **DOES NOT FIRE** |
| APPDATA | `<appdata>` | fires | fires | **DOES NOT FIRE** |
| account directory, by POSITION | `<account-dir>` | fires | fires | **DOES NOT FIRE** |

**SEVERITY, IN ONE SENTENCE: A PLATFORM ACCOUNT ID RENDERS VERBATIM IN THE ESCAPED
SPELLING.** `CLAUDE.md` section 2 names the account subdirectory as personal data outright
and non-negotiable 3 forbids it reaching a tracked file, so this is what makes CS-861 tier 1
rather than a tidy-up.

**THE POSITION RULE IS SILENT AND THE DIGIT-RUN BACKSTOP RESCUES EXACTLY ONE SHAPE.** The
positional pass cannot match because its anchor holds single separators while the escaped
text holds doubled ones, so the account directory falls back on the digit-run backstop alone,
whose floor `MIN_ACCOUNT_ID_DIGITS` was measured at 8. Four SYNTHETIC ids under the real
save-root layout, re-measured 2026-08-29 (session 46):

| Synthetic account directory | Shape | native | `as_posix` | ESCAPED |
|---|---|---|---|---|
| `90000000000000001` | all-digit, 17 long | redacted | redacted | redacted |
| `MSFT-abcdef` | prefixed token, no digit run | redacted | redacted | **SURVIVES** |
| `a1b2c3d4e5f60718` | Epic-shaped hex | redacted | redacted | **SURVIVES** |
| `a1b2c3d4-1234-5678-9abc-def012345678` | braceless GUID | redacted | redacted | **SURVIVES** |

**THE STEAM SYNTHETIC WAS REPLACED, AND THE REASON IS THIS NOTE'S OWN SUBJECT.** The id this
row used to carry opened with the public `7656119` SteamID64 constant and continued with
digits nobody had chosen to differ from a real one, so a synthetic in a TRACKED file sat
closer to a real value than it had any need to. The replacement is outside the SteamID64
range entirely and so shares a leading prefix with nothing. The row proves exactly what it
proved before: the backstop keys on a RUN OF DIGITS, never on the prefix.

**THREE OF THE FOUR TESTED SHAPES SURVIVE.** The Epic-shaped hex carries digits, but its
longest run of CONSECUTIVE digits is 5, below the floor of 8, so the backstop cannot reach
it. The braceless GUID fails for a DIFFERENT sub-reason, worth keeping separate because it
constrains the remedy: its longest run is 9, ABOVE the floor, and the backstop still refuses,
because that run is not separated from the hex around it and the pattern's boundary assertion
excludes an alphanumeric neighbour. **A RUN LONG ENOUGH IS NOT THE SAME AS A RUN THE BACKSTOP
CAN SEE.** The backstop rescues the all-digit shape and nothing else. The braceless GUID is
also the shape the module's own comment attributes to the Microsoft Store, so the fourth row
is not a curiosity - it is a shipping platform that had gone untested.

**THIS COUNT HAS NOW MOVED TWICE AND IS THE SEVERITY OF THE ITEM.** A first draft said one
shape survives; an independent re-measurement found two; a session-46 reviewer found the
braceless GUID untested altogether and it survives as well. Re-derive it rather than carrying
it forward.

**THE WHOLE MECHANISM IN ONE RENDERED LINE.** The tail only - the prefix is elided because it
is a real path, and it was separately measured to carry no personal value once redacted:

    ...FactoryGame//Saved//SaveGames//MSFT-abcdef//<save-file>'

The save-FILE rule fires. The positional rule is silent. The account id stands in the clear
between the two. The trailing quote is the closing quote of the `%r` rendering, and the
leading ellipsis is the elision, not part of the output.

**THE MODULE ALREADY SAYS WHY THIS IS THE FAILURE MODE.** `clockspeed/data/locate.py:141`
records that the position rule exists because only one platform puts digits in that slot -
Epic writes a hex token, the Microsoft Store a braceless GUID, and a `CLOCKSPEED_ACCOUNT_DIR`
override whatever the operator typed - and calls keying on digits precisely how a redactor
comes to be correct for one shape and silent for the other three. The escaped rendering
returns the module to exactly that state, and the table above is that sentence coming true:
correct for the all-digit shape, silent for all three others tested.

**EVERY ID IN THIS NOTE IS SYNTHETIC AND INVENTED**, which is precisely why it is safe to
write them down. The real account directory is never written into a tracked file - `CLAUDE.md`
non-negotiable 3 - and the commit gate blocks on it.

**WHAT STILL WORKS, STATED SO THIS IS NOT OVERCLAIMED.** The account-NAME rule DOES fire on
the escaped rendering, and the save-FILE rule fires in all three renderings. Both were
measured rather than assumed.

**CONTAINMENT ON THIS MACHINE IS LAYOUT LUCK, NOT REDACTION.** The pinned development
machine's home has three path components and the account name is the only personal one, so
the surviving account-NAME rule happens to cover the home path in the escaped spelling as
well - measured: the doubled home spelling does NOT survive `redact()` here. That is a
property of this layout, not of the redactor. A home carrying a SECOND personal component -
a company name, a real name, a redirected profile root - has nothing covering that component
once the home rule is silent. Do not read the green result on this machine as the rule
working.

**THE MODULE ALREADY REASONS ABOUT ALTERNATE RENDERINGS AND MISSED THIS ONE.**
`clockspeed/data/locate.py:39` reads "exception or a repr goes through redact() first",
closing a sentence that begins on the line above it. The module's own "WHAT redact() LEARNED
THE HARD WAY" list records the 8.3 short form - an alternate RENDERING of the same path
whose spelling no needle held. The escaped rendering is a fourth member of that same class,
and it is the one the docstring's promise about a repr walks straight into.

**REACHABILITY IS UNVERIFIED.** What is measured is the FUNCTION, in isolation, called
directly. NO live call chain has been shown to reach `redact()` with an escaped spelling.
The docstring's claim makes such a chain plausible; it does not prove one exists. Anyone
closing this item must establish reachability by measurement or record the defect as latent.
Do not round this paragraph up to a live leak.

**DO NOT FOLD THIS INTO CS-860 OR CS-857.** CS-860 is the pytest report redactor in
`tests/conftest.py` - a different module, a different needle builder, a different consumer
set, and it carries NO normalisation step at all, so it fails for a related but distinct
reason. CS-857 owns the chained-cause channel. This item is the same MECHANISM CLASS in
PRODUCTION code and needs its own remedy. Folding a general production defect into a
specific harness item is how a false clearance ships: the harness item closes, and
`clockspeed/` stays ungraded behind it.

**NO REMEDY IS SETTLED HERE.** The acceptance names what must be true. How `redact()` gets
there - collapsing runs of separators, adding the escaped spelling to the needle population,
or matching a normalised form of both sides - is the implementer's call, and the options
differ in their over-redaction risk.

## CS-864

### Filed 2026-08-30 (session 50)

**THE SEAM ARMS GRADE SYNTAX, NOT REACH.** The three arms in
`tests/save/test_independent_table.py` that keep `independent_table.py` free of shipped
readers match `objects.<name>(...)` syntactically and check that each named attribute is
non-callable. Graded with five mutants, pristine floor restored after each:

| mutant | arms that fired |
|---|---|
| direct `objects.parse_body(...)` | 2 of 3 |
| `from clockspeed.save.objects import parse_body` | 1 of 3 |
| alias then call | 1 of 3 |
| `objects.struct.unpack_from(...)` - two-level reach | 0 of 3 |
| `getattr(objects, "parse_body")(...)` | 0 of 3 |

**The module ALREADY calls an attribute reached through `objects.`** - `.get` on the layout
mapping at the pair lookup - and the arm named for that prohibition passes anyway. So the
prohibition as worded is already false of the shipped tree, which is the part to fix first:
either grade what is claimed, or narrow the claim to what is graded. The docstring has been
narrowed already; the arms have not.

### NARROWED BY CS-862 - measured 2026-08-31 (session 51), and what is LEFT

**BOTH UNCAUGHT ROUTES NOW REDDEN SOMEWHERE - just not in a static arm.** CS-862 added
dynamic seam arms that degrade the shipped record table AT ITS SOURCE and require the
second reading to still match the fixture and the body's own bytes. Graded, pristine floor
restored after each, all four static arms including the transcription anti-drift arm
staying GREEN throughout:

STATIC below is the four arms in that module's seam-guard section - the three seam arms
plus the discriminator anti-drift arm. DYNAMIC is the 15 cases of
`tests/save/test_independent_table.py::test_the_second_reading_stays_right_while_the_shipped_record_table_is_degraded`
plus
`tests/save/test_independent_table.py::test_a_degraded_shipped_record_table_cannot_move_the_hand_built_offsets`.

| route | static red | dynamic red |
|---|---|---|
| `getattr(objects, "parse" + "_body")` wrapper | 0 of 4 | 15 of 15 |
| kind read as `objects._KIND_BY_OBJECT_TYPE.get(...)` | 0 of 4 | 5 of 5 reachable |

For scale, the DIRECT `objects.parse_body(...)` wrapper - the least subtle route there is -
reddens 2 of those 4 static arms, not 3 and not 4.

**WHAT THAT DOES AND DOES NOT CHANGE.** It removes the sharpest consequence - neither
route is invisible to the whole suite any more - and it does NOT satisfy this item. The
acceptance is about THESE ARMS grading what they CLAIM, and the claim is still worded as a
prohibition that the shipped tree already violates: `.get` on the layout mapping is an
attribute reached through `objects.` and the arm forbidding it passes. A dynamic arm
elsewhere is a different guard, not a repair of this one.

**AND THE DYNAMIC ARMS DO NOT COVER THE GENERAL CASE.** They move a reading only where it
delegates to something `objects.parse_body` itself consults. A reading rebuilt out of
shipped `_Cursor` primitives is moved by neither plant. That residue is this item's.

## CS-865

### Filed 2026-08-30 (session 50), from the CS-829 adjudication

**A FITTED BOUND WITH ZERO HEADROOM.** `_UNEXPLAINED_WORD_CEILING` is 1 and the library
sits at exactly 1. Per version pair one subset alone gives 2. It is deliberately NOT
skipped, and that decision is measured rather than assumed: skipping its excess was built
and REVERTED in an earlier round because an in-process mutant refusing the weakest reading
word at `objects._decode_struct_interior` is caught by that arm and NO OTHER, so the skip
that spared the subset also spared a real defect.

**WHAT THIS ITEM IS NOT.** It is not a request to raise the bound, and it is not a request
to skip it. Both have been tried and both are recorded as wrong. It is a request to ground
the per-word residue in evidence that does not depend on which saves the operator's library
happens to hold at the moment the suite runs.

## CS-868

### Filed 2026-08-31 (session 53), from an adversarial pass CS-863's own session recorded as owed

**CS-863 SHIPPED WITHOUT AN INDEPENDENT PASS AND SAID SO.** Its arms were built and graded
by the session that wrote them. THE ARMS ARE THOSE OF
`tests/save/test_struct_interior.py`, which is the module every measurement below is
taken over; that citation moved here from the item line, which does not carry it. This is that pass, and it REFUTES them. Two agents that
produced no part of CS-863, working from different briefs and building their mutants
independently from source, reached the same counter-example; the second never opened the
first's directory.

**THE COUNTER-EXAMPLE.** Replace the body of `_independent_sites_of` with a memo over a call
to `tests/save/test_decode_oracles.py`'s `_walk_with_the_shipped_reader`. That helper carries
its own `for _ in range(objects._MAX_TAGS_PER_PAYLOAD)`, so the mutant puts CS-863's defect
straight back - the second reading consults the shared ceiling again.

| variant, whole module | observed |
|---|---|
| pristine floor | 37 passed, EXIT 0 |
| the memo mutant | **37 passed, EXIT 0** |
| the same mutant with the memo deleted | 1 failed, 1 passed, EXIT 1 |
| the memo ALONE over the repaired walk | 37 passed, EXIT 0 |

**TWO MECHANISMS, AND BOTH HAVE TO BE FIXED.** `_shared_tag_symbols` records a symbol only
where the AST node is an attribute over the name `objects`, and it parses THIS MODULE'S
SOURCE ONLY - so the assertion that the ceiling's name is absent cannot see a ceiling read
in another module. And `_run_ceiling_control` takes its pristine and its degraded reading
over the SAME body object, so under a memo the degraded call is always a cache hit.

**IT IS A FAIR MUTANT, NOT AN ADVERSARIAL CURIOSITY**, and that is the reason to word this
as a hole. The memo alone is invisible. The call is one line away - `_shipped_sites_of`
already calls that same helper and the module is already imported. Every record is walked
twice, so a memo is the obvious performance edit. And the project has been bitten by this
exact shape twice already in the sibling module: CS-862's correction and CS-866.

**DO NOT REPAIR THIS BY DELETING THE MEMO.** There is no memo in the tree. The arms have to
be unable to accept a reading that is a cached function of the shipped one, which is what
CS-866 did next door by making every graded case ask a question no earlier call answered.

## CS-869

### Filed 2026-08-31 (session 53), from the same pass

**THE CONTROL'S STRENGTH IS PICKED, AND ITS SKIP IS KEYED ON THE WRONG QUANTITY.**
`_CEILING_CONTROL_TAGS` is a bare literal; nothing derives it from the corpus and nothing
asserts the corpus exceeds it. Measured on the graded pair, one library read:

| control ceiling | struct sites, pristine to degraded | records reached, pristine to degraded | skip fires |
|---|---|---|---|
| 8 (shipped) | 30642 to 28716 | 77263 to 76368 | no |
| 22, 24, 26 | 30642 to 30642 | 77263 to **77260** | **yes** |

The skip compares SITE counts. The plant refuses whole RECORDS, and the three it refuses
carry no struct tag, so the site count never moves and the arm skips before either
assertion is reached. **THE SUPPRESSED TRUE POSITIVE, measured:** with CS-863's defect
deliberately restored, a control ceiling of 24 gives 1 skipped EXIT 0 where the shipped
literal 8 gives 1 failed EXIT 1.

**THE CONSTANT'S OWN DOCSTRING IS FALSE.** It says any ceiling below the corpus's observed
maximum exercises the same loss class. The observed maximum is 31 and 22 through 26 are
below it and exercise nothing.

**NOT A REQUEST TO PICK A BETTER NUMBER.** A second hand-picked literal is the same item
again. The counts are library-dependent and the operator plays while sessions run.

## CS-870

### Filed 2026-08-31 (session 53), from the same pass

**THE REVERT ASSERTION GRADES `monkeypatch`, NOT THE CONTROL.** In
`test_a_stricter_shared_ceiling_cannot_improve_this_modules_grade`, `monkeypatch.undo()`
restores the value `monkeypatch.setattr` saved, and the next line asserts that value is
what the module now carries. It cannot fail while `monkeypatch` works, whatever
`_run_ceiling_control` did.

**AND THE CONTROL REALLY CAN LEAVE THE MODULE DEGRADED.** Proven by direct call rather than
by the mutant alone: with the trailing `_install_ceiling(original)` deleted from the
control's record loop, a direct call leaves the ceiling installed at the control's own
value instead of the shipped one, and the arm still reports 1 passed EXIT 0. The docstring
claiming the plant is asserted to have landed, fired and been reverted is two thirds true.

**WHY IT MATTERS BEYOND THE ARM.** A control that leaves a shipped constant degraded
poisons every later measurement in the same process. `monkeypatch` happens to save the
session here, which is exactly why the arm cannot notice that it is doing all the work.

## CS-871

### Filed 2026-08-31 (session 53), from the CS-866 adjudication

**A DEAD CROSS-REFERENCE SHIPPED INSIDE THE COMMIT THAT REPAIRS THAT FAULT CLASS, AND NO
GUARD SAW IT.** Two `:func:` roles in `tests/save/test_independent_table.py` named a function
bound nowhere. An adjudicator found them by reading; nothing mechanical did. They are FIXED -
this item is the GAP, not the instance.

**WHY NOTHING CAUGHT IT.** `tests/test_docs_citations.py` matches the shape
`<path>.py::<name>`. A Sphinx role written `:func:` with the symbol in backticks is a
different shape and no judged pattern covers it. The guard's population is also the tracked
DOCS; a role inside a test module is not in it at all.

**THIS IS THE SAME FAULT CLASS SESSION 52 WAS BITTEN BY, ONE LAYER OVER.** There, a
subagent's paraphrase of an arm name reached a note and the citation guard DID catch it,
because it was written in the shape the guard reads. Here the identifier was wrong in a
shape the guard does not read. The lesson is that the guard grades a SPELLING, not the
property, and the property is that every identifier written down resolves.

**THE SECOND RESIDUE THIS ITEM CARRIES.** `_bodies_no_dynamic_case_may_reuse` enumerates
only the bodies THIS module builds, while `tests/save/test_struct_interior.py` calls
`independent_table.independent_records` at four sites in the same process. The adjudicator
measured that all four hand over real decompressed save bodies and that the guard's set and
the dynamic set have ZERO overlap, so no collision exists today - and NOTHING ASSERTS EITHER
FACT. The prose has been narrowed to the module scope the guard measures; the assertion has
not been written. A real body is a save's whole world and a synthetic fixture is a few
hundred bytes, so the honest form is probably a size floor rather than an enumeration.

**DO NOT REPAIR THIS BY WIDENING THE DOC CITATION REGEX ALONE.** The role shape is one
spelling of the same property; a guard that learns `:func:` and stops has bought one
spelling, which is exactly the finding CS-864 records about the seam arms and CS-868 records
about `_shared_tag_symbols`. Resolve the symbol against the module's own symbol table.



## CS-888

### NOTE - filed 2026-09-03 (session 57) by the merger, MEASURED BY AN ADVERSARY, EXECUTED

**DEFERRAL IS PROVEN BY IMPORT ALONE, AND THAT IS A CLEARANCE ANY IMPORT CAN BUY.**
`tests/chained_exemption_guard.py` requires every module that statically reads a raise's
`cause` field to be the owner, defer to the owner, be recorded, or be a finding. Deferral is
decided by `defers_to_owner`, which asks only whether the module imports the census.

**MEASURED, NOT READ.** CS-880 added `from tests.chained_cause_guard import FORM_EXPLICIT,
FORM_SUPPRESSED, Site` - three constants and a dataclass, none of which returns a chaining
verdict. The immune set went from FOUR modules to SIX. An adversary appended an identical
static cause read to `tests/exception_message_guard.py` in a copy of each tree and ran the
live arm: RED at 528d5b6 naming the planted line, GREEN at 55e7b75. Coverage was lost and
nothing in the tree can see it.

**FIVE OF THE SIX IMMUNE MODULES READ NO `cause` FIELD AT ALL**, so they hold unused
immunity. Nothing pins the set, so a seventh is free.

**THE MERGER CAUSED THIS AND SAYS SO.** The session-57 brief MANDATED the import, because the
alternative - an `EXEMPT` entry in `tests/chained_exemption_guard.py` - was on no slice's
write-list. That was a decomposition error. The import is still the better of the two
available routes: removing it makes the module an UNRECORDED adjudicator, which is worse.
**DO NOT "FIX" THIS BY DELETING CS-880's IMPORT.**

**THE FENCE.** The repair is about what EARNS immunity, not about who currently holds it. A
narrower rule that reports more is the correct direction here - `memory/a-guard-can-measure-
spelling.md` records that an over-proving guard costs a reader the belief that they need to
look at all.


## CS-889

### NOTE - filed 2026-09-03 (session 57) by the merger, MEASURED BEFORE FILING

**THE CITATION GUARD READS ONE FORM IN ONE PLACE.** `tests/test_docs_citations.py` resolves
the module-and-symbol citation form inside `docs/*.md`. A citation naming a LINE NUMBER instead of a symbol, or one written
anywhere outside `docs/`, is read by nothing.

**FIVE DEAD ONES IN A SINGLE FILE, MEASURED.** `tests/test_make_cert.py` cited
`scripts/make_cert.py:224`, `:279` and `:222`, plus two line RANGES into
`scripts/verify_env.py`. Two were pointing at a bare `"-out",` and at a BLANK LINE. All five
were already dead before session 57 and CS-882 pushed the targets a further 44 lines away
while `tests/test_docs_citations.py` stayed green at 135 passed. They are now repaired to
symbol form by the CS-882 residual slice - **the INSTANCES are fixed and the CLASS is not**.

**THIS IS THE FAULT `Site.key` AND `Copy.key` ALREADY DESIGN AGAINST** by omitting line
numbers, for the reason CS-857 recorded. The lesson is in the code and absent from the guard.

**A NOTE ON SCOPE.** The cheapest sound repair may be to FORBID the line-number citation form
outright rather than to resolve it, since a resolvable line number still rots on the next
edit above it. Measure both before choosing.


## CS-890

### NOTE - filed 2026-09-03 (session 57) by the merger, MEASURED BEFORE FILING

**A DANGLING WIKILINK IN THE DURABLE STORE, AND THE GUARD OVER THAT STORE IS GREEN.**
`memory/a-proof-can-require-the-defect.md` links `[[a-pooled-guard-hides-its-worst-member]]`.
No such file exists in `memory/` and no such row exists in `memory/MEMORY.md`.
`tools/drift_guard.py` reports CLEAN 10 of 10 with the link in place, so guard (b), memory
reachability, does not read wikilink targets.

**FOUND BY A BUILDER THAT NEARLY SHIPPED THE SAME FAULT.** The CS-880 repair slice cited
`memory/pooled-guard-hides-its-worst-member.md` in two files, caught before committing that
the path does not exist in the repo - it exists only in the harness-side store, which is a
DIFFERENT store that no tracked file may cite - and repointed to
`memory/a-guard-can-be-green-by-accident.md`, which owns the same shape at line 40. The
merger had propagated the wrong path into four briefs and into its own session reporting.

**THE INSTANCE IS REPAIRED IN THE SAME COMMIT THAT FILES THIS.** The link now points at
`a-guard-can-be-green-by-accident`. What remains open is the CLASS: nothing stops the next
one.

**TIER 1 RATHER THAN 2** because the repair is a reachability sweep over one directory, not a
change to any grading population.
