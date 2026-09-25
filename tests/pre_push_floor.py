"""CS-824 - the ONE helper that gives a sandbox pre-push copy a test-local floor.

WHY THIS EXISTS. ``.githooks/pre-push`` refuses a green run that passed fewer
tests than one literal floor, and the floor is never read from the environment
or config. Sandbox arms whose subject is something else - a ref race, the
interpreter ladder, a probe bound - push one-test trees, and the shipped floor
would refuse every one of them for a reason unrelated to what they grade.

THE RULING, recorded in ``docs/LEDGER.md`` under "CS-824 - GRANT CLARIFICATION".
A sandbox copy of pre-push may differ from the tracked hook on the floor line
ONLY, rewritten to a test-local value. Every other byte stays identical, and the
identity arms assert exactly that relation. The pre-commit and commit-msg copies
stay wholly byte-identical, so :func:`wired_hook_bytes` returns them unchanged.

THE SHIPPED FLOOR IS NOT GRADED THROUGH THIS MODULE. The boundary arms in
``tests/test_pre_push_suite_floor.py`` push through an UNSUBSTITUTED copy and read
the constant with :func:`shipped_floor`.

THIS MODULE NEVER WRITES A FILE. Callers write the returned bytes into their own
sandbox under ``tmp_path``; nothing here can reach ``.githooks/``.
"""

from __future__ import annotations

import re
from typing import Final

PRE_PUSH: Final = "pre-push"

#: The whole-line shape of the floor declaration, ruled fixed. A line that
#: merely mentions the name - a comment, a comparison - does not match.
FLOOR_LINE: Final = re.compile(rb"CS_PASS_FLOOR=[0-9]+")

#: The value a sandbox copy carries. One passing test clears it, which is every
#: sandbox tree the non-floor arms build.
TEST_FLOOR: Final = 1


class FloorLineError(ValueError):
    """The tracked hook does not carry exactly one floor line."""


def _floor_index(lines: list[bytes]) -> int:
    """The index of the single floor line, or raise."""
    found = [index for index, line in enumerate(lines) if FLOOR_LINE.fullmatch(line)]
    if len(found) != 1:
        raise FloorLineError(f"expected exactly one floor line, found {len(found)}")
    return found[0]


def shipped_floor(raw: bytes) -> int:
    """The floor the tracked hook ships, read from its one floor line."""
    lines = raw.split(b"\n")
    return int(lines[_floor_index(lines)].split(b"=", 1)[1])


def with_test_floor(raw: bytes, floor: int = TEST_FLOOR) -> bytes:
    """``raw`` with its one floor line rewritten to ``floor`` and nothing else touched.

    Raises unless exactly one floor line exists, and asserts the result differs
    from the input on exactly that line - so a substitution that never applied,
    or one that also moved another byte, cannot pass as a floor copy.
    """
    lines = raw.split(b"\n")
    index = _floor_index(lines)
    rewritten = list(lines)
    rewritten[index] = b"CS_PASS_FLOOR=" + str(floor).encode("ascii")
    result = b"\n".join(rewritten)
    if not differs_only_on_floor_line(result, raw):
        raise FloorLineError("the floor substitution did not change exactly the floor line")
    return result


def differs_only_on_floor_line(copy: bytes, tracked: bytes) -> bool:
    """Whether ``copy`` equals ``tracked`` everywhere except its one floor line.

    False when they are byte-identical too: an identity arm that accepted an
    unsubstituted copy would be grading a copy that refuses every one-test push.
    """
    left = copy.split(b"\n")
    right = tracked.split(b"\n")
    if len(left) != len(right):
        return False
    changed = [index for index, (a, b) in enumerate(zip(left, right, strict=True)) if a != b]
    if len(changed) != 1:
        return False
    try:
        return changed[0] == _floor_index(right) == _floor_index(left)
    except FloorLineError:
        return False


def wired_hook_bytes(hook: str, raw: bytes) -> bytes:
    """What a sandbox installs for ``hook``: pre-push gets the test floor, others are verbatim."""
    return with_test_floor(raw) if hook == PRE_PUSH else raw
