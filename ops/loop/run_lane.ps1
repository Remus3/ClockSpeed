# run_lane.ps1 - the detached runner for one headless worker, spawned hidden by
# ops/loop/lane_launcher.py. It pipes the prompt file to the CLI on stdin, so
# there is no command-line quoting risk and no length ceiling on the prompt.
#
# 7-BIT ASCII, LF LINE ENDINGS, NO BOM, AND THAT IS A MECHANISM RATHER THAN A
# HOUSE STYLE. Windows PowerShell 5.1 ANSI-decodes a .ps1 with no BOM, so a
# UTF-8 em-dash inside a double-quoted string arrives as a byte the tokenizer
# treats as a string terminator and the whole script fails to parse - a fault
# invisible to anyone reading the file. Use a spaced hyphen for a clause break.
# tests/test_lane_launcher.py asserts this on the BYTES.
#
# EVERY EXIT IS WRITTEN DOWN, AND THAT IS THE WHOLE SHAPE OF THIS FILE.
# MEASURED across two nights: thirteen cycles left a log holding the "lane
# start" header and nothing else - 134 bytes, no exit line - and a log that
# stops after its header cannot be told apart from a worker still running. The
# header is therefore written BEFORE anything that can refuse, and everything
# that follows sits inside a try/finally whose finally writes the exit line.
# tests/test_lane_runner_script.py grades this by RUNNING this script against a
# PATH with no CLI on it, because a grep for "finally" passes on a script whose
# try does not enclose the thing that throws.
param(
  [Parameter(Mandatory)][string]$PromptFile,
  [Parameter(Mandatory)][string]$Cwd,
  [Parameter(Mandatory)][string]$Log
)

# Native stderr must not kill the lane. Everything goes to the log instead.
$ErrorActionPreference = "Continue"

# RIDE THE SUBSCRIPTION LOGIN, NEVER AN INHERITED API KEY. MEASURED: a lane
# spawned correctly and died three seconds later on "Credit balance is too low",
# because the key is set at MACHINE scope, a spawned lane inherits it, and the
# CLI prefers it over the browser login. That was latent for as long as the key
# had credit and it fails the whole lane the moment it does not. Cleared for
# THIS process only - the machine-wide variable is left alone, because other
# consumers on this box are none of this script's business.
$env:ANTHROPIC_API_KEY = $null

# Wait long enough for the worker's background subagents to finish before the
# CLI terminates them. MEASURED: at the default ceiling a verifier was still
# re-running a suite when the CLI killed it, and the worker exited 0 having
# committed nothing - a whole pass lost. Forty minutes is ample for this
# repository's suite plus a re-read, while staying bounded so a truly wedged
# task still exits and reports rather than hanging forever.
#
# KEPT AFTER CS-1108 AS DEFENCE IN DEPTH, not because the switch below needs it.
# With background tasks disabled a subagent runs in the foreground and this cap
# is moot. It stays because the disable switch could not be tied to its gate in
# the CLI statically - it was proved only by a probe - so if a later CLI ignored
# the switch, background subagents would still be waited for rather than killed.
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = "2400000"

# CS-1108 - NOTHING THE WORKER RUNS IS BACKGROUNDED, AND A LONG COMMAND SURVIVES.
# MEASURED 2026-09-16 on the lane's own CLI: the ceiling above covers background
# SUBAGENTS and workflows only. A background SHELL is killed about five seconds
# after the final reply - the CLI's debug line reads "print wind-down: killing
# background shell ... after 5000ms grace". Every cycle that backgrounded a suite
# and then ended its turn lost it; three cycles in one day ended commit=no with
# their suite logs stopping at 8% and 20%.
#
# THE SWITCH removes run_in_background from the Bash and subagent tools, so a
# command runs in the foreground to completion. Probed: a 45-second command that
# the default kills completed with the switch set.
#
# THE TIMEOUTS ARE ITS REQUIRED COMPANION, or the fix trades one kill for another:
# a foreground Bash call is capped at ten minutes by default, while a whole-tree
# run was measured from 8:49 to about fifteen minutes and the frozen pre-push
# hook runs the whole suite. Forty minutes covers the slow end more than twice
# over and stays bounded, so a wedged command still dies and the cycle reports.
# Probed with all three set: an eleven-minute foreground command completed, exit 0.
# The effective ceiling is the larger of the two timeouts, so both are raised.
#
# ALL SET BEFORE THE INVOCATION, IN THIS PROCESS, which the CLI child inherits.
# tests/ops/test_lane_background_tasks.py reads the child's environment by value.
$env:CLAUDE_CODE_DISABLE_BACKGROUND_TASKS = "1"
$env:BASH_MAX_TIMEOUT_MS = "2400000"
$env:BASH_DEFAULT_TIMEOUT_MS = "2400000"

# THE MODEL COMES FROM ops/loop/config.json, READ VIA $PSScriptRoot AND NOT THE
# WORKING DIRECTORY. This runner always lives in the MAIN tree, while $Cwd is a
# fresh worktree checkout that does not carry a gitignored config - reading it
# relative to the cwd would find nothing on every real fire. A known-good model
# is set FIRST and every read or parse fault keeps it, because a lane must never
# fail to spawn over a config read.
#
# THIS STAYS AHEAD OF THE HEADER because it cannot throw: it carries its own
# catch and every fault keeps the fallback. Nothing else above the header can
# refuse, which is what makes the header reachable on every path.
$model = "claude-opus-5"

# THE EFFORT IS RESOLVED THE SAME WAY AND VALIDATED HARDER, and the asymmetry is
# deliberate. An unrecognised --model is rejected by the CLI, so a bad one fails
# loudly. An unrecognised --effort is NOT: measured 2026-09-16, the CLI prints
# "Unknown --effort value ... ignoring it and using the default effort" and runs
# on. A typo would therefore produce a lane running at DEFAULT effort while the
# header line below recorded the value nobody applied - a log that lies about
# the run it describes. So the value is checked against the five documented
# levels here, and anything else falls back rather than travelling to the CLI.
$effort = "high"
$validEfforts = @("low", "medium", "high", "xhigh", "max")
try {
  $cfgPath = Join-Path $PSScriptRoot "config.json"
  if (Test-Path -LiteralPath $cfgPath) {
    $cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
    if ($cfg.executor_model) { $model = [string]$cfg.executor_model }
    if ($cfg.executor_effort) {
      $wanted = ([string]$cfg.executor_effort).Trim().ToLowerInvariant()
      if ($validEfforts -contains $wanted) { $effort = $wanted }
    }
  }
} catch {
  # Any read or parse fault keeps the fallback model and effort set above.
}

"lane start $(Get-Date -Format s) cwd=$Cwd model=$model effort=$effort prompt=$PromptFile" |
  Out-File "$Log" -Encoding utf8

# A DEFINED WORD RATHER THAN AN EMPTY ONE. An exit line reading "code=" says
# nothing, and a reader cannot tell it from a truncated write; "none" records
# that the worker never got far enough to have a code. Same reasoning as the
# launcher's REASON_UNSPECIFIED.
$code = "none"
try {
  # RESOLVED, NOT ASSUMED, and inside the try. This is a TERMINATING failure -
  # it used to run above the header, so a box with no CLI on PATH produced no
  # log at all and the launcher blamed the runner for exiting early.
  $claude = (Get-Command claude -ErrorAction Stop).Source

  # TERMINATING TOO, deliberately. A worker running in the wrong directory is
  # worse than a lane that refuses: $Cwd is the worktree that keeps a lane off
  # the main tree, and a non-terminating Set-Location would leave the CLI
  # running wherever this process happened to start.
  Set-Location -LiteralPath "$Cwd" -ErrorAction Stop

  # `*>> $Log` WROTE THE WORKER'S OUTPUT AS UTF-16LE. On Windows PowerShell 5.1
  # the redirection operators use the shell's default Unicode encoding, while
  # the header line above is UTF-8. MEASURED on a real 4298-byte lane log:
  # UTF-8 for the first 119 bytes, then UTF-16LE for the remaining 4179 - 2066
  # NUL bytes in one file. Anything reading it as one encoding got interleaved
  # nulls for the half that mattered.
  #
  # `*>&1 |` merges every stream into the pipeline so Out-File sets the encoding
  # for all of them, which KEEPS the "native stderr must not kill the lane"
  # property above: the streams are still folded into the same file, they are
  # just written as UTF-8 now.
  #
  # CS-1178 - `--output-format json`, so the run ends in ONE result object the
  # driver can read. In the default text mode a usage-limit refusal (exit 1,
  # one turn, zero cost, an error flag, api_error_status 429) and a crashed
  # executor are the same five seconds and the same exit code, and the driver
  # recorded the refusal as a run that happened. The object is what separates
  # them; see `_worker_result` in ops/loop/queue_loop.py.
  #
  # CAPTURED, then written in THIS order: the result's text as readable lines,
  # then everything the run emitted (the JSON line and any stderr), then the
  # exit line below. A person reading the log still sees the worker's words
  # rather than one escaped JSON string, and the JSON stays at the tail where
  # the driver reads it. `claude -p` writes nothing until it finishes, so
  # capturing costs no live output the log ever had.
  #
  # RESIDUAL, NAMED RATHER THAN FIXED: everything is held in $out until the CLI
  # exits, so a worker the driver KILLS at its timeout leaves none of its
  # stderr in this log - the kill unwinds nothing, and the write below never
  # runs. Streaming would keep it, at the cost of the ordering above.
  $out = @(Get-Content -LiteralPath "$PromptFile" -Raw |
    & $claude -p --model $model --effort $effort --output-format json --dangerously-skip-permissions *>&1)

  $code = $LASTEXITCODE

  foreach ($item in $out) {
    $text = [string]$item
    if (-not $text.TrimStart().StartsWith("{")) { continue }
    try {
      $parsed = $text | ConvertFrom-Json -ErrorAction Stop
      if ($parsed.type -eq "result" -and $null -ne $parsed.result) {
        [string]$parsed.result | Out-File "$Log" -Append -Encoding utf8
      }
    } catch {
      # Not a result object; it is still written whole just below.
    }
  }
  $out | Out-File "$Log" -Append -Encoding utf8
} catch {
  # THE TYPE AND THE ERROR ID, NEVER $_.Exception.Message. An error id is
  # symbolic - "CommandNotFoundException,Microsoft.PowerShell.Commands.GetCommandCommand"
  # - and is path-free by construction, while a message routinely embeds the
  # path it failed on and this log is written unattended (CLAUDE.md
  # non-negotiable 12). The same rule the Python half obeys in `_fault`.
  "lane fault $(Get-Date -Format s) type=$($_.Exception.GetType().Name) id=$($_.FullyQualifiedErrorId)" |
    Out-File "$Log" -Append -Encoding utf8
} finally {
  # EVERY PATH OUT, including a terminating fault above. The one death this
  # cannot cover is TerminateProcess - a taskkill /F unwinds nothing - and that
  # one is written by whoever fired the kill: see `note_worker_abort` in
  # ops/loop/lane_launcher.py.
  "lane exit $(Get-Date -Format s) code=$code" |
    Out-File "$Log" -Append -Encoding utf8
}
