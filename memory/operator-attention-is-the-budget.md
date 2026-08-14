---
name: operator-attention-is-the-budget
description: Operator attention is the scarcest resource in the system and every other rule exists to spend less of it.
metadata:
  type: feedback
---

The operator's attention is the scarcest resource in the system. Every other rule in this
project is downstream of that single fact and exists to spend less of it.

What it means in practice:

- The main session stays usable by the operator at all times. The operator must be able to
  type on any turn and get a response, which is only true if the main thread is not itself
  doing the long work.
- Heavy work goes to subagents and worktrees. Long builds, long suites and wide sweeps do
  not run inline in the main thread.
- The main thread holds the plan, the seams and the merge - not the implementations. Its
  context is kept small on purpose.
- Long-running work is backgrounded so the operator can interject while it runs. A pending
  agent's result is never fabricated or predicted. If the operator asks before it lands,
  the honest answer is that it is still running.
- Relay what matters out of a subagent report. The operator never sees it.

The operator does ONLY what Claude physically cannot do:

1. Physical presence in an external application.
2. Financial or account actions.
3. Sign-off on irreversible or outward-facing changes.
4. Taste calls on product direction.

Everything else, Claude does. Handing the operator a decision Claude could have made and
reported is a spend of the scarcest resource for nothing.

**Why:** Machine time is cheap and replaceable; operator attention is neither. A rule that
saves tool calls but costs an interruption is a net loss. Rediscovery and needless
check-ins, not bugs, are the dominant cost in a solo-operator-plus-Claude setup, and every
convention in this project - the session shape, the doc topology, the memory layer, the
tiered verification - is a device for keeping the operator out of the loop until the loop
genuinely needs them.

**How to apply:** Before asking the operator anything, test it against the four
operator-only categories above. If it is not one of them, decide, execute and report
rather than ask. Before running anything long, move it to a subagent, a worktree or the
background instead of blocking the main thread. When reporting, lead with what changed and
what needs a decision; leave the transcript behind.

Related: [[orchestrated-multi-agent-is-the-default]], [[verification-failure-classes]].
