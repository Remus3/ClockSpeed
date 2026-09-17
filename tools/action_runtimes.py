"""CS-990 - grade every action pin in every tracked workflow by its RUNTIME.

WHY THIS EXISTS. GitHub retires the Node runtime an action major ships on. When it
does, the runner does NOT fail the job - it force-runs the deprecated action on the
current Node and prints a warning. So a repository pinned to a retired runtime keeps
going green, and the upgrade is applied by GitHub rather than by the project, until
the fallback is withdrawn on a day the project did not choose.

WHAT IS DERIVED AND WHAT IS LISTED, because the two are not the same claim. The
POPULATION of pins graded is DERIVED from the workflow files - twice, by two
enumerations that share no constant - so a pin added to a workflow cannot escape the
grade by not being on a list. The RUNTIME TABLE is a shipped constant, because no
test on this project reaches the network. An action the table does not name is a
LOUD offence, never a silent pass: a table that forgives what it does not know is
the silent-permissive failure this project's doctrine rules against.

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

# The lowest MAJOR of each action whose runtime GitHub still supports. Every major
# below these ships on Node 20, whose runtime is deprecated; every major at or above
# them ships on Node 24. Bump an entry only against the action's own release notes,
# never to make a red go away.
RUNTIME_SUPPORTED_FROM: dict[str, int] = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "actions/upload-artifact": 5,
    "actions/setup-node": 5,
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


def _reference(workflow: str, value: object) -> Pin | None:
    if not isinstance(value, str) or "@" not in value:
        return None
    action, _, ref = value.partition("@")
    return Pin(workflow=workflow, action=action, ref=ref)


def pins_by_parse(workflow: str, text: str) -> list[Pin]:
    """ENUMERATION ONE - what the YAML PARSER resolves.

    Walks every mapping the document contains and collects the step-reference key's
    value wherever it appears, at any depth, so a nested or composite shape cannot
    hide a pin from the grade.
    """
    found: list[Pin] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "uses":
                    pin = _reference(workflow, value)
                    if pin is not None:
                        found.append(pin)
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(yaml.safe_load(text))
    return found


_SLUG_LINE = re.compile(
    r"^[^\S\n]*-?[^\S\n]*[A-Za-z_][A-Za-z0-9_-]*:[^\S\n]*"
    r"([A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*@[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"[^\S\n]*$",
    re.MULTILINE,
)


def pins_by_scan(workflow: str, text: str) -> list[Pin]:
    """ENUMERATION TWO - what the raw TEXT shows, by SHAPE alone.

    This function names no key. It recognises a pin by the owner/repo@ref shape
    sitting alone on the right of a mapping key, so it shares no constant with
    enumeration one and cannot inherit that enumeration's blind spot. A pin the
    parser resolves that this scan cannot see - or the reverse - is a disagreement
    the arms report rather than average away.
    """
    return [
        pin for raw in _SLUG_LINE.findall(text) if (pin := _reference(workflow, raw)) is not None
    ]


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
        for pin in pins_by_parse(_relative(root, path), path.read_text(encoding="utf-8"))
    ]


def derive_pins_independently(root: Path) -> list[Pin]:
    """The same population, taken from enumeration two. Compared, never merged."""
    return [
        pin
        for path in workflow_files(root)
        for pin in pins_by_scan(_relative(root, path), path.read_text(encoding="utf-8"))
    ]


_MAJOR = re.compile(r"^v([0-9]+)(?:\.[0-9]+)*$")


def grade_pin(pin: Pin) -> str | None:
    """The offence this pin carries, or None when its runtime is still supported."""
    supported_from = RUNTIME_SUPPORTED_FROM.get(pin.action)
    if supported_from is None:
        return (
            f"{pin.workflow} pins {pin.spelling}, an action "
            "tools/action_runtimes.py RUNTIME_SUPPORTED_FROM does not name, so its "
            "runtime is ungraded. Add it to that table against its release notes."
        )
    match = _MAJOR.match(pin.ref)
    if match is None:
        return (
            f"{pin.workflow} pins {pin.spelling}, whose ref carries no major version, "
            "so no runtime can be read off it."
        )
    major = int(match.group(1))
    if major < supported_from:
        return (
            f"{pin.workflow} pins {pin.spelling}, whose runtime is deprecated. "
            f"{pin.action} ships a supported runtime from v{supported_from}."
        )
    return None


def offences(root: Path) -> list[str]:
    """Every pin whose runtime is deprecated, ungradable or unknown to the table."""
    return [offence for pin in derive_pins(root) if (offence := grade_pin(pin)) is not None]
