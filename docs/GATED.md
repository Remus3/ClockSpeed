# Clockspeed - Gated items

**Section status: LIVE.** A dated heading in this file records provenance - when the
text was filed, moved or measured - and never that the section itself is historical.

**Owner file for:** work items blocked on something OUTSIDE the repo.

One line per item, plus the exact external condition that unblocks it. An item that is
merely unstarted is not gated - that is `ROADMAP.md`. An item that is merely wished for
is not gated - that is `BACKLOG.md`. **Gated means: no amount of work inside this repo
can close it.**

Gated IDs use the `CS-G` series. They are permanent and never reused. When a gated item
unblocks, it moves to `ROADMAP.md` under its own `CS-G` ID and closes into
`docs/LEDGER.md` under the same ID.

**NAMING A LIVE ROADMAP ID ANYWHERE IN THIS FILE PUTS THAT ROW INTO A POPULATION THE
BLOCK BELOW MUST CLASSIFY.** `ops/loop/scope.py`'s `gate_classification` still scans this
whole file for every `CS-` id, wherever it appears, and **that wide scan is not the thing
to weaken** - a real gate names its blocked row in PROSE rather than in any structural
field, CS-G06 below is the live proof, and a fence reading only headings or a declared
field would fail open on exactly the rows the fence exists for. What changed is what the
scan ANSWERS. The scan is the POPULATION; the classification block below is the
CLASSIFIER; and every id the scan finds is declared either **BLOCKED** - a gate here
genuinely blocks that row - or **MENTIONED** - this file merely talks about it. **An id
the scan finds that the block does not classify is treated as GATED and is reported by
name. Omission fails CLOSED.**

**WHY THE PARTITION EXISTS, MEASURED RATHER THAN ARGUED.** Under the bare scan, FOURTEEN
live `ROADMAP.md` rows were fenced by mention alone and an adjudicator graded THIRTEEN of
them accidental. The sharpest was a deadlock: the row whose entire job is to empty CS-G05
out of this file was fenced BY this file, so the headless lane could never execute the
repair. Four more were fenced by a sentence whose own opening clause reads "What remains
open here is narrower and is filed separately", and one by a heading reading "WHY IT IS NO
LONGER GATED, BY THIS FILE'S OWN DEFINITION".

**DESCRIBE-NEVER-NUMBER IS NO LONGER THE UNFENCING MECHANISM, and that is a fence rather
than a loss of convenience.** Before the classifier, the only way to unfence a row this
file discussed was to stop spelling its number, and one commit did exactly that to four
rows. **That move is a FAIL-OPEN LEVER:** the same edit applied to a row a gate GENUINELY
blocks unfences it, and no guard can tell the two apart afterwards, because the evidence
has been deleted. Under the partition, a row this file merely discusses is unfenced by a
`MENTIONED` line and may be spelled by number freely; **a row a gate genuinely blocks is
unfenced ONLY by deleting its `BLOCKED` line**, which is an edit somebody has to make on
purpose and which this block records. Describing rather than numbering remains good prose
for a mention. It is no longer evidence of anything, and it must never again be cited as
an unfencing.

### The classification block - the classifier, read by `ops/loop/scope.py`

Every id the wide scan finds appears here exactly once. `BLOCKED` carries the `CS-G` gate
that blocks the row; `MENTIONED` carries no second field. **The two sentinel lines are what
delimit the classifier** - a `CS-` id spelled anywhere else in this file classifies
nothing, so quoting the mechanism inside the file it governs cannot switch it off. An id
appearing twice, or twice with different verdicts, is UNCLASSIFIED rather than resolved:
a partition is not a vote, and resolving a disagreement either way would let a `BLOCKED`
row be unfenced by appending a `MENTIONED` line under it.

`CS-8` and `CS-9` are not item ids. They are what the scan's own `CS-[0-9]+` pattern reads
out of the `CS-8nn` and `CS-9nn` block names in the prose below. They are classified here
rather than argued away, because the population is whatever the scan LITERALLY finds and
an exception carved for a cosmetic case is the first hole in an allowlist.

CS-1157 is MENTIONED for a reason worth stating, because it is the first id here that
names a MECHANISM rather than a number in prose. Clause 3 of CS-G03 cites the frozen-file
grant that set the two attribution keys, and that grant's id is CS-1157 - a CLOSED item,
recorded in `docs/LEDGER.md`, blocked by nothing. Dropping the id to keep the scan quiet
would have cost the traceability the citation exists for, and narrowing the scan is the
repair this file's own guard forbids.

CS-700 is MENTIONED because the two notes filed 2026-09-24 at the end of CS-G03 cite it
as the plan the flip runs, and the dependency runs the other way: CS-G03 waits on
CS-700, not CS-700 on a gate here. Its irreversible steps S9 and S12 are held by the
operator confirmation those notes require be typed into the main session,
not by a fence in this file, and MENTIONED leaves the lane's scope exactly as it was
before the notes named the id.

The four rows carried at the end of the block are MENTIONED here **on purpose and with
nothing else riding on it**. They are the four that commit `7fbe529` unfenced by deleting
their numbers from gate prose; naming and classifying them pins that decision in a form a
later session can read, instead of leaving it resting on the absence of a sentence.

```
CLOCKSPEED-GATE-CLASSIFICATION BEGIN
gate: CS-913 BLOCKED CS-G06
gate: CS-8 MENTIONED
gate: CS-9 MENTIONED
gate: CS-300 MENTIONED
gate: CS-413 MENTIONED
gate: CS-501 MENTIONED
gate: CS-700 MENTIONED
gate: CS-702 MENTIONED
gate: CS-703 MENTIONED
gate: CS-813 MENTIONED
gate: CS-815 MENTIONED
gate: CS-817 MENTIONED
gate: CS-821 MENTIONED
gate: CS-828 MENTIONED
gate: CS-829 MENTIONED
gate: CS-830 MENTIONED
gate: CS-831 MENTIONED
gate: CS-832 MENTIONED
gate: CS-847 MENTIONED
gate: CS-850 MENTIONED
gate: CS-867 MENTIONED
gate: CS-938 MENTIONED
gate: CS-981 MENTIONED
gate: CS-982 MENTIONED
gate: CS-983 MENTIONED
gate: CS-1040 MENTIONED
gate: CS-1044 MENTIONED
gate: CS-1047 MENTIONED
gate: CS-1048 MENTIONED
gate: CS-1157 MENTIONED
gate: CS-1186 MENTIONED
gate: CS-1187 MENTIONED
gate: CS-1272 MENTIONED
gate: CS-1274 MENTIONED
gate: CS-1275 MENTIONED
gate: CS-1279 MENTIONED
CLOCKSPEED-GATE-CLASSIFICATION END
```

---

## The rule that protects this file

**Gated items are NEVER closed synthetically.**

Substituting a proxy for the external condition and declaring the item done is **the
single most common way a gated backlog gets falsely drained**. It is attractive precisely
because it feels like progress: the proxy is buildable, the tests go green, and the line
moves out of this file. What actually happened is that the real condition is still unmet
and the project has lost its own record of that fact.

Concrete shapes this takes, all of which are the same failure:

- Clearing a license gate with a verbal opinion instead of a written verdict.
- Declaring an external-dependency item done because a stub or a mock of it works.
- Marking a data item complete against hand-entered data standing in for the real source.
- Treating "we decided we probably do not need it" as the condition being met. That is a
  scope change, and it closes as a scope change with its own record - not as a gate
  clearing.

**Every gated item splits into two halves:**

| Half | Definition | Availability |
|---|---|---|
| **DRAIN** | The part that genuinely requires the external condition. | Blocked. Untouchable until the condition is met. |
| **PREP** | The harness, the interface, the assertions, the fixtures, the failing tests that will grade the DRAIN half when it arrives. | **Always workable, right now.** |

Work the PREP half freely and record PREP progress in `docs/LEDGER.md` under the same ID,
stating explicitly that the DRAIN half remains gated. PREP being finished never closes
the item.

---

## Open gated items

### CS-G06 - A mature-world snapshot with a repeatable home

**One line:** CS-913 cannot be validated without a save that demonstrably carries unlock
state, kept somewhere a later run can reproduce.

**Unblocked by:** a snapshot of a progressed world in `corpus/` that the tree can tell apart
from the pinned development world BY ITS WORLD TOKEN - either an operator-recorded pin of the
development world's token, held masked, which the corpus save's token differs from, or a corpus
save whose world token differs from every world in the live save library. **A save in `corpus/`
is not enough on its own, and reading it so is MEASURED FALSE** (`docs/LEDGER.md`, the
2026-09-15 CS-G06 record): since the CS-G05 repair every world in the library decodes non-empty
unlock state, so non-emptiness tells no world apart, and the save placed there is
byte-identical to one still in the live save directory. `.gitignore` reserves `/corpus/`, and
ADR 0004 recommended the snapshot. **No amount of work inside this repo can
close it** - a save is a personal-data-bearing artifact under non-negotiables 11 and 12,
it may never be committed, and an agent may not place one.

**Why a synthetic fixture is not a substitute, and this entry refuses that trade.** The
settled rule is that fixtures are small synthetic registries hand-authored in the repo,
and CS-913's arms must indeed run on a machine with no game installed - that is what a
synthetic `PropertyMap` is for. But a synthetic fixture built parallel to the reader
stays green through the real defect, which is the failure ADR 0004 names in its own
consequences. The corpus is what tells us the reader agrees with a real save, once.

**The pinned development world cannot serve.** ADR 0004 states S6 must not be settled on
it, and a 2026-09-05 spike measured worse: every record of every `(14,60)` save decodes
ZERO property tags, so it cannot exercise the decoder at all. It is the CONTROL. This is
adjacent to CS-G05 and does not supersede it.

**Filed 2026-09-05** out of the CS-913 re-spec recorded in `docs/LEDGER.md`.
The unblocking condition was reworded 2026-10-20 (session 150) to the world-token test the
2026-09-15 CS-G06 record names.

### CS-G01 - Asset-parsing library for resource-node extraction

**One line:** Extract resource-node coordinates and purity from the shipped game assets,
as the fallback path when the save does not carry node actors.

**Unblocked by, ALL of the following:**

1. Spike S4 **failing** - that is, the save proving not to carry resource-node actors
   with usable transforms. **If S4 succeeds, this item is VOID, not done.** It closes as
   "no longer required", with the S4 result cited.
2. The third-party asset-parsing library clearing the license gate, with a **written
   verdict** recorded in `docs/LEDGER.md` and as an ADR. Verbal clearance is not written
   clearance, and the absence of a LICENSE file is not permission. Copyleft stays
   do-not-vendor regardless of who says otherwise.

**Note on ordering:** spike S8 runs before S4. If node data turns out to be
seed-dependent, the static-asset path is invalid for a given world regardless of the
license outcome, and this item collapses - the save becomes the only correct source and
S4 becomes load-bearing rather than merely important.

**PREP half, workable now:** the node-data interface that both the save path and the
asset path must satisfy, the fixtures, and the tests that grade either implementation.

**Do not** substitute a community-compiled node dataset. It carries provenance risk that
a later public flip makes worse, and it is not this item.

**STATUS 2026-08-22 (session 28): CONDITION 1 ABOVE IS MEASURED STALE, AND READ LITERALLY IT
WOULD VOID AN ITEM THAT ADR 0003 MAKES LOAD-BEARING. DO NOT CLOSE THIS ITEM ON IT.**

Condition 1 unblocks this item on spike S4 **failing**, and rules that if S4 succeeds the item
is VOID. **S4 SUCCEEDED, and `docs/adr/0003-s4-node-actors-in-save.md` has been `accepted`
since 2026-08-13 recording it - but S4 SPLIT, and condition 1 is written as though it could
not.** That ADR's decision line is "Geometry: yes. Semantics: no". Measured there: 626 node
actors, 626 of 626 carrying a valid transform; and `mPurity`, `mResourceNodeType`,
`mResourceClass`, `EResourcePurity` and `mExtractResourceNode` occurring ZERO times in any save
examined, across three worlds and four game builds. The mechanism is recorded and it is
ordinary Unreal behaviour: a save stores deltas from level defaults, and a node's resource type
and purity are level defaults that never change, so they are never written to the save at all.

**THE TWO HALVES OF THIS ITEM'S ONE-LINE THEREFORE MOVED IN OPPOSITE DIRECTIONS.** The
COORDINATES half is genuinely superseded - the save carries placement, so the asset path is no
longer needed as a fallback for it. The PURITY half is not merely still open: it is now
LOAD-BEARING rather than a fallback, because the save is measured not to carry it at all.
**ADR 0003 ALREADY DRAWS EXACTLY THIS CONCLUSION IN ITS OWN CONSEQUENCES AND POINTS AT THIS
FILE** - the node semantics layer needs the asset-extraction path, and the licence gate "is now
a real, scheduled obligation rather than a contingency".

**WHAT IS ACTUALLY BLOCKING IS CONDITION 2, WHICH IS UNMET AND UNSTARTED.** No candidate
library has been triaged and no written verdict exists; `docs/LEDGER.md` carries ZERO records
citing this item, at any date.

**THE REPAIR IS TO RESTATE CONDITION 1, NOT TO ACT ON IT.** Rewrite it to ask the question S4
actually answered - per HALF rather than per spike - and record the coordinates half as
superseded with the ADR cited. Until that happens, treat the VOID clause as stale text.
**NOTE THAT THIS FILE'S OWN RULE AGAINST SYNTHETIC CLOSURE COVERS THIS DIRECTION TOO:** voiding
an item because a condition sentence reads that way, when the ADR that sentence defers to says
the opposite, drains the backlog exactly as falsely as substituting a proxy would. Nothing
outside the repo changed here - what changed is that the condition was never re-read against
the ADR that answered it.

**STATUS, measured 2026-09-13 (session 85): CONDITION 1 IS NOW RESOLVED ON BOTH HALVES, AND
A DIFFERENT EXTERNAL BLOCK HAS TAKEN ITS PLACE. THE ID IS NOT QUIETLY REPURPOSED** - the
original purpose and the replacement are recorded separately below, because an item whose
block silently changes underneath its one-line is an item nobody can audit.

**HALF ONE - COORDINATES. VOID, as condition 1 always said it would be.** Re-measured this
session against the live save: 1065 resource-node actors, every one carrying exact
coordinates. The save IS the source. The asset path is not needed as a fallback for
coordinates and that half of this item's one-line is superseded, with ADR 0003 and this
measurement cited. That is a condition RESOLVING, not a gate clearing.

**HALF TWO - PURITY. THE QUESTION IS CLOSED, AND NOT THE WAY THIS ITEM EXPECTED.** The
2026-08-22 block above made the purity half LOAD-BEARING on the strength of a
zero-occurrence sampling measurement. It is now closed BY DECLARATION, which is a stronger
result: the install ships `CommunityResources/Headers.zip` beside the `Docs` file this
project already reads, and `FGResourceNode.h` declares `mPurity` with NO `SaveGame`
specifier. A property without `SaveGame` is structurally incapable of being serialized into
a save ON ANY BUILD. `mResourceClass` and `mResourceNodeType` are the same. **Purity is not
in any save and no future session should re-derive that.** The reasoning is recorded in
`docs/adr/0019-the-map-underlay-and-the-purity-declaration.md`, and the roadmap row that
builds a `SaveGame`-specifier index over those shipped headers answers questions of this
shape once and for all.

**WHAT THIS DOES NOT DO.** It does not make purity obtainable. The shipped assets remain the
only conceivable source, and reaching them is what the NEW block below prevents. The honest
substitute shipping in the meantime - an operator annotation whose published provenance
reads operator and never measured, carried by the roadmap row that owns the map underlay
and the purity annotation - is a SCOPE CHANGE recorded as one. **It is not
this gate clearing, and it must never be written up as one.** This file's rule against
synthetic closure covers exactly that move.

**THE NEW BLOCK, STATED PLAINLY RATHER THAN INHERITED: OODLE DATA.** Measured 2026-09-13,
read-only against the install. The pak index is unencrypted and all 13576 entries parse in
pure stdlib - but 6993 of them, `DefaultGame.ini` included, are Oodle-compressed, and the
install ships NO callable `oo2core`. What it does ship is `OodleNetwork`, which is a
DIFFERENT codec and decodes none of it. Oodle Data is proprietary RAD/Epic software.

**THE REVISED UNBLOCKING CONDITION, which supersedes the wording of conditions 1 and 2 above
without deleting them:**

1. RESOLVED, on both halves, as recorded in this block. Nothing further is owed against it.
2. **A WRITTEN `CONVENTIONS.md` section 14 licence verdict on an Oodle Data decoder**, one
   that reads the LICENSE text, the copyright line AND the provenance claim, and is recorded
   in `docs/LEDGER.md` and as an ADR. **Verbal clearance is not written clearance. The
   absence of a LICENSE file is not permission.** Copyleft stays do-not-vendor regardless of
   who says otherwise. Until that verdict exists, EVERY pak-asset extraction is gated here
   and none of it goes to `ROADMAP.md`.

**WHAT IS NOT GATED BY THIS, so the gate does not grow by accident.** `Headers.zip` is an
ordinary zip of text sitting beside a file this project already reads; nothing in it touches
a pak, so the Oodle Data gate does not reach it and the header-index row is an ordinary
roadmap item.

**AND THE GATE WOULD NOT YIELD THE MAP TRANSFORM EVEN IF IT CLEARED.** Read directly from
the shipped headers: `mUpperLeftWorld` and `mWorldToMapScale` carry NO `UPROPERTY` macro at
all, and the declaring class overrides neither `Serialize` nor `PostLoad`. A member with no
`UPROPERTY` is not written into the cooked asset either, so no pak extraction reaches it
and no Oodle verdict changes that. This is strictly stronger than "they live behind Oodle":
the fit-and-prove derivation is not the preferred path for the map transform, it is the
ONLY path.

**PREP half, workable now, unchanged in spirit:** the node-data interface both paths must
satisfy, the fixtures, and the declared availability flags every consumer already reads.

### CS-G07 - Usable water region geometry for extractor siting

**One line:** the map is required to draw outlined and tinted usable water regions for water
extractors, and the geometry that defines them is level geometry inside the paks.

**Unblocked by:** the SAME written `CONVENTIONS.md` section 14 verdict on Oodle Data
recorded under CS-G01 above. No amount of work inside this repo reaches it.

**Measured 2026-09-13.** `FGWaterVolume` declares `mCanPlaceExtractor` - exactly the flag
the requirement wants - but it is `EditDefaultsOnly` level geometry.

**RE-MEASURED AGAINST THE SHIPPED HEADERS: THE SAVE IS NOT SILENT, IT IS EMPTY, AND THE
DIFFERENCE MATTERS.** It holds three object references to ONE named level actor,
`FGWaterVolume30_0`, and they carry no geometry. `FGWaterVolume` declares ZERO `SaveGame`
properties, so no build of it ever serializes one. A reference to a volume is not the
volume, and a later session reading "zero water-volume type paths" would go looking for
paths that are in fact there and conclude the earlier measurement was wrong. The save
still cannot answer this question.

**THE THREE-PUMP PARTIAL WAS CONSIDERED AND IS REJECTED BY NAME, so nobody re-proposes it.**
The only water points the save confirms are the three built pumps, through each one's own
extractable-resource reference. Shipping those three as "water coverage" would imply that
every unmarked water body is unusable - silently wrong rather than flagged, which is the
non-negotiable 7 trap precisely. **Ship `water_regions_available: false` and draw nothing**,
as the map-model row already specifies, until the verdict lands.

**PREP half, workable now:** the availability flag, and the panel rendering that says
UNAVAILABLE rather than drawing an empty map and letting a reader infer no water. The
roadmap row that models the map's categories, extents and elevation order carries the
flag; the row that renders the map panel carries the UNAVAILABLE rendering. Both are
workable today and neither is named here by number, for the reason this file's header
gives.

### CS-G02 - External LP/ILP optimizer dependency

**One line:** Add an external linear or integer programming backend behind
`OptimizerBackend`.

**Unblocked by, BOTH of the following:**

1. The candidate library clearing the license gate with a written verdict recorded in
   `docs/LEDGER.md` and as an ADR.
2. **Phase 3 completing first, dependency-free, behind the `OptimizerBackend`
   interface.** The interface must exist and must be proven by a working in-repo backend
   before any external solver is considered. The external backend must then slot in
   without changing a single caller.

**PREP half, workable now:** the interface itself, the in-repo branch-and-bound or
weighted-greedy backend, and the degenerate-case test that asserts two backends produce
identical results.

**PREP half COMPLETE 2026-08-14 under CS-300. The DRAIN half remains GATED.** Condition 2
above is now satisfied: `clockspeed/solve/optimize.py` owns `OptimizerBackend`, and
`clockspeed/solve/backends/` holds TWO in-repo implementations with genuinely different
mechanisms - complete lattice enumeration, and a reachability least fixed point that prunes
on feasibility before scoring. Both are reached only through `select_backend`, and an
unknown backend name refuses at every precedence level rather than falling back, which is
what makes "swappable" testable at all. Verification is in the CS-300 ledger entry.
Condition 1 - a written license verdict for a candidate library, recorded here and as an
ADR - is UNMET and no candidate has been triaged. This item does not close, and completing
the PREP half never closes it. The external backend must still slot in without changing a
single caller.

The public visibility flip gate, CS-G03, CLEARED at T2 and has left this file: its section is in `docs/history_notes.md` and its closing record in `docs/LEDGER.md`, both under CS-G03.

### CS-G04 - Dedicated-server data lane

**One line:** Read world state from the dedicated server API instead of, or in addition
to, a single-player save.

**Unblocked by:** the operator actually running a dedicated server. Not by the API
documentation being on disk - it already is, it is free to read, and it is not the
condition.

**PREP half, workable now:** nothing beyond reading the local API documentation for
reference. Do not build a lane for a server that does not exist.

### CS-G05 - Save version 60's property payload grammar is under-sampled

**One line:** Measure the property tag grammar inside a save version 60 payload, which the
grammar measured on the other three version pairs does not accept.

**Unblocked by:** the local library gaining a save of that pair that is STRUCTURALLY
DIFFERENT from the two already present. Playing the pinned development world forward and
saving on the current game build is the only thing that produces one.

**STATUS 2026-09-12 (session 86): CS-829 IS ROUTED OUT OF THIS FILE. CS-830 AND CS-831 WERE
NEVER IN IT. THE ROUTING THE BLOCK BELOW DECLINED TO IMPROVISE IS NOW TAKEN, AND NOTHING
HERE CLOSES ANYTHING.** The block below says in terms that it "does not by itself relocate
this item, close CS-829, or write an acceptance clause for either", and that routing is "a
decomposition question that was deliberately NOT improvised inside this status block".
CS-981 in `ROADMAP.md` is that decomposition question. This block is its answer for the
parts that live in this file.

**CS-829 IS RELOCATED, NOT CLOSED AND NOT NARROWED.** Its section is gone from this file and
its body - every fence, verbatim - now sits in `docs/item_notes/phase4-followups.md` under
CS-829, which is the leaf the leaf membership rule in `docs/item_notes.md` names for a Phase 4 item
in the `CS-8nn` block below CS-850. Its item LINE is back in `ROADMAP.md` under Phase 4
carrying the acceptance clause it held before it was gated, WORD FOR WORD. **The clause was
not rewritten and the population was not narrowed**, because CS-829's own fences say a
restated clause is a scope change that closes as one and is not the gate clearing. Whether
that clause is satisfiable AS WRITTEN is a MEASUREMENT, not a routing decision, and nothing
here takes it.

**WHY IT IS NO LONGER GATED, BY THIS FILE'S OWN DEFINITION.** CS-829's stated unblocking
condition was "CS-G05 clearing". The block below records that gate as discharged. A
condition that no longer holds is not a gate, and the rule at the top of this file says an
item that is merely unstarted is not gated - that is `ROADMAP.md`.

**NEITHER CS-830 NOR CS-831 WAS EVER FILED HERE, AND NEITHER IS OPEN WORK AT
ALL.** CS-981's acceptance named three items as gated behind this one. One of them was. Both of the others
are CLOSED and their records are in `docs/LEDGER.md` - CS-830 as a NARROWED close taken
after an adversary refuted the first one, CS-831 with an acceptance the operator AMENDED the
same day. Neither carries an open line in `ROADMAP.md` and neither has ever had a section in
this file. The correction is recorded in CS-981's line and in its section under
`docs/item_notes/phase4-followups-960.md`, the upper leaf of the `CS-9nn` block after the
split.

**WHAT REMAINS OF CS-G05 ITSELF.** The block below assigns every measured residue to an item
that is not this one: the unmeasured tag types and the extent disagreements to CS-828 and
CS-832, the struct interiors to CS-829, and the weakest flags bit is CS-982. What is left
over and owned by nothing is ONE thing - the PREP harness
`tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept` is
now vacuous, its green is not evidence, and the block below says correcting it is a separate
slice. That is work entirely inside this repository. **By this file's own definition - gated
means no amount of work inside this repo can close it - CS-G05 IS NOT GATED, AND THE
DECISION TAKEN HERE IS THAT IT ROUTES OUT.**

**THE DECISION IS TAKEN; ITS EXECUTION IS NOT COMPLETE, AND SAYING SO IS THE POINT OF THIS
PARAGRAPH.** Routing CS-G05 out means a `ROADMAP.md` line under its own `CS-G` ID - the
route this file's header prescribes - plus its body relocated into the leaf the routing
table names. That leaf is `docs/item_notes/phase4.md`: CS-G05 is a Phase 4 item whose ID
falls outside both the `CS-8nn` and the `CS-9nn` blocks, on the same footing as CS-501.
**That file was outside the write-list of the slice that took this decision**, and writing a
body into a file a slice may not open - or deleting the body instead of moving it - are both
worse than saying plainly that the move is owed. So CS-G05's section STAYS IN THIS FILE
until its body lands in that leaf, and it stays as a DECIDED-OUT item rather than as a gate.
**THE MOVE IS OWNED BY CS-983 IN `ROADMAP.md`, FILED 2026-09-12 BY THIS SESSION'S MERGER AFTER
AN ADVERSARY REFUTED THE HALF-MOVE.** Its finding stands and is recorded rather than argued
away: a section declaring that it does not meet this file's own membership rule, while
staying in this file, is incoherent under that rule. It is a TRANSITIONAL state with a named
owner and an acceptance clause, which is what this project does with every other state it
cannot finish in one slice - it is not a licence to leave it here indefinitely.
**DO NOT re-decide this, and DO NOT close CS-G05 as part of executing it.** The move is a
relocation and every status block below travels with it, verbatim.

**THE HAZARD THE MOVE MUST NOT OUTRUN.** `docs/item_notes/phase4-followups.md` under CS-847
records two live sites in `clockspeed/save/objects.py` that hand off to `CS-G05` in prose,
and says they are harmless only while CS-G05 stays GATED - if it CLOSED with those sentences
standing, the module would stay green. Routing CS-G05 OUT does not close it, so the hazard
does not fire here. It fires on a CLOSE, and CS-847 is the item that owns fixing it.
**STATUS 2026-09-11 (session 61): THE PREMISE OF THIS ENTRY IS REFUTED. THE (14,60) ZERO WAS
A DEFECT IN THIS REPOSITORY'S READER, NOT A PROPERTY OF THE SAVE FORMAT. IT IS FIXED, AND
THE PROPERTY PAYLOAD NOW READS ON EVERY RECORD OF THE PINNED DEVELOPMENT WORLD.** Ground
truth beats every document including this one - `CLAUDE.md` section 8 - and the ground truth
is the operator's: a third-party interactive map renders container contents and machine
settings out of THE SAME FILE on THIS machine. The data is therefore present and decodable,
so every sentence below that reads "zero payloads reach a terminator" as a fact about the
PAIR, and the CONTROL framing that followed from it, was a fact about
`clockspeed/save/objects.py` instead. Nothing below is deleted: the reasoning is a record of
how a reader defect was carried for eight sessions as a format property, which is worth more
kept than tidied away.

**THE TWO OFFSETS THAT LOCALISED IT, read out of the bytes by hand rather than hypothesised.**

- **ONE OPAQUE BYTE stands between a payload's head and its first tag.** On an actor that is
  just past the component list; on a component it is the payload's first byte. The walk
  landed exactly one byte short of the first tag name and read that byte as the top of a
  length prefix. This is the "single leading byte" the blocks below say "accounts for 669 of
  1832 and nothing like all of it" - the arithmetic was right and the conclusion drawn from
  it was wrong. It is the first half of one grammar, not a rival explanation.
- **THE TAG SPELLS ITS TYPE AS A RECURSIVE NAME** - a word, an int32 parameter count, then
  that many nested names - rather than as a type word followed by per-type extra strings.
  There is no index field, and the tag closes with a FLAGS BYTE rather than a guid-present
  flag. A container's element words are the top-level parameters of that name. Stepping the
  lead byte ALONE gets 3215 of 3918 payloads of the current world to a terminator with ZERO
  container values; the 703 that still break are the ones whose flags byte the old
  guid-flag reading refuses. Neither half is a fix on its own.

**THE FLAGS BYTE'S BITS ARE MEASURED ONE AT A TIME AND THE UNSEEN ONES ARE REFUSED.** Over
9058 tags the byte takes four values: 0x00 on 6123, 0x08 on 757, 0x09 on 2 and 0x10 on 176.
0x08 rides only on the four container-and-struct words and adds no bytes; 0x10 rides only on
`BoolProperty` and IS its true value; 0x01 adds an int32, and that is the weakest reading in
the repair - it rests on TWO tags, and what makes it more than a coincidence is that
dropping the four bytes costs a whole record. **0x02 reads like a property guid and appears
on NOT ONE TAG**, so the width of whatever follows it is unknown and a payload carrying any
unobserved bit is FLAGGED rather than stepped over (non-negotiable 7).

**WHAT THE REPAIR IS MEASURED AT, from a read-only probe reporting no path, no name, no
string and no value.** All 3918 walked records of the pinned development world now decode
their payload and 0 remain flagged unparsed, against 3918 of 3918 flagged before. 189
distinct property names are published. 641 container values decode, and their element total
is dominated by ONE `ByteProperty` array of 2^20 elements bounded by uniform width - the
other 640 close on their own element grammar, so the aggregate is a byte blob plus 3097
elements and not a million decoded items. 1970 object references and 1365 integers decode.

**WHAT IS STILL OPEN, AND IT IS NOT THIS GATE.** 1530 tags are of types this project has not
measured and 803 values disagree with their declared extent - both were INVISIBLE on this
pair while nothing read at all, and both belong to the existing items that own them
(`CS-828`, `CS-832`). **ZERO struct interiors decode on this pair**, because the repair
deliberately did not carry the new grammar into the struct-interior reader: a struct's word
is a parameter of the type name here, and CS-829 is the item that owns reading it. That is a
narrower CS-829 than the one filed below, not a wider one.

**THE `#### The (14,60) wall` SUB-BLOCK BELOW ASKS FRAMING OR VALUE GRAMMAR. THE ANSWER IS
BOTH, AND ITS NAMED SUSPECT IS CLEARED.** The 22 opaque bytes inside the package summary are
NOT the discriminator and nothing needed to read a UE5 file version: the version PAIR this
reader already dispatches on was sufficient. The sub-block's own warning held - the
resemblance it found was not the finding.

**THE PREP HARNESS IS NOW VACUOUS AND ITS GREEN IS NOT EVIDENCE.**
`tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept`
still passes, and it passes because its sweep carries its own independent reader of the
LEGACY tag grammar. Its zero is therefore a true statement about that grammar and a FALSE
statement about the save, which its own docstring now asserts ("save 60 reaches a terminator
on no payload at all"). **Correcting it is a separate slice** - that file was outside the
write-list of the slice that made this measurement, and rewriting a test to match a repair
in the same breath as the repair is exactly the self-grading `CLAUDE.md` section 5 forbids.
Until then, do not cite that test's green for anything.

**WHAT THIS DOES NOT DO.** It does not by itself relocate this item, close CS-829, or write
an acceptance clause for either. The GATE - "no amount of work inside this repo can close
it" - is what is refuted, since work inside this repo did close it; where the residue lives
under `CLAUDE.md` section 4 is a routing decision, and improvising one inside a status block
is the synthetic closure this file's own rule forbids. Graded by
`tests/save/test_property_payload_14_60.py`, on a SYNTHETIC (14,60) fixture, so every arm
runs on a machine with no game and no save.

**STATUS 2026-08-16 (session 15): THE OPERATOR PLAYED THE WORLD FORWARD AND SAVED. THE
CONDITION IS PLAUSIBLY MET AND IS DELIBERATELY NOT DECLARED MET.** Measured read-only,
counts only: the pair now has FIVE files where the entry above was written against two,
their sizes all differ, and NO pair of them is byte-identical over the region this entry
names - 10 of 10 pairs diverge, against 0 of 1 before. **WHAT THAT DOES NOT ESTABLISH, and
this entry refuses to round it up:** the earliest divergence between any two of them sits at
offset 12 and the latest at offset 30, which is header metadata - a save timestamp and a
play duration differ between ANY two saves of any world. So what is measured is that they
are distinct FILES. Whether the PROPERTY PAYLOAD is now independently sampled is UNMEASURED,
and that is the whole question this item turns on. **Reading a file count as an independence
count is the error this entry already warns about, and the first probe taken this session
walked into it before a second one caught it.** The next session establishes payload-level
independence with the object walk over the new files before treating the DRAIN half as
workable; if it turns out the payloads are near-identical because the play session changed
little, the honest outcome is that this stays gated and needs more varied play.

**STATUS 2026-08-31 (session 53): THREE MORE SAVES OF THE PAIR ARRIVED WHILE THE SESSION
RAN, TAKING IT TO EIGHT. THE CONDITION IS STILL NOT DECLARED MET.** Measured read-only,
counts only, from a probe that reports no path and no name. The entry above asks for
payload-level independence established with the object walk, and that is STILL UNMEASURED -
three more files is a file count, and reading a file count as an independence count is the
error this entry exists to warn about. What the three do carry is a 120-byte run at the tail
of the body that the walk does not model, byte-identical across all three. **That is the
BODY TAIL, not a property payload, so it is not this gate and does not clear it** - it is
filed as CS-867 in `ROADMAP.md`, and it is why
`tests/save/test_objects.py::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body`
is red on this machine.

**The PREP harness was re-run against the enlarged library this session and still PASSES**,
which is the correct result and not a disappointment: it pins the REFUSAL as a negative
result, the refusal still holds, and no quantity of new saves was ever going to resolve the
grammar on its own. New saves buy material to measure with; measuring is the drain work.

**Why no work inside the repo can close it, measured rather than argued.** The pair reaches
a property terminator on 0 of 1832 payloads at every alignment tried, and a single leading
byte accounts for 669 of 1832 with the rest unexplained. The two files of that pair are
byte-identical from offset 4 through 150074, so they are ONE observation and not two. This
is the same shape as the save-52 grid preamble recorded in session 5: reading a file count
as an independence count is the error, and n=1 there is a CEILING rather than a sampling
accident that more of the same files would fix.

**This is deliberately NOT filed as a grammar defect**, which is the distinction that makes
it gated at all. The variable trailing run on the other three pairs IS a grammar question -
more saves will not fix it, and it stays in `ROADMAP.md` - under CS-413 when this was
written, and under **CS-828** since CS-413 closed on 2026-08-23, and CS-828 is scoped to the THREE
pairs this paragraph names - not to all four measured pairs. A first draft of CS-828 scoped it to every
measured pair, which would have swept (14,60) in and done precisely what the next sentence forbids;
an adversary caught it before it landed. Save 60 is the
opposite. Filing both as one item would hide a blocked half behind a workable one.

**PREP half, COMPLETE and workable now.** The harness that will grade the DRAIN half already
exists: `tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept`
pins the refusal as a negative result, guarded by a liveness assertion without which the zero
also passes when the walker reaches a terminator on nothing at all. That guard is the whole
value of the test - a bare zero is not a measurement.

**Do not** close this by relaxing that test, by interpolating from the three measured
neighbours, or by declaring the pair unsupported. Three measured neighbours making a fourth
look derivable is precisely the refuted arithmetic route ADR 0005 fences, and the test above
exists to stop it being closed by resemblance.

**STATUS 2026-08-22 (session 28): THE NEXT STEP THE BLOCK ABOVE NAMES WAS NEVER TAKEN. THE
DRAIN HALF IS STILL NOT WORKABLE, AND THE ITEM SITS EXACTLY WHERE 2026-08-16 LEFT IT.**

The status above says in terms that "the next session establishes payload-level independence
with the object walk over the new files before treating the DRAIN half as workable". Six days
and several sessions on, no artifact records that walk. Measured rather than recalled:
`docs/LEDGER.md` carries ZERO records citing this item at any date; the last commit touching it
is `f20411c` on 2026-08-16, which is the commit that WROTE the status above; and no commit
since names node data, save 60, purity or payload independence in its subject. The PREP harness
still pins the refusal unchanged - `tests/save/test_properties.py` still records that save
version 60 refuses the grammar the other three pairs accept, on not one payload.

**THAT IS THE WHOLE FINDING, AND IT IS A NEGATIVE ONE: nothing decayed and nothing advanced.**
The condition remains PLAUSIBLY MET AND DELIBERATELY NOT DECLARED MET, which was the right call
on 2026-08-16 and is still the right call. What is missing is the measurement that would settle
it in either direction, and no amount of further play substitutes for it.

**THE RISK THIS RECORD EXISTS TO STOP.** The longer an undischarged "the next session will
measure this" sits in a status block, the more it reads on a later pass as though the
measurement had been taken. That is this item's own file-count-as-independence-count error,
displaced from the data onto the record of the data. The next session that opens this item
establishes payload-level independence FIRST, or writes down plainly that it did not.

**STATUS 2026-09-03 (session 59): THE UNBLOCKING CONDITION IS MEASURED AND MET. PAYLOAD
INDEPENDENCE IS ESTABLISHED AT n = 9. THE DRAIN HALF IS WORKABLE. THE ITEM IS NOT CLOSED
AND NOTHING BELOW CLOSES IT.** The three status blocks above each ask for one thing - that
payload-level independence be established with the object walk before the DRAIN half is
treated as workable - and each records that it was not done. It is now done. Measured
read-only, counts only, from a probe reporting no path, no name and no save byte, using
this repo's own chunk walk and object parse rather than a new parser.

**WHAT WAS MEASURED, AND WHY IT IS NOT THE FILE COUNT THIS ENTRY KEEPS WARNING ABOUT.**
The pair now holds NINE files. All nine carry a DISTINCT property-region digest, which is
a statement about the region the grammar question lives in and not about the file. The
tightest available control is the last four: they share an identical record count and an
identical class count, so record growth cannot explain their divergence, and every pair of
them still diverges on between 112 and 138 records. The earliest divergence inside the
property tag region sits 44 bytes in, spread across 17 to 35 distinct classes and 34 to 58
distinct offsets, on both actor and component kinds. Header metadata occupies offsets 12
to 30 and is not in the region measured. 505 record identities carry more than one
distinct payload across 51 classes. **This is the independence count the entry asked for,
not a file count wearing its name.**

**FIVE FACTS IN THE BLOCKS ABOVE ARE NOW STALE, AND THE LOUDEST ONE WAS BEING CARRIED
FORWARD BETWEEN SESSIONS AS A LIVE OBSTACLE.** The session-53 block says a 120-byte run at
the tail of the body is unmodeled by the walk and is why
`tests/save/test_objects.py::test_every_real_save_of_a_measured_pair_walks_to_the_end_of_its_body`
is red on this machine. **THAT TEST PASSES.** CS-867 closed on 2026-08-31 and modeled the
run - the record is in `docs/LEDGER.md` - and the walk now consumes the body exactly, with
zero unreached records and zero unwalked tail bytes on all nine files. The run is still
real and still sits outside every record extent, so it never enters the payload
measurement, but it is neither unmodeled nor an obstacle. The count of eight is now nine.
The denominator of 1832 payloads is now 23244. The claim that the two files of the pair are
one observation and that n = 1 is a CEILING was true of the two-file state and is refuted
as a description of the present library: n went 1 to 9 by exactly the mechanism the entry
predicted would not help, which is the operator playing the world forward.

**THE REFUSAL IS UNCHANGED AND THAT IS THE POINT OF THE PREP HARNESS.** Zero of 23244
payloads reach a property terminator, against zero of 1832 before.
`tests/save/test_properties.py::test_save_60_refuses_the_grammar_the_other_pairs_accept`
still passes, pinning the refusal as a negative result. Twelve times the material and the
same answer is a stronger negative than the one this entry was written on, not a weaker
one - the grammar was never going to fall out of more saves, and the entry said so.

**THE CAVEAT, STATED BEFORE ANYONE BUILDS ON THE NUMBER.** All nine files are ONE world
played forward. This is a longitudinal series, not nine independent worlds, so n = 9 is a
BYTE-LEVEL independence count and not a count of independent world generations. The
grammar-shape material is better described by the class population, which rises from 62
distinct classes in the earliest file to 111 in the latest. A drain that needs independent
WORLD generation still needs more play; a drain that needs varied property payloads does
not, and that is the drain this gate blocks.

**WHAT THIS DOES NOT DO.** It does not close CS-G05, it does not clear CS-829, and it does
not write an acceptance clause for the drain. The gate's external condition is met; the
work behind it is unstarted, which is a different state and belongs in a different file
under the topology in CLAUDE.md section 4. Routing it - deciding whether CS-G05 stays here
with its DRAIN half open or is replaced by an open item carrying a derived acceptance
clause, and what that does to CS-829 - is a decomposition question that was deliberately
NOT improvised inside this status block. Filing a clause here to make the entry look
finished is the synthetic closure this file's own rule forbids, one level up.


---

#### The (14,60) wall - a named target - relocated from `docs/item_notes/phase4-followups-900.md` 2026-09-10

This is CS-G05's territory and is NOT closed here. Recorded because the probe
found where to look.

**Nothing in this tree reads a UE5 file version.** The only such field anywhere
is inside the `.usmap` container header, which is a different file. No `1011` or
`1012` appears in the repository, and two external sources give that gating
constant differently, so neither number may be hardcoded from a citation.

**Where it would live.** `(14,60)` is the ONLY pair carrying a package summary,
and that summary is read as a string, then **22 OPAQUE BYTES THAT ARE SKIPPED**,
then a custom-version count and that many 20-byte entries. A package summary
carrying a custom-version array is exactly where an engine writes its file
versions. Those 22 discarded bytes are the one region in this tree that could
hold the discriminator.

**BUT THE CAUSE IS NOT ESTABLISHED, AND A RESEMBLANCE IS NOT A FINDING.**
`(14,60)` is also the only pair with a per-payload int32 trailer and the only one
whose second collectables block is unnamed - so it already differs in payload
FRAMING, not only in tag content. A framing difference that puts a body offset
one field out produces the identical symptom: zero payloads reaching a
terminator. The observation that zero reached one "at every alignment tried"
argues against a pure start-offset error, but the set of alignments tried was
never recorded, so it does not settle it either. Do not close CS-G05 by
resemblance to the three readable pairs - its own section forbids exactly that.

### CS-G09 - MAIN's kit-hook commands in a probed form

**One line:** CS-815's kit-hook half: the subagent-first and claims PreToolUse hook
commands in `.claude/settings.json` stay ORDER-exact on a bare interpreter, and only MAIN
can make a probed form conformant.

**Unblocked by:** a MAIN ruling or kit version that makes a probed (interpreter-checked)
form of the subagent-first and claims PreToolUse hook commands conformant. MAIN's orders
fix those commands, so no amount of work inside this repo reaches it. The ruling is
`docs/LEDGER.md`, the 2026-10-23 CS-815 FROZEN-FILE GRANT DENIED, DEFERRED TO MAIN record.

**Not a second state for CS-815.** It stays OPEN in `ROADMAP.md` and this gate holds its
kit-hook half only, so the classification block keeps it MENTIONED; fencing the row would
be a cross-file edit this filing does not make.

**Filed 2026-10-23** (session 151) from that record.

### CS-G10 - 1.0 phase costs from the shipped GP_ phase assets (UFGGamePhase::mCosts)

**One line:** the milestone-gap advice domain needs each space-elevator phase's cost on a
1.0 build, and that cost lives in the shipped `GP_` phase assets' `UFGGamePhase::mCosts`,
inside the paks.

**Unblocked by:** the SAME written `CONVENTIONS.md` section 14 verdict on Oodle Data
recorded under CS-G01 above, which pak extraction needs. No amount of work inside this repo
reaches it.

**The save is not a 1.0 phase-cost source**, and that is measured, not assumed:
`docs/adr/0016-unlock-arrays-carriers-and-serialized-grammar.md` records that no 1.0-native
save writes `mGamePhaseCosts`, that the shipped header marks the array deprecated and kept
only for save compatibility, and that the one measured table - written by a world carried
forward from pre-1.0 builds - names phases the installed vocabulary lacks. Mapping its
`EGP_` names onto `GP_` phases without measuring is not a substitute, and this entry refuses
that trade.

**Tier 2 when it unblocks.** It blocks the milestone-gap advice domain, one of the four v1
domains in `CLAUDE.md` section 7: until it lands, every library world publishes no phase
cost, under a named reason.

**PREP half, workable now:** a pak-backed source slots behind
`clockspeed/progress/phases.py::PhaseCostSource` beside the save-backed one, so no consumer
changes when the verdict lands.

**Filed 2026-10-24** (session 151) by the close of the item that wired the save phase-cost
source.

---

## Cross-references

- Open work: `ROADMAP.md`
- Aspirational and conditional-trigger work: `BACKLOG.md`
- Completion records: `docs/LEDGER.md`
- Decisions and their fences: `docs/adr/README.md`
