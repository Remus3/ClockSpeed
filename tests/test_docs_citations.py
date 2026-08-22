#!/usr/bin/env python3
"""CS-442 - the Verification pointer in ``docs/`` is guarded, or it is not evidence.

WHY THIS MODULE EXISTS, and the structural fact is sharper than the typo that
opened the item: NOTHING IN THIS REPOSITORY READ ``docs/``.
``tests/save/test_oracle_citations`` scans ``clockspeed/``,
``tests/save/test_absolute_claims`` scans ``tests/``, and neither looked at
``docs/`` at all. So the VERIFICATION POINTER - the one field
``docs/LEDGER.md`` declares mandatory, and the entire reason that file is
trustworthy - was the least guarded prose in the project.

THE RESOLVER IS IMPORTED, NOT TRANSCRIBED, for the reason
``test_absolute_claims`` states about itself: another copy of it would be
another place to get it subtly wrong. :func:`module_scope_names` WIDENS the
imported resolver rather than replacing it, and the widening is stated in its
docstring because it is the difference between the two questions - a pytest
node id can only address a module-level function, while a docs citation may
legitimately name a class or a module-level constant.

FOUR TRAPS SHAPE THIS MODULE. Each was measured on the real corpus, and a
checker that misses any one of them is red on correct history, which is the
failure that gets a guard switched off.

1. A DEAD CITATION IS NOT ONE THING. A record that was RIGHT WHEN WRITTEN and
   whose target the tree later moved is not a defect in the record. A record
   that was WRONG WHEN WRITTEN is. ``docs/LEDGER.md`` is append-only, so the
   second cannot be repaired by editing the entry that carries it - it needs a
   later correcting record. :data:`DISPOSITIONS` is where that distinction is
   recorded, and every entry in it is MACHINE-CHECKED rather than believed.

2. AN UNQUALIFIED CITATION IS NOT A DEAD ONE. A bare basename like
   ``registry.py:206`` resolved repo-relative and then declared missing
   manufactures a finding. A census that did exactly that reported six dead
   targets and all six were artifacts. This module DECLINES to judge an
   unqualified pointer and says so out loud rather than passing it in silence.

3. A ``file:line`` POINTER INTO ``docs/LEDGER.md`` ROTS BY CONSTRUCTION. That
   file is append-only NEWEST FIRST, so prepending an entry shifts every line
   number below it. Asserting one would redden on correct history.

4. A CITATION CAN ASSERT AN ABSENCE. A correction record proving an earlier
   pointer is dead cites the dead name ON PURPOSE - its evidence is that
   ``grep -c`` returns 0. Reddening on it would punish the record for doing the
   right thing. That is the :data:`DELIBERATE` disposition, and the ledger
   already contains one such record.

WHAT THIS MODULE DOES NOT COVER, stated rather than left to be discovered.
``docs/history_notes.md`` is EXCLUDED: it is the deep archive, and its detail
blocks QUOTE dead names deliberately while discussing them, so the quoting and
the citing are indistinguishable by shape there. A citation written as bare
``::name`` with no path in front of it is invisible to both arms below. Both
are recorded in ``ROADMAP.md`` rather than implied here.
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from tests.save import test_oracle_citations as oracle_citations

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# Non-negotiable 4 is 7-bit ASCII, so the highest byte an authored file may
# carry is 0x7E - the tilde, the last printable character in the range.
HIGHEST_ASCII: Final = 0x7E

# The ledger is scoped to its entries. The two pairs above the heading are the
# preamble's ILLUSTRATIVE pointers - they show the shape of a valid citation and
# name no real test - so judging them would redden the documentation of the rule.
LEDGER: Final = "docs/LEDGER.md"
ENTRIES_HEADING: Final = "## Entries"

# ROADMAP.md and docs/GATED.md carry citations too and both measured clean, so
# they are guarded from the start rather than after they rot.
GUARDED_DOCS: Final = (LEDGER, "ROADMAP.md", "docs/GATED.md")

# A path segment may begin with a dot - `.github/workflows/tier1.yml:250` is a
# real citation, and a pattern anchored on an alphanumeric drops the dot and
# then reports a path that does not exist. Measured, on that exact pointer.
_PATH = r"\.?[A-Za-z0-9_][A-Za-z0-9_/.-]*"

CITATION_RE: Final = re.compile(rf"({_PATH}\.py)::([A-Za-z_][A-Za-z0-9_]*)")
LINE_POINTER_RE: Final = re.compile(
    rf"({_PATH}\.(?:py|md|json|toml|yml|yaml|cfg|txt|ini)):([0-9]+)"
)

# A bare test identifier, NOT preceded by "::" or "." - those forms are the
# other two arms' business. The length floor keeps ordinary words out.
BARE_RE: Final = re.compile(r"(?<![:.\w])(test_[a-z0-9_]{8,})\b")

# --- dispositions -----------------------------------------------------------

MOVED: Final = "MOVED"
RENAMED: Final = "RENAMED"
NO_TARGET: Final = "NO_TARGET"
DELIBERATE: Final = "DELIBERATE"


@dataclass(frozen=True)
class Disposition:
    """One recorded answer for one citation that does not resolve as written.

    Attributes:
        kind: MOVED, RENAMED, NO_TARGET or DELIBERATE.
        target: For MOVED and RENAMED, the live ``path::name`` this citation
            should be read as. Empty for the other two, which have nothing to
            verify against.
        why: The evidence, in one line, so the table is auditable without
            re-deriving it.
    """

    kind: str
    target: str
    why: str


# EVERY ENTRY HERE IS CHECKED, IN BOTH DIRECTIONS. A MOVED or RENAMED target
# that stops resolving fails, and an entry whose citation no longer appears -
# or which now resolves on its own - ALSO fails. That second direction is the
# point: an exemption table nothing verifies is how a false declaration ends up
# shipped, and this project has an open item about exactly that.
DISPOSITIONS: Final[Mapping[tuple[str, str], Disposition]] = {
    # --- class 1: the record was RIGHT when written; CS-495 moved the tests.
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_every_library_reaching_module_in_the_package_is_declared",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_every_library_reaching_module_in_the_package_is_declared",
        "CS-471 cited test_properties.py; CS-495 relocated the reach-guard"
        " suite. Not a record defect.",
    ),
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_the_suite_wide_guard_catches_a_module_that_declares_nothing",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_the_suite_wide_guard_catches_a_module_that_declares_nothing",
        "CS-471 citation, relocated by CS-495. Not a record defect.",
    ),
    (
        LEDGER,
        "tests/save/test_properties.py"
        "::test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating",
    ): Disposition(
        MOVED,
        "tests/save/test_reach_guard.py"
        "::test_a_helper_handing_back_a_wrapped_body_is_flagged_as_propagating",
        "CS-471 citation, relocated by CS-495. Not a record defect.",
    ),
    # --- class 2: WRONG WHEN WRITTEN, one unambiguous live target. Each is
    # corrected by a later ledger record, because this file is append-only.
    (
        LEDGER,
        "tests/save/test_absolute_claims.py"
        "::test_the_scanned_prose_carries_no_unbacked_absolute_claim",
    ): Disposition(
        RENAMED,
        "tests/save/test_absolute_claims.py"
        "::test_the_fenced_prose_carries_no_unbacked_absolute_claim",
        "one-word slip, scanned for fenced; the cited name is in no commit in history.",
    ),
    (
        LEDGER,
        "tests/data/test_registry.py::test_the_misspelled_keys_are_used_verbatim_not_autocorrected",
    ): Disposition(
        RENAMED,
        "tests/data/test_registry.py"
        "::test_the_misspelled_game_keys_are_used_verbatim_not_autocorrected",
        "the word game was dropped; the cited name is in no commit in history.",
    ),
    (
        LEDGER,
        "tests/save/test_workdir.py"
        "::test_the_refusal_message_carries_no_non_digit_account_directory",
    ): Disposition(
        RENAMED,
        "tests/save/test_workdir.py"
        "::test_the_refusal_message_carries_no_raw_account_directory_of_a_non_digit_shape",
        "CS-454 is about the non-digit shape, and the surviving variant"
        " postdates the entry and matches its sentence.",
    ),
    # --- class 3: WRONG WHEN WRITTEN, and NO target may be assigned.
    (
        LEDGER,
        "tests/save/test_properties.py::test_the_reach_guard_catches_every_spliced_shape",
    ): Disposition(
        NO_TARGET,
        "",
        "no test bears this meaning: CS-441 records 26 of 46 spliced shapes"
        " still escaping, and stays OPEN.",
    ),
    # --- the bare-identifier arm, which sees what a path scanner cannot.
    (LEDGER, "test_the_header_scan_advertises_no_bound_it_cannot_enforce"): Disposition(
        RENAMED,
        "tests/test_precommit_gate.py"
        "::test_the_header_scan_time_bound_declares_the_scope_it_actually_has",
        "added by ee36d0d, the CS-436 commit, alongside the live sibling the same entry cites.",
    ),
    (LEDGER, "test_the_scanned_prose_carries_no_unbacked_absolute_claim"): Disposition(
        RENAMED,
        "tests/save/test_absolute_claims.py"
        "::test_the_fenced_prose_carries_no_unbacked_absolute_claim",
        "THE SECOND SITE of the same slip, spent bare inside a grep -c with no path attached.",
    ),
    (LEDGER, "test_no_recorded_gap_is_blocked_by_a_frozen_file"): Disposition(
        DELIBERATE,
        "",
        "the CS-411 correction record cites this name to prove it is DEAD;"
        " grep -c returning 0 IS its evidence.",
    ),
}


# --- resolution -------------------------------------------------------------


def module_scope_names(source: str) -> frozenset[str]:
    """Every name a module binds at module scope.

    A DELIBERATE SUPERSET of ``test_oracle_citations.module_scope_functions``,
    which is imported rather than re-implemented and supplies the function half.
    The widening is the difference between the two questions this repository
    asks. A pytest node id carrying one ``::`` can only address a module-level
    FUNCTION, so that module is right to stop there. A docs citation is prose
    and may name a class or a module-level constant - and
    ``clockspeed/save/objects.py::_BYTE_ORDER_CANNOT_SEPARATE_VALUES`` is a real
    one. Resolving functions alone reports it dead, which was measured here
    before this function existed.

    Args:
        source: The module's full text.

    Returns:
        Module-level function, class and assignment-target names.

    Raises:
        SyntaxError: If the source does not parse.
    """
    names = set(oracle_citations.module_scope_functions(source))
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return frozenset(names)


def scoped_text(doc: str, text: str) -> str:
    """Return the part of a doc whose citations are adjudicated.

    Args:
        doc: The repo-relative doc path.
        text: Its full text.

    Returns:
        For the ledger, everything below the entries heading - the preamble's
        illustrative pointers are documentation of the citation SHAPE and name
        no real test. For every other doc, the whole text.
    """
    if doc != LEDGER:
        return text
    _head, marker, tail = text.partition("\n" + ENTRIES_HEADING)
    return tail if marker else text


def citations_in(text: str) -> list[tuple[str, str]]:
    """Extract distinct ``(path, name)`` citations, in order of appearance."""
    out: list[tuple[str, str]] = []
    for path, name in CITATION_RE.findall(text):
        pair = (path, name)
        if pair not in out:
            out.append(pair)
    return out


def unresolved_citations(
    doc: str,
    text: str,
    sources: Mapping[str, str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
) -> list[tuple[str, str, str]]:
    """Every citation in one doc that neither resolves nor carries a disposition.

    Args:
        doc: The repo-relative doc path, used to key :data:`DISPOSITIONS`.
        text: The doc's full text.
        sources: Repo-relative POSIX path to module text. Injected rather than
            read from disk, so a control can supply a corpus with no filesystem
            involved - the same reason the imported resolver takes one.
        dispositions: The recorded answers. Injected for the same reason, and
            because the target-verification branch below only fires when a
            recorded target STOPS resolving - which never happens on the live
            table, so it is a guard on a non-default path and would ship
            untested if a control could not reach it. A mutation battery caught
            exactly that.

    Returns:
        ``(path, name, reason)`` for each citation that is a defect.
    """
    table = DISPOSITIONS if dispositions is None else dispositions
    problems: list[tuple[str, str, str]] = []
    for path, name in citations_in(scoped_text(doc, text)):
        if resolves(path, name, sources):
            continue
        recorded = table.get((doc, f"{path}::{name}"))
        if recorded is None:
            problems.append((path, name, "dead and carries NO recorded disposition"))
            continue
        if recorded.kind in (MOVED, RENAMED):
            target_path, _, target_name = recorded.target.partition("::")
            if not resolves(target_path, target_name, sources):
                problems.append(
                    (path, name, f"its {recorded.kind} target {recorded.target} does not resolve")
                )
    return problems


def resolves(path: str, name: str, sources: Mapping[str, str]) -> bool:
    """Whether ``path`` exists in ``sources`` and binds ``name`` at module scope."""
    source = sources.get(path)
    if source is None:
        return False
    try:
        return name in module_scope_names(source)
    except SyntaxError:
        return False


# --- the file:line arm ------------------------------------------------------


def line_pointer_problems(
    text: str,
    line_counts: Mapping[str, int],
) -> tuple[list[str], list[str]]:
    """Judge every ``file:line`` pointer that can honestly be judged.

    Args:
        text: The scoped doc text.
        line_counts: Repo-relative POSIX path to that file's line count. A path
            absent from this mapping is not a tracked file.

    Returns:
        ``(problems, declined)``. A pointer is DECLINED rather than judged when
        it names the ledger itself, whose line numbers shift every time an entry
        is prepended, or when it is an unqualified bare basename carrying no
        directory - resolving one repo-relative and calling it missing is how a
        census manufactured six findings that were all artifacts.

        Only the pointer's RANGE is judged. Asserting what sits AT the line
        would redden on every edit above it, which is a guard nobody keeps.
    """
    problems: list[str] = []
    declined: list[str] = []
    seen: set[tuple[str, str]] = set()
    for path, lineno in LINE_POINTER_RE.findall(text):
        if (path, lineno) in seen:
            continue
        seen.add((path, lineno))
        if path == LEDGER:
            declined.append(f"{path}:{lineno} - the ledger's own line numbers rot by construction")
        elif "/" not in path:
            declined.append(
                f"{path}:{lineno} - unqualified basename, no directory to resolve against"
            )
        elif path not in line_counts:
            problems.append(f"{path}:{lineno} - names a path that is not a tracked file")
        elif int(lineno) > line_counts[path]:
            problems.append(f"{path}:{lineno} - beyond the end of a {line_counts[path]}-line file")
    return problems, declined


# --- the bare-identifier arm ------------------------------------------------


def bare_name_problems(
    doc: str,
    text: str,
    known_names: Iterable[str],
    module_basenames: Iterable[str],
    dispositions: Mapping[tuple[str, str], Disposition] | None = None,
) -> list[tuple[str, str]]:
    """Judge bare ``test_*`` identifiers, which no path-shaped scanner can see.

    This is the shape the item calls the most important one to cover: the
    mandatory Verification field spends them inside ``grep -c <name>``, with no
    path attached, and a ``path::name`` scanner is structurally blind to them.
    One dead citation in the ledger is visible ONLY here.

    Args:
        doc: The repo-relative doc path, used to key :data:`DISPOSITIONS`.
        text: The scoped doc text.
        known_names: Every name bound at module scope anywhere in the tree.
        module_basenames: Tracked module basenames without the extension. A
            bare ``test_properties`` is a MODULE, not a test, and reporting it
            would be noise - the imported resolver's own docstring names that
            ambiguity as the reason it reads a local citation permissively.
        dispositions: The recorded answers, injected for the same reason as
            in :func:`unresolved_citations` - the redirect-verification
            branch is a guard on a non-default path and a control has to be
            able to reach it.

    Returns:
        ``(name, reason)`` for each bare identifier that is a defect.
    """
    table = DISPOSITIONS if dispositions is None else dispositions
    known = set(known_names)
    modules = set(module_basenames)
    problems: list[tuple[str, str]] = []
    seen: set[str] = set()
    # A path::name pair's right half is the other arm's business; blank the
    # whole pair out so it is not judged twice under two different rules.
    stripped = CITATION_RE.sub(" ", text)
    for name in BARE_RE.findall(stripped):
        if name in seen or name in known or name in modules:
            continue
        seen.add(name)
        recorded = table.get((doc, name))
        if recorded is None:
            problems.append((name, "bound nowhere in the tree and carries NO recorded disposition"))
        elif recorded.kind in (MOVED, RENAMED):
            _target_path, _, target_name = recorded.target.partition("::")
            if target_name not in known:
                problems.append(
                    (name, f"its {recorded.kind} target {recorded.target} does not resolve")
                )
    return problems


# --- the live corpus --------------------------------------------------------


def tracked_files() -> list[str]:
    """Every path in this checkout's index, POSIX-separated."""
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    ).stdout
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


@pytest.fixture(scope="module")
def tracked() -> list[str]:
    return tracked_files()


@pytest.fixture(scope="module")
def sources(tracked: list[str]) -> dict[str, str]:
    return {
        path: (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in tracked
        if path.endswith(".py")
    }


@pytest.fixture(scope="module")
def line_counts(tracked: list[str]) -> dict[str, int]:
    counts = {}
    for path in tracked:
        try:
            body = (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        counts[path] = len(body.split("\n"))
    return counts


@pytest.fixture(scope="module")
def known_names(sources: Mapping[str, str]) -> frozenset[str]:
    names: set[str] = set()
    for source in sources.values():
        try:
            names |= module_scope_names(source)
        except SyntaxError:
            continue
    return frozenset(names)


def doc_text(doc: str) -> str:
    return (REPO_ROOT / doc).read_text(encoding="ascii", errors="replace")


# --- contract 1: every citation resolves or carries a checked disposition ----


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_every_path_name_citation_in_a_guarded_doc_resolves(
    doc: str, sources: Mapping[str, str]
) -> None:
    problems = unresolved_citations(doc, doc_text(doc), sources)

    assert not problems, (
        "dead citations in "
        + doc
        + ":\n"
        + "\n".join(f"  {path}::{name} - {why}" for path, name, why in problems)
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_every_file_line_pointer_in_a_guarded_doc_is_in_range(
    doc: str, line_counts: Mapping[str, int]
) -> None:
    problems, _declined = line_pointer_problems(scoped_text(doc, doc_text(doc)), line_counts)

    assert not problems, (
        "broken file:line pointers in "
        + doc
        + ":\n"
        + "\n".join(f"  {problem}" for problem in problems)
    )


def test_every_bare_identifier_in_the_ledger_resolves(
    known_names: frozenset[str], tracked: list[str]
) -> None:
    basenames = {path.rsplit("/", 1)[-1][:-3] for path in tracked if path.endswith(".py")}

    problems = bare_name_problems(
        LEDGER, scoped_text(LEDGER, doc_text(LEDGER)), known_names, basenames
    )

    assert not problems, (
        "dead bare identifiers in "
        + LEDGER
        + ":\n"
        + "\n".join(f"  {name} - {why}" for name, why in problems)
    )


# --- contract 2: the disposition table cannot accumulate false declarations --


def test_every_recorded_disposition_is_still_in_use(sources: Mapping[str, str]) -> None:
    """An entry that stopped being needed is a false declaration waiting to happen.

    Checked in the direction an exemption table normally is NOT. A citation that
    was repaired, or a doc that stopped carrying it, leaves an entry here that
    forgives something no longer present - and the next citation that happens to
    match it is forgiven silently. This repository has an open item about
    exactly that shape, so the table is built with the check from the start.
    """
    texts = {doc: scoped_text(doc, doc_text(doc)) for doc in GUARDED_DOCS}
    unused = []
    for doc, cited in DISPOSITIONS:
        haystack = texts.get(doc, "")
        name = cited.rpartition("::")[2] if "::" in cited else cited
        if "::" in cited:
            path = cited.partition("::")[0]
            still_cited = f"{path}::{name}" in haystack
            if still_cited and resolves(path, name, sources):
                unused.append((doc, cited, "now resolves on its own"))
                continue
        else:
            still_cited = name in BARE_RE.findall(CITATION_RE.sub(" ", haystack))
        if not still_cited:
            unused.append((doc, cited, f"no longer cited in {doc}"))

    assert not unused, "stale entries in DISPOSITIONS:\n" + "\n".join(
        f"  {doc} :: {cited} - {why}" for doc, cited, why in unused
    )


def test_every_correctable_disposition_names_a_target_and_the_others_do_not() -> None:
    """The table's own shape, so a MOVED entry cannot silently carry no target."""
    for (doc, cited), recorded in DISPOSITIONS.items():
        assert recorded.kind in (MOVED, RENAMED, NO_TARGET, DELIBERATE), (
            f"{doc}::{cited} carries an unknown disposition {recorded.kind!r}"
        )
        if recorded.kind in (MOVED, RENAMED):
            assert "::" in recorded.target, (
                f"{doc}::{cited} is {recorded.kind} and names no path::name target"
            )
        else:
            assert recorded.target == "", (
                f"{doc}::{cited} is {recorded.kind} and must name no target"
            )
        assert recorded.why.strip(), f"{doc}::{cited} records no evidence"


# --- contract 3: the controls. A guard that cannot fail is not a guard. ------

_LIVE_SOURCE: Final = "def test_a_real_one() -> None:\n    pass\n"
_CORPUS: Final = {"tests/synthetic/test_planted.py": _LIVE_SOURCE}


def test_the_checker_fires_on_a_planted_dead_pointer() -> None:
    """THE CONTROL THE ACCEPTANCE ASKS FOR, on a synthetic corpus."""
    text = "Verification: `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`.\n"

    problems = unresolved_citations("ROADMAP.md", text, _CORPUS)

    assert [(p, n) for p, n, _ in problems] == [
        ("tests/synthetic/test_planted.py", "test_a_name_that_is_not_there")
    ], "a planted dead pointer was not reported"


def test_the_checker_passes_the_same_pointer_once_it_resolves() -> None:
    """The other side of the branch, so the control above is not vacuous."""
    text = "Verification: `tests/synthetic/test_planted.py::test_a_real_one`.\n"

    assert unresolved_citations("ROADMAP.md", text, _CORPUS) == []


def test_a_citation_naming_a_module_that_does_not_exist_is_reported() -> None:
    text = "Verification: `tests/synthetic/test_absent.py::test_a_real_one`.\n"

    problems = unresolved_citations("ROADMAP.md", text, _CORPUS)

    assert len(problems) == 1, "a citation into a missing module was not reported"


def test_a_citation_naming_a_module_level_constant_resolves() -> None:
    """The widening in :func:`module_scope_names`, pinned.

    Resolving functions alone reported a real constant dead. That artifact is
    what this test exists to keep from coming back.
    """
    corpus = {"clockspeed/synthetic/mod.py": "_A_CONSTANT: int = 3\n\n\nclass Thing:\n    pass\n"}

    assert (
        unresolved_citations(
            "ROADMAP.md", "see `clockspeed/synthetic/mod.py::_A_CONSTANT`\n", corpus
        )
        == []
    )
    assert (
        unresolved_citations("ROADMAP.md", "see `clockspeed/synthetic/mod.py::Thing`\n", corpus)
        == []
    )


def test_a_leading_dot_in_a_cited_path_survives_the_pattern() -> None:
    """`.github/workflows/tier1.yml:250` is real, and a dot-blind pattern drops it."""
    problems, declined = line_pointer_problems(
        "CI runs it (`.github/workflows/tier1.yml:250`).\n",
        {".github/workflows/tier1.yml": 259},
    )

    assert problems == [], "a valid dotted path was reported as broken"
    assert declined == [], "a valid dotted path was declined instead of judged"


def test_a_line_pointer_beyond_the_end_of_a_file_is_reported() -> None:
    problems, _declined = line_pointer_problems(
        "see `tools/thing.py:900`\n", {"tools/thing.py": 12}
    )

    assert len(problems) == 1, "a pointer past the end of the file was not reported"


def test_an_unqualified_basename_is_declined_rather_than_called_dead() -> None:
    """TRAP 2. A census that judged these reported six findings, all artifacts."""
    problems, declined = line_pointer_problems("see `registry.py:206`\n", {})

    assert problems == [], "an unqualified basename was judged as a defect"
    assert len(declined) == 1, "an unqualified basename was passed in silence"


def test_a_pointer_into_the_ledger_itself_is_declined() -> None:
    """TRAP 3. Prepending one entry shifts every line number below it."""
    problems, declined = line_pointer_problems(f"see `{LEDGER}:128`\n", {LEDGER: 10})

    assert problems == [], "a ledger self-pointer was judged, and it rots by construction"
    assert len(declined) == 1, "a ledger self-pointer was passed in silence"


def test_the_bare_arm_reports_a_dead_name_the_path_arm_cannot_see() -> None:
    """The whole reason the bare arm exists, on a synthetic ledger fragment."""
    text = 'Verification: `grep -c "test_a_name_that_is_not_bound" tests/x.py` returns 1.\n'

    assert unresolved_citations("ROADMAP.md", text, _CORPUS) == [], (
        "the path arm should be blind to a bare identifier - if it is not, this "
        "control no longer proves the bare arm is load-bearing"
    )
    assert bare_name_problems("ROADMAP.md", text, [], []) == [
        (
            "test_a_name_that_is_not_bound",
            "bound nowhere in the tree and carries NO recorded disposition",
        )
    ]


def test_the_bare_arm_does_not_report_a_module_basename() -> None:
    text = "gated by `test_properties` and the retention controls\n"

    assert bare_name_problems("ROADMAP.md", text, [], ["test_properties"]) == []


def test_the_bare_arm_does_not_re_judge_the_name_half_of_a_full_citation() -> None:
    """Otherwise one dead citation is reported twice under two different rules."""
    text = "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"

    assert bare_name_problems("ROADMAP.md", text, [], []) == []


# --- contract 4: a disposition is a REDIRECT, and a redirect is verified -----
#
# THESE FOUR EXIST BECAUSE A MUTATION BATTERY FOUND THE GAP. Deleting the
# target-verification branch left the whole module green, because every
# recorded target resolves today - so the branch was a guard on a non-default
# path, which is the shape this project's own TDD rules call out as untested by
# construction. The controls below reach it with a synthetic table.

_REDIRECT_TEXT: Final = "see `tests/synthetic/test_planted.py::test_a_name_that_is_not_there`\n"
_REDIRECT_KEY: Final = (
    "ROADMAP.md",
    "tests/synthetic/test_planted.py::test_a_name_that_is_not_there",
)


def test_a_disposition_whose_target_resolves_forgives_the_citation() -> None:
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_planted.py::test_a_real_one", "the target is live"
        )
    }

    assert unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table) == []


def test_a_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The mutant that survived until this test was written."""
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_planted.py::test_gone_now", "the target rotted"
        )
    }

    problems = unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)

    assert len(problems) == 1, "a disposition pointing at a dead target was accepted"
    assert "does not resolve" in problems[0][2]


def test_a_disposition_whose_target_file_vanished_is_reported() -> None:
    table = {
        _REDIRECT_KEY: Disposition(
            MOVED, "tests/synthetic/test_deleted.py::test_a_real_one", "the file is gone"
        )
    }

    assert len(unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table)) == 1


def test_a_bare_disposition_whose_target_stopped_resolving_is_reported() -> None:
    """The same non-default branch, on the arm that has no path to check."""
    text = 'Verification: `grep -c "test_a_name_that_is_not_bound" x.py`\n'
    key = ("ROADMAP.md", "test_a_name_that_is_not_bound")

    live = {key: Disposition(RENAMED, "tests/x.py::test_a_real_one", "live")}
    rotted = {key: Disposition(RENAMED, "tests/x.py::test_gone_now", "rotted")}

    assert bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], live) == []
    assert len(bare_name_problems("ROADMAP.md", text, ["test_a_real_one"], [], rotted)) == 1


def test_a_no_target_disposition_forgives_without_naming_anything() -> None:
    """A disposition with nothing to verify forgives without naming a target.

    NO_TARGET and DELIBERATE must not be treated as a redirect carrying an
    empty target, which would resolve to nothing and report a defect on a
    citation that was deliberately left unassigned.
    """
    table = {_REDIRECT_KEY: Disposition(NO_TARGET, "", "no test bears this meaning")}

    assert unresolved_citations("ROADMAP.md", _REDIRECT_TEXT, _CORPUS, table) == []


def test_this_test_module_is_seven_bit_ascii() -> None:
    """Non-negotiable 4, checked on this file rather than assumed of it."""
    raw = Path(__file__).read_bytes()

    assert not [byte for byte in raw if byte > HIGHEST_ASCII], (
        "this module carries a byte above the 7-bit range"
    )
