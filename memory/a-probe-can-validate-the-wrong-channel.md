---
name: a-probe-can-validate-the-wrong-channel
description: A check that validates one channel while its consumer reads another proves nothing, and a harness that cannot reach the second channel cannot grade it.
metadata:
  type: reference
---

**A probe that validates one channel while the consumer reads another proves nothing.** Ask
which channel the DECISION is taken from, and validate that one.

Measured on this project, CS-703. The tier-0 hooks resolved an interpreter with a probe, then
took every gate decision from the process exit status. The first repair made the probe demand
that the candidate WRITE BACK a computed token - sound-looking, and it closed the reported
defect. It was still a fail-open, because stdout was never the channel that decided anything.
A wrapper that forwards stdout faithfully and drops the exit status answered the probe with the
exact token and turned the character-set gate, the secret scan, the message checks and the
whole-suite pre-push run into no-ops at once. Two ordinary shapes do it and neither knows the
token: a POSIX wrapper ending in `| cat`, because a pipeline's status is its LAST command's, and
a Windows `.cmd` wrapping its body in `setlocal` / `endlocal`, because `endlocal` resets
ERRORLEVEL.

**The corollary is about the harness, and it is the expensive half.** Both the suite and the
merger's independent oracle graded that build GREEN while four escapes were live. Neither was
careless - both substituted `true`, `:` and `echo`, which fail at the stdout comparison and
therefore NEVER REACH the exit-code question. **A harness that cannot reach a channel cannot
grade it, and its green is silence about that channel rather than evidence.** Two independent
harnesses agreeing meant only that they shared a blind spot; see
[[verification-failure-classes]] on agreement not being evidence.

**How to use this.** Before trusting any pre-flight check - an interpreter probe, a health
check, a capability sniff, a dependency assertion - write down which observable the real
consumer reads, and confirm the probe reads THAT. Then build one candidate that is correct on
the probed channel and wrong on the consumed one, and watch the check pass. If you cannot
construct that candidate, you have not established the probe is sound; you have established
that you did not try.

**A second instance of the same shape, same session.** The same hooks proved WHICH interpreter
they had and never proved THE PROGRAM ARRIVED. A heredoc above one shell's 4096-byte delivery
limit arrived as zero bytes, the interpreter read an empty program - valid, exits 0 - and the
hook reported success with empty stderr. The fix is the same principle: make the program prove
it ran, rather than enumerating the ways delivery can fail. See
[[hook-presence-is-not-hook-firing]], which is this lesson one level up.
