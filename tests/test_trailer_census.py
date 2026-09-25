"""CS-1183 - the trailer-shaped census, graded over throwaway repositories only.

THE DEFINITION UNDER TEST IS NOT RESTATED HERE. It is owned by the paragraph
headed THE TRAILER-SHAPED CENSUS in ``docs/item_notes/phase7.md``; every arm
below is one clause of it, read back through ``tools/trailer_census.py``.

EVERY REPOSITORY IS BUILT IN ``tmp_path`` WITH ``git commit-tree``. That
plumbing runs no hook and applies no message cleanup, so the message bytes an
arm writes are the bytes the census reads - ``git commit`` would strip trailing
whitespace and collapse blank lines, which would make the strippability arms
grade git's cleanup rather than the census. The operator's own git
configuration is aimed at paths that do not exist, so a global gpgsign or
template cannot answer for git here.

PROSE THAT NAMES THE TRAILER MUST NOT COUNT, and that is the point of the
census rather than a detail of it: ``docs/GATED.md`` CS-G03 measured a plain
substring search returning one more than the trailer-shaped match, the extra
being a commit message discussing the rule. The colon is what separates them.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
CENSUS_SOURCE: Final = REPO_ROOT / "tools" / "trailer_census.py"

#: Seconds one git plumbing call or one CLI run may take in these arms.
TIMEOUT: Final = 60

#: A marker placed in message bodies so an arm can prove the CLI never prints a
#: message byte. It matches no trailer shape.
BODY_MARKER: Final = "flip-census-body-marker-7c1"

#: The trailer value every planted line carries. Synthetic, and an address in
#: the reserved ``.invalid`` domain.
VALUE: Final = "Someone <someone@example.invalid>"


def _load() -> ModuleType:
    """Import ``tools/trailer_census.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_trailer_census", CENSUS_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {CENSUS_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


census = _load()


@dataclass
class Repo:
    """A throwaway repository and the environment its git runs under."""

    path: Path
    env: dict[str, str]
    empty_tree: str = ""
    shas: list[str] = field(default_factory=list)

    def git(self, *args: str, data: bytes | None = None) -> str:
        """Run one git command in the repository and return its stripped stdout."""
        completed = subprocess.run(
            ["git", *args],
            cwd=self.path,
            env=self.env,
            input=data,
            capture_output=True,
            timeout=TIMEOUT,
            check=True,
        )
        return completed.stdout.decode("ascii").strip()

    def commit(self, message: bytes, *parents: str) -> str:
        """Write one commit carrying exactly ``message`` and point main at it."""
        argv = ["commit-tree", self.empty_tree]
        for parent in parents:
            argv += ["-p", parent]
        sha = self.git(*argv, data=message)
        self.git("update-ref", "refs/heads/main", sha)
        self.shas.append(sha)
        return sha


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    """An empty repository with a synthetic identity and no inherited config."""
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = "Synthetic"
        env[f"GIT_{role}_EMAIL"] = "synthetic@example.invalid"
    path = tmp_path / "repo"
    path.mkdir()
    made = Repo(path, env)
    made.git("init", "-q")
    made.empty_tree = made.git("write-tree")
    return made


def cli(repo: Repo, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the census CLI in a fresh interpreter against ``repo``."""
    return subprocess.run(
        [sys.executable, "-B", str(CENSUS_SOURCE), "--repo", str(repo.path), *args],
        env=repo.env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def message(*lines: str) -> bytes:
    """Join ``lines`` with LF and terminate with one LF."""
    return ("\n".join(lines) + "\n").encode("ascii")


# --- the predicate: one clause of the definition per arm ----------------------


@pytest.mark.parametrize(
    "line",
    [
        "Co-authored-by: " + VALUE,
        "co-authored-by: " + VALUE,
        "CO-AUTHORED-BY: " + VALUE,
        "Co-Authored-By: " + VALUE,
        "Co-authored-by : " + VALUE,
        "Co-authored-by\t: " + VALUE,
        "Co-authored-by:" + VALUE,
    ],
    ids=["mixed", "lower", "upper", "title", "space-before-colon", "tab-before-colon", "no-gap"],
)
def test_every_trailer_shaped_line_counts(line: str) -> None:
    """Column zero, a colon, and the trimmed token folds to the key."""
    assert census.is_trailer_line(line.encode("ascii"))


@pytest.mark.parametrize(
    "line",
    [
        " Co-authored-by: " + VALUE,
        "\tCo-authored-by: " + VALUE,
        "The Co-authored-by trailer is refused by the gate.",
        "Co-authored-by " + VALUE,
        "see Co-authored-by: in the gate",
        "Co-authored-byx: " + VALUE,
        "Co-authored-by",
        "",
    ],
    ids=[
        "indented",
        "tab-indented",
        "prose",
        "no-colon",
        "mid-sentence",
        "longer-key",
        "bare-key",
        "blank",
    ],
)
def test_prose_and_indented_lines_do_not_count(line: str) -> None:
    """Prose that NAMES the trailer is separated from a trailer by the colon."""
    assert not census.is_trailer_line(line.encode("ascii"))


# --- the walk over a real repository ------------------------------------------


def test_the_census_counts_lines_and_commits_over_a_real_walk(repo: Repo) -> None:
    """Two trailer commits among clean ones and one that only names the trailer."""
    root = repo.commit(message("CS-1 - root", "", BODY_MARKER))
    first = repo.commit(message("CS-2 - one", "", "body", "", "Co-authored-by: " + VALUE), root)
    prose = repo.commit(message("CS-3 - names the Co-authored-by trailer in prose"), first)
    second = repo.commit(
        message("CS-4 - two", "", "Co-authored-by: " + VALUE, "co-authored-by : " + VALUE), prose
    )

    walked = census.walk(repo.path, "main")

    assert len(walked) == len(repo.shas)
    hits = {entry.sha: len(entry.hit_lines) for entry in walked if entry.hit_lines}
    assert hits == {first: 1, second: 2}


def test_a_trailer_in_the_subject_line_counts(repo: Repo) -> None:
    """The definition walks every line of the message, the subject included."""
    sha = repo.commit(message("Co-authored-by: " + VALUE))

    walked = census.walk(repo.path, "main")

    assert [entry.sha for entry in walked if entry.hit_lines] == [sha]


def test_a_range_walks_only_its_own_side(repo: Repo) -> None:
    """``A..B`` excludes A's ancestry, so an old trailer outside it is not counted."""
    old = repo.commit(message("CS-1 - old", "", "Co-authored-by: " + VALUE))
    new = repo.commit(message("CS-2 - new", "", "clean"), old)

    walked = census.walk(repo.path, f"{old}..{new}")

    assert [entry.sha for entry in walked] == [new]
    assert not walked[0].hit_lines


# --- strippability: the S1 seventh-axis clause --------------------------------


def test_a_final_trailer_after_a_blank_line_is_strippable(repo: Repo) -> None:
    """``subject LF LF body LF LF trailer LF`` is exactly what S7a's strip removes."""
    repo.commit(message("CS-1 - s", "", "body", "", "Co-authored-by: " + VALUE))

    (entry,) = census.walk(repo.path, "main")

    assert entry.strippable


def test_a_final_trailer_without_a_final_lf_is_strippable(repo: Repo) -> None:
    """The strip removes the same two lines whether or not the trailer ends in LF."""
    repo.commit(("CS-1 - s\n\nbody\n\nCo-authored-by: " + VALUE).encode("ascii"))

    (entry,) = census.walk(repo.path, "main")

    assert entry.strippable


@pytest.mark.parametrize(
    "body",
    [
        ("CS-1 - s", "", "Co-authored-by: " + VALUE, "", "trailing prose"),
        ("CS-1 - s", "", "body", "Co-authored-by: " + VALUE),
        ("CS-1 - s", "", "Co-authored-by: " + VALUE, "", "Co-authored-by: " + VALUE),
        ("CS-1 - s", "", "body", "", "Co-authored-by: " + VALUE, ""),
        ("Co-authored-by: " + VALUE,),
    ],
    ids=["not-final", "no-blank-before", "two-trailers", "blank-after", "subject-only"],
)
def test_a_trailer_the_strip_would_leave_behind_is_not_strippable(
    repo: Repo, body: tuple[str, ...]
) -> None:
    """Every shape S7a's two-line removal cannot express is refused."""
    repo.commit(message(*body))

    (entry,) = census.walk(repo.path, "main")

    assert entry.hit_lines
    assert not entry.strippable


def test_a_trailer_on_a_merge_commit_is_not_strippable(repo: Repo) -> None:
    """The S1 axis names a NON-merge commit's message, so a merge is refused."""
    left = repo.commit(message("CS-1 - left"))
    right = repo.commit(message("CS-2 - right"))
    repo.commit(message("CS-3 - merge", "", "Co-authored-by: " + VALUE), left, right)

    merge = next(entry for entry in census.walk(repo.path, "main") if entry.hit_lines)

    assert merge.parents == len((left, right))
    assert not merge.strippable


# --- the CLI contract ---------------------------------------------------------


def test_the_cli_exits_zero_and_prints_counts_on_a_clean_walk(repo: Repo) -> None:
    """Exit 0, the walked count printed, and nothing else claimed."""
    repo.commit(message("CS-1 - clean", "", BODY_MARKER))

    completed = cli(repo, "main")

    assert completed.returncode == census.EXIT_CLEAN, completed.stdout + completed.stderr
    assert "commits walked 1" in completed.stdout
    assert "trailer lines 0" in completed.stdout


def test_the_cli_exits_one_and_names_shas_never_message_bytes(repo: Repo) -> None:
    """The offending commit's SHA is printed and no byte of its message is."""
    sha = repo.commit(message("CS-1 - " + BODY_MARKER, "", "Co-authored-by: " + VALUE))

    completed = cli(repo, "main")
    output = completed.stdout + completed.stderr

    assert completed.returncode == census.EXIT_HITS, output
    assert sha in completed.stdout
    leaked = BODY_MARKER in output or "example.invalid" in output
    assert not leaked, "the census printed a message byte"


@pytest.mark.parametrize(
    "rev",
    ["refs/heads/absent", "--all", ""],
    ids=["unresolvable", "option-shaped", "empty"],
)
def test_the_cli_exits_two_when_it_cannot_run(repo: Repo, rev: str) -> None:
    """An unresolvable rev, an option smuggled in as one, or nothing, is not a clean census."""
    repo.commit(message("CS-1 - clean"))

    completed = cli(repo, "--", rev) if rev.startswith("-") else cli(repo, rev)

    assert completed.returncode == census.EXIT_COULD_NOT_RUN, completed.stdout + completed.stderr


def test_an_empty_walk_exits_two_unless_allowed(repo: Repo) -> None:
    """A census of nothing satisfies every zero, so it is refused by default."""
    sha = repo.commit(message("CS-1 - only"))

    refused = cli(repo, f"{sha}..{sha}")
    allowed = cli(repo, "--allow-empty", f"{sha}..{sha}")

    assert refused.returncode == census.EXIT_COULD_NOT_RUN, refused.stdout + refused.stderr
    assert allowed.returncode == census.EXIT_CLEAN, allowed.stdout + allowed.stderr
    assert "commits walked 0" in allowed.stdout


def test_the_cli_exits_two_outside_a_repository(tmp_path: Path) -> None:
    """A directory that is not a repository could not be walked at all."""
    plain = tmp_path / "plain"
    plain.mkdir()

    completed = subprocess.run(
        [sys.executable, "-B", str(CENSUS_SOURCE), "--repo", str(plain), "HEAD"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )

    assert completed.returncode == census.EXIT_COULD_NOT_RUN, completed.stdout + completed.stderr
