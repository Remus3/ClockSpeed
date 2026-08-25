"""CS-850 - no shipped assertion renders a value its own class declared withheld.

THE CHANNEL IS NOT THE MESSAGE, and that single sentence is the whole item.
pytest rewrites ``assert TEST, MESSAGE`` and renders the sub-expressions of TEST
with their own reprs, independently of MESSAGE. The part a reviewer reads is the
part that does not control what is printed. ``tests/assertion_rendering_guard``
carries the mechanism in full; this module is what drives it and what proves it.

THE POPULATION IS DERIVED TWICE OVER, and neither derivation is a list. A class
that ships a hand-written ``__repr__`` in order to withhold its contents has
DECLARED its fields unsafe to render - twenty-six of them do, and every one says
so in its own docstring. Which fields are withheld is read out of that
``__repr__``'s body. Which assertions reach one is read out of pytest's own
rewriting rules. Nothing below names a module, a class or a field, so a
redacting class added tomorrow is covered the moment it exists. CS-205 records
why that matters: a hand-listed acceptance in this project went stale between
being written and being worked, every time.

PROVEN BY WHAT PYTEST ACTUALLY PRINTS. Reading the message text would grade
exactly the half of the channel that is not the channel, so the proof below
forces a representative arm of each guarded module to FAIL inside a real pytest
subprocess, with a synthetic token planted in the withheld field, and greps the
rendered output for it. Three token classes are planted - a save-derived name, a
home path and an account directory - and
``test_every_sensitive_class_is_covered_by_the_forced_arms`` asserts all three
are actually exercised rather than merely defined.

THE CONTROL IS THE HALF THAT MAKES THE REST MEAN ANYTHING. A sandbox where no
token is found proves nothing unless the same sandbox WITHOUT the remedy is
measured finding them. Both arms run, and the unremedied one asserts every
planted token IS rendered. If it ever finds none, this module proves nothing and
says so in those words rather than passing.

LIVE AND LATENT, and why both are reported. The same construct is a DISCLOSURE
when the holder came from the real save library, from a machine fixture or from
a caller one frame up, and a LATENT defect when it was built from bytes this
process hand-authored. The synthetic case carries nothing personal, and
rewriting those arms would destroy the expected-versus-actual diff that is their
entire diagnostic value while buying no privacy at all. So the hard requirement
is on the LIVE partition and the latent one is reported, with
``test_the_partition_is_read_from_provenance_and_not_from_the_file`` proving the
partition responds to how a holder was built rather than to where it sits.

WHY A STATIC GUARD IS NEEDED AT ALL, measured rather than argued. ``conftest``
already redacts home paths and account names out of every failure report, so two
of the three classes have a runtime net under them.
``test_the_runtime_redactor_cannot_reach_a_save_derived_name`` measures that net
and shows it does NOT catch the third: a world name, a save name or a struct
word is not derivable from this machine's environment, so no redactor can know
it. That is the gap this guard exists to close, and it is measured here rather
than asserted.

THE MARKERS ARE SYNTHETIC AND THE MACHINE'S ARE NEVER PRINTED. Every planted
token below is invented. The one place this module touches real machine state -
the redactor measurement - derives its spellings at run time and reports a
verdict rather than a value.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final

import pytest

from tests.assertion_rendering_guard import (
    LIBRARY_LOCATORS,
    Finding,
    describe,
    explained,
    scan_repo,
    scan_source,
)
from tests.conftest import REDACTED_HOME, REDACTED_USER, redact_personal_data
from tests.save import reach_guard

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT: Final = 300

#: pytest's exit code when tests ran and at least one of them failed.
PYTEST_TESTS_FAILED: Final = 1

#: A synthetic save-derived name: the class of value a world name, a save name,
#: a session name or a decoded struct word belongs to. NOTHING on this machine
#: is spelled like this, and nothing that is may be written into a tracked file.
#: The three below are flagged by bandit as hardcoded secrets, which is the
#: rule firing on the right SHAPE for the wrong reason: they are the planted
#: markers a leak is grepped for, and a marker that is not in the source is a
#: marker the grep cannot look for.
SAVE_NAME_TOKEN: Final = "Cs850SyntheticSaveName"  # noqa: S105

#: A synthetic home path. The drive letter and the account name are both
#: invented; the SHAPE is what matters, because that is what leaks.
#:
#: ASSEMBLED FROM FRAGMENTS ON PURPOSE, and the reason is another guard doing
#: its job rather than a formatting whim. ``tests/test_scaffold.py`` greps every
#: authored file's BYTES for a contiguous drive-Users-account run and CANNOT
#: tell an invented account name from a real one - which is the correct
#: conservative behaviour and must not be loosened for this file. Splitting the
#: literal leaves the runtime VALUE identical, which is the only half the grep
#: below reads. ``tests/test_exception_rendering.py`` builds its crash marker
#: the same way, for the same reason, and the scaffold guard's own positive
#: samples are assembled the same way too.
HOME_PATH_TOKEN: Final = "Q:/" + "Users" + "/cs850synthetic/AppData/Local"

#: A synthetic platform account directory - the numeric subdirectory under the
#: save root, which CLAUDE.md section 2 names as personal data outright.
ACCOUNT_DIR_TOKEN: Final = "90000000000000850"  # noqa: S105

#: The three classes the acceptance names, in the order it names them.
SENSITIVE_TOKENS: Final = (SAVE_NAME_TOKEN, HOME_PATH_TOKEN, ACCOUNT_DIR_TOKEN)

#: A home directory is at least a root plus a name. Anything shorter is a bare
#: filesystem root, which is not personal data.
MIN_HOME_SPELLING: Final = 4

#: The glob the guard hands git. The one ``.py`` literal it is allowed to carry,
#: because it names a file TYPE rather than a module.
GIT_PY_GLOB: Final = "*.py"

#: Live findings that survive the change which added this guard, path to why.
#:
#: A RECORD OF KNOWN RESIDUALS, NOT AN ALLOWLIST THAT ABSORBS THE NEXT ONE. A
#: live finding in any file NOT named here is red, and a file named here whose
#: findings have all been repaired is ALSO red - see
#: :func:`test_no_live_assertion_renders_a_field_its_class_withheld`, which
#: asserts the record in both directions so it cannot rot into a silent
#: exemption after the code it describes has gone.
LIVE_DISCLOSURE_RESIDUALS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "tests/save/test_container_elements.py": (
            "Seven arms render a field the module's own _ContainerSweep withholds, "
            "and that sweep is fed by the real save library rather than by a "
            "synthetic fixture. Not repaired in the change that added this guard: "
            "the file was owned by another unit of work at the time, and a repair "
            "applied to a file from two places at once lands on one copy and is "
            "merged from the other."
        ),
        "tests/save/test_struct_interior.py": (
            "The site this item was opened on, and it is still live. A confinement "
            "arm compares a len() of the frozenset of struct words, and pytest "
            "reprs the frozenset INSIDE that len() - bypassing the counts-only "
            "__repr__ the sweep object carries specifically to prevent it. Two "
            "further arms in the same file were repaired at the site where they "
            "were found and the module was never swept, which is the "
            "instance-not-population defect this guard replaces. Same ownership "
            "reason as the entry above."
        ),
        "tests/test_facts_probe.py": (
            "Three arms render a FakeMachine path field. Every one of those fields "
            "is built under tmp_path, which on Windows sits inside the operator's "
            "profile directory, so the rendered value carries a home path and the "
            "account name. Outside the write-list of the change that added this "
            "guard."
        ),
    }
)


def _live(findings: tuple[Finding, ...]) -> list[Finding]:
    """The findings whose holder carries real save or machine data.

    Args:
        findings: The whole sweep.

    Returns:
        The live partition.
    """
    return [finding for finding in findings if finding.live]


def _latent(findings: tuple[Finding, ...]) -> list[Finding]:
    """The findings whose holder was built from a synthetic fixture.

    Args:
        findings: The whole sweep.

    Returns:
        The latent partition.
    """
    return [finding for finding in findings if not finding.live]


# ---------------------------------------------------------------------------
# The detector is proven able to fail, before anything it says is believed
# ---------------------------------------------------------------------------

RENDERED_SHAPES_SOURCE: Final = '''
"""One instance of every shape that reaches a withheld field."""


class Holder:
    words: frozenset[str]
    count: int

    def __repr__(self) -> str:
        return f"Holder(words={len(self.words)}, count={self.count})"


def make() -> Holder:
    return Holder()


def each_shape(holder: Holder) -> None:
    assert holder.words == frozenset()
    assert len(holder.words) == 0
    assert not holder.words
    assert holder.words and True
    assert sorted(holder.words) == []
    assert helper(holder.words) == 0
    assert holder.words in ({},)
    assert make().words == frozenset()
    alias = holder.words
    assert len(alias) == 0
'''

#: How many rendered sites the source above carries. A COUNT OF SHAPES, and the
#: assertion that consumes it names each one, so a shape lost from the detector
#: reddens by name rather than by arithmetic.
RENDERED_SHAPE_COUNT: Final = 9

SAFE_SHAPES_SOURCE: Final = '''
"""Every shape that must NOT be flagged, one instance each."""


class Holder:
    words: frozenset[str]
    count: int

    def __repr__(self) -> str:
        return f"Holder(words={len(self.words)}, count={self.count})"


def safe_shapes(holder: Holder, other: Holder) -> None:
    assert holder.count == 0
    assert holder == other
    assert [holder, other] == []
    total = len(holder.words)
    assert total == 0
    present = "x" in holder.words
    assert present is False
'''

OPAQUE_FIELD_SOURCE: Final = '''
"""A withheld field whose own type redacts itself is safe to render."""


class Inner:
    name: str

    def __repr__(self) -> str:
        return "Inner(<withheld>)"


class Outer:
    inner: Inner
    many: tuple[Inner, ...]
    words: frozenset[str]

    def __repr__(self) -> str:
        return "Outer()"


def render(outer: Outer) -> None:
    assert outer.inner is None
    assert outer.many == ()
    assert outer.words == frozenset()
'''


def test_the_detector_flags_every_rendered_shape():
    # WITHOUT THIS, A GREEN SWEEP IS A GREEN LIGHT WITH NOTHING BEHIND IT. Each
    # shape below reaches the withheld frozenset through a different rewriter
    # path, and losing any one of them would make the sweep quietly narrower.
    found = scan_source("<shapes>", RENDERED_SHAPES_SOURCE)
    shapes = len({finding.lineno for finding in found})
    assert shapes == RENDERED_SHAPE_COUNT, (
        f"the detector found {shapes} of {RENDERED_SHAPE_COUNT} rendered shapes. "
        "A shape it no longer sees is a shape a leak can be written in:\n" + describe(found)
    )
    fields = sorted({finding.field for finding in found})
    off_target = [name for name in fields if name != "words"]
    strays = len(off_target)
    assert strays == 0, f"flagged something other than the withheld field: {off_target}"


def test_no_safe_shape_is_flagged():
    # THE OTHER HALF, AND IT IS LOAD-BEARING. A detector that flags a disclosed
    # field, a whole object or the scalar-binding REMEDY makes whoever sees the
    # red either "fix" correct code or loosen this until it grades nothing.
    found = scan_source("<safe>", SAFE_SHAPES_SOURCE)
    flagged = len(found)
    assert flagged == 0, (
        "the detector flagged a shape that renders nothing the class withheld. "
        "The three that must stay green are a disclosed field, the whole object "
        "(whose redacting __repr__ is exactly what runs), and the remedy:\n" + describe(found)
    )


def test_a_withheld_field_whose_own_type_redacts_is_not_flagged():
    # Rendering a value whose repr is itself redacting discloses nothing. A
    # tuple of them is the same case, because a tuple's repr calls each
    # element's. The bare frozenset of strings in the same class is the control
    # that keeps this from being an assertion about an empty sweep.
    found = scan_source("<opaque>", OPAQUE_FIELD_SOURCE)
    fields = sorted(finding.field for finding in found)
    only_the_transparent_one = fields == ["words"]
    assert only_the_transparent_one, (
        "expected only the transparent field to be flagged, got "
        f"{fields}. A container of redacting classes renders redacted reprs"
    )


def test_the_explained_set_matches_the_rewriter_on_the_measured_shape():
    # THE SHAPE THIS ITEM WAS OPENED ON, read back from the rewriter's own
    # rules: the attribute inside the len() is rendered, which is why a
    # counts-only message does not save it.
    tree = ast.parse("assert len(sweep.miss_words) <= 2, 'counts only'")
    statement = tree.body[0]
    assert isinstance(statement, ast.Assert)
    rendered = sorted({ast.unparse(node) for node in explained(statement.test)})
    reaches_the_attribute = "sweep.miss_words" in rendered
    assert reaches_the_attribute, (
        "the explained set no longer contains the attribute inside the len(). "
        f"It contains {sorted(rendered)}, and the whole item is that pytest "
        "reprs that attribute"
    )


# ---------------------------------------------------------------------------
# The population is derived, and the derivation is not empty
# ---------------------------------------------------------------------------


def test_the_sweep_parses_a_population_that_is_not_empty():
    declarations, _ = scan_repo()
    holders = [entry for entry in declarations if entry.withheld]
    assert len(holders) > 1, (
        f"the sweep derived {len(holders)} classes with a withheld field. At one "
        "or fewer, every assertion below it is about nothing"
    )
    modules = {entry.module for entry in declarations}
    assert len(modules) > 1, (
        "every redacting class the sweep found sits in one file, so the tree walk "
        "is reading one module rather than the repository"
    )


def test_the_sweep_enumerates_rather_than_hardcoding_a_module_list():
    # THE ANTI-STALENESS PROPERTY, ASSERTED ON THE GUARD'S OWN SOURCE. CS-205
    # records a hand-written instance set that was stale before it was worked.
    # A path literal in the guard would be that set coming back.
    #
    # A LITERAL IS A ONE-TOKEN STRING ENDING IN .py. Prose ending in a module
    # name is a citation, not a population - the first spelling of this test
    # matched every docstring that names a sibling file and then RENDERED ALL OF
    # THEM into its own failure report, which is the channel this module is
    # about, written by hand, in the module that grades it.
    source = (REPO_ROOT / "tests" / "assertion_rendering_guard.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    named = sorted(
        {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.endswith(".py")
            and not node.value.split()[1:]
            and node.value != GIT_PY_GLOB
        }
    )
    count = len(named)
    assert count == 0, (
        f"the guard names {count} module path(s) rather than enumerating the "
        f"tree. A hand-listed population is stale before it is worked: {named}"
    )


def test_the_locator_seeds_match_the_reach_guard():
    # ONE VOCABULARY, TWO READERS. CS-433's defect was two hand-maintained lists
    # of the same kind of thing in two files, drifting until one guard named
    # none of what its sibling enumerated. The seeds are spelled here so this
    # module does not depend on the save package importing, and this is what
    # stops the second spelling drifting away from the first.
    agreed = LIBRARY_LOCATORS == reach_guard._LIBRARY_LOCATORS  # noqa: SLF001
    assert agreed, (
        "the locator seeds and the reach guard's own set have drifted. A name "
        "added there and forgotten here shrinks this guard's live partition "
        "silently, which is the direction that hides a disclosure"
    )


# ---------------------------------------------------------------------------
# The partition, and that it reads provenance rather than a path
# ---------------------------------------------------------------------------

PROVENANCE_SOURCE: Final = '''
"""One holder from the real library, one hand-authored, same assertion shape."""

from types import MappingProxyType


class Sweep:
    words: frozenset[str]

    def __repr__(self) -> str:
        return f"Sweep(words={len(self.words)})"


def _read_the_library() -> Sweep:
    return Sweep()


def _sweep_or_skip() -> Sweep:
    sweep = _read_the_library()
    return sweep


def test_from_the_library() -> None:
    sweep = _sweep_or_skip()
    assert len(sweep.words) == 0


def test_from_a_fixture() -> None:
    sweep = Sweep()
    assert len(sweep.words) == 0


_GRADED_LIBRARY_REACH = MappingProxyType({_read_the_library.__name__: "reads the library"})
'''


def test_the_partition_is_read_from_provenance_and_not_from_the_file():
    # TWO ASSERTIONS OF IDENTICAL SHAPE IN ONE FILE, one fed by a helper the
    # module DECLARES as reaching the library and one by a fixture built in the
    # process. A partition keyed on the path could not tell them apart; this one
    # must, or the live tier is grading the file name.
    found = scan_source("<provenance>", PROVENANCE_SOURCE)
    live = sorted(finding.lineno for finding in found if finding.live)
    latent = sorted(finding.lineno for finding in found if not finding.live)
    split_one_each = (len(live), len(latent)) == (1, 1)
    assert split_one_each, (
        f"expected one live finding and one latent, got {len(live)} live and "
        f"{len(latent)} latent. The partition is not reading the declared reach"
    )
    assert live[0] < latent[0], (
        "the live finding is not the one fed by the declared library reader, so "
        "the partition has inverted"
    )


def test_both_partitions_are_populated_on_the_real_tree():
    # A PARTITION WITH ONE EMPTY SIDE IS A CONSTANT WEARING A PREDICATE'S NAME.
    _, findings = scan_repo()
    live = _live(findings)
    latent = _latent(findings)
    both_sides_populated = bool(live) and bool(latent)
    assert both_sides_populated, (
        f"the sweep put {len(live)} findings live and {len(latent)} latent. With "
        "either side empty the partition below is not grading provenance at all"
    )


# ---------------------------------------------------------------------------
# THE SWEEP. This is what a new leak site lands on.
# ---------------------------------------------------------------------------


def test_no_live_assertion_renders_a_field_its_class_withheld():
    _, findings = scan_repo()
    live = _live(findings)
    unexpected = [finding for finding in live if finding.module not in LIVE_DISCLOSURE_RESIDUALS]
    reddening = len(unexpected)
    assert reddening == 0, (
        "an assertion renders a field its own class ships a __repr__ to WITHHOLD, "
        "and the holder carries real save or machine data. The message attached "
        "to the assert does not control this - pytest reprs the sub-expressions "
        "of the TEST independently of it (CLAUDE.md non-negotiables 11 and 12). "
        "Bind the aggregate, or the whole predicate, to a plain scalar BEFORE "
        "the assert:\n" + describe(unexpected)
    )
    # Non-vacuous in the other direction: a recorded residual that has been
    # repaired must lose its entry rather than stand as a silent exemption.
    still_red = {finding.module for finding in live}
    stale = sorted(path for path in LIVE_DISCLOSURE_RESIDUALS if path not in still_red)
    surviving = len(stale)
    assert surviving == 0, f"these residuals were repaired; delete their entries: {stale}"


def test_every_recorded_residual_names_a_file_that_exists():
    missing = sorted(path for path in LIVE_DISCLOSURE_RESIDUALS if not (REPO_ROOT / path).is_file())
    absent = len(missing)
    assert absent == 0, f"a residual names a file that is not in the tree: {missing}"


def test_the_latent_population_is_visible_rather_than_absent():
    # The latent tier is REPORTED, not asserted to zero: those holders are built
    # from bytes this process hand-authored, and rewriting an equality against a
    # hand-authored constant would delete the expected-versus-actual diff that
    # is the arm's whole diagnostic value while buying no privacy. What must
    # stay true is that every one of them sits in a file the sweep can still
    # find, so the record cannot quietly become about nothing.
    _, findings = scan_repo()
    latent = _latent(findings)
    missing = sorted({f.module for f in latent if not (REPO_ROOT / f.module).is_file()})
    unreadable = len(missing)
    assert unreadable == 0, f"the sweep reported a finding in a file it cannot read: {missing}"


# ---------------------------------------------------------------------------
# The forced arms - graded on what pytest ACTUALLY PRINTS
# ---------------------------------------------------------------------------


def _representative_arms() -> list[tuple[str, str, str, str]]:
    """One forced arm per guarded module, derived from the live findings.

    Returns:
        Module, holder class, withheld field and planted token, one tuple per
        module carrying a live finding. The token cycles through the three
        classes the acceptance names so every one is exercised.
    """
    _, findings = scan_repo()
    chosen: dict[str, Finding] = {}
    for finding in sorted(_live(findings), key=lambda f: (f.module, f.lineno)):
        chosen.setdefault(finding.module, finding)
    arms = []
    for index, (module, finding) in enumerate(sorted(chosen.items())):
        arms.append((module, finding.holder, finding.field, SENSITIVE_TOKENS[index % 3]))
    return arms


def _arm_source(index: int, holder: str, field: str, token: str, *, remedied: bool) -> str:
    """The text of one forced arm, in the leaking form or the remedied one.

    THE TOKEN IS BOUND AT MODULE SCOPE AND NAMED IN THE BODY, never spelled
    inside the failing function. MEASURED: the first spelling planted it as a
    literal in the test body, and the REMEDIED arm leaked all three tokens
    anyway - pytest renders the failing function's own SOURCE LINES above the
    assertion, so the literal was printed by the traceback rather than by the
    rewriter. That is a second channel with a second remedy, and grading it as
    if it were this one would have reported the fix as failing when it worked.
    Module-scope bindings are not in the rendered frame.

    Args:
        index: Distinguishes the generated names within one sandbox module.
        holder: The redacting class the real finding names.
        field: The withheld field the real finding names.
        token: The synthetic value planted inside that field.
        remedied: When True, the aggregate is bound to a scalar first.

    Returns:
        Python source for one class, one planted value and one failing test.
    """
    name = f"Holder{index}"
    planted = f"PLANTED_{index}"
    body = (
        f'    count = len(item.{field})\n    assert count <= 0, f"{{count}} - counts only"\n'
        if remedied
        else f'    assert len(item.{field}) <= 0, f"{{len(item.{field})}} - counts only"\n'
    )
    return (
        f"class {name}:\n"
        f"    def __init__(self, value):\n"
        f"        self.{field} = value\n"
        f"    def __repr__(self):\n"
        f'        return f"{holder}({field}={{len(self.{field})}})"\n'
        f"\n"
        f"{planted} = frozenset({{{token!r}}})\n"
        f"\n"
        f"def test_forced_arm_{index}():\n"
        f"    item = {name}({planted})\n"
        f"{body}"
    )


def _sandbox_module(*, remedied: bool) -> str:
    """A whole sandbox module: one forced arm per guarded module.

    Args:
        remedied: Whether each arm binds its aggregate to a scalar first.

    Returns:
        Python source.
    """
    parts = ['"""Generated by tests/test_assertion_rendering.py - synthetic only."""\n']
    for index, (_, holder, field, token) in enumerate(_representative_arms()):
        parts.append(_arm_source(index, holder, field, token, remedied=remedied))
    return "\n\n".join(parts)


def _run_sandbox(root: Path, *, remedied: bool) -> tuple[int, str]:
    """Write the sandbox and run real pytest over it.

    The sandbox is isolated from this repository deliberately: no conftest, no
    rootdir here, no cache. The subject is what the REWRITER prints, and a
    redactor running over the top would grade the redactor instead.

    Args:
        root: A directory to write into.
        remedied: Which form of the arms to write.

    Returns:
        pytest's own exit code, and its combined output.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "test_forced_arms.py"
    target.write_bytes(_sandbox_module(remedied=remedied).encode("ascii"))
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(root),
            "-p",
            "no:randomly",
        ],
        capture_output=True,
        check=False,
        cwd=str(root),
        timeout=SUBPROCESS_TIMEOUT,
    )
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    return (completed.returncode, text)


@pytest.fixture(scope="module")
def leaking_arms(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The forced arms in the shape the tree ships - the CONTROL."""
    return _run_sandbox(tmp_path_factory.mktemp("cs850_leaking"), remedied=False)


@pytest.fixture(scope="module")
def remedied_arms(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, str]:
    """The same arms with the aggregate bound to a scalar first."""
    return _run_sandbox(tmp_path_factory.mktemp("cs850_remedied"), remedied=True)


def test_the_forced_arms_actually_ran_and_failed(leaking_arms: tuple[int, str]):
    # DETECTED IS NOT CRASHED. A sandbox that died during collection renders no
    # planted token either, and that is not the property under test.
    code, output = leaking_arms
    arms = len(_representative_arms())
    assert arms > 1, f"only {arms} guarded modules were derived; the proof would be about one file"
    assert code == PYTEST_TESTS_FAILED, (
        f"the control sandbox exited {code}; expected {PYTEST_TESTS_FAILED}, "
        "which is 'tests ran and failed'"
    )
    collected = f"collected {arms} item" in output
    assert collected, f"the control sandbox did not collect all {arms} forced arms"


def test_the_unremedied_arms_render_every_planted_token(leaking_arms: tuple[int, str]):
    # THE CONTROL, AND THE WHOLE OF THIS MODULE RESTS ON IT. If a planted token
    # is NOT rendered here, the grep below cannot distinguish a remedy that
    # worked from a harness that never looked.
    _, output = leaking_arms
    planted = {token for _, _, _, token in _representative_arms()}
    missing = sorted(token for token in planted if token not in output)
    unrendered = len(missing)
    assert unrendered == 0, (
        f"{len(missing)} of {len(planted)} planted tokens were NOT rendered by "
        "the unremedied arms, so this module is not measuring the channel it "
        "claims to measure. The tokens are synthetic and safe to name: " + repr(missing)
    )


def test_the_remedied_arms_render_no_planted_token(remedied_arms: tuple[int, str]):
    # THE ACCEPTANCE, GRADED ON THE RENDERED OUTPUT. Same arms, same failures,
    # the aggregate bound to a plain scalar before the assert.
    code, output = remedied_arms
    assert code == PYTEST_TESTS_FAILED, (
        f"the remedied sandbox exited {code}; it must still FAIL, or a clean "
        "grep only proves the arms stopped running"
    )
    planted = {token for _, _, _, token in _representative_arms()}
    leaked = sorted(token for token in planted if token in output)
    survivors = len(leaked)
    assert survivors == 0, (
        f"{len(leaked)} planted tokens survived the remedy into the rendered "
        "failure report. Binding the aggregate to a scalar is the whole fix, so "
        "a token still present means the rendered expression still holds the "
        "container: " + repr(leaked)
    )


def test_every_sensitive_class_is_covered_by_the_forced_arms():
    # The acceptance names three classes. A proof that plants only one of them
    # and reports a pass is a proof about one class wearing the name of three.
    planted = {token for _, _, _, token in _representative_arms()}
    uncovered = sorted(token for token in SENSITIVE_TOKENS if token not in planted)
    gaps = len(uncovered)
    assert gaps == 0, (
        "the forced arms do not plant every class the acceptance names - a "
        "save-derived name, a home path and an account directory. Uncovered: " + repr(uncovered)
    )


# ---------------------------------------------------------------------------
# Why the runtime redactor is not the remedy for the third class
# ---------------------------------------------------------------------------


def test_the_runtime_redactor_cannot_reach_a_save_derived_name():
    # MEASURED, NOT ARGUED, and it is the reason this guard is static. The
    # conftest redactor derives its spellings from THIS MACHINE - the home
    # directory and the account name - so it catches two of the three classes
    # wherever they are rendered. A world name, a save name or a decoded struct
    # word is derivable from nothing on this machine, so no redactor can know
    # it, and only a guard over the ASSERTION can stop it being printed.
    #
    # The machine's own spellings are derived at run time and never echoed: what
    # is reported below is a verdict and a length, never a value.
    home = str(Path.home())
    assert len(home) >= MIN_HOME_SPELLING, (
        "this machine's home path is too short to be personal data, so the "
        "measurement below would be vacuous"
    )
    redacted_home = redact_personal_data(home)
    home_survived = home in redacted_home
    assert not home_survived, (
        "the conftest redactor did not replace this machine's home path, so the "
        "premise of this measurement - that two of the three classes have a "
        "runtime net - does not hold on this machine"
    )
    assert REDACTED_HOME in redacted_home or REDACTED_USER in redacted_home, (
        "the redactor changed the home path into something that carries neither "
        "placeholder, so what it did is not the redaction this measures"
    )

    # And now the third class, which no runtime rule can derive.
    name_survived = SAVE_NAME_TOKEN in redact_personal_data(SAVE_NAME_TOKEN)
    assert name_survived, (
        "the redactor replaced a synthetic save-derived name. If that is now "
        "true, this module's premise has changed and the static guard's "
        "justification must be rewritten rather than left standing"
    )
