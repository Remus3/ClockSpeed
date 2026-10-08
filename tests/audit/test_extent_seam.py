"""CS-1266: no audit module reads a record's payload extent.

``ObjectRecord.body_offset`` and ``body_length`` are positions the save layer
reads and publishes to nobody - ``clockspeed/save/world.py`` states the rule,
because a buffer position handed upward is the reach past a neighbour the seam
discipline forbids. The one fact a consumer needs from them, whether the walk
paired a record with any payload, crosses as
``clockspeed.save.world.RecordProperties.payload_present``.

Graded over the SOURCE of every module in ``clockspeed/audit``: an attribute
access or a string constant naming either field is a read. The detector is
shown to fire on a planted control per form before its silence is believed.

A module of its own, apart from the model suites, because it reads source files
and asserts over file names only - it holds no model, so no withheld field can
sit in a frame or an assertion here.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

#: The shipped audit package, read as source.
AUDIT_ROOT: Final = Path(__file__).resolve().parents[2] / "clockspeed" / "audit"

#: The two record fields no audit module may read.
EXTENT_FIELDS: Final = frozenset({"body_offset", "body_length"})


def extent_reads(tree: ast.AST) -> int:
    """Count the reads of a record extent in one module: attribute or string.

    Args:
        tree: The parsed module.

    Returns:
        How many attribute accesses or string constants name an extent field.
    """
    return sum(
        1
        for node in ast.walk(tree)
        if (isinstance(node, ast.Attribute) and node.attr in EXTENT_FIELDS)
        or (isinstance(node, ast.Constant) and node.value in EXTENT_FIELDS)
    )


def test_the_extent_read_detector_fires_on_each_planted_form() -> None:
    planted = (
        "record.body_length > 0",
        "model.objects.records[0].body_offset",
        "getattr(record, 'body_length')",
    )
    for source in planted:
        hits = extent_reads(ast.parse(source))
        assert hits == 1, source


def test_no_audit_module_reads_a_record_extent() -> None:
    modules = sorted(AUDIT_ROOT.glob("*.py"))
    count = len(modules)
    assert count > 0
    readers = sorted(
        path.name for path in modules if extent_reads(ast.parse(path.read_bytes().decode("ascii")))
    )
    assert readers == []
