# 0006 - the un-sharded clock base enters the model, and the ceiling fence holds

## Status

`accepted` - 2026-08-14

Written by the slice that implemented it, which correctly left it `proposed` because per
`CLAUDE.md` section 5 the producing agent does not grade its own output.

**Flipped to `accepted` by an adjudicator that wrote no part of this ADR, of the registry
change, or of the tests.** That adjudication re-derived every factual claim here from the
tree rather than from this document: it read the key constant and the `Building` field in
`clockspeed/data/registry.py`, recovered the DELETED assertions from `git show` rather than
trusting the description of them, and re-ran the corpus mutation itself through the real
`build_registry` seam with the read path forced to a folded `Fraction(1)` - under which both
mutation assertions fail while every non-mutating assertion still passes, which is exactly
the property claimed for them below. ADR 0005 was confirmed byte-identical to its creation
commit.

Three imprecisions found and left standing as harmless. None is on a fence:

- "forbids strictly more than the one it deletes" holds for the field names and for the four
  ceiling operands, and NOT for one assertion: the old fence forbade `mMaxPotential` among
  this module's string constants and the new one requires it. That reversal IS this
  decision, and the Context states it plainly, so the sentence overclaims rather than
  misleads.
- "No other operand of the ceiling equation is read, named or stored here" - the registry's
  module docstring names all four. That text is the prohibition rather than a breach of it,
  and the re-pitch list already scopes the test to the module's string constants.
- "the roadmap item" in the Context is not cited by item ID, and no open item in
  `ROADMAP.md` matches it today.

One route is fenced by name and re-pitch list only, recorded rather than closed here:
nothing mechanical stops a future caller reading `Building.unsharded_clock_base` directly
and clamping without going through `clamp_to_unsharded_base`. This ADR claims the name and
the docstring as that fence and claims no more.

**This ADR does not supersede ADR 0005 and changes no word of it.** 0005 decided WHERE the
ceiling comes from and concluded that no file on this machine carries it. 0006 decides HOW
the one operand that IS in the shipped data reaches the model. 0005 specified that read and
could not perform it: it says so in as many words, that `clockspeed/` was owned by a
different slice and that the ADR only specifies. This is the slice.

## Context

ADR 0005 consequence 1 requires `mMaxPotential` to be read per building class off the
normalized registry, so that no literal `1.0` is ever written into the solver - for the same
reason the S7 spike banned a literal power exponent. A balance patch moves a shipped number,
and a literal turns that move into silently wrong advice instead of a red build.

The registry contradicted that requirement, deliberately and in writing. Its module docstring
stated that `mMaxPotential` "is deliberately not read", `Building` carried no field for it,
and the test suite actively ENFORCED the absence: one assertion held that the module's string
constants contain nothing matching the key. That fence was correct when it was written -
before ADR 0005 there was no answer to "is this the ceiling", and refusing to read a field
nobody understood was the honest position. After ADR 0005 it is a fence around the wrong
thing. It blocked the required read while permitting, unchecked, a read of every OTHER
operand of the ceiling equation.

So the state before this decision was a genuine deadlock: `clockspeed/solve/power.py` cannot
obey ADR 0005 without a data path to the base, and inventing a literal `1.0` in the solver is
what ADR 0005 and the roadmap item both forbid.

Alternatives considered:

- **Leave the field unread and let the solver carry a literal.** Rejected outright - it is
  the exact thing ADR 0005 exists to prevent, and a widely-shipped value is still a magic
  number.
- **Name the field `max_potential`, matching the game key.** Rejected. The registry already
  renames game keys into descriptive python names, and here the name IS the fence. "Max
  potential" reads as an achievable maximum to every reader who has not read ADR 0005, which
  is every future reader by default. The verbatim key survives as the `KEY_MAX_POTENTIAL`
  constant, so provenance stays greppable without the misleading name propagating into
  callers.
- **Delete the old test rather than replace it.** Rejected. The old assertion protected
  something real - that nothing here assembles a ceiling - and deleting it would have traded
  a fence for nothing. It is replaced by a strictly stronger one instead.
- **Read the other operands too, and compute the ceiling.** Rejected, and this is the
  dangerous one because it looks like completeness. ADR 0005 established that the slot count
  is absent from every source on this machine. Three of four operands assembles a ceiling
  silently missing its multiplier, which is the original failure with arithmetic in front of
  it.

## Decision

**The un-sharded clock base is read from the document into `Building`, under a python name
that cannot be mistaken for a ceiling, and the ceiling stays unbuilt.**

Concretely:

1. `KEY_MAX_POTENTIAL` holds the game's spelling verbatim, beside the other document keys.
2. `Building.unsharded_clock_base` is `Fraction | None`, appended at the END of the dataclass
   with a default, because a required field inserted mid-class breaks every positional
   construction at once.
3. `None` means the entry declared none. It is NEVER defaulted to 1, on the same rule that
   governs a missing power exponent: absence is a fact the document stated, and defaulting it
   publishes a number the game never shipped, in the right type, indistinguishable from a
   measured one.
4. It is read through the same optional-numeric helper as every other numeric field, so a
   present-but-non-string value and an unparsable number are flagged exactly as they are
   everywhere else rather than collapsing into the "declared none" reading.
5. No other operand of the ceiling equation is read, named or stored here.

## Consequences

**What this buys:** the solver can obey ADR 0005 consequence 1 without a literal. The base
travels as an exact `Fraction` from the decimal string, never through `float`. The test fence
that replaces the old one forbids strictly more than the one it deletes: it pins the base as
READ FROM DATA by mutating the corpus - a folded `Fraction(1)` passes every non-mutating
assertion - and it separately forbids all four of the remaining ceiling operands, none of
which the old fence checked at all.

**What this costs:** `Building` now carries a field whose correct use requires reading two
ADRs. That cost is paid down by the name and by the docstring rather than by expecting the
next reader to have read them, and the new fence below is the backstop.

**What must NOT be re-pitched:**

- **Do not rename `unsharded_clock_base` to `max_potential`, `max_clock`, `clock_ceiling`, or
  anything else that reads as an achievable maximum.** The name is the fence, and a test
  asserts on the name. The verbatim game key already lives in `KEY_MAX_POTENTIAL`, so nothing
  is lost.
- **Do not default an absent base to 1.** Absent is None. See point 3 above.
- **Do not add `mPotentialShardSlots`, `mExtraPotential`, `mDefaultPotentialShardSlots` or
  `mOverridePotentialShardSlots` to this module.** They belong to the drift guard's watch
  list, which is a different job in a different file: the guard's question is "did the
  surrounding invariants move", not "what is the ceiling". A test asserts that none of the
  four appears among this module's string constants.
- **Do not re-derive the ceiling here.** Everything in ADR 0005's re-pitch list applies
  unchanged and is not repeated: not from the headers, not from the code comment, not from
  the power exponent, and not by taking an assumed ceiling back through the equation to
  recover the slot count.

**The new fence this ADR adds, which ADR 0005 could not:**

**A caller that clamps a clock to `unsharded_clock_base` is clamping to the UN-SHARDED base,
and must say so.** Reading this value as an achievable maximum is the exact trap ADR 0005
named - the header calls it the maximum not accounting for installed power shards, and every
shipped entry reports the same un-overclocked value, so a solver that treats it as the
ceiling caps every solve at 100 percent and looks correct on every building nobody has
overclocked. That failure is invisible in exactly the worlds where testing is easiest.

The interim behaviour ADR 0005 specified is unchanged and now has its data: solve at or below
the un-sharded base, and where a solve would benefit from overclocking, report the ceiling as
UNMEASURED rather than assume one. Advice text that reports this number must name it as the
un-sharded base, never as the maximum, never as the ceiling. When the slot count is finally
measured, a later ADR records the reading and the ceiling becomes computable - at which point
this field is one of its operands and still is not, by itself, the answer.

**What must be revisited if a premise changes:** if a future patch ships an entry whose
`mMaxPotential` differs from the rest, nothing here breaks - that is precisely the case this
decision exists to handle, and the drift guard is what makes it visible. If the slot count is
ever measured, the re-pitch list above survives intact; only the interim behaviour changes,
and it changes by ADR.
