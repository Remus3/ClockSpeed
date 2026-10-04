"""CS-815 - the folded probe: one start, a per-run nonce, the 97 - run as a FILE.

THE GRANT AND ITS AMENDMENT. docs/LEDGER.md, "2026-10-03 - CS-815 - FROZEN-FILE
GRANT" and the "AMENDMENT TO THE FROZEN-FILE GRANT" above it. The wrapper's
latency was almost all probe, so the grant let the probe fold its questions
into ONE interpreter start, shorten the expiry self-check to 0.05s, and skip
the stdin half through ONE caller-declared variable - except in commit-msg,
which hands its checker on stdin.

WHY A NONCE. Folding a FIXED token and the 97 into one start let a wrapper
that never runs its program - ``printf clockspeed-python-ok; exit 97`` - pass,
where the split probe refused it because its token start had to exit 0. The
amendment replaced the fixed token: the probe draws a nonce at run time with
``od``, embeds it in the program, and demands BOTH the decimal of the nonce
plus a fixed non-zero offset, computed by the program, AND exit 97. A failed,
empty or non-digit draw refuses: there is no fallback.

WHAT EACH ARM PROVES, against the amended conditions, on all four copies:

    declaration  CS_HOOK_STDIN_HALF declared once, outside the probe, and only
                 commit-msg runs the stdin half
    starts       one start answers the probe; commit-msg adds the stdin half,
                 and an inherited value cannot make it skip
    refused      the constant wrapper, a replay of an earlier honest run's
                 output, an argument-echoing wrapper, every CS-703 shape, and
                 a PATH ``od`` that fails, prints nothing or prints a non-digit
    control      the honest wrapper is accepted
    killed       mutants dropping the nonce, the offset or the 97 demand each
                 accept a wrapper the pristine probe refuses; each mutation is
                 asserted to have APPLIED
    expiry       the self-check bound is 0.05s, and non-zero

RUN AS A FILE. Every arm writes the copy's own probe bytes into a script and
runs it with sh, which is how pre-commit and the wrapper run it.

MUTANTS ARE BUILT FROM TMP COPIES. No tracked file is ever modified here, so a
killed run cannot leave a mutant on disk.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. Every outcome is reduced to a bool,
an int or a short fixed string before it is asserted on (CLAUDE.md
non-negotiables 3 and 12).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Final, NamedTuple

import pytest

from tests.test_hook_interpreter_ladder import (
    ARGUMENT_IGNORING_PROGRAMS,
    HONEST_SHIM,
    LIAR_SHIM,
    REAL_PYTHON_POSIX,
    probe_block,
    write_shim,
)
from tests.test_pretooluse_gate import require_posix_shell, shell_environment

REPO_ROOT: Final = Path(__file__).resolve().parent.parent

COMMIT_MSG: Final = "commit-msg"
CARRIERS: Final = {
    "pre-commit": REPO_ROOT / ".githooks" / "pre-commit",
    COMMIT_MSG: REPO_ROOT / ".githooks" / "commit-msg",
    "pre-push": REPO_ROOT / ".githooks" / "pre-push",
    "claude_hook.sh": REPO_ROOT / "tools" / "claude_hook.sh",
}

STDIN_HALF_NAME: Final = "CS_HOOK_STDIN_HALF"
DECLARATION: Final = re.compile(rb"^CS_HOOK_STDIN_HALF=([a-z]+)$", re.MULTILINE)
RUN_VALUE: Final = b"run"
SKIP_VALUE: Final = b"skip"

# The start order a correct probe produces, per carrier. ONE ``-c`` start
# answers the nonce and the 97; commit-msg adds the stdin half.
FOLDED: Final = ("-c",)
FOLDED_WITH_STDIN: Final = ("-c", "-")

EXPIRY_CHECK: Final = b"timeout -k 1 0.05 sleep 5 "
OLD_EXPIRY: Final = b" 0.2 sleep"

BLOCK_DIE: Final = b"die() { printf 'DIE: %s\\n' \"$1\"; exit 3; }\n"
BLOCK_TAIL: Final = b'\ncs_probe "$1"\nprintf \'RC=%s\\n\' "$?"\n'
PROBE_TIMEOUT: Final = 120
ACCEPTED: Final = "0"
REFUSED: Final = "1"

# A wrapper whose LAST command resets the status to 0 - the POSIX shape of a
# .cmd shim ending in ``endlocal``, which resets ERRORLEVEL. It forwards stdout.
ENDLOCAL_SHIM: Final = '#!/bin/sh\n"' + REAL_PYTHON_POSIX + '" "$@"\nexit 0\n'

# The amendment's named escape: never runs its program, prints the old fixed
# token and exits 97. The split probe refused it; a fixed-token fold did not.
CONSTANT_SHIM: Final = "#!/bin/sh\nprintf clockspeed-python-ok\nexit 97\n"

# Echoes every argument it was handed - the program text, nonce included -
# and exits 97, so only the OFFSET stands between it and the answer.
ARGUMENT_ECHO_SHIM: Final = "#!/bin/sh\nprintf '%s' \"$*\"\nexit 97\n"

# Lifts the nonce out of the program text and prints it bare, exiting 97: the
# wrapper that the offset alone defeats. Its non-vacuity is the offset mutant.
PARROT_SHIM: Final = (
    "#!/bin/sh\n"
    'cs_p=""\n'
    'for cs_a in "$@"; do case "$cs_a" in *"str("*) cs_p=$cs_a ;; esac; done\n'
    "cs_n=${cs_p#*str(}\n"
    "cs_n=${cs_n%%[!0-9]*}\n"
    "printf '%s' \"$cs_n\"\n"
    "exit 97\n"
)

# The CS-703 shapes and the amendment's wrappers a probe must refuse. Bare
# names run as the candidate itself; shim bodies are written to a file first.
SHIM_SHAPES: Final = {
    "pipe-cat": LIAR_SHIM,
    "endlocal": ENDLOCAL_SHIM,
    "constant": CONSTANT_SHIM,
    "argument-echo": ARGUMENT_ECHO_SHIM,
    "parrot": PARROT_SHIM,
}
REFUSED_SHAPES: Final = tuple(ARGUMENT_IGNORING_PROGRAMS) + tuple(sorted(SHIM_SHAPES))

# PATH-first stand-ins for ``od``: the draw fails, says nothing, or says a
# non-digit. Each must refuse BEFORE the candidate is ever started.
OD_SHIMS: Final = {
    "fails": "#!/bin/sh\nexit 1\n",
    "prints-nothing": "#!/bin/sh\nexit 0\n",
    "prints-a-non-digit": "#!/bin/sh\nprintf '  12x4\\n'\n",
    "prints-a-leading-zero": "#!/bin/sh\nprintf '  0123\\n'\n",
}

# The mutants the amendment requires killed. Each is (old, new) byte pairs that
# must ALL apply exactly once, and the name of the wrapper that kills it.
FINAL_GRADE: Final = b'    [ "$cs_probe_code" = "$CS_PROBE_EXIT_EXPECTED" ]\n}'
NONCE_DRAW: Final = (
    b'    cs_probe_nonce=$(od -An -N4 -tu4 /dev/urandom 2>/dev/null) || cs_probe_nonce=""\n'
)
OFFSET_LINE: Final = re.compile(rb"\nCS_PROBE_OFFSET=([1-9][0-9]*)\n")
MUTANTS: Final = {
    "97-demand-dropped": (
        ((FINAL_GRADE, b'    [ "$cs_probe_code" != "not reached" ]\n}'),),
        "pipe-cat",
    ),
    "sentinel-made-zero": (
        (
            (b"; sys.exit(97)'\n", b"'\n"),
            (b"\nCS_PROBE_EXIT_EXPECTED=97\n", b"\nCS_PROBE_EXIT_EXPECTED=0\n"),
        ),
        "pipe-cat",
    ),
    "nonce-dropped": (((NONCE_DRAW, b"    cs_probe_nonce=12345\n"),), "replay"),
    "offset-dropped": ((), "parrot"),
}


class ProbeRun(NamedTuple):
    """The probe run as a file, reduced to scalars and fixed strings."""

    died: bool
    rc: str
    modes: tuple[str, ...]


def logging_shim(log: Path, target: str) -> str:
    """A wrapper that records each start's mode, then execs ``target`` intact."""
    return (
        "#!/bin/sh\n"
        'case "$1" in -c|-) cs_m="$1" ;; *) cs_m=other ;; esac\n'
        'printf \'%s\\n\' "$cs_m" >>"' + log.as_posix() + '"\n'
        'exec "' + target + '" "$@"\n'
    )


def recording_shim(capture: Path) -> str:
    """An honest wrapper that also keeps what its ``-c`` start printed."""
    real = '"' + REAL_PYTHON_POSIX + '"'
    return (
        "#!/bin/sh\n"
        'if [ "$1" = -c ]; then\n'
        "    cs_o=$(" + real + ' "$@"); cs_r=$?\n'
        '    printf \'%s\' "$cs_o" >"' + capture.as_posix() + '"\n'
        "    printf '%s' \"$cs_o\"\n"
        '    exit "$cs_r"\n'
        "fi\n"
        "exec " + real + ' "$@"\n'
    )


def declaration_line(raw: bytes) -> bytes:
    """The copy's own stdin-half declaration line, or empty when it has none."""
    found = DECLARATION.search(raw)
    return found.group(0) + b"\n" if found else b""


def probe_file(raw: bytes) -> bytes:
    """A runnable script: a stub die, the copy's declaration, its probe, a tail."""
    return BLOCK_DIE + declaration_line(raw) + probe_block(raw) + BLOCK_TAIL


def run_probe(
    tmp_path: Path,
    raw: bytes,
    candidate: str,
    extra_env: dict[str, str] | None = None,
    path_first: Path | None = None,
) -> ProbeRun:
    """Run ``raw``'s probe as a FILE against ``candidate``, under the real timeout."""
    shell = require_posix_shell()
    tmp_path.mkdir(parents=True, exist_ok=True)
    script = tmp_path / "probe-under-test.sh"
    script.write_bytes(probe_file(raw))
    env = shell_environment(shell)
    for name in ("CLOCKSPEED_PYTHON", "PYTHONINSPECT", STDIN_HALF_NAME):
        env.pop(name, None)
    env.update(extra_env or {})
    if path_first is not None:
        env["PATH"] = str(path_first) + os.pathsep + env["PATH"]
    log = tmp_path / "starts.log"
    log.write_bytes(b"")
    # A bare program name - ``:`` above all, a shell builtin - is handed to the
    # probe as itself, exactly as the ladder hands it; only a file is wrapped.
    if Path(candidate).is_file():
        shim = logging_shim(log, candidate)
        candidate = Path(write_shim(tmp_path / "logged", "candidate.sh", shim)).as_posix()
    proc = subprocess.run(
        [shell, str(script), candidate],
        capture_output=True,
        text=True,
        env=env,
        timeout=PROBE_TIMEOUT,
        check=False,
    )
    rc_lines = [line[3:] for line in proc.stdout.splitlines() if line.startswith("RC=")]
    modes = tuple(log.read_text(encoding="ascii").split())
    return ProbeRun("DIE: " in proc.stdout, rc_lines[0] if rc_lines else "", modes)


def shim_path(tmp_path: Path, name: str, body: str) -> str:
    """``body`` written as an executable shim, by its POSIX path."""
    return Path(write_shim(tmp_path / "shapes", name + ".sh", body)).as_posix()


def replay_of(tmp_path: Path, raw: bytes) -> str:
    """A wrapper replaying what an EARLIER honest run of ``raw`` printed, exiting 97."""
    capture = tmp_path / "honest-output.txt"
    recorder = shim_path(tmp_path, "recorder", recording_shim(capture))
    honest = run_probe(tmp_path, raw, recorder)
    assert honest.rc == ACCEPTED, f"the recording run was refused with [{honest.rc}]"
    seen = capture.read_text(encoding="ascii")
    digits = seen.isdigit()
    assert digits, "the recording run captured no decimal answer, so a replay means nothing"
    return shim_path(tmp_path, "replay", "#!/bin/sh\nprintf '%s' '" + seen + "'\nexit 97\n")


def candidate_for(tmp_path: Path, shape: str, raw: bytes) -> str:
    """A bare program name as itself, the replay, or a shim body written out."""
    if shape == "replay":
        return replay_of(tmp_path, raw)
    if shape not in SHIM_SHAPES:
        return shape
    return shim_path(tmp_path, shape, SHIM_SHAPES[shape])


def offset_pairs(raw: bytes) -> tuple[tuple[bytes, bytes], ...]:
    """The offset mutant for ``raw``: its declared offset line made zero."""
    found = OFFSET_LINE.search(raw)
    assert found is not None, "the copy declares no non-zero CS_PROBE_OFFSET - nothing to drop"
    return ((found.group(0), b"\nCS_PROBE_OFFSET=0\n"),)


def mutated(raw: bytes, mutant: str) -> bytes:
    """``raw`` with every replacement of ``mutant`` applied, each asserted to apply once."""
    pairs = MUTANTS[mutant][0] or offset_pairs(raw)
    out = raw
    for old, new in pairs:
        hits = out.count(old)
        assert hits == 1, f"the {mutant} mutation matched {hits} times, not once - it never applied"
        out = out.replace(old, new)
    changed = out != raw
    assert changed, f"the {mutant} mutant is byte-identical to the pristine copy"
    return out


# --- declaration ------------------------------------------------------------


@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_each_copy_declares_the_stdin_half_once_outside_the_probe(carrier: str) -> None:
    """Exactly one declaration, never inside the identity region, run only by commit-msg."""
    raw = CARRIERS[carrier].read_bytes()
    values = DECLARATION.findall(raw)
    assert len(values) == 1, f"{carrier} declares the stdin half {len(values)} times, not once"
    inside = b"CS_HOOK_STDIN_HALF=" in probe_block(raw)
    assert not inside, f"{carrier} declares the stdin half inside the byte-identical probe"
    want = RUN_VALUE if carrier == COMMIT_MSG else SKIP_VALUE
    right = values[0] == want
    assert right, f"{carrier} declares the stdin half as the wrong value"


# --- starts -----------------------------------------------------------------


@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_one_start_answers_the_probe_and_only_commit_msg_adds_the_stdin_half(
    tmp_path: Path, carrier: str
) -> None:
    """The fold, observed by counting starts of an honest logging wrapper."""
    run = run_probe(tmp_path, CARRIERS[carrier].read_bytes(), REAL_PYTHON_POSIX)
    want = FOLDED_WITH_STDIN if carrier == COMMIT_MSG else FOLDED
    assert not run.died, f"{carrier}'s probe died on a real interpreter"
    assert run.rc == ACCEPTED, f"{carrier}'s probe returned [{run.rc}] for a real interpreter"
    assert run.modes == want, f"{carrier}'s probe started the candidate as {run.modes}"


def test_an_inherited_value_cannot_make_commit_msg_skip_the_stdin_half(tmp_path: Path) -> None:
    """commit-msg ASSIGNS the variable, so the environment's value never reaches the probe."""
    raw = CARRIERS[COMMIT_MSG].read_bytes()
    run = run_probe(tmp_path, raw, REAL_PYTHON_POSIX, {STDIN_HALF_NAME: SKIP_VALUE.decode()})
    assert run.rc == ACCEPTED, f"commit-msg's probe returned [{run.rc}] for a real interpreter"
    assert run.modes == FOLDED_WITH_STDIN, f"commit-msg's probe started {run.modes}"


# --- refused ----------------------------------------------------------------


@pytest.mark.parametrize("shape", [*REFUSED_SHAPES, "replay"])
@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_every_refused_shape_is_refused_by_every_copy(
    tmp_path: Path, carrier: str, shape: str
) -> None:
    """CS-703's shapes and the amendment's wrappers: each refused, none died."""
    raw = CARRIERS[carrier].read_bytes()
    candidate = candidate_for(tmp_path, shape, raw)
    run = run_probe(tmp_path, raw, candidate)
    assert not run.died, f"{carrier}'s probe died on {shape} instead of refusing it"
    assert run.rc == REFUSED, f"{carrier}'s probe returned [{run.rc}] for {shape}"


@pytest.mark.parametrize("od", sorted(OD_SHIMS))
@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_a_failed_nonce_draw_refuses_before_any_start(
    tmp_path: Path, carrier: str, od: str
) -> None:
    """The draw FAILS CLOSED: no fallback, and the candidate is never even started."""
    fakes = tmp_path / "fake-od"
    write_shim(fakes, "od", OD_SHIMS[od])
    run = run_probe(tmp_path, CARRIERS[carrier].read_bytes(), REAL_PYTHON_POSIX, path_first=fakes)
    assert not run.died, f"{carrier}'s probe died when od {od}"
    assert run.rc == REFUSED, f"{carrier}'s probe returned [{run.rc}] when od {od}"
    started = len(run.modes)
    assert started == 0, f"{carrier}'s probe started the candidate {started} times when od {od}"


@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_refusal_control_an_honest_wrapper_is_accepted_by_every_copy(
    tmp_path: Path, carrier: str
) -> None:
    """The non-vacuity control: a wrapper forwarding both channels passes."""
    honest = shim_path(tmp_path, "honest", HONEST_SHIM)
    run = run_probe(tmp_path, CARRIERS[carrier].read_bytes(), honest)
    assert not run.died, f"{carrier}'s probe died on the honest wrapper"
    assert run.rc == ACCEPTED, f"{carrier}'s probe returned [{run.rc}] for the honest wrapper"


# --- killed -----------------------------------------------------------------


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_each_required_mutant_is_killed(tmp_path: Path, carrier: str, mutant: str) -> None:
    """Pristine refuses the killer; the mutant still accepts honest AND now accepts the killer.

    The middle clause is what makes the kill meaningful: a mutant that refused
    everything would also "differ" from pristine on the killer.
    """
    raw = CARRIERS[carrier].read_bytes()
    killer = MUTANTS[mutant][1]
    pristine = run_probe(tmp_path, raw, candidate_for(tmp_path / "pristine", killer, raw))
    assert pristine.rc == REFUSED, f"pristine {carrier} returned [{pristine.rc}] for {killer}"
    bad = mutated(raw, mutant)
    honest = run_probe(tmp_path, bad, REAL_PYTHON_POSIX)
    assert honest.rc == ACCEPTED, f"the {mutant} mutant of {carrier} refused a real interpreter"
    escaped = run_probe(tmp_path, bad, candidate_for(tmp_path / "mutant", killer, bad))
    assert escaped.rc == ACCEPTED, (
        f"the {mutant} mutant of {carrier} returned [{escaped.rc}] for {killer}, so the "
        "refusal arms cannot tell it from the pristine probe"
    )


# --- expiry -----------------------------------------------------------------


@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_the_expiry_self_check_is_short_and_never_zero(carrier: str) -> None:
    """0.05s, exactly once; 0 would disable timeout, and the old 0.2s is gone."""
    block = probe_block(CARRIERS[carrier].read_bytes())
    hits = block.count(EXPIRY_CHECK)
    assert hits == 1, f"{carrier}'s probe carries the 0.05s self-check {hits} times"
    stale = OLD_EXPIRY in block
    assert not stale, f"{carrier}'s probe still carries the 0.2s self-check"


def test_no_carrier_path_is_missing() -> None:
    """The four copies exist, so no parametrised arm above measured an absent file."""
    missing = sum(1 for path in CARRIERS.values() if not path.is_file())
    assert missing == 0, f"{missing} of the four probe copies are missing"
