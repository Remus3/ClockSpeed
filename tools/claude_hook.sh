#!/bin/sh
# Clockspeed Claude Code hook wrapper - CS-815.
#
# USAGE, exactly as .claude/settings.json invokes it:
#
#     sh claude_hook.sh pretooluse  <tool.py> [argument ...]
#     sh claude_hook.sh posttooluse <tool.py> [argument ...]
#
# WHAT THIS FIXES. Both Claude hooks used to name a bare interpreter - `pythonw`
# and `python` - with no resolution ladder and no probe of any kind. By the
# PreToolUse gate's own protocol, exit 2 denies and every other status is
# non-blocking, so a missing or substituted interpreter produced a non-2 status
# and the gate FAILED OPEN in silence. JSON cannot express a probe, so the probe
# lives here, and settings.json names this file instead of an interpreter.
#
# THE PROBE AND THE LADDER ARE NOT WRITTEN HERE, THEY ARE CARRIED. The constants,
# `cs_probe`, `cs_python` and the CS-818 marked ladder below are byte-identical to
# .githooks/pre-commit, apart from the ladder's two closing-voice lines, and
# tests/test_claude_hook.py pins that identity. Edit them there, then copy.
#
# HOW A RUN GOES.
#   1. THE RESOLVE CHILD. This file re-runs itself with `--resolve` under ONE
#      outer bound of CS_PROBE_BOUND seconds plus a one-second kill grace, with
#      stdin from /dev/null. The child runs the ladder and prints a single
#      verdict word on stdout. So the whole ladder, however many rungs it
#      tries, is bounded, and the worst case of a call is that bound plus the
#      grace plus the tool.
#   2. THE TOOL. On a passed probe the parent `exec`s the tool. Nothing is
#      buffered and nothing is re-emitted: the tool inherits the harness's own
#      stdin, stdout and stderr, and its exit status IS this process's exit
#      status. A deny from tools/pretooluse_gate.py (exit 2) still denies.
#   3. THE WINDOWED LEG. On `pretooluse` the tool runs under pythonw, found
#      BESIDE THE WINNING INTERPRETER by asking that interpreter where it lives,
#      never by name on PATH. pythonw allocates no console, which is the flash
#      half of CS-425. On a platform that has no pythonw the winner itself runs.
#
# THE HARNESS'S STDIN IS NEVER READ BY THE PROBE. Every probe half and the
# resolve child run with stdin from /dev/null or a pipe of their own; only the
# exec'd tool ever sees the envelope.
#
# A FAILED PROBE IS LOUD AND IS NEVER A DENY. It writes EXACTLY ONE stderr line,
# picked from a fixed set by this file, and exits 1 - never 2, which on the
# PreToolUse leg would deny every shell call. The Claude Code hooks reference,
# section "Exit code output", subsection "Other exit codes": for a status other
# than 0 and 2 with empty stdout the action proceeds and the transcript shows a
# hook-error notice followed by the FIRST LINE of stderr. So the one line is the
# whole report and it is shown without a verbose view. The line never echoes
# an environment value, a path, an interpreter name or anything a candidate
# printed: it is chosen from the fixed table below and carries no colon, so a
# candidate named `:` cannot be mistaken for part of it.
#
# THIS IS AN ACCIDENT DETECTOR, NOT A SECURITY BOUNDARY, exactly as the probe
# comment below says of itself. The shell running this file is itself unprobed;
# that residual is declared in docs/LEDGER.md under the CS-815 grant.
#
# LINE ENDINGS. LF only, no BOM, 7-bit ASCII (.gitattributes pins *.sh).

set -u

cs_hook_refuse() {
    printf 'clockspeed claude hook - REFUSED (CS-815) - %s - the hook tool did not run\n' "$1" >&2
    exit 1
}

# THE LADDER'S OWN REFUSAL, REDIRECTED. The carried ladder and probe call `die`
# with a headline and several lines of detail, some of which render the observed
# probe output and interpreter names. Inside the resolve child NONE of that is
# printed: the headline is matched against the carried text and reduced to one
# fixed verdict word on stdout, which the parent maps to its one line.
die() {
    case "$1" in
        "no working GNU timeout"*) cs_hook_verdict="refused-bound" ;;
        "the interpreter probe did not answer"*) cs_hook_verdict="refused-slow" ;;
        "CLOCKSPEED_PYTHON is set"*) cs_hook_verdict="refused-pinned" ;;
        "no usable python"*) cs_hook_verdict="refused-exhausted" ;;
        *) cs_hook_verdict="refused-unknown" ;;
    esac
    printf '%s' "$cs_hook_verdict"
    exit 1
}

CS_PY=""
CS_PY_ARG=""
# CS-815: whether cs_probe runs its stdin half. ASSIGNED here, outside the
# byte-identical probe, never read from the environment -
# this file hands no program on stdin, so the half is skipped.
CS_HOOK_STDIN_HALF=skip

# THE PROBE PROVES THE CANDIDATE BOTH RUNS A PROGRAM AND CAN REPORT ITS FAILURE.
#
# CS-703: the previous probe ran the candidate with -c and read only its exit
# status, so `true`, `:` and `echo` all passed it. The heredoc or the gate
# invocation was then handed to that program, which ignored it and exited 0, and
# the hook reported success - one environment variable silently disarmed the
# character-set gate, the secret scan, the message checks and the pre-push suite
# at once. An unrunnable check is not a passed check, and neither is a check
# handed to something that cannot run it.
#
# THE SECOND HALF EXISTS BECAUSE THE GATES READ A CHANNEL THE FIRST HALF NEVER
# VALIDATES. Every gate decision in every one of these hooks is taken from `$?`.
# A probe that compares only stdout therefore proves the candidate RAN the
# program and says nothing about whether it can REPORT a failure - so a wrapper
# that forwards stdout faithfully and drops the exit status answers the first
# half with the exact token and turns all three tier-0 gates into no-ops. Two
# ordinary shapes do exactly that, and neither is purpose-built nor knows the
# token: a POSIX wrapper ending in `| cat`, because a pipeline's status is its
# LAST command's, and a Windows .cmd shim wrapping its body in `setlocal` /
# `endlocal`, because `endlocal` resets ERRORLEVEL. The second half hands the
# candidate a program that exits 97 and demands 97 back. The sentinel avoids 0,
# 1, 2 and 5, which are ordinary results, and 125, 126 and 127, which `env` and
# the shell itself produce on an exec failure - so a candidate that never ran the
# program cannot answer correctly by accident.
#
# CS-815: BOTH QUESTIONS ARE ASKED OF ONE START. The program prints the token
# AND exits 97, and the probe demands both from that one run. Two starts
# asked nothing more than one: a candidate that forwards stdout and drops the
# status still answers 0, and one that cannot run the program still prints
# no token. Folding them halved the probe's cost on every hook call.
#
# THAT ESCAPE WAS REACHABLE THROUGH THE `python` RUNG WITH NO ENVIRONMENT
# VARIABLE SET AT ALL. It was never a CLOCKSPEED_PYTHON problem, and unsetting
# that variable was never a mitigation for it.
#
# THE TOKEN IS ASSEMBLED FROM THREE PIECES at run time, so the string being
# compared never appears literally in the program text the candidate is handed.
# A candidate that merely echoes its arguments back cannot reproduce it by
# accident, and `echo` is the live example of one that tries.
#
# THE COMPARISON IS EXACT RATHER THAN CONTAINMENT, deliberately. Exact equality
# refuses a candidate whose stdout carries anything extra - a sitecustomize that
# prints, a .cmd shim without `@echo off`, PYTHONIOENCODING=utf-8-sig - and each
# of those is a FALSE REFUSAL this accepts knowingly. Containment would accept
# all three, and would also accept any program that emits the token among other
# output. In a gate a LOUD FALSE REFUSAL beats a SILENT FALSE ACCEPT: the
# message below fixes the first in a minute, and the second is the defect that
# made this item exist.
#
# THE TOKEN CARRIES NO TRAILING NEWLINE, so the comparison never depends on how
# the interpreter and the shell each treat a line terminator. Measured here:
# python writes CR LF to a pipe and this bash strips both, so the newline form
# happens to compare equal on THIS toolchain - exactly the version-specific
# tolerance CONVENTIONS.md section 16 says to re-measure rather than inherit.
# Writing no newline removes the dependency instead of resting on it.
#
# THIS IS AN ACCIDENT DETECTOR, NOT A SECURITY BOUNDARY. It catches a
# MISCONFIGURED interpreter, which is what CS-703 was. It stops nobody who means
# to get past it: a program written on purpose to print the token and exit 97
# passes both halves, and `git commit --no-verify` skips every hook here without
# needing to. Never cite this probe as evidence that a commit was checked.
CS_PROBE_PROGRAM='import sys; sys.stdout.write("clockspeed-" + "python-" + "ok"); sys.exit(97)'
CS_PROBE_EXPECTED='clockspeed-python-ok'
CS_PROBE_EXIT_EXPECTED=97
CS_PROBE_BOUND=10
CS_PROBE_CAPTURE='cs_o=$("$@"); cs_r=$?; printf "%s" "$cs_o"; exit "$cs_r"'

cs_probe() {
    # ALL initialised BEFORE first use. The failure paths below render them,
    # and `set -u` would abort the hook on an unset one instead. The exit code
    # starts as a WORD rather than a number on purpose: a refusal that never
    # reached the second half must not be readable as "the candidate returned 0".
    cs_probe_out=""
    cs_probe_code="not reached"
    cs_probe_rc="not reached"
    cs_probe_bound_ok=""
    # CS-816: EVERY HALF OF THIS PROBE RUNS UNDER A BOUND OF CS_PROBE_BOUND
    # SECONDS, AND A HALF THAT DOES NOT RETURN INSIDE IT REFUSES THE HOOK.
    # Three hang shapes were measured, none of them exotic. PYTHONINSPECT=1
    # goes interactive after the program, because under MSYS /dev/null is the
    # NUL character device and reports a tty. A candidate that leaves a
    # background process holding stdout makes a command substitution wait for
    # that process rather than for the candidate. A wrapper that execs python
    # with stdin from /dev/null answers every -c program and then spins on a
    # program handed to it on stdin. The answer is a BOUND rather than an
    # enumeration of causes, and so the probe also hands the candidate one
    # program on stdin - the shape commit-msg delivers its checker in - and
    # grades only that it RETURNS.
    #
    # THE BOUND IS ONE LITERAL, byte-identical in the three hooks and never read
    # from the environment or a config file. Its value is justified against a
    # cold-start measurement in the closing record of CS-816 in docs/LEDGER.md.
    #
    # A TIMED-OUT PROBE NEVER FALLS THROUGH to the next rung. The last rung is
    # 'py -3', the measured interpreter that carries no toolchain, and a probe
    # that timed out and then proceeded is the CS-703 no-op wearing a clock. An
    # ordinary MISMATCH still falls through exactly as it always did.
    #
    # THE BOUNDING BINARY IS CHECKED BY BEHAVIOUR, NEVER BY NAME. On Windows,
    # System32 carries a 'timeout' that is a pause command with unrelated
    # semantics, behind GNU timeout on PATH. Before any candidate runs, the
    # binary must pass an ordinary exit status straight through AND return 124
    # when a short bound expires. Absent, foreign, or never expiring, it refuses
    # the hook: a probe is never run without a time limit.
    #
    # CS-1200: 137 IS A WORKING BOUND TOO. It is the KILL sent after the
    # one-second grace, and a loaded box measured it in 2 of 12 runs, when
    # 'sleep' outlived the TERM. Either status proves the bound fired; a binary
    # that never expires still answers 0 here and still refuses.
    timeout -k 1 "$CS_PROBE_BOUND" sh -c 'exit 42' </dev/null >/dev/null 2>&1
    if [ "$?" = 42 ]; then
        timeout -k 1 0.05 sleep 5 </dev/null >/dev/null 2>&1
        case "$?" in
            124 | 137) cs_probe_bound_ok="yes" ;;
        esac
    fi
    if [ "$cs_probe_bound_ok" != "yes" ]; then
        die "no working GNU timeout was found, so the interpreter probe cannot be bounded." \
            "The hook refuses rather than run a probe with no time limit (CS-816)." \
            "'timeout' is checked by behaviour: it must pass an ordinary exit status" \
            "through and return 124 when its bound expires, or 137 when the kill" \
            "after its grace ends the run. A different program of the same name," \
            "such as the Windows pause command, fails that check." \
            "Fix: put GNU coreutils 'timeout' and 'sleep' first on PATH. Git for" \
            "Windows ships both in its own usr/bin directory." \
            "BLOCKED: an unbounded probe is not a passed probe."
    fi
    # THE CAPTURE RUNS INSIDE THE BOUNDED PROCESS. CS_PROBE_CAPTURE is a small sh
    # program that takes the candidate's output itself and re-emits it, so the
    # only processes holding THIS substitution's pipe are ones the bound kills.
    # Capturing the candidate here directly would let a background process it
    # left behind hold the pipe after the bounded child exited, and this
    # substitution would wait on that process with no limit at all.
    #
    # THE EXIT STATUS IS GRADED BEFORE THE TOKEN. MEASURED under a 3 second
    # bound: PYTHONINSPECT=1 returned 124 while the capture already held the
    # exact token. 124 is the bound expiring, 137 the KILL sent when a candidate
    # ignored TERM, and 143 a TERM from elsewhere. Each refuses, whatever the
    # capture holds.
    #
    # ONE START ANSWERS BOTH QUESTIONS (CS-815). $? is captured IMMEDIATELY on
    # the next line, because any command in between - a `[` included -
    # overwrites it. The status is RECORDED only when the token matched, so
    # 'not reached' still means the output check failed or nothing ran.
    cs_probe_out=$(timeout -k 1 "$CS_PROBE_BOUND" sh -c "$CS_PROBE_CAPTURE" \
        cs_probe "$@" -c "$CS_PROBE_PROGRAM" 2>/dev/null </dev/null)
    cs_probe_rc=$?
    if [ "$cs_probe_out" = "$CS_PROBE_EXPECTED" ]; then
        cs_probe_code=$cs_probe_rc
        # THE STDIN HALF runs unless the CALLER declared CS_HOOK_STDIN_HALF as
        # 'skip' outside this probe. Every caller assigns it, so no inherited
        # value reaches here; unset - an extracted copy - runs it. Only
        # commit-msg hands a program on stdin, and only it declares 'run'.
        if [ "$cs_probe_code" = "$CS_PROBE_EXIT_EXPECTED" ] &&
            [ "${CS_HOOK_STDIN_HALF:-run}" != skip ]; then
            # THE STDIN HALF grades only that the candidate RETURNS inside the
            # bound. Its output and its status are deliberately not compared:
            # this half exists for the hang, and a stricter grade here would
            # refuse candidates that the two halves above already judge.
            printf '%s' "$CS_PROBE_PROGRAM" | timeout -k 1 "$CS_PROBE_BOUND" \
                sh -c "$CS_PROBE_CAPTURE" cs_probe "$@" - >/dev/null 2>&1
            cs_probe_rc=$?
        fi
    fi
    case "$cs_probe_rc" in
        124|137|143)
            die "the interpreter probe did not answer within $CS_PROBE_BOUND seconds." \
                "Observed status: [$cs_probe_rc] (124 is the bound expiring)." \
                "A probe that times out REFUSES and never falls through to the next" \
                "rung: the last rung, 'py -3', is the measured interpreter that" \
                "carries no toolchain (CS-816)." \
                "Known causes: PYTHONINSPECT set in the environment; an interpreter" \
                "wrapper that redirects stdin from /dev/null; a wrapper that leaves a" \
                "background process holding stdout." \
                "Unset PYTHONINSPECT, or point CLOCKSPEED_PYTHON at a plain python." \
                "BLOCKED: an unanswered probe is not a passed probe."
            ;;
    esac
    # Compared as STRINGS. Both sides are literal digits here, and `=` cannot
    # raise on a non-numeric value the way `-eq` would.
    [ "$cs_probe_code" = "$CS_PROBE_EXIT_EXPECTED" ]
}

cs_python() {
    if [ -n "$CS_PY_ARG" ]; then
        "$CS_PY" "$CS_PY_ARG" "$@"
    else
        "$CS_PY" "$@"
    fi
}

# THE ONE KILL GRACE of the outer bound, in seconds - the same `-k 1` every
# probe half above uses. The worst case of a call is CS_PROBE_BOUND plus this
# plus the tool, and tests/test_claude_hook.py holds that sum under each leg's
# settings.json timeout.
CS_HOOK_KILL_GRACE=1

# Asked of the WINNING interpreter on the windowed leg. It names pythonw.exe
# beside its own executable, and only if that file exists; on a platform with no
# pythonw it names itself. Forward slashes, because sh execs that form on
# Windows without any path translation. No trailing newline.
CS_HOOK_BESIDE_PROGRAM='import os, sys
e = sys.executable or ""
if os.name != "nt":
    sys.stdout.write(e)
elif os.path.isabs(e):
    w = os.path.join(os.path.dirname(e), "pythonw.exe")
    if os.path.isfile(w):
        sys.stdout.write(w.replace(chr(92), "/"))'

cs_hook_run() {
    cs_hook_leg=$1
    shift
    if [ "$#" -lt 1 ]; then
        cs_hook_refuse "no hook tool was named"
    fi
    # THE RESOLVE CHILD, bounded as a whole. Its stderr is discarded and its
    # stdout is only ever COMPARED, never printed, so nothing a candidate says
    # can reach the one report line.
    cs_hook_out=$(timeout -k "$CS_HOOK_KILL_GRACE" "$CS_PROBE_BOUND" \
        sh "$0" --resolve "$cs_hook_leg" </dev/null 2>/dev/null)
    cs_hook_rc=$?
    case "$cs_hook_rc" in
        0) ;;
        124|137|143) cs_hook_refuse "the interpreter ladder did not finish inside its bound" ;;
        *)
            case "$cs_hook_out" in
                refused-bound) cs_hook_refuse "no working bounding program was found" ;;
                refused-slow) cs_hook_refuse "the interpreter probe did not answer inside its bound" ;;
                refused-pinned) cs_hook_refuse "the pinned interpreter variable failed the probe" ;;
                refused-exhausted) cs_hook_refuse "no interpreter rung passed the probe" ;;
                refused-windowed) cs_hook_refuse "no windowed interpreter was found beside the probe winner" ;;
                *) cs_hook_refuse "the interpreter probe ended without a verdict" ;;
            esac
            ;;
    esac
    case "$cs_hook_out" in
        "resolved-3 "?*)
            exec "${cs_hook_out#resolved-3 }" -3 "$@"
            ;;
        "resolved "?*)
            exec "${cs_hook_out#resolved }" "$@"
            ;;
    esac
    cs_hook_refuse "the interpreter probe ended without a verdict"
}

case "${1:-}" in
    pretooluse | posttooluse)
        cs_hook_run "$@"
        ;;
    --resolve)
        # Falls through to the carried ladder below.
        CS_HOOK_LEG=${2:-}
        ;;
    *)
        cs_hook_refuse "the hook leg was not named"
        ;;
esac

# >>> CS-818 LADDER BEGIN - resolves CS_PY and CS_PY_ARG; pinned across the hooks.
if [ -n "${CLOCKSPEED_PYTHON:-}" ]; then
    # SET BUT FAILING IS A HARD FAILURE, NOT A FALL-THROUGH. The old form was
    # one `&&` condition, so a value that failed the probe fell quietly through
    # to `python`: the operator's explicit choice was overruled, the run
    # continued under an interpreter they did not pick, and nothing said so.
    # That is the CS-806 shape in a quieter form. Refusing costs one loud
    # message; falling through costs silence.
    if cs_probe "$CLOCKSPEED_PYTHON"; then
        CS_PY="$CLOCKSPEED_PYTHON"
    else
        # NONE OF THE CANDIDATE'S OUTPUT IS RENDERED, only its size (CS-814). A
        # candidate that ignores its arguments can print anything - its own
        # environment, and the live credentials in it, included - and this text
        # reaches logs and reports (CLAUDE.md non-negotiable 13). The VALUE of
        # CLOCKSPEED_PYTHON is not echoed back either: it is routinely an
        # absolute path under a home directory (non-negotiable 3).
        cs_probe_bytes=$(printf '%s' "$cs_probe_out" | wc -c 2>/dev/null | tr -d ' ')
        die "CLOCKSPEED_PYTHON is set but did not answer the probe." \
            "It must name ONE EXECUTABLE, not a command line with arguments." \
            "'py -3' is two tokens, so it cannot be this variable's value. Unset" \
            "the variable and the ladder reaches 'py -3' by itself, last." \
            "Observed probe output: [$cs_probe_bytes] bytes, not shown - a candidate" \
            "that ignores its arguments can print the environment (CS-814)." \
            "Observed exit status when asked to fail: [$cs_probe_code]" \
            "(expected $CS_PROBE_EXIT_EXPECTED; 'not reached' means this half" \
            "never ran. That happens BOTH when the candidate could not be" \
            "executed at all AND when it ran but answered the output check" \
            "wrongly - zero bytes above point at the first.)" \
            "An interpreter must BOTH run the program it is handed AND report a" \
            "failure back. That is CS-703: judging the exit code alone let 'true'," \
            "':' and 'echo' through, and judging stdout alone let a wrapper that" \
            "forwards output but drops the exit status turn every tier-0 gate" \
            "into a no-op." \
            "Point CLOCKSPEED_PYTHON at a working python executable, or unset it." \
            "The hook tool is BLOCKED: an unrunnable gate is not a passed gate."
    fi
elif cs_probe python; then
    CS_PY="python"
elif cs_probe python3; then
    CS_PY="python3"
elif cs_probe py -3; then
    CS_PY="py"
    CS_PY_ARG="-3"
else
    die "no usable python interpreter found." \
        "Tried \$CLOCKSPEED_PYTHON, 'python', 'python3', 'py -3'." \
        "Set CLOCKSPEED_PYTHON to an interpreter and retry." \
        "The hook tool is BLOCKED: an unrunnable gate is not a passed gate."
fi
# <<< CS-818 LADDER END

# THE VERDICT. One word, then the executable. `resolved-3` carries the ladder's
# only possible extra argument, the `-3` of the `py` rung, so the parent never
# has to split a value that may contain spaces.
if [ "$CS_HOOK_LEG" = pretooluse ]; then
    cs_hook_exe=$(cs_python -c "$CS_HOOK_BESIDE_PROGRAM" </dev/null 2>/dev/null) || cs_hook_exe=""
    if [ -z "$cs_hook_exe" ]; then
        printf '%s' "refused-windowed"
        exit 1
    fi
    printf 'resolved %s' "$cs_hook_exe"
    exit 0
fi
if [ -n "$CS_PY_ARG" ]; then
    printf 'resolved%s %s' "$CS_PY_ARG" "$CS_PY"
else
    printf 'resolved %s' "$CS_PY"
fi
exit 0
