"""CS-1166 - the pytest temp-directory retention settings, pinned.

WHY AN ARM RATHER THAN A COMMENT. The numbered pytest run root is per-Windows-
account and NOT per-repository: several trees on this machine write into the
same directory, and nothing about its location attributes a byte of it to this
project. Measured when this module was filed, by matching the tmp_path leaf
names against this suite's own test-function names, 165,093 of 268,401 files
under that shared root carried Clockspeed test names. A single targeted run of
tests/test_doc_budget.py left 440 files and 339 directories behind at pytest's
default retention; with the two keys below in force the same run left 84 files
and 5,448 bytes. Those two keys are the whole of that difference, so a silent
edit to either one silently restores the growth.

WHAT EACH ARM HAS TEETH AGAINST, stated because the two keys are NOT symmetric:

  tmp_path_retention_policy  pytest's default is "all". An arm that reads the
      value in force therefore has real teeth on this key - "failed" cannot be
      produced by leaving the setting out.

  tmp_path_retention_count   pytest's default is 3 and this project deliberately
      KEEPS 3 (see the comment in pyproject.toml: the root is shared, and a
      smaller count only widens how much of other trees' evidence this suite
      deletes on its way past). So a value-in-force arm on this key would be
      satisfied by the setting's own absence, which is a vacuous arm. Its teeth
      come from test_the_retention_keys_are_declared_in_pyproject below, which
      reads the FILE - deleting the key turns that arm red even though the
      effective value never moves.

The pair is deliberate. One arm proves the file declares the setting; the other
proves nothing outranks the file. tests/test_mypy_gate.py records the same trap
for [tool.mypy]: a competing configuration file dropped beside pyproject.toml
demotes the table to decoration while every arm that reads it goes on describing
it. pytest has the same precedence ladder - pytest.ini, then pyproject.toml,
then tox.ini, then setup.cfg - so reading the file alone is not enough, and
reading the value in force alone cannot see a deleted key.
"""

import tomllib
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The values this project has chosen. Both are restated here ON PURPOSE and it
# is not a drift risk in the sense CLAUDE.md section 4 warns about: this module
# IS the machine-checked owner of the claim that pyproject.toml carries these
# two values, so a literal here that disagrees with the file turns an arm red
# rather than sitting in prose going stale.
EXPECTED_POLICY = "failed"
EXPECTED_COUNT = 3


def _pytest_ini_table() -> dict[str, Any]:
    """Return the [tool.pytest.ini_options] table from pyproject.toml.

    Returns:
        The parsed table.
    """
    parsed = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    table: dict[str, Any] = parsed["tool"]["pytest"]["ini_options"]
    return table


def test_the_retention_keys_are_declared_in_pyproject() -> None:
    table = _pytest_ini_table()

    policy = table.get("tmp_path_retention_policy")
    assert policy == EXPECTED_POLICY, (
        "pyproject.toml's [tool.pytest.ini_options] must declare "
        f"tmp_path_retention_policy = {EXPECTED_POLICY!r}; it declares {policy!r}. "
        "Without it pytest keeps the tmp_path of every PASSING test, which is "
        "this project's entire measured contribution to the shared pytest temp "
        "root. If the policy is being changed deliberately, change the constant "
        "in this module and record why in the pyproject.toml comment."
    )

    count = table.get("tmp_path_retention_count")
    assert count == EXPECTED_COUNT, (
        "pyproject.toml's [tool.pytest.ini_options] must declare "
        f"tmp_path_retention_count = {EXPECTED_COUNT}; it declares {count!r}. "
        "This arm is the only one with teeth on this key, because pytest's own "
        "default is the same number - a value-in-force check cannot tell the "
        "setting from its absence. The number is held at the default on purpose: "
        "the numbered run root is shared between trees and pytest's cleanup "
        "cannot tell whose run dir it is deleting, so a smaller count destroys "
        "other projects' evidence without shrinking this one's footprint."
    )


def test_the_retention_values_are_the_ones_actually_in_force(
    pytestconfig: pytest.Config,
) -> None:
    # Compared against the module constants rather than against the parsed
    # file, DELIBERATELY. Reading the file here and indexing the key would
    # raise a bare KeyError the moment the key is deleted - measured on the
    # first run of this module - which destroys this arm's own message and
    # duplicates the arm above. Arm one owns "the file declares it"; this arm
    # owns "nothing outranks the file", and it must render its own reason in
    # every failing case including the deleted one.
    in_force_policy = pytestconfig.getini("tmp_path_retention_policy")
    assert in_force_policy == EXPECTED_POLICY, (
        f"tmp_path_retention_policy in force for THIS run is {in_force_policy!r}, not the "
        f"chosen {EXPECTED_POLICY!r}. pytest reads pytest.ini, then pyproject.toml, then "
        "tox.ini, then setup.cfg, and the first file carrying a pytest section wins outright - "
        "so a competing configuration file dropped beside pyproject.toml demotes the whole "
        "[tool.pytest.ini_options] table to decoration while the arm above goes on describing "
        "it. Delete the competing file, or move the configuration into it."
    )

    # getini returns this key as a STRING even though pyproject declares it as
    # an integer - pytest's own ini type for it is "string", so `3` comes back
    # as `'3'`. Comparing the raw value against an int is a guaranteed red that
    # says nothing about retention, which is what the first run of this module
    # measured. Normalise BOTH sides through int() so the arm grades the VALUE
    # in force rather than the type pytest happened to hand back.
    in_force_count = int(str(pytestconfig.getini("tmp_path_retention_count")).strip())
    assert in_force_count == EXPECTED_COUNT, (
        f"tmp_path_retention_count in force for THIS run is {in_force_count!r}, not the chosen "
        f"{EXPECTED_COUNT}. See the precedence note above - the same shadowing explains both "
        "keys at once. Note this arm alone cannot see the key DELETED, because pytest's own "
        "default is the same number; that case belongs to "
        "test_the_retention_keys_are_declared_in_pyproject."
    )


def test_the_chosen_policy_is_not_pytests_own_default() -> None:
    """Anti-vacuity control for the policy arm.

    A pin whose expected value equals the tool's default passes whether or not
    the setting exists, which is the failure this module documents for
    tmp_path_retention_count. This arm asserts the POLICY constant is not in
    that position, so the value-in-force arm above is known to have teeth
    rather than assumed to.
    """
    assert EXPECTED_POLICY != "all", (
        "EXPECTED_POLICY has been set to pytest's own default, which makes "
        "test_the_retention_values_are_the_ones_actually_in_force vacuous - it "
        "would pass with the setting deleted. Either choose a non-default policy "
        "or delete that arm rather than leaving it green and empty."
    )
    assert EXPECTED_POLICY in {"failed", "none"}, (
        f"EXPECTED_POLICY is {EXPECTED_POLICY!r}, which pytest does not accept. "
        "The accepted values are all, failed and none."
    )
