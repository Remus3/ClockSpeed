#!/usr/bin/env python3
"""Tests for tools/outbound_gate.py - the CS-957 outbound leak gate.

WHY THIS MODULE EXISTS. A responder that takes a class-A1 action - "read-only
measurement in own tree, REPORTED BACK" - writes nothing and can still carry a
home path, an account name, a platform account id or a world name out in the
reply. That breaks CLAUDE.md non-negotiable 3 without touching a byte on disk.
The outbound gate is the thing that reads a payload before it is sent.

THE DEFECT THIS SUITE EXISTS TO PREVENT REPRODUCING, MEASURED on this tree on
2026-09-08 rather than predicted. `tools/precommit_gate.py --text-stdin` fed a
payload carrying an absolute Windows home path prints
`PASS - 1 checked, 1 skipped, 0 blocking` and exits 0, while `check_pii` on
those identical bytes yields a `PII` diagnostic at line 1 col 19. The cause is
structural and is still visible at `tools/precommit_gate.py::mode_text_stdin`:
``mode_text_stdin`` calls ``check_charset`` and ``check_secrets`` and never
``check_pii``, while ``main`` builds ``PiiMatchers`` before dispatch. So the
gate a responder reaches for first prints a coverage-shaped reassurance and
scans none of the four personal-data classes. `test_planted_home_path_refuses`
and `test_coverage_lines_are_not_a_pii_verdict` are the two arms that make
that shape impossible here.

EVERY VIOLATING LITERAL IN THIS FILE IS ASSEMBLED FROM FRAGMENTS AT RUNTIME,
and that is a mechanism rather than a style. This file is itself scanned by
tools/precommit_gate.py, whose ``check_pii`` has NO placeholder escape - the
``NOT_?A_?SECRET`` allowance in ``PLACEHOLDER_RE`` covers the SECRET rules
only (tools/precommit_gate.py::PLACEHOLDER_RE). A spelled-out home path here would block
the commit that adds these tests. The gate's own source uses the same trick
for the same reason (tools/precommit_gate.py::PII_WIN_HOME_RE).

NO REAL PERSONAL VALUE IS EVER PLANTED, ASSERTED ON OR PRINTED. The three
save-derived arms seed the gate's OWN discovery overrides with synthetic
values and then read the value back out of the discovery function, so the
value under test genuinely came from ``discover_*`` and is still known to be
synthetic before the gate ever sees it. If discovery hands back anything other
than the seeded value the arm SKIPS rather than plants it - a machine whose
config leaked a real world in is a machine this suite refuses to test on.

ASSERTIONS BIND SCALARS BEFORE COMPARING. pytest rewrites `assert TEST` so the
sub-expressions of TEST render with their own reprs, independently of any
message (CS-850, tests/assertion_rendering_guard.py). An arm that wrote
`assert discovered_value not in stderr` would render the discovered value into
the failure report - the same leak in a different costume.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "outbound_gate.py"
PRECOMMIT_GATE = REPO_ROOT / "tools" / "precommit_gate.py"

# The closed exit set, named rather than spelled inline. Named because a bare
# `== 1` is both a ruff PLR2004 magic value and unreadable at the call site:
# the whole contract of this gate is WHICH code came back.
CLEAN = 0
REFUSED = 1
USAGE = 2
UNMEASURED = 3
CLOSED_EXIT_SET = frozenset({CLEAN, REFUSED, USAGE, UNMEASURED})

# The first byte that is not 7-bit ASCII. Named because ruff PLR2004 is right
# that a bare 0x80 in a comparison is unreadable, and because the whole of
# CLAUDE.md non-negotiable 4 is this one boundary.
FIRST_NON_ASCII_BYTE = 0x80

# The six classes the coverage block reports one row each for.
CLASSES = (
    "home-path",
    "account-name",
    "account-id",
    "world-name",
    "world-token",
    "credential",
)

# Assembled, never spelled out. See the module docstring.
WINDOWS_HOME_PATH = "C:" + "\\" + "Users" + "\\" + "someoperator" + "\\" + "notes.txt"
POSIX_HOME_PATH = "/" + "home" + "/someoperator" + "/app.log"

# A synthetic credential matching SECRET_PATTERNS' AWS rule
# (tools/precommit_gate.py::SECRET_PATTERNS) and matching no branch of PLACEHOLDER_RE, so
# the placeholder allowance cannot excuse it. Assembled, because the joined
# literal would be a finding in this very file.
SYNTHETIC_CREDENTIAL = "AKIA" + ("Q7" * 8)

# Synthetic seeds for the three save-derived classes. Each is above its
# matchability floor: MIN_ACCOUNT_DIR_CHARS is 8, MIN_WORLD_TOKEN_CHARS is 8
# and a world name is floored at MIN_ACCOUNT_NAME_CHARS, which is 3
# (tools/precommit_gate.py::MIN_ACCOUNT_NAME_CHARS). None of these exists on any real machine.
SEED_ACCOUNT_ID = "12345678901234567"
SEED_WORLD_NAME = "Zynthetiqua" + "Prime"
SEED_WORLD_TOKEN = "Zq7vNbXt41" + "KpRs93" + "MwYd2C"

# The synthetic account name every child environment in this module logs in
# as. Above MIN_ACCOUNT_NAME_CHARS, absent from GENERIC_ACCOUNT_NAMES
# (tools/precommit_gate.py::GENERIC_ACCOUNT_NAMES) and longer than
# outbound_gate.WARN_SHORT_CHARS, so a hit on it is a refusal and not a
# warning. Owned here rather than spelled inline in base_env, so the arm that
# plants it and the environment that discovers it cannot drift apart.
SEED_ACCOUNT_NAME = "gatetestaccount"

# Ordinary prose. Carries no path, no credential shape and no seeded value,
# and is the negative control the planted arms are graded against.
CLEAN_PAYLOAD = (
    "The solver returned an exact Fraction and the ratio closed at 2:3.\n"
    "Milestone gap is four recipes; power headroom is 180 MW.\n"
)

TIMEOUT = 180


def require_gate() -> None:
    """Fail loudly while tools/outbound_gate.py is absent.

    THIS IS THE ANTI-VACUITY LATCH FOR THE WHOLE MODULE and it is not
    ceremony. Run against a missing file the interpreter itself exits 2 with
    an ASCII message on stderr - which silently SATISFIES
    `test_exit_codes_are_closed_set`, `test_output_is_seven_bit_ascii` and
    `test_emit_is_not_reused`. Three of fourteen arms would report green
    against a module that does not exist. Routing every subprocess through
    this check makes the absence the failure instead of the result.
    """
    assert GATE.is_file(), (
        "tools/outbound_gate.py is absent; every arm in this module is vacuous until it exists"
    )


def base_env(tmp_path: Path) -> dict[str, str]:
    """A deterministic child environment that only ever REMOVES capability.

    The save root is pinned at a directory that does not exist and the local
    config at a file that does not exist, so the three save-derived classes
    are underivable and the account name is a value no machine logs in as.
    Nothing here GRANTS the child anything, which is what keeps the arms built
    on it honest on a bare CI box with no game installed and no save root - the
    condition BOOTSTRAP.md section 5.4 requires the rule suite to run under.

    The world overrides are popped rather than overwritten so an operator
    machine that declares a real world in config/local.json cannot feed a real
    value into any arm here.
    """
    env = dict(os.environ)
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        env.pop(key, None)
    env["USERNAME"] = SEED_ACCOUNT_NAME
    env["USER"] = SEED_ACCOUNT_NAME
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_gate(
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, bytes, bytes]:
    """Drive the CLI as a real subprocess and return (code, stdout, stderr).

    A SUBPROCESS because the exit code is half the contract, and RAW BYTES
    because `test_output_is_seven_bit_ascii` is a claim about bytes that a
    decode with errors="replace" would launder away. The call captures the
    code directly rather than through a shell pipeline: a pipe reports the
    last stage's status, so a refusal would read back as exit 0.
    """
    require_gate()
    proc = subprocess.run(
        [sys.executable, str(GATE), *args],
        input=stdin,
        capture_output=True,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def text(data: bytes) -> str:
    """Decode a captured stream for substring assertions, losing nothing."""
    return data.decode("utf-8", "replace")


def load_precommit_gate() -> ModuleType:
    """Import tools/precommit_gate.py by path, for the discovery functions.

    By path rather than `import tools.precommit_gate`, which is the idiom
    tests/test_precommit_gate.py already uses: it keeps tools/ out of this
    suite's import graph and does not depend on the shape of sys.path.
    """
    name = "clockspeed_precommit_gate_for_outbound_tests"
    spec = importlib.util.spec_from_file_location(name, PRECOMMIT_GATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module: the gate declares dataclasses under
    # `from __future__ import annotations`, and @dataclass resolves those
    # string annotations through sys.modules[cls.__module__].
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def seeded_discovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    env_name: str,
    seed: str,
    discover: str,
) -> str:
    """Seed one discovery override, run the real discovery, return the value.

    The value handed back genuinely came out of ``discover_*`` rather than out
    of this file, which is what the arms using it are about - but it came out
    of the override channel, which is source 1 of three and the highest
    precedence one (tools/precommit_gate.py::discover_world_names). So the value is discovered
    AND known synthetic, and the two properties do not trade against each
    other.

    Skips, with the discovery channel's own reason, when discovery yields
    nothing - the matchability filters at ``_matchable`` can legitimately drop
    a value, and an arm that planted the empty string would grade nothing.
    Skips ALSO when what comes back is not the seed: that means a real value
    reached the discovery path, and planting a real value is forbidden
    outright (CLAUDE.md non-negotiable 3).
    """
    gate = load_precommit_gate()
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-save-root"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    monkeypatch.setenv(env_name, seed)
    report = gate.Report()
    values = getattr(gate, discover)(report)
    if not values:
        reasons = "; ".join(why for _, why in report.skipped) or "no reason reported"
        pytest.skip(f"{discover} yielded no value on this machine: {reasons}")
    discovered = str(values[0])
    if len(values) != 1 or discovered != seed:
        pytest.skip(
            f"{discover} returned a value this suite did not seed; refusing to "
            "plant a possibly-real value"
        )
    return discovered


def assert_absent_in_any_case(needle: str, haystacks: tuple[bytes, ...]) -> None:
    """Assert a planted value appears in no stream, in no case variant.

    Binds a COUNT before asserting. `assert needle not in blob` would render
    both operands into the pytest failure report, which is the echo path
    CLAUDE.md non-negotiable 12 forbids; an integer renders safely.
    """
    folded_needle = needle.lower()
    assert folded_needle, "an empty needle would make this check vacuous"
    hits = sum(text(blob).lower().count(folded_needle) for blob in haystacks)
    assert hits == 0, f"a refusal echoed the planted value {hits} time(s)"


# --------------------------------------------------------------------------
# 1. The anti-vacuity arm - grades on a bare box with no save root at all
# --------------------------------------------------------------------------


def test_planted_home_path_refuses(tmp_path: Path) -> None:
    """Prove the gate scans the home-path class at all, on any machine.

    Both spellings, because PII_WIN_HOME_RE and PII_NIX_HOME_RE are separate
    rules and a gate wired to one of them is half-wired. This is the ONE arm
    that needs no save directory, no game install and no particular
    environment, so it is the arm that still grades where the three
    save-derived classes are permanently UNMEASURED.

    Were this arm absent, the exact measured defect - a stdin mode that prints
    a pass line and calls no PII check - would ship green.
    """
    for planted in (WINDOWS_HOME_PATH, POSIX_HOME_PATH):
        payload = ("See " + planted + " for details.\n").encode("ascii")
        code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)

        assert code == REFUSED, f"exit {code} for a planted home path; stdout {text(out)!r}"
        assert "outbound-gate: REFUSED" in text(err)
        assert "home-path" in text(err)
        assert "Nothing was sent." in text(err)


# --------------------------------------------------------------------------
# 2. The regression for the measured defect
# --------------------------------------------------------------------------


def test_coverage_lines_are_not_a_pii_verdict(tmp_path: Path) -> None:
    """Prove coverage rows and a PII scan happen in the SAME invocation.

    This is the regression for the shape measured on 2026-09-08: the stdin
    mode of tools/precommit_gate.py emits a reassuring coverage-shaped summary
    line and scans none of the personal-data classes. Splitting that into two
    arms - one that a coverage block is printed, one that a home path is
    caught - would pass against exactly that defect, because both are true of
    it separately and neither is true of it at once. So the assertion is
    conjunctive on ONE run.

    Were this arm absent, a gate that prints six UNMEASURED rows and scans
    nothing would satisfy the coverage requirement and the refusal requirement
    in different invocations and ship.
    """
    payload = ("See " + WINDOWS_HOME_PATH + " for details.\n").encode("ascii")
    code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)
    out_text = text(out)
    err_text = text(err)

    assert code == REFUSED, f"exit {code}; stdout {out_text!r}"
    assert "UNMEASURED" in out_text, "no coverage block on the run that refused"
    assert "home-path" in err_text, "coverage printed but the home path was not caught"
    missing = [name for name in CLASSES if name not in out_text]
    assert not missing, f"coverage block omitted {missing}"


# --------------------------------------------------------------------------
# 3-5. The save-derived classes
# --------------------------------------------------------------------------


def test_planted_account_id_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove a platform account id discovered at runtime is refused.

    The id is the class BOOTSTRAP.md section 2.2 calls out by name: the save
    subdirectory name is a platform account id and is personal data. It is
    seeded through the gate's own override and read back out of
    ``discover_account_ids``, so the arm grades the discovery path rather than
    a literal this file made up.

    Were this arm absent, a gate covering only the two classes derivable
    without a save root would pass every other arm here.
    """
    planted = seeded_discovery(
        monkeypatch, tmp_path, "CLOCKSPEED_ACCOUNT_DIR", SEED_ACCOUNT_ID, "discover_account_ids"
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_ACCOUNT_DIR"] = planted
    payload = ("account dir " + planted + " holds the saves\n").encode("ascii")
    code, out, err = run_gate(env=env, stdin=payload)

    assert code == REFUSED, f"exit {code}; stdout {text(out)!r}"
    assert "outbound-gate: REFUSED" in text(err)
    assert "account-id" in text(err)


def test_planted_world_name_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove a world name discovered at runtime is refused.

    Same shape as the account-id arm and a separate class on purpose: the
    contract forbids a pooled MEASURED flag precisely because a population
    threshold met by its strongest member leaves the weakest unmeasured while
    still passing.

    Were this arm absent, a gate that derived world names and never matched
    them would still report the class MEASURED.
    """
    planted = seeded_discovery(
        monkeypatch, tmp_path, "CLOCKSPEED_WORLD_NAMES", SEED_WORLD_NAME, "discover_world_names"
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_NAMES"] = planted
    payload = ("the world " + planted + " is at 12 GW\n").encode("ascii")
    code, out, err = run_gate(env=env, stdin=payload)

    assert code == REFUSED, f"exit {code}; stdout {text(out)!r}"
    assert "outbound-gate: REFUSED" in text(err)
    assert "world-name" in text(err)


def test_planted_world_token_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove a world token discovered at runtime is refused.

    The token is the value the advice ledger is keyed by, so it travels in
    exactly the diagnostic payloads a responder would report back.

    Were this arm absent, the class the ledger keys on would be the one class
    with no grading.
    """
    planted = seeded_discovery(
        monkeypatch, tmp_path, "CLOCKSPEED_WORLD_TOKENS", SEED_WORLD_TOKEN, "discover_world_tokens"
    )
    env = base_env(tmp_path)
    env["CLOCKSPEED_WORLD_TOKENS"] = planted
    payload = ("ledger key " + planted + " resolved\n").encode("ascii")
    code, out, err = run_gate(env=env, stdin=payload)

    assert code == REFUSED, f"exit {code}; stdout {text(out)!r}"
    assert "outbound-gate: REFUSED" in text(err)
    assert "world-token" in text(err)


# --------------------------------------------------------------------------
# 6. Credentials
# --------------------------------------------------------------------------


def test_planted_credential_refuses(tmp_path: Path) -> None:
    """Prove the credential class is scanned, using a real SECRET_PATTERNS shape.

    The value matches the AWS access key id rule at
    tools/precommit_gate.py::SECRET_PATTERNS and matches no branch of PLACEHOLDER_RE, so a
    refusal here cannot be the placeholder allowance firing by accident.
    Credentials are the second of the two classes derivable with no save root.

    Were this arm absent, a gate that imported ``check_secrets`` and never
    called it would pass every remaining arm.
    """
    payload = ("aws = " + '"' + SYNTHETIC_CREDENTIAL + '"' + "\n").encode("ascii")
    code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)

    assert code == REFUSED, f"exit {code}; stdout {text(out)!r}"
    assert "outbound-gate: REFUSED" in text(err)
    assert "credential" in text(err)


# --------------------------------------------------------------------------
# 7. The negative control
# --------------------------------------------------------------------------


def test_clean_payload_passes(tmp_path: Path) -> None:
    """THE NEGATIVE CONTROL. Ordinary prose is never refused.

    Exit is 0 or 3 and never 1 - 3 rather than 0 alone because on a machine
    with no save root three classes are legitimately underivable, and the
    contract makes CLEAN unreachable there by construction.

    Were this arm absent, a gate that refused every payload unconditionally
    would pass all six planted arms and every ordering arm besides. This is
    the only arm that distinguishes a filter from a wall.
    """
    code, out, err = run_gate(env=base_env(tmp_path), stdin=CLEAN_PAYLOAD.encode("ascii"))
    out_text = text(out)
    err_text = text(err)

    assert code != REFUSED, f"ordinary prose was refused; stderr {err_text!r}"
    assert code in {CLEAN, UNMEASURED}, f"exit {code} for ordinary prose"
    assert "REFUSED" not in err_text
    missing = [name for name in CLASSES if name not in out_text]
    assert not missing, f"coverage block omitted {missing} on a clean run"


# --------------------------------------------------------------------------
# 8. Non-negotiable 12 - the refusal is not itself an echo path
# --------------------------------------------------------------------------


def test_refusal_never_echoes_the_value(tmp_path: Path) -> None:
    """Prove a refusal names the class and the position, never the match.

    CLAUDE.md non-negotiable 12: a diagnostic is printed to a terminal and
    pasted into replies, so a diagnostic that echoes what it found is the same
    leak in a different costume. Checked over stdout AND stderr together,
    because a coverage row on stdout is just as much an echo path as a
    refusal line on stderr, and in any case variant, because a gate that
    lower-cased a value before printing it would still have printed it.

    Were this arm absent, the gate could refuse correctly and leak the value
    in the act of refusing - which is the failure mode that motivates the
    whole item.
    """
    for planted in (WINDOWS_HOME_PATH, POSIX_HOME_PATH, SYNTHETIC_CREDENTIAL):
        payload = ("value " + planted + " here\n").encode("ascii")
        code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)

        assert code == REFUSED, f"exit {code}; the echo check needs a refusal to grade"
        assert_absent_in_any_case(planted, (out, err))


# --------------------------------------------------------------------------
# 9-10. Vacuity, and the ordering between a finding and an unmeasured class
# --------------------------------------------------------------------------


def test_vacuity_is_not_clean(tmp_path: Path) -> None:
    """Prove an underivable class reports UNMEASURED rather than passing.

    The save root is pointed at an empty directory that really exists, so the
    three save-derived classes are underivable for the honest reason rather
    than because a path was malformed. CLOCKSPEED_SAVE_ROOT is the override
    ``save_root`` actually reads (tools/precommit_gate.py::save_root); the name is
    read out of the gate rather than invented here.

    CLEAN must never appear. A gate that could not derive three of six classes
    and still said CLEAN would be reporting a threshold met by its strongest
    member, which is exactly the pooled verdict the contract forbids.

    Were this arm absent, the gate could report CLEAN on a bare CI box and
    every planted arm would still pass.
    """
    empty_root = tmp_path / "empty-save-root"
    empty_root.mkdir()
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(empty_root)

    code, out, err = run_gate(env=env, stdin=CLEAN_PAYLOAD.encode("ascii"))
    out_text = text(out)

    assert code == UNMEASURED, f"exit {code}; stdout {out_text!r} stderr {text(err)!r}"
    assert "UNMEASURED" in out_text
    assert "CLEAN" not in out_text + text(err), "an underivable class was reported CLEAN"


def test_finding_dominates_unmeasured(tmp_path: Path) -> None:
    """Prove a finding outranks an unmeasured class: 1, never 3.

    Both conditions hold at once here - a planted home path AND an empty save
    root - which is the ordinary state on any machine without the game
    installed. A gate that resolved that pair to 3 would let a caller that
    treats 3 as advisory send a payload carrying a home path.

    Were this arm absent, the precedence between the two non-zero non-usage
    codes would be untested and either resolution would pass.
    """
    empty_root = tmp_path / "empty-save-root"
    empty_root.mkdir()
    env = base_env(tmp_path)
    env["CLOCKSPEED_SAVE_ROOT"] = str(empty_root)
    payload = ("See " + POSIX_HOME_PATH + " for details.\n").encode("ascii")

    code, out, err = run_gate(env=env, stdin=payload)
    out_text = text(out)

    assert code == REFUSED, f"exit {code}; a finding must dominate an unmeasured class"
    assert "UNMEASURED" in out_text, "the unmeasured half of the precondition did not hold"
    assert "home-path" in text(err)


# --------------------------------------------------------------------------
# 11. Fail closed on input the gate cannot read
# --------------------------------------------------------------------------


def test_undecodable_input_refuses(tmp_path: Path) -> None:
    """Prove undecodable bytes refuse rather than pass or crash.

    A payload that is not valid UTF-8 cannot be scanned, and a class that
    cannot be scanned on a payload that was nonetheless SENT is a leak the
    gate declined to look at. The contract makes the gate raising its own
    exception a 1 for the same reason: fail closed.

    The bytes are a lone continuation byte and a truncated multi-byte lead,
    which no decoder accepts and which no charset check can launder.

    Were this arm absent, a gate that wrapped its decode in a bare except and
    returned 0 would pass every other arm in this module.
    """
    payload = b"prefix " + bytes([0xFF, 0xFE, 0x80, 0xC3]) + b" suffix\n"
    code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)

    assert code == REFUSED, f"exit {code} on undecodable input; stdout {text(out)!r}"
    assert "REFUSED" in text(err)


# --------------------------------------------------------------------------
# 12-14. Properties of the output channel itself
# --------------------------------------------------------------------------


def test_output_is_seven_bit_ascii(tmp_path: Path) -> None:
    """Prove both streams stay 7-bit ASCII, on a clean run and on a refusal.

    CLAUDE.md non-negotiable 4 covers authored content, and a gate's output is
    authored content that gets pasted into a reply and into a .ps1 alike.
    Graded on BOTH outcomes because the refusal path is a different set of
    format strings from the pass path and is the one carrying a reason string.

    The offending bytes are collected as INTEGERS before asserting: rendering
    the stream itself into a pytest failure report would be the echo path the
    module docstring rules out.

    Were this arm absent, a reason string carrying an em dash would ship and
    would break a PowerShell 5.1 consumer at the tokenizer.
    """
    payloads = (
        CLEAN_PAYLOAD.encode("ascii"),
        ("See " + WINDOWS_HOME_PATH + " for details.\n").encode("ascii"),
    )
    for payload in payloads:
        code, out, err = run_gate(env=base_env(tmp_path), stdin=payload)
        offending = sorted(
            {byte for blob in (out, err) for byte in blob if byte >= FIRST_NON_ASCII_BYTE}
        )

        assert code in CLOSED_EXIT_SET, f"exit {code} outside the closed set"
        assert not offending, f"non-ASCII byte(s) {offending} in the gate output"


def test_exit_codes_are_closed_set(tmp_path: Path) -> None:
    """Prove every code the gate returns is one of 0, 1, 2 and 3.

    A caller branches on this set, so a fifth code is an unhandled branch at
    every call site. The subset check alone would be vacuous if no interesting
    path ran, so the arm also pins that the population actually contains a
    refusal and a usage error - two paths that are easy to conflate and that
    mean opposite things: 1 means something was found, 2 means nothing was
    scanned.

    Were this arm absent, an unexpected traceback exiting 70 or a bare `exit
    True` would be caught by nothing.
    """
    observed = set()
    code, _, _ = run_gate(env=base_env(tmp_path), stdin=CLEAN_PAYLOAD.encode("ascii"))
    observed.add(code)
    code, _, _ = run_gate(
        env=base_env(tmp_path),
        stdin=("See " + POSIX_HOME_PATH + "\n").encode("ascii"),
    )
    observed.add(code)
    code, _, _ = run_gate("--no-such-flag", env=base_env(tmp_path), stdin=b"")
    observed.add(code)

    assert observed <= CLOSED_EXIT_SET, f"codes outside the closed set: {observed}"
    assert REFUSED in observed, "no refusal was exercised; the subset check would be vacuous"
    assert USAGE in observed, "argparse did not report a usage error as 2"


def test_emit_is_not_reused(tmp_path: Path) -> None:
    """Prove the commit gate's PASS vocabulary never appears in this output.

    tools/precommit_gate.py::emit prints `PASS - %d checked, %d skipped, 0
    blocking`. That sentence means "safe to commit". This gate answers a
    different question - "safe to SEND" - and a caller that pattern-matches
    the familiar line would read an outbound verdict as a commit verdict. The
    idiom is banned rather than the function, because the risk is the reader's
    and not the implementation's.

    Graded on a clean run and a refusal, since a lazy implementation would
    reuse ``emit`` on the pass path specifically.

    Were this arm absent, the cheapest implementation of this gate - import
    ``emit`` and call it - would pass every other arm here.
    """
    payloads = (
        CLEAN_PAYLOAD.encode("ascii"),
        ("See " + WINDOWS_HOME_PATH + "\n").encode("ascii"),
    )
    for payload in payloads:
        _, out, err = run_gate(env=base_env(tmp_path), stdin=payload)
        both = text(out) + text(err)

        assert "PASS - " not in both, "the commit gate's PASS idiom was reused"
        assert "blocking" not in both, "the commit gate's blocking-count idiom was reused"


# --------------------------------------------------------------------------
# 15-18. THE COVERAGE ROWS' POLARITY, AND THE UNATTRIBUTED ORACLE BRANCH
#
# ADDED AFTER A MUTATION PASS REFUTED THE CLAIM THAT THE FOURTEEN ARMS ABOVE
# GRADE THIS MODULE. Ten mutants were planted in tools/outbound_gate.py and two
# shipped GREEN: ``_canary_measured`` hardcoded to ``return True``, and the
# oracle reconciliation inside ``scan`` no-op'd.
#
# Both survivors are of the module's OWN stated subject, which is what makes
# them worth four arms rather than one. A coverage block that reassures without
# measuring is the defect the gate exists to repair, reproduced inside the
# repair; and "a rule this module fails to attribute cannot become a rule it
# fails to enforce" is the sentence the reconciliation is the whole of.
#
# THE LAST TWO ARMS ARE DRIVEN IN-PROCESS, and that is forced rather than
# preferred. Both halves of the oracle comparison share one rule table, so the
# disagreement cannot be produced through the CLI by any payload; and a rule
# cannot be weakened from outside the process without editing a module this
# slice does not own. Every patch lands through the gate's own
# ``load_precommit_gate`` so it reaches the SAME module object ``scan``
# resolves, and pytest's monkeypatch restores each one at teardown.
# --------------------------------------------------------------------------

# A regex that matches nothing anywhere: `(?!)` is an empty negative lookahead,
# so it fails at every position of every string. It is the weakened rule the
# canary arm substitutes in, and it is deliberately a VALID pattern - a rule
# that raised on compile would make the arm a test about an exception.
NEVER_MATCHES = re.compile("(?!)")

# The phantom position the oracle is made to report in the last two arms. Line
# 4 is past the end of the payloads those arms scan, so the per-matcher half
# cannot produce it by any route and the reconciliation is the only thing that
# can turn it into a finding.
PHANTOM_LINE = 4
PHANTOM_COL = 17

# The marker the last arm's payload carries. Not personal data, not a
# credential shape, and matched by no rule - its only job is to be a value the
# rendered refusal must not echo.
PHANTOM_MARKER = "holes957" + "marker"


def load_outbound_gate() -> ModuleType:
    """Import tools/outbound_gate.py by path, for the in-process arms.

    By path for the same reason ``load_precommit_gate`` above is: tools/ has no
    ``__init__.py``, so the import form would depend on the shape of sys.path.
    Cached in sys.modules so repeated arms share one module object - which is
    also what lets ``monkeypatch.setattr`` reach the object ``scan`` uses.
    """
    require_gate()
    name = "clockspeed_outbound_gate_under_test"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, GATE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module, matching load_precommit_gate: the module
    # declares dataclasses under `from __future__ import annotations`, and
    # @dataclass resolves those string annotations through sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pin_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Give an in-process arm the capability-removing environment base_env gives.

    ``base_env`` builds a dict for a CHILD process; an arm that calls ``scan``
    inside the pytest process inherits this machine's real environment instead,
    where a save root and a real world name may both be discoverable. So the
    same removals are applied here through monkeypatch, which restores them at
    teardown. Nothing here grants the process anything.

    The outbound exclusion key is popped as well: an operator who has silenced
    a false positive on this machine would otherwise change what these arms
    measure. The key's NAME is read out of the gate rather than restated.
    """
    outbound = load_outbound_gate()
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-save-root"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv(outbound.ENV_OUTBOUND_EXCLUSIONS, raising=False)
    monkeypatch.setenv("USERNAME", "gatetestaccount")
    monkeypatch.setenv("USER", "gatetestaccount")


def coverage_verdict(out_text: str, klass: str) -> str:
    """Return the verdict word from the coverage ROW for `klass`.

    Reads one row rather than searching the whole block for the word
    UNMEASURED, and that difference is the hole this closes. On any machine
    with no save root three rows are legitimately unmeasured, so the word is
    present under EITHER polarity of the two canary rows - which is exactly how
    a ``_canary_measured`` hardcoded to True satisfied every arm above.
    """
    prefix = "  " + klass.ljust(14) + " "
    rows = [line for line in out_text.splitlines() if line.startswith(prefix)]
    assert len(rows) == 1, f"expected exactly one coverage row for {klass}, read {len(rows)}"
    word = rows[0][len(prefix) :].split(" ", 1)[0]
    assert word in {"MEASURED", "UNMEASURED"}, f"unreadable verdict word on the {klass} row"
    return word


def coverage_row_for(rows: object, klass: str) -> Any:
    """Return the single Coverage row for `klass` out of a `scan` result.

    Typed `Any` rather than `object` because the module under test is loaded by
    path at runtime, so its `Coverage` class is not a name this file can import
    without duplicating the loader. `object` was the honest first answer and it
    made every attribute read at the call sites a type error - four of them,
    caught by the repo-wide mypy gate rather than by the module's own run.
    """
    matching = [row for row in rows if row.klass == klass]  # type: ignore[attr-defined]
    assert len(matching) == 1, f"expected exactly one {klass} row, got {len(matching)}"
    return matching[0]


def patch_oracle_phantom(monkeypatch: pytest.MonkeyPatch, gate: ModuleType) -> None:
    """Make the commit gate's `check_pii` report one position no matcher can.

    The real oracle still runs, so everything the arms would otherwise observe
    is unchanged and only the disagreement is added. This is the ONLY way to
    reach the reconciliation branch: the per-matcher scan and ``check_pii``
    share one rule table, so end to end they cannot disagree.
    """
    real_check_pii = gate.check_pii

    def phantom_check_pii(label: str, payload: str, matchers: object, report: object) -> None:
        """Run the real oracle, then add a position the scan cannot produce."""
        real_check_pii(label, payload, matchers, report)
        report.add(  # type: ignore[attr-defined]
            gate.Diagnostic(label, PHANTOM_LINE, PHANTOM_COL, "PII", "a phantom oracle position")
        )

    monkeypatch.setattr(gate, "check_pii", phantom_check_pii)


def test_coverage_polarity_is_per_class(tmp_path: Path) -> None:
    """Prove each coverage row carries ITS OWN polarity, read by name.

    KILLS THE MUTANT ``_canary_measured`` HARDCODED TO ``return True``. That
    mutant shipped green against all fourteen arms above, demonstrated with a
    two-cell control: the home-path rule was replaced by a never-matching regex
    and the home-path row flipped between MEASURED and UNMEASURED while the
    suite reported the identical failure set both ways. No arm above reads a
    row; ``test_vacuity_is_not_clean`` and ``test_clean_payload_passes`` are
    satisfied by either polarity.

    On a machine with no save root the polarity is fully determined, and
    per-class rather than pooled is the module's own contract: home-path and
    credential are canary-derived and need no machine state, while the three
    save-derived classes are underivable. The account-name row is deliberately
    NOT pinned - its population comes from the environment, and it is the one
    row here that may legitimately differ between an operator box and a bare
    runner. It is still required to render a legible verdict word.

    The two canary rows are asserted as their WHOLE rendered text, so a gate
    reporting MEASURED against a reason describing something else fails too.
    """
    code, out, err = run_gate(env=base_env(tmp_path), stdin=CLEAN_PAYLOAD.encode("ascii"))
    out_text = text(out)

    assert code == UNMEASURED, f"exit {code}; stderr {text(err)!r}"
    verdicts = {name: coverage_verdict(out_text, name) for name in CLASSES}
    expected = {
        "home-path": "MEASURED",
        "account-id": "UNMEASURED",
        "world-name": "UNMEASURED",
        "world-token": "UNMEASURED",
        "credential": "MEASURED",
    }
    actual = {name: verdicts[name] for name in expected}
    assert actual == expected, "a coverage row reported the wrong polarity"

    lines = out_text.splitlines()
    for name in ("home-path", "credential"):
        row = "  " + name.ljust(14) + " MEASURED    canary matched"
        assert row in lines, f"the {name} row is not a canary verdict"


def test_canary_row_is_derived_not_asserted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove the home-path coverage row MEASURES the rules it reports on.

    KILLS THE MUTANT ``_canary_measured`` HARDCODED TO ``return True``, and its
    mirror image - a constant False - in the same arm. A two-cell control in
    ONE invocation each: the same scan runs against the real rules and then
    against a regex that cannot match, and the row must FLIP. A row that is a
    constant cannot flip, and a row that flips is not a constant. That is the
    property ``_canary_measured``'s own docstring claims and that nothing else
    in this suite checked.

    The refusal counts are asserted alongside the rows, so the weakened cell is
    known to have actually disarmed the rule rather than merely to have been
    reported as disarmed - the same conjunctive shape
    ``test_coverage_lines_are_not_a_pii_verdict`` uses, for the same reason.
    """
    outbound = load_outbound_gate()
    pin_environment(monkeypatch, tmp_path)
    payload = "See " + WINDOWS_HOME_PATH + " and " + POSIX_HOME_PATH + " here.\n"

    healthy_refusals, _, healthy_rows = outbound.scan(payload)
    healthy_row = coverage_row_for(healthy_rows, "home-path")
    healthy_hits = sum(1 for finding in healthy_refusals if finding.klass == "home-path")

    assert healthy_row.measured is True, "the home-path canary failed against the real rules"
    assert healthy_row.reason == "canary matched"
    assert healthy_hits > 0, "the control cell caught nothing; the weakened cell would prove little"

    gate = outbound.load_precommit_gate()
    monkeypatch.setattr(gate, "PII_WIN_HOME_RE", NEVER_MATCHES)
    monkeypatch.setattr(gate, "PII_NIX_HOME_RE", NEVER_MATCHES)

    weakened_refusals, _, weakened_rows = outbound.scan(payload)
    weakened_row = coverage_row_for(weakened_rows, "home-path")
    weakened_hits = sum(1 for finding in weakened_refusals if finding.klass == "home-path")

    assert weakened_hits == 0, "the substituted rule still matched; the cell is not weakened"
    assert weakened_row.measured is False, "a home-path rule that catches nothing read MEASURED"
    assert weakened_row.reason == "the rules failed their canary"


def test_oracle_disagreement_becomes_unattributed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove a position only the oracle reports is still refused.

    KILLS THE MUTANT THAT NO-OP'D THE RECONCILIATION in ``scan``. That mutant
    shipped green at 14 passed: an instrumented reachability probe with a
    known-good control showed the ``unattributed`` branch is not entered once
    across every arm above. It is not dead code - it silently backstops other
    arms, and disabling the home-path scan alone reddens three arms while
    disabling the scan AND the reconciliation reddens five, so two arms were
    being held green by the oracle rather than by what they claim to grade.

    The payload is ordinary prose that yields no finding at all, so the only
    thing that can produce a refusal here is the reconciliation. The verdict is
    asserted alongside the finding because attribution without enforcement is
    the failure the module's docstring rules out in as many words.
    """
    outbound = load_outbound_gate()
    pin_environment(monkeypatch, tmp_path)
    gate = outbound.load_precommit_gate()

    clean_refusals, _, _ = outbound.scan(CLEAN_PAYLOAD)
    assert not clean_refusals, "the payload is not clean; the disagreement would be ambiguous"

    patch_oracle_phantom(monkeypatch, gate)
    refusals, _, coverage = outbound.scan(CLEAN_PAYLOAD)
    positions = [(finding.klass, finding.line, finding.col) for finding in refusals]

    assert positions == [("unattributed", PHANTOM_LINE, PHANTOM_COL)], (
        "the oracle's extra position was not attributed to the unattributed class"
    )
    assert outbound.verdict(refusals, coverage) == REFUSED, (
        "an unattributed finding was reported but did not refuse"
    )


def test_unattributed_refusal_names_the_class_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove the rendered unattributed line names the class and echoes nothing.

    KILLS THE SAME RECONCILIATION MUTANT from the reporting side: a gate that
    dropped the branch renders no line here at all. It also extends
    ``test_refusal_never_echoes_the_value`` to the one class that arm cannot
    reach - the unattributed line is rendered from a position with no matcher
    behind it, so it is the refusal most likely to reach for the payload to
    explain itself, and CLAUDE.md non-negotiable 12 forbids exactly that.

    The marker is checked through ``assert_absent_in_any_case``, which binds a
    count before asserting so the failure report cannot render the value it is
    complaining about.
    """
    outbound = load_outbound_gate()
    pin_environment(monkeypatch, tmp_path)
    gate = outbound.load_precommit_gate()
    patch_oracle_phantom(monkeypatch, gate)

    payload = "a note carrying " + PHANTOM_MARKER + " and nothing else\n"
    refusals, warnings, coverage = outbound.scan(payload)
    _, err = outbound.render(refusals, warnings, coverage)

    assert "outbound-gate: REFUSED" in err
    assert "<pii:unattributed>" in err, "the refusal line does not name the class"
    assert "line %d col %d" % (PHANTOM_LINE, PHANTOM_COL) in err, "the position is not reported"
    assert "disagreed with this gate's attribution" in err, "the reason does not say what happened"
    assert_absent_in_any_case(PHANTOM_MARKER, (err.encode("ascii"),))


# --------------------------------------------------------------------------
# 19. The environment-derived class - account name
# --------------------------------------------------------------------------


def test_planted_account_name_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove this machine's account name is refused, and that prose is not.

    THE ONE CLASS THAT GRADES EVERYWHERE AND HAD NO ARM. Its population comes
    from USERNAME/USER (tools/precommit_gate.py::current_account_names) rather
    than from a save root, so unlike account-id, world-name and world-token it
    is derivable on a bare CI box with no game installed and no save
    directory - and it was the one name in ``CLASS_ORDER`` with no planted
    arm. The three arms that DO plant a value are exactly the three that skip
    or report UNMEASURED there. So a silently weakened account-name rule
    reddened nothing in this suite on precisely the machines where this suite
    is the only thing grading.

    Were this arm absent, an account-name rule that matched nothing would pass
    every other arm in this module: the coverage row is not pinned, no planted
    arm reaches the class, and the negative control cannot tell a rule that
    catches nothing from a rule with nothing to catch.

    THE ARM GRADES THE REFUSAL AND PINS NO COVERAGE ROW.
    ``test_coverage_polarity_is_per_class`` declines to pin the account-name
    row because its population is environment-derived and may legitimately
    differ between an operator box and a bare runner; nothing here pins it
    either. Asserting the refusal is the stronger claim anyway - a row cannot
    read MEASURED while the value it was derived from goes unrefused - and it
    is the claim that makes the oracle observe its own subject: the assertion
    is on the ``<pii:account-name>`` class in the refusal, not on a non-zero
    exit that any other class could have produced.

    THE NEGATIVE CONTROL IS IN THIS ARM, under the same pinned environment and
    the same discovered value, because a wall refuses ordinary prose too.

    The value is read back out of ``current_account_names`` rather than taken
    from this file, the same shape ``seeded_discovery`` gives the three
    save-derived arms, so what gets planted genuinely came out of discovery
    and is still known synthetic before the gate sees it.

    Placed last rather than beside the other planted arms so the numbered
    sections above - and the arm counts two of them record from a mutation
    measurement taken before this arm existed - stay true to what was
    measured.
    """
    # Both keys, matching base_env: current_account_names reads USERNAME then
    # USER, and a real USER left standing would make discovery return a second
    # value and skip this arm on exactly the machine it is meant to grade.
    monkeypatch.setenv("USER", SEED_ACCOUNT_NAME)
    planted = seeded_discovery(
        monkeypatch, tmp_path, "USERNAME", SEED_ACCOUNT_NAME, "current_account_names"
    )
    env = base_env(tmp_path)
    payload = ("the operator " + planted + " ran the audit\n").encode("ascii")
    code, out, err = run_gate(env=env, stdin=payload)
    err_text = text(err)
    named = err_text.count("<pii:account-name>")

    assert code == REFUSED, f"exit {code} for a planted account name; stdout {text(out)!r}"
    assert "outbound-gate: REFUSED" in err_text
    assert named > 0, "the refusal does not name the account-name class"
    assert_absent_in_any_case(planted, (out, err))

    clean_code, clean_out, clean_err = run_gate(env=env, stdin=CLEAN_PAYLOAD.encode("ascii"))
    clean_named = (text(clean_out) + text(clean_err)).count("<pii:account-name>")

    assert clean_code != REFUSED, f"ordinary prose was refused; stderr {text(clean_err)!r}"
    assert clean_code in {CLEAN, UNMEASURED}, f"exit {clean_code} for ordinary prose"
    assert clean_named == 0, "the account-name class fired on prose carrying no account name"
