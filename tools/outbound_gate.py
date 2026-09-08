#!/usr/bin/env python3
"""CS-957 - grade outbound text before it leaves this machine.

WHY THIS EXISTS. A sibling project's auto-responder proposal admits four
actions a responder may take with no operator in the loop, and the first of
them is class A1: "read-only measurement in own tree, REPORTED BACK". The
reporting half is an exfiltration path. A measurement that writes nothing can
still carry a home path, this machine's account name, a platform account id or
a world name out in the reply, which breaks CLAUDE.md non-negotiable 3 without
touching a byte on disk. This gate is what reads a payload before it is sent.

THE DEFECT IT MUST NOT REPRODUCE, MEASURED on this tree 2026-09-08 rather than
predicted. `tools/precommit_gate.py --text-stdin` fed a payload carrying an
absolute Windows home path exits 0 with a pass line, while `check_pii` on those
identical bytes yields a `PII` diagnostic on line 1. The cause is structural:
`mode_text_stdin` calls the charset and secret checks and never `check_pii`,
while `main` builds `PiiMatchers` before dispatch - so the run performs the
discovery whose skip lines LOOK like a measured personal-data verdict, and then
scans for none of it. A gate that prints a coverage block and scans nothing is
worse than one that prints neither, because it manufactures the confidence.
`tests/test_outbound_gate.py::test_coverage_lines_are_not_a_pii_verdict` is the
arm that makes that shape impossible here: it requires the coverage rows and
the catch in ONE invocation, because the defect satisfies each separately.

IT REFUSES, IT DOES NOT REWRITE, and the direction is the whole design. This
project already ships both idioms and they answer different questions.
`locate.redact` REWRITES because its output is a message being printed anyway,
so a miss costs a line of a log. `check_pii` REFUSES because its subject is
bytes about to become permanent, and a miss costs a leak that cannot be
recalled. Outbound bytes are the second case and worse: they are in another
repository before anyone re-reads them. So a silent redactor that misses leaks
a value, while a refuser that over-fires blocks a send a human then edits. Only
one of those two failures is recoverable.

WHY THE VERDICT IS PER CLASS AND NEVER POOLED. Two of the six classes need no
machine state and are always measurable; the three save-derived ones are
underivable on any box with no game installed, which includes CI. A single
MEASURED flag over that population either reports the whole run unmeasured
everywhere - so it gets ignored - or reports it measured because one strong
member was, which is a threshold met by the population's best member while its
weakest goes ungraded. Each class carries its own verdict and the exit code is
driven by the worst row.

VACUITY IS AN OUTCOME, NEVER A CLEAN RESULT. A class this machine cannot derive
is reported UNMEASURED with the discovery channel's own reason. CLEAN is
therefore unreachable where there is no save root - by construction rather than
by anyone remembering to check - which is what stops a bare CI box reporting
that it verified four classes it never looked at.

ATTRIBUTION IS BY MATCHER, NOT BY REASON STRING. `check_pii` reports every
class under one code, so telling them apart afterwards would mean parsing its
prose - and prose is not an interface. This module instead scans with the
individual compiled matchers `PiiMatchers` already built, which yields the
class directly. `check_pii` is then run as an INDEPENDENT ORACLE over the same
bytes and its finding count must not exceed this module's; any excess becomes
an `unattributed` finding that still refuses. So a rule this module fails to
attribute cannot become a rule it fails to enforce.

IT EDITS NOTHING AND IMPORTS FROM A FROZEN FILE. `tools/precommit_gate.py` is
on the CLAUDE.md section 6 frozen list and is not touched: this module loads it
by path and reuses its matchers, its discovery and its secret patterns. No
frozen-file grant is required or sought.

THE OUTPUT DELIBERATELY AVOIDS THE COMMIT GATE'S VOCABULARY. That gate's
"PASS - n checked, n skipped, 0 blocking" means SAFE TO COMMIT. This one
answers SAFE TO SEND, and a reader who pattern-matched the familiar sentence
would read one verdict as the other.

Exit codes, a closed set a caller can branch on:

    0  CLEAN       every class measured, nothing found
    1  REFUSED     something was found, OR this gate itself raised
    2  usage       argparse only; nothing was scanned
    3  UNMEASURED  nothing found, but a class could not be derived here

A finding DOMINATES an unmeasured class - 1, never 3 - because a caller that
treats 3 as advisory would otherwise send a payload carrying a home path.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
PRECOMMIT_GATE = REPO_ROOT / "tools" / "precommit_gate.py"

EXIT_CLEAN = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_UNMEASURED = 3

#: The class names, in report order. These strings are the interface: the
#: refusal lines and the coverage rows both key on them, and
#: tests/test_outbound_gate.py asserts each one by name.
CLASS_HOME_PATH = "home-path"
CLASS_ACCOUNT_NAME = "account-name"
CLASS_ACCOUNT_ID = "account-id"
CLASS_WORLD_NAME = "world-name"
CLASS_WORLD_TOKEN = "world-token"  # noqa: S105 - a class label, not a credential
CLASS_CREDENTIAL = "credential"
CLASS_UNATTRIBUTED = "unattributed"

CLASS_ORDER = (
    CLASS_HOME_PATH,
    CLASS_ACCOUNT_NAME,
    CLASS_ACCOUNT_ID,
    CLASS_WORLD_NAME,
    CLASS_WORLD_TOKEN,
    CLASS_CREDENTIAL,
)

#: Fixed per-class reasons, authored here and never built from the match. A
#: reason that quoted what it found would be the same leak in a different
#: costume (CLAUDE.md non-negotiable 12), so the class and the line:column say
#: where to look and nothing says what was there.
CLASS_REASONS = {
    CLASS_HOME_PATH: "an absolute home path; auto-detect it at runtime instead",
    CLASS_ACCOUNT_NAME: "this machine's account name appears as a whole word",
    CLASS_ACCOUNT_ID: "a platform account id discovered under the save root",
    CLASS_WORLD_NAME: "a world name discovered on this machine appears",
    CLASS_WORLD_TOKEN: "a world token for this machine appears",
    CLASS_CREDENTIAL: "a credential shape",
    CLASS_UNATTRIBUTED: (
        "the commit gate's scan found more than this gate attributed; "
        "refusing rather than guessing which class it was"
    ),
}

#: Classes derivable with no machine state at all. These two are the reason a
#: bare CI box still grades something rather than reporting a uniform silence.
ALWAYS_MEASURABLE = frozenset({CLASS_HOME_PATH, CLASS_CREDENTIAL})

#: What each class's coverage row says when it IS measured. A count of derived
#: spellings is safe to print; a spelling is not, and none is ever printed.
MEASURED_BY_RULE = "anchored shape rules, no machine state required"

TOOL = "outbound-gate"


@dataclass(frozen=True)
class Finding:
    """One refusal, carrying a position and a class and never a value."""

    klass: str
    line: int
    col: int


@dataclass(frozen=True)
class Coverage:
    """One class's verdict, and the reason when it could not be derived."""

    klass: str
    measured: bool
    reason: str


def load_precommit_gate() -> ModuleType:
    """Load the frozen commit gate by path, without importing the package.

    By path rather than `import tools.precommit_gate` because `tools/` is a
    namespace package with no `__init__.py`, so the import form depends on the
    caller's `sys.path` - and an A1 responder's invocation path is not this
    project's to assume.
    """
    name = "clockspeed_precommit_gate_for_outbound_gate"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, PRECOMMIT_GATE)
    if spec is None or spec.loader is None:
        message = "cannot load the commit gate from " + PRECOMMIT_GATE.name
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE exec_module: the gate declares dataclasses under
    # `from __future__ import annotations`, and @dataclass resolves those
    # string annotations through sys.modules[cls.__module__].
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _skip_reason(skipped: Sequence[tuple[str, str]], label: str, hint: str) -> str:
    """The discovery channel's own words for why a class was not derived.

    `hint` disambiguates the two classes that share one skip label: world names
    and world tokens are both reported under `<pii:world>`, so the row for each
    prefers a skip that names it. Falling back to the first skip under the
    label is deliberate - a reason slightly less specific than it could be
    still beats this module inventing prose about a measurement it did not
    take.
    """
    under_label = [why for used, why in skipped if used == label]
    for why in under_label:
        if hint in why.lower():
            return why
    if under_label:
        return under_label[0]
    return "no value of this class is discoverable on this machine"


def _matches(patterns: Sequence[re.Pattern[str]], text: str, klass: str) -> list[Finding]:
    """Every position `patterns` match in `text`, tagged with `klass`."""
    found: list[Finding] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for pattern in patterns:
            found.extend(
                Finding(klass, lineno, match.start() + 1) for match in pattern.finditer(line)
            )
    return found


def scan(text: str) -> tuple[list[Finding], list[Coverage]]:
    """Grade `text`, returning its findings and one coverage row per class.

    The coverage rows are built from the SAME `PiiMatchers` construction whose
    matchers do the scanning, so a class cannot be reported measured by one
    half and go unscanned by the other - which is precisely the split that made
    the commit gate's stdin mode reassuring and empty.
    """
    gate = load_precommit_gate()
    report = gate.Report()
    matchers = gate.PiiMatchers(report)
    skipped = list(report.skipped)

    findings: list[Finding] = []
    findings.extend(_matches([gate.PII_WIN_HOME_RE], text, CLASS_HOME_PATH))
    findings.extend(_matches([gate.PII_NIX_HOME_RE], text, CLASS_HOME_PATH))
    findings.extend(_matches(matchers.name_res, text, CLASS_ACCOUNT_NAME))
    findings.extend(_matches(matchers.id_res, text, CLASS_ACCOUNT_ID))
    findings.extend(_matches(matchers.world_name_res, text, CLASS_WORLD_NAME))
    findings.extend(_matches(matchers.world_token_res, text, CLASS_WORLD_TOKEN))

    secret_report = gate.Report()
    gate.check_secrets("outbound", text, secret_report)
    findings.extend(
        Finding(CLASS_CREDENTIAL, diag.line, diag.col) for diag in secret_report.diagnostics
    )

    # THE INDEPENDENT ORACLE. check_pii answers the same question through its
    # own code path; if it finds more than this module attributed, the excess
    # is a rule this module does not know about and the run refuses on it
    # rather than reporting a total it cannot explain.
    oracle = gate.Report()
    gate.check_pii("outbound", text, matchers, oracle)
    attributed = sum(1 for finding in findings if finding.klass != CLASS_CREDENTIAL)
    unattributed = max(0, len(oracle.diagnostics) - attributed)
    findings.extend(Finding(CLASS_UNATTRIBUTED, 0, 0) for _ in range(unattributed))

    populations = {
        CLASS_ACCOUNT_NAME: (matchers.account_names, gate.PII_ACCOUNT_NAME_LABEL, "account name"),
        CLASS_ACCOUNT_ID: (matchers.account_ids, gate.PII_ACCOUNT_ID_LABEL, "account"),
        CLASS_WORLD_NAME: (matchers.world_names, gate.PII_WORLD_LABEL, "world name"),
        CLASS_WORLD_TOKEN: (matchers.world_tokens, gate.PII_WORLD_LABEL, "world token"),
    }
    coverage: list[Coverage] = []
    for klass in CLASS_ORDER:
        if klass in ALWAYS_MEASURABLE:
            coverage.append(Coverage(klass, True, MEASURED_BY_RULE))
            continue
        values, label, hint = populations[klass]
        if values:
            coverage.append(Coverage(klass, True, "%d spelling(s) discovered" % len(values)))
        else:
            coverage.append(Coverage(klass, False, _skip_reason(skipped, label, hint)))
    return findings, coverage


def _ascii(value: str) -> str:
    """Force a rendered line to 7-bit ASCII.

    CLAUDE.md non-negotiable 4 applies to this gate's own output, which gets
    pasted into replies and into `.ps1` files alike - and a UTF-8 dash in a
    double-quoted PowerShell 5.1 string terminates it at the tokenizer. The
    reasons flow through here from another module, so this is enforced at the
    boundary rather than assumed of the source.
    """
    return value.encode("ascii", "replace").decode("ascii")


def render(findings: Sequence[Finding], coverage: Sequence[Coverage]) -> tuple[str, str]:
    """Return the (stdout, stderr) text for one run.

    The coverage block prints on EVERY run including a clean one, because its
    job is to say what was NOT looked at, and a run with nothing to report is
    exactly when that is easiest to forget.
    """
    out = [TOOL + ": coverage"]
    for row in coverage:
        verdict = "MEASURED  " if row.measured else "UNMEASURED"
        out.append("  %-14s %s  %s" % (row.klass, verdict, _ascii(row.reason)))

    err: list[str] = []
    if findings:
        err.append(TOOL + ": REFUSED")
        err.extend(
            "  <pii:%s>  line %d col %d  %s"
            % (finding.klass, finding.line, finding.col, _ascii(CLASS_REASONS[finding.klass]))
            for finding in sorted(findings, key=lambda f: (f.line, f.col, f.klass))
        )
        err.append("%s: REFUSED - %d finding(s). Nothing was sent." % (TOOL, len(findings)))
    return "\n".join(out) + "\n", ("\n".join(err) + "\n" if err else "")


def verdict(findings: Sequence[Finding], coverage: Sequence[Coverage]) -> int:
    """The exit code: a finding dominates, then an unmeasured class, then clean."""
    if findings:
        return EXIT_REFUSED
    if any(not row.measured for row in coverage):
        return EXIT_UNMEASURED
    return EXIT_CLEAN


def read_payload(path: str | None) -> str:
    """Read the payload, refusing anything that is not valid UTF-8.

    A payload that cannot be decoded cannot be scanned, and a class that was
    not scanned on bytes that were nonetheless SENT is a leak this gate
    declined to look at. So an undecodable payload is a refusal and never a
    pass - `errors="replace"` here would launder exactly the bytes a scan
    needs to see.
    """
    data = Path(path).read_bytes() if path is not None else sys.stdin.buffer.read()
    return data.decode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Grade one payload and report. Writes nothing, reaches no network."""
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description="Grade outbound text for personal data and credentials before it is sent.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="read the payload from this path instead of standard input",
    )
    args = parser.parse_args(argv)

    try:
        text = read_payload(args.file)
        findings, coverage = scan(text)
    except Exception as exc:  # fail closed, see below
        # FAIL CLOSED. Every failure here - an undecodable payload, an
        # unreadable file, a matcher that raised - leaves the payload ungraded,
        # and an ungraded payload must never read as a safe one. The exception
        # is rendered through the commit gate's own path-free helper where that
        # is loadable, because an OSError's str() carries the filename it
        # failed on and that filename can be personal data.
        try:
            detail = load_precommit_gate().safe_exc_text(exc)
        except Exception:  # the renderer is best-effort
            detail = type(exc).__name__
        sys.stderr.write(
            "%s: REFUSED\n  <gate:error>  %s\n%s: REFUSED - the payload was not graded. "
            "Nothing was sent.\n" % (TOOL, _ascii(detail), TOOL)
        )
        return EXIT_REFUSED

    out, err = render(findings, coverage)
    sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return verdict(findings, coverage)


if __name__ == "__main__":
    raise SystemExit(main())
