"""CS-850 - no shipped assertion renders a value its own class declared withheld.

THE CHANNEL IS NOT THE MESSAGE, and that single sentence is the whole item.
pytest rewrites ``assert TEST, MESSAGE`` and renders the sub-expressions of TEST
with their own reprs, independently of MESSAGE. The part a reviewer reads is the
part that does not control what is printed. ``tests/assertion_rendering_guard``
carries the mechanism in full; this module is what drives it and what proves it.

WHAT IS DERIVED, AND WHAT IS NOT. The POPULATION is derived twice over: a class
that ships a hand-written ``__repr__`` in order to withhold its contents has
DECLARED its fields unsafe to render, which fields are withheld is read out of
that ``__repr__``'s body, and which assertions reach one is read out of pytest's
own rewriting rules. No module, class or field is named anywhere, so a redacting
class added tomorrow is covered the moment it exists. What IS written down is
vocabulary - which wrappers mask, which types are scalars, which fixtures carry
this machine - and each of those is a partition with a test on it rather than a
list of the things being graded. CS-205 records why the distinction matters: a
hand-listed POPULATION in this project went stale between being written and
being worked, every time.

AND THE POPULATION IS A PROXY FOR THE ACCEPTANCE'S, NOT THE SAME SET. The
acceptance names three kinds of DATA. This names a set of DECLARATIONS. Where
they differ is measured, not guessed - see the boundary paragraph above and the
pinned probes in the test module.

PROVEN BY WHAT PYTEST ACTUALLY PRINTS. Reading the message text would grade
exactly the half of the channel that is not the channel, so the proof below
forces one arm per covered module to FAIL inside a real pytest subprocess, with
a synthetic token planted in the withheld field, and greps the rendered output
for it.

WHAT THOSE ARMS PROVE, STATED EXACTLY. Each runs a GENERATED stand-in carrying
the module's own (class, field) shape and no imports, so what is measured is
that pytest's rewriter renders that shape - not that the shipped code path
does. The shipped path is graded statically by the sweep; these arms are what
stop the sweep's premise from being an assumption.

Three token classes are planted - a save-derived name, a home path and an
account directory - and
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

from tests import assertion_rendering_guard as guard
from tests.assertion_rendering_guard import (
    CONTENT_REDUCERS,
    CONTENT_TRANSPARENT,
    LIBRARY_LOCATORS,
    REACH_PRIMITIVES,
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
#:
#: EMPTY, AND THAT IS THE DESIGNED OUTCOME. The sole entry named
#: tests/save/test_struct_interior.py, whose confinement arm was repaired by
#: the CS-829 merge. The both-directions assertion went RED on that merge and
#: is what required this entry to be deleted rather than left to rot.
LIVE_DISCLOSURE_RESIDUALS: Final[Mapping[str, str]] = MappingProxyType({})


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


def test_the_guard_names_no_module_path_of_its_own():
    # WHAT THIS ENFORCES, STATED EXACTLY, because the name it used to carry
    # claimed more than it checks. It forbids a MODULE PATH literal - a
    # single-token string ending in .py - and nothing else. The guard DOES ship
    # vocabularies: CONTENT_TRANSPARENT, CONTENT_REDUCERS, SCALAR_TYPES,
    # PASS_THROUGH_TYPES, MACHINE_FIXTURES, LIBRARY_LOCATORS and
    # REACH_PRIMITIVES. Those are language and platform vocabularies, each
    # partitioned and each pinned by a test; they are not a list of the things
    # being graded. The population - modules, classes, fields - is what carries
    # no list, and this is the half of that claim a machine can check.
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


def test_the_liveness_flag_is_not_a_constant():
    # A PARTITION WITH ONE EMPTY SIDE IS A CONSTANT WEARING A PREDICATE'S NAME -
    # and the first spelling of this test proved that against the REAL TREE, by
    # requiring the live side to be non-empty. So a tree with zero live leaks
    # turned this module RED, and a green run still certified that at least one
    # module leaks. MEASURED: with every live flag cleared - which is exactly
    # the tree that repairing the last residual produces - it reported "0
    # findings live and 206 latent" and failed.
    #
    # THAT IS THE SAME DEFECT AS DERIVING THE FORCED ARMS FROM LIVE FINDINGS. It
    # moved function and did not leave the module. A guard must not require the
    # defect to exist, anywhere in it, so non-vacuity is proven HERE against
    # SYNTHETIC sources whose verdicts cannot change when the tree is repaired.
    verdicts: set[bool] = set()
    for label, source in (
        ("provenance", PROVENANCE_SOURCE),
        ("declared", DECLARED_SOURCE),
        ("undeclared", UNDECLARED_SOURCE),
    ):
        verdicts.update(finding.live for finding in scan_source(f"<{label}>", source))
    takes_both_values = verdicts == {True, False}
    assert takes_both_values, (
        f"the liveness flag took the values {sorted(verdicts)} across the "
        "synthetic corpus. With one value it is a constant, and every "
        "partition assertion in this module is about nothing"
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


def _covered_modules() -> list[tuple[str, str, str]]:
    """One (module, class, withheld field) per module this guard COVERS.

    DERIVED FROM THE DECLARATIONS, NEVER FROM THE FINDINGS, and that is the
    whole of defect 1. Deriving the forced arms from LIVE FINDINGS made this
    module's proof ANTI-MONOTONE in the property it certifies: three live
    modules were needed to plant the three sensitive classes, so repairing a
    leak dropped the count and turned the acceptance RED, and a green run
    therefore certified that at least three modules still leaked. A tier 1
    privacy guard whose green state requires the defect to exist punishes the
    next person who fixes one.

    The declarations do not shrink when a leak is repaired - a class keeps its
    redacting ``__repr__`` - so this population is stable under exactly the
    change the guard exists to cause.

    Returns:
        The first withheld field of the first redacting class in each module
        that ships one, sorted so the arm-to-token assignment is deterministic.
    """
    declarations, _ = scan_repo()
    chosen: dict[str, tuple[str, str]] = {}
    for entry in sorted(declarations, key=lambda entry: (entry.module, entry.lineno)):
        if entry.withheld:
            chosen.setdefault(entry.module, (entry.name, sorted(entry.withheld)[0]))
    return [(module, holder, field) for module, (holder, field) in sorted(chosen.items())]


def _representative_arms() -> list[tuple[str, str, str, str]]:
    """One forced arm per COVERED module, with a sensitive token planted in it.

    Returns:
        Module, holder class, withheld field and planted token. The token cycles
        through the three classes the acceptance names so every one is
        exercised.
    """
    return [
        (module, holder, field, SENSITIVE_TOKENS[index % len(SENSITIVE_TOKENS)])
        for index, (module, holder, field) in enumerate(_covered_modules())
    ]


def test_the_forced_arms_survive_every_leak_being_repaired():
    # THE PROOF MUST NOT BE ANTI-MONOTONE IN THE PROPERTY IT CERTIFIES.
    # Measured on the previous spelling: live=3 green, live=2 red, live=1 red,
    # live=0 red. Repairing a leak broke the proof that leaks are repaired, and
    # a sibling slice hardening seven sites that were never leaks would have
    # done it at the merge rather than hypothetically.
    _, findings = scan_repo()
    leaking = {finding.module for finding in findings if finding.live}
    covered = {module for module, _, _, _ in _representative_arms()}
    survivors = sorted(covered - leaking)
    remaining = len(survivors)
    assert remaining >= len(SENSITIVE_TOKENS), (
        f"only {remaining} of {len(covered)} forced arms sit in a module with "
        f"no live finding, and {len(SENSITIVE_TOKENS)} are needed to plant one "
        "of each sensitive class. Repairing the remaining leaks would turn this "
        "module's own acceptance red"
    )


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


# ---------------------------------------------------------------------------
# The mask rule - what a redacting __repr__ actually withholds
# ---------------------------------------------------------------------------

MASK_RULE_SOURCE: Final = """
\"\"\"Three renderings: one masked, one transformed, one bare.\"\"\"

MASK_PREFIX = "sha256:"


def masked(token):
    if not token:
        return MASK_PREFIX
    digest = sha256(token).hexdigest()
    return MASK_PREFIX + digest[:8]


class Holder:
    counted: frozenset[str]
    transformed: dict[str, int]
    digested: str
    bare: int

    def __repr__(self) -> str:
        return (
            f"Holder(counted={len(self.counted)}, "
            f"transformed={dict(sorted(self.transformed.items()))}, "
            f"digested={masked(self.digested)!r}, "
            f"bare={self.bare})"
        )


def render(holder: Holder) -> None:
    assert holder.counted == frozenset()
    assert holder.transformed == {}
    assert holder.digested == ""
    assert holder.bare == 0
"""


def test_a_container_transform_in_a_repr_is_disclosure_and_not_a_mask():
    # THE FALSE-POSITIVE HALF, and it is the one that gets a guard ignored.
    # `len(x)` and `sum(x)` cannot carry their argument's contents. `dict(
    # sorted(x.items()))` renders every key and every value, so a class writing
    # that has DISCLOSED the field and an assertion rendering it discloses
    # nothing new. Reading any wrapping call as a mask reported seven leaks in
    # a class whose own docstring reads "COUNTS ONLY. No field here can hold a
    # path, a name, a word or a value" - and every one of them was wrong.
    found = scan_source("<mask>", MASK_RULE_SOURCE)
    flagged = sorted({finding.field for finding in found})
    assert flagged == ["counted", "digested"], (
        "expected only the count-masked and the digest-masked fields to be "
        f"withheld; got {flagged}. A container transform and a bare "
        "interpolation are both disclosure"
    )


def test_a_digest_helper_is_derived_as_a_mask_rather_than_named():
    # `masked_token()` in clockspeed/save/header.py is a real mask and is not a
    # builtin, so a rule that knows only builtins reports the world token as
    # disclosed and stops grading the one field that matters most. It is
    # derived: no return in that helper reaches its parameter except through a
    # hashing primitive, and that is checkable rather than declared.
    found = scan_source("<mask>", MASK_RULE_SOURCE)
    digested = [finding for finding in found if finding.field == "digested"]
    reached = len(digested)
    assert reached == 1, (
        f"the digest-masked field yielded {reached} findings, expected 1. A "
        "helper whose returns never carry its parameter through is a mask"
    )


# ---------------------------------------------------------------------------
# The evasion shapes - one token each, all inside the declared population
# ---------------------------------------------------------------------------

EVASION_SOURCE: Final = """
\"\"\"Six renderings of one withheld field, none of them the plain form.\"\"\"


class Sweep:
    words: frozenset[str]
    count: int

    def __repr__(self) -> str:
        return f"Sweep(words={len(self.words)}, count={self.count})"


class Model:
    sweep: Sweep
    count: int

    def __repr__(self) -> str:
        return f"Model(count={self.count})"


def interpolated(sweep: Sweep) -> None:
    assert f"{sweep.words}" == ""


def walrused(sweep: Sweep) -> None:
    assert len(words := sweep.words) == 0


def chain_assigned(sweep: Sweep) -> None:
    first = second = sweep.words
    assert len(first) == 0
    assert len(second) == 0


def tuple_assigned(sweep: Sweep) -> None:
    words, other = sweep.words, None
    assert len(words) == 0


def looped(one: Sweep, two: Sweep) -> None:
    for sweep in (one, two):
        assert len(sweep.words) == 0


def chained(model: Model) -> None:
    assert len(model.sweep.words) == 0
"""

#: The six evasion shapes, named so a lost one reddens by name.
EVASION_FUNCTIONS: Final = (
    "interpolated",
    "walrused",
    "chain_assigned",
    "tuple_assigned",
    "looped",
    "chained",
)


def test_the_detector_flags_every_evasion_shape():
    # MEASURED UNDER REAL PYTEST: all six render the field's own repr into the
    # failure report past a counts-only message. An adversary found the
    # detector caught ONE. Four of the five it missed are DIRECT bindings, so
    # they were never covered by the one-hop limit this module admits to - they
    # were undisclosed.
    found = scan_source("<evasion>", EVASION_SOURCE)
    lines = {finding.lineno for finding in found}
    caught = len(lines)
    expected = len(EVASION_FUNCTIONS) + 1
    assert caught >= expected, (
        f"the detector reached {caught} of the {expected} rendered sites in "
        "the evasion probe. Each shape below renders the same frozenset:\n"
        + "\n".join(f"  {name}" for name in EVASION_FUNCTIONS)
    )
    fields = sorted({finding.field for finding in found})
    strays = [name for name in fields if name != "words"]
    assert not strays, f"flagged something other than the withheld field: {strays}"


# ---------------------------------------------------------------------------
# Under-declaration must fail loudly, not demote a live leak to latent
# ---------------------------------------------------------------------------

#: A module that genuinely REACHES - it opens a discovered path - and so owes a
#: declaration. A module that reaches nothing owes none, and grading its silence
#: as under-declaration is a different defect wearing the same word.
UNDECLARED_SOURCE: Final = """
\"\"\"A module that reads the library and declares nothing about it.\"\"\"


class Sweep:
    words: frozenset[str]

    def __repr__(self) -> str:
        return f"Sweep(words={len(self.words)})"


def _read_the_library() -> Sweep:
    for path in resolve_save_root().iterdir():
        open(path, "rb").close()
    return Sweep()


def test_it() -> None:
    sweep = _read_the_library()
    assert len(sweep.words) == 0
"""

MISDECLARED_SOURCE: Final = (
    UNDECLARED_SOURCE
    + """

_GRADED_LIBRARY_REACHES = {"_read_the_library": "misspelt binding name"}
"""
)

UNREADABLE_SOURCE: Final = (
    UNDECLARED_SOURCE
    + """

_GRADED_LIBRARY_REACH = frozenset({"_read_the_library"})
"""
)

#: The positive control for the rule above: the same reach, DECLARED readably.
#: Without it the test is satisfied by grading every module live, and the
#: partition has quietly stopped existing.
DECLARED_SOURCE: Final = (
    UNDECLARED_SOURCE
    + """

def test_from_a_fixture() -> None:
    sweep = Sweep()
    assert len(sweep.words) == 0


_GRADED_LIBRARY_REACH = {"_read_the_library": "reads the library"}
"""
)


def test_a_module_that_declares_no_reach_defaults_to_live():
    # THE PARTITION RESTS ON A SELF-DECLARATION, so under-declaration must cost
    # something. Measured on identical source with only the declaration varied,
    # an absent one, a misspelt binding and a `{**BASE}` merge whose key reads
    # as None each demoted a live leak to latent - silently, and in the
    # direction that hides a disclosure.
    for label, source in (
        ("absent", UNDECLARED_SOURCE),
        ("misspelt", MISDECLARED_SOURCE),
        ("unreadable", UNREADABLE_SOURCE),
    ):
        found = scan_source(f"<{label}>", source)
        live = [finding for finding in found if finding.live]
        graded_live = len(live)
        all_live = graded_live == len(found)
        assert graded_live > 0, f"the {label} probe found nothing, so it grades nothing"
        assert all_live, (
            f"the {label} declaration produced {graded_live} live of "
            f"{len(found)} findings. Latent is a claim, and a module that "
            "makes no readable claim has not made it"
        )


def test_a_readable_declaration_is_what_earns_the_latent_grade():
    # The other direction, or the test above is satisfied by grading
    # everything live and the partition has stopped existing.
    found = scan_source("<provenance>", PROVENANCE_SOURCE)
    latent = [finding for finding in found if not finding.live]
    earned = len(latent)
    assert earned == 1, (
        f"a readable declaration earned {earned} latent findings, expected 1. "
        "With none, the partition is a constant wearing a predicate's name"
    )


# ---------------------------------------------------------------------------
# THE BOUNDARY, PINNED. These shapes are NOT covered, and that is measured.
# ---------------------------------------------------------------------------

UNCOVERED_SOURCES: Final = MappingProxyType(
    {
        "a frozen dataclass with the DEFAULT repr": """
from dataclasses import dataclass

@dataclass(frozen=True)
class Plain:
    world_name: str

def render(plain: Plain) -> None:
    assert plain.world_name == ""
""",
        "a bare str holding a world name": """
def render(world_name: str) -> None:
    assert world_name == ""
""",
        "a pathlib Path from tmp_path": """
from pathlib import Path

def render(tmp_path: Path) -> None:
    assert tmp_path.exists()
""",
        "a plain dict, list or set": """
def render(names: dict[str, int]) -> None:
    assert names == {}
""",
        "a NamedTuple with no hand-written repr": """
from typing import NamedTuple

class Machine(NamedTuple):
    home: str

def render(machine: Machine) -> None:
    assert machine.home == ""
""",
        "a value returned straight from a fixture with no class": """
import pytest

@pytest.fixture
def world_name(tmp_path) -> str:
    return str(tmp_path)

def test_it(world_name) -> None:
    assert world_name == ""
""",
        "fields assigned in __init__ with no class-level annotation": """
class Holder:
    def __init__(self, words):
        self.words = words

    def __repr__(self) -> str:
        return f"Holder(words={len(self.words)})"

def render(holder: Holder) -> None:
    assert len(holder.words) == 0
""",
    }
)


def test_the_uncovered_shapes_are_pinned_rather_than_silently_absent():
    # THE POPULATION IS STRUCTURAL AND THE ACCEPTANCE'S IS NOT. The acceptance
    # names three kinds of DATA; this guard derives a set of DECLARATIONS, and
    # a value that is personal but whose holder never declared a redacting
    # __repr__ is invisible here because there is no declaration to bypass.
    # Every source below carries a save-derived name or a home path and yields
    # ZERO findings. That is recorded as the guard's boundary rather than left
    # for the next adversary to discover, and the one shape that CAN be closed
    # without a type checker - fields assigned in __init__ - is closed, so its
    # entry here is asserted to have moved rather than left standing.
    still_uncovered = []
    for label, source in UNCOVERED_SOURCES.items():
        if not scan_source(f"<{label}>", source):
            still_uncovered.append(label)
    closed = sorted(set(UNCOVERED_SOURCES) - set(still_uncovered))
    assert closed == ["fields assigned in __init__ with no class-level annotation"], (
        "the pinned boundary has moved. Shapes now COVERED that this record "
        f"still calls uncovered: {closed}. Update the record - a boundary "
        "statement that is no longer true is worse than none"
    )


# ---------------------------------------------------------------------------
# The vocabularies are partitions, and each is pinned
# ---------------------------------------------------------------------------


def test_the_reach_primitives_match_the_reach_guard():
    # ONE VOCABULARY, TWO READERS, on the same terms as the locator seeds.
    # These decide only whether a module OWED a reach declaration, and reading
    # a shrunken set would call a reaching module silent - the direction that
    # lets an under-declared module keep a latent grade.
    agreed = REACH_PRIMITIVES == reach_guard._REACHES_THE_LIBRARY  # noqa: SLF001
    assert agreed, (
        "the reach primitives and the reach guard's own set have drifted. A "
        "name added there and forgotten here shrinks the set of modules this "
        "guard holds to a declaration"
    )


def test_the_wrapper_vocabularies_do_not_overlap():
    # A name in BOTH would make the mask verdict depend on which set was
    # consulted first, which is a coin toss wearing a rule's name.
    both = sorted(CONTENT_TRANSPARENT & CONTENT_REDUCERS)
    overlap = len(both)
    assert overlap == 0, f"these names are classed as both mask and disclosure: {both}"


SCALAR_FIELD_SOURCE: Final = """
\"\"\"A withheld field that is a number discloses a number.\"\"\"


class Table:
    consumed: int
    declared: int
    ratio: float
    words: frozenset[str]

    def __repr__(self) -> str:
        return f"Table(words={len(self.words)})"


def render(table: Table) -> None:
    assert table.consumed == table.declared
    assert table.ratio == 0.0
    assert table.words == frozenset()
"""


def test_a_withheld_field_that_is_a_number_is_not_a_finding():
    # WITHHELD IS NOT THE SAME CLAIM AS DISCLOSING. A __repr__ may leave an int
    # out for brevity; that does not make an assertion over it a leak. Before
    # this rule the guard reported `assert table.body_consumed ==
    # table.declared_body_length` - two integers - as a live disclosure.
    found = scan_source("<scalar>", SCALAR_FIELD_SOURCE)
    flagged = sorted({finding.field for finding in found})
    assert flagged == ["words"], (
        f"expected only the string-bearing field to be flagged, got {flagged}"
    )


COMPREHENSION_SOURCE: Final = """
\"\"\"A generator renders a memory address; a comprehension renders its result.\"\"\"


class Sweep:
    words: frozenset[str]

    def __repr__(self) -> str:
        return f"Sweep(words={len(self.words)})"


def opaque(sweep: Sweep) -> None:
    assert not any(name for name in sweep.words)


def transparent(sweep: Sweep) -> None:
    assert [name.upper() for name in sweep.words] == []
"""


def test_a_generator_is_opaque_and_a_comprehension_is_not():
    # MEASURED UNDER REAL PYTEST RATHER THAN REASONED ABOUT, because the two
    # look identical in the source. `any(x for x in sweep.words)` renders
    # "<generator object ... at 0x...>" and carries nothing; the list
    # comprehension beside it renders its RESULT, which carries what the field
    # held. Reading them alike cost three false findings in one file.
    found = scan_source("<comprehension>", COMPREHENSION_SOURCE)
    lines = sorted({finding.lineno for finding in found})
    caught = len(lines)
    assert caught == 1, (
        f"expected exactly the comprehension to be flagged, got {caught} "
        f"findings at lines {lines}. A generator's repr is a memory address"
    )


def test_a_readable_declaration_on_a_reaching_module_earns_latent():
    # THE POSITIVE CONTROL for the under-declaration rule, and it is the SAME
    # REACHING MODULE as the three probes above with only the declaration added.
    # Two arms of identical shape: one holder from the DECLARED reader, which
    # must stay live, and one built in the process, which the declaration is
    # what earns latent for. Without this the under-declaration rule is
    # satisfied by grading every module live, and the partition has quietly
    # stopped existing.
    found = scan_source("<declared>", DECLARED_SOURCE)
    live = sorted(finding.lineno for finding in found if finding.live)
    latent = sorted(finding.lineno for finding in found if not finding.live)
    split_one_each = (len(live), len(latent)) == (1, 1)
    assert split_one_each, (
        f"the declared reaching module split {len(live)} live and "
        f"{len(latent)} latent, expected one of each. Declaring correctly has "
        "to buy something, and it must not buy the declared reader a pass"
    )
    assert live[0] < latent[0], (
        "the live finding is not the one fed by the declared reader, so the partition has inverted"
    )


def test_the_declaration_reader_is_the_reach_guard_own_one():
    # THE COMPREHENSION SPELLING IS REAL AND IS SHIPPED. A literal-only reader
    # called a module UNDER-DECLARED whose declaration is a comprehension over a
    # table of (label, function) pairs, and graded 36 of its assertions live on
    # the strength of it. reach_guard owns that grammar and is refuted over it;
    # this asserts the borrowed reader is actually reachable, so the fallback
    # cannot become the silent normal case.
    borrowed = guard._borrowed_declaration_reader()  # noqa: SLF001
    assert borrowed is not None, (
        "the reach guard's declaration reader did not load, so every module "
        "whose declaration is not a plain dict literal is being graded "
        "under-declared. That is louder than wrong, but it is still wrong"
    )


def test_an_imported_mask_is_resolved_across_modules():
    # A SURVIVING MUTANT IS WHAT CAUGHT THIS, and nothing else would have.
    # `masked_token` is defined in clockspeed/save/header.py and IMPORTED by
    # clockspeed/save/world.py, so a reader resolving only a module's own
    # functions could not see that `f"{masked_token(self.token)!r}"` masks
    # anything - and graded the world token DISCLOSED. A re-introduced leak over
    # that exact field then passed the sweep in silence, and a mutation that
    # survives looks exactly like one that never applied.
    #
    # Asserted as a DIFFERENCE rather than by naming the class, so it stays a
    # derived property: resolving tree-wide must withhold strictly more than
    # resolving module by module, or the cross-module hop is buying nothing.
    declarations, _ = scan_repo()
    tree_wide = sum(len(entry.withheld) for entry in declarations)

    trees = {}
    for relative in guard.tracked_python_files():
        source = (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        trees[relative] = ast.parse(source)
    opaque = frozenset(
        node.name
        for parsed in trees.values()
        for node in ast.walk(parsed)
        if isinstance(node, ast.ClassDef) and guard.repr_method(node) is not None
    )
    local_only = sum(
        len(entry.withheld)
        for relative, parsed in trees.items()
        for entry in guard.redacting_classes(relative, parsed, opaque)
    )

    gained = tree_wide - local_only
    assert gained > 0, (
        f"resolving masks tree-wide withheld {tree_wide} fields and resolving "
        f"module by module withheld {local_only}. With no difference the "
        "cross-module hop is dead code, and an imported mask is being read as "
        "disclosure somewhere"
    )


BOOLEAN_MASK_SOURCE: Final = """
\"\"\"Three masks that render a boolean or a literal word, not a value.\"\"\"


class Holder:
    struct_word: str | None
    value: str | None
    super_name: str | None
    words: frozenset[str]

    def __repr__(self) -> str:
        return (
            f"Holder(struct_word={self.struct_word is not None}, "
            f"decoded={self.value is not None}, "
            f"super={'present' if self.super_name is not None else 'absent'}, "
            f"any_words={'yes' if self.words else 'no'})"
        )


def render(holder: Holder) -> None:
    assert holder.struct_word == ""
    assert holder.value == ""
    assert holder.super_name == ""
    assert holder.words == frozenset()
"""

#: The four fields the source above masks. Named so a lost one reddens by name.
BOOLEAN_MASKED_FIELDS: Final = ("struct_word", "super_name", "value", "words")


def test_a_comparison_and_a_conditional_are_masks():
    # THREE OF THESE ARE SHIPPED SHAPES, and the mask rule stopped reading them
    # when it was rewritten to walk the parent chain for a reducing CALL - an
    # ast.Compare is not a call and neither is an ast.IfExp.
    # ContainerValue.struct_word, ContainerElement.value and Schema.super_name
    # each render a boolean or a literal word and each went WITHHELD ->
    # DISCLOSED, so every assertion over them stopped being graded.
    # ContainerValue.struct_word is a decoded struct type word off a real save -
    # the same data class as this module's one recorded residual.
    found = scan_source("<boolean>", BOOLEAN_MASK_SOURCE)
    flagged = sorted({finding.field for finding in found})
    missing = [name for name in BOOLEAN_MASKED_FIELDS if name not in flagged]
    unseen = len(missing)
    assert unseen == 0, (
        f"{unseen} of {len(BOOLEAN_MASKED_FIELDS)} boolean-masked fields are "
        f"being read as DISCLOSED, so nothing grades them: {missing}. A repr "
        "that prints `x is not None` prints a boolean"
    )


ELEMENT_REDUCTION_SOURCE: Final = """
\"\"\"A repr masking with max(), which returns an element rather than a count.\"\"\"


class Holder:
    words: frozenset[str]

    def __repr__(self) -> str:
        return f"Holder(widest={max(self.words)})"


def render(holder: Holder) -> None:
    assert holder.words == frozenset()
"""


def test_an_element_returning_reduction_still_keeps_the_field_withheld():
    # THE FAILURE DIRECTION, MEASURED, AND IT IS THE OPPOSITE OF WHAT EXCLUDING
    # min AND max WAS MEANT TO BUY. Anything absent from CONTENT_REDUCERS is
    # read as NOT a mask, hence as disclosure, hence the field leaves `withheld`
    # and EVERY assertion over that container goes unflagged. So excluding them
    # does not make the guard louder about a repr that prints one word - it
    # makes the guard go SILENT on the whole frozenset.
    #
    # This replaces an assertion that compared CONTENT_REDUCERS against a
    # literal set, which restated a constant and would have survived the
    # detector being gutted.
    found = scan_source("<element>", ELEMENT_REDUCTION_SOURCE)
    graded = len(found)
    assert graded == 1, (
        f"a field masked with max() yielded {graded} findings, expected 1. "
        "Reading an element-returning reduction as disclosure drops the field "
        "out of the withheld set and stops the guard grading it at all"
    )
