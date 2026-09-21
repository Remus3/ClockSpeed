"""CS-946 - the pre-commit gate's lint invocation resolves the project's globs.

Split out of tests/test_precommit_gate.py, which sat inside the tests-tree size
approach band. The fixtures come from that module by import, which is the
relocation the band's own arm prescribes.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.test_precommit_gate import (
    GATE,
    TRACKED_PRE_COMMIT,
    base_env,
    git,
    git_with_env,
    load_gate,
    run_gate,
)

# --------------------------------------------------------------------------
# CS-946 - a format exclusion the project declares must mean the same thing
#          to this gate as it does to CI
# --------------------------------------------------------------------------
#
# THE MEASUREMENT THIS SECTION RESTS ON, reproducible in one minute with ruff
# 0.16.x and nothing else:
#
#   ruff format --check --config <project pyproject> <the vendored file>
#       run from the repository root            -> exit 0, excluded
#   the IDENTICAL BYTES copied to <tmp>/u0000/<basename>, same config, same cwd
#                                               -> exit 1, "Would reformat"
#   the same bytes at <tmp>/<repo-relative path>, cwd=<tmp>, same config
#                                               -> exit 0, excluded again
#   a malformed file at <tmp>/notexcluded/bad.py, cwd=<tmp>, same config
#                                               -> exit 1, still refused
#
# RUFF RESOLVES `exclude` AND `per-file-ignores` AGAINST THE INVOCATION'S
# WORKING DIRECTORY. Not against the config file's location, and not against
# an absolute path. `force-exclude = true` is necessary and is not sufficient:
# it makes an explicitly named path obey the exclusion at all, but WHICH name
# the glob is matched against is still decided by cwd. So a gate that flattens
# every staged unit into <tmp>/u0000/<basename> and invokes ruff from the
# repository root hands ruff a name no project glob can ever match, and every
# repo-relative exclusion and ignore the project declares silently evaporates.
#
# Before CS-946 that was written off as "more advisory findings, never fewer,
# and it cannot change what blocks". `ruff format --check` is a SECOND
# BLOCKING BAND that reassurance never covered: its verdict is the process
# exit code, and an exclusion that does not reach it turns into a FORMAT block
# on a file the project has deliberately exempted.

VENDOR_PINNED = b'"""Pinned upstream. Not ours to reformat."""\n\nVALUE = [1,2,3]\n'
VENDOR_OTHER_DIRTY = b'"""Ours, and malformed."""\n\nOTHER = [4,5,6]\n'
VENDOR_IGNORED_NOTE = b"NOTED = 1\n"
VENDOR_NOTICED_NOTE = b"NOTICED = 1\n"

# force-exclude plus ONE format exclusion plus ONE per-file-ignore, which is
# the smallest config that can tell the three failure modes apart: an
# exclusion that does not reach the formatter, an ignore that does not reach
# the linter, and a gate that simply stopped checking.
VENDOR_PYPROJECT = """\
[tool.ruff]
line-length = 100
force-exclude = true

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "D"]

[tool.ruff.lint.per-file-ignores]
"ignored/noted.py" = ["D100"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
exclude = ["vendored/pinned.py"]
"""

# The two process working directories every arm below is run from. "outside
# any repository" is NOT one of them, and that is a property of the gate
# rather than an omission: mode_staged calls repo_root() with no cwd, so it
# reads THE PROCESS's directory, and a --staged run outside a repository has
# no index to read at all. A nested subdirectory is the second cwd because it
# is the one that actually exercises the risk this item introduces - the fix
# hands ruff a cwd of its own, so any surviving os.getcwd() arithmetic in the
# parent changes answer with depth. The --files half of the question gets its
# own arm below.
GATE_CWDS = ("root", "nested")


@pytest.fixture
def vendor_exclude_repo(tmp_path: Path) -> Path:
    """A throwaway repo whose own config excludes one path from the formatter.

    Wired to the REAL .githooks/pre-commit and carrying a base commit, so
    "HEAD is unchanged" is a real assertion. The gate and the config are left
    untracked, exactly as tracked_hook_repo leaves them, so they never join
    the list of units an arm checks.
    """
    root = tmp_path / "vendorexcluderepo"
    root.mkdir()
    assert git("init", "-q", "-b", "main", cwd=root).returncode == 0
    git("config", "user.email", "gate@example.invalid", cwd=root)
    git("config", "user.name", "Gate Test", cwd=root)
    git("config", "commit.gpgsign", "false", cwd=root)

    (root / "seed.txt").write_bytes(b"seed\n")
    assert git("add", "seed.txt", cwd=root).returncode == 0
    assert git("commit", "-q", "-m", "seed", cwd=root).returncode == 0

    (root / "tools").mkdir()
    shutil.copy2(GATE, root / "tools" / "precommit_gate.py")
    (root / "pyproject.toml").write_bytes(VENDOR_PYPROJECT.encode("ascii"))
    (root / "nested" / "deeper").mkdir(parents=True)

    hooks = root / "gate-hooks"
    hooks.mkdir()
    installed = hooks / "pre-commit"
    installed.write_bytes(TRACKED_PRE_COMMIT.read_bytes())
    installed.chmod(0o755)
    assert git("config", "core.hooksPath", "gate-hooks", cwd=root).returncode == 0
    readback = git("config", "--get", "core.hooksPath", cwd=root)
    assert readback.stdout.strip() == "gate-hooks", "core.hooksPath did not take"
    return root


def gate_cwd(root: Path, which: str) -> Path:
    """Resolve one of GATE_CWDS to a real directory inside the throwaway repo."""
    return root if which == "root" else root / "nested" / "deeper"


def stage_one(root: Path, name: str, body: bytes) -> None:
    """Write one file and stage it, with no commit attempted."""
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    assert git("add", name, cwd=root).returncode == 0


def format_lines(stderr: str) -> list[str]:
    """Every FORMAT diagnostic line, which is the band this section grades.

    Diagnostics go to stderr and notes go to stdout, so reading stderr alone
    keeps the --verbose channels out of the assertion.
    """
    return [line for line in stderr.splitlines() if " FORMAT " in line]


def require_ruff() -> None:
    """Skip when ruff is absent - run_ruff returns before any of this fires."""
    if load_gate().ruff_command() is None:
        pytest.skip("ruff is not installed, so run_ruff returns before the format check")


@pytest.mark.parametrize("which", GATE_CWDS)
def test_a_format_excluded_path_is_not_format_blocked_under_staged(
    vendor_exclude_repo: Path, tmp_path: Path, which: str
) -> None:
    """ARM 1. The exclusion the project declares must reach the staged check.

    RED BEFORE THE FIX, and red for exactly one reason: stage_for_lint wrote
    the index bytes to <tmp>/u0000/pinned.py and ruff was invoked from the
    gate's own cwd, so the glob vendored/pinned.py matched nothing and the
    formatter refused a file the project exempted. The assertion names that
    path so a broken fixture - a config that did not resolve, a file that was
    never staged - cannot be mistaken for the defect.
    """
    require_ruff()
    stage_one(vendor_exclude_repo, "vendored/pinned.py", VENDOR_PINNED)

    result = run_gate(
        "--staged",
        env=base_env(tmp_path),
        cwd=gate_cwd(vendor_exclude_repo, which),
    )

    named = [line for line in format_lines(result.stderr) if "vendored/pinned.py" in line]
    assert not named, (
        "the project excludes vendored/pinned.py from the formatter and the "
        "staged gate refused it anyway: " + repr(named)
    )
    assert result.returncode == 0, (
        f"exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.parametrize("which", GATE_CWDS)
def test_a_non_excluded_malformed_path_still_blocks_beside_the_excluded_one(
    vendor_exclude_repo: Path, tmp_path: Path, which: str
) -> None:
    """ARM 2. DOES-NOT-WEAKEN. Green before the fix and green after it.

    Arm 1 alone ships a hole: an implementation that simply stopped running
    `ruff format --check` under --staged, or stopped blocking on its verdict,
    passes arm 1 perfectly. This arm stages a SECOND malformed file at a path
    no exclusion names, in the same index, in the same invocation, and
    requires the refusal to survive - through a REAL git commit, graded on
    HEAD rather than on the gate's exit code.

    THE EXCLUSION HALF OF THIS SCENARIO IS A SEPARATE ARM, deliberately. An
    arm that is red before the fix and green after it cannot also serve as the
    control that proves the fix took nothing away, because a does-not-weaken
    control is only worth anything if it was green on the OLD code too. The
    arm immediately below drives the identical staging and asserts the other
    half.
    """
    require_ruff()
    stage_one(vendor_exclude_repo, "vendored/pinned.py", VENDOR_PINNED)
    stage_one(vendor_exclude_repo, "other/dirty.py", VENDOR_OTHER_DIRTY)

    result = run_gate(
        "--staged",
        env=base_env(tmp_path),
        cwd=gate_cwd(vendor_exclude_repo, which),
    )

    assert result.returncode == 1, (
        f"a malformed non-excluded file did not block\nstdout:\n{result.stdout}"
    )
    named = format_lines(result.stderr)
    assert any("other/dirty.py" in line for line in named), (
        "no FORMAT diagnostic named the non-excluded file: " + repr(named)
    )

    before = git("rev-parse", "HEAD", cwd=vendor_exclude_repo).stdout.strip()
    assert before, "there is no base commit, so HEAD-unchanged would prove nothing"
    attempt = git_with_env(
        "commit",
        "-m",
        "CS-946: stage a malformed non-excluded file",
        cwd=vendor_exclude_repo,
        env=base_env(tmp_path),
    )
    after = git("rev-parse", "HEAD", cwd=vendor_exclude_repo).stdout.strip()
    assert after == before, (
        "HEAD MOVED, so the real hook let a format violation through: "
        + attempt.stdout
        + attempt.stderr
    )


@pytest.mark.parametrize("which", GATE_CWDS)
def test_the_excluded_path_stays_unnamed_while_its_neighbour_blocks(
    vendor_exclude_repo: Path, tmp_path: Path, which: str
) -> None:
    """ARM 2, the half that was RED. The exclusion holds under a real refusal.

    Arm 1 proves the exclusion reaches a run that otherwise passes. This
    proves it reaches a run that BLOCKS, which is the case that matters: a fix
    that made the format check agree with the project config only when there
    was nothing to report would be indistinguishable from arm 1's point of
    view. The blocking neighbour is asserted first so a run that checked
    nothing at all cannot satisfy the exclusion assertion vacuously.
    """
    require_ruff()
    stage_one(vendor_exclude_repo, "vendored/pinned.py", VENDOR_PINNED)
    stage_one(vendor_exclude_repo, "other/dirty.py", VENDOR_OTHER_DIRTY)

    result = run_gate(
        "--staged",
        env=base_env(tmp_path),
        cwd=gate_cwd(vendor_exclude_repo, which),
    )

    named = format_lines(result.stderr)
    assert any("other/dirty.py" in line for line in named), (
        "nothing blocked, so the exclusion assertion below would be vacuous: " + repr(named)
    )
    assert not any("vendored/pinned.py" in line for line in named), (
        "the excluded file was named after all: " + repr(named)
    )


@pytest.mark.parametrize("which", GATE_CWDS)
def test_a_repo_relative_per_file_ignore_suppresses_its_note_under_staged(
    vendor_exclude_repo: Path, tmp_path: Path, which: str
) -> None:
    """ARM 3. The same cwd resolution decides per-file-ignores, not just exclude.

    The pairing is the non-vacuity control: ignored/noted.py is named by the
    project's per-file-ignores and noticed/noted.py is not, the two files
    are byte-equivalent in the only respect that matters, and both are staged
    in the SAME invocation. A run that simply stopped linting loses both
    notes and fails on the second assertion.
    """
    require_ruff()
    stage_one(vendor_exclude_repo, "ignored/noted.py", VENDOR_IGNORED_NOTE)
    stage_one(vendor_exclude_repo, "noticed/noted.py", VENDOR_NOTICED_NOTE)

    result = run_gate(
        "--staged",
        "--verbose",
        env=base_env(tmp_path),
        cwd=gate_cwd(vendor_exclude_repo, which),
    )

    notes = [line for line in result.stdout.splitlines() if "D100" in line]
    assert any("noticed/noted.py" in line for line in notes), (
        "the control note is missing, so this arm cannot tell an applied "
        "ignore from a lint that never ran: " + repr(notes)
    )
    assert not any("ignored/noted.py" in line for line in notes), (
        "the project's per-file-ignore did not reach the staged lint: " + repr(notes)
    )


def test_the_staged_verdict_does_not_change_with_the_process_directory(
    vendor_exclude_repo: Path, tmp_path: Path
) -> None:
    """ARM 4. One run of each cwd, compared against each other directly.

    The parametrized arms above each assert their own verdict, which catches
    a cwd that changes the ANSWER. This one catches a cwd that changes the
    LABELS - a relative name leaking out of the staging directory into the
    parent's arithmetic and being attributed to the wrong unit, or to no unit
    at all, while the exit code stays right.
    """
    require_ruff()
    stage_one(vendor_exclude_repo, "vendored/pinned.py", VENDOR_PINNED)
    stage_one(vendor_exclude_repo, "other/dirty.py", VENDOR_OTHER_DIRTY)
    stage_one(vendor_exclude_repo, "ignored/noted.py", VENDOR_IGNORED_NOTE)
    stage_one(vendor_exclude_repo, "noticed/noted.py", VENDOR_NOTICED_NOTE)

    seen: dict[str, tuple[int, list[str]]] = {}
    for which in GATE_CWDS:
        result = run_gate(
            "--staged",
            env=base_env(tmp_path),
            cwd=gate_cwd(vendor_exclude_repo, which),
        )
        seen[which] = (result.returncode, sorted(format_lines(result.stderr)))

    assert seen["root"][0] == seen["nested"][0], seen
    assert seen["root"][1] == seen["nested"][1], seen
    assert seen["root"][1], "no FORMAT diagnostic at all, so this arm is vacuous"


def test_a_files_run_outside_any_repository_still_skips_the_format_check(
    vendor_exclude_repo: Path, tmp_path: Path
) -> None:
    """ARM 4, the --files half, and it PINS A PRE-EXISTING DIVERGENCE.

    --files is the only mode that can run outside a repository at all, and
    there main() cannot resolve a root, so ruff_config_args returns empty and
    run_ruff_format takes the documented R1 skip. That is older than CS-946
    and is NOT what this item changed; it is asserted here so a later reader
    cannot mistake it for a hole the cwd work opened. The same paths run from
    inside the repository DO get the format verdict, which is the control that
    stops this arm passing for the wrong reason.
    """
    require_ruff()
    (vendor_exclude_repo / "other").mkdir(parents=True, exist_ok=True)
    target = vendor_exclude_repo / "other" / "dirty.py"
    target.write_bytes(VENDOR_OTHER_DIRTY)

    outside = run_gate("--files", str(target), env=base_env(tmp_path), cwd=tmp_path)
    inside = run_gate("--files", str(target), env=base_env(tmp_path), cwd=vendor_exclude_repo)

    assert not format_lines(outside.stderr), (
        "a --files run outside any repository produced a FORMAT verdict, so "
        "the R1 skip is gone: " + outside.stderr
    )
    assert format_lines(inside.stderr), (
        "the same file inside the repository produced no FORMAT verdict, so "
        "the arm above passes for the wrong reason: " + inside.stderr
    )


def test_the_gate_carries_no_path_literal_and_no_vendored_carve_out() -> None:
    """ARM 6. The repair is a resolution fix, never an allowlist.

    CONVENTIONS.md section 15.1: a guard can be green while self-excusing. The
    cheapest wrong fix for CS-946 is a carve-out naming the one vendored file,
    which would be exactly that. The gate must know nothing about which paths
    the project exempts; the PROJECT CONFIG owns that, and the gate's only job
    is to invoke ruff so the config can be read the way CI reads it.
    """
    source = GATE.read_bytes().decode("ascii")

    assert "NO path allowlist of any kind" in source, (
        "the header sentence that commits this gate to having no allowlist is gone"
    )
    assert "slots" not in source, (
        "the gate names the vendored file, which is an allowlist wearing a different hat"
    )
    for literal in (
        ":" + chr(92) + "Clockspeed",
        ":/Clockspeed",
        "ops/loop",
        "ops" + chr(92) * 2 + "loop",
    ):
        assert literal not in source, "the gate carries a repo path literal: " + literal
