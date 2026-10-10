"""CS-1175 - a secret rule narrowed by its flags, a quantifier or a class reddens.

THE DEFECT. CS-1172 graded every rule per BRANCH, and nothing else. A rule
narrowed WITHOUT touching a branch - its case-insensitive flag dropped, its
word-prefix quantifier dropped or shortened, a length quantifier's minimum
raised, or a member range removed from a character class - still matched
every filed canary, so the credential row stayed MEASURED. MEASURED on the
CS-1172 candidate by the adversary pass that could not refute it.

WHY A FINGERPRINT AND NOT A CANARY, for all four kinds. A canary can only
see a narrowing if it encodes the rule's PRISTINE shape: the boundary
length, the case, the class endpoint. Derived from the LIVE rule, it is
derived from the already-narrowed rule, so it matches that rule and the row
stays green - circular. Recorded, it is a hand list. So the pin is the
fingerprint `tools/outbound_gate.py::credential_rule_fingerprint` DERIVES from
each compiled rule - its flags, a digest of its source, every quantifier with
its bounds and every class atom with its members, under a quantifier or not -
checked against `CREDENTIAL_RULE_FINGERPRINTS`. Any change to a rule's source
or flags reddens the row, naming the rule and what changed, and is re-recorded
deliberately from `--print-fingerprints` output.

EVERY PLANT IS INDEPENDENT. Each mutation edits a rule's SOURCE TEXT in-test
and recompiles it, never through the module's own derivation, and never by
touching the frozen `tools/precommit_gate.py` on disk.

NO CANARY IS HELD IN A LOCAL. The last arm forces every canary arm red in a
child run under `--showlocals` and counts canary values in what it printed.
"""

from __future__ import annotations

import importlib.util
import operator
import os
import re
import subprocess
import sys
from itertools import chain
from pathlib import Path
from types import ModuleType

import pytest

from tests.test_canary_population import (
    CHILD_FLAG,
    DERIVATION_ARMS,
    derived_canary_suites,
    issue_child_flag,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTBOUND_PATH = REPO_ROOT / "tools" / "outbound_gate.py"

#: Private to this file, so no other suite's patches can reach this copy.
OUTBOUND_MODULE_NAME = "clockspeed_outbound_gate_for_cs1175"

TIMEOUT = 300

#: CS-1301: the largest exit a process reports for itself; past it, the
#: number is a Windows status the child died with.
LAST_REPORTED_EXIT = 255

_QUOTED = "credential assigned a quoted literal of 16 or more characters"
_ENTROPY = "credential assigned a bare high-entropy literal"


def load_outbound() -> ModuleType:
    """Load the outbound gate by path under a module name private to this file."""
    cached = sys.modules.get(OUTBOUND_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(OUTBOUND_MODULE_NAME, OUTBOUND_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[OUTBOUND_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


OUTBOUND = load_outbound()
GATE = OUTBOUND.load_precommit_gate()

#: (kind, rule reason, old source text, new source text, flags to clear, the
#: phrase the row must carry). One plant per kind at least; the kinds are the
#: acceptance's own four. Old and new are raw source fragments of the rule.
PLANTS: tuple[tuple[str, str, str, str, int, str], ...] = (
    ("flag", _QUOTED, "(?i)", "", re.IGNORECASE, "flag IGNORECASE dropped"),
    ("flag", _ENTROPY, "(?i)", "", re.IGNORECASE, "flag IGNORECASE dropped"),
    ("prefix-drop", _ENTROPY, r"\b\w*(?:", r"\b(?:", 0, r"quantifier \w* dropped"),
    (
        "prefix-shorten",
        _ENTROPY,
        r"\b\w*(?:",
        r"\b\w{0,3}(?:",
        0,
        r"maximum of \w* lowered unbounded -> 3",
    ),
    (
        "min-raise",
        "GitHub token",
        "{20,}",
        "{21,}",
        0,
        "minimum of [A-Za-z0-9]{20,} raised 20 -> 21",
    ),
    ("min-raise", _QUOTED, "{16,}", "{17,}", 0, "raised 16 -> 17"),
    (
        "min-raise",
        "AWS access key id",
        "{16}",
        "{17}",
        0,
        "minimum of [0-9A-Z]{16} raised 16 -> 17",
    ),
    (
        "class-range",
        "GitHub token",
        "[A-Za-z0-9]{20,}",
        "[a-z0-9]{20,}",
        0,
        "member A-Z removed from [A-Za-z0-9]{20,}",
    ),
    (
        "class-range",
        "PEM private key block",
        "[A-Z0-9 ]",
        "[A-Z ]",
        0,
        "member 0-9 removed from [A-Z0-9 ]{0,32}",
    ),
    ("class-member", "bearer token", "._~+/=-]", "._+/=-]", 0, "member ~ removed from"),
    # REPAIR F1: a class that NO quantifier repeats. Before the repair the
    # fingerprint held only quantifiers, so these four read MEASURED.
    (
        "class-unquantified",
        "PuTTY private key file",
        "-\\d",
        "-[0-8]",
        0,
        "member \\d removed from \\d",
    ),
    (
        "class-unquantified",
        "PuTTY private key file",
        "-\\d",
        "-[0-9]",
        0,
        "member \\d removed from \\d",
    ),
    (
        "class-unquantified",
        _ENTROPY,
        "*[0-9][",
        "*[0-8][",
        0,
        "member 0-9 removed from [0-9]",
    ),
    (
        "class-unquantified",
        _ENTROPY,
        "*[0-9])",
        "*[0-8])",
        0,
        "member 0-9 removed from [0-9]",
    ),
    # REPAIR F2: a change outside every flag, quantifier and class - here an
    # anchor the canaries still satisfy - is named too.
    (
        "other",
        "Anthropic API or admin key (vendor prefix)",
        "{20,}",
        "{20,}\\b",
        0,
        "a change outside its flags, quantifiers and classes",
    ),
)

#: Floors for the pinned population: two case-insensitive rules, one word
#: prefix, and at least three rules with a length minimum and a class range.
MIN_FOLDED = 2
MIN_FLOORED = 3
MIN_RANGED = 3

#: The acceptance's four kinds; the plants above must reach every one.
KINDS = frozenset(
    {"flag", "prefix-drop", "prefix-shorten", "min-raise", "class-range", "class-unquantified"}
)


def pin_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Remove every machine-derived capability, so only the canary rows vary."""
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-save-root"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local-config.json"))
    for key in ("CLOCKSPEED_WORLD_NAMES", "CLOCKSPEED_WORLD_TOKENS", "CLOCKSPEED_ACCOUNT_DIR"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv(OUTBOUND.ENV_OUTBOUND_EXCLUSIONS, raising=False)
    monkeypatch.setenv("USERNAME", "gatetestaccount")
    monkeypatch.setenv("USER", "gatetestaccount")


def credential_row(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[bool, str]:
    """Scan a clean payload and return the credential row as (measured, reason)."""
    pin_environment(monkeypatch, tmp_path)
    _, _, rows = OUTBOUND.scan("ordinary prose\n")
    matching = [row for row in rows if row.klass == OUTBOUND.CLASS_CREDENTIAL]
    count = len(matching)
    assert count == 1, "expected exactly one credential row, got %d" % count
    return bool(matching[0].measured), str(matching[0].reason)


def planted(reason: str, old: str, new: str, clear: int) -> list[tuple[re.Pattern[str], str]]:
    """The rule list with ONE rule's source edited, asserting the edit landed."""
    rules: list[tuple[re.Pattern[str], str]] = []
    landed = 0
    for pattern, rule_reason in GATE.SECRET_PATTERNS:
        if rule_reason == reason and old in pattern.pattern:
            source = pattern.pattern.replace(old, new, 1)
            rules.append((re.compile(source, pattern.flags & ~clear), reason))
            landed += 1
        else:
            rules.append((pattern, rule_reason))
    assert landed == 1, "the plant did not land on exactly one rule: " + reason
    changed = rules != list(GATE.SECRET_PATTERNS)
    assert changed, "the plant left the rule list unchanged: " + reason
    return rules


# --------------------------------------------------------------------------
# Arm 1 - every narrowing kind reddens the row, naming the rule and the change
# --------------------------------------------------------------------------


def test_the_plants_reach_every_kind() -> None:
    """Anti-vacuity: the mutation table covers each of the acceptance's kinds."""
    reached = {plant[0] for plant in PLANTS}
    missing = sorted(KINDS - reached)
    assert not missing, "no plant for kind(s): " + ", ".join(missing)


@pytest.mark.parametrize(
    ("kind", "reason", "old", "new", "clear", "phrase"),
    PLANTS,
    ids=["%s-%d" % (plant[0], number) for number, plant in enumerate(PLANTS)],
)
def test_a_narrowed_rule_reddens_the_row_by_rule_and_change(
    kind: str,
    reason: str,
    old: str,
    new: str,
    clear: int,
    phrase: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """One narrowing of one rule turns the row UNMEASURED and names both.

    The pristine row is read in the SAME test as the control, so a row that
    was already red cannot pass this arm by accident.
    """
    healthy, healthy_reason = credential_row(monkeypatch, tmp_path)
    assert healthy is True, "the pristine row is not MEASURED: " + healthy_reason

    monkeypatch.setattr(GATE, "SECRET_PATTERNS", planted(reason, old, new, clear))
    measured, row_reason = credential_row(monkeypatch, tmp_path)
    assert measured is False, "a rule narrowed by kind %s read MEASURED: %s" % (kind, reason)
    named = (reason + " / fingerprint") in row_reason
    changed = phrase in row_reason
    assert named, "the row did not name the narrowed rule: " + reason
    assert changed, "the row did not name what narrowed (%s): %s" % (phrase, row_reason)


def test_a_widening_reddens_too(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """ANY change is named, so the pin is re-recorded deliberately, never drifted past."""
    rules = planted("GitHub token", "{20,}", "{19,}", 0)
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", rules)
    measured, row_reason = credential_row(monkeypatch, tmp_path)
    changed = "minimum of [A-Za-z0-9]{20,} lowered 20 -> 19" in row_reason
    assert measured is False, "a widened rule read MEASURED"
    assert changed, row_reason


# --------------------------------------------------------------------------
# Arm 2 - the recorded pin cannot drift from the rules it certifies
# --------------------------------------------------------------------------


def test_the_tree_as_it_stands_has_no_fingerprint_gap() -> None:
    """The control for every mutation above: pristine, nothing is named."""
    gaps = OUTBOUND.credential_fingerprint_gaps(GATE)
    count = len(gaps)
    assert count == 0, "; ".join(gaps)


def test_every_rule_has_a_recorded_fingerprint_and_none_is_stale() -> None:
    """The recorded table and the live rule list name exactly the same rules."""
    live = {reason for _, reason in GATE.SECRET_PATTERNS}
    recorded = set(OUTBOUND.CREDENTIAL_RULE_FINGERPRINTS)
    stale = sorted(recorded - live)
    missing = sorted(live - recorded)
    assert not stale, "fingerprints for no such rule: " + ", ".join(stale)
    assert not missing, "rules with no fingerprint: " + ", ".join(missing)


def test_the_recorded_population_reaches_every_kind() -> None:
    """Anti-vacuity: the pinned rules carry each kind the acceptance names.

    Read off the DERIVED fingerprints, so a renderer that dropped a whole
    kind - say, every class member - would leave this arm with nothing.
    """
    prints = [OUTBOUND.credential_rule_fingerprint(pattern) for pattern, _ in GATE.SECRET_PATTERNS]
    folded = sum(1 for fp in prints if "IGNORECASE" in fp[0].split())
    prefixed = sum(1 for fp in prints if "quantifier \\w*" in fp)
    unquantified = sum(1 for fp in prints if "class \\d" in fp)
    floored = sum(1 for fp in prints for q in fp[1:] if re.search(r"\{[1-9]\d*[,}]", q))
    ranged = sum(1 for fp in prints for q in fp[1:] if re.search(r"\[[^\]]*\w-\w", q))
    assert folded >= MIN_FOLDED, "case-insensitive rules pinned: %d" % folded
    assert prefixed >= 1, "word-prefix quantifiers pinned: %d" % prefixed
    assert unquantified >= 1, "classes no quantifier repeats pinned: %d" % unquantified
    assert floored >= MIN_FLOORED, "length minimums pinned: %d" % floored
    assert ranged >= MIN_RANGED, "classes with a member range pinned: %d" % ranged


def test_a_rule_with_no_recorded_fingerprint_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """A rule added upstream with no pin is a gap by name, with no edit here."""
    fake = "cs1175 planted rule with no fingerprint"
    monkeypatch.setattr(GATE, "SECRET_PATTERNS", [*GATE.SECRET_PATTERNS, (re.compile("x"), fake)])
    gaps = OUTBOUND.credential_fingerprint_gaps(GATE)
    matched = gaps == [fake + " (no recorded fingerprint)"]
    assert matched, "; ".join(gaps)


def test_a_fingerprint_for_no_such_rule_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """A pin for a rule the list no longer has is drift, named."""
    fake = "cs1175 recorded fingerprint with no rule"
    table = dict(OUTBOUND.CREDENTIAL_RULE_FINGERPRINTS)
    table[fake] = ("flags UNICODE",)
    monkeypatch.setattr(OUTBOUND, "CREDENTIAL_RULE_FINGERPRINTS", table)
    gaps = OUTBOUND.credential_fingerprint_gaps(GATE)
    matched = gaps == [fake + " (fingerprint for no such rule)"]
    assert matched, "; ".join(gaps)


def test_an_underivable_parser_names_every_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the private parser API moves, every rule is named, never called pinned."""

    class Moved:
        """A parser whose entry point is gone."""

        def parse(self, *_: object) -> object:
            """Raise as a moved private API would."""
            message = "parse moved"
            raise AttributeError(message)

    monkeypatch.setattr(OUTBOUND, "_RE_PARSER", Moved())
    gaps = OUTBOUND.credential_fingerprint_gaps(GATE)
    suffix = " (its fingerprint could not be derived)"
    matched = gaps == [reason + suffix for _, reason in GATE.SECRET_PATTERNS]
    assert matched, "; ".join(gaps)


def run_print_fingerprints() -> tuple[int, str, str]:
    """Run the CLI's `--print-fingerprints` mode: (exit, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(OUTBOUND_PATH), "--print-fingerprints"],
        capture_output=True,
        cwd=REPO_ROOT,
        timeout=TIMEOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.decode("ascii"), proc.stderr.decode("ascii")


def test_print_fingerprints_emits_the_table_as_source() -> None:
    """REPAIR F3: re-recording is deliberate but never hand-typed.

    The printed source, executed with the module's own reason constants, is
    exactly the live derivation - and on the pristine tree, exactly the
    recorded table. It prints; it never rewrites a file.
    """
    before = OUTBOUND_PATH.read_bytes()
    code, out, err = run_print_fingerprints()
    after = OUTBOUND_PATH.read_bytes()
    assert code == 0, "exit %d: %s" % (code, err)
    unchanged = before == after
    assert unchanged, "--print-fingerprints rewrote the module"
    namespace: dict[str, object] = {}
    exec(out, namespace)  # noqa: S102 - the module's own printed source
    printed = namespace["CREDENTIAL_RULE_FINGERPRINTS"]
    live = {
        reason: OUTBOUND.credential_rule_fingerprint(pattern)
        for pattern, reason in GATE.SECRET_PATTERNS
    }
    derived = printed == live
    recorded = printed == OUTBOUND.CREDENTIAL_RULE_FINGERPRINTS
    assert derived, "the printed table is not the live derivation"
    assert recorded, "the printed table is not the recorded one on a pristine tree"


# --------------------------------------------------------------------------
# Arm 3 - a MISSING private regex module degrades the row by name, measured
# --------------------------------------------------------------------------

#: Imports `re` FIRST, as every real run has it, then blocks one private
#: module, then runs the gate as a script on clean prose.
BLOCKER = """
import io, re, runpy, sys
sys.modules[%r] = None
sys.argv = ["outbound_gate.py"]
sys.stdin = io.TextIOWrapper(io.BytesIO(b"ordinary prose\\n"))
runpy.run_path(%r, run_name="__main__")
"""


@pytest.mark.parametrize("blocked", ["re._parser", "re._constants"])
def test_a_missing_private_regex_module_names_every_rule(blocked: str, tmp_path: Path) -> None:
    """The gate still runs, prints no traceback, and names every rule UNMEASURED.

    MEASURED before CS-1175: the module-level import raised
    ModuleNotFoundError, the script died with a traceback carrying absolute
    file paths, and printed no coverage block at all.
    """
    script = tmp_path / "cs1175_blocker.py"
    script.write_text(BLOCKER % (blocked, str(OUTBOUND_PATH)), encoding="ascii")
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=TIMEOUT,
        check=False,
    )
    output = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    crashed = "Traceback" in output
    assert not crashed, "the gate crashed with a traceback when %s was missing" % blocked
    assert proc.returncode == OUTBOUND.EXIT_UNMEASURED, "exit %d" % proc.returncode
    rows = [line for line in output.splitlines() if line.strip().startswith("credential ")]
    count = len(rows)
    assert count == 1, "credential rows printed: %d" % count
    unmeasured = "UNMEASURED" in rows[0]
    assert unmeasured, "the credential row read measured with %s missing" % blocked
    unnamed = [
        reason
        for _, reason in GATE.SECRET_PATTERNS
        if reason + " (its branches could not be derived)" not in rows[0]
        or reason + " (its fingerprint could not be derived)" not in rows[0]
    ]
    assert not unnamed, "rules not named underivable: " + ", ".join(unnamed)


# --------------------------------------------------------------------------
# Arm 4 - no canary renders under --showlocals when every arm is forced red
# --------------------------------------------------------------------------

#: Loaded by the child run; forces every secret rule to match nothing, so
#: every canary arm goes red at once.
FORCER = """
import importlib.util, re, sys
from pathlib import Path

NAME = "clockspeed_precommit_gate_for_outbound_gate"


def pytest_configure(config):
    path = Path(%r) / "tools" / "precommit_gate.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = module
    spec.loader.exec_module(module)
    never = re.compile("(?!)")
    module.SECRET_PATTERNS[:] = [(never, reason) for _, reason in module.SECRET_PATTERNS]
"""

#: The positive control: a failing test that holds a canary in a LOCAL and
#: asserts only on a scalar, so assertion rewriting alone renders nothing and
#: only `--showlocals` can put the value on screen.
LEAKY = """
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs1175_leaky_outbound", Path(%r))
module = importlib.util.module_from_spec(spec)
sys.modules["cs1175_leaky_outbound"] = module
spec.loader.exec_module(module)


def test_holds_a_canary_in_a_local():
    held = module.CREDENTIAL_CANARIES["AWS access key id"]
    size = len(held)
    assert size == 0
"""

#: Every suite whose arms read canary values - DERIVED, never typed. CS-1177
#: retired the hand-kept tuple this name used to hold: the membership rule and
#: its derivation live in tests/test_canary_population.py, so a new module that
#: reads a canary table is run by the forced arm below without an edit here.
CANARY_SUITES = derived_canary_suites()


def canaries_in(output: str) -> int:
    """How many canary values, from either table, appear in `output`.

    A helper, so the values never become a local of a test frame that
    `--showlocals` would render. CS-1177: and never a named local of THIS
    frame or of a generator inside it either, since a helper that raises has
    its locals rendered too - the values only ever live on the stack.
    """
    return sum(
        map(
            output.count,
            chain(
                OUTBOUND.CREDENTIAL_CANARIES.values(),
                chain.from_iterable(
                    map(
                        operator.methodcaller("values"),
                        OUTBOUND.CREDENTIAL_BRANCH_CANARIES.values(),
                    )
                ),
            ),
        )
    )


def child_pytest(tmp_path: Path, args: list[str]) -> tuple[int, str]:
    """Run pytest in a child with `tmp_path` importable; return (code, output).

    CS-1193: the child is told it is a forced child, by a nonce issued for it
    alone, so the canary population suite's derivation-only arms skip there -
    the parent derived and graded them already.
    """
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")}
    env["PYTHONPATH"] = str(tmp_path)
    env[CHILD_FLAG], held = issue_child_flag(tmp_path / "cs1193_flag")
    env["CLOCKSPEED_SAVE_ROOT"] = str(tmp_path / "absent-save-root")
    env["CLOCKSPEED_LOCAL_CONFIG"] = str(tmp_path / "absent-local-config.json")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-vv", "-p", "no:cacheprovider", *args],
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
            timeout=TIMEOUT,
            check=False,
        )
    finally:
        held.unlink(missing_ok=True)
    output = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    return proc.returncode, output


def control_pytest(tmp_path: Path, args: list[str]) -> tuple[int, str]:
    """A leaky control's child run, its collection cut at `tmp_path`.

    CS-1301: the control's only path lives under the temp root, on another
    drive from the repo the child runs in. pytest then finds no common
    ancestor, keeps the confcutdir at the repo, and walks EVERY ancestor of
    the temp path from the drive root down, listing and lstat'ing each
    sibling; one removed mid-walk by a concurrent run's temp cleanup made the
    control exit 2 under load. Not in `child_pytest`: the forced run's paths
    are in the repo, where this cut would walk the repo's drive instead.
    """
    return child_pytest(tmp_path, ["--confcutdir=%s" % tmp_path, *args])


def child_failure(code: int, output: str) -> str:
    """The child's exit and the error it raised, named by identifiers only.

    CS-1301: the error types its report printed and the frames they were
    raised in - never the report's text, where a path carries the home
    directory and an E line can carry a canary - and any canary value among
    those identifiers is redacted. An exit past 255 is a Windows status the
    child died with before it could report, so it is shown in hex too.
    Built in one expression, so no value is bound to a name of this frame
    (CS-1177).
    """
    return re.sub(
        "|".join(
            map(
                re.escape,
                chain(
                    OUTBOUND.CREDENTIAL_CANARIES.values(),
                    chain.from_iterable(
                        map(
                            operator.methodcaller("values"),
                            OUTBOUND.CREDENTIAL_BRANCH_CANARIES.values(),
                        )
                    ),
                ),
            )
        ),
        "<redacted>",
        "exit %s; raised %s; in %s"
        % (
            str(code)
            if 0 <= code <= LAST_REPORTED_EXIT
            else "%d (0x%08X)" % (code, code & 0xFFFFFFFF),
            ", ".join(
                dict.fromkeys(
                    re.findall(
                        r"^E\s+((?:\w+\.)*\w*(?:Error|Exception|Exit|Interrupt))\b",
                        output,
                        re.MULTILINE,
                    )
                )
            )
            or "nothing",
            ", ".join(dict.fromkeys(re.findall(r":\d+: in (\w+)\s*$", output, re.MULTILINE)))
            or "no frame",
        ),
    )


#: CS-1301: loaded by a control child as a `-p` plugin. It removes a SIBLING
#: of the control's directory while pytest lists that directory's parent, the
#: way a concurrent run's temp cleanup does under load.
REAPER = """
from pathlib import Path

SIBLING = Path(%r)


def pytest_collect_directory(path, parent):
    if path == SIBLING:
        path.rmdir()
"""


@pytest.mark.parametrize("flags", [[], ["--showlocals"]], ids=["plain", "showlocals"])
def test_a_reaped_sibling_leaves_the_control_red_forced_red_output(
    flags: list[str], tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Each leaky control fails on its canary even as a sibling vanishes.

    CS-1301: the control's collection never lists above its own directory,
    so a temp directory removed beside it cannot turn its exit 1 into 2. The
    name carries `forced_red_output`, so a forced child never recurses here.
    """
    sibling = tmp_path_factory.mktemp("cs1301_sibling")
    assert sibling.parent == tmp_path.parent, "the sibling is not beside the control"
    (tmp_path / "cs1301_reaper.py").write_text(REAPER % str(sibling), encoding="ascii")
    leaky = tmp_path / "cs1175_leaky_check.py"
    leaky.write_text(LEAKY % str(OUTBOUND_PATH), encoding="ascii")

    failure = child_failure(*control_pytest(tmp_path, [*flags, "-p", "cs1301_reaper", str(leaky)]))
    assert failure.startswith("exit 1;"), "the leaky control did not fail: " + failure
    assert sibling.is_dir(), "the control's collection listed above its own directory"


def test_showlocals_forced_red_output_renders_no_canary(tmp_path: Path) -> None:
    """Every canary arm forced red under `--showlocals` prints no canary value.

    Two controls run first in the same test: the leaky arm renders NOTHING
    without the flag and a canary WITH it, so a count of zero from the real
    arms is a measurement of the flag, not a capture that cannot see.
    """
    (tmp_path / "cs1175_forcer.py").write_text(FORCER % str(REPO_ROOT), encoding="ascii")
    leaky = tmp_path / "cs1175_leaky_check.py"
    leaky.write_text(LEAKY % str(OUTBOUND_PATH), encoding="ascii")

    code, output = control_pytest(tmp_path, [str(leaky)])
    plain = canaries_in(output)
    assert code == 1, "the leaky control did not fail: " + child_failure(code, output)
    assert plain == 0, "the control renders a canary even without --showlocals"

    code, output = control_pytest(tmp_path, ["--showlocals", str(leaky)])
    shown = canaries_in(output)
    assert code == 1, "the leaky control did not fail under --showlocals: " + child_failure(
        code, output
    )
    assert shown > 0, "the capture cannot see a canary rendered by --showlocals"

    args = ["--showlocals", "-p", "cs1175_forcer", "-k", "not forced_red_output"]
    code, output = child_pytest(tmp_path, [*args, *CANARY_SUITES])
    failed = re.search(r"(\d+) failed", output)
    failures = int(failed.group(1)) if failed else 0
    leaked = canaries_in(output)
    shows_locals = len(re.findall(r"tmp_path\s+= ", output))
    rederived = sum(
        1
        for line in output.splitlines()
        if any("::" + arm + " " in line for arm in DERIVATION_ARMS)
        and re.search(r" (PASSED|FAILED|ERROR)\b", line)
    )
    assert code == 1, "the forced run did not fail: " + child_failure(code, output)
    assert failures >= len(GATE.SECRET_PATTERNS), "too few arms went red: %d" % failures
    assert shows_locals > 0, "the forced run rendered no locals at all"
    assert leaked == 0, "the forced-red output rendered %d canary value(s)" % leaked
    assert rederived == 0, "%d derivation-only arm(s) ran in the child" % rederived
