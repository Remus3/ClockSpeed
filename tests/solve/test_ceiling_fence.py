"""CS-303 - the ADR 0006 name-fence on ``Building.unsharded_clock_base``, mechanically.

ADR 0006 decided how the one shipped ceiling operand reaches the model, and it was
explicit about what it did NOT close: "nothing mechanical stops a future caller
reading ``Building.unsharded_clock_base`` directly and clamping without going
through ``clamp_to_unsharded_base``. This ADR claims the name and the docstring as
that fence and claims no more." The adjudication raised the mechanism as a roadmap
candidate and explicitly not as a condition of its acceptance. This module is that
mechanism.

WHY A NAME IS NOT A FENCE. The trap ADR 0005 named is that the un-sharded base reads
as an achievable maximum. Every shipped entry reports the same un-overclocked value,
so a caller that clamps to it caps every solve at 100 percent and looks correct on
every building nobody has overclocked - the failure is invisible in exactly the
worlds where testing is easiest. A reader who has not read both ADRs will not be
stopped by a good name, because a good name is only a hint. The read itself has to
be refused.

THE OWNER IS A PATH, NOT A PACKAGE. ``clockspeed/solve/power.py`` is the one module
allowed to touch the field, because it is the module that owns
``clamp_to_unsharded_base`` and ``ceiling_for`` - the two functions whose entire job
is to say what was clamped to. Widening the owner to ``clockspeed/solve/`` would let
any sibling in that package clamp silently, which is the defect.

THE TEST CORPUS IS EXEMPTED BY NAME AND NEVER BY A GLOB, which is the shape the item
asks for and is worth stating as a rule rather than as an accident. A blanket
``tests/**`` forgiveness would forgive a test written tomorrow that nobody chose to
forgive, and forgiveness granted to a population rather than to a file is the
pooled-guard shape this project has already had to repair elsewhere. Every entry in
:data:`EXEMPT` is an exact repo-relative path with a reason, and three arms below
keep the table honest: no entry may carry a glob metacharacter, every entry must name
a file that exists, and every entry must still hold a site. A forgiveness that
forgives nothing is dead prose, and dead prose is how a fence quietly stops fencing.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Final

from tests.assertion_rendering_guard import REPO_ROOT, tracked_python_files

#: The field ADR 0006 fences. Held as a string because this module must never
#: perform the read it forbids - writing the attribute here would make the guard
#: its own first offender.
FIELD: Final = "unsharded_clock_base"

#: The argument count a ``getattr`` call must reach before its second argument
#: exists to be read. Named rather than spelled inline so the check reads as the
#: arity question it is.
_GETATTR_NAME_ARITY: Final = 2


@dataclass(frozen=True)
class Site:
    """One direct read of the fenced field.

    Attributes:
        path: The repo-relative path of the module holding the read.
        lineno: The 1-based line the read starts on.
        source: The unparsed expression, so a failure names the read itself
            rather than only its coordinates.
    """

    path: str
    lineno: int
    source: str


def ceiling_fence_sites(source: str, path: str) -> tuple[Site, ...]:
    """Every direct read of the fenced field in one module's source.

    Two spellings count, because they are the same read:

    * ``<anything>.unsharded_clock_base`` - the attribute access itself.
    * ``getattr(<anything>, "unsharded_clock_base")`` - the hand-back, which
      resolves to the identical value while spelling the name in a string. A
      guard that reads only the first is evaded by typing the second.

    A bare string carrying the name is NOT a read. Tests that assert on the
    NAME - which ADR 0006 requires, since the name is the fence it claims - must
    stay green here or the mechanism would forbid the thing it protects.

    Args:
        source: The module's text.
        path: The repo-relative path, used only to label a finding.

    Returns:
        The sites, in source order.

    Raises:
        SyntaxError: The source does not parse. Swallowing that would make an
            unparseable module indistinguishable from a clean one.
    """
    tree = ast.parse(source)
    found: list[Site] = []
    for node in ast.walk(tree):
        # Narrowed to the two node types that can BE a read before anything is
        # asked of the node, so the loop never reaches for a position on a node
        # that has none.
        if not isinstance(node, ast.Attribute | ast.Call):
            continue
        attribute = isinstance(node, ast.Attribute) and node.attr == FIELD
        if attribute or _is_getattr_handback(node):
            found.append(Site(path=path, lineno=node.lineno, source=ast.unparse(node)))
    return tuple(sorted(found, key=lambda site: (site.lineno, site.source)))


def _is_getattr_handback(node: ast.AST) -> bool:
    """Whether a node is ``getattr(<anything>, "<the fenced field>")``.

    Args:
        node: Any AST node.

    Returns:
        True for the hand-back spelling of the fenced read.
    """
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "getattr":
        return False
    if len(node.args) < _GETATTR_NAME_ARITY:
        return False
    name = node.args[1]
    return isinstance(name, ast.Constant) and name.value == FIELD


def test_a_direct_attribute_read_outside_the_owner_is_reported() -> None:
    source = "def clamp(building, clock):\n    return min(clock, building.unsharded_clock_base)\n"
    sites = ceiling_fence_sites(source, "clockspeed/solve/elsewhere.py")
    assert [site.lineno for site in sites] == [2]
    assert sites[0].path == "clockspeed/solve/elsewhere.py"


def test_the_getattr_handback_spelling_is_reported() -> None:
    source = 'def clamp(building):\n    return getattr(building, "unsharded_clock_base")\n'
    sites = ceiling_fence_sites(source, "clockspeed/solve/elsewhere.py")
    assert [site.lineno for site in sites] == [2]


def test_a_string_naming_the_field_is_not_a_read() -> None:
    source = 'NAMES = ["unsharded_clock_base"]\nassert "unsharded_clock_base" in NAMES\n'
    assert ceiling_fence_sites(source, "tests/data/test_registry.py") == ()


#: The one module allowed to read the field, as a repo-relative path. A PATH and
#: not a package: widening this to the ``clockspeed/solve/`` directory would let
#: any sibling clamp silently, which is the defect ADR 0006 left open.
OWNER: Final = "clockspeed/solve/power.py"

#: Path -> why that exact file is forgiven. Exact repo-relative paths only. See
#: the module docstring for why this is never a glob. Each entry is a test that
#: has to read the field to grade the field; none of them clamps with it, which
#: is the behaviour the fence exists to refuse.
EXEMPT: Final[dict[str, str]] = {
    "tests/data/test_registry.py": (
        "grades the registry read itself - that the base is taken per building "
        "from the shipped entry, that an absent one is never defaulted to 1, and "
        "that the value is not a folded constant. Reading the field IS the subject."
    ),
    "tests/solve/test_power.py": (
        "grades clamp_to_unsharded_base and ceiling_for against the base they "
        "clamp to. An oracle that cannot observe the value it names would pass "
        "for that reason alone, so this one reads it."
    ),
    "tests/solve/test_synthetic.py": (
        "test_every_building_carries_the_unsharded_clock_base walks the synthetic "
        "registry and asserts the field is populated per building. Named as an "
        "exemption by the CS-303 item note before this guard existed."
    ),
}

#: The characters that would turn an exemption key into a population instead of a
#: file. Checked rather than assumed, because the whole value of this table is
#: that somebody chose each line of it.
_GLOB_CHARS: Final = "*?[]"


def repo_sites() -> tuple[Site, ...]:
    """Every direct read of the fenced field in the whole tracked tree.

    Returns:
        The sites, ordered by path then line.
    """
    found: list[Site] = []
    for relative in tracked_python_files():
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        found.extend(ceiling_fence_sites(source, relative))
    return tuple(sorted(found, key=lambda site: (site.path, site.lineno)))


def test_no_module_outside_the_owner_reads_the_fenced_field_directly() -> None:
    offenders = [
        f"{site.path}:{site.lineno} {site.source}"
        for site in repo_sites()
        if site.path != OWNER and site.path not in EXEMPT
    ]
    assert not offenders, (
        f"a direct read of {FIELD} outside {OWNER}, with no exemption recorded by name "
        f"in EXEMPT: {offenders}"
    )


def test_the_owner_still_reads_the_field_so_the_fence_is_not_vacuous() -> None:
    owner = [site for site in repo_sites() if site.path == OWNER]
    assert owner, (
        f"{OWNER} holds no read of {FIELD}. Either the owner moved and this guard now "
        f"fences an empty file, or the clamp stopped reading the base it clamps to. "
        f"Both make every arm above pass for the wrong reason."
    )


def test_no_exemption_is_spelled_as_a_population() -> None:
    globbed = sorted(path for path in EXEMPT if any(char in path for char in _GLOB_CHARS))
    assert not globbed, (
        f"an exemption key carries a glob metacharacter, which forgives a population "
        f"rather than a file somebody chose: {globbed}"
    )


def test_every_exemption_names_a_file_git_actually_tracks() -> None:
    tracked = set(tracked_python_files())
    missing = sorted(path for path in EXEMPT if path not in tracked)
    assert not missing, (
        f"an exemption names a path that is not a tracked Python file, so it forgives "
        f"nothing and hides a rename: {missing}"
    )


def test_every_exemption_still_holds_a_read_it_forgives() -> None:
    reading = {site.path for site in repo_sites()}
    dead = sorted(path for path in EXEMPT if path not in reading)
    assert not dead, (
        f"an exemption forgives a file that no longer reads {FIELD}. A forgiveness "
        f"that forgives nothing is dead prose, and the next reader inherits a table "
        f"they cannot tell from a live one: {dead}"
    )


# WHAT THIS ARM PROVES AND WHAT IT DOES NOT, said here rather than implied by its
# name. It is a NON-BLANKNESS check: it proves the reason field was filled in, and
# it proves nothing at all about whether the sentence is true or even relevant. That
# is the weakness class CS-937 owns, and this arm is deliberately inside it rather
# than pretending to be outside it - a stronger claim would need a criterion nobody
# has written down, and a guard that grades against an unwritten criterion is the
# other failure this lane is fenced against.
def test_every_exemption_records_a_reason() -> None:
    silent = sorted(path for path, reason in EXEMPT.items() if not reason.strip())
    assert not silent, (
        f"an exemption carries no reason, so nothing records who chose it or why: {silent}"
    )
