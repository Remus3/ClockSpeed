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
import contextlib
import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable, Sequence

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
        "the commit gate's scan disagreed with this gate's attribution; "
        "refusing rather than reporting a total it cannot explain"
    ),
}

#: THE OUTBOUND GATE'S OWN EXCLUSION CHANNEL, AND WHY IT MUST NOT SHARE THE
#: COMMIT GATE'S. Measured 2026-09-08 by a read-only adversary: the commit
#: gate's `world_name_exclusions` key is consumed inside `discover_world_names`,
#: which `PiiMatchers.__init__` calls for BOTH gates. So an operator silencing
#: an outbound false positive through that key ALSO blinds
#: `tools/precommit_gate.py` - a CLAUDE.md section 6 frozen file - to that same
#: real world name, permanently, for every future commit. Demonstrated, not
#: argued: the commit gate's diagnostics on a payload carrying that name went
#: 1 to 0 while the blocklist went 25 to 17.
#:
#: That converts an over-fire from "a send a human then edits" into a certain,
#: invisible, cross-gate fail-open, which is the exact trade the commit gate's
#: own source says must never be made. So this gate reads its OWN key and
#: applies it to its OWN verdict only. The value never reaches `PiiMatchers`.
#: SUPPRESSING AN OUTBOUND FALSE POSITIVE MUST NEVER BE DONE THROUGH THE COMMIT
#: GATE'S KEY.
ENV_OUTBOUND_EXCLUSIONS = "CLOCKSPEED_OUTBOUND_EXCLUSIONS"

#: Classes whose short values are WARNED about rather than refused, and the
#: length at or below which that applies. MEASURED on 217 files: every
#: world-name finding in the corpus came from a length-4 name, and no name of
#: length 12 or more ever fired. A short discovered value is an ordinary word
#: before it is a world, and this project's own vocabulary and its world names
#: are drawn from the same semantic well - one world named `run` made 46 of 79
#: real outbound notes unsendable.
#:
#: A HIGHER FLOOR WAS THE OBVIOUS FIX AND IS THE WRONG ONE. The commit gate
#: already denied it by measurement: a floor of 5 drops 8 of the 25 real names
#: on this machine out of the COMMIT gate too. Warning keeps the value graded
#: and visible while leaving the send possible, which a dropped floor does not.
WARN_SHORT_CLASSES = frozenset({CLASS_WORLD_NAME, CLASS_ACCOUNT_NAME})
WARN_SHORT_CHARS = 5

#: The canaries the always-derivable classes are PROVEN against rather than
#: assumed. Assembled from fragments because this gate's own source is scanned
#: by the commit gate, and a spelled-out home path or credential here would
#: block the commit that adds it - the same reason the commit gate assembles
#: its own.
CANARY_WIN_HOME = "C:" + "\\" + "Users" + "\\" + "canary" + "\\" + "file.txt"
CANARY_NIX_HOME = "/" + "home" + "/canary" + "/file.txt"
CANARY_CREDENTIAL = "AKIA" + ("Q7" * 8)

TOOL = "outbound-gate"


@dataclass(frozen=True)
class Finding:
    """One hit, carrying a position and a class and never a value."""

    klass: str
    line: int
    col: int


@dataclass(frozen=True)
class Coverage:
    """One class's verdict, and the reason when it could not be derived."""

    klass: str
    measured: bool
    reason: str


class QuietParser(argparse.ArgumentParser):
    """An argument parser that never echoes what it was given.

    MEASURED 2026-09-08 by a read-only adversary: the stock parser's error path
    writes `unrecognized arguments: <argv>` to stderr and exits before any of
    this module's path-free renderers exist. The ordinary slip of passing the
    payload as an argument instead of on stdin therefore printed the whole
    ungraded payload - home path, world name and token included. The proof was
    that feeding this gate its own exit-2 stderr made it refuse to send it.

    `--help` maps to the usage code rather than 0 for a second reason from the
    same pass: 0 means CLEAN in this gate's closed set, and a help run scanned
    nothing. A caller branching on 0 would read a help text as a clean verdict.
    """

    def error(self, message: str) -> None:  # type: ignore[override]  # noqa: ARG002
        """Report a usage error without quoting the argument vector."""
        write_stream(sys.stderr, "%s: usage error; nothing was scanned\n" % TOOL)
        raise SystemExit(EXIT_USAGE)

    def exit(self, status: int = 0, message: str | None = None) -> None:  # type: ignore[override]
        """Leave through the usage code, never through CLEAN."""
        if message:
            write_stream(sys.stderr, message)
        raise SystemExit(EXIT_USAGE if status == 0 else status)


def write_stream(stream: object, payload: str) -> None:
    """Write to a stream, tolerating one that has gone away.

    MEASURED: `sys.stdout.write` sat outside this module's guard, so a run
    piped into a consumer that closes stdin exited 120 - a code outside the set
    this gate's own docstring tells a caller to branch on. A caller written as
    `if code == REFUSED: block else: send` therefore SENT a payload carrying a
    home path. The verdict must survive the reporting of it.
    """
    try:
        stream.write(payload)  # type: ignore[attr-defined]
        stream.flush()  # type: ignore[attr-defined]
    except (OSError, ValueError, AttributeError):
        _neutralise(stream)


def _neutralise(stream: object) -> None:
    """Point a broken stream at the null device so shutdown cannot re-raise.

    SWALLOWING THE WRITE IS NOT ENOUGH, and the first repair of this defect
    stopped there and did not work. Measured: a refusal piped into a consumer
    that closes the pipe still exited 120 on three of three runs, because the
    failed flush leaves the payload in the buffer and CPython flushes again
    during interpreter shutdown - after main has returned its verdict, where no
    handler of this module's can reach it. The interpreter reports that as
    `Exception ignored` and overrides the exit status with 120, a code outside
    the closed set a caller was told to branch on.

    Redirecting the underlying file descriptor at the null device discards the
    buffer's destination, so the shutdown flush succeeds against nothing and
    the verdict survives its own reporting.
    """
    try:
        fileno = stream.fileno()  # type: ignore[attr-defined]
    except (OSError, ValueError, AttributeError):
        return
    try:
        null = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        return
    try:
        with contextlib.suppress(OSError):
            os.dup2(null, fileno)
    finally:
        with contextlib.suppress(OSError):
            os.close(null)


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


def outbound_exclusions() -> frozenset[str]:
    """The values this gate alone suppresses, folded for comparison.

    Read from this gate's OWN environment key and never from the commit gate's
    configuration. See ENV_OUTBOUND_EXCLUSIONS for the measurement that forced
    the split.
    """
    raw = os.environ.get(ENV_OUTBOUND_EXCLUSIONS, "")
    return frozenset(part.strip().casefold() for part in raw.split(",") if part.strip())


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


def _matches(patterns: Iterable[re.Pattern[str]], text: str, klass: str) -> list[Finding]:
    """Every position `patterns` match in `text`, tagged with `klass`."""
    found: list[Finding] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for pattern in patterns:
            found.extend(
                Finding(klass, lineno, match.start() + 1) for match in pattern.finditer(line)
            )
    return found


def _valued_matches(
    gate: ModuleType,
    values: Sequence[str],
    text: str,
    klass: str,
    fold: bool,
) -> tuple[list[Finding], list[Finding], list[Finding], int]:
    """Scan `values` one at a time, splitting hits into refusals and warnings.

    ONE VALUE AT A TIME, through the commit gate's own `_word_res`, so the
    escaping and folding semantics are the gate's rather than a reimplementation
    of them - and so each hit is attributable to the LENGTH of the value that
    produced it. A pooled compile cannot tell a four-character world from a
    thirty-six character one, and that distinction is the whole of the warn
    tier.

    Returns (refusals, warnings, suppressed, excluded_count).

    SUPPRESSED POSITIONS ARE RETURNED RATHER THAN DISCARDED, and that is not
    bookkeeping. The oracle below treats any position it found that this gate
    did not as `unattributed` and refuses on it. A value suppressed by this
    gate's own exclusion key is still matched by `check_pii`, so discarding its
    positions made the oracle fire on exactly the value the operator had
    excluded - measured: the exclusion suppressed the class and the run still
    exited 1. The exclusion has to be visible to the reconciliation or it is
    not an exclusion at all.
    """
    excluded = outbound_exclusions()
    refusals: list[Finding] = []
    warnings: list[Finding] = []
    suppressed: list[Finding] = []
    dropped = 0
    for value in values:
        if value.casefold() in excluded:
            dropped += 1
            patterns = gate._word_res([value], fold=fold)  # noqa: SLF001
            suppressed.extend(_matches(patterns, text, klass))
            continue
        # SLF001: the commit gate's own compiler is used deliberately. Its
        # escaping and word-boundary semantics are the contract being
        # matched against, and reimplementing them here would be a second
        # copy free to drift from the one that grades commits.
        patterns = gate._word_res([value], fold=fold)  # noqa: SLF001
        hits = _matches(patterns, text, klass)
        if klass in WARN_SHORT_CLASSES and len(value) <= WARN_SHORT_CHARS:
            warnings.extend(hits)
        else:
            refusals.extend(hits)
    return refusals, warnings, suppressed, dropped


def _canary_measured(patterns: Iterable[re.Pattern[str]], canaries: Sequence[str]) -> bool:
    """Whether these rules still match values built to be matched.

    DERIVED RATHER THAN ASSERTED, and the difference is the item's own subject.
    The first draft carried a hardcoded set of always-measurable classes, so the
    two rows that need no machine state said MEASURED without consulting
    anything - meaning a silently weakened home-path rule would leave the
    coverage block reassuring while nothing was caught. That is the shape of the
    defect this gate exists to repair, reproduced inside it. A canary makes the
    row a measurement.
    """
    return all(any(pattern.search(canary) for pattern in patterns) for canary in canaries)


def scan(text: str) -> tuple[list[Finding], list[Finding], list[Coverage]]:
    """Grade `text`. Returns (refusals, warnings, coverage rows).

    The coverage rows are built from the SAME `PiiMatchers` construction whose
    values do the scanning, so a class cannot be reported measured by one half
    and go unscanned by the other - which is precisely the split that made the
    commit gate's stdin mode reassuring and empty.
    """
    gate = load_precommit_gate()
    report = gate.Report()
    matchers = gate.PiiMatchers(report)
    skipped = list(report.skipped)

    home_res = [gate.PII_WIN_HOME_RE, gate.PII_NIX_HOME_RE]
    refusals = _matches(home_res, text, CLASS_HOME_PATH)
    warnings: list[Finding] = []
    suppressed: list[Finding] = []
    dropped: dict[str, int] = {}

    valued = (
        (CLASS_ACCOUNT_NAME, matchers.account_names, True),
        (CLASS_ACCOUNT_ID, matchers.account_ids, False),
        (CLASS_WORLD_NAME, matchers.world_names, True),
        (CLASS_WORLD_TOKEN, matchers.world_tokens, False),
    )
    for klass, values, fold in valued:
        hits, warned, quiet, count = _valued_matches(gate, values, text, klass, fold)
        refusals.extend(hits)
        warnings.extend(warned)
        suppressed.extend(quiet)
        dropped[klass] = count

    secret_report = gate.Report()
    gate.check_secrets("outbound", text, secret_report)
    refusals.extend(
        Finding(CLASS_CREDENTIAL, diag.line, diag.col) for diag in secret_report.diagnostics
    )

    # THE INDEPENDENT ORACLE, COMPARED AS A SET AND NOT AS A COUNT. `check_pii`
    # answers the same question through its own code path. The first draft
    # compared LENGTHS, and an adjudicator demonstrated two equal-length
    # disagreements cancelling: the oracle finding a hit at one column while
    # this module reported another. Sets cannot cancel that way. Anything the
    # oracle saw that this module did not becomes an `unattributed` refusal, so
    # a rule this gate fails to attribute cannot become one it fails to enforce.
    #
    # WHAT THIS ORACLE CANNOT DO, stated rather than implied: it shares its
    # matchers and its rule table with the thing it checks, so its ceiling is
    # `check_pii` itself. A class the commit gate never learned to detect yields
    # nothing from both halves. That residual is not closeable from this module.
    oracle = gate.Report()
    gate.check_pii("outbound", text, matchers, oracle)
    seen = {(finding.line, finding.col) for finding in refusals + warnings + suppressed}
    unattributed = {
        (diag.line, diag.col) for diag in oracle.diagnostics if (diag.line, diag.col) not in seen
    }
    refusals.extend(Finding(CLASS_UNATTRIBUTED, line, col) for line, col in sorted(unattributed))

    populations = {
        CLASS_ACCOUNT_NAME: (matchers.account_names, gate.PII_ACCOUNT_NAME_LABEL, "account name"),
        CLASS_ACCOUNT_ID: (matchers.account_ids, gate.PII_ACCOUNT_ID_LABEL, "account"),
        CLASS_WORLD_NAME: (matchers.world_names, gate.PII_WORLD_LABEL, "world name"),
        CLASS_WORLD_TOKEN: (matchers.world_tokens, gate.PII_WORLD_LABEL, "world token"),
    }
    coverage: list[Coverage] = []
    for klass in CLASS_ORDER:
        if klass == CLASS_HOME_PATH:
            live = _canary_measured(home_res, (CANARY_WIN_HOME, CANARY_NIX_HOME))
            coverage.append(
                Coverage(klass, live, "canary matched" if live else "the rules failed their canary")
            )
            continue
        if klass == CLASS_CREDENTIAL:
            probe = gate.Report()
            gate.check_secrets("canary", CANARY_CREDENTIAL, probe)
            live = bool(probe.diagnostics)
            coverage.append(
                Coverage(klass, live, "canary matched" if live else "the rules failed their canary")
            )
            continue
        values, label, hint = populations[klass]
        if values:
            count = dropped.get(klass, 0)
            detail = "%d spelling(s) discovered" % len(values)
            if count:
                detail += ", %d suppressed by %s" % (count, ENV_OUTBOUND_EXCLUSIONS)
            coverage.append(Coverage(klass, True, detail))
        else:
            coverage.append(Coverage(klass, False, _skip_reason(skipped, label, hint)))
    return refusals, warnings, coverage


def _ascii(value: str) -> str:
    """Force a rendered line to 7-bit ASCII.

    CLAUDE.md non-negotiable 4 applies to this gate's own output, which gets
    pasted into replies and into `.ps1` files alike - and a UTF-8 dash in a
    double-quoted PowerShell 5.1 string terminates it at the tokenizer. The
    reasons flow through here from another module, so this is enforced at the
    boundary rather than assumed of the source.
    """
    return value.encode("ascii", "replace").decode("ascii")


def render(
    refusals: Sequence[Finding],
    warnings: Sequence[Finding],
    coverage: Sequence[Coverage],
) -> tuple[str, str]:
    """Return the (stdout, stderr) text for one run.

    The coverage block prints on EVERY run including a clean one, because its
    job is to say what was NOT looked at, and a run with nothing to report is
    exactly when that is easiest to forget.
    """
    out = [TOOL + ": coverage"]
    for row in coverage:
        verdict_word = "MEASURED  " if row.measured else "UNMEASURED"
        out.append("  %-14s %s  %s" % (row.klass, verdict_word, _ascii(row.reason)))
    out.extend(
        "  WARN  <pii:%s>  line %d col %d  a short discovered value; not refused"
        % (warning.klass, warning.line, warning.col)
        for warning in sorted(warnings, key=lambda f: (f.line, f.col, f.klass))
    )

    err: list[str] = []
    if refusals:
        err.append(TOOL + ": REFUSED")
        err.extend(
            "  <pii:%s>  line %d col %d  %s"
            % (finding.klass, finding.line, finding.col, _ascii(CLASS_REASONS[finding.klass]))
            for finding in sorted(refusals, key=lambda f: (f.line, f.col, f.klass))
        )
        err.append("%s: REFUSED - %d finding(s). Nothing was sent." % (TOOL, len(refusals)))
    return "\n".join(out) + "\n", ("\n".join(err) + "\n" if err else "")


def verdict(refusals: Sequence[Finding], coverage: Sequence[Coverage]) -> int:
    """The exit code: a finding dominates, then an unmeasured class, then clean.

    A WARNING NEVER CHANGES THE CODE. That is the point of the tier: the value
    is named and its position printed, and the send remains possible, because a
    gate that refuses routine prose is a gate that gets routed around - and a
    routed-around gate restores exactly the hazard it was built to close.
    """
    if refusals:
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


def _refuse_ungraded(detail: str) -> int:
    """Report a payload this gate could not grade, without echoing a path."""
    write_stream(
        sys.stderr,
        "%s: REFUSED\n  <gate:error>  %s\n%s: REFUSED - the payload was not graded. "
        "Nothing was sent.\n" % (TOOL, _ascii(detail), TOOL),
    )
    return EXIT_REFUSED


def main(argv: Sequence[str] | None = None) -> int:
    """Grade one payload and report. Writes nothing, reaches no network."""
    parser = QuietParser(
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
        refusals, warnings, coverage = scan(text)
        out, err = render(refusals, warnings, coverage)
        code = verdict(refusals, coverage)
    except BaseException as exc:
        # FAIL CLOSED, AND CATCH BaseException RATHER THAN Exception. Every
        # failure here leaves the payload ungraded, and an ungraded payload must
        # never read as a safe one. BaseException because a `SystemExit` raised
        # inside the loaded commit gate would otherwise escape and print an
        # interpreter traceback - and a traceback renders this file's absolute
        # path per frame, which is personal data wherever the tool runs from a
        # home-rooted checkout or worktree. That is the deployment this gate was
        # written for, so the guard has to cover it.
        if isinstance(exc, KeyboardInterrupt):
            raise
        try:
            detail = load_precommit_gate().safe_exc_text(exc)
        except BaseException:  # the renderer is best-effort
            detail = type(exc).__name__
        return _refuse_ungraded(detail)

    # The writes are INSIDE the guarded region by construction: write_stream
    # swallows a stream that has gone away, so a broken pipe cannot turn a
    # refusal into an exit code outside the closed set.
    write_stream(sys.stdout, out)
    if err:
        write_stream(sys.stderr, err)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(EXIT_REFUSED) from None
