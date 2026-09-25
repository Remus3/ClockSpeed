# Clockspeed - Architecture Decision Records

**Owner file for:** the ADR index, the ADR format, the numbering rule and the status
vocabulary.

**This directory contains nothing that is not a decision.** Module maps go in
`docs/ARCHITECTURE.md`, commands in `docs/OPERATIONS.md`, completion records in
`docs/LEDGER.md`, blocked items in `docs/GATED.md`.

---

## 1. Format

One file per decision. Filename is `NNNN-short-kebab-slug.md`. Every ADR has exactly four
sections, in this order:

| Section | Contains |
|---|---|
| **Status** | One of the values in section 3, plus the date it reached that status. |
| **Context** | The forces at play. What was true, what was constrained, what alternatives existed and what each cost. This is the fence. |
| **Decision** | What was decided, in the active voice. |
| **Consequences** | What follows - what becomes easier, what becomes harder, what is now foreclosed, and what must be revisited if a stated premise changes. |

**Record the fence, not only the conclusion.** An ADR that states only what was decided
invites the next reader to rebuild the argument from scratch and arrive somewhere else.
The Context section is what makes the decision durable: it says what was already
considered, so a rejected alternative stays rejected without being re-argued.

Keep an ADR short. It is a record of a decision, not a design document. If the design
needs pages, the design goes in its own file and the ADR points at it.

---

## 2. Numbering

- **Numbers run from `0001` upward, zero-padded to four digits.**
- **A number is permanent. It is never renumbered and never reused** - not when an ADR is
  superseded, not when one is deprecated, not when a reserved slot goes unused. Every
  ledger entry, roadmap item, commit message and code comment that cites an ADR cites the
  number, and renumbering breaks all of them silently.
- A number may be **reserved** ahead of the decision, as in section 4 below. A reserved
  number is burned whether or not the ADR is eventually written.
- The number is allocated once and does not change if the filename slug changes.

---

## 3. Statuses

| Status | Meaning |
|---|---|
| `proposed` | Written, not yet accepted. Not binding. Nothing may cite it as settled. |
| `accepted` | In force. Binding. Cite it freely. |
| `superseded by NNNN` | No longer in force. **The file stays exactly where it is.** The superseding ADR's Context explains what changed. |
| `deprecated` | No longer in force and not replaced - the decision simply no longer applies, typically because its subject was removed. |

**A superseded ADR is never deleted.** The mechanism is specific and it has cost real
time in real projects: a decision that is silently removed comes back. Someone
rediscovers the original problem, finds no record that it was ever settled, re-runs the
same analysis, and frequently reaches the opposite conclusion - because the reason the
first decision was reversed is exactly the context that got deleted with it. Keeping the
superseded file costs a few kilobytes. Losing it costs a session.

The same rule applies to a superseded status line: when an ADR is superseded, update its
Status line to point at the successor and leave every other word of it untouched.

---

## 4. Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-adr-process.md) | ADR process | `accepted` |
| [0002](0002-s8-node-data-seed-dependence.md) | S8 - seed dependence of resource-node data | `accepted` |
| [0003](0003-s4-node-actors-in-save.md) | S4 - resource-node actors in the save | `accepted` |
| [0004](0004-s6-unlock-state-recoverability.md) | S6 - unlock-state recoverability from the save | `accepted` |
| [0005](0005-overclock-ceiling-source.md) | S7 - source of the overclock clock ceiling | `accepted` |
| [0006](0006-unsharded-clock-base-and-the-ceiling-fence.md) | The un-sharded clock base in the registry, and the ceiling fence | `accepted` |
| [0007](0007-header-and-chunk-framing-are-version-dependent.md) | Save header and chunk framing are version dependent | `accepted` |
| [0008](0008-detection-claims-are-derived-never-written.md) | A detection claim is derived by the suite, never written in prose | `accepted` |
| [0009](0009-inventory-potential-top-level-carries-no-slot-count.md) | The serialized potential component's top level carries no slot count | `proposed` |
| [0010](0010-item-notes-is-an-index-over-per-phase-leaves.md) | `docs/item_notes.md` is an index over per-phase leaves | `accepted` |
| [0011](0011-the-cs-8nn-follow-up-leaf-splits-at-cs-850.md) | The `CS-8nn` follow-up leaf splits at CS-850 | `accepted` |
| [0012](0012-dashboard-refusal-vocabulary-and-wire-form.md) | The dashboard's refusal vocabulary and its exact-rational wire form | `accepted` |
| [0013](0013-electron-licence-gate.md) | Electron clears the licence gate for local use, with obligations only on distribution | `accepted` |
| [0014](0014-the-shell-trusts-one-pinned-certificate.md) | The shell trusts one pinned certificate and defers every other host | `accepted` |
| [0015](0015-the-shell-may-start-the-surface.md) | The shell may start the surface, and stops only what it started | `accepted` |
| [0016](0016-unlock-arrays-carriers-and-serialized-grammar.md) | The unlock arrays' carriers, and their serialized grammar | `proposed` |
| [0017](0017-the-lane-forks-the-shared-loop-modules.md) | The lane FORKS the cross-repo loop modules rather than joining their pin | `accepted` |
| [0018](0018-the-flip-recreates-the-remote-and-keeps-the-commit-graph.md) | The public flip recreates the remote and keeps the commit graph unrewritten | `accepted` |
| [0019](0019-the-map-underlay-and-the-purity-declaration.md) | The map underlay, and purity closed by declaration | `accepted` |
| [0020](0020-shipped-asset-extraction.md) | Shipped-asset extraction, and where each of the four map requirements is recoverable from | `accepted` |
| [0021](0021-the-variable-power-law.md) | The variable-power law is two bounds, and the building estimate is their envelope | `accepted` |
| [0022](0022-acceptance-lives-in-the-item-note.md) | An item's acceptance lives in its item-notes section, with a pointer on the line | `accepted` |
| [0024](0024-the-credential-scan-population-boundary.md) | The credential-scan population boundary is publication, not location | `accepted` |

Slots 0002, 0003 and 0004 were reserved for the three phase-1 spike decisions and have now
been written, in the order the spikes ran: S8, then S4, then S6. These three are the spikes
that can change the shape of the product, which is why each got its own numbered decision
rather than a line in a report.

Each records a binary result measured against live data, plus the stated limits of that
measurement. Read 0003 before planning any node-data work: it is the one whose result
contradicts a premise in `BOOTSTRAP.md` section 8.3, and the correction is recorded in
`docs/LEDGER.md`.

**Slot 0020 was reserved on 2026-09-13 and is now WRITTEN**, in the same session that
reserved it. Its slug was shortened on filing to keep section 5's short-kebab rule and to
stay inside the citation guard's byte ceiling, which had 65 bytes free. Do not open a second
slot for that subject - the session-85 plan named `0019` for it before `0019` was taken by
the map-underlay adjudication, and that pointer is stale.

**Slot 0021 was taken and written in one cycle on 2026-09-14 under CS-301.** It is the first
decision to use the header index ADR 0020 built for a question about MEANING rather than
about serialization.

**Slot 0022 was taken and written in one cycle on 2026-09-17 under CS-971**, recording an
adjudicator ruling on where an item's acceptance clause lives. No slot is reserved ahead of
it - take 0023 next.

---

## 5. Adding an ADR

1. Take the next unused number. Check this index, not the directory listing - a reserved
   number may have no file yet.
2. Create `NNNN-short-kebab-slug.md` with the four sections from section 1.
3. Add the row to the index table in section 4.
4. If the ADR supersedes an existing one, update that ADR's Status line to
   `superseded by NNNN` and change nothing else in it.
5. Cite the ADR from the ledger entry for the item that produced it.
