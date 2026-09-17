"""CS-1096 - the world-token bound enumeration is GRADED, not read.

`_world_tokens_from_headers` in tools/precommit_gate.py carries a docstring
that spells how many truncating bounds reach the exit status, and lists them.
That sentence was wrong twice in a row - "All four" over five bounds, then
"All FIVE" over six - and two sibling comments in the function body carried a
stale number after the docstring was repaired. Nothing graded any of it.

This arm grades it, and the two sides never read what they grade:

- The CODE reader walks the syntax tree only. From `_world_tokens_from_headers`
  it follows calls into module-level functions of the same source, binds the
  arguments it can resolve, honours an `if <parameter>:` guard whose value is
  bound, walks nested functions and lambdas, and collects every distinct
  BLOCKING PRODUCTION: a call of `_report_world_token_uncovered` whose
  `blocking` resolves True, any `Diagnostic(...)` construction, and any use of
  the blocking reason text. A production is keyed by its CALL PATH from the
  target, so one helper reached from two call sites is two productions.
  Module-wide, it REFUSES any reference to `_report_world_token_uncovered` or
  to `Diagnostic` that is not a call, so an alias of THOSE TWO cannot hide a
  production. It never looks at a docstring or a comment.

KNOWN LIMITS, stated rather than implied (adjudicated after the second
refutation):

- F2: an alias, a `sys.modules` lookup or any indirect reach to an
  INTERMEDIATE helper (for example `_report_root_cap`) is not followed and not
  refused. Only direct calls by bare name are walked. Accepted as obfuscation
  rather than a plausible maintainer shape.
- F3, filed as CS-1105: the arm counts REPORTING SITES, not truncation
  conditions. A cap that only ORs into `scan_capped` beside an existing
  report, or any cap inside clockspeed/save/header.py's scanner, adds no
  reporting site and is not counted.
- CS-1106 retired F5. The NON-BLOCKING population is now read from the code
  too: every exception handler reached from the target that neither re-raises
  nor makes a blocking production, and every `suppress(...)` call, keyed by
  call path. Any spelled total over that population, in the docstring or the
  body comments, is graded against it, and the allowlist entry that used to
  clear "the one deliberate non-blocking degradation" is gone. Limits: a
  swallow shaped as an early return or a `continue` with no handler (an
  absent save root, an unresolvable declared directory) is NOT counted, and a
  handler that raises through a helper it calls is counted as swallowing.
- The PROSE reader tokenizes the function's source range and keeps STRING and
  COMMENT tokens only. It never looks at a call, a name or a keyword.

What the prose side grades:

1. Every spelled TOTAL in the docstring ("All N", "The N bounds", "the other
   N") equals the code count, and at least one is present - an arm that finds
   no total grades nothing. A bare "N of them" is NOT a total: "every one of
   them is self-healing" is distributive, and it sits in this very docstring.
2. The list that "All N of them" introduces has as many members as the code
   count, with a member of the shape "the N above" expanded to N.
3. The function-body comments carry NO count at all (adjudicated Q4): a total
   in a comment is a second copy of the number to drift, which is the exact
   defect this row was filed for. This is an ALLOWLIST - any cardinal, digits
   or a number word, is red unless a justified form in _COMMENT_ALLOWLIST
   masks it - because a denylist of total phrasings let "the remaining four"
   through. An ARRIVAL ordinal ("the Nth bound") is not a cardinal; it is
   history that stays true when a later bound lands, so it is only held to
   not exceed the code count.

UNGRADED by design (adjudicated Q5): "The first five used to report through
the skip channel alone". It is a historical fact about which bounds predated
CS-1087 and stays true however many bounds are added later, so grading it
against the live count would bake history into the arm and false-red on the
next bound. The total patterns above do not match it.

The mutation arms feed MODIFIED SOURCE TEXT to the same readers. The frozen
file on disk is never mutated, and every mutant asserts it actually applied
before its verdict is read.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "precommit_gate.py"

TARGET = "_world_tokens_from_headers"
SINK = "_report_world_token_uncovered"
DIAGNOSTIC = "Diagnostic"
REASON = "WORLD_SCAN_UNCOVERED_REASON"
SUPPRESS = "suppress"

_CARDINALS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}
_ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
}
_NUM = r"(\d+|" + "|".join(_CARDINALS) + r")"
_NUM_WORD_OR_DIGITS = r"\b" + _NUM + r"\b"

# A spelled TOTAL. Each pattern yields the total it asserts; "the other N"
# asserts N plus the one being described.
_TOTAL_PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"\ball\s+" + _NUM + r"\b", re.IGNORECASE), 0),
    (re.compile(r"\b" + _NUM + r"\s+(?:\w+\s+)?bounds\b", re.IGNORECASE), 0),
    (re.compile(r"\bother\s+" + _NUM + r"\b", re.IGNORECASE), 1),
)
_ORDINAL_BOUND = re.compile(r"\b(" + "|".join(_ORDINALS) + r")\s+(?:\w+\s+)?bound\b", re.IGNORECASE)
_LIST_INTRO = re.compile(
    r"\ball\s+" + _NUM + r"\s+of\s+them\s+-\s+(.*?)\s+-\s+reach\b", re.IGNORECASE
)
_GROUP_MEMBER = re.compile(r"^the\s+" + _NUM + r"\s+above$", re.IGNORECASE)


def _number(word: str) -> int:
    return int(word) if word.isdigit() else _CARDINALS[word.lower()]


def gate_source() -> str:
    """The gate source as text, decoded from bytes so no newline is rewritten."""
    return GATE.read_bytes().decode("utf-8")


# --------------------------------------------------------------------------
# The CODE reader. Syntax tree only; never a docstring, never a comment.
# --------------------------------------------------------------------------


def _resolve(node: ast.expr | None, env: dict[str, object]) -> object:
    """A constant value for an argument expression, or the UNKNOWN sentinel."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    return _UNKNOWN


_UNKNOWN = object()

# A production's identity: the chain of (line, col) call sites from TARGET down
# to the producing node, so one helper line reached twice is two productions.
Site = tuple[tuple[int, int], ...]
# Where a walk stands: the call path so far and the stack of function names.
Where = tuple[Site, tuple[str, ...]]


def _bind(func: ast.FunctionDef, call: ast.Call, env: dict[str, object]) -> dict[str, object]:
    """Bind a call's resolvable arguments to the callee's parameter names."""
    args = func.args
    positional = [*args.posonlyargs, *args.args]
    bound: dict[str, object] = {}
    defaulted = positional[len(positional) - len(args.defaults) :]
    for param, default in zip(defaulted, args.defaults, strict=True):
        bound[param.arg] = _resolve(default, {})
    for param, kw_default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        if kw_default is not None:
            bound[param.arg] = _resolve(kw_default, {})
    # Not strict: a call may pass fewer positionals than the signature names.
    for param, value in zip(positional, call.args, strict=False):
        bound[param.arg] = _resolve(value, env)
    for keyword in call.keywords:
        if keyword.arg is not None:
            bound[keyword.arg] = _resolve(keyword.value, env)
    return bound


def _called_name(call: ast.Call) -> str | None:
    """The bare name a call invokes, whether spelled `f(...)` or `x.f(...)`."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _params(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> set[str]:
    args = node.args
    names = {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
    names.update(a.arg for a in (args.vararg, args.kwarg) if a is not None)
    return names


def _annotation_node_ids(tree: ast.AST) -> set[int]:
    """Every node that sits inside a type annotation, where a name is not a use."""
    roots: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
            roots.append(node.returns)
        if isinstance(node, ast.arg) and node.annotation is not None:
            roots.append(node.annotation)
        if isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
    return {id(inner) for root in roots for inner in ast.walk(root)}


def indirect_references(source: str) -> list[str]:
    """Module-wide refusals: the sink or Diagnostic reached by anything but a call.

    An alias (`f = SINK`), a rebinding, an argument pass or a lookup by string
    name would let a blocking production hide from the call walk below, so
    each is REFUSED rather than followed - following aliases is a denylist of
    spellings, and refusing every non-call reference is an allowlist of one.
    """
    tree = ast.parse(source)
    watched = {SINK, DIAGNOSTIC}
    call_funcs = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    annotations = _annotation_node_ids(tree)
    problems: list[str] = []
    for node in ast.walk(tree):
        if id(node) in call_funcs or id(node) in annotations:
            continue
        name = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            name = node.value
        # isinstance narrows for the type checker only: a non-None name was read
        # from a Name, Attribute or Constant, each of which is an ast.expr.
        if name in watched and isinstance(node, ast.expr):
            problems.append(
                "%s is referenced without being called at line %d" % (name, node.lineno)
            )
    return problems


def analyse_code(source: str) -> tuple[set[Site], list[str]]:
    """Blocking productions reachable from TARGET, plus what the walk could not read."""
    sites, problems, _degradations = walk_target(source)
    return sites, problems


def _reraises(handler: ast.ExceptHandler) -> bool:
    """Whether a handler's own body raises, not counting nested functions."""
    pending: list[ast.AST] = list(handler.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        pending.extend(ast.iter_child_nodes(node))
    return False


def walk_target(source: str) -> tuple[set[Site], list[str], set[Site]]:
    """Blocking productions, unreadable spots and NON-BLOCKING DEGRADATIONS.

    A NON-BLOCKING DEGRADATION (CS-1106) is a place where a failure to look is
    absorbed without reaching the exit status: an `except` handler that
    neither re-raises nor makes a blocking production while it is walked, or
    a `suppress(...)` call. Every such handler counts, whatever it returns -
    fail closed - and each is keyed by its call path exactly as a production
    is.

    A BLOCKING PRODUCTION is any of: a call of the sink whose `blocking`
    resolves True; a `Diagnostic(...)` construction, since every diagnostic on
    a report reaches the exit status; and a use of the blocking reason text
    outside a `Diagnostic(...)` it already counted. The sink's own body is
    never walked, so its one internal construction is not counted again.

    Nested functions, lambdas and classes inside a reached function are walked
    whether or not anything calls them - an uncalled nested producer counts,
    which fails closed. A reached sink call whose `blocking` cannot be resolved
    is returned as a problem rather than skipped.
    """
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert TARGET in functions, "the gate no longer defines " + TARGET
    sites: set[Site] = set()
    problems: list[str] = []
    degradations: set[Site] = set()

    def walk_function(
        name: str, env: dict[str, object], path: Site, stack: tuple[str, ...]
    ) -> None:
        # The recursion guard is the live call STACK, never a visited set: a
        # visited set keyed on the callee collapses two call sites of one
        # helper into one production, which is the F1 defect.
        if name in stack:
            return
        for statement in functions[name].body:
            walk_node(statement, env, (path, (*stack, name)), in_diagnostic=False)

    def walk_node(node: ast.AST, env: dict[str, object], at: Where, *, in_diagnostic: bool) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            inner = {k: v for k, v in env.items() if k not in _params(node)}
            body = node.body if isinstance(node.body, list) else [node.body]
            for child in body:
                walk_node(child, inner, at, in_diagnostic=in_diagnostic)
            return
        if isinstance(node, ast.ExceptHandler):
            before = len(sites)
            for child in node.body:
                walk_node(child, env, at, in_diagnostic=in_diagnostic)
            if len(sites) == before and not _reraises(node):
                degradations.add((*at[0], (node.lineno, node.col_offset)))
            return
        children: list[ast.AST] = list(ast.iter_child_nodes(node))
        if isinstance(node, ast.If):
            guard = _resolve(node.test, env)
            children = [node.test]
            children += node.body if guard is _UNKNOWN or guard else []
            children += node.orelse if guard is _UNKNOWN or not guard else []
        if isinstance(node, ast.Name) and node.id == REASON and not in_diagnostic:
            sites.add((*at[0], (node.lineno, node.col_offset)))
        if isinstance(node, ast.Call):
            in_diagnostic = visit_call(node, env, at) or in_diagnostic
        for nested in children:
            walk_node(nested, env, at, in_diagnostic=in_diagnostic)

    def visit_call(node: ast.Call, env: dict[str, object], at: Where) -> bool:
        """Record what one call produces; True when it constructs a Diagnostic."""
        callee = _called_name(node)
        site = (*at[0], (node.lineno, node.col_offset))
        if callee == SINK:
            value = next(
                (_resolve(k.value, env) for k in node.keywords if k.arg == "blocking"),
                _UNKNOWN,
            )
            if value is _UNKNOWN:
                problems.append("unresolvable blocking at line %d" % node.lineno)
            elif value is True:
                sites.add(site)
            return False
        if callee == DIAGNOSTIC:
            sites.add(site)
            return True
        if callee == SUPPRESS:
            degradations.add(site)
        if isinstance(node.func, ast.Name) and callee in functions:
            walk_function(callee, _bind(functions[callee], node, env), site, at[1])
        return False

    walk_function(TARGET, {}, (), ())
    return sites, problems, degradations


def non_blocking_degradation_sites(source: str) -> set[Site]:
    """Every non-blocking degradation reachable from TARGET, keyed by call path."""
    return walk_target(source)[2]


def blocking_bound_sites(source: str) -> set[Site]:
    """Every blocking production reachable from TARGET, keyed by its call path."""
    return analyse_code(source)[0]


# --------------------------------------------------------------------------
# The PROSE reader. STRING and COMMENT tokens only; never a call or a name.
# --------------------------------------------------------------------------


def target_prose(source: str) -> tuple[str, list[str]]:
    """The TARGET docstring and its body comments, from tokens alone.

    The function's line range is located by its `def` line and the next
    top-level statement, found textually, so no syntax-tree node of the body
    is consulted.
    """
    lines = source.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("def " + TARGET + "("))
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if lines[i][:1] not in ("", " ", "\t", "\n", "\r", "#")
        ),
        len(lines),
    )
    chunk = "".join(lines[start:end])
    docstring = ""
    comments: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(chunk).readline):
        if token.type == tokenize.STRING and not docstring:
            docstring = ast.literal_eval(token.string)
        elif token.type == tokenize.COMMENT:
            comments.append(token.string.lstrip("#").strip())
    return docstring, comments


def _normalise(text: str) -> str:
    return " ".join(text.split())


def spelled_totals(text: str) -> list[tuple[str, int]]:
    """Every spelled total in a piece of prose, as (phrase, total asserted)."""
    flat = _normalise(text)
    return [
        (match.group(0), _number(match.group(1)) + extra)
        for pattern, extra in _TOTAL_PATTERNS
        for match in pattern.finditer(flat)
    ]


_CARDINAL = re.compile(_NUM_WORD_OR_DIGITS, re.IGNORECASE)

# The ALLOWLIST for numerals in body comments. Anything a cardinal appears in
# that is not masked by one of these is red, whatever it is next to - a
# denylist of total phrasings leaked on its first adversarial pass. Each entry
# is a form that cannot state how many bounds there are:
_COMMENT_ALLOWLIST: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        # An item id names a row, not a quantity.
        r"\bCS-\d+\b",
        # A CLAUDE.md rule number names a rule, not a quantity.
        r"\bnon-negotiables? \d+\b",
        # A pronoun standing for "budget" after a decimal literal. Listed
        # BEFORE the decimal entry, which would otherwise mask its anchor.
        r"\b\d+\.\d+ second one\b",
        # A decimal literal is a time value quoted from a format example.
        r"\b\d+\.\d+\b",
        # A ratio between two renderings of one budget.
        r"\ba factor of two\b",
        # A pronoun: the aggregate budget is the only one there is.
        r"\bthe only one there is\b",
        # The granted CS-1096 wording: an increment, never a total.
        r"\bit is one more bound\b",
    )
)


def unallowed_cardinals(comment: str) -> list[str]:
    """Every cardinal (digits, or a number word) left after the allowlist masks."""
    masked = comment
    for pattern in _COMMENT_ALLOWLIST:
        masked = pattern.sub(lambda match: " " * len(match.group(0)), masked)
    return [match.group(0) for match in _CARDINAL.finditer(masked)]


def listed_members(docstring: str) -> int | None:
    """How many bounds the "All N of them - ... - reach" list names, or None."""
    match = _LIST_INTRO.search(_normalise(docstring))
    if match is None:
        return None
    members = [m.strip() for m in re.split(r",\s*(?:and\s+)?", match.group(2)) if m.strip()]
    total = 0
    for member in members:
        group = _GROUP_MEMBER.match(member)
        total += _number(group.group(1)) if group else 1
    return total


# --------------------------------------------------------------------------
# The grade.
# --------------------------------------------------------------------------


def mismatches(source: str) -> list[str]:
    """Every disagreement between the prose and the code, empty when they agree."""
    sites, code_problems = analyse_code(source)
    code_problems = code_problems + indirect_references(source)
    count = len(sites)
    docstring, comments = target_prose(source)
    problems: list[str] = []

    totals = spelled_totals(docstring)
    if not totals:
        problems.append("the docstring spells no bound total, so nothing is graded")
    for phrase, total in totals:
        if total != count:
            problems.append("docstring %r says %d; the code has %d" % (phrase, total, count))

    listed = listed_members(docstring)
    if listed is None:
        problems.append("the docstring no longer introduces its bound list")
    elif listed != count:
        problems.append("the docstring list names %d bounds; the code has %d" % (listed, count))

    problems.extend(code_problems)
    for comment in comments:
        problems.extend(
            "CS-1096 Q4 numeral rule, not a bound-count mismatch: body comment %r "
            "carries the numeral %r, and no body comment of %s may carry one. If it "
            "states no bound total, add a justified entry to _COMMENT_ALLOWLIST in "
            "tests/test_world_token_bound_count.py" % (comment, word, TARGET)
            for word in unallowed_cardinals(comment)
        )
        problems.extend(
            "body comment %r exceeds %d bounds" % (match.group(0), count)
            for match in _ORDINAL_BOUND.finditer(comment)
            if _ORDINALS[match.group(1).lower()] > count
        )
    return problems


# A spelled total over the NON-BLOCKING population (CS-1106). "not the only
# non-blocking degradation" is a denial of a total, not a total, so it is
# excluded by the lookbehind rather than graded as one.
_NON_BLOCKING_TOTALS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b" + _NUM + r"\s+(?:\w+\s+){0,2}non-blocking\s+degradations?\b", re.IGNORECASE),
    re.compile(
        r"\b" + _NUM + r"\s+degradations?\s+(?:is|are)\s+(?:\w+\s+){0,2}not\s+blocking\b",
        re.IGNORECASE,
    ),
)
_SOLE_NON_BLOCKING = re.compile(
    r"(?<!not the )\b(?:only|sole|singular|single)\s+(?:\w+\s+){0,2}non-blocking\s+degradation\b",
    re.IGNORECASE,
)


def spelled_non_blocking_totals(text: str) -> list[tuple[str, int]]:
    """Every total a piece of prose spells over the non-blocking population."""
    flat = _normalise(text)
    found = [
        (match.group(0), _number(match.group(1)))
        for pattern in _NON_BLOCKING_TOTALS
        for match in pattern.finditer(flat)
    ]
    found += [(match.group(0), 1) for match in _SOLE_NON_BLOCKING.finditer(flat)]
    return found


def non_blocking_mismatches(source: str) -> list[str]:
    """CS-1106: every non-blocking total in the target's prose against the code.

    The docstring and the body comments are each read as one text, so a total
    wrapped across two comment lines is still seen. No total at all is GREEN:
    prose that states no count cannot drift from one, which is the shape the
    CS-1096 grant chose for the bound count too.
    """
    count = len(non_blocking_degradation_sites(source))
    docstring, comments = target_prose(source)
    return [
        "%s %r says %d non-blocking degradation(s); the code reaches %d"
        % (where, phrase, total, count)
        for where, text in (("docstring", docstring), ("body comment", " ".join(comments)))
        for phrase, total in spelled_non_blocking_totals(text)
        if total != count
    ]


def test_the_non_blocking_total_agrees_with_the_code() -> None:
    """CS-1106: a total over the non-blocking degradations matches the code."""
    problems = non_blocking_mismatches(gate_source())
    assert problems == [], "\n".join(problems)


def test_the_non_blocking_walk_reaches_the_target_and_its_helpers() -> None:
    """Anti-vacuity: the set holds handlers in the target AND behind a call.

    A walk that never left the target, or never entered it, would grade a
    total against the wrong population and could agree with a false sentence.
    """
    degradations = non_blocking_degradation_sites(gate_source())
    assert any(len(path) == 1 for path in degradations)
    assert any(len(path) > 1 for path in degradations)


def test_the_bound_prose_agrees_with_the_code() -> None:
    """The spelled count, its list and the body comments all match the code."""
    problems = mismatches(gate_source())
    assert problems == [], "\n".join(problems)


# --------------------------------------------------------------------------
# Mutation arms - in memory only, each asserting its mutant applied.
# --------------------------------------------------------------------------

_ANCHOR = "    started = time.monotonic()\n"


def _plant_in_target(source: str, *lines: str) -> str:
    assert source.count(_ANCHOR) == 1, "the plant anchor is not unique"
    mutant = source.replace(_ANCHOR, _ANCHOR + "".join("    " + line + "\n" for line in lines))
    assert mutant != source, "the plant did not apply"
    return mutant


def test_a_planted_blocking_bound_reddens_the_arm() -> None:
    """A new blocking bound without touching the sentence FAILS (acceptance)."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, SINK + '(report, "planted", blocking=True)')
    assert len(blocking_bound_sites(mutant)) == len(blocking_bound_sites(pristine)) + 1
    assert mismatches(mutant) != []


def test_a_planted_non_blocking_report_stays_green() -> None:
    """blocking=False is not a bound reaching the exit status."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, SINK + '(report, "planted", blocking=False)')
    assert len(blocking_bound_sites(mutant)) == len(blocking_bound_sites(pristine))
    assert mismatches(mutant) == mismatches(pristine)


def test_a_blocking_bound_the_scan_never_reaches_stays_green() -> None:
    """A blocking call in a function TARGET never calls is not one of its bounds."""
    pristine = gate_source()
    mutant = (
        pristine
        + "\n\ndef _cs1096_unreached(report):\n    "
        + SINK
        + '(report, "planted", blocking=True)\n'
    )
    assert mutant != pristine
    assert len(blocking_bound_sites(mutant)) == len(blocking_bound_sites(pristine))
    assert mismatches(mutant) == mismatches(pristine)


def test_parameter_binding_is_followed_through_callers() -> None:
    """Flipping a caller's flag removes the sites that flag controls."""
    pristine = gate_source()
    old = "files_only=True, uncovered_blocks=True"
    assert pristine.count(old) == 1, "the binding anchor is not unique"
    mutant = pristine.replace(old, "files_only=True, uncovered_blocks=False")
    assert mutant != pristine
    assert len(blocking_bound_sites(mutant)) < len(blocking_bound_sites(pristine))
    assert mismatches(mutant) != []


def test_a_changed_spelled_total_reddens_the_arm() -> None:
    """The prose side is graded too: a wrong number in the docstring FAILS."""
    pristine = gate_source()
    docstring, _ = target_prose(pristine)
    phrase, _total = spelled_totals(docstring)[0]
    word = phrase.split()[1] if phrase.lower().startswith("all ") else phrase.split()[0]
    wrong = "twenty" if word.lower() != "twenty" else "nineteen"
    mutant = pristine.replace(phrase, phrase.replace(word, wrong), 1)
    assert mutant != pristine
    assert mismatches(mutant) != []


def test_a_total_restated_in_a_body_comment_reddens_the_arm() -> None:
    """A spelled total in a body comment is a second copy to drift (Q4)."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, "# belongs with the other three bounds.")
    assert mismatches(mutant) != []


def test_the_historical_first_five_sentence_is_not_graded() -> None:
    """Q5: the arrival history of the first bounds is not a total.

    It lives in the DOCSTRING, which is graded by total phrasing; the
    body-comment allowlist does not apply there. Asserting the sentence is
    present keeps this arm from passing because the sentence moved.
    """
    history = "The first five used to report through the skip channel alone"
    docstring, _ = target_prose(gate_source())
    assert history in _normalise(docstring)
    assert spelled_totals(history) == []


def test_an_inline_blocking_diagnostic_reddens_the_arm() -> None:
    """A blocking bound done INLINE, without the helper, is still a bound.

    The arm counts blocking PRODUCTION, not calls to one helper name: a direct
    `report.add` of the uncovered-population diagnostic reaches the exit status
    exactly as the helper does.
    """
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine,
        'report.add(Diagnostic(PII_WORLD_LABEL, 0, 0, "PII", WORLD_SCAN_UNCOVERED_REASON))',
    )
    assert mismatches(mutant) != []


def test_a_local_alias_of_the_sink_reddens_the_arm() -> None:
    """Calling the helper through a local name must not hide the call."""
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine, "_alias = " + SINK, '_alias(report, "planted", blocking=True)'
    )
    assert mismatches(mutant) != []


def test_a_lookup_of_the_sink_by_string_name_reddens_the_arm() -> None:
    """A getattr by name is an alias the call walk cannot see, so it is refused."""
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine, 'getattr(sys.modules[__name__], "' + SINK + '")(report, "p", blocking=True)'
    )
    assert mismatches(mutant) != []


def test_a_sink_call_inside_a_nested_function_reddens_the_arm() -> None:
    """A nested def inside the target is part of the target."""
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine,
        "def _inner() -> None:",
        "    " + SINK + '(report, "planted", blocking=True)',
        "_inner()",
    )
    assert mismatches(mutant) != []


def test_a_sink_call_inside_a_lambda_reddens_the_arm() -> None:
    """A lambda inside the target is part of the target."""
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine, "(lambda: " + SINK + '(report, "planted", blocking=True))()'
    )
    assert mismatches(mutant) != []


@pytest.mark.parametrize(
    "comment",
    [
        "# belongs with the remaining four and not with the skip.",
        "# the 6 caps that truncate this population",
        "# a pair of bounds, then three more",
        "# there are seven now",
    ],
)
def test_any_cardinal_in_a_body_comment_reddens_the_arm(comment: str) -> None:
    """The comment check is an ALLOWLIST: a count in any phrasing is red."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, comment)
    assert mismatches(mutant) != []


def test_a_second_call_of_a_shared_reporting_helper_reddens_the_arm() -> None:
    """Productions are keyed by CALL PATH, not by the line inside the helper.

    A second `_report_root_cap(..., blocking=True)` in the target reaches the
    same sink line inside the helper as the first one does, so a count keyed
    by that line saw one production where there are two.
    """
    pristine = gate_source()
    mutant = _plant_in_target(
        pristine, '_report_root_cap(report, PII_WORLD_LABEL, "declared dirs", blocking=True)'
    )
    assert len(blocking_bound_sites(mutant)) == len(blocking_bound_sites(pristine)) + 1
    assert mismatches(mutant) != []


def test_a_numeral_in_a_comment_names_the_rule_it_broke() -> None:
    """A numeral-rule red says what it is and where to clear it (adjudicated F4).

    "one file at a time" states no bound total, so the message must not read as
    a bound-count mismatch: it names the CS-1096 Q4 numeral rule, this test
    file, and _COMMENT_ALLOWLIST as the place a justified entry goes.
    """
    pristine = gate_source()
    mutant = _plant_in_target(pristine, "# one file at a time")
    problems = mismatches(mutant)
    assert problems != []
    message = "\n".join(problems)
    assert "CS-1096 Q4 numeral rule" in message
    assert "not a bound-count mismatch" in message
    assert "tests/test_world_token_bound_count.py" in message
    assert "_COMMENT_ALLOWLIST" in message


# --------------------------------------------------------------------------
# CS-1106 mutation arms - the non-blocking population, in memory only.
# --------------------------------------------------------------------------

_DOCSTRING_ANCHOR = "    Returns:\n        The tokens read, unfiltered,"


def _plant_in_docstring(source: str, sentence: str) -> str:
    assert source.count(_DOCSTRING_ANCHOR) == 1, "the docstring anchor is not unique"
    mutant = source.replace(_DOCSTRING_ANCHOR, "    " + sentence + "\n\n" + _DOCSTRING_ANCHOR)
    assert mutant != source, "the plant did not apply"
    return mutant


def _without_non_blocking_totals(source: str) -> str:
    """The source with every non-blocking total in the target's prose neutralised.

    The mutation arms below need a pristine baseline that is GREEN on this
    arm whatever the frozen file currently says, so a verdict reads the effect
    of the plant alone. Each total's cardinal is replaced by "some", which the
    patterns do not read, and the rewrite asserts it removed every total.
    """
    docstring, comments = target_prose(source)
    mutant = source
    for text in (docstring, *comments):
        for phrase, _total in spelled_non_blocking_totals(text):
            word = phrase.split()[0]
            mutant = mutant.replace(phrase, "some" + phrase[len(word) :])
    assert all(
        spelled_non_blocking_totals(text) == []
        for text in (target_prose(mutant)[0], " ".join(target_prose(mutant)[1]))
    ), "a non-blocking total survived the neutralising rewrite"
    return mutant


def test_a_false_non_blocking_total_in_a_body_comment_reddens_the_arm() -> None:
    """The CS-1106 sentence shape, planted, is red against the code count."""
    pristine = _without_non_blocking_totals(gate_source())
    assert non_blocking_mismatches(pristine) == []
    count = len(non_blocking_degradation_sites(pristine))
    mutant = _plant_in_target(
        pristine, "# the %d deliberate non-blocking degradations" % (count + 1)
    )
    assert non_blocking_mismatches(mutant) != []


def test_a_false_sole_non_blocking_claim_in_the_docstring_reddens_the_arm() -> None:
    """A sole-claim ("The only non-blocking degradation") asserts a total of one."""
    pristine = _without_non_blocking_totals(gate_source())
    assert len(non_blocking_degradation_sites(pristine)) != 1
    mutant = _plant_in_docstring(pristine, "The only non-blocking degradation is a bad file.")
    assert non_blocking_mismatches(mutant) != []


def test_a_denied_sole_claim_is_not_a_total() -> None:
    """A denial ("not the only non-blocking degradation") states no total."""
    assert spelled_non_blocking_totals("it is not the only non-blocking degradation") == []


def test_a_true_non_blocking_total_stays_green() -> None:
    """The arm grades against the CODE, so a total equal to the count is green."""
    pristine = _without_non_blocking_totals(gate_source())
    count = len(non_blocking_degradation_sites(pristine))
    mutant = _plant_in_docstring(pristine, "%d DEGRADATIONS ARE NOT BLOCKING." % count)
    assert spelled_non_blocking_totals(target_prose(mutant)[0]) != []
    assert non_blocking_mismatches(mutant) == []


def test_a_planted_swallowing_handler_is_one_more_degradation() -> None:
    """A new `except` that absorbs a failure raises the code count by one."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, "try:", "    pass", "except OSError:", "    pass")
    after = non_blocking_degradation_sites(mutant)
    assert len(after) == len(non_blocking_degradation_sites(pristine)) + 1


def test_a_planted_suppress_is_one_more_degradation() -> None:
    """`with suppress(...)` swallows without a handler node, and still counts."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, "with suppress(OSError):", "    pass")
    after = non_blocking_degradation_sites(mutant)
    assert len(after) == len(non_blocking_degradation_sites(pristine)) + 1


@pytest.mark.parametrize(
    "handler_body",
    [
        ["    raise"],
        ["    " + SINK + '(report, "planted", blocking=True)'],
    ],
)
def test_a_handler_that_raises_or_blocks_is_not_a_degradation(handler_body: list[str]) -> None:
    """Re-raising, or reaching the exit status, is not a non-blocking swallow."""
    pristine = gate_source()
    mutant = _plant_in_target(pristine, "try:", "    pass", "except OSError:", *handler_body)
    assert len(non_blocking_degradation_sites(mutant)) == len(
        non_blocking_degradation_sites(pristine)
    )


def test_a_swallowing_handler_the_scan_never_reaches_is_not_counted() -> None:
    """A handler in a function the target never calls is another population."""
    pristine = gate_source()
    unreached = (
        "def _cs1106_unreached():\n    try:\n        pass\n    except OSError:\n        pass\n"
    )
    mutant = pristine + "\n\n" + unreached
    assert mutant != pristine
    assert len(non_blocking_degradation_sites(mutant)) == len(
        non_blocking_degradation_sites(pristine)
    )
