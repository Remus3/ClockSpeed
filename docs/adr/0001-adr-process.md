# 0001 - ADR process

## Status

`accepted` - 2026-08-13.

This ADR establishes the ADR process itself. It is the one decision that cannot cite an
earlier ADR as precedent.

---

## Context

The operating doctrine for this project (`CONVENTIONS.md` section 4) organizes every work
item into exactly one of four states - open, aspirational, gated, closed - each with
exactly one owner file. That structure answers "what is the state of this work". It does
not by itself answer "why is the work shaped this way", and that second question is the
expensive one.

**Rediscovery, not ignorance, is the dominant failure mode of this project.** The costly
events are not the ones where something was unknown. They are the ones where something
was already known and the knowledge was not reachable at the moment it was needed:

- **Redoing closed work.** An item that shipped is picked up again because nothing
  visible says it shipped, or says it under a name the next reader searched for.
- **Re-pitching a refuted idea.** An approach was evaluated, found wanting for a specific
  reason, and dropped. The conclusion survived in someone's memory; the reason did not.
  The idea returns, sounds good again - because the objection to it is exactly what was
  lost - and consumes a second full evaluation to reach the same answer.
- **Acting on a stale doc.** A document states something that was true when written. It
  is read as current, and work is built on it.

Each of these costs more than any bug in this project has. A bug is bounded by the code
it is in; a rediscovery consumes a session and can also produce a reversal of a decision
that was correct the first time.

Two further forces make the plain conclusion insufficient on its own:

1. **Work runs in parallel, worktree-isolated agent slices.** A decision reached inside
   one slice's context does not exist anywhere else unless it is written to a shared
   file. Subagent context is not inherited and is not durable.
2. **A recorded conclusion without its fence invites reconstruction.** "We chose X" is an
   invitation to ask why not Y, and the honest answer to that question is another full
   analysis unless the original one was written down. `CONVENTIONS.md` section 4 makes
   this explicit for settled items: record the fence, not just the conclusion.

Alternatives considered:

- **Decisions recorded in the ledger only.** Rejected: the ledger is a per-item
  completion record and is append-only by date. A decision that must be found by subject
  five months later is not findable in a date-ordered list, and a superseded decision has
  nowhere to point.
- **Decisions recorded in `CLAUDE.md` only.** Rejected: `CLAUDE.md` is auto-loaded every
  turn and is size-budgeted. It can hold a one-line settled entry, and it cannot hold the
  context that makes the entry durable.
- **No formal record; rely on the git log and on memory.** Rejected: this is the status
  quo that produces the three failure modes above.

---

## Decision

**Every architectural decision gets a numbered ADR in `docs/adr/`, and the ADR records
the fence around the decision as well as the conclusion.**

Specifically:

1. An ADR is written for any decision that constrains future work - a technology choice,
   an interface boundary, a data-model commitment, an explicitly rejected approach, a
   spike outcome that changes the product's shape.
2. Each ADR carries Status, Context, Decision and Consequences. **The Context section is
   mandatory and is the point of the exercise.** It records what was true at the time,
   which alternatives were on the table, and what each one cost - so that a later reader
   who wants to reopen the question can see whether their new argument is actually new.
3. Numbers are permanent and are never reused or renumbered. Statuses are `proposed`,
   `accepted`, `superseded by NNNN` and `deprecated`.
4. A superseded ADR is never deleted. Its Status line is updated to name its successor
   and nothing else in it is changed.
5. `docs/adr/README.md` is the index, and every ADR appears in it.

---

## Consequences

**What this buys:**

- **ADRs are cited by ledger entries and by roadmap items.** A ledger entry that closes a
  decision-bearing item names the ADR; a roadmap item constrained by a decision names it
  too. The citation is by permanent number, which is why renumbering is forbidden.
- A refuted idea stays refuted, because the refutation is reachable by subject rather
  than by date or by memory.
- A decision made inside an isolated agent slice becomes visible to every later session,
  which is the only mechanism by which parallel work accumulates rather than diverges.
- A reversal is honest and visible: the superseding ADR must state what changed, and both
  documents survive.

**What this costs, stated plainly:**

- **A decision that is not in an ADR is not settled, and may be re-litigated.** This is
  the sharp edge of the rule and it is intentional. Anyone may reopen an unrecorded
  decision without having done anything wrong, and the cost of that falls on whoever
  failed to record it. Conversely, an accepted ADR is binding: reopening it requires a
  new ADR that supersedes it, not an argument in a session transcript.
- Writing the Context section takes real effort at exactly the moment when the decision
  feels obvious and the effort feels unnecessary. That feeling is the failure mode - a
  decision feels obvious to the person who just made it and to nobody else, including
  that same person later.
- The index must be maintained by hand, and an ADR missing from it is effectively
  invisible. Step 3 of the add procedure in `docs/adr/README.md` exists for this.

**What must be revisited if a premise changes:** if work stops running in parallel
isolated slices, force 1 in the Context weakens - but the rediscovery cost that motivates
this ADR does not depend on that force, so the decision stands regardless.
