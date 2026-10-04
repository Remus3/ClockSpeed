"""CS-704 - a trailer that reaches a branch by ANY route is caught by CI, not by the hook.

WHAT THIS GRADES. ``.githooks/commit-msg`` refuses the trailer-shaped line on the
commands that fire it, and CS-702 is forward-only by construction. The CS-702
bypass adversary landed a trailer git itself recognises through routes that never
fire that hook: ``git rebase`` on both backends, ``git am``, ``git cherry-pick``,
``git revert``, ``git commit --no-verify``, a fresh clone that was never
bootstrapped (``core.hooksPath`` is machine-local and never cloned), and a
remapped ``core.commentChar`` or ``core.commentString``, which moves the comment
leader the hook skips onto the trailer itself. The ledger's CS-704 ROUTE puts the
catcher in ``.github/workflows/tier1.yml``: a step that refuses unless a member
of the pinned accept set - the baseline or its CS-700 S7a image - is an ancestor
of HEAD, then runs ``tools/trailer_census.py`` over ``baseline..HEAD``. The
trailer SHAPE is owned by the paragraph headed THE TRAILER-SHAPED CENSUS in
``docs/item_notes/phase7.md`` and computed only by that tool; nothing here
restates it.

THE STEP IS EXECUTED, NEVER COPIED. Every arm reads the step's ``run`` text out of
the workflow by a YAML parse, substitutes the throwaway repository's own baseline
for the granted one, and runs it the way GitHub runs a ``shell: bash`` step -
``bash --noprofile --norc -eo pipefail`` - with the throwaway repository as its
working directory. The substitution is ASSERTED to have landed: one that never
applied would run the step against a SHA no throwaway repository holds, and every
arm would then go red, or a mutated step green, for that reason alone.

EACH ROUTE PRODUCES A NEW COMMIT AND THE ARM DEMANDS THAT ONE BY NAME. Before the
step runs, git's own ``interpret-trailers --parse`` confirms the route's product
carries a trailer git recognises, so a route that silently dropped the line fails
its own precondition rather than passing as "caught". The step must then exit
non-zero AND name the product's SHA on a ``hit`` line - a non-zero exit alone is
also what a broken step prints.

THE RANGE IS GRADED, NOT THE TIP. The rebase, am and cherry-pick arms land a
clean commit on top of the route's product, and two arms put a merge in the
range - one with the trailer on the merged side branch, one on the merge itself -
so a step that censused only HEAD, or skipped a range holding a merge, is red.

THE CENSUS RUNS FROM A COPY. The throwaway repository's root commit carries
byte-copies of ``tools/trailer_census.py`` and the sibling it imports, taken at
test time, because the step names the tool by a path relative to the checkout.
The copy is the shipped bytes; a mutated census is a mutated copy.

WHAT RUNS NO HOOK. Two arms install a SYNTHETIC ``commit-msg`` hook that refuses
every message - never the shipped one - so ``--no-verify`` and the unbootstrapped
clone are each shown to bypass a hook that is demonstrably live (a control commit
through it is refused and HEAD does not move). The other routes need no hook: the
step is the catcher under test, and it reads the object store, not the hook.

RESOURCE LIFETIME. Every subprocess carries a timeout. Every repository lives
under ``tmp_path``, which the suite's retention policy removes on a pass. No arm
touches a remote other than a local clone inside ``tmp_path``, and none pushes.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
WORKFLOW: Final = REPO_ROOT / ".github" / "workflows" / "tier1.yml"

#: The job that hosts the step, and the step's name. Addressed BY NAME, as
#: tests/test_tier1_budget.py addresses its steps.
HOST_JOB: Final = "save"
STEP_NAME: Final = "Trailer census since the baseline"

#: The baseline the 2026-09-25 grant pins, and the shape every substitute takes.
GRANTED_BASELINE: Final = "c6f36874194aeed450c6d75a93be883f72c8f45e"

#: Its image under the CS-700 S7a rewrite, admitted by the 2026-10-04 CS-704
#: ruling in docs/LEDGER.md. The step accepts EXACTLY these two: it passes when
#: at least one is an ancestor of HEAD and refuses when neither is.
GRANTED_IMAGE: Final = "b7b4a2c4b71c942bb759aa2b4f3b9ba906ddc1ec"

#: The accept set, as the ruling states it.
ACCEPT_SET: Final = frozenset({GRANTED_BASELINE, GRANTED_IMAGE})

#: A stand-in for the image that no throwaway repository holds - what every arm
#: graded on unrewritten history substitutes, as a pre-S7a checkout lacks it.
ABSENT_IMAGE: Final = "fedcba9876543210fedcba9876543210fedcba98"

#: The tool the step must call, and the one sibling it imports.
CENSUS_TOOL: Final = "tools/trailer_census.py"
CENSUS_FILES: Final = (CENSUS_TOOL, "tools/toolpath.py")

#: Seconds one git call, one hook-bearing commit or one step run may take. This
#: bounds a hang; it does not police speed.
TIMEOUT: Final = 120

BASH: Final = shutil.which("bash")
GIT: Final = shutil.which("git")

needs_tools = pytest.mark.skipif(
    BASH is None or GIT is None,
    reason="no bash or no git on PATH; the census step was NOT executed",
)

#: The trailer value every planted line carries. Synthetic, reserved domain.
VALUE: Final = "Someone <someone@example.invalid>"

#: The planted line, built so no source line of this module is itself one.
TRAILER: Final = "Co-authored-by: " + VALUE

#: A commit-msg hook that refuses EVERY message. Synthetic - never the shipped one.
REFUSE_ALL_HOOK: Final = b"#!/bin/sh\necho synthetic commit-msg refusal >&2\nexit 1\n"

#: An editor that appends the trailer paragraph to the message file it is handed.
APPEND_EDITOR: Final = (
    "import sys\n"
    "path = sys.argv[-1]\n"
    "with open(path, 'rb') as handle:\n"
    "    body = handle.read().rstrip(b'\\n')\n"
    "with open(path, 'wb') as handle:\n"
    "    handle.write(body + b'\\n\\n' + sys.argv[1].encode('ascii') + b'\\n')\n"
)


# --- the step, read out of the workflow ---------------------------------------


def workflow_jobs() -> dict[str, Any]:
    """The workflow's jobs mapping, parsed - never a substring search."""
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(document, dict), "tier1.yml did not parse to a mapping"
    jobs = document.get("jobs")
    assert isinstance(jobs, dict), "tier1.yml declares no jobs mapping"
    return jobs


def host_steps() -> list[dict[str, Any]]:
    """Every step of the hosting job, in order."""
    job = workflow_jobs().get(HOST_JOB)
    assert isinstance(job, dict), f"tier1.yml declares no job {HOST_JOB!r}"
    steps = job.get("steps")
    assert isinstance(steps, list), f"job {HOST_JOB!r} declares no step list"
    return [step for step in steps if isinstance(step, dict)]


def step_script() -> str:
    """The census step's ``run`` text, exactly as the workflow ships it."""
    names = [str(step.get("name")) for step in host_steps()]
    matched = [step for step in host_steps() if step.get("name") == STEP_NAME]
    assert len(matched) == 1, f"expected one step {STEP_NAME!r} in {HOST_JOB!r}; saw {names}"
    script = matched[0].get("run")
    assert isinstance(script, str), f"step {STEP_NAME!r} declares no run script"
    return script


def substituted(baseline: str, image: str = ABSENT_IMAGE) -> str:
    """The step's script with ``baseline`` and ``image`` in place of the granted pair.

    Raises:
        AssertionError: When either granted SHA does not appear exactly once, or
            a substitute did not land - a substitution that never applied looks
            exactly like a step that refuses every repository.
    """
    script = step_script()
    for granted in (GRANTED_BASELINE, GRANTED_IMAGE):
        occurrences = script.count(granted)
        assert occurrences == 1, f"the step names {granted} {occurrences} times, not once"
    rewritten = script.replace(GRANTED_BASELINE, baseline).replace(GRANTED_IMAGE, image)
    landed = (
        rewritten.count(baseline),
        rewritten.count(image),
        rewritten.count(GRANTED_BASELINE),
        rewritten.count(GRANTED_IMAGE),
    )
    assert landed == (1, 1, 0, 0), f"the accept-set substitution did not land: {landed}"
    return rewritten


# --- throwaway repositories ---------------------------------------------------


def isolated_env(tmp_path: Path) -> dict[str, str]:
    """An environment with no inherited git location, config or identity."""
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    for role in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{role}_NAME"] = "Synthetic"
        env[f"GIT_{role}_EMAIL"] = "synthetic@example.invalid"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


@dataclass(repr=False)
class Repo:
    """A throwaway repository and the environment its git runs under.

    ``repr=False`` on purpose: the generated repr would render the whole
    environment and a temp path into any assertion that reached an instance.
    Every assertion below binds its value to a scalar first as well.
    """

    path: Path
    env: dict[str, str]
    counter: int = 0

    def run(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run one git command here and return the completed process, unchecked."""
        assert GIT is not None, "guarded by needs_tools"
        return subprocess.run(
            [GIT, *args],
            cwd=self.path,
            env=self.env if env is None else env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        """Run one git command here, require success, return stripped stdout."""
        completed = self.run(*args, env=env)
        code = completed.returncode
        assert code == 0, f"git {args[0]} exited {code}"
        return completed.stdout.strip()

    def head(self) -> str:
        """HEAD's full object name."""
        return self.git("rev-parse", "HEAD")

    def touch(self, name: str = "work.txt") -> None:
        """Change one tracked file, so the next commit has content."""
        self.counter += 1
        (self.path / name).write_bytes(f"line {self.counter}\n".encode("ascii"))
        self.git("add", "-A")

    def commit(
        self, subject: str, *extra: str, trailer: bool = False, name: str = "work.txt"
    ) -> str:
        """Commit a content change with ``git commit -F`` and return the new HEAD."""
        self.touch(name)
        body = subject + "\n\n" + ("body\n\n" + TRAILER if trailer else "body") + "\n"
        message = self.path.parent / f"{self.path.name}-message.txt"
        message.write_bytes(body.encode("ascii"))
        self.git("commit", "-q", *extra, "-F", str(message))
        return self.head()


def make_repo(tmp_path: Path, *, trailer_before_baseline: bool = False) -> tuple[Repo, str]:
    """A repository holding the census tool, a baseline, and ``main`` at the baseline.

    Returns:
        The repository and its baseline commit's full object name.
    """
    env = isolated_env(tmp_path)
    path = tmp_path / "repo"
    path.mkdir()
    repo = Repo(path, env)
    repo.git("init", "-q", "-b", "main")
    for relative in CENSUS_FILES:
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / relative).read_bytes())
    repo.commit("CS-1 - root, carrying the census tool")
    repo.commit("CS-2 - before the baseline", trailer=trailer_before_baseline)
    baseline = repo.commit("CS-3 - the baseline")
    return repo, baseline


def run_step(
    repo: Repo, baseline: str, tmp_path: Path, image: str = ABSENT_IMAGE
) -> subprocess.CompletedProcess[str]:
    """Execute the shipped step, accept set substituted, exactly as the runner would."""
    assert BASH is not None, "guarded by needs_tools"
    script = tmp_path / f"step-{repo.path.name}.sh"
    script.write_bytes(substituted(baseline, image).encode("ascii"))
    env = dict(repo.env)
    workflow_env = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8")).get("env") or {}
    env.update({str(key): str(value) for key, value in workflow_env.items()})
    # `python` on the step's PATH is the interpreter running this suite, as
    # setup-python makes it on the runner.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [BASH, "--noprofile", "--norc", "-eo", "pipefail", str(script)],
        cwd=repo.path,
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def git_sees_trailer(repo: Repo, sha: str) -> bool:
    """Whether git's own trailer parser reads the planted trailer off ``sha``.

    The comment leader is pinned back to ``#`` for THIS read only, so a route
    that remapped it in the repository is still graded on the bytes it wrote.
    """
    message = repo.git("log", "-1", "--format=%B", sha)
    assert GIT is not None, "guarded by needs_tools"
    parsed = subprocess.run(
        [GIT, "-c", "core.commentChar=#", "interpret-trailers", "--parse"],
        cwd=repo.path,
        env=repo.env,
        input=message + "\n",
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    code = parsed.returncode
    assert code == 0, f"interpret-trailers exited {code}"
    return TRAILER in parsed.stdout.splitlines()


def step_outcome(
    repo: Repo, baseline: str, tmp_path: Path, image: str = ABSENT_IMAGE
) -> tuple[int, str]:
    """The step's exit code and stdout, as scalars an assertion may render."""
    result = run_step(repo, baseline, tmp_path, image)
    return result.returncode, result.stdout


def is_ancestor(repo: Repo, commit: str) -> int:
    """``git merge-base --is-ancestor COMMIT HEAD``'s exit code."""
    return repo.run("merge-base", "--is-ancestor", commit, "HEAD").returncode


def assert_caught(repo: Repo, baseline: str, product: str, tmp_path: Path) -> None:
    """The route's product carries a real trailer, and the step refuses naming it."""
    seen = git_sees_trailer(repo, product)
    assert seen, "the route dropped the trailer; it proves nothing"
    reachable = is_ancestor(repo, product)
    assert reachable == 0, "the route's product is not on HEAD, so the step never walks it"
    code, stdout = step_outcome(repo, baseline, tmp_path)
    hits = [line for line in stdout.splitlines() if line.startswith("hit ")]
    verdict = (code != 0, f"hit {product}" in hits)
    assert verdict == (True, True), (
        f"the step did not catch the route's product: exit {code}, hits {hits}, stdout {stdout!r}"
    )


def install_refusing_hook(repo: Repo, hooks: Path) -> None:
    """Point ``core.hooksPath`` at a synthetic hook that refuses every message."""
    hooks.mkdir()
    hook = hooks / "commit-msg"
    hook.write_bytes(REFUSE_ALL_HOOK)
    hook.chmod(0o755)
    repo.git("config", "core.hooksPath", hooks.as_posix())


def assert_hook_refuses(repo: Repo) -> None:
    """Control: a plain commit through the synthetic hook is refused and HEAD holds."""
    before = repo.head()
    repo.touch()
    message = repo.path.parent / f"{repo.path.name}-control.txt"
    message.write_bytes(("CS-9 - control\n\n" + TRAILER + "\n").encode("ascii"))
    code = repo.run("commit", "-q", "-F", str(message)).returncode
    after = repo.head()
    assert (code != 0, after) == (True, before), (
        "the synthetic hook did not refuse, so the bypass below proves nothing"
    )


def bury(repo: Repo, product: str) -> None:
    """Land a clean commit on top of ``product``, so the trailer is NOT on the tip.

    A step that censused only HEAD would pass every arm whose trailer sits on the
    tip; burying the route's product is what makes the RANGE the thing graded.
    """
    tip = repo.commit("CS-10 - a clean commit lands after the trailer")
    parent = repo.git("rev-parse", "HEAD~1")
    assert (tip != product, parent) == (True, product), "the product is still the tip"


def topic_with_trailer(repo: Repo, baseline: str) -> str:
    """A topic branch off the baseline carrying one trailer commit; main then advances.

    Returns:
        The ORIGINAL trailer commit, which no route below leaves reachable from HEAD.
    """
    repo.git("checkout", "-q", "-b", "topic", baseline)
    original = repo.commit("CS-5 - the topic change", trailer=True, name="topic.txt")
    repo.git("checkout", "-q", "main")
    repo.commit("CS-6 - main moves on")
    return original


# --- the step's shape in the workflow -----------------------------------------


def test_the_step_runs_after_a_full_history_checkout_and_the_interpreter() -> None:
    """The baseline must be IN the checkout, and ``python`` must exist, before the step.

    A shallow checkout holds no baseline, so the ancestor check would refuse every
    push - loud, but a red lane for no defect. ``fetch-depth: 0`` is what makes
    the baseline present.
    """
    names = [str(step.get("name")) for step in host_steps()]
    uses = [str(step.get("uses", "")) for step in host_steps()]
    at = names.index(STEP_NAME)
    checkout = next(index for index, used in enumerate(uses) if used.startswith("actions/checkout"))
    python = next(
        index for index, used in enumerate(uses) if used.startswith("actions/setup-python")
    )
    depth = (host_steps()[checkout].get("with") or {}).get("fetch-depth")
    assert (depth, checkout < at, python < at) == (0, True, True), (
        f"job {HOST_JOB!r}: fetch-depth {depth!r}, steps {names}"
    )


def test_the_step_calls_the_census_tool_and_never_excuses_an_empty_walk() -> None:
    """The count comes ONLY from the census tool, and its zero-walk refusal stands.

    ``--allow-empty`` would turn the census's refusal of a zero-commit walk into
    a clean verdict. The step handles the one empty range it can meet - HEAD is
    the baseline - by name, so every other empty walk must still refuse.
    """
    script = step_script()
    calls = [
        shlex.split(line.split("||")[0])
        for line in script.splitlines()
        if CENSUS_TOOL in line and not line.lstrip().startswith("#")
    ]
    assert calls == [["python", CENSUS_TOOL, "${BASELINE}..HEAD"]], (
        f"the step must call the census exactly once, with the range and NO option - an"
        f" argparse abbreviation of --allow-empty is still that option: {calls}"
    )
    assert "continue-on-error" not in script, "the step makes its own failure advisory"


# --- every named route is caught ------------------------------------------------


@needs_tools
@pytest.mark.parametrize("backend", ["--merge", "--apply"])
def test_a_rebase_on_either_backend_is_caught(backend: str, tmp_path: Path) -> None:
    """``git rebase`` re-commits without the commit-msg hook, on both backends."""
    repo, baseline = make_repo(tmp_path)
    original = topic_with_trailer(repo, baseline)
    repo.git("checkout", "-q", "topic")
    repo.git("rebase", "-q", backend, "main")
    product = repo.head()
    left_behind = is_ancestor(repo, original)
    assert (product != original, left_behind) == (True, 1), (
        "the rebase did not rewrite the topic commit, so HEAD still holds the original"
    )
    bury(repo, product)
    assert_caught(repo, baseline, product, tmp_path)


@needs_tools
def test_git_am_is_caught(tmp_path: Path) -> None:
    """``git am`` applies a mailed patch, trailer and all, with no commit-msg hook."""
    repo, baseline = make_repo(tmp_path)
    original = topic_with_trailer(repo, baseline)
    patch = tmp_path / "topic.patch"
    mailed = repo.git("format-patch", "-1", "--stdout", original)
    patch.write_bytes(mailed.encode("ascii") + b"\n")
    repo.git("am", "-q", str(patch))
    product = repo.head()
    left_behind = is_ancestor(repo, original)
    assert (product != original, left_behind) == (True, 1), "am reproduced the original"
    bury(repo, product)
    assert_caught(repo, baseline, product, tmp_path)


@needs_tools
def test_git_cherry_pick_is_caught(tmp_path: Path) -> None:
    """``git cherry-pick`` copies the message onto a new commit through the sequencer."""
    repo, baseline = make_repo(tmp_path)
    original = topic_with_trailer(repo, baseline)
    repo.git("cherry-pick", original)
    product = repo.head()
    left_behind = is_ancestor(repo, original)
    assert (product != original, left_behind) == (True, 1), "the pick reproduced the original"
    bury(repo, product)
    assert_caught(repo, baseline, product, tmp_path)


@needs_tools
def test_git_revert_with_an_edited_message_is_caught(tmp_path: Path) -> None:
    """``git revert --edit``, the sequencer sibling the first enumeration missed."""
    repo, baseline = make_repo(tmp_path)
    reverted = repo.commit("CS-7 - a change to revert")
    editor = tmp_path / "append_trailer.py"
    editor.write_bytes(APPEND_EDITOR.encode("ascii"))
    env = dict(repo.env)
    env["GIT_EDITOR"] = f'"{Path(sys.executable).as_posix()}" "{editor.as_posix()}" "{TRAILER}"'
    repo.git("revert", "--edit", reverted, env=env)
    product = repo.head()
    parent = repo.git("rev-parse", "HEAD~1")
    subject = repo.git("log", "-1", "--format=%s")
    shape = (parent == reverted, subject.startswith("Revert "))
    assert shape == (True, True), f"the revert did not land on main: {shape}"
    assert_caught(repo, baseline, product, tmp_path)


@needs_tools
def test_commit_no_verify_is_caught(tmp_path: Path) -> None:
    """``git commit --no-verify`` skips a hook that is demonstrably live."""
    repo, baseline = make_repo(tmp_path)
    install_refusing_hook(repo, tmp_path / "hooks")
    assert_hook_refuses(repo)
    product = repo.commit("CS-8 - skips the hook", "--no-verify", trailer=True)
    assert_caught(repo, baseline, product, tmp_path)


@needs_tools
def test_an_unbootstrapped_clone_is_caught(tmp_path: Path) -> None:
    """A fresh clone carries no ``core.hooksPath``, so it runs no hook at all."""
    source, baseline = make_repo(tmp_path)
    install_refusing_hook(source, tmp_path / "hooks")
    assert_hook_refuses(source)
    clone_path = tmp_path / "clone"
    source.git("clone", "-q", "--no-hardlinks", str(source.path), str(clone_path))
    clone = Repo(clone_path, source.env)
    unset = clone.run("config", "--get", "core.hooksPath").returncode
    assert unset == 1, "the clone inherited core.hooksPath, so this is not the route"
    product = clone.commit("CS-8 - committed in a clone nobody bootstrapped", trailer=True)
    assert_caught(clone, baseline, product, tmp_path)


def comment_string_supported(repo: Repo) -> bool:
    """Whether this git reads ``core.commentString`` (added in git 2.45)."""
    probe = repo.run("-c", "core.commentString=//", "stripspace", "--strip-comments")
    return probe.returncode == 0


@needs_tools
@pytest.mark.parametrize(
    ("key", "leader"), [("core.commentChar", "C"), ("core.commentString", "Co")]
)
def test_a_remapped_comment_leader_is_caught(key: str, leader: str, tmp_path: Path) -> None:
    """A comment leader the trailer starts with makes a comment-skipping check skip it.

    ``git commit -F`` cleans up whitespace only, so the line survives into the
    object while any check that skips comment lines skips it. The remap stays in
    force while the step runs: the census reads the object store, not the leader.
    """
    repo, baseline = make_repo(tmp_path)
    if key == "core.commentString" and not comment_string_supported(repo):
        pytest.skip("this git predates core.commentString; the route does not exist here")
    repo.git("config", key, leader)
    product = repo.commit("CS-8 - under a remapped comment leader", trailer=True)
    in_force = repo.git("config", "--get", key)
    assert in_force == leader, "the remap is not in force"
    assert_caught(repo, baseline, product, tmp_path)


# --- a range holding a merge ----------------------------------------------------


def merge_count(repo: Repo, baseline: str) -> int:
    """How many merge commits ``baseline..HEAD`` holds."""
    return len(repo.git("rev-list", "--merges", f"{baseline}..HEAD").split())


@needs_tools
def test_a_trailer_on_a_merged_side_branch_is_caught(tmp_path: Path) -> None:
    """A trailer on a side-branch commit, reachable only through a merge at the tip."""
    repo, baseline = make_repo(tmp_path)
    original = topic_with_trailer(repo, baseline)
    repo.git("merge", "-q", "--no-ff", "-m", "CS-11 - merge the topic", "topic")
    tip = repo.head()
    merges = merge_count(repo, baseline)
    assert (merges, tip != original) == (1, True), "no merge sits between the tip and the plant"
    assert_caught(repo, baseline, original, tmp_path)


@needs_tools
def test_a_trailer_on_the_merge_commit_itself_is_caught(tmp_path: Path) -> None:
    """The census reads merge messages too, so a merge carrying the trailer is a hit."""
    repo, baseline = make_repo(tmp_path)
    repo.git("checkout", "-q", "-b", "topic", baseline)
    repo.commit("CS-5 - a clean topic change", name="topic.txt")
    repo.git("checkout", "-q", "main")
    repo.commit("CS-6 - main moves on")
    message = tmp_path / "merge-message.txt"
    message.write_bytes(("CS-11 - merge the topic\n\n" + TRAILER + "\n").encode("ascii"))
    repo.git("merge", "-q", "--no-ff", "-F", str(message), "topic")
    product = repo.head()
    merges = merge_count(repo, baseline)
    assert merges == 1, "the tip is not a merge"
    assert_caught(repo, baseline, product, tmp_path)


# --- controls -----------------------------------------------------------------


#: A census that cannot run: it exits 2, as the real one does on an unreadable
#: stream, an unresolvable range or a missing git.
COULD_NOT_RUN_CENSUS: Final = (
    b"import sys\nprint('trailer_census: could not run - stubbed', file=sys.stderr)\nsys.exit(2)\n"
)


@needs_tools
def test_a_census_that_could_not_run_fails_the_step_by_name(tmp_path: Path) -> None:
    """Exit 2 is a failure, never a pass: a census that did not run found nothing.

    The stub replaces the working-tree copy only, AFTER a clean range exists, so
    the ancestor check passes and the step reaches the census before it refuses.
    A step that failed only on exit 1 would print a pass here.
    """
    repo, baseline = make_repo(tmp_path)
    repo.commit("CS-4 - clean")
    (repo.path / CENSUS_TOOL).write_bytes(COULD_NOT_RUN_CENSUS)
    code, stdout = step_outcome(repo, baseline, tmp_path)
    shape = (
        code != 0,
        "exited 2" in stdout,
        "could not run" in stdout,
        "FAIL: the trailer baseline" in stdout,
    )
    assert shape == (True, True, True, False), (
        f"a census that could not run was not refused by name: {shape}, stdout {stdout!r}"
    )


@needs_tools
def test_a_clean_range_passes_and_walks_every_commit_after_the_baseline(tmp_path: Path) -> None:
    """Control: no trailer after the baseline is green, over a walk that is not empty."""
    repo, baseline = make_repo(tmp_path)
    repo.commit("CS-4 - clean")
    repo.commit("CS-5 - also clean, and it names the Co-authored-by trailer in prose")
    code, stdout = step_outcome(repo, baseline, tmp_path)
    assert (code, "commits walked 2;" in stdout) == (0, True), (
        f"a clean range did not pass: exit {code}, stdout {stdout!r}"
    )


@needs_tools
def test_a_baseline_that_is_not_an_ancestor_fails_and_names_why(tmp_path: Path) -> None:
    """Control: HEAD on a line that does not contain the baseline is refused."""
    repo, baseline = make_repo(tmp_path)
    repo.git("checkout", "-q", "-b", "elsewhere", "HEAD~2")
    repo.commit("CS-4 - a line the baseline is not on")
    code, stdout = step_outcome(repo, baseline, tmp_path)
    named = f"{baseline} is present but not an ancestor of HEAD" in stdout
    assert (code != 0, named) == (True, True), (
        f"a non-ancestor baseline was not refused by name: exit {code}, stdout {stdout!r}"
    )


@needs_tools
def test_a_baseline_absent_from_the_checkout_fails_and_names_why(tmp_path: Path) -> None:
    """Control: a baseline the object store lacks - a shallow checkout - is refused."""
    repo, _baseline = make_repo(tmp_path)
    repo.commit("CS-4 - clean")
    absent = "0123456789abcdef0123456789abcdef01234567"
    code, stdout = step_outcome(repo, absent, tmp_path)
    shape = (
        code != 0,
        f"{absent} is absent from this checkout" in stdout,
        f"{ABSENT_IMAGE} is absent from this checkout" in stdout,
    )
    assert shape == (True, True, True), (
        f"neither member present was not refused by name: {shape}, stdout {stdout!r}"
    )


@needs_tools
def test_a_trailer_before_the_baseline_does_not_redden(tmp_path: Path) -> None:
    """Control: history before the baseline is out of scope, by the grant."""
    repo, baseline = make_repo(tmp_path, trailer_before_baseline=True)
    before = repo.git("rev-parse", "HEAD~1")
    planted = git_sees_trailer(repo, before)
    assert planted, "the pre-baseline plant carries no trailer"
    repo.commit("CS-4 - clean")
    code, stdout = step_outcome(repo, baseline, tmp_path)
    assert (code, "commits walked 1;" in stdout) == (0, True), (
        f"a pre-baseline trailer reddened the step: exit {code}, stdout {stdout!r}"
    )


@needs_tools
def test_head_at_the_baseline_passes_by_name_and_walks_nothing(tmp_path: Path) -> None:
    """The EMPTY RANGE, decided: HEAD is the baseline, so nothing follows it.

    The census refuses a zero-commit walk because it reads like a clean one. With
    the ancestor check passed, ``baseline..HEAD`` is empty ONLY when HEAD is the
    baseline itself, so the step answers that case by name and never reaches the
    census - which keeps the census's refusal live for every other empty walk.
    """
    repo, baseline = make_repo(tmp_path)
    code, stdout = step_outcome(repo, baseline, tmp_path)
    shape = (code, "HEAD is the baseline" in stdout, "trailer_census:" in stdout)
    assert shape == (0, True, False), (
        f"HEAD at the baseline was not answered by name: {shape}, stdout {stdout!r}"
    )


# --- CS-704 accept set: the baseline OR its S7a image ---------------------------


def test_the_step_accepts_exactly_the_granted_pair() -> None:
    """The step names the two ruled SHAs and no other full object name."""
    script = step_script()
    named = frozenset(re.findall(r"\b[0-9a-f]{40}\b", script))
    assert named == ACCEPT_SET, f"the step's accept set is {sorted(named)}"


def rewritten_repo(tmp_path: Path) -> tuple[Repo, str, str]:
    """A repository standing in for history S7a rewrote.

    The ORIGINAL stand-in sits on a side line HEAD does not contain, as the
    pre-rewrite baseline does once ``main`` is replaced by its image; the IMAGE
    stand-in is on ``main``.

    Returns:
        The repository, the original stand-in and the image stand-in.
    """
    repo, original = make_repo(tmp_path)
    repo.git("checkout", "-q", "-b", "rewritten", "HEAD~2")
    image = repo.commit("CS-3 - the baseline's image")
    gone = is_ancestor(repo, original)
    assert gone == 1, "the original stand-in is still an ancestor of HEAD"
    return repo, original, image


@needs_tools
def test_the_image_passes_on_rewritten_history(tmp_path: Path) -> None:
    """After S7a the original is not an ancestor; its image is, and the range starts there."""
    repo, original, image = rewritten_repo(tmp_path)
    repo.commit("CS-4 - clean after the image")
    code, stdout = step_outcome(repo, original, tmp_path, image)
    assert (code, "commits walked 1;" in stdout) == (0, True), (
        f"rewritten history with the image present did not pass: exit {code}, stdout {stdout!r}"
    )


@needs_tools
def test_a_trailer_after_the_image_is_caught(tmp_path: Path) -> None:
    """Admitting the image never excuses what follows it: the census runs from it."""
    repo, original, image = rewritten_repo(tmp_path)
    product = repo.commit("CS-4 - trailer after the image", trailer=True)
    bury(repo, product)
    seen = git_sees_trailer(repo, product)
    assert seen, "the plant carries no trailer"
    code, stdout = step_outcome(repo, original, tmp_path, image)
    assert (code != 0, f"hit {product}" in stdout) == (True, True), (
        f"a trailer after the image was not caught: exit {code}, stdout {stdout!r}"
    )


@needs_tools
def test_head_at_the_image_passes_by_name(tmp_path: Path) -> None:
    """The empty range is decided for the image exactly as for the baseline."""
    repo, original, image = rewritten_repo(tmp_path)
    code, stdout = step_outcome(repo, original, tmp_path, image)
    shape = (code, "HEAD is the baseline" in stdout, "trailer_census:" in stdout)
    assert shape == (0, True, False), f"HEAD at the image: {shape}, stdout {stdout!r}"


@needs_tools
def test_a_history_holding_neither_member_as_an_ancestor_fails(tmp_path: Path) -> None:
    """A non-member: both SHAs present, neither on HEAD's line - refused, each by name."""
    repo, original, image = rewritten_repo(tmp_path)
    repo.git("checkout", "-q", "-b", "third", "HEAD~1")
    repo.commit("CS-4 - a line holding neither member")
    code, stdout = step_outcome(repo, original, tmp_path, image)
    shape = (
        code != 0,
        f"{original} is present but not an ancestor of HEAD" in stdout,
        f"{image} is present but not an ancestor of HEAD" in stdout,
        "trailer_census:" in stdout,
    )
    assert shape == (True, True, True, False), (
        f"a history holding neither member was not refused: {shape}, stdout {stdout!r}"
    )
