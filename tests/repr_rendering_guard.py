"""CS-852 - the repr channel, derived from the shipped FIELD ANNOTATIONS.

WHAT THIS GRADES AND WHY IT IS NOT A CS-850 WIDENING. ``tests/
assertion_rendering_guard.py`` derives its population from classes that SHIP a
redacting ``__repr__`` and asks which fields that method discloses. A class
shipping NO ``__repr__`` cannot enter that population at all - the sweep reads
``repr_method(node)`` and skips on None - so the one shape this module exists
for is invisible to it BY CONSTRUCTION. The question here is the other one:
which classes get a GENERATED field-rendering repr while holding a field that
can carry save bytes, a save-derived name or a home path.

THE DISCRIMINATOR IS "GENERATED", NOT "ABSENT", AND THAT WAS MEASURED RATHER
THAN REASONED. A plain class with no ``__repr__`` inherits ``object.__repr__``,
which renders ``<module.Class object at 0x...>`` and DISCLOSES NO FIELD; both
``_Cursor`` types in this project hold a raw save buffer in ``_data`` and leak
nothing on this channel. A ``@dataclass`` with no ``__repr__`` gets one
SYNTHESISED FROM ITS FIELDS and renders every one of them. Grading on "ships no
``__repr__``" would have reported both cursors as leaks and buried the real
findings in false positives.

THE POPULATION IS DERIVED BY TWO MECHANICAL RULES, NEITHER OF THEM A LIST:

  R1  every generated-repr class under any :data:`R1_LAYERS` prefix - the
      layer ``docs/ARCHITECTURE.md`` names as the one that reads a save, and
      the audit and surface layers its content is published through - holding
      at least one field whose annotation is not provably non-disclosing.
  R2  every generated-repr class anywhere under :data:`SHIPPED_ROOT` holding a
      field annotated with a :data:`CARRIER_TYPES` word.

R2 exists because a carrier can appear above the save layer the day a world
value is cached in ``advisor/`` or ``surface/``. THAT DAY HAS ARRIVED, and the
earlier wording here is left visible rather than deleted because of how it went
false. It read "MEASURED at the time of writing: R2 adds nothing R1 does not
already hold", which was true of the tree it was measured against. CS-601's
surface layer then landed the first candidates R1 cannot reach - a resolved
``ServerConfig`` holding certificate, key and asset ``Path`` fields, and the
providers holding a save directory, an install resolver and an asset directory
- and NOTHING WENT RED when the sentence stopped being true, because no arm
grades a docstring. A restated measurement is a claim with a shelf life, and
this one is the worked example.

A HAND-WRITTEN ``__repr__`` IS NOT AUTOMATICALLY A PASS. A class carrying
``repr=False`` plus a method that renders the carrier anyway is graded
``disclosed`` and is a finding, on the same footing as the generated one.
Without that arm the remedy for every finding would be to write a ``__repr__``
that changes nothing.

EXEMPTIONS CARRY THE PROVENANCE JUDGEMENT, BECAUSE AN ANNOTATION CANNOT. Nothing
in ``reason: str`` says whether the string was authored in this repository or
read out of a save, and the annotation is all a static derivation can see.
:data:`EXEMPT` is where that judgement is written down with its reason, one
entry per class, and every entry was measured at its construction sites rather
than assumed. The record is checked in BOTH directions: an entry naming a class
that is no longer a candidate is REPORTED rather than failed, because failing
there is the anti-monotone shape that refuted three items in one session -
repairing a leak would turn the proof red.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Final

from tests.assertion_rendering_guard import (
    REPO_ROOT,
    _cannot_disclose,
    annotation_names,
    annotation_tail,
    declared_fields,
    disclosed_fields,
    module_functions,
    repr_method,
    tracked_python_files,
)

#: The layer ``docs/ARCHITECTURE.md`` names as the one that reads a save. Stated
#: as a path prefix rather than a module list so a new module in the layer is
#: graded on arrival instead of on somebody remembering to add it.
SAVE_LAYER: Final = "clockspeed/save/"

#: The layer that assembles the published models from the save layer's model
#: (CS-1024). Every value the dashboard serves about a world is one of these.
AUDIT_LAYER: Final = "clockspeed/audit/"

#: The layer that serialises and serves them (CS-1024).
#:
#: THE RULE, stated so it can be refuted: "every model on the published path"
#: is every model that CARRIES WORLD CONTENT on its way out, whichever layer
#: holds it. An earlier draft stopped at the audit layer on the argument that
#: ``surface/`` never computes, so anything it held had already been graded one
#: layer down. An adversary refuted that on this rule's own words: the response
#: envelope holds the SERIALISED payload built from those models, and a
#: generated repr of the envelope rendered a planted string in full. Grading a
#: value where it is made does not grade the containers it is later put in.
SURFACE_LAYER: Final = "clockspeed/surface/"

#: Every prefix R1 grades: the save layer that reads a save, and the two layers
#: its content travels through on the way to a consumer. A tuple so
#: ``str.startswith`` reads it directly, and so a narrowing is one visible edit
#: that the membership pin in ``tests/test_repr_rendering.py`` reddens on.
R1_LAYERS: Final = (SAVE_LAYER, AUDIT_LAYER, SURFACE_LAYER)

#: Everything shipped. Tests, tools and scripts are not graded here: this item is
#: about what the PRODUCT renders, and a test that reprs a value is CS-850's and
#: CS-851's subject on their own channels.
SHIPPED_ROOT: Final = "clockspeed/"

#: Annotations that can carry raw save content directly.
BYTES_TYPES: Final = frozenset({"bytearray", "bytes", "memoryview"})

#: Annotations that can carry a home directory or an account directory. A
#: ``Path`` renders in full - ``WindowsPath('C:/Users/<account>/...')`` - so a
#: rendered one defeats non-negotiable 3 without any save being parsed.
PATH_TYPES: Final = frozenset({"Path", "PosixPath", "PurePath", "WindowsPath"})

#: The union R2 fires on.
CARRIER_TYPES: Final = BYTES_TYPES | PATH_TYPES

#: Decorator words that synthesise a field-rendering ``__repr__``.
GENERATING_DECORATORS: Final = frozenset({"dataclass"})

#: Base words that do the same.
GENERATING_BASES: Final = frozenset({"NamedTuple"})

#: A class is graded ``generated`` when its repr is synthesised, ``disclosed``
#: when its own method renders a graded field, ``withheld`` when its own method
#: does not, and ``inherited`` when nothing renders a field at all.
KIND_GENERATED: Final = "generated"
KIND_DISCLOSED: Final = "disclosed"
KIND_WITHHELD: Final = "withheld"
KIND_INHERITED: Final = "inherited"

#: Method names that render an object through a channel this module does not
#: grade. Lifted out of the scan body so it can be asserted non-empty: an
#: adversary replaced the literal set with ``set()`` and the census went silent
#: while still reporting "nothing here", which is the one thing it exists to
#: rule out.
ALTERNATE_RENDERING_METHODS: Final = frozenset({"__format__", "__str__"})

#: Base words whose rendering comes from ``BaseException`` rather than from
#: ``object``. A class reaching any of these renders ``args`` through both
#: ``__repr__`` and ``__str__``, which is NOT the channel this module grades.
EXCEPTION_ROOTS: Final = frozenset(
    {
        "ArithmeticError",
        "AttributeError",
        "BaseException",
        "Exception",
        "IndexError",
        "KeyError",
        "LookupError",
        "OSError",
        "RuntimeError",
        "TypeError",
        "ValueError",
    }
)

#: Kinds that render a graded field into a repr. These are the findings.
LEAKING_KINDS: Final = frozenset({KIND_GENERATED, KIND_DISCLOSED})

#: Classes whose graded fields cannot carry save-derived content, each with the
#: reason and where it was measured. EVERY ENTRY WAS CHECKED AT ITS CONSTRUCTION
#: SITES - none is a rubber stamp, and a class whose sites change is expected to
#: leave this record rather than to have its reason quietly widened.
EXEMPT: Final[Mapping[str, str]] = {
    "clockspeed/save/chunks.py::ChunkFrame": (
        "framing is one of the module's own variant words, chosen by "
        "_select_variant from the marker word alone. No save string reaches it."
    ),
    "clockspeed/save/chunks.py::ChunkWarning": (
        "MEASURED at the one construction site, decompress_body around line "
        "923: code comes from _cross_check and detail from the _WARNING_DETAIL "
        "constant table. No buffer content reaches either. THE FIRST DRAFT OF "
        "THIS ENTRY CITED A PRIVATE HELPER THAT HAS NEVER EXISTED IN THIS "
        "REPOSITORY, transcribed from the aggregator in the sibling objects "
        "module. The conclusion was right and the evidence was invented, which "
        "is the rubber stamp this record claims not to contain."
    ),
    "clockspeed/save/header.py::HeaderWarning": (
        "MEASURED at both construction sites: subject is f'{header_version}/"
        "{save_version}' and str(len(world_token)). Both are derived SCALARS - "
        "a version pair and a length - never the token or a header string."
    ),
    "clockspeed/save/objects.py::BodyLayout": (
        "level_tail is one of the LEVEL_TAIL_* constants, named in the "
        "attribute's own docstring as NAMED levels only. No save string."
    ),
    "clockspeed/save/objects.py::ObjectWarning": (
        "code and detail are module constants describing what was noticed, not what was read."
    ),
    "clockspeed/save/objects.py::UnknownClass": (
        "ACCEPTED DISCLOSURE, NOT PROVEN SAFE, and the distinction is the "
        "point. BOOTSTRAP.md section 9 REQUIRES naming unmodelled content, so "
        "rendering type_path is the type's purpose rather than an accident. "
        "But type_path is cursor.string(...) read straight out of the save "
        "body under MAX_STRING_BYTES and NOTHING validates it is a class path; "
        "a CS-852 adversary planted a marker and it rendered verbatim. The "
        "same module 240 lines away discards a level name because 'holding one "
        "would put world content into the returned model and into its repr'. "
        "That tension is real and is recorded here rather than argued away."
    ),
    "clockspeed/save/usmap.py::UsmapWarning": (
        "code and subject are module constants and positional labels such as "
        "'name-<position>'. detail is a constant at 10 of 12 log.add sites and "
        "an f-string over install-file counts at the other two - corrected "
        "after an adversary measured it; the earlier wording said all three "
        "were constants. The usmap is an INSTALL file, not a save."
    ),
    "clockspeed/save/usmap.py::_NameTable": (
        "names is the usmap name table, read from the game install rather than "
        "from a save. Publisher-owned game data, not personal data."
    ),
    "clockspeed/save/workdir.py::ListingProblem": (
        "The type's own docstring is the reason and it is already explicit: an "
        "OSError reaches its path through str(), filename, strerror and args, "
        "so _listing_problem lifts ONLY errno as a named field and detail is "
        "the fixed line for the code."
    ),
    "clockspeed/save/world.py::WorldWarning": (
        "source is a module constant. code, detail AND subject are all "
        "FORWARDED rather than authored here - MEASURED in _carried, "
        "which copies them from the originating layer's own warning type, and "
        "passes subject from exactly two of the four arms, the header one and "
        "the usmap one. This entry therefore INHERITS the reasons recorded "
        "above for HeaderWarning and UsmapWarning and stops being true if "
        "either changes. An earlier wording called code and detail constants, "
        "which an adversary measured false."
    ),
}

#: Per-FIELD clearances, keyed like :data:`EXEMPT`, each naming the exact field
#: set its reason covers (CS-1024).
#:
#: WHY FIELDS AND NOT A CLASS. An :data:`EXEMPT` entry clears a class whole, so
#: a field ADDED to an exempted class after its measurement renders unmeasured -
#: which is precisely the defect CS-1024 names for ``Placement``. A clearance
#: here covers only the fields it lists: a class whose graded fields exceed its
#: cleared set is a finding again, so the next ``str`` field on any of these
#: models reddens the census until somebody measures it. Every entry was traced
#: to its construction sites; "ACCEPTED" marks a field that renders save-read
#: text NOT proven safe, recorded on the ``UnknownClass`` terms above rather
#: than argued away.
CLEARED_FIELDS: Final[Mapping[str, tuple[frozenset[str], str]]] = {
    "clockspeed/audit/balance.py::DrawContribution": (
        frozenset({"class_name"}),
        "MEASURED in _classify, reached only from draw_of over the placement "
        "model's built_counts keys - the closed built allowlist in placement.py. "
        "No name outside that closed set can reach the field.",
    ),
    "clockspeed/audit/balance.py::DrawGap": (
        frozenset({"class_name", "kind", "reason"}),
        "class_name on the DrawContribution terms, from built_counts. kind is "
        "GAP_NO_REGISTRY_ENTRY, GAP_DRAW_INEXACT or a shape word from "
        "declared_draw; reason is _GAP_REASON or the fixed reason declared_draw "
        "returns from the solve layer's constant table. Nothing is read from a save.",
    ),
    "clockspeed/audit/footprint.py::Footprint": (
        frozenset({"class_name", "category", "x", "y", "z", "extent"}),
        "class_name is admitted only as a key of CATEGORY_OF_CLASS and category "
        "is its value, both closed tables. x, y and z are decimal_string over a "
        "finite float, digits only. extent is a FootprintExtent, graded here "
        "on its own entry.",
    ),
    "clockspeed/audit/footprint.py::FootprintExtent": (
        frozenset({"x", "y", "z"}),
        "Built only by _extent_of from three finite scale components, each "
        "through decimal_string - a numeric rendering that names nothing.",
    ),
    "clockspeed/audit/inventory.py::ItemTotal": (
        frozenset({"item_key"}),
        "ACCEPTED DISCLOSURE, NOT PROVEN SAFE. _item_key_of reduces a save-read "
        "str or reference path with class_name_of_path and validates it against "
        "no closed set, so an arbitrary string under one of the "
        "ITEM_KEY_PROPERTY_NAMES renders here. It is the value the inventory "
        "route serves anyway, so the repr is no wider than the published answer.",
    ),
    "clockspeed/audit/machines.py::MachineState": (
        frozenset({"class_name", "recipe_class_name"}),
        "recipe_class_name passes _permitted_recipe_path first. class_name is "
        "ACCEPTED DISCLOSURE, NOT PROVEN SAFE: machines_of reduces the record's "
        "type_path with class_name_of_path and checks it against no closed set, "
        "the UnknownClass shape - recorded rather than cleared on a false proof.",
    ),
    "clockspeed/audit/network.py::NodeUse": (
        frozenset({"class_name"}),
        "Copied from each ResourceNode in model.nodes, whose class_name the save "
        "layer admits only from its own closed node class set before it builds "
        "the node at all.",
    ),
    "clockspeed/audit/placement.py::AxisBounds": (
        frozenset({"min_value", "max_value"}),
        "Built only by _bounds from the finite coordinate triples _placement_of "
        "kept, each end through decimal_string. Digits only.",
    ),
    "clockspeed/audit/placement.py::Placement": (
        frozenset({"class_name", "x", "y", "z", "rotation", "scale"}),
        "MEASURED in _placement_of and its two callers. class_name is a "
        "ResourceNode class name from the save layer's closed node set, or a "
        "built name admitted only by BUILT_CLASS_ALLOWLIST. x, y and z are "
        "decimal_string over finite floats; rotation and scale are _rotation_of "
        "and _scale_of, decimal strings or None. No instance name, no path.",
    ),
    "clockspeed/surface/api/contract.py::Route": (
        frozenset({"method", "template"}),
        "MEASURED at every construction site in the api package: method is a "
        "module constant HTTP verb and template a module constant route string "
        "matching ENDPOINT_PATTERN, or a pair from a module-level constant table. "
        "The handler, which binds whatever the server supplied, is withheld.",
    ),
    "clockspeed/audit/placement.py::WorldBounds": (
        frozenset({"x", "y", "z"}),
        "Three AxisBounds and nothing else, each graded here on its own entry, "
        "so this repr renders exactly what those three render.",
    ),
}


@dataclass(frozen=True)
class ReprCandidate:
    """One shipped class the derivation put in the population.

    Attributes:
        module: Repo-relative path.
        class_name: The class.
        lineno: Where it is declared.
        kind: One of :data:`KIND_GENERATED`, :data:`KIND_DISCLOSED`,
            :data:`KIND_WITHHELD` or :data:`KIND_INHERITED`.
        graded: The field names that put it in the population.
        carriers: The subset of ``graded`` annotated with a carrier word.
        rule: ``R1``, ``R2`` or ``R1+R2`` - which derivation rule caught it.
        tails: Each graded field to its annotation, for the report.
    """

    module: str
    class_name: str
    lineno: int
    kind: str
    graded: tuple[str, ...]
    carriers: tuple[str, ...]
    rule: str
    tails: tuple[str, ...]

    @property
    def key(self) -> str:
        """The :data:`EXEMPT` key for this class.

        Returns:
            ``<module>::<ClassName>``.
        """
        return f"{self.module}::{self.class_name}"


def _generating(node: ast.ClassDef) -> bool:
    """Whether this class would receive a synthesised field-rendering repr.

    ``repr=False`` on the decorator suppresses the synthesis, which is the
    project's existing spelling for "this type writes its own".

    Args:
        node: The class.

    Returns:
        True when a repr would be generated from the fields.
    """
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        word = getattr(target, "id", None) or getattr(target, "attr", None)
        if word not in GENERATING_DECORATORS:
            continue
        if isinstance(decorator, ast.Call):
            for keyword in decorator.keywords:
                suppressed = (
                    keyword.arg == "repr"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is False
                )
                if suppressed:
                    return False
        return True
    for base in node.bases:
        if (getattr(base, "id", None) or getattr(base, "attr", None)) in GENERATING_BASES:
            return True
    return False


def _repr_suppressed_fields(node: ast.ClassDef) -> frozenset[str]:
    """Fields declared ``field(repr=False)``, which a GENERATED repr skips.

    Read only for a class whose repr is generated: a hand-written ``__repr__``
    ignores the keyword, so honouring it there would excuse a method that
    renders the field anyway. Both ``field(...)`` and ``dataclasses.field(...)``
    are read; only a literal ``False`` suppresses, so anything the AST cannot
    settle stays graded - the direction that keeps grading.

    Args:
        node: The class.

    Returns:
        The suppressed field names.
    """
    suppressed: set[str] = set()
    for item in node.body:
        if not (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and isinstance(item.value, ast.Call)
        ):
            continue
        func = item.value.func
        if (getattr(func, "id", None) or getattr(func, "attr", None)) != "field":
            continue
        for keyword in item.value.keywords:
            if (
                keyword.arg == "repr"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
            ):
                suppressed.add(item.target.id)
    return frozenset(suppressed)


@cache
def opaque_class_names() -> frozenset[str]:
    """Every class name in the tree that ships a hand-written ``__repr__``.

    Read tree-wide rather than per module because a container annotated with a
    type declared elsewhere is safe exactly when THAT type redacts itself.

    Returns:
        The names.

    Raises:
        RuntimeError: When the file list cannot be read. An empty sweep and a
            clean one must not look alike.
    """
    found: set[str] = set()
    for relative in tracked_python_files():
        tree = _parsed(relative)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and repr_method(node) is not None:
                found.add(node.name)
    return frozenset(found)


@cache
def _parsed(relative: str) -> ast.Module | None:
    """Parse one repo-relative module.

    Args:
        relative: The path.

    Returns:
        The tree, or None when it could not be read or parsed.
    """
    try:
        source = (REPO_ROOT / Path(relative)).read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


@cache
def known_functions() -> Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Every module-level function in the tree, by name.

    TREE-WIDE RATHER THAN PER MODULE, AND THE FIRST DRAFT OF THIS MODULE GOT IT
    WRONG. A project mask is a free function, and ``masked_token`` is declared
    in ``clockspeed/save/header.py`` and IMPORTED by ``clockspeed/save/
    world.py``. Resolving only same-module names left ``masked_token(self.
    token)`` unresolvable, so :func:`disclosed_fields` reported ``token`` as
    DISCLOSED and seven correctly-redacting classes came back as findings.
    ``redacting_classes`` carries the same warning for the same reason.

    Returns:
        The mapping.
    """
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for relative in tracked_python_files():
        tree = _parsed(relative)
        if tree is not None:
            found.update(module_functions(tree))
    return found


def candidates_in(module: str, tree: ast.Module, opaque: frozenset[str]) -> list[ReprCandidate]:
    """Every class in one module that the two rules put in the population.

    Args:
        module: Repo-relative path.
        tree: The parsed module.
        opaque: Class names shipping a hand-written ``__repr__``.

    Returns:
        One record per class in the population, whatever its grade.
    """
    functions = {**known_functions(), **module_functions(tree)}
    in_r1_layer = module.startswith(R1_LAYERS)
    out: list[ReprCandidate] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        fields = declared_fields(node)
        hidden = (
            _repr_suppressed_fields(node)
            if repr_method(node) is None and _generating(node)
            else frozenset()
        )
        disclosing: list[str] = []
        carriers: list[str] = []
        tails: list[str] = []
        for name, annotation in fields.items():
            if name in hidden:
                continue
            words = annotation_names(annotation)
            is_carrier = bool(words & CARRIER_TYPES)
            if is_carrier:
                carriers.append(name)
            if is_carrier or not _cannot_disclose(words, opaque):
                disclosing.append(name)
                tails.append(f"{name}: {annotation_tail(annotation) or '?'}")
        by_r1 = in_r1_layer and bool(disclosing)
        by_r2 = bool(carriers)
        if not (by_r1 or by_r2):
            continue
        graded = disclosing if by_r1 else carriers
        own = repr_method(node)
        if own is None:
            kind = KIND_GENERATED if _generating(node) else KIND_INHERITED
        else:
            # A HAND-WRITTEN repr MADE A PER-FIELD DECISION, AND ONLY CARRIERS
            # ARE RE-GRADED HERE. Whether a save-layer `str` may be shown is a
            # provenance question CS-850 already owns; asking it again in this
            # module reported six correctly-redacting classes, among them
            # `ResourceNode`, whose repr shows the game `class_name` on purpose
            # and withholds `instance_name` exactly as its docstring says. A
            # carrier is different in kind: a rendered `bytes` or `Path` is a
            # leak on its face, whatever the author intended, so `repr=False`
            # plus a method that renders one anyway stays a finding here.
            shown = disclosed_fields(own, functions)
            kind = KIND_DISCLOSED if set(carriers) & set(shown) else KIND_WITHHELD
        rule = "R1+R2" if by_r1 and by_r2 else ("R1" if by_r1 else "R2")
        out.append(
            ReprCandidate(
                module=module,
                class_name=node.name,
                lineno=node.lineno,
                kind=kind,
                graded=tuple(graded),
                carriers=tuple(carriers),
                rule=rule,
                tails=tuple(tails),
            )
        )
    return out


@cache
def scan_tree() -> tuple[tuple[ReprCandidate, ...], tuple[ReprCandidate, ...]]:
    """Derive the population and the findings across the shipped tree.

    Returns:
        Every candidate, and the subset that renders a graded field without a
        stated exemption.
    """
    opaque = opaque_class_names()
    population: list[ReprCandidate] = []
    for relative in tracked_python_files():
        if not relative.startswith(SHIPPED_ROOT):
            continue
        tree = _parsed(relative)
        if tree is None:
            continue
        population.extend(candidates_in(relative, tree, opaque))
    findings = tuple(candidate for candidate in population if is_finding(candidate))
    return tuple(population), findings


def uncleared_fields(
    candidate: ReprCandidate,
    cleared: Mapping[str, tuple[frozenset[str], str]] | None = None,
) -> tuple[str, ...]:
    """The graded fields of one candidate that no clearance covers.

    Args:
        candidate: The record.
        cleared: The per-field record to grade against. Defaults to
            :data:`CLEARED_FIELDS`; a parameter so the mechanism is gradable.

    Returns:
        The field names, in declaration order.
    """
    record = CLEARED_FIELDS if cleared is None else cleared
    covered = record[candidate.key][0] if candidate.key in record else frozenset()
    return tuple(name for name in candidate.graded if name not in covered)


def is_finding(
    candidate: ReprCandidate,
    cleared: Mapping[str, tuple[frozenset[str], str]] | None = None,
) -> bool:
    """Whether one candidate renders a graded field that nothing clears.

    A class-wide :data:`EXEMPT` entry clears the whole class; otherwise EVERY
    graded field must be covered by the class's :data:`CLEARED_FIELDS` entry,
    so a field added after the measurement makes the class a finding again.

    Args:
        candidate: The record.
        cleared: As for :func:`uncleared_fields`.

    Returns:
        True for a finding.
    """
    if candidate.kind not in LEAKING_KINDS or candidate.key in EXEMPT:
        return False
    return bool(uncleared_fields(candidate, cleared))


def alternate_rendering_methods() -> tuple[str, ...]:
    """Shipped classes defining ``__str__`` or ``__format__``.

    NOT A CHANNEL THIS MODULE GRADES, AND THAT IS THE POINT OF COUNTING IT.
    ``f"{obj}"`` calls ``__str__``, which falls back to ``__repr__`` only while
    no ``__str__`` exists. A class defining one would render through a path
    every rule here is blind to. MEASURED at the time of writing: the shipped
    tree defines neither, anywhere. The arm that reads this fails the day that
    stops being true, so the scope is re-decided deliberately rather than
    silently outgrown.

    Returns:
        ``<module>::<ClassName>::<method>`` for each, sorted.
    """
    found: list[str] = []
    for relative in tracked_python_files():
        if not relative.startswith(SHIPPED_ROOT):
            continue
        tree = _parsed(relative)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if item.name in ALTERNATE_RENDERING_METHODS:
                    found.append(f"{relative}::{node.name}::{item.name}")
    return tuple(sorted(found))


def swept_modules() -> tuple[str, ...]:
    """Every module the sweep actually walks.

    EXPOSED SO THE REACH IS GRADED RATHER THAN ASSUMED. When this was written
    every candidate lived under :data:`SAVE_LAYER`, so an adversary narrowed
    :data:`SHIPPED_ROOT` back to the save layer and nothing went red - the rule
    that exists to catch a save value cached above the save layer could be
    switched off silently. THAT IS NO LONGER THE TREE: CS-601's surface layer
    put candidates above the save layer, so the same narrowing now drops them
    out of the population and the membership pin reddens on the departure. This
    function stays anyway, because what it grades is the REACH and not today's
    census - the day the surface candidates are all repaired away, the pin goes
    quiet again and this is what still measures whether R2 can see anything.

    Returns:
        Repo-relative module paths, sorted.
    """
    return tuple(sorted(r for r in tracked_python_files() if r.startswith(SHIPPED_ROOT)))


def exception_rendering_classes() -> tuple[str, ...]:
    """Save-layer classes that render through ``BaseException``'s own channel.

    A CHANNEL THIS MODULE DOES NOT GRADE, COUNTED SO THE GAP CANNOT GROW
    SILENTLY. The premise behind :data:`KIND_INHERITED` - that a class with no
    ``__repr__`` inherits ``object.__repr__`` and discloses no field - is TRUE
    for a plain class and FALSE for every exception: ``BaseException.__repr__``
    renders ``args`` in full, and ``BaseException.__str__`` renders it too, so
    an f-string over the exception discloses whatever was interpolated into the
    message. An adversary added a save-derived ``instance_name`` to a shipped
    error, interpolated it into the message, and every arm here stayed green.

    Deciding whether a given error leaks needs the message-building CODE PATH,
    not the field annotations this module reads, so it is out of scope for the
    derivation and is recorded instead. Their real protection today is the
    hand-placed ``locate.redact`` calls at the raise sites and the
    ``_checked_field`` validation some of them apply.

    Returns:
        ``<module>::<ClassName>`` for each, sorted.
    """
    declared: dict[str, tuple[str, tuple[str, ...]]] = {}
    for relative in tracked_python_files():
        if not relative.startswith(SHIPPED_ROOT):
            continue
        tree = _parsed(relative)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = tuple(
                word
                for base in node.bases
                if (word := getattr(base, "id", None) or getattr(base, "attr", None))
            )
            declared[node.name] = (relative, bases)

    def reaches(word: str, seen: frozenset[str]) -> bool:
        if word in EXCEPTION_ROOTS:
            return True
        if word not in declared or word in seen:
            return False
        return any(reaches(b, seen | {word}) for b in declared[word][1])

    return tuple(
        sorted(
            f"{relative}::{name}"
            for name, (relative, bases) in declared.items()
            if relative.startswith(SAVE_LAYER) and any(reaches(b, frozenset()) for b in bases)
        )
    )


def stale_exemptions(record: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Exemption keys that no longer name a class needing one.

    Reported rather than asserted. A repair removes a class from the leaking
    kinds, and failing on that would make the proof require the defect.

    TAKES A RECORD SO THE MECHANISM CAN BE GRADED. Reading only the module
    global left the arm that consumes this with nothing to assert: an adversary
    replaced the body with ``return ()`` and every test stayed green, because
    the live record happens to be clean and a clean result is what a broken
    reporter also returns.

    Args:
        record: The exemption record to grade. Defaults to :data:`EXEMPT`.

    Returns:
        The keys, sorted.
    """
    population, _ = scan_tree()
    needing = {c.key for c in population if c.kind in LEAKING_KINDS}
    return tuple(sorted(set(EXEMPT if record is None else record) - needing))


def stale_clearances(
    record: Mapping[str, tuple[frozenset[str], str]] | None = None,
) -> tuple[str, ...]:
    """Cleared fields that no longer name a field needing clearance.

    Reported rather than asserted, on the :func:`stale_exemptions` terms: a
    repaired or removed field leaves its clearance behind, and failing on that
    would make the proof require the defect.

    Args:
        record: The clearance record to grade. Defaults to :data:`CLEARED_FIELDS`.

    Returns:
        ``<key>`` for a key naming no rendering candidate and ``<key>::<field>``
        for a cleared field the candidate no longer grades, sorted.
    """
    population, _ = scan_tree()
    graded = {c.key: set(c.graded) for c in population if c.kind in LEAKING_KINDS}
    stale: list[str] = []
    for key, (names, _reason) in (CLEARED_FIELDS if record is None else record).items():
        if key not in graded:
            stale.append(key)
            continue
        stale.extend(f"{key}::{name}" for name in names if name not in graded[key])
    return tuple(sorted(stale))


def describe(candidates: tuple[ReprCandidate, ...]) -> str:
    """Render candidates as a report.

    Args:
        candidates: The records.

    Returns:
        One block per record. Field NAMES and annotations only - never a value,
        because this text reaches a failure report.
    """
    if not candidates:
        return "none"
    lines: list[str] = []
    for candidate in sorted(candidates, key=lambda c: (c.module, c.class_name)):
        lines.append(
            f"{candidate.module}:{candidate.lineno} {candidate.class_name} "
            f"[{candidate.kind}, {candidate.rule}]"
        )
        lines.extend(f"      {tail}" for tail in candidate.tails)
        if candidate.key in CLEARED_FIELDS:
            lines.append(f"      uncleared: {', '.join(uncleared_fields(candidate)) or '-'}")
    return "\n".join(lines)
