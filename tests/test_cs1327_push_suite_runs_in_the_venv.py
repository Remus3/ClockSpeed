"""CS-1327 - the pre-push suite runs under the interpreter the ladder chose, venv included.

THE DEFECT, measured at 28b1cba on Windows. The CS-818 ladder in
``.githooks/pre-push`` resolves ``python`` the way ``sh`` does, on PATH, so from
an activated virtual environment it picks the venv's ``python``. The suite line
then hands the kit's suite gate the BARE WORD ``python`` as its command. The
gate starts it with ``subprocess.run`` and no shell, and Windows CreateProcess
searches the PARENT'S APPLICATION DIRECTORY before PATH. A venv's
``python.exe`` is a redirector whose running process is the BASE interpreter,
so the gate's image lives in the base install and the bare word starts the base
interpreter: the suite runs OUTSIDE the venv. Where the base has no pytest - a
fresh clone set up per ``docs/OPERATIONS.md`` - every push is refused with
"pytest wrote no report"; where it has one, the suite silently runs under an
interpreter no probe vetted (the CS-703 / CS-821 family).

THE ORACLE IS WHERE THE SUITE RAN, NOT WHETHER PYTEST WAS MISSING. The sandbox
suite records its own ``sys.prefix`` into a marker outside the work tree, and
the arm asserts that marker names the venv put first on PATH. That reads red at
28b1cba on Windows whether or not the base interpreter carries pytest: with it
the marker names the base install, without it there is no marker at all.

THE VENV NEEDS NO NETWORK. It is made ``--without-pip`` under ``tmp_path`` and
pytest's own installed distribution closure is copied into its site-packages
from the interpreter running this arm, so pytest resolves from the venv's OWN
site-packages - which is exactly what the hook's CS-821 probe demands.

ON POSIX this passes before and after the repair: ``exec`` honours PATH there.

NOTHING HERE RENDERS A PATH OR AN ENVIRONMENT VALUE (CLAUDE.md non-negotiables
3 and 13). Assertions read booleans and a fixed classification word; the hook
output shown is its own banner lines only.

RESOURCE LIFETIME. Every child is a ``subprocess.run`` bounded by a timeout,
which reaps it. The venv, the sandbox, its bare remote and the hook's temporary
directory all live under pytest's ``tmp_path``.
"""

from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Final, NamedTuple

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from tests.fleet_hook_kit import (
    OPERATOR_IDENT_KEY,
    commit_margin_env,
    install_hook_kit,
    suite_dir_env,
)
from tests.git_env import scrub
from tests.pre_push_floor import with_test_floor

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
TRACKED_HOOK: Final = REPO_ROOT / ".githooks" / "pre-push"

GIT_TIMEOUT: Final = 300
VENV_TIMEOUT: Final = 300
PROBE_TIMEOUT: Final = 60
BRANCH: Final = "cs1327-sandbox"
FIXTURE_NAME: Final = "CS-1327 Fixture"
FIXTURE_EMAIL: Final = "cs1327@example.invalid"
HOOK_BANNER: Final = "clockspeed pre-push"
ENVIRONMENT_REPR: Final = "<environment withheld>"

#: The variable the sandbox suite reads its marker path from.
MARKER_ENV: Final = "CS1327_PREFIX_MARKER"

#: The one distribution whose installed closure the venv is given.
ROOT_DISTRIBUTION: Final = "pytest"

#: What the sandbox suite runs: it records the prefix of the interpreter it ran under.
SANDBOX_TEST: Final = (
    "import os\n"
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "\n"
    "def test_records_the_prefix_it_ran_under() -> None:\n"
    "    target = Path(os.environ['" + MARKER_ENV + "'])\n"
    "    target.write_text(sys.prefix, encoding='utf-8')\n"
)

#: Exits 0 only when run inside a venv whose pytest lives under that venv's prefix.
VENV_OWNS_PYTEST: Final = (
    "import os, sys\n"
    "if sys.prefix == sys.base_prefix:\n"
    "    sys.exit(2)\n"
    "import pytest\n"
    "where = os.path.normcase(os.path.realpath(pytest.__file__))\n"
    "home = os.path.normcase(os.path.realpath(sys.prefix))\n"
    "sys.exit(0 if os.path.commonpath([home, where]) == home else 4)\n"
)

#: Prints the venv's purelib directory. Read by this arm, never rendered.
PURELIB_PROGRAM: Final = "import sys, sysconfig; sys.stdout.write(sysconfig.get_path('purelib'))"


class Environment(NamedTuple):
    """The child environment, wrapped so pytest cannot render its contents."""

    variables: dict[str, str]

    def __repr__(self) -> str:
        """Render without any of the environment's contents."""
        return ENVIRONMENT_REPR


class Venv(NamedTuple):
    """A throwaway virtual environment under ``tmp_path`` that owns a pytest."""

    home: Path
    scripts: Path

    def __repr__(self) -> str:
        """Render without any path."""
        return "<CS-1327 venv, paths withheld>"


class Sandbox(NamedTuple):
    """A throwaway repository wired to a copy of the hook, with a bare remote."""

    work: Path
    env: dict[str, str]

    def __repr__(self) -> str:
        """Render without any path and without the environment."""
        return "<CS-1327 sandbox, paths withheld>"


def same_place(left: str | Path, right: str | Path) -> bool:
    """Whether two paths name one directory, after links and case are resolved."""
    return os.path.normcase(os.path.realpath(left)) == os.path.normcase(os.path.realpath(right))


def pytest_closure() -> list[metadata.Distribution]:
    """The installed distributions pytest needs here, markers evaluated, extras excluded."""
    found: dict[str, metadata.Distribution] = {}
    pending = [ROOT_DISTRIBUTION]
    while pending:
        name = pending.pop()
        key = canonicalize_name(name)
        if key in found:
            continue
        dist = metadata.distribution(name)
        found[key] = dist
        for spec in dist.requires or []:
            requirement = Requirement(spec)
            marker = requirement.marker
            if marker is None or marker.evaluate({"extra": ""}):
                pending.append(requirement.name)
    return list(found.values())


def copy_closure(purelib: Path) -> int:
    """Copy every installed file of pytest's closure into ``purelib``; return the count.

    Files a distribution recorded OUTSIDE its site-packages (console scripts,
    ``../`` entries) are skipped: the hook runs ``-m pytest`` and needs none.
    """
    copied = 0
    for dist in pytest_closure():
        files = dist.files
        assert files is not None, "a distribution in pytest's closure has no file record"
        for entry in files:
            relative = PurePosixPath(str(entry))
            if ".." in relative.parts:
                continue
            source = Path(str(dist.locate_file(entry)))
            if not source.is_file():
                continue
            target = purelib.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied += 1
    return copied


@pytest.fixture
def isolated(tmp_path: Path) -> Environment:
    """An environment cut loose from the operator's git config and from this pytest."""
    env = scrub(dict(os.environ))
    env["GIT_CONFIG_GLOBAL"] = str(tmp_path / "absent" / "gitconfig-global")
    env["GIT_CONFIG_SYSTEM"] = str(tmp_path / "absent" / "gitconfig-system")
    for leaked in [
        name
        for name in env
        if name.upper().startswith("PYTEST_")
        or name.upper() in {"CLOCKSPEED_PYTHON", "PYTHONPATH", "TMPDIR", MARKER_ENV}
    ]:
        env.pop(leaked, None)
    hook_tmp = tmp_path / "hook-tmp"
    hook_tmp.mkdir()
    env["TMPDIR"] = str(hook_tmp)
    env.update(suite_dir_env(tmp_path))
    # CS-1349: the gate's commit margin is 0 for a sandbox push (grant clause C).
    env.update(commit_margin_env())
    return Environment(env)


@pytest.fixture
def venv(tmp_path: Path, isolated: Environment) -> Venv:
    """A pip-less venv under ``tmp_path`` whose OWN site-packages hold pytest."""
    return build_venv(tmp_path / "venv", isolated)


def build_venv(home: Path, isolated: Environment) -> Venv:
    """Make a pip-less venv at ``home`` and give its OWN site-packages pytest.

    The purelib probe runs in UTF-8 mode (``-X utf8``) and is decoded as UTF-8,
    so a venv whose path the ANSI code page cannot encode is still built here:
    the harness must not die of the very fault the CS-1327 round-2 arm grades.
    """
    made = subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(home)],
        capture_output=True,
        timeout=VENV_TIMEOUT,
        env=isolated.variables,
        check=False,
    )
    assert made.returncode == 0, "the test venv could not be created"
    scripts = home / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    assert python.is_file(), "the test venv has no python"
    asked = subprocess.run(
        [str(python), "-I", "-X", "utf8", "-c", PURELIB_PROGRAM],
        capture_output=True,
        encoding="utf-8",
        timeout=PROBE_TIMEOUT,
        env=isolated.variables,
        check=False,
    )
    purelib = Path(asked.stdout)
    inside = (
        asked.returncode == 0
        and purelib.is_dir()
        and purelib.resolve().is_relative_to(home.resolve())
    )
    assert inside, "the test venv's site-packages did not resolve inside the venv"
    assert copy_closure(purelib) > 0, "no file of pytest's closure was copied"
    owns = subprocess.run(
        [str(python), "-P", "-c", VENV_OWNS_PYTEST],
        capture_output=True,
        timeout=PROBE_TIMEOUT,
        env=isolated.variables,
        check=False,
    )
    assert owns.returncode == 0, (
        f"harness fault, not the defect: the test venv does not own its pytest "
        f"(status {owns.returncode})"
    )
    return Venv(home=home, scripts=scripts)


def git(
    box: Sandbox, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run git inside the sandbox with the operator's own configuration excluded."""
    return subprocess.run(
        ["git", *args],
        cwd=str(box.work),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT,
        env=box.env if env is None else env,
        check=False,
    )


def push(
    box: Sandbox, overrides: dict[str, str], *, path_first: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Offer the sandbox branch to its remote under the sandbox env plus ``overrides``.

    The child environment is composed HERE and never bound in a test's frame,
    so no assertion scope holds it (``tests/test_locals_rendering.py``).
    ``path_first`` goes in front of the sandbox PATH.
    """
    env = {**box.env, **overrides}
    if path_first is not None:
        env["PATH"] = str(path_first) + os.pathsep + box.env.get("PATH", "")
    return git(box, "push", "origin", BRANCH, env=env)


def tip(box: Sandbox, *, remote: bool) -> str:
    """The sandbox branch locally, or as the bare remote itself holds it."""
    if remote:
        proc = git(box, "ls-remote", "origin", "refs/heads/" + BRANCH)
        line = proc.stdout.strip() if proc.returncode == 0 else ""
        return line.split()[0] if line else ""
    proc = git(box, "rev-parse", "refs/heads/" + BRANCH)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def make_sandbox(
    tmp_path: Path, isolated: Environment, *, relative_remote: bool = False
) -> Sandbox:
    """A real repository wired to the tracked hook (test-local floor), seeded remotely.

    ``relative_remote`` names the bare remote as ``../remote.git``, so git's own
    "failed to push some refs to" line carries no absolute path, and an arm that
    reads the whole push output for a path reads only what the HOOK rendered.
    """
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    installed = hooks / "pre-push"
    installed.write_bytes(with_test_floor(TRACKED_HOOK.read_bytes()))
    installed.chmod(0o755)

    work = tmp_path / "work"
    work.mkdir()
    remote = tmp_path / "remote.git"
    box = Sandbox(work=work, env=isolated.variables)

    assert git(box, "init", "-q", "-b", BRANCH).returncode == 0, "the sandbox could not init"
    for key, value in (
        ("user.name", FIXTURE_NAME),
        ("user.email", FIXTURE_EMAIL),
        ("commit.gpgsign", "false"),
        ("core.hooksPath", str(hooks)),
        (OPERATOR_IDENT_KEY, FIXTURE_EMAIL),
    ):
        assert git(box, "config", key, value).returncode == 0, f"{key} did not write"

    suite = work / "tests"
    suite.mkdir()
    (suite / "test_sandbox.py").write_bytes(SANDBOX_TEST.encode("ascii"))
    (work / "pytest.ini").write_bytes(b"[pytest]\n")
    install_hook_kit(work)

    assert git(box, "init", "-q", "--bare", str(remote)).returncode == 0, "no bare remote"
    url = "../" + remote.name if relative_remote else str(remote)
    assert git(box, "remote", "add", "origin", url).returncode == 0, "no origin"
    assert git(box, "add", "-A").returncode == 0, "the seed could not be staged"
    assert git(box, "commit", "-q", "-m", "CS-1327 seed").returncode == 0, "no seed commit"
    seeded = git(box, "push", "-q", "--no-verify", "origin", BRANCH)
    assert seeded.returncode == 0, "the seed could not reach the bare remote"
    return box


def where_it_ran(marker: Path, venv: Venv) -> str:
    """Classify the marker the sandbox suite wrote - a fixed word, never a path."""
    if not marker.is_file():
        return "no-marker"
    recorded = marker.read_text(encoding="utf-8").strip()
    if same_place(recorded, venv.home):
        return "the-venv"
    if same_place(recorded, sys.base_prefix):
        return "the-base-install"
    return "elsewhere"


def test_the_push_suite_runs_inside_the_venv_first_on_path(
    tmp_path: Path, isolated: Environment, venv: Venv
) -> None:
    """THE ACCEPTANCE ARM. RED at 28b1cba on Windows: the suite ran outside the venv.

    The venv's scripts directory goes first on the push's PATH, so the hook's
    ladder resolves ``python`` to the venv. The suite the hook then runs must
    record the venv's own prefix, and the push must land.
    """
    box = make_sandbox(tmp_path, isolated)
    marker = tmp_path / "suite-prefix.txt"
    made = git(box, "commit", "-q", "--allow-empty", "-m", "CS-1327 offered commit")
    assert made.returncode == 0, "the offered commit could not be made"
    proc = push(
        box, {"VIRTUAL_ENV": str(venv.home), MARKER_ENV: str(marker)}, path_first=venv.scripts
    )
    said = "\n".join(
        line.strip() for line in proc.stderr.splitlines() if line.strip().startswith(HOOK_BANNER)
    )

    where = where_it_ran(marker, venv)
    ran_in_the_venv = where == "the-venv"
    assert ran_in_the_venv, (
        f"the push suite did not run inside the venv first on PATH - it ran in "
        f"[{where}] (push exit {proc.returncode})\n{said}"
    )
    landed = tip(box, remote=True) == tip(box, remote=False) != ""
    assert landed, f"the push was refused (exit {proc.returncode})\n{said}"


# ROUND 2 (session 142, adversary lens 4): THE RESOLVE MUST SURVIVE A PATH THE
# ANSI CODE PAGE CANNOT ENCODE. ``-I`` makes the interpreter ignore PYTHONUTF8
# and PYTHONIOENCODING, so on Windows the resolve's stdout encodes through the
# ANSI code page. A venv whose path holds a character outside it - the
# adversary's was U+0416 on cp1252 - raises UnicodeEncodeError inside the
# resolve, which then reads EMPTY, and the hook dies BLOCKED (CS-1327) on an
# interpreter its own ladder accepted and that pushed fine before CS-1327.

#: CYRILLIC CAPITAL LETTER ZHE, built at run time because this source is ASCII
#: only. It sits outside cp1252 and every other Western ANSI code page.
OUTSIDE_THE_CODE_PAGE: Final = chr(0x416)

#: The hook's own CS-1327 refusal, read as a fixed string.
CS1327_REFUSAL: Final = "BLOCKED (CS-1327)"

#: How the push is led to the venv: first on PATH (the README shape), or named
#: by CLOCKSPEED_PYTHON (the adversary's own reproduction).
ROUTES: Final = ("path-first", "clockspeed-python")


def hook_said(stderr: str) -> str:
    """The hook's own banner lines only - never git's lines, never the suite's."""
    return "\n".join(
        line.strip() for line in stderr.splitlines() if line.strip().startswith(HOOK_BANNER)
    )


def venv_python(venv: Venv) -> Path:
    """The venv's own interpreter."""
    return venv.scripts / ("python.exe" if os.name == "nt" else "python")


def home_outside_the_code_page(tmp_path: Path) -> Path:
    """An empty directory whose last component holds U+0416, or a skip saying why not."""
    name = "venv-" + OUTSIDE_THE_CODE_PAGE
    home = tmp_path / name
    try:
        os.fsencode(home)
        home.mkdir()
        held = any(entry.name == name for entry in tmp_path.iterdir())
    except (OSError, UnicodeError):
        held = False
    if not held:
        pytest.skip("this filesystem or platform cannot hold a directory name with U+0416")
    return home


@pytest.mark.parametrize("route", ROUTES)
def test_the_push_resolves_a_venv_whose_path_the_code_page_cannot_encode(
    tmp_path: Path, isolated: Environment, route: str
) -> None:
    """ROUND 2, adversary lens 4. RED at the round-1 candidate on a cp1252 Windows box.

    The venv's last path component holds U+0416. The hook must resolve that
    interpreter's own path, must NOT die BLOCKED (CS-1327), must run the suite
    inside the venv, and the push must land - on both routes to the venv.
    """
    venv = build_venv(home_outside_the_code_page(tmp_path), isolated)
    box = make_sandbox(tmp_path, isolated)
    marker = tmp_path / "suite-prefix.txt"
    made = git(box, "commit", "-q", "--allow-empty", "-m", "CS-1327 offered commit")
    assert made.returncode == 0, "the offered commit could not be made"
    if route == "path-first":
        proc = push(
            box, {"VIRTUAL_ENV": str(venv.home), MARKER_ENV: str(marker)}, path_first=venv.scripts
        )
    else:
        proc = push(box, {"CLOCKSPEED_PYTHON": str(venv_python(venv)), MARKER_ENV: str(marker)})
    said = hook_said(proc.stderr)

    died_on_the_resolve = CS1327_REFUSAL in proc.stderr
    assert not died_on_the_resolve, (
        f"the hook died {CS1327_REFUSAL} on a venv whose path the code page cannot "
        f"encode - the resolve read empty (route {route}, push exit {proc.returncode})\n{said}"
    )
    where = where_it_ran(marker, venv)
    assert where == "the-venv", (
        f"the push suite did not run inside the venv - it ran in [{where}] "
        f"(route {route}, push exit {proc.returncode})\n{said}"
    )
    landed = tip(box, remote=True) == tip(box, remote=False) != ""
    assert landed, f"the push was refused (route {route}, exit {proc.returncode})\n{said}"


# THE CS-1327 REFUSAL ITSELF RENDERS NO PATH (round 2, closing adversary lens
# 3's coverage gap). The arm above proves the refusal is not reached for a good
# interpreter; this one REACHES it and reads everything the push printed.
#
# THE INTERPRETER is a shim that runs the real one for every call but the
# resolve. On the resolve it touches a sentinel - proof the refusal was reached
# through the resolve and nothing else - then prints its own path, the real
# interpreter's path and the home path on BOTH streams, and fails. A hook that
# rendered the resolve's streams, or rendered the interpreter it refused, is
# caught. Only scalars are asserted: no assertion here can render a path.

#: The shim's directory name - a fixed token any partial echo of its path carries.
INTERPRETER_CANARY: Final = "cs1327-interpreter-canary"

#: The resolve program is the only call that names this attribute.
RESOLVE_WORD: Final = "sys.executable"

#: Below this length a path form is too generic to grade - a bare ``/`` matches all.
SHORTEST_GRADED_FORM: Final = 4

#: A drive-letter path in forward-slash spelling, which MSYS spells ``/c/...``.
DRIVE_PREFIX: Final = re.compile(r"[A-Za-z]:/")


def path_forms(path: str | Path) -> set[str]:
    """One path as the hook could spell it - native, forward-slash, MSYS - lower-cased."""
    raw = str(path)
    posix = raw.replace("\\", "/")
    forms = {raw, posix}
    if DRIVE_PREFIX.match(posix):
        forms.add("/" + posix[0].lower() + posix[2:])
    return {form.lower() for form in forms if len(form) >= SHORTEST_GRADED_FORM}


def short_form(path: Path) -> str:
    """The Windows 8.3 spelling of ``path``, or the path itself where there is none."""
    if sys.platform != "win32":
        return str(path)
    buffer = ctypes.create_unicode_buffer(1024)
    size = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
    return buffer.value if 0 < size < len(buffer) else str(path)


def personal_forms(shim: Path) -> set[str]:
    """Every spelling of the interpreter paths and the home path the arm grades."""
    forms = {INTERPRETER_CANARY}
    for interpreter in (shim, shim.parent, sys.executable, os.path.realpath(sys.executable)):
        forms |= path_forms(interpreter)
    home = Path.home()
    if home.parent != home:
        for spelling in (home, Path(os.path.realpath(home)), Path(short_form(home))):
            forms |= path_forms(spelling)
    return forms


def leaks(text: str, forms: set[str]) -> int:
    """How many of ``forms`` occur in ``text``, case-folded - a count, never the text."""
    folded = text.lower()
    return sum(1 for form in forms if form in folded)


def refusing_shim(directory: Path, sentinel: Path) -> Path:
    """An interpreter that runs the real one, except that it fails the resolve noisily."""
    real = Path(sys.executable).as_posix()
    home = Path.home().as_posix()
    shell_safe = not any(ch in home + real for ch in '"$`\\')
    noise = '"$0" "' + real + '" "' + home + '"' if shell_safe else '"$0"'
    body = (
        "#!/bin/sh\n"
        'case "$*" in\n'
        "    *" + RESOLVE_WORD + "*)\n"
        '        : > "' + sentinel.as_posix() + '"\n'
        "        printf '%s\\n' " + noise + "\n"
        "        printf '%s\\n' " + noise + " >&2\n"
        "        exit 1\n"
        "        ;;\n"
        "esac\n"
        'exec "' + real + '" "$@"\n'
    )
    directory.mkdir(parents=True)
    shim = directory / "python-shim"
    shim.write_bytes(body.encode("utf-8"))
    shim.chmod(0o755)
    return shim


def test_the_cs1327_refusal_renders_no_interpreter_path_and_no_home_path(
    tmp_path: Path, isolated: Environment
) -> None:
    """Drive the BLOCKED (CS-1327) refusal; the push output names no personal path.

    The shim fails only the resolve, so the hook reaches the refusal past every
    earlier check. The non-vacuity half: the sentinel proves the shim saw the
    resolve, the refusal word proves the hook took that branch, and the oracle
    is shown finding the very paths it then reports absent.
    """
    sentinel = tmp_path / "resolve-was-asked.flag"
    shim = refusing_shim(tmp_path / INTERPRETER_CANARY, sentinel)
    forms = personal_forms(shim)
    oracle_sees_paths = leaks(shim.as_posix(), forms) > 0 and leaks(str(Path.home()), forms) > 0
    assert oracle_sees_paths, "harness fault: the path oracle cannot see the paths it grades"

    box = make_sandbox(tmp_path, isolated, relative_remote=True)
    made = git(box, "commit", "-q", "--allow-empty", "-m", "CS-1327 offered commit")
    assert made.returncode == 0, "the offered commit could not be made"
    proc = push(box, {"CLOCKSPEED_PYTHON": str(shim)})
    output = proc.stdout + proc.stderr

    resolve_asked = sentinel.is_file()
    refused_on_the_resolve = CS1327_REFUSAL in output
    landed = tip(box, remote=True) == tip(box, remote=False) != ""
    reached = resolve_asked and refused_on_the_resolve and not landed
    assert reached, (
        f"the CS-1327 refusal was not reached through the resolve (asked "
        f"{resolve_asked}, refused {refused_on_the_resolve}, landed {landed}, "
        f"push exit {proc.returncode})"
    )
    hits = leaks(output, forms)
    assert hits == 0, (
        f"the CS-1327 refusal rendered {hits} interpreter or home path spelling(s); "
        f"none is shown here (push exit {proc.returncode})"
    )
