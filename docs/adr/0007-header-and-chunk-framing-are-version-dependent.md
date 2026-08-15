# 0007 - Save header and chunk framing are version dependent

## Status

`accepted` - 2026-08-14.

Written by the slice that took the measurement, and accepted by an adjudicator that did
not write it, per `docs/adr/0001`. Every claim was independently re-derived against all
14 local saves by a third read-only probe that reduced each string to a boolean or a
length before printing: the four version combinations, the string count per header
version by structural walk rather than by inspection, the positional labelling proof,
the 22-character identifier on 14 of 14, the 0-byte and 28-byte tails, and both chunk
framings confirmed by decompressing every chunk of every save to a clean end of file.
The undetermined key was re-tested formally - the framing is a function of the header
version, of the save version and of the build changelist alike, so no local file
separates them and the record stands as undetermined.

That adjudication returned NEEDS-REVISION rather than ACCEPT, and named four defects.
All four were applied by the merger at the adjudicator's direction before this status
was written, and the adjudicator's own text is used verbatim above: ADR 0003 and ledger
item CS-104 are now named as corrected rather than silently contradicted; the int8 after
the datetime ticks is recorded as unverified in MEANING rather than labelled "session
visibility"; Decision item 4 gained the render-site-only clause; and Decision item 6 is
restated as a commitment rather than as a description of code that does not yet exist.

Known limit of that acceptance: every measured save comes from one machine, one account
and one map, with an empty mod metadata field on all 14. The version triple is therefore
an unproven discriminator against a save from another platform or a modded save, which
would present a KNOWN triple with an unmeasured field shape and would not trip the
unknown-combination guard in Decision item 3..

Written by the slice that took the measurement. Per `docs/adr/0001` the author of a thing
does not grade it, so an adjudicator that did not write this flips the status.

---

## Context

Phase 4 is the save reader. Every phase-4 slice is written against the header layout and
the chunk framing recorded in `BOOTSTRAP.md` sections 2.4 and 3.1. Until this ADR, both
of those tables stated a layout **without a version qualifier** - a single header table
and a single chunk-framing sentence, presented as settled fact.

Both were wrong, in the specific way that is most expensive: they were correct for the
majority of the sample and silently incorrect for the rest.

**What was measured.** The operator's local library is 14 saves carrying four distinct
combinations of header version, save version and build changelist, spanning three header
versions. The measurement was taken twice - once by a planner against the live library,
then re-derived independently by a second probe that printed shapes only and no string
value. Both runs agree. `CLAUDE.md` section 8 governs: the probe beats the document.

**Finding 1 - the header string block varies in COUNT and in ORDER.** Header version 14
carries four length-prefixed strings before the fixed block; header versions 10 and 13
carry three, and the extra leading string is the one absent from the older layout. The
per-version tables live in `BOOTSTRAP.md` section 2.4, which owns those measurements.

The labelling was established **by property and never by value**: the map name is a fixed
game constant and the options string is a query string containing a distinctive separator,
so each field's position is identifiable without reading any operator-authored text. This
matters beyond method hygiene - see the PII mechanism below.

**This ADR corrects two earlier records, and NAMES them rather than editing them.**
`docs/adr/0003-s4-node-actors-in-save.md` is status `accepted` - binding, and citable
freely - and its Context item 1 states the unqualified framing verbatim, including the
compression-algorithm byte and the int64 body length. `docs/LEDGER.md` CS-104 records the
same claim. Both are corrected on that point by this ADR and on no other point. Per
`docs/adr/README.md` an accepted ADR's text is never edited and the ledger is append-only,
so the correction travels as a pointer: a reader who searches for the framing and lands on
0003 first - it is the entry carrying the hex constants - is routed forward to here. A
matching correction entry is recorded in `docs/LEDGER.md` against CS-104. Leaving the
refuted text holding the higher status was the defect this paragraph closes.

**Finding 2 - the chunk framing varies.** On header versions 13 and 14 the frame carries a
non-zero marker and an explicit compression-algorithm byte. On header version 10 the marker
is zero and **the compression-algorithm byte is absent entirely**, shifting the start of
the zlib stream by one byte. A parser built from the unqualified claim fails on 3 of 14
saves and looks correct on the other 11. Relatedly, "the decompressed body opens with an
int64 length" holds on the newer versions and does not hold on the oldest.

**What could NOT be determined, and why.** Whether the framing variant keys on the HEADER
version or on the SAVE version is **undetermined**. The two fields covary across the entire
local library - each header version appears with exactly one set of save versions and never
crosses over - so **no file available locally can separate them.** No amount of further
work on the existing corpus resolves this; it needs a save that breaks the covariance, and
none exists here.

Alternatives considered:

- **Pick the likelier key and move on.** Rejected. The two hypotheses make identical
  predictions on every local file, so choosing one buys no verification and converts an
  honest unknown into a fact the next reader will trust. The failure would surface on a
  file this project has never seen, far from the decision that caused it.
- **Leave the tables unqualified and handle versions in code only.** Rejected. The tables
  are what the phase-4 slices are written against; a spec that says one layout produces
  parsers that assume one layout.
- **Support only the newest header version.** Rejected. The operator's own library is
  majority older saves, and the progression corpus that validates the reader is built from
  exactly those files.

### The PII mechanism - why this matters beyond parsing

This is the load-bearing consequence and the reason the ADR exists at all.

**A redactor that targets a NAMED FIELD is defeated by a version-dependent field ORDER.**

On header versions 10 and 13 the third string is the **session name** - the operator-chosen
world name. On header version 14 the third string is the **options string**. A parser that
labels "the third string" as options, and redacts by that label, renders a world name in
clear text. Non-negotiables 3, 11 and 12 all land on that single off-by-one.

This is not hypothetical. It was demonstrated live during the session that produced this
measurement: a probe printed one such value into an agent transcript. The mechanism is
already proven; the only question is whether the design prevents a recurrence.

---

## Decision

**Neither the save header layout nor the chunk framing has a single fixed shape. Both are
version dispatched from day one, and the version-dependent field order is treated as a
privacy hazard rather than merely a parsing detail.**

Specifically:

1. `BOOTSTRAP.md` sections 2.4 and 3.1 carry **version-qualified** tables. They own those
   measurements; no other file restates them.
2. The chunk-framing variant is **detected from the marker word**, which is directly
   observable in the bytes, and cross-checked against both version fields. Detection does
   not depend on resolving the undetermined key.
3. The header-versus-save-version key stays **recorded as undetermined** until a file that
   separates them exists. A parser that meets a combination outside the measured set flags
   it as unknown content and skips, per non-negotiable 7 - it never guesses a layout.
   There are **three** unrefuted candidate keys, not two: the build changelist predicts the
   framing on this corpus exactly as well as the two version fields do. Naming only two
   would understate the ambiguity. The remedy in item 2 is immune to which one is right,
   which is precisely why it is the remedy.
4. **The header parser redacts EVERY header string by default**, positionally, without
   reference to what any field is called. The PII-bearing strings are **not fields on the
   default returned type at all**, so rendering one requires deliberately reaching for an
   opt-in path rather than merely forgetting to redact.
   **The opt-in path is render-site only: never stored, never logged, never placed in
   exception context, and never held on a long-lived object.** This clause is load-bearing
   and is not defensive verbosity. `clockspeed.data.locate.redact()` strips the home path,
   the account name, the account directory and the save filename - it holds **no needle for
   a session name read out of a header**, because that string is not knowable in advance.
   So the one sanctioned way to obtain the value returns a string the project's own
   redactor cannot neutralize. Without this clause the friction in the sentence above is
   defeated by the first debugging session.
   Note also what item 4 does NOT cover: an ad hoc probe reading header bytes directly never
   touches the returned type. The leak that produced this ADR was exactly that - a probe,
   not the parser - so the type-level design would not by itself have prevented the incident
   it cites as its own proof. Probes carry the same obligation and nothing enforces it for
   them.
5. The 28-byte header tail on versions 13 and 14 is skipped **by length**. Its internal
   structure is unverified and no field breakdown is invented for it.
   The same restraint applies one field earlier, and it was nearly missed: the int8 between
   the datetime ticks and the editor object version is **measured in POSITION and unverified
   in MEANING**. Its position is proven by the editor object version reading 40 on all 14
   saves immediately after it. Its value is `0x00` on header versions 10 and 13 and on
   header 14 save 60, and one of `0x10`, `0x50`, `0x90` or `0xD0` on the eight header-14
   save-52 saves. It is therefore NOT a 0/1 flag, and a parser treating it as one is wrong
   on 8 of 14 saves. `BOOTSTRAP.md` section 2.4 records it as unverified for that reason.
6. `clockspeed/save/workdir.py` **will be** the only module in the save package with a
   write, so that "no other save module writes" becomes a static, machine-checkable
   assertion. This item is a COMMITMENT, not a description: at the time this ADR was
   written `clockspeed/save/` held only `__init__.py`, neither `workdir.py` nor `header.py`
   existed, and no check enforced the property. The phase-4 gate is what converts it from
   an intention into an assertion, and until that gate exists this item states an intent
   that a later reader must not mistake for shipped code.

**Do not re-pitch:**

- **A single fixed header layout.** Tried in session 1, recorded as fact, and disproved by
  re-probe. It fails on the operator's own oldest saves.
- **A single fixed chunk framing.** Same failure, worse shape: it fails on 3 of 14 saves
  while appearing correct on the other 11.
- **Resolving the header-versus-save-version key by choosing the more likely one.** No
  local file can separate them. Detect from the marker and cross-check. A confident answer
  here is a guess wearing a fact's clothing.
- **Redacting the header by field name.** That is precisely the defeated design: the name
  is stable and the position is not.

---

## Consequences

**What this buys:**

- The phase-4 parser is correct on the whole local library rather than on the newest
  majority of it, and the progression corpus stays usable as regression input.
- The privacy guarantee stops depending on a correct field labelling. Positional redaction
  plus absent-by-default fields means a labelling bug becomes a parsing bug, not a leak.
- An unknown version combination degrades to a flag-and-skip instead of a plausible-looking
  wrong parse.

**What this costs, stated plainly:**

- Version dispatch is structural in the save reader from the first commit, and every new
  field measured has to be measured per version rather than once.
- The undetermined key stays an open thread indefinitely. That is uncomfortable and it is
  the honest state; a resolved-looking answer would be worse than an open one.
- Opt-in rendering of the PII strings is deliberately awkward to reach. That friction is
  the feature, and it will occasionally be inconvenient during debugging.

**What must be revisited if a premise changes:** if a save ever appears whose header and
save versions break the current covariance, the undetermined key becomes answerable -
record the answer in a superseding ADR rather than editing this one. If the game ships a
header version beyond those measured, the tables in `BOOTSTRAP.md` section 2.4 are extended
by measurement, never by extrapolation from the newest known layout.
