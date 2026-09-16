#!/usr/bin/env python3
"""CS-910 - the tool resolver, and the census of every program this tree spawns.

TWO INSTRUMENTS, AND NEITHER IS A SUBSTITUTE FOR THE OTHER.

The PURE half grades :mod:`toolpath` by injecting a PATH and an executability
probe, so the search order, the rooted-entry refusal and every named refusal are
graded identically on Windows and on Linux. CI runs this suite on both, and a
Windows-only rule that only Windows can grade is a rule half the runs skip.

The LIVE half plants a real executable in a real working directory, removes the
current-directory gate from a real child environment, and measures what the
shipped resolver offers. It is Windows-only because the behaviour is: POSIX has
no current-directory search to disarm, so the arm would grade nothing there and
a green result would be a statement about nothing.

THE CONTROL IS PART OF THE LIVE ARM AND NOT A COURTESY. A negative measurement -
"the resolver did not offer the plant" - is worth exactly nothing without
evidence that the plant COULD have been offered. So the live arm asserts, in
order: the plant landed, the current-directory search is live in this process,
and ``shutil.which`` DOES offer the plant. Only then does it assert that
:func:`toolpath.resolve_tool` does not. A first probe of this class came back
clean and meant nothing, because the shell it ran under sets the gate variable
for itself.

NO PATH IS EVER THE SUBJECT OF AN ASSERTION. pytest renders the asserted
EXPRESSION independently of the message, and a ``tmp_path`` on Windows carries
both a home directory and the account name - non-negotiable 3. Every assertion
below binds a scalar - a boolean, a count, a verdict word - and asserts on that.
The pure arms use synthetic rooted directories that exist on no machine.
"""

from __future__ import annotations

import ast
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]

# tools/ joins the path so the module under test is imported under the SAME bare
# name every other importer uses. See scripts/make_cert.py for the measurement
# that rules out the `tools.toolpath` spelling: `tools` carries no __init__.py,
# so mypy resolves the file under two module names and refuses the run.
_TOOLS_DIR: Final = REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import toolpath  # noqa: E402

from tests.toolpath_guard import (  # noqa: E402
    BARE_NAME,
    CURDIR_RESOLVER,
    EXEMPTION_BUDGET,
    EXEMPTION_REASON_MINIMUM,
    EXEMPTIONS,
    FILE_FLOOR,
    FINDING_VERDICTS,
    INDIRECT,
    INTERPRETER,
    RESOLVED,
    SITE_FLOOR,
    SPAWN_ROOTS,
    SPELLED_PATH,
    VERDICTS,
    ProgramSite,
    describe,
    exemption_budget_problems,
    findings,
    frozen_files,
    graded_python_files,
    is_frozen,
    scan_repository,
    scan_source,
    stale_exemptions,
    unfrozen_exemptions,
    ungraded,
)

# ---------------------------------------------------------------------------
# Synthetic PATHs. Rooted, and on no machine anywhere.
# ---------------------------------------------------------------------------

#: A drive-rooted directory that exists nowhere. Every pure arm searches these,
#: so nothing below can accidentally resolve a real tool and pass for the wrong
#: reason.
FIRST_DIR: Final = "Q:\\first"
SECOND_DIR: Final = "Q:\\second"

#: A POSIX-rooted pair, for the arms that grade the non-Windows branch.
FIRST_POSIX: Final = "/first"
SECOND_POSIX: Final = "/second"

#: A suffix list with two members, so directory-major order is observable.
TWO_SUFFIXES: Final = ".COM;.EXE"

#: The name the pure arms resolve. One character, so a candidate string is short
#: enough to read in a failure.
TOOL: Final = "t"

#: Every PATH entry shape that is NOT rooted and must therefore be skipped. Each
#: is here with the reason it reads as absolute and is not - see
#: tools/toolpath.py::WINDOWS_ROOTED.
UNROOTED_ENTRIES: Final = (
    ".",
    "..",
    "relative",
    "sub\\dir",
    "C:name",
    "\\no-drive",
    "/no-drive",
)

#: The environment variable Windows consults before searching the current
#: directory. Set at NEITHER machine nor user scope on the development machine,
#: which is what makes the search live for anything Explorer launches.
CURDIR_GATE: Final = "NoDefaultCurrentDirectoryInExePath"

WINDOWS_ONLY: Final = pytest.mark.skipif(
    os.name != "nt",
    reason=(
        "the current-directory executable search is a Windows behaviour; there is nothing"
        " on POSIX for this arm to disarm, so it would grade nothing. The property itself"
        " is graded on every platform by the injected arms above."
    ),
)


def _recording_probe(seen: list[str]) -> Callable[[str], bool]:
    """A probe that records every candidate and accepts none.

    Args:
        seen: The list each candidate is appended to.

    Returns:
        The probe.
    """

    def probe(candidate: str) -> bool:
        seen.append(candidate)
        return False

    return probe


# ---------------------------------------------------------------------------
# The resolver - the property, graded on every platform
# ---------------------------------------------------------------------------


def test_the_current_directory_is_never_searched() -> None:
    """CS-910 - the defect, in its pure form.

    ``.`` is how the current directory arrives inside a PATH, and ``shutil.which``
    inserts exactly that string at position zero. A resolver that honoured it
    would offer a candidate from a directory the caller never named.
    """
    seen: list[str] = []
    toolpath.resolve(
        TOOL,
        path_value=f".;{FIRST_DIR}",
        path_ext=TWO_SUFFIXES,
        is_executable=_recording_probe(seen),
        windows=True,
    )

    from_curdir = [candidate for candidate in seen if candidate.startswith(".")]
    assert from_curdir == [], f"{len(from_curdir)} candidate(s) came from the current directory"
    assert len(seen) > 0, "no candidate was tested at all, so this arm graded nothing"


@pytest.mark.parametrize("entry", UNROOTED_ENTRIES)
def test_an_unrooted_path_entry_is_skipped_entirely(entry: str) -> None:
    """Every shape whose meaning depends on where the process is standing.

    ``C:name`` and a leading separator with no drive are the two that read as
    absolute and are not: the first is relative to that drive's own current
    directory and the second to the current drive.
    """
    seen: list[str] = []
    resolution = toolpath.resolve(
        TOOL,
        path_value=entry,
        path_ext=TWO_SUFFIXES,
        is_executable=_recording_probe(seen),
        windows=True,
    )

    assert seen == [], f"an unrooted entry was searched, producing {len(seen)} candidate(s)"
    assert resolution.refusal == toolpath.REFUSE_NO_TOOL


def test_the_search_is_directory_major() -> None:
    """Every suffix in one directory before moving to the next.

    Windows searches this way. Getting it backwards would let a suffix earlier in
    PATHEXT win from a directory later in PATH, which is a different tool than
    the operating system would have run.
    """
    seen: list[str] = []
    toolpath.resolve(
        TOOL,
        path_value=f"{FIRST_DIR};{SECOND_DIR}",
        path_ext=TWO_SUFFIXES,
        is_executable=_recording_probe(seen),
        windows=True,
    )

    expected = [
        f"{FIRST_DIR}\\{TOOL}.COM",
        f"{FIRST_DIR}\\{TOOL}.EXE",
        f"{SECOND_DIR}\\{TOOL}.COM",
        f"{SECOND_DIR}\\{TOOL}.EXE",
    ]
    assert seen == expected


def test_what_comes_back_is_rooted() -> None:
    """The whole contract in one line: an absolute path, or nothing."""
    resolved = toolpath.resolve_tool(
        TOOL,
        path_value=f"{FIRST_DIR};{SECOND_DIR}",
        path_ext=TWO_SUFFIXES,
        is_executable=lambda candidate: candidate.endswith(".EXE"),
        windows=True,
    )

    assert resolved == f"{FIRST_DIR}\\{TOOL}.EXE"


def test_a_trailing_separator_on_a_path_entry_does_not_double() -> None:
    """A hand-written PATH often ends an entry with a separator."""
    seen: list[str] = []
    toolpath.resolve(
        TOOL,
        path_value=f"{FIRST_DIR}\\\\",
        path_ext=".EXE",
        is_executable=_recording_probe(seen),
        windows=True,
    )

    assert seen == [f"{FIRST_DIR}\\{TOOL}.EXE"]


def test_the_posix_branch_searches_the_bare_name_and_skips_the_current_directory() -> None:
    """POSIX has no suffix list, and ``.`` is unrooted there too."""
    seen: list[str] = []
    toolpath.resolve(
        TOOL,
        path_value=f".:{FIRST_POSIX}:{SECOND_POSIX}",
        is_executable=_recording_probe(seen),
        windows=False,
    )

    assert seen == [f"{FIRST_POSIX}/{TOOL}", f"{SECOND_POSIX}/{TOOL}"]


def test_a_name_already_carrying_a_known_suffix_is_tried_bare_first() -> None:
    """Otherwise a caller asking for `t.exe` is only ever offered `t.exe.EXE`."""
    seen: list[str] = []
    toolpath.resolve(
        f"{TOOL}.exe",
        path_value=FIRST_DIR,
        path_ext=".EXE",
        is_executable=_recording_probe(seen),
        windows=True,
    )

    assert seen == [f"{FIRST_DIR}\\{TOOL}.exe", f"{FIRST_DIR}\\{TOOL}.exe.EXE"]


def test_a_probe_that_answers_with_something_other_than_true_is_not_believed() -> None:
    """`is True`, not truthiness.

    A probe answering with a truthy non-boolean has lost track of the question,
    and reading that as yes would resolve a tool on the strength of a value that
    was never an answer.
    """
    resolution = toolpath.resolve(
        TOOL,
        path_value=FIRST_DIR,
        path_ext=".EXE",
        is_executable=lambda _candidate: "yes",  # type: ignore[arg-type,return-value]
        windows=True,
    )

    assert resolution.refusal == toolpath.REFUSE_NO_TOOL


# ---------------------------------------------------------------------------
# The refusals - every member of the vocabulary, reachable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["", "sub/t", "sub\\t", "C:t"])
def test_a_name_that_is_already_a_path_is_refused(name: str) -> None:
    """This module resolves NAMES, not paths.

    Something carrying a directory part is a choice already made, and resolving
    it would confirm that choice rather than check it.
    """
    resolution = toolpath.resolve(name, path_value=FIRST_DIR, path_ext=".EXE", windows=True)

    assert resolution.refusal == toolpath.REFUSE_UNNAMED_TOOL


def test_an_empty_path_is_a_refusal_and_not_a_missing_tool() -> None:
    """An unreadable PATH and a missing tool are different answers.

    They need different operator actions, so they get different words rather
    than a shared None that collapses both into "not installed".
    """
    resolution = toolpath.resolve(TOOL, path_value="", path_ext=".EXE", windows=True)

    assert resolution.refusal == toolpath.REFUSE_UNSEARCHABLE_PATH


def test_a_pathext_naming_no_suffix_is_a_refusal() -> None:
    """A PATHEXT naming no usable suffix leaves nothing to build.

    On Windows an extension-less candidate is not launchable by the call that
    spawns it, so there is no candidate left to offer.
    """
    resolution = toolpath.resolve(TOOL, path_value=FIRST_DIR, path_ext="junk", windows=True)

    assert resolution.refusal == toolpath.REFUSE_UNKNOWN_EXTENSIONS


def test_a_full_search_that_finds_nothing_refuses_rather_than_guessing() -> None:
    """A full search that finds nothing refuses rather than guessing.

    A caller that spawned the answer without checking then spawns None and
    fails loudly, rather than silently running whatever happened to be nearest.
    """
    resolution = toolpath.resolve(
        TOOL,
        path_value=FIRST_DIR,
        path_ext=".EXE",
        is_executable=lambda _candidate: False,
        windows=True,
    )

    assert resolution.refusal == toolpath.REFUSE_NO_TOOL
    assert resolution.path is None
    assert resolution.ok is False


def test_every_published_refusal_is_reachable() -> None:
    """A vocabulary member no condition produces is a word that grades nothing.

    Graded by walking THIS module's arms for the refusals they assert, so a
    refusal added to :data:`toolpath.REFUSALS` without an arm reddens here rather
    than sitting unexercised.
    """
    source = Path(__file__).read_text(encoding="ascii")
    tree = ast.parse(source)
    asserted = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "toolpath"
        and node.attr.startswith("REFUSE_")
    }

    missing = sorted(toolpath.REFUSALS - asserted)
    assert missing == [], (
        f"{len(missing)} published refusal(s) are asserted by no arm here: {missing}"
    )
    unknown = sorted(asserted - toolpath.REFUSALS)
    assert unknown == [], f"{len(unknown)} arm(s) assert a refusal the module does not publish"


def test_the_environment_is_read_when_nothing_is_injected() -> None:
    """The default path. Without this arm every other one grades an injection."""
    seen: list[str] = []
    toolpath.resolve(TOOL, is_executable=_recording_probe(seen))

    assert len(seen) > 0, "no candidate was built from the real environment"
    unrooted = [candidate for candidate in seen if not Path(candidate).is_absolute()]
    assert unrooted == [], f"{len(unrooted)} candidate(s) built from the environment are relative"


@pytest.mark.parametrize(
    "entry",
    [
        "C:\\with\x00null",
        "C:\\" + "a" * 5000,
        "C:\\wild*card?",
        "C:\\",
    ],
    ids=["embedded-null", "very-long", "wildcards", "bare-drive"],
)
def test_a_malformed_path_entry_refuses_rather_than_raising(entry: str) -> None:
    """A hostile PATH must produce a refusal, never an exception.

    THIS RESOLVER IS REACHED FROM A SessionStart HOOK AND A PRE-COMMIT GATE, and
    a gate that cannot START does not block. An embedded null reaches ``os.stat``
    as a ValueError rather than an OSError; the running interpreter's
    ``Path.is_file`` happens to swallow it, but that is a property of this
    version and this project supports back to 3.13, so the refusal is asserted
    here rather than borrowed.
    """
    resolution = toolpath.resolve(TOOL, path_value=entry, path_ext=".EXE", windows=True)

    assert resolution.refusal == toolpath.REFUSE_NO_TOOL
    assert resolution.path is None


# ---------------------------------------------------------------------------
# The live half - a real plant, a real child, a real search
# ---------------------------------------------------------------------------


@WINDOWS_ONLY
def test_a_candidate_planted_in_the_working_directory_is_never_offered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CS-910 - measured against the real filesystem, with the gate disarmed.

    THE THREE CONTROLS COME FIRST. Without them a green result cannot be told
    apart from an arm that reproduced nothing: the shell this was first probed
    under sets the gate variable for itself, and under that shell the shipped
    ``shutil.which`` looked correct.
    """
    import _winapi  # noqa: PLC0415

    planted_name = "cs910probe"
    planted = tmp_path / f"{planted_name}.exe"
    planted.write_bytes(b"MZ not a real executable, and it does not need to be\n")

    landed = planted.is_file() and planted.stat().st_size > 0
    assert landed, "the plant did not land, so this arm grades nothing"

    monkeypatch.chdir(tmp_path)
    for key in [name for name in os.environ if name.upper() == CURDIR_GATE.upper()]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))

    gate_open = _winapi.NeedCurrentDirectoryForExePath(planted_name)
    assert gate_open is True, (
        "the current-directory search is not live in this process, so this arm cannot"
        " reproduce the defect it exists to grade"
    )

    import shutil  # noqa: PLC0415

    control = shutil.which(planted_name)
    assert control is not None, (
        "the current-directory-consulting resolver did not offer the plant, so the"
        " control failed and the negative below would prove nothing"
    )
    control_is_relative = not Path(control).is_absolute()
    assert control_is_relative, (
        "the control resolved something ABSOLUTE, so it did not reach the plant by the"
        " route this arm is about"
    )

    offered = toolpath.resolve_tool(planted_name)
    assert offered is None, (
        "tools/toolpath.py offered a candidate supplied by the working directory, which"
        " is the single property it exists to have"
    )


# ---------------------------------------------------------------------------
# The census - the whole tree, per site
# ---------------------------------------------------------------------------


def test_no_program_in_the_spawn_roots_can_be_supplied_by_the_working_directory() -> None:
    """CS-910's acceptance, over every graded site, one at a time.

    PER SITE AND NEVER POOLED. A ratio or a total over this population would be
    satisfied by its strongest member while the weakest went unmeasured, so every
    finding is named here and none is absorbed into a score.
    """
    unrouted = findings(scan_repository())

    assert unrouted == [], (
        f"{len(unrouted)} program(s) under {SPAWN_ROOTS} are chosen by where the process"
        f" happens to be standing:\n{describe(unrouted)}"
    )


def test_the_census_reaches_a_plausible_share_of_the_tree() -> None:
    """A walk that broke and enumerated nothing passes every per-site rule here.

    The two floors are literals well beneath what this tree holds. They catch a
    dead walk, not ordinary churn.
    """
    files = graded_python_files()
    sites = scan_repository()

    assert len(files) >= FILE_FLOOR
    assert len(sites) >= SITE_FLOOR


@pytest.mark.parametrize("root", SPAWN_ROOTS)
def test_every_spawn_root_is_reached_by_the_walk(root: str) -> None:
    """The floors above are tree-wide, and a tree-wide floor is met by tests alone.

    This is the per-root half: a root that stops being enumerated - renamed,
    excluded, or emptied by a broken walk - reddens here instead of quietly
    contributing nothing to a total that still clears.
    """
    directory = REPO_ROOT / root
    assert directory.is_dir(), f"{root} is named as a spawn root and is not a directory"

    reached = {path.split("/")[0] for path in graded_python_files()}
    assert root in reached, f"the enumeration returned no file under {root}"


def test_the_exemption_budget_holds_in_both_directions() -> None:
    """A ceiling checked only from below is met forever by a table that shrinks."""
    problems = exemption_budget_problems(EXEMPTIONS, EXEMPTION_BUDGET)

    assert problems == [], "\n".join(problems)


def test_every_exemption_states_a_reason_rather_than_a_word() -> None:
    """Every exemption argues its case rather than naming one.

    A minimum length cannot make a reason TRUE. It only makes a placeholder
    cost more to type than it is worth.
    """
    thin = sorted(
        f"{path} {callee} #{ordinal} in {function}()"
        for (path, function, callee, ordinal), reason in EXEMPTIONS.items()
        if len(reason) < EXEMPTION_REASON_MINIMUM
    )

    assert thin == [], f"{len(thin)} exemption(s) carry no argument: {thin}"


def test_every_exemption_names_a_site_that_is_still_a_finding() -> None:
    """A stale exemption is a forgiveness with nothing left to forgive.

    Left in place it will silently absorb the next site that lands on its key.
    """
    stale = stale_exemptions(scan_repository())

    assert stale == [], f"{len(stale)} exemption(s) are stale:\n" + "\n".join(stale)


def test_every_exemption_names_a_file_frozen_by_claude_md() -> None:
    """The table's whole justification, asserted rather than asserted-in-prose.

    CS-910 cannot fully close while this is non-empty: its acceptance says every
    external tool this repository spawns, and these four sit behind CLAUDE.md
    section 6, which no agent may open for itself.
    """
    outside = unfrozen_exemptions(EXEMPTIONS)

    assert outside == [], (
        f"{len(outside)} exemption(s) name a file CLAUDE.md's frozen LIST does not"
        f" cover, so the table's stated reason does not apply to them:\n" + "\n".join(outside)
    )


def test_the_frozen_check_reads_the_list_and_not_the_whole_document() -> None:
    """THE META-TEST ON THE ORACLE, because the oracle is what was broken.

    The arm above used to ask ``path not in CLAUDE.md``. CLAUDE.md's module map
    and tooling map name ten non-frozen ``.py`` files, so that check accepted an
    exemption for any of them - MEASURED by planting a row keyed on
    ``tools/drift_guard.py``, hashing the file to prove the mutation landed, and
    watching the arm pass.

    The document-mention is asserted here on purpose. Without it this test would
    pass for the wrong reason on a day CLAUDE.md stopped mentioning the file at
    all, and would then be pinning nothing.
    """
    entries = frozen_files()
    document = (REPO_ROOT / "CLAUDE.md").read_text(encoding="ascii")
    decoy = "tools/drift_guard.py"

    assert decoy in document, (
        f"{decoy} is no longer mentioned in CLAUDE.md, so it is not the decoy this"
        " arm needs - pick another non-frozen file the document names"
    )
    assert is_frozen("tools/precommit_gate.py", entries), (
        "a file the frozen list names was not recognised, so the parser read the"
        " wrong section or the list shape changed"
    )
    assert not is_frozen(decoy, entries), (
        f"{decoy} is mentioned by CLAUDE.md and is NOT in its frozen list, so a"
        " check that accepts it is reading the document rather than the list"
    )
    planted = {(decoy, "planted", "subprocess.run", 1): "a reason that does not apply"}
    assert len(unfrozen_exemptions(planted)) == 1, (
        "an exemption naming a non-frozen file was not reported, so the table's"
        " justification is still unchecked"
    )


def test_the_frozen_list_covers_the_hook_directory_it_freezes() -> None:
    """The glob entry, which an exact-string comparison would silently drop.

    CLAUDE.md freezes the hook directory as a pattern rather than file by file.
    A membership test that compared strings would accept the literal entry - a
    path no file has - while refusing every real hook under it, so the one
    directory most worth freezing would be the one left unprotected.
    """
    entries = frozen_files()

    assert is_frozen(".githooks/pre-commit", entries), (
        "a file directly under the frozen hook directory was not recognised as"
        " frozen, so the glob entry is being compared rather than honoured"
    )
    assert not is_frozen("tools/toolpath.py", entries), (
        "an unrelated file matched the frozen list, so the glob is too greedy"
    )


# ---------------------------------------------------------------------------
# CS-1102 - the exemption key survives an edit ABOVE a site and still grades one AT it
# ---------------------------------------------------------------------------

#: The exempted file the plants are made against. FROZEN, so every plant below
#: happens in memory through scan_source and the file on disk is only read.
EXEMPTED_PATH: Final = "scripts/install_hooks.py"

#: The exempted function inside it, and the callee its exempted spawn makes.
EXEMPTED_FUNCTION: Final = "run_git"
EXEMPTED_CALLEE: Final = "subprocess.run"

#: The block planted above the exempted spawn. Comments only, so the edit moves
#: the site without changing it - which is the whole of what the acceptance asks.
COMMENT_BLOCK: Final = (
    "# CS-1102 plant - a comment block above the exempted spawn.",
    "# It changes no statement, no callee and no program.",
    "# It moves every line below it down by the length of this block.",
    "# A key that carries the line reads that move as a new site.",
    "# A key that does not carry it must leave every arm green.",
)

#: A NEW unexempted spawn, planted as a statement in the exempted function.
PLANTED_SPAWN: Final = 'subprocess.run(["git", "cs1102"], timeout=1)'

#: The name a planted function takes. Nothing in the tree defines it.
PLANTED_FUNCTION: Final = "cs1102_planted"


def _pristine_exempted_source() -> str:
    """The exempted file's real text, read and never written."""
    return (REPO_ROOT / EXEMPTED_PATH).read_text(encoding="utf-8")


def _exempted_sites(source: str) -> list[ProgramSite]:
    """The finding sites in the exempted function that make the exempted callee."""
    return [
        site
        for site in scan_source(EXEMPTED_PATH, source)
        if site.finding and site.function == EXEMPTED_FUNCTION and site.callee == EXEMPTED_CALLEE
    ]


def _exempted_spawn_statement(source: str) -> ast.stmt:
    """The simple statement holding the exempted spawn, located by AST and never by line.

    Returns:
        The one Assign or Expr inside the exempted function whose expression
        calls the exempted callee.
    """
    tree = ast.parse(source)
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == EXEMPTED_FUNCTION
    ]
    assert len(functions) == 1, f"{EXEMPTED_FUNCTION} is defined {len(functions)} time(s)"
    statements = [
        node
        for node in ast.walk(functions[0])
        if isinstance(node, ast.Assign | ast.Expr)
        and any(
            isinstance(call, ast.Call) and ast.unparse(call.func) == EXEMPTED_CALLEE
            for call in ast.walk(node)
        )
    ]
    assert len(statements) == 1, (
        f"{EXEMPTED_FUNCTION} holds {len(statements)} statement(s) calling {EXEMPTED_CALLEE},"
        " so the plant has no single site to stand above"
    )
    return statements[0]


def _insert_lines(source: str, before: int, lines: tuple[str, ...], indent: int) -> str:
    """``source`` with ``lines`` inserted above 1-based line ``before`` at ``indent``."""
    kept = source.splitlines(keepends=True)
    block = "".join(f"{' ' * indent}{line}\n" for line in lines)
    return "".join(kept[: before - 1]) + block + "".join(kept[before - 1 :])


def _census_with(path: str, source: str) -> list[ProgramSite]:
    """The real census of every other file, with ``path`` graded from ``source``."""
    return [site for site in scan_repository() if site.path != path] + scan_source(path, source)


def test_an_edit_above_an_exempted_spawn_moves_no_arm() -> None:
    """The first half of CS-1102: a site that MOVED is not a site that CHANGED.

    Measured twice before this arm existed - an edit above two spawn sites, and
    each time the exemption reported stale and the finding reported live.
    """
    pristine = _pristine_exempted_source()
    statement = _exempted_spawn_statement(pristine)
    planted = _insert_lines(pristine, statement.lineno, COMMENT_BLOCK, statement.col_offset)

    before = [site.lineno for site in _exempted_sites(pristine)]
    after = [site.lineno for site in _exempted_sites(planted)]
    assert len(before) == 1, f"the pristine file holds {len(before)} exempted site(s), not 1"
    moved = after[0] - before[0] if len(after) == 1 else None
    assert moved == len(COMMENT_BLOCK), f"the plant moved the site by {moved} line(s)"

    census = _census_with(EXEMPTED_PATH, planted)
    problems = [str(site) for site in findings(census)] + stale_exemptions(census)

    assert problems == [], (
        f"{len(problems)} arm(s) moved on an edit that changed no site:\n" + "\n".join(problems)
    )


@pytest.mark.parametrize("position", ["above", "below"])
def test_a_second_spawn_inside_an_exempted_function_still_reddens(position: str) -> None:
    """The anti-narrowing control: a key loose enough to survive a shift must still grade.

    Same path, same function, same callee - the only thing that tells the
    planted spawn from the exempted one is that there are now two of them. At
    most one may be excused. ABOVE is the known residue: the exemption may
    excuse the plant and report the original, which is still red.
    """
    pristine = _pristine_exempted_source()
    statement = _exempted_spawn_statement(pristine)
    line = statement.lineno if position == "above" else (statement.end_lineno or 0) + 1
    planted = _insert_lines(pristine, line, (PLANTED_SPAWN,), statement.col_offset)
    spawned = len(_exempted_sites(planted)) - len(_exempted_sites(pristine))
    assert spawned == 1, f"the plant added {spawned} site(s) to {EXEMPTED_FUNCTION}, not 1"

    census = _census_with(EXEMPTED_PATH, planted)
    live = findings(census)
    in_function = sum(1 for site in live if site.function == EXEMPTED_FUNCTION)
    stale = len(stale_exemptions(census))

    assert (len(live), in_function, stale) == (1, 1, 0), describe(live)


def test_a_new_spawn_in_another_function_of_an_exempted_file_still_reddens() -> None:
    """The same control where the new site shares the file and nothing else."""
    pristine = _pristine_exempted_source()
    planted = (
        pristine.rstrip("\r\n") + f"\n\n\ndef {PLANTED_FUNCTION}() -> None:\n    {PLANTED_SPAWN}\n"
    )

    live = findings(_census_with(EXEMPTED_PATH, planted))
    named = [site.function for site in live]

    assert named == [PLANTED_FUNCTION], describe(live)


def test_a_change_at_an_exempted_site_reports_the_exemption_stale() -> None:
    """The staleness arm still fires when the site itself changes, not merely moves."""
    pristine = _pristine_exempted_source()
    needle = f"def {EXEMPTED_FUNCTION}("
    occurrences = pristine.count(needle)
    assert occurrences == 1, f"the rename needle occurs {occurrences} time(s)"
    planted = pristine.replace(needle, f"def {PLANTED_FUNCTION}(")

    census = _census_with(EXEMPTED_PATH, planted)
    stale = stale_exemptions(census)
    named = [site.function for site in findings(census)]

    assert (len(stale), named) == (1, [PLANTED_FUNCTION]), "\n".join(stale)
    assert f" {EXEMPTED_FUNCTION}()" in stale[0], stale[0]


def test_a_row_matching_more_than_one_live_site_is_reported() -> None:
    """Each row must answer EXACTLY one site. A row that answers two is not stale and not fine."""
    pristine = _pristine_exempted_source()
    census = _census_with(EXEMPTED_PATH, pristine) + scan_source(EXEMPTED_PATH, pristine)

    problems = stale_exemptions(census)
    rows = sum(1 for (path, _f, _c, _o) in EXEMPTIONS if path == EXEMPTED_PATH)

    assert rows >= 1, f"no exemption row names {EXEMPTED_PATH}, so this arm grades nothing"
    assert len(problems) == rows, "\n".join(problems)


def test_the_exemption_budget_is_typed_by_hand() -> None:
    """The budget is an integer LITERAL, never derived from the roster's own length."""
    tree = ast.parse((REPO_ROOT / "tests" / "toolpath_guard.py").read_text(encoding="utf-8"))
    values = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign | ast.AnnAssign)
        and any(
            isinstance(target, ast.Name) and target.id == "EXEMPTION_BUDGET"
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    literal = [
        isinstance(value, ast.Constant)
        and isinstance(value.value, int)
        and not isinstance(value.value, bool)
        for value in values
    ]

    assert literal == [True], f"EXEMPTION_BUDGET is assigned {len(values)} time(s): {literal}"


def test_the_ungraded_remainder_lies_entirely_outside_the_spawn_roots() -> None:
    """The boundary, asserted rather than assumed.

    The remainder is REPORTED and not asserted over - see tests/toolpath_guard.py
    on why, and on whose write-list repairing it is. What IS asserted is that the
    partition is exact: nothing under a spawn root may end up in the reported
    remainder, which is how a root quietly leaving :data:`SPAWN_ROOTS` would show
    up as a green suite and a shorter graded population.
    """
    leaked = [site for site in ungraded(scan_repository()) if site.graded]

    assert leaked == [], f"{len(leaked)} graded site(s) reached the ungraded remainder"


def test_indirect_is_not_counted_as_an_answer() -> None:
    """The guard's stated limit, said out loud by the suite.

    An expression that does not fold is neither routed nor a finding. Promoting
    it to either would be the guard claiming a reach it does not have.
    """
    assert INDIRECT not in FINDING_VERDICTS
    assert INDIRECT in VERDICTS
    assert INDIRECT not in toolpath.REFUSALS


# ---------------------------------------------------------------------------
# The census machinery, graded in BOTH directions on synthetic source
# ---------------------------------------------------------------------------

#: One module per verdict, each the shortest thing that produces it. Written as
#: source rather than pointed at a real file so the arm keeps grading after the
#: tree it describes has been repaired.
SYNTHETIC: Final = {
    BARE_NAME: "import subprocess\ndef f():\n    subprocess.run(['git', 'x'])\n",
    SPELLED_PATH: "import subprocess\ndef f():\n    subprocess.run(['C:/t/git.exe', 'x'])\n",
    CURDIR_RESOLVER: "import shutil\ndef f():\n    return shutil.which('git')\n",
    INTERPRETER: (
        "import subprocess, sys\ndef f():\n    subprocess.run([sys.executable, '-c', ''])\n"
    ),
    RESOLVED: (
        "import subprocess\nfrom toolpath import resolve_tool\n"
        "def f():\n    g = resolve_tool('git')\n    subprocess.run([g, 'x'])\n"
    ),
    INDIRECT: "import subprocess\ndef f(argv):\n    subprocess.run(argv)\n",
}


@pytest.mark.parametrize("verdict", sorted(SYNTHETIC))
def test_the_scanner_produces_each_verdict_from_the_source_that_earns_it(verdict: str) -> None:
    """The positive direction, one verdict at a time."""
    sites = scan_source("scripts/synthetic.py", SYNTHETIC[verdict])

    produced = [site.verdict for site in sites]
    assert verdict in produced, f"expected {verdict}, got {produced}"


def test_a_name_assigned_a_bare_constant_does_not_walk_past_the_scanner() -> None:
    """The obvious evasion: hide the literal one line above the call.

    A scanner that only reads call sites is disarmed by two lines of ordinary
    code, which is why the fold resolves an identifier against its enclosing
    function and then against module scope.
    """
    source = "import subprocess\nPROG = 'git'\ndef f():\n    subprocess.run([PROG, 'x'])\n"

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [BARE_NAME]


def test_a_name_assigned_through_another_name_does_not_walk_past_the_scanner() -> None:
    """THE REGRESSION THIS GUARD WAS MEASURED FAILING.

    The first version of the fold stopped at the first assigned value that was
    not a constant. Planted against the repaired tree - ``git = GIT_NAME`` in
    place of the resolver call, with ``GIT_NAME = "git"`` already at module scope
    - the census answered INDIRECT and stayed GREEN. The mutation had landed; the
    guard was blind to it. That is one indirection, and one indirection is what an
    ordinary edit produces, so it is graded here rather than trusted.
    """
    source = (
        "import subprocess\n"
        "GIT_NAME = 'git'\n"
        "def f():\n"
        "    prog = GIT_NAME\n"
        "    subprocess.run([prog, 'x'])\n"
    )

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [BARE_NAME]


def test_a_name_that_is_sometimes_resolved_is_still_reported() -> None:
    """Safest-first, when the paths disagree.

    A program routed on one branch and named on another is chosen by the working
    directory on the branch that names it, so the finding is what comes back.
    Claiming ROUTED because one assignment was routed would be the guard rounding
    an uncertainty up into a clearance.
    """
    source = (
        "import subprocess\n"
        "from toolpath import resolve_tool\n"
        "def f(fallback):\n"
        "    prog = resolve_tool('git')\n"
        "    if fallback:\n"
        "        prog = 'git'\n"
        "    subprocess.run([prog, 'x'])\n"
    )

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [BARE_NAME]


def test_a_name_that_refers_to_itself_terminates() -> None:
    """A cycle in the fold would hang the suite rather than fail it."""
    source = (
        "import subprocess\n"
        "def f(seed):\n    prog = seed\n    seed = prog\n    subprocess.run([prog])\n"
    )

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [INDIRECT]


def test_an_aliased_import_does_not_walk_past_the_scanner() -> None:
    """An alias binds the same function under an unrecognisable name.

    ``from shutil import which as w`` is invisible to any text scan, so the
    walk follows import aliases rather than spellings.
    """
    source = "from shutil import which as w\ndef f():\n    return w('git')\n"

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [CURDIR_RESOLVER]


@pytest.mark.parametrize(
    "source",
    [
        "from os import system\ndef f():\n    system('git status')\n",
        "from os import system as s\ndef f():\n    s('git status')\n",
    ],
    ids=["plain", "aliased"],
)
def test_an_os_spawner_imported_by_name_does_not_walk_past_the_scanner(source: str) -> None:
    """A WHOLE IMPORT FORM THE CENSUS DID NOT ENUMERATE.

    MEASURED before the repair: both sources below produced ZERO sites - not a
    finding, not an ungraded row, nothing. A site the walk never records is
    invisible to :func:`findings`, to :func:`ungraded` and to the site floor
    alike, so the census reported a clean tree while one of its spawn roots held
    a live ``os.system``. That was confirmed end to end: the plant was written
    into a real spawn root, the mutation was hashed to prove it landed, and the
    whole module stayed green.

    THE DEFENCE EXISTED TWICE AND WAS NOT APPLIED THE THIRD TIME.
    ``_imported_from`` was already run over ``subprocess`` and over the resolver
    module, and never over ``os`` - so ``import os`` was covered, an aliased
    ``from shutil import ...`` was covered, and this form fell between them.
    """
    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]

    assert verdicts == [BARE_NAME], (
        "an os spawner bound by a from-import was not enumerated at all, so no"
        " assertion in this file could have reached it"
    )


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess\ndef f():\n    argv = ['git', 'x']\n    subprocess.run(argv)\n",
        "import subprocess\ndef f():\n    argv = ('git', 'x')\n    subprocess.run(argv)\n",
    ],
    ids=["list", "tuple"],
)
def test_a_program_list_bound_to_a_name_does_not_walk_past_the_scanner(source: str) -> None:
    """THE PLAINEST INDIRECTION THERE IS, and the fold used to stop one step short.

    ``tests/toolpath_guard.py`` claims one hop of constant folding because "one
    indirection is what an ordinary edit produces". A list literal bound to a
    name on the line above the spawn is the MOST ordinary form of that, and it
    folded to INDIRECT: the sequence was unwrapped only at the direct-argument
    position, so a Name bound to a List gave up rather than taking its first
    element.

    INDIRECT is not a finding, so this shape was reported as ungraded and the
    census stayed green - the same walk-past the constant-fold arm above exists
    to prevent, wearing different syntax.
    """
    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]

    assert verdicts == [BARE_NAME], (
        "a program list bound to a name folded to something other than the bare"
        " name it holds, so an ordinary edit walks past this census"
    )


def test_a_binding_inside_a_nested_function_is_not_folded_into_the_outer_scope() -> None:
    """A name bound in a scope the call cannot see is not the name the call uses.

    Folding across that boundary would answer a question nobody asked, and would
    do it confidently.
    """
    source = (
        "import subprocess\n"
        "def outer(prog):\n"
        "    def inner():\n"
        "        prog = 'git'\n"
        "        return prog\n"
        "    subprocess.run([prog, 'x'])\n"
    )

    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]
    assert verdicts == [INDIRECT]


@pytest.mark.parametrize(
    "source",
    [
        "import os\ndef f():\n    os.system('git status')\n",
        "import subprocess\ndef f():\n    subprocess.getoutput('git status')\n",
    ],
    ids=["os.system", "subprocess.getoutput"],
)
def test_a_shell_string_spawner_is_judged_by_its_first_word(source: str) -> None:
    """The same question in different syntax.

    ``os.system`` and ``getoutput`` hand a COMMAND to a shell rather than an
    argv to CreateProcess, and the shell resolves the first word the same way.
    Neither shape is used in this tree today, so without this arm the whole
    :data:`tests.toolpath_guard.OS_SPAWNERS` table would be declared and never
    exercised - a rule that grades nothing until the day it has to, which is the
    day it is discovered not to work.
    """
    verdicts = [site.verdict for site in scan_source("tools/synthetic.py", source)]

    assert verdicts == [BARE_NAME]


def test_a_file_with_no_spawn_yields_no_site() -> None:
    """The negative direction.

    Without it every arm above could be satisfied by a scanner that reports a
    site for every line it reads.
    """
    sites = scan_source("tools/synthetic.py", "import subprocess\nx = 1\n")

    assert sites == []


def test_every_verdict_the_tree_produces_is_one_this_module_names() -> None:
    """The published vocabulary covers everything the tree actually produces.

    A verdict the guard can emit that the vocabulary does not list is a class
    no arm here grades.
    """
    produced = {site.verdict for site in scan_repository()}

    unknown = sorted(produced - VERDICTS)
    assert unknown == [], f"{len(unknown)} verdict(s) are outside the published set: {unknown}"


# ---------------------------------------------------------------------------
# The platform gate over the runtime arms
# ---------------------------------------------------------------------------

#: What a runtime arm touches when it grades the current-directory search.
#: BOTH SPELLINGS ARE HERE BECAUSE THE ARM THAT BROKE THE LANE NAMED NEITHER
#: OUTRIGHT AT AN IMPORT. It reached the module through ``__import__`` inside a
#: probe STRING, so a scan for the import statement alone would have reported a
#: clean population while the defect was live. The scan below reads the whole
#: unparsed function, string constants included, for exactly that reason.
CURDIR_ARM_TERMS: Final = ("_winapi", "NeedCurrentDirectoryForExePath")

#: What a decorator must contain, once resolved and unparsed, to count as a
#: Windows gate. BOTH HALVES ARE REQUIRED AND THAT IS THE POINT: ``skipif``
#: alone would accept a skip taken for any reason at all, and the population
#: here is defined by the PLATFORM the mechanism exists on rather than by the
#: presence of some skip.
CURDIR_GATE_TERMS: Final = ("skipif", "os.name")


def _module_bindings(tree: ast.Module) -> dict[str, str]:
    """Unparse every module-level ``NAME = ...`` so a bare decorator resolves.

    A gate is routinely written once as a module constant and applied by name -
    :data:`WINDOWS_ONLY` above is that shape. A scan that read only the
    decorator's own text would call every such use ungated.

    Args:
        tree: The parsed module.

    Returns:
        Name to unparsed value, for simple single-name assignments only.
    """
    bindings: dict[str, str] = {}
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        value = getattr(node, "value", None)
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                bindings[target.id] = ast.unparse(value)
    return bindings


def _is_windows_gated(node: ast.FunctionDef, bindings: dict[str, str]) -> bool:
    """Whether ``node`` carries a decorator that skips it off Windows.

    Args:
        node: The test function.
        bindings: Module-level names, from :func:`_module_bindings`.

    Returns:
        True when some decorator, resolved through ``bindings``, is a skip
        conditioned on the platform.
    """
    for decorator in node.decorator_list:
        text = ast.unparse(decorator)
        if isinstance(decorator, ast.Name):
            text = bindings.get(decorator.id, text)
        if all(term in text for term in CURDIR_GATE_TERMS):
            return True
    return False


def _ungated_curdir_arms() -> list[str]:
    """Every test in ``tests/`` that grades the search without a platform gate.

    Returns:
        Sorted ``path::name`` for each ungated arm. Repo-relative, so nothing
        here can carry the account name (non-negotiable 3).
    """
    tests_dir = REPO_ROOT / "tests"
    offenders: list[str] = []
    for source in sorted(tests_dir.rglob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        bindings = _module_bindings(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            body = ast.unparse(node)
            if not any(term in body for term in CURDIR_ARM_TERMS):
                continue
            if _is_windows_gated(node, bindings):
                continue
            relative = source.relative_to(REPO_ROOT).as_posix()
            offenders.append(f"{relative}::{node.name}")
    return sorted(offenders)


def test_every_current_directory_arm_is_skipped_off_windows() -> None:
    """CS-910 - an arm for a Windows mechanism may not run where it is absent.

    THIS EXISTS BECAUSE THE POPULATION WAS THREE AND ONE OF THEM ESCAPED. Two
    of the runtime arms carry a platform skip. The third carried a LIVENESS
    GATE INSTEAD, written so that it answered True on any non-Windows host -
    which reports the mechanism live exactly where it does not exist. The arm
    then reached a control that cannot pass off Windows and failed the lane on
    a host where there was never anything to grade.

    SO THE GUARD IS STRUCTURAL RATHER THAN BEHAVIOURAL, and it has to be: the
    development machine is Windows, where the defective arm passes. Nothing
    that runs here could have caught it. What a scan of the SHAPE catches on
    every platform is the missing gate itself.

    THE ASSERTION BINDS A LIST OF REPO-RELATIVE NAMES. pytest renders the
    asserted expression independently of the message, and a temporary path on
    Windows carries the account name.
    """
    ungated = _ungated_curdir_arms()

    assert ungated == [], (
        f"{len(ungated)} arm(s) grade the current-directory executable search with no"
        f" skip off Windows, so they run where the mechanism does not exist: {ungated}"
    )


def test_the_current_directory_arm_population_is_not_empty() -> None:
    """CS-910 - the guard above must be measuring something.

    A SCAN THAT MATCHES NOTHING PASSES FOREVER. If the terms drift out of the
    suite - renamed, reworded, or reached by some spelling the scan does not
    know - :func:`_ungated_curdir_arms` returns an empty list and reports a
    clean population over zero files. That is the unrun-gate failure class
    (CONVENTIONS.md section 7.2), so the population is asserted non-empty here
    rather than assumed by the guard.
    """
    tests_dir = REPO_ROOT / "tests"
    matched = 0
    for source in sorted(tests_dir.rglob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            if any(term in ast.unparse(node) for term in CURDIR_ARM_TERMS):
                matched += 1

    assert matched > 0, (
        "no test in the suite mentions the current-directory search, so the guard above"
        " is scanning an empty population and would pass whatever the tree held"
    )
