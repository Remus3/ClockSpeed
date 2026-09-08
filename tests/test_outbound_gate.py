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
import subprocess
import sys
from pathlib import Path
from types import ModuleType

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
    env["USERNAME"] = "gatetestaccount"
    env["USER"] = "gatetestaccount"
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
