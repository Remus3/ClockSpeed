#!/usr/bin/env python3
"""CS-1185 - every dependency has a licence verdict, and the set is DERIVED.

WHAT THIS CHECKS. ``THIRD_PARTY.md``'s dependency verdicts section records one
row per dependency, each carrying the version read, the licence read from the
installed files and from the manifest, the copyright LINE read
(``CONVENTIONS.md`` section 14 trap 3) and a verdict. This tool derives the
dependency set from the manifests and compares the two in both directions:

- A dependency with no row is a finding.
- A row naming no dependency is a finding.
- A row whose verdict does not begin ``**CLEARED``, whose copyright cell names
  neither a ``Copyright`` / ``(c)`` line nor an explicit ``NONE`` record, or
  whose date is not ``YYYY-MM-DD`` is a finding.

THE TWO DERIVATIONS, AND WHICH ONE DEPENDS ON THE MACHINE.

- NODE is read from ``shell/package-lock.json``, which is tracked, so the set is
  the same on every machine. Every entry under a ``node_modules/`` key is a
  member, nested ones included, named by the text after its LAST
  ``node_modules/``. The version a row records must equal the lockfile's, and a
  dependency ``shell/package.json`` declares that the lockfile does not pin is a
  finding (a stale lockfile).
- PYTHON has no lockfile (ruling D-Z: none is added here), so the closure is
  walked through ``importlib.metadata`` in THE RUNNING ENVIRONMENT, rooted at
  ``pyproject.toml``'s ``[project].dependencies`` plus every
  ``[project.optional-dependencies]`` extra. That is environment-dependent by
  construction, and the register says so. A requirement gated on an ``extra``
  that no parent requested is not followed. Every OTHER marker is kept as the
  edge's condition: a package's "Reached when" cell is ``always`` or the
  disjunction of its incoming conditions (each conjoined with its parent's), and
  it is a member HERE only when that condition evaluates true in this
  interpreter. A row whose condition is false here is neither required nor
  stale - that is what lets a ``sys_platform == "win32"`` row pass on a Linux
  runner - but its recorded condition must still equal the derived one.
  VERSIONS are recorded for Python and NOT compared, because the dev extra is a
  range and CI resolves its own point in it.

``[build-system].requires`` is NOT part of the derived set: it is installed into
pip's isolated build environment, not into the environment the tool and the
suite run in, so its files are not on disk to read. The register states that
exclusion rather than leaving it silent.

EXIT CODES. 0 when the recorded set equals the derived set and every row is
complete; 1 on any finding; 2 when the audit could not run - an input missing
or unparseable, a register section absent, ``packaging`` not importable, a
requirement shape this tool does not model, or an applicable requirement whose
metadata is not installed so its children could not be walked. A finding
outranks an incomplete walk: what was seen to be wrong is reported as wrong.
While the walk is incomplete, a Python row it could not reach is NOT called
stale, because it may name one of the unseen children.

OUTPUT IS COUNTS AND PACKAGE NAMES, never licence text and never a filesystem
path - an installed distribution's location carries a home directory.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

EXIT_CLEAN = 0
EXIT_MISMATCH = 1
EXIT_COULD_NOT_RUN = 2

SECTION_HEADING = "## Dependency licence verdicts"
PYTHON_HEADING = "### Python dependencies"
NODE_HEADING = "### Node dependencies"

#: The condition of an edge, or of a package, that no marker gates.
ALWAYS = "always"

PYTHON_COLUMNS = 7
NODE_COLUMNS = 6
TABLE_PREAMBLE_ROWS = 2

REGISTER = "THIRD_PARTY.md"
PYPROJECT = "pyproject.toml"
PACKAGE_JSON = "shell/package.json"
LOCKFILE = "shell/package-lock.json"

#: The manifest keys whose entries ``npm install`` resolves into the lockfile.
NODE_DECLARING_KEYS = (
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
)

NODE_MODULES = "node_modules/"
BACKTICK_RE = re.compile(r"`([^`]+)`")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COPYRIGHT_RE = re.compile(r"copyright|\(c\)", re.IGNORECASE)
EXTRA_RE = re.compile(r"\bextra\b")
VERDICT_PREFIX = "**CLEARED"
NONE_PREFIX = "NONE"

#: A cycle of conditional edges mints a new, longer condition on every lap, so
#: the walk would never end. Every package the real closure reaches carries at
#: most two distinct incoming conditions; a package past this many is a cycle.
MAX_CONDITIONS_PER_PACKAGE = 32


class AuditError(Exception):
    """The audit could not run; the message says why and names no path."""


class Dist(Protocol):
    """The two attributes of an installed distribution the walk reads."""

    @property
    def version(self) -> str:
        """The installed version."""
        ...

    @property
    def requires(self) -> list[str] | None:
        """The ``Requires-Dist`` lines, or None."""
        ...


Lookup = Callable[[str], Dist | None]


def installed(name: str) -> Dist | None:
    """Return the installed distribution named ``name``, or None.

    Args:
        name: A distribution name in any spelling PEP 503 folds together.

    Returns:
        The distribution, or None when it is not installed here.
    """
    try:
        return importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def normalise(name: str) -> str:
    """Return the PEP 503 normal form of a Python distribution name.

    Args:
        name: Any spelling.

    Returns:
        The lowercase, single-hyphen form.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _conjoin(parent: str, marker: str) -> str:
    """Return the condition of an edge ``marker`` hanging from ``parent``."""
    if parent == ALWAYS:
        return marker
    if marker == ALWAYS:
        return parent
    return f"({parent}) and ({marker})"


def _disjoin(conditions: Iterable[str]) -> str:
    """Return one condition that holds when any of ``conditions`` does."""
    unique = sorted(set(conditions))
    if ALWAYS in unique:
        return ALWAYS
    if len(unique) == 1:
        return unique[0]
    return " or ".join(f"({condition})" for condition in unique)


@dataclass
class PythonDerivation:
    """The Python closure as walked in this interpreter."""

    #: Every reached name mapped to its derived condition, true here or not.
    conditions: dict[str, str] = field(default_factory=dict)
    #: The names whose condition is true in this interpreter.
    members: set[str] = field(default_factory=set)
    #: Members whose metadata is not installed, so their children were unseen.
    incomplete: list[str] = field(default_factory=list)


def _evaluate(condition: str) -> bool:
    """Return whether ``condition`` holds in this interpreter.

    Raises:
        AuditError: If ``packaging`` is absent or the condition is not a marker.
    """
    if condition == ALWAYS:
        return True
    try:
        from packaging.markers import InvalidMarker, Marker  # noqa: PLC0415
    except ImportError as exc:
        message = "the packaging distribution is not importable"
        raise AuditError(message) from exc
    try:
        return Marker(condition).evaluate({"extra": ""})
    except InvalidMarker as exc:
        message = "a condition is not a PEP 508 marker"
        raise AuditError(message) from exc


def _parse_requirement(line: str) -> tuple[str, str] | None:
    """Return ``(name, condition)`` for one requirement, or None when extra-gated.

    Raises:
        AuditError: On an unparseable line, a requested extra, or a marker mixing
            an extra with a clause that holds without it.
    """
    try:
        from packaging.requirements import (  # noqa: PLC0415
            InvalidRequirement,
            Requirement,
        )
    except ImportError as exc:
        message = "the packaging distribution is not importable"
        raise AuditError(message) from exc
    try:
        requirement = Requirement(line)
    except InvalidRequirement as exc:
        message = "a requirement line does not parse"
        raise AuditError(message) from exc
    marker = str(requirement.marker) if requirement.marker is not None else ALWAYS
    if marker != ALWAYS and EXTRA_RE.search(marker):
        if requirement.marker is not None and requirement.marker.evaluate({"extra": ""}):
            message = f"{requirement.name}: an extra-bearing marker holds with no extra"
            raise AuditError(message)
        return None
    if requirement.extras:
        message = f"{requirement.name}: requested extras are not modelled by this audit"
        raise AuditError(message)
    return normalise(requirement.name), marker


def _roots(pyproject_text: str) -> list[tuple[str, str]]:
    """Return ``(name, condition)`` for the runtime list and every extra.

    Raises:
        AuditError: If the manifest does not parse.
    """
    try:
        project = tomllib.loads(pyproject_text).get("project", {})
    except tomllib.TOMLDecodeError as exc:
        message = f"{PYPROJECT} does not parse"
        raise AuditError(message) from exc
    lines: list[str] = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        lines.extend(extra)
    parsed = (_parse_requirement(line) for line in lines)
    return [root for root in parsed if root is not None]


def derive_python(pyproject_text: str, lookup: Lookup) -> PythonDerivation:
    """Walk the runtime list and every extra of a ``pyproject.toml``.

    Args:
        pyproject_text: The manifest's text.
        lookup: Returns the installed distribution for a name, or None.

    Returns:
        The derivation.

    Raises:
        AuditError: If the manifest does not parse or the walk cannot model it.
    """
    edges: dict[str, set[str]] = {}
    pending = _roots(pyproject_text)
    derivation = PythonDerivation()
    while pending:
        name, condition = pending.pop()
        seen = edges.setdefault(name, set())
        if condition in seen:
            continue
        seen.add(condition)
        if len(seen) > MAX_CONDITIONS_PER_PACKAGE:
            message = f"{name}: the requirement walk did not converge"
            raise AuditError(message)
        derived = _disjoin(seen)
        derivation.conditions[name] = derived
        if not _evaluate(condition):
            continue
        dist = lookup(name)
        if dist is None:
            continue
        for line in dist.requires or []:
            parsed = _parse_requirement(line)
            if parsed is not None:
                child, marker = parsed
                pending.append((child, _conjoin(condition, marker)))

    for name, condition in derivation.conditions.items():
        if _evaluate(condition):
            derivation.members.add(name)
            if lookup(name) is None:
                derivation.incomplete.append(name)
    derivation.incomplete.sort()
    return derivation


@dataclass
class NodeDerivation:
    """The node packages the lockfile pins, and what the manifest left unpinned."""

    #: Every pinned name mapped to its version, or to a sorted comma list.
    versions: dict[str, str] = field(default_factory=dict)
    #: Names ``package.json`` declares that the lockfile does not pin.
    unpinned: list[str] = field(default_factory=list)


def derive_node(package_json_text: str, lock_text: str) -> NodeDerivation:
    """Read the node dependency set from the lockfile.

    Args:
        package_json_text: ``shell/package.json``'s text.
        lock_text: ``shell/package-lock.json``'s text.

    Returns:
        The derivation.

    Raises:
        AuditError: If either file is not the JSON shape expected.
    """
    try:
        manifest = json.loads(package_json_text)
        lock = json.loads(lock_text)
    except json.JSONDecodeError as exc:
        message = "a node manifest does not parse"
        raise AuditError(message) from exc
    packages = lock.get("packages") if isinstance(lock, dict) else None
    if not isinstance(packages, dict) or not isinstance(manifest, dict):
        message = f"{LOCKFILE} carries no packages map"
        raise AuditError(message)
    found: dict[str, set[str]] = {}
    for key, entry in packages.items():
        if NODE_MODULES not in key:
            continue
        name = key.rsplit(NODE_MODULES, 1)[1]
        version = entry.get("version", "") if isinstance(entry, dict) else ""
        found.setdefault(name, set()).add(str(version))
    derivation = NodeDerivation(
        versions={name: ", ".join(sorted(versions)) for name, versions in found.items()}
    )
    for key in NODE_DECLARING_KEYS:
        declared = manifest.get(key, {})
        if isinstance(declared, dict):
            derivation.unpinned.extend(
                name for name in declared if f"{NODE_MODULES}{name}" not in packages
            )
    derivation.unpinned.sort()
    return derivation


@dataclass(frozen=True)
class Row:
    """One register row, reduced to the cells the audit grades."""

    name: str
    version: str
    condition: str
    copyright_line: str
    verdict: str
    date: str


def _table(text: str, heading: str) -> list[list[str]]:
    """Return the body rows of the first table under ``heading`` in ``text``.

    Raises:
        AuditError: If the heading or its table is absent.
    """
    marker = heading + "\n"
    if marker not in text:
        message = f"{REGISTER} carries no {heading!r} heading"
        raise AuditError(message)
    rows: list[list[str]] = []
    for line in text.split(marker, 1)[1].splitlines():
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows or line.startswith("#"):
            break
    if len(rows) < TABLE_PREAMBLE_ROWS:
        message = f"the table under {heading!r} has no header"
        raise AuditError(message)
    return rows[TABLE_PREAMBLE_ROWS:]


def _backticked(cell: str) -> str:
    """Return the single backticked token of ``cell``, or the stripped cell."""
    tokens = BACKTICK_RE.findall(cell)
    return tokens[0] if len(tokens) == 1 else cell


def parse_register(text: str) -> tuple[list[Row], list[Row], list[str]]:
    """Read the two dependency tables of the register.

    Args:
        text: The register's text, newlines normalised to LF.

    Returns:
        The Python rows, the node rows, and findings about malformed rows.

    Raises:
        AuditError: If the section or either table is absent.
    """
    if SECTION_HEADING + "\n" not in text:
        message = f"{REGISTER} carries no {SECTION_HEADING!r} section"
        raise AuditError(message)
    section = text.split(SECTION_HEADING + "\n", 1)[1]
    findings: list[str] = []
    python_rows: list[Row] = []
    for cells in _table(section, PYTHON_HEADING):
        if len(cells) != PYTHON_COLUMNS:
            findings.append(f"python: a row has {len(cells)} cells, not {PYTHON_COLUMNS}")
            continue
        name, version, condition, _licence, copyright_line, verdict, date = cells
        python_rows.append(
            Row(
                normalise(_backticked(name)),
                version,
                _backticked(condition),
                copyright_line,
                verdict,
                date,
            )
        )
    node_rows: list[Row] = []
    for cells in _table(section, NODE_HEADING):
        if len(cells) != NODE_COLUMNS:
            findings.append(f"node: a row has {len(cells)} cells, not {NODE_COLUMNS}")
            continue
        name, version, _licence, copyright_line, verdict, date = cells
        node_rows.append(Row(_backticked(name), version, ALWAYS, copyright_line, verdict, date))
    return python_rows, node_rows, findings


def _row_findings(ecosystem: str, rows: list[Row]) -> list[str]:
    """Return the completeness findings of ``rows``: verdict, copyright, date, duplicates."""
    findings: list[str] = []
    seen: set[str] = set()
    for row in rows:
        label = f"{ecosystem}: `{row.name}`"
        if row.name in seen:
            findings.append(f"{label} is recorded more than once")
        seen.add(row.name)
        if not row.verdict.startswith(VERDICT_PREFIX):
            findings.append(f"{label} carries no CLEARED verdict")
        line = row.copyright_line
        if not (COPYRIGHT_RE.search(line) or line.lstrip("*").startswith(NONE_PREFIX)):
            findings.append(f"{label} records no copyright line and no NONE record")
        if not DATE_RE.match(row.date):
            findings.append(f"{label} carries no YYYY-MM-DD date")
    return findings


@dataclass
class AuditResult:
    """Everything one audit observed."""

    findings: list[str] = field(default_factory=list)
    incomplete: list[str] = field(default_factory=list)
    python_derived: int = 0
    python_recorded: int = 0
    node_derived: int = 0
    node_recorded: int = 0


def _read(root: Path, relative: str) -> str:
    """Return one input's text with newlines normalised.

    Raises:
        AuditError: If the file is missing or unreadable.
    """
    try:
        raw = (root / relative).read_bytes()
    except OSError as exc:
        message = f"{relative} could not be read"
        raise AuditError(message) from exc
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n")


def _python_findings(derivation: PythonDerivation, rows: list[Row]) -> list[str]:
    """Compare the Python rows with the derivation in both directions."""
    findings: list[str] = []
    recorded = {row.name: row for row in rows}
    findings.extend(
        f"python: `{name}` is a dependency here and has no register row"
        for name in sorted(derivation.members - recorded.keys())
    )
    for name, row in sorted(recorded.items()):
        derived = derivation.conditions.get(name)
        if derived is None:
            # An incomplete walk has unseen children, so a row it cannot reach
            # may name one of them. That is "could not run", not a finding.
            if not derivation.incomplete:
                findings.append(f"python: `{name}` has a register row and is no dependency")
        elif row.condition != derived:
            findings.append(f"python: `{name}` is reached when `{derived}`, not as recorded")
    return findings


def _node_findings(derivation: NodeDerivation, rows: list[Row]) -> list[str]:
    """Compare the node rows with the lockfile in both directions."""
    findings = [
        f"node: `{name}` is declared in {PACKAGE_JSON} and absent from {LOCKFILE}"
        for name in derivation.unpinned
    ]
    recorded = {row.name: row for row in rows}
    findings.extend(
        f"node: `{name}` is pinned by the lockfile and has no register row"
        for name in sorted(derivation.versions.keys() - recorded.keys())
    )
    for name, row in sorted(recorded.items()):
        pinned = derivation.versions.get(name)
        if pinned is None:
            findings.append(f"node: `{name}` has a register row and is no dependency")
        elif row.version != pinned:
            findings.append(f"node: `{name}` is pinned at {pinned}, not the version recorded")
    return findings


def audit(root: Path, lookup: Lookup = installed) -> AuditResult:
    """Derive both dependency sets under ``root`` and grade the register against them.

    Args:
        root: A directory laid out like the repository.
        lookup: Returns the installed distribution for a name, or None.

    Returns:
        The result.

    Raises:
        AuditError: If the audit could not run.
    """
    python = derive_python(_read(root, PYPROJECT), lookup)
    node = derive_node(_read(root, PACKAGE_JSON), _read(root, LOCKFILE))
    python_rows, node_rows, findings = parse_register(_read(root, REGISTER))
    findings.extend(_row_findings("python", python_rows))
    findings.extend(_row_findings("node", node_rows))
    findings.extend(_python_findings(python, python_rows))
    findings.extend(_node_findings(node, node_rows))
    applicable = sum(
        1
        for row in python_rows
        if python.conditions.get(row.name) is not None and _evaluate(row.condition)
    )
    return AuditResult(
        findings=findings,
        incomplete=python.incomplete,
        python_derived=len(python.members),
        python_recorded=applicable,
        node_derived=len(node.versions),
        node_recorded=len(node_rows),
    )


def exit_code(result: AuditResult) -> int:
    """Return the exit code a result earns: a finding outranks an incomplete walk.

    Args:
        result: One audit's result.

    Returns:
        0, 1 or 2.
    """
    if result.findings:
        return EXIT_MISMATCH
    if result.incomplete:
        return EXIT_COULD_NOT_RUN
    return EXIT_CLEAN


def main(argv: list[str] | None = None) -> int:
    """Run the audit and print its counts.

    Args:
        argv: Command-line arguments; ``--root`` names the tree to audit.

    Returns:
        The exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="the tree to audit (default: this repository)",
    )
    args = parser.parse_args(argv)
    try:
        result = audit(args.root)
    except AuditError as exc:
        print(f"licence_audit: could not run - {exc}")
        return EXIT_COULD_NOT_RUN
    print(
        f"licence_audit: python derived {result.python_derived}, recorded "
        f"{result.python_recorded}; node derived {result.node_derived}, recorded "
        f"{result.node_recorded}; findings {len(result.findings)}"
    )
    for finding in result.findings:
        print(f"  {finding}")
    for name in result.incomplete:
        print(f"  python: `{name}` applies here and is not installed, so its children are unseen")
    return exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
