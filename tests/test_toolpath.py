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
    describe,
    exemption_budget_problems,
    findings,
    graded_python_files,
    scan_repository,
    scan_source,
    stale_exemptions,
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
        f"{path}:{line} {callee} in {function}()"
        for (path, function, callee, line), reason in EXEMPTIONS.items()
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
    frozen_text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="ascii")
    outside = sorted({path for (path, _f, _c, _l) in EXEMPTIONS if path not in frozen_text})

    assert outside == [], (
        f"{len(outside)} exemption(s) name a file CLAUDE.md does not freeze, so the"
        f" table's stated reason does not apply to them: {outside}"
    )


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
    :data:`toolpath_guard.OS_SPAWNERS` table would be declared and never
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
