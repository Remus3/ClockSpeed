"""CS-990 - grade every action pin in every tracked workflow by its RUNTIME.

WHY THIS EXISTS. GitHub retires the Node runtime an action major ships on. When it
does, the runner does NOT fail the job - it force-runs the deprecated action on the
current Node and prints a warning. So a repository pinned to a retired runtime keeps
going green, and the upgrade is applied by GitHub rather than by the project, until
the fallback is withdrawn on a day the project did not choose.

WHAT IS DERIVED AND WHAT IS OBSERVED, because the two are not the same claim. The
POPULATION of pins graded is DERIVED from the workflow files - twice, by two
enumerations that share no constant - so a pin added to a workflow cannot escape the
grade by not being on a list. The RUNTIME each major ships is OBSERVED, because no
test on this project reaches the network.

THE RECORD IS PER MAJOR AND NOT A THRESHOLD, AND THAT IS THE WHOLE POINT OF ITS
SHAPE. The first cut of this module held one integer per action - the lowest major
whose runtime was current - and a verifier refuted it the day it was written: the
integer for `actions/upload-artifact` was one too low, because that action's v5 is
still Node 20 while every sibling's same-numbered bump was not. A threshold is a
CONCLUSION, and a wrong conclusion is indistinguishable from a clean tree. An
observation can be re-taken. Every entry below is what that major's own `action.yml`
declares under `runs.using`, re-measurable with:

    curl -sS https://raw.githubusercontent.com/<owner>/<repo>/<major>/action.yml

A PINNED MAJOR WITH NO OBSERVATION IS A LOUD OFFENCE, never a silent pass, and so is
an action the record does not name at all and a ref carrying no major version. A
record that waves through what it has not measured fails in the permissive direction
and would forgive a real deprecation forever with nothing red.

NEVER GRADE THIS BY A FLOOR OVER THE PIN COUNT. A population-summed threshold is met
by its strongest member - the CS-988 shape, forbidden on CS-990's item line by name.
The two enumerations are compared as MULTISETS, which a floor is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

WORKFLOW_DIRECTORY = ".github/workflows"

# The runtimes GitHub still supports. Every other value below is deprecated.
SUPPORTED_RUNTIMES = frozenset({"node24"})

# `runs.using` as each major's own action.yml declares it. MEASURED 2026-09-17.
# Add a row by probing the tag, never by pattern-matching a sibling action's
# numbering - that assumption is exactly what the first cut of this module got wrong.
OBSERVED_RUNTIMES: dict[str, dict[int, str]] = {
    "actions/checkout": {3: "node16", 4: "node20", 5: "node24", 6: "node24"},
    "actions/setup-python": {3: "node16", 4: "node16", 5: "node20", 6: "node24"},
    "actions/setup-node": {3: "node16", 4: "node20", 5: "node24", 6: "node24"},
    "actions/upload-artifact": {4: "node20", 5: "node20", 6: "node24", 7: "node24"},
}


@dataclass(frozen=True)
class Pin:
    """One action reference as it stands in one workflow file."""

    workflow: str
    action: str
    ref: str

    @property
    def spelling(self) -> str:
        """The pin as it is written in the file, for a message a reader can grep."""
        return f"{self.action}@{self.ref}"


def pins_by_parse(text: str) -> list[str]:
    """ENUMERATION ONE - what the YAML PARSER resolves.

    Walks every mapping the document contains and collects the step-reference key's
    value wherever it appears, at any depth, so a nested or composite shape cannot
    hide a pin from the grade. Returns raw references and builds nothing, so it
    shares not one callee with enumeration two.
    """
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "uses" and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(yaml.safe_load(text))
    return found


SLUG_LINE = re.compile(
    r"^[^\S\n]*-?[^\S\n]*[A-Za-z_][A-Za-z0-9_-]*:[^\S\n]*"
    r"([A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*@[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"[^\S\n]*$",
    re.MULTILINE,
)


def pins_by_scan(text: str) -> list[str]:
    """ENUMERATION TWO - what the raw TEXT shows, by SHAPE alone.

    This function names no key, reads no constant enumeration one reads, and calls
    nothing enumeration one calls. It recognises a reference by the owner/repo@ref
    shape sitting alone on the right of a mapping key, so it cannot inherit the
    parser's blind spot. A reference the parser resolves that this scan cannot see -
    or the reverse - is a disagreement the arms report rather than average away.
    """
    return list(SLUG_LINE.findall(text))


def to_pin(workflow: str, reference: str) -> Pin | None:
    """Split one raw reference into a Pin. Outside BOTH enumerations, on purpose."""
    if "@" not in reference:
        return None
    action, _, ref = reference.partition("@")
    return Pin(workflow=workflow, action=action, ref=ref)


def workflow_files(root: Path) -> list[Path]:
    """Every tracked workflow, taken from the DIRECTORY rather than from a list."""
    directory = root / WORKFLOW_DIRECTORY
    return sorted(
        path for path in directory.glob("*") if path.is_file() and path.suffix in {".yml", ".yaml"}
    )


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def derive_pins(root: Path) -> list[Pin]:
    """The graded population, taken from enumeration one over every tracked workflow."""
    return [
        pin
        for path in workflow_files(root)
        for reference in pins_by_parse(path.read_text(encoding="utf-8"))
        if (pin := to_pin(_relative(root, path), reference)) is not None
    ]


def derive_pins_independently(root: Path) -> list[Pin]:
    """The same population, taken from enumeration two. Compared, never merged."""
    return [
        pin
        for path in workflow_files(root)
        for reference in pins_by_scan(path.read_text(encoding="utf-8"))
        if (pin := to_pin(_relative(root, path), reference)) is not None
    ]


_MAJOR = re.compile(r"^v([0-9]+)(?:\.[0-9]+)*$")


def grade_pin(pin: Pin) -> str | None:
    """The offence this pin carries, or None when its runtime is still supported."""
    observed = OBSERVED_RUNTIMES.get(pin.action)
    if observed is None:
        return (
            f"{pin.workflow} pins {pin.spelling}, an action "
            "tools/action_runtimes.py OBSERVED_RUNTIMES does not name, so its runtime "
            "is ungraded. Probe that major's action.yml and add what it declares."
        )
    match = _MAJOR.match(pin.ref)
    if match is None:
        return (
            f"{pin.workflow} pins {pin.spelling}, whose ref carries no major version, "
            "so no runtime can be read off it."
        )
    runtime = observed.get(int(match.group(1)))
    if runtime is None:
        return (
            f"{pin.workflow} pins {pin.spelling}, a major "
            "tools/action_runtimes.py OBSERVED_RUNTIMES carries no reading for, so its "
            "runtime is ungraded. Probe that major's action.yml and add what it says."
        )
    if runtime not in SUPPORTED_RUNTIMES:
        current = sorted(major for major, using in observed.items() if using in SUPPORTED_RUNTIMES)
        return (
            f"{pin.workflow} pins {pin.spelling}, which runs on {runtime}, a runtime "
            f"GitHub has deprecated. {pin.action} majors on a supported runtime: "
            f"{current or 'none recorded'}."
        )
    return None


def offences(root: Path) -> list[str]:
    """Every pin whose runtime is deprecated, ungradable or unobserved."""
    return [offence for pin in derive_pins(root) if (offence := grade_pin(pin)) is not None]
