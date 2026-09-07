"""CS-928 grading arm: docs/ARCHITECTURE.md may not attribute an absent capability.

`BOOTSTRAP.md` is the specification and is allowed to describe an intended build.
`docs/ARCHITECTURE.md` is the owner file for the module map, so a sentence there
that names a module is a claim about SHIPPED code. Copying a spec sentence into
this file and appending an `Implemented by:` line converts intent into a false
claim, and until this module existed nothing warned about it. That is the same
mechanism recorded at CS-922 in `docs/LEDGER.md` after seven `README.md` claims
were refuted.

Five checks, each parametrized so a single bad row is a single red test rather
than one pooled failure whose strongest member hides its weakest:

(a) every module path the document names resolves on disk - in prose, inside the
    package-topology fence, and on every `Implemented by:` line;
(b) every module or package an `Implemented by:` line names binds at least one
    public name, asserted PER MODULE, so a docstring-only `__init__.py` reddens;
(c) every capability clause in an attributed section has a live witness inside
    the attributed module - an importable public name, a populated dataclass
    field, or a machine-checked package property;
(d) the manifest TILES the attributed prose: the clauses, joined by single
    spaces, must reproduce the section body exactly. A sentence added tomorrow
    without a witness reddens on the day it is written, which is the half that
    stops this item from recurring;
(e) a section that declares itself NOT BUILT carries no `Implemented by:` line,
    and every package it names really does bind zero public names - so the
    document cannot overstate OR understate what exists.

Traps this arm is written to survive, all measured in this repo:

- `audit_exact` at `clockspeed/solve/exact.py` is a float-absence assertion, not
  a world audit, and it lives outside `clockspeed/audit/`. A keyword grep scores
  pillar 3 as partially present. Witnesses therefore name a module explicitly and
  are resolved by import, never by searching the repo for a word.
- `tests/test_scaffold.py` names `clockspeed/audit/` and `clockspeed/progress/`
  but asserts only directory existence and importability, so it passes green
  against an empty `__init__.py`. Check (b) counts AST definitions instead.
- A name in a docstring, a comment or a never-populated dataclass field is
  ABSENT. Public names are counted from the AST, and a `field` witness must also
  find the type constructed with that field as a keyword argument.

PRE-REPAIR MEASUREMENT. Run against `git show 67180af:docs/ARCHITECTURE.md`
written to a temp path and pointed at by CLOCKSPEED_ARCHITECTURE_DOC, this
module reported 20 failed, 127 passed, 0 skipped, exit 1. The twenty were:

  6  `advisor/trace.py`, `advisor/cards.py` and `advisor/ledger.py` named in
     prose and again in the module table, none of which exists on disk;
  3  the same three files listed inside the package-topology fence;
  6  attributions to `advisor/trace.py`, `advisor/cards.py`, `advisor/ledger.py`,
     `advisor/rules/`, `audit/` and `progress/`, of which the three that do exist
     bind zero public names - each is a module docstring and nothing else;
  5  all five pillar sections, whose prose matched no manifest entry.

Reproduce with:

    git show 67180af:docs/ARCHITECTURE.md > <tmp>/pre.md
    CLOCKSPEED_ARCHITECTURE_DOC=<tmp>/pre.md python -m pytest -q
        tests/test_architecture_attributions.py
"""

from __future__ import annotations

import ast
import importlib
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The tracked document is the default and the only one CI ever grades. The
# override exists so the pre-repair red run recorded above can be reproduced
# against an older revision without editing this file, which is how the
# "watch it fail for the right reason" step was performed.
DOC_ENV_VAR = "CLOCKSPEED_ARCHITECTURE_DOC"

IMPLEMENTED_BY = "**Implemented by:**"
NOT_BUILT = "NOT BUILT"
STATUS_PREFIX = "**Status:**"

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BACKTICKED = re.compile(r"`([^`\n]+)`")
_BARE_MODULE_PATH = re.compile(r"(?<![\w./-])([a-z_][a-z0-9_]*(?:/[a-z0-9_.-]+)+\.py)(?![\w])")
_FENCE = "```"


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------


def architecture_path() -> Path:
    override = os.environ.get(DOC_ENV_VAR)
    return Path(override) if override else REPO_ROOT / "docs" / "ARCHITECTURE.md"


def document() -> str:
    return architecture_path().read_text(encoding="ascii")


def sections() -> list[tuple[str, list[str]]]:
    """Split the document into (heading text, body lines) pairs."""
    found: list[tuple[str, list[str]]] = []
    heading = "(preamble)"
    body: list[str] = []
    for line in document().splitlines():
        matched = _HEADING.match(line)
        if matched:
            found.append((heading, body))
            heading, body = matched.group(2).strip(), []
        else:
            body.append(line)
    found.append((heading, body))
    return found


def attribution_line_index(body: list[str]) -> int | None:
    for index, line in enumerate(body):
        if line.startswith(IMPLEMENTED_BY):
            return index
    return None


def attribution_tokens(body: list[str]) -> list[str]:
    """Backticked paths on the `Implemented by:` line and its continuations."""
    start = attribution_line_index(body)
    if start is None:
        return []
    stop = start
    while stop < len(body) and body[stop].strip():
        stop += 1
    return [
        token
        for line in body[start:stop]
        for token in _BACKTICKED.findall(line)
        if looks_like_a_module_path(token)
    ]


def prose_block(body: list[str]) -> str:
    """The descriptive prose of an attributed section, whitespace-normalized."""
    start = attribution_line_index(body)
    return " ".join(" ".join(body[:start]).split())


def looks_like_a_module_path(token: str) -> bool:
    if ".." in token or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]*", token):
        return False
    return token.endswith((".py", "/"))


def resolve(token: str) -> Path | None:
    """Resolve a documented path against the repo root, then against the package."""
    relative = token.rstrip("/")
    for base in (REPO_ROOT, REPO_ROOT / "clockspeed"):
        candidate = base / relative
        if candidate.exists():
            return candidate
    return None


def documented_paths() -> list[str]:
    text = document()
    tokens = {token for token in _BACKTICKED.findall(text) if looks_like_a_module_path(token)}
    tokens.update(_BARE_MODULE_PATH.findall(text))
    return sorted(tokens)


def topology_entries() -> list[tuple[str, str]]:
    """(path, trailing comment) for every line of the package-topology tree.

    The tree is a fenced block, so its filenames carry no backticks and the
    prose scanners cannot see them. Three files that do not exist were listed
    there, which is why this parser is separate.
    """
    for heading, body in sections():
        if not heading.startswith("1. Package topology"):
            continue
        inside = False
        stack: list[tuple[int, str]] = []
        entries: list[tuple[str, str]] = []
        for line in body:
            if line.strip().startswith(_FENCE):
                if inside:
                    return entries
                inside = True
                continue
            if not inside or not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            fields = line.strip().split()
            token, comment = fields[0], " ".join(fields[1:])
            while stack and stack[-1][0] >= indent:
                stack.pop()
            entries.append(("".join(name for _, name in stack) + token, comment))
            if token.endswith("/"):
                stack.append((indent, token))
        return entries
    return []


def not_built_sections() -> list[tuple[str, list[str]]]:
    return [
        (heading, body)
        for heading, body in sections()
        if any(line.startswith(STATUS_PREFIX) and NOT_BUILT in line for line in body)
    ]


# ---------------------------------------------------------------------------
# Witnesses - what makes a capability PRESENT rather than described
# ---------------------------------------------------------------------------


def public_names(target: Path) -> set[str]:
    """Module-level names an AST parse proves are defined. Docstrings count zero."""
    files = (
        [path for path in sorted(target.rglob("*.py")) if "__pycache__" not in path.parts]
        if target.is_dir()
        else [target]
    )
    names: set[str] = set()
    for path in files:
        for node in ast.parse(path.read_text(encoding="ascii")).body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                names.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return {name for name in names if not name.startswith("_")}


def third_party_imports(relative_package: str) -> list[str]:
    standard = set(sys.stdlib_module_names)
    outside: list[str] = []
    for path in sorted((REPO_ROOT / relative_package).rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="ascii"))):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots = [node.module.split(".")[0]]
            outside.extend(
                f"{path.relative_to(REPO_ROOT).as_posix()} imports {root}"
                for root in roots
                if root not in standard and root != "clockspeed"
            )
    return outside


def _refute_attr(module_name: str, attribute: str) -> str:
    module = importlib.import_module(module_name)
    if not hasattr(module, attribute):
        return f"{module_name} defines no {attribute}"
    exported = getattr(module, "__all__", None)
    if exported is not None and attribute not in exported:
        return f"{module_name}.{attribute} exists but is not public (__all__)"
    return ""


def _refute_field(module_name: str, type_name: str, field: str) -> str:
    module = importlib.import_module(module_name)
    holder = getattr(module, type_name, None)
    if holder is None:
        return f"{module_name} defines no {type_name}"
    if field not in getattr(holder, "__dataclass_fields__", {}):
        return f"{module_name}.{type_name} has no field {field}"
    source = Path(module.__file__ or "").read_text(encoding="ascii")
    if f"{type_name}(" not in source or f"{field}=" not in source:
        return f"{module_name}.{type_name}.{field} is declared but never populated"
    return ""


def _refute_no_third_party(relative_package: str) -> str:
    outside = third_party_imports(relative_package)
    return "" if not outside else f"{relative_package} is not dependency-free: {outside}"


def refute(witness: tuple[str, ...]) -> str:
    """Return why the witness is ABSENT, or the empty string when it is present."""
    kind, arguments = witness[0], witness[1:]
    resolvers: dict[str, Callable[..., str]] = {
        "attr": _refute_attr,
        "field": _refute_field,
        "no_third_party": _refute_no_third_party,
    }
    resolver = resolvers.get(kind)
    if resolver is None:
        return f"unknown witness kind {kind}"
    return resolver(*arguments)


# ---------------------------------------------------------------------------
# The capability manifest
#
# One entry per attributed section. The clause texts, joined by single spaces,
# must reproduce that section's prose EXACTLY - that is check (d), and it is
# what makes an unwitnessed new sentence impossible to add quietly.
# ---------------------------------------------------------------------------

RATIO = "clockspeed.solve.ratio"
EXACT = "clockspeed.solve.exact"
OPTIMIZE = "clockspeed.solve.optimize"
BACKENDS = "clockspeed.solve.backends"

MANIFEST: dict[str, tuple[tuple[str, tuple[tuple[str, ...], ...]], ...]] = {
    "Pillar 1 - Target-rate ratio solve": (
        (
            "Given a requested rate of an item, emit exact building counts,",
            (("field", RATIO, "PlanStep", "machines"),),
        ),
        (
            "byproduct handling",
            (
                ("field", RATIO, "ProductionPlan", "byproducts"),
                ("field", RATIO, "ProductionPlan", "byproduct_policy"),
                ("attr", RATIO, "BYPRODUCT_POLICIES"),
            ),
        ),
        (
            "and raw input totals.",
            (("field", RATIO, "ProductionPlan", "raw_inputs"),),
        ),
        (
            'It solves both directions - "I want this much of X"',
            (("attr", RATIO, "solve_for_targets"), ("attr", RATIO, "RatioRequest")),
        ),
        (
            'and "I have this much of a raw input, what rate of the named item does it buy".',
            (("attr", RATIO, "solve_for_supply"), ("attr", RATIO, "SupplyRequest")),
        ),
        (
            "Arithmetic is exact rational end to end because floating-point drift in a ratio"
            " calculator is a correctness bug and not a rounding nuisance.",
            (
                ("attr", EXACT, "audit_exact"),
                ("attr", EXACT, "to_exact"),
                ("attr", EXACT, "InexactValueError"),
            ),
        ),
        (
            "Recipe loops and byproducts that feed back into their own chain are the hard case"
            " and are handled explicitly rather than assumed away.",
            (("attr", EXACT, "solve_linear"), ("attr", RATIO, "InfeasibleChain")),
        ),
    ),
    "Pillar 2 - Alt-recipe selection under constraints": (
        (
            "Given an objective and the set of unlocked recipes, choose the recipe set that"
            " optimizes it.",
            (
                ("attr", OPTIMIZE, "optimize_plan"),
                ("attr", OPTIMIZE, "OptimizeRequest"),
                ("attr", OPTIMIZE, "OptimizeResult"),
            ),
        ),
        (
            "Objectives are individually selectable and combinable with weights:",
            (
                ("attr", OPTIMIZE, "weighted_objective"),
                ("attr", OPTIMIZE, "score_plan"),
                ("attr", OPTIMIZE, "Objective"),
            ),
        ),
        ("minimize raw resource consumption,", (("attr", OPTIMIZE, "OBJECTIVE_RAW"),)),
        ("minimize power draw,", (("attr", OPTIMIZE, "OBJECTIVE_POWER"),)),
        ("minimize building count.", (("attr", OPTIMIZE, "OBJECTIVE_BUILDINGS"),)),
        ("The implementation starts dependency-free", (("no_third_party", "clockspeed/solve"),)),
        (
            "- exact ratio solve plus a weighted-greedy search -",
            (
                ("attr", RATIO, "solve_for_targets"),
                ("attr", f"{BACKENDS}.greedy", "GreedyBackend"),
            ),
        ),
        (
            "behind a pluggable optimizer interface,",
            (
                ("attr", OPTIMIZE, "OptimizerBackend"),
                ("attr", OPTIMIZE, "select_backend"),
                ("attr", BACKENDS, "BACKEND_FACTORIES"),
            ),
        ),
        (
            "and constrains by what is unlocked rather than by what exists in the data.",
            (("attr", OPTIMIZE, "usable_candidates"), ("attr", OPTIMIZE, "EXCLUDED_LOCKED")),
        ),
        (
            "An external linear or integer programming library is a later and gated decision"
            " that must slot behind the existing interface without changing a caller.",
            (("attr", OPTIMIZE, "select_backend"), ("attr", BACKENDS, "available_backends")),
        ),
    ),
}


# ---------------------------------------------------------------------------
# Collection-time populations
# ---------------------------------------------------------------------------

DOCUMENTED_PATHS = documented_paths()
TOPOLOGY = [(path, comment) for path, comment in topology_entries() if "GITIGNORED" not in comment]
ATTRIBUTED = [(heading, body) for heading, body in sections() if attribution_line_index(body)]
ATTRIBUTED_TOKENS = sorted({token for _, body in ATTRIBUTED for token in attribution_tokens(body)})
WITNESS_ROWS = [
    (heading, clause, witness)
    for heading, clauses in MANIFEST.items()
    for clause, witnesses in clauses
    for witness in witnesses
]
# Only the Status line itself, never the section prose: a NOT BUILT section is
# free to mention a package that IS built (as a future consumer, say), and
# sweeping the whole body would grade those too and redden for the wrong reason.
NOT_BUILT_PACKAGES = sorted(
    {
        token
        for _, body in not_built_sections()
        for line in body
        if line.startswith(STATUS_PREFIX) and NOT_BUILT in line
        for token in _BACKTICKED.findall(line)
        if looks_like_a_module_path(token) and (resolve(token) or REPO_ROOT).is_dir()
    }
)


# ---------------------------------------------------------------------------
# (0) A gate that grades nothing reports PASS. Prove the populations are real.
# ---------------------------------------------------------------------------


def test_the_extractors_found_a_population_to_grade() -> None:
    counts = (len(DOCUMENTED_PATHS), len(TOPOLOGY), len(ATTRIBUTED), len(WITNESS_ROWS))
    smallest = min(counts)
    assert smallest > 0, f"an extractor returned nothing, so its checks graded nothing: {counts}"


# ---------------------------------------------------------------------------
# (a) Every path the document names exists.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("token", DOCUMENTED_PATHS)
def test_a_documented_module_path_exists_on_disk(token: str) -> None:
    assert resolve(token) is not None, f"docs/ARCHITECTURE.md names {token}, which does not exist"


@pytest.mark.parametrize("path", [entry[0] for entry in TOPOLOGY], ids=[e[0] for e in TOPOLOGY])
def test_a_path_in_the_package_topology_tree_exists_on_disk(path: str) -> None:
    assert (REPO_ROOT / path).exists(), f"the package topology tree lists {path}, which is absent"


# ---------------------------------------------------------------------------
# (b) Every attributed module binds a public name. Asserted per module: a
#     threshold pooled over the set is met by its strongest member.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("token", ATTRIBUTED_TOKENS)
def test_an_attributed_module_binds_at_least_one_public_name(token: str) -> None:
    target = resolve(token)
    assert target is not None, f"an Implemented by: line names {token}, which does not exist"
    bound = len(public_names(target))
    assert bound > 0, (
        f"docs/ARCHITECTURE.md attributes a capability to {token}, which defines no public"
        " name at all - a module docstring is not an implementation"
    )


# ---------------------------------------------------------------------------
# (c) Every retained capability clause has a live witness inside its module.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("heading", "clause", "witness"),
    WITNESS_ROWS,
    ids=[f"{row[0][:9]}::{row[2][1]}.{row[2][-1]}" for row in WITNESS_ROWS],
)
def test_a_capability_clause_has_a_live_witness(
    heading: str, clause: str, witness: tuple[str, ...]
) -> None:
    reason = refute(witness)
    assert not reason, f"{heading}: the clause {clause!r} is unwitnessed - {reason}"


# ---------------------------------------------------------------------------
# (d) The anti-drift half. The manifest must tile the attributed prose, so a
#     sentence added without a witness reddens on the day it is written.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("heading", "body"), ATTRIBUTED, ids=[heading for heading, _ in ATTRIBUTED]
)
def test_the_manifest_tiles_the_attributed_prose(heading: str, body: list[str]) -> None:
    assert heading in MANIFEST, (
        f"section {heading!r} carries an {IMPLEMENTED_BY} line but has no manifest entry, so"
        " every capability it claims is ungraded"
    )
    tiled = " ".join(clause for clause, _ in MANIFEST[heading])
    assert tiled == prose_block(body), (
        f"section {heading!r} does not match its manifest. Every clause of an attributed"
        " section needs a witness; add the new text to MANIFEST with one, or remove it."
    )


def test_the_manifest_names_no_section_the_document_lost() -> None:
    attributed = {heading for heading, _ in ATTRIBUTED}
    stale = sorted(set(MANIFEST) - attributed)
    assert not stale, f"MANIFEST grades sections that no longer carry an attribution: {stale}"


# ---------------------------------------------------------------------------
# (e) A NOT BUILT section may not attribute, and its packages must be empty.
# ---------------------------------------------------------------------------


# An empty parametrize SKIPS, and a suite that skips a check still reports PASS.
# Both populations below are therefore padded with a sentinel row that asserts
# the emptiness is genuine, so these two checks always execute.
NOT_BUILT_SECTIONS = not_built_sections()
_NO_SECTIONS: list[tuple[str, list[str]]] = [("", [])]
_NO_PACKAGES = [""]


@pytest.mark.parametrize(
    ("heading", "body"),
    NOT_BUILT_SECTIONS or _NO_SECTIONS,
    ids=[heading for heading, _ in NOT_BUILT_SECTIONS] or ["(no NOT BUILT section)"],
)
def test_a_not_built_section_attributes_nothing(heading: str, body: list[str]) -> None:
    if not heading:
        assert NOT_BUILT not in document(), "a NOT BUILT section exists but was not collected"
        return
    assert attribution_line_index(body) is None, (
        f"section {heading!r} declares itself {NOT_BUILT} and then names implementing modules"
    )


@pytest.mark.parametrize(
    "token", NOT_BUILT_PACKAGES or _NO_PACKAGES, ids=NOT_BUILT_PACKAGES or ["(no such package)"]
)
def test_a_package_the_document_calls_not_built_really_is(token: str) -> None:
    if not token:
        assert not NOT_BUILT_SECTIONS, "a NOT BUILT section names no package, so nothing is graded"
        return
    target = resolve(token)
    assert target is not None
    bound = sorted(public_names(target))
    assert not bound, (
        f"docs/ARCHITECTURE.md still calls {token} {NOT_BUILT}, but it now binds {bound}."
        " The document understates what shipped; update the section."
    )
