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

---

## Cross-references

- Open work: `ROADMAP.md`
- Aspirational and conditional-trigger work: `BACKLOG.md`
- Completion records: `docs/LEDGER.md`
- Decisions and their fences: `docs/adr/README.md`
