"""Which redactor the package's render sites reach, derived rather than listed.

CS-454's acceptance criterion says personal data is redacted in EVERY RENDERED
MESSAGE. "Every" is a population claim, and until this module nobody had made
that population a derived fact - it was a sentence in a docstring, which is the
exact defect ADR 0008 exists to foreclose and the exact shape CS-458 and CS-459
were opened to remove. So nothing here writes down a list of call sites. The
population is read out of the source tree on every run, and the two properties
below are asserted against whatever that scan finds.

WHAT THIS MODULE ESTABLISHES, precisely and no wider:

    Of the messages this package renders THROUGH the project's single
    redactor, every one reaches ``clockspeed.data.locate.redact`` itself
    rather than a same-named local, and none of them hands it a bare path
    segment.

WHAT IT DOES NOT ESTABLISH, stated because an overclaim here would be the ADR
0008 defect sitting inside the control that grades ADR 0008 compliance:

  - It does NOT show that no render site bypasses ``redact()`` entirely. A
    message built with no redactor at all is invisible to both tests below,
    because both start from a redact call and there is nothing to start from.
    That question belongs to ``tests/test_exception_rendering.py`` and is
    MEASURED OPEN - see CS-441, CS-450 and CS-451 in ``ROADMAP.md``.
  - It does NOT cover a chained exception cause. ``clockspeed/save/world.py``
    line 971 raises ``WorldLoadError(...) from exc``, and Python's own
    traceback machinery renders the cause - filename included - without
    consulting any call site this module can see.
  - It does NOT cover ``tests/conftest.py``. That file carries a SEPARATE
    redactor, ``redact_personal_data``, which imports nothing from
    ``clockspeed`` and never calls ``locate.redact``. Its rules are its own
    and it has no account-directory rule at all.
  - It is scoped to ``clockspeed/``. ``tools/`` and ``scripts/`` also call the
    redactor and are not graded here.

BOTH PROPERTIES ARE FENCES, NOT REPRODUCTIONS. Both are green at HEAD and are
meant to stay green - neither one reproduces a live defect, and writing either
up as a bug caught would be a false sentence about what the suite measured.
Property (b) in particular was measured at zero before it was written. What it
buys is a bound on a hole that cannot be closed any other way: a bare directory
name is information-theoretically unredactable, because a redactor handed the
string ``common`` has no way to tell a folder from an account id. Redaction
works on paths because position and structure carry the signal, and stripping
the path off before the call throws that signal away.

Nothing here needs a game install, a save library or any CLOCKSPEED_*
variable: every input is source text read off the repository.
"""

from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# The population, derived from paths rather than written down
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "clockspeed"

#: The one redactor the whole package is supposed to funnel through.
REDACTOR_MODULE = "clockspeed.data.locate"

#: The redactor's own file, DERIVED from the dotted name above so the two can
#: never drift apart and so this module holds no second copy of the path.
REDACTOR_SOURCE = (REPO_ROOT / Path(*REDACTOR_MODULE.split("."))).with_suffix(".py")

#: The attribute every call site must end up at.
REDACT = "redact"

#: Fully qualified target a bare ``redact`` name has to have been imported from.
_QUALIFIED_REDACT = f"{REDACTOR_MODULE}.{REDACT}"

#: Recorded when a module binds ``redact`` itself - a def, a class or an
#: assignment. Legitimate in exactly one file and a shadow everywhere else.
_DEFINED_LOCALLY = "<bound in this module>"

#: Attributes that reduce a path to one segment.
#:
#: THE STATED LIMIT, because the earlier wording here claimed these were "the
#: two spellings in the standard library that throw away every directory above
#: the last one" and that is FALSE. ``os.path.basename(p)``,
#: ``os.path.split(p)[1]`` and ``PurePath(p).parts[-1]`` all reduce a path to
#: its last segment too, and ``os.path.basename`` is the canonical spelling.
#: This detector matches an ATTRIBUTE NAME, so it sees none of them: they are
#: calls and subscripts, not attribute access. Measured at the time of writing,
#: no such spelling reaches a redact() call site in the package - so this is a
#: coverage limit rather than a live hole, and the first one added walks
#: straight through. Widening it to calls is separate work; recording the limit
#: is not.
_BARE_SEGMENT_ATTRS = frozenset({"name", "stem"})


def _package_sources() -> list[tuple[str, str]]:
    """Read every Python file in the package.

    Returns:
        Pairs of (repo-relative posix label, source text), sorted by label.
    """
    return sorted(
        (path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        for path in PACKAGE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _redact_calls(tree: ast.AST) -> list[ast.Call]:
    """Find every call that lands on the name ``redact``, however it was reached.

    An AST is the right instrument and a grep is not. ``clockspeed/`` mentions
    ``redact()`` dozens of times in prose - module docstrings explaining the
    seam, comments recording what it learned - and a text scan cannot tell
    those from the four modules that actually call it.

    Args:
        tree: A parsed module.

    Returns:
        The call nodes, in traversal order.
    """
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        by_name = isinstance(func, ast.Name) and func.id == REDACT
        by_attribute = isinstance(func, ast.Attribute) and func.attr == REDACT
        if by_name or by_attribute:
            found.append(node)
    return found


def _import_bindings(tree: ast.AST) -> tuple[str | None, dict[str, str]]:
    """Read what a module's imports bind, ignoring anything it defines itself.

    Args:
        tree: A parsed module.

    Returns:
        A pair. First, the fully qualified target a bare ``redact`` was
        imported from, or None. Second, local name to dotted module for every
        module alias the file establishes.
    """
    bare: str | None = None
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # A relative import has no resolvable dotted name here, and the
            # project bans them outright (ruff TID, ban-relative-imports), so
            # a module=None node degrades to the bare alias rather than being
            # guessed at - which leaves it unresolved and therefore reported.
            for alias in node.names:
                local = alias.asname or alias.name
                target = f"{node.module}.{alias.name}" if node.module else alias.name
                if local == REDACT:
                    bare = target
                else:
                    aliases[local] = target
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                    if alias.asname == REDACT:
                        bare = alias.name
                else:
                    # "import a.b.c" binds only "a"; a later "a.b.c.redact" is
                    # an attribute chain this module reports as unresolved
                    # rather than silently approving.
                    root = alias.name.split(".")[0]
                    aliases[root] = root
    return bare, aliases


def _binds_redact_itself(tree: ast.AST) -> bool:
    """Report whether a module binds the name ``redact`` with its own statement.

    Walked at every depth rather than at module level only. A ``def redact``
    tucked inside a function body shadows the import for every call after it
    and is precisely the substitution this module has to be able to see.

    Args:
        tree: A parsed module.

    Returns:
        True when a def, a class or an assignment binds the name.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if node.name == REDACT:
                return True
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == REDACT for target in node.targets
        ):
            return True
    return False


def _bindings(tree: ast.AST) -> tuple[str | None, dict[str, str]]:
    """Work out what a module has bound the name ``redact``, and which modules it aliases.

    A local binding OVERRIDES an import unconditionally, whatever order the
    two appear in. That is deliberately the pessimistic reading: a file that
    both imports the redactor and defines the name somewhere is treated as
    shadowed, because deciding which binding a given call actually reaches
    would mean modelling scope, and getting that wrong silently is the one
    outcome a privacy fence cannot afford.

    Args:
        tree: A parsed module.

    Returns:
        A pair. First, what the bare name ``redact`` is bound to - a fully
        qualified import target, ``_DEFINED_LOCALLY``, or None when the module
        never binds it. Second, the module alias map.
    """
    bare, aliases = _import_bindings(tree)
    if _binds_redact_itself(tree):
        bare = _DEFINED_LOCALLY
    return bare, aliases


def _unresolved_call_sites(label: str, source: str, *, is_redactor: bool) -> list[str]:
    """Report every redact call in one module that does not reach the single redactor.

    Args:
        label: How to name the module in a failure message.
        source: Module source text.
        is_redactor: True for the redactor's own file, which is allowed - and
            required - to bind ``redact`` by defining it.

    Returns:
        One string per offending call site, empty when every call resolves.
    """
    tree = ast.parse(source)
    bare, aliases = _bindings(tree)
    offenders: list[str] = []

    for call in _redact_calls(tree):
        where = f"{label}:{call.lineno}"
        func = call.func
        if isinstance(func, ast.Name):
            if is_redactor and bare == _DEFINED_LOCALLY:
                continue
            if bare == _QUALIFIED_REDACT:
                continue
            found = bare if bare is not None else "nothing"
            offenders.append(f"{where} calls a bare redact() bound to {found}")
        elif isinstance(func, ast.Attribute):
            value = func.value
            if not isinstance(value, ast.Name):
                offenders.append(f"{where} calls redact() on an expression with no simple name")
                continue
            resolved = aliases.get(value.id)
            if resolved != REDACTOR_MODULE:
                found = resolved if resolved is not None else "nothing"
                offenders.append(f"{where} calls {value.id}.redact(), and {value.id} is {found}")
    return offenders


def _bare_segment_call_sites(label: str, source: str) -> list[str]:
    """Report every redact call in one module handed a bare path segment.

    Each argument is walked in full rather than matched at its top level. The
    leak is the same whether the segment is passed alone, interpolated into an
    f-string, or wrapped in ``str()``, so all three have to be visible.

    Args:
        label: How to name the module in a failure message.
        source: Module source text.

    Returns:
        One string per offending call site, empty when none passes a segment.
    """
    offenders: list[str] = []
    for call in _redact_calls(ast.parse(source)):
        arguments: list[ast.expr] = [*call.args, *(kw.value for kw in call.keywords)]
        for argument in arguments:
            offenders.extend(
                f"{label}:{call.lineno} passes .{node.attr}"
                for node in ast.walk(argument)
                if isinstance(node, ast.Attribute) and node.attr in _BARE_SEGMENT_ATTRS
            )
    return offenders


def test_the_redactor_source_is_where_this_module_thinks_it_is() -> None:
    """The derived path to the redactor resolves, or every scan below is vacuous.

    ``REDACTOR_SOURCE`` is built from the dotted module name. If the redactor
    were ever moved, both properties below would still pass - by grading a
    population that no longer contained the file that matters - so the
    existence of the target is asserted first, exactly as the phase 2 gate
    asserts its forced-absent path really is absent.
    """
    assert REDACTOR_SOURCE.is_file(), (
        f"{REDACTOR_MODULE} does not resolve to a file at {REDACTOR_SOURCE.name}; the "
        "redactor moved and this module is grading the wrong population"
    )


def test_every_redact_call_site_in_the_package_resolves_to_the_single_redactor() -> None:
    """Every redact call under clockspeed/ reaches locate.redact and not a look-alike.

    The failure this fences off is a same-named local: a module-level
    ``def redact`` added as a "temporary" wrapper, a ``redact = something``
    rebinding, or an import of the name from a second helper. Any of those
    leaves every call site in the file reading exactly as it does today while
    routing around the redactor that carries the account-directory rules.

    The count is asserted non-zero as well, because a scan that found nothing
    would satisfy the offender check perfectly. That is the CONVENTIONS.md
    section 15.1 failure - a green claim about the pattern rather than about
    the codebase - and it is what a typo in the glob would produce.
    """
    sources = _package_sources()
    assert sources, f"no Python sources found under {PACKAGE_ROOT.name}/"

    total = 0
    offenders: list[str] = []
    for label, source in sources:
        is_redactor = (REPO_ROOT / label) == REDACTOR_SOURCE
        total += len(_redact_calls(ast.parse(source)))
        offenders.extend(_unresolved_call_sites(label, source, is_redactor=is_redactor))

    assert total > 0, (
        "the scan found no redact() call anywhere in the package, so it is grading an "
        "empty population and would stay green through any substitution"
    )
    assert not offenders, (
        f"redact() call sites that do not resolve to {REDACTOR_MODULE}: {offenders}"
    )


def test_no_redact_call_site_renders_a_bare_segment() -> None:
    """No redact call under clockspeed/ is handed a lone path segment.

    A bare segment is unredactable in principle rather than in practice, which
    is why this is a fence and not a bug report. Handed ``common``, the
    redactor cannot tell an ordinary directory from an account id: the two are
    the same string, and the only thing that distinguished them - the save root
    sitting above it - was discarded by the caller before the call was made.
    Every rule in the redactor that works on position stops working at that
    point, and no improvement to the redactor can recover it.

    Pass the path. Let the redactor decide what to strip.
    """
    offenders: list[str] = []
    for label, source in _package_sources():
        offenders.extend(_bare_segment_call_sites(label, source))
    assert not offenders, (
        "redact() is handed a bare path segment, which it cannot redact because the "
        f"position that identifies an account directory is already gone: {offenders}"
    )


# ---------------------------------------------------------------------------
# Detector self-tests
# ---------------------------------------------------------------------------
#
# Run against synthetic source text, following the pattern at
# tests/data/test_phase2_gate.py::test_the_import_time_call_finder_actually
# _finds. Both scans above report an empty list at HEAD, and an empty list is
# the same output a broken scanner produces. These are what separate the two.


def test_the_call_site_resolver_flags_a_shadow_and_clears_the_real_bindings() -> None:
    """The resolver rejects a local shadow and accepts all three legitimate styles.

    The three accepting cases are not decoration. The package really does bind
    the redactor three different ways - a bare import of the name, a module
    alias reached by attribute, and the redactor's own definition of it - so a
    resolver that understood only one of them would fail the package while
    looking strict rather than broken.
    """
    shadowed = "def redact(text):\n    return str(text)\n\ndef render(p):\n    return redact(p)\n"
    offenders = _unresolved_call_sites("planted.py", shadowed, is_redactor=False)
    assert len(offenders) == 1, (
        f"the resolver missed a module-local def redact shadowing the import: {offenders}"
    )
    assert "planted.py:5" in offenders[0], (
        f"the resolver flagged the wrong line for the shadowed call: {offenders}"
    )

    nested = (
        "from clockspeed.data.locate import redact\n"
        "\n"
        "def render(p):\n"
        "    def redact(text):\n"
        "        return str(text)\n"
        "    return redact(p)\n"
    )
    assert _unresolved_call_sites("planted.py", nested, is_redactor=False), (
        "the resolver missed a shadow defined inside a function body, which overrides "
        "the module-level import for every call after it"
    )

    imported_from_elsewhere = (
        "from clockspeed.surface.helpers import redact\n\ndef render(p):\n    return redact(p)\n"
    )
    assert _unresolved_call_sites("planted.py", imported_from_elsewhere, is_redactor=False), (
        "the resolver accepted redact imported from a module that is not the redactor"
    )

    by_name = "from clockspeed.data.locate import redact\n\ndef render(p):\n    return redact(p)\n"
    assert not _unresolved_call_sites("planted.py", by_name, is_redactor=False), (
        "the resolver rejected a direct import of the real redactor"
    )

    by_alias = "from clockspeed.data import locate\n\ndef render(p):\n    return locate.redact(p)\n"
    assert not _unresolved_call_sites("planted.py", by_alias, is_redactor=False), (
        "the resolver rejected the module-alias style that clockspeed/save/workdir.py uses"
    )

    wrong_alias = (
        "from clockspeed.save import locate\n\ndef render(p):\n    return locate.redact(p)\n"
    )
    assert _unresolved_call_sites("planted.py", wrong_alias, is_redactor=False), (
        "the resolver approved an attribute call on a name aliased to the wrong module, "
        "so it is matching the spelling rather than the binding"
    )

    defines_it = "def redact(text):\n    return str(text)\n\ndef _note(s):\n    return redact(s)\n"
    assert not _unresolved_call_sites("planted.py", defines_it, is_redactor=True), (
        "the resolver rejected the redactor's own file, which must define redact"
    )


def test_the_bare_segment_detector_flags_a_segment_and_leaves_a_path_alone() -> None:
    """The segment detector catches all three spellings and does not flag a whole path.

    The negatives carry the weight. Passing a path, a resolved path or an
    exception is what every call site in the package does today, and a detector
    that flagged those would be switched off within a week.
    """
    positives = (
        ("bare", "redact(path.name)"),
        ("interpolated", "redact(f'reading {path.stem}')"),
        ("wrapped", "redact(str(target.name))"),
    )
    for description, sample in positives:
        assert _bare_segment_call_sites("planted.py", sample), (
            f"the detector missed a {description} bare segment: {sample}"
        )

    negatives = (
        "redact(path)",
        "redact(path.resolve())",
        "redact(exc)",
        "redact(f'cannot read {resolved}: errno {exc.errno}')",
    )
    for sample in negatives:
        assert not _bare_segment_call_sites("planted.py", sample), (
            f"the detector flagged a legitimate whole-path rendering: {sample}"
        )
