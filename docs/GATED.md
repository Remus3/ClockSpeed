# Clockspeed - Gated items

**Owner file for:** work items blocked on something OUTSIDE the repo.

One line per item, plus the exact external condition that unblocks it. An item that is
merely unstarted is not gated - that is `ROADMAP.md`. An item that is merely wished for
is not gated - that is `BACKLOG.md`. **Gated means: no amount of work inside this repo
can close it.**

Gated IDs use the `CS-G` series. They are permanent and never reused. When a gated item
unblocks, it moves to `ROADMAP.md` under its own `CS-G` ID and closes into
`docs/LEDGER.md` under the same ID.

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

**Therefore the flip has an eighth precondition, additional to the seven above:** the
published history is generated fresh; the identity it is authored under is chosen
deliberately at that point rather than inherited from the local git config; and no commit
in it carries an agent co-authorship trailer. A scrubbed working tree pushed onto the
existing history satisfies none of the three.

**Do not** treat the working-tree scrub as having cleared this item. It cleared the tree,
which is the PREP half. The DRAIN half is the flip itself and it remains gated.

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
more saves will not fix it, and it stays in `ROADMAP.md` under CS-413. Save 60 is the
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

---

## Cross-references

- Open work: `ROADMAP.md`
- Aspirational and conditional-trigger work: `BACKLOG.md`
- Completion records: `docs/LEDGER.md`
- Decisions and their fences: `docs/adr/README.md`
