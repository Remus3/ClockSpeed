"""CS-1290 - the ONE helper that readies a hook sandbox for the kit v13 wiring.

WHY THIS EXISTS. Under the CS-1290 frozen-file grant ``.githooks/pre-push`` now
runs the kit's identity check first and its whole suite inside the kit's suite
gate, and ``.githooks/commit-msg`` ends with the kit's trailer strip. A sandbox
that drives the real hook bytes therefore needs three things the tracked tree
has and a throwaway repository does not:

1. The kit files those lines run, at ``ops/fleet_kit/`` in the sandbox work
   tree - the identity line names a path relative to the hook's working
   directory, and the gate loads its two sibling files beside itself.
2. A LOCAL ``fleet.operatorIdent`` naming the sandbox's own synthetic committer,
   or the identity check refuses every push (no value set = refuse).
3. ``FLEET_SUITE_DIR`` aimed under the arm's own ``tmp_path``, so a sandbox suite
   never takes one of this machine's real slots - the suite that runs THESE
   tests already holds one, and a second arm queued behind it would wait out the
   gate's timeout.

Grant condition C.3 (``docs/LEDGER.md``, 2026-10-09 CS-1290): no assertion is
weakened by any of this. The hook bytes the sandboxes install stay the tracked
bytes, floor line apart (``tests/pre_push_floor.py``).

CS-1349, THE COMMIT MARGIN. The gate admits a run only while free commit covers
the run's history-derived requirement PLUS a margin, and a fresh slot directory
holds no history, so every sandbox push would ask for the kit's default
requirement and its default margin together. Every sandbox that drives a real
push sets the margin to 0 in its own environment through :func:`commit_margin_env`.
The variable is NAMED by reading the kit's own ``ENV_COMMIT_MARGIN`` constant,
never restated here, and its value is never rendered (CLAUDE.md non-negotiable
13). Grant clause C, ``docs/LEDGER.md``, 2026-10-23 CS-1349.

THIS MODULE NEVER WRITES OUTSIDE THE DIRECTORY IT IS HANDED.
"""

from __future__ import annotations

import ast
import shutil
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
KIT_DIR: Final = REPO_ROOT / "ops" / "fleet_kit"

#: The kit files the wired hook lines reach: the identity check, the suite gate
#: and the two siblings the gate and the lock load by path.
HOOK_KIT_FILES: Final = (
    "fleet_identity.py",
    "fleet_suite_gate.py",
    "fleet_claims.py",
    "fleet_gitlock.py",
)

#: The LOCAL git config key the identity check reads its operator set from.
OPERATOR_IDENT_KEY: Final = "fleet.operatorIdent"

#: The variable the suite gate reads its slot directory from.
SUITE_DIR_ENV: Final = "FLEET_SUITE_DIR"


def install_hook_kit(work: Path) -> Path:
    """Copy the hook-reached kit files into ``work/ops/fleet_kit`` and return it."""
    target = work / "ops" / "fleet_kit"
    target.mkdir(parents=True, exist_ok=True)
    for name in HOOK_KIT_FILES:
        shutil.copy2(KIT_DIR / name, target / name)
    return target


#: The kit file whose module-level string constants this module reads by name.
SUITE_GATE_FILE: Final = KIT_DIR / "fleet_suite_gate.py"

#: The margin every sandbox push asks the gate for.
SANDBOX_COMMIT_MARGIN: Final = 0


class KitConstantError(LookupError):
    """The kit file does not assign the named constant exactly once, to a string."""


def kit_constant(name: str) -> str:
    """The string the suite gate's source assigns to ``name`` at module level.

    Read from the source's syntax tree, never by importing the kit, so asking for
    a name runs none of the kit's own code. Raises unless exactly one top-level
    assignment binds ``name`` to a plain string literal.
    """
    tree = ast.parse(SUITE_GATE_FILE.read_text(encoding="ascii"))
    values = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and [getattr(target, "id", None) for target in node.targets] == [name]
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        raise KitConstantError(f"{name}: {len(values)} string assignment(s) in the suite gate")
    return values[0]


#: The variable the suite gate reads its commit margin from, named by the kit.
COMMIT_MARGIN_ENV: Final = kit_constant("ENV_COMMIT_MARGIN")

#: The file the gate appends one record per run to, inside its slot directory.
DURATIONS_FILE: Final = kit_constant("DURATIONS")


def suite_dir_env(tmp_path: Path) -> dict[str, str]:
    """The gate's slot directory, under the arm's own temporary directory."""
    return {SUITE_DIR_ENV: str(tmp_path / "fleet-suite-gate")}


def commit_margin_env() -> dict[str, str]:
    """The gate's commit margin, set to 0 for a sandbox push (CS-1349)."""
    return {COMMIT_MARGIN_ENV: str(SANDBOX_COMMIT_MARGIN)}
