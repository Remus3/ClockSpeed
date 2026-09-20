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

## The main session is the operator's window, not a log

Every session is CAVEMAN-ULTRA in the main transcript. The operator watches several
projects side by side, so prose there costs attention on both ends and buries the thing
being decided.

- **The CHECKLIST is BATCHED, not continuous.** Refined by the operator 2026-09-20 after
  a session emitted one per finding. Print it at exactly three moments: at SESSION START,
  once at least FOUR tasks have completed since the last one, and as the PRE-FLIGHT of
  `/done` before clearing. Also print it on demand when the operator OR an agent asks for
  status - that answer is the checklist, never prose. It carries what is DONE this
  session, what is STILL OPEN, and what was ADDED or RETRACTED as things moved.
- **Do NOT narrate an item as it finishes**, and do not write a session review, a summary
  of what was learned, or commentary on the work. Finishing a task is not an event worth a
  turn. Let the tool-call labels carry it and fold the result into the next batched
  checklist.
- **Every action, bash call, tool call and agent dispatch carries an expected duration in
  its label**, e.g. `(22m)`. The panel shows elapsed only, so the estimate is the only
  thing that makes a wait legible.
- Narration belongs in a tool call's `description` field, which renders as the visible
  label and costs nothing in the response body. Long findings go to a file, a ledger entry
  or an item note - never into chat.
- SUBAGENT FIRST. The main session holds the plan and the seams, not the implementations.
- Keep the chat session's own context in mind: run `/done` and clear when appropriate,
  unless running in the background headless lane.

Related: [[full-authority-adjudicate-do-not-ask]],
[[orchestrated-multi-agent-is-the-default]].
