---
name: orchestrated-multi-agent-is-the-default
description: Orchestrated, multi-agent, self-adjudicating, self-adversarial is the default session shape, not an escalation.
metadata:
  type: feedback
---

Orchestrated, multi-agent, self-adjudicating and self-adversarial is the DEFAULT shape of
every session. It is not an escalation reserved for big work. Choosing it needs no
justification; departing from it does.

The four properties, each load-bearing:

- **Orchestrated.** One merger holds the plan and the merge. Work is decomposed into
  disjoint slices BEFORE any of it starts. The merger holds the plan and the seams, not
  the implementations.
- **Multi-agent.** Slices run in parallel on non-overlapping files, worktree-isolated
  wherever they write. Disjointness is a precondition checked before dispatch, not a hope.
- **Self-adjudicating.** A distinct agent picks between competing outputs against stated
  criteria. The agent that produced a thing NEVER grades it.
- **Self-adversarial.** Every finding and every "done" claim gets an independent pass whose
  job is to REFUTE it, and that pass defaults to REFUTED when uncertain.

The only exception is genuinely trivial work: a one-line cosmetic edit, a doc typo, a
single string, a conversational answer. **Substance decides, not file count.** A one-file
engine change is substantive and gets the full shape. A five-file rename is not.

Two rules about evidence that fall out of this:

- Refuters get distinct LENSES - correctness, security, does-it-reproduce, resource
  lifetime - rather than N identical skeptics. Diversity catches failure modes that
  redundancy cannot.
- **Agreement between two agents is not evidence.** Two agents derived from the same stale
  doc or the same fixture are wrong in exactly the same way, and their agreement reads as
  confirmation while adding zero information.

**Why:** A single thread grading its own work is the cheapest possible verification and the
weakest. The shape exists because the expensive failures are not typos - they are confident
wrong answers that nobody was assigned to attack, and stale premises that every agent
inherited at once. It also keeps the main session responsive, which is the point of
[[operator-attention-is-the-budget]].

**A proven-disjoint write-list does NOT make worktrees optional.** Learned by skipping them
after mechanically proving nine slices shared no path: the proof bounds where agents
DECLARE they will write, and bounds nothing about TRANSIENT mutation. A builder doing TDD
properly needs to watch a test fail, and the cheapest way to watch a test fail is to break
something - so builders reach outside their write-list, break a file, observe the red, and
restore it. Two did exactly that in one session, on a tracked source file and on another
slice's test module. Both restored correctly and neither left residue; both nonetheless
turned an unrelated suite red while a verifier was measuring it, and the verifier came
within one careful reproduction of filing it as a genuine phase defect.

So: isolate by worktree wherever an agent WRITES, and when a shared tree is genuinely
warranted, state the rule explicitly in the dispatch - every break-revert-observe cycle
happens on a scratchpad COPY, never on a file in the repo. An agent told only "do not write
outside your list" will still break a file it intends to restore, because it does not
classify that as writing.

**How to apply:** At session start, decompose into disjoint slices before writing anything,
then dispatch. Never let a builder verify its own slice. When spawning refuters, name each
one's lens explicitly in its prompt. Treat concurring agents as one source, not two, and
re-derive the shared premise instead. Never trust a subagent's claim about test counts,
green CI or file existence - probe it directly.

Related: [[operator-attention-is-the-budget]], [[verification-failure-classes]],
[[test-quality-failure-classes]].
