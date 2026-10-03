"""CS-1183 - the tier-3 flip checks, graded over throwaway repositories only.

ADR 0025 rules the executor a LOCAL tools script, never CI. These arms grade
``tools/flip_checks.py`` without ever pointing it at the real history or the
real save directory: every repository is built in ``tmp_path``, every PII
needle is synthetic, and the one arm that derives needles aims the save-root
and account overrides at a synthetic save written by ``tests/save/synthetic.py``.
The real run walks all history; these arms do not.

NO NEEDLE IS EVER RENDERED. Every assertion that concerns a needle binds a
scalar first, so pytest's assertion rewriting has nothing to print but a
boolean or a count, and the needle objects' own ``repr`` withholds every value.

EVERY CHECK IS GRADED BOTH WAYS - its positive control must be found, and a
clean population must pass - because a control that is always found and a
check that always passes render identically in a summary.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

from tests.save import synthetic

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
FLIP_SOURCE: Final = REPO_ROOT / "tools" / "flip_checks.py"

#: Seconds one git call made by an arm may take.
TIMEOUT: Final = 120

#: A synthetic display name, planted only in synthetic saves.
DISPLAY_NAME: Final = "Synthetic Pioneer"

#: A synthetic, all-digit account directory name. Invented.
ACCOUNT_DIR: Final = "10000000000000001"

#: The bound the README control's hang is held to in these arms.
FAST_CONTROL_TIMEOUT: Final = 3


def _load() -> ModuleType:
    """Import ``tools/flip_checks.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_flip_checks", FLIP_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {FLIP_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


flip = _load()


@pytest.fixture(autouse=True)
def _isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the operator's git configuration out of every arm, and CI's refusal off."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "absent-global"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "absent-system"))
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


def run_git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` with a synthetic identity; return stripped stdout."""
    completed = subprocess.run(
        ["git", "-c", "user.name=arm", "-c", "user.email=arm@example.invalid", *args],
        cwd=repo,
        capture_output=True,
        timeout=TIMEOUT,
        check=True,
    )
    return completed.stdout.decode("utf-8").strip()


def work_repo(path: Path, files: dict[str, bytes], *, executable: tuple[str, ...] = ()) -> str:
    """A repository with a real work tree holding ``files``, committed with no hook."""
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, "init", "-q")
    for name, data in files.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    run_git(path, "add", "-A")
    for name in executable:
        run_git(path, "update-index", "--chmod=+x", name)
    run_git(path, "-c", "core.hooksPath=.no-hooks", "commit", "-q", "-m", "CS-0 - fixture")
    return run_git(path, "rev-parse", "HEAD")


def recording(called: list[bool]) -> Any:
    """A runner that records being called and measures nothing."""

    def runner(*_args: object) -> list[object]:
        called.append(True)
        return []

    return runner


def passing(key: str = "1") -> object:
    """A check result that passes."""
    return flip.CheckResult(key, "fake", counts={"n": 1}, control=True)


# --- ADR 0025: local, by hand, never on push ----------------------------------


def test_no_workflow_hook_or_lane_names_the_tool() -> None:
    """Decision item 1: nothing that runs on push, on a schedule or in the lane names it."""
    listed = run_git(
        REPO_ROOT, "ls-files", ".github", ".githooks", "ops", "tools/headless-queue.md"
    )
    naming = [
        name
        for name in listed.splitlines()
        if "flip_checks" in (REPO_ROOT / name).read_text(encoding="utf-8", errors="replace")
    ]
    assert naming == []
    tier3_exists = (REPO_ROOT / ".github" / "workflows" / "tier3.yml").exists()
    assert not tier3_exists


def test_the_tool_refuses_to_run_under_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    """A future workflow that did name it would get exit 2, never a run."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    called: list[bool] = []

    code = flip.main(
        ["HEAD", "--stage", "s8", "--repo", str(REPO_ROOT)],
        runner=recording(called),
    )

    assert code == flip.EXIT_COULD_NOT_RUN
    assert called == []


# --- the run: ref, exit codes, the final line, the scratch directory ---------


def test_an_unresolvable_ref_exits_two(tmp_path: Path) -> None:
    """Decision item 2: an unresolvable ref could not run, and nothing is measured."""
    work_repo(tmp_path / "repo", {"README.md": b"x\n"})
    called: list[bool] = []

    code = flip.main(
        ["refs/heads/absent", "--stage", "s8", "--repo", str(tmp_path / "repo")],
        runner=recording(called),
    )

    assert code == flip.EXIT_COULD_NOT_RUN
    assert called == []


def test_an_option_shaped_ref_exits_two(tmp_path: Path) -> None:
    """A ref that starts with a dash is an option smuggled in, never a revision."""
    repo = tmp_path / "repo"
    work_repo(repo, {"README.md": b"x\n"})
    called: list[bool] = []

    code = flip.main(
        ["--stage", "s8", "--repo", str(repo), "--", "--all"], runner=recording(called)
    )

    assert code == flip.EXIT_COULD_NOT_RUN
    assert called == []


def test_a_half_given_baseline_exits_two(tmp_path: Path) -> None:
    """The S8 baseline is a ref AND a count; one without the other is refused."""
    work_repo(tmp_path / "repo", {"README.md": b"x\n"})

    code = flip.main(
        [
            "HEAD",
            "--stage",
            "s8",
            "--repo",
            str(tmp_path / "repo"),
            "--trailer-baseline-count",
            "3",
        ],
        runner=lambda *_args: [passing()],
    )

    assert code == flip.EXIT_COULD_NOT_RUN


def test_the_sha_prints_first_and_the_final_line_is_never_a_bare_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Decision items 2 and 7, read off the real output of a passing run."""
    sha = work_repo(tmp_path / "repo", {"README.md": b"x\n"})

    code = flip.main(
        ["HEAD", "--stage", "s8", "--repo", str(tmp_path / "repo")],
        runner=lambda *_args: [passing("1"), passing("T")],
    )
    lines = capsys.readouterr().out.strip().splitlines()

    assert code == flip.EXIT_PASS
    assert lines[0] == f"flip_checks: ref {sha}"
    assert lines[-1] != "PASS"
    assert "automated verdict PASS" in lines[-1]
    assert "NOT-RUN-HERE 2" in lines[-1]
    assert "does not clear CS-G03" in lines[-1]
    assert sum(1 for line in lines if "human half: NOT-RUN-HERE" in line) == len(flip.HUMAN_HALVES)


@pytest.mark.parametrize(
    "broken",
    [
        {"control": False},
        {"skips": 1},
        {"failures": ["a fixed reason"]},
    ],
    ids=["control-not-found", "one-skip", "one-failure"],
)
def test_a_missing_control_a_skip_or_a_failure_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], broken: dict[str, object]
) -> None:
    """Decision items 5 and 7: any of the three makes the run fail."""
    work_repo(tmp_path / "repo", {"README.md": b"x\n"})
    fields: dict[str, object] = {"counts": {"n": 1}, "control": True, **broken}
    bad = flip.CheckResult("2", "fake", **fields)

    code = flip.main(
        ["HEAD", "--stage", "s8", "--repo", str(tmp_path / "repo")],
        runner=lambda *_args: [passing(), bad],
    )
    last = capsys.readouterr().out.strip().splitlines()[-1]

    assert code == flip.EXIT_FAIL
    assert "automated verdict FAIL" in last


def test_an_empty_result_list_is_not_a_pass(tmp_path: Path) -> None:
    """A run that measured nothing is not a run that found nothing."""
    work_repo(tmp_path / "repo", {"README.md": b"x\n"})

    code = flip.main(
        ["HEAD", "--stage", "s8", "--repo", str(tmp_path / "repo")], runner=lambda *_args: []
    )

    assert code == flip.EXIT_FAIL


def test_the_scratch_directory_is_inside_the_git_directory_and_removed(tmp_path: Path) -> None:
    """Every built path avoids the temp directory, and nothing is left behind."""
    repo = tmp_path / "repo"
    work_repo(repo, {"README.md": b"x\n"})
    seen: list[Path] = []

    def recording_scratch_runner(*args: object) -> list[object]:
        scratch = args[3]
        assert isinstance(scratch, Path)
        seen.append(scratch)
        return [passing()]

    flip.main(["HEAD", "--stage", "s8", "--repo", str(repo)], runner=recording_scratch_runner)

    (scratch,) = seen
    inside = scratch.resolve().is_relative_to((repo / ".git").resolve())
    assert inside
    assert not scratch.exists()


def rendered_leak(text: str) -> bool:
    """Whether ``text`` carries the home directory or the interpreter's path."""
    folded = text.lower()
    return str(Path.home()).lower() in folded or sys.executable.lower() in folded


def test_a_child_that_will_not_die_exits_two_and_renders_no_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A reap that times out escapes every check; main names the TYPE and exits 2."""
    repo = tmp_path / "repo"
    work_repo(repo, {"README.md": b"x\n"})
    tree = readme_tree(
        tmp_path / "tree",
        {"hangs.py": b"import time\ntime.sleep(3600)\n"},
        "```\npython scripts/hangs.py\n```\n",
    )

    def never_reaps(_self: subprocess.Popen[bytes], timeout: float | None = None) -> int:
        raise subprocess.TimeoutExpired([sys.executable, str(Path.home())], timeout or 0)

    def runner(*_args: object) -> list[object]:
        monkeypatch.setattr(subprocess.Popen, "wait", never_reaps)
        walk = lambda: flip.readme_walk(tree, python=sys.executable, timeout=1)  # noqa: E731
        return [flip.measure("5", "readme-walk", walk, lambda: True)]

    code = flip.main(["HEAD", "--stage", "s8", "--repo", str(repo)], runner=runner)
    monkeypatch.undo()
    captured = capsys.readouterr()
    text = captured.out + captured.err
    leaked = rendered_leak(text)
    named = "TimeoutExpired during check 5" in captured.err

    assert code == flip.EXIT_COULD_NOT_RUN
    assert named
    assert not leaked


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (KeyboardInterrupt(), 130),
        (RuntimeError(sys.executable + " " + str(Path.home())), 2),
        (SystemExit(sys.executable), 2),
    ],
    ids=["ctrl-c", "runtime-error-carrying-paths", "system-exit"],
)
def test_no_exception_renders_a_traceback_or_a_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    raised: BaseException,
    expected: int,
) -> None:
    """Every exception ends in one fixed line: the phase and the TYPE, nothing else."""
    repo = tmp_path / "repo"
    work_repo(repo, {"README.md": b"x\n"})

    def runner(*_args: object) -> list[object]:
        flip.PHASE[0] = "check 2"
        raise raised

    code = flip.main(["HEAD", "--stage", "s8", "--repo", str(repo)], runner=runner)
    captured = capsys.readouterr()
    text = captured.out + captured.err
    leaked = rendered_leak(text)
    traceback_rendered = "Traceback" in text

    assert code == expected
    assert "during check 2" in captured.err
    assert not leaked
    assert not traceback_rendered


def test_a_git_failure_never_carries_git_stderr(tmp_path: Path) -> None:
    """A child's stderr quotes its arguments and can quote paths; the reason is fixed text."""
    repo = flip.ControlRepo(tmp_path / "repo")
    repo.commit({"README.md": b"x\n"}, b"x\n")
    marker = "flipstderrmarker" + "5a0d"

    with pytest.raises(flip.FlipError) as caught:
        flip.git(repo.path, ["cat-file", "-p", marker])
    carried = marker in caught.value.reason

    assert not carried


#: Identifiers that would put a child's argv, output or stderr - or the
#: interpreter's path - into printed text, a FlipError reason or a failure.
UNRENDERABLE: Final = frozenset({"argv", "cmd", "stderr", "stdout", "output", "executable"})


def test_no_rendering_call_can_reach_an_argv_or_a_child_stream() -> None:
    """Every print, FlipError and failure reason in the tool names none of them."""
    import ast  # noqa: PLC0415 - only this arm reads the tool as source

    tree = ast.parse(FLIP_SOURCE.read_text(encoding="utf-8"))
    offending: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        renders = (isinstance(func, ast.Name) and func.id in {"print", "FlipError"}) or (
            isinstance(func, ast.Attribute)
            and func.attr == "append"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "failures"
        )
        if not renders:
            continue
        names = {
            inner.id if isinstance(inner, ast.Name) else inner.attr
            for argument in node.args
            for inner in ast.walk(argument)
            if isinstance(inner, ast.Name | ast.Attribute)
        }
        if names & UNRENDERABLE:
            offending.append(node.lineno)

    assert offending == []


def test_a_failing_readme_command_renders_no_argv(tmp_path: Path) -> None:
    """A failed child is counted; its argv, interpreter path included, is never printed."""
    tree = readme_tree(
        tmp_path / "tree",
        {"fails.py": b"raise SystemExit(3)\n"},
        "```\npython scripts/fails.py\n```\n",
    )

    result = flip.readme_walk(tree, python=sys.executable, timeout=30)
    leaked = rendered_leak("\n".join(result.render()))

    assert result.counts["failed"] == 1
    assert not leaked


def test_a_step_that_could_not_be_taken_fails_its_check() -> None:
    """``measure`` turns a raise into a failure and a raising control into NOT FOUND."""

    def body() -> object:
        raise flip.FlipError("fixed reason")

    def control() -> bool:
        raise flip.FlipError("fixed reason")

    result = flip.measure("9", "fake", body, control)

    assert not result.passed
    assert result.control is False
    assert result.failures == ["could not measure: fixed reason"]


# --- check 1: secrets ---------------------------------------------------------


def test_the_secret_control_finds_a_credential_that_lives_only_in_history(tmp_path: Path) -> None:
    """Planted, then deleted: only a history scan can see it."""
    assert flip.control_secret(tmp_path)


def test_a_clean_history_has_no_secret_finding(tmp_path: Path) -> None:
    """The other direction: the check passes a clean population."""
    repo = flip.ControlRepo(tmp_path / "clean")
    tip = repo.commit({"README.md": b"nothing here\n"}, b"clean\n")

    result = flip.secret_scan(repo.path, tip)

    assert result.counts["findings"] == 0
    assert result.failures == []


def test_a_blob_the_gate_declines_is_scanned_raw_rather_than_skipped(tmp_path: Path) -> None:
    """A known-binary extension is declined by the gate; history is scanned anyway."""
    repo = flip.ControlRepo(tmp_path / "declined")
    line = "access" + "_key = " + flip.synthetic_credential() + "\n"
    tip = repo.commit({"image.png": line.encode("ascii")}, b"x\n")

    result = flip.secret_scan(repo.path, tip)

    assert result.counts["declined by the gate and scanned raw"] == 1
    assert result.counts["findings"] >= 1


def test_a_credential_in_a_commit_message_is_found(tmp_path: Path) -> None:
    """Commit messages are a channel of their own, scanned with the same rules."""
    repo = flip.ControlRepo(tmp_path / "message")
    line = "access" + "_key = " + flip.synthetic_credential() + "\n"
    tip = repo.commit({"README.md": b"clean\n"}, ("subject\n\n" + line).encode("ascii"))

    result = flip.secret_scan(repo.path, tip)

    assert result.counts["findings"] >= 1
    assert result.shas == [tip]


# --- check 2: personal data ---------------------------------------------------


def test_the_pii_control_finds_a_synthetic_needle_in_every_channel(tmp_path: Path) -> None:
    """Blob, path and message all see the planted token, by the same scan."""
    assert flip.control_pii(tmp_path, flip.NeedleSet())


def test_a_history_only_needle_fails_the_check_and_is_never_rendered(tmp_path: Path) -> None:
    """The hit is found, named by blob SHA, and the needle appears in no rendering."""
    token = "flipneedle" + "4e1c9a"
    needles = flip.NeedleSet()
    needles.add("header-string", token)
    repo = flip.ControlRepo(tmp_path / "pii")
    repo.commit({"notes.md": f"by {token}.\n".encode("ascii")}, b"plant\n")
    tip = repo.commit({"notes.md": b"clean\n"}, b"remove\n")

    result = flip.pii_scan(repo.path, tip, needles)
    rendered = "\n".join(result.render()) + repr(needles) + repr(needles.matchers())
    leaked = token in rendered

    assert result.counts["blob hits"] == 1
    assert "a needle is reachable from REF" in result.failures
    assert not leaked


def test_a_clean_history_passes_the_pii_scan(tmp_path: Path) -> None:
    """A needle absent from every channel yields zero hits and no failure."""
    needles = flip.NeedleSet()
    needles.add("header-string", "flipabsent" + "77d0")
    repo = flip.ControlRepo(tmp_path / "clean")
    tip = repo.commit({"README.md": b"nothing here\n"}, b"clean\n")

    result = flip.pii_scan(repo.path, tip, needles)

    assert result.failures == []
    assert result.skips == 0


def test_needles_match_whole_words_case_insensitively() -> None:
    """The gate's own boundary: a longer identifier does not match."""
    matcher = flip.Matcher.of_values("account-name", ["Synthetic"])

    assert matcher.count(b"by SYNTHETIC here") == 1
    assert matcher.count(b"Synthetics and synthetic_x") == 0


def test_a_path_needle_matches_either_slash() -> None:
    """A home path arrives with backslashes in one file and slashes in another."""
    matcher = flip.Matcher.of_values("home-path", ["D:/work/synthetic"])

    assert matcher.count(b"at D:\\work\\synthetic\\x and D:/work/synthetic/y") == len("xy")


def test_a_needle_too_short_to_match_safely_is_a_skip(tmp_path: Path) -> None:
    """A dropped needle is an unmeasured value, so the check cannot pass."""
    needles = flip.NeedleSet()
    needles.add("account-name", "ab")
    repo = flip.ControlRepo(tmp_path / "short")
    tip = repo.commit({"README.md": b"x\n"}, b"x\n")

    result = flip.pii_scan(repo.path, tip, needles)

    assert result.skips == 1
    assert not result.passed


def test_the_spec_named_constants_are_not_needles() -> None:
    """``BOOTSTRAP.md`` section 2.2 names the platform and ``None`` as non-personal."""
    needles = flip.NeedleSet()
    for value in ("STEAM", "None", "steam"):
        needles.add("header-string", value)

    kinds = len(needles.counts())
    dropped = int(needles.dropped)

    assert kinds == 0
    assert dropped == 0


def player_info(*strings: str, wide: str | None = None) -> str:
    """A hex-encoded options value shaped like the measured player snapshot."""
    blob = b"".join(synthetic.fstring(text) for text in strings)
    blob += (10000000000000001).to_bytes(8, "little")
    if wide is not None:
        blob += synthetic.fstring(wide, wide=True)
    return blob.hex().upper()


def test_option_strings_decode_every_length_prefixed_string() -> None:
    """Narrow and wide strings in a hex value are read; plain values are not."""
    options = (
        "?listenServer=0?PlayerInfoSnapshot="
        + player_info("STEAM", "None", DISPLAY_NAME, wide="Wide Pioneer")
        + "?Visibility=SV_Private"
    )

    decoded = flip.decoded_option_strings(options)

    assert decoded == ["STEAM", "None", DISPLAY_NAME, "Wide Pioneer"]


def synthetic_save_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Aim every override at a synthetic save root holding one synthetic account."""
    root = tmp_path / "saves"
    account = root / ACCOUNT_DIR
    account.mkdir(parents=True)
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(root))
    monkeypatch.setenv("CLOCKSPEED_ACCOUNT_DIR", str(account))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local.json"))
    return account


def test_needles_derive_from_a_synthetic_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The display name and the session name come out of the header; counts only."""
    account = synthetic_save_root(tmp_path, monkeypatch)
    options = "?PlayerInfoSnapshot=" + player_info("STEAM", "None", DISPLAY_NAME)
    (account / "synthetic.sav").write_bytes(synthetic.build_header(options=options))

    needles = flip.derive_needles()
    counts = needles.counts()
    found = any(m.count(b"by " + DISPLAY_NAME.encode("ascii") + b".") for m in needles.matchers())
    failures = len(needles.failures)
    unreadable = int(needles.unreadable)

    assert failures == 0
    assert unreadable == 0
    assert counts.get("header-string") == 1
    assert counts.get("world-name") == 1
    assert counts.get("account-id", 0) >= 1
    assert found


def test_a_save_root_that_does_not_resolve_fails_check_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Decision item 4: no needle source is a FAILURE, never a skip."""
    monkeypatch.setenv("CLOCKSPEED_SAVE_ROOT", str(tmp_path / "absent-saves"))
    monkeypatch.setenv("CLOCKSPEED_ACCOUNT_DIR", str(tmp_path / "absent-account"))
    monkeypatch.setenv("CLOCKSPEED_LOCAL_CONFIG", str(tmp_path / "absent-local.json"))
    repo = flip.ControlRepo(tmp_path / "repo")
    tip = repo.commit({"README.md": b"x\n"}, b"x\n")

    result = flip.pii_scan(repo.path, tip, flip.derive_needles())

    assert "the save root did not resolve" in result.failures
    assert "no header string was decoded, so no display name was derived" in result.failures


def test_an_unreadable_save_header_is_a_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A save the header parser refuses is an unmeasured source."""
    account = synthetic_save_root(tmp_path, monkeypatch)
    options = "?PlayerInfoSnapshot=" + player_info(DISPLAY_NAME)
    (account / "good.sav").write_bytes(synthetic.build_header(options=options))
    (account / "broken.sav").write_bytes(b"\x01\x02")

    unreadable = int(flip.derive_needles().unreadable)

    assert unreadable == 1


# --- check 4: publisher-owned assets ------------------------------------------


def test_the_publisher_control_finds_a_path_that_lives_only_in_history(tmp_path: Path) -> None:
    """A save added and then deleted is still reachable history."""
    assert flip.control_publisher(tmp_path)


def test_a_blob_stored_at_two_paths_is_seen_at_both(tmp_path: Path) -> None:
    """``rev-list --objects`` names a blob once; the history walk must see the second path."""
    repo = flip.ControlRepo(tmp_path / "twice")
    tip = repo.commit({"a.txt": b"same bytes\n", "b.sav": b"same bytes\n"}, b"x\n")

    result = flip.publisher_scan(repo.path, tip)

    assert result.counts["publisher paths"] == 1
    assert result.shas == [tip]


def test_a_clean_history_has_no_publisher_path(tmp_path: Path) -> None:
    """The other direction."""
    repo = flip.ControlRepo(tmp_path / "clean")
    tip = repo.commit({"README.md": b"x\n"}, b"x\n")

    result = flip.publisher_scan(repo.path, tip)

    assert result.failures == []


# --- checks 3 and 6: the child tools ------------------------------------------


def test_the_licence_control_adds_a_finding_over_the_real_inputs(tmp_path: Path) -> None:
    """An unrecorded lockfile package is a finding of the audit's own CLI."""
    assert flip.control_licence(REPO_ROOT, tmp_path)


# --- CS-1230: a path named across two Windows drives -------------------------


def _other_drive_anchor() -> Path:
    """An absolute directory under no home, on the ``D:`` drive anchor.

    The GitHub windows runner checks the repository out there. Nothing is
    created under it. Only a drive-letter path is ever allowed as the absolute
    fallback, so the arms that expect it allowed run where drives exist.
    """
    if not Path.home().drive:
        pytest.skip("drive letters exist only on Windows")
    return Path("D:" + "\\") / "cs1230-anchor" / "repo"


def _drives_only() -> None:
    """Skip an arm whose subject is Windows drive-letter path semantics."""
    if not Path.home().drive:
        pytest.skip("drive letters exist only on Windows")


def _cross_drive_relpath(*_args: object) -> str:
    """``os.path.relpath`` as it behaves across two Windows drives."""
    message = "path is on mount 'D:', start on mount 'C:'"
    raise ValueError(message)


def _carries_a_home(argv: list[str]) -> bool:
    """Whether any argv element renders this machine's home, or any home shape."""
    home = str(Path.home()).lower()
    rules = flip.gate()
    shapes = [
        re.compile(rules.PII_WIN_HOME_RE.pattern, re.IGNORECASE),
        re.compile(rules.PII_NIX_HOME_RE.pattern, re.IGNORECASE),
    ]
    return any(
        home in part.lower() or any(shape.search(part) is not None for shape in shapes)
        for part in argv
    )


def test_a_child_tool_on_another_drive_is_named_without_a_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tool and a cwd on two drive anchors: no exception, and no home in the argv."""
    monkeypatch.setattr(flip.os.path, "relpath", _cross_drive_relpath)
    tool = _other_drive_anchor() / "tools" / "licence_audit.py"

    argv = flip._tool_argv(tool, tmp_path, "--root", ".")  # noqa: SLF001 - the CS-1230 arm names the helper

    leaked = _carries_a_home(argv[2:])
    assert argv[3:] == ["--root", "."]
    assert not leaked


def test_a_real_second_drive_names_the_child_tool_without_a_home(tmp_path: Path) -> None:
    """The same, with no monkeypatch, where this box really has a second drive."""
    tool = _other_drive_anchor() / "tools" / "licence_audit.py"
    if tool.drive.lower() == tmp_path.drive.lower():
        pytest.skip("tmp_path already sits on the second drive")

    argv = flip._tool_argv(tool, tmp_path)  # noqa: SLF001 - the CS-1230 arm names the helper

    leaked = _carries_a_home(argv[2:])
    assert not leaked


def test_a_child_tool_under_a_home_on_another_drive_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No relative spelling and a home in the absolute one: refused, naming no path."""
    monkeypatch.setattr(flip.os.path, "relpath", _cross_drive_relpath)
    tool = Path.home() / "cs1230-tool.py"

    with pytest.raises(flip.FlipError) as caught:
        flip._tool_argv(tool, tmp_path)  # noqa: SLF001 - the CS-1230 arm names the helper

    leaked = _carries_a_home([str(caught.value)])
    assert not leaked


def _refused_without_a_path(tool: Path, start: Path) -> bool:
    """Whether naming ``tool`` from ``start`` is refused with text naming no path."""
    try:
        flip._tool_argv(tool, start)  # noqa: SLF001 - the CS-1230 arm names the helper
    except flip.FlipError as exc:
        return not _carries_a_home([str(exc)]) and "\\" not in str(exc)
    return False


def test_a_unc_spelling_of_the_home_is_refused(tmp_path: Path) -> None:
    """A UNC admin-share spelling of the home has no drive letter: never the fallback.

    No monkeypatch - the real ``os.path.relpath`` raises between a UNC path and C:.
    """
    _drives_only()
    home = str(Path.home())
    unc = Path("\\\\localhost\\" + home[0].lower() + "$" + home[2:]) / "cs1230-tool.py"

    refused = _refused_without_a_path(unc, tmp_path)

    assert refused


@pytest.mark.parametrize("prefix", ["\\\\?\\D:\\", "\\\\.\\D:\\"])
def test_a_device_or_verbatim_prefix_is_refused(tmp_path: Path, prefix: str) -> None:
    """Verbatim and device-namespace spellings are not plain drive-letter paths: refused."""
    _drives_only()

    refused = _refused_without_a_path(Path(prefix + "cs1230-anchor\\tool.py"), tmp_path)

    assert refused


def test_a_lower_case_home_shape_on_another_drive_is_refused(tmp_path: Path) -> None:
    """A lower-case ``users`` home of ANOTHER account is a home shape all the same."""
    _drives_only()
    other = "e" if tmp_path.drive.lower() != "e:" else "f"
    tool = Path(other + ":\\" + "users" + "\\other\\cs1230-tool.py")

    refused = _refused_without_a_path(tool, tmp_path)

    assert refused


def test_a_home_on_another_drive_is_refused_by_its_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A home in no ``users`` shape, on another drive, is refused by its location alone."""
    _drives_only()
    home = Path("E:" + "\\") / "Profiles" / "x"
    monkeypatch.setattr(flip.Path, "home", staticmethod(lambda: home))

    refused = _refused_without_a_path(home / "cs1230-tool.py", tmp_path)
    allowed = flip._tool_argv(home.parent / "cs1230-tool.py", tmp_path)  # noqa: SLF001 - the CS-1230 arm names the helper

    assert refused
    assert allowed[2].lower().endswith("cs1230-tool.py")


def _realpath_mapping(source: Path, target: str) -> Any:
    """A stand-in ``os.path.realpath`` that resolves ``source`` alone to ``target``.

    It models a ``subst`` or mapped drive without creating one; every other
    path - the home itself included - resolves to its own spelling.
    """
    real = flip.os.path.realpath

    def resolve(path: Any, *args: Any, **named: Any) -> str:
        if str(path) == str(source):
            return target
        resolved: str = real(path, *args, **named)
        return resolved

    return resolve


def test_a_drive_path_resolving_to_a_unc_home_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plain drive spelling whose REAL path is a UNC home: the real spelling decides."""
    _drives_only()
    home = str(Path.home())
    unc = "\\\\localhost\\" + home[0].lower() + "$" + home[2:] + "\\cs1230-tool.py"
    tool = _other_drive_anchor() / "cs1230-tool.py"
    monkeypatch.setattr(flip.os.path, "realpath", _realpath_mapping(tool, unc))

    refused = _refused_without_a_path(tool, tmp_path)

    assert refused


def test_a_drive_path_resolving_under_the_home_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plain drive spelling whose REAL path is under the home: the real path decides."""
    _drives_only()
    tool = Path("Q:" + "\\") / "x.py"
    resolved = str(Path.home() / "x.py")
    monkeypatch.setattr(flip.os.path, "realpath", _realpath_mapping(tool, resolved))

    refused = _refused_without_a_path(tool, tmp_path)

    assert refused


def test_an_unresolvable_home_refuses_with_fixed_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Path.home()`` raising leaves no way to rule a home out: refused, naming no path."""
    tool = _other_drive_anchor() / "cs1230-tool.py"

    def no_home() -> Path:
        message = "Could not determine home directory."
        raise RuntimeError(message)

    monkeypatch.setattr(flip.Path, "home", staticmethod(no_home))

    with pytest.raises(flip.FlipError) as caught:
        flip._tool_argv(tool, tmp_path)  # noqa: SLF001 - the CS-1230 arm names the helper

    text = str(caught.value)
    assert "\\" not in text
    assert "home" in text


def _recording_git(calls: list[list[str]]) -> Any:
    """A stand-in for :func:`flip.git` that records each argv and runs nothing."""

    def record(_repo: Path, args: Any, *_rest: object, **_named: object) -> bytes:
        calls.append(list(args))
        return b""

    return record


def test_a_clone_source_on_another_drive_is_named_without_a_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A clone source and a scratch target on two drive anchors: no home in git's argv."""
    monkeypatch.setattr(flip.os.path, "relpath", _cross_drive_relpath)
    calls: list[list[str]] = []
    monkeypatch.setattr(flip, "git", _recording_git(calls))

    flip.clone_at(_other_drive_anchor(), "0" * 40, tmp_path / "tree")

    leaked = any(_carries_a_home(call) for call in calls)
    clones = sum(1 for call in calls if call[:1] == ["clone"])
    assert clones == 1
    assert not leaked


def test_a_clone_source_under_a_home_on_another_drive_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clone source has no relative spelling and its absolute one is a home: refused."""
    monkeypatch.setattr(flip.os.path, "relpath", _cross_drive_relpath)
    calls: list[list[str]] = []
    monkeypatch.setattr(flip, "git", _recording_git(calls))

    with pytest.raises(flip.FlipError) as caught:
        flip.clone_at(Path.home() / "cs1230-repo", "0" * 40, tmp_path / "tree")

    leaked = _carries_a_home([str(caught.value)])
    ran = len(calls)
    assert ran == 0
    assert not leaked


def test_the_doc_sweep_control_adds_a_finding(tmp_path: Path) -> None:
    """An orphan markdown file adds a finding to the sweep's own CLI."""
    assert flip.control_doc_sweep(tmp_path)


#: Synthetic stand-ins for the two pinned sets and the repository URL. The arms
#: pass these, never the tool's real pins, so no arm depends on the live tree.
WIKI_PIN: Final = "https://synthetic.wiki.gg/wiki/Pinned_Page"
WIKI_UNPINNED: Final = "https://synthetic.wiki.gg/wiki/Other_Page"
BADGE_PAGE: Final = "https://forge.example.invalid/owner/repo/actions/workflows/t1.yml"
BADGE_IMAGE: Final = BADGE_PAGE + "/badge.svg"
REPO_URL: Final = "https://forge.example.invalid/owner/repo"
OTHER_DEAD: Final = "https://elsewhere.example.invalid/gone"


def pinned_tree(tmp_path: Path, extra: str = "") -> Path:
    """A tree carrying one badge (link plus image) and the pinned wiki URL."""
    readme = f"# x\n\n[![t1]({BADGE_IMAGE})]({BADGE_PAGE})\n\nSee <{WIKI_PIN}>.\n{extra}"
    repo = flip.ControlRepo(tmp_path / "docs")
    repo.commit({"README.md": readme.encode("ascii")}, b"x\n")
    flip.git(repo.path, ["checkout", "-q", "-f", "main"], env=repo.env)
    path: Path = repo.path
    return path


def sweep_pinned(
    tree: Path, statuses: dict[str, int], *, wiki: frozenset[str] = frozenset({WIKI_PIN})
) -> Any:
    """Check 6 over ``tree`` with a stub fetcher and synthetic pins - never the network."""
    result = flip.doc_sweep(
        tree,
        fetch=lambda url: statuses[url],
        probe=lambda url: statuses[url],
        allowlists=({}, {}),
        no_fetch_pinned=wiki,
        pre_publication_dead=frozenset({BADGE_PAGE, BADGE_IMAGE}),
        repository_url=REPO_URL,
    )
    result.control = True
    return result


PRIVATE: Final = {BADGE_PAGE: 404, BADGE_IMAGE: 404, REPO_URL: 404}


def test_the_pristine_pinned_tree_passes_check_six(tmp_path: Path) -> None:
    """Both pins hold, each reported by its own count, and nothing else is found."""
    result = sweep_pinned(pinned_tree(tmp_path), PRIVATE)

    assert result.failures == []
    assert result.skips == 0
    assert result.counts["policy-excluded"] == 1
    assert result.counts["pre-publication-dead"] == len((BADGE_PAGE, BADGE_IMAGE))
    assert result.passed


def test_an_unpinned_no_fetch_url_fails(tmp_path: Path) -> None:
    """A second wiki URL is outside the exact pin, whatever the count."""
    result = sweep_pinned(pinned_tree(tmp_path, f"\nAnd <{WIKI_UNPINNED}>.\n"), PRIVATE)

    assert "a no-fetch URL outside the pinned set" in result.failures
    assert not result.passed


def test_an_unpinned_dead_url_fails(tmp_path: Path) -> None:
    """A 404 outside the pre-publication pin is a dead URL, private repository or not."""
    statuses = {**PRIVATE, OTHER_DEAD: 404}
    result = sweep_pinned(pinned_tree(tmp_path, f"\nAnd <{OTHER_DEAD}>.\n"), statuses)

    assert "a dead URL outside the pre-publication pin" in result.failures
    assert not result.passed


def test_a_stale_pin_fails(tmp_path: Path) -> None:
    """A pinned URL the tree no longer carries is a stale excuse."""
    stale = frozenset({WIKI_PIN, WIKI_UNPINNED})
    result = sweep_pinned(pinned_tree(tmp_path), PRIVATE, wiki=stale)

    assert "a pinned URL the tree no longer carries" in result.failures
    assert not result.passed


def test_a_pinned_badge_404_fails_once_the_repository_is_public(tmp_path: Path) -> None:
    """The pin excuses a 404 only while the repository root answers 404 too."""
    statuses = {**PRIVATE, REPO_URL: 200}
    result = sweep_pinned(pinned_tree(tmp_path), statuses)

    assert "a dead URL outside the pre-publication pin" in result.failures
    assert not result.passed


def test_a_pinned_url_answering_neither_404_nor_200_fails(tmp_path: Path) -> None:
    """A pre-publication URL answering 500 is not the state the pin describes."""
    statuses = {**PRIVATE, BADGE_IMAGE: 500}
    result = sweep_pinned(pinned_tree(tmp_path), statuses)

    assert "a pre-publication URL answered neither 404 nor 200" in result.failures
    assert not result.passed


def test_a_short_name_repo_path_is_resolved_before_cloning(tmp_path: Path) -> None:
    """An 8.3 spelling of --repo is resolved once; git never sees it and it is never printed."""
    if sys.platform != "win32":
        pytest.skip("8.3 short names exist only on Windows volumes")
    import ctypes  # noqa: PLC0415 - Windows only

    repo = tmp_path / "a-long-repository-name"
    sha = work_repo(repo, {"README.md": b"x\n"})
    buffer = ctypes.create_unicode_buffer(1024)
    size = ctypes.windll.kernel32.GetShortPathNameW(str(repo), buffer, len(buffer))
    short = buffer.value if size else ""
    if not short or short.lower() == str(repo).lower():
        pytest.skip("this volume generates no 8.3 short names")

    def short_path_runner(repo_arg: Path, sha_arg: str, *rest: object) -> list[object]:
        scratch = rest[1]
        assert isinstance(scratch, Path)
        flip.clone_at(repo_arg, sha_arg, scratch / "tree")
        return [passing()]

    code = flip.main(["HEAD", "--stage", "s8", "--repo", short], runner=short_path_runner)

    assert sha
    assert code == flip.EXIT_PASS


# --- check 5: the README walk -------------------------------------------------


SERVE_SCRIPT: Final = b"""import os, socket, time
port = int(os.environ["CLOCKSPEED_DASHBOARD_PORT"])
listener = socket.socket()
listener.bind(("127.0.0.1", port))
listener.listen()
time.sleep(60)
"""

ENV_SCRIPT: Final = b"""import json, os
keys = sorted(k for k in os.environ if k.upper().startswith("CLOCKSPEED_"))
values = {k: os.environ[k] for k in keys}
open("seen-env.json", "w").write(json.dumps(values))
"""


def readme_tree(path: Path, scripts: dict[str, bytes], readme: str) -> Path:
    """A plain tree holding ``scripts/`` and a README."""
    (path / "scripts").mkdir(parents=True, exist_ok=True)
    for name, body in scripts.items():
        (path / "scripts" / name).write_bytes(body)
    (path / "README.md").write_text(readme, encoding="ascii")
    return path


def test_the_readme_control_sees_a_failure_and_a_hang(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both planted commands fail: a non-zero exit, and a hang that never served."""
    monkeypatch.setattr(flip, "CONTROL_COMMAND_TIMEOUT", FAST_CONTROL_TIMEOUT)

    assert flip.control_readme(tmp_path, python=sys.executable)


def test_a_command_that_exits_zero_or_serves_passes(tmp_path: Path) -> None:
    """The other direction, including a command that binds the port and keeps running."""
    tree = readme_tree(
        tmp_path / "tree",
        {"ok.py": b"raise SystemExit(0)\n", "serve.py": SERVE_SCRIPT},
        "# x\n\n```\npython scripts/ok.py\n```\n\n```\npython scripts/serve.py\n```\n",
    )

    result = flip.readme_walk(tree, python=sys.executable, timeout=30)

    assert result.counts == {"commands": 2, "failed": 0}
    assert result.failures == []


def test_the_walk_scrubs_overrides_and_builds_only_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An outsider has no override set; the walk's own four are relative and absent."""
    monkeypatch.setenv("CLOCKSPEED_CERT_DIR", str(tmp_path / "operator-certs"))
    tree = readme_tree(
        tmp_path / "tree", {"env.py": ENV_SCRIPT}, "```\npython scripts/env.py\n```\n"
    )

    flip.readme_walk(tree, python=sys.executable, timeout=30)
    seen = (tree / "seen-env.json").read_text(encoding="ascii")
    cert_dir_leaked = "CLOCKSPEED_CERT_DIR" in seen
    paths = re.findall(
        r'"CLOCKSPEED_(?:GAME_DIR|SAVE_ROOT|ACCOUNT_DIR|LOCAL_CONFIG)": "([^"]*)"', seen
    )
    absolute = [path for path in paths if Path(path).is_absolute()]

    assert not cert_dir_leaked
    assert len(paths) == len(("game", "saves", "account", "local"))
    assert absolute == []


def test_an_unrunnable_readme_line_is_a_skip(tmp_path: Path) -> None:
    """A line the walker will not run is counted, never run and never ignored."""
    tree = readme_tree(
        tmp_path / "tree",
        {"ok.py": b"raise SystemExit(0)\n"},
        "```\npython scripts/ok.py\npython -c 'print(1)'\n```\n",
    )

    result = flip.readme_walk(tree, python=sys.executable, timeout=30)

    assert result.skips == 1
    assert result.counts["commands"] == 1


def test_a_readme_with_no_command_fails(tmp_path: Path) -> None:
    """A walk of nothing is not a clean walk."""
    tree = readme_tree(tmp_path / "tree", {}, "# nothing to run\n")

    result = flip.readme_walk(tree, python=sys.executable, timeout=30)

    assert "README carries no runnable command line" in result.failures


# --- check 7: the clean checkout ----------------------------------------------


INSTALL_HOOKS: Final = b"""import subprocess, sys
subprocess.run(["git", "config", "core.hooksPath", ".githooks"], check=True, timeout=60)
sys.exit(0)
"""

OPERATIONS: Final = b"""# Ops

## 1. Fresh-clone bootstrap - run this first

```
python scripts/install_hooks.py        # sets core.hooksPath
```

## 2. Later

```
python scripts/not_part_of_bootstrap.py
```
"""


def checkout_repo(tmp_path: Path, hook: bytes, install: bytes = INSTALL_HOOKS) -> tuple[Path, str]:
    """A repository whose bootstrap arms ``hook`` as its pre-commit, cloned fresh."""
    source = tmp_path / "source"
    sha = work_repo(
        source,
        {
            "docs/OPERATIONS.md": OPERATIONS,
            "scripts/install_hooks.py": install,
            ".githooks/pre-commit": hook,
        },
        executable=(".githooks/pre-commit",),
    )
    return flip.clone_at(source, sha, tmp_path / "fresh"), sha


def test_the_clean_checkout_passes_when_the_armed_hook_refuses(tmp_path: Path) -> None:
    """Control: HEAD moves with no hook. Probe: HEAD stays put once armed."""
    clone, sha = checkout_repo(tmp_path, b"#!/bin/sh\necho refused >&2\nexit 1\n")

    result = flip.clean_checkout(clone, sha, python=sys.executable)

    assert result.control
    assert result.counts == {"bootstrap commands": 1, "failed": 0}
    assert result.failures == []
    assert result.passed


def test_a_hook_that_does_not_fire_fails_the_check(tmp_path: Path) -> None:
    """An armed hook that lets the violation through is the failure the check exists for."""
    clone, sha = checkout_repo(tmp_path, b"#!/bin/sh\nexit 0\n")

    result = flip.clean_checkout(clone, sha, python=sys.executable)

    assert "a staged violation committed - the armed hooks did not fire" in result.failures


def test_a_failing_bootstrap_step_fails_the_check(tmp_path: Path) -> None:
    """A bootstrap command that exits non-zero is a failure, whatever the hook does."""
    clone, sha = checkout_repo(tmp_path, b"#!/bin/sh\nexit 1\n", install=b"raise SystemExit(1)\n")

    result = flip.clean_checkout(clone, sha, python=sys.executable)

    assert "a bootstrap command exited non-zero" in result.failures


# --- the trailer axis ---------------------------------------------------------

TRAILER: Final = b"Co-authored-by: Synthetic <synthetic@example.invalid>"


def trailer_repo(tmp_path: Path, *messages: bytes) -> tuple[Any, str]:
    """A repository whose commits carry ``messages`` in order."""
    repo = flip.ControlRepo(tmp_path / "trailers")
    tip = ""
    for index, message in enumerate(messages):
        tip = repo.commit({"README.md": str(index).encode("ascii")}, message)
    return repo, tip


def test_s1_passes_strippable_trailers_as_an_early_warning(tmp_path: Path) -> None:
    """At S1 the hits ARE the population S7a removes; they are recorded, not failed."""
    repo, tip = trailer_repo(tmp_path, b"a\n", b"s\n\nbody\n\n" + TRAILER + b"\n")

    result = flip.trailer_axis(repo.path, tip, "s1")

    assert result.failures == []
    assert result.counts["commits with a hit"] == 1


def test_s1_fails_on_zero_trailers(tmp_path: Path) -> None:
    """A census that found nothing at S1 measured nothing."""
    repo, tip = trailer_repo(tmp_path, b"a\n")

    result = flip.trailer_axis(repo.path, tip, "s1")

    assert "S1 found zero trailers, so the census measured nothing" in result.failures


def test_s1_fails_on_a_trailer_the_strip_would_leave(tmp_path: Path) -> None:
    """A trailer that is not the final line after a blank line survives S7a."""
    repo, tip = trailer_repo(tmp_path, b"s\n\n" + TRAILER + b"\n\nprose after\n")

    result = flip.trailer_axis(repo.path, tip, "s1")

    assert "a trailer S7a's strip would leave behind" in result.failures


def test_s8_fails_on_any_trailer(tmp_path: Path) -> None:
    """After the strip, one trailer is one too many."""
    repo, tip = trailer_repo(tmp_path, b"s\n\nbody\n\n" + TRAILER + b"\n")

    result = flip.trailer_axis(repo.path, tip, "s8", (tip, 1))

    assert "a trailer is reachable from REF after the strip" in result.failures


def test_s8_without_its_baseline_control_is_a_skip(tmp_path: Path) -> None:
    """The phase7 S8 control is the census over the pre-S7a baseline; absent, it is unmeasured."""
    repo, tip = trailer_repo(tmp_path, b"clean\n")

    result = flip.trailer_axis(repo.path, tip, "s8")

    assert result.skips == 1
    assert not result.passed


def test_s8_passes_a_clean_tip_with_a_matching_baseline(tmp_path: Path) -> None:
    """The baseline ref returns the count it recorded, and the tip carries none."""
    base_repo, base = trailer_repo(tmp_path, b"s\n\nbody\n\n" + TRAILER + b"\n")
    tip = base_repo.commit({"README.md": b"after\n"}, b"clean\n")
    fresh = flip.ControlRepo(tmp_path / "rewritten")
    clean_tip = fresh.commit({"README.md": b"x\n"}, b"clean\n")
    flip.git(fresh.path, ["fetch", "-q", str(base_repo.path), f"{base}:refs/preserve/base"])

    passing_result = flip.trailer_axis(fresh.path, clean_tip, "s8", ("refs/preserve/base", 1))
    wrong_count = flip.trailer_axis(fresh.path, clean_tip, "s8", ("refs/preserve/base", 2))

    assert tip
    assert passing_result.failures == []
    assert passing_result.skips == 0
    assert (
        "the S8 baseline census did not return its recorded non-zero count" in wrong_count.failures
    )


def test_the_trailer_control_finds_a_planted_trailer(tmp_path: Path) -> None:
    """The census reads the planted line through the same walk."""
    assert flip.control_trailer(tmp_path)


# --- the result object --------------------------------------------------------


@pytest.mark.parametrize(
    ("control", "skips", "failures", "expected"),
    [
        (True, 0, [], True),
        (False, 0, [], False),
        (True, 1, [], False),
        (True, 0, ["x"], False),
    ],
    ids=["pass", "no-control", "skip", "failure"],
)
def test_a_check_passes_only_with_its_control_no_skip_and_no_failure(
    control: bool, skips: int, failures: list[str], expected: bool
) -> None:
    """The three conditions ADR 0025 decision item 7 puts on exit 0, per check."""
    result = flip.CheckResult("1", "x", control=control, skips=skips, failures=failures)

    assert result.passed is expected
