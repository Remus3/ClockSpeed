"""The lane refusal seam, graded end to end: `lanes.py` -> `run_cycle` -> the row.

A REFUSED ACQUIRE IS A DURABLE FACT. `run_cycle` turns a refusal dict built by
`ops/loop/lanes.py` into a cycle row, and `append_record` writes that row into
`ops/loop/reports/queue_loop.jsonl`, a file that outlives every session. Every
value copied out of the refusal dict is therefore a value copied off a LOCK
FILE this driver did not write into a file that keeps it.

CS-1014 grades the pid half of that copy, which had a correct guard and no arm.

No arm here spawns a process, sleeps or reads the live channel. The lock arms
take REAL lane locks, but only under `tmp_path`, and each proves its own lock is
gone before it returns.
"""

from __future__ import annotations

import ast
import contextlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# A PLAIN IMPORT, never importorskip: a missing driver is a COLLECTION error.
from ops.loop import lane_launcher, lanes, queue_loop  # noqa: E402

#: A path SEGMENT planted where an account name would sit. A segment carries no
#: separator, so it survives every escaping a renderer can apply.
NEEDLE: Final = "cs1014-account-needle"

#: A PATH-SHAPED pid, synthetic and rooted at no real home directory. Built from
#: parts so no tracked byte spells a home path; `Path` gives it this platform's
#: separator, which is the shape a hand-edited or older lock file would carry.
PLANTED_PID: Final = str(Path("/") / "synthetic-home" / NEEDLE / "lanes" / "queue.lock")

#: The two refusal words, and so the two sites that render `(pid {pid})`.
REFUSAL_WORDS: Final = ("lane_held", "worktree_in_use")


class FakeClock:
    """A wall and a monotonic clock that advance only through `sleep`."""

    def __init__(self) -> None:
        """Start both clocks at fixed readings."""
        self.wall = 1_000_000.0
        self.mono = 0.0

    def time(self) -> float:
        """Wall time, for the row stamp."""
        return self.wall

    def monotonic(self) -> float:
        """Deadline time."""
        return self.mono

    def sleep(self, seconds: float) -> None:
        """Advance both clocks instead of blocking."""
        self.wall += float(seconds)
        self.mono += float(seconds)


def _stated_surface(_worktree: Any) -> dict[str, Any]:
    """A STATED channel fact, so no arm here reads `moon_sync_inbox/`."""
    return {"unread": 0, "names": [], "more": 0, "reason": ""}


def _never_launch(_lane: str, **_kw: Any) -> dict[str, Any]:
    """A refused cycle must never reach the launcher."""
    message = "a refused acquire reached the launcher"
    raise AssertionError(message)


def _refusing(word: str, **extra: Any):
    """An `acquire` seam that refuses every attempt with `word`."""
    payload: dict[str, Any] = {"ok": False, "refused": word, "holder": "queue-b", "pid": 99}
    payload.update(extra)
    return lambda _lane, **_kw: dict(payload)


def _cycle(acquire, worktree: str = "cs-lane-queue", **over: Any) -> dict[str, Any]:
    """Run ONE refused cycle through the real `run_cycle`, every other seam faked."""
    clock = FakeClock()
    seams: dict[str, Any] = {
        "acquire": acquire,
        "release": lambda _token, **_kw: True,
        "launch": _never_launch,
        "alive": lambda _pid: False,
        "proc_started": lambda _pid: 1.0,
        "stranger": lambda _pid, _started: False,
        "kill": lambda _pid: None,
        "acquire_retries": 1,
        "sleep": clock.sleep,
        "clock": clock.time,
        "monotonic": clock.monotonic,
        "worktree": worktree,
        "surface": _stated_surface,
        "emit": lambda _line: None,
    }
    seams.update(over)
    return queue_loop.run_cycle(1, **seams)


def _write_and_read_back(record: dict[str, Any], log: Path) -> str:
    """Write the row through the driver's own writer and return the FILE bytes."""
    queue_loop.append_record(record, log, hold=contextlib.nullcontext, emit=lambda _l: None)
    return log.read_bytes().decode("utf-8")


def _flatten(text: object) -> str:
    """Collapse every separator run and case-fold, so escaping cannot hide a leak.

    `repr` doubles a backslash and `json.dumps` doubles it again; a raw substring
    search for the planted value then never matches, which is an oracle blind
    to its subject. Searching for a SEGMENT after this collapse is not.
    """
    return re.sub(r"[\\/]+", "/", str(text)).casefold()


def _leaked(rendered: object, needle: str) -> bool:
    """Did `needle` survive into `rendered` under any escaping."""
    return _flatten(needle) in _flatten(rendered)


# ===========================================================================
# CS-1014 - a path-shaped pid never reaches `detail` or the written row
# ===========================================================================


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_the_plant_is_potent_when_the_pid_guard_is_removed(
    word: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE CONTROL: with the guard replaced by `return pid`, the plant LANDS.

    Without this, the arm below could pass because the planted value never
    travelled as far as the row at all - a refusal the driver did not read, a
    seam it did not call - and its silence would measure nothing. Replacing the
    guard with the identity function IS the `return pid` mutant, applied through
    the module attribute `run_cycle` resolves at call time, and it must put the
    needle into BOTH the detail and the bytes on disk, on BOTH render sites.
    """
    monkeypatch.setattr(queue_loop, "_holder_pid", lambda pid: pid)
    got = _cycle(_refusing(word, pid=PLANTED_PID))
    written = _write_and_read_back(got, tmp_path / "cycles.jsonl")

    assert got["outcome"] == word, "the plant did not ride the refusal it was planted on"
    assert _leaked(got["detail"], NEEDLE), f"the plant never reached detail on {word}"
    assert _leaked(written, NEEDLE), f"the plant never reached the written row on {word}"


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_a_path_shaped_pid_reaches_neither_detail_nor_the_written_row(
    word: str, tmp_path: Path
) -> None:
    """THE ARM: the same plant, the real guard, and the needle is nowhere.

    `_holder_pid` is the only thing standing between a lock file's `pid` field
    and the durable row, and the control above proves that without it the value
    lands. Graded on the BYTES `append_record` wrote, not on the dict it was
    handed, because the file is what outlives the session.
    """
    got = _cycle(_refusing(word, pid=PLANTED_PID))
    log = tmp_path / "cycles.jsonl"
    written = _write_and_read_back(got, log)

    # THE ANCHOR: the refusal really was read, so "no leak" is not the empty
    # truth of a driver that never looked at this payload.
    assert got["outcome"] == word
    # THE LEAK ASSERTIONS COME FIRST, so the `return pid` mutant reddens on the
    # property this arm is named for rather than on an anchor beside it.
    assert not _leaked(got["detail"], NEEDLE), f"a path-shaped pid reached detail on {word}"
    assert not _leaked(written, NEEDLE), f"a path-shaped pid reached the written row on {word}"
    assert not _leaked(json.dumps(got), NEEDLE), f"a path-shaped pid reached the record on {word}"
    assert "(pid None)" in got["detail"], f"the pid was not replaced by the guard: {word}"
    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    assert len(rows) == 1, "the writer did not write exactly one row"


@pytest.mark.parametrize("word", REFUSAL_WORDS)
def test_cs1014_an_honest_integer_pid_is_still_rendered(word: str, tmp_path: Path) -> None:
    """THE OTHER SIDE OF THE GUARD: a real pid is kept, so the fix is not erasure.

    A guard that returned None for everything would pass the arm above and
    destroy the one number an operator reads off a refusal row to find the
    holder. `bool` is an `int` subclass and is refused as a process.
    """
    got = _cycle(_refusing(word, pid=4242))
    written = _write_and_read_back(got, tmp_path / "cycles.jsonl")
    assert "(pid 4242)" in got["detail"], f"an honest pid was dropped on {word}"
    assert "(pid 4242)" in written, f"an honest pid did not reach the written row on {word}"

    flagged = _cycle(_refusing(word, pid=True))
    assert "(pid None)" in flagged["detail"], f"a bool was rendered as a pid on {word}"


# ===========================================================================
# CS-1015 - the refusal vocabulary, DERIVED from lanes.py rather than restated
# ===========================================================================

#: The emitter, read as SOURCE. Parsed rather than imported and introspected,
#: because the vocabulary is not a constant `lanes.py` exports - it lives in the
#: dict literals its refusal builders return - and exporting one would be a
#: second copy of the same words, which is the defect this item names.
LANES_SOURCE: Final = ROOT / "ops" / "loop" / "lanes.py"

#: The key a refusal is spelled under, the one literal this arm has to name.
REFUSED_KEY: Final = "refused"


#: The SHAPE of a refusal word - lower-case snake case of two or more parts, as
#: `lane_held` and `worktree_in_use` are. A literal of this shape that no
#: recognised emit form accounts for is a finding, because a word can reach the
#: dict by a route that never spells the key beside it.
_WORD_SHAPE: Final = re.compile(r"[a-z]+(?:_[a-z]+)+")

#: Method calls whose FIRST argument is a mapping key being READ, which is the
#: one place a key-shaped literal may sit outside a dict literal or a subscript.
_KEY_READERS: Final = frozenset({"get", "pop"})


def _key_aliases(nodes: list[ast.AST]) -> tuple[set[str], set[int]]:
    """Names bound to the refusal key, and the binding literals themselves.

    A binding literal is ACCOUNTED FOR by the binding - every later load of the
    name is then graded like the literal - so it is not a stray key. A binding
    that is anything but plain names (a tuple unpack, an attribute) is left
    unconsumed, and the stray-key sweep reports it.
    """
    aliases: set[str] = set()
    bindings: set[int] = set()
    for node in nodes:
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        value = node.value
        if not (isinstance(value, ast.Constant) and value.value == REFUSED_KEY):
            continue
        names = [target.id for target in targets if isinstance(target, ast.Name)]
        if names and len(names) == len(targets):
            aliases.update(names)
            bindings.add(id(value))
    return aliases, bindings


def _field_name_positions(nodes: list[ast.AST]) -> set[int]:
    """Positions where a snake-case literal NAMES a field rather than carries one.

    A dict literal key, a subscript index, and the key argument of `.get` or
    `.pop`. Nowhere else may a literal of refusal-word shape sit unaccounted.
    """
    positions: set[int] = set()
    for node in nodes:
        if isinstance(node, ast.Dict):
            positions.update(id(key) for key in node.keys if key is not None)
        elif isinstance(node, ast.Subscript):
            positions.add(id(node.slice))
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _KEY_READERS
            and node.args
        ):
            positions.add(id(node.args[0]))
    return positions


def _emitted_refusals(source: str) -> tuple[set[str], list[str]]:
    """Every `refused` word `source` can emit, and every site it cannot vouch for.

    THREE RECOGNISED EMIT FORMS: a dict literal key, a `dict(refused=...)`
    keyword, and a `x["refused"] = ...` subscript store - the key spelled as the
    literal or as any name bound to it. A recognised form whose value is not a
    string literal is a finding.

    FAIL CLOSED BEYOND THAT, which is what the first version did not do: it
    knew three spellings and silently walked past a fourth. So two sweeps run
    over the WHOLE tree after the forms are read, and each hit is a finding:

    - the refusal KEY - the literal, or a load of a name bound to it - anywhere a
      recognised form did not consume it (`setdefault`, a list of pairs, an
      `update`, a tuple unpack, a call argument);
    - a literal of refusal-word SHAPE anywhere but a recognised form's value, a
      dict literal key, a subscript index, or the key argument of `.get` /
      `.pop` - the positions where a snake-case literal names a field rather
      than carrying a word.

    AND A KEY IT CANNOT RESOLVE IS A FINDING TOO - see `_opaque_keys`. A key
    spelled through a class attribute, a concatenation or a module constant is
    RESOLVED statically first, so `{C.KEY: ...}` and `{'refu' + 'sed': ...}`
    are read as the refusal key they are rather than walked past.

    Args:
        source: Python source text.

    Returns:
        The set of literal words, and one `line N: ...` finding per site.
    """
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    aliases, consumed = _key_aliases(nodes)
    static = _static_resolver(tree)
    words: set[str] = set()
    values: set[int] = set()
    findings: list[str] = []

    def is_key(node: ast.AST | None) -> bool:
        if isinstance(node, ast.Name) and node.id in aliases:
            return True
        return node is not None and static(node) == REFUSED_KEY

    def take(value: ast.AST, line: int) -> None:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            words.add(value.value)
            values.add(id(value))
        else:
            findings.append(f"line {line}: a non-literal refusal word")

    for node in nodes:
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if is_key(key):
                    consumed.add(id(key))
                    take(value, node.lineno)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == REFUSED_KEY:
                    take(keyword.value, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and is_key(target.slice):
                    consumed.add(id(target.slice))
                    take(node.value, node.lineno)

    accounted = values | _field_name_positions(nodes)
    stray = _stray_sites(nodes, is_key, consumed, accounted)
    return words, findings + stray + _opaque_keys(nodes, static)


def _static_resolver(tree: ast.Module):
    """A function answering the STATIC string value of an expression, or None.

    Cheap on purpose: a string literal; a name bound ONCE, at module or class
    level, to a string literal; `Class.NAME` for such a class binding; a `+` of
    two resolvable strings; an f-string whose every part resolves. Anything else
    - a call, a local, a name bound twice - is None, which `_opaque_keys` then
    treats as a key it cannot vouch for.
    """
    module: dict[object, str | None] = {}
    classes: dict[object, str | None] = {}

    def bind(table: dict[object, str | None], key: object, value: ast.AST | None) -> None:
        literal = value.value if isinstance(value, ast.Constant) else None
        text = literal if isinstance(literal, str) else None
        table[key] = text if key not in table or table[key] == text else None

    def bindings(body: list[ast.stmt]) -> list[tuple[str, ast.AST | None]]:
        found: list[tuple[str, ast.AST | None]] = []
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                found += [(t.id, stmt.value) for t in stmt.targets if isinstance(t, ast.Name)]
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                found.append((stmt.target.id, stmt.value))
        return found

    for name, value in bindings(tree.body):
        bind(module, name, value)
    for stmt in tree.body:
        if isinstance(stmt, ast.ClassDef):
            for name, value in bindings(stmt.body):
                bind(classes, (stmt.name, name), value)

    def joined(node: ast.JoinedStr) -> str | None:
        parts: list[str] = []
        for part in node.values:
            if isinstance(part, ast.FormattedValue):
                if part.conversion != -1 or part.format_spec is not None:
                    return None
                text = resolve(part.value)
            else:
                text = resolve(part)
            if text is None:
                return None
            parts.append(text)
        return "".join(parts)

    def resolve(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else None
        if isinstance(node, ast.Name):
            return module.get(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return classes.get((node.value.id, node.attr))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = resolve(node.left), resolve(node.right)
            return None if left is None or right is None else left + right
        if isinstance(node, ast.JoinedStr):
            return joined(node)
        return None

    return resolve


def _provably_not_str(value: ast.AST | None) -> bool:
    """True only when `value` can never evaluate to a string.

    The ONE exemption from the opaque-key rule, and a narrow one: a container
    display, a comprehension, a non-string literal, or a conditional both of
    whose arms are one of those. `lanes.py`'s own ownership table is keyed by
    computed paths and holds tuples, and a tuple is never a refusal word.
    """
    if value is None:
        return True
    if isinstance(value, ast.Constant):
        return not isinstance(value.value, str)
    displays = (ast.Tuple, ast.List, ast.Set, ast.Dict, ast.ListComp, ast.SetComp)
    if isinstance(value, (*displays, ast.DictComp, ast.GeneratorExp)):
        return True
    if isinstance(value, ast.IfExp):
        return _provably_not_str(value.body) and _provably_not_str(value.orelse)
    return False


def _key_pairs(node: ast.AST, found: list[str]) -> list[tuple[ast.AST, ast.AST | None]]:
    """The (key, value) pairs one node WRITES, noting the writes it cannot read."""
    pairs: list[tuple[ast.AST, ast.AST | None]] = []
    if isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                found.append(f"line {node.lineno}: a ** unpack this derivation cannot read")
            else:
                pairs.append((key, value))
    elif isinstance(node, (ast.Assign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        pairs += [(t.slice, node.value) for t in targets if isinstance(t, ast.Subscript)]
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "setdefault" and node.args:
            pairs.append((node.args[0], node.args[1] if len(node.args) > 1 else None))
        elif node.func.attr == "update" and any(not isinstance(a, ast.Dict) for a in node.args):
            found.append(f"line {node.lineno}: an update this derivation cannot read")
    return pairs


def _opaque_keys(nodes: list[ast.AST], static) -> list[str]:
    """FAIL CLOSED on every key this derivation cannot see through.

    A dict literal key, a subscript STORE key, and a `setdefault` key whose
    static value cannot be resolved are findings - unless the value beside it
    provably cannot be a string. So are a `**` unpack inside a dict literal and
    an `update` fed anything but a dict literal, because either can carry the
    refusal key in from somewhere this parse never looks.
    """
    found: list[str] = []
    for node in nodes:
        for key, value in _key_pairs(node, found):
            if static(key) is None and not _provably_not_str(value):
                line = getattr(key, "lineno", getattr(node, "lineno", 0))
                found.append(f"line {line}: a key this derivation cannot resolve")
    return found


def _stray_sites(
    nodes: list[ast.AST], is_key, consumed: set[int], accounted: set[int]
) -> list[str]:
    """The fail-closed sweep: every key and word-shaped literal nothing accounted for."""
    stray: list[str] = []
    for node in nodes:
        line = getattr(node, "lineno", 0)
        loaded = not isinstance(node, ast.Name) or isinstance(node.ctx, ast.Load)
        if is_key(node) and loaded and id(node) not in consumed:
            stray.append(f"line {line}: the refusal key outside a recognised emit form")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _WORD_SHAPE.fullmatch(node.value)
            and id(node) not in accounted
        ):
            stray.append(f"line {line}: a refusal-shaped literal outside a recognised form")
    return stray


def _driver_covers(words: set[str]) -> set[str]:
    """The emitted words the driver does NOT hold. Empty means covered."""
    return words - set(queue_loop._ACQUIRE_REFUSALS)  # noqa: SLF001 - the contract under test


def test_cs1015_every_refused_word_lanes_can_emit_is_one_the_driver_holds() -> None:
    """THE CONTRACT: `set(_ACQUIRE_REFUSALS)` covers what `lanes.py` emits.

    Measured when this item was filed: renaming the word at the emitter alone
    left every queue-loop arm passing, because each fake spelled the word again
    by hand. This arm reads the words OUT OF THE EMITTER, so a rename or a new
    word there is a word the driver does not hold, and this reddens.
    """
    words, opaque = _emitted_refusals(LANES_SOURCE.read_text(encoding="utf-8"))

    # ANTI-VACUITY: an empty derivation covers trivially. The emitter answers
    # at least the two faults CS-1011 separated, so fewer than two means the
    # parse is looking in the wrong place, not that the vocabulary shrank.
    assert len(words) >= len(REFUSAL_WORDS), f"the derivation found too few words: {sorted(words)}"
    assert opaque == [], f"lanes.py has refusal sites this contract cannot vouch for: {opaque}"
    uncovered = sorted(_driver_covers(words))
    assert uncovered == [], f"lanes.py emits refusal words the driver does not hold: {uncovered}"


def test_cs1015_a_rename_in_a_temp_copy_of_lanes_reddens_the_contract(tmp_path: Path) -> None:
    """THE RENAME MUTANT, in a TEMP COPY, so the real emitter is never touched.

    Proves the arm above is live against the exact edit the item was filed on:
    one word renamed at the emitter and nowhere else.
    """
    pristine = LANES_SOURCE.read_text(encoding="utf-8")
    # THE BUILDER'S OWN LINE, anchored on its indentation: the same pair also
    # appears in `try_acquire_lane`'s docstring, and renaming prose would be a
    # mutant the AST never sees.
    old = '\n        "refused": "worktree_in_use",\n'
    sites = pristine.count(old)
    assert sites == 1, f"the rename site moved - re-aim the mutant ({sites} matches)"
    copy = tmp_path / "lanes.py"
    copy.write_text(
        pristine.replace(old, '\n        "refused": "worktree_taken",\n'), encoding="utf-8"
    )
    mutated = copy.read_text(encoding="utf-8")
    assert old not in mutated, "THE MUTANT DID NOT APPLY - a green here would measure nothing"

    words, opaque = _emitted_refusals(mutated)
    assert opaque == []
    assert _driver_covers(words) == {"worktree_taken"}, "the rename was not seen as uncovered"
    # AND THE PRISTINE FLOOR IN THE SAME RUN: the same derivation, the real file.
    assert _driver_covers(_emitted_refusals(pristine)[0]) == set()


def test_cs1015_a_new_word_or_an_opaque_value_in_a_temp_copy_reddens(tmp_path: Path) -> None:
    """GROWTH and INDIRECTION: a third word, and a word the parse cannot read.

    Both spellings a later edit could reach for - a new refusal builder, and a
    word held in a variable or a subscript store - must fail the contract
    rather than slip past it.
    """
    pristine = LANES_SOURCE.read_text(encoding="utf-8")
    grown = tmp_path / "lanes_grown.py"
    grown.write_text(
        pristine + '\n\ndef _third(state):\n    return {"ok": False, "refused": "lane_retired"}\n',
        encoding="utf-8",
    )
    words, _ = _emitted_refusals(grown.read_text(encoding="utf-8"))
    assert _driver_covers(words) == {"lane_retired"}, "a new emitter word was not seen"

    indirect = tmp_path / "lanes_indirect.py"
    indirect.write_text(
        pristine
        + "\n\nWORD = 'lane_held'\n\n"
        + "def _fourth(answer):\n"
        + "    answer['refused'] = 'lane_parked'\n"
        + "    return dict(ok=False, refused=WORD)\n",
        encoding="utf-8",
    )
    words, opaque = _emitted_refusals(indirect.read_text(encoding="utf-8"))
    assert "lane_parked" in _driver_covers(words), "a subscript-store word was not seen"
    flagged = [f for f in opaque if "non-literal" in f]
    assert len(flagged) == 1, f"a non-literal refusal word was not flagged: {opaque}"


def _contract_faults(source: str) -> list[str]:
    """Everything that makes the contract RED for `source`: findings, then gaps."""
    words, findings = _emitted_refusals(source)
    return findings + [f"uncovered word {w}" for w in sorted(_driver_covers(words))]


#: THE FOUR FORMS the first derivation walked straight past, each measured by an
#: adversary to leave the contract green while `lanes.py` grew a word. Every one
#: is planted as the LAST line of a temp copy, so its line number is known.
_UNRECOGNISED_FORMS: Final = {
    "setdefault": "def _x(a):\n    a.setdefault('refused', 'lane_orphaned')\n",
    "dict-of-pairs": "def _y():\n    return dict([('refused', 'lane_gone')])\n",
    "update-of-pairs": "def _z(a):\n    a.update([('refused', 'lane_away')])\n",
    "aliased-key": "K = 'refused'\n\n\ndef _k():\n    return {K: 'lane_keyed'}\n",
    # THE SECOND ADVERSARY PASS: keys that are not literals, with a one-word
    # value that the refusal-word SHAPE alone does not catch.
    "class-attribute-key": (
        "class C:\n    KEY = 'refused'\n\n\ndef _a():\n    return {C.KEY: 'parked'}\n"
    ),
    "concatenated-key": "def _c():\n    return {'refu' + 'sed': 'parked'}\n",
    "fstring-key": "def _f():\n    k = 'sed'\n    return {f'refu{k}': 'parked'}\n",
    "computed-setdefault-key": "def _s(a, k):\n    a.setdefault(k, 'parked')\n",
    "computed-subscript-key": "def _t(a, k):\n    a[k] = 'parked'\n",
    "opaque-update": "def _u(a, other):\n    a.update(other)\n",
    "unpacked-dict": "def _v(other):\n    return {**other, 'ok': False}\n",
}


@pytest.mark.parametrize("form", sorted(_UNRECOGNISED_FORMS))
def test_cs1015_every_way_to_emit_a_refusal_word_reddens_the_contract(
    form: str, tmp_path: Path
) -> None:
    """FAIL CLOSED: a form the derivation does not recognise is a finding.

    A derivation that knows three spellings of "put a word under `refused`" is
    blind to the fourth, and a blind derivation reports that the contract holds.
    So any occurrence of the refusal KEY - as a literal or through a name bound
    to it - that no recognised emit form accounts for is itself red, as is any
    refusal-shaped literal no recognised form accounts for. The planted line is
    named, so the finding points at the code rather than at the arm.
    """
    pristine = LANES_SOURCE.read_text(encoding="utf-8")
    planted = tmp_path / "lanes.py"
    planted.write_text(pristine + "\n\n" + _UNRECOGNISED_FORMS[form], encoding="utf-8")
    text = planted.read_text(encoding="utf-8")
    applied = text.endswith(_UNRECOGNISED_FORMS[form])
    assert applied, "THE PLANT DID NOT APPLY - a green here would measure nothing"
    last_line = len(text.splitlines())

    faults = _contract_faults(text)
    assert faults, f"the {form} form left the contract GREEN"
    named = [f for f in faults if f"line {last_line}" in f or f"line {last_line - 1}" in f]
    assert named or any("uncovered" in f for f in faults), f"{form}: no fault names it: {faults}"
    # AND THE PRISTINE FLOOR IN THE SAME RUN.
    floor = _contract_faults(pristine)
    assert floor == [], f"the pristine emitter is red: {floor}"


# ===========================================================================
# CS-1016 - a REAL worktree collision, driven into run_cycle and onto disk
# ===========================================================================


def test_cs1016_a_real_worktree_collision_is_written_as_one_naming_the_occupant(
    tmp_path: Path,
) -> None:
    """Two lanes, ONE worktree, REAL locks, and the row that reaches the file.

    Every CS-1011 arm fed `run_cycle` a hand-built refusal dict, so what the
    driver makes of the dict `lanes.try_acquire_lane` ACTUALLY returns was
    never measured, and CS-1011 exists because a row once said one thing while
    the driver decided another. Here `queue-b` takes a real lock on a tree,
    `queue` asks for the same tree through the real acquire, and the bytes
    `append_record` writes must name the fault and the occupying lane. Because
    the refusal word is whatever the emitter really answers, this is also
    CS-1015 end to end: a word renamed in `lanes.py` alone lands here as
    `lane_held` and reddens the outcome assertion.

    RESOURCE LIFETIME: both locks live under `tmp_path`, the occupant's is
    released in a `finally`, and the arm proves no lock file and no ownership
    entry survives it - a leaked entry in `lanes._OWNED` would outlive the test
    in this process and bias every later arm that reads it.
    """
    root = tmp_path / "locks"
    root.mkdir()
    shared = tmp_path / "cs-lane-shared"
    shared.mkdir()
    occupant = "queue-b"
    asking = "queue"
    assert occupant in lanes.LANES
    assert asking in lanes.LANES

    held = lanes.try_acquire_lane(occupant, run_id="cs1016a", worktree=shared, root=root)
    token = held.get("token")
    try:
        assert held.get("ok") is True, "the occupant could not take its real lock"
        assert lanes.lane_state(root, None, occupant)["state"] == lanes.RUNNING

        def acquire(lane: str, **kw: Any) -> dict[str, Any]:
            return lanes.try_acquire_lane(lane, root=root, **kw)

        def release(tok: Any, **_kw: Any) -> bool:
            return lanes.release_lane(tok, root=root)

        got = _cycle(acquire, worktree=str(shared), lane=asking, release=release)
        written = _write_and_read_back(got, tmp_path / "cycles.jsonl")
    finally:
        lanes.release_lane(token, root=root)

    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    assert len(rows) == 1, "the writer did not write exactly one row"
    row = rows[0]
    # THE FAULT, as the driver's own word, read off the FILE.
    assert row["outcome"] == queue_loop.OUTCOME_WORKTREE_IN_USE, (
        f"a real collision was written as {row['outcome']!r}"
    )
    assert row["worker_ok"] is False
    # THE OCCUPYING LANE, named - and not the asking lane, which holds nothing.
    assert f"lane {occupant!r}" in row["detail"], "the written row does not name the occupant"
    assert f"lane {asking!r}" not in row["detail"], "the row names the asking lane as occupant"
    # The tree's path is on the real refusal and must not ride into the file.
    assert not _leaked(written, shared.name), "the real refusal's worktree path reached the row"

    # NOTHING LEAKS: the asking lane never got a lock, the occupant's is gone,
    # and neither lock left an ownership entry behind in this process.
    leftover = sorted(p.name for p in root.iterdir())
    assert leftover == [], f"a lock survived the arm: {leftover}"
    assert lanes.lane_state(root, None, occupant)["state"] == lanes.FREE
    assert lanes.path_key(token) not in lanes._OWNED  # noqa: SLF001 - the lifetime under test


# ===========================================================================
# CS-1017 - the consumed wait and the reason word, ON THE ROW
# ===========================================================================

#: The launcher's liveness grace, read from the launcher rather than restated.
GRACE_S: Final = float(lane_launcher._SPAWN_LIVENESS_GRACE_S)  # noqa: SLF001 - the grace under test

#: How long the early-exiting runner lives. Deliberately a clean fraction of the
#: grace, so the row's number can be compared exactly.
EARLY_EXIT_S: Final = 0.5


class _LaunchClock:
    """The launcher's monotonic clock, advanced only by the fake process."""

    def __init__(self) -> None:
        """Start at a fixed reading."""
        self.now = 100.0

    def __call__(self) -> float:
        """The current reading."""
        return self.now


def _fake_popen(clock: _LaunchClock, exits_after: float | None, spawned: list[list[str]]):
    """A `subprocess.Popen` stand-in that NEVER starts a process.

    `wait(timeout)` advances the launcher's clock by exactly what a real wait
    would have consumed: `exits_after` when the runner dies inside the grace,
    the whole timeout when it does not.
    """

    class FakeProc:
        pid = 4242

        def __init__(self, argv: list[str], **_kw: Any) -> None:
            spawned.append(list(argv))

        def wait(self, timeout: float | None = None) -> int:
            limit = float(timeout or 0.0)
            if exits_after is not None and exits_after < limit:
                clock.now += exits_after
                return 1
            clock.now += limit
            raise subprocess.TimeoutExpired("runner", limit)

    return FakeProc


def _launch_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    exits_after: float | None,
    repoint: bool,
) -> dict[str, Any]:
    """Drive ONE cycle through the REAL `launch_lane` and `_spawn`, then the writer.

    Only what would touch the world is faked: the process, the worktree, the
    tool lookup, the lock re-point, the kill. The measurement, the refusal and
    the row are the real code.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    clock = _LaunchClock()
    spawned: list[list[str]] = []
    killed: list[Any] = []
    tree = tmp_path / "cs-lane-queue"
    tree.mkdir(exist_ok=True)
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"# synthetic\n")
    monkeypatch.setattr(lane_launcher.subprocess, "Popen", _fake_popen(clock, exits_after, spawned))
    # NOT raising at base, where the attribute does not exist yet: the arm must
    # fail on the missing FIELD, not on its own set-up.
    monkeypatch.setattr(lane_launcher, "_monotonic", clock, raising=False)
    monkeypatch.setattr(lane_launcher, "resolve_tool", lambda _name: "synthetic-shell")
    monkeypatch.setattr(lane_launcher, "command_path", lambda _lane, **_kw: prompt)
    monkeypatch.setattr(lane_launcher, "ensure_worktree", lambda _lane, **_kw: tree)
    monkeypatch.setattr(lane_launcher, "_refuse_main_tree", lambda *_a: None)
    monkeypatch.setattr(lane_launcher, "_kill", killed.append)
    monkeypatch.setattr(lane_launcher.lanes, "repoint_lane_pid", lambda *_a, **_k: repoint)
    monkeypatch.setattr(lane_launcher.lanes, "release_lane", lambda *_a, **_k: True)

    def launch(lane: str, **kw: Any) -> dict[str, Any]:
        return lane_launcher.launch_lane(lane, log_dir=tmp_path / "logs", **kw)

    got = _cycle(lambda _lane, **_kw: {"ok": True, "token": "T"}, launch=launch)
    written = _write_and_read_back(got, tmp_path / "cycles.jsonl")
    assert len(spawned) == 1, "the fake process was not the one spawned"
    rows = [json.loads(line) for line in written.splitlines() if line.strip()]
    assert len(rows) == 1
    row: dict[str, Any] = rows[0]
    row["_killed"] = len(killed)
    return row


def test_cs1017_an_early_exit_and_a_post_grace_kill_are_one_field_apart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The 2026-09-11 diagnosis had to INVENT a duration argument, and it was wrong.

    `duration_s` is the driver's cycle clock; the 2.0s grace runs from the
    `Popen`. A runner that died at 1.97s and a runner killed after a refused
    re-point after the full grace both came out as `launch_failed` with a
    duration a little over two seconds. The row now carries the seconds
    `proc.wait` actually consumed and the reason word, so the two are told apart
    by READING a field, not by subtracting clocks that do not share an origin.
    """
    early = _launch_row(tmp_path / "early", monkeypatch, exits_after=EARLY_EXIT_S, repoint=True)
    killed = _launch_row(tmp_path / "killed", monkeypatch, exits_after=None, repoint=False)

    # THE CONTROL: the two really are the two cases, and the row as it stood
    # could not tell them apart - same outcome, same kind of detail.
    outcomes = (early["outcome"], killed["outcome"])
    kills = (early["_killed"], killed["_killed"])
    assert outcomes == (queue_loop.OUTCOME_LAUNCH_FAILED,) * 2, f"outcomes {outcomes}"
    assert kills == (0, 1), f"the kill path was not the one driven: {kills}"

    # THE CONSUMED WAIT, one field, and it alone separates them.
    # BOUND TO SCALARS: a row carries a temp path, and pytest renders an
    # asserted dict whole whatever message the assertion carries.
    early_waited = early.get("launch_waited_s")
    killed_waited = killed.get("launch_waited_s")
    assert early_waited == EARLY_EXIT_S, f"early exit waited {early_waited}"
    assert killed_waited == GRACE_S, f"post-grace kill waited {killed_waited}"
    # AND THE REASON WORD, as its own field rather than a suffix inside detail.
    early_reason = early.get("launch_reason")
    killed_reason = killed.get("launch_reason")
    assert early_reason == "runner_exited_early", f"early exit reason {early_reason}"
    assert killed_reason == "repoint_refused", f"post-grace kill reason {killed_reason}"


def test_cs1017_a_launched_worker_s_row_carries_both_fields_as_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ON EVERY ROW, so a reader never has to ask whether the field exists.

    A worker that survived its grace is not a refusal, so it has no reason word
    and the launcher reports no wait for it - `launch_lane`'s return key set is
    pinned by `tests/test_lane_launcher.py`. Both fields are PRESENT and None,
    which is distinguishable from a row written before this item, where they
    were absent.
    """
    row = _launch_row(tmp_path, monkeypatch, exits_after=None, repoint=True)
    outcome = row["outcome"]
    present = ("launch_reason" in row, "launch_waited_s" in row)
    values = (row.get("launch_reason"), row.get("launch_waited_s"))
    assert outcome == queue_loop.OUTCOME_COMPLETED, f"outcome {outcome}"
    assert present == (True, True), f"a launched row omits a field: {present}"
    assert values == (None, None), f"a launched row carries {values}"


@pytest.mark.parametrize(
    "waited", [float("nan"), float("inf"), -1.0, True, "2.0", 10**9, None, object()]
)
def test_cs1017_a_wait_the_driver_cannot_vouch_for_is_written_as_none(waited: object) -> None:
    """The number comes from another module and lands in a durable row.

    Only a finite, non-negative real inside the ceiling is written; anything
    else - a string, a bool, a NaN, an absurd value - is None, never rendered.
    """
    assert queue_loop._launch_waited(waited) is None  # noqa: SLF001 - the validator
