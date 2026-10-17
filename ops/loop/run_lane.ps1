# run_lane.ps1 - the detached runner for one headless worker, spawned hidden by
# ops/loop/lane_launcher.py. It pipes the prompt file on stdin to the fleet
# kit's spawn command line, and the KIT starts the CLI (CS-1231 slice C, FLEET
# item 10), so there is no command-line quoting risk here and no length ceiling.
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
# PATH with no interpreter on it, because a grep for "finally" passes on a script whose
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

# CS-1282 - THE KIT'S SUB-AGENT-FIRST HOOK IS OFF FOR A LANE WORKER. FLEET-KIT
# v10 wires a PreToolUse hook that denies every guarded tool in a thread with no
# agent id, and it DEFAULTS TO DENY when its mode file is absent - a gitignored
# file a lane worktree never carries. A headless worker has no operator and no
# main pane to keep clear, so the kit's own spawn turns the hook off in every
# child it starts. KEPT HERE AS DEFENCE IN DEPTH now that CS-1231 slice C runs
# the CLI through the kit: set in this process, which the kit and the CLI
# inherit. tests/ops/test_headless_route.py reads it by value.
$env:FLEET_SUBAGENT_FIRST = "off"

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
  # CS-1225 - ROUTED OR REFUSED, BEFORE THE CLI IS EVEN LOOKED UP. The launcher
  # hands this process a copy of its environment routed through the local proxy
  # by ops/loop/headless_route.py; an empty value here means this runner was
  # started some other way, and running the CLI anyway would bill whatever
  # account the box happens to be logged into. Inside the try, after the header,
  # so the refusal still gets its exit line from the finally below. The variable
  # is NAMED, never its value.
  #
  # THE SAME WHOLE-STRING ALLOWLIST as ops/loop/headless_route.py, not a
  # non-empty test: http(s), a loopback host, port 3456, URL-safe segments. A
  # backslash or an at-sign lets two URL parsers disagree on the host, so
  # nothing outside this shape reaches the CLI. Case-sensitive and anchored on
  # \z, so a trailing newline cannot slip past the end anchor.
  $routeShape = '^https?://(127\.0\.0\.1|localhost|\[::1\]):3456(/[A-Za-z0-9._~-]+)*/?\z'
  if ([string]::IsNullOrEmpty($env:ANTHROPIC_BASE_URL) -or ($env:ANTHROPIC_BASE_URL -cnotmatch $routeShape)) {
    "lane refused $(Get-Date -Format s) reason=ANTHROPIC_BASE_URL is empty or outside the loopback allowlist - headless route not established" |
      Out-File "$Log" -Append -Encoding utf8
    $code = 3
    exit 3
  }

  # CS-1231 SLICE C - THE KIT STARTS THE CLI; THIS RUNNER STARTS THE KIT.
  # FLEET item 10 makes the fleet kit's spawn helper the ONLY path that starts
  # the CLI. So this runner runs `python ops/fleet_kit/fleet_headless.py spawn`
  # and the kit resolves the CLI itself (never from the working directory),
  # routes it through the proxy, counts it against the fleet run budget, opens
  # no console window and kills the whole process tree at its timeout.
  #
  # RESOLVED, NOT ASSUMED, and inside the try. This is a TERMINATING failure -
  # the lookup used to run above the header, so a box with nothing on PATH
  # produced no log at all and the launcher blamed the runner for exiting early.
  $python = (Get-Command python -ErrorAction Stop).Source

  # THE MAIN TREE AND ITS VENDORED KIT, from $PSScriptRoot and never the cwd,
  # for the reason the config is read that way above: this runner lives in the
  # MAIN tree. The kit keeps its budget, status and usage files under --root.
  # GetFullPath only normalises a path; it never throws for one that is absent.
  $root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
  $kit = Join-Path $root "ops\fleet_kit\fleet_headless.py"

  # The usage line's label is the log's own name, which names the lane and the
  # run, so one usage line can be joined to its log. Never empty: the kit's
  # command line refuses an empty --note.
  $label = [System.IO.Path]::GetFileNameWithoutExtension("$Log")
  if ([string]::IsNullOrEmpty($label)) { $label = "lane" }

  # TERMINATING TOO, deliberately. A worker running in the wrong directory is
  # worse than a lane that refuses: $Cwd is the worktree that keeps a lane off
  # the main tree, and a non-terminating Set-Location would leave the worker
  # running wherever this process happened to start. --cwd below hands the kit
  # the same directory for the CLI it starts.
  Set-Location -LiteralPath "$Cwd" -ErrorAction Stop

  # TODAY'S VALUES, CARRIED ACROSS AND NOT WIDENED. The direct start passed
  # --dangerously-skip-permissions, which IS the CLI's bypassPermissions mode;
  # the kit's one pass-through flag spells it so. --model and --effort are the
  # values resolved above. The kit adds only narrowing flags of its own (no
  # session persistence, strict MCP config, project and local settings).
  #
  # --timeout IS THE DRIVER'S CYCLE BUDGET, DEFAULT_CYCLE_TIMEOUT_S in
  # ops/loop/queue_loop.py. The direct start had no ceiling of its own - the
  # driver killed the tree at that budget - and the kit's default is one hour,
  # which would kill a worker the driver was still waiting for.
  # tests/test_lane_runner_script.py binds the two by name.
  #
  # --floors-in-hooks: this tree's floors live in hooks, so the kit refuses
  # --bare for it. The prompt goes on STDIN, as it always has; the kit's
  # command line reads stdin when no --prompt-file is given.
  $kitArgs = @(
    "$kit", "spawn",
    "--root", "$root",
    "--code", "CS",
    "--note", "$label",
    "--kind", "build",
    "--writes-code",
    "--model", "$model",
    "--effort", "$effort",
    "--floors-in-hooks",
    "--permission-mode", "bypassPermissions",
    "--timeout", "14400",
    "--cwd", "$Cwd"
  )

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
  # CS-1178 - THE RUN ENDS IN ONE RESULT OBJECT the driver can read; the kit
  # asks the CLI for `--output-format json`. In text mode a usage-limit refusal
  # (exit 1, one turn, zero cost, an error flag, api_error_status 429) and a
  # crashed executor are the same five seconds and the same exit code, and the
  # driver recorded the refusal as a run that happened. The object is what
  # separates them; see `_worker_result` in ops/loop/queue_loop.py.
  #
  # RESIDUAL, NAMED RATHER THAN FIXED: everything is held in $out until the kit
  # exits, so a worker the driver KILLS at its timeout leaves none of its
  # output in this log - the kill unwinds nothing, and the writes below never
  # run. The CLI's own stderr is captured by the kit and not printed by its
  # command line, so it never reaches this log at all.
  $out = @(Get-Content -LiteralPath "$PromptFile" -Raw |
    & $python @kitArgs *>&1)

  $code = $LASTEXITCODE

  # THE KIT PRINTS ONE JSON LINE. Exit 0 (ran) and 4 (timed out): its usage
  # line, the CLI's result object nested under "receipt". Exit 3 (refused): a
  # "refused" message and a "code" word. Found by its keys; everything else in
  # $out is the kit's own stderr, still written below.
  $kitLine = $null
  $rest = @()
  foreach ($item in $out) {
    $text = [string]$item
    if (($null -eq $kitLine) -and $text.TrimStart().StartsWith("{")) {
      try {
        $parsed = $text | ConvertFrom-Json -ErrorAction Stop
        $keys = @($parsed.PSObject.Properties | ForEach-Object { $_.Name })
        if (($keys -contains "kit") -or ($keys -contains "refused")) {
          $kitLine = $parsed
          continue
        }
      } catch {
        # Not the kit's line; it is written with the rest.
      }
    }
    $rest += $item
  }

  if ($code -eq 3) {
    # THE CODE ONLY, NEVER THE MESSAGE. The code is a fixed kit vocabulary word;
    # the message is text built from an exception, and this log is written
    # unattended (CLAUDE.md non-negotiable 12). A code of any other shape is
    # not echoed either: it is written as "unknown".
    $kitCode = "unknown"
    if (($null -ne $kitLine) -and (([string]$kitLine.code) -cmatch '^[a-z][a-z-]{0,39}\z')) {
      $kitCode = [string]$kitLine.code
    }
    "lane refused $(Get-Date -Format s) kit_code=$kitCode" |
      Out-File "$Log" -Append -Encoding utf8
    exit 3
  }

  if ((($code -eq 0) -or ($code -eq 4)) -and ($null -ne $kitLine)) {
    # WRITTEN IN TODAY'S ORDER: the result's text as readable lines, then
    # anything else the run emitted, then the result object WHOLE on one line,
    # so it sits at the tail where the driver reads it, exactly as it did off
    # the direct start. A person reading the log still sees the worker's words
    # rather than one escaped JSON string. The kit's usage line is not written:
    # it is not a result object, it nests a second copy of one that would
    # double the tail the driver reads, and the kit appends it to its own log.
    $receipt = $kitLine.receipt
    if (($null -ne $receipt) -and ($null -ne $receipt.result)) {
      [string]$receipt.result | Out-File "$Log" -Append -Encoding utf8
    }
    if ($rest.Count -gt 0) {
      $rest | Out-File "$Log" -Append -Encoding utf8
    }
    if ($null -ne $receipt) {
      ConvertTo-Json -InputObject $receipt -Compress -Depth 100 |
        Out-File "$Log" -Append -Encoding utf8
    }
    # THE WORKER'S CODE, as the direct start recorded it: on a run that ended,
    # the kit's 0 means "ran" and the CLI's own exit code is its "rc".
    $rc = $kitLine.rc
    if (($code -eq 0) -and (($rc -is [int]) -or ($rc -is [long]))) {
      $code = $rc
    }
  } else {
    $out | Out-File "$Log" -Append -Encoding utf8
  }
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
