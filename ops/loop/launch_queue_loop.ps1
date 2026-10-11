# launch_queue_loop.ps1 - detached launcher for ops/loop/queue_loop.py, the driver
# that re-fires the one-row `queue` lane worker cycle after cycle.
#
# THIS SCRIPT'S ONLY JOB IS TO START THE DRIVER AND TELL THE TRUTH ABOUT WHETHER
# IT STARTED. Both halves of that have been got wrong before, in the tree this
# was ported from, and both failures had the same shape: a real pid, exit 0, and
# no work done. Everything below that looks defensive is one of them.
#
# $PSScriptRoot in a param default is not a guess - PowerShell sets it for a
# script file BEFORE it binds parameters. That keeps the default relative to
# wherever this repo is checked out instead of pinning an absolute path into a
# param block, which CLAUDE.md non-negotiable 3 forbids anyway.
param(
  [int]$Cycles = 12,
  [int]$Settle = 45,
  # WHICH LANE. Empty means "the driver's own default", and that is deliberate:
  # a lane name spelled here would be a second copy of queue_loop.LANE, and two
  # copies of one fact is the drift CLAUDE.md section 4 exists to stop. The
  # driver refuses a lane that is not on its roster, so a typo fails loudly
  # there rather than silently here.
  [string]$Lane = "",
  # Empty means "derive it from the lane" - see the block below the param list,
  # which is where it is computed because a param default cannot see another
  # param reliably enough to bet a whole night on.
  [string]$Log  = "",
  # See the sentinel pre-check below. -Force starts the driver over a stop file
  # that is already present; it does NOT override the driver's own check.
  [switch]$Force,
  # Passed straight through. The driver waits on CI by default, which is the
  # whole point of it owning the wait; -NoCiGate is for a box with no `gh`
  # credentials, and -LocalSuite adds the full local suite between cycles.
  [switch]$NoCiGate,
  [switch]$LocalSuite
)
# ONE LOG PER LAUNCH, and this is a measured loss rather than tidiness.
# Start-Process TRUNCATES its redirect target at every launch. With one fixed
# name per lane, a second lane pointed at one file erased the first lane's log
# the moment it started - and, CS-1018, a later NIGHT of the same lane erased
# the only record of the 2026-09-10 cycle gap, which is why that gap can never
# be diagnosed now. So the default name carries a UTC launch stamp and a run
# token, and a name already on disk is re-minted rather than truncated.
#
# This file is the copy that ALSO catches a crash before the driver opens its
# own log. The driver keeps its own night log as well (queue_loop.night_log),
# opened exclusively, so an explicit -Log - which is taken exactly as given,
# and which Start-Process WILL truncate - still loses no night. The durable
# record is the JSONL ledger either way; these are the human tail.
if (-not $Log) {
  $suffix = ""
  if ($Lane) { $suffix = "-$Lane" }
  do {
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd'T'HHmmss'Z'")
    $token = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $Log = Join-Path $PSScriptRoot "reports\queue_loop$suffix-$stamp-$token.log"
  } while ((Test-Path $Log) -or (Test-Path "$Log.err"))
}

$ErrorActionPreference = "Stop"   # unlike run_lane.ps1: nothing here is long-lived
                                  # enough to ride out a fault, and a launcher that
                                  # half-worked must fail loudly at the prompt.

# Ride the subscription login, never the API key. Clearing it HERE matters more
# than clearing it in the runner: this process is the ancestor of every worker
# the driver spawns, and a Windows child inherits the parent's environment block,
# so one clear at the root covers the whole run. Scoped to this process only -
# the machine-wide variable is left alone.
$env:ANTHROPIC_API_KEY = $null

# pythonw.exe, not python.exe - the driver runs for hours, and a stray console
# would sit in the taskbar for the whole night waiting to be closed by accident.
#
# RESOLVED, NEVER HARDCODED. The ported original wrote an absolute path under a
# user profile directory, which is a home path and CLAUDE.md non-negotiable 3
# forbids one in a tracked file. Three rungs, most specific first, and a loud
# failure rather than a fallback: a launcher that silently picked a different
# interpreter would be the same class of lie as the two below.
$py = $null
if ($env:CLOCKSPEED_PYTHONW -and (Test-Path $env:CLOCKSPEED_PYTHONW)) {
  $py = $env:CLOCKSPEED_PYTHONW
} else {
  $cmd = Get-Command pythonw -ErrorAction SilentlyContinue
  if ($cmd) {
    $py = $cmd.Source
  } else {
    # pythonw sits beside python in every CPython layout on Windows.
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
      $sibling = Join-Path (Split-Path $cmd.Source -Parent) "pythonw.exe"
      if (Test-Path $sibling) { $py = $sibling }
    }
  }
}
if (-not $py) {
  throw "pythonw.exe not found. Set CLOCKSPEED_PYTHONW, or put python on PATH."
}

$driver = Join-Path $PSScriptRoot "queue_loop.py"
$repo   = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path $driver)) { throw "driver not found: $driver" }

# STOP SENTINELS, CHECKED BEFORE THE SPAWN.
#
# The driver honours these files itself and correctly runs zero cycles when one
# is present - but a launcher that printed "driver started pid=..." over exactly
# that no-op is how a whole night gets lost while the operator believes it ran.
# The operator reads this banner, not the ledger, so the refusal has to happen
# HERE as well as there.
#
# The same relative paths as queue_loop.STOP_RELPATHS, in the same order.
# tests/test_launch_queue_loop.py asserts that correspondence, because two
# copies of one list is exactly the drift CLAUDE.md section 4 is about.
#
# THESE ARE BOX-WIDE AND NOT PER-LANE, said plainly rather than discovered at
# 3am: any one of them refuses EVERY lane, whatever -Lane was asked for. A
# per-lane sentinel is a separate change - it moves STOP_RELPATHS, which this
# list is pinned against.
$sentinels = @(
  (Join-Path $PSScriptRoot "control\STOP"),
  (Join-Path $PSScriptRoot "control\lanes\QUEUE_STOP"),
  (Join-Path $PSScriptRoot "control\lanes\QUEUE_DRAINED")
)
$present = @($sentinels | Where-Object { Test-Path $_ })
if ($present.Count -gt 0) {
  Write-Warning "queue-loop: stop sentinel present - the driver would run ZERO cycles."
  foreach ($p in $present) { Write-Warning "  present: $p" }
  if (-not $Force) {
    # exit 2 matches queue_loop.EXIT_STOP_SENTINEL, so a wrapper sees ONE number
    # for one condition whichever half of the pair refused.
    Write-Warning "REFUSING to start. Delete the file above to run, or pass -Force."
    exit 2
  }
  # Said plainly rather than implied: -Force only gets PAST this script. The
  # driver re-checks the same files before cycle 1 and will still run zero
  # cycles and exit 2 while they exist. It is for the case where the file is
  # about to be removed, or where --control-dir points somewhere else.
  Write-Warning "-Force given: starting anyway. NOTE the driver re-checks these files itself."
}

# Start-Process refuses to point stdout and stderr at the SAME file, so stderr
# gets a sibling. Start-Process truncates both, which is why the default name
# above is new for every launch; the DURABLE record is still
# ops/loop/reports/queue_loop.jsonl - these two are the human tail, not the
# ledger.
$logDir = Split-Path $Log -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$errLog = "$Log.err"

# NO DETACHED_PROCESS EQUIVALENT ANYWHERE IN THIS FILE, and that is deliberate.
# MEASURED over three spawns of one script differing only in flags: a spawn
# carrying DETACHED_PROCESS issues a real pid and returns rc=0 while doing
# NOTHING AT ALL, because the child cannot initialise a host without a console.
# Start-Process already returns immediately and leaves the child running
# independently of this session, so detachment costs nothing extra;
# -WindowStyle Hidden is the belt to pythonw's braces.
#
# EVERY PATH ARGUMENT IS QUOTED, and this is not defensive style. MEASURED on
# the first real fire of the ported original: Start-Process joins an
# -ArgumentList array with spaces and quotes NOTHING, so a repo root containing
# a space split the path in two and the interpreter received only the first
# half - "can't open file 'C:\Riot': [Errno 2] No such file or directory". The
# failure is silent in the shape that matters: Start-Process still issued a real
# pid and the script still printed "driver started", so the whole night would
# have produced nothing. This tree's root has no space in it TODAY, which makes
# this latent rather than absent - and a latent version of a measured failure is
# still that failure.
$argList = @("`"$driver`"", "--cycles", $Cycles, "--settle", $Settle)
# QUOTED for the same measured reason as the driver path above, and forwarded
# only when it was asked for, so the driver's own default stays the one answer.
if ($Lane)       { $argList += @("--lane", "`"$Lane`"") }
if ($NoCiGate)   { $argList += "--no-ci-gate" }
if ($LocalSuite) { $argList += "--local-suite" }

$proc = Start-Process -FilePath $py -ArgumentList $argList `
                      -WorkingDirectory $repo `
                      -WindowStyle Hidden -PassThru `
                      -RedirectStandardOutput $Log -RedirectStandardError $errLog

# THE BANNER IS UNREACHABLE FROM THE REFUSAL PATH ABOVE - the `exit 2` returns
# before it. That ordering is the property, and it is what the guard asserts.
$laneSaid = if ($Lane) { $Lane } else { "the driver's default" }
"queue-loop driver started pid=$($proc.Id) lane=$laneSaid cycles=$Cycles settle=$Settle"
"  log:    $Log"
"  errlog: $errLog"
"  night:  $(Join-Path $PSScriptRoot 'reports\queue_loop_night-*.log') (the driver's own, one per night)"
"  ledger: $(Join-Path $PSScriptRoot 'reports\queue_loop.jsonl')"
"  stop:   create ops\loop\control\lanes\QUEUE_STOP (or control\STOP for everything)"
"  kill:   taskkill /F /T /PID $($proc.Id)"
