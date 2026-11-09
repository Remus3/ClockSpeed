---
name: feedback-model-and-effort-fit-the-task
description: Pick the Claude model and reasoning effort to fit each task, run, command, sub-agent and headless spawn
metadata:
  type: feedback
---
Rule: always utilize the appropriate Claude model and effort for the tasks, runs, commands and so on.

Operator, 2026-11-08, verbatim: "always utilize appropriate claude model and effort for the tasks/runs/commands/etc"

**Why:** Cost and quality. A top model at max effort on trivial work (acks, triage, lookups) wastes spend; a weak model at low effort on code changes, design, reviews or rulings gives poor results.

**How to apply:** Set `model` and `effort` deliberately on every Agent spawn, workflow agent and fleet_headless spawn. Use a cheap/fast model with low effort for acks, inbox triage, mechanical edits and searches. Use a stronger model with higher effort for code changes, debugging, reviews and adjudication. Consistent with FLEET-COMMON 10 (sonnet unless the note orders code changes; effort low for acknowledgements).
