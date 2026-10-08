---
description: The TDD loop - failing test first, watch it fail for the RIGHT reason, minimum implementation, sibling-case grep with a test for each, then the tier-appropriate suite.
argument-hint: <feature or bug, e.g. CS-021 byproduct loop in ratio solve>
---

# /tdd - test-driven development loop

## WHO RUNS THIS - ONE SUB-AGENT, NEVER THE MAIN SESSION

FLEET-KIT v10 (MAIN's 2026-10-08 08:39 ORDER, item 4; the FLEET-COMMON banner; CS-1282):
the main session does NOT run these steps. It dispatches the WHOLE of this command -
every step below, with this file's text and the arguments as the prompt - to ONE
sub-agent (the Agent tool, in the background by default), waits for that sub-agent's
completion notification, and relays ONLY its final line, the command's one-line result,
to chat. The sub-agent runs every step itself and never re-dispatches the whole command.
The kit's PreToolUse hook `ops/fleet_kit/fleet_subagent_first.py` denies Bash,
PowerShell, Read, Edit, Write, Grep, Glob and NotebookEdit in the main thread once its
mode is deny, so a step run there stops at its first tool call.

Target: $ARGUMENTS

All feature work and all bug fixes follow this loop. No exceptions.

## 0. Confirm the API surface exists BEFORE writing the test

- [ ] Grep to confirm EVERY method, field and data shape the test will use ACTUALLY EXISTS.
- [ ] Cite `file:line` for each one. **Never scaffold against an assumed API.**
- [ ] **An empty grep is a claim about your PATTERN, not about the codebase.** Vary the
      delimiters and the casing before concluding something is absent.
- [ ] Name the tier now: 0 cosmetic, 1 local logic in one module, 2 schema / engine / core
      algorithm / version bump / public interface.

## 1. Write the FAILING test FIRST

- [ ] Characterization test for a feature, regression test for a bug.
- [ ] Assert on a COMPUTED quantity rather than a data-fragile cross-item comparison.
- [ ] **Assert what IS there, not what is absent.** A negative assertion rules out without
      pinning down: "field X is absent" passes for the correct output AND for a totally
      collapsed one.
- [ ] If you need a spy, use a RECORDING spy and assert on the record. **A raising spy is
      vacuous under fail-soft code** - if production catches broad exceptions, a spy raising
      `AssertionError` proves nothing because the guard passes both ways.
- [ ] Build fixtures from real captured behaviour, hand-authored synthetic registries, or
      first-party reference material - **never from the implementation's own assumptions.**
      Fixtures built parallel to the implementation stay green straight through the real
      defect.
- [ ] Fixtures are small, synthetic and hand-authored in the repo. Never a slice of real game
      data, never a save file, never anything extracted from the install.
- [ ] Test must run on a machine with NO game installed.
- [ ] 7-bit ASCII in the test file, and no account name, account id, world name, machine
      name or home path anywhere in it.

## 2. Watch it FAIL, and confirm it failed for the RIGHT REASON

- [ ] Run ONLY the new test. Record the command and the exit code.
- [ ] **Quote the failure line.** Read it. Is it failing because the behaviour is missing, or
      because of an import error, a typo, a missing fixture, or a wrong path?
- [ ] **A test that passes before the fix is a test about nothing.** If it passed, the test
      is wrong - go back to step 1. Do not proceed.
- [ ] A failure for the wrong reason is also a stop. Fix the test, re-run, quote the new
      failure.

## 3. Implement the MINIMUM that makes it pass

- [ ] Smallest change that satisfies the assertion. No speculative generality, no adjacent
      refactor, no "while I am here".
- [ ] Stay inside the declared write-list if you are running as a slice.
- [ ] When adding a required field to a dataclass, **APPEND IT AT THE END WITH A DEFAULT.** A
      mid-class required field breaks every existing positional construction.
- [ ] Exact rational arithmetic in the solve path - `fractions.Fraction` end to end. Floating
      point drift in a ratio calculator is a CORRECTNESS BUG, not a rounding nuisance.
- [ ] Unknown game content is flagged and skipped, never fatal, never silently wrong.
- [ ] Re-run the test. It must now pass. **Do not re-read the file you just edited to confirm
      the edit** - Edit fails loudly.

## 4. Grep for EVERY sibling case sharing the same root cause - add a test for each

- [ ] This step is not optional and it is where most of the value is. A fix applied to one
      call site while three siblings share the root cause is a fix that will be re-reported.
- [ ] Grep by the MECHANISM, not by the symptom string. Vary delimiters and casing.
- [ ] **A resolver fix is not a consumer fix.** A falling residual count can hide a private
      copy in a consumer that never adopted the fix. Diff the CONSUMER's artifact.
- [ ] Add a test per sibling. Watch each new test fail first, for the right reason.
- [ ] List every sibling found and every one you deliberately excluded, with the reason.

## 5. Run the tier-appropriate suite

- [ ] From the REPO ROOT with an EXPLICIT target directory. Never a bare recursive invocation
      from the root - it can sweep runtime state directories and destroy live locks or data.
      - tier 0: syntax check plus lint on the changed paths.
      - tier 1: `python -m pytest tests/<module> -q`
      - tier 2: `python -m pytest tests -q` plus `python -m mypy clockspeed`, plus restart and
        mirror sync.
- [ ] Run the linter before reporting done. Generated test files have broken CI before.
- [ ] Run the suite ONCE and trust the exit code. Re-run only if you edited since or the tool
      pipe demonstrably glitched. Never prophylactically.
- [ ] Report the exact pass / fail / skipped counts observed THIS run and the exit code.
      Never carry forward a prior or subagent-reported count.

## 6. Adversarial pass before calling it done

- [ ] Every substantive claim gets an independent refutation pass. Tier 0 is exempt.
- [ ] Ask specifically: would this test still pass if the implementation were DELETED?
- [ ] **Proving your change happened is not proving it matters.** Verify the DOWNSTREAM output
      changed, not just that the code path executed.
- [ ] **A mutation that fails to apply looks GREEN.** If a mutant survives, suspect the
      harness before congratulating the test. And a surviving mutant may be an EQUIVALENT
      mutant that cannot change behaviour - swap the mutant, do not weaken the test.
- [ ] **Beating a naive alternative is not soundness.** Derive attacks from the mechanism.
- [ ] **Delete the guard test:** a guard on a non-default call path is untested. If the suite
      stays green without the guard, the guard was never exercised.
