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

**Unblocked by:** the operator placing a snapshot of a progressed world into `corpus/`.
`.gitignore` already reserves `/corpus/` and the directory does not exist; ADR 0004
recommended exactly this and it was never done. **No amount of work inside this repo can
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

### CS-G03 - Public visibility flip

**One line:** Flip the repository from private to public.

**Unblocked by:** all seven CI tier-3 gate checks passing - full-history secret scan, PII
scan across all tracked files and all commit messages, third-party license audit, no
publisher-owned data assets tracked in the tree or in history, `README.md` taking an
outsider from zero to a first result, all doc cross-references resolving with no orphaned
or stale markdown, and a clean-checkout probe passing on a machine that has never seen
the project.

**This is an operator sign-off item as well as a technical one.** It is outward-facing
and irreversible in practice, so the gate clearing is necessary and not sufficient.

**PREP half, workable now:** every one of the seven checks exists as a runnable job long
before the flip is contemplated. Hygiene is enforced from the first commit and is not
deferred on the grounds that the repo is private.

**The third-party licence audit has its first recorded verdict.** Electron's gate result -
split into local use, a public manifest merely NAMING it, and distribution of a packaged
binary - is `docs/adr/0013-electron-licence-gate.md`. The audit consumes that record rather
than re-deriving it, and the ADR states which of the three scopes was cleared only WITH
obligations.

#### Operator decision 2026-08-13: the flip ships from a FRESH history

**The working tree is clean of PII; the history is not, and cannot be made clean without
a rewrite.** Decided: do not rewrite. The public artifact is produced from a squashed or
orphan-branch history instead, and the local development history is kept intact and
private because it is genuinely useful.

Two facts force this, both measured rather than assumed:

1. **The tree carried personal data and every commit still does.** `BOOTSTRAP.md` carried
   the pinned world name and three world-identity tokens. The working tree has been
   scrubbed, but all commits that existed at the time of the decision carry the unscrubbed
   file. Commit MESSAGES were checked and are clean.
2. **Author identity is real-identity-linked in every commit.** Every commit is authored
   under a real email address. This was NOT caught when the operator was asked about the
   PII question - it was surfaced afterwards by the adjudicator reviewing the LICENSE
   change, as the common-mode risk in the reasoning behind that change. Changing the
   LICENSE holder to a collective name does not touch it, and neither does scrubbing
   `BOOTSTRAP.md`.

3. **Agent co-authorship trailers are publication metadata too.** Operator decision: no
   commit carries a `Co-authored-by:` trailer naming an agent. Measured at the time of the
   decision, no commit did - the trailer had never been added - so this is a standing rule
   going forward rather than a cleanup, and it costs nothing to keep true. It is recorded
   here rather than only in a habit because a trailer is trivial to reintroduce by default
   and impossible to remove later without the rewrite this section exists to avoid.

   **TWO MECHANISMS CARRY THIS CLAUSE, and until CS-1157 only one of them existed.**
   `.githooks/commit-msg` REFUSES a `co-authored-by` trailer end to end, on a polarity
   deliberately wider than the rule, and `tests/test_commit_msg_gate.py` drives it - so the
   trailer has never landed. But refusing is not the same as not generating: the harness
   injected an attribution instruction into every session, worded as though it superseded
   earlier guidance, and the only thing between that instruction and a refused commit was a
   model reading a memory note and declining by hand each time. `.claude/settings.json` now
   sets `attribution` to blank and `includeCoAuthoredBy` to false, under the frozen-file
   grant recorded in `docs/LEDGER.md` under CS-1157, and the same two keys are set at user
   scope so a repository with no settings file on this machine is covered too. BOTH KEYS,
   because an older client reads only the deprecated one and would reintroduce the trailer
   silently. The gate stays the primary defence and is not weakened by this: a settings key
   is a request to the tool and the gate is a refusal by the repository.

   The blanked `attribution.pr` suppresses the PR-body footer as well, which is MORE than
   this clause asks for. That is a deliberate extension on this clause's own reasoning -
   publication metadata is trivial to reintroduce and impossible to remove later - and it is
   written down rather than left to be discovered.

**Therefore the flip has an eighth precondition, additional to the seven above:** the
published history is generated fresh; the identity it is authored under is chosen
deliberately at that point rather than inherited from the local git config; and no commit
in it carries an agent co-authorship trailer. A scrubbed working tree pushed onto the
existing history satisfies none of the three.

**Do not** treat the working-tree scrub as having cleared this item. It cleared the tree,
which is the PREP half. The DRAIN half is the flip itself and it remains gated.

#### Measured 2026-08-22 (CS-702): the rule was broken the day after it was written, and is now ENFORCED

**Nothing above this heading is edited, and that is deliberate.** The 2026-08-13 record
stands exactly as written, its measurement sentence included, because that sentence was
true when written. What follows is a LATER observation and what it changed. Filed as new
text rather than as a correction in place, because the dated record is now the evidence
that the rule was written down BEFORE it was broken - the most useful thing it holds.

**The measurement, and how to re-derive it rather than trust it.** Walk every commit body
on `main` and match a line that sits at column zero, carries a colon, and whose text before
that colon - trailing whitespace trimmed - folds to `co-authored-by`. That is the shape git
itself reads as a trailer, and it is the shape the gate matches. Measured on 2026-08-22:
EIGHTEEN commits match, oldest `e9af2df`, newest `5907d45`, all dated 2026-08-14 or
2026-08-15, and ZERO since. The eighteen are a closed set at that date. The repository
total keeps growing, so the eighteen, the two SHAs and the two dates are the stable figures
here - not a ratio. The stripped-prefix method this section first described returns the
same eighteen over this history, so the correction recorded further down changes the gate,
not the census.

**A naive census gets this wrong - but only for ONE SPELLING of the token, and naming which
spelling is the whole of the point.** A plain substring search for the COLON-LESS token
`co-authored-by` also matches PROSE ABOUT THE RULE, this subsection included: measured
2026-08-22 over `main`, it returns NINETEEN where the trailer-shaped match returns EIGHTEEN,
and the nineteenth is a commit message discussing this very item. Search for the token WITH
its colon and the gap closes - that returns EIGHTEEN as well. So in that particular
comparison it is the COLON doing the separating, not the anchor, and an earlier draft of
this paragraph cited the nineteen without saying which token it had searched for. A count
whose matcher is unstated cannot be checked by the next reader, which is the only thing a
recorded measurement is for.

**What was overtaken is the CONSEQUENCE, not the measurement.** Every one of the eighteen
postdates the 2026-08-13 decision by one or two days. What did not hold is the clause that
followed it - that the rule "costs nothing to keep true". A rule kept by habit, against a
tool whose default violates it, is a rule that fails on the first session nobody is
watching, and this one failed on the next. The same entry predicted that in its closing
sentence and shipped no mechanism.

**What changed: the rule is now MECHANICAL.** `.githooks/commit-msg` rejects the trailer,
under the frozen-file grant recorded in `docs/LEDGER.md` for CS-702. The acceptance is an
end-to-end transcript - a real staged change, a real `git commit`, a non-zero exit and an
unmoved HEAD - because a hook's presence is never proof that it fires.
`tests/test_commit_msg_gate.py` drives real commits in a throwaway repository for exactly
that reason: `core.hooksPath` is machine-local configuration that is never cloned, so a
unit test of the matcher would be byte-identical green whether the gate fired or not.

**The gate's polarity is WIDER than this section's rule, deliberately.** The 2026-08-13
decision forbids a trailer NAMING AN AGENT; the gate rejects EVERY co-authorship trailer,
name-free, a hypothetical human one included. A list of agent names would fail open on the
next harness or model rename, which is the continuous pressure the item was filed against.
Measured cost at the grant: zero - all eighteen name an agent, and no human co-author
trailer exists anywhere in the history. A genuine human co-author is BLOCKED, which is the
intended failure direction; the route out is a new item and a recorded allowlist entry,
never a shortened matcher.

**The predicate is derived from GIT'S OWN TRAILER PARSER, after a first cut that was wrong
in BOTH directions at once.** That first cut matched a body line whose STRIPPED form started
with `co-authored-by:`. Measured against git 2.53, it was simultaneously too narrow and too
wide, and the two halves were refuted independently.

TOO NARROW, which is a gate failing OPEN on the exact thing it exists to stop. git locates
the separator FIRST and trims the token AFTERWARDS, so a line reading `Co-authored-by :
value` - one space before the colon - is a real trailer to git. Under the first cut the
commit was ACCEPTED, HEAD moved, and
`git log -1 --format=%(trailers:key=Co-authored-by,valueonly)` returned the value. A tab
before the colon behaved identically.

TOO WIDE, which is how a gate gets switched off. git refuses whitespace before the token
has begun, so an INDENTED line is not a trailer to git at any position in any message -
`interpret-trailers --parse` returns nothing for it and the key reads empty on a commit
carrying one. The first cut blocked it anyway, and the cost was that this repository could
not QUOTE THE SHAPE IT FORBIDS: this subsection, the ledger entry closing the item and the
commit message landing it were all rejected by the gate they describe.

**So the shipped predicate judges a line only at column zero, and compares the trimmed
token before the first colon, case-folded.** To quote the shape rather than record one,
INDENT the example by one space - which is exactly the shape git also declines to read.

**A FENCED BLOCK IS NOT A SHIELD, and this gate must never be taught that it is.** Measured
2026-08-22 on git 2.53: a triple-backtick block whose only trailer-shaped line is a
co-authorship one is not parsed as a trailer, but the SAME block carrying a GIT-GENERATED
trailer beside it - a sign-off, or a cherry-pick line - is parsed whole, fence lines and
all, and the co-authorship line inside it becomes a real trailer. The gate therefore still
refuses a fenced example whose content sits flush at column zero. That is a DECLARED
divergence in the fail-CLOSED direction, pinned by a test so it cannot drift silently, and
the obvious cheap fix - skip fenced blocks - would fail OPEN on precisely the sign-off
message above. Indent the content instead.

**THIS GATE IS A CLIENT-SIDE, LOCALLY-ARMED CONTROL, and a whole CLASS of routes goes around
it.** Naming only two of them, as this section first did, understated the shape of the
problem. The hook fires only where `core.hooksPath` points at `.githooks/` on the machine
doing the commit, and only on the code paths git chooses to run `commit-msg` on. Members of
the class, recorded rather than chased, each its own item: `git commit --no-verify`;
`git cherry-pick`; `git revert`, which is a sequencer sibling of cherry-pick and was MISSED
by the first enumeration of this list; `git rebase` on either backend; `git am`; a fresh
clone on which nobody
has run the bootstrap, where the hook is present but unarmed; `core.commentChar` or
`core.commentString` remapped, which moves the comment-stripping the gate is built on; and a
substituted interpreter, which was a live member of this class until **CS-703 CLOSED it on
2026-08-22**. The ladder now requires a candidate to answer with a token it has to COMPUTE
and to return a failure code it has to REPORT, and a set-but-failing `CLOCKSPEED_PYTHON` is
refused rather than silently replaced by the next rung. That member sat ABOVE the edit line
the CS-702 grant drew and could not be touched under it; CS-703's own grant drew the new
line. **It was never a `CLOCKSPEED_PYTHON` problem:** the same escape was measured through
the `python` rung with no environment variable set at all, so unsetting the variable was
never a mitigation. What remains open here is narrower and is filed separately - the probe
proves PYTHONHOOD and not TOOLCHAIN (CS-817), pre-push trusts an exit code for pytest's
presence (CS-821), and `.claude/settings.json` carries no probe at all (CS-815).

**THE HOOK PREDICTS THE BYTES GIT WILL STORE AND NEVER OBSERVES THEM, and three further
escapes follow from that. They are MEASURED, they are NOT closed here, and they are filed as
CS-813.** Cleanup runs AFTER this hook: on the editor path the hook sees git's full template
while the stored message has it stripped. The comment-stripping this gate inherits models one
cleanup mode out of five. Measured with real commits: a co-authorship trailer below git's cut
token is stored and git reads it as a trailer; a comment line carrying a byte above 0x7E puts
that byte in the stored message, which is a hole in non-negotiable 4 inside the hook that
enforces it; and a long comment line as the first line inflates the STORED subject past the
72-character cap. All three predate the trailer check and none is caused by it.

**A REWRITE OF THAT PRE-FILTER WAS BUILT UNDER A WIDENED GRANT, MEASURED, AND DELIBERATELY NOT
SHIPPED - that is a result, not an unfinished attempt.** It closed all three escapes and a
fourth nobody had named, and it was refuted anyway. Reading the whole buffer is sound for a
SCAN and unsound for a SELECTION: the subject is chosen from the first non-blank line, so
reading more lines does not widen the check, it picks a DIFFERENT line from the one git stores.
A message whose first line is a comment therefore passed with a stored subject well over the
cap, and the same shape let a placeholder subject through - both cases the inherited
comment-stripping got RIGHT. It also rejected `git commit --verbose` whenever the staged diff
carried a byte above 0x7E, which blocks precisely the work of fixing such a byte, and rejected
git's own generated `fixup!` subject for any commit whose subject is 66 characters or longer.
The honest reading is that a commit-msg hook can be made conservative and cannot be made
complete, because two inputs to the prediction - an explicit cleanup override and the verbose
flag - are invisible to any hook. The measurements are kept against CS-813 so the next attempt
starts from them rather than from scratch.

**What closes the class is not a better matcher - it is a RANGE SCAN.** Over the pushed
commits, in `.githooks/pre-push`, or on the CI side, or both: a range scan reads history as
it LANDS rather than as it is authored, and none of the routes above can avoid being read.
Each is its own frozen file and its own grant. Until one exists, read this gate as making
the rule hard to break BY ACCIDENT - which is the failure it was actually filed against, a
tool whose default violates the rule every session - and not as making it impossible to
break on purpose.

**The eighth precondition above is NOT breached by the eighteen.** It speaks of the
PUBLISHED history, and this section already rules that the published history is generated
fresh from a squash or an orphan branch, which need not carry them. What the eighteen broke
was the standing rule and the consequence drawn from it, not the flip.

#### Filed 2026-09-24 (CS-700): ADR 0018 replaces the fresh-history mechanism above

No dated text above this note is edited; it stands exactly as written, and the
sentences this note supersedes are listed here instead of being marked in place.
`docs/adr/0018-the-flip-recreates-the-remote-and-keeps-the-commit-graph.md`,
accepted 2026-09-08, replaced the squash or orphan-branch mechanism of the
2026-08-13 decision: the remote is deleted and recreated and `main` is pushed
with its commit graph kept. Superseded, located by content:

- In the 2026-08-13 decision's opening paragraph, "Decided: do not rewrite." and
  "The public artifact is produced from a squashed or orphan-branch history
  instead" - `main` is published, and S7a rewrites its identity and strips its
  trailers.
- In the eighth precondition, the first clause "the published history is generated
  fresh". It now reads - the published history is `main` after CS-700 step S7a,
  which rewrites author and committer to the chosen noreply identity and strips
  every agent co-authorship trailer. Its second and third clauses stand unchanged
  and are discharged at S7a, and S8 proves both: its re-scan re-runs S7a's identity
  allowlist check and the trailer-shaped census. `main` pushed WITHOUT S7a still satisfies
  none of the three.
- The CS-702 section's closing paragraph, "The eighth precondition above is NOT
  breached by the eighteen", rested on a history "generated fresh from a squash or
  an orphan branch" and no longer holds - without the S7a strip the eighteen would
  publish.

The trailer-shaped census the flip runs is defined in exactly one place, CS-700 step S7a
in `docs/item_notes/phase7.md`. The CS-702 section's "Walk every commit body on
`main`" paragraph is the method that measured the eighteen on 2026-08-22, kept as
dated evidence; it is not the census's definition, and where the two differ S7a
governs. Steps and controls: CS-700 in `docs/item_notes/phase7.md`.

#### Filed 2026-09-24 (CS-700): who decides the flip and who performs it

"Operator sign-off" above and in CS-700 S9 is read through `CLAUDE.md` section
6.1, and it splits three ways.

**(a) The adjudicator DECIDES readiness.** The decision that the gate has cleared
is an in-session adjudicator's, ruled at a frozen SHA - CS-700 step S8a - on
evidence re-run that session against all eight preconditions; a ruling from MAIN
may stand in for that decision. The adjudicated SHA is the SHA S9 onward operates
on. A commit to `main` after S7a voids S7a through S8a and restarts them from the
preservation bundle - CS-700's one late-commit rule, stated at S7a; no range is
re-adjudicated. S10 pushes the adjudicated SHA itself, not a branch name.
The ruling itself is recorded outside that history until S12 completes, so
recording it never moves `main` - CS-700 step S8a states where.

**(b) The operator's single confirmation is the irreversible-act FLOOR, not a
decision.** S9 deletes and recreates the remote and S12 publishes the repository;
both are outward-facing and cannot be undone. The operator confirms them in their
own words typed into the main session, once, immediately before S9, and
that confirmation covers S9 through S12 as one run. It lapses if any step's control
aborts, if the session ends, or if `main` moves past the adjudicated SHA, and is
never reused: continuing needs a new own-words confirmation, and CS-700's plan
states the remote's state at each halt point and where a run resumes. It
confirms a plan already ruled at (a). It is not a request to authorise a choice or
to pick a direction - section 6.1 routes those away from the operator - and it is
not delegable: section 6.1 names this exact act as its one exception, an
irreversible outward act on the repository itself that waits for the operator's
own-words confirmation, "a safety floor no adjudicator or stand-in lifts".

**(c) The floor binds every actor** - an adjudicator, MAIN and any session,
including the one running the flip. Section 6.1 states the floor directly in its
exception for an irreversible outward act on the repository itself, and says of
MAIN's stand-in that it "lifts no safety floor - destructive or irreversible acts"
among them. This note cites those sentences and does not extend them. The session
agent executes every step; the operator's hands are needed only for a credential
or scope grant.

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

### CS-G08 - A disposable environment that has never seen the project

**One line:** the clean-checkout probe (CS-1187) and the no-game half of the README walk (CS-1186) need an environment with no prior clone, no hooks path, no user-scope agent settings, no project cache and no game install, and this machine has none available.

**Unblocked by:** Windows Sandbox (optional feature Containers-DisposableClientVM, measured disabled 2026-09-25, and needing a reboot) being enabled at a time the operator chooses, OR any other disposable VM or machine that has never held a clone of this repository. The condition is met when that environment launches. The protocol - the acceptance clause below, run as written - then runs, and a different agent repeats it clean.

**Why no workaround:** a fresh local account on this machine is an accounts act and inherits machine-wide installs and the game's registration. The tier-2 `clean-checkout-probe` job says in its own comment that it is not a substitute. Blocks CS-G03 check 7 and the human half of check 5.

**Filed 2026-09-25** by the wave-2 adjudicator ruling (session 113), which re-probed the feature's install state and found no sandbox executable. Enabling it takes a reboot, and a reboot takes down every concurrent session on the operator's machine - a destructive act no agent takes, and one no stand-in ruling can lift.

**CS-1187 IS THIS GATE'S ITEM, AND ITS ID IS CLASSIFIED MENTIONED BY DESIGN.** Its `ROADMAP.md` line was removed when it was gated, so it is no longer a live row, and a BLOCKED line fences only a live row - `tests/ops/test_lane_scope.py` pins that. The item now lives here under CS-G08, and when the gate unblocks it moves to `ROADMAP.md` under CS-G08, as this file's header prescribes. **CS-1186 stays OPEN and takeable, and is MENTIONED too:** only its no-game half is gated here; the README walk on an override approximation is workable now, and it does not discharge the no-game clause. Its section in `docs/item_notes/phase7.md` records that.

**CS-1187's item section, relocated VERBATIM from `docs/item_notes/phase7.md` 2026-09-25 when the item was gated.** The acceptance clause moved UNCHANGED and is what CS-G08's drain half must meet. The headings are re-nested one level to sit under this entry; their text and the body are byte-identical.

#### Acceptance

in a disposable environment with no prior clone, no hooks path, no user-scope agent
settings and no project cache (e.g. Windows Sandbox), a fresh clone plus the
docs/OPERATIONS.md bootstrap yields verify_env exit 0, armed hooks proven by a
staged violation leaving HEAD unmoved, and a green tier-1 suite.

#### Full headline

the clean-checkout probe has never run on a machine that has never seen the project

#### FILED 2026-09-24, from the N0 adjudicator ruling at `599528c`

Gate item 7. CS-700 section 5 records that it FAILS today; CS-938 is one known
cause, not the probe. The `clean-checkout-probe` job in
`.github/workflows/tier2.yml` says in its own comment that it is NOT a substitute,
because a runner is not a machine that has never seen the project.

---

## Cross-references

- Open work: `ROADMAP.md`
- Aspirational and conditional-trigger work: `BACKLOG.md`
- Completion records: `docs/LEDGER.md`
- Decisions and their fences: `docs/adr/README.md`
