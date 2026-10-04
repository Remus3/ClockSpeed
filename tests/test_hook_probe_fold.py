"""CS-815 - the folded probe: one start answers the token AND the 97, run as a FILE.

THE GRANT. docs/LEDGER.md, "2026-10-03 - CS-815 - FROZEN-FILE GRANT". The
wrapper's latency was almost all probe: a 0.2s expiry self-check plus three
interpreter starts. The grant lets the probe (1) fold the token and the 97
sentinel into ONE start and demand both, (2) shorten the expiry self-check to
0.05s, never zero, and (3) skip the stdin half through ONE caller-declared
variable set outside the identity region - except in commit-msg, which hands
its checker on stdin.

WHAT EACH ARM PROVES, against the grant's conditions:

    declaration  each of the four copies declares CS_HOOK_STDIN_HALF exactly
                 once, outside the extracted probe, and only commit-msg runs it
    starts       the probe, run as a FILE the way the hooks run it, starts the
                 candidate once - and commit-msg once more, on stdin - and an
                 inherited environment value cannot make commit-msg skip it
    CS-703       every ARGUMENT_IGNORING_PROGRAMS entry, the ``| cat`` liar and
                 the endlocal shape are refused by all four copies, and the
                 honest wrapper is accepted by all four (the control)
    mutant       a probe that drops the 97 demand accepts the liar, so the liar
                 arms kill it; each mutation is asserted to have APPLIED
    expiry       the self-check bound is 0.05s, and non-zero

RUN AS A FILE. The grant's recorded residual is that no probe test ran the
probe as a FILE. Every arm here writes the copy's own probe bytes into a script
and runs that script with sh, which is how pre-commit and the wrapper run it.

MUTANTS ARE BUILT FROM TMP COPIES. No tracked file is ever modified here, so a
killed run cannot leave a mutant on disk.

PATHS STAY OUT OF EVERY ASSERTION MESSAGE. Every outcome is reduced to a bool,
an int or a short fixed string before it is asserted on (CLAUDE.md
non-negotiables 3 and 12).
"""

from __future__ import annotations

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
# answers the token and the 97; commit-msg adds the stdin half.
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

# The CS-703 shapes a probe must refuse. Bare names run as the candidate
# itself; shim bodies are written to a file first.
SHIM_SHAPES: Final = {"pipe-cat": LIAR_SHIM, "endlocal": ENDLOCAL_SHIM}
REFUSED_SHAPES: Final = tuple(ARGUMENT_IGNORING_PROGRAMS) + tuple(sorted(SHIM_SHAPES))

# The final grade line every copy ends cs_probe with, and the two mutants that
# drop the 97 demand. Each is (old, new) byte pairs that must ALL apply once.
FINAL_GRADE: Final = b'    [ "$cs_probe_code" = "$CS_PROBE_EXIT_EXPECTED" ]\n}'
MUTANTS: Final = {
    "grade-on-token-only": ((FINAL_GRADE, b'    [ "$cs_probe_out" = "$CS_PROBE_EXPECTED" ]\n}'),),
    "sentinel-made-zero": (
        (b"; sys.exit(97)'\n", b"'\n"),
        (b"\nCS_PROBE_EXIT_EXPECTED=97\n", b"\nCS_PROBE_EXIT_EXPECTED=0\n"),
    ),
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


def declaration_line(raw: bytes) -> bytes:
    """The copy's own stdin-half declaration line, or empty when it has none."""
    found = DECLARATION.search(raw)
    return found.group(0) + b"\n" if found else b""


def probe_file(raw: bytes) -> bytes:
    """A runnable script: a stub die, the copy's declaration, its probe, a tail."""
    return BLOCK_DIE + declaration_line(raw) + probe_block(raw) + BLOCK_TAIL


def run_probe(
    tmp_path: Path, raw: bytes, candidate: str, extra_env: dict[str, str] | None = None
) -> ProbeRun:
    """Run ``raw``'s probe as a FILE against ``candidate``, under the real timeout."""
    shell = require_posix_shell()
    script = tmp_path / "probe-under-test.sh"
    script.write_bytes(probe_file(raw))
    env = shell_environment(shell)
    for name in ("CLOCKSPEED_PYTHON", "PYTHONINSPECT", STDIN_HALF_NAME):
        env.pop(name, None)
    env.update(extra_env or {})
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


def candidate_for(tmp_path: Path, shape: str) -> str:
    """A bare program name as itself, or a shim body written out as a file."""
    if shape not in SHIM_SHAPES:
        return shape
    return Path(write_shim(tmp_path / "shapes", shape + ".sh", SHIM_SHAPES[shape])).as_posix()


def mutated(raw: bytes, mutant: str) -> bytes:
    """``raw`` with every replacement of ``mutant`` applied, each asserted to apply once."""
    out = raw
    for old, new in MUTANTS[mutant]:
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


# --- CS-703 -----------------------------------------------------------------


@pytest.mark.parametrize("shape", REFUSED_SHAPES)
@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_every_cs703_shape_is_refused_by_every_copy(
    tmp_path: Path, carrier: str, shape: str
) -> None:
    """true, ``:``, echo, the ``| cat`` liar and the endlocal shape: all refused, none died."""
    candidate = candidate_for(tmp_path, shape)
    run = run_probe(tmp_path, CARRIERS[carrier].read_bytes(), candidate)
    assert not run.died, f"{carrier}'s probe died on {shape} instead of refusing it"
    assert run.rc == REFUSED, f"{carrier}'s probe returned [{run.rc}] for {shape}"


@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_cs703_control_an_honest_wrapper_is_accepted_by_every_copy(
    tmp_path: Path, carrier: str
) -> None:
    """The non-vacuity control: a wrapper forwarding both channels passes."""
    honest = Path(write_shim(tmp_path / "shapes", "honest.sh", HONEST_SHIM)).as_posix()
    run = run_probe(tmp_path, CARRIERS[carrier].read_bytes(), honest)
    assert not run.died, f"{carrier}'s probe died on the honest wrapper"
    assert run.rc == ACCEPTED, f"{carrier}'s probe returned [{run.rc}] for the honest wrapper"


# --- mutant -----------------------------------------------------------------


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
@pytest.mark.parametrize("carrier", sorted(CARRIERS))
def test_a_mutant_dropping_the_97_demand_is_killed_by_the_liar(
    tmp_path: Path, carrier: str, mutant: str
) -> None:
    """Pristine refuses the liar; the mutant still accepts honest AND now accepts the liar.

    The middle clause is what makes the kill meaningful: a mutant that refused
    everything would also "differ" from pristine on the liar.
    """
    raw = CARRIERS[carrier].read_bytes()
    liar = candidate_for(tmp_path, "pipe-cat")
    pristine = run_probe(tmp_path, raw, liar)
    assert pristine.rc == REFUSED, f"pristine {carrier} returned [{pristine.rc}] for the liar"
    bad = mutated(raw, mutant)
    honest = run_probe(tmp_path, bad, REAL_PYTHON_POSIX)
    assert honest.rc == ACCEPTED, f"the {mutant} mutant of {carrier} refused a real interpreter"
    escaped = run_probe(tmp_path, bad, liar)
    assert escaped.rc == ACCEPTED, (
        f"the {mutant} mutant of {carrier} returned [{escaped.rc}] for the liar, so the liar "
        "arms cannot tell it from the pristine probe"
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
