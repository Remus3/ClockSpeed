---
name: full-authority-adjudicate-do-not-ask
description: Full authority is granted by default in every session shape, so a blocked decision goes to an adjudicator and never to the operator - it removes the operator from the approval path and removes nothing else.
metadata:
  type: feedback
---

# Full authority is granted - adjudicate, do not ask

**Filed 2026-09-13 by operator directive, session 85. Applies to EVERY session shape from
this point forward: interactive, headless, headless laned, and headless laned with
siblings. The operator stated they do not want to repeat it.**

## The grant

Frozen files, full computer use, OBS, computer vision, keyboard, mouse, window control,
browser, research, download, install, terminal and settings access are GRANTED. Restarting
the local server, the companion overlay or the dashboard is allowed even while the game is
running.

The frozen-file route in `CLAUDE.md` section 6 is UNCHANGED in shape and CHANGED in who
grants: the proposal still goes through an adjudicator and the grant is still recorded in
`docs/LEDGER.md` before the edit. The operator is no longer the grantor.

## The rule that replaces asking

**Anything an agent would have marked "I will not do this without operator approval" is
adjudicated instead, and the best recommendation is taken IMMEDIATELY.** No question is put
to the operator to authorise a send or to pick a direction. A blocked decision is a
decision routed to an adjudicator, never a stalled session.

## Why - the operator's own evidence

Across the five projects on this machine and thousands of commits, the acceptance rate on
recommended choices is close to 100 percent, and the operator's answer has been "go ahead"
or "proceed" nearly every time. The asking cost more than it bought. Verbatim: "Just do it,
the operator will intervene if necessary." The operator can type into the main session at
any moment, and that is the correction channel - not a pre-authorisation prompt.

## What it does NOT license

It does not license shipping a red suite, skipping the failing-test-first order, calling a
thing done that its acceptance says is not, or any of the section 3 non-negotiables. The
never-write rule and the zero-language-model rule are invariants, not permissions. It
removes the OPERATOR from the approval path; it does not remove the approval.

## The commit and push clause

Nothing is left uncommitted or unpushed. Batch commits and pushes so CI waits overlap with
other work rather than blocking serially. CI runs only the TIP of a push, so a batch leaves
its intermediate commits untested - size the batch knowing that.

## The status clause

When the operator or an agent asks for status, the answer is the session CHECKLIST inline:
what is DONE this session, what is STILL OPEN, and any additions or retractions. Not prose
about what happened. Every action, bash call, tool call and agent dispatch carries an
expected duration in its label.

Related: [[operator-attention-is-the-budget]], [[orchestrated-multi-agent-is-the-default]].

## The grant is REAFFIRMED AND WIDENED

**Reaffirmed 2026-09-20 by operator directive, session 110.** The operator restated this
grant verbatim in substance and asked, a second time, not to have to repeat it. It carries to EVERY session shape for this repository from this point
forward: interactive, headless, headless laned, headless laned with siblings. Treat a
further restatement as evidence this file was not read.

**The track record is the argument, and the operator made it explicitly.** Across the five
sibling projects and thousands of commits, the acceptance rate of the recommended choice
is close to 100 per cent, and the operator's replies are overwhelmingly continue, go
ahead, proceed. So the expected value of stopping to ask is near zero and its cost is a
whole turn of operator attention. ACT ON THE BEST RECOMMENDATION IMMEDIATELY. The operator
intervenes by typing into the main session, which is always open to them; that is the
control, not a pre-approval gate.

**Anything phrased as "I will not do this without operator approval" is a defect.** Route
it to an adjudicator and take the best recommendation in the same turn. This covers
commits, pushes, frozen files, restarts and sends.

**NOTHING STAYS UNCOMMITTED OR UNPUSHED.** Commit and push as a matter of course. Be smart
about batching for multi-session work so CI waits overlap with other work rather than
blocking it - remembering that CI runs only the TIP of a push, so a batch leaves its
intermediate commits untested.

## The main session is the operator's window, not a log

Output discipline - the batched checklist, the duration labels, subagent-first,
and what never reaches the transcript - is owned by
[[operator-attention-is-the-budget]]. It was relocated there when this file hit its
size budget; nothing was dropped.

Related: [[operator-attention-is-the-budget]], [[orchestrated-multi-agent-is-the-default]].

## ALWAYS DELIVER A REPLY

Operator directive, 2026-09-20. **Never stand silent on the cross-repo channel.** If a
note addresses this tree, asks it a question, names it in a table, or states something
about it, ANSWER IT - including when the answer is "nothing is asked of us and here is why
we agree", and including when another tree has already said this tree owes nothing.

Silence READS AS DISSENT on that channel by its own convention, and a sender cannot tell
an unread note from a considered non-answer. A reply that only confirms costs one note and
removes an ambiguity that would otherwise sit in five inboxes.

**A confirmation is worth sending even when it is not required.** Re-measuring another
tree's published figure from this tree's own disk is a real contribution: it either
corroborates them or catches a divergence nobody could see from inside one tree. Say
plainly which of the two the reply is - and if several trees hashed the SAME artifact,
record that as one measurement with several witnesses rather than as several independent
confirmations.

Related: [[operator-attention-is-the-budget]].
