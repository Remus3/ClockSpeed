#!/usr/bin/env python3
"""CS-910 - resolve an external tool to an absolute path, from PATH and only PATH.

WHY THIS MODULE EXISTS. Naming a tool and letting the spawn find it is a local
code-execution vector on Windows, because the CURRENT DIRECTORY is searched
before PATH. MEASURED 2026-09-05 on the pinned interpreter, in a directory
holding a planted executable and with the gate variable absent from the
environment: ``shutil.which("openssl")`` returned a RELATIVE path to the plant,
and ``scripts/make_cert.py`` spawned it. So the tool a script runs was chosen by
wherever the process happened to be standing.

THE GATE, AND WHY A FIRST PROBE OF THIS CLASS MEANS NOTHING. CPython decides
whether to prepend the current directory by asking the Win32
``NeedCurrentDirectoryForExePath``, which consults an environment variable that
is set at NEITHER machine nor user scope on the development machine. Some shells
set it for themselves. A probe run under one of those comes back clean and has
measured nothing at all, which is why every arm that grades this removes the
variable from the CHILD environment rather than trusting what it inherited. The
same gate governs ``CreateProcess``, so a bare ``"git"`` in an argv is the same
defect wearing different syntax and is graded by the same census.

NOT MODELLED ON ``shutil.which``. It is the function the finding is ABOUT. What
is mirrored here is ``shell/lib/supervisor.js::resolveInterpreter``, which solved
this class on the Node side: walk PATH, discard any entry that is not rooted,
never consult the working directory, and answer a NAMED REFUSAL rather than a
guess. A relative PATH entry is discarded for exactly the reason the current
directory is - ``.`` is how the current directory arrives inside a PATH, and an
entry that is not rooted is one whose meaning depends on where the process is
standing.

DO NOT FIX THIS CLASS BY SPELLING A PATH. CLAUDE.md non-negotiable 3 forbids an
absolute tool path in a tracked file: a path can carry the Windows account name,
and a tool named by where it lives today is the hardcoded-interpreter defect
BOOTSTRAP.md section 2.5 forbids. Resolution is therefore a RUNTIME act against
the environment the process was handed. A PATH MAY BE COMPUTED HERE, BUT NONE
MAY BE SPELLED HERE - every string this module returns is built from what the
caller or the environment supplied. The two regular expressions below describe
the SHAPE of a rooted directory and are patterns rather than paths; they name no
drive, no directory and no account.

WHAT THIS DOES NOT DEFEND AGAINST, stated rather than implied:

  - a PATH whose own entries are attacker-controlled;
  - an absolute entry containing parent-directory segments;
  - a tool that is legitimately on PATH and has been replaced in place.

All three require the attacker to already control the environment or a directory
the operator trusts, at which point the tool being resolved is not the weakest
thing they can reach. The property offered here is narrower and exact: NOTHING
THIS MODULE RETURNS CAN BE SUPPLIED BY THE WORKING DIRECTORY.

IT IMPORTS THE STANDARD LIBRARY AND NOTHING ELSE. Nothing from ``scripts/``, in
particular: ``tools/facts_probe.py`` already imports ``scripts/verify_env.py``,
so a back-import would close a cycle. Nothing from ``clockspeed/`` either -
``docs/ARCHITECTURE.md`` permits ``tools/`` to import the package and not the
reverse, and a resolver that needed the package could not be used by the gates
that run before it is installed.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# The refusals - a named word for every way this declines to answer
# ---------------------------------------------------------------------------

# Each one is a REFUSAL rather than a None, so a caller that wants to know which
# question went unanswered can ask, and a caller that only wants the answer can
# read `.path` and get None. A bare None collapses "PATH was unreadable" into
# "the tool is not installed", and those need different operator actions.

#: The name was not a bare tool name - empty, or carrying a directory part.
REFUSE_UNNAMED_TOOL: Final = "REFUSE_UNNAMED_TOOL"

#: PATH held no usable entry at all, so nothing could be searched.
REFUSE_UNSEARCHABLE_PATH: Final = "REFUSE_UNSEARCHABLE_PATH"

#: Windows only - PATHEXT named no suffix, so no candidate could be built.
REFUSE_UNKNOWN_EXTENSIONS: Final = "REFUSE_UNKNOWN_EXTENSIONS"

#: PATH was searched in full and nothing answered.
REFUSE_NO_TOOL: Final = "REFUSE_NO_TOOL"

#: Every refusal this module can produce. Published so an arm can assert over
#: the whole vocabulary instead of over the members somebody remembered.
#:
#: ONE MEMBER OF THE NODE VOCABULARY IS DELIBERATELY ABSENT.
#: ``shell/lib/supervisor.js`` carries a REFUSE_UNTESTABLE_CANDIDATE for a probe
#: that is not a function, because JavaScript cannot say that in a signature.
#: Python can, and mypy proves the branch unreachable, so carrying it here would
#: put a refusal in this set that nothing can produce - a member no arm could
#: exercise and every arm would have to excuse. A non-callable probe raises
#: TypeError instead, which is loud and legible.
REFUSALS: Final = frozenset(
    {
        REFUSE_UNNAMED_TOOL,
        REFUSE_UNSEARCHABLE_PATH,
        REFUSE_UNKNOWN_EXTENSIONS,
        REFUSE_NO_TOOL,
    }
)

# ---------------------------------------------------------------------------
# The shapes - patterns, never paths
# ---------------------------------------------------------------------------

#: What a Windows PATH entry has to look like before it is searched at ALL:
#: drive-rooted, or a UNC share.
#:
#: WRITTEN AS A PATTERN RATHER THAN AS A TEST FOR A LEADING SEPARATOR, because
#: the two near-misses are the whole point. ``C:name`` is rooted on a DRIVE but
#: relative to that drive's own current directory, and a leading separator with
#: no drive is relative to the current drive. Both read as absolute, neither is,
#: and both would reintroduce exactly the dependence on where the process is
#: standing that this module exists to remove.
WINDOWS_ROOTED: Final = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\[^\\/])")

#: The same question on POSIX, where it has a one-character answer.
POSIX_ROOTED: Final = re.compile(r"^/")

#: A trailing separator on a PATH entry, which a hand-written PATH often has.
TRAILING_SEPARATORS: Final = re.compile(r"[\\/]+$")

#: What disqualifies a NAME. A tool name carrying any of these is not a name to
#: be resolved but a path already chosen, and this module resolves names.
#: ``:`` is included on both platforms: it introduces a drive or an alternate
#: data stream on Windows, and it is the PATH separator on POSIX, so a name
#: holding one could never have come from an ordinary caller.
NAME_IS_A_PATH: Final = re.compile(r"[\\/:]")

#: How PATH separates its entries, per platform.
WINDOWS_LIST_SEPARATOR: Final = ";"
POSIX_LIST_SEPARATOR: Final = ":"

#: What joins a directory to a file name, per platform.
WINDOWS_SEPARATOR: Final = "\\"
POSIX_SEPARATOR: Final = "/"

#: The suffix list used where a platform has no notion of one. A single empty
#: string, so the bare name is the only candidate built.
NO_SUFFIXES: Final = ("",)

#: The environment names read when a caller supplies neither.
PATH_VARIABLE: Final = "PATH"
PATHEXT_VARIABLE: Final = "PATHEXT"


@dataclass(frozen=True)
class Resolution:
    """What one resolution attempt produced.

    Exactly one of the two fields carries the answer, and :attr:`ok` is the one
    place that relationship is stated. A caller reading ``path`` alone is never
    misled - it is None on every refusal - and a caller that wants the reason
    reads ``refusal``.

    Attributes:
        path: An ABSOLUTE path to the tool, or None.
        refusal: A named refusal, or the empty string when ``path`` is set.
    """

    path: str | None
    refusal: str

    @property
    def ok(self) -> bool:
        """True exactly when a tool was resolved."""
        return self.path is not None and not self.refusal


def _entries(value: str, separator: str) -> list[str]:
    """Split a raw list value into its usable entries.

    Args:
        value: The raw environment value.
        separator: What separates its entries.

    Returns:
        The trimmed, non-empty entries, in order. Possibly empty.
    """
    return [entry.strip() for entry in value.split(separator) if entry.strip()]


def _default_probe(candidate: str) -> bool:
    """Whether ``candidate`` names something this process could launch.

    Args:
        candidate: An absolute path. Never a bare name.

    Returns:
        True when it is a file the process may execute.
    """
    try:
        return Path(candidate).is_file() and os.access(candidate, os.X_OK)
    except (OSError, ValueError):
        # A candidate the platform will not even answer about is not a tool.
        # Falling closed here matters: this resolver is reached from a
        # SessionStart hook and a pre-commit gate, and an exception escaping
        # would turn a malformed PATH entry into a crash rather than a refusal.
        #
        # ValueError IS CAUGHT DELIBERATELY AND IS NOT REDUNDANT. An embedded
        # null in a PATH entry reaches `os.stat` as a ValueError rather than an
        # OSError. MEASURED on the running interpreter: `Path.is_file()` swallows
        # it and answers False - but that is a behaviour of THIS version, and
        # this project supports back to 3.13. Catching it here makes the refusal
        # a property of this module rather than one borrowed from pathlib.
        return False


def _suffixes(name: str, path_ext: str | None, windows: bool) -> list[str] | None:
    """The suffixes to try after ``name``, in order, or None to refuse.

    A NAME THAT ALREADY CARRIES A KNOWN SUFFIX IS TRIED BARE FIRST, which is what
    Windows itself does. Without that, a caller asking for ``git.exe`` would only
    ever be offered ``git.exe.EXE``.

    A BARE NAME IS OTHERWISE NEVER OFFERED ON WINDOWS. An extension-less file is
    not launchable by the call that spawns it, so such a candidate could only be
    a false positive.

    Args:
        name: The tool name, already validated.
        path_ext: The raw suffix list, or None to read the environment.
        windows: Whether Windows rules apply.

    Returns:
        The suffixes, or None when none could be derived.
    """
    if not windows:
        return list(NO_SUFFIXES)
    raw = os.environ.get(PATHEXT_VARIABLE, "") if path_ext is None else path_ext
    # A suffix that does not begin with a separator dot cannot name an
    # extension, so it is dropped rather than concatenated into a candidate
    # that could never match anything.
    found = [entry for entry in _entries(raw, WINDOWS_LIST_SEPARATOR) if entry.startswith(".")]
    if not found:
        return None
    if any(name.upper().endswith(entry.upper()) for entry in found):
        return ["", *found]
    return found


def resolve(
    name: str,
    *,
    path_value: str | None = None,
    path_ext: str | None = None,
    is_executable: Callable[[str], bool] | None = None,
    windows: bool | None = None,
) -> Resolution:
    """Find ``name`` as an absolute path, searching PATH and only PATH.

    THE CURRENT DIRECTORY IS NEVER CONSULTED, and neither is any PATH entry that
    is not rooted. See this module's docstring for the measurement that makes
    that the whole purpose of the function rather than a nicety.

    ORDER IS DIRECTORY-MAJOR - every suffix in one directory before moving to the
    next - which is the order Windows itself searches in. Getting it backwards
    would let a suffix earlier in the list win from a directory later in PATH.

    THE PROBE IS INJECTABLE SO THE PROPERTY IS GRADABLE ANYWHERE. Asking the real
    filesystem is the default and is what every caller in this repository uses;
    an arm that wants to prove the search ORDER, or to prove a rooted-entry
    refusal on a platform whose rules differ, supplies its own. ``windows`` is
    injectable for the same reason: CI runs this suite on Linux as well, and a
    Windows-only rule that only Windows can grade is a rule half the runs skip.

    Args:
        name: A bare tool name, with no directory part.
        path_value: The raw PATH, or None to read the environment. Pass ``""``
            to state that there is no PATH rather than to read one.
        path_ext: The raw executable-suffix list, or None to read the
            environment. Ignored off Windows.
        is_executable: Whether a candidate names something runnable, called with
            absolute paths only. None uses the filesystem.
        windows: Whether Windows rules apply. None asks the running platform.

    Returns:
        A :class:`Resolution` carrying an absolute path or a named refusal.
    """
    on_windows = os.name == "nt" if windows is None else bool(windows)

    if not name or NAME_IS_A_PATH.search(name):
        return Resolution(None, REFUSE_UNNAMED_TOOL)

    raw_path = os.environ.get(PATH_VARIABLE, "") if path_value is None else path_value
    list_separator = WINDOWS_LIST_SEPARATOR if on_windows else POSIX_LIST_SEPARATOR
    directories = _entries(raw_path, list_separator)
    if not directories:
        return Resolution(None, REFUSE_UNSEARCHABLE_PATH)

    suffixes = _suffixes(name, path_ext, on_windows)
    if suffixes is None:
        return Resolution(None, REFUSE_UNKNOWN_EXTENSIONS)

    probe = _default_probe if is_executable is None else is_executable

    rooted = WINDOWS_ROOTED if on_windows else POSIX_ROOTED
    joiner = WINDOWS_SEPARATOR if on_windows else POSIX_SEPARATOR

    for directory in directories:
        # THE FILTER IS HERE AND NOT IN A PRIOR PASS, so a directory that fails
        # it is SKIPPED rather than repaired into something searchable.
        if not rooted.match(directory):
            continue
        base = TRAILING_SEPARATORS.sub("", directory) + joiner
        for suffix in suffixes:
            candidate = base + name + suffix
            # `is True` rather than truthiness, mirroring the Node resolver: an
            # injected probe that answers with something other than a boolean
            # has lost track of the question, and a truthy non-answer would be
            # read as yes.
            if probe(candidate) is True:
                return Resolution(candidate, "")

    # Searched, and nothing answered. A refusal rather than the name, so a
    # caller that spawned the result without checking would spawn None and fail
    # loudly rather than silently running whatever was nearest.
    return Resolution(None, REFUSE_NO_TOOL)


def resolve_tool(
    name: str,
    *,
    path_value: str | None = None,
    path_ext: str | None = None,
    is_executable: Callable[[str], bool] | None = None,
    windows: bool | None = None,
) -> str | None:
    """The absolute path to ``name``, or None.

    THE SHAPE ``shutil.which`` HAS, so a call site changes by one identifier and
    keeps its existing None handling. What changes is the answer: this one cannot
    be supplied by the working directory.

    Args:
        name: A bare tool name, with no directory part.
        path_value: The raw PATH, or None to read the environment.
        path_ext: The raw executable-suffix list, or None to read the
            environment.
        is_executable: Whether a candidate names something runnable.
        windows: Whether Windows rules apply. None asks the running platform.

    Returns:
        An absolute path, or None on any refusal.
    """
    return resolve(
        name,
        path_value=path_value,
        path_ext=path_ext,
        is_executable=is_executable,
        windows=windows,
    ).path
