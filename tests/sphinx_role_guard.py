#!/usr/bin/env python3
"""CS-871 - a Sphinx role in a ``tests/`` module resolves, or it is not a citation.

WHY THIS MODULE EXISTS. ``tests/test_docs_citations.py`` grades the shape
``<path>.py::<name>`` and its population is the tracked DOCS. A cross reference
written as a Sphinx role - the symbol in backticks behind ``:func:`` or
``:data:`` - is a different SPELLING of the same property, and it lives inside
test modules, which that population does not contain at all. Two ``:func:``
roles naming a function bound nowhere shipped inside the very commit that
repaired that fault class, and an adjudicator found them by READING. Nothing
mechanical did.

THE PROPERTY IS RESOLUTION, NOT SPELLING, and the item that filed this module
says so in as many words: a guard that learns one role and stops has bought one
spelling. So the role vocabulary is DECLARED in :data:`ROLE_DISPOSITIONS` and
the corpus is asserted against it - a seventh spelling appearing in a test
module reddens this guard until somebody classifies it, rather than passing in
the silence that let the first two through.

THE RESOLVER IS IMPORTED, NOT TRANSCRIBED.
:func:`tests.test_docs_citations.module_scope_names` supplies the module-scope
half and :func:`tests.bare_path_guard.module_file` supplies the dotted-name to
path map. A second copy of either is a second place to get it subtly wrong,
which is the finding CS-892 records about the memory walk.

THREE TRAPS SHAPE THE RESOLUTION, each measured on this corpus before the walk
was written.

1. A MODULE'S NAMESPACE IS WIDER THAN ITS MODULE SCOPE. A role inside a class
   docstring may name a method of that class, and a role anywhere in the module
   may name something the module IMPORTED. Resolving against module scope alone
   reports both dead, which manufactures findings on correct prose.
   :func:`module_namespace` states that widening rather than hiding it.

2. A QUALIFIED ROLE IS RESOLVED AGAINST THE MODULE IT NAMES. A test module that
   legitimately points at a symbol in another module writes the dotted path, and
   the head of that path is not - and should not have to be - a name the citing
   module binds. :func:`dotted_target_resolves` reads the named module's own
   namespace instead. This is also the REPAIR shape for an unqualified
   cross-module role: qualify it, do not delete it.

3. AN UNRESOLVED ROLE IS NOT A ROLE WITH A TYPO IN THE MODULE PATH. A dotted
   target whose leading segments name no file on disk is reported as an
   unresolved SYMBOL, because "no such module" and "no such name in that module"
   are both the same defect to the reader of the prose - a written identifier
   that does not resolve.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final

from tests.bare_path_guard import REPO_ROOT, module_file
from tests.test_docs_citations import module_scope_names

#: Every Sphinx role spelling this corpus is allowed to contain, mapped to
#: either :data:`GRADED` or the reason it is not graded yet. THE TABLE IS AN
#: ALLOWLIST AND IT IS ASSERTED AS AN EQUALITY against the corpus, not as a
#: subset: a denylist of known-bad spellings forgives every spelling nobody
#: thought of, which is the defect this project has measured wearing four
#: different fields across four green commits.
#:
#: ``:func:``, ``:data:`` and ``:class:`` all name something a module's own
#: namespace can bind, so one resolver answers all three. ``:attr:`` and
#: ``:meth:`` name a member of a class rather than a module-level symbol, and
#: ``:mod:`` names a module rather than a symbol in one; each needs a different
#: resolution and each is filed as CS-1075 rather than graded badly here.
GRADED: Final = "GRADED"

ROLE_DISPOSITIONS: Final[Mapping[str, str]] = {
    "func": GRADED,
    "data": GRADED,
    "class": GRADED,
    "attr": "CS-1075 - names a class member, which module-scope resolution cannot answer",
    "meth": "CS-1075 - names a class member, which module-scope resolution cannot answer",
    "mod": "CS-1075 - names a module rather than a symbol bound inside one",
}

#: The tests-package prefix whose modules this guard reads.
TESTS_PREFIX: Final = "tests/"

#: Any Sphinx role with a backticked target. The role name is captured so the
#: corpus can be graded against :data:`ROLE_DISPOSITIONS` rather than filtered
#: down to the graded spellings before anybody can see what else is there.
ROLE_RE: Final = re.compile(r":(?P<role>[a-z]+):`(?P<target>[^`]+)`")


def graded_roles() -> frozenset[str]:
    """The role spellings :func:`unresolved_roles` actually resolves.

    Returns:
        The keys of :data:`ROLE_DISPOSITIONS` marked :data:`GRADED`.
    """
    return frozenset(
        role for role, disposition in ROLE_DISPOSITIONS.items() if disposition == GRADED
    )


def module_namespace(source: str) -> frozenset[str]:
    """Every name the module makes available to a cross reference in its prose.

    A DELIBERATE SUPERSET of
    :func:`tests.test_docs_citations.module_scope_names`, which is imported
    rather than re-implemented and supplies the module-scope half. Two
    widenings, and both were measured necessary on this corpus:

    NESTED DEFINITIONS. A role inside a class docstring naming a method of that
    class is correct prose. Module scope does not contain the method.

    IMPORTED NAMES. ``from tests.bare_path_guard import module_file`` binds
    ``module_file`` in this module, so a role naming it here resolves. Module
    scope as that function computes it does not include an import.

    Args:
        source: The module's full text.

    Returns:
        Module-scope names, every nested function and class name, and every
        name an import statement binds.

    Raises:
        SyntaxError: If the source does not parse.
    """
    names = set(module_scope_names(source))
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return frozenset(names)


def _namespace_of_file(path: Path) -> frozenset[str] | None:
    """The namespace of a module on disk, or ``None`` if there is no reading it.

    Args:
        path: The module file.

    Returns:
        Its namespace, or ``None`` when the file is absent or does not parse.
        The two are collapsed ON PURPOSE - both mean this walk cannot say the
        name is bound, and a caller that treated an unparseable module as a
        resolution would forgive every target inside it.
    """
    try:
        return module_namespace(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


def dotted_target_resolves(target: str) -> bool:
    """Whether a dotted role target names a symbol in the module it points at.

    THE LONGEST MODULE PREFIX WINS AND THE SEARCH RUNS DOWNWARD, so
    ``tests.save.reach_guard._reach_primitives`` is read as the symbol
    ``_reach_primitives`` in ``tests/save/reach_guard.py`` rather than as the
    symbol ``save`` in a ``tests`` package. A search that ran upward would stop
    at the first importable prefix and ask the wrong module.

    Args:
        target: The role's target with any leading tilde already stripped.

    Returns:
        True when some prefix of the dotted name is a module file on disk whose
        namespace binds the segment that follows it.
    """
    parts = target.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        dotted = ".".join(parts[:cut])
        for candidate in (module_file(dotted), REPO_ROOT.joinpath(*parts[:cut], "__init__.py")):
            names = _namespace_of_file(candidate)
            if names is not None:
                return parts[cut] in names
    return False


def role_sites(source: str) -> list[tuple[int, str, str]]:
    """Every Sphinx role in a module's text, graded or not.

    Args:
        source: The module's full text.

    Returns:
        One ``(line number, role, target)`` triple per occurrence, with the
        leading tilde and a trailing call suffix stripped from the target.
    """
    found: list[tuple[int, str, str]] = []
    for number, line in enumerate(source.splitlines(), 1):
        for match in ROLE_RE.finditer(line):
            target = match["target"].removeprefix("~").removesuffix("()")
            found.append((number, match["role"], target))
    return found


def role_spellings(sources: Mapping[str, str]) -> frozenset[str]:
    """Every role spelling the corpus actually contains.

    Args:
        sources: Module path to full text.

    Returns:
        The set of role names found, which
        :data:`ROLE_DISPOSITIONS` is asserted equal to.
    """
    return frozenset(role for text in sources.values() for _, role, _ in role_sites(text))


def unresolved_roles(sources: Mapping[str, str]) -> list[tuple[str, int, str, str]]:
    """Every graded role whose target no namespace this walk can reach binds.

    Args:
        sources: Module path to full text, for the modules to grade.

    Returns:
        One ``(path, line, role, target)`` tuple per unresolved site, in path
        then line order.
    """
    graded = graded_roles()
    dead: list[tuple[str, int, str, str]] = []
    for path in sorted(sources):
        own = module_namespace(sources[path])
        for number, role, target in role_sites(sources[path]):
            if role not in graded:
                continue
            head, _, rest = target.partition(".")
            if head in own:
                continue
            if rest and dotted_target_resolves(target):
                continue
            dead.append((path, number, role, target))
    return dead


def graded_site_count(sources: Mapping[str, str]) -> int:
    """How many role sites :func:`unresolved_roles` actually judged.

    THE ANTI-VACUITY DENOMINATOR. A resolver that silently stopped reading -
    a regex that matched nothing, a population that enumerated nothing - would
    report zero unresolved roles, which is the same output as a clean corpus.
    The arms assert this count against a floor so the two cannot look alike.

    Args:
        sources: Module path to full text.

    Returns:
        The number of occurrences of a graded role.
    """
    graded = graded_roles()
    return sum(1 for text in sources.values() for _, role, _ in role_sites(text) if role in graded)


def graded_sources(tracked: Iterable[str]) -> dict[str, str]:
    """The tracked ``tests/`` modules, read.

    Args:
        tracked: Every tracked path, POSIX-separated.

    Returns:
        Module path to full text for every tracked Python file under
        :data:`TESTS_PREFIX`.
    """
    return {
        path: (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in tracked
        if path.startswith(TESTS_PREFIX) and path.endswith(".py")
    }
