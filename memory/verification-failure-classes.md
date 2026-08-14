---
name: verification-failure-classes
description: Ways a verification can look convincing and prove nothing, each with the mechanism behind it.
metadata:
  type: reference
---

Failure classes for verification, each with its MECHANISM. Before asserting external state
- a key is valid, a process is dead, a file is missing, a thing is broken - verify it live
against the source of truth rather than a stale doc or another agent's output.

- **A filed count is a hypothesis, not a fact.** It was true when written, against a set
  the writer did not record. Filed counts have been wrong by an order of magnitude, and
  rows have refuted their own author. Re-derive every count from the artifact before acting
  on it.
- **Check a row's AGE before building on it.** A row filed months ago may describe code
  that no longer exists, so the work it implies is already done or already impossible. Age
  is cheap to read and expensive to ignore.
- **A resolver fix is not a consumer fix.** A falling residual count hides a private copy in
  a consumer that never adopted the fix - the shared path got better while the local one
  did not. Diff the CONSUMER's artifact, not the resolver's.
- **Proving your change happened is not proving it matters.** Instrumentation showing the
  code path executed says nothing about whether the downstream output changed. Verify the
  output.
- **An empty grep is a claim about your PATTERN, not about the codebase.** Different
  delimiters, different casing, a line break inside the token, or a computed name all
  produce a clean empty result. Vary the pattern before concluding absence.
- **A decline reason goes stale before the count does.** The blockers recorded against a
  past rejection may answer a proposal nobody is making now. Re-read WHY something was
  rejected before citing the rejection as settled.
- **A caveat stated in chat is not a caveat in the artifact.** The chat scrolls away and the
  artifact is what the next reader acts on. If a qualifier changes how a result should be
  used, it goes IN the deliverable.
- **A guard can be green while self-excusing.** Guards commonly skip files they cannot
  handle, which are disproportionately the files most in need of checking - so the guard is
  green precisely on its blind spot. Read what the guard skips, not just its exit code.
- **A detached background process can return a real PID and exit code zero while doing zero
  work.** The launch succeeded; the work never started, or died immediately after. Assert
  the WORK PRODUCT - the file written, the port bound, the row inserted - never the launch.
- **A syntax checker can be blind on certain file shapes.** It may parse a subset, bail
  early, or treat an unfamiliar construct as opaque and pass it. Verify the checker actually
  parses the construct you care about before trusting a clean exit.
- **Using the implementation as its own test oracle proves nothing.** A test that asks
  `redact(x) != x` to decide whether `x` holds personal data inherits every blind spot the
  redactor has: where the redactor is blind, the test reports clean, and it does so most
  confidently on exactly the inputs the redactor fails. The oracle must be derived
  INDEPENDENTLY of the code under test. Generalizes past redaction to any is-it-valid,
  is-it-sanitized or is-it-escaped check that calls the sanitizer to find out.
- **A working-tree grep is not a repository grep.** `git ls-files | xargs grep` enumerates
  tracked PATHS but reads WORKING-TREE contents, so it reports clean the moment a file is
  edited and says nothing about what git actually stores. Scrubbing something and then
  grepping that way produces convincing evidence for a claim you have not tested. Use
  `git grep <pattern> HEAD`, or `git log -S`, when the question is about the repository
  rather than the checkout - and state which of the two you checked.
- **Per-file green is not repo-wide green.** Linters, formatters and type checkers are
  routinely run against the files a change touched, while CI runs them across the tree. The
  per-file pass is a different and weaker claim, and it is the one most likely to be
  reported as "all clean". Run the command CI runs, with CI's scope.
- **A stale bytecode cache can make a correct tree look broken.** Python stores a
  source mtime at one-second granularity in the `.pyc`, so an edit landing in the same
  second as the cache write AND preserving the file size is not detected: the interpreter
  serves the old module while the source on disk is right. It presents as a genuine test
  failure against code that is provably correct. Clear `__pycache__` before believing a
  surprising red.

Ground truth when the tool pipe is unreliable is `git status`, Edit success or failure, test
output written to a FILE, and an explicit exit sentinel - not raw stdout, which can replay
stale or out-of-order results.

Related: [[test-quality-failure-classes]], [[hook-presence-is-not-hook-firing]],
[[orchestrated-multi-agent-is-the-default]].
