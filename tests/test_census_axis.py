"""CS-1328 (b) - the tracked census axis, graded over throwaway repositories only.

THE DEFINITION UNDER TEST is the module docstring of ``tools/census_axis.py``; every arm
below is one clause of it. These arms are the out-of-tree v3 measurement's own self-test,
moved into the suite: its fixture, its planted spellings and its exact expected counts,
with every drive letter, root, host name and folder name replaced by a value this module
builds at run time.

NOTHING HERE IS REAL DATA. Every repository is made under a pytest temporary directory;
the roots the census counts are that directory's own paths; the two drive letters are
ones the census is told to use, never this machine's; the host name is a random token;
the historical folder names are synthetic. No path, drive root or host name is written
as a literal, because the whole-tree path and host guards read this file too, and no
assertion renders a root, a host, an environment or a matched string - each is bound to
a count or a boolean first.

MUTANT CONTROLS. A green arm proves nothing until it has been seen to go red, so
``test_each_mutant_turns_its_arm_red`` applies one mutation per arm to the loaded module,
asserts the mutation landed, and asserts the arm's own oracle then fails.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
AXIS_SOURCE: Final = REPO_ROOT / "tools" / "census_axis.py"

#: Seconds one git call or one CLI run may take in these arms.
TIMEOUT: Final = 120

#: The two drive letters every arm tells the census to use, in its label order. Synthetic:
#: the census takes its letters from ``--drive`` or derives them at run time.
DRIVES: Final = ("K", "M")

#: One hit, and none: (occurrences, lines, objects).
ONE: Final = (1, 1, 1)
ZERO: Final = (0, 0, 0)

#: The synthetic host every arm plants, lower case; random, so it names no machine.
HOST: Final = "hq" + secrets.token_hex(5)

#: A token planted once in the fixture, so a census told to use it as its absent token
#: finds it there (the absent control's mutant).
PLANT: Final = secrets.token_hex(6)

#: Exit codes of the census.
EXIT_OK: Final = 0
EXIT_FAILED_CONTROL: Final = 1
EXIT_UNMEASURED: Final = 2

#: The number of controls a census run reports, and of sidecar categories.
CONTROL_COUNT: Final = 7
SIDECAR_CATEGORIES: Final = 6

#: The exact refusal line a run with a failed control prints before its exit line.
FAILED_CONTROL_LINE: Final = (
    "UNMEASURED a control failed - an adjudicator rules before the count is used"
)

#: The two historical folder names this module PINS, independently of the census's own
#: constants, so a census that derives either wrong is graded against the right one: the
#: old worktree root's suffix after the repo folder name, and the old walk harness folder.
WT_SUFFIX_PIN: Final = "-wt"
WALK_PIN: Final = "cs-walk-131"

#: The historical-folder source the fixture plants as ``tests/test_readme_audit.py``, in
#: the real file's shape: an annotated, implicitly concatenated rf-string whose field is a
#: module-level atomic group, a bare folder alternative and the layout alternative. Its
#: folder names are synthetic.
HIST_FIXTURE: Final = r"""from typing import Final

_SEP: Final = (
    r"(?>\\+u005c|\\*/|\\|%5c|[\\/]|&#0*92;)"
)
_SIDECAR_NAME: Final = (
    rf"(?:cs-(?:oldlanes|old-backup)|oldcars"
    rf"|cs{_SEP}+(?:worktree|walk|scratch)(?![A-Za-z0-9]))"
)
OTHER: Final = rf"x{_SIDECAR_NAME}y"
"""
HIST_NAMES: Final = [["cs-oldlanes"], ["cs-old-backup"]]
HIST_BARE: Final = [["oldcars"]]

#: What the derivation reads: (cs- folders, bare folders, layout alternatives).
Derived = tuple[list[list[str]], list[list[str]], int]

#: Sources the derivation must read, and what it must read from each.
HIST_GOOD: Final[tuple[tuple[str, Derived], ...]] = (
    ('_SIDECAR_NAME = "(?:cs-(?:a|b-c))"\n', ([["cs-a"], ["cs-b-c"]], [], 0)),
    ('_SIDECAR_NAME = "(?:old|cs-(?:a)" + "|new)"\n', ([["cs-a"]], [["old"], ["new"]], 0)),
    (
        '_S = "(?:/)"\n_T = rf"(?:{_S}|[)|]|\\))"\n'
        '_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_T}+(?:walk)(?![A-Za-z0-9]))"\n',
        ([["cs-a"]], [], 1),
    ),
)

#: Sources the derivation must refuse, each with the fixed reason it must give.
HIST_BAD: Final = (
    ('_SIDECAR_NAME = "(?:sidecars)"\n', "no single cs- folder alternation"),
    ('_SIDECAR_NAME = "(?:cs-(?:a)|cs-(?:b))"\n', "no single cs- folder alternation"),
    ("_SIDECAR_NAME = build()\n", "not a literal this script reads"),
    ('_SIDECAR_NAME = b"(?:cs-(?:a|b))"\n', "not a literal this script reads"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b))" + OTHER\n', "not a literal this script reads"),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b))"\n_SIDECAR_NAME = "(?:cs-(?:c))"\n',
        "the pattern is bound more than once",
    ),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b))"\n_SIDECAR_NAME += "|x"\n', "the pattern is augmented"),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b))"\ndef f():\n    global _SIDECAR_NAME\n'
        '    _SIDECAR_NAME = "(?:cs-(?:c))"\n',
        "the pattern is bound more than once",
    ),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b))"\nfor _SIDECAR_NAME in ():\n    pass\n',
        "the pattern is bound more than once",
    ),
    ("import os as _SIDECAR_NAME\n", "not bound by a plain module-level assignment"),
    (
        'from os import *\n_SIDECAR_NAME = "(?:cs-(?:a|b))"\n',
        "the pattern is bound more than once",
    ),
    (
        '_SIDECAR_NAME, X = "(?:cs-(?:a|b))", 1\n',
        "not bound by a plain module-level assignment",
    ),
    (
        'if True:\n    _SIDECAR_NAME = "(?:cs-(?:a|b))"\n',
        "not bound by a plain module-level assignment",
    ),
    (
        'X = _SIDECAR_NAME = "(?:cs-(?:a|b))"\n',
        "not bound by a plain module-level assignment",
    ),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b))"\nglobals()["_SIDECAR_NAME"] = "(?:cs-(?:c))"\n',
        "a string spells the pattern's name",
    ),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b))"\ndel _SIDECAR_NAME\n',
        "the pattern is bound more than once",
    ),
    ('OTHER = "(?:cs-(?:a|b))"\n', "the pattern is not bound"),
    (
        '_S = "(?:/)"\n_SIDECAR_NAME = rf"(?:cs-(?:a)|{_S!r})"\n',
        "a field this script does not read",
    ),
    (
        '_S = "(?:/)"\n_SIDECAR_NAME = rf"(?:cs-(?:a)|{_S:>3})"\n',
        "a field this script does not read",
    ),
    ('_SIDECAR_NAME = rf"(?:cs-(?:a)|{build()})"\n', "a field this script does not read"),
    (
        '_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_NOPE}+(?:walk)(?![A-Za-z0-9]))"\n',
        "a name the pattern reads is not bound",
    ),
    (
        '_S = "/"\n_S = "\\\\"\n_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_S}+(?:walk)(?![A-Za-z0-9]))"\n',
        "a name the pattern reads is bound more than once",
    ),
    (
        '_S = "(?:/)"\n_S += "|cs-(?:z)"\n'
        '_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_S}+(?:walk)(?![A-Za-z0-9]))"\n',
        "a name the pattern reads is augmented",
    ),
    (
        '_S = "/|cs-(?:evil)"\n_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_S}+(?:walk)(?![A-Za-z0-9]))"\n',
        "a name the pattern reads is not one whole regex group",
    ),
    (
        '_S = "(?:/)|(?:x)"\n_SIDECAR_NAME = rf"(?:cs-(?:a)|cs{_S}+(?:walk)(?![A-Za-z0-9]))"\n',
        "a name the pattern reads is not one whole regex group",
    ),
    ('_SIDECAR_NAME = rf"(?:cs-(?:a)|{_SIDECAR_NAME})"\n', "reads a name in a cycle"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b)|x+y)"\n', "a shape this script does not read"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b)|Old)"\n', "a shape this script does not read"),
    (
        '_SIDECAR_NAME = "(?:cs-(?:a|b)|cs/+(?:walk)(?![A-Za-z0-9]))"\n',
        "a shape this script does not read",
    ),
    ('_SIDECAR_NAME = "cs-(?:a|b)"\n', "the pattern is not one (?:...) group"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b)"\n', "the pattern is not one (?:...) group"),
    ('_SIDECAR_NAME = "(?:cs-(?:a))(?:x)"\n', "the pattern is not one (?:...) group"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|a))"\n', "a folder name is repeated"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b)|old|old)"\n', "a folder name is repeated"),
    ('_SIDECAR_NAME = "(?:cs-(?:a|b)|cs-a)"\n', "a folder name is repeated"),
    ("def broken(:\n", "the test pattern source is unreadable"),
)


def _load() -> ModuleType:
    """Import ``tools/census_axis.py`` by path.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("clockspeed_census_axis", AXIS_SOURCE)
    if spec is None or spec.loader is None:
        message = f"could not load {AXIS_SOURCE.name}"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


census = _load()

Table = dict[tuple[str, str], dict[str, tuple[int, int, int]]]
Run = tuple[int, Table, list[str]]


# --- the oracle's own spellings and paths, independent of the census's ----------------


def _spell(drive: bytes, comps: list[bytes], sep: bytes) -> bytes:
    """A drive spelling: the drive, a colon, then the components joined by ``sep``."""
    return drive + b":" + sep + sep.join(comps)


def _bash(drive: bytes, comps: list[bytes], sep: bytes, lead: bytes = b"/") -> bytes:
    """A Git Bash spelling: ``lead``, the lower-case drive, then the components."""
    return lead + drive.lower() + sep + sep.join(comps)


def _drive_path(letter: str, *parts: str, sep: str = "\\") -> str:
    """A drive-rooted path, built at run time."""
    return letter + ":" + sep + sep.join(parts)


def _posix_path(*parts: str) -> str:
    """A POSIX absolute path, built at run time."""
    return "/" + "/".join(parts)


def _enc(comps: list[str]) -> list[bytes]:
    """Components as UTF-8 bytes."""
    return [c.encode("utf-8") for c in comps]


def _git_env(base: Path) -> dict[str, str]:
    """The test's own git environment: no inherited GIT_ variable, no operator config."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = str(base / "absent-global")
    env["GIT_CONFIG_SYSTEM"] = str(base / "absent-system")
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(cwd: Path, *args: str, env: dict[str, str]) -> bytes:
    """Run one git command in ``cwd`` under ``env`` and return its stdout."""
    completed = subprocess.run(
        ["git", *args], cwd=cwd, env=env, capture_output=True, timeout=TIMEOUT, check=True
    )
    return completed.stdout


@dataclass
class World:
    """The synthetic world: a repository, its clone under a sidecar root, and its roots."""

    base: Path
    sidecars: Path
    fake_repo: Path
    fake_main: Path
    clone: Path
    tip: str
    hosts: dict[str, str]

    def roots(self, **replace: object) -> dict[str, list[str]]:
        """The census roots; each keyword replaces one category's components."""
        parts: dict[str, object] = {
            "repo": census.split_root(str(self.fake_repo)),
            "sidecar": census.split_root(str(self.sidecars)),
            "hist": HIST_NAMES,
            "bare": HIST_BARE,
            "wt": [self.fake_repo.name + WT_SUFFIX_PIN],
            "walk": [WALK_PIN],
            "main": census.split_root(str(self.fake_main)),
        }
        parts.update(replace)
        roots: dict[str, list[str]] = census.root_set(
            parts["repo"], parts["sidecar"], parts["hist"], parts["bare"], parts["wt"],
            parts["walk"], parts["main"],
        )  # fmt: skip
        return roots


def _commit(repo: Path, base: Path, files: dict[str, bytes | None], message: bytes) -> None:
    """Write ``files`` (None deletes one) and commit them with exactly ``message``."""
    env = _git_env(base)
    for rel, data in files.items():
        target = repo / rel
        if data is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    msg = base / "msg.txt"
    msg.write_bytes(message)
    _git(repo, "add", "-A", env=env)
    # The author name carries a host needle: a header scanned as message would count it.
    _git(
        repo,
        "-c", f"user.name=synthetic {HOST.upper()}", "-c", "user.email=synthetic@example.invalid",
        "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={base / 'nohooks'}",
        "commit", "-q", "--cleanup=verbatim", "-F", str(msg),
        env=env,
    )  # fmt: skip


def _blobs(rc: list[bytes], sc: list[bytes], mc: list[bytes], wt: list[bytes]
           ) -> dict[str, bytes]:  # fmt: skip
    """The fixture's planted blobs, v3's own, every drive letter one of ``DRIVES``."""
    d1, d2 = (d.encode("ascii") for d in DRIVES)
    l1, l2 = d1.lower(), d2.lower()
    h1, h2 = _enc(HIST_NAMES[0]), _enc(HIST_NAMES[1])
    wk = [WALK_PIN.encode("ascii")]
    bc = _enc(HIST_BARE[0])
    up = HOST.upper().encode("ascii")
    low = HOST.encode("ascii")
    a1 = b"".join([
        b"see " + _spell(d1, rc, b"\\") + b"\\file.py here\n",
        _spell(d2, rc, b"/") + b"/other and " + _spell(d1, rc, b"/") + b"\n",
        _spell(d1, rc, b"\\") + b"-old\\x\n",
        _spell(b"Z", [b"nothing"], b"\\") + b"\n",
        b"https://example.com/a:b\n",
        b"host " + up + b" ok\n",
        b"x" + up + b" not" + low + b"-y\n",
        low + b".lan\n",
        b'"' + _spell(d1, rc, b"\\\\") + b'"\n',
        _spell(d2, h2, b"\\") + b"\\stamp\n",
        _bash(d1, rc, b"/") + b"/x\n",
    ])  # fmt: skip
    b_blob = b"".join([
        b"main root: " + _spell(d1, mc, b"\\") + b"\\outbox\n",
        b"sidecar: " + _spell(d2, sc, b"\\") + b"\\CS\\Walk\n",
        _spell(l1, [c.lower() for c in rc], b"/") + b"\n",
    ])  # fmt: skip
    u_blob = ("\ufeffpath " + _spell(d1, rc, b"\\").decode("utf-8") + "\n").encode("utf-16-le")
    h_blob = b"".join([
        # drive spellings of the historical folders, then their negatives
        b"old lanes " + _spell(d2, h1, b"\\") + b"\\lane1\n",
        _spell(d1, [c.upper() for c in h2], b"/") + b'/stamp and "'
        + _spell(d2, h2, b"\\\\") + b'"\n',
        _spell(d1, h1, b"\\") + b"\n",
        _spell(d2, h1, b"\\") + b"-x " + d2 + b":\\stash\\" + h1[0] + b" x"
        + _spell(d2, h1, b"\\") + b" " + d2 + b":" + h1[0] + b"\n",
        # Git Bash spellings of the historical folders, then their negatives
        b"bash " + _bash(l2, h1, b"/") + b"/x\n",
        _bash(l1, h2, b"/", lead=b"//") + b"\n",
        b'"' + _bash(l2, h2, b"\\/", lead=b"\\/") + b'"\n',
        _bash(l1, h1, b"/") + b"\n",
        b"/mnt" + _bash(l2, h1, b"/") + b" https://host" + _bash(l2, h1, b"/") + b" "
        + _bash(l2, h1, b"/") + b"-x a" + _bash(l2, h1, b"/") + b" ."
        + _bash(l1, h1, b"/") + b" " + _bash(l2, h1, b"/", lead=b"////") + b"\n",
        # Git Bash spellings of the repo, current sidecar and main roots, then negatives
        _bash(l1, rc, b"/") + b"\n",
        _bash(l2, sc, b"/") + b"/CS/Walk\n",
        _bash(l1, mc, b"\\/", lead=b"\\/") + b"\n",
        _bash(l1, rc, b"/") + b"-old x" + _bash(l1, rc, b"/") + b"\n",
    ])  # fmt: skip
    w_blob = b"".join([
        # the old worktree root, all four spellings (one glued)
        b"wt " + _spell(d2, wt, b"\\") + b"\\lane1\n",
        _spell(l1, [c.lower() for c in wt], b"/") + b"\n",
        _bash(l2, wt, b"/") + b"/x\n",
        b"-C" + _bash(l1, wt, b"/", lead=b"//") + b"\n",
        # the old walk harness folder (a glued drive, a JSON-escaped lead)
        _spell(d1, wk, b"\\") + b"\\run\n",
        b'"' + _bash(l2, wk, b"\\/", lead=b"\\/\\/") + b'\\/x"\n',
        b"-I" + _spell(d2, wk, b"\\") + b"\n",
        _bash(l1, wk, b"/") + b"\n",
        # the bare folder alternative (a doubled-backslash JSON-escaped lead)
        _spell(d1, bc, b"\\") + b"\\x\n",
        _spell(l2, bc, b"/") + b"\n",
        _bash(l2, bc, b"/") + b"/y\n",
        _bash(l1, bc, b"\\\\/", lead=b"\\\\/\\\\/") + b"\n",
        # the repo root behind glued options
        b"git -C" + _bash(l1, rc, b"/") + b"/x\n",
        b"cc -I" + _spell(d1, rc, b"/") + b"\n",
        # negatives: no anchor at all, then an anchor but no needle
        b"a-C" + _bash(l1, wk, b"/") + b"\n",
        b"9-I" + _spell(d2, wk, b"\\") + b"\n",
        b'"' + _bash(l2, wk, b"\\/", lead=b"\\/\\/\\/\\/") + b'"\n',
        b"x" + _spell(d2, bc, b"/") + b"\n",
        _spell(d1, wt, b"\\") + b"x\n",
        _bash(l1, wk, b"/") + b"0\n",
    ])  # fmt: skip
    return {"a1": a1, "b": b_blob, "u": u_blob, "h": h_blob, "w": w_blob}


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> World:
    """Three commits planted with every spelling, cloned under a synthetic sidecar root."""
    base = tmp_path_factory.mktemp("cax")
    # A one-letter folder, or one ending in a glued option, above the synthetic repo
    # would be an extra Git Bash anchor inside every spelling planted below.
    awkward = sum(
        1
        for c in census.split_root(str(base))
        if len(c) == 1 or re.search(r"(?:^|[^A-Za-z0-9])-[A-Za-z]$", c)
    )
    if awkward:
        pytest.fail("the temporary directory holds a one-letter or glued-option folder")
    env = _git_env(base)
    (base / "nohooks").mkdir()
    sidecars = base / "sc"
    for marker in census.SIDECAR_MARKERS:
        sidecars.joinpath(*marker).mkdir(parents=True, exist_ok=True)
    out_dir = sidecars.joinpath(*census.SIDECAR_MARKERS[-1], "out")
    out_dir.mkdir()
    fake_repo = base / "FakeRepo"
    fake_main = base / "FakeMain"
    fake_main.mkdir()
    _git(base, "init", "-q", "-b", "main", str(fake_repo), env=env)
    _git(fake_repo, "config", "core.autocrlf", "false", env=env)
    fake_repo.joinpath(*census.MAIN_CONFIG).parent.mkdir()
    fake_repo.joinpath(*census.MAIN_CONFIG).write_bytes(
        json.dumps({census.MAIN_KEY: str(fake_main)}).encode("utf-8")
    )
    fake_repo.joinpath(*census.HIST_SOURCE).parent.mkdir()
    fake_repo.joinpath(*census.HIST_SOURCE).write_bytes(HIST_FIXTURE.encode("utf-8"))
    fake_repo.joinpath(".git", "info").mkdir(parents=True, exist_ok=True)
    fake_repo.joinpath(".git", "info", "exclude").write_bytes(b"config/\ntests/\n")

    rc = _enc(census.split_root(str(fake_repo)))
    sc = _enc(census.split_root(str(sidecars)))
    mc = _enc(census.split_root(str(fake_main)))
    wt = _enc([fake_repo.name + WT_SUFFIX_PIN])
    h2 = _enc(HIST_NAMES[1])
    d1, d2 = (d.encode("ascii") for d in DRIVES)
    up = HOST.upper().encode("ascii")
    blobs = _blobs(rc, sc, mc, wt)
    _commit(
        fake_repo, base, {"a.txt": blobs["a1"], "docs/n.md": b"x\n"},
        b"first\n\nsee " + _spell(d2, sc, b"\\") + b"\\x\n",
    )  # fmt: skip
    _commit(
        fake_repo, base,
        {"a.txt": b"clean\n", "b.txt": blobs["b"], "u.txt": blobs["u"], "h.txt": blobs["h"],
         "w.txt": blobs["w"], "p.txt": b"absent-" + PLANT.encode("ascii") + b"\n",
         f"logs/{HOST.upper()}/r.txt": b"x\n"},
        b"second " + _spell(d1, rc, b"\\") + b"\\y\n",
    )  # fmt: skip
    _commit(
        fake_repo, base, {"docs/n.md": None, "c.txt": b"y\n"},
        b"third on " + up + b"\n\nran " + _bash(d1, rc, b"/") + b"\nand "
        + _bash(d2, h2, b"\\/", lead=b"\\/") + b"\n",
    )  # fmt: skip
    clone = out_dir / "clone"
    _git(base, "clone", "-q", "--no-local", str(fake_repo), str(clone), env=env)
    tip = _git(clone, "rev-parse", "HEAD", env=env).decode("ascii").strip()
    hosts = {"netbios": HOST.upper(), "dns": HOST, "fqdn": HOST + ".lan"}
    return World(base, sidecars, fake_repo, fake_main, clone, tip, hosts)


def _run(
    world: World, roots: dict[str, list[str]] | None = None, drives: list[str] | None = None
) -> Run:
    """One census run over the clone: (exit code, table, emitted lines)."""
    lines: list[str] = []
    code, table = census.run_census(
        world.clone, world.tip, world.roots() if roots is None else roots, world.hosts,
        list(DRIVES) if drives is None else drives, lines.append,
    )  # fmt: skip
    return code, table, lines


@pytest.fixture(scope="module")
def pristine(world: World) -> Run:
    """The unmutated census run every arm compares against."""
    return _run(world)


def _expected() -> Table:
    """v3's exact expected counts, its two drive letters read as ``DRIVES``."""
    d1, d2 = DRIVES
    b1, b2 = f"{census.BASH}.{d1}", f"{census.BASH}.{d2}"
    w_hits = {
        f"{cat}.{sp}": ONE
        for cat in (census.SIDECAR_WT, census.SIDECAR_WALK, f"{census.SIDECAR_BARE}1")
        for sp in (d1, d2, b1, b2)
    }
    hist = census.SIDECAR_HIST
    shared = {
        f"sidecar_root.{d2}": ONE, f"main_root.{d1}": ONE,
        f"{hist}1.{d2}": ONE, f"{hist}1.{d1}": ONE, f"{hist}2.{d1}": ONE,
        f"{hist}1.{b2}": ONE, f"{hist}1.{b1}": ONE,
        f"{hist}2.{b2}": ONE, f"{hist}2.{b1}": ONE,
        f"sidecar_root.{b2}": ONE, f"main_root.{b1}": ONE, **w_hits,
    }  # fmt: skip
    hosts_in_paths = {"host.netbios": ONE, "host.dns": ONE}
    return {
        ("head", "blobs"): {
            **shared, f"repo_root.{d1}": (3, 3, 3), f"{hist}2.{d2}": ONE,
            f"repo_root.{b1}": (2, 2, 2),
            census.ANY_LABEL: (18, 16, 4), census.BASH_LABEL: (17, 17, 2),
        },
        ("full", "blobs"): {
            **shared, f"repo_root.{d1}": (6, 6, 4), f"repo_root.{d2}": ONE,
            f"{hist}2.{d2}": (2, 2, 2), f"repo_root.{b1}": (3, 3, 3),
            census.ANY_LABEL: (25, 22, 5), census.BASH_LABEL: (18, 18, 3),
            "host.netbios": (2, 2, 1), "host.dns": (2, 2, 1), "host.fqdn": ONE,
        },
        ("head", "paths"): dict(hosts_in_paths),
        ("full", "paths"): dict(hosts_in_paths),
        ("head", "messages"): {
            **hosts_in_paths, f"repo_root.{b1}": ONE, f"{hist}2.{b2}": ONE,
            census.BASH_LABEL: (2, 2, 1),
        },
        ("full", "messages"): {
            **hosts_in_paths, f"repo_root.{d1}": ONE, f"sidecar_root.{d2}": ONE,
            census.ANY_LABEL: (2, 2, 2), f"repo_root.{b1}": ONE, f"{hist}2.{b2}": ONE,
            census.BASH_LABEL: (2, 2, 1),
        },
    }  # fmt: skip


def _miscounted(table: Table) -> int:
    """How many (cell, label) pairs differ from the expected counts; -1 for a wrong cell set."""
    expect = _expected()
    if set(table) != set(expect):
        return -1
    wrong = 0
    for cell, row in table.items():
        want = expect[cell]
        wrong += sum(
            1
            for label in row
            if not label.startswith(census.COVER_PREFIX) and row[label] != want.get(label, ZERO)
        )
        wrong += sum(1 for label in want if label not in row)
    return wrong


#: A letter neither of ``DRIVES``, which no census told to use ``DRIVES`` may count.
IDLE: Final = next(chr(c) for c in range(ord("A"), ord("Z") + 1) if chr(c) not in DRIVES)


def _cover_gaps(table: Table, roots: list[str]) -> int:
    """(cell, root, spelling) triples whose letter-class occ is not the per-letter sum."""
    gaps = 0
    for row in table.values():
        for name in roots:
            drive_sum = sum(row[f"{name}.{c}"][0] for c in DRIVES)
            bash_sum = sum(row[f"{name}.{census.BASH}.{c}"][0] for c in DRIVES)
            gaps += row[f"{census.COVER_PREFIX}{name}"][0] != drive_sum
            gaps += row[f"{census.COVER_PREFIX}{name}.{census.BASH}"][0] != bash_sum
    return gaps


def _control(lines: list[str], name: str, verdict: str) -> bool:
    """True when ``lines`` hold the control ``name`` with ``verdict``."""
    return any(x.startswith(f"control {name} {verdict} ") for x in lines)


def _absent() -> list[str]:
    """A root no fixture plants."""
    return [f"cs-absent-{secrets.token_hex(8)}"]


# --- the axis counts ------------------------------------------------------------------


def test_every_cell_counts_exactly(pristine: Run) -> None:
    _code, table, _lines = pristine
    miscounted = _miscounted(table)
    assert miscounted == 0


def test_hits_never_abort_and_all_seven_controls_pass(pristine: Run) -> None:
    code, table, lines = pristine
    hits = sum(v[0] for row in table.values() for label, v in row.items()
               if not label.startswith(census.ABSENT_PREFIX))  # fmt: skip
    passed = sum(1 for x in lines if x.startswith("control ") and " PASS " in x)
    summary = f"result controls_passed {CONTROL_COUNT} of {CONTROL_COUNT}; hits never abort"
    has_summary = summary in lines
    last_is_exit_0 = lines[-1] == "exit 0"
    refusals = sum(1 for x in lines if x.startswith("UNMEASURED"))
    assert hits > 0
    assert code == EXIT_OK
    assert passed == CONTROL_COUNT
    assert has_summary
    assert last_is_exit_0
    assert refusals == 0


def test_only_the_drive_letters_are_counted(pristine: Run) -> None:
    _code, table, lines = pristine
    idle_labels = sum(1 for row in table.values() for label in row if label.endswith(f".{IDLE}"))
    idle_lines = sum(1 for x in lines if f".{IDLE} occ " in x)
    assert idle_labels == 0
    assert idle_lines == 0


def test_letter_class_needles_equal_the_per_letter_sum_in_every_cell(
    world: World,
    pristine: Run,
) -> None:
    _code, table, lines = pristine
    gaps = _cover_gaps(table, list(world.roots()))
    covered = _control(lines, "drive_coverage", "PASS")
    assert gaps == 0
    assert covered


def test_every_drive_letter_is_printed_even_with_no_hits(world: World) -> None:
    _c, _t, seeded = _run(world, drives=[*DRIVES, IDLE])
    idle_label = f" repo_root.{IDLE} "
    printed = sum(1 for x in seeded if idle_label in x)
    zero_lines = sum(1 for x in seeded if idle_label in x and x.endswith(" occ 0 lines 0 objs 0"))
    cells = len(census.SCOPES) * len(census.POPULATIONS)
    assert printed == cells
    assert zero_lines == cells


def _coverage_table(gap_population: str, gap: int) -> Table:
    """A census table for one root, its letter-class count ``gap`` ahead in one population.

    The gap sits in ``gap_population`` of the full closure and nowhere else.
    """
    table: Table = {}
    for scope in census.SCOPES:
        for pop in census.POPULATIONS:
            row: dict[str, tuple[int, int, int]] = {}
            for i, drive in enumerate(DRIVES, 1):
                row[f"repo_root.{drive}"] = (i, i, 1)
                row[f"repo_root.{census.BASH}.{drive}"] = (2 * i, 2 * i, 1)
            extra = gap if (scope, pop) == ("full", gap_population) else 0
            per_letter = sum(range(1, len(DRIVES) + 1))
            row[f"{census.COVER_PREFIX}repo_root"] = (per_letter + extra, 1, 1)
            row[f"{census.COVER_PREFIX}repo_root.{census.BASH}"] = (2 * per_letter, 1, 1)
            table[(scope, pop)] = row
    return table


@pytest.mark.parametrize("population", ["blobs", "paths", "messages"])
def test_drive_coverage_reads_every_population_of_the_full_closure(population: str) -> None:
    gap = 3
    off = census.uncovered(_coverage_table(population, gap), ["repo_root"], list(DRIVES))
    clean = census.uncovered(_coverage_table(population, 0), ["repo_root"], list(DRIVES))
    assert off == gap
    assert clean == 0


def test_drive_coverage_never_lets_one_population_offset_another() -> None:
    table = _coverage_table("paths", 2)
    row = table[("full", "messages")]
    occ, lines, objs = row[f"{census.COVER_PREFIX}repo_root"]
    row[f"{census.COVER_PREFIX}repo_root"] = (occ - 2, lines, objs)
    off = census.uncovered(table, ["repo_root"], list(DRIVES))
    assert off == 4  # noqa: PLR2004 - two ahead in paths plus two behind in messages


def test_count_lines_never_name_the_absent_needles(pristine: Run) -> None:
    _code, _table, lines = pristine
    named = sum(1 for x in lines if census.ABSENT_PREFIX in x)
    count_lines = sum(1 for x in lines if x.startswith("count "))
    assert named == 0
    assert count_lines > 0


def test_liveness_reports_each_sidecar_category_exactly(pristine: Run) -> None:
    _code, _table, lines = pristine
    want = {
        census.SIDECAR_ROOT: (2, 3), f"{census.SIDECAR_HIST}1": (4, 4),
        f"{census.SIDECAR_HIST}2": (5, 6), f"{census.SIDECAR_BARE}1": (4, 4),
        census.SIDECAR_WT: (4, 4), census.SIDECAR_WALK: (4, 4),
    }  # fmt: skip
    expected = [
        f"liveness {cat} full_blobs_occ {b} full_all_occ {a} zero_in_history false"
        for cat, (b, a) in want.items()
    ]
    same = [x for x in lines if x.startswith("liveness ")] == expected
    assert same


def test_a_zero_repo_root_residual_fails_its_control(world: World) -> None:
    code, _table, lines = _run(world, world.roots(repo=_absent()))
    root_failed = _control(lines, "root_residual_nonzero", "FAIL")
    sidecar_passed = _control(lines, "sidecar_residual_nonzero", "PASS")
    passed = sum(1 for x in lines if x.startswith("control ") and " PASS " in x)
    summary = f"result controls_passed {CONTROL_COUNT - 1} of {CONTROL_COUNT}; hits never abort"
    has_summary = summary in lines
    refusal_then_exit = lines[-2:] == [FAILED_CONTROL_LINE, "exit 1"]
    assert code == EXIT_FAILED_CONTROL
    assert root_failed
    assert sidecar_passed
    assert passed == CONTROL_COUNT - 1
    assert has_summary
    assert refusal_then_exit


def test_a_zero_sidecar_residual_fails_its_control(world: World) -> None:
    roots = world.roots(
        sidecar=_absent(), hist=[_absent(), _absent()], bare=[_absent()], wt=_absent(),
        walk=_absent(),
    )  # fmt: skip
    code, _table, lines = _run(world, roots)
    zeros = sum(
        1 for x in lines if x.startswith("liveness ") and x.endswith(" zero_in_history true")
    )
    sidecar_failed = _control(lines, "sidecar_residual_nonzero", "FAIL")
    categories_failed = _control(lines, "sidecar_categories_live", "FAIL")
    root_passed = _control(lines, "root_residual_nonzero", "PASS")
    refusal_then_exit = lines[-2:] == [FAILED_CONTROL_LINE, "exit 1"]
    assert code == EXIT_FAILED_CONTROL
    assert sidecar_failed
    assert categories_failed
    assert root_passed
    assert zeros == SIDECAR_CATEGORIES
    assert refusal_then_exit


#: For each sidecar category, the replacements that leave it the only one with hits.
ALONE: Final = {
    "historical cs- folder": ("sidecar", "bare", "wt", "walk"),
    "current sidecar root": ("hist", "bare", "wt", "walk"),
    "bare folder": ("sidecar", "hist", "wt", "walk"),
    "old worktree root": ("sidecar", "hist", "bare", "walk"),
    "old walk harness folder": ("sidecar", "hist", "bare", "wt"),
}


@pytest.mark.parametrize("keep", sorted(ALONE))
def test_each_sidecar_category_alone_carries_the_residual_not_the_liveness(
    world: World, keep: str
) -> None:
    empty = {"sidecar": _absent(), "hist": [], "bare": [], "wt": _absent(), "walk": _absent()}
    code, _table, lines = _run(world, world.roots(**{k: empty[k] for k in ALONE[keep]}))
    sidecar_passed = _control(lines, "sidecar_residual_nonzero", "PASS")
    categories_failed = _control(lines, "sidecar_categories_live", "FAIL")
    assert code == EXIT_FAILED_CONTROL
    assert sidecar_passed
    assert categories_failed


#: Each sidecar category a needle-derivation break can zero, by its root keyword.
ZEROED: Final = {
    "sidecar": census.SIDECAR_ROOT,
    "wt": census.SIDECAR_WT,
    "walk": census.SIDECAR_WALK,
}


@pytest.mark.parametrize("which", sorted(ZEROED))
def test_a_category_absent_from_history_fails_the_liveness_control_alone(
    world: World, which: str
) -> None:
    code, table, lines = _run(world, world.roots(**{which: _absent()}))
    zero = f"liveness {ZEROED[which]} full_blobs_occ 0 full_all_occ 0 zero_in_history true" in lines
    categories_failed = _control(lines, "sidecar_categories_live", "FAIL")
    passed = sum(1 for x in lines if x.startswith("control ") and " PASS " in x)
    count_lines = sum(1 for x in lines if x.startswith("count "))
    _c, _t, full_lines = _run(world)
    full_count_lines = sum(1 for x in full_lines if x.startswith("count "))
    refusal_then_exit = lines[-2:] == [FAILED_CONTROL_LINE, "exit 1"]
    assert code == EXIT_FAILED_CONTROL
    assert zero
    assert categories_failed
    assert passed == CONTROL_COUNT - 1
    assert count_lines == full_count_lines
    assert refusal_then_exit
    assert len(table) == len(census.SCOPES) * len(census.POPULATIONS)


def test_absent_needles_are_live_when_planted(world: World) -> None:
    plant = "cs-absent-plant"
    probe = census.build_scanner(world.roots(), world.hosts, [plant], "absent-plant", list(DRIVES))
    d1, d2 = (d.encode("ascii") for d in DRIVES)
    p = [plant.encode("ascii")]
    buffer = b"\n".join([
        _spell(d1, p, b"\\"), _spell(d2.lower(), p, b"/"), _bash(d1, p, b"/"),
        _bash(d2, p, b"/", lead=b"//"), b"absent-plant",
    ])  # fmt: skip
    got = dict(zip(probe.labels, probe.scan(buffer), strict=True))
    absent = sorted(x for x in probe.labels if x.startswith(census.ABSENT_PREFIX))
    want = sorted(
        [f"{census.ABSENT_PREFIX}root.{d}" for d in DRIVES]
        + [f"{census.ABSENT_PREFIX}root.{census.BASH}.{d}" for d in DRIVES]
        + [f"{census.ABSENT_PREFIX}host"]
    )
    same = absent == want
    live = sum(1 for x in absent if got[x] == (1, 1))
    assert same
    assert live == len(want)


def test_matcher_selfcheck_holds_for_every_needle(world: World) -> None:
    ok = census.matcher_selfcheck(world.roots(), world.hosts, list(DRIVES))
    assert ok is True


def test_walk_is_complete_against_rev_list(pristine: Run) -> None:
    _code, _table, lines = pristine
    walk_passed = _control(lines, "walk_complete", "PASS")
    assert walk_passed


# --- mutant controls: each arm above, seen to go red -----------------------------------


def _mutate_header(module: ModuleType) -> object:
    """parse_commit, but the whole object - header included - read as the message."""
    real = module.parse_commit

    def header_as_message(data: bytes) -> tuple[str, list[str], bytes]:
        tree, parents, _message = real(data)
        return tree, parents, data

    return header_as_message


def _mutate_walk(module: ModuleType) -> object:
    """rev_list_family, but naming one blob the walk never reached."""
    real = module.rev_list_family

    def extra_blob(repo: Path, tip: str) -> dict[str, set[str]]:
        family: dict[str, set[str]] = real(repo, tip)
        family["blob"].add("f" * len(tip))
        return family

    return extra_blob


def _constant(value: object) -> Callable[[ModuleType], object]:
    """A replacement factory that ignores the module and returns ``value``."""
    return lambda _module: value


#: Each mutation: (arm, module attribute, replacement factory, the oracle that must turn red).
MUTANTS: Final = (
    ("matcher_selfcheck", "NAME_TAIL", _constant(b""), "selfcheck"),
    ("utf16 decoding", "text_of", _constant(lambda data: (data, False)), "counts"),
    ("message is the body only", "parse_commit", _mutate_header, "counts"),
    ("host edge", "HOST_EDGE", _constant(frozenset()), "counts"),
    ("drive left edge", "ANY_DRIVE", _constant(re.compile(rb"[a-z]:[\\/]")), "counts"),
    ("walk_complete", "rev_list_family", _mutate_walk, "walk_complete"),
    ("absent_token_zero", "secrets", _constant(SimpleNamespace(token_hex=lambda _n: PLANT)),
     "absent_token_zero"),
    ("drive_coverage", "root_pattern", _constant(lambda _drive, _comps: re.compile(rb"(?!)")),
     "drive_coverage"),
)  # fmt: skip


@pytest.mark.parametrize(
    ("attribute", "factory", "oracle"),
    [m[1:] for m in MUTANTS],
    ids=[m[0] for m in MUTANTS],
)
def test_each_mutant_turns_its_arm_red(
    world: World, monkeypatch: pytest.MonkeyPatch, attribute: str,
    factory: Callable[[ModuleType], object], oracle: str,
) -> None:  # fmt: skip
    replacement = factory(census)
    monkeypatch.setattr(census, attribute, replacement)
    landed = getattr(census, attribute) is replacement
    assert landed
    if oracle == "selfcheck":
        ok = census.matcher_selfcheck(world.roots(), world.hosts, list(DRIVES))
        assert ok is False
        return
    code, table, lines = _run(world)
    if oracle == "counts":
        miscounted = _miscounted(table)
        assert miscounted != 0
        return
    failed = _control(lines, oracle, "FAIL")
    assert code == EXIT_FAILED_CONTROL
    assert failed


# --- the command line -------------------------------------------------------------------


def _main(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    """One in-process CLI run: (exit code, stdout)."""
    code: int = census.main(argv)
    return code, capsys.readouterr().out


def _drive_args() -> list[str]:
    """``--drive`` once per letter of ``DRIVES``."""
    return [arg for d in DRIVES for arg in ("--drive", d)]


def test_cli_prints_counts_and_booleans_only(
    world: World, pristine: Run, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:  # fmt: skip
    monkeypatch.setattr(census, "derive_hosts", lambda: (dict(world.hosts), 0))
    code, text = _main(["--repo", str(world.clone), "--tip", world.tip, *_drive_args()], capsys)
    out = text.splitlines()
    _c, _t, run_lines = pristine
    same_counts = [x for x in out if x.startswith("count ")] == [
        x for x in run_lines if x.startswith("count ")
    ]
    derived = {
        "derive repo_root true (source origin)",
        "derive sidecar_root true (source ancestor)",
        f"derive {census.SIDECAR_HIST} true (source test pattern) folders 2 bare 1 layout 1",
        f"derive {census.SIDECAR_WT} true (source repo root folder name)",
        f"derive {census.SIDECAR_WALK} true (source fixed historical name)",
        "derive main_root true (source local config)",
        f"derive drives {len(DRIVES)} (source arg)",
    }
    missing = len(derived - set(out))
    leaks = [world.base.name, "fakerepo", "fakemain", HOST, "oldlanes", "old-backup", "oldcars",
             WALK_PIN, world.tip, world.tip[:7]]  # fmt: skip
    low = text.lower()
    leaked = sum(1 for s in leaks if s.lower() in low)
    drive_rooted = census.ANY_DRIVE.search(low.encode("ascii", "replace")) is not None
    bash_rooted = census.ANY_BASH.search(low.encode("ascii", "replace")) is not None
    ascii_only = text.isascii()
    summary = f"result controls_passed {CONTROL_COUNT} of {CONTROL_COUNT}; hits never abort"
    has_summary = summary in out
    last_is_exit_0 = out[-1] == "exit 0"
    refusals = sum(1 for x in out if x.startswith("UNMEASURED"))
    assert code == EXIT_OK
    assert same_counts
    assert missing == 0
    assert leaked == 0
    assert not drive_rooted
    assert not bash_rooted
    assert ascii_only
    assert has_summary
    assert last_is_exit_0
    assert refusals == 0


def _other_root(tmp_path: Path, world: World) -> Path:
    """A second repo root, named as the fixture's is, whose own path no blob spells.

    Every other derived root - the sidecar root, both historical folders, the bare folder,
    the old worktree root, the walk folder and MAIN's root - matches the fixture's, so a
    census run against it fails exactly one control: root_residual_nonzero.
    """
    root = tmp_path / world.fake_repo.name
    root.joinpath(".git").mkdir(parents=True)
    root.joinpath(*census.MAIN_CONFIG).parent.mkdir()
    root.joinpath(*census.MAIN_CONFIG).write_bytes(
        json.dumps({census.MAIN_KEY: str(world.fake_main)}).encode("utf-8")
    )
    root.joinpath(*census.HIST_SOURCE).parent.mkdir()
    root.joinpath(*census.HIST_SOURCE).write_bytes(HIST_FIXTURE.encode("utf-8"))
    return root


def test_cli_pins_the_exit_line_the_return_code_and_the_refusal_on_a_failed_control(
    world: World, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:  # fmt: skip
    monkeypatch.setattr(census, "derive_hosts", lambda: (dict(world.hosts), 0))
    root = _other_root(tmp_path, world)
    argv = ["--repo", str(world.clone), "--tip", world.tip, "--root", str(root),
            "--sidecars", str(world.sidecars), *_drive_args()]  # fmt: skip
    code, text = _main(argv, capsys)
    out = text.splitlines()
    root_failed = _control(out, "root_residual_nonzero", "FAIL")
    failed = sum(1 for x in out if x.startswith("control ") and " FAIL " in x)
    summary = f"result controls_passed {CONTROL_COUNT - 1} of {CONTROL_COUNT}; hits never abort"
    has_summary = summary in out
    refusal_then_exit = out[-2:] == [FAILED_CONTROL_LINE, "exit 1"]
    refusals = sum(1 for x in out if x.startswith("UNMEASURED"))
    assert code == EXIT_FAILED_CONTROL
    assert root_failed
    assert failed == 1
    assert has_summary
    assert refusal_then_exit
    assert refusals == 1


#: Which system drive the needle-set arm plants, by letter, as a synthetic value.
SYNTHETIC_SYSTEM_DRIVE: Final = DRIVES[1] + ":"


def _components(text: str) -> list[str]:
    """This module's own split of a root: after its drive letter or its leading '/'."""
    body = re.sub(r"^[A-Za-z]:", "", text)
    return [c for c in re.split(r"[\\/]+", body) if c and c != "."]


def _letter_of(text: str) -> str | None:
    match = re.match(r"([A-Za-z]):", text)
    return match.group(1).upper() if match is not None else None


def test_cli_derives_exactly_the_needle_set_the_fixture_defines(
    world: World,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen: dict[str, tuple[object, ...]] = {}

    def spy_census(*args: object) -> tuple[int, Table]:
        seen["census"] = args
        return EXIT_OK, {}

    real_drives = census.derive_drives

    def spy_drives(root: str, overrides: object, system: object) -> object:
        seen["drives_from"] = (root,)
        return real_drives(root, overrides, system)

    monkeypatch.setattr(census, "derive_hosts", lambda: (dict(world.hosts), 0))
    monkeypatch.setattr(census, "run_census", spy_census)
    monkeypatch.setattr(census, "derive_drives", spy_drives)
    monkeypatch.setenv("SYSTEMDRIVE", SYNTHETIC_SYSTEM_DRIVE)
    code, _text = _main(["--repo", str(world.clone), "--tip", world.tip], capsys)
    call = seen.get("census", (None,) * 6)
    tip, roots, hosts, drives = call[1], call[2], call[3], call[4]
    want_roots = {
        "repo_root": _components(str(world.fake_repo)),
        census.SIDECAR_ROOT: _components(str(world.sidecars)),
        f"{census.SIDECAR_HIST}1": HIST_NAMES[0],
        f"{census.SIDECAR_HIST}2": HIST_NAMES[1],
        f"{census.SIDECAR_BARE}1": HIST_BARE[0],
        census.SIDECAR_WT: [world.fake_repo.name + WT_SUFFIX_PIN],
        census.SIDECAR_WALK: [WALK_PIN],
        "main_root": _components(str(world.fake_main)),
    }
    want_drives: list[str] = []
    for letter in (_letter_of(str(world.fake_repo)), DRIVES[1]):
        if letter is not None and letter not in want_drives:
            want_drives.append(letter)
    drives_from = str(seen.get("drives_from", ("",))[0])
    from_root = census.same_path(Path(drives_from), world.fake_repo) if drives_from else False
    distinct = not census.same_path(world.clone, world.fake_repo)
    same_roots = roots == want_roots
    same_drives = drives == want_drives
    same_hosts = hosts == world.hosts
    same_tip = tip == world.tip
    assert code == EXIT_OK
    assert same_roots
    assert same_drives
    assert same_hosts
    assert same_tip
    assert distinct
    assert from_root


def test_cli_accepts_the_checkout_itself_as_its_root(
    world: World,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(census, "derive_hosts", lambda: (dict(world.hosts), 0))
    argv = ["--repo", str(world.fake_repo), "--tip", world.tip, "--root", str(world.fake_repo),
            "--sidecars", str(world.sidecars), *_drive_args()]  # fmt: skip
    code, text = _main(argv, capsys)
    out = text.splitlines()
    root_from_arg = "derive repo_root true (source arg)" in out
    sidecars_from_arg = "derive sidecar_root true (source arg)" in out
    assert code == EXIT_OK
    assert root_from_arg
    assert sidecars_from_arg


@pytest.mark.parametrize(
    ("case", "secret"),
    [("bad tip", "not-a-sha"), ("no tip", ""), ("unknown option", "--bogus"),
     ("bad drive", "KQ")],
)  # fmt: skip
def test_cli_refusals_exit_2_and_echo_no_value(
    world: World,
    capsys: pytest.CaptureFixture[str],
    case: str,
    secret: str,
) -> None:
    argv = {
        "bad tip": ["--repo", str(world.clone), "--tip", secret, *_drive_args()],
        "no tip": ["--repo", str(world.clone), *_drive_args()],
        "unknown option": [secret, str(world.base)],
        "bad drive": ["--repo", str(world.clone), "--tip", world.tip, "--drive", secret],
    }[case]
    code, text = _main(argv, capsys)
    out = text.splitlines()
    echoed = bool(secret) and secret in text
    base_echoed = world.base.name in text
    last_is_exit_2 = out[-1] == "exit 2"
    refusal = out[-2].startswith("UNMEASURED ")
    assert code == EXIT_UNMEASURED
    assert not echoed
    assert not base_echoed
    assert last_is_exit_2
    assert refusal


def _bad_root(tmp_path: Path, source: str | None) -> Path:
    """A repo root with a git dir, a local config and ``source`` as its pattern file."""
    root = tmp_path / "BadRoot"
    root.joinpath(".git").mkdir(parents=True)
    root.joinpath(*census.MAIN_CONFIG).parent.mkdir()
    root.joinpath(*census.MAIN_CONFIG).write_bytes(
        json.dumps({census.MAIN_KEY: str(tmp_path / "FakeMain")}).encode("utf-8")
    )
    if source is not None:
        root.joinpath(*census.HIST_SOURCE).parent.mkdir()
        root.joinpath(*census.HIST_SOURCE).write_bytes(source.encode("utf-8"))
    return root


@pytest.mark.parametrize(
    ("source", "phrase"),
    [(None, "UNMEASURED historical sidecar folders not derivable: the test pattern source is "
            "unreadable"),
     (HIST_FIXTURE + '_SIDECAR_NAME += "|x"\n', "UNMEASURED historical sidecar folders not "
                                                "derivable: the pattern is augmented")],
    ids=["missing", "augmented"],
)  # fmt: skip
def test_cli_fails_closed_on_the_pattern_source(
    world: World,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    source: str | None,
    phrase: str,
) -> None:
    root = _bad_root(tmp_path, source)
    argv = ["--repo", str(world.clone), "--tip", world.tip, "--root", str(root),
            "--sidecars", str(world.sidecars), *_drive_args()]  # fmt: skip
    code, text = _main(argv, capsys)
    refused = phrase in text.splitlines()
    assert code == EXIT_UNMEASURED
    assert refused


def test_the_script_runs_as_a_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(AXIS_SOURCE), "--bogus"],
        capture_output=True, timeout=TIMEOUT, check=False,
    )  # fmt: skip
    out = completed.stdout.decode("ascii").splitlines()
    last_is_exit_2 = bool(out) and out[-1] == "exit 2"
    quiet = completed.stderr == b""
    assert completed.returncode == EXIT_UNMEASURED
    assert last_is_exit_2
    assert quiet


# --- the derivations --------------------------------------------------------------------


def _refused(phrase: str, func: Callable[..., object], *args: object) -> bool:
    """True when ``func(*args)`` raises the census's refusal with ``phrase`` in its reason."""
    try:
        func(*args)
    except census.UnmeasuredError as exc:
        return phrase in exc.reason
    return False


def test_repo_root_is_derived_from_the_clone_origin(world: World) -> None:
    root, source = census.derive_repo_root(world.clone, None)
    same = census.same_path(root, world.fake_repo)
    assert same
    assert source == "origin"


def test_repo_root_without_an_origin_asks_for_root(world: World) -> None:
    refused = _refused("pass --root", census.derive_repo_root, world.fake_repo, None)
    assert refused


def test_repo_root_from_a_remote_origin_is_refused(tmp_path: Path) -> None:
    env = _git_env(tmp_path)
    repo = tmp_path / "Remote"
    _git(tmp_path, "init", "-q", str(repo), env=env)
    _git(repo, "config", "remote.origin.url", "https://example.invalid/x.git", env=env)
    refused = _refused("origin is not a local path", census.derive_repo_root, repo, None)
    assert refused


def test_repo_root_from_an_origin_naming_the_clone_itself_is_refused(tmp_path: Path) -> None:
    env = _git_env(tmp_path)
    repo = tmp_path / "Selfish"
    _git(tmp_path, "init", "-q", str(repo), env=env)
    _git(repo, "config", "remote.origin.url", str(repo), env=env)
    repo.joinpath(*census.MAIN_CONFIG).parent.mkdir()
    repo.joinpath(*census.MAIN_CONFIG).write_bytes(b"{}")
    refused = _refused("the clone itself", census.derive_repo_root, repo, None)
    assert refused


def test_sidecar_root_is_derived_from_the_clone_ancestors(world: World) -> None:
    root, source = census.derive_sidecar_root(world.clone, world.fake_repo, None)
    same = census.same_path(root, world.sidecars)
    assert same
    assert source == "ancestor"


def test_a_sidecars_override_without_the_markers_is_refused(world: World) -> None:
    refused = _refused(
        "does not hold the sidecar markers", census.derive_sidecar_root, world.clone,
        world.fake_repo, str(world.fake_main),
    )  # fmt: skip
    assert refused


def _unc_path(*parts: str) -> str:
    """A network-share path, built at run time; its anchor is no local drive's."""
    return "//" + "/".join(parts)


def test_the_drive_scan_reads_the_repo_root_drive_not_the_clone_drive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scanned: list[Path] = []

    def spy_scan(drive_root: Path) -> Path:
        scanned.append(drive_root)
        return tmp_path

    clone = tmp_path / "Lone"
    repo_root = Path(_unc_path("srv", "share", "Repo"))
    monkeypatch.setattr(census, "drive_scan", spy_scan)
    root, source = census.derive_sidecar_root(clone, repo_root, None)
    want = Path(repo_root.anchor)
    distinct = want != Path(clone.anchor)
    read_root_drive = scanned == [want]
    chosen = root == tmp_path
    assert distinct
    assert read_root_drive
    assert chosen
    assert source == "drive-scan"


def _marked(parent: Path, name: str, markers: int) -> Path:
    """A folder under ``parent`` holding the first ``markers`` sidecar markers."""
    folder = parent / name
    for marker in census.SIDECAR_MARKERS[:markers]:
        folder.joinpath(*marker).mkdir(parents=True, exist_ok=True)
    folder.mkdir(exist_ok=True)
    return folder


def test_the_drive_scan_takes_its_one_candidate_over_every_decoy(tmp_path: Path) -> None:
    _marked(tmp_path, "Bare", 0)
    _marked(tmp_path, "Half", 1)
    tmp_path.joinpath("note.txt").write_bytes(b"x\n")
    only = _marked(tmp_path, "Whole", len(census.SIDECAR_MARKERS))
    chosen = census.drive_scan(tmp_path) == only
    assert chosen


@pytest.mark.parametrize("candidates", [0, 2, 3])
def test_the_drive_scan_refuses_none_or_several_candidates(tmp_path: Path, candidates: int) -> None:
    _marked(tmp_path, "Half", 1)
    for i in range(candidates):
        _marked(tmp_path, f"Whole{i}", len(census.SIDECAR_MARKERS))
    refused = _refused("none or several", census.drive_scan, tmp_path)
    assert refused


def test_main_root_is_read_from_the_local_config(world: World) -> None:
    same = census.derive_main_root(world.fake_repo) == census.split_root(str(world.fake_main))
    assert same


def test_main_root_from_an_empty_config_is_refused(tmp_path: Path) -> None:
    tmp_path.joinpath(*census.MAIN_CONFIG).parent.mkdir()
    tmp_path.joinpath(*census.MAIN_CONFIG).write_bytes(b"{}")
    refused = _refused("names no root", census.derive_main_root, tmp_path)
    assert refused


def test_historical_folders_are_read_from_the_pattern_source(world: World) -> None:
    same = census.derive_hist_sidecars(world.fake_repo) == (HIST_NAMES, HIST_BARE, 1)
    assert same


def test_this_tree_pattern_source_is_readable() -> None:
    hist, bare, layout = census.derive_hist_sidecars(REPO_ROOT)
    folders, bares = len(hist), len(bare)
    assert folders == 2  # noqa: PLR2004 - the two cs- folders
    assert bares == 1
    assert layout == 1


@pytest.mark.parametrize(("source", "want"), HIST_GOOD)
def test_historical_folders_read_each_good_source(
    tmp_path: Path,
    source: str,
    want: tuple[list[list[str]], list[list[str]], int],
) -> None:
    tmp_path.joinpath(*census.HIST_SOURCE).parent.mkdir()
    tmp_path.joinpath(*census.HIST_SOURCE).write_bytes(source.encode("utf-8"))
    same = census.derive_hist_sidecars(tmp_path) == want
    assert same


@pytest.mark.parametrize(("source", "phrase"), HIST_BAD)
def test_historical_folders_fail_closed_on_each_bad_source(
    tmp_path: Path,
    source: str,
    phrase: str,
) -> None:
    tmp_path.joinpath(*census.HIST_SOURCE).parent.mkdir()
    tmp_path.joinpath(*census.HIST_SOURCE).write_bytes(source.encode("utf-8"))
    refused = _refused(phrase, census.derive_hist_sidecars, tmp_path)
    assert refused


def test_the_old_worktree_root_is_the_repo_folder_plus_its_suffix(world: World) -> None:
    same = census.derive_wt_root(world.fake_repo) == [world.fake_repo.name + WT_SUFFIX_PIN]
    assert same


def test_drives_come_from_the_root_then_the_system_drive() -> None:
    d1, d2 = DRIVES
    drives, source = census.derive_drives(_drive_path(d1.lower(), "Some", "Repo"), None, d2 + ":")
    same = drives == list(DRIVES)
    assert same
    assert source == "derived"


def test_drives_are_never_repeated() -> None:
    d1, _d2 = DRIVES
    drives, _source = census.derive_drives(_drive_path(d1, "x", sep="/"), None, d1.lower() + ":")
    same = drives == [d1]
    assert same


def test_drive_overrides_win_in_their_own_order() -> None:
    d1, d2 = DRIVES
    root = _drive_path(d1, "x", sep="/")
    drives, source = census.derive_drives(root, [d2.lower(), d1 + ":", d2], None)
    same = drives == [d2, d1]
    assert same
    assert source == "arg"


def test_no_derivable_drive_asks_for_drive() -> None:
    refused = _refused("pass --drive", census.derive_drives, _posix_path("srv", "repo"), None, None)
    assert refused


@pytest.mark.parametrize("bad", ["", "KQ", "1", ":"])
def test_a_drive_override_that_is_not_one_letter_is_refused(bad: str) -> None:
    refused = _refused(
        "one drive letter", census.derive_drives, _posix_path("srv", "repo"), [bad], None
    )
    assert refused


def test_split_root_reads_drive_and_posix_roots() -> None:
    drive_comps = census.split_root(_drive_path(DRIVES[0], "a", ".", "b") + "//c")
    posix_comps = census.split_root(_posix_path("srv", "b"))
    same_drive = drive_comps == ["a", "b", "c"]
    same_posix = posix_comps == ["srv", "b"]
    assert same_drive
    assert same_posix


#: Roots split_root must refuse, built at run time by name.
BAD_ROOTS: Final = {
    "bare drive": lambda: DRIVES[0] + ":\\",
    "relative": lambda: "relative\\x",
    "unc backslash": lambda: "\\\\" + "server\\share",
    "unc slash": lambda: "//" + "server/share",
    "posix root alone": lambda: "/",
    "dot-dot segment": lambda: _posix_path("a", "..", "b"),
}


@pytest.mark.parametrize("case", sorted(BAD_ROOTS))
def test_split_root_refuses_a_root_with_no_usable_components(case: str) -> None:
    refused = _refused("", census.split_root, BAD_ROOTS[case]())
    assert refused


def test_host_filter_drops_placeholders_and_keeps_plain_names() -> None:
    kept = sum(
        1
        for x in ("localhost", "127.0.0.1", "fe80::1", "pc", "example.com", "a.example.com", "")
        if census.host_usable(x)
    )
    plain = census.host_usable("cafe") and census.host_usable("ab-12")
    assert kept == 0
    assert plain


def test_derived_hosts_are_usable() -> None:
    hosts, _excluded = census.derive_hosts()
    count = len(hosts)
    unusable = sum(1 for name in hosts.values() if not census.host_usable(name))
    assert count >= 1
    assert unusable == 0


@pytest.mark.parametrize("bad_tip", ["HEAD", "zero", "short", "upper"])
def test_preconditions_refuse_a_tip_that_is_not_a_full_lower_hex_commit(
    world: World,
    bad_tip: str,
) -> None:
    tip = {"HEAD": "HEAD", "zero": "0" * len(world.tip), "short": world.tip[:12],
           "upper": world.tip.upper()}[bad_tip]  # fmt: skip
    refused = _refused("", census.preconditions, world.clone, tip, lambda _line: None)
    assert refused


def test_sidecar_labels_are_the_sidecar_categories_only() -> None:
    d1, d2 = DRIVES
    sidecar = (f"sidecar_root.{d1}", f"sidecar_root.bash.{d2}", f"sidecar_hist1.{d2}",
               f"sidecar_hist12.bash.{d1}", f"sidecar_bare1.{d1}", f"sidecar_wt.bash.{d2}",
               f"sidecar_walk.{d2}")  # fmt: skip
    other = (f"repo_root.{d1}", f"main_root.bash.{d2}", f"absent.root.{d1}",
             f"sidecar_histx.{d1}", f"sidecar_barex.{d1}", f"sidecar_wtx.{d1}",
             f"sidecar_walk1.{d2}", census.ANY_LABEL, census.BASH_LABEL, "host.dns")  # fmt: skip
    wrong = sum(1 for x in sidecar if not census.is_sidecar_label(x)) + sum(
        1 for x in other if census.is_sidecar_label(x)
    )
    category = census.sidecar_category(f"sidecar_bare1.bash.{d1}") == "sidecar_bare1"
    assert wrong == 0
    assert category
