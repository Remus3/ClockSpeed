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
$env:CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS = "2400000"

$claude = (Get-Command claude -ErrorAction Stop).Source
Set-Location -LiteralPath "$Cwd"

# THE MODEL COMES FROM ops/loop/config.json, READ VIA $PSScriptRoot AND NOT THE
# WORKING DIRECTORY. This runner always lives in the MAIN tree, while $Cwd is a
# fresh worktree checkout that does not carry a gitignored config - reading it
# relative to the cwd would find nothing on every real fire. A known-good model
# is set FIRST and every read or parse fault keeps it, because a lane must never
# fail to spawn over a config read.
$model = "claude-opus-5"
try {
  $cfgPath = Join-Path $PSScriptRoot "config.json"
  if (Test-Path -LiteralPath $cfgPath) {
    $cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json
    if ($cfg.executor_model) { $model = [string]$cfg.executor_model }
  }
} catch {
  # Any read or parse fault keeps the fallback model set above.
}

"lane start $(Get-Date -Format s) cwd=$Cwd model=$model prompt=$PromptFile" |
  Out-File "$Log" -Encoding utf8

# `*>> $Log` WROTE THE WORKER'S OUTPUT AS UTF-16LE. On Windows PowerShell 5.1
# the redirection operators use the shell's default Unicode encoding, while the
# header line above is UTF-8. MEASURED on a real 4298-byte lane log: UTF-8 for
# the first 119 bytes, then UTF-16LE for the remaining 4179 - 2066 NUL bytes in
# one file. Anything reading it as one encoding got interleaved nulls for the
# half that mattered.
#
# `*>&1 |` merges every stream into the pipeline so Out-File sets the encoding
# for all of them, which KEEPS the "native stderr must not kill the lane"
# property above: the streams are still folded into the same file, they are just
# written as UTF-8 now.
Get-Content -LiteralPath "$PromptFile" -Raw |
  & $claude -p --model $model --dangerously-skip-permissions *>&1 |
  Out-File "$Log" -Append -Encoding utf8

"lane exit $(Get-Date -Format s) code=$LASTEXITCODE" |
  Out-File "$Log" -Append -Encoding utf8
