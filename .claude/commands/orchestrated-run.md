---
description: Set up the section 5 shape for a named unit of work - disjoint decomposition first, dispatch, adjudicate with an agent that did not produce the work, then an adversarial refutation pass.
argument-hint: <unit of work, e.g. CS-012 save header parser>
---

# /orchestrated-run - the default session shape

## WHO RUNS THIS - ONE SUB-AGENT, NEVER THE MAIN SESSION

FLEET-KIT v10, carried at v11 (MAIN's 2026-10-08 08:39 ORDER, item 4; the FLEET-COMMON banner; CS-1282, CS-1287):
the main session does NOT run these steps. It dispatches the WHOLE of this command -
every step below, with this file's text and the arguments as the prompt - to ONE
sub-agent (the Agent tool, in the background by default), waits for that sub-agent's
completion notification, and relays ONLY its final line, the command's one-line result,
to chat. The sub-agent runs every step itself and never re-dispatches the whole command.
The kit's PreToolUse hook `ops/fleet_kit/fleet_subagent_first.py` denies Bash,
PowerShell, Read, Edit, Write, Grep, Glob and NotebookEdit in the main thread once its
mode is deny, so a step run there stops at its first tool call.

Unit of work: $ARGUMENTS

Orchestrated, multi-agent, self-adjudicating, self-adversarial is the DEFAULT shape of every
session, not an escalation. Choosing it needs no justification; DEPARTING from it does. The
only exception is genuinely trivial work - a one-line cosmetic edit, a doc typo, a single
string, a conversational answer. SUBSTANCE decides, not file count: a one-file engine change
is substantive, a five-file rename is not.

## Phase 0 - recall before building

- [ ] Query the memory store with the task IN YOUR OWN WORDS, through the projection tool
      rather than a raw recall. Also grep `docs/LEDGER.md` and the `Settled` section of
      `CLAUDE.md`.
- [ ] If a settled or ledger hit says this work is CLOSED, REFUTED or shipped, **STOP and
      report that instead of building it.** This is the entire point of the store.
- [ ] Read a decline reason before citing it. A decline reason goes stale before the count
      does - the blockers may answer a proposal nobody made.

## Phase 1 - spec first, then act

- [ ] Dispatch `planner`. It emits the spec BEFORE any code exists.
- [ ] Verify the spec against GROUND TRUTH before a single file is scaffolded: grep every
      cited `file:line`, list every cited file, probe every cited endpoint, read `git log`.
      **Never scaffold against an assumed API surface.**
- [ ] Confirm the acceptance criterion is TESTABLE. "Works correctly" is not a criterion.

## Phase 2 - decompose into DISJOINT slices BEFORE any work starts

- [ ] Every slice declares an EXACT file write-list. No globs, no "and related files".
- [ ] Every slice declares the seams it CONSUMES and the seams it PUBLISHES.
- [ ] **Check disjointness as a PRECONDITION rather than hoping for it.** Print the union of
      all write-lists and assert no path appears twice. If two slices need the same file,
      merge them, or extract the shared file into its own slice that runs FIRST and
      publishes a seam.
- [ ] Sequence any slice that must precede another, and say why. A seam consumer never
      starts before its producer publishes.
- [ ] Confirm no slice touches a frozen file from `CLAUDE.md` without an adjudicator grant.
- [ ] Record the decomposition before dispatching. An undeclared write-list is a merge
      conflict already.

## Phase 3 - dispatch

- [ ] One `builder` per slice, worktree-isolated wherever it writes.
- [ ] Each builder receives: its slice goal, its EXACT write-list, its seams, its tier, its
      acceptance criterion. Nothing else - the merger holds the plan, not the
      implementations.
- [ ] Background long-running work so the operator can interject on any turn. **The main
      thread reads, plans, dispatches, merges and reports. It does NOT run long builds, long
      suites or wide sweeps inline.**
- [ ] **Never fabricate or predict a pending agent's result.** If the operator asks before it
      lands, say it is still running.
- [ ] Relay what matters from each agent's report - the operator does not see it.

## Phase 4 - verify, independently

- [ ] Dispatch `verifier`. It re-runs the suite itself and reports the counts IT observed.
- [ ] **Never trust a subagent's claim about test counts, green CI or file existence.** List
      the cited file, re-run the suite, read the exit code.
- [ ] A builder's own green report is an input to verification, never a substitute for it.

## Phase 5 - adjudicate with an agent that did not produce the work

- [ ] Dispatch `adjudicator` with the criteria stated IN PRIORITY ORDER, before it sees the
      candidates.
- [ ] **The agent that produced a thing never grades it.** If only one candidate exists, the
      adjudicator still checks it against the criteria and the non-negotiables - it is not a
      rubber stamp.
- [ ] Ask it explicitly for the COMMON-MODE risk: what shared doc, fixture or assumption do
      the candidates depend on that neither of them tests?

## Phase 6 - adversarial refutation pass

- [ ] Dispatch `adversary` instances with DISTINCT LENSES - correctness, security and
      privacy, does-it-reproduce, resource lifetime, scope and siblings. **Not N identical
      skeptics.** Diversity catches failure modes redundancy cannot.
- [ ] Each defaults to REFUTED when uncertain. "Could not break it" is NOT REFUTED, never
      "confirmed".
- [ ] **Agreement between two agents is not evidence.** Two agents deriving from the same
      stale doc or the same fixture are wrong the same way. If two agree, go find their
      shared input and test THAT.
- [ ] Adversarial verification is the default, not the exception - including for your own
      single-thread edits. Tier 0 is exempt.

## Phase 7 - merge and report

- [ ] Merge slice by slice. Re-run the tier-appropriate suite AFTER the merge - slices that
      passed independently can fail together at the seam.
- [ ] Report: what each slice delivered, the verifier verdict, the adjudicator decision plus
      the runner-up's best argument, every adversary verdict, and every UNRESOLVED item.
- [ ] Anything unverified is labelled unverified. Do not round an uncertainty up to a claim.
- [ ] Finish with `/done`.
