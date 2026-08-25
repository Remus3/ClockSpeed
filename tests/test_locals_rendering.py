"""CS-851 - the locals channel, graded on what pytest ACTUALLY PRINTS under ``-l``.

WHAT IS ASSERTED HERE AND WHAT IS NOT. The subject is the frame's LOCALS at the
moment a shipped assertion fails, which ``tests/locals_rendering_guard.py``
derives statically, and which the forced arms below measure for real by running
pytest in a subprocess and grepping the rendered failure report for a token
planted for that purpose. The ASSERTED EXPRESSION belongs to CS-850 and the
failing function's own SOURCE LINES belong to nobody yet; both are named as
uncovered rather than left to read as covered.

THE ARMS DO NOT DERIVE FROM THE FINDINGS, and that is not a style preference.
Three items were refuted in one session for proofs whose forced cases came from
the live population, so REPAIRING A LEAK TURNED THE PROOF RED and a green run
certified that the tree still leaked. Every forced arm below is generated from
:data:`FOLLOWED_FORMS` - the binding shapes the scan CLAIMS to cover - and from
synthetic holders authored in this file. Not one of them reads
:func:`scan_tree`. ``test_the_sweep_is_green_on_a_corpus_with_no_such_binding``
proves the green-on-a-clean-tree property directly, on a corpus that uses every
covered form in the remedied shape.

THE COST IS REPORTED RATHER THAN ENGINEERED AWAY. The live residual is recorded
PER SITE - module, scope and local name - with a reason read from the
declaration it holds. A finding whose key is not in the record is red, so a new
leaky binding in an already-recorded file is red AND SO IS A REPLACEMENT: the
per-module CEILING this record replaced could not tell "still the same eight
sites" from "eight different ones", and eight repairs plus eight brand-new leaky
bindings under brand-new names passed it.

THE RECORD ASSERTS ONE WAY AND REPORTS THE OTHER, deliberately. A recorded key
that no longer names a live finding is a repaired site, and
``test_a_repaired_residual_is_reported_rather_than_reddening`` warns with the
exact line to delete rather than failing. Failing there would need the live
population to still hold every recorded site, which is the anti-monotone shape
that refuted three items in one session: repairing a leak turned the proof red,
and a green run certified the tree still leaked. The MECHANISM is graded hard,
on synthetic findings built from the record's own keys, by
``test_a_repaired_site_is_reported_as_stale_rather_than_reddening``.

NO ARM HERE REQUIRES THE LIVE POPULATION TO BE NON-EMPTY. Every forced case is
generated from :data:`FOLLOWED_FORMS`, from :data:`RECORDED_FORMS`, from the
record's declared keys or from sources authored in this file. Repairing every
live finding in the repository leaves every arm green.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from tests.assertion_rendering_guard import _parent_map, _reaches_unmasked, scan_source
from tests.locals_rendering_guard import (
    ANNOTATED,
    ASSIGN,
    CHAINED,
    FOLLOWED_FORMS,
    FOR_TARGET,
    KNOWN_FORMS,
    RECORDED_FORMS,
    UNPACK,
    WALRUS,
    WITH_TARGET,
    LocalFinding,
    LocalSweep,
    describe_locals,
    describe_residual_keys,
    flows_into,
    residual_key,
    scan_source_locals,
    scan_sources,
    scan_tree,
    shipped_binding_forms,
    stale_residuals,
    unrecorded_residuals,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT: Final = 300

#: pytest's exit code when tests ran and at least one of them failed.
PYTEST_TESTS_FAILED: Final = 1

#: A synthetic save-derived name: the class a world name, a save name, a session
#: name or a decoded struct word belongs to. NOTHING on this machine is spelled
#: like this, and nothing that is may be written into a tracked file. The three
#: below are flagged by bandit as hardcoded secrets, which is the rule firing on
#: the right SHAPE for the wrong reason: they are the markers a leak is grepped
#: for, and a marker absent from the source is one the grep cannot look for.
#: They are spelled differently from CS-850's so a grep for one cannot be
#: satisfied by the other module's sandbox.
SAVE_NAME_TOKEN: Final = "Cs851SyntheticSaveName"  # noqa: S105

#: A synthetic home path. The drive letter and the account name are invented;
#: the SHAPE is what leaks. ASSEMBLED FROM FRAGMENTS ON PURPOSE:
#: ``tests/test_scaffold.py`` greps every authored file's BYTES for a contiguous
#: drive-Users-account run and cannot tell an invented account name from a real
#: one, which is the correct conservative behaviour and must not be loosened for
#: this file. Splitting the literal leaves the runtime VALUE identical, which is
#: the only half the sandbox and the grep below read.
HOME_PATH_TOKEN: Final = "Q:/" + "Users" + "/cs851synthetic/AppData/Local"

#: A synthetic platform account directory - the numeric subdirectory under the
#: save root, which CLAUDE.md section 2 names as personal data outright.
ACCOUNT_DIR_TOKEN: Final = "90000000000000851"  # noqa: S105

#: The three classes the acceptance names, in the order it names them.
SENSITIVE_TOKENS: Final = (SAVE_NAME_TOKEN, HOME_PATH_TOKEN, ACCOUNT_DIR_TOKEN)

#: The reason one accepted residual is accepted, by the DECLARATION it reads -
#: the holder class and the withheld field - rather than per site. Two sites
#: holding ``Checkout.home`` are accepted for the same reason and must not
#: drift into two spellings of it; a fourth site holding a field nothing here
#: names has no reason at all, and :data:`LIVE_LOCALS_RESIDUALS` cannot be
#: written for it without one.
#:
#: THE SPLIT IS THE HONEST SEVERITY. ``tests/conftest.py``'s report hook
#: rewrites home paths and the account name in a rendered failure - its own
#: docstring names the locals under ``-l`` as a channel it reaches - so a local
#: holding a sandbox path is a static finding whose RENDERING is already
#: redacted. Nothing on this machine can enumerate the words a save contains,
#: so a save-derived string passes straight through that hook, and the
#: save-package entries are the class this guard exists for.
RESIDUAL_REASONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "PropertyMap.schemas": (
            "usmap-derived schema keys; game data rather than personal data, and outside "
            "the runtime redactor's reach"
        ),
        "PropertyMap.warnings": (
            "usmap-derived warning details; game data rather than personal data, and "
            "outside the runtime redactor's reach"
        ),
        "WorldModel.token": (
            "a real world token off a real save; nothing can enumerate a save-derived "
            "string, so tests/conftest.py cannot reach it"
        ),
        "WorldModel.warnings": (
            "a warning-code projection off a real world model; outside the runtime "
            "redactor's reach for the same reason"
        ),
        "Sandbox.work": (
            "a sandbox path derived from tmp_path; the rendered value is a home path, "
            "which tests/conftest.py rewrites at render time"
        ),
        "Sandbox.hooks": (
            "a sandbox hooks path derived from tmp_path; rewritten at render time by "
            "tests/conftest.py"
        ),
        "Checkout.home": (
            "a synthetic-home sandbox path derived from tmp_path; rewritten at render "
            "time by tests/conftest.py"
        ),
        "Checkout.root": (
            "a sandbox checkout root derived from tmp_path; rewritten at render time by "
            "tests/conftest.py"
        ),
        "Environment.variables": (
            "an environment-variable NAME projection off a sandbox environment; the "
            "paths in it are rewritten at render time"
        ),
    }
)

#: The live findings this guard was built alongside, one entry per SITE, keyed
#: by module, scope and local name. A finding whose key is absent is RED.
#:
#: KEYED BY IDENTITY RATHER THAN BY COUNT, and the difference is a measured
#: escape rather than a preference. The record this replaced held a per-module
#: CEILING, which is met just as well by eight replacements as by the eight
#: sites it was written for: repair all eight, plant eight brand-new leaky
#: bindings under brand-new names at brand-new lines, and the ceiling passes.
#: A key moves only when the site moves.
#:
#: ASSERTED ONE WAY AND REPORTED THE OTHER. An unrecorded finding is red;
#: a recorded key nothing finds any more is a stale entry, reported by
#: ``test_a_repaired_residual_is_reported_rather_than_reddening`` with the exact
#: line to delete. Reddening on THAT direction would mean repairing a site
#: breaks this module, which is the anti-monotone shape the fence forbids.
LIVE_LOCALS_RESIDUALS: Final[Mapping[tuple[str, str, str], str]] = MappingProxyType(
    {
        ("tests/save/test_usmap.py", "_assert_nothing_was_substituted", "schema"): (
            RESIDUAL_REASONS["PropertyMap.schemas"]
        ),
        ("tests/save/test_usmap.py", "_detail_for", "matching"): (
            RESIDUAL_REASONS["PropertyMap.warnings"]
        ),
        ("tests/test_commit_msg_gate.py", "attempt", "handle"): (RESIDUAL_REASONS["Sandbox.work"]),
        ("tests/test_commit_msg_gate.py", "attempt", "tracked"): (RESIDUAL_REASONS["Sandbox.work"]),
        (
            "tests/test_commit_msg_gate.py",
            "test_the_wired_hook_is_a_byte_identical_copy_of_the_tracked_hook",
            "copied",
        ): RESIDUAL_REASONS["Sandbox.hooks"],
        ("tests/test_facts_probe.py", "assert_no_home_segment", "candidates"): (
            RESIDUAL_REASONS["Checkout.home"]
        ),
        ("tests/test_facts_probe.py", "assert_no_home_segment", "leaked"): (
            RESIDUAL_REASONS["Checkout.home"]
        ),
        (
            "tests/test_facts_probe.py",
            "test_a_hooks_path_inside_the_checkout_relativises_without_needing_the_redactor",
            "hooks_dir",
        ): RESIDUAL_REASONS["Checkout.root"],
        (
            "tests/test_facts_probe.py",
            "test_default_hooks_path_inside_the_checkout_carries_no_home_path",
            "hooks_dir",
        ): RESIDUAL_REASONS["Checkout.root"],
        (
            "tests/test_facts_probe.py",
            "test_default_hooks_path_outside_the_checkout_is_redacted_but_still_readable",
            "shared_hooks",
        ): RESIDUAL_REASONS["Checkout.home"],
        (
            "tests/test_facts_probe.py",
            "test_git_facts_are_withheld_rather_than_leaked_when_the_redactor_is_missing",
            "shared_hooks",
        ): RESIDUAL_REASONS["Checkout.home"],
        (
            "tests/test_facts_probe.py",
            "test_the_printed_default_line_carries_no_home_segment_from_the_git_facts",
            "hooks_dir",
        ): RESIDUAL_REASONS["Checkout.root"],
        (
            "tests/test_facts_probe.py",
            "test_unredacted_git_facts_emit_the_raw_branch_and_the_raw_hooks_path",
            "hooks_dir",
        ): RESIDUAL_REASONS["Checkout.root"],
        ("tests/test_hook_interpreter_ladder.py", "commit_and_scan", "payload"): (
            RESIDUAL_REASONS["Sandbox.work"]
        ),
        ("tests/test_hook_interpreter_ladder.py", "commit_attempt", "payload"): (
            RESIDUAL_REASONS["Sandbox.work"]
        ),
        (
            "tests/test_hook_interpreter_ladder.py",
            "test_a_chatty_candidate_cannot_flood_the_terminal",
            "shim",
        ): RESIDUAL_REASONS["Sandbox.hooks"],
        (
            "tests/test_hook_interpreter_ladder.py",
            "test_a_liar_on_every_ladder_rung_exhausts_the_ladder_rather_than_passing",
            "shadow",
        ): RESIDUAL_REASONS["Sandbox.hooks"],
        (
            "tests/test_hook_interpreter_ladder.py",
            "test_a_liar_on_the_path_is_refused_with_no_environment_variable_set",
            "shadow",
        ): RESIDUAL_REASONS["Sandbox.hooks"],
        (
            "tests/test_hook_interpreter_ladder.py",
            "test_the_environment_carrier_withholds_its_contents",
            "leaked",
        ): RESIDUAL_REASONS["Environment.variables"],
        (
            "tests/test_hook_interpreter_ladder.py",
            "test_the_wired_hook_is_a_byte_identical_copy_of_the_tracked_hook",
            "copied",
        ): RESIDUAL_REASONS["Sandbox.hooks"],
    }
)


def _live(findings: Sequence[LocalFinding]) -> list[LocalFinding]:
    """The findings whose holder carries real save or machine data.

    Args:
        findings: The whole sweep.

    Returns:
        The live partition.
    """
    return [finding for finding in findings if finding.live]


def _latent(findings: Sequence[LocalFinding]) -> list[LocalFinding]:
    """The findings whose holder was built from a synthetic fixture in process.

    Args:
        findings: The whole sweep.

    Returns:
        The latent partition.
    """
    return [finding for finding in findings if not finding.live]


# ---------------------------------------------------------------------------
# The generated arms. ONE PER COVERED BINDING FORM, in a leaking shape and a
# remedied one, used both as the detector's own positive corpus and as the
# source of the forced pytest runs below.
# ---------------------------------------------------------------------------

#: Leaking body then remedied body, per followed binding form. THE REMEDY ON
#: THIS CHANNEL IS NOT CS-850's. Binding the aggregate to a scalar first leaves
#: the aggregate's own local in the frame; the fix is to NOT BIND IT AT ALL, and
#: the two live sites closed on main in session 39 were closed exactly that way
#: rather than with ``del``, because the name is live until the ``del`` runs.
_ARM_BODIES: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        ASSIGN: (
            "    words = item.words\n    count = len(words)\n",
            "    count = len(item.words)\n",
        ),
        ANNOTATED: (
            "    words: frozenset = item.words\n    count = len(words)\n",
            "    count: int = len(item.words)\n",
        ),
        CHAINED: (
            "    first = second = item.words\n    count = len(first) + len(second)\n",
            "    count = 2 * len(item.words)\n",
        ),
        UNPACK: (
            "    words, spare = item.words, None\n"
            "    count = len(words) + (0 if spare is None else 1)\n",
            "    count, spare = len(item.words), None\n",
        ),
        WALRUS: (
            "    count = len(words := item.words)\n",
            "    count = len(item.words)\n",
        ),
        FOR_TARGET: (
            "    count = 0\n    for words in (item.words,):\n        count += len(words)\n",
            "    count = 0\n    for size in (len(item.words),):\n        count += size\n",
        ),
        WITH_TARGET: (
            "    with item.words.opened() as words:\n        count = len(words)\n",
            "    with nullcontext(len(item.words)) as count:\n        pass\n",
        ),
    }
)


def arm_specs() -> list[tuple[str, str]]:
    """One forced arm per COVERED binding form, with a sensitive token planted.

    DERIVED FROM THE SHAPES THIS SCAN CLAIMS TO COVER, NEVER FROM THE FINDINGS.
    Nothing in here reads :func:`scan_tree`, so repairing every live finding in
    the repository changes not one arm. The forms do not shrink when a leak is
    repaired, which is exactly the stability the acceptance's last clause asks
    for.

    Returns:
        Binding form and the token planted in that arm, sorted so the
        arm-to-token assignment is deterministic. The token cycles through the
        three classes the acceptance names so every one is exercised.
    """
    return [
        (form, SENSITIVE_TOKENS[index % len(SENSITIVE_TOKENS)])
        for index, form in enumerate(sorted(FOLLOWED_FORMS))
    ]


def _arm_source(index: int, form: str, token: str, *, remedied: bool) -> str:
    """The text of one forced arm, in the leaking form or the remedied one.

    THE TOKEN IS BOUND AT MODULE SCOPE AND NAMED IN THE BODY, never spelled
    inside the failing function. pytest prints the failing function's own SOURCE
    LINES above the assertion, so a literal in the body is rendered by the
    traceback rather than by the frame - a second channel with a second remedy,
    and grading it as if it were this one would report the fix as failing when
    it worked. Module-scope bindings are not in the rendered frame.

    Args:
        index: Distinguishes the generated names within one sandbox module.
        form: Which member of ``FOLLOWED_FORMS`` this arm exercises.
        token: The synthetic value planted inside the withheld field.
        remedied: When True, nothing binds the aggregate to a local.

    Returns:
        Python source for one class, one planted value and one failing test.

    THE ``with`` ARM IS A METHOD CALL ON THE FIELD, NOT A FACTORY TAKING IT AS
    AN ARGUMENT, and that shape is derived from the population rather than
    chosen. The tree's only live ``with``-target finding is ``with
    tracked.open(...) as handle``. A fixture written the other way - ``with
    nullcontext(item.words) as words`` - LEAKS AT RUNTIME under ``-l`` and is
    NOT flagged by this scan, because a call ARGUMENT is a barrier here. That
    gap was found by writing the arm the convenient way and watching the
    detector miss it while the forced run rendered the token anyway; it is the
    disclosed cost of ``_argument_carries`` rather than a shape the tree ships.
    """
    name = f"Holder{index}"
    planted = f"PLANTED_{index}"
    leaking, remedy = _ARM_BODIES[form]
    body = remedy if remedied else leaking
    return (
        f"class {name}:\n"
        f"    def __init__(self, value):\n"
        f"        self.words = value\n"
        f"    def __repr__(self):\n"
        f'        return f"{name}(words={{len(self.words)}})"\n'
        f"\n"
        f"{planted} = Words({{{token!r}}})\n"
        f"\n"
        f"def test_forced_arm_{index}():\n"
        f"    item = {name}({planted})\n"
        f"{body}"
        f'    assert count <= 0, f"{{count}} - counts only"\n'
    )


def sandbox_module(*, remedied: bool) -> str:
    """A whole sandbox module: one forced arm per covered binding form.

    Args:
        remedied: Whether each arm avoids binding the aggregate to a local.

    Returns:
        Python source.
    """
    parts = [
        '"""Generated by tests/test_locals_rendering.py - synthetic only."""\n\n'
        "from contextlib import nullcontext\n"
        "\n"
        "class Words(frozenset):\n"
        "    def opened(self):\n"
        "        return nullcontext(self)\n"
    ]
    parts += [
        _arm_source(index, form, token, remedied=remedied)
        for index, (form, token) in enumerate(arm_specs())
    ]
    return "\n\n".join(parts)


def _run_sandbox(root: Path, *, remedied: bool, showlocals: bool) -> tuple[int, str]:
    """Write the sandbox and run real pytest over it.

    The sandbox is isolated from this repository deliberately: no conftest, no
    rootdir here, no cache. The subject is what pytest PRINTS, and the runtime
    redactor running over the top would grade the redactor instead.

    Args:
        root: A directory to write into.
        remedied: Which form of the arms to write.
        showlocals: Whether to pass ``-l``.

    Returns:
        pytest's own exit code, and its combined output.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_forced_arms.py"
    target.write_bytes(sandbox_module(remedied=remedied).encode("ascii"))
    argv = [
        sys.executable,
        "-m",
        "pytest",
        str(target),
        "-p",
        "no:cacheprovider",
        "--rootdir",
        str(root),
    ]
    if showlocals:
        argv.append("-l")
    completed = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=str(root),
        timeout=SUBPROCESS_TIMEOUT,
    )
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    return (completed.returncode, text)


@pytest.fixture(scope="module")
def leaking_showlocals(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The arms in the shape the defect has, under ``-l`` - the CONTROL."""
    return _run_sandbox(tmp_path_factory.mktemp("cs851_leak_l"), remedied=False, showlocals=True)


@pytest.fixture(scope="module")
def leaking_default(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The same leaking arms under DEFAULT flags - the channel boundary."""
    return _run_sandbox(tmp_path_factory.mktemp("cs851_leak_d"), remedied=False, showlocals=False)


@pytest.fixture(scope="module")
def remedied_showlocals(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The arms with nothing binding the aggregate, under ``-l``."""
    return _run_sandbox(tmp_path_factory.mktemp("cs851_fixed_l"), remedied=True, showlocals=True)


# ---------------------------------------------------------------------------
# The detector is proven able to fail, before anything it says is believed
# ---------------------------------------------------------------------------

CANONICAL_SOURCE: Final = '''
"""The shape CS-850 is blind to BY CONSTRUCTION, from CS-851's own note."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def test_it(sweep: Sweep) -> None:
    unexplained = sweep.words
    count = len(unexplained)
    assert count == 0, f"{count} - counts only"
'''

SAFE_SOURCE: Final = '''
"""Every shape that must NOT be flagged, one function each."""


class Sweep:
    def __init__(self, words, saves):
        self.words = words
        self.saves = saves

    def __repr__(self):
        return f"Sweep(saves={self.saves}, words={len(self.words)})"


def make() -> Sweep:
    return Sweep(frozenset(), 0)


def reduced(sweep: Sweep) -> None:
    count = len(sweep.words)
    assert count == 0


def whole_object(sweep: Sweep) -> None:
    other = make()
    assert other == sweep


def disclosed(sweep: Sweep) -> None:
    saves = sweep.saves
    assert saves == 0


def constructed(sweep: Sweep) -> None:
    wrapper = Sweep(sweep.words, 0)
    assert wrapper is not None


def masked(sweep: Sweep) -> None:
    present = bool(sweep.words)
    assert not present
'''

ORDER_SOURCE: Final = '''
"""A binding made AFTER the assert is not in the frame when it fails."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def test_it(sweep: Sweep) -> None:
    count = len(sweep.words)
    assert count == 0
    unexplained = sweep.words
    assert unexplained is not None
'''

LOOP_SOURCE: Final = '''
"""A binding LATER in a loop body IS in the frame the second time round."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def test_it(sweep: Sweep, cases) -> None:
    for _case in cases:
        count = len(sweep.words)
        assert count == 0
        carried = sweep.words
        del carried
'''

REBIND_SOURCE: Final = '''
"""A name reused for something safe stops carrying what it held before."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def test_it(sweep: Sweep) -> None:
    held = sweep.words
    held = len(held)
    assert held == 0
'''

PROVENANCE_SOURCE: Final = '''
"""One live holder and one latent holder, so the flag is not a constant."""

from types import MappingProxyType


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def _read_the_library() -> Sweep:
    return Sweep(frozenset(open("save.sav").read().split()))


def _synthetic() -> Sweep:
    return Sweep(frozenset({"authored-here"}))


def test_from_the_library() -> None:
    sweep = _read_the_library()
    held = sweep.words
    count = len(held)
    assert count == 0


def test_from_a_fixture() -> None:
    sweep = _synthetic()
    held = sweep.words
    count = len(held)
    assert count == 0


_GRADED_LIBRARY_REACH = MappingProxyType({_read_the_library.__name__: "reads the library"})
'''

#: Where a recorded form's fixture carries its planted value. A source with no
#: mark cannot bind a withheld field AT ALL - an ``import`` target is a module
#: object and a ``def`` target is a function - so it is pinned structurally and
#: the forced run has nothing to grep for. Every other source carries one.
RECORDED_TOKEN_MARK: Final = "__CS851_RECORDED_MARK__"  # noqa: S105


def recorded_token(index: int) -> str:
    """The synthetic marker planted in one recorded form's fixture.

    NOT A PREFIX OF ANY OTHER. Two markers where one is a prefix of the other
    make a substring grep attribute form N's leak to form N-plus-ten, which is
    a false clean read on the shorter one.

    Args:
        index: The form's position in sorted order.

    Returns:
        An ASCII marker unique to that form.
    """
    return f"Cs851RecordedForm{index:02d}Mark"


def _recorded_module(body: str) -> str:
    """One recorded-form fixture: a redacting holder, a planted value, a body.

    THE PLANTED VALUE IS BOUND AT MODULE SCOPE, never spelled in the function.
    pytest prints the failing function's own SOURCE LINES above the assertion,
    so a literal in the body is rendered by the traceback rather than by the
    frame, and grading it as this channel would report a leak that is not one.

    Args:
        body: The test function, and any holder it needs.

    Returns:
        Python source for one whole sandbox module.
    """
    return (
        "class Sweep:\n"
        "    def __init__(self, words):\n"
        "        self.words = words\n"
        "    def __repr__(self):\n"
        '        return f"Sweep(words={len(self.words)})"\n'
        "\n"
        f'WORDS = frozenset({{"{RECORDED_TOKEN_MARK}"}})\n'
        "\n" + body
    )


#: One source per RECORDED form, each carrying the same withheld field in that
#: form. THESE ARE GRADED TWICE AND THE SECOND GRADE IS THE ONE THAT MATTERS:
#: ``test_the_recorded_forms_are_pinned_rather_than_silently_absent`` measures
#: the SCANNER'S SILENCE, which is true by construction wherever no scan step
#: exists, and ``test_every_recorded_form_renders_exactly_as_it_declares`` runs
#: a real ``pytest -l`` over them and grades what is PRINTED against the
#: ``renders`` field each form declares. Four of these forms LEAK; the first
#: grade alone read all ten as safe, which is the fixture trap - a fixture
#: authored beside the assumption it is meant to test.
RECORDED_SOURCES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "augmented-assign": _recorded_module(
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    total = []\n"
            "    total += sweep.words\n"
            "    count = len(total)\n"
            "    assert count == 0\n"
        ),
        "subscript-target": _recorded_module(
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    holder = {}\n"
            '    holder["w"] = sweep.words\n'
            "    count = len(holder)\n"
            "    assert count == 0\n"
        ),
        # A PLAIN ``@dataclass`` RATHER THAN A BARE CLASS, and the difference is
        # the whole finding. ``class Sink: pass`` reprs as ``<Sink object at
        # 0x...>`` and renders nothing whatever it holds, so a fixture built
        # that way pins the form SAFE by accident. A generated dataclass repr
        # prints every field - and this tree ships plain dataclasses, so that is
        # the population's shape rather than a chosen one.
        "attribute-target": _recorded_module(
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass\n"
            "class Sink:\n"
            "    words: object = None\n"
            "\n"
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    sink = Sink()\n"
            "    sink.words = sweep.words\n"
            "    count = 0\n"
            "    assert count == 0\n"
        ),
        # THE ASSERT SITS INSIDE THE HANDLER, which is where the handler name is
        # still bound. An assert AFTER the handler renders nothing, because
        # Python deletes the name on the way out - measured, and the reason this
        # form's record names the handler interior specifically.
        "except-target": _recorded_module(
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    try:\n"
            "        raise ValueError(sweep.words)\n"
            "    except ValueError as exc:\n"
            "        count = len(exc.args)\n"
            "        assert count == 0\n"
        ),
        "match-capture": _recorded_module(
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    match sweep.words:\n"
            "        case captured:\n"
            "            count = len(captured)\n"
            "            assert count == 0\n"
        ),
        "comprehension-target": _recorded_module(
            "def test_it() -> None:\n"
            "    sweep = Sweep(WORDS)\n"
            "    count = len([1 for _w in sweep.words])\n"
            "    assert count == 0\n"
        ),
        "import": (
            "import ast\n"
            "\n"
            "def test_it() -> None:\n"
            "    count = len(ast.__name__)\n"
            "    assert count == 0\n"
        ),
        "definition": (
            "def helper():\n"
            "    return 1\n"
            "\n"
            "def test_it() -> None:\n"
            "    count = helper()\n"
            "    assert count == 0\n"
        ),
        "type-alias": (
            "type Words = frozenset[str]\n"
            "\n"
            "def test_it() -> None:\n"
            "    count = len(Words.__name__)\n"
            "    assert count == 0\n"
        ),
        # CARRIES THE WITHHELD FIELD THROUGH THE DECLARATION, which the source
        # this replaced did not: it read a module-level zero and could not have
        # graded the form against anything. A ``global`` target is not in the
        # function's frame, so this is the form's whole claim under measurement.
        "scope-declaration": _recorded_module(
            "HELD = None\n"
            "\n"
            "def test_it() -> None:\n"
            "    global HELD\n"
            "    sweep = Sweep(WORDS)\n"
            "    HELD = sweep.words\n"
            "    count = len(HELD)\n"
            "    assert count == 0\n"
        ),
        "parameter": _recorded_module(
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def sweep():\n"
            "    return Sweep(WORDS)\n"
            "\n"
            "def test_it(sweep: Sweep) -> None:\n"
            "    count = len(sweep.words)\n"
            "    assert count == 0\n"
        ),
    }
)


def _recorded_sandbox(root: Path, *, showlocals: bool) -> tuple[int, str]:
    """Write every recorded-form fixture and run real pytest over the lot.

    ONE SUBPROCESS FOR ALL OF THEM, one file each so their identically named
    holders and tests cannot collide. Each file gets its own marker, so a
    single grep of the combined report attributes every leak to its form.

    Args:
        root: A directory to write into.
        showlocals: Whether to pass ``-l``.

    Returns:
        pytest's own exit code, and its combined output.
    """
    root.mkdir(parents=True, exist_ok=True)
    for index, form in enumerate(sorted(RECORDED_SOURCES)):
        source = RECORDED_SOURCES[form].replace(RECORDED_TOKEN_MARK, recorded_token(index))
        # The arms must FAIL, or a clean grep only proves nothing ran.
        source = source.replace("assert count == 0", "assert count < 0")
        (root / f"test_recorded_{index:02d}.py").write_bytes(source.encode("ascii"))
    argv = [
        sys.executable,
        "-m",
        "pytest",
        str(root),
        "-p",
        "no:cacheprovider",
        "--rootdir",
        str(root),
    ]
    if showlocals:
        argv.append("-l")
    completed = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=str(root),
        timeout=SUBPROCESS_TIMEOUT,
    )
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    return (completed.returncode, text)


@pytest.fixture(scope="module")
def recorded_showlocals(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """Every recorded-form fixture under ``-l``."""
    return _recorded_sandbox(tmp_path_factory.mktemp("cs851_rec_l"), showlocals=True)


@pytest.fixture(scope="module")
def recorded_default(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """Every recorded-form fixture under the flags this project ships."""
    return _recorded_sandbox(tmp_path_factory.mktemp("cs851_rec_d"), showlocals=False)


def _measured_rendering(output: str) -> dict[str, bool]:
    """Which recorded forms had their marker printed in one rendered report.

    Args:
        output: pytest's combined output over the recorded-form sandbox.

    Returns:
        Form label to whether its marker reached the report. Forms whose
        fixture carries no marker are absent from the mapping.
    """
    measured: dict[str, bool] = {}
    for index, form in enumerate(sorted(RECORDED_SOURCES)):
        if RECORDED_TOKEN_MARK not in RECORDED_SOURCES[form]:
            continue
        measured[form] = recorded_token(index) in output
    return measured


def test_the_canonical_shape_is_a_finding_here_and_not_in_cs850():
    # THE BOUNDARY, MEASURED AGAINST THE SHIPPED GUARD RATHER THAN QUOTED FROM
    # A NOTE. If this module could not find the shape, it would have rebuilt
    # CS-850; if CS-850 started finding it, two modules would be grading the
    # same thing and one of them should go.
    theirs = len(scan_source("<canonical>", CANONICAL_SOURCE))
    mine = scan_source_locals("<canonical>", CANONICAL_SOURCE)
    assert theirs == 0, (
        f"CS-850's assertion-channel guard reported {theirs} findings on the "
        "canonical locals shape. Its boundary has moved and this module's "
        "reason to exist needs re-deriving"
    )
    found = len(mine)
    assert found == 1, f"the locals scan reported {found} findings on the canonical shape"
    names = sorted(finding.local for finding in mine)
    assert names == ["unexplained"], (
        f"the finding names {names}; the leak is the aggregate's own local, not the scalar"
    )


def test_every_followed_binding_form_reaches_a_finding():
    # DERIVED FROM THE ARM GENERATOR, so the shapes proven detectable here are
    # byte-identical to the ones the forced pytest runs below execute.
    sweep = scan_sources({"<leaking>": sandbox_module(remedied=False)})
    seen = {finding.form for finding in sweep.findings}
    missing = sorted(FOLLOWED_FORMS - seen)
    undetected = len(missing)
    assert undetected == 0, (
        f"{undetected} of {len(FOLLOWED_FORMS)} covered binding forms produced no "
        f"finding in the generated leaking arms: {missing}"
    )


def test_no_safe_shape_is_flagged():
    findings = scan_source_locals("<safe>", SAFE_SOURCE)
    flagged = len(findings)
    assert flagged == 0, (
        "a shape that discloses nothing was flagged - a reduction, a whole "
        "redacting object, a disclosed field or a constructor argument:\n"
        + describe_locals(findings)
    )


def test_a_binding_made_after_the_assert_is_not_in_the_frame():
    # ``frame.f_locals`` holds what has been ASSIGNED so far. A set-of-bindings
    # analysis would report this and be wrong about the only moment that counts.
    lines = sorted(finding.lineno for finding in scan_source_locals("<order>", ORDER_SOURCE))
    at_the_first_assert = [line for line in lines if line < max(lines or [0])]
    early = len(at_the_first_assert)
    assert early == 0, f"a binding below the first assert was reported at lines {lines}"


def test_a_binding_later_in_a_loop_body_is_in_the_frame_on_the_next_pass():
    findings = scan_source_locals("<loop>", LOOP_SOURCE)
    carried = [finding for finding in findings if finding.local == "carried"]
    found = len(carried)
    assert found == 1, (
        "a binding made after the assert but inside the same loop body is in "
        f"the frame on the second iteration; {found} findings named it"
    )


def test_a_rebinding_to_something_safe_clears_the_finding():
    findings = scan_source_locals("<rebind>", REBIND_SOURCE)
    flagged = len(findings)
    assert flagged == 0, (
        "a name reused for a scalar still carried the aggregate it held "
        "before:\n" + describe_locals(findings)
    )


def test_the_recorded_forms_are_pinned_rather_than_silently_absent():
    # WHAT THIS MEASURES IS THE SCANNER'S SILENCE, AND ONLY THAT. Each source
    # carries the same withheld field in a form the scan states it does not
    # follow, so a zero here says the scan is quiet about it - which is true by
    # construction wherever no scan step exists. It is NOT evidence that the
    # form is safe, and reading it that way is how four leaking forms came to
    # be pinned as though they were not. The rendering half is graded by
    # test_every_recorded_form_renders_exactly_as_it_declares, against a real
    # pytest -l run over these same sources.
    #
    # A form that starts being FOLLOWED turns this red and gets its entry moved
    # rather than quietly gaining coverage nobody graded.
    noisy = {
        form: len(scan_source_locals(f"<{form}>", source))
        for form, source in RECORDED_SOURCES.items()
    }
    unexpected = sorted(form for form, count in noisy.items() if count)
    surprises = len(unexpected)
    assert surprises == 0, f"a form recorded as not followed produced findings: {unexpected}"
    uncovered = sorted(set(RECORDED_FORMS) - set(RECORDED_SOURCES))
    gaps = len(uncovered)
    assert gaps == 0, f"these recorded forms have no pinning source: {uncovered}"


GLOBAL_SOURCE: Final = '''
"""A `global` target is not a local of the frame that renders."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


HELD = None


def test_it(sweep: Sweep) -> None:
    global HELD
    HELD = sweep.words
    count = len(HELD)
    assert count == 0
'''


def test_a_global_declared_name_is_not_a_local_of_the_failing_frame():
    findings = scan_source_locals("<global>", GLOBAL_SOURCE)
    flagged = len(findings)
    assert flagged == 0, (
        "an assignment to a name declared `global` was reported as a local "
        "holding a withheld field. It is not one: the binding lives in the "
        "module's namespace, and a real forced run under -l renders nothing "
        "for it. A false positive whose own recorded reason says it should not "
        "fire is the fastest way to train a reader to ignore a tier 1 "
        "guard:\n" + describe_locals(findings)
    )


NONLOCAL_SOURCE: Final = '''
"""A `nonlocal` target IS rendered - the global fix must not reach it."""


class Sweep:
    def __init__(self, words):
        self.words = words

    def __repr__(self):
        return f"Sweep(words={len(self.words)})"


def test_it(sweep: Sweep) -> None:
    held = None

    def inner(sweep: Sweep) -> None:
        nonlocal held
        held = sweep.words
        count = len(held)
        assert count == 0

    inner(sweep)
'''


def test_a_nonlocal_declared_name_is_still_a_finding():
    # THE REGRESSION PIN ON THE ARM ABOVE, AND THE HALF THAT IS NOT SYMMETRIC.
    # `global` and `nonlocal` read alike and behave oppositely: a nonlocal name
    # is a cell in the declaring frame and a free variable in the inner one,
    # and pytest renders BOTH - measured. Suppressing it alongside `global`
    # would trade a false positive for a false negative, which is the direction
    # that hides a leak.
    findings = scan_source_locals("<nonlocal>", NONLOCAL_SOURCE)
    named = sorted(finding.local for finding in findings)
    assert named == ["held"], (
        "a name assigned under `nonlocal` IS in the frame pytest renders, so "
        f"it must stay a finding; the scan reported {named}"
    )


def test_every_recorded_form_renders_exactly_as_it_declares(
    recorded_showlocals: tuple[int, str],
    recorded_default: tuple[int, str],
):
    # THE FIXTURE TRAP, CLOSED. The arm below this one measures the SCANNER'S
    # SILENCE, which is true by construction wherever no scan step exists - it
    # is not evidence about rendering, and reading it as evidence pinned four
    # leaking forms as safe. This one runs real pytest over the same fixtures
    # and grades what is PRINTED against what each form DECLARES.
    code_l, out_l = recorded_showlocals
    code_d, out_d = recorded_default
    plantable = sum(1 for entry in RECORDED_FORMS.values() if entry.plantable)
    for code in (code_l, code_d):
        assert code == PYTEST_TESTS_FAILED, (
            f"the recorded-form sandbox exited {code}; expected "
            f"{PYTEST_TESTS_FAILED}. A sandbox that died renders no marker "
            "either, and that is not the property under test"
        )
    collected = f"collected {len(RECORDED_SOURCES)} item" in out_l
    assert collected, (
        f"the recorded-form sandbox did not collect all {len(RECORDED_SOURCES)} fixtures"
    )
    measured_l = _measured_rendering(out_l)
    measured_d = _measured_rendering(out_d)
    graded = len(measured_l)
    assert graded == plantable, (
        f"{graded} recorded fixtures planted a marker against {plantable} forms "
        "declared plantable; a form whose fixture carries no marker is graded "
        "on silence rather than on what pytest printed"
    )
    wrong = sorted(
        form
        for form, entry in RECORDED_FORMS.items()
        if form in measured_l
        and (measured_l[form], measured_d[form]) != (entry.renders, entry.renders_by_default)
    )
    drifted = len(wrong)
    assert drifted == 0, (
        f"{drifted} recorded forms render differently from what they declare. "
        "A form that started rendering must have its reason restated to say so "
        "plainly, or gain a scan step; a form that stopped may have its record "
        "corrected: " + repr(wrong)
    )


def test_the_liveness_flag_is_not_a_constant():
    # A PARTITION WITH ONE EMPTY SIDE IS A CONSTANT WEARING A PREDICATE'S NAME.
    # Proven on SYNTHETIC sources whose verdicts cannot change when the tree is
    # repaired - requiring the real tree's live side to be non-empty is the
    # defect that refuted three items in one session.
    verdicts = {finding.live for finding in scan_source_locals("<prov>", PROVENANCE_SOURCE)}
    both = verdicts == {True, False}
    assert both, (
        f"the liveness flag took the values {sorted(verdicts)} across the "
        "synthetic corpus; with one value every partition assertion is vacuous"
    )


def test_the_two_channels_agree_except_at_a_call_argument():
    # THE SEAM PIN. The vocabularies are imported from CS-850's module and the
    # walk is not, so this runs BOTH walks over the same nodes on every run. A
    # change to the borrowed mask rule shows up here rather than silently
    # re-grading this channel.
    cases = {
        "len(sweep.words)": (False, False),
        "sorted(sweep.words)": (True, True),
        "sweep.words": (True, True),
        "sweep.words == other": (False, False),
        "helper(sweep.words)": (True, False),
    }
    disagreements: list[str] = []
    for text, (assertion_channel, locals_channel) in cases.items():
        value = ast.parse(text, mode="eval").body
        read = next(
            node
            for node in ast.walk(value)
            if isinstance(node, ast.Attribute) and node.attr == "words"
        )
        kin = _parent_map(value)
        theirs = _reaches_unmasked(read, kin, {id(value)}, {}, 2)
        mine = flows_into(read, kin, id(value))
        if (theirs, mine) != (assertion_channel, locals_channel):
            disagreements.append(f"{text}: expected {(assertion_channel, locals_channel)}")
    moved = len(disagreements)
    assert moved == 0, (
        "the two channels no longer differ where this module says they do; "
        "re-derive the difference before trusting either grade: " + repr(disagreements)
    )


# ---------------------------------------------------------------------------
# THE SWEEP. This is what a new leaky binding lands on.
# ---------------------------------------------------------------------------


def test_the_sweep_read_a_population_that_is_not_empty():
    # "Found nothing" and "looked for nothing" are the same output. Every
    # number here is STABLE under a leak being repaired: modules, scopes,
    # asserts and redacting declarations do not shrink when a binding is moved.
    sweep = scan_tree()
    assert sweep.modules > 1, f"the sweep parsed {sweep.modules} modules; it is reading one file"
    assert sweep.asserts > 1, f"the sweep graded {sweep.asserts} assertions"
    assert sweep.declarations > 1, (
        f"the sweep derived {sweep.declarations} classes with a withheld field; "
        "at one or fewer every assertion below it is about nothing"
    )


def test_every_binding_form_the_tree_ships_is_a_form_this_module_knows():
    # THE POPULATION IS DERIVED FROM THE SHIPPED BINDINGS, and this is the
    # derivation. The census is exhaustive over STATEMENT KINDS rather than over
    # the forms the scan follows, so a binding shape arriving in the tree that
    # nothing here has graded is RED. It is monotone-safe in the other
    # direction: a form disappearing from the tree cannot break it.
    #
    # IT CANNOT CATCH A RECORDED FORM ARRIVING, and that is a boundary rather
    # than a gap: a recorded form is inside KNOWN_FORMS by construction, so the
    # difference below is empty for it however many the tree ships. The arm
    # after this one is the half that grades presence.
    forms = shipped_binding_forms()
    unknown = sorted(set(forms) - KNOWN_FORMS)
    ungraded = len(unknown)
    assert ungraded == 0, (
        f"the tree ships {ungraded} binding forms this module neither follows "
        f"nor records: {unknown}. Add each to FOLLOWED_FORMS with a scan step, "
        "or to RECORDED_FORMS with the reason and a pinning source"
    )


def test_every_recorded_form_is_present_or_absent_as_it_declares():
    # THE ARRIVAL CHECK THAT WAS MISSING, AND THE ONE THIS MODULE NEEDED. It
    # shipped recording `match-capture` as absent - "this tree contains none" -
    # while the census counted the form and the tree carried eight `match`
    # statements, three of them in the guard module itself. Nothing could have
    # reddened: the only census arm asks whether a form is KNOWN, and a
    # recorded form is known by construction.
    #
    # DERIVED, NOT COUNTED. The number of occurrences is deliberately not
    # pinned - it moves on every edit and pinning it would be a maintenance tax
    # with no privacy content. Presence is the bit that changes what this
    # module owes a reader.
    census = shipped_binding_forms()
    arrived = sorted(
        form
        for form, entry in RECORDED_FORMS.items()
        if not entry.in_tree and census.get(form, 0) > 0
    )
    unannounced = len(arrived)
    assert unannounced == 0, (
        f"{unannounced} binding forms recorded as ABSENT from this tree are "
        "now in it. Restate the record's in_tree field and re-read the reason "
        "beside it - a form arriving is exactly when 'not followed' stops "
        f"being free: {arrived}"
    )


def test_a_recorded_form_that_left_the_tree_is_reported_rather_than_reddening():
    # THE OTHER DIRECTION IS A REPORT. Code disappearing is not a privacy
    # defect, and reddening on it would mean deleting the last `match`
    # statement in the tree breaks this module. The claim is still worth
    # keeping true, so it is named rather than asserted.
    census = shipped_binding_forms()
    left = sorted(
        form for form, entry in RECORDED_FORMS.items() if entry.in_tree and census.get(form, 0) == 0
    )
    if left:
        warnings.warn(
            f"{len(left)} binding forms recorded as present are no longer in "
            f"the tree; clear their in_tree field: {left}",
            stacklevel=1,
        )
    # THE SHAPE, NOT THE SIZE, for the same reason as the residual report. A
    # form reported as departed must be one this module records; anything else
    # means the census and the record are keyed differently.
    foreign = sorted(set(left) - set(RECORDED_FORMS))
    invented = len(foreign)
    assert invented == 0, f"{invented} departed forms are not recorded here at all: {foreign}"


def test_no_unrecorded_live_local_holds_a_withheld_field_at_an_assertion():
    live = _live(scan_tree().findings)
    over = unrecorded_residuals(live, LIVE_LOCALS_RESIDUALS)
    reddening = len(over)
    unrecorded = set(over)
    assert reddening == 0, (
        "a local holds a field its own class ships a __repr__ to WITHHOLD, and "
        "is still in the frame when an assertion in that scope fails. Under "
        "-l/--showlocals pytest renders it whatever the assertion said "
        "(CLAUDE.md non-negotiables 11 and 12). The remedy is to STOP BINDING "
        "it - inline the read into the reduction - not to bind a scalar beside "
        "it, which leaves the original local in the frame:\n"
        + describe_locals([f for f in live if residual_key(f) in unrecorded])
    )


def test_a_replacement_finding_is_not_absorbed_by_the_record():
    # DERIVED FROM THE RECORD'S OWN KEYS, never from the live sweep, so this
    # arm is identical on a tree where every recorded site has been repaired.
    #
    # THE COUNTER-EXAMPLE THAT RETIRED THE CEILING, IN PROCESS. Every planted
    # finding sits in a file the record already names, at a scope and under a
    # local name the record does not. A per-module count reported none of them.
    planted = [
        LocalFinding(
            module=module,
            lineno=1,
            scope=f"test_planted_scope_{index}",
            local=f"planted_local_{index}",
            bound_at=1,
            form=ASSIGN,
            holder="Planted",
            field="words",
            source="planted.words",
            live=True,
        )
        for index, module in enumerate(sorted({key[0] for key in LIVE_LOCALS_RESIDUALS}))
    ]
    reported = unrecorded_residuals(planted, LIVE_LOCALS_RESIDUALS)
    absorbed = len(planted) - len(reported)
    assert absorbed == 0, (
        f"{absorbed} of {len(planted)} BRAND-NEW leaky bindings - new scope, "
        "new local name, in a file the record already names - were absorbed by "
        "the record and reported nothing. A record that cannot tell 'still the "
        "same site' from 'a different site' accepts every replacement"
    )


def test_a_finding_in_a_module_the_record_does_not_name_is_reported():
    # THE SECOND DIRECTION. A file with no entry at all has no ceiling to be
    # under and no key to match, so one finding in it is enough.
    planted = [
        LocalFinding(
            module="tests/<synthetic-unrecorded>.py",
            lineno=1,
            scope="test_planted",
            local="planted_local",
            bound_at=1,
            form=ASSIGN,
            holder="Planted",
            field="words",
            source="planted.words",
            live=True,
        )
    ]
    reported = len(unrecorded_residuals(planted, LIVE_LOCALS_RESIDUALS))
    assert reported == 1, (
        f"a live finding in a module the record does not name was reported "
        f"{reported} times; it must be reported exactly once"
    )


def test_a_repaired_site_is_reported_as_stale_rather_than_reddening():
    # THE THIRD DIRECTION, AND THE ONE THAT MUST NOT BE AN ASSERTION ON THE
    # LIVE TREE. Repairing a recorded site leaves its entry behind; the record
    # must name that entry precisely, so the repair costs one line to finish
    # rather than a hunt. Proven on a SYNTHETIC finding set built from the
    # record's own keys, so it grades the same on a fully repaired tree.
    keys = sorted(LIVE_LOCALS_RESIDUALS)
    repaired = keys[0]
    surviving = [
        LocalFinding(
            module=module,
            lineno=1,
            scope=scope,
            local=local,
            bound_at=1,
            form=ASSIGN,
            holder="Recorded",
            field="words",
            source="recorded.words",
            live=True,
        )
        for module, scope, local in keys[1:]
    ]
    stale = stale_residuals(surviving, LIVE_LOCALS_RESIDUALS)
    named = stale == [repaired]
    assert named, (
        f"repairing one recorded site left {len(stale)} stale entries reported "
        "instead of exactly the one repaired; the report names the wrong "
        "line to delete:\n" + describe_residual_keys(stale)
    )
    # AND THE REPAIR IS NOT ALSO A RED. The same synthetic sweep must produce
    # no unrecorded finding, or the record would punish the fix it asks for.
    reddening = len(unrecorded_residuals(surviving, LIVE_LOCALS_RESIDUALS))
    assert reddening == 0, (
        f"repairing one recorded site produced {reddening} unrecorded findings; "
        "the guard would go red on a tree that got better"
    )


def test_a_repaired_residual_is_reported_rather_than_reddening():
    # A REPORT, NOT AN ASSERTION, AND THE DIFFERENCE IS THE FENCE. An arm that
    # reddened here would need the live population to still hold every recorded
    # site - the shape that refuted three items in one session, where repairing
    # a leak turned the proof red and a green run certified the tree still
    # leaked. The mechanism itself is graded above on synthetic findings.
    stale = stale_residuals(_live(scan_tree().findings), LIVE_LOCALS_RESIDUALS)
    if stale:
        warnings.warn(
            f"{len(stale)} recorded residuals no longer name a live finding. "
            "Each is a site that has been repaired; delete these entries from "
            "LIVE_LOCALS_RESIDUALS:\n" + describe_residual_keys(stale),
            stacklevel=1,
        )
    # WHAT IS ASSERTED IS THE REPORT'S SHAPE, not the population's size: a
    # stale entry can only ever be one the record itself names, so a key from
    # anywhere else means the partition is reading the wrong thing. This holds
    # on an empty tree and on a fully repaired one alike.
    foreign = sorted(set(stale) - set(LIVE_LOCALS_RESIDUALS))
    invented = len(foreign)
    assert invented == 0, (
        f"{invented} keys reported stale are not in the record at all:\n"
        + describe_residual_keys(foreign)
    )


def test_every_recorded_residual_names_a_file_that_exists():
    missing = sorted(
        {module for module, _, _ in LIVE_LOCALS_RESIDUALS if not (REPO_ROOT / module).is_file()}
    )
    absent = len(missing)
    assert absent == 0, f"a residual names a file that is not in the tree: {missing}"


def test_every_recorded_residual_carries_a_reason_from_the_declaration_table():
    # A RECORD ENTRY WITH A BESPOKE REASON IS A REASON THAT CAN DRIFT FROM ITS
    # SIBLINGS. Every entry reads its text from RESIDUAL_REASONS, keyed by the
    # DECLARATION it holds, so two sites reading the same withheld field cannot
    # end up with two accounts of why that is accepted.
    known = set(RESIDUAL_REASONS.values())
    bespoke = sorted(key for key, reason in LIVE_LOCALS_RESIDUALS.items() if reason not in known)
    loose = len(bespoke)
    assert loose == 0, (
        f"{loose} residual entries carry a reason that is not one of the "
        "declaration-keyed texts:\n" + describe_residual_keys(bespoke)
    )


def test_the_latent_population_is_visible_rather_than_absent():
    # REPORTED, NOT ASSERTED TO ZERO: those holders are built from bytes the
    # process hand-authored beside them. What must stay true is that every one
    # sits in a file the sweep can still read, so the record cannot quietly
    # become about nothing.
    latent = _latent(scan_tree().findings)
    missing = sorted({f.module for f in latent if not (REPO_ROOT / f.module).is_file()})
    unreadable = len(missing)
    assert unreadable == 0, f"the sweep reported a finding in a file it cannot read: {missing}"


# ---------------------------------------------------------------------------
# GREEN ON A TREE THAT HAS NONE. The fence session 39 paid for three times.
# ---------------------------------------------------------------------------


def _clean_corpus() -> LocalSweep:
    """The remedied arms, scanned as a corpus in their own right.

    Returns:
        The sweep over a corpus that uses every covered binding form and leaks
        through none of them.
    """
    return scan_sources({"<clean>": sandbox_module(remedied=True)})


def test_the_sweep_is_green_on_a_corpus_with_no_such_binding():
    # THE ACCEPTANCE'S LAST CLAUSE, PROVEN DIRECTLY. A privacy guard whose green
    # state REQUIRES a leak is worse than no guard: repairing one turns it red
    # and a green run certifies that the tree still leaks. This corpus exercises
    # every covered form in the remedied shape, so a zero here is a zero earned
    # on content rather than on absence.
    sweep = _clean_corpus()
    leaked = len(sweep.findings)
    assert leaked == 0, (
        "the remedied arms - which bind no aggregate to any local - still "
        "produced findings, so this guard would go red on a repaired "
        "tree:\n" + describe_locals(sweep.findings)
    )
    assert sweep.asserts >= len(FOLLOWED_FORMS), (
        f"the clean corpus graded {sweep.asserts} assertions against "
        f"{len(FOLLOWED_FORMS)} covered forms, so the zero above is absence "
        "rather than evidence"
    )
    assert sweep.declarations >= len(FOLLOWED_FORMS), (
        f"the clean corpus declared {sweep.declarations} redacting classes; "
        "with fewer, the scan had nothing to grade against"
    )


def test_the_leaking_and_remedied_corpora_differ_in_exactly_the_binding():
    # THE CONTROL FOR THE ARM ABOVE. Same forms, same holders, same number of
    # assertions - the only difference is whether the aggregate is bound to a
    # local. If the leaking corpus were also clean, the green above would be
    # measuring the generator rather than the remedy; if the remedied one simply
    # had fewer assertions, it would be measuring arms that stopped running.
    #
    # THE COUNT IS OF BINDINGS AND NOT OF FORMS, because they are not the same
    # number: ``first = second = item.words`` is ONE chained-assign statement
    # binding TWO locals, and both are in the frame. Asserting an equality
    # against the form count read that as an error the first time it ran.
    leaking = scan_sources({"<leaking>": sandbox_module(remedied=False)})
    remedied = _clean_corpus()
    same_arms = leaking.asserts == remedied.asserts
    assert same_arms, (
        f"the leaking corpus grades {leaking.asserts} assertions and the "
        f"remedied one {remedied.asserts}; they must differ only in the binding"
    )
    found = len(leaking.findings)
    assert found >= len(FOLLOWED_FORMS), (
        f"the leaking corpus produced {found} findings for "
        f"{len(FOLLOWED_FORMS)} covered forms, so at least one form is not "
        "exercised by a leak at all"
    )
    surviving = len(remedied.findings)
    assert surviving == 0, (
        f"{surviving} findings survived into the remedied corpus:\n"
        + describe_locals(remedied.findings)
    )


# ---------------------------------------------------------------------------
# THE FORCED ARMS - graded on what pytest ACTUALLY PRINTS
# ---------------------------------------------------------------------------


def test_the_forced_arms_are_derived_from_the_covered_forms():
    # NOT FROM THE FINDINGS. Nothing in arm_specs() reads scan_tree(), so
    # repairing every live finding in the repository leaves this population
    # untouched - which is the property session 39 refuted three items for
    # lacking.
    specs = arm_specs()
    covered = {form for form, _ in specs}
    uncovered = sorted(FOLLOWED_FORMS - covered)
    gaps = len(uncovered)
    assert gaps == 0, f"these covered forms have no forced arm: {uncovered}"
    arms = len(specs)
    assert arms > 1, f"only {arms} arms were generated; the proof would be about one shape"


def test_every_sensitive_class_is_covered_by_the_forced_arms():
    planted = {token for _, token in arm_specs()}
    uncovered = sorted(token for token in SENSITIVE_TOKENS if token not in planted)
    gaps = len(uncovered)
    assert gaps == 0, (
        "the forced arms do not plant every class the acceptance names - a "
        "save-derived name, a home path and an account directory. Uncovered: " + repr(uncovered)
    )


def test_the_forced_arms_actually_ran_and_failed(leaking_showlocals: tuple[int, str]):
    # DETECTED IS NOT CRASHED. A sandbox that died during collection renders no
    # planted token either, and that is not the property under test.
    code, output = leaking_showlocals
    arms = len(arm_specs())
    assert code == PYTEST_TESTS_FAILED, (
        f"the control sandbox exited {code}; expected {PYTEST_TESTS_FAILED}, "
        "which is 'tests ran and failed'"
    )
    collected = f"collected {arms} item" in output
    assert collected, f"the control sandbox did not collect all {arms} forced arms"


def test_the_unremedied_arms_render_every_planted_token_under_showlocals(
    leaking_showlocals: tuple[int, str],
):
    # THE CONTROL, AND THE WHOLE OF THIS SECTION RESTS ON IT. If a planted token
    # is NOT rendered here, the greps below cannot distinguish a remedy that
    # worked from a harness that never looked.
    _, output = leaking_showlocals
    planted = {token for _, token in arm_specs()}
    missing = sorted(token for token in planted if token not in output)
    unrendered = len(missing)
    assert unrendered == 0, (
        f"{unrendered} of {len(planted)} planted tokens were NOT rendered under "
        "-l, so this module is not measuring the channel it claims to measure. "
        "The tokens are synthetic and safe to name: " + repr(missing)
    )


def test_the_unremedied_arms_render_no_planted_token_by_default(
    leaking_default: tuple[int, str],
):
    # THE CHANNEL BOUNDARY, MEASURED. The SAME leaking arms under the flags this
    # project actually ships render nothing, which is what makes this the LOCALS
    # channel rather than CS-850's. It is also the honest severity: -l is a
    # debugging flag, not the default, and saying "every failure leaks" would be
    # a claim this measurement refutes.
    code, output = leaking_default
    assert code == PYTEST_TESTS_FAILED, (
        f"the default-flag sandbox exited {code}; it must still FAIL, or a clean "
        "grep only proves the arms stopped running"
    )
    planted = {token for _, token in arm_specs()}
    leaked = sorted(token for token in planted if token in output)
    rendered = len(leaked)
    assert rendered == 0, (
        f"{rendered} planted tokens reached the report WITHOUT -l, so these arms "
        "are leaking through the assertion or source channel as well and this "
        "module is not isolating the one it names: " + repr(leaked)
    )


def test_the_remedied_arms_render_no_planted_token_under_showlocals(
    remedied_showlocals: tuple[int, str],
):
    # THE ACCEPTANCE, GRADED ON THE RENDERED OUTPUT. Same forms, same failures,
    # same -l - with nothing binding the aggregate to a local.
    code, output = remedied_showlocals
    assert code == PYTEST_TESTS_FAILED, (
        f"the remedied sandbox exited {code}; it must still FAIL, or a clean "
        "grep only proves the arms stopped running"
    )
    planted = {token for _, token in arm_specs()}
    leaked = sorted(token for token in planted if token in output)
    survivors = len(leaked)
    assert survivors == 0, (
        f"{survivors} planted tokens survived the remedy into the rendered "
        "failure report under -l. Removing the BINDING is the whole fix, so a "
        "token still present means a local still holds the aggregate: " + repr(leaked)
    )
