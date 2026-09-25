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

    def runner(*args: object) -> list[object]:
        scratch = args[3]
        assert isinstance(scratch, Path)
        seen.append(scratch)
        return [passing()]

    flip.main(["HEAD", "--stage", "s8", "--repo", str(repo)], runner=runner)

    (scratch,) = seen
    inside = scratch.resolve().is_relative_to((repo / ".git").resolve())
    assert inside
    assert not scratch.exists()


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


def test_the_doc_sweep_control_adds_a_finding(tmp_path: Path) -> None:
    """An orphan markdown file adds a finding to the sweep's own CLI."""
    assert flip.control_doc_sweep(tmp_path)


def test_a_doc_sweep_skip_fails_the_check(tmp_path: Path) -> None:
    """A URL the sweep never fetches is a skip, and a skip fails - never a network call."""
    repo = flip.ControlRepo(tmp_path / "docs")
    repo.commit({"README.md": b"# x\n\nSee <https://example.wiki.gg/wiki/Page>.\n"}, b"x\n")
    flip.git(repo.path, ["checkout", "-q", "-f", "main"], env=repo.env)

    result = flip.doc_sweep(repo.path)
    result.control = True

    assert result.skips >= 1
    assert not result.passed


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
