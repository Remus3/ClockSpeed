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
