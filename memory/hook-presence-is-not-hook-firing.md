---
name: hook-presence-is-not-hook-firing
description: The four ways a hook can exist and silently do nothing, and the only valid end-to-end test.
metadata:
  type: reference
---

A hook that exists but does not fire is worse than no hook, because it is trusted. Never
treat a hook's presence, or a settings entry naming it, as proof it fires.

**Four confounds to eliminate before concluding anything about a hook:**

1. **Invalid JSON in the settings file.** A single-backslash Windows path inside a JSON
   string makes the file invalid. It never parses, so no hook registers, and nothing warns
   you - there is no error surfaced at the point of failure. Assert the settings file
   parses before trusting any negative result about hooks.
2. **An untrusted workspace.** In a headless run an untrusted workspace silently discards
   the permission allowlist. The symptom is nearly identical to hooks not loading, so the
   two get confused and the wrong fix gets applied.
3. **Path-string keying.** Trust and config keys are per path STRING, not per resolved
   directory. `C:\X`, `C:/X` and `C:/x` are three separate config entries, and different
   modes read different ones. Every worktree path is therefore its own key with its own
   trust state, which is why a gate proven in the main checkout can be absent in a slice
   worktree.
4. **Presence is simply not firing.** The registration can be valid and the hook still not
   run for the action you care about.

**The only valid test is end to end:** stage a real violation, attempt the real action, and
assert it was blocked - HEAD unchanged, exit non-zero, the artifact not written. Reading
the config, seeing the file on disk, or observing that the hook script runs when invoked by
hand all prove something weaker than what is being claimed.

**Hook findings are version-specific and they expire.** Re-measure on the current
toolchain; never inherit a previous session's conclusion about which hook fires when. A
recorded result from an older version is a hypothesis, not a fact.

Defense in depth applies: the git hooks are authoritative, the editor-side hooks are a
convenience layer that catches a violation earlier. Do not let a convenience-layer pass
substitute for the authoritative gate.

**`git commit --no-verify` defeats every local hook, by git's design.** No client-side
hook can prevent it. This is not a defect in the gate and it is not fixable locally - the
mitigation is server-side, which is why the same character-set and secret checks run again
in CI tier 1. A local gate is a fast feedback loop, never the last line of defence.

**Measured 2026-08-13, correcting a widely repeated claim:** CRLF line endings in a hook
do NOT break it on Git for Windows (git 2.53.0.windows.3, GNU bash 5.2.37 msys). A CRLF
hook was executed alongside its LF twin and produced identical stdout and an identical
exit code, and an em dash staged against the CRLF hook was still blocked end to end. So
CRLF is NOT a valid explanation for a hook that appears dead on this toolchain - look at
the other three confounds first. LF remains mandatory because dash, ash and older msys
releases genuinely do fail on a trailing CR, and CI runs these hooks on a POSIX runner.
Recording the correction rather than the folklore is the point: a failure class stated
without its real mechanism sends the next debugger down the wrong path.

Related: [[seven-bit-ascii-is-a-hard-rule]], [[verification-failure-classes]],
[[orchestrated-multi-agent-is-the-default]].
