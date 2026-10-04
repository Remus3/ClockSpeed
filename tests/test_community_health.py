"""CS-959 - the four community-health files an outsider reads first.

THE LOAD-BEARING ARM IS RESOLUTION, NOT EXISTENCE. A community-health file
that names a path or links to a file that is not in the tree is the exact
defect a stranger hits on their first minute in this repository, and it is
invisible to every other gate here: `tools/drift_guard.py` guard (c) resolves
citations inside `memory/` only, and `tools/doc_budget.py` does not walk
`.github/` at all. So these four files carry no automated resolution check
anywhere else, and this module is it.

EVERY ARM CARRIES AN ANTI-VACUITY FLOOR. A regex that stops matching turns a
resolution check into a check of nothing while still reporting PASS, which is
the failure class `CONVENTIONS.md` section 15.1 names. Each file therefore
asserts a minimum number of citations actually extracted and resolved, so a
silently-empty population fails instead of passing.

THE CHARACTER-SET AND LINE-ENDING ARMS ARE NOT REDUNDANT WITH THE HOOKS. The
tier-0 gates run on a machine that has had `scripts/install_hooks.py` run in
it; a fresh clone has not, and these files are precisely the ones a fresh
clone reads.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB_DIR = REPO_ROOT / ".github"

# The four rows CS-959 fills, with the anti-vacuity floor each one's body must
# clear. The floors are deliberately well under what each file carries, so a
# later edit that removes one citation does not fail the suite, while a regex
# that matches nothing at all does.
COMMUNITY_FILES: tuple[tuple[str, int], ...] = (
    ("CONTRIBUTING.md", 8),
    ("CODE_OF_CONDUCT.md", 1),
    ("SECURITY.md", 2),
    ("PULL_REQUEST_TEMPLATE.md", 2),
    # The legacy single-file template: the only shape that fills the profile API's
    # files.issue_template row. Folder templates leave it null (CS-959).
    ("ISSUE_TEMPLATE.md", 2),
)

FILE_NAMES: tuple[str, ...] = tuple(name for name, _ in COMMUNITY_FILES)

# A markdown inline link. The target is taken verbatim so a finding can quote
# what the author wrote rather than a normalised form of it.
_MDLINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# A backticked span. Narrowed to path-shaped spans by _is_repo_path below
# rather than in the pattern, so that what is excluded can be counted.
_BACKTICK = re.compile(r"`([^`\n]+)`")

# Anything carrying a scheme is not a repository path and is not resolved here.
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

# A path-shaped backticked span: no whitespace, so a shell command line is
# excluded, and either a directory separator or a source-file extension, so a
# bare identifier such as `core.hooksPath` is excluded.
_PATH_SHAPE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")
_PATH_SUFFIXES = (".md", ".py", ".yml", ".yaml", ".json", ".toml", ".ps1")

# The highest code point 7-bit ASCII carries. Named so the arm below reads as the rule
# it enforces rather than as a bare comparison against a literal.
ASCII_MAX = 0x7F


def _body(name: str) -> str:
    return (GITHUB_DIR / name).read_text(encoding="utf-8", errors="replace")


def _is_repo_path(span: str) -> bool:
    """Whether a backticked span names a path this tree should carry."""
    if not _PATH_SHAPE.match(span) or _URL_SCHEME.match(span):
        return False
    return "/" in span or span.lower().endswith(_PATH_SUFFIXES)


def _citations(body: str) -> list[tuple[str, str]]:
    """``(kind, target)`` pairs this body claims exist, duplicates collapsed.

    Both shapes are harvested because both are claims about the tree: a
    relative markdown link is one an outsider clicks, and a backticked path is
    one they type. A fragment-only link and an absolute URL name no file here
    and are dropped; a link carrying a fragment keeps its path part.

    THE KIND IS CARRIED BECAUSE THE TWO SHAPES RESOLVE AGAINST DIFFERENT
    BASES, and collapsing them would be a real loss. GitHub resolves a
    relative LINK against the directory holding the file, so a link written in
    `.github/` names a sibling there; a backticked PATH is what a contributor
    types at a shell in the repository root. Resolving either against both
    bases would forgive a link GitHub renders broken, which is the one defect
    this module exists to catch.
    """
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, raw: str) -> None:
        target = raw.split("#", 1)[0].strip().replace("\\", "/")
        entry = (kind, target)
        if target and entry not in seen:
            seen.add(entry)
            found.append(entry)

    for match in _MDLINK.finditer(body):
        raw = match.group(1).strip()
        if raw.startswith(("#", "//")) or _URL_SCHEME.match(raw):
            continue
        add("link", raw)
    for match in _BACKTICK.finditer(body):
        span = match.group(1).strip()
        if _is_repo_path(span):
            add("path", span)
    return found


def _resolves(kind: str, target: str) -> bool:
    """Whether one citation names something this tree carries.

    A trailing slash means a directory was cited and a directory is what must
    be there - a file at that name is a finding, not a pass.
    """
    base = GITHUB_DIR if kind == "link" else REPO_ROOT
    if target.endswith("/"):
        return (base / target.rstrip("/")).is_dir()
    candidate = base / target
    return candidate.is_file() or candidate.is_dir()


@pytest.mark.parametrize("name", FILE_NAMES)
def test_community_health_file_exists(name: str) -> None:
    """The file GitHub's community profile looks for is in .github/."""
    path = GITHUB_DIR / name
    assert path.is_file(), (
        f".github/{name} is missing - GitHub's community profile reports that row empty "
        "and an outsider sees the gap before they see the code"
    )


@pytest.mark.parametrize("name", FILE_NAMES)
def test_community_health_file_is_seven_bit_ascii(name: str) -> None:
    """CLAUDE.md non-negotiable 4 - 7-bit ASCII in all authored content."""
    raw = (GITHUB_DIR / name).read_bytes()
    offending = sorted({byte for byte in raw if byte > ASCII_MAX})
    assert not offending, (
        f".github/{name} carries non-ASCII byte(s) {[hex(b) for b in offending]} - "
        "CLAUDE.md non-negotiable 4 forbids them in authored content"
    )


@pytest.mark.parametrize("name", FILE_NAMES)
def test_community_health_file_is_lf_only(name: str) -> None:
    """No CR anywhere - the harness writes CRLF and git hides it on read."""
    raw = (GITHUB_DIR / name).read_bytes()
    assert b"\r" not in raw, (
        f".github/{name} carries a carriage return - this tree is LF only and "
        "a text-mode read would not have shown it"
    )


@pytest.mark.parametrize(("name", "floor"), COMMUNITY_FILES)
def test_community_health_citations_resolve(name: str, floor: int) -> None:
    """Every path and relative link these files claim exists does exist.

    The floor is the anti-vacuity control: a green verdict over an empty
    population would say nothing, and this arm is the only place these four
    files are resolved at all.
    """
    citations = _citations(_body(name))
    assert len(citations) >= floor, (
        f".github/{name} yielded {len(citations)} resolvable citation(s), under the "
        f"floor of {floor} - the extractor matched nothing, so a PASS here would "
        "cover no claims at all"
    )
    unresolved = [entry for entry in citations if not _resolves(*entry)]
    assert not unresolved, (
        f".github/{name} cites {unresolved}, which this tree does not carry - "
        "a community-health file that links to a file that is not there is the "
        "first thing an outsider hits"
    )


def test_security_policy_carries_no_email_address() -> None:
    """CS-959 acceptance - the reporting route is GitHub's, never an address.

    The operator's address is this repository's commit identity and a sibling
    has already published it once by accident, so an address in the file an
    outsider is told to use is the one place it must not appear.
    """
    body = _body("SECURITY.md")
    addresses = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", body)
    assert not addresses, (
        f".github/SECURITY.md carries an address-shaped token {addresses} - the "
        "acceptance routes reports through GitHub private vulnerability reporting "
        "and forbids an email address here"
    )
    assert "security advisor" in body.lower() or "report a vulnerability" in body.lower(), (
        ".github/SECURITY.md names no GitHub private-vulnerability-reporting route, "
        "so it tells a reporter nothing they can act on"
    )


def test_contributing_states_the_non_negotiables() -> None:
    """CS-959 acceptance - the four a drive-by change would break.

    Stated as substring probes over the body rather than as a rendering
    assertion, because what matters is that a contributor who reads only this
    file cannot miss them.
    """
    body = _body("CONTRIBUTING.md").lower()
    required = {
        "7-bit ASCII": "7-bit ascii",
        "no lifted wiki datasets": "wiki",
        "never write to the game install or a save": "never write",
        "the failing test first": "failing test",
        "the hook bootstrap": "docs/operations.md",
    }
    missing = sorted(label for label, probe in required.items() if probe not in body)
    assert not missing, (
        f".github/CONTRIBUTING.md does not state {missing} - a fresh clone runs zero "
        "protection until someone wires it, so an unstated rule is an unenforced one"
    )


def test_pull_request_template_asks_for_the_review_shape() -> None:
    """This repository reviews by item id, acceptance conjunct and evidence."""
    body = _body("PULL_REQUEST_TEMPLATE.md").lower()
    required = {
        "the item id": "cs-",
        "the acceptance conjunct discharged": "acceptance",
        "the evidence": "evidence",
    }
    missing = sorted(label for label, probe in required.items() if probe not in body)
    assert not missing, (
        f".github/PULL_REQUEST_TEMPLATE.md does not ask for {missing} - it would "
        "collect a description instead of the three things this repository reviews on"
    )
