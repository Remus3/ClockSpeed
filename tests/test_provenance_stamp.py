"""CS-1165 slice S2 - the provenance stamp tool refuses every unclassified write.

WHAT THIS GRADES. ``tools/provenance_stamp.py`` is the ERGONOMIC writer of
``tools/provenance.tsv``, the whole-population provenance manifest. It is not
the oracle - the ``test_provenance_manifest`` arm re-derives every rule from
the manifest itself, so a hand-edited TSV is graded there. What this module
proves is that the tool cannot be used to launder a file: every refusal it
promises fires, a refusal writes nothing and leaves nothing behind, and the
only multi-path writer (``bootstrap``) refuses to overwrite a manifest that
exists, so there is no blind "regenerate everything" route through it.

EVERY REPOSITORY HERE IS SYNTHETIC. Each test builds a throwaway git repository
under ``tmp_path`` holding a hand-authored register, one hand-authored
"vendored" file and a few authored ones. No real game data, no save and no
sibling tree is read. The child environment is scrubbed through
``tests/git_env.py`` so a pre-push ``GIT_DIR`` cannot point a throwaway
``git init`` at the real repository.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from tests import git_env

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_SOURCE = REPO_ROOT / "tools" / "provenance_stamp.py"

#: The subcommands the tool may offer. Pinned here so a bulk "stamp every
#: unlisted file" mode cannot be added without this arm going red.
EXPECTED_SUBCOMMANDS = frozenset({"add", "mv", "rm", "check", "bootstrap"})

GIT_TIMEOUT_SECONDS = 60

#: The tool's exit codes: 1 is a check that found something, 2 a refusal.
FOUND = 1
REFUSED = 2
ASCII_LIMIT = 0x80

#: The near-duplicate constants, pinned from the plan section 2.4 so the S1 arm
#: and this tool cannot drift apart silently.
PLAN_THRESHOLD = Fraction(1, 2)
PLAN_MIN_LINE_LENGTH = 20

#: A vendored file body: enough distinct long lines that the overlap metric has
#: a real denominator. Synthetic, authored here.
VENDORED_LINES = [f"def vendored_function_number_{index:02d}(arg): pass" for index in range(10)]
VENDORED_BYTES = ("\n".join(["# upstream header, branded", *VENDORED_LINES]) + "\n").encode()

#: The backtick is spliced in rather than typed, so the citation guards do not
#: read these synthetic fixture paths as citations of files in this tree.
TICK = "`"
REGISTER_TEXT = f"""# Third-party register

### Vendored files

| File | Upstream | Verdict |
|---|---|---|
| {TICK}lib/vendored.py{TICK} | a synthetic upstream | CLEARED |

### Considered

| Item | Verdict |
|---|---|
| {TICK}lib/considered.py{TICK} | not vendored |
"""

#: Every item id a test cites must be spelled in one of these two, as the arm
#: requires. CS-0099 is deliberately in NEITHER.
ROADMAP_TEXT = "# Roadmap\n\n- CS-5 open\n- CS-7 open\n- CS-8 open\n- CS-9 open\n"
LEDGER_TEXT = "# Ledger\n\n- CS-1 closed\n- CS-42 closed\n- CS-0042 closed\n- CS-1165 closed\n"


def _load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cs1165_provenance_stamp", TOOL_SOURCE)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return _load_tool()


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
        env=git_env.scrub(dict(os.environ)),
    )
    assert completed.returncode == 0, f"git {args[0]} failed: {completed.stderr.strip()}"
    return completed.stdout


def _commit(root: Path, subject: str) -> None:
    _git(
        root,
        "-c",
        "user.name=fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.hooksPath=",
        "commit",
        "-q",
        "-m",
        subject,
    )


def _write(root: Path, relative: str, data: bytes) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed synthetic repository with a register and a vendored file."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _write(root, "THIRD_PARTY.md", REGISTER_TEXT.encode())
    _write(root, "lib/vendored.py", VENDORED_BYTES)
    _write(root, "ROADMAP.md", ROADMAP_TEXT.encode())
    _write(root, "docs/LEDGER.md", LEDGER_TEXT.encode())
    _git(root, "add", "THIRD_PARTY.md", "lib/vendored.py", "ROADMAP.md", "docs/LEDGER.md")
    _commit(root, "Phase 0 wave - seed the tree")
    _write(root, "lib/authored.py", b"print('authored here, nothing shared at all')\n")
    _write(root, "Zeta.md", b"# upper-case first byte sorts before lower-case\n")
    _git(root, "add", "lib/authored.py", "Zeta.md")
    _commit(root, "CS-0042 - add the authored module")
    return root


def _run(tool: ModuleType, root: Path, *args: str) -> int:
    code: int = tool.main(["--root", str(root), *args])
    return code


def _manifest(root: Path) -> Path:
    return root / "tools" / "provenance.tsv"


def _rows(root: Path) -> list[list[str]]:
    lines = _manifest(root).read_bytes().decode("ascii").split("\n")
    assert lines[-1] == "", "the manifest does not end with a single LF"
    return [line.split("\t") for line in lines[1:-1]]


def _seed_manifest(root: Path, rows: list[tuple[str, str, str, str]]) -> bytes:
    """Write a well-formed manifest by hand, return its bytes."""
    body = "".join("\t".join(row) + "\n" for row in sorted(rows, key=lambda r: r[0].encode()))
    data = ("# hand-seeded manifest for a test\n" + body).encode("ascii")
    _write(root, "tools/provenance.tsv", data)
    return data


def _leftovers(root: Path) -> list[str]:
    tools_dir = root / "tools"
    if not tools_dir.is_dir():
        return []
    return sorted(p.name for p in tools_dir.iterdir() if p.name != "provenance.tsv")


# --- the add path ---------------------------------------------------------


def test_add_stamps_a_tracked_authored_file_sorted_lf_ascii(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    assert _run(tool, repo, "add", "Zeta.md", "--class", "authored", "--item", "CS-8") == 0
    raw = _manifest(repo).read_bytes()
    assert b"\r" not in raw
    assert all(byte < ASCII_LIMIT for byte in raw)
    assert raw.startswith(b"#")
    assert _rows(repo) == [
        ["Zeta.md", "authored", "CS-8", "stamped"],
        ["lib/authored.py", "authored", "CS-7", "stamped"],
    ]
    assert _leftovers(repo) == []


def test_add_accepts_a_staged_but_uncommitted_file(tool: ModuleType, repo: Path) -> None:
    _write(repo, "lib/staged.py", b"x = 'staged only, never committed'\n")
    _git(repo, "add", "lib/staged.py")
    assert _run(tool, repo, "add", "lib/staged.py", "--class", "authored", "--item", "CS-9") == 0
    assert ["lib/staged.py", "authored", "CS-9", "stamped"] in _rows(repo)


def test_add_accepts_an_untracked_unignored_file(tool: ModuleType, repo: Path) -> None:
    # The population is the arm's: tracked PLUS untracked-not-ignored, because a
    # plain copy with no git add is exactly the acceptance mutation.
    _write(repo, "lib/loose.py", b"x = 'copied in, never added'\n")
    assert _run(tool, repo, "add", "lib/loose.py", "--class", "authored", "--item", "CS-9") == 0
    assert ["lib/loose.py", "authored", "CS-9", "stamped"] in _rows(repo)


def test_add_refuses_an_ignored_file_and_writes_nothing(tool: ModuleType, repo: Path) -> None:
    _stage(repo, ".gitignore", b"scratch/\n")
    _write(repo, "scratch/loose.py", b"x = 1\n")
    assert (
        _run(tool, repo, "add", "scratch/loose.py", "--class", "authored", "--item", "CS-9")
        == REFUSED
    )
    assert not _manifest(repo).exists()
    assert _leftovers(repo) == []


def test_add_refuses_a_path_that_does_not_exist(tool: ModuleType, repo: Path) -> None:
    assert (
        _run(tool, repo, "add", "lib/absent.py", "--class", "authored", "--item", "CS-9") == REFUSED
    )
    assert not _manifest(repo).exists()


def test_add_refuses_a_path_already_listed(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    before = _manifest(repo).read_bytes()
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-8")
        == REFUSED
    )
    assert _manifest(repo).read_bytes() == before


def test_add_without_a_class_is_refused_there_is_no_default(tool: ModuleType, repo: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        _run(tool, repo, "add", "lib/authored.py", "--item", "CS-7")
    assert raised.value.code == REFUSED
    assert not _manifest(repo).exists()


def test_add_with_an_unknown_class_is_refused(tool: ModuleType, repo: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        _run(tool, repo, "add", "lib/authored.py", "--class", "mine", "--item", "CS-7")
    assert raised.value.code == REFUSED
    assert not _manifest(repo).exists()


def test_add_without_an_item_is_refused(tool: ModuleType, repo: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored")
    assert raised.value.code == REFUSED
    assert not _manifest(repo).exists()


@pytest.mark.parametrize("item", ["1165", "CS-", "cs-1165", "CS-12a", "CS-12 ", "CS-\t1", "XS-1"])
def test_add_refuses_an_item_that_is_not_a_cs_id(tool: ModuleType, repo: Path, item: str) -> None:
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", item) == REFUSED
    )
    assert not _manifest(repo).exists()


def test_add_vendored_needs_a_register_row(tool: ModuleType, repo: Path) -> None:
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "vendored", "--item", "CS-7")
        == REFUSED
    )
    assert not _manifest(repo).exists()


def test_add_vendored_with_a_register_row_is_accepted(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/vendored.py", "--class", "vendored", "--item", "CS-5") == 0
    assert _rows(repo) == [["lib/vendored.py", "vendored", "CS-5", "stamped"]]


def test_the_considered_table_is_not_read_as_vendored(tool: ModuleType, repo: Path) -> None:
    _write(repo, "lib/considered.py", b"x = 'considered, never vendored'\n")
    _git(repo, "add", "lib/considered.py")
    assert (
        _run(tool, repo, "add", "lib/considered.py", "--class", "vendored", "--item", "CS-5")
        == REFUSED
    )


def test_add_authored_refuses_the_register_path_itself(tool: ModuleType, repo: Path) -> None:
    assert (
        _run(tool, repo, "add", "lib/vendored.py", "--class", "authored", "--item", "CS-5")
        == REFUSED
    )
    assert not _manifest(repo).exists()


def _stage(repo: Path, relative: str, data: bytes) -> None:
    _write(repo, relative, data)
    _git(repo, "add", relative)


def test_add_authored_refuses_a_byte_identical_vendored_copy(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _stage(repo, "lib/fresh.py", VENDORED_BYTES)
    capsys.readouterr()
    assert (
        _run(tool, repo, "add", "lib/fresh.py", "--class", "authored", "--item", "CS-1165")
        == REFUSED
    )
    said = capsys.readouterr()
    text = said.out + said.err
    assert "lib/fresh.py" in text
    assert "lib/vendored.py" in text
    assert "vendored_function_number" not in text, "the refusal echoed file bytes"
    assert not _manifest(repo).exists()
    assert _leftovers(repo) == []


def test_add_authored_refuses_a_crlf_copy_of_a_vendored_file(tool: ModuleType, repo: Path) -> None:
    _stage(repo, "lib/fresh.py", VENDORED_BYTES.replace(b"\n", b"\r\n"))
    assert (
        _run(tool, repo, "add", "lib/fresh.py", "--class", "authored", "--item", "CS-1165")
        == REFUSED
    )


def test_add_authored_refuses_a_rebranded_near_duplicate(tool: ModuleType, repo: Path) -> None:
    body = ["# a new header that names nobody", *VENDORED_LINES[:6], "x = 'a local addition line'"]
    _stage(repo, "lib/fresh.py", ("\n".join(body) + "\n").encode())
    assert (
        _run(tool, repo, "add", "lib/fresh.py", "--class", "authored", "--item", "CS-1165")
        == REFUSED
    )
    assert not _manifest(repo).exists()


def test_add_authored_accepts_overlap_just_below_the_threshold(
    tool: ModuleType, repo: Path
) -> None:
    # Control against a vacuously-refusing tool: four of ten long lines is 0.4.
    body = ["# authored", *VENDORED_LINES[:4], "y = 'the rest of this file is new work'"]
    _stage(repo, "lib/fresh.py", ("\n".join(body) + "\n").encode())
    assert _run(tool, repo, "add", "lib/fresh.py", "--class", "authored", "--item", "CS-1165") == 0


def test_overlap_score_is_exact_and_uses_the_vendored_denominator(tool: ModuleType) -> None:
    # The branded header is itself a long line, so the denominator is eleven.
    five = ("\n".join(["short", *VENDORED_LINES[:5]]) + "\n").encode()
    assert tool.overlap_score(five, VENDORED_BYTES) == Fraction(5, 11)
    body = ("\n".join(VENDORED_LINES) + "\n").encode()
    half = ("\n".join(["short", *VENDORED_LINES[:5]]) + "\n").encode()
    assert tool.overlap_score(half, body) == Fraction(1, 2)
    # Repeats and surrounding whitespace do not inflate the share.
    padded = ("\n".join([f"   {VENDORED_LINES[0]}  ", VENDORED_LINES[0]]) + "\n").encode()
    assert tool.overlap_score(padded, body) == Fraction(1, 10)
    assert tool.overlap_score(VENDORED_BYTES, VENDORED_BYTES) == Fraction(1)
    assert tool.overlap_score(b"nothing\n", VENDORED_BYTES) == Fraction(0)
    # Lines under the length floor never count, so a file of short lines scores zero.
    assert tool.overlap_score(b"a\nb\n", b"a\nb\n") == Fraction(0)
    # Undecodable bytes fall back to byte equality only.
    assert tool.overlap_score(b"\xff\xfe" + VENDORED_BYTES, VENDORED_BYTES) == Fraction(0)
    assert tool.NEAR_DUPLICATE_THRESHOLD == PLAN_THRESHOLD
    assert tool.MIN_LINE_LENGTH == PLAN_MIN_LINE_LENGTH
    # The floor is inclusive: a line of exactly the floor counts, one shorter never does.
    at_floor, under = "x" * PLAN_MIN_LINE_LENGTH, "y" * (PLAN_MIN_LINE_LENGTH - 1)
    pair = (at_floor + "\n" + under + "\n").encode()
    assert tool.overlap_score(pair, pair) == Fraction(1)
    assert tool.overlap_score((under + "\n").encode(), pair) == Fraction(0)


@pytest.mark.parametrize(
    "path",
    ["/abs/lib/authored.py", "C:/x/lib/authored.py", "../repo/lib/authored.py", "lib/../Zeta.md"],
)
def test_add_refuses_a_path_that_is_not_plain_repo_relative(
    tool: ModuleType, repo: Path, path: str
) -> None:
    assert _run(tool, repo, "add", path, "--class", "authored", "--item", "CS-7") == REFUSED
    assert not _manifest(repo).exists()


def test_add_refuses_a_path_spelling_the_home_directory(
    tool: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_named = "Users/fixtureperson/notes.md"
    _stage(repo, home_named, b"a file whose repo path spells a home directory\n")
    monkeypatch.setattr(tool, "_home_markers", lambda: ("users/fixtureperson",))
    assert _run(tool, repo, "add", home_named, "--class", "authored", "--item", "CS-7") == REFUSED
    assert not _manifest(repo).exists()


def test_a_backslash_spelling_is_normalised_to_posix(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib\\authored.py", "--class", "authored", "--item", "CS-7") == 0
    assert _rows(repo) == [["lib/authored.py", "authored", "CS-7", "stamped"]]


def test_add_refuses_to_rewrite_a_malformed_manifest(tool: ModuleType, repo: Path) -> None:
    broken = b"# header\nlib/vendored.py\tvendored\tCS-5\n"
    _write(repo, "tools/provenance.tsv", broken)
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7")
        == REFUSED
    )
    assert _manifest(repo).read_bytes() == broken


@pytest.mark.parametrize(
    "row",
    [
        "lib/vendored.py\tmine\tCS-5\tstamped",
        "lib/vendored.py\tvendored\t5\tstamped",
        "lib/vendored.py\tvendored\tCS-5\tguessed",
    ],
)
def test_a_manifest_row_with_a_bad_field_is_malformed(
    tool: ModuleType, repo: Path, row: str
) -> None:
    broken = f"# header\n{row}\n".encode()
    _write(repo, "tools/provenance.tsv", broken)
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7")
        == REFUSED
    )
    assert _manifest(repo).read_bytes() == broken


def test_an_unsorted_manifest_is_malformed(tool: ModuleType, repo: Path) -> None:
    broken = b"# h\nlib/b.py\tauthored\tCS-1\tstamped\nlib/a.py\tauthored\tCS-1\tstamped\n"
    _write(repo, "tools/provenance.tsv", broken)
    assert _run(tool, repo, "check") == REFUSED


def test_a_crlf_manifest_is_malformed(tool: ModuleType, repo: Path) -> None:
    broken = b"# h\r\nlib/vendored.py\tvendored\tCS-5\tstamped\r\n"
    _write(repo, "tools/provenance.tsv", broken)
    assert _run(tool, repo, "check") == REFUSED


# --- atomicity ------------------------------------------------------------


def test_a_failed_rename_leaves_the_manifest_and_no_temp_file(
    tool: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    before = _manifest(repo).read_bytes()

    def refuse(_self: object, _target: object) -> None:
        raise PermissionError(13, "denied")

    monkeypatch.setattr(tool.Path, "replace", refuse)
    monkeypatch.setattr(tool.time, "sleep", lambda _seconds: None)
    with pytest.raises(PermissionError):
        _run(tool, repo, "add", "Zeta.md", "--class", "authored", "--item", "CS-8")
    assert _manifest(repo).read_bytes() == before
    assert _leftovers(repo) == []


# --- mv and rm ------------------------------------------------------------


def test_mv_keeps_class_and_item_and_restamps(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    _git(repo, "mv", "lib/authored.py", "lib/moved.py")
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/moved.py") == 0
    assert _rows(repo) == [["lib/moved.py", "authored", "CS-7", "stamped"]]


def test_mv_refuses_while_the_old_path_is_still_tracked(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    _stage(repo, "lib/copy.py", b"print('authored here, nothing shared at all')\n")
    before = _manifest(repo).read_bytes()
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/copy.py") == REFUSED
    assert _manifest(repo).read_bytes() == before


def test_mv_refuses_while_the_old_path_is_still_on_disk_untracked(
    tool: ModuleType, repo: Path
) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    _git(repo, "rm", "-q", "--cached", "lib/authored.py")
    _stage(repo, "lib/moved.py", b"x = 'the destination exists'\n")
    before = _manifest(repo).read_bytes()
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/moved.py") == REFUSED
    assert _manifest(repo).read_bytes() == before


def test_mv_refuses_an_absent_destination(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    _git(repo, "rm", "-q", "lib/authored.py")
    before = _manifest(repo).read_bytes()
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/nowhere.py") == REFUSED
    assert _manifest(repo).read_bytes() == before


def test_mv_refuses_an_unlisted_source(tool: ModuleType, repo: Path) -> None:
    _seed_manifest(repo, [("Zeta.md", "authored", "CS-8", "stamped")])
    _git(repo, "mv", "lib/authored.py", "lib/moved.py")
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/moved.py") == REFUSED


def test_mv_of_an_authored_row_onto_vendored_bytes_is_refused(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    _git(repo, "mv", "lib/authored.py", "lib/moved.py")
    _write(repo, "lib/moved.py", VENDORED_BYTES)
    _git(repo, "add", "lib/moved.py")
    before = _manifest(repo).read_bytes()
    assert _run(tool, repo, "mv", "lib/authored.py", "lib/moved.py") == REFUSED
    assert _manifest(repo).read_bytes() == before


def test_mv_of_a_vendored_row_to_an_unregistered_path_is_refused(
    tool: ModuleType, repo: Path
) -> None:
    assert _run(tool, repo, "add", "lib/vendored.py", "--class", "vendored", "--item", "CS-5") == 0
    _git(repo, "mv", "lib/vendored.py", "lib/elsewhere.py")
    assert _run(tool, repo, "mv", "lib/vendored.py", "lib/elsewhere.py") == REFUSED


def test_rm_refuses_while_tracked_and_removes_once_untracked(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-7") == 0
    assert _run(tool, repo, "rm", "lib/authored.py") == REFUSED
    _git(repo, "rm", "-q", "lib/authored.py")
    assert _run(tool, repo, "rm", "lib/authored.py") == 0
    assert _rows(repo) == []


def test_rm_refuses_an_unlisted_path(tool: ModuleType, repo: Path) -> None:
    _seed_manifest(repo, [("Zeta.md", "authored", "CS-8", "stamped")])
    assert _run(tool, repo, "rm", "lib/gone.py") == REFUSED


# --- check ----------------------------------------------------------------


def _full_rows() -> list[tuple[str, str, str, str]]:
    return [
        ("ROADMAP.md", "authored", "CS-1", "first-add:root"),
        ("THIRD_PARTY.md", "authored", "CS-1", "first-add:root"),
        ("Zeta.md", "authored", "CS-42", "first-add:CS-42"),
        ("docs/LEDGER.md", "authored", "CS-1", "first-add:root"),
        ("lib/authored.py", "authored", "CS-42", "first-add:CS-42"),
        ("lib/vendored.py", "vendored", "CS-1", "first-add:root"),
        ("tools/provenance.tsv", "authored", "CS-1165", "stamped"),
    ]


def test_check_is_clean_on_a_complete_manifest(tool: ModuleType, repo: Path) -> None:
    _seed_manifest(repo, _full_rows())
    _git(repo, "add", "tools/provenance.tsv")
    assert _run(tool, repo, "check") == 0


def test_check_names_an_unlisted_tracked_path(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed_manifest(repo, _full_rows())
    _stage(repo, "lib/new.py", VENDORED_BYTES)
    _git(repo, "add", "tools/provenance.tsv")
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    assert "lib/new.py" in capsys.readouterr().out


def test_check_names_a_stale_row(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed_manifest(repo, [*_full_rows(), ("lib/gone.py", "authored", "CS-7", "stamped")])
    _git(repo, "add", "tools/provenance.tsv")
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    assert "lib/gone.py" in capsys.readouterr().out


def test_check_names_a_vendored_row_the_register_does_not_carry(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = [
        r if r[0] != "Zeta.md" else ("Zeta.md", "vendored", "CS-42", "stamped")
        for r in _full_rows()
    ]
    _seed_manifest(repo, rows)
    _git(repo, "add", "tools/provenance.tsv")
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    assert "Zeta.md" in capsys.readouterr().out


def test_check_names_a_register_row_listed_as_authored(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = [
        r if r[0] != "lib/vendored.py" else ("lib/vendored.py", "authored", "CS-1", "stamped")
        for r in _full_rows()
    ]
    _seed_manifest(repo, rows)
    _git(repo, "add", "tools/provenance.tsv")
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    assert "lib/vendored.py" in capsys.readouterr().out


def test_check_names_an_authored_near_duplicate(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _stage(repo, "lib/fresh.py", VENDORED_BYTES)
    _seed_manifest(repo, [*_full_rows(), ("lib/fresh.py", "authored", "CS-1165", "stamped")])
    _git(repo, "add", "tools/provenance.tsv")
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    out = capsys.readouterr().out
    assert "lib/fresh.py" in out
    assert "vendored_function_number" not in out


def test_check_on_a_missing_manifest_names_it_and_the_tool(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    said = capsys.readouterr()
    text = said.out + said.err
    assert "tools/provenance.tsv" in text
    assert "provenance_stamp.py" in text


# --- bootstrap ------------------------------------------------------------


def test_bootstrap_seeds_every_tracked_path_from_its_first_add(
    tool: ModuleType, repo: Path
) -> None:
    assert _run(tool, repo, "bootstrap") == 0
    assert _rows(repo) == [
        ["ROADMAP.md", "authored", "CS-1165", "first-add:root"],
        ["THIRD_PARTY.md", "authored", "CS-1165", "first-add:root"],
        ["Zeta.md", "authored", "CS-0042", "first-add:CS-0042"],
        ["docs/LEDGER.md", "authored", "CS-1165", "first-add:root"],
        ["lib/authored.py", "authored", "CS-0042", "first-add:CS-0042"],
        ["lib/vendored.py", "vendored", "CS-1165", "first-add:root"],
        ["tools/provenance.tsv", "authored", "CS-1165", "stamped"],
    ]
    assert _leftovers(repo) == []
    _git(repo, "add", "tools/provenance.tsv")
    assert _run(tool, repo, "check") == 0


def test_bootstrap_refuses_a_first_add_id_recorded_nowhere(tool: ModuleType, repo: Path) -> None:
    _stage(repo, "lib/orphan.py", b"x = 'filed under an id nothing records'\n")
    _commit(repo, "CS-0099 - an id neither record spells")
    assert _run(tool, repo, "bootstrap") == REFUSED
    assert not _manifest(repo).exists()


def test_add_refuses_an_item_recorded_nowhere(tool: ModuleType, repo: Path) -> None:
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-0099")
        == REFUSED
    )
    # CS-4 is a prefix of nothing recorded and CS-11 would falsely match CS-1 by prefix.
    for near_miss in ("CS-4", "CS-11", "CS-116"):
        assert (
            _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", near_miss)
            == REFUSED
        )
    assert not _manifest(repo).exists()


def _record_a_block_name(repo: Path) -> None:
    """Make the records spell the block `CS-6nn` and never the id CS-6 itself."""
    _write(repo, "ROADMAP.md", (ROADMAP_TEXT + "- the CS-6nn block\n").encode())
    _git(repo, "add", "ROADMAP.md")
    _commit(repo, "CS-42 - name the CS-6nn block")


def test_bootstrap_does_not_read_an_id_out_of_a_block_name(tool: ModuleType, repo: Path) -> None:
    # Measured on the S3 bootstrap: "Open the CS-9nn block and file CS-900" seeded
    # a row citing CS-9, an item that does not exist, because the lookahead refused
    # only a following digit and the records spell `CS-9nn` too.
    _record_a_block_name(repo)
    _stage(repo, "lib/block.py", b"x = 'filed when the block opened'\n")
    _commit(repo, "Open the CS-6nn block and file CS-42")
    assert _run(tool, repo, "bootstrap") == 0
    rows = {row[0]: row for row in _rows(repo)}
    assert rows["lib/block.py"] == ["lib/block.py", "authored", "CS-42", "first-add:CS-42"]


def test_add_refuses_an_id_recorded_only_as_a_block_name(tool: ModuleType, repo: Path) -> None:
    _record_a_block_name(repo)
    assert (
        _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-6")
        == REFUSED
    )
    assert not _manifest(repo).exists()
    # The control: an id the records do spell whole is accepted on the same tree.
    assert _run(tool, repo, "add", "lib/authored.py", "--class", "authored", "--item", "CS-42") == 0


def test_check_names_a_row_whose_item_is_recorded_nowhere(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rows = [
        r if r[0] != "Zeta.md" else ("Zeta.md", "authored", "CS-0099", "stamped")
        for r in _full_rows()
    ]
    _seed_manifest(repo, rows)
    capsys.readouterr()
    assert _run(tool, repo, "check") == FOUND
    assert "CS-0099" in capsys.readouterr().out


def test_a_header_without_its_space_is_malformed(tool: ModuleType, repo: Path) -> None:
    _write(repo, "tools/provenance.tsv", b"#nospace\nZeta.md\tauthored\tCS-8\tstamped\n")
    assert _run(tool, repo, "check") == REFUSED


def test_a_blank_line_is_malformed(tool: ModuleType, repo: Path) -> None:
    _write(repo, "tools/provenance.tsv", b"# h\n\nZeta.md\tauthored\tCS-8\tstamped\n")
    assert _run(tool, repo, "check") == REFUSED


# --- the format the arm parses, replicated independently -----------------
#
# The test_provenance_manifest arm owns the grammar and lives in another
# slice, so its parser is not imported here. These rules are RE-STATED from the
# plan section 2.1 and the S1 grammar, written without the tool's own
# constants, so a tool that drifted from the arm's format goes red here rather
# than first at pre-push.

ARM_BASIS_RE = r"stamped|first-add:(?:root|CS-[0-9]+)"
ARM_CITED_RE = r"(?<![A-Za-z0-9])CS-[0-9]+(?![0-9A-Za-z])"


ARM_COLUMNS = 4


def _arm_row_faults(cells: list[str], cited: set[str]) -> list[str]:
    """Return what is wrong with one well-shaped row, by the arm's rules."""
    path, klass, item, basis = cells
    faults: list[str] = []
    if klass not in {"authored", "vendored"}:
        faults.append(f"class: {path}")
    if not re.fullmatch(r"CS-[0-9]+", item) or item not in cited:
        faults.append(f"item: {path}")
    if not re.fullmatch(ARM_BASIS_RE, basis):
        faults.append(f"basis: {path}")
    if any(ch in path for ch in '\t"') or not path.isascii():
        faults.append(f"path: {path}")
    return faults


def _arm_grade(root: Path) -> list[str]:
    """Grade the manifest exactly as the arm's rules read, returning faults."""
    raw = _manifest(root).read_bytes()
    faults: list[str] = []
    if not raw.isascii():
        faults.append("non-ascii")
    if b"\r" in raw:
        faults.append("cr")
    if not raw.endswith(b"\n"):
        faults.append("no final newline")
    lines = raw.decode("ascii", "replace").split("\n")[:-1]
    if not lines[0].startswith("# "):
        faults.append("header")
    if any(line.startswith("#") for line in lines[1:]):
        faults.append("second comment")
    records = "".join(
        (root / name).read_text(encoding="utf-8") for name in ("ROADMAP.md", "docs/LEDGER.md")
    )
    cited = set(re.findall(ARM_CITED_RE, records))
    paths: list[bytes] = []
    for line in lines[1:]:
        cells = line.split("\t")
        if len(cells) != ARM_COLUMNS or not line:
            faults.append(f"cells: {line!r}")
            continue
        paths.append(cells[0].encode("utf-8"))
        faults += _arm_row_faults(cells, cited)
    if paths != sorted(set(paths)):
        faults.append("order or duplicates")
    if b"tools/provenance.tsv" not in paths:
        faults.append("the manifest does not list itself")
    vendored = {line.split("\t")[0] for line in lines[1:] if "\tvendored\t" in line}
    if vendored != {"lib/vendored.py"}:
        faults.append("vendored rows differ from the register")
    return faults


def test_a_tool_written_manifest_satisfies_the_arm_grammar(tool: ModuleType, repo: Path) -> None:
    assert _run(tool, repo, "bootstrap") == 0
    _stage(repo, "lib/later.py", b"x = 'stamped after the bootstrap'\n")
    assert _run(tool, repo, "add", "lib/later.py", "--class", "authored", "--item", "CS-9") == 0
    _git(repo, "mv", "Zeta.md", "Alpha.md")
    assert _run(tool, repo, "mv", "Zeta.md", "Alpha.md") == 0
    assert _arm_grade(repo) == []
    assert _run(tool, repo, "check") == 0


def test_the_arm_grammar_replica_is_not_vacuous(tool: ModuleType, repo: Path) -> None:
    # Control: the replica must redden a manifest the tool would refuse to write.
    assert _run(tool, repo, "bootstrap") == 0
    good = _manifest(repo).read_bytes()
    for broken in (
        good.replace(b"\n", b"\r\n"),
        good.replace(b"# ", b"#", 1),
        good.replace(b"CS-0042", b"CS-0099"),
        good.replace(b"\tauthored\t", b"\tmine\t", 1),
        good.replace(b"first-add:root", b"first-add:guess", 1),
        good.replace(b"tools/provenance.tsv\t", b"tools/other.tsv\t"),
        good.replace(b"lib/vendored.py\tvendored", b"lib/vendored.py\tauthored"),
    ):
        assert broken != good, "a control mutant did not land"
        _write(repo, "tools/provenance.tsv", broken)
        assert _arm_grade(repo) != []


def test_bootstrap_takes_the_oldest_add_of_a_readded_path(tool: ModuleType, repo: Path) -> None:
    _git(repo, "rm", "-q", "Zeta.md")
    _commit(repo, "CS-0050 - drop it")
    _stage(repo, "Zeta.md", b"# back again, re-added later\n")
    _commit(repo, "CS-0060 - re-add it")
    assert _run(tool, repo, "bootstrap") == 0
    assert ["Zeta.md", "authored", "CS-0042", "first-add:CS-0042"] in _rows(repo)


def test_bootstrap_refuses_over_an_existing_manifest(tool: ModuleType, repo: Path) -> None:
    before = _seed_manifest(repo, [("Zeta.md", "authored", "CS-8", "stamped")])
    assert _run(tool, repo, "bootstrap") == REFUSED
    assert _manifest(repo).read_bytes() == before
    assert _leftovers(repo) == []


def test_bootstrap_refuses_a_path_with_no_first_add(tool: ModuleType, repo: Path) -> None:
    _stage(repo, "lib/staged.py", b"x = 'staged, never committed'\n")
    assert _run(tool, repo, "bootstrap") == REFUSED
    assert not _manifest(repo).exists()


def test_bootstrap_refuses_an_authored_near_duplicate(tool: ModuleType, repo: Path) -> None:
    _stage(repo, "lib/fresh.py", VENDORED_BYTES)
    _commit(repo, "CS-0070 - a lift nobody registered")
    assert _run(tool, repo, "bootstrap") == REFUSED
    assert not _manifest(repo).exists()


def test_bootstrap_refuses_a_shallow_clone(tool: ModuleType, repo: Path, tmp_path: Path) -> None:
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", repo.resolve().as_uri(), str(shallow))
    assert _run(tool, shallow, "bootstrap") == REFUSED
    assert not _manifest(shallow).exists()


def test_bootstrap_is_deterministic(tool: ModuleType, repo: Path, tmp_path: Path) -> None:
    twin = tmp_path / "twin"
    _git(tmp_path, "clone", "-q", repo.resolve().as_uri(), str(twin))
    assert _run(tool, repo, "bootstrap") == 0
    assert _run(tool, twin, "bootstrap") == 0
    assert _manifest(repo).read_bytes() == _manifest(twin).read_bytes()


def test_no_written_byte_or_message_spells_the_root(
    tool: ModuleType, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(tool, repo, "bootstrap") == 0
    assert _run(tool, repo, "check") == 0
    raw = _manifest(repo).read_bytes().decode("ascii")
    said = capsys.readouterr()
    for spelling in {str(repo), repo.as_posix(), str(Path.home()), Path.home().as_posix()}:
        assert spelling not in raw
        assert spelling not in said.out + said.err


# --- the surface ----------------------------------------------------------


def test_the_cli_offers_no_bulk_mode(tool: ModuleType) -> None:
    assert frozenset(tool.SUBCOMMANDS) == EXPECTED_SUBCOMMANDS


def test_add_takes_exactly_one_path(tool: ModuleType, repo: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        _run(
            tool, repo, "add", "lib/authored.py", "Zeta.md", "--class", "authored", "--item", "CS-7"
        )
    assert raised.value.code == REFUSED
    assert not _manifest(repo).exists()
