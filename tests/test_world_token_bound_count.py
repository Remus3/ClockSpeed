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
  bound, and collects every distinct call site of
  `_report_world_token_uncovered` whose `blocking` resolves to True. It never
  looks at a docstring or a comment.
- The PROSE reader tokenizes the function's source range and keeps STRING and
  COMMENT tokens only. It never looks at a call, a name or a keyword.

What the prose side grades:

1. Every spelled TOTAL in the docstring ("All N", "The N bounds", "the other
   N") equals the code count, and at least one is present - an arm that finds
   no total grades nothing. A bare "N of them" is NOT a total: "every one of
   them is self-healing" is distributive, and it sits in this very docstring.
2. The list that "All N of them" introduces has as many members as the code
   count, with a member of the shape "the N above" expanded to N.
3. The function-body comments carry NO spelled total at all (adjudicated Q4):
   a total in a comment is a second copy of the number to drift, which is the
   exact defect this row was filed for. An ARRIVAL ordinal ("the Nth bound")
   is history rather than a total and stays true when a later bound lands, so
   it is only held to not exceed the code count.

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

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "precommit_gate.py"

TARGET = "_world_tokens_from_headers"
SINK = "_report_world_token_uncovered"

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


def blocking_bound_sites(source: str) -> set[tuple[int, int]]:
    """Every (line, col) call site of the sink that blocks, reachable from TARGET.

    Raises AssertionError when a reached sink call has a `blocking` the walk
    cannot resolve - an arm that silently skips what it cannot read grades
    less than it claims.
    """
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert TARGET in functions, "the gate no longer defines " + TARGET
    sites: set[tuple[int, int]] = set()
    visited: set[tuple[str, tuple[tuple[str, str], ...]]] = set()

    def walk_function(name: str, env: dict[str, object]) -> None:
        key = (name, tuple(sorted((k, repr(v)) for k, v in env.items())))
        if key in visited:
            return
        visited.add(key)
        for statement in functions[name].body:
            walk_node(statement, env)

    def walk_node(node: ast.AST, env: dict[str, object]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return
        if isinstance(node, ast.If):
            guard = _resolve(node.test, env)
            walk_node(node.test, env)
            if guard is _UNKNOWN or guard:
                for child in node.body:
                    walk_node(child, env)
            if guard is _UNKNOWN or not guard:
                for child in node.orelse:
                    walk_node(child, env)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            callee = node.func.id
            if callee == SINK:
                value = next(
                    (_resolve(k.value, env) for k in node.keywords if k.arg == "blocking"),
                    _UNKNOWN,
                )
                assert value is not _UNKNOWN, "unresolvable blocking at line %d" % node.lineno
                if value is True:
                    sites.add((node.lineno, node.col_offset))
            elif callee in functions and callee != TARGET:
                walk_function(callee, _bind(functions[callee], node, env))
        for child in ast.iter_child_nodes(node):
            walk_node(child, env)

    walk_function(TARGET, {})
    return sites


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
    count = len(blocking_bound_sites(source))
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

    for comment in comments:
        for phrase, total in spelled_totals(comment):
            problems.append("body comment %r spells a total (%d)" % (phrase, total))
        problems.extend(
            "body comment %r exceeds %d bounds" % (match.group(0), count)
            for match in _ORDINAL_BOUND.finditer(comment)
            if _ORDINALS[match.group(1).lower()] > count
        )
    return problems


def test_the_bound_prose_agrees_with_the_code() -> None:
    """The spelled count, its list and the body comments all match the code."""
    problems = mismatches(gate_source())
    assert problems == [], "\n".join(problems)


# --------------------------------------------------------------------------
# Mutation arms - in memory only, each asserting its mutant applied.
# --------------------------------------------------------------------------

_ANCHOR = "    started = time.monotonic()\n"


def _plant_in_target(source: str, line: str) -> str:
    assert source.count(_ANCHOR) == 1, "the plant anchor is not unique"
    mutant = source.replace(_ANCHOR, _ANCHOR + "    " + line + "\n")
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
    """Q5: the arrival history of the first bounds is not a total."""
    assert spelled_totals("The first five used to report through the skip channel alone") == []
